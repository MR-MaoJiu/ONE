"""
情节记忆实现
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
import json
from .base import Memory, MemoryStore, MemoryStorageException

class EpisodicMemory(Memory):
    """扩展的情节记忆类"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.related_memories: Set[str] = set()  # 相关记忆ID集合
        self.tags: List[str] = []  # 标签列表
        self.decay_rate: float = 0.1  # 重要性衰减率

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "related_memories": list(self.related_memories),
            "tags": self.tags,
            "decay_rate": self.decay_rate
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EpisodicMemory':
        memory = super().from_dict(data)
        memory.related_memories = set(data.get("related_memories", []))
        memory.tags = data.get("tags", [])
        memory.decay_rate = data.get("decay_rate", 0.1)
        return memory

class EpisodicMemoryStore(MemoryStore):
    """情节记忆存储实现"""

    def __init__(self, max_size: int = 1000, importance_threshold: float = 0.7):
        """
        初始化情节记忆存储
        
        Args:
            max_size: 最大存储容量
            importance_threshold: 重要性阈值，低于此值的记忆可能被清理
        """
        super().__init__()
        self.max_size = max_size
        self.importance_threshold = importance_threshold
        self.tag_index = defaultdict(set)  # 标签索引
        self.temporal_index = defaultdict(list)  # 时间索引

    def add(self, memory: EpisodicMemory) -> bool:
        """添加新的情节记忆"""
        try:
            if len(self.memories) >= self.max_size:
                self._cleanup_unimportant()

            self.memories[memory.memory_id] = memory
            
            # 更新索引
            self._update_indices(memory)
            
            return True
        except Exception as e:
            raise MemoryStorageException(f"添加情节记忆失败: {str(e)}")

    def get(self, memory_id: str) -> Optional[EpisodicMemory]:
        """获取情节记忆"""
        try:
            memory = self.memories.get(memory_id)
            if memory:
                # 更新重要性分数（考虑时间衰减）
                self._update_importance(memory)
            return memory
        except Exception as e:
            raise MemoryStorageException(f"获取情节记忆失败: {str(e)}")

    def update(self, memory: EpisodicMemory) -> bool:
        """更新情节记忆"""
        try:
            if memory.memory_id not in self.memories:
                return False

            # 移除旧索引
            old_memory = self.memories[memory.memory_id]
            self._remove_from_indices(old_memory)

            # 更新记忆和索引
            self.memories[memory.memory_id] = memory
            self._update_indices(memory)

            return True
        except Exception as e:
            raise MemoryStorageException(f"更新情节记忆失败: {str(e)}")

    def delete(self, memory_id: str) -> bool:
        """删除情节记忆"""
        try:
            if memory_id not in self.memories:
                return False

            memory = self.memories[memory_id]
            self._remove_from_indices(memory)
            del self.memories[memory_id]

            return True
        except Exception as e:
            raise MemoryStorageException(f"删除情节记忆失败: {str(e)}")

    def list(self, filters: Dict[str, Any] = None) -> List[EpisodicMemory]:
        """列出情节记忆"""
        try:
            memories = list(self.memories.values())

            if filters:
                if "tags" in filters:
                    tag_memories = set.intersection(
                        *[self.tag_index[tag] for tag in filters["tags"]]
                    )
                    memories = [m for m in memories if m.memory_id in tag_memories]

                if "start_time" in filters:
                    memories = [m for m in memories if m.timestamp >= filters["start_time"]]

                if "end_time" in filters:
                    memories = [m for m in memories if m.timestamp <= filters["end_time"]]

                if "min_importance" in filters:
                    memories = [m for m in memories if m.importance_score >= filters["min_importance"]]

            # 更新所有记忆的重要性分数
            for memory in memories:
                self._update_importance(memory)

            # 按重要性分数降序排序
            memories.sort(key=lambda x: x.importance_score, reverse=True)

            return memories
        except Exception as e:
            raise MemoryStorageException(f"列出情节记忆失败: {str(e)}")

    def _update_indices(self, memory: EpisodicMemory) -> None:
        """更新索引"""
        # 更新标签索引
        for tag in memory.tags:
            self.tag_index[tag].add(memory.memory_id)

        # 更新时间索引
        date_key = memory.timestamp.strftime("%Y-%m-%d")
        if memory.memory_id not in self.temporal_index[date_key]:
            self.temporal_index[date_key].append(memory.memory_id)

    def _remove_from_indices(self, memory: EpisodicMemory) -> None:
        """从索引中移除"""
        # 从标签索引中移除
        for tag in memory.tags:
            self.tag_index[tag].discard(memory.memory_id)

        # 从时间索引中移除
        date_key = memory.timestamp.strftime("%Y-%m-%d")
        if memory.memory_id in self.temporal_index[date_key]:
            self.temporal_index[date_key].remove(memory.memory_id)

    def _update_importance(self, memory: EpisodicMemory) -> None:
        """更新重要性分数（考虑时间衰减）"""
        days_passed = (datetime.now() - memory.timestamp).days
        decay = memory.decay_rate * days_passed
        memory.importance_score = max(0.1, memory.importance_score - decay)

    def _cleanup_unimportant(self) -> None:
        """清理不重要的记忆"""
        if not self.memories:
            return

        # 按重要性分数排序
        memories_by_importance = sorted(
            self.memories.items(),
            key=lambda x: x[1].importance_score
        )

        # 移除最不重要的记忆，直到低于最大容量
        while len(self.memories) >= self.max_size:
            memory_id, memory = memories_by_importance.pop(0)
            if memory.importance_score < self.importance_threshold:
                self.delete(memory_id)
            else:
                break  # 如果重要性分数高于阈值，停止清理

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "total_memories": len(self.memories),
            "max_size": self.max_size,
            "importance_threshold": self.importance_threshold,
            "total_tags": len(self.tag_index),
            "memories_by_date": {
                date: len(memories) 
                for date, memories in self.temporal_index.items()
            }
        }