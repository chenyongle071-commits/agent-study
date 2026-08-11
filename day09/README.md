# Day09 Embedding 与向量检索

## 今日目标

- 学习 Embedding 的作用
- 接入 Chroma 向量数据库
- 实现文档 Chunk 的向量化入库
- 实现根据问题检索相关 Chunk

## Embedding 是什么

Embedding 是把文本转换成一组数字向量。

比如：

```text
我的名字叫小乐
```

会被模型转换成类似这样的数字：
[0.12, -0.43, 0.88, ...]
这些数字不是给人看的，而是给计算机比较语义相似度用的。
意思相近的文本，向量距离会更近。
为什么 RAG 需要 Embedding
普通数据库更适合精确查询，比如：
where user_id = 1
但是用户的问题通常不是完全匹配文档原文。
比如文档里写的是：
我的名字叫小乐
用户问的是：
我的名字叫什么？
这两句话文字不完全一样，但语义相关。
Embedding 可以帮助系统根据“意思”找到相关内容。
Chroma 是什么
Chroma 是一个向量数据库。
它用来保存：
chunk 原文
chunk 的向量
chunk 的 metadata
在本项目中，SQLite 保存用户、文档、消息等普通业务数据；Chroma 保存文档 chunk 的向量，用于语义检索。
当前实现的流程
1. 上传文档
通过 /documents/upload 上传 txt 或 md 文件。
系统会：
读取文件
-> 清洗文本
-> 计算 hash 防重复
-> 保存 Document
-> 切分 Chunk
-> 保存 Chunk
2. 文档向量化
通过接口：
POST /documents/{document_id}/index
系统会：
根据 document_id 查询 chunks
-> 把 chunk 文本交给 Chroma
-> Chroma 自动生成 embedding
-> 保存到本地 chroma_db
第一次运行时，Chroma 会下载默认 embedding 模型：
all-MiniLM-L6-v2
这个模型用于把文本转换成向量。
3. 向量检索
通过接口：
POST /rag/search
请求示例：
{
  "user_id": 1,
  "query": "我的名字叫什么？",
  "top_k": 3
}
系统会：
把用户问题转成向量
-> 在 Chroma 中查找最相似的 chunk
-> 根据 user_id 做数据隔离
-> 返回相关 chunk 原文和 metadata
返回结果字段说明
chunk_id：向量数据库里的 chunk 编号。
text：检索到的原文片段。
metadata：chunk 的附加信息，比如文件名、用户 id、文档 id、chunk 序号。
distance：向量距离。一般来说，distance 越小，说明越相似。
我对 Day09 的理解
Day09 解决的是 RAG 中“怎么找到相关文档”的问题。
Chunk 被向量化以后，不是原文消失了，而是系统同时保存了：
chunk 原文
chunk 向量
chunk 元信息
向量用于搜索，原文用于返回给用户或后续交给大模型生成回答。