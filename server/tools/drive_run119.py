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

LAST = {}
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
    LAST["pm"] = pm; LAST["pid"] = pid
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
# RE-POINTED BY RUN 121. Run 119 answered the silent three-band lift with a HOLD; the owner has
# ruled the hold off and required the DISCLOSURE to survive it. So the measurement Run 119 built
# is asserted unchanged above -- the lift is still three bands -- and what changes here is only
# the consequence: the module publishes Green AND says on its reading that it was lifted.
ck("RUN 121: NOT held -- the module publishes the Green it computed",
   (a.get("status_color"), a.get("module_state")), ("Green", "stands"))
ck("the movement is DISCLOSED rather than held",
   ((a.get("pm_review_audit_record") or {}).get("lift_disclosed"),
    (a.get("pm_review_audit_record") or {}).get("held_for_lift")), (True, False))
ck("AND THE DISCLOSURE IS IN THE SENTENCE A READER READS, not only on the audit record",
   "DISCLOSED LIFT: this reading is two or more bands BETTER" in str(a.get("evidence_metric")),
   True)
ck("the source rating is preserved beside the adjusted posture, verbatim",
   (a.get("pm_review_audit_record") or {}).get("source_rating"), "Unsatisfactory")
ck("the audit record carries the band the source rating normalised to",
   (a.get("pm_review_audit_record") or {}).get("source_rating_posture"), "Red")
ck("the disclosure sentence names the lift",
   "two or more bands BETTER" in str(a.get("module_state_words")), True)
ck("A4 carries the module rather than forming without it, and the removed state reaches nothing",
   ("pending_pm_review" not in json.dumps(cats or {}), cats.get("A4") is not None),
   (True, True))
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
    (b.get("pm_review_audit_record") or {}).get("lift_disclosed"),
    b.get("status_color"), b.get("module_state")), (1, False, "Green", "stands"))
ck("and a one-band lift carries NO disclosure sentence -- the disclosure discriminates",
   "DISCLOSED LIFT" in str(b.get("evidence_metric")), False)

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


# ==========================================================================================
# SECTION 5. THE COMMISSIONING REPORT COMPLETES THE PROJECT.
# ==========================================================================================
BAC = 4_000_000
COST_IDENTITY = [
    ("contract", "contract_value", {"original_contract_sum": BAC,
                                    "project_start_date": "2026-01-01",
                                    "project_end_date": "2026-12-31"}),
    ("tps", "time_phased_schedule", {"planned_value_to_date": BAC,
                                     "planned_percent_complete": 100.0,
                                     "data_date": END, "document_date": END}),
    ("pay", "pay_application", {"amount_paid_to_date": BAC, "completed_to_date": BAC,
                                "percent_complete_verified": 100.0,
                                "application_date": END, "document_date": END}),
]
def cx_doc(total, cleared):
    return ("comm", "commissioning_report",
            {"document_date": END, "document_risk_score": 0.1,
             "commissioning_items_total": total, "commissioning_items_cleared": cleared})

def status_of(pid, docs):
    """
    THE PROJECT STATUS AND THE COMPLETION BASIS, READ OFF THE REAL `projectresults` RESPONSE --
    the same response the page the owner loads is built from. Nothing is supplied to it.
    """
    res, ab, st, cats, si = build(pid + "-" + STAMP, pid, docs)
    view = post({"action": "projectresults", "session_token": LAST["pm"],
                 "id": LAST["pid"], "period": 1})
    result = (view.get("result") or {})
    basis = (result.get("project_status_basis") or {})
    return result.get("project_status") or st, basis, si

print("\n5A. EVERY ITEM CLEARED, AND NO COST IDENTITY AT ALL -> COMPLETE")
st, basis, si = status_of("PRJ-R119-C5A", [cx_doc(48, 48)])
ck("the project publishes Complete on the commissioning path alone",
   (st, basis.get("delivery_complete_basis")),
   ("Complete", "every item on the commissioning report cleared for testing"))
ck("the clearance record reached the served response",
   (basis.get("commissioning_clearance") or {}).get("all_cleared"), True)
ck("COMPLETE IS APPLIED AHEAD OF THE REQUIRED-CORE GATE -- Run 112's measurement still holds: "
   "this project has NO assessed category at all and still publishes Complete",
   (basis.get("official"), st), (True, "Complete"))

print("\n5B. SOME ITEMS OUTSTANDING -> NOT COMPLETE, and the reading says how many remain")
st, basis, si = status_of("PRJ-R119-C5B", [cx_doc(48, 45)])
ck("not Complete", st != "Complete", True)
ck("the reading states how many remain",
   (basis.get("commissioning_clearance") or {}).get("outstanding"), 3)
ck("and it says so in words",
   "3 remain" in str(basis.get("commissioning_clearance_words")), True)

print("\n5C. THE COST TEST IS UNTOUCHED -- a project satisfying it stays Complete")
st, basis, si = status_of("PRJ-R119-C5C", COST_IDENTITY)
ck("Complete, on the cost identity, with no commissioning report at all",
   (st, basis.get("delivery_complete_basis"),
    basis.get("commissioning_clearance")),
   ("Complete", "the cost identity", None))

print("\n5D. FALSIFY -- A COMMISSIONING REPORT THAT STATES NEITHER FIGURE COMPLETES NOTHING")
st, basis, si = status_of("PRJ-R119-C5D", [
    ("comm", "commissioning_report", {"document_date": END, "document_risk_score": 0.1})])
ck("no clearance record is assembled and the project is not Complete",
   ("commissioningClearance" in (si or {}), st == "Complete"), (False, False))

print("\n5E. FALSIFY -- MORE CLEARED THAN EXIST IS NOT A READING")
st, basis, si = status_of("PRJ-R119-C5E", [cx_doc(48, 50)])
ck("the record is refused and the project is not Complete",
   (basis.get("commissioning_clearance"), st == "Complete"), (None, False))


# ==========================================================================================
# SECTION 2. NCR RATE AVERAGES THREE DOCUMENTS.
# ==========================================================================================
def ncr_docs(*, log=True, qa=None, fr=None, log_unit="inspections_performed", log_qty=200):
    d = []
    if log:
        d.append(("ncr", "ncr_log", {"ncr_issued": 3, "ncr_closed": 1, "ncr_open": 2,
                                     "report_period": "2026-03", log_unit: log_qty}))
    if qa is not None:
        d.append(("qa", "quality_audit_report",
                  dict({"total_findings": qa[0], "critical_findings": 0, "audit_score": 96,
                        "audit_date": END}, **({qa[2]: qa[1]} if qa[1] is not None else {}))))
    if fr is not None:
        d.append(("fr", "field_report",
                  dict({"document_date": END, "document_risk_score": 0.1,
                        "quality_deficiencies_noted": fr[0]},
                       **({fr[2]: fr[1]} if fr[1] is not None else {}))))
    return d

def a44(pid, docs):
    res, ab, st, cats, si = build(pid + "-" + STAMP, pid, docs)
    return (res.get("A4.4") or ab.get("A4.4") or {}), (si.get("ncrExposureRecord") or {})

print("\n2A. THE THREE DOCUMENTS POOL: 3+4+2 findings over 200+50+100 inspections")
r, rec = a44("PRJ-R119-N2A", ncr_docs(qa=(4, 50, "inspections_performed"),
                                      fr=(2, 100, "inspections_performed")))
ck("one rate over a pooled numerator and a pooled denominator",
   (rec.get("ncr_count"), rec.get("exposure_quantity")), (9, 350.0))
ck("9 of 350 is 2.57 per cent -> Yellow on the owner's unchanged ladder",
   r.get("status_color"), "Yellow")
ck("all three documents are named as contributors",
   sorted(c["source_document_type"] for c in
          (rec.get("ncr_rate_pooling") or {}).get("contributing_documents") or []),
   ["field_report", "ncr_log", "quality_audit_report"])

print("\n2B. THE NCR LOG ALONE, unchanged: 3 of 200 is 1.5 per cent -> Green")
r, rec = a44("PRJ-R119-N2B", ncr_docs())
ck("the ladder and its overrides are untouched by this run",
   (r.get("status_color"), rec.get("ncr_count"), rec.get("exposure_quantity")),
   ("Green", 3, 200.0))

print("\n2C. A DOCUMENT STATING FINDINGS AND NO EXPOSURE CONTRIBUTES NEITHER HALF")
r, rec = a44("PRJ-R119-N2C", ncr_docs(qa=(40, None, "inspections_performed")))
ck("40 audit findings with no stated exposure do NOT inflate the rate",
   (rec.get("ncr_count"), rec.get("exposure_quantity"), r.get("status_color")),
   (3, 200.0, "Green"))
_ex = (rec.get("ncr_rate_pooling") or {}).get("excluded_documents") or []
ck("and the exclusion is named on the record with its reason",
   ([e["source_document_type"] for e in _ex],
    "not the exposure it found it over" in str(_ex)), (["quality_audit_report"], True))

print("\n2D. THE TWO DENOMINATOR UNITS ARE NEVER MIXED")
r, rec = a44("PRJ-R119-N2D", ncr_docs(qa=(4, 50, "active_work_packages"),
                                      fr=(2, 100, "inspections_performed")))
ck("the inspections documents pool; the fallback-unit document is excluded and named",
   (rec.get("exposure_unit"), rec.get("ncr_count"), rec.get("exposure_quantity"),
    [e["source_document_type"] for e in
     (rec.get("ncr_rate_pooling") or {}).get("excluded_documents") or []]),
   ("inspections", 5, 300.0, ["quality_audit_report"]))

print("\n2E. FALSIFY -- THE POOL CHANGES THE BAND. The same NCR log with a field report")
print("    stating 30 defects over 20 inspections: 33 of 220 is 15 per cent -> Red")
r, rec = a44("PRJ-R119-N2E", ncr_docs(fr=(30, 20, "inspections_performed")))
ck("the third document moved the band from Green to Red -- the pool is not decorative",
   (r.get("status_color"), rec.get("ncr_count"), rec.get("exposure_quantity")),
   ("Red", 33, 220.0))
ck("and the precedence change is stated on the record",
   "Before Run 119 this record came from the NCR log alone"
   in str((rec.get("ncr_rate_pooling") or {}).get("precedence_change")), True)

print()
print("=" * 100)
print(f"RUN 119 DRIVER: {P} passed, {F} failed")
print("=" * 100)
sys.exit(1 if F else 0)
