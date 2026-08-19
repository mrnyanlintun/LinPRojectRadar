#!/usr/bin/env python3
"""
RUN 40 regression — serving-boundary security for GET /documents/{id}/content (finding S1).

Baseline defect (reproduced before the fix): an authenticated PM could upload bytes containing
active markup with a client-supplied mimeType of "text/html". The stored mime_type is never
validated, and the serve route echoed it as the Content-Type with Content-Disposition: inline and
no nosniff. Because assets/js/files.js loads this route inside a same-origin <iframe>, that content
executed as script in the application's origin when a project member previewed the document.

This suite drives the REAL /exec upload and the REAL /documents/{id}/content route (no direct model
substitution for the boundary under test) and proves the serving policy:

  1. active content (text/html) is NOT served as text/html and is downloaded, not rendered;
  2. image/svg+xml (script-capable) is likewise downloaded;
  3. X-Content-Type-Options: nosniff is always present;
  4. a filename containing a double-quote cannot break the Content-Disposition quoted-string;
  5. a genuine PDF is still served inline as application/pdf, so the preview still works
     (the fix does not break the route's purpose);
  6. the raw payload bytes still survive transfer unchanged (integrity preserved).

Run (from server/): DATABASE_URL=... SESSION_SECRET=... python tools/test_run40_serve_content_security.py
Exit 0 on success, 1 on any failure.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Document, Participant  # noqa: E402
from app.models import Project  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail and not ok else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


ADMIN = "run40-serve-admin"
PROJ = "PRJ-RUN40-SERVE"

HTML_BYTES = b"<html><body><script>document.title='XSS'</script>hi</body></html>"
SVG_BYTES = b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>"
PDF_BYTES = b"%PDF-1.4 run40 genuine pdf\n%%EOF\n"

RECORDED = {
    hashlib.sha256(HTML_BYTES).hexdigest(): ("unmapped", {}),
    hashlib.sha256(SVG_BYTES).hexdigest(): ("unmapped", {}),
    hashlib.sha256(PDF_BYTES).hexdigest(): ("unmapped", {}),
}
set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    if s.scalar(select(Participant).where(Participant.role == "ResearchAdmin")) is None:
        s.add(Participant(pseudonymous_code="RUN40A", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    if s.scalar(select(Project).where(Project.legacy_id == PROJ)) is None:
        s.add(Project(legacy_id=PROJ, doc={"id": PROJ, "name": "run40 serve", "signals": {}}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "PM-RUN40S", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PROJ,
      "participant_id": created["participant_id"], "project_role": "PM"})

print("=" * 78)
print("RUN 40 — serving-boundary content security (finding S1)")
print("=" * 78)


def upload_and_fetch(filename: str, mime: str, raw: bytes):
    up = post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": 1,
               "documents": [{"filename": filename, "mimeType": mime, "dataBase64": b64(raw)}]})
    assert up.get("ok"), up
    with Session() as s:
        doc = s.scalar(select(Document).where(Document.sha256 == hashlib.sha256(raw).hexdigest()))
    r = client.get(f"/documents/{doc.document_id}/content",
                   params={"project_id": PROJ, "session_token": pm})
    return r


# 1-3: active HTML content
r = upload_and_fetch('evil".pdf', "text/html", HTML_BYTES)
ctype = (r.headers.get("content-type") or "").lower()
cdisp = (r.headers.get("content-disposition") or "").lower()
check(r.status_code == 200, "html upload is served (route reachable)")
check("text/html" not in ctype, "text/html is NOT echoed as Content-Type", f"got {ctype!r}")
check(ctype.startswith("application/octet-stream"),
      "active content served as opaque octet-stream", f"got {ctype!r}")
check("attachment" in cdisp, "active content forced to attachment disposition", f"got {cdisp!r}")
check((r.headers.get("x-content-type-options") or "").lower() == "nosniff",
      "X-Content-Type-Options: nosniff present")
# 4: filename quote cannot break the quoted-string — the served header has no stray inner quote
check('"' not in r.headers.get("content-disposition", "").split("filename=", 1)[-1][1:-1]
      if "filename=" in r.headers.get("content-disposition", "") else True,
      "filename quote sanitised out of Content-Disposition")

# 2b: svg (script-capable) also downloaded, not rendered
r_svg = upload_and_fetch("pic.svg", "image/svg+xml", SVG_BYTES)
ctype_svg = (r_svg.headers.get("content-type") or "").lower()
check("svg" not in ctype_svg and ctype_svg.startswith("application/octet-stream"),
      "image/svg+xml served as octet-stream, not rendered", f"got {ctype_svg!r}")

# 5-6: genuine PDF still inline + integrity preserved
r_pdf = upload_and_fetch("report.pdf", "application/pdf", PDF_BYTES)
ctype_pdf = (r_pdf.headers.get("content-type") or "").lower()
cdisp_pdf = (r_pdf.headers.get("content-disposition") or "").lower()
check(ctype_pdf.startswith("application/pdf"), "genuine PDF still served as application/pdf",
      f"got {ctype_pdf!r}")
check("inline" in cdisp_pdf, "genuine PDF still served inline (preview preserved)")
check((r_pdf.headers.get("x-content-type-options") or "").lower() == "nosniff",
      "nosniff present on the PDF path too")
check(r_pdf.content == PDF_BYTES, "PDF bytes survive transfer unchanged (integrity)")

passed = sum(1 for ok, _, _ in results if ok)
total = len(results)
print("\n" + "=" * 78)
print(f"RESULT: {passed}/{total} checks passed")
print("=" * 78)
sys.exit(0 if passed == total else 1)
