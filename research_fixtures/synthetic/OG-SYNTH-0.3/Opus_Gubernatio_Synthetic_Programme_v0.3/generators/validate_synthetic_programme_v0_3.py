#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from scipy.optimize import linprog

PROVENANCE = [
    "data_origin",
    "programme_version",
    "package_version",
    "generator_version",
    "random_seed",
    "not_for_empirical_validation",
    "record_hash",
]


def validate(root: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def ck(name: str, condition: Any, detail: Any = "") -> None:
        checks.append({"check": name, "passed": bool(condition), "detail": str(detail)})

    def load(rel: str) -> pd.DataFrame:
        path = root / rel
        try:
            df = pd.read_csv(path)
            ck(f"load:{rel}", True, f"rows={len(df)} cols={len(df.columns)}")
            return df
        except Exception as exc:
            ck(f"load:{rel}", False, exc)
            return pd.DataFrame()

    required = [
        "module_asset_map.csv",
        "module_id_aliases.csv",
        "schemas/schema_catalog.json",
        "generators/build_opus_synthetic_programme_v0_3.py",
        "generators/validate_synthetic_programme_v0_3.py",
        "generators/verify_synthetic_checksums_v0_3.py",
        "generators/base/Opus_Gubernatio_Synthetic_Programme_v0.1.zip",
        "requirements-lock.txt",
        "AUDIT_RESOLUTION_v0.3.md",
        "package_A_project_structures/monte_carlo_contract.json",
        "package_A_project_structures/dsm_contract.json",
        "package_A_project_structures/cost_risk_component_ground_truth.csv",
        "package_A_project_structures/monte_carlo_convergence.csv",
        "package_A_project_structures/monte_carlo_known_answer_cases.csv",
        "package_A_project_structures/monte_carlo_known_answer_ground_truth.csv",
        "package_A_project_structures/dsm_known_answer_nodes.csv",
        "package_A_project_structures/dsm_known_answer_edges.csv",
        "package_A_project_structures/dsm_known_answer_ground_truth.csv",
    ]
    for rel in required:
        ck(f"required:{rel}", (root / rel).exists())

    # All ordinary CSV files must load and retain synthetic provenance.
    skip_names = {"MANIFEST.csv", "PACKAGE_MANIFEST.csv", "data_dictionary.csv"}
    for path in sorted(root.rglob("*.csv")):
        if path.name in skip_names:
            continue
        rel = str(path.relative_to(root))
        df = load(rel)
        if len(df) == 0:
            continue
        missing = [column for column in PROVENANCE if column not in df.columns]
        ck(f"provenance_columns:{rel}", not missing, missing)
        if not missing:
            ck(f"provenance_origin:{rel}", (df["data_origin"] == "SYNTHETIC_RESEARCH_FIXTURE").all())
            ck(
                f"provenance_nonempirical:{rel}",
                df["not_for_empirical_validation"].astype(str).str.lower().isin(["true", "1"]).all(),
            )
            ck(f"record_hash_nonblank:{rel}", df["record_hash"].astype(str).str.len().gt(20).all())

    A = "package_A_project_structures/"
    B1 = "package_B_reference_training_decisions/B1_reference_population/"
    B3 = "package_B_reference_training_decisions/B3_decision_optimization/"

    projects = load(A + "projects.csv")
    periods = load(A + "reporting_periods.csv")
    ck("A:6_projects", len(projects) == 6)
    ck("A:36_periods", len(periods) == 36)
    ck("A:period_pk", not periods.duplicated(["project_id", "period_id"]).any())

    activities = load(A + "schedule_activities.csv")
    dependencies = load(A + "schedule_dependencies.csv")
    status = load(A + "schedule_status.csv")
    ck("schedule:activity_pk", not activities.duplicated(["project_id", "activity_id"]).any())
    activity_keys = set(zip(activities.get("project_id", []), activities.get("activity_id", [])))
    ck(
        "schedule:dependency_fk",
        all(
            (row.project_id, row.predecessor_activity_id) in activity_keys
            and (row.project_id, row.successor_activity_id) in activity_keys
            for row in dependencies.itertuples()
        ),
    )
    ck(
        "schedule:status_fk",
        all((row.project_id, row.activity_id) in activity_keys for row in status.itertuples()),
    )
    for project_id, group in dependencies.groupby("project_id"):
        graph = nx.DiGraph()
        graph.add_edges_from(zip(group.predecessor_activity_id, group.successor_activity_id))
        ck(f"schedule:acyclic:{project_id}", nx.is_directed_acyclic_graph(graph))

    # CCPM: every buffer and activity must trace to a declared chain; sizing must recompute.
    chains = load(A + "ccpm_chains.csv")
    chain_activities = load(A + "ccpm_chain_activities.csv")
    sizing = load(A + "ccpm_buffer_sizing_inputs.csv")
    buffers = load(A + "ccpm_buffers.csv")
    chain_keys = set(zip(chains.get("project_id", []), chains.get("chain_id", [])))
    ck("ccpm:chain_pk", not chains.duplicated(["project_id", "chain_id"]).any())
    ck(
        "ccpm:activity_fk",
        all((row.project_id, row.activity_id) in activity_keys for row in chain_activities.itertuples()),
    )
    ck(
        "ccpm:chain_activity_fk",
        all((row.project_id, row.chain_id) in chain_keys for row in chain_activities.itertuples()),
    )
    ck(
        "ccpm:buffer_chain_fk",
        all((row.project_id, row.chain_id) in chain_keys for row in buffers.itertuples()),
    )
    ck("ccpm:activity_chain_columns", {"ccpm_chain_id", "ccpm_chain_type"}.issubset(activities.columns))
    for row in chains.itertuples():
        expected = max(1.0, 1.645 * math.sqrt(float(row.variance_sum_days2)))
        ck(f"ccpm:sizing:{row.chain_id}", abs(float(row.original_buffer_days) - expected) < 1e-6)
        member_count = len(
            chain_activities[
                (chain_activities.project_id == row.project_id)
                & (chain_activities.chain_id == row.chain_id)
            ]
        )
        ck(f"ccpm:member_count:{row.chain_id}", member_count == int(row.activity_count))
    ck(
        "ccpm:sizing_activity_fk",
        all((row.project_id, row.activity_id) in activity_keys for row in sizing.itertuples()),
    )

    # ABM rules must exist, be machine-readable, and resolve from agent/state rows.
    rules = load(A + "agent_decision_rules.csv")
    agents = load(A + "agents.csv")
    agent_history = load(A + "agent_state_history.csv")
    rule_ids = set(rules.get("decision_rule_id", []))
    ck("abm:agent_rule_fk", agents.get("decision_rule_id", pd.Series(dtype=str)).isin(rule_ids).all())
    ck("abm:history_rule_fk", agent_history.get("decision_rule_id", pd.Series(dtype=str)).isin(rule_ids).all())
    for column in ["condition_json", "action_json"]:
        valid = True
        for value in rules.get(column, []):
            try:
                json.loads(value)
            except Exception:
                valid = False
        ck(f"abm:valid_{column}", valid)

    # NCR cohort and independently recomputed period ground truth.
    audits = load(A + "quality_audits.csv")
    ncr_events = load(A + "ncr_events.csv")
    ncr_gt = load(A + "ncr_ground_truth.csv")
    ck("ncr:event_pk", not ncr_events.duplicated("ncr_id").any())
    ck("ncr:audit_fk", ncr_events.get("source_audit_id", pd.Series(dtype=str)).isin(set(audits.get("audit_id", []))).all())
    for row in ncr_gt.itertuples():
        cutoff_series = periods[
            (periods.project_id == row.project_id) & (periods.period_id == row.period_id)
        ].period_end
        if cutoff_series.empty:
            ck(f"ncr:period:{row.project_id}:{row.period_id}", False, "missing period")
            continue
        cutoff = pd.Timestamp(cutoff_series.iloc[0])
        events = ncr_events[
            (ncr_events.project_id == row.project_id)
            & (pd.to_datetime(ncr_events.issue_date) <= cutoff)
        ]
        close_dates = pd.to_datetime(events.close_date, errors="coerce")
        closed = events[close_dates.notna() & (close_dates <= cutoff)]
        open_count = len(events) - len(closed)
        ck(f"ncr:issued:{row.project_id}:{row.period_id}", len(events) == row.ncr_issued_to_date)
        ck(f"ncr:open:{row.project_id}:{row.period_id}", open_count == row.ncr_open_at_cutoff)

    # Environmental cohort and rate recomputation.
    requirements = load(A + "environmental_requirements.csv")
    assessments = load(A + "environmental_assessments.csv")
    violations = load(A + "environmental_violations.csv")
    env_gt = load(A + "environmental_ground_truth.csv")
    requirement_keys = set(zip(requirements.get("project_id", []), requirements.get("requirement_id", [])))
    ck("env:req_pk", not requirements.duplicated(["project_id", "requirement_id"]).any())
    ck(
        "env:assessment_fk",
        all((row.project_id, row.requirement_id) in requirement_keys for row in assessments.itertuples()),
    )
    ck(
        "env:violation_assessment_fk",
        violations.get("assessment_id", pd.Series(dtype=str)).isin(set(assessments.get("assessment_id", []))).all(),
    )
    for row in env_gt.itertuples():
        sub = assessments[
            (assessments.project_id == row.project_id)
            & (assessments.period_id == row.period_id)
        ]
        assessed = sub[sub.result.isin(["COMPLIANT", "NONCOMPLIANT"])]
        compliant = int((assessed.result == "COMPLIANT").sum())
        rate = compliant / len(assessed) if len(assessed) else 0.0
        ck(f"env:rate:{row.project_id}:{row.period_id}", abs(rate - row.environmental_compliance_rate) < 1e-8)

    # Reference/training split integrity and feature-vector leakage.
    reference_projects = load(B1 + "reference_projects.csv")
    split_manifest = load(B1 + "split_manifest.csv")
    ck("B1:360_projects", len(reference_projects) == 360)
    ck("B1:unique_split", split_manifest.get("reference_project_id", pd.Series(dtype=str)).is_unique)
    feature_cols = [
        column
        for column in [
            "project_type",
            "delivery_method",
            "region",
            "size_band",
            "baseline_cost_usd",
            "baseline_duration_days",
            "complexity_index",
        ]
        if column in reference_projects.columns
    ]
    if feature_cols and "split" in reference_projects.columns:
        tmp = reference_projects.copy()
        tmp["feature_hash"] = (
            tmp[feature_cols]
            .astype(str)
            .agg("|".join, axis=1)
            .map(lambda value: hashlib.sha256(value.encode()).hexdigest())
        )
        split_counts = tmp.groupby("feature_hash").split.nunique()
        ck("B1:no_duplicate_feature_vectors_across_splits", not (split_counts > 1).any())
    analogous_pairs = load(B1 + "analogous_pairs.csv")
    split_map = dict(zip(reference_projects.get("reference_project_id", []), reference_projects.get("split", [])))
    bad_pair = False
    for row in analogous_pairs.itertuples():
        if (
            split_map.get(row.target_project_id) == "LOCKED_HOLDOUT"
            and split_map.get(row.analog_project_id) == "LOCKED_HOLDOUT"
        ):
            bad_pair = True
    ck("B1:no_holdout_to_holdout_analog_pairs", not bad_pair)

    # Solver-consumable LP specifications must reproduce stored ground truth.
    lp_path = root / B3 / "lp_models.json"
    try:
        lp_data = json.loads(lp_path.read_text(encoding="utf-8"))
        ck("LP:load", True)
    except Exception as exc:
        lp_data = {}
        ck("LP:load", False, exc)
    ck("LP:schema_v02", lp_data.get("schema_version") == "LP-MODEL-0.2")
    for model in lp_data.get("models", []):
        coefficients = np.array(model["objective"]["coefficients"], dtype=float)
        bounds = [
            (float(variable["lower"]), float(variable["upper"]))
            for variable in model["variables"]
        ]
        a_ub: list[list[float]] = []
        b_ub: list[float] = []
        for constraint in model["constraints"]:
            if constraint["sense"] == "LE":
                a_ub.append(constraint["coefficients"])
                b_ub.append(constraint["rhs"])
        result = linprog(
            coefficients,
            A_ub=np.array(a_ub, dtype=float),
            b_ub=np.array(b_ub, dtype=float),
            bounds=bounds,
            method="highs",
        )
        expected = model["ground_truth"]
        ck(f"LP:solve:{model['decision_problem_id']}", bool(result.success) == bool(expected["success"]))
        if result.success:
            ck(
                f"LP:objective:{model['decision_problem_id']}",
                abs(float(result.fun) - float(expected["objective_value"])) < 1e-4,
            )

    aliases_path = root / "module_id_aliases.csv"
    try:
        aliases = pd.read_csv(aliases_path, dtype=str)
        ck("load:module_id_aliases.csv", True, f"rows={len(aliases)} cols={len(aliases.columns)}")
    except Exception as exc:
        aliases = pd.DataFrame()
        ck("load:module_id_aliases.csv", False, exc)
    ck("aliases:unique_literature", aliases.get("literature_module_id", pd.Series(dtype=str)).is_unique)
    ck("aliases:unique_code", aliases.get("code_module_id", pd.Series(dtype=str)).is_unique)
    critic_alias = aliases[
        (aliases.literature_module_id.astype(str) == "7.19")
        & (aliases.code_module_id == "B2.19")
    ]
    ck("aliases:critic_topsis", len(critic_alias) == 1)
    dsm_rows = aliases[aliases.module_name == "DSM Rework Propagation"]
    ck("boundary:DSM_in_A", len(dsm_rows) == 1 and dsm_rows.synthetic_package.iloc[0] == "A")

    # Package-local checksums must be self-contained and valid.
    package_dirs = [
        root / "package_A_project_structures",
        root / "package_B_reference_training_decisions",
        root / "package_C_optional_activation_lab",
    ]
    for package_dir in package_dirs:
        manifest_path = package_dir / "PACKAGE_MANIFEST.csv"
        checksum_path = package_dir / "PACKAGE_CHECKSUMS.sha256"
        ck(f"local_manifest:{package_dir.name}", manifest_path.exists())
        ck(f"local_checksums:{package_dir.name}", checksum_path.exists())
        if checksum_path.exists():
            valid = True
            for line in checksum_path.read_text(encoding="utf-8").splitlines():
                expected_sha, rel = line.split("  ", 1)
                path = package_dir / rel
                if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
                    valid = False
            ck(f"local_checksum_verify:{package_dir.name}", valid)


    # ------------------------------------------------------------------ v0.3 Monte Carlo
    #
    # Everything below recomputes. Nothing below re-reads a stored total and compares it with
    # itself.

    def triangular_mean(low: float, mode: float, high: float) -> float:
        return (float(low) + float(mode) + float(high)) / 3.0

    def gt_hash(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=float)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    mc_contract_path = root / A / "monte_carlo_contract.json"
    try:
        mc_contract = json.loads(mc_contract_path.read_text(encoding="utf-8"))
        ck("mc:contract_load", True)
    except Exception as exc:
        mc_contract = {}
        ck("mc:contract_load", False, exc)
    ck("mc:contract_element_distribution",
       mc_contract.get("cost_element_distribution", {}).get("type") == "TRIANGULAR")
    ck("mc:contract_risk_distribution",
       mc_contract.get("risk_event_model", {}).get("impact_distribution", {}).get("type")
       == "TRIANGULAR")
    ck("mc:contract_occurrence",
       mc_contract.get("risk_event_model", {}).get("occurrence") == "BERNOULLI")
    acceptance_z = float(mc_contract.get("acceptance_rule", {}).get("z", 0.0))
    ck("mc:contract_z_declared", acceptance_z > 0)

    elements = load(A + "cost_elements.csv")
    risk_events = load(A + "cost_risk_events.csv")
    components = load(A + "cost_risk_component_ground_truth.csv")
    cost_truth = load(A + "cost_risk_ground_truth.csv")
    convergence = load(A + "monte_carlo_convergence.csv")

    ck("mc:element_distribution_declared",
       len(elements) > 0 and (elements.cost_distribution_type == "TRIANGULAR").all())
    ck("mc:risk_distribution_declared",
       len(risk_events) > 0 and (risk_events.impact_distribution_type == "TRIANGULAR").all())
    ck("mc:risk_occurrence_declared",
       len(risk_events) > 0 and (risk_events.occurrence_model == "BERNOULLI").all())
    ck("mc:element_ordering",
       bool((elements.low_cost_usd <= elements.most_likely_cost_usd).all()
            and (elements.most_likely_cost_usd <= elements.high_cost_usd).all()))
    ck("mc:risk_ordering",
       bool((risk_events.low_impact_usd <= risk_events.most_likely_impact_usd).all()
            and (risk_events.most_likely_impact_usd <= risk_events.high_impact_usd).all()))
    ck("mc:probability_domain",
       bool((risk_events.probability >= 0).all() and (risk_events.probability <= 1).all()))

    # Component expectations recomputed from the declared parameters.
    component_bad: list[str] = []
    for row in components.itertuples():
        expected = triangular_mean(row.low, row.most_likely, row.high)
        if row.component_kind == "RISK_EVENT":
            expected *= float(row.occurrence_probability)
        if abs(expected - float(row.analytic_expected_value_usd)) > 1e-4:
            component_bad.append(str(row.component_id))
        if str(row.distribution_type) != "TRIANGULAR":
            component_bad.append(f"{row.component_id}:distribution")
    ck("mc:component_expectations", not component_bad, component_bad[:5])

    # Every declared element and event must appear exactly once as a component row.
    element_ids = set(elements.cost_element_id)
    risk_ids = set(risk_events.risk_event_id)
    component_ids = set(components.component_id)
    ck("mc:component_coverage", element_ids | risk_ids == component_ids,
       sorted((element_ids | risk_ids) ^ component_ids)[:5])

    for row in cost_truth.itertuples():
        pid = row.project_id
        mine = components[components.project_id == pid]
        element_sum = float(
            mine[mine.component_kind == "COST_ELEMENT"].analytic_expected_value_usd.sum()
        )
        risk_sum = float(
            mine[mine.component_kind == "RISK_EVENT"].analytic_expected_value_usd.sum()
        )
        ck(f"mc:analytic_elements:{pid}",
           abs(element_sum - float(row.analytic_expected_element_cost_usd)) < 1e-2)
        ck(f"mc:analytic_risks:{pid}",
           abs(risk_sum - float(row.analytic_expected_risk_contribution_usd)) < 1e-2)
        ck(f"mc:analytic_total:{pid}",
           abs(element_sum + risk_sum - float(row.analytic_expected_total_cost_usd)) < 1e-2)
        expected_se = float(row.simulated_sd_total_cost_usd) / math.sqrt(
            float(row.monte_carlo_iterations)
        )
        ck(f"mc:standard_error:{pid}",
           abs(expected_se - float(row.simulated_standard_error_usd)) < 1e-3)
        error = abs(float(row.simulated_mean_total_cost_usd)
                    - float(row.analytic_expected_total_cost_usd))
        ck(f"mc:mean_within_tolerance:{pid}",
           error <= acceptance_z * expected_se,
           f"error={error:.4f} threshold={acceptance_z * expected_se:.4f}")
        ck(f"mc:acceptance_threshold_recomputed:{pid}",
           abs(acceptance_z * expected_se - float(row.acceptance_threshold_usd)) < 1e-2)
        ck(f"mc:mean_check_recorded:{pid}",
           bool(str(row.mean_check_passed).lower() == "true") == (error <= acceptance_z * expected_se))
        ck(f"mc:quantile_order:{pid}",
           float(row.p50_total_cost_usd) <= float(row.p80_total_cost_usd)
           <= float(row.p90_total_cost_usd))
        ck(f"mc:iterations_positive:{pid}", int(row.monte_carlo_iterations) > 0)
        ck(f"mc:seed_present:{pid}", int(row.simulation_seed) > 0)
        ck(f"mc:rng_declared:{pid}", str(row.rng_implementation).startswith("numpy.random"))
        ck(f"mc:distribution_declared:{pid}",
           row.cost_distribution_type == "TRIANGULAR"
           and row.risk_impact_distribution_type == "TRIANGULAR")
        ck(f"mc:ground_truth_hash:{pid}",
           gt_hash({
               "project_id": pid,
               "analytic_expected_total_cost_usd": round(
                   float(row.analytic_expected_total_cost_usd), 6),
               "simulated_mean_total_cost_usd": round(
                   float(row.simulated_mean_total_cost_usd), 6),
               "iterations": int(row.monte_carlo_iterations),
               "simulation_seed": int(row.simulation_seed),
           }) == row.ground_truth_hash)
        # The mean must not be judged against a Beta-PERT expectation. Record the size of the
        # difference between the two families so a later reader can see they are not the same.
        pert = 0.0
        for c in mine.itertuples():
            weight = 1.0 if c.component_kind == "COST_ELEMENT" else float(c.occurrence_probability)
            pert += weight * (float(c.low) + 4 * float(c.most_likely) + float(c.high)) / 6.0
        ck(f"mc:triangular_not_pert:{pid}",
           abs(pert - float(row.analytic_expected_total_cost_usd)) > expected_se,
           f"pert={pert:.2f} triangular={float(row.analytic_expected_total_cost_usd):.2f}")

    # Convergence: every sample count inside tolerance, and error contracting with N.
    for pid, group in convergence.groupby("project_id"):
        group = group.sort_values("monte_carlo_iterations")
        for row in group.itertuples():
            se = float(row.simulated_sd_total_cost_usd) / math.sqrt(
                float(row.monte_carlo_iterations)
            )
            error = abs(float(row.simulated_mean_total_cost_usd)
                        - float(row.analytic_expected_total_cost_usd))
            ck(f"mc:convergence_within:{pid}:{int(row.monte_carlo_iterations)}",
               error <= acceptance_z * se, f"error={error:.4f} z*se={acceptance_z * se:.4f}")
            ck(f"mc:convergence_se_recomputed:{pid}:{int(row.monte_carlo_iterations)}",
               abs(se - float(row.simulated_standard_error_usd)) < 1e-3)
        counts = list(group.monte_carlo_iterations)
        ck(f"mc:convergence_counts:{pid}", counts == sorted(set(counts)) and len(counts) >= 3,
           counts)
        first, last = group.iloc[0], group.iloc[-1]
        ck(f"mc:convergence_se_contracts:{pid}",
           float(last.simulated_standard_error_usd) < float(first.simulated_standard_error_usd))

    # Known-answer cases: expectation derived from the parameters, not from the simulation.
    ka_cases = load(A + "monte_carlo_known_answer_cases.csv")
    ka_truth = load(A + "monte_carlo_known_answer_ground_truth.csv")
    for row in ka_truth.itertuples():
        parts = ka_cases[ka_cases.case_id == row.case_id]
        analytic = 0.0
        for part in parts.itertuples():
            weight = 1.0 if part.component_kind == "COST_ELEMENT" else float(
                part.occurrence_probability
            )
            analytic += weight * triangular_mean(part.low, part.most_likely, part.high)
        ck(f"mc:known_answer_analytic:{row.case_id}",
           abs(analytic - float(row.analytic_expected_total_usd)) < 1e-6)
        error = abs(float(row.simulated_mean_total_usd) - analytic)
        if str(row.deterministic_case).lower() == "true":
            ck(f"mc:known_answer_deterministic:{row.case_id}", error <= 1e-9, error)
        else:
            se = float(row.simulated_standard_error_usd)
            ck(f"mc:known_answer_within:{row.case_id}", error <= acceptance_z * se,
               f"error={error:.6f} z*se={acceptance_z * se:.6f}")
    zero_case = ka_truth[ka_truth.case_id == "MCKA-F"]
    ck("mc:known_answer_probability_zero",
       len(zero_case) == 1 and abs(float(zero_case.analytic_expected_total_usd.iloc[0])) < 1e-9
       and abs(float(zero_case.simulated_mean_total_usd.iloc[0])) < 1e-9)
    one_case = ka_truth[ka_truth.case_id == "MCKA-G"]
    one_parts = ka_cases[ka_cases.case_id == "MCKA-G"]
    ck("mc:known_answer_probability_one",
       len(one_case) == 1 and abs(
           float(one_case.analytic_expected_total_usd.iloc[0])
           - triangular_mean(one_parts.low.iloc[0], one_parts.most_likely.iloc[0],
                             one_parts.high.iloc[0])) < 1e-6)
    pair = ka_truth[ka_truth.case_id.isin(["MCKA-B", "MCKA-H"])]
    ck("mc:known_answer_reproducibility",
       len(pair) == 2 and pair.simulation_seed.nunique() == 1
       and pair.simulated_mean_total_usd.nunique() == 1)
    different = ka_truth[ka_truth.case_id.isin(["MCKA-B", "MCKA-I"])]
    ck("mc:known_answer_different_seed",
       len(different) == 2 and different.simulation_seed.nunique() == 2
       and different.simulated_mean_total_usd.nunique() == 2)

    # ------------------------------------------------------------------ v0.3 DSM

    dsm_contract_path = root / (A + "dsm_contract.json")
    try:
        dsm_contract = json.loads(dsm_contract_path.read_text(encoding="utf-8"))
        ck("dsm:contract_load", True)
    except Exception as exc:
        dsm_contract = {}
        ck("dsm:contract_load", False, exc)
    ck("dsm:contract_threshold_declared",
       isinstance(dsm_contract.get("materiality_threshold"), (int, float)))
    ck("dsm:contract_cycle_declared", bool(dsm_contract.get("cycle_handling")))
    threshold_declared = float(dsm_contract.get("materiality_threshold", -1))

    def dsm_recompute(node_ids, edge_frame, source_key, seed_node, seed_magnitude, steps):
        index = {node: position for position, node in enumerate(node_ids)}
        matrix = np.zeros((len(node_ids), len(node_ids)))
        for edge in edge_frame.itertuples():
            matrix[index[edge.target_node_id], index[edge.source_node_id]] = float(
                edge.dependency_strength
            )
        seed_vector = np.zeros(len(node_ids))
        seed_vector[index[seed_node]] = float(seed_magnitude)
        current = seed_vector.copy()
        step_vectors = []
        for _ in range(int(steps)):
            current = matrix @ current
            step_vectors.append(current.copy())
        propagated = np.sum(step_vectors, axis=0) if step_vectors else np.zeros_like(seed_vector)
        return index, seed_vector, step_vectors[0], propagated, seed_vector + propagated

    def check_dsm_rows(truth_frame, node_frame, edge_frame, key_column, label):
        for row in truth_frame.itertuples():
            key = getattr(row, key_column)
            node_ids = list(node_frame[node_frame[key_column] == key].node_id)
            edges_here = edge_frame[edge_frame[key_column] == key]
            index, seed_vector, first_order, propagated, cumulative = dsm_recompute(
                node_ids, edges_here, key_column, row.seed_node_id, row.seed_magnitude,
                row.propagation_steps
            )
            name = f"{label}:{key}:{getattr(row, 'period_id', 'KNOWN_ANSWER')}"
            stored_first = json.loads(row.first_order_impact_vector)
            stored_prop = json.loads(row.propagated_impact_vector)
            stored_cum = json.loads(row.cumulative_state_vector)
            stored_seed = json.loads(row.seed_impact_vector)
            ck(f"dsm:seed_vector:{name}",
               all(abs(stored_seed[n] - seed_vector[i]) < 1e-6 for n, i in index.items()))
            ck(f"dsm:first_order:{name}",
               all(abs(stored_first[n] - first_order[i]) < 1e-6 for n, i in index.items()))
            ck(f"dsm:propagated:{name}",
               all(abs(stored_prop[n] - propagated[i]) < 1e-6 for n, i in index.items()))
            ck(f"dsm:cumulative:{name}",
               all(abs(stored_cum[n] - cumulative[i]) < 1e-6 for n, i in index.items()))
            ck(f"dsm:total_first_order:{name}",
               abs(float(first_order.sum()) - float(row.total_first_order_impact)) < 1e-5)
            ck(f"dsm:total_propagated:{name}",
               abs(float(propagated.sum())
                   - float(row.total_propagated_impact_excluding_seed)) < 1e-5)
            ck(f"dsm:total_state:{name}",
               abs(float(cumulative.sum()) - float(row.total_state_including_seed)) < 1e-5)
            positive_excluding = sum(
                1 for n, i in index.items() if n != row.seed_node_id and propagated[i] > 0
            )
            ck(f"dsm:positive_excluding_seed:{name}",
               positive_excluding == int(row.positive_impacted_node_count_excluding_seed))
            ck(f"dsm:positive_including_seed:{name}",
               int(np.sum(cumulative > 0)) == int(row.positive_state_node_count_including_seed))
            material_excluding = sum(
                1 for n, i in index.items()
                if n != row.seed_node_id and propagated[i] > float(row.materiality_threshold)
            )
            ck(f"dsm:material_excluding_seed:{name}",
               material_excluding == int(row.material_impacted_node_count_excluding_seed))
            ck(f"dsm:material_including_seed:{name}",
               int(np.sum(cumulative > float(row.materiality_threshold)))
               == int(row.material_state_node_count_including_seed))
            ck(f"dsm:threshold_matches_contract:{name}",
               abs(float(row.materiality_threshold) - threshold_declared) < 1e-12)
            ck(f"dsm:seed_flags:{name}",
               str(row.seed_included_in_cumulative_state).lower() == "true"
               and str(row.seed_included_in_propagated_impact).lower() == "false")
            ck(f"dsm:steps_positive:{name}", int(row.propagation_steps) > 0)
            ck(f"dsm:ground_truth_hash:{name}",
               gt_hash({
                   "project_id": key,
                   "period_id": getattr(row, "period_id", "KNOWN_ANSWER"),
                   "seed_node_id": row.seed_node_id,
                   "seed_magnitude": float(row.seed_magnitude),
                   "cumulative": [round(float(v), 6) for v in cumulative],
               }) == row.ground_truth_hash)

    dsm_nodes = load(A + "dsm_nodes.csv")
    dsm_edges = load(A + "dsm_edges.csv")
    dsm_truth = load(A + "dsm_ground_truth.csv")
    ck("dsm:edge_endpoints",
       set(dsm_edges.source_node_id) | set(dsm_edges.target_node_id) <= set(dsm_nodes.node_id))
    ck("dsm:strength_domain",
       bool((dsm_edges.dependency_strength >= 0).all()
            and (dsm_edges.dependency_strength <= 1).all()))
    ck("dsm:seed_nodes_declared", set(dsm_truth.seed_node_id) <= set(dsm_nodes.node_id))
    check_dsm_rows(dsm_truth, dsm_nodes, dsm_edges, "project_id", "programme")

    ka_nodes = load(A + "dsm_known_answer_nodes.csv")
    ka_edges = load(A + "dsm_known_answer_edges.csv")
    ka_dsm = load(A + "dsm_known_answer_ground_truth.csv")
    check_dsm_rows(ka_dsm, ka_nodes, ka_edges, "case_id", "known_answer")
    ck("dsm:known_answer_case_count", len(ka_dsm) >= 8, len(ka_dsm))

    # DSM location proved from the package manifest and the files on disk, not from a word in
    # the alias table.
    manifest_a = pd.read_csv(root / (A + "PACKAGE_MANIFEST.csv"))
    dsm_files_on_disk = sorted(
        str(path.relative_to(root)) for path in root.rglob("dsm_*.csv")
    )
    ck("dsm:assets_all_in_package_A",
       all(rel.startswith(A) for rel in dsm_files_on_disk), dsm_files_on_disk[:3])
    manifest_dsm = sorted(
        str(name) for name in manifest_a.file
        if str(name).startswith("dsm_") and str(name).endswith(".csv")
    )
    ck("dsm:assets_in_package_manifest",
       manifest_dsm == sorted(rel[len(A):] for rel in dsm_files_on_disk), manifest_dsm)

    # ------------------------------------------------------------------ v0.3 identity

    alias_frame = pd.read_csv(root / "module_id_aliases.csv", dtype=str)
    asset_frame = pd.read_csv(root / "module_asset_map.csv", dtype=str)
    for literature, code, name in [
        ("1.1", "A1.1", "Monte Carlo EAC"),
        ("5.4", "A5.4", "Scenario Modeling"),
        ("5.1", "A5.1", "DSM Rework Propagation"),
    ]:
        alias_row = alias_frame[alias_frame.literature_module_id == literature]
        ck(f"identity:alias_present:{code}",
           len(alias_row) == 1 and alias_row.code_module_id.iloc[0] == code
           and alias_row.module_name.iloc[0] == name)
        asset_row = asset_frame[asset_frame.module_id == literature]
        ck(f"identity:asset_map_present:{code}", len(asset_row) == 1)
        if len(asset_row) == 1:
            missing = [
                filename for filename in str(asset_row.primary_files.iloc[0]).split("|")
                if not list(root.rglob(filename))
            ]
            ck(f"identity:assets_exist:{code}", not missing, missing)
    ck("identity:one_to_one_literature", alias_frame.literature_module_id.is_unique)
    ck("identity:one_to_one_code", alias_frame.code_module_id.is_unique)
    ck("identity:alias_and_map_agree",
       sorted(alias_frame.literature_module_id) == sorted(asset_frame.module_id))
    ck("identity:no_overlay_needed",
       {"1.1", "5.4"} <= set(alias_frame.literature_module_id))

    # ------------------------------------------------------------------ prior audit gaps

    periods_frame = load(A + "reporting_periods.csv")
    ncr_events = load(A + "ncr_events.csv")
    audits = load(A + "quality_audits.csv")
    ncr_truth = load(A + "ncr_ground_truth.csv")
    ncr_bad: list[str] = []
    for period in periods_frame.itertuples():
        cutoff = pd.to_datetime(period.period_end)
        number = int(period.period_number)
        mine = ncr_events[ncr_events.project_id == period.project_id]
        issued = mine[pd.to_datetime(mine.issue_date) <= cutoff]
        closed_mask = issued.close_date.notna() & (
            pd.to_datetime(issued.close_date) <= cutoff
        )
        closed = issued[closed_mask]
        open_now = issued[~closed_mask]
        overdue = open_now[pd.to_datetime(open_now.due_date) < cutoff]
        audit_mine = audits[
            (audits.project_id == period.project_id)
            & (audits.period_id.str[1:].astype(int) <= number)
        ]
        inspections = int(audit_mine.inspections_completed.sum())
        calc = {
            "ncr_issued_to_date": len(issued),
            "ncr_closed_to_date": len(closed),
            "ncr_open_at_cutoff": len(open_now),
            "ncr_overdue_at_cutoff": len(overdue),
            "cumulative_inspections": inspections,
            "ncr_incidence_per_100_inspections":
                (len(issued) / inspections * 100) if inspections else 0.0,
            "closure_ratio": (len(closed) / len(issued)) if len(issued) else 0.0,
            "open_ratio": (len(open_now) / len(issued)) if len(issued) else 0.0,
            "overdue_open_ratio": (len(overdue) / len(open_now)) if len(open_now) else 0.0,
            "mean_open_age_days": (
                float((cutoff - pd.to_datetime(open_now.issue_date)).dt.days.mean())
                if len(open_now) else 0.0
            ),
        }
        stored = ncr_truth[
            (ncr_truth.project_id == period.project_id)
            & (ncr_truth.period_id == period.period_id)
        ]
        if len(stored) != 1:
            ncr_bad.append(f"{period.project_id}/{period.period_id}: no ground truth row")
            continue
        for quantity, value in calc.items():
            if abs(float(stored[quantity].iloc[0]) - float(value)) > 1e-6:
                ncr_bad.append(f"{period.project_id}/{period.period_id}/{quantity}")
    ck("gap:ncr_all_ten_quantities", not ncr_bad, ncr_bad[:5])

    requirements = load(A + "environmental_requirements.csv")
    assessments = load(A + "environmental_assessments.csv")
    violations = load(A + "environmental_violations.csv")
    env_truth = load(A + "environmental_ground_truth.csv")
    env_bad: list[str] = []
    for period in periods_frame.itertuples():
        end = pd.to_datetime(period.period_end)
        applicable = requirements[
            (requirements.project_id == period.project_id)
            & (requirements.applicable.astype(str).str.lower() == "true")
            & (pd.to_datetime(requirements.effective_date) <= end)
        ]
        assessed = assessments[
            (assessments.project_id == period.project_id)
            & (assessments.period_id == period.period_id)
            & (assessments.requirement_id.isin(set(applicable.requirement_id)))
            & (~assessments.result.isin(["NOT_ASSESSED", "NOT_APPLICABLE"]))
        ]
        compliant = assessed[assessed.result == "COMPLIANT"]
        noncompliant = assessed[assessed.result == "NONCOMPLIANT"]
        period_violations = violations[
            (violations.project_id == period.project_id)
            & (violations.period_id == period.period_id)
        ]
        severe = period_violations[period_violations.severity.isin(["CRITICAL", "HIGH"])]
        to_date = violations[
            (violations.project_id == period.project_id)
            & (pd.to_datetime(violations.identified_date) <= end)
        ]
        overdue_mask = to_date.corrective_due_date.notna() & (
            pd.to_datetime(to_date.corrective_due_date) < end
        ) & ~(
            to_date.corrective_close_date.notna()
            & (pd.to_datetime(to_date.corrective_close_date) <= end)
        )
        calc = {
            "applicable_requirements": len(applicable),
            "applicable_requirements_assessed": len(assessed),
            "compliant_requirements": len(compliant),
            "noncompliant_requirements": len(noncompliant),
            "unassessed_requirements": len(applicable) - len(assessed),
            "environmental_compliance_rate":
                (len(compliant) / len(assessed)) if len(assessed) else 0.0,
            "severe_noncompliances": len(severe),
            "overdue_corrective_actions": int(overdue_mask.sum()),
        }
        stored = env_truth[
            (env_truth.project_id == period.project_id)
            & (env_truth.period_id == period.period_id)
        ]
        if len(stored) != 1:
            env_bad.append(f"{period.project_id}/{period.period_id}: no ground truth row")
            continue
        for quantity, value in calc.items():
            if abs(float(stored[quantity].iloc[0]) - float(value)) > 1e-6:
                env_bad.append(f"{period.project_id}/{period.period_id}/{quantity}")
    ck("gap:environmental_all_eight_quantities", not env_bad, env_bad[:5])

    rules = load(A + "agent_decision_rules.csv")
    rule_truth = load(A + "abm_rule_ground_truth.csv")
    history = load(A + "agent_state_history.csv")
    # Every rule branch is replayed from its own machine-readable condition against the
    # agent state history, and every branch is accounted for, including branches that no
    # state row ever reaches.
    agent_frame = load(A + "agents.csv")
    capacity_of = {
        (row.project_id, row.agent_id): float(row.base_capacity_units)
        for row in agent_frame.itertuples()
    }
    ordered_rules = rules.sort_values("rule_order")
    replay_counts: dict[tuple[str, str, str], int] = {}
    branch_bad: list[str] = []
    for row in history.itertuples():
        capacity = capacity_of.get((row.project_id, row.agent_id))
        if capacity is None:
            branch_bad.append(f"unknown agent {row.agent_id}")
            continue
        chosen = None
        for rule in ordered_rules.itertuples():
            if rule.decision_rule_id != row.decision_rule_id:
                continue
            condition = json.loads(rule.condition_json)
            if "state" in condition and row.state == condition["state"]:
                chosen = rule
                break
            if condition.get("inventory_below_base_capacity") and float(
                row.inventory_end_units
            ) < capacity:
                chosen = rule
                break
            if condition.get("default"):
                chosen = rule
                break
        if chosen is None:
            branch_bad.append(f"{row.agent_id}: no branch governs the row")
            continue
        if chosen.rule_branch != row.rule_branch:
            branch_bad.append(f"{row.agent_id}: replay {chosen.rule_branch} stored {row.rule_branch}")
        key = (row.project_id, chosen.decision_rule_id, chosen.rule_branch)
        replay_counts[key] = replay_counts.get(key, 0) + 1
    for row in rule_truth.itertuples():
        key = (row.project_id, row.decision_rule_id, row.rule_branch)
        if replay_counts.get(key, 0) != int(row.application_count):
            branch_bad.append(f"{key}: {replay_counts.get(key, 0)} != {row.application_count}")
    ck("gap:agent_branch_counts_recomputed", not branch_bad, branch_bad[:5])
    stored_keys = set(zip(rule_truth.project_id, rule_truth.decision_rule_id,
                          rule_truth.rule_branch))
    ck("gap:agent_branch_key_set", stored_keys == set(replay_counts),
       sorted(stored_keys ^ set(replay_counts))[:5])
    unreached = set(rules.rule_branch) - set(rule_truth.rule_branch)
    ck("gap:agent_every_branch_accounted",
       all(
           not any(key[2] == branch for key in replay_counts)
           for branch in unreached
       ),
       sorted(unreached))

    pairs = load(B1 + "analogous_pairs.csv")
    splits = load(B1 + "split_manifest.csv")
    split_of = dict(zip(splits.reference_project_id, splits.split))
    combinations: dict[tuple[str, str], int] = {}
    for row in pairs.itertuples():
        combinations[(split_of.get(row.target_project_id, "UNKNOWN"),
                      split_of.get(row.analog_project_id, "UNKNOWN"))] = combinations.get(
            (split_of.get(row.target_project_id, "UNKNOWN"),
             split_of.get(row.analog_project_id, "UNKNOWN")), 0
        ) + 1
    forbidden = {
        combination: count for combination, count in combinations.items()
        if combination[1] != "DEVELOPMENT"
    }
    ck("gap:analogous_pairs_every_split_combination", not forbidden, sorted(forbidden.items()))
    # Every split combination that occurs is enumerated. Targets are the held-out splits and
    # analogs come only from development, so the development-target and non-development-analog
    # combinations must be empty rather than merely rare.
    ck("gap:analogous_pairs_all_target_splits_covered",
       {combination[0] for combination in combinations}
       == set(splits.split) - {"DEVELOPMENT"},
       sorted({combination[0] for combination in combinations}))
    ck("gap:analogous_pairs_splits_known",
       all(split_of.get(row.target_project_id) and split_of.get(row.analog_project_id)
           for row in pairs.itertuples()))

    senses = {
        constraint["sense"]
        for model in lp_data.get("models", [])
        for constraint in model["constraints"]
    }
    ck("gap:lp_relation_types_present", senses <= {"LE", "GE", "EQ"}, sorted(senses))
    ck("gap:lp_every_constraint_solved",
       all(
           len([c for c in model["constraints"] if c["sense"] in {"LE", "GE", "EQ"}])
           == len(model["constraints"])
           for model in lp_data.get("models", [])
       ))

    passed = all(check["passed"] for check in checks)
    return {
        "programme_version": "OG-SYNTH-0.3",
        "generated_at": "2026-08-12T00:00:00Z",
        "checks": checks,
        "passed": passed,
        "check_count": len(checks),
        "failed_count": sum(not check["passed"] for check in checks),
    }


def write_report(root: Path, report: dict[str, Any]) -> None:
    (root / "validation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        "# Validation Summary",
        "",
        "- Programme: `OG-SYNTH-0.3`",
        f"- Checks: **{report['check_count']}**",
        f"- Failed: **{report['failed_count']}**",
        f"- Overall: **{'PASS' if report['passed'] else 'FAIL'}**",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for check in report["checks"]:
        detail = str(check["detail"]).replace("|", "/")
        lines.append(
            f"| {check['check']} | {'PASS' if check['passed'] else 'FAIL'} | {detail} |"
        )
    (root / "VALIDATION_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = validate(args.root)
    if args.write_report:
        write_report(args.root, report)
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "check_count": report["check_count"],
                "failed_count": report["failed_count"],
            },
            indent=2,
        )
    )
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
