<!-- ChatLayout.vue -->
<template>
  <a-layout class="chat-container">
    <!-- 可折叠侧边栏 -->
    <a-layout-sider
      :collapsed="collapsed"
      collapsible
      :trigger="null"
      @collapse="collapsed = $event"
      width="260"
      class="chat-sidebar"
    >
      <thread-list
        :threads="threads"
        :active-thread-id="activeThreadId"
        :collapsed="collapsed"
        @new-thread="onNewThread"
        @select-thread="onSelectThread"
        @delete-thread="onDeleteThread"
        @rename-thread="onRenameThread"  
      />

    </a-layout-sider>

    <a-layout>
      <!-- 粘性 Header -->
      <a-layout-header class="chat-header">
        <div class="header-left">
          <a-button type="text" class="menu-btn" @click="collapsed = !collapsed">
            <MenuOutlined />
          </a-button>
          <h1 class="thread-title">{{ activeThreadTitle }}</h1>
          <span class="thread-stats">共 {{ threads.length }} 个会话</span>
        </div>

        <a-dropdown overlay-class-name="chat-dropdown-overlay">
          <template #overlay>
            <a-menu @click="onMenuClick" class="chat-header-menu">
              <a-menu-item key="clear">
                <ClearOutlined /> 清空对话
              </a-menu-item>
              <a-menu-item key="export">
                <ExportOutlined /> 导出
              </a-menu-item>
            </a-menu>
          </template>
          <a-button type="text" class="more-btn">
            <EllipsisOutlined />
          </a-button>
        </a-dropdown>
      </a-layout-header>

      <a-layout-content class="chat-content-wrap">
        <message-list
          :messages="messages"
          :has-more="hasMore"
          :loading-more="loadingMore"
          @load-more="$emit('load-more')"
        >
          <!-- 功能型欢迎卡 -->
          <template #welcome>
            <div class="welcome-card-wrapper">
              <div class="welcome-card-upgraded">
                <div class="welcome-header">
                  <div class="logo"><img :src="loginIcon" alt="学院 Logo" /></div>
                  <h2>欢迎使用安全应急学院智能助手</h2>
                  <p>一个智能对话助手，试试下面这些话题：</p>
                </div>
                <div class="welcome-examples-upgraded">
                  <a-button
                    v-for="(ex, i) in examples"
                    :key="i"
                    class="example-pill"
                    @click="selectExample(ex)"
                    type="default"
                  >
                    {{ ex }}
                  </a-button>
                </div>
              </div>
            </div>
          </template>
        </message-list>
        <input-box v-model="input" :sending="sending" @send="onSend" />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref } from 'vue'
import {
  MenuOutlined,
  EllipsisOutlined,
  SettingOutlined,
  RobotOutlined,
  ClearOutlined,
  ExportOutlined
} from '@ant-design/icons-vue'
import loginIcon from '@/assets/login_icon.jpg'
import ThreadList from './ThreadList.vue'
import MessageList from './MessageList.vue'
import InputBox from './InputBox.vue'

const props = defineProps({
  threads: Array,
  activeThreadId: String,
  activeThreadTitle: String,
  messages: Array,
  hasMore: Boolean,
  loadingMore: Boolean,
})
const emit = defineEmits([
  'select-thread',
  'new-thread',
  'load-more',
  'send',
  'delete-thread',
  'rename-thread',   // 只发事件，不弹窗
  'clear-messages',
  'export'
])

const collapsed = ref(false)
const input = ref('')
const sending = ref(false)

// 示例问题
const examples = [
  '请介绍安全科学与应急管理学院',
  '如何用 Python 实现快速排序？',
  '深度学习中什么是过拟合，如何防止？',
  '写一首关于春天的现代诗',
  '安全应急学院师资状况如何?'
]

function onNewThread() {
  emit('new-thread')
}
function onSelectThread(id) {
  emit('select-thread', id)
}

// 左侧删除：确认框保留
import { Modal as AntdModal } from 'ant-design-vue'
function onDeleteThread(id) {
  AntdModal.confirm({
    title: '确认删除该会话？',
    content: '此操作不可撤销，确认要删除吗？',
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk() {
      emit('delete-thread', id)
    }
  })
}

// 左侧重命名：只发事件，不弹窗
function onRenameThread(id) {
  // 找到当前标题
  const thread = props.threads.find(t => t.id === id) || {}
  emit('rename-thread', { id, newName: thread.title })
}

function onSend(text) {
  emit('send', text)
}

function onMenuClick({ key }) {
  if (key === 'clear') emit('clear-messages')
  if (key === 'export') emit('export')
}

function selectExample(ex) {
  input.value = ex
  emit('send', ex)
}



</script>

<style scoped>
.chat-container {
  height: 100vh;
}

/* 会话页内嵌侧边栏：与主侧边栏风格一致 */
:deep(.chat-sidebar.ant-layout-sider) {
  background: linear-gradient(180deg, #0d1320 0%, #0a0f1a 50%, #080c14 100%) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

:deep(.chat-sidebar .ant-layout-sider-children) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 顶部标题栏 */
.chat-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(13, 19, 32, 0.85);
  backdrop-filter: blur(12px);
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  height: 56px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-btn,
.more-btn {
  color: rgba(255, 255, 255, 0.75) !important;
}
.menu-btn:hover,
.more-btn:hover {
  color: rgba(255, 255, 255, 0.95) !important;
  background: rgba(22, 119, 255, 0.12) !important;
}

.thread-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #fff;
}

.thread-stats {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
  margin-left: 6px;
}

.chat-content-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px);
  background: #0a0f1a;
}

/* 欢迎卡：深色玻璃拟态 */
.welcome-card-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: -60px;
}

.welcome-card-upgraded {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  max-width: 800px;
  width: 100%;
  padding: 32px 24px;
  text-align: center;
}

.welcome-header {
  margin-bottom: 24px;
}

.welcome-header .logo {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(22, 119, 255, 0.3);
  box-shadow: 0 0 24px rgba(22, 119, 255, 0.2);
}

.welcome-header .logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.welcome-header h2 {
  margin: 0;
  font-size: 22px;
  color: #fff;
  font-weight: 600;
}

.welcome-header p {
  margin: 8px 0 0;
  color: rgba(255, 255, 255, 0.55);
  font-size: 14px;
}

.welcome-examples-upgraded {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.example-pill {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
  padding: 10px 20px;
  font-size: 14px;
  transition: all 0.2s;
}

.example-pill:hover {
  background: rgba(22, 119, 255, 0.25);
  border-color: rgba(22, 119, 255, 0.4);
  color: #fff;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.25);
  transform: translateY(-2px);
}
</style>
