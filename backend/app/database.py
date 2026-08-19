"""
Async SQLAlchemy engine/session setup.

Uses SQLite by default for local development, while supporting PostgreSQL
(e.g. Neon) in production through asyncpg.
"""

from datetime import datetime

from sqlalchemy import DateTime, inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }


# ---------------------------------------------------------------------------
# Database engine configuration
# ---------------------------------------------------------------------------

database_url = settings.database_url
connect_args = {}

if database_url.startswith("sqlite"):
    # SQLite: local development
    connect_args = {"check_same_thread": False}

else:
    # PostgreSQL / Neon:
    # SQLAlchemy asyncpg requires the asyncpg dialect.
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

    # asyncpg does not accept the libpq-style `sslmode` parameter.
    # Neon requires SSL, so remove sslmode from the URL and provide
    # SSL explicitly through connect_args.
    if database_url.startswith("postgresql+asyncpg://"):
        if "?" in database_url:
            base_url, query = database_url.split("?", 1)

            query_parts = [
                part
                for part in query.split("&")
                if not part.startswith("sslmode=")
            ]

            database_url = base_url

            if query_parts:
                database_url += "?" + "&".join(query_parts)

        connect_args = {
            "ssl": True,
        }


engine = create_async_engine(
    database_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# FastAPI database dependency
# ---------------------------------------------------------------------------

async def get_db():
    """FastAPI dependency that yields a request-scoped DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

async def init_db():
    """Create tables on startup.

    For production, replace create_all with Alembic migrations once the
    production schema is stable.
    """

    # Import models so they're registered on Base.metadata before create_all
    from models import (
        chunk,
        conversation,
        document,
        feedback,
        message,
        suggestion,
        user,
    )  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_user_table)
        await conn.run_sync(_migrate_document_conversation_id)
        await conn.run_sync(_migrate_document_embedding_metadata)
        await conn.run_sync(_migrate_timestamp_columns)
        await conn.run_sync(_migrate_pgvector)


# ---------------------------------------------------------------------------
# User table migration
# ---------------------------------------------------------------------------

def _migrate_user_table(sync_conn) -> None:
    """Add newly introduced user profile columns to older databases."""

    inspector = inspect(sync_conn)

    if not inspector.has_table("users"):
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    user_columns = {
        "phone": "VARCHAR(50)",
        "age": "INTEGER",
        "date_of_birth": "VARCHAR(20)",
        "gender": "VARCHAR(50)",
        "marital_status": "VARCHAR(50)",
        "family_status": "VARCHAR(100)",
        "father_name": "VARCHAR(255)",
        "mother_name": "VARCHAR(255)",
        "citizenship": "VARCHAR(100)",
        "disability_status": "VARCHAR(100)",
        "critical_illness": "VARCHAR(255)",
        "occupation": "VARCHAR(255)",
        "employer": "VARCHAR(255)",
        "annual_income": "VARCHAR(100)",
        "employment_status": "VARCHAR(100)",
        "education_level": "VARCHAR(100)",
        "address": "VARCHAR(500)",
        "country": "VARCHAR(100)",
        "state": "VARCHAR(100)",
        "city": "VARCHAR(100)",
        "pin_code": "VARCHAR(20)",
        "dependents_count": "INTEGER",
        "smoker_status": "VARCHAR(50)",
        "alcohol_use": "VARCHAR(50)",
        "existing_conditions": "VARCHAR(500)",
        "insurance_history": "VARCHAR(500)",
        "nominee_name": "VARCHAR(255)",
        "nominee_relation": "VARCHAR(100)",
        "emergency_contact_name": "VARCHAR(255)",
        "emergency_contact_phone": "VARCHAR(50)",
    }

    for column_name, column_type in user_columns.items():
        if column_name not in existing_columns:
            sync_conn.execute(
                text(
                    f"ALTER TABLE users "
                    f"ADD COLUMN {column_name} {column_type}"
                )
            )


def _migrate_document_conversation_id(sync_conn) -> None:
    """Add the nullable document-to-conversation association to older databases."""

    inspector = inspect(sync_conn)

    if not inspector.has_table("documents"):
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("documents")
    }
    if "conversation_id" in existing_columns:
        return

    if sync_conn.dialect.name == "postgresql":
        sync_conn.execute(text("ALTER TABLE documents ADD COLUMN conversation_id VARCHAR(36)"))
        sync_conn.execute(
            text(
                "ALTER TABLE documents "
                "ADD CONSTRAINT fk_documents_conversation_id "
                "FOREIGN KEY (conversation_id) REFERENCES conversations (id)"
            )
        )
    else:
        sync_conn.execute(
            text(
                "ALTER TABLE documents "
                "ADD COLUMN conversation_id VARCHAR(36) REFERENCES conversations (id)"
            )
        )

    sync_conn.execute(
        text("CREATE INDEX ix_documents_conversation_id ON documents (conversation_id)")
    )


def _migrate_document_embedding_metadata(sync_conn) -> None:
    """Add nullable duplicate-detection metadata without changing legacy rows."""

    inspector = inspect(sync_conn)
    if not inspector.has_table("documents"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("documents")}
    columns = {
        "content_sha256": "VARCHAR(64)",
        "embedding_model": "VARCHAR(255)",
    }
    for column_name, column_type in columns.items():
        if column_name not in existing_columns:
            sync_conn.execute(text(f"ALTER TABLE documents ADD COLUMN {column_name} {column_type}"))

    existing_indexes = {index["name"] for index in inspector.get_indexes("documents")}
    if "ix_documents_user_content_sha256" not in existing_indexes:
        sync_conn.execute(
            text(
                "CREATE INDEX ix_documents_user_content_sha256 "
                "ON documents (user_id, content_sha256)"
            )
        )


def _migrate_timestamp_columns(sync_conn) -> None:
    """Convert legacy naive timestamps to PostgreSQL timestamptz columns."""

    if sync_conn.dialect.name != "postgresql":
        return

    inspector = inspect(sync_conn)
    timestamp_columns = {
        "users": ("created_at", "updated_at"),
        "conversations": ("created_at", "updated_at"),
        "messages": ("created_at",),
        "documents": ("created_at", "updated_at"),
        "document_chunks": ("created_at",),
        "feedback": ("created_at",),
        "suggestions": ("created_at",),
    }

    for table_name, column_names in timestamp_columns.items():
        if not inspector.has_table(table_name):
            continue

        columns = {
            column["name"]: column
            for column in inspector.get_columns(table_name)
        }

        for column_name in column_names:
            column = columns.get(column_name)
            if column is None or getattr(column["type"], "timezone", False):
                continue

            sync_conn.execute(
                text(
                    f"ALTER TABLE {table_name} "
                    f"ALTER COLUMN {column_name} TYPE TIMESTAMP WITH TIME ZONE "
                    f"USING {column_name} AT TIME ZONE 'UTC'"
                )
            )


def _migrate_pgvector(sync_conn) -> None:
    """Safely prepare pgvector extension and embedding vector column on PostgreSQL."""
    if sync_conn.dialect.name != "postgresql":
        return

    inspector = inspect(sync_conn)
    if not inspector.has_table("document_chunks"):
        return

    try:
        sync_conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception:
        pass

    existing_columns = {column["name"] for column in inspector.get_columns("document_chunks")}
    if "embedding" not in existing_columns:
        from app.config import settings

        try:
            sync_conn.execute(
                text(
                    f"ALTER TABLE document_chunks "
                    f"ADD COLUMN IF NOT EXISTS embedding vector({settings.gemini_embedding_dimensions})"
                )
            )
        except Exception:
            pass
