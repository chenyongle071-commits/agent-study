# Day20 超时降级、人工确认与幂等性

## 今日目标

- 实现超时和降级
- 实现高风险操作人工确认
- 实现幂等性设计说明和最小演示

## 为什么要做 Day20

Day19 已经让 Agent 具备了：

- 多轮会话 Memory
- 工具失败重试
- 工具执行日志

Day20 继续补工程安全能力。

真实 Agent 不能只考虑“正常调用成功”的情况，还要处理：

- 工具一直不返回
- 工具失败后如何给用户一个可控结果
- 高风险操作不能直接执行
- 用户重复点击或网络重试时，不能重复产生副作用

所以 Day20 的核心是：

```text
不要无限等
不要危险操作直接执行
不要重复执行同一个副作用请求
```

## 一、超时和降级

### 超时是什么

超时就是给工具调用设置最大等待时间。

本次模拟工具中，如果问题包含：

```text
触发超时
```

工具会执行：

```python
time.sleep(5)
```

而 `run_tool_with_retry()` 设置了：

```text
timeout_seconds = 2
```

所以工具超过 2 秒还没有结果，就会被视为超时。

### 降级是什么

降级就是工具一直失败或超时后，不让整个服务崩溃，而是返回一个可理解的备用结果。

返回结果中会包含：

```json
{
  "success": false,
  "attempts": 3,
  "timed_out": true,
  "fallback_used": true,
  "message": "工具暂时不可用，请稍后重试。"
}
```

### 测试结果

请求：

```json
{
  "user_id": 1,
  "question": "对比实验1和实验2的F1，触发超时",
  "thread_id": "timeout-test"
}
```

结果：

```text
工具超时
-> 自动重试
-> 总共尝试 3 次
-> 返回 fallback_used = true
```

同时 `/agent/state/timeout-test` 中可以看到：

```text
tool_attempt_timeout
tool_fallback_used
```

这说明超时、重试、降级和日志已经串起来了。

## 二、高风险操作人工确认

### 为什么需要人工确认

有些工具不是普通查询，而是可能修改数据。

例如：

- 删除实验
- 重新运行实验
- 修改实验配置

这类操作不能因为模型判断要执行，就直接执行。

所以本次给 `/agent/run` 增加了：

```json
{
  "confirmed": false
}
```

默认不确认。

### 未确认时

请求：

```json
{
  "user_id": 1,
  "question": "删除实验1",
  "thread_id": "confirm-test",
  "confirmed": false
}
```

返回：

```json
{
  "confirmation_status": "pending_confirmation",
  "tool_result": {
    "success": false,
    "executed": false,
    "requires_confirmation": true
  }
}
```

这说明系统识别到这是高风险操作，但没有执行工具。

### 确认后

再次发送同样问题，但改成：

```json
{
  "user_id": 1,
  "question": "删除实验1",
  "thread_id": "confirm-test",
  "confirmed": true
}
```

返回：

```json
{
  "confirmation_status": "confirmed_and_executed"
}
```

这说明人工确认后，工具才被放行。

当前项目里的工具仍是模拟工具，所以不会真的删除数据库数据。这里验证的是安全流程。

## 三、幂等性

### 幂等性是什么

幂等性指的是：

```text
同一个请求重复提交多次，最终效果只发生一次
```

比如用户点击两次“删除实验1”，系统不能真的删除两次。

本次给 `/agent/run` 增加了：

```json
{
  "request_id": "delete-exp-1"
}
```

系统会把已经处理过的 `request_id` 存到 `idempotency_records` 中。

### 第一次提交

请求：

```json
{
  "user_id": 1,
  "question": "删除实验1",
  "thread_id": "idempotency-test-2",
  "confirmed": true,
  "request_id": "delete-exp-1"
}
```

第一次返回：

```json
{
  "idempotent_replay": false
}
```

说明这是第一次执行。

### 第二次重复提交

再次发送完全相同的请求。

第二次返回：

```json
{
  "idempotent_replay": true
}
```

说明系统发现这个 `request_id` 已经处理过，于是直接返回历史结果，没有再次执行工具。

## 当前工作流

Day20 后的 Agent 工具流程可以理解为：

```text
用户问题
-> 读取 thread_id 的历史状态
-> 判断是否重复 request_id
-> 判断是否高风险
-> 高风险且未确认：暂停执行，等待人工确认
-> 已确认或低风险：执行工具
-> 工具超时或失败：重试
-> 多次失败后：返回降级结果
-> 记录执行日志
-> 保存 State
```

## 当前实现的限制

当前仍然使用 `MemorySaver` 做演示。

因此：

- 服务运行期间可以保存 `messages`、`tool_logs`、`idempotency_records`
- 服务重启后这些内存状态会丢失

生产环境中应该使用：

- 数据库存储 `request_id`
- 对 `request_id` 加唯一索引
- 使用真正支持超时取消的异步 HTTP 客户端
- 对高风险操作记录审批人、审批时间和操作对象

## 我对 Day20 的理解

Day20 不是为了让 Agent 更“聪明”，而是让它更像一个可靠系统。

这一天解决的是工程底线：

```text
卡住了能退出
失败了能降级
危险操作要确认
重复请求不重复执行
```

这些能力在真实 Agent 项目里非常重要，因为 Agent 一旦开始调用工具，就不只是聊天，而是在影响真实业务数据。
