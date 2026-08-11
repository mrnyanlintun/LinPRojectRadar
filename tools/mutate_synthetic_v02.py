#!/usr/bin/env python3
"""Fault-injection proof for the OG-SYNTH-0.2 validator.

Each injection is applied to a discarded scratch copy of the staged fixture,
never to the authoritative extraction. Every injection is confirmed to have
actually changed bytes on disk before the validator is rerun, so a silently
inert injection cannot report a false clean.

Writes code_audit/synthetic_v02_mutation_proof.csv.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "research_fixtures/synthetic/OG-SYNTH-0.2/Opus_Gubernatio_Synthetic_Programme_v0.2"
A = "package_A_project_structures"
B1 = "package_B_reference_training_decisions/B1_reference_population"
B3 = "package_B_reference_training_decisions/B3_decision_optimization"


def edit_csv(path: Path, mutate) -> None:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    fields = list(rows[0].keys())
    mutate(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def m_ccpm_fk(root: Path) -> str:
    path = root / A / "ccpm_chain_activities.csv"

    def go(rows):
        rows[0]["chain_id"] = "PRJ-AIR-CC-DOES-NOT-EXIST"

    edit_csv(path, go)
    return "ccpm_chain_activities.csv row 1 chain_id repointed to an undeclared chain"


def m_agent_fk(root: Path) -> str:
    path = root / A / "agents.csv"

    def go(rows):
        rows[0]["decision_rule_id"] = "RULE_THAT_WAS_NEVER_DECLARED"

    edit_csv(path, go)
    return "agents.csv row 1 decision_rule_id repointed to an undeclared rule"


def m_ncr(root: Path) -> str:
    path = root / A / "ncr_ground_truth.csv"

    def go(rows):
        for row in rows:
            if int(row["ncr_issued_to_date"]) > 0:
                row["ncr_issued_to_date"] = str(int(row["ncr_issued_to_date"]) + 3)
                break

    edit_csv(path, go)
    return "ncr_ground_truth.csv issued count inflated by three at one cutoff"


def m_env(root: Path) -> str:
    path = root / A / "environmental_ground_truth.csv"

    def go(rows):
        rows[0]["environmental_compliance_rate"] = "0.99999999"

    edit_csv(path, go)
    return "environmental_ground_truth.csv compliance rate overwritten at one period"


def m_lp(root: Path) -> str:
    path = root / B3 / "lp_models.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["models"][0]["objective"]["coefficients"][0] *= 1.75
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return "lp_models.json first objective coefficient scaled by 1.75"


def m_alias(root: Path) -> str:
    path = root / "module_id_aliases.csv"

    def go(rows):
        for row in rows:
            if row["code_module_id"] == "A2.2":
                row["code_module_id"] = "A2.3"  # collide with CCPM Buffer Health
                break

    edit_csv(path, go)
    return "module_id_aliases.csv code id A2.2 collided onto A2.3"


def m_leakage(root: Path) -> str:
    projects = root / B1 / "reference_projects.csv"
    rows = list(csv.DictReader(projects.open(newline="", encoding="utf-8")))
    fields = list(rows[0].keys())
    source = next(r for r in rows if r["split"] == "LOCKED_HOLDOUT")
    target = next(r for r in rows if r["split"] == "DEVELOPMENT")
    for column in (
        "project_type",
        "delivery_method",
        "region",
        "baseline_cost_usd",
        "baseline_duration_days",
        "complexity_index",
    ):
        target[column] = source[column]
    with projects.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return (
        f"reference_projects.csv development project {target['reference_project_id']} "
        f"given the feature vector of locked-holdout {source['reference_project_id']}"
    )


INJECTIONS = [
    ("CCPM chain foreign-key break", m_ccpm_fk),
    ("Agent decision-rule foreign-key break", m_agent_fk),
    ("NCR ground-truth mismatch", m_ncr),
    ("Environmental compliance-rate mismatch", m_env),
    ("LP coefficient change", m_lp),
    ("Module-ID alias collision", m_alias),
    ("Train/validation/holdout leakage", m_leakage),
]


def run_validator(root: Path) -> tuple[int, list[str], int]:
    script = root / "generators/validate_synthetic_programme_v0_2.py"
    code = (
        "import json,sys;sys.path.insert(0,%r);"
        "import importlib.util;"
        "spec=importlib.util.spec_from_file_location('v',%r);"
        "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
        "from pathlib import Path;"
        "r=m.validate(Path(%r));"
        "print(json.dumps({'count':r['check_count'],'failed':r['failed_count'],"
        "'names':[c['check'] for c in r['checks'] if not c['passed']]}))"
    ) % (str(root / "generators"), str(script), str(root))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    payload = json.loads(out.stdout.strip().splitlines()[-1])
    return payload["failed"], payload["names"], payload["count"]


def main() -> int:
    results = []
    baseline_failed, baseline_names, baseline_count = run_validator(ROOT)
    print(f"baseline: {baseline_count} checks, {baseline_failed} failed")
    results.append(
        {
            "injection": "BASELINE (authoritative extraction, unmodified)",
            "scratch_copy": "n/a",
            "injection_applied": "n/a",
            "validator_checks": baseline_count,
            "validator_failures": baseline_failed,
            "detected": "n/a",
            "named_checks": "",
        }
    )

    for label, mutate in INJECTIONS:
        with tempfile.TemporaryDirectory(prefix="og-synth-scratch-") as tmp:
            scratch = Path(tmp) / "root"
            shutil.copytree(ROOT, scratch)
            before = {p: p.read_bytes() for p in scratch.rglob("*") if p.is_file()}
            detail = mutate(scratch)
            after = {p: p.read_bytes() for p in scratch.rglob("*") if p.is_file()}
            changed = [str(p.relative_to(scratch)) for p in after if before.get(p) != after[p]]
            applied = bool(changed)
            failed, names, count = run_validator(scratch)
            detected = applied and failed > baseline_failed
            results.append(
                {
                    "injection": label,
                    "scratch_copy": str(scratch),
                    "injection_applied": f"yes: {detail} (bytes changed in {changed})"
                    if applied
                    else "NO - injection did not change any bytes",
                    "validator_checks": count,
                    "validator_failures": failed,
                    "detected": "yes" if detected else "NO",
                    "named_checks": "; ".join(names[:6]),
                }
            )
            print(f"{label}: applied={applied} failures={failed} named={names[:4]}")

    recheck_failed, _, recheck_count = run_validator(ROOT)
    results.append(
        {
            "injection": "BASELINE RECHECK after all scratch copies discarded",
            "scratch_copy": "n/a",
            "injection_applied": "n/a",
            "validator_checks": recheck_count,
            "validator_failures": recheck_failed,
            "detected": "n/a",
            "named_checks": "",
        }
    )
    out = REPO / "code_audit/synthetic_v02_mutation_proof.csv"
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    undetected = [r["injection"] for r in results if r["detected"] == "NO"]
    print(f"recheck: {recheck_count} checks, {recheck_failed} failed")
    print(f"undetected injections: {undetected}")
    return 1 if undetected or recheck_failed else 0


if __name__ == "__main__":
    sys.exit(main())
