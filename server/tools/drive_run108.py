"""
RUN 108. THE WORKING CALENDAR, ON THE PAGE THE OWNER LOADS, AND ON A PROJECT THAT HAS NONE.

WHAT IS REAL AND WHAT IS HARNESS, STATED BEFORE ANYTHING IS MEASURED.

  REAL ROUTE. TWO projects are built end to end through the REAL upload route, the REAL
  extraction contract, the REAL `saveprojectdata` intake and the REAL compute route, and read
  back through the REAL `projectresults` route. Project A's schedule update DEFINES ITS
  CALENDARS; project B's schedule update is identical except that it defines none. Section 4
  serves the REAL application and opens project A's REAL detail page in Chromium. NOTHING UNDER
  TEST IS SUPPLIED TO A RENDERER: no reading is composed here, none is injected, and
  `window.LinResults.rowFor` is NOT substituted -- it is only READ, to wait for the row the page
  itself fetched.

  THE CALENDAR IS NEVER HANDED TO A MODULE. It is stated by a document, extracted by the real
  contract, assembled by `documents.py` and read by the modules from the signal inputs. No
  `projectCalendar` is supplied through `saveprojectdata` anywhere in this file.

  HARNESS. Section 3 calls the module runners directly to prove each rule ABLE TO GO THE OTHER
  WAY -- that is what an injection is for -- and says so where it does.

  NO MODEL CALL IS SIMULATED. There is no ANTHROPIC_API_KEY here; extraction runs through
  `StubExtractor`. The extraction-contract text this run added -- `schedule_calendar_json` and
  `schedule_baseline_finish_date` -- is UNEXERCISED AGAINST A REAL MODEL and is reported as such.
"""
import base64, copy, hashlib, json, logging, os, pathlib, socket, sys, threading, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant

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

STAMP = str(int(time.time())); ADMIN = "r108-" + STAMP
PID_A = "PRJ-R108A-" + STAMP     # states its calendars
PID_B = "PRJ-R108B-" + STAMP     # states none
END = "2026-03-31"; BAC = 4_000_000; PERIOD = 1

# =============================================================================================
# THE DOCUMENTS. Read out of Run 103's own census set so the fixture cannot drift from the
# corpus, with the schedule update GROWN by this run's contract for project A only.
# =============================================================================================
_src = (HERE / "drive_run103_census.py").read_text()
_docs_src = _src[_src.index("DOCS = ["):_src.index("]\ndef raw(")+1]
_ns = {"BAC": BAC, "END": END}
exec(_docs_src, _ns)
BASE_DOCS = list(_ns["DOCS"])

# THE CALENDAR DEFINITIONS, PRINTED AS A SCHEDULE EXPORT PRINTS THEM. Two calendars, and
# NEITHER IS A FIVE-DAY MONDAY-TO-FRIDAY WEEK, because a fixture that happened to match the
# thing the platform must never assume would prove nothing. The project works a SIX-DAY week
# (Monday to Saturday) on its default calendar, and its holidays are its own.
CALENDARS = [
    {"calendar_id": "Contract calendar Rev 1",
     "working_days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday",
                              "saturday"],
     "holidays": ["2026-01-01", "2026-05-25", "2026-07-03", "2026-09-07", "2026-11-26",
                  "2026-12-25"]},
    {"calendar_id": "Contract weather calendar Rev 1",
     "working_days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
     "holidays": ["2026-01-01", "2026-12-25"]},
]

def docs_for(with_calendar: bool):
    out = []
    for t, ty, ex in BASE_DOCS:
        ex = dict(ex)
        if t == "sched":
            if with_calendar:
                ex["schedule_calendar"] = "Contract calendar Rev 1"
                ex["schedule_calendars_json"] = [c["calendar_id"] for c in CALENDARS]
                ex["schedule_calendar_json"] = copy.deepcopy(CALENDARS)
                ex["schedule_baseline_finish_date"] = "2027-06-30"
            else:
                # THE PROJECT WITH NO STATED CALENDAR. It still NAMES one -- which is exactly
                # the state the platform was in before this run -- and defines none.
                ex["schedule_calendar"] = "5-day work week"
                ex["schedule_calendars_json"] = ["5-day work week"]
                ex.pop("schedule_calendar_json", None)
                ex["schedule_baseline_finish_date"] = "2027-06-30"
        out.append((t, ty, ex))
    return out

# =============================================================================================
# THE GOVERNED STRUCTURES. The three arms' own inputs, and NOT ONE working-day figure among
# them: every working day in this run is COUNTED BY THE PLATFORM on the project's own calendar.
# =============================================================================================
STRUCTURES = {
  # A1.6. Note what is NOT here: `working_days_per_period` and `remaining_planned_working_days`,
  # which Run 107 read off this structure and which no document ever stated. They are counted.
  "timePhasedBaseline": {
    "baseline_version": "Baseline Rev 3", "approval_source": "Owner approval letter 2026-01-15",
    "actual_time_periods": 4,
    "approved_milestones": [
        {"milestone_id": "M900 Substantial completion", "milestone_class": "contractual",
         "planned_period_index": 12, "required_period_index": 12}],
    "periods": [{"period_index": i, "period": f"2026-{i:02d}",
                 "cumulative_pv": 250_000 * i} for i in range(1, 13)]},
  # A4.5. THE RECORD STATES ITS DAY BASIS -- calendar days -- and each event's span. Run 107
  # divided a delay of unstated basis by working-day float.
  "weatherImpactEvents": {
    "source": "Weather impact record 2026-03, with OAC minutes 2026-03-24",
    "weather_calendar_id": "Contract weather calendar Rev 1",
    "day_basis": "calendar_days",
    "allowance_days_remaining": 1,
    "weather_allowance_days": 10, "weather_days_claimed": 9, "weather_days_approved": 7,
    "approval_period": "2026-03", "approval_source": "OAC meeting minutes 2026-03-24",
    "time_extension_granted": True, "time_extension_days_granted": 7,
    "time_extension_incorporated_in_baseline": True,
    "milestone_forecast_late": False, "milestone_class": "contractual",
    "events": [
      {"event_id": "WX-01", "event_date": "2026-03-02", "event_start_date": "2026-03-02",
       "event_end_date": "2026-03-08", "activity_id": "A140",
       "schedule_path_id": "P1", "planned_work": "Structure",
       "actual_lost_days": 7, "available_float_days": 4,
       "causal_evidence": "daily reports and NOAA record", "mitigation_days": 0}]},
  # A4.9. THE REGISTER COUNTS CALENDAR DAYS AND PRINTS CALENDAR DATES. Run 107 left exactly
  # this register Not Assessed because no calendar reached the module.
  "procurementItems": {
    "source": "Procurement register 2026-03",
    "day_basis": "calendar_days",
    "items": [
      {"item_id": "SWGR-01", "required_on_site_date": "2026-05-04",
       "forecast_delivery_date": "2026-05-02",
       "available_float_days": 5, "criticality": "controlling",
       "procurement_status": "released", "schedule_activity_id": "A160", "long_lead": True,
       "protection_date_missed": False, "causes_required_milestone_late": False},
      {"item_id": "AHU-02", "required_on_site_date": "2026-05-18",
       "forecast_delivery_date": "2026-05-27",
       "available_float_days": 8, "criticality": "not_critical",
       "procurement_status": "fabricating", "schedule_activity_id": "A160", "long_lead": True,
       "protection_date_missed": False, "causes_required_milestone_late": False}]},
}

with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R108-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    for pid, nm in ((PID_A, "Run 108 fixture, calendar stated"),
                    (PID_B, "Run 108 fixture, no calendar stated")):
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": nm, "sector": "construction",
                                              "signals": {}, "events": []}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
c = post({"action": "adminparticipantcreate", "session_token": admin,
          "pseudonymous_code": "R108-PM-" + STAMP, "role": "Participant",
          "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
PM_ID = c["participant_id"]
for pid in (PID_A, PID_B):
    post({"action": "adminmemberadd", "session_token": admin, "id": pid,
          "participant_id": PM_ID, "project_role": "PM"})

print("=" * 92)
print("SECTION 1 -- TWO PROJECTS, THROUGH THE REAL ROUTES")
print("=" * 92)

def build(pid, with_calendar):
    docs = docs_for(with_calendar)
    def raw(t): return f"%PDF-1.4 R108 {STAMP} {pid} {t}\n".encode()
    set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest(): (ty, ex)
                                          for t, ty, ex in docs}))
    for t, ty, _ex in docs:
        r = post({"action": "projectupload", "session_token": PM, "id": pid,
                  "period": PERIOD, "period_end": END,
                  "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                                 "dataBase64": b64(raw(t))}]})
        assert r.get("ok"), (t, str(r)[:200])
    for key, rec in STRUCTURES.items():
        r = post({"action": "saveprojectdata", "session_token": PM, "id": pid, "structure": key,
                  "record": rec, "effectivePeriod": PERIOD,
                  "suppliedBy": "R108 owner data intake",
                  "source": "the project's own governed records"})
        assert r.get("ok"), (key, str(r)[:200])
    r = post({"action": "projectcomputeall", "session_token": PM, "id": pid})
    assert r.get("ok"), str(r)[:300]
    post({"action": "projectcategoryapply", "session_token": PM, "id": pid, "period": PERIOD})
    # READ BACK THE ROW THE REAL COMPUTE ROUTE WROTE. Nothing is recomputed here and nothing is
    # supplied: this is the stored result, read as the results route reads it.
    from app.research_models import ComputedResult
    with S() as s:
        p = s.scalar(select(Project).where(Project.legacy_id == pid))
        row = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == p.id, ComputedResult.period == PERIOD,
            ComputedResult.superseded_by.is_(None)))
        out = {m.get("module_id"): m for m in (row.module_results or [])}
        out.update({a.get("module_id"): a for a in (row.abstained or [])
                    if a.get("module_id") not in out})
        return out, row.project_status

MA, STATUS_A = build(PID_A, True)
MB, STATUS_B = build(PID_B, False)
print(f"project A: {len(MA)} module rows, status {STATUS_A!r}   "
      f"project B: {len(MB)} module rows, status {STATUS_B!r}")

# =============================================================================================
# SECTION 2. WHAT THE THREE ARMS PRODUCE ON A REAL PROJECT, THROUGH THE REAL ROUTES.
# =============================================================================================
print()
print("=" * 92)
print("SECTION 2 -- THE THREE ARMS, ON THE STORED ROWS THE REAL COMPUTE ROUTE WROTE")
print("=" * 92)
A16, A45, A49 = MA.get("A1.6") or {}, MA.get("A4.5") or {}, MA.get("A4.9") or {}
B16, B45, B49 = MB.get("A1.6") or {}, MB.get("A4.5") or {}, MB.get("A4.9") or {}

print("A1.6:", json.dumps({k: A16.get(k) for k in (
    "status_color", "working_calendar_id", "working_calendar_days_per_week",
    "working_calendar_holiday_count", "working_days_per_period",
    "remaining_planned_working_days", "spi_time", "schedule_variance_time")}, default=str))
check(A16.get("working_calendar_id") == "Contract calendar Rev 1",
      "A1.6 READ THE PROJECT'S OWN CALENDAR, by the name the schedule update printed",
      repr(A16.get("working_calendar_id")))
check(A16.get("working_calendar_days_per_week") == 6,
      "and it counted a SIX-day working week, which is what the document defined and is not a "
      "five-day week assumed by the platform",
      repr(A16.get("working_calendar_days_per_week")))
check((A16.get("working_days_per_period") or 0) > 0
      and (A16.get("remaining_planned_working_days") or 0) > 0,
      "A1.6's time-variance component now HAS BOTH FIGURES: working days per period and the "
      "remaining planned working duration, both COUNTED on that calendar",
      f"{A16.get('working_days_per_period')} per period, "
      f"{A16.get('remaining_planned_working_days')} remaining")
_tv = [c for c in (A16.get("band_components") or []) if "time variance" in str(c.get("component"))]
check(bool(_tv) and _tv[0].get("band"),
      "and the component the owner's ladder is defined on is FORMED rather than Not Assessed",
      json.dumps(_tv[0] if _tv else None, default=str)[:160])

print()
print("A4.9:", json.dumps({k: A49.get(k) for k in (
    "status_color", "day_basis", "day_basis_converted_on_calendar", "working_calendar_id",
    "converted_item_slacks", "band_governing_item_id")}, default=str))
check(A49.get("day_basis") == "calendar_days" and A49.get("day_basis_converted_on_calendar"),
      "A4.9's register counts CALENDAR days and the platform CONVERTED it on the project's own "
      "calendar -- Run 107 left exactly this register Not Assessed")
check(A49.get("status_color") in ("Green", "Yellow", "Amber", "Red"),
      "and A4.9 now bands on a real project", repr(A49.get("status_color")))
_conv = {c["item_id"]: c for c in (A49.get("converted_item_slacks") or [])}
check(_conv.get("AHU-02", {}).get("calendar_day_slack") == -9
      and _conv.get("AHU-02", {}).get("working_day_slack") == -7,
      "AND THE CONVERSION IS ARITHMETIC, not a relabelling: 2026-05-18 to 2026-05-27 is 9 "
      "calendar days and 7 working days on this project's six-day calendar, because Sunday 24 "
      "May is not worked and 25 May is one of the holidays the document defined",
      json.dumps(_conv.get("AHU-02"), default=str))

print()
print("A4.5:", json.dumps({k: A45.get(k) for k in (
    "status_color", "weather_day_basis", "weather_working_day_recount",
    "direct_path_effect_days", "weather_delay_days_used_in_float_share")}, default=str))
check(A45.get("weather_day_basis") == "calendar_days",
      "A4.5's record STATES its day basis, which no record did before this run")
check((A45.get("weather_working_day_recount") or {}).get("working_days_lost") == 5
      and (A45.get("weather_working_day_recount") or {}).get("calendar_days_lost") == 7,
      "and the seven CALENDAR days lost from 2026-03-02 to 2026-03-08 are recounted as FIVE "
      "WORKING days on the weather calendar the record names -- a five-day week, which is a "
      "DIFFERENT calendar from the project's six-day default, and the module used the one the "
      "record named",
      json.dumps(A45.get("weather_working_day_recount"), default=str))
check(A45.get("weather_delay_days_used_in_float_share")
      != A45.get("direct_path_effect_days"),
      "so the delay divided by working-day float is NOT the calendar-day figure any more",
      f"{A45.get('direct_path_effect_days')} calendar -> "
      f"{A45.get('weather_delay_days_used_in_float_share')} working")

# =============================================================================================
# SECTION 3. THE PROJECT WITH NO STATED CALENDAR. THIS IS THE CHECK THAT PROVES NOTHING
# QUIETLY DEFAULTED TO A FIVE-DAY WEEK.
# =============================================================================================
print()
print("=" * 92)
print("SECTION 3 -- A PROJECT WHOSE DOCUMENTS STATE NO CALENDAR")
print("=" * 92)
check(B16.get("working_calendar_id") is None
      and B16.get("working_calendar_days_per_week") is None,
      "A1.6 reads NO calendar on project B, whose schedule update NAMES '5-day work week' and "
      "DEFINES nothing", repr(B16.get("working_calendar_id")))
check(B16.get("working_days_per_period") is None
      and B16.get("remaining_planned_working_days") is None,
      "and it counts NO working days -- no five-day week, no weekend, no holiday set")
_btv = [c for c in (B16.get("band_components") or []) if "time variance" in str(c.get("component"))]
_breason = (_btv[0].get("not_assessed_reason") if _btv else "") or ""
print("A1.6 SAYS: " + _breason[:420])
check("WHAT IS NEEDED" in _breason and "working days of the week" in _breason
      and "holiday" in _breason,
      "AND IT SAYS WHAT IT NEEDS: the working days of the week and the holiday set")
check("A calendar NAME alone is not a calendar" in _breason,
      "and it says in terms that the name it does hold is not a calendar")
_b49 = [i for i in (B49.get("band_item_postures") or []) if i.get("not_assessed_reason")]
print("A4.9 SAYS: " + ((_b49[0].get("not_assessed_reason") if _b49 else ""))[:340])
check(B49.get("status_color") is None and bool(_b49),
      "A4.9 ABSTAINS on project B rather than converting calendar days by a guess",
      repr(B49.get("status_color")))
_b45 = [c for c in (B45.get("band_components") or [])
        if "float" in str(c.get("component")) and c.get("not_assessed_reason")]
print("A4.5 SAYS: " + ((_b45[0].get("not_assessed_reason") if _b45 else ""))[:340])
check(bool(_b45),
      "A4.5's float-consumed component is Not Assessed on project B rather than dividing "
      "calendar days by working-day float")

# =============================================================================================
# SECTION 4. INJECTIONS. EVERY RULE ABOVE PROVED ABLE TO GO RED. HARNESS, and said to be.
# =============================================================================================
print()
print("=" * 92)
print("SECTION 4 -- INJECTIONS (HARNESS: the runners are called directly)")
print("=" * 92)
from app.simulation.models_doc import run_procurement_lead_time, run_weather_impact
from app.simulation.models_evm import run_earned_schedule
from app.simulation import working_calendar as WC
CUT = None
SI_A = {"projectCalendar": {"calendars": copy.deepcopy(CALENDARS),
                            "default_calendar_id": "Contract calendar Rev 1"},
        "scheduleReferenceDates": {"data_date": END, "baseline_finish_date": "2027-06-30"},
        "ev": 1_000_000, "bac": BAC}
def si(**kw):
    out = dict(SI_A); out.update(copy.deepcopy(STRUCTURES)); out.update(kw); return out

# THE CALENDAR ITSELF, PROVED ABLE TO GIVE A DIFFERENT ANSWER.
_six = WC.normalise_calendar(CALENDARS[0]); _five = WC.normalise_calendar(CALENDARS[1])
from datetime import date as _d
_a, _b = _d(2026, 5, 18).toordinal(), _d(2026, 6, 1).toordinal()
check(WC.working_days_between(_six, _a, _b) == 11
      and WC.working_days_between(_five, _a, _b) == 10,
      "INJECTION: the SAME two dates give 11 working days on the six-day calendar and 10 on the "
      "five-day one, so the conversion is reading the calendar and not a constant",
      f"{WC.working_days_between(_six, _a, _b)} vs {WC.working_days_between(_five, _a, _b)}")
_noholi = {**CALENDARS[0], "holidays": []}
check(WC.working_days_between(WC.normalise_calendar(_noholi), _a, _b) == 12,
      "INJECTION: remove the holidays the document defined and the same span is 12 working "
      "days, so the holiday set is being read too")
check(WC.working_days_between(_six, _b, _a) == -11,
      "and the conversion is SIGNED: travelling backwards gives the negative")
check(WC.normalise_calendar({"calendar_id": "x"}) is None
      and WC.normalise_calendar({"working_days_of_week": []}) is None,
      "INJECTION: a calendar stating no working day is REFUSED, not defaulted")
check(WC.read_project_calendar({"projectCalendar": {"calendars": CALENDARS}}) is None,
      "INJECTION: TWO defined calendars with no stated default is AMBIGUOUS and nothing is "
      "returned -- the first is not silently picked")

# A4.9 ABLE TO GO RED THROUGH THE CONVERSION.
_pr = copy.deepcopy(STRUCTURES["procurementItems"])
_pr["items"][1]["forecast_delivery_date"] = "2026-06-05"
r = run_procurement_lead_time(si(procurementItems=_pr), None, CUT)
check(r.get("status_color") == "Red",
      "INJECTION: push the same item to 2026-06-05 -- more than 10 WORKING days late on this "
      "calendar -- and A4.9 goes Red", repr(r.get("status_color")))
_pr2 = copy.deepcopy(STRUCTURES["procurementItems"])
_pr2["items"][1]["forecast_delivery_day"] = 133
_pr2["items"][1].pop("forecast_delivery_date")
_pr2["items"][1]["required_on_site_day"] = 130
_pr2["items"][1].pop("required_on_site_date")
r = run_procurement_lead_time(si(procurementItems=_pr2), None, CUT)
_na = [i for i in (r.get("band_item_postures") or []) if i.get("not_assessed_reason")]
check(bool(_na) and "schedule's own axis" in (_na[0].get("not_assessed_reason") or ""),
      "INJECTION: an item printing a schedule-AXIS day number under a calendar-day basis is NOT "
      "converted -- there is no calendar date to count between",
      (_na[0].get("not_assessed_reason") if _na else "")[:90])

# A1.6's TIME-VARIANCE COMPONENT ABLE TO GO ADVERSE.
_tpb = copy.deepcopy(STRUCTURES["timePhasedBaseline"])
_tpb["actual_time_periods"] = 11
r = run_earned_schedule(si(timePhasedBaseline=_tpb), None, CUT)
_c = [c for c in (r.get("band_components") or []) if "time variance" in str(c.get("component"))]
check(bool(_c) and _c[0].get("band") in ("Yellow", "Amber", "Red"),
      "INJECTION: put the project seven periods behind and A1.6's time-variance component -- "
      "the one that could never form before this run -- goes adverse",
      json.dumps(_c[0] if _c else None, default=str)[:150])
_tpb2 = copy.deepcopy(STRUCTURES["timePhasedBaseline"])
_tpb2["periods"] = [{"period_index": i, "period": f"Period {i}", "cumulative_pv": 250_000 * i}
                    for i in range(1, 13)]
r = run_earned_schedule(si(timePhasedBaseline=_tpb2), None, CUT)
_c = [c for c in (r.get("band_components") or []) if "time variance" in str(c.get("component"))]
check(bool(_c) and _c[0].get("not_assessed_reason")
      and "period labels" in _c[0]["not_assessed_reason"],
      "INJECTION: relabel the periods 'Period 1'..'Period 12' -- a label that states no date "
      "span -- and the component is Not Assessed rather than assuming a month",
      (_c[0].get("not_assessed_reason") or "")[:100])

# A4.5's RECOUNT ABLE TO BE REFUSED.
_wx = copy.deepcopy(STRUCTURES["weatherImpactEvents"])
for _e in _wx["events"]:
    _e.pop("event_start_date"); _e.pop("event_end_date")
r = run_weather_impact(si(weatherImpactEvents=_wx), None, CUT)
_c = [c for c in (r.get("band_components") or [])
      if "float" in str(c.get("component")) and c.get("not_assessed_reason")]
check(bool(_c) and "event_start_date" in (_c[0].get("not_assessed_reason") or ""),
      "INJECTION: take the event spans away and A4.5's float share is Not Assessed rather than "
      "dividing calendar days by working-day float")

# =============================================================================================
# SECTION 5. THE PAGE THE OWNER LOADS.
# =============================================================================================
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

def open_page(pid):
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
        }""", pid)
        browser.close()
        return out

print()
print("=" * 92)
print("SECTION 5 -- THE REAL PAGES, IN CHROMIUM")
print("=" * 92)
OUT_A = open_page(PID_A)
OUT_B = open_page(PID_B)
srv.should_exit = True
PAGE_A = (OUT_A.get("pageText") or ""); PAGE_B = (OUT_B.get("pageText") or "")
SIG_A = (OUT_A.get("signals") or ""); SIG_B = (OUT_B.get("signals") or "")
check(bool(OUT_A.get("card")) and bool(OUT_B.get("card")),
      "both detail pages rendered on the real application")
check(OUT_A.get("rowStatus") in ("Green", "Yellow", "Amber", "Red", "Awaiting analysis"),
      "project A publishes a status on the page the owner loads",
      repr(OUT_A.get("rowStatus")))
check(OUT_B.get("rowStatus") in ("Green", "Yellow", "Amber", "Red", "Awaiting analysis"),
      "project B publishes a status too -- an absent calendar withholds arms, not the project",
      repr(OUT_B.get("rowStatus")))
_wanted = "Contract calendar Rev 1"
check(_wanted in PAGE_A and "6-day working week" in PAGE_A,
      "THE CALENDAR THE PROJECT STATED IS ON THE RENDERED PAGE, by name and by shape",
      _wanted)
check(_wanted not in PAGE_B,
      "and project B's page names no counted calendar -- nothing defaulted")
check("no approved working calendar reaches this module" in PAGE_B
      or "A calendar NAME alone is not a calendar" in PAGE_B,
      "AND PROJECT B'S RENDERED PAGE SAYS WHAT IT NEEDS, in the owner's own words",
      "found" if "calendar NAME alone" in PAGE_B else "not found")
import re as _re
_idx = PAGE_B.find("A calendar NAME alone")
if _idx > 0:
    print()
    print("FROM PROJECT B'S RENDERED PAGE:")
    print("  ..." + PAGE_B[max(0, _idx - 260):_idx + 300].replace("\n", " "))

print()
print("=" * 92)
print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
print("=" * 92)
sys.exit(1 if FAIL else 0)
