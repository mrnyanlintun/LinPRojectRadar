#!/usr/bin/env python3
"""RUN 41 sections 2/4 - REAL BROWSER proof for S1 at the document-serving boundary.

Boots the real FastAPI app under uvicorn against a throwaway SQLite, uploads attacker
payloads through the real /exec facade, then loads GET /documents/{id}/content in a real
Chromium page in the app's own origin (exactly as assets/js/files.js does via <iframe>).

Execution is detected by the payload itself writing a marker into the page. A payload that
merely downloads, or renders as inert text, cannot set the marker.

Prints PREFIX / POSTFIX mode result. argv[1] = label written into the JSON at argv[2].
"""
from __future__ import annotations
import base64, hashlib, json, os, socket, subprocess, sys, threading, time

ROOT = __file__.rsplit("tools", 1)[0]
sys.path.insert(0, ROOT)
LABEL = sys.argv[1]
OUTJSON = sys.argv[2]
DBPATH = sys.argv[3]

os.environ["DATABASE_URL"] = f"sqlite:///{DBPATH}"
os.environ["SESSION_SECRET"] = "test-secret"

from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.research_identity import hash_access_token
from app.research_models import Document, Participant
from app.models import Project

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

def post(payload):
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return r.json()
def b64(raw): return base64.b64encode(raw).decode("ascii")

MARK = "__OG_R41_EXECUTED"
HTML = ("<html><body><script>window.top." + MARK + "=1;window." + MARK +
        "=1;document.title='EXECUTED';</script>ordinary looking report</body></html>").encode()
SVG = ("<svg xmlns='http://www.w3.org/2000/svg' width='80' height='80'><script>window.top."
       + MARK + "=1;window." + MARK + "=1;</script><rect width='80' height='80'/></svg>").encode()
PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
TXT = b"ordinary plain text evidence line 1\nline 2\n"

def uniq(b: bytes, tag: bytes) -> bytes:
    # content-addressed storage dedupes identical bytes into ONE document row, which would
    # silently collapse distinct cases; a per-case comment keeps each upload a separate document.
    return b.replace(b"</body>", b"<!--" + tag + b"--></body>").replace(
        b"</svg>", b"<!--" + tag + b"--></svg>") if (b"</body>" in b or b"</svg>" in b) else b + b"\n%" + tag

PAYLOADS = [
    # label, filename, client mime, bytes, is_attack
    ("legitimate_pdf",           "report.pdf",     "application/pdf",  uniq(PDF, b"p1"),  False),
    ("legitimate_txt",           "notes.txt",      "text/plain",       uniq(TXT, b"p2"),  False),
    ("spoofed_html_as_pdf",      "quarterly.pdf",  "text/html",        uniq(HTML, b"p3"), True),
    ("script_payload_html_ext",  "payload.html",   "text/html",        uniq(HTML, b"p4"), True),
    ("svg_active_content",       "chart.svg",      "image/svg+xml",    uniq(SVG, b"p5"),  True),
    ("stored_mime_mismatch",     "chart.png",      "text/html",        uniq(HTML, b"p6"), True),
]

RECORDED = {hashlib.sha256(p[3]).hexdigest(): ("unmapped", {}) for p in PAYLOADS}
set_extractor_override(StubExtractor(RECORDED))

ADMIN = f"run41-br-{LABEL}"; PROJ = f"PRJ-R41-BR"
with Session() as s:
    if s.scalar(select(Participant).where(Participant.role == "ResearchAdmin")) is None:
        s.add(Participant(pseudonymous_code="R41BR", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    if s.scalar(select(Project).where(Project.legacy_id == PROJ)) is None:
        s.add(Project(legacy_id=PROJ, doc={"id": PROJ, "name": "r41 browser", "signals": {}}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"PM-R41BR", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PROJ,
      "participant_id": created["participant_id"], "project_role": "PM"})

docids = {}
for label, fn, mime, raw, _atk in PAYLOADS:
    up = post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": 1,
               "documents": [{"filename": fn, "mimeType": mime, "dataBase64": b64(raw)}]})
    assert up.get("ok"), up
    with Session() as s:
        d = s.scalar(select(Document).where(Document.sha256 == hashlib.sha256(raw).hexdigest()))
        docids[label] = d.document_id

# ---- boot a REAL server -------------------------------------------------------
sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn
cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="error")
server = uvicorn.Server(cfg)
t = threading.Thread(target=server.run, daemon=True); t.start()
for _ in range(200):
    try:
        s2 = socket.create_connection(("127.0.0.1", PORT), 0.2); s2.close(); break
    except OSError: time.sleep(0.05)

BASE = f"http://127.0.0.1:{PORT}"
from playwright.sync_api import sync_playwright

out = {"label": LABEL, "base": BASE, "cases": {}}
with sync_playwright() as p:
    br = p.chromium.launch(executable_path="/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell", args=["--no-sandbox"])
    for label, fn, mime, raw, is_attack in PAYLOADS:
        url = (f"{BASE}/documents/{docids[label]}/content?project_id={PROJ}"
               f"&session_token={pm}")
        ctx = br.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.on("dialog", lambda d: d.dismiss())
        executed = False; reached = False; served = {}
        downloaded = {"n": 0}
        ctx.on("download", lambda d: downloaded.__setitem__("n", downloaded["n"] + 1))
        # Load the app origin first, then embed the content route in a same-origin iframe,
        # exactly as assets/js/files.js does. window.top marker survives the iframe.
        page.goto(f"{BASE}/documents/{docids['legitimate_txt']}/content?project_id={PROJ}&session_token={pm}",
                  wait_until="domcontentloaded")
        page.evaluate(f"window.{MARK}=0")
        # capture the actual serving headers the browser saw
        hdr = {}
        def on_resp(r):
            if "/content" in r.url and docids[label] in r.url:
                hdr.update({k.lower(): v for k, v in r.headers.items()})
                hdr["__status"] = r.status
        page.on("response", on_resp)
        try:
            page.evaluate("""(u) => new Promise((res) => {
                const f = document.createElement('iframe');
                f.src = u; f.onload = () => res(1); f.onerror = () => res(0);
                document.body.appendChild(f); setTimeout(() => res(2), 3000);
            })""", url)
        except Exception:
            pass
        page.wait_for_timeout(700)
        reached = bool(hdr.get("__status") == 200)
        try:
            executed = bool(page.evaluate(f"window.{MARK} === 1"))
        except Exception:
            executed = False
        out["cases"][label] = {
            "filename": fn, "client_mime": mime, "is_attack": is_attack,
            "boundary_reached_http_200": reached,
            "served_content_type": hdr.get("content-type"),
            "served_content_disposition": hdr.get("content-disposition"),
            "served_nosniff": hdr.get("x-content-type-options"),
            "active_content_executed": executed,
            "downloads_triggered": downloaded["n"],
        }
        ctx.close()
    br.close()
server.should_exit = True; time.sleep(0.4)

print("=" * 78); print(f"RUN 41 REAL-BROWSER S1 PROOF [{LABEL}]"); print("=" * 78)
atk_exec = 0
for k, v in out["cases"].items():
    print(f"\n[{k}] attack={v['is_attack']}")
    for kk, vv in v.items():
        if kk != "is_attack": print(f"   {kk}: {vv!r}")
    if v["is_attack"] and v["active_content_executed"]: atk_exec += 1
out["attacker_executions"] = atk_exec
out["all_attacks_reached_boundary"] = all(
    v["boundary_reached_http_200"] for v in out["cases"].values() if v["is_attack"])
print("\n" + "=" * 78)
print(f"attacker-controlled active content executions = {atk_exec}")
print(f"all attacks reached the document-serving boundary (HTTP 200) = {out['all_attacks_reached_boundary']}")
print("=" * 78)
json.dump(out, open(OUTJSON, "w"), indent=2)
