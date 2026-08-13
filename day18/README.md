# Day18 Agent 主工作流与 Checkpoint

## 今日目标

- 实现 Agent 主工作流
- 实现条件路由
- 实现 Checkpoint 和状态持久化
- 验证同一个 `thread_id` 可以读取到工作流状态

## 为什么要做 Day18

Day17 只是先判断问题该走哪条路：

- RAG
- 工具
- 普通问答

但真正的 Agent 不能停在“判断”。

它还要继续执行：

```text
用户提问
-> 分类
-> 路由到对应节点
-> 执行节点
-> 返回结果
```

所以 Day18 的重点是把“分类器”变成“工作流”。

## 主工作流是什么

现在的工作流大概是：

```text
START
-> classify_question
-> rag / tool / normal
-> END
```

这意味着：

- 先判断问题类型
- 再进入对应节点
- 最后输出结果

这就是 Agent 的最小可用主链路。

## 条件路由是什么

条件路由的意思是：

```text
根据 state["route"] 决定下一步走哪条边
```

本次在 `app/agent_graph.py` 里实现了：

- `rag` -> `rag_node`
- `tool` -> `tool_node`
- `normal` -> `normal_node`

这样就不再是固定流程，而是能按问题类型动态走不同分支。

## State 扩展了什么

Day17 的 State 只有：

- `user_id`
- `question`
- `route`

Day18 扩展成可以继续携带更多信息：

- `answer`
- `sources`
- `tool_result`
- `error`

这样每个节点都可以把自己的结果塞回 State，后面的节点还能继续使用。

## Checkpoint 是什么

Checkpoint 可以理解为“流程存档”。

本次使用的是 `MemorySaver`，它会记住：

- 这次执行用了哪个 `thread_id`
- 当前工作流的状态是什么
- 上一次运行留下了什么数据

你可以把它理解成：

```text
同一个 thread_id
-> 可以找回同一条会话状态
```

这对多轮会话、调试、恢复现场都很重要。

## 接口

### 1. `/agent/classify`

这个接口还是保留的。

它只负责看问题该走哪条路。

### 2. `/agent/run`

这个接口是真正执行工作流的入口。

请求示例：

```json
{
  "user_id": 1,
  "question": "对比实验1和实验2的F1",
  "thread_id": "checkpoint-test"
}
```

它会返回：

- `route`
- `answer`
- `sources`
- `tool_result`

### 3. `/agent/state/{thread_id}`

这个接口用来查看 checkpoint 里的当前状态。

如果你传入：

```text
checkpoint-test
```

就能看到这条线程当前保存的状态。

## 测试结果

### 1. RAG 问题

```text
小乐的身高是多少？
```

返回：

```text
route = rag
```

### 2. 工具问题

```text
对比实验1和实验2的F1
```

返回：

```text
route = tool
```

并且会带上 `tool_result`。

### 3. 普通问答

```text
你好，你是谁？
```

返回：

```text
route = normal
```

### 4. Checkpoint 验证

同一个 `thread_id = checkpoint-test`：

1. 先调用 `/agent/run`
2. 再调用 `/agent/state/checkpoint-test`

可以读回同一份状态，说明 checkpoint 生效。

## 我对 Day18 的理解

Day18 的核心不是多写几个接口，而是把 Agent 从“能分类”推进到“能执行流程”。

这一步很像搭积木：

```text
分类
-> 路由
-> 执行
-> 存状态
-> 可回看
```

后面 Day19 就可以在这个基础上做多轮会话，让同一个线程持续聊下去。
