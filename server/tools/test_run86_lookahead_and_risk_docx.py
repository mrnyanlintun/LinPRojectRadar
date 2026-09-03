#!/usr/bin/env python3
"""
Run 86: A2.8 computes from the look-ahead DOCUMENT, and A3.6 computes from a risk-register
.docx of the shape `risk_table_from_document` recognises.

Proves, against the /exec surface with the StubExtractor (no API key here; the model call is
NOT exercised and is never reported as the model's behaviour — what is exercised is the
production route around it: contract fingerprint, upload, persistence, assembly, module run):

  (a) the Run-86 contract growth changed the lookahead_schedule fingerprint, so 0030
      invalidates every cached look-ahead extraction made under the old contract;
  (b) a look-ahead upload whose extraction states the activity table, the horizon and the
      status date assembles lookAheadSchedule on the normal path and A2.8 COMPUTES the ready
      fraction (10 planned, 3 open constraints -> 0.70);
  (c) a stale-fingerprint look-ahead row re-extracts exactly once on re-upload;
  (d) a synthetic risk-register .docx printing the recognised headings (Risk ID, Risk
      Description, Probability, Cost Impact ($), Status) uploads through the real route,
      `_persist_project_risks` reads its rows from the stored bytes, and A3.6 Cost Risk P80
      COMPUTES on the register plus the period's BAC. The .docx bytes are built with pinned
      zip timestamps so the fixture is deterministic (Run 73's lesson).

Run (from server/): DATABASE_URL=sqlite:///fresh86.db SESSION_SECRET=test \
    python tools/test_run86_lookahead_and_risk_docx.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import zipfile
from io import BytesIO

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor, extraction_contract_fingerprint
from app.research_identity import hash_access_token
from app.research_models import Document, Participant
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
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


# ------------------------------------------------------------------ deterministic fixtures

LOOKAHEAD_BYTES = b"%PDF-1.4 RUN86 THREE-WEEK LOOK-AHEAD - STATUS DATE 2026-07-31\n"
LOOKAHEAD_SHA = hashlib.sha256(LOOKAHEAD_BYTES).hexdigest()

# The table exactly as the prompt asks for it: one object per printed row, the table's own
# column headings as keys, the status word as printed. 10 activities, 3 with open constraints.
_ROWS = []
for i in range(1, 11):
    row = {"Activity ID": f"A-{100 + i}", "Activity Description": f"Work package {i}",
           "Constraint Status": "Cleared"}
    _ROWS.append(row)
for i, cat in ((1, "Materials"), (4, "Engineering"), (7, "Permits")):
    _ROWS[i - 1]["Constraint Status"] = "Open"
    _ROWS[i - 1]["Constraint Category"] = cat

MONTHLY_BYTES = b"%PDF-1.4 RUN86 MONTHLY REPORT - BAC 10,000,000\n"
MONTHLY_SHA = hashlib.sha256(MONTHLY_BYTES).hexdigest()


def _docx(tables_xml: str) -> bytes:
    """A minimal .docx: word/document.xml inside a zip, timestamps pinned (deterministic)."""
    doc = ('<?xml version="1.0"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           f'<w:body>{tables_xml}</w:body></w:document>')
    ct = ('<?xml version="1.0"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
          'officedocument.wordprocessingml.document.main+xml"/></Types>')
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in (("[Content_Types].xml", ct), ("word/document.xml", doc)):
            info = zipfile.ZipInfo(name, date_time=(2026, 8, 29, 0, 0, 0))
            zf.writestr(info, data)
    return buf.getvalue()


def _tbl(rows: list[list[str]]) -> str:
    out = "<w:tbl>"
    for r in rows:
        out += "<w:tr>" + "".join(
            f"<w:tc><w:p><w:r><w:t>{c}</w:t></w:r></w:p></w:tc>" for c in r) + "</w:tr>"
    return out + "</w:tbl>"


# The shape §7.3 of the report prints for the owner's generating model: these headings are in
# `risk_register._HEADINGS` verbatim ("cost impact" matches with a trailing unit qualifier).
RISK_ROWS = [
    ["Risk ID", "Risk Description", "Probability", "Cost Impact ($)", "Status"],
    ["R-01", "Differing site conditions at the north abutment", "0.40", "1,200,000", "Open"],
    ["R-02", "Steel delivery slips past erection window", "0.25", "2,000,000", "Open"],
    ["R-03", "Permit renewal delayed by agency backlog", "0.10", "800,000", "Open"],
    ["R-04", "Design rework of MEP risers", "0.50", "600,000", "Open"],
]
RISK_DOCX = _docx(_tbl(RISK_ROWS))
RISK_SHA = hashlib.sha256(RISK_DOCX).hexdigest()

RECORDED = {
    LOOKAHEAD_SHA: ("lookahead_schedule", {
        "activities_planned": 10, "activities_constrained": 3, "lookahead_weeks": 3,
        # RUN 126. The recording states its own row count, as a compliant reply now must.
        "register_row_counts": {"lookahead_activities_json": len(_ROWS)},
        "lookahead_activities_json": _ROWS,
        "lookahead_horizon": "3 weeks", "lookahead_status_date": "2026-07-31",
    }),
    MONTHLY_BYTES and MONTHLY_SHA: ("monthly_report", {
        "earned_value": 4000000, "actual_cost": 4400000, "planned_value": 4500000,
        "budget_at_completion": 10000000, "report_date": "2026-07-31",
    }),
    RISK_SHA: ("risk_register", {
        "document_risk_score": 0.4, "document_date": "2026-07-31",
    }),
}
stub = StubExtractor(RECORDED)
set_extractor_override(stub)

ADMIN = "run86-admin"
PROJ = "PRJ-R86"

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-R86-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PROJ)) is None:
        s.add(Project(legacy_id=PROJ, doc={"id": PROJ, "name": "Run86", "signals": {}}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "PM-R86", "role": "Participant",
                "account_type": "operational"})
assert created.get("ok"), created
pm = post({"action": "researchlogin",
           "access_token": created["access_token"]})["session_token"]
r = post({"action": "adminmemberadd", "session_token": admin, "id": PROJ,
          "participant_id": created["participant_id"], "project_role": "PM"})
assert r.get("ok"), r


def upload(filename: str, mime: str, raw: bytes) -> dict:
    return post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": 1,
                 "documents": [{"filename": filename, "mimeType": mime,
                                "dataBase64": b64(raw)}]})


def stored_modules(result: dict) -> list[dict]:
    """The module readings, from the stored computed_results row — the canonical store."""
    from app.research_models import ComputedResult
    with Session() as s:
        row = s.scalar(select(ComputedResult)
                       .where(ComputedResult.result_id == result.get("result_id")))
        return list(row.module_results or []) if row is not None else []


def module(result: dict, name: str) -> dict | None:
    for m in stored_modules(result):
        if isinstance(m, dict) and name in (m.get("method_class"), m.get("module_id")):
            return m
    return None


print("=" * 78)
print("Run 86 — A2.8 from the look-ahead document; A3.6 from the risk-register .docx")
print("=" * 78)

print("\n(a) the grown contract changed the lookahead_schedule fingerprint")
FP_BEFORE = "d1cd40f8f9148cf322b539e9a2f498489bd00bd9ba3a6f2f8748d2e46398519a"  # measured pre-change
fp_now = extraction_contract_fingerprint("lookahead_schedule")
check(fp_now != FP_BEFORE, "lookahead_schedule fingerprint moved", fp_now[:16])

print("\n(b) look-ahead upload -> assembly -> A2.8 computes the ready fraction")
stub.calls.clear()
up = upload("weekly-lookahead-schedule.pdf", "application/pdf", LOOKAHEAD_BYTES)
check(up.get("ok") is True, "look-ahead upload accepted", str(up)[:120])
up2 = upload("monthly-report-07.pdf", "application/pdf", MONTHLY_BYTES)
check(up2.get("ok") is True, "monthly report upload accepted", str(up2)[:120])
res = post({"action": "projectcompute", "session_token": pm, "id": PROJ, "period": 1})
check(res.get("ok") is True, "projectcompute ran", str(res)[:160])
m = module(res, "Lookahead_Health")
check(m is not None, "A2.8 Lookahead_Health present in the computed modules",
      str([x.get("model") or x.get("name") for x in res.get("modules") or []])[:200]
      if m is None else "")
if m is not None:
    check(abs(float(m.get("ready_fraction") or -1) - 0.70) < 1e-9,
          "ready fraction is 0.70 (10 planned, 3 open)", json.dumps(m)[:220])
    check(m.get("calibration_pending") is True and m.get("band_asserted") is False,
          "A2.8 computed bandless (calibration pending), not abstained",
          (m.get("evidence_metric") or "")[:160])

print("\n(c) a stale-fingerprint look-ahead row re-extracts exactly once")
with Session() as s:
    doc = s.scalar(select(Document).where(Document.sha256 == LOOKAHEAD_SHA))
    doc.extraction_contract = "0" * 64
    s.commit()
stub.calls.clear()
up3 = upload("weekly-lookahead-schedule.pdf", "application/pdf", LOOKAHEAD_BYTES)
check(up3["files"][0]["was_cached"] is False, "stale look-ahead row not served from cache")
check(len(stub.calls) == 1, "exactly one re-extraction call", f"calls={len(stub.calls)}")
with Session() as s:
    doc = s.scalar(select(Document).where(Document.sha256 == LOOKAHEAD_SHA))
    check(doc.extraction_contract == fp_now, "restamped with the current fingerprint")
stub.calls.clear()
up4 = upload("weekly-lookahead-schedule.pdf", "application/pdf", LOOKAHEAD_BYTES)
check(up4["files"][0]["was_cached"] is True and len(stub.calls) == 0,
      "second identical upload serves from cache with zero calls")

print("\n(d) the risk-register .docx -> stored rows -> A3.6 computes")
up5 = upload("risk-register.docx",
             "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
             RISK_DOCX)
check(up5.get("ok") is True, "risk .docx upload accepted", str(up5)[:160])
res2 = post({"action": "projectcompute", "session_token": pm, "id": PROJ, "period": 1})
check(res2.get("ok") is True, "recompute ran", str(res2)[:120])
m2 = module(res2, "A3.6")
check(m2 is not None, "A3.6 Cost_Risk_Analysis present in the computed modules",
      str([x.get("module_id") for x in stored_modules(res2)])[:260] if m2 is None
      else (m2.get("evidence_metric") or "")[:200])
if m2 is not None:
    check(isinstance(m2.get("p80_total_cost"), (int, float)) and m2["p80_total_cost"] > 10000000,
          "the reading carries a P80 above the base cost",
          f"p80_total_cost={m2.get('p80_total_cost')}")
with Session() as s:
    from app.research_models import ProjectRisk
    n = len(s.scalars(select(ProjectRisk)).all())
    check(n == 4, "four register rows persisted from the .docx bytes", f"rows={n}")

print("\n" + "=" * 78)
passed = sum(1 for ok, *_ in results if ok)
for ok, label, detail in results:
    if not ok:
        print(f"  FAILED: {label}  {detail}")
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
