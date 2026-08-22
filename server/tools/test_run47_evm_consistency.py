#!/usr/bin/env python3
"""
RUN 47. THE EVM CONSISTENCY CHECK, DRIVEN THROUGH THE REAL ROUTES.

WHAT THIS SUITE EXISTS TO PROTECT. A document that states both a value and the percentage that
determines it against a known budget at completion can disagree with itself, and until Run 47
the platform stored both figures and never compared them. Schedule performance is earned value
over planned value, so a planned value 24 per cent low reads a project as ahead of schedule
when the same document's percentages say it is behind.

THE RULES THIS SUITE HOLDS ITSELF TO.

  * EVERY EXPECTED VALUE IS HAND-COMPUTED FROM THE STATED FORMULA and written here as a
    literal. Nothing is read back from `evm_consistency` and compared with itself, and no
    generated output validates itself against its own generator.
  * THE ARITHMETIC IN THE ORDER WAS RE-DERIVED RATHER THAN COPIED. The order states the implied
    `ev` as 1,066,671. Executed: 5,874,620 x 0.1816 = 1,066,830.992, and the relative
    difference against a stated 1,046,735 is 1.8837 per cent, not the order's 1.9 per cent read
    off 1,066,671. Either figure is below the 2 per cent tolerance, so the verdict the order
    requires (no finding) is unchanged; the FIGURE asserted below is the one this suite
    computed, and the discrepancy is recorded in the Run 47 report.
  * THE DENOMINATOR IS THE IMPLIED VALUE. `|stated - implied| / |implied|`. The boundary checks
    in section 3 exercise that reading and no other: relative to the STATED value the same two
    fixtures read 2.04 and 2.05 per cent, so a check written against the wrong denominator
    fails here rather than passing quietly.
  * A FIXTURE IS BUILT THROUGH THE ROUTES THE APPLICATION ACTUALLY TAKES: `researchlogin`,
    `adminparticipantcreate`, `adminmemberadd`, `projectupload`, `projectcomputeall`,
    `projectresults`. Extraction is stubbed, which is the one substitution every suite in this
    repository makes; everything downstream of it is the production path.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run47_evm_consistency.py
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
import app.documents as documents  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.evm_consistency import CONSISTENCY_RELATIONS, TOLERANCE, consistency_findings  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, registry_index, service_index,
)

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


# --------------------------------------------------------------- the figures
#
# THE RENDER'S OWN FOUR FIGURES, as the order states them. Hand-computed expectations follow.
BAC = 5_874_620
PV_STATED = 824_370
PLANNED_PCT = 18.47
EV_STATED = 1_046_735
ACTUAL_PCT = 18.16
AC_STATED = 857_930

#: 5,874,620 x 18.47 / 100. Long division, not a call into the module under test:
#:   5,874,620 x 18   = 105,743,160
#:   5,874,620 x 0.47 =   2,761,071.4
#:   sum / 100        =   1,085,042.314
PV_IMPLIED = 1_085_042.314
#: |824,370 - 1,085,042.314| = 260,672.314; / 1,085,042.314 = 0.24024161...
PV_DIFF_PCT = 24.024161144373586

#: 5,874,620 x 18.16 / 100:
#:   5,874,620 x 18   = 105,743,160
#:   5,874,620 x 0.16 =     939,939.2
#:   sum / 100        =   1,066,830.992
#: THE ORDER SAYS 1,066,671. IT IS WRONG BY 159.992, and the figure asserted is the one
#: computed here. The verdict is unaffected: both give a difference below 2 per cent.
EV_IMPLIED = 1_066_830.992
#: |1,046,735 - 1,066,830.992| = 20,095.992; / 1,066,830.992 = 0.018837090...
EV_DIFF_PCT = 1.8837090552015088

#: The boundary fixture. A round budget at completion so both sides are exact in binary.
B_BAC = 1_000_000
B_PCT = 10.0                 # implies 100,000
B_AT_TOLERANCE = 98_000      # |98,000 - 100,000| / 100,000 = 0.02 exactly. NO finding.
B_OVER_TOLERANCE = 97_990    # |97,990 - 100,000| / 100,000 = 0.0201. A finding.
B_OVER_DIFF_PCT = 2.01

PERIOD_END = {1: "2026-03-31", 2: "2026-04-30", 3: "2026-05-31", 4: "2026-06-30"}

ADMIN = "run47-admin-token"
D = "PRJ-R47-DISAGREE"   # the render's figures: pv disagrees, ev does not
A = "PRJ-R47-AGREE"      # the same shape with a pv the percentage implies
N = "PRJ-R47-NOBAC"      # a disagreeing pair with no contract anywhere: no finding, no error
S = "PRJ-R47-SPLIT"      # value and percentage from DIFFERENT documents
B = "PRJ-R47-BOUNDARY"   # exactly 2 per cent, and 2.01 per cent

CONTRACT = {"original_contract_sum": BAC,
            "project_start_date": "2026-01-01", "project_end_date": "2027-06-30"}
B_CONTRACT = {"original_contract_sum": B_BAC,
              "project_start_date": "2026-01-01", "project_end_date": "2027-06-30"}


def tps(pv: float, pct: float, period: int) -> dict:
    """A Time-phased Schedule stating BOTH figures, which is the shape the check is about."""
    return {"planned_value_to_date": pv, "planned_percent_complete": pct,
            "data_date": PERIOD_END[period], "document_date": PERIOD_END[period]}


def payapp(period: int) -> dict:
    return {"amount_paid_to_date": AC_STATED, "completed_to_date": EV_STATED,
            "percent_complete_verified": ACTUAL_PCT,
            "application_date": PERIOD_END[period], "document_date": PERIOD_END[period]}


#: (project, tag, period, doc_type, extraction)
DOCS: list[tuple[str, str, int, str, dict]] = [
    # D: the render. pv 824,370 against a planned 18.47; ev 1,046,735 against an actual 18.16.
    (D, "contract", 1, "contract_value", CONTRACT),
    (D, "tps4", 4, "time_phased_schedule", tps(PV_STATED, PLANNED_PCT, 4)),
    (D, "payapp4", 4, "pay_application", payapp(4)),
    # A: IDENTICAL IN EVERY OTHER RESPECT, with the planned value the percentage implies. The
    # control for the census comparison and for "a check that fires on everything is not a
    # check".
    (A, "contract", 1, "contract_value", CONTRACT),
    (A, "tps4", 4, "time_phased_schedule", tps(1_085_042, PLANNED_PCT, 4)),
    (A, "payapp4", 4, "pay_application", payapp(4)),
    # N: the SAME disagreeing pair, and no document anywhere states a contract sum.
    (N, "tps4", 4, "time_phased_schedule", tps(PV_STATED, PLANNED_PCT, 4)),
    # S: the value and the percentage in two different documents. The Time-phased Schedule
    # states the planned value and no percentage; the Monthly Progress Report states the
    # percentage and no planned value.
    (S, "contract", 1, "contract_value", CONTRACT),
    (S, "tps4", 4, "time_phased_schedule",
     {"planned_value_to_date": PV_STATED,
      "data_date": PERIOD_END[4], "document_date": PERIOD_END[4]}),
    (S, "mr4", 4, "monthly_report",
     {"planned_percent_complete": PLANNED_PCT,
      "report_date": PERIOD_END[4], "document_date": PERIOD_END[4]}),
    # B: the tolerance boundary, both sides of it, on a round budget at completion.
    (B, "contract", 1, "contract_value", B_CONTRACT),
    (B, "tps3", 3, "time_phased_schedule", tps(B_AT_TOLERANCE, B_PCT, 3)),
    (B, "tps4", 4, "time_phased_schedule", tps(B_OVER_TOLERANCE, B_PCT, 4)),
]


def doc_bytes(project: str, tag: str) -> bytes:
    return f"%PDF-1.4 RUN47 {project} {tag}\n".encode()


RECORDED: dict[str, tuple[str, dict]] = {
    hashlib.sha256(doc_bytes(_p, _tag)).hexdigest(): (_type, _ex)
    for _p, _tag, _per, _type, _ex in DOCS
}
set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R47-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy in (D, A, N, S, B):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy,
                          doc={"id": legacy, "name": legacy, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R47-PM", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
for legacy in (D, A, N, S, B):
    post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
          "participant_id": created["participant_id"], "project_role": "PM"})

for _p, _tag, _per, _type, _ex in DOCS:
    r = post({"action": "projectupload", "session_token": pm, "id": _p, "period": _per,
              "period_end": PERIOD_END[_per],
              "documents": [{"filename": f"{_p}-{_tag}.pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(doc_bytes(_p, _tag))}]})
    assert r.get("ok") is True, str(r)[:300]

for _legacy in (D, A, N, S, B):
    _r = post({"action": "projectcomputeall", "session_token": pm, "id": _legacy})
    assert _r.get("ok") is True, str(_r)[:300]


def result(legacy: str, period: int) -> dict:
    r = post({"action": "projectresults", "session_token": pm, "id": legacy, "period": period})
    assert r.get("ok") is True, str(r)[:300]
    return r["result"]


def findings(legacy: str, period: int) -> list[dict]:
    return result(legacy, period).get("consistency_findings") or []


def census(res: dict) -> str:
    """THE FULL CENSUS OF A SERVED RESULT, as a stable string.

    Every band, status, colour, posture and abstention the result carries, and every module
    result in it, in a canonical order. `consistency_findings` is DELIBERATELY excluded: it is
    the thing being added, and including it would make the comparison trivially unequal and
    prove nothing. Everything else is in.
    """
    keep = {k: v for k, v in res.items()
            if k not in ("consistency_findings", "computed_at", "result_id")}
    return json.dumps(keep, sort_keys=True, default=str)


try:
    print("=" * 78)
    print("1. A DOCUMENT THAT DISAGREES WITH ITSELF BY MORE THAN 2 PER CENT (S8.1, S8.4)")
    print("=" * 78)

    f4 = findings(D, 4)
    pv_f = next((x for x in f4 if x["field"] == "pv"), None)
    check(pv_f is not None, "the render's planned value produces a disagreement finding",
          str(f4)[:200])
    if pv_f:
        check(pv_f["statedValue"] == PV_STATED,
              f"the stated value is reported as {PV_STATED:,}, exactly as stored",
              str(pv_f["statedValue"]))
        check(abs(pv_f["impliedValue"] - PV_IMPLIED) < 1e-6,
              f"the implied value is {PV_IMPLIED:,}, hand-computed from BAC x planned per cent",
              str(pv_f["impliedValue"]))
        check(abs(pv_f["differencePct"] - PV_DIFF_PCT) < 1e-9,
              f"the relative difference is {PV_DIFF_PCT:.6f} per cent",
              str(pv_f["differencePct"]))
        check(pv_f["documentType"] == "time_phased_schedule",
              "the document that stated both figures is named by type",
              str(pv_f["documentType"]))
        check(bool(pv_f["documentId"]), "the document is named by identity too",
              str(pv_f["documentId"]))
        check(pv_f["period"] == 4, "the finding carries its period", str(pv_f["period"]))
        check("24.0 percent" in pv_f["sentence"],
              "the sentence states the difference as 24.0 percent", pv_f["sentence"][:160])
        check(not any(k in pv_f for k in ("status", "band", "colour", "color", "severity")),
              "the finding carries no band, no colour and no severity", str(sorted(pv_f)))

    print()
    print("=" * 78)
    print("2. THE RENDER'S EARNED VALUE PRODUCES NO FINDING (S8.5)")
    print("=" * 78)

    check(not any(x["field"] == "ev" for x in f4),
          f"earned value {EV_STATED:,} against an implied {EV_IMPLIED:,} "
          f"({EV_DIFF_PCT:.4f} per cent) is below tolerance and is not reported",
          str([x['field'] for x in f4]))
    # The pair is REACHABLE: it is refused on the tolerance, not on a missing precondition.
    _si_d = result(D, 4)["signal_inputs"]
    _src = _si_d.get("sources") or {}
    check(_si_d.get("ev") == EV_STATED and _si_d.get("actualPctComplete") == ACTUAL_PCT
          and (_src.get("ev") or {}).get("documentId")
          == (_src.get("actualPctComplete") or {}).get("documentId"),
          "and the earned-value pair IS present and IS from one document, so the refusal is "
          "the tolerance and not an absent precondition")

    print()
    print("=" * 78)
    print("3. THE TOLERANCE BOUNDARY, BOTH SIDES (S8.2, S8.3)")
    print("=" * 78)

    check(TOLERANCE == 0.02, "the tolerance is 2 per cent", str(TOLERANCE))
    check(findings(B, 3) == [],
          f"a difference of exactly 2 per cent ({B_AT_TOLERANCE:,} against an implied "
          f"{B_BAC * B_PCT / 100:,.0f}) produces NO finding", str(findings(B, 3))[:200])
    b4 = findings(B, 4)
    check(len(b4) == 1 and b4[0]["field"] == "pv",
          f"a difference of 2.01 per cent ({B_OVER_TOLERANCE:,} against an implied "
          f"{B_BAC * B_PCT / 100:,.0f}) produces a finding", str(b4)[:200])
    if b4:
        check(abs(b4[0]["differencePct"] - B_OVER_DIFF_PCT) < 1e-9,
              "and reports it as 2.01 per cent", str(b4[0]["differencePct"]))
        check("2.01 percent" in b4[0]["sentence"],
              "the sentence prints 2.01, not a rounded 2.0", b4[0]["sentence"][:200])

    print()
    print("=" * 78)
    print("4. THE TWO CONDITIONS ON EVERY CHECK (S8.7, S5.2)")
    print("=" * 78)

    _si_n = result(N, 4)["signal_inputs"]
    check(_si_n.get("bac") is None,
          "the no-contract project stores an ABSENT budget at completion, present and null",
          str(_si_n.get("bac")))
    check(_si_n.get("pv") == PV_STATED and _si_n.get("plannedPctComplete") == PLANNED_PCT,
          "and it holds the same disagreeing pair, so the refusal is the absent budget",
          f"pv={_si_n.get('pv')} pct={_si_n.get('plannedPctComplete')}")
    check(findings(N, 4) == [],
          "an absent budget at completion produces NO finding and NO error",
          str(findings(N, 4))[:200])

    _si_s = result(S, 4)["signal_inputs"]
    _ssrc = _si_s.get("sources") or {}
    _pv_doc = (_ssrc.get("pv") or {}).get("documentId")
    _pct_doc = (_ssrc.get("plannedPctComplete") or {}).get("documentId")
    check(_si_s.get("pv") == PV_STATED and _si_s.get("plannedPctComplete") == PLANNED_PCT
          and _si_s.get("bac") == BAC,
          "the split project holds the same disagreeing pair against a known budget",
          f"pv={_si_s.get('pv')} pct={_si_s.get('plannedPctComplete')} bac={_si_s.get('bac')}")
    check(bool(_pv_doc) and bool(_pct_doc) and _pv_doc != _pct_doc,
          "and the two figures demonstrably came from two DIFFERENT documents",
          f"{_pv_doc} vs {_pct_doc}")
    check(findings(S, 4) == [],
          "a value and a percentage from different documents is NOT reported as a "
          "disagreement in this run", str(findings(S, 4))[:200])

    print()
    print("=" * 78)
    print("5. NOTHING IS DERIVED INTO STORAGE (S8.6)")
    print("=" * 78)

    check(_si_d.get("pv") == PV_STATED,
          f"pv is stored as the document stated it, {PV_STATED:,}, not the implied "
          f"{PV_IMPLIED:,}", str(_si_d.get("pv")))
    check(_si_d.get("plannedPctComplete") == PLANNED_PCT,
          "and the percentage is stored as stated too", str(_si_d.get("plannedPctComplete")))
    check(_si_d.get("spi") == round(EV_STATED / PV_STATED, 3),
          "schedule performance is still earned value over the STORED planned value, "
          f"{round(EV_STATED / PV_STATED, 3)}, unaltered by the finding", str(_si_d.get("spi")))
    _before = census(result(D, 4))
    _rec = post({"action": "projectcomputeall", "session_token": pm, "id": D})
    assert _rec.get("ok") is True, str(_rec)[:300]
    _after_si = result(D, 4)["signal_inputs"]
    check(json.dumps(_si_d, sort_keys=True, default=str)
          == json.dumps(_after_si, sort_keys=True, default=str),
          "a full recompute after the check exists stores byte-identical signal inputs")

    print()
    print("=" * 78)
    print("6. A DISAGREEMENT CHANGES NO BAND, STATUS, COLOUR OR POSTURE (S8.8, S8.9)")
    print("=" * 78)

    _res_with = result(D, 4)
    _with = census(_res_with)
    _real = documents.consistency_findings
    try:
        documents.consistency_findings = lambda si, period=None: []
        _res_without = result(D, 4)
    finally:
        documents.consistency_findings = _real
    check((_res_with.get("consistency_findings") or []) != [],
          "the disagreement IS present on the served result, so the comparison is not vacuous")
    check((_res_without.get("consistency_findings") or []) == [],
          "and the suppressed serve carries none, so the two serves genuinely differ in it")
    check(census(_res_without) == _with,
          "THE FULL CENSUS WITH AND WITHOUT THE DISAGREEMENT IS IDENTICAL: every module "
          "result, every category status, every band, every colour, every posture and every "
          "abstention")
    check(_res_with.get("project_status") == _res_without.get("project_status"),
          "project status unchanged", str(_res_with.get("project_status")))
    check(_res_with.get("category_statuses") == _res_without.get("category_statuses"),
          "category statuses unchanged")
    check((_res_with.get("abstained") or []) == (_res_without.get("abstained") or []),
          "NO MODULE ABSTAINS THAT WOULD OTHERWISE COMPUTE: the abstention list is identical",
          str(len(_res_with.get("abstained") or [])))
    check(_res_with.get("recommendation_basis") == _res_without.get("recommendation_basis"),
          "the recommendation's own basis is unchanged")
    _res_a = result(A, 4)
    check((_res_a.get("consistency_findings") or []) == [],
          "the agreeing control project reports nothing, so the check does not fire on "
          "everything", str(_res_a.get("consistency_findings"))[:200])

    print()
    print("=" * 78)
    print("7. THE WORDING (S8.11, NAMING_AUTHORITY)")
    print("=" * 78)

    _sentences = [x["sentence"] for x in f4 + b4]
    check(bool(_sentences), "there is wording to check", str(len(_sentences)))
    import re as _re
    _bad_id = _re.compile(r"\bCat\s*\d|\b[A-D]\d\.\d|\bPH\.\d")
    for _s in _sentences:
        check(not _bad_id.search(_s), "no module identifier and no number-scheme label",
              _s[:120])
        check("—" not in _s and "--" not in _s, "no em dash", _s[:120])
        check("should" not in _s.lower() and "wrong" not in _s.lower()
              and "incorrect" not in _s.lower() and "error" not in _s.lower(),
              "does not tell the reader what to conclude and asserts no figure is wrong",
              _s[:120])

    print()
    print("=" * 78)
    print("8. THE RELATIONS THE SWEEP FOUND (S5)")
    print("=" * 78)

    _pairs = {(r["value_field"], r["pct_field"]) for r in CONSISTENCY_RELATIONS}
    check(_pairs == {("pv", "plannedPctComplete"), ("ev", "actualPctComplete")},
          "exactly two relations are checked, and they are the two the order names",
          str(sorted(_pairs)))
    # THE SWEEP, RE-EXECUTED AGAINST THE LIVE EMISSION TABLE rather than transcribed. Every
    # document type that emits BOTH members of a checked pair must be reachable by the check.
    from app.extraction_merge import _NUMERIC_EMISSIONS  # noqa: E402
    for _vf, _pf in sorted(_pairs):
        _writers = sorted(dt for dt, pairs in _NUMERIC_EMISSIONS.items()
                          if _vf in {f for _, f in pairs} and _pf in {f for _, f in pairs})
        check(bool(_writers), f"at least one document type states {_vf} and {_pf} together",
              str(_writers))
        print(f"        {_vf} x {_pf}: {', '.join(_writers)}")

    print()
    print("=" * 78)
    print("9. THE PURE FUNCTION'S OWN REFUSALS")
    print("=" * 78)

    _one_doc = {"docType": "time_phased_schedule", "documentId": "X1"}
    _base = {"bac": B_BAC, "pv": B_OVER_TOLERANCE, "plannedPctComplete": B_PCT,
             "sources": {"pv": _one_doc, "plannedPctComplete": _one_doc}}
    check(len(consistency_findings(_base, 1)) == 1, "the pure function reports the fixture")
    check(consistency_findings({**_base, "bac": None}, 1) == [], "absent budget: nothing")
    check(consistency_findings({**_base, "bac": 0}, 1) == [], "zero budget: nothing")
    check(consistency_findings({**_base, "pv": None}, 1) == [], "absent value: nothing")
    check(consistency_findings({**_base, "plannedPctComplete": None}, 1) == [],
          "absent percentage: nothing")
    check(consistency_findings({**_base, "plannedPctComplete": 0}, 1) == [],
          "a zero percentage implies zero and is refused rather than divided by")
    check(consistency_findings({**_base, "sources": {"pv": _one_doc}}, 1) == [],
          "a percentage with no source record: nothing")
    check(consistency_findings({**_base, "sources": {
              "pv": {"docType": "time_phased_schedule"},
              "plannedPctComplete": {"docType": "time_phased_schedule"}}}, 1) == [],
          "two records that BOTH lack a document identity are not thereby the same document")
    check(consistency_findings(None, 1) == [] and consistency_findings({}, 1) == [],
          "an empty or absent row: nothing, and no error")

    print()
    print("=" * 78)
    print("10. THE STANDING POPULATION GUARANTEES, DERIVED (S8.12, S8.13)")
    print("=" * 78)

    check(len(service_index()) == 63, f"63 modules in service, not {len(service_index())}")
    check(len(registry_index()) == 101, f"101 in the registry, not {len(registry_index())}")
    check(sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
          "the voting count is exactly 2, A1.7 and A1.8", str(sorted(CORE_VOTING_MODULES)))

finally:
    print()
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    sys.exit(1 if FAILED else 0)
