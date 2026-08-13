from typing import Literal, TypedDict


class AgentState(TypedDict):
    user_id: int
    question: str
    route: Literal["rag", "tool", "normal"]