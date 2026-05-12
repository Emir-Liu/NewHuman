
from langchain.messages import SystemMessage

from langchain.messages import SystemMessage, HumanMessage, AIMessage

from config.llm_config import LLMConfig
from config.soul_config import SoulConfig
from utils.llm_operator import LLMOperator

# from tools.calculator_tool import add, multiply, divide
# from tools.vectorstore_tool import add_document, delete_document, update_document, search_knowledge

from func.graph.tools.tool_used import tools

llm_config: LLMConfig = LLMConfig()
soul_config: SoulConfig = SoulConfig()

model = LLMOperator(
    llm_config
).get_llm()


# Augment the LLM with tools
# tools = [add, multiply, divide]
# tools = [add_document, delete_document, update_document, search_knowledge]
# tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


def load_system_prompt():
    """从soul文件夹加载系统提示词"""
    soul_content = ''
    try:
        with open(soul_config.soul_path, "r", encoding="utf-8") as f:
            soul_content = f.read()
    except Exception as e:
        print(f'加载soul文件夹失败: {e}')

    system_prompt = f"{soul_content}"
    return system_prompt

def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""
    # print(f'llm_call节点状态:\n{state}')
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(content=load_system_prompt())
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }