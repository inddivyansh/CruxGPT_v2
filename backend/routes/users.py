from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from models.user import User
from schemas.user import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.name is not None:
        user.name = payload.name
    if payload.organization is not None:
        user.organization = payload.organization
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.age is not None:
        user.age = payload.age
    if payload.date_of_birth is not None:
        user.date_of_birth = payload.date_of_birth
    if payload.gender is not None:
        user.gender = payload.gender
    if payload.marital_status is not None:
        user.marital_status = payload.marital_status
    if payload.family_status is not None:
        user.family_status = payload.family_status
    if payload.father_name is not None:
        user.father_name = payload.father_name
    if payload.mother_name is not None:
        user.mother_name = payload.mother_name
    if payload.citizenship is not None:
        user.citizenship = payload.citizenship
    if payload.disability_status is not None:
        user.disability_status = payload.disability_status
    if payload.critical_illness is not None:
        user.critical_illness = payload.critical_illness
    if payload.occupation is not None:
        user.occupation = payload.occupation
    if payload.employer is not None:
        user.employer = payload.employer
    if payload.annual_income is not None:
        user.annual_income = payload.annual_income
    if payload.employment_status is not None:
        user.employment_status = payload.employment_status
    if payload.education_level is not None:
        user.education_level = payload.education_level
    if payload.address is not None:
        user.address = payload.address
    if payload.country is not None:
        user.country = payload.country
    if payload.state is not None:
        user.state = payload.state
    if payload.city is not None:
        user.city = payload.city
    if payload.pin_code is not None:
        user.pin_code = payload.pin_code
    if payload.dependents_count is not None:
        user.dependents_count = payload.dependents_count
    if payload.smoker_status is not None:
        user.smoker_status = payload.smoker_status
    if payload.alcohol_use is not None:
        user.alcohol_use = payload.alcohol_use
    if payload.existing_conditions is not None:
        user.existing_conditions = payload.existing_conditions
    if payload.insurance_history is not None:
        user.insurance_history = payload.insurance_history
    if payload.nominee_name is not None:
        user.nominee_name = payload.nominee_name
    if payload.nominee_relation is not None:
        user.nominee_relation = payload.nominee_relation
    if payload.emergency_contact_name is not None:
        user.emergency_contact_name = payload.emergency_contact_name
    if payload.emergency_contact_phone is not None:
        user.emergency_contact_phone = payload.emergency_contact_phone
    await db.commit()
    await db.refresh(user)
    return user
