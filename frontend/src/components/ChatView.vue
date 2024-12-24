<template>
  <div class="chat-container">
    <!-- 聊天消息列表 -->
    <div class="messages-container" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.type === 'user' ? 'user-message' : 'system-message']">
        <div class="message-content">{{ message.content }}</div>
        <div class="message-time">{{ formatTime(message.timestamp) }}</div>
      </div>
    </div>
    
    <!-- 输入区域 -->
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
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useStore } from 'vuex'
import dayjs from 'dayjs'

const store = useStore()
const inputMessage = ref('')
const messagesContainer = ref(null)

// 从store获取消息列表和连接状态
const messages = computed(() => store.state.messages)
const isConnected = computed(() => store.state.isConnected)

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
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
  box-sizing: border-box;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  margin-bottom: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f9f9f9;
}

.message {
  margin: 10px 0;
  padding: 10px;
  border-radius: 8px;
  max-width: 80%;
}

.user-message {
  margin-left: auto;
  background: #007bff;
  color: white;
}

.system-message {
  margin-right: auto;
  background: white;
  border: 1px solid #ddd;
}

.message-content {
  word-break: break-word;
  white-space: pre-wrap;
}

.message-time {
  font-size: 0.8em;
  color: #888;
  margin-top: 5px;
  text-align: right;
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  font-size: 1em;
}

.button-group {
  display: flex;
  gap: 10px;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: #007bff;
  color: white;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background: #0056b3;
}
</style> 