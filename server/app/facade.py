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


# ---------------------------------------------------------------- runtime settings
#
# The GET handlers take (session, params) and have no settings argument, so main injects the
# resolved Settings here once at startup.
#
# Injected rather than built here on demand: when SESSION_SECRET is unset, load_settings() mints
# a RANDOM per-process secret, so a second Settings instance would disagree with main's about how
# to verify a session token. One instance, one secret.
_runtime_settings: Any = None


def configure(settings: Any) -> None:
    """Called once by main after settings load. Idempotent; safe to call again in tests."""
    global _runtime_settings
    _runtime_settings = settings


def _setting(attr: str, default: Any = False) -> Any:
    """Read an injected setting, defaulting when the facade is used without configure()."""
    return getattr(_runtime_settings, attr, default) if _runtime_settings is not None else default


def now_iso() -> str:
    """Match the live format: ISO 8601, milliseconds, trailing Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


def err(message: str) -> dict[str, Any]:
    """The only error shape. Always served with HTTP 200."""
    return {"ok": False, "error": message}


# ---------------------------------------------------------------- projections


def live_statuses(session: Session, projects: list) -> dict[str, dict[str, Any]]:
    """
    The live stored computed status for each of these projects, keyed by internal project id.

    WHY THIS EXISTS. `project.doc` is the legacy document and carries a `status` that nothing
    writes any more: computation stores its answer in `computed_results` and never writes back.
    Before this, `a_list`, `a_listslim` and `a_get` returned the doc alone, so the project list,
    the status legend and the portfolio all read an empty status and rendered "Awaiting
    analysis" for a project whose stored row said Green, while the Signals tab — which fetches
    `projectresults` — showed the truth. Same project, same session, two answers. Verified on a
    clean single-compute project on 2026-08-03, so it was never an artifact of superseding.

    ONE QUERY for the whole page, not one per project. The read paths below are collection
    endpoints and an N+1 here would be paid on every portfolio load.

    ONLY THE LIVE ROW. `superseded_by IS NULL` is the same predicate `_live_result` uses in
    documents.py, so a recompute moves every surface at once and a superseded row can never be
    what a list renders.

    STATUS ONLY, DELIBERATELY. `module_results` is NOT included and must not be: it carries the
    action-bearing fields `_result_view` redacts unless `recommendation_visible` allows them,
    and a project list is not a place that predicate has been evaluated. `category_statuses`
    carries a status, a conflict number and a group per category, none of which is an action,
    and the radar reads it through the same accessor.
    """
    if not projects:
        return {}
    from .research_models import ComputedResult

    rows = session.scalars(
        select(ComputedResult).where(
            ComputedResult.project_id.in_([p.id for p in projects]),
            ComputedResult.superseded_by.is_(None),
        ).order_by(ComputedResult.period)
    ).all()
    # RUN 75, THE OWNER'S RULING: A ROW EXISTING IS NOT THE SAME AS A RESULT EXISTING.
    #
    # This is the THIRD place that reads "the project's latest live period", after
    # `_computed_periods` and the detail page, and it is the one the list, the portfolio and
    # `storedResult` resolve through. A live row holding NO MODULE RESULTS won the "latest
    # period" contest here exactly as it did there: the owner's project carried a complete
    # period 1 and an evidence-free period 2, and every list read the period 2 row -- no status,
    # so `with_stored_status` left the legacy document's empty one and the surface said
    # "awaiting analysis" for a project that had been computed to Amber over 8 modules.
    #
    # Worse than the label: `storedResult` STATES A PERIOD, and detail.js's graft refuses a
    # served row whose period differs from it (Run 69, section 7.3). So the empty period 2
    # projection made the page reject the real period 1 row it had just fetched.
    #
    # The predicate is the same one `_computed_periods` uses and for the same reason: a row with
    # no module results has nothing any surface can render. Filtering here, not in the
    # projection below -- what is RETURNED is unchanged and still status only.
    rows = [r for r in rows if (r.module_results or [])]
    # Ordered by period so that, for a project with several live periods, the LATEST period is
    # the one left in the map. That matches what a list is understood to be showing: where the
    # project stands now, not where it stood first.
    # RUN 79. THE STATUS ON THIS PROJECTION IS THE SPECIFICATION READINGS' STATUS.
    #
    # This projection is what `a_list`, `a_listslim` and `a_get` attach as `storedResult`, so
    # it is the portfolio list row, the status legend and the project header line. Before this
    # run it published `r.project_status` and `r.category_statuses` -- the retired Python
    # module layer's answer out of `computed_results` -- while the category panel two clicks
    # away published the specification layer's. Same project, same session, two answers, which
    # is the exact defect the docstring above records this function being written to remove.
    #
    # `r` STILL DECIDES WHICH PERIOD, for the reason the Run 75 note above gives: a period the
    # project has no evidence row for is not a period any surface can render. What `r` no
    # longer decides is WHAT THE STATUS IS.
    #
    # NO FALLBACK. A project whose categories have never been called gets an empty
    # `category_statuses`, and the Python module layer's older figure is NOT substituted for it.
    # That is the order's rule at section 2: the surface renders the stored reading or it
    # renders nothing.
    #
    # RUN 100 CORRECTS WHAT THIS NOTE SAID NEXT. It claimed such a project gets `project_status`
    # None, so `with_stored_status` leaves the legacy document's empty status and "the list says
    # the project is awaiting analysis". THAT HAS BEEN FALSE SINCE RUN 89. `spec_projection.
    # project_status` applies the required-core gate first: A1, A2, A3, A6 must each carry a
    # posture, and when any of them does not a WORD is published -- not None. So
    # `with_stored_status` finds a truthy status, sets it on the row, and the list prints it.
    # None is now published only when the required core is fully assessed and the project rule's
    # band is itself absent.
    #
    # RUN 106, GOAL TWO. THAT WORD IS NOW "Awaiting analysis", and it is one of the owner's six.
    # It was "Indeterminate", a seventh status he had not ruled on; he has now ruled it out. The
    # required core is A1, A2, A3, A4 and A6 (five since Run 95, not the four this note listed),
    # and the list row carries `project_status_reason` beside the word so the portfolio can say
    # WHICH category is unassessed rather than printing a label nobody can act on.
    #
    # The stale note mattered: it described the portfolio as falling through to an empty status,
    # which is why a defect in what the list actually publishes stayed invisible to inspection
    # of this file. Measured on the real list route this run, not asserted.
    from . import spec_projection

    # RUN 99. The computed row's own figures ride along so the Complete promotion is decided on
    # the portfolio list by the SAME function the detail page and the compute route use. The
    # readings still decide the risk band; these decide only whether the work is delivered.
    projections = spec_projection.projections(
        session, [(r.project_id, r.period) for r in rows],
        {r.project_id: (r.signal_inputs or {}) for r in rows})
    out: dict[str, dict[str, Any]] = {}
    # RUN 102, GOAL ONE. THE SAME PER-CATEGORY FALLBACK THE DETAIL CARD NOW USES, applied here
    # so the header line and the portfolio row cannot say one thing while the card says another
    # -- which is the exact defect the docstring above records this function existing to remove.
    # The "NO FALLBACK" paragraph above is superseded by the owner's Run 102 ruling, section 2.
    # `merge_python_row` fills only the categories the specification layer has NO reading for,
    # and labels every posture it serves.
    for r in rows:
        proj = spec_projection.merge_python_row(
            projections[r.project_id], r.module_results, r.abstained,
            r.category_statuses, r.signal_inputs)
        out[r.project_id] = {
            "result_id": r.result_id,
            "period": r.period,
            "project_status": proj["project_status"],
            "category_statuses": proj["category_statuses"],
            "posture_layers": proj["posture_layers"],
            "python_fallback_categories": proj["python_fallback_categories"],
        }
    return out


def with_stored_status(doc: dict, stored: dict | None) -> dict[str, Any]:
    """
    The project document as a reader should see it: the stored computed status wins.

    RUN 105 MEASURED WHAT `stored` ACTUALLY IS, because the name invites the wrong reading.
    It is NOT the `computed_results` row. It is `live_statuses`'s output above, whose
    `project_status` comes from `spec_projection.merge_python_row` -- the merged mapping through
    the required-core gate and `worst_band`. So the portfolio list, the slim list and `a_get`
    have always served the SPECIFICATION path's status, the same one the detail page serves, and
    the Run 104 divergence never reached them. Measured on the real GET routes, not asserted:
    `tools/drive_run105.py` part 1 presses `list` and `listslim` and compares them with
    `projectresults`.

    RETURNS A COPY AND NEVER MUTATES `doc`. `project.doc` is a live ORM attribute on a JSON
    column, so assigning into it here would be picked up by the next flush and written back to
    the database — quietly creating the second source of truth this fix exists to remove. The
    copy is shallow on purpose: nothing below the top level is touched.

    `storedResult` is the field name taxonomy.js's `rowFor()` already looks for, so a caller
    that reads a status through `getProjectFusion` needs no change to find it.
    """
    if not stored:
        return doc
    merged = dict(doc)
    if stored.get("project_status"):
        merged["status"] = stored["project_status"]
    merged["storedResult"] = stored
    return merged


def slim_row(doc: dict, stored: dict | None = None) -> dict[str, Any]:
    """
    The listslim projection.

    `stored` is the live computed result for this project, or None when it has never been
    computed. When present its `project_status` is the row's status, because that is the only
    thing that has computed one since results moved to `computed_results`; when absent the
    legacy document's own status is used unchanged, which is what keeps a genuinely uncomputed
    project reading "Awaiting analysis".

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
        "status": (stored or {}).get("project_status") or doc.get("status"),
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
    #
    # Training projects (`is_training`) are excluded here, not layered on as a separate filter
    # downstream, because every portfolio surface (project list, status legend counts, map/radar/
    # globe placement, Portfolio Health's client-side aggregate, and its own "3+ projects" pool
    # threshold) is fed from this one query via window.LIN_PROJECTS. Filtering at the source closes
    # all of them at once instead of requiring each consumer to remember to filter. This is
    # deliberately independent of the research-export isolation filter in research_export.py,
    # which stays untouched — this is the portfolio-surface filter the training-gating report
    # flagged as "not yet decided" and left out of scope.
    return session.scalars(
        select(Project)
        .where(Project.archived == archived, Project.is_training.is_(False))
        .order_by(Project.created_at, Project.legacy_id)
    ).all()


# ---------------------------------------------------------------- GET actions


def _ai_provider_diagnostics() -> dict[str, Any]:
    """Never raises: a health endpoint that 500s on a bad AI setting hides the real state."""
    try:
        from .ai_provider import provider_diagnostics
        return provider_diagnostics()
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def _recognition_diagnostics() -> dict[str, Any]:
    """Never raises, for the same reason `_ai_provider_diagnostics` does not."""
    try:
        from .recognition import recognition_diagnostics
        return recognition_diagnostics()
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def a_health(session: Session, params: dict) -> dict[str, Any]:
    return {
        "ok": True,
        "apiVersion": FACADE_API_VERSION,          # rule 4: health uses "apiVersion"
        "parentFolder": "postgres",                 # no Drive folder exists; see PR notes
        "parentFolderId": "",
        # Whether a provider key is configured on THIS service, which is what the live backend
        # reported. It is not a claim that the AI actions work: they are still deferred, and
        # `endpoints` below advertises only what is served.
        "openaiKeyPresent": bool(_setting("openai_key_present")),
        "anthropicKeyPresent": bool(_setting("anthropic_key_present")),
        # Run 93. WHICH provider and model each of the three call sites is configured for, and
        # whether that provider's key is present. PRESENCE ONLY -- no key value is ever
        # reported here, and the two flags above are kept because the live backend reported
        # them and callers read them.
        "aiProviders": _ai_provider_diagnostics(),
        # Run 111. WHICH provider and model the RECOGNITION call site is configured for, whether
        # its key is present, and which modules have a recipe. Presence only, no key value. This
        # is the surface the owner checks BEFORE uploading: a wrong model identifier should be
        # visible here rather than discovered from a failed upload.
        "recognition": _recognition_diagnostics(),
        # Still literally false: there is no Drive knowledge library on this service.
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
        # Key configured on this service, not "AI is available". deployedAt_note above and
        # postActionsRegistered below are what say which actions actually run.
        "anthropicKeyPresent": bool(_setting("anthropic_key_present")),
        "openaiKeyPresent": bool(_setting("openai_key_present")),
        # Only the actions this build actually serves. AI and ingestion paths are omitted
        # deliberately: advertising them would promise writes that return an error.
        "postActionsRegistered": sorted(_implemented_post_actions()),
        "portfolioanalyzeRegistered": False,
        "timestamp": now_iso(),
    }


def _visible(session: Session, params: dict, rows: list) -> list:
    """
    Drop the projects this caller is not a member of.

    Collections are filtered rather than refused: a portfolio call that fails because ONE of its
    rows belongs to someone else would be unusable for anybody who is a member of some projects
    and not others, which is every real user. `readable_project_ids` returns None only when no
    caller was resolved, which dispatch_get makes impossible — it is the direct-call case, kept so
    a handler exercised on its own does not silently filter everything away.
    """
    from .research_membership import readable_project_ids
    allowed = readable_project_ids(session, params)
    if allowed is None:
        return rows
    return [p for p in rows if p.legacy_id in allowed]


def a_list(session: Session, params: dict) -> dict[str, Any]:
    rows = _visible(session, params, _ordered(session, archived=False))
    statuses = live_statuses(session, rows)
    return {"ok": True,
            "projects": [with_stored_status(p.doc, statuses.get(p.id)) for p in rows]}


def a_listslim(session: Session, params: dict) -> dict[str, Any]:
    rows = _visible(session, params, _ordered(session, archived=False))
    statuses = live_statuses(session, rows)
    return {"ok": True,
            "projects": [slim_row(p.doc, statuses.get(p.id)) for p in rows]}


def a_listarchived(session: Session, params: dict) -> dict[str, Any]:
    rows = _visible(session, params, _ordered(session, archived=True))
    return {"ok": True, "projects": [p.doc for p in rows]}


def a_get(session: Session, params: dict) -> dict[str, Any]:
    pid = params.get("id")
    project = _project(session, pid)
    if not project or project.archived:
        # Live wording, reproduced exactly. An archived project is Not found here: the capture
        # shows ?action=get&id=01 returning "Not found: 01" while 01 appears in listarchived.
        return err(f"Not found: {pid}")
    statuses = live_statuses(session, [project])
    return {"ok": True, "project": with_stored_status(project.doc, statuses.get(project.id))}


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
    # The latest by the snapshot's OWN `savedAt` (millisecond resolution, stamped by
    # `_server_now()`), not by the `saved_at` DB column: sqlite's `func.now()` default is
    # second-resolution, so two saves in the same second would tie on the column and make
    # "latest" ambiguous now that saves accumulate instead of replacing. `snapshot["savedAt"]`
    # is a fixed-width ISO string, so max() over it is the same ordering a timestamp compare
    # would give.
    rows = session.scalars(
        select(ProjectSnapshot).where(ProjectSnapshot.period == PORTFOLIO_HEALTH_PERIOD)
    ).all()
    candidates = [r for r in rows if isinstance(r.snapshot, dict) and r.snapshot.get("savedAt")]
    row = max(candidates, key=lambda r: r.snapshot["savedAt"]) if candidates else None
    if row is None:
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


# GET actions that are PUBLIC, each named here on purpose.
#
# The write side rotted because a permissive default let every new action inherit permission
# without anyone deciding it should. This list is the opposite: a read is authenticated unless it
# appears here, so an action added to GET_ACTIONS is closed by default and opening it is a visible
# edit to this line rather than an omission somewhere else.
#
# All three return build and capability information and NO project data — verified by probing
# them against a populated database: version strings, which API keys are present as booleans, the
# advertised endpoint list, a timestamp. They stay public because a deployment has to be able to
# say it is alive before anyone signs in, and because `health` is the readiness signal an operator
# and a monitor both reach for. `/healthz` and `/readyz` are separate routes and are unaffected.
PUBLIC_GET_ACTIONS: frozenset[str] = frozenset({"health", "ping", "version"})


def dispatch_get(session: Session, params: dict, settings=None) -> dict[str, Any]:
    # Rule 2: lowercase before matching. Default matches the live dispatcher's default of 'health'.
    action = str(params.get("action") or "health").lower()
    handler = GET_ACTIONS.get(action)
    if handler is None:
        return err(f"Unknown GET action: {action}")

    # EVERY READ THAT CAN RETURN PROJECT DATA IS AUTHENTICATED, on the same terms as the write
    # guard. Measured before this existed: an anonymous GET returned any project's document, its
    # event log, its legacy signalInputs, its stored period snapshots and the portfolio-health
    # snapshot. `list` and `listslim` returned every project on the deployment to anyone.
    if action not in PUBLIC_GET_ACTIONS:
        from .research_membership import guard_project_read
        refused = guard_project_read(session, params, settings, action)
        if refused is not None:
            return refused
    return handler(session, params)


def _implemented_post_actions() -> set[str]:
    from .writes import POST_ACTIONS
    return set(POST_ACTIONS)


def dispatch_post(session: Session, payload: dict, settings=None) -> dict[str, Any]:
    # writes and research_identity import facade for err/now_iso, so these imports are local to
    # break the cycle.
    from .documents import DOCUMENT_ACTIONS
    from .files import FILE_ACTIONS
    from .workspace import WORKSPACE_ACTIONS
    from .questionnaires import QUESTIONNAIRE_ACTIONS
    from .research_assignment import ASSIGNMENT_ACTIONS
    from .research_consent import ConsentRequired
    from .research_decision import DECISION_ACTIONS
    from .research_expert import EXPERT_ACTIONS
    from .research_export import EXPORT_ACTIONS
    from .research_membership import (
        MEMBERSHIP_ACTIONS, PROJECT_WRITE_ACTIONS, guard_project_write,
    )
    from .research_transitions import TRANSITION_ACTIONS
    from .research_identity import IDENTITY_ACTIONS
    from .writes import DEFERRED_AI_ACTIONS, POST_ACTIONS

    # Rule 2: lowercase before matching, so the frontend's camelCase identifyOnly still resolves.
    action = str(payload.get("action") or "").lower()

    # EVERY facade write is authenticated, and the guard is applied over the whole POST surface
    # rather than over a hand-maintained subset. PROJECT_WRITE_ACTIONS listed eleven actions and
    # POST_ACTIONS implements ten, but the two sets are not the same: `create` and
    # `saveportfoliohealth` were in POST_ACTIONS and NOT in PROJECT_WRITE_ACTIONS, so they reached
    # no guard at all. Taking the union means a write added to either set inherits authentication
    # instead of waiting for someone to remember the other list.
    if action in PROJECT_WRITE_ACTIONS or action in POST_ACTIONS:
        refused = guard_project_write(session, payload, settings)
        if refused is not None:
            return refused

    identity = (IDENTITY_ACTIONS.get(action) or ASSIGNMENT_ACTIONS.get(action)
                or DECISION_ACTIONS.get(action) or TRANSITION_ACTIONS.get(action)
                or EXPORT_ACTIONS.get(action) or MEMBERSHIP_ACTIONS.get(action)
                or DOCUMENT_ACTIONS.get(action) or WORKSPACE_ACTIONS.get(action)
                or QUESTIONNAIRE_ACTIONS.get(action) or EXPERT_ACTIONS.get(action)
                or FILE_ACTIONS.get(action))
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
