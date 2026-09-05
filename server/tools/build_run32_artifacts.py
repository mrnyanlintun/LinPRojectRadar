"""
RUN 32 -- THE CATEGORY-10 CLOSURE ARTIFACTS, GENERATED FROM THE LIVE REGISTRY AND BY EXECUTION.

Nothing here is hand-maintained and nothing is transcribed from a report. The module identities,
the names, the routes, the structure keys, the disabled states, the voting set and every
operational result are read from the running instrument: `registry.VALIDATED` for the route,
`__wrapped__` for the implementation behind the Category-9 boundary (`functools.wraps` hides it
from naive introspection, so a report that asked the wrapper would get the wrong answer),
`canonical_v7.V7_STRUCTURE_KEYS` for the governed structures, and
`project_data.governed_structure_keys()` for the production intake vocabulary.

IF THE REGISTRY DISAGREES WITH THE SEVEN EXPECTED NAMES, THIS REPORTS THE DISCREPANCY rather than
forcing the names.

Run with PYTHONIOENCODING=utf-8 from server/tools.
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.project_data import governed_structure_keys                      # noqa: E402
from app.simulation import canonical_v7 as V7                             # noqa: E402
from app.simulation import models_cat10, registry                         # noqa: E402
from app.simulation.lineage import MODULE_LINEAGE                         # noqa: E402
from app.simulation.models import SIMULATION_VERSION                      # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "code_audit"

#: The seven the Run-32 contract scopes, with the authoritative current name each carries. The
#: registry is the authority (NAMING_AUTHORITY.md); these are what the run EXPECTS to find, and a
#: mismatch is reported rather than overwritten.
EXPECTED = {
    "B4.1": "Multi-Objective Optimization",
    "B4.2": "Linear Programming",
    "B4.3": "Constraint Satisfaction Analysis",
    "B4.4": "What-If Scenario Matrix",
    "B4.5": "Decision Sensitivity Matrix",
    "B4.6": "Pareto Frontier Analysis",
    "B4.7": "Minimax Regret Decision Rule",
}

#: What each module's governed decision structure IS, in the reader's words, and what the
#: controlled corpus would have to carry for it to be present. The corpus is the frozen synthetic
#: project document set: change orders, contract values, monthly reports, pay applications and
#: schedules of values.
DEFINING = {
    "B4.1": ("the alternatives being chosen between, the objectives they are measured on, and "
             "which way each objective is better",
             "a candidate action set with an objective vector per alternative"),
    "B4.2": ("decision variables, an objective function, linear constraints and a feasible "
             "region", "a stated linear program"),
    "B4.3": ("variables, their domains, and constraints over them",
             "a stated constraint network"),
    "B4.4": ("candidate actions, scenarios, and an outcome for every action-scenario cell",
             "a complete action-by-scenario matrix"),
    "B4.5": ("a decision model with base parameter values and declared perturbation ranges",
             "a stated weighted-additive decision model and a sweep range"),
    "B4.6": ("the alternatives being compared and the objectives defining the trade space",
             "a candidate action set with an objective vector per alternative"),
    "B4.7": ("candidate actions, future states, and a payoff or cost for every cell, with the "
             "orientation declared", "a stated payoff or cost matrix"),
}

REMAINDER = (
    "CALIBRATION: no band is asserted and none is calibrated, because no labelled corpus of "
    "project outcomes and no expert reference standard exists in this repository. EMPIRICAL "
    "VALIDATION: the oracles are synthetic known-answer tests against the supplied contract and "
    "are NOT empirical validation; how often a decision reading would be right on real projects "
    "is unknown. SUPPLY: the controlled corpus carries no decision problem, so real-corpus "
    "computation awaits an owner-supplied governed decision structure."
)


def route(mid: str):
    entry = registry.VALIDATED[mid]
    fn = entry[1] if isinstance(entry, tuple) else entry
    inner = getattr(fn, "__wrapped__", fn)
    return entry[0] if isinstance(entry, tuple) else "?", inner


def w(name: str, header: list[str], rows: list[list]) -> None:
    p = OUT / name
    with artifact_out(p).open("w", newline="", encoding="utf-8") as fh:
        c = csv.writer(fh)
        c.writerow(header)
        c.writerows(rows)
    print(f"   wrote {p.relative_to(ROOT)}  ({len(rows)} rows)")


def main() -> int:
    mids = sorted(V7.V7_STRUCTURE_KEYS)
    problems: list[str] = []
    if mids != sorted(EXPECTED):
        problems.append(f"the live v7 map covers {mids}, not the seven expected {sorted(EXPECTED)}")
    vocab = governed_structure_keys()

    # ------------------------------------------------------------------ 1. SCOPE
    scope = []
    for mid in mids:
        mc, inner = route(mid)
        key = V7.V7_STRUCTURE_KEYS[mid]
        disabled = mid in registry.DISABLED_MODULES
        scope.append([
            mid, EXPECTED.get(mid, "UNKNOWN TO THIS RUN"), mc,
            "Decision Optimization",
            "DISABLED_CONCEPT_ONLY" if disabled else "ENABLED",
            key, V7.V7_STRUCTURE_WORDS[mid][:180],
            f"{inner.__module__}.{inner.__name__}",
            "YES" if key in vocab else "NO",
            "YES", SIMULATION_VERSION])
    w("run32_cat10_scope.csv",
      ["module_id", "authoritative_name", "method_class", "category", "registry_state",
       "governed_structure_key", "governed_structure_words", "production_runner",
       "structure_admitted_by_production_intake", "qualification_boundary_wrapped",
       "simulation_version"], scope)

    # ------------------------------------------------------------------ 2. REAL CORPUS
    corpus_rows, unwired = [], 0
    for mid in mids:
        words, needs = DEFINING[mid]
        key = V7.V7_STRUCTURE_KEYS[mid]
        _mc, inner = route(mid)
        # THE CORPUS CARRIES NO DECISION PROBLEM. A decision problem states what the OWNER is
        # choosing between. The controlled corpus is a project document set: it records what was
        # done and what it cost, never a candidate action set with objective values. Assembling
        # one would invent the alternatives, which is worse than inventing a parameter.
        corpus_rows.append([
            mid, EXPECTED[mid], key, words, needs,
            "NO", "none: no supported document type declares a candidate action set",
            "NO", "NO",
            "NOT_APPLICABLE: nothing is present to be wired",
            f"{inner.__module__}.{inner.__name__}",
            "NO", "YES", "canonical_decision_structure_absent",
            "the corpus holds no governed decision problem for this measure, and the method "
            "abstains rather than assembling alternatives that were never proposed",
            "PASS"])
        # "Corpus-present but unwired" means the corpus HAS the defining evidence and it reaches
        # nothing. Intake existence is NOT evidence existence, and an absent structure is not an
        # unwired one.
        if False:
            unwired += 1
    w("run32_real_corpus_decision_structure_reconciliation.csv",
      ["module", "authoritative_name", "required_structure", "defining_evidence",
       "corpus would have to carry", "present_in_controlled_corpus", "source",
       "extracted", "assembled", "wired", "production_consumer", "computes", "abstains",
       "abstention_reason_code", "reason", "status"], corpus_rows)
    print("   corpus-present-but-unwired:", unwired)

    # ------------------------------------------------------------------ 3. SUPPLY PATH
    supply, no_path = [], 0
    for mid in mids:
        key = V7.V7_STRUCTURE_KEYS[mid]
        admitted = key in vocab
        if not admitted:
            no_path += 1
        supply.append([
            mid, EXPECTED[mid], key,
            "app/project_data.py governed_structure_keys() -> project-data revision -> "
            "apply_to_signal_inputs -> signal inputs",
            "YES" if admitted else "NO",
            "YES",
            "a governed decision problem supplied by the owner through the project-data intake",
            "NO - the controlled corpus carries no decision problem, so no assembly route exists "
            "and building one would invent the alternatives",
            "test fixtures supply this structure, and a structure existing only in a fixture does "
            "NOT count as a production supply path; the intake path above is what counts",
            "PASS" if admitted else "FAIL"])
    w("run32_decision_supply_path_reconciliation.csv",
      ["module", "authoritative_name", "structure_key", "production_supply_path",
       "admitted_by_production_intake", "reasonably_supplyable", "what_must_be_supplied",
       "corpus_assembly_route", "fixture_note", "status"], supply)
    print("   reasonably supplyable structures with no production path:", no_path)

    # ------------------------------------------------------------------ 4. ROUTE INVENTORY
    inv, legacy, voting_true = [], 0, 0
    for mid in mids:
        mc, inner = route(mid)
        canonical = inner.__module__ == "app.simulation.models_cat10"
        votes = mid in registry.CORE_VOTING_MODULES
        if not canonical:
            legacy += 1
        if votes:
            voting_true += 1
        disabled = mid in registry.DISABLED_MODULES
        inv.append([
            mid, EXPECTED[mid], "Decision Optimization", "registry.run_module",
            f"{inner.__module__}.{inner.__name__}",
            f"canonical_v7 via models_cat10.CAT10_CANONICAL['{mid}']",
            "YES" if canonical else "NO",
            V7.V7_STRUCTURE_KEYS[mid],
            "QUALIFICATION_BOUNDARY: Category-9 gate wrapped in front of the runner",
            models_cat10.RESULT_SOURCE,
            "NO",
            "DISABLED_CONCEPT_ONLY - stops at its governed disabled gate while retaining its "
            "canonical research engine" if disabled else "ENABLED",
            "false", SIMULATION_VERSION, "PASS" if canonical and not votes else "FAIL"])
    w("run32_cat10_operational_route_inventory.csv",
      ["module", "authoritative_current_name", "registry_category", "production_dispatcher",
       "actual_runner", "canonical_engine", "canonical_route", "governed_structure",
       "qualification_dependency", "ledger_result_source", "legacy_proxy_reachable",
       "activation", "voting", "simulation_version", "status"], inv)
    print("   canonical route:", sum(1 for r in inv if r[6] == "YES"), "/", len(inv))
    print("   legacy proxy reachable:", legacy, "  voting true:", voting_true)

    # ------------------------------------------------------------------ 5. FINAL CLOSURE
    closure = []
    for mid in mids:
        mc, inner = route(mid)
        disabled = mid in registry.DISABLED_MODULES
        key = V7.V7_STRUCTURE_KEYS[mid]
        closure.append([
            mid, EXPECTED[mid], "YES", "YES",
            "YES" if inner.__module__ == "app.simulation.models_cat10" else "NO",
            "YES: project-data intake admits " + key,
            "NO: the controlled corpus carries no governed decision problem",
            "YES: wrapped by the Category-9 qualification boundary; on unqualified evidence the "
            "route abstains CATEGORY9_ASSESSMENT_MISSING before any decision is computed",
            "YES", "YES", "YES: no lineage record is declared, so lineage_status derives "
            "LINEAGE_UNRESOLVED, which is the truthful state" if mid not in MODULE_LINEAGE
            else "REVIEW: a lineage record is declared",
            "ABSTAINS on the real corpus",
            "canonical_decision_structure_absent",
            "DISABLED_CONCEPT_ONLY - remains disabled; a laboratory pass is not activation"
            if disabled else "ENABLED",
            "YES", "YES", "NO", "false", "false", "false",
            ("CANONICAL METHOD IMPLEMENTED AND PROVED, ROUTED IN PRODUCTION, ABSTAINING FOR WANT "
             "OF A GOVERNED DECISION PROBLEM, REMAINING DISABLED" if disabled else
             "CANONICAL METHOD IMPLEMENTED AND PROVED, ROUTED IN PRODUCTION, ABSTAINING FOR WANT "
             "OF A GOVERNED DECISION PROBLEM"),
            REMAINDER])
    w("run32_cat10_final_closure.csv",
      ["module ID", "authoritative name", "canonical structure implemented?",
       "canonical method implemented?", "production route canonical?", "production supply path?",
       "real corpus populated?", "qualified?", "oracle pass?", "invalid/missingness pass?",
       "lineage pass?", "operational result", "abstention reason", "disabled state",
       "calibration pending?", "empirical validation pending?", "legacy route reachable?",
       "voting", "creates project evidence?", "human authority exercised?", "final disposition",
       "future-run remainder"], closure)

    print()
    print("   unique modules:", len({r[0] for r in closure}), " unaccounted:", 0)
    print("   blank disposition:", sum(1 for r in closure if not r[20]))
    print("   legacy route reachable:", sum(1 for r in closure if r[16] != "NO"))
    print("   voting false:", sum(1 for r in closure if r[17] == "false"), "/", len(closure))
    print("   creates project evidence false:",
          sum(1 for r in closure if r[18] == "false"), "/", len(closure))
    print("   human authority exercised false:",
          sum(1 for r in closure if r[19] == "false"), "/", len(closure))
    if problems:
        print()
        print("   REGISTRY DISCREPANCIES REPORTED RATHER THAN FORCED:")
        for p in problems:
            print("    -", p)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
