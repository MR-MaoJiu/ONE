"""
聊天管理器模块
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from services.llm_service import LLMService
from core.storage.memory_storage import MemoryStorage
from core.snapshot.snapshot_manager import SnapshotManager
from utils.logger import get_logger
import asyncio
import httpx
import json

chat_logger = get_logger('chat')

class ChatManager:
    """聊天管理器"""
    
    def __init__(self, llm_service: LLMService, storage: MemoryStorage, snapshot_manager: SnapshotManager):
        """
        初始化聊天管理器
        
        Args:
            llm_service: LLM服务实例
            storage: 存储实例
            snapshot_manager: 快照管理器实例
        """
        self.llm_service = llm_service
        self.storage = storage
        self.snapshot_manager = snapshot_manager
        self.history = []
        self.http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        chat_logger.info("聊天管理器初始化完成")
    
    async def chat(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理用户输入，生成回复
        
        Args:
            query: 用户输入
            context: 上下文信息，包含API调用相关设置
            
        Returns:
            Dict[str, Any]: 包含回复文本和思考步骤的字典
        """
        try:
            chat_logger.info("收到用户输入：%s", query)
            
            # 准备上下文
            context = context or {}
            context.update({
                'history': self.history,
            })
            
            # 获取相关记忆
            relevant_snapshots = await self.snapshot_manager.get_relevant_snapshots(query)
            if relevant_snapshots:
                context['relevant_memories'] = [
                    {
                        'content': snapshot.content,
                        'score': score,
                        'timestamp': snapshot.timestamp.isoformat()
                    }
                    for snapshot, score in relevant_snapshots
                ]
            
            # 如果启用了API调用
            if context.get('enable_api_call') and context.get('api_docs'):
                chat_logger.info("API调用已启用，正在分析API文档")
                # 添加API调用相关的思考步骤
                thinking_steps = []
                thinking_steps.append({
                    'type': 'api_feature_check',
                    'description': 'API功能状态',
                    'result': '已启用API调用功能，我将尝试通过调用API来获取所需信息。'
                })
                
                # 让LLM分析API文档和用户需求
                api_analysis = await self.llm_service.analyze_api(
                    query=query,
                    api_docs=context['api_docs'],
                    context=context
                )
                
                # 添加API分析的思考步骤
                if 'thinking_steps' in api_analysis:
                    thinking_steps.extend(api_analysis['thinking_steps'])
                
                # 如果需要调用API
                if api_analysis.get('should_call_api', False):
                    api_calls = api_analysis.get('api_calls', [])
                    api_results = []
                    
                    for i, call in enumerate(api_calls, 1):
                        thinking_steps.append({
                            'type': 'api_request',
                            'description': f'发送API请求 #{i}',
                            'result': f"""正在发送API请求：
- 接口：{call.get('url', '')}
- 方法：{call.get('method', 'GET')}
- 目的：{call.get('purpose', '未指定')}
- 参数：{json.dumps(call.get('params', {}), ensure_ascii=False, indent=2)}
- 数据：{json.dumps(call.get('data', {}), ensure_ascii=False, indent=2)}"""
                        })
                        
                        try:
                            # 执行API调用
                            response = await self.http_client.request(
                                method=call.get('method', 'GET'),
                                url=call['url'],
                                headers=call.get('headers', {}),
                                params=call.get('params', {}),
                                json=call.get('data', {})
                            )
                            
                            # 解析响应
                            result = response.json() if response.text else None
                            api_results.append({
                                'success': True,
                                'data': result,
                                'status_code': response.status_code
                            })
                            
                            thinking_steps.append({
                                'type': 'api_response',
                                'description': f'API响应 #{i}',
                                'result': f"""收到API响应：
- 状态码：{response.status_code}
- 响应数据：{json.dumps(result, ensure_ascii=False, indent=2)}
- 数据分析：正在解析API返回的数据，以提取有用信息。"""
                            })
                            
                        except Exception as e:
                            error_msg = f"API调用失败：{str(e)}"
                            chat_logger.error(error_msg)
                            api_results.append({
                                'success': False,
                                'error': str(e)
                            })
                            
                            thinking_steps.append({
                                'type': 'api_error',
                                'description': f'API错误 #{i}',
                                'result': f"""API调用出错：
- 错误信息：{str(e)}
- 错误分析：
  1. 可能是网络连接问题
  2. API地址可能不正确
  3. 请求参数可能有误
  4. API服务器可能暂时不可用
- 解决方案：我将尝试其他方式回答您的问题"""
                            })
                    
                    # 添加API调用总结
                    success_count = sum(1 for r in api_results if r['success'])
                    total_count = len(api_results)
                    thinking_steps.append({
                        'type': 'api_summary',
                        'description': 'API调用总结',
                        'result': f"""API调用情况：
- 总计调用：{total_count} 个API
- 成功调用：{success_count} 个
- 失败调用：{total_count - success_count} 个
- 后续处理：我将根据获取到的API数据为您生成答案。"""
                    })
                    
                    # 更新上下文，加入API调用结果
                    context['api_results'] = api_results
            
            # 生成最终回复
            result = await self.llm_service.chat(query, context)
            
            # 如果之前有API调用的思考步骤，添加到结果中
            if 'thinking_steps' in locals():
                result['thinking_steps'] = thinking_steps + result.get('thinking_steps', [])
            
            # 更新历史记录
            self._add_to_history(query, result['response'])
            
            # 异步处理存储操作
            asyncio.create_task(self._process_storage(query, result['response']))
            
            return result
            
        except Exception as e:
            chat_logger.error("处理对话失败：%s", str(e), exc_info=True)
            return {
                'response': "抱歉，处理您的输入时出现了错误。",
                'thinking_steps': []
            }
    
    async def _process_storage(self, query: str, response: str):
        """
        异步处理存储操作
        
        Args:
            query: 用户输入
            response: AI回复
        """
        try:
            # 保存记忆
            memory = await self.storage.save_memory(
                content=query,
                metadata={'is_user': True}
            )
            await self.storage.save_memory(
                content=response,
                metadata={'is_user': False}
            )
            
            # 创建快照
            await self.snapshot_manager.create_snapshot(memory)
            
            chat_logger.info("存储操作完成")
            
        except Exception as e:
            chat_logger.error("存储操作失败：%s", str(e))
    
    def _add_to_history(self, query: str, response: str):
        """添加到历史记录"""
        self.history.extend([
            {
                'content': query,
                'timestamp': datetime.now().isoformat(),
                'is_user': True
            },
            {
                'content': response,
                'timestamp': datetime.now().isoformat(),
                'is_user': False
            }
        ])
        
        # 保持历史记录在限定长度内
        if len(self.history) > 20:
            self.history = self.history[-20:]
    
    async def get_all_memories(self) -> List[Dict[str, Any]]:
        """获取所有记忆"""
        try:
            memories = await self.storage.get_all_memories()
            return [memory.to_dict() for memory in memories]
        except Exception as e:
            chat_logger.error("获取记忆失败：%s", str(e))
            return []
    
    async def get_all_snapshots(self) -> List[Dict[str, Any]]:
        """获取所有快照"""
        try:
            snapshots = await self.storage.get_all_snapshots()
            return [snapshot.to_dict() for snapshot in snapshots]
        except Exception as e:
            chat_logger.error("获取快照失败：%s", str(e))
            return []
    
    async def clear_all(self):
        """清空所有记忆和历史记录"""
        try:
            # 清空数据库
            await self.storage.clear_all()
            # 清空历史记录
            self.history.clear()
            chat_logger.info("所有数据已清空")
        except Exception as e:
            chat_logger.error("清空数据失败：%s", str(e))
            raise 