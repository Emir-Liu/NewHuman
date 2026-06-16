"""
会话服务层
处理会话变量相关的业务逻辑
"""

import time
from typing import Optional, List

from schema.conversations_model import (
    ConversationVariable,
    ConversationVariableListResponse,
)
from func.graph.agent_handler import agent_handler


class ConversationsService:
    """会话服务"""

    def get_variables(
        self,
        conversation_id: str,
        user: Optional[str] = None,
        last_id: Optional[str] = None,
        limit: int = 20,
        variable_name: Optional[str] = None,
    ) -> ConversationVariableListResponse:
        """
        获取会话变量列表（从 LangGraph state 读取）

        Args:
            conversation_id: 会话 ID
            user: 用户标识符
            last_id: 游标分页的起始 ID
            limit: 每页条数（1-100，默认 20）
            variable_name: 按变量名过滤

        Returns:
            ConversationVariableListResponse
        """
        # 从 LangGraph state 获取原始变量字典
        raw_variables = agent_handler.get_conversation_variables(conversation_id)

        # 转为 ConversationVariable 列表
        variables: List[ConversationVariable] = [
            ConversationVariable(**v) for v in raw_variables
        ]

        # 按变量名过滤
        if variable_name:
            variables = [v for v in variables if v.name == variable_name]

        # 游标分页
        if last_id:
            start_idx = 0
            for i, v in enumerate(variables):
                if v.id == last_id:
                    start_idx = i + 1
                    break
            variables = variables[start_idx:]

        # 截取 limit 条
        has_more = len(variables) > limit
        variables = variables[:limit]

        return ConversationVariableListResponse(
            limit=limit,
            has_more=has_more,
            data=variables,
        )


# 全局服务实例
conversations_service = ConversationsService()
