<template>
  <a-layout class="chat-container">
    <!-- 侧边栏 -->
    <a-layout-sider v-if="showSidebar" class="sidebar" width="260">
      <div class="logo-container">
        <h2>DeepSeek-R1</h2>
      </div>
      <div class="threads-container">
        <a-button type="primary" class="new-thread-btn" @click="newThread">
          <template #icon><PlusOutlined/></template> 新建对话
        </a-button>
        <div class="thread-list">
          <div
            v-for="thread in threads"
            :key="thread.id"
            class="thread-item"
            :class="{ active: activeThreadId === thread.id }"
            @click="selectThread(thread.id)"
          >
            <MessageOutlined/>
            <span class="thread-title">{{ thread.title }}</span>
            <span class="thread-date">{{ formatDate(thread.created_at) }}</span>
          </div>
        </div>
      </div>
      <div class="settings">
        <a-button type="text"><SettingOutlined/> 设置</a-button>
      </div>
    </a-layout-sider>

    <!-- 主区域 -->
    <a-layout>
      <a-layout-header class="header">
        <div class="header-left">
          <a-button type="text" @click="toggleSidebar"><MenuOutlined/></a-button>
          <h1 class="thread-title">{{ activeThreadTitle }}</h1>
        </div>
        <div class="header-right">
          <a-button type="text" @click="deleteHistory"><DeleteOutlined/> 删除会话</a-button>
          <a-button type="text" @click="clearChat"><ClearOutlined/> 清空对话</a-button>
          <a-button type="text" @click="exportChat"><ExportOutlined/> 导出</a-button>
          <a-dropdown>
            <a-button type="text"><EllipsisOutlined/></a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item key="1"><UserOutlined/> 个人中心</a-menu-item>
                <a-menu-item key="2"><LogoutOutlined/> 退出登录</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <a-layout-content class="chat-content">
        <div
          ref="messagesContainer"
          class="messages-container"
          @scroll.passive="onScroll"
        >
          <!-- 欢迎卡 -->
          <div v-if="messages.length === 0 && !loadingMore" class="welcome-message">
            <div class="welcome-card">
              <div class="avatar-container">
                <a-avatar :size="80" style="background:#1677ff"><RobotOutlined/></a-avatar>
              </div>
              <h2>欢迎使用 DeepSeek-R1</h2>
              <p>这是一个基于 DeepSeek-R1-Distill-Qwen-1.5B 模型的智能助手</p>
              <div class="examples-container">
                <h3>您可以尝试以下问题：</h3>
                <div class="examples-grid">
                  <a-card
                    v-for="(ex, i) in examples"
                    :key="i"
                    class="example-card"
                    @click="selectExample(ex)"
                  >
                    <template #actions><SendOutlined/></template>
                    <p>{{ ex }}</p>
                  </a-card>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载更多 -->
          <div
            v-if="hasMore && messages.length > 0"
            class="load-more"
            @click="loadMessages"
          >
            {{ loadingMore ? '加载中...' : '加载更多历史消息' }}
          </div>

          <!-- 聊天消息 -->
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="message-wrapper"
          >
            <!-- 用户消息 -->
            <div v-if="msg.role === 'user'" class="message user-message">
              <div class="message-header">
                <a-avatar class="user-avatar"><UserOutlined/></a-avatar>
                <span class="sender-name">您</span>
                <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
              <div class="message-content">{{ msg.content }}</div>
            </div>

            <!-- AI 消息（合并自 message.vue）-->
            <div v-else class="message ai-message">
              <div class="message-header">
                <a-avatar style="background:#1677ff">
                  <MessageOutlined v-if="!msg.isStreaming" />
                  <LoadingOutlined v-else />
                </a-avatar>
                <span class="sender-name">DeepSeek-R1</span>
                <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
              <div class="message-content">
                <div v-if="msg.isStreaming" class="answer-content">
                  {{ msg.content }}<span class="streaming-cursor"></span>
                </div>
                <div v-else v-html="msg.rendered"></div>
              </div>
            </div>
          </div>

          <!-- 初次加载指示 -->
          <div
            v-if="loadingMore && messages.length === 0"
            class="message ai-message thinking"
          >
            <div class="message-content">加载中，请稍候...</div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-container">
          <div class="input-box">
            <a-textarea
              v-model:value="input"
              placeholder="输入您的问题..."
              :auto-size="{ minRows: 1, maxRows: 4 }"
              @pressEnter="sendMessage"
            />
            <div class="input-actions">
              <a-button type="text" title="添加文件"><PaperClipOutlined/></a-button>
              <a-button
                type="primary"
                class="send-btn"
                :disabled="!input.trim() || sending"
                @click="sendMessage"
              ><SendOutlined/></a-button>
            </div>
          </div>
          <div class="input-footer">
            <span>DeepSeek-R1 可以犯错，请验证重要信息</span>
            <a-button type="link" size="small">使用条款</a-button>
          </div>
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import {
  MenuOutlined,
  ClearOutlined,
  ExportOutlined,
  EllipsisOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  PlusOutlined,
  MessageOutlined,
  RobotOutlined,
  SendOutlined,
  DeleteOutlined,
  PaperClipOutlined,
  LoadingOutlined
} from '@ant-design/icons-vue'
import { marked } from 'marked'
import {
  listThreads,
  createThread,
  deleteThread,
  listMessages,
  clearMessages,
  streamChat,
  saveThreadId
} from '@/api'

// 线程列表
const threads = ref([])
const activeThreadId = ref(null)
const activeThreadTitle = ref('')

// 消息列表与分页
const messages = ref([])
const hasMore = ref(true)
const loadingMore = ref(false)
let beforeCursor = null

// 输入框与流控
const input = ref('')
const sending = ref(false)
const messagesContainer = ref(null)
const abortCtrl = ref(null)

// 侧栏与示例
const showSidebar = ref(true)
const examples = [
  '请解释量子计算的基本原理',
  '如何用 Python 实现快速排序算法？',
  'Transformer 架构的工作原理是什么？',
  '解释一下 JavaScript 中的闭包概念',
  '深度学习中如何防止过拟合？',
  '写一首关于春天的现代诗'
]

// 工具：滚动到底部
const scrollToBottom = () =>
  nextTick(() => {
    messagesContainer.value?.scrollTo({
      top: messagesContainer.value.scrollHeight
    })
  })

// 时间格式化
const formatTime = (d) =>
  new Date(d).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  })
const formatDate = (d) =>
  new Date(d).toLocaleDateString([], {
    month: 'short',
    day: 'numeric'
  })

// 加载会话线程
async function loadThreads() {
  try {
    const list = await listThreads()
    threads.value = list
    if (list.length) await selectThread(list[0].id)
  } catch {
    window.location.href = '/login'
  }
}

// 新建
async function newThread() {
  const t = await createThread('新会话')
  threads.value.unshift(t)
  await selectThread(t.id)
}

// 切换
async function selectThread(id) {
  activeThreadId.value = id
  activeThreadTitle.value =
    threads.value.find((t) => t.id === id)?.title || ''
  messages.value = []
  hasMore.value = true
  beforeCursor = null
  await loadMessages(true)
}

// 分页加载
async function loadMessages(reset = false) {
  if (loadingMore.value || (!hasMore.value && !reset)) return
  loadingMore.value = true
  if (reset) {
    messages.value = []
    beforeCursor = null
    hasMore.value = true
  }

  let logs = []
  try {
    logs = await listMessages(activeThreadId.value, {
      before: beforeCursor,
      limit: 40
    })
  } catch {
    loadingMore.value = false
    return
  }

  const page = []
  logs.reverse().forEach((l) => {
    page.push({
      id: `${l.id}-u`,
      role: 'user',
      content: l.prompt,
      timestamp: l.created_at,
      rendered: l.prompt,
      isStreaming: false
    })
    page.push({
      id: `${l.id}-a`,
      role: 'assistant',
      content: l.answer,
      timestamp: l.created_at,
      rendered: marked.parse(l.answer),
      isStreaming: false
    })
  })

  messages.value = reset
    ? page
    : [...messages.value, ...page]
  if (logs.length < 40) hasMore.value = false
  else beforeCursor = logs[logs.length - 1].id

  loadingMore.value = false
  scrollToBottom()
}

// 顶部滚动加载
function onScroll(e) {
  if (e.target.scrollTop === 0 && hasMore.value) loadMessages()
}

// 清空当前
function clearChat() {
  messages.value = []
  hasMore.value = true
  beforeCursor = null
}

// 删除线程
async function deleteHistory() {
  if (!activeThreadId.value) return
  await deleteThread(activeThreadId.value)
  const idx = threads.value.findIndex((t) => t.id === activeThreadId.value)
  if (idx !== -1) threads.value.splice(idx, 1)
  if (threads.value.length) await selectThread(threads.value[0].id)
  else await newThread()
}

// 发送并流式更新
async function sendMessage() {
  const text = input.value.trim()
  if (!text || sending.value) return

  // 1. 推入用户消息
  const userMsg = {
    id: `u-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: new Date(),
    rendered: text,
    isStreaming: false
  }
  messages.value = [...messages.value, userMsg]
  input.value = ''
  sending.value = true
  scrollToBottom()

  // 2. 推入 AI 占位
  let aiMsg = {
    id: `a-${Date.now()}`,
    role: 'assistant',
    content: '',
    rendered: '',
    isStreaming: true,
    timestamp: new Date()
  }
  messages.value = [...messages.value, aiMsg]
  scrollToBottom()

  // 3. 中止上次
  abortCtrl.value?.abort?.()
  abortCtrl.value = new AbortController()

  try {
    const reader = await streamChat(
      { message: text, thread_id: activeThreadId.value },
      abortCtrl.value.signal
    )

    // 4. 读取更新
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      if (!value) continue

      let data
      try {
        data = JSON.parse(new TextDecoder().decode(value))
      } catch {
        continue
      }
      if (data.text) {
        aiMsg.content += data.text
        aiMsg.rendered = aiMsg.content
        // 替换最后一条 AI 消息
        messages.value = [
          ...messages.value.slice(0, -1),
          { ...aiMsg }
        ]
        scrollToBottom()
      }
    }
  } catch (err) {
    aiMsg.content = `错误：${err.message}`
    aiMsg.rendered = aiMsg.content
    messages.value = [
      ...messages.value.slice(0, -1),
      { ...aiMsg }
    ]
    scrollToBottom()
  } finally {
    // 5. 结束，渲染 Markdown，关闭 streaming
    aiMsg.isStreaming = false
    aiMsg.rendered = marked.parse(aiMsg.content)
    messages.value = [
      ...messages.value.slice(0, -1),
      { ...aiMsg }
    ]
    await nextTick()
    sending.value = false
    scrollToBottom()
  }
}

// 辅助
function exportChat() { /* ... */ }
function toggleSidebar() { showSidebar.value = !showSidebar.value }
function selectExample(ex) { input.value = ex; sendMessage() }

// 初始化
onMounted(loadThreads)
</script>

<style scoped>

.chat-container {
  height: 100vh;
  background: #f0f2f5;
  display: flex;
}

.sidebar {
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.logo-container {
  padding: 20px 16px;
  border-bottom: 1px solid #e8e8e8;
}

.logo-container h2 {
  margin: 0;
  color: #1677ff;
  font-weight: 600;
}

.threads-container {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.new-thread-btn {
  width: 100%;
  margin-bottom: 16px;
}

.thread-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.thread-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
}

.thread-item:hover {
  background: #f5f7fa;
}

.thread-item.active {
  background: #e6f4ff;
}

.thread-title {
  font-weight: 500;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thread-date {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.settings {
  padding: 16px;
  border-top: 1px solid #e8e8e8;
}

.settings-btn {
  width: 100%;
  text-align: left;
}

.header {
  background: #fff;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e8e8e8;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.menu-btn {
  font-size: 16px;
}

.thread-title {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-content {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
  padding: 24px;
  background: #fafafa;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.welcome-message {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.welcome-card {
  max-width: 800px;
  text-align: center;
  padding: 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.avatar-container {
  margin-bottom: 24px;
}

.welcome-card h2 {
  font-size: 28px;
  margin-bottom: 16px;
  color: #1f1f1f;
}

.welcome-card p {
  font-size: 16px;
  color: #595959;
  margin-bottom: 32px;
}

.examples-container {
  margin: 40px 0;
}

.examples-container h3 {
  font-size: 18px;
  margin-bottom: 16px;
  color: #1f1f1f;
  text-align: center;
}

.examples-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  max-width: 700px;
  margin: 0 auto;
}

.example-card {
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 8px;
  text-align: left;
  height: 100%;
}

.example-card:hover {
  border-color: #1677ff;
  transform: translateY(-2px);
}

.example-card p {
  margin: 0;
  color: #1f1f1f;
}

.send-icon {
  color: #1677ff;
}

.capabilities {
  margin-top: 40px;
}

.capabilities h3 {
  font-size: 18px;
  margin-bottom: 16px;
  color: #1f1f1f;
  text-align: center;
}

.capabilities-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  max-width: 600px;
  margin: 0 auto;
}

.capability {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
}

.capability span {
  margin-top: 8px;
  font-size: 14px;
}

.messages-list {
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.message {
  border-radius: 12px;
  padding: 16px;
  position: relative;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.sender-name {
  margin: 0 12px;
  font-weight: 500;
}

.message-time {
  font-size: 12px;
  color: #8c8c8c;
}

.message-content {
  line-height: 1.6;
}

.user-message {
  background: #e6f4ff;
  align-self: flex-end;
  max-width: 80%;
  border-bottom-right-radius: 0;
}

.ai-message {
  background: #fff;
  border: 1px solid #e8e8e8;
  align-self: flex-start;
  max-width: 80%;
  border-bottom-left-radius: 0;
}

.ai-message.thinking .message-content {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #8c8c8c;
}

.message-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.streaming-content {
  display: inline-block;
}

.streaming-cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background-color: #1677ff;
  margin-left: 4px;
  animation: blink 1s infinite;
  vertical-align: text-bottom;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.input-container {
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  padding-top: 24px;
}

.input-box {
  position: relative;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #d9d9d9;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.input-box :deep(.ant-input) {
  border: none !important;
  box-shadow: none !important;
  padding: 16px;
  padding-right: 60px;
}

.input-actions {
  position: absolute;
  right: 16px;
  bottom: 16px;
  display: flex;
  gap: 8px;
}

.action-btn {
  color: #8c8c8c;
}

.send-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  padding: 8px 16px;
  font-size: 12px;
  color: #8c8c8c;
}

@media (max-width: 768px) {
  .sidebar {
    position: absolute;
    z-index: 100;
    height: 100%;
    transform: translateX(-100%);
    transition: transform 0.3s;
  }
  
  .sidebar.open {
    transform: translateX(0);
  }
  
  .examples-grid {
    grid-template-columns: 1fr;
  }
  
  .capabilities-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .user-message, .ai-message {
    max-width: 90%;
  }
}
</style>