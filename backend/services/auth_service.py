from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import DuplicateEmailError, InvalidCredentialsError, UnauthorizedError
from app.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.user import User
from schemas.auth import RegisterRequest, TokenResponse


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise DuplicateEmailError()

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        organization=payload.organization,
        phone=payload.phone,
        age=payload.age,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        marital_status=payload.marital_status,
        family_status=payload.family_status,
        father_name=payload.father_name,
        mother_name=payload.mother_name,
        citizenship=payload.citizenship,
        disability_status=payload.disability_status,
        critical_illness=payload.critical_illness,
        occupation=payload.occupation,
        employer=payload.employer,
        annual_income=payload.annual_income,
        employment_status=payload.employment_status,
        education_level=payload.education_level,
        address=payload.address,
        country=payload.country,
        state=payload.state,
        city=payload.city,
        pin_code=payload.pin_code,
        dependents_count=payload.dependents_count,
        smoker_status=payload.smoker_status,
        alcohol_use=payload.alcohol_use,
        existing_conditions=payload.existing_conditions,
        insurance_history=payload.insurance_history,
        nominee_name=payload.nominee_name,
        nominee_relation=payload.nominee_relation,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_phone=payload.emergency_contact_phone,
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    return user


def issue_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    try:
        user_id = decode_token(refresh_token, expected_type="refresh")
    except InvalidTokenError as exc:
        raise UnauthorizedError("Refresh token is invalid or expired.") from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User account no longer exists.")

    return issue_tokens(user)
