"""
记忆存储模块
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from core.models.database import get_session, Memory, Snapshot, MemorySnapshot
from utils.logger import get_logger

storage_logger = get_logger('storage')

class MemoryStorage:
    """记忆存储类"""
    
    def __init__(self):
        """初始化存储"""
        self.session = get_session()
        storage_logger.info("记忆存储初始化完成")
    
    async def save_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Memory:
        """
        保存记忆
        
        Args:
            content: 记忆内容
            metadata: 元数据
            
        Returns:
            Memory: 保存的记忆对象
        """
        try:
            memory = Memory(
                content=content,
                meta_info=metadata or {}
            )
            self.session.add(memory)
            self.session.commit()
            storage_logger.info("保存记忆成功：%s", content)
            return memory
        except Exception as e:
            self.session.rollback()
            storage_logger.error("保存记忆失败：%s", str(e))
            raise
    
    async def get_memory(self, memory_id: int) -> Optional[Memory]:
        """
        获取记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            Optional[Memory]: 记忆对象，如果不存在则返回None
        """
        try:
            memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
            return memory
        except Exception as e:
            storage_logger.error("获取记忆失败：%s", str(e))
            raise
    
    async def get_all_memories(self) -> List[Memory]:
        """
        获取所有记忆
        
        Returns:
            List[Memory]: 记忆列表
        """
        try:
            memories = self.session.query(Memory).all()
            return memories
        except Exception as e:
            storage_logger.error("获取所有记忆失败：%s", str(e))
            raise
    
    async def save_snapshot(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Snapshot:
        """
        保存快照
        
        Args:
            content: 快照内容
            metadata: 元数据
            
        Returns:
            Snapshot: 保存的快照对象
        """
        try:
            snapshot = Snapshot(
                content=content,
                meta_info=metadata or {}
            )
            self.session.add(snapshot)
            self.session.commit()
            storage_logger.info("保存快照成功：%s", content)
            return snapshot
        except Exception as e:
            self.session.rollback()
            storage_logger.error("保存快照失败：%s", str(e))
            raise
    
    async def get_snapshot(self, snapshot_id: int) -> Optional[Snapshot]:
        """
        获取快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[Snapshot]: 快照对象，如果不存在则返回None
        """
        try:
            snapshot = self.session.query(Snapshot).filter(Snapshot.id == snapshot_id).first()
            return snapshot
        except Exception as e:
            storage_logger.error("获取快照失败：%s", str(e))
            raise
    
    async def get_all_snapshots(self) -> List[Snapshot]:
        """
        获取所有快照
        
        Returns:
            List[Snapshot]: 快照列表
        """
        try:
            snapshots = self.session.query(Snapshot).all()
            return snapshots
        except Exception as e:
            storage_logger.error("获取所有快照失败：%s", str(e))
            raise
    
    async def link_memory_snapshot(self, memory_id: int, snapshot_id: int, relevance_score: float = 0.0):
        """
        关联记忆和快照
        
        Args:
            memory_id: 记忆ID
            snapshot_id: 快照ID
            relevance_score: 相关度分数
        """
        try:
            link = MemorySnapshot(
                memory_id=memory_id,
                snapshot_id=snapshot_id,
                relevance_score=relevance_score
            )
            self.session.add(link)
            self.session.commit()
            storage_logger.info("关联记忆和快照成功：memory_id=%d, snapshot_id=%d", memory_id, snapshot_id)
        except Exception as e:
            self.session.rollback()
            storage_logger.error("关联记忆和快照失败：%s", str(e))
            raise
    
    async def get_memory_snapshots(self, memory_id: int) -> List[Snapshot]:
        """
        获取记忆相关的快照
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            List[Snapshot]: 快照列表
        """
        try:
            memory = await self.get_memory(memory_id)
            if memory:
                return memory.snapshots
            return []
        except Exception as e:
            storage_logger.error("获取记忆相关快照失败：%s", str(e))
            raise
    
    async def clear_all(self):
        """清空所有数据"""
        try:
            # 先删除关联表数据
            self.session.query(MemorySnapshot).delete()
            # 删除快照
            self.session.query(Snapshot).delete()
            # 删除记忆
            self.session.query(Memory).delete()
            # 提交事务
            self.session.commit()
            storage_logger.info("清空所有数据成功")
        except Exception as e:
            self.session.rollback()
            storage_logger.error("清空数据失败：%s", str(e))
            raise
    
    def __del__(self):
        """关闭数据库会话"""
        self.session.close() 