"""
基于向量存储的记忆检索模块
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from core.retrieval.vector_store import VectorStore
from utils.logger import get_logger

retrieval_logger = get_logger('memory_retrieval')

class MemoryRetriever:
    """记忆检索器，使用向量存储实现语义搜索"""
    
    def __init__(self, vector_store: VectorStore):
        """
        初始化记忆检索器
        
        Args:
            vector_store: 向量存储实例
        """
        self.vector_store = vector_store
        retrieval_logger.info("记忆检索器初始化完成")
    
    async def search_memories(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.6,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        搜索相关记忆
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            threshold: 相似度阈值
            context: 上下文信息（可选）
            
        Returns:
            List[Tuple[Dict[str, Any], float]]: 记忆和相似度得分的列表
        """
        try:
            # 使用向量存储搜索相关记忆
            results = await self.vector_store.search(
                query=query,
                top_k=top_k * 2,  # 获取更多候选结果用于重排序
                threshold=threshold
            )
            
            # 如果有上下文信息，进行重排序
            if context and results:
                results = self._rerank_with_context(results, context)
                # 只保留前 top_k 个结果
                results = results[:top_k]
            
            retrieval_logger.info(f"记忆检索完成，找到 {len(results)} 条相关记忆")
            return results
            
        except Exception as e:
            retrieval_logger.error(f"记忆检索失败: {str(e)}")
            raise
    
    def _rerank_with_context(
        self,
        results: List[Tuple[Dict[str, Any], float]],
        context: Dict[str, Any]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        使用上下文信息重排序搜索结果
        
        Args:
            results: 原始搜索结果
            context: 上下文信息
            
        Returns:
            List[Tuple[Dict[str, Any], float]]: 重排序后的结果
        """
        try:
            # 提取重要的上下文信息
            current_time = datetime.now()
            user_id = context.get('user_id')
            conversation_id = context.get('conversation_id')
            
            # 计算每个结果的综合得分
            scored_results = []
            for memory, similarity in results:
                # 基础分数就是相似度得分
                score = similarity
                
                # 时间衰减因子：越新的记忆得分越高
                if 'timestamp' in memory:
                    memory_time = datetime.fromisoformat(memory['timestamp'])
                    time_diff = (current_time - memory_time).total_seconds() / 3600  # 转换为小时
                    time_factor = 1 / (1 + np.log1p(time_diff))  # 使用对数衰减
                    score *= (0.8 + 0.2 * time_factor)  # 时间因素占20%权重
                
                # 用户相关性：同一用户的记忆得分更高
                if user_id and memory.get('metadata', {}).get('user_id') == user_id:
                    score *= 1.2  # 提升20%
                
                # 对话相关性：同一对话的记忆得分更高
                if conversation_id and memory.get('metadata', {}).get('conversation_id') == conversation_id:
                    score *= 1.3  # 提升30%
                
                # 记忆类型权重：根据不同类型的记忆赋予不同权重
                memory_type = memory.get('metadata', {}).get('type', 'general')
                type_weights = {
                    'important': 1.5,  # 重要记忆
                    'concept': 1.3,    # 概念解释
                    'example': 1.2,    # 示例
                    'general': 1.0     # 一般记忆
                }
                score *= type_weights.get(memory_type, 1.0)
                
                scored_results.append((memory, score))
            
            # 按综合得分排序
            scored_results.sort(key=lambda x: x[1], reverse=True)
            
            retrieval_logger.info("记忆重排序完成")
            return scored_results
            
        except Exception as e:
            retrieval_logger.error(f"记忆重排序失败: {str(e)}")
            return results  # 如果重排序失败，返回原始结果
    
    async def add_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加记忆到检索系统
        
        Args:
            memory_id: 记忆ID
            content: 记忆内容
            metadata: 记忆元数据
        """
        try:
            await self.vector_store.add_memory(
                memory_id=memory_id,
                content=content,
                metadata=metadata
            )
            retrieval_logger.info(f"记忆已添加到检索系统: {memory_id}")
            
        except Exception as e:
            retrieval_logger.error(f"添加记忆失败: {str(e)}")
            raise
    
    async def save_state(self, path: str) -> None:
        """
        保存检索系统状态
        
        Args:
            path: 保存路径
        """
        try:
            await self.vector_store.save(path)
            retrieval_logger.info(f"检索系统状态已保存到: {path}")
            
        except Exception as e:
            retrieval_logger.error(f"保存状态失败: {str(e)}")
            raise
    
    async def load_state(self, path: str) -> None:
        """
        加载检索系统状态
        
        Args:
            path: 加载路径
        """
        try:
            await self.vector_store.load(path)
            retrieval_logger.info(f"检索系统状态已加载")
            
        except Exception as e:
            retrieval_logger.error(f"加载状态失败: {str(e)}")
            raise
    
    async def clear(self) -> None:
        """清空检索系统"""
        try:
            await self.vector_store.clear()
            retrieval_logger.info("检索系统已清空")
            
        except Exception as e:
            retrieval_logger.error(f"清空系统失败: {str(e)}")
            raise 