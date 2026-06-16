"""
会话变量 API 数据模型
参考 Dify API: https://docs.dify.ai/api-reference/conversations/list-conversation-variables
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 列表响应模型 ====================

class ConversationVariable(BaseModel):
    """会话变量"""
    id: str = Field(..., description="变量唯一 ID")
    name: str = Field(..., description="变量名称")
    value_type: str = Field(..., description="变量值类型（如 string, number 等）")
    value: str = Field(..., description="变量当前值")
    description: str = Field(default="", description="变量描述")
    created_at: int = Field(..., description="创建时间戳（Unix 秒）")
    updated_at: int = Field(..., description="更新时间戳（Unix 秒）")


class ConversationVariableListResponse(BaseModel):
    """会话变量列表响应"""
    limit: int = Field(..., description="本次返回的实际条数上限")
    has_more: bool = Field(..., description="是否还有更多数据")
    data: List[ConversationVariable] = Field(default_factory=list, description="变量对象数组")
