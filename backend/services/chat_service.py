"""
Chat service - the RAG query pipeline described in spec sections 18/39/42.

query -> (load/create conversation) -> bounded recent history -> retrieval
query rewrite -> embed -> vector search (user-scoped) -> build context ->
LLM -> structured result -> persist messages -> return answer + sources.
"""
import json
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConversationNotFoundError
from models.conversation import Conversation
from models.document import Document
from models.message import Message
from rag.generator import get_generator
from rag.prompt import format_context, format_history
from rag.retriever import build_retrieval_query, retrieve_chunks
from schemas.chat import ChatRequest, ChatResponse, SourceItem

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


async def answer_query(db: AsyncSession, user_id: str, payload: ChatRequest) -> ChatResponse:
    start = time.monotonic()

    conversation = await _get_or_create_conversation(db, user_id, payload.conversation_id)

    history = await _recent_history(db, conversation.id)
    previous_user_message = await _last_user_message(db, conversation.id)

    # Persist the user's message first so it's never lost even if generation fails downstream.
    user_message = Message(conversation_id=conversation.id, role="user", content=payload.message, action=payload.action)
    db.add(user_message)
    await db.commit()

    retrieval_query = build_retrieval_query(payload.message, previous_user_message)
    scored_chunks = await retrieve_chunks(
        db=db,
        user_id=user_id,
        query=retrieval_query,
        document_ids=payload.document_ids or None,
    )

    document_ids = list({c.document_id for c, _ in scored_chunks})
    document_names: dict[str, str] = {}
    if document_ids:
        doc_result = await db.execute(select(Document).where(Document.id.in_(document_ids)))
        document_names = {d.id: d.original_filename for d in doc_result.scalars().all()}

    context = format_context(scored_chunks, document_names)
    history_text = format_history(history)

    generator = get_generator()
    generation = await generator.generate(
        query=payload.message, action=payload.action, context=context, history=history_text
    )

    sources = [
        SourceItem(
            document_id=chunk.document_id,
            document_name=document_names.get(chunk.document_id, "Unknown document"),
            page=chunk.page_number,
            section=chunk.section,
            text=chunk.text[:400],
            relevance_score=round(score, 4),
        )
        for chunk, score in scored_chunks
    ]

    processing_time = round(time.monotonic() - start, 3)

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=generation.answer,
        sources_json=json.dumps([s.model_dump() for s in sources]),
        action=payload.action,
        confidence=generation.confidence,
        processing_time=processing_time,
    )
    db.add(assistant_message)

    # Auto-title new conversations from the first user message
    if conversation.title == "New conversation":
        conversation.title = payload.message[:80]

    await db.commit()
    await db.refresh(assistant_message)

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        answer=generation.answer,
        decision=generation.decision,
        conditions=generation.conditions,
        exclusions=generation.exclusions,
        sources=sources,
        confidence=generation.confidence,
        processing_time=processing_time,
    )
