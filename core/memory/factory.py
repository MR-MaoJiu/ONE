"""
记忆系统工厂模块
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from core.storage.memory_storage import MemoryStorage
from core.snapshot.snapshot_manager import SnapshotManager
from services.llm_service import LLMService
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
            # 创建存储
            storage = MemoryStorage()
            memory_factory_logger.info("存储初始化完成")
            
            # 加载 LLM 配置
            llm_config_path = str(Path(__file__).parent.parent.parent / 'config' / 'llm_config.json')
            memory_factory_logger.info(f"尝试加载 LLM 配置文件: {llm_config_path}")
            
            if os.path.exists(llm_config_path):
                with open(llm_config_path, 'r') as f:
                    loaded_llm_config = json.load(f)
                memory_factory_logger.info(f"成功加载 LLM 配置: {loaded_llm_config}")
                llm_config = loaded_llm_config
            else:
                memory_factory_logger.warning(f"LLM 配置文件不存在: {llm_config_path}")
            
            # 创建LLM服务
            memory_factory_logger.info(f"创建 LLM 服务，使用配置: {llm_config or {}}")
            llm_service = LLMService(llm_config or {})
            memory_factory_logger.info("LLM服务创建成功")
            
            # 创建快照管理器
            snapshot_manager = SnapshotManager(storage=storage, llm_service=llm_service)
            memory_factory_logger.info("快照管理器初始化完成")
            
            # 创建聊天管理器
            # 延迟导入以避免循环依赖
            from core.chat.chat_manager import ChatManager
            chat_manager = ChatManager(
                llm_service=llm_service,
                storage=storage,
                snapshot_manager=snapshot_manager
            )
            memory_factory_logger.info("聊天管理器初始化完成")
            
            return chat_manager
            
        except Exception as e:
            memory_factory_logger.error(f"创建记忆系统失败：{str(e)}", exc_info=True)
            raise 