<template>
  <div class="chat-container">
    <!-- 头部 -->
    <div class="chat-header">
      <h1>AI对话助手</h1>
      <el-button type="primary" @click="startNewChat">新对话</el-button>
    </div>
    
    <!-- 消息列表 -->
    <div class="message-list" ref="messageList">
      <div v-for="(message, index) in messages" 
           :key="index" 
           :class="['message', message.type]">
        <!-- 头像和名称 -->
        <div class="message-avatar">
          <el-avatar :size="40" :src="message.type === 'user' ? '/user-avatar.png' : '/ai-avatar.png'" />
          <span class="name">{{ message.type === 'user' ? '你' : 'AI' }}</span>
        </div>
        
        <!-- 消息内容 -->
        <div class="message-content">
          <p>{{ message.content }}</p>
          <span class="time">{{ formatTime(message.timestamp) }}</span>
        </div>
      </div>
    </div>
    
    <!-- 输入框 -->
    <div class="input-area">
      <el-input 
        v-model="inputMessage" 
        type="textarea" 
        :rows="3"
        placeholder="输入消息..."
        @keyup.enter.ctrl="sendMessage" />
      <el-button type="primary" 
                 :loading="sending"
                 @click="sendMessage">
        发送
      </el-button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useStore } from 'vuex'
import moment from 'moment'
import { ElMessage } from 'element-plus'

export default {
  name: 'Chat',
  
  setup() {
    const store = useStore()
    const inputMessage = ref('')
    const sending = ref(false)
    const messageList = ref(null)
    
    // 从store获取消息列表
    const messages = computed(() => store.state.messages)
    
    // 发送消息
    const sendMessage = async () => {
      if (!inputMessage.value.trim() || sending.value) {
        return
      }
      
      sending.value = true
      try {
        const messageData = {
          content: inputMessage.value.trim(),
          context: {
            history: store.state.messages.map(m => ({
              is_user: m.type === 'user',
              content: m.content,
              timestamp: m.timestamp
            }))
          }
        }
        
        await store.dispatch('sendMessage', messageData)
        inputMessage.value = ''
        // 滚动到底部
        await nextTick()
        scrollToBottom()
      } catch (error) {
        console.error('发送失败:', error)
        ElMessage.error(error.message || '发送失败，请重试')
      } finally {
        sending.value = false
      }
    }
    
    // 开始新对话
    const startNewChat = () => {
      store.dispatch('startNewConversation')
    }
    
    // 滚动到底部
    const scrollToBottom = () => {
      if (messageList.value) {
        messageList.value.scrollTop = messageList.value.scrollHeight
      }
    }
    
    // 格式化时间
    const formatTime = (timestamp) => {
      return moment(timestamp).format('HH:mm:ss')
    }
    
    // 组件挂载时开始新对话
    onMounted(() => {
      startNewChat()
    })
    
    return {
      inputMessage,
      sending,
      messageList,
      messages,
      sendMessage,
      startNewChat,
      formatTime
    }
  }
}
</script>

<style scoped>
.chat-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.chat-header {
  padding: 16px;
  background-color: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message.user {
  flex-direction: row-reverse;
  align-self: flex-end;
}

.message-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.message-avatar .name {
  font-size: 0.8rem;
  color: #666;
}

.message-content {
  background-color: white;
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
}

.message.user .message-content {
  background-color: #1976d2;
  color: white;
}

.message-content p {
  margin: 0;
  white-space: pre-wrap;
}

.message-content .time {
  position: absolute;
  bottom: -20px;
  font-size: 0.8rem;
  color: #999;
}

.message.user .message-content .time {
  right: 0;
}

.input-area {
  padding: 20px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 16px;
}

.input-area .el-input {
  flex: 1;
}

@media (max-width: 768px) {
  .message {
    max-width: 90%;
  }
}
</style> 