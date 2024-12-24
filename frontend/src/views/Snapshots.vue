<template>
  <div class="snapshots-container">
    <!-- 头部 -->
    <div class="snapshots-header">
      <h1>记忆快照</h1>
      <el-button @click="$router.push('/')">返回对话</el-button>
      <el-button type="primary" @click="updateSnapshots">更新快照</el-button>
    </div>
    
    <!-- 快照树 -->
    <div class="snapshots-content">
      <el-tree
        :data="snapshots"
        :props="defaultProps"
        default-expand-all
      >
        <template #default="{ node, data }">
          <div class="snapshot-node">
            <!-- 基础快照 -->
            <template v-if="!node.parent">
              <div class="base-snapshot">
                <h3>{{ data.category }}</h3>
                <div class="keywords">
                  <el-tag
                    v-for="keyword in data.keywords"
                    :key="keyword"
                    size="small"
                  >
                    {{ keyword }}
                  </el-tag>
                </div>
              </div>
            </template>
            
            <!-- 详细快照 -->
            <template v-else>
              <div class="detail-snapshot">
                <div class="summary">{{ data.summary }}</div>
                <div class="tags">
                  <div class="emotions">
                    <el-tag
                      v-for="emotion in data.emotion_tags"
                      :key="emotion"
                      type="warning"
                      size="small"
                    >
                      {{ emotion }}
                    </el-tag>
                  </div>
                  <div class="elements">
                    <el-tag
                      v-for="element in data.key_elements"
                      :key="element"
                      type="info"
                      size="small"
                    >
                      {{ element }}
                    </el-tag>
                  </div>
                </div>
                <div class="time">
                  {{ formatTime(data.timestamp) }}
                </div>
              </div>
            </template>
          </div>
        </template>
      </el-tree>
      
      <!-- 空状态 -->
      <el-empty v-if="!snapshots.length"
                description="暂无快照">
      </el-empty>
    </div>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'

export default {
  name: 'Snapshots',
  
  setup() {
    const store = useStore()
    
    // 获取快照列表
    const snapshots = computed(() => store.state.snapshots)
    
    // 树形配置
    const defaultProps = {
      children: 'details',
      label: node => node.summary || node.category
    }
    
    // 加载快照
    const loadSnapshots = async () => {
      try {
        await store.dispatch('fetchSnapshots')
      } catch (error) {
        console.error('加载快照失败:', error)
        ElMessage.error('加载快照失败，请重试')
      }
    }
    
    // 更新快照
    const updateSnapshots = async () => {
      try {
        await store.dispatch('updateSnapshots')
        ElMessage.success('快照已更新')
      } catch (error) {
        console.error('更新快照失败:', error)
        ElMessage.error('更新快照失败，请重试')
      }
    }
    
    // 格式化时间
    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleString()
    }
    
    // 组件挂载时加载快照
    onMounted(loadSnapshots)
    
    return {
      snapshots,
      defaultProps,
      updateSnapshots,
      formatTime
    }
  }
}
</script>

<style lang="scss" scoped>
.snapshots-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  
  .snapshots-header {
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
  
  .snapshots-content {
    flex-grow: 1;
    padding: 20px;
    overflow-y: auto;
    
    .snapshot-node {
      width: 100%;
      
      .base-snapshot {
        h3 {
          margin: 0 0 10px;
        }
        
        .keywords {
          display: flex;
          gap: 5px;
          flex-wrap: wrap;
        }
      }
      
      .detail-snapshot {
        .summary {
          margin-bottom: 10px;
          white-space: pre-wrap;
        }
        
        .tags {
          display: flex;
          flex-direction: column;
          gap: 5px;
          margin-bottom: 10px;
          
          .emotions, .elements {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
          }
        }
        
        .time {
          font-size: 0.9em;
          color: #666;
        }
      }
    }
  }
}
</style> 