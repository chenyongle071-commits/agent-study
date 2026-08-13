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


def rag_node(state: AgentState) -> AgentState:
    return {
        **state,
        "answer": f"这是 RAG 节点处理的问题：{state['question']}",
        "sources": [],
    }


def tool_node(state: AgentState) -> AgentState:
    tool_result = {
        "message": "这里后续会接入真实实验工具",
        "question": state["question"],
    }

    return {
        **state,
        "answer": f"这是工具节点处理的问题：{state['question']}",
        "tool_result": tool_result,
    }


def normal_node(state: AgentState) -> AgentState:
    return {
        **state,
        "answer": f"这是普通问答节点处理的问题：{state['question']}",
    }


def route_question(state: AgentState) -> str:
    return state["route"]