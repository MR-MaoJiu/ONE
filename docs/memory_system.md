# 记忆系统文档

## 数据结构

### 基础记忆 (BaseMemory)
```json
{
    "id": "memory_uuid",
    "content": "记忆内容",
    "timestamp": "2024-12-24T14:08:07.103Z",
    "context": {
        "user_id": "用户ID",
        "session_id": "会话ID",
        "other_context": "其他上下文信息"
    }
}
```

### 记忆快照 (MemorySnapshot)
```json
{
    "id": "snapshot_uuid",
    "key_points": ["关键点1", "关键点2"],
    "memory_refs": ["memory_id1", "memory_id2"],
    "category": "分类名称",
    "timestamp": "2024-12-24T14:08:07.103Z",
    "importance": 0.8
}
```

### 元快照 (MetaSnapshot)
```json
{
    "id": "meta_uuid",
    "category": "分类名称",
    "keywords": ["关键词1", "关键词2"],
    "snapshot_refs": ["snapshot_id1", "snapshot_id2"],
    "description": "分类描述",
    "timestamp": "2024-12-24T14:08:07.103Z"
}
```

### 存储索引结构
```json
{
    "memories": {
        "memory_id": {
            "path": "memories/memory_id.json",
            "timestamp": "2024-12-24T14:08:07.103Z",
            "type": "base"
        }
    },
    "snapshots": {
        "snapshot_id": {
            "path": "snapshots/snapshot_id.json",
            "timestamp": "2024-12-24T14:08:07.103Z",
            "type": "snapshot"
        }
    },
    "meta_snapshots": {
        "meta_id": {
            "path": "meta_snapshots/meta_id.json",
            "timestamp": "2024-12-24T14:08:07.103Z",
            "type": "meta"
        }
    },
    "categories": {}
}
```

### 记忆检索结构

#### 记忆检索请求
```json
{
    "current_query": "用户当前输入",
    "history": [
        {
            "is_user": true,
            "content": "用户消息",
            "timestamp": "2024-12-24T14:08:07.103Z"
        }
    ],
    "timestamp": "2024-12-24T14:08:07.103Z"
}
```

#### 记忆检索响应
```json
{
    "relevant_memories": [
        {
            "memory_id": "记忆ID",
            "relevance_score": 0.8,
            "reason": "相关原因说明"
        }
    ]
}
```

## 模块职责

### 存储模块 (MemoryStorage)
负责记忆和快照的持久化存储。

方法：
- `save_memory(memory_id: str, memory_data: Dict)` - 保存记忆
- `save_snapshot(snapshot_id: str, snapshot_data: Dict)` - 保存快照
- `save_meta_snapshot(meta_id: str, meta_data: Dict)` - 保存元快照
- `load_memory(memory_id: str) -> Optional[Dict]` - 加载记忆
- `load_snapshot(snapshot_id: str) -> Optional[Dict]` - 加载快照
- `load_meta_snapshot(meta_id: str) -> Optional[Dict]` - 加载元快照
- `cleanup_old_memories(days: int)` - 清理旧记忆

### 快照管理器 (SnapshotManager)
负责记忆快照的创建、更新和检索。

方法：
- `add_memory(memory: BaseMemory) -> str` - 添加记忆
- `create_snapshot(key_points: List[str], memory_ids: List[str], category: str, importance: float) -> MemorySnapshot` - 创建快照
- `create_meta_snapshot(category: str, keywords: List[str], snapshot_ids: List[str], description: str) -> MetaSnapshot` - 创建元快照
- `get_memory(memory_id: str) -> Optional[BaseMemory]` - 获取记忆
- `get_snapshot(snapshot_id: str) -> Optional[MemorySnapshot]` - 获取快照
- `get_meta_snapshot(meta_id: str) -> Optional[MetaSnapshot]` - 获取元快照
- `find_snapshots_by_category(category: str) -> List[MemorySnapshot]` - 按分类查找快照
- `find_meta_snapshots_by_category(category: str) -> List[MetaSnapshot]` - 按分类查找元快照

### 快照生成器 (SnapshotGenerator)
负责使用 LLM 生成快照内容。

方法：
- `generate_detail_snapshot(memories: List[BaseMemory], snapshot_id: str) -> MemorySnapshot` - 生成详细快照
- `generate_meta_snapshot(snapshots: List[MemorySnapshot], meta_id: str) -> MetaSnapshot` - 生成元快照

生成详细快照的 LLM 输入格式：
```json
{
    "key_points": ["关键要素1", "关键要素2"],
    "category": "分类名称",
    "importance": 0.8
}
```

生成元快照的 LLM 输入格式：
```json
{
    "category": "分类名称",
    "keywords": ["关键词1", "关键词2"],
    "description": "分类描述"
}
```

### 快照处理器 (SnapshotProcessor)
负责处理记忆内容，生成和管理快照。

方法：
- `process_memory(content: Dict[str, Any]) -> str` - 处理记忆内容，生成快照
- `get_relevant_memories(context: Dict[str, Any]) -> List[Tuple[BaseMemory, float]]` - 获取相关记忆

记忆内容格式：
```json
{
    "content": "记忆内容",
    "context": {
        "user_id": "用户ID",
        "session_id": "会话ID"
    },
    "timestamp": "2024-12-24T14:08:07.103Z"
}
```

### LLM 服务 (LLMService)
负责与 LLM API 交互。

方法：
- `chat(query: str, context: Dict[str, Any] = None) -> str` - 聊天接口
- `generate_json(prompt: str) -> Dict[str, Any]` - 生成 JSON 格式的回复

## 注意事项

1. 所有时间戳使用 ISO 格式：`YYYY-MM-DDTHH:mm:ss.sssZ`
2. 所有 ID 使用 UUID 格式，并添加相应前缀：
   - 记忆：`memory_`
   - 快照：`snapshot_`
   - 元快照：`meta_`
3. JSON 字段名保持一致：
   - ID 统一使用 `id`
   - 时间戳统一使用 `timestamp`
   - 分类统一使用 `category`
   - 关键词统一使用 `keywords`
   - 相关度分数统一使用 `relevance_score`
   - 重要性分数统一使用 `importance`
4. 所有异步方法使用 `async/await`
5. 所有方法都需要进行异常处理和日志记录
6. 记忆检索相关：
   - 相关度分数范围：0-1
   - 只返回相关度大于 0.5 的记忆
   - 按相关度从高到低排序
   - 考虑内容相关性、时间相关性和上下文匹配 