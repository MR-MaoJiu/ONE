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
from datetime import datetime

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
        llm_logger.info("开始处理配置数据: %s", data)
        
        # 确保环境变量已加载
        llm_logger.info("当前环境变量: OPENAI_API_KEY=%s, OPENAI_API_BASE=%s", 
                       '***' if os.getenv('OPENAI_API_KEY') else None,
                       os.getenv('OPENAI_API_BASE'))
        
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                env_value = os.getenv(env_var)
                llm_logger.info("处理环境变量 %s: %s -> %s", key, env_var, 
                              '***' if 'key' in key.lower() else env_value)
                processed_data[key] = env_value
            else:
                processed_data[key] = value
                llm_logger.info("使用原始值 %s: %s", key, 
                              '***' if 'key' in key.lower() else value)
        
        llm_logger.info("配置处理完成: %s", 
                       {k: '***' if 'key' in k.lower() else v for k, v in processed_data.items()})
        return cls(**processed_data)

class LLMService:
    """LLM服务基类"""
    def __init__(self, config: Dict[str, Any]):
        # 处理配置
        llm_logger.info("开始初始化LLM服务，原始配置：%s", config)
        self.config = LLMConfig.from_dict(config)
        llm_logger.info("LLM配置处理完成：%s", {
            'provider': self.config.provider,
            'model': self.config.model,
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
            'api_key': '***' if self.config.api_key else None,
            'base_url': self.config.base_url
        })
        
        # 创建OpenAI客户端
        llm_logger.info("正在创建OpenAI客户端，base_url: %s", self.config.base_url)
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            http_client=httpx.Client(
                base_url=self.config.base_url,
                follow_redirects=True,
            ) if self.config.base_url else None
        )
        llm_logger.info("OpenAI客户端创建完成")
        
        # 初始化思考步骤列表
        self.thinking_steps = []
        
    def _record_thinking_step(self, step_type: str, description: str, result: str = None):
        """记录思考步骤"""
        step = {
            'type': step_type,
            'description': description,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        self.thinking_steps.append(step)
        return step
        
    async def chat(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        聊天接口
        
        Args:
            query: 用户输入
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 包含回复文本和思考步骤的字典
        """
        try:
            # 清空思考步骤
            self.thinking_steps = []
            
            # 记录接收到的查询
            self._record_thinking_step(
                'input',
                '接收到用户查询',
                query
            )
            
            # 构建消息列表
            messages = []
            
            # 添加历史记录
            if context and 'history' in context:
                self._record_thinking_step(
                    'context',
                    '加载历史对话记录',
                    f'加载了 {len(context["history"])} 条历史消息'
                )
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
                self._record_thinking_step(
                    'memory',
                    '检索相关记忆',
                    memory_text
                )
                messages.append({
                    'role': 'system',
                    'content': memory_text
                })
            
            # 添加当前查询
            messages.append({
                'role': 'user',
                'content': query
            })
            
            # 记录开始生成回复
            self._record_thinking_step(
                'process',
                '开始生成回复',
                '使用OpenAI API生成回复'
            )
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # 提取回复文本
            reply = response.choices[0].message.content.strip()
            
            # 记录生成的回复
            self._record_thinking_step(
                'output',
                '生成回复完成',
                reply
            )
            
            llm_logger.info("生成回复：%s", reply)
            
            return {
                'response': reply,
                'thinking_steps': self.thinking_steps
            }
            
        except Exception as e:
            # 记录错误
            self._record_thinking_step(
                'error',
                '生成回复失败',
                str(e)
            )
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