#!/usr/bin/env python3
"""
RUN 127. THE UPLOAD BATCH CAP, AND THE PER-FILE GUARDS IT MUST NOT DISPLACE.

A CHECK SCRIPT, NOT A PYTEST MODULE -- `server/tools/` holds scripts by convention; under
pytest this file reports "no tests ran". Run it as:

    cd server && DATABASE_URL=sqlite+pysqlite:///<throwaway>.db \
        python tools/test_run127_upload_batch_cap.py [--revert]

NO MODEL CALL IS MADE OR SIMULATED. There is no key in this environment. What serves in a
model's place is `StubExtractor`, keyed on the exact sha256 of each constructed document, which
raises on an unrecorded hash rather than inventing an extraction. Every count below names the
fixture it came from.

WHAT IS PROVED
  1. FIXTURE `BATCH_30` -- exactly `MAX_BATCH_DOCUMENTS` documents -- is ACCEPTED.
  2. FIXTURE `BATCH_31` -- one document over the cap -- is REFUSED, and the refusal names both
     the limit and the number sent.
  3. The refusal happens BEFORE anything is decoded or stored: no `document_uploads` row and no
     `upload_attempts` row appears for the refused batch.
  4. FIXTURE `OVERSIZE_B64` and FIXTURE `OVERSIZE_BYTES` -- the pre-existing per-file guards
     `MAX_BASE64_CHARS` and `MAX_FILE_BYTES` -- still fire inside an under-cap batch. This run
     must not displace them.

`--revert` raises `MAX_BATCH_DOCUMENTS` to 10_000 at run time, which is the fault injection: it
makes check 2 and check 3 FAIL, which is what shows they are capable of failing at all.
"""
from __future__ import annotations
import base64, hashlib, json, logging, sys, time, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)

from fastapi.testclient import TestClient
from sqlalchemy import select, func
import app.documents as documents
import app.main as main
from app.documents import set_extractor_override, MAX_BASE64_CHARS, MAX_FILE_BYTES
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant, DocumentUpload, UploadAttempt

REVERT = "--revert" in sys.argv
CAP = documents.MAX_BATCH_DOCUMENTS
if REVERT:
    documents.MAX_BATCH_DOCUMENTS = 10_000
    print("!! --revert: MAX_BATCH_DOCUMENTS raised to 10000. Checks 2 and 3 MUST fail.\n")

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R127-{STAMP}"
ADMIN = f"run127-{STAMP}"
PE = "2026-03-31"

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(("  ok   " if cond else "  FAIL ") + label + (f"  [{detail}]" if detail else ""))
    if not cond:
        FAILURES.append(label)


def post(p):
    return client.post("/exec", content=json.dumps(p),
                       headers={"Content-Type": "text/plain"}).json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


# ------------------------------------------------------------------------- the fixtures
#
# Plain-text documents, not PDFs: `_decode` speaks base64 only and `StubExtractor` keys on the
# sha256 of the decoded bytes, so the container format is irrelevant to what is being proved
# here and a PDF writer would only add a dependency.
#
# FIXTURE `BATCH_31`: 31 distinct one-line documents. `BATCH_30` is its first 30. Each is given
# doc_type "monthly_report" with a single stated `document_date`, which is the smallest
# extraction the merge accepts.
DOCS: list[tuple[str, bytes]] = []
OV: dict[str, tuple] = {}
for i in range(1, 32):
    fn = f"D{i:02d}_monthly_report.txt"
    raw = f"monthly report {i} stamp {STAMP}\ndocument_date: {PE}\n".encode()
    DOCS.append((fn, raw))
    OV[hashlib.sha256(raw).hexdigest()] = ("monthly_report", {"document_date": PE}, 0.95)


def entry(fn: str, raw: bytes) -> dict:
    return {"filename": fn, "mimeType": "text/plain", "dataBase64": b64(raw)}


BATCH_31 = [entry(fn, raw) for fn, raw in DOCS]
BATCH_30 = BATCH_31[:CAP]

# FIXTURE `OVERSIZE_B64`: one document whose base64 exceeds MAX_BASE64_CHARS (5,000,000), in a
# batch of three -- comfortably under the cap, so only the per-file guard can refuse it.
OVERSIZE_B64 = [
    entry(*DOCS[0]),
    {"filename": "huge.txt", "mimeType": "text/plain",
     "dataBase64": "A" * (MAX_BASE64_CHARS + 4)},
    entry(*DOCS[1]),
]

# FIXTURE `OVERSIZE_BYTES`: one document whose DECODED size exceeds MAX_FILE_BYTES (20 MB).
#
# A FINDING, RECORDED RATHER THAN PAPERED OVER. `MAX_FILE_BYTES` IS UNREACHABLE. `_decode` tests
# `len(b64) > MAX_BASE64_CHARS` BEFORE it decodes, and base64 is 4/3 the size of the bytes it
# carries, so 5,000,000 base64 chars can never decode to more than about 3,750,000 bytes -- far
# below 20 MB. Any document large enough to trip the 20 MB guard is refused by the 3 MB guard
# first, and this fixture demonstrates exactly that: it is refused, but by the base64 guard.
#
# This is NOT introduced by this run and is not repaired by it: raising MAX_BASE64_CHARS to make
# the byte guard reachable would let a ~4x larger document through, which is a change to what the
# platform accepts and belongs to its own run. What is checked here is the ARITHMETIC that makes
# one guard shadow the other, which is a claim that can be false and would become false the
# moment either constant moved.
OVERSIZE_BYTES = {"dataBase64": b64(b"x" * (MAX_FILE_BYTES + 1))}

set_extractor_override(StubExtractor(OV))

# ------------------------------------------------------------------------- the harness
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code=f"R127-A-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 127 batch cap",
                                      "signals": {}, "events": []}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
cr = post({"action": "adminparticipantcreate", "session_token": admin,
           "pseudonymous_code": f"R127-PM-{STAMP}", "role": "Participant",
           "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": cr["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": cr["participant_id"], "project_role": "PM"})

with Session() as s:
    PROJ_UUID = s.scalar(select(Project.id).where(Project.legacy_id == PID))


def counts() -> tuple[int, int]:
    with Session() as s:
        u = s.scalar(select(func.count()).select_from(DocumentUpload)
                     .where(DocumentUpload.project_id == PROJ_UUID))
        a = s.scalar(select(func.count()).select_from(UploadAttempt)
                     .where(UploadAttempt.project_id == PROJ_UUID))
    return int(u or 0), int(a or 0)


print(f"MAX_BATCH_DOCUMENTS in force: {documents.MAX_BATCH_DOCUMENTS} "
      f"(constant as shipped: {CAP})\n")

# --------------------------------------------- 2 and 3, first: the refusal must store nothing
print("REFUSAL -- fixture BATCH_31, one document over the cap")
before = counts()
r31 = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 2,
            "period_end": PE, "documents": BATCH_31})
after = counts()
check("a batch of 31 is refused", r31.get("ok") is not True,
      f"ok={r31.get('ok')} error={str(r31.get('error'))[:90]!r}")
msg = str(r31.get("error") or "")
check("the refusal names the limit", str(CAP) in msg, msg[:90])
check("the refusal names how many were sent", "31" in msg, msg[:90])
check("the refused batch wrote no document_uploads row", after[0] == before[0],
      f"{before[0]} -> {after[0]}")
check("the refused batch wrote no upload_attempts row", after[1] == before[1],
      f"{before[1]} -> {after[1]}")

# ---------------------------------------------------------- 1: exactly at the cap is accepted
print("\nACCEPTANCE -- fixture BATCH_30, exactly at the cap")
before = counts()
r30 = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
            "period_end": PE, "documents": BATCH_30})
after = counts()
check(f"a batch of exactly {CAP} is accepted", r30.get("ok") is True,
      f"ok={r30.get('ok')} error={str(r30.get('error'))[:90]!r}")
check(f"all {CAP} files come back", len(r30.get("files") or []) == CAP,
      str(len(r30.get("files") or [])))
check(f"{CAP} document_uploads rows were written", after[0] - before[0] == CAP,
      f"{before[0]} -> {after[0]}")

# --------------------------------------- 4: the per-file guards this run must not displace
print("\nPER-FILE GUARDS -- they must still fire inside an under-cap batch")
rb = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 3,
           "period_end": PE, "documents": OVERSIZE_B64})
check("MAX_BASE64_CHARS still refuses an oversize file (batch of 3)",
      rb.get("ok") is not True and "3 MB" in str(rb.get("error") or ""),
      str(rb.get("error"))[:90])
raw, problem = documents._decode(OVERSIZE_BYTES)
check("an over-20MB document is refused (by the base64 guard, see the fixture note)",
      raw is None and "3 MB" in str((problem or {}).get("error") or ""),
      str((problem or {}).get("error"))[:90])
check("MAX_BASE64_CHARS shadows MAX_FILE_BYTES: the byte guard is unreachable",
      MAX_BASE64_CHARS * 3 // 4 < MAX_FILE_BYTES,
      f"max decode {MAX_BASE64_CHARS * 3 // 4} < {MAX_FILE_BYTES}")

print()
if FAILURES:
    print(f"{len(FAILURES)} FAILED: " + "; ".join(FAILURES))
    sys.exit(1)
print("all checks passed")
