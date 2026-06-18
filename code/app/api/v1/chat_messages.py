"""
对话消息 API 接口实现
参考 Dify API: https://docs.dify.ai/api-reference/chats/send-chat-message
"""

import json
import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from schema.chat_messages_model import (
    ChatMessageRequest,
    ChatMessageResponse,
    StopChatMessageRequest,
    StopResponse,
)
from utils.logger_operator import LoguruOperator
from service.chat_messages_service import chat_service

logger = LoguruOperator.init_app(name='chat_message')

router = APIRouter(prefix="/chat-messages", tags=["对话消息"])

# ==================== API 端点 ====================

@router.post("", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest
):
    """
    发送聊天消息
    
    支持 blocking 和 streaming 两种响应模式：
    - blocking: 完成后一次性返回完整响应
    - streaming: 使用 SSE 流式返回，适合长文本生成
    
    **请求示例**:
    ```json
    {
        "inputs": {"city": "Beijing"},
        "query": "今天天气怎么样？",
        "response_mode": "streaming",
        "conversation_id": "",
        "user": "user-123",
        "files": []
    }
    ```
    """
    logger.info(f'对话传入参数:{request}')
    # 创建任务
    task_id = await chat_service.create_task(
        user=request.user,
        conversation_id=request.conversation_id
    )
    
    if request.response_mode == "streaming":
        # 流式响应
        async def event_generator():
            yield ": stream-start\n\n"
            async for event in chat_service.generate_streaming_response(task_id, request):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    else:
        # 阻塞响应
        response = await chat_service.generate_blocking_response(task_id, request)
        return response


@router.post("/{task_id}/stop", response_model=StopResponse)
async def stop_chat_message(
    task_id: str,
    request: StopChatMessageRequest
):
    """
    停止消息生成
    
    仅对 streaming 模式有效，用于中断正在生成的回复。
    
    **路径参数**:
    - task_id: 任务ID（从 send_chat_message 响应中获取）
    
    **请求示例**:
    ```json
    {
        "user": "user-123"
    }
    ```
    """
    success = chat_service.stop_task(task_id, request.user)
    
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在或已完成")
    
    return StopResponse(result="success")



# 注意：APIRouter 不支持 exception_handler 装饰器
# 异常处理统一在 main.py 的全局异常处理器中完成
