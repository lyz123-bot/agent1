<template>
  <!-- 用户气泡 -->
  <div v-if="msg.role === 'user'" class="bubble user">
    <a-card class="user-card">
      <div class="user-content">{{ msg.content }}</div>
    </a-card>
  </div>

  <!-- AI 气泡 -->
  <div v-else class="bubble ai" :class="{ streaming: msg.isStreaming }">
    <a-avatar size="small" style="background: #1677ff">
      <MessageOutlined v-if="!msg.isStreaming" />
      <LoadingOutlined v-else />
    </a-avatar>
    <a-card class="answer-card">
      <!-- 流式传输时显示纯文本 -->
      <div v-if="msg.isStreaming" class="answer-content">
        {{ msg.content }}
        <span class="cursor"></span>
      </div>
      <!-- 传输完成后显示渲染内容 -->
      <div v-else v-html="msg.rendered"></div>
    </a-card>
  </div>
</template>

<script setup>
import { MessageOutlined, LoadingOutlined } from '@ant-design/icons-vue';

defineProps({
  msg: {
    type: Object,
    required: true
  }
});
</script>

<style scoped>
/* 添加流式内容样式 */
.answer-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  padding: 14px 16px;
}

/* 其余样式保持不变 */
.bubble {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.user {
  justify-content: flex-end;
}

.ai {
  justify-content: flex-start;
}

.user-card {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  border-radius: 16px 16px 4px 16px;
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);
  transition: transform 0.2s ease;
}

.user-content {
  padding: 12px 16px;
  line-height: 1.5;
}
/* 悬停效果 */
.user-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(79, 172, 254, 0.4);
}

.answer-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}
/* AI气泡 */
.answer-card {
  background: linear-gradient(135deg, #f5f7fa, #ffffff);
  border-radius: 16px 16px 16px 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: none;
  transition: transform 0.2s ease;
}

/* 流式响应样式 */
.bubble.ai.streaming .answer-card {
  box-shadow: 0 2px 12px rgba(22, 119, 255, 0.15);
  border-color: #b6d4fe;
}

.cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background-color: #1677ff;
  margin-left: 4px;

  vertical-align: text-bottom;
  animation: pulse 1.2s infinite;
}


@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
/* Markdown 内容样式 */
.answer-card :deep(pre) {
  padding: 12px;
  background: #f6f8fa;
  border-radius: 6px;
  overflow: auto;
  margin: 8px 0;
  font-size: 14px;
}

.answer-card :deep(code) {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 14px;
}

.answer-card :deep(blockquote) {
  border-left: 4px solid #ddd;
  padding-left: 16px;
  margin: 12px 0;
  color: #666;
}

.answer-card :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.answer-card :deep(th),
.answer-card :deep(td) {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: left;
}

.answer-card :deep(th) {
  background-color: #f7f7f7;
  font-weight: 600;
}

.answer-card :deep(ul),
.answer-card :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.answer-card :deep(li) {
  margin-bottom: 4px;
}

.answer-card :deep(a) {
  color: #1677ff;
  text-decoration: none;
}

.answer-card :deep(a:hover) {
  text-decoration: underline;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .user-card, .answer-card {
    max-width: 85%;
  }
  
  .bubble {
    margin-bottom: 16px;
  }
}
.user-content,
.answer-card,
.answer-card :deep(*) {
  user-select: text;
  cursor: text;
}
</style>