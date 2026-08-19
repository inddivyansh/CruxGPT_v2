from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from models.user import _now, _uuid


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_user_content_sha256", "user_id", "content_sha256"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("conversations.id"), index=True, nullable=True
    )

    filename: Mapped[str] = mapped_column(String(255))  # safe, generated storage filename
    original_filename: Mapped[str] = mapped_column(String(255))  # never trusted for paths
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    # Nullable for documents created before content-addressed deduplication.
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Identifies the model that generated this document's stored chunk vectors.
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # uploaded -> processing -> indexed | failed
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    storage_path: Mapped[str] = mapped_column(String(500))  # server-internal path, never sent to client
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
