<!-- src/views/ChatPage.vue -->
<template>
  <!-- 重命名模态框 -->
  <a-modal
    v-model:visible="renameModalVisible"
    title="重命名会话"
    @ok="onConfirmRename"
    @cancel="onCancelRename"
    okText="确定"
    cancelText="取消"
  >
    <a-input v-model:value="renameValue" placeholder="请输入新的会话名称" maxlength="120" />
  </a-modal>

  <!-- 主布局 -->
  <ChatLayout
    :threads="threads"
    :active-thread-id="activeThreadId"
    :active-thread-title="activeThreadTitle"
    :messages="messages"
    :has-more="hasMore"
    :loading-more="loadingMore"
    @select-thread="handleSelectThread"
    @new-thread="handleNewThread"
    @load-more="loadMoreMessages"
    @send="handleSendMessage"
    @delete-thread="handleDeleteThread"
    @rename-thread="openRenameModal"
    @clear-messages="handleClearMessages"
    @export="handleExport"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import { message } from 'ant-design-vue'
import ChatLayout from '@/components/ChatLayout.vue'
import {
  listThreads,
  createThread,
  deleteThread,
  updateThread,
  listMessages,
  clearMessages,
  streamChat
} from '@/api'
import { saveAs } from 'file-saver'   
import dayjs from 'dayjs'
const router = useRouter()

// —— 会话列表 & 状态 —— 
const threads = ref([])
const activeThreadId = ref(null)
const activeThreadTitle = ref('')
const messages = ref([])
const hasMore = ref(false)
const loadingMore = ref(false)

// —— 重命名模态框状态 —— 
const renameModalVisible = ref(false)
const renameValue = ref('')
const renameTargetId = ref(null)

/** 统一错误处理：鉴权失败跳登录 */
function handleAuthError(err) {
  console.error(err)
  message.error('登录已过期，请重新登录')
  router.push('/login')
}

// 页面加载：获取会话列表
onMounted(async () => {
  try {
    threads.value = await listThreads()
    if (threads.value.length) {
      await selectThread(threads.value[0].id)
    }
  } catch (err) {
    handleAuthError(err)
  }
})

// 选中会话，并加载消息
async function selectThread(id) {
  activeThreadId.value = id
  const t = threads.value.find(t => t.id === id)
  activeThreadTitle.value = t?.title || ''
  messages.value = []
  hasMore.value = true
  await loadMoreMessages(true)
}

let beforeCursor = null
async function loadMoreMessages(reset = false) {
  if (loadingMore.value || (!hasMore.value && !reset)) return
  loadingMore.value = true
  if (reset) {
    messages.value = []
    beforeCursor = null
    hasMore.value = true
  }
  try {
    const logs = await listMessages(activeThreadId.value, { before: beforeCursor, limit: 40 })
    const page = []
    logs.reverse().forEach(l => {
      page.push({
        id: l.id + '-u',
        role: 'user',
        content: l.prompt,
        timestamp: l.created_at,
        rendered: l.prompt,
        isStreaming: false
      })
      page.push({
        id: l.id + '-a',
        role: 'assistant',
        content: l.answer,
        timestamp: l.created_at,
        rendered: marked.parse(l.answer),
        isStreaming: false,
        sources: l.source_documents || []
      })
    })
    if (reset) messages.value = page
    else messages.value.push(...page)

    hasMore.value = logs.length === 40
    beforeCursor = hasMore.value ? logs[logs.length - 1].id : null
  } catch (err) {
    handleAuthError(err)
  } finally {
    loadingMore.value = false
  }
}

// 新建会话
async function handleNewThread() {
  try {
    const t = await createThread('新会话')
    threads.value.unshift(t)
    await selectThread(t.id)
  } catch (err) {
    handleAuthError(err)
  }
}

// 删除会话
async function handleDeleteThread(id) {
  const tid = id || activeThreadId.value
  if (!tid) return
  try {
    await deleteThread(tid)
    threads.value = threads.value.filter(t => t.id !== tid)
    if (threads.value.length) {
      await selectThread(threads.value[0].id)
    } else {
      activeThreadId.value = null
      activeThreadTitle.value = ''
      messages.value = []
    }
  } catch (err) {
    handleAuthError(err)
  }
}

// 打开“重命名”模态框
function openRenameModal({ id, newName }) {
  renameTargetId.value = id
  renameValue.value = newName || ''
  renameModalVisible.value = true
}

// 确认重命名
async function onConfirmRename() {
  const id = renameTargetId.value
  const title = renameValue.value.trim()
  if (!title) {
    message.error('名称不能为空')
    return
  }
  try {
    await updateThread(id, { title })
    const t = threads.value.find(t => t.id === id)
    if (t) t.title = title
    if (activeThreadId.value === id) activeThreadTitle.value = title
    message.success('重命名成功')
    renameModalVisible.value = false
  } catch (err) {
    console.error(err)
    message.error('重命名失败，请稍后重试')
  }
}

// 取消重命名
function onCancelRename() {
  renameModalVisible.value = false
}

// 清空消息
async function handleClearMessages() {
  if (!activeThreadId.value) return
  try {
    await clearMessages(activeThreadId.value)
    messages.value = []
    hasMore.value = false
  } catch (err) {
    handleAuthError(err)
  }
}

// 发送消息（支持 SSE 流式）
let abortCtrl = null
async function handleSendMessage(text) {
  if (!activeThreadId.value) {
    const t = await createThread('新会话')
    threads.value.unshift(t)
    activeThreadId.value = t.id
    activeThreadTitle.value = t.title
  }

  // 推入用户消息
  messages.value.push({
    id: `u-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: new Date(),
    rendered: text,
    isStreaming: false,
    sources: []
  })

  // 准备一个空的 AI 消息
  const aiMsg = {
    id: `a-${Date.now()}`,
    role: 'assistant',
    content: '',
    rendered: '',
    isStreaming: true,
    timestamp: new Date(),
    sources: []    // ← 用于存放后端返回的 source_documents
  }
  messages.value.push(aiMsg)

  // 取消上次请求
  abortCtrl?.abort?.()
  abortCtrl = new AbortController()

  try {
    const reader = await streamChat(
      { message: text, thread_id: activeThreadId.value },
      abortCtrl.signal
    )
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      const data = JSON.parse(new TextDecoder().decode(value))

      // 如果 SSE 推送了纯文本片段
      if (data.text) {
        aiMsg.content += data.text
        aiMsg.rendered = aiMsg.content
        // 更新列表中的最后一条
        messages.value.splice(-1, 1, { ...aiMsg })
      }

      // 如果后端发了结束事件并带回 source_documents
      if (data.event === 'end') {
        aiMsg.sources = data.source_documents || []
      }
    }
  } catch (err) {
    aiMsg.content = `错误：${err.message}`
    aiMsg.rendered = aiMsg.content
    messages.value.splice(-1, 1, { ...aiMsg })
  } finally {
    // 流式结束，渲染 Markdown
    aiMsg.isStreaming = false
    aiMsg.rendered = marked.parse(aiMsg.content)
    messages.value.splice(-1, 1, { ...aiMsg })
  }
}
function messagesToMarkdown(threadTitle, msgs) {
  const lines = []
  lines.push(`# ${threadTitle || '未命名会话'}`)
  lines.push('')
  lines.push(`_导出时间：${dayjs().format('YYYY‑MM‑DD HH:mm')}_`)
  lines.push('')
  lines.push('---')
  lines.push('')
  lines.push('## 会话记录')
  lines.push('')

  msgs.forEach(m => {
    if (!m.content?.trim()) return          // 跳过空消息
    const time = dayjs(m.timestamp).format('YYYY‑MM‑DD HH:mm')
    if (m.role === 'user') {
      // 开一行日期
      lines.push(`### ${time}`)
      lines.push(`**你：** ${m.content.replace(/\n/g, '  \n')}`)
    } else if (m.role === 'assistant') {
      // 同一时间段继续写助手回复
      lines[lines.length - 1] += `  \n**助手：** ${m.content.replace(/\n/g, '  \n')}`
    }
  })
  lines.push('')
  return lines.join('\n')
}
// 导出会话
function handleExport() {
  if (!messages.value.length) {
    message.warning('当前会话为空，无法导出')
    return
  }
  const md = messagesToMarkdown(activeThreadTitle.value, messages.value)
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
  const fileName = `${activeThreadTitle.value || 'chat'}-${dayjs().format('YYYYMMDD-HHmm')}.md`
  saveAs(blob, fileName)
  message.success('已导出 Markdown')
}

// 绑定选择事件
function handleSelectThread(id) {
  selectThread(id)
}
</script>

<style scoped>
.chat-page {
  max-width: 800px;
  margin: 24px auto;
}
</style>
