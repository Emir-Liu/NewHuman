"""
会话级别 API 接口
参考 Dify API: https://docs.dify.ai/api-reference/conversations/list-conversation-variables
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from schema.conversations_model import ConversationVariableListResponse
from service.conversations_service import conversations_service

router = APIRouter(prefix="/conversations", tags=["会话管理"])


# ==================== API 端点 ====================

@router.get(
    "/{conversation_id}/variables",
    response_model=ConversationVariableListResponse,
)
async def list_conversation_variables(
    conversation_id: str,
    user: Optional[str] = Query(default=None, description="用户标识符"),
    last_id: Optional[str] = Query(default=None, description="上一页最后一条记录ID（游标分页）"),
    limit: int = Query(default=20, ge=1, le=100, description="每页返回条数（1-100）"),
    variable_name: Optional[str] = Query(
        default=None,
        min_length=1,
        max_length=255,
        description="按变量名过滤",
    ),
):
    """
    获取会话变量列表

    返回指定对话关联的所有变量及其当前值，支持游标分页和按名称过滤。

    **路径参数**:
    - conversation_id: 会话 ID

    **查询参数示例**:
    ```
    ?user=user-123&last_id=xxx&limit=20&variable_name=user_preference
    ```

    **响应格式**:
    ```json
    {
        "limit": 20,
        "has_more": false,
        "data": [
            {
                "id": "uuid",
                "name": "user_preference",
                "value_type": "string",
                "value": "dark_mode",
                "description": "用户偏好设置",
                "created_at": 1705407629,
                "updated_at": 1705411229
            }
        ]
    }
    ```
    """
    try:
        return conversations_service.get_variables(
            conversation_id=conversation_id,
            user=user,
            last_id=last_id,
            limit=limit,
            variable_name=variable_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
