"""
记忆管理器模块
"""
import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from core.retrieval.vector_store import VectorStore
from core.retrieval.memory_retriever import MemoryRetriever
from core.retrieval.batch_processor import BatchProcessor
from utils.logger import get_logger

memory_logger = get_logger('memory_manager')

class MemoryManager:
    """记忆管理器，负责记忆的存储、检索和维护"""
    
    def __init__(self, storage_path: str = "data/memories"):
        """
        初始化记忆管理器
        
        Args:
            storage_path: 存储路径
        """
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        # 初始化向量存储
        self.vector_store = VectorStore()
        
        # 初始化记忆检索器
        self.retriever = MemoryRetriever(self.vector_store)
        
        # 初始化批量处理器
        self.batch_processor = BatchProcessor(self.vector_store)
        
        # API 调用结果缓存
        self._api_results: Dict[str, Any] = {}
        
        memory_logger.info("记忆管理器初始化完成")
        
        # 优化任务
        self._optimization_task = None
    
    async def initialize(self):
        """异步初始化"""
        # 加载已有记忆
        await self._load_existing_memories()
        
        # 启动定期优化任务
        await self._start_optimization_task()
    
    async def _load_existing_memories(self):
        """加载已有的记忆数据"""
        try:
            vector_path = os.path.join(self.storage_path, 'vectors')
            if os.path.exists(vector_path):
                await self.retriever.load_state(vector_path)
                memory_logger.info("已加载现有记忆")
        except Exception as e:
            memory_logger.error(f"加载记忆失败: {str(e)}")
    
    async def _start_optimization_task(self):
        """启动定期优化任务"""
        async def optimize_periodically():
            while True:
                try:
                    # 每天优化一次索引
                    await asyncio.sleep(24 * 3600)
                    await self.optimize_index()
                except Exception as e:
                    memory_logger.error(f"定期优化失败: {str(e)}")
                    await asyncio.sleep(60)  # 发生错误时等待1分钟后重试
        
        # 在后台运行优化任务
        self._optimization_task = asyncio.create_task(optimize_periodically())
    
    async def cleanup(self):
        """清理资源"""
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
    
    async def set_api_result(self, memory_id: str, result: Any) -> None:
        """
        设置 API 调用结果
        
        Args:
            memory_id: 记忆ID
            result: API 调用结果
        """
        self._api_results[memory_id] = result
    
    async def get_api_result(self, memory_id: str, timeout: float = 10.0) -> Optional[Any]:
        """
        获取 API 调用结果，如果结果未就绪则等待
        
        Args:
            memory_id: 记忆ID
            timeout: 超时时间（秒）
            
        Returns:
            Optional[Any]: API 调用结果，如果超时则返回 None
        """
        start_time = datetime.now()
        while True:
            if memory_id in self._api_results:
                result = self._api_results.pop(memory_id)
                return result
            
            if (datetime.now() - start_time).total_seconds() > timeout:
                return None
                
            await asyncio.sleep(0.1)
    
    async def get_complete_content(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0
    ) -> str:
        """
        获取完整的内容，包括 API 调用结果
        
        Args:
            memory_id: 记忆ID
            content: 原始内容
            metadata: 记忆元数据
            timeout: 等待 API 结果的超时时间
            
        Returns:
            str: 完整内容
        """
        try:
            # 如果启用了 API 调用，等待结果
            if metadata and metadata.get('api_enabled'):
                api_result = await self.get_api_result(memory_id, timeout)
                if api_result:
                    return f"{content}\n\nAPI调用结果：{api_result}"
            
            return content
            
        except Exception as e:
            memory_logger.error(f"获取完整内容失败: {str(e)}")
            return content
    
    async def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        wait_for_api: bool = False
    ) -> str:
        """
        添加新记忆
        
        Args:
            content: 记忆内容
            metadata: 记忆元数据
            wait_for_api: 是否等待 API 调用结果
            
        Returns:
            str: 记忆ID
        """
        try:
            # 生成记忆ID
            memory_id = f"memory_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.vector_store)}"
            
            # 获取完整内容
            if wait_for_api:
                content = await self.get_complete_content(memory_id, content, metadata)
            
            # 添加到检索系统
            await self.retriever.add_memory(
                memory_id=memory_id,
                content=content,
                metadata=metadata
            )
            
            # 保存状态
            await self._save_state()
            
            memory_logger.info(f"成功添加新记忆: {memory_id}")
            return memory_id
            
        except Exception as e:
            memory_logger.error(f"添加记忆失败: {str(e)}")
            raise
    
    async def add_memories_batch(
        self,
        memories: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> List[str]:
        """
        批量添加记忆
        
        Args:
            memories: 记忆列表，每个记忆包含 content 和可选的 metadata
            show_progress: 是否显示进度条
            
        Returns:
            List[str]: 记忆ID列表
        """
        try:
            # 为每个记忆生成ID
            memory_ids = []
            processed_memories = []
            
            for memory in memories:
                memory_id = f"memory_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.vector_store) + len(memory_ids)}"
                memory_ids.append(memory_id)
                
                processed_memories.append({
                    'id': memory_id,
                    'content': memory['content'],
                    'metadata': memory.get('metadata')
                })
            
            # 使用批处理器添加记忆
            await self.batch_processor.process_memories(
                memories=processed_memories,
                show_progress=show_progress
            )
            
            # 保存状态
            await self._save_state()
            
            memory_logger.info(f"成功批量添加 {len(memory_ids)} 条记忆")
            return memory_ids
            
        except Exception as e:
            memory_logger.error(f"批量添加记忆失败: {str(e)}")
            raise
    
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
            results = await self.retriever.search_memories(
                query=query,
                top_k=top_k,
                threshold=threshold,
                context=context
            )
            
            memory_logger.info(f"记忆搜索完成，找到 {len(results)} 条相关记忆")
            return results
            
        except Exception as e:
            memory_logger.error(f"搜索记忆失败: {str(e)}")
            raise
    
    async def optimize_index(self) -> None:
        """优化向量索引"""
        try:
            await self.batch_processor.optimize_index()
            await self._save_state()
            memory_logger.info("向量索引优化完成")
            
        except Exception as e:
            memory_logger.error(f"优化索引失败: {str(e)}")
            raise
    
    async def _save_state(self) -> None:
        """保存记忆系统状态"""
        try:
            vector_path = os.path.join(self.storage_path, 'vectors')
            await self.retriever.save_state(vector_path)
            memory_logger.info("记忆系统状态已保存")
            
        except Exception as e:
            memory_logger.error(f"保存状态失败: {str(e)}")
            raise
    
    async def clear_all(self) -> None:
        """清空所有记忆"""
        try:
            await self.retriever.clear()
            await self._save_state()
            memory_logger.info("所有记忆已清空")
            
        except Exception as e:
            memory_logger.error(f"清空记忆失败: {str(e)}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取记忆系统统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_memories': len(self.vector_store),
            'storage_path': self.storage_path,
            'last_update': datetime.now().isoformat()
        } 