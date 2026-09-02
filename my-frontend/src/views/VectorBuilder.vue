<template>
  <div class="vdb-container">
    <a-page-header title="向量数据库管理" sub-title="上传文档以进行向量化处理，支持批量操作" class="page-header">
      <template #extra>
        <a-button type="primary" @click="showHelpModal">
          <template #icon>
            <QuestionCircleOutlined />
          </template>
          使用指南
        </a-button>
      </template>
    </a-page-header>

    <a-tabs v-model:activeKey="activeTab" class="vdb-tabs">
      <!-- 上传文档 Tab -->
      <a-tab-pane key="upload" tab="上传文档">
        <a-card class="upload-card" :bordered="false">
          <a-row :gutter="24">
            <!-- 上传区域 -->
            <a-col :xl="12" :lg="24" :md="24" :sm="24" :xs="24">
              <a-card title="文件上传" :head-style="{ border: 'none', padding: '0 0 16px', background: 'transparent' }"
                :body-style="{ padding: 0, background: 'transparent' }" class="upload-area">
                <a-upload-dragger multiple :file-list="fileList" :before-upload="beforeUpload" :custom-request="noop"
                  @remove="confirmRemove" :show-upload-list="false" class="dragger" :disabled="uploading">
                  <div class="upload-content">
                    <div class="upload-icon">
                      <CloudUploadOutlined class="upload-dragger-icon" />
                    </div>
                    <p class="ant-upload-text">拖拽文件到此处或点击上传</p>
                    <p class="ant-upload-hint">
                      支持 PDF, DOCX, TXT, CSV 格式，单个文件不超过 50MB
                    </p>
                    <a-button type="primary" size="large" style="margin-top: 16px">
                      <template #icon>
                        <UploadOutlined />
                      </template>
                      选择文件
                    </a-button>
                  </div>
                </a-upload-dragger>

                <div class="upload-actions">
                  <a-space>
                    <a-button type="primary" @click="uploadAll" :loading="uploading" :disabled="!hasPendingFiles"
                      size="large">
                      <template #icon>
                        <CloudUploadOutlined />
                      </template>
                      开始上传
                    </a-button>
                    <a-button @click="clearAll" :disabled="!fileList.length || uploading" size="large">
                      <template #icon>
                        <ClearOutlined />
                      </template>
                      清空列表
                    </a-button>
                  </a-space>
                </div>
              </a-card>

              <a-alert v-if="hasPendingFiles" class="pending-tip-alert" message="提示"
                description="请点击「开始上传」按钮处理选中的文件" type="info" show-icon />
            </a-col>

            <!-- 本地列表（模拟） -->
            <a-col :xl="12" :lg="24" :md="24" :sm="24" :xs="24">
              <a-card title="文件列表" :head-style="{ border: 'none', padding: '0 0 16px' }"
                :body-style="{ padding: 0, background: 'transparent' }" class="file-list-card">
                <div class="file-list-header">
                  <a-input-search v-model:value="searchText" placeholder="搜索文件名" allow-clear @search="onSearch"
                    style="width: 300px" />

                  <div class="stats">
                    <a-tag color="blue">总数：{{ fileList.length }}</a-tag>
                    <a-tag color="green">已完成：{{ doneCount }}</a-tag>
                    <a-tag color="red">失败：{{ failedCount }}</a-tag>
                  </div>
                </div>

                <div class="table-container">
                  <a-table :data-source="filteredList" :row-key="record => record.uid" :loading="uploading"
                    :pagination="paginationConfig" class="file-table">
                    <a-table-column title="文件名" dataIndex="name" key="name">
                      <template #default="{ record }">
                        <div class="file-name-cell">
                          <FileIcon :type="getFileType(record.name)" />
                          <a-tooltip :title="record.name" placement="topLeft">
                            <span class="file-name">{{ formatFileName(record.name) }}</span>
                          </a-tooltip>
                        </div>
                      </template>
                    </a-table-column>

                    <a-table-column title="大小" dataIndex="size" key="size" width="120">
                      <template #default="{ text }">
                        {{ formatFileSize(text) }}
                      </template>
                    </a-table-column>

                    <a-table-column title="状态" key="status" width="140">
                      <template #default="{ record }">
                        <a-tag v-if="record.status !== 'uploading'" :color="getStatusColor(record.status)">
                          {{ getStatusText(record.status) }}
                        </a-tag>
                      </template>
                    </a-table-column>

                    <a-table-column title="进度" key="percent" width="180">
                      <template #default="{ record }">
                        <a-progress v-if="record.status === 'uploading'" :percent="Math.round(record.percent)"
                          :stroke-color="getProgressColor(record.percent)" size="small" />
                        <span v-else-if="record.status === 'success'">
                          <CheckCircleOutlined style="color: #52c41a; margin-right: 5px" />
                          完成
                        </span>
                        <span v-else-if="record.status === 'error'">
                          <CloseCircleOutlined style="color: #f5222d; margin-right: 5px" />
                          失败
                        </span>
                        <span v-else>等待上传</span>
                      </template>
                    </a-table-column>

                    <a-table-column title="操作" key="actions" width="120">
                      <template #default="{ record }">
                        <a-button type="text" :icon="h(DeleteOutlined)" @click="confirmRemove(record)"
                          :disabled="uploading" />
                      </template>
                    </a-table-column>
                  </a-table>
                </div>
              </a-card>
            </a-col>
          </a-row>
        </a-card>

        <!-- 帮助模态框 -->
        <a-modal v-model:open="helpVisible" title="向量数据库使用指南" width="800px" :footer="null"
          wrap-class-name="locator-modal-dark">
          <div class="help-content">
            <a-steps direction="vertical" :current="3">
              <a-step title="文件准备">
                <template #description>
                  <p>准备需要处理的文档文件：</p>
                  <ul>
                    <li>支持 PDF、DOCX、TXT、CSV 格式</li>
                    <li>单个文件大小不超过 50MB</li>
                    <li>确保文件内容清晰可读</li>
                  </ul>
                </template>
              </a-step>
              <a-step title="上传文件">
                <template #description>
                  <p>通过拖拽或点击上传区域添加文件：</p>
                  <ul>
                    <li>支持批量上传多个文件</li>
                    <li>上传前可查看文件列表</li>
                    <li>点击"开始上传"处理所有文件</li>
                  </ul>
                </template>
              </a-step>
              <a-step title="处理与构建">
                <template #description>
                  <p>文件上传后将自动进行向量化处理：</p>
                  <ul>
                    <li>文本内容会被提取并分割为片段</li>
                    <li>每个片段将转换为向量表示</li>
                    <li>向量数据存储到向量数据库中</li>
                  </ul>
                </template>
              </a-step>
              <a-step title="使用向量数据">
                <template #description>
                  <p>向量化完成后即可使用：</p>
                  <ul>
                    <li>在智能对话中检索相关知识</li>
                    <li>用于文档相似度分析</li>
                    <li>支持语义搜索和推荐</li>
                  </ul>
                </template>
              </a-step>
            </a-steps>
          </div>
        </a-modal>

        <!-- 文件预览模态框 -->
        <a-modal v-model:open="previewVisible" :title="previewTitle" width="80%" :footer="null"
          wrap-class-name="locator-modal-dark">
          <div v-if="currentPreview" class="preview-container">
            <div class="preview-header">
              <div class="file-info">
                <FileIcon :type="getFileType(currentPreview.name)" large />
                <div>
                  <h3>{{ currentPreview.name }}</h3>
                  <div class="file-meta">
                    <span>{{ formatFileSize(currentPreview.size) }}</span>
                    <span>上传时间：{{ currentPreview.uploadTime || '刚刚' }}</span>
                  </div>
                </div>
              </div>

              <a-button type="primary" @click="processFile(currentPreview)">
                <template #icon>
                  <CodeOutlined />
                </template>
                构建向量
              </a-button>
            </div>

            <div class="preview-content">
              <div v-if="previewLoading" class="loading-container">
                <a-spin tip="加载文件内容..." />
              </div>

              <div v-else class="preview-body">
                <h4>文件预览</h4>
                <div class="preview-text">
                  <p>这是文件预览区域。实际应用中，这里将显示文件内容。</p>
                  <p>对于 PDF 文件，会显示文档预览；对于文本文件，会显示文本内容；对于 CSV 文件，会显示表格视图。</p>
                </div>
              </div>
            </div>
          </div>
        </a-modal>
      </a-tab-pane>

      <!-- 管理已入库文档 Tab -->
      <a-tab-pane key="manage" tab="已入库文档">
        <a-card class="stored-panel-card">
          <div class="stored-header">
            <a-space>
              <a-input-search v-model:value="storedSearchText" placeholder="搜索来源文件或文档哈希" allow-clear
                @search="fetchFiles" style="width: 250px" />
              <a-button type="primary" @click="fetchFiles" :loading="storedLoading">
                刷新列表
              </a-button>
            </a-space>

          </div>

          <a-table class="stored-table" :data-source="filteredStoredList" :row-key="record => record.doc_hash"
            :pagination="storedPagination" :loading="storedLoading">
            <a-table-column title="来源文件" dataIndex="source" key="source" />
            <a-table-column title="Chunk ID" dataIndex="chunk_id" key="chunk_id" width="80" />
            <a-table-column title="文档哈希" dataIndex="doc_hash" key="doc_hash" />
            <a-table-column title="操作" key="actions" width="120">
              <template #default="{ record }">
                <a-space size="small">
                  <a-button type="link" @click="previewChunk(record)">查看</a-button>
                  <a-popconfirm title="确定删除此文档片段？" @confirm="deleteChunk(record.doc_hash)">
                    <a-button type="link" danger>删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </a-table-column>
          </a-table>
        </a-card>

        <!-- Chunk 预览模态 -->
        <a-modal v-model:open="chunkPreviewVisible" title="Chunk 预览" width="60%" :footer="null"
          wrap-class-name="locator-modal-dark">
          <pre class="chunk-preview-pre">{{ currentChunk.page_content }}</pre>
        </a-modal>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup>
import { ref, computed, reactive, h, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  CloudUploadOutlined,
  UploadOutlined,
  ClearOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  QuestionCircleOutlined,
  CodeOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { vdbUpload, vdbList, vdbDelete } from '@/api'

// 用户权限（暂未使用）
const userStore = useUserStore()

// Tabs 控制
const activeTab = ref('upload')

// 上传状态
const fileList = ref([])
const searchText = ref('')
const uploading = ref(false)
const helpVisible = ref(false)
const previewVisible = ref(false)
const previewLoading = ref(false)
const currentPreview = ref(null)

// 管理列表状态
const storedLoading = ref(false)
const storedList = ref([])
const storedSearchText = ref('')
const filteredStoredList = computed(() => {
  const txt = storedSearchText.value.trim().toLowerCase()
  if (!txt) return storedList.value
  return storedList.value.filter(item =>
    item.source.toLowerCase().includes(txt) ||
    item.doc_hash.toLowerCase().includes(txt)
  )
})
const storedTotal = ref(0)
const storedPagination = reactive({
  current: 1,
  pageSize: 6,
  total: 0,
  showSizeChanger: false,
  showQuickJumper: false,
  showTotal: total => `共 ${total} 条`,
  onChange: (page, pageSize) => {
    storedPagination.current = page
    storedPagination.pageSize = pageSize
    fetchFiles()
  }
})
const currentChunk = ref({})
const chunkPreviewVisible = ref(false)

// 分页配置
const paginationConfig = reactive({
  pageSize: 5,
  hideOnSinglePage: false,
  showSizeChanger: false,
  showQuickJumper: false,
  size: 'default'
})

// 上传 Tab 计算属性
const filteredList = computed(() => {
  const txt = searchText.value.trim().toLowerCase()
  return fileList.value.filter(i => i.name.toLowerCase().includes(txt))
})
const doneCount = computed(() => fileList.value.filter(i => i.status === 'success').length)
const failedCount = computed(() => fileList.value.filter(i => i.status === 'error').length)
const hasPendingFiles = computed(() => fileList.value.some(i => i.status === 'pending'))
const previewTitle = computed(() => currentPreview.value ? `文件预览 - ${currentPreview.value.name}` : '文件预览')

// 辅助：文件类型/颜色/格式化
function getFileType(name) {
  const ext = name.split('.').pop().toLowerCase()
  return ['pdf', 'doc', 'docx', 'txt', 'csv', 'xlsx'].includes(ext) ? ext : 'default'
}
function getFileColor(type) {
  const map = { pdf: '#f5222d', doc: '#1890ff', docx: '#1890ff', txt: '#52c41a', csv: '#faad14', xlsx: '#faad14', default: '#bfbfbf' }
  return map[type] || map.default
}
function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024, sizes = ['B', 'KB', 'MB', 'GB'], i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}
function formatFileName(name) {
  const max = 10; return name.length > max ? name.slice(0, max - 3) + '...' : name
}
function getStatusText(s) { return { pending: '等待上传', uploading: '上传中', success: '已完成', error: '失败' }[s] || '未知' }
function getStatusColor(s) { return { pending: 'blue', uploading: 'orange', success: 'green', error: 'red' }[s] || 'default' }
function getProgressColor(p) { return p < 30 ? '#1890ff' : p < 70 ? '#52c41a' : '#faad14' }

// no-op 拦截
function noop() { }

// 上传前验证
function beforeUpload(file) {
  if (file.size / 1024 / 1024 > 50) { message.error(`${file.name} 超过 50MB`); return false }
  const ext = file.name.split('.').pop().toLowerCase(), valid = ['pdf', 'doc', 'docx', 'txt', 'csv', 'xlsx']
  if (!valid.includes(ext)) { message.error(`${file.name} 不支持的类型`); return false }
  fileList.value.push({ uid: file.uid, name: file.name, size: file.size, file, percent: 0, status: 'pending', uploadTime: new Date().toLocaleTimeString() })
  return false
}

// 批量上传到后端
async function uploadAll() {
  if (!hasPendingFiles.value) { message.warning('没有待上传文件'); return }
  uploading.value = true
  const files = fileList.value.map(i => i.file)
  try {
    const { task_id } = await vdbUpload(files)
    message.success(`上传成功，任务ID：${task_id}`)
    fileList.value.forEach(i => { if (i.status === 'pending') { i.status = 'success'; i.percent = 100 } })
  } catch (e) {
    message.error(`上传失败：${e.message}`)
    fileList.value.forEach(i => { if (i.status === 'pending') i.status = 'error' })
  } finally { uploading.value = false }
}

// 构建向量（模拟）
function processFile(item) {
  if (item.status !== 'success') { message.warning('请先上传'); return }
  message.loading({ content: `正在构建向量: ${item.name}`, key: 'proc' })
  setTimeout(() => message.success({ content: `向量构建完成: ${item.name}`, key: 'proc' }), 2000)
}

// 删除本地列表项
function confirmRemove(item) {
  Modal.confirm({
    title: '确认删除？',
    content: `删除 "${item.name}"？`,
    okText: '删除', okType: 'danger', cancelText: '取消',
    onOk() { fileList.value = fileList.value.filter(f => f.uid !== item.uid); message.success('删除成功') }
  })
}

// 清空本地列表
function clearAll() {
  Modal.confirm({
    title: '确认清空？',
    content: '清空所有已成功上传记录？',
    okText: '清空', okType: 'danger', cancelText: '取消',
    onOk() { fileList.value = fileList.value.filter(f => f.status === 'success'); message.success('已清空') }
  })
}

// 搜索
function onSearch(val) { searchText.value = val }

// 帮助
function showHelpModal() { helpVisible.value = true }

// —— 管理 Tab 方法 ——
// 拉列表
async function fetchFiles() {
  storedLoading.value = true
  try {
    const data = await vdbList()
    storedList.value = data
    storedPagination.total = data.length
  } catch (e) {
    message.error('拉取失败：' + e.message)
  } finally {
    storedLoading.value = false
  }
}
// 查看 chunk
function previewChunk(r) { currentChunk.value = r; chunkPreviewVisible.value = true }
// 删除 chunk
async function deleteChunk(hash) {
  try { await vdbDelete(hash); message.success('删除成功'); fetchFiles() }
  catch (e) { message.error('删除失败：' + e.message) }
}

// Tab 切换监听
watch(activeTab, key => {
  if (key === 'manage') fetchFiles()
})
</script>

<style scoped>
/* 与智能识图页一致的深色主内容区 */
.vdb-container {
  padding: 20px;
  background: #0a0f1a;
  min-height: 100%;
  color: rgba(255, 255, 255, 0.9);
  max-width: 1400px;
  margin: 0 auto;
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

.vdb-tabs {
  margin-top: 4px;
}
.vdb-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 16px;
}
.vdb-tabs :deep(.ant-tabs-tab) {
  color: rgba(255, 255, 255, 0.6);
}
.vdb-tabs :deep(.ant-tabs-tab-active .ant-tabs-tab-btn) {
  color: #fff;
}
.vdb-tabs :deep(.ant-tabs-ink-bar) {
  background: #1677ff;
}
.vdb-tabs :deep(.ant-tabs-nav::before) {
  border-color: rgba(255, 255, 255, 0.08);
}

.upload-card {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
.upload-card :deep(.ant-card-body) {
  padding: 0;
}

.upload-area,
.file-list-card {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
  margin-bottom: 24px;
  padding: 24px 28px !important;
}
.upload-area :deep(.ant-card-head),
.file-list-card :deep(.ant-card-head) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: #fff;
}
.upload-area :deep(.ant-card-head-title),
.file-list-card :deep(.ant-card-head-title) {
  color: #fff;
  font-weight: 600;
}
.upload-area :deep(.ant-card-body),
.file-list-card :deep(.ant-card-body) {
  color: rgba(255, 255, 255, 0.85);
}

.dragger :deep(.ant-upload-drag) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px dashed rgba(255, 255, 255, 0.15) !important;
  border-radius: 12px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.dragger :deep(.ant-upload-drag:hover:not(.ant-upload-disabled)) {
  border-color: rgba(22, 119, 255, 0.5) !important;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.15);
}

.dragger {
  padding: 48px 32px !important;
}

.upload-dragger-icon {
  font-size: 48px;
  color: #69b1ff;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-icon {
  margin-bottom: 16px;
}

.dragger :deep(.ant-upload-drag p.ant-upload-text),
.dragger :deep(.ant-upload-drag .ant-upload-text) {
  font-size: 16px;
  font-weight: 500;
  color: #fff !important;
  margin-bottom: 8px;
}
.dragger :deep(.ant-upload-drag p.ant-upload-hint),
.dragger :deep(.ant-upload-drag .ant-upload-hint) {
  color: rgba(255, 255, 255, 0.55) !important;
  text-align: center;
  max-width: 90%;
  margin-bottom: 16px;
}

.upload-actions {
  margin-top: 24px;
  text-align: center;
}
.upload-actions :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.35);
}
.upload-actions :deep(.ant-btn:not(.ant-btn-primary)) {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: rgba(255, 255, 255, 0.85) !important;
}
.upload-actions :deep(.ant-btn:not(.ant-btn-primary):hover:not(:disabled)) {
  border-color: rgba(22, 119, 255, 0.4) !important;
  color: #69b1ff !important;
}

.vdb-container :deep(.pending-tip-alert) {
  margin-top: 16px;
}
.vdb-container :deep(.ant-alert-info) {
  background: rgba(22, 119, 255, 0.12);
  border: 1px solid rgba(22, 119, 255, 0.35);
}
.vdb-container :deep(.ant-alert-message) {
  color: #fff;
}
.vdb-container :deep(.ant-alert-description) {
  color: rgba(255, 255, 255, 0.65);
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 16px;
}

.stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.vdb-container :deep(.ant-input-affix-wrapper),
.vdb-container :deep(.ant-input-search .ant-input-group .ant-input) {
  background: rgba(255, 255, 255, 0.06) !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
  color: rgba(255, 255, 255, 0.9) !important;
}
.vdb-container :deep(.ant-input::placeholder) {
  color: rgba(255, 255, 255, 0.35);
}
.vdb-container :deep(.ant-input-search-button) {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%) !important;
  border: none !important;
}

.table-container {
  display: flex;
  flex-direction: column;
  height: calc(100% - 60px);
  min-height: 300px;
}

.file-table {
  border-radius: 12px;
  overflow: hidden;
  flex: 1;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.file-table :deep(.ant-table-container) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.file-table :deep(.ant-table-body) {
  flex: 1;
  overflow-y: auto !important;
}

.file-table :deep(.ant-table),
.file-table :deep(.ant-table-cell) {
  background: transparent !important;
  color: rgba(255, 255, 255, 0.88) !important;
}
.file-table :deep(.ant-table-thead > tr > th) {
  background: rgba(255, 255, 255, 0.06) !important;
  color: rgba(255, 255, 255, 0.85) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  font-weight: 600;
}
.file-table :deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
}
.file-table :deep(.ant-table-tbody > tr:hover > td) {
  background: rgba(22, 119, 255, 0.08) !important;
}

.file-table :deep(.ant-pagination) {
  padding: 16px 0;
  margin-top: auto;
  background: rgba(10, 15, 26, 0.95);
  position: sticky;
  bottom: 0;
  z-index: 1;
}
.file-table :deep(.ant-pagination-item a),
.file-table :deep(.ant-pagination-prev button),
.file-table :deep(.ant-pagination-next button) {
  color: rgba(255, 255, 255, 0.75);
}
.file-table :deep(.ant-pagination-item-active) {
  border-color: #1677ff;
}
.file-table :deep(.ant-pagination-item-active a) {
  color: #69b1ff;
}

.file-name-cell {
  display: flex;
  align-items: center;
  min-height: 40px;
  gap: 8px;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
  color: rgba(255, 255, 255, 0.9);
}

.stored-panel-card {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
}
.stored-panel-card :deep(.ant-card-body) {
  color: rgba(255, 255, 255, 0.85);
}

.stored-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 16px;
}

.stored-table {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.stored-table :deep(.ant-table),
.stored-table :deep(.ant-table-cell) {
  background: transparent !important;
  color: rgba(255, 255, 255, 0.88) !important;
}
.stored-table :deep(.ant-table-thead > tr > th) {
  background: rgba(255, 255, 255, 0.06) !important;
  color: rgba(255, 255, 255, 0.85) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}
.stored-table :deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
}
.stored-table :deep(.ant-table-tbody > tr:hover > td) {
  background: rgba(22, 119, 255, 0.08) !important;
}
.stored-table :deep(.ant-pagination-item a),
.stored-table :deep(.ant-pagination-prev button),
.stored-table :deep(.ant-pagination-next button) {
  color: rgba(255, 255, 255, 0.75);
}
.stored-table :deep(.ant-pagination-item-active) {
  border-color: #1677ff;
}
.stored-table :deep(.ant-btn-link) {
  color: #69b1ff;
}
.stored-table :deep(.ant-btn-link.ant-btn-dangerous) {
  color: #ff7875;
}

.stored-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>