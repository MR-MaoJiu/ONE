<template>
  <div class="app-container">
    <nav class="nav-bar">
      <router-link to="/" class="nav-item">聊天</router-link>
      <router-link to="/memories" class="nav-item">记忆管理</router-link>
    </nav>
    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav-bar {
  background: #fff;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  gap: 1rem;
}

.nav-item {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  color: #333;
  text-decoration: none;
  transition: all 0.3s ease;
}

.nav-item:hover {
  background: #f0f0f0;
}

.router-link-active {
  background: #007bff;
  color: white;
}

.router-link-active:hover {
  background: #0056b3;
}

.main-content {
  flex: 1;
  padding: 1rem;
}
</style> 