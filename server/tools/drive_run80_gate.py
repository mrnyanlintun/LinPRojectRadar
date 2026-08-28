#!/usr/bin/env python3
"""
RUN 80. THREE DEFECTS, MEASURED BY EXECUTION ON A LOCAL REPRODUCTION.

TST-007 IS NOT IN THIS DATABASE. This builds the SHAPE through the REAL routes: real
reportlab PDFs, the real `projectupload`, the real `projectcomputeall`, and the real
`projectdocumentarchive`. Extraction is the StubExtractor (no ANTHROPIC_API_KEY here), so
the FIELD NAMES come from `extraction_fields_for` -- the prompt's own contract -- and the
values are fixture data.

argv[1] = label   argv[2] = output json
"""
from __future__ import annotations
import base64, hashlib, io, json, logging, os, pathlib, sys, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run80"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run80_capture.json")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

from reportlab.lib.pagesizes import LETTER            # noqa: E402
from reportlab.pdfgen import canvas as rl_canvas      # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
from sqlalchemy import select, func                   # noqa: E402
import app.main as main                               # noqa: E402
from app.documents import set_extractor_override      # noqa: E402
from app.extraction_client import StubExtractor       # noqa: E402
from app.extraction_fields import extraction_fields_for  # noqa: E402
from app.models import Project                        # noqa: E402
from app.research_identity import hash_access_token   # noqa: E402
from app.research_models import Participant, Observation, Document, DocumentUpload  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R80-{STAMP}"
ADMIN = f"run80-admin-{STAMP}"
PERIOD_END = "2026-03-31"

def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:400]}"
    return r.json()

def b64(raw): return base64.b64encode(raw).decode()

DOCSET = [
    ("D01_contract_award.pdf",                  "contract_value"),
    ("D02_pay_application.pdf",                 "pay_application"),
    ("D03_schedule_of_values.pdf",              "schedule_of_values"),
    ("D04_time_phased_schedule.pdf",            "time_phased_schedule"),
    ("D06_monthly_report.pdf",                  "monthly_report"),
    ("D08_cost_report.pdf",                     "cost_report"),
    ("D09_rfi_log.pdf",                         "rfi_log"),
    ("D11_submittal_register.pdf",              "submittal_register"),
    ("D12_ncr_log.pdf",                         "ncr_log"),
    ("D14_quality_audit_report.pdf",            "quality_audit_report"),
    ("D15_safety_report.pdf",                   "safety_report"),
    ("D23_risk_register.pdf",                   "risk_register"),
    ("D26_past_performance_report.pdf",         "past_performance_report"),
    ("D27_historical_project_data.pdf",         "historical_data"),
]

VALUES = {
  "original_contract_sum": 4_000_000, "project_start_date": "2026-01-01",
  "project_end_date": "2027-06-30", "federal_acquisition": True,
  "contracting_agency": "General Services Administration",
  "acquisition_designation": "development", "major_acquisition": True,
  "agency_procedure_requires_evms": True, "evms_clause_id": "FAR 52.234-4",
  "award_date": "2026-01-01", "acquisition_id": "GS-P-26-0114",
  "amount_paid_to_date": 1_050_000, "completed_to_date": 1_000_000,
  "percent_complete_verified": 25.0, "application_date": PERIOD_END,
  "original_contingency": 920_000, "remaining_contingency": 892_400,
  "retainage_held": 52_500, "retainage_percent": 5.0,
  "scheduled_value_total": 4_000_000, "period_to_date": 1_000_000,
  "planned_value_to_date": 1_020_000, "planned_percent_complete": 25.5,
  "data_date": PERIOD_END,
  "baseline_version": "PMB Rev 2", "baseline_approval_source": "BCB-2026-004",
  "total_float_days": 12, "critical_path_length_days": 540,
  "earned_value": 1_000_000, "actual_cost": 1_050_000, "planned_value": 1_020_000,
  "actual_percent_complete": 25.0, "budget_at_completion": 4_000_000,
  "report_date": PERIOD_END,
  "indirect_cost_plan": 480_000, "indirect_cost_actual": 561_000,
  "material_cost_baseline": 900_000, "material_cost_current": 940_000,
  "overhead_allocation_base": "direct labour hours",
  "planned_allocation_base_quantity": 120_000,
  "actual_allocation_base_quantity": 131_000,
  "overhead_driver_source": "the overhead schedule printed in this cost report",
  "rfi_total": 120, "rfi_open": 30, "rfi_answered": 90, "rfi_overdue": 8,
  "avg_response_days": 11, "rfi_period_days": 30, "oldest_open_days": 44,
  "log_date": PERIOD_END,
  "submittals_total": 200, "submittals_rejected": 24, "submittals_overdue": 7,
  "ncr_issued": 14, "ncr_closed": 9, "ncr_open": 5, "report_period": PERIOD_END,
  "total_findings": 18, "critical_findings": 3, "audit_score": 82,
  "audit_date": PERIOD_END,
  "osha_recordable_incidents": 2, "total_manhours": 180_000, "incident_rate": 2.2,
  "lost_time_incidents": 1,
  "overall_rating": "Satisfactory", "schedule_rating": "Satisfactory",
  "cost_rating": "Marginal", "quality_rating": "Very Good",
  "source": "CPARS record for the prior contract",
  "analogous_overrun_pct": 9.0, "analogous_project_type": "federal courthouse fit-out",
  "completion_year": 2023, "similar_project_bac": 3_600_000,
  "similar_project_final_cost": 3_906_000,
  "document_risk_score": 0.4, "document_date": PERIOD_END,
}

def extraction_for(doc_type: str) -> dict:
    ex = {}
    for f in (extraction_fields_for(doc_type) or []):
        if f in VALUES:
            ex[f] = VALUES[f]
    ex.setdefault("document_date", PERIOD_END)
    return ex

def make_pdf(filename: str, doc_type: str, ex: dict) -> bytes:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=LETTER)
    c.setFont("Helvetica-Bold", 13); c.drawString(72, 720, filename)
    c.setFont("Helvetica", 9); y = 700
    c.drawString(72, y, f"Document type: {doc_type}  Period 1 ending {PERIOD_END}"); y -= 16
    c.drawString(72, y, f"run stamp {STAMP}"); y -= 20
    for k, v in ex.items():
        s = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
        for chunk in [s[i:i+90] for i in range(0, max(len(s), 1), 90)]:
            c.drawString(72, y, f"{k}: {chunk}"); y -= 12
            if y < 60:
                c.showPage(); c.setFont("Helvetica", 9); y = 720
    c.showPage(); c.save()
    return buf.getvalue()

BYTES, OVERRIDE, EXPECTED = {}, {}, {}
for fn, dt in DOCSET:
    ex = extraction_for(dt); EXPECTED[fn] = ex
    raw = make_pdf(fn, dt, ex); BYTES[fn] = raw
    OVERRIDE[hashlib.sha256(raw).hexdigest()] = (dt, ex, 0.95)
set_extractor_override(StubExtractor(OVERRIDE))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code=f"R80-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 80 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R80-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

UP = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
           "period_end": PERIOD_END,
           "documents": [{"filename": fn, "mimeType": "application/pdf",
                          "dataBase64": b64(BYTES[fn])} for fn, _ in DOCSET]})
CR = post({"action": "projectcomputeall", "session_token": PM, "id": PID})

def snapshot(tag):
    pr = post({"action": "projectperiods", "session_token": PM, "id": PID})
    LP = pr.get("latest_computed_period")
    res = post({"action": "projectresults", "session_token": PM, "id": PID, "period": LP})
    ROW = res.get("result") or {}
    SI = ROW.get("signal_inputs") or {}
    MR = ROW.get("module_results") or []
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PID))
        obs = s.execute(
            select(Document.filename, Observation.field, Observation.value,
                   Observation.source_doc_type, Observation.document_id,
                   Observation.withdrawn_at, Observation.withdrawn_by,
                   Observation.withdrawn_by_event_id)
            .join(Observation, Observation.document_id == Document.document_id)
            .where(Observation.project_id == proj.id, Observation.period == 1)).all()
    return {"tag": tag, "period": LP, "si": SI, "modules": MR,
            "obs": [{"file": o[0], "field": o[1], "value": o[2], "sdt": o[3], "doc": o[4],
                     "withdrawn_at": o[5], "withdrawn_by": o[6], "withdrawn_event": o[7]}
                    for o in obs]}


# =====================================================================================
# RUN 80, FIX ONE. THE CATEGORY-9 GATE, SETTLED BY EXECUTION RATHER THAN BY OPINION.
#
# Run 66 found the gate. Run 68 reported it fixed. Run 78 measured that the gate PASSES on
# current code and found the real cause upstream: `_period_is_stale` compared document sets
# only, so a row computed before Run 67 shipped was NOT stale, `projectcomputeall` skipped it,
# and `evidenceQualification` never appeared. Run 78 added a second staleness condition at
# documents.py:1211. This driver EXECUTES that claim end to end:
#
#   PHASE 1  compute normally                -> is the key written? do gated modules pass?
#   PHASE 2  strip the key from the stored    -> reproduces a pre-Run-67 row EXACTLY: same
#            row, in the database                documents, same fingerprint, no assessment
#   PHASE 3  re-run the gated modules on that stripped signal_inputs -> do they refuse?
#   PHASE 4  press projectcomputeall again    -> does the Run 78 condition find it stale,
#                                                rewrite the key, and free the modules?
# =====================================================================================
from app.research_models import ComputedResult              # noqa: E402
from app.simulation.registry import run_module, service_index  # noqa: E402
from app.simulation.qualification_boundary import gated_module_ids  # noqa: E402
from app.documents import _period_is_stale                  # noqa: E402
import datetime as _dt                                      # noqa: E402

GATE_SENTENCE = "carries no Category-9 assessment"

GATED_IN_SERVICE = sorted(set(gated_module_ids()) & set(service_index()))

def gate_probe(si: dict) -> dict:
    """Run every gated module in service on this signal_inputs. Count gate refusals."""
    refused, other, values = [], [], []
    for mid in GATED_IN_SERVICE:
        try:
            r = run_module(mid, si, lambda: 0.5, _dt.date.fromisoformat(PERIOD_END))
        except Exception as e:                      # noqa: BLE001
            other.append((mid, f"RAISED {type(e).__name__}: {e}")); continue
        note = str(r.get("evidence_metric") or r.get("note") or r.get("reason") or "")
        code = str(r.get("abstention_reason_code") or "")
        if code == "CATEGORY9_ASSESSMENT_MISSING" or GATE_SENTENCE in note:
            refused.append((mid, note))
        elif r.get("insufficient_data") or r.get("value") is None:
            other.append((mid, code + " :: " + note[:200]))
        else:
            values.append((mid, r.get("value"), note[:120]))
    return {"gated_total": len(GATED_IN_SERVICE), "refused_by_gate": len(refused),
            "abstained_other": len(other), "produced_value": len(values),
            "refused": refused, "other": other, "values": values}

def stored_si():
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PID))
        row = s.scalars(select(ComputedResult)
                        .where(ComputedResult.project_id == proj.id)
                        .order_by(ComputedResult.period.desc())).first()
        return dict(row.signal_inputs or {}), row.period

REPORT = {"label": LABEL, "project": PID,
          "gated_module_ids_declared": len(gated_module_ids()),
          "gated_in_service": GATED_IN_SERVICE,
          "service_index_size": len(service_index())}

# ---------------- PHASE 1: as computed by the real route
SI1, PERIOD = stored_si()
REPORT["phase1_key_present"] = "evidenceQualification" in SI1
REPORT["phase1_evidenceQualification"] = SI1.get("evidenceQualification")
REPORT["phase1_probe"] = gate_probe(SI1)

# ---------------- PHASE 2: strip the key in the database, reproducing a pre-Run-67 row
with Session() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == PID))
    row = s.scalars(select(ComputedResult).where(ComputedResult.project_id == proj.id)
                    .order_by(ComputedResult.period.desc())).first()
    si = dict(row.signal_inputs or {}); si.pop("evidenceQualification", None)
    row.signal_inputs = si
    s.add(row); s.commit()
SI2, _ = stored_si()
REPORT["phase2_key_present"] = "evidenceQualification" in SI2

# ---------------- PHASE 3: do the gated modules refuse on the stripped row?
REPORT["phase3_probe"] = gate_probe(SI2)

# ---------------- PHASE 3b: does the Run 78 staleness condition FIND that row stale?
with Session() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == PID))
    row = s.scalars(select(ComputedResult).where(ComputedResult.project_id == proj.id)
                    .order_by(ComputedResult.period.desc())).first()
    stale, reason = _period_is_stale(s, proj, row.period, row)
REPORT["phase3b_is_stale"] = stale
REPORT["phase3b_reason"] = reason

# ---------------- PHASE 4: press the real recompute route
REPORT["phase4_recompute"] = post({"action": "projectcomputeall", "session_token": PM, "id": PID})
SI4, _ = stored_si()
REPORT["phase4_key_present"] = "evidenceQualification" in SI4
REPORT["phase4_probe"] = gate_probe(SI4)

json.dump(REPORT, OUT.open("w"), indent=2, default=str)
print(f"project {PID}  period {PERIOD}")
print(f"gated_module_ids() declares {len(gated_module_ids())}; in service: {len(GATED_IN_SERVICE)}")
print(f"  {GATED_IN_SERVICE}")
for ph in ("phase1", "phase3", "phase4"):
    p = REPORT[f"{ph}_probe"]
    print(f"{ph}: key_present={REPORT.get(ph.replace('phase3','phase2')+'_key_present')} "
          f"refused_by_gate={p['refused_by_gate']}/{p['gated_total']} "
          f"abstained_other={p['abstained_other']} produced_value={p['produced_value']}")
print(f"phase3b _period_is_stale -> {REPORT['phase3b_is_stale']}: {REPORT['phase3b_reason']}")
print(f"capture -> {OUT}")
