"""业务办理后路由：含个人账户转账时进入槽位提取"""

from func.graph.state.state import WorkflowState


def transfer_router(state: WorkflowState) -> str:
    business_names = [
        b.get("business_name", "")
        for b in state.get("business", [])
    ]
    if "个人账户转账" in business_names:
        return "transfer_slot_extraction"
    return "save_history"
