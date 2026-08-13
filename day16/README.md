# Day16 多指标变化、文档检索与工具安全

## 今日目标

- 实现查询失败案例工具
- 实现计算指标变化工具
- 实现检索实验文档工具
- 禁止模型直接生成任意 SQL
- 工具调用继承用户权限

## 为什么要做 Day16

Day15 已经把实验查询和单指标对比做通了。

Day16 继续补三个重要能力：

- 更丰富的指标对比
- 实验文档检索
- 失败案例查询

同时强调一个底线：

```text
模型不能直接拼 SQL
模型只能调用后端暴露的工具
```

## 多指标变化工具

本次实现了 `calculate_metric_changes_tool()`。

它可以一次比较多个指标，比如：

- accuracy
- f1
- latency_ms
- cost

### 请求示例

```json
{
  "user_id": 1,
  "experiment_a_id": 1,
  "experiment_b_id": 2,
  "metrics": ["accuracy", "f1", "latency_ms", "cost"]
}
```

### 返回结果

每个指标都会返回：

- `a_value`
- `b_value`
- `delta`
- `change_percent`
- `better_experiment_id`

### 规则

- `accuracy` / `f1` 越大越好
- `latency_ms` / `cost` 越小越好

## 参数校验

Day16 继续使用 Pydantic 做参数白名单。

例如：

```json
{
  "metrics": ["delete_all"]
}
```

会直接返回 `422`，不会进入业务逻辑。

这说明工具参数不是“模型随便说什么都行”，而是被明确限制的。

## 权限继承

Day16 的工具继续继承 user_id 权限。

工具内部会先检查实验是否属于当前用户，再返回结果。

这意味着：

```text
模型想查别人的实验
-> 工具会拒绝
```

## 检索实验文档工具

本次还实现了 `search_experiment_documents_tool()`。

它复用 RAG 的混合检索能力，按用户问题检索实验相关 chunk。

### 请求示例

```json
{
  "user_id": 1,
  "query": "小乐身高",
  "top_k": 3
}
```

### 返回结果

返回内容包括：

- `chunk_id`
- `filename`
- `text`
- `retrieval_method`
- `distance`

这说明工具不仅能查结构化实验数据，也能查实验相关文档片段。

## 查询失败案例工具

本次还实现了 `query_failure_cases_tool()`。

它直接读取 Day13-14 的评测结果文件，用来查询失败案例。

### 请求示例

```json
{
  "user_id": 1,
  "category": "unknown",
  "only_failed": true,
  "limit": 5
}
```

### 返回结果

返回内容包括：

- `id`
- `category`
- `question`
- `answer`
- `status_code`
- `passed`
- `reasons`

这对后续分析 RAG 失败原因很有用。

## 当前已完成的工具基础

Day15 和 Day16 的工具层已经具备这些能力：

- 查询指定实验
- 对比单个指标
- 对比多个指标
- 检索实验文档
- 查询失败案例
- Pydantic 白名单校验
- user_id 权限校验

## 本次测试结果

### 1. 多指标对比成功

使用：

```json
{
  "user_id": 1,
  "experiment_a_id": 1,
  "experiment_b_id": 2,
  "metrics": ["accuracy", "f1", "latency_ms", "cost"]
}
```

成功返回了四个指标的变化结果。

### 2. 非法参数被拦截

使用：

```json
{
  "metrics": ["delete_all"]
}
```

接口返回 `422`，说明参数白名单生效。

### 3. 实验文档检索成功

使用：

```json
{
  "user_id": 1,
  "query": "小乐身高",
  "top_k": 3
}
```

成功返回相关 chunk，说明实验文档检索工具可用。

### 4. 失败案例查询成功

使用：

```json
{
  "user_id": 1,
  "category": "unknown",
  "only_failed": true,
  "limit": 5
}
```

成功返回结果。

当 `category` 填成非法值时，接口返回 `422`，说明白名单生效。

## 我对 Day16 的理解

Day16 的核心不是再加一个接口，而是把工具层做得更安全、更可控。

Agent 工程里，工具是模型真正执行动作的地方。

所以工具必须满足：

- 参数明确
- 权限明确
- 结果结构化
- 不能直接暴露任意 SQL

这一步让后续的 Agent 工作流更稳定，也更适合真实业务场景。
