"""
快照生成相关提示词模板
"""

DETAIL_SNAPSHOT_TEMPLATE = """
从以下记忆内容生成详细快照:

记忆内容:
{memory_contents}

情感标签:
{emotion_tags}

时间范围:
{time_range}

请分析以下方面:
1. 核心主题
   - 识别主要话题和事件
   - 提取关键人物和场景
   - 总结重要细节

2. 情感分析
   - 识别主要情感倾向
   - 分析情感变化
   - 评估情感强度

3. 关键要素
   - 提取重要概念
   - 识别关键词
   - 总结核心观点

输出格式:
{
    "summary": "记忆内容的简要总结",
    "key_elements": ["关键要素1", "关键要素2"],
    "emotion_analysis": {
        "primary_emotions": ["主要情感1", "主要情感2"],
        "intensity": 0.8
    },
    "topics": ["主题1", "主题2"],
    "importance_score": 0.9
}
"""

BASE_SNAPSHOT_TEMPLATE = """
从以下详细快照生成基础快照:

详细快照列表:
{detail_snapshots}

请分析以下方面:
1. 主题分类
   - 识别共同主题
   - 归纳核心类别
   - 提取关键特征

2. 时间关联
   - 分析时间跨度
   - 识别时序关系
   - 评估时间相关性

3. 概念关联
   - 分析概念重叠
   - 识别关联强度
   - 构建概念网络

输出格式:
{
    "category": "主题分类",
    "keywords": ["关键词1", "关键词2"],
    "time_span": {
        "start": "开始时间",
        "end": "结束时间"
    },
    "concept_graph": [
        {
            "concept": "概念1",
            "related_concepts": ["相关概念1", "相关概念2"],
            "strength": 0.8
        }
    ],
    "importance_score": 0.9
}
"""

SNAPSHOT_OPTIMIZATION_TEMPLATE = """
优化现有快照:

当前快照:
{current_snapshot}

相关记忆:
{related_memories}

优化目标:
1. 内容优化
   - 提高摘要质量
   - 优化关键词提取
   - 改进主题分类

2. 结构优化
   - 合并相似快照
   - 拆分过大快照
   - 调整层级关系

3. 时效性优化
   - 更新过期内容
   - 保留重要历史
   - 移除冗余信息

输出格式:
{
    "optimization_type": "优化类型",
    "changes": [
        {
            "type": "修改类型",
            "target": "修改目标",
            "reason": "修改原因",
            "suggestion": "具体建议"
        }
    ],
    "expected_improvement": 0.8
}
""" 