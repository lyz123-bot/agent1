<template>
  <div class="input-container" :class="{ focused }">
    <!-- 隐藏的文件选择 input -->
    <input
      ref="fileInput"
      type="file"
      multiple
      class="file-input"
      @change="onFilesSelected"
    />

    <!-- 文件预览区域 -->
    <div v-if="files.length > 0" class="file-previews">
      <div v-for="(file, index) in files" :key="index" class="file-preview">
        <div class="file-info">
          <PaperClipOutlined class="file-icon" />
          <div class="file-details">
            <div class="file-name" :title="file.name">
              {{ truncateFileName(file.name) }}
            </div>
            <div class="file-size">{{ formatFileSize(file.size) }}</div>
          </div>
        </div>
        <a-button
          type="text"
          size="small"
          class="file-remove"
          @click.stop="removeFile(index)"
        >
          <CloseOutlined />
        </a-button>
      </div>
    </div>

    <a-textarea
      ref="textareaRef"
      v-model:value="text"
      placeholder="输入您的问题…（Shift+Enter 换行，Enter 发送）"
      :auto-size="{ minRows: 1, maxRows: 4 }"
      @focus="focused = true"
      @blur="focused = false"
      @keydown.enter.exact.prevent="onKeydown"
      class="input-area"
    />

    <div class="input-actions">
      <!-- 文件上传按钮 -->
      <a-tooltip title="添加附件">
        <a-button
          type="text"
          :disabled="sending"
          @click="fileInput.click()"
        >
          <PaperClipOutlined />
        </a-button>
      </a-tooltip>

      <!-- 发送按钮 -->
      <a-tooltip title="发送消息">
        <a-button
          type="primary"
          :disabled="!canSend"
          @click="onSend"
          class="send-button"
        >
          <SendOutlined />
        </a-button>
      </a-tooltip>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { 
  SendOutlined, 
  PaperClipOutlined,
  CloseOutlined 
} from '@ant-design/icons-vue'

const props = defineProps({
  modelValue: String,
  sending: Boolean
})
const emit = defineEmits(['update:modelValue', 'send', 'attach-files'])

const text = ref(props.modelValue || '')
const focused = ref(false)
const textareaRef = ref(null)
const fileInput = ref(null)
const files = ref([]) // 存储上传的文件

// 计算属性：是否可以发送（有文本或有文件）
const canSend = computed(() => {
  return (text.value.trim() || files.value.length > 0) && !props.sending
})

// 同步外部 v-model
watch(text, val => {
  emit('update:modelValue', val)
})

/**
 * 处理按键：纯 Enter 发送，Shift+Enter 插入换行（默认行为）
 */
async function onKeydown(e) {
  // 由于 .enter.exact.prevent 修饰符已阻止默认换行，只需处理发送逻辑
  if (canSend.value) {
    await onSend()
  }
}

// 点击发送
async function onSend() {
  const msg = text.value.trim()

  // 如果有文件，先触发附加文件事件
  if (files.value.length > 0) {
    emit('attach-files', files.value)
  }

  // 发送文本消息（即使为空，也可能只有文件）
  emit('send', msg)

  // 清空输入和文件
  text.value = ''
  files.value = []

  await nextTick()
  // 聚焦回输入框
  const el = textareaRef.value.$el.querySelector('textarea')
  el.focus()
}

// 处理选中文件
function onFilesSelected() {
  const selectedFiles = Array.from(fileInput.value.files)
  if (selectedFiles.length) {
    files.value = [...files.value, ...selectedFiles]
    fileInput.value.value = '' // 重置，以便再次选同一文件
  }
}

// 移除文件
function removeFile(index) {
  files.value.splice(index, 1)
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 截断长文件名
function truncateFileName(name, maxLength = 30) {
  if (name.length <= maxLength) return name
  const extensionIndex = name.lastIndexOf('.')
  if (extensionIndex === -1) return name.substring(0, maxLength) + '...'
  const namePart = name.substring(0, extensionIndex)
  const extension = name.substring(extensionIndex)
  if (namePart.length <= maxLength - 3) return name
  return namePart.substring(0, maxLength - 3 - extension.length) + '...' + extension
}
</script>

<style scoped>
.input-container {
  position: sticky;
  bottom: 0;
  background: rgba(13, 19, 32, 0.92);
  backdrop-filter: blur(12px);
  padding: 14px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.input-container.focused {
  border-top-color: rgba(22, 119, 255, 0.3);
  box-shadow: 0 -4px 24px rgba(22, 119, 255, 0.08);
}

.file-input {
  display: none;
}

.file-previews {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 4px;
}

.file-preview {
  display: flex;
  align-items: center;
  background: rgba(22, 119, 255, 0.12);
  border-radius: 10px;
  padding: 8px 12px;
  border: 1px solid rgba(22, 119, 255, 0.25);
  transition: all 0.2s;
}

.file-preview:hover {
  background: rgba(22, 119, 255, 0.18);
  border-color: rgba(22, 119, 255, 0.4);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #69b1ff;
  font-size: 16px;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-size: 12px;
  font-weight: 500;
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.9);
}

.file-size {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.file-remove {
  margin-left: 8px;
  color: rgba(255, 255, 255, 0.5) !important;
}

.file-remove:hover {
  color: #ff7875 !important;
}

/* 输入框：深色玻璃（TextArea 包装器 + 内部 textarea） */
:deep(.input-area.ant-input-outlined),
:deep(.input-area.ant-input) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 14px !important;
  transition: border-color 0.2s, box-shadow 0.2s;
}

:deep(.input-area .ant-input),
:deep(.input-area textarea) {
  background: transparent !important;
  border: none !important;
  padding: 10px 16px !important;
  color: #fff !important;
  resize: none;
}

:deep(.input-area .ant-input::placeholder),
:deep(.input-area textarea::placeholder) {
  color: #fff !important;
}

:deep(.input-area:hover .ant-input-outlined),
:deep(.input-area:hover) {
  border-color: rgba(255, 255, 255, 0.15) !important;
}

:deep(.input-area.ant-input-focused),
:deep(.input-area:focus-within) {
  border-color: rgba(22, 119, 255, 0.5) !important;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.15) !important;
}

.input-actions {
  display: flex;
  gap: 8px;
  align-self: flex-end;
}

.input-actions :deep(.ant-btn) {
  color: rgba(255, 255, 255, 0.6) !important;
}

.input-actions :deep(.ant-btn:hover:not(:disabled)) {
  color: rgba(255, 255, 255, 0.9) !important;
  background: rgba(22, 119, 255, 0.15) !important;
}

.send-button {
  border-radius: 12px !important;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%) !important;
  border: none !important;
  color: #fff !important;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.35);
  transition: transform 0.2s, box-shadow 0.2s;
}

.send-button:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(22, 119, 255, 0.45) !important;
}

@media (max-width: 768px) {
  .file-name {
    max-width: 120px;
  }
  .input-actions {
    gap: 4px;
  }
}
</style>
