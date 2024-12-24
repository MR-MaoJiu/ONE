import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import MemoryView from '../views/MemoryView.vue'

const routes = [
  {
    path: '/',
    name: 'chat',
    component: ChatView
  },
  {
    path: '/memories',
    name: 'memories',
    component: MemoryView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 