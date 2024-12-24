"""
基于文件系统的记忆存储实现
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from .base import Memory, MemoryStore, BaseSnapshot, DetailSnapshot, MemoryStorageException
from utils.logger import memory_logger

class FileMemoryStore(MemoryStore):
    """基于文件系统的记忆存储"""
    
    def __init__(self, base_dir: str):
        """初始化存储
        
        Args:
            base_dir: 基础存储目录
        """
        self.base_dir = Path(base_dir)
        
        # 记忆存储目录
        self.memories_dir = self.base_dir / "memories"
        
        # 快照存储目录
        self.snapshots_dir = self.base_dir / "snapshots"
        self.base_snapshots_dir = self.snapshots_dir / "base"
        self.detail_snapshots_dir = self.snapshots_dir / "detail"
        
        # 索引存储目录
        self.index_dir = self.base_dir / "indexes"
        self.memory_snapshot_index_dir = self.index_dir / "memory_snapshots"
        self.snapshot_memory_index_dir = self.index_dir / "snapshot_memories"
        
        # 创建必要的目录
        for dir_path in [
            self.memories_dir,
            self.snapshots_dir,
            self.base_snapshots_dir,
            self.detail_snapshots_dir,
            self.index_dir,
            self.memory_snapshot_index_dir,
            self.snapshot_memory_index_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        memory_logger.info(f"初始化文件存储: {base_dir}")
        
        # 加载索引
        self._load_indexes()
    
    def _load_indexes(self):
        """加载索引"""
        try:
            # 记忆ID -> 快照ID的映射
            self.memory_snapshot_index: Dict[str, Set[str]] = {}
            
            # 快照ID -> 记忆ID的映射
            self.snapshot_memory_index: Dict[str, Set[str]] = {}
            
            # 基础快照ID -> 详细快照ID的映射
            self.base_detail_index: Dict[str, Set[str]] = {}
            
            # 加载记忆-快照索引
            for file_path in self.memory_snapshot_index_dir.glob("*.json"):
                memory_id = file_path.stem
                with open(file_path, "r", encoding="utf-8") as f:
                    self.memory_snapshot_index[memory_id] = set(json.load(f))
            
            # 加载快照-记忆索引
            for file_path in self.snapshot_memory_index_dir.glob("*.json"):
                snapshot_id = file_path.stem
                with open(file_path, "r", encoding="utf-8") as f:
                    self.snapshot_memory_index[snapshot_id] = set(json.load(f))
            
            # 加载基础快照索引
            for file_path in self.base_snapshots_dir.glob("*.json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.base_detail_index[data["snapshot_id"]] = set(data["detail_snapshot_ids"])
            
            memory_logger.info("索引加载完成")
            
        except Exception as e:
            memory_logger.error(f"加载索引失败: {str(e)}")
            raise MemoryStorageException(f"加载索引失败: {str(e)}")
    
    def _save_memory_snapshot_index(self, memory_id: str):
        """保存记忆-快照索引"""
        try:
            file_path = self.memory_snapshot_index_dir / f"{memory_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(list(self.memory_snapshot_index.get(memory_id, set())), f)
        except Exception as e:
            memory_logger.error(f"保存记忆-快照索引失败: {str(e)}")
    
    def _save_snapshot_memory_index(self, snapshot_id: str):
        """保存快照-记忆索引"""
        try:
            file_path = self.snapshot_memory_index_dir / f"{snapshot_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(list(self.snapshot_memory_index.get(snapshot_id, set())), f)
        except Exception as e:
            memory_logger.error(f"保存快照-记忆索引失败: {str(e)}")
    
    def add(self, memory: Memory) -> bool:
        """添加记忆"""
        try:
            # 保存记忆
            file_path = self.memories_dir / f"{memory.memory_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(memory.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 初始化索引
            if memory.memory_id not in self.memory_snapshot_index:
                self.memory_snapshot_index[memory.memory_id] = set()
                self._save_memory_snapshot_index(memory.memory_id)
            
            return True
        except Exception as e:
            memory_logger.error(f"添加记忆失败: {str(e)}")
            return False
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """获取指定记忆"""
        try:
            file_path = self.memories_dir / f"{memory_id}.json"
            if not file_path.exists():
                return None
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Memory.from_dict(data)
        except Exception as e:
            memory_logger.error(f"获取记忆失败: {str(e)}")
            return None
    
    def list(self) -> List[Memory]:
        """列出所有记忆"""
        memories = []
        try:
            for file_path in self.memories_dir.glob("*.json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                memories.append(Memory.from_dict(data))
            return memories
        except Exception as e:
            memory_logger.error(f"列出记忆失败: {str(e)}")
            return []
    
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            # 删除记忆文件
            file_path = self.memories_dir / f"{memory_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            # 更新索引
            if memory_id in self.memory_snapshot_index:
                # 获取关联的快照
                snapshot_ids = self.memory_snapshot_index[memory_id]
                
                # 从快照-记忆索引中删除
                for snapshot_id in snapshot_ids:
                    if snapshot_id in self.snapshot_memory_index:
                        self.snapshot_memory_index[snapshot_id].discard(memory_id)
                        self._save_snapshot_memory_index(snapshot_id)
                
                # 删除记忆-快照索引
                del self.memory_snapshot_index[memory_id]
                index_path = self.memory_snapshot_index_dir / f"{memory_id}.json"
                if index_path.exists():
                    index_path.unlink()
            
            return True
        except Exception as e:
            memory_logger.error(f"删除记忆失败: {str(e)}")
            return False
    
    def update(self, memory: Memory) -> bool:
        """更新记忆"""
        return self.add(memory)
    
    def get_base_snapshots(self) -> List[BaseSnapshot]:
        """获取所有基础快照"""
        snapshots = []
        try:
            for file_path in self.base_snapshots_dir.glob("*.json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                snapshots.append(BaseSnapshot(**data))
            return snapshots
        except Exception as e:
            memory_logger.error(f"获取基础快照失败: {str(e)}")
            return []
    
    def get_detail_snapshots(self, base_snapshot_id: str) -> List[DetailSnapshot]:
        """获取指定基础快照关联的详细快照"""
        snapshots = []
        try:
            # 从索引获取详细快照ID
            detail_ids = self.base_detail_index.get(base_snapshot_id, set())
            
            # 加载详细快照
            for snapshot_id in detail_ids:
                file_path = self.detail_snapshots_dir / f"{snapshot_id}.json"
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                    snapshots.append(DetailSnapshot(**data))
            
            return snapshots
        except Exception as e:
            memory_logger.error(f"获取详细快照失败: {str(e)}")
            return []
    
    def get_memories_by_ids(self, memory_ids: List[str]) -> List[Memory]:
        """根据ID列表批量获取记忆"""
        memories = []
        for memory_id in memory_ids:
            memory = self.get(memory_id)
            if memory:
                memories.append(memory)
        return memories
    
    def create_detail_snapshot(self, memories: List[Memory]) -> DetailSnapshot:
        """从记忆列表创建详细快照"""
        try:
            # 生成快照ID
            snapshot_id = f"detail_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 提取关键信息
            memory_contents = [m.content for m in memories]
            memory_emotions = []
            for m in memories:
                for e in m.emotions:
                    if isinstance(e, dict) and 'type' in e:
                        memory_emotions.append(e['type'])
            memory_ids = [m.memory_id for m in memories]
            
            # 创建快照
            snapshot = DetailSnapshot(
                snapshot_id=snapshot_id,
                summary="\n".join(memory_contents[:3]),  # 简单示例,实际应该用LLM生成摘要
                key_elements=list(set(word for content in memory_contents 
                                    for word in content.split()[:10])),  # 简单示例
                emotion_tags=list(set(memory_emotions)),
                memory_ids=memory_ids,
                timestamp=datetime.now()
            )
            
            # 保存快照
            file_path = self.detail_snapshots_dir / f"{snapshot_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(snapshot.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 更新索引
            for memory_id in memory_ids:
                if memory_id not in self.memory_snapshot_index:
                    self.memory_snapshot_index[memory_id] = set()
                self.memory_snapshot_index[memory_id].add(snapshot_id)
                self._save_memory_snapshot_index(memory_id)
            
            if snapshot_id not in self.snapshot_memory_index:
                self.snapshot_memory_index[snapshot_id] = set()
            self.snapshot_memory_index[snapshot_id].update(memory_ids)
            self._save_snapshot_memory_index(snapshot_id)
            
            return snapshot
            
        except Exception as e:
            memory_logger.error(f"创建详细快照失败: {str(e)}")
            raise MemoryStorageException(f"创建详细快照失败: {str(e)}")
    
    def create_base_snapshot(self, detail_snapshots: List[DetailSnapshot]) -> BaseSnapshot:
        """从详细快照列表创建基础快照"""
        try:
            # 生成快照ID
            snapshot_id = f"base_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 提取关键信息
            all_key_elements = []
            detail_snapshot_ids = []
            for snapshot in detail_snapshots:
                all_key_elements.extend(snapshot.key_elements)
                detail_snapshot_ids.append(snapshot.snapshot_id)
            
            # 创建快照
            snapshot = BaseSnapshot(
                snapshot_id=snapshot_id,
                category="自动分类",  # 简单示例,实际应该用LLM生成分类
                keywords=list(set(all_key_elements)),
                detail_snapshot_ids=detail_snapshot_ids
            )
            
            # 保存快照
            file_path = self.base_snapshots_dir / f"{snapshot_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(snapshot.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self.base_detail_index[snapshot_id] = set(detail_snapshot_ids)
            
            return snapshot
            
        except Exception as e:
            memory_logger.error(f"创建基础快照失败: {str(e)}")
            raise MemoryStorageException(f"创建基础快照失败: {str(e)}")
            
    def get_snapshot_memories(self, snapshot_id: str) -> List[Memory]:
        """获取快照关联的所有记忆"""
        try:
            memory_ids = self.snapshot_memory_index.get(snapshot_id, set())
            return self.get_memories_by_ids(list(memory_ids))
        except Exception as e:
            memory_logger.error(f"获取快照记忆失败: {str(e)}")
            return []
    
    def get_memory_snapshots(self, memory_id: str) -> List[str]:
        """获取记忆关联的所有快照ID"""
        try:
            return list(self.memory_snapshot_index.get(memory_id, set()))
        except Exception as e:
            memory_logger.error(f"获取记忆快照失败: {str(e)}")
            return []
    
    def get_working_memories(self) -> List[Memory]:
        """获取工作记忆"""
        try:
            memories = self.list()
            # 按时间戳排序，返回最近的10条记忆
            memories.sort(key=lambda m: m.timestamp, reverse=True)
            return memories[:10]
        except Exception as e:
            memory_logger.error(f"获取工作记忆失败: {str(e)}")
            return []
    
    def get_episodic_memories(self) -> List[Memory]:
        """获取情节记忆"""
        try:
            memories = self.list()
            # 按重要性分数排序
            memories.sort(key=lambda m: m.importance_score, reverse=True)
            return memories
        except Exception as e:
            memory_logger.error(f"获取情节记忆失败: {str(e)}")
            return []
    
    def get_semantic_memories(self) -> List[Memory]:
        """获取语义记忆"""
        try:
            # 获取所有基础快照
            base_snapshots = self.get_base_snapshots()
            
            # 收集所有记忆ID
            memory_ids = set()
            for snapshot in base_snapshots:
                # 获取详细快照
                detail_snapshots = self.get_detail_snapshots(snapshot.snapshot_id)
                # 收集记忆ID
                for detail in detail_snapshots:
                    memory_ids.update(detail.memory_ids)
            
            # 获取记忆
            return self.get_memories_by_ids(list(memory_ids))
        except Exception as e:
            memory_logger.error(f"获取语义记忆失败: {str(e)}")
            return []
    
    def clear_all_memories(self) -> bool:
        """清空所有记忆"""
        try:
            # 删除所有记忆文件
            for file_path in self.memories_dir.glob("*.json"):
                file_path.unlink()
            
            # 清空索引
            self.memory_snapshot_index.clear()
            self.snapshot_memory_index.clear()
            self.base_detail_index.clear()
            
            # 删除所有索引文件
            for file_path in self.memory_snapshot_index_dir.glob("*.json"):
                file_path.unlink()
            for file_path in self.snapshot_memory_index_dir.glob("*.json"):
                file_path.unlink()
            
            # 删除所有快照文件
            for file_path in self.base_snapshots_dir.glob("*.json"):
                file_path.unlink()
            for file_path in self.detail_snapshots_dir.glob("*.json"):
                file_path.unlink()
                
            return True
        except Exception as e:
            memory_logger.error(f"清空记忆失败: {str(e)}")
            return False