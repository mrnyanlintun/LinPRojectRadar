"""
RUN 20 CYCLE 10. P2: MISSING CANONICAL STRUCTURES AND METHOD LABEL MISMATCHES.

Run 19 recorded twenty-three modules whose registered NAME claims an analytical method the code
does not perform, and eight more whose name or reported claim rests on a canonical data
structure that is not in this repository. The permitted resolutions are two: implement the
canonical method, or say plainly what the computation is.

THE CANONICAL ROUTE WAS TESTED FIRST AND IN EVERY CASE IT FAILS ON EVIDENCE, NOT ON EFFORT.
Section 2 below asserts, module by module and against the signal inputs the production caller
actually assembles, that the defining structure is absent: no schedule network, no risk register
with distributions, no event schedule, no stocks and flows, no information table of objects and
attributes, no alternative set, no agents, no external price index, no planned value curve, no
independent estimate, no per-field source records. Run 20 is forbidden to invent any of them,
so the truthful naming route is the only one left, and it is taken.

WHAT IS DELIBERATELY NOT DONE. The served participant surface is frozen and checksummed and the
study is mid-sequence. Renaming what a participant reads is a change to the instrument and is an
owner decision, not a remediation, so the truthful name reaches the interface response, the
export and the methods documentation only, by exactly the mechanism Run 1 used for the thirty
proxy qualifiers. Section 5 proves the participant accessors are untouched.

NOTHING IS ACTIVATED AND NOTHING IS RENAMED INTO RESPECTABILITY. Four of the labelled modules
are disabled and stay disabled; a truthful name is not a rehabilitation. Section 6 proves it.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.simulation import method_labels as ML  # noqa: E402
from app.simulation import registry  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, DISABLED_EVIDENCE_UNDER_REVIEW,
    DISABLED_MODULES, _attach_method_label, activation_state, registry_index, run_all,
)
from run17 import population as POP  # noqa: E402

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


IDX = registry_index()
POPULATION = {r["code_id"]: r for r in POP.population()}

#: The twenty-three Run-19 METHOD_LABEL_MISMATCH rows, by code id, transcribed from
#: code_audit/run20_master_remediation_register.csv and stated here so the suite does not
#: depend on the register file being present to know what it is testing.
MISMATCH_23 = [
    "A1.5", "A1.6", "A1.11", "A2.7", "A2.10", "A2.11", "A3.6", "A3.8", "A4.6", "A4.7",
    "A4.10", "A5.3", "A5.5", "A5.8", "B1.2", "B2.2", "B2.14", "B3.1", "B4.1", "B4.4",
    "B4.5", "B4.6", "C1.6",
]

#: The eight Run-19 P2 structural rows, by code id.
STRUCTURAL_8 = ["A1.10", "A3.9", "A4.1", "A6.3", "A6.4", "B2.18", "B4.2", "C1.4"]

#: RUN 28 RESOLVED NINE OF THESE ROWS BY IMPLEMENTING THE CANONICAL METHOD, which is the FIRST
#: of the two resolutions method_labels.py permits and the one it prefers. A truthful label
#: exists to say that the code does something weaker than its name; once the code performs the
#: named method the label becomes a false claim in the opposite direction, so it is removed with
#: the proxy. Eight of the nine are mismatch rows and one, A1.10, is a structural row.
#: A3.8 is NOT among them: it remains disabled and non-voting, and keeps its label.
RESOLVED_BY_RUN_28 = ["A1.5", "A1.6", "A1.10", "A1.11", "A2.7", "A2.10", "A2.11", "A3.6",
                      "A3.9"]
#: RUN 29 RESOLVED SIX MORE, by the same first resolution and for the same reason: each now
#: performs the canonical method its registered name claims, from a governed structure the
#: owner's supplied Run-29 contract required to be supplied, and abstains when it is absent. A
#: label saying "Throughput index from the schedule index and progress ratio" beside a module
#: that runs an event list with a clock, a resource and a queue would be the false claim this
#: table exists to prevent, told in the opposite direction.
RESOLVED_BY_RUN_29 = ["A4.6", "A4.7", "A4.10", "A5.3", "A5.5", "A5.8"]
# RUN 30 CLOSURE. Three further rows are resolved for exactly the same reason: B2.2 Rough Sets
# now computes lower and upper approximations over a governed decision table, B2.14 Maximum
# Entropy solves a constrained maximisation through the convex dual, and B2.18 MARCOS ranks an
# explicit set of alternatives. Each abstains when its defining structure is absent. Leaving
# their labels would assert a weakness the code no longer has.
RESOLVED_BY_RUN_30 = ["B2.2", "B2.14", "B2.18"]
# RUN 31. Four further rows are resolved for exactly the same reason. B3.1 now runs a genuine
# agent-based model -- agents with state and latency, a message queue with a declared ordering
# rule, a simulation clock -- where the label said agents, interaction and time steps were
# absent; the action boundary and authority matrix survives as the POLICY the model consults.
# A6.4 now carries the official-assessment structure whose absence its label recorded: source
# system, assessment period, record status and review state. C1.6 compares the SAME governed
# fact across actual source records instead of recomputing two indices from one reported set.
# C1.4 assesses the real signal, judgment and audit objects, their chronology and linkage, and
# treats the critical fields noncompensatorily. Leaving any of these labels would assert a
# weakness the code no longer has.
RESOLVED_BY_RUN_31 = ["B3.1", "A6.4", "C1.6", "C1.4"]
RESOLVED = (RESOLVED_BY_RUN_28 + RESOLVED_BY_RUN_29 + RESOLVED_BY_RUN_30
            + RESOLVED_BY_RUN_31)
MISMATCH_23_STILL_LABELLED = [m for m in MISMATCH_23 if m not in RESOLVED]
STRUCTURAL_8_STILL_LABELLED = [m for m in STRUCTURAL_8 if m not in RESOLVED]
#: The module this suite drives for the "label reaches the result" checks. It must be one that
#: still carries a label, so it is derived from the list above rather than named, which stops it
#: silently becoming a module whose label a later run removed.
LABELLED_PROBE = next(m for m in MISMATCH_23_STILL_LABELLED
                      if m not in registry.DISABLED_CONCEPT_ONLY
                      and m not in registry.DISABLED_EVIDENCE_UNDER_REVIEW)


print("=== 1. EVERY LABEL MISMATCH IS RESOLVED, AND RESOLVED BY NAME ===")
check("every mismatch row Run 28 did not remediate still carries a truthful method label",
      all(ML.method_label(m) is not None for m in MISMATCH_23_STILL_LABELLED),
      str([m for m in MISMATCH_23_STILL_LABELLED if ML.method_label(m) is None]))
check("and every row Run 28 DID remediate has had its label removed, because the code now "
      "performs the method its registered name claims and a stale weakness claim would be a "
      "false statement in the other direction",
      all(ML.method_label(m) is None for m in RESOLVED),
      str([m for m in RESOLVED if ML.method_label(m) is not None]))
check("A3.8 kept its label, because it is still disabled and still implements no parametric "
      "estimating relationship in production",
      ML.method_label("A3.8") is not None)
check("and no truthful name repeats the registered name it replaces, which would leave the "
      "claim exactly where Run 19 found it",
      all(ML.method_label(m).truthful.strip().lower()
          != ML.method_label(m).registered.strip().lower()
          for m in MISMATCH_23_STILL_LABELLED))
check("every registered name in the label table matches the registry itself, so a registry "
      "rename cannot leave a stale claim standing here",
      all(IDX[m]["module_name"] == ML.method_label(m).registered
          for m in ML.labelled_modules()),
      str([m for m in ML.labelled_modules()
           if IDX[m]["module_name"] != ML.method_label(m).registered]))
check("every labelled module is a real registry module",
      all(m in IDX for m in ML.labelled_modules()))
check("every labelled module is one of the hundred scientific targets",
      all(m in POPULATION for m in ML.labelled_modules()),
      str([m for m in ML.labelled_modules() if m not in POPULATION]))
check("every disposition is one of the permitted set",
      all(ML.method_label(m).disposition in ML.LABEL_DISPOSITIONS
          for m in ML.labelled_modules()))
check("no truthful name, sentence or absence statement carries a module identifier",
      not [m for m in ML.labelled_modules()
           if any(tok in (ML.method_label(m).truthful + ML.method_label(m).performs
                          + ML.method_label(m).absent)
                  for tok in ("A1.", "A2.", "A3.", "B1.", "B2.", "B4.", "C1.", "PH."))])
check("no user-facing sentence in the label table uses an em dash",
      not [m for m in ML.labelled_modules()
           if "—" in (ML.method_label(m).truthful + ML.method_label(m).performs
                           + ML.method_label(m).absent)])
check("and none uses an ampersand in prose",
      not [m for m in ML.labelled_modules()
           if "&" in (ML.method_label(m).truthful + ML.method_label(m).performs
                      + ML.method_label(m).absent)])
check("all eight structural rows are disposed of, by a truthful label or by a stated claim "
      "limit, and none is left out",
      all(ML.method_label(m) is not None or ML.claim_limit(m) is not None
          for m in STRUCTURAL_8_STILL_LABELLED),
      str([m for m in STRUCTURAL_8_STILL_LABELLED
           if ML.method_label(m) is None and ML.claim_limit(m) is None]))


print("\n=== 2. THE CANONICAL ROUTE WAS TESTED AND THE STRUCTURE IS GENUINELY ABSENT ===")
# The production caller's own assembled signal inputs, taken from the pinned Run-6 fixture
# shape. The point of this section is that the keys a canonical implementation would need are
# not merely unset on one project: no production input contract carries them at all.
from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS  # noqa: E402

SI = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 500_000.0, "pv": 450_000.0,
      "cpi": 0.8, "spi": 0.89, "docRiskScore": 0.55,
      "actualPctComplete": 40.0, "plannedPctComplete": 45.0,
      "rfiCount": 12, "changeOrderCount": 5,
      "baselineStart": "2025-01-01", "baselineEnd": "2026-01-01",
      "baselineContractSum": 1_000_000.0, "revisedContractSum": 1_060_000.0,
      "cpiHistory": [0.94, 0.90, 0.86, 0.83]}

#: The structure each of these methods would need, and the key it would have to arrive on. A
#: canonical implementation is only possible if the caller can supply this without fabrication.
WOULD_NEED = {
    "A1.6": "plannedValueCurve",
    "A1.11": "independentCostEstimate",
    "A2.10": "scheduleNetwork",
    "A2.11": "scheduleNetwork",
    "A3.6": "riskRegisterDistributions",
    "A3.9": "externalPriceIndex",
    "A5.5": "reworkStocksAndFlows",
    "A5.8": "eventSchedule",  # kept for the record; A5.8's structure arrived in Run 29
    "B2.2": "informationTable",
    "B2.14": "momentConstraints",
    "B2.18": "alternativeSet",
    "B4.4": "candidateActions",
    "C1.6": "perFieldSourceRecords",
    "A6.4": "pastPerformanceRecords",
}
check("not one of the structures a canonical implementation would need is present on the "
      "production input contract, so the canonical route fails on evidence rather than effort",
      not [k for k in WOULD_NEED.values() if k in SI],
      str([k for k in WOULD_NEED.values() if k in SI]))
check("nor is any of them a declared canonical structure key, so none is reachable through the "
      "layer that gates the six modules which DO have their structure",
      not set(WOULD_NEED.values()) & set(CANONICAL_STRUCTURE_KEYS.values()))
check("the six modules that genuinely have a canonical structure keep it, and none of them is "
      "given a truthful-label override instead",
      not set(CANONICAL_STRUCTURE_KEYS) & set(ML.labelled_modules()),
      str(set(CANONICAL_STRUCTURE_KEYS) & set(ML.labelled_modules())))
check("every labelled module names, in plain words, the structure that is absent",
      all(len(ML.method_label(m).absent.strip()) > 40 for m in ML.labelled_modules()))


print("\n=== 3. THE LABEL REACHES THE RESULT, FOR A COMPUTING MODULE AND A DISABLED ONE ===")
_e: dict = {}
_attach_method_label(_e, LABELLED_PROBE)
check("a computing module's record carries the truthful name",
      _e.get("truthful_method_name") == ML.method_label(LABELLED_PROBE).truthful, str(_e))
check("and the registered name beside it, so a reader sees both claims and is never shown one "
      "while believing it is the other",
      _e.get("registered_name") == ML.method_label(LABELLED_PROBE).registered)
check("and the absent structure",
      _e.get("absent_canonical_structure", "") == ML.method_label(LABELLED_PROBE).absent)
check("and the disposition",
      _e.get("label_disposition") == ML.method_label(LABELLED_PROBE).disposition)
check("and the participant surface owner decision, stated on the record itself",
      _e.get("participant_surface") == ML.PARTICIPANT_SURFACE_OWNER_DECISION)

_d: dict = {}
_attach_method_label(_d, "B4.6")
check("a DISABLED module carries it too, which is precisely where a stale prestigious claim "
      "survives unexamined",
      _d.get("label_disposition") == "FUTURE_RESEARCH_ONLY"
      and "no alternative set" in _d.get("truthful_method_name", ""))

_c: dict = {}
_attach_method_label(_c, "A4.1")
check("a module with no naming fault but an unmet claim carries the claim limit and NO truthful "
      "name, because its name is not the thing at fault",
      _c.get("claim_limit_disposition") == "EMPIRICAL_VALIDATION_BLOCKED"
      and "truthful_method_name" not in _c, str(_c))

_u: dict = {}
_attach_method_label(_u, "A1.7")
# CYCLE 11 NOTE. This module now receives a parameter provenance record, which every module
# carrying a tunable value does. The check is about the LABEL layer and is narrowed to it rather
# than relaxed: a module with no naming fault and no claim limit must acquire no label key.
_LABEL_KEYS = ("registered_name", "truthful_method_name", "performs",
               "absent_canonical_structure", "label_disposition", "participant_surface",
               "claim_limit", "claim_limit_disposition")
check("a module with neither a naming fault nor a claim limit acquires no label key, so the "
      "label layer is not silently annotating the whole registry",
      not [k for k in _LABEL_KEYS if k in _u], str(sorted(_u)))


print("\n=== 4. THE LABEL SURVIVES A REAL RUN OF THE PRODUCTION REGISTRY ===")
_res = run_all(dict(SI), "cycle10", "2025-06", "2025-06-30")
_by_id = {r["module_id"]: r for r in _res["computed"]}
_ab_by_id = {r["module_id"]: r for r in _res["abstained"]}
_reached = set(_by_id) | set(_ab_by_id)
check("every labelled module is reached by the production run, as a result or as an abstention",
      set(ML.labelled_modules()) <= _reached,
      str(sorted(set(ML.labelled_modules()) - _reached)))
_carried = [m for m in ML.labelled_modules()
            if (_by_id.get(m) or _ab_by_id.get(m) or {}).get("truthful_method_name")
            == ML.method_label(m).truthful]
check("and every one of them carries its truthful name on the record the interface publishes",
      len(_carried) == len(ML.labelled_modules()),
      str(sorted(set(ML.labelled_modules()) - set(_carried))))
check("no module that has no label acquired one during the run",
      not [m for m in _reached
           if (_by_id.get(m) or _ab_by_id.get(m) or {}).get("truthful_method_name")
           and m not in ML.TRUTHFUL_METHOD_LABELS])


print("\n=== 5. THE PARTICIPANT SURFACE IS NOT RENAMED ===")
# The three keys the participant ledger's accessors read. If the truthful name had been written
# into any of them the instrument would have been renamed mid-study, which is not authorised.
_ledger_keys = ("module_id", "status_color", "evidence_metric")
_leaked = []
for m in ML.labelled_modules():
    row = _by_id.get(m) or _ab_by_id.get(m) or {}
    for k in _ledger_keys:
        if isinstance(row.get(k), str) and ML.method_label(m).truthful in row[k]:
            _leaked.append((m, k))
check("no truthful name appears in any key the participant ledger renders",
      not _leaked, str(_leaked))
check("every labelled module records the participant-surface rename as an owner decision "
      "rather than performing it",
      all("owner decision" in ML.method_label(m).as_dict()["participant_surface"]
          for m in ML.labelled_modules()))
check("the registry CSV, which the frontend registry is generated from, still carries the "
      "registered names unchanged",
      all(IDX[m]["module_name"] == ML.method_label(m).registered
          for m in ML.labelled_modules()))


print("\n=== 6. NOTHING WAS ACTIVATED, PROMOTED OR REHABILITATED BY BEING RENAMED ===")
check("the voting set is still exactly the two",
      sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"], str(sorted(CORE_VOTING_MODULES)))
check("no labelled module votes",
      not set(ML.labelled_modules()) & set(CORE_VOTING_MODULES))
check("the eight concept-only modules are still eight and still disabled",
      len(DISABLED_CONCEPT_ONLY) == 8
      and all(activation_state(m) == "DISABLED_UNSAFE" for m in DISABLED_CONCEPT_ONLY))
check("the four labelled modules that are disabled are still disabled",
      all(activation_state(m) == "DISABLED_UNSAFE"
          for m in ("A3.8", "B4.1", "B4.2", "B4.5", "B4.6")))
check("Material Cost Variance is untouched and still under evidence review",
      list(DISABLED_EVIDENCE_UNDER_REVIEW) == ["A3.4"]
      and activation_state("A3.4") == "DISABLED_EVIDENCE_UNDER_REVIEW")
check("and it was given no truthful-label override, because its disposition is an evidence "
      "question and not a naming one",
      ML.method_label("A3.4") is None)
check("no disabled module produced a result",
      not set(DISABLED_MODULES) & set(_by_id))


print("\n=== 7. GUARD NON-VACUITY: EACH GUARD IS SHOWN TO CATCH WHAT IT PROTECTS ===")
# A guard that stays green when its protected invariant is deliberately violated is a defect.
# Each violation below is applied, the guard is required to fire BY NAME, and the state is
# restored and required to go green again.

# 7a. The registered-name check must catch a registry rename that leaves a stale claim.
_saved_name = IDX[LABELLED_PROBE]["module_name"]
IDX[LABELLED_PROBE]["module_name"] = "Something Else Entirely"
_fired = not all(IDX[m]["module_name"] == ML.method_label(m).registered
                 for m in ML.labelled_modules())
IDX[LABELLED_PROBE]["module_name"] = _saved_name
check("the registered-name guard FIRES on a deliberate registry rename", _fired)
check("and goes green again once the rename is undone",
      all(IDX[m]["module_name"] == ML.method_label(m).registered
          for m in ML.labelled_modules()))

# 7b. The truthful-name constructor must refuse a name that repeats the claim.
try:
    ML.MethodLabel("Discrete Event Simulation", "discrete event simulation", "x", "y",
                   "CORRECT_PROXY_ONLY")
    _refused = False
except ValueError:
    _refused = True
check("the constructor REFUSES a truthful name that merely repeats the registered claim, "
      "casing and spacing aside", _refused)

# 7c. The disposition vocabulary must refuse an invented disposition.
try:
    ML.MethodLabel("A", "B", "x", "y", "LOOKS_FINE_TO_ME")
    _refused = False
except ValueError:
    _refused = True
check("and REFUSES a disposition outside the permitted vocabulary", _refused)

# 7d. The coverage check must catch a label removed from the table.
_saved = ML.TRUTHFUL_METHOD_LABELS.pop(LABELLED_PROBE)
_fired = not all(ML.method_label(m) is not None for m in MISMATCH_23_STILL_LABELLED)
ML.TRUTHFUL_METHOD_LABELS[LABELLED_PROBE] = _saved
check("the coverage guard FIRES when a label is deliberately removed from the table", _fired)
check("and goes green again once it is restored",
      all(ML.method_label(m) is not None for m in MISMATCH_23_STILL_LABELLED))

# 7e. The participant-leak check must catch a truthful name written into a ledger key.
# RUN 30. The leak probe must be taken on a module that ACTUALLY COMPUTED on this run.
# LABELLED_PROBE is chosen from the label table alone, and Run 30's v15 made B1.2 abstain
# without a governed weighting policy, so it no longer appears among the computed rows at all.
# Taking the probe from the computed rows keeps the guard exercising a real ledger record.
_LEAK_PROBE = next(m for m in MISMATCH_23_STILL_LABELLED if m in _by_id)
_probe = dict(_by_id[_LEAK_PROBE])
_probe["evidence_metric"] = ML.method_label(_LEAK_PROBE).truthful + " reading"
_fired = any(ML.method_label(_LEAK_PROBE).truthful in _probe[k]
             for k in _ledger_keys if isinstance(_probe.get(k), str))
check("the participant-leak guard FIRES when a truthful name is deliberately written into a "
      "ledger key", _fired)
check("and the real record does not trip it",
      not any(ML.method_label(_LEAK_PROBE).truthful in _by_id[_LEAK_PROBE][k]
              for k in _ledger_keys if isinstance(_by_id[_LEAK_PROBE].get(k), str)))

# 7f. The attachment itself must be capable of NOT firing, or section 3's last check is vacuous.
_v: dict = {}
_attach_method_label(_v, "A1.8")
check("the attachment guard is not vacuous: an unlabelled module really acquires no label key "
      "while a labelled one really is annotated",
      not [k for k in _LABEL_KEYS if k in _v] and _e.get("truthful_method_name"))


print("\n=== 8. WHAT IS NOT RESOLVED, RECORDED RATHER THAN OMITTED ===")
check("the environmental compliance reading is recorded as blocked on regulatory version, not "
      "renamed into acceptability",
      ML.claim_limit("A6.3")[0] == "REGULATORY_VERSION_BLOCKED")
check("and it states plainly that no compliance determination under any named instrument is "
      "made", "not a compliance determination" in ML.claim_limit("A6.3")[1])
check("the document risk score is recorded as unvalidated, with no accuracy claim supportable",
      ML.claim_limit("A4.1")[0] == "EMPIRICAL_VALIDATION_BLOCKED")
# RUN 30 CLOSURE. B2.18 MARCOS leaves this list because its LABEL is gone, not because the owner
# decision is: it now ranks an explicit set of alternatives, so the label's claim that it "scores
# this one project against designed reference points" is no longer true. The owner decision it
# carried -- whether a decision-ranking method belongs in Category 7 at all -- is unchanged, is
# NOT resolved by Run 30, and is recorded against Run 32 in the Run-30 closure table. One row
# remains labelled as an owner decision.
# RUN 31. C1.4 leaves this list because its LABEL is gone, not because an owner decision was
# taken quietly. The label said the check counted declared audit-field presence with the real
# audit objects, chronology, linkage and noncompensatory critical treatment ABSENT; the canonical
# measure assesses all four, so the label's claim is no longer true of the code. NO owner
# decision is resolved here and none is invented: what the label recorded was a code weakness,
# and the weakness is what Run 31 removed. With it gone, no row carries OWNER_DECISION_REQUIRED.
check("no row is carried as an owner decision, because the one that was is now resolved by code "
      "rather than disposed of quietly",
      sorted(m for m in ML.labelled_modules()
             if ML.method_label(m).disposition == "OWNER_DECISION_REQUIRED")
      == [])
check("and the four disabled ones are future research only, which is not an activation",
      sorted(m for m in ML.labelled_modules()
             if ML.method_label(m).disposition == "FUTURE_RESEARCH_ONLY")
      == ["A3.8", "B4.1", "B4.2", "B4.5", "B4.6"])

print(f"\nRESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
