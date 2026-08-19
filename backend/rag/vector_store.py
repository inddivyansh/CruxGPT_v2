"""
Vector store.

MVP implementation: embeddings live alongside their chunk metadata in the
document_chunks table (see models/chunk.py), and search is brute-force
cosine similarity in Python/NumPy, always filtered by user_id first at the
SQL level. This is the enforcement point for multi-user isolation - a
query can never see another user's chunks because they're excluded before
similarity is even computed.

At the data volumes a document-QA MVP sees (thousands, not millions, of
chunks per user) brute force is fast and removes an entire infra dependency
(no FAISS/Qdrant/Pinecone service to run). If/when scale demands it, this
module is the only place that needs to change - swap the SQL fetch +
numpy similarity below for a FAISS/Qdrant/pgvector query, the rest of the
RAG pipeline (retriever/generator) is unaffected.
"""
import json

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chunk import DocumentChunk


async def similarity_search(
    db: AsyncSession,
    user_id: str,
    query_embedding: list[float],
    top_k: int,
    document_ids: list[str] | None = None,
) -> list[tuple[DocumentChunk, float]]:
    stmt = select(DocumentChunk).where(DocumentChunk.user_id == user_id)
    if document_ids:
        stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

    result = await db.execute(stmt)
    candidates = result.scalars().all()
    if not candidates:
        return []

    query_vec = np.array(query_embedding, dtype=np.float32)
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return []

    scored: list[tuple[DocumentChunk, float]] = []
    for chunk in candidates:
        try:
            vec = np.array(json.loads(chunk.embedding_json), dtype=np.float32)
        except (json.JSONDecodeError, TypeError):
            continue
        vec_norm = np.linalg.norm(vec)
        if vec_norm == 0:
            continue
        score = float(np.dot(query_vec, vec) / (query_norm * vec_norm))
        scored.append((chunk, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]
