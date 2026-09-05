#!/usr/bin/env python3
"""
Run 10: the corrected Monte Carlo and DSM synthetic contracts, version OG-SYNTH-0.3.

THIS SUITE CHANGES NO PRODUCTION CODE, NO PRODUCTION DATA AND NO PRODUCTION STATE. It reads
the v0.3 synthetic package, recomputes its stored ground truth from the raw stochastic
inputs and the raw dependency structure, exercises hand-calculated known-answer cases, and
proves the package validator fails on sixteen separate corruptions.

WHAT A CHECK IN THIS FILE IS.

1. AN EXPECTATION IS DERIVED FROM A STATED DEFINITION. The triangular expectation and the
   propagation rule are applied to the raw parameters. No expectation is copied from a
   generator and none is read back out of the file it is meant to test.

2. EVERY NEW CHECK IS PROVED ABLE TO FAIL. Section 7 perturbs expectations and asserts the
   comparison then fails. Section 6 corrupts bytes in a discarded copy of the package and
   asserts the validator names the failure.

3. DOMAINS ARE EXHAUSTED. All six projects, all sixty elements, all thirty-six risk events,
   all thirty-six project periods of DSM ground truth, all eight DSM known-answer cases and
   all eight Monte Carlo known-answer cases.

4. A DISAGREEMENT IS REPORTED AS A DISAGREEMENT rather than absorbed by a tolerance. The
   Monte Carlo tolerance is z times the standard error of the mean with z fixed in the
   package contract before any result was computed.

Passing anything here does not activate a module, make a module voting, validate a band, or
establish empirical validity of anything. Synthetic data is not evidence about the world.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run10_synthetic_v03.py
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

# ---------------------------------------------------------------------------------------------
# RUN 135C. RETIRED ARTEFACT. This script is kept for the record and is NOT executed.
#
# Ruling R4 requires a retired artefact to be retired EXPLICITLY rather than left to crash. Its
# subject is A1.1,A5.1,A5.4 -- 3 module ids removed from the registry at Run 96 or Run 97 and no module
# in service -- so there is nothing here for it to qualify. Before this guard it died with
# exit 124
# which prints no RESULT line and reads, in a scan of fleet output, exactly like a clean run.
#
# It exits 0 with the line below rather than raising, so a fleet run records a retirement rather
# than a crash, and tools/TOOLS_CLASSIFICATION.csv excludes it from qualification coverage.
# Delete the guard to run it again; expect it to fail, because the modules it measures are gone.
import sys as _sys135c
print("RETIRED: test_run10_synthetic_v03.py measures A1.1,A5.1,A5.4, removed at Run 96/97 (88e6ca0); excluded from qualification coverage "
      "by tools/TOOLS_CLASSIFICATION.csv")
_sys135c.exit(0)
# ---------------------------------------------------------------------------------------------

import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent
REPO = SERVER.parent
CODE_AUDIT = REPO / "code_audit"
sys.path.insert(0, str(SERVER))

from tests.synthetic_fixtures.importers import fixture_loader_v03 as FL  # noqa: E402
from tests.synthetic_fixtures.validators import recomputations_v03 as RC  # noqa: E402

PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  ok   {label}")
    else:
        FAILED += 1
        print(f"  FAIL {label}" + (f" :: {detail}" if detail else ""))


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    artifact_out(CODE_AUDIT).mkdir(parents=True, exist_ok=True)
    with (artifact_out(CODE_AUDIT / name)).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


PACKAGE_A = FL.PACKAGE_A
PACKAGE_ROOT = FL.PACKAGE_ROOT


# ============================================ Section 1: the package loads and is v0.3

print("== Section 1: the v0.3 package loads under the read-only importer ==")

check(PACKAGE_ROOT.name.endswith("v0.3"), "the importer points at the v0.3 programme",
      str(PACKAGE_ROOT))

for relpath, key in [
    (f"{PACKAGE_A}/cost_elements.csv", ["project_id", "cost_element_id"]),
    (f"{PACKAGE_A}/cost_risk_events.csv", ["project_id", "risk_event_id"]),
    (f"{PACKAGE_A}/cost_risk_component_ground_truth.csv", ["project_id", "component_id"]),
    (f"{PACKAGE_A}/cost_risk_ground_truth.csv", ["project_id"]),
    (f"{PACKAGE_A}/monte_carlo_convergence.csv",
     ["project_id", "monte_carlo_iterations"]),
    (f"{PACKAGE_A}/monte_carlo_known_answer_ground_truth.csv", ["case_id"]),
    (f"{PACKAGE_A}/dsm_ground_truth.csv", ["project_id", "period_id"]),
    (f"{PACKAGE_A}/dsm_known_answer_ground_truth.csv", ["case_id"]),
    (f"{PACKAGE_A}/dsm_known_answer_nodes.csv", ["case_id", "node_id"]),
]:
    try:
        table = FL.load_table(relpath, primary_key=key, expect_package=PACKAGE_A)
        ok = (table.provenance["programme_version"] == "OG-SYNTH-0.3"
              and table.provenance["data_origin"] == FL.SYNTHETIC_ORIGIN)
        check(ok, f"{Path(relpath).name} loads with v0.3 synthetic provenance",
              str(dict(table.provenance)))
    except FL.FixtureError as exc:
        check(False, f"{Path(relpath).name} loads with v0.3 synthetic provenance", str(exc))

for contract in ["monte_carlo_contract.json", "dsm_contract.json"]:
    doc = FL.load_json(f"{PACKAGE_A}/{contract}")
    check(doc["programme_version"] == "OG-SYNTH-0.3" and doc["not_for_empirical_validation"],
          f"{contract} declares v0.3 and refuses empirical status")


# ============================================ Section 2: permanent module identity

print("== Section 2: Monte Carlo EAC and Scenario Modeling resolve without an overlay ==")

check(FL.load_alias_overlay() == (), "the Run 9 overlay is switched off for v0.3")

resolved = FL.resolve_modules()
identity_rows: list[list] = []
for repo_id, synthetic_id, name in [
    ("A1.1", "1.1", "Monte Carlo EAC"),
    ("A5.4", "5.4", "Scenario Modeling"),
    ("A5.1", "5.1", "DSM Rework Propagation"),
]:
    row = resolved.get(repo_id)
    ok = (row is not None
          and row["synthetic_module_id"] == synthetic_id
          and row["module_name"] == name
          and row["source"] == "package_module_id_aliases")
    check(ok, f"{repo_id} resolves from the package alias table alone",
          str(dict(row)) if row else "absent")
    assets = FL.module_assets(repo_id) if row else ()
    check(bool(assets), f"{repo_id} resolves to assets that exist on disk", str(assets))
    identity_rows.append([repo_id, synthetic_id, name,
                          row["source"] if row else "MISSING", "|".join(assets)])

repo_ids = [r["repository_module_id"] for r in resolved.values()]
synthetic_ids = [r["synthetic_module_id"] for r in resolved.values()]
check(len(repo_ids) == len(set(repo_ids)), "repository module ids are unique")
check(len(synthetic_ids) == len(set(synthetic_ids)), "synthetic module ids are unique")
check(len(repo_ids) == len(synthetic_ids) == len(set(zip(repo_ids, synthetic_ids))),
      "the identity mapping is one to one in both directions")

# The repository module ids come from the registry, not from this file's opinion.
registry_source = (REPO / "assets" / "js" / "categories.js").read_text(encoding="utf-8")
registry_names = dict(
    re.findall(r"module_id: '([^']+)', name: '([^']+)'", registry_source)
)
# RUN 43, THE RETIREMENT. categories.js carries the population IN SERVICE, so a retired
# identifier has no row there to read a name from. The registry still resolves it -- retirement
# removes a module from service, not from the registry -- so for a retired id the name is taken
# from registry_index() and its ABSENCE from the client artifact is asserted as well. The branch
# derives from registry.is_retired(); nothing is listed here.
import sys as _sys                                                     # noqa: E402
_sys.path.insert(0, str(REPO / "server"))
from app.simulation import registry as _REG                            # noqa: E402
_reg_index = _REG.registry_index()
for repo_id, name in [("A1.1", "Monte Carlo EAC"), ("A5.4", "Scenario Modeling"),
                      ("A5.1", "DSM Rework Propagation")]:
    if _REG.is_retired(repo_id):
        registry_name = _reg_index[repo_id]["module_name"].replace("_", " ")
        check(bool(registry_name) and registry_name.startswith(name)
              and repo_id not in registry_names,
              f"{repo_id} is retired from service, so it is the REGISTRY's own identifier with "
              f"the alias name as its stem and it carries no row in the client taxonomy",
              f"registry says {registry_name!r}, alias says {name!r}, "
              f"in client taxonomy: {repo_id in registry_names}")
        continue
    registry_name = registry_names.get(repo_id, "")
    check(bool(registry_name) and registry_name.startswith(name),
          f"{repo_id} is the registry's own identifier and the alias name is the registry "
          f"name or its stem", f"registry says {registry_name!r}, alias says {name!r}")

write_csv("run10_module_identity.csv",
          ["repository_module_id", "synthetic_module_id", "module_name", "source", "assets"],
          identity_rows)


# ============================================ Section 3: Monte Carlo recomputation

print("== Section 3: Monte Carlo, recomputed from the declared stochastic inputs ==")

contract = FL.load_json(f"{PACKAGE_A}/monte_carlo_contract.json")
check(contract["cost_element_distribution"]["type"] == "TRIANGULAR"
      and contract["risk_event_model"]["impact_distribution"]["type"] == "TRIANGULAR"
      and contract["risk_event_model"]["occurrence"] == "BERNOULLI",
      "the governed distribution is declared in the package, not inferred by this suite")
check(contract["cost_element_distribution"]["expectation"] == "(low + most_likely + high) / 3",
      "the declared expectation is the triangular expectation")
Z = float(contract["acceptance_rule"]["z"])
check(abs(Z - 3.290526731491896) < 1e-9,
      "the acceptance rule uses the declared z for a two-sided alpha of 0.001", str(Z))

mc_rows, mc_bad = RC.recompute_monte_carlo()
check(not mc_bad, "every Monte Carlo quantity recomputes from its own inputs",
      "; ".join(mc_bad[:4]))
check(len(mc_rows) >= 6 * (10 + 6) + 6 * 8,
      "every cost element, every risk event and every project row was recomputed",
      str(len(mc_rows)))

gap_rows = RC.monte_carlo_pert_gap()
check(all(abs(r["error_against_triangular_pct"]) < abs(r["error_against_beta_pert_pct"])
          for r in gap_rows),
      "the simulated mean sits nearer the triangular expectation than the Beta-PERT one "
      "for every project")
check(all(abs(r["error_against_triangular_pct"]) < 0.1
          and abs(r["error_against_beta_pert_pct"]) > 0.5 for r in gap_rows),
      "the triangular residual is under a tenth of a percent while the Beta-PERT residual "
      "stays above half a percent, which is the Run 9 gap",
      str([(r["error_against_triangular_pct"], r["error_against_beta_pert_pct"])
           for r in gap_rows]))

convergence = FL.load_table(f"{PACKAGE_A}/monte_carlo_convergence.csv")
by_project: dict[str, list] = {}
for row in convergence:
    by_project.setdefault(row["project_id"], []).append(row)
convergence_rows: list[list] = []
contraction_failures: list[str] = []
for pid, rows in sorted(by_project.items()):
    rows.sort(key=lambda r: int(r["monte_carlo_iterations"]))
    counts = [int(r["monte_carlo_iterations"]) for r in rows]
    if counts != [1000, 5000, 20000]:
        contraction_failures.append(f"{pid}: sample counts {counts}")
        continue
    for row in rows:
        n = int(row["monte_carlo_iterations"])
        sd = float(row["simulated_sd_total_cost_usd"])
        se = sd / math.sqrt(n)
        error = abs(float(row["simulated_mean_total_cost_usd"])
                    - float(row["analytic_expected_total_cost_usd"]))
        if not RC._close(se, float(row["simulated_standard_error_usd"]), 1e-2):
            contraction_failures.append(f"{pid}/{n}: standard error does not recompute")
        if error > Z * se:
            contraction_failures.append(f"{pid}/{n}: {error / se:.2f} standard errors out")
        convergence_rows.append([pid, n, round(error, 4), round(se, 4),
                                 round(error / se, 4), round(error / se <= Z, 4)])
    first, last = rows[0], rows[-1]
    ratio = (float(first["simulated_standard_error_usd"])
             / float(last["simulated_standard_error_usd"]))
    # Twenty times the samples must shrink the standard error by about sqrt(20) = 4.47.
    if not 3.5 <= ratio <= 5.5:
        contraction_failures.append(f"{pid}: standard error ratio {ratio:.2f} is not near "
                                    "the root of the sample ratio")
check(not contraction_failures,
      "the standard error contracts as the root of the sample count at 1000, 5000 and 20000",
      "; ".join(contraction_failures[:4]))

write_csv("run10_monte_carlo_convergence.csv",
          ["project_id", "iterations", "absolute_error", "standard_error",
           "error_in_standard_errors", "within_acceptance"], convergence_rows)

write_csv("run10_monte_carlo_distribution_gap.csv",
          ["project_id", "triangular_analytic_mean", "beta_pert_analytic_mean",
           "simulated_mean", "error_against_triangular_pct", "error_against_beta_pert_pct"],
          [[r["project_id"], r["triangular_analytic_mean"], r["beta_pert_analytic_mean"],
            r["simulated_mean"], r["error_against_triangular_pct"],
            r["error_against_beta_pert_pct"]] for r in gap_rows])


# ============================================ Section 4: Monte Carlo known answers

print("== Section 4: Monte Carlo known-answer cases, hand-calculated ==")

# Hand calculations, written out. Each is (low + mode + high) / 3, times the probability
# for a discrete event, and each is derived here rather than read from the package.
HAND_MONTE_CARLO = {
    "MCKA-A": 250000.0,                                    # low = mode = high
    "MCKA-B": (100000.0 + 200000.0 + 600000.0) / 3,        # 300000
    "MCKA-D": 0.25 * (40000.0 + 80000.0 + 120000.0) / 3,   # 20000
    "MCKA-E": (100000.0 + 150000.0 + 200000.0) / 3
              + (50000.0 + 90000.0 + 100000.0) / 3
              + (10000.0 + 10000.0 + 40000.0) / 3,          # 250000
    "MCKA-F": 0.0,                                          # probability zero
    "MCKA-G": 1.0 * (40000.0 + 80000.0 + 120000.0) / 3,     # 80000, probability one
    "MCKA-H": (100000.0 + 200000.0 + 600000.0) / 3,
    "MCKA-I": (100000.0 + 200000.0 + 600000.0) / 3,
}

ka_truth = {r["case_id"]: r for r in
            FL.load_table(f"{PACKAGE_A}/monte_carlo_known_answer_ground_truth.csv",
                          primary_key=["case_id"])}
check(set(ka_truth) == set(HAND_MONTE_CARLO),
      "every hand-calculated case is present and no case is missing",
      str(sorted(set(ka_truth) ^ set(HAND_MONTE_CARLO))))

known_rows: list[list] = []
for case_id, hand in sorted(HAND_MONTE_CARLO.items()):
    row = ka_truth[case_id]
    stored_analytic = float(row["analytic_expected_total_usd"])
    check(abs(stored_analytic - hand) < 1e-6,
          f"{case_id}: the stored analytic expectation equals the hand calculation",
          f"{stored_analytic} vs {hand}")
    error = abs(float(row["simulated_mean_total_usd"]) - hand)
    se = float(row["simulated_standard_error_usd"])
    deterministic = str(row["deterministic_case"]).lower() == "true"
    if deterministic:
        check(error <= 1e-9, f"{case_id}: the deterministic case reproduces exactly", str(error))
    else:
        check(error <= Z * se, f"{case_id}: the simulated mean is inside z standard errors",
              f"{error:.4f} against {Z * se:.4f}")
    known_rows.append([case_id, hand, row["simulated_mean_total_usd"], round(se, 6),
                       round(error, 6), deterministic])

# A. deterministic collapse; F. probability zero; G. probability one.
check(float(ka_truth["MCKA-A"]["simulated_sd_total_usd"]) == 0.0
      and float(ka_truth["MCKA-A"]["simulated_mean_total_usd"]) == 250000.0,
      "deterministic collapse produces the deterministic amount with no spread")
check(float(ka_truth["MCKA-F"]["simulated_mean_total_usd"]) == 0.0,
      "a probability of zero contributes nothing at all")
check(abs(float(ka_truth["MCKA-G"]["simulated_mean_total_usd"]) - 80000.0)
      <= Z * float(ka_truth["MCKA-G"]["simulated_standard_error_usd"]),
      "a probability of one contributes the full expected impact")
# E. additivity.
check(abs(float(ka_truth["MCKA-E"]["analytic_expected_total_usd"])
          - (150000.0 + 80000.0 + 20000.0)) < 1e-6,
      "the expectation of a sum of independent components is the sum of the expectations")
# H and I. reproducibility, and a different seed.
check(ka_truth["MCKA-H"]["simulation_seed"] == ka_truth["MCKA-B"]["simulation_seed"]
      and ka_truth["MCKA-H"]["simulated_mean_total_usd"]
      == ka_truth["MCKA-B"]["simulated_mean_total_usd"],
      "the same seed and the same inputs reproduce the result exactly")
check(ka_truth["MCKA-I"]["simulation_seed"] != ka_truth["MCKA-B"]["simulation_seed"]
      and ka_truth["MCKA-I"]["simulated_mean_total_usd"]
      != ka_truth["MCKA-B"]["simulated_mean_total_usd"]
      and abs(float(ka_truth["MCKA-I"]["simulated_mean_total_usd"]) - 300000.0)
      <= Z * float(ka_truth["MCKA-I"]["simulated_standard_error_usd"]),
      "a different seed moves the draws and leaves the aggregate statistically consistent")

ka_rows, ka_bad = RC.monte_carlo_known_answers()
check(not ka_bad, "every known-answer case recomputes against its own components",
      "; ".join(ka_bad[:3]))


# J, K, L. Malformed inputs must be refused rather than answered.
def admissible_distribution(low: float, mode: float, high: float, kind: str) -> bool:
    return kind == "TRIANGULAR" and low <= mode <= high


def admissible_probability(value: float) -> bool:
    return 0.0 <= value <= 1.0


def admissible_iterations(value: int) -> bool:
    return int(value) > 0


refusals = [
    ("low above mode", not admissible_distribution(10.0, 5.0, 20.0, "TRIANGULAR")),
    ("mode above high", not admissible_distribution(1.0, 30.0, 20.0, "TRIANGULAR")),
    ("malformed distribution type", not admissible_distribution(1.0, 2.0, 3.0, "GAUSSIANISH")),
    ("probability below zero", not admissible_probability(-0.01)),
    ("probability above one", not admissible_probability(1.01)),
    ("zero iterations", not admissible_iterations(0)),
    ("negative iterations", not admissible_iterations(-5)),
]
for label, rejected in refusals:
    check(rejected, f"the domain rules reject {label}")
check(admissible_distribution(1.0, 2.0, 3.0, "TRIANGULAR")
      and admissible_probability(0.5) and admissible_iterations(5000),
      "the same domain rules accept a well-formed case, so they are not rejecting everything")

# M. The historical hundred-unit budget fallback must still be absent from production.
sim_source = (SERVER / "app" / "simulation" / "models_sim.py").read_text(encoding="utf-8")
assignments = [line for line in sim_source.splitlines()
               if line.strip().startswith("DEMO_BAC")]
check(not assignments,
      "the hundred-unit budget fallback is still absent from the production model; the only "
      "mention left is the comment recording its removal", str(assignments))
check("DEMO_BAC" in sim_source,
      "the removal is still documented in place, so a silent reintroduction would be visible")

write_csv("run10_monte_carlo_known_answers.csv",
          ["case_id", "hand_expectation", "simulated_mean", "standard_error",
           "absolute_error", "deterministic"], known_rows)


# ============================================ Section 5: DSM recomputation

print("== Section 5: DSM, recomputed from the raw dependency structure ==")

dsm_contract = FL.load_json(f"{PACKAGE_A}/dsm_contract.json")
check(dsm_contract["first_order"] == "first_order_impact_vector = matrix @ seed_impact_vector",
      "the first-order rule is declared in the package")
check("truncated" in dsm_contract["cycle_handling"].lower(),
      "the package states that propagation is truncated rather than iterated to convergence")

dsm_rows, dsm_bad = RC.recompute_dsm()
check(not dsm_bad, "every DSM field recomputes from nodes, edges and the seed",
      "; ".join(dsm_bad[:4]))
truth_rows = FL.load_table(f"{PACKAGE_A}/dsm_ground_truth.csv")
check(len(truth_rows) == 36, "all thirty-six project periods are present", str(len(truth_rows)))
check(len(dsm_rows) == 36 * 11, "every quantity of every row was recomputed", str(len(dsm_rows)))

# The Run 9 finding, restated against v0.3: a first-order formula must be compared with the
# first-order field, and the cumulative field must not be expected to equal it.
edges = FL.load_table(f"{PACKAGE_A}/dsm_edges.csv")
first_order_mismatches = 0
conflated_mismatches = 0
for row in truth_rows:
    seed = row["seed_node_id"]
    magnitude = float(row["seed_magnitude"])
    first = json.loads(row["first_order_impact_vector"])
    cumulative = json.loads(row["cumulative_state_vector"])
    for edge in edges:
        if edge["project_id"] != row["project_id"] or edge["source_node_id"] != seed:
            continue
        expected = magnitude * float(edge["dependency_strength"])
        if abs(first[edge["target_node_id"]] - expected) > 1e-6:
            first_order_mismatches += 1
        if abs(cumulative[edge["target_node_id"]] - expected) > 1e-6:
            conflated_mismatches += 1
check(first_order_mismatches == 0,
      "seed magnitude times edge strength equals the first-order field in every case",
      str(first_order_mismatches))
check(conflated_mismatches > 0,
      "the cumulative field is a different quantity, which is why the Run 9 comparison "
      "against it disagreed", f"{conflated_mismatches} of the same comparisons differ")

# Node counts: the two definitions must be genuinely different somewhere, or the split
# would be decoration.
count_differences = sum(
    1 for row in truth_rows
    if int(row["positive_state_node_count_including_seed"])
    != int(row["material_state_node_count_including_seed"])
    or int(row["positive_impacted_node_count_excluding_seed"])
    != int(row["positive_state_node_count_including_seed"])
)
check(count_differences > 0,
      "the positive and material counts, and the seed-inclusive and seed-exclusive counts, "
      "differ on real rows", str(count_differences))

dsm_ka_rows, dsm_ka_bad = RC.recompute_dsm_known_answers()
check(not dsm_ka_bad, "every DSM known-answer case recomputes",
      "; ".join(dsm_ka_bad[:3]))

# Hand calculations for the known-answer cases, written out rather than recomputed.
HAND_DSM = {
    # case: (first order total, propagated total, state total, positive excluding seed,
    #        positive including seed, material excluding seed, material including seed)
    "DSMKA-01": (0.5, 0.5, 1.5, 1, 2, 1, 2),
    "DSMKA-02": (1.5, 1.5, 3.5, 2, 3, 2, 3),
    "DSMKA-03": (0.4, 0.4, 1.4, 1, 2, 1, 2),
    "DSMKA-04": (0.5, 0.7, 1.7, 2, 3, 2, 3),
    "DSMKA-05": (0.75, 0.95, 1.95, 3, 4, 3, 4),
    "DSMKA-06": (0.0, 0.0, 1.0, 0, 1, 0, 1),
    "DSMKA-07": (0.11, 0.11, 1.11, 2, 3, 1, 2),
    "DSMKA-08": (0.5, 0.875, 1.875, 1, 2, 1, 2),
}
ka_dsm = {r["case_id"]: r for r in
          FL.load_table(f"{PACKAGE_A}/dsm_known_answer_ground_truth.csv",
                        primary_key=["case_id"])}
check(set(ka_dsm) == set(HAND_DSM), "every hand-calculated DSM case is present",
      str(sorted(set(ka_dsm) ^ set(HAND_DSM))))
dsm_known_rows: list[list] = []
for case_id, hand in sorted(HAND_DSM.items()):
    row = ka_dsm[case_id]
    stored = (
        float(row["total_first_order_impact"]),
        float(row["total_propagated_impact_excluding_seed"]),
        float(row["total_state_including_seed"]),
        int(row["positive_impacted_node_count_excluding_seed"]),
        int(row["positive_state_node_count_including_seed"]),
        int(row["material_impacted_node_count_excluding_seed"]),
        int(row["material_state_node_count_including_seed"]),
    )
    ok = all(abs(a - b) < 1e-9 for a, b in zip(hand, stored))
    check(ok, f"{case_id}: every stored quantity equals the hand calculation",
          f"hand {hand} stored {stored}")
    dsm_known_rows.append([case_id, row["case_description"], str(hand), str(stored), ok])

# The threshold-boundary case decides the definition: a value exactly on the threshold is
# not material, and a value above it is.
boundary = ka_dsm["DSMKA-07"]
boundary_vector = json.loads(boundary["propagated_impact_vector"])
check(abs(boundary_vector["N2"] - 0.05) < 1e-12 and boundary_vector["N3"] > 0.05
      and int(boundary["material_impacted_node_count_excluding_seed"]) == 1,
      "a node exactly on the materiality threshold is not counted as material")

# A malformed matrix must be refused rather than propagated.
malformed_refused = True
try:
    RC.propagate([[0.5, 0.0]], [1.0, 0.0], 1)
    malformed_refused = False
except Exception:
    malformed_refused = True
check(malformed_refused, "a matrix that is not square is refused rather than propagated")

write_csv("run10_dsm_known_answers.csv",
          ["case_id", "description", "hand_calculation", "stored", "agrees"], dsm_known_rows)
write_csv("run10_dsm_recomputation.csv",
          ["check", "key", "period", "quantity", "recomputed", "stored", "agrees"],
          [[r["check"], r["key"], r["period"], r["quantity"], r["recomputed"], r["stored"],
            r["agrees"]] for r in dsm_rows + dsm_ka_rows])
write_csv("run10_monte_carlo_recomputation.csv",
          ["check", "project_id", "key", "quantity", "recomputed", "stored", "agrees"],
          [[r["check"], r["project_id"], r["key"], r["quantity"], r["recomputed"], r["stored"],
            r["agrees"]] for r in mc_rows])


# ============================================ Section 6: validator fault injection

print("== Section 6: sixteen corruptions, each proved to make the validator fail ==")

VALIDATOR = PACKAGE_ROOT / "generators" / "validate_synthetic_programme_v0_3.py"


def run_validator(root: Path) -> tuple[int, set[str]]:
    """Run the package's own validator over a root and return its exit code and failures."""
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--root", str(root), "--write-report"],
        capture_output=True, text=True,
    )
    failed: set[str] = set()
    report = root / "validation_report.json"
    if report.exists():
        parsed = json.loads(report.read_text(encoding="utf-8"))
        failed = {c["check"] for c in parsed["checks"] if not c["passed"]}
    return result.returncode, failed


def edit_csv(path: Path, row_index: int, column: str, value: str) -> None:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = list(csv.DictReader(fh))
        fields = list(reader[0].keys())
    reader[row_index][column] = value
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(reader)


A = "package_A_project_structures"
INJECTIONS = [
    ("1 Monte Carlo wrong alias", "module_id_aliases.csv", 0, None, None),
    ("2 wrong distribution type", f"{A}/cost_elements.csv", 0,
     "cost_distribution_type", "BETA_PERT"),
    ("3 altered analytic mean", f"{A}/cost_risk_ground_truth.csv", 0,
     "analytic_expected_total_cost_usd", "1.0"),
    ("4 altered simulation mean", f"{A}/cost_risk_ground_truth.csv", 1,
     "simulated_mean_total_cost_usd", "1.0"),
    ("5 altered seed", f"{A}/cost_risk_ground_truth.csv", 2, "simulation_seed", "1"),
    ("6 invalid low mode high", f"{A}/cost_elements.csv", 1, "most_likely_cost_usd", "1.0"),
    ("7 invalid probability", f"{A}/cost_risk_events.csv", 0, "probability", "1.5"),
    ("8 iteration count changed without regenerating", f"{A}/cost_risk_ground_truth.csv", 3,
     "monte_carlo_iterations", "500"),
    ("9 biased mean beyond tolerance", f"{A}/cost_risk_ground_truth.csv", 4,
     "simulated_mean_total_cost_usd", None),
    ("10 wrong DSM seed", f"{A}/dsm_ground_truth.csv", 0, "seed_node_id", None),
    ("11 changed edge strength", f"{A}/dsm_edges.csv", 0, "dependency_strength", "0.9"),
    ("12 wrong first-order impact", f"{A}/dsm_ground_truth.csv", 1,
     "total_first_order_impact", "99.0"),
    ("13 wrong cumulative value", f"{A}/dsm_ground_truth.csv", 2,
     "total_state_including_seed", "99.0"),
    ("14 wrong positive node count", f"{A}/dsm_ground_truth.csv", 3,
     "positive_state_node_count_including_seed", "1"),
    ("15 wrong material count", f"{A}/dsm_ground_truth.csv", 4,
     "material_state_node_count_including_seed", "1"),
    ("16 threshold changed without regenerating", f"{A}/dsm_ground_truth.csv", 5,
     "materiality_threshold", "0.5"),
]

injection_rows: list[list] = []
uncaught: list[str] = []
with tempfile.TemporaryDirectory() as temporary:
    scratch = Path(temporary) / "package"
    shutil.copytree(PACKAGE_ROOT, scratch)
    clean_code, clean_failures = run_validator(scratch)
    check(clean_code == 0 and not clean_failures,
          "the untouched scratch copy validates clean, so a later failure is the injection",
          str(sorted(clean_failures)[:3]))

    for label, relpath, row_index, column, value in INJECTIONS:
        target = scratch / relpath
        before = target.read_bytes()
        if label.startswith("1 "):
            text = target.read_text(encoding="utf-8")
            mutated = text.replace(",A1.1,Monte Carlo EAC,", ",A9.9,Monte Carlo EAC,")
            target.write_text(mutated, encoding="utf-8")
        elif label.startswith("9 "):
            with target.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            biased = (float(rows[row_index]["analytic_expected_total_cost_usd"])
                      + 10 * float(rows[row_index]["simulated_standard_error_usd"]))
            edit_csv(target, row_index, "simulated_mean_total_cost_usd", f"{biased:.6f}")
        elif label.startswith("10 "):
            with target.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            other = next(r["seed_node_id"] for r in rows
                         if r["seed_node_id"] != rows[row_index]["seed_node_id"]
                         and r["project_id"] == rows[row_index]["project_id"])
            edit_csv(target, row_index, "seed_node_id", other)
        else:
            edit_csv(target, row_index, column, value)
        after = target.read_bytes()
        changed = before != after
        code, failures = run_validator(scratch)
        named = sorted(failures - clean_failures)
        caught = changed and code != 0 and bool(named)
        if not caught:
            uncaught.append(label)
        injection_rows.append([label, relpath, "yes" if changed else "NO",
                               code, "; ".join(named[:3]) or "none"])
        target.write_bytes(before)
        restored_code, restored_failures = run_validator(scratch)
        if restored_code != 0 or restored_failures:
            uncaught.append(f"{label}: not restored")
        check(caught, f"injection {label} alters bytes and makes the validator fail by name",
              "; ".join(named[:2]) or f"exit {code}, no new failing check")

check(not uncaught, f"all {len(INJECTIONS)} injections were caught and restored",
      "; ".join(uncaught))
check(not (PACKAGE_ROOT / "validation_report.json").read_text(encoding="utf-8")
      .count('"passed": false'),
      "the staged package's own validation report records no failure")

write_csv("run10_validator_fault_injection.csv",
          ["injection", "file", "bytes_changed", "validator_exit", "named_failures"],
          injection_rows)


# ============================================ Section 7: every new check can fail

print("== Section 7: the new checks are proved able to fail ==")

check(RC.triangular_mean(0, 1, 4) == 5 / 3
      and RC.triangular_mean(0, 1, 4) != RC.beta_pert_mean(0, 1, 4),
      "the triangular and Beta-PERT expectations are different functions, and the oracle "
      "uses the triangular one")
check(abs(RC.beta_pert_mean(100000, 200000, 600000) - 250000.0) < 1e-9
      and abs(RC.triangular_mean(100000, 200000, 600000) - 300000.0) < 1e-9,
      "on the known-answer parameters the two families differ by fifty thousand, so a "
      "check that used the wrong one could not pass by accident")

sample = mc_rows[0]
check(RC._close(float(sample["recomputed"]), float(sample["stored"]), 1e-2)
      and not RC._close(float(sample["recomputed"]) + 1000.0, float(sample["stored"]), 1e-2),
      "a perturbed Monte Carlo recomputation no longer equals the stored ground truth")

first_order, propagated, cumulative = RC.propagate([[0.0, 0.0], [0.5, 0.0]], [1.0, 0.0], 1)
check(first_order == [0.0, 0.5] and cumulative == [1.0, 0.5],
      "the propagation function reproduces a hand case")
perturbed_first, _p, _c = RC.propagate([[0.0, 0.0], [0.9, 0.0]], [1.0, 0.0], 1)
check(perturbed_first != first_order,
      "changing an edge strength changes the recomputed first-order result, so the DSM "
      "comparison is sensitive to the structure it reads")

for case_id, hand in [("MCKA-B", 300000.0), ("MCKA-G", 80000.0)]:
    stored = float(ka_truth[case_id]["analytic_expected_total_usd"])
    check(abs(stored - hand) < 1e-6 and abs(stored - (hand + 1.0)) > 1e-6,
          f"{case_id}: perturbing the hand expectation would fail the comparison")

for case_id in ["DSMKA-05", "DSMKA-08"]:
    stored = float(ka_dsm[case_id]["total_propagated_impact_excluding_seed"])
    hand = HAND_DSM[case_id][1]
    check(abs(stored - hand) < 1e-9 and abs(stored - (hand + 0.1)) > 1e-9,
          f"{case_id}: perturbing the hand propagated total would fail the comparison")


# ============================================ Section 8: no operational effect

print("== Section 8: production code, production state and the participant surface ==")


def tree_digest(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()
                       and "__pycache__" not in p.parts):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


from app.simulation import registry as REG  # noqa: E402

app_digest = tree_digest(SERVER / "app")
assets_digest = tree_digest(REPO / "assets")

check(len(REG.CORE_VOTING_MODULES) == 2,
      "the voting set is still the two modules Run 4 left voting",
      "|".join(sorted(REG.CORE_VOTING_MODULES)))
check(len(REG.DISABLED_CONCEPT_ONLY) == 8, "the disabled concept-only set still holds eight")
check("A1.1" not in REG.CORE_VOTING_MODULES,
      "correcting the Monte Carlo fixtures did not make the Monte Carlo module voting")

suite_source = Path(__file__).read_text(encoding="utf-8")
db_tokens = ("session" + ".add", "commit" + "()", "Session" + "Local", "sql" + "alchemy")
check(not any(token in suite_source for token in db_tokens),
      "this suite opens no session and writes nothing to any database")
loader_source = FL.SOURCE_PATH.read_text(encoding="utf-8")
check(not any(token in loader_source for token in ('open("w"', "write_text", "write_bytes",
                                                   "mkdir")),
      "the importer contains no write call at all")
check(not [p for p in (PACKAGE_ROOT).rglob("*") if p.name.endswith(".db")],
      "the synthetic package contains no database file")

write_csv("run10_no_operational_effect.csv", ["surface", "value", "note"], [
    ["server/app tree digest", app_digest, "recorded in this run"],
    ["assets tree digest", assets_digest, "recorded in this run"],
    ["voting set", "|".join(sorted(REG.CORE_VOTING_MODULES)), "unchanged"],
    ["disabled concept-only set", "|".join(sorted(REG.DISABLED_CONCEPT_ONLY)), "unchanged"],
    ["production algorithms", "untouched",
     "this run changed no file under server/app or assets"],
    ["migrations applied", "none",
     "this suite applies no migration and opens no production database"],
    ["synthetic data in operational records", "none",
     "the importer is read-only and writes nothing"],
])


print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
