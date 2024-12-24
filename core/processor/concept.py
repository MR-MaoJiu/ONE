"""
概念提取器实现
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

from ..memory.base import Memory
from services.llm_service import LLMService
from prompts.memory_prompts import CONCEPT_EXTRACTION_TEMPLATE

@dataclass
class ConceptProcessorConfig:
    """概念提取器配置"""
    max_concepts: int = 10
    min_relevance: float = 0.5
    concept_types: List[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConceptProcessorConfig':
        return cls(
            max_concepts=data.get("max_concepts", 10),
            min_relevance=data.get("min_relevance", 0.5),
            concept_types=data.get("concept_types", [])
        )

class ConceptProcessor:
    """概念提取器"""
    
    def __init__(self, config: ConceptProcessorConfig, llm_service: LLMService):
        self.config = config
        self.llm_service = llm_service
    
    def process(self, data):
        """处理输入数据，提取概念信息"""
        try:
            text = data.get('text', '')
            context = data.get('context', {})
            
            # 调用LLM进行概念提取
            result = self.llm_service.analyze_concepts(text, context)
            
            # 解析结果
            concepts = []
            if result and 'concepts' in result:
                for concept_data in result['concepts']:
                    if concept_data.get('importance', 0.0) >= self.config.min_relevance:
                        concept = Concept(
                            name=concept_data.get('name', ''),
                            category=concept_data.get('type', ''),  # 使用type作为category
                            importance=float(concept_data.get('importance', 0.0)),
                            relations=concept_data.get('relations', [])
                        )
                        concepts.append(concept)
                
                # 按重要性排序
                concepts.sort(key=lambda x: x.importance, reverse=True)
                
                # 限制返回的概念数量
                concepts = concepts[:self.config.max_concepts]
            
            return ConceptResult(
                success=True,
                concepts=concepts
            )
            
        except Exception as e:
            return ConceptResult(
                success=False,
                error=str(e)
            )
    
    def extract_concepts(self, text: str, context: Optional[List[Memory]] = None) -> List[Dict[str, Any]]:
        """提取概念"""
        try:
            # 准备上下文
            context_str = ""
            if context:
                context_str = "\n".join([
                    f"- {mem.content}"
                    for mem in context[-3:]  # 只使用最近的3条记忆
                ])
            
            # 构建提示词
            prompt = CONCEPT_EXTRACTION_TEMPLATE.format(
                text=text,
                context=context_str,
                concept_types=", ".join(self.config.concept_types)
            )
            
            # 调用LLM进行概念提取
            response = self.llm_service.generate_json(prompt)
            
            # 解析响应
            concepts = []
            for concept in response.get("concepts", []):
                if concept.get("relevance", 0) >= self.config.min_relevance:
                    concepts.append({
                        "type": concept["type"],
                        "name": concept["name"],
                        "relevance": concept["relevance"],
                        "attributes": concept.get("attributes", {})
                    })
            
            # 按相关度排序并限制数量
            concepts.sort(key=lambda c: c["relevance"], reverse=True)
            return concepts[:self.config.max_concepts]
            
        except Exception as e:
            print(f"概念提取失败: {str(e)}")
            return []
    
    def merge_concepts(self, concepts1: List[Dict[str, Any]], concepts2: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并概念列表"""
        try:
            # 创建概念映射
            concept_map = {}
            
            # 处理第一个概念列表
            for concept in concepts1:
                key = (concept["type"], concept["name"])
                concept_map[key] = concept.copy()
            
            # 处理第二个概念列表
            for concept in concepts2:
                key = (concept["type"], concept["name"])
                if key in concept_map:
                    # 更新现有概念
                    existing = concept_map[key]
                    existing["relevance"] = max(existing["relevance"], concept["relevance"])
                    existing["attributes"].update(concept.get("attributes", {}))
                else:
                    # 添加新概念
                    concept_map[key] = concept.copy()
            
            # 转换回列表并排序
            merged = list(concept_map.values())
            merged.sort(key=lambda c: c["relevance"], reverse=True)
            
            return merged[:self.config.max_concepts]
            
        except Exception as e:
            print(f"合并概念失败: {str(e)}")
            return []

class ConceptResult:
    def __init__(self, success, concepts=None, error=None):
        self.success = success
        self.concepts = concepts or []
        self.error = error
        
    def to_dict(self):
        return {
            'success': self.success,
            'concepts': [c.to_dict() for c in self.concepts],
            'error': self.error
        }

class Concept:
    def __init__(self, name, category='', importance=0.0, relations=None):
        self.name = name
        self.category = category
        self.importance = importance
        self.relations = relations or []
        
    def to_dict(self):
        return {
            'name': self.name,
            'category': self.category,
            'importance': self.importance,
            'relations': self.relations
        } 