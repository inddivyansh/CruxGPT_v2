from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.errors import AppError
from models.conversation import Conversation
from models.feedback import Feedback
from models.message import Message
from models.user import User
from schemas.feedback import FeedbackRequest

router = APIRouter(prefix="/api/messages", tags=["feedback"])


@router.post("/{message_id}/feedback", status_code=201)
async def submit_feedback(
    message_id: str,
    payload: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    if message is None:
        raise AppError("MESSAGE_NOT_FOUND", "The requested message could not be found.", status.HTTP_404_NOT_FOUND)

    conv_result = await db.execute(select(Conversation).where(Conversation.id == message.conversation_id))
    conversation = conv_result.scalar_one_or_none()
    if conversation is None or conversation.user_id != user.id:
        raise AppError("MESSAGE_NOT_FOUND", "The requested message could not be found.", status.HTTP_404_NOT_FOUND)

    feedback = Feedback(message_id=message_id, user_id=user.id, feedback=payload.feedback, reason=payload.reason)
    db.add(feedback)
    await db.commit()
    return {"status": "recorded"}
