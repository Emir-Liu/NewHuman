"""
转账槽位提取节点
业务办理且意图含「个人账户转账」时，调用 LLM 提取 account/payee/amount
"""

from typing import Any, AsyncIterator, Dict, List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from config.llm_config import LLMConfig
from utils.llm_operator import LLMOperator
from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer

llm_config = LLMConfig()
model = LLMOperator(llm_config).get_llm()

TRANSFER_SLOT_SYSTEM_PROMPT = """# Role
你是一名银行智能客服系统的槽位提取专家。你的任务是从用户输入中准确提取结构化的槽位信息。

# Task: 槽位提取

所有可提取的槽位类型有：

1. **收款人账号** (account): 纯数字，默认为0
2. **收款人姓名** (payee): 字符串，默认是空字符串
3. **转账金额** (amount): 带2位小数的数值，默认为0

# 提取规则

1. **准确性优先**：只提取明确存在的信息，不要猜测或推断
2. **缺失处理**：如果某个槽位不存在，返回默认值

现在，请从以下用户输入中提取槽位信息"""


class TransferSlotsOutput(BaseModel):
    account: float = Field(default=0, description="收款人账号，纯数字")
    payee: str = Field(default="", description="收款人姓名，字符串")
    amount: float = Field(default=0, description="转账金额，带2位小数的数值")


def _format_slots(account: float, payee: str, amount: float) -> List[Dict[str, str]]:
    """对齐 Dify 槽位格式化逻辑"""
    slot_array: List[Dict[str, str]] = []
    if account is not None and account != 0.0:
        slot_array.append({"slot_name": "account", "slot_value": str(int(account))})
    if payee is not None and str(payee).strip():
        slot_array.append({"slot_name": "payee", "slot_value": str(payee).strip()})
    if amount is not None and amount != 0.0:
        slot_array.append({"slot_name": "amount", "slot_value": f"{amount:.2f}"})
    return slot_array


async def transfer_slot_extraction_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """转账槽位提取节点"""
    writer = create_event_writer(state, node_name="transfer_slot_extraction")

    query = state.get("query", "")
    parser = PydanticOutputParser(pydantic_object=TransferSlotsOutput)

    slot_prompt = ChatPromptTemplate.from_messages([
        ("system", TRANSFER_SLOT_SYSTEM_PROMPT + "\n\n{format_instructions}"),
        ("human", "{query}"),
    ]).partial(format_instructions=parser.get_format_instructions())

    slot_chain = slot_prompt | model | parser

    try:
        result: TransferSlotsOutput = await slot_chain.ainvoke({"query": query})
        slot_array = _format_slots(result.account, result.payee, result.amount)
    except Exception:
        slot_array = []

    new_state = {
        "bool_slot": 1 if slot_array else 0,
        "slot": slot_array,
    }

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
