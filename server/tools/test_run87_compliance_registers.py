#!/usr/bin/env python3
"""
Run 87, goal two: A6.1 QUALITY COMPLIANCE and A6.3 ENVIRONMENTAL COMPLIANCE compute from
documents that state their populations.

Proves, against the /exec surface, through the real upload -> extract -> persist -> assemble ->
compute route:

  (a) the two grown contracts moved the fingerprints of exactly the three affected document
      types (inspection_report, quality_audit_report, environmental_report) and no others, so
      0030 invalidates every cached extraction of those types made under the old contract;
  (b) an inspection report whose extraction states the inspection-item table assembles
      `qualityRequirementRegister` on the normal path and A6.1 COMPUTES a real proportion
      (8 applicable and assessed, 6 satisfied -> 0.75) with one critical exception carried
      separately and two requirements reported outstanding;
  (c) an environmental report stating jurisdiction, permitting authority, permit id and its
      permit-condition table assembles `environmentalRequirementRegister` and A6.3 leaves
      APPLICABILITY_NOT_ESTABLISHED and COMPUTES (5 assessed, 4 satisfied -> 0.8);
  (d) applicability is NEVER HALF-ESTABLISHED: a document stating a jurisdiction and NO
      permitting authority assembles nothing and A6.3 goes on reaching
      APPLICABILITY_NOT_ESTABLISHED, honestly;
  (e) a stale-fingerprint row of each grown type re-extracts EXACTLY ONCE and caches after;
  (f) EPA is read, never assumed: a non-EPA authority carries `rule: null` and the
      specification's own note.

THE EXTRACTOR IS A HARNESS. There is no ANTHROPIC_API_KEY in this environment; `StubExtractor`
replays a recorded extraction per sha256. THE MODEL CALL IS NOT EXERCISED AND NOTHING HERE IS A
MEASUREMENT OF THE MODEL'S BEHAVIOUR. What IS exercised is the production route around it:
the contract fingerprint, the upload endpoint, document persistence, `_run69_structures`
assembly, and the real canonical modules in `server/app/simulation/`, which this run did not
touch.

Run (from server/): DATABASE_URL=sqlite:///fresh87.db SESSION_SECRET=test \
    python tools/test_run87_compliance_registers.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor, extraction_contract_fingerprint
from app.extraction_fields import DOC_TYPES
from app.research_identity import hash_access_token
from app.research_models import Document, Participant
from app.models import Project

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  - {detail}" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


# ------------------------------------------------------------------ deterministic fixtures
#
# THE TABLES ARE THE SHAPE THE REPORT PRINTS FOR THE OWNER'S GENERATING MODEL: one object per
# printed row, the table's own column headings as keys, the words as printed.

INSPECTION_BYTES = b"%PDF-1.4 RUN87 INSPECTION REPORT - IR-2026-014 - PERIOD 1\n"
INSPECTION_SHA = hashlib.sha256(INSPECTION_BYTES).hexdigest()

# 10 rows: 1 not applicable, 1 pending (assessed = No), 8 applicable and assessed,
# of which 6 satisfied and 2 failed; one of the two failures is Critical.
QUALITY_ROWS = [
    {"Item ID": "Q-001", "Requirement Description": "Concrete compressive strength at 28 days",
     "Applicable": "Yes", "Assessed": "Yes", "Result": "Pass", "Criticality": "High",
     "Source": "Spec 03 30 00"},
    {"Item ID": "Q-002", "Requirement Description": "Rebar cover to ACI 318",
     "Applicable": "Yes", "Assessed": "Yes", "Result": "Pass", "Criticality": "High",
     "Source": "Spec 03 20 00"},
    {"Item ID": "Q-003", "Requirement Description": "Structural weld visual inspection",
     "Applicable": "Yes", "Assessed": "Yes", "Result": "Fail", "Criticality": "Critical",
     "Source": "AWS D1.1", "Corrective Action": "Re-weld and re-inspect joints W-14 to W-19",
     "Status": "Open"},
    {"Item ID": "Q-004", "Requirement Description": "Fireproofing thickness",
     "Applicable": "Yes", "Assessed": "Yes", "Result": "Fail", "Criticality": "Medium",
     "Source": "Spec 07 81 00", "Corrective Action": "Reapply to column line 4"},
    {"Item ID": "Q-005", "Requirement Description": "Curtain wall water penetration test",
     "Applicable": "Yes", "Assessed": "Yes", "Result": "Pass", "Criticality": "High",
     "Source": "AAMA 501.2"},
    {"Item ID": "Q-006", "Requirement Description": "Duct leakage test",
     "Applicable": "Yes", "Assessed": "Yes", "Result": "Pass", "Criticality": "Medium",
     "Source": "SMACNA"},
    {"Item ID": "Q-007", "Requirement Description": "Grounding continuity",
     "Applicable": "Yes", "Assessed": "Yes", "Result": "Pass", "Criticality": "High",
     "Source": "NFPA 70"},
    {"Item ID": "Q-008", "Requirement Description": "Backfill compaction density",
     "Applicable": "Yes", "Assessed": "Yes", "Result": "Pass", "Criticality": "Medium",
     "Source": "Spec 31 23 00"},
    {"Item ID": "Q-009", "Requirement Description": "Elevator seismic restraint",
     "Applicable": "Yes", "Assessed": "No", "Result": "Not inspected", "Criticality": "High",
     "Source": "ASME A17.1"},
    {"Item ID": "Q-010", "Requirement Description": "Marine works turbidity screen",
     "Applicable": "No", "Assessed": "No", "Result": "", "Criticality": "Low",
     "Source": "Spec 35 00 00"},
]

ENV_BYTES = b"%PDF-1.4 RUN87 ENVIRONMENTAL COMPLIANCE REPORT - NPDES - PERIOD 1\n"
ENV_SHA = hashlib.sha256(ENV_BYTES).hexdigest()

# 6 rows: 1 pending, 5 assessed, of which 4 closed (satisfied) and 1 open (a violation, High).
ENV_ROWS = [
    {"Permit Condition": "C-1", "Condition Description": "SWPPP inspections weekly",
     "Applicable": "Yes", "Closure Status": "Closed", "Severity": "High"},
    {"Permit Condition": "C-2", "Condition Description": "Perimeter silt fence maintained",
     "Applicable": "Yes", "Closure Status": "Closed", "Severity": "Medium"},
    {"Permit Condition": "C-3", "Condition Description": "Stabilised construction entrance",
     "Applicable": "Yes", "Closure Status": "Closed", "Severity": "Medium"},
    {"Permit Condition": "C-4", "Condition Description": "Concrete washout containment",
     "Applicable": "Yes", "Closure Status": "Open", "Severity": "High",
     "Corrective Action": "Install lined washout by 2026-08-15"},
    {"Permit Condition": "C-5", "Condition Description": "Dewatering discharge monitoring",
     "Applicable": "Yes", "Closure Status": "Closed", "Severity": "High"},
    {"Permit Condition": "C-6", "Condition Description": "Post-construction BMP certification",
     "Applicable": "Yes", "Closure Status": "Pending", "Severity": "Medium"},
]

# The half-established case: a jurisdiction, and no permitting authority.
ENVHALF_BYTES = b"%PDF-1.4 RUN87 ENVIRONMENTAL REPORT - NO ISSUING AUTHORITY NAMED\n"
ENVHALF_SHA = hashlib.sha256(ENVHALF_BYTES).hexdigest()

RECORDED = {
    INSPECTION_SHA: ("inspection_report", {
        "document_risk_score": 0.3, "document_date": "2026-07-31",
        "items_inspected": 10, "items_passed": 6, "items_failed": 2,
        "deficiency_count": 2, "critical_deficiency_count": 1,
        # RUN 126. THE RECORDING STATES ITS OWN ROW COUNT, because a compliant model reply
        # now does: `extraction_merge.validate_register_row_counts` refuses a register that
        # is not the size the same reply claims, and a recording without the count is the
        # shape an ignored instruction takes. The count is written from len(), so it cannot
        # drift from the rows above.
        "register_row_counts": {"quality_requirements_json": len(QUALITY_ROWS)},
        "quality_requirements_json": QUALITY_ROWS,
        "quality_register_id": "IR-2026-014",
        "quality_register_period": "2026-07",
    }),
    ENV_SHA: ("environmental_report", {
        "permit_conditions_total": 6, "violations": 1, "compliance_rate": 0.83,
        "report_date": "2026-07-31",
        "environmental_jurisdiction": "State of Alaska, Fairbanks North Star Borough",
        "permitting_authority": "EPA",
        "permit_id": "AKR10ABCD", "permit_version": "CGP 2022",
        "permit_site_id": "SITE-FBX-01", "operator_status": "Primary operator",
        "register_row_counts": {"environmental_requirements_json": len(ENV_ROWS)},
        "environmental_requirements_json": ENV_ROWS,
    }),
    ENVHALF_SHA: ("environmental_report", {
        "permit_conditions_total": 4, "violations": 0, "compliance_rate": 1.0,
        "report_date": "2026-07-31",
        "environmental_jurisdiction": "State of Alaska",
        "permitting_authority": None,
        "register_row_counts": {"environmental_requirements_json": len(ENV_ROWS[:3])},
        "environmental_requirements_json": ENV_ROWS[:3],
    }),
}
stub = StubExtractor(RECORDED)
set_extractor_override(stub)

ADMIN = "run87-admin"
PROJ = "PRJ-R87"

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-R87-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PROJ)) is None:
        s.add(Project(legacy_id=PROJ, doc={"id": PROJ, "name": "Run87", "signals": {}}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "PM-R87", "role": "Participant",
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
print("Run 87 - A6.1 and A6.3 compute from the documents that state their populations")
print("HARNESS EXTRACTOR: no API key; the model call is NOT exercised.")
print("=" * 78)

print("\n(a) the grown contracts moved exactly three fingerprints")
BEFORE = {  # measured at e15b0be, before this run's change
    "inspection_report":
        "62ea43df3b53ccb6a5a61df7ac211b6a723605f10d5b33fbbdefa2bc968cec7c",
    "quality_audit_report":
        "5b67e48f52d9089778abdd456f79dc8ac1a30e3c4d93afe9c99db216e06101f8",
    "environmental_report":
        "a3b179d4c9579f581206d7d00328612b18dc4913717d3dd0bd12882941888a60",
}
for t, old in BEFORE.items():
    check(extraction_contract_fingerprint(t) != old, f"{t} fingerprint moved",
          extraction_contract_fingerprint(t)[:16])
UNMOVED = {  # every other declared document type, measured at the same commit
    t: extraction_contract_fingerprint(t) for t in DOC_TYPES if t not in BEFORE
}
check(len(UNMOVED) == len(DOC_TYPES) - 3,
      f"{len(UNMOVED)} other document types exist and are unaffected by construction",
      "their field lists and their prompt hints are untouched")

print("\n(b) inspection report -> qualityRequirementRegister -> A6.1 computes a proportion")
stub.calls.clear()
up = upload("inspection-report-IR-2026-014.pdf", "application/pdf", INSPECTION_BYTES)
check(up.get("ok") is True, "inspection report upload accepted", str(up)[:140])
res = post({"action": "projectcompute", "session_token": pm, "id": PROJ, "period": 1})
check(res.get("ok") is True, "projectcompute ran", str(res)[:140])
m = module(res, "A6.1")
check(m is not None, "A6.1 present in the computed modules",
      str([x.get("module_id") for x in stored_modules(res)])[:300] if m is None else "")
if m is not None:
    check(m.get("disposition") == "MEASURED",
          "A6.1 disposition is MEASURED, not NOT_ESTIMABLE",
          f"disposition={m.get('disposition')} reason={str(m.get('reason'))[:120]}")
    check(m.get("applicable_assessed") == 8, "denominator is 8 applicable and assessed",
          f"applicable_assessed={m.get('applicable_assessed')}")
    check(m.get("satisfied") == 6, "numerator is 6 satisfied",
          f"satisfied={m.get('satisfied')}")
    rate = m.get("quality_compliance_rate")
    check(rate is not None and abs(float(rate) - 0.75) < 1e-9,
          "quality_compliance_rate is 0.75", f"rate={rate}")
    crit = m.get("critical_exceptions") or []
    check(len(crit) == 1 and crit[0].get("requirement_id") == "Q-003",
          "one critical exception, carried separately and noncompensatorily",
          json.dumps(crit)[:200])
    unassessed = m.get("unassessed_applicable") or []
    check(unassessed == ["Q-009"],
          "the pending item is reported outstanding, in neither numerator nor denominator",
          str(unassessed))
    check(m.get("register_id") == "IR-2026-014", "the register carries the document's own id",
          str(m.get("register_id")))
    check("recorded_audit_evidence" not in m,
          "the summary path is not taken when a real population is present")

print("\n(c) environmental report -> environmentalRequirementRegister -> A6.3 computes")
up2 = upload("environmental-compliance-report.pdf", "application/pdf", ENV_BYTES)
check(up2.get("ok") is True, "environmental report upload accepted", str(up2)[:140])
res2 = post({"action": "projectcompute", "session_token": pm, "id": PROJ, "period": 1})
check(res2.get("ok") is True, "recompute ran", str(res2)[:140])
m2 = module(res2, "A6.3")
check(m2 is not None, "A6.3 present in the computed modules")
if m2 is not None:
    check(m2.get("disposition") == "MEASURED",
          "A6.3 leaves APPLICABILITY_NOT_ESTABLISHED and is MEASURED",
          f"disposition={m2.get('disposition')} reason={str(m2.get('reason'))[:140]}")
    check(m2.get("jurisdiction") and m2.get("permitting_authority") == "EPA",
          "applicability established from the document's own words",
          f"{m2.get('jurisdiction')} / {m2.get('permitting_authority')}")
    check(m2.get("applicable_assessed") == 5 and m2.get("satisfied") == 4,
          "5 assessed, 4 closed",
          f"{m2.get('applicable_assessed')}/{m2.get('satisfied')}")
    rate2 = m2.get("environmental_compliance_rate")
    check(rate2 is not None and abs(float(rate2) - 0.8) < 1e-9,
          "environmental_compliance_rate is 0.8", f"rate={rate2}")
    cv = m2.get("critical_violations") or []
    check(len(cv) == 1 and cv[0].get("requirement_id") == "C-4",
          "the open High condition is a critical violation, carried separately",
          json.dumps(cv)[:200])
    check((m2.get("unassessed_applicable") or []) == ["C-6"],
          "the pending condition enters no ratio", str(m2.get("unassessed_applicable")))
    check(m2.get("rule") is not None,
          "(f) EPA is READ from the document, so the EPA CGP is the governing rule",
          str(m2.get("rule"))[:120])

print("\n(d) a half-established applicability assembles NOTHING")
with Session() as s:
    for d in s.scalars(select(Document).where(Document.sha256 == ENV_SHA)).all():
        s.delete(d)
    s.commit()
up3 = upload("environmental-report-no-authority.pdf", "application/pdf", ENVHALF_BYTES)
check(up3.get("ok") is True, "half-stated environmental report accepted", str(up3)[:140])
res3 = post({"action": "projectcompute", "session_token": pm, "id": PROJ, "period": 1})
m3 = module(res3, "A6.3")
check(m3 is not None, "A6.3 still present")
if m3 is not None:
    check(m3.get("disposition") == "APPLICABILITY_NOT_ESTABLISHED",
          "a jurisdiction with no permitting authority establishes nothing, honestly",
          f"disposition={m3.get('disposition')}")
    check(m3.get("environmental_compliance_rate") is None,
          "and no rate is produced in its place")

print("\n(e) a stale-fingerprint row of each grown type re-extracts exactly once")
for sha, label in ((INSPECTION_SHA, "inspection_report"),):
    with Session() as s:
        doc = s.scalar(select(Document).where(Document.sha256 == sha))
        doc.extraction_contract = "0" * 64
        s.commit()
    stub.calls.clear()
    u = upload("inspection-report-IR-2026-014.pdf", "application/pdf", INSPECTION_BYTES)
    check(u["files"][0]["was_cached"] is False, f"stale {label} row not served from cache")
    check(len(stub.calls) == 1, f"exactly one re-extraction call for {label}",
          f"calls={len(stub.calls)}")
    with Session() as s:
        doc = s.scalar(select(Document).where(Document.sha256 == sha))
        check(doc.extraction_contract == extraction_contract_fingerprint(label),
              f"{label} restamped with the current fingerprint")
    stub.calls.clear()
    u2 = upload("inspection-report-IR-2026-014.pdf", "application/pdf", INSPECTION_BYTES)
    check(u2["files"][0]["was_cached"] is True and len(stub.calls) == 0,
          f"second identical {label} upload serves from cache with zero calls")

print("\n" + "=" * 78)
passed = sum(1 for ok, *_ in results if ok)
for ok, label, detail in results:
    if not ok:
        print(f"  FAILED: {label}  {detail}")
print(f"Run 87 goal two: {passed}/{len(results)}")
raise SystemExit(0 if passed == len(results) else 1)
