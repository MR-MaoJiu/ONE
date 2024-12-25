"""
聊天管理器模块
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from services.llm_service import LLMService
from core.storage.memory_storage import MemoryStorage
from core.snapshot.snapshot_manager import SnapshotManager
from utils.logger import get_logger

chat_logger = get_logger('chat')

class ChatManager:
    """聊天管理器"""
    
    def __init__(self, llm_service: LLMService, storage: MemoryStorage, snapshot_manager: SnapshotManager):
        """
        初始化聊天管理器
        
        Args:
            llm_service: LLM服务实例
            storage: 存储实例
            snapshot_manager: 快照管理器实例
        """
        self.llm_service = llm_service
        self.storage = storage
        self.snapshot_manager = snapshot_manager
        self.history = []
        chat_logger.info("聊天管理器初始化完成")
    
    async def chat(self, query: str) -> Dict[str, Any]:
        """
        处理用户输入，生成回复
        
        Args:
            query: 用户输入
            
        Returns:
            Dict[str, Any]: 包含回复文本和思考步骤的字典
        """
        try:
            chat_logger.info("收到用户输入：%s", query)
            
            # 准备上下文
            context = {
                'history': self.history,
            }
            
            # 获取相关记忆
            relevant_snapshots = await self.snapshot_manager.get_relevant_snapshots(query)
            if relevant_snapshots:
                context['relevant_memories'] = [
                    {
                        'content': snapshot.content,
                        'score': score,
                        'timestamp': snapshot.timestamp.isoformat()
                    }
                    for snapshot, score in relevant_snapshots
                ]
            
            # 生成回复
            result = await self.llm_service.chat(query, context)
            
            # 保存记忆
            memory = await self.storage.save_memory(
                content=query,
                metadata={'is_user': True}
            )
            await self.storage.save_memory(
                content=result['response'],
                metadata={'is_user': False}
            )
            
            # 创建快照
            await self.snapshot_manager.create_snapshot(memory)
            
            # 更新历史记录
            self._add_to_history(query, result['response'])
            
            return result
            
        except Exception as e:
            chat_logger.error("处理对话失败：%s", str(e), exc_info=True)
            return {
                'response': "抱歉，处理您的输入时出现了错误。",
                'thinking_steps': []
            }
    
    def _add_to_history(self, query: str, response: str):
        """添加到历史记录"""
        self.history.extend([
            {
                'content': query,
                'timestamp': datetime.now().isoformat(),
                'is_user': True
            },
            {
                'content': response,
                'timestamp': datetime.now().isoformat(),
                'is_user': False
            }
        ])
        
        # 保持历史记录在限定长度内
        if len(self.history) > 20:
            self.history = self.history[-20:]
    
    async def get_all_memories(self) -> List[Dict[str, Any]]:
        """获取所有记忆"""
        try:
            memories = await self.storage.get_all_memories()
            return [memory.to_dict() for memory in memories]
        except Exception as e:
            chat_logger.error("获取记忆失败：%s", str(e))
            return []
    
    async def get_all_snapshots(self) -> List[Dict[str, Any]]:
        """获取所有快照"""
        try:
            snapshots = await self.storage.get_all_snapshots()
            return [snapshot.to_dict() for snapshot in snapshots]
        except Exception as e:
            chat_logger.error("获取快照失败：%s", str(e))
            return []
    
    async def clear_all(self):
        """清空所有记忆和历史记录"""
        try:
            # 清空数据库
            await self.storage.clear_all()
            # 清空历史记录
            self.history.clear()
            chat_logger.info("所有数据已清空")
        except Exception as e:
            chat_logger.error("清空数据失败：%s", str(e))
            raise 