#!/usr/bin/env python3
"""Build the OG-SYNTH-0.2 audit CSVs: file inventory, checksum results, the
Run 8 Bucket 3/4/5 reconciliation and the prior-gap closure table.

The Run 8 module set is read from the committed classification, never typed in,
and set equality is asserted so drift fails rather than passing quietly.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "research_fixtures/synthetic/OG-SYNTH-0.2/Opus_Gubernatio_Synthetic_Programme_v0.2"
OUT = REPO / "code_audit"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def inventory() -> None:
    rows = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        rel = str(path.relative_to(ROOT))
        data = path.read_bytes()
        record_count = column_count = ""
        if path.suffix == ".csv":
            parsed = read_csv(path)
            record_count = str(len(parsed))
            column_count = str(len(parsed[0]) if parsed else 0)
        rows.append(
            {
                "relative_path": rel,
                "package": rel.split("/")[0] if "/" in rel else "ROOT",
                "bytes": str(len(data)),
                "sha256": hashlib.sha256(data).hexdigest(),
                "rows": record_count,
                "columns": column_count,
                "executable_bit": "yes" if path.stat().st_mode & 0o111 else "no",
            }
        )
    write_csv(
        OUT / "synthetic_v02_file_inventory.csv",
        rows,
        ["relative_path", "package", "bytes", "sha256", "rows", "columns", "executable_bit"],
    )
    print(f"inventory: {len(rows)} files")


def checksum_results() -> None:
    def load(path: Path) -> dict[str, str]:
        out = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                expected, rel = line.split("  ", 1)
                out[rel] = expected
        return out

    rows = []
    programme = load(ROOT / "CHECKSUMS.sha256")
    for rel, expected in programme.items():
        path = ROOT / rel
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""
        rows.append(
            {
                "manifest": "CHECKSUMS.sha256 (programme)",
                "relative_path": rel,
                "expected_sha256": expected,
                "recomputed_sha256": actual,
                "result": "MATCH" if actual == expected else ("MISSING" if not actual else "MISMATCH"),
            }
        )
    for package in (
        "package_A_project_structures",
        "package_B_reference_training_decisions",
        "package_C_optional_activation_lab",
    ):
        pdir = ROOT / package
        for rel, expected in load(pdir / "PACKAGE_CHECKSUMS.sha256").items():
            path = pdir / rel
            actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""
            rows.append(
                {
                    "manifest": f"{package}/PACKAGE_CHECKSUMS.sha256 (package-local)",
                    "relative_path": rel,
                    "expected_sha256": expected,
                    "recomputed_sha256": actual,
                    "result": "MATCH" if actual == expected else ("MISSING" if not actual else "MISMATCH"),
                }
            )
    write_csv(
        OUT / "synthetic_v02_checksum_results.csv",
        rows,
        ["manifest", "relative_path", "expected_sha256", "recomputed_sha256", "result"],
    )
    counts = {}
    for row in rows:
        counts[row["result"]] = counts.get(row["result"], 0) + 1
    print(f"checksums: {counts}")


RECONCILIATION = {
    # code id -> (required structure per Run 8, v0.2 assets, complete, remaining gap)
    "A1.1": (
        "cost risk quantification: three-point or distributional cost ranges per risk or work package",
        "cost_risk_events.csv|cost_elements.csv|cost_correlations.csv|cost_risk_ground_truth.csv",
        "yes",
        "no alias row: the module carries no entry in module_id_aliases.csv or module_asset_map.csv, so a "
        "repository join has to be made by hand",
    ),
    "A2.2": (
        "locations or units, crews, quantities and production rates",
        "lob_work_packages.csv|lob_ground_truth.csv",
        "yes",
        "none",
    ),
    "A2.3": (
        "a critical chain with a project buffer and feeding buffers sized from activity estimates",
        "ccpm_chains.csv|ccpm_chain_activities.csv|ccpm_buffer_sizing_inputs.csv|ccpm_buffers.csv|ccpm_ground_truth.csv",
        "yes",
        "none: every activity and buffer traces to a declared chain and every buffer recomputes from the "
        "RSS PERT variance at z = 1.645",
    ),
    "A4.4": (
        "an audited nonconformance cohort carrying a findings total",
        "quality_audits.csv|ncr_events.csv|ncr_ground_truth.csv",
        "yes",
        "none: the corpus that was absent in the prior version now exists and recomputes at every cutoff",
    ),
    "A5.6": (
        "arrival and service processes, capacity and a queue discipline",
        "queue_events.csv|queue_ground_truth.csv",
        "yes",
        "none",
    ),
    "A5.7": (
        "agents, states, rules and interactions",
        "agent_decision_rules.csv|agents.csv|agent_state_history.csv|abm_ground_truth.csv|abm_rule_ground_truth.csv",
        "yes",
        "one declared branch, the low inventory restock branch, is never exercised by the state history, so "
        "replay covers two of the three branches",
    ),
    "A6.3": (
        "audited permit condition compliance",
        "environmental_requirements.csv|environmental_assessments.csv|environmental_violations.csv|environmental_ground_truth.csv",
        "yes",
        "none: the corpus that was absent in the prior version now exists and recomputes at every period",
    ),
    "A5.4": (
        "an actions-by-scenarios payoff structure with defined scenarios and probabilities",
        "decision_problems.csv|actions.csv|scenarios.csv|action_scenario_outcomes.csv|payoff_matrices.csv|ground_truth_decisions.csv",
        "yes",
        "no alias row: the module carries no entry in module_id_aliases.csv or module_asset_map.csv, so a "
        "repository join has to be made by hand",
    ),
    "B2.19": (
        "an alternatives-by-criteria decision matrix, weights computed across alternatives",
        "alternative_criteria_matrix.csv|criteria.csv|ground_truth_decisions.csv",
        "yes",
        "none structurally; the degenerate single-alternative weighting remains a separate production decision",
    ),
    "A3.1": (
        "a population of comparable completed projects with realised overruns",
        "reference_projects.csv|reference_class_membership.csv|reference_outcomes.csv|split_manifest.csv",
        "yes",
        "none; the module stays disabled and abstaining regardless",
    ),
    "A5.1": (
        "a project-specific dependency matrix",
        "dsm_nodes.csv|dsm_edges.csv|dsm_ground_truth.csv",
        "yes",
        "none; Package A is now stated consistently as the boundary; the module stays disabled and abstaining",
    ),
}

PACKAGE_OF = {
    "A1.1": "A",
    "A2.2": "A",
    "A2.3": "A",
    "A4.4": "A",
    "A5.6": "A",
    "A5.7": "A",
    "A6.3": "A",
    "A5.4": "B3",
    "B2.19": "B3",
    "A3.1": "B1",
    "A5.1": "A",
}


def run8_reconciliation() -> None:
    classification = read_csv(REPO / "code_audit/run8_module_classification.csv")
    run8 = {
        r["module_id"]: r
        for r in classification
        if r["final_owner_action_bucket"] in ("3", "4", "5")
    }
    assert set(run8) == set(RECONCILIATION), (
        f"Run 8 bucket 3/4/5 set drift: only in classification {set(run8) - set(RECONCILIATION)}, "
        f"only in reconciliation {set(RECONCILIATION) - set(run8)}"
    )
    aliases = {r["code_module_id"]: r for r in read_csv(ROOT / "module_id_aliases.csv")}
    rows = []
    A = ROOT / "package_A_project_structures"
    B1 = ROOT / "package_B_reference_training_decisions/B1_reference_population"
    B3 = ROOT / "package_B_reference_training_decisions/B3_decision_optimization"
    for code_id, run8_row in sorted(run8.items()):
        structure, assets, complete, gap = RECONCILIATION[code_id]
        present = []
        for name in assets.split("|"):
            found = any((base / name).exists() for base in (A, B1, B3))
            present.append(f"{name}:{'present' if found else 'ABSENT'}")
            if not found:
                complete, gap = "no", f"asset {name} not found in the package"
        rows.append(
            {
                "code_module_id": code_id,
                "literature_module_id": aliases.get(code_id, {}).get("literature_module_id", "not mapped"),
                "module": run8_row["module_name"],
                "run8_bucket": run8_row["final_owner_action_bucket"],
                "package": PACKAGE_OF[code_id],
                "required_structure": structure,
                "v02_assets": " ".join(present),
                "complete": complete,
                "remaining_gap": gap,
            }
        )
    write_csv(
        OUT / "synthetic_v02_run8_reconciliation.csv",
        rows,
        [
            "code_module_id",
            "literature_module_id",
            "module",
            "run8_bucket",
            "package",
            "required_structure",
            "v02_assets",
            "complete",
            "remaining_gap",
        ],
    )
    complete_count = sum(1 for r in rows if r["complete"] == "yes")
    print(f"run8 reconciliation: {complete_count}/{len(rows)} complete")


def gap_closure(independent_csv: Path) -> None:
    checks = read_csv(independent_csv) if independent_csv.exists() else []

    def verdict(area: str) -> str:
        rows = [r for r in checks if r["area"] == area]
        if not rows:
            return "not run"
        failed = [r for r in rows if r["result"] == "FAIL"]
        return f"{len(rows) - len(failed)} of {len(rows)} independent checks pass"

    rows = [
        {
            "prior_finding": "1. NCR Rate corpus absent",
            "closed": "yes",
            "evidence": "quality_audits.csv, ncr_events.csv and ncr_ground_truth.csv exist; issued, closed, "
            "open, overdue, cumulative inspections, incidence per hundred inspections, closure ratio, open "
            "ratio, overdue open ratio and mean open age recomputed from the event rows at all 36 cutoffs",
            "independent_checks": verdict("ncr"),
            "residual": "none",
        },
        {
            "prior_finding": "2. Environmental Compliance Rate corpus absent",
            "closed": "yes",
            "evidence": "requirements, assessments, violations and ground truth exist; applicable, assessed, "
            "compliant, noncompliant, unassessed, the compliance rate and severe noncompliances recomputed at "
            "all 36 periods",
            "independent_checks": verdict("env"),
            "residual": "none",
        },
        {
            "prior_finding": "3. CCPM buffers untraceable and flat fifteen per cent",
            "closed": "yes",
            "evidence": "every chain activity, buffer and sizing input traces to a declared chain; PERT sigma "
            "and variance recomputed from the three-point estimates; every original buffer recomputed as "
            "1.645 times the root of the summed variance; no chain matches a flat fifteen per cent of chain length",
            "independent_checks": verdict("ccpm"),
            "residual": "none",
        },
        {
            "prior_finding": "4. Agent interaction rules undefined",
            "closed": "yes",
            "evidence": "agent_decision_rules.csv defines the rules; every condition and action parses as a JSON "
            "object; every branch in the state history resolves; branch selection replayed independently for all "
            "576 state rows and branch counts reproduced for all 12 ground-truth rows",
            "independent_checks": verdict("abm"),
            "residual": "the low inventory restock branch is declared but never exercised, so replay covers two "
            "of the three declared branches",
        },
        {
            "prior_finding": "5. DSM package boundary contradiction",
            "closed": "yes",
            "evidence": "Package A is stated in module_asset_map.csv, module_id_aliases.csv, the Package A "
            "README and AUDIT_RESOLUTION_v0.2.md, and the DSM files are physically in Package A",
            "independent_checks": verdict("dsm"),
            "residual": "none",
        },
        {
            "prior_finding": "6. Linear programming models were prose, not solvable",
            "closed": "yes",
            "evidence": "lp_models.json carries numeric objective coefficient vectors, numeric variable bounds, "
            "numeric constraint coefficient vectors, right-hand sides, senses, a solver reference and a "
            "ground-truth solution and objective; all 12 models solved independently reproduce the stored "
            "objective and success flag",
            "independent_checks": verdict("lp"),
            "residual": "none",
        },
        {
            "prior_finding": "7. Divergent module numbering",
            "closed": "partly",
            "evidence": "module_id_aliases.csv is a genuine one-to-one mapping in both directions and carries "
            "7.19 to B2.19, 4.4 to A4.4 and 8.8 to A6.3; the asset map agrees with it on every row it covers",
            "independent_checks": verdict("aliases"),
            "residual": "two of the eleven Run 8 modules in scope, Monte Carlo EAC and Scenario Modeling, have "
            "no row in either the alias table or the asset map, so those two joins remain manual",
        },
    ]
    write_csv(
        OUT / "synthetic_v02_gap_closure.csv",
        rows,
        ["prior_finding", "closed", "evidence", "independent_checks", "residual"],
    )
    print(f"gap closure: {sum(1 for r in rows if r['closed'] == 'yes')} of {len(rows)} fully closed")


def main() -> int:
    inventory()
    checksum_results()
    run8_reconciliation()
    gap_closure(OUT / "synthetic_v02_independent_checks.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
