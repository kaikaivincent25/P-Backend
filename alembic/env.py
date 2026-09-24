"""
Alembic environment configured for our async engine.

We don't hardcode the DB URL here — it's pulled from app.config.Settings
(which reads DATABASE_URL from the environment), so `alembic upgrade head`
works identically on a laptop, in CI, and in Render's build process against Neon.
"""
import asyncio
from logging.config import fileConfig
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import get_settings
from app.database import Base, _to_asyncpg_url
# Import every model module so Base.metadata is fully populated before autogenerate runs.
from app.models import *  # noqa: F401,F403


def _fix_neon_asyncpg_url(url: str) -> str:
    """
    Convert scheme to postgresql+asyncpg:// and swap `sslmode` parameter for `ssl`
    so asyncpg doesn't throw a TypeError.
    """
    url = _to_asyncpg_url(url)
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Convert ?sslmode=... to ?ssl=require for asyncpg compatibility
    if "sslmode" in query_params:
        query_params.pop("sslmode")
        query_params["ssl"] = ["require"]

    # Reconstruct the cleaned connection URL
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


config = context.config
settings = get_settings()

# Set the sanitized database URL for Alembic
cleaned_url = _fix_neon_asyncpg_url(settings.DATABASE_URL)
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
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())