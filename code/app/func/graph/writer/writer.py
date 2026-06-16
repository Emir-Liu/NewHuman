"""
统一的事件写入器
所有节点通过此模块发送流式事件，保证输出格式一致。
"""
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from langgraph.config import get_stream_writer


class EventWriter:
    """
    LangGraph 流式事件写入器
    
    封装 writer 调用，提供统一的发送接口：    
    - send_token()    : 发送 LLM token（流式输出）
    - send_message_end() : 发送消息结束事件
    - send_node_end() : 发送节点完成事件
    """
    
    def __init__(
        self,
        conversation_id: str = "",
        message_id: str = "",
        node_name: str = "",
    ):
        self._writer = get_stream_writer()
        self.conversation_id = conversation_id
        self.message_id = message_id or str(uuid.uuid4())
        self.node_name = node_name
    
    # ============ 序列化辅助 ============
    
    @staticmethod
    def _safe_state(state: Dict[str, Any]) -> Dict[str, Any]:
        """排除不可序列化的字段（如 messages）"""
        safe = {}
        for key, value in state.items():
            # if key == "messages":
            #     safe[key] = f"[{len(value)} 条消息]" if value else "[]"
            # else:
            try:
                json.dumps(value)
                safe[key] = value
            except (TypeError, ValueError):
                safe[key] = str(value)
        return safe
    
    # ============ 事件发送 ============
    
    def send_token(
        self,
        delta: str,
        full_text: str = "",
        state: Optional[Dict[str, Any]] = None,
        metadata: Any = None,
    ):
        """发送 LLM token 事件"""
        self._writer({
            "id": str(uuid.uuid4()),
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "event": "message",
            "created_at": int(datetime.now().timestamp()),
            "data": {
                "delta": delta,
                "full_text": full_text,
                "metadata": metadata,
            },
            "state": self._safe_state(state) if state else {},
        })
    
    def send_message_end(self, state: Optional[Dict[str, Any]] = None):
        """发送消息结束事件"""
        self._writer({
            "id": str(uuid.uuid4()),
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "event": "message_end",
            "created_at": int(datetime.now().timestamp()),
            "data": {},
            "state": self._safe_state(state) if state else {},
        })
    
    def send_node_end(
        self,
        updates: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None,
    ):
        """发送节点完成事件"""
        self._writer({
            "id": str(uuid.uuid4()),
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "event": "node_end",
            "created_at": int(datetime.now().timestamp()),
            "data": {
                "node_name": self.node_name,
                "updates": updates,
            },
            "state": self._safe_state(state) if state else {},
        })


# ==================== 工厂函数 ====================

def create_event_writer(
    state: Dict[str, Any],
    node_name: str = "",
) -> EventWriter:
    """
    从 state 和 config 创建 EventWriter
    
    在节点中使用：
        writer = create_event_writer(state, node_name="llm_call")
        writer.send_token(delta="你好")
    """
    from langgraph.config import get_config
    
    config = get_config()
    conversation_id = config.get("configurable", {}).get("thread_id", "")
    
    return EventWriter(
        conversation_id=conversation_id,
        node_name=node_name,
    )
