#!/usr/bin/env python3
"""RUN 41 section 2 - reproduce S1 on CURRENT (pre-fix) v25 behaviour.

Drives the REAL /exec upload facade and the REAL GET /documents/{id}/content route.
Records what the serving boundary actually returns for attacker-controlled bytes.
No assertions about the fix - this only CAPTURES pre-fix behaviour as evidence.
"""
from __future__ import annotations
import base64, hashlib, json, sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.research_identity import hash_access_token
from app.research_models import Document, Participant
from app.models import Project
from app.files import preview_kind

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

def post(payload):
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return r.json()

def b64(raw): return base64.b64encode(raw).decode("ascii")

ADMIN = "run41-s1-admin"; PROJ = "PRJ-RUN41-S1"
HTML = b"<html><body><script>window.__OG_XSS_EXECUTED=true;document.title='XSS-RAN'</script>benign looking</body></html>"
SVG  = b"<svg xmlns='http://www.w3.org/2000/svg'><script>window.__OG_XSS_EXECUTED=true</script></svg>"
PDF  = b"%PDF-1.4 run41 genuine\n%%EOF\n"
RECORDED = {hashlib.sha256(x).hexdigest(): ("unmapped", {}) for x in (HTML, SVG, PDF)}
set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    if s.scalar(select(Participant).where(Participant.role == "ResearchAdmin")) is None:
        s.add(Participant(pseudonymous_code="R41A", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    if s.scalar(select(Project).where(Project.legacy_id == PROJ)) is None:
        s.add(Project(legacy_id=PROJ, doc={"id": PROJ, "name": "run41 s1", "signals": {}}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "PM-R41S1", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PROJ,
      "participant_id": created["participant_id"], "project_role": "PM"})

def upload_and_fetch(filename, mime, raw):
    up = post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": 1,
               "documents": [{"filename": filename, "mimeType": mime, "dataBase64": b64(raw)}]})
    assert up.get("ok"), up
    with Session() as s:
        doc = s.scalar(select(Document).where(Document.sha256 == hashlib.sha256(raw).hexdigest()))
        stored_mime = doc.mime_type
        did = doc.document_id
    r = client.get(f"/documents/{did}/content", params={"project_id": PROJ, "session_token": pm})
    return did, stored_mime, r

out = {}
print("="*78); print("RUN 41 section 2 - S1 PRE-FIX REPRODUCTION (current v25 behaviour)"); print("="*78)
for label, fn, mime, raw in [("html_spoofed_as_pdf_name", "quarterly.pdf", "text/html", HTML),
                             ("svg_active_content", "chart.svg", "image/svg+xml", SVG),
                             ("genuine_pdf", "report.pdf", "application/pdf", PDF)]:
    did, stored, r = upload_and_fetch(fn, mime, raw)
    rec = {
        "filename": fn, "client_supplied_mime": mime, "stored_mime_type": stored,
        "http_status": r.status_code,
        "response_content_type": r.headers.get("content-type"),
        "response_content_disposition": r.headers.get("content-disposition"),
        "x_content_type_options": r.headers.get("x-content-type-options"),
        "bytes_echoed_verbatim": r.content == raw,
        "preview_kind_client_uses": preview_kind(fn),
    }
    out[label] = rec
    print(f"\n[{label}]")
    for k, v in rec.items(): print(f"   {k}: {v!r}")

print("\n" + "="*78)
h = out["html_spoofed_as_pdf_name"]
print("S1 PRE-FIX FINDINGS:")
print(f"  attacker bytes reach response verbatim ......... {h['bytes_echoed_verbatim']}")
print(f"  client MIME echoed as response Content-Type .... {'text/html' in (h['response_content_type'] or '')}")
print(f"  served inline (same-origin interpretation) ..... {'inline' in (h['response_content_disposition'] or '')}")
print(f"  nosniff absent ................................. {h['x_content_type_options'] is None}")
print(f"  preview path loads this route in an iframe ..... {h['preview_kind_client_uses'] == 'native'}")
print("="*78)
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/null", "w"), indent=2)
