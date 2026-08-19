import uuid
from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    date_of_birth: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    family_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    father_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mother_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    citizenship: Mapped[str | None] = mapped_column(String(100), nullable=True)
    disability_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    critical_illness: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    annual_income: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employment_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pin_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dependents_count: Mapped[int | None] = mapped_column(nullable=True)
    smoker_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    alcohol_use: Mapped[str | None] = mapped_column(String(50), nullable=True)
    existing_conditions: Mapped[str | None] = mapped_column(String(500), nullable=True)
    insurance_history: Mapped[str | None] = mapped_column(String(500), nullable=True)
    nominee_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nominee_relation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user")  # "user" | "admin"
    created_at: Mapped[datetime] = mapped_column(default=_now)
    updated_at: Mapped[datetime] = mapped_column(default=_now, onupdate=_now)
