

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from config.llm_config import LLMConfig
from utils.llm_operator import LLMOperator

# from tools.calculator_tool import add, multiply, divide
# from tools.vectorstore_tool import add_document, delete_document, update_document, search_knowledge

from func.graph.tools.tool_used import tools

llm_config: LLMConfig = LLMConfig()

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
    # with open("soul/agent_memory_prompt.md", "r", encoding="utf-8") as f:
    #     return f.read()
    system_prompt = """
    你叫可可，是刘一鸣的助理，你是一个有用的助手，可以帮助刘一鸣完成工作。
    """
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