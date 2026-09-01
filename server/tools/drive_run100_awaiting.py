"""RUN 100, BUG FOUR. The awaiting-analysis prose, read from the RENDERED DOM of the real
detail page, on a real server, with NOTHING under test supplied.

Two projects are seeded through the REAL upload route and NEITHER is computed:
  UP  -- documents uploaded and extracted, "Process all" never pressed. The owner's definition
         of AWAITING ANALYSIS.
  BARE -- no documents at all. Not awaiting analysis; there is nothing to analyse.
The page is opened in Chromium, the ledger tab is pressed, and the prose is read out of the DOM.
"""
import base64, hashlib, json, logging, os, pathlib, socket, sys, threading, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
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
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type":"text/plain"})
    assert r.status_code == 200, r.text[:300]
    return r.json()
def b64(x): return base64.b64encode(x).decode()
STAMP=str(int(time.time())); ADMIN="r100aw-"+STAMP; END="2026-03-31"
UP="PRJ-R100UP-"+STAMP; BARE="PRJ-R100BARE-"+STAMP
DOCS=[("contract","contract_value",{"original_contract_sum":4_000_000,
        "project_start_date":"2026-01-01","project_end_date":"2027-06-30"}),
      ("pay","pay_application",{"amount_paid_to_date":1_000_000,"completed_to_date":1_000_000,
        "percent_complete_verified":25.0,"application_date":END,"document_date":END})]
def raw(t): return f"%PDF-1.4 R100AW {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest():(ty,ex) for t,ty,ex in DOCS}))
with S() as s:
    r=s.scalar(select(Participant).where(Participant.role=="ResearchAdmin"))
    if r is None: s.add(Participant(pseudonymous_code="R100AW-A-"+STAMP,role="ResearchAdmin",access_token_hash=hash_access_token(ADMIN)))
    else: r.access_token_hash=hash_access_token(ADMIN)
    for pid,nm in ((UP,"Run 100 uploaded not processed"),(BARE,"Run 100 nothing uploaded")):
        if s.scalar(select(Project).where(Project.legacy_id==pid)) is None:
            s.add(Project(legacy_id=pid,doc={"id":pid,"name":nm,"sector":"construction","signals":{},"events":[]}))
    s.commit()
admin=post({"action":"researchlogin","access_token":ADMIN})["session_token"]
c=post({"action":"adminparticipantcreate","session_token":admin,"pseudonymous_code":"R100AW-PM-"+STAMP,"role":"Participant","account_type":"operational"})
PM=post({"action":"researchlogin","access_token":c["access_token"]})["session_token"]
for pid in (UP,BARE):
    post({"action":"adminmemberadd","session_token":admin,"id":pid,"participant_id":c["participant_id"],"project_role":"PM"})
for t,ty,ex in DOCS:
    r=post({"action":"projectupload","session_token":PM,"id":UP,"period":1,"period_end":END,
            "documents":[{"filename":t+".pdf","mimeType":"application/pdf","dataBase64":b64(raw(t))}]})
    assert r.get("ok"), str(r)[:200]
print(f"{UP}: {len(DOCS)} documents uploaded through the real route, COMPUTE NEVER PRESSED")
print(f"{BARE}: no documents at all")
print("no projectcomputeall was called for either project")

sock=socket.socket(); sock.bind(("127.0.0.1",0)); PORT=sock.getsockname()[1]; sock.close()
import uvicorn
cfg=uvicorn.Config(main.app,host="127.0.0.1",port=PORT,log_level="critical")
threading.Thread(target=uvicorn.Server(cfg).run,daemon=True).start()
for _ in range(200):
    try: s2=socket.create_connection(("127.0.0.1",PORT),0.2); s2.close(); break
    except OSError: time.sleep(0.05)
BASE=f"http://127.0.0.1:{PORT}"
print(f"served at {BASE}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=SHELL,args=["--use-gl=swiftshader","--no-sandbox"])
    for VW in (1280,1024):
        for pid,label in ((UP,"UPLOADED, NOT PROCESSED"),(BARE,"NO DOCUMENTS")):
            page=browser.new_page(viewport={"width":VW,"height":2000})
            errs=[]; page.on("pageerror",lambda e: errs.append(str(e)))
            for pat in ("**accounts.google.com**","**apis.google.com**","**gstatic.com**",
                        "**tiles.openfreemap.org**","**maps.googleapis.com**"):
                page.route(pat, lambda r: r.abort())
            page.goto(BASE+"/",wait_until="domcontentloaded")
            page.evaluate("(t)=>sessionStorage.setItem('og-session-token',t)",PM)
            page.goto(BASE+"/",wait_until="domcontentloaded")
            page.wait_for_timeout(7000)
            page.evaluate("(id)=>window.LinApp.openDetail(id)",pid)
            page.wait_for_timeout(2500)
            try:
                page.click("#section-d-ledger .collapse-header",timeout=6000)
            except Exception as e:
                print("   (ledger tab click:",str(e)[:80],")")
            page.wait_for_timeout(2000)
            txt=page.evaluate("""()=>{const n=document.querySelector('.awaiting-state');
                return n?n.innerText.replace(/\\s+/g,' ').trim():null;}""")
            print()
            print("="*92)
            print(f"{VW}px  {label}  {pid}")
            print("="*92)
            print("  .awaiting-state DOM text:")
            print("   ", (txt or "<<NOT RENDERED>>")[:520])
            if errs: print("  PAGE ERRORS:",json.dumps(errs[:3]))
            page.close()
    browser.close()
