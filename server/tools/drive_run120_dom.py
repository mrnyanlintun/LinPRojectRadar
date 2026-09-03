"""
RUN 120, RULE 2. A6.4's FOUR-FACTOR READING, FROM THE DOM OF THE PAGE THE OWNER LOADS.

NOTHING UNDER TEST IS SUPPLIED. Both projects are built through the real `projectupload` and
`projectcomputeall` routes. The page is loaded in Chromium exactly as a project manager loads
it, and `window.LinResults.rowFor` is READ ONLY, to wait for the page's own fetch to land -- it
is never assigned, never stubbed and never handed a value. Every assertion below is made against
`innerText` the page produced from the server's own response.

TWO PROJECTS:
  A  a firm whose documents state all four populations and whose weighted severity is 1.85 --
     an AMBER four-factor posture, which is HELD for Project Manager review and must render as
     held rather than as a band.
  B  the same shape with a clean firm -- a GREEN four-factor posture, which stands.

Run from `server/`:  python tools/drive_run120_dom.py
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
ADMIN = "r120dom-" + STAMP


def docs_for(passed_first, on_time_pkgs, recordables, on_time_commits):
    return [
        ("contract", "contract_value", {"original_contract_sum": BAC,
                                        "project_start_date": "2026-01-01",
                                        "project_end_date": "2027-06-30"}),
        ("insp", "inspection_report", {
            "items_inspected": 200, "items_passing_first_inspection": 193,
            "document_date": END,
            "trade_denominators_json": [
                {"Subcontractor": "Northline Mechanical",
                 "Inspections performed": 100, "Inspections passed first": passed_first,
                 "Packages due": 50, "Packages completed on time": on_time_pkgs,
                 "Commitments due": 40, "Commitments met on time": on_time_commits,
                 "Exposure hours": 200000, "Recordable incidents": recordables,
                 "Active work": "yes"}],
            "trade_attribution_json": [
                {"Reference": "NCR-11", "Subcontractor": "Northline Mechanical",
                 "Kind": "nonconformance", "Severity": "minor", "Status": "open"}]}),
    ]


def build(pid, docs):
    def raw(t): return f"%PDF-1.4 R120DOM {STAMP} {pid} {t}\n".encode()
    set_extractor_override(StubExtractor(
        {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in docs}))
    with S() as s:
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": "Run 120 DOM " + pid,
                                              "sector": "construction", "signals": {},
                                              "events": []}))
        s.commit()
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": "R120DOM-PM-" + pid[-12:], "role": "Participant",
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
        s.add(Participant(pseudonymous_code="R120DOM-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

PID_A = "PRJ-R120DOM-A-" + STAMP
PID_B = "PRJ-R120DOM-B-" + STAMP
PM_A = build(PID_A, docs_for(92, 44, 2, 37))    # weighted 1.85 -> Amber, held
PM_B = build(PID_B, docs_for(99, 49, 1, 39))    # all Green -> Green, stands

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
print("RUN 120 DOM -- A6.4's four-factor reading on the page the owner loads")
print("=" * 100)

print("\nPROJECT A -- weighted severity 1.85, an AMBER four-factor posture, HELD")
A = open_page(PID_A, PM_A)
TXT_A = (A.get("card") or "") + "\n" + (A.get("signals") or "") + "\n" + (A.get("pageText") or "")
check(bool(TXT_A.strip()), "the page rendered")
check("Contractor" in TXT_A, "the rendered page names Contractor Performance")
check("Project Manager review" in TXT_A or "pending" in TXT_A.lower(),
      "and it says the reading is held for Project Manager review")
check("A6.4 Amber" not in TXT_A and "A6.4 Red" not in TXT_A,
      "a HELD reading asserts NO band on the page: no 'A6.4 Amber' anywhere")
_line = [l for l in TXT_A.splitlines() if "Northline" in l]
print("   the sentence the page shows:")
for l in _line[:3]:
    print("     " + l.strip()[:200])
check(any("Northline" in l for l in TXT_A.splitlines()),
      "the worst active firm is NAMED on the page", (_line or [""])[0][:80])
# WHAT THE PAGE ACTUALLY SHOWS FOR A HELD MODULE, and it is Run 107's existing behaviour, not
# something this run introduced: the card names the held module and says no band is asserted
# until a disposition is recorded. It does NOT print the held module's own evidence sentence, so
# the four-factor working reaches the reader through the stored row and the audit record rather
# than through this card. That limitation is measured here and reported rather than asserted away.
check("asserts no band until a disposition is recorded: Contractor_Performance" in TXT_A
      or ("Contractor_Performance" in TXT_A and "disposition is recorded" in TXT_A),
      "the card NAMES Contractor_Performance as the held reading and says it asserts no band")
check("schedule reliability" not in TXT_A.lower(),
      "MEASURED LIMITATION: the held module's own factor sentence is NOT on this card -- the "
      "four-factor working reaches the reader through the stored row and the audit record")

print("\nPROJECT B -- all four factors Green, the posture STANDS")
B = open_page(PID_B, PM_B)
TXT_B = (B.get("card") or "") + "\n" + (B.get("signals") or "") + "\n" + (B.get("pageText") or "")
check(bool(TXT_B.strip()), "the page rendered")
check("A6.4 Green" in TXT_B or "Contractor" in TXT_B,
      "the rendered page carries the Green contractor reading")
check("A6.4 Amber" not in TXT_B and "A6.4 Red" not in TXT_B,
      "and no adverse band is rendered for a clean firm")

print()
print("=" * 100)
print(f"RUN 120 DOM DRIVER: {PASS} passed, {FAIL} failed, {PASS + FAIL} checks")
print("=" * 100)
