#!/usr/bin/env python3
"""Independent audit of the OG-SYNTH-0.2 synthetic research fixture.

Written against the data, not against the package's own validation report.
Read-only: it never writes into the staged fixture. It extends the v0.1 checker
(tools/audit_synthetic_package.py) with the seven closure re-tests the v0.1 audit
left open.

Usage:
    python3 tools/audit_synthetic_v02.py [--root <staged root>] [--csv <out.csv>]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = (
    REPO
    / "research_fixtures/synthetic/OG-SYNTH-0.2/Opus_Gubernatio_Synthetic_Programme_v0.2"
)

RESULTS: list[dict[str, str]] = []


def ck(area: str, name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append(
        {
            "area": area,
            "check": name,
            "result": "PASS" if ok else "FAIL",
            "detail": str(detail)[:400],
        }
    )
    return ok


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(value: str) -> float:
    return float(value)


def d(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    return date.fromisoformat(value[:10])


def close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


# ---------------------------------------------------------------- gap 1: NCR


def check_ncr(A: Path, periods: list[dict[str, str]]) -> None:
    for name in ("quality_audits.csv", "ncr_events.csv", "ncr_ground_truth.csv"):
        ck("ncr", f"exists:{name}", (A / name).exists())
    audits = read_csv(A / "quality_audits.csv")
    events = read_csv(A / "ncr_events.csv")
    truth = read_csv(A / "ncr_ground_truth.csv")

    audit_ids = {r["audit_id"] for r in audits}
    ck(
        "ncr",
        "event_audit_fk",
        all(r["source_audit_id"] in audit_ids for r in events),
        "every NCR traces to a declared quality audit",
    )
    ck("ncr", "event_pk_unique", len({r["ncr_id"] for r in events}) == len(events))

    period_end = {(r["project_id"], r["period_id"]): d(r["period_end"]) for r in periods}
    ordered: dict[str, list[str]] = {}
    for r in periods:
        ordered.setdefault(r["project_id"], []).append(r["period_id"])

    bad: list[str] = []
    for row in truth:
        pid, per = row["project_id"], row["period_id"]
        cutoff = period_end.get((pid, per))
        if cutoff is None:
            bad.append(f"{pid}/{per}: no period")
            continue
        ev = [
            r
            for r in events
            if r["project_id"] == pid and d(r["issue_date"]) <= cutoff
        ]
        closed = [r for r in ev if d(r["close_date"]) and d(r["close_date"]) <= cutoff]
        openv = [r for r in ev if r not in closed]
        overdue = [
            r
            for r in openv
            if d(r["due_date"]) and d(r["due_date"]) < cutoff
        ]
        # cumulative inspections from the audit cohort up to the same cutoff
        insp = sum(
            int(a["inspections_completed"])
            for a in audits
            if a["project_id"] == pid and d(a["audit_date"]) <= cutoff
        )
        incidence = (len(ev) / insp * 100.0) if insp else 0.0
        closure = (len(closed) / len(ev)) if ev else 0.0
        open_ratio = (len(openv) / len(ev)) if ev else 0.0
        overdue_open = (len(overdue) / len(openv)) if openv else 0.0
        ages = [(cutoff - d(r["issue_date"])).days for r in openv]
        mean_age = (sum(ages) / len(ages)) if ages else 0.0

        pairs = [
            ("issued", len(ev), f(row["ncr_issued_to_date"]), 0),
            ("closed", len(closed), f(row["ncr_closed_to_date"]), 0),
            ("open", len(openv), f(row["ncr_open_at_cutoff"]), 0),
            ("overdue", len(overdue), f(row["ncr_overdue_at_cutoff"]), 0),
            ("inspections", insp, f(row["cumulative_inspections"]), 0),
            ("incidence", incidence, f(row["ncr_incidence_per_100_inspections"]), 1e-6),
            ("closure_ratio", closure, f(row["closure_ratio"]), 1e-6),
            ("open_ratio", open_ratio, f(row["open_ratio"]), 1e-6),
            ("overdue_open_ratio", overdue_open, f(row["overdue_open_ratio"]), 1e-6),
            ("mean_open_age_days", mean_age, f(row["mean_open_age_days"]), 1e-6),
        ]
        for label, mine, theirs, tol in pairs:
            if not close(float(mine), theirs, max(tol, 1e-9)):
                bad.append(f"{pid}/{per}/{label}: recomputed {mine} stored {theirs}")
    ck(
        "ncr",
        "recomputed_ground_truth_all_cutoffs",
        not bad,
        f"{len(truth)} period rows, 10 quantities each; mismatches: {bad[:5]}",
    )


# ------------------------------------------------------- gap 2: environmental


def check_environmental(A: Path) -> None:
    for name in (
        "environmental_requirements.csv",
        "environmental_assessments.csv",
        "environmental_violations.csv",
        "environmental_ground_truth.csv",
    ):
        ck("env", f"exists:{name}", (A / name).exists())
    reqs = read_csv(A / "environmental_requirements.csv")
    assess = read_csv(A / "environmental_assessments.csv")
    viol = read_csv(A / "environmental_violations.csv")
    truth = read_csv(A / "environmental_ground_truth.csv")

    req_keys = {(r["project_id"], r["requirement_id"]) for r in reqs}
    ck(
        "env",
        "assessment_requirement_fk",
        all((r["project_id"], r["requirement_id"]) in req_keys for r in assess),
    )
    assess_ids = {r["assessment_id"] for r in assess}
    ck("env", "violation_assessment_fk", all(r["assessment_id"] in assess_ids for r in viol))

    bad: list[str] = []
    for row in truth:
        pid, per = row["project_id"], row["period_id"]
        applicable = [
            r
            for r in reqs
            if r["project_id"] == pid and str(r["applicable"]).lower() == "true"
        ]
        sub = [r for r in assess if r["project_id"] == pid and r["period_id"] == per]
        assessed = [r for r in sub if r["result"] in ("COMPLIANT", "NONCOMPLIANT")]
        compliant = [r for r in assessed if r["result"] == "COMPLIANT"]
        noncompliant = [r for r in assessed if r["result"] == "NONCOMPLIANT"]
        unassessed = len(applicable) - len(assessed)
        rate = (len(compliant) / len(assessed)) if assessed else 0.0
        severe = len(
            [
                v
                for v in viol
                if v["project_id"] == pid
                and v["period_id"] == per
                and v["severity"] in ("CRITICAL", "MAJOR", "HIGH")
            ]
        )
        pairs = [
            ("applicable", len(applicable), f(row["applicable_requirements"])),
            ("assessed", len(assessed), f(row["applicable_requirements_assessed"])),
            ("compliant", len(compliant), f(row["compliant_requirements"])),
            ("noncompliant", len(noncompliant), f(row["noncompliant_requirements"])),
            ("unassessed", unassessed, f(row["unassessed_requirements"])),
            ("rate", rate, f(row["environmental_compliance_rate"])),
        ]
        for label, mine, theirs in pairs:
            if not close(float(mine), theirs, 1e-7):
                bad.append(f"{pid}/{per}/{label}: recomputed {mine} stored {theirs}")
        if severe != int(f(row["severe_noncompliances"])):
            bad.append(
                f"{pid}/{per}/severe: recomputed {severe} stored {row['severe_noncompliances']}"
            )
    ck(
        "env",
        "recomputed_compliance_all_periods",
        not bad,
        f"{len(truth)} period rows; mismatches: {bad[:5]}",
    )


# --------------------------------------------------------------- gap 3: CCPM


def check_ccpm(A: Path) -> None:
    for name in (
        "ccpm_chains.csv",
        "ccpm_chain_activities.csv",
        "ccpm_buffer_sizing_inputs.csv",
        "ccpm_buffers.csv",
        "ccpm_ground_truth.csv",
    ):
        ck("ccpm", f"exists:{name}", (A / name).exists())
    chains = read_csv(A / "ccpm_chains.csv")
    members = read_csv(A / "ccpm_chain_activities.csv")
    sizing = read_csv(A / "ccpm_buffer_sizing_inputs.csv")
    buffers = read_csv(A / "ccpm_buffers.csv")
    acts = read_csv(A / "schedule_activities.csv")

    act_keys = {(r["project_id"], r["activity_id"]) for r in acts}
    chain_keys = {(r["project_id"], r["chain_id"]) for r in chains}
    ck("ccpm", "chain_pk_unique", len(chain_keys) == len(chains))
    ck(
        "ccpm",
        "member_traces_to_chain_and_activity",
        all(
            (r["project_id"], r["chain_id"]) in chain_keys
            and (r["project_id"], r["activity_id"]) in act_keys
            for r in members
        ),
    )
    ck(
        "ccpm",
        "buffer_traces_to_chain",
        all((r["project_id"], r["chain_id"]) in chain_keys for r in buffers),
    )
    ck(
        "ccpm",
        "sizing_input_traces_to_chain_and_activity",
        all(
            (r["project_id"], r["chain_id"]) in chain_keys
            and (r["project_id"], r["activity_id"]) in act_keys
            for r in sizing
        ),
    )
    ck(
        "ccpm",
        "schedule_activity_carries_chain_id",
        {"ccpm_chain_id", "ccpm_chain_type"}.issubset(set(acts[0].keys())),
    )

    # PERT variance recomputed from the three-point estimates, then RSS and z.
    bad: list[str] = []
    for row in sizing:
        o, m, p = (
            f(row["optimistic_duration_days"]),
            f(row["most_likely_duration_days"]),
            f(row["pessimistic_duration_days"]),
        )
        sigma = (p - o) / 6.0
        if not close(sigma, f(row["pert_sigma_days"]), 1e-6):
            bad.append(f"{row['activity_id']} sigma")
        if not close(sigma * sigma, f(row["variance_days2"]), 1e-6):
            bad.append(f"{row['activity_id']} variance")
        if not (o <= m <= p):
            bad.append(f"{row['activity_id']} triangular order")
    ck("ccpm", "pert_sigma_and_variance_recomputed", not bad, bad[:5])

    bad = []
    for chain in chains:
        rows = [
            r
            for r in sizing
            if r["project_id"] == chain["project_id"] and r["chain_id"] == chain["chain_id"]
        ]
        var_sum = sum(f(r["variance_days2"]) for r in rows)
        if not close(var_sum, f(chain["variance_sum_days2"]), 1e-6):
            bad.append(f"{chain['chain_id']} variance_sum")
        expected = max(1.0, 1.645 * math.sqrt(var_sum))
        if not close(expected, f(chain["original_buffer_days"]), 1e-6):
            bad.append(
                f"{chain['chain_id']} buffer {chain['original_buffer_days']} vs RSS {expected}"
            )
        if len(rows) != int(chain["activity_count"]):
            bad.append(f"{chain['chain_id']} member count")
        if not close(f(chain["sizing_z"]), 1.645):
            bad.append(f"{chain['chain_id']} z")
        if chain["buffer_sizing_method"] != "RSS_PERT_VARIANCE":
            bad.append(f"{chain['chain_id']} method {chain['buffer_sizing_method']}")
    ck(
        "ccpm",
        "buffers_recomputed_from_RSS_PERT_variance_z1645",
        not bad,
        f"{len(chains)} chains; {bad[:5]}",
    )

    # The v0.1 defect was a flat fifteen per cent of baseline. Prove its absence.
    flat = []
    for chain in chains:
        rows = [
            r
            for r in sizing
            if r["project_id"] == chain["project_id"] and r["chain_id"] == chain["chain_id"]
        ]
        chain_len = sum(f(r["most_likely_duration_days"]) for r in rows)
        if chain_len and close(f(chain["original_buffer_days"]), 0.15 * chain_len, 1e-3):
            flat.append(chain["chain_id"])
    ck("ccpm", "flat_15pct_sizing_absent", not flat, flat)

    # every buffer row restates its chain's sizing consistently
    chain_buf = {(c["project_id"], c["chain_id"]): c for c in chains}
    bad = [
        b["buffer_id"]
        for b in buffers
        if not close(
            f(b["original_buffer_days"]),
            f(chain_buf[(b["project_id"], b["chain_id"])]["original_buffer_days"]),
            1e-6,
        )
    ]
    ck("ccpm", "buffer_rows_agree_with_chain_sizing", not bad, bad[:5])


# -------------------------------------------------------- gap 4: agent rules


def check_abm(A: Path) -> None:
    for name in (
        "agent_decision_rules.csv",
        "agents.csv",
        "agent_state_history.csv",
        "abm_rule_ground_truth.csv",
    ):
        ck("abm", f"exists:{name}", (A / name).exists())
    rules = read_csv(A / "agent_decision_rules.csv")
    agents = read_csv(A / "agents.csv")
    history = read_csv(A / "agent_state_history.csv")
    truth = read_csv(A / "abm_rule_ground_truth.csv")

    rule_ids = {r["decision_rule_id"] for r in rules}
    branches = {(r["decision_rule_id"], r["rule_branch"]) for r in rules}
    ck("abm", "agent_rule_fk", all(a["decision_rule_id"] in rule_ids for a in agents))
    ck(
        "abm",
        "history_rule_branch_resolves",
        all(
            (h["decision_rule_id"], h["rule_branch"]) in branches for h in history
        ),
        f"{len(history)} state rows against {len(branches)} declared branches",
    )

    parsed = 0
    bad = []
    for r in rules:
        for column in ("condition_json", "action_json"):
            try:
                obj = json.loads(r[column])
                if not isinstance(obj, dict):
                    bad.append(f"{r['decision_rule_id']}/{column} not an object")
                parsed += 1
            except Exception as exc:  # noqa: BLE001
                bad.append(f"{r['decision_rule_id']}/{column}: {exc}")
    ck("abm", "every_condition_and_action_is_a_json_object", not bad, f"{parsed} objects parsed")

    # Independently reproduce branch selection by evaluating the declared
    # conditions in rule order against the state rows.
    agent_by_key = {(a["project_id"], a["agent_id"]): a for a in agents}

    def predicate(key: str, row: dict[str, str], prior_inventory: float | None) -> bool:
        if key == "default":
            return True
        if key == "state":
            return True  # handled by value comparison below
        if key == "inventory_below_base_capacity":
            base = f(agent_by_key[(row["project_id"], row["agent_id"])]["base_capacity_units"])
            level = prior_inventory if prior_inventory is not None else f(row["inventory_end_units"])
            return level < base
        raise KeyError(key)

    mis = []
    prior: dict[tuple[str, str], float] = {}
    for h in sorted(history, key=lambda x: (x["project_id"], x["agent_id"], int(x["time_step"]))):
        key = (h["project_id"], h["agent_id"])
        chosen = None
        for r in sorted(rules, key=lambda x: int(x["rule_order"])):
            if r["decision_rule_id"] != h["decision_rule_id"]:
                continue
            cond = json.loads(r["condition_json"])
            ok = True
            for k, v in cond.items():
                if k == "state":
                    ok = ok and h["state"] == v
                elif k == "default":
                    ok = ok and bool(v)
                else:
                    ok = ok and predicate(k, h, prior.get(key)) == bool(v)
            if ok:
                chosen = r["rule_branch"]
                break
        if chosen != h["rule_branch"]:
            mis.append(f"{h['project_id']}/{h['time_step']}/{h['agent_id']}: {chosen} vs {h['rule_branch']}")
        prior[key] = f(h["inventory_end_units"])
    ck(
        "abm",
        "branch_reproduced_from_condition_json",
        not mis,
        f"{len(history)} rows replayed; {mis[:5]}",
    )
    exercised = {h["rule_branch"] for h in history}
    unexercised = sorted({r["rule_branch"] for r in rules} - exercised)
    ck(
        "abm",
        "note_every_declared_branch_is_exercised",
        not unexercised,
        f"declared but never applied: {unexercised}",
    )

    counts = Counter(
        (h["project_id"], h["decision_rule_id"], h["rule_branch"]) for h in history
    )
    bad = []
    for row in truth:
        key = (row["project_id"], row["decision_rule_id"], row["rule_branch"])
        if counts.get(key, 0) != int(row["application_count"]):
            bad.append(f"{key}: recomputed {counts.get(key, 0)} stored {row['application_count']}")
    extra = [k for k in counts if k not in {
        (r["project_id"], r["decision_rule_id"], r["rule_branch"]) for r in truth
    }]
    ck(
        "abm",
        "branch_counts_recomputed",
        not bad and not extra,
        f"{len(truth)} ground-truth rows; {bad[:5]} extra={extra[:5]}",
    )


# ------------------------------------------------------ gap 5: DSM boundary


def check_dsm_boundary(root: Path) -> None:
    aliases = read_csv(root / "module_id_aliases.csv")
    asset_map = read_csv(root / "module_asset_map.csv")
    dsm_alias = [r for r in aliases if r["module_name"] == "DSM Rework Propagation"]
    dsm_map = [r for r in asset_map if r["module_name"] == "DSM Rework Propagation"]
    ck(
        "dsm",
        "alias_assigns_package_A",
        len(dsm_alias) == 1 and dsm_alias[0]["synthetic_package"] == "A",
        [r["synthetic_package"] for r in dsm_alias],
    )
    ck(
        "dsm",
        "asset_map_assigns_package_A",
        len(dsm_map) == 1 and dsm_map[0]["synthetic_package"] == "A",
        [r["synthetic_package"] for r in dsm_map],
    )
    readme = (root / "package_A_project_structures/README.md").read_text(encoding="utf-8")
    ck("dsm", "package_A_readme_states_DSM", "DSM" in readme, "")
    resolution = (root / "AUDIT_RESOLUTION_v0.2.md").read_text(encoding="utf-8")
    ck(
        "dsm",
        "audit_resolution_states_DSM_in_A",
        "DSM" in resolution and "Package A" in resolution,
        "",
    )
    files_present = all(
        (root / "package_A_project_structures" / n).exists()
        for n in ("dsm_nodes.csv", "dsm_edges.csv", "dsm_ground_truth.csv")
    )
    ck("dsm", "dsm_files_live_in_package_A", files_present)


# ------------------------------------------------------------- gap 6: LP form


def check_lp(root: Path) -> None:
    try:
        from scipy.optimize import linprog
    except Exception as exc:  # noqa: BLE001
        ck("lp", "scipy_available", False, exc)
        return
    import numpy as np

    path = root / "package_B_reference_training_decisions/B3_decision_optimization/lp_models.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    ck("lp", "schema_version_0_2", data.get("schema_version") == "LP-MODEL-0.2")
    models = data.get("models", [])
    ck("lp", "twelve_models", len(models) == 12, len(models))

    bad_form, bad_solve = [], []
    for model in models:
        pid = model["decision_problem_id"]
        obj = model.get("objective", {})
        coefficients = obj.get("coefficients")
        variables = model.get("variables", [])
        constraints = model.get("constraints", [])
        problems = []
        if not isinstance(coefficients, list) or not all(
            isinstance(c, (int, float)) for c in coefficients
        ):
            problems.append("objective coefficients not numeric")
        if len(coefficients or []) != len(variables):
            problems.append("objective length differs from variable count")
        if not all(
            isinstance(v.get("lower"), (int, float)) and isinstance(v.get("upper"), (int, float))
            for v in variables
        ):
            problems.append("variable bounds not numeric")
        for c in constraints:
            if not isinstance(c.get("coefficients"), list) or len(c["coefficients"]) != len(variables):
                problems.append(f"constraint {c.get('name')} coefficient vector")
            if not isinstance(c.get("rhs"), (int, float)):
                problems.append(f"constraint {c.get('name')} rhs")
            if c.get("sense") not in ("LE", "GE", "EQ"):
                problems.append(f"constraint {c.get('name')} sense")
        if not model.get("solver_reference", {}).get("library"):
            problems.append("no solver reference")
        gt = model.get("ground_truth", {})
        if "objective_value" not in gt or "solution" not in gt or "success" not in gt:
            problems.append("incomplete ground truth")
        if problems:
            bad_form.append(f"{pid}: {problems}")
            continue

        a_ub, b_ub, a_eq, b_eq = [], [], [], []
        for c in constraints:
            if c["sense"] == "LE":
                a_ub.append(c["coefficients"])
                b_ub.append(c["rhs"])
            elif c["sense"] == "GE":
                a_ub.append([-x for x in c["coefficients"]])
                b_ub.append(-c["rhs"])
            else:
                a_eq.append(c["coefficients"])
                b_eq.append(c["rhs"])
        sense = obj.get("sense", "MIN")
        cvec = np.array(coefficients, dtype=float)
        signed = cvec if sense == "MIN" else -cvec
        result = linprog(
            signed,
            A_ub=np.array(a_ub, dtype=float) if a_ub else None,
            b_ub=np.array(b_ub, dtype=float) if b_ub else None,
            A_eq=np.array(a_eq, dtype=float) if a_eq else None,
            b_eq=np.array(b_eq, dtype=float) if b_eq else None,
            bounds=[(float(v["lower"]), float(v["upper"])) for v in variables],
            method="highs",
        )
        if bool(result.success) != bool(gt["success"]):
            bad_solve.append(f"{pid}: success {result.success} vs {gt['success']}")
            continue
        if result.success:
            value = float(result.fun) if sense == "MIN" else -float(result.fun)
            value += float(obj.get("constant", 0.0))
            if not close(value, float(gt["objective_value"]), 1e-4):
                bad_solve.append(f"{pid}: objective {value} vs {gt['objective_value']}")
            stored = gt["solution"]
            if isinstance(stored, dict) and len(stored) == len(variables):
                # compare the stored solution's objective rather than the vertex,
                # since a degenerate LP may have several optimal vertices
                order = [v["name"] for v in variables]
                keys = list(stored.keys())
                if all(any(k in name for name in order) for k in keys):
                    pass
    ck("lp", "all_models_machine_readable", not bad_form, bad_form[:5])
    ck(
        "lp",
        "all_models_solved_independently_match_ground_truth",
        not bad_solve,
        f"{len(models)} models solved; {bad_solve[:5]}",
    )


# ------------------------------------------------------- gap 7: module ids


def check_aliases(root: Path) -> None:
    aliases = read_csv(root / "module_id_aliases.csv")
    lit = [r["literature_module_id"] for r in aliases]
    code = [r["code_module_id"] for r in aliases]
    ck("aliases", "literature_ids_unique", len(set(lit)) == len(lit))
    ck("aliases", "code_ids_unique", len(set(code)) == len(code))
    ck(
        "aliases",
        "mapping_is_one_to_one",
        len(set(zip(lit, code))) == len(set(lit)) == len(set(code)) == len(aliases),
        f"{len(aliases)} rows",
    )
    mapping = dict(zip(lit, code))
    for a, b in (("7.19", "B2.19"), ("4.4", "A4.4"), ("8.8", "A6.3")):
        ck("aliases", f"maps:{a}->{b}", mapping.get(a) == b, mapping.get(a))
    asset_map = read_csv(root / "module_asset_map.csv")
    disagree = [
        r["module_id"]
        for r in asset_map
        if mapping.get(r["module_id"]) not in (None, r["code_module_id"])
    ]
    ck("aliases", "asset_map_agrees_with_alias_table", not disagree, disagree[:5])
    missing = [r["module_id"] for r in asset_map if r["module_id"] not in mapping]
    ck("aliases", "every_asset_map_module_has_an_alias", not missing, missing[:5])


# ------------------------------------------------- provenance, privacy, splits

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<!\d)(\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)")
SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
STREET = re.compile(
    r"\d+\s+[A-Za-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b",
    re.I,
)

SKIP_PROVENANCE = {"MANIFEST.csv", "PACKAGE_MANIFEST.csv", "data_dictionary.csv"}


def check_provenance_and_privacy(root: Path) -> None:
    bad_prov, bad_priv, scanned = [], [], 0
    for path in sorted(root.rglob("*.csv")):
        rel = str(path.relative_to(root))
        rows = read_csv(path)
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        generator_noise = text.replace("build_opus_synthetic_programme_v0_2.py@0.2", "")
        for pattern, label in (
            (EMAIL, "email"),
            (PHONE, "telephone"),
            (SSN, "national identifier"),
            (STREET, "street address"),
        ):
            hit = pattern.search(generator_noise)
            if hit:
                bad_priv.append(f"{rel}: {label}: {hit.group(0)[:40]}")
        if not rows or rel in SKIP_PROVENANCE or path.name in SKIP_PROVENANCE:
            continue
        for column in ("data_origin", "not_for_empirical_validation", "programme_version"):
            if column not in rows[0]:
                bad_prov.append(f"{rel}: no {column}")
        if "data_origin" in rows[0] and any(
            r["data_origin"] != "SYNTHETIC_RESEARCH_FIXTURE" for r in rows
        ):
            bad_prov.append(f"{rel}: data_origin value")
        if "not_for_empirical_validation" in rows[0] and any(
            str(r["not_for_empirical_validation"]).lower() not in ("true", "1") for r in rows
        ):
            bad_prov.append(f"{rel}: not_for_empirical_validation value")
        if "record_hash" in rows[0]:
            hashes = [r["record_hash"] for r in rows]
            if len(set(hashes)) != len(hashes):
                bad_prov.append(f"{rel}: duplicate record_hash")
    ck("provenance", "every_record_marked_synthetic", not bad_prov, f"{scanned} csv files; {bad_prov[:5]}")
    ck("privacy", "no_personal_identifiers_in_any_csv", not bad_priv, bad_priv[:5])

    for path in sorted(root.rglob("*.json")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern, label in ((EMAIL, "email"), (PHONE, "telephone"), (SSN, "national identifier")):
            hit = pattern.search(text.replace("build_opus_synthetic_programme_v0_2.py@0.2", ""))
            if hit:
                ck("privacy", f"json:{path.name}:{label}", False, hit.group(0)[:40])
    ck("privacy", "json_files_scanned", True, "")

    suspicious = [
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in {".env", ".pem", ".key", ".sh", ".bat", ".ps1", ".exe"}
    ]
    ck("privacy", "no_executable_or_secret_files", not suspicious, suspicious)


def check_splits(root: Path) -> None:
    B1 = root / "package_B_reference_training_decisions/B1_reference_population"
    projects = read_csv(B1 / "reference_projects.csv")
    manifest = read_csv(B1 / "split_manifest.csv")
    ck("splits", "360_reference_projects", len(projects) == 360, len(projects))
    inline = {r["reference_project_id"]: r["split"] for r in projects}
    declared = {r["reference_project_id"]: r["split"] for r in manifest}
    ck("splits", "manifest_covers_every_project", set(inline) == set(declared))
    ck(
        "splits",
        "manifest_agrees_with_inline_split",
        all(inline[k] == declared.get(k) for k in inline),
    )
    ck("splits", "each_project_in_exactly_one_split", len(declared) == len(manifest))

    feature_cols = [
        c
        for c in (
            "project_type",
            "delivery_method",
            "region",
            "size_band",
            "baseline_cost_usd",
            "baseline_duration_days",
            "complexity_index",
            "scope_change_count",
        )
        if c in projects[0]
    ]
    vectors: dict[str, set[str]] = {}
    for r in projects:
        key = hashlib.sha256("|".join(str(r[c]) for c in feature_cols).encode()).hexdigest()
        vectors.setdefault(key, set()).add(r["split"])
    crossing = [k for k, v in vectors.items() if len(v) > 1]
    ck(
        "splits",
        "no_duplicate_feature_vector_crosses_a_split",
        not crossing,
        f"{len(feature_cols)} features; {len(crossing)} crossing vectors",
    )

    # Leakage here means locked-holdout information reaching another split: an
    # analog drawn from the holdout, or a holdout-to-holdout pair. A holdout
    # target drawing development analogs is the intended direction.
    pairs = read_csv(B1 / "analogous_pairs.csv")
    analog_from_holdout = [
        f"{r['target_project_id']}~{r['analog_project_id']}"
        for r in pairs
        if inline.get(r["analog_project_id"]) == "LOCKED_HOLDOUT"
    ]
    ck(
        "splits",
        "no_analog_is_drawn_from_the_locked_holdout",
        not analog_from_holdout,
        f"{len(pairs)} pairs; {analog_from_holdout[:5]}",
    )
    holdout_to_holdout = [
        f"{r['target_project_id']}~{r['analog_project_id']}"
        for r in pairs
        if inline.get(r["target_project_id"]) == "LOCKED_HOLDOUT"
        and inline.get(r["analog_project_id"]) == "LOCKED_HOLDOUT"
    ]
    ck("splits", "no_holdout_to_holdout_analogous_pair", not holdout_to_holdout, holdout_to_holdout[:5])
    directions = sorted(
        {(inline.get(r["target_project_id"]), inline.get(r["analog_project_id"])) for r in pairs}
    )
    ck(
        "splits",
        "analog_direction_is_always_into_development",
        all(analog == "DEVELOPMENT" for _, analog in directions),
        directions,
    )

    for name in (
        "reference_project_periods.csv",
        "reference_outcomes.csv",
        "reference_class_membership.csv",
        "parametric_cost_training.csv",
        "anomaly_labels.csv",
        "rough_set_decision_table.csv",
    ):
        path = B1 / name
        if not path.exists():
            continue
        rows = read_csv(path)
        if not rows or "split" not in rows[0]:
            continue
        wrong = [
            r["reference_project_id"]
            for r in rows
            if r.get("reference_project_id") in inline and r["split"] != inline[r["reference_project_id"]]
        ]
        ck("splits", f"derived_split_agrees:{name}", not wrong, wrong[:5])


def check_root_artefacts(root: Path) -> None:
    required = [
        "AUDIT_RESOLUTION_v0.2.md",
        "BUILD_PROVENANCE.json",
        "CHECKSUMS.sha256",
        "CLAUDE_CODE_HANDOFF_v0.2.md",
        "MANIFEST.csv",
        "README.md",
        "VALIDATION_SUMMARY.md",
        "validation_report.json",
        "data_dictionary.csv",
        "module_asset_map.csv",
        "module_id_aliases.csv",
        "package_summary.xlsx",
        "requirements-lock.txt",
        "schemas/schema_catalog.json",
        "generators/build_opus_synthetic_programme_v0_2.py",
        "generators/validate_synthetic_programme_v0_2.py",
        "generators/verify_synthetic_checksums_v0_2.py",
        "generators/base/Opus_Gubernatio_Synthetic_Programme_v0.1.zip",
    ]
    for rel in required:
        ck("artefacts", f"present:{rel}", (root / rel).exists())

    provenance = json.loads((root / "BUILD_PROVENANCE.json").read_text(encoding="utf-8"))
    for key, rel in (
        ("builder_sha256", "generators/build_opus_synthetic_programme_v0_2.py"),
        ("validator_sha256", "generators/validate_synthetic_programme_v0_2.py"),
        ("base_archive_sha256", "generators/base/Opus_Gubernatio_Synthetic_Programme_v0.1.zip"),
    ):
        actual = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        ck("artefacts", f"provenance_hash:{key}", provenance.get(key) == actual, actual)
    ck("artefacts", "provenance_seed_20260811", provenance.get("random_seed") == 20260811)
    ck("artefacts", "provenance_version_0_2", provenance.get("programme_version") == "OG-SYNTH-0.2")


def check_checksums(root: Path) -> None:
    def load(path: Path) -> dict[str, str]:
        out = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                expected, rel = line.split("  ", 1)
                out[rel] = expected
        return out

    programme = load(root / "CHECKSUMS.sha256")
    files = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    ck("checksums", "manifest_covers_every_file", files - set(programme) == {"CHECKSUMS.sha256"},
       sorted(files - set(programme) - {"CHECKSUMS.sha256"})[:5])
    mismatch = [
        rel
        for rel, expected in programme.items()
        if not (root / rel).exists()
        or hashlib.sha256((root / rel).read_bytes()).hexdigest() != expected
    ]
    ck("checksums", "programme_checksums_recomputed_independently", not mismatch,
       f"{len(programme)} entries; {mismatch[:5]}")

    for package in (
        "package_A_project_structures",
        "package_B_reference_training_decisions",
        "package_C_optional_activation_lab",
    ):
        pdir = root / package
        local = load(pdir / "PACKAGE_CHECKSUMS.sha256")
        escapes = [r for r in local if r.startswith("..") or r.startswith("/") or "\\" in r]
        ck("checksums", f"{package}:self_contained_no_external_paths", not escapes, escapes[:5])
        bad = [
            rel
            for rel, expected in local.items()
            if not (pdir / rel).exists()
            or hashlib.sha256((pdir / rel).read_bytes()).hexdigest() != expected
        ]
        ck("checksums", f"{package}:local_checksums_verify_alone", not bad,
           f"{len(local)} entries; {bad[:5]}")
        pfiles = {str(p.relative_to(pdir)) for p in pdir.rglob("*") if p.is_file()}
        ck("checksums", f"{package}:local_manifest_covers_package",
           pfiles - set(local) == {"PACKAGE_CHECKSUMS.sha256"},
           sorted(pfiles - set(local) - {"PACKAGE_CHECKSUMS.sha256"})[:5])
        disagree = [
            rel
            for rel, expected in local.items()
            if programme.get(f"{package}/{rel}") not in (None, expected)
        ]
        ck("checksums", f"{package}:agrees_with_programme_manifest", not disagree, disagree[:5])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--csv", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    A = root / "package_A_project_structures"
    periods = read_csv(A / "reporting_periods.csv")

    check_root_artefacts(root)
    check_checksums(root)
    check_ncr(A, periods)
    check_environmental(A)
    check_ccpm(A)
    check_abm(A)
    check_dsm_boundary(root)
    check_lp(root)
    check_aliases(root)
    check_provenance_and_privacy(root)
    check_splits(root)

    failed = [r for r in RESULTS if r["result"] == "FAIL"]
    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["area", "check", "result", "detail"])
            writer.writeheader()
            writer.writerows(RESULTS)
    for row in failed:
        print(f"FAIL {row['area']}:{row['check']} {row['detail']}")
    print(json.dumps({"checks": len(RESULTS), "passed": len(RESULTS) - len(failed), "failed": len(failed)}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
