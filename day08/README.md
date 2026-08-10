# Day08 文档上传、清洗与 Chunk 切分

## 今日目标

Day08 开始进入 RAG 系统的第一步。

今天不做 Embedding、向量数据库和问答检索，而是先完成：

```text
文档上传
-> 文档解析
-> 文本清洗
-> Chunk 切分
-> Metadata 设计
-> 保存到数据库

```

依赖
Day08 需要安装：
python -m pip install python-multipart
python-multipart 是 FastAPI 处理文件上传需要的依赖。
因为文件上传不是普通 JSON 请求，而是：
multipart/form-data

Document
Document 表示一个完整上传文件。
主要字段：
id
user_id
filename
content_type
content_hash
char_count
created_at
其中：
user_id：表示文档属于哪个用户
filename：原始文件名
content_type：文件类型
content_hash：文档内容指纹，用来判断重复上传
char_count：清洗后的文本字符数
Chunk
Chunk 表示从文档中切出来的一小段文本。
主要字段：
id
document_id
user_id
chunk_index
text
char_start
char_end
meta
created_at
其中：
document_id：表示 chunk 属于哪个文档
user_id：用于后续用户数据隔离
chunk_index：chunk 在文档中的顺序
text：chunk 文本内容
char_start / char_end：chunk 在原文中的字符位置
meta：chunk 的来源信息
Metadata
Metadata 用于记录 chunk 的来源信息。
示例：
{
  "filename": "草稿.txt",
  "content_type": "text/plain",
  "chunk_index": 0,
  "char_start": 0,
  "char_end": 55,
  "source_type": "uploaded_document"
}
后续做 RAG 引用来源时，需要依赖这些 metadata。

响应模型
DocumentRead
DocumentRead 返回文档基本信息。
ChunkRead
ChunkRead 返回每个 chunk 的信息。
DocumentUploadResponse
DocumentUploadResponse 是文档上传成功后的响应结构。
它会一次性返回：
document
chunk_count
chunks
文档处理函数
Day08 新增了：
app/document_processing.py
里面包含：
calculate_content_hash()
clean_text()
split_text_into_chunks()
build_chunk_metadata()
calculate_content_hash
计算文档内容 hash。
作用：
识别重复文档
避免同一个用户重复上传相同内容
clean_text
清洗原始文本。
主要处理：
统一换行符
合并多余空格
合并过多空行
去掉首尾空白
split_text_into_chunks
将长文本切分成多个 chunk。
当前使用：
chunk_size = 500
overlap = 80
overlap 表示相邻 chunk 之间保留一部分重叠内容，避免重要信息刚好被切断。
build_chunk_metadata
为每个 chunk 构造 metadata。
接口
POST /documents/upload
上传文档接口。
请求内容：
user_id
file
流程：
接收 user_id 和 file
-> 检查用户是否存在
-> 检查文件类型
-> 读取 UTF-8 文本
-> 清洗文本
-> 计算 hash
-> 防止重复上传
-> 创建 Document
-> 切分 chunks
-> 创建 Chunk 记录
-> 返回文档和 chunks
当前只支持：
.txt
.md
PDF 解析后面再做。
GET /documents/{document_id}/chunks
查询指定文档的 chunks。
流程：
接收 document_id
-> 查询文档是否存在
-> 查询该文档下所有 chunks
-> 按 chunk_index 排序
-> 返回 chunk 列表
今日理解
RAG 的第一步不是直接问文档，而是先把文档处理成可检索的数据结构。
原始文档通常太长、太乱，不能直接全部塞给模型。
所以需要先进行：
清洗
切分
保存来源信息
Document 表保存完整文档的信息。
Chunk 表保存被切分后的小文本块。
Metadata 记录 chunk 的来源，后面用于引用和溯源。