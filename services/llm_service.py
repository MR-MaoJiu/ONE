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
    model: str = "gpt-4o"
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
                '理解用户问题',
                f'我收到了你的问题："{query}"'
            )
            
            # 构建消息列表
            messages = []
            
            # 添加历史记录
            if context and 'history' in context:
                history_count = len(context["history"])
                if history_count > 0:
                    self._record_thinking_step(
                        'context',
                        '回忆对话历史',
                        f'我回忆起了我们之前的 {history_count} 条对话'
                    )
                for msg in context['history']:
                    messages.append({
                        'role': 'user' if msg['is_user'] else 'assistant',
                        'content': msg['content']
                    })
            
            # 添加相关记忆
            if context and 'relevant_memories' in context:
                memory_text = "我找到了一些相关的记忆：\n"
                for memory in context['relevant_memories']:
                    memory_text += f"- {memory['content']}\n"
                self._record_thinking_step(
                    'memory',
                    '搜索相关记忆',
                    memory_text
                )
                messages.append({
                    'role': 'system',
                    'content': memory_text
                })
            
            # 添加API调用结果
            if context and 'api_results' in context:
                api_results_text = "我获取到了以下API调用结果：\n"
                for result in context['api_results']:
                    if result['success']:
                        api_results_text += f"- 成功：{json.dumps(result['data'], ensure_ascii=False)}\n"
                    else:
                        api_results_text += f"- 失败：{result['error']}\n"
                self._record_thinking_step(
                    'api_results',
                    '处理API调用结果',
                    api_results_text
                )
                messages.append({
                    'role': 'system',
                    'content': api_results_text
                })
            
            # 记录思考过程
            self._record_thinking_step(
                'process',
                '思考回答',
                '我正在思考如何回答你的问题...'
            )
            
            # 调用OpenAI API生成回复
            messages.append({
                'role': 'user',
                'content': query
            })
            
            try:
                # 调用OpenAI API
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                
                # 提取回复文本
                reply = response.choices[0].message.content.strip()
                
                # 记录输出结果
                self._record_thinking_step(
                    'output',
                    '生成回答',
                    f'我的回答是："{reply}"'
                )
                
                return {
                    'response': reply,
                    'thinking_steps': self.thinking_steps
                }
                
            except Exception as api_error:
                # 记录API调用错误
                error_message = f"调用API时发生错误：{str(api_error)}"
                self._record_thinking_step(
                    'error',
                    'API调用失败',
                    error_message
                )
                return {
                    'response': '抱歉，我现在无法回答您的问题。请稍后再试。',
                    'thinking_steps': self.thinking_steps
                }
            
        except Exception as e:
            # 记录其他错误
            error_message = f"处理过程中出现了错误：{str(e)}"
            self._record_thinking_step(
                'error',
                '发生错误',
                error_message
            )
            return {
                'response': '抱歉，处理您的请求时出现了错误。请稍后再试。',
                'thinking_steps': self.thinking_steps
            }

    async def analyze_api(self, query: str, api_docs: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        分析API文档和用户需求，生成API调用计划
        
        Args:
            query: 用户输入
            api_docs: API文档内容
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: API分析结果，包含是否需要调用API、调用计划等
        """
        try:
            # 记录开始分析的思考步骤
            self._record_thinking_step(
                'api_analysis_start',
                'API分析开始',
                '我正在分析您的需求和API文档...'
            )
            
            # 构建提示词
            prompt = f"""请分析以下用户需求和API文档，生成API调用计划：

用户需求：{query}

API文档：
{api_docs}

请按以下JSON格式返回分析结果：
{{
    "should_call_api": true/false,  // 是否需要调用API
    "reason": "解释为什么需要/不需要调用API",
    "plan": "API调用计划的详细说明",
    "api_calls": [  // 需要调用的API列表
        {{
            "url": "API地址",
            "method": "GET/POST/PUT/DELETE",
            "headers": {{}},  // 请求头
            "params": {{}},   // URL参数
            "data": {{}},     // 请求体数据
            "purpose": "这个API调用的目的是什么",  // 新增：说明这个API调用的目的
            "expected_result": "预期会得到什么结果"  // 新增：预期结果说明
        }}
    ]
}}"""

            # 记录正在分析的思考步骤
            self._record_thinking_step(
                'api_analysis_process',
                'API需求分析',
                f'我正在分析您的需求："{query}"，并将其与API文档进行匹配...'
            )

            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        'role': 'system',
                        'content': '你是一个API分析专家，请帮助分析用户需求并生成API调用计划。'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # 解析响应
            result = json.loads(response.choices[0].message.content.strip())
            llm_logger.info("API分析结果：%s", result)
            
            # 记录分析结果的思考步骤
            if result['should_call_api']:
                self._record_thinking_step(
                    'api_analysis_result',
                    'API调用决策',
                    f"我决定调用API，原因是：{result['reason']}"
                )
                
                # 记录调用计划
                self._record_thinking_step(
                    'api_call_plan',
                    'API调用计划',
                    f"调用计划：\n{result['plan']}"
                )
                
                # 记录每个API调用的详细信息
                for i, call in enumerate(result['api_calls'], 1):
                    self._record_thinking_step(
                        'api_call_detail',
                        f'API调用 #{i} 详情',
                        f"""调用信息：
- 目的：{call.get('purpose', '未指定')}
- URL：{call['url']}
- 方法：{call['method']}
- 预期结果：{call.get('expected_result', '未指定')}
- 参数：{json.dumps(call.get('params', {}), ensure_ascii=False, indent=2)}
- 数据：{json.dumps(call.get('data', {}), ensure_ascii=False, indent=2)}"""
                    )
            else:
                self._record_thinking_step(
                    'api_analysis_result',
                    'API调用决策',
                    f"我决定不调用API，原因是：{result['reason']}"
                )
            
            # 将思考步骤添加到结果中
            result['thinking_steps'] = self.thinking_steps
            return result
            
        except Exception as e:
            error_msg = f"API分析失败：{str(e)}"
            llm_logger.error(error_msg)
            
            # 记录错误的思考步骤
            self._record_thinking_step(
                'api_analysis_error',
                'API分析错误',
                error_msg
            )
            
            return {
                'should_call_api': False,
                'reason': error_msg,
                'plan': '无法生成API调用计划',
                'api_calls': [],
                'thinking_steps': self.thinking_steps
            }

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
            llm_logger.info("调用LLM：%s", messages)
            
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
            
            # 解析JSON
            return json.loads(result)
            
        except Exception as e:
            error_msg = f"生成JSON失败：{str(e)}"
            llm_logger.error(error_msg)
            return {
                'error': error_msg
            } 