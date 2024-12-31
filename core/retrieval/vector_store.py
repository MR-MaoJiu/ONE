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
        
        # 内存映射：索引ID -> 记忆ID
        self.id_map: Dict[int, str] = {}
        
        # 记忆映射：记忆ID -> 内容
        self.memory_map: Dict[str, Dict[str, Any]] = {}
        
        # 向量缓存
        self._vector_cache: Dict[str, np.ndarray] = {}
        
        vector_logger.info("向量存储初始化完成")
    
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
                'content': content,
                'metadata': metadata or {},
                'vector_id': current_id,
                'timestamp': datetime.now().isoformat()
            }
            
            vector_logger.info(f"成功添加记忆: {memory_id}")
            
        except Exception as e:
            vector_logger.error(f"添加记忆失败: {str(e)}")
            raise
    
    async def search(self, query: str, top_k: int = 5, threshold: float = 0.6) -> List[Tuple[Dict[str, Any], float]]:
        """
        搜索相关记忆
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            threshold: 相似度阈值
            
        Returns:
            List[Tuple[Dict[str, Any], float]]: 记忆和相似度得分的列表
        """
        try:
            # 生成查询向量
            query_vector = self.model.encode([query])[0]
            
            # 搜索最相似的向量
            scores, indices = self.index.search(
                np.array([query_vector]).astype('float32'), 
                min(top_k, len(self.id_map))
            )
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                # 计算余弦相似度（FAISS返回的是L2距离）
                similarity = 1 / (1 + score)
                
                # 只返回相似度超过阈值的结果
                if similarity >= threshold:
                    memory_id = self.id_map[idx]
                    memory_data = self.memory_map[memory_id]
                    results.append((memory_data, similarity))
            
            vector_logger.info(f"搜索完成，找到 {len(results)} 条相关记忆")
            return results
            
        except Exception as e:
            vector_logger.error(f"搜索失败: {str(e)}")
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
            
            # 保存映射数据
            mappings = {
                'id_map': self.id_map,
                'memory_map': self.memory_map
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
            
            # 加载映射数据
            mappings_path = os.path.join(path, 'mappings.json')
            with open(mappings_path, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
            
            self.id_map = {int(k): v for k, v in mappings['id_map'].items()}
            self.memory_map = mappings['memory_map']
            
            # 清空向量缓存
            self._vector_cache.clear()
            
            vector_logger.info(f"向量存储已加载，共 {len(self.memory_map)} 条记忆")
            
        except Exception as e:
            vector_logger.error(f"加载失败: {str(e)}")
            raise
    
    async def clear(self) -> None:
        """清空向量存储"""
        try:
            self.index = faiss.IndexFlatL2(self.vector_dim)
            self.id_map.clear()
            self.memory_map.clear()
            self._vector_cache.clear()
            vector_logger.info("向量存储已清空")
            
        except Exception as e:
            vector_logger.error(f"清空失败: {str(e)}")
            raise
    
    def __len__(self) -> int:
        """返回记忆数量"""
        return len(self.memory_map) 