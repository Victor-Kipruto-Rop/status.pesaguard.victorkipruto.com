"""Async SQLAlchemy engine, shared across the app."""
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def make_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or settings.database_url
    if url.startswith("sqlite"):
        # In-memory SQLite gives each new connection its own empty database
        # unless pinned to a single shared connection via StaticPool — this
        # matters for tests, which use sqlite+aiosqlite:///:memory:.
        return create_async_engine(
            url,
            echo=settings.debug,
            future=True,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(
        url,
        echo=settings.debug,
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )


engine: AsyncEngine = make_engine()
