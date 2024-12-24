"""
记忆快照系统的核心数据结构
实现了三层记忆结构：基础记忆、记忆快照和元快照
"""
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from uuid import uuid4
import asyncio
from utils.logger import get_logger
from .storage import MemoryStorage
from services.llm_service import LLMService

# 创建logger
snapshot_logger = get_logger('snapshot')

@dataclass
class BaseMemory:
    """基础记忆类，存储完整的对话内容和上下文"""
    id: str
    content: str
    timestamp: datetime
    context: Dict
    
    @classmethod
    def create(cls, content: str, context: Dict) -> 'BaseMemory':
        return cls(
            id=str(uuid4()),
            content=content,
            timestamp=datetime.now(),
            context=context
        )
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context
        }

@dataclass
class MemorySnapshot:
    """记忆快照类，存储记忆的核心要素"""
    id: str
    key_points: List[str]  # 核心要素列表
    memory_refs: List[str]  # 关联的基础记忆ID列表
    category: str  # 所属分类
    timestamp: datetime
    importance: float  # 重要性分数
    
    @classmethod
    def create(cls, key_points: List[str], memory_refs: List[str], category: str, importance: float) -> 'MemorySnapshot':
        return cls(
            id=str(uuid4()),
            key_points=key_points,
            memory_refs=memory_refs,
            category=category,
            timestamp=datetime.now(),
            importance=importance
        )
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'key_points': self.key_points,
            'memory_refs': self.memory_refs,
            'category': self.category,
            'timestamp': self.timestamp.isoformat(),
            'importance': self.importance
        }

@dataclass
class MetaSnapshot:
    """元快照类，对记忆快照进行更高层次的归类"""
    id: str
    category: str  # 分类名称
    keywords: List[str]  # 关键词列表
    snapshot_refs: List[str]  # 关联的快照ID列表
    description: str  # 分类描述
    timestamp: datetime
    
    @classmethod
    def create(cls, category: str, keywords: List[str], snapshot_refs: List[str], description: str) -> 'MetaSnapshot':
        return cls(
            id=str(uuid4()),
            category=category,
            keywords=keywords,
            snapshot_refs=snapshot_refs,
            description=description,
            timestamp=datetime.now()
        )
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'category': self.category,
            'keywords': self.keywords,
            'snapshot_refs': self.snapshot_refs,
            'description': self.description,
            'timestamp': self.timestamp.isoformat()
        }

class SnapshotManager:
    """快照管理器，负责快照的创建、更新和检索"""
    
    def __init__(self, storage: MemoryStorage, llm_service: LLMService):
        """
        初始化快照管理器
        
        Args:
            storage: 存储实例
            llm_service: LLM服务实例
        """
        self.storage = storage
        self.llm_service = llm_service
        self.memories: Dict[str, BaseMemory] = {}
        self.snapshots: Dict[str, MemorySnapshot] = {}
        self.meta_snapshots: Dict[str, MetaSnapshot] = {}
        snapshot_logger.info("快照管理器初始化完成")
    
    async def initialize(self):
        """初始化管理器，加载已有数据"""
        await self._load_from_storage()
    
    async def _load_from_storage(self):
        """从存储加载数据"""
        try:
            # 加载记忆
            for memory_id, memory_info in self.storage.index.get('memories', {}).items():
                memory_data = await self.storage.load_memory(memory_id)
                if memory_data:
                    self.memories[memory_id] = BaseMemory(
                        id=memory_id,
                        content=memory_data['content'],
                        timestamp=datetime.fromisoformat(memory_data['timestamp']),
                        context=memory_data['context']
                    )
            
            # 加载快照
            for snapshot_id, snapshot_info in self.storage.index.get('snapshots', {}).items():
                snapshot_data = await self.storage.load_snapshot(snapshot_id)
                if snapshot_data:
                    self.snapshots[snapshot_id] = MemorySnapshot(
                        id=snapshot_id,
                        key_points=snapshot_data['key_points'],
                        memory_refs=snapshot_data['memory_refs'],
                        category=snapshot_data['category'],
                        timestamp=datetime.fromisoformat(snapshot_data['timestamp']),
                        importance=snapshot_data['importance']
                    )
            
            # 加载元快照
            for meta_id, meta_info in self.storage.index.get('meta_snapshots', {}).items():
                meta_data = await self.storage.load_meta_snapshot(meta_id)
                if meta_data:
                    self.meta_snapshots[meta_id] = MetaSnapshot(
                        id=meta_id,
                        category=meta_data['category'],
                        keywords=meta_data['keywords'],
                        snapshot_refs=meta_data['snapshot_refs'],
                        description=meta_data['description'],
                        timestamp=datetime.fromisoformat(meta_data['timestamp'])
                    )
                    
            snapshot_logger.info(
                "数据加载完成：%d条记忆，%d个快照，%d个元快照",
                len(self.memories),
                len(self.snapshots),
                len(self.meta_snapshots)
            )
            
        except Exception as e:
            snapshot_logger.error(f"加载数据失败：{str(e)}", exc_info=True)
            raise
    
    async def add_memory(self, memory: BaseMemory) -> str:
        """添加新的基础记忆"""
        self.memories[memory.id] = memory
        if self.storage:
            await self.storage.save_memory(memory.id, memory.to_dict())
        return memory.id
    
    async def create_snapshot(self, key_points: List[str], memory_ids: List[str], 
                            category: str, importance: float) -> MemorySnapshot:
        """从基础记忆创建快照"""
        # 验证所有memory_ids都存在
        for mid in memory_ids:
            if mid not in self.memories:
                raise ValueError(f"Memory {mid} not found")
        
        snapshot = MemorySnapshot.create(key_points, memory_ids, category, importance)
        self.snapshots[snapshot.id] = snapshot
        
        if self.storage:
            await self.storage.save_snapshot(snapshot.id, snapshot.to_dict())
        
        return snapshot
    
    async def create_meta_snapshot(self, category: str, keywords: List[str], 
                                 snapshot_ids: List[str], description: str) -> MetaSnapshot:
        """创建元快照"""
        # 验证所有snapshot_ids都存在
        for sid in snapshot_ids:
            if sid not in self.snapshots:
                raise ValueError(f"Snapshot {sid} not found")
        
        meta = MetaSnapshot.create(category, keywords, snapshot_ids, description)
        self.meta_snapshots[meta.id] = meta
        
        if self.storage:
            await self.storage.save_meta_snapshot(meta.id, meta.to_dict())
        
        return meta
    
    def get_memory(self, memory_id: str) -> Optional[BaseMemory]:
        """获取基础记忆"""
        return self.memories.get(memory_id)
    
    def get_snapshot(self, snapshot_id: str) -> Optional[MemorySnapshot]:
        """获取记忆快照"""
        return self.snapshots.get(snapshot_id)
    
    def get_meta_snapshot(self, meta_id: str) -> Optional[MetaSnapshot]:
        """获取元快照"""
        return self.meta_snapshots.get(meta_id)
    
    def find_snapshots_by_category(self, category: str) -> List[MemorySnapshot]:
        """按分类查找快照"""
        return [s for s in self.snapshots.values() if s.category == category]
    
    def find_meta_snapshots_by_category(self, category: str) -> List[MetaSnapshot]:
        """按分类查找元快照"""
        return [m for m in self.meta_snapshots.values() if m.category == category]
    
    async def cleanup_old_memories(self, days: int = 30):
        """清理旧记忆"""
        if self.storage:
            await self.storage.cleanup_old_memories(days)
            # 重新加载数据
            self.memories.clear()
            self.snapshots.clear()
            self.meta_snapshots.clear()
            await self._load_from_storage() 