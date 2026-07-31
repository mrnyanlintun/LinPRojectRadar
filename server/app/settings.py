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
import secrets
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
    # Signs research session tokens. See load_settings for the fallback behaviour.
    session_secret: str = ""
    session_ttl_seconds: int = 8 * 3600
    # Whether an AI provider key is configured, NOT the key itself. These back the
    # anthropicKeyPresent / openaiKeyPresent flags the /exec health and ping actions report,
    # which the live backend uses to mean "this deployment has a key", nothing more.
    #
    # Presence rather than value is deliberate. Nothing on this service makes a provider call
    # yet — every AI action is still deferred — so holding the secret in a long-lived object
    # would add an exposure surface (a stray repr, a debugger frame, a future log line) that
    # buys nothing today. When an AI action lands it should read its key at the point of use.
    # This mirrors the rule the module already follows for DATABASE_URL: expose the derived,
    # credential-free fact, never the credential.
    anthropic_key_present: bool = False
    openai_key_present: bool = False

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

    # SESSION_SECRET signs research session tokens. If it is unset the service still starts, with
    # a secret generated per process: sessions then stop working across a restart or a second
    # instance. That is a visible, explainable failure (participants are asked to log in again),
    # unlike a hardcoded default, which would be a forgeable signing key in a public repository.
    # The condition is logged at startup so it is never a silent downgrade.
    session_secret = (env.get("SESSION_SECRET") or "").strip()
    if not session_secret:
        session_secret = secrets.token_urlsafe(48)

    try:
        ttl = int(env.get("SESSION_TTL_SECONDS") or 8 * 3600)
    except ValueError:
        raise SettingsError("SESSION_TTL_SECONDS must be an integer number of seconds.")

    return Settings(
        database_url=database_url,
        cors_origins=_split_origins(env.get("CORS_ORIGINS", "")),
        session_secret=session_secret,
        session_ttl_seconds=ttl,
        # Absent and empty are the same thing: a variable set to "" is not a usable key, and
        # reporting it as present would send whoever debugs it looking in the wrong place.
        anthropic_key_present=bool((env.get("ANTHROPIC_API_KEY") or "").strip()),
        openai_key_present=bool((env.get("OPENAI_API_KEY") or "").strip()),
    )


def session_secret_is_ephemeral(environ: dict[str, str] | None = None) -> bool:
    """True when SESSION_SECRET was absent and a per-process secret was generated."""
    env = os.environ if environ is None else environ
    return not (env.get("SESSION_SECRET") or "").strip()
