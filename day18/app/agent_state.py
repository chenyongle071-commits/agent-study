from typing import Literal, TypedDict
from typing_extensions import NotRequired


class AgentState(TypedDict):
    # 当前用户
    user_id: int

    # 用户问题
    question: str

    # 问题分类结果
    route: Literal["rag", "tool", "normal"]

    # 后续节点产生的结果
    answer: NotRequired[str]

    # RAG 返回的引用来源
    sources: NotRequired[list[dict[str, object]]]

    # 工具执行结果
    tool_result: NotRequired[dict[str, object]]

    # 工作流发生错误时记录原因
    error: NotRequired[str]