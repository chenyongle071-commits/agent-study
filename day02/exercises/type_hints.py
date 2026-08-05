# 类型标注练习：模拟 Agent 项目里的“指标计算”和“用户消息构造”。


#定义一个函数，接收旧指标和新指标，两个都是小数，最后返回一个小数。
def calculate_metric_delta(old_value: float, new_value: float) -> float:
    """计算新旧指标的差值"""
    return new_value - old_value


def build_user_message(user_id: int, content: str) -> dict[str, int | str]:
    """把用户 ID 和用户输入内容整理成一个消息字典。"""
    message = {
        "user_id": user_id,
        "role": "user",
        "content": content,
    }

    return message


if __name__ == "__main__":
    delta = calculate_metric_delta(0.72, 0.81)
    message = build_user_message(1, "模型 F1 有提升吗？")

    print(delta)
    print(message)