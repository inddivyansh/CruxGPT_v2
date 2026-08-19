from datetime import datetime

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from models.user import _now, _uuid


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), index=True)

    role: Mapped[str] = mapped_column(String(20))  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text)

    # JSON-encoded list of source dicts: [{document_id, document_name, page, section, text, relevance_score}]
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    action: Mapped[str | None] = mapped_column(String(30), nullable=True)  # quick-action type, if any
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_time: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=_now)
