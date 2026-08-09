# Day06 Prompt & Context 基础

## 今日目标

1. 复制 Day05 为 Day06
2. 学习 Message / Prompt / Context
3. 理解 System Prompt
4. 理解 Temperature
5. 理解 Token
6. 实现历史消息拼接
7. 控制上下文长度
8. 测试多轮对话
9. Git 提交

## 我的理解

### Prompt

Prompt 是发给模型的完整输入，不只是聊天内容的总结。  
它包含系统规则、历史上下文、当前问题和回答约束，决定模型看什么、怎么答、答到什么程度。

### System Prompt

System Prompt 是 Prompt 里的第一层规则，通常用来定义模型身份、回答风格和边界。

例如：

```text
你是一个帮助用户学习 Agent 应用开发的助手。
回答要准确、简洁，优先解释工程实现。
```

Temperature
Temperature 用来控制模型输出的随机性。
temperature 越低，回答越稳定、越保守
temperature 越高，回答越随机、越发散、更有创意
在本项目中，通常使用较低的 temperature，让技术回答更稳定。
Token
Token 是大模型处理文本时的基本计费和计算单位。
我的理解是：
输入 token 越多，费用越高
输出 token 越多，费用越高
上下文越长，token 越多，费用越高
所以在多轮对话中，不能无限把历史都传给模型，必须控制上下文长度。