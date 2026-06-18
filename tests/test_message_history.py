"""message_history 单元测试。"""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from func.graph.utils.message_history import trim_to_last_turns


def test_trim_keeps_last_three_human_turns():
    messages = []
    for i in range(5):
        messages.append(HumanMessage(content=f"q{i}"))
        messages.append(AIMessage(content=f"a{i}"))

    trimmed = trim_to_last_turns(messages, 3)
    texts = [m.content for m in trimmed if isinstance(m, HumanMessage)]
    assert texts == ["q2", "q3", "q4"]


def test_trim_preserves_tool_messages_in_turn():
    messages = [
        HumanMessage(content="old"),
        AIMessage(content="", tool_calls=[{"name": "x", "args": {}, "id": "1"}]),
        ToolMessage(content="result", tool_call_id="1", name="x"),
        AIMessage(content="done old"),
        HumanMessage(content="new"),
        AIMessage(content="answer new"),
    ]
    trimmed = trim_to_last_turns(messages, 1)
    assert len(trimmed) == 2
    assert trimmed[0].content == "new"
    assert trimmed[1].content == "answer new"


def test_trim_zero_means_no_limit():
    messages = [HumanMessage(content="a"), AIMessage(content="b")]
    assert trim_to_last_turns(messages, 0) == messages
