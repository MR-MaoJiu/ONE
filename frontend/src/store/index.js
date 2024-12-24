import { createStore } from 'vuex'
import axios from 'axios'

// 配置 axios 默认值
axios.defaults.headers.common['Content-Type'] = 'application/json'

export default createStore({
  state: {
    messages: [],
    currentConversationId: null,
    memories: [],
    snapshots: []
  },
  
  mutations: {
    SET_MESSAGES(state, messages) {
      state.messages = messages
    },
    ADD_MESSAGE(state, message) {
      state.messages.push(message)
    },
    SET_CONVERSATION_ID(state, id) {
      state.currentConversationId = id
    },
    SET_MEMORIES(state, memories) {
      state.memories = memories
    },
    SET_SNAPSHOTS(state, snapshots) {
      state.snapshots = snapshots
    }
  },
  
  actions: {
    async sendMessage({ commit, state }, message) {
      try {
        const response = await axios.post('/chat', {
          content: message.content,
          context: {
            current_query: message.content,
            history: state.messages.map(m => ({
              is_user: m.type === 'user',
              content: m.content,
              timestamp: m.timestamp
            }))
          }
        })
        
        // 添加用户消息
        commit('ADD_MESSAGE', {
          type: 'user',
          content: message.content,
          timestamp: new Date().toISOString()
        })
        
        // 添加AI回复
        commit('ADD_MESSAGE', {
          type: 'system',
          content: response.data.response,
          timestamp: new Date().toISOString()
        })
        
        return response.data
      } catch (error) {
        console.error('发送消息失败:', error)
        if (error.response) {
          throw new Error(error.response.data.error || '服务器响应错误')
        } else if (error.request) {
          throw new Error('无法连接到服务器')
        } else {
          throw new Error('发送请求失败')
        }
      }
    },
    
    async fetchMemories({ commit }) {
      try {
        const response = await axios.get('/memories')
        commit('SET_MEMORIES', response.data)
      } catch (error) {
        console.error('获取记忆失败:', error)
        throw error
      }
    },
    
    async fetchSnapshots({ commit }) {
      try {
        const response = await axios.get('/snapshots')
        commit('SET_SNAPSHOTS', response.data)
      } catch (error) {
        console.error('获取快照失败:', error)
        throw error
      }
    },
    
    async updateSnapshots({ dispatch }) {
      try {
        await axios.post('/snapshots/update')
        await dispatch('fetchSnapshots')
      } catch (error) {
        console.error('更新快照失败:', error)
        throw error
      }
    },
    
    async clearMemories({ commit }) {
      try {
        await axios.delete('/memories')
        commit('SET_MEMORIES', [])
        commit('SET_SNAPSHOTS', [])
      } catch (error) {
        console.error('清空记忆失败:', error)
        throw error
      }
    },
    
    startNewConversation({ commit }) {
      const conversationId = `conv-${Date.now()}`
      commit('SET_CONVERSATION_ID', conversationId)
      commit('SET_MESSAGES', [])
      return conversationId
    }
  }
}) 