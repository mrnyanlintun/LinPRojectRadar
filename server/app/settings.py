"""
Environment-derived settings.

Fails fast and loudly when DATABASE_URL is missing. A web service that starts without a database
and only discovers it on the first request produces a confusing partial outage; refusing to boot
is the clearer failure.

No setting value is ever logged. DATABASE_URL contains credentials, so only its derived,
credential-free description is exposed for diagnostics.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit


class SettingsError(RuntimeError):
    """Raised when the environment cannot produce a usable configuration."""


def _split_origins(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: list[str] = field(default_factory=list)

    @property
    def database_backend(self) -> str:
        """Scheme only, for logs and health payloads. Never includes credentials."""
        scheme = urlsplit(self.database_url).scheme or "unknown"
        return scheme.split("+", 1)[0]

    @property
    def database_host(self) -> str:
        """
        Host and port only. urlsplit keeps userinfo out of .hostname, so this cannot leak a
        password even when the URL embeds one.
        """
        parts = urlsplit(self.database_url)
        if not parts.hostname:
            return "local"
        return f"{parts.hostname}:{parts.port}" if parts.port else parts.hostname


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    env = os.environ if environ is None else environ

    database_url = (env.get("DATABASE_URL") or "").strip()
    if not database_url:
        raise SettingsError(
            "DATABASE_URL is not set. The service cannot start without a database connection "
            "string. In Render, set it on the web service under Environment; locally, export it, "
            "for example DATABASE_URL=sqlite:///./local.db"
        )

    # Render's managed Postgres emits postgres:// URLs, which SQLAlchemy 2.x no longer resolves
    # to a driver. Normalise to the psycopg 3 dialect rather than failing at first connection.
    if database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]
    elif database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgresql://"):]

    return Settings(
        database_url=database_url,
        cors_origins=_split_origins(env.get("CORS_ORIGINS", "")),
    )
