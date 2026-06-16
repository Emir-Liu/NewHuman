"""意图路由：根据 business_status 分发到不同回复分支"""

from func.graph.edges.business_emotion_router import business_emotion_router
from func.graph.state.state import WorkflowState


def intent_router(state: WorkflowState) -> str:
    """
    根据 business_status 字段进行意图路由

    路由规则（优先级从高到低）：
    - sensitive_word → sensitive_reply
    - anti_injection → anti_injection_reply
    - business + 有业务个数 → business_emotion_router（angry / business_reply）
    - business + 无业务个数 → reject_reply
    - inquiry → inquiry_retrieval
    - chitchat → chitchat_reply
    - reject → reject_reply
    - 默认 → chitchat_reply
    """
    business_status = state.get("business_status", "reject")
    business = state.get("business", [])
    num_business_intent = len(business)

    if business_status == "sensitive_word":
        return "sensitive_reply"

    if business_status == "anti_injection":
        return "anti_injection_reply"

    if business_status == "business":
        if num_business_intent >= 1:
            return business_emotion_router(state)
        return "reject_reply"

    if business_status == "inquiry":
        return "inquiry_retrieval"

    if business_status == "chitchat":
        return "chitchat_reply"

    if business_status == "reject":
        return "reject_reply"

    return "chitchat_reply"
