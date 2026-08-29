#!/usr/bin/env python3
"""
Run 85: the extraction cache is keyed on the bytes AND the extraction contract.

Proves, against the /exec surface with the StubExtractor (no API key here; the model call
itself is NOT exercised, the invalidation decision is):

  (a) same bytes + same contract      -> served from cache: was_cached true, no model call;
  (b) same bytes + grown contract     -> re-extracted: was_cached false, one model call, the
                                         stored row updated in place with the new fingerprint,
                                         still ONE documents row for the sha256;
  (c) non-vacuity: with the fingerprint comparison neutralised (every stored fingerprint
      forced to look current), (b) goes red for the intended reason -- the stale row is served
      from cache -- and the checks detect it.

A "grown contract" is simulated by rewriting the stored row's fingerprint to a stale value,
which is byte-for-byte what a pre-0030 row (NULL) or a row extracted under an older field list
looks like to the comparison; the fingerprint itself is derived from the real prompt builder at
call time, so a genuine field-list change produces exactly this state.

Run (from server/): DATABASE_URL=sqlite:///fresh.db SESSION_SECRET=test \
    python tools/test_run85_extraction_contract.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor, extraction_contract_fingerprint
from app.research_identity import hash_access_token
from app.research_models import Document, DocumentUpload, Participant
from app.models import Project

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


BYTES = b"%PDF-1.4 RUN85 MONTHLY REPORT - EV 4,000,000 AC 4,400,000\n"
SHA = hashlib.sha256(BYTES).hexdigest()
RECORDED = {SHA: ("monthly_report", {
    "earned_value": 4000000, "actual_cost": 4400000, "planned_value": 4500000,
    "budget_at_completion": 10000000, "report_date": "2026-06-30",
})}
stub = StubExtractor(RECORDED)
set_extractor_override(stub)

ADMIN = "run85-admin"
PROJ = "PRJ-R85"

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-R85-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PROJ)) is None:
        s.add(Project(legacy_id=PROJ, doc={"id": PROJ, "name": "Run85", "signals": {}}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "PM-R85", "role": "Participant",
                "account_type": "operational"})
assert created.get("ok"), created
pm = post({"action": "researchlogin",
           "access_token": created["access_token"]})["session_token"]
r = post({"action": "adminmemberadd", "session_token": admin, "id": PROJ,
          "participant_id": created["participant_id"], "project_role": "PM"})
assert r.get("ok"), r


def upload() -> dict:
    return post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": 1,
                 "documents": [{"filename": "monthly-06.pdf",
                                "mimeType": "application/pdf",
                                "dataBase64": b64(BYTES)}]})


print("=" * 78)
print("Run 85 — extraction cache keyed on bytes AND contract")
print("=" * 78)

print("\n(a) first upload extracts and stamps the fingerprint; re-upload is a cache hit")
stub.calls.clear()
up1 = upload()
check(up1.get("ok") is True, "first upload accepted", str(up1)[:120])
check(up1["files"][0]["was_cached"] is False, "first upload paid a model call")
check(len(stub.calls) == 1, "exactly one model call", f"calls={len(stub.calls)}")
with Session() as s:
    doc = s.scalar(select(Document).where(Document.sha256 == SHA))
    current = extraction_contract_fingerprint(doc.doc_type or "")
    check(doc.extraction_contract == current,
          "stored fingerprint equals the current contract fingerprint")
    first_extraction = dict(doc.extraction or {})

stub.calls.clear()
up2 = upload()
check(up2["files"][0]["was_cached"] is True,
      "re-upload under an unchanged contract is served from cache")
check(len(stub.calls) == 0, "no model call on the cache hit", f"calls={len(stub.calls)}")

print("\n(b) the same bytes under a GROWN contract re-extract once, updating the row")
with Session() as s:
    doc = s.scalar(select(Document).where(Document.sha256 == SHA))
    doc.extraction_contract = "0" * 64  # what an older-contract (or pre-0030 NULL) row is
    doc.extraction = {"report_date": "2026-06-30"}  # visibly the old, narrower extraction
    s.commit()
stub.calls.clear()
up3 = upload()
check(up3["files"][0]["was_cached"] is False,
      "stale-contract upload is NOT reported as cached")
check(len(stub.calls) == 1, "exactly one re-extraction model call",
      f"calls={len(stub.calls)}")
with Session() as s:
    docs = s.scalars(select(Document).where(Document.sha256 == SHA)).all()
    check(len(docs) == 1, "still exactly one documents row for the sha256",
          f"rows={len(docs)}")
    doc = docs[0]
    check(doc.extraction_contract == extraction_contract_fingerprint(doc.doc_type or ""),
          "the refreshed row carries the current fingerprint")
    check((doc.extraction or {}).get("earned_value") == 4000000,
          "the refreshed extraction carries the fields the new contract asks for",
          str(doc.extraction)[:120])

print("\n(c) non-vacuity: with the comparison neutralised, (b) goes red")
import app.documents as documents_mod
import app.extraction_client as ec

real_fp = ec.extraction_contract_fingerprint
try:
    with Session() as s:
        doc = s.scalar(select(Document).where(Document.sha256 == SHA))
        stale_value = "1" * 64
        doc.extraction_contract = stale_value
        s.commit()
    # Neutralise the comparison exactly where the seam reads it: every stored fingerprint
    # now "matches", which is the pre-Run-85 behaviour of the cache.
    documents_mod.extraction_contract_fingerprint = lambda _t: stale_value
    stub.calls.clear()
    up4 = upload()
    served_stale = up4["files"][0]["was_cached"] is True and len(stub.calls) == 0
    check(served_stale,
          "with the fingerprint comparison removed, the stale extraction is replayed "
          "(the exact defect the owner measured), so the guard above is not vacuous",
          f"was_cached={up4['files'][0]['was_cached']} calls={len(stub.calls)}")
finally:
    documents_mod.extraction_contract_fingerprint = real_fp

print("\n" + "=" * 78)
passed = sum(1 for ok, *_ in results if ok)
for ok, label, detail in results:
    if not ok:
        print(f"  FAILED: {label}  {detail}")
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
