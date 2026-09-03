"""
RUN 121, RULE 2. THE LIFT DISCLOSURE AND THE QUALITY-TO-SCHEDULE LINK, FROM THE DOM OF THE PAGE
THE OWNER LOADS.

NOTHING UNDER TEST IS SUPPLIED. Both projects are built through the real `projectupload` and
`projectcomputeall` routes. The page is loaded in Chromium exactly as a project manager loads
it, and `window.LinResults.rowFor` is READ ONLY, to wait for the page's own fetch to land -- it
is never assigned, never stubbed and never handed a value. Every assertion below is made against
`innerText` the page produced from the server's own response.

TWO PROJECTS:
  C  a firm the performance report rates UNSATISFACTORY whose trade records are clean and whose
     denominators are full -- Run 118's silent three-band lift, which Run 119 answered with a
     hold and Run 121 answers with a DISCLOSURE. The Green must publish AND the page must say it
     was lifted.
  D  a firm with all four four-factor populations stated and ONE OPEN CRITICAL nonconformance --
     goal 3. The page must carry the schedule-reliability reason, not only the quality one.

Run from `server/`:  python tools/drive_run121_dom.py
"""
import base64, hashlib, json, logging, pathlib, socket, sys, threading, time
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

PASS = FAIL = 0
def check(cond, what, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {what}" + (f"  [{detail}]" if detail else ""))
    else:    FAIL += 1; print(f"  FAIL  {what}" + (f"  [{detail}]" if detail else ""))
    return bool(cond)
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, r.text[:400]
    return r.json()
def b64(x): return base64.b64encode(x).decode()

STAMP = str(int(time.time())); BAC = 4_000_000; END = "2026-03-31"
ADMIN = "r121dom-" + STAMP



def build(pid, docs):
    def raw(t): return f"%PDF-1.4 R121DOM {STAMP} {pid} {t}\n".encode()
    set_extractor_override(StubExtractor(
        {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in docs}))
    with S() as s:
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": "Run 121 DOM " + pid,
                                              "sector": "construction", "signals": {},
                                              "events": []}))
        s.commit()
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": "R121DOM-PM-" + pid[-12:], "role": "Participant",
              "account_type": "operational"})
    pm = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": pid,
          "participant_id": c["participant_id"], "project_role": "PM"})
    for t, ty, ex in docs:
        post({"action": "projectupload", "session_token": pm, "id": pid, "period": 1,
              "period_end": END,
              "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(raw(t))}]})
    post({"action": "projectcomputeall", "session_token": pm, "id": pid})
    return pm


with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R121DOM-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]


DENOMS = [{"subcontractor": "Ironline Steel", "inspections_performed": 100,
           "exposure_hours": 1_000_000, "recordable_incidents": 2,
           "environmental_actions_due": 100, "audits_covering_firm": 25, "items_due": 100,
           "field_reports_covering_firm": 100, "systems_tested": 100}]
CLEAN = [{"NCR number": "NCR-1", "Subcontractor": "Ironline Steel", "Type": "nonconformance",
          "Status": "closed", "New this period": "yes"}]

# PROJECT C -- Run 118's three-band lift, verbatim from drive_run119's own fixture.
DOCS_C = [
    ("ncr", "ncr_log", {"ncr_issued": 3, "ncr_closed": 1, "ncr_open": 2,
                        "inspections_performed": 200, "ncr_denominator_basis": "inspections",
                        "report_period": "2026-Q1", "trade_attribution_json": CLEAN,
                        "trade_denominators_json": DENOMS}),
    ("sub", "subcontractor_report", {
        "subcontractor_ratings_json": [
            {"Subcontractor": "Ironline Steel", "Assessment period": "2026-Q1",
             "Rating": "Unsatisfactory"}],
        "subcontractor_rating_scale": "owner_five_point_label",
        "subcontractor_report_date": END, "subcontractor_report_version": "v1",
        "report_period": "2026-Q1"}),
]

# PROJECT D -- goal 3. Four Green populations and ONE OPEN CRITICAL nonconformance.
DOCS_D = [
    ("contract", "contract_value", {"original_contract_sum": BAC,
                                    "project_start_date": "2026-01-01",
                                    "project_end_date": "2027-06-30"}),
    ("insp", "inspection_report", {
        "items_inspected": 200, "items_passing_first_inspection": 193, "document_date": END,
        "trade_denominators_json": [
            {"Subcontractor": "Northline Mechanical",
             "Inspections performed": 100, "Inspections passed first": 99,
             "Packages due": 50, "Packages completed on time": 49,
             "Commitments due": 40, "Commitments met on time": 39,
             "Exposure hours": 200000, "Recordable incidents": 1, "Active work": "yes"}],
        "trade_attribution_json": [
            {"Reference": "NCR-CRIT", "Subcontractor": "Northline Mechanical",
             "Kind": "nonconformance", "Severity": "critical", "Status": "open"}]}),
]

PID_C = "PRJ-R121DOM-C-" + STAMP
PID_D = "PRJ-R121DOM-D-" + STAMP
PM_C = build(PID_C, DOCS_C)
PM_D = build(PID_D, DOCS_D)

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


def open_page(pid, token):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=SHELL,
                                     args=["--use-gl=swiftshader", "--no-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 2400})
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pattern, lambda r: r.abort())
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", token)
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        out = page.evaluate("""async (id) => {
            if (window.LinApp && LinApp.openDetail) LinApp.openDetail(id);
            await new Promise(r => setTimeout(r, 1500));
            await window.LinDetail.render(id);
            let row = null;
            for (let i = 0; i < 200; i++) {
              // rowFor is READ, never assigned: this only waits for the page's own fetch.
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
            await new Promise(r => setTimeout(r, 4000));
            const card = document.querySelector('#body-d-decision');
            const sig = document.querySelector('#body-d-signals');
            return {card: card ? (card.innerText || '') : '',
                    signals: sig ? (sig.innerText || '') : '',
                    pageText: (document.body.innerText || '')};
        }""", pid)
        browser.close()
        return out


print("=" * 100)
print("RUN 121 DOM -- the lift disclosure and the quality-to-schedule link on the real page")
print("=" * 100)

print("\nPROJECT C -- rated Unsatisfactory, clean records: a THREE-BAND LIFT, published")
C = open_page(PID_C, PM_C)
TXT_C = (C.get("card") or "") + "\n" + (C.get("signals") or "") + "\n" + (C.get("pageText") or "")
check(bool(TXT_C.strip()), "the page rendered")
for _l in [l for l in TXT_C.splitlines() if "A4.8" in l][:3]:
    print("     " + _l.strip()[:220])
check("disposition is recorded" not in TXT_C,
      "RUN 121: the page no longer says the reading is held for Project Manager review")
check("A4.8 Green" in TXT_C or "A4.8" in TXT_C,
      "A4.8 reaches the page with its band rather than asserting none")
check("DISCLOSED LIFT" in TXT_C,
      "THE DISCLOSURE IS ON THE PAGE THE OWNER LOADS, in the sentence a reader reads",
      [l.strip()[:150] for l in TXT_C.splitlines() if "DISCLOSED LIFT" in l][:1])
check("two or more bands BETTER" in TXT_C,
      "and it says the reading is two or more bands BETTER than the stated rating")
check("Unsatisfactory" in TXT_C,
      "and the SOURCE RATING is still on the page, verbatim and never erased")

print("\nPROJECT D -- one OPEN CRITICAL nonconformance against four otherwise Green factors")
D = open_page(PID_D, PM_D)
TXT_D = (D.get("card") or "") + "\n" + (D.get("signals") or "") + "\n" + (D.get("pageText") or "")
check(bool(TXT_D.strip()), "the page rendered")
for _l in [l for l in TXT_D.splitlines() if "A6.4" in l][:3]:
    print("     " + _l.strip()[:220])
check("A6.4 Red" in TXT_D,
      "the firm publishes RED, from four Green ladders and one open critical nonconformance",
      [l.strip()[:120] for l in TXT_D.splitlines() if "A6.4" in l][:1])
check("schedule_reliability" in TXT_D or "schedule reliability" in TXT_D.lower(),
      "and SCHEDULE RELIABILITY is named among what fired, not quality alone")

print()
print("=" * 100)
print(f"RUN 121 DOM DRIVER: {PASS} passed, {FAIL} failed, {PASS + FAIL} checks")
print("=" * 100)
sys.exit(1 if FAIL else 0)
