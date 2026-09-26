"""
Async SQLAlchemy engine, session factory, and declarative base.

All models inherit from ``Base`` defined here.
Supports both SQLite (local dev) and PostgreSQL (Docker/production).
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine_kwargs: dict = {
    "echo": (settings.APP_ENV == "development"),
}

if not _is_sqlite:
    engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


async def get_db():
    """FastAPI dependency – yields an async database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
