<template>
  <div class="chat-container">
    <!-- 聊天区域 -->
    <div class="chat-section">
      <div class="messages" ref="messagesContainer">
        <div v-for="(message, index) in messages" :key="index" class="message" :class="message.type">
          <div class="message-content">{{ message.content }}</div>
          <div class="message-time">{{ formatTime(message.timestamp) }}</div>
        </div>
      </div>
      <div class="input-area">
        <input 
          v-model="inputMessage" 
          @keyup.enter="sendMessage"
          placeholder="输入消息..."
          class="message-input"
          :disabled="isAnalyzing"
        />
        <button @click="sendMessage" class="send-button" :disabled="isAnalyzing">
          {{ isAnalyzing ? '分析中...' : '发送' }}
        </button>
      </div>
    </div>

    <!-- 分析区域 -->
    <div class="analysis-section">
      <div class="analysis-header">
        <h3>分析过程</h3>
      </div>
      <div v-if="isAnalyzing" class="analysis-loading">
        <div class="loading-spinner"></div>
        <div class="loading-text">正在分析...</div>
      </div>
      <AnalysisViewer v-else-if="currentAnalysis" :analysis-steps="currentAnalysis" />
      <div v-else class="analysis-placeholder">
        在这里显示消息分析过程...
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import AnalysisViewer from '../components/AnalysisViewer.vue'
import axios from 'axios'

const messages = ref([])
const inputMessage = ref('')
const messagesContainer = ref(null)
const currentAnalysis = ref(null)
const isAnalyzing = ref(false)

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isAnalyzing.value) return

  // 添加用户消息
  messages.value.push({
    type: 'user',
    content: inputMessage.value,
    timestamp: new Date()
  })

  // 清空输入
  const messageText = inputMessage.value
  inputMessage.value = ''

  // 滚动到底部
  await scrollToBottom()

  try {
    // 开始分析
    isAnalyzing.value = true
    currentAnalysis.value = null

    // 发送聊天请求
    const response = await axios.post('/chat', {
      content: messageText,
      context: {
        current_query: messageText,
        history: messages.value.map(m => ({
          is_user: m.type === 'user',
          content: m.content,
          timestamp: m.timestamp
        }))
      }
    })

    if (response.data.analysis) {
      currentAnalysis.value = response.data.analysis
    }

    // 添加系统响应消息
    messages.value.push({
      type: 'system',
      content: response.data.response,
      timestamp: new Date()
    })

    // 滚动到底部
    await scrollToBottom()

  } catch (error) {
    console.error('发送消息失败:', error)
    messages.value.push({
      type: 'system',
      content: '抱歉，处理消息时出现错误。',
      timestamp: new Date()
    })
    await scrollToBottom()
  } finally {
    isAnalyzing.value = false
  }
}

onMounted(() => {
  // 初始化时滚动到底部
  scrollToBottom()
})
</script>

<style scoped>
.chat-container {
  width: 100%;
  height: 100vh;
  display: flex;
  background-color: #f5f5f5;
}

.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: white;
  border-right: 1px solid #e0e0e0;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
}

.message.user {
  align-self: flex-end;
  background-color: #1976d2;
  color: white;
}

.message.system {
  align-self: flex-start;
  background-color: #f5f5f5;
  color: #333;
}

.message-content {
  margin-bottom: 4px;
  word-break: break-word;
}

.message-time {
  font-size: 0.75rem;
  opacity: 0.7;
  position: absolute;
  bottom: -20px;
  right: 8px;
}

.input-area {
  padding: 20px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 12px;
}

.message-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.3s;
}

.message-input:focus {
  border-color: #1976d2;
}

.message-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.send-button {
  padding: 0 24px;
  background-color: #1976d2;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
  min-width: 100px;
}

.send-button:hover:not(:disabled) {
  background-color: #1565c0;
}

.send-button:disabled {
  background-color: #90caf9;
  cursor: not-allowed;
}

.analysis-section {
  width: 400px;
  background-color: white;
  border-left: 1px solid #e0e0e0;
  overflow-y: auto;
}

.analysis-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
  background-color: #fafafa;
}

.analysis-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
}

.analysis-loading {
  padding: 40px 20px;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 16px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1976d2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  color: #666;
  font-size: 0.9rem;
}

.analysis-placeholder {
  padding: 20px;
  color: #666;
  text-align: center;
  font-style: italic;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
  }

  .analysis-section {
    width: 100%;
    height: 300px;
    border-left: none;
    border-top: 1px solid #e0e0e0;
  }
}
</style> 