# 装饰器练习：模拟记录一个工具函数的执行耗时。
#装饰器不是简单“调用一个通用行为”，而是把某个函数包起来，让这个函数在执行前、执行后，或者执行出错时，自动附加一段通用逻辑。

import time
from collections.abc import Callable
from typing import Any


#比如没有装饰器时，每个工具都要这样写:          再写一个工具，又重复：
#start_time = time.time()                     start_time = time.time()          
#result = query_experiment(...)               result = compare_metrics(...)
#latency_ms = ...                             latency_ms = ...
#print(...)                                   print(...)
#复用通用逻辑
#减少重复代码
#让核心业务代码更干净
#让函数行为更清晰
def log_latency(func: Callable[..., Any]) -> Callable[..., Any]:
    """给函数增加耗时日志。"""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        latency_ms = (time.time() - start_time) * 1000
        print(f"{func.__name__} took {latency_ms:.2f} ms")
        return result

    return wrapper


@log_latency
def mock_tool_call(query: str) -> str:
    """模拟一个 Agent 工具调用。"""
    time.sleep(0.2)
    return f"查询完成：{query}"


if __name__ == "__main__":
    result = mock_tool_call("对比实验 A 和实验 B 的 F1")
    print(result)