import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import Memories from '../views/Memories.vue'
import Snapshots from '../views/Snapshots.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'chat',
      component: ChatView
    },
    {
      path: '/memories',
      name: 'memories',
      component: Memories
    },
    {
      path: '/snapshots',
      name: 'snapshots',
      component: Snapshots
    }
  ]
})

export default router 