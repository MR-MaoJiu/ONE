# AI助手系统

这是一个基于大语言模型的AI助手系统，具有记忆管理和对话能力。

## 主要特性

- 智能对话：基于大语言模型的自然对话能力
- 记忆系统：分层的记忆管理，包括基础记忆、记忆快照和元快照
- 动态分类：自动对记忆进行分类和管理
- 上下文感知：根据对话上下文检索相关记忆

## 系统架构

系统主要包含以下模块：

- `core/`: 核心功能模块
  - `memory/`: 记忆系统实现
  - `processor/`: 记忆处理器
  - `retrieval/`: 记忆检索
- `api/`: API接口
- `services/`: 外部服务集成
- `utils/`: 工具函数
- `config/`: 配置文件

### 记忆系统

记忆系统采用三层架构：

1. 基础记忆（BaseMemory）
   - 存储完整的对话内容和上下文
   - 包含时间戳、重要性等元数据

2. 记忆快照（MemorySnapshot）
   - 提取记忆的关键信息
   - 包含对原始记忆的引用
   - 按类别组织

3. 元快照（MetaSnapshot）
   - 对相似快照进行分类和总结
   - 提供更高层次的记忆组织

## 配置说明

系统配置位于`config/`目录：

- `default_memory_config.json`: 记忆系统配置
  - `storage`: 存储相关配置
  - `snapshot`: 快照处理配置
  - `chat`: 对话相关配置

## API接口

### 对话接口

```http
POST /chat
Content-Type: application/json

{
    "query": "用户输入",
    "context": {} // 可选的上下文信息
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

2. 配置
- 复制`config/default_memory_config.json`为`config/memory_config.json`
- 根据需要修改配置参数

3. 运行
```bash
python api/main.py
```

## 注意事项

- 定期清理旧记忆以优化存储空间
- 合理配置记忆重要性阈值
- 监控记忆统计信息
