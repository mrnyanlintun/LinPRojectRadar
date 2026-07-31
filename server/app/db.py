"""
Database engine and readiness probe.

Readiness checks two things, not one: that the database answers, and that its schema is at the
revision this code expects. Connectivity alone is not readiness. A SELECT 1 succeeds against a
completely empty database, which is exactly what happened in production: /readyz reported ready
for hours while every table-touching action failed with ProgrammingError, because the migrations
had never been applied. A health check that cannot distinguish "reachable" from "usable" is worse
than none, because it is trusted.
"""

from __future__ import annotations

import pathlib
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


# The migration directory, resolved relative to this file rather than the working directory, so the
# check behaves the same under uvicorn, alembic and a test runner.
ALEMBIC_DIR = pathlib.Path(__file__).resolve().parent.parent / "alembic"


def expected_head() -> tuple[str | None, str | None]:
    """
    Read the head revision from the migration scripts on disk.

    Derived, never hardcoded. A literal revision string in application code is a second source of
    truth that drifts silently the moment someone adds a migration and forgets to update it, and
    the failure mode is a health check that reports ready against the wrong schema.

    Returns (head, error). Exactly one is non-None.
    """
    try:
        from alembic.script import ScriptDirectory

        script = ScriptDirectory(str(ALEMBIC_DIR))
        heads = script.get_heads()
    except Exception as exc:  # noqa: BLE001 - an unreadable migration tree must be visible
        return None, f"could not read migration scripts at {ALEMBIC_DIR}: {type(exc).__name__}: {exc}"

    if not heads:
        return None, f"no migration revisions found at {ALEMBIC_DIR}"
    if len(heads) > 1:
        # Multiple heads mean an unmerged branch. Picking one would be arbitrary.
        return None, f"migration tree has {len(heads)} heads ({', '.join(sorted(heads))}); merge them"
    return heads[0], None


def check_schema(engine: Engine) -> ReadinessResult:
    """
    Confirm the database schema is at the revision this code expects.

    Distinguishes three failures that need different responses:
      SchemaMissing    no alembic_version table: migrations have never run here
      SchemaOutOfDate  alembic_version present but not at head: run alembic upgrade head
      SchemaUnknown    the migration scripts could not be read, or the version table is unreadable
    """
    head, problem = expected_head()
    if problem:
        return ReadinessResult(False, problem, "SchemaUnknown")

    try:
        with engine.connect() as connection:
            if not connection.dialect.has_table(connection, "alembic_version"):
                return ReadinessResult(
                    False,
                    f"no alembic_version table; migrations have never been applied to this "
                    f"database, expected {head}",
                    "SchemaMissing",
                )
            rows = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
    except Exception as exc:  # noqa: BLE001
        return ReadinessResult(
            False, f"could not read alembic_version: {str(exc).strip().splitlines()[0][:200]}",
            "SchemaUnknown",
        )

    if not rows:
        return ReadinessResult(
            False, f"alembic_version is empty, expected {head}", "SchemaMissing"
        )
    if len(rows) > 1:
        return ReadinessResult(
            False,
            f"alembic_version holds {len(rows)} revisions ({', '.join(sorted(rows))}), expected {head}",
            "SchemaOutOfDate",
        )
    current = rows[0]
    if current != head:
        return ReadinessResult(
            False, f"alembic_version is {current}, expected {head}", "SchemaOutOfDate"
        )

    return ReadinessResult(True, f"schema at head {head}")


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
