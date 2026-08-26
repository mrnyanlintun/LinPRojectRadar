#!/usr/bin/env python3
"""
RUN 67. THE CATEGORY-9 ASSESSMENT THE PLATFORM NEVER WROTE, AND WHAT A ROW WITH NO BAND DOES.

Two things this suite pins, both of which became observable only after Run 65 let every module
that computed vote into its own category.

ONE. `documents._evidence_qualification` writes the period's Category-9 assessment, and it must
     state ONLY facts the platform already holds. The omissions are the substance of the change,
     so they are asserted as omissions: no verification claim, no source authority, no
     reliability weight, no timeliness verdict, no self-declared qualification state. Each is
     proved to matter by injecting the claim and confirming the verdict is not bought by it.

TWO. A row that computed and asserted NO BAND -- the `calibration_pending` contract, which 34 of
     the 63 in-service modules can produce -- now reaches `by_category` for the first time,
     because Run 65 removed the filter that used to keep it out. Nothing anywhere asserted what
     the fusion does with it. It contributes no mass and cannot drag a category, and that is
     pinned here rather than left to be rediscovered.

Every check is proved able to fail by an injection at the exact site it is about.
"""
from __future__ import annotations
import pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))

from app.documents import _evidence_qualification            # noqa: E402
from app.simulation.fusion import fuse_signals               # noqa: E402
from app.simulation.lineage import lineage_record            # noqa: E402
from app.simulation.qualification_boundary import declared_evidence  # noqa: E402
from app.simulation.qualified_evidence import (              # noqa: E402
    ELIGIBLE_STATES, REVIEW_REQUIRED, UNASSESSED)

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  -- {detail}" if detail else ""))


OBS = [
    {"field": "ev", "value": 2_000_000, "tier": 0, "as_of": "2026-04-30",
     "doc_type": "pay_application"},
    {"field": "ac", "value": 2_100_000, "tier": 0, "as_of": "2026-04-30",
     "doc_type": "pay_application"},
    # A field two documents disagree on, resolved by DECLARED PRECEDENCE: different tiers.
    {"field": "bac", "value": 4_000_000, "tier": 0, "as_of": "2026-01-01",
     "doc_type": "contract"},
    {"field": "bac", "value": 4_500_000, "tier": 1, "as_of": "2026-04-30",
     "doc_type": "change_order"},
]

print("=" * 90)
print("1. THE RECORD STATES ONLY WHAT THE PLATFORM HOLDS")
print("=" * 90)

rec = _evidence_qualification(2, OBS)
check(rec is not None, "the period's Category-9 assessment is written at all")
check(rec["evidence_id"] == "P2-evidence-base",
      "its identity is the PERIOD's, carrying no project id, so two projects that uploaded the "
      "same bytes reach the same assessment", rec["evidence_id"])
check(rec["effective_date"] == "2026-04-30",
      "its effective date is the latest as-of among the period's own observations, which is a "
      "date the documents state and not one chosen here", str(rec["effective_date"]))
for absent in ("verification_status", "source_authority", "reliability_weight",
               "timeliness_status", "qualification_state"):
    check(absent not in rec,
          f"and it asserts NO {absent}: nobody verified these documents, no authority is "
          f"claimed, no governed rubric exists, and the record does not grade itself")
check(_evidence_qualification(2, []) is None,
      "a period with no observations gets NO record, rather than a record claiming an assessed "
      "evidence base that does not exist")

print()
print("=" * 90)
print("2. THE DECLARED PRECEDENCE RULE IS NOT A CONFLICT, AND AN UNDECIDABLE PAIR IS")
print("=" * 90)

check(rec["material_conflicts"] == [],
      "two documents disagreeing on a field at DIFFERENT declared writer tiers is not an "
      "unresolved conflict: selection decides it by the declared rule",
      str(rec["material_conflicts"]))
# THE INJECTION. Same field, same lowest tier, same as-of, two values: the declared precedence
# has nothing left to decide with, and the record must say so.
UNDECIDABLE = OBS + [{"field": "ev", "value": 1_750_000, "tier": 0, "as_of": "2026-04-30",
                      "doc_type": "cost_report"}]
conf = _evidence_qualification(2, UNDECIDABLE)["material_conflicts"]
check([c["field"] for c in conf] == ["ev"],
      "FAULT: two documents of EQUAL declared tier and equal date stating different values IS "
      "recorded as an unresolved material conflict, so the record can refuse and this check is "
      "not vacuous", str(conf))
check(conf and set(conf[0]) >= {"field", "writer_tier", "distinct_values", "documents", "reason"},
      "and the conflict names the field, the tier, how many values were stated, which document "
      "types stated them, and why the rule could not decide", str(conf[0] if conf else None))

print()
print("=" * 90)
print("3. THE VERDICT IS EARNED BY THE EVIDENCE, NEVER BOUGHT BY A CLAIM")
print("=" * 90)

USE = "Delivery Quality Performance"
ev = declared_evidence({"evidenceQualification": rec}, "A6.1", USE)
check(ev.qualification_state in ELIGIBLE_STATES,
      "handed the honest record and nothing else, the boundary assesses the evidence ELIGIBLE",
      ev.qualification_state)
check(any("reliability" in r for r in ev.qualification_reasons),
      "and records the one honest limitation: no governed reliability mapping is established, "
      "so no numeric weight is asserted", str(ev.qualification_reasons))

# FAULT ONE: a record that declares itself verified, authoritative and timely must reach the
# SAME verdict. A favourable claim buys nothing, which is why omitting the claims costs nothing.
claimed = dict(rec, verification_status="verified", source_authority="system_of_record",
               timeliness_status="TIMELY", qualification_state="QUALIFIED")
ev_claimed = declared_evidence({"evidenceQualification": claimed}, "A6.1", USE)
check(ev_claimed.qualification_state == ev.qualification_state,
      "FAULT: a record that declares itself verified, authoritative, timely and QUALIFIED "
      "reaches the identical verdict -- a favourable claim is not honoured, which is why the "
      "honest record omitting all four loses nothing",
      f"{ev.qualification_state} vs {ev_claimed.qualification_state}")

# FAULT TWO: an UNFAVOURABLE fact IS honoured. The conflict record must refuse the use.
ev_conf = declared_evidence(
    {"evidenceQualification": _evidence_qualification(2, UNDECIDABLE)}, "A6.1", USE)
check(ev_conf.qualification_state == REVIEW_REQUIRED
      and ev_conf.use_eligibility.get("requirement_conformance") is False,
      "FAULT: with an unresolved material conflict on the record the same use is REFUSED, so "
      "the assessment is capable of blocking and is not a rubber stamp",
      f"{ev_conf.qualification_state} {ev_conf.use_eligibility}")
# FAULT THREE: a record may still declare ITSELF unassessed, and that IS honoured.
ev_un = declared_evidence({"evidenceQualification": dict(rec, qualification_state=UNASSESSED)},
                          "A6.1", USE)
check(ev_un.qualification_state == UNASSESSED,
      "and a record may declare itself UNASSESSED and be believed, because that direction is "
      "never self-serving", ev_un.qualification_state)

print()
print("=" * 90)
print("4. A ROW THAT COMPUTED AND ASSERTED NO BAND CANNOT DRAG ITS CATEGORY")
print("=" * 90)


def sig(mid, band, body):
    return {"module_id": mid, "status": band,
            "lineage": lineage_record(mid, lineage_group_ids=(body,))}


red_only = fuse_signals([sig("A4.2", "Red", "doc")])
with_null = fuse_signals([sig("A4.2", "Red", "doc"), sig("A4.4", None, "doc")])
check(red_only["status"] == with_null["status"] == "Red",
      "a calibration-pending row beside a banded one leaves the category exactly where the "
      "banded one put it: it contributes no mass in either direction",
      f"{red_only['status']} vs {with_null['status']}")
check(red_only["mass"] == with_null["mass"],
      "and not one unit of mass moves, so it cannot drag the category down and cannot lift it "
      "either")
check(fuse_signals([sig("A3.2", None, "cost"), sig("A3.6", None, "cost")]) is None,
      "a category in which EVERY module asserted no band fuses to nothing at all, rather than "
      "to Unknown, so it does not vote and does not enter the project rollup")
# FAULT: the check above is not vacuous -- give one of them a band and the category lights.
check(fuse_signals([sig("A3.2", "Amber", "cost"), sig("A3.6", None, "cost")])["status"] == "Amber",
      "FAULT: give one of those two a band and the category lights, so the assertion above is "
      "about the missing band and not about the fixture")

print()
print("=" * 90)
failed = [r for r in RESULTS if not r[0]]
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print(f"RESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
print("=" * 90)
sys.exit(1 if failed else 0)
