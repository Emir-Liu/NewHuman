"""
根据输入参数，修改会话变量
"""

from typing import Dict, Any, AsyncIterator

from func.graph.state.state import WorkflowState  # 根据你的实际路径调整
from func.graph.writer.writer import create_event_writer
from func.graph.params.params import (
    num_history_default,
    business_mapping_default,
    risk_keyword_list_default,
    injection_keyword_list_default,
    intent_mapping_default,
    business_des_kb_top_k_default,
    business_des_kb_id_default,
    business_data_kb_top_k_default,
    business_data_kb_id_default,
    inquiry_kb_top_k_default,
    inquiry_kb_id_default,
    inquiry_score_threshold_default,
)


async def input_updates_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    输入参数初始化会话变量节点
    """
    writer = create_event_writer(state, node_name="input_updates")

    inputs = state.get('inputs',{})
    update_session = inputs.get('update_session',{})
    new_state = {}
    if update_session:
        new_state = {
            'business_mapping': update_session
        }
    else:
        new_state = {
            'business_mapping': business_mapping_default
        }

    new_state.update(
        {
            'num_history': num_history_default,
            'risk_keyword_list': risk_keyword_list_default,
            'injection_keyword_list': injection_keyword_list_default,
            'intent_mapping': intent_mapping_default,
            'business_des_kb_top_k': business_des_kb_top_k_default,
            'business_des_kb_id': business_des_kb_id_default,
            'business_data_kb_top_k': business_data_kb_top_k_default,
            'business_data_kb_id': business_data_kb_id_default,
            'inquiry_kb_top_k': inputs.get('inquiry_kb_top_k', inquiry_kb_top_k_default),
            'inquiry_kb_id': inputs.get('inquiry_kb_id', inquiry_kb_id_default),
            'inquiry_score_threshold': inputs.get(
                'inquiry_score_threshold', inquiry_score_threshold_default
            ),
            'bool_slot': 0,
            'slot_list': [],
            'slot': [],
            'bool_ai_generate': False,
            'inquiry_rag_result': [],
            'inquiry_knowledge_result': '',
            'knowledge_result': '',
        }
    )

    writer.send_node_end(updates=new_state, state=new_state)

    return new_state


    