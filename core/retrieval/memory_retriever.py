"""
记忆检索模块，使用向量检索实现语义搜索
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils.logger import get_logger
from core.retrieval.vector_store import VectorStore

retriever_logger = get_logger('memory_retriever')

class MemoryRetriever:
    """记忆检索类，使用向量检索进行语义搜索"""
    
    def __init__(self, vector_store: VectorStore):
        """
        初始化检索器
        
        Args:
            vector_store: 向量存储实例
        """
        self.vector_store = vector_store
        self._cache: Dict[str, List[Tuple[Dict[str, Any], float]]] = {}
        retriever_logger.info("记忆检索器初始化完成")
    
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
            context: 上下文信息
            
        Returns:
            List[Tuple[Dict[str, Any], float]]: 记忆和相似度得分的列表
        """
        try:
            # 检查缓存
            cache_key = f"{query}_{top_k}_{threshold}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # 使用向量检索
            results = await self.vector_store.search(
                query=query,
                top_k=top_k,
                threshold=threshold
            )
            
            # 结合上下文重排序
            if context:
                results = await self._rerank_with_context(results, context)
            
            # 更新缓存
            self._cache[cache_key] = results
            
            return results
            
        except Exception as e:
            retriever_logger.error(f"搜索记忆失败: {str(e)}")
            return []
    
    async def _rerank_with_context(
        self,
        results: List[Tuple[Dict[str, Any], float]],
        context: Dict[str, Any]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        基于上下文重新排序
        
        Args:
            results: 原始检索结果
            context: 上下文信息
            
        Returns:
            List[Tuple[Dict[str, Any], float]]: 重排序后的结果
        """
        try:
            reranked_results = []
            
            for memory, score in results:
                # 时间衰减
                if 'current_time' in context and 'timestamp' in memory:
                    current_time = context['current_time']
                    memory_time = datetime.fromisoformat(memory['timestamp'])
                    time_diff = (current_time - memory_time).total_seconds()
                    decay = 1.0 / (1.0 + time_diff / (24 * 3600))  # 24小时衰减一半
                    score *= decay
                
                # 用户相关性
                if 'user_id' in context:
                    user_id = context['user_id']
                    if memory.get('metadata', {}).get('user_id') == user_id:
                        score *= 1.2  # 提升用户相关内容的权重
                
                reranked_results.append((memory, score))
            
            # 重新排序
            reranked_results.sort(key=lambda x: x[1], reverse=True)
            return reranked_results
            
        except Exception as e:
            retriever_logger.error(f"重排序失败: {str(e)}")
            return results
    
    async def add_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加新记忆
        
        Args:
            memory_id: 记忆ID
            content: 记忆内容
            metadata: 记忆元数据
        """
        try:
            # 清除相关缓存
            self._cache.clear()
            
            # 添加到向量存储
            await self.vector_store.add_memory(
                memory_id=memory_id,
                content=content,
                metadata=metadata
            )
            
        except Exception as e:
            retriever_logger.error(f"添加记忆失败: {str(e)}")
            raise 