"""
Chat service - the RAG query pipeline with caching, pgvector support,
timing observability, and strict structured JSON responses.

query -> (cache check) -> (retrieve + rank candidates + diversity prune) ->
(1 Gemini generation) -> (cache store) -> persist messages -> return response.
"""
import json
import logging
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConversationNotFoundError, DocumentNotFoundError
from models.conversation import Conversation
from models.document import Document
from models.message import Message
from rag.cache import get_response_cache
from rag.generator import get_generator
from rag.prompt import format_context, format_history, select_context_chunks
from rag.retriever import build_retrieval_query, retrieve_chunks
from schemas.chat import ChatRequest, ChatResponse, SourceItem

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 8


async def _get_or_create_conversation(db: AsyncSession, user_id: str, conversation_id: str | None) -> Conversation:
    if conversation_id:
        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conversation = result.scalar_one_or_none()
        if conversation is None or conversation.user_id != user_id:
            raise ConversationNotFoundError()
        return conversation

    conversation = Conversation(user_id=user_id, title="New conversation")
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def _recent_history(db: AsyncSession, conversation_id: str) -> list[dict]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(MAX_HISTORY_MESSAGES)
    )
    messages = list(result.scalars().all())
    messages.reverse()
    return [{"role": m.role, "content": m.content} for m in messages]


async def _last_user_message(db: AsyncSession, conversation_id: str) -> str | None:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.role == "user")
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    msg = result.scalar_one_or_none()
    return msg.content if msg else None


async def _conversation_documents(
    db: AsyncSession,
    user_id: str,
    conversation_id: str,
    requested_document_ids: list[str],
) -> list[Document]:
    """Resolve documents owned by this user and attached to this conversation."""
    requested_ids = list(dict.fromkeys(requested_document_ids))
    stmt = select(Document).where(
        Document.user_id == user_id,
        Document.conversation_id == conversation_id,
    )
    if requested_ids:
        result = await db.execute(stmt.where(Document.id.in_(requested_ids)))
        docs = list(result.scalars().all())
        if len(docs) != len(requested_ids):
            # Match existing no-information-leak behavior for documents.
            raise DocumentNotFoundError()
        return docs

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def answer_query(db: AsyncSession, user_id: str, payload: ChatRequest) -> ChatResponse:
    start = time.monotonic()
    t_retrieval_start = start
    t_retrieval_end = start
    t_context_start = start
    t_context_end = start
    t_gen_start = start
    t_gen_end = start

    conversation = await _get_or_create_conversation(db, user_id, payload.conversation_id)

    docs = await _conversation_documents(
        db,
        user_id,
        conversation.id,
        payload.document_ids,
    )
    conversation_document_ids = [d.id for d in docs]
    document_names = {d.id: d.original_filename for d in docs}
    document_snapshots = [
        (d.id, d.content_sha256, d.updated_at.isoformat() if d.updated_at else "")
        for d in docs
    ]

    history = await _recent_history(db, conversation.id)
    previous_user_message = await _last_user_message(db, conversation.id)

    # 1. Response Cache Check
    cache = get_response_cache()
    cache_key = cache.compute_cache_key(
        user_id=user_id,
        conversation_id=conversation.id,
        query=payload.message,
        action=payload.action,
        document_snapshots=document_snapshots,
    )
    cached_payload = cache.get(cache_key)

    if cached_payload is not None:
        # Cache hit: 0 embedding calls + 0 generation calls
        user_message = Message(conversation_id=conversation.id, role="user", content=payload.message, action=payload.action)
        db.add(user_message)
        await db.commit()

        processing_time = round(time.monotonic() - start, 3)
        sources = [SourceItem(**s) for s in cached_payload.get("sources", [])]

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=cached_payload.get("answer", ""),
            sources_json=json.dumps([s.model_dump() for s in sources]),
            action=payload.action,
            confidence=cached_payload.get("confidence"),
            processing_time=processing_time,
        )
        db.add(assistant_message)
        if conversation.title == "New conversation":
            conversation.title = payload.message[:80]
        await db.commit()
        await db.refresh(assistant_message)

        total_ms = (time.monotonic() - start) * 1000
        logger.info(
            "[chat_timing] cache_hit=True query_embedding_ms=0.0 retrieval_ms=0.0 context_ms=0.0 generation_ms=0.0 total_ms=%.1f",
            total_ms,
        )

        return ChatResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            answer=cached_payload.get("answer", ""),
            summary=cached_payload.get("summary"),
            key_points=cached_payload.get("key_points", []),
            decision=cached_payload.get("decision"),
            conditions=cached_payload.get("conditions", []),
            exclusions=cached_payload.get("exclusions", []),
            sources=sources,
            confidence=cached_payload.get("confidence"),
            insufficient_context=cached_payload.get("insufficient_context", False),
            processing_time=processing_time,
        )

    # 2. Cache Miss: Persist user message first
    user_message = Message(conversation_id=conversation.id, role="user", content=payload.message, action=payload.action)
    db.add(user_message)
    await db.commit()

    # 3. Candidate Retrieval & Vector Search
    t_retrieval_start = time.monotonic()
    retrieval_query = build_retrieval_query(payload.message, previous_user_message)
    scored_chunks = await retrieve_chunks(
        db=db,
        user_id=user_id,
        query=retrieval_query,
        document_ids=conversation_document_ids,
    )
    t_retrieval_end = time.monotonic()

    # 4. Context Construction with Diversity and Redundancy Filtering
    t_context_start = time.monotonic()
    context_chunks = select_context_chunks(scored_chunks, document_names)
    context = format_context(context_chunks, document_names)
    history_text = format_history(history)
    t_context_end = time.monotonic()

    # 5. Single Structured Gemini Generation
    t_gen_start = time.monotonic()
    generator = get_generator()
    generation = await generator.generate(
        query=payload.message, action=payload.action, context=context, history=history_text
    )
    t_gen_end = time.monotonic()

    sources = [
        SourceItem(
            document_id=chunk.document_id,
            document_name=document_names.get(chunk.document_id, "Unknown document"),
            page=chunk.page_number,
            section=chunk.section,
            text=chunk.text[:400],
            relevance_score=round(score, 4),
        )
        for chunk, score in context_chunks
    ]

    processing_time = round(time.monotonic() - start, 3)

    gen_answer = getattr(generation, "answer", "") or ""
    gen_summary = getattr(generation, "summary", None)
    gen_key_points = list(getattr(generation, "key_points", []) or [])
    gen_decision = getattr(generation, "decision", None)
    gen_conditions = list(getattr(generation, "conditions", []) or [])
    gen_exclusions = list(getattr(generation, "exclusions", []) or [])
    gen_confidence = getattr(generation, "confidence", None)
    gen_insufficient_context = bool(getattr(generation, "insufficient_context", False))

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=gen_answer,
        sources_json=json.dumps([s.model_dump() for s in sources]),
        action=payload.action,
        confidence=gen_confidence,
        processing_time=processing_time,
    )
    db.add(assistant_message)

    if conversation.title == "New conversation":
        conversation.title = payload.message[:80]

    await db.commit()
    await db.refresh(assistant_message)

    # 6. Store in Response Cache
    cache_entry = {
        "answer": gen_answer,
        "summary": gen_summary,
        "key_points": gen_key_points,
        "decision": gen_decision,
        "conditions": gen_conditions,
        "exclusions": gen_exclusions,
        "sources": [s.model_dump() for s in sources],
        "confidence": gen_confidence,
        "insufficient_context": gen_insufficient_context,
    }
    cache.set(cache_key, cache_entry)

    retrieval_ms = (t_retrieval_end - t_retrieval_start) * 1000
    context_ms = (t_context_end - t_context_start) * 1000
    generation_ms = (t_gen_end - t_gen_start) * 1000
    total_ms = (time.monotonic() - start) * 1000

    logger.info(
        "[chat_timing] cache_hit=False retrieval_ms=%.1f context_ms=%.1f generation_ms=%.1f total_ms=%.1f",
        retrieval_ms,
        context_ms,
        generation_ms,
        total_ms,
    )

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        answer=gen_answer,
        summary=gen_summary,
        key_points=gen_key_points,
        decision=gen_decision,
        conditions=gen_conditions,
        exclusions=gen_exclusions,
        sources=sources,
        confidence=gen_confidence,
        insufficient_context=gen_insufficient_context,
        processing_time=processing_time,
    )
