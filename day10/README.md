# Day10 Retriever、Top-K 与基础 RAG 问答

## 今日目标

- 实现 Retriever
- 实现 Top-K 召回
- 实现基础 RAG 问答接口
- 返回答案和引用来源

## Retriever 是什么

Retriever 是检索器。

它的作用不是生成回答，而是根据用户问题去知识库里寻找相关资料。

在本项目中，Retriever 会调用 Chroma 向量数据库，根据用户的问题检索最相关的 chunk。

## Top-K 召回是什么

Top-K 召回表示返回最相关的前 K 个结果。

比如：

```json
{
  "query": "我的名字叫什么？",
  "top_k": 3
}
意思是系统最多返回 3 个最相关的 chunk。
K 越大，模型能看到的资料越多，但 token 消耗也会增加；K 太小，可能漏掉关键资料。
```

基础 RAG 流程
Day09 做到的是：
用户问题
-> Chroma 检索
-> 返回相关 chunk
Day10 做到的是：
用户问题
-> Retriever 检索 Chroma
-> 拿到 Top-K chunks
-> 拼成 context
-> 构造 Prompt
-> 调用 DeepSeek
-> 返回 answer + sources
也就是完整的基础 RAG：
用户问：我的名字叫什么？
-> Retriever 去 Chroma 找相关 chunk
-> 找到“我的名字叫小乐”
-> 把这个 chunk 拼进 prompt
-> DeepSeek 根据资料生成回答
-> 返回 answer + sources
新增模块
app/retriever.py
retrieve_chunks()：
负责根据用户问题调用向量检索，拿到 Top-K chunks。
build_context_from_chunks()：
负责把检索到的 chunks 拼成一段上下文，放进 prompt 里交给大模型。
示例 context：
资料 1，来源文件：草稿.txt
我的名字叫小乐，请你记住
新增接口
POST /rag/answer
请求示例：
{
  "user_id": 1,
  "query": "我的名字叫什么？",
  "top_k": 3,
  "temperature": 0.3
}
返回示例：
{
  "answer": "根据资料，你的名字叫小乐。",
  "sources": [
    {
      "chunk_id": "chunk:1",
      "filename": "草稿.txt",
      "text": "我的名字叫小乐，请你记住",
      "distance": 0.7835
    }
  ]
}
answer 和 sources 的意义
answer 是大模型根据资料生成的最终回答。
sources 是这次回答参考的文档片段。
RAG 项目里 sources 很重要，因为它能说明答案有没有依据，也方便用户检查模型是不是胡说。
我对 Day10 的理解
Day10 把 Day09 的“找资料”升级成了“根据资料回答问题”。
向量数据库负责找相关 chunk，大模型负责阅读这些 chunk 并生成自然语言答案。
RAG 的核心不是让模型凭记忆回答，而是先从外部文档里找依据，再让模型基于依据回答。
目前系统已经实现基础 RAG 问答，但还只是最简单版本。后续还需要继续优化召回质量、引用格式、无关问题拒答和评测指标。

你保存完之后，建议再测试一个“资料里没有的问题”，比如：

```json
{
  "user_id": 1,
  "query": "我的生日是哪一天？",
  "top_k": 3,
  "temperature": 0.3
}
看它能不能回答“根据当前资料无法回答”。这个测试很重要，因为 RAG 不光要会答，还要知道什么时候不能乱答。