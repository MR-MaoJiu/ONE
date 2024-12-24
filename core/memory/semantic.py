"""
语义记忆实现
"""
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict
import json
from datetime import datetime
from .base import Memory, MemoryStore, MemoryStorageException

class Concept:
    """概念类"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.attributes: Dict[str, float] = {}  # 属性及其强度
        self.related_concepts: Dict[str, float] = {}  # 相关概念及其关联强度
        self.memory_references: Set[str] = set()  # 引用此概念的记忆ID
        self.last_updated = datetime.now()
        self.update_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "attributes": self.attributes,
            "related_concepts": self.related_concepts,
            "memory_references": list(self.memory_references),
            "last_updated": self.last_updated.isoformat(),
            "update_count": self.update_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Concept':
        concept = cls(data["name"], data["description"])
        concept.attributes = data["attributes"]
        concept.related_concepts = data["related_concepts"]
        concept.memory_references = set(data["memory_references"])
        concept.last_updated = datetime.fromisoformat(data["last_updated"])
        concept.update_count = data["update_count"]
        return concept

class SemanticMemory(Memory):
    """语义记忆类"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.concepts: List[str] = []  # 概念名称列表
        self.concept_weights: Dict[str, float] = {}  # 概念权重

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "concepts": self.concepts,
            "concept_weights": self.concept_weights
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticMemory':
        memory = super().from_dict(data)
        memory.concepts = data.get("concepts", [])
        memory.concept_weights = data.get("concept_weights", {})
        return memory

class SemanticMemoryStore(MemoryStore):
    """语义记忆存储实现"""

    def __init__(self, max_concepts: int = 5000, min_relation_strength: float = 0.5):
        """
        初始化语义记忆存储
        
        Args:
            max_concepts: 最大概念数量
            min_relation_strength: 最小关系强度
        """
        super().__init__()
        self.max_concepts = max_concepts
        self.min_relation_strength = min_relation_strength
        self.concepts = {}  # 概念存储
        self.concept_index = defaultdict(set)  # 概念到记忆的索引

    def add(self, memory: SemanticMemory) -> bool:
        """添加语义记忆"""
        try:
            self.memories[memory.memory_id] = memory
            
            # 更新概念索引
            for concept_name in memory.concepts:
                self.concept_index[concept_name].add(memory.memory_id)
                
                # 如果是新概念，创建概念对象
                if concept_name not in self.concepts:
                    self._create_concept(concept_name)
                
                # 更新概念引用
                concept = self.concepts[concept_name]
                concept.memory_references.add(memory.memory_id)
                concept.update_count += 1
                concept.last_updated = datetime.now()
            
            # 更新概念间的关系
            self._update_concept_relations(memory)
            
            return True
        except Exception as e:
            raise MemoryStorageException(f"添加语义记忆失败: {str(e)}")

    def update(self, memory: SemanticMemory) -> bool:
        """更新语义记忆"""
        try:
            if memory.memory_id not in self.memories:
                return False

            old_memory = self.memories[memory.memory_id]
            
            # 移除旧概念索引
            for concept_name in old_memory.concepts:
                self.concept_index[concept_name].discard(memory.memory_id)
                if concept_name in self.concepts:
                    self.concepts[concept_name].memory_references.discard(memory.memory_id)

            # 更新记忆
            self.memories[memory.memory_id] = memory
            
            # 更新新概念索引
            for concept_name in memory.concepts:
                self.concept_index[concept_name].add(memory.memory_id)
                if concept_name not in self.concepts:
                    self._create_concept(concept_name)
                self.concepts[concept_name].memory_references.add(memory.memory_id)

            # 更新概念关系
            self._update_concept_relations(memory)
            
            return True
        except Exception as e:
            raise MemoryStorageException(f"更新语义记忆失败: {str(e)}")

    def delete(self, memory_id: str) -> bool:
        """删除语义记忆"""
        try:
            if memory_id not in self.memories:
                return False

            memory = self.memories[memory_id]
            
            # 清理概念索引
            for concept_name in memory.concepts:
                self.concept_index[concept_name].discard(memory_id)
                if concept_name in self.concepts:
                    self.concepts[concept_name].memory_references.discard(memory_id)

            del self.memories[memory_id]
            return True
        except Exception as e:
            raise MemoryStorageException(f"删除语义记忆失败: {str(e)}")

    def list(self, filters: Dict[str, Any] = None) -> List[SemanticMemory]:
        """列出语义记忆"""
        try:
            memories = list(self.memories.values())

            if filters:
                if "concepts" in filters:
                    concept_memories = set.intersection(
                        *[self.concept_index[concept] for concept in filters["concepts"]]
                    )
                    memories = [m for m in memories if m.memory_id in concept_memories]

                if "min_weight" in filters:
                    memories = [
                        m for m in memories 
                        if any(w >= filters["min_weight"] for w in m.concept_weights.values())
                    ]

            return sorted(memories, key=lambda x: x.importance_score, reverse=True)
        except Exception as e:
            raise MemoryStorageException(f"列出语义记忆失败: {str(e)}")

    def get_concept(self, concept_name: str) -> Optional[Concept]:
        """获取概念"""
        return self.concepts.get(concept_name)

    def find_related_concepts(self, concept_name: str, min_strength: float = None) -> List[Tuple[str, float]]:
        """查找相关概念"""
        try:
            concept = self.concepts.get(concept_name)
            if not concept:
                return []

            min_strength = min_strength or self.min_relation_strength
            related = [
                (name, strength) 
                for name, strength in concept.related_concepts.items()
                if strength >= min_strength
            ]
            
            return sorted(related, key=lambda x: x[1], reverse=True)
        except Exception as e:
            raise MemoryStorageException(f"查找相关概念失败: {str(e)}")

    def find_memories_by_concept(self, concept_name: str) -> List[SemanticMemory]:
        """通过概念查找记忆"""
        try:
            memory_ids = self.concept_index.get(concept_name, set())
            memories = [
                self.memories[mid] 
                for mid in memory_ids 
                if mid in self.memories
            ]
            return sorted(memories, key=lambda x: x.importance_score, reverse=True)
        except Exception as e:
            raise MemoryStorageException(f"通过概念查找记忆失败: {str(e)}")

    def _create_concept(self, name: str) -> None:
        """创建新概念"""
        if len(self.concepts) >= self.max_concepts:
            self._cleanup_concepts()
        
        if name not in self.concepts:
            self.concepts[name] = Concept(name)

    def _update_concept_relations(self, memory: SemanticMemory) -> None:
        """更新概念关系"""
        # 更新共现关系
        for i, concept1 in enumerate(memory.concepts):
            for concept2 in memory.concepts[i+1:]:
                weight = memory.concept_weights.get(concept1, 0.5) * \
                        memory.concept_weights.get(concept2, 0.5)
                
                # 更新双向关系
                self.concepts[concept1].related_concepts[concept2] = \
                    self.concepts[concept1].related_concepts.get(concept2, 0) + weight
                
                self.concepts[concept2].related_concepts[concept1] = \
                    self.concepts[concept2].related_concepts.get(concept1, 0) + weight

    def _cleanup_concepts(self) -> None:
        """清理不重要的概念"""
        if not self.concepts:
            return

        # 计算概念重要性
        concept_importance = []
        for name, concept in self.concepts.items():
            importance = len(concept.memory_references) * 0.5 + \
                        len(concept.related_concepts) * 0.3 + \
                        concept.update_count * 0.2
            concept_importance.append((importance, name))

        # 按重要性排序
        concept_importance.sort()

        # 删除最不重要的概念
        while len(self.concepts) >= self.max_concepts:
            _, concept_name = concept_importance.pop(0)
            if concept_name in self.concepts:
                del self.concepts[concept_name]

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "total_memories": len(self.memories),
            "total_concepts": len(self.concepts),
            "max_concepts": self.max_concepts,
            "min_relation_strength": self.min_relation_strength,
            "concept_stats": {
                name: {
                    "memory_count": len(concept.memory_references),
                    "relation_count": len(concept.related_concepts),
                    "update_count": concept.update_count,
                    "last_updated": concept.last_updated.isoformat()
                }
                for name, concept in self.concepts.items()
            }
        }