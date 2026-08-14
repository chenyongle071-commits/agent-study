# Day21 MCP 概念与第三周验收

## 今日目标

- 了解 MCP 的工具暴露和调用概念
- 可选实现最小 MCP 工具服务
- 完成第三周验收：Agent 稳定选择并调用至少 3 个真实工具

## 为什么要做 Day21

Day15 到 Day20 已经实现了：

- 真实业务工具
- 工具参数校验
- 用户权限继承
- LangGraph 条件路由
- 多轮会话 Memory
- 工具失败重试
- 工具执行日志
- 超时、降级、人工确认、幂等性

Day21 是第三周收尾。

这一天有两个重点：

```text
理解 MCP 如何把工具暴露给 AI 应用
验证主项目里的 Agent 能稳定选择并调用真实工具
```

## 一、MCP 是什么

MCP 全称是 Model Context Protocol。

可以简单理解为：

```text
把工具、资源、Prompt 用统一协议暴露给 AI 应用
```

在普通 FastAPI 项目里，前端或后端通过 HTTP 调接口：

```text
前端 / 后端
-> FastAPI
-> Python 函数
```

在 MCP 里，AI Host 或 MCP Client 通过 MCP 协议发现和调用工具：

```text
AI Host / MCP Client
-> MCP Server
-> Python 工具函数
```

所以 MCP 的重点不是页面，也不是 REST API，而是：

```text
工具标准化暴露
工具 schema 可发现
工具可被 AI Host 调用
```

## 二、MCP Demo

本次单独创建了：

```text
D:\agent_study\day21_mcp_demo
```

这个目录不影响主项目，只用于理解 MCP。

### 安装依赖

使用了：

```powershell
python -m pip install "mcp[cli]"
python -m pip install uv
```

这里 `uv` 很重要。

MCP Inspector 启动 server 时使用了类似：

```text
uv run --with mcp==2.0.0 mcp run server.py
```

如果没有安装 `uv`，Inspector 页面会打开，但连接 server 会失败。

### MCP Server

`server.py` 中使用：

```python
from mcp.server import MCPServer

mcp = MCPServer("experiment-agent-mcp-demo")
```

然后用：

```python
@mcp.tool()
```

把普通 Python 函数暴露成 MCP 工具。

### 暴露的 3 个 MCP 工具

本次 MCP demo 暴露了：

```text
calculate_metric_delta
compare_experiment_metric
check_high_risk_action
```

它们分别对应：

- 计算指标变化
- 对比两个实验指标
- 判断高风险操作

### MCP Inspector 测试

启动命令：

```powershell
mcp dev server.py
```

启动后，MCP Inspector 成功连接：

```text
experiment-agent-mcp-demo
Connected
```

在 Inspector 的 Tools 页面中，成功看到并调用了 3 个工具。

这说明：

```text
Python 函数
-> MCP 工具
-> MCP Inspector 发现工具
-> MCP Inspector 调用工具
```

这条链路已经跑通。

## 三、主项目第三周验收

MCP demo 是为了理解“工具暴露”。

第三周真正的项目验收是：

```text
Agent 稳定选择并调用至少 3 个真实工具
```

所以本次又复制 Day20 为：

```text
D:\agent_study\day21
```

并在主项目里让 `/agent/run` 根据用户问题选择真实工具。

## 四、Agent 真实工具选择逻辑

本次在 `main.py` 中增加了问题解析和工具选择逻辑。

### 提取实验 ID

从问题中提取：

```text
实验1
实验2
```

得到：

```python
[1, 2]
```

### 提取指标

从问题中识别：

```text
accuracy
F1
latency
cost
```

也支持中文表达：

```text
准确率
延迟
更快
成本
```

### 工具选择规则

当前规则：

```text
问题包含 1 个实验 ID
-> get_experiment_tool

问题包含 2 个实验 ID + 1 个指标
-> compare_metric_tool

问题包含 2 个实验 ID + 多个指标
-> calculate_metric_changes_tool

问题包含 失败案例
-> query_failure_cases_tool
```

这不是最终形态，但足够完成本周验收。

后续可以把规则分类升级成 LLM 工具选择或 LangGraph 工具节点。

## 五、验收测试结果

### 1. 查询指定实验

请求：

```json
{
  "user_id": 1,
  "question": "查询实验1的信息",
  "thread_id": "tool-check-1"
}
```

成功选择：

```text
get_experiment_tool
```

返回了实验 1 的信息：

- name
- model_name
- dataset_name
- accuracy
- f1
- latency_ms
- cost
- status

### 2. 对比实验指标

请求：

```json
{
  "user_id": 1,
  "question": "对比实验1和实验2的F1",
  "thread_id": "tool-check-2"
}
```

成功选择：

```text
compare_metric_tool
```

返回了：

- experiment_a_id
- experiment_b_id
- metric_name
- a_value
- b_value
- delta
- better_experiment_id

### 3. 计算多个指标变化

请求：

```json
{
  "user_id": 1,
  "question": "计算实验1和实验2的accuracy和latency变化",
  "thread_id": "tool-check-3"
}
```

成功选择：

```text
calculate_metric_changes_tool
```

返回了多个指标变化：

- accuracy
- latency_ms

并给出：

- a_value
- b_value
- delta
- change_percent
- better_experiment_id

## 六、当前 Agent 工具链路

现在主项目中的工具调用链路是：

```text
用户问题
-> /agent/run
-> LangGraph 分类为 tool
-> 解析问题中的实验 ID 和指标
-> 选择真实工具
-> Pydantic 参数校验
-> 工具内部检查用户权限
-> 返回结构化工具结果
```

这说明 Agent 不只是返回“应该调用工具”，而是已经能真正调用业务工具。

## 当前限制

当前 Day21 的工具选择还是规则版。

限制包括：

- 只能识别固定表达方式
- 复杂自然语言可能解析不准
- 工具选择逻辑暂时写在 FastAPI 接口层
- LangGraph 的 `tool_node` 还没有直接接入真实工具

后续可以优化为：

```text
LLM 判断工具名和参数
-> Pydantic 校验参数
-> LangGraph tool_node 执行真实工具
-> 工具结果进入最终回答节点
```

## 我对 Day21 的理解

Day21 做了两件重要的事：

```text
MCP：理解工具如何被标准化暴露给 AI 应用
周验收：验证 Agent 能稳定选择并调用真实业务工具
```

MCP 解决的是“工具怎么开放给外部 AI Host 调用”。

主项目验收解决的是“Agent 自己能不能稳定使用工具完成任务”。

这两件事合起来，说明第三周已经从“写工具”推进到了“让 Agent 编排和调用工具”。
