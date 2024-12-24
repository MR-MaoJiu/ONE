"""
记忆存储模块
提供基于文件系统的记忆存储实现
"""
import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from utils.logger import get_logger

# 创建logger
storage_logger = get_logger('storage')

class MemoryStorage:
    """记忆存储类"""
    
    def __init__(self, storage_dir: str):
        """
        初始化存储
        
        Args:
            storage_dir: 存储根目录
        """
        self.storage_dir = Path(storage_dir)
        self.memories_dir = self.storage_dir / 'memories'
        self.snapshots_dir = self.storage_dir / 'snapshots'
        self.meta_snapshots_dir = self.storage_dir / 'meta_snapshots'
        self.index_file = self.storage_dir / 'index.json'
        
        # 创建目录
        self.memories_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.meta_snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载或创建索引
        self.index = self._load_index()
        storage_logger.info("存储初始化完成，根目录：%s", storage_dir)
    
    def _load_index(self) -> Dict:
        """加载索引文件"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                storage_logger.error(f"加载索引文件失败：{str(e)}")
                return self._create_index()
        else:
            return self._create_index()
    
    def _create_index(self) -> Dict:
        """创建新的索引"""
        index = {
            'memories': {},
            'snapshots': {},
            'meta_snapshots': {},
            'categories': {}
        }
        self._save_index(index)
        return index
    
    def _save_index(self, index: Dict):
        """保存索引文件"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            storage_logger.error(f"保存索引文件失败：{str(e)}")
    
    async def save_memory(self, memory_id: str, memory_data: Dict):
        """
        保存记忆
        
        Args:
            memory_id: 记忆ID
            memory_data: 记忆数据
        """
        try:
            file_path = self.memories_dir / f"{memory_id}.json"
            relative_path = f"memories/{memory_id}.json"
            
            async with asyncio.Lock():
                # 保存记忆数据
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(memory_data, f, indent=2, ensure_ascii=False)
                
                # 更新索引
                if memory_id not in self.index['memories']:
                    self.index['memories'][memory_id] = {
                        'path': relative_path,
                        'timestamp': datetime.now().isoformat(),
                        'type': 'base'
                    }
                    self._save_index(self.index)
                    
            storage_logger.debug("保存记忆成功：%s", memory_id)
            
        except Exception as e:
            storage_logger.error(f"保存记忆失败：{str(e)}")
            raise
    
    async def save_snapshot(self, snapshot_id: str, snapshot_data: Dict):
        """
        保存快照
        
        Args:
            snapshot_id: 快照ID
            snapshot_data: 快照数据
        """
        try:
            file_path = self.snapshots_dir / f"{snapshot_id}.json"
            relative_path = f"snapshots/{snapshot_id}.json"
            
            async with asyncio.Lock():
                # 保存快照数据
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
                
                # 更新索引
                if snapshot_id not in self.index['snapshots']:
                    self.index['snapshots'][snapshot_id] = {
                        'path': relative_path,
                        'timestamp': datetime.now().isoformat(),
                        'type': 'snapshot'
                    }
                    self._save_index(self.index)
                    
            storage_logger.debug("保存快照成功：%s", snapshot_id)
            
        except Exception as e:
            storage_logger.error(f"保存快照失败：{str(e)}")
            raise
    
    async def save_meta_snapshot(self, meta_id: str, meta_data: Dict):
        """
        保存元快照
        
        Args:
            meta_id: 元快照ID
            meta_data: 元快照数据
        """
        try:
            file_path = self.meta_snapshots_dir / f"{meta_id}.json"
            relative_path = f"meta_snapshots/{meta_id}.json"
            
            async with asyncio.Lock():
                # 保存元快照数据
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, indent=2, ensure_ascii=False)
                
                # 更新索引
                if meta_id not in self.index['meta_snapshots']:
                    self.index['meta_snapshots'][meta_id] = {
                        'path': relative_path,
                        'timestamp': datetime.now().isoformat(),
                        'type': 'meta'
                    }
                    self._save_index(self.index)
                    
            storage_logger.debug("保存元快照成功：%s", meta_id)
            
        except Exception as e:
            storage_logger.error(f"保存元快照失败：{str(e)}")
            raise
    
    async def load_memory(self, memory_id: str) -> Optional[Dict]:
        """
        加载记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            Dict: 记忆数据，如果不存在则返回None
        """
        try:
            file_path = self.memories_dir / f"{memory_id}.json"
            if not file_path.exists():
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            storage_logger.error(f"加载记忆失败：{str(e)}")
            return None
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict]:
        """
        加载快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Dict: 快照数据，如果不存在则返回None
        """
        try:
            file_path = self.snapshots_dir / f"{snapshot_id}.json"
            if not file_path.exists():
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            storage_logger.error(f"加载快照失败：{str(e)}")
            return None
    
    async def load_meta_snapshot(self, meta_id: str) -> Optional[Dict]:
        """
        加载元快照
        
        Args:
            meta_id: 元快照ID
            
        Returns:
            Dict: 元快照数据，如果不存在则返回None
        """
        try:
            file_path = self.meta_snapshots_dir / f"{meta_id}.json"
            if not file_path.exists():
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            storage_logger.error(f"加载元快照失败：{str(e)}")
            return None
    
    async def cleanup_old_memories(self, days: int = 30):
        """
        清理旧记忆
        
        Args:
            days: 保留天数，默认30天
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            removed_memories = []
            removed_snapshots = []
            removed_meta_snapshots = []
            
            # 清理记忆
            for memory_id, memory_info in list(self.index['memories'].items()):
                timestamp = datetime.fromisoformat(memory_info['timestamp'])
                if timestamp < cutoff:
                    file_path = self.memories_dir / f"{memory_id}.json"
                    file_path.unlink(missing_ok=True)
                    removed_memories.append(memory_id)
                    del self.index['memories'][memory_id]
            
            # 清理快照
            for snapshot_id, snapshot_info in list(self.index['snapshots'].items()):
                timestamp = datetime.fromisoformat(snapshot_info['timestamp'])
                if timestamp < cutoff:
                    file_path = self.snapshots_dir / f"{snapshot_id}.json"
                    file_path.unlink(missing_ok=True)
                    removed_snapshots.append(snapshot_id)
                    del self.index['snapshots'][snapshot_id]
            
            # 清理元快照
            for meta_id, meta_info in list(self.index['meta_snapshots'].items()):
                timestamp = datetime.fromisoformat(meta_info['timestamp'])
                if timestamp < cutoff:
                    file_path = self.meta_snapshots_dir / f"{meta_id}.json"
                    file_path.unlink(missing_ok=True)
                    removed_meta_snapshots.append(meta_id)
                    del self.index['meta_snapshots'][meta_id]
            
            # 保存索引
            self._save_index(self.index)
            
            storage_logger.info(
                "清理完成：删除%d条记忆，%d个快照，%d个元快照",
                len(removed_memories),
                len(removed_snapshots),
                len(removed_meta_snapshots)
            )
            
        except Exception as e:
            storage_logger.error(f"清理失败：{str(e)}")
            raise 