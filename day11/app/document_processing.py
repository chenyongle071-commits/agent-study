import hashlib
import re
from typing import Any


def calculate_content_hash(text: str) -> str:
    """计算文档内容 hash，用于后续判断重复文档。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean_text(text: str) -> str:
    """清洗原始文本。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 80,
) -> list[tuple[int, int, str]]:
    """按字符长度切分文本，并保留 overlap。"""
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0。")

    if overlap < 0:
        raise ValueError("overlap 不能小于 0。")

    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size。")

    chunks: list[tuple[int, int, str]] = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append((start, end, chunk_text))

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def build_chunk_metadata(
    filename: str,
    content_type: str,
    chunk_index: int,
    char_start: int,
    char_end: int,
) -> dict[str, Any]:
    """构造 chunk metadata。"""
    return {
        "filename": filename,
        "content_type": content_type,
        "chunk_index": chunk_index,
        "char_start": char_start,
        "char_end": char_end,
        "source_type": "uploaded_document",
    }