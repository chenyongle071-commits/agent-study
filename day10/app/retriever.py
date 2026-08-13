from typing import Any

from app.vector_store import search_chunks


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