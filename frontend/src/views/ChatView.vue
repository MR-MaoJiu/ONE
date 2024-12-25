<template>
  <div class="chat-container">
    <div class="split-view">
      <!-- API调用设置区域 -->
      <div class="api-settings" v-if="showApiSettings">
        <div class="api-settings-header">
          <h3>API调用设置</h3>
          <button class="close-btn" @click="toggleApiSettings">×</button>
        </div>
        <div class="api-settings-content">
          <div class="api-switch">
            <label class="switch">
              <input type="checkbox" v-model="enableApiCall">
              <span class="slider"></span>
            </label>
            <span class="switch-label">启用API调用</span>
          </div>
          <div class="api-warning" v-if="enableApiCall">
            注意：启用API调用可能会增加响应时间
          </div>
          <div class="api-docs-input" v-if="enableApiCall">
            <label>API文档：</label>
            <textarea
              v-model="apiDocs"
              placeholder="请输入API文档内容..."
              rows="5"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- 聊天区域 -->
      <div class="chat-section">
        <div class="chat-header">
          <button class="settings-btn" @click="toggleApiSettings">
            <span v-if="!isMobile" class="settings-icon">⚙️</span>
            <span v-if="!isMobile">API设置</span>
            <span v-else class="settings-icon">⚙️</span>
          </button>
        </div>
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
            <button @click="sendMessage" :disabled="!inputMessage.trim() || isThinking">
              <span v-if="!isMobile">发送</span>
              <span v-else>📤</span>
            </button>
            <button @click="clearChat" class="btn-secondary">
              <span v-if="!isMobile">清空对话</span>
              <span v-else>🗑️</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 思考步骤区域 -->
      <AIThinkingViewer :thinking-steps="thinkingSteps" ref="thinkingViewer" />

      <!-- 移动端思考面板控制按钮 -->
      <button v-if="isMobile" class="thinking-toggle-btn" @click="toggleThinking">
        <span class="toggle-icon">🧠</span>
      </button>
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
const showApiSettings = ref(false)

// 从store获取状态
const messages = computed(() => store.state.messages)
const thinkingSteps = computed(() => store.state.thinkingSteps)
const isThinking = computed(() => store.state.isThinking)

// API调用相关的计算属性
const enableApiCall = computed({
  get: () => store.state.enableApiCall,
  set: (value) => store.dispatch('setApiCallEnabled', value)
})

const apiDocs = computed({
  get: () => store.state.apiDocs,
  set: (value) => store.dispatch('setApiDocs', value)
})

// 监听消息列表变化，自动滚动到底部
watch(messages, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
})

// 切换API设置面板
function toggleApiSettings() {
  showApiSettings.value = !showApiSettings.value
}

// 发送消息
async function sendMessage() {
  if (!inputMessage.value.trim() || isThinking.value) return
  
  try {
    await store.dispatch('sendMessage', {
      content: inputMessage.value
    })
    
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
    store.commit('SET_MESSAGES', [])
    store.commit('CLEAR_THINKING_STEPS')
  }
}

// 格式化时间
function formatTime(timestamp) {
  return dayjs(timestamp).format('HH:mm:ss')
}

// 添加移动端相关状态
const isMobile = computed(() => window.innerWidth <= 768)
const thinkingViewer = ref(null)

// 切换思考面板显示状态
function toggleThinking() {
  if (thinkingViewer.value) {
    thinkingViewer.value.toggleThinking()
  }
}
</script>

<style scoped>
/* PC端样式 */
.chat-container {
  height: calc(100vh - 60px);
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

.chat-header {
  padding: 10px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
}

.settings-btn {
  background: none;
  border: 1px solid #333;
  color: #e0e0e0;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.9em;
}

.settings-btn:hover {
  background: rgba(0, 255, 157, 0.1);
  border-color: #00ff9d;
}

.settings-icon {
  font-size: 1.2em;
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

/* API设置面板样式 */
.api-settings {
  width: 300px;
  background: #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 150, 255, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.api-settings-header {
  padding: 15px;
  background: #1a1a1a;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #333;
}

.api-settings-header h3 {
  margin: 0;
  color: #e0e0e0;
  font-size: 1.1em;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 1.5em;
  cursor: pointer;
  padding: 0 5px;
}

.close-btn:hover {
  color: #e0e0e0;
}

.api-settings-content {
  padding: 15px;
  flex: 1;
  overflow-y: auto;
}

.api-switch {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #333;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: #fff;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background: linear-gradient(135deg, #00ff9d 0%, #00a8ff 100%);
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.switch-label {
  color: #e0e0e0;
  font-size: 0.95em;
}

.api-warning {
  color: #ff9d00;
  font-size: 0.85em;
  margin-bottom: 15px;
  padding: 8px;
  background: rgba(255, 157, 0, 0.1);
  border-radius: 4px;
}

.api-docs-input {
  margin-top: 15px;
}

.api-docs-input label {
  display: block;
  color: #e0e0e0;
  margin-bottom: 8px;
}

.api-docs-input textarea {
  width: 100%;
  min-height: 150px;
  padding: 8px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #e0e0e0;
  font-size: 0.9em;
  resize: vertical;
}

.api-docs-input textarea:focus {
  outline: none;
  border-color: #00ff9d;
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

/* 移动端专用样式 */
@media (max-width: 768px) {
  .chat-container {
    height: 100vh;
    padding: 0;
    position: relative;
  }

  .split-view {
    flex-direction: column;
  }

  .chat-section {
    height: 100%;
    border-radius: 0;
  }

  .messages-container {
    padding: 12px;
    padding-bottom: 80px;
  }

  .message {
    max-width: 88%;
    padding: 10px 12px;
    font-size: 14px;
  }

  .user-message {
    margin-left: auto;
    margin-right: 8px;
    background: #4a9eff;
    color: white;
    border-radius: 16px;
    border-bottom-right-radius: 4px;
  }

  .system-message {
    margin-right: auto;
    margin-left: 8px;
    background: #2a2a2a;
    border-radius: 16px;
    border-bottom-left-radius: 4px;
  }

  .input-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 12px;
    background: #1a1a1a;
    border-top: 1px solid #333;
  }

  .input-wrapper {
    display: flex;
    gap: 8px;
    align-items: flex-end;
  }

  textarea {
    min-height: 40px;
    max-height: 120px;
    padding: 10px 12px;
    font-size: 14px;
    border-radius: 20px;
    background: #2a2a2a;
  }

  .button-group {
    display: flex;
    gap: 8px;
  }

  button {
    width: 40px;
    height: 40px;
    padding: 0;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .settings-btn {
    position: fixed;
    top: 12px;
    right: 12px;
    z-index: 100;
    background: rgba(26, 26, 26, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid #444;
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 13px;
  }

  .api-settings {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 90%;
    max-width: none;
    max-height: 80vh;
    border-radius: 20px;
    z-index: 1000;
    background: rgba(26, 26, 26, 0.95);
    backdrop-filter: blur(20px);
  }

  .api-settings-header {
    padding: 16px;
  }

  .api-settings-header h3 {
    font-size: 16px;
  }

  .api-settings-content {
    padding: 16px;
  }

  .api-switch {
    margin-bottom: 20px;
  }

  .api-docs-input textarea {
    min-height: 120px;
    border-radius: 12px;
  }

  .api-warning {
    font-size: 12px;
    padding: 10px;
    border-radius: 10px;
  }

  /* 移动端动画 */
  @keyframes slideUp {
    from {
      transform: translate(-50%, 100%);
    }
    to {
      transform: translate(-50%, -50%);
    }
  }

  .api-settings.show {
    animation: slideUp 0.3s ease-out forwards;
  }

  /* 思考面板控制按钮样式 */
  .thinking-toggle-btn {
    position: fixed;
    bottom: 100px;
    right: 16px;
    z-index: 1000;
    width: 40px;
    height: 40px;
    padding: 0;
    background: rgba(26, 26, 26, 0.9);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(0, 255, 157, 0.3);
    border-radius: 50%;
    color: #00ff9d;
    font-size: 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .toggle-icon {
    font-size: inherit;
  }

  .thinking-toggle-btn:active {
    transform: scale(0.95);
  }

  .button-group button {
    width: 40px;
    height: 40px;
    padding: 0;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
  }

  .settings-btn {
    width: 40px;
    height: 40px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
  }
}
</style> 