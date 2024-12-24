"""
记忆系统配置模块
"""
from typing import Dict, Any, Optional
from pathlib import Path
import json
from pydantic import BaseModel

class StorageConfig(BaseModel):
    """存储配置"""
    storage_dir: str = "data/memories"
    index_file: str = "index.json"

class SnapshotConfig(BaseModel):
    """快照配置"""
    min_importance: float = 0.5
    max_key_points: int = 5
    max_snapshots_per_category: int = 10
    cleanup_days: int = 30

class ChatConfig(BaseModel):
    """对话配置"""
    max_history_length: int = 10
    max_relevant_memories: int = 5
    memory_recency_weight: float = 0.3

class MemoryConfig(BaseModel):
    """记忆系统配置"""
    storage: StorageConfig
    snapshot: SnapshotConfig
    chat: ChatConfig

    @classmethod
    def from_file(cls, config_path: str) -> 'MemoryConfig':
        """从文件加载配置"""
        config_path = Path(config_path)
        if not config_path.exists():
            config_path = config_path.parent / 'default_memory_config.json'
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            
        return cls(**config_data) 