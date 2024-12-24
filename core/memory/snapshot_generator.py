"""
智能快照生成器
"""
import json
from typing import List, Dict, Any
from datetime import datetime

from .snapshot import BaseMemory, MemorySnapshot, MetaSnapshot
from services.llm_service import LLMService
from utils.logger import get_logger

# 创建logger
generator_logger = get_logger('generator')

class SnapshotGenerator:
    """智能快照生成器"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    async def generate_detail_snapshot(
        self,
        memories: List[BaseMemory],
        snapshot_id: str
    ) -> MemorySnapshot:
        """生成详细快照"""
        try:
            # 准备记忆数据
            memory_data = [m.to_dict() for m in memories]
            
            # 构建提示词
            prompt = f"""
            请根据以下记忆生成一个详细快照:
            {json.dumps(memory_data, ensure_ascii=False)}
            
            请返回以下格式的JSON:
            {{
                "key_points": ["关键要素1", "关键要素2"],
                "category": "分类名称",
                "importance": 0.8
            }}
            """
            
            # 调用LLM生成快照
            result = await self.llm_service.generate_json(prompt)
            
            if not result:
                raise Exception("生成快照失败")
            
            # 创建快照对象
            snapshot = MemorySnapshot.create(
                key_points=result.get("key_points", []),
                memory_refs=[m.id for m in memories],
                category=result.get("category", "未分类"),
                importance=result.get("importance", 0.5)
            )
            
            return snapshot
            
        except Exception as e:
            generator_logger.error(f"生成详细快照失败: {str(e)}")
            raise
    
    async def generate_meta_snapshot(
        self,
        snapshots: List[MemorySnapshot],
        meta_id: str
    ) -> MetaSnapshot:
        """生成元快照"""
        try:
            # 准备快照数据
            snapshot_data = [s.to_dict() for s in snapshots]
            
            # 构建提示词
            prompt = f"""
            请根据以下快照生成一个元快照:
            {json.dumps(snapshot_data, ensure_ascii=False)}
            
            请返回以下格式的JSON:
            {{
                "category": "分类名称",
                "keywords": ["关键词1", "关键词2"],
                "description": "分类描述"
            }}
            """
            
            # 调用LLM生成快照
            result = await self.llm_service.generate_json(prompt)
            
            if not result:
                raise Exception("生成快照失败")
            
            # 创建快照对象
            snapshot = MetaSnapshot.create(
                category=result.get("category", "未分类"),
                keywords=result.get("keywords", []),
                snapshot_refs=[s.id for s in snapshots],
                description=result.get("description", "")
            )
            
            return snapshot
            
        except Exception as e:
            generator_logger.error(f"生成元快照失败: {str(e)}")
            raise 