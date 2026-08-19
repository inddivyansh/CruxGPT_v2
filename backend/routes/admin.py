from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from models.user import User
from schemas.admin import AdminStatsResponse
from services import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(_: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return await admin_service.get_admin_stats(db)
