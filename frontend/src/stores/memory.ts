import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface MemoryNode {
  id: string
  title: string
  content: string
  x: number
  y: number
  isActive: boolean
}

export interface MemoryStore {
  nodes: MemoryNode[]
  activeNodes: string[]
  hasNodes: boolean
  activeNodeCount: number
  initializeNodePositions: (containerWidth: number, containerHeight: number) => void
  updateNodes: (newNodes: MemoryNode[]) => void
  activateNodes: (nodeIds: string[]) => void
  resetNodes: () => void
  removeNode: (nodeId: string) => void
  updateNodePosition: (nodeId: string, x: number, y: number) => void
}

export const useMemoryStore = defineStore('memory', () => {
  const nodes = ref<MemoryNode[]>([])
  const activeNodes = ref<string[]>([])

  // 计算属性
  const hasNodes = computed(() => nodes.value.length > 0)
  const activeNodeCount = computed(() => activeNodes.value.length)

  // 初始化节点位置
  const initializeNodePositions = (containerWidth: number, containerHeight: number) => {
    const centerX = containerWidth / 2
    const centerY = containerHeight / 2
    const radius = Math.min(containerWidth, containerHeight) * 0.3

    nodes.value = nodes.value.map((node, index) => {
      const angle = (index / nodes.value.length) * 2 * Math.PI
      return {
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      }
    })
  }

  // 更新节点
  const updateNodes = (newNodes: MemoryNode[]) => {
    nodes.value = newNodes.map(node => ({
      ...node,
      isActive: activeNodes.value.includes(node.id)
    }))
  }

  // 激活节点
  const activateNodes = (nodeIds: string[]) => {
    activeNodes.value = nodeIds
    nodes.value = nodes.value.map(node => ({
      ...node,
      isActive: nodeIds.includes(node.id)
    }))
  }

  // 重置所有节点状态
  const resetNodes = () => {
    nodes.value = nodes.value.map(node => ({
      ...node,
      isActive: false
    }))
    activeNodes.value = []
  }

  // 移除节点
  const removeNode = (nodeId: string) => {
    nodes.value = nodes.value.filter(node => node.id !== nodeId)
    activeNodes.value = activeNodes.value.filter(id => id !== nodeId)
  }

  // 更新节点位置
  const updateNodePosition = (nodeId: string, x: number, y: number) => {
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      node.x = x
      node.y = y
    }
  }

  return {
    nodes,
    activeNodes,
    hasNodes,
    activeNodeCount,
    initializeNodePositions,
    updateNodes,
    activateNodes,
    resetNodes,
    removeNode,
    updateNodePosition
  }
}) 