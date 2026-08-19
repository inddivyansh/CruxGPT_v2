from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from models.user import User
from schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from schemas.user import UserResponse
from services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, payload)
    return auth_service.issue_tokens(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, payload.email, payload.password)
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_access_token(db, payload.refresh_token)


@router.post("/logout", status_code=204)
async def logout(user: User = Depends(get_current_user)):
    # Stateless JWTs: logout is enforced client-side by discarding the tokens.
    # For server-side revocation, swap in a token blocklist/refresh-token table.
    return None


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user
