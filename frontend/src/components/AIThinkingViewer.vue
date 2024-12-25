<template>
  <div class="thinking-container" :class="{ 'show': isShowThinking }">
    <div class="thinking-header">
      <div class="header-content">
        <div class="pulse-dot" :class="{ 'active': isThinking }"></div>
        <h3>AI 思考过程</h3>
      </div>
      <button v-if="isMobile" class="close-thinking" @click="closeThinking">×</button>
    </div>
    <div class="thinking-content">
      <template v-if="uniqueSteps.length">
        <div v-for="(step, index) in uniqueSteps" 
             :key="index" 
             class="thinking-step"
             :class="{ 'fade-in': true }">
          <div class="step-number">
            <div class="number-circle">{{ index + 1 }}</div>
            <div class="step-line" v-if="index < uniqueSteps.length - 1"></div>
          </div>
          <div class="step-content">
            <div class="step-type">
              <span class="type-icon">{{ getTypeIcon(step.type) }}</span>
              {{ getTypeText(step.type) }}
            </div>
            <div class="step-description">{{ step.description }}</div>
            <div v-if="step.result" class="step-result">
              <pre>{{ formatResult(step.result) }}</pre>
            </div>
          </div>
        </div>
      </template>
      <div v-else-if="isThinking" class="thinking-animation-container">
        <div class="thinking-status">
          <div class="thinking-animation">
            <div class="circle"></div>
            <div class="circle"></div>
            <div class="circle"></div>
          </div>
          <span class="thinking-text">AI 正在思考中...</span>
        </div>
      </div>
      <div v-else class="no-thinking">
        <span class="idle-text">发送消息后，这里将显示 AI 的思考过程</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useStore } from 'vuex'

const store = useStore()
const props = defineProps({
  thinkingSteps: {
    type: Array,
    default: () => []
  }
})

const displaySteps = ref([])
const isThinking = computed(() => store.state.isThinking)
const stepDelay = 500 // 每个步骤显示的延迟时间（毫秒）

// 移动端相关状态
const isMobile = computed(() => window.innerWidth <= 768)
const isShowThinking = ref(false)

// 监听思考状态变化
watch(isThinking, (newValue) => {
  if (isMobile.value) {
    isShowThinking.value = newValue
  }
})

// 关闭思考面板
const closeThinking = () => {
  isShowThinking.value = false
}

// 去重后的思考步骤
const uniqueSteps = computed(() => {
  const steps = new Map()
  const finalSteps = []
  const responseSteps = []
  
  // 将步骤分类并去重
  displaySteps.value.forEach(step => {
    const key = `${step.type}-${step.description}`
    
    // 将生成回答和最终回答的步骤单独存储
    if (step.type === 'response_generation' || step.type === 'final_response') {
      if (!responseSteps.some(s => s.type === step.type)) {
        responseSteps.push(step)
      }
    } else {
      steps.set(key, step)
    }
  })
  
  // 将普通步骤添加到最终数组
  finalSteps.push(...Array.from(steps.values()))
  
  // 按照特定顺序添加响应步骤
  const responseOrder = ['response_generation', 'final_response']
  responseOrder.forEach(type => {
    const step = responseSteps.find(s => s.type === type)
    if (step) {
      finalSteps.push(step)
    }
  })
  
  return finalSteps
})

// 监听思考步骤的变化
watch(() => props.thinkingSteps, (newSteps) => {
  if (newSteps.length === 0) {
    displaySteps.value = []
    return
  }
  
  // 逐步显示每个步骤
  displaySteps.value = []
  newSteps.forEach((step, index) => {
    setTimeout(() => {
      displaySteps.value.push(step)
    }, index * stepDelay)
  })
}, { deep: true })

// 监听消息发送事件
watch(() => store.state.messages, (newMessages, oldMessages) => {
  if (newMessages.length > oldMessages.length) {
    const lastMessage = newMessages[newMessages.length - 1]
    if (lastMessage.type === 'user') {
      // 用户发送消息时，立即设置思考状态为true并清空步骤
      isThinking.value = true
      displaySteps.value = []
    }
  }
}, { deep: true })

// 监听WebSocket连接状态
watch(() => store.state.isConnected, (newValue) => {
  if (!newValue) {
    // WebSocket断开时，重置状态
    isThinking.value = false
    displaySteps.value = []
  }
}, { immediate: true })

// 获取步骤类型的图标
const getTypeIcon = (type) => {
  const icons = {
    // 基础步骤
    'input_analysis': '🔍',
    'history_analysis': '📜',
    'memory_analysis': '🧠',
    'response_generation': '✍️',
    'final_response': '📝',
    'error_handling': '⚠️',
    
    // API相关步骤
    'api_feature_check': '🔌',
    'api_doc_analysis': '📚',
    'requirement_analysis': '📋',
    'api_matching': '🔄',
    'api_decision': '🤔',
    'api_plan': '📊',
    'api_preparation': '🛠️',
    'api_request': '📤',
    'api_response': '📥',
    'api_error': '❌',
    'api_summary': '📑'
  }
  return icons[type] || '❓'
}

// 获取步骤类型的中文文本
const getTypeText = (type) => {
  const texts = {
    // 基础步骤
    'input_analysis': '输入分析',
    'history_analysis': '历史分析',
    'memory_analysis': '记忆分析',
    'response_generation': '生成回答',
    'final_response': '最终回答',
    'error_handling': '错误处理',
    
    // API相关步骤
    'api_feature_check': 'API功能检查',
    'api_doc_analysis': 'API文档分析',
    'requirement_analysis': '需求分析',
    'api_matching': 'API匹配分析',
    'api_decision': 'API调用决策',
    'api_plan': 'API调用计划',
    'api_preparation': 'API调用准备',
    'api_request': 'API请求发送',
    'api_response': 'API响应接收',
    'api_error': 'API错误处理',
    'api_summary': 'API调用总结'
  }
  return texts[type] || type
}

// 格式化结果文本
const formatResult = (result) => {
  if (result.includes('相关记忆:')) {
    return result.split('\n').map(line => line.trim()).join('\n')
  }
  return result
}

// 切换思考面板显示状态
const toggleThinking = () => {
  isShowThinking.value = !isShowThinking.value
}

// 暴露方法给父组件
defineExpose({
  toggleThinking
})
</script>

<style scoped>
/* PC端样式 */
.thinking-container {
  width: 30%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 150, 255, 0.15);
  color: #e0e0e0;
}

.thinking-header {
  padding: 16px;
  border-bottom: 1px solid #333;
  background: linear-gradient(90deg, #1a1a1a 0%, #2a2a2a 100%);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pulse-dot {
  width: 12px;
  height: 12px;
  background: #666;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.pulse-dot.active {
  background: #00ff9d;
  animation: pulse 2s infinite;
}

.thinking-header h3 {
  margin: 0;
  color: #00ff9d;
  font-size: 1.2rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.thinking-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.thinking-step {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  opacity: 0;
  transform: translateY(20px);
  animation: fadeInUp 0.5s forwards;
}

.step-number {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.number-circle {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #00ff9d 0%, #00a8ff 100%);
  color: #1a1a1a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  box-shadow: 0 0 15px rgba(0, 255, 157, 0.3);
}

.step-line {
  flex: 1;
  width: 2px;
  background: linear-gradient(180deg, #00ff9d 0%, transparent 100%);
  margin: 8px 0;
}

.step-content {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid rgba(0, 255, 157, 0.2);
}

.step-type {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #00ff9d;
  font-weight: 500;
  margin-bottom: 8px;
}

.type-icon {
  font-size: 1.2em;
}

.step-description {
  color: #b0b0b0;
  margin-bottom: 12px;
}

.step-result {
  background: rgba(0, 0, 0, 0.3);
  padding: 12px;
  border-radius: 6px;
  margin-top: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.step-result pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: #00a8ff;
  font-family: 'Fira Code', monospace;
}

.no-thinking {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  color: #666;
}

.idle-text {
  color: #666;
  font-style: italic;
}

.thinking-animation-container {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thinking-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(0, 255, 157, 0.2);
}

.thinking-text {
  color: #00ff9d;
  font-size: 1.1em;
  font-weight: 500;
  text-shadow: 0 0 10px rgba(0, 255, 157, 0.3);
}

.thinking-animation {
  display: flex;
  gap: 8px;
}

.circle {
  width: 12px;
  height: 12px;
  background: #00ff9d;
  border-radius: 50%;
  animation: bounce 1s infinite;
  box-shadow: 0 0 10px rgba(0, 255, 157, 0.5);
}

.circle:nth-child(2) {
  animation-delay: 0.2s;
}

.circle:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(0, 255, 157, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(0, 255, 157, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 255, 157, 0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* 自定义滚动条 */
.thinking-content::-webkit-scrollbar {
  width: 6px;
}

.thinking-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.thinking-content::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #00ff9d 0%, #00a8ff 100%);
  border-radius: 3px;
}

/* 移动端专用样式 */
@media (max-width: 768px) {
  .thinking-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border-radius: 0;
    transform: translateY(100%);
    transition: transform 0.3s ease;
    z-index: 1000;
    background: rgba(26, 26, 26, 0.98);
    backdrop-filter: blur(20px);
  }

  .thinking-container.show {
    transform: translateY(0);
  }

  .thinking-header {
    position: relative;
    padding: 16px;
    background: linear-gradient(180deg, #1a1a1a 0%, transparent 100%);
  }

  .close-thinking {
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: #666;
    font-size: 24px;
    padding: 8px;
    cursor: pointer;
    transition: color 0.3s ease;
  }

  .close-thinking:hover {
    color: #00ff9d;
  }

  .header-content {
    justify-content: center;
  }

  .thinking-content {
    padding: 20px 16px;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }

  .thinking-step {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .step-number {
    display: none;
  }

  .step-content {
    margin: 0;
  }

  .step-type {
    font-size: 14px;
    color: #00ff9d;
    margin-bottom: 8px;
  }

  .type-icon {
    font-size: 16px;
    margin-right: 8px;
  }

  .step-description {
    font-size: 13px;
    color: #e0e0e0;
    margin-bottom: 10px;
  }

  .step-result {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 12px;
    padding: 12px;
    margin-top: 10px;
  }

  .step-result pre {
    font-size: 12px;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .thinking-animation-container {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .thinking-status {
    text-align: center;
  }

  .thinking-animation {
    margin-bottom: 16px;
  }

  .circle {
    width: 10px;
    height: 10px;
    margin: 0 4px;
  }

  .thinking-text {
    font-size: 14px;
    color: #00ff9d;
  }

  .no-thinking {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    text-align: center;
  }

  .idle-text {
    font-size: 14px;
    color: #666;
    line-height: 1.5;
  }

  /* 移动端动画 */
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .thinking-step {
    animation: slideIn 0.3s ease-out forwards;
  }
}
</style> 