"""
对话管理器
负责处理对话流程，包括记忆检索、对话生成等
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime

from ..memory.snapshot import BaseMemory
from ..processor.snapshot_processor import SnapshotProcessor
from services.llm_service import LLMService
from config.chat_config import ChatConfig
from utils.logger import get_logger

# 创建对话管理器专用的logger
chat_logger = get_logger('chat_manager')

class ChatManager:
    """对话管理器"""
    
    def __init__(self, config: ChatConfig, llm_service: LLMService, snapshot_processor: SnapshotProcessor):
        self.config = config
        self.llm_service = llm_service
        self.snapshot_processor = snapshot_processor
        self.history: List[Dict[str, Any]] = []
        chat_logger.info("对话管理器初始化完成，配置：%s", config)
    
    def _prepare_context(self, query: str) -> Dict[str, Any]:
        """准备对话上下文"""
        return {
            'history': self.history[-self.config.max_history_length:],
            'current_query': query,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _get_relevant_memories(self, context: Dict[str, Any]) -> List[Tuple[BaseMemory, float]]:
        """获取相关记忆"""
        try:
            chat_logger.info("开始检索相关记忆")
            
            # 使用快照处理器获取相关记忆
            memories = await self.snapshot_processor.get_relevant_memories(context)
            
            # 应用时间衰减
            now = datetime.now().timestamp()
            weighted_memories = []
            for memory, score in memories:
                time_diff = now - memory.timestamp.timestamp()
                time_weight = 1.0 / (1.0 + self.config.memory_recency_weight * time_diff / (24 * 3600))  # 24小时作为基准
                weighted_score = score * time_weight
                weighted_memories.append((memory, weighted_score))
            
            # 按加权分数排序并限制数量
            weighted_memories.sort(key=lambda x: x[1], reverse=True)
            relevant_memories = weighted_memories[:self.config.max_relevant_memories]
            
            chat_logger.info(
                "找到 %d 条相关记忆，分数范围：%.2f - %.2f",
                len(relevant_memories),
                relevant_memories[-1][1] if relevant_memories else 0,
                relevant_memories[0][1] if relevant_memories else 0
            )
            
            return relevant_memories
            
        except Exception as e:
            chat_logger.error("获取相关记忆失败：%s", str(e), exc_info=True)
            return []
    
    async def _create_memory(self, query: str, response: str, context: Dict[str, Any]):
        """创建新的记忆"""
        try:
            # 创建记忆内容
            memory_content = {
                "content": f"User: {query}\nAssistant: {response}",
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
            # 处理记忆，生成快照
            await self.snapshot_processor.process_memory(memory_content)
            
            chat_logger.info("成功创建新记忆")
            
        except Exception as e:
            chat_logger.error("创建记忆失败：%s", str(e), exc_info=True)
    
    def _add_to_history(self, query: str, response: str):
        """添加对话到历史记录"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'is_user': True,
            'content': query
        })
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'is_user': False,
            'content': response
        })
        
        # 保持历史记录在限定长度内
        if len(self.history) > self.config.max_history_length * 2:
            self.history = self.history[-self.config.max_history_length * 2:]
    
    async def chat(self, query: str) -> str:
        """处理用户输入，生成回复"""
        try:
            chat_logger.info("收到用户输入：%s", query)
            
            # 准备上下文
            context = self._prepare_context(query)
            
            # 获取相关记忆
            relevant_memories = await self._get_relevant_memories(context)
            
            # 将相关记忆添加到上下文
            if relevant_memories:
                context['relevant_memories'] = [
                    {
                        'content': memory.content,
                        'score': score,
                        'timestamp': memory.timestamp.isoformat()
                    }
                    for memory, score in relevant_memories
                ]
            
            # 生成回复
            response = await self.llm_service.chat(query, context)
            
            # 添加到历史记录
            self._add_to_history(query, response)
            
            # 创建新的记忆
            await self._create_memory(query, response, context)
            
            chat_logger.info("生成回复：%s", response)
            return response
            
        except Exception as e:
            chat_logger.error("处理对话失败：%s", str(e), exc_info=True)
            return "抱歉，处理您的输入时出现了错误。"
    
    def clear_history(self):
        """清空对话历史"""
        self.history.clear()
        chat_logger.info("对话历史已清空") 