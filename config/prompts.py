"""
提示词配置模块
"""

MEMORY_PROMPTS = {
    'needs_memory': """请判断以下问题是否需要查询历史记忆来回答（只需返回JSON格式的true或false）：

问题："{query}"

判断标准：
1. 如果问题涉及到"还记得"、"之前"、"刚才"等词，需要记忆
2. 如果问题询问过去发生的事情，需要记忆
3. 如果问题是在寻找之前提到过的东西，需要记忆
4. 如果是普通的问候、闲聊或独立的问题，不需要记忆

请返回：
{{"needs_memory": true或false}}""",

    'summarize': """请总结以下内容的关键信息，并返回JSON格式：
{content}

请返回以下格式：
{{
    "summary": "一句话总结",
    "key_points": ["要点1", "要点2", ...]
}}""",

    'evaluate_relevance': """请评估以下内容与查询"{query}"的相关度（0-1分）：
            
{contents}

请返回一个JSON对象，包含每条内容的相关度分数，格式如下：
{{
    "scores": [0.8, 0.2, 0.5, ...]
}}"""
} 