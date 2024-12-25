"""
快照管理模块
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from core.storage.memory_storage import MemoryStorage
from core.models.database import Memory, Snapshot
from services.llm_service import LLMService
from utils.logger import get_logger

snapshot_logger = get_logger('snapshot')

class SnapshotManager:
    """快照管理器"""
    
    def __init__(self, storage: MemoryStorage, llm_service: LLMService):
        """
        初始化快照管理器
        
        Args:
            storage: 存储实例
            llm_service: LLM服务实例
        """
        self.storage = storage
        self.llm_service = llm_service
        snapshot_logger.info("快照管理器初始化完成")
    
    async def create_snapshot(self, memory: Memory) -> Snapshot:
        """
        从记忆创建快照
        
        Args:
            memory: 记忆对象
            
        Returns:
            Snapshot: 创建的快照对象
        """
        try:
            # 使用LLM生成快照内容
            prompt = f"""请总结以下内容的关键信息，并返回JSON格式：
{memory.content}

请返回以下格式：
{{
    "summary": "一句话总结",
    "key_points": ["要点1", "要点2", ...]
}}"""
            result = await self.llm_service.generate_json(prompt)
            
            # 生成快照内容
            summary = result.get('summary', '')
            key_points = result.get('key_points', [])
            snapshot_content = f"{summary}\n\n关键要点：\n" + "\n".join(f"- {point}" for point in key_points)
            
            # 保存快照
            snapshot = await self.storage.save_snapshot(
                content=snapshot_content,
                metadata={
                    'summary': summary,
                    'key_points': key_points,
                    'source_memory_id': memory.id,
                    'original_content': memory.content
                }
            )
            
            # 关联记忆和快照
            await self.storage.link_memory_snapshot(memory.id, snapshot.id)
            
            snapshot_logger.info("创建快照成功：memory_id=%d, snapshot_id=%d", memory.id, snapshot.id)
            return snapshot
            
        except Exception as e:
            snapshot_logger.error("创建快照失败：%s", str(e))
            raise
    
    async def get_relevant_snapshots(self, query: str, limit: int = 5) -> List[Tuple[Snapshot, float]]:
        """
        获取与查询相关的快照
        
        Args:
            query: 查询文本
            limit: 返回结果数量限制
            
        Returns:
            List[Tuple[Snapshot, float]]: 快照和相关度分数的列表
        """
        try:
            # 获取所有快照
            snapshots = await self.storage.get_all_snapshots()
            
            if not snapshots:
                return []
            
            # 构建提示词
            contents = [f"- {s.content}" for s in snapshots]
            prompt = f"""请评估以下内容与查询"{query}"的相关度（0-1分）：
            
{chr(10).join(contents)}

请返回一个JSON对象，包含每条内容的相关度分数，格式如下：
{{
    "scores": [0.8, 0.2, 0.5, ...]
}}"""
            
            # 使用LLM评估相关度
            result = await self.llm_service.generate_json(prompt)
            scores = result.get('scores', [0] * len(snapshots))
            
            # 将快照和分数配对并排序
            snapshot_scores = list(zip(snapshots, scores))
            snapshot_scores.sort(key=lambda x: x[1], reverse=True)
            
            return snapshot_scores[:limit]
            
        except Exception as e:
            snapshot_logger.error("获取相关快照失败：%s", str(e))
            raise
    
    async def update_snapshots(self):
        """更新所有快照"""
        try:
            # 获取所有记忆
            memories = await self.storage.get_all_memories()
            
            for memory in memories:
                # 检查记忆是否已有快照
                existing_snapshots = await self.storage.get_memory_snapshots(memory.id)
                if not existing_snapshots:
                    # 为没有快照的记忆创建快照
                    await self.create_snapshot(memory)
            
            snapshot_logger.info("更新快照完成")
            
        except Exception as e:
            snapshot_logger.error("更新快照失败：%s", str(e))
            raise 