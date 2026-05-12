# from langchain.messages import ToolMessage
from langgraph.prebuilt import ToolNode

from func.graph.tools.tool_used import tools

tool_node = ToolNode(tools)


# 下面是自定义的tool_node
# from graph.tools.tool_used import tools_by_name

# def tool_node(state: dict):
#     """Performs the tool call"""
#     print(f'tool node节点状态:\n{state}')

#     result = []
#     for tool_call in state["messages"][-1].tool_calls:
#         tool = tools_by_name[tool_call["name"]]
#         observation = tool.invoke(tool_call["args"])
#         result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
#     return {"messages": result}