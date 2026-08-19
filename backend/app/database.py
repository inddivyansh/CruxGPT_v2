"""
Async SQLAlchemy engine/session setup.

Uses SQLite by default for local development, while supporting PostgreSQL
(e.g. Neon) in production through asyncpg.
"""

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


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
