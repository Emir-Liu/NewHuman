"""
LangGraph 工作流图构建

ReAct 流程：
    START -> llm_call -> (tool_calls?) -> tools -> llm_call -> ... -> END
"""
from loguru import logger
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from func.graph.edges.should_continue import should_continue
from func.graph.nodes.llm_call import llm_call
from func.graph.nodes.tool_node import tool_node
from func.graph.state.state import WorkflowState

from config.langfuse_config import LangfuseConfig

langfuse_config = LangfuseConfig()

def _create_langfuse_handler():
    """创建 Langfuse callback；OpenTelemetry 版本不一致时降级为 None。"""
    try:
        from langfuse.langchain import CallbackHandler

        return CallbackHandler()
    except ImportError as exc:
        logger.warning(
            "Langfuse 已启用但初始化失败（多为 opentelemetry 版本不一致）: {}。"
            "请执行: pip install -r requirements.txt",
            exc,
        )
        return None

def build_graph():
    agent_builder = StateGraph(WorkflowState)

    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tools", tool_node)

    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call",
        should_continue,
        {"tools": "tools", "end": END},
    )
    agent_builder.add_edge("tools", "llm_call")

    checkpointer = MemorySaver()

    agent = agent_builder.compile(checkpointer=checkpointer)
    if langfuse_config.enabled:
        langfuse_handler = _create_langfuse_handler()
        if langfuse_handler is not None:
            agent = agent.with_config({"callbacks": [langfuse_handler]})

    return agent
