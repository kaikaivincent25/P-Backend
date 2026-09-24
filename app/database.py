"""
Async SQLAlchemy 2.0 engine/session setup for Neon Postgres.

Why async: the app also does async I/O for outbound email (aiosmtplib) and
sits behind slowapi rate limiting on a hot endpoint (/api/contact/). Using
an async DB driver end-to-end avoids blocking the event loop on every query.

Neon specifics:
- Neon's connection string uses the `postgresql://` scheme and requires TLS.
- We swap the scheme to `postgresql+asyncpg://` so SQLAlchemy picks asyncpg.
- Neon's pooled connection string works fine with SQLAlchemy's own pool;
  we keep pool_size modest since Render free/starter tiers and Neon's pooler
  both have connection ceilings.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


def _to_asyncpg_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):  # some providers still hand out this legacy scheme
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(
    _to_asyncpg_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,       # avoids stale-connection errors after Neon idles a connection
    connect_args={"ssl": True} if "sslmode" not in settings.DATABASE_URL else {},
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
