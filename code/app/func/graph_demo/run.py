from langchain_core.messages import (
    HumanMessage, 
    AIMessage, 
    ToolMessage, 
    BaseMessage
)

from func.graph.build import build_graph
from func.graph.show_graph import save_graph_img

agent = build_graph()

# save_graph_img(agent)

def single_message():
    # Invoke
    from langchain_core.messages import HumanMessage
    messages = [HumanMessage(content="Add 3 and 4.")]
    messages = agent.invoke({"messages": messages})
    for m in messages["messages"]:
        m.pretty_print()

    # Token 级别的流式输出
    print("Token 级流式输出:")


def stream_response(user_input: str, thread_id: str = '测试'):
    """流式输出 AI 回复"""
    # 准备输入
    input_messages = [HumanMessage(content=user_input)]
    
    # 配置：指定 thread_id 以维持对话历史
    config = {
        "configurable": {
            "thread_id": thread_id  # 相同的 thread_id 会加载历史记录
        }
    }
    
    print("🤖 AI: ", end="", flush=True)
    
    # 流式执行
    for chunk, metadata in agent.stream(
        {"messages": input_messages},
        config=config,
        stream_mode="messages"  # 流式返回消息内容
    ):
        if hasattr(chunk, 'content'):
            print(chunk.content, end="", flush=True)
    
    print()  # 换行


def main():
    """主函数：终端交互界面"""
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
        try:
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
                # 获取当前对话历史
                config = {"configurable": {"thread_id": current_thread}}
                state = agent.get_state(config)
                print("\n📜 对话历史：")
                for msg in state.values.get("messages", []):
                    role = "👤" if isinstance(msg, HumanMessage) else "🤖"
                    print(f"{role} {msg.content[:100]}...")
                continue
            
            elif not user_input:
                continue
            
            # 流式获取回复
            stream_response(user_input, current_thread)
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == '__main__':
    # single_message()

    # stream_chat()

    main()