// src/api.js

import { useUserStore } from '@/stores/user'

const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

/** 从 Pinia/localStorage 读取 access & refresh token */
function readTokens() {
  try {
    const u = useUserStore()
    return { access: u.accessToken, refresh: u.refreshToken, store: u }
  } catch {
    return {
      access: localStorage.getItem('access') || '',
      refresh: localStorage.getItem('refresh') || '',
      store: null
    }
  }
}

/** 刷新 access token */
async function refreshAccess(refreshToken) {
  const res = await fetch(`${BASE}/accounts/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken }),
  })
  if (!res.ok) throw new Error('refresh 失败')
  const { access } = await res.json()
  return access
}

/** 一次性尝试带 token 的 fetch */
async function attemptFetch(path, options = {}, accessTk) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (accessTk) headers.Authorization = `Bearer ${accessTk}`

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  })
  return res
}

/** 通用带刷新能力的 fetch */
async function withAuthFetch(path, options = {}) {
  let { access, refresh, store } = readTokens()
  let res = await attemptFetch(path, options, access)

  if (res.status === 401 && refresh) {
    try {
      const newAccess = await refreshAccess(refresh)
      store?.setAccess(newAccess)
      localStorage.setItem('access', newAccess)
      res = await attemptFetch(path, options, newAccess)
    } catch {
      store?.logout?.()
      throw new Error('登录已过期，请重新登录')
    }
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`请求失败 ${res.status} ${res.statusText} ${text}`)
  }
  return res
}

// ———— 线程相关 ————

export async function listThreads() {
  const res = await withAuthFetch('/chat/threads/', { method: 'GET' })
  return res.json()
}

export async function createThread(title = '新会话') {
  const res = await withAuthFetch('/chat/threads/', {
    method: 'POST',
    body: JSON.stringify({ title }),
  })
  return res.json()
}

export async function deleteThread(threadId) {
  await withAuthFetch(`/chat/threads/${threadId}/delete/`, { method: 'DELETE' })
}

export async function updateThread(threadId, { title }) {
  const res = await withAuthFetch(`/chat/threads/${threadId}/`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  })
  return res.json()
}

// ———— 消息相关 ————

export async function listMessages(threadId, params = {}) {
  const qs = new URLSearchParams()
  if (params.before) qs.set('before', params.before)
  if (params.limit)  qs.set('limit', String(params.limit))

  const res = await withAuthFetch(
    `/chat/threads/${threadId}/messages/?${qs.toString()}`,
    { method: 'GET' }
  )
  return res.json()
}

export async function clearMessages(threadId) {
  await withAuthFetch(`/chat/threads/${threadId}/messages/`, { method: 'DELETE' })
}

// ———— 流式聊天 SSE ————

export async function streamChat(params, signal) {
  const options = {
    method: 'POST',
    headers: { Accept: 'text/event-stream' },
    body: JSON.stringify(params),
  }
  const res = await withAuthFetch('/chat/', { ...options, signal })

  const contentType = res.headers.get('Content-Type') || ''
  if (contentType.includes('application/json')) {
    const data = await res.json()
    return {
      async read() {
        const payload = { text: data.answer, thread_id: data.thread_id }
        return {
          value: new TextEncoder().encode(JSON.stringify(payload)),
          done: true
        }
      }
    }
  }

  if (!res.body) {
    throw new Error(`SSE 请求失败：${res.status} ${res.statusText}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  return {
    async read() {
      while (true) {
        const endIndex = buffer.indexOf('\n\n')
        if (endIndex !== -1) {
          const message = buffer.substring(0, endIndex)
          buffer = buffer.substring(endIndex + 2)
          if (message.startsWith('data:')) {
            const dataStr = message.substring(5).trim()
            try {
              const data = JSON.parse(dataStr)
              return { value: new TextEncoder().encode(JSON.stringify(data)), done: false }
            } catch (err) {
              console.error('解析SSE数据失败', err)
            }
          }
        } else {
          const { value, done } = await reader.read()
          if (done) {
            if (buffer.length > 0) {
              const lastData = buffer
              buffer = ''
              return { value: new TextEncoder().encode(JSON.stringify({ text: lastData })), done: false }
            }
            return { done: true }
          }
          buffer += decoder.decode(value, { stream: true })
        }
      }
    }
  }
}

// ====== 以下是修改后的 locatorUpload ======

/** 图片定位：上传单个文件，支持 token 刷新重试 */
export async function locatorUpload(file) {
  const form = new FormData()
  form.append('file', file)

  let { access, refresh, store } = readTokens()
  if (!access) {
    throw new Error('未授权，请先登录')
  }

  // 上传请求函数
  async function doUpload(token) {
    return await fetch(`${BASE}/locator/`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
      credentials: 'include'
    })
  }

  // 首次上传
  let res = await doUpload(access)

  // 如果未授权且有 refresh，尝试刷新并重试
  if (res.status === 401 && refresh) {
    try {
      const newAccess = await refreshAccess(refresh)
      store?.setAccess(newAccess)
      localStorage.setItem('access', newAccess)
      access = newAccess
      res = await doUpload(newAccess)
    } catch {
      store?.logout?.()
      throw new Error('登录已过期，请重新登录')
    }
  }

  // 最终检查
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`locator 上传失败 ${res.status} ${text}`)
  }

  return res.json()  // { filename, best_match }
}

/** 向量库批量上传：上传多个文件 */
export async function vdbUpload(files = []) {
  const form = new FormData()
  files.forEach(f => form.append('files', f))

  let { access, refresh, store } = readTokens()
  if (!access) {
    throw new Error('未授权，请先登录')
  }

  // 简单尝试一次上传
  let res = await fetch(`${BASE}/vdb/upload/`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${access}` },
    body: form,
    credentials: 'include'
  })

  // 不处理刷新逻辑，这里假设 admin 已登录
  if (res.status === 401) {
    throw new Error('未授权，请先登录')
  }
  if (res.status !== 202) {
    const text = await res.text().catch(() => '')
    throw new Error(`vdb 上传返回 ${res.status} ${text}`)
  }

  return res.json()
}

/** 向量库查询：GET /vdb/query/?q=...&top_k=... */
export async function vdbQuery(q, top_k = 5) {
  const qs = new URLSearchParams({ q, top_k: String(top_k) })
  const res = await withAuthFetch(`/vdb/query/?${qs}`, { method: 'GET' })
  return res.json()
}

/** 列出所有向量库条目 */
export async function vdbList() {
  const res = await withAuthFetch('/vdb/files/', { method: 'GET' })
  return res.json()
}

/** 删除单个 chunk */
export async function vdbDelete(doc_hash) {
  await withAuthFetch(`/vdb/files/${doc_hash}/`, { method: 'DELETE' })
}

/** 图像识别：上传单个文件，返回 { filename, result:{ type, confidence, image_url } } */
export async function recognizeUpload(file) {
  const form = new FormData()
  form.append('file', file)

  let { access, refresh, store } = readTokens()
  if (!access) throw new Error('未授权，请先登录')

  async function doUpload(token) {
    return fetch(`${BASE}/locator/recognize/`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
      credentials: 'include'
    })
  }

  let res = await doUpload(access)

  if (res.status === 401 && refresh) {
    try {
      const newAccess = await refreshAccess(refresh)
      store?.setAccess(newAccess)
      localStorage.setItem('access', newAccess)
      res = await doUpload(newAccess)
    } catch {
      store?.logout?.()
      throw new Error('登录已过期，请重新登录')
    }
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`recognize 上传失败 ${res.status} ${text}`)
  }
  return res.json()
}

/** 对话：caption + history + question → answer */
export async function chatWithCaption(payload) {
  // payload = { caption, history, question }
  const res = await withAuthFetch('/locator/chat/', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
  return res.json()          // { answer: "..." }
}

/** 生成图片描述：上传单张图片 → { caption }；locatorContext 为识别/定位结果 JSON（可选） */
export async function captionUpload(file, locatorContext = null) {
  const form = new FormData()
  form.append('file', file)
  if (locatorContext && typeof locatorContext === 'object') {
    form.append('locator_context', JSON.stringify(locatorContext))
  }

  // ---------- withAuthFetch 但不指定 Content-Type ----------
  let { access, refresh, store } = readTokens()

  async function doPost(token) {
    return fetch(`${BASE}/locator/caption/`, {
      method   : 'POST',
      headers  : token ? { Authorization: `Bearer ${token}` } : {},
      body     : form,
      credentials: 'include'
    })
  }

  let res = await doPost(access)

  if (res.status === 401 && refresh) {
    try {
      const newAccess = await refreshAccess(refresh)
      store?.setAccess(newAccess)
      localStorage.setItem('access', newAccess)
      res = await doPost(newAccess)
    } catch {
      store?.logout?.()
      throw new Error('登录已过期，请重新登录')
    }
  }

  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`caption 上传失败 ${res.status} ${txt}`)
  }
  return res.json()   // { caption: "..." }
}
export async function vqaChatUpload(file, payload) {
  // payload = { caption, history, question }
  const form = new FormData()
  form.append('file', file)
  form.append('meta', JSON.stringify(payload))

  let { access, refresh, store } = readTokens()
  if (!access) throw new Error('未授权，请登录')

  async function doPost(tok) {
    return fetch(`${BASE}/locator/chat/`, {
      method : 'POST',
      headers: tok ? { Authorization: `Bearer ${tok}` } : {},
      body   : form,
      credentials: 'include'
    })
  }
  let res = await doPost(access)

  if (res.status === 401 && refresh) {
    const newAccess = await refreshAccess(refresh)
    store?.setAccess(newAccess)
    localStorage.setItem('access', newAccess)
    res = await doPost(newAccess)
  }
  if (!res.ok) throw new Error(`chat 失败 ${res.status}`)
  return res.json()   // { answer }
}
