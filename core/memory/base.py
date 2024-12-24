"""
记忆系统的基础类和接口定义
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import json

@dataclass
class Emotion:
    """情感数据类"""
    type: str
    intensity: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "intensity": self.intensity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Emotion':
        return cls(
            type=data["type"],
            intensity=data["intensity"]
        )

@dataclass
class Memory:
    """记忆对象"""
    memory_id: str  # 记忆ID
    content: str  # 记忆内容
    timestamp: datetime  # 创建时间
    importance_score: float  # 重要性分数
    context: Dict[str, Any]  # 上下文信息
    conversation_id: Optional[str] = None  # 对话ID
    memory_type: Optional[str] = None  # 记忆类型
    emotions: List[Dict[str, Any]] = field(default_factory=list)  # 情感标签
    concepts: List[Dict[str, Any]] = field(default_factory=list)  # 概念标签

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        try:
            return {
                "memory_id": self.memory_id,
                "content": self.content,
                "timestamp": self.timestamp.isoformat(),
                "importance_score": float(self.importance_score),  # 确保是浮点数
                "context": self.context,
                "conversation_id": self.conversation_id,
                "memory_type": self.memory_type,
                "emotions": [
                    {
                        "type": str(e.get("type", "")),
                        "intensity": float(e.get("intensity", 0.0))
                    } for e in self.emotions
                ] if self.emotions else [],
                "concepts": [
                    {
                        "name": str(c.get("name", "")),
                        "type": str(c.get("type", "")),
                        "relevance": float(c.get("relevance", 0.0))
                    } for c in self.concepts
                ] if self.concepts else []
            }
        except Exception as e:
            memory_logger.error(f"记忆序列化失败: {str(e)}")
            raise MemoryException(f"记忆序列化失败: {str(e)}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """从字典创建对象"""
        try:
            # 复制数据以避免修改原始数据
            data = data.copy()
            
            # 转换时间戳
            if isinstance(data.get("timestamp"), str):
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            
            # 确保重要性分数是浮点数
            if "importance_score" in data:
                try:
                    data["importance_score"] = float(data["importance_score"])
                except (TypeError, ValueError):
                    data["importance_score"] = 0.0
            
            # 处理情感数据
            if "emotions" in data:
                try:
                    data["emotions"] = [
                        {
                            "type": str(e.get("type", "")),
                            "intensity": float(e.get("intensity", 0.0))
                        }
                        for e in data["emotions"]
                    ] if data["emotions"] else []
                except Exception:
                    data["emotions"] = []
            
            # 处理概念数据
            if "concepts" in data:
                try:
                    data["concepts"] = [
                        {
                            "name": str(c.get("name", "")),
                            "type": str(c.get("type", "")),
                            "relevance": float(c.get("relevance", 0.0))
                        }
                        for c in data["concepts"]
                    ] if data["concepts"] else []
                except Exception:
                    data["concepts"] = []
            
            # 确保context是字典
            if not isinstance(data.get("context"), dict):
                data["context"] = {}
            
            return cls(**data)
            
        except Exception as e:
            memory_logger.error(f"从字典创建记忆对象失败: {str(e)}")
            raise MemoryException(f"从字典创建记忆对象失败: {str(e)}")

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'Memory':
        return cls.from_dict(json.loads(json_str))

@dataclass
class BaseSnapshot:
    """基础快照（Level 1）- 最抽象的分类层"""
    snapshot_id: str
    category: str  # 分类名称，如"旅游"、"工作"
    keywords: List[str]  # 关键词列表
    detail_snapshot_ids: List[str]  # 关联的详细快照ID列表
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "category": self.category,
            "keywords": self.keywords,
            "detail_snapshot_ids": self.detail_snapshot_ids
        }

@dataclass
class DetailSnapshot:
    """详细快照（Level 2）- 具体记忆的核心摘要"""
    snapshot_id: str
    summary: str  # 核心摘要
    key_elements: List[str]  # 关键要素
    emotion_tags: List[str]  # 情感标签
    memory_ids: List[str]  # 关联的完整记忆ID列表
    timestamp: datetime  # 最近更新时间
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "summary": self.summary,
            "key_elements": self.key_elements,
            "emotion_tags": self.emotion_tags,
            "memory_ids": self.memory_ids,
            "timestamp": self.timestamp.isoformat()
        }

class MemoryStore(ABC):
    """记忆存储接口"""
    
    @abstractmethod
    def add(self, memory: Memory) -> bool:
        """添加记忆"""
        pass
        
    @abstractmethod
    def get(self, memory_id: str) -> Optional[Memory]:
        """获取指定记忆"""
        pass
        
    @abstractmethod
    def list(self) -> List[Memory]:
        """列出所有记忆"""
        pass
        
    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        pass
        
    @abstractmethod
    def update(self, memory: Memory) -> bool:
        """更新记忆"""
        pass
        
    @abstractmethod
    def get_base_snapshots(self) -> List[BaseSnapshot]:
        """获取所有基础快照"""
        pass
        
    @abstractmethod
    def get_detail_snapshots(self, base_snapshot_id: str) -> List[DetailSnapshot]:
        """获取指定基础快照关联的详细快照"""
        pass
        
    @abstractmethod
    def get_memories_by_ids(self, memory_ids: List[str]) -> List[Memory]:
        """根据ID列表批量获取记忆"""
        pass
        
    @abstractmethod
    def create_detail_snapshot(self, memories: List[Memory]) -> DetailSnapshot:
        """从记忆列表创建详细快照"""
        pass
        
    @abstractmethod
    def create_base_snapshot(self, detail_snapshots: List[DetailSnapshot]) -> BaseSnapshot:
        """从详细快照列表创建基础快照"""
        pass

class MemoryManager(ABC):
    """记忆管理接口"""

    @abstractmethod
    def process_memory(self, content: str, context: Dict[str, Any]) -> Memory:
        """处理新的记忆"""
        pass

    @abstractmethod
    def evaluate_importance(self, memory: Memory) -> float:
        """评估记忆重要性"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理过期或不重要的记忆"""
        pass

    @abstractmethod
    def get_relevant_memories(self, query: str, limit: int = 5) -> List[Memory]:
        """检索相关记忆"""
        pass

class MemoryException(Exception):
    """记忆系统异常基类"""
    pass

class MemoryStorageException(MemoryException):
    """存储相关异常"""
    pass

class MemoryProcessException(MemoryException):
    """处理相关异常"""
    pass

class MemoryRetrievalException(MemoryException):
    """检索相关异常"""
    pass 