

"""
对话消息服务层
处理聊天消息的核心业务逻辑，调用 LangGraph Agent 进行实际推理
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import HTTPException

from schema.chat_messages_model import ChatMessageRequest, ChatMessageResponse
from func.graph.agent_handler import agent_handler


# ==================== 服务层 ====================

class ChatService:
    """聊天服务"""
    
    def __init__(self):
        self.active_tasks: Dict[str, dict] = {}
    
    async def create_task(self, user: str, conversation_id: str) -> str:
        """创建任务"""
        task_id = str(uuid.uuid4())
        # 为每个任务创建独立的停止标志
        stop_event = asyncio.Event()
        self.active_tasks[task_id] = {
            "user": user,
            "conversation_id": conversation_id,
            "status": "running",
            "stop_event": stop_event,
            "created_at": datetime.now().timestamp(),
        }
        return task_id
    
    def stop_task(self, task_id: str, user: str) -> bool:
        """停止任务"""
        task = self.active_tasks.get(task_id)
        if not task:
            return False
        if task["user"] != user:
            raise HTTPException(status_code=403, detail="无权操作此任务")
        
        task["status"] = "stopped"
        # 触发停止信号
        task["stop_event"].set()
        return True
    
    def _is_stopped(self, task_id: str) -> bool:
        """检查任务是否已被停止"""
        task = self.active_tasks.get(task_id)
        if not task:
            return True
        return task["status"] == "stopped"
    
    def _get_stop_event(self, task_id: str) -> asyncio.Event:
        """获取任务的停止事件"""
        return self.active_tasks.get(task_id, {}).get("stop_event", asyncio.Event())
    
    async def generate_streaming_response(
        self,
        task_id: str,
        request: ChatMessageRequest
    ) -> Any:
        """
        生成流式响应（SSE 格式）
        
        调用 LangGraph Agent 的 stream 方法，将每个 token 封装为
        Dify 兼容的 SSE 事件字典。
        """
        message_id = str(uuid.uuid4())
        conversation_id = request.conversation_id or str(uuid.uuid4())
        created_at = int(datetime.now().timestamp())
        stop_event = self._get_stop_event(task_id)
        
        try:
            async for agent_event in agent_handler.stream_chat(
                user_input=request.query,
                conversation_id=conversation_id,
                stop_flag=stop_event,
            ):
                # 检查外部停止请求
                if self._is_stopped(task_id):
                    yield {
                        "event": "error",
                        "task_id": task_id,
                        "id": str(uuid.uuid4()),
                        "message": "Generation stopped by user",
                        "status": 400,
                        "code": "generation_stopped",
                        "created_at": int(datetime.now().timestamp()),
                    }
                    return
                
                if not agent_event:
                    continue

                if isinstance(agent_event, dict) and agent_event.get("type") == "tool_call":
                    yield {
                        "event": "tool_call",
                        "task_id": task_id,
                        "id": str(uuid.uuid4()),
                        "message_id": message_id,
                        "conversation_id": conversation_id,
                        "tool": agent_event.get("tool", ""),
                        "args": agent_event.get("args") or {},
                        "result": agent_event.get("result", ""),
                        "created_at": created_at,
                    }
                    continue

                # 发送消息片段
                yield {
                    "event": "message",
                    "task_id": task_id,
                    "id": str(uuid.uuid4()),
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "mode": "chat",
                    "answer": agent_event,
                    "created_at": created_at,
                }
            
            # 发送结束事件
            yield {
                "event": "message_end",
                "task_id": task_id,
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "metadata": {
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "prompt_unit_price": "0",
                        "completion_unit_price": "0",
                        "prompt_price": "0",
                        "completion_price": "0",
                        "total_price": "0",
                        "currency": "USD",
                        "latency": 0,
                    },
                    "retriever_resources": [],
                },
                "created_at": int(datetime.now().timestamp()),
            }
            
        except Exception as e:
            yield {
                "event": "error",
                "task_id": task_id,
                "id": str(uuid.uuid4()),
                "message": str(e),
                "status": 500,
                "code": "internal_error",
                "created_at": int(datetime.now().timestamp()),
            }
        
        finally:
            # 更新任务状态
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "completed"
    
    async def generate_blocking_response(
        self,
        task_id: str,
        request: ChatMessageRequest
    ) -> ChatMessageResponse:
        """
        生成阻塞响应
        
        调用 LangGraph Agent 的 invoke 方法，一次性返回完整回复。
        """
        message_id = str(uuid.uuid4())
        conversation_id = request.conversation_id or str(uuid.uuid4())
        created_at = int(datetime.now().timestamp())
        
        try:
            answer = await agent_handler.blocking_chat(
                user_input=request.query,
                conversation_id=conversation_id,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent 执行错误: {str(e)}")
        finally:
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "completed"
        
        return ChatMessageResponse(
            event="message",
            task_id=task_id,
            id=str(uuid.uuid4()),
            message_id=message_id,
            conversation_id=conversation_id,
            mode="chat",
            answer=answer,
            metadata={
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": len(answer),
                    "total_tokens": len(answer),
                    "prompt_unit_price": "0",
                    "completion_unit_price": "0",
                    "prompt_price": "0",
                    "completion_price": "0",
                    "total_price": "0",
                    "currency": "USD",
                    "latency": 0,
                },
                "retriever_resources": [],
            },
            created_at=created_at,
        )


# 全局服务实例
chat_service = ChatService()