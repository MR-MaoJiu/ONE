"""
LLM服务模块
"""
import os
from typing import Dict, Any, List, Optional
import httpx
from openai import OpenAI
from pydantic import BaseModel
from utils.logger import get_logger
from dotenv import load_dotenv
import json

# 加载环境变量
load_dotenv()

# 创建logger
llm_logger = get_logger('llm')

class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMConfig':
        """从字典创建配置，处理环境变量引用"""
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                processed_data[key] = os.getenv(env_var)
            else:
                processed_data[key] = value
        return cls(**processed_data)

class LLMService:
    """LLM服务基类"""
    def __init__(self, config: Dict[str, Any]):
        # 处理配置
        self.config = LLMConfig.from_dict(config)
        
        # 创建OpenAI客户端
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            http_client=httpx.Client(
                base_url=self.config.base_url,
                follow_redirects=True,
            ) if self.config.base_url else None
        )
        
    async def chat(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        聊天接口
        
        Args:
            query: 用户输入
            context: 上下文信息
            
        Returns:
            str: 助手回复
        """
        try:
            # 构建消息列表
            messages = []
            
            # 添加历史记录
            if context and 'history' in context:
                for msg in context['history']:
                    messages.append({
                        'role': 'user' if msg['is_user'] else 'assistant',
                        'content': msg['content']
                    })
            
            # 添加相关记忆
            if context and 'relevant_memories' in context:
                memory_text = "相关记忆:\n"
                for memory in context['relevant_memories']:
                    memory_text += f"- {memory['content']} (相关度: {memory['score']:.2f})\n"
                messages.append({
                    'role': 'system',
                    'content': memory_text
                })
            
            # 添加当前查询
            messages.append({
                'role': 'user',
                'content': query
            })
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # 提取回复文本
            reply = response.choices[0].message.content.strip()
            llm_logger.info("生成回复：%s", reply)
            
            return reply
            
        except Exception as e:
            llm_logger.error("生成回复失败：%s", str(e), exc_info=True)
            raise 

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        生成JSON格式的回复
        
        Args:
            prompt: 提示词
            
        Returns:
            Dict: JSON格式的回复
        """
        try:
            # 构建消息列表
            messages = [
                {
                    'role': 'system',
                    'content': '你是一个智能助手，请直接返回JSON对象，不要包含任何其他格式或标记。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # 提取回复文本
            result = response.choices[0].message.content.strip()
            llm_logger.info("生成JSON回复：%s", result)
            
            # 清理可能的 Markdown 代码块标记
            result = result.replace('```json', '').replace('```', '').strip()
            
            # 解析JSON
            if not result:
                return {}
                
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                llm_logger.error(f"JSON解析失败: {result}")
                return {}
            
        except Exception as e:
            llm_logger.error(f"生成JSON失败: {str(e)}")
            return {} 