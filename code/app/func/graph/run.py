"""
终端交互入口 — 直接运行 LangGraph Agent（无需启动 HTTP 服务）

用法（在仓库根目录）:
    .\\scripts\\run_agent.ps1
或:
    cd code\\app
    $env:PYTHONPATH = (Get-Location)
    python -m func.graph.run
"""

from __future__ import annotations

import asyncio
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from func.graph.build import build_graph
from func.graph.tools.tool_registry import format_tools_prompt_names

agent = build_graph()


async def stream_response(user_input: str, thread_id: str) -> None:
    config = {"configurable": {"thread_id": thread_id}}
    input_params = {
        "messages": [HumanMessage(content=user_input)],
        "query": user_input,
    }

    print("AI: ", end="", flush=True)
    printed_tool = False

    try:
        async for chunk in agent.astream(
            input_params,
            config=config,
            stream_mode="custom",
        ):
            if isinstance(chunk, str) and chunk:
                print(chunk, end="", flush=True)

        # 若 LLM 走了 tool call，custom 流可能没有最终文字 — 读 state 补全
        state = agent.get_state(config)
        messages = (state.values or {}).get("messages") or []
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage) and not printed_tool:
                print(f"\n  [tool {msg.name}] done", flush=True)
                printed_tool = True
            if isinstance(msg, AIMessage) and msg.content:
                # 流式已输出过则跳过
                break
    except Exception as e:
        print(f"\n[error] {e}", flush=True)
        return

    print("\n", flush=True)


async def main() -> None:
    print("=" * 56)
    print(" NewHuman 终端智能体")
    print(f" 工具: {format_tools_prompt_names()}")
    print("-" * 56)
    print(" 命令:")
    print("   /new     新对话")
    print("   /history 查看历史")
    print("   /exit    退出")
    print("=" * 56)

    current_thread = "terminal-default"

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if user_input.lower() in ("/exit", "exit", "quit"):
            print("再见!")
            break

        if user_input.lower() == "/new":
            current_thread = str(uuid.uuid4())
            print(f"新对话: {current_thread[:8]}...")
            continue

        if user_input.lower() == "/history":
            config = {"configurable": {"thread_id": current_thread}}
            state = agent.get_state(config)
            print("\n--- 历史 ---")
            for msg in (state.values or {}).get("messages") or []:
                if isinstance(msg, HumanMessage):
                    print(f"  You: {(msg.content or '')[:120]}")
                elif isinstance(msg, AIMessage):
                    tools = getattr(msg, "tool_calls", None) or []
                    if tools:
                        names = [t.get("name", "?") for t in tools]
                        print(f"  AI [tools: {', '.join(names)}]")
                    if msg.content:
                        print(f"  AI: {(msg.content or '')[:200]}")
                elif isinstance(msg, ToolMessage):
                    print(f"  [{msg.name}] {(msg.content or '')[:100]}...")
            continue

        if not user_input:
            continue

        await stream_response(user_input, current_thread)


if __name__ == "__main__":
    asyncio.run(main())
