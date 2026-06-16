"""金融风险路由：检测到风险关键词 → sensitive_reply"""

from func.graph.state.state import WorkflowState


def risk_router(state: WorkflowState) -> str:
    """
    金融风险路由
    bool_risk == 0 → injection_check (继续)
    bool_risk != 0 → sensitive_reply
    """
    bool_risk = state.get("bool_risk", 0)
    if bool_risk == 0:
        return "injection_check"
    return "parse_intent"
