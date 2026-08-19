from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    # Only name, email, and password are required
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    # All profile fields are optional
    organization: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    age: int | None = Field(default=None, ge=0, le=150)
    gender: str | None = Field(default=None, max_length=50)
    marital_status: str | None = Field(default=None, max_length=50)
    citizenship: str | None = Field(default=None, max_length=100)
    occupation: str | None = Field(default=None, max_length=255)
    employment_status: str | None = Field(default=None, max_length=100)
    annual_income: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=500)
    country: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    pin_code: str | None = Field(default=None, min_length=4, max_length=20)
    smoker_status: str | None = Field(default=None, max_length=50)
    existing_conditions: str | None = Field(default=None, max_length=500)
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, min_length=7, max_length=20)
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

    @field_validator(
        "phone",
        "pin_code",
        "emergency_contact_phone",
        "organization",
        "gender",
        "marital_status",
        "citizenship",
        "occupation",
        "employment_status",
        "annual_income",
        "address",
        "country",
        "state",
        "city",
        "smoker_status",
        "existing_conditions",
        "emergency_contact_name",
        "education_level",
        "family_status",
        "father_name",
        "mother_name",
        "disability_status",
        "critical_illness",
        "employer",
        "date_of_birth",
        "alcohol_use",
        "insurance_history",
        "nominee_name",
        "nominee_relation",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("age", "dependents_count", mode="before")
    @classmethod
    def empty_int_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
