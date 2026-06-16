"""
Terminal 测试入口
用于在终端中测试 LangGraph 工作流
"""

import asyncio
from langchain_core.messages import (
    HumanMessage, 
    AIMessage, 
    ToolMessage, 
    BaseMessage
)

from func.graph.build import build_graph

agent = build_graph()


async def stream_response(user_input: str, thread_id: str = '测试'):
    """异步流式输出 AI 回复"""

    # 准备输入
    input_messages = [HumanMessage(content=user_input)]
    
    # 配置：指定 thread_id 以维持对话历史
    config = {
        "configurable": {
            "thread_id": thread_id  # 相同的 thread_id 会加载历史记录
        }
    }
    
    print("🤖 AI: ", end="", flush=True)
    
    input_params = {
        "messages": input_messages,
        "inputs": {
            "update_session": {
                "个人信息维护":"personalcustomer360"
            }
        }
    }

    # 异步流式执行
    full_response = ""
    async for chunk  in agent.astream(  # ← 改为 astream
        input_params,
        config=config,
        stream_mode=["custom"],
        version="v2"
    ):
        print(f'chunk: {chunk}')
    print()  # 换行


async def main():
    """异步主函数：终端交互界面"""
    print("=" * 50)
    print("🚀 LangGraph 智能助手（支持工具调用 & 记忆）")
    print("-" * 50)
    print("命令：")
    print("  • /new - 开启新对话")
    print("  • /history - 查看当前对话历史")
    print("  • /exit - 退出程序")
    print("=" * 50)
    
    # 当前对话线程 ID
    current_thread = "default_session"
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        # 处理命令
        if user_input.lower() in ['/exit', 'exit', 'quit']:
            print("👋 再见！")
            break
        
        elif user_input.lower() == '/new':
            import uuid
            current_thread = str(uuid.uuid4())
            print(f"🆕 已开启新对话，会话 ID: {current_thread[:8]}...")
            continue
        
        elif user_input.lower() == '/history':
            # 获取当前对话历史（同步方法，不需要 await）
            config = {"configurable": {"thread_id": current_thread}}
            state = agent.get_state(config)
            print("\n📜 对话历史：")
            for msg in state.values.get("messages", []):
                role = "👤" if isinstance(msg, HumanMessage) else "🤖"
                print(f"{role} {msg.content[:100]}...")
            continue
        
        elif not user_input:
            continue
        
        # 异步流式获取回复
        await stream_response(user_input, current_thread)  # ← 添加 await
            

    # while True:
    #     try:
    #         user_input = input("\n👤 You: ").strip()
            
    #         # 处理命令
    #         if user_input.lower() in ['/exit', 'exit', 'quit']:
    #             print("👋 再见！")
    #             break
            
    #         elif user_input.lower() == '/new':
    #             import uuid
    #             current_thread = str(uuid.uuid4())
    #             print(f"🆕 已开启新对话，会话 ID: {current_thread[:8]}...")
    #             continue
            
    #         elif user_input.lower() == '/history':
    #             # 获取当前对话历史（同步方法，不需要 await）
    #             config = {"configurable": {"thread_id": current_thread}}
    #             state = agent.get_state(config)
    #             print("\n📜 对话历史：")
    #             for msg in state.values.get("messages", []):
    #                 role = "👤" if isinstance(msg, HumanMessage) else "🤖"
    #                 print(f"{role} {msg.content[:100]}...")
    #             continue
            
    #         elif not user_input:
    #             continue
            
    #         # 异步流式获取回复
    #         await stream_response(user_input, current_thread)  # ← 添加 await
            
    #     except KeyboardInterrupt:
    #         print("\n👋 再见！")
    #         break
    #     except Exception as e:
    #         print(f"❌ 错误: {e}")

if __name__ == '__main__':
    # 使用 asyncio.run 运行异步主函数
    asyncio.run(main())
