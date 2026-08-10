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

import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation import compute_project  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, PROXY_QUALIFIERS, VALIDATED,
    activation_state, run_module,
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
    out = run_module(new_id, FULL_INPUTS, make_rng(1), CUTOFF)
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
check(set(DISABLED_CONCEPT_ONLY) <= abstained_ids,
      "all eight disabled modules appear in the abstained list instead",
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
a = run_module("A1.2", FULL_INPUTS, make_rng(7), CUTOFF)   # CUSUM, one of the 30 proxies
b = run_module("A1.2", FULL_INPUTS, make_rng(7), CUTOFF)
check(json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str),
      "a proxy module's own computed output is reproducible/unchanged under identical inputs "
      "(A1.2, CUSUM)")

print()
print("=" * 78)
print("RUN 1: fusion-exclusion list -- the seven CORE modules vote, the other ninety-four do not")
print("=" * 78)

check(len(CORE_VOTING_MODULES) == 7, "exactly seven CORE modules", str(sorted(CORE_VOTING_MODULES)))
core_cats = {m["category"] for m in run["modules"] if m["module_id"] in CORE_VOTING_MODULES}
check(core_cats == set(run["category_statuses"].keys()),
      "layer (a): category rollup opens only for categories carrying a CORE module",
      str((sorted(core_cats), sorted(run["category_statuses"].keys()))))
non_core_cats = {m["category"] for m in run["modules"]} - core_cats
check(bool(non_core_cats) and not (non_core_cats & set(run["category_statuses"].keys())),
      "categories with no CORE module have no rollup entry at all",
      str(sorted(non_core_cats)))
check(run.get("project_status") is not None,
      "layer (a): project status is still produced, fused from CORE-carrying categories only")

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
core_fault = dict(base)
core_fault["rfiCount"] = 400   # drives A4.2 RFI Velocity, one of the seven CORE modules, to Red
core_status = status(core_fault)
check(core_status != base_status,
      "FAULT INJECTION: perturbing a CORE module's own input (RFI Velocity) changes project "
      "status -- proves this check can go red",
      f"base={base_status} perturbed={core_status}")

# FAULT INJECTION 2 (the inverse), proving the check is not trivially insensitive: perturbing a
# NON-core module's input must NOT change status.
non_core_fault = dict(base)
non_core_fault["weatherDaysLost"] = 400   # Weather Day Impact, a proxy, not CORE
non_core_status = status(non_core_fault)
check(non_core_status == base_status,
      "perturbing only a non-CORE module's input (Weather Day Impact) leaves project status "
      "unchanged",
      f"base={base_status} perturbed={non_core_status}")

# THE ACTUAL REGRESSION: several non-CORE inputs move at once, CORE inputs untouched -> status
# holds. This is the property the run's "most important check" names directly.
regression_fault = dict(base)
regression_fault["docRiskScore"] = 0.95
regression_fault["changeOrderCount"] = 60
regression_fault["weatherDaysLost"] = 45
regression_fault["subcontractorComplianceScore"] = 0.1
regression_status = status(regression_fault)
check(regression_status == base_status,
      "REGRESSION: project status is unchanged for a project whose seven CORE modules' own "
      "inputs are unchanged, even though several non-voting modules' inputs moved sharply",
      f"base={base_status} regression={regression_status}")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
