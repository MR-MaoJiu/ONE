"""
记忆检索相关的提示词
"""

def get_memory_retrieval_prompt(query: str, memory_data: str) -> str:
    """
    获取记忆检索的提示词
    
    Args:
        query: 当前查询
        memory_data: 记忆数据的JSON字符串
        
    Returns:
        str: 完整的提示词
    """
    return f"""你是一个记忆检索助手。请根据以下记忆和当前查询，评估它们的相关度。

当前查询：{query}

记忆列表：
{memory_data}

请评估每条记忆与当前查询的相关程度，考虑以下因素：
1. 内容相关性：记忆内容是否与查询主题相关
2. 时间相关性：记忆的时间是否与查询相关
3. 上下文匹配：记忆的上下文是否与当前查询场景匹配

你必须严格按照以下JSON格式返回结果。以下是一些示例：

示例1（有相关记忆）：
{{
    "relevant_memories": [
        {{
            "memory_id": "memory_123",
            "relevance_score": 0.9,
            "reason": "这条记忆提到用户把手机放在了客厅桌子上充电，与当前查询直接相关"
        }},
        {{
            "memory_id": "memory_456",
            "relevance_score": 0.7,
            "reason": "这条记忆提到用户在找手机，虽然没有具体位置但上下文相关"
        }}
    ]
}}

示例2（没有相关记忆）：
{{
    "relevant_memories": []
}}

要求：
1. 必须返回一个包含 relevant_memories 数组的 JSON
2. relevant_memories 数组可以为空，但必须存在这个字段
3. memory_id 必须来自记忆列表中的 id 字段
4. relevance_score 必须是 0-1 之间的浮点数
5. 只返回相关度大于 0.5 的记忆
6. 按相关度从高到低排序
7. reason 字段必须用中文解释为什么这条记忆与查询相关

请确保返回的JSON格式完全符合上述要求：
1. 不要添加任何额外的字段
2. 不要添加任何注释
3. 不要返回任何其他内容
4. 如果没有相关记忆，返回空数组：{{"relevant_memories": []}}
5. 每个记忆对象必须包含且仅包含 memory_id、relevance_score 和 reason 三个字段

现在请分析记忆列表，找出与当前查询相关的记忆，并按照上述格式返回结果。

注意：你的回复必须是一个有效的JSON字符串，不要包含任何其他内容。
不要返回 query、relevance、explanation 或其他任何额外字段。
只返回包含 relevant_memories 数组的对象。
不要在JSON中添加任何注释或说明。
不要在JSON前后添加任何文字。
不要使用 ```json 或 ``` 标记。
直接返回JSON字符串。

错误示例1（不要这样做）：
{{
    "query": "我手机在哪",
    "relevance_score": 0.8,
    "explanation": "这是一个解释"
}}

错误示例2（不要这样做）：
```json
{{
    "relevant_memories": []
}}
```

错误示例3（不要这样做）：
以下是我的回复：
{{
    "relevant_memories": []
}}

错误示例4（不要这样做）：
{{
    "relevant_memories": [
        {{
            "id": "memory_123",
            "content": "记忆内容",
            "timestamp": "2024-12-24T14:46:06.522063"
        }}
    ]
}}

正确示例：
{{
    "relevant_memories": [
        {{
            "memory_id": "memory_123",
            "relevance_score": 0.9,
            "reason": "这条记忆提到用户把手机放在了客厅桌子上充电，与当前查询直接相关"
        }}
    ]
}}

记住：
1. memory_id 字段必须使用记忆列表中的 id 字段值
2. 不要返回记忆的内容和时间戳
3. 不要修改字段名称（比如把 memory_id 改成 id）
4. 不要添加额外的字段
5. 不要在JSON前后添加任何文字或标记""" 