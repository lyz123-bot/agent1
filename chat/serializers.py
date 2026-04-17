from rest_framework import serializers
from .models import Thread, ChatLog

class ChatRequestSerializer(serializers.Serializer):
    message   = serializers.CharField(max_length=4000)
    thread_id = serializers.CharField(required=False)

class ChatResponseSerializer(serializers.Serializer):
    answer            = serializers.CharField()
    latency           = serializers.FloatField()
    prompt_tokens     = serializers.IntegerField()
    completion_tokens = serializers.IntegerField()
    model_name        = serializers.CharField()
    source_documents  = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=[],
        help_text="检索到的文档列表，每项包含 metadata 和 page_content 片段"
    )

class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Thread
        fields = ('id', 'title', 'created_at')

class ChatLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatLog
        fields = ('id', 'user', 'thread', 'prompt', 'answer', 'created_at','source_documents')
        read_only_fields = ('id', 'created_at')
