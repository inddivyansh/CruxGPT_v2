"""
Async SQLAlchemy engine/session setup.

Uses SQLite by default so the project runs with zero external setup, but the
models use only portable SQLAlchemy types, so pointing DATABASE_URL at
Postgres (e.g. postgresql+asyncpg://...) works without any model changes.
"""
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, echo=False, connect_args=connect_args)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db():
    """FastAPI dependency that yields a request-scoped DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create tables on startup. For production, replace with Alembic migrations."""
    # Import models so they're registered on Base.metadata before create_all
    from models import chunk, conversation, document, feedback, message, suggestion, user  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_user_table)


def _migrate_user_table(sync_conn) -> None:
    """Add newly introduced user profile columns to older SQLite databases."""
    inspector = inspect(sync_conn)
    if not inspector.has_table('users'):
        return

    existing_columns = {column['name'] for column in inspector.get_columns('users')}
    user_columns = {
        'phone': 'VARCHAR(50)',
        'age': 'INTEGER',
        'date_of_birth': 'VARCHAR(20)',
        'gender': 'VARCHAR(50)',
        'marital_status': 'VARCHAR(50)',
        'family_status': 'VARCHAR(100)',
        'father_name': 'VARCHAR(255)',
        'mother_name': 'VARCHAR(255)',
        'citizenship': 'VARCHAR(100)',
        'disability_status': 'VARCHAR(100)',
        'critical_illness': 'VARCHAR(255)',
        'occupation': 'VARCHAR(255)',
        'employer': 'VARCHAR(255)',
        'annual_income': 'VARCHAR(100)',
        'employment_status': 'VARCHAR(100)',
        'education_level': 'VARCHAR(100)',
        'address': 'VARCHAR(500)',
        'country': 'VARCHAR(100)',
        'state': 'VARCHAR(100)',
        'city': 'VARCHAR(100)',
        'pin_code': 'VARCHAR(20)',
        'dependents_count': 'INTEGER',
        'smoker_status': 'VARCHAR(50)',
        'alcohol_use': 'VARCHAR(50)',
        'existing_conditions': 'VARCHAR(500)',
        'insurance_history': 'VARCHAR(500)',
        'nominee_name': 'VARCHAR(255)',
        'nominee_relation': 'VARCHAR(100)',
        'emergency_contact_name': 'VARCHAR(255)',
        'emergency_contact_phone': 'VARCHAR(50)',
    }

    for column_name, column_type in user_columns.items():
        if column_name not in existing_columns:
            sync_conn.execute(text(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}'))
