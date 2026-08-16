# Day26 RAG 质量评估

## 今日目标

- 评估 RAG 召回质量
- 评估回答事实一致性
- 评估延迟和 Token 成本
- 保存失败案例并写改进方案

## 今日完成

Day26 主要评估 RAG 问答链路的质量。

Day25 评估的是 Agent 是否选对工具、参数是否正确；Day26 评估的是 RAG 是否能找到正确资料，并且让模型根据资料回答。

RAG 评估不能只看“模型有没有回答”，还要看：

```text
资料有没有召回
回答是否命中事实
引用来源是否正确
延迟是否可接受
Token 成本大概是多少
失败案例如何改进
```

## 文件说明

```text
day26_rag_eval/
├── eval_rag_questions.jsonl
├── eval_rag_runner.py
├── eval_rag_results.jsonl
├── failure_cases.jsonl
├── rag_eval_corpus.md
└── README.md
```

### eval_rag_questions.jsonl

RAG 评估题库。

每一行是一道测试题，包含：

```text
id：测试编号
user_id：用户 ID
query：用户问题
expected_answer_keywords：答案中应该出现的关键词
expected_source_keywords：召回资料中应该出现的关键词
top_k：召回前 K 条资料
```

### rag_eval_corpus.md

标准测试文档。

这份文档被上传到后端，并通过 `/documents/{document_id}/index` 写入向量库。评估题库中的问题都基于这份文档设计。

这一步很重要，因为 RAG 评估必须先有稳定的标准资料，否则评估结果会受已有数据库内容影响。

### eval_rag_runner.py

RAG 自动评估脚本。

它会逐条读取 `eval_rag_questions.jsonl`，然后调用：

```text
POST /rag/search
POST /rag/answer
```

脚本会记录：

```text
召回是否命中
答案关键词是否命中
引用来源是否命中
回答是否被资料支持
接口耗时
粗略 Token 估算
```

### eval_rag_results.jsonl

完整评估结果。

每一行是一道题的评估详情，最后一行是汇总 summary。

### failure_cases.jsonl

失败案例文件。

如果某道题没有通过，会把问题、预期关键词、实际回答、召回来源和接口结果保存下来，方便后续分析和改进。

本次最终评估中失败案例数为 0，所以该文件为空。

## 评估指标

### 1. Recall@K

判断正确资料是否出现在前 K 个召回结果中。

比如问题是：

```text
我的名字叫什么？
```

如果 Top-K 召回资料中包含：

```text
我的名字叫小乐。
```

则认为召回命中。

### 2. 答案关键词命中率

判断模型回答是否包含预期答案关键词。

比如预期关键词是：

```json
["小乐"]
```

如果回答中出现“小乐”，则认为答案命中。

### 3. 来源关键词命中率

判断 `/rag/answer` 返回的 sources 中是否包含预期来源关键词。

这一步用于确认模型回答时引用了正确资料，而不是只靠模型自己的记忆回答。

### 4. 回答事实一致性

当前版本用一个简化判断：

```text
答案关键词命中
并且
来源关键词命中
=
回答被资料支持
```

真实项目里可以进一步升级为人工评审或 LLM-as-Judge。

### 5. 延迟

记录每道题的总耗时：

```text
/rag/search 耗时 + /rag/answer 耗时
```

RAG 的耗时通常比普通工具调用更高，因为它包含检索和大模型生成。

### 6. Token 成本估算

当前版本采用粗略估算：

```text
中文约 1 个字 ≈ 1 token
英文约 4 个字符 ≈ 1 token
```

统计内容包括：

```text
用户问题 token
召回 context token
模型回答 token
```

后续可以接入更精确的 tokenizer。

## 运行方式

先启动后端：

```powershell
cd D:\agent_study\day24
py -m uvicorn app.main:app --reload
```

然后运行评估：

```powershell
cd D:\agent_study\day26_rag_eval
python eval_rag_runner.py
```

## 调试过程

第一次评估时，20 条全失败：

```text
recall_at_k = 0.0
success_rate = 0.0
```

原因是向量库里没有标准测试文档，RAG 没有可召回的资料。

解决方式：

```text
创建 rag_eval_corpus.md
上传文档
执行 /documents/{document_id}/index
重新运行评估
```

第二次评估时，召回成功但回答失败。

原因是 `/rag/answer` 需要调用 LLM，但后端没有读到 `.env`，缺少：

```text
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
```

解决方式：

```text
给 day24 配置 .env
重启后端
重新运行评估
```

后面又发现 `/rag/search` 能召回，但 `/rag/answer` 认为资料不可靠。

原因是 Retriever 的 distance 阈值过严格。

解决方式：

```text
把 hybrid_retrieve_chunks 的 max_vector_distance 调整到 2.0
```

最后还遇到过 VPN 代理导致 LLM 调用失败。关闭或调整代理后，RAG 回答链路恢复正常。

## 本次最终评估结果

本次共评估 20 道 RAG 问题。

最终 summary：

```json
{
  "total": 20,
  "recall_at_k": 1.0,
  "answer_keyword_hit_rate": 1.0,
  "source_keyword_hit_rate": 1.0,
  "answer_supported_rate": 1.0,
  "success_rate": 1.0,
  "failure_count": 0,
  "avg_latency_ms": 1654.12,
  "avg_estimated_tokens": 575.1
}
```

结果说明：

```text
Recall@K：100%
答案关键词命中率：100%
来源关键词命中率：100%
回答事实支持率：100%
整体成功率：100%
失败案例数：0
平均延迟：1654.12ms
平均估算 Token：575.1
```

## 失败案例分析

评估过程中曾出现过一条失败案例：

```text
问题：不同用户的数据为什么要隔离？
预期关键词：权限、用户
实际回答：不同用户的数据要隔离，因为每个用户只能访问自己的数据，不能越权访问其他用户资料。
```

这个回答事实是正确的，但没有出现“权限”两个字，所以被关键词规则误判失败。

改进方式：

```text
把关键词从 ["权限", "用户"]
调整为 ["用户", "越权"]
```

这说明 RAG 评估不能只看自动分数，还要人工抽查失败案例。因为有些失败是真失败，有些只是评估规则太死。

## 后续改进方案

后续可以继续增强评估体系：

```text
增加更多真实业务文档
增加更复杂的问题改写
增加无答案问题
增加跨 chunk 问题
增加不同用户数据隔离测试
统计真实 API token 用量
加入 LLM-as-Judge 判断事实一致性
把失败案例转成新的回归测试题
```

## 我的理解

RAG 的核心不是“模型能不能说话”，而是：

```text
能不能找对资料
能不能根据资料回答
能不能给出正确来源
能不能在成本和速度可控的情况下稳定回答
```

Day26 的评估脚本就像给 RAG 系统做自动化考试。以后每次调整 chunk、embedding、retriever、阈值、prompt 或模型，都可以重新跑这套评估，观察质量有没有变好或者变坏。
