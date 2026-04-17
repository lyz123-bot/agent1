# chat/models.py
from django.db import models
from django.conf import settings
import uuid
class Thread(models.Model):
    """
    会话线程（聊天窗口左侧列表的一行）
    - 每个用户可拥有多条线程
    - 使用 UUID 作为主键，前端直接当 id 传递
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="threads",
    )
    title = models.CharField(max_length=120, default="新会话")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self) -> str:  # 在 Django Admin 中更友好
        return f"{self.title} ({self.user})"
class ChatLog(models.Model):
    """
    单条对话消息
    """
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_logs",
    )

    prompt = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # 统计信息（接入真实 LLM 后可写）
    latency = models.FloatField(null=True, blank=True)
    prompt_tokens = models.IntegerField(null=True, blank=True)
    completion_tokens = models.IntegerField(null=True, blank=True)
    model_name = models.CharField(max_length=64, default="dummy-echo")
    source_documents = models.JSONField(default=list, blank=True)
    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.thread_id}] {self.prompt[:20]}…"