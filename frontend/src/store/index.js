import { createStore } from 'vuex'
import axios from 'axios'

// 配置 axios 默认值
axios.defaults.headers.common['Content-Type'] = 'application/json'

// 从localStorage加载API设置
const loadApiSettings = () => {
  try {
    const settings = localStorage.getItem('api_settings')
    if (settings) {
      return JSON.parse(settings)
    }
  } catch (e) {
    console.error('加载API设置失败:', e)
  }
  return {
    enableApiCall: false,
    apiDocs: ''
  }
}

// 保存API设置到localStorage
const saveApiSettings = (settings) => {
  try {
    localStorage.setItem('api_settings', JSON.stringify(settings))
  } catch (e) {
    console.error('保存API设置失败:', e)
  }
}

// 加载初始API设置
const initialApiSettings = loadApiSettings()

export default createStore({
  state: {
    messages: [], // 聊天消息列表
    memories: [], // 记忆列表
    snapshots: [], // 快照列表
    currentAnalysis: null, // 当前分析数据
    thinkingSteps: [], // AI思考步骤
    isThinking: false, // 是否正在思考
    enableApiCall: initialApiSettings.enableApiCall, // 是否启用API调用功能
    apiDocs: initialApiSettings.apiDocs, // API文档内容
  },
  
  mutations: {
    SET_MESSAGES(state, messages) {
      state.messages = messages
    },
    ADD_MESSAGE(state, message) {
      state.messages.push(message)
    },
    SET_MEMORIES(state, memories) {
      state.memories = memories
    },
    SET_SNAPSHOTS(state, snapshots) {
      state.snapshots = snapshots
    },
    SET_CURRENT_ANALYSIS(state, analysis) {
      state.currentAnalysis = analysis
    },
    SET_THINKING_STEPS(state, steps) {
      state.thinkingSteps = steps
    },
    ADD_THINKING_STEP(state, step) {
      state.thinkingSteps.push(step)
    },
    CLEAR_THINKING_STEPS(state) {
      state.thinkingSteps = []
    },
    SET_THINKING(state, status) {
      state.isThinking = status
    },
    SET_API_CALL_ENABLED(state, enabled) {
      state.enableApiCall = enabled
      // 保存设置
      saveApiSettings({
        enableApiCall: state.enableApiCall,
        apiDocs: state.apiDocs
      })
    },
    SET_API_DOCS(state, docs) {
      state.apiDocs = docs
      // 保存设置
      saveApiSettings({
        enableApiCall: state.enableApiCall,
        apiDocs: state.apiDocs
      })
    },
    CLEAR_ALL(state) {
      state.messages = []
      state.memories = []
      state.snapshots = []
      state.thinkingSteps = []
      state.currentAnalysis = null
      // 不清除API设置
    }
  },
  
  actions: {
    // 发送聊天消息
    async sendMessage({ commit, state }, message) {
      try {
        // 设置思考状态为true
        commit('SET_THINKING', true)
        commit('CLEAR_THINKING_STEPS')
        
        // 添加用户消息到列表
        commit('ADD_MESSAGE', {
          type: 'user',
          content: message.content,
          timestamp: new Date().toISOString()
        })

        // 发送消息到后端
        const response = await axios.post('/chat', {
          content: message.content,
          context: message.context || {},
          enable_api_call: state.enableApiCall,
          api_docs: state.apiDocs
        })
        
        // 更新思考步骤
        if (response.data.thinking_steps) {
          commit('SET_THINKING_STEPS', response.data.thinking_steps)
        }
        
        // 添加系统回复
        if (response.data.response) {
          commit('ADD_MESSAGE', {
            type: 'system',
            content: response.data.response,
            timestamp: new Date().toISOString()
          })
        }
        
        // 更新分析数据
        if (response.data.analysis) {
          commit('SET_CURRENT_ANALYSIS', response.data.analysis)
        }
        
        // 设置思考状态为false
        setTimeout(() => {
          commit('SET_THINKING', false)
        }, 1000) // 延迟1秒关闭思考状态，让用户能看清最后的步骤
        
        return response.data
      } catch (error) {
        console.error('发送消息失败:', error)
        commit('SET_THINKING', false)
        throw new Error(error.response?.data?.detail || '发送消息失败')
      }
    },
    
    // 更新API调用状态
    setApiCallEnabled({ commit }, enabled) {
      commit('SET_API_CALL_ENABLED', enabled)
    },
    
    // 更新API文档
    setApiDocs({ commit }, docs) {
      commit('SET_API_DOCS', docs)
    },
    
    // 获取所有记忆
    async fetchMemories({ commit }) {
      try {
        const response = await axios.get('/memories')
        commit('SET_MEMORIES', response.data)
      } catch (error) {
        console.error('获取记忆失败:', error)
        throw new Error(error.response?.data?.detail || '获取记忆失败')
      }
    },
    
    // 获取所有快照
    async fetchSnapshots({ commit }) {
      try {
        const response = await axios.get('/snapshots')
        commit('SET_SNAPSHOTS', response.data)
      } catch (error) {
        console.error('获取快照失败:', error)
        throw new Error(error.response?.data?.detail || '获取快照失败')
      }
    },
    
    // 更新快照
    async updateSnapshots({ dispatch }) {
      try {
        await axios.post('/snapshots/update')
        // 更新后重新获取快照列表
        await dispatch('fetchSnapshots')
      } catch (error) {
        console.error('更新快照失败:', error)
        throw new Error(error.response?.data?.detail || '更新快照失败')
      }
    },
    
    // 清空所有记忆
    async clearMemories({ commit }) {
      try {
        await axios.delete('/memories')
        commit('CLEAR_ALL')
      } catch (error) {
        console.error('清空记忆失败:', error)
        throw new Error(error.response?.data?.detail || '清空记忆失败')
      }
    }
  }
}) 