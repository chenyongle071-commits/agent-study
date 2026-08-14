# Day23 实验管理前端

## 今日目标

- 完成实验管理页面
- 完成指标对比图表
- 展示 Agent 工具执行过程
- 展示 RAG 引用来源占位
- 把 Day22 的聊天页面升级成 Agent 工作台

## 页面结构

Day23 在 Day22 对话页面基础上增加了 Tab 页面。

目前包含三个 Tab：

```text
对话
实验管理
执行过程
整体页面从单纯聊天窗口，升级成了一个实验分析 Agent 工作台。
对话页面
对话页面保留 Day22 的能力：
输入用户问题
调用后端 /agent/run
展示用户消息
展示 Agent 回复
加载状态
错误状态
模拟流式逐字输出
自动滚动到底部
清空当前前端会话
请求流程：
用户输入问题
-> Vue 保存用户消息
-> fetch 请求 FastAPI
-> FastAPI 调用 Agent 工作流
-> 后端返回 answer、route、tool_result
-> Vue 展示 Agent 回复
-> Vue 保存执行过程
实验管理页面
实验管理页面用于展示实验信息。
当前先使用前端静态数据，模拟后端实验表数据。
实验字段包括：
实验 ID
实验名称
模型名称
数据集名称
Accuracy
F1
Latency
Cost
Status
示例数据结构：
type Experiment = {
  id: number
  name: string
  modelName: string
  datasetName: string
  accuracy: number
  f1: number
  latencyMs: number
  cost: number
  status: string
}
这一步主要练习 Vue 的列表渲染：
<tr v-for="experiment in experiments" :key="experiment.id">
指标对比图表
Day23 实现了一个简单的 F1 指标横向柱状图。
没有引入额外图表库，而是用 Vue 数据绑定和 CSS 实现。
核心思路：
<div
  class="bar-fill"
  :style="{ width: `${(experiment.f1 / maxF1) * 100}%` }"
/>
含义是：
实验 F1 越高
-> width 越大
-> 柱状图越长
这让用户可以直观看到不同实验之间的指标差异。
执行过程页面
执行过程页面用于展示 Agent 每次调用的内部过程。
前端新增了 activities 状态：
type ActivityRecord = {
  question: string
  route: string
  answer: string
  toolResult: Record<string, unknown> | null
  sources: Array<Record<string, unknown>>
  createdAt: string
}
每次后端返回结果后，前端会保存一条执行记录：
activities.value.unshift({
  question,
  route: data.route,
  answer,
  toolResult: data.tool_result,
  sources: data.sources || [],
  createdAt: new Date().toLocaleString(),
})
这样用户不只能看到 Agent 的最终回答，还能看到：
用户问了什么
Agent 选择了什么 route
Agent 调用了什么工具
工具返回了什么结果
是否有引用来源
工具结果美化
一开始工具结果直接展示 JSON。
虽然准确，但用户不容易阅读。
Day23 对 get_experiment_tool 的结果做了美化展示。
从原始结构：
{
  "selected_tool": "get_experiment_tool",
  "tool_result": {
    "id": 1,
    "name": "rag baseline",
    "model_name": "deepseek-chat",
    "dataset_name": "rag_eval_v1",
    "accuracy": 0.82,
    "f1": 0.79,
    "latency_ms": 1200,
    "cost": 0.03,
    "status": "completed"
  }
}
转换成页面信息块：
调用工具：get_experiment_tool
实验名称：rag baseline
模型：deepseek-chat
数据集：rag_eval_v1
Accuracy：0.82
F1：0.79
Latency：1200 ms
Cost：0.03
状态：completed
这样页面更接近真实产品，而不是只像接口调试工具。
引用来源
执行过程页面也预留了引用来源展示区域。
如果后端返回：
sources
前端会展示来源内容。
如果没有返回引用来源，则显示：
本次没有返回引用来源。
工具调用类问题通常没有引用来源。
RAG 文档问答类问题才更可能返回引用来源。
今日理解
Day22 解决的是：
前端能不能和 Agent 后端聊起来
Day23 解决的是：
用户能不能看懂 Agent 做了什么
一个 Agent 应用不能只给最终答案。
更好的产品应该能展示：
数据
指标
工具调用
执行过程
引用来源
这能让 Agent 从一个黑盒聊天框，变成一个更可信的工作台。
当前完成情况
实验管理页面：完成
指标对比图表：完成
工具执行过程展示：完成
引用来源展示占位：完成
```