# 异常处理练习：模拟把用户输入的指标值转换成数字。就是把用户发来的数据变成计算机能解析的数字形式，因为用户发来的信息都是字符串


def parse_metric_value(raw_value: str) -> float:
    """把字符串形式的指标值转换成 float。"""
    try:
        return float(raw_value)
    except ValueError:
        raise ValueError(f"指标值必须是数字，当前输入是：{raw_value}")


if __name__ == "__main__":
    values = ["0.91", "abc", "120"]

    for value in values:
        try:
            parsed = parse_metric_value(value)
            print(f"解析成功：{parsed}")
        except ValueError as error:
            print(f"解析失败：{error}")

#如果你不会异常处理，程序可能直接崩掉。
#如果你会异常处理，就可以返回清楚的错误：
#{
#  "error": "实验不存在",
#  "experiment_id": 123
#}