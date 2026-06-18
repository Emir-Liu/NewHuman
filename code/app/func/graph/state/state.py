from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class WorkflowState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    query: str
    inputs: dict
    response: str
    outputs: dict
