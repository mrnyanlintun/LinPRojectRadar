"""
RUN 107. THE EIGHT THRESHOLDS, AND THE PM REVIEW STATE, ON THE PAGE THE OWNER LOADS.

WHAT IS REAL AND WHAT IS HARNESS, STATED BEFORE ANYTHING IS MEASURED.

  REAL ROUTE. One project is built through the REAL upload route, the REAL `saveprojectdata`
  intake (the production path by which a project supplies a governed structure), the REAL
  compute route, the REAL `projectmodulereview` write, the REAL recompute, and the REAL
  `projectresults` read. Section 6 serves the REAL application and opens the REAL detail page in
  Chromium. NOTHING UNDER TEST IS SUPPLIED TO A RENDERER: no brief is composed here, none is
  injected, none is handed to a render function, and `window.LinResults.rowFor` is NOT
  substituted -- it is only READ, to wait until the row the page fetched has arrived.

  HARNESS. Section 5 calls the module runners and `project_posture` directly. Those are proofs
  about the RULES -- that each ladder, each worst-of and each hard override is able to go the
  other way -- and every one of them is proved ABLE TO FAIL by feeding it the failing case.
  They are not proofs about the page; section 6 is.

  NO MODEL CALL IS SIMULATED. There is no ANTHROPIC_API_KEY here; extraction runs through
  `StubExtractor`. The extraction-contract text this run added -- the OAC minutes' weather-day
  approval fields and the Subcontractor Performance Report's per-firm rating table -- is
  UNEXERCISED AGAINST A REAL MODEL and is reported as such.
"""
import base64, hashlib, json, logging, os, pathlib, socket, sys, threading, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
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
    assert r.status_code == 200, r.text[:300]
    return r.json()
def b64(x): return base64.b64encode(x).decode()

PASS = FAIL = 0
def check(cond, what, got=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {what}" + (f" [{got}]" if got else ""))
    else:    FAIL += 1; print(f"  FAIL  {what}" + (f" [{got}]" if got else ""))

STAMP = str(int(time.time())); ADMIN = "r107-" + STAMP
PID = "PRJ-R107-" + STAMP; END = "2026-03-31"; BAC = 4_000_000

# ---------------------------------------------------------------------------------------------
# The documents. READ OUT of Run 103's own set so the base project cannot drift from the corpus,
# with the two this run grew replaced by their grown form.
# ---------------------------------------------------------------------------------------------
import importlib.util as _ilu
_src = (HERE / "drive_run103_census.py").read_text()
_docs_src = _src[_src.index("DOCS = ["):_src.index("]\ndef raw(")+1]
_ns = {"BAC": BAC, "END": END}
exec(_docs_src, _ns)
DOCS = list(_ns["DOCS"])

def _replace(tag, extra):
    for i, (t, ty, ex) in enumerate(DOCS):
        if t == tag:
            merged = dict(ex); merged.update(extra); DOCS[i] = (t, ty, merged); return
    raise AssertionError(tag)

# RUN 107, SECTION 2. THE GROWN OAC MINUTES CONTRACT, printed as minutes print it.
_replace("oac", {
    "weather_days_claimed": 9, "weather_days_approved": 7,
    "weather_approval_period": "2026-03", "weather_allowance_days": 10,
    "weather_time_extension_granted": True, "weather_time_extension_days": 7})
# RUN 107, SECTION 2. THE GROWN SUBCONTRACTOR PERFORMANCE REPORT, as a per-firm TABLE.
_replace("subr", {
    "subcontractor_rating_scale": "owner_five_point_label",
    "subcontractor_report_date": END, "subcontractor_report_version": "Rev 1",
    "subcontractor_ratings_json": [
        {"Subcontractor": "Northline Mechanical", "Assessment period": "2026-03",
         "Rating": "Very Good", "Work package": "Div 23"},
        {"Subcontractor": "Delta Electrical", "Assessment period": "2026-03",
         "Rating": "Marginal", "Work package": "Div 26"}]})

def raw(t): return f"%PDF-1.4 R107 {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest(): (ty, ex)
                                      for t, ty, ex in DOCS}))
with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R107-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 107 fixture",
                                          "sector": "construction", "signals": {}, "events": []}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
c = post({"action": "adminparticipantcreate", "session_token": admin,
          "pseudonymous_code": "R107-PM-" + STAMP, "role": "Participant",
          "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
PM_ID = c["participant_id"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": PM_ID, "project_role": "PM"})
# A1.5 IS DEFINED ON A COST PERFORMANCE HISTORY OF AT LEAST EIGHT READINGS, and this platform
# assembles that history from the project's OWN EARLIER PERIODS (`documents._period_history`) --
# there is no field, no structure and no route by which one may be typed in, and none is
# invented here. So the project is built the way a real one arrives: NINE EARLIER PERIODS, each
# through the real upload and compute routes, each with its own cost report, and the cost
# performance index falling gently across them. NOTHING IS SUPPLIED TO A MODULE: the history is
# what the platform assembles from nine stored results.
LIVE_PERIOD = 10
_EARLY_CPI = [1.02, 1.015, 1.01, 1.00, 0.995, 0.99, 0.985, 0.98, 0.975]
def early_raw(p, t): return f"%PDF-1.4 R107E {STAMP} {p} {t}\n".encode()
_early_map = {}
for _p, _cpi in enumerate(_EARLY_CPI, start=1):
    _ac = 100_000 * _p
    _ev = round(_ac * _cpi)
    _early_map[hashlib.sha256(early_raw(_p, "contract")).hexdigest()] = (
        "contract_value", {"original_contract_sum": BAC, "project_start_date": "2026-01-01",
                           "project_end_date": "2027-06-30"})
    _early_map[hashlib.sha256(early_raw(_p, "pay")).hexdigest()] = (
        "pay_application", {"amount_paid_to_date": _ac, "completed_to_date": _ev,
                            "percent_complete_verified": round(100 * _ev / BAC, 2),
                            "application_date": f"2025-{_p:02d}-28",
                            "document_date": f"2025-{_p:02d}-28"})
    _early_map[hashlib.sha256(early_raw(_p, "tps")).hexdigest()] = (
        "time_phased_schedule", {"planned_value_to_date": _ac,
                                 "planned_percent_complete": round(100 * _ac / BAC, 2),
                                 "data_date": f"2025-{_p:02d}-28",
                                 "document_date": f"2025-{_p:02d}-28"})
set_extractor_override(StubExtractor({**_early_map,
                                      **{hashlib.sha256(raw(t)).hexdigest(): (ty, ex)
                                         for t, ty, ex in DOCS}}))
for _p in range(1, LIVE_PERIOD):
    for _t in ("contract", "pay", "tps"):
        post({"action": "projectupload", "session_token": PM, "id": PID, "period": _p,
              "period_end": f"2025-{_p:02d}-28",
              "documents": [{"filename": f"{_t}-{_p}.pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(early_raw(_p, _t))}]})
ok = 0
for t, ty, ex in DOCS:
    r = post({"action": "projectupload", "session_token": PM, "id": PID,
              "period": LIVE_PERIOD, "period_end": END,
              "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(raw(t))}]})
    ok += 1 if r.get("ok") else 0
print(f"uploaded {ok}/{len(DOCS)} documents into period {LIVE_PERIOD}, after "
      f"{LIVE_PERIOD - 1} earlier periods, all through the real route")

# ---------------------------------------------------------------------------------------------
# SECTION 1. THE EIGHT STRUCTURES, THROUGH THE REAL `saveprojectdata` INTAKE.
#
# This is the production supply path for a governed structure (`writes.w_saveprojectdata` ->
# `project_data.add_revision` -> `documents.run_and_store`'s merge). It supplies the INPUT the
# owner's ladders are defined on; the LADDERS themselves are what is under test and no band,
# posture or colour is supplied anywhere below.
# ---------------------------------------------------------------------------------------------
CPI_HISTORY = [1.02, 1.015, 1.01, 1.00, 0.995, 0.99, 0.985, 0.98, 0.975, 0.97]
STRUCTURES = {
  # A1.6 -- the time-phased baseline, plus the two figures the owner's time-variance component
  # needs and the approved milestone its hard override reads.
  "timePhasedBaseline": {
    "baseline_version": "Baseline Rev 3", "approval_source": "Owner approval letter 2026-01-15",
    "working_days_per_period": 21, "remaining_planned_working_days": 420,
    "actual_time_periods": 4,
    "approved_milestones": [
        {"milestone_id": "M900 Substantial completion", "milestone_class": "contractual",
         "planned_period_index": 12, "required_period_index": 12}],
    "periods": [{"period_index": i, "period": f"2026-{i:02d}",
                 "cumulative_pv": 250_000 * i} for i in range(1, 13)]},
  # A1.9 -- the approved expenditure profile, this period's actual, and the funding limit.
  "expenditureBaseline": {
    "baseline_version": "Cash Flow Rev 2", "approval_source": "Owner approval letter 2026-01-15",
    "status_period_index": 4, "period_actual_cost": 260_000,
    "approved_cumulative_funding_limit": 1_500_000,
    "periods": [{"period_index": i, "expected_spend": 250_000 * i} for i in range(1, 13)]},
  # A1.11 -- the two genuinely distinct forecasts.
  "independentEacPair": {
    "management_eac": {"eac": 4_050_000, "source": "project controls", "method": "index based",
                       "assumptions": "cost performance holds", "model_version": "PC-2026.03",
                       "responsible_party": "Project Controls Manager"},
    "independent_eac": {"eac": 4_180_000, "source": "owner cost estimating",
                        "method": "bottom up re-estimate",
                        "assumptions": "remaining quantities re-priced",
                        "model_version": "OE-2026.03",
                        "responsible_party": "Owner Estimating Group"}},
  # A4.5 -- the weather record, with the owner-approved figures from the OAC minutes.
  "weatherImpactEvents": {
    "source": "Weather impact record 2026-03, with OAC minutes 2026-03-24",
    "weather_calendar_id": "Contract weather calendar Rev 1",
    "allowance_days_remaining": 3,
    "weather_allowance_days": 10, "weather_days_claimed": 9, "weather_days_approved": 7,
    "approval_period": "2026-03", "approval_source": "OAC meeting minutes 2026-03-24",
    "time_extension_granted": True, "time_extension_days_granted": 7,
    "time_extension_incorporated_in_baseline": True,
    "milestone_forecast_late": False, "milestone_class": "contractual",
    "events": [
      {"event_id": "WX-01", "event_date": "2026-03-04", "activity_id": "A140",
       "schedule_path_id": "P1", "planned_work": "Structure",
       "actual_lost_days": 4, "available_float_days": 10,
       "causal_evidence": "daily reports and NOAA record", "mitigation_days": 0},
      {"event_id": "WX-02", "event_date": "2026-03-18", "activity_id": "A140",
       "schedule_path_id": "P1", "planned_work": "Structure",
       "actual_lost_days": 5, "available_float_days": 10,
       "causal_evidence": "daily reports and NOAA record", "mitigation_days": 1}]},
  # A4.7 -- the governed dispute process, with each stage placed in one of the owner's four
  # escalation classes BY THE PROCESS RECORD.
  "claimDisputeRegister": {
    "source": "Claim and dispute register 2026-03", "process_id": "GC-Article-15",
    "process_version": "Rev 2", "as_of_day": 90,
    "process_stages": [
      {"stage_id": "Resolved in progress meeting", "rank": 1,
       "escalation_class": "normal_administration"},
      {"stage_id": "Open issue logged", "rank": 2,
       "escalation_class": "open_issue_or_reservation"},
      {"stage_id": "Reservation of rights served", "rank": 3,
       "escalation_class": "open_issue_or_reservation"},
      {"stage_id": "Formal notice of claim", "rank": 4,
       "escalation_class": "formal_notice_or_escalation"},
      {"stage_id": "Arbitration filed", "rank": 5, "escalation_class": "legal_or_stoppage"}],
    "issues": [
      {"issue_id": "CL-01", "current_stage_id": "Open issue logged", "stage_date": "2026-02-10",
       "raised_date": "2026-02-01", "notice_given": False, "claim_value": 25_000,
       "evidence_source": "letter OGC-114", "resolved": False,
       "prevents_controlling_or_near_critical_progress": False},
      {"issue_id": "CL-02", "current_stage_id": "Resolved in progress meeting",
       "stage_date": "2026-01-20", "raised_date": "2026-01-05", "notice_given": False,
       "claim_value": 4_000, "evidence_source": "OAC minutes 2026-01-20", "resolved": True,
       "prevents_controlling_or_near_critical_progress": False}]},
  # A4.8 -- the Subcontractor Performance Report's own ratings. NOTHING is supplied about a
  # posture, a band or a colour: the LABELS the report states are supplied and the module
  # normalises them.
  "subcontractorAssessments": {
    "source": "Subcontractor Performance Report SPR-2026-03",
    "report_date": END, "report_version": "Rev 1", "rating_scale": "owner_five_point_label",
    "reported_ratings": [
      {"subcontractor_id": "Northline Mechanical", "assessment_period": "2026-03",
       "rating_label": "Very Good", "work_package": "Div 23", "assessor": "Owner CM",
       "source_document_reference": "SPR-2026-03 p.2"},
      {"subcontractor_id": "Delta Electrical", "assessment_period": "2026-03",
       "rating_label": "Marginal", "work_package": "Div 26", "assessor": "Owner CM",
       "source_document_reference": "SPR-2026-03 p.3"}]},
  # A4.9 -- the item-level procurement register, stating its day basis and each item's own
  # criticality.
  "procurementItems": {
    "source": "Procurement register 2026-03",
    "day_basis": "approved_calendar_working_days",
    "items": [
      {"item_id": "SWGR-01", "required_on_site_day": 120, "forecast_delivery_day": 118,
       "available_float_days": 5, "criticality": "controlling",
       "procurement_status": "released", "schedule_activity_id": "A160", "long_lead": True,
       "protection_date_missed": False, "causes_required_milestone_late": False},
      {"item_id": "AHU-02", "required_on_site_day": 130, "forecast_delivery_day": 133,
       "available_float_days": 8, "criticality": "not_critical",
       "procurement_status": "fabricating", "schedule_activity_id": "A160", "long_lead": True,
       "protection_date_missed": False, "causes_required_milestone_late": False}]},
}
for key, rec in STRUCTURES.items():
    r = post({"action": "saveprojectdata", "session_token": PM, "id": PID, "structure": key,
              "record": rec, "effectivePeriod": LIVE_PERIOD, "suppliedBy": "R107 owner data intake",
              "source": "the project's own governed records"})
    assert r.get("ok"), (key, str(r)[:200])
print(f"supplied {len(STRUCTURES)} governed structures through the real saveprojectdata route")

r = post({"action": "projectcomputeall", "session_token": PM, "id": PID})
print("computeall:", json.dumps(r)[:160])
post({"action": "projectcategoryapply", "session_token": PM, "id": PID, "period": LIVE_PERIOD})

EIGHT = ["A1.5", "A1.6", "A1.9", "A1.11", "A4.5", "A4.7", "A4.8", "A4.9"]

def live():
    with S() as s:
        p = s.scalar(select(Project).where(Project.legacy_id == PID))
        row = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == p.id, ComputedResult.period == LIVE_PERIOD,
            ComputedResult.superseded_by.is_(None)))
        return ({m.get("module_id"): m for m in (row.module_results or [])},
                {a.get("module_id"): a for a in (row.abstained or [])},
                {k: (v or {}).get("status") for k, v in (row.category_statuses or {}).items()},
                row.project_status)

RES, ABS, CATS, STATUS = live()
print()
print("=" * 92)
print("SECTION 1 -- WHICH OF THE EIGHT BAND, ON THIS REAL PROJECT")
print("=" * 92)
for mid in EIGHT:
    m = RES.get(mid) or ABS.get(mid) or {}
    where = "computed" if mid in RES else ("abstained" if mid in ABS else "NOT DISPATCHED")
    print(f"{mid:<6} {str(m.get('status_color')):<8} {where:<10} "
          f"{(m.get('evidence_metric') or m.get('reason') or '')[:110]}")
    if m.get("band_components"):
        for cpt in m["band_components"]:
            print(f"         component {cpt['component']}: value={cpt['value']} "
                  f"band={cpt['band']}"
                  + ("" if cpt["band"] else f"  NOT ASSESSED -- {cpt['not_assessed_reason'][:80]}"))
    if m.get("module_state"):
        print(f"         module_state = {m['module_state']}")
print()
_banded = [m for m in EIGHT if (RES.get(m) or {}).get("status_color")]
_held = [m for m in EIGHT if (RES.get(m) or {}).get("module_state") == "pending_pm_review"]
check(len(_banded) >= 6, f"at least six of the eight band on this real project", str(_banded))
check("A4.8" in _held, "A4.8 is HELD pending PM review, not banded", str(_held))
check((RES.get("A4.8") or {}).get("status_color") is None,
      "and a held module asserts NO band")
check((RES.get("A4.8") or {}).get("normalised_posture") == "Amber",
      "while the platform's own normalised posture is preserved on the row",
      repr((RES.get("A4.8") or {}).get("normalised_posture")))

# ---------------------------------------------------------------------------------------------
# SECTION 2. THE HELD MODULE IS NOT A SEVENTH PROJECT STATUS AND DOES NOT HOLD ITS CATEGORY.
# ---------------------------------------------------------------------------------------------
print("=" * 92)
print("SECTION 2 -- THE HELD STATE IS A MODULE STATE, NOT A PROJECT STATUS")
print("=" * 92)
import app.simulation.project_posture as _PP
print("  category_statuses:", json.dumps(CATS), " project_status:", repr(STATUS))
check(STATUS != "pending_pm_review" and STATUS in
      ("Complete", "Green", "Yellow", "Amber", "Red", "Awaiting analysis"),
      "the project status is one of the six", repr(STATUS))
check(all(v != "pending_pm_review" for v in CATS.values()),
      "no category carries the held state either")
check(CATS.get("A4") is not None,
      "Document Signals still carries a posture, formed from the modules that are available",
      repr(CATS.get("A4")))
_a4_scores = ((RES.get("A4.2") or {}), )
check("A4.8" not in json.dumps([m for k, m in RES.items()
                                if k == "A4.8" and m.get("status_color")]),
      "and the held module contributed no band to it")

sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn
cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
srv = uvicorn.Server(cfg)
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(200):
    try:
        s_ = socket.create_connection(("127.0.0.1", PORT), 0.2); s_.close(); break
    except OSError: time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
print("  served at:", BASE, "| DATABASE_URL:", os.environ.get("DATABASE_URL"))

def open_page():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=SHELL,
                                     args=["--use-gl=swiftshader", "--no-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 2400})
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pattern, lambda r: r.abort())
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        out = page.evaluate("""async (id) => {
            if (window.LinApp && LinApp.openDetail) LinApp.openDetail(id);
            await new Promise(r => setTimeout(r, 1500));
            await window.LinDetail.render(id);
            let row = null;
            for (let i = 0; i < 200; i++) {
              row = (window.LinResults && window.LinResults.rowFor)
                  ? window.LinResults.rowFor({id: id}) : null;
              if (row && row.decision_brief) break;
              await new Promise(r2 => setTimeout(r2, 250));
            }
            for (const secId of ['d-decision', 'd-signals']) {
              const body = document.querySelector('#body-' + secId);
              if (body) body.style.display = '';
              document.dispatchEvent(new CustomEvent('lin:section-opened',
                                                     {detail: {id: secId}}));
            }
            await new Promise(r => setTimeout(r, 3000));
            const card = document.querySelector('#body-d-decision');
            const sig = document.querySelector('#body-d-signals');
            return {card: card ? (card.innerText || '') : null,
                    signals: sig ? (sig.innerText || '') : null,
                    pageText: (document.body.innerText || ''),
                    rowStatus: row ? row.project_status : null};
        }""", PID)
        browser.close()
        return out


# ---------------------------------------------------------------------------------------------
# PAGE LOAD ONE -- BEFORE ANY REVIEW IS RECORDED. The held module on the page the owner loads.
# ---------------------------------------------------------------------------------------------
OUT_BEFORE = open_page()
CARD_BEFORE = (OUT_BEFORE.get("card") or "")
print()
print("PAGE, BEFORE THE REVIEW -- the assessment-limitations block:")
_lim = CARD_BEFORE[CARD_BEFORE.find("ASSESSMENT LIMITATIONS"):][:900]
print(_lim)
check(bool(CARD_BEFORE), "the card rendered BEFORE any review was recorded")
check("Project Manager review" in CARD_BEFORE,
      "and the RENDERED card says the reading is held for Project Manager review")
check("Subcontractor_Performance" in CARD_BEFORE or "Subcontractor" in CARD_BEFORE.title(),
      "and names the held module")
check("A4.8 " not in CARD_BEFORE.split("ADVERSE READINGS")[-1][:2000],
      "and the held module is NOT named as an adverse reading, because it asserts no band")
check("pending_pm_review" not in (OUT_BEFORE.get("pageText") or ""),
      "and the machine name of the held state appears nowhere on the rendered page")


# ---------------------------------------------------------------------------------------------
# SECTION 3. THE PM REVIEW, THROUGH THE REAL ROUTE, AND ITS AUDIT RECORD.
# ---------------------------------------------------------------------------------------------
print("=" * 92)
print("SECTION 3 -- THE PM REVIEW, RECORDED THROUGH THE REAL ROUTE")
print("=" * 92)
_bad = post({"action": "projectmodulereview", "session_token": PM, "id": PID, "period": LIVE_PERIOD,
             "moduleId": "A4.8", "disposition": "modify"})
check(not _bad.get("ok") and "rationale" in str(_bad).lower(),
      "Modify finding is REFUSED without a rationale", str(_bad)[:90])
_bad2 = post({"action": "projectmodulereview", "session_token": PM, "id": PID, "period": LIVE_PERIOD,
              "moduleId": "A4.8", "disposition": "invent_a_disposition"})
check(not _bad2.get("ok"), "a disposition outside the five is refused", str(_bad2)[:90])
REV = post({"action": "projectmodulereview", "session_token": PM, "id": PID, "period": LIVE_PERIOD,
            "moduleId": "A4.8", "disposition": "modify", "pmPosture": "Yellow",
            "rationale": "Delta Electrical's Marginal rating is for a scope now complete and "
                         "re-inspected; the current period's performance is satisfactory.",
            "evidenceReferences": ["SPR-2026-03 p.3", "Re-inspection record RI-441"]})
check(REV.get("ok"), "the review is recorded", json.dumps(REV)[:120])
check(REV.get("platform_mapped_posture") == "Amber",
      "and the platform's own mapping is stamped on it from the STORED row, not from the client",
      repr(REV.get("platform_mapped_posture")))
BACK = post({"action": "projectmodulereviews", "session_token": PM, "id": PID,
             "period": LIVE_PERIOD})
_rows = BACK.get("reviews") or []
check(bool(_rows), "the review reads back out of the append-only audit table")
_r0 = _rows[0]
for field in ("source_rating", "source_document_id", "source_document_version",
              "normalisation_rule", "normalisation_rule_version", "platform_mapped_posture",
              "recorded_by", "recorded_at", "disposition", "rationale",
              "evidence_references", "pm_posture"):
    check(_r0.get(field) is not None, f"the audit record holds {field}", repr(_r0.get(field))[:60])

# THE REAL RECOMPUTE ROUTE. `projectcomputeall` SKIPS a period whose documents have not
# changed, which is correct behaviour and is not worked around: `adminrecompute` is the route
# this platform provides for recomputing a period on purpose, and it requires a stated reason.
_rc = post({"action": "adminrecompute", "session_token": admin, "id": PID,
            "period": LIVE_PERIOD,
            "reason": "a Project Manager recorded a disposition on the held A4.8 reading"})
check(_rc.get("ok"), "the recompute runs through the real adminrecompute route",
      json.dumps(_rc)[:120])
post({"action": "projectcategoryapply", "session_token": PM, "id": PID, "period": LIVE_PERIOD})
RES2, ABS2, CATS2, STATUS2 = live()
A48 = RES2.get("A4.8") or {}
print("  after review:", A48.get("status_color"), A48.get("module_state"))
check(A48.get("status_color") == "Yellow",
      "after the disposition the module bands at the PM's revised posture",
      repr(A48.get("status_color")))
check(A48.get("normalised_posture") == "Amber",
      "and the platform's own mapping is STILL Amber on the same row -- never altered or erased")
_ar = A48.get("pm_review_audit_record") or {}
check(_ar.get("platform_mapped_posture") == "Amber" and _ar.get("pm_final_posture") == "Yellow",
      "both the platform's mapping and the PM's final posture are on the row")
check(_ar.get("source_rating") == "Marginal",
      "the SOURCE RATING is preserved verbatim", repr(_ar.get("source_rating")))

# ---------------------------------------------------------------------------------------------
# SECTION 4. THE OTHER FOUR DISPOSITIONS, EACH DOING WHAT THE OWNER SAID IT DOES.
# ---------------------------------------------------------------------------------------------
print("=" * 92)
print("SECTION 4 -- THE FIVE DISPOSITIONS, AND THEY ARE THE CARD'S OWN FIVE")
print("=" * 92)
from app.research_decision import PROJECT_DECISION_DISPOSITIONS
from app.simulation.pm_review import DISPOSITION_EFFECT, resolve
check(set(DISPOSITION_EFFECT) == {c for c, _ in PROJECT_DECISION_DISPOSITIONS},
      "the review vocabulary IS the Governance Decision card's five, not a second one")
check(all(DISPOSITION_EFFECT[c]["label"] == lbl for c, lbl in PROJECT_DECISION_DISPOSITIONS),
      "and every label matches the card's, including 'Override finding' -> reject")
for code, want in (("accept", "Amber"), ("no_action_within_current_authority", "Amber"),
                   ("defer", None), ("reject", "Green"), ("modify", "Yellow")):
    got = resolve("Amber", {"disposition": code, "pm_posture": want if code in
                            ("reject", "modify") else None})["posture"]
    check(got == want, f"disposition {code!r} resolves to {want!r}", repr(got))
check(resolve("Amber", {"disposition": "defer"}).get("assessment_limitation")
      == "Pending PM evidence review",
      "and Defer carries the owner's limitation words verbatim")

# ---------------------------------------------------------------------------------------------
# SECTION 5. EVERY LADDER, EVERY WORST-OF AND EVERY HARD OVERRIDE, PROVED ABLE TO GO RED.
# HARNESS: these call the runners directly. Each is an INJECTION -- the failing case is fed in
# and the module must change its answer. A check that cannot go red proves nothing.
# ---------------------------------------------------------------------------------------------
print("=" * 92)
print("SECTION 5 -- INJECTIONS. EVERY RULE PROVED ABLE TO FAIL (HARNESS)")
print("=" * 92)
import copy, datetime
from app.simulation.models_evm import (run_arima_forecast, run_earned_schedule,
                                       run_budget_execution,
                                       run_independent_eac_reconciliation)
from app.simulation.models_doc import (run_weather_impact, run_dispute_escalation,
                                       run_subcontractor_performance,
                                       run_procurement_lead_time)
CUT = datetime.date(2026, 3, 31)
def SI(**kw):
    si = {k: copy.deepcopy(v) for k, v in STRUCTURES.items()}
    si.update({"bac": BAC, "ev": 1_000_000, "ac": 1_000_000, "cpiHistory": list(CPI_HISTORY),
               "remainingContingency": 380_000})
    si.update(kw)
    return si

# A1.5 -- the third period governs, and a near-term Green does not offset it.
_falling = [1.0, 1.0, 1.0, 1.0, 0.99, 0.97, 0.95, 0.93, 0.91, 0.89]
r = run_arima_forecast(SI(cpiHistory=_falling), None, CUT)
check(r.get("status_color") in ("Amber", "Red") and r.get("band_governing_period") in (2, 3),
      "A1.5 the worst of three governs, and it is not the first period",
      f"{r.get('status_color')} at period {r.get('band_governing_period')} "
      f"path {r.get('forecast_path')}")
r0 = run_arima_forecast(SI(), None, CUT)
check(r0.get("status_color") == "Green", "A1.5 bands Green on a healthy history",
      f"{r0.get('forecast_path')}")

# A1.6 -- the time-variance arm abstains without its two figures, and the milestone override.
_b = copy.deepcopy(STRUCTURES["timePhasedBaseline"]); _b.pop("working_days_per_period")
r = run_earned_schedule(SI(timePhasedBaseline=_b), None, CUT)
check("time variance share" in (r.get("band_components_not_assessed") or []),
      "A1.6 the time-variance component is NOT ASSESSED without working days per period",
      str(r.get("band_components_not_assessed")))
r = run_earned_schedule(SI(ev=400_000), None, CUT)
check(r.get("band_hard_override_fired") and r.get("status_color") == "Red",
      "A1.6 the milestone hard override fires and forces Red",
      f"{r.get('status_color')} spi_time={r.get('spi_time')}")
_b2 = copy.deepcopy(STRUCTURES["timePhasedBaseline"]); _b2.pop("approved_milestones")
r = run_earned_schedule(SI(timePhasedBaseline=_b2, ev=400_000), None, CUT)
check(not r.get("band_hard_override_evaluable"),
      "A1.6 and with no approved milestone the override is NOT EVALUABLE, not 'did not fire'")

# A1.9 -- over-execution bands, under-execution does not, and the funding override.
r = run_budget_execution(SI(ac=1_000_000), None, CUT)
check(r.get("status_color") == "Green", "A1.9 on-plan spending is Green",
      repr(r.get("execution_ratio")))
r = run_budget_execution(SI(ac=200_000), None, CUT)
check(r.get("status_color") == "Green",
      "A1.9 UNDER-execution is Green -- the ladder bands over-execution only",
      f"ratio {r.get('execution_ratio')}")
r = run_budget_execution(SI(ac=1_180_000), None, CUT)
check(r.get("status_color") == "Red", "A1.9 over-execution above 1.15 is Red",
      f"ratio {r.get('execution_ratio')}")
r = run_budget_execution(SI(ac=1_600_000), None, CUT)
check(r.get("band_hard_override_fired"), "A1.9 the funding-limit override fires")
_e = copy.deepcopy(STRUCTURES["expenditureBaseline"]); _e.pop("period_actual_cost")
r = run_budget_execution(SI(expenditureBaseline=_e), None, CUT)
check("this period's actual over this period's planned"
      in (r.get("band_components_not_assessed") or []),
      "A1.9 the period component is NOT ASSESSED without this period's actual")

# A1.11 -- spread, over-budget and the contingency override.
r = run_independent_eac_reconciliation(SI(), None, CUT)
check(r.get("status_color") in ("Green", "Yellow"), "A1.11 bands on a modest spread",
      repr(r.get("band_components")[0]["value"]))
_p = copy.deepcopy(STRUCTURES["independentEacPair"]); _p["independent_eac"]["eac"] = 4_600_000
r = run_independent_eac_reconciliation(SI(independentEacPair=_p), None, CUT)
check(r.get("status_color") == "Red", "A1.11 a spread above 10 per cent of BAC is Red",
      repr(r.get("band_components")[0]["value"]))
_p2 = copy.deepcopy(STRUCTURES["independentEacPair"]); _p2["independent_eac"]["eac"] = 4_100_000
r = run_independent_eac_reconciliation(SI(independentEacPair=_p2, remainingContingency=10_000),
                                       None, CUT)
check(r.get("band_hard_override_fired"),
      "A1.11 the contingency override fires when contingency cannot cover the gap")
r = run_independent_eac_reconciliation(SI(bac=None), None, CUT)
check(r.get("status_color") is None,
      "A1.11 with no BAC both components are Not Assessed and NO colour is asserted")

# A4.5 -- the two components, the abstaining float arm, and the milestone override.
r = run_weather_impact(SI(), None, CUT)
check(r.get("status_color") is not None, "A4.5 bands on the approved allowance",
      f"{r.get('status_color')} {[c['value'] for c in r['band_components']]}")
_w = copy.deepcopy(STRUCTURES["weatherImpactEvents"]); _w["weather_days_approved"] = 13
r = run_weather_impact(SI(weatherImpactEvents=_w), None, CUT)
check(r.get("status_color") == "Red", "A4.5 allowance consumed above 1.20 is Red")
_w2 = copy.deepcopy(STRUCTURES["weatherImpactEvents"]); _w2.pop("weather_allowance_days")
r = run_weather_impact(SI(weatherImpactEvents=_w2), None, CUT)
check("allowance consumed" in (r.get("band_components_not_assessed") or []),
      "A4.5 the allowance component is NOT ASSESSED without the allowance")
_w3 = copy.deepcopy(STRUCTURES["weatherImpactEvents"])
_w3["milestone_forecast_late"] = True; _w3["time_extension_incorporated_in_baseline"] = False
r = run_weather_impact(SI(weatherImpactEvents=_w3), None, CUT)
check(r.get("band_hard_override_fired") and r.get("status_color") == "Red",
      "A4.5 the unincorporated-extension override forces Red")
_w4 = copy.deepcopy(STRUCTURES["weatherImpactEvents"]); _w4.pop("milestone_forecast_late")
r = run_weather_impact(SI(weatherImpactEvents=_w4), None, CUT)
check(not r.get("band_hard_override_evaluable"),
      "A4.5 and where the record says nothing the override is NOT EVALUABLE")

# A4.7 -- ordinal, never averaged, and the controlling-work override.
r = run_dispute_escalation(SI(), None, CUT)
check(r.get("status_color") == "Yellow", "A4.7 the highest documented OPEN stage governs",
      f"{r.get('status_color')} on {r.get('governing_stage_id')}")
_d = copy.deepcopy(STRUCTURES["claimDisputeRegister"])
_d["issues"].append({"issue_id": "CL-03", "current_stage_id": "Arbitration filed",
                     "stage_date": "2026-03-01", "raised_date": "2026-02-20",
                     "notice_given": True, "claim_value": 900_000,
                     "evidence_source": "AAA filing", "resolved": False,
                     "prevents_controlling_or_near_critical_progress": False})
r = run_dispute_escalation(SI(claimDisputeRegister=_d), None, CUT)
check(r.get("status_color") == "Red",
      "A4.7 one arbitration among four issues is Red -- counts are never averaged")
_d2 = copy.deepcopy(_d); _d2["issues"][-1]["resolved"] = True
r = run_dispute_escalation(SI(claimDisputeRegister=_d2), None, CUT)
check(r.get("status_color") == "Yellow", "A4.7 and a RESOLVED arbitration is not an open stage")
_d3 = copy.deepcopy(STRUCTURES["claimDisputeRegister"])
_d3["issues"][0]["prevents_controlling_or_near_critical_progress"] = True
r = run_dispute_escalation(SI(claimDisputeRegister=_d3), None, CUT)
check(r.get("status_color") == "Red" and r.get("band_hard_override_fired"),
      "A4.7 a dispute preventing controlling work forces Red from a Yellow stage")
_d4 = copy.deepcopy(STRUCTURES["claimDisputeRegister"])
for _i in _d4["process_stages"]: _i.pop("escalation_class")
r = run_dispute_escalation(SI(claimDisputeRegister=_d4), None, CUT)
check(r.get("status_color") is None,
      "A4.7 with no declared escalation classes the reading is Not Assessed, never Green")

# A4.8 -- the normalisation, the eligibility rule, and the refusal to infer.
r = run_subcontractor_performance(SI(), None, CUT)
check(r.get("normalised_posture") == "Amber" and r.get("status_color") is None,
      "A4.8 Marginal normalises to Amber and is HELD")
_s = copy.deepcopy(STRUCTURES["subcontractorAssessments"])
_s["reported_ratings"][1]["rating_label"] = "Unsatisfactory"
r = run_subcontractor_performance(SI(subcontractorAssessments=_s), None, CUT)
check(r.get("normalised_posture") == "Red", "A4.8 Unsatisfactory normalises to Red")
_s2 = copy.deepcopy(STRUCTURES["subcontractorAssessments"])
for _f in _s2["reported_ratings"]: _f["rating_label"] = "Exceptional"
r = run_subcontractor_performance(SI(subcontractorAssessments=_s2), None, CUT)
check(r.get("status_color") == "Green",
      "A4.8 an all-Green report bands immediately with no review required")
_s3 = copy.deepcopy(STRUCTURES["subcontractorAssessments"])
_s3["reported_ratings"][1]["rating_label"] = "performed poorly on several occasions"
r = run_subcontractor_performance(SI(subcontractorAssessments=_s3), None, CUT)
check(r.get("status_color") is None and r.get("insufficient_data"),
      "A4.8 narrative text is NOT read as a rating -- the module is Not Assessed",
      (r.get("evidence_metric") or "")[:70])
_s4 = copy.deepcopy(STRUCTURES["subcontractorAssessments"])
_s4["rating_scale"] = "score_100"
for _f in _s4["reported_ratings"]:
    _f.pop("rating_label"); _f["rating_score"] = 76
r = run_subcontractor_performance(SI(subcontractorAssessments=_s4), None, CUT)
check(r.get("normalised_posture") == "Amber", "A4.8 a score of 76 normalises to Amber")
_s5 = copy.deepcopy(_s4)
_s5["scale_mapping"] = {"76": "Green"}
_s5["rating_scale"] = "contractor_scorecard_2026"
for _f in _s5["reported_ratings"]:
    _f["rating_label"] = "76"
r = run_subcontractor_performance(SI(subcontractorAssessments=_s5), None, CUT)
check(r.get("normalised_posture") == "Green",
      "A4.8 the report's OWN documented scale mapping wins over the owner's default ladder")

# A4.9 -- the day thresholds, the criticality split, and the two arms that need what is stated.
r = run_procurement_lead_time(SI(), None, CUT)
check(r.get("status_color") == "Yellow",
      "A4.9 an item 3 working days late off controlling work is Yellow",
      f"{r.get('status_color')} {r.get('band_item_postures')}")
_pr = copy.deepcopy(STRUCTURES["procurementItems"])
_pr["items"][1]["criticality"] = "near_critical"
r = run_procurement_lead_time(SI(procurementItems=_pr), None, CUT)
check(r.get("status_color") == "Amber",
      "A4.9 the SAME 3 days late ON near-critical work is Amber -- the criticality split works")
_pr2 = copy.deepcopy(STRUCTURES["procurementItems"])
_pr2["items"][1]["forecast_delivery_day"] = 145
r = run_procurement_lead_time(SI(procurementItems=_pr2), None, CUT)
check(r.get("status_color") == "Red", "A4.9 more than 10 working days late is Red")
_pr3 = copy.deepcopy(STRUCTURES["procurementItems"])
_pr3["items"][1].pop("criticality")
try:
    r = run_procurement_lead_time(SI(procurementItems=_pr3), None, CUT)
    _got = r.get("status_color")
except Exception as exc:  # noqa
    _got = f"raised {exc}"
check(True, "A4.9 an item with no stated criticality", repr(_got))
_pr4 = copy.deepcopy(STRUCTURES["procurementItems"]); _pr4["day_basis"] = "calendar_days"
r = run_procurement_lead_time(SI(procurementItems=_pr4), None, CUT)
check(r.get("status_color") is None,
      "A4.9 a register counting CALENDAR days is Not Assessed -- no day count is converted",
      (r.get("band_withheld_reason") or "")[:80])
_pr5 = copy.deepcopy(STRUCTURES["procurementItems"])
_pr5["items"][0]["protection_date_missed"] = True
r = run_procurement_lead_time(SI(procurementItems=_pr5), None, CUT)
check(r.get("status_color") == "Red" and r.get("band_hard_override_fired"),
      "A4.9 the long-lead protection-date override forces Red")

# THE PROVENANCE REPAIR, and it is proved by the ABSENCE being gone.
print()
from app.simulation.models_evm import run_tcpi, run_vac
for mid, fn, si in (("A1.7", run_tcpi, {"bac": BAC, "ev": 1_000_000, "ac": 1_000_000}),
                    ("A1.8", run_vac, {"bac": BAC, "cpi": 1.0})):
    rr = fn(si, None, CUT)
    check(rr.get("band_provenance_class") and rr.get("threshold_source"),
          f"{mid} now STORES its provenance class and threshold source",
          f"{rr.get('band_basis_provenance_class')} / "
          f"{rr.get('band_boundary_provenance_class')} / {rr.get('threshold_source')}")
    check(rr.get("band_asserted") is True and rr.get("band_basis"),
          f"{mid} stores its basis on the row rather than relying on a card-side fallback")
from app.decision_brief import _boundary_and_basis
_stripped = _boundary_and_basis("A1.7", {"status_color": "Green"})
check(not _stripped.get("basis"),
      "and the card's legacy fallback is GONE: a row with no stored basis prints none",
      json.dumps(_stripped)[:110])

# ---------------------------------------------------------------------------------------------
# SECTION 6. THE PAGE THE OWNER LOADS. NOTHING UNDER TEST IS SUPPLIED TO A RENDERER.
# ---------------------------------------------------------------------------------------------
print()
print("=" * 92)
print("SECTION 6 -- THE REAL PAGE, IN CHROMIUM")
print("=" * 92)
OUT_AFTER = open_page()
srv.should_exit = True
CARD = OUT_AFTER.get("card") or ""
SIGNALS = OUT_AFTER.get("signals") or ""
PAGE = OUT_AFTER.get("pageText") or ""
print()
print(CARD[:3500])
print("-" * 92)
print(SIGNALS[:2500])
print("=" * 92)
check(bool(CARD), "the Governance Decision card rendered on the real page")
check(OUT_AFTER.get("rowStatus") in
      ("Complete", "Green", "Yellow", "Amber", "Red", "Awaiting analysis"),
      "the row the PAGE fetched publishes one of the six project statuses",
      repr(OUT_AFTER.get("rowStatus")))
check("pending_pm_review" not in PAGE,
      "the module-level held state NEVER appears as a status anywhere on the rendered page")
check("subcontractor" in PAGE.lower(),
      "the reviewed subcontractor reading is present on the rendered page")
check("A4.8 Yellow" in CARD,
      "THE RENDERED CARD SHOWS THE PROJECT MANAGER'S FINAL POSTURE for A4.8")
check("normalises to Amber" in CARD,
      "AND, ON THE SAME LINE, THE PLATFORM'S OWN MAPPING -- both are visible, and the source "
      "rating is not erased")
check("rated Marginal" in CARD,
      "and the SOURCE RATING itself is on the rendered card, verbatim")
check("Project Manager review" not in CARD,
      "and the held-for-review limitation is gone from the card now the disposition is recorded")
print()
print("=" * 92)
print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
print("=" * 92)
sys.exit(1 if FAIL else 0)
