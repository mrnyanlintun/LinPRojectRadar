"""
RUN 119. THE FIVE THAT WERE NEVER REACHED, THROUGH THE REAL UPLOAD ROUTE.

NOTHING UNDER TEST IS SUPPLIED. Every document goes through `projectupload`,
`projectcomputeall` and `projectcategoryapply`. No structure is handed to a module and
`saveprojectdata` is never called. Every assertion is made on what `computed_results` holds
afterwards.

Run from `server/`:  python tools/drive_run119.py
"""
import base64, hashlib, json, logging, sys, time
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

STAMP = str(int(time.time())); ADMIN = "r119-" + STAMP; END = "2026-03-31"
P = F = 0
def ck(name, got, want):
    global P, F
    ok = got == want
    if ok: P += 1
    else:  F += 1
    print(("  PASS " if ok else "  FAIL ") + name + f"\n         got={got!r}\n        want={want!r}")

with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R119-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

def build(pid, name, docs):
    def raw(t): return f"%PDF-1.4 R119 {STAMP} {pid} {t}\n".encode()
    set_extractor_override(StubExtractor(
        {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in docs}))
    with S() as s:
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": name, "sector": "construction",
                                              "signals": {}, "events": []}))
        s.commit()
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": f"R119-{pid}", "role": "Participant",
              "account_type": "operational"})
    pm = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": pid,
          "participant_id": c["participant_id"], "project_role": "PM"})
    for t, ty, ex in docs:
        r = post({"action": "projectupload", "session_token": pm, "id": pid, "period": 1,
                  "period_end": END, "documents": [{"filename": t + ".pdf",
                  "mimeType": "application/pdf", "dataBase64": b64(raw(t))}]})
        assert r.get("ok"), (t, str(r)[:300])
    post({"action": "projectcomputeall", "session_token": pm, "id": pid})
    post({"action": "projectcategoryapply", "session_token": pm, "id": pid, "period": 1})
    with S() as s:
        p = s.scalar(select(Project).where(Project.legacy_id == pid))
        row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                    ComputedResult.superseded_by.is_(None)))
        res = {m.get("module_id"): m for m in (row.module_results or [])} if row else {}
        ab = {a.get("module_id"): a for a in (row.abstained or [])} if row else {}
        return res, ab, (row.project_status if row else None), \
               (row.category_statuses if row else None), (row.signal_inputs if row else {})

print("=" * 100)
print("RUN 119 -- THROUGH THE REAL ROUTE. NOTHING SUPPLIED.")
print("=" * 100)

# ==========================================================================================
# SECTION 1. THE LIFT IS HELD FOR REVIEW.
# ==========================================================================================
DENOMS = [{"subcontractor": "Ironline Steel", "inspections_performed": 100,
           "exposure_hours": 1_000_000, "recordable_incidents": 2,
           "environmental_actions_due": 100, "audits_covering_firm": 25, "items_due": 100,
           "field_reports_covering_firm": 100, "systems_tested": 100}]
CLEAN = [{"NCR number": "NCR-1", "Subcontractor": "Ironline Steel", "Type": "nonconformance",
          "Status": "closed", "New this period": "yes"}]

def rating_docs(word):
    return [("ncr", "ncr_log", {"ncr_issued": 3, "ncr_closed": 1, "ncr_open": 2,
                                "inspections_performed": 200,
                                "ncr_denominator_basis": "inspections",
                                "report_period": "2026-Q1",
                                "trade_attribution_json": CLEAN,
                                "trade_denominators_json": DENOMS}),
            ("sub", "subcontractor_report",
             {"subcontractor_ratings_json": [
                 {"Subcontractor": "Ironline Steel", "Assessment period": "2026-Q1",
                  "Rating": word}],
              "subcontractor_rating_scale": "owner_five_point_label",
              "subcontractor_report_date": END, "subcontractor_report_version": "v1",
              "report_period": "2026-Q1"})]

print("\n1A. UNSATISFACTORY + CLEAN RECORDS + FULL DENOMINATORS -- RUN 118'S SILENT THREE-BAND LIFT")
res, ab, st, cats, si = build("PRJ-R119A-" + STAMP, "1A", rating_docs("Unsatisfactory"))
a = res.get("A4.8") or ab.get("A4.8") or {}
gp = (a.get("trade_firm_postures") or [{}])[0]
ck("the stated rating still normalises to Red", a.get("reported_rating_posture"), "Red")
ck("the factors still lift the firm to Green -- NOTHING about the arithmetic changed",
   gp.get("adjusted_posture"), "Green")
ck("the lift is three bands and is measured", (a.get("pm_review_audit_record") or {}).get("lift_bands"), 3)
ck("HELD: the module asserts NO band and is pending_pm_review",
   (a.get("status_color"), a.get("module_state")), (None, "pending_pm_review"))
ck("held BY THE MOVEMENT, not by the posture",
   (a.get("pm_review_audit_record") or {}).get("held_for_lift"), True)
ck("the source rating is preserved beside the adjusted posture, verbatim",
   (a.get("pm_review_audit_record") or {}).get("source_rating"), "Unsatisfactory")
ck("the audit record carries the band the source rating normalised to",
   (a.get("pm_review_audit_record") or {}).get("source_rating_posture"), "Red")
ck("the held sentence names the lift",
   "lifted two or more bands" in str(a.get("module_state_words")), True)
ck("A4 forms without it -- the hold does not drag the category",
   "pending_pm_review" not in json.dumps(cats or {}), True)
print("        category statuses:", cats, "| project status:", st)

# ITERATION 1 OF THIS CASE USED "Marginal", which normalises to Amber; the clean records lift
# it to Green, which is TWO bands and is correctly held. The fixture was wrong, not the rule.
# "Satisfactory" normalises to Yellow and the same clean records lift it ONE band.
print("\n1B. FALSIFY -- A ONE-BAND LIFT IS NOT HELD (Satisfactory -> Yellow, records lift to Green)")
res, ab, st, cats, si = build("PRJ-R119B-" + STAMP, "1B", rating_docs("Satisfactory"))
b = res.get("A4.8") or ab.get("A4.8") or {}
gpb = (b.get("trade_firm_postures") or [{}])[0]
print("        stated=", b.get("reported_rating_posture"), " adjusted=", gpb.get("adjusted_posture"),
      " lift=", (b.get("pm_review_audit_record") or {}).get("lift_bands"),
      " state=", b.get("module_state"), " band=", b.get("status_color"))
ck("a one-band lift is NOT held, and the module bands",
   ((b.get("pm_review_audit_record") or {}).get("lift_bands"),
    (b.get("pm_review_audit_record") or {}).get("held_for_lift"),
    b.get("status_color"), b.get("module_state")), (1, False, "Green", "stands"))

print("\n1C. FALSIFY -- A GREEN-RATED FIRM WITH CLEAN RECORDS DOES NOT MOVE AND IS NOT HELD")
res, ab, st, cats, si = build("PRJ-R119C-" + STAMP, "1C", rating_docs("Very Good"))
c = res.get("A4.8") or ab.get("A4.8") or {}
ck("no movement, so it stands and bands Green",
   (c.get("status_color"), c.get("module_state"),
    (c.get("pm_review_audit_record") or {}).get("lift_bands")), ("Green", "stands", 0))


# ==========================================================================================
# SECTION 3. DISPUTE ESCALATION BECOMES A DURATION.
# ==========================================================================================
CAL = [{"calendar_id": "5-day work week",
        "working_days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
        "holidays": ["2026-02-16"]}]

def disp_docs(rows, as_of="2026-03-02", calendar=CAL):
    d = [("oac", "oac_minutes", {"document_date": as_of, "document_risk_score": 0.1,
                                 "disputes_json": rows, "report_period": "2026-03"})]
    if calendar is not None:
        d.append(("sched", "schedule_update", {"data_date": as_of,
                                               "schedule_calendar_json": calendar}))
    return d

def a47(pid, rows, **kw):
    res, ab, st, cats, si = build(pid + "-" + STAMP, pid, disp_docs(rows, **kw))
    return res.get("A4.7") or ab.get("A4.7") or {}

print("\n3A. NO OPEN DISPUTE -- every dispute recorded is RESOLVED -> GREEN")
r = a47("PRJ-R119-D3A", [{"Dispute": "D-1", "Raised": "2026-01-05", "Status": "Resolved",
                          "Subject": "Access to level 3"}])
ck("Green, and the resolved dispute stops counting",
   (r.get("status_color"), r.get("dispute_open_count"), r.get("dispute_resolved_count")),
   ("Green", 0, 1))

print("\n3B. ONE DISPUTE OPEN, RAISED THE WORKING DAY BEFORE -> YELLOW")
r = a47("PRJ-R119-D3B", [{"Dispute": "D-1", "Raised": "2026-02-27", "Status": "Open"}])
ck("open one working day is Yellow, not Amber",
   (r.get("status_color"), r.get("dispute_open_working_days")), ("Yellow", 1.0))
ck("one week is the project calendar's own week, read from the calendar",
   (r.get("dispute_working_days_per_week"), r.get("dispute_amber_after_working_days"),
    r.get("dispute_red_after_working_days")), (5, 5, 10))

print("\n3C. OPEN MORE THAN ONE WEEK -> AMBER")
r = a47("PRJ-R119-D3C", [{"Dispute": "D-1", "Raised": "2026-02-19", "Status": "Open"}])
# ITERATION 1 OF THIS CASE EXPECTED 6; the platform counted 7. The platform is right --
# 19 Feb to 2 Mar 2026 excludes two weekends and is seven working days -- and the driver's own
# arithmetic was wrong, not the module's. Recorded rather than quietly corrected.
ck("7 working days open is more than one week (5) -> Amber",
   (r.get("status_color"), r.get("dispute_open_working_days")), ("Amber", 7.0))

print("\n3D. OPEN MORE THAN TWO WEEKS -> RED")
r = a47("PRJ-R119-D3D", [{"Dispute": "D-1", "Raised": "2026-02-05", "Status": "Open"}])
ck("more than ten working days open -> Red", r.get("status_color"), "Red")

print("\n3E. THE HOLIDAY WEEKEND. Raised 2026-02-13 (Fri), as of 2026-02-20 (Fri), with")
print("    Monday 2026-02-16 a stated holiday: SEVEN CALENDAR DAYS but FOUR WORKING DAYS.")
r = a47("PRJ-R119-D3E", [{"Dispute": "D-1", "Raised": "2026-02-13", "Status": "Open"}],
        as_of="2026-02-20")
ck("it is NOT Amber: nobody worked the holiday and the holiday is not counted",
   (r.get("status_color"), r.get("dispute_open_working_days")), ("Yellow", 4.0))

print("\n3F. THE OLDEST OPEN DISPUTE GOVERNS, and a resolved older one does not")
r = a47("PRJ-R119-D3F", [
    {"Dispute": "D-1", "Raised": "2025-11-01", "Status": "Closed"},
    {"Dispute": "D-2", "Raised": "2026-02-27", "Status": "Open"},
    {"Dispute": "D-3", "Raised": "2026-02-05", "Status": "Outstanding"}])
ck("D-3, the oldest OPEN one, governs -- not D-1, which is older and resolved",
   (r.get("governing_dispute_id"), r.get("status_color")), ("D-3", "Red"))

print("\n3G. A STATUS WORD THIS PLATFORM DOES NOT HOLD IS READ AS NEITHER")
r = a47("PRJ-R119-D3G", [{"Dispute": "D-1", "Raised": "2026-01-05", "Status": "With counsel"},
                         {"Dispute": "D-2", "Raised": "2026-02-27", "Status": "Open"}])
ck("the unreadable row is named and enters no band; D-2 alone bands",
   (r.get("status_color"), len(r.get("dispute_unreadable") or []),
    r.get("governing_dispute_id")), ("Yellow", 1, "D-2"))

print("\n3H. FALSIFY -- NO PROJECT CALENDAR: the duration cannot be counted and is not faked")
r = a47("PRJ-R119-D3H", [{"Dispute": "D-1", "Raised": "2026-02-05", "Status": "Open"}],
        calendar=None)
ck("it abstains and the sentence names the calendar",
   (r.get("status_color"), "working calendar" in str(r.get("reason") or "")), (None, True))

print("\n3I. FALSIFY -- NO AS-OF DAY ON THE MINUTES: no day to measure against")
res, ab, st, cats, si = build("PRJ-R119-D3I-" + STAMP, "3I", [
    ("oac", "oac_minutes", {"document_risk_score": 0.1, "report_period": "2026-03",
                            "disputes_json": [{"Dispute": "D-1", "Raised": "2026-02-05",
                                               "Status": "Open"}]}),
    ("sched", "schedule_update", {"data_date": "2026-03-02", "schedule_calendar_json": CAL})])
r = res.get("A4.7") or ab.get("A4.7") or {}
ck("it abstains rather than reading the system clock",
   (r.get("status_color"), "as of" in str(r.get("reason") or "")), (None, True))

print()
print("=" * 100)
print(f"RUN 119 DRIVER: {P} passed, {F} failed")
print("=" * 100)
sys.exit(1 if F else 0)
