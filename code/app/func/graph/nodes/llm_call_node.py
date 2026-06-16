

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Dict, Any
from config.llm_config import LLMConfig
from utils.llm_operator import LLMOperator

llm_config: LLMConfig = LLMConfig()

model = LLMOperator(
    llm_config
).get_llm()

from typing import AsyncIterator
from func.graph.state.state import WorkflowState  # 根据你的实际路径调整
import asyncio
from langgraph.config import get_stream_writer
from langgraph.config import get_config

from func.graph.writer.writer import create_event_writer

async def llm_streaming_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """异步 LLM 流式节点"""

    config = get_config()
    # print(f'config:{config}')
    full_response = ""

    writer = create_event_writer(
        state,
        node_name="llm_streaming_node"
    )
    
    async for chunk in model.astream(state.messages):
        token = chunk.content
        full_response += token
        # 一行发送 token
        writer.send_token(
            delta=token,
            full_text=full_response,
            state=state,
            metadata=chunk,
        )

    # 发送消息结束事件
    writer.send_message_end(state=state)

    return {
        "response": full_response
    }