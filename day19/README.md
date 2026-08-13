# Day19 多轮会话、工具重试与执行日志

## 今日目标

- 实现多轮会话 Memory
- 实现工具失败重试
- 记录工具执行过程日志

## 为什么要做 Day19

Day18 已经实现了 Agent 的基础工作流：

```text
问题分类
-> 条件路由
-> 执行 RAG / 工具 / 普通问答节点
-> 保存 Checkpoint
```

但是一个实际的 Agent 还需要处理连续对话和异常情况：

- 用户会连续追问
- 工具调用可能失败
- 工具可能需要重试
- 出现问题时需要知道每一步发生了什么

因此 Day19 在 Day18 的基础上增加了 Memory、重试和日志。

## 一、多轮会话 Memory

### State 增加 messages

在 `app/agent_state.py` 中增加了消息结构：

```python
class AgentMessage(TypedDict):
    role: Literal["user", "assistant"]
    content: str
```

`AgentState` 中增加：

```python
messages: list[AgentMessage]
```

它保存当前 `thread_id` 对应的历史消息。

一轮对话会保存两条消息：

```json
{
  "role": "user",
  "content": "对比实验1和实验2的F1"
}
```

```json
{
  "role": "assistant",
  "content": "这是工具节点处理的问题：对比实验1和实验2的F1"
}
```

### 多轮会话流程

同一个 `thread_id` 下，下一次请求会先读取上一次 Checkpoint 中的 `messages`：

```text
读取历史 messages
-> 加入当前用户问题
-> 执行 Agent 节点
-> 加入当前助手回答
-> 保存新的 messages
```

### 测试结果

第一次请求：

```json
{
  "user_id": 1,
  "question": "对比实验1和实验2的F1",
  "thread_id": "memory-test"
}
```

第二次请求：

```json
{
  "user_id": 1,
  "question": "那哪个实验更快？",
  "thread_id": "memory-test"
}
```

查询 `/agent/state/memory-test` 后，`messages` 中出现了四条记录：

```text
user: 对比实验1和实验2的F1
assistant: ...
user: 那哪个实验更快？
assistant: ...
```

这说明同一个线程可以保存多轮对话历史。

当前实现已经能保存历史，但节点还没有真正根据历史内容进行复杂推理。后续接入真实工具和 LLM 后，才会充分利用这些历史消息。

## 二、工具失败重试

### 重试逻辑

在 `app/agent_nodes.py` 中增加了：

```python
run_tool_with_retry()
```

当前配置为：

```text
max_retries = 2
```

因此一次工具调用最多执行：

```text
第一次尝试 + 2 次重试 = 总共 3 次
```

执行流程：

```text
调用工具
-> 成功：直接返回
-> 失败：重新调用
-> 达到最大次数仍失败：返回结构化失败结果
```

### 正常测试

请求：

```json
{
  "user_id": 1,
  "question": "对比实验1和实验2的F1",
  "thread_id": "retry-ok"
}
```

结果：

```json
{
  "success": true,
  "attempts": 1
}
```

说明工具第一次调用就成功。

### 失败测试

请求中加入 `触发失败`：

```json
{
  "user_id": 1,
  "question": "对比实验1和实验2的F1，触发失败",
  "thread_id": "retry-fail"
}
```

结果：

```json
{
  "success": false,
  "attempts": 3,
  "error": "模拟工具调用失败"
}
```

说明工具失败后重试了两次，最后返回了可控的错误结果，服务没有崩溃。

## 三、工具执行过程日志

### 日志保存位置

Day19 在 `AgentState` 中增加了：

```python
tool_logs: NotRequired[list[dict[str, object]]]
```

工具每次尝试都会记录：

- 事件类型
- 工具名称
- 第几次尝试
- 开始时间
- 结束时间
- 错误原因

### 失败时的日志

失败测试后，可以通过：

```text
GET /agent/state/tool-log-test
```

查看日志。

日志中包含：

```text
tool_attempt_failed
tool_attempt_failed
tool_attempt_failed
tool_failed_after_retries
```

这说明：

```text
第 1 次失败
-> 第 2 次失败
-> 第 3 次失败
-> 记录最终失败
```

### 为什么要记录日志

如果工具调用失败，只返回一句“失败了”，很难排查问题。

有了执行日志，就可以知道：

- 调用了哪个工具
- 调用了几次
- 每次什么时候开始和结束
- 具体错误是什么
- 是单次失败还是重试后仍然失败

这对线上排错、性能分析和后续评测都很重要。

## 当前工作流

Day19 的工作流可以表示为：

```text
用户问题
-> 读取 thread_id 对应的历史消息
-> 分类问题
-> 条件路由
-> 执行工具或其他节点
-> 工具失败时自动重试
-> 记录工具执行日志
-> 保存新的 State
-> 返回回答
```

## 当前实现的限制

目前使用的是 LangGraph 的 `MemorySaver`：

- 服务运行期间可以保存状态
- 可以通过 `thread_id` 读取状态
- 重启服务后，内存中的状态会清空

因此当前是教学和调试版本，不是真正的生产级持久化。

后续可以把 Checkpoint 换成 SQLite 或 PostgreSQL，让服务重启后仍然保留会话状态。

## 我对 Day19 的理解

Day19 让 Agent 具备了三个重要能力：

```text
记得住
-> 失败后再试
-> 能查清执行过程
```

这说明 Agent 不只是“调用模型并返回文本”，还需要管理状态、处理异常和留下可追踪记录。
