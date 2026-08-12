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
    project = Project(legacy_id=pid, doc=doc, archived=False, record_version=1)
    session.add(project)

    # A PROJECT MUST NEVER EXIST WITHOUT A PM, and this action could produce one.
    #
    # `a_projectcreate` has always written the membership row in the same transaction as the
    # project. This one never did, so every project made through the legacy action came into the
    # world unmembered. That used to be invisible, because an unmembered project was readable and
    # writable by anyone; now that the guards authorise against membership unconditionally, such a
    # project would be reachable by NOBODY, including whoever just created it. Measured before
    # this change: created successfully, then refused on read, on write, and absent from its
    # creator's own list.
    #
    # The caller id comes from guard_project_write, which resolved it a moment ago and is the only
    # way this handler runs at all. Same transaction as the project row: one commit, both rows or
    # neither.
    caller_id = str(payload.get("_caller_participant_id") or "").strip()
    if caller_id:
        from .research_membership import ROLE_PM
        from .research_models import ProjectMember
        session.flush()                      # project.id is needed for the foreign key
        session.add(ProjectMember(project_id=project.id, user_key=caller_id,
                                   project_role=ROLE_PM, added_by=caller_id))
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

    # D2, THE FOURTH ENTRY POINT — the live action nobody had listed. This handler replaces
    # the stored document wholesale, and the client's copy carries a `signalInputs` blob, so
    # a malformed or out-of-range numeric could enter the stored record through an ordinary
    # save without touching a document or the overwritesignal action. Only fields whose value
    # CHANGED are validated: refusing a save because an already-stored value fails the
    # contract would brick every edit of a project carrying it, and the stored value is not
    # this save's doing. The refusal names the field and changes nothing.
    from .extraction_merge import (
        DocRiskScoreRangeError, MalformedNumericError, NumericRangeError,
        validate_signal_value,
    )
    stored_inputs = (project.doc or {}).get("signalInputs") or {}
    incoming_inputs = fresh.get("signalInputs")
    if isinstance(incoming_inputs, dict):
        for _field, _value in incoming_inputs.items():
            if _value == stored_inputs.get(_field):
                continue
            try:
                validate_signal_value(str(_field), _value)
            except (DocRiskScoreRangeError, MalformedNumericError,
                    NumericRangeError) as exc:
                return err(f"Save refused: {exc}")

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
    # RUN 16, WORKSTREAM A7. CLEARING THE SOURCE EVIDENCE MUST INVALIDATE WHAT WAS DERIVED FROM
    # IT, AND MUST DO SO HERE RATHER THAN IN THE BROWSER.
    #
    # Until this run, the reset emptied `signals`, `signalInputs` and `simulationSignals` on the
    # project document and left `computed_results` alone. The stored row is where every surface
    # actually reads from -- the ledger, the portfolio list's status, the category rollup and the
    # Signal Flow diagram all resolve through it -- so a project whose evidence had just been
    # cleared went on serving a full set of module results, category statuses and a project
    # status, through the API, in the same session, AND after a reload. That is not a
    # presentation fault: the server was answering with derived values whose inputs no longer
    # existed. Reproduced in a real browser BEFORE the change; see
    # code_audit/run16_final_flow_browser_facts.csv, state C-cleared-server.
    #
    # THE ROW IS NOT DELETED AND NOT EDITED. `computed_results` is append-only, and a submitted
    # decision that references a row must still resolve years from now. Marking it superseded is
    # the ONE update the database permits on a referenced row (migration 0009), and it is the
    # same mechanism a recompute uses. `superseded_by` carries a fresh identifier that no row
    # bears, because nothing REPLACED this result: the evidence behind it was withdrawn. The row
    # itself stays readable by `result_id` forever, which is what preserves the audit lineage,
    # and `_live_result`, `live_statuses` and the export all filter on `superseded_by IS NULL`,
    # so one write moves every surface at once.
    #
    # EVERY live period is invalidated, not just the latest: the reset clears the project's
    # evidence entirely, so no period's derived result survives it. The rows are invalidated
    # BEFORE the event is appended so the event can record how many there were, by shape, on the
    # same footing as the rest of that record.
    from .research_models import ComputedResult, new_ulid
    live_rows = session.scalars(
        select(ComputedResult).where(
            ComputedResult.project_id == project.id,
            ComputedResult.superseded_by.is_(None),
        )
    ).all()
    invalidated = [{"result_id": r.result_id, "period": r.period} for r in live_rows]
    for _row in live_rows:
        _row.superseded_by = new_ulid()

    fresh = _touch(_append_event(
        fresh, "signals_reset",
        invalidated_derived_results=len(invalidated),
        invalidated_periods=sorted({r["period"] for r in invalidated}),
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
    # RUN 16. The verified-write rule applied to the invalidation as well as to the document.
    # A reset that reported success while a derived result was still live is exactly the failure
    # this run found, so the absence of a live row is CONFIRMED here rather than assumed.
    still_live = session.scalars(
        select(ComputedResult).where(
            ComputedResult.project_id == project.id,
            ComputedResult.superseded_by.is_(None),
        )
    ).all()
    if still_live:
        return err(
            f"Reset could not be verified for {pid}: {len(still_live)} derived result(s) are "
            f"still live after the reset"
        )
    return {"ok": True, "id": pid, "reset": True, "invalidated_results": invalidated}


def w_overwritesignal(session: Session, payload: dict) -> dict[str, Any]:
    pid, field = payload.get("id"), payload.get("field")
    if not pid or not field:
        return err("id and field are required")

    # THE FIELD NAME ITSELF, validated against the one declared vocabulary. Before this, any
    # string was accepted: a caller could write a key no computation reads and nothing would
    # ever clean up, surviving every recompute because nothing downstream looks at it. The
    # known set is `field_registry.ALL_SI_FIELDS` — every field the merge can emit, plus the
    # three the computation layer still reads even though nothing emits them any more
    # (rfiNumber, rfiResponseTimeDays, docDate), plus cpi/spi. Read from the registry rather
    # than duplicated here, so the two can never drift.
    from .field_registry import ALL_SI_FIELDS
    if field not in ALL_SI_FIELDS:
        return err(f"Unknown signal field: {field!r}. This platform has no field by that "
                   f"name; nothing was changed.")

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
    # A PM could set docRiskScore to 85 or -3 here — or, before D2, set earned value to "TBD"
    # — and reach a stored record by a route that never touches a document. Guarded with the
    # same rules as the extraction boundary (malformed refuses, out-of-range refuses,
    # docRiskScore keeps its 0..1 authority), converted to the refusal shape this module
    # returns rather than raised, because /exec callers read `error`.
    from .extraction_merge import (
        DocRiskScoreRangeError, MalformedNumericError, NumericRangeError,
        validate_signal_value,
    )
    try:
        validate_signal_value(str(field), new_value)
    except (DocRiskScoreRangeError, MalformedNumericError, NumericRangeError) as exc:
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

    APPENDS. This was the one `session.delete` in the application: every save deleted every prior
    portfolio-health snapshot before inserting the new one, reproducing the live model's single
    `portfolio_health.json` file at the Drive root. Nothing reads more than the latest row —
    `a_getportfoliohealth` already orders by `saved_at DESC` and takes `.first()`, which is a
    SELECTION, not a consequence of there being only one row to select from — so nothing depends
    on the store holding exactly one snapshot. The read behaviour here is UNCHANGED: a caller who
    wants the latest still gets exactly the latest. What changes is that the snapshots before it
    are retained rather than destroyed, the way every other record in this module is (`savehistory`
    already accumulates two rows for two saves of the same period; this now matches it).
    """
    if payload.get("results") is None:
        return err("health payload required")

    snapshot = {k: v for k, v in payload.items() if k != "action"}
    snapshot["savedAt"] = _server_now()

    session.add(ProjectSnapshot(project_id=None, period=PORTFOLIO_HEALTH_PERIOD, snapshot=snapshot))
    session.commit()

    session.expire_all()
    # Verified by the snapshot's own savedAt, not the DB column — see a_getportfoliohealth for
    # why the column alone cannot be trusted to order two saves in the same second.
    matches = [
        r for r in session.scalars(
            select(ProjectSnapshot).where(ProjectSnapshot.period == PORTFOLIO_HEALTH_PERIOD)
        ).all()
        if isinstance(r.snapshot, dict) and r.snapshot.get("savedAt") == snapshot["savedAt"]
    ]
    if not matches:
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
#
# `extractsignals` LEFT THIS SET on 2026-08-04. It is dispatched by DOCUMENT_ACTIONS, which the
# facade consults before this set, so the entry would now be unreachable as well as wrong.
#
# WHAT IS STILL HERE IS NOT ALL THE SAME KIND OF THING. Checked one by one against the code
# rather than assumed, because `chat` and `extractsignals` were both found stranded — an endpoint
# that exists, has its key, and is simply never dispatched:
#
#   analyze, portfolioanalyze, audit, chat, tts
#       No handler exists anywhere in server/app. These are Apps Script actions that were never
#       ported, so the refusal is accurate: there is nothing to dispatch to. `chat` and
#       `portfolioanalyze` and `audit` additionally have FEATURE FLAGS in features.py
#       (`chat`, `health_dialog`, `auditor`), which is what makes them look implemented from the
#       frontend; a flag gates a feature, it does not supply one.
#   identifyonly
#       No handler, but UNLIKE the others the capability it names DOES exist and is reachable:
#       `AnthropicExtractor.classify_with_confidence` is called on every upload, and the type and
#       confidence come back on the projectupload/extractsignals response. Wiring the standalone
#       action would add a second model call per document for an answer the upload already
#       returns. Left deferred deliberately, not overlooked.
#   ingestcorpus
#       No handler. The corpus surface that DOES exist is `projectcorpus` in files.py, which is
#       dispatched and gated on the existing `auditor` flag. This name is the retired one.
#
# So `extractsignals` was the only genuinely stranded action of the eight. See
# REPORT_2026-08-04_real-extraction.md for the evidence behind each line above.
DEFERRED_AI_ACTIONS = {
    "chat", "analyze", "identifyonly", "audit", "portfolioanalyze",
    "ingestcorpus", "tts",
}
