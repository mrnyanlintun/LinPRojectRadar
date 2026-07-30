"""
Opus Gubernatio migration beachhead.

M1 scope: a deployable FastAPI service with health endpoints and a database connection. It serves
no application traffic and implements no Apps Script action. The Apps Script backend remains the
production backend; assets/js/config.js is untouched.

Endpoint contract:

  GET /healthz  liveness. Answers 200 whenever the process is running. Makes no database call, so
                a database outage never causes the platform to restart a healthy process.
  GET /readyz   readiness. Answers 200 only after a real database round-trip succeeds, and 503
                with a structured reason otherwise.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .db import build_engine, build_session_factory, check_readiness
from .logging_config import configure_logging
from .settings import SettingsError, load_settings

SERVICE_NAME = "opus-gubernatio-server"
SERVICE_VERSION = "m1-beachhead"

configure_logging(os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger(SERVICE_NAME)

# Deliberately not wrapped in try/except. A missing DATABASE_URL must stop the boot with the
# message from settings.py rather than yield a service that answers /healthz while being unable
# to do anything useful.
try:
    settings = load_settings()
except SettingsError as exc:
    log.critical("configuration_error", extra={"reason": str(exc)})
    raise

engine = build_engine(settings)
SessionFactory = build_session_factory(engine)

app = FastAPI(
    title="Opus Gubernatio Server",
    description="Migration beachhead. Health endpoints only; serves no application traffic.",
    version=SERVICE_VERSION,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )


@app.on_event("startup")
def on_startup() -> None:
    # Backend scheme and host only. The connection string is never logged.
    log.info(
        "service_start",
        extra={
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "db_backend": settings.database_backend,
            "db_host": settings.database_host,
            "cors_origin_count": len(settings.cors_origins),
        },
    )


@app.get("/healthz", tags=["health"])
def healthz() -> dict[str, Any]:
    """Liveness. No database call by design."""
    return {"status": "ok", "service": SERVICE_NAME, "version": SERVICE_VERSION, "checks": []}


@app.get("/readyz", tags=["health"])
def readyz() -> JSONResponse:
    """Readiness. 200 only when a real database round-trip succeeds; 503 with a reason otherwise."""
    result = check_readiness(engine)

    body: dict[str, Any] = {
        "status": "ready" if result.ready else "not_ready",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "checks": [
            {
                "name": "database",
                "ok": result.ready,
                "backend": settings.database_backend,
                "host": settings.database_host,
                "detail": result.detail,
                **({"error_type": result.error_type} if result.error_type else {}),
            }
        ],
    }

    if not result.ready:
        log.warning(
            "readiness_failed",
            extra={"error_type": result.error_type, "detail": result.detail,
                   "db_backend": settings.database_backend, "db_host": settings.database_host},
        )

    return JSONResponse(status_code=200 if result.ready else 503, content=body)
