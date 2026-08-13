from app.agent_state import AgentMessage, AgentState
from datetime import datetime, timezone

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


def append_turn_messages(
    state: AgentState,
    answer: str,
) -> list[AgentMessage]:
    messages = state.get("messages", [])

    return [
        *messages,
        {
            "role": "user",
            "content": state["question"],
        },
        {
            "role": "assistant",
            "content": answer,
        },
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
    answer = f"这是 RAG 节点处理的问题：{state['question']}"

    return {
        **state,
        "answer": answer,
        "sources": [],
        "messages": append_turn_messages(state, answer),
    }


def tool_node(state: AgentState) -> AgentState:
    tool_result, current_logs = run_tool_with_retry(state["question"])
    previous_logs = state.get("tool_logs", [])

    if tool_result["success"]:
        answer = f"这是工具节点处理的问题：{state['question']}"
    else:
        answer = f"工具调用失败，已经重试 {tool_result['attempts']} 次，错误原因：{tool_result['error']}"

    return {
        **state,
        "answer": answer,
        "tool_result": tool_result,
        "tool_logs": [
            *previous_logs,
            *current_logs,
        ],
        "messages": append_turn_messages(state, answer),
    }


def normal_node(state: AgentState) -> AgentState:
    answer = f"这是普通问答节点处理的问题：{state['question']}"

    return {
        **state,
        "answer": answer,
        "messages": append_turn_messages(state, answer),
    }


def route_question(state: AgentState) -> str:
    return state["route"]


def run_mock_tool(question: str) -> dict[str, object]:
    if "触发失败" in question:
        raise RuntimeError("模拟工具调用失败")

    return {
        "message": "这里后续会接入真实实验工具",
        "question": question,
    }


def run_tool_with_retry(
    question: str,
    max_retries: int = 2,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    last_error = ""
    logs = []

    for attempt in range(1, max_retries + 2):
        started_at = datetime.now(timezone.utc).isoformat()

        try:
            result = run_mock_tool(question)
            finished_at = datetime.now(timezone.utc).isoformat()

            logs.append(
                {
                    "event": "tool_attempt_succeeded",
                    "tool_name": "mock_experiment_tool",
                    "attempt": attempt,
                    "started_at": started_at,
                    "finished_at": finished_at,
                }
            )

            return {
                **result,
                "success": True,
                "attempts": attempt,
            }, logs

        except Exception as error:
            finished_at = datetime.now(timezone.utc).isoformat()
            last_error = str(error)

            logs.append(
                {
                    "event": "tool_attempt_failed",
                    "tool_name": "mock_experiment_tool",
                    "attempt": attempt,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "error": last_error,
                }
            )

    logs.append(
        {
            "event": "tool_failed_after_retries",
            "tool_name": "mock_experiment_tool",
            "attempts": max_retries + 1,
            "error": last_error,
        }
    )

    return {
        "success": False,
        "attempts": max_retries + 1,
        "error": last_error,
    }, logs