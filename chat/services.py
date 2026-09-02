# services.py
# 知识库问答：检索仍用本地 embedder/reranker，生成改为 DeepSeek API

import time
import threading
import math

import torch
from django.conf import settings
from openai import OpenAI

from sentence_transformers import CrossEncoder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma as LCChroma
from langchain.prompts import PromptTemplate

# ─────────── Prompt & 超参数 ───────────
QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "你是官方知识助手，用中文回答下列问题。\n"
        "如果资料不足，请回复“资料中未找到相关信息”。\n\n"
        "{context}\n\n"
        "【问题】\n{question}\n\n"
        "【回答】"
    )
)

MAX_DIST    = 0.5   # 距离阈值，超过则直接调用 LLM
MMR_LAMBDA  = 0.5   # λ-MMR 重排参数
TOP_N       = 3     # 最终返回 top N 文档

# 线程本地缓存，用于模型实例复用
_tl = threading.local()

def get_embedder() -> HuggingFaceEmbeddings:
    if hasattr(_tl, "embedder"):
        return _tl.embedder
    _tl.embedder = HuggingFaceEmbeddings(
        model_name=settings.EMBED_MODEL_PATH,
        model_kwargs={
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "trust_remote_code": True
        },
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 64
        }
    )
    return _tl.embedder

def get_reranker() -> CrossEncoder:
    if hasattr(_tl, "reranker"):
        return _tl.reranker
    _tl.reranker = CrossEncoder(
        settings.RERANK_PATH,
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    return _tl.reranker

def adaptive_k(num_docs: int) -> int:
    """根据向量库大小自适应检索 k 值"""
    return min(max(round(math.log2(max(num_docs, 2))) + 5, 10), 80)


def _get_deepseek_client() -> OpenAI:
    api_key = getattr(settings, "DEEPSEEK_API_KEY", None) or ""
    base_url = getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return OpenAI(api_key=api_key.strip(), base_url=base_url.rstrip("/"))


def _get_chat_model() -> str:
    return getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat")


def _history_to_messages(history: list[dict[str, str]] | None, prompt: str):
    """(history or []) + [user: prompt] -> OpenAI messages"""
    msgs = []
    for h in (history or []):
        msgs.append({"role": h["role"], "content": h["content"]})
    msgs.append({"role": "user", "content": prompt})
    return msgs


def generate(
    prompt: str,
    history: list[dict[str, str]] | None = None,
    max_tokens: int = 1024,
) -> dict:
    """调用 DeepSeek API 生成回答，用于知识库问答（含无检索 / 有检索）。"""
    start = time.time()
    client = _get_deepseek_client()
    messages = _history_to_messages(history, prompt)
    try:
        resp = client.chat.completions.create(
            model=_get_chat_model(),
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2,
        )
        msg = resp.choices[0].message
        answer = (msg.content or "").strip()
        # 若 prompt 内含【回答】且模型也输出了该标记，只取其后内容
        if "【回答】" in answer:
            answer = answer.rsplit("【回答】", 1)[-1].strip()
        usage = getattr(resp, "usage", None)
        return {
            "answer": answer,
            "latency": round(time.time() - start, 3),
            "prompt_tokens": getattr(usage, "prompt_tokens", None) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", None) or 0,
            "model_name": _get_chat_model(),
        }
    except Exception as e:
        return {
            "answer": f"抱歉，生成失败：{e}",
            "latency": round(time.time() - start, 3),
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "model_name": _get_chat_model(),
        }


def generate_stream(
    prompt: str,
    history: list[dict[str, str]] | None = None,
    max_tokens: int = 1024,
):
    """流式调用 DeepSeek API，用于知识库问答 SSE。"""
    client = _get_deepseek_client()
    messages = _history_to_messages(history, prompt)
    try:
        stream = client.chat.completions.create(
            model=_get_chat_model(),
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and getattr(delta, "content", None):
                yield delta.content
    except Exception as e:
        yield f"\n\n[生成失败: {e}]"

