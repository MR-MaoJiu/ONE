"""
情感分析相关提示词模板
"""

EMOTION_ANALYSIS_JSON_TEMPLATE = """
请分析以下文本的情感，返回JSON格式的结果:
文本: {text}
{context_str}
请返回以下格式的JSON:
{
    "emotions": [
        {
            "type": "情感类型",
            "intensity": "情感强度(0-1之间的浮点数)"
        }
    ],
    "primary_emotion": {
        "type": "主要情感类型",
        "intensity": "主要情感强度(0-1之间的浮点数)"
    }
}

情感类型可以是: 喜悦、悲伤、愤怒、恐惧、惊讶、期待、信任、厌恶等。

注意：
1. 输出必须是有效的 JSON 格式
2. emotions 是一个数组，可以为空 []
3. intensity 必须是 0 到 1 之间的浮点数
4. type 必须是指定的情感类型之一
5. 所有字段都必须存在且不能为 null
"""

EMOTION_ANALYSIS_TEMPLATE = """
请分析以下文本的情感特征：
文本：{text}

请从以下维度分析：
1. 主要情感类型（如：快乐、悲伤、愤怒等）
2. 情感强度（0-1）
3. 情感倾向（积极/消极）
4. 是否包含多种情感
5. 情感变化趋势

输出格式：
{
    "primary_emotion": {
        "type": "joy",
        "intensity": 0.8
    },
    "secondary_emotions": [
        {
            "type": "excitement",
            "intensity": 0.6
        }
    ],
    "sentiment": "positive",
    "complexity": "multiple",
    "trend": "stable"
}
"""

EMOTION_TRACKING_TEMPLATE = """
基于历史情感记录，分析用户的情感变化：
历史记录：{history}
当前情感：{current}

请分析：
1. 情感变化趋势
2. 情感波动程度
3. 潜在的情感触发因素
4. 是否需要特别关注

输出格式：
{
    "trend": "improving/stable/declining",
    "volatility": 0.4,
    "triggers": ["工作压力", "人际关系"],
    "needs_attention": false,
    "suggestion": "用户情绪稳定，保持当前的交互方式"
}
"""

EMOTION_RESPONSE_TEMPLATE = """
根据用户的情感状态，生成合适的回应：
用户情感：{emotion}
对话历史：{history}
当前话题：{topic}

回应要求：
1. 表达共情和理解
2. 提供适当的支持
3. 保持对话的自然流畅
4. 适当引用相关的历史对话

注意：
- 如果用户情绪消极，提供积极的支持
- 如果用户情绪积极，表达真诚的祝贺
- 避免过度夸张或轻描淡写
""" 