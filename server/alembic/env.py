"""
Alembic environment.

The database URL is read from DATABASE_URL through app.settings, never from alembic.ini, so a
connection string is never committed. Settings also normalises Render's postgres:// form to the
psycopg 3 dialect.

target_metadata points at the declarative Base. Both the facade models and the research models
are imported below so that every table is registered before autogenerate compares.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base  # noqa: E402
# Imported for their side effect: registering tables on Base.metadata so autogenerate can see
# them. Without these imports autogenerate would propose dropping every table it cannot find.
from app import models, research_models  # noqa: E402,F401
from app.settings import load_settings  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", load_settings().database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def _is_async_url(url: str) -> bool:
    """True when the URL names an asyncio DBAPI driver.

    A synchronous engine over an async driver (``sqlite+aiosqlite``, ``postgresql+asyncpg``)
    dies with ``MissingGreenlet`` the moment it opens a connection. Tool scripts that point
    DATABASE_URL at an async URL and then migrate a throwaway database hit exactly that, so the
    driver decides which engine we build rather than the caller having to know.
    """
    try:
        from sqlalchemy.engine.url import make_url

        return make_url(url).get_dialect().is_async
    except Exception:
        return "+aiosqlite" in url or "+asyncpg" in url


async def _run_migrations_online_async() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    if _is_async_url(config.get_main_option("sqlalchemy.url")):
        import asyncio

        asyncio.run(_run_migrations_online_async())
        return
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        _do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
