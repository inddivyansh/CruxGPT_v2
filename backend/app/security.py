"""
Password hashing and JWT access/refresh token handling.

Design notes:
- Passwords are hashed with bcrypt via passlib. Plaintext passwords are never
  stored or logged.
- Access tokens are short-lived and used to authenticate API requests.
- Refresh tokens are longer-lived and only used to mint new access tokens.
- The frontend must never be trusted to say who the user is - every
  protected route resolves the user from the verified JWT, never from a
  client-supplied user_id.
"""
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def _create_token(subject: str, expires_delta: timedelta, token_type: Literal["access", "refresh"]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID) -> str:
    return _create_token(
        str(user_id), timedelta(minutes=settings.access_token_expire_minutes), "access"
    )


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(
        str(user_id), timedelta(days=settings.refresh_token_expire_days), "refresh"
    )


class InvalidTokenError(Exception):
    pass


def decode_token(token: str, expected_type: Literal["access", "refresh"] = "access") -> str:
    """Returns the user_id (as string) encoded in the token, or raises InvalidTokenError."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError("Token is invalid or expired") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type} token")

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Token missing subject")

    return user_id
