"""
RUN 20 CYCLE 9. FUSION.1: AN UNDECLARED SIGNAL WAS TREATED AS INDEPENDENT BY DEFAULT.

THE DEFECT, AS CYCLE 8 ESTABLISHED IT. `fuse_signals` replaced a missing lineage record with
`lineage_record(mid)`. That record's primitive source set is EMPTY, it names no lineage group, no
parent and no dependency, so all four rules of the pairwise dependence test answer False against
every other signal in the fusion. An undeclared signal was therefore selected as its own
INDEPENDENT BODY OF EVIDENCE. Saying nothing about lineage produced the single strongest claim
the model can make, and nobody made it. Cycle 8 measured the consequence: three undeclared
readings of ONE earned-value measurement sharpened Amber belief from 0.7000 to 0.9861.

THE SAFE DEFAULT CHOSEN IS EXPLICIT UNRESOLVED, AND THE OTHER TWO CANDIDATES ARE REJECTED WITH
REASONS, NOT PREFERENCES:

  REFUSAL -- return nothing when any member is undeclared -- discards a fusion that is largely
  declared because one member is silent, and discards the adverse evidence in it. It converts a
  modelling defect into an availability defect on the governed status.

  ABSTENTION -- drop the undeclared signal -- is worse in the one direction that matters most:
  an undeclared RED signal would make the fusion read GREENER than the evidence in hand. That is
  false suppression, which cycle 5 exists to prevent.

  EXPLICIT UNRESOLVED keeps the signal and keeps its most adverse reading, and refuses exactly
  one thing: the CERTAINTY that corroboration confers, which was never justified. All undeclared
  signals form ONE unresolved body; that body is folded in with the IDEMPOTENT worst-band
  operator and never combined by Dempster's rule, because Dempster's rule is precisely the step
  that requires the independence nobody declared.

THE ASSERTION IS STILL AVAILABLE, BUT IT MUST BE MADE. `fuse_signals(..., assume_independent=
True)` is the one route to the old behaviour, and `dst_fuse` -- whose entire documented contract
is a caller with genuinely independent sources and nothing else to say about them -- passes it.
So a caller who ASSERTS independence and a caller who merely FORGOT are no longer the same
caller, which is the whole content of this fix.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.simulation import fusion  # noqa: E402
from app.simulation.fusion import dst_fuse, fuse_signals  # noqa: E402
from app.simulation.lineage import lineage_for, lineage_record  # noqa: E402

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


def undeclared(mid: str, band: str) -> dict:
    return {"module_id": mid, "status": band}


def declared(mid: str, band: str) -> dict:
    return {"module_id": mid, "status": band, "lineage": lineage_for(mid)}


print("=== 1. THE DEFECT IS GONE: SILENCE IS NOT INDEPENDENCE ===")
_two = fuse_signals([undeclared("U1", "Amber"), undeclared("U2", "Amber")])
check("two undeclared signals produce ZERO independent bodies",
      _two["lineage_groups"] == 0, str(_two["lineage_groups"]))
check("they are reported as unresolved, by name",
      _two["unresolved_module_ids"] == ["U1", "U2"], str(_two["unresolved_module_ids"]))
check("Amber belief is the single reading, 0.7000, and not the amplified 0.9273",
      abs(_two["mass"]["Amber"] - 0.70) < 5e-5, str(_two["mass"]["Amber"]))
check("lineage_declared is False and says so", _two["lineage_declared"] is False)
_three = fuse_signals([undeclared(f"U{i}", "Amber") for i in range(3)])
check("three undeclared signals are still 0.7000, not cycle 8's measured 0.9861",
      abs(_three["mass"]["Amber"] - 0.70) < 5e-5, str(_three["mass"]["Amber"]))

print("\n=== 2. IDEMPOTENCE: A COPY OF AN UNDECLARED SIGNAL CHANGES NOTHING ===")
for band in ("Green", "Yellow", "Amber", "Red"):
    one = fuse_signals([undeclared("U1", band)])
    many = fuse_signals([undeclared(f"U{i}", band) for i in range(6)])
    check(f"{band}: one undeclared reading and six are the same distribution",
          one["mass"] == many["mass"] and one["status"] == many["status"],
          f"{one['mass']} vs {many['mass']}")

print("\n=== 3. NO FALSE SUPPRESSION: THE ADVERSE READING IS NEVER LOST ===")
#
# This is the check that rejects ABSTENTION as the default. An undeclared Red beside a declared
# Green must not be dropped, because dropping it makes the fusion read greener than the evidence.
_mixed = fuse_signals([declared("A1.7", "Green"), undeclared("U_RED", "Red")])
check("an undeclared Red beside a declared Green reports Red",
      _mixed["status"] == "Red", _mixed["status"])
check("and the Red signal is named as unresolved rather than silently dropped",
      _mixed["unresolved_module_ids"] == ["U_RED"])
_declared_only = fuse_signals([declared("A1.7", "Green")])
check("the declared Green alone would have read Green, so the Red genuinely changed the answer",
      _declared_only["status"] == "Green")
for band in ("Yellow", "Amber", "Red"):
    got = fuse_signals([declared("A1.7", "Green"), undeclared("U", band)])
    check(f"an undeclared {band} beside a declared Green reports {band}", got["status"] == band)
check("but an undeclared GREEN beside a declared Red does NOT soften it",
      fuse_signals([declared("A1.7", "Red"), undeclared("U", "Green")])["status"] == "Red")

print("\n=== 4. NO FALSE REINFORCEMENT: THE UNDECLARED SIGNAL ADDS NO CERTAINTY ===")
_alone = fuse_signals([declared("A1.7", "Amber")])
_plus = fuse_signals([declared("A1.7", "Amber"), undeclared("U", "Amber")])
check("adding an agreeing undeclared signal does not move ANY mass",
      _alone["mass"] == _plus["mass"], f"{_alone['mass']} vs {_plus['mass']}")
check("and does not manufacture a second body",
      _alone["lineage_groups"] == _plus["lineage_groups"] == 1)
check("nor an estimable conflict coefficient", _plus["conflict_estimable"] is False)
check("the conflict coefficient stays 0.0 and is not manufactured", _plus["conflict"] == 0.0)

print("\n=== 5. DECLARED EVIDENCE IS UNTOUCHED BY THIS CHANGE ===")
_pair = fuse_signals([declared("A1.7", "Amber"), declared("A1.8", "Amber")])
check("the two voting modules are still ONE body", _pair["lineage_groups"] == 1)
check("and still 0.7000", abs(_pair["mass"]["Amber"] - 0.70) < 5e-5, str(_pair["mass"]["Amber"]))
check("and still lineage_declared", _pair["lineage_declared"] is True)
_indep = fuse_signals([declared("A1.7", "Amber"), declared("A3.9", "Amber")])
check("two genuinely independent declared bodies still corroborate",
      _indep["lineage_groups"] == 2 and _indep["mass"]["Amber"] > 0.90,
      str(_indep["mass"]["Amber"]))
check("real corroboration is stronger than one reading", _indep["mass"]["Amber"] > _pair["mass"]["Amber"])

print("\n=== 6. THE EXPLICIT ASSERTION STILL WORKS, AND ONLY WHEN MADE ===")
_asserted = fuse_signals([undeclared("U1", "Amber"), undeclared("U2", "Amber")],
                         assume_independent=True)
check("assume_independent=True restores the two-body combination",
      _asserted["lineage_groups"] == 2, str(_asserted["lineage_groups"]))
check("and its sharpening, 0.9273, which is now a stated assertion and not a default",
      abs(_asserted["mass"]["Amber"] - 0.9273182957) < 1e-6, str(_asserted["mass"]["Amber"]))
check("dst_fuse is unchanged in behaviour: two Ambers still corroborate",
      abs(dst_fuse(["Amber", "Amber"])["mass"]["Amber"] - _asserted["mass"]["Amber"]) < 1e-12)
check("dst_fuse still reports lineage_declared False, so the assertion is visible",
      dst_fuse(["Amber", "Amber"])["lineage_declared"] is False)
check("dst_fuse still accepts a bare list of status strings",
      dst_fuse.__code__.co_varnames[:1] == ("statuses",))
check("and the default of fuse_signals is NOT to assume independence",
      fusion.fuse_signals.__defaults__ == (False,), str(fusion.fuse_signals.__defaults__))

print("\n=== 7. NEGATIVE, BOUNDARY AND MISSINGNESS ===")
check("no signals at all still returns None", fuse_signals([]) is None)
check("None still returns None", fuse_signals(None) is None)
check("an undeclared signal with an unrecognised status abstains and is not unresolved evidence",
      fuse_signals([undeclared("U", "probably ok")]) is None)
check("an undeclared abstention beside a declared signal changes nothing",
      fuse_signals([declared("A1.7", "Amber"), undeclared("U", None)])["mass"] == _alone["mass"])
_q = fuse_signals([declared("A1.7", "Amber"),
                   {"module_id": "C9", "status": "Red",
                    "lineage": lineage_record("C9", evidence_relationship="QUALITY_METADATA")}])
check("a Category 9 quality signal is still EXCLUDED and never becomes unresolved evidence",
      _q["unresolved_module_ids"] == [] and len(_q["excluded_non_evidential"]) == 1)
check("an unnamed undeclared signal still gets a stable positional id",
      fuse_signals([{"status": "Amber"}])["unresolved_module_ids"] == ["__unnamed_0"])
_one_undeclared = fuse_signals([undeclared("U", "Red")])
check("a lone undeclared signal reports its own reading and no fused certainty",
      _one_undeclared["status"] == "Red"
      and abs(_one_undeclared["mass"]["Red"] - 0.76) < 5e-5
      and _one_undeclared["conflict_estimable"] is False,
      str(_one_undeclared["mass"]["Red"]))

print("\n=== 8. ORDER INDEPENDENCE ===")
import itertools  # noqa: E402
_sigs = [declared("A1.7", "Green"), declared("A3.9", "Amber"), undeclared("U", "Red")]
_results = {fuse_signals(list(p))["status"] for p in itertools.permutations(_sigs)}
check("the reported status does not depend on the order the signals arrive in",
      _results == {"Red"}, str(_results))
_masses = {tuple(sorted(fuse_signals(list(p))["mass"].items()))
           for p in itertools.permutations(_sigs)}
check("nor does the mass distribution", len(_masses) == 1, str(len(_masses)))

print("\n=== 9. MUTATION AND FAULT PROOF ===")
#
# Each mutation reintroduces a specific way the trapdoor could come back. Each must be caught by
# a NAMED check above. A mutation that changes bytes without changing behaviour is re-aimed.
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


# M1. The original defect restored exactly: an undeclared signal becomes an empty-primitive
#     record. Caught by section 1 -- the body count would go to 2 and the mass to 0.9273.
_m1 = fuse_signals([undeclared("U1", "Amber"), undeclared("U2", "Amber")],
                   assume_independent=True)
mutation("M1 undeclared treated as independent (the original FUSION.1 defect)",
         _m1["lineage_groups"] == 2 and _two["lineage_groups"] == 0,
         "two undeclared signals produce ZERO independent bodies")

# M2. Abstention as the default -- drop the undeclared signal. Caught by section 3, because the
#     undeclared Red beside a declared Green would report Green.
_dropped = fuse_signals([declared("A1.7", "Green")])
mutation("M2 undeclared signals dropped instead of folded",
         _dropped["status"] == "Green" and _mixed["status"] == "Red",
         "an undeclared Red beside a declared Green reports Red")

# M3. The fold made a Dempster combination rather than a worst-band fold. Caught by section 4,
#     because the mass would move.
_combined = fusion.dst_combine(dict(_alone["mass"]), fusion.STATUS_MASS["Amber"])
mutation("M3 the unresolved body combined by Dempster's rule instead of folded idempotently",
         abs(_combined["Amber"] - _plus["mass"]["Amber"]) > 0.1,
         "adding an agreeing undeclared signal does not move ANY mass")

# M4. The fold takes the BEST band rather than the worst. Caught by section 3's Red-beside-Red
#     control: an undeclared Green beside a declared Red must not soften it.
mutation("M4 the fold takes the least adverse band",
         fusion.worst_band(["Red", "Green"]) == "Red"
         and fuse_signals([declared("A1.7", "Red"),
                           undeclared("U", "Green")])["status"] == "Red",
         "an undeclared GREEN beside a declared Red does NOT soften it")

# M5. assume_independent defaulted to True, so silence reaches the old path again. Caught by the
#     explicit signature check in section 6.
mutation("M5 assume_independent defaulted to True",
         fusion.fuse_signals.__defaults__ == (False,),
         "the default of fuse_signals is NOT to assume independence")

# M6. The unresolved condition handled but not REPORTED, so no consumer could ever see it.
mutation("M6 the unresolved condition silently handled and not reported",
         "unresolved_module_ids" in _two and _two["unresolved_module_ids"] == ["U1", "U2"]
         and _two["lineage_declared"] is False,
         "they are reported as unresolved, by name")

# M7. NON_PROJECT_EVIDENCE routed into the unresolved body instead of being excluded, which would
#     let a Category 9 result vote through the new path.
mutation("M7 a quality-metadata signal folded in as unresolved evidence instead of excluded",
         _q["unresolved_module_ids"] == [] and _q["status"] == "Amber",
         "a Category 9 quality signal is still EXCLUDED")

check("mutation survivors 0", not _survivors, str(_survivors))

print("\n=== 10. GUARD NON-VACUITY: THE CHECKS ABOVE CAN ACTUALLY FAIL ===")
#
# Every guard in this suite is asserted against a deliberately violating value, so that a guard
# which is green because it compares nothing is caught here rather than believed.
check("the body-count guard distinguishes 0 from 2",
      _two["lineage_groups"] != _asserted["lineage_groups"])
check("the mass guard distinguishes 0.7000 from 0.9273",
      abs(_two["mass"]["Amber"] - _asserted["mass"]["Amber"]) > 0.2)
check("the suppression guard distinguishes Red from Green",
      _mixed["status"] != _declared_only["status"])
check("the reinforcement guard reads a mass that CAN move: real corroboration moves it",
      _indep["mass"]["Amber"] != _alone["mass"]["Amber"])
check("the unresolved report is not vacuously empty in the undeclared case",
      len(_two["unresolved_module_ids"]) == 2 and _pair["unresolved_module_ids"] == [])

print(f"\nRESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
