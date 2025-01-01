"""
向量存储模块，用于记忆的语义检索
"""
import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from datetime import datetime
from utils.logger import get_logger

vector_logger = get_logger('vector_store')

class VectorStore:
    """向量存储类，用于管理和检索记忆的向量表示"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', vector_dim: int = 384):
        """
        初始化向量存储
        
        Args:
            model_name: embedding模型名称
            vector_dim: 向量维度
        """
        self.model_name = model_name
        self.vector_dim = vector_dim
        
        # 初始化embedding模型
        vector_logger.info(f"正在加载embedding模型: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # 初始化FAISS索引
        self.index = faiss.IndexFlatL2(vector_dim)
        
        # 初始化元快照索引
        self.meta_index = faiss.IndexFlatL2(vector_dim)
        
        # 内存映射：索引ID -> 记忆ID
        self.id_map: Dict[int, str] = {}
        self.meta_id_map: Dict[int, str] = {}
        
        # 记忆映射：记忆ID -> 内容
        self.memory_map: Dict[str, Dict[str, Any]] = {}
        self.meta_map: Dict[str, Dict[str, Any]] = {}
        
        # 向量缓存
        self._vector_cache: Dict[str, np.ndarray] = {}
        
        vector_logger.info("向量存储初始化完成")
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.6
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        优化的向量检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            threshold: 相似度阈值
            
        Returns:
            List[Tuple[Dict[str, Any], float]]: 记忆和相似度得分的列表
        """
        try:
            # 1. 生成查询向量
            query_vector = self.model.encode([query])[0]
            
            # 2. 使用FAISS的高效批量检索
            scores, indices = self.index.search(
                np.array([query_vector]).astype('float32'), 
                min(top_k * 2, len(self.id_map))  # 检索更多候选
            )
            
            # 3. 计算归一化分数并过滤
            results = []
            for score, idx in zip(scores[0], indices[0]):
                # 将L2距离转换为相似度分数
                similarity = 1 / (1 + score)
                
                # 获取记忆数据
                memory_id = self.id_map[idx]
                memory_data = self.memory_map[memory_id]
                
                # 添加额外的相关性计算
                final_score = similarity
                
                # 考虑记忆的重要性权重
                if 'importance' in memory_data.get('metadata', {}):
                    importance = memory_data['metadata']['importance']
                    final_score *= (1 + importance * 0.2)  # 重要性影响20%
                
                results.append((memory_data, final_score))
            
            # 4. 排序并返回结果
            results.sort(key=lambda x: x[1], reverse=True)
            
            vector_logger.info(f"向量检索完成，找到 {len(results)} 条结果")
            return results
            
        except Exception as e:
            vector_logger.error(f"向量检索失败: {str(e)}")
            raise
    
    async def search_meta_snapshots(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        搜索元快照
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            List[Tuple[Dict[str, Any], float]]: 元快照和相似度得分的列表
        """
        try:
            # 使用专门的元快照索引
            query_vector = self.model.encode([query])[0]
            
            # 使用高效的批量检索
            scores, indices = self.meta_index.search(
                np.array([query_vector]).astype('float32'),
                min(top_k, len(self.meta_id_map))
            )
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                similarity = 1 / (1 + score)
                meta_id = self.meta_id_map[idx]
                meta_data = self.meta_map[meta_id]
                results.append((meta_data, similarity))
            
            return results
            
        except Exception as e:
            vector_logger.error(f"元快照检索失败: {str(e)}")
            return []
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定ID的记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            Optional[Dict[str, Any]]: 记忆数据
        """
        return self.memory_map.get(memory_id)
    
    async def add_memory(self, memory_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        添加记忆到向量存储
        
        Args:
            memory_id: 记忆ID
            content: 记忆内容
            metadata: 记忆元数据
        """
        try:
            # 检查缓存
            if memory_id in self._vector_cache:
                vector = self._vector_cache[memory_id]
            else:
                # 生成embedding
                vector = self.model.encode([content])[0]
                # 添加到缓存
                self._vector_cache[memory_id] = vector
            
            # 添加到FAISS索引
            self.index.add(np.array([vector]).astype('float32'))
            
            # 更新映射
            current_id = len(self.id_map)
            self.id_map[current_id] = memory_id
            self.memory_map[memory_id] = {
                'id': memory_id,
                'content': content,
                'metadata': metadata or {},
                'vector_id': current_id,
                'timestamp': datetime.now().isoformat()
            }
            
            vector_logger.info(f"成功添加记忆: {memory_id}")
            
        except Exception as e:
            vector_logger.error(f"添加记忆失败: {str(e)}")
            raise
    
    async def add_meta_snapshot(
        self,
        meta_id: str,
        content: str,
        memory_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加元快照到向量存储
        
        Args:
            meta_id: 元快照ID
            content: 元快照内容
            memory_ids: 关联的记忆ID列表
            metadata: 元快照元数据
        """
        try:
            # 生成embedding
            vector = self.model.encode([content])[0]
            
            # 添加到元快照索引
            self.meta_index.add(np.array([vector]).astype('float32'))
            
            # 更新映射
            current_id = len(self.meta_id_map)
            self.meta_id_map[current_id] = meta_id
            self.meta_map[meta_id] = {
                'id': meta_id,
                'content': content,
                'memory_ids': memory_ids,
                'metadata': metadata or {},
                'vector_id': current_id,
                'timestamp': datetime.now().isoformat()
            }
            
            vector_logger.info(f"成功添加元快照: {meta_id}")
            
        except Exception as e:
            vector_logger.error(f"添加元快照失败: {str(e)}")
            raise
    
    def get_all_vectors(self) -> Optional[np.ndarray]:
        """
        获取所有向量
        
        Returns:
            Optional[np.ndarray]: 所有向量的数组，如果为空则返回None
        """
        try:
            if self.index.ntotal == 0:
                return None
            
            # 获取所有向量
            vectors = faiss.vector_to_array(self.index.get_xb())
            vectors = vectors.reshape(self.index.ntotal, self.vector_dim)
            
            return vectors
            
        except Exception as e:
            vector_logger.error(f"获取向量失败: {str(e)}")
            return None
    
    def rebuild_index(self, vectors: np.ndarray) -> None:
        """
        重建优化的索引
        
        Args:
            vectors: 向量数组
        """
        try:
            # 创建新的优化索引
            optimized_index = faiss.IndexIVFFlat(
                faiss.IndexFlatL2(self.vector_dim),  # 量化器
                self.vector_dim,  # 向量维度
                min(int(np.sqrt(len(vectors))), 100)  # 聚类中心数量
            )
            
            # 训练索引
            optimized_index.train(vectors)
            
            # 添加向量
            optimized_index.add(vectors)
            
            # 替换旧索引
            self.index = optimized_index
            
            vector_logger.info("索引重建完成")
            
        except Exception as e:
            vector_logger.error(f"重建索引失败: {str(e)}")
            raise
    
    async def save(self, path: str) -> None:
        """
        保存向量存储到文件
        
        Args:
            path: 保存路径
        """
        try:
            os.makedirs(path, exist_ok=True)
            
            # 保存FAISS索引
            index_path = os.path.join(path, 'index.faiss')
            faiss.write_index(self.index, index_path)
            
            # 保存元快照索引
            meta_index_path = os.path.join(path, 'meta_index.faiss')
            faiss.write_index(self.meta_index, meta_index_path)
            
            # 保存映射数据
            mappings = {
                'id_map': self.id_map,
                'meta_id_map': self.meta_id_map,
                'memory_map': self.memory_map,
                'meta_map': self.meta_map
            }
            mappings_path = os.path.join(path, 'mappings.json')
            with open(mappings_path, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)
            
            vector_logger.info(f"向量存储已保存到: {path}")
            
        except Exception as e:
            vector_logger.error(f"保存失败: {str(e)}")
            raise
    
    async def load(self, path: str) -> None:
        """
        从文件加载向量存储
        
        Args:
            path: 加载路径
        """
        try:
            # 加载FAISS索引
            index_path = os.path.join(path, 'index.faiss')
            self.index = faiss.read_index(index_path)
            
            # 加载元快照索引
            meta_index_path = os.path.join(path, 'meta_index.faiss')
            if os.path.exists(meta_index_path):
                self.meta_index = faiss.read_index(meta_index_path)
            
            # 加载映射数据
            mappings_path = os.path.join(path, 'mappings.json')
            with open(mappings_path, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
            
            self.id_map = {int(k): v for k, v in mappings['id_map'].items()}
            self.meta_id_map = {int(k): v for k, v in mappings.get('meta_id_map', {}).items()}
            self.memory_map = mappings['memory_map']
            self.meta_map = mappings.get('meta_map', {})
            
            # 清空向量缓存
            self._vector_cache.clear()
            
            vector_logger.info(f"向量存储已加载，共 {len(self.memory_map)} 条记忆，{len(self.meta_map)} 个元快照")
            
        except Exception as e:
            vector_logger.error(f"加载失败: {str(e)}")
            raise
    
    async def clear(self) -> None:
        """清空向量存储"""
        try:
            self.index = faiss.IndexFlatL2(self.vector_dim)
            self.meta_index = faiss.IndexFlatL2(self.vector_dim)
            self.id_map.clear()
            self.meta_id_map.clear()
            self.memory_map.clear()
            self.meta_map.clear()
            self._vector_cache.clear()
            vector_logger.info("向量存储已清空")
            
        except Exception as e:
            vector_logger.error(f"清空失败: {str(e)}")
            raise
    
    def __len__(self) -> int:
        """返回记忆数量"""
        return len(self.memory_map) 