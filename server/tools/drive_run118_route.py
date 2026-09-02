"""
RUN 118. THE TRADE RECORDS MOVE A4.8'S BAND, THROUGH THE REAL UPLOAD ROUTE.

NOTHING UNDER TEST IS SUPPLIED. Every document goes through `projectupload`, `projectcomputeall`
and `projectcategoryapply`. No structure is handed to a module and `saveprojectdata` is never
called. The only thing this driver asserts on is what `computed_results` holds afterwards.

FOUR PROJECTS, each a paired proof of one claim:
  A  a Green-rated firm with clean trade records                    -> stays Green
  B  the SAME firm, the SAME denominators, records made adverse     -> the band moves
  C  a Green-rated firm and ONE stop-work order                     -> Red, bypassing the average
  D  NO subcontractor performance report at all, one unrated firm   -> banded from the records,
     and what that does to the category and the project status (the owner's specific caution)

Run from `server/`:  python tools/drive_run118_route.py
"""
import base64, hashlib, json, logging, pathlib, sys, time
sys.path.insert(0, "/home/user/LinPRojectRadar/server")
logging.disable(logging.INFO)
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant, ComputedResult

client = TestClient(main.app, raise_server_exceptions=False); S = main.SessionFactory
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, r.text[:400]
    return r.json()
def b64(x): return base64.b64encode(x).decode()

STAMP = str(int(time.time())); ADMIN = "r118-" + STAMP; END = "2026-03-31"
P = F = 0
def ck(name, got, want):
    global P, F
    ok = got == want
    if ok: P += 1
    else:  F += 1
    print(("  PASS " if ok else "  FAIL ") + name + f"\n         got={got!r}\n        want={want!r}")

DENOMS = [{"subcontractor": "Ironline Steel", "inspections_performed": 100,
           "exposure_hours": 1_000_000, "recordable_incidents": 2,
           "environmental_actions_due": 100, "audits_covering_firm": 25, "items_due": 100,
           "field_reports_covering_firm": 100, "systems_tested": 100}]
RATING = {"subcontractor_ratings_json": [
              {"Subcontractor": "Ironline Steel", "Assessment period": "2026-Q1",
               "Rating": "Very Good"}],
          "subcontractor_rating_scale": "owner_five_point_label",
          "subcontractor_report_date": END, "subcontractor_report_version": "v1"}

CLEAN = [{"NCR number": "NCR-1", "Subcontractor": "Ironline Steel", "Type": "nonconformance",
          "Status": "closed", "New this period": "yes"}]
ADVERSE = ([{"NCR number": f"NCR-{i}", "Subcontractor": "Ironline Steel",
             "Type": "nonconformance", "Status": "open", "New this period": "yes"}
            for i in range(6)]
           + [{"Reference": f"INS-{i}", "Subcontractor": "Ironline Steel",
               "Type": "inspection_failure", "Status": "open"} for i in range(11)])
STOPWORK = [{"Reference": "SW-1", "Subcontractor": "Ironline Steel", "Type": "safety_incident",
             "Status": "open", "Severity": "stop_work_order"}]

def build(pid, name, docs):
    def raw(t): return f"%PDF-1.4 R118 {STAMP} {pid} {t}\n".encode()
    set_extractor_override(StubExtractor(
        {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in docs}))
    with S() as s:
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": name, "sector": "construction",
                                              "signals": {}, "events": []}))
        s.commit()
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": f"R118-{pid}", "role": "Participant",
              "account_type": "operational"})
    pm = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": pid,
          "participant_id": c["participant_id"], "project_role": "PM"})
    for t, ty, ex in docs:
        r = post({"action": "projectupload", "session_token": pm, "id": pid, "period": 1,
                  "period_end": END, "documents": [{"filename": t + ".pdf",
                  "mimeType": "application/pdf", "dataBase64": b64(raw(t))}]})
        assert r.get("ok"), (t, str(r)[:200])
    post({"action": "projectcomputeall", "session_token": pm, "id": pid})
    post({"action": "projectcategoryapply", "session_token": pm, "id": pid, "period": 1})
    with S() as s:
        p = s.scalar(select(Project).where(Project.legacy_id == pid))
        row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                    ComputedResult.superseded_by.is_(None)))
        res = {m.get("module_id"): m for m in (row.module_results or [])} if row else {}
        ab = {a.get("module_id"): a for a in (row.abstained or [])} if row else {}
        return res, ab, (row.project_status if row else None), (row.category_statuses if row else None)

def docs_for(attr, with_report=True):
    d = [("ncr", "ncr_log", {"ncr_issued": 3, "ncr_closed": 1, "ncr_open": 2,
                             "inspections_performed": 200, "ncr_denominator_basis": "inspections",
                             "report_period": "2026-Q1",
                             "trade_attribution_json": attr,
                             "trade_denominators_json": DENOMS})]
    if with_report:
        d.append(("sub", "subcontractor_report", dict(RATING, report_period="2026-Q1")))
    return d

with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R118-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

print("=" * 100)
print("RUN 118 -- THE TRADE RECORDS MOVE A4.8, THROUGH THE REAL ROUTE. NOTHING SUPPLIED.")
print("=" * 100)

print("\nA. A GREEN-RATED FIRM WITH CLEAN RECORDS")
res, ab, st, cats = build("PRJ-R118A-" + STAMP, "A", docs_for(CLEAN))
a = res.get("A4.8") or ab.get("A4.8") or {}
ck("A4.8 bands Green", a.get("status_color"), "Green")
ck("the stated rating is the starting band", a.get("reported_rating_posture"), "Green")
gp = (a.get("trade_firm_postures") or [{}])[0]
ck("the firm is assessed and named", gp.get("subcontractor"), "Ironline Steel")
ck("a CLOSED NCR is not counted", gp.get("closed_records_not_counted"), 1)
ck("the denominators reached the factors", gp.get("denominators", {}).get("inspections_performed"),
   100.0)

print("\nB. THE SAME FIRM, THE SAME DENOMINATORS, ADVERSE RECORDS -- THE FAULT INTRODUCED")
res, ab, st, cats = build("PRJ-R118B-" + STAMP, "B", docs_for(ADVERSE))
b = res.get("A4.8") or ab.get("A4.8") or {}
gp = (b.get("trade_firm_postures") or [{}])[0]
ck("6 new open NCRs / 100 inspections = 6 per 100 -> down two bands from Green -> Amber",
   gp.get("factor_bands", {}).get("nonconformances"), "Amber")
ck("11 failed first inspections / 100 = 11 per cent -> Red",
   gp.get("factor_bands", {}).get("failed_inspections"), "Red")
ck("the two adverse factors average against the six clean ones",
   (gp.get("factor_mean_score"), gp.get("adjusted_posture")), (1.125, "Yellow"))
ck("the adjustment is recorded", gp.get("adjustment"), "down 1 band(s) from the stated rating")
ck("A4.8's band MOVED from A -- the records reached the firm", b.get("status_color"), "Yellow")
ck("the audit record carries every factor rate",
   sorted((b.get("pm_review_audit_record") or {}).get("trade_factor_rates", {})),
   ["commissioning", "environmental", "failed_inspections", "field_observations",
    "nonconformances", "procurement", "quality_audit", "safety"])
ck("the audit record carries the source rating, UNALTERED",
   (b.get("pm_review_audit_record") or {}).get("source_rating"), "Very Good")

print("\nC. ONE STOP-WORK ORDER, SEVEN CLEAN FACTORS")
res, ab, st, cats = build("PRJ-R118C-" + STAMP, "C", docs_for(CLEAN + STOPWORK))
c = res.get("A4.8") or ab.get("A4.8") or {}
gp = (c.get("trade_firm_postures") or [{}])[0]
ck("the firm is Red and the average is bypassed",
   (gp.get("adjusted_posture"), gp.get("adjustment_rule")), ("Red", "stop_work_order"))
ck("Red is HELD for PM review: the module asserts no band",
   (c.get("status_color"), c.get("module_state")), (None, "pending_pm_review"))
ck("the stop-work order is on the audit record",
   len((c.get("pm_review_audit_record") or {}).get("trade_stop_work_orders") or []), 1)

print("\nD. NO PERFORMANCE REPORT AT ALL -- SECTION 1.4, AND THE OWNER'S CAUTION")
res, ab, st, cats = build("PRJ-R118D-" + STAMP, "D", docs_for(ADVERSE, with_report=False))
d = res.get("A4.8") or ab.get("A4.8") or {}
ck("A4.8 no longer abstains: it reads the records", d.get("canonical_structure"),
   "subcontractor_trade_factors")
ck("no rating was stated and none was inferred", d.get("reported_rating_posture"), None)
gp = (d.get("trade_firm_postures") or [{}])[0]
ck("with NO starting band the nonconformance displacement produces no band",
   gp.get("factor_bands", {}).get("nonconformances"), None)
ck("the six ladder factors still band and average",
   (gp.get("factor_mean_score"), gp.get("adjusted_posture")), (1.4286, "Yellow"))
ck("Yellow is not held, so it enters the category", d.get("status_color"), "Yellow")
print("        category statuses with the unrated firm banding:", cats)
print("        project status:", st)
ck("FALSIFY -- an UNATTRIBUTED record moves nothing: the same rows with no firm named",
   (lambda r: (r[0].get("A4.8") or r[1].get("A4.8") or {}).get("canonical_structure"))(
       build("PRJ-R118E-" + STAMP, "E",
             docs_for([{k: v for k, v in row.items() if k != "Subcontractor"}
                       for row in ADVERSE], with_report=False))),
   None)

print("\n" + "=" * 100)
print(f"RUN 118 ROUTE SUITE: {P} passed, {F} failed, {P+F} total")
print("=" * 100)
sys.exit(1 if F else 0)
