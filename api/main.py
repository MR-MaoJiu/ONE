"""
AI Assistant API Documentation / AI助手API文档

This is the main API entry point for the AI Assistant system. It provides endpoints for chat interactions
and memory management.

这是AI助手系统的主要API入口点，提供聊天交互和记忆管理的接口。

Features / 功能特点:
1. Chat Interface / 聊天接口
   - HTTP POST endpoint for single message exchanges / 用于单条消息交换的HTTP POST接口
   - WebSocket endpoint for real-time chat / 用于实时聊天的WebSocket接口
   - Context-aware responses using memory system / 使用记忆系统的上下文感知响应
   
2. Memory System / 记忆系统
   - Stores conversation history / 存储对话历史
   - Creates memory snapshots for important information / 为重要信息创建记忆快照
   - Retrieves relevant memories for context / 检索相关的上下文记忆

3. LLM Integration / LLM集成
   - Connects to LLM service for generating responses / 连接LLM服务生成响应
   - Handles context and memory integration / 处理上下文和记忆集成

API Endpoints / API端点:

1. Chat / 聊天
   POST /chat
   - Process single message / 处理单条消息
   - Input: Message object / 输入：消息对象
   - Output: Response object / 输出：响应对象

2. WebSocket Chat / WebSocket聊天
   WS /ws
   - Real-time chat connection / 实时聊天连接
   - Bi-directional message flow / 双向消息流

3. Memory Management / 记忆管理
   GET /memories
   - Retrieve all memories / 获取所有记忆
   
   GET /snapshots
   - Retrieve all snapshots / 获取所有快照
   
   POST /snapshots/update
   - Update memory snapshots / 更新记忆快照
   
   DELETE /memories
   - Clear all memories and snapshots / 清空所有记忆和快照
"""
import os
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.chat.chat_manager import ChatManager
from core.memory.factory import MemorySystemFactory
from utils.logger import api_logger

# Create FastAPI application / 创建FastAPI应用
app = FastAPI(
    title="AI Assistant API / AI助手API",
    description="API interface for AI assistant system with memory capabilities / 具有记忆能力的AI助手系统API接口",
    version="1.0.0"
)

# Configure CORS / 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL / 前端URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create chat manager / 创建聊天管理器
async def create_chat_manager() -> ChatManager:
    """Initialize the chat manager with memory system / 初始化带有记忆系统的聊天管理器"""
    chat_manager = await MemorySystemFactory.create_from_config()
    api_logger.info("Chat manager created successfully / 聊天管理器创建成功")
    return chat_manager

# Get chat manager instance / 获取聊天管理器实例
chat_manager: Optional[ChatManager] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the chat manager on application startup / 在应用启动时初始化聊天管理器"""
    global chat_manager
    chat_manager = await create_chat_manager()

class Message(BaseModel):
    """
    Chat message model / 聊天消息模型
    
    Attributes / 属性:
        content: The message text content / 消息文本内容
        context: Optional context information for the message / 消息的可选上下文信息
    """
    content: str = Field(..., description="The message content / 消息内容")
    context: Dict[str, Any] = Field(default={}, description="Optional context information / 可选的上下文信息")

class Memory(BaseModel):
    """
    Memory model / 记忆模型
    
    Attributes / 属性:
        id: Unique identifier for the memory / 记忆的唯一标识符
        content: The memory content / 记忆内容
        timestamp: When the memory was created / 记忆创建时间
        context: Associated context information / 相关的上下文信息
    """
    id: str = Field(..., description="Memory ID / 记忆ID")
    content: str = Field(..., description="Memory content / 记忆内容")
    timestamp: str = Field(..., description="Creation timestamp / 创建时间戳")
    context: Dict[str, Any] = Field(..., description="Context information / 上下文信息")

class Snapshot(BaseModel):
    """
    Memory snapshot model / 记忆快照模型
    
    Attributes / 属性:
        id: Unique identifier for the snapshot / 快照的唯一标识符
        key_points: List of key information points / 关键信息点列表
        category: Category of the snapshot / 快照类别
        importance: Importance score (0-1) / 重要性分数 (0-1)
    """
    id: str = Field(..., description="Snapshot ID / 快照ID")
    key_points: List[str] = Field(..., description="Key information points / 关键信息点")
    category: str = Field(..., description="Snapshot category / 快照类别")
    importance: float = Field(..., ge=0, le=1, description="Importance score / 重要性分数")

@app.post("/chat", response_model=Dict[str, str])
async def chat(message: Message):
    """
    Process a chat message and return a response / 处理聊天消息并返回响应
    
    Args / 参数:
        message: The chat message with content and optional context
                聊天消息，包含内容和可选的上下文
        
    Returns / 返回:
        Dict with response text or error message
        包含响应文本或错误消息的字典
        
    Raises / 异常:
        HTTPException: If chat manager is not initialized or processing fails
                      如果聊天管理器未初始化或处理失败
    """
    try:
        if not chat_manager:
            raise HTTPException(status_code=503, detail="Chat manager not initialized / 聊天管理器未初始化")
            
        response = await chat_manager.chat(message.content)
        return {"response": response}
        
    except Exception as e:
        api_logger.error(f"Failed to process chat request / 处理聊天请求失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat / 用于实时聊天的WebSocket端点
    
    Handles / 处理:
    - Connection initialization / 连接初始化
    - Message processing / 消息处理
    - Error handling / 错误处理
    - Connection cleanup / 连接清理
    """
    try:
        await websocket.accept()
        
        if not chat_manager:
            await websocket.send_json({"error": "Chat manager not initialized / 聊天管理器未初始化"})
            return
            
        while True:
            # Receive message / 接收消息
            data = await websocket.receive_json()
            message = Message(**data)
            
            # Process message / 处理消息
            response = await chat_manager.chat(message.content)
            
            # Send response / 发送响应
            await websocket.send_json({"response": response})
            
    except WebSocketDisconnect:
        api_logger.info("WebSocket connection closed / WebSocket连接已关闭")
    except Exception as e:
        api_logger.error(f"WebSocket processing failed / WebSocket处理失败: {str(e)}", exc_info=True)
        await websocket.send_json({"error": str(e)})

@app.get("/memories", response_model=List[Memory])
async def get_memories():
    """
    Retrieve all stored memories / 获取所有存储的记忆
    
    Returns / 返回:
        List of Memory objects / 记忆对象列表
        
    Raises / 异常:
        HTTPException: If memory retrieval fails / 如果记忆检索失败
    """
    try:
        if not chat_manager:
            raise HTTPException(status_code=503, detail="Chat manager not initialized / 聊天管理器未初始化")
            
        memories = await chat_manager.snapshot_processor.get_all_memories()
        return memories
        
    except Exception as e:
        api_logger.error(f"Failed to get memories / 获取记忆失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/snapshots", response_model=List[Snapshot])
async def get_snapshots():
    """
    Retrieve all memory snapshots / 获取所有记忆快照
    
    Returns / 返回:
        List of Snapshot objects / 快照对象列表
        
    Raises / 异常:
        HTTPException: If snapshot retrieval fails / 如果快照检索失败
    """
    try:
        if not chat_manager:
            raise HTTPException(status_code=503, detail="Chat manager not initialized / 聊天管理器未初始化")
            
        snapshots = await chat_manager.snapshot_processor.get_all_snapshots()
        return snapshots
        
    except Exception as e:
        api_logger.error(f"Failed to get snapshots / 获取快照失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/snapshots/update")
async def update_snapshots():
    """
    Trigger manual update of memory snapshots / 触发记忆快照的手动更新
    
    Returns / 返回:
        Success message / 成功消息
        
    Raises / 异常:
        HTTPException: If update fails / 如果更新失败
    """
    try:
        if not chat_manager:
            raise HTTPException(status_code=503, detail="Chat manager not initialized / 聊天管理器未初始化")
            
        await chat_manager.snapshot_processor.update_snapshots()
        return {"message": "Snapshots updated successfully / 快照更新成功"}
        
    except Exception as e:
        api_logger.error(f"Failed to update snapshots / 更新快照失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories")
async def clear_memories():
    """
    Clear all stored memories and snapshots / 清空所有存储的记忆和快照
    
    Returns / 返回:
        Success message / 成功消息
        
    Raises / 异常:
        HTTPException: If clearing fails / 如果清空失败
    """
    try:
        if not chat_manager:
            raise HTTPException(status_code=503, detail="Chat manager not initialized / 聊天管理器未初始化")
            
        await chat_manager.snapshot_processor.clear_all()
        return {"message": "All memories cleared successfully / 所有记忆清空成功"}
        
    except Exception as e:
        api_logger.error(f"Failed to clear memories / 清空记忆失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 