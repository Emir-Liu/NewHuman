from langchain_core.messages import AnyMessage
from typing import Annotated
from typing_extensions import TypedDict
import operator

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int