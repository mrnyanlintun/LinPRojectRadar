"""
/exec compatibility facade.

Reproduces the Apps Script action API on Postgres so the existing frontend could talk to this
service unchanged. Read paths live here; write paths live in writes.py. AI and file-ingestion
actions are still deferred.

Four contract rules, all taken from the M0 live capture rather than from source:

1. Application errors are HTTP 200 with {"ok": false, "error": "..."}. The frontend reads `ok`
   from a 200 body and never inspects the status code. Non-200 is reserved for genuine transport
   faults. `getportfoliohealth` on live v10.29 returns an unknown-action error with status 200,
   which is the evidence for this rule.
2. Action names are matched case-insensitively. The live dispatcher lowercases before comparing,
   and the frontend sends `identifyOnly` in camelCase at store.js:508. Exact matching would break
   document identification silently.
3. Key sets and types match p0-baseline/contracts/.
4. `ping` and `version` are aliases and report the version under "version"; `health` reports it
   under "apiVersion". Both conventions are preserved deliberately.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import File, Project, ProjectSnapshot

FACADE_API_VERSION = "opus-gubernatio-facade-a1b"

# Portfolio health is a singleton snapshot with no owning project. It lives in
# project_snapshots under this reserved period so it can never be mistaken for project history.
PORTFOLIO_HEALTH_PERIOD = "__portfolio_health__"

# Mirrors the live okHealth_ endpoints array. Advertising strings only; it does not gate dispatch.
HEALTH_ENDPOINTS = [
    "?action=health", "?action=list", "?action=listslim", "?action=listarchived",
    "?action=get&id=01", "?action=listcorpus&id=01", "?action=listauditresults&id=01",
    "?action=gethistory&id=01",
    "POST create", "POST save", "POST setprojectnumber", "POST archive", "POST restore",
    "POST chat", "POST analyze", "POST extractsignals", "POST overwritesignal", "POST tts",
    "POST ingestcorpus", "POST audit", "POST resetsignals", "POST saveauditresult",
    "POST savehistory", "POST portfolioanalyze",
]


def now_iso() -> str:
    """Match the live format: ISO 8601, milliseconds, trailing Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


def err(message: str) -> dict[str, Any]:
    """The only error shape. Always served with HTTP 200."""
    return {"ok": False, "error": message}


# ---------------------------------------------------------------- projections


def slim_row(doc: dict) -> dict[str, Any]:
    """
    The listslim projection.

    Every field below was derived by comparing the captured list and listslim fixtures, and this
    function reproduces all 15 live slim rows exactly.

    Two are worth naming because neither is where it looks:
      status  comes from the document root, not signals.evm.status. PRJ-08421 is "Red" at the root
              while signals.evm.status is "amber".
      docCount is the number of signals_extracted events, not a file count. PRJ-08421 reports 36
              while listcorpus returns 3 entries.
    """
    events = doc.get("events") or []
    inputs = doc.get("signalInputs") or {}
    evm = (doc.get("signals") or {}).get("evm") or {}
    sim = doc.get("simulationSignals") or {}

    return {
        "id": doc.get("id"),
        "name": doc.get("name"),
        "sector": doc.get("sector"),
        "status": doc.get("status"),
        "updatedAt": doc.get("updatedAt"),
        "cpi": evm.get("cpi"),
        "spi": evm.get("spi"),
        "docRiskScore": inputs.get("docRiskScore"),
        "actualPctComplete": inputs.get("actualPctComplete"),
        "simModuleCount": len(sim.get("signal_array") or []),
        "docCount": sum(
            1 for e in events if isinstance(e, dict) and e.get("event") == "signals_extracted"
        ),
        "slim": True,
    }


# ---------------------------------------------------------------- lookups


def _project(session: Session, legacy_id: str | None) -> Project | None:
    if not legacy_id:
        return None
    return session.scalar(select(Project).where(Project.legacy_id == legacy_id))


def _ordered(session: Session, archived: bool):
    # created_at preserves the live ordering, which the fixtures show is stable and which the
    # frontend relies on for the portfolio list.
    return session.scalars(
        select(Project).where(Project.archived == archived).order_by(Project.created_at, Project.legacy_id)
    ).all()


# ---------------------------------------------------------------- GET actions


def a_health(session: Session, params: dict) -> dict[str, Any]:
    return {
        "ok": True,
        "apiVersion": FACADE_API_VERSION,          # rule 4: health uses "apiVersion"
        "parentFolder": "postgres",                 # no Drive folder exists; see PR notes
        "parentFolderId": "",
        "openaiKeyPresent": False,                  # no AI action is implemented by the facade
        "anthropicKeyPresent": False,
        "libPresent": False,
        "libFileCount": 0,
        "timestamp": now_iso(),
        "endpoints": list(HEALTH_ENDPOINTS),
    }


def a_ping(session: Session, params: dict) -> dict[str, Any]:
    return {
        "ok": True,
        "version": FACADE_API_VERSION,              # rule 4: ping/version use "version"
        "deployedAt_note": f"Facade build {FACADE_API_VERSION}. AI and ingestion actions are not implemented.",
        "anthropicKeyPresent": False,
        "openaiKeyPresent": False,
        # Only the actions this build actually serves. AI and ingestion paths are omitted
        # deliberately: advertising them would promise writes that return an error.
        "postActionsRegistered": sorted(_implemented_post_actions()),
        "portfolioanalyzeRegistered": False,
        "timestamp": now_iso(),
    }


def a_list(session: Session, params: dict) -> dict[str, Any]:
    return {"ok": True, "projects": [p.doc for p in _ordered(session, archived=False)]}


def a_listslim(session: Session, params: dict) -> dict[str, Any]:
    return {"ok": True, "projects": [slim_row(p.doc) for p in _ordered(session, archived=False)]}


def a_listarchived(session: Session, params: dict) -> dict[str, Any]:
    return {"ok": True, "projects": [p.doc for p in _ordered(session, archived=True)]}


def a_get(session: Session, params: dict) -> dict[str, Any]:
    pid = params.get("id")
    project = _project(session, pid)
    if not project or project.archived:
        # Live wording, reproduced exactly. An archived project is Not found here: the capture
        # shows ?action=get&id=01 returning "Not found: 01" while 01 appears in listarchived.
        return err(f"Not found: {pid}")
    return {"ok": True, "project": project.doc}


def _files(session: Session, params: dict, doc_type: str):
    project = _project(session, params.get("id"))
    if not project:
        return None, err(f"Project not found: {params.get('id')}")
    rows = session.scalars(
        select(File).where(File.project_id == project.id, File.doc_type == doc_type)
        .order_by(File.ingested_at, File.name)
    ).all()
    return rows, None


def a_listcorpus(session: Session, params: dict) -> dict[str, Any]:
    project = _project(session, params.get("id"))
    if not project:
        return err(f"Project not found: {params.get('id')}")
    rows = session.scalars(
        select(File).where(File.project_id == project.id, File.doc_type != "audit_result")
        .order_by(File.ingested_at, File.name)
    ).all()
    return {
        "ok": True,
        "corpus": [
            {
                "fileId": f.drive_file_id,
                "name": f.name,
                "docType": f.doc_type,
                "mimeType": "application/pdf",
                "ingestedAt": f.ingested_at.strftime("%Y-%m-%dT%H:%M:%S.") + f"{f.ingested_at.microsecond // 1000:03d}Z",
            }
            for f in rows
        ],
    }


def a_listauditresults(session: Session, params: dict) -> dict[str, Any]:
    project = _project(session, params.get("id"))
    if not project:
        return err(f"Project not found: {params.get('id')}")
    rows = session.scalars(
        select(File).where(File.project_id == project.id, File.doc_type == "audit_result")
        .order_by(File.ingested_at, File.name)
    ).all()
    return {
        "ok": True,
        "results": [
            {
                "fileId": f.drive_file_id,
                "name": f.name,
                "createdAt": f.ingested_at.strftime("%Y-%m-%dT%H:%M:%S.") + f"{f.ingested_at.microsecond // 1000:03d}Z",
            }
            for f in rows
        ],
    }


def a_gethistory(session: Session, params: dict) -> dict[str, Any]:
    project = _project(session, params.get("id"))
    if not project:
        return err(f"Project not found: {params.get('id')}")
    rows = session.scalars(
        select(ProjectSnapshot)
        .where(ProjectSnapshot.project_id == project.id,
               ProjectSnapshot.period.is_distinct_from(PORTFOLIO_HEALTH_PERIOD))
        .order_by(ProjectSnapshot.saved_at)
    ).all()
    # Reads project_snapshots, never doc["history"]. The capture proves they are different stores.
    return {"ok": True, "history": [r.snapshot for r in rows]}


def a_getportfoliohealth(session: Session, params: dict) -> dict[str, Any]:
    """
    INTENTIONAL DEVIATION from live v10.29, which answers
    {"ok": false, "error": "Unknown GET action: getportfoliohealth"}.

    The frontend calls this at store.js:542 and deepdive.js:2330 consumes it, so on live the Health
    dialog calls an endpoint that does not exist. The facade closes that gap.

    The returned shape is the stored snapshot spread at the top level, NOT the v10.36 dispatcher's
    {"ok": true, "health": readPortfolioHealth_()}. The nested form would not work: the only
    consumer reads `resp.results` at deepdive.js:2331, and the writer at signals.js:574 posts
    results, projectCount and computedAt as top level fields. Nesting them under "health" leaves
    resp.results undefined and the Health dialog renders nothing. Reproducing a shape the consumer
    cannot read would satisfy the source and fail the user.

    An empty results object rather than null keeps deepdive.js:2332's Object.keys() check safe when
    no snapshot has been computed yet.
    """
    row = session.scalars(
        select(ProjectSnapshot).where(ProjectSnapshot.period == PORTFOLIO_HEALTH_PERIOD)
        .order_by(ProjectSnapshot.saved_at.desc())
    ).first()
    if row is None or not isinstance(row.snapshot, dict):
        return {"ok": True, "results": {}, "projectCount": 0, "computedAt": None}
    payload = {"ok": True}
    payload.update(row.snapshot)
    payload.setdefault("results", {})
    return payload


GET_ACTIONS: dict[str, Callable[[Session, dict], dict]] = {
    "health": a_health,
    "ping": a_ping,
    "version": a_ping,                 # rule 4: true alias, identical payload
    "list": a_list,
    "listslim": a_listslim,
    "listarchived": a_listarchived,
    "get": a_get,
    "listcorpus": a_listcorpus,
    "listauditresults": a_listauditresults,
    "gethistory": a_gethistory,
    "getportfoliohealth": a_getportfoliohealth,
}


def dispatch_get(session: Session, params: dict) -> dict[str, Any]:
    # Rule 2: lowercase before matching. Default matches the live dispatcher's default of 'health'.
    action = str(params.get("action") or "health").lower()
    handler = GET_ACTIONS.get(action)
    if handler is None:
        return err(f"Unknown GET action: {action}")
    return handler(session, params)


def _implemented_post_actions() -> set[str]:
    from .writes import POST_ACTIONS
    return set(POST_ACTIONS)


def dispatch_post(session: Session, payload: dict, settings=None) -> dict[str, Any]:
    # writes and research_identity import facade for err/now_iso, so these imports are local to
    # break the cycle.
    from .research_consent import ConsentRequired
    from .research_identity import IDENTITY_ACTIONS
    from .writes import DEFERRED_AI_ACTIONS, POST_ACTIONS

    # Rule 2: lowercase before matching, so the frontend's camelCase identifyOnly still resolves.
    action = str(payload.get("action") or "").lower()

    identity = IDENTITY_ACTIONS.get(action)
    if identity is not None:
        if settings is None:
            return err("research identity is not configured on this build")
        try:
            return identity(session, payload, settings.session_secret, settings.session_ttl_seconds)
        except ConsentRequired as exc:
            # The consent gate fires during flush, so it can surface from any handler that writes.
            session.rollback()
            return err(str(exc))

    handler = POST_ACTIONS.get(action)
    if handler is not None:
        return handler(session, payload)

    if action in DEFERRED_AI_ACTIONS:
        # Deferred, not unknown. Saying "unknown" about an action the backend is known to support
        # would send whoever debugs it looking for a typo.
        return err(f"Action not implemented in this build: {action}")

    return err(f"Unknown POST action: {action}")
