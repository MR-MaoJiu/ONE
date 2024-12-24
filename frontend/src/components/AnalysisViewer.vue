<template>
  <div class="analysis-viewer">
    <div class="analysis-steps">
      <div v-for="(step, index) in analysisSteps" 
           :key="index" 
           class="analysis-step"
           :class="{ active: currentStep === index }">
        <div class="step-header" @click="selectStep(index)">
          <span class="step-number">{{ index + 1 }}</span>
          <span class="step-name">{{ step.step }}</span>
          <span class="step-time">{{ formatTime(step.timestamp) }}</span>
        </div>
        
        <div class="step-content" v-show="currentStep === index">
          <div class="step-description">{{ step.description }}</div>
          
          <!-- 输入数据展示 -->
          <div class="input-section">
            <h4>输入数据</h4>
            <div class="data-viewer">
              <template v-if="step.step === '情感分析' || step.step === '概念分析'">
                <div class="text-content">
                  <span v-for="(word, i) in highlightText(step.input.text, getKeywords(step))" 
                        :key="i"
                        :class="{ highlighted: word.highlight }">
                    {{ word.text }}
                  </span>
                </div>
              </template>
              <template v-else>
                <pre>{{ JSON.stringify(step.input, null, 2) }}</pre>
              </template>
            </div>
          </div>
          
          <!-- 输出数据展示 -->
          <div class="output-section">
            <h4>分析结果</h4>
            <div class="data-viewer">
              <template v-if="step.step === '情感分析'">
                <div class="emotion-result">
                  <div v-for="(value, emotion) in step.output" :key="emotion" class="emotion-item">
                    <span class="emotion-label">{{ emotion }}</span>
                    <div class="emotion-bar">
                      <div class="emotion-value" :style="getBarStyle(value)"></div>
                    </div>
                    <span class="emotion-score">{{ formatPercentage(value) }}</span>
                  </div>
                </div>
              </template>
              <template v-else-if="step.step === '概念分析'">
                <div class="concepts-result">
                  <div v-for="concept in step.output.concepts" :key="concept.name" class="concept-item">
                    <span class="concept-name">{{ concept.name }}</span>
                    <span class="concept-type">{{ concept.type }}</span>
                    <div class="concept-relevance">
                      <div class="relevance-bar" :style="getBarStyle(concept.relevance)"></div>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else-if="step.step === '基础快照匹配' || step.step === '详细快照匹配'">
                <div class="snapshot-matches">
                  <div v-for="snapshot in step.output.matched_snapshots" 
                       :key="snapshot.snapshot_id" 
                       class="snapshot-item">
                    <div class="snapshot-header">
                      <span class="snapshot-id">{{ snapshot.snapshot_id }}</span>
                      <span class="match-score" v-if="snapshot.relevance_score">
                        {{ formatPercentage(snapshot.relevance_score) }}
                      </span>
                    </div>
                    <div class="snapshot-details">
                      <template v-if="step.step === '基础快照匹配'">
                        <div class="category">{{ snapshot.category }}</div>
                        <div class="keywords">
                          <span v-for="keyword in snapshot.keywords" 
                                :key="keyword"
                                class="keyword">{{ keyword }}</span>
                        </div>
                      </template>
                      <template v-else>
                        <div class="summary">{{ snapshot.summary }}</div>
                        <div class="elements">
                          <span v-for="element in snapshot.key_elements" 
                                :key="element"
                                class="element">{{ element }}</span>
                        </div>
                      </template>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else-if="step.step === '记忆评估'">
                <div class="memory-results">
                  <div v-for="memory in step.output.relevant_memories" 
                       :key="memory.memory.memory_id" 
                       class="memory-item">
                    <div class="memory-header">
                      <span class="memory-id">{{ memory.memory.memory_id }}</span>
                      <span class="relevance-score">{{ formatPercentage(memory.relevance_score) }}</span>
                    </div>
                    <div class="memory-content">{{ memory.memory.content }}</div>
                    <div class="memory-reason">{{ memory.reason }}</div>
                    <div class="memory-suggestion">{{ memory.usage_suggestion }}</div>
                  </div>
                </div>
              </template>
              <template v-else>
                <pre>{{ JSON.stringify(step.output, null, 2) }}</pre>
              </template>
            </div>
          </div>
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
    getBarStyle(value) {
      return { width: (value * 100) + '%' }
    },
    getKeywords(step) {
      if (step.step === '情感分析') {
        return Object.keys(step.output)
      } else if (step.step === '概念分析') {
        return step.output.concepts.map(c => c.name)
      }
      return []
    },
    highlightText(text, keywords) {
      if (!text || !keywords || keywords.length === 0) {
        return [{ text, highlight: false }]
      }
      
      const result = []
      let lastIndex = 0
      
      // 创建正则表达式匹配所有关键词
      const pattern = new RegExp(keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'gi')
      
      let match
      while ((match = pattern.exec(text)) !== null) {
        if (match.index > lastIndex) {
          result.push({
            text: text.substring(lastIndex, match.index),
            highlight: false
          })
        }
        result.push({
          text: match[0],
          highlight: true
        })
        lastIndex = pattern.lastIndex
      }
      
      if (lastIndex < text.length) {
        result.push({
          text: text.substring(lastIndex),
          highlight: false
        })
      }
      
      return result
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

.analysis-step {
  margin-bottom: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.step-header {
  padding: 12px;
  background-color: #f5f5f5;
  cursor: pointer;
  display: flex;
  align-items: center;
  border-radius: 8px 8px 0 0;
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
}

.step-name {
  font-weight: 500;
  flex-grow: 1;
}

.step-time {
  color: #666;
  font-size: 0.9em;
}

.step-content {
  padding: 16px;
}

.step-description {
  color: #666;
  margin-bottom: 16px;
}

.data-viewer {
  background-color: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  margin-top: 8px;
}

.text-content {
  line-height: 1.6;
}

.highlighted {
  background-color: #fff176;
  padding: 2px 0;
}

.emotion-result, .concepts-result {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.emotion-item, .concept-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.emotion-bar, .concept-relevance {
  flex-grow: 1;
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.emotion-value, .relevance-bar {
  height: 100%;
  background-color: #1976d2;
  transition: width 0.3s ease;
}

.snapshot-matches, .memory-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.snapshot-item, .memory-item {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 12px;
}

.snapshot-header, .memory-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.match-score, .relevance-score {
  color: #1976d2;
  font-weight: 500;
}

.keywords, .elements {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.keyword, .element {
  background-color: #e3f2fd;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9em;
}

.memory-content {
  margin: 8px 0;
  line-height: 1.6;
}

.memory-reason, .memory-suggestion {
  color: #666;
  font-size: 0.9em;
  margin-top: 4px;
}

.active {
  border-color: #1976d2;
}

.active .step-header {
  background-color: #e3f2fd;
}
</style> 