"""
Vector store.

Supports both PostgreSQL native pgvector similarity search and Python/NumPy
in-memory cosine similarity fallback (on SQLite or legacy datasets).
Always filtered by user_id and document_ids at the SQL level to enforce
multi-user and multi-conversation isolation.
"""
import json

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.chunk import DocumentChunk


async def _try_pgvector_search(
    db: AsyncSession,
    user_id: str,
    query_embedding: list[float],
    top_k: int,
    document_ids: list[str],
) -> list[tuple[DocumentChunk, float]] | None:
    """Execute native pgvector cosine similarity search when available on PostgreSQL."""
    bind = db.bind
    if bind is None and hasattr(db, "get_bind"):
        bind = db.get_bind()

    dialect_name = getattr(getattr(bind, "dialect", None), "name", "")
    if dialect_name != "postgresql":
        return None

    try:
        query_vec_str = "[" + ",".join(f"{x:.6f}" for x in query_embedding) + "]"
        stmt = text(
            """
            SELECT id, (1.0 - (embedding <=> CAST(:query_vec AS vector))) AS similarity_score
            FROM document_chunks
            WHERE user_id = :user_id
              AND document_id = ANY(:document_ids)
              AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:query_vec AS vector)
            LIMIT :top_k
            """
        )
        res = await db.execute(
            stmt,
            {
                "user_id": user_id,
                "document_ids": document_ids,
                "query_vec": query_vec_str,
                "top_k": top_k,
            },
        )
        rows = res.fetchall()
        if not rows:
            return None

        chunk_ids = [row[0] for row in rows]
        score_by_id = {row[0]: float(row[1]) for row in rows}

        chunks_res = await db.execute(select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids)))
        chunk_by_id = {c.id: c for c in chunks_res.scalars().all()}

        ordered_scored: list[tuple[DocumentChunk, float]] = []
        for cid in chunk_ids:
            chunk = chunk_by_id.get(cid)
            if chunk is not None:
                ordered_scored.append((chunk, score_by_id.get(cid, 0.0)))
        return ordered_scored
    except Exception:
        # If pgvector extension/column is not enabled or fails, smoothly fall back to NumPy
        return None


async def similarity_search(
    db: AsyncSession,
    user_id: str,
    query_embedding: list[float],
    top_k: int,
    document_ids: list[str],
) -> list[tuple[DocumentChunk, float]]:
    if not document_ids:
        return []

    # 1. Attempt pgvector native search on PostgreSQL
    pgvector_results = await _try_pgvector_search(db, user_id, query_embedding, top_k, document_ids)
    if pgvector_results is not None:
        return pgvector_results

    # 2. Python/NumPy cosine similarity fallback
    stmt = select(DocumentChunk).where(
        DocumentChunk.user_id == user_id,
        DocumentChunk.document_id.in_(document_ids),
    )

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
