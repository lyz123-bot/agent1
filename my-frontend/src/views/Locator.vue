<template>
  <div class="locator-container">
    <!-- 页眉 -->
    <a-page-header title="智能识图" sub-title="通过图像识别确定地理位置 / 场景类型" class="page-header">
      <template #extra>
        <a-button type="primary" @click="showHelp">
          <template #icon><question-circle-outlined /></template>
          使用指南
        </a-button>
      </template>
    </a-page-header>

    <a-row :gutter="24" class="content-row">
      <!-- 左侧操作面板 -->
      <a-col :xs="24" :sm="24" :md="12" :lg="10" :xl="8">
        <a-card title="图像上传" class="upload-card">
          <div class="upload-section">
            <a-upload-dragger v-model:fileList="fileList" name="file" accept="image/*" :max-count="1" :action="null"
              :before-upload="beforeUpload" @change="handleUploadChange" class="upload-area">
              <p class="ant-upload-drag-icon"><cloud-upload-outlined /></p>
              <p class="ant-upload-text">点击或拖拽图片到此处上传</p>
              <p class="ant-upload-hint">支持 JPG/PNG/WebP，单张 ≤10 MB</p>
            </a-upload-dragger>

            <!-- 预览 -->
            <div v-if="previewImage" class="preview-container">
              <div class="image-wrapper">
                <img :src="previewImage" alt="预览图片" class="preview-image" />
                <div class="image-actions">
                  <a-tooltip title="删除图片">
                    <delete-outlined class="action-icon delete" @click="handleRemoveImage" />
                  </a-tooltip>
                  <a-tooltip title="增强图片">
                    <highlight-outlined class="action-icon" />
                  </a-tooltip>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <a-button type="primary" :disabled="!previewImage" :loading="locating" @click="handleLocate">
                <template #icon><environment-outlined /></template>开始定位
              </a-button>

              <a-button :disabled="!previewImage" :loading="recognizing" @click="handleRecognize">
                <template #icon><search-outlined /></template>开始识别
              </a-button>

              <a-button :disabled="!previewImage || captionLoading" :loading="captionLoading" @click="startChat">
                <template #icon><message-outlined /></template>开始对话
              </a-button>
            </div>
          </div>

          <a-divider dashed />

          <!-- 最近上传 -->
          <div class="history-section">
            <h3>最近上传</h3>
            <a-list :data-source="recentUploads" class="upload-history">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta :description="item.date">
                    <template #title>
                      <a @click="selectHistory(item)">{{ item.name }}</a>
                    </template>
                    <template #avatar>
                      <img :src="item.preview" class="history-thumb" />
                    </template>
                  </a-list-item-meta>
                  <template #actions>
                    <a-tooltip title="定位此图片">
                      <environment-outlined @click="locateHistory(item)" />
                    </a-tooltip>
                  </template>
                </a-list-item>
              </template>
            </a-list>
          </div>
        </a-card>
      </a-col>

      <!-- 右侧结果展示：定位/识别 两个 Tab -->
      <a-col :xs="24" :sm="24" :md="12" :lg="14" :xl="16">
        <a-card class="result-card">
          <a-tabs v-model:activeKey="activeTab">
            <!-- Tab 1：定位 -->
            <a-tab-pane key="location" tab="定位结果">
              <a-spin :spinning="locating" tip="正在分析图像并定位中...">
                <div v-if="resultData" class="result-container">
                  <div class="map-container">
                    <!-- 百度地图容器：有 AK 且已解析到坐标时显示 -->
                    <div v-show="mapReady" ref="mapContainerRef" id="baidu-map-container" class="baidu-map-inner"></div>
                    <!-- 未配置 AK 或地理编码中/失败时显示占位 -->
                    <div v-show="!mapReady" class="map-placeholder">
                      <div v-if="mapError" class="map-error-tip">{{ mapError }}</div>
                      <template v-else>
                        <div class="map-marker">
                          <environment-filled style="font-size: 36px; color: #1890ff" />
                          <div class="marker-pulse"></div>
                        </div>
                        <div class="map-actions">
                          <a-tooltip title="放大">
                            <plus-circle-outlined class="map-action-icon" />
                          </a-tooltip>
                          <a-tooltip title="缩小">
                            <minus-circle-outlined class="map-action-icon" />
                          </a-tooltip>
                          <a-tooltip title="卫星视图">
                            <radar-chart-outlined class="map-action-icon" />
                          </a-tooltip>
                          <a-tooltip title="路线规划">
                            <apartment-outlined class="map-action-icon" />
                          </a-tooltip>
                        </div>
                      </template>
                    </div>
                  </div>

                  <div class="location-details">
                    <div class="location-header">
                      <h3>位置信息</h3>
                      
                    </div>

                    <a-descriptions bordered :column="1" class="location-info">
                      <a-descriptions-item label="匹配图像">
                        {{ resultData.prediction.label }}
                      </a-descriptions-item>
                      <a-descriptions-item label="地点">
                        {{ campusDisplayLocation(resultData.prediction.location_text) }}
                      </a-descriptions-item>
                      <a-descriptions-item label="匹配分数">
                        {{ resultData.prediction.match_score }}
                      </a-descriptions-item>
                    </a-descriptions>

                    <div class="location-actions">
                      <a-button type="primary" @click="handleViewMatch">
                        <template #icon><environment-outlined /></template>
                        查看匹配图像
                      </a-button>
                    </div>
                  </div>
                </div>

                <div v-else class="empty-result">
                  <div class="empty-content">
                    <compass-outlined class="empty-icon" />
                    <h3>等待定位结果</h3>
                    <p>上传图片并点击“开始定位”</p>
                  </div>
                </div>
              </a-spin>
            </a-tab-pane>

            <!-- Tab 2：识别（与定位相同的数据：匹配图像 / 地点 / 分数，不含地图） -->
            <a-tab-pane key="recognition" tab="识别结果">
              <a-spin :spinning="recognizing" tip="正在分析图像…">
                <div v-if="recognitionResultData" class="result-container recognition-result-wrap">
                  <div class="location-details recognition-details">
                    <div class="location-header">
                      <h3>匹配信息</h3>
                    </div>
                    <a-descriptions bordered :column="1" class="location-info">
                      <a-descriptions-item label="匹配图像">
                        {{ recognitionResultData.prediction.label }}
                      </a-descriptions-item>
                      <a-descriptions-item label="地点">
                        {{ campusDisplayLocation(recognitionResultData.prediction.location_text) }}
                      </a-descriptions-item>
                      <a-descriptions-item label="匹配分数">
                        {{ recognitionResultData.prediction.match_score }}
                      </a-descriptions-item>
                    </a-descriptions>
                    <div class="location-actions">
                      <a-button type="primary" @click="handleViewMatchRecognition">
                        <template #icon><environment-outlined /></template>
                        查看匹配图像
                      </a-button>
                    </div>
                  </div>
                </div>

                <div v-else class="empty-result">
                  <div class="empty-content">
                    <search-outlined class="empty-icon" />
                    <h3>等待识别结果</h3>
                    <p>上传图片并点击「开始识别」（与定位同一套匹配，此处不展示地图）</p>
                  </div>
                </div>
              </a-spin>
            </a-tab-pane>
            <!-- 3. 对话 -->
            <a-tab-pane key="chat" tab="对话问答">
              <a-spin :spinning="captionLoading">
                <div v-if="chatMessages.length" class="chat-window">
                  <div v-for="m in chatMessages" :key="m.id" :class="['msg', m.role]">
                    <strong>{{ m.role === 'user' ? '你' : '助手' }}：</strong> {{ m.content }}
                  </div>
                </div>
                <div v-else class="empty-chat">点击“开始对话”生成图片描述后再聊天</div>

                <div class="chat-input">
                  <a-input-search v-model:value="chatInput" enter-button="发送" :loading="sending" @search="sendChat"
                    placeholder="向图像提问..." />
                </div>
              </a-spin>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>

    <!-- 使用指南 Modal -->
    <a-modal v-model:visible="helpVisible" title="智能识图使用指南" width="800px" :footer="null" wrap-class-name="locator-modal-dark">
      <div class="help-content">
        <a-steps direction="vertical" :current="3">
          <a-step title="上传图片">
            <template #description>
              <p>上传 JPG/PNG/WebP 格式图像，单张 ≤10 MB</p>
            </template>
          </a-step>
          <a-step title="开始定位或识别">
            <template #description>
              <p>点击按钮触发 AI 分析</p>
            </template>
          </a-step>
          <a-step title="查看结果">
            <template #description>
              <p>在对应页签中查看定位或识别结果</p>
            </template>
          </a-step>
        </a-steps>
      </div>
    </a-modal>

    <!-- 匹配图像预览 Modal -->
    <a-modal v-model:visible="showMatchModal" title="匹配图像预览" width="60%" :footer="null" centered destroy-on-close wrap-class-name="locator-modal-dark">
      <img :src="matchImageUrl" alt="匹配图像" class="modal-img" />
    </a-modal>

  </div>
</template>

<script setup>
/* ------------------------------------------------------------------ */
/* Imports */
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  CloudUploadOutlined,
  EnvironmentOutlined,
  EnvironmentFilled,
  DeleteOutlined,
  HighlightOutlined,
  QuestionCircleOutlined,
  PlusCircleOutlined,
  MinusCircleOutlined,
  RadarChartOutlined,
  ApartmentOutlined,
  SearchOutlined,
  MessageOutlined
} from '@ant-design/icons-vue'

import { locatorUpload, vqaChatUpload, captionUpload } from '@/api.js'

/** 匹配库图片等 API 根路径（与 api.js 一致，不含末尾 /） */
const API_BASE = (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api').replace(/\/$/, '')

/* ------------------------------------------------------------------ */
/* 上传 & 预览 */
const fileList = ref([])
const previewImage = ref('')
const recentUploads = ref([])

const beforeUpload = file => {
  const isImg = file.type.startsWith('image/')
  const isSize = file.size / 1024 / 1024 < 10
  if (!isImg) message.error('只能上传图片文件!')
  if (!isSize) message.error('图片大小不能超过10MB!')
  return false
}

function handleUploadChange(info) {
  fileList.value = info.fileList.slice(-1)
  if (fileList.value.length) {
    previewImage.value = URL.createObjectURL(info.fileList[0].originFileObj)
    resetResults()
  } else {
    previewImage.value = ''
    resetResults()
  }
}

function handleRemoveImage() {
  fileList.value = []
  previewImage.value = ''
  resetResults()
}

function resetResults() {
  destroyBaiduMap()
  resultData.value = null
  recognitionResultData.value = null
  captionText.value = ''
  chatMessages.value = []
}

/* ------------------------------------------------------------------ */
/* Tab / 弹窗 */
const activeTab = ref('location')
const helpVisible = ref(false)
const showMatchModal = ref(false)
const matchImageUrl = ref('')

/* ------------------------------------------------------------------ */
/* 1. 定位 */
const locating = ref(false)
const resultData = ref(null)

/* 2. 识别：与定位同一接口结果，仅展示文案无地图 */
const recognizing = ref(false)
const recognitionResultData = ref(null)

/* 地图与展示：位置限定在武汉理工大学马房山校区东院（武汉市） */
const LOC_CAMPUS = '武汉理工大学马房山校区东院'
const LOC_CITY_HINT = '武汉市'

/* 百度地图：优先从环境变量 VITE_BAIDU_MAP_AK 读取，否则使用项目配置的默认 AK */
const BAIDU_MAP_AK = import.meta.env.VITE_BAIDU_MAP_AK || 'W8yhdaYnLiu7aHZK616yphbauD0wbrYe'

/**
 * 地点统一为「武汉理工大学马房山校区东院」与匹配片段直接拼接，无括号、无「匹配参考」等分隔。
 * 若片段已以东院全名开头则原样返回；否则去掉片段首部与校区重复的前缀再拼接。
 */
function campusConcatLocation(fragment) {
  let f = (typeof fragment === 'string' ? fragment : '').trim().replace(/\s+/g, '')
  if (!f) return LOC_CAMPUS
  if (f.startsWith(LOC_CAMPUS)) return f
  const stripPrefixes = [
    LOC_CAMPUS,
    '武汉理工大学马房山校区',
    '马房山校区东院',
    '马房山东院',
    '东院',
    '武汉理工大学',
  ]
  for (const p of stripPrefixes) {
    if (p && f.startsWith(p)) {
      f = f.slice(p.length)
      break
    }
  }
  f = f.replace(/^[\s·\-—]+/, '')
  if (!f) return LOC_CAMPUS
  return `${LOC_CAMPUS}${f}`
}

function campusDisplayLocation(fragment) {
  return campusConcatLocation(fragment)
}

const mapContainerRef = ref(null)
const mapReady = ref(false)
const mapError = ref('')
let baiduMapInstance = null

/** 百度异步加载必须用 callback，否则 onload 时 BMap 往往尚未挂到 window（表现为「BMap 未加载」） */
let baiduMapScriptPromise = null

function loadBaiduMapScript() {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('仅浏览器环境可加载地图'))
  }
  if (window.BMap) return Promise.resolve()
  if (baiduMapScriptPromise) return baiduMapScriptPromise

  baiduMapScriptPromise = new Promise((resolve, reject) => {
    let settled = false
    let deadline = null
    const finish = (ok, err) => {
      if (settled) return
      settled = true
      if (deadline != null) window.clearTimeout(deadline)
      if (!ok) baiduMapScriptPromise = null
      if (ok) resolve()
      else reject(err)
    }

    const cbName = `__baiduMapCb_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
    window[cbName] = () => {
      try {
        delete window[cbName]
      } catch {
        window[cbName] = undefined
      }
      if (window.BMap) finish(true)
      else finish(false, new Error('BMap 未加载'))
    }

    const script = document.createElement('script')
    script.type = 'text/javascript'
    const ak = encodeURIComponent(BAIDU_MAP_AK)
    script.src = `https://api.map.baidu.com/api?v=3.0&ak=${ak}&s=1&callback=${cbName}`
    script.async = true
    script.onerror = () => {
      try {
        delete window[cbName]
      } catch {
        window[cbName] = undefined
      }
      finish(false, new Error('百度地图脚本加载失败'))
    }
    document.head.appendChild(script)

    deadline = window.setTimeout(() => {
      if (settled) return
      if (window.BMap) {
        try {
          delete window[cbName]
        } catch {
          window[cbName] = undefined
        }
        finish(true)
        return
      }
      finish(false, new Error('百度地图加载超时，请检查网络或 AK 是否有效'))
    }, 30000)
  })

  return baiduMapScriptPromise
}

function destroyBaiduMap() {
  if (baiduMapInstance) {
    baiduMapInstance.destroy()
    baiduMapInstance = null
  }
  mapReady.value = false
  mapError.value = ''
}

/**
 * 百度地图地理编码。参数须为与界面「地点」一致的完整检索串（调用方请传 campusConcatLocation(原始 location_text)）。
 * 不在此函数内再次拼接校区，避免与展示不一致或仅使用固定校区名。
 */
function initBaiduMapWithAddress(fullGeocodeAddress) {
  const addr = typeof fullGeocodeAddress === 'string' ? fullGeocodeAddress.trim() : ''
  if (!addr || !BAIDU_MAP_AK) {
    mapError.value = BAIDU_MAP_AK ? '暂无地点信息' : '请配置 VITE_BAIDU_MAP_AK 以显示地图'
    mapReady.value = false
    return
  }
  mapError.value = ''
  mapReady.value = false
  loadBaiduMapScript()
    .then(() => {
      nextTick(() => {
        if (!mapContainerRef.value) return
        const BMap = window.BMap
        const geocoder = new BMap.Geocoder()
        geocoder.getPoint(addr, point => {
          if (!point) {
            mapError.value = `无法解析地址「${addr}」，请检查地点名称`
            mapReady.value = false
            return
          }
          destroyBaiduMap()
          baiduMapInstance = new BMap.Map(mapContainerRef.value)
          baiduMapInstance.centerAndZoom(point, 16)
          baiduMapInstance.addOverlay(new BMap.Marker(point))
          baiduMapInstance.enableScrollWheelZoom(true)
          mapReady.value = true
        }, LOC_CITY_HINT)
      })
    })
    .catch(e => {
      mapError.value = e.message || '地图加载失败'
      mapReady.value = false
    })
}

async function resolveUploadFile() {
  let imgFile = fileList.value[0]?.originFileObj
  if (!imgFile) {
    const resp = await fetch(previewImage.value)
    if (!resp.ok) throw new Error('无法重新获取图片，请重新上传')
    const blob = await resp.blob()
    imgFile = new File([blob], 'history.jpg', { type: blob.type })
  }
  return imgFile
}

async function handleLocate() {
  if (!fileList.value.length) return
  locating.value = true
  activeTab.value = 'location'
  try {
    const imgFile = await resolveUploadFile()
    const { filename, best_match } = await locatorUpload(imgFile)
    if (!best_match) {
      message.warning('未找到任何匹配结果')
      resultData.value = null
    } else {
      resultData.value = {
        filename,
        confidence: best_match.confidence ?? 0,
        prediction: best_match
      }
      // 地图与「地点」展示同一套拼接串，避免只把固定校区名传给地理编码
      initBaiduMapWithAddress(campusConcatLocation(best_match.location_text ?? ''))
      // 最近上传
      if (recentUploads.value.length >= 10) recentUploads.value.pop()
      recentUploads.value.unshift({
        id: Date.now(),
        name: filename,
        preview: previewImage.value,
        date: new Date().toLocaleString()
      })
    }
  } catch (e) {
    message.error(e.message || '定位失败')
  } finally {
    locating.value = false
  }
}

function handleViewMatch() {
  const label = resultData.value?.prediction?.label
  if (!label) return
  matchImageUrl.value = `${API_BASE}/locator/db-image/${encodeURIComponent(label)}/`
  showMatchModal.value = true
}

function handleViewMatchRecognition() {
  const label = recognitionResultData.value?.prediction?.label
  if (!label) return
  matchImageUrl.value = `${API_BASE}/locator/db-image/${encodeURIComponent(label)}/`
  showMatchModal.value = true
}

async function handleRecognize() {
  if (!fileList.value.length) return
  recognizing.value = true
  activeTab.value = 'recognition'
  try {
    const imgFile = await resolveUploadFile()
    const { filename, best_match } = await locatorUpload(imgFile)
    if (!best_match) {
      message.warning('未找到任何匹配结果')
      recognitionResultData.value = null
    } else {
      recognitionResultData.value = {
        filename,
        confidence: best_match.confidence ?? 0,
        prediction: best_match
      }
      if (recentUploads.value.length >= 10) recentUploads.value.pop()
      recentUploads.value.unshift({
        id: Date.now(),
        name: filename,
        preview: previewImage.value,
        date: new Date().toLocaleString()
      })
    }
  } catch (e) {
    message.error(e.message || '识别失败')
    recognitionResultData.value = null
  } finally {
    recognizing.value = false
  }
}

/* ------------------------------------------------------------------ */
/* 3. 对话问答 */
const captionLoading = ref(false)
const captionText = ref('')     // 保存图片描述
const chatMessages = ref([])     // {id, role, content}
const chatInput = ref('')
const sending = ref(false)
let msgId = 0

/**
 * 去掉助手回复里常见的 Markdown 符号（*、#、`、链接、围栏代码等），便于纯文本阅读。
 */
function sanitizeAssistantMarkdown(raw) {
  if (raw == null || typeof raw !== 'string') return ''
  let s = raw.replace(/\r\n/g, '\n')
  // 围栏代码 ```lang ... ```
  s = s.replace(/```[\w\-]*\n?([\s\S]*?)```/g, (_, inner) => inner.trim())
  // 行内 `code`
  s = s.replace(/`([^`]+)`/g, '$1')
  // 链接与图片
  s = s.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
  s = s.replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
  // ATX 标题
  s = s.replace(/^#{1,6}\s+/gm, '')
  // 分隔线 --- / *** / ___
  s = s.replace(/^\s{0,3}(?:[-*_]\s*){3,}\s*$/gm, '')
  // 粗体 **...**（多轮剥离嵌套）
  for (let i = 0; i < 8; i++) {
    const next = s.replace(/\*\*([^*]+?)\*\*/g, '$1')
    if (next === s) break
    s = next
  }
  s = s.replace(/\*\*/g, '')
  // 单行内 *强调*（不含换行，避免误伤整段）
  s = s.replace(/\*([^*\n]+?)\*/g, '$1')
  // 列表行首 * - +
  s = s.replace(/^(\s*)[*+-]\s+/gm, '$1')
  // 剩余孤立 *（常见于未闭合或列表残留）
  s = s.replace(/\*+/g, '')
  // 下划线强调 __x__ _x_（保守：仅配对）
  s = s.replace(/__([^_]+?)__/g, '$1')
  s = s.replace(/(?<![\w])_([^_\n]+?)_(?![\w])/g, '$1')
  // 多余反引号
  s = s.replace(/`+/g, '')
  return s.replace(/\n{3,}/g, '\n\n').trim()
}

function addMsg(role, content) {
  const text = role === 'assistant' ? sanitizeAssistantMarkdown(content) : content
  chatMessages.value.push({ id: ++msgId, role, content: text })
}

/** 优先「识别结果」，否则「定位结果」，供 caption / 对话写入提示词 */
function getLocatorContextForPrompt() {
  const pack = recognitionResultData.value || resultData.value
  if (!pack?.prediction) return null
  const p = pack.prediction
  return {
    filename: pack.filename,
    label: p.label ?? '',
    location_text: p.location_text ?? '',
    match_score: p.match_score
  }
}

/* ---------- 开始对话（生成图片描述 + 初始化聊天） ---------- */
async function startChat() {
  if (!fileList.value.length) return            // 没有选中图片
  captionLoading.value = true                   // Spin
  activeTab.value = 'chat'

  try {
    /* 1️⃣  取得 File 对象
           - 正常上传：originFileObj 存在
           - 历史记录：只有 preview URL，需要 fetch → blob → File        */
    let imgFile = fileList.value[0].originFileObj
    if (!imgFile) {
      // 从预览地址重新拉取图片
      const resp = await fetch(previewImage.value)
      if (!resp.ok) throw new Error('reFetchFail')
      const blob = await resp.blob()
      imgFile = new File([blob], 'history.jpg', { type: blob.type })
    }

    /* 2️⃣  调用后端 /locator/caption/ 生成中文描述（附带识别/定位结果写入提示词） */
    const { caption } = await captionUpload(imgFile, getLocatorContextForPrompt())

    /* 3️⃣  初始化聊天窗口 */
    const cap = caption || '（未能生成描述）'
    chatMessages.value = []
    addMsg('assistant', cap)
    captionText.value = chatMessages.value[0]?.content ?? ''

  } catch (err) {
    if (err.message === 'reFetchFail') {
      message.error('无法重新获取图片，请尝试重新上传')
    } else {
      message.error(err.message || '生成描述失败')
    }
  } finally {
    captionLoading.value = false
  }
}


async function sendChat() {
  if (!chatInput.value.trim()) return
  const question = chatInput.value.trim()
  chatInput.value = ''
  addMsg('user', question)

  // history 不含 caption，也不含本轮问题
  const history = chatMessages.value.slice(1, -1)

  sending.value = true
  try {
    let imgFile = fileList.value[0]?.originFileObj
    if (!imgFile) {
      const resp = await fetch(previewImage.value)
      if (!resp.ok) throw new Error('reFetchFail')
      const blob = await resp.blob()
      imgFile = new File([blob], 'history.jpg', { type: blob.type })
    }
    const res = await vqaChatUpload(imgFile, {
      caption: captionText.value,
      history,
      question,
      locator_context: getLocatorContextForPrompt()
    })
    addMsg('assistant', res.answer || '（无回答）')
  } catch (e) {
    if (e.message === 'reFetchFail') {
      addMsg('assistant', '无法获取图片，请重新上传后再试')
    } else {
      addMsg('assistant', e.message || '出错了，稍后再试')
    }
  } finally {
    sending.value = false
  }
}

/* ------------------------------------------------------------------ */
/* 其它工具 */
function showHelp() { helpVisible.value = true }
function selectHistory(item) {
  fileList.value = [{ uid: item.id, name: item.name, originFileObj: null }]
  previewImage.value = item.preview
  resetResults()
  activeTab.value = 'location'
}
function locateHistory(item) {
  selectHistory(item)
  setTimeout(handleLocate, 400)
}

// 当定位结果变化时（如从历史记录切回）同步更新地图
watch(resultData, (val) => {
  if (val?.prediction) {
    initBaiduMapWithAddress(campusConcatLocation(val.prediction.location_text ?? ''))
  } else {
    destroyBaiduMap()
  }
}, { immediate: false })

onUnmounted(() => {
  destroyBaiduMap()
})
</script>


<style scoped>
.locator-container {
  padding: 20px;
  background: #0a0f1a;
  min-height: 100%;
  color: rgba(255, 255, 255, 0.9);
}

.page-header {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 20px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}
.page-header :deep(.ant-page-header-heading-title) {
  color: #fff;
}
.page-header :deep(.ant-page-header-heading-sub-title) {
  color: rgba(255, 255, 255, 0.55);
}
.page-header :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.35);
}

.content-row {
  margin-top: 16px;
}

.upload-card,
.result-card {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}
.upload-card :deep(.ant-card-head),
.result-card :deep(.ant-card-head) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: #fff;
}
.upload-card :deep(.ant-card-head-title),
.result-card :deep(.ant-card-head-title) {
  color: #fff;
  font-weight: 600;
}
.upload-card :deep(.ant-card-body),
.result-card :deep(.ant-card-body) {
  color: rgba(255, 255, 255, 0.85);
}

/* 上传拖拽区 */
.upload-area :deep(.ant-upload-drag) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px dashed rgba(255, 255, 255, 0.15) !important;
  border-radius: 12px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.upload-area :deep(.ant-upload-drag:hover) {
  border-color: rgba(22, 119, 255, 0.5) !important;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.15);
}
/* 覆盖 ant-design 默认深色文案（scoped 下需 :deep + 与组件同权重的选择器） */
.upload-area :deep(.ant-upload-drag .ant-upload-drag-icon) {
  font-size: 48px;
  color: #69b1ff;
  margin-bottom: 16px;
}
.upload-area :deep(.ant-upload-drag p.ant-upload-text),
.upload-area :deep(.ant-upload-drag .ant-upload-text) {
  font-size: 16px;
  font-weight: 500;
  color: #fff !important;
}
.upload-area :deep(.ant-upload-drag p.ant-upload-hint),
.upload-area :deep(.ant-upload-drag .ant-upload-hint) {
  color: #fff !important;
}
.upload-area :deep(.ant-upload-list-item),
.upload-area :deep(.ant-upload-list-item-name),
.upload-area :deep(a.ant-upload-list-item-name),
.upload-area :deep(.ant-upload-list-item .ant-upload-text-icon .anticon) {
  color: #fff !important;
}
.upload-area :deep(.ant-upload-list-item .ant-upload-list-item-actions) {
  color: rgba(255, 255, 255, 0.65);
}

.preview-container {
  margin-top: 24px;
  text-align: center;
}

.image-wrapper {
  position: relative;
  display: inline-block;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.preview-image,
.modal-img {
  max-width: 100%;
  max-height: 300px;
  display: block;
  margin: 0 auto;
  border-radius: 8px;
}

.image-actions {
  position: absolute;
  bottom: 10px;
  right: 10px;
  display: flex;
  gap: 10px;
}

.action-icon {
  background: rgba(0, 0, 0, 0.5);
  color: rgba(255, 255, 255, 0.9);
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.2s;
}

.action-icon:hover {
  transform: scale(1.08);
  background: rgba(22, 119, 255, 0.4);
  border-color: rgba(22, 119, 255, 0.5);
}

.action-icon.delete:hover {
  background: rgba(255, 77, 79, 0.4);
  color: #ff7875;
}

.action-buttons {
  margin-top: 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}
.action-buttons :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.35);
}
.action-buttons :deep(.ant-btn-primary:hover:not(:disabled)) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(22, 119, 255, 0.45) !important;
}
.action-buttons :deep(.ant-btn:not(.ant-btn-primary)) {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: rgba(255, 255, 255, 0.85) !important;
}
.action-buttons :deep(.ant-btn:not(.ant-btn-primary):hover:not(:disabled)) {
  border-color: rgba(22, 119, 255, 0.4) !important;
  color: #69b1ff !important;
}

:deep(.ant-divider-dashed) {
  border-color: rgba(255, 255, 255, 0.08);
}

.history-section {
  margin-top: 20px;
}
.history-section h3 {
  color: #fff;
  font-size: 15px;
  margin-bottom: 12px;
}
.upload-history :deep(.ant-list-item) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
  color: #fff !important;
}
.upload-history :deep(.ant-list-item-meta),
.upload-history :deep(.ant-list-item-meta-content) {
  color: #fff !important;
}
.upload-history :deep(.ant-list-item-meta-title),
.upload-history :deep(.ant-list-item-meta-title a) {
  color: #fff !important;
}
.upload-history :deep(.ant-list-item-meta-title a:hover) {
  color: #69b1ff !important;
}
.upload-history :deep(.ant-list-item-meta-description) {
  color: #fff !important;
}
.upload-history :deep(.ant-list-item-action) {
  color: rgba(255, 255, 255, 0.75) !important;
}
.upload-history :deep(.ant-list-item-action li:hover) {
  color: #69b1ff !important;
}

.history-thumb {
  width: 60px;
  height: 45px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.empty-result {
  height: 380px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-content h3 {
  color: rgba(255, 255, 255, 0.9);
  margin: 16px 0 8px;
}
.empty-content p {
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.empty-icon {
  font-size: 72px;
  color: rgba(22, 119, 255, 0.4);
}

.modal-img {
  max-width: 100%;
  max-height: 70vh;
}

/* Tabs 深色 */
.result-card :deep(.ant-tabs-nav) {
  margin-bottom: 16px;
}
.result-card :deep(.ant-tabs-tab) {
  color: rgba(255, 255, 255, 0.6);
}
.result-card :deep(.ant-tabs-tab-active .ant-tabs-tab-btn) {
  color: #fff;
}
.result-card :deep(.ant-tabs-ink-bar) {
  background: #1677ff;
}
.result-card :deep(.ant-tabs-nav::before) {
  border-color: rgba(255, 255, 255, 0.08);
}

.recognition-result-wrap {
  margin-top: 0;
}
.recognition-details {
  margin-top: 0;
}

.map-container {
  position: relative;
  height: 400px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.2);
}

.baidu-map-inner {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.map-error-tip {
  color: rgba(255, 255, 255, 0.7);
  padding: 20px;
  text-align: center;
  font-size: 14px;
}

.map-placeholder {
  height: 100%;
  background: linear-gradient(180deg, rgba(13, 19, 32, 0.95) 0%, rgba(10, 15, 26, 0.98) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.map-marker {
  position: relative;
  z-index: 10;
  animation: pulse 2s infinite;
}
.map-marker :deep(.anticon) {
  color: #69b1ff !important;
  filter: drop-shadow(0 0 12px rgba(22, 119, 255, 0.5));
}

.marker-pulse {
  position: absolute;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: rgba(22, 119, 255, 0.2);
  top: -32px;
  left: -32px;
  z-index: 1;
  animation: ripple 2s infinite;
}

.map-actions {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.map-action-icon {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s;
}

.map-action-icon:hover {
  color: #69b1ff;
  transform: scale(1.1);
}

.location-details {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  margin-top: 16px;
}

.location-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.location-header h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #fff;
}

.location-info :deep(.ant-descriptions-bordered .ant-descriptions-view) {
  border-color: rgba(255, 255, 255, 0.08) !important;
}
.location-info :deep(.ant-descriptions-item-label) {
  background: rgba(255, 255, 255, 0.06) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  color: rgba(255, 255, 255, 0.7) !important;
  font-weight: 500;
  width: 100px;
}
.location-info :deep(.ant-descriptions-item-content) {
  background: transparent !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  color: rgba(255, 255, 255, 0.9) !important;
}

.location-actions :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.35);
}

.help-content {
  padding: 10px 20px;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); }
}

@keyframes ripple {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(2); opacity: 0; }
}

@media (max-width: 992px) {
  .content-row { flex-direction: column; }
  .action-buttons { flex-direction: column; }
  .action-buttons :deep(.ant-btn) { width: 100%; }
}

/* 对话问答区域 */
.chat-window {
  max-height: 300px;
  overflow-y: auto;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  margin-bottom: 12px;
}

.msg {
  margin-bottom: 10px;
  color: rgba(255, 255, 255, 0.9);
}

.msg.user {
  text-align: right;
}

.chat-input :deep(.ant-input-search) {
  border-radius: 10px;
  overflow: hidden;
}
.chat-input :deep(.ant-input-affix-wrapper) {
  background: #fff !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
  color: rgba(0, 0, 0, 0.88) !important;
}
.chat-input :deep(.ant-input-affix-wrapper-focused),
.chat-input :deep(.ant-input-affix-wrapper:hover) {
  border-color: rgba(22, 119, 255, 0.55) !important;
}
.chat-input :deep(.ant-input) {
  color: #000 !important;
  background: #fff !important;
}
.chat-input :deep(.ant-input::placeholder) {
  color: rgba(0, 0, 0, 0.35);
}
.chat-input :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%) !important;
  border: none !important;
}

.empty-chat {
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  padding: 24px;
}
</style>
