<template>
  <div class="thread-list" :class="{ collapsed }">
    <div class="logo" v-if="!collapsed">安应-Agent</div>
    <a-input-search
      v-if="!collapsed"
      placeholder="搜索会话"
      allowClear
      v-model:value="filter"
      class="search"
    />
    <div class="items">
      <div
        v-for="t in filtered"
        :key="t.id"
        class="item"
        :class="{ active: t.id === activeThreadId }"
        @click="$emit('select-thread', t.id)"
      >
        <!-- 左侧图标 + 标题+日期 -->
        <div class="info-wrapper">
          <MessageOutlined />
          <div v-if="!collapsed" class="info">
            <span class="title">{{ t.title }}</span>
            <span class="date">{{ formatDate(t.created_at) }}</span>
          </div>
        </div>

        <!-- 右侧操作：重命名 + 删除 -->
        <div class="actions" v-if="!collapsed">
          <EditOutlined
            class="icon rename"
            @click.stop="$emit('rename-thread', t.id)"
          />
          <DeleteOutlined
            class="icon delete"
            @click.stop="$emit('delete-thread', t.id)"
          />
        </div>
      </div>
    </div>

    <a-button
      type="primary"
      block
      class="new-btn"
      @click="$emit('new-thread')"
    >
      <template #icon><PlusOutlined/></template>
      新建对话
    </a-button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  MessageOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  threads: {
    type: Array,
    default: () => []
  },
  activeThreadId: String,
  collapsed: Boolean
})
const emit = defineEmits([
  'select-thread',
  'new-thread',
  'delete-thread',
  'rename-thread'
])

const filter = ref('')

const filtered = computed(() =>
  props.threads.filter(t =>
    t.title.includes(filter.value)
  )
)

const formatDate = d =>
  new Date(d).toLocaleDateString([], { month:'short', day:'numeric' })
</script>

<style scoped>
.thread-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
}

.logo {
  padding: 18px 16px;
  font-size: 17px;
  font-weight: 700;
  background: linear-gradient(135deg, #fff 0%, #a5d8ff 50%, #69b1ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

:deep(.search .ant-input-search) {
  margin: 0 12px 10px;
  width: calc(100% - 24px);
}
:deep(.search .ant-input-affix-wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.85);
}
:deep(.search .ant-input-affix-wrapper:hover),
:deep(.search .ant-input-affix-wrapper-focused) {
  border-color: rgba(22, 119, 255, 0.4);
  background: rgba(255, 255, 255, 0.06);
}
:deep(.search .ant-input) {
  background: transparent;
  color: rgba(255, 255, 255, 0.85);
}
:deep(.search .ant-input::placeholder) {
  color: rgba(255, 255, 255, 0.4);
}
:deep(.search .ant-input-prefix) {
  color: rgba(255, 255, 255, 0.5);
}

.items {
  flex: 1;
  overflow-y: auto;
  min-width: 0;
  padding: 4px 8px;
}

.item {
  position: relative;
  display: flex;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 10px;
  transition: background 0.2s, box-shadow 0.2s;
  margin-bottom: 2px;
}

.item:hover:not(.active) {
  background: rgba(255, 255, 255, 0.05);
}

.item.active {
  background: rgba(22, 119, 255, 0.18);
  box-shadow: 0 0 0 1px rgba(22, 119, 255, 0.25);
}

.item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: #1677ff;
  border-radius: 0 2px 2px 0;
}

.info-wrapper {
  display: flex;
  align-items: center;
  min-width: 0;
  color: rgba(255, 255, 255, 0.75);
}

.item.active .info-wrapper {
  color: rgba(255, 255, 255, 0.95);
}

.info {
  margin-left: 10px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.title {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: inherit;
}

.date {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 2px;
}

.actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.45);
  cursor: pointer;
  transition: color 0.2s, transform 0.2s;
  padding: 4px;
}

.icon:hover {
  color: #69b1ff;
  transform: translateY(-1px);
}

.icon.delete:hover {
  color: #ff7875;
}

.thread-list.collapsed .info,
.thread-list.collapsed .search,
.thread-list.collapsed .logo,
.thread-list.collapsed .actions {
  display: none;
}

.new-btn {
  margin: 12px;
  width: calc(100% - 24px);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-radius: 10px;
  height: 40px;
  font-weight: 500;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.35);
  transition: transform 0.2s, box-shadow 0.2s;
}

.new-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(22, 119, 255, 0.45) !important;
}
</style>
