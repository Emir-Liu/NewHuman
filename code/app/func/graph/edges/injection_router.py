"""防注入路由：检测到注入攻击 → anti_injection_reply"""

from func.graph.state.state import WorkflowState


def injection_router(state: WorkflowState) -> str:
    """
    防注入路由
    bool_injection == 0 → rewrite_query (继续)
    bool_injection != 0 → anti_injection_reply
    """
    bool_injection = state.get("bool_injection", 0)
    if bool_injection == 0:
        return "rewrite_query"
    return "parse_intent"
