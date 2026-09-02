"""
RUN 119, GOAL 6. THE BUDGET RE-BASING, READ FROM THE DOM OF THE PAGE THE OWNER LOADS.

THE OWNER'S RULING, SECTION 6: "show the original contract sum, the change orders that re-based
it, and the resulting budget -- so a reader sees the movement rather than one figure with no
history." A display change, not a recalculation.

NOTHING UNDER TEST IS SUPPLIED. Both projects are built through the real `projectupload` and
`projectcomputeall` routes. The page is loaded in Chromium exactly as a project manager loads
it, and `window.LinResults.rowFor` is READ ONLY to wait for the page's own fetch to land -- it
is never assigned, never stubbed and never handed a value. The assertions are made against
`document.querySelector('[data-budget-rebasing]').innerText` and its figures line, which are DOM
text the page produced from the server's own response.

TWO PROJECTS, AND THE SECOND IS THE OWNER'S OWN CONDITION:
  A  a contract of $4,000,000 re-based to $4,300,000 by two approved change orders
  B  THE SAME DOCUMENTS with the change order removing nothing -- revised equals original --
     which must render NOTHING AT ALL rather than a re-basing of nought.

PROVED ABLE TO FAIL a second way: the server-side composer is suppressed in the LIVE module,
the DOM node must be absent, and it is then restored and required back.

Run from `server/`:  python tools/drive_run119_dom.py
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
PID = "PRJ-R119DOM-" + STAMP; ADMIN = "r119dom-" + STAMP

DOCS = [
    ("contract", "contract_value", {"original_contract_sum": BAC,
                                    "project_start_date": "2026-01-01",
                                    "project_end_date": "2027-06-30"}),
    ("pay", "pay_application", {"amount_paid_to_date": 1_000_000,
                                "completed_to_date": 1_000_000,
                                "percent_complete_verified": 25.0,
                                "application_date": END, "document_date": END,
                                "original_contingency": 400_000,
                                "remaining_contingency": 380_000}),
    ("tps", "time_phased_schedule", {"planned_value_to_date": 1_000_000,
                                     "planned_percent_complete": 25.0, "data_date": END,
                                     "document_date": END, "total_float": 30,
                                     "consumed_float": 2}),
    ("oac", "oac_minutes", {"document_date": END, "document_risk_score": 0.10,
                            "outstanding_action_items": 2, "subcontractor_disputes": 0,
                            "report_period": "2026-03", "disputes_recorded": 1}),
    ("subr", "subcontractor_report", {"compliance_score": 95, "report_period": "2026-03",
                                      "subcontractor_ratings_json": [
                                          {"Subcontractor": "Northline Mechanical",
                                           "Assessment period": "2026-03",
                                           "Rating": "Very Good"}],
                                      "subcontractor_rating_scale": "owner_five_point_label",
                                      "subcontractor_report_date": END,
                                      "subcontractor_report_version": "1"}),
]

REVISED = 4_300_000


def build(pid, revised):
    docs = DOCS + [("co", "change_order",
                    {"change_order_count": 2, "baseline_contract_sum": BAC,
                     "revised_contract_sum": revised, "change_order_date": END})]
    def raw(t): return f"%PDF-1.4 R119DOM {STAMP} {pid} {t}\n".encode()
    set_extractor_override(StubExtractor(
        {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in docs}))
    with S() as s:
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": "Run 119 re-basing",
                                              "sector": "construction", "signals": {},
                                              "events": []}))
        s.commit()
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": "R119DOM-PM-" + pid, "role": "Participant",
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
        s.add(Participant(pseudonymous_code="R119DOM-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

PID_A = "PRJ-R119DOM-A-" + STAMP
PID_B = "PRJ-R119DOM-B-" + STAMP
PM = build(PID_A, REVISED)
PM_B = build(PID_B, BAC)

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


def open_page(pid=None, token=None):
    pid = pid or PID_A
    token = token or PM
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
            // rowFor is READ, never assigned: this only waits for the page's own fetch.
            for (let i = 0; i < 200; i++) {
              const row = (window.LinResults && window.LinResults.rowFor)
                  ? window.LinResults.rowFor({id: id}) : null;
              if (row && row.information_completeness) break;
              await new Promise(r2 => setTimeout(r2, 250));
            }
            const body = document.querySelector('#body-d-brief');
            if (body) body.style.display = '';
            document.dispatchEvent(new CustomEvent('lin:section-opened',
                                                   {detail: {id: 'd-brief'}}));
            await new Promise(r => setTimeout(r, 6000));
            const node = document.querySelector('[data-budget-rebasing]');
            const figs = document.querySelector('[data-budget-rebasing-figures]');
            const sec = document.querySelector('[data-brief-rebasing]');
            const brief = document.querySelector('#body-d-brief');
            const rec = document.querySelector('.eb-rec');
            return {
              caveat: node ? (node.innerText || '').trim() : null,
              figures: figs ? (figs.innerText || '').trim() : null,
              sectionText: sec ? (sec.innerText || '').trim() : null,
              briefText: brief ? (brief.innerText || '').trim() : null,
              recText: rec ? (rec.innerText || '').trim() : null,
              caveatIsLast: !!(sec && brief &&
                  brief.querySelectorAll('.eb-section')[
                      brief.querySelectorAll('.eb-section').length - 1] === sec)
            };
        }""", pid)
        browser.close()
        return out


print("=" * 94)
print("RUN 119, GOAL 6 -- THE BUDGET RE-BASING ON THE PAGE THE OWNER LOADS, READ FROM THE DOM")
print("=" * 94)
OUT = open_page()
print("\n--- the disclosure node's own text, verbatim from the DOM ---")
print(OUT.get("caveat"))
print("--- the figures line, verbatim from the DOM ---")
print(OUT.get("figures"))
print("--- end ---\n")
check(bool(OUT.get("caveat")), "the re-basing node exists in the rendered DOM")
check(str(OUT.get("caveat") or "").startswith("This project's budget has been re-based"),
      "and it says the budget was re-based", str(OUT.get("caveat"))[:60])
_f = str(OUT.get("figures") or "")
check("$4,000,000" in _f, "the ORIGINAL contract sum is on the page", _f)
check("2 approved change orders $300,000" in _f,
      "the CHANGE ORDERS that re-based it are on the page, with their movement", _f)
check("$4,300,000" in _f, "the RESULTING budget is on the page", _f)
check("computed against the REVISED budget" in str(OUT.get("caveat") or ""),
      "and the sentence says TCPI and VAC still compute against the revised budget")

print()
print("=" * 94)
print("SECTION 2 -- AN UNCHANGED BUDGET RENDERS NOTHING, NOT A RE-BASING OF NOUGHT")
print("=" * 94)
NOMOVE = open_page(PID_B, PM_B)
check(NOMOVE.get("caveat") is None and NOMOVE.get("figures") is None,
      "the same documents with revised equal to original produce NO node at all",
      str(NOMOVE.get("caveat")))
check(bool(NOMOVE.get("briefText")),
      "and the brief itself still rendered on that project, so the absence is the "
      "disclosure's and not the page's",
      str(NOMOVE.get("briefText"))[:60])

print()
print("=" * 94)
print("FALSIFICATION -- the same page, with the server-side composer suppressed in the LIVE module")
print("=" * 94)
import app.documents as DOCMOD
_real = DOCMOD.budget_rebasing
DOCMOD.budget_rebasing = lambda si: None
try:
    BROKEN = open_page()
finally:
    DOCMOD.budget_rebasing = _real
check(BROKEN.get("caveat") is None,
      "FALSIFIED: with the server composing nothing, the DOM node is absent",
      str(BROKEN.get("caveat")))
AGAIN = open_page()
check(str(AGAIN.get("caveat") or "").startswith("This project's budget has been re-based"),
      "RESTORED: the disclosure is back in the DOM once the suppression is removed",
      str(AGAIN.get("caveat"))[:60])

print("\n" + "=" * 94)
print(f"RUN 119 DOM DRIVER: {PASS} passed, {FAIL} failed, {PASS + FAIL} checks")
print("=" * 94)
sys.exit(1 if FAIL else 0)
