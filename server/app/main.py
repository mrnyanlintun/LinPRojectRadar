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

import json
import logging
import os
import platform
import sys
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi import Request

from .db import ReadinessResult, build_engine, build_session_factory, check_readiness, check_schema
from .facade import dispatch_get, dispatch_post, err
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
    """
    Liveness. No database call by design.

    Also reports the running interpreter version. A wrong interpreter has already caused one loud
    failure (psycopg-binary could not resolve) and one silent one (SQLAlchemy dropped its C
    extensions with nothing in the build log saying so). Reporting it here makes the pin verifiable
    at runtime instead of only by reading a build log.

    Deliberately limited to the version. No paths, environment variables, package list, or
    sys.version build string, which would leak compiler and build-host detail.
    """
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "python_version": platform.python_version(),
        "python_version_info": list(sys.version_info),
        "checks": [],
    }


@app.get("/readyz", tags=["health"])
def readyz() -> JSONResponse:
    """
    Readiness. 200 only when connectivity AND schema-at-head both hold; 503 with a structured
    reason otherwise.

    The schema check is not decoration. SELECT 1 succeeds against an empty database, and this
    endpoint reported ready for hours in production while every table-touching action failed,
    because the migrations had never been applied. Connectivity is a precondition for readiness,
    not readiness itself.

    Migrations are still applied by hand, deliberately: they are not in buildCommand, so a schema
    change cannot ship without someone deciding to apply it. This check does not change that. It
    stops the health endpoint from claiming everything is fine while it has not been done.
    """
    database = check_readiness(engine)

    checks: list[dict[str, Any]] = [
        {
            "name": "database",
            "ok": database.ready,
            "backend": settings.database_backend,
            "host": settings.database_host,
            "detail": database.detail,
            **({"error_type": database.error_type} if database.error_type else {}),
        }
    ]

    # Only meaningful if the database answered. Reporting a schema failure on an unreachable
    # database would name the wrong cause.
    if database.ready:
        schema = check_schema(engine)
        checks.append({
            "name": "schema",
            "ok": schema.ready,
            "detail": schema.detail,
            **({"error_type": schema.error_type} if schema.error_type else {}),
        })
    else:
        schema = ReadinessResult(False, "not evaluated: database unreachable", "NotEvaluated")
        checks.append({
            "name": "schema", "ok": False,
            "detail": schema.detail, "error_type": schema.error_type,
        })

    ready = database.ready and schema.ready

    body: dict[str, Any] = {
        "status": "ready" if ready else "not_ready",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "checks": checks,
    }

    if not ready:
        failed = [c for c in checks if not c["ok"]]
        log.warning(
            "readiness_failed",
            extra={"failed_checks": [c["name"] for c in failed],
                   "error_type": failed[0].get("error_type") if failed else None,
                   "detail": failed[0].get("detail") if failed else None,
                   "db_backend": settings.database_backend, "db_host": settings.database_host},
        )

    return JSONResponse(status_code=200 if ready else 503, content=body)


# ---------------------------------------------------------------- /exec facade


def _exec_response(payload: dict[str, Any]) -> JSONResponse:
    """
    Contract rule 1: application errors are HTTP 200 with ok:false. The frontend reads `ok` from
    the body and never inspects the status code, so returning 4xx here would break it. Non-200 is
    reserved for genuine transport faults.
    """
    return JSONResponse(status_code=200, content=payload)


@app.get("/exec", tags=["facade"])
def exec_get(request: Request) -> JSONResponse:
    params = dict(request.query_params)
    try:
        with SessionFactory() as session:
            return _exec_response(dispatch_get(session, params))
    except Exception as exc:  # noqa: BLE001
        # Even an unexpected fault is reported in the contract's error shape, because a 500 body
        # would not parse as {ok:false} and the frontend would surface nothing useful.
        log.exception("exec_get_failed", extra={"action": params.get("action")})
        return _exec_response(err(f"Server error: {type(exc).__name__}"))


@app.post("/exec", tags=["facade"])
async def exec_post(request: Request) -> JSONResponse:
    """
    The frontend posts text/plain to avoid a CORS preflight Apps Script cannot answer, so the body
    is JSON but the content type is not application/json. Parse the raw body rather than relying on
    FastAPI's JSON binding, which would reject it.
    """
    raw = await request.body()
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
        if not isinstance(payload, dict):
            raise ValueError("payload is not an object")
    except (ValueError, UnicodeDecodeError) as exc:
        return _exec_response(err(f"Bad request body: {exc}"))

    try:
        with SessionFactory() as session:
            return _exec_response(dispatch_post(session, payload))
    except Exception as exc:  # noqa: BLE001
        log.exception("exec_post_failed", extra={"action": payload.get("action")})
        return _exec_response(err(f"Server error: {type(exc).__name__}"))
