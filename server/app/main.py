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

import pathlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from fastapi import Request

from .db import ReadinessResult, build_engine, build_session_factory, check_readiness, check_schema
from .facade import configure as configure_facade, dispatch_get, dispatch_post, err
from .features import FEATURE_ACTIONS, gate_action
from .theme import THEME_ACTIONS
from .training import TRAINING_ACTIONS
from .research_consent import ConsentRequired, install as install_consent_gate
from .logging_config import configure_logging
from .settings import SettingsError, load_settings, session_secret_is_ephemeral

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

# The facade's GET handlers have no settings argument; give them a read-only view of the one
# Settings instance so health and ping can report which provider keys are actually configured
# instead of a hardcoded false.
configure_facade(settings)

# Registered on the Session class, so it covers every session including ones created by code
# written later. See research_consent for why this is not a per-endpoint check.
install_consent_gate()

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
    if session_secret_is_ephemeral():
        # Never a silent downgrade: sessions will not survive a restart or a second instance.
        log.warning(
            "session_secret_ephemeral",
            extra={"detail": "SESSION_SECRET is unset; a per-process secret was generated, so "
                             "research sessions will not survive a restart. Set SESSION_SECRET."},
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


def _session_token_from(request: Request, params: dict) -> str:
    """
    The session token for a GET, read from a HEADER in preference to the query string.

    A token in a URL is logged by every intermediary that logs URLs — the reverse proxy, the
    access log, the browser's history, a `Referer` on any outbound link — so it is the wrong place
    to put a credential that grants read access to project data. `Authorization: Bearer` is the
    standard carrier and is what assets/js/store.js now sends.

    The no-custom-headers rule that store.js was written under came from Apps Script: a custom
    header makes a cross-origin request non-simple and triggers a preflight the old backend could
    not answer. That constraint expired at T1, when the app moved to the same origin as /exec —
    config.js says so in its header. Same-origin requests issue no preflight whatever headers they
    carry.

    `session_token` in the query string is still accepted, for one reason: an EXISTING caller that
    cannot set headers. `/documents/{id}/content` is loaded as an iframe `src` by the document
    viewer (workspace.js:624), and a browser navigation carries no custom headers, so that route
    has always taken the token as a parameter. Rejecting the parameter here would not improve that
    route and would break any caller mid-session. It is a fallback, not the mechanism.
    """
    header = request.headers.get("authorization") or ""
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return str(request.headers.get("x-session-token") or params.get("session_token") or "")


@app.get("/exec", tags=["facade"])
def exec_get(request: Request) -> JSONResponse:
    params = dict(request.query_params)
    # The credential is resolved once, here, and put where every downstream guard already looks
    # for it. Handlers keep taking (session, params) and need no new argument.
    token = _session_token_from(request, params)
    if token:
        params["session_token"] = token
    try:
        with SessionFactory() as session:
            # T1: feature flags are enforced server-side, before dispatch. Hiding a feature in
            # the UI is not enforcement, and a per-handler check is only as reliable as whoever
            # adds the next handler.
            refused = gate_action(session, str(params.get("action") or ""), params, settings)
            if refused is not None:
                return _exec_response(refused)
            return _exec_response(dispatch_get(session, params, settings))
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

    action = str(payload.get("action") or "").lower()
    try:
        with SessionFactory() as session:
            refused = gate_action(session, action, payload, settings)
            if refused is not None:
                return _exec_response(refused)
            # The feature-flag admin actions are dispatched here rather than from facade.py,
            # which this phase must not modify: another session may be editing it concurrently.
            handler = (FEATURE_ACTIONS.get(action) or THEME_ACTIONS.get(action)
                      or TRAINING_ACTIONS.get(action))
            if handler is not None:
                return _exec_response(handler(session, payload, settings.session_secret,
                                              settings.session_ttl_seconds))
            return _exec_response(dispatch_post(session, payload, settings))
    except ConsentRequired as exc:
        # Reported in the contract's error shape, not as a 500: it is an application outcome.
        log.warning("consent_gate_blocked", extra={"action": payload.get("action"),
                                                   "detail": str(exc)})
        return _exec_response(err(str(exc)))
    except Exception as exc:  # noqa: BLE001
        log.exception("exec_post_failed", extra={"action": payload.get("action")})
        return _exec_response(err(f"Server error: {type(exc).__name__}"))


# ---------------------------------------------------------------- static SPA (T1)
#
# The frontend is served from this origin so it can call /exec same-origin, with no CORS
# request and no Apps Script redirect.
#
# WHY THIS CANNOT SHADOW THE HEALTH ENDPOINTS, which is the thing most likely to go wrong here:
#
#   1. There is no catch-all. Only three things are served — the /assets prefix, "/" and
#      "/index.html" as exact paths, and "/logo.png" as an exact path. A request to /healthz,
#      /readyz or /exec matches none of them, so it can only ever reach its own route. Mounting
#      StaticFiles at "/" would have introduced exactly that risk, and is deliberately not done.
#   2. Registration order reinforces it. Starlette matches routes in order and takes the first
#      full match; these are declared after the health and facade routes.
#
# It also serves only what the SPA actually loads. Serving the repository root would have
# published server/app/*.py, apps_script/, p0-baseline/ and .git/ to the public internet.
# The allowlist below is the whole delivery surface.

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_ASSETS_DIR = REPO_ROOT / "assets"
_INDEX_HTML = REPO_ROOT / "index.html"
_LOGO_PNG = REPO_ROOT / "logo.png"
# T6: workspace.html, admin-ops.html, questionnaires.html and decision.html were folded into
# index.html as sections and deleted. Their routes are gone with them, so those paths now 404 —
# which is the point: a participant must not be able to reach any part of the decision sequence
# by typing a URL, and a route that still served a deleted page would be a second front door.
#
# research/deepdive.html is the exception, and deliberately a narrow one. It is the only surface
# that still runs a model in the browser, because re-running one live IS what it is for. The
# application does not load sim.js/simulations.js/categories.js at all, so that behaviour cannot
# exist there; it exists here instead. Nothing links to this page and it holds no data of its
# own — every action it would call is authenticated and refused server-side for a caller without
# the role and membership. The guarantee is that no participant-facing route loads a client-side
# model, not that this URL is secret.
_DEEPDIVE_HTML = REPO_ROOT / "research" / "deepdive.html"

if _ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_ASSETS_DIR)), name="assets")


def _static_file(path: pathlib.Path, media_type: str) -> FileResponse | JSONResponse:
    if not path.is_file():
        # A JSON body rather than FastAPI's HTML 404: everything else this service returns is
        # JSON, and a missing bundle should read as a deployment fault, not a routing mystery.
        return JSONResponse(status_code=404,
                            content={"ok": False, "error": f"not deployed: {path.name}"})
    return FileResponse(path, media_type=media_type)


@app.get("/", include_in_schema=False)
def spa_root():
    return _static_file(_INDEX_HTML, "text/html")


@app.get("/index.html", include_in_schema=False)
def spa_index():
    return _static_file(_INDEX_HTML, "text/html")


@app.get("/logo.png", include_in_schema=False)
def spa_logo():
    return _static_file(_LOGO_PNG, "image/png")


@app.get("/research/deepdive.html", include_in_schema=False)
def research_deepdive():
    """The researcher-side deep dive. See the note beside _DEEPDIVE_HTML for why it is separate."""
    return _static_file(_DEEPDIVE_HTML, "text/html")


# ---------------------------------------------------------------- document content (T3)
#
# The one thing /exec cannot serve: PDF bytes. /exec is JSON in, JSON out (see exec_post's
# docstring), and base64-wrapping a multi-hundred-KB PDF into a JSON string the browser then
# has to decode is exactly the inefficiency a dedicated binary route avoids.
#
# Auth here cannot be a session COOKIE — nothing in this app sets one; the session token is a
# bearer value the frontend already holds in sessionStorage (research_identity.py's session
# convention). So it travels as a query parameter on this GET, which is the only place a
# <iframe>/<embed> or a plain browser navigation can attach it. It is authorization for a GET,
# not a credential change, so this does not need the same "never touch a database credential in
# a query string" caution that would apply to, say, a password reset link — but it does mean
# this URL should not be pasted into a support ticket or shared casually, same as any bearer URL.
#
# Membership is checked here again rather than trusted from the frontend: any active member of
# the project may read a document uploaded to it, but that document may ALSO be linked to other
# projects via the sha256 cache (B7b) — a caller must not be able to read a document by knowing
# its id if it never reached a project they belong to. The check is therefore "does a
# document_uploads row link this document to a project this caller is an active member of",
# not merely "does this document exist".


@app.get("/documents/{document_id}/content", include_in_schema=False)
def document_content(document_id: str, project_id: str, session_token: str):
    from sqlalchemy import select
    from fastapi.responses import StreamingResponse

    from .research_identity import resolve_caller
    from .research_membership import _project_by_legacy, active_membership
    from .research_models import Document, DocumentUpload

    with SessionFactory() as session:
        caller, problem = resolve_caller(session, {"session_token": session_token},
                                         settings.session_secret)
        if problem:
            return JSONResponse(status_code=403, content=problem)

        project = _project_by_legacy(session, project_id)
        if project is None:
            return JSONResponse(status_code=404,
                                content={"ok": False, "error": "Project not found"})
        if active_membership(session, project, caller.participant_id) is None:
            return JSONResponse(status_code=403,
                                content={"ok": False,
                                         "error": "not authorized: not a member of this project"})

        doc = session.get(Document, document_id)
        linked = doc is not None and session.scalar(
            select(DocumentUpload).where(DocumentUpload.project_id == project.id,
                                         DocumentUpload.document_id == document_id)
        ) is not None
        if not linked:
            # Deliberately the same 404 whether the document_id is unknown or simply never
            # reached this project — distinguishing them would confirm a document's existence
            # to a caller who only guessed its id.
            return JSONResponse(status_code=404,
                                content={"ok": False, "error": "Document not found"})

        # BYTEA has no server-side large-object streaming in this schema, so the driver round
        # trip is one materialised column value — the framework does not offer a chunked-fetch
        # path for BYTEA the way it would for a filesystem file. What StreamingResponse buys
        # here is real: the bytes are handed to Starlette as a chunked iterator rather than
        # built into one JSON/Response body first, so a multi-MB PDF is written to the socket
        # in pieces instead of fully buffered a second time inside the response layer.
        content = doc.content or b""

        def chunks(data: bytes, size: int = 256 * 1024):
            for i in range(0, len(data), size):
                yield data[i:i + size]

        return StreamingResponse(
            chunks(content),
            media_type=doc.mime_type or "application/octet-stream",
            headers={"Content-Disposition": f'inline; filename="{doc.filename}"',
                    "Content-Length": str(len(content))},
        )
