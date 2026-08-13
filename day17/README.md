# Day17 LangGraph 问题分类节点

## 今日目标

- 学习 LangGraph 的 State、Node、Edge
- 实现一个问题分类节点
- 把用户问题分成三类：RAG、工具、普通问答
- 提供 `/agent/classify` 接口进行测试

## 为什么要做 Day17

前面已经分别完成了：

- RAG：能根据文档资料回答问题
- Tool Calling：能查询实验、对比指标、检索失败案例
- 普通聊天：能直接调用大模型回答

但是一个真正的 Agent 不能只会一个固定流程。

它需要先判断：

```text
用户这个问题应该走哪条路？
```

所以 Day17 的核心不是让模型马上回答，而是先实现一个最小工作流：

```text
用户问题
-> LangGraph 状态流转
-> 问题分类节点
-> 输出 route
```

## State 是什么

State 可以理解为 Agent 工作流里的“状态包”。

本次在 `app/agent_state.py` 中定义了：

```python
class AgentState(TypedDict):
    user_id: int
    question: str
    route: Literal["rag", "tool", "normal"]
```

它保存了工作流运行时需要携带的数据：

- `user_id`：当前用户是谁
- `question`：用户问了什么
- `route`：这个问题应该走哪条路线

后续 LangGraph 的每个节点都会读取或修改这个 State。

## Node 是什么

Node 是工作流里的一个处理步骤。

本次在 `app/agent_nodes.py` 中实现了：

```python
def classify_question_node(state: AgentState) -> AgentState:
```

这个节点负责根据关键词判断问题类型。

当前规则：

- 命中实验、指标、F1、accuracy、latency、cost、对比、失败案例：走 `tool`
- 命中文档、资料、根据资料、来源、小乐、张三、身高：走 `rag`
- 都没命中：走 `normal`

这里先用关键词规则，是为了让流程清晰、可测试。

后面可以升级成让 LLM 做分类，或者使用更复杂的分类器。

## Edge 是什么

Edge 是节点之间的连接线，决定流程从哪里走到哪里。

本次在 `app/agent_graph.py` 中定义了最小图：

```text
START
-> classify_question
-> END
```

也就是说，现在的图只有一个节点：问题分类。

它的作用是先把 LangGraph 的基本结构跑通。

## 接口

新增接口：

```text
POST /agent/classify
```

请求示例：

```json
{
  "user_id": 1,
  "question": "对比实验1和实验2的F1"
}
```

返回示例：

```json
{
  "user_id": 1,
  "question": "对比实验1和实验2的F1",
  "route": "tool"
}
```

## 测试结果

### 1. RAG 问题

问题：

```text
小乐身高多少？
```

结果：

```text
route = rag
```

说明这个问题需要查资料或文档。

### 2. 工具问题

问题：

```text
对比实验1和实验2的F1
```

结果：

```text
route = tool
```

说明这个问题需要调用实验工具，而不是让模型直接编答案。

### 3. 普通问答

问题：

```text
你好，你是谁？
```

结果：

```text
route = normal
```

说明这个问题不需要查文档，也不需要调用业务工具，可以走普通大模型回答。

## 我对 Day17 的理解

Day17 是从“单个功能”进入“Agent 工作流”的第一步。

之前的 RAG、工具、普通聊天都像是单独的能力模块。

LangGraph 的作用是把这些模块组织起来，让 Agent 根据问题状态决定下一步怎么走。

目前实现的是最小版本：

```text
先分类，再决定路线
```

后续 Day18 会在这个基础上继续扩展：

```text
识别问题
-> 判断使用 RAG / 工具 / 普通问答
-> 执行对应节点
-> 检查结果是否充分
-> 生成最终回答
```

这一步虽然简单，但很关键，因为它是 Agent 从“能调用功能”走向“能编排流程”的开始。
