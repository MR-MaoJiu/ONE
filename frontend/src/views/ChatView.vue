<template>
  <div class="chat-container">
    <div class="split-view">
      <!-- 聊天区域 -->
      <div class="chat-section">
        <div class="messages-container" ref="messagesContainer">
          <div v-for="(message, index) in messages" :key="index" 
               :class="['message', message.type === 'user' ? 'user-message' : 'system-message']">
            <div class="message-content">{{ message.content }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
        
        <div class="input-container">
          <textarea
            v-model="inputMessage"
            @keyup.enter.exact="sendMessage"
            @keyup.enter.shift.exact="newLine"
            placeholder="输入消息，按Enter发送，Shift+Enter换行"
            rows="3"
          ></textarea>
          <div class="button-group">
            <button @click="sendMessage" :disabled="!inputMessage.trim()">发送</button>
            <button @click="clearChat">清空对话</button>
            <button @click="toggleConnection">
              {{ isConnected ? '断开WebSocket' : '连接WebSocket' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 思考步骤区域 -->
      <AIThinkingViewer :thinking-steps="thinkingSteps" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useStore } from 'vuex'
import dayjs from 'dayjs'
import AIThinkingViewer from '../components/AIThinkingViewer.vue'

const store = useStore()
const inputMessage = ref('')
const messagesContainer = ref(null)

// 从store获取消息列表和连接状态
const messages = computed(() => store.state.messages)
const isConnected = computed(() => store.state.isConnected)
const thinkingSteps = computed(() => store.state.thinkingSteps)

// 在组件挂载时初始化WebSocket连接
onMounted(() => {
  store.dispatch('initWebSocket')
})

// 监听消息列表变化，自动滚动到底部
watch(messages, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
})

// 发送消息
async function sendMessage() {
  if (!inputMessage.value.trim()) return
  
  try {
    // 清空思考步骤
    store.dispatch('clearThinkingSteps')
    
    if (isConnected.value) {
      // 使用WebSocket发送
      await store.dispatch('sendWebSocketMessage', {
        content: inputMessage.value
      })
    } else {
      // 使用HTTP发送
      await store.dispatch('sendMessage', {
        content: inputMessage.value
      })
    }
    
    // 清空输入框
    inputMessage.value = ''
  } catch (error) {
    console.error('发送消息失败:', error)
    alert(error.message)
  }
}

// 处理换行
function newLine(e) {
  e.preventDefault()
  inputMessage.value += '\n'
}

// 清空聊天记录
function clearChat() {
  if (confirm('确定要清空聊天记录吗？')) {
    store.dispatch('clearMessages')
  }
}

// 切换WebSocket连接
function toggleConnection() {
  if (isConnected.value) {
    store.state.wsConnection?.close()
  } else {
    store.dispatch('initWebSocket')
  }
}

// 格式化时间
function formatTime(timestamp) {
  return dayjs(timestamp).format('HH:mm:ss')
}
</script>

<style scoped>
.chat-container {
  height: 100vh;
  padding: 20px;
  box-sizing: border-box;
  background: #f5f5f5;
}

.split-view {
  display: flex;
  gap: 20px;
  height: 100%;
}

.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  max-width: 80%;
  padding: 12px;
  border-radius: 8px;
  position: relative;
}

.user-message {
  align-self: flex-end;
  background: #1976d2;
  color: white;
}

.system-message {
  align-self: flex-start;
  background: #f5f5f5;
  color: #333;
}

.message-content {
  word-break: break-word;
  white-space: pre-wrap;
}

.message-time {
  font-size: 0.8em;
  color: #888;
  margin-top: 4px;
  text-align: right;
}

.input-container {
  padding: 20px;
  border-top: 1px solid #eee;
}

textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  font-size: 1em;
  margin-bottom: 12px;
}

.button-group {
  display: flex;
  gap: 12px;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: #1976d2;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}

button:hover:not(:disabled) {
  background: #1565c0;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .split-view {
    flex-direction: column;
  }
  
  .chat-section, .thinking-section {
    height: 50vh;
  }
}
</style> 