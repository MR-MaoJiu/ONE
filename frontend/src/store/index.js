import { createStore } from 'vuex'
import axios from 'axios'

// 配置 axios 默认值
axios.defaults.headers.common['Content-Type'] = 'application/json'

export default createStore({
  state: {
    messages: [], // 聊天消息列表
    memories: [], // 记忆列表
    snapshots: [], // 快照列表
    wsConnection: null, // WebSocket连接
    isConnected: false, // WebSocket连接状态
    currentAnalysis: null, // 当前分析数据
    thinkingSteps: [], // 新增：AI思考步骤
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
    SET_WS_CONNECTION(state, connection) {
      state.wsConnection = connection
      state.isConnected = connection !== null
    },
    SET_CONNECTED(state, status) {
      state.isConnected = status
    },
    SET_CURRENT_ANALYSIS(state, analysis) {
      state.currentAnalysis = analysis
    },
    // 新增：设置思考步骤
    SET_THINKING_STEPS(state, steps) {
      state.thinkingSteps = steps
    },
    // 新增：添加思考步骤
    ADD_THINKING_STEP(state, step) {
      state.thinkingSteps.push(step)
    },
    // 新增：清空思考步骤
    CLEAR_THINKING_STEPS(state) {
      state.thinkingSteps = []
    }
  },
  
  actions: {
    // 发送聊天消息 (HTTP)
    async sendMessage({ commit }, message) {
      try {
        // 添加用户消息到列表
        commit('ADD_MESSAGE', {
          type: 'user',
          content: message.content,
          timestamp: new Date().toISOString()
        })

        // 发送消息到后端
        const response = await axios.post('/chat', {
          content: message.content,
          context: message.context || {}
        })
        
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
        
        return response.data
      } catch (error) {
        console.error('发送消息失败:', error)
        throw new Error(error.response?.data?.detail || '发送消息失败')
      }
    },

    // 初始化WebSocket连接
    initWebSocket({ commit, dispatch }) {
      const ws = new WebSocket('ws://localhost:8000/ws')
      
      ws.onopen = () => {
        commit('SET_CONNECTED', true)
        console.log('WebSocket连接已建立')
      }
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.response) {
          commit('ADD_MESSAGE', {
            type: 'system',
            content: data.response,
            timestamp: new Date().toISOString()
          })
        }
        if (data.analysis) {
          commit('SET_CURRENT_ANALYSIS', data.analysis)
        }
      }
      
      ws.onclose = () => {
        commit('SET_CONNECTED', false)
        console.log('WebSocket连接已关闭')
        // 尝试重新连接
        setTimeout(() => dispatch('initWebSocket'), 3000)
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        ws.close()
      }
      
      commit('SET_WS_CONNECTION', ws)
    },
    
    // 通过WebSocket发送消息
    async sendWebSocketMessage({ state, commit }, message) {
      if (!state.wsConnection || !state.isConnected) {
        throw new Error('WebSocket未连接')
      }
      
      try {
        // 添加用户消息到列表
        commit('ADD_MESSAGE', {
          type: 'user',
          content: message.content,
          timestamp: new Date().toISOString()
        })
        
        // 发送消息
        state.wsConnection.send(JSON.stringify({
          content: message.content,
          context: message.context || {}
        }))
      } catch (error) {
        console.error('WebSocket发送消息失败:', error)
        throw error
      }
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
        commit('SET_MEMORIES', [])
        commit('SET_SNAPSHOTS', [])
      } catch (error) {
        console.error('清空记忆失败:', error)
        throw new Error(error.response?.data?.detail || '清空记忆失败')
      }
    },
    
    // 清空聊天记录
    clearMessages({ commit }) {
      commit('SET_MESSAGES', [])
      commit('CLEAR_THINKING_STEPS')
    },
    
    // 开始新对话
    startNewConversation({ commit }) {
      commit('SET_MESSAGES', [])
      commit('CLEAR_THINKING_STEPS')
    },

    // 新增：记录AI思考步骤
    recordThinkingStep({ commit }, step) {
      commit('ADD_THINKING_STEP', step)
    },

    // 新增：清空思考步骤
    clearThinkingSteps({ commit }) {
      commit('CLEAR_THINKING_STEPS')
    }
  }
}) 