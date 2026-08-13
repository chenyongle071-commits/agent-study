from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent_nodes import (
    classify_question_node,
    normal_node,
    rag_node,
    route_question,
    tool_node,
)
from app.agent_state import AgentState


checkpointer = MemorySaver()


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify_question", classify_question_node)
    graph.add_node("rag", rag_node)
    graph.add_node("tool", tool_node)
    graph.add_node("normal", normal_node)

    graph.add_edge(START, "classify_question")

    graph.add_conditional_edges(
        "classify_question",
        route_question,
        {
            "rag": "rag",
            "tool": "tool",
            "normal": "normal",
        },
    )

    graph.add_edge("rag", END)
    graph.add_edge("tool", END)
    graph.add_edge("normal", END)

    return graph.compile(checkpointer=checkpointer)


agent_graph = build_agent_graph()


def classify_question(user_id: int, question: str) -> AgentState:
    initial_state: AgentState = {
        "user_id": user_id,
        "question": question,
        "route": "normal",
        "messages": [],
        "confirmed": False,
    }

    result = agent_graph.invoke(
        initial_state,
        config={
            "configurable": {
                "thread_id": f"classify-{user_id}",
            }
        },
    )

    return result

def run_agent(
    user_id: int,
    question: str,
    thread_id: str,
    confirmed: bool,
    request_id: str | None,
) -> AgentState:
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    snapshot = agent_graph.get_state(config)
    previous_messages = []

    previous_idempotency_records = {}

    if snapshot.values:
        previous_messages = snapshot.values.get("messages", [])
        previous_idempotency_records = snapshot.values.get("idempotency_records", {})

    initial_state: AgentState = {
        "user_id": user_id,
        "question": question,
        "route": "normal",
        "messages": previous_messages,
        "confirmed": confirmed,
        "request_id": request_id,
        "idempotency_records": previous_idempotency_records,
        "idempotent_replay": False,
    }

    result = agent_graph.invoke(
        initial_state,
        config=config,
    )

    return result

def get_agent_state(thread_id: str) -> AgentState | None:
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    snapshot = agent_graph.get_state(config)

    if not snapshot.values:
        return None

    return snapshot.values