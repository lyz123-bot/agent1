from django.urls import path
from .views import (
    ChatView,
    ThreadListCreateView,
    ThreadDestroyView,
    MessageListView,
    ThreadUpdateView
)

urlpatterns = [
    # 聊天主接口（流式 SSE 或 JSON）
    path("", ChatView.as_view(), name="chat"),

    # 线程：列表 & 新建
    path("threads/", ThreadListCreateView.as_view(), name="threads"),

    path("threads/<uuid:pk>/", ThreadUpdateView.as_view(), name="thread-update"),
    # 线程：删除
    path("threads/<uuid:pk>/delete/", ThreadDestroyView.as_view(), name="thread-delete"),

    # 消息：分页查询 & 删除历史
    path(
        "threads/<uuid:tid>/messages/",
        MessageListView.as_view(),
        name="message-list",
    ),
]