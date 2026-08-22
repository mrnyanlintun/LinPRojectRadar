#!/usr/bin/env python3
"""
RUN 45. RETRIEVAL BY FIELD KIND, DRIVEN THROUGH THE REAL ROUTES.

WHAT THIS SUITE EXISTS TO PROTECT. Run 44 measured that `_period_documents` scopes EVERY field
to the period a document was uploaded into, so a contract uploaded at period 1 is invisible at
periods 2 to 4 and a contract sum falls through to whatever weaker writer the later period
happens to hold. Run 45 divides the fields into two canonical kinds, signed off by the owner
(`code_audit/run45_field_classification_proposal.md` and the ruling recorded in the Run 45
report), and retrieves each kind by its own rule:

  * IDENTITY - the latest value AT OR BEFORE the period being computed, declared document-type
    precedence holding ACROSS the carry-forward.
  * PERIOD - the period's own documents and nothing else. Byte-for-byte as before Run 45.

NOTHING HERE ASSERTS THAT A CATEGORY LIGHTS UP. Expected values are hand-computed from the
stated formula (see section 5's contingency arithmetic), never read back from the code that
produced them, and the fixture's own figures are chosen so a fall-through is identifiable by
VALUE alone: 5,874,620 is the contract, 6,100,000 the change order's account, 4,463,290 the pay
application's weaker restatement. Those are Run 44's measured numbers.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run45_period_scoping.py
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
from app.field_registry import (  # noqa: E402
    FIELD_KINDS, IDENTITY_FIELDS, PERIOD_FIELDS, UNDETERMINED_FIELDS, retrieval_kind,
)
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402
from app.simulation.portfolio_health import live_portfolio_modules  # noqa: E402
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

#: Run 44's measured figures, so a fall-through is identifiable by value alone.
CONTRACT_SUM = 5_874_620          # the contract's own original_contract_sum
CO_BASELINE_ACCOUNT = 6_100_000   # the change order's account of the ORIGINAL baseline
CO_REVISED = 6_100_000            # the change order's revised contract sum
PAYAPP_RESTATEMENT = 4_463_290    # the pay application's weaker restatement

ORIGINAL_CONTINGENCY = 300_000    # stated ONCE, at period 1, and never again
REMAINING = {1: 250_000, 3: 150_000, 4: 100_000}
EV = {1: 2_000_000, 3: 2_600_000, 4: 3_000_000}
AC = {1: 1_800_000, 3: 2_500_000, 4: 2_900_000}
PCT = {1: 34.0, 3: 44.0, 4: 51.0}

PERIOD_END = {1: "2026-03-31", 2: "2026-04-30", 3: "2026-05-31", 4: "2026-06-30"}

ADMIN = "run45-admin-token"
P = "PRJ-R45"        # the project under test
Q = "PRJ-R45-OTHER"  # a second project, for the leakage check
R = "PRJ-R45-REV"    # the same evidence as P, uploaded in reverse order


def payapp(period: int) -> dict:
    return {"amount_paid_to_date": AC[period],
            "completed_to_date": EV[period],
            "percent_complete_verified": PCT[period],
            "original_contract_sum": PAYAPP_RESTATEMENT,
            "remaining_contingency": REMAINING[period],
            # THE ORIGINAL CONTINGENCY IS STATED ONCE, AT PERIOD 1. That is the whole point of
            # the identity classification the owner ruled for it: it cannot meaningfully differ
            # per period, and under the old all-period scoping A3.2 abstained from period 2 on.
            **({"original_contingency": ORIGINAL_CONTINGENCY} if period == 1 else {}),
            "application_date": PERIOD_END[period],
            "document_date": PERIOD_END[period]}


CONTRACT = {"original_contract_sum": CONTRACT_SUM,
            "project_start_date": "2026-01-01",
            "project_end_date": "2027-06-30"}

CHANGE_ORDER = {"revised_contract_sum": CO_REVISED,
                "baseline_contract_sum": CO_BASELINE_ACCOUNT,
                "revised_completion_date": "2027-09-30",
                "change_order_date": PERIOD_END[2],
                "document_date": PERIOD_END[2]}

#: (period, tag, doc_type, extraction). Period 2 holds a change order and NOTHING ELSE, which
#: is what makes the period-field guarantee testable: `ev` and `ac` must be absent at period 2
#: even though period 1 reported both.
DOCS: list[tuple[int, str, str, dict]] = [
    (1, "contract", "contract_value", CONTRACT),
    (1, "payapp1", "pay_application", payapp(1)),
    (2, "co", "change_order", CHANGE_ORDER),
    (3, "payapp3", "pay_application", payapp(3)),
    (4, "payapp4", "pay_application", payapp(4)),
]

#: The second project's contract differs in every digit, so a leak is unmistakable.
OTHER_CONTRACT_SUM = 9_111_222


def doc_bytes(project_tag: str, tag: str) -> bytes:
    return f"%PDF-1.4 RUN45 {project_tag} {tag}\n".encode()


RECORDED: dict[str, tuple[str, dict]] = {}
for _p, _tag, _type, _ex in DOCS:
    for _proj in ("P", "R"):
        RECORDED[hashlib.sha256(doc_bytes(_proj, _tag)).hexdigest()] = (_type, _ex)
RECORDED[hashlib.sha256(doc_bytes("Q", "contract")).hexdigest()] = (
    "contract_value", {**CONTRACT, "original_contract_sum": OTHER_CONTRACT_SUM})
RECORDED[hashlib.sha256(doc_bytes("Q", "payapp3")).hexdigest()] = (
    "pay_application", payapp(3))
set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R45-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy, name in ((P, "Run45 Under Test"), (Q, "Run45 Other"), (R, "Run45 Reversed")):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy, doc={"id": legacy, "name": name, "signals": {},
                                                 "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R45-PM", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
for legacy in (P, Q, R):
    post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
          "participant_id": created["participant_id"], "project_role": "PM"})


def upload(legacy: str, project_tag: str, tag: str, period: int) -> dict:
    return post({"action": "projectupload", "session_token": pm, "id": legacy, "period": period,
                 "period_end": PERIOD_END[period],
                 "documents": [{"filename": f"{project_tag}-{tag}.pdf",
                                "mimeType": "application/pdf",
                                "dataBase64": b64(doc_bytes(project_tag, tag))}]})


for _p, _tag, _type, _ex in DOCS:
    upload(P, "P", _tag, _p)
#: R carries byte-identical evidence to P, uploaded in exactly the reverse order.
for _p, _tag, _type, _ex in reversed(DOCS):
    upload(R, "R", _tag, _p)
upload(Q, "Q", "contract", 1)
upload(Q, "Q", "payapp3", 3)

for _legacy in (P, Q, R):
    _r = post({"action": "projectcomputeall", "session_token": pm, "id": _legacy})
    assert _r.get("ok") is True, str(_r)[:300]


def result(legacy: str, period: int) -> dict:
    r = post({"action": "projectresults", "session_token": pm, "id": legacy, "period": period})
    assert r.get("ok") is True, str(r)[:300]
    return r["result"]


def si(legacy: str, period: int) -> dict:
    return result(legacy, period)["signal_inputs"]


def module(legacy: str, period: int, module_id: str) -> dict | None:
    res = result(legacy, period)
    for m in res["module_results"]:
        if m.get("module_id") == module_id:
            return m
    for m in res.get("abstained") or []:
        if m.get("module_id") == module_id:
            return m
    return None


try:
    print("=" * 78)
    print("1. AN IDENTITY FIELD UPLOADED AT PERIOD 1 IS RETRIEVED AT PERIODS 2, 3 AND 4")
    print("=" * 78)

    for p in (1, 2, 3, 4):
        s_p = si(P, p)
        check(s_p.get("baselineContractSum") == CONTRACT_SUM,
              f"period {p}: baselineContractSum is the contract's own figure {CONTRACT_SUM:,}",
              str(s_p.get("baselineContractSum")))
        check(s_p.get("baselineStart") == "2026-01-01",
              f"period {p}: baselineStart carries from the period-1 contract",
              str(s_p.get("baselineStart")))
        check(s_p.get("originalContingency") == ORIGINAL_CONTINGENCY,
              f"period {p}: originalContingency carries from its single period-1 statement",
              str(s_p.get("originalContingency")))

    # NON-VACUITY. The document really was uploaded into period 1 alone, so periods 2 to 4
    # genuinely had to reach back for it rather than finding it in their own set.
    status = post({"action": "projectuploadstatus", "session_token": pm, "id": P, "period": 2})
    types_in_p2 = sorted({d.get("doc_type") for d in (status.get("documents") or [])})
    check(types_in_p2 == ["change_order"],
          "period 2 really holds only a change order, so the carry-forward was exercised",
          str(types_in_p2))

    print()
    print("=" * 78)
    print("2. AN IDENTITY FIELD SUPERSEDED AT PERIOD 2 KEEPS THE OLD VALUE BEFORE IT")
    print("=" * 78)

    # `bac` is the effective contract state: the change order at period 2 is the amendment, and
    # it supersedes the contract's figure from period 2 onward and NOT before.
    check(si(P, 1).get("bac") == CONTRACT_SUM,
          f"period 1: bac is the contract, {CONTRACT_SUM:,}", str(si(P, 1).get("bac")))
    for p in (2, 3, 4):
        check(si(P, p).get("bac") == CO_REVISED,
              f"period {p}: bac is the change order's revised sum {CO_REVISED:,}",
              str(si(P, p).get("bac")))
    check(si(P, 1).get("baselineEnd") == "2027-06-30",
          "period 1: baselineEnd is the contract's completion date",
          str(si(P, 1).get("baselineEnd")))
    for p in (2, 3, 4):
        check(si(P, p).get("baselineEnd") == "2027-09-30",
              f"period {p}: baselineEnd is the amendment's revised completion date",
              str(si(P, p).get("baselineEnd")))

    print()
    print("=" * 78)
    print("3. A PERIOD FIELD NEVER CARRIES FORWARD")
    print("=" * 78)

    check(si(P, 1).get("ev") == EV[1],
          f"period 1: ev is {EV[1]:,}, reported by that period's pay application")
    check(si(P, 2).get("ev") is None,
          "period 2: ev is ABSENT, though period 1 reported one",
          str(si(P, 2).get("ev")))
    check(si(P, 2).get("ac") is None,
          "period 2: ac is ABSENT, though period 1 reported one",
          str(si(P, 2).get("ac")))
    check(si(P, 2).get("remainingContingency") is None,
          "period 2: remainingContingency is ABSENT - the owner ruled it a PERIOD field",
          str(si(P, 2).get("remainingContingency")))
    check(si(P, 3).get("ev") == EV[3],
          f"period 3: ev is that period's own {EV[3]:,}, not period 1's",
          str(si(P, 3).get("ev")))
    check(si(P, 2).get("actualPctComplete") is None,
          "period 2: actualPctComplete is ABSENT", str(si(P, 2).get("actualPctComplete")))

    print()
    print("=" * 78)
    print("4. THE DECLARED PRECEDENCE HOLDS ACROSS PERIODS - RUN 44'S INVERSION IS DEAD")
    print("=" * 78)

    # Run 44, executed: a change order alone in a period yielded 6,100,000 for
    # baselineContractSum, against `field_registry.py:185`, which declares the contract's own
    # figure beats a change order's account of it. The change order in period 2 carries exactly
    # that account, and the contract sits in period 1.
    check(si(P, 2).get("baselineContractSum") == CONTRACT_SUM,
          "the contract at period 1 beats the change order at period 2 for baselineContractSum",
          str(si(P, 2).get("baselineContractSum")))
    check(si(P, 2).get("baselineContractSum") != CO_BASELINE_ACCOUNT,
          f"the {CO_BASELINE_ACCOUNT:,} inversion Run 44 measured does not reproduce")
    # NON-VACUITY: the change order really did carry its own account of the original baseline,
    # so the precedence rule had something to beat.
    check(CHANGE_ORDER["baseline_contract_sum"] == CO_BASELINE_ACCOUNT
          and CO_BASELINE_ACCOUNT != CONTRACT_SUM,
          "the change order really did state a DIFFERENT original baseline")
    # And the weaker writer never wins either: the pay application restates the contract sum at
    # every period, and must lose to the contract (tier 1) and the change order (tier 0).
    for p in (1, 2, 3, 4):
        check(si(P, p).get("bac") != PAYAPP_RESTATEMENT,
              f"period {p}: the pay application's {PAYAPP_RESTATEMENT:,} never wins bac",
              str(si(P, p).get("bac")))

    print()
    print("=" * 78)
    print("5. WHAT THE CONTINGENCY RULING BUYS, HAND-COMPUTED FROM THE STATED FORMULA")
    print("=" * 78)

    # canonical_v3.contingency_burn: C = (Original - Remaining) / Original, and
    # NormalizedBurn = C / ProgressFraction. Computed here by hand, in this file, from those
    # two sentences - NOT read back from the module.
    for p in (3, 4):
        expected_consumed = (ORIGINAL_CONTINGENCY - REMAINING[p]) / ORIGINAL_CONTINGENCY
        expected_burn = expected_consumed / (PCT[p] / 100.0)
        m = module(P, p, "A3.2")
        check(m is not None and m.get("consumed_fraction") == round(expected_consumed, 2),
              f"period {p}: A3.2 reports a consumed fraction of {round(expected_consumed, 2)}",
              str(m and m.get("consumed_fraction")))
        check(m is not None and m.get("normalized_burn") == round(expected_burn, 2),
              f"period {p}: A3.2's normalized burn is {round(expected_burn, 2)}",
              str(m and m.get("normalized_burn")))
        check(m is not None and m.get("original_contingency") == float(ORIGINAL_CONTINGENCY),
              f"period {p}: A3.2 used the carried original contingency",
              str(m and m.get("original_contingency")))
    # And it still abstains where the PERIOD half is genuinely absent: period 2 reports no
    # remaining contingency, and no carry-forward invents one.
    m2 = module(P, 2, "A3.2")
    check(m2 is not None and m2.get("consumed_fraction") is None,
          "period 2: A3.2 still abstains - the period half is absent and nothing invents it",
          str(m2 and m2.get("consumed_fraction")))

    print()
    print("=" * 78)
    print("6. UPLOAD ORDER DOES NOT AFFECT RETRIEVAL FOR EITHER KIND")
    print("=" * 78)

    # RUN 42'S PROOF, RE-RUN UNDER THE NEW RETRIEVAL. P and R carry byte-identical evidence in
    # exactly reversed upload order, so any difference is one the order produced.
    for p in (1, 2, 3, 4):
        a, b = result(P, p), result(R, p)
        fa = {k: v for k, v in a["signal_inputs"].items() if k != "sources"}
        fb = {k: v for k, v in b["signal_inputs"].items() if k != "sources"}
        check(fa == fb, f"period {p}: reversed upload order reports identical figures",
              str([k for k in fa if fa[k] != fb.get(k)]))
        ba = {m["module_id"]: m.get("status") for m in a["module_results"]}
        bb = {m["module_id"]: m.get("status") for m in b["module_results"]}
        check(ba == bb, f"period {p}: reversed upload order reaches identical bands",
              str([k for k in ba if ba[k] != bb.get(k)]))
        check(sorted(x["module_id"] for x in (a.get("abstained") or []))
              == sorted(x["module_id"] for x in (b.get("abstained") or [])),
              f"period {p}: reversed upload order abstains in exactly the same modules")
    check([d[0] for d in DOCS] != [d[0] for d in reversed(DOCS)],
          "the fixture really did reverse the upload order, so this section tested something")

    print()
    print("=" * 78)
    print("7. NO CROSS-PROJECT LEAKAGE")
    print("=" * 78)

    for p in (1, 3):
        check(si(Q, p).get("baselineContractSum") == OTHER_CONTRACT_SUM,
              f"period {p}: the other project reports its OWN contract sum",
              str(si(Q, p).get("baselineContractSum")))
        check(si(Q, p).get("bac") != CO_REVISED,
              f"period {p}: the other project never sees this project's change order",
              str(si(Q, p).get("bac")))
    check(si(Q, 3).get("originalContingency") is None,
          "the other project has no original contingency, and does not borrow one",
          str(si(Q, 3).get("originalContingency")))
    # Its period 2 was never uploaded to at all: the carry-forward must not manufacture one.
    q_periods = post({"action": "projectperiods", "session_token": pm, "id": Q})
    check(q_periods.get("ok") is True and 2 not in (q_periods.get("periods") or []),
          "the other project never opened a period 2, and none was manufactured",
          str(q_periods.get("periods")))

    print()
    print("=" * 78)
    print("8. THE CLASSIFICATION IS COMPLETE, DISJOINT, AND DERIVED")
    print("=" * 78)

    total = len(FIELD_KINDS)
    check(len(IDENTITY_FIELDS) == 13, f"13 identity fields, not {len(IDENTITY_FIELDS)}")
    check(len(UNDETERMINED_FIELDS) == 2,
          f"2 undetermined fields, not {len(UNDETERMINED_FIELDS)}")
    check(len(PERIOD_FIELDS) == 62, f"62 period fields, not {len(PERIOD_FIELDS)}")
    check(len(IDENTITY_FIELDS) + len(PERIOD_FIELDS) + len(UNDETERMINED_FIELDS) == total == 77,
          f"the three kinds partition all {total} emittable fields exactly",
          f"{len(IDENTITY_FIELDS)}+{len(PERIOD_FIELDS)}+{len(UNDETERMINED_FIELDS)} vs {total}")
    check(not (IDENTITY_FIELDS & PERIOD_FIELDS) and not (IDENTITY_FIELDS & UNDETERMINED_FIELDS)
          and not (PERIOD_FIELDS & UNDETERMINED_FIELDS),
          "no field carries two kinds")
    check(IDENTITY_FIELDS <= set(FIELD_KINDS) and UNDETERMINED_FIELDS <= set(FIELD_KINDS),
          "every classified name is a field the emission layer can actually produce")
    check(retrieval_kind("bac") == "IDENTITY" and retrieval_kind("ev") == "PERIOD"
          and retrieval_kind("totalFloat") == "UNDETERMINED",
          "retrieval_kind answers from the declaration")
    # The owner's ruling, field by field, on the five that were open at §5.1.
    check("originalContingency" in IDENTITY_FIELDS, "ruling 1.2: originalContingency is identity")
    check("remainingContingency" in PERIOD_FIELDS, "ruling 1.2: remainingContingency is period")
    check("changeOrderCount" in PERIOD_FIELDS, "ruling 1.3: changeOrderCount stays period")
    check("totalFloat" in UNDETERMINED_FIELDS and "consumedFloat" in UNDETERMINED_FIELDS,
          "ruling 1.4: the float pair stays undetermined")
    # An UNDETERMINED field is retrieved as a PERIOD field - today's behaviour, unchanged.
    check(all(f not in IDENTITY_FIELDS for f in UNDETERMINED_FIELDS),
          "an undetermined field never carries forward")

    print()
    print("=" * 78)
    print("9. THE STANDING POPULATION GUARANTEES, DERIVED")
    print("=" * 78)

    check(sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
          "the voting count is exactly 2, A1.7 and A1.8", str(sorted(CORE_VOTING_MODULES)))
    check(len(service_index()) == 63, f"63 modules in service, not {len(service_index())}")
    check(len(registry_index()) == 101, f"101 in the registry, not {len(registry_index())}")
    check(len(registry_index()) - len(service_index()) == 38,
          "the 38 retired identifiers reconcile 63 + 38 = 101")
    check(live_portfolio_modules() == (),
          "Portfolio Health computes nowhere on any production path",
          str(live_portfolio_modules()))

finally:
    print()
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    sys.exit(1 if FAILED else 0)
