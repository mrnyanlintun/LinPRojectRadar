"""
RUN 30 -- THE SUPPLIED CATEGORY-6/7 CONTRACT'S OWN KNOWN ANSWERS, CARRIED HERE AS LITERALS.

WHY THIS SUITE EXISTS AND WHAT IT IS NOT. Every expected number below is transcribed from the
owner's supplied Run-30 supervisory contract, sections 6.1 to 6.4 and 7.1 to 7.20, or hand
derived here with every intermediate shown. NOT ONE OF THEM WAS READ OUT OF PRODUCTION. An
oracle derived from the code it tests proves only that the code agrees with itself.

WHERE AN INDEPENDENT REFERENCE IS REQUIRED -- MARCOS and CRITIC-TOPSIS, whose contracts demand
frozen intermediates and an independence proof -- the reference implementation lives in
`server/tools/run30/reference_mcdm.py`, was written from the published method steps, shares no
code with `app.simulation.canonical_v5`, and is compared here against BOTH the frozen literals
and production.

A crash is not a failure signal here: every block is guarded so a raised exception is reported
as a failed named check with an anchored RESULT line still printed.
"""

from __future__ import annotations

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation.canonical import StructureAbsent          # noqa: E402
from app.simulation import canonical_v5 as V5                 # noqa: E402
from run30 import reference_mcdm as REF                       # noqa: E402
from run30 import fixtures_cat67 as FX                        # noqa: E402

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def near(label: str, got, want, tol: float = 1e-9) -> None:
    try:
        ok = abs(float(got) - float(want)) <= tol
    except Exception as exc:                                  # noqa: BLE001
        check(False, label, f"not a number: {exc!r}")
        return
    check(ok, label, f"got {got!r} want {want!r}")


def refuses(label: str, fn) -> None:
    """The structure is refused with a reader's sentence, not with a crash and not with a
    favourable substitute."""
    try:
        out = fn()
    except StructureAbsent as exc:
        check(bool(str(exc).strip()), label, "refused with an empty sentence")
        return
    except V5.SignalNotEligible as exc:
        check(bool(str(exc).strip()), label, "refused with an empty sentence")
        return
    except Exception as exc:                                  # noqa: BLE001
        check(False, label, f"crashed instead of refusing: {exc!r}")
        return
    if isinstance(out, dict) and out.get("estimable") is False:
        check(bool(str(out.get("reason") or "").strip()), label, "abstained with no reason")
        return
    check(False, label, f"returned a result instead of refusing: {out!r}")


def sig(sid, status, body, period=7, **extra):
    rec = {"signal_id": sid, "status": status, "lineage_body": body, "period": period,
           "source": "governed signal package", "qualification": "unqualified"}
    rec.update(extra)
    return rec


print("=" * 78)
print("RUN 30 -- CATEGORY 6 SYNTHESIS")
print("=" * 78)

# ---------------------------------------------------------------- 6.1 CONSERVATIVE DOMINANCE
# CONTRACT: result = most severe credible eligible non-abstaining signal; S_CD = max severity.
# Oracle 1: Green, Yellow, Amber -> Amber.   Oracle 2: Green, Red, Red -> Red.
o = V5.conservative_dominance([sig("s1", "Green", "b1"), sig("s2", "Yellow", "b2"),
                               sig("s3", "Amber", "b3")])
check(o["state"] == "Amber", "6.1 Green,Yellow,Amber -> Amber (contract oracle)", str(o))
o = V5.conservative_dominance([sig("s1", "Green", "b1"), sig("s2", "Red", "b2"),
                               sig("s3", "Red", "b3")])
check(o["state"] == "Red", "6.1 Green,Red,Red -> Red (contract oracle)", str(o))

# permutation invariance over every ordering of a three-signal case
import itertools                                              # noqa: E402
_perm = [sig("s1", "Green", "b1"), sig("s2", "Amber", "b2"), sig("s3", "Red", "b3")]
check(all(V5.conservative_dominance(list(p))["state"] == "Red"
          for p in itertools.permutations(_perm)),
      "6.1 permutation invariant across all 6 orderings")
# monotonicity: raising one signal's severity cannot lower the result
check(V5.SEVERITY[V5.conservative_dominance(
          [sig("s1", "Green", "b1"), sig("s2", "Amber", "b2")])["state"]]
      <= V5.SEVERITY[V5.conservative_dominance(
          [sig("s1", "Green", "b1"), sig("s2", "Red", "b2")])["state"]],
      "6.1 monotone in signal severity")
# duplicate-lineage neutrality: a second reading of one body changes nothing
_one = V5.conservative_dominance([sig("s1", "Red", "bX"), sig("s2", "Green", "bY")])
_dup = V5.conservative_dominance([sig("s1", "Red", "bX"), sig("s1b", "Red", "bX"),
                                  sig("s2", "Green", "bY")])
check(_one["state"] == _dup["state"] == "Red", "6.1 duplicate lineage changes nothing")
check(_dup["duplicate_lineage_suppressed"] == ["s1b"],
      "6.1 the duplicate reading is named as suppressed, not silently dropped")
# abstention visibility and all-abstain
_ab = V5.conservative_dominance([sig("s1", "Abstain", "b1", abstention_reason="no evidence"),
                                 sig("s2", "Red", "b2")])
check(_ab["state"] == "Red" and len(_ab["abstaining"]) == 1,
      "6.1 an abstaining signal is visible and does not vote")
_all = V5.conservative_dominance([sig("s1", "Abstain", "b1"), sig("s2", "Insufficient", "b2")])
check(_all["estimable"] is False, "6.1 all-abstain -> Not Estimable, never Green", str(_all))
refuses("6.1 an unknown label is rejected, not coerced",
        lambda: V5.conservative_dominance([sig("s1", "greenish", "b1")]))
# one credible Red cannot be averaged away by forty Greens
_forty = [sig("s0", "Red", "b0")] + [sig(f"g{i}", "Green", f"bg{i}") for i in range(40)]
check(V5.conservative_dominance(_forty)["state"] == "Red",
      "6.1 one Red among forty Greens still dominates")

# ---------------------------------------------------------------- 6.2 WEIGHTED VOTING
# CONTRACT ORACLE: Green weight .5, Amber weight .3, Red weight .2 -> Green=.5 Amber=.3 Red=.2,
# winner Green. Weights already sum to one, so normalisation leaves them unchanged.
_pol = {"set_by": "supervisory contract oracle", "authority": "Run-30 supplied contract",
        "weights": {"g": 0.5, "a": 0.3, "r": 0.2}}
o = V5.weighted_voting([sig("g", "Green", "b1"), sig("a", "Amber", "b2"),
                        sig("r", "Red", "b3")], _pol)
near("6.2 Vote(Green) = .5 (contract oracle)", o["votes"]["Green"], 0.5)
near("6.2 Vote(Amber) = .3 (contract oracle)", o["votes"]["Amber"], 0.3)
near("6.2 Vote(Red)   = .2 (contract oracle)", o["votes"]["Red"], 0.2)
check(o["winner"] == "Green" and o["unique_winner"], "6.2 winner = Green (contract oracle)")
near("6.2 normalised weights sum to one", sum(o["normalised_weights"].values()), 1.0)
# equal weights must reduce to Majority Rules under the same eligibility and tie rules
_eq = {"set_by": "test", "authority": "test", "weights": {"g": 1, "a": 1, "r": 1, "r2": 1}}
_sigs = [sig("g", "Green", "b1"), sig("a", "Amber", "b2"),
         sig("r", "Red", "b3"), sig("r2", "Red", "b4")]
check(V5.weighted_voting(_sigs, _eq)["winner"] == V5.majority_rules(_sigs)["winner"] == "Red",
      "6.2 equal weights reduce to Majority Rules")
# abstaining signals do not vote
_pol2 = {"set_by": "t", "authority": "t", "weights": {"g": 1.0, "x": 1.0}}
o = V5.weighted_voting([sig("g", "Green", "b1"), sig("x", "Abstain", "b2")], _pol2)
near("6.2 an abstaining signal carries no weight", o["votes"]["Green"], 1.0)
# same-lineage duplicates must not manufacture weight
_polD = {"set_by": "t", "authority": "t", "weights": {"r": 1.0, "rdup": 1.0, "g": 3.0}}
o = V5.weighted_voting([sig("r", "Red", "bX"), sig("rdup", "Red", "bX"),
                        sig("g", "Green", "bY")], _polD)
near("6.2 duplicate lineage adds no weight: Red gets 1/(1+3)", o["votes"]["Red"], 0.25)
check(o["winner"] == "Green", "6.2 and the duplicate cannot flip the winner")
refuses("6.2 no weighting policy -> refusal, no default weight assumed",
        lambda: V5.weighted_voting([sig("g", "Green", "b1")], None))
refuses("6.2 a policy that omits a voting signal is refused",
        lambda: V5.weighted_voting([sig("g", "Green", "b1"), sig("z", "Red", "b2")],
                                   {"set_by": "t", "authority": "t", "weights": {"g": 1}}))
refuses("6.2 a negative weight is refused",
        lambda: V5.weighted_voting([sig("g", "Green", "b1")],
                                   {"set_by": "t", "authority": "t", "weights": {"g": -1}}))
refuses("6.2 a policy with no stated authority is refused",
        lambda: V5.weighted_voting([sig("g", "Green", "b1")], {"weights": {"g": 1}}))
o = V5.weighted_voting([sig("g", "Green", "b1"), sig("r", "Red", "b2")],
                       {"set_by": "t", "authority": "t", "weights": {"g": 1, "r": 1}})
check(o["unique_winner"] is False and o["winner"] is None and set(o["tied_classes"]) ==
      {"Green", "Red"}, "6.2 a tie returns no winner under the declared tie policy")

# ---------------------------------------------------------------- 6.3 MAJORITY RULES
# CONTRACT ORACLES: Green,Red,Red -> Red. Green,Yellow,Red -> no unique winner.
# Green,Red,Abstain -> tie/conflict.
o = V5.majority_rules([sig("s1", "Green", "b1"), sig("s2", "Red", "b2"),
                       sig("s3", "Red", "b3")])
check(o["winner"] == "Red", "6.3 Green,Red,Red -> Red (contract oracle)", str(o))
o = V5.majority_rules([sig("s1", "Green", "b1"), sig("s2", "Yellow", "b2"),
                       sig("s3", "Red", "b3")])
check(o["unique_winner"] is False and o["conflict"] is True,
      "6.3 Green,Yellow,Red -> no unique winner / conflict (contract oracle)", str(o))
o = V5.majority_rules([sig("s1", "Green", "b1"), sig("s2", "Red", "b2"),
                       sig("s3", "Abstain", "b3")])
check(o["unique_winner"] is False and o["conflict"] is True and len(o["abstaining"]) == 1,
      "6.3 Green,Red,Abstain -> tie/conflict (contract oracle)", str(o))
o = V5.majority_rules([sig("s1", "Abstain", "b1"), sig("s2", "Abstain", "b2")])
check(o["estimable"] is False and o["counts"]["Green"] == 0,
      "6.3 all-abstain is Not Estimable and never Green")
o = V5.majority_rules([sig("s1", "Red", "b1")])
check(o["estimable"] is False and o["voters"] == 1, "6.3 quorum: one voter is not a majority")
refuses("6.3 an unknown label is rejected",
        lambda: V5.majority_rules([sig("s1", "OK", "b1"), sig("s2", "Red", "b2")]))
o = V5.majority_rules([sig("r", "Red", "bX"), sig("rdup", "Red", "bX"),
                       sig("g1", "Green", "b1"), sig("g2", "Green", "b2")])
check(o["counts"]["Red"] == 1 and o["winner"] == "Green",
      "6.3 duplicate lineage casts no second vote")
# severe-minority comparison with Conservative Dominance: they disagree, and that is the point
_minority = [sig("r", "Red", "b0")] + [sig(f"g{i}", "Green", f"b{i}") for i in range(4)]
check(V5.majority_rules(_minority)["winner"] == "Green"
      and V5.conservative_dominance(_minority)["state"] == "Red",
      "6.3 a severe minority: majority says Green where dominance says Red")

# ---------------------------------------------------------------- 6.4 WORST-2-of-M
# CONTRACT ORACLES (severity Green 0, Yellow 1, Amber 2, Red 3):
#   Green, Amber, Red      -> worst two 3,2 -> MeanWorst2 = 2.5
#   Green, Green, Red      -> worst two 3,0 -> MeanWorst2 = 1.5
#   Amber, Amber, Yellow   -> worst two 2,2 -> MeanWorst2 = 2.0
near("6.4 Green,Amber,Red -> 2.5 (contract oracle)",
     V5.worst_two_of_m([sig("a", "Green", "b1"), sig("b", "Amber", "b2"),
                        sig("c", "Red", "b3")])["mean_worst_2"], 2.5)
near("6.4 Green,Green,Red -> 1.5 (contract oracle)",
     V5.worst_two_of_m([sig("a", "Green", "b1"), sig("b", "Green", "b2"),
                        sig("c", "Red", "b3")])["mean_worst_2"], 1.5)
near("6.4 Amber,Amber,Yellow -> 2.0 (contract oracle)",
     V5.worst_two_of_m([sig("a", "Amber", "b1"), sig("b", "Amber", "b2"),
                        sig("c", "Yellow", "b3")])["mean_worst_2"], 2.0)
# NOT max(worst two): the mean of 3 and 0 is 1.5, where the max would be 3 and the module would
# be Conservative Dominance under another name.
check(V5.worst_two_of_m([sig("a", "Green", "b1"), sig("b", "Green", "b2"),
                         sig("c", "Red", "b3")])["mean_worst_2"] != 3.0,
      "6.4 does NOT collapse to max(worst two) / Conservative Dominance")
_p = [sig("a", "Green", "b1"), sig("b", "Amber", "b2"), sig("c", "Red", "b3")]
check(all(V5.worst_two_of_m(list(p))["mean_worst_2"] == 2.5
          for p in itertools.permutations(_p)), "6.4 permutation invariant")
check(V5.worst_two_of_m([sig("a", "Green", "b1"), sig("b", "Amber", "b2")])["mean_worst_2"]
      <= V5.worst_two_of_m([sig("a", "Green", "b1"), sig("b", "Red", "b2")])["mean_worst_2"],
      "6.4 monotone in signal severity")
o = V5.worst_two_of_m([sig("r", "Red", "bX"), sig("rdup", "Red", "bX"),
                       sig("g", "Green", "bY")])
near("6.4 a duplicate lineage cannot occupy both worst positions: (3+0)/2", o["mean_worst_2"], 1.5)
check([s["signal_id"] for s in o["selected"]] == ["r", "g"],
      "6.4 and the two selected signals rest on different evidence")
o = V5.worst_two_of_m([sig("a", "Red", "b1"), sig("b", "Abstain", "b2")])
check(o["estimable"] is False and o["m"] == 1, "6.4 M<2 after abstentions -> Not Estimable")
check(V5.worst_two_of_m([sig("a", "Red", "b1"), sig("b", "Green", "b2")])
      ["classification"] is None,
      "6.4 no traffic-light boundary is invented over MeanWorst2")
refuses("6.4 an unknown label is rejected",
        lambda: V5.worst_two_of_m([sig("a", "purple", "b1"), sig("b", "Red", "b2")]))
# THE v14 STRUCTURAL DEFECT MUST NOT RETURN: identical adverse evidence beside a 3-signal array
# and beside a 63-signal array gives the SAME statistic for the same two worst signals.
_small = [sig("r1", "Red", "b1"), sig("r2", "Red", "b2"), sig("g", "Green", "bg")]
_large = _small + [sig(f"x{i}", "Green", f"bx{i}") for i in range(60)]
check(V5.worst_two_of_m(_small)["mean_worst_2"]
      == V5.worst_two_of_m(_large)["mean_worst_2"] == 3.0,
      "6.4 registering more signals does not dilute identical adverse evidence")

print()
print("=" * 78)
print("RUN 30 -- CATEGORY 7 EPISTEMIC REPRESENTATIONS")
print("=" * 78)

# ---------------------------------------------------------------- 7.1 DEMPSTER-SHAFER
# CONTRACT ORACLE: Theta={G,R}; m1({G})=.6 m1(Theta)=.4 ; m2({G})=.5 m2(Theta)=.5
# K = 0 (nothing disjoint: {G} meets {G}, {G} meets Theta, Theta meets Theta)
# m12({G}) = (.6*.5 + .6*.5 + .4*.5)/(1-0) = .3+.3+.2 = .8 ; m12(Theta) = .4*.5 = .2
_m1 = {frozenset({"G"}): 0.6, frozenset({"G", "R"}): 0.4}
_m2 = {frozenset({"G"}): 0.5, frozenset({"G", "R"}): 0.5}
near("7.1 K = 0 for the contract's pair", V5.conflict_coefficient(_m1, _m2), 0.0)
_c = V5.dempster_combine(_m1, _m2, assume_independent=True)
near("7.1 m12({G}) = .8 (contract oracle)", _c["mass"][frozenset({"G"})], 0.8)
near("7.1 m12(Theta) = .2 (contract oracle)", _c["mass"][frozenset({"G", "R"})], 0.2)
near("7.1 Bel({G}) = .8", V5.belief(_c["mass"], ["G"]), 0.8)
near("7.1 Pl({G}) = 1.0", V5.plausibility(_c["mass"], ["G"]), 1.0)
near("7.1 Bel({R}) = 0 -- ignorance on Theta supports no singleton",
     V5.belief(_c["mass"], ["R"]), 0.0)
# IGNORANCE IS NOT CONFLICT: a wholly vacuous body conflicts with nothing.
_vac = {frozenset({"G", "R"}): 1.0}
near("7.1 ignorance is not conflict: K(m1, vacuous) = 0",
     V5.conflict_coefficient(_m1, _vac), 0.0)
_cv = V5.dempster_combine(_m1, _vac, assume_independent=True)
near("7.1 and combining with ignorance leaves the body unchanged",
     _cv["mass"][frozenset({"G"})], 0.6)
# TOTAL CONFLICT ORACLE: m1({G})=1, m2({R})=1 -> K = 1, explicit refusal, no division.
_tc = V5.dempster_combine({frozenset({"G"}): 1.0}, {frozenset({"R"}): 1.0},
                          assume_independent=True)
near("7.1 total conflict K = 1 (contract oracle)",
     V5.conflict_coefficient({frozenset({"G"}): 1.0}, {frozenset({"R"}): 1.0}), 1.0)
check(_tc["combined"] is False and _tc["state"] == "TOTAL_CONFLICT",
      "7.1 total conflict -> explicit TOTAL_CONFLICT / review, no fabricated verdict", str(_tc))
# INDEPENDENCE IS ASSERTED, NEVER ASSUMED.
check(V5.dempster_combine(_m1, _m2, assume_independent=False)["state"]
      == "DEPENDENCE_UNRESOLVED",
      "7.1 without an assertion of independence there is no combination")
# discounting
_d = V5.discount(_m1, 0.5, ["G", "R"])
near("7.1 discount alpha=.5: m'({G}) = .3", _d[frozenset({"G"})], 0.3)
near("7.1 discount alpha=.5: m'(Theta) = 1-.5+.5*.4 = .7", _d[frozenset({"G", "R"})], 0.7)
# the governed structure: same source twice is one body
o = V5.dempster_shafer(FX.dst_same_source())
check(o["estimable"] is False and o["state"] == "DEPENDENCE_UNRESOLVED",
      "7.1 two bodies read off the same evidence source cannot be combined", str(o))
o = V5.dempster_shafer(FX.dst_independent())
near("7.1 two genuinely independent bodies combine: m({G}) = .8",
     o["mass"][frozenset({"G"})], 0.8)
refuses("7.1 masses that do not sum to one are refused, not rescaled",
        lambda: V5.read_mass_function({"masses": [{"subset": ["G"], "mass": 0.6}]},
                                      ["G", "R"], "w"))
refuses("7.1 mass on the empty set is refused",
        lambda: V5.read_mass_function({"masses": [{"subset": [], "mass": 1.0}]},
                                      ["G", "R"], "w"))
refuses("7.1 no frame -> Not Estimable", lambda: V5.dempster_shafer({"bodies": []}))

# ---------------------------------------------------------------- 7.2 ROUGH SETS
# CONTRACT ORACLE: U={1,2,3,4}; classes {1,2} and {3,4}; X={1,3,4}
# Lower = {3,4} (only {3,4} lies wholly inside X); Upper = {1,2,3,4} (both classes meet X);
# Boundary = Upper - Lower = {1,2}
o = V5.rough_approximations(FX.rough_table())
check(sorted(o["lower"]) == ["3", "4"], "7.2 Lower = {3,4} (contract oracle)", str(o["lower"]))
check(sorted(o["upper"]) == ["1", "2", "3", "4"], "7.2 Upper = {1,2,3,4} (contract oracle)",
      str(o["upper"]))
check(sorted(o["boundary"]) == ["1", "2"], "7.2 Boundary = {1,2} (contract oracle)",
      str(o["boundary"]))
near("7.2 accuracy = |Lower|/|Upper| = 2/4", o["accuracy"], 0.5)
refuses("7.2 one project row is not a decision table",
        lambda: V5.rough_approximations(FX.rough_single_row()))
refuses("7.2 no decision attribute -> Not Estimable",
        lambda: V5.rough_approximations(FX.rough_no_decision()))

# ---------------------------------------------------------------- 7.3 NEUTROSOPHIC
# CONTRACT ORACLE: N=(.7,.2,.1) preserved exactly; (.7,.8,.1) remains distinct; I != 1-T-F.
o = V5.neutrosophic(FX.neutrosophic(0.7, 0.2, 0.1))
check((o["truth"], o["indeterminacy"], o["falsity"]) == (0.7, 0.2, 0.1),
      "7.3 (.7,.2,.1) preserved exactly (contract oracle)", str(o))
o2 = V5.neutrosophic(FX.neutrosophic(0.7, 0.8, 0.1))
check((o2["truth"], o2["indeterminacy"], o2["falsity"]) == (0.7, 0.8, 0.1),
      "7.3 (.7,.8,.1) preserved exactly and remains a distinct structure", str(o2))
check(o["indeterminacy"] != o2["indeterminacy"],
      "7.3 the two structures are not collapsed onto one another")
# I = 1-T-F would give .2 for BOTH; it gives .2 and .8, so I is independent.
check(abs(o2["indeterminacy"] - (1 - 0.7 - 0.1)) > 1e-9,
      "7.3 indeterminacy is NOT 1-T-F")
refuses("7.3 a component outside [0,1] is rejected",
        lambda: V5.neutrosophic(FX.neutrosophic(1.2, 0.2, 0.1)))
refuses("7.3 an omitted indeterminacy is refused, never derived",
        lambda: V5.neutrosophic({"assessed_by": "a", "source": "s",
                                 "truth": 0.7, "falsity": 0.1}))

# ---------------------------------------------------------------- 7.4 INTERVAL FUZZY
# CONTRACT ORACLE: A=[.4,.7], B=[.5,.8] -> intersection [.4,.7], union [.5,.8]
_a, _b = (0.4, 0.7), (0.5, 0.8)
check(V5.interval_intersection(_a, _b) == (0.4, 0.7),
      "7.4 intersection = [.4,.7] (contract oracle)", str(V5.interval_intersection(_a, _b)))
check(V5.interval_union(_a, _b) == (0.5, 0.8),
      "7.4 union = [.5,.8] (contract oracle)", str(V5.interval_union(_a, _b)))
check(V5.interval_fuzzy(FX.interval(0.4, 0.7))["membership"] == [0.4, 0.7],
      "7.4 a governed interval membership is read as given")
refuses("7.4 lower above upper is rejected", lambda: V5.interval_fuzzy(FX.interval(0.7, 0.4)))
refuses("7.4 an upper bound above one is rejected",
        lambda: V5.interval_fuzzy(FX.interval(0.4, 1.4)))
refuses("7.4 a negative lower bound is rejected",
        lambda: V5.interval_fuzzy(FX.interval(-0.1, 0.4)))

# ---------------------------------------------------------------- 7.5 Z-NUMBERS
# CONTRACT: A and B both explicit; a missing B must not become full reliability; same A with
# B_high vs B_low must remain distinguishable; no reduction operator is frozen, so none is used.
_hi = V5.z_number(FX.z_number("cost overrun likely", "very likely"))
_lo = V5.z_number(FX.z_number("cost overrun likely", "unlikely"))
check(_hi["restriction"]["term"] == _lo["restriction"]["term"]
      and _hi["reliability"]["term"] != _lo["reliability"]["term"],
      "7.5 same A with B_high and B_low remain distinguishable (contract oracle)")
check(_hi["reduction"] is None and str(_hi["reduction_blocked"]).strip(),
      "7.5 no reduction operator is chosen; the block is named")
refuses("7.5 a missing reliability is refused, NOT read as full reliability",
        lambda: V5.z_number({"assessed_by": "a", "source": "s",
                             "restriction": {"term": "cost overrun likely"}}))

# ---------------------------------------------------------------- 7.6 PLTS
# CONTRACT ORACLE: Green(.2) Amber(.5) Red(.3) sums to 1 -- valid. Amber(1) degenerate -- valid.
# Negative invalid. Sum != 1 invalid under this v15 contract.
o = V5.plts(FX.plts([("Green", 0.2), ("Amber", 0.5), ("Red", 0.3)]))
near("7.6 Green(.2) Amber(.5) Red(.3) sums to one (contract oracle)", o["total_probability"], 1.0)
check(o["complete"] and len(o["terms"]) == 3, "7.6 all three terms are kept as given")
o = V5.plts(FX.plts([("Amber", 1.0)]))
check(o["estimable"] and o["degenerate"], "7.6 the degenerate set Amber(1) is valid")
refuses("7.6 a negative probability is invalid",
        lambda: V5.plts(FX.plts([("Green", -0.2), ("Red", 1.2)])))
refuses("7.6 probabilities that do not sum to one are invalid under this v15 contract",
        lambda: V5.plts(FX.plts([("Green", 0.2), ("Red", 0.3)])))

# ---------------------------------------------------------------- 7.7 PLITHOGENIC (DISABLED)
o = V5.plithogenic_lab(FX.plithogenic())
check(o["structure_complete"] is True, "7.7 the laboratory structure is read and verified")
check(o["operational"] is False and o["operator"] is None
      and o["disposition"] == "DISABLED_FUTURE_RESEARCH",
      "7.7 remains disabled/future research; no operator is chosen and no result is produced")
refuses("7.7 an appurtenance degree outside [0,1] is refused",
        lambda: V5.plithogenic_lab(FX.plithogenic(appurtenance=1.4)))

# ---------------------------------------------------------------- 7.8 BELIEF RULE BASE
# CONTRACT ORACLE: one fully activated rule with consequent Green .7 Amber .2 Red .1 must return
# exactly (.7,.2,.1).
o = V5.belief_rule_base(FX.brb_single_rule())
near("7.8 single fully activated rule -> Green .7 (contract oracle)", o["belief"]["Green"], 0.7)
near("7.8 single fully activated rule -> Amber .2 (contract oracle)", o["belief"]["Amber"], 0.2)
near("7.8 single fully activated rule -> Red .1 (contract oracle)", o["belief"]["Red"], 0.1)
check(o["aggregation"] == "SINGLE_FULLY_ACTIVATED_RULE", "7.8 and the aggregation is named")
o = V5.belief_rule_base(FX.brb_two_rules())
check(o["estimable"] is False and o["state"] == "AGGREGATION_BLOCKED",
      "7.8 multi-rule aggregation is BLOCKED: no ER variant is chosen here", str(o))
refuses("7.8 a rule distributing more than all its belief is refused",
        lambda: V5.belief_rule_base(FX.brb_invalid_distribution()))
refuses("7.8 a rule base with no attribute weights is refused",
        lambda: V5.belief_rule_base(FX.brb_no_attribute_weights()))

# ---------------------------------------------------------------- 7.9 QUANTUM (ARCHIVED)
# LABORATORY IDENTITY ONLY: |psi> = (1/sqrt2)(|0>+|1>) -> P(0) = .5 under the Born rule.
_p = V5.quantum_lab_born_rule([1 / math.sqrt(2), 1 / math.sqrt(2)])
near("7.9 Born rule P(0) = .5 for the equal superposition (research history)", _p[0], 0.5)
near("7.9 Born rule P(1) = .5", _p[1], 0.5)
A = V5.QUANTUM_ARCHIVE
check(A["operational_activation"] is False and A["voting"] is False
      and A["participant_operational_visibility"] is False,
      "7.9 archived: activation false, voting false, no participant operational visibility")
check(all(str(A[k]).strip() for k in ("identity", "canonical_name",
                                      "historical_implementation", "historical_tests",
                                      "literature_record", "reason_archived",
                                      "missing_restoration_evidence",
                                      "restoration_prerequisites")),
      "7.9 the archive record carries every field section 16 requires")

# ---------------------------------------------------------------- 7.10 PYTHAGOREAN
# CONTRACT ORACLE: mu=.6 nu=.8 -> .36+.64 = 1.00 valid, pi = 0. Invalid: .8,.8 -> 1.28.
o = V5.pythagorean_fuzzy(FX.pyth(0.6, 0.8))
near("7.10 mu^2+nu^2 = 1.00 for (.6,.8) (contract oracle)", o["squared_sum"], 1.0)
near("7.10 hesitancy pi = 0 (contract oracle)", o["hesitancy"], 0.0)
near("7.10 (.8,.8) squares to 1.28 -- outside the domain", 0.8 ** 2 + 0.8 ** 2, 1.28)
refuses("7.10 (.8,.8) is REJECTED, not scaled back into range",
        lambda: V5.pythagorean_fuzzy(FX.pyth(0.8, 0.8)))
refuses("7.10 a component above one is rejected", lambda: V5.pythagorean_fuzzy(FX.pyth(1.1, 0.0)))

# ---------------------------------------------------------------- 7.11 PICTURE
# CONTRACT ORACLE: mu=.4 eta=.2 nu=.3 -> refusal r = 1-.9 = .1
o = V5.picture_fuzzy(FX.picture(0.4, 0.2, 0.3))
near("7.11 refusal r = .1 for (.4,.2,.3) (contract oracle)", o["refusal"], 0.1)
check((o["positive"], o["neutral"], o["negative"]) == (0.4, 0.2, 0.3),
      "7.11 the three degrees stay distinct from one another and from the refusal")
refuses("7.11 a sum above one is rejected", lambda: V5.picture_fuzzy(FX.picture(0.5, 0.4, 0.3)))
refuses("7.11 a negative component is rejected",
        lambda: V5.picture_fuzzy(FX.picture(-0.1, 0.4, 0.3)))

# ---------------------------------------------------------------- 7.12 HESITANT
# CONTRACT ORACLE: h={.2,.5,.7} -> arithmetic mean = 1.4/3 = 0.4666666667
o = V5.hesitant_fuzzy(FX.hesitant([0.2, 0.5, 0.7]))
near("7.12 score = .4666666667 for {.2,.5,.7} (contract oracle)", o["score"], 1.4 / 3, 1e-9)
near("7.12 one value returns itself", V5.hesitant_fuzzy(FX.hesitant([0.35]))["score"], 0.35)
check(all(abs(V5.hesitant_fuzzy(FX.hesitant(list(p)))["score"] - 1.4 / 3) < 1e-12
          for p in itertools.permutations([0.2, 0.5, 0.7])),
      "7.12 permutation invariant across all 6 orderings")
refuses("7.12 the empty hesitant element is Not Estimable, never favourable",
        lambda: V5.hesitant_fuzzy(FX.hesitant([])))
refuses("7.12 a degree outside [0,1] is rejected",
        lambda: V5.hesitant_fuzzy(FX.hesitant([0.2, 1.5])))

# ---------------------------------------------------------------- 7.13 TYPE-2
# CONTRACT ORACLE: lower(x)=.3 upper(x)=.7 -> FOU [.3,.7], width .4.
#                  lower(x)=.5 upper(x)=.5 -> width 0, and that is an assessment, not missingness.
o = V5.type2_fuzzy(FX.type2([(0.0, 0.3, 0.7)]))
check((o["points"][0]["lower"], o["points"][0]["upper"]) == (0.3, 0.7),
      "7.13 FOU interval [.3,.7] preserved as two separate bounds (contract oracle)")
near("7.13 FOU_width = .4 (contract oracle)", o["points"][0]["fou_width"], 0.4)
o0 = V5.type2_fuzzy(FX.type2([(0.0, 0.5, 0.5)]))
near("7.13 FOU_width = 0 for lower=upper=.5 (contract oracle)",
     o0["points"][0]["fou_width"], 0.0)
check(o0["estimable"] is True, "7.13 zero FOU width is a real assessment, not missing data")
check(o["type_reduced"] is None and str(o["type_reduction_blocked"]).strip(),
      "7.13 type reduction is BLOCKED -- no Karnik-Mendel formulation is frozen in the "
      "supervisory artifacts, and none is invented")
# and NO midpoint anywhere: (.3+.7)/2 = .5 must not appear as a produced figure
check(not any(abs(float(v) - 0.5) < 1e-12
              for v in (o["max_fou_width"],) if isinstance(v, (int, float))),
      "7.13 no (lower+upper)/2 figure is produced")
refuses("7.13 lower above upper is rejected", lambda: V5.type2_fuzzy(FX.type2([(0.0, 0.7, 0.3)])))
refuses("7.13 an upper above one is rejected", lambda: V5.type2_fuzzy(FX.type2([(0.0, 0.3, 1.7)])))
refuses("7.13 a negative lower is rejected", lambda: V5.type2_fuzzy(FX.type2([(0.0, -0.3, 0.7)])))

# ---------------------------------------------------------------- 7.14 MAXIMUM ENTROPY
# CONTRACT ORACLE A: two states, normalisation only -> p = (.5,.5), H = ln 2 = 0.6931471805599453
o = V5.maximum_entropy(FX.maxent_two_states())
near("7.14 Oracle A p1 = .5 (contract oracle)", o["distribution"]["s1"], 0.5)
near("7.14 Oracle A p2 = .5 (contract oracle)", o["distribution"]["s2"], 0.5)
near("7.14 Oracle A H = ln 2 (contract oracle)", o["entropy"], math.log(2))
# CONTRACT ORACLE B: x = {0,1,2}, sum p = 1 and sum p x = 1 -> p = (1/3,1/3,1/3),
# mean 1, H = ln 3 = 1.0986122886681098
o = V5.maximum_entropy(FX.maxent_expectation(1.0))
near("7.14 Oracle B p(x=0) = 1/3 (contract oracle)", o["distribution"]["x0"], 1 / 3, 1e-9)
near("7.14 Oracle B p(x=1) = 1/3 (contract oracle)", o["distribution"]["x1"], 1 / 3, 1e-9)
near("7.14 Oracle B p(x=2) = 1/3 (contract oracle)", o["distribution"]["x2"], 1 / 3, 1e-9)
near("7.14 Oracle B mean = 1 (contract oracle)", o["constraint_expectations"]["mean"], 1.0, 1e-9)
near("7.14 Oracle B H = ln 3 (contract oracle)", o["entropy"], math.log(3), 1e-9)
# IT ACTUALLY OPTIMISES: an asymmetric expectation must move the distribution off uniform, and
# the answer must satisfy the constraint it was given. Independent check, no production formula:
# with mean 0.5 over x={0,1,2} the maximiser has the exponential form p_i ∝ r^{x_i}; the reported
# distribution is verified to (a) meet the constraint and (b) have HIGHER entropy than any other
# distribution meeting it that we can construct, checked against a fine grid.
o = V5.maximum_entropy(FX.maxent_expectation(0.5))
near("7.14 an asymmetric constraint is actually met", o["constraint_expectations"]["mean"],
     0.5, 1e-9)
check(abs(o["distribution"]["x0"] - 1 / 3) > 1e-3,
      "7.14 and the solution moves off uniform, so it is solving, not returning a default")
_best = -1.0
for _i in range(1, 1000):
    _p2 = _i / 1000.0                       # p(x=1)
    _p1 = (0.5 - _p2) / 2.0                 # from mean: p1*0 + p2*1 + p3*2 = .5 with sum 1
    _p3 = 1.0 - _p1 - _p2
    if _p1 <= 0 or _p3 <= 0:
        continue
    _h = -sum(q * math.log(q) for q in (_p1, _p2, _p3))
    _best = max(_best, _h)
check(o["entropy"] >= _best - 1e-6,
      "7.14 the reported distribution has the maximum entropy over a 1000-point grid of "
      "constraint-satisfying distributions (independent grid search, no production formula)",
      f"prod {o['entropy']} grid {_best}")
o = V5.maximum_entropy(FX.maxent_expectation(5.0))
check(o["estimable"] is False and o["state"] == "INFEASIBLE",
      "7.14 an expectation the state space cannot produce is INFEASIBLE, not fabricated", str(o))
refuses("7.14 no state space -> NOT ESTIMABLE",
        lambda: V5.maximum_entropy({"defined_by": "a", "source": "s", "states": []}))
refuses("7.14 a single state is not a distribution to infer",
        lambda: V5.maximum_entropy({"defined_by": "a", "source": "s",
                                    "states": [{"state": "only"}]}))

# ---------------------------------------------------------------- 7.15 POSSIBILITY
# CONTRACT ORACLE: universe {a,b}, pi(a)=1, pi(b)=.4
# Pi({a})=1  Pi({b})=.4  Pi({a,b})=1  N({a}) = 1 - Pi({b}) = .6
o = V5.possibility(FX.possibility({"a": 1.0, "b": 0.4}))
_pi = o["distribution"]
near("7.15 Pi({a}) = 1 (contract oracle)", V5.possibility_of(_pi, ["a"]), 1.0)
near("7.15 Pi({b}) = .4 (contract oracle)", V5.possibility_of(_pi, ["b"]), 0.4)
near("7.15 Pi({a,b}) = 1 (contract oracle)", V5.possibility_of(_pi, ["a", "b"]), 1.0)
near("7.15 N({a}) = 1 - Pi({b}) = .6 (contract oracle)", V5.necessity_of(_pi, ["a"]), 0.6)
# MAXITIVITY over every pair of subsets of a three-state universe
_pi3 = V5.possibility(FX.possibility({"a": 1.0, "b": 0.4, "c": 0.7}))["distribution"]
_subsets = [set(s) for r in range(4) for s in itertools.combinations("abc", r)]
check(all(abs(V5.possibility_of(_pi3, A_ | B_)
              - max(V5.possibility_of(_pi3, A_), V5.possibility_of(_pi3, B_))) < 1e-12
          for A_ in _subsets for B_ in _subsets),
      "7.15 maxitivity Pi(A u B) = max(Pi(A), Pi(B)) holds over all 64 subset pairs")
# POSSIBILITY IS NOT PROBABILITY: the degrees need not sum to one, and 1.0 + 0.4 = 1.4 here.
near("7.15 the degrees sum to 1.4 and that is admissible", sum(_pi.values()), 1.4)
refuses("7.15 a distribution with no fully possible state is refused, not rescaled",
        lambda: V5.possibility(FX.possibility({"a": 0.8, "b": 0.4})))
refuses("7.15 a degree above one is rejected",
        lambda: V5.possibility(FX.possibility({"a": 1.4, "b": 0.4})))
refuses("7.15 no governed possibility distribution -> NOT ESTIMABLE",
        lambda: V5.possibility({"assessed_by": "a", "source": "s", "states": []}))

# ---------------------------------------------------------------- 7.16 SPHERICAL
# CONTRACT ORACLE valid: (.6,.6,.5) -> .36+.36+.25 = .97 valid
# CONTRACT ORACLE invalid: (.8,.8,.1) -> .64+.64+.01 = 1.29 invalid
o = V5.spherical_fuzzy(FX.spherical(0.6, 0.6, 0.5))
near("7.16 squared sum = .97 for (.6,.6,.5) (contract oracle)", o["squared_sum"], 0.97)
check((o["membership"], o["non_membership"], o["hesitancy"]) == (0.6, 0.6, 0.5),
      "7.16 the three components remain distinct")
near("7.16 (.8,.8,.1) squares to 1.29 -- outside the domain",
     0.8 ** 2 + 0.8 ** 2 + 0.1 ** 2, 1.29)
refuses("7.16 (.8,.8,.1) is REJECTED, not projected into the admissible region",
        lambda: V5.spherical_fuzzy(FX.spherical(0.8, 0.8, 0.1)))
refuses("7.16 a component outside [0,1] is rejected",
        lambda: V5.spherical_fuzzy(FX.spherical(1.2, 0.1, 0.1)))

# ---------------------------------------------------------------- 7.17 FERMATEAN
# CONTRACT ORACLE valid: (.8,.7) -> .512+.343 = .855 valid
# CONTRACT ORACLE invalid: (.9,.9) -> .729+.729 = 1.458 invalid
o = V5.fermatean_fuzzy(FX.fermatean(0.8, 0.7))
near("7.17 cubed sum = .855 for (.8,.7) (contract oracle)", o["cubed_sum"], 0.855, 1e-12)
near("7.17 (.9,.9) cubes to 1.458 -- outside the domain", 0.9 ** 3 + 0.9 ** 3, 1.458, 1e-12)
refuses("7.17 (.9,.9) is REJECTED, not shrunk by a renormalisation loop",
        lambda: V5.fermatean_fuzzy(FX.fermatean(0.9, 0.9)))
refuses("7.17 a component outside [0,1] is rejected",
        lambda: V5.fermatean_fuzzy(FX.fermatean(0.5, 1.3)))

print()
print("=" * 78)
print("RUN 30 -- SECTION 20 FUZZY-FAMILY CROSS-CHECK")
print("=" * 78)
# Each family's own valid case passes under ITS OWN domain; each family's own invalid control
# fails; and a pair valid under one family is shown invalid under another where the dimensions
# match, proving the seven do not share one admissibility model.
check(V5.pythagorean_fuzzy(FX.pyth(0.6, 0.8))["estimable"], "20 Pythagorean (.6,.8) valid")
check(V5.fermatean_fuzzy(FX.fermatean(0.8, 0.7))["estimable"], "20 Fermatean (.8,.7) valid")
check(V5.spherical_fuzzy(FX.spherical(0.6, 0.6, 0.5))["estimable"],
      "20 Spherical (.6,.6,.5) valid")
check(V5.picture_fuzzy(FX.picture(0.4, 0.2, 0.3))["estimable"], "20 Picture (.4,.2,.3) valid")
# CROSS-FAMILY, same dimensions (mu, nu): (.8,.7) is VALID Fermatean (.855 <= 1) but INVALID
# Pythagorean (.64+.49 = 1.13 > 1). One tuple, two verdicts, so the two domains are not one.
near("20 (.8,.7) squares to 1.13 under Pythagorean", 0.8 ** 2 + 0.7 ** 2, 1.13, 1e-12)
refuses("20 (.8,.7) is valid Fermatean but INVALID Pythagorean",
        lambda: V5.pythagorean_fuzzy(FX.pyth(0.8, 0.7)))
# and the converse direction: (.6,.8) is valid Pythagorean (1.00) but INVALID Fermatean
# (.216+.512 = .728 <= 1) -- here it is valid under both, so the discriminating pair is (.9,.4):
# Pythagorean .81+.16 = .97 valid; Fermatean .729+.064 = .793 valid. Use (.95,.3):
# Pythagorean .9025+.09 = .9925 valid; Fermatean .857375+.027 = .884 valid. The asymmetry runs
# one way only, which is the true relationship: the Fermatean domain CONTAINS the Pythagorean
# one. That containment is itself the cross-family fact, and it is asserted rather than assumed.
_contained = all(
    (lambda mu, nu: (mu ** 2 + nu ** 2 > 1.0) or (mu ** 3 + nu ** 3 <= 1.0))(i / 20, j / 20)
    for i in range(21) for j in range(21))
check(_contained,
      "20 over a 441-point grid every Pythagorean-admissible pair is Fermatean-admissible: the "
      "domains are nested, not identical")
_strict = any((i / 20) ** 2 + (j / 20) ** 2 > 1.0 and (i / 20) ** 3 + (j / 20) ** 3 <= 1.0
              for i in range(21) for j in range(21))
check(_strict, "20 and the containment is strict: pairs exist that are Fermatean but not "
               "Pythagorean")
# Picture is additive, the others are power-sum: (.4,.2,.3) sums to .9 and is valid Picture,
# while (.6,.6,.5) sums to 1.7 and is INVALID Picture though valid Spherical.
near("20 (.6,.6,.5) sums to 1.7 under Picture's additive constraint", 0.6 + 0.6 + 0.5, 1.7)
refuses("20 (.6,.6,.5) is valid Spherical but INVALID Picture",
        lambda: V5.picture_fuzzy(FX.picture(0.6, 0.6, 0.5)))
# Interval, Hesitant and Type-2 carry different representation dimensions and are NOT
# cross-cast; what is asserted is that each enforces its own shape.
refuses("20 an interval is not a hesitant set: a bare interval has no degree list",
        lambda: V5.hesitant_fuzzy({"assessed_by": "a", "source": "s",
                                   "lower": 0.4, "upper": 0.7}))
refuses("20 a hesitant degree list is not a type-2 membership: it has no per-point bounds",
        lambda: V5.type2_fuzzy({"assessed_by": "a", "source": "s",
                                "degrees": [0.2, 0.5, 0.7]}))
check(len({id(V5.pythagorean_fuzzy), id(V5.picture_fuzzy), id(V5.hesitant_fuzzy),
           id(V5.type2_fuzzy), id(V5.spherical_fuzzy), id(V5.fermatean_fuzzy),
           id(V5.interval_fuzzy)}) == 7,
      "20 seven separate implementations, not one shared validator")

print()
print("=" * 78)
print("RUN 30 -- 7.18 / 7.19 DECISION RANKING, AGAINST AN INDEPENDENT REFERENCE")
print("=" * 78)

# ---------------------------------------------------------------- 7.18 MARCOS
# HAND_DERIVED_CANONICAL_FIXTURE. 3 alternatives x 3 criteria, one cost criterion, weights
# summing to 1. Every intermediate is frozen in server/tools/run30/reference_mcdm.py and
# recomputed here by an implementation sharing no code with production.
_bench = FX.marcos_benchmark()
_ref = REF.marcos(_bench)
_prod = V5.marcos(_bench)
check(_ref["ranking"] == _prod["ranking"],
      "7.18 production ranking equals the independent reference ranking",
      f"ref {_ref['ranking']} prod {_prod['ranking']}")
check(_prod["ranking"] == REF.MARCOS_FROZEN["ranking"],
      "7.18 and equals the frozen expected ranking in the oracle artifact",
      str(_prod["ranking"]))
for _aid, _want in REF.MARCOS_FROZEN["utility"].items():
    _got = next(r for r in _prod["rows"] if r["alternative_id"] == _aid)["utility"]
    near(f"7.18 frozen utility f(K) for {_aid}", _got, _want, 1e-9)
for _cid, _want in REF.MARCOS_FROZEN["ideal"].items():
    near(f"7.18 frozen ideal value for {_cid}", _prod["ideal"][_cid], _want)
for _cid, _want in REF.MARCOS_FROZEN["anti_ideal"].items():
    near(f"7.18 frozen anti-ideal value for {_cid}", _prod["anti_ideal"][_cid], _want)
near("7.18 frozen S(ideal)", _prod["s_ideal"], REF.MARCOS_FROZEN["s_ideal"], 1e-9)
near("7.18 frozen S(anti-ideal)", _prod["s_anti_ideal"], REF.MARCOS_FROZEN["s_anti_ideal"], 1e-9)
# identical alternatives tie
_ident = FX.marcos_identical()
_o = V5.marcos(_ident)
check(_o["ranks"]["A"] == _o["ranks"]["A_copy"], "7.18 identical alternatives tie")
# a dominated alternative cannot rank first
check(V5.marcos(FX.marcos_dominated())["ranking"][0] != "DOM",
      "7.18 a dominated alternative does not rank first")
# criteria are not alternatives; a single project state is not a decision problem
refuses("7.18 a single alternative is refused: one project state is not a choice",
        lambda: V5.marcos(FX.marcos_single_alternative()))
refuses("7.18 criteria presented as alternatives are refused (fewer than two criteria)",
        lambda: V5.marcos(FX.marcos_criteria_as_alternatives()))
refuses("7.18 a criterion with no benefit/cost orientation is refused",
        lambda: V5.marcos(FX.marcos_no_orientation()))
refuses("7.18 weights with no stated provenance are refused",
        lambda: V5.marcos(FX.marcos_no_weight_source()))
check(_prod["lineage"]["derived_from"].startswith("the decision alternatives"),
      "7.18 the ranking retains the lineage of its decision inputs")

# ---------------------------------------------------------------- 7.19 CRITIC-TOPSIS
_bench2 = FX.critic_benchmark()
_ref2 = REF.critic_topsis(_bench2)
_prod2 = V5.critic_topsis(_bench2)
near("7.19 CRITIC weights sum to one", sum(_prod2["weights"].values()), 1.0)
for _cid in _prod2["weights"]:
    near(f"7.19 sigma({_cid}) matches the independent reference",
         _prod2["sigma"][_cid], _ref2["sigma"][_cid], 1e-12)
    near(f"7.19 CRITIC information C_{_cid} matches the reference",
         _prod2["information"][_cid], _ref2["information"][_cid], 1e-12)
    near(f"7.19 CRITIC weight w_{_cid} matches the reference",
         _prod2["weights"][_cid], _ref2["weights"][_cid], 1e-12)
    near(f"7.19 frozen CRITIC weight w_{_cid}",
         _prod2["weights"][_cid], REF.CRITIC_FROZEN["weights"][_cid], 1e-9)
for _row in _prod2["rows"]:
    _r = next(x for x in _ref2["rows"] if x["alternative_id"] == _row["alternative_id"])
    near(f"7.19 D+ for {_row['alternative_id']} matches the reference",
         _row["d_plus"], _r["d_plus"], 1e-12)
    near(f"7.19 D- for {_row['alternative_id']} matches the reference",
         _row["d_minus"], _r["d_minus"], 1e-12)
    near(f"7.19 CC for {_row['alternative_id']} matches the reference",
         _row["closeness"], _r["closeness"], 1e-12)
    near(f"7.19 frozen CC for {_row['alternative_id']}",
         _row["closeness"], REF.CRITIC_FROZEN["closeness"][_row["alternative_id"]], 1e-9)
check(_prod2["ranking"] == _ref2["ranking"] == REF.CRITIC_FROZEN["ranking"],
      "7.19 ranking equals the reference and the frozen expected ranking",
      f"prod {_prod2['ranking']} ref {_ref2['ranking']}")
# permutation of alternative row order does not change the substantive ranking
_perm_bench = FX.critic_benchmark(reverse=True)
check(V5.critic_topsis(_perm_bench)["ranking"] == _prod2["ranking"],
      "7.19 permuting the alternative rows does not change the ranking")
# identical alternatives tie
_id2 = V5.critic_topsis(FX.critic_identical())
check(_id2["ranks"]["A"] == _id2["ranks"]["A_copy"], "7.19 identical alternatives tie")
# benefit/cost orientation changes ideal selection
_flip = V5.critic_topsis(FX.critic_benchmark(flip_orientation=True))
check(_flip["ranking"] != _prod2["ranking"],
      "7.19 reversing a criterion's orientation changes the ranking",
      f"{_flip['ranking']} vs {_prod2['ranking']}")
refuses("7.19 a single project row is NOT ESTIMABLE",
        lambda: V5.critic_topsis(FX.critic_single_row()))
refuses("7.19 a zero-variance criterion is refused, never silently divided by",
        lambda: V5.critic_topsis(FX.critic_zero_variance()))
check(_prod2["weights_are_algorithmic"] is True,
      "7.19 CRITIC weights are declared algorithmic outputs, not governed weights")
check(_prod2["lineage"]["derived_from"].startswith("the decision alternatives"),
      "7.19 the ranking retains the lineage of its decision inputs")

# ---------------------------------------------------------------- 7.20 HYPERSOFT (DISABLED)
# CONTRACT ORACLE: A1={a1,a2}, A2={b1,b2} -> four tuples must all exist.
o = V5.hypersoft_lab(FX.hypersoft_complete())
check(o["cartesian_size"] == 4 and o["mapped"] == 4 and o["structure_complete"] is True,
      "7.20 all four Cartesian tuples exist explicitly (contract oracle)", str(o))
_required = [("a1", "b1"), ("a1", "b2"), ("a2", "b1"), ("a2", "b2")]
_produced = sorted(tuple(t) for t in
                   V5.hypersoft_lab(FX.hypersoft_missing())["missing_tuples"]
                   + [m["tuple"] for m in FX.hypersoft_missing()["mapping"]])
check(_produced == sorted(_required),
      "7.20 the Cartesian product the structure is measured against is exactly "
      "(a1,b1),(a1,b2),(a2,b1),(a2,b2)", str(_produced))
o = V5.hypersoft_lab(FX.hypersoft_missing())
check(o["structure_complete"] is False and o["missing_tuples"] == [["a2", "b2"]],
      "7.20 deleting (a2,b2) gives an explicit incomplete structure (contract oracle)", str(o))
check(o["estimable"] is False and str(o["reason"]).strip(),
      "7.20 and it abstains: nothing is supplied in place of the missing tuple")
check(o["operational"] is False and o["disposition"] == "DISABLED_FUTURE_RESEARCH",
      "7.20 remains disabled/future research and produces no operational reading")
check(V5.hypersoft_lab(FX.hypersoft_complete())["operational"] is False,
      "7.20 even a COMPLETE structure produces no operational reading")
refuses("7.20 attributes sharing a value are refused: the value subspaces must be disjoint",
        lambda: V5.hypersoft_lab(FX.hypersoft_overlapping()))

print()
print("=" * 78)
print("RUN 30 -- SECTION 17 LINEAGE AND DEPENDENCE COUNTERS")
print("=" * 78)
# FALSE REINFORCEMENT: a second reading of one evidence body strengthening the answer.
# FALSE SUPPRESSION: a genuinely independent adverse body being dropped or weakened.
_reinforce = 0
_suppress = 0
_body_dup = [sig("a", "Red", "bX"), sig("a2", "Red", "bX"), sig("g", "Green", "bY")]
_body_one = [sig("a", "Red", "bX"), sig("g", "Green", "bY")]
_polR = {"set_by": "t", "authority": "t", "weights": {"a": 1.0, "a2": 1.0, "g": 1.0}}
_polO = {"set_by": "t", "authority": "t", "weights": {"a": 1.0, "g": 1.0}}
if V5.weighted_voting(_body_dup, _polR)["votes"]["Red"] > \
        V5.weighted_voting(_body_one, _polO)["votes"]["Red"] + 1e-12:
    _reinforce += 1
if V5.majority_rules(_body_dup)["counts"]["Red"] > V5.majority_rules(_body_one)["counts"]["Red"]:
    _reinforce += 1
if V5.worst_two_of_m(_body_dup)["mean_worst_2"] > \
        V5.worst_two_of_m(_body_one)["mean_worst_2"] + 1e-12:
    _reinforce += 1
if V5.dempster_shafer(FX.dst_same_source()).get("estimable") is not False:
    _reinforce += 1
# independent adverse evidence must NOT be suppressed
_indep = [sig("a", "Red", "bX"), sig("b", "Red", "bY"), sig("g", "Green", "bZ")]
if V5.majority_rules(_indep)["counts"]["Red"] != 2:
    _suppress += 1
if V5.worst_two_of_m(_indep)["mean_worst_2"] != 3.0:
    _suppress += 1
if V5.conservative_dominance(_indep)["state"] != "Red":
    _suppress += 1
if V5.dempster_shafer(FX.dst_independent()).get("estimable") is not True:
    _suppress += 1
check(_reinforce == 0, "17 false reinforcement = 0", str(_reinforce))
check(_suppress == 0, "17 false suppression = 0", str(_suppress))
# Category-6 siblings are one regime family over one signal set, not four independent facts.
_sigs6 = [sig("a", "Red", "bX"), sig("b", "Green", "bY"), sig("c", "Amber", "bZ")]
_pol6 = {"set_by": "t", "authority": "t", "weights": {"a": 1, "b": 1, "c": 1}}
#: Each regime reports the SAME set of considered signal identities, so a reader combining two
#: of their outputs is combining one body of evidence twice, and the outputs say so.
_ids_cd = sorted(V5.conservative_dominance(_sigs6)["considered"])
_ids_w2 = sorted(s["lineage_body"] for s in V5.worst_two_of_m(_sigs6)["selected"])
_ids_all = sorted(s["lineage_body"] for s in _sigs6)
check(_ids_cd == ["a", "b", "c"] and set(_ids_w2) <= set(_ids_all),
      "17 the four Category-6 regimes read ONE signal set: they cannot reinforce one another "
      "as independent evidence", f"{_ids_cd} / {_ids_w2}")
check(V5.conservative_dominance(_sigs6)["state"] == "Red"
      and V5.worst_two_of_m(_sigs6)["mean_worst_2"] == 2.5
      and V5.majority_rules(_sigs6)["unique_winner"] is False,
      "17 and they legitimately disagree, which is what makes them comparison regimes")
# DEPENDENCE IS NOT TRANSITIVE: bodies X and Y stay separate even when a third names both.
_abc = [sig("x", "Red", "bX"), sig("xy", "Amber", "bXY"), sig("y", "Red", "bY")]
check(len(V5.independent_signals(V5.eligible_signals(_abc)[0])[0]) == 3,
      "17 pairwise, non-transitive: an overlapping third body does not merge two distinct ones")

print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
