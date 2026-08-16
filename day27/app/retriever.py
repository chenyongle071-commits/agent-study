from typing import Any

from app.vector_store import search_chunks

from sqlmodel import Session, select

from app.models import Chunk


def retrieve_chunks(query: str, user_id: int, top_k: int = 3) -> list[dict[str, Any]]:
    """
    根据用户问题，从向量数据库中检索最相关的 chunks。
    """
    results = search_chunks(
        query=query,
        user_id=user_id,
        top_k=top_k,
    )

    return results


#去 SQLite 的 chunks 表里找
#-> user_id 必须匹配
#-> chunk.text 里必须包含 query 这段文字
#-> 最多返回 top_k 条
def keyword_search_chunks(
    query: str,
    user_id: int,
    session: Session,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    使用普通数据库做关键词检索。

    它不是语义搜索，而是检查 chunk 原文里是否包含用户输入的关键词。
    """
    statement = (
        select(Chunk)
        .where(Chunk.user_id == user_id)
        .where(Chunk.text.contains(query))
        .limit(top_k)
    )

    chunks = session.exec(statement).all()

    results = []
    for chunk in chunks:
        results.append(
            {
                "id": f"chunk:{chunk.id}",
                "text": chunk.text,
                "metadata": {
                    "filename": chunk.meta.get("filename", "unknown"),
                    "content_type": chunk.meta.get("content_type", "unknown"),
                    "source_type": chunk.meta.get("source_type", "uploaded_document"),
                    "user_id": chunk.user_id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "chunk_db_id": chunk.id,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                },
                "distance": 0.0,
                "retrieval_method": "keyword",
            }
        )

    return results

#1. 先用关键词检索找一批
#2. 再用向量检索找一批
#3. 把两批结果合并
#4. 如果同一个 chunk 重复出现，只保留一次
#5. 最后只返回 top_k 条

#关键词结果排前面
#向量结果排后面
def hybrid_retrieve_chunks(
    query: str,
    user_id: int,
    session: Session,
    top_k: int = 3,
    max_vector_distance: float = 2.0,
) -> list[dict[str, Any]]:
    """
    混合检索：同时使用关键词检索和向量检索，然后合并去重。

    max_vector_distance 用来过滤明显无关的向量召回结果。
    distance 越大，表示越不相关。
    """
    keyword_results = keyword_search_chunks(
        query=query,
        user_id=user_id,
        session=session,
        top_k=top_k,
    )

    vector_results = retrieve_chunks(
        query=query,
        user_id=user_id,
        top_k=top_k,
    )

    filtered_vector_results = []
    for result in vector_results:
        if result["distance"] <= max_vector_distance:
            filtered_vector_results.append(result)

    merged_results: list[dict[str, Any]] = []
    seen_chunk_ids = set()

    for result in keyword_results + filtered_vector_results:
        chunk_id = result["id"]

        if chunk_id in seen_chunk_ids:
            continue

        seen_chunk_ids.add(chunk_id)

        if "retrieval_method" not in result:
            result["retrieval_method"] = "vector"

        merged_results.append(result)

    return merged_results[:top_k]

def build_context_from_chunks(chunks: list[dict[str, Any]]) -> str:
    """
    把检索到的 chunks 拼成一段上下文，后面会放进 prompt 里交给大模型。
    """
    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk["metadata"]
        filename = metadata.get("filename", "unknown")
        text = chunk["text"]

        context_parts.append(
            f"资料 {index}，来源文件：{filename}\n{text}"
        )

    return "\n\n".join(context_parts)