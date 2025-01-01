"""
快照管理器实现
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import json

from .base import Memory, BaseSnapshot, DetailSnapshot, MemoryStore
from .snapshot_generator import SnapshotGenerator
from services.llm_service import LLMService
from utils.logger import memory_logger

class SnapshotManager:
    """快照管理器"""
    
    def __init__(
        self,
        memory_store: MemoryStore,
        llm_service: LLMService,
        update_interval: timedelta = timedelta(hours=1),
        cache_ttl: int = 3600  # 缓存过期时间(秒)
    ):
        self.memory_store = memory_store
        self.llm_service = llm_service
        self.update_interval = update_interval
        self.cache_ttl = cache_ttl
        self.last_update = datetime.min
        
        # 初始化生成器
        self.generator = SnapshotGenerator(llm_service)
        
        # 初始化统计信息
        self.stats = {
            "total_snapshots": 0,
            "base_snapshots": 0,
            "detail_snapshots": 0,
            "last_optimization": None,
            "optimization_count": 0
        }
        
        # 更新锁
        self._update_lock = asyncio.Lock()
        
        memory_logger.info("快照管理器初始化完成")
    
    @lru_cache(maxsize=1000)
    def get_base_snapshots(self) -> List[BaseSnapshot]:
        """获取基础快照(带缓存)"""
        return self.memory_store.get_base_snapshots()
    
    @lru_cache(maxsize=1000)
    def get_detail_snapshots(self, base_id: str) -> List[DetailSnapshot]:
        """获取详细快照(带缓存)"""
        return self.memory_store.get_detail_snapshots(base_id)
    
    async def update_snapshots(self) -> None:
        """异步更新快照"""
        try:
            # 检查更新间隔
            now = datetime.now()
            if now - self.last_update < self.update_interval:
                return
            
            # 获取更新锁
            async with self._update_lock:
                memory_logger.info("开始更新快照")
                
                # 获取所有记忆
                memories = self.memory_store.list()
                if not memories:
                    return
                
                # 按时间分组
                time_groups = self._group_by_time(memories)
                
                # 异步更新详细快照
                detail_tasks = []
                for group in time_groups:
                    task = asyncio.create_task(
                        self._create_or_update_detail_snapshot(group)
                    )
                    detail_tasks.append(task)
                
                detail_snapshots = []
                for task in asyncio.as_completed(detail_tasks):
                    snapshot = await task
                    if snapshot:
                        detail_snapshots.append(snapshot)
                
                # 更新基础快照
                if detail_snapshots:
                    await self._create_or_update_base_snapshots(detail_snapshots)
                
                # 执行优化
                await self._optimize_snapshots()
                
                # 更新统计信息
                self._update_stats()
                
                self.last_update = now
                memory_logger.info("快照更新完成")
        
        except Exception as e:
            memory_logger.error(f"更新快照失败: {str(e)}")
    
    def _group_by_time(self, memories: List[Memory]) -> List[List[Memory]]:
        """按时间将记忆分组"""
        # 按天分组
        groups: Dict[str, List[Memory]] = {}
        for memory in memories:
            day = memory.timestamp.strftime("%Y-%m-%d")
            if day not in groups:
                groups[day] = []
            groups[day].append(memory)
        
        return list(groups.values())
    
    async def _create_or_update_detail_snapshot(
        self,
        memories: List[Memory]
    ) -> Optional[DetailSnapshot]:
        """异步创建或更新详细快照"""
        try:
            # 检查是否已有快照
            existing_snapshots = []
            for memory in memories:
                snapshots = self.memory_store.get_detail_snapshots(memory.memory_id)
                existing_snapshots.extend(snapshots)
            
            # 如果已有快照且未过期,直接返回
            if existing_snapshots:
                latest = max(existing_snapshots, key=lambda x: x.timestamp)
                if datetime.now() - latest.timestamp < self.update_interval:
                    return latest
            
            # 生成快照ID
            snapshot_id = f"detail_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 使用生成器创建新快照
            snapshot = await asyncio.to_thread(
                self.generator.generate_detail_snapshot,
                memories,
                snapshot_id
            )
            
            # 保存快照
            self.memory_store.create_detail_snapshot(snapshot)
            
            # 清除缓存
            self.get_detail_snapshots.cache_clear()
            
            return snapshot
            
        except Exception as e:
            memory_logger.error(f"创建/更新详细快照失败: {str(e)}")
            return None
    
    async def _create_or_update_base_snapshots(
        self,
        detail_snapshots: List[DetailSnapshot]
    ) -> None:
        """异步创建或更新基础快照"""
        try:
            # 获取现有基础快照
            existing_snapshots = self.memory_store.get_base_snapshots()
            
            # 按主题聚类详细快照
            clusters = await self._cluster_by_topic(detail_snapshots)
            
            # 更新每个主题的基础快照
            for cluster in clusters:
                # 检查是否已有对应的基础快照
                existing = None
                if existing_snapshots:
                    for snapshot in existing_snapshots:
                        if set(snapshot.detail_snapshot_ids) == set(s.snapshot_id for s in cluster):
                            existing = snapshot
                            break
                
                # 如果没有或需要更新,则创建新的基础快照
                if not existing:
                    snapshot_id = f"base_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    snapshot = await asyncio.to_thread(
                        self.generator.generate_base_snapshot,
                        cluster,
                        snapshot_id
                    )
                    self.memory_store.create_base_snapshot(snapshot)
            
            # 清除缓存
            self.get_base_snapshots.cache_clear()
            
        except Exception as e:
            memory_logger.error(f"创建/更新基础快照失败: {str(e)}")
    
    async def _cluster_by_topic(
        self,
        snapshots: List[DetailSnapshot]
    ) -> List[List[DetailSnapshot]]:
        """使用向量相似度进行主题聚类"""
        try:
            if not snapshots:
                return []
                
            # 获取所有快照的向量表示
            vectors = []
            for snapshot in snapshots:
                # 使用快照的摘要和关键元素生成向量
                text = f"{snapshot.summary}\n{' '.join(snapshot.key_elements)}"
                vector = await self.vector_store.get_embedding(text)
                vectors.append(vector)
            
            # 使用层次聚类
            clusters = []
            used = set()
            
            for i, snapshot in enumerate(snapshots):
                if i in used:
                    continue
                    
                cluster = [snapshot]
                used.add(i)
                
                # 找到相似的快照
                for j, other in enumerate(snapshots):
                    if j in used or j == i:
                        continue
                        
                    # 计算余弦相似度
                    similarity = self.vector_store.compute_similarity(
                        vectors[i],
                        vectors[j]
                    )
                    
                    # 如果相似度超过阈值，加入同一个簇
                    if similarity > 0.8:  # 可调整的阈值
                        cluster.append(other)
                        used.add(j)
                
                clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            memory_logger.error(f"聚类失败: {str(e)}")
            # 如果聚类失败，将每个快照作为单独的簇
            return [[s] for s in snapshots]
    
    async def _optimize_snapshots(self) -> None:
        """优化快照"""
        try:
            # 获取所有详细快照
            detail_snapshots = []
            for base in self.memory_store.get_base_snapshots():
                snapshots = self.memory_store.get_detail_snapshots(base.snapshot_id)
                detail_snapshots.extend(snapshots)
            
            # 对每个快照进行优化
            for snapshot in detail_snapshots:
                # 获取关联记忆
                memories = self.memory_store.get_memories_by_ids(snapshot.memory_ids)
                
                # 生成优化建议
                optimization = await asyncio.to_thread(
                    self.generator.optimize_snapshot,
                    snapshot,
                    memories
                )
                
                # TODO: 根据优化建议执行具体的优化操作
                memory_logger.info(f"快照优化建议: {optimization}")
            
            # 更新统计信息
            self.stats["last_optimization"] = datetime.now()
            self.stats["optimization_count"] += 1
            
        except Exception as e:
            memory_logger.error(f"优化快照失败: {str(e)}")
    
    def _update_stats(self):
        """更新统计信息"""
        try:
            base_snapshots = self.memory_store.get_base_snapshots()
            detail_snapshots = []
            for base in base_snapshots:
                snapshots = self.memory_store.get_detail_snapshots(base.snapshot_id)
                detail_snapshots.extend(snapshots)
            
            self.stats.update({
                "total_snapshots": len(base_snapshots) + len(detail_snapshots),
                "base_snapshots": len(base_snapshots),
                "detail_snapshots": len(detail_snapshots)
            })
            
        except Exception as e:
            memory_logger.error(f"更新统计信息失败: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy() 