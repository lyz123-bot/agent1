<template>
  <div class="msg-list" ref="box" @scroll.passive="onScroll">
    <div v-if="messages.length === 0 && !loadingMore" class="welcome-slot">
      <slot name="welcome" />
    </div>
    <div v-if="loadingMore && messages.length === 0" class="loading">加载中...</div>

    <template v-else>
      <div v-for="(group, idx) in grouped" :key="idx">
        <div class="date-sep">{{ group.date }}</div>
        <div v-for="msg in group.msgs" :key="msg.id" class="bubble-wrapper">
          <!-- 原有消息气泡 -->
          <message-bubble :msg="msg" />

          <!-- 仅对已完成流式的 assistant 消息显示复制图标 -->
          <copy-outlined v-if="msg.role === 'assistant' && !msg.isStreaming" class="copy-icon"
            @click="copyMessage(msg)" />
        </div>
      </div>
      <div v-if="hasMore" class="load-more" @click="$emit('load-more')">
        {{ loadingMore ? '加载中...' : '加载更多' }}
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { CopyOutlined } from '@ant-design/icons-vue'
import MessageBubble from './MessageBubble.vue'

const props = defineProps({
  messages: Array,
  hasMore: Boolean,
  loadingMore: Boolean
})
const emit = defineEmits(['load-more'])
const box = ref(null)

function onScroll() {
  if (box.value.scrollTop === 0 && props.hasMore) {
    emit('load-more')
  }
}

// 分组逻辑
const grouped = computed(() => {
  const res = []
  let curDate = '', curGroup = null
  for (const m of props.messages) {
    const d = new Date(m.timestamp).toLocaleDateString()
    if (d !== curDate) {
      curDate = d
      curGroup = { date: d, msgs: [] }
      res.push(curGroup)
    }
    curGroup.msgs.push(m)
  }
  return res
})

/** 复制到剪贴板 */
function copyMessage(m) {
  const text = m.content ?? ''
  if (!text.trim()) {
    message.error('没有可复制的内容')
    return
  }
  navigator.clipboard.writeText(text)
    .then(() => message.success('已复制到剪贴板'))
    .catch(() => message.error('复制失败，请手动复制'))
}
</script>

<style scoped>
.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
  scrollbar-width: thin;
}

.date-sep {
  text-align: center;
  margin: 16px 0;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  position: relative;
}

.date-sep::before,
.date-sep::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 35%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.12), transparent);
}

.date-sep::before {
  left: 0;
}

.date-sep::after {
  right: 0;
}

.bubble-wrapper {
  position: relative;
  margin-bottom: 14px;
}

.copy-icon {
  position: absolute;
  left: 60px;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: color 0.2s, transform 0.2s;
  z-index: 5;
}

.copy-icon:hover {
  color: #69b1ff;
  transform: scale(1.1);
}

.load-more {
  text-align: center;
  margin: 12px 0;
  padding: 8px 16px;
  color: rgba(22, 119, 255, 0.9);
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s, color 0.2s;
}

.load-more:hover {
  background: rgba(22, 119, 255, 0.15);
  color: #fff;
}

.loading,
.welcome-slot {
  text-align: center;
  margin-top: 20%;
  color: rgba(255, 255, 255, 0.45);
}

.msg-list::-webkit-scrollbar {
  width: 6px;
}

.msg-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 3px;
}

.msg-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
