"""
批量处理模块，用于高效处理大量记忆的向量化
"""
import asyncio
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from core.retrieval.vector_store import VectorStore
from utils.logger import get_logger

batch_logger = get_logger('batch_processor')

class BatchProcessor:
    """批量处理器，用于高效处理大量记忆的向量化"""
    
    def __init__(self, vector_store: VectorStore, batch_size: int = 32):
        """
        初始化批量处理器
        
        Args:
            vector_store: 向量存储实例
            batch_size: 批处理大小
        """
        self.vector_store = vector_store
        self.batch_size = batch_size
        batch_logger.info(f"批量处理器初始化完成，批大小: {batch_size}")
    
    async def process_memories(
        self,
        memories: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> None:
        """
        批量处理记忆
        
        Args:
            memories: 记忆列表，每个记忆包含 id、content 和 metadata
            show_progress: 是否显示进度条
        """
        try:
            total_batches = (len(memories) + self.batch_size - 1) // self.batch_size
            
            with tqdm(total=len(memories), disable=not show_progress) as pbar:
                for i in range(0, len(memories), self.batch_size):
                    batch = memories[i:i + self.batch_size]
                    
                    # 并行处理批次中的记忆
                    tasks = []
                    for memory in batch:
                        task = self.vector_store.add_memory(
                            memory_id=memory['id'],
                            content=memory['content'],
                            metadata=memory.get('metadata')
                        )
                        tasks.append(task)
                    
                    # 等待批次完成
                    await asyncio.gather(*tasks)
                    
                    # 更新进度条
                    pbar.update(len(batch))
            
            batch_logger.info(f"批量处理完成，共处理 {len(memories)} 条记忆")
            
        except Exception as e:
            batch_logger.error(f"批量处理失败: {str(e)}")
            raise
    
    async def optimize_index(self) -> None:
        """优化向量索引"""
        try:
            # 获取当前索引中的所有向量
            vectors = self.vector_store.get_all_vectors()
            
            if not vectors:
                batch_logger.info("索引为空，无需优化")
                return
            
            # 重建优化的索引
            self.vector_store.rebuild_index(vectors)
            batch_logger.info("索引优化完成")
            
        except Exception as e:
            batch_logger.error(f"索引优化失败: {str(e)}")
            raise 