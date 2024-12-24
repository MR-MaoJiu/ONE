<template>
  <div class="memory-container">
    <div class="header">
      <h2>记忆管理</h2>
      <div class="button-group">
        <button @click="clearAllMemories" class="danger">清空记忆</button>
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
            <span class="category">{{ snapshot.category }}</span>
            <span class="importance">重要性: {{ (snapshot.importance * 100).toFixed(0) }}%</span>
          </div>
          <div class="key-points">
            <h4>关键点：</h4>
            <ul>
              <li v-for="(point, index) in snapshot.key_points" :key="index">
                {{ point }}
              </li>
            </ul>
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
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.button-group {
  display: flex;
  gap: 10px;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: #007bff;
  color: white;
  cursor: pointer;
}

button.danger {
  background: #dc3545;
}

button:hover {
  opacity: 0.9;
}

.tabs {
  display: flex;
  gap: 2px;
  margin-bottom: 20px;
  background: #f0f0f0;
  padding: 4px;
  border-radius: 8px;
}

.tab {
  padding: 10px 20px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
  color: #666;
}

.tab:hover {
  background: rgba(255, 255, 255, 0.5);
}

.tab.active {
  background: white;
  color: #007bff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.section {
  margin-bottom: 30px;
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
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.memory-content {
  flex: 1;
  line-height: 1.5;
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.memory-meta {
  font-size: 0.9em;
  color: #666;
  white-space: nowrap;
}

.snapshot-item {
  padding: 15px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.snapshot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.category {
  font-weight: bold;
  color: #007bff;
}

.importance {
  font-size: 0.9em;
  color: #666;
}

.key-points {
  h4 {
    margin: 0 0 10px 0;
  }
  
  ul {
    margin: 0;
    padding-left: 20px;
  }
  
  li {
    margin-bottom: 5px;
  }
}
</style> 