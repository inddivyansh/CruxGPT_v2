from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from models.user import User
from schemas.chat import ChatRequest, ChatResponse
from services import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await chat_service.answer_query(db, user.id, payload)
