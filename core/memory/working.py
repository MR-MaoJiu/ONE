"""
工作记忆实现
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import heapq
from .base import Memory, MemoryStore, MemoryStorageException

class WorkingMemoryStore(MemoryStore):
    """工作记忆存储实现"""

    def __init__(self, max_size: int = 50, ttl: int = 3600):
        """
        初始化工作记忆存储
        
        Args:
            max_size: 最大存储容量
            ttl: 记忆生存时间（秒）
        """
        super().__init__()
        self.max_size = max_size
        self.ttl = ttl
        self.access_count = {}  # 访问计数
        self.last_accessed = {}  # 最后访问时间

    def add(self, memory: Memory) -> bool:
        """
        添加新的记忆
        
        如果达到容量上限，会自动清理最不重要的记忆
        """
        try:
            self._cleanup_expired()
            
            if len(self.memories) >= self.max_size:
                self._remove_least_important()
            
            self.memories[memory.memory_id] = memory
            self.access_count[memory.memory_id] = 1
            self.last_accessed[memory.memory_id] = datetime.now()
            
            return True
        except Exception as e:
            raise MemoryStorageException(f"添加记忆失败: {str(e)}")

    def get(self, memory_id: str) -> Optional[Memory]:
        """
        获取记忆
        
        每次访问都会更新访问计数和最后访问时间
        """
        try:
            self._cleanup_expired()
            
            memory = self.memories.get(memory_id)
            if memory:
                self.access_count[memory_id] = self.access_count.get(memory_id, 0) + 1
                self.last_accessed[memory_id] = datetime.now()
            
            return memory
        except Exception as e:
            raise MemoryStorageException(f"获取记忆失败: {str(e)}")

    def _cleanup_expired(self) -> None:
        """清理过期记忆"""
        current_time = datetime.now()
        expired_ids = []
        
        for memory_id, last_accessed in self.last_accessed.items():
            if (current_time - last_accessed).total_seconds() > self.ttl:
                expired_ids.append(memory_id)
        
        for memory_id in expired_ids:
            self.delete(memory_id)

    def _remove_least_important(self) -> None:
        """移除最不重要的记忆"""
        if not self.memories:
            return
        
        # 计算综合重要性分数
        # 综合考虑原始重要性分数、访问频率和最后访问时间
        memory_scores = []
        current_time = datetime.now()
        
        for memory_id, memory in self.memories.items():
            access_score = self.access_count.get(memory_id, 0) / 10  # 访问频率影响
            time_score = 1 - min(1, (current_time - self.last_accessed[memory_id]).total_seconds() / self.ttl)  # 时间衰减
            final_score = memory.importance_score * 0.5 + access_score * 0.3 + time_score * 0.2
            
            memory_scores.append((final_score, memory_id))
        
        # 移除最不重要的记忆
        _, memory_id = min(memory_scores)
        self.delete(memory_id)

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "total_memories": len(self.memories),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "memory_ids": list(self.memories.keys()),
            "access_counts": self.access_count.copy()
        } 