"""
记忆检索模块，使用向量检索实现语义搜索
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import math
import time
import asyncio
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
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 3600  # 缓存过期时间(秒)
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
            # 1. 检查缓存并生成缓存键
            cache_key = f"{query}_{top_k}_{threshold}_{hash(str(context))}"
            if cache_key in self._cache:
                cache_data = self._cache[cache_key]
                if time.time() - cache_data['timestamp'] < self.cache_ttl:
                    retriever_logger.info("命中缓存")
                    return cache_data['results']
            
            # 2. 并行执行向量检索和元快照检索
            vector_results, meta_results = await asyncio.gather(
                self.vector_store.search(
                    query=query,
                    top_k=top_k * 2,  # 扩大初始搜索范围
                    threshold=threshold * 0.8  # 降低初始阈值以获取更多候选
                ),
                self._search_meta_snapshots(query, top_k)
            )
            
            # 3. 合并结果
            combined_results = await self._merge_search_results(
                vector_results,
                meta_results,
                top_k
            )
            
            # 4. 结合上下文重新排序
            if context:
                combined_results = await self._rerank_with_context(
                    combined_results,
                    context
                )
            
            # 5. 过滤并限制结果数量
            final_results = [
                (memory, score) 
                for memory, score in combined_results
                if score >= threshold
            ][:top_k]
            
            # 6. 更新缓存
            self._cache[cache_key] = {
                'results': final_results,
                'timestamp': time.time()
            }
            
            # 7. 异步清理过期缓存
            asyncio.create_task(self._cleanup_cache())
            
            return final_results
            
        except Exception as e:
            retriever_logger.error(f"搜索记忆失败: {str(e)}")
            return []

    async def _search_meta_snapshots(
        self,
        query: str,
        top_k: int
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        搜索元快照
        """
        try:
            # 获取所有元快照
            meta_snapshots = await self.vector_store.search_meta_snapshots(
                query=query,
                top_k=top_k
            )
            
            # 从元快照获取相关记忆
            results = []
            for meta_snapshot, meta_score in meta_snapshots:
                # 获取关联的记忆快照
                memory_ids = meta_snapshot.get('memory_ids', [])
                for memory_id in memory_ids:
                    memory = await self.vector_store.get_memory(memory_id)
                    if memory:
                        # 继承元快照的相似度分数
                        results.append((memory, meta_score * 0.9))
            
            return results
            
        except Exception as e:
            retriever_logger.error(f"搜索元快照失败: {str(e)}")
            return []

    async def _merge_search_results(
        self,
        vector_results: List[Tuple[Dict[str, Any], float]],
        meta_results: List[Tuple[Dict[str, Any], float]],
        top_k: int
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        合并向量检索和元快照检索的结果
        """
        try:
            # 创建记忆ID到最高分数的映射
            memory_scores: Dict[str, float] = {}
            
            # 处理向量检索结果
            for memory, score in vector_results:
                memory_id = memory.get('id')
                if memory_id:
                    memory_scores[memory_id] = score
            
            # 处理元快照结果，取较高的分数
            for memory, score in meta_results:
                memory_id = memory.get('id')
                if memory_id:
                    current_score = memory_scores.get(memory_id, 0)
                    memory_scores[memory_id] = max(current_score, score)
            
            # 构建最终结果
            results = []
            seen_memories = set()
            
            # 首先添加高分结果
            for memory_id, score in sorted(
                memory_scores.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                if len(results) >= top_k:
                    break
                    
                if memory_id not in seen_memories:
                    memory = await self.vector_store.get_memory(memory_id)
                    if memory:
                        results.append((memory, score))
                        seen_memories.add(memory_id)
            
            return results
            
        except Exception as e:
            retriever_logger.error(f"合并搜索结果失败: {str(e)}")
            return []

    async def _rerank_with_context(
        self,
        results: List[Tuple[Dict[str, Any], float]],
        context: Dict[str, Any]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        优化的上下文重排序
        """
        try:
            reranked_results = []
            current_time = datetime.now()
            
            for memory, score in results:
                # 基础分数
                final_score = score
                
                # 1. 时间衰减
                if 'timestamp' in memory:
                    memory_time = datetime.fromisoformat(memory['timestamp'])
                    time_diff = (current_time - memory_time).total_seconds()
                    # 使用对数衰减而不是线性衰减
                    time_factor = 1.0 / (1.0 + math.log1p(time_diff / (24 * 3600)))
                    final_score *= time_factor
                
                # 2. 用户相关性
                if 'user_id' in context:
                    user_id = context['user_id']
                    if memory.get('metadata', {}).get('user_id') == user_id:
                        final_score *= 1.2
                
                # 3. 会话相关性
                if 'session_id' in context:
                    session_id = context['session_id']
                    if memory.get('metadata', {}).get('session_id') == session_id:
                        final_score *= 1.1
                
                # 4. 主题相关性
                if 'topic' in context and 'topic' in memory.get('metadata', {}):
                    if context['topic'] == memory['metadata']['topic']:
                        final_score *= 1.15
                
                # 5. API调用相关性
                if context.get('enable_api_call'):
                    if memory.get('metadata', {}).get('has_api_call'):
                        final_score *= 1.1
                
                reranked_results.append((memory, final_score))
            
            # 重新排序
            reranked_results.sort(key=lambda x: x[1], reverse=True)
            return reranked_results
            
        except Exception as e:
            retriever_logger.error(f"重排序失败: {str(e)}")
            return results

    async def _cleanup_cache(self):
        """
        清理过期缓存
        """
        try:
            current_time = time.time()
            expired_keys = [
                key for key in self._cache
                if current_time - self._cache[key]['timestamp'] > self.cache_ttl
            ]
            for key in expired_keys:
                del self._cache[key]
        except Exception as e:
            retriever_logger.error(f"清理缓存失败: {str(e)}")
    
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