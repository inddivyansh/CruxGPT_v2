from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from models.user import _now, _uuid


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    filename: Mapped[str] = mapped_column(String(255))  # safe, generated storage filename
    original_filename: Mapped[str] = mapped_column(String(255))  # never trusted for paths
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)

    # uploaded -> processing -> indexed | failed
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    storage_path: Mapped[str] = mapped_column(String(500))  # server-internal path, never sent to client
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
