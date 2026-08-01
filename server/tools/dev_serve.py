#!/usr/bin/env python3
"""
Local development server.

WHY THIS EXISTS

The application refuses to start without DATABASE_URL (settings.py fails fast, deliberately —
a web service that starts without a database is worse than one that does not start). That is
correct for production and inconvenient for local work, because the preview tooling launches a
process from .claude/launch.json and has no way to set an environment variable.

So this script sets a LOCAL default and starts uvicorn. Three rules it keeps:

  1. It never invents a production URL. If DATABASE_URL is already set, that value is used
     unchanged — so this script cannot silently redirect a deliberate configuration.
  2. Its default is a file inside the repository, named dev.db, which .gitignore already
     excludes. A local database cannot be committed by accident.
  3. It migrates to head before serving, because a server whose schema is behind answers /readyz
     with 503 and every request with confusing failures.

NOT FOR DEPLOYMENT. Render runs uvicorn directly with a real DATABASE_URL; nothing here is on
that path.

Run:
    server/.venv/Scripts/python.exe server/tools/dev_serve.py [port]
"""

from __future__ import annotations

import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SERVER_DIR = REPO_ROOT / "server"

# The app package lives under server/, and alembic.ini resolves its script location relative to
# that directory too, so both the import path and the working directory have to point there.
sys.path.insert(0, str(SERVER_DIR))
os.chdir(SERVER_DIR)

if not os.environ.get("DATABASE_URL"):
    # Rule 1 above: only ever fills a gap, never overrides.
    os.environ["DATABASE_URL"] = f"sqlite:///{(SERVER_DIR / 'dev.db').as_posix()}"
if not os.environ.get("SESSION_SECRET"):
    # A fixed local secret so sessions survive a restart during development. Production sets its
    # own; load_settings() mints a random per-process one when this is absent, which would sign
    # every restart's tokens differently.
    os.environ["SESSION_SECRET"] = "local-development-only-not-a-secret"

import alembic.config  # noqa: E402
import uvicorn  # noqa: E402

# --------------------------------------------------------------------------- dev fixtures
#
# Without ANTHROPIC_API_KEY the extractor is B7b's StubExtractor, which serves recordings keyed
# by sha256 and REFUSES anything it has not been given — it will not invent an extraction. That
# refusal is correct and must stay, so local work needs recordings rather than a relaxed stub.
#
# The three documents below exist to exercise the analytical layer locally, and one of them is
# deliberately pathological: DEV_CASES["on-budget"] has earned value exactly equal to actual
# cost, so cpi is exactly 1.0. A project exactly on budget is entirely ordinary, and it is the
# input the JavaScript port was found to mishandle, so it is the case worth being able to
# reproduce on demand.
#
# NOT ON THE PRODUCTION PATH. Render runs uvicorn directly and never imports this module; a
# deployment with a real key gets AnthropicExtractor and never sees these.

import hashlib  # noqa: E402

def _doc(title: str, ev: int, ac: int, pv: int) -> bytes:
    return (f"{title}\nEarned Value: {ev}\nActual Cost: {ac}\nPlanned Value: {pv}\n"
            f"Budget at Completion: 10000000\nReport Date: 2026-06-30\n").encode("utf-8")


DEV_CASES = {
    # name          earned value  actual cost  planned value   cpi     spi
    "healthy":     (5_250_000,    5_000_000,   5_000_000),   # 1.05    1.05
    "on-budget":   (4_000_000,    4_000_000,   4_000_000),   # 1.00    1.00  <- the artefact case
    "distressed":  (4_000_000,    4_800_000,   5_000_000),   # 0.833   0.80
}

DEV_RECORDINGS: dict[str, tuple[str, dict]] = {}
for _name, (_ev, _ac, _pv) in DEV_CASES.items():
    _raw = _doc(f"MONTHLY REPORT {_name.upper()}", _ev, _ac, _pv)
    DEV_RECORDINGS[hashlib.sha256(_raw).hexdigest()] = ("monthly_report", {
        "earned_value": _ev, "actual_cost": _ac, "planned_value": _pv,
        "budget_at_completion": 10_000_000,
        "actual_percent_complete": round(_ev / 10_000_000 * 100, 2),
        "planned_percent_complete": round(_pv / 10_000_000 * 100, 2),
        "report_date": "2026-06-30",
    })
    (SERVER_DIR / "dev_fixtures").mkdir(exist_ok=True)
    (SERVER_DIR / "dev_fixtures" / f"monthly_report_{_name}.txt").write_bytes(_raw)

from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402

set_extractor_override(StubExtractor(DEV_RECORDINGS))
print(f"[dev_serve] stub extractor seeded with {len(DEV_RECORDINGS)} recordings; "
      f"fixture documents written to server/dev_fixtures/")

# --------------------------------------------------------------------------- no stale assets
#
# The browser caches /assets aggressively, so an edited JS file keeps running its old version
# while the server serves the new one. That has cost real time in three separate sessions: the
# symptom is behaviour disagreeing with the source, and the diagnosis looks like a logic bug
# until someone fetches the file and compares.
#
# DEVELOPMENT ONLY. Render runs uvicorn directly and never imports this module, so production
# caching is untouched — and production wants those headers.
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402
import app.main as _main  # noqa: E402


class _NoAssetCache(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/assets") or request.url.path.endswith(".html"):
            response.headers["Cache-Control"] = "no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response


_main.app.add_middleware(_NoAssetCache)
print("[dev_serve] /assets served no-store; edits take effect on reload")

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8010

print(f"[dev_serve] database : {os.environ['DATABASE_URL']}")
print("[dev_serve] migrating to head")
alembic.config.main(argv=["upgrade", "head"])

print(f"[dev_serve] serving http://127.0.0.1:{port}")
uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="warning")
