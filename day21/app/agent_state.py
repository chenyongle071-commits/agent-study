from typing import Literal, TypedDict
from typing_extensions import NotRequired


class AgentMessage(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class AgentState(TypedDict):
    # 当前用户
    user_id: int

    # 用户问题
    question: str

    # 问题分类结果
    route: Literal["rag", "tool", "normal"]

    # 多轮会话记忆
    messages: list[AgentMessage]

    # 是否经过人工确认
    confirmed: bool

    # 幂等请求 ID，用于避免重复执行高风险操作
    request_id: NotRequired[str]

    # 已处理过的幂等请求结果
    idempotency_records: NotRequired[dict[str, dict[str, object]]]

    idempotent_replay: NotRequired[bool]

    # 当前高风险操作的确认状态
    confirmation_status: NotRequired[str]

    # 后续节点产生的结果
    answer: NotRequired[str]

    # RAG 返回的引用来源
    sources: NotRequired[list[dict[str, object]]]

    # 工具执行结果
    tool_result: NotRequired[dict[str, object]]

    # 工具执行过程日志
    tool_logs: NotRequired[list[dict[str, object]]]

    # 工作流发生错误时记录原因
    error: NotRequired[str]