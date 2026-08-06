# Day03 LLM Client 基础

## 今日目标

- 学习 `async/await`
- 学习 Pydantic 数据模型
- 学习环境变量 `.env`
- 学习 HTTP 请求
- 写一个可以调用真实 LLM API 的最小 Python 脚本
- 理解 SDK 和 HTTP 请求的区别

## 1. async/await

`async/await` 用于处理异步任务。

普通函数通常是一个任务做完，再做下一个任务。  
异步函数可以在等待网络请求、数据库查询、文件 IO 时，把执行权让给其他任务。

我的理解：

> `async` 表示这个函数可以异步执行，`await` 表示这里需要等待，但不会把整个程序完全卡住。

在 Agent 项目中，异步很重要，因为后面会同时涉及：

- 调用 LLM API
- 查询数据库
- 检索向量库
- 调用工具
- 流式返回结果

练习文件：

```text
exercises/async_demo.py