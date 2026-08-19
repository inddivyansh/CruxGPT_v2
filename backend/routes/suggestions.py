from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security import InvalidTokenError, decode_token
from models.suggestion import Suggestion
from models.user import User
from schemas.suggestion import SuggestionRequest

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])


async def _optional_user(
    authorization: str | None = Header(default=None), db: AsyncSession = Depends(get_db)
) -> User | None:
    """Suggestions can be submitted anonymously, but if the user is logged
    in we prefer their account's email/organization over anything (or
    nothing) supplied in the form, per spec section 30."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = decode_token(token, expected_type="access")
    except InvalidTokenError:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


@router.post("", status_code=201)
async def submit_suggestion(
    payload: SuggestionRequest,
    user: User | None = Depends(_optional_user),
    db: AsyncSession = Depends(get_db),
):
    suggestion = Suggestion(
        user_id=user.id if user else None,
        email=(user.email if user else payload.email) or "anonymous@unknown",
        organization=(user.organization if user else payload.organization),
        contact=payload.contact,
        suggestion=payload.suggestion,
    )
    db.add(suggestion)
    await db.commit()
    return {"status": "received"}
