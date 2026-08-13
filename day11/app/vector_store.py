from pathlib import Path
from typing import Any

import chromadb


CHROMA_DIR = Path(__file__).resolve().parents[1] / "chroma_db"
COLLECTION_NAME = "document_chunks"


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(name=COLLECTION_NAME)


def build_chroma_id(chunk_id: int) -> str:
    return f"chunk:{chunk_id}"


def index_chunks(
    chunks: list[dict[str, Any]],
) -> int:
    """把 chunks 写入 Chroma。"""

    if not chunks:
        return 0

    collection = get_collection()

    ids = [build_chroma_id(chunk["id"]) for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    return len(chunks)


def search_chunks(
    query: str,
    user_id: int,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """根据 query 检索相似 chunks。"""

    collection = get_collection()

    result = collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"user_id": user_id},
    )

    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    results: list[dict[str, Any]] = []

    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
        results.append(
            {
                "id": chunk_id,
                "text": text,
                "metadata": metadata,
                "distance": distance,
            }
        )

    return results