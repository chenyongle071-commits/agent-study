# Day25 Agent 工具调用评估

## 今日目标

- 评估工具选择准确率
- 评估工具参数正确率
- 评估任务完成率

## 今日完成

Day25 不再继续增加新的 Agent 功能，而是开始评估 Agent 的工具调用能力。

核心问题是：

```text
用户提出问题
-> Agent 是否选对工具
-> Agent 是否抽对参数
-> 最终任务是否完成
```

这一步的意义是把 Agent 的表现变成可以量化的数据，而不是只靠手动测试和感觉判断。

## 文件说明

```text
day25_eval_tools/
├── eval_tools.jsonl
├── eval_tool_runner.py
├── eval_tool_results.jsonl
└── README.md
```

### eval_tools.jsonl

这是工具评估题库。

每一行是一条 JSON 数据，包含：

```text
id：测试题编号
user_id：用户 ID
question：用户问题
expected_tool：预期应该调用的工具
expected_params：预期应该抽取的参数
expected_task：预期完成的任务
```

示例：

```json
{"id":"tool_004","user_id":1,"question":"对比实验1和实验2的F1","expected_tool":"compare_metric_tool","expected_params":{"experiment_a_id":1,"experiment_b_id":2,"metric_name":"f1"},"expected_task":"比较两个实验的F1指标"}
```

### eval_tool_runner.py

这是评估脚本。

它会读取 `eval_tools.jsonl`，逐条调用后端接口：

```text
POST http://127.0.0.1:8000/agent/run
```

然后对比：

```text
expected_tool    和 actual_tool
expected_params  和 actual_params
任务是否有有效返回
```

最后生成：

```text
eval_tool_results.jsonl
```

### eval_tool_results.jsonl

这是评估结果文件。

每一行记录一条测试结果，包括：

```text
工具是否选对
参数是否正确
任务是否完成
接口耗时
后端响应内容
```

最后一行是汇总结果。

## 评估指标

### 1. 工具选择准确率

判断 Agent 有没有选对工具。

比如：

```text
查询实验1的信息
```

预期工具是：

```text
get_experiment_tool
```

如果实际工具也是 `get_experiment_tool`，则工具选择正确。

### 2. 工具参数正确率

判断 Agent 有没有抽对工具参数。

比如：

```text
对比实验1和实验2的F1
```

预期参数是：

```json
{
  "experiment_a_id": 1,
  "experiment_b_id": 2,
  "metric_name": "f1"
}
```

如果实际返回的参数包含这些值，则参数正确。

### 3. 任务完成率

判断这次请求是否完成了有效处理。

在当前版本里，只要接口没有严重错误，并且返回了有效 answer、tool_result 或明确业务结果，就认为任务完成。

## 后端配合改动

为了让评估脚本能判断参数是否正确，后端 `/agent/run` 的 `tool_result` 中增加了结构化字段：

```json
{
  "selected_tool": "compare_metric_tool",
  "selected_params": {
    "user_id": 1,
    "experiment_a_id": 1,
    "experiment_b_id": 2,
    "metric_name": "f1"
  },
  "raw_result": {}
}
```

这样评估脚本不需要猜测 Agent 做了什么，而是直接读取实际工具和实际参数。

## 运行方式

先启动 Day24 后端：

```powershell
cd D:\agent_study\day24
py -m uvicorn app.main:app --reload
```

然后另开一个终端运行评估：

```powershell
cd D:\agent_study\day25_eval_tools
python eval_tool_runner.py
```

## 本次评估结果

本次共测试 20 道工具调用问题。

```text
总测试数：20
工具选择正确：20
参数正确：20
任务完成：20
```

汇总指标：

```text
工具选择准确率：100%
工具参数正确率：100%
任务完成率：100%
```

对应 summary：

```json
{
  "total": 20,
  "tool_accuracy": 1.0,
  "parameter_accuracy": 1.0,
  "task_completion_rate": 1.0,
  "tool_correct_count": 20,
  "params_correct_count": 20,
  "task_completed_count": 20
}
```

## 结果观察

普通数据库工具调用耗时较低，通常在几十毫秒以内。

文档检索类工具耗时更高，例如搜索 RAG、embedding、Top-K 相关内容时，需要访问检索逻辑和向量库，所以耗时明显高于普通工具。

本次 100% 说明 Agent 在这 20 道标准题上通过了评估，但不代表真实场景已经完全稳定。

后续还需要继续加入更多复杂测试：

```text
问题换一种说法
省略实验编号
中英文混合
指标别名
恶意请求
缺少参数
用户无权限
无关问题
```

## 我的理解

Day25 的重点不是让 Agent 回答更多问题，而是检查它是否真的可靠。

一个可用的 Agent 不能只看最终回答，还要看中间过程：

```text
有没有选对工具
有没有传对参数
有没有拿到正确结果
有没有完成用户任务
```

评估脚本相当于给 Agent 做自动化考试。以后每次改工具逻辑、路由逻辑或参数抽取逻辑，都可以重新跑一遍评估，防止新代码把原来能工作的能力改坏。
