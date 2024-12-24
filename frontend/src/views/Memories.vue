<template>
  <div class="memories-container">
    <!-- 头部 -->
    <div class="memories-header">
      <h1>记忆管理</h1>
      <el-button @click="$router.push('/')">返回对话</el-button>
      <el-button type="danger" @click="confirmClearMemories">清空所有记忆</el-button>
    </div>
    
    <!-- 记忆列表 -->
    <div class="memories-list">
      <el-timeline>
        <el-timeline-item
          v-for="memory in memories"
          :key="memory.id"
          :timestamp="formatTime(memory.timestamp)"
          placement="top"
        >
          <el-card>
            <!-- 记忆内容 -->
            <div class="memory-content">
              <p>{{ memory.content }}</p>
            </div>
            
            <!-- 记忆信息 -->
            <div class="memory-info">
              <!-- 分类标签 -->
              <div v-if="memory.category" class="category">
                <el-tag type="success" size="small">
                  {{ memory.category }}
                </el-tag>
              </div>
              
              <!-- 重要性分数 -->
              <div class="importance">
                重要性: {{ (memory.importance * 100).toFixed(0) }}%
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      
      <!-- 空状态 -->
      <el-empty v-if="!memories.length"
                description="暂无记忆">
      </el-empty>
    </div>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'Memories',
  
  setup() {
    const store = useStore()
    
    // 获取记忆列表
    const memories = computed(() => store.state.memories)
    
    // 加载记忆
    const loadMemories = async () => {
      try {
        await store.dispatch('fetchMemories')
      } catch (error) {
        console.error('加载记忆失败:', error)
        ElMessage.error('加载记忆失败，请重试')
      }
    }
    
    // 清空记忆
    const clearMemories = async () => {
      try {
        await store.dispatch('clearMemories')
        ElMessage.success('记忆已清空')
      } catch (error) {
        console.error('清空记忆失败:', error)
        ElMessage.error('清空记忆失败，请重试')
      }
    }
    
    // 确认清空记忆
    const confirmClearMemories = () => {
      ElMessageBox.confirm(
        '确定要清空所有记忆吗？此操作不可恢复',
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        clearMemories()
      }).catch(() => {})
    }
    
    // 格式化时间
    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleString()
    }
    
    // 组件挂载时加载记忆
    onMounted(loadMemories)
    
    return {
      memories,
      confirmClearMemories,
      formatTime
    }
  }
}
</script>

<style lang="scss" scoped>
.memories-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  
  .memories-header {
    padding: 20px;
    background: white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    gap: 20px;
    
    h1 {
      margin: 0;
      flex-grow: 1;
    }
  }
  
  .memories-list {
    flex-grow: 1;
    padding: 20px;
    overflow-y: auto;
    
    .el-timeline {
      padding: 0;
    }
    
    .el-card {
      margin-bottom: 10px;
      
      .memory-content {
        p {
          margin: 0;
          white-space: pre-wrap;
        }
      }
      
      .memory-info {
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid #eee;
        
        .category {
          margin-bottom: 10px;
        }
        
        .importance {
          font-size: 0.9em;
          color: #666;
        }
      }
    }
  }
}
</style> 