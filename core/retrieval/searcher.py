"""
记忆检索器实现
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json

from ..memory import Memory, MemoryStore, BaseSnapshot, DetailSnapshot
from ..processor.emotion import EmotionProcessor
from ..processor.concept import ConceptProcessor
from services.llm_service import LLMService
from prompts.memory_prompts import (
    MEMORY_RETRIEVAL_TEMPLATE,
    BASE_SNAPSHOT_TEMPLATE,
    DETAIL_SNAPSHOT_TEMPLATE
)
from utils.logger import memory_logger

@dataclass
class SearchConfig:
    """检索配置"""
    max_results: int = 10  # 最大返回结果数
    min_relevance: float = 0.6  # 最小相关度
    time_decay_factor: float = 0.1  # 时间衰减因子
    
    # 不同类型记忆的权重
    type_weights: Dict[str, float] = None

    def __post_init__(self):
        if self.type_weights is None:
            self.type_weights = {
                "working": 1.0,  # 工作记忆权重
                "episodic": 0.8,  # 情节记忆权重
                "semantic": 0.6   # 语义记忆权重
            }

@dataclass
class SearchResult:
    """检索结果"""
    memory: Memory  # 记忆内容
    relevance_score: float  # 相关度分数
    reason: str  # 相关原因
    usage_suggestion: str  # 使用建议

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory": self.memory.to_dict(),
            "relevance_score": self.relevance_score,
            "reason": self.reason,
            "usage_suggestion": self.usage_suggestion
        }

class MemorySearcher:
    """记忆检索器"""
    
    def __init__(
        self,
        memory_store: MemoryStore,
        llm_service: LLMService,
        emotion_processor: EmotionProcessor,
        concept_processor: ConceptProcessor,
        config: Optional[SearchConfig] = None
    ):
        self.memory_store = memory_store
        self.llm_service = llm_service
        self.emotion_processor = emotion_processor
        self.concept_processor = concept_processor
        self.config = config or SearchConfig()
    
    def search(
        self,
        query: str,
        context: Dict[str, Any],
        memory_type: Optional[str] = None
    ) -> List[SearchResult]:
        """搜索相关记忆"""
        try:
            memory_logger.info(f"开始记忆检索，查询：{query}")
            memory_logger.debug(f"检索上下文：{json.dumps(context, ensure_ascii=False)}")
            memory_logger.debug(f"记忆类型过滤：{memory_type}")
            
            # 第一层：基础快照匹配
            base_snapshots = self.memory_store.get_base_snapshots()
            memory_logger.info(f"获取到 {len(base_snapshots)} 个基础快照")
            
            if not base_snapshots:
                memory_logger.info("没有可用的基础快照，直接搜索所有记忆")
                return self._search_all_memories(query, context, memory_type)
            
            # 评估基础快照相关性
            relevant_base = self._evaluate_base_snapshots(
                query,
                context,
                base_snapshots
            )
            memory_logger.info(f"找到 {len(relevant_base)} 个相关的基础快照")
            
            if not relevant_base:
                memory_logger.info("没有找到相关的基础快照，尝试搜索所有记忆")
                return self._search_all_memories(query, context, memory_type)
            
            # 第二层：详细快照匹配
            detail_snapshots = []
            for base in relevant_base:
                details = self.memory_store.get_detail_snapshots(base.snapshot_id)
                detail_snapshots.extend(details)
            memory_logger.info(f"从基础快照中获取到 {len(detail_snapshots)} 个详细快照")
            
            if not detail_snapshots:
                memory_logger.info("没有找到相关的详细快照，尝试搜索所有记忆")
                return self._search_all_memories(query, context, memory_type)
            
            # 评估详细快照相关性
            relevant_details = self._evaluate_detail_snapshots(
                query,
                context,
                detail_snapshots
            )
            memory_logger.info(f"找到 {len(relevant_details)} 个相关的详细快照")
            
            if not relevant_details:
                memory_logger.info("没有找到相关的详细快照，尝试搜索所有记忆")
                return self._search_all_memories(query, context, memory_type)
            
            # 第三层：加载完整记忆
            memory_ids = []
            for detail in relevant_details:
                memory_ids.extend(detail.memory_ids)
            memory_logger.debug(f"从详细快照中提取的记忆ID：{memory_ids}")
            
            memories = self.memory_store.get_memories_by_ids(memory_ids)
            memory_logger.info(f"成功加载 {len(memories)} 条完整记忆")
            
            # 最终评估完整记忆的相关性
            results = self._evaluate_memories(
                query,
                context,
                memories
            )
            memory_logger.info(f"评估得到 {len(results)} 条相关记忆")
            
            if not results:
                memory_logger.info("没有找到相关的完整记忆")
                return []
            
            # 应用记忆类型过滤
            if memory_type:
                filtered_results = [r for r in results if r.memory.context.get("type") == memory_type]
                memory_logger.info(f"应用记忆类型过滤后剩余 {len(filtered_results)} 条记忆")
                results = filtered_results
            
            # 按相关度排序并返回结果
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            final_results = results[:self.config.max_results]
            
            memory_logger.info(f"检索完成，返回结果数：{len(final_results)}")
            memory_logger.debug(f"最终结果相关度分数：{[r.relevance_score for r in final_results]}")
            return final_results
            
        except Exception as e:
            memory_logger.error(f"记忆检索失败: {str(e)}", exc_info=True)
            return []
    
    def _search_all_memories(
        self,
        query: str,
        context: Dict[str, Any],
        memory_type: Optional[str] = None
    ) -> List[SearchResult]:
        """在所有记忆中搜索（兜底方案）"""
        try:
            memory_logger.info("开始全量记忆搜索")
            memories = self.memory_store.list()
            memory_logger.info(f"获取到 {len(memories)} 条记忆")
            
            if memory_type:
                filtered_memories = [m for m in memories if m.context.get("type") == memory_type]
                memory_logger.info(f"应用记忆类型过滤后剩余 {len(filtered_memories)} 条记忆")
                memories = filtered_memories
            
            if not memories:
                memory_logger.info("没有可用的记忆")
                return []
            
            results = self._evaluate_memories(query, context, memories)
            memory_logger.info(f"评估得到 {len(results)} 条相关记忆")
            return results
            
        except Exception as e:
            memory_logger.error(f"全量记忆搜索失败: {str(e)}", exc_info=True)
            return []
    
    def _evaluate_base_snapshots(
        self,
        query: str,
        context: Dict[str, Any],
        snapshots: List[BaseSnapshot]
    ) -> List[BaseSnapshot]:
        """评估基础快照的相关性"""
        try:
            memory_logger.info("开始评估基础快照相关性")
            
            # 分析查询意图
            emotion_result = self.emotion_processor.process({
                "text": query,
                "context": context
            })
            memory_logger.debug(f"情感分析结果：{json.dumps(emotion_result.__dict__, ensure_ascii=False)}")
            
            concept_result = self.concept_processor.process({
                "text": query,
                "context": context
            })
            memory_logger.debug(f"概念分析结果：{json.dumps(concept_result.__dict__, ensure_ascii=False)}")
            
            # 构建评估提示词
            prompt = self._build_base_evaluation_prompt(
                query,
                context,
                emotion_result.emotions if emotion_result.success else [],
                concept_result.concepts if concept_result.success else [],
                [s.to_dict() for s in snapshots]
            )
            memory_logger.debug(f"基础快照评估提示词：{prompt}")
            
            # 调用LLM评估相关性
            result = self.llm_service.generate_json(prompt)
            memory_logger.debug(f"LLM评估结果：{json.dumps(result, ensure_ascii=False)}")
            
            if not result or "relevant_categories" not in result:
                memory_logger.warning("LLM返回的结果格式不正确")
                return []
            
            # 返回相关的基础快照
            relevant_ids = [c["snapshot_id"] for c in result["relevant_categories"]]
            relevant_snapshots = [s for s in snapshots if s.snapshot_id in relevant_ids]
            memory_logger.info(f"找到 {len(relevant_snapshots)} 个相关的基础快照")
            return relevant_snapshots
            
        except Exception as e:
            memory_logger.error(f"基础快照评估失败: {str(e)}", exc_info=True)
            return []
    
    def _evaluate_detail_snapshots(
        self,
        query: str,
        context: Dict[str, Any],
        snapshots: List[DetailSnapshot]
    ) -> List[DetailSnapshot]:
        """评估详细快照的相关性"""
        try:
            memory_logger.info("开始评估详细快照相关性")
            
            # 分析查询的情感和概念
            emotion_result = self.emotion_processor.process({
                "text": query,
                "context": context
            })
            memory_logger.debug(f"情感分析结果：{json.dumps(emotion_result.__dict__, ensure_ascii=False)}")
            
            concept_result = self.concept_processor.process({
                "text": query,
                "context": context
            })
            memory_logger.debug(f"概念分析结果：{json.dumps(concept_result.__dict__, ensure_ascii=False)}")
            
            # 构建评估提示词
            prompt = self._build_detail_evaluation_prompt(
                query,
                context,
                emotion_result.emotions if emotion_result.success else [],
                concept_result.concepts if concept_result.success else [],
                [s.to_dict() for s in snapshots]
            )
            memory_logger.debug(f"详细快照评估提示词：{prompt}")
            
            # 调用LLM评估相关性
            result = self.llm_service.generate_json(prompt)
            memory_logger.debug(f"LLM评估结果：{json.dumps(result, ensure_ascii=False)}")
            
            if not result or "relevant_snapshots" not in result:
                memory_logger.warning("LLM返回的结果格式不正确")
                return []
            
            # 返回相关的详细快照
            relevant_ids = [s["snapshot_id"] for s in result["relevant_snapshots"]
                          if s["relevance_score"] >= self.config.min_relevance]
            relevant_snapshots = [s for s in snapshots if s.snapshot_id in relevant_ids]
            memory_logger.info(f"找到 {len(relevant_snapshots)} 个相关的详细快照")
            memory_logger.debug(f"相关快照ID：{relevant_ids}")
            return relevant_snapshots
            
        except Exception as e:
            memory_logger.error(f"详细快照评估失败: {str(e)}", exc_info=True)
            return []
    
    def _evaluate_memories(
        self,
        query: str,
        context: Dict[str, Any],
        memories: List[Memory]
    ) -> List[SearchResult]:
        """评估记忆的相关性"""
        try:
            memory_logger.info("开始评估记忆相关性")
            
            if not memories:
                memory_logger.info("没有可用的记忆进行评估")
                return []
            
            # 分析查询的情感和概念
            emotion_result = self.emotion_processor.process({
                "text": query,
                "context": context
            })
            memory_logger.debug(f"情感分析结果：{json.dumps(emotion_result.__dict__, ensure_ascii=False)}")
            
            concept_result = self.concept_processor.process({
                "text": query,
                "context": context
            })
            memory_logger.debug(f"概念分析结果：{json.dumps(concept_result.__dict__, ensure_ascii=False)}")
            
            # 构建评估提示词
            prompt = self._build_retrieval_prompt(
                query,
                context,
                emotion_result.emotions if emotion_result.success else [],
                concept_result.concepts if concept_result.success else [],
                [m.to_dict() for m in memories]
            )
            memory_logger.debug(f"记忆评估提示词：{prompt}")
            
            # 调用LLM评估相关性
            result = self.llm_service.generate_json(prompt)
            memory_logger.debug(f"LLM评估结果：{json.dumps(result, ensure_ascii=False)}")
            
            if not result:
                memory_logger.warning("LLM返回空结果")
                return []
                
            if not isinstance(result, dict):
                memory_logger.warning(f"LLM返回的结果不是字典类型: {type(result)}")
                return []
                
            if "relevant_memories" not in result:
                memory_logger.warning("LLM返回的结果中缺少relevant_memories字段")
                return []
                
            if not isinstance(result["relevant_memories"], list):
                memory_logger.warning(f"relevant_memories不是列表类型: {type(result['relevant_memories'])}")
                return []
            
            # 解析结果
            relevant_memories = []
            for memory_result in result["relevant_memories"]:
                try:
                    if not isinstance(memory_result, dict):
                        memory_logger.warning(f"记忆结果不是字典类型: {type(memory_result)}")
                        continue
                        
                    memory_id = memory_result.get("memory_id")
                    if not memory_id:
                        memory_logger.warning(f"记忆结果缺少memory_id: {json.dumps(memory_result, ensure_ascii=False)}")
                        continue
                        
                    memory = next((m for m in memories if m.memory_id == memory_id), None)
                    if not memory:
                        memory_logger.warning(f"未找到ID为{memory_id}的记忆")
                        continue
                        
                    # 确保相关度分数是有效的浮点数
                    try:
                        relevance_score = float(memory_result.get("relevance_score", 0.0))
                        if not (0 <= relevance_score <= 1):
                            memory_logger.warning(f"相关度分数{relevance_score}超出范围[0,1]，将使用默认值0.0")
                            relevance_score = 0.0
                    except (TypeError, ValueError):
                        memory_logger.warning(f"无效的相关度分数: {memory_result.get('relevance_score')}，将使用默认值0.0")
                        relevance_score = 0.0
                    
                    if relevance_score < self.config.min_relevance:
                        memory_logger.debug(f"记忆{memory_id}的相关度{relevance_score}低于阈值{self.config.min_relevance}")
                        continue
                        
                    relevant_memories.append(SearchResult(
                        memory=memory,
                        relevance_score=relevance_score,
                        reason=str(memory_result.get("reason", "未提供原因")),
                        usage_suggestion=str(memory_result.get("usage_suggestion", "未提供使用建议"))
                    ))
                    memory_logger.debug(f"记忆{memory_id}的相关度评分：{relevance_score}")
                except Exception as e:
                    memory_logger.error(f"处理记忆结果时出错: {str(e)}")
                    continue
            
            memory_logger.info(f"评估完成，找到 {len(relevant_memories)} 条相关记忆")
            return relevant_memories
            
        except Exception as e:
            memory_logger.error(f"相关度评估失败: {str(e)}", exc_info=True)
            return []
    
    def _build_base_evaluation_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        emotions: List[Dict],
        concepts: List[Dict],
        snapshots: List[Dict]
    ) -> str:
        """构建基础快照评估提示词"""
        requirements = {
            "query": query,
            "emotions": emotions,
            "concepts": concepts,
            "snapshots": snapshots,
            "context": context
        }
        
        return BASE_SNAPSHOT_TEMPLATE.format(
            requirements=json.dumps(requirements, ensure_ascii=False)
        )
        
    def _build_detail_evaluation_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        emotions: List[Dict],
        concepts: List[Dict],
        snapshots: List[Dict]
    ) -> str:
        """构建详细快照评估提示词"""
        requirements = {
            "query": query,
            "emotions": emotions,
            "concepts": concepts,
            "snapshots": snapshots,
            "context": context,
            "min_relevance": self.config.min_relevance
        }
        
        return DETAIL_SNAPSHOT_TEMPLATE.format(
            requirements=json.dumps(requirements, ensure_ascii=False)
        )

    def _apply_weight(
        self,
        results: List[SearchResult],
        memory_type: str
    ) -> List[SearchResult]:
        """应用记忆类型权重"""
        weight = self.config.type_weights.get(memory_type, 1.0)
        for result in results:
            result.relevance_score *= weight
        return results

    def _build_retrieval_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        emotions: List[Dict],
        concepts: List[Dict],
        memories: List[Dict]
    ) -> str:
        """构建检索评估提示词"""
        # 构建检索要求
        requirements = {
            "min_relevance": self.config.min_relevance,
            "max_results": self.config.max_results,
            "consider_emotions": len(emotions) > 0,
            "consider_concepts": len(concepts) > 0,
            "emotions": emotions,
            "concepts": concepts,
            "memories": memories
        }
        
        # 构建对话历史
        history = context.get("history", [])
        
        # 使用模板生成提示词
        return MEMORY_RETRIEVAL_TEMPLATE.format(
            input=query,
            history=json.dumps(history, ensure_ascii=False),
            requirements=json.dumps(requirements, ensure_ascii=False)
        ) 