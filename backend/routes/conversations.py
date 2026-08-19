import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.errors import ConversationNotFoundError
from models.conversation import Conversation
from models.message import Message
from models.user import User
from schemas.conversation import (
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


async def _get_owned_conversation(db: AsyncSession, user_id: str, conversation_id: str) -> Conversation:
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    if conversation is None or conversation.user_id != user_id:
        raise ConversationNotFoundError()
    return conversation


def _to_message_response(message: Message) -> MessageResponse:
    sources = json.loads(message.sources_json) if message.sources_json else []
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        sources=sources,
        action=message.action,
        confidence=message.confidence,
        created_at=message.created_at,
    )


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    payload: ConversationCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = Conversation(user_id=user.id, title=payload.title or "New conversation")
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    conversation = await _get_owned_conversation(db, user.id, conversation_id)
    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at.asc())
    )
    messages = [_to_message_response(m) for m in result.scalars().all()]
    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages,
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    conversation = await _get_owned_conversation(db, user.id, conversation_id)
    await db.execute(
        Message.__table__.delete().where(Message.conversation_id == conversation.id)
    )
    await db.delete(conversation)
    await db.commit()
    return None
