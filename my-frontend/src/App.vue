<template>
  <a-config-provider>
    <!-- 主布局，仅当需要时渲染 -->
    <template v-if="showLayout">
      <a-layout class="app-layout">
        <!-- 左侧 Sider -->
        <!-- 折叠状态用 v-model:collapsed 与 collapsed ref 同步 -->
        <a-layout-sider
          v-model:collapsed="collapsed"
          width="220"
          :collapsedWidth="64"
          breakpoint="lg"
          class="app-sider"
        >
          <div class="sider-inner">
            <!-- 顶部 Logo -->
            <router-link to="/" class="logo">
              <span class="logo-glow"></span>
              <img :src="collegeIcon" alt="安应 Agent" class="logo-img" />
            </router-link>

            <!-- 动态菜单：管理员多 “向量数据库” -->
            <a-menu
              :selectedKeys="[route.path]"
              mode="inline"
              :items="menuItems"
              @click="onSelect"
              class="app-menu"
            />

            <!-- 底部用户区：头像 + 退出 -->
            <div class="sider-footer">
              <a-dropdown placement="topLeft" overlay-class-name="app-dropdown-overlay">
                <template #overlay>
                  <a-menu @click="onDropdown" class="dropdown-menu">
                    <a-menu-item key="logout">退出登录</a-menu-item>
                  </a-menu>
                </template>

                <div class="user-block">
                  <span class="user-avatar">{{ userInitial }}</span>
                  <span v-if="!collapsed" class="user-name">{{ userName }}</span>
                </div>
              </a-dropdown>
            </div>
          </div>
        </a-layout-sider>

        <!-- 右侧内容 -->
        <a-layout-content class="content">
          <!-- 只缓存 ChatPage，保持对话状态 -->
          <keep-alive include="ChatPage">
            <router-view class="view" />
          </keep-alive>
        </a-layout-content>
      </a-layout>
    </template>

    <!-- 无主布局页面（如登录页）直接渲染 -->
    <template v-else>
      <router-view />
    </template>
  </a-config-provider>
</template>

<script setup>
import { h, computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  MessageOutlined,
  CompassOutlined,
  DatabaseOutlined
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import collegeIcon from '@/assets/college_icon.png'

/* 基础实例 */
const router    = useRouter()
const route     = useRoute()
const user      = useUserStore()
const collapsed = ref(false) // Sider 折叠状态

/* 判断是否显示主布局（路由上 meta.layout !== false） */
const showLayout = computed(() => route.meta.layout !== false)

/* 公共菜单 */
const baseMenus = [
  { key: '/chat',    icon: () => h(MessageOutlined), label: '智能对话' },
  { key: '/locator', icon: () => h(CompassOutlined), label: '智能识图' }
]

/* 根据角色动态增删菜单 */
const menuItems = computed(() =>
  user.isAdmin
    ? [...baseMenus,
       { key: '/vdb', icon: () => h(DatabaseOutlined), label: '向量数据库' }]
    : baseMenus
)

/* 头像首字母 & 名称 */
const userInitial = computed(() => (user.isAdmin ? 'A' : 'U'))
const userName    = computed(() => (user.isAdmin ? '管理员' : '用户'))

/* 菜单导航 */
function onSelect ({ key }) {
  if (key !== route.path) router.push(key)
}

/* 下拉菜单（目前只有退出） */
function onDropdown ({ key }) {
  if (key === 'logout') user.logout()
}
</script>

<style scoped>
html, body, #app { height: 100%; margin: 0; }

/* 整体布局 */
.app-layout { height: 100vh; display: flex; }

/* ─────── 侧边栏容器 ─────── */
:deep(.app-sider.ant-layout-sider) {
  background: linear-gradient(180deg, #0d1320 0%, #0a0f1a 50%, #080c14 100%) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

:deep(.app-sider .ant-layout-sider-children) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sider-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

/* ─────── Logo ─────── */
.logo {
  position: relative;
  display: block;
  padding: 18px 20px;
  text-decoration: none;
  overflow: hidden;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  transition: background 0.2s ease;
}

.logo:hover {
  background: rgba(22, 119, 255, 0.06);
}

.logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 120%;
  height: 120%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(22, 119, 255, 0.15) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.25s ease;
  pointer-events: none;
}

.logo:hover .logo-glow {
  opacity: 1;
}

.logo-img {
  display: block;
  width: 100%;
  max-width: 140px;
  height: auto;
  position: relative;
  z-index: 1;
  filter: drop-shadow(0 0 8px rgba(22, 119, 255, 0.2));
}

/* ─────── 菜单（覆盖 Ant Design） ─────── */
.app-menu {
  flex: 1;
  margin-top: 8px;
  padding: 0 12px;
  border: none !important;
  background: transparent !important;
}

:deep(.app-menu.ant-menu-inline) {
  background: transparent !important;
}

:deep(.app-menu .ant-menu-item) {
  margin: 4px 0;
  height: 44px;
  line-height: 44px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.6);
  transition: color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}

:deep(.app-menu .ant-menu-item:hover) {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.05);
}

:deep(.app-menu .ant-menu-item-selected) {
  color: #fff;
  background: rgba(22, 119, 255, 0.2);
  box-shadow: 0 0 0 1px rgba(22, 119, 255, 0.3);
}

:deep(.app-menu .ant-menu-item-selected::after) {
  display: none;
}

:deep(.app-menu .ant-menu-item .anticon) {
  color: inherit;
  font-size: 16px;
}

:deep(.app-menu.ant-menu-inline.ant-menu-root .ant-menu-item) {
  padding-inline: 14px;
}

/* 折叠时 Logo 居中 */
:deep(.app-sider.ant-layout-sider-collapsed .logo) {
  padding: 18px 12px;
}

:deep(.app-sider.ant-layout-sider-collapsed .logo-img) {
  margin: 0 auto;
}

/* ─────── 底部用户区 ─────── */
.sider-footer {
  margin-top: auto;
  padding: 14px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.2);
}

.user-block {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 10px;
  transition: background 0.2s ease;
}

.user-block:hover {
  background: rgba(255, 255, 255, 0.05);
}

.user-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border-radius: 8px;
  box-shadow: 0 0 12px rgba(22, 119, 255, 0.4);
}

.user-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 下拉菜单样式与侧边栏一致 */
:deep(.dropdown-menu.ant-menu) {
  background: #0d1320 !important;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}

:deep(.dropdown-menu .ant-menu-item) {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.dropdown-menu .ant-menu-item:hover) {
  background: rgba(22, 119, 255, 0.15) !important;
  color: #fff;
}

/* ─────── 内容区 ─────── */
.content {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  background: #0a0f1a;
}

.view { height: 100%; }
</style>
