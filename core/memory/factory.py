"""
记忆系统工厂模块
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from .storage import MemoryStorage
from .snapshot import SnapshotManager
from ..processor.snapshot_processor import SnapshotProcessor
from config.chat_config import ChatConfig
from config.memory_config import MemoryConfig
from services.llm_service import LLMService, LLMConfig
from utils.logger import get_logger

# 创建logger
memory_factory_logger = get_logger('memory_factory')

class MemorySystemFactory:
    """记忆系统工厂"""
    
    @staticmethod
    async def create_from_config(config_path: Optional[str] = None, llm_config: Optional[Dict[str, Any]] = None) -> 'ChatManager':
        """
        从配置创建记忆系统
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
            llm_config: LLM配置，如果为None则使用默认配置
        
        Returns:
            ChatManager: 聊天管理器实例
        """
        try:
            # 加载配置
            if config_path is None:
                config_path = str(Path(__file__).parent.parent.parent / 'config' / 'default_memory_config.json')
                
            memory_factory_logger.info(f"加载配置文件: {config_path}")
            config = MemoryConfig.from_file(config_path)
            
            # 创建存储
            storage = MemoryStorage(storage_dir=config.storage.storage_dir)
            memory_factory_logger.info("存储初始化完成")
            
            # 创建LLM服务
            llm_service = LLMService(llm_config or {})
            memory_factory_logger.info("LLM服务创建成功")
            
            # 创建快照管理器
            snapshot_manager = SnapshotManager(storage=storage, llm_service=llm_service)
            await snapshot_manager.initialize()
            memory_factory_logger.info("快照管理器初始化完成")
            
            # 创建快照处理器
            processor = SnapshotProcessor(
                snapshot_manager=snapshot_manager,
                config=config.snapshot
            )
            memory_factory_logger.info("快照处理器初始化完成")
            
            # 创建聊天管理器
            # 延迟导入以避免循环依赖
            from ..chat.chat_manager import ChatManager
            chat_manager = ChatManager(
                config=config.chat,
                llm_service=llm_service,
                snapshot_processor=processor
            )
            memory_factory_logger.info("聊天管理器初始化完成")
            
            return chat_manager
            
        except Exception as e:
            memory_factory_logger.error(f"创建记忆系统失败：{str(e)}", exc_info=True)
            raise 