// src/stores/user.js
import { defineStore } from 'pinia'
import router from '@/router'

export const useUserStore = defineStore('user', {
  state: () => ({
    // 从 localStorage 恢复
    access : localStorage.getItem('access')  || '',
    refresh: localStorage.getItem('refresh') || '',
    role   : localStorage.getItem('role')    || ''   // 'user' | 'admin'
  }),

  getters: {
    isAuthed     : s => !!s.access,
    isAdmin      : s => s.role === 'admin',          // ★ 新增
    accessToken  : s => s.access,
    refreshToken : s => s.refresh
  },

  actions: {
    /**
     * 登录成功后调用。会同步写入 localStorage，
     * 以便页面刷新时仍保持登录状态。
     */
    login({ access, refresh, role }) {
      this.access  = access
      this.refresh = refresh
      this.role    = role
      localStorage.setItem('access',  access)
      localStorage.setItem('refresh', refresh)
      localStorage.setItem('role',    role)
    },

    /** 仅更新 access，用于刷新 token */
    setAccess(token) {
      this.access = token
      localStorage.setItem('access', token)
    },

    /** 退出登录：清空状态并跳转登录页 */
    logout() {
      this.access = ''
      this.refresh = ''
      this.role = ''
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      localStorage.removeItem('role')
      router.push('/login')
    }
  }
})
