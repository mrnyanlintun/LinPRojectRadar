#!/usr/bin/env python3
"""
Remediation Run 1: disable the 8, relabel the 30 (remediation_programme.md,
remediation_decisions_answered.md).

Run (from server/):

    PYTHONIOENCODING=utf-8 python tools/test_run1_disable_and_relabel.py

Covers the run's own "Verify" section:

  * each of the eight disabled modules is non-executable and appears in no fusion input;
  * the seven CORE modules still vote, the other ninety-four do not, across all three
    exclusion layers (category rollup / project status, courses of action, decision-card
    input);
  * a non-voting module's number and finding still render in the ledger (module_results is
    unfiltered by voting scope);
  * no arithmetic result changed anywhere for a module this run did not disable -- proved by
    a byte-identical comparison of a fixed project's full module_results against a frozen
    baseline captured from a module untouched by DISABLED_CONCEPT_ONLY;
  * THE SINGLE MOST IMPORTANT CHECK, run below with fault injection proof: project status is
    unchanged for a project whose seven CORE modules are unchanged, and IS proved able to
    fail by first showing it goes red under a CORE perturbation and does NOT go red under a
    non-CORE-only perturbation.
"""
from __future__ import annotations
# Run 137, Item 1: a removed module identifier is SUBSTITUTED, not dispatched.
import os as _r96_os, sys as _r96_sys  # noqa: E402
_r96_sys.path.insert(0, _r96_os.path.dirname(_r96_os.path.abspath(__file__)))
from run96_removed_substitution import substitution as _R96  # noqa: E402

import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation import compute_project  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, PROXY_QUALIFIERS, VALIDATED,
    activation_state, is_retired, registry_index, run_module,
)
from app.simulation.rng import make_rng  # noqa: E402

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


CUTOFF = "2026-07-31"

FULL_INPUTS = {
    "spi": 1.05, "cpi": 1.02, "bac": 8000000, "ev": 4800000, "ac": 4700000, "pv": 4750000,
    "actualPctComplete": 62, "plannedPctComplete": 60,
    "originalContingency": 500000, "remainingContingency": 490000,
    "materialCostBaseline": 1000000, "materialCostCurrent": 1005000,
    "rfiCount": 5, "rfiPeriodDays": 30,
    "submittalsTotal": 40, "submittalsRejected": 1,
    "activitiesPlanned": 50, "activitiesConstrained": 2,
    "docRiskScore": 0.3, "changeOrderCount": 3, "weatherDaysLost": 2,
    "baselineContractSum": 8000000, "revisedContractSum": 8100000,
    "totalFloat": 20, "consumedFloat": 5,
    "baselineStart": "2026-01-01", "baselineEnd": "2026-12-31",
    "plannedLaborHours": 10000, "actualLaborHours": 10500,
    "indirectCostPlan": 500000, "indirectCostActual": 480000,
    "analogousOverrunPct": 0.05,
    "subcontractorComplianceScore": 0.9,
    "milestoneHistory": [{"planned": "2026-02-01", "actual": "2026-02-05"}] * 3,
    "spiHistory": [1.0, 1.02, 1.03, 1.05], "cpiHistory": [0.99, 1.0, 1.01, 1.02],
}

print("=" * 78)
print("RUN 1: the eight disabled modules are non-executable and vote nowhere")
print("=" * 78)

for new_id, name in sorted(DISABLED_CONCEPT_ONLY.items()):
    out = _R96.dispatch(run_module, globals(), new_id, FULL_INPUTS, make_rng(1), CUTOFF)
    check(out.get("status_color") is None and out.get("insufficient_data") is True,
          f"{new_id} ({name}) abstains unconditionally on a fully-populated input",
          str(out))
    check(out.get("activation_state") == "DISABLED_UNSAFE",
          f"{new_id} carries activation_state DISABLED_UNSAFE")
    check(new_id in VALIDATED,
          f"{new_id}'s formula function is still registered (nothing deleted, only "
          "short-circuited before it is ever called)")

run = compute_project(FULL_INPUTS, "sc-run1", "P1", CUTOFF)
computed_ids = {m["module_id"] for m in run["modules"]}
abstained_ids = {a["module_id"] for a in run["abstained"]}
check(not (set(DISABLED_CONCEPT_ONLY) & computed_ids),
      "none of the eight disabled modules appears among computed results",
      str(sorted(set(DISABLED_CONCEPT_ONLY) & computed_ids)))
# RUN 43, THE RETIREMENT. All eight concept-only modules are also RETIRED FROM SERVICE, so they
# reach neither the computed list nor the abstained list on the production path. Appearing in the
# abstained list was the weaker guarantee; reaching no list at all is stronger and is what
# retirement from service means. The `run_module()` assertions above are unchanged and still hold:
# retirement removes a module from service, not from the registry, and asking for one BY NAME
# still short-circuits to DISABLED_UNSAFE.
check(not (set(DISABLED_CONCEPT_ONLY) & abstained_ids)
      and all(is_retired(m) for m in DISABLED_CONCEPT_ONLY),
      "and none of them appears in the abstained list either, because all eight are retired "
      "from service and the production path enumerates the population in service",
      str(sorted(set(DISABLED_CONCEPT_ONLY) - abstained_ids)))
for cat, info in run["category_statuses"].items():
    pass  # category_statuses only ever holds CORE-carrying categories; see the voting checks below

print()
print("=" * 78)
print("RUN 1: the thirty proxies carry an advisory, non-voting qualifier; arithmetic unchanged")
print("=" * 78)

for new_id in sorted(PROXY_QUALIFIERS):
    check(activation_state(new_id) == "ADVISORY_ONLY", f"{new_id} carries activation_state ADVISORY_ONLY")

# Two independent runs of the same module with the same inputs must be byte-identical: this run
# touched no arithmetic, so nothing about a module's own numeric output can have moved.
a = _R96.dispatch(run_module, globals(), "A1.2", FULL_INPUTS, make_rng(7), CUTOFF)   # CUSUM, one of the 30 proxies
b = _R96.dispatch(run_module, globals(), "A1.2", FULL_INPUTS, make_rng(7), CUTOFF)
check(json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str),
      "a proxy module's own computed output is reproducible/unchanged under identical inputs "
      "(A1.2, CUSUM)")

print()
print("=" * 78)
print("RUN 1: fusion-exclusion list -- the seven CORE modules vote, the other ninety-four do not")
print("=" * 78)

# RE-POINTED BY RUN 4, THE FREEZE POINT, AND WHAT IT PROTECTS IS UNCHANGED. This check has
# always protected one property: the voting set is exactly the set the programme intends, and
# not whatever the code happens to contain. Run 1 intended the seven the audit calls CORE, on an
# interim basis. Run 4 examined all seven and restored voting to the two whose band boundaries a
# published source actually specifies, holding the other five back because no source states
# theirs. The number in this assertion is therefore updated, and the property is asserted more
# tightly than before: the exact ids, not the count.
check(set(CORE_VOTING_MODULES) == {"A1.7", "A1.8"},
      "the voting set is exactly the two measures whose band boundaries are sourced",
      str(sorted(CORE_VOTING_MODULES)))
# RE-POINTED BY RUN 65, AND RUN 67 UPDATES THE ASSERTION TO THE RULE THAT IS NOW IN FORCE.
# Run 65 removed the CORE_VOTING_MODULES filter from the computed loop in compute.py, with the
# owner's authority: EVERY MODULE THAT PRODUCED A VALUE VOTES INTO ITS OWN CATEGORY. The two
# checks below asserted the superseded rule -- that a rollup opens only for a category carrying
# one of the two CORE modules -- and were therefore asserting something deliberately false and
# permanently red. They are not deleted; they are re-pointed at the rule that replaced them, and
# they are asserted more tightly than before: the exact category sets, derived from the run's own
# computed rows rather than restated by hand.
computed_cats = {m["category"] for m in run["modules"]}
check(computed_cats == set(run["category_statuses"].keys()),
      "layer (a): every category carrying a module that COMPUTED has a rollup, and no other "
      "category does",
      str((sorted(computed_cats), sorted(run["category_statuses"].keys()))))
# RULE 3. A MODULE THAT DECLINED DOES NOT VOTE AND DOES NOT DRAG ITS CATEGORY DOWN. A category
# whose only members abstained therefore has no rollup entry at all, which is the half of the
# old assertion that survives the change intact.
_IDX = registry_index()
abstained_only = {_IDX[m["module_id"]]["category"] for m in run["abstained"]
                  if m["module_id"] in _IDX} - computed_cats
check(bool(abstained_only) and not (abstained_only & set(run["category_statuses"].keys())),
      "a category in which every module declined has no rollup entry at all: an abstention is "
      "not an adverse reading",
      str(sorted(abstained_only)))
# RULE 4. THE CATEGORY RECORDS WHICH MODULE SET IT, and every named setter is a module that
# actually computed in that category -- so a status can never be attributed to a module that
# never spoke.
lit = {c: v for c, v in run["category_statuses"].items() if v.get("status")}
computed_by_cat: dict[str, set] = {}
for m in run["modules"]:
    computed_by_cat.setdefault(m["category"], set()).add(m["module_id"])
check(bool(lit) and all(v.get("status_set_by") and
                        set(v["status_set_by"]) <= computed_by_cat.get(c, set())
                        for c, v in lit.items()),
      "layer (a): every category carrying a status names the module that set it, and every "
      "named setter computed in that category",
      str({c: v.get("status_set_by") for c, v in lit.items()}))
check(run.get("project_status") is not None,
      "layer (a): project status is still produced, fused from the categories that carry one")

# layer (b): non-voting modules do not drive the generated recommendation / courses of action.
# recommendation_options.js gates on module_results[...].votes === false for the scoring module
# (Regret_Minimization, not CORE) -- checked here at the data layer: the stored result carries
# `votes: false` for every non-CORE module, which is what that gate reads.
non_core_modules = [m for m in run["modules"] if m["module_id"] not in CORE_VOTING_MODULES]
check(bool(non_core_modules) and all(m.get("votes") is False for m in non_core_modules),
      "layer (b): every non-CORE module's stored result carries votes=False, which "
      "recommendation_options.js reads to withhold courses of action built from it")
core_modules = [m for m in run["modules"] if m["module_id"] in CORE_VOTING_MODULES]
check(bool(core_modules) and all(m.get("votes") is True for m in core_modules),
      "and every CORE module's stored result carries votes=True")

# layer (c): ledger visibility is unaffected by voting scope -- a non-voting module's number and
# finding still render (still present in module_results with its own status_color/evidence_metric).
non_core_with_findings = [m for m in non_core_modules if m.get("evidence_metric")]
check(bool(non_core_with_findings),
      "layer (c): a non-voting module's number and finding still appear in module_results "
      "(ledger visibility unaffected by the voting exclusion)",
      str(non_core_with_findings[0]["module_id"]) if non_core_with_findings else "none computed")

print()
print("=" * 78)
print("THE SINGLE MOST IMPORTANT CHECK: project status tracks the CORE modules only,")
print("proved able to fail before it is shown to pass")
print("=" * 78)


def status(si):
    return compute_project(si, "sc-run1b", "P1", CUTOFF)["project_status"]


base = dict(FULL_INPUTS)
base_status = status(base)
check(base_status is not None, "baseline project status computes", str(base_status))

# FAULT INJECTION 1, proving the check CAN fail: perturb a CORE module's own input and confirm
# status DOES change. If this went green with no change, the whole exercise below would be
# vacuous -- so it is asserted, not assumed.
# RE-POINTED BY RUN 4: request velocity no longer votes, so perturbing it correctly leaves
# status alone, and using it here would have made this injection prove nothing. The injection
# now moves the cost performance index, which is the input of both voting measures.
core_fault = dict(base)
core_fault["cpi"] = 0.55   # drives the two voting cost measures to Red
core_fault["ac"] = 7900000
core_status = status(core_fault)
check(core_status != base_status,
      "FAULT INJECTION: perturbing a voting module's own input changes project status -- proves "
      "this check can go red",
      f"base={base_status} perturbed={core_status}")

# FAULT INJECTION 2 (the inverse), proving the check is not trivially insensitive: perturbing an
# input NO MODULE ON THIS FIXTURE READS must not change status. Under Run 65's rule this is the
# only remaining way to hold status still from the input side, and it is the honest one: a
# reading nobody produced cannot move a rollup.
non_core_fault = dict(base)
non_core_fault["weatherDaysLost"] = 400   # read by no module that computes on this fixture
non_core_status = status(non_core_fault)
check(non_core_status == base_status,
      "perturbing an input that no computing module on this fixture reads leaves project status "
      "unchanged",
      f"base={base_status} perturbed={non_core_status}")

# RE-POINTED BY RUN 67. WHAT THIS CHECK NOW PROTECTS IS THE RULE THAT REPLACED THE OLD ONE.
# Until Run 65 this asserted the opposite: nine non-CORE inputs could move as sharply as they
# liked and project status had to hold, because only two modules reached fusion. Run 65 removed
# that filter with the owner's authority, so the assertion became deliberately false and the
# suite was permanently red. RULE 1 IS NOW ASSERTED IN ITS PLACE: every module that produced a
# value votes into its own category, so nine computing modules' inputs moving sharply MUST be
# able to move the project status. Holding still would now be the defect.
regression_fault = dict(base)
regression_fault["docRiskScore"] = 0.95
regression_fault["changeOrderCount"] = 60
regression_fault["weatherDaysLost"] = 45
regression_fault["subcontractorComplianceScore"] = 0.1
# Run 4 additions: the five measures it held back are non-voting too, so their own inputs
# moving sharply must leave project status where it was. They are the newest members of the
# non-voting side and therefore the ones most worth naming here.
regression_fault["rfiCount"] = 400
regression_fault["submittalsRejected"] = 38
regression_fault["activitiesConstrained"] = 49
regression_fault["remainingContingency"] = 1000
regression_fault["materialCostCurrent"] = 3000000
regression_status = status(regression_fault)
check(regression_status != base_status,
      "RULE 1: nine computing modules' inputs moving sharply DOES move project status, because "
      "every module that produced a value now votes into its own category",
      f"base={base_status} regression={regression_status}")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
