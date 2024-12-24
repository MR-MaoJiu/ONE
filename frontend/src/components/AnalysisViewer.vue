<template>
  <div class="analysis-viewer">
    <div class="analysis-steps">
      <div v-for="(step, index) in analysisSteps" 
           :key="index" 
           class="analysis-step"
           :class="{ active: currentStep === index }">
        <div class="step-header" @click="selectStep(index)">
          <span class="step-number">{{ index + 1 }}</span>
          <span class="step-name">{{ getStepName(step.step) }}</span>
          <span class="step-time">{{ formatTime(step.timestamp) }}</span>
        </div>
        
        <div class="step-content" v-show="currentStep === index">
          <div class="step-description">{{ step.description }}</div>
          
          <!-- 记忆检索结果 -->
          <template v-if="step.step === 'memory_retrieval'">
            <div class="memory-results">
              <div v-for="memory in step.output.relevant_memories" 
                   :key="memory.memory_id" 
                   class="memory-item">
                <div class="memory-header">
                  <span class="relevance-score">相关度: {{ formatPercentage(memory.relevance_score) }}</span>
                </div>
                <div class="memory-content">{{ memory.content }}</div>
                <div class="memory-reason">{{ memory.reason }}</div>
              </div>
            </div>
          </template>
          
          <!-- 快照匹配结果 -->
          <template v-else-if="step.step === 'snapshot_matching'">
            <div class="snapshot-matches">
              <div v-for="snapshot in step.output.matched_snapshots" 
                   :key="snapshot.id" 
                   class="snapshot-item">
                <div class="snapshot-header">
                  <span class="category">{{ snapshot.category }}</span>
                  <span class="match-score">
                    匹配度: {{ formatPercentage(snapshot.relevance_score) }}
                  </span>
                </div>
                <div class="key-points">
                  <div v-for="point in snapshot.key_points" 
                       :key="point"
                       class="key-point">
                    {{ point }}
                  </div>
                </div>
              </div>
            </div>
          </template>
          
          <!-- 其他分析步骤 -->
          <template v-else>
            <div class="step-result">
              <pre>{{ JSON.stringify(step.output, null, 2) }}</pre>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalysisViewer',
  props: {
    analysisSteps: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      currentStep: 0
    }
  },
  methods: {
    selectStep(index) {
      this.currentStep = index
    },
    formatTime(timestamp) {
      const date = new Date(timestamp)
      return date.toLocaleTimeString()
    },
    formatPercentage(value) {
      return (value * 100).toFixed(1) + '%'
    },
    getStepName(step) {
      const stepNames = {
        'memory_retrieval': '记忆检索',
        'snapshot_matching': '快照匹配',
        'response_generation': '回复生成'
      }
      return stepNames[step] || step
    }
  }
}
</script>

<style scoped>
.analysis-viewer {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.analysis-steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.analysis-step {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
}

.step-header {
  padding: 12px 16px;
  background-color: #f8f9fa;
  cursor: pointer;
  display: flex;
  align-items: center;
  border-radius: 8px 8px 0 0;
  transition: background-color 0.2s;
}

.step-header:hover {
  background-color: #f0f0f0;
}

.step-number {
  width: 24px;
  height: 24px;
  background-color: #1976d2;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-size: 0.9em;
}

.step-name {
  font-weight: 500;
  flex-grow: 1;
  color: #333;
}

.step-time {
  color: #666;
  font-size: 0.85em;
}

.step-content {
  padding: 16px;
}

.step-description {
  color: #666;
  margin-bottom: 16px;
  font-size: 0.9em;
  line-height: 1.5;
}

.memory-results, .snapshot-matches {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.memory-item, .snapshot-item {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 12px;
}

.memory-header, .snapshot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.relevance-score, .match-score {
  font-size: 0.85em;
  color: #1976d2;
  background: rgba(25, 118, 210, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
}

.memory-content {
  color: #333;
  margin-bottom: 8px;
  line-height: 1.5;
}

.memory-reason {
  color: #666;
  font-size: 0.9em;
  font-style: italic;
}

.category {
  font-weight: 500;
  color: #1976d2;
}

.key-points {
  margin-top: 8px;
}

.key-point {
  color: #333;
  margin-bottom: 4px;
  line-height: 1.4;
  position: relative;
  padding-left: 16px;
}

.key-point::before {
  content: "•";
  position: absolute;
  left: 0;
  color: #1976d2;
}

.step-result {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 12px;
}

.step-result pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.9em;
  line-height: 1.5;
  color: #333;
}
</style> 