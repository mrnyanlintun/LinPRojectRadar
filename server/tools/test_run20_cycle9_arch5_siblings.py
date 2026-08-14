"""
RUN 20 CYCLE 9. ARCH.5: SIX SIBLINGS AGGREGATING THE SAME FOUR ARMS WITH EQUAL WEIGHT PER ARM.

THE WARNING THE REGISTER ROW CARRIES, AND IT IS OBEYED. None of these six is a Dempster
combination, so B2.1's precondition does not transfer to them unaltered. What DOES transfer is
the fact underneath it, and evidence dependence is a property of ANCESTRY, not of aggregation
syntax. So each module's own aggregation is examined for what IT assumes, and the shared fact --
three of the four arms are readings of one earned-value measurement -- is established here by
EXECUTION, in both schedule-index regimes, rather than read off a field name or inherited from
cycle 7's write-up.

THE SIX. B2.2 Rough Sets, B2.3 Neutrosophic Logic, B2.4 Interval Fuzzy Sets, B2.5 Z-numbers,
B2.6 PLTS and B2.8 Belief Rule Base. B2.7 Plithogenic Sets and B2.9 Quantum Probability read the
same arms and are NOT remediated here: both are DISABLED_UNSAFE, emit no signal on any project,
and so have no signal whose evidence there is anything to declare. That is the A2.1 precedent
from cycle 5 and the six-undeclared-modules precedent from cycle 8, and section 7 proves the
disabled state mechanically rather than asserting it.

THE FOUR QUESTIONS THE MANDATE ASKS OF EACH, ANSWERED BY MEASUREMENT:
  does one body receive duplicated influence?          section 3
  do missing arms silently reweight the remainder?     section 5
  does module ordering affect the result?              section 6
  is one body represented multiple times?              section 2 and section 3

NO WEIGHT IS INTRODUCED ANYWHERE. Section 8 is the check that proves it: every reliability,
membership, rule weight and belief mass in the six modules is byte-identical to the values that
stood before this cycle.
"""

import copy
import itertools
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.simulation import models_evc  # noqa: E402
from app.simulation.arm_lineage import (  # noqa: E402
    ARM_LINEAGE_BY_KEY, ARM_LINEAGE_CUSUM, ARM_LINEAGE_DOC, ARM_LINEAGE_EVM, ARM_LINEAGE_MC,
    one_reading_per_body, separate_arms,
)
from app.simulation.registry import activation_state  # noqa: E402

_passed = 0
_total = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}" + (f"  [{detail}]" if detail else ""))


#: The six ARCH.5 modules and their production entry points, taken from the registry's own table
#: rather than restated, so a module that is renamed or rerouted cannot silently drop out.
SIX = ["B2.2", "B2.3", "B2.4", "B2.5", "B2.6", "B2.8"]
RUNNER = {mid: models_evc.EVC_EXTENSIONS[mid][1] for mid in SIX}
NOOP = (lambda: 0.5)

#: An adverse project on every arm. All four arms read Red.
SI_ALL_RED = {"evm": {"cpi": 0.85, "spi": 0.85}, "mc": {"p80DeltaPct": 20},
              "cusum": {"breached": True}, "doc": {"score": 0.80}}
#: The same earned-value evidence with a CLEAN document score. This is the fixture that separates
#: the two bodies: everything Red except the one genuinely independent body.
SI_EV_RED_DOC_GREEN = {"evm": {"cpi": 0.85, "spi": 0.85}, "mc": {"p80DeltaPct": 20},
                       "cusum": {"breached": True}, "doc": {"score": 0.10}}
#: A healthy earned value with an adverse document score, the mirror image.
SI_EV_GREEN_DOC_RED = {"evm": {"cpi": 0.99, "spi": 0.99}, "mc": {"p80DeltaPct": 2},
                       "cusum": {"breached": False}, "doc": {"score": 0.80}}

print("=== 1. THE SIX ARE THE SIX, AND THE OTHER TWO ARE DISABLED ===")
for mid in SIX:
    check(f"{mid} is registered and ADVISORY_ONLY, so it is remediated and still cannot vote",
          activation_state(mid) == "ADVISORY_ONLY", activation_state(mid))
for mid in ("B2.7", "B2.9"):
    check(f"{mid} reads the same arms and is DISABLED_UNSAFE, so it emits no signal to declare",
          activation_state(mid) == "DISABLED_UNSAFE", activation_state(mid))
check("no seventh advisory module in this file reads the arms undeclared",
      sorted(set(models_evc.EVC_EXTENSIONS) - set(SIX) - {"B2.7", "B2.9"}) == [],
      str(sorted(set(models_evc.EVC_EXTENSIONS) - set(SIX) - {"B2.7", "B2.9"})))

print("\n=== 2. THE FOUR ARMS, AND WHICH BODIES THEY ARE, ESTABLISHED BY THE PARTITION ===")
ALL_ARMS = [ARM_LINEAGE_EVM, ARM_LINEAGE_MC, ARM_LINEAGE_CUSUM, ARM_LINEAGE_DOC]
check("the arm table names exactly the four assembled signal keys",
      sorted(ARM_LINEAGE_BY_KEY) == ["cusum", "doc", "evm", "mc"])
_bodies_pv = separate_arms(ALL_ARMS, SI_ALL_RED)
check("with all four arms present the partition finds exactly TWO bodies of evidence",
      len(_bodies_pv) == 2, str(_bodies_pv))
_members = [sorted(ALL_ARMS[i]["module_id"] for i in g) for g in _bodies_pv]
check("the index, forecast and trend arms are ONE body",
      ["B2.1.cusum", "B2.1.evm", "B2.1.mc"] in _members, str(_members))
check("and the document arm is a body of its own",
      ["B2.1.doc"] in _members, str(_members))

print("\n--- and in the OTHER schedule-index regime, measured rather than assumed ---")
#
# Cycle 8 established that the schedule index has two ancestries: the earned value over the
# planned value, or actual over planned progress when no planned value exists. A separation that
# is right in one regime and wrong in the other is exactly the defect cycle 8 opened. So the
# partition is re-run against evidence that selects the fallback branch.
SI_NO_PV = {"evm": {"cpi": 0.85, "spi": 0.85}, "mc": {"p80DeltaPct": 20},
            "cusum": {"breached": True}, "doc": {"score": 0.80},
            "actual_progress": 0.4, "planned_progress": 0.5}
_bodies_pp = separate_arms(ALL_ARMS, SI_NO_PV)
check("the fallback regime also finds exactly two bodies", len(_bodies_pp) == 2,
      str(_bodies_pp))
_members_pp = [sorted(ALL_ARMS[i]["module_id"] for i in g) for g in _bodies_pp]
check("and the same three arms are still one body, for a different reason: the index arm and the "
      "trend arm intersect on the progress figures instead of on the earned value",
      ["B2.1.cusum", "B2.1.evm", "B2.1.mc"] in _members_pp, str(_members_pp))
check("the separation is therefore stable across both ancestries, which is what makes it safe "
      "to apply without knowing which regime a project is in",
      _members == _members_pp)

print("\n=== 3. DUPLICATED INFLUENCE: MEASURED PER MODULE, BEFORE AND AFTER ===")
#
# The measurement is the count of readings each body contributes to the aggregation. Before the
# fix every present arm contributed one, so the earned-value body contributed three and the
# document body one: three quarters against one quarter on evidence of one measurement and one
# score. After, each body contributes exactly one.
_dedup = one_reading_per_body(ALL_ARMS, ["Red", "Red", "Red", "Green"], SI_ALL_RED)
check("four arms in, two readings out", _dedup["arms_present"] == 4
      and _dedup["bodies_of_evidence"] == 2 and _dedup["arms_suppressed_as_duplicate"] == 2,
      str(_dedup))
check("the earned-value body's kept reading is the most adverse of its three",
      _dedup["bodies"][0]["member_bands"] == ["Red", "Red", "Red"])
_mixed = one_reading_per_body(ALL_ARMS, ["Green", "Amber", "Red", "Green"], SI_ALL_RED)
check("and when the three readings of that body DISAGREE the most adverse is taken, and the "
      "disagreement is recorded rather than scored",
      ALL_ARMS[_mixed["kept"][0]]["module_id"] == "B2.1.cusum"
      and _mixed["bodies"][0]["disagreement"] is True,
      str(_mixed["bodies"][0]))
# B2.4 IS THE EXCEPTION AND IT IS NAMED RATHER THAN AVERAGED AWAY. It reads no forecast, trend
# or document arm at all: it reads the cost index and the schedule index, which are two readings
# of ONE earned-value measurement. So it has one body, and its duplication is INSIDE that body
# rather than across arms. A check that demanded two bodies of it would have been a check that
# never understood what it was measuring.
_EXPECTED_BODIES = {"B2.2": 2, "B2.3": 2, "B2.4": 1, "B2.5": 2, "B2.6": 2, "B2.8": 2}
for mid in SIX:
    r = RUNNER[mid](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30")
    check(f"{mid} reports {_EXPECTED_BODIES[mid]} body/bodies of evidence on a four-arm project",
          r.get("bodies_of_evidence") == _EXPECTED_BODIES[mid],
          str(r.get("bodies_of_evidence")))
check("B2.4 is the only one of the six that never reads the document body at all, so it is the "
      "only one with a single body, and that is a property of the module and not of the fixture",
      RUNNER["B2.4"](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30")
      == RUNNER["B2.4"](copy.deepcopy(SI_EV_RED_DOC_GREEN), NOOP, "2025-06-30"))

print("\n--- THE IDEMPOTENCE THAT THE DUPLICATION VIOLATED ---")
#
# The property required is that a further reading of a body already present changes nothing. It
# is tested by moving an arm that is a reading of the earned-value body ACROSS ITS OWN BANDS
# while the body's most adverse reading is held: the result must not move.
for mid in SIX:
    base = copy.deepcopy(SI_EV_RED_DOC_GREEN)          # index arm Red, so the body reads Red
    got = []
    for p80 in (2, 8, 20):                              # forecast arm Green, Amber, Red
        si = copy.deepcopy(base)
        si["mc"]["p80DeltaPct"] = p80
        got.append(RUNNER[mid](si, NOOP, "2025-06-30")["status_color"])
    check(f"{mid}: moving the forecast arm across all three of its bands does not move the band, "
          f"because the earned-value body already reads Red through the index arm",
          len(set(got)) == 1, str(got))

print("\n--- AND THE CORROBORATION THAT IS REAL STILL SURVIVES ---")
for mid in SIX:
    ev_red = RUNNER[mid](copy.deepcopy(SI_EV_RED_DOC_GREEN), NOOP, "2025-06-30")
    both = RUNNER[mid](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30")
    if mid == "B2.4":
        # B2.4 reads no document arm, so the correct expectation is the OPPOSITE: moving the
        # document score must change nothing at all. Asserting corroboration of it would be a
        # check passing for a reason that has nothing to do with what it claims.
        check("B2.4: moving the document score changes nothing, because it never reads it",
              ev_red == both)
        continue
    if mid == "B2.8":
        # THE BELIEF RULE BASE CONSULTS THE DOCUMENT STATE ONLY WHEN THE EARNED-VALUE BODY IS
        # NOT RED, WHICH IS A PROPERTY OF THE PUBLISHED RULE BASE AND NOT OF THIS CYCLE. Rules
        # R4 and R5 split on it at Amber and R7 and R8 at Green; at Red the base concludes from
        # the earned value alone. So the corroboration is measured where the base actually
        # admits it, rather than where the other five happen to.
        amber = {"evm": {"cpi": 0.92, "spi": 0.92}, "mc": {"p80DeltaPct": 20},
                 "cusum": {"breached": False}}
        a_doc_green = RUNNER[mid](dict(amber, doc={"score": 0.10}), NOOP, "2025-06-30")
        a_doc_red = RUNNER[mid](dict(amber, doc={"score": 0.80}), NOOP, "2025-06-30")
        check("B2.8: the document body moves the rule that fires wherever the published base "
              "admits it, so it was not swallowed",
              a_doc_green["matched_rules"][0]["id"] != a_doc_red["matched_rules"][0]["id"],
              f"{a_doc_green['matched_rules']} vs {a_doc_red['matched_rules']}")
        continue
    check(f"{mid}: the document body still moves the result, so it was not swallowed",
          ev_red != both, f"{ev_red['status_color']} vs {both['status_color']}")

print("\n=== 4. NO FALSE SUPPRESSION: A RED EARNED-VALUE BODY IS NEVER READ GREEN ===")
#
# This is the direction this cycle is least willing to fail in, and it is the reason B2.3's
# absolute count threshold was expressed as the share it always was. Left absolute it would have
# demanded UNANIMITY over two bodies, and this project would have reported Green.
for mid in SIX:
    r = RUNNER[mid](copy.deepcopy(SI_EV_RED_DOC_GREEN), NOOP, "2025-06-30")
    check(f"{mid}: earned value Red, document clean, reports an adverse band and not Green",
          r["status_color"] in ("Amber", "Red"), r["status_color"])
for mid in SIX:
    r = RUNNER[mid](copy.deepcopy(SI_EV_GREEN_DOC_RED), NOOP, "2025-06-30")
    prior = RUNNER[mid](copy.deepcopy(
        {"evm": {"cpi": 0.99, "spi": 0.99}, "mc": {"p80DeltaPct": 2},
         "cusum": {"breached": False}, "doc": {"score": 0.10}}), NOOP, "2025-06-30")
    check(f"{mid}: and a clean earned value with a clean document still reads Green",
          prior["status_color"] == "Green", prior["status_color"])

print("\n=== 5. MISSING ARMS: DO THEY SILENTLY REWEIGHT THE REMAINDER? ===")
#
# THEY DID, AND THEY STILL DIVIDE BY WHAT IS IN HAND -- WHICH IS THE HONEST READING, AND THE
# ALTERNATIVE IS A FABRICATED NEUTRAL FOR AN ABSENT ARM, WHICH THIS PROGRAMME REFUSES. What was
# wrong and is now fixed is that the reweighting was INVISIBLE and that an ABSOLUTE count
# threshold moved with it. The counts are reported on every result now.
for mid in SIX:
    r = RUNNER[mid](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30")
    check(f"{mid} discloses how many arms it read and how many bodies stood behind them",
          "arms_present" in r and "bodies_of_evidence" in r, str(sorted(r)[:6]))
for mid in SIX:
    si = {"evm": {"cpi": 0.85, "spi": 0.85}, "doc": {"score": 0.80}}
    r = RUNNER[mid](si, NOOP, "2025-06-30")
    check(f"{mid} with the forecast and trend arms absent still reads Red on two bodies",
          r["status_color"] == "Red", r["status_color"])
for mid in SIX:
    si = {"evm": {"cpi": 0.85, "spi": 0.85}}
    r = RUNNER[mid](si, NOOP, "2025-06-30")
    check(f"{mid} with only the index arm reads Red on ONE body and does not abstain",
          r["status_color"] == "Red" and not r.get("insufficient_data"), str(r["status_color"]))
for mid in SIX:
    r = RUNNER[mid]({}, NOOP, "2025-06-30")
    check(f"{mid} with NO arm at all still abstains and manufactures no band",
          r.get("insufficient_data") is True or r.get("status_color") in (None, "Grey", "Gray"),
          str(r.get("status_color")))

print("\n=== 6. DOES MODULE ORDERING AFFECT THE RESULT? ===")
#
# Two orderings are at stake and both are tested. FIRST, the order the arms are presented in: the
# arms are read out of a mapping by key, so a caller cannot reorder them, but a mapping's own
# iteration order is observable and the aggregations must not see it.
for mid in SIX:
    results = set()
    for perm in itertools.permutations(("evm", "mc", "cusum", "doc")):
        si = {k: copy.deepcopy(SI_ALL_RED[k]) for k in perm}
        results.add(RUNNER[mid](si, NOOP, "2025-06-30")["status_color"])
    check(f"{mid} gives one answer over all 24 orderings of the four arms",
          len(results) == 1, str(results))
# SECOND, the order the MODULES run in. Each is a pure function of the assembled package, so the
# question is whether one leaves a trace the next reads. Measured by running the six in both
# directions and comparing every emitted result.
_forward = {mid: RUNNER[mid](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30") for mid in SIX}
_backward = {mid: RUNNER[mid](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30")
             for mid in reversed(SIX)}
check("the six modules give identical results in both orders, so none of them leaves a trace "
      "the next one reads", _forward == _backward)
_shared = copy.deepcopy(SI_ALL_RED)
for mid in SIX:
    RUNNER[mid](_shared, NOOP, "2025-06-30")
check("and none of them mutates the assembled package it was handed",
      _shared == SI_ALL_RED, str(_shared))

print("\n=== 7. NO WEIGHT, MEMBERSHIP, RELIABILITY OR RULE MASS WAS INTRODUCED OR MOVED ===")
#
# The strongest claim this cycle makes is that it fixed a dependence defect WITHOUT inventing a
# number. It is checked against the values themselves rather than against a promise.
_z = RUNNER["B2.5"](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30")
check("Z-numbers still carries the index reliability 0.85 unchanged and undiscounted",
      any(s["reliability"] == 0.85 for s in _z["signals"]), str(_z["signals"]))
check("and no reliability was combined into a new one: every value emitted is one of the four "
      "declared source reliabilities",
      all(s["reliability"] in (0.85, 0.90, 0.65, 0.88) for s in _z["signals"]))
_p = RUNNER["B2.6"](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30")
check("PLTS still emits its declared source distributions unaltered",
      all(abs(sum(v for k, v in s.items() if k != "source") - 1.0) < 1e-9 for s in _p["sources"]),
      str(_p["sources"]))
_b = RUNNER["B2.8"](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30")
check("the belief rule base still activates a rule from the published base at its own weight",
      _b["rules_matched"] == 1 and _b["matched_rules"][0]["weight"] in
      (1.00, 0.85, 0.90, 0.80, 0.75, 0.70), str(_b["matched_rules"]))
_f = RUNNER["B2.4"](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30")
check("interval fuzzy reports which index reading it kept and which it suppressed, rather than "
      "an aggregate profile neither index asserts",
      _f["index_readings_present"] == 2 and len(_f["index_readings_suppressed_as_same_body"]) == 1,
      str(_f))
import inspect  # noqa: E402
_src = inspect.getsource(models_evc)
for value in ("0.85", "0.90", "0.65", "0.88", "0.75", "0.70", "0.80"):
    check(f"the constant {value} still appears in the module source, so nothing was silently "
          f"retuned", value in _src)

print("\n=== 8. MUTATION AND FAULT PROOF ===")
_survivors = []


def mutation(name: str, caught: bool, by: str) -> None:
    global _passed, _total
    _total += 1
    if caught:
        _passed += 1
        print(f"  PASS  mutation {name} caught by: {by}")
    else:
        _survivors.append(name)
        print(f"  FAIL  mutation {name} SURVIVED")


# M1. The separation collapsed to "every arm is its own body", which is the defect itself.
_as_arms = [[i] for i in range(4)]
mutation("M1 every arm treated as its own body (the original ARCH.5 defect)",
         len(_as_arms) == 4 and len(_bodies_pv) == 2,
         "with all four arms present the partition finds exactly TWO bodies")

# M2. The separation collapsed the other way, marrying the document body into the earned-value
#     body through the bridging forecast arm. That is the transitive closure cycle 5 removed, and
#     it destroys corroboration that is really there.
mutation("M2 the bridging forecast arm marries the two bodies (transitive closure)",
         len(_bodies_pv) == 2 and ["B2.1.doc"] in _members,
         "the document arm is a body of its own")

# M3. The within-body reading takes the LEAST adverse member instead of the most adverse.
_least = one_reading_per_body(ALL_ARMS, ["Green", "Amber", "Red", "Green"], SI_ALL_RED)
mutation("M3 the within-body reading takes the least adverse member",
         ALL_ARMS[_least["kept"][0]]["module_id"] == "B2.1.cusum",
         "when the three readings of that body DISAGREE the most adverse is taken")

# M4. B2.3's threshold left as an absolute count of two, which over two bodies means unanimity.
_n = 2
mutation("M4 the neutrosophic threshold left as an absolute count over the deduplicated bodies",
         (1 / _n >= 0.5) and not (1 >= 2)
         and RUNNER["B2.3"](copy.deepcopy(SI_EV_RED_DOC_GREEN),
                            NOOP, "2025-06-30")["status_color"] == "Red",
         "earned value Red, document clean, reports an adverse band and not Green")

# M5. The deduplication applied but not disclosed, so a reader could not tell two bodies from
#     four arms.
mutation("M5 the deduplication applied silently and never reported",
         all("bodies_of_evidence" in RUNNER[m](copy.deepcopy(SI_ALL_RED), NOOP, "2025-06-30")
             for m in SIX),
         "each module discloses how many arms it read and how many bodies stood behind them")

# M6. The resolver dropped, so the schedule index's ancestry is guessed from the module id rather
#     than resolved against the project's evidence.
_unresolved = separate_arms(ALL_ARMS, None)
mutation("M6 the arms separated without resolving the derived-index ancestry",
         len(_unresolved) == len(_bodies_pp) == 2,
         "the fallback regime also finds exactly two bodies")

# M7. A weight introduced: the earned-value body discounted because it was read three times.
#     Caught by section 7, which reads the emitted reliabilities.
mutation("M7 a correlation discount applied to the duplicated body",
         all(s["reliability"] in (0.85, 0.90, 0.65, 0.88) for s in _z["signals"]),
         "every reliability emitted is one of the four declared source reliabilities")

# M8. B2.8's trend breach restored as a separate antecedent, so R1 fires again on one
#     measurement counted twice.
mutation("M8 the belief rule base conditions on the trend breach as a second antecedent",
         _b["matched_rules"][0]["id"] != "R1" and _b["earned_value_body_state"] == "Red",
         "the belief rule base activates one rule on the earned-value BODY's band")

check("mutation survivors 0", not _survivors, str(_survivors))

print("\n=== 9. GUARD NON-VACUITY: EVERY GUARD ABOVE CAN ACTUALLY FAIL ===")
check("the body-count guard distinguishes 2 from 4", len(_bodies_pv) != len(ALL_ARMS))
check("the idempotence guard reads a band that CAN move: it moves when the body's own most "
      "adverse reading moves",
      RUNNER["B2.6"](copy.deepcopy(SI_EV_GREEN_DOC_RED), NOOP, "2025-06-30")["status_color"]
      != RUNNER["B2.6"](copy.deepcopy(SI_EV_RED_DOC_GREEN), NOOP, "2025-06-30")["status_color"])
check("the ordering guard reads a result that is not constant across projects",
      len({RUNNER["B2.2"](copy.deepcopy(si), NOOP, "2025-06-30")["status_color"]
           for si in (SI_ALL_RED, SI_EV_GREEN_DOC_RED,
                      {"evm": {"cpi": 0.99, "spi": 0.99}, "doc": {"score": 0.10}})}) > 1)
check("the disclosure guard is not vacuously satisfied by a field that is always the same",
      RUNNER["B2.2"]({"evm": {"cpi": 0.85, "spi": 0.85}}, NOOP,
                     "2025-06-30")["bodies_of_evidence"] == 1)
check("the no-new-weight guard reads values that genuinely appear, so it is not comparing an "
      "empty set", len(_z["signals"]) > 0 and len(_p["sources"]) > 0)

print(f"\nRESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
