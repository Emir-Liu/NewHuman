"""
更新会话历史记录
管理消息列表长度，限制在 num_history 轮以内
"""

from typing import Dict, Any, AsyncIterator

from func.graph.state.state import WorkflowState  # 根据你的实际路径调整
from func.graph.writer.writer import create_event_writer


async def history_updates_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    历史记录管理节点
    限制消息列表长度，确保不超出记忆轮次
    """
    print(f'state:{state}')
    writer = create_event_writer(
        state,
        node_name="history_updates_node"
    )

    messages = state.get('messages', [])
    query = messages[-1].content
    num_history = state.get('num_history')

    if len(messages) > num_history*2:
        messages = messages[-num_history*2:]

    new_state = {
        'query': query,
        'messages': messages
    }

    writer.send_node_end(updates=new_state, state=new_state)
    return new_state

    
