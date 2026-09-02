// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

/* 懒加载页面组件 */
const Home          = () => import('@/views/Home.vue')
const ChatPage      = () => import('@/views/ChatPage.vue')
const Locator       = () => import('@/views/Locator.vue')
const VectorBuilder = () => import('@/views/VectorBuilder.vue')
const Login         = () => import('@/views/Login.vue')

/* 路由表 */
const routes = [
  { path: '/login', name: 'Login', component: Login, meta: { layout: false } },

  { path: '/', name: 'Home', component: Home, meta: { requireAuth: true } },

  {
    path: '/chat',
    name: 'ChatPage',           // keep‑alive 依赖
    component: ChatPage,
    meta: { requireAuth: true }
  },
  {
    path: '/locator',
    name: 'Locator',
    component: Locator,
    meta: { requireAuth: true }
  },
  {
    path: '/vdb',
    name: 'VectorBuilder',
    component: VectorBuilder,
    meta: {
      requireAuth: true,
      requireRole: 'admin'      // ★ 仅管理员可访问
    }
  },

  { path: '/:pathMatch(.*)*', redirect: '/' }           // 兜底
]

/* 创建 Router 实例 */
const router = createRouter({
  history: createWebHistory(),
  routes
})

/* 全局守卫：鉴权 + 角色拦截 */
router.beforeEach((to, _from, next) => {
  const store = useUserStore()

  // 1) 未登录访问受限页面 → 跳登录
  if (to.meta.requireAuth && !store.isAuthed) {
    return next('/login')
  }

  // 2) 已登录访问 /login → 跳转首页
  if (to.path === '/login' && store.isAuthed) {
    return next('/')
  }

  // 3) 角色不符 → 拦截到默认页
  if (to.meta.requireRole && store.role !== to.meta.requireRole) {
    return next('/chat')
  }

  // 4) 其余情况正常放行
  next()
})

export default router
