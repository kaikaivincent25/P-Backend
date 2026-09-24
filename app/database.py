"""
Async SQLAlchemy 2.0 engine/session setup for Neon Postgres.
Strips query string parameters like `sslmode` and `channel_binding` that `asyncpg` rejects.
"""
from collections.abc import AsyncGenerator
from urllib.parse import urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


def _prepare_asyncpg_url(url: str) -> str:
    """Convert scheme to postgresql+asyncpg:// and strip query string params."""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    # Strip ?sslmode=... & channel_binding=... so asyncpg doesn't throw a TypeError
    return urlunparse(parsed._replace(query=""))


cleaned_db_url = _prepare_asyncpg_url(settings.DATABASE_URL)

engine = create_async_engine(
    cleaned_db_url,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    connect_args={"ssl": True},  # Enforces SSL cleanly for Neon without query params
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one session per request, always closed."""
    async with AsyncSessionLocal() as session:
        yield session