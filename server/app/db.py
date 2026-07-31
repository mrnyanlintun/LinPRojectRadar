"""
Database engine and readiness probe.

No application tables are defined at M1. Base exists so Alembic has a metadata target to
autogenerate against once the research schema arrives at B1.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .settings import Settings


class Base(DeclarativeBase):
    """Declarative base. Intentionally has no subclasses at M1."""


def build_engine(settings: Settings) -> Engine:
    kwargs: dict = {
        "pool_pre_ping": True,  # discard connections a proxy or Postgres has already closed
        "future": True,
    }

    # SQLite is used for local verification only. It needs no pool sizing, and the default
    # single-thread check would reject connections reused across the ASGI worker's threads.
    if settings.database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(pool_size=5, max_overflow=5, pool_recycle=300)

    return create_engine(settings.database_url, **kwargs)


def build_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@dataclass(frozen=True)
class ReadinessResult:
    ready: bool
    detail: str
    error_type: str | None = None


def check_readiness(engine: Engine) -> ReadinessResult:
    """
    Issue a real round-trip. `SELECT 1` is deliberate: it proves the connection is open and the
    server answers, which pool_pre_ping alone does not demonstrate to the caller.

    Any exception is caught and reported. The exception text is returned so the reason is visible,
    and the JSON formatter redacts URL userinfo as a backstop should a driver embed the DSN in its
    message.
    """
    try:
        with engine.connect() as connection:
            value = connection.execute(text("SELECT 1")).scalar_one()
    except Exception as exc:  # noqa: BLE001 - readiness must report every failure, not just known ones
        return ReadinessResult(
            ready=False,
            detail=str(exc).strip().splitlines()[0][:300] if str(exc).strip() else repr(exc),
            error_type=type(exc).__name__,
        )

    if value != 1:
        return ReadinessResult(
            ready=False,
            detail=f"database round-trip returned {value!r}, expected 1",
            error_type="UnexpectedResult",
        )

    return ReadinessResult(ready=True, detail="database round-trip succeeded")
