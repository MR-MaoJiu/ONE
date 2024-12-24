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

<style>
/* 全局样式 */
:root {
  --primary-color: #00ff9d;
  --primary-gradient: linear-gradient(135deg, #00ff9d 0%, #00a8ff 100%);
  --bg-dark: #1a1a1a;
  --bg-darker: #141414;
  --text-light: #e0e0e0;
  --text-dim: #888;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background: var(--bg-darker);
  color: var(--text-light);
  line-height: 1.6;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav-bar {
  background: var(--bg-dark);
  padding: 0.5rem 1rem;
  box-shadow: 0 2px 8px rgba(0, 150, 255, 0.15);
  display: flex;
  gap: 1rem;
  position: relative;
  z-index: 100;
  height: 50px;
  align-items: center;
}

.nav-item {
  padding: 0.35rem 0.8rem;
  border-radius: 4px;
  color: var(--text-light);
  text-decoration: none;
  transition: all 0.3s ease;
  border: 1px solid transparent;
  font-size: 0.95em;
}

.nav-item:hover {
  background: rgba(0, 255, 157, 0.1);
  border-color: rgba(0, 255, 157, 0.2);
}

.router-link-active {
  background: var(--primary-gradient);
  color: var(--bg-dark);
}

.router-link-active:hover {
  background: var(--primary-gradient);
  opacity: 0.9;
}

.main-content {
  flex: 1;
  position: relative;
  height: calc(100vh - 50px);
  overflow: hidden;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

::-webkit-scrollbar-thumb {
  background: var(--primary-gradient);
  border-radius: 3px;
}

/* 文本选择样式 */
::selection {
  background: rgba(0, 255, 157, 0.3);
  color: var(--text-light);
}
</style> 