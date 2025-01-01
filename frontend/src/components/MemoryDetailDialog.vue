<template>
  <div class="memory-detail-dialog" v-if="show" @click.self="close">
    <div class="dialog-content">
      <div class="dialog-header">
        <h3>记忆详情</h3>
        <button class="close-btn" @click="close">×</button>
      </div>
      <div class="dialog-body">
        <div class="detail-item">
          <div class="label">创建时间</div>
          <div class="value">{{ formatTime(memory.timestamp) }}</div>
        </div>
        <div class="detail-item">
          <div class="label">类型</div>
          <div class="value">{{ memory.type || '未分类' }}</div>
        </div>
        <div class="detail-item">
          <div class="label">内容</div>
          <div class="value content" v-html="formattedContent"></div>
        </div>
        <div class="detail-item" v-if="memory.metadata">
          <div class="label">元数据</div>
          <pre class="value metadata">{{ JSON.stringify(memory.metadata, null, 2) }}</pre>
        </div>
        <div class="detail-item" v-if="memory.api_results">
          <div class="label">API 调用结果</div>
          <pre class="value api-results">{{ JSON.stringify(memory.api_results, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import dayjs from 'dayjs'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  memory: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:show'])

const md = new MarkdownIt({
  breaks: true,
  linkify: true
})

const formattedContent = computed(() => {
  if (!props.memory.content) return ''
  const rendered = md.render(props.memory.content)
  return DOMPurify.sanitize(rendered)
})

const formatTime = (timestamp) => {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

const close = () => {
  emit('update:show', false)
}
</script>

<style scoped>
.memory-detail-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog-content {
  background: #2a2a2a;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 150, 255, 0.15);
}

.dialog-header {
  padding: 16px;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-header h3 {
  margin: 0;
  color: #e0e0e0;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e0e0e0;
}

.dialog-body {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.detail-item {
  margin-bottom: 16px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.label {
  font-size: 14px;
  color: #888;
  margin-bottom: 4px;
}

.value {
  color: #e0e0e0;
  line-height: 1.5;
}

.content {
  white-space: pre-wrap;
  background: #1a1a1a;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #333;
}

.metadata, .api-results {
  font-family: monospace;
  background: #1a1a1a;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  border: 1px solid #333;
  margin: 0;
}

:deep(pre) {
  background: #1a1a1a;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

:deep(code) {
  font-family: monospace;
  background: #1a1a1a;
  padding: 2px 4px;
  border-radius: 4px;
}

:deep(a) {
  color: #00ff9d;
  text-decoration: none;
}

:deep(a:hover) {
  text-decoration: underline;
}

:deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}
</style> 