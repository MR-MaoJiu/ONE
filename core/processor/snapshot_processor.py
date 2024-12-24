"""
快照处理器模块
"""
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
from utils.logger import get_logger

from services.llm_service import LLMService
from ..memory.snapshot import SnapshotManager, BaseMemory
from ..memory.snapshot_generator import SnapshotGenerator

# 创建logger
snapshot_processor_logger = get_logger('snapshot_processor')

class SnapshotProcessor:
    """快照处理器"""
    
    def __init__(self, snapshot_manager: SnapshotManager, config: Dict[str, Any]):
        """
        初始化快照处理器
        
        Args:
            snapshot_manager: 快照管理器
            config: 配置信息
        """
        self.snapshot_manager = snapshot_manager
        self.config = config
        self.generator = SnapshotGenerator(self.snapshot_manager.llm_service)
        snapshot_processor_logger.info("快照处理器初始化完成")
        
    async def process_memory(self, content: Dict[str, Any]) -> str:
        """
        处理记忆内容，生成快照
        
        Args:
            content: 记忆内容，包含content、context和timestamp字段
            
        Returns:
            str: 记忆ID
        """
        try:
            # 生成记忆ID
            memory_id = f"memory_{uuid.uuid4().hex}"
            
            # 创建记忆对象
            memory = BaseMemory(
                id=memory_id,
                content=content.get('content', ''),
                timestamp=datetime.fromisoformat(content.get('timestamp', datetime.now().isoformat())),
                context=content.get('context', {})
            )
            
            # 保存记忆
            await self.snapshot_manager.add_memory(memory)
            
            # 生成详细快照
            detail_snapshot = await self.generator.generate_detail_snapshot(
                [memory],
                f"detail_{uuid.uuid4().hex}"
            )
            
            # 保存详细快照
            if detail_snapshot:
                await self.snapshot_manager.create_snapshot(
                    key_points=detail_snapshot.key_points,
                    memory_ids=[memory.id],
                    category=detail_snapshot.category,
                    importance=detail_snapshot.importance
                )
            
            return memory_id
            
        except Exception as e:
            snapshot_processor_logger.error(f"处理记忆失败：{str(e)}", exc_info=True)
            raise
            
    async def get_relevant_memories(self, context: Dict[str, Any]) -> List[Tuple[BaseMemory, float]]:
        """
        获取与当前上下文相关的记忆
        
        Args:
            context: 当前上下文，包含 current_query 和 history 字段
            
        Returns:
            List[Tuple[BaseMemory, float]]: 记忆和相关度分数的列表
        """
        try:
            # 获取当前查询
            query = context.get('current_query', '')
            if not query:
                return []
            
            # 获取所有记忆
            memories = list(self.snapshot_manager.memories.values())
            if not memories:
                return []
            
            # 为每个记忆准备简化的数据
            memory_data = []
            for memory in memories:
                # 只包含必要的字段
                memory_data.append({
                    'id': memory.id,
                    'content': memory.content,
                    'timestamp': memory.timestamp.isoformat()
                })
            
            # 构建提示词
            prompt = f"""
            请根据以下记忆和当前查询，评估它们的相关度。
            
            当前查询：{query}
            
            记忆列表：
            {json.dumps(memory_data, ensure_ascii=False, indent=2)}
            
            请评估每条记忆与当前查询的相关程度，考虑以下因素：
            1. 内容相关性：记忆内容是否与查询主题相关
            2. 时间相关性：记忆的时间是否与查询相关
            3. 上下文匹配：记忆的上下文是否与当前查询场景匹配
            
            请返回以下格式的JSON：
            {{
                "relevant_memories": [
                    {{
                        "memory_id": "记忆ID",
                        "relevance_score": 0.8,
                        "reason": "相关原因说明"
                    }}
                ]
            }}
            
            注意：
            1. relevance_score 必须是 0-1 之间的浮点数
            2. 只返回相关度大于 0.5 的记忆
            3. 按相关度从高到低排序
            """
            
            # 调用LLM评估相关度
            result = await self.generator.llm_service.generate_json(prompt)
            
            if not result or 'relevant_memories' not in result:
                return []
            
            # 获取相关记忆
            relevant_memories = []
            for memory_result in result['relevant_memories']:
                memory_id = memory_result.get('memory_id')
                if not memory_id:
                    continue
                    
                memory = self.snapshot_manager.get_memory(memory_id)
                if not memory:
                    continue
                    
                try:
                    score = float(memory_result.get('relevance_score', 0))
                    if score >= 0.5:  # 只保留相关度大于 0.5 的记忆
                        relevant_memories.append((memory, score))
                except (TypeError, ValueError):
                    continue
            
            # 按相关度排序
            relevant_memories.sort(key=lambda x: x[1], reverse=True)
            return relevant_memories
            
        except Exception as e:
            snapshot_processor_logger.error(f"获取相关记忆失败：{str(e)}")
            return []

    async def get_all_memories(self) -> List[Dict[str, Any]]:
        """获取所有记忆"""
        try:
            memories = []
            for memory in self.snapshot_manager.memories.values():
                memories.append({
                    'id': memory.id,
                    'content': memory.content,
                    'timestamp': memory.timestamp.isoformat(),
                    'context': memory.context
                })
            return memories
        except Exception as e:
            snapshot_processor_logger.error(f"获取所有记忆失败：{str(e)}")
            return []

    async def get_all_snapshots(self) -> List[Dict[str, Any]]:
        """获取所有快照"""
        try:
            snapshots = []
            for snapshot in self.snapshot_manager.snapshots.values():
                snapshots.append({
                    'id': snapshot.id,
                    'key_points': snapshot.key_points,
                    'category': snapshot.category,
                    'importance': snapshot.importance
                })
            return snapshots
        except Exception as e:
            snapshot_processor_logger.error(f"获取所有快照失败：{str(e)}")
            return []

    async def update_snapshots(self) -> None:
        """更新所有快照"""
        try:
            # 获取所有记忆
            memories = list(self.snapshot_manager.memories.values())
            if not memories:
                return

            # 生成新的快照
            snapshot_id = f"detail_{uuid.uuid4().hex}"
            detail_snapshot = await self.generator.generate_detail_snapshot(
                memories,
                snapshot_id
            )
            
            # 保存新快照
            if detail_snapshot:
                await self.snapshot_manager.create_snapshot(
                    key_points=detail_snapshot.key_points,
                    memory_ids=[m.id for m in memories],
                    category=detail_snapshot.category,
                    importance=detail_snapshot.importance
                )
        except Exception as e:
            snapshot_processor_logger.error(f"更新快照失败：{str(e)}")
            raise 