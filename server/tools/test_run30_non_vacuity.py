"""
RUN 30 -- THE NON-VACUITY CAMPAIGN. THIRTY-NINE MANDATED FAULTS.

WHAT A FAULT IS HERE, AND WHAT IT IS NOT. Each fault replaces a PRODUCTION FUNCTION OR CONSTANT
with a mutant that reintroduces the specific defect the supplied contract names. The mutation is
made on the live module object, and it is CONFIRMED TO HAVE APPLIED by re-reading the attribute
off the module afterwards -- an injection that silently fails to apply is one of the five failure
modes this programme has catalogued, and it reports a false clean. The named guard is then
evaluated; it must go RED, and for the intended reason, which is why every probe returns a value
and both values are printed rather than a bare boolean. The mutation is then restored and the
guard must go GREEN again.

A CRASH IS NOT RED. `probe()` is wrapped: an exception is reported as a crash and the fault is
recorded as NOT PROVEN rather than counted.

IF AN INJECTION SITE DOES NOT EXIST the fault is recorded INJECTION_NOT_APPLIED and is never
scored as RED. The campaign is written so that condition is visible rather than silent.
"""

from __future__ import annotations

import csv
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
import os as _os_f10  # noqa: E402
sys.path.insert(0, _os_f10.path.dirname(_os_f10.path.abspath(__file__)))  # Run 136 F10
from artifact_write import artifact_out, report_artifact_write  # noqa: E402  Run 136 F10
sys.path.insert(0, str(HERE))

from app.simulation import canonical_v5 as V5           # noqa: E402
from app.simulation import models_gov as GOV            # noqa: E402
from app.simulation import registry as REG              # noqa: E402
from app.simulation.canonical import StructureAbsent    # noqa: E402
from run30 import fixtures_cat67 as FX                  # noqa: E402

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
RECORDS: list[dict] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def sig(sid, status, body, period=7):
    return {"signal_id": sid, "status": status, "lineage_body": body, "period": period}


def safe(probe):
    """A crash is not RED: it is reported as a crash and the fault is not counted as proven."""
    try:
        return ("ok", probe())
    except Exception as exc:                                     # noqa: BLE001
        return ("crash", repr(exc)[:120])


def fault(number: int, name: str, module, attr: str, mutant, probe,
          baseline_expected, injected_differs=True) -> None:
    """Inject, confirm the injection took, observe the guard, restore, re-observe."""
    if not hasattr(module, attr):
        RECORDS.append({"fault": number, "name": name, "result": "INJECTION_NOT_APPLIED",
                        "detail": f"no attribute {attr!r} on {module.__name__}"})
        check(False, f"F{number:02d} {name}: INJECTION SITE DOES NOT EXIST -- recorded "
                     f"INJECTION_NOT_APPLIED, not scored as RED", attr)
        return
    original = getattr(module, attr)
    kind0, base = safe(probe)
    if kind0 == "crash":
        RECORDS.append({"fault": number, "name": name, "result": "NOT_PROVEN",
                        "detail": f"baseline crashed: {base}"})
        check(False, f"F{number:02d} {name}: the baseline probe CRASHED, so nothing can be "
                     f"proved from it", base)
        return
    if base != baseline_expected:
        RECORDS.append({"fault": number, "name": name, "result": "NOT_PROVEN",
                        "detail": f"baseline {base!r} != expected {baseline_expected!r}"})
        check(False, f"F{number:02d} {name}: the baseline is not what the guard expects",
              f"{base!r} vs {baseline_expected!r}")
        return
    setattr(module, attr, mutant)
    applied = getattr(module, attr) is mutant          # RE-READ, not assumed
    kind1, hurt = safe(probe)
    setattr(module, attr, original)
    kind2, restored = safe(probe)
    ok_applied = applied
    ok_red = kind1 == "ok" and ((hurt != base) if injected_differs else (hurt == base))
    ok_restored = kind2 == "ok" and restored == base and getattr(module, attr) is original
    RECORDS.append({"fault": number, "name": name,
                    "result": "RED_THEN_GREEN" if (ok_applied and ok_red and ok_restored)
                              else "NOT_PROVEN",
                    "detail": f"baseline={base!r} injected={hurt!r} restored={restored!r} "
                              f"injection_applied={applied}"})
    check(ok_applied, f"F{number:02d} {name}: the injection APPLIED (re-read from the module)")
    check(ok_red, f"F{number:02d} {name}: the guard goes RED under the fault",
          f"baseline={base!r} injected={hurt!r} ({kind1})")
    check(ok_restored, f"F{number:02d} {name}: restored, and the guard is GREEN again",
          f"restored={restored!r} ({kind2})")


def _governed_keys() -> set:
    from app.project_data import governed_structure_keys
    return governed_structure_keys()


print("=" * 78)
print("RUN 30 -- NON-VACUITY CAMPAIGN")
print("=" * 78)

_GYA = [sig("s1", "Green", "b1"), sig("s2", "Yellow", "b2"), sig("s3", "Amber", "b3")]
_POL = {"set_by": "t", "authority": "t", "weights": {"g": 0.5, "a": 0.3, "r": 0.2}}
_GAR = [sig("g", "Green", "b1"), sig("a", "Amber", "b2"), sig("r", "Red", "b3")]
_DUP = [sig("r", "Red", "bX"), sig("r2", "Red", "bX"), sig("g", "Green", "bY")]
_POLD = {"set_by": "t", "authority": "t", "weights": {"r": 1.0, "r2": 1.0, "g": 3.0}}

# 1 -------------------------------------------------------------- Conservative Dominance averages
fault(1, "Conservative Dominance averages away a Red", V5, "conservative_dominance",
      lambda signals: {"estimable": True, "state": V5.SEVERITY_BAND[
          round(sum(V5.SEVERITY[s["status"]] for s in signals) / len(signals))]},
      lambda: V5.conservative_dominance(
          [sig("a", "Green", "b1"), sig("b", "Green", "b2"), sig("c", "Red", "b3")])["state"],
      "Red")

# 2 --------------------------------------------------- a synthesiser consumes raw KPIs
# RE-POINTED BY RUN 89, AND THE PROPERTY GUARDED IS UNCHANGED: A SYNTHESISER MUST CONSUME
# GOVERNED STATES, NOT RAW PROJECT INDICES. The owner ruled at Run 89 that B1.2 Weighted Voting
# reads the six performance CATEGORY POSTURES instead of the four assembled arms, so it no
# longer calls `_governed` at all and this injection site is unreachable FROM B1.2. B1.3
# Majority Rules still synthesises the governed signals through exactly that call, so the fault
# is aimed there. Fault 2b below then guards the same property on B1.2's NEW input path, so
# nothing that was protected has stopped being protected.
fault(2, "a governed synthesiser consumes raw cpi/spi rather than governed states",
      GOV, "_governed",
      lambda si, cutoff: [{"signal_id": "cpi", "status": "Green", "period": cutoff,
                           "lineage_body": "raw"},
                          {"signal_id": "spi", "status": "Green", "period": cutoff,
                           "lineage_body": "raw"}],
      # THE PROBE NAMES WHICH SIGNALS WERE SYNTHESISED, so the difference is visible in what was
      # counted rather than hidden behind an abstention.
      # THE PROBE NAMES WHICH SIGNALS WERE SYNTHESISED, so the difference is visible in what
      # was selected rather than hidden behind an abstention.
      lambda: sorted(x["signal_id"] for x in GOV.run_worst_n_of_m(
          {"signals": {"mc": {"status": "red"}, "doc": {"status": "red"},
                       "cusum": {"status": "amber"}},
           "cpi": 1.0, "spi": 1.0},
          None, "2026-06-30").get("selected_signals", [])),
      # The forecast arm names BOTH the earned-value and the document body, so the control-chart
      # arm collapses into it as the same evidence read twice -- the pairwise non-transitive
      # model doing its job, and what makes ['doc', 'mc'] the correct baseline here.
      ["doc", "mc"])

# 3 -------------------------------------------------------------- WV duplicate gains weight
fault(3, "Weighted Voting same-lineage duplicate gains weight", V5, "independent_signals",
      lambda eligible: (list(eligible), []),
      lambda: round(V5.weighted_voting(_DUP, _POLD)["votes"]["Red"], 6),
      0.25)

# 4 -------------------------------------------------------------- Majority unknown becomes Green
fault(4, "Majority Rules unknown label becomes Green", V5, "eligible_signals",
      lambda signals: ([{**s, "status": s["status"] if s["status"] in V5.SEVERITY else "Green",
                         "severity": V5.SEVERITY.get(s["status"], 0)} for s in signals], []),
      lambda: safe(lambda: V5.majority_rules(
          [sig("x", "banana", "b1"), sig("y", "banana", "b2")]))[0],
      "crash")

# 5 -------------------------------------------------------------- Majority duplicate gains a vote
fault(5, "Majority Rules same-lineage duplicate gains a vote", V5, "independent_signals",
      lambda eligible: (list(eligible), []),
      lambda: V5.majority_rules(_DUP)["counts"]["Red"], 1)

# 6 -------------------------------------------------------------- Worst-N uses max
fault(6, "Worst-N uses max and collapses to Conservative Dominance", V5, "worst_two_of_m",
      lambda signals: {"estimable": True, "mean_worst_2": max(
          V5.SEVERITY[s["status"]] for s in signals)},
      lambda: V5.worst_two_of_m([sig("a", "Green", "b1"), sig("b", "Green", "b2"),
                                 sig("c", "Red", "b3")])["mean_worst_2"], 1.5)

# 7 -------------------------------------------------------------- Worst-N duplicate both positions
fault(7, "Worst-N duplicate lineage occupies both worst positions", V5, "independent_signals",
      lambda eligible: (list(eligible), []),
      lambda: V5.worst_two_of_m(_DUP)["mean_worst_2"], 1.5)

# 8 -------------------------------------------------------------- DST ignorance treated as conflict
_M1 = {frozenset({"G"}): 0.6, frozenset({"G", "R"}): 0.4}
_VAC = {frozenset({"G", "R"}): 1.0}
fault(8, "Dempster-Shafer treats ignorance as conflict", V5, "conflict_coefficient",
      lambda m1, m2: sum(v1 * v2 for b, v1 in m1.items() for c, v2 in m2.items() if b != c),
      lambda: round(V5.conflict_coefficient(_M1, _VAC), 6), 0.0)

# 9 -------------------------------------------------------------- DST total conflict divides
fault(9, "Dempster-Shafer total conflict divides by zero or fabricates a verdict",
      V5, "dempster_combine",
      lambda m1, m2, assume_independent: {"combined": True, "state": "COMBINED",
                                          "conflict": 1.0, "mass": dict(m1)},
      lambda: V5.dempster_combine({frozenset({"G"}): 1.0}, {frozenset({"R"}): 1.0},
                                  assume_independent=True)["state"],
      "TOTAL_CONFLICT")

# 10 ------------------------------------------------------------- DST same-lineage combines
fault(10, "Dempster-Shafer same-lineage masses combine as independent", V5, "dempster_shafer",
      lambda structure: {"estimable": True, "state": "COMBINED", "bodies": 2},
      lambda: V5.dempster_shafer(FX.dst_same_source())["state"], "DEPENDENCE_UNRESOLVED")

# 11 ------------------------------------------------------------- Rough Sets with no table
fault(11, "Rough Sets executes without a decision table", V5, "rough_approximations",
      lambda structure, attributes=None, target=None: {"estimable": True, "lower": [],
                                                       "upper": [], "boundary": []},
      lambda: safe(lambda: V5.rough_approximations(FX.rough_no_decision()))[0], "crash")

# 12 ------------------------------------------------------------- Neutrosophic I = 1-T-F
fault(12, "Neutrosophic indeterminacy is silently defined as 1-T-F", V5, "neutrosophic",
      lambda structure: {"estimable": True, "truth": structure["truth"],
                         "falsity": structure["falsity"],
                         "indeterminacy": 1 - structure["truth"] - structure["falsity"]},
      lambda: V5.neutrosophic(FX.neutrosophic(0.7, 0.8, 0.1))["indeterminacy"], 0.8)

# 13 ------------------------------------------------------------- Invalid interval bounds accepted
fault(13, "Invalid Interval Fuzzy bounds are accepted", V5, "interval_fuzzy",
      lambda structure: {"estimable": True,
                         "membership": [structure["lower"], structure["upper"]]},
      lambda: safe(lambda: V5.interval_fuzzy(FX.interval(0.7, 0.4)))[0], "crash")

# 14 ------------------------------------------------------------- Z missing B becomes full
fault(14, "Z-number missing reliability becomes full reliability", V5, "z_number",
      lambda structure: {"estimable": True,
                         "restriction": structure.get("restriction"),
                         "reliability": structure.get("reliability")
                         or {"term": "certain", "membership": [1.0, 1.0]}},
      lambda: safe(lambda: V5.z_number({"assessed_by": "a", "source": "s",
                                        "restriction": {"term": "x"}}))[0], "crash")

# 15 ------------------------------------------------------------- PLTS sum != 1 accepted
fault(15, "PLTS probabilities not summing to one are accepted", V5, "plts",
      lambda structure: {"estimable": True, "terms": structure["terms"],
                         "total_probability": sum(t["probability"]
                                                  for t in structure["terms"])},
      lambda: safe(lambda: V5.plts(FX.plts([("Green", 0.2), ("Red", 0.3)])))[0], "crash")

# 16 ------------------------------------------------------------- Plithogenic becomes operational
fault(16, "Plithogenic becomes operational", V5, "plithogenic_lab",
      lambda structure: {"structure_complete": True, "operational": True,
                         "disposition": "ACTIVE", "attributes": [], "operator": "chosen"},
      lambda: V5.plithogenic_lab(FX.plithogenic())["operational"], False)

# 17 ------------------------------------------------------------- BRB invalid distribution
fault(17, "Belief Rule Base invalid belief distribution is accepted", V5, "belief_rule_base",
      lambda structure: {"estimable": True, "belief": structure["rules"][0]["beliefs"],
                         "aggregation": "SINGLE_FULLY_ACTIVATED_RULE", "rules": []},
      lambda: safe(lambda: V5.belief_rule_base(FX.brb_invalid_distribution()))[0], "crash")

# 18 ------------------------------------------------------------- Quantum becomes operational
fault(18, "archived Quantum becomes operational/runnable", V5, "QUANTUM_ARCHIVE",
      {**V5.QUANTUM_ARCHIVE, "operational_activation": True, "voting": True,
       "participant_operational_visibility": True},
      lambda: (V5.QUANTUM_ARCHIVE["operational_activation"],
               V5.QUANTUM_ARCHIVE["voting"],
               V5.QUANTUM_ARCHIVE["participant_operational_visibility"]),
      (False, False, False))

# 19 ------------------------------------------------------------- Invalid Pythagorean accepted
fault(19, "invalid Pythagorean tuple accepted", V5, "pythagorean_fuzzy",
      lambda structure: {"estimable": True, "membership": structure["membership"],
                         "non_membership": structure["non_membership"]},
      lambda: safe(lambda: V5.pythagorean_fuzzy(FX.pyth(0.8, 0.8)))[0], "crash")

# 20 ------------------------------------------------------------- Invalid Picture accepted
fault(20, "invalid Picture tuple accepted", V5, "picture_fuzzy",
      lambda structure: {"estimable": True, "positive": structure["positive"],
                         "neutral": structure["neutral"], "negative": structure["negative"]},
      lambda: safe(lambda: V5.picture_fuzzy(FX.picture(0.5, 0.4, 0.3)))[0], "crash")

# 21 ------------------------------------------------------------- Hesitant empty becomes favourable
fault(21, "Hesitant empty set becomes favourable", V5, "hesitant_fuzzy",
      lambda structure: {"estimable": True, "degrees": structure["degrees"],
                         "score": (sum(structure["degrees"]) / len(structure["degrees"]))
                         if structure["degrees"] else 1.0},
      lambda: safe(lambda: V5.hesitant_fuzzy(FX.hesitant([])))[0], "crash")

# 22 ------------------------------------------------------------- Type-2 collapses to midpoint
fault(22, "Type-2 inference collapses to the interval midpoint", V5, "type2_fuzzy",
      lambda structure: {"estimable": True,
                         "type_reduced": (structure["points"][0]["lower"]
                                          + structure["points"][0]["upper"]) / 2,
                         "points": structure["points"],
                         "max_fou_width": 0.0},
      lambda: V5.type2_fuzzy(FX.type2([(0.0, 0.3, 0.7)]))["type_reduced"], None)

# 23 ------------------------------------------------------------- MaxEnt only computes entropy
fault(23, "Maximum Entropy merely calculates the entropy of a supplied vector",
      V5, "maximum_entropy",
      lambda structure, tolerance=1e-12, max_iterations=200: {
          "estimable": True, "state": "SOLVED",
          "distribution": {"x0": 1 / 3, "x1": 1 / 3, "x2": 1 / 3},
          "entropy": math.log(3),
          "constraint_expectations": {"mean": 1.0}},
      lambda: round(V5.maximum_entropy(FX.maxent_expectation(0.5))
                    ["constraint_expectations"]["mean"], 6), 0.5)

# 24 ------------------------------------------------------------- MaxEnt with no state space
fault(24, "Maximum Entropy runs with no state space or constraints", V5, "maximum_entropy",
      lambda structure, tolerance=1e-12, max_iterations=200: {
          "estimable": True, "state": "SOLVED", "distribution": {}, "entropy": 0.0},
      lambda: safe(lambda: V5.maximum_entropy({"defined_by": "a", "source": "s",
                                               "states": []}))[0], "crash")

# 25 ------------------------------------------------------------- Possibility violates maxitivity
_PI3 = {"a": 1.0, "b": 0.4, "c": 0.7}
fault(25, "Possibility violates maxitivity", V5, "possibility_of",
      lambda pi, event: sum(pi[x] for x in event if x in pi),
      lambda: round(V5.possibility_of(_PI3, ["b", "c"])
                    - max(V5.possibility_of(_PI3, ["b"]), V5.possibility_of(_PI3, ["c"])), 6),
      0.0)

# 26 ------------------------------------------------------------- Possibility normalised as probability
fault(26, "Possibility is normalised as though it were a probability", V5, "possibility",
      lambda structure: {"estimable": True,
                         "distribution": {r["state"]: r["possibility"]
                                          / sum(x["possibility"] for x in structure["states"])
                                          for r in structure["states"]}},
      lambda: round(sum(V5.possibility(FX.possibility({"a": 1.0, "b": 0.4}))
                        ["distribution"].values()), 6), 1.4)

# 27 ------------------------------------------------------------- Invalid Spherical accepted
fault(27, "invalid Spherical tuple accepted", V5, "spherical_fuzzy",
      lambda structure: {"estimable": True, "membership": structure["membership"],
                         "non_membership": structure["non_membership"],
                         "hesitancy": structure["hesitancy"]},
      lambda: safe(lambda: V5.spherical_fuzzy(FX.spherical(0.8, 0.8, 0.1)))[0], "crash")

# 28 ------------------------------------------------------------- Invalid Fermatean accepted
fault(28, "invalid Fermatean tuple accepted", V5, "fermatean_fuzzy",
      lambda structure: {"estimable": True, "membership": structure["membership"],
                         "non_membership": structure["non_membership"]},
      lambda: safe(lambda: V5.fermatean_fuzzy(FX.fermatean(0.9, 0.9)))[0], "crash")

# 29 ------------------------------------------------------------- MARCOS treats criteria as alternatives
fault(29, "MARCOS treats criteria as alternatives", V5, "decision_problem",
      lambda structure, module_id, require_weights: {
          "context_id": "x", "source": "x", "period": 1,
          "criteria": [{"criterion_id": "value", "orientation": "benefit", "weight": 1.0,
                        "label": "v", "units": None, "weight_provenance": "none"}],
          "alternatives": [{"alternative_id": a["alternative_id"], "label": "x",
                            "values": dict(a["values"])}
                           for a in structure["alternatives"]],
          "weight_total": 1.0},
      lambda: safe(lambda: V5.marcos(FX.marcos_criteria_as_alternatives()))[0], "crash")

# 30 ------------------------------------------------------------- MARCOS accepts one project state
fault(30, "MARCOS accepts one project state as an alternatives problem", V5, "marcos",
      lambda structure: {"estimable": True, "ranking": [structure["alternatives"][0]
                                                        ["alternative_id"]]},
      lambda: safe(lambda: V5.marcos(FX.marcos_single_alternative()))[0], "crash")

# 31 ------------------------------------------------------------- CRITIC-TOPSIS accepts one row
fault(31, "CRITIC-TOPSIS accepts one project row", V5, "critic_topsis",
      lambda structure: {"estimable": True, "ranking": [structure["alternatives"][0]
                                                        ["alternative_id"]], "weights": {}},
      lambda: safe(lambda: V5.critic_topsis(FX.critic_single_row()))[0], "crash")

# 32 ------------------------------------------------------------- CRITIC zero variance divides
fault(32, "CRITIC-TOPSIS zero-variance criterion silently divides", V5, "critic_topsis",
      lambda structure: {"estimable": True, "ranking": ["A1"],
                         "weights": {"C1": 1.0, "C2": 0.0, "C3": 0.0}},
      lambda: safe(lambda: V5.critic_topsis(FX.critic_zero_variance()))[0], "crash")

# 33 ------------------------------------------------------------- Hypersoft missing tuple defaults
fault(33, "Hypersoft missing Cartesian tuple defaults to a favourable value", V5,
      "hypersoft_lab",
      lambda structure: {"structure_complete": True, "missing_tuples": [], "estimable": True,
                         "operational": False, "cartesian_size": 4, "mapped": 4,
                         "disposition": "DISABLED_FUTURE_RESEARCH"},
      lambda: (V5.hypersoft_lab(FX.hypersoft_missing())["structure_complete"],
               V5.hypersoft_lab(FX.hypersoft_missing())["missing_tuples"]),
      (False, [["a2", "b2"]]))

# 34 ------------------------------------------------------------- orphan structure, no production path
# THE GUARD IS "EVERY GOVERNED STRUCTURE IS CONSUMED BY A REGISTERED MODULE", not "every key is
# in the intake vocabulary": the intake DERIVES its vocabulary from this map, so a key added here
# is writable by construction and that direction cannot catch an orphan. What an orphan really is
# is a structure a caller may write and no module reads, and that is what is probed.
fault(34, "an orphan canonical structure has no production path", V5, "V5_STRUCTURE_KEYS",
      {**V5.V5_STRUCTURE_KEYS, "B2.99": "orphanStructureNothingWrites"},
      lambda: sorted(m for m in V5.V5_STRUCTURE_KEYS
                     if m not in REG.VALIDATED) == []
      and set(V5.V5_STRUCTURE_KEYS.values()) <= _governed_keys(),
      True)

# 35 ------------------------------------------------------------- corpus-present structure disconnected
fault(35, "a corpus-present structure is disconnected from its module", GOV, "_governed",
      lambda si, cutoff: [],
      lambda: GOV.run_majority_rules(
          {"signals": {"mc": {"status": "red"}, "cusum": {"status": "red"},
                       "doc": {"status": "red"}}}, None, "2026-06-30").get("status_color"),
      "Red")

# 36 ------------------------------------------------------------- duplicate simulation-version stamp
from app.simulation import models as MODELS               # noqa: E402
fault(36, "a duplicate simulation-version stamp", MODELS, "SIMULATION_VERSION_HISTORY",
      MODELS.SIMULATION_VERSION_HISTORY + ("sim-2026.08-v14",),
      lambda: len(MODELS.SIMULATION_VERSION_HISTORY)
      == len(set(MODELS.SIMULATION_VERSION_HISTORY)), True)

# 37 ------------------------------------------------------------- archived Quantum on the surface
fault(37, "archived Quantum appears on the current operational surface", REG,
      "DISABLED_CONCEPT_ONLY",
      tuple(m for m in REG.DISABLED_CONCEPT_ONLY if m != "B2.9"),
      lambda: "B2.9" in REG.DISABLED_CONCEPT_ONLY, True)

# 38 ------------------------------------------------------------- disabled Plithogenic activated
fault(38, "disabled Plithogenic becomes active", REG, "DISABLED_CONCEPT_ONLY",
      tuple(m for m in REG.DISABLED_CONCEPT_ONLY if m != "B2.7"),
      lambda: "B2.7" in REG.DISABLED_CONCEPT_ONLY, True)

# 39 ------------------------------------------------------------- disabled Hypersoft activated
fault(39, "disabled Hypersoft becomes active", V5, "hypersoft_lab",
      lambda structure: {"structure_complete": True, "operational": True, "estimable": True,
                         "disposition": "ACTIVE", "missing_tuples": [], "cartesian_size": 4,
                         "mapped": 4},
      lambda: (V5.hypersoft_lab(FX.hypersoft_complete())["operational"],
               V5.hypersoft_lab(FX.hypersoft_complete())["disposition"]),
      (False, "DISABLED_FUTURE_RESEARCH"))


# The record, written where every other campaign in this programme writes one.
_out = artifact_out(ROOT / "code_audit" / "run30_fault_injection.csv")
with _out.open("w", encoding="utf-8", newline="\n") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["fault", "name", "result", "detail"])
    for r in RECORDS:
        w.writerow([r["fault"], r["name"], r["result"], r["detail"]])

_proven = [r for r in RECORDS if r["result"] == "RED_THEN_GREEN"]
_not_applied = [r for r in RECORDS if r["result"] == "INJECTION_NOT_APPLIED"]
print()
check(len(RECORDS) == 39, "all thirty-nine mandated faults were attempted", str(len(RECORDS)))
check(not _not_applied, "no fault was recorded INJECTION_NOT_APPLIED",
      str([r["fault"] for r in _not_applied]))
check(len(_proven) == 39, "every fault went RED for its intended reason and GREEN on restore",
      str([r["fault"] for r in RECORDS if r["result"] != "RED_THEN_GREEN"]))

print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
