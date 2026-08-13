from langgraph.graph import END, START, StateGraph

from app.agent_nodes import classify_question_node
from app.agent_state import AgentState


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify_question", classify_question_node)

    graph.add_edge(START, "classify_question")
    graph.add_edge("classify_question", END)

    return graph.compile()


agent_graph = build_agent_graph()


def classify_question(user_id: int, question: str) -> AgentState:
    initial_state: AgentState = {
        "user_id": user_id,
        "question": question,
        "route": "normal",
    }

    result = agent_graph.invoke(initial_state)

    return result