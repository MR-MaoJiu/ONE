"""
API服务入口
"""
import os
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.chat.chat_manager import ChatManager
from core.memory.factory import MemorySystemFactory
from utils.logger import api_logger

# 创建FastAPI应用
app = FastAPI(title="AI助手API", description="AI助手系统的API接口")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建聊天管理器
async def create_chat_manager() -> ChatManager:
    # 使用工厂创建聊天管理器
    chat_manager = await MemorySystemFactory.create_from_config()
    api_logger.info("聊天管理器创建成功")
    return chat_manager

# 获取聊天管理器实例
chat_manager: Optional[ChatManager] = None

@app.on_event("startup")
async def startup_event():
    global chat_manager
    chat_manager = await create_chat_manager()

class Message(BaseModel):
    content: str
    context: Dict[str, Any] = {}

@app.post("/chat")
async def chat(message: Message):
    """
    处理聊天请求
    """
    try:
        if not chat_manager:
            return {"error": "聊天管理器未初始化"}
            
        # 处理聊天请求
        response = await chat_manager.chat(message.content, message.context)
        
        # 返回响应和分析结果
        return {
            "response": response,
            "analysis": {
                "steps": [
                    {
                        "type": "memory_retrieval",
                        "description": "检索相关记忆",
                        "output": {
                            "relevant_memories": message.context.get("relevant_memories", [])
                        }
                    },
                    {
                        "type": "response_generation",
                        "description": "生成回复",
                        "output": response
                    }
                ]
            }
        }
        
    except Exception as e:
        api_logger.error(f"处理聊天请求失败: {str(e)}", exc_info=True)
        return {"error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket聊天接口
    """
    try:
        await websocket.accept()
        
        if not chat_manager:
            await websocket.send_json({"error": "聊天管理器未初始化"})
            return
            
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message = Message(**data)
            
            # 处理消息
            response = await chat_manager.chat(message.content)
            
            # 发送响应
            await websocket.send_json({"response": response})
            
    except WebSocketDisconnect:
        api_logger.info("WebSocket连接断开")
    except Exception as e:
        api_logger.error(f"WebSocket处理失败: {str(e)}", exc_info=True)
        await websocket.send_json({"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 