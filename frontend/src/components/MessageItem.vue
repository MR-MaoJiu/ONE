<template>
  <div :class="['message', message.type === 'user' ? 'user-message' : 'system-message']">
    <div class="message-content">
      <div v-if="message.type === 'system' && !contentLoaded" class="loading">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
      <div v-else v-html="formattedContent"></div>
    </div>
    <div class="message-time">{{ formatTime(message.timestamp) }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import dayjs from 'dayjs'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const md = new MarkdownIt({
  breaks: true,
  linkify: true
})

const contentLoaded = ref(false)

onMounted(() => {
  // 模拟加载延迟
  if (props.message.type === 'system') {
    setTimeout(() => {
      contentLoaded.value = true
    }, 100)
  } else {
    contentLoaded.value = true
  }
})

// 格式化消息内容
const formattedContent = computed(() => {
  if (!props.message.content) return ''
  const rendered = md.render(props.message.content)
  return DOMPurify.sanitize(rendered)
})

// 格式化时间
const formatTime = (timestamp) => {
  return dayjs(timestamp).format('HH:mm:ss')
}
</script>

<style scoped>
.message {
  padding: 8px 12px;
  margin: 4px 0;
  border-radius: 8px;
  max-width: 80%;
  word-break: break-word;
  transition: opacity 0.3s;
}

.user-message {
  background: linear-gradient(135deg, #00ff9d 0%, #00a8ff 100%);
  color: #1a1a1a;
  margin-left: auto;
}

.system-message {
  background: #1a1a1a;
  color: #e0e0e0;
  border: 1px solid rgba(0, 255, 157, 0.2);
  margin-right: auto;
}

.message-content {
  font-size: 14px;
  line-height: 1.5;
}

.message-time {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  text-align: right;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  padding: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #666;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

:deep(pre) {
  background-color: #2a2a2a;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

:deep(code) {
  font-family: monospace;
  background-color: #2a2a2a;
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