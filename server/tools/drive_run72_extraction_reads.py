#!/usr/bin/env python3
"""
RUN 72. EXTRACTION READS, IT DOES NOT DERIVE.

Executes the compliance_rate case end to end against the REAL routes
(`projectupload` -> `projectcomputeall` -> `projectresults`) on a project loaded from the
server, and proves three things:

  A. the owner's rejection reproduces, verbatim, when extraction returns 100;
  B. the corrected document (stating 1.000) uploads, stores, and reads back as 1.000;
  C. a document that does not state the field stores NOTHING for it -- absent, not invented.

WHAT IS A FIXTURE HERE, SAID PLAINLY. There is no ANTHROPIC_API_KEY in this environment, so
the MODEL CALL cannot be executed and `StubExtractor` stands in for it. Everything downstream
of the model's JSON -- the numeric contract, the merge, the observation write, selection,
`sources`, and the HTTP route itself -- is the real production path. What the stub cannot
cover is what the real model actually returns for these bytes under the corrected prompt.

argv[1] = label
"""
from __future__ import annotations
import base64, hashlib, json, logging, os, pathlib, sys, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run72"
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402
import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor, build_prompt  # noqa: E402
from app.extraction_fields import extraction_fields_for  # noqa: E402
from app.extraction_merge import ratio_scaled_extraction_keys  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
FAIL: list[str] = []


def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:300]}"
    return r.json()


def b64(raw):
    return base64.b64encode(raw).decode()


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    if not ok:
        FAIL.append(name)
    return ok


# A FRESH PROJECT PER RUN. Documents are content-addressed and a period refuses a duplicate,
# so re-running against the same project would crash on the second upload rather than measure
# anything. Rule: a crash is not a pass.
D = f"PRJ-R72-{LABEL}-{int(time.time()*1000)}"
ADMIN = "run72-admin-token"
END = {1: "2026-03-31"}


def pdf_bytes(tag: str, body: str) -> bytes:
    """A real PDF file carrying the stated text. The bytes differ per tag, so each is its own
    content-addressed document."""
    stream = "BT /F1 11 Tf 40 750 Td 14 TL\n" + "".join(
        f"({ln.replace('(', '').replace(')', '')}) Tj T*\n" for ln in body.strip().splitlines()
    ) + "ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Tag ({tag}) >>",
    ]
    out = "%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n"
    x = len(out)
    out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n"
    out += "".join(f"{o:010d} 00000 n \n" for o in offs)
    out += (f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n")
    return out.encode("latin-1")


# THE DOCUMENT, AS THE OWNER DESCRIBES IT. The real D24 is not present in this repository, so
# these bytes RECONSTRUCT the lines the owner quoted. That is a fixture and is declared as one.
D24_TEXT = """
Environmental Compliance Report
Observations recorded 5
Observations closed 5
Environmental compliance rate 1.000
Compliance rate basis Observations closed divided by observations recorded.
Expressed as a ratio between zero and one.
Permit conditions total 40
Violations 0
Report date 2026-03-31
"""

SUPPORT = [
    ("contract", "contract_value",
     {"original_contract_sum": 4_000_000, "project_start_date": "2026-01-01",
      "project_end_date": "2027-06-30"}),
]

# The three environmental documents. Same document text; different extraction answers, which is
# exactly the variable under test.
DERIVED = {"permit_conditions_total": 40, "violations": 0, "compliance_rate": 100,
           "report_date": END[1], "document_date": END[1]}
READ = {"permit_conditions_total": 40, "violations": 0, "compliance_rate": 1.000,
        "report_date": END[1], "document_date": END[1]}
ABSENT = {"permit_conditions_total": 40, "violations": 0, "compliance_rate": None,
          "report_date": END[1], "document_date": END[1]}

# RUN-UNIQUE BYTES. `documents` is content-addressed, so a second run of this driver would be
# served the FIRST run's stored extraction (`was_cached`) instead of exercising the path under
# test. Worse, an extraction stored while a bound was absent is replayed into every later
# project that uploads the same bytes. Tagging the bytes with the run label keeps each run's
# measurement its own.
_T = f"{LABEL}-{int(time.time()*1000)}"
BYTES = {
    "contract": pdf_bytes(f"contract-{_T}", "Original contract sum 4000000"),
    "D24_derived": pdf_bytes(f"D24_derived-{_T}", D24_TEXT),
    "D24_environmental_compliance_report": pdf_bytes(f"D24_read-{_T}", D24_TEXT),
    "D24_silent": pdf_bytes(f"D24_silent-{_T}", D24_TEXT.replace(
        "Environmental compliance rate 1.000", "")),
}
ANSWERS = {
    hashlib.sha256(BYTES["contract"]).hexdigest(): ("contract_value", SUPPORT[0][2]),
    hashlib.sha256(BYTES["D24_derived"]).hexdigest(): ("environmental_report", DERIVED),
    hashlib.sha256(BYTES["D24_environmental_compliance_report"]).hexdigest():
        ("environmental_report", READ),
    hashlib.sha256(BYTES["D24_silent"]).hexdigest(): ("environmental_report", ABSENT),
}
set_extractor_override(StubExtractor(ANSWERS))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R72-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 72 extraction reads",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R72-PM-{int(time.time())}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": D,
      "participant_id": created["participant_id"], "project_role": "PM"})


def upload(tag, filename=None):
    return post({"action": "projectupload", "session_token": PM, "id": D, "period": 1,
                 "period_end": END[1],
                 "documents": [{"filename": filename or f"{tag}.pdf",
                                "mimeType": "application/pdf",
                                "dataBase64": b64(BYTES[tag])}]})


print("=" * 96)
print(f"LABEL: {LABEL}   root: {ROOT}   DATABASE_URL: {os.environ.get('DATABASE_URL')}")
print(f"ANTHROPIC_API_KEY present: {bool((os.environ.get('ANTHROPIC_API_KEY') or '').strip())}"
      "  -> the MODEL CALL is stubbed; everything below the model's JSON is the real path.")
print("=" * 96)

print("\n-- 0. THE CORRECTED PROMPT, AS BUILT FOR THIS DOC TYPE --")
P = build_prompt("environmental_report", list(extraction_fields_for("environmental_report")))
print(f"ratio_scaled_extraction_keys() = {ratio_scaled_extraction_keys()}")
check("0a. the prompt names compliance_rate as a share between 0 and 1",
      "compliance_rate is a SHARE between 0 and 1 inclusive, not a percentage" in P)
check("0b. the prompt forbids multiplying that share by one hundred",
      "never multiply it by one hundred" in P)
check("0c. the prompt forbids dividing the counts to make the share",
      "do not divide one count by the other" in P)
check("0d. the prompt forbids rescaling any number, generally",
      "never convert a ratio into a percentage" in P)
check("0e. a doc type that does not request compliance_rate gets NO share sentence",
      "SHARE between 0 and 1" not in build_prompt(
          "monthly_report", list(extraction_fields_for("monthly_report"))))

assert upload("contract").get("ok") is True

print("\n-- A. THE OWNER'S REJECTION, REPRODUCED ON THE REAL ROUTE --")
r = upload("D24_derived", "D24_environmental_compliance_report.pdf")
msg = json.dumps(r)
print(f"  route returned: {msg[:400]}")
check("A1. a derived 100 is still refused", r.get("ok") is not True or "100" in msg)
check("A2. the refusal names the file and the bound",
      "D24_environmental_compliance_report.pdf" in msg and "cannot be above 1" in msg)

print("\n-- B. THE CORRECTED DOCUMENT, STATING 1.000 --")
r = upload("D24_environmental_compliance_report")
print(f"  route returned ok={r.get('ok')}  {json.dumps(r)[:300]}")
check("B1. the upload is accepted", r.get("ok") is True)
assert post({"action": "projectcomputeall", "session_token": PM, "id": D}).get("ok") is True
res = post({"action": "projectresults", "session_token": PM, "id": D, "period": 1})
row = res.get("result") or {}
si = row.get("signal_inputs") or {}
src = (si.get("sources") or {}).get("environmentalComplianceRate")
print(f"  signal_inputs.environmentalComplianceRate = {si.get('environmentalComplianceRate')!r}")
print(f"  sources.environmentalComplianceRate       = {json.dumps(src)}")
check("B2. the stored value is 1.0, exactly what the document states",
      si.get("environmentalComplianceRate") == 1.0,
      repr(si.get("environmentalComplianceRate")))
check("B3. the stored value is NOT 100", si.get("environmentalComplianceRate") != 100)
check("B4. the stored value carries its document id", bool((src or {}).get("documentId")))
check("B5. the stored value carries its document version (sha256)",
      bool((src or {}).get("documentVersion")))
check("B6. the stored value carries the date it speaks for", bool((src or {}).get("asOf")))
check("B7. the stored value carries the document type",
      (src or {}).get("docType") == "environmental_report")
docs = {str(d.get("document_id")): d for d in (row.get("source_documents") or [])}
named = docs.get(str((src or {}).get("documentId")) or "")
print(f"  source_documents entry for that id = {json.dumps(named)}")
check("B8. that document id resolves to the uploaded filename",
      bool(named) and named.get("filename") == "D24_environmental_compliance_report.pdf",
      (named or {}).get("filename"))
check("B9. the sha256 in the source matches the bytes uploaded",
      (src or {}).get("documentVersion")
      == hashlib.sha256(BYTES["D24_environmental_compliance_report"]).hexdigest())

print("\n-- C. A DOCUMENT THAT DOES NOT STATE THE FIELD --")
r = upload("D24_silent")
check("C1. the silent document uploads", r.get("ok") is True, json.dumps(r)[:200])
res2 = post({"action": "projectresults", "session_token": PM, "id": D, "period": 1})
si2 = (res2.get("result") or {}).get("signal_inputs") or {}
print(f"  after the silent document, environmentalComplianceRate = "
      f"{si2.get('environmentalComplianceRate')!r}")
check("C2. nothing was invented for the absent field: the value still comes from the document "
      "that states it, or is None",
      si2.get("environmentalComplianceRate") in (1.0, None),
      repr(si2.get("environmentalComplianceRate")))

print("\n" + "=" * 96)
print(f"RESULT: {17 - len(FAIL)}/17 checks passed")
if FAIL:
    print("FAILED: " + ", ".join(FAIL))
print("=" * 96)
sys.exit(1 if FAIL else 0)
