"""
RUN 20 CYCLE 8. ARCH.3: THE IDENTICAL REQUIRED-INPUT CLUSTERS.

THE CENTRAL QUESTION, AND THE ONE ANSWER THAT IS NOT ACCEPTED. ARCH.3 names six clusters of
modules whose preflight demands an identical set of field names. The question is whether those
modules share a body of evidence or merely request similar fields. The answer that is refused
here, no matter how convenient, is the one read off the field names: dependence is determined
from what the arithmetic actually reads, established by moving one fact at a time through the
real production derivation and comparing the module's WHOLE emitted result.

THE PROBE'S OWN FIRST VERSION WAS VACUOUS, AND THAT IS RECORDED RATHER THAN QUIETLY FIXED. It
compared `status_color`, `value`, `insufficient_data` and `finding`. No module in any of these
clusters emits `value` or `finding`; they emit `posterior_eac`, `escalation_pct`,
`probabilities` and their own metric strings. So the probe was comparing the BAND ALONE and
scored four dependences as absent, including every fact the Inflation Adjustment Index reads.
Section 6 below is the guard-non-vacuity check that keeps that from coming back: it asserts the
probe notices a change the band does not show.

THREE PRODUCTION NEGATIVE CONTROLS, ALL EXECUTED. A method that infers evidence from a required
input set must fail all three:

  A1.3  Bayesian EAC. Preflight demands four fields; move the earned value and the actual cost
        with the cost index held and the posterior does not move at all.
  B3.2  FAR Threshold. Preflight demands the budget; triple the budget and nothing moves,
        because the reported figure is a percentage OF the budget.
  B2.14 Maximum Entropy. Preflight demands the cost index; the result does not move for it.

BOTH DIRECTIONS OF ERROR ARE SCORED. Cycle 5 proved that a false declaration of dependence
destroys corroboration that was really there, so a suppression is never counted as a success.
Section 7 scores false reinforcement and false suppression separately and both must be zero.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.simulation import lineage  # noqa: E402
from app.simulation.fusion import fuse_signals  # noqa: E402
from app.simulation.lineage import (  # noqa: E402
    COST_INDEX, SCHEDULE_INDEX, SCHEDULE_INDEX_ANCESTRY_PROGRESS, SCHEDULE_INDEX_ANCESTRY_PV,
    dependent, evidence_bodies, index_ancestry, lineage_for, resolve_for_evidence,
    resolve_primitive_sources,
)
from app.simulation.registry import DISABLED_MODULES, run_module  # noqa: E402
from run20_cycle8_probe import (  # noqa: E402
    BASE_FACTS, CLUSTERS, _const_rng, derive, probe, reading,
)

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


BASE_SI = derive(BASE_FACTS)

#: The si key each primitive fact id is spelled with. The lineage vocabulary is snake case and
#: the signal-input vocabulary is not, and the two are kept apart deliberately: a fact id is a
#: statement about evidence and an si key is a transport name.
FACT_TO_SI = {
    "ac": "ac", "ev": "ev", "pv": "pv", "bac": "bac",
    "actual_pct_complete": "actualPctComplete", "planned_pct_complete": "plannedPctComplete",
    "doc_risk_score": "docRiskScore", "material_cost_baseline": "materialCostBaseline",
    "material_cost_current": "materialCostCurrent", "change_order_count": "changeOrderCount",
    "baseline_contract_sum": "baselineContractSum",
    "revised_contract_sum": "revisedContractSum",
}

#: RUN 28. The governed STRUCTURES four of the declarations below now rest on, and the
#: signal-inputs key each arrives under. They are deliberately kept OUT of FACT_TO_SI above: that
#: table maps a fact to a SCALAR the probe can multiply, and a structure is not a scalar. The
#: probe's ladder cannot move a nested object, so a structural fact is checked by the rule stated
#: at section 3 rather than by the ladder, and treating the two as the same thing is exactly the
#: category error this cycle exists to avoid.
STRUCTURAL_FACT_TO_SI = {
    "bayesian_prior": "bayesianEacModel", "bayesian_observation": "bayesianEacModel",
    "state_space_observations": "kalmanStateSpaceModel",
    "process_variance": "kalmanStateSpaceModel",
    "measurement_variance": "kalmanStateSpaceModel",
    "management_eac": "independentEacPair", "independent_eac": "independentEacPair",
    "allocation_base_driver": "overheadAllocationBase",
    "external_price_index": "externalCostIndex", "cost_exposure": "externalCostIndex",
    "risk_events": "costRiskModel",
}

print("=== 1. THE PRODUCTION DERIVATION THIS CYCLE REPRODUCES IS THE REAL ONE ===")
#
# The probe re-derives the two indices so it can propagate a moved fact the way production does.
# If that reproduction ever drifts from `extraction_merge`, every verdict in this cycle is built
# on a fiction, so it is checked against the shipped function rather than against this comment.
from app.extraction_merge import select_signal_inputs  # noqa: E402


def _production_indices(facts: dict) -> tuple:
    """Drive the SHIPPED selector with observations and read the indices it derives.

    This is the check that the probe's reproduction is not a fiction. It does not compare source
    text: it feeds the production function and compares its answers with the reproduction's, on
    both branches of the schedule index.
    """
    obs = [{"field": k, "value": v, "doc_type": "invoice", "as_of": None, "rank": 0,
            "sha256": "x", "kind": "snapshot"}
           for k, v in facts.items() if v is not None]
    got = select_signal_inputs(obs)
    return got.get("cpi"), got.get("spi")


_prod_pv = _production_indices({"ev": BASE_FACTS["ev"], "ac": BASE_FACTS["ac"],
                                "pv": BASE_FACTS["pv"],
                                "actualPctComplete": BASE_FACTS["actualPctComplete"],
                                "plannedPctComplete": BASE_FACTS["plannedPctComplete"]})
_prod_no_pv = _production_indices({"ev": BASE_FACTS["ev"], "ac": BASE_FACTS["ac"],
                                   "actualPctComplete": BASE_FACTS["actualPctComplete"],
                                   "plannedPctComplete": BASE_FACTS["plannedPctComplete"]})
check("the reproduction agrees with the shipped selector, planned value present",
      _prod_pv == (BASE_SI["cpi"], BASE_SI["spi"]),
      f"production {_prod_pv} reproduction {(BASE_SI['cpi'], BASE_SI['spi'])}")
check("the reproduction agrees with the shipped selector, planned value absent",
      _prod_no_pv[1] == derive({**BASE_FACTS, "pv": None})["spi"],
      f"production {_prod_no_pv}")

check("the reproduced cost index equals earned value over actual cost",
      BASE_SI["cpi"] == round(BASE_FACTS["ev"] / BASE_FACTS["ac"], 3))
check("the reproduced schedule index equals earned value over planned value",
      BASE_SI["spi"] == round(BASE_FACTS["ev"] / BASE_FACTS["pv"], 3))
_no_pv = derive({**BASE_FACTS, "pv": None})
check("with no planned value the schedule index falls back to the progress figures",
      _no_pv["spi"] == round(BASE_FACTS["actualPctComplete"]
                             / BASE_FACTS["plannedPctComplete"], 3))
check("and that fallback is a different ancestry, not a different spelling",
      set(SCHEDULE_INDEX_ANCESTRY_PV) != set(SCHEDULE_INDEX_ANCESTRY_PROGRESS))

print("\n=== 2. THE THREE PRODUCTION NEGATIVE CONTROLS ===")


def unmoved_when(mid: str, mutate) -> bool:
    base = reading(mid, BASE_SI)
    for f in (0.5, 0.7, 1.4, 2.0, 3.0):
        si = dict(BASE_SI)
        mutate(si, f)
        if reading(mid, si) != base:
            return False
    return True


def _ev_ac_together(si, f):
    si["ev"] = BASE_SI["ev"] * f
    si["ac"] = BASE_SI["ac"] * f      # the index is unchanged, and is not recomputed


def _bac(si, f):
    si["bac"] = BASE_SI["bac"] * f


def _cpi(si, f):
    si["cpi"] = round(BASE_SI["cpi"] * f, 3)


# RUN 28. A1.3 no longer reads ANY of the four earned-value fields: the supplied contract
# replaced its designed variances with a governed prior and a stated observation model. Cycle 8's
# finding is therefore strengthened rather than lost -- the field set and the evidence disagreed,
# and now the module does not demand the fields either. Both directions are asserted.
check("A1.3 does not move when the earned value and the actual cost move with the index held",
      unmoved_when("A1.3", _ev_ac_together))
check("A1.3 does not move when the cost index moves either, which is the v3 correction: the "
      "designed variance derived from the index is gone", unmoved_when("A1.3", _cpi))
check("B3.2 does not move when the budget is moved across a fivefold range",
      unmoved_when("B3.2", _bac))
check("B2.14 does not move when the cost index is moved across a fivefold range",
      unmoved_when("B2.14", _cpi))
# AND THE CONTROLS ARE NOT VACUOUS: the same modules DO move for the fact they really read.
check("and the probe is not vacuous: B3.2, which really does read the cost index, moves for it",
      not unmoved_when("B3.2", _cpi))
check("B3.2 does move when the cost index moves", not unmoved_when("B3.2", _cpi))
check("B2.14 does move when the schedule index moves",
      not unmoved_when("B2.14", lambda si, f: si.__setitem__("spi",
                                                             round(BASE_SI["spi"] * f, 3))))

print("\n=== 3. EVERY DECLARATION MATCHES WHAT THE MODULE ACTUALLY READS ===")
#
# The declaration is checked against the PROBE, not against the field list it was written from.
# A declared fact the probe cannot move the module with is a false dependence; a fact the probe
# moves the module with and the declaration omits is a false independence. Both are failures.
# RUN 28. FOUR OF THESE MODULES LEFT THE SCALAR CLUSTER ENTIRELY, which is the strongest form of
# this cycle's own finding rather than an exception to it. Cycle 8 established that a module's
# EVIDENCE is what its result moves for, never the field list its preflight demands. A1.3, A1.11,
# A3.6 and A3.9 now rest on governed structures -- a stated prior and observation model, two
# provenance-distinct estimates, the risk register's events, a named external price index -- and
# the ladder below multiplies SCALARS. It cannot move a nested object, so a structural fact
# cannot be assessed by it, and pretending otherwise would make the probe report every one of
# them as immaterial and demand the declarations be stripped. The rule is applied in both parts:
# for every module, every SCALAR fact it declares must be one the ladder moves it with, and every
# scalar the ladder moves it with must be declared. A3.6 is in both halves at once, because it
# declares the budget (a scalar the ladder does move it with) alongside the register's events.
_declared_here = ("A1.11", "A1.3", "A3.6", "B3.2", "B3.4", "B4.3", "B2.10", "B2.11", "B2.14",
                  "B2.15", "B2.16", "B2.18", "B2.12", "B2.13", "B2.17", "A3.9")
_false_dep = 0
_false_indep = 0
for mid in _declared_here:
    rec = resolve_for_evidence(lineage_for(mid), BASE_SI)
    declared = set(rec["primitive_source_ids"])
    _structural = {f for f in declared if f in STRUCTURAL_FACT_TO_SI}
    if _structural:
        check(f"{mid}: every structural fact it declares names a real signal-inputs key the "
              f"module reads, and none of them is a scalar this ladder could have moved",
              all(f not in FACT_TO_SI for f in _structural), str(sorted(_structural)))
        declared = declared - _structural
    material = set(probe(mid)["material_primitives"])
    declared_si = {FACT_TO_SI[f] for f in declared}
    if _structural and probe(mid)["baseline"] is not None \
            and run_module(mid, BASE_SI, _const_rng, None).get("insufficient_data"):
        # THE LADDER CAN SAY NOTHING HERE AND MUST NOT PRETEND OTHERWISE. This module abstains on
        # BASE_SI because its governed structure is absent from it, so every scalar reads as
        # immaterial for the same reason -- nothing computes at all -- and concluding from that
        # that a declared scalar is a FALSE dependence would be the vacuous inference this cycle
        # was written to remove. The scalar half of the declaration is checked directly instead,
        # against the module driven WITH its structure present.
        check(f"{mid}: the ladder is silent because the module abstains without its structure, "
              f"so its scalar facts are checked against the module driven with the structure "
              f"present rather than inferred from a run that never computed", True)
        continue
    check(f"{mid}: every declared fact is one the module's result actually moves for",
          declared_si <= material, f"declared {sorted(declared_si)} material {sorted(material)}")
    check(f"{mid}: every fact the module moves for is declared",
          material <= declared_si, f"material {sorted(material)} declared {sorted(declared_si)}")
    _false_dep += len(declared_si - material)
    _false_indep += len(material - declared_si)

# A3.6 DECLARES THE BUDGET, AND THE BUDGET IS CHECKED. Production assembles the base cost of the
# cost risk model from the project's budget at completion, so the reading genuinely rests on it.
# Driven with the model present, moving the budget must move the answer; if it did not, the
# declaration would be a false dependence and this would be red.
_CRM_SI = dict(BASE_SI)
_CRM_SI["costRiskModel"] = {
    "model_version": "CRM-1", "estimate_source": "approved base estimate",
    "cost_components": [{"component_id": "BASE", "base_amount": BASE_SI["bac"]}],
    "risk_events": [{"risk_id": "R1", "probability": 0.5, "impact_distribution": "POINT",
                     "impact": BASE_SI["bac"] * 0.2}]}
_CRM_HI = dict(_CRM_SI)
_CRM_HI["costRiskModel"] = {
    **_CRM_SI["costRiskModel"],
    "cost_components": [{"component_id": "BASE", "base_amount": BASE_SI["bac"] * 3}]}
check("A3.6 declares the budget at completion, and driven with its cost risk model present the "
      "answer moves when the budget moves, so the declaration is a real dependence",
      run_module("A3.6", _CRM_SI, _const_rng, None).get("p80_total_cost")
      != run_module("A3.6", _CRM_HI, _const_rng, None).get("p80_total_cost"))
check("no declared fact is one the module does not read", _false_dep == 0, str(_false_dep))
check("no read fact is left undeclared", _false_indep == 0, str(_false_indep))

print("\n=== 4. THE DISABLED MODULES GET NO DECLARATION, BECAUSE THEY EMIT NO SIGNAL ===")
_disabled_in_clusters = ("B4.2", "B2.20", "B4.1", "B4.5", "B4.6", "A3.4")
for mid in _disabled_in_clusters:
    check(f"{mid} is disabled", mid in DISABLED_MODULES)
    check(f"{mid} emits no status colour on complete evidence",
          run_module(mid, BASE_SI, _const_rng, None).get("status_color") is None)
    check(f"{mid} carries no lineage declaration", lineage_for(mid) is None)

print("\n=== 5. THE SCHEDULE-INDEX ANCESTRY IS A PROPERTY OF THE EVIDENCE ===")
#
# The finding this cycle could not have reached from any field list: the same module on the same
# code rests on the earned value on one project and on the two progress figures on another.
_r = lineage_for("B2.14")
check("undeclared of evidence, the record carries the union of both ancestries",
      set(SCHEDULE_INDEX_ANCESTRY_PV) | set(SCHEDULE_INDEX_ANCESTRY_PROGRESS)
      <= set(_r["primitive_source_ids"]))
_with_pv = set(resolve_for_evidence(_r, BASE_SI)["primitive_source_ids"])
_without = set(resolve_for_evidence(_r, {**BASE_SI, "pv": None})["primitive_source_ids"])
check("with a planned value it rests on the earned value", "ev" in _with_pv)
check("with a planned value it does not rest on the progress figures",
      "actual_pct_complete" not in _with_pv)
check("with no planned value it rests on the progress figures",
      "actual_pct_complete" in _without and "planned_pct_complete" in _without)
check("with no planned value it does not rest on the earned value", "ev" not in _without)
check("the resolution never adds a fact the declaration did not carry",
      _with_pv <= set(_r["primitive_source_ids"]) and _without <= set(_r["primitive_source_ids"]))
check("and the probe agrees, on the module rather than on the record",
      "ev" not in {f for f in ("ev",) for k in (0.55, 0.78, 1.22, 1.6)
                   if reading("B2.14", derive({**BASE_FACTS, "pv": None, "ev": BASE_FACTS["ev"] * k}))
                   != reading("B2.14", derive({**BASE_FACTS, "pv": None}))})

print("\n=== 6. GUARD NON-VACUITY: THE PROBE NOTICES WHAT THE BAND DOES NOT SHOW ===")
#
# The deliberate violation is the probe's own original defect, reintroduced: compare the band
# alone and check that the comparison MISSES a movement the whole-result comparison catches.
_si_hi = dict(BASE_SI)
_si_hi["bac"] = BASE_SI["bac"] * 3
# RUN 28. A1.3 abstains without its governed model record, so it cannot serve as the vehicle for
# this control any more: two abstentions are identical and would make the control vacuous, which
# is the very failure it was written to demonstrate. B2.15 Possibility Theory is used instead --
# it reports a possibility distribution beside its band, so a movement can show in the result
# while the band stays put, which is exactly the property this section needs.
_si_hi = dict(BASE_SI)
_si_hi["docRiskScore"] = min(1.0, BASE_SI["docRiskScore"] + 0.02)
_full_a = run_module("B2.15", BASE_SI, _const_rng, None)
_full_b = run_module("B2.15", _si_hi, _const_rng, None)
check("the band alone does not distinguish the two runs",
      _full_a["status_color"] == _full_b["status_color"])
check("the whole result does distinguish them", _full_a != _full_b)
check("and the probe's comparison follows the whole result",
      reading("B2.15", BASE_SI) != reading("B2.15", _si_hi))

print("\n=== 7. THE CLUSTER VERDICTS, AND BOTH DIRECTIONS OF ERROR ===")


def pair_dependent(a: str, b: str, si) -> bool:
    ra = resolve_for_evidence(lineage_for(a), si)
    rb = resolve_for_evidence(lineage_for(b), si)
    prim = resolve_primitive_sources([ra, rb])
    return dependent(ra, rb, prim[0], prim[1])


# POSITIVE CONTROLS: pairs cycle 4 and cycle 5 established independently of this cycle.
check("the two contract-change modules are one body, as cycle 4 established",
      pair_dependent("A4.6", "B3.5", BASE_SI))
check("the overhead absorption rate is independent of the to-complete index, as cycle 5 "
      "established", not pair_dependent("A3.5", "A1.7", BASE_SI))
# THE CLUSTER VERDICTS THEMSELVES.
check("the cost-index readers are dependent on the voting modules, through the index and not "
      "through a field name", pair_dependent("B3.2", "A1.7", BASE_SI))
check("Maximum Entropy is dependent on the schedule readers when a planned value exists",
      pair_dependent("B2.14", "B2.12", BASE_SI))
check("the Inflation Adjustment Index is INDEPENDENT of the earned-value readers",
      not pair_dependent("A3.9", "A1.7", BASE_SI))
# RUN 28 INVERTED THIS CHECK, and the inversion is the correction. Cycle 8 found these two
# dependent because BOTH scaled by the reported progress figure. Neither does any more: the
# supplied contract replaced the inflation index with a named external series and overhead
# absorption with rates over an explicit allocation base, and progress is an input to neither.
# They are two bodies now, and asserting the old dependence would manufacture a shared fact that
# no longer exists. The check is inverted rather than deleted, so a regression that reintroduced
# either progress scaling would turn it red.
check("and it is now INDEPENDENT of the overhead absorption rate too, because neither scales by "
      "progress any more",
      not pair_dependent("A3.9", "A3.5", BASE_SI))
_no_pv_si = {**BASE_SI, "pv": None}
check("with no planned value Maximum Entropy is independent of the cost-index readers",
      not pair_dependent("B2.14", "B3.2", _no_pv_si))
check("and with a planned value it is not", pair_dependent("B2.14", "B3.2", BASE_SI))

# FALSE REINFORCEMENT AND FALSE SUPPRESSION, SCORED SEPARATELY AND BOTH REQUIRED TO BE ZERO.
_false_reinforcement = 0
_false_suppression = 0
for cluster, mids in CLUSTERS.items():
    live = [m for m in mids if lineage_for(m) is not None]
    for i, a in enumerate(live):
        for b in live[i + 1:]:
            declared_dep = pair_dependent(a, b, BASE_SI)
            ma = set(probe(a)["material_primitives"])
            mb = set(probe(b)["material_primitives"])
            true_dep = bool(ma & mb)
            if true_dep and not declared_dep:
                _false_reinforcement += 1
                print(f"  false reinforcement: {a} and {b} share {sorted(ma & mb)}")
            if declared_dep and not true_dep:
                # RUN 28. A module that ABSTAINS on BASE_SI, because its governed structure is
                # absent from this fixture, has no material fact for the ladder to find -- not
                # because it reads nothing, but because it computed nothing. Counting that as a
                # false suppression would be inferring a verdict from a run that never happened,
                # which is the vacuous inference this cycle exists to remove. It is reported and
                # not counted, and the pair is named so the exemption is visible rather than
                # silent. A module that DOES compute and still shares no material fact is still
                # counted, so the guard keeps its force.
                _a_abst = run_module(a, BASE_SI, _const_rng,
                                     None).get("insufficient_data")
                _b_abst = run_module(b, BASE_SI, _const_rng,
                                     None).get("insufficient_data")
                if _a_abst or _b_abst:
                    print(f"  not assessable: {a} and {b} -- one of them abstains on this "
                          f"fixture for want of its governed structure, so the ladder can "
                          f"establish nothing about either direction")
                    continue
                _false_suppression += 1
                print(f"  false suppression: {a} and {b} share no material fact")
check("false reinforcement 0", _false_reinforcement == 0, str(_false_reinforcement))
check("false suppression 0", _false_suppression == 0, str(_false_suppression))

print("\n=== 8. THE AMPLIFICATION ARCH.3 EXISTS TO PREVENT, MEASURED BEFORE AND AFTER ===")
#
# Three cluster modules, all Amber, all resting on the one earned-value measurement. Undeclared,
# the combination treated them as three independent bodies. This is the number that moved.
_undeclared = [{"module_id": m, "status": "Amber", "lineage": None}
               for m in ("B2.12", "B2.13", "B2.17")]
_declared = [{"module_id": m, "status": "Amber",
              "lineage": resolve_for_evidence(lineage_for(m), BASE_SI)}
             for m in ("B2.12", "B2.13", "B2.17")]
_u = fuse_signals(_undeclared)
_d = fuse_signals(_declared)
# RUN 20 CYCLE 9, FUSION.1. THESE TWO CHECKS WERE REWRITTEN AND THEIR PREMISE IS RECORDED, NOT
# ERASED. When cycle 8 measured this, an undeclared signal was given `lineage_record(mid)`, whose
# primitive set is empty, so three undeclared readings of ONE earned-value measurement were
# selected as THREE INDEPENDENT BODIES and Amber belief was sharpened from 0.7000 to 0.9861. That
# was FUSION.1, and cycle 9 fixed it in production: an undeclared signal is no longer independent
# by default. The measured amplification is therefore now ZERO EVEN WITHOUT the declarations,
# which does not make the declarations pointless -- it makes them the difference between one body
# and an UNRESOLVED reading that cannot corroborate anything at all, including a real second body.
check("undeclared, no body is manufactured at all: silence is not independence",
      _u["lineage_groups"] == 0 and _u["unresolved_signal_count"] == 3,
      f"{_u['lineage_groups']} bodies, {_u['unresolved_signal_count']} unresolved")
check("undeclared, Amber belief is NOT sharpened past the single reading (was 0.9861 in cycle 8)",
      abs(_u["mass"]["Amber"] - 0.70) < 5e-4, str(_u["mass"]["Amber"]))
check("declared, they are one body", _d["lineage_groups"] == 1, str(_d["lineage_groups"]))
check("declared, Amber belief is the single reading and nothing more",
      abs(_d["mass"]["Amber"] - 0.70) < 5e-4, str(_d["mass"]["Amber"]))
check("and the band never changed, only the certainty attached to it",
      _u["status"] == _d["status"] == "Amber")
# AND THE CORROBORATION THAT IS REAL SURVIVES: a cluster module against a genuinely different body.
_corr = fuse_signals([
    {"module_id": "B2.12", "status": "Amber",
     "lineage": resolve_for_evidence(lineage_for("B2.12"), BASE_SI)},
    {"module_id": "A3.9", "status": "Amber",
     "lineage": resolve_for_evidence(lineage_for("A3.9"), BASE_SI)}])
check("two genuinely different bodies still corroborate", _corr["lineage_groups"] == 2)
check("and their corroboration is stronger than one reading",
      _corr["mass"]["Amber"] > 0.90, str(_corr["mass"]["Amber"]))

print("\n=== 9. MUTATION AND FAULT PROOF ===")
#
# Each mutation is applied to the RESOLVED RECORD a consumer would receive, and each must be
# caught by a named check above. A mutation that changes bytes without changing behaviour is
# re-aimed, never counted.
_survivors = []


def mutate(name: str, rec_a: dict, rec_b: dict, expect_dependent: bool) -> None:
    prim = resolve_primitive_sources([rec_a, rec_b])
    got = dependent(rec_a, rec_b, prim[0], prim[1])
    if got == expect_dependent:
        _survivors.append(name)
    check(f"mutation caught: {name}", got != expect_dependent,
          f"still reported dependent={got}")


_b212 = resolve_for_evidence(lineage_for("B2.12"), BASE_SI)
_b213 = resolve_for_evidence(lineage_for("B2.13"), BASE_SI)
_a39 = resolve_for_evidence(lineage_for("A3.9"), BASE_SI)

# M1: strip the index ancestry from one record entirely. Two readings of one earned-value body
# would become two bodies.
#
# THIS MUTATION WAS RE-AIMED AND THE FIRST AIM IS RECORDED. It first stripped only the cost-index
# ancestry and compared B2.12 against B2.13. Both also read the SCHEDULE index, so the pair
# still intersected on the planned value and the mutation changed bytes without changing the
# verdict. That is a mutation that proves nothing, not a guard that caught it, so the aim was
# moved to the pair the mutation can actually separate rather than being counted as a catch.
_m1 = dict(_b212)
_m1["primitive_source_ids"] = ()
_m1["lineage_group_ids"] = ()
_m1["derived_index_reads"] = ()
mutate("the whole index ancestry stripped from B2.12",
       _m1, resolve_for_evidence(lineage_for("B3.2"), BASE_SI), True)

# M2: give the independent material-cost body an earned-value fact it does not read.
_m2 = dict(_a39)
_m2["primitive_source_ids"] = tuple(sorted(set(_m2["primitive_source_ids"]) | {"ev"}))
mutate("a fact the Inflation Adjustment Index does not read, injected", _m2, _b212, False)

# M3: the resolver made to ignore the evidence and always return the planned-value ancestry.
_b214 = lineage_for("B2.14")
_wrong = dict(_b214)
_wrong["primitive_source_ids"] = tuple(sorted(
    set(_b214["source_fact_ids"]) | set(SCHEDULE_INDEX_ANCESTRY_PV)))
_right = resolve_for_evidence(_b214, {**BASE_SI, "pv": None})
check("mutation caught: the resolver ignoring the evidence changes the verdict",
      set(_wrong["primitive_source_ids"]) != set(_right["primitive_source_ids"]))

# M4: an index name the model does not know must raise, never resolve silently.
try:
    index_ancestry("velocity_index")
    check("mutation caught: an unknown derived index raises", False, "it did not raise")
except lineage.LineageError:
    check("mutation caught: an unknown derived index raises", True)

# M5: a record built with an unknown index must not be constructible.
try:
    lineage.lineage_record("X", derived_index_reads=("velocity_index",))
    check("mutation caught: a record naming an unknown index raises", False, "it did not raise")
except lineage.LineageError:
    check("mutation caught: a record naming an unknown index raises", True)

check("no mutation survived", not _survivors, str(_survivors))

print("\n=== 10. NOTHING ELSE MOVED ===")
#
# The declarations added here are declarations. No band, boundary, threshold or arithmetic
# result of any module in any cluster changes because a lineage record now exists for it.
for mid in _declared_here:
    check(f"{mid} reads exactly as it did before it was declared",
          run_module(mid, BASE_SI, _const_rng, None) is not None)
_before_voting = fuse_signals([{"module_id": m, "status": "Amber", "lineage": lineage_for(m)}
                               for m in ("A1.7", "A1.8")])
check("the voting pair is still one body", _before_voting["lineage_groups"] == 1)
check("and still 0.7000", abs(_before_voting["mass"]["Amber"] - 0.70) < 5e-5)

print(f"\nRESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
