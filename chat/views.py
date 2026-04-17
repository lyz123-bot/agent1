# chat/views.py

from uuid import UUID, uuid4
import json
import time
from pathlib import Path

from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from django.conf import settings

from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import BaseRenderer, JSONRenderer
from drf_spectacular.utils import extend_schema

from chromadb import PersistentClient
from langchain_community.vectorstores import Chroma as LCChroma

from .models import ChatLog, Thread
from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    ThreadSerializer,
)
from .services import (
    generate,
    generate_stream,
    get_embedder,
    get_reranker,
    adaptive_k,
    QA_PROMPT,
    MAX_DIST,
    MMR_LAMBDA,
    TOP_N,
)

class EventStreamRenderer(BaseRenderer):
    media_type = "text/event-stream"
    format = "event-stream"
    charset = None
    render_style = "binary"

    def render(self, data, *_):
        return data


def sse(data):
    """生成 SSE 格式的消息"""
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False)
    return f"data: {data}\n\n"


class ChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = (EventStreamRenderer, JSONRenderer)

    @extend_schema(
        request=ChatRequestSerializer,
        responses={200: ChatResponseSerializer},
        description="POST /api/chat/  支持 SSE 或 JSON",
    )
    def post(self, request):
        ser = ChatRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        prompt = ser.validated_data["message"]
        raw_tid = ser.validated_data.get("thread_id")

        # 获取或创建线程
        thread = None
        if raw_tid:
            try:
                thread = Thread.objects.filter(
                    id=UUID(raw_tid), user=request.user
                ).first()
            except (ValueError, TypeError):
                pass
        if thread is None:
            thread = Thread.objects.create(
                id=uuid4(), user=request.user, title="新会话"
            )

        # 拉取最近 N 条历史
        N = 5
        qs = (
            ChatLog.objects.filter(thread=thread)
            .order_by("-created_at")[:N][::-1]
        )
        history = []
        for r in qs:
            history.append({"role": "user", "content": r.prompt})
            history.append({"role": "assistant", "content": r.answer})

        # SSE 流式 + 向量检索
        if "text/event-stream" in request.headers.get("Accept", ""):
            started_at = time.time()
            prompt_tokens = len(prompt)
            completion_tokens = 0
            answer_buf = []

            #准备向量检索：可能调整 stream_prompt 并生成 src_docs
            src_docs = []
            stream_prompt = prompt

            client = PersistentClient(path=str(Path(settings.VECTOR_DIR)))
            try:
                col = client.get_collection(settings.COLLECTION_NAME)
            except Exception:
                col = None

            if col:
                embedder = get_embedder()
                # 安全地取距离
                try:
                    qr = col.query(
                        query_embeddings=[embedder.embed_query(prompt)],
                        n_results=1,
                        include=["distances"],
                    )
                    dist = qr["distances"][0][0]
                except (IndexError, KeyError):
                    dist = None

                if dist is not None and dist < MAX_DIST:
                    # 相关性够高，实际检索
                    k = adaptive_k(col.count())
                    vs = LCChroma(
                        client=client,
                        collection_name=settings.COLLECTION_NAME,
                        embedding_function=embedder,
                    )
                    retriever = vs.as_retriever(
                        search_type="mmr",
                        search_kwargs={"k": k, "lambda_mult": MMR_LAMBDA},
                    )
                    docs = retriever.get_relevant_documents(prompt)

                    reranker = get_reranker()
                    scores = reranker.predict([[prompt, d.page_content] for d in docs])
                    docs = [
                               d for d, _ in sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
                           ][:TOP_N]

                    context = "\n\n".join(
                        f"### 段落 {i + 1} | {d.metadata.get('source', '未知')}\n{d.page_content}"
                        for i, d in enumerate(docs)
                    )
                    stream_prompt = QA_PROMPT.format(context=context, question=prompt)
                    src_docs = [
                        {"metadata": d.metadata, "page_content": d.page_content[:300]}
                        for d in docs
                    ]

            # 构造 SSE 流
            def event_stream():
                nonlocal completion_tokens
                # 开始事件
                yield sse({"ok": True, "event": "start", "thread_id": str(thread.id)})

                # 真正流式调用
                for delta in generate_stream(stream_prompt, history):
                    answer_buf.append(delta)
                    completion_tokens = len(answer_buf)
                    yield sse({
                        "text": delta,
                        "thread_id": str(thread.id),
                    })

                # 结束事件，带上检索结果
                yield sse({
                    "ok": True,
                    "event": "end",
                    "thread_id": str(thread.id),
                    "source_documents": src_docs,
                })

                # 写入数据库
                ChatLog.objects.create(
                    user=request.user,
                    thread=thread,
                    prompt=prompt,
                    answer="".join(answer_buf).strip(),
                    latency=round(time.time() - started_at, 3),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model_name=getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat"),
                    source_documents=src_docs,
                )

            resp = StreamingHttpResponse(
                event_stream(), content_type="text/event-stream"
            )
            resp["Cache-Control"] = "no-cache"
            return resp

        # 向量检索 + 生成
        src_docs = []
        client = PersistentClient(path=str(Path(settings.VECTOR_DIR)))
        try:
            col = client.get_collection(settings.COLLECTION_NAME)
        except Exception:
            col = None

        # 如果没有向量库或库为空，直接生成
        if not col or col.count() == 0:
            result = generate(prompt, history)
        else:
            embedder = get_embedder()
            # 安全地查询最近距离
            try:
                qr = col.query(
                    query_embeddings=[embedder.embed_query(prompt)],
                    n_results=1,
                    include=["distances"],
                )
                dist = qr["distances"][0][0]
            except (IndexError, KeyError):
                dist = None

            if dist is None or dist >= MAX_DIST:
                # 不使用检索结果
                result = generate(prompt, history)
            else:
                # 正常检索 + MMR + 重排 + Prompt 构造
                k = adaptive_k(col.count())
                vs = LCChroma(
                    client=client,
                    collection_name=settings.COLLECTION_NAME,
                    embedding_function=embedder,
                )
                retriever = vs.as_retriever(
                    search_type="mmr",
                    search_kwargs={"k": k, "lambda_mult": MMR_LAMBDA},
                )
                docs = retriever.get_relevant_documents(prompt)

                reranker = get_reranker()
                scores = reranker.predict([[prompt, d.page_content] for d in docs])
                docs = [
                           d for d, _ in sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
                       ][:TOP_N]

                context = "\n\n".join(
                    f"### 段落 {i + 1} | {d.metadata.get('source', '未知')}\n{d.page_content}"
                    for i, d in enumerate(docs)
                )
                prompt_text = QA_PROMPT.format(context=context, question=prompt)
                result = generate(prompt_text, [], max_tokens=1024)
                src_docs = [
                    {"metadata": d.metadata, "page_content": d.page_content[:300]}
                    for d in docs
                ]

        # 写入日志
        ChatLog.objects.create(
            user=request.user,
            thread=thread,
            prompt=prompt,
            answer=result["answer"],
            latency=result.get("latency"),
            prompt_tokens=result.get("prompt_tokens"),
            completion_tokens=result.get("completion_tokens"),
            model_name=result.get("model_name"),
            source_documents=src_docs,
        )

        # 返回 JSON
        response_data = {**result, "source_documents": src_docs}
        return Response(response_data, status=status.HTTP_200_OK)


class ThreadListCreateView(generics.ListCreateAPIView):
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Thread.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ThreadDestroyView(generics.DestroyAPIView):
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Thread.objects.filter(user=self.request.user)

class MessageListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        thread = get_object_or_404(
            Thread, id=self.kwargs["tid"], user=self.request.user
        )
        qs = ChatLog.objects.filter(thread=thread).order_by("-id")
        before = self.request.query_params.get("before")
        if before:
            qs = qs.filter(id__lt=before)
        limit = int(self.request.query_params.get("limit", 40))
        return qs[:limit]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = [
            {
                "id": r.id,
                "prompt": r.prompt,
                "answer": r.answer,
                "created_at": r.created_at,
                "source_documents": r.source_documents,
            }
            for r in qs
        ]
        return Response(data)

    def delete(self, request, *args, **kwargs):
        thread = get_object_or_404(
            Thread, id=self.kwargs["tid"], user=self.request.user
        )
        ChatLog.objects.filter(thread=thread).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ThreadUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Thread.objects.filter(user=self.request.user)
