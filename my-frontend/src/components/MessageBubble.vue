<!-- src/components/MessageBubble.vue -->
<template>
  <div :class="['bubble-wrapper', msg.role]">
    <div class="avatar">
      <component
        :is="
          msg.role === 'user'
            ? UserOutlined
            : msg.isStreaming
            ? LoadingOutlined
            : MessageOutlined
        "
      />
    </div>
    <div class="bubble" :class="{ streaming: msg.isStreaming }">
      <div v-if="!msg.isStreaming" class="bubble-inner" v-html="msg.rendered" />
      <div v-else class="bubble-stream">
        {{ msg.content }}<span class="cursor"></span>
      </div>
      <div class="arrow"></div>
      <!-- 源文档引用列表 -->
      <ul v-if="msg.sources && msg.sources.length" class="source-list">
        <li
          v-for="(s, idx) in msg.sources"
          :key="idx"
          class="source-item"
        >
          <div class="source-meta">{{ s.metadata.source }}</div>
          <div class="source-snippet">{{ s.page_content }}…</div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
import {
  MessageOutlined,
  LoadingOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'

const props = defineProps({
  msg: {
    type: Object,
    required: true
  }
})

// 如果需要格式化时间，可保留；目前未使用
const formatTime = d =>
  new Date(d).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
</script>

<style scoped>
.bubble-wrapper {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.bubble-wrapper.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  color: #fff;
  margin: 0 10px;
}

.bubble-wrapper.user .avatar {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  box-shadow: 0 0 14px rgba(22, 119, 255, 0.4);
}

.bubble-wrapper.assistant .avatar {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.bubble {
  max-width: 70%;
  position: relative;
  padding: 14px 16px;
  border-radius: 14px;
  transition: box-shadow 0.2s;
}

.bubble-wrapper.assistant .bubble {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  color: rgba(255, 255, 255, 0.9);
}

.bubble-wrapper.user .bubble {
  background: linear-gradient(135deg, rgba(22, 119, 255, 0.35) 0%, rgba(22, 119, 255, 0.25) 100%);
  border: 1px solid rgba(22, 119, 255, 0.4);
  box-shadow: 0 4px 20px rgba(22, 119, 255, 0.2);
  color: #fff;
}

.arrow {
  width: 0;
  height: 0;
  border: 8px solid transparent;
  position: absolute;
  top: 14px;
}

.bubble-wrapper.user .arrow {
  border-right-color: rgba(22, 119, 255, 0.35);
  right: -16px;
}

.bubble-wrapper.assistant .arrow {
  border-left-color: rgba(255, 255, 255, 0.05);
  left: -16px;
}

.bubble-inner :deep(pre) {
  background: rgba(0, 0, 0, 0.25);
  padding: 10px 12px;
  border-radius: 8px;
  overflow: auto;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.bubble-inner :deep(code) {
  color: rgba(255, 255, 255, 0.9);
}

.bubble-stream {
  white-space: pre-wrap;
  word-break: break-word;
  color: inherit;
}

.cursor {
  display: inline-block;
  width: 4px;
  height: 14px;
  background: #1677ff;
  vertical-align: text-bottom;
  animation: blink 1s infinite;
  margin-left: 4px;
  border-radius: 2px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.bubble-inner {
  user-select: text !important;
  -webkit-user-select: text !important;
  cursor: text;
}

.bubble-inner :deep(pre),
.bubble-inner :deep(code) {
  user-select: text !important;
  -webkit-user-select: text !important;
}

.source-list {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(255, 255, 255, 0.12);
  list-style: none;
}

.source-item {
  margin-bottom: 6px;
}

.source-meta {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.6);
}

.source-snippet {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-left: 4px;
}
</style>
