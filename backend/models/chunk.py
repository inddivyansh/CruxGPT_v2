from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from models.user import _now, _uuid


class DocumentChunk(Base):
    """
    One chunk of a document plus its embedding.

    The embedding is stored as a JSON-encoded list of floats in a TEXT
    column. This keeps the vector store abstraction (rag/vector_store.py)
    swappable later (FAISS/Qdrant/pgvector) without touching this schema -
    every vector row already carries user_id/document_id/page/section, which
    is the hard requirement for per-user isolation.
    """

    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)

    embedding_json: Mapped[str] = mapped_column(Text)  # JSON list[float]
    embedding_dim: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(default=_now)
