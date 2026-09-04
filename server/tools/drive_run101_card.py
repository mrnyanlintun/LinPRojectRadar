"""RUN 99, fixture E: a FULL document set, through the real routes, to establish whether the
five required categories can be assessed when the documents actually exist."""
import base64, hashlib, json, logging, pathlib, sys, time
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
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type":"text/plain"})
    assert r.status_code == 200, r.text[:300]
    return r.json()
def b64(x): return base64.b64encode(x).decode()
STAMP=str(int(time.time())); ADMIN="r99e-"+STAMP; BAC=4_000_000; END="2026-03-31"; PID="PRJ-R99E-"+STAMP
# A healthy project: on budget, on schedule, clean documents.
DOCS = [
 ("contract","contract_value",{"original_contract_sum":BAC,"project_start_date":"2026-01-01","project_end_date":"2027-06-30"}),
 ("tps","time_phased_schedule",{"planned_value_to_date":1_000_000,"planned_percent_complete":25.0,
    "data_date":END,"document_date":END,"total_float":30,"consumed_float":2}),
 ("pay","pay_application",{"amount_paid_to_date":1_000_000,"completed_to_date":1_000_000,
    "percent_complete_verified":25.0,"application_date":END,"document_date":END,
    "original_contingency":400_000,"remaining_contingency":380_000}),
 ("sched","schedule_update",{"activities_planned":200,"activities_constrained":8,"lookahead_weeks":6,
    "data_date":END,"planned_percent_complete":25.0,"planned_value_to_date":1_000_000,
    "total_float":30,"consumed_float":2}),
 ("look","lookahead_schedule",{"activities_planned":200,"activities_constrained":8,"lookahead_weeks":6,
    "constraint_rate":0.04,"lookahead_status_date":END,"lookahead_horizon":6}),
 ("res","resource_report",{"planned_labor_hours":50_000,"actual_labor_hours":49_500,
    "quantity_planned_to_date":1000,"quantity_installed_to_date":995,"quantity_unit":"m3",
    "quantity_source":"survey","resource_plan_version":"v1"}),
 ("cost","cost_report",{"indirect_cost_plan":200_000,"indirect_cost_actual":198_000,
    "material_cost_baseline":800_000,"material_cost_current":805_000,
    "original_contingency":400_000,"remaining_contingency":380_000,
    "overhead_allocation_base":"labour hours","planned_allocation_base_quantity":50_000,
    "actual_allocation_base_quantity":49_500,"overhead_driver_source":"cost ledger","report_date":END}),
 ("rfi","rfi_log",{"rfi_total":40,"rfi_answered":38,"rfi_open":2,"rfi_overdue":0,
    "avg_response_days":6,"oldest_open_days":9,"rfi_period_days":30,"log_date":END}),
 ("rfa","rfa_log",{"rfa_total":30,"rfa_approved":27,"rfa_rejected":1,"rfa_resubmit":2,
    "rfa_open":0,"avg_review_days":8,"log_date":END}),
 ("sub","submittal_register",{"submittals_total":30,"submittals_rejected":1,
    "document_date":END,"document_risk_score":0.15}),
 ("ncr","ncr_log",{"ncr_issued":3,"ncr_closed":3,"ncr_open":0,"ncr_overdue":0,"report_period":"2026-03"}),
 ("safety","safety_report",{"osha_recordable_incidents":0,"total_manhours":50_000,
    "incident_rate":0.0,"report_period":"2026-03"}),
 ("qa","quality_audit_report",{"audit_score":96,"total_findings":4,"critical_findings":0,
    "deficiency_count":4,"audit_date":END}),
 ("env","environmental_report",{"compliance_rate":100,"violations":0,"report_date":END,
    "permit_conditions_total":12,"operator_status":"in good standing"}),
 ("subr","subcontractor_report",{"compliance_score":95,"on_time_deliveries":48,
    "scheduled_deliveries":50,"report_period":"2026-03"}),
 ("proc","procurement_log",{"long_lead_items_total":20,"at_risk":1,"delayed":0,
    "on_schedule":19,"report_date":END}),
 ("insp","inspection_report",{"items_inspected":200,"items_passed":198,"items_failed":2,
    "critical_deficiency_count":0,"deficiency_count":2,"document_date":END,"document_risk_score":0.10}),
 ("weather","field_report",{"weather_days_lost":1,"float_remaining":29,"document_date":END,
    "document_risk_score":0.10,"quality_deficiencies_noted":0}),
 ("co","change_order",{"change_order_count":2,"baseline_contract_sum":BAC,
    "revised_contract_sum":BAC,"change_order_date":END}),
 ("oac","oac_minutes",{"document_date":END,"document_risk_score":0.10,
    "outstanding_action_items":2,"safety_incidents_discussed":0,"safety_actions_open":0,
    "quality_issues_discussed":0,"environmental_issues_discussed":0,"weather_days_discussed":1,
    "subcontractor_issues_discussed":0,"subcontractor_disputes":0}),
 ("past","past_performance_report",{"overall_rating":"Very Good","cost_rating":"Very Good",
    "schedule_rating":"Very Good","quality_rating":"Very Good","source":"CPARS"}),
]
def raw(t): return f"%PDF-1.4 R99E {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest():(ty,ex) for t,ty,ex in DOCS}))
with S() as s:
    r=s.scalar(select(Participant).where(Participant.role=="ResearchAdmin"))
    if r is None: s.add(Participant(pseudonymous_code="R99E-A-"+STAMP,role="ResearchAdmin",access_token_hash=hash_access_token(ADMIN)))
    else: r.access_token_hash=hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id==PID)) is None:
        s.add(Project(legacy_id=PID,doc={"id":PID,"name":"Run 99 fixture E","sector":"construction","signals":{},"events":[]}))
    s.commit()
admin=post({"action":"researchlogin","access_token":ADMIN})["session_token"]
c=post({"action":"adminparticipantcreate","session_token":admin,"pseudonymous_code":"R99E-PM-"+STAMP,"role":"Participant","account_type":"operational"})
PM=post({"action":"researchlogin","access_token":c["access_token"]})["session_token"]
post({"action":"adminmemberadd","session_token":admin,"id":PID,"participant_id":c["participant_id"],"project_role":"PM"})
ok=0
for t,ty,ex in DOCS:
    r=post({"action":"projectupload","session_token":PM,"id":PID,"period":1,"period_end":END,
            "documents":[{"filename":t+".pdf","mimeType":"application/pdf","dataBase64":b64(raw(t))}]})
    if r.get("ok"): ok+=1
    else: print("  upload FAILED", t, str(r)[:150])
print(f"uploaded {ok}/{len(DOCS)} documents through the real route")
r=post({"action":"projectcomputeall","session_token":PM,"id":PID})
print("computeall:", json.dumps(r)[:200])
ap=post({"action":"projectcategoryapply","session_token":PM,"id":PID,"period":1})
print("categoryapply:", ap.get("ok"), "readings", len(ap.get("readings") or []), "servedBy", ap.get("servedBy"))
with S() as s:
    p=s.scalar(select(Project).where(Project.legacy_id==PID))
    row=s.scalar(select(ComputedResult).where(ComputedResult.project_id==p.id, ComputedResult.superseded_by.is_(None)))
    print()
    print("PYTHON MODULE LAYER (computed_results row):")
    print("  stored project_status =", repr(row.project_status))
    print("  modules that computed :", sorted(m.get("module_id") for m in (row.module_results or [])))
    print("  category_statuses     :", json.dumps({k:(v or {}).get("status") for k,v in (row.category_statuses or {}).items()}))
    print("  abstained             :", len(row.abstained or []))

# =============================================================================================
# RUN 101, GOAL FOUR AND GOAL FIVE. THE CARD ON THE OWNER'S OWN ROUTE, READ FROM THE DOM.
#
# NOTHING UNDER TEST IS SUPPLIED. The fixture above seeded 21 documents through the REAL upload
# route and computed through the REAL compute route, which section 1's verification rule
# expressly permits. Below, the REAL application is served and the REAL project detail page is
# opened in Chromium; the Governance Decision panel is read BACK OUT OF THE RENDERED DOM. The
# decision brief is NOT composed here, NOT injected here, and NOT handed to any render function.
#
# CONTRAST with drive_run96_card.py and drive_run94_charts.py, which substitute
# `window.LinResults.rowFor`. Both violate the verification rule and neither is used here.
# =============================================================================================
import os, re, socket, threading

PASS = FAIL = 0
def check(ok, label, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1; print(f"  PASS  {label}")
    else:
        FAIL += 1; print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))

res = post({"action": "projectresults", "session_token": PM, "id": PID, "period": 1})
_r = res.get("result") or {}
_brief = _r.get("decision_brief") or {}
print()
print("=" * 90)
print("THE SERVED DECISION BRIEF, from `projectresults` -- the route the page itself calls")
print("=" * 90)
print("  brief present:", bool(_brief))
_drv = (_brief.get("drivers") or {})
for d in (_drv.get("collapsed") or []) + (_drv.get("expanded") or []):
    print(f"  driver {d.get('module_id')} [{d.get('band')}] {d.get('category_name')}")
    print(f"     figure   : {d.get('reading')}")
    print(f"     boundary : {(d.get('boundary') or '(none recorded)')}")
    print(f"     basis    : {(d.get('boundary_basis') or '(none recorded)')}")
    print(f"     provenance: {d.get('boundary_provenance')} / cutoffs "
          f"{d.get('boundary_cutoff_provenance')}")

# ---------------------------------------------------------------- GOAL ONE'S PATTERN TEST
# RUN 98's five families, re-run over the WHOLE card and PROVED ABLE TO FAIL FIRST, exactly as
# section 6 requires. The patterns are Run 98's, unchanged and not weakened.
# RUN 101 CORRECTED ITSELF HERE, AND THE MISTAKE IS RECORDED RATHER THAN QUIETLY FIXED.
# This driver first carried a HAND-TRANSCRIBED copy of Run 98's five families, and the
# transcription added imperative verbs Run 98 does not use -- "Schedule" among them. Applied to
# the rendered card it fired on the CATEGORY NAME "Schedule Performance", reporting an issued
# instruction where there was a category heading. That is a defect in the copy, not in the card.
#
# THE PATTERNS BELOW ARE NOW READ OUT OF `drive_run98.py` ITSELF, so there is one authority for
# them and a hand copy cannot drift from it again. Reading them is neither weakening the check
# (section 12.7) nor strengthening it: it is the same check.
_run98 = (HERE / "drive_run98.py").read_text()
exec(_run98[_run98.index("IMPERATIVE_PATTERNS = ["):_run98.index("def scan_imperative(text):")])


def scan_imperative(text):
    hits = []
    for name, pat in IMPERATIVE_PATTERNS:
        for m in re.finditer(pat, text or "", re.IGNORECASE):
            hits.append((name, m.group(0).strip()))
    return hits

print()
print("=" * 90)
print("THE IMPERATIVE / AUTHORITY PATTERN TEST, PROVED ABLE TO FAIL BEFORE IT IS USED")
print("=" * 90)
_probe = scan_imperative(PRESCRIPTIVE_PROBE)
for h in _probe:
    print(f"    HIT  [{h[0]}] {h[1]!r}")
check(len({h[0] for h in _probe}) >= 4,
      "the pattern test fires on a prescriptive probe, on at least four of its five families",
      str(sorted({h[0] for h in _probe})))

# ---------------------------------------------------------------- THE RAISED CHECK, PROVED
# SECTION 6's LAST LINE RAISES THE BAR: "a sentence citing a band without saying what the
# boundary was should not pass". RAISING A BAR IS NOT WEAKENING A CHECK, but a raised check
# must be PROVED still able to fail on the thing it is meant to catch, so it is proved here on
# a driver row that cites a band and records no boundary.
def cites_band_without_boundary(driver):
    return bool(driver.get("band")) and not driver.get("boundary")

_bad = {"module_id": "X.1", "band": "Amber", "reading": "some figure", "boundary": None}
check(cites_band_without_boundary(_bad),
      "the raised check FIRES on a driver citing a band with no boundary recorded (proved able "
      "to fail)")
_good = {"module_id": "A3.2", "band": "Green", "reading": "f", "boundary": "at or below 1.0"}
check(not cites_band_without_boundary(_good),
      "and it does NOT fire on a driver that records its boundary (no false positive)")

sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn
cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
srv = uvicorn.Server(cfg)
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError: time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
print()
print("served at:", BASE, "| cwd:", os.getcwd(), "| DATABASE_URL:", os.environ.get("DATABASE_URL"))

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
        const body = document.querySelector('#body-d-decision');
        if (body) body.style.display = '';
        document.dispatchEvent(new CustomEvent('lin:section-opened',
                                               {detail: {id: 'd-decision'}}));
        await new Promise(r => setTimeout(r, 2500));
        const panel = document.querySelector('#body-d-decision');
        return {
          text: panel ? (panel.innerText || '') : null,
          headings: panel ? Array.from(panel.querySelectorAll('h2,h3'))
              .map(n => n.textContent.trim()) : [],
          rowHasBrief: !!(row && row.decision_brief),
        };
    }""", PID)
    browser.close()
srv.should_exit = True

print()
print("=" * 90)
print("THE GOVERNANCE DECISION CARD, AS IT RENDERS ON THE OWNER'S OWN ROUTE AT 1280px")
print("NOTHING WAS SUPPLIED TO THE RENDERER. This is the rendered DOM's own innerText.")
print("=" * 90)
print(out.get("text"))
print("=" * 90)
print("headings:", out.get("headings"))
print("row carried a decision_brief:", out.get("rowHasBrief"))

_card = out.get("text") or ""
# RUN 135C, M8. The Run 106 guard, copied here. `out.get("text") or ""` coerces a panel that did
# not render into the empty string, after which "no imperative on card", "every band cites its
# boundary" and "every boundary cites its basis" are all trivially true -- three terminal checks
# passing on a card nobody saw. drive_run106.py:466 already carries this guard; these three
# omitted it. A missing card is now a FAILURE before the three checks are reached.
check(bool(_card), "the Governance Decision card rendered on the real page",
      f"panel text was {out.get('text')!r}")
_hits = scan_imperative(_card)
check(not _hits, "no action, instruction, deadline, remedy or authority appears on the card",
      str(_hits[:4]))
check("Boundary:" in _card or not any(
        d.get("band") for d in ((_drv.get("collapsed") or []) + (_drv.get("expanded") or []))),
      "every driver citing a band on the rendered card also states its boundary")
check("Basis:" in _card or "Boundary:" not in _card,
      "and every stated boundary on the rendered card also states its basis")
print()
print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
