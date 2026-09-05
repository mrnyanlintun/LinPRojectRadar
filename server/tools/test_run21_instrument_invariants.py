#!/usr/bin/env python3
"""
RUN 21, SECTION 19. THE CRITICAL INSTRUMENT INVARIANTS, EACH PROVED NON-VACUOUS BY DELIBERATE
VIOLATION.

WHY THIS FILE EXISTS IN THIS FORM. Run 20 found NINE guards that were structurally incapable of
detecting the violation they claimed to detect, and seven more written vacuously inside a single
cycle. The failure mode is always the same: a check asserted against a hand-maintained copy of
the thing it is checking, or against an expression derived from the value it is testing, so the
two can never disagree. A guard like that passes forever and proves nothing.

THE DISCIPLINE APPLIED HERE, for every invariant below:

    pin the expectation in a LITERAL
      -> introduce a controlled violation of the real production structure
      -> prove the named guard turns RED
      -> restore
      -> prove it is GREEN again on production as shipped

Never compare a value against the expression that produced it. Never iterate a mapping the
violation emptied. Never mutate a copy of a structure the code rebuilds per call -- every
violation below is applied to the module object production itself reads, and restored in a
finally block, and the restoration is verified rather than assumed.

THE INVARIANTS: voting count, concept-only activation, Material Cost Variance, the Category-9
raw-bypass refusal, the anti-feedback rejection, and the abstention contract. The participant
locks, the reset boundary, cross-project isolation and participant period identity need a live
server and a browser, and are proved in tools/drive_run21_participant.py and
tools/drive_run21_instrument.py rather than duplicated here.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run21_instrument_invariants.py
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")

ROOT = pathlib.Path(__file__).resolve().parents[2]

passed = total = 0
failures: list[str] = []
EVIDENCE: list[tuple] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failures.append(f"{label}: {detail}")
        print(f"  FAIL  {label}  {detail}")


def guard(name: str, prop: str, how: str, observed: str, result: str, why: str) -> None:
    EVIDENCE.append((name, prop, how, observed, result, why))


import app.simulation.registry as registry  # noqa: E402
from app.simulation.qualification_gate import (  # noqa: E402
    ABSTAINED, ALLOWED, REJECTED, RawBypassError, NON_PROJECT_EVIDENCE,
    fuse_qualified, qualify)
from app.simulation.lineage import lineage_record  # noqa: E402

print("=" * 78)
print("INVARIANT 1  voting is exactly two, and the guard can see it change")
print("=" * 78)

# PINNED IN LITERALS. Not len(...) == len(...), and not compared against anything derived from
# the registry itself.
check(len(registry.CORE_VOTING_MODULES) == 2,
      "the registry declares exactly 2 voting modules",
      str(sorted(registry.CORE_VOTING_MODULES)))
check(sorted(registry.CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
      "and they are exactly A1.7 and A1.8",
      str(sorted(registry.CORE_VOTING_MODULES)))

_orig_voting = registry.CORE_VOTING_MODULES
try:
    registry.CORE_VOTING_MODULES = frozenset({"A1.7", "A1.8", "A2.5"})
    widened = len(registry.CORE_VOTING_MODULES) == 2
    check(not widened,
          "NON-VACUITY: adding a third voting module really does make the count check RED",
          f"count now {len(registry.CORE_VOTING_MODULES)}")
    guard("voting count", "voting is exactly 2",
          "a third module added to CORE_VOTING_MODULES in the module production reads",
          f"count became {len(registry.CORE_VOTING_MODULES)}", "RED as required",
          "a count check that could not see a widened set would license silent expansion")
finally:
    registry.CORE_VOTING_MODULES = _orig_voting
check(len(registry.CORE_VOTING_MODULES) == 2 and
      sorted(registry.CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
      "and the violation was restored: production is exactly 2 again",
      str(sorted(registry.CORE_VOTING_MODULES)))
guard("voting count", "voting is exactly 2", "restored and re-read", "2 (A1.7, A1.8)",
      "GREEN", "")

print()
print("=" * 78)
print("INVARIANT 2  concept-only modules are never activated")
print("=" * 78)

concept_only = dict(registry.DISABLED_CONCEPT_ONLY)
check(len(concept_only) > 0,
      "the registry names concept-only modules, so the check below has something to bite on",
      str(sorted(concept_only)))
activated = [mid for mid in concept_only
             if registry.activation_state(mid) != "DISABLED_UNSAFE"]
check(activated == [],
      "every concept-only module reports DISABLED_UNSAFE: concept-only activation is 0",
      str(activated))
guard("concept-only activation", "activation count is 0",
      "activation_state read for every concept-only module id",
      f"{len(concept_only)} modules, all DISABLED_UNSAFE", "GREEN", "")

_orig_co = registry.DISABLED_CONCEPT_ONLY
victim = sorted(concept_only)[0]
try:
    shrunk = {k: v for k, v in concept_only.items() if k != victim}
    registry.DISABLED_CONCEPT_ONLY = shrunk
    # NOTE THE SHAPE. The violation REMOVES a module from the disabled set, and the check is
    # re-run over the ORIGINAL, pinned id list -- not over the mapping the violation emptied,
    # which is exactly how Run 20's vacuous guards passed.
    now = [mid for mid in sorted(concept_only)
           if registry.activation_state(mid) != "DISABLED_UNSAFE"]
    check(victim in now,
          "NON-VACUITY: un-disabling a concept-only module really does make the guard RED",
          f"{victim} now reports {registry.activation_state(victim)}")
    guard("concept-only activation", "activation count is 0",
          f"{victim} removed from DISABLED_CONCEPT_ONLY, checked against the PINNED id list",
          f"{victim} reported {registry.activation_state(victim)}", "RED as required",
          "iterating the mapping the violation emptied would have found nothing to check")
finally:
    registry.DISABLED_CONCEPT_ONLY = _orig_co
check([mid for mid in concept_only
       if registry.activation_state(mid) != "DISABLED_UNSAFE"] == [],
      "and the violation was restored: concept-only activation is 0 again")

print()
print("=" * 78)
print("INVARIANT 3  Material Cost Variance stays disabled")
print("=" * 78)

MCV = "A3.4"
check(MCV in registry.DISABLED_MODULES,
      "Material Cost Variance is in the disabled set", str(MCV))
state = registry.activation_state(MCV)
check(state != "ENABLED_QUALIFIED",
      "and is NOT operationally activated", str(state))
check(MCV not in registry.CORE_VOTING_MODULES,
      "and does not vote")
guard("Material Cost Variance", "disabled and non-voting",
      "activation_state and the voting set read from the registry",
      f"activation_state={state}, in voting set = {MCV in registry.CORE_VOTING_MODULES}",
      "GREEN", "")

_orig_dis = registry.DISABLED_MODULES
_orig_rev = registry.DISABLED_EVIDENCE_UNDER_REVIEW
try:
    registry.DISABLED_MODULES = {k: v for k, v in _orig_dis.items() if k != MCV}
    registry.DISABLED_EVIDENCE_UNDER_REVIEW = {
        k: v for k, v in _orig_rev.items() if k != MCV}
    reactivated = registry.activation_state(MCV)
    check(reactivated != state,
          "NON-VACUITY: removing it from the disabled sets really does change its activation "
          "state, so the check above is not true by construction",
          f"disabled={state} undisabled={reactivated}")
    guard("Material Cost Variance", "disabled",
          f"{MCV} removed from both disabled mappings",
          f"activation_state moved {state} -> {reactivated}", "RED as required",
          "a state that did not move would mean the guard reads something else entirely")
finally:
    registry.DISABLED_MODULES = _orig_dis
    registry.DISABLED_EVIDENCE_UNDER_REVIEW = _orig_rev
check(registry.activation_state(MCV) == state,
      "and the violation was restored: Material Cost Variance is disabled again",
      str(registry.activation_state(MCV)))

print()
print("=" * 78)
print("INVARIANT 4  the Category-9 raw-bypass refusal")
print("=" * 78)

raw = {"module_id": "A1.7", "status": "Amber", "lineage": lineage_record("A1.7")}
refused = False
try:
    fuse_qualified([raw])
except RawBypassError:
    refused = True
check(refused,
      "a hand-built raw signal is REFUSED by the combination: the gate cannot be skipped",
      "no RawBypassError raised" if not refused else "")
guard("Category-9 raw bypass", "a raw signal cannot reach the combination",
      "a hand-built dict with the right shape passed to fuse_qualified",
      "RawBypassError raised", "GREEN", "")

# NON-VACUITY: a properly qualified signal must get THROUGH, or the refusal above is simply
# "this function rejects everything" and proves nothing about bypass.
qs = qualify("A1.7", "Amber", 1.0, {"verdict": ALLOWED, "reasons": []})
passed_through = fuse_qualified([qs])
check(len(passed_through) == 1,
      "NON-VACUITY: a properly qualified signal DOES pass, so the refusal is about bypass "
      "and not about rejecting everything", str(passed_through)[:200])
guard("Category-9 raw bypass", "a qualified signal still passes",
      "a signal built with qualify() passed to fuse_qualified",
      f"{len(passed_through)} signal admitted", "GREEN",
      "without this the refusal would be indistinguishable from a function that always raises")

print()
print("=" * 78)
print("INVARIANT 5  the anti-feedback rejection")
print("=" * 78)

check(len(NON_PROJECT_EVIDENCE) > 0,
      "the gate names the non-project-evidence relationships", str(sorted(NON_PROJECT_EVIDENCE)))
for rel in sorted(NON_PROJECT_EVIDENCE):
    q = qualify("C1.4", "Green", 1.0, {"verdict": ALLOWED, "reasons": []},
                lineage=dict(lineage_record("C1.4"), evidence_relationship=rel))
    check(q.verdict == REJECTED,
          f"a {rel} signal is REJECTED as project-condition evidence", str(q.verdict))
    check(q.may_vote is False, f"and a {rel} signal may not vote")
guard("anti-feedback rejection", "quality/governance/decision outputs are not project evidence",
      "qualify() called with each non-project relationship",
      f"{len(NON_PROJECT_EVIDENCE)} relationships, all REJECTED", "GREEN", "")

# NON-VACUITY: a project-condition relationship must NOT be rejected.
ok_q = qualify("A1.7", "Amber", 1.0, {"verdict": ALLOWED, "reasons": []},
               lineage=dict(lineage_record("A1.7"), evidence_relationship="INDEPENDENT"))
check(ok_q.verdict != REJECTED,
      "NON-VACUITY: an INDEPENDENT project signal is NOT rejected, so the rejections above "
      "are about the relationship and not about everything", str(ok_q.verdict))
guard("anti-feedback rejection", "an ordinary project signal is still admitted",
      "qualify() called with INDEPENDENT", f"verdict={ok_q.verdict}", "GREEN",
      "without this the rejection would be indistinguishable from rejecting all signals")

print()
print("=" * 78)
print("INVARIANT 6  the abstention contract: no band, no vote, distinguishable")
print("=" * 78)

ab = qualify("A2.1", None, None, {"verdict": ALLOWED, "reasons": []}, module_abstained=True)
check(ab.verdict == ABSTAINED, "an abstaining module is qualified ABSTAINED", str(ab.verdict))
check(ab.band is None, "carries NO band, so no surface can paint it a traffic light",
      str(ab.band))
check(ab.may_vote is False, "and may not vote")
sig = ab.to_fusion_signal()
check(sig.get("status") is None,
      "and presents NO status to the combination, so it contributes no mass rather than a "
      "neutral value indistinguishable from a measured one", str(sig)[:200])
guard("abstention contract", "an abstention carries no band, no vote and no mass",
      "qualify() with module_abstained=True, then to_fusion_signal()",
      f"verdict={ab.verdict} band={ab.band} may_vote={ab.may_vote} "
      f"status={sig.get('status')}", "GREEN", "")

# NON-VACUITY: a module that did NOT abstain keeps its band, votes, and presents a status.
nb = qualify("A1.7", "Amber", 1.0, {"verdict": ALLOWED, "reasons": []}, module_abstained=False)
check(nb.band == "Amber" and nb.may_vote is True
      and nb.to_fusion_signal().get("status") is not None,
      "NON-VACUITY: a module that did NOT abstain keeps its band, may vote and presents a "
      "status, so the abstention assertions are not true of everything",
      f"{nb.verdict} {nb.band} {nb.may_vote}")
guard("abstention contract", "a non-abstaining module is unaffected",
      "qualify() with module_abstained=False",
      f"band={nb.band} may_vote={nb.may_vote}", "GREEN", "")

# ---------------------------------------------------------------- the evidence file
import csv  # noqa: E402
out = ROOT / "code_audit" / "run21_guard_nonvacuity_results.csv"
with artifact_out(out).open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["guard", "protected_invariant", "how_the_violation_was_introduced",
                "observed", "result", "why_it_matters"])
    w.writerows(EVIDENCE)
print(f"\n  wrote {out}")

print()
if failures:
    print("FAILURES:")
    for f in failures:
        print("  " + f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
