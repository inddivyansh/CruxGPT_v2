from datetime import datetime

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    organization: str | None
    phone: str | None = None
    age: int | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    marital_status: str | None = None
    family_status: str | None = None
    father_name: str | None = None
    mother_name: str | None = None
    citizenship: str | None = None
    disability_status: str | None = None
    critical_illness: str | None = None
    occupation: str | None = None
    employer: str | None = None
    annual_income: str | None = None
    employment_status: str | None = None
    education_level: str | None = None
    address: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    pin_code: str | None = None
    dependents_count: int | None = None
    smoker_status: str | None = None
    alcohol_use: str | None = None
    existing_conditions: str | None = None
    insurance_history: str | None = None
    nominee_name: str | None = None
    nominee_relation: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    organization: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    age: int | None = Field(default=None, ge=0, le=150)
    date_of_birth: str | None = Field(default=None, max_length=20)
    gender: str | None = Field(default=None, max_length=50)
    marital_status: str | None = Field(default=None, max_length=50)
    family_status: str | None = Field(default=None, max_length=100)
    father_name: str | None = Field(default=None, max_length=255)
    mother_name: str | None = Field(default=None, max_length=255)
    citizenship: str | None = Field(default=None, max_length=100)
    disability_status: str | None = Field(default=None, max_length=100)
    critical_illness: str | None = Field(default=None, max_length=255)
    occupation: str | None = Field(default=None, max_length=255)
    employer: str | None = Field(default=None, max_length=255)
    annual_income: str | None = Field(default=None, max_length=100)
    employment_status: str | None = Field(default=None, max_length=100)
    education_level: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=500)
    country: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    pin_code: str | None = Field(default=None, max_length=20)
    dependents_count: int | None = Field(default=None, ge=0, le=50)
    smoker_status: str | None = Field(default=None, max_length=50)
    alcohol_use: str | None = Field(default=None, max_length=50)
    existing_conditions: str | None = Field(default=None, max_length=500)
    insurance_history: str | None = Field(default=None, max_length=500)
    nominee_name: str | None = Field(default=None, max_length=255)
    nominee_relation: str | None = Field(default=None, max_length=100)
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=50)
