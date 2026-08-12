#!/usr/bin/env python3
"""
Build the Opus Gubernatio Synthetic Programme v0.3 from the staged v0.2 tree.

v0.3 changes exactly two ground-truth families and the module identity tables. Everything
else is carried across from v0.2 unchanged apart from version stamps and re-hashed
provenance.

1. Monte Carlo EAC (cost risk). v0.2 stored four aggregate numbers with no declaration of
   the distribution that produced them. The v0.1 generator, which produced those numbers and
   which v0.2 carried across untouched, samples TRIANGULAR marginals for cost elements
   (scipy.stats.triang.ppf through a Gaussian copula) and TRIANGULAR risk impacts
   (scipy.stats.triang.rvs) gated by an independent Bernoulli occurrence draw. It does not
   sample Beta-PERT anywhere in the cost-risk model. v0.3 declares that contract in the data,
   stores every stochastic input beside every output, and stores the analytic expectation and
   the sampling error against which the simulated mean is judged.

2. DSM rework propagation. v0.2 stored `total_propagated_rework` and `impacted_node_count`
   without saying which of several distinct quantities each was. v0.3 separates seed, first
   order, multi-step, cumulative state, positive counts and material counts into named fields
   with an explicit materiality threshold and an explicit statement of whether the seed node
   is inside each count.

3. Module identity. Monte Carlo EAC and Scenario Modeling become permanent rows in the
   authoritative alias table and asset map, so no overlay is needed to reach their assets.

Synthetic data verifies implementation only. It is not empirical evidence and nothing built
here validates a module, a band or a threshold.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm, triang

PROGRAMME_VERSION = "OG-SYNTH-0.3"
GENERATOR_VERSION = "build_opus_synthetic_programme_v0_3.py@0.3"
SEED = 20260812
DATA_ORIGIN = "SYNTHETIC_RESEARCH_FIXTURE"

# Statistical acceptance rule for every Monte Carlo mean check in this package.
# z = 3.291 is the two-sided normal quantile for alpha = 0.001. 0.001 is 0.05 Bonferroni
# corrected across fifty checks, which comfortably covers the six project means, the
# eighteen convergence points and the known-answer cases in this package. It is fixed here
# before any result is computed and it is not adjusted to admit a result.
ACCEPTANCE_Z = 3.290526731491896
ACCEPTANCE_ALPHA = 0.001
ITERATIONS = 5000
CONVERGENCE_SAMPLE_COUNTS = (1000, 5000, 20000)
RNG_IMPLEMENTATION = "numpy.random.Generator(PCG64)"

# DSM contract constants. Defined from the propagation structure, not from stored values.
DSM_MATERIALITY_THRESHOLD = 0.05
DSM_PROPAGATION_STEPS = 3

MODULE_ADDITIONS = [
    {
        "module_id": "1.1",
        "module_name": "Monte Carlo EAC",
        "category_number": 1,
        "synthetic_package": "A",
        "primary_files": (
            "cost_elements.csv|cost_risk_events.csv|cost_correlations.csv|"
            "cost_risk_ground_truth.csv|cost_risk_component_ground_truth.csv|"
            "monte_carlo_convergence.csv|monte_carlo_known_answer_cases.csv|"
            "monte_carlo_known_answer_ground_truth.csv"
        ),
        "proposed_owner_action": "IMPLEMENT_OR_TEST_WITH_SYNTHETIC_FIXTURES",
    },
    {
        "module_id": "5.4",
        "module_name": "Scenario Modeling",
        "category_number": 5,
        "synthetic_package": "B3",
        "primary_files": (
            "decision_problems.csv|actions.csv|scenarios.csv|action_scenario_outcomes.csv|"
            "payoff_matrices.csv|ground_truth_decisions.csv"
        ),
        "proposed_owner_action": "IMPLEMENT_OR_TEST_WITH_SYNTHETIC_FIXTURES",
    },
]


# ------------------------------------------------------------------ v0.2 tooling reuse


def load_v02_builder(base_root: Path):
    """Import the v0.2 builder and repoint its version constants at v0.3.

    Importing rather than copying keeps one implementation of the manifest, checksum,
    workbook and schema-catalog machinery. The v0.2 module has no import-time side effects.
    """
    path = base_root / "generators" / "build_opus_synthetic_programme_v0_2.py"
    spec = importlib.util.spec_from_file_location("og_build_v0_2", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.PROGRAMME_VERSION = PROGRAMME_VERSION
    module.GENERATOR_VERSION = GENERATOR_VERSION
    module.SEED = SEED

    def package_version_for(target: Path, root: Path) -> str:
        parts = target.relative_to(root).parts
        if parts and parts[0] == "package_A_project_structures":
            return "A-0.3"
        if parts[:2] == ("package_B_reference_training_decisions", "B1_reference_population"):
            return "B1-0.3"
        if parts[:2] == ("package_B_reference_training_decisions", "B2_expert_epistemic"):
            return "B2-0.3"
        if parts[:2] == ("package_B_reference_training_decisions", "B3_decision_optimization"):
            return "B3-0.3"
        if parts and parts[0] == "package_C_optional_activation_lab":
            return "C-0.3"
        return "ROOT-0.3"

    module.package_version_for = package_version_for

    def update_json_versions(value: Any) -> Any:
        if isinstance(value, dict):
            out = {key: update_json_versions(item) for key, item in value.items()}
            if "programme_version" in out:
                out["programme_version"] = PROGRAMME_VERSION
            if "data_origin" in out:
                out["data_origin"] = DATA_ORIGIN
            if "not_for_empirical_validation" in out:
                out["not_for_empirical_validation"] = True
            return out
        if isinstance(value, list):
            return [update_json_versions(item) for item in value]
        if value in ("OG-SYNTH-0.1", "OG-SYNTH-0.2"):
            return PROGRAMME_VERSION
        return value

    module.update_json_versions = update_json_versions
    return module


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_seed(*parts: str) -> int:
    material = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:4], "big")


def ground_truth_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=float)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ Monte Carlo


def triangular_mean(low: float, mode: float, high: float) -> float:
    """E[X] for a triangular variable is (a + m + b) / 3. Closed form, no sampling."""
    return (float(low) + float(mode) + float(high)) / 3.0


def triangular_variance(low: float, mode: float, high: float) -> float:
    a, m, b = float(low), float(mode), float(high)
    return (a * a + m * m + b * b - a * m - a * b - m * b) / 18.0


def simulate_cost_risk(
    elements: pd.DataFrame,
    risks: pd.DataFrame,
    correlation: np.ndarray,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    """The governed sampling contract, in one place.

    Cost elements: triangular marginals, dependence induced by a Gaussian copula over the
    declared correlation matrix. Risk events: independent Bernoulli occurrence times a
    triangular impact. Nothing here is Beta-PERT.
    """
    rng = np.random.default_rng(seed)
    n = len(elements)
    chol = np.linalg.cholesky(correlation)
    z = rng.normal(size=(iterations, n)) @ chol.T
    u = norm.cdf(z)
    element_samples = np.zeros((iterations, n))
    for i, row in enumerate(elements.itertuples()):
        low = float(row.low_cost_usd)
        mode = float(row.most_likely_cost_usd)
        high = float(row.high_cost_usd)
        if high - low <= 0:
            # Deterministic collapse: low, mode and high coincide, so the variable is the
            # constant and no draw is taken.
            element_samples[:, i] = low
            continue
        c = (mode - low) / (high - low)
        element_samples[:, i] = triang.ppf(u[:, i], c=c, loc=low, scale=high - low)
    risk_total = np.zeros(iterations)
    for row in risks.itertuples():
        low = float(row.low_impact_usd)
        mode = float(row.most_likely_impact_usd)
        high = float(row.high_impact_usd)
        occurs = rng.random(iterations) < float(row.probability)
        if high - low <= 0:
            impacts = np.full(iterations, low)
        else:
            c = (mode - low) / (high - low)
            impacts = triang.rvs(
                c=c, loc=low, scale=high - low, size=iterations, random_state=rng
            )
        risk_total += occurs * impacts
    total = element_samples.sum(axis=1) + risk_total
    return {
        "total": total,
        "mean": float(np.mean(total)),
        "sd": float(np.std(total, ddof=1)),
        "p50": float(np.quantile(total, 0.5)),
        "p80": float(np.quantile(total, 0.8)),
        "p90": float(np.quantile(total, 0.9)),
    }


def build_monte_carlo(module, root: Path) -> None:
    package = root / "package_A_project_structures"
    projects = pd.read_csv(package / "projects.csv")
    elements_all = module.strip_provenance(pd.read_csv(package / "cost_elements.csv"))
    risks_all = module.strip_provenance(pd.read_csv(package / "cost_risk_events.csv"))
    corr_all = module.strip_provenance(pd.read_csv(package / "cost_correlations.csv"))
    status = pd.read_csv(package / "schedule_status.csv")

    elements_all["cost_distribution_type"] = "TRIANGULAR"
    elements_all["distribution_parameterisation"] = "LOW_MODE_HIGH"
    elements_all["dependence_model"] = "GAUSSIAN_COPULA_ON_DECLARED_CORRELATION"
    risks_all["occurrence_model"] = "BERNOULLI"
    risks_all["impact_distribution_type"] = "TRIANGULAR"
    risks_all["impact_parameterisation"] = "LOW_MODE_HIGH"
    risks_all["dependence_model"] = "INDEPENDENT"

    module.write_csv(elements_all, package / "cost_elements.csv", root)
    module.write_csv(risks_all, package / "cost_risk_events.csv", root)

    component_rows: list[dict[str, Any]] = []
    project_rows: list[dict[str, Any]] = []
    convergence_rows: list[dict[str, Any]] = []

    for project in projects.itertuples():
        pid = project.project_id
        elements = elements_all[elements_all.project_id == pid].reset_index(drop=True)
        risks = risks_all[risks_all.project_id == pid].reset_index(drop=True)
        ids = list(elements.cost_element_id)
        index = {value: position for position, value in enumerate(ids)}
        correlation = np.eye(len(ids))
        for row in corr_all[corr_all.project_id == pid].itertuples():
            correlation[index[row.cost_element_id_a], index[row.cost_element_id_b]] = float(
                row.correlation
            )

        analytic_elements = 0.0
        for row in elements.itertuples():
            mean = triangular_mean(row.low_cost_usd, row.most_likely_cost_usd, row.high_cost_usd)
            analytic_elements += mean
            component_rows.append(
                {
                    "project_id": pid,
                    "component_kind": "COST_ELEMENT",
                    "component_id": row.cost_element_id,
                    "component_name": row.cost_element_name,
                    "occurrence_probability": 1.0,
                    "distribution_type": "TRIANGULAR",
                    "low": round(float(row.low_cost_usd), 2),
                    "most_likely": round(float(row.most_likely_cost_usd), 2),
                    "high": round(float(row.high_cost_usd), 2),
                    "dependency_group": row.correlation_group,
                    "analytic_expected_value_usd": round(mean, 6),
                    "analytic_variance_usd2": round(
                        triangular_variance(
                            row.low_cost_usd, row.most_likely_cost_usd, row.high_cost_usd
                        ),
                        6,
                    ),
                    "expectation_formula": "(low + most_likely + high) / 3",
                }
            )
        analytic_risks = 0.0
        for row in risks.itertuples():
            impact_mean = triangular_mean(
                row.low_impact_usd, row.most_likely_impact_usd, row.high_impact_usd
            )
            contribution = float(row.probability) * impact_mean
            analytic_risks += contribution
            component_rows.append(
                {
                    "project_id": pid,
                    "component_kind": "RISK_EVENT",
                    "component_id": row.risk_event_id,
                    "component_name": row.risk_name,
                    "occurrence_probability": float(row.probability),
                    "distribution_type": "TRIANGULAR",
                    "low": round(float(row.low_impact_usd), 2),
                    "most_likely": round(float(row.most_likely_impact_usd), 2),
                    "high": round(float(row.high_impact_usd), 2),
                    "dependency_group": "INDEPENDENT",
                    "analytic_expected_value_usd": round(contribution, 6),
                    "analytic_variance_usd2": "",
                    "expectation_formula": "probability * (low + most_likely + high) / 3",
                }
            )

        seed = stable_seed(PROGRAMME_VERSION, pid, "cost_risk", str(SEED))
        result = simulate_cost_risk(elements, risks, correlation, ITERATIONS, seed)
        analytic_total = analytic_elements + analytic_risks
        standard_error = result["sd"] / math.sqrt(ITERATIONS)
        absolute_error = abs(result["mean"] - analytic_total)
        threshold = ACCEPTANCE_Z * standard_error

        actual = status[status.project_id == pid]
        actual_cost = (
            float(actual.actual_cost_usd.sum()) if "actual_cost_usd" in actual.columns else ""
        )

        payload = {
            "project_id": pid,
            "analytic_expected_total_cost_usd": round(analytic_total, 6),
            "simulated_mean_total_cost_usd": round(result["mean"], 6),
            "iterations": ITERATIONS,
            "simulation_seed": seed,
        }
        project_rows.append(
            {
                "project_id": pid,
                "reporting_period_scope": "PROJECT_TOTAL_AT_COMPLETION",
                "bac_usd": float(project.baseline_budget_usd),
                "actual_cost_to_date_usd": actual_cost,
                "cost_element_count": len(elements),
                "risk_event_count": len(risks),
                "cost_distribution_type": "TRIANGULAR",
                "risk_impact_distribution_type": "TRIANGULAR",
                "risk_occurrence_model": "BERNOULLI",
                "dependence_model": "GAUSSIAN_COPULA_ON_DECLARED_CORRELATION",
                "rng_implementation": RNG_IMPLEMENTATION,
                "simulation_seed": seed,
                "seed_derivation": "sha256(programme_version|project_id|cost_risk|programme_seed)[:4]",
                "monte_carlo_iterations": ITERATIONS,
                "analytic_expected_element_cost_usd": round(analytic_elements, 6),
                "analytic_expected_risk_contribution_usd": round(analytic_risks, 6),
                "analytic_expected_total_cost_usd": round(analytic_total, 6),
                "simulated_mean_total_cost_usd": round(result["mean"], 6),
                "simulated_sd_total_cost_usd": round(result["sd"], 6),
                "simulated_standard_error_usd": round(standard_error, 6),
                "p50_total_cost_usd": round(result["p50"], 2),
                "p80_total_cost_usd": round(result["p80"], 2),
                "p90_total_cost_usd": round(result["p90"], 2),
                "probability_exceed_baseline_budget": round(
                    float(np.mean(result["total"] > float(project.baseline_budget_usd))), 6
                ),
                "absolute_mean_error_usd": round(absolute_error, 6),
                "relative_mean_error": round(absolute_error / analytic_total, 9),
                "mean_error_in_standard_errors": round(absolute_error / standard_error, 6),
                "acceptance_rule": "abs(simulated_mean - analytic_mean) <= z * standard_error",
                "acceptance_z": ACCEPTANCE_Z,
                "acceptance_alpha_two_sided": ACCEPTANCE_ALPHA,
                "acceptance_threshold_usd": round(threshold, 6),
                "mean_check_passed": bool(absolute_error <= threshold),
                "ground_truth_hash": ground_truth_hash(payload),
            }
        )

        for count in CONVERGENCE_SAMPLE_COUNTS:
            convergence_seed = stable_seed(
                PROGRAMME_VERSION, pid, "cost_risk_convergence", str(count)
            )
            run = simulate_cost_risk(elements, risks, correlation, count, convergence_seed)
            run_se = run["sd"] / math.sqrt(count)
            run_error = abs(run["mean"] - analytic_total)
            convergence_rows.append(
                {
                    "project_id": pid,
                    "monte_carlo_iterations": count,
                    "simulation_seed": convergence_seed,
                    "rng_implementation": RNG_IMPLEMENTATION,
                    "analytic_expected_total_cost_usd": round(analytic_total, 6),
                    "simulated_mean_total_cost_usd": round(run["mean"], 6),
                    "simulated_sd_total_cost_usd": round(run["sd"], 6),
                    "simulated_standard_error_usd": round(run_se, 6),
                    "absolute_mean_error_usd": round(run_error, 6),
                    "relative_mean_error": round(run_error / analytic_total, 9),
                    "mean_error_in_standard_errors": round(run_error / run_se, 6),
                    "acceptance_z": ACCEPTANCE_Z,
                    "within_acceptance": bool(run_error <= ACCEPTANCE_Z * run_se),
                }
            )

    module.write_csv(
        pd.DataFrame(component_rows),
        package / "cost_risk_component_ground_truth.csv",
        root,
    )
    module.write_csv(pd.DataFrame(project_rows), package / "cost_risk_ground_truth.csv", root)
    module.write_csv(pd.DataFrame(convergence_rows), package / "monte_carlo_convergence.csv", root)
    build_monte_carlo_known_answers(module, root)

    module.write_json(
        {
            "programme_version": PROGRAMME_VERSION,
            "data_origin": DATA_ORIGIN,
            "not_for_empirical_validation": True,
            "module": {"repository_module_id": "A1.1", "synthetic_module_id": "1.1",
                       "module_name": "Monte Carlo EAC"},
            "cost_element_distribution": {
                "type": "TRIANGULAR",
                "parameters": ["low_cost_usd", "most_likely_cost_usd", "high_cost_usd"],
                "expectation": "(low + most_likely + high) / 3",
                "variance": "(a^2 + m^2 + b^2 - am - ab - mb) / 18",
                "dependence": "Gaussian copula over cost_correlations.csv",
            },
            "risk_event_model": {
                "occurrence": "BERNOULLI",
                "impact_distribution": {"type": "TRIANGULAR",
                                        "expectation": "(low + most_likely + high) / 3"},
                "expected_contribution": "probability * impact expectation",
                "dependence": "independent across events and of the cost elements",
            },
            "rng": {"implementation": RNG_IMPLEMENTATION,
                    "seed_derivation": "sha256(programme_version|project_id|purpose|programme_seed)[:4]"},
            "iterations": ITERATIONS,
            "convergence_sample_counts": list(CONVERGENCE_SAMPLE_COUNTS),
            "acceptance_rule": {
                "statistic": "abs(simulated_mean - analytic_mean)",
                "threshold": "z * simulated_sd / sqrt(iterations)",
                "z": ACCEPTANCE_Z,
                "alpha_two_sided": ACCEPTANCE_ALPHA,
                "justification": (
                    "alpha 0.001 is 0.05 Bonferroni corrected across fifty mean checks in this "
                    "package. The rule is fixed before any result is computed."
                ),
            },
            "not_the_production_model": (
                "The repository module A1.1 forecasts a completion cost from earned value "
                "indices through a Beta-PERT. This package models a bottom-up triangular cost "
                "build-up with discrete risk events. They are different models and this "
                "fixture family is not an oracle for the production module."
            ),
        },
        root / "package_A_project_structures" / "monte_carlo_contract.json",
    )


def build_monte_carlo_known_answers(module, root: Path) -> None:
    """Cases whose expectation is derivable by hand, independently of any simulation."""
    package = root / "package_A_project_structures"
    cases = [
        # case_id, description, components as (kind, prob, low, mode, high)
        ("MCKA-A", "Deterministic collapse: low equals mode equals high",
         [("COST_ELEMENT", 1.0, 250000.0, 250000.0, 250000.0)]),
        ("MCKA-B", "Single triangular cost element",
         [("COST_ELEMENT", 1.0, 100000.0, 200000.0, 600000.0)]),
        ("MCKA-D", "Single discrete risk event at probability one quarter",
         [("RISK_EVENT", 0.25, 40000.0, 80000.0, 120000.0)]),
        ("MCKA-E", "Three independent cost elements",
         [("COST_ELEMENT", 1.0, 100000.0, 150000.0, 200000.0),
          ("COST_ELEMENT", 1.0, 50000.0, 90000.0, 100000.0),
          ("COST_ELEMENT", 1.0, 10000.0, 10000.0, 40000.0)]),
        ("MCKA-F", "Risk event at probability zero",
         [("RISK_EVENT", 0.0, 40000.0, 80000.0, 120000.0)]),
        ("MCKA-G", "Risk event at probability one",
         [("RISK_EVENT", 1.0, 40000.0, 80000.0, 120000.0)]),
        ("MCKA-H", "Reproducibility pair, same seed as MCKA-B",
         [("COST_ELEMENT", 1.0, 100000.0, 200000.0, 600000.0)]),
        ("MCKA-I", "Different seed, same inputs as MCKA-B",
         [("COST_ELEMENT", 1.0, 100000.0, 200000.0, 600000.0)]),
    ]
    seeds = {"MCKA-H": "MCKA-B", "MCKA-I": "MCKA-I-ALT"}
    case_rows: list[dict[str, Any]] = []
    truth_rows: list[dict[str, Any]] = []
    for case_id, description, components in cases:
        elements = pd.DataFrame(
            [
                {
                    "cost_element_id": f"{case_id}-CE-{i + 1:02d}",
                    "cost_element_name": "COMPONENT",
                    "low_cost_usd": low,
                    "most_likely_cost_usd": mode,
                    "high_cost_usd": high,
                    "correlation_group": "CG-1",
                }
                for i, (kind, _p, low, mode, high) in enumerate(components)
                if kind == "COST_ELEMENT"
            ]
        )
        risks = pd.DataFrame(
            [
                {
                    "risk_event_id": f"{case_id}-CR-{i + 1:02d}",
                    "risk_name": "EVENT",
                    "probability": probability,
                    "low_impact_usd": low,
                    "most_likely_impact_usd": mode,
                    "high_impact_usd": high,
                }
                for i, (kind, probability, low, mode, high) in enumerate(components)
                if kind == "RISK_EVENT"
            ]
        )
        analytic = 0.0
        for i, (kind, probability, low, mode, high) in enumerate(components):
            weight = 1.0 if kind == "COST_ELEMENT" else probability
            analytic += weight * triangular_mean(low, mode, high)
            case_rows.append(
                {
                    "case_id": case_id,
                    "case_description": description,
                    "component_index": i + 1,
                    "component_kind": kind,
                    "occurrence_probability": probability,
                    "distribution_type": "TRIANGULAR",
                    "low": low,
                    "most_likely": mode,
                    "high": high,
                    "hand_expectation_formula": (
                        "(low + most_likely + high) / 3"
                        if kind == "COST_ELEMENT"
                        else "probability * (low + most_likely + high) / 3"
                    ),
                }
            )
        seed = stable_seed(PROGRAMME_VERSION, seeds.get(case_id, case_id), "known_answer")
        correlation = np.eye(max(len(elements), 1))
        if len(elements) == 0:
            elements = pd.DataFrame(
                columns=[
                    "cost_element_id",
                    "cost_element_name",
                    "low_cost_usd",
                    "most_likely_cost_usd",
                    "high_cost_usd",
                    "correlation_group",
                ]
            )
            correlation = np.zeros((0, 0))
        result = simulate_cost_risk(elements, risks, correlation, ITERATIONS, seed)
        sd = result["sd"] if result["sd"] > 0 else 0.0
        standard_error = sd / math.sqrt(ITERATIONS)
        error = abs(result["mean"] - analytic)
        deterministic = sd == 0.0
        truth_rows.append(
            {
                "case_id": case_id,
                "case_description": description,
                "monte_carlo_iterations": ITERATIONS,
                "simulation_seed": seed,
                "rng_implementation": RNG_IMPLEMENTATION,
                "analytic_expected_total_usd": round(analytic, 6),
                "simulated_mean_total_usd": round(result["mean"], 6),
                "simulated_sd_total_usd": round(sd, 6),
                "simulated_standard_error_usd": round(standard_error, 6),
                "absolute_mean_error_usd": round(error, 9),
                "acceptance_z": ACCEPTANCE_Z,
                "acceptance_threshold_usd": round(ACCEPTANCE_Z * standard_error, 9),
                "deterministic_case": deterministic,
                "mean_check_passed": bool(
                    error <= 1e-9 if deterministic else error <= ACCEPTANCE_Z * standard_error
                ),
                "ground_truth_hash": ground_truth_hash(
                    {"case_id": case_id, "analytic": round(analytic, 6), "simulation_seed": seed}
                ),
            }
        )
    module.write_csv(pd.DataFrame(case_rows), package / "monte_carlo_known_answer_cases.csv", root)
    module.write_csv(
        pd.DataFrame(truth_rows), package / "monte_carlo_known_answer_ground_truth.csv", root
    )


# ------------------------------------------------------------------ DSM


def propagate(matrix: np.ndarray, seed_vector: np.ndarray, steps: int) -> dict[str, np.ndarray]:
    """The declared DSM propagation semantics.

    matrix[t, s] is the rework strength carried from source s to target t. A step multiplies
    the current step vector by the matrix; it does not re-inject the seed. The propagated
    vector is the sum of the step vectors and excludes the seed. The cumulative state is the
    seed plus the propagated vector. This is a fixed-depth truncated series, not the limit of
    the series: the fixture graphs contain a cycle and the truncation is the contract.
    """
    current = seed_vector.copy()
    step_vectors: list[np.ndarray] = []
    for _ in range(steps):
        current = matrix @ current
        step_vectors.append(current.copy())
    propagated = np.sum(step_vectors, axis=0) if step_vectors else np.zeros_like(seed_vector)
    return {
        "first_order": step_vectors[0] if step_vectors else np.zeros_like(seed_vector),
        "steps": step_vectors,
        "propagated": propagated,
        "cumulative": seed_vector + propagated,
    }


def dsm_row(
    project_id: str,
    period_id: str,
    node_ids: list[str],
    matrix: np.ndarray,
    seed_node: str,
    seed_magnitude: float,
    steps: int,
) -> dict[str, Any]:
    index = {node: position for position, node in enumerate(node_ids)}
    seed_vector = np.zeros(len(node_ids))
    seed_vector[index[seed_node]] = seed_magnitude
    out = propagate(matrix, seed_vector, steps)
    propagated = out["propagated"]
    cumulative = out["cumulative"]
    positive_excluding_seed = int(
        sum(
            1
            for node, position in index.items()
            if node != seed_node and propagated[position] > 0
        )
    )
    positive_including_seed = int(np.sum(cumulative > 0))
    material_including_seed = int(np.sum(cumulative > DSM_MATERIALITY_THRESHOLD))
    material_excluding_seed = int(
        sum(
            1
            for node, position in index.items()
            if node != seed_node and propagated[position] > DSM_MATERIALITY_THRESHOLD
        )
    )
    vector = lambda values: json.dumps(  # noqa: E731 - local formatting helper
        {node: round(float(values[position]), 6) for node, position in index.items()},
        sort_keys=True,
    )
    payload = {
        "project_id": project_id,
        "period_id": period_id,
        "seed_node_id": seed_node,
        "seed_magnitude": seed_magnitude,
        "cumulative": [round(float(v), 6) for v in cumulative],
    }
    return {
        "project_id": project_id,
        "period_id": period_id,
        "seed_node_id": seed_node,
        "seed_magnitude": round(float(seed_magnitude), 6),
        "propagation_steps": steps,
        "propagation_rule": "step_k = matrix @ step_(k-1); step_0 = seed vector",
        "cycle_handling": "FIXED_DEPTH_TRUNCATION_NOT_CONVERGENCE",
        "seed_impact_vector": vector(seed_vector),
        "first_order_impact_vector": vector(out["first_order"]),
        "propagated_impact_vector": vector(propagated),
        "cumulative_state_vector": vector(cumulative),
        "total_first_order_impact": round(float(out["first_order"].sum()), 6),
        "total_propagated_impact_excluding_seed": round(float(propagated.sum()), 6),
        "total_state_including_seed": round(float(cumulative.sum()), 6),
        "positive_impacted_node_count_excluding_seed": positive_excluding_seed,
        "positive_state_node_count_including_seed": positive_including_seed,
        "material_impacted_node_count_excluding_seed": material_excluding_seed,
        "material_state_node_count_including_seed": material_including_seed,
        "materiality_threshold": DSM_MATERIALITY_THRESHOLD,
        "seed_included_in_cumulative_state": True,
        "seed_included_in_propagated_impact": False,
        "ground_truth_hash": ground_truth_hash(payload),
    }


def build_dsm(module, root: Path) -> None:
    package = root / "package_A_project_structures"
    nodes = pd.read_csv(package / "dsm_nodes.csv")
    edges = pd.read_csv(package / "dsm_edges.csv")
    previous = pd.read_csv(package / "dsm_ground_truth.csv")
    rows: list[dict[str, Any]] = []
    for entry in previous.itertuples():
        pid = entry.project_id
        node_ids = list(nodes[nodes.project_id == pid].node_id)
        index = {node: position for position, node in enumerate(node_ids)}
        matrix = np.zeros((len(node_ids), len(node_ids)))
        for edge in edges[edges.project_id == pid].itertuples():
            matrix[index[edge.target_node_id], index[edge.source_node_id]] = float(
                edge.dependency_strength
            )
        period_number = int(str(entry.period_id)[1:])
        rows.append(
            dsm_row(
                pid,
                entry.period_id,
                node_ids,
                matrix,
                entry.seed_node_id,
                1.0 + 0.15 * period_number,
                DSM_PROPAGATION_STEPS,
            )
        )
    module.write_csv(pd.DataFrame(rows), package / "dsm_ground_truth.csv", root)
    build_dsm_known_answers(module, root)
    module.write_json(
        {
            "programme_version": PROGRAMME_VERSION,
            "data_origin": DATA_ORIGIN,
            "not_for_empirical_validation": True,
            "module": {"repository_module_id": "A5.1", "synthetic_module_id": "5.1",
                       "module_name": "DSM Rework Propagation"},
            "matrix_orientation": "matrix[target, source] = dependency_strength of edge source to target",
            "seed": "seed_impact_vector carries seed_magnitude at seed_node_id and zero elsewhere",
            "first_order": "first_order_impact_vector = matrix @ seed_impact_vector",
            "step_rule": "step_k = matrix @ step_(k-1), for k = 1 to propagation_steps",
            "propagated": "propagated_impact_vector = sum of step vectors, seed excluded",
            "cumulative": "cumulative_state_vector = seed_impact_vector + propagated_impact_vector",
            "counts": {
                "positive_impacted_node_count_excluding_seed":
                    "nodes other than the seed whose propagated impact is above zero",
                "positive_state_node_count_including_seed":
                    "nodes whose cumulative state is above zero, seed included",
                "material_impacted_node_count_excluding_seed":
                    "nodes other than the seed whose propagated impact exceeds the threshold",
                "material_state_node_count_including_seed":
                    "nodes whose cumulative state exceeds the threshold, seed included",
            },
            "materiality_threshold": DSM_MATERIALITY_THRESHOLD,
            "cycle_handling": (
                "The dependency graphs contain a cycle. Propagation is truncated at "
                "propagation_steps rather than iterated to convergence, so the stored state is "
                "a partial sum of the series and not its limit."
            ),
        },
        package / "dsm_contract.json",
    )


DSM_KNOWN_ANSWER_CASES: list[dict[str, Any]] = [
    {
        "case_id": "DSMKA-01",
        "case_description": "One seed with one outgoing edge",
        "nodes": ["N1", "N2"],
        "edges": [("N1", "N2", 0.5)],
        "seed_node": "N1",
        "seed_magnitude": 1.0,
        "steps": 1,
    },
    {
        "case_id": "DSMKA-02",
        "case_description": "One seed with two outgoing edges",
        "nodes": ["N1", "N2", "N3"],
        "edges": [("N1", "N2", 0.5), ("N1", "N3", 0.25)],
        "seed_node": "N1",
        "seed_magnitude": 2.0,
        "steps": 1,
    },
    {
        "case_id": "DSMKA-03",
        "case_description": "Disconnected node never receives impact",
        "nodes": ["N1", "N2", "N3"],
        "edges": [("N1", "N2", 0.4)],
        "seed_node": "N1",
        "seed_magnitude": 1.0,
        "steps": 3,
    },
    {
        "case_id": "DSMKA-04",
        "case_description": "Two step chain",
        "nodes": ["N1", "N2", "N3"],
        "edges": [("N1", "N2", 0.5), ("N2", "N3", 0.4)],
        "seed_node": "N1",
        "seed_magnitude": 1.0,
        "steps": 2,
    },
    {
        "case_id": "DSMKA-05",
        "case_description": "Branching then converging paths",
        "nodes": ["N1", "N2", "N3", "N4"],
        "edges": [("N1", "N2", 0.5), ("N1", "N3", 0.25), ("N2", "N4", 0.2), ("N3", "N4", 0.4)],
        "seed_node": "N1",
        "seed_magnitude": 1.0,
        "steps": 2,
    },
    {
        "case_id": "DSMKA-06",
        "case_description": "Zero strength edge carries nothing",
        "nodes": ["N1", "N2"],
        "edges": [("N1", "N2", 0.0)],
        "seed_node": "N1",
        "seed_magnitude": 1.0,
        "steps": 2,
    },
    {
        "case_id": "DSMKA-07",
        "case_description": "Threshold boundary: one node lands exactly on the threshold",
        "nodes": ["N1", "N2", "N3"],
        "edges": [("N1", "N2", 0.05), ("N1", "N3", 0.06)],
        "seed_node": "N1",
        "seed_magnitude": 1.0,
        "steps": 1,
    },
    {
        "case_id": "DSMKA-08",
        "case_description": "Two node cycle truncated at three steps",
        "nodes": ["N1", "N2"],
        "edges": [("N1", "N2", 0.5), ("N2", "N1", 0.5)],
        "seed_node": "N1",
        "seed_magnitude": 1.0,
        "steps": 3,
    },
]


def build_dsm_known_answers(module, root: Path) -> None:
    package = root / "package_A_project_structures"
    node_rows: list[dict[str, Any]] = []
    edge_rows: list[dict[str, Any]] = []
    truth_rows: list[dict[str, Any]] = []
    for case in DSM_KNOWN_ANSWER_CASES:
        for node in case["nodes"]:
            node_rows.append(
                {"case_id": case["case_id"], "node_id": node, "node_name": node,
                 "node_type": "KNOWN_ANSWER_NODE"}
            )
        for source, target, strength in case["edges"]:
            edge_rows.append(
                {
                    "case_id": case["case_id"],
                    "source_node_id": source,
                    "target_node_id": target,
                    "dependency_type": "REWORK_PROPAGATION",
                    "dependency_strength": strength,
                }
            )
        index = {node: position for position, node in enumerate(case["nodes"])}
        matrix = np.zeros((len(case["nodes"]), len(case["nodes"])))
        for source, target, strength in case["edges"]:
            matrix[index[target], index[source]] = strength
        row = dsm_row(
            case["case_id"],
            "KNOWN_ANSWER",
            case["nodes"],
            matrix,
            case["seed_node"],
            case["seed_magnitude"],
            case["steps"],
        )
        row["case_id"] = row.pop("project_id")
        row["case_description"] = case["case_description"]
        row.pop("period_id")
        truth_rows.append(row)
    module.write_csv(pd.DataFrame(node_rows), package / "dsm_known_answer_nodes.csv", root)
    module.write_csv(pd.DataFrame(edge_rows), package / "dsm_known_answer_edges.csv", root)
    module.write_csv(
        pd.DataFrame(truth_rows), package / "dsm_known_answer_ground_truth.csv", root
    )


# ------------------------------------------------------------------ module identity


def build_module_identity(module, root: Path) -> None:
    """Make Monte Carlo EAC and Scenario Modeling permanent, one to one, by identifier."""
    module_map = module.strip_provenance(
        pd.read_csv(root / "module_asset_map.csv", dtype={"module_id": str})
    )
    module_map = module_map.drop(columns=["code_module_id"], errors="ignore")
    for addition in MODULE_ADDITIONS:
        if (module_map.module_id == addition["module_id"]).any():
            continue
        row = dict(addition)
        row["category_name"] = module.CATEGORY_NAMES[addition["category_number"]]
        module_map = pd.concat([module_map, pd.DataFrame([row])], ignore_index=True)
    # Monte Carlo's asset list grew in v0.3; keep it current whether or not it pre-existed.
    for addition in MODULE_ADDITIONS:
        module_map.loc[module_map.module_id == addition["module_id"], "primary_files"] = addition[
            "primary_files"
        ]
    module_map["category_number"] = module_map.category_number.astype(int)
    module_map["category_name"] = module_map.apply(
        lambda row: module.CATEGORY_NAMES.get(int(row.category_number), row.category_name), axis=1
    )
    module_map.insert(1, "code_module_id", module_map.module_id.map(module.code_module_id_for))
    module_map = module_map.sort_values(
        ["category_number", "module_id"], key=lambda series: series.astype(str)
    )
    duplicates = module_map.module_id.duplicated().any() or module_map.code_module_id.duplicated().any()
    if duplicates:
        raise RuntimeError("module identity is not one to one")
    module.write_csv(module_map, root / "module_asset_map.csv", root)

    aliases = module_map[
        [
            "module_id",
            "code_module_id",
            "module_name",
            "category_number",
            "category_name",
            "synthetic_package",
        ]
    ].rename(columns={"module_id": "literature_module_id"})
    module.write_csv(aliases, root / "module_id_aliases.csv", root)


# ------------------------------------------------------------------ documentation


def write_documentation(root: Path) -> None:
    (root / "AUDIT_RESOLUTION_v0.3.md").write_text(
        "\n".join(
            [
                "# Audit resolution, v0.3",
                "",
                "Two ground-truth families were corrected and the module identity tables were",
                "made permanent. Nothing else changed apart from version stamps.",
                "",
                "| Finding | v0.3 resolution |",
                "|---|---|",
                "| Monte Carlo distribution undeclared | Cost elements and risk impacts declare "
                "TRIANGULAR explicitly, in the element and event tables and in "
                "monte_carlo_contract.json. |",
                "| Monte Carlo mean judged against a Beta-PERT expectation | The analytic mean "
                "is the triangular expectation, which is what the generator samples. The mean "
                "is judged against z times the standard error, not a percentage. |",
                "| Monte Carlo outputs not traceable to inputs | Every element and event now "
                "carries its own analytic expectation row, and every project row carries seed, "
                "generator, iterations, standard error and acceptance threshold. |",
                "| Monte Carlo identity by overlay | Permanent alias and asset map rows. |",
                "| DSM fields mixed several quantities | Seed, first order, propagated, "
                "cumulative state, positive counts and material counts are separate named "
                "fields with an explicit threshold and explicit seed inclusion flags. |",
                "| DSM cycle behaviour undocumented | Truncation at a fixed depth is declared "
                "in dsm_contract.json and in every row. |",
                "",
                "Synthetic data verifies implementation only. It is not empirical evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    readme = root / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        text = text.replace("v0.2", "v0.3").replace("OG-SYNTH-0.2", "OG-SYNTH-0.3")
        readme.write_text(text, encoding="utf-8")


def create_requirements_lock(root: Path) -> None:
    versions = []
    for name in ["numpy", "pandas", "scipy", "networkx", "openpyxl"]:
        versions.append(f"{name}=={getattr(__import__(name), '__version__', 'UNKNOWN')}")
    (root / "requirements-lock.txt").write_text("\n".join(versions) + "\n", encoding="utf-8")


def write_build_provenance(root: Path, base_root: Path) -> None:
    generators = root / "generators"
    payload = {
        "programme_version": PROGRAMME_VERSION,
        "generated_at": "2026-08-12T00:00:00Z",
        "base_programme": "OG-SYNTH-0.2",
        "builder": "build_opus_synthetic_programme_v0_3.py",
        "builder_sha256": sha256_path(Path(__file__)),
        "validator": "validate_synthetic_programme_v0_3.py",
        "validator_sha256": sha256_path(generators / "validate_synthetic_programme_v0_3.py"),
        "random_seed": SEED,
        "rng_implementation": RNG_IMPLEMENTATION,
        "python_version": sys.version.split()[0],
        "dependency_versions": {
            name: getattr(__import__(name), "__version__", "UNKNOWN")
            for name in ["numpy", "pandas", "scipy", "networkx", "openpyxl"]
        },
        "lxml_present_in_build_interpreter": _lxml_present(),
        "data_origin": DATA_ORIGIN,
        "not_for_empirical_validation": True,
    }
    (root / "BUILD_PROVENANCE.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )


def _lxml_present() -> bool:
    try:
        import lxml  # noqa: F401
    except Exception:
        return False
    return True


# ------------------------------------------------------------------ main


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-root",
        type=Path,
        default=here.parents[2] / "OG-SYNTH-0.2" / "Opus_Gubernatio_Synthetic_Programme_v0.2",
    )
    parser.add_argument("--output-root", type=Path, default=here.parent)
    parser.add_argument("--combined-zip", type=Path, default=None)
    args = parser.parse_args()

    base_root = args.base_root.resolve()
    root = args.output_root.resolve()
    combined_zip = args.combined_zip or (root.parent / f"{root.name}.zip")

    module = load_v02_builder(base_root)

    # Clear everything except this generators directory, then restage from v0.2.
    for path in sorted(root.iterdir()) if root.exists() else []:
        if path.name == "generators":
            continue
        shutil.rmtree(path) if path.is_dir() else path.unlink()
    root.mkdir(parents=True, exist_ok=True)
    for name in [
        "package_A_project_structures",
        "package_B_reference_training_decisions",
        "package_C_optional_activation_lab",
    ]:
        shutil.copytree(base_root / name, root / name)
    for name in ["README.md", "CLAUDE_CODE_HANDOFF_v0.2.md", "module_asset_map.csv",
                 "module_id_aliases.csv"]:
        if (base_root / name).exists():
            shutil.copy2(base_root / name, root / name)
    (root / "CLAUDE_CODE_HANDOFF_v0.2.md").rename(root / "CLAUDE_CODE_HANDOFF_v0.3.md")
    shutil.copytree(base_root / "generators" / "base", root / "generators" / "base",
                    dirs_exist_ok=True)
    shutil.copy2(
        base_root / "generators" / "build_opus_synthetic_programme_v0_2.py",
        root / "generators" / "build_opus_synthetic_programme_v0_2.py",
    )
    for name in ["PACKAGE_MANIFEST.csv", "PACKAGE_CHECKSUMS.sha256"]:
        for path in root.rglob(name):
            path.unlink(missing_ok=True)

    module.refresh_csv_provenance(root)
    module.refresh_json_versions(root)

    build_monte_carlo(module, root)
    build_dsm(module, root)
    module.build_module_maps  # kept importable; identity is written by build_module_identity
    build_module_identity(module, root)
    write_documentation(root)
    module.recursive_json_version_update(root)
    module.refresh_csv_provenance(root)
    create_requirements_lock(root)
    module.create_schema_catalog(root)
    write_build_provenance(root, base_root)
    module.create_package_local_manifests(root)

    validator = root / "generators" / "validate_synthetic_programme_v0_3.py"
    subprocess.run(
        [sys.executable, str(validator), "--root", str(root), "--write-report"], check=True
    )
    validation = json.loads((root / "validation_report.json").read_text(encoding="utf-8"))

    manifest = module.create_root_manifest(root)
    module.create_workbook(root, manifest, validation)
    module.create_package_local_manifests(root)
    manifest = module.create_root_manifest(root)

    module.deterministic_zip(root, combined_zip, root.name)

    verifier = root / "generators" / "verify_synthetic_checksums_v0_3.py"
    subprocess.run([sys.executable, str(verifier), "--root", str(root)], check=True)

    print(
        json.dumps(
            {
                "root": str(root),
                "combined_zip": str(combined_zip),
                "combined_zip_sha256": sha256_path(combined_zip),
                "validation_checks": validation["check_count"],
                "validation_failures": validation["failed_count"],
                "manifest_files": len(manifest),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
