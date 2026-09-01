#!/usr/bin/env python3
"""
RUN 99. THE SIX STATUSES, ON THE PORTFOLIO PAGE THE OWNER LOADS.

NOTHING UNDER TEST IS SUPPLIED. Four fixtures are built through the REAL upload / compute /
category-apply routes; the browser then opens the REAL page, lets the page's own store fetch
the REAL list route, and reads the status legend and every project row BACK OUT OF THE
RENDERED DOM. No status is handed to any renderer, and `LinResults.rowFor` is not substituted.

  A  documents uploaded, Process all NOT pressed   -> must read "Awaiting analysis"
  B  documents uploaded, Process all pressed
  C  as B plus the participant's own `projectcategoryapply`
  D  as C, EV = PV = AC = BAC at 100 per cent (the owner's Complete condition)
"""
from __future__ import annotations
import base64, hashlib, json, logging, os, pathlib, socket, sys, threading, time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

from fastapi.testclient import TestClient            # noqa: E402
from sqlalchemy import select                        # noqa: E402
import app.main as main                              # noqa: E402
from app.documents import set_extractor_override     # noqa: E402
from app.extraction_client import StubExtractor      # noqa: E402
from app.models import Project                       # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant          # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = FAILED = 0

def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1; print(f"  PASS  {label}")
    else:
        FAILED += 1; print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))
    return bool(ok)

def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:300]}"
    return r.json()

def b64(x): return base64.b64encode(x).decode()

STAMP = str(int(time.time()))
ADMIN = "run99-drv-" + STAMP
BAC = 4_000_000
END = "2026-03-31"
FIG  = {"ev": 1_000_000, "ac": 1_050_000, "pv": 1_020_000, "ppct": 25.50, "apct": 25.00}
FIGD = {"ev": BAC, "ac": BAC, "pv": BAC, "ppct": 100.0, "apct": 100.0}
IDS = {k: f"PRJ-R99{k}-{STAMP}" for k in "ABCD"}

def docs_for(pid, f):
    return [(f"{pid}-contract", "contract_value",
             {"original_contract_sum": BAC, "project_start_date": "2026-01-01",
              "project_end_date": "2027-06-30"}),
            (f"{pid}-tps", "time_phased_schedule",
             {"planned_value_to_date": f["pv"], "planned_percent_complete": f["ppct"],
              "data_date": END, "document_date": END}),
            (f"{pid}-pay", "pay_application",
             {"amount_paid_to_date": f["ac"], "completed_to_date": f["ev"],
              "percent_complete_verified": f["apct"],
              "application_date": END, "document_date": END})]

ALL = {k: docs_for(IDS[k], FIGD if k == "D" else FIG) for k in "ABCD"}
def raw(tag): return f"%PDF-1.4 RUN99 {STAMP} {tag}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest(): (ty, ex)
                                      for k in "ABCD" for t, ty, ex in ALL[k]}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R99-ADM-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for k in "ABCD":
        if s.scalar(select(Project).where(Project.legacy_id == IDS[k])) is None:
            s.add(Project(legacy_id=IDS[k], doc={"id": IDS[k], "name": f"Run 99 fixture {k}",
                                                 "sector": "construction",
                                                 "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R99-PM-" + STAMP, "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
for k in "ABCD":
    post({"action": "adminmemberadd", "session_token": admin, "id": IDS[k],
          "participant_id": created["participant_id"], "project_role": "PM"})
    for tag, _ty, _ex in ALL[k]:
        r = post({"action": "projectupload", "session_token": PM, "id": IDS[k], "period": 1,
                  "period_end": END,
                  "documents": [{"filename": tag + ".pdf", "mimeType": "application/pdf",
                                 "dataBase64": b64(raw(tag))}]})
        assert r.get("ok") is True, str(r)[:300]

SERVER_STATUS = {}
for k in "BCD":
    r = post({"action": "projectcomputeall", "session_token": PM, "id": IDS[k]})
    assert r.get("ok") is True, str(r)[:200]
    SERVER_STATUS[k] = (r.get("results") or [{}])[0].get("project_status")
for k in "CD":
    post({"action": "projectcategoryapply", "session_token": PM, "id": IDS[k], "period": 1})

print("=" * 96)
print("WHAT THE SERVER STORED / SERVES, before the browser is asked anything")
print("=" * 96)
def httpget(action, **kw):
    q = "".join(f"&{a}={b}" for a, b in kw.items())
    return client.get(f"/exec?action={action}&session_token={PM}{q}").json()

FULL = {p["id"]: p for p in (httpget("list").get("projects") or [])}
SLIM = {p["id"]: p for p in (httpget("listslim").get("projects") or [])}
for k in "ABCD":
    pid = IDS[k]
    f, sl = FULL.get(pid, {}), SLIM.get(pid, {})
    print(f"  {k}  compute route stored={SERVER_STATUS.get(k)!r}")
    print(f"      list      status={f.get('status')!r} "
          f"storedResult.project_status={((f.get('storedResult') or {}).get('project_status'))!r}")
    print(f"      listslim  status={sl.get('status')!r} "
          f"storedResult={'present' if sl.get('storedResult') else 'ABSENT'}")

sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn  # noqa: E402
cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
threading.Thread(target=uvicorn.Server(cfg).run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError:
        time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"
print(f"\ncwd={os.getcwd()}  repo={HERE.parents[1]}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
print(f"served at {BASE}")

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=SHELL,
                                 args=["--use-gl=swiftshader", "--no-sandbox"])
    for VW in (1280, 1024):
        print()
        print("=" * 96)
        print(f"THE OWNER'S OWN PORTFOLIO PAGE AT {VW}px -- real server, real page, nothing injected")
        print("=" * 96)
        page = browser.new_page(viewport={"width": VW, "height": 2400})
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                    "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pat, lambda r: r.abort())
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.wait_for_timeout(9000)
        out = page.evaluate("""(ids) => {
            const host = document.getElementById('status-legend');
            const legend = host ? Array.from(host.querySelectorAll('.legend-item')).map(n => ({
                key: n.getAttribute('data-status'),
                name: (n.querySelector('.legend-name')||{}).textContent,
                count: (n.querySelector('.legend-count')||{}).textContent})) : null;
            const rows = {};
            document.querySelectorAll('button,li,div').forEach(n => {
              const code = n.querySelector && n.querySelector('.li-code');
              if (!code) return;
              const id = code.textContent.trim();
              if (!ids.includes(id)) return;
              rows[id] = {
                state: (n.querySelector('.li-state')||{}).textContent || null,
                computed: (n.querySelector('.li-computed')||{}).textContent || null,
                text: (n.innerText||'').replace(/\\n/g,' | ').slice(0,300)};
            });
            const P = (window.LIN_PROJECTS||[]).filter(p => ids.includes(p.id));
            return {legend, rows, slim: P.map(p => ({id:p.id, slim:!!p.slim, status:p.status,
                      stateLabel: (window.LinApp && LinApp.stateLabel)
                                    ? LinApp.stateLabel(p) : null})),
                    nProjects: (window.LIN_PROJECTS||[]).length,
                    lastCounts: (window.LinApp && LinApp.renderStatusLegend)
                                  ? (LinApp.renderStatusLegend.lastCounts || null) : null};
        }""", [IDS[k] for k in "ABCD"])
        print("  legend: " + json.dumps(out["legend"]))
        print("  LIN_PROJECTS count: %s   legend counts: %s"
              % (out["nProjects"], json.dumps(out.get("lastCounts"))))
        for k in "ABCD":
            pid = IDS[k]
            r = (out["rows"] or {}).get(pid)
            sl = next((x for x in out["slim"] if x["id"] == pid), None)
            print(f"  {k}  slimrow={json.dumps(sl)}")
            print(f"      DOM state={None if not r else r['state']!r}  "
                  f"computed={None if not r else r['computed']!r}")
            if r: print(f"      row text: {r['text'][:220]}")
        if errs: print("  PAGE ERRORS: " + json.dumps(errs[:5]))
        leg = {x["name"]: x["count"] for x in (out["legend"] or [])}
        check(list(leg.keys()) == ["Complete", "Green", "Yellow", "Amber", "Red",
                                  "Awaiting analysis"],
              f"[{VW}] the legend names exactly the owner's six, in his order", str(list(leg.keys())))
        rowA = (out["rows"] or {}).get(IDS["A"]) or {}
        check((rowA.get("state") or "").strip() == "Awaiting analysis",
              f"[{VW}] A (uploaded, NOT processed) reads Awaiting analysis",
              repr(rowA.get("state")))
        for k in "BCD":
            r = (out["rows"] or {}).get(IDS[k]) or {}
            st = (r.get("state") or "").strip()
            check(st != "Awaiting analysis",
                  f"[{VW}] {k} (PROCESSED) does NOT read Awaiting analysis", repr(st))
        # RUN 99, GOAL TWO. A PRODUCED PROJECT THAT CARRIES Complete, read off the owner's page.
        rowD = (out["rows"] or {}).get(IDS["D"]) or {}
        check((rowD.get("state") or "").strip() == "Complete",
              f"[{VW}] D (EV = PV = AC = BAC at 100 per cent) reads Complete on the row",
              repr(rowD.get("state")))
        check(leg.get("Complete") == "1",
              f"[{VW}] and the legend counts exactly one Complete", json.dumps(leg))
        counts = out.get("lastCounts") or {}
        check(sum(v for v in counts.values()) == out["nProjects"],
              f"[{VW}] the legend's counts reconcile against LIN_PROJECTS", json.dumps(counts))
        page.close()
    browser.close()

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
