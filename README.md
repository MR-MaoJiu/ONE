# AI永久记忆系统

这是一个基于大语言模型的AI助手系统，具有记忆管理、对话能力和API调用功能。

## 主要特性

- 智能对话：基于大语言模型的自然对话能力
- 记忆系统：分层的记忆管理，包括基础记忆、记忆快照和元快照
- 动态分类：自动对记忆进行分类和管理
- 上下文感知：根据对话上下文检索相关记忆
- API调用：支持通过对话调用外部API，实现更强大的功能扩展

## 系统架构

系统主要包含以下模块：

- `core/`: 核心功能模块
  - `memory/`: 记忆系统实现
  - `processor/`: 记忆处理器
  - `retrieval/`: 记忆检索
  - `chat/`: 对话管理
- `api/`: API接口
- `services/`: 外部服务集成
- `utils/`: 工具函数
- `config/`: 配置文件
- `frontend/`: 前端界面实现

### 记忆系统

记忆系统采用三层架构：

1. 基础记忆（BaseMemory）
   - 存储完整的对话内容和上下文
   - 包含时间戳、重要性等元数据
   - 记录API调用相关信息

2. 记忆快照（MemorySnapshot）
   - 提取记忆的关键信息
   - 包含对原始记忆的引用
   - 按类别组织
   - 保存API调用结果和分析

3. 元快照（MetaSnapshot）
   - 对相似快照进行分类和总结
   - 提供更高层次的记忆组织
   - 总结API使用模式和效果

## 配置说明

系统配置位于`config/`目录：

- `default_memory_config.json`: 记忆系统配置
  - `storage`: 存储相关配置
  - `snapshot`: 快照处理配置
  - `chat`: 对话相关配置
  - `api`: API调用相关配置

## API接口

### 对话接口

```http
POST /chat
Content-Type: application/json

{
    "query": "用户输入",
    "context": {
        "enable_api_call": true,  // 是否启用API调用
        "api_docs": "API文档内容"  // API接口文档
    }
}
```

### 记忆管理

```http
POST /clear_history  # 清空对话历史
POST /cleanup_memories  # 清理旧记忆
GET /memory_stats  # 获取记忆统计
```

## 开发指南

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 运行
```bash
python run.py

cd .\frontend\
npm install
npm run dev
```

## API调用功能

系统支持通过对话方式调用外部API，主要特点：

1. 动态API调用
   - 支持在对话中启用/禁用API调用
   - 可以动态提供API文档
   - 自动分析API调用需求

2. 智能分析
   - 自动分析用户需求
   - 匹配合适的API
   - 生成调用计划

3. 安全控制
   - API调用开关
   - 文档验证
   - 调用限制

4. 结果处理
   - 自动处理API响应
   - 整合到对话流程
   - 记录调用历史

5. 使用方法
   - 在对话界面启用API调用开关
   - 提供API文档（支持OpenAPI/Swagger格式）
   - 正常进行对话，系统会自动判断是否需要调用API

## 注意事项

- 定期清理旧记忆以优化存储空间
- 合理配置记忆重要性阈值
- 监控记忆统计信息
- API调用相关：
  - 确保API文档格式正确
  - 注意API调用频率限制
  - 定期检查API可用性

## UI参考
![ai.png](docs/ai.png)

## 赞助
1. 如果您觉得对您有用的话请给个star或者打赏一下，您的激励会使我更加有动力！！！
![img.png](docs/img.png)