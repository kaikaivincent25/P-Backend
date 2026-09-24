"""
Alembic environment configured for our async engine.
Strips query parameters like `sslmode` and `channel_binding` from Neon URLs
so `asyncpg` does not crash during migration connections.
"""
import asyncio
from logging.config import fileConfig
from urllib.parse import urlparse, urlunparse

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.database import Base, _to_asyncpg_url
from app.models import *  # noqa: F401,F403


def _clean_neon_url(url: str) -> str:
    """Ensure asyncpg scheme and strip all query params that cause asyncpg TypeErrors."""
    url = _to_asyncpg_url(url)
    parsed = urlparse(url)
    # Reconstruct URL without query string
    return urlunparse(parsed._replace(query=""))


config = context.config
settings = get_settings()

cleaned_url = _clean_neon_url(settings.DATABASE_URL)
config.set_main_option("sqlalchemy.url", cleaned_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    # Create engine directly with connect_args for SSL to prevent parameter mismatch
    connectable = create_async_engine(
        cleaned_url,
        poolclass=pool.NullPool,
        connect_args={"ssl": True},
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())