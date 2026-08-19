from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from models.user import _now, _uuid


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_uuid,
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id"),
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20)
    )

    content: Mapped[str] = mapped_column(
        Text
    )

    sources_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    action: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    processing_time: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now,
    )
