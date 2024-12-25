<template>
  <div class="memory-container">
    <div class="header">
      <h2>记忆管理</h2>
      <div class="button-group">
        <button @click="clearAllMemories" class="btn-danger">清空记忆</button>
      </div>
    </div>
    
    <!-- Tab 切换 -->
    <div class="tabs">
      <div 
        class="tab" 
        :class="{ active: activeTab === 'snapshots' }"
        @click="activeTab = 'snapshots'"
      >
        快照列表
      </div>
      <div 
        class="tab" 
        :class="{ active: activeTab === 'memories' }"
        @click="activeTab = 'memories'"
      >
        记忆列表
      </div>
    </div>
    
    <!-- 记忆列表 -->
    <div v-show="activeTab === 'memories'" class="section">
      <div class="memory-list">
        <div v-for="memory in memories" :key="memory.id" class="memory-item">
          <div class="memory-content text-ellipsis">{{ memory.content }}</div>
          <div class="memory-meta">
            <span>时间: {{ formatTime(memory.timestamp) }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 快照列表 -->
    <div v-show="activeTab === 'snapshots'" class="section">
      <div class="snapshot-list">
        <div v-for="snapshot in snapshots" :key="snapshot.id" class="snapshot-item">
          <div class="snapshot-header">
            <span class="summary">{{ snapshot.metadata.summary || '无摘要' }}</span>
          </div>
          <div class="content">
            <p>{{ snapshot.content }}</p>
          </div>
          <div class="key-points" v-if="snapshot.metadata.key_points && snapshot.metadata.key_points.length > 0">
            <h4>关键点：</h4>
            <ul>
              <li v-for="(point, index) in snapshot.metadata.key_points" :key="index">
                {{ point }}
              </li>
            </ul>
          </div>
          <div class="snapshot-meta">
            <span>时间: {{ formatTime(snapshot.timestamp) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import dayjs from 'dayjs'

const store = useStore()
const activeTab = ref('snapshots') // 默认选中快照列表

// 从store获取数据
const memories = computed(() => store.state.memories)
const snapshots = computed(() => store.state.snapshots)

// 在组件挂载时加载数据
onMounted(async () => {
  await store.dispatch('fetchMemories')
  await store.dispatch('fetchSnapshots')
})

// 清空所有记忆
async function clearAllMemories() {
  if (!confirm('确定要清空所有记忆和快照吗？此操作不可恢复！')) {
    return
  }
  
  try {
    await store.dispatch('clearMemories')
  } catch (error) {
    console.error('清空记忆失败:', error)
    alert(error.message)
  }
}

// 格式化时间
function formatTime(timestamp) {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}
</script>

<style scoped>
.memory-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  height: calc(100vh - 50px);
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  color: var(--primary-color);
  font-size: 1.5rem;
  font-weight: 500;
}

.button-group {
  display: flex;
  gap: 10px;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: var(--primary-gradient);
  color: var(--bg-dark);
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
}

button.btn-danger {
  background: linear-gradient(135deg, #ff4d4d 0%, #f02929 100%);
  color: white;
}

button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 255, 157, 0.3);
}

button.btn-danger:hover {
  box-shadow: 0 4px 12px rgba(255, 77, 77, 0.3);
}

.tabs {
  display: flex;
  gap: 2px;
  margin-bottom: 20px;
  background: var(--bg-dark);
  padding: 4px;
  border-radius: 8px;
}

.tab {
  padding: 10px 20px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
  color: var(--text-dim);
  border: 1px solid transparent;
}

.tab:hover {
  color: var(--text-light);
  background: rgba(0, 255, 157, 0.1);
  border-color: rgba(0, 255, 157, 0.2);
}

.tab.active {
  background: var(--primary-gradient);
  color: var(--bg-dark);
  box-shadow: 0 2px 8px rgba(0, 255, 157, 0.2);
}

.section {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
}

.memory-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.snapshot-list {
  display: grid;
  gap: 15px;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.memory-item {
  padding: 12px;
  border-radius: 8px;
  background: var(--bg-dark);
  box-shadow: 0 2px 8px rgba(0, 150, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  border: 1px solid rgba(0, 255, 157, 0.1);
  transition: all 0.3s ease;
}

.memory-item:hover {
  border-color: rgba(0, 255, 157, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 150, 255, 0.2);
}

.memory-content {
  flex: 1;
  line-height: 1.5;
  color: var(--text-light);
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.memory-meta {
  font-size: 0.9em;
  color: var(--text-dim);
  white-space: nowrap;
}

.snapshot-item {
  padding: 15px;
  border-radius: 8px;
  background: var(--bg-dark);
  box-shadow: 0 2px 8px rgba(0, 150, 255, 0.1);
  border: 1px solid rgba(0, 255, 157, 0.1);
  transition: all 0.3s ease;
}

.snapshot-item:hover {
  border-color: rgba(0, 255, 157, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 150, 255, 0.2);
}

.snapshot-header {
  margin-bottom: 10px;
}

.summary {
  font-weight: bold;
  color: var(--primary-color);
}

.content {
  margin: 10px 0;
  color: var(--text-light);
  line-height: 1.5;
}

.key-points {
  margin-top: 10px;
  
  h4 {
    margin: 0 0 10px 0;
    color: var(--text-light);
  }
  
  ul {
    margin: 0;
    padding-left: 20px;
    color: var(--text-light);
  }
  
  li {
    margin-bottom: 5px;
    color: var(--text-dim);
  }
}

.snapshot-meta {
  margin-top: 10px;
  font-size: 0.9em;
  color: var(--text-dim);
}

/* 自定义滚动条 */
.section::-webkit-scrollbar {
  width: 4px;
}

.section::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.section::-webkit-scrollbar-thumb {
  background: var(--primary-gradient);
  border-radius: 2px;
}

@media (max-width: 768px) {
  .memory-container {
    padding: 10px;
  }

  .tabs {
    padding: 3px;
  }

  .tab {
    padding: 8px 12px;
    font-size: 0.9em;
  }

  .snapshot-list {
    grid-template-columns: 1fr;
  }

  .memory-item, .snapshot-item {
    padding: 10px;
  }
}
</style> 