#!/usr/bin/env python3
"""
document_risk_score is refused outside 0..1, at every point it can enter.

WHY REFUSE. The value is emitted by the extraction model and copied through; the analytical
layer bands it at 0.30 / 0.70. Before this guard there was no range check anywhere on the
server: 85 stored as 85 and pinned every project Red, "85%" stored as 85.0, and -3 stored as -3
and read as GREEN. The negative case is the dangerous one, because it fails in the reassuring
direction and nothing downstream could trace that Green back to a bad input.

The decision is REFUSE, not clamp and not store-and-flag. Clamping turns -3 into a confident
0.0; store-and-flag keeps the wrong number in the research record and relies on someone reading
the flag. Loud refusal over quiet approximation.

THREE ENTRY POINTS, and the third is the one an audit of extraction_merge alone would miss:

  1. extract_many()          the extraction boundary, where the value enters from the model
  2. assemble_signal_inputs() both merge branches, the last line before fusion
  3. overwritesignal         a live PM-gated /exec write that puts a caller-supplied value
                             into an arbitrary signalInputs field with no validation at all,
                             reaching fusion without touching a document

0 and 1 are VALID and must survive. 0 is a genuine "no concern" reading, and the prompt asks the
model for a number "between 0 and 1 inclusive".

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_doc_risk_range.py
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402

import app.main as main  # noqa: E402
from app.extraction_client import extract_many  # noqa: E402
from app.extraction_merge import (  # noqa: E402
    DOC_RISK_SCORE_MAX,
    DOC_RISK_SCORE_MIN,
    DocRiskScoreRangeError,
    assemble_signal_inputs,
    validate_doc_risk_score,
)

client = TestClient(main.app, raise_server_exceptions=False)
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


# The facade fails closed on writes as of 2026-08-02, so this suite signs in. Set at first use
# below, because the participant row has to exist before a login can succeed.
SESSION: str | None = None


def post(payload: dict) -> dict:
    body = dict(payload)
    if "session_token" not in body and SESSION:
        body["session_token"] = SESSION
    r = client.post("/exec", content=json.dumps(body), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def risk_doc(value):
    return [{"sha256": "a" * 64, "doc_type": "risk_register", "filename": "x.pdf",
             "extraction": {"document_risk_score": value, "document_date": "2026-06-30"}}]


# Values that must be REFUSED, and why each is here.
OUT_OF_RANGE = [
    (85, "a 0-100 percentage, the failure the prompt warns against"),
    ("85%", "the same, as a string the coercion strips to 85.0"),
    (100, "a percentage at its ceiling"),
    (-3, "negative: reads as the BEST band if stored, the dangerous direction"),
    (-0.0001, "just under the floor"),
    (1.0001, "just over the ceiling"),
    (2, "a small out-of-range integer, not obviously a percentage"),
]

# Values that must be ACCEPTED unchanged.
IN_RANGE = [
    (0, "the floor: a genuine no-concern reading, must be STORED not dropped"),
    (1, "the ceiling: inclusive per the extraction prompt"),
    (0.0, "the floor as a float"),
    (1.0, "the ceiling as a float"),
    (0.30, "a band edge"),
    (0.70, "the other band edge"),
    (0.42, "an ordinary mid-range value"),
]

print("test_doc_risk_range - refusal outside 0..1, at every entry point")
print()

print("1. The validator itself")
check(DOC_RISK_SCORE_MIN == 0.0 and DOC_RISK_SCORE_MAX == 1.0,
      "the contract is 0..1", f"{DOC_RISK_SCORE_MIN}..{DOC_RISK_SCORE_MAX}")
for value, why in OUT_OF_RANGE:
    raised = False
    try:
        validate_doc_risk_score(value)
    except DocRiskScoreRangeError:
        raised = True
    check(raised, f"refuses {value!r} ({why})")
for value, why in IN_RANGE:
    ok = True
    try:
        validate_doc_risk_score(value)
    except DocRiskScoreRangeError:
        ok = False
    check(ok, f"accepts {value!r} ({why})")
for value, why in [(None, "absent: the field is optional"),
                   ("", "empty: treated as absent"),
                   ("1.2.3", "unparseable: merge stores nothing anyway")]:
    ok = True
    try:
        validate_doc_risk_score(value)
    except DocRiskScoreRangeError:
        ok = False
    check(ok, f"allows {value!r} through ({why})")

print("\n2. The refusal says something the uploader can act on")
try:
    validate_doc_risk_score(85, filename="pay_app_07.pdf")
    msg = ""
except DocRiskScoreRangeError as exc:
    msg = str(exc)
check("85" in msg, "names the offending value")
check("pay_app_07.pdf" in msg, "names the file it came from")
check("0 to 1" in msg or "0.0 to 1.0" in msg, "states the required range")
check("percentage" in msg, "names the likely cause")
check("Nothing was stored" in msg, "says what happened to the document")
check("—" not in msg, "no em dash (house rule)")

print("\n3. Entry point one: the extraction boundary refuses before anything is stored")


class _FakeExtractor:
    """Returns whatever it is told to. Stands in for a model, not for a document."""
    model_id = "test/fake"

    def __init__(self, value):
        self.value = value

    def extract(self, raw, mime_type, filename, doc_type=None):
        return "risk_register", {"document_risk_score": self.value, "document_date": "2026-06-30"}


job = [{"sha256": "b" * 64, "content": b"x", "mime_type": "application/pdf",
        "filename": "risk.pdf", "doc_type": "risk_register"}]
for value, _why in OUT_OF_RANGE[:4]:
    res = extract_many(_FakeExtractor(value), job)[0]
    check(res["ok"] is False, f"extract_many marks {value!r} failed")
    check("outside the required range" in (res["error"] or ""),
          f"extract_many carries the reason for {value!r}", str(res["error"])[:70])
for value, _why in IN_RANGE[:4]:
    res = extract_many(_FakeExtractor(value), job)[0]
    check(res["ok"] is True, f"extract_many accepts {value!r}")

print("\n4. Entry point two: the merge boundary refuses, and stores valid values unchanged")
for value, _why in OUT_OF_RANGE:
    raised = False
    try:
        assemble_signal_inputs(risk_doc(value))
    except DocRiskScoreRangeError:
        raised = True
    check(raised, f"assemble_signal_inputs refuses {value!r}")
for value, _why in IN_RANGE:
    si = assemble_signal_inputs(risk_doc(value))
    check(si.get("docRiskScore") == value,
          f"assemble_signal_inputs stores {value!r} unchanged", str(si.get("docRiskScore")))

# The other branch. commissioning_report sets docRiskScore and deliberately no docDate, so it
# is a separate code path and a guard on the shared branch alone would leave it open.
print("\n5. The commissioning_report branch is guarded too, not just the shared one")


def commissioning_doc(value):
    return [{"sha256": "c" * 64, "doc_type": "commissioning_report", "filename": "c.pdf",
             "extraction": {"document_risk_score": value}}]


for value, _why in OUT_OF_RANGE[:4]:
    raised = False
    try:
        assemble_signal_inputs(commissioning_doc(value))
    except DocRiskScoreRangeError:
        raised = True
    check(raised, f"commissioning_report branch refuses {value!r}")
check(assemble_signal_inputs(commissioning_doc(0.5)).get("docRiskScore") == 0.5,
      "commissioning_report branch stores a valid value")

print("\n6. Entry point three: overwritesignal, the path that never touches a document")
PID = "PRJ-DOCRISK01"
_WRITER = "docrisk-writer-token"
with main.SessionFactory() as _s:
    from app.research_models import Participant as _P
    from app.research_identity import hash_access_token as _h
    _s.add(_P(pseudonymous_code="DOCRISK-WRITER", role="Participant",
              account_type="operational", access_token_hash=_h(_WRITER)))
    _s.commit()
SESSION = client.post("/exec", content=json.dumps(
    {"action": "researchlogin", "username": "DOCRISK-WRITER", "password": _WRITER}),
    headers={"Content-Type": "text/plain"}).json()["session_token"]
post({"action": "create", "id": PID, "name": "Doc risk range", "sector": "Aviation"})

# SEED signalInputs FIRST. w_overwritesignal returns "No extracted signals to overwrite" on an
# empty set, and that refusal happens BEFORE the range guard. Without this seed every check
# below would pass for the wrong reason: the action would refuse 85 because the project has no
# signals, not because 85 is out of range, and the suite would be green with the guard deleted.
# Reads are authenticated as of 2026-08-02; the credential goes in a header, not the query string.
doc = client.get("/exec", params={"action": "get", "id": PID},
                 headers={"Authorization": "Bearer " + SESSION}).json()["project"]
doc["signals"] = {"evm": {"cpi": 0.9}}
doc["signalInputs"] = {"cpi": 0.9, "docRiskScore": 0.4}
post({"action": "save", "project": doc})

seed = post({"action": "overwritesignal", "id": PID, "field": "docRiskScore",
             "value": 0.55, "reason": "seed"})
check(seed.get("ok") is True and seed.get("to") == 0.55,
      "a valid docRiskScore can be set", str(seed)[:120])

for value, _why in OUT_OF_RANGE[:4]:
    r = post({"action": "overwritesignal", "id": PID, "field": "docRiskScore",
              "value": value, "reason": "test"})
    check(r.get("ok") is not True, f"overwritesignal refuses {value!r}", str(r)[:100])
    check("outside the required range" in (r.get("error") or ""),
          f"overwritesignal explains the refusal for {value!r}", str(r.get("error"))[:70])

# And the refusal must not have written anything. Read back independently rather than trusting
# the refusal's own response: the point is what is in storage, not what the handler said.
stored = client.get("/exec", params={"action": "get", "id": PID},
                    headers={"Authorization": "Bearer " + SESSION}).json()
check(stored["project"]["signalInputs"]["docRiskScore"] == 0.55,
      "a refused overwrite left the stored value untouched",
      str(stored["project"]["signalInputs"].get("docRiskScore")))

# Other fields are deliberately NOT range-checked here: this guard is about one field with one
# known contract, not a general validation layer that would need a decision per field.
other = post({"action": "overwritesignal", "id": PID, "field": "cpi",
              "value": 0.85, "reason": "unrelated field"})
check(other.get("ok") is True, "an unrelated field is unaffected by the guard", str(other)[:100])

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
