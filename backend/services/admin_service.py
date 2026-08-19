"""
Admin service - real statistics instead of the frontend's hard-coded mock
values (spec section 60/27). If there isn't enough feedback data yet, the
accuracy figure honestly says so rather than showing a fabricated number.
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from models.conversation import Conversation
from models.document import Document
from models.feedback import Feedback
from models.message import Message
from models.user import User
from schemas.admin import AdminStatsResponse

MIN_FEEDBACK_FOR_ACCURACY = 10


async def get_admin_stats(db: AsyncSession) -> AdminStatsResponse:
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_documents = (await db.execute(select(func.count(Document.id)))).scalar_one()
    total_conversations = (await db.execute(select(func.count(Conversation.id)))).scalar_one()

    positive_feedback = (
        await db.execute(select(func.count(Feedback.id)).where(Feedback.feedback == "positive"))
    ).scalar_one()
    negative_feedback = (
        await db.execute(select(func.count(Feedback.id)).where(Feedback.feedback == "negative"))
    ).scalar_one()

    total_feedback = positive_feedback + negative_feedback
    if total_feedback >= MIN_FEEDBACK_FOR_ACCURACY:
        overall_accuracy: float | str = round((positive_feedback / total_feedback) * 100, 1)
    else:
        overall_accuracy = "Not enough evaluation data"

    avg_response_time = (
        await db.execute(select(func.avg(Message.processing_time)).where(Message.role == "assistant"))
    ).scalar_one()

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    queries_today = (
        await db.execute(
            select(func.count(Message.id)).where(Message.role == "user", Message.created_at >= today_start)
        )
    ).scalar_one()

    return AdminStatsResponse(
        overall_accuracy=overall_accuracy,
        average_response_time=round(avg_response_time, 2) if avg_response_time else 0.0,
        queries_today=queries_today,
        total_users=total_users,
        total_documents=total_documents,
        total_conversations=total_conversations,
        positive_feedback=positive_feedback,
        negative_feedback=negative_feedback,
        system_status="operational",
        rag_pipeline="active" if settings.gemini_api_key else "inactive (GEMINI_API_KEY not set)",
        maintenance_mode=False,
    )
