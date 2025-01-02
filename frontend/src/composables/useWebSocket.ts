import { ref, onUnmounted } from 'vue'
import type { MemoryStore } from '@/stores/memory'

export interface Message {
  type: 'text' | 'voice'
  content: string
  timestamp?: number
}

export function useWebSocket(memoryStore: MemoryStore) {
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5

  const connect = async () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/voice`
      
      ws.value = new WebSocket(wsUrl)
      
      ws.value.onopen = () => {
        console.log('WebSocket连接已建立')
        isConnected.value = true
        reconnectAttempts.value = 0
      }
      
      ws.value.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'voice') {
            // 播放语音响应
            const audio = new Audio(data.content)
            await audio.play()
          }
          
          if (data.memories) {
            // 更新记忆节点
            memoryStore.updateNodes(data.memories)
          }
          
          if (data.activeMemories) {
            // 激活相关记忆节点
            memoryStore.activateNodes(data.activeMemories)
          }
        } catch (error) {
          console.error('处理WebSocket消息失败:', error)
        }
      }
      
      ws.value.onclose = () => {
        console.log('WebSocket连接已关闭')
        isConnected.value = false
        handleReconnect()
      }
      
      ws.value.onerror = (error) => {
        console.error('WebSocket错误:', error)
        isConnected.value = false
      }
    } catch (error) {
      console.error('建立WebSocket连接失败:', error)
      handleReconnect()
    }
  }

  const disconnect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
      isConnected.value = false
    }
  }

  const handleReconnect = () => {
    if (reconnectAttempts.value < maxReconnectAttempts) {
      reconnectAttempts.value++
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 10000)
      setTimeout(connect, delay)
    }
  }

  const sendMessage = async (message: Message) => {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket未连接')
    }

    try {
      ws.value.send(JSON.stringify({
        ...message,
        timestamp: Date.now()
      }))
    } catch (error) {
      console.error('发送消息失败:', error)
      throw error
    }
  }

  // 组件卸载时清理WebSocket连接
  onUnmounted(() => {
    disconnect()
  })

  return {
    connect,
    disconnect,
    sendMessage,
    isConnected
  }
} 