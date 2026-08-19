"""
Retriever: query -> query embedding -> vector search -> top-K chunks.

Query rewriting (spec section 41) is intentionally left as a simple, cheap
heuristic rather than an extra LLM call: it only fires for short
conversational follow-ups, and just prepends the previous user question for
retrieval purposes. This avoids doubling LLM latency/cost on every turn
while still helping pronoun-heavy follow-ups ("what about surgery?") retrieve
the right chunks. It's the one spot to upgrade to an LLM-based rewrite later
if retrieval quality demands it.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from models.chunk import DocumentChunk
from rag.embeddings import get_embedding_service
from rag.vector_store import similarity_search


def build_retrieval_query(current_message: str, previous_user_message: str | None) -> str:
    if previous_user_message and len(current_message.strip()) < 60:
        return f"{previous_user_message}\n{current_message}"
    return current_message


async def retrieve_chunks(
    db: AsyncSession,
    user_id: str,
    query: str,
    document_ids: list[str] | None = None,
    top_k: int | None = None,
) -> list[tuple[DocumentChunk, float]]:
    # Callers resolve this list from the authenticated conversation. An empty
    # conversation must never fall back to searching all of a user's chunks.
    if not document_ids:
        return []

    embedding_service = get_embedding_service()
    query_embedding = await embedding_service.embed_query(query)
    return await similarity_search(
        db=db,
        user_id=user_id,
        query_embedding=query_embedding,
        top_k=top_k or settings.retrieval_top_k,
        document_ids=document_ids,
    )
