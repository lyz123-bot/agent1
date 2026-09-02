# vectordb/views.py

import uuid
from pathlib import Path

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status, permissions
from chromadb import PersistentClient
from django.conf import settings

from .tasks import build_vectors_task

# 上传目录、向量持久化目录
UPLOAD_DIR = Path('uploads')
VECTOR_DIR = Path('vector_store')


class VDBUploadView(APIView):
    """
    POST /vdb/upload/
    tags: [VectorDB]
    summary: Batch upload documents for vectorization (admin only)
    security: BearerAuth
    requestBody: multipart/form-data { files: [binary] }
    responses:
      202: { task_id: string }
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]

    def post(self, request):
        files = request.FILES.getlist('files')
        if not files:
            return Response({'error': '未检测到文件'}, status=status.HTTP_400_BAD_REQUEST)

        # 1) 保存到本地
        UPLOAD_DIR.mkdir(exist_ok=True)
        for f in files:
            unique_name = f"{uuid.uuid4().hex}_{f.name}"
            dest = UPLOAD_DIR / unique_name
            with open(dest, 'wb') as dst:
                for chunk in f.chunks():
                    dst.write(chunk)

        # 2) 异步触发向量构建（从 UPLOAD_DIR 读取所有文件）
        task = build_vectors_task.delay()

        # 3) 返回 202 Accepted 与 task_id
        return Response({'task_id': task.id}, status=status.HTTP_202_ACCEPTED)


class VectorFileListView(APIView):
    """
    GET /api/vdb/files/       → 列出 collection 中所有 chunk 及其内容
    DELETE /api/vdb/files/    → 清空整个 collection
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        client = PersistentClient(path=str(settings.VECTOR_DIR))
        col = client.get_collection(settings.COLLECTION_NAME)

        # 取出所有 metadata 和 documents（实际的文本片段）
        resp = col.get(include=["metadatas", "documents"])

        metas = resp.get("metadatas", [])
        docs = resp.get("documents", [])

        # 合并成一个列表，每条带上 metadata + page_content
        results = []
        for meta, doc in zip(metas, docs):
            entry = meta.copy()  # meta 里已经有 source, chunk_id, doc_hash 等
            entry["page_content"] = doc
            results.append(entry)

        return Response(results, status=status.HTTP_200_OK)

    def delete(self, request):
        client = PersistentClient(path=str(settings.VECTOR_DIR))
        col = client.get_collection(settings.COLLECTION_NAME)
        col.delete()  # 全部删除
        return Response(status=status.HTTP_204_NO_CONTENT)


class VectorFileDeleteView(APIView):
    """
    DELETE /api/vdb/files/{doc_hash}/  → 删除单个 chunk
    """
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, doc_hash):
        client = PersistentClient(path=str(settings.VECTOR_DIR))
        col = client.get_collection(settings.COLLECTION_NAME)
        col.delete(where={"doc_hash": doc_hash})
        return Response(status=status.HTTP_204_NO_CONTENT)
