"""业务办理情绪路由：angry → 安抚话术，否则 → 固定引导话术"""

from func.graph.state.state import WorkflowState


def business_emotion_router(state: WorkflowState) -> str:
    """
    业务办理分支内的情绪路由（对齐 Dify「条件分支 8」）

    angry → angry_reply（LLM 安抚 + 引导选业务）
    非 angry → business_reply（固定话术）
    """
    emotion = state.get("emotion", "neutral")
    if emotion == "angry":
        return "angry_reply"
    return "business_reply"
