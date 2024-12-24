"""
情感处理器实现
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

from ..memory.base import Memory, Emotion
from services.llm_service import LLMService
from prompts.emotion_prompts import EMOTION_ANALYSIS_TEMPLATE

@dataclass
class EmotionProcessorConfig:
    """情感处理器配置"""
    min_confidence: float = 0.6
    max_emotions: int = 3
    emotion_types: List[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmotionProcessorConfig':
        return cls(
            min_confidence=data.get("min_confidence", 0.6),
            max_emotions=data.get("max_emotions", 3),
            emotion_types=data.get("emotion_types", [])
        )

class EmotionProcessor:
    """情感处理器"""
    
    def __init__(self, config: EmotionProcessorConfig, llm_service: LLMService):
        self.config = config
        self.llm_service = llm_service
    
    def analyze(self, text: str, context: Optional[List[Memory]] = None) -> List[Emotion]:
        """分析文本情感"""
        try:
            # 准备上下文
            context_str = ""
            if context:
                context_str = "\n".join([
                    f"- {mem.content} (情感: {', '.join([e.name for e in mem.emotions])})"
                    for mem in context[-3:]  # 只使用最近的3条记忆
                ])
            
            # 构建提示词
            prompt = EMOTION_ANALYSIS_TEMPLATE.format(
                text=text,
                context=context_str,
                emotion_types=", ".join(self.config.emotion_types)
            )
            
            # 调用LLM进行情感分析
            response = self.llm_service.generate_json(prompt)
            
            # 解析响应
            emotions = []
            for emotion_data in response.get("emotions", []):
                if emotion_data.get("confidence", 0) >= self.config.min_confidence:
                    emotions.append(Emotion(
                        name=emotion_data["name"],
                        intensity=emotion_data["intensity"],
                        confidence=emotion_data["confidence"]
                    ))
            
            # 按置信度排序并限制数量
            emotions.sort(key=lambda e: e.confidence, reverse=True)
            return emotions[:self.config.max_emotions]
            
        except Exception as e:
            print(f"情感分析失败: {str(e)}")
            return []
    
    def track_changes(self, current: List[Emotion], previous: List[Emotion]) -> Dict[str, Any]:
        """跟踪情感变化"""
        try:
            changes = {
                "added": [],
                "removed": [],
                "intensified": [],
                "weakened": []
            }
            
            # 创建情感映射
            current_map = {e.name: e for e in current}
            previous_map = {e.name: e for e in previous}
            
            # 检查新增和强度变化的情感
            for name, emotion in current_map.items():
                if name not in previous_map:
                    changes["added"].append(emotion)
                else:
                    prev_intensity = previous_map[name].intensity
                    if emotion.intensity > prev_intensity:
                        changes["intensified"].append(emotion)
                    elif emotion.intensity < prev_intensity:
                        changes["weakened"].append(emotion)
            
            # 检查移除的情感
            for name, emotion in previous_map.items():
                if name not in current_map:
                    changes["removed"].append(emotion)
            
            return changes
            
        except Exception as e:
            print(f"跟踪情感变化失败: {str(e)}")
            return {
                "added": [],
                "removed": [],
                "intensified": [],
                "weakened": []
            }
    
    def process(self, data):
        """处理输入数据，提取情感信息"""
        try:
            text = data.get('text', '')
            context = data.get('context', {})
            
            # 调用LLM进行情感分析
            result = self.llm_service.analyze_emotion(text, context)
            
            # 解析结果
            emotions = []
            primary_emotion = None
            if result and 'emotions' in result:
                for emotion_data in result['emotions']:
                    emotion = Emotion(
                        type=emotion_data.get('type', ''),
                        intensity=float(emotion_data.get('intensity', 0.0))
                    )
                    emotions.append(emotion)
                
                if emotions:
                    # 选择强度最高的情感作为主要情感
                    primary_emotion = max(emotions, key=lambda x: x.intensity)
            
            return EmotionResult(
                success=True,
                emotions=emotions,
                primary_emotion=primary_emotion
            )
            
        except Exception as e:
            return EmotionResult(
                success=False,
                error=str(e)
            )

class EmotionResult:
    def __init__(self, success, emotions=None, primary_emotion=None, error=None):
        self.success = success
        self.emotions = emotions or []
        self.primary_emotion = primary_emotion
        self.error = error
        
    def to_dict(self):
        return {
            'success': self.success,
            'emotions': [e.to_dict() for e in self.emotions],
            'primary_emotion': self.primary_emotion.to_dict() if self.primary_emotion else None,
            'error': self.error
        }

class Emotion:
    def __init__(self, type, intensity, valence=0):
        self.type = type
        self.intensity = intensity
        self.valence = valence
        
    def to_dict(self):
        return {
            'type': self.type,
            'intensity': self.intensity,
            'valence': self.valence
        } 