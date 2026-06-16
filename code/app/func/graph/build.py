"""
LangGraph 工作流图构建

工作流流程：
    START
      ↓

    END
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from func.graph.state.state import WorkflowState

# 节点导入


# 条件边导入


def build_graph():

    agent_builder = StateGraph(WorkflowState)

    # ==================== 注册节点 ====================


    # ==================== 连接边 ====================


    # 编译
    checkpointer = MemorySaver()
    agent = agent_builder.compile(checkpointer=checkpointer)

    return agent
