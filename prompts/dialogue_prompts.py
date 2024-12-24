"""
对话生成相关提示词模板
"""

DIALOGUE_GENERATION_TEMPLATE = """
基于上下文生成对话回复：
用户输入：{input}
对话历史：{history}
记忆上下文：{memory_context}
用户画像：{user_profile}

生成要求：
1. 回复内容
   - 准确回应用户的问题/话题
   - 保持对话的连贯性
   - 适当引入相关记忆
   - 展现个性化理解

2. 情感表达
   - 根据用户情感调整语气
   - 表达适度的共情
   - 在必要时提供情感支持
   - 保持积极正向的态度

3. 对话策略
   - 适时引导话题深入
   - 保持对话的趣味性
   - 鼓励用户分享更多
   - 注意对话的边界

输出格式：
{
    "response": "生成的回复内容",
    "reasoning": "回复的思考过程",
    "strategy": "采用的对话策略",
    "used_memories": ["使用的记忆列表"],
    "emotional_tone": "采用的情感基调"
}
"""

DIALOGUE_PLANNING_TEMPLATE = """
规划对话策略：
当前话题：{topic}
用户状态：{user_state}
对话目标：{goal}

策略规划：
1. 话题展开
   - 当前话题的重要方面
   - 可能的延伸方向
   - 需要避免的敏感区域

2. 互动设计
   - 适当的提问时机
   - 引导用户分享的方式
   - 保持对话的活跃度

3. 记忆运用
   - 相关记忆的使用时机
   - 记忆引入的自然方式
   - 避免过度重复

输出格式：
{
    "topic_aspects": ["话题的重要方面列表"],
    "interaction_points": ["适合互动的节点"],
    "memory_usage": ["可以使用的记忆点"],
    "sensitive_areas": ["需要注意的敏感话题"],
    "suggested_approach": "建议的对话策略"
}
"""

DIALOGUE_REPAIR_TEMPLATE = """
修复对话中的问题：
对话历史：{history}
问题描述：{issue}
用户反馈：{feedback}

修复策略：
1. 问题分析
   - 确定问题的根源
   - 评估影响程度
   - 找出修复机会

2. 修复方案
   - 制定补救措施
   - 调整对话策略
   - 预防类似问题

3. 后续跟进
   - 验证修复效果
   - 更新对话策略
   - 完善预防机制

输出格式：
{
    "issue_analysis": "问题分析结果",
    "repair_plan": "具体的修复方案",
    "prevention": "预防类似问题的建议",
    "follow_up": "后续跟进计划"
}
""" 