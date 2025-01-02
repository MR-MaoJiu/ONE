<template>
  <div class="app-container">
    <nav class="nav-bar">
      <router-link to="/" class="nav-item" :class="{ active: $route.name === 'chat' }">
        <i class="fas fa-comments"></i>
        文字聊天
      </router-link>
      <router-link to="/voice" class="nav-item" :class="{ active: $route.name === 'voice-chat' }">
        <i class="fas fa-microphone"></i>
        语音聊天
      </router-link>
      <router-link to="/memories" class="nav-item" :class="{ active: $route.name === 'memories' }">
        <i class="fas fa-brain"></i>
        记忆管理
      </router-link>
    </nav>
    
    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1a1a1a;
}

.nav-bar {
  display: flex;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  gap: 1rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  color: #fff;
  text-decoration: none;
  transition: all 0.3s ease;
}

.nav-item:hover {
  background: rgba(64, 158, 255, 0.1);
}

.nav-item.active {
  background: #409EFF;
}

.main-content {
  flex: 1;
  overflow: hidden;
}
</style> 