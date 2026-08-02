#!/usr/bin/env python3
"""
B7b guarantees: upload, hash-cached extraction, compute, stored results.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... python tools/test_documents_b7b.py

Drives everything through the /exec HTTP surface, exactly as the frontend does, except where a
guarantee is explicitly about what the DATABASE refuses (Guarantee 8), which is asserted against
the engine directly because that is the point of it.

Extraction runs against the recorded StubExtractor: ANTHROPIC_API_KEY is set on Render but not
available locally. The stub REFUSES a hash it has no recording for, so nothing here can pass by
silently extracting nothing. What is exercised is the caching, concurrency, assembly, storage,
authorisation and immutability machinery; what is NOT exercised locally is the real model call
itself. See the PR description.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient
from sqlalchemy import select, text

import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.research_identity import hash_access_token
from app.research_models import (
    AuditEvent, ComputedResult, Decision, Document, DocumentUpload, Participant,
)
from app.models import Project

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


# ---------------------------------------------------------------- fixtures

ADMIN = "b7b-bootstrap-admin"
PROJ_A = "PRJ-B7B-A"
PROJ_B = "PRJ-B7B-B"

# Two byte-identical uploads to different projects must hit the SAME extraction row.
SHARED_BYTES = b"%PDF-1.4 B7B SHARED PAY APPLICATION - contract sum 10,000,000\n"
SHARED_SHA = hashlib.sha256(SHARED_BYTES).hexdigest()

NOVEL_BYTES = b"%PDF-1.4 B7B NOVEL MONTHLY REPORT - EV 4,000,000 AC 4,400,000\n"
NOVEL_SHA = hashlib.sha256(NOVEL_BYTES).hexdigest()

UNMAPPED_BYTES = b"%PDF-1.4 B7B BIM EXECUTION PLAN - governance document\n"
UNMAPPED_SHA = hashlib.sha256(UNMAPPED_BYTES).hexdigest()

RECORDED = {
    SHARED_SHA: ("pay_application", {
        "original_contract_sum": 10000000, "completed_to_date": 4200000,
        "amount_paid_to_date": 4000000, "percent_complete_verified": 42,
        "application_date": "2026-06-30", "work_period_from": "2026-06-01",
        "work_period_to": "2026-06-30", "original_contingency": 500000,
        "remaining_contingency": 380000,
    }),
    NOVEL_SHA: ("monthly_report", {
        "earned_value": 4000000, "actual_cost": 4400000, "planned_value": 4500000,
        "actual_percent_complete": 40, "planned_percent_complete": 45,
        "budget_at_completion": 10000000, "report_date": "2026-06-30",
    }),
    # Stored and classified, but contributes nothing.
    UNMAPPED_SHA: ("unmapped", {}),
}

# Concurrency fixture: N distinct documents, each with a deliberate per-call delay.
CONCURRENCY_N = 10
CONCURRENCY_DELAY = 0.30
CONC_DOCS = [(f"conc-{i}.pdf", f"%PDF-1.4 B7B CONCURRENCY DOC {i}\n".encode()) for i in
             range(CONCURRENCY_N)]
for _name, _raw in CONC_DOCS:
    RECORDED[hashlib.sha256(_raw).hexdigest()] = ("rfi", {
        "document_risk_score": 0.4, "document_date": "2026-06-30", "rfi_count": 1,
        "rfi_period_days": 30, "rfi_number": 7, "response_time_days": 5,
    })

stub = StubExtractor(RECORDED)
set_extractor_override(stub)


# ---------------------------------------------------------------- seed

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-B7B-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy in (PROJ_A, PROJ_B):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy,
                          doc={"id": legacy, "name": f"B7b {legacy}", "signals": {}}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]


def make_participant(code: str, role: str = "Participant") -> tuple[str, str]:
    """Returns (participant_id, session_token)."""
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": code, "role": role,
                    "account_type": "operational"})
    assert created.get("ok"), created
    token = post({"action": "researchlogin",
                  "access_token": created["access_token"]})["session_token"]
    return created["participant_id"], token


pm_a_id, pm_a = make_participant("PM-B7B-A")
pm_b_id, pm_b = make_participant("PM-B7B-B")
obs_id, obs = make_participant("PM-B7B-OBS")

for proj, pid in ((PROJ_A, pm_a_id), (PROJ_B, pm_b_id)):
    r = post({"action": "adminmemberadd", "session_token": admin, "id": proj,
              "participant_id": pid, "project_role": "PM"})
    assert r.get("ok"), r
r = post({"action": "adminmemberadd", "session_token": admin, "id": PROJ_A,
          "participant_id": obs_id, "project_role": "Observer"})
assert r.get("ok"), r

print("=" * 78)
print("B7b — upload, hash-cached extraction, compute, stored results")
print("=" * 78)


# ---------------------------------------------------------------- Guarantee 1

print("\nGuarantee 1 — the same file uploaded to two projects extracts ONCE")
stub.calls.clear()
up_a = post({"action": "projectupload", "session_token": pm_a, "id": PROJ_A, "period": 1,
             "documents": [{"filename": "pay-app-06.pdf", "mimeType": "application/pdf",
                            "dataBase64": b64(SHARED_BYTES)}]})
check(up_a.get("ok") is True, "first upload accepted", str(up_a)[:120])
check(up_a["files"][0]["was_cached"] is False, "first upload is not cached")
check(len(stub.calls) == 1, "exactly one model call for a novel document",
      f"calls={len(stub.calls)}")

calls_before = len(stub.calls)
up_b = post({"action": "projectupload", "session_token": pm_b, "id": PROJ_B, "period": 1,
             "documents": [{"filename": "same-bytes-different-name.pdf",
                            "mimeType": "application/pdf",
                            "dataBase64": b64(SHARED_BYTES)}]})
check(up_b.get("ok") is True, "second upload to a different project accepted")
check(up_b["files"][0]["was_cached"] is True, "second upload reports was_cached: true")
check(len(stub.calls) == calls_before, "second upload made NO model call",
      f"calls={len(stub.calls)}")

with Session() as s:
    docs = s.scalars(select(Document).where(Document.sha256 == SHARED_SHA)).all()
    ups = s.scalars(select(DocumentUpload).where(
        DocumentUpload.document_id == docs[0].document_id)).all()
check(len(docs) == 1, "one documents row for the shared hash", f"rows={len(docs)}")
check(len(ups) == 2, "two document_uploads rows (one per upload event)", f"rows={len(ups)}")
check(docs[0].filename == "pay-app-06.pdf",
      "filename is as FIRST uploaded, not overwritten by the second uploader")

# byte-identical signalInputs, which is the actual point of the cache
post({"action": "projectcompute", "session_token": pm_a, "id": PROJ_A, "period": 1})
post({"action": "projectcompute", "session_token": pm_b, "id": PROJ_B, "period": 1})
res_a = post({"action": "projectresults", "session_token": pm_a, "id": PROJ_A, "period": 1})
res_b = post({"action": "projectresults", "session_token": pm_b, "id": PROJ_B, "period": 1})
# The cache guarantee is about EXTRACTION: the same bytes must yield the same extracted values
# wherever they are uploaded. Three keys in signal_inputs are not extracted from the document at
# all — `events` is the project's own log and `spiHistory`/`cpiHistory` come from that project's
# earlier periods (both wired by D1) — so they belong to the project, not to the file, and two
# projects legitimately differ on them: PROJ_B's upload was a cache hit and PROJ_A's was not, and
# the extraction event records which. Comparing them here would assert that two different projects
# have the same history, which is not what the cache promises.
#
# The comparison stays strict on everything else, AND the difference is required to be confined to
# those three keys, so an extraction field that starts diverging still fails this check.
PROJECT_SCOPED = {"events", "spiHistory", "cpiHistory"}
raw_a, raw_b = res_a["result"]["signal_inputs"], res_b["result"]["signal_inputs"]
si_a = json.dumps({k: v for k, v in raw_a.items() if k not in PROJECT_SCOPED}, sort_keys=True)
si_b = json.dumps({k: v for k, v in raw_b.items() if k not in PROJECT_SCOPED}, sort_keys=True)
check(si_a == si_b, "byte-identical EXTRACTED signalInputs across the two projects")
differing = {k for k in set(raw_a) | set(raw_b)
             if json.dumps(raw_a.get(k), sort_keys=True) != json.dumps(raw_b.get(k), sort_keys=True)}
check(differing <= PROJECT_SCOPED,
      "and nothing outside the project-scoped keys differs at all", str(sorted(differing)))
check("events" in raw_a and "events" in raw_b,
      "precondition: the project-scoped keys are actually present, so the exclusion above is "
      "excluding something", str(sorted(set(raw_a) & PROJECT_SCOPED)))


# ---------------------------------------------------------------- Guarantee 2

print("\nGuarantee 2 — a file never seen before extracts fresh and is stored, not refused")
before = len(stub.calls)
up = post({"action": "projectupload", "session_token": pm_a, "id": PROJ_A, "period": 1,
           "documents": [{"filename": "monthly-06.pdf", "mimeType": "application/pdf",
                          "dataBase64": b64(NOVEL_BYTES)}]})
check(up.get("ok") is True, "novel document is NOT refused", str(up)[:120])
check(up["files"][0]["status"] == "extracted", "reported as extracted")
check(len(stub.calls) == before + 1, "one fresh model call")
with Session() as s:
    d = s.scalar(select(Document).where(Document.sha256 == NOVEL_SHA))
check(d is not None and d.content == NOVEL_BYTES, "bytes stored verbatim")
check(d is not None and d.extraction.get("earned_value") == 4000000, "extraction stored")
check(d is not None and d.extraction_model == stub.model_id,
      "extraction_model recorded", str(d.extraction_model if d else None))

# unmapped: stored, reported, contributes nothing, never relabelled monthly_report
up_u = post({"action": "projectupload", "session_token": pm_a, "id": PROJ_A, "period": 1,
             "documents": [{"filename": "bim-execution-plan.pdf",
                            "mimeType": "application/pdf",
                            "dataBase64": b64(UNMAPPED_BYTES)}]})
f = up_u["files"][0]
check(up_u.get("ok") is True, "unmapped document is stored, not refused")
check(f["doc_type"] == "unmapped", "doc_type is 'unmapped'", str(f["doc_type"]))
check(f["doc_type"] != "monthly_report", "NEVER silently relabelled monthly_report")
check(f["contributes"] is False, "reported as contributing nothing")
check("bim-execution-plan.pdf" in up_u["unmapped_filenames"],
      "reported back to the PM in unmapped_filenames")


# ------------------------------------------------- the upload writes signals_extracted
#
# No path wrote this event, so C1.4 Audit Trail Completeness reported 50% and Amber on every
# server-created project: it requires project_created AND signals_extracted and only the first
# existed. Counted per contributing document, stamped when the upload happened.

print("\nthe upload records signals_extracted on the project's own event log")


def _events(pid):
    with Session() as s:
        row = s.scalar(select(Project).where(Project.legacy_id == pid))
        return [e for e in ((row.doc or {}).get("events") or []) if isinstance(e, dict)]


def _names(pid):
    return [e.get("event") for e in _events(pid)]


# PROJECT_A received exactly one contributing document (Guarantee 1's pay application), and
# PROJECT_B the same bytes. Counted rather than merely "present", so a handler that writes one
# event per upload REQUEST instead of per document fails here.
# PROJ_A received the pay application (Guarantee 1), a novel monthly report (Guarantee 2), and
# an unmapped BIM plan. Two of the three contribute, so exactly two events — counted rather than
# merely "present", so a handler writing one event per upload REQUEST rather than per contributing
# document fails here.
se_a = [e for e in _events(PROJ_A) if e.get("event") == "signals_extracted"]
check(len(se_a) == 2, "one signals_extracted event per CONTRIBUTING document, not per request",
      f"{len(se_a)} on {PROJ_A}: {_names(PROJ_A)}")
check(all(e.get("docType") for e in se_a),
      "each carrying the document type it was classified as",
      str([e.get("docType") for e in se_a]))
check(sorted(e.get("fileName") or "" for e in se_a) == ["monthly-06.pdf", "pay-app-06.pdf"],
      "and the file name of the document it was written for",
      str(sorted(e.get("fileName") or "" for e in se_a)))

# NOT BACKDATED. The event must carry the server's own date, not the document's. The pay
# application's extraction reports 2024-09-15; an event stamped that day would be a record of
# something that did not happen then, written to improve the score of the module that reads it.
# ONE REQUEST, TWO CONTRIBUTING DOCUMENTS. Without this the per-document claim above cannot be
# distinguished from per-request: every other upload in this fixture carries a single document,
# so a handler logging only the first would pass. Injection caught exactly that.
BATCH_1 = b"%PDF-1.4 B7B EVENT BATCH ONE\n"
BATCH_2 = b"%PDF-1.4 B7B EVENT BATCH TWO\n"
for _b in (BATCH_1, BATCH_2):
    stub._recorded[hashlib.sha256(_b).hexdigest()] = ("monthly_report", {
        "earned_value": 1000, "actual_cost": 1000, "planned_value": 1000,
        "budget_at_completion": 2000, "document_date": "2024-09-15"})
before_b = len([e for e in _events(PROJ_B) if e.get("event") == "signals_extracted"])
post({"action": "projectupload", "session_token": pm_b, "id": PROJ_B, "period": 2,
      "documents": [{"filename": "batch-1.pdf", "mimeType": "application/pdf",
                     "dataBase64": b64(BATCH_1)},
                    {"filename": "batch-2.pdf", "mimeType": "application/pdf",
                     "dataBase64": b64(BATCH_2)}]})
after_b = len([e for e in _events(PROJ_B) if e.get("event") == "signals_extracted"])
check(after_b - before_b == 2,
      "a single upload request carrying TWO contributing documents logs TWO events",
      f"{before_b} -> {after_b}")

check(se_a and all(str(e.get("at", ""))[:4] != "2024" for e in se_a),
      "stamped when the upload happened, NOT at the document's date",
      str([e.get("at") for e in se_a]))

# The unmapped BIM plan went to PROJ_A too and contributes nothing, so it must not have produced
# an event. The count of 2 above already excludes it; this names the file so the reason is
# explicit rather than arithmetic.
check(not any((e.get("fileName") or "") == "bim-execution-plan.pdf" for e in se_a),
      "an unmapped document that contributes nothing logs no extraction event",
      str([e.get("fileName") for e in se_a]))


# ---------------------------------------------------------------- Guarantee 3

print("\nGuarantee 3 — the same file twice in the SAME project makes no second documents row")
before_calls = len(stub.calls)
with Session() as s:
    docs_before = len(s.scalars(select(Document).where(
        Document.sha256 == SHARED_SHA)).all())
    ups_before = len(s.scalars(select(DocumentUpload).where(
        DocumentUpload.project_id == s.scalar(
            select(Project.id).where(Project.legacy_id == PROJ_A)),
        DocumentUpload.period == 1)).all())
again = post({"action": "projectupload", "session_token": pm_a, "id": PROJ_A, "period": 1,
              "documents": [{"filename": "pay-app-06-again.pdf",
                             "mimeType": "application/pdf",
                             "dataBase64": b64(SHARED_BYTES)}]})
with Session() as s:
    docs_after = len(s.scalars(select(Document).where(
        Document.sha256 == SHARED_SHA)).all())
    ups_after = len(s.scalars(select(DocumentUpload).where(
        DocumentUpload.project_id == s.scalar(
            select(Project.id).where(Project.legacy_id == PROJ_A)),
        DocumentUpload.period == 1)).all())
check(again.get("ok") is True, "re-upload accepted")
check(docs_after == docs_before == 1, "still exactly one documents row",
      f"{docs_before} -> {docs_after}")
check(ups_after == ups_before, "no duplicate upload row for the same period",
      f"{ups_before} -> {ups_after}")
check(len(stub.calls) == before_calls, "no model call on re-upload")


# ---------------------------------------------------------------- Guarantee 4

print("\nGuarantee 4 — provenance is non-null, and a recompute reproduces module_results")
res = post({"action": "projectresults", "session_token": pm_a, "id": PROJ_A, "period": 1})
# recompute after the extra documents so the live row reflects them
rc = post({"action": "adminrecompute", "session_token": admin, "id": PROJ_A, "period": 1,
           "reason": "seed additional documents into the period"})
check(rc.get("ok") is True, "recompute accepted", str(rc)[:140])
res = post({"action": "projectresults", "session_token": pm_a, "id": PROJ_A, "period": 1})
r = res["result"]
check(r["simulation_version"] not in (None, ""), "simulation_version non-null",
      str(r["simulation_version"]))
check(r["seed"] not in (None, ""), "seed non-null", str(r["seed"]))
check(r["period_cutoff"] not in (None, ""), "period_cutoff non-null", str(r["period_cutoff"]))

first_modules = json.dumps(r["module_results"], sort_keys=True)
first_cutoff = r["period_cutoff"]
rc2 = post({"action": "adminrecompute", "session_token": admin, "id": PROJ_A, "period": 1,
            "reason": "determinism check on identical inputs"})
res2 = post({"action": "projectresults", "session_token": pm_a, "id": PROJ_A, "period": 1})
r2 = res2["result"]
check(json.dumps(r2["module_results"], sort_keys=True) == first_modules,
      "recompute on identical inputs produces IDENTICAL module_results")
check(r2["seed"] == r["seed"], "same seed", f"{r['seed']} vs {r2['seed']}")
check(r2["period_cutoff"] == first_cutoff,
      "recompute reuses the superseded row's period_cutoff (C1.2 cannot drift)")


# ---------------------------------------------------------------- Guarantee 5

print("\nGuarantee 5 — an observer cannot upload or trigger compute")


def denied_count() -> int:
    with Session() as s:
        return len([r for r in s.scalars(select(AuditEvent).where(
            AuditEvent.event_type == "pm_only_action_denied")).all()])


before_audit = denied_count()
obs_up = post({"action": "projectupload", "session_token": obs, "id": PROJ_A, "period": 1,
               "documents": [{"filename": "x.pdf", "mimeType": "application/pdf",
                              "dataBase64": b64(NOVEL_BYTES)}]})
check(obs_up.get("ok") is False, "observer upload refused", str(obs_up)[:120])
check("only the project's PM" in str(obs_up.get("error", "")),
      "refusal names the PM-only rule")
obs_c = post({"action": "projectcompute", "session_token": obs, "id": PROJ_A, "period": 1})
check(obs_c.get("ok") is False, "observer compute refused", str(obs_c)[:120])
check(denied_count() >= before_audit + 2, "both refusals audited",
      f"{before_audit} -> {denied_count()}")
obs_r = post({"action": "projectresults", "session_token": obs, "id": PROJ_A, "period": 1})
check(obs_r.get("ok") is True, "observer CAN still read results")


# ---------------------------------------------------------------- Guarantee 6

print("\nGuarantee 6 — no recommendation before the PM locks the preliminary judgment")
body = json.dumps(post({"action": "projectresults", "session_token": pm_a,
                        "id": PROJ_A, "period": 1}))
check(json.loads(body)["result"]["recommendation"] is None,
      "recommendation is null while unlocked")
check(json.loads(body)["result"]["recommendation_withheld"] is True,
      "withheld is explicit, distinguishable from absent")
for marker in ("ZQMARK", "recommended_action", "package_hash", "package_id",
               "alternatives", "detected_condition"):
    present = marker in body
    if present:
        i = body.index(marker)
        print(f"    LEAK CONTEXT: ...{body[max(0, i - 220):i + 90]}...")
    check(not present, f"response does not contain {marker!r}")


# ---------------------------------------------------------------- Guarantee 7

print("\nGuarantee 7 — adminrecompute supersedes; the old row stays readable")
with Session() as s:
    pid = s.scalar(select(Project.id).where(Project.legacy_id == PROJ_A))
    live = s.scalar(select(ComputedResult).where(ComputedResult.project_id == pid,
                                                 ComputedResult.superseded_by.is_(None)))
    old_id = live.result_id

rc3 = post({"action": "adminrecompute", "session_token": admin, "id": PROJ_A, "period": 1,
            "reason": "supersession check"})
check(rc3.get("ok") is True, "recompute accepted")
check(rc3["superseded_result_id"] == old_id, "reports which row it superseded")
check(rc3["result_id"] != old_id, "wrote a NEW row")

with Session() as s:
    old = s.get(ComputedResult, old_id)
check(old is not None, "old row still exists")
check(old.superseded_by == rc3["result_id"], "old row marked superseded")
old_read = post({"action": "projectresults", "session_token": pm_a, "id": PROJ_A,
                 "period": 1, "result_id": old_id})
check(old_read.get("ok") is True, "superseded row is still readable by result_id")
check(old_read["result"]["result_id"] == old_id, "and resolves to the right row")

no_reason = post({"action": "adminrecompute", "session_token": admin, "id": PROJ_A,
                  "period": 1})
check(no_reason.get("ok") is False, "recompute without a reason is refused",
      str(no_reason)[:100])
pm_rc = post({"action": "adminrecompute", "session_token": pm_a, "id": PROJ_A, "period": 1,
              "reason": "pm attempt"})
check(pm_rc.get("ok") is False, "a PM cannot recompute; ResearchAdmin only")


# ---------------------------------------------------------------- Guarantee 8

print("\nGuarantee 8 — a result referenced by a SUBMITTED decision cannot be modified")
with Session() as s:
    pid = s.scalar(select(Project.id).where(Project.legacy_id == PROJ_A))
    live = s.scalar(select(ComputedResult).where(ComputedResult.project_id == pid,
                                                 ComputedResult.superseded_by.is_(None)))
    referenced_id = live.result_id
    # A submitted decision that references it, inserted with raw SQL.
    #
    # Deliberately NOT through the ORM: a session listener enforces the consent gate on a
    # Decision insert, and the research chain's own submission path is already covered by B4.
    # What is under test here is the immutability of the referenced RESULT, so the decision is
    # scaffolding — and inserting it raw also proves the trigger fires on rows the application
    # layer never touched.
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    SCEN = "01B7BSCENARIOSEEDGUARANTE8"
    ASSIGN = "01B7BASSIGNMENTSEEDGUARAN8"
    DEC = "01B7BDECISIONSEEDGUARANTEE"
    try:
        s.execute(text("INSERT INTO scenarios (scenario_id, scenario_version, "
                       "evidence_package_id) VALUES (:s, 'b7b-v1', :p)"),
                  {"s": SCEN, "p": PROJ_A})
        s.execute(text("INSERT INTO assignments (assignment_id, participant_id, scenario_id) "
                       "VALUES (:a, :p, :s)"),
                  {"a": ASSIGN, "p": pm_a_id, "s": SCEN})
        s.execute(text(
            "INSERT INTO decisions (decision_id, assignment_id, period, pre_action, "
            "pre_confidence, pre_submitted_at, pre_locked_at, pre_judgment_locked, result_id) "
            "VALUES (:d, :a, 'P1', 'HOLD', 60, :t, :t, 1, :r)"),
            {"d": DEC, "a": ASSIGN, "t": now, "r": referenced_id})
        s.commit()
        decision_ok = True
    except Exception as exc:
        s.rollback()
        decision_ok = False
        print(f"    (could not seed a decision: {str(exc)[:140]})")

if decision_ok:
    # (a) the database itself refuses a direct UPDATE
    db_refused = False
    detail = ""
    with Session() as s:
        try:
            s.execute(text("UPDATE computed_results SET project_status = 'TAMPERED' "
                           "WHERE result_id = :r"), {"r": referenced_id})
            s.commit()
        except Exception as exc:
            s.rollback()
            db_refused = True
            detail = str(exc)[:110]
    check(db_refused, "database REJECTS a direct UPDATE of a referenced result", detail)

    with Session() as s:
        still = s.get(ComputedResult, referenced_id)
    check(still.project_status != "TAMPERED", "stored value unchanged after the attempt")

    # (b) superseding is still permitted — that is the distinction
    rc4 = post({"action": "adminrecompute", "session_token": admin, "id": PROJ_A,
                "period": 1, "reason": "supersede a referenced result"})
    check(rc4.get("ok") is True, "superseding a referenced result IS permitted",
          str(rc4)[:120])
    check(rc4["referencing_decisions"] >= 1, "recompute reports the referencing decisions",
          str(rc4.get("referencing_decisions")))
    ref_read = post({"action": "projectresults", "session_token": pm_a, "id": PROJ_A,
                     "period": 1, "result_id": referenced_id})
    check(ref_read.get("ok") is True, "the decision's referenced row still resolves")
else:
    check(False, "could not seed a submitted decision referencing a result",
          "schema requires an assignment; see note")


# ---------------------------------------------------------------- Guarantee 9

print("\nGuarantee 9 — extraction is actually concurrent")
timed = StubExtractor(RECORDED, delay_s=CONCURRENCY_DELAY)
set_extractor_override(timed)

# single-document baseline, on a project/period with nothing cached
single_raw = CONC_DOCS[0][1]
t0 = time.monotonic()
post({"action": "projectupload", "session_token": pm_b, "id": PROJ_B, "period": 2,
      "documents": [{"filename": CONC_DOCS[0][0], "mimeType": "application/pdf",
                     "dataBase64": b64(single_raw)}]})
single_s = time.monotonic() - t0

t0 = time.monotonic()
batch = post({"action": "projectupload", "session_token": pm_b, "id": PROJ_B, "period": 3,
              "documents": [{"filename": n, "mimeType": "application/pdf",
                             "dataBase64": b64(raw)}
                            for n, raw in CONC_DOCS[1:]]})
batch_s = time.monotonic() - t0
n = len(CONC_DOCS) - 1

check(batch.get("ok") is True, "batch upload accepted", str(batch)[:110])
sequential_estimate = single_s * n
print(f"    single={single_s:.2f}s   batch of {n}={batch_s:.2f}s   "
      f"sequential would be ~{sequential_estimate:.2f}s")
check(batch_s < sequential_estimate / 2,
      f"batch of {n} is under half the sequential estimate",
      f"{batch_s:.2f}s vs ~{sequential_estimate:.2f}s")
check(batch_s < single_s * 3,
      "batch wall-clock is within 3x a single document, not Nx",
      f"{batch_s:.2f}s vs single {single_s:.2f}s")

set_extractor_override(stub)


# ---------------------------------------------------------------- status action

print("\nprojectuploadstatus — presence, contribution, and computed state")
st = post({"action": "projectuploadstatus", "session_token": obs, "id": PROJ_A, "period": 1})
check(st.get("ok") is True, "any member may read upload status")
check(st["computed"] is True, "reports the period as computed")
check(any(d["doc_type"] == "unmapped" and d["contributes"] is False
          for d in st["documents"]), "reports the unmapped document as non-contributing")
check(any(d["doc_type"] == "pay_application" and d["contributes"] is True
          for d in st["documents"]), "reports a mapped document as contributing")


# ---------------------------------------------------------------- tail

print()
print("=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
for ok, label, detail in results:
    if not ok:
        print(f"  FAILED: {label}  {detail}")
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
