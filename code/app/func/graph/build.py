"""
LangGraph 工作流图构建

工作流流程：
    START
      ↓
    input_updates (参数初始化)
      ↓
    keyword_risk (金融风险检测)
      ↓ (risk_router)
      ├─ 有风险 → sensitive_reply → save_history → END
      ↓ (无风险)
    history_updates (历史记录管理)
      ↓
    injection_check (防注入检测)
      ↓ (injection_router)
      ├─ 有注入 → anti_injection_reply → save_history → END
      ↓ (无注入)
    rewrite_query (指代消解 LLM)
      ↓
    knowledge_retrieval (知识库检索)
      ↓
    intent_recognition (意图/情绪/业务识别 LLM)
      ↓
    parse_intent (解析意图结果)
      ↓ (intent_router)
      ├─ business → angry_reply / business_reply → [transfer_router]
      ├─ inquiry → inquiry_retrieval → inquiry_reply
      ├─ chitchat → chitchat_reply
      ├─ sensitive_word → sensitive_reply
      ├─ reject → reject_reply
      ├─ anti_injection → anti_injection_reply
      ↓
    save_history (保存对话历史)
      ↓
    END
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from func.graph.state.state import WorkflowState

# 节点导入
from func.graph.nodes.input_updates import input_updates_node
from func.graph.nodes.keyword_risk import keyword_risk_node
from func.graph.nodes.history_updates import history_updates_node
from func.graph.nodes.injection_check import injection_check_node
from func.graph.nodes.rewrite_query import rewrite_query_node
from func.graph.nodes.business_des_retrieval import business_des_retrieval_node
from func.graph.nodes.business_data_retrieval import business_data_retrieval_node
from func.graph.nodes.intent_recognition import intent_recognition_node
from func.graph.nodes.parse_intent import parse_intent_node
from func.graph.nodes.inquiry_retrieval import inquiry_retrieval_node
from func.graph.nodes.inquiry_reply import inquiry_reply_node
from func.graph.nodes.transfer_slot_extraction import transfer_slot_extraction_node
from func.graph.nodes.business_reply import business_reply_node
from func.graph.nodes.chitchat_reply import chitchat_reply_node
from func.graph.nodes.sensitive_reply import sensitive_reply_node
from func.graph.nodes.reject_reply import reject_reply_node
from func.graph.nodes.anti_injection_reply import anti_injection_reply_node
from func.graph.nodes.angry_reply import angry_reply_node
from func.graph.nodes.save_history import save_history_node

# 条件边导入
from func.graph.edges.intent_router import intent_router
from func.graph.edges.risk_router import risk_router
from func.graph.edges.injection_router import injection_router
from func.graph.edges.transfer_router import transfer_router

def build_graph():
    # # 现在新版本的图结构构建的写法
    # graph = (
    #     StateGraph(WorkflowState)
    #     .add_node(input_updates_node)
    #     .add_node(history_updates_node)
    #     .add_node(keyword_risk_node)
    #     .add_node(injection_check_node)
    #     .add_node(rewrite_query_node)
    #     .add_node(intent_recognition_node)
    #     .add_node(parse_intent_node)
    #     .add_node(inquiry_reply_node)
    #     .add_node(business_reply_node)
    #     .add_node(chitchat_reply_node)
    #     .add_node(sensitive_reply_node)
    #     .add_node(reject_reply_node)
    #     .add_node(anti_injection_reply_node)
    #     .add_node(angry_reply_node)
    #     .add_node(save_history_node)
    # )

    agent_builder = StateGraph(WorkflowState)

    # ==================== 注册节点 ====================

    # 预处理节点
    agent_builder.add_node("input_updates", input_updates_node)
    agent_builder.add_node("history_updates", history_updates_node)

    # 风险检测节点
    agent_builder.add_node("keyword_risk", keyword_risk_node)

    # 防注入节点
    agent_builder.add_node("injection_check", injection_check_node)

    # 指代消解节点
    agent_builder.add_node("rewrite_query", rewrite_query_node)

    # 知识库检索节点
    agent_builder.add_node("business_des_retrieval", business_des_retrieval_node)
    agent_builder.add_node("business_data_retrieval", business_data_retrieval_node)

    # 意图识别节点
    agent_builder.add_node("intent_recognition", intent_recognition_node)
    agent_builder.add_node("parse_intent", parse_intent_node)

    # 回复处理节点
    agent_builder.add_node("inquiry_retrieval", inquiry_retrieval_node)
    agent_builder.add_node("inquiry_reply", inquiry_reply_node)
    agent_builder.add_node("transfer_slot_extraction", transfer_slot_extraction_node)
    agent_builder.add_node("business_reply", business_reply_node)
    agent_builder.add_node("chitchat_reply", chitchat_reply_node)
    agent_builder.add_node("sensitive_reply", sensitive_reply_node)
    agent_builder.add_node("reject_reply", reject_reply_node)
    agent_builder.add_node("anti_injection_reply", anti_injection_reply_node)
    agent_builder.add_node("angry_reply", angry_reply_node)

    # 后处理节点
    agent_builder.add_node("save_history", save_history_node)

    # ==================== 连接边 ====================

    # START → input_updates
    agent_builder.add_edge(START, "input_updates")

    agent_builder.add_edge("input_updates", "history_updates")

    # input_updates → keyword_risk
    agent_builder.add_edge("history_updates", "keyword_risk")

    # keyword_risk → [risk_router] → history_updates / sensitive_reply
    agent_builder.add_conditional_edges(
        "keyword_risk",
        risk_router,
        {
            "injection_check": "injection_check",
            "parse_intent": "parse_intent",
        }
    )

    # injection_check → [injection_router] → rewrite_query / anti_injection_reply
    agent_builder.add_conditional_edges(
        "injection_check",
        injection_router,
        {
            "rewrite_query": "rewrite_query",
            "parse_intent": "parse_intent",
        }
    )

    # rewrite_query → knowledge_retrieval → intent_recognition
    agent_builder.add_edge("rewrite_query", "business_des_retrieval")
    agent_builder.add_edge("business_des_retrieval", "business_data_retrieval")
    agent_builder.add_edge("business_data_retrieval", "intent_recognition")

    # intent_recognition → parse_intent
    agent_builder.add_edge("intent_recognition", "parse_intent")

    # parse_intent → [intent_router] → 各回复节点
    agent_builder.add_conditional_edges(
        "parse_intent",
        intent_router,
        {
            "inquiry_retrieval": "inquiry_retrieval",
            "angry_reply": "angry_reply",
            "business_reply": "business_reply",
            "chitchat_reply": "chitchat_reply",
            "sensitive_reply": "sensitive_reply",
            "reject_reply": "reject_reply",
            "anti_injection_reply": "anti_injection_reply",
        }
    )

    agent_builder.add_edge("inquiry_retrieval", "inquiry_reply")

    agent_builder.add_conditional_edges(
        "angry_reply",
        transfer_router,
        {
            "transfer_slot_extraction": "transfer_slot_extraction",
            "save_history": "save_history",
        },
    )

    agent_builder.add_conditional_edges(
        "business_reply",
        transfer_router,
        {
            "transfer_slot_extraction": "transfer_slot_extraction",
            "save_history": "save_history",
        },
    )

    # 所有回复节点 → save_history（统一出口）
    agent_builder.add_edge("inquiry_reply", "save_history")
    agent_builder.add_edge("transfer_slot_extraction", "save_history")
    agent_builder.add_edge("chitchat_reply", "save_history")
    agent_builder.add_edge("sensitive_reply", "save_history")
    agent_builder.add_edge("reject_reply", "save_history")
    agent_builder.add_edge("anti_injection_reply", "save_history")
    agent_builder.add_edge("angry_reply", "save_history")

    # save_history → END
    agent_builder.add_edge("save_history", END)

    # 编译
    checkpointer = MemorySaver()
    agent = agent_builder.compile(checkpointer=checkpointer)

    return agent
