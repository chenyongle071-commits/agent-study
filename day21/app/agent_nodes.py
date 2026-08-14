from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime, timezone
import time

from app.agent_state import AgentMessage, AgentState

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
    "删除",
    "重新运行",
    "重跑",
    "修改",
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

HIGH_RISK_KEYWORDS = [
    "删除",
    "重新运行",
    "重跑",
    "修改实验配置",
]


def is_high_risk_action(question: str) -> bool:
    return any(keyword in question for keyword in HIGH_RISK_KEYWORDS)

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
    question = state["question"]
    request_id = state.get("request_id")
    idempotency_records = state.get("idempotency_records", {})
    previous_logs = state.get("tool_logs", [])

    if request_id and request_id in idempotency_records:
        record = idempotency_records[request_id]
        answer = str(record.get("answer", "该请求已经执行过，直接返回历史结果。"))

        return {
            **state,
            "answer": answer,
            "tool_result": record.get("tool_result"),
            "confirmation_status": record.get("confirmation_status"),
            "idempotent_replay": True,
            "messages": append_turn_messages(state, answer),
        }

    if is_high_risk_action(question) and not state["confirmed"]:
        answer = "该操作可能修改或删除实验数据，需要人工确认后才能执行。"

        confirmation_log = {
            "event": "tool_waiting_for_human_confirmation",
            "tool_name": "mock_experiment_tool",
            "question": question,
        }

        return {
            **state,
            "answer": answer,
            "confirmation_status": "pending_confirmation",
            "tool_result": {
                "success": False,
                "executed": False,
                "requires_confirmation": True,
            },
            "tool_logs": [
                *previous_logs,
                confirmation_log,
            ],
            "messages": append_turn_messages(state, answer),
        }

    tool_result, current_logs = run_tool_with_retry(question)

    if tool_result["success"]:
        answer = f"这是工具节点处理的问题：{question}"
    else:
        answer = (
            f"工具调用失败，已经重试 {tool_result['attempts']} 次，"
            f"错误原因：{tool_result['error']}"
        )

    confirmation_status = None

    if is_high_risk_action(question):
        confirmation_status = "confirmed_and_executed"

    next_state: AgentState = {
        **state,
        "answer": answer,
        "confirmation_status": confirmation_status,
        "tool_result": tool_result,
        "tool_logs": [
            *previous_logs,
            *current_logs,
        ],
        "messages": append_turn_messages(state, answer),
    }

    if request_id:
        next_state["idempotency_records"] = {
            **idempotency_records,
            request_id: {
                "question": question,
                "answer": answer,
                "tool_result": tool_result,
                "confirmation_status": confirmation_status,
            },
        }

    return next_state

def build_idempotency_record(state: AgentState) -> dict[str, object]:
    return {
        "question": state["question"],
        "answer": state.get("answer"),
        "tool_result": state.get("tool_result"),
        "confirmation_status": state.get("confirmation_status"),
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

    if "触发超时" in question:
        time.sleep(5)

    return {
        "message": "这里后续会接入真实实验工具",
        "question": question,
    }


def run_tool_with_retry(
    question: str,
    max_retries: int = 2,
    timeout_seconds: float = 2,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    last_error = ""
    logs: list[dict[str, object]] = []

    for attempt in range(1, max_retries + 2):
        started_at = datetime.now(timezone.utc).isoformat()
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(run_mock_tool, question)

        try:
            result = future.result(timeout=timeout_seconds)
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
                "timed_out": False,
                "fallback_used": False,
            }, logs

        except FuturesTimeoutError:
            finished_at = datetime.now(timezone.utc).isoformat()
            last_error = f"工具执行超过 {timeout_seconds} 秒"

            logs.append(
                {
                    "event": "tool_attempt_timeout",
                    "tool_name": "mock_experiment_tool",
                    "attempt": attempt,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "error": last_error,
                }
            )

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

        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    logs.append(
        {
            "event": "tool_fallback_used",
            "tool_name": "mock_experiment_tool",
            "attempts": max_retries + 1,
            "error": last_error,
        }
    )

    return {
        "success": False,
        "attempts": max_retries + 1,
        "timed_out": "超过" in last_error,
        "fallback_used": True,
        "message": "工具暂时不可用，请稍后重试。",
        "error": last_error,
    }, logs