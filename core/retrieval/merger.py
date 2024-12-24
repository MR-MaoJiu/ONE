"""
记忆合并器实现
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

from ..memory.base import Memory
from ..processor.emotion import EmotionProcessor
from .searcher import SearchResult
from services.llm_service import LLMService
from prompts.memory_prompts import MEMORY_CONSOLIDATION_TEMPLATE
from utils.logger import llm_logger

@dataclass
class MergerConfig:
    """合并器配置"""
    max_memories_per_response: int = 5  # 每次响应最多使用的记忆数量
    min_coherence_score: float = 0.7  # 最小连贯性分数
    emotion_weight: float = 0.3  # 情感连贯性权重
    content_weight: float = 0.7  # 内容连贯性权重

@dataclass
class MergeResult:
    """合并结果"""
    response: str  # 生成的回复
    used_memories: List[Memory]  # 使用的记忆
    coherence_score: float  # 连贯性分数
    emotional_state: Dict[str, Any]  # 情感状态

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "used_memories": [m.to_dict() for m in self.used_memories],
            "coherence_score": self.coherence_score,
            "emotional_state": self.emotional_state
        }

class MemoryMerger:
    """记忆合并器"""
    
    def __init__(
        self,
        config: MergerConfig,
        emotion_processor: EmotionProcessor,
        llm_service: LLMService
    ):
        """
        初始化记忆合并器
        
        Args:
            config: 合并器配置
            emotion_processor: 情感处理器
            llm_service: LLM服务
        """
        self.config = config
        self.emotion_processor = emotion_processor
        self.llm_service = llm_service
        llm_logger.info("初始化记忆合并器，检查 LLM 服务类型: %s", type(llm_service).__name__)

    def merge(
        self,
        query: str,
        context: Dict[str, Any],
        search_results: List[SearchResult]
    ) -> MergeResult:
        """
        合并记忆生成回复
        
        Args:
            query: 用户输入
            context: 对话上下文
            search_results: 检索结果列表
            
        Returns:
            合并结果
        """
        try:
            # 分析用户输入的情感
            current_emotion = self._analyze_emotion(query, context)
            
            # 如果没有检索到记忆，直接生成回复
            if not search_results:
                llm_logger.info("没有找到相关记忆，直接生成回复")
                response = self.llm_service.generate(
                    f"请根据以下对话历史和用户输入生成合适的回复。\n\n对话历史：\n" + 
                    "\n".join([f"{'用户' if msg['type'] == 'user' else 'AI'}: {msg['content']}" 
                             for msg in context.get('history', [])]) +
                    f"\n\n用户输入：{query}\n\n请生成回复："
                )
                if not response:
                    response = "你好！很高兴见到你。"
                return MergeResult(
                    response=response,
                    used_memories=[],
                    coherence_score=1.0,
                    emotional_state={
                        "current": current_emotion,
                        "response": {"type": "neutral", "intensity": 0.5}
                    }
                )
            
            # 选择要使用的记忆
            selected_memories = self._select_memories(
                search_results,
                current_emotion
            )
            
            # 生成回复
            response_result = self._generate_response(
                query, 
                context,
                selected_memories,
                current_emotion
            )
            
            if not response_result:
                return MergeResult(
                    response="我需要一点时间来整理这些信息。",
                    used_memories=[r.memory for r in selected_memories],
                    coherence_score=0.5,
                    emotional_state={
                        "current": current_emotion,
                        "response": {"type": "neutral", "intensity": 0.5}
                    }
                )
            
            # 评估连贯性
            coherence_score = self._evaluate_coherence(
                query,
                response_result["response"],
                selected_memories,
                current_emotion
            )
            
            # 如果连贯性不足，尝试重新生成
            attempts = 1
            while (coherence_score < self.config.min_coherence_score 
                   and attempts < 3):
                response_result = self._generate_response(
                    query,
                    context,
                    selected_memories,
                    current_emotion,
                    previous_attempt=response_result["response"]
                )
                coherence_score = self._evaluate_coherence(
                    query,
                    response_result["response"],
                    selected_memories,
                    current_emotion
                )
                attempts += 1
            
            return MergeResult(
                response=response_result["response"],
                used_memories=[r.memory for r in selected_memories],
                coherence_score=coherence_score,
                emotional_state={
                    "current": current_emotion,
                    "response": response_result.get("emotional_state", {})
                }
            )
            
        except Exception as e:
            llm_logger.error(f"记忆合并失败: {str(e)}")
            return MergeResult(
                response="我现在有点混乱，让我重新组织一下思路。",
                used_memories=[],
                coherence_score=0.5,
                emotional_state={
                    "current": {"type": "neutral", "intensity": 0.5},
                    "response": {"type": "neutral", "intensity": 0.5}
                }
            )

    def _analyze_emotion(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析情感状态"""
        result = self.emotion_processor.process({
            "text": text,
            "context": context
        })
        
        if result.success and result.primary_emotion:
            return result.primary_emotion.to_dict()
        return {}

    def _select_memories(
        self,
        search_results: List[SearchResult],
        current_emotion: Dict[str, Any]
    ) -> List[SearchResult]:
        """选择要使用的记忆"""
        # 按相关度排序
        sorted_results = sorted(
            search_results,
            key=lambda x: x.relevance_score,
            reverse=True
        )
        
        # 限制使用的记忆数量
        selected = sorted_results[:self.config.max_memories_per_response]
        
        # 根据情感连贯性进行过滤
        if current_emotion:
            selected = [
                r for r in selected
                if self._is_emotionally_coherent(
                    r.memory,
                    current_emotion
                )
            ]
        
        return selected

    def _is_emotionally_coherent(
        self,
        memory: Memory,
        current_emotion: Dict[str, Any]
    ) -> bool:
        """检查情感连贯性"""
        # 如果记忆没有情感标注，认为是中性的
        if not memory.emotions:
            return True
        
        # 如果当前没有明显情感，任何记忆都可以使用
        if not current_emotion:
            return True
            
        # 检查情感的相容性
        memory_emotion = memory.emotions[0]
        return self._are_emotions_compatible(
            current_emotion,
            memory_emotion.to_dict()
        )

    def _are_emotions_compatible(
        self,
        emotion1: Dict[str, Any],
        emotion2: Dict[str, Any]
    ) -> bool:
        """检查两种情感是否相容"""
        # 定义情感相容性规则
        compatibility_rules = {
            "joy": ["joy", "trust", "anticipation"],
            "trust": ["joy", "trust", "anticipation"],
            "anticipation": ["joy", "trust", "anticipation"],
            "surprise": ["joy", "surprise", "anticipation"],
            "sadness": ["sadness", "fear"],
            "fear": ["sadness", "fear"],
            "anger": ["anger", "disgust"],
            "disgust": ["anger", "disgust"],
            "neutral": ["joy", "trust", "anticipation", "surprise", 
                       "sadness", "fear", "anger", "disgust", "neutral"]
        }
        
        emotion1_type = emotion1.get("type", "neutral")
        emotion2_type = emotion2.get("type", "neutral")
        
        compatible_emotions = compatibility_rules.get(emotion1_type, [])
        return emotion2_type in compatible_emotions

    def _generate_response(
        self,
        query: str,
        context: Dict[str, Any],
        selected_memories: List[SearchResult],
        current_emotion: Dict[str, Any],
        previous_attempt: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """生成回复"""
        try:
            # 构建提示词
            prompt = self._build_consolidation_prompt(
                query,
                context,
                selected_memories,
                current_emotion,
                previous_attempt
            )
            
            # 调用LLM生成回复
            response = self.llm_service.generate_json(prompt)
            
            if not response or "response" not in response:
                return None
                
            return {
                "response": response["response"],
                "emotional_state": response.get("emotional_state", {})
            }
            
        except Exception as e:
            print(f"回复生成失败: {str(e)}")
            return None

    def _evaluate_coherence(
        self,
        query: str,
        response: str,
        used_memories: List[SearchResult],
        current_emotion: Dict[str, Any]
    ) -> float:
        """评估回复的连贯性"""
        # 评估内容连贯性
        content_coherence = self._evaluate_content_coherence(
            query,
            response,
            used_memories
        )
        
        # 评估情感连贯性
        emotional_coherence = self._evaluate_emotional_coherence(
            response,
            current_emotion
        )
        
        # 加权平均
        return (
            content_coherence * self.config.content_weight +
            emotional_coherence * self.config.emotion_weight
        )

    def _evaluate_content_coherence(
        self,
        query: str,
        response: str,
        used_memories: List[SearchResult]
    ) -> float:
        """评估内容连贯性"""
        try:
            # 构建评估提示词
            prompt = f"""
            评估回复的内容连贯性:
            用户输入: {query}
            生成回复: {response}
            使用的记忆: {json.dumps([m.memory.content for m in used_memories], ensure_ascii=False)}
            
            请评估:
            1. 回复是否自然地融入了记忆内容
            2. 回复是否与用户输入相关
            3. 记忆的使用是否合理
            
            输出格式:
            {{
                "coherence_score": 0.85,  # 0-1之间的分数
                "reasoning": "回复自然地融入了...",
            }}
            """
            
            result = self.llm_service.generate_json(prompt)
            return result.get("coherence_score", 0.5)
            
        except Exception as e:
            print(f"内容连贯性评估失败: {str(e)}")
            return 0.5

    def _evaluate_emotional_coherence(
        self,
        response: str,
        current_emotion: Dict[str, Any]
    ) -> float:
        """评估情感连贯性"""
        try:
            # 分析回复的情感
            response_emotion = self._analyze_emotion(response, {})
            
            # 如果没有明显情感，返回中等分数
            if not current_emotion or not response_emotion:
                return 0.7
            
            # 检查情感相容性
            if self._are_emotions_compatible(
                current_emotion,
                response_emotion
            ):
                # 根据情感强度的接近程度评分
                intensity_diff = abs(
                    current_emotion.get("intensity", 0.5) -
                    response_emotion.get("intensity", 0.5)
                )
                return 1.0 - intensity_diff
            
            return 0.3
            
        except Exception as e:
            print(f"情感连贯性评估失败: {str(e)}")
            return 0.5

    def _build_consolidation_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        selected_memories: List[SearchResult],
        current_emotion: Dict[str, Any],
        previous_attempt: Optional[str] = None
    ) -> str:
        """构建记忆合并提示词"""
        # 准备记忆数据
        memories_data = [
            {
                "content": r.memory.content,
                "relevance": r.relevance_score,
                "reason": r.reason,
                "usage": r.usage_suggestion
            }
            for r in selected_memories
        ]
        
        # 构建上下文
        consolidation_context = {
            "current_emotion": current_emotion,
            "history": context.get("history", []),
            "previous_attempt": previous_attempt
        }
        
        return MEMORY_CONSOLIDATION_TEMPLATE.format(
            memories=json.dumps(memories_data, ensure_ascii=False),
            context=json.dumps(consolidation_context, ensure_ascii=False),
            input=query
        )