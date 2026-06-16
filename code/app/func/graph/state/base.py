"""
所有工作流均需要使用的状态基类
"""

from langchain_core.messages import AnyMessage
from typing import Annotated, Dict, Any, List
from typing_extensions import TypedDict
import operator


class MessagesStateBase(TypedDict):
    # 消息列表，用于追加新消息
    messages: list[AnyMessage]

    # 输入参数
    query: str  # 用户对话内容
    inputs: Dict[str, Any]  # 输入字典

    # 输出参数
    response: str  # 最终响应内容
    outputs: Dict[str, Any]  # 输出字典

