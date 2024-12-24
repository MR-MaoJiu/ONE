<template>
  <div class="chat-container">
    <!-- 聊天区域 -->
    <div class="main-section">
      <div class="chat-section">
        <div class="messages" ref="messagesContainer">
          <div v-for="(message, index) in messages" :key="index" class="message" :class="message.type">
            <div class="message-content">{{ message.content }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
        <div class="input-area">
          <textarea 
            v-model="inputMessage" 
            @keyup.enter.exact="sendMessage"
            @keydown.enter.exact.prevent
            placeholder="输入消息..."
            class="message-input"
            :disabled="isAnalyzing"
            rows="1"
            ref="messageInput"
            @input="adjustTextareaHeight"
          ></textarea>
          <button @click="sendMessage" class="send-button" :disabled="isAnalyzing">
            {{ isAnalyzing ? '思考中...' : '发送' }}
          </button>
        </div>
      </div>

      <!-- 分析区域 -->
      <div class="analysis-section">
        <div class="analysis-header">
          <h3>思考过程</h3>
        </div>
        <div v-if="isAnalyzing" class="analysis-loading">
          <div class="loading-spinner"></div>
          <div class="loading-text">正在思考...</div>
        </div>
        <AnalysisViewer v-else-if="currentAnalysis" :analysis-steps="currentAnalysis" />
        <div v-else class="analysis-placeholder">
          这里会显示AI的思考过程...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useStore } from 'vuex'
import AnalysisViewer from '../components/AnalysisViewer.vue'

const store = useStore()
const messages = computed(() => store.state.messages)
const inputMessage = ref('')
const messagesContainer = ref(null)
const messageInput = ref(null)
const isAnalyzing = ref(false)
const currentAnalysis = computed(() => store.state.currentAnalysis)

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

const adjustTextareaHeight = () => {
  const textarea = messageInput.value
  if (!textarea) return
  
  textarea.style.height = 'auto'
  textarea.style.height = textarea.scrollHeight + 'px'
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isAnalyzing.value) return

  // 开始分析
  isAnalyzing.value = true

  try {
    const messageData = {
      content: inputMessage.value.trim(),
      context: {
        current_query: inputMessage.value.trim(),
        history: messages.value.map(m => ({
          is_user: m.type === 'user',
          content: m.content,
          timestamp: m.timestamp
        }))
      }
    }

    // 发送消息
    await store.dispatch('sendMessage', messageData)
    
    // 清空输入
    inputMessage.value = ''
    messageInput.value.style.height = 'auto'

    // 滚动到底部
    await scrollToBottom()

  } catch (error) {
    console.error('发送消息失败:', error)
    // 显示错误消息
    store.commit('addMessage', {
      type: 'system',
      content: '抱歉，处理消息时出现错误。',
      timestamp: new Date().toISOString()
    })
  } finally {
    isAnalyzing.value = false
  }
}

onMounted(() => {
  // 初始化时滚动到底部
  scrollToBottom()
  // 开始新对话
  store.dispatch('startNewConversation')
})
</script>

<style scoped>
.chat-container {
  width: 100%;
  height: 100vh;
  background-color: #f5f5f5;
  padding: 20px;
  box-sizing: border-box;
}

.main-section {
  width: 100%;
  height: 100%;
  display: flex;
  gap: 20px;
  max-width: 1800px;
  margin: 0 auto;
}

.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
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
  line-height: 1.5;
  white-space: pre-wrap;
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
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s;
  resize: none;
  min-height: 24px;
  max-height: 150px;
  line-height: 1.5;
  font-family: inherit;
}

.message-input:focus {
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.1);
}

.message-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.send-button {
  padding: 12px 24px;
  background-color: #1976d2;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
  min-width: 100px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-button:hover:not(:disabled) {
  background-color: #1565c0;
}

.send-button:disabled {
  background-color: #90caf9;
  cursor: not-allowed;
}

.analysis-section {
  width: 500px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1976d2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  color: #666;
  font-size: 1rem;
}

.analysis-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 1rem;
  padding: 20px;
  text-align: center;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 1200px) {
  .main-section {
    flex-direction: column;
  }
  
  .analysis-section {
    width: 100%;
    height: 400px;
  }
}
</style> 