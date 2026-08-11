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
        "generators/build_opus_synthetic_programme_v0_2.py",
        "generators/validate_synthetic_programme_v0_2.py",
        "generators/verify_synthetic_checksums_v0_2.py",
        "generators/base/Opus_Gubernatio_Synthetic_Programme_v0.1.zip",
        "requirements-lock.txt",
        "AUDIT_RESOLUTION_v0.2.md",
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

    passed = all(check["passed"] for check in checks)
    return {
        "programme_version": "OG-SYNTH-0.2",
        "generated_at": "2026-08-11T00:00:00Z",
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
        "- Programme: `OG-SYNTH-0.2`",
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
