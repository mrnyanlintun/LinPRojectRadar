#!/usr/bin/env python3
"""
Document versioning: a revision supersedes, computation uses the latest, the old stays readable.

THE DEFECT, AS MEASURED BEFORE THIS WAS BUILT. A revised document did not replace the one it
revised and did not collide with it. Both were stored, and BOTH reached computation, because
`_period_documents` filtered on (project, period) and de-duplicated on sha256 only. Which
version's figures survived was then decided by `_ordered_docs`'s sort key, whose tiebreak for two
documents of the same type is the SHA256 -- a content hash:

  * first-wins fields took the LOWER hash, last-wins fields the HIGHER (opposite directions),
  * additive fields counted BOTH (an RFI log revised from 10 to 12 assembled to 22),
  * a downward correction to a keep_max field was discarded.

So one revision could produce a signalInputs mixing both versions, deterministically. Section 1
below reproduces that against the pure merge function, so the suite carries the evidence for why
the mechanism exists rather than only testing the mechanism.

THE VACUOUS-CHECK TRAP. The last three sessions each shipped a check that passed for the wrong
reason. The specific trap here: a supersede test can pass because the superseding document
happened to win the sha256 tiebreak anyway, proving nothing. Every fixture below is therefore
built so that WITHOUT supersession the ORIGINAL wins -- the hashes are chosen and asserted, not
hoped for. Section 2 asserts that precondition explicitly, so if a fixture ever stops having it,
this suite fails rather than going quietly green.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_document_versioning.py
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
from app.extraction_merge import assemble_signal_inputs  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


print("=" * 78)
print("Document versioning")
print("=" * 78)

# ---------------------------------------------------------------- section 1: the defect

print("\n1. The defect this exists to fix, reproduced against the pure merge")


def monthly(sha: str, ev: int) -> dict:
    return {"sha256": sha, "doc_type": "monthly_report", "filename": "m.pdf",
            "extraction": {"earned_value": ev, "actual_cost": 4_000_000,
                           "planned_value": 5_000_000, "budget_at_completion": 10_000_000,
                           "report_date": "2026-06-30"}}


# STORAGE REDESIGN (0014). This section used to REPRODUCE the pre-0013 defects — the sha256
# deciding which revision wins, and an additive field double-counting a revision. Both are
# now asserted DEAD: recency on the value's own date decides between dated revisions
# (regardless of hash), and register totals replace rather than sum.

LOW, HIGH = "0" * 64, "f" * 64


def monthly_dated(sha: str, ev: int, report_date: str) -> dict:
    d = monthly(sha, ev)
    d["extraction"]["report_date"] = report_date
    return d


# The LOWER hash carries the LATER date: under the old fold the hash decided; now the date does.
si_recency = assemble_signal_inputs([monthly_dated(LOW, 5_000_000, "2026-06-30"),
                                     monthly_dated(HIGH, 4_000_000, "2026-05-31")])
check(si_recency["ev"] == 5_000_000,
      "between dated revisions, recency wins — the sha256 no longer decides",
      f"ev={si_recency['ev']}")


def rfi_log(sha: str, total: int) -> dict:
    return {"sha256": sha, "doc_type": "rfi_log", "filename": "r.pdf",
            "extraction": {"rfi_total": total, "log_date": "2026-06-30"}}


def rfi(sha: str, count: int) -> dict:
    return {"sha256": sha, "doc_type": "rfi", "filename": "r.pdf",
            "extraction": {"rfi_count": count, "document_date": "2026-06-30"}}


# A register revised within one period yields the revised figure, NEVER the sum (10 then 12
# is 12, not 22) — and the individual rfi form contributes nothing at all: it routes to
# unmapped, so the accumulating branch and the "rfi" < "rfi_log" ordering dependency are gone.
si_reg = assemble_signal_inputs([rfi_log("1" * 64, 10), rfi_log("2" * 64, 12)])
check(si_reg["rfiCount"] == 12,
      "a register revised within one period yields the revised figure, not the sum",
      str(si_reg["rfiCount"]))
si_ind = assemble_signal_inputs([rfi("1" * 64, 10), rfi("2" * 64, 12)])
check(si_ind["rfiCount"] is None,
      "individual rfi forms route to unmapped and contribute nothing",
      str(si_ind["rfiCount"]))

# ---------------------------------------------------------------- fixtures

PROJ = "PRJ-DOCVER01"
ADMIN = "docver-admin-token"

# Two versions of one monthly report. ORIGINAL says EV 4.0M (cpi 1.00); REVISION says 5.0M
# (cpi 1.25). The bytes are chosen below so the ORIGINAL's sha256 sorts LOWER, which means the
# original wins the tiebreak and therefore wins if supersession does nothing at all.
ORIGINAL_EV, REVISED_EV = 4_000_000, 5_000_000


def find_ordered_pair() -> tuple[bytes, bytes]:
    """Bytes whose hashes make the ORIGINAL win the deterministic same-date tiebreak (higher
    hash, the fold's historical last-write order), so an unsuperseded original wins and the
    later supersedes claim is provably what flips the outcome. Both versions carry the SAME
    report_date — an undeclared revision with a LATER date now wins on recency alone, which
    section 1 asserts; this fixture is the equal-date case where only a declaration can."""
    for i in range(2000):
        a = f"%PDF-1.4 MONTHLY REPORT ORIGINAL {i}\n".encode()
        b = f"%PDF-1.4 MONTHLY REPORT REVISION {i}\n".encode()
        if hashlib.sha256(a).hexdigest() > hashlib.sha256(b).hexdigest():
            return a, b
    raise AssertionError("no ordered pair found")


ORIGINAL_BYTES, REVISED_BYTES = find_ordered_pair()
ORIGINAL_SHA = hashlib.sha256(ORIGINAL_BYTES).hexdigest()
REVISED_SHA = hashlib.sha256(REVISED_BYTES).hexdigest()


def report_fields(ev: int) -> dict:
    return {"earned_value": ev, "actual_cost": 4_000_000, "planned_value": 5_000_000,
            "budget_at_completion": 10_000_000, "actual_percent_complete": 40.0,
            "planned_percent_complete": 50.0, "report_date": "2026-06-30"}


RECORDED = {
    ORIGINAL_SHA: ("monthly_report", report_fields(ORIGINAL_EV)),
    REVISED_SHA: ("monthly_report", report_fields(REVISED_EV)),
}
set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="DOCVER-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PROJ)) is None:
        s.add(Project(legacy_id=PROJ, doc={"id": PROJ, "name": "Doc versioning", "signals": {}}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "DOCVER-PM", "role": "Participant",
                "account_type": "operational"})
pm_id = created["participant_id"]
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PROJ,
      "participant_id": pm_id, "project_role": "PM"})

print("\n2. The fixture is built so the ORIGINAL wins without supersession")
check(ORIGINAL_SHA > REVISED_SHA,
      "the original wins the equal-date tiebreak unaided (higher hash, last-write order)",
      f"{ORIGINAL_SHA[:8]} > {REVISED_SHA[:8]}")
# The precondition, proved against the merge rather than assumed from the hash ordering.
si_unsuperseded = assemble_signal_inputs([
    {"sha256": ORIGINAL_SHA, "doc_type": "monthly_report", "filename": "o.pdf",
     "extraction": report_fields(ORIGINAL_EV)},
    {"sha256": REVISED_SHA, "doc_type": "monthly_report", "filename": "r.pdf",
     "extraction": report_fields(REVISED_EV)},
])
check(si_unsuperseded["ev"] == ORIGINAL_EV,
      "PRECONDITION: with both present and neither superseded, the ORIGINAL's figure wins",
      f"ev={si_unsuperseded['ev']}")

# ---------------------------------------------------------------- section 3: upload + compute

print("\n3. The original alone computes from the original")
up1 = post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": 1,
            "documents": [{"filename": "monthly-06.pdf", "mimeType": "application/pdf",
                           "dataBase64": b64(ORIGINAL_BYTES)}]})
check(up1.get("ok") is True, "original uploaded", str(up1)[:120])
original_doc_id = post({"action": "projectuploadstatus", "session_token": pm,
                        "id": PROJ, "period": 1})["documents"][0]["document_id"]
check(bool(original_doc_id), "original has a document_id", str(original_doc_id))

c1 = post({"action": "projectcompute", "session_token": pm, "id": PROJ, "period": 1})
check(c1.get("ok") is True, "first compute succeeded", str(c1)[:120])
r1 = post({"action": "projectresults", "session_token": pm, "id": PROJ, "period": 1})["result"]
check(r1["signal_inputs"]["ev"] == ORIGINAL_EV,
      "computation used the original's earned value", str(r1["signal_inputs"]["ev"]))
cpi_before = r1["signal_inputs"]["cpi"]

print("\n4. A revision that supersedes: computation uses the LATEST")
up2 = post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": 1,
            "documents": [{"filename": "monthly-06-rev1.pdf", "mimeType": "application/pdf",
                           "dataBase64": b64(REVISED_BYTES),
                           "supersedes": original_doc_id}]})
check(up2.get("ok") is True, "revision uploaded with an explicit supersedes claim", str(up2)[:150])

# adminrecompute, because projectcompute refuses when a live result already exists and a
# recompute must carry a stated reason to be auditable.
c2 = post({"action": "adminrecompute", "session_token": admin, "id": PROJ, "period": 1,
           "reason": "revised monthly report supersedes the original"})
check(c2.get("ok") is True, "recompute succeeded", str(c2)[:150])
r2 = post({"action": "projectresults", "session_token": pm, "id": PROJ, "period": 1})["result"]
ev_after = r2["signal_inputs"]["ev"]
check(ev_after == REVISED_EV,
      "computation now uses the REVISION's earned value, not the original's",
      f"ev={ev_after}, expected {REVISED_EV}")
check(r2["signal_inputs"]["cpi"] != cpi_before,
      "the computed cpi actually moved", f"{cpi_before} -> {r2['signal_inputs']['cpi']}")

print("\n5. The superseded document is still readable, and is out of computation")
status = post({"action": "projectuploadstatus", "session_token": pm, "id": PROJ, "period": 1})
live_ids = [d["document_id"] for d in status["documents"]]
sup = status.get("superseded") or []
check(original_doc_id not in live_ids,
      "the superseded document is no longer in the live set", str(live_ids))
check(len(sup) == 1 and sup[0]["document_id"] == original_doc_id,
      "the superseded document is still listed and readable", str(sup)[:160])
check(sup and sup[0]["contributes"] is False,
      "it is marked as contributing nothing")
check(sup and sup[0]["filename"] == "monthly-06.pdf",
      "its filename is still available", str(sup[0].get("filename") if sup else None))
check(sup and sup[0]["superseded_by_document_id"] in live_ids,
      "it names the version that replaced it, and that version is live",
      str(sup[0].get("superseded_by_document_id") if sup else None))

# Readability that matters most: the bytes and the extraction must still be in the database.
# Deleting a superseded document would make a decision recorded against it unreproducible,
# which is the property the About tab states.
with Session() as s:
    from app.research_models import Document as _Doc
    kept = s.scalar(select(_Doc).where(_Doc.document_id == original_doc_id))
check(kept is not None, "the superseded document row was not deleted")
check(kept is not None and kept.content == ORIGINAL_BYTES,
      "its original bytes are retained verbatim")
check(kept is not None and (kept.extraction or {}).get("earned_value") == ORIGINAL_EV,
      "its extraction is retained, so what was shown can be reproduced",
      str((kept.extraction or {}).get("earned_value") if kept else None))

print("\n6. The stored result says which document versions produced it")
res = post({"action": "projectresults", "session_token": pm, "id": PROJ, "period": 1})
src = (res.get("result") or {}).get("source_documents")
check(isinstance(src, list) and len(src) == 1,
      "the live result names exactly one source document", str(src)[:160])
check(src and src[0]["sha256"] == REVISED_SHA,
      "and it is the REVISION, identified by content hash",
      str(src[0].get("sha256")[:12] if src else None))
check(src and src[0]["document_id"] != original_doc_id,
      "the superseded document is not credited with producing the live result")

print("\n7. A supersedes claim is validated, not trusted")
bad = post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": 1,
            "documents": [{"filename": "x.pdf", "mimeType": "application/pdf",
                           "dataBase64": b64(b"%PDF-1.4 UNRELATED\n"),
                           "supersedes": "01JQZZZZZZZZZZZZZZZZZZZZZZ"}]})
check(bad.get("ok") is not True, "an unknown supersedes id is refused", str(bad)[:120])
check("cannot supersede" in (bad.get("error") or ""),
      "the refusal names the problem", str(bad.get("error"))[:110])

# A document from ANOTHER period is not supersedable from this one: supersession is scoped to
# (project, period), and a claim across periods would silently drop evidence from a period the
# uploader is not even looking at.
post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": 2,
      "documents": [{"filename": "p2.pdf", "mimeType": "application/pdf",
                     "dataBase64": b64(ORIGINAL_BYTES)}]})
cross = post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": 3,
              "documents": [{"filename": "p3.pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(REVISED_BYTES),
                             "supersedes": original_doc_id}]})
check(cross.get("ok") is not True,
      "a claim against a document in a different period is refused", str(cross)[:130])

print("\n8. Nothing changed for a period with no supersession")
status2 = post({"action": "projectuploadstatus", "session_token": pm, "id": PROJ, "period": 2})
check(status2.get("superseded") == [],
      "a period with no revisions reports an empty superseded list",
      str(status2.get("superseded")))
check(len(status2["documents"]) == 1,
      "and its live document set is unchanged", str(len(status2["documents"])))

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
