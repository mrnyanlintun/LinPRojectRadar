"""
/exec write actions (A1b).

Response shapes come from the v10.36 reference, since no live POST fixture exists: every write was
DEFERRED_TO_MANUAL at M0 and never captured. Error wording is reproduced verbatim, because
store.js surfaces `error` straight to the user.

Four rules apply to every handler here.

  Server clocks only. Any client supplied timestamp is discarded and replaced. A client clock can
  be wrong, skewed, or forged, and updatedAt doubles as the concurrency token.

  Verified write. Each handler commits, re-reads from the database, and confirms the change landed
  before returning ok:true. A write that cannot be confirmed returns ok:false with a specific
  reason rather than reporting a success it never checked.

  Conflicts are ok:false, never 409. Contract rule 1 admits no non-200 for an application outcome.

  JSON columns are replaced, never mutated in place. SQLAlchemy does not track in-place mutation of
  a JSON/JSONB value, so `doc["x"] = y` would be dropped silently at flush. Every handler builds a
  new dict and assigns it.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .facade import PORTFOLIO_HEALTH_PERIOD, err, now_iso
from .models import File, Project, ProjectSnapshot


class StaleWrite(Exception):
    """The client's copy is older than the stored record."""


def _server_now() -> str:
    return now_iso()


def _project(session: Session, legacy_id: str | None) -> Project | None:
    if not legacy_id:
        return None
    return session.scalar(select(Project).where(Project.legacy_id == legacy_id))


# ---------------------------------------------------------------- concurrency


def _concurrency_token(payload: dict, incoming_doc: dict | None):
    """
    Pick the optimistic-concurrency token from what the client actually sends.

    The frontend never sends record_version: store.js:359 posts {action:"save", project} and
    nothing more. The token it does round-trip is project.updatedAt, which the server assigns on
    every write, so a client that has not re-read since the last write presents a stale value.

    record_version is preferred when present, so a future same-origin client can use the stronger
    token without a contract change.
    """
    if payload.get("record_version") is not None:
        return ("record_version", payload["record_version"])
    if incoming_doc and incoming_doc.get("updatedAt") is not None:
        return ("updatedAt", incoming_doc["updatedAt"])
    return None


def _check_not_stale(project: Project, token) -> None:
    if token is None:
        # Nothing to compare against. Allowed rather than rejected: rejecting would break the
        # existing frontend for any project whose document has never carried updatedAt.
        return
    kind, value = token
    if kind == "record_version":
        if int(value) != int(project.record_version):
            raise StaleWrite(
                f"Stale write for {project.legacy_id}: record_version {value} does not match "
                f"stored {project.record_version}. Re-read the project and retry."
            )
        return
    stored = (project.doc or {}).get("updatedAt")
    if stored is not None and value != stored:
        raise StaleWrite(
            f"Stale write for {project.legacy_id}: updatedAt {value} does not match stored "
            f"{stored}. Re-read the project and retry."
        )


# ---------------------------------------------------------------- doc helpers


def _touch(doc: dict, created: str | None = None) -> dict:
    """Copy with server-assigned timestamps. Never trusts the client clock."""
    fresh = dict(doc)
    fresh["updatedAt"] = _server_now()
    if created is not None:
        fresh["createdAt"] = created
    return fresh


def _append_event(doc: dict, event: str, **extra: Any) -> dict:
    fresh = dict(doc)
    events = list(fresh.get("events") or [])
    entry = {"event": event, "at": _server_now()}
    entry.update(extra)
    events.append(entry)
    fresh["events"] = events
    return fresh


_ID_OK = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.")


def _valid_id(value: str) -> bool:
    return bool(value) and all(c in _ID_OK for c in value)


# ---------------------------------------------------------------- handlers


def w_create(session: Session, payload: dict) -> dict[str, Any]:
    pid = (payload.get("id") or "").strip()
    if not pid:
        return err("Missing id")
    if not _valid_id(pid):
        return err("Project number contains invalid characters")

    existing = _project(session, pid)
    if existing is not None:
        return err(
            f"Project number exists in archive: {pid}" if existing.archived
            else f"Project number already exists: {pid}"
        )

    now = _server_now()
    doc = {
        "id": pid,
        "name": payload.get("name") or pid,
        "sector": payload.get("sector") or "",
        "signals": {},
        "events": [{"event": "project_created", "at": now}],
        "status": "",
        "createdAt": now,
        "updatedAt": now,
    }
    session.add(Project(legacy_id=pid, doc=doc, archived=False, record_version=1))
    session.commit()

    session.expire_all()
    saved = _project(session, pid)
    if saved is None or saved.doc.get("id") != pid:
        return err(f"Create could not be verified for {pid}: project not readable after commit")
    return {"ok": True, "project": saved.doc}


def w_save(session: Session, payload: dict) -> dict[str, Any]:
    incoming = payload.get("project")
    if not isinstance(incoming, dict):
        return err("Missing project")
    pid = incoming.get("id")
    if not pid:
        return err("Missing id")

    project = _project(session, pid)
    if project is None:
        return err(f"Not found: {pid}")

    try:
        _check_not_stale(project, _concurrency_token(payload, incoming))
    except StaleWrite as exc:
        return err(str(exc))

    stored_created = (project.doc or {}).get("createdAt")
    fresh = _touch(incoming, created=stored_created)

    # THE EVENT LOG MAY BE EXTENDED, NEVER SHORTENED OR SUBSTITUTED.
    #
    # This handler replaces the stored document wholesale with the client's copy, so `events` was
    # whatever the client happened to send. Measured: a save carrying no `events` key at all wiped
    # the log, and a save carrying a fabricated one-entry list replaced it — both accepted, and
    # neither needs a concurrency token, since `_check_not_stale` returns without complaint when
    # the client presents no token. That is a larger hole than the one w_resetsignals had, on the
    # write path the legacy frontend actually uses: a project whose in-memory copy came from the
    # slim projection never carried `events` at all, and saving it destroyed the log.
    #
    # The client is a legitimate APPENDER — assets/js/signals.js pushes a `simulation_run` entry
    # and then calls saveProject — so the server cannot simply own the list. It can require that
    # whatever arrives starts with what is already stored, which permits an append and refuses a
    # truncation or a rewrite of history. Anything that does not extend the stored log leaves the
    # stored log standing.
    stored_events = (project.doc or {}).get("events") or []
    incoming_events = fresh.get("events")
    extends = (isinstance(incoming_events, list)
               and len(incoming_events) >= len(stored_events)
               and incoming_events[:len(stored_events)] == stored_events)
    fresh["events"] = incoming_events if extends else stored_events

    # Geocode only when the address CHANGED, which is what v10.29 did and what the comment in
    # assets/js/ingest.js still describes. Re-geocoding an unchanged address on every save would
    # spend the rate limit answering a question already answered, and the cache would make it
    # free but pointless.
    #
    # Non-fatal by construction: apply_to_doc never raises, so a save cannot fail because a
    # geocoder was unreachable. The project stores a geocodeError instead and the interface
    # shows it.
    from .geocode import normalize as _norm
    old_address = (project.doc or {}).get("address") or ""
    new_address = str(fresh.get("address") or "").strip()
    if new_address and _norm(new_address) != _norm(old_address):
        from .geocode import apply_to_doc
        # `project.doc` is the STORED document and is what a retained coordinate must come from:
        # this handler replaces the stored doc wholesale with the client's copy, so reading the
        # previous position out of `fresh` would trust a client that may not have sent it.
        apply_to_doc(fresh, new_address, previous=project.doc or {})
    elif not new_address:
        # The address was cleared, so the coordinates it produced must go with it rather than
        # leaving the project pinned where it used to be. This is the user saying there is no
        # address, not a geocoder failing to answer, so nothing is retained.
        for stale in ("lat", "lng", "formattedAddress", "geocodeError", "geocodeStale"):
            fresh.pop(stale, None)

    expected_version = project.record_version + 1

    project.doc = fresh
    project.record_version = expected_version
    session.commit()

    session.expire_all()
    saved = _project(session, pid)
    if saved is None:
        return err(f"Save could not be verified for {pid}: project not readable after commit")
    if saved.record_version != expected_version:
        return err(
            f"Save could not be verified for {pid}: record_version is {saved.record_version}, "
            f"expected {expected_version}"
        )
    if saved.doc.get("updatedAt") != fresh["updatedAt"]:
        return err(f"Save could not be verified for {pid}: stored updatedAt does not match the write")
    return {"ok": True, "project": saved.doc}


def _set_archived(session: Session, pid: str, archived: bool, event: str):
    project = _project(session, pid)
    if project is None:
        return None, err(f"Not found: {pid}")

    project.doc = _touch(_append_event(project.doc or {}, event))
    project.archived = archived
    project.record_version = project.record_version + 1
    session.commit()

    session.expire_all()
    saved = _project(session, pid)
    if saved is None or bool(saved.archived) is not archived:
        return None, err(
            f"{event} could not be verified for {pid}: archived flag is "
            f"{None if saved is None else saved.archived}, expected {archived}"
        )
    return saved, None


def w_archive(session: Session, payload: dict) -> dict[str, Any]:
    pid = payload.get("id")
    if not pid:
        return err("Missing id")
    if _project(session, pid) is None:
        return err(f"Not found: {pid}")
    _, problem = _set_archived(session, pid, True, "project_archived")
    if problem:
        return problem
    return {"ok": True, "archived": True, "id": pid, "timestamp": _server_now()}


def w_restore(session: Session, payload: dict) -> dict[str, Any]:
    pid = payload.get("id")
    if not pid:
        return err("Missing id")
    project = _project(session, pid)
    if project is None or not project.archived:
        return err(f"Archived project not found: {pid}")
    saved, problem = _set_archived(session, pid, False, "project_restored")
    if problem:
        return problem
    return {"ok": True, "restored": True, "id": pid, "project": saved.doc, "timestamp": _server_now()}


def w_setprojectnumber(session: Session, payload: dict) -> dict[str, Any]:
    pid, new_id = payload.get("id"), payload.get("newId")
    if not pid or not new_id:
        return err("id and newId are required")
    if not _valid_id(new_id):
        return err("Project number contains invalid characters")
    if pid == new_id:
        return {"ok": True, "id": pid, "unchanged": True}

    project = _project(session, pid)
    if project is None:
        return err(f"Project not found: {pid}")
    if _project(session, new_id) is not None:
        return err(f"Project number already exists: {new_id}")

    fresh = dict(project.doc or {})
    fresh["id"] = new_id
    fresh = _touch(_append_event(fresh, "project_number_changed", **{"from": pid, "to": new_id}))

    project.legacy_id = new_id
    project.doc = fresh
    project.record_version = project.record_version + 1
    session.commit()

    session.expire_all()
    saved = _project(session, new_id)
    if saved is None or saved.doc.get("id") != new_id:
        return err(f"Rename could not be verified for {pid}: {new_id} not readable after commit")
    if _project(session, pid) is not None:
        return err(f"Rename could not be verified for {pid}: the old project number still resolves")
    return {"ok": True, "id": new_id, "project": saved.doc}


def w_resetsignals(session: Session, payload: dict) -> dict[str, Any]:
    pid = payload.get("id")
    if not pid:
        return err("id is required")
    project = _project(session, pid)
    if project is None:
        return err(f"Project not found: {pid}")

    fresh = dict(project.doc or {})
    prior_inputs = dict(fresh.get("signalInputs") or {})
    prior_signal_keys = sorted((fresh.get("signals") or {}).keys())
    prior_sim_modules = len((fresh.get("simulationSignals") or {}).get("signal_array") or [])
    fresh["signals"] = {}
    fresh["signalInputs"] = {}
    fresh["simulationSignals"] = {}

    # THE EVENT LOG IS NOT TOUCHED. This used to keep only `signals_extracted` and discard every
    # other entry — project_created, project_archived, project_restored, project_number_changed,
    # signal_overwritten and any earlier signals_reset — which made this the one write on the
    # platform that destroyed a record of something having happened rather than adding one.
    #
    # Nothing required the deletion. The two surfaces that read this log filter it themselves
    # (detail.js's Uploaded Documents table and signals.js's audit panel both select the event
    # types they render), and the slim docCount counts `signals_extracted` specifically, so
    # keeping the rest changes neither. What the deletion did change, since D1 wired `events`
    # into signalInputs, is C1.4 Audit Trail Completeness: dropping `project_created` takes it
    # from 100% to 0% and Green to Red on a project whose trail is intact — the reset was
    # reporting a worse audit trail than the project actually had.
    #
    # The reset is now recorded the way every other mutation on this module is recorded, with
    # `_append_event`. It carries what was cleared BY SHAPE — how many signalInputs fields, which
    # signal blocks, how many simulation modules — and not by value: the point of the action is to
    # remove those values, so writing them into an event that `get` returns would defeat it.
    fresh = _touch(_append_event(
        fresh, "signals_reset",
        cleared_signal_input_fields=len(prior_inputs),
        cleared_signal_input_names=sorted(prior_inputs.keys()),
        cleared_signal_blocks=prior_signal_keys,
        cleared_simulation_modules=prior_sim_modules,
        reason=str(payload.get("reason") or ""),
    ))

    project.doc = fresh
    project.record_version = project.record_version + 1
    session.commit()

    session.expire_all()
    saved = _project(session, pid)
    if saved is None or saved.doc.get("signals") != {}:
        return err(f"Reset could not be verified for {pid}: signals are not empty after commit")
    return {"ok": True, "id": pid, "reset": True}


def w_overwritesignal(session: Session, payload: dict) -> dict[str, Any]:
    pid, field = payload.get("id"), payload.get("field")
    if not pid or not field:
        return err("id and field are required")
    project = _project(session, pid)
    if project is None:
        return err(f"Project not found: {pid}")

    inputs = dict((project.doc or {}).get("signalInputs") or {})
    if not inputs:
        return err("No extracted signals to overwrite")

    old_value = inputs.get(field)
    new_value = payload.get("value")

    # THE THIRD ENTRY POINT, and the one an audit of extraction_merge alone would miss.
    # This action writes an arbitrary caller-supplied value into an arbitrary signalInputs
    # field with no validation of either, so it bypasses the extraction boundary completely.
    # A PM could set docRiskScore to 85 or -3 here and reach fusion by a route that never
    # touches a document. Guarded with the same rule, converted to the refusal shape this
    # module returns rather than raised, because /exec callers read `error`.
    if field == "docRiskScore":
        from .extraction_merge import DocRiskScoreRangeError, validate_doc_risk_score
        try:
            validate_doc_risk_score(new_value)
        except DocRiskScoreRangeError as exc:
            return err(str(exc))

    inputs[field] = new_value

    fresh = dict(project.doc or {})
    fresh["signalInputs"] = inputs
    fresh = _touch(_append_event(
        fresh, "signal_overwritten", field=field, reason=payload.get("reason") or ""
    ))

    project.doc = fresh
    project.record_version = project.record_version + 1
    session.commit()

    session.expire_all()
    saved = _project(session, pid)
    if saved is None or (saved.doc.get("signalInputs") or {}).get(field) != new_value:
        return err(f"Overwrite could not be verified for {pid}: {field} did not persist")
    return {
        "ok": True, "id": pid, "field": field,
        "from": old_value, "to": saved.doc["signalInputs"][field],
        "signalInputs": saved.doc["signalInputs"],
    }


def w_savehistory(session: Session, payload: dict) -> dict[str, Any]:
    pid = payload.get("id")
    if not pid:
        return err("id is required")
    snapshot = payload.get("snapshot")
    if snapshot is None:
        return err("snapshot is required")
    project = _project(session, pid)
    if project is None:
        return err(f"Project not found: {pid}")

    period = payload.get("period") or _server_now()[:7]
    row = ProjectSnapshot(project_id=project.id, period=period, snapshot=snapshot)
    session.add(row)
    session.commit()

    row_id = row.id
    session.expire_all()
    stored = session.get(ProjectSnapshot, row_id)
    if stored is None or stored.snapshot != snapshot:
        return err(f"History could not be verified for {pid}: snapshot not readable after commit")
    return {"ok": True, "period": period, "fileName": f"history_{period}.json"}


def w_saveauditresult(session: Session, payload: dict) -> dict[str, Any]:
    pid = payload.get("id")
    if not pid:
        return err("id is required")
    project = _project(session, pid)
    if project is None:
        return err(f"Project not found: {pid}")

    audit = payload.get("auditData") or {}
    stamp = _server_now().replace(":", "-").replace(".", "-")
    name = audit.get("name") or f"audit_{audit.get('reviewType') or 'result'}_{stamp}.json"
    audit_id = str(uuid.uuid4())

    row = File(project_id=project.id, drive_file_id=audit_id, name=name, doc_type="audit_result")
    session.add(row)
    session.commit()

    row_id = row.id
    session.expire_all()
    stored = session.get(File, row_id)
    if stored is None or stored.doc_type != "audit_result":
        return err(f"Audit result could not be verified for {pid}: row not readable after commit")
    return {"ok": True, "audit_id": audit_id}


def w_saveportfoliohealth(session: Session, payload: dict) -> dict[str, Any]:
    """
    Stores exactly the shape getportfoliohealth returns.

    a_getportfoliohealth spreads the stored snapshot at the top level beside ok, so the snapshot
    must carry results / projectCount / computedAt as top level keys. savedAt is server assigned.
    """
    if payload.get("results") is None:
        return err("health payload required")

    snapshot = {k: v for k, v in payload.items() if k != "action"}
    snapshot["savedAt"] = _server_now()

    # One current snapshot. Replacing rather than accumulating matches the live model, which keeps
    # a single portfolio_health.json at the Drive root.
    for old in session.scalars(
        select(ProjectSnapshot).where(ProjectSnapshot.period == PORTFOLIO_HEALTH_PERIOD)
    ).all():
        session.delete(old)

    session.add(ProjectSnapshot(project_id=None, period=PORTFOLIO_HEALTH_PERIOD, snapshot=snapshot))
    session.commit()

    session.expire_all()
    stored = session.scalars(
        select(ProjectSnapshot).where(ProjectSnapshot.period == PORTFOLIO_HEALTH_PERIOD)
    ).all()
    if len(stored) != 1 or stored[0].snapshot.get("savedAt") != snapshot["savedAt"]:
        return err("Portfolio health could not be verified: snapshot not readable after commit")
    return {"ok": True, "savedAt": snapshot["savedAt"]}


POST_ACTIONS: dict[str, Callable[[Session, dict], dict]] = {
    "create": w_create,
    "save": w_save,
    "archive": w_archive,
    "restore": w_restore,
    "setprojectnumber": w_setprojectnumber,
    "resetsignals": w_resetsignals,
    "overwritesignal": w_overwritesignal,
    "savehistory": w_savehistory,
    "saveauditresult": w_saveauditresult,
    "saveportfoliohealth": w_saveportfoliohealth,
}

# AI and file-ingestion paths, deferred until the write paths are proven.
DEFERRED_AI_ACTIONS = {
    "chat", "analyze", "extractsignals", "identifyonly", "audit", "portfolioanalyze",
    "ingestcorpus", "tts",
}
