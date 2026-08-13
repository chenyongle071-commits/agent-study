# Day15 真实工具与参数校验

## 今日目标

- 实现真实工具：查询指定实验
- 实现真实工具：对比模型指标
- 所有工具参数使用 Pydantic 校验
- 工具调用必须继承用户权限

## 为什么要做 Tool Calling

RAG 解决的是“去文档里找资料再回答”。

Tool Calling 解决的是“调用后端真实能力去完成任务”。

比如用户问：

```text
实验 1 的 F1 是多少？
```

模型不应该自己猜，而应该调用真实工具去查数据库。

## 当前实现的实验表

本次新增了 `Experiment` 表，用来保存实验结果。

主要字段包括：

- `id`
- `user_id`
- `name`
- `model_name`
- `dataset_name`
- `accuracy`
- `f1`
- `latency_ms`
- `cost`
- `status`
- `created_at`

这个表是后面工具层的真实数据来源。

## 工具参数模型

本次把工具入参统一放进了 Pydantic 模型里。

### GetExperimentInput

用于查询指定实验：

```python
class GetExperimentInput(BaseModel):
    user_id: int
    experiment_id: int
```

### CompareMetricInput

用于对比两个实验的指标：

```python
class CompareMetricInput(BaseModel):
    user_id: int
    experiment_a_id: int
    experiment_b_id: int
    metric_name: Literal["accuracy", "f1", "latency_ms", "cost"]
```

这里的 `Literal` 就是白名单。

如果模型乱传：

```json
{
  "metric_name": "delete_all"
}
```

接口会直接返回 `422`，不会进入工具逻辑。

## 工具函数

### get_experiment_tool()

根据 `experiment_id` 查询指定实验。

它会先校验：

```text
实验是否存在
实验是否属于当前 user_id
```

如果不是当前用户的实验，会返回：

```text
403 无权访问该实验
```

### compare_metric_tool()

对比两个实验的某个指标。

支持的指标是：

- accuracy
- f1
- latency_ms
- cost

对比规则：

- `accuracy` / `f1` 越大越好
- `latency_ms` / `cost` 越小越好

## 暴露出来的测试接口

### POST /tools/get-experiment

请求示例：

```json
{
  "user_id": 1,
  "experiment_id": 1
}
```

返回实验详情。

### POST /tools/compare-metric

请求示例：

```json
{
  "user_id": 1,
  "experiment_a_id": 1,
  "experiment_b_id": 2,
  "metric_name": "f1"
}
```

返回两个实验的指标值、差值和更优实验。

## 权限控制

工具层不能直接相信模型传来的参数。

当前实现里，每次查询实验都会做 user_id 检查：

```text
当前用户不是实验所有者
-> 直接拒绝访问
```

这一步很重要，因为后面真正接入 Agent 时，模型可能会尝试调用不属于当前用户的数据。

## 本次测试结果

### 1. 创建实验

成功创建了两个实验：

- `rag baseline`
- `rag hybrid retrieval`

### 2. 查询实验

调用 `POST /tools/get-experiment` 成功返回了实验详情。

### 3. 对比指标

调用 `POST /tools/compare-metric` 成功返回：

- `experiment_a_id`
- `experiment_b_id`
- `metric_name`
- `a_value`
- `b_value`
- `delta`
- `better_experiment_id`

### 4. 参数校验

当我把 `metric_name` 填成：

```json
"delete_all"
```

接口返回 `422`，说明 Pydantic 校验生效。

### 5. 权限校验

当我把 `user_id` 改成 `2` 时，接口返回无权限访问，说明工具层的权限检查生效。

## 我对 Day15 的理解

Day15 的重点不是把模型变聪明，而是把真实业务能力封装成工具。

模型只负责判断“要不要调用工具”，工具负责真正查数据。

这一层的关键是三件事：

- 参数必须校验
- 数据必须有权限边界
- 工具必须返回结构化结果

这就是 Agent 工程里很核心的一步。
