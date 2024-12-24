"""
聊天配置模块
"""
from typing import Dict, Any
from pydantic import BaseModel

class ChatConfig(BaseModel):
    """对话配置"""
    max_history_length: int = 10
    max_relevant_memories: int = 5
    memory_recency_weight: float = 0.3
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatConfig':
        return cls(
            max_history_length=data.get('max_history_length', 10),
            max_relevant_memories=data.get('max_relevant_memories', 5),
            memory_recency_weight=data.get('memory_recency_weight', 0.3)
        ) 