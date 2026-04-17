from celery import shared_task
import traceback, hashlib, uuid, shutil
from pathlib import Path
from typing import List

from django.conf import settings

import pdfplumber, docx, pptx, torch, chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from chromadb import PersistentClient

# 同视图保持一致
UPLOAD_DIR = Path('uploads')
VECTOR_DIR = Path('vector_store')


def extract_text(fp: Path) -> str:
    suf = fp.suffix.lower()
    try:
        if suf in {'.txt', '.md', '.markdown'}:
            return fp.read_text(encoding='utf-8', errors='ignore')

        if suf == '.pdf':
            with pdfplumber.open(fp) as pdf:
                return "\n".join(p.extract_text() or '' for p in pdf.pages)

        if suf in {'.docx', '.doc'}:
            doc = docx.Document(fp)
            return "\n".join(p.text for p in doc.paragraphs)

        if suf in {'.pptx', '.ppt'}:
            texts = []
            for slide in pptx.Presentation(fp).slides:
                for shape in slide.shapes:
                    if hasattr(shape, 'text'):
                        texts.append(shape.text)
            return "\n".join(texts)

        return fp.read_text(encoding='utf-8', errors='ignore')

    except Exception as e:
        print(f"[warn] 解析失败 {fp.name}: {e}")
        return ""


@shared_task(bind=True)
def build_vectors_task(self):
    """
    1. 从 UPLOAD_DIR 读取文件并提取文本
    2. 使用 LangChain 切块（含 MD 分级切块）
    3. 用 HuggingFaceEmbeddings 计算 embedding
    4. 存入 Chroma 持久化目录 VECTOR_DIR，增量去重(md5)
    5. 清理 UPLOAD_DIR
    返回 { task_id, added, total } 或 { error }
    """
    try:
        # 1) 提取原始文本与元信息
        raw_texts, metas = [], []
        for fp in UPLOAD_DIR.glob("*"):
            txt = extract_text(fp).strip()
            if txt:
                raw_texts.append(txt)
                metas.append({'source': fp.name})
        if not raw_texts:
            return {'msg': '没有可用文件'}

        # 2) 切块
        splitter_default = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=40,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " "],
        )
        splitter_md = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", 1), ("##", 2), ("###", 3), ("####", 4)]
        )

        chunks, meta_chunks = [], []
        for txt, meta in zip(raw_texts, metas):
            splitter = splitter_md if meta['source'].lower().endswith(('.md', '.markdown')) else splitter_default
            cks = splitter.split_text(txt)
            for idx, chunk in enumerate(cks):
                chunks.append(chunk)
                meta_chunks.append({**meta, 'chunk_id': idx})

        # 3) 嵌入器 & Chroma 客户端
        embedder = HuggingFaceEmbeddings(
            model_name=settings.EMBED_MODEL_PATH,
            model_kwargs={
                'device': 'cuda' if torch.cuda.is_available() else 'cpu',
                'trust_remote_code': True
            },
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 64}
        )
        VECTOR_DIR.mkdir(exist_ok=True)
        client = PersistentClient(path=str(VECTOR_DIR))

        class EmbFn:
            def __init__(self, e): self.e = e
            def __call__(self, input: List[str]):
                return self.e.embed_documents(input)

        try:
            col = client.get_collection(settings.COLLECTION_NAME)
        except chromadb.errors.NotFoundError:
            col = client.create_collection(
                name=settings.COLLECTION_NAME,
                embedding_function=EmbFn(embedder),
                metadata={'hnsw:space': 'cosine'}
            )

        # 4) 增量去重(md5) + 写入
        new_chunks, new_meta = [], []
        for chunk, meta in zip(chunks, meta_chunks):
            md5 = hashlib.md5(chunk.encode('utf-8')).hexdigest()
            exists = col.get(where={'doc_hash': md5}, include=['metadatas'])
            if exists['ids']:
                continue
            meta['doc_hash'] = md5
            new_chunks.append(chunk)
            new_meta.append(meta)

        if new_chunks:
            embeddings = embedder.embed_documents(new_chunks)
            col.add(
                ids=[uuid.uuid4().hex for _ in new_chunks],
                documents=new_chunks,
                metadatas=new_meta,
                embeddings=embeddings
            )

        # 5) 清理上传目录
        shutil.rmtree(UPLOAD_DIR)
        UPLOAD_DIR.mkdir(exist_ok=True)

        return {
            'task_id': self.request.id,
            'added': len(new_chunks),
            'total': len(chunks)
        }

    except Exception as e:
        traceback.print_exc()
        return {'error': str(e)}
