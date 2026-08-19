from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    organization: str | None = Field(default=None, max_length=255)
    phone: str = Field(min_length=7, max_length=20)
    age: int = Field(ge=0, le=150)
    gender: str = Field(min_length=1, max_length=50)
    marital_status: str = Field(min_length=1, max_length=50)
    citizenship: str = Field(min_length=1, max_length=100)
    occupation: str = Field(min_length=1, max_length=255)
    employment_status: str = Field(min_length=1, max_length=100)
    annual_income: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=500)
    country: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    pin_code: str = Field(min_length=4, max_length=20)
    smoker_status: str = Field(min_length=1, max_length=50)
    existing_conditions: str = Field(min_length=1, max_length=500)
    emergency_contact_name: str = Field(min_length=1, max_length=255)
    emergency_contact_phone: str = Field(min_length=7, max_length=20)
    education_level: str | None = Field(default=None, max_length=100)
    family_status: str | None = Field(default=None, max_length=100)
    father_name: str | None = Field(default=None, max_length=255)
    mother_name: str | None = Field(default=None, max_length=255)
    disability_status: str | None = Field(default=None, max_length=100)
    critical_illness: str | None = Field(default=None, max_length=255)
    employer: str | None = Field(default=None, max_length=255)
    date_of_birth: str | None = Field(default=None, max_length=20)
    dependents_count: int | None = Field(default=None, ge=0, le=50)
    alcohol_use: str | None = Field(default=None, max_length=50)
    insurance_history: str | None = Field(default=None, max_length=500)
    nominee_name: str | None = Field(default=None, max_length=255)
    nominee_relation: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
