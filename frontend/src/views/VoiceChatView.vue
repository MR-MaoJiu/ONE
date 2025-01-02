<template>
  <div class="voice-chat">
    <div class="chat-container">
      <!-- 语音控制区域 -->
      <div class="voice-controls">
        <div class="voice-status">
          <div :class="['status-indicator', { 'active': isRecording }]"></div>
          <span>{{ statusText }}</span>
        </div>
        
        <div class="control-buttons">
          <button
            class="voice-button"
            :class="{ 'recording': isRecording }"
            @click="toggleRecording"
          >
            <i class="fas" :class="isRecording ? 'fa-stop' : 'fa-microphone'"></i>
          </button>

          <button
            class="settings-button"
            @click="openSettings"
          >
            <i class="fas fa-cog"></i>
          </button>
        </div>
      </div>

      <!-- 音色列表和试听区域 -->
      <div class="voice-list" v-if="voiceConfigs.length > 0">
        <h3>已保存的音色</h3>
        <div class="voice-items">
          <div v-for="config in voiceConfigs" :key="config.name" class="voice-item">
            <div class="voice-info">
              <h4>{{ config.name }}</h4>
              <div class="voice-params">
                <span>类型: {{ config.type }}</span>
                <span>语言: {{ config.language }}</span>
              </div>
              <div class="voice-description">
                {{ config.description }}
              </div>
            </div>
            <div class="voice-actions">
              <el-button type="primary" size="small" @click="selectedVoice = config.name">
                选择使用
              </el-button>
              <el-button type="warning" size="small" @click="editVoice(config)" v-if="config.type === 'cloned'">
                编辑
              </el-button>
              <el-button type="danger" size="small" @click="deleteVoice(config.name)" v-if="config.type === 'cloned'">
                删除
              </el-button>
            </div>
          </div>
        </div>

        <!-- 试听区域 -->
        <div class="synthesize-area" v-if="selectedVoice">
          <h3>试听合成</h3>
          <div class="synthesize-controls">
            <el-input
              v-model="synthesizeText"
              placeholder="输入要合成的文本"
              type="textarea"
              :rows="3"
            />
            <el-button type="primary" @click="synthesizeVoice">
              合成试听
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 语音克隆配置对话框 -->
    <el-dialog
      v-model="showSettings"
      title="语音克隆配置"
      width="600px"
      destroy-on-close
    >
      <div class="voice-settings">
        <el-steps :active="currentStep" finish-status="success">
          <el-step title="录制语音样本" description="请录制3-10秒的语音样本" />
          <el-step title="试听确认" description="确认录音质量" />
          <el-step title="保存配置" description="设置音色参数" />
        </el-steps>

        <!-- 步骤1：录制语音样本 -->
        <div v-if="currentStep === 0" class="step-content">
          <div class="record-status">
            <el-progress
              v-if="isRecordingSample"
              type="circle"
              :percentage="recordProgress"
              :status="recordProgress >= 100 ? 'success' : 'warning'"
            />
            <span>{{ recordTip }}</span>
          </div>
          
          <div class="record-controls">
            <el-button
              type="primary"
              :icon="isRecordingSample ? 'el-icon-video-pause' : 'el-icon-video-play'"
              @click="toggleSampleRecording"
            >
              {{ isRecordingSample ? '停止录制' : '开始录制' }}
            </el-button>
          </div>
        </div>

        <!-- 步骤2：试听确认 -->
        <div v-if="currentStep === 1" class="step-content">
          <audio v-if="sampleAudioUrl" :src="sampleAudioUrl" controls class="audio-preview"></audio>
          <div class="step-controls">
            <el-button @click="currentStep--">重新录制</el-button>
            <el-button type="primary" @click="currentStep++">确认使用</el-button>
          </div>
        </div>

        <!-- 步骤3：保存配置 -->
        <div v-if="currentStep === 2" class="step-content">
          <el-form :model="voiceConfig" label-width="80px">
            <el-form-item label="音色名称">
              <el-input v-model="voiceConfig.name" placeholder="给这个音色起个名字" />
            </el-form-item>
            <el-form-item label="语速">
              <el-slider v-model="voiceConfig.speed" :min="0.5" :max="2" :step="0.1" />
            </el-form-item>
            <el-form-item label="音调">
              <el-slider v-model="voiceConfig.pitch" :min="-12" :max="12" :step="1" />
            </el-form-item>
          </el-form>
          <div class="step-controls">
            <el-button @click="currentStep--">上一步</el-button>
            <el-button type="primary" @click="saveVoiceConfig">保存配置</el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 编辑音色对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑音色"
      width="400px"
    >
      <el-form :model="editingVoice" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="editingVoice.name" placeholder="输入音色名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editingVoice.description"
            type="textarea"
            :rows="3"
            placeholder="输入音色描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="saveVoiceEdit">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElDialog, ElSteps, ElStep, ElProgress, ElButton, ElForm, ElFormItem, ElInput, ElSlider, ElMessageBox } from 'element-plus'
import 'element-plus/dist/index.css'

// 基础状态
const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])
const audioStream = ref<MediaStream | null>(null)

// 设置相关状态
const showSettings = ref(false)
const currentStep = ref(0)
const isRecordingSample = ref(false)
const recordProgress = ref(0)
const sampleAudioUrl = ref('')
const voiceConfig = ref({
  name: '',
  speed: 1,
  pitch: 0
})

// 计算属性
const statusText = computed(() => isRecording.value ? '正在录音...' : '点击开始说话')
const recordTip = computed(() => {
  if (!isRecordingSample.value) return '请录制3-10秒的语音样本'
  return `录音中... ${recordProgress.value}%`
})

// 开始录音
const startRecording = async () => {
  try {
    // 检查浏览器支持
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('浏览器不支持录音功能')
    }

    // 请求麦克风权限，设置高质量音频参数
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: 1,
        sampleRate: 16000,
        sampleSize: 16
      }
    })
    
    audioStream.value = stream
    audioChunks.value = []

    // 创建 MediaRecorder，使用较高的比特率
    mediaRecorder.value = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus',
      audioBitsPerSecond: 128000
    })

    // 收集音频数据
    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    }

    // 处理录音停止
    mediaRecorder.value.onstop = async () => {
      try {
        const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
        console.log('录音完成，音频大小:', audioBlob.size)

        // 创建表单数据
        const formData = new FormData()
        formData.append('audio', audioBlob, 'recording.webm')

        // 发送到后端进行处理
        const response = await fetch('http://localhost:3000/api/voice/transcribe', {
          method: 'POST',
          body: formData
        })

        if (response.ok) {
          const result = await response.json()
          ElMessage.success('语音识别成功')
          console.log('识别结果:', result)
        } else {
          const errorText = await response.text()
          console.error('语音识别失败:', errorText)
          throw new Error('语音识别失败')
        }
      } catch (error) {
        console.error('处理录音失败:', error)
        ElMessage.error(error instanceof Error ? error.message : '处理录音失败')
      }
    }

    // 开始录音
    mediaRecorder.value.start()
    isRecording.value = true
    ElMessage.success('开始录音')

  } catch (error) {
    console.error('启动录音失败:', error)
    if (error instanceof Error) {
      if (error.name === 'NotAllowedError') {
        ElMessage.error('请允许使用麦克风')
      } else {
        ElMessage.error(error.message)
      }
    }
    isRecording.value = false
  }
}

// 停止录音
const stopRecording = () => {
  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop()
  }
  
  if (audioStream.value) {
    audioStream.value.getTracks().forEach(track => track.stop())
    audioStream.value = null
  }
  
  isRecording.value = false
  ElMessage.success('录音已停止')
}

// 切换录音状态
const toggleRecording = () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

// 打开设置对话框
const openSettings = () => {
  // 重置配置
  currentStep.value = 0
  sampleAudioUrl.value = ''
  voiceConfig.value = {
    name: '',
    speed: 1,
    pitch: 0
  }
  showSettings.value = true
}

// 录制语音样本
let progressTimer: number | null = null

const startSampleRecording = async () => {
  try {
    // 请求麦克风权限，设置高质量音频参数
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: 1,
        sampleRate: 16000,
        sampleSize: 16
      }
    })
    audioStream.value = stream
    audioChunks.value = []

    // 创建 MediaRecorder，使用较高的比特率
    mediaRecorder.value = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus',
      audioBitsPerSecond: 128000
    })

    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    }

    mediaRecorder.value.onstop = () => {
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
      sampleAudioUrl.value = URL.createObjectURL(audioBlob)
      currentStep.value = 1
    }

    mediaRecorder.value.start()
    isRecordingSample.value = true
    recordProgress.value = 0

    // 启动进度计时器，限制录音时长在 3-10 秒之间
    progressTimer = window.setInterval(() => {
      recordProgress.value = Math.min(recordProgress.value + 2, 100)
      if (recordProgress.value >= 100) {
        stopSampleRecording()
      }
    }, 100)

  } catch (error) {
    console.error('启动录音失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '无法启动录音')
  }
}

const stopSampleRecording = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }

  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop()
  }

  if (audioStream.value) {
    audioStream.value.getTracks().forEach(track => track.stop())
    audioStream.value = null
  }

  isRecordingSample.value = false
}

const toggleSampleRecording = () => {
  if (isRecordingSample.value) {
    stopSampleRecording()
  } else {
    startSampleRecording()
  }
}

// 保存语音配置
const saveVoiceConfig = async () => {
  try {
    if (!sampleAudioUrl.value) {
      throw new Error('请先录制语音样本')
    }

    const response = await fetch(sampleAudioUrl.value)
    const audioBlob = await response.blob()
    
    const formData = new FormData()
    formData.append('audio', audioBlob, 'sample.webm')
    formData.append('config', JSON.stringify(voiceConfig.value))

    const saveResponse = await fetch('http://localhost:3000/api/voice/clone', {
      method: 'POST',
      body: formData
    })

    if (saveResponse.ok) {
      ElMessage.success('语音配置保存成功')
      showSettings.value = false
      // 重新获取音色列表
      await fetchVoiceConfigs()
    } else {
      throw new Error('保存失败')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '保存配置失败')
  }
}

// 类型定义
interface VoiceConfig {
  name: string
  language: string
  description: string
  type: string
  sample_path?: string
}

// 音色列表
const voiceConfigs = ref<VoiceConfig[]>([])

// 获取音色列表
const fetchVoiceConfigs = async () => {
  try {
    console.log('开始获取音色列表...')
    const response = await fetch('http://localhost:3000/api/voice/configs')
    console.log('获取音色列表响应:', response)
    if (response.ok) {
      const data = await response.json()
      console.log('获取到的音色列表数据:', data)
      if (Array.isArray(data.configs)) {
        voiceConfigs.value = data.configs
        console.log('更新后的音色列表:', voiceConfigs.value)
      } else {
        console.error('音色列表数据格式错误:', data)
        throw new Error('音色列表数据格式错误')
      }
    } else {
      const errorText = await response.text()
      console.error('获取音色列表失败:', errorText)
      throw new Error(`获取音色列表失败: ${errorText}`)
    }
  } catch (error) {
    console.error('获取音色列表失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '获取音色列表失败')
  }
}

// 试听合成
const synthesizeText = ref('')
const selectedVoice = ref('')

const synthesizeVoice = async () => {
  try {
    if (!synthesizeText.value || !selectedVoice.value) {
      ElMessage.warning('请输入文本并选择音色')
      return
    }

    const formData = new FormData()
    formData.append('text', synthesizeText.value)
    formData.append('voice_name', selectedVoice.value)

    const response = await fetch('http://localhost:3000/api/voice/synthesize', {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      const audioBlob = await response.blob()
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      audio.play()
    } else {
      throw new Error('语音合成失败')
    }
  } catch (error) {
    console.error('语音合成失败:', error)
    ElMessage.error('语音合成失败')
  }
}

// 编辑相关的状态
const showEditDialog = ref(false)
const editingVoice = ref<VoiceConfig>({
  name: '',
  language: 'multilingual',
  description: '',
  type: 'cloned'
})

// 编辑音色
const editVoice = (config: VoiceConfig) => {
  editingVoice.value = { ...config }
  showEditDialog.value = true
}

// 保存音色编辑
const saveVoiceEdit = async () => {
  try {
    const response = await fetch(`http://localhost:3000/api/voice/edit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(editingVoice.value)
    })

    if (response.ok) {
      ElMessage.success('音色编辑成功')
      showEditDialog.value = false
      await fetchVoiceConfigs()
    } else {
      throw new Error('编辑失败')
    }
  } catch (error) {
    console.error('编辑音色失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '编辑音色失败')
  }
}

// 删除音色
const deleteVoice = async (name: string) => {
  try {
    const confirmed = await ElMessageBox.confirm(
      '确定要删除这个音色吗？此操作不可恢复。',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (confirmed) {
      const response = await fetch(`http://localhost:3000/api/voice/delete/${name}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        ElMessage.success('音色删除成功')
        if (selectedVoice.value === name) {
          selectedVoice.value = ''
        }
        await fetchVoiceConfigs()
      } else {
        throw new Error('删除失败')
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除音色失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '删除音色失败')
    }
  }
}

// 生命周期钩子
onMounted(() => {
  console.log('VoiceChatView 组件已加载')
  fetchVoiceConfigs()
})

onUnmounted(() => {
  // 清理资源
  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop()
  }
  if (audioStream.value) {
    audioStream.value.getTracks().forEach(track => track.stop())
  }
  if (progressTimer) {
    clearInterval(progressTimer)
  }
})
</script>

<style>
@import 'element-plus/theme-chalk/dark/css-vars.css';
</style>

<style scoped>
.voice-chat {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
  color: #fff;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 20px;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.voice-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 32px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.voice-status {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 15px;
  font-weight: 500;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #4b5563;
  transition: all 0.3s ease;
}

.status-indicator.active {
  background: #409EFF;
  animation: pulse 1.5s infinite;
}

.control-buttons {
  display: flex;
  gap: 16px;
}

.voice-button {
  width: 56px;
  height: 56px;
  font-size: 22px;
  border-radius: 50%;
  border: none;
  background: #409EFF;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.voice-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.voice-button.recording {
  background: #F56C6C;
  animation: pulse 1.5s infinite;
}

.settings-button {
  width: 48px;
  height: 48px;
  font-size: 18px;
  border-radius: 50%;
  border: none;
  background: #67C23A;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.settings-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.voice-settings {
  padding: 20px;
}

.step-content {
  margin-top: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.record-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.step-controls {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

.audio-preview {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(64, 158, 255, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0);
  }
}

.voice-list {
  margin-top: 32px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.voice-items {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.voice-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.voice-info h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
}

.voice-params {
  display: flex;
  gap: 12px;
  font-size: 14px;
  color: #909399;
}

.voice-description {
  margin-top: 8px;
  font-size: 14px;
  color: #C0C4CC;
}

.voice-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.sample-audio {
  width: 200px;
}

.synthesize-area {
  margin-top: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.synthesize-controls {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.synthesize-controls .el-input {
  flex: 1;
}
</style> 