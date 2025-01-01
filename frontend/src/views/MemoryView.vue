<template>
  <div class="memory-view">
    <!-- Tab 切换 -->
    <div class="tabs-container">
      <div class="tabs">
        <div 
          class="tab" 
          :class="{ active: activeTab === 'memories' }"
          @click="activeTab = 'memories'"
        >
          记忆列表
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'snapshots' }"
          @click="activeTab = 'snapshots'"
        >
          快照列表
        </div>
      </div>
      <button @click="clearAll" class="clear-all-btn">
        清空全部
      </button>
    </div>

    <!-- 记忆列表 -->
    <div v-show="activeTab === 'memories'" class="content-panel">
      <div class="memory-list">
        <div class="list-header">
          <h2>记忆列表</h2>
          <div class="header-actions">
            <button @click="refreshMemories" class="refresh-btn">
              刷新
            </button>
          </div>
        </div>
        <div class="list-content">
          <div v-for="memory in memories" 
               :key="memory.id" 
               class="memory-item"
               @click="showMemoryDetail(memory)">
            <div class="memory-header">
              <span class="memory-type">{{ memory.type || '记忆详情' }}</span>
              <span class="memory-time">{{ formatTime(memory.timestamp) }}</span>
            </div>
            <div class="memory-content">{{ truncateContent(memory.content) }}</div>
            <div class="memory-metadata" v-if="memory.metadata">
              <div v-if="memory.metadata.summary" class="memory-summary">
                {{ memory.metadata.summary }}
              </div>
              <div v-if="memory.metadata.key_points" class="memory-key-points">
                {{ memory.metadata.key_points.length }} 个关键点
              </div>
            </div>
            <div class="memory-footer">
              <span v-if="memory.metadata?.tags?.length" class="memory-tag">
                {{ memory.metadata.tags.join(', ') }}
              </span>
              <span v-if="memory.api_results" class="memory-api">
                包含API结果
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快照列表 -->
    <div v-show="activeTab === 'snapshots'" class="content-panel">
      <div class="snapshot-list">
        <div class="list-header">
          <h2>快照列表</h2>
          <div class="header-actions">
            <button @click="refreshSnapshots" class="refresh-btn">
              刷新
            </button>
          </div>
        </div>
        <div class="list-content">
          <div v-for="snapshot in snapshots" 
               :key="snapshot.id" 
               class="snapshot-item"
               @click="showSnapshotDetail(snapshot)">
            <div class="snapshot-header">
              <span class="snapshot-type">{{ getSnapshotType(snapshot) }}</span>
              <span class="snapshot-time">{{ formatTime(snapshot.timestamp) }}</span>
            </div>
            <div class="snapshot-summary" v-if="snapshot.metadata?.summary">
              {{ snapshot.metadata.summary }}
            </div>
            <div class="snapshot-content">{{ truncateContent(snapshot.content) }}</div>
            <div class="snapshot-footer">
              <span v-if="snapshot.metadata?.key_points?.length" class="snapshot-points">
                {{ snapshot.metadata.key_points.length }} 个关键点
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 记忆详情对话框 -->
    <MemoryDetailDialog
      v-model:show="showDetail"
      :memory="selectedMemory"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useStore } from 'vuex'
import dayjs from 'dayjs'
import MemoryDetailDialog from '../components/MemoryDetailDialog.vue'

const store = useStore()
const showDetail = ref(false)
const selectedMemory = ref(null)
const activeTab = ref('memories')
const memories = ref([])
const snapshots = ref([])

// 获取记忆列表
const refreshMemories = async () => {
  try {
    await store.dispatch('fetchMemories')
    memories.value = store.state.memories
  } catch (error) {
    console.error('获取记忆失败:', error)
    alert(error.message)
  }
}

// 获取快照列表
const refreshSnapshots = async () => {
  try {
    await store.dispatch('fetchSnapshots')
    snapshots.value = store.state.snapshots
  } catch (error) {
    console.error('获取快照失败:', error)
    alert(error.message)
  }
}

// 显示记忆详情
const showMemoryDetail = (memory) => {
  selectedMemory.value = memory
  showDetail.value = true
}

// 显示快照详情
const showSnapshotDetail = (snapshot) => {
  selectedMemory.value = snapshot
  showDetail.value = true
}

// 格式化时间
const formatTime = (timestamp) => {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

// 截断内容
const truncateContent = (content) => {
  if (!content) return ''
  return content.length > 100 ? content.slice(0, 100) + '...' : content
}

const getSnapshotType = (snapshot) => {
  if (!snapshot.type) {
    return snapshot.metadata?.is_meta ? '元快照' : '记忆快照'
  }
  return snapshot.type
}

// 清空记忆
const clearMemories = async () => {
  if (!confirm('确定要清空所有记忆吗？此操作不可恢复。')) {
    return
  }
  try {
    await store.dispatch('clearMemories')
    await refreshMemories()
  } catch (error) {
    console.error('清空记忆失败:', error)
    alert(error.message)
  }
}

// 清空所有数据
const clearAll = async () => {
  if (!confirm('确定要清空所有记忆和快照吗？此操作不可恢复。')) {
    return
  }
  try {
    await store.dispatch('clearMemories')
    await refreshMemories()
    await refreshSnapshots()
  } catch (error) {
    console.error('清空失败:', error)
    alert('清空失败: ' + error.message)
  }
}

onMounted(() => {
  refreshMemories()
  refreshSnapshots()
})
</script>

<style scoped>
.memory-view {
  padding: 20px;
  height: 100%;
  background: #1a1a1a;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tabs {
  display: flex;
  gap: 2px;
  background: #2a2a2a;
  padding: 4px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 150, 255, 0.15);
}

.tab {
  padding: 8px 16px;
  border-radius: 6px;
  color: #888;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
}

.tab:hover {
  color: #e0e0e0;
  background: rgba(0, 255, 157, 0.1);
}

.tab.active {
  background: linear-gradient(135deg, #00ff9d 0%, #00a8ff 100%);
  color: #1a1a1a;
}

.content-panel {
  flex: 1;
  background: #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 150, 255, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.memory-list {
  background: #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 150, 255, 0.15);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-header {
  padding: 16px;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-header h2 {
  margin: 0;
  color: #e0e0e0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.refresh-btn {
  background: none;
  border: 1px solid #333;
  color: #e0e0e0;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.refresh-btn:hover {
  background: rgba(0, 255, 157, 0.1);
  border-color: #00ff9d;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.memory-item {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.memory-item:hover {
  border-color: #00ff9d;
  box-shadow: 0 0 10px rgba(0, 255, 157, 0.2);
  transform: translateY(-1px);
}

.memory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.memory-type {
  font-size: 12px;
  color: #00ff9d;
  background: rgba(0, 255, 157, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.memory-time {
  font-size: 12px;
  color: #666;
}

.memory-content {
  color: #e0e0e0;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 8px;
  white-space: pre-wrap;
}

.memory-footer {
  display: flex;
  gap: 8px;
}

.memory-meta,
.memory-api {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  color: #888;
}

.snapshot-list {
  background: #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 150, 255, 0.15);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.snapshot-item {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.snapshot-item:hover {
  border-color: #00ff9d;
  box-shadow: 0 0 10px rgba(0, 255, 157, 0.2);
  transform: translateY(-1px);
}

.snapshot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.snapshot-type {
  font-size: 12px;
  color: #00a8ff;
  background: rgba(0, 168, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.snapshot-time {
  font-size: 12px;
  color: #666;
}

.snapshot-summary {
  color: #00ff9d;
  font-size: 14px;
  margin-bottom: 8px;
  padding: 4px 8px;
  background: rgba(0, 255, 157, 0.1);
  border-radius: 4px;
}

.snapshot-content {
  color: #e0e0e0;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 8px;
  white-space: pre-wrap;
}

.snapshot-footer {
  display: flex;
  gap: 8px;
}

.snapshot-points {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 168, 255, 0.1);
  color: #00a8ff;
}

.memory-metadata {
  margin: 8px 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.memory-summary {
  color: #00ff9d;
  font-size: 14px;
  padding: 4px 8px;
  background: rgba(0, 255, 157, 0.1);
  border-radius: 4px;
}

.memory-key-points {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 168, 255, 0.1);
  color: #00a8ff;
}

.memory-tag {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  color: #888;
}

.clear-btn {
  padding: 6px 12px;
  border-radius: 6px;
  background: #ff4757;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  background: #ff6b81;
}

.tabs-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.clear-all-btn {
  padding: 8px 16px;
  border-radius: 6px;
  background: linear-gradient(135deg, #ff4d4d 0%, #ff0000 100%);
  color: white;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.clear-all-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}
</style> 