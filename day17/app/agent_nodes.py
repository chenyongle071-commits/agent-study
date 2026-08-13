from app.agent_state import AgentState


TOOL_KEYWORDS = [
    "实验",
    "指标",
    "F1",
    "f1",
    "accuracy",
    "latency",
    "cost",
    "对比",
    "失败案例",
]

RAG_KEYWORDS = [
    "文档",
    "资料",
    "根据资料",
    "来源",
    "小乐",
    "张三",
    "身高",
]


def classify_question_node(state: AgentState) -> AgentState:
    question = state["question"]

    route = "normal"

    if any(keyword in question for keyword in TOOL_KEYWORDS):
        route = "tool"
    elif any(keyword in question for keyword in RAG_KEYWORDS):
        route = "rag"

    return {
        **state,
        "route": route,
    }