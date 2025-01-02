import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import VoiceChatView from '@/views/VoiceChatView.vue'
import MemoryView from '@/views/MemoryView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'chat',
      component: ChatView
    },
    {
      path: '/voice',
      name: 'voice-chat',
      component: VoiceChatView
    },
    {
      path: '/memories',
      name: 'memories',
      component: MemoryView
    }
  ]
})

export default router 