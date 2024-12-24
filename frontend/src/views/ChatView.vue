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
            <button @click="clearChat" class="btn-secondary">清空对话</button>
            <button @click="toggleConnection" class="btn-secondary">
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
  height: calc(100vh - 60px); /* 减去导航栏的高度 */
  padding: 10px;
  box-sizing: border-box;
  background: #1a1a1a;
}

.split-view {
  display: flex;
  gap: 10px;
  height: 100%;
  max-height: 100%;
}

.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 150, 255, 0.15);
  overflow: hidden;
  max-height: 100%;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message {
  max-width: 85%;
  padding: 8px 12px;
  border-radius: 8px;
  position: relative;
}

.user-message {
  align-self: flex-end;
  background: linear-gradient(135deg, #00ff9d 0%, #00a8ff 100%);
  color: #1a1a1a;
}

.system-message {
  align-self: flex-start;
  background: #1a1a1a;
  color: #e0e0e0;
  border: 1px solid rgba(0, 255, 157, 0.2);
}

.message-content {
  word-break: break-word;
  white-space: pre-wrap;
  font-size: 0.95em;
  line-height: 1.4;
}

.message-time {
  font-size: 0.75em;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
  text-align: right;
}

.input-container {
  padding: 10px;
  border-top: 1px solid #333;
  background: #1a1a1a;
}

textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid rgba(0, 255, 157, 0.2);
  border-radius: 8px;
  resize: none;
  font-size: 0.95em;
  margin-bottom: 8px;
  background: #2a2a2a;
  color: #e0e0e0;
  transition: all 0.3s ease;
  max-height: 100px;
  min-height: 40px;
}

textarea:focus {
  outline: none;
  border-color: #00ff9d;
  box-shadow: 0 0 10px rgba(0, 255, 157, 0.2);
}

textarea::placeholder {
  color: #666;
}

.button-group {
  display: flex;
  gap: 8px;
}

button {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  background: linear-gradient(135deg, #00ff9d 0%, #00a8ff 100%);
  color: #1a1a1a;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 0.9em;
}

button.btn-secondary {
  background: transparent;
  border: 1px solid rgba(0, 255, 157, 0.2);
  color: #00ff9d;
}

button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 255, 157, 0.3);
}

button.btn-secondary:hover:not(:disabled) {
  background: rgba(0, 255, 157, 0.1);
}

button:disabled {
  background: #333;
  color: #666;
  cursor: not-allowed;
}

/* 自定义滚动条 */
.messages-container::-webkit-scrollbar {
  width: 4px;
}

.messages-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #00ff9d 0%, #00a8ff 100%);
  border-radius: 2px;
}

@media (max-width: 768px) {
  .chat-container {
    padding: 0;
    height: calc(100vh - 50px); /* 移动端导航栏更小 */
  }

  .split-view {
    flex-direction: column;
  }
  
  .chat-section {
    border-radius: 0;
    height: 60vh;
  }
  
  .thinking-section {
    height: 40vh;
  }

  .message {
    max-width: 90%;
  }

  .input-container {
    padding: 8px;
  }

  textarea {
    max-height: 80px;
  }

  button {
    padding: 6px 10px;
    font-size: 0.85em;
  }
}
</style> 