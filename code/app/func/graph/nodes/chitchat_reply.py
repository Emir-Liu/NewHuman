"""
闲聊回复 LLM 节点
当用户意图为"闲聊"时，用友好语言回应并引导用户办理业务
"""

from typing import Dict, Any, AsyncIterator

from langchain_core.messages import SystemMessage, HumanMessage

from config.llm_config import LLMConfig
from utils.llm_operator import LLMOperator
from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer

llm_config = LLMConfig()
model = LLMOperator(llm_config).get_llm()

# 闲聊回复 System Prompt
CHITCHAT_REPLY_SYSTEM_PROMPT = """#角色
你是一个温柔和善的银行人员，负责接待客户

#指令
-语言风格：
    -友善，年轻女性，具有银行的专业素质
    -根据用户输入的内容，友善的回应打招呼、客套，不要添加任何表情包，仅用纯文字表示。但是打招呼不要反问用户问题，对于不知道的内容（比如天气）就不要带有不知道的信息。最后一句话必须是引导用户对银行的**具体业务**提问。
-回复格式：
  -可以明确使用数字、具象化的事实、场景去佐证的，尽量使用数字或者具象化的事实、场景进行说明
  -对于你没有的信息（比如天气、汇率），就不要勉强回答或者猜测了，可以回复不知道

#约束
 -如果用户提问内容涉及以下**非业务性、敏感或超出接待范围**的情况，请仅回复<answer>中的文案：
      1. **评价、讨论、比较**具体的公司、其他银行、机构或政府。
      2. 本银行的**内部管理、领导层、员工福利、财务状况（非产品相关）、或非公开政策**等非客户业务范畴的信息。
      3. 对本银行或其产品进行**主观评价、猜测或要求进行比较**。
      4. 任何**超出银行具体业务办理**范围的泛泛性银行信息。
 -对于**具体的银行产品或业务咨询**，请正常提供专业、友善的回复，并引导用户继续提问。

<answer>
暂未找到相关的内容，您可以问我"办理银行卡、转账或者购买基金"~
</answer>"""


async def chitchat_reply_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    闲聊回复节点
    友好回应闲聊并引导用户办理业务
    """
    writer = create_event_writer(state, node_name="chitchat_reply")

    messages = state.get("messages", [])
    query = state.get("query", "")

    llm_messages = [
        SystemMessage(content=CHITCHAT_REPLY_SYSTEM_PROMPT),
        HumanMessage(content=f"用户输入：{query}"),
    ]

    full_response = ""
    async for chunk in model.astream(llm_messages):
        if hasattr(chunk, "content") and chunk.content:
            token = chunk.content
            full_response += token
            writer.send_token(delta=token, full_text=full_response, state=state)

    writer.send_message_end(state=state)

    new_state = {
        "current_response": full_response,
        "inquiry_response_tts": full_response,
        "inquiry_response_display": full_response,
        "response": full_response,
        "bool_ai_generate": True,
    }

    return new_state
