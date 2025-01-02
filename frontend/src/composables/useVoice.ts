import { ref } from 'vue'
import type { Message } from './useWebSocket'

interface VoiceState {
  isRecording: boolean
  audioStream: MediaStream | null
  mediaRecorder: MediaRecorder | null
  audioChunks: Blob[]
}

interface WebSocketInstance {
  sendMessage: (message: Message) => Promise<void>
}

export function useVoice(ws: WebSocketInstance) {
  const state = ref<VoiceState>({
    isRecording: false,
    audioStream: null,
    mediaRecorder: null,
    audioChunks: []
  })

  // 开始语音输入
  const startVoiceInput = async () => {
    try {
      state.value.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      state.value.mediaRecorder = new MediaRecorder(state.value.audioStream)
      state.value.audioChunks = []

      state.value.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          state.value.audioChunks.push(event.data)
        }
      }

      state.value.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(state.value.audioChunks, { type: 'audio/wav' })
        const formData = new FormData()
        formData.append('audio', audioBlob)

        try {
          const response = await fetch('/api/voice/transcribe', {
            method: 'POST',
            body: formData
          })
          
          if (response.ok) {
            const { text } = await response.json()
            await ws.sendMessage({ type: 'text', content: text })
          }
        } catch (error) {
          console.error('转写失败:', error)
        }
      }

      state.value.mediaRecorder.start(100) // 每100ms收集一次数据
    } catch (error) {
      console.error('启动语音输入失败:', error)
    }
  }

  // 停止语音输入
  const stopVoiceInput = async () => {
    if (state.value.mediaRecorder && state.value.mediaRecorder.state !== 'inactive') {
      state.value.mediaRecorder.stop()
    }
    if (state.value.audioStream) {
      state.value.audioStream.getTracks().forEach(track => track.stop())
    }
  }

  // 开始录制音色样本
  const startVoiceRecording = async () => {
    try {
      state.value.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      state.value.mediaRecorder = new MediaRecorder(state.value.audioStream)
      state.value.audioChunks = []

      state.value.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          state.value.audioChunks.push(event.data)
        }
      }

      state.value.mediaRecorder.start()
      state.value.isRecording = true
    } catch (error) {
      console.error('启动录音失败:', error)
    }
  }

  // 停止录制音色样本
  const stopVoiceRecording = async (): Promise<string> => {
    return new Promise((resolve) => {
      if (state.value.mediaRecorder && state.value.mediaRecorder.state !== 'inactive') {
        state.value.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(state.value.audioChunks, { type: 'audio/wav' })
          const audioUrl = URL.createObjectURL(audioBlob)
          state.value.isRecording = false
          resolve(audioUrl)
        }
        state.value.mediaRecorder.stop()
      } else {
        resolve('')
      }
    })
  }

  // 保存音色配置
  const saveVoiceProfile = async (audioUrl: string) => {
    try {
      const response = await fetch(audioUrl)
      const audioBlob = await response.blob()
      const formData = new FormData()
      formData.append('voice', audioBlob)

      const saveResponse = await fetch('/api/voice/clone', {
        method: 'POST',
        body: formData
      })

      if (!saveResponse.ok) {
        throw new Error('保存音色失败')
      }

      return true
    } catch (error) {
      console.error('保存音色失败:', error)
      return false
    }
  }

  return {
    startVoiceInput,
    stopVoiceInput,
    startVoiceRecording,
    stopVoiceRecording,
    saveVoiceProfile
  }
} 