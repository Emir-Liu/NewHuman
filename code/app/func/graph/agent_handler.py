"""
Agent Handler - 将 LangGraph Agent 与 API 服务层桥接

提供：
- 流式对话 (stream_chat)：yield SSE 事件字典，供 chat_messages_service 使用
- 阻塞对话 (blocking_chat)：返回完整回答
- 会话变量查询 (get_conversation_variables)：读取 LangGraph state 作为会话变量

用法：
    from func.graph.agent_handler import agent_handler
    async for event in agent_handler.stream_chat("你好", "conv-123"):
        ...
"""

import asyncio
import json
import uuid
import time
from typing import AsyncGenerator, Dict, Any, Optional, List

from langchain_core.messages import HumanMessage, AIMessage

from func.graph.build import build_graph


def _safe_serialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """安全序列化 state，处理不可 JSON 序列化的字段（如 messages）"""
    safe = {}
    for key, value in state.items():
        # # messages 字段包含 LangChain 消息对象，转换为可读格式
        # if key == "messages" and isinstance(value, list):
        #     safe_msgs = []
        #     for msg in value:
        #         if isinstance(msg, BaseMessage):
        #             safe_msgs.append({
        #                 "role": msg.type,
        #                 "content": msg.content[:200] if isinstance(msg.content, str) else str(msg.content)[:200],
        #             })
        #         elif isinstance(msg, dict):
        #             safe_msgs.append(msg)
        #         else:
        #             safe_msgs.append(str(msg))
        #     safe[key] = safe_msgs
        # else:
        try:
            json.dumps(value)
            safe[key] = value
        except (TypeError, ValueError):
            safe[key] = str(value)
    return safe


class AgentHandler:
    """LangGraph Agent 处理器，封装 Agent 的调用逻辑"""

    def __init__(self, agent=None):
        """
        初始化处理器

        Args:
            agent: 可注入已有的 agent 实例（用于测试），不传则自动构建
        """
        self._agent = agent

    @property
    def agent(self):
        """懒加载 agent，首次访问时构建"""
        if self._agent is None:
            self._agent = build_graph()
        return self._agent

    async def stream_chat(
        self,
        user_input: str,
        conversation_id: str,
        stop_flag: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式对话

        遍历 LangGraph agent.stream 的每个 chunk，yield 标准事件字典。
        流结束后自动获取最终 state 并通过 workflow_finished 事件返回。

        Args:
            user_input: 用户输入文本
            conversation_id: 会话 ID（用作 LangGraph thread_id）
            stop_flag: 可选 asyncio.Event，当被 set 时停止生成

        Yields:
            dict: 事件字典，最后会 yield workflow_finished 事件包含完整 state
        """
        config = {"configurable": {"thread_id": conversation_id}}
        input_messages = [HumanMessage(content=user_input)]

        full_answer = ""

        async for chunk in self.agent.astream(
            {"messages": input_messages},
            config=config,
            stream_mode="custom",
        ):
            # # 检查停止标志
            # if stop_flag and stop_flag.is_set():
            #     break

            # if hasattr(chunk, "content") and chunk.content:
            #     delta = chunk.content
            #     full_answer += delta

                yield chunk

    async def blocking_chat(
        self,
        user_input: str,
        conversation_id: str,
    ) -> str:
        """
        阻塞式对话

        使用 agent.ainvoke 一次性获取完整回复。

        Args:
            user_input: 用户输入文本
            conversation_id: 会话 ID（用作 LangGraph thread_id）

        Returns:
            str: AI 的完整回复文本
        """
        config = {"configurable": {"thread_id": conversation_id}}
        input_messages = [HumanMessage(content=user_input)]
        result = await self.agent.ainvoke(
            {"messages": input_messages},
            config=config,
        )

        # 提取最后一条 AI 消息的内容作为回复
        answer = result.get("response", "")
        return answer

    def get_conversation_variables(
        self,
        conversation_id: str,
    ) -> list:
        """
        获取会话变量（来自 LangGraph state）

        直接读取 state 中的所有字段并原样返回，不做任何映射。

        Args:
            conversation_id: 会话 ID（用作 LangGraph thread_id）

        Returns:
            list[dict]: 会话变量列表
        """
        config = {"configurable": {"thread_id": conversation_id}}

        try:
            state = self.agent.get_state(config)
            # print
        except Exception:
            return []

        if state is None or state.values is None or not state.values:
            return []

        values = state.values
        now = int(time.time())

        created_at = now
        if hasattr(state, "created_at") and state.created_at:
            try:
                created_at = int(state.created_at.timestamp())
            except Exception:
                created_at = now

        def _ensure_short_id(key: str) -> str:
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{conversation_id}:{key}"))

        def _serialize(val: Any) -> str:
            """将任意值序列化为字符串"""
            if val is None:
                return ""
            if isinstance(val, (str, int, float, bool)):
                return str(val)
            try:
                return json.dumps(val, ensure_ascii=False, default=str)
            except Exception:
                return str(val)

        def _infer_type(val: Any) -> str:
            """推断值的类型"""
            if val is None:
                return "string"
            if isinstance(val, bool):
                return "boolean"
            if isinstance(val, int):
                return "number"
            if isinstance(val, float):
                return "number"
            if isinstance(val, str):
                return "string"
            if isinstance(val, (list, tuple)):
                return "array"
            if isinstance(val, dict):
                return "object"
            return "string"

        variables = []
        for key, raw_value in values.items():
            value_type = _infer_type(raw_value)
            value = _serialize(raw_value)

            variables.append({
                "id": _ensure_short_id(key),
                "name": key,
                "value_type": value_type,
                "value": value,
                "description": "",
                "created_at": created_at,
                "updated_at": now,
            })

        return variables


# ==================== 全局单例 ====================

agent_handler = AgentHandler()
