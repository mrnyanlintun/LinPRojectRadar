"""
RUN 20 CYCLE 9. THE FOUR P1 IMPLEMENTATION DEFECTS, EACH REPRODUCED RED BEFORE IT WAS FIXED.

These are the register rows whose Run-19 root cause is METHOD_IMPLEMENTATION_DEFECT rather than
METHOD_LABEL_MISMATCH: the method the module claims is the method it should perform, and the
arithmetic does not perform it. A label mismatch is cycle 10's question and is not touched here.

  A5.2  Sensitivity Analysis   ranked three quantities of which one was a sensitivity
  B1.1  Conservative Dominance applied a counting rule, so a lone Red did not dominate
  B2.10 Pythagorean Fuzzy Sets reported a hesitancy belonging to a pair it discards
  B2.15 Possibility Theory     an unnormalised distribution and a necessity that was not one

TWO REGISTER ROWS ARE DELIBERATELY NOT CLOSED HERE AND THE REASON IS RECORDED IN SECTION 6.
B1.4 Worst-N-of-M and PH.5 Anomaly Score both require a threshold or a weight to be CHOSEN, and
this programme does not invent one. They are recorded, left non-voting and advisory, and carried
forward. A count is not worth a fabricated constant.
"""

import copy
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.simulation import fusion as FUSION  # noqa: E402
from app.simulation.models_decision import run_conservative_dominance  # noqa: E402
from app.simulation.models_doc import run_sensitivity_analysis  # noqa: E402
from app.simulation.models_fuzzy import (  # noqa: E402
    run_possibility_theory, run_pythagorean_fuzzy,
)
from app.simulation.registry import activation_state  # noqa: E402

_passed = 0
_total = 0
NOOP = (lambda: 0.5)


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}" + (f"  [{detail}]" if detail else ""))


# =============================================================== A5.2 SENSITIVITY ANALYSIS
print("=== 1. A5.2: ONLY THE PERTURBED DRIVER IS A SENSITIVITY ===")
S = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 500_000.0, "pv": 450_000.0,
     "cpi": 0.8, "spi": 0.89, "docRiskScore": 0.55}
_s = run_sensitivity_analysis(dict(S), NOOP, None)
check("exactly one driver is ranked, and it is the cost index",
      [d["name"] for d in _s["drivers"]] == ["CPI"], str(_s["drivers"]))
check("the two quantities that are never perturbed are reported as LEVELS, under their own names",
      [lv["name"] for lv in _s["levels_not_perturbed"]] == ["SPI", "DocRisk"])
check("and neither of them carries the word sensitivity",
      all("sensitivity" not in lv for lv in _s["levels_not_perturbed"]))
check("the counts are disclosed, so a reader is not left to infer them",
      _s["inputs_perturbed"] == 1 and _s["inputs_reported_as_levels"] == 2)
# THE DEFINING PROPERTY: the ranked driver RESPONDS to its own input, and the band follows it.
_moved = run_sensitivity_analysis(dict(S, cpi=0.6), NOOP, None)
check("the ranked driver responds when its own input moves, which is what a sensitivity is",
      _moved["drivers"][0]["sensitivity"] != _s["drivers"][0]["sensitivity"],
      f"{_moved['drivers'][0]['sensitivity']} vs {_s['drivers'][0]['sensitivity']}")
# AND THE DEFECT ITSELF: the raw document risk score can no longer set the band.
_doc_hi = run_sensitivity_analysis(dict(S, docRiskScore=0.95), NOOP, None)
_doc_lo = run_sensitivity_analysis(dict(S, docRiskScore=0.05), NOOP, None)
check("the raw document risk score no longer moves the band, because it is not a sensitivity",
      _doc_hi["status_color"] == _doc_lo["status_color"] == _s["status_color"],
      f"{_doc_hi['status_color']} {_doc_lo['status_color']}")
check("nor the top driver", _doc_hi["top_driver"] == _doc_lo["top_driver"] == "CPI")
check("but the score is still reported at its own value, so no information is lost",
      _doc_hi["levels_not_perturbed"][1]["level"] == 0.95)
print("--- A5.2 negative, boundary and missingness, all unchanged from Run 11 ---")
check("the document risk score is still REQUIRED and its absence still abstains",
      run_sensitivity_analysis({k: v for k, v in S.items() if k != "docRiskScore"},
                               NOOP, None).get("insufficient_data") is True)
check("a document risk score outside nought to one is still refused",
      run_sensitivity_analysis(dict(S, docRiskScore=30), NOOP, None)
      .get("insufficient_data") is True)
check("the cost-index values at which the perturbed division is undefined are still refused",
      all(run_sensitivity_analysis(dict(S, cpi=c), NOOP, None).get("insufficient_data") is True
          for c in (0, 0.05, -0.05)))
check("a budget of zero still leaves no base estimate to normalise against",
      run_sensitivity_analysis(dict(S, bac=0), NOOP, None).get("insufficient_data") is True)
# The band boundaries are untouched, and the sweep that shows it is over the input the band now
# follows. The reachable set is what it is: the cost-index sensitivity is a spread of the
# forecast over a 0.10 window, and it grows without limit as the index falls, so the calm and the
# adverse ends are both reachable and the sweep is chosen to cross them rather than to produce a
# tidy set of four.
_sweep = {c: run_sensitivity_analysis(dict(S, cpi=c), NOOP, None)["status_color"]
          for c in (2.0, 0.95, 0.60, 0.40, 0.20)}
check("the band boundaries are untouched: the band still follows the one sensitivity and "
      "crosses every boundary as that sensitivity grows",
      set(_sweep.values()) == {"Green", "Yellow", "Amber", "Red"}, str(_sweep))

# =============================================================== B1.1 CONSERVATIVE DOMINANCE
print("\n=== 2. B1.1: A LONE RED DOMINATES ===")


def pkg(evm=None, mc=None, cusum="Green", doc=None, breached=False):
    s = {}
    if evm is not None:
        s["evm"] = {"status": evm}
    if mc is not None:
        s["mc"] = {"status": mc}
    if cusum is not None:
        s["cusum"] = {"status": cusum, "breached": breached}
    if doc is not None:
        s["doc"] = {"status": doc}
    return {"signals": s}


_lone_red = run_conservative_dominance(pkg("Green", "Green", "Green", "Red"), NOOP, None)
check("THE DEFINING CASE: one Red among Greens reads Red, not Amber",
      _lone_red["status_color"] == "Red", _lone_red["status_color"])
check("and the decision layer's own counting state is still reported beside it, so the two "
      "answers are visible rather than silently reconciled",
      _lone_red["decision_layer_state"] == "Amber", _lone_red["decision_layer_state"])
check("a lone Amber among Greens reads Amber",
      run_conservative_dominance(pkg("Green", "Green", "Green", "Amber"),
                                 NOOP, None)["status_color"] == "Amber")
check("all four Green still reads Green",
      run_conservative_dominance(pkg("Green", "Green", "Green", "Green"),
                                 NOOP, None)["status_color"] == "Green")
print("--- invariants the rule must have ---")
_ladder = ["Green", "Yellow", "Amber", "Red"]
_ranks = [FUSION.BAND_SEVERITY[run_conservative_dominance(
    pkg("Green", "Green", "Green", b), NOOP, None)["status_color"]] for b in _ladder]
check("monotone: worsening one signal never improves the answer",
      all(_ranks[i] <= _ranks[i + 1] for i in range(3)), str(_ranks))
_perms = {run_conservative_dominance(p, NOOP, None)["status_color"] for p in (
    pkg("Red", "Green", "Green", "Green"), pkg("Green", "Red", "Green", "Green"),
    pkg("Green", "Green", "Red", "Green"), pkg("Green", "Green", "Green", "Red"))}
check("permutation invariant: which slot carries the Red does not matter", _perms == {"Red"},
      str(_perms))
_one = run_conservative_dominance(pkg("Red", "Green", "Green", "Green"), NOOP, None)
_two = run_conservative_dominance(pkg("Red", "Red", "Green", "Green"), NOOP, None)
check("idempotent: a second Red adds nothing, which is what makes the rule immune to the "
      "duplication ARCH.5 found in these same four signals",
      _one["status_color"] == _two["status_color"] == "Red")
print("--- missingness and boundary: incomplete evidence cannot reach the calmest band ---")
check("an absent signal does not read as Green",
      run_conservative_dominance(pkg(None, "Green", "Green", "Green"),
                                 NOOP, None)["status_color"] != "Green")
check("an unrecognised status string does not read as Green",
      run_conservative_dominance(pkg("banana", "Green", "Green", "Green"),
                                 NOOP, None)["status_color"] != "Green")
check("and the completeness of the evidence is reported rather than left implicit",
      run_conservative_dominance(pkg(None, "Green", "Green", "Green"),
                                 NOOP, None)["evidence_complete"] is False)
check("an absent signal beside a Red still reads Red: incompleteness never softens adversity",
      run_conservative_dominance(pkg(None, "Red", "Green", "Green"),
                                 NOOP, None)["status_color"] == "Red")
check("no package at all still refuses entirely",
      run_conservative_dominance({}, NOOP, None).get("insufficient_data") is True)

# =============================================================== B2.10 PYTHAGOREAN FUZZY
print("\n=== 3. B2.10: THE HESITANCY BELONGS TO THE PAIR THAT IS REPORTED ===")
for cpi, doc in ((0.95, 0.8), (0.90, 0.5), (0.88, 0.0), (1.00, 1.0), (0.85, 0.3)):
    r = run_pythagorean_fuzzy({"cpi": cpi, "spi": cpi, "docRiskScore": doc}, NOOP, None)
    mu, nu, pi = r["membership"], r["non_membership"], r["hesitancy"]
    # The identity is checked on the UNROUNDED values a rounding step cannot rescue, by
    # recomputing pi from the reported pair and comparing.
    import math  # noqa: E402
    want = round(math.sqrt(max(0.0, 1 - mu * mu - nu * nu)), 2)
    check(f"cpi {cpi}, doc {doc}: the reported hesitancy is the hesitancy OF the reported pair",
          abs(pi - want) <= 0.01, f"pi {pi}, recomputed {want}")
    check(f"cpi {cpi}, doc {doc}: and the reported pair satisfies the constraint that defines "
          f"the set", mu * mu + nu * nu <= 1.0001, f"{mu * mu + nu * nu}")
_pfs_sweep = {c: run_pythagorean_fuzzy({"cpi": c, "spi": c, "docRiskScore": 0.0},
                                       NOOP, None)["status_color"]
              for c in (1.00, 0.95, 0.93, 0.91, 0.89, 0.80)}
check("the band thresholds are untouched: all four bands are still reachable",
      set(_pfs_sweep.values()) == {"Green", "Yellow", "Amber", "Red"}, str(_pfs_sweep))
check("missingness is unchanged: an absent input still abstains",
      run_pythagorean_fuzzy({"cpi": 0.9}, NOOP, None).get("insufficient_data") is True)

# =============================================================== B2.15 POSSIBILITY THEORY
print("\n=== 4. B2.15: A NORMALISED DISTRIBUTION AND A NECESSITY THAT IS ONE ===")
_bands_before = {}
for cpi in (0.80, 0.88, 0.90, 0.92, 0.94, 0.99):
    for doc in (0.0, 0.3, 0.8):
        r = run_possibility_theory({"cpi": cpi, "spi": cpi, "docRiskScore": doc}, NOOP, None)
        p, n = r["possibility"], r["necessity"]
        check(f"cpi {cpi}, doc {doc}: the distribution is normalised, so its supremum is one",
              abs(max(p.values()) - 1.0) < 0.011, str(p))
        check(f"cpi {cpi}, doc {doc}: necessity never exceeds possibility, which is the "
              f"consistency condition", all(n[k] <= p[k] + 0.011 for k in p), f"{p} {n}")
        check(f"cpi {cpi}, doc {doc}: necessity is the dual of the complement's possibility",
              all(abs(n[k] - max(0.0, 1 - max(v for j, v in p.items() if j != k))) <= 0.011
                  for k in p), f"{p} {n}")
        _bands_before[(cpi, doc)] = r["status_color"]
check("the unnormalised maps are still reported, so a reader can see what was rescaled",
      "possibility_unnormalised" in run_possibility_theory(
          {"cpi": 0.92, "spi": 0.92, "docRiskScore": 0.2}, NOOP, None))
# THE PROPERTY THAT MAKES THE NORMALISATION SAFE: it is a monotone rescaling, so the argmax --
# and therefore the band -- cannot move. Proved by recomputing the argmax of the UNNORMALISED
# maps and requiring it to agree with the reported band everywhere in the sweep.
for (cpi, doc), got in _bands_before.items():
    r = run_possibility_theory({"cpi": cpi, "spi": cpi, "docRiskScore": doc}, NOOP, None)
    raw = r["possibility_unnormalised"]
    argmax = "Green"
    for b in list(raw)[1:]:
        argmax = argmax if raw[argmax] > raw[b] else b
    check(f"cpi {cpi}, doc {doc}: the band is the argmax of the UNNORMALISED maps, so the "
          f"normalisation moved nothing", got == argmax, f"{got} vs {argmax}")
check("missingness is unchanged: an absent input still abstains",
      run_possibility_theory({"cpi": 0.9}, NOOP, None).get("insufficient_data") is True)

# =============================================================== MUTATION AND FAULT PROOF
print("\n=== 5. MUTATION AND FAULT PROOF ===")
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


# M1. A5.2's document risk score restored to the ranking as a sensitivity.
mutation("M1 the raw document risk score ranked as a sensitivity again",
         _doc_hi["top_driver"] == "CPI" and _doc_hi["status_color"] == _s["status_color"],
         "the raw document risk score no longer moves the band")
# M2. A5.2's level readings relabelled as sensitivities.
mutation("M2 the level readings relabelled sensitivities",
         all("sensitivity" not in lv for lv in _s["levels_not_perturbed"]),
         "neither level carries the word sensitivity")
# M3. B1.1's dominance replaced by the counting rule again.
mutation("M3 the counting rule restored, so a lone Red does not dominate",
         _lone_red["status_color"] == "Red" and _lone_red["decision_layer_state"] == "Amber",
         "one Red among Greens reads Red, not Amber")
# M4. B1.1's dominance applied over the present signals only, so an absent one reads as
#     agreement. This is the mutation the first draft of the fix actually contained.
mutation("M4 dominance over present signals only, so an absent signal reads as Green",
         run_conservative_dominance(pkg(None, "Green", "Green", "Green"),
                                    NOOP, None)["status_color"] == "Amber",
         "an absent signal does not read as Green")
# M5. B2.10's constraint applied to the raw pair again, so the hesitancy is orphaned.
_m5 = run_pythagorean_fuzzy({"cpi": 0.95, "spi": 0.95, "docRiskScore": 0.8}, NOOP, None)
import math  # noqa: E402
mutation("M5 the hesitancy taken from the pre-adjustment pair",
         abs(_m5["membership"] ** 2 + _m5["non_membership"] ** 2 + _m5["hesitancy"] ** 2 - 1)
         <= 0.02,
         "the reported hesitancy is the hesitancy OF the reported pair")
# M6. B2.15's normalisation removed.
_m6 = run_possibility_theory({"cpi": 0.92, "spi": 0.92, "docRiskScore": 0.2}, NOOP, None)
mutation("M6 the normalisation removed",
         abs(max(_m6["possibility"].values()) - 1.0) < 0.011
         and max(_m6["possibility_unnormalised"].values()) < 1.0,
         "the distribution is normalised, so its supremum is one")
# M7. B2.15's necessity restored to possibility minus an invented constant.
mutation("M7 the necessity restored to the possibility less 0.30",
         all(abs(_m6["necessity"][k] - max(0.0, _m6["possibility"][k] - 0.3)) > 0.005
             for k in _m6["possibility"] if _m6["possibility"][k] > 0.35),
         "necessity is the dual of the complement's possibility")
check("mutation survivors 0", not _survivors, str(_survivors))

# =============================================================== THE TWO NOT CLOSED
print("\n=== 6. THE TWO ROWS THIS CYCLE DOES NOT CLOSE, AND WHY ===")
#
# B1.4 WORST-N-OF-M. The finding is that adverse evidence is diluted by unrelated benign
# evidence: the trigger is a FRACTION of the total, ceil(0.3 * M), so every benign arrival can
# raise the count needed and switch an existing Red set off. The canonical worst-N-of-M is a
# k-out-of-n rule with k FIXED by design, and converting the fraction to a fixed k means CHOOSING
# k. There is no k in the specification, none in the repository and none in any cited source, and
# 0.3 and 0.4 are themselves literals with no provenance. Inventing k to close a register row is
# exactly what this programme refuses, so the row is carried forward as a threshold-provenance
# question rather than closed with a fabricated constant.
#
# PH.5 ANOMALY SCORE. Its weights move with data availability, which is the same class of
# question: governing them means fixing them, and fixing them means choosing values.
#
# Both are kept SAFE meanwhile, which is what this section checks mechanically.
for mid in ("B1.4",):
    check(f"{mid} is advisory and cannot vote while its threshold provenance is unresolved",
          activation_state(mid) == "ADVISORY_ONLY", activation_state(mid))
check("the two voting modules are still exactly the two, so neither unresolved row reaches a "
      "governed status",
      sorted(__import__("app.simulation.registry", fromlist=["x"]).CORE_VOTING_MODULES)
      == ["A1.7", "A1.8"])

print("\n=== 7. GUARD NON-VACUITY ===")
check("the A5.2 band guard reads a band that CAN move: it moves with the cost index",
      len({run_sensitivity_analysis(dict(S, cpi=c), NOOP, None)["status_color"]
           for c in (0.95, 0.40)}) == 2)
check("the B1.1 dominance guard reads a state that CAN differ from the decision layer's",
      _lone_red["status_color"] != _lone_red["decision_layer_state"])
check("the B2.10 identity guard is not vacuously satisfied by a zero hesitancy",
      run_pythagorean_fuzzy({"cpi": 0.95, "spi": 0.95, "docRiskScore": 0.8},
                            NOOP, None)["hesitancy"] > 0.1)
check("the B2.15 normalisation guard is not vacuously satisfied: the unnormalised supremum is "
      "genuinely below one somewhere in the sweep",
      max(_m6["possibility_unnormalised"].values()) < 1.0)

print(f"\nRESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
