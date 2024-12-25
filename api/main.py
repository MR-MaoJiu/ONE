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
"""
import os
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.memory.factory import MemorySystemFactory
from utils.logger import get_logger

api_logger = get_logger('api')

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
async def create_chat_manager() -> 'ChatManager':
    """Initialize the chat manager with memory system / 初始化带有记忆系统的聊天管理器"""
    chat_manager = await MemorySystemFactory.create_from_config()
    api_logger.info("Chat manager created successfully / 聊天管理器创建成功")
    return chat_manager

# Get chat manager instance / 获取聊天管理器实例
chat_manager: Optional['ChatManager'] = None

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
        enable_api_call: Whether to enable API call functionality / 是否启用API调用功能
        api_docs: API documentation content when API call is enabled / 启用API调用时的API文档内容
    """
    content: str = Field(..., description="The message content / 消息内容")
    context: Dict[str, Any] = Field(default={}, description="Optional context information / 可选的上下文信息")
    enable_api_call: bool = Field(default=False, description="Whether to enable API call functionality / 是否启用API调用功能")
    api_docs: str = Field(default="", description="API documentation content / API文档内容")

class Memory(BaseModel):
    """
    Memory model / 记忆模型
    
    Attributes / 属性:
        id: Unique identifier for the memory / 记忆的唯一标识符
        content: The memory content / 记忆内容
        timestamp: When the memory was created / 记忆创建时间
        metadata: Associated metadata / 相关的元数据
    """
    id: int = Field(..., description="Memory ID / 记忆ID")
    content: str = Field(..., description="Memory content / 记忆内容")
    timestamp: str = Field(..., description="Creation timestamp / 创建时间戳")
    metadata: Dict[str, Any] = Field(..., description="Metadata / 元数据")

class Snapshot(BaseModel):
    """
    Memory snapshot model / 记忆快照模型
    
    Attributes / 属性:
        id: Unique identifier for the snapshot / 快照的唯一标识符
        content: The snapshot content / 快照内容
        timestamp: When the snapshot was created / 快照创建时间
        metadata: Associated metadata / 相关的元数据
    """
    id: int = Field(..., description="Snapshot ID / 快照ID")
    content: str = Field(..., description="Snapshot content / 快照内容")
    timestamp: str = Field(..., description="Creation timestamp / 创建时间戳")
    metadata: Dict[str, Any] = Field(..., description="Metadata / 元数据")

class ChatResponse(BaseModel):
    """
    Chat response model / 聊天响应模型
    
    Attributes:
        response: The response text / 响应文本
        thinking_steps: The AI's thinking steps / AI的思考步骤
    """
    response: str = Field(..., description="Response text / 响应文本")
    thinking_steps: List[Dict[str, Any]] = Field(..., description="AI's thinking steps / AI的思考步骤")

@app.post("/chat", response_model=ChatResponse)
async def chat(message: Message):
    """
    Process a chat message and return a response / 处理聊天消息并返回响应
    
    Args:
        message: The chat message with content and optional context
                聊天消息，包含内容和可选的上下文
        
    Returns:
        ChatResponse with response text and thinking steps
        包含响应文本和思考步骤的ChatResponse对象
        
    Raises:
        HTTPException: If chat manager is not initialized or processing fails
                      如果聊天管理器未初始化或处理失败
    """
    try:
        if not chat_manager:
            raise HTTPException(status_code=503, detail="Chat manager not initialized / 聊天管理器未初始化")
            
        # 添加API调用相关的上下文信息
        context = message.context or {}
        if message.enable_api_call:
            context.update({
                'enable_api_call': True,
                'api_docs': message.api_docs,
                'api_warning': '注意：API调用可能会增加响应时间'
            })
        else:
            context.update({
                'enable_api_call': False,
                'api_docs': '',
                'api_warning': ''
            })
            
        result = await chat_manager.chat(message.content, context)
        return ChatResponse(
            response=result['response'],
            thinking_steps=result['thinking_steps']
        )
        
    except Exception as e:
        api_logger.error(f"Failed to process chat request / 处理聊天请求失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for chat / 聊天的WebSocket端点
    
    Handles:
    - Connection initialization / 连接初始化
    - Message processing / 消息处理
    - Error handling / 错误处理
    - Connection cleanup / 连接清理
    """
    try:
        await websocket.accept()
        api_logger.info("WebSocket连接已建立")
        
        while True:
            try:
                # 等待接收消息
                data = await websocket.receive_json()
                content = data.get("content", "")
                enable_api_call = data.get("enable_api_call", False)
                api_docs = data.get("api_docs", "")
                
                # 清空之前的思考步骤
                await websocket.send_json({
                    "type": "thinking_clear"
                })
                
                # 处理用户消息并获取回复
                if not chat_manager:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Chat manager not initialized"
                    })
                    continue
                
                # 构建上下文信息
                context = {}
                if enable_api_call:
                    context.update({
                        'enable_api_call': True,
                        'api_docs': api_docs,
                        'api_warning': '注意：API调用可能会增加响应时间'
                    })
                else:
                    context.update({
                        'enable_api_call': False,
                        'api_docs': '',
                        'api_warning': ''
                    })
                    
                result = await chat_manager.chat(content, context)
                
                # 发送思考步骤
                if 'thinking_steps' in result:
                    for step in result['thinking_steps']:
                        await websocket.send_json({
                            "type": "thinking_step",
                            "step": step
                        })
                
                # 发送最终回复
                await websocket.send_json({
                    "type": "message",
                    "response": result['response']
                })
                
            except WebSocketDisconnect:
                api_logger.info("WebSocket连接已断开")
                return
            except Exception as e:
                api_logger.error(f"处理消息时发生错误: {str(e)}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"处理消息时发生错误: {str(e)}"
                    })
                except:
                    api_logger.error("发送错误消息失败")
                continue
                
    except WebSocketDisconnect:
        api_logger.info("WebSocket连接初始化时断开")
    except Exception as e:
        api_logger.error(f"WebSocket连接错误: {str(e)}")
    finally:
        api_logger.info("WebSocket连接关闭")

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
            
        memories = await chat_manager.get_all_memories()
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
            
        snapshots = await chat_manager.get_all_snapshots()
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
            
        await chat_manager.snapshot_manager.update_snapshots()
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
            
        await chat_manager.clear_all()
        return {"message": "All memories cleared successfully / 所有记忆清空成功"}
        
    except Exception as e:
        api_logger.error(f"Failed to clear memories / 清空记忆失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 