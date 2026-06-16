
from typing import Union, List, Dict, Any

from func.graph.state.base import MessagesStateBase


class WorkflowState(MessagesStateBase):
    # 金融风险检测
    risk_keyword_list: List[str]  # 金融风险关键词列表
    bool_risk: int  # 是否触发风险: 0=无风险, 1=有风险

    # 防注入检测
    injection_keyword_list: List[str]  # 防注入关键词列表
    bool_injection: int  # 是否触发防注入: 0=无风险, 1=有风险

    # 业务描述知识库检索
    business_des_kb_top_k: int  # 业务描述知识库检索数量
    business_des_kb_id: str  # 业务描述知识库ID

    # 业务数据知识库检索
    business_data_kb_top_k: int  # 业务数据知识库检索数量
    business_data_kb_id: str  # 业务数据知识库ID

    # 咨询 QA 知识库检索（chunk_mode=qa：Q 匹配、A 作答）
    inquiry_kb_top_k: int  # 咨询 QA 知识库检索数量
    inquiry_kb_id: str  # 咨询专用 QA 知识库 UUID（为空时回退 label=inquiry）
    inquiry_score_threshold: float  # 咨询直出 KB 内容的相似度阈值
    inquiry_rag_result: List[Dict[str, Any]]  # 咨询知识库原始检索结果
    inquiry_knowledge_result: str  # 咨询知识库格式化 context
    # knowledge_result: str  # 兼容 Dify 命名，与 inquiry_knowledge_result 同步
    bool_ai_generate: bool  # 是否由 LLM 生成回复

    # 意图识别
    business_mapping: Dict[str, str]  # 业务名称→业务代码映射
    intent_mapping: Dict[str, str]  # 意图分类→意图代码映射
    emotion: str  # 情绪: happy/sad/angry/neutral
    reasoning: str  # 推理过程
    business_status: str  # 用户意图分类结果: business/inquiry/chitchat/sensitive_word/reject/anti_injection
    business: List[Dict[str, Any]]  # 业务意图列表

    # 指代消解
    rewrite: str  # 用户问题重构（含指代消解）

    # 业务描述知识库检索结果
    business_des_knowledge_result: str  # 业务描述知识库检索结果
    # 业务数据知识库检索结果
    business_data_knowledge_result: str  # 业务数据知识库检索结果

    # 槽位提取
    bool_slot: int  # 是否进行槽位提取
    slot_list: List[Dict[str, Any]]  # 槽位列表
    slot: List[Dict[str, Any]]  # 槽位提取结果

    # 会话变量更新
    update_session: Dict[str, Any]  # 外部传入的会话变量更新
    num_history: int  # 记忆轮次
