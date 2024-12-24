"""
记忆处理相关提示词模板
"""

MEMORY_IMPORTANCE_TEMPLATE = """
评估内容的重要性：
内容：{content}
上下文：{context}
当前时间：{current_time}

评估维度：
1. 情感重要性
   - 情感强度：用户表达的情感有多强烈？
   - 情感影响：这种情感会持续多久？
   - 情感共鸣：我是否需要在未来对话中回应这种情感？

2. 事件重要性
   - 生活影响：这件事对用户的生活有多大影响？
   - 时间跨度：这是一次性事件还是持续性事件？
   - 后续发展：是否需要在未来跟进？

3. 关系重要性
   - 人际关联：涉及哪些重要的人际关系？
   - 社交影响：对用户的社交圈有何影响？
   - 关系发展：是否影响未来的关系发展？

输出格式：
{
    "importance_score": 0.85,
    "dimensions": {
        "emotional": 0.9,
        "event": 0.8,
        "relational": 0.85
    },
    "reasoning": "这是一个重要的职业发展节点...",
    "retention_suggestion": "应当长期保存在情节记忆中"
}
"""

CONCEPT_EXTRACTION_TEMPLATE = """
请分析以下文本，提取其中的主要概念。
{context_str}
文本内容：{text}

请提取以下类型的概念：{concept_types}

请以JSON格式返回结果，包含以下字段：
- concepts: 概念列表，每个概念包含：
  - type: 概念类型
  - name: 概念名称
  - relevance: 相关度(0-1)
  - attributes: 概念属性(可选)
"""

MEMORY_RETRIEVAL_TEMPLATE = """
基于当前对话检索相关记忆：
当前输入：{input}
对话历史：{history}
检索要求：{requirements}

你的任务是：
1. 分析用户输入和对话历史
2. 评估每条候选记忆的相关性
3. 返回结构化的JSON响应
4. 严格遵循JSON格式，不要返回任何其他内容如果成功返回你将会收到奖励否则会有惩罚
评估标准：
1. 话题相关性
   - 核心话题是否相同或相关？
   - 是否涉及相同的人或事？
   - 背景信息是否相关？

2. 情感联系
   - 情感类型是否相似？
   - 情感强度是否相近？
   - 是否能引起情感共鸣？

3. 时间关联
   - 事件发生的时间顺序
   - 是否存在因果关系
   - 时间跨度是否合适

4. 用途相关
   - 这段记忆是否有助于当前对话？
   - 如何自然地引入这段记忆？
   - 引用这段记忆的价值是什么？

你必须返回以下格式的JSON响应：
{{
    "relevant_memories": [
        {{
            "memory_id": "记忆ID",
            "relevance_score": 0.9,
            "reason": "相关原因",
            "usage_suggestion": "使用建议"
        }}
    ]
}}

严格要求：
1. 响应必须是合法的JSON格式
2. relevant_memories必须是数组，即使为空也要返回[]
3. relevance_score必须是0到1之间的浮点数
4. reason和usage_suggestion必须是非空字符串
5. memory_id必须来自输入的记忆列表
6. 所有字段都必须存在且不能为null
7. 不要返回任何其他字段
8. 不要在JSON之外返回任何文本
"""

MEMORY_CONSOLIDATION_TEMPLATE = """
整合多条记忆生成回复：
相关记忆：{memories}
当前上下文：{context}
用户输入：{input}

整合要求：
1. 内容整合
   - 找出记忆之间的关联
   - 提取关键信息
   - 形成连贯的叙述

2. 情感连接
   - 保持情感的连贯性
   - 建立情感共鸣
   - 适当的情感过渡

3. 个性化表达
   - 符合用户的表达习惯
   - 考虑用户的性格特点
   - 保持对话的自然感

输出格式：
{
    "response": "生成的回复内容",
    "used_memories": ["使用的记忆ID列表"],
    "reasoning": "使用这些记忆的原因",
    "emotional_coherence": "情感连贯性说明"
}
"""

BASE_SNAPSHOT_TEMPLATE = """
评估当前查询与基础记忆分类的相关性：

查询信息：
{requirements}

请评估每个基础分类的相关程度，考虑：
1. 主题相关性：查询的主题是否与分类匹配
2. 关键词匹配：查询中的关键词是否出现在分类的关键词列表中
3. 语义相关性：查询的语义是否与分类的含义相关

输出格式：
{
    "relevant_categories": [
        {
            "snapshot_id": "分类ID",
            "relevance_reason": "相关原因说明"
        }
    ],
    "reasoning": "选择这些分类的整体思路"
}
"""

DETAIL_SNAPSHOT_TEMPLATE = """
评估当前查询与详细记忆快照的相关性：

查询信息：
{requirements}

请评估每个快照的相关程度，考虑：
1. 内容相关性：快照摘要与查询的相关程度
2. 情感匹配：情感标签的匹配程度
3. 关键要素：核心要素的重合度
4. 时间相关：时间上的关联性

请仔细评估每个快照的相关性，并按照以下 JSON 格式输出结果：
{
    "relevant_snapshots": [
        {
            "snapshot_id": "快照ID",
            "relevance_score": 0.85,
            "match_aspects": [
                "内容高度相关",
                "情感标签匹配",
                "包含相同关键要素"
            ]
        }
    ],
    "reasoning": "选择这些快照的整体思路"
}

注意：
1. 输出必须是有效的 JSON 格式
2. relevant_snapshots 是一个数组，可以为空 []
3. relevance_score 必须是 0 到 1 之间的浮点数
4. match_aspects 必须是非空字符串数组，至少包含一个元素
5. reasoning 必须是非空字符串，详细说明选择理由
6. snapshot_id 必须从输入的快照列表中选择
7. 所有字段都必须存在且不能为 null
"""

MEMORY_ANALYSIS_TEMPLATE = """
请分析以下记忆内容，提取关键信息。
{context_str}
记忆内容：{content}

请以JSON格式返回分析结果，包含以下字段：
- key_points: 关键点列表，每个关键点是一句简短的描述
- importance: 重要性评分(0-1)
- category: 记忆分类(例如：工作、生活、学习、娱乐等)
- emotions: 情感标签列表

注意：
1. 关键点应该是对记忆内容的精炼总结
2. 重要性评分基于内容的价值和影响
3. 分类应该准确反映记忆的主题
4. 情感标签应该反映记忆中的情感倾向
"""

KEY_POINTS_SUMMARY_TEMPLATE = """
请对以下关键点进行总结和归类：
{key_points}

请以JSON格式返回总结结果，包含以下字段：
- keywords: 核心关键词列表
- description: 一句话总结
- category: 最适合的分类

注意：
1. 关键词应该是最具代表性的词语
2. 描述应该简洁但完整地概括所有关键点
3. 分类应该能够准确反映内容的主题
""" 