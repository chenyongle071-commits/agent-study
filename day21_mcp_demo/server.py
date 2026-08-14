from mcp.server import MCPServer


mcp = MCPServer("experiment-agent-mcp-demo")


@mcp.tool()
def calculate_metric_delta(old_value: float, new_value: float) -> dict[str, float]:
    delta = new_value - old_value

    return {
        "old_value": old_value,
        "new_value": new_value,
        "delta": delta,
    }


@mcp.tool()
def compare_experiment_metric(
    experiment_a_id: int,
    experiment_b_id: int,
    metric_name: str,
    experiment_a_value: float,
    experiment_b_value: float,
) -> dict[str, object]:
    delta = experiment_b_value - experiment_a_value

    better_experiment_id = experiment_b_id
    if experiment_a_value > experiment_b_value:
        better_experiment_id = experiment_a_id

    return {
        "experiment_a_id": experiment_a_id,
        "experiment_b_id": experiment_b_id,
        "metric_name": metric_name,
        "experiment_a_value": experiment_a_value,
        "experiment_b_value": experiment_b_value,
        "delta": delta,
        "better_experiment_id": better_experiment_id,
    }


@mcp.tool()
def check_high_risk_action(question: str) -> dict[str, object]:
    high_risk_keywords = [
        "删除",
        "重新运行",
        "重跑",
        "修改实验配置",
    ]

    is_high_risk = any(keyword in question for keyword in high_risk_keywords)

    return {
        "question": question,
        "is_high_risk": is_high_risk,
        "requires_confirmation": is_high_risk,
    }


if __name__ == "__main__":
    mcp.run()