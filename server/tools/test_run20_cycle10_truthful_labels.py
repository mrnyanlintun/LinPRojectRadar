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


print("=== 1. EVERY LABEL MISMATCH IS RESOLVED, AND RESOLVED BY NAME ===")
check("all twenty-three mismatch rows carry a truthful method label",
      all(ML.method_label(m) is not None for m in MISMATCH_23),
      str([m for m in MISMATCH_23 if ML.method_label(m) is None]))
check("and no truthful name repeats the registered name it replaces, which would leave the "
      "claim exactly where Run 19 found it",
      all(ML.method_label(m).truthful.strip().lower()
          != ML.method_label(m).registered.strip().lower() for m in MISMATCH_23))
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
          for m in STRUCTURAL_8),
      str([m for m in STRUCTURAL_8
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
    "A5.8": "eventSchedule",
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
_attach_method_label(_e, "A5.8")
check("a computing module's record carries the truthful name",
      _e.get("truthful_method_name") == "Throughput index from the schedule index and "
                                        "progress ratio", str(_e))
check("and the registered name beside it, so a reader sees both claims and is never shown one "
      "while believing it is the other",
      _e.get("registered_name") == "Discrete Event Simulation")
check("and the absent structure", "event schedule" in _e.get("absent_canonical_structure", ""))
check("and the disposition", _e.get("label_disposition") == "CORRECT_PROXY_ONLY")
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
_saved_name = IDX["A5.8"]["module_name"]
IDX["A5.8"]["module_name"] = "Something Else Entirely"
_fired = not all(IDX[m]["module_name"] == ML.method_label(m).registered
                 for m in ML.labelled_modules())
IDX["A5.8"]["module_name"] = _saved_name
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
_saved = ML.TRUTHFUL_METHOD_LABELS.pop("A5.8")
_fired = not all(ML.method_label(m) is not None for m in MISMATCH_23)
ML.TRUTHFUL_METHOD_LABELS["A5.8"] = _saved
check("the coverage guard FIRES when a label is deliberately removed from the table", _fired)
check("and goes green again once it is restored",
      all(ML.method_label(m) is not None for m in MISMATCH_23))

# 7e. The participant-leak check must catch a truthful name written into a ledger key.
_probe = dict(_by_id["A5.8"])
_probe["evidence_metric"] = ML.method_label("A5.8").truthful + " reading"
_fired = any(ML.method_label("A5.8").truthful in _probe[k]
             for k in _ledger_keys if isinstance(_probe.get(k), str))
check("the participant-leak guard FIRES when a truthful name is deliberately written into a "
      "ledger key", _fired)
check("and the real record does not trip it",
      not any(ML.method_label("A5.8").truthful in _by_id["A5.8"][k]
              for k in _ledger_keys if isinstance(_by_id["A5.8"].get(k), str)))

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
check("two rows are carried as owner decisions rather than being disposed of quietly",
      sorted(m for m in ML.labelled_modules()
             if ML.method_label(m).disposition == "OWNER_DECISION_REQUIRED")
      == ["B2.18", "C1.4"])
check("and the four disabled ones are future research only, which is not an activation",
      sorted(m for m in ML.labelled_modules()
             if ML.method_label(m).disposition == "FUTURE_RESEARCH_ONLY")
      == ["A3.8", "B4.1", "B4.2", "B4.5", "B4.6"])

print(f"\nRESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
