"""
重要性处理器实现
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from .base import Processor, ProcessorConfig, ProcessorResult, ProcessorException
from ..memory.base import Memory
from services.llm_service import LLMService
from prompts.memory_prompts import MEMORY_IMPORTANCE_TEMPLATE

@dataclass
class ImportanceProcessorConfig(ProcessorConfig):
    """重要性处理器配置"""
    weights: Dict[str, float] = None  # 各维度权重
    min_score: float = 0.1  # 最小分数
    max_score: float = 1.0  # 最大分数

    def __post_init__(self):
        if self.weights is None:
            self.weights = {
                "emotion": 0.4,  # 情感权重
                "concept": 0.3,  # 概念权重
                "time": 0.3  # 时间权重
            }

@dataclass
class Dimension:
    """评估维度"""
    name: str
    score: float
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "reasoning": self.reasoning
        }

@dataclass
class ImportanceEvaluationResult(ProcessorResult):
    """重要性评估结果"""
    importance_score: Optional[float] = None
    dimensions: Optional[List[Dimension]] = None
    retention_suggestion: Optional[str] = None

class ImportanceProcessor(Processor):
    """重要性处理器"""
    
    def __init__(self, config: ImportanceProcessorConfig, llm_service: LLMService):
        super().__init__(config)
        self.llm_service = llm_service
        self.config: ImportanceProcessorConfig = config

    def process(self, input_data: Dict[str, Any]) -> ImportanceEvaluationResult:
        """
        评估内容的重要性
        
        Args:
            input_data: 包含内容和上下文的字典
                {
                    "content": str,  # 待评估内容
                    "context": Dict[str, Any],  # 上下文信息
                    "emotions": List[Dict],  # 情感分析结果
                    "concepts": List[Dict]  # 概念分析结果
                }
        """
        try:
            if not self.validate_input(input_data):
                return ImportanceEvaluationResult(
                    success=False,
                    error_message="输入数据验证失败"
                )

            # 调用LLM评估重要性
            evaluation_result = self._evaluate_importance(
                input_data["content"],
                input_data.get("context", {}),
                input_data.get("emotions", []),
                input_data.get("concepts", [])
            )

            if not evaluation_result:
                return ImportanceEvaluationResult(
                    success=False,
                    error_message="重要性评估失败"
                )

            # 处理评估结果
            dimensions = self._process_dimensions(evaluation_result)
            
            # 计算综合重要性分数
            importance_score = self._calculate_importance_score(dimensions)
            
            # 生成保留建议
            retention_suggestion = self._generate_retention_suggestion(
                importance_score,
                dimensions
            )

            return ImportanceEvaluationResult(
                success=True,
                importance_score=importance_score,
                dimensions=dimensions,
                retention_suggestion=retention_suggestion,
                data=evaluation_result
            )

        except Exception as e:
            return ImportanceEvaluationResult(
                success=False,
                error_message=f"重要性处理异常: {str(e)}"
            )

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        if not isinstance(input_data, dict):
            return False
        
        if "content" not in input_data:
            return False
        
        if not isinstance(input_data["content"], str):
            return False
        
        if not input_data["content"].strip():
            return False
        
        return True

    def _evaluate_importance(
        self,
        content: str,
        context: Dict[str, Any],
        emotions: List[Dict],
        concepts: List[Dict]
    ) -> Dict[str, Any]:
        """调用LLM评估重要性"""
        try:
            # 构建提示词
            prompt = self._build_importance_prompt(
                content,
                context,
                emotions,
                concepts
            )
            
            # 调用LLM服务
            response = self.llm_service.generate_json(prompt)
            
            return response
            
        except Exception as e:
            raise ProcessorException(f"重要性评估失败: {str(e)}")

    def _process_dimensions(self, evaluation_result: Dict[str, Any]) -> List[Dimension]:
        """处理评估结果，返回维度列表"""
        dimensions = []
        
        if "dimensions" in evaluation_result:
            for name, data in evaluation_result["dimensions"].items():
                if isinstance(data, dict):
                    score = data.get("score", 0.0)
                    reasoning = data.get("reasoning", "")
                else:
                    score = float(data)
                    reasoning = ""
                
                dimension = Dimension(
                    name=name,
                    score=self._normalize_score(score),
                    reasoning=reasoning
                )
                dimensions.append(dimension)
        
        return dimensions

    def _calculate_importance_score(self, dimensions: List[Dimension]) -> float:
        """计算综合重要性分数"""
        if not dimensions:
            return self.config.min_score
        
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for dimension in dimensions:
            weight = self.config.weights.get(dimension.name.lower(), 1.0)
            weighted_sum += dimension.score * weight
            weight_sum += weight
        
        if weight_sum == 0:
            return self.config.min_score
        
        score = weighted_sum / weight_sum
        return self._normalize_score(score)

    def _normalize_score(self, score: float) -> float:
        """归一化分数到配置的范围"""
        return max(
            self.config.min_score,
            min(self.config.max_score, score)
        )

    def _generate_retention_suggestion(
        self,
        importance_score: float,
        dimensions: List[Dimension]
    ) -> str:
        """生成保留建议"""
        if importance_score >= 0.8:
            return "应当长期保存在情节记忆中，并建立概念关联"
        elif importance_score >= 0.6:
            return "保存在情节记忆中，定期评估重要性"
        elif importance_score >= 0.4:
            return "暂时保存在工作记忆中，等待进一步观察"
        else:
            return "可以仅在工作记忆中短期保存"

    def _build_importance_prompt(
        self,
        content: str,
        context: Dict[str, Any],
        emotions: List[Dict],
        concepts: List[Dict]
    ) -> str:
        """构建重要性评估提示词"""
        # 构建评估上下文
        evaluation_context = {
            "content": content,
            "emotions": emotions,
            "concepts": concepts,
            **context
        }
        
        return MEMORY_IMPORTANCE_TEMPLATE.format(
            content=content,
            context=json.dumps(evaluation_context, ensure_ascii=False),
            current_time=datetime.now().isoformat()
        )