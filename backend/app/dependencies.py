"""
Auth dependencies.

get_current_user is the single place that resolves "who is making this
request" from a verified JWT. Every protected route depends on this rather
than trusting any user_id the client might send in a request body - per the
spec's multi-user isolation requirement, the frontend is never trusted to
say who it is.
"""
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.errors import ForbiddenError, UnauthorizedError
from app.security import InvalidTokenError, decode_token
from models.user import User


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header.")

    token = authorization.split(" ", 1)[1].strip()

    try:
        user_id = decode_token(token, expected_type="access")
    except InvalidTokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User account no longer exists.")

    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise ForbiddenError("This endpoint requires administrator access.")
    return user
