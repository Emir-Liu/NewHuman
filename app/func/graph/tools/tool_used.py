from func.graph.tools.vectorstore_tool import add_document, delete_document, update_document, search_knowledge
# from func.graph.tools.terminal_tool import execute_command
# from func.graph.tools.calculator_tool import add, multiply, divide

tools = [add_document, delete_document, update_document, search_knowledge]
# tools = [add, multiply, divide]

tools_by_name = {tool.name: tool for tool in tools}

# 创建 ToolExecutor，自动处理工具路由
# tool_executor = ToolExecutor(tools)