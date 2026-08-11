"""Independent recomputations of the staged synthetic ground truth.

Every function here recomputes a stored quantity from the RAW fixture rows, using arithmetic
written from the stated definition of the quantity rather than copied from any production
module. Nothing in this file imports server.app. Nothing here writes anything.

Each function returns (rows, mismatches) where rows are audit records and mismatches is a list
of human-readable disagreements. An empty mismatch list is the pass condition.
"""

from __future__ import annotations

import collections
import json
import math
from datetime import date
from typing import Any

from ..importers.fixture_loader import (
    PACKAGE_A,
    PACKAGE_B,
    load_json,
    load_metadata_table,
    load_table,
)

TOL = 1e-8


def _d(value: str) -> date | None:
    return date.fromisoformat(value) if value else None


def _close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= tol


# ------------------------------------------------------------------ A. NCR

NCR_QUANTITIES = (
    "ncr_issued_to_date",
    "ncr_closed_to_date",
    "ncr_open_at_cutoff",
    "ncr_overdue_at_cutoff",
    "cumulative_inspections",
    "ncr_incidence_per_100_inspections",
    "closure_ratio",
    "open_ratio",
    "overdue_open_ratio",
    "mean_open_age_days",
)


def recompute_ncr() -> tuple[list[dict[str, Any]], list[str]]:
    periods = load_table(f"{PACKAGE_A}/reporting_periods.csv",
                         primary_key=["project_id", "period_id"])
    events = load_table(f"{PACKAGE_A}/ncr_events.csv", primary_key=["ncr_id"])
    audits = load_table(f"{PACKAGE_A}/quality_audits.csv", primary_key=["audit_id"])
    truth = load_table(f"{PACKAGE_A}/ncr_ground_truth.csv",
                       primary_key=["project_id", "period_id"])
    stored = {(r["project_id"], r["period_id"]): r for r in truth}

    rows: list[dict[str, Any]] = []
    bad: list[str] = []
    for p in periods:
        pid, per_id = p["project_id"], p["period_id"]
        cutoff = _d(p["period_end"])
        pnum = int(p["period_number"])
        mine = [e for e in events if e["project_id"] == pid]
        # No future-event leakage: a quantity as of a cutoff may read only events issued
        # on or before it.
        issued = [e for e in mine if _d(e["issue_date"]) <= cutoff]
        for e in mine:
            if _d(e["issue_date"]) > cutoff and e in issued:  # pragma: no cover - guard
                bad.append(f"{pid}/{per_id}: future event admitted")
        closed = [e for e in issued
                  if e["close_date"] and _d(e["close_date"]) <= cutoff]
        open_now = [e for e in issued
                    if not (e["close_date"] and _d(e["close_date"]) <= cutoff)]
        overdue = [e for e in open_now if _d(e["due_date"]) < cutoff]
        inspections = sum(
            int(a["inspections_completed"]) for a in audits
            if a["project_id"] == pid and int(a["period_id"][1:]) <= pnum
        )
        calc = {
            "ncr_issued_to_date": len(issued),
            "ncr_closed_to_date": len(closed),
            "ncr_open_at_cutoff": len(open_now),
            "ncr_overdue_at_cutoff": len(overdue),
            "cumulative_inspections": inspections,
            "ncr_incidence_per_100_inspections":
                (len(issued) / inspections * 100) if inspections else 0.0,
            "closure_ratio": (len(closed) / len(issued)) if issued else 0.0,
            "open_ratio": (len(open_now) / len(issued)) if issued else 0.0,
            "overdue_open_ratio": (len(overdue) / len(open_now)) if open_now else 0.0,
            "mean_open_age_days":
                (sum((cutoff - _d(e["issue_date"])).days for e in open_now) / len(open_now))
                if open_now else 0.0,
        }
        g = stored[(pid, per_id)]
        for key in NCR_QUANTITIES:
            ok = _close(round(calc[key], 8), float(g[key]), 1e-8)
            rows.append({"check": "ncr", "project_id": pid, "period_id": per_id,
                         "quantity": key, "recomputed": round(calc[key], 8),
                         "stored": g[key], "agrees": ok})
            if not ok:
                bad.append(f"NCR {pid}/{per_id} {key}: {calc[key]} != {g[key]}")
    return rows, bad


def ncr_status_identity() -> list[str]:
    """Event identity, timing order and the absence of a reopen concept."""
    events = load_table(f"{PACKAGE_A}/ncr_events.csv", primary_key=["ncr_id"])
    bad = []
    for e in events:
        if e["close_date"] and _d(e["close_date"]) < _d(e["issue_date"]):
            bad.append(f"{e['ncr_id']}: closed before issued")
        if _d(e["due_date"]) < _d(e["issue_date"]):
            bad.append(f"{e['ncr_id']}: due before issued")
    if any("reopen" in c for c in events.rows[0]):
        bad.append("unexpected reopen column: the recomputation does not model reopening")
    return bad


# ------------------------------------------------------- B. Environmental

ENV_QUANTITIES = (
    "applicable_requirements",
    "applicable_requirements_assessed",
    "compliant_requirements",
    "noncompliant_requirements",
    "unassessed_requirements",
    "environmental_compliance_rate",
    "severe_noncompliances",
    "overdue_corrective_actions",
)


def recompute_environmental() -> tuple[list[dict[str, Any]], list[str]]:
    periods = load_table(f"{PACKAGE_A}/reporting_periods.csv")
    reqs = load_table(f"{PACKAGE_A}/environmental_requirements.csv",
                      primary_key=["requirement_id"])
    assessments = load_table(f"{PACKAGE_A}/environmental_assessments.csv",
                             primary_key=["assessment_id"])
    violations = load_table(f"{PACKAGE_A}/environmental_violations.csv",
                            primary_key=["violation_id"])
    truth = load_table(f"{PACKAGE_A}/environmental_ground_truth.csv",
                       primary_key=["project_id", "period_id"])
    stored = {(r["project_id"], r["period_id"]): r for r in truth}

    rows: list[dict[str, Any]] = []
    bad: list[str] = []
    for p in periods:
        pid, per_id, end = p["project_id"], p["period_id"], _d(p["period_end"])
        applicable = [r for r in reqs
                      if r["project_id"] == pid and r["applicable"] == "True"
                      and _d(r["effective_date"]) <= end]
        applicable_ids = {r["requirement_id"] for r in applicable}
        assessed = [a for a in assessments
                    if a["project_id"] == pid and a["period_id"] == per_id
                    and a["requirement_id"] in applicable_ids
                    and a["result"] not in ("NOT_ASSESSED", "NOT_APPLICABLE")]
        compliant = [a for a in assessed if a["result"] == "COMPLIANT"]
        noncompliant = [a for a in assessed if a["result"] == "NONCOMPLIANT"]
        period_violations = [v for v in violations
                             if v["project_id"] == pid and v["period_id"] == per_id]
        severe = [v for v in period_violations if v["severity"] in ("CRITICAL", "HIGH")]
        to_date = [v for v in violations
                   if v["project_id"] == pid and _d(v["identified_date"]) <= end]
        overdue = [v for v in to_date
                   if v["corrective_due_date"] and _d(v["corrective_due_date"]) < end
                   and not (v["corrective_close_date"]
                            and _d(v["corrective_close_date"]) <= end)]
        calc = {
            "applicable_requirements": len(applicable),
            "applicable_requirements_assessed": len(assessed),
            "compliant_requirements": len(compliant),
            "noncompliant_requirements": len(noncompliant),
            "unassessed_requirements": len(applicable) - len(assessed),
            "environmental_compliance_rate":
                (len(compliant) / len(assessed)) if assessed else 0.0,
            "severe_noncompliances": len(severe),
            "overdue_corrective_actions": len(overdue),
        }
        g = stored[(pid, per_id)]
        # Denominator integrity: assessed is the denominator of the rate and can never
        # exceed the applicable set.
        if calc["applicable_requirements_assessed"] > calc["applicable_requirements"]:
            bad.append(f"env {pid}/{per_id}: assessed exceeds applicable")
        if calc["compliant_requirements"] + calc["noncompliant_requirements"] != len(assessed):
            bad.append(f"env {pid}/{per_id}: compliant plus noncompliant is not assessed")
        for key in ENV_QUANTITIES:
            ok = _close(round(float(calc[key]), 8), float(g[key]), 1e-8)
            rows.append({"check": "environmental", "project_id": pid, "period_id": per_id,
                         "quantity": key, "recomputed": round(float(calc[key]), 8),
                         "stored": g[key], "agrees": ok})
            if not ok:
                bad.append(f"ENV {pid}/{per_id} {key}: {calc[key]} != {g[key]}")
    return rows, bad


# --------------------------------------------------------------- C. CCPM

def recompute_ccpm() -> tuple[list[dict[str, Any]], list[str]]:
    acts = load_table(f"{PACKAGE_A}/schedule_activities.csv",
                      primary_key=["project_id", "activity_id"])
    chain_acts = load_table(f"{PACKAGE_A}/ccpm_chain_activities.csv")
    chains = load_table(f"{PACKAGE_A}/ccpm_chains.csv",
                        primary_key=["project_id", "chain_id"])
    buffers = load_table(f"{PACKAGE_A}/ccpm_buffers.csv",
                         primary_key=["project_id", "period_id", "buffer_id"])
    activity = {(a["project_id"], a["activity_id"]): a for a in acts}
    chain_key = {(c["project_id"], c["chain_id"]): c for c in chains}

    rows: list[dict[str, Any]] = []
    bad: list[str] = []
    for c in chains:
        key = (c["project_id"], c["chain_id"])
        members = [m for m in chain_acts if (m["project_id"], m["chain_id"]) == key]
        if not members:
            bad.append(f"chain {key} has no declared activities")
            continue
        variance = 0.0
        for m in members:
            a = activity.get((m["project_id"], m["activity_id"]))
            if a is None:
                bad.append(f"chain {key} names a missing activity {m['activity_id']}")
                continue
            o = float(a["optimistic_duration_days"])
            p = float(a["pessimistic_duration_days"])
            variance += ((p - o) / 6.0) ** 2
            if a["ccpm_chain_id"] != m["chain_id"]:
                bad.append(f"{m['activity_id']} is declared in {m['chain_id']} but the "
                           f"activity row says {a['ccpm_chain_id']}")
        buffer_days = 1.645 * math.sqrt(variance)
        ok_v = _close(variance, float(c["variance_sum_days2"]), 1e-6)
        ok_b = _close(buffer_days, float(c["original_buffer_days"]), 1e-6)
        rows.append({"check": "ccpm_chain", "project_id": c["project_id"],
                     "period_id": "", "quantity": f"{c['chain_id']}:buffer_days",
                     "recomputed": round(buffer_days, 8),
                     "stored": c["original_buffer_days"], "agrees": ok_v and ok_b})
        if not (ok_v and ok_b):
            bad.append(f"CCPM {key}: variance/buffer {variance}/{buffer_days} != "
                       f"{c['variance_sum_days2']}/{c['original_buffer_days']}")
        if len(members) != int(c["activity_count"]):
            bad.append(f"CCPM {key}: declared activity_count does not match membership")
        if c["buffer_sizing_method"] != "RSS_PERT_VARIANCE":
            bad.append(f"CCPM {key}: sizing method is {c['buffer_sizing_method']}")

    seen_types = set()
    for b in buffers:
        key = (b["project_id"], b["chain_id"])
        seen_types.add(b["buffer_type"])
        c = chain_key.get(key)
        if c is None:
            bad.append(f"buffer {b['buffer_id']} joins no declared chain")
            continue
        if b["buffer_type"] != c["chain_type"]:
            bad.append(f"buffer {b['buffer_id']} type disagrees with its chain")
        if not _close(float(b["original_buffer_days"]), float(c["original_buffer_days"]), 1e-6):
            bad.append(f"buffer {b['buffer_id']} sizing disagrees with its chain")
        # Flat percentage sizing must be absent: 0.15 times the chain duration would be
        # a different number from the root-sum-square figure, and the method column would
        # not say RSS_PERT_VARIANCE.
        if b["buffer_sizing_method"] != "RSS_PERT_VARIANCE":
            bad.append(f"buffer {b['buffer_id']} is not sized by root sum of PERT variances")
    if seen_types != {"PROJECT", "FEEDING"}:
        bad.append(f"project and feeding buffers are not both distinguishable: {seen_types}")
    return rows, bad


def ccpm_flat_fifteen_percent_absent() -> tuple[bool, str]:
    """Prove no buffer equals fifteen per cent of its chain's declared duration."""
    acts = load_table(f"{PACKAGE_A}/schedule_activities.csv")
    chain_acts = load_table(f"{PACKAGE_A}/ccpm_chain_activities.csv")
    chains = load_table(f"{PACKAGE_A}/ccpm_chains.csv")
    activity = {(a["project_id"], a["activity_id"]): a for a in acts}
    hits = []
    for c in chains:
        key = (c["project_id"], c["chain_id"])
        members = [m for m in chain_acts if (m["project_id"], m["chain_id"]) == key]
        duration = sum(
            float(activity[(m["project_id"], m["activity_id"])]["most_likely_duration_days"])
            for m in members
        )
        if _close(float(c["original_buffer_days"]), 0.15 * duration, 1e-3):
            hits.append(c["chain_id"])
    return (not hits), f"chains sized at a flat fifteen per cent: {hits}"


# --------------------------------------------------------- D. Agent rules

def replay_agent_rules() -> tuple[list[dict[str, Any]], list[str]]:
    rules = sorted(load_table(f"{PACKAGE_A}/agent_decision_rules.csv"),
                   key=lambda r: int(r["rule_order"]))
    states = load_table(f"{PACKAGE_A}/agent_state_history.csv")
    agents = load_table(f"{PACKAGE_A}/agents.csv", primary_key=["project_id", "agent_id"])
    truth = load_table(f"{PACKAGE_A}/abm_rule_ground_truth.csv")
    base = {(a["project_id"], a["agent_id"]): a for a in agents}
    known_rule_ids = {r["decision_rule_id"] for r in rules}

    rows: list[dict[str, Any]] = []
    bad: list[str] = []
    counts: collections.Counter = collections.Counter()
    for r in states:
        agent = base.get((r["project_id"], r["agent_id"]))
        if agent is None:
            bad.append(f"state row references an unknown agent {r['agent_id']}")
            continue
        if r["decision_rule_id"] not in known_rule_ids:
            bad.append(f"state row references an unknown rule {r['decision_rule_id']}")
            continue
        capacity = float(agent["base_capacity_units"])
        inventory = float(r["inventory_end_units"])
        selected = []
        for rule in rules:
            if rule["decision_rule_id"] != r["decision_rule_id"]:
                continue
            condition = json.loads(rule["condition_json"])
            if "state" in condition and r["state"] == condition["state"]:
                selected.append(rule)
                break
            if condition.get("inventory_below_base_capacity") and inventory < capacity:
                selected.append(rule)
                break
            if condition.get("default"):
                selected.append(rule)
                break
        if len(selected) != 1:
            bad.append(f"{r['agent_id']}@{r['time_step']}: {len(selected)} branches governed")
            continue
        chosen = selected[0]
        counts[(r["project_id"], chosen["decision_rule_id"], chosen["rule_branch"])] += 1
        if chosen["rule_branch"] != r["rule_branch"]:
            bad.append(f"{r['agent_id']}@{r['time_step']}: replay chose "
                       f"{chosen['rule_branch']}, stored {r['rule_branch']}")
    for g in truth:
        key = (g["project_id"], g["decision_rule_id"], g["rule_branch"])
        ok = counts[key] == int(g["application_count"])
        rows.append({"check": "agent_rules", "project_id": g["project_id"], "period_id": "",
                     "quantity": f"{g['decision_rule_id']}:{g['rule_branch']}",
                     "recomputed": counts[key], "stored": g["application_count"],
                     "agrees": ok})
        if not ok:
            bad.append(f"ABM {key}: replay {counts[key]} != stored {g['application_count']}")
    if len(counts) != len(truth.rows):
        bad.append("replayed branch key set differs from the stored branch key set")
    # Every condition must be machine-readable: parseable JSON with a recognised predicate.
    for rule in rules:
        condition = json.loads(rule["condition_json"])
        if not set(condition) & {"state", "inventory_below_base_capacity", "default"}:
            bad.append(f"rule {rule['rule_branch']} has no machine-readable predicate")
    return rows, bad


# ------------------------------------------------- E. DSM package boundary

def dsm_boundary() -> tuple[list[dict[str, Any]], list[str]]:
    """Locate DSM by the files that actually exist, not by the alias table's word."""
    from ..importers.fixture_loader import PACKAGE_ROOT

    rows: list[dict[str, Any]] = []
    bad: list[str] = []
    found = sorted(
        p.relative_to(PACKAGE_ROOT).as_posix()
        for p in PACKAGE_ROOT.rglob("dsm_*.csv")
        if "generators" not in p.parts
    )
    for rel in found:
        in_a = rel.startswith(PACKAGE_A + "/")
        rows.append({"check": "dsm_boundary", "project_id": "", "period_id": "",
                     "quantity": rel, "recomputed": "package_A" if in_a else "elsewhere",
                     "stored": "package_A", "agrees": in_a})
        if not in_a:
            bad.append(f"DSM asset outside package A: {rel}")
    if not found:
        bad.append("no DSM assets found on disk")
    # Manifest agreement, independent of the alias table.
    manifest = load_metadata_table(f"{PACKAGE_A}/PACKAGE_MANIFEST.csv")
    manifest_files = {r.get("file") or "" for r in manifest}
    for rel in found:
        name = rel.rsplit("/", 1)[-1]
        if name not in manifest_files:
            bad.append(f"{name} is on disk but not in the package A manifest")
    # The DSM node and edge tables must be project-specific, not a single global matrix.
    nodes = load_table(f"{PACKAGE_A}/dsm_nodes.csv", primary_key=["project_id", "node_id"])
    projects = {n["project_id"] for n in nodes}
    if len(projects) < 2:
        bad.append("DSM nodes are not project-specific")
    rows.append({"check": "dsm_boundary", "project_id": "", "period_id": "",
                 "quantity": "project_specific_node_sets", "recomputed": len(projects),
                 "stored": ">=2", "agrees": len(projects) >= 2})
    return rows, bad


# ------------------------------------------------------------ F. LP models

def solve_lp_models() -> tuple[list[dict[str, Any]], list[str]]:
    from scipy.optimize import linprog

    doc = load_json(f"{PACKAGE_B}/B3_decision_optimization/lp_models.json")
    rows: list[dict[str, Any]] = []
    bad: list[str] = []
    for model in doc["models"]:
        dp = model["decision_problem_id"]
        objective = model["objective"]
        variables = model["variables"]
        if not all(isinstance(c, (int, float)) for c in objective["coefficients"]):
            bad.append(f"{dp}: objective vector is not numerical")
        sense = objective["sense"]
        sign = 1.0 if sense == "MIN" else -1.0
        c = [sign * float(x) for x in objective["coefficients"]]
        a_ub: list[list[float]] = []
        b_ub: list[float] = []
        a_eq: list[list[float]] = []
        b_eq: list[float] = []
        for con in model["constraints"]:
            coefficients = [float(x) for x in con["coefficients"]]
            rhs = float(con["rhs"])
            relation = con["sense"]
            if relation in ("LE", "<="):
                a_ub.append(coefficients)
                b_ub.append(rhs)
            elif relation in ("GE", ">="):
                a_ub.append([-x for x in coefficients])
                b_ub.append(-rhs)
            elif relation in ("EQ", "="):
                a_eq.append(coefficients)
                b_eq.append(rhs)
            else:
                bad.append(f"{dp}: unsupported relation {relation}")
        bounds = [(float(v["lower"]), float(v["upper"])) for v in variables]
        if any(int(v.get("integrality", 0)) not in (0, 1) for v in variables):
            bad.append(f"{dp}: unreadable integrality flag")
        if any(int(v.get("integrality", 0)) == 1 for v in variables):
            from scipy.optimize import Bounds, LinearConstraint, milp
            import numpy as np
            constraints = []
            if a_ub:
                constraints.append(LinearConstraint(np.array(a_ub), -np.inf, np.array(b_ub)))
            if a_eq:
                constraints.append(LinearConstraint(np.array(a_eq), np.array(b_eq),
                                                    np.array(b_eq)))
            res = milp(c=np.array(c), constraints=constraints,
                       integrality=np.array([int(v.get("integrality", 0)) for v in variables]),
                       bounds=Bounds([b[0] for b in bounds], [b[1] for b in bounds]))
            success, x, fun = res.success, res.x, res.fun
        else:
            res = linprog(c, a_ub or None, b_ub or None, a_eq or None, b_eq or None,
                          bounds=bounds, method="highs")
            success, x, fun = res.success, res.x, res.fun
        truth = model["ground_truth"]
        ok_status = bool(success) == bool(truth["success"])
        if not ok_status:
            bad.append(f"{dp}: solver status {success} != stored {truth['success']}")
        value = None
        if success:
            value = (fun if sense == "MIN" else -fun) + float(objective.get("constant", 0.0))
            if not _close(value, float(truth["objective_value"]), 1e-4):
                bad.append(f"{dp}: objective {value} != stored {truth['objective_value']}")
            solution = truth.get("solution", {})
            for name, xi in zip((v["name"] for v in variables), x):
                key = name.replace("_intensity", "")
                if key in solution and not _close(solution[key], xi, 1e-4):
                    bad.append(f"{dp}: {name} {xi} != stored {solution[key]}")
                if not (bounds[0][0] - 1e-9 <= xi <= max(b[1] for b in bounds) + 1e-9):
                    bad.append(f"{dp}: {name} outside its bounds")
        rows.append({"check": "lp", "project_id": dp, "period_id": "",
                     "quantity": "objective_value",
                     "recomputed": round(value, 4) if value is not None else "infeasible",
                     "stored": truth["objective_value"], "agrees": ok_status})
    return rows, bad


# ----------------------------------------------------------- G. Leakage

def leakage_checks() -> tuple[list[dict[str, Any]], list[str]]:
    B1 = f"{PACKAGE_B}/B1_reference_population"
    manifest = load_table(f"{B1}/split_manifest.csv", primary_key=["reference_project_id"])
    projects = load_table(f"{B1}/reference_projects.csv",
                          primary_key=["reference_project_id"])
    outcomes = load_table(f"{B1}/reference_outcomes.csv",
                          primary_key=["reference_project_id"])
    pairs = load_table(f"{B1}/analogous_pairs.csv")
    split = {r["reference_project_id"]: r["split"] for r in manifest}

    rows: list[dict[str, Any]] = []
    bad: list[str] = []

    # Project-ID overlap between splits.
    members: dict[str, set] = collections.defaultdict(set)
    for pid, s in split.items():
        members[s].add(pid)
    names = sorted(members)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            overlap = members[a] & members[b]
            rows.append({"check": "leakage", "project_id": f"{a}|{b}", "period_id": "",
                         "quantity": "project_id_overlap", "recomputed": len(overlap),
                         "stored": 0, "agrees": not overlap})
            if overlap:
                bad.append(f"split overlap {a}/{b}: {sorted(overlap)[:5]}")

    # Every project in exactly one split, and the split column agrees with the manifest.
    for p in projects:
        if p["reference_project_id"] not in split:
            bad.append(f"{p['reference_project_id']} has no split")
        elif p["split"] != split[p["reference_project_id"]]:
            bad.append(f"{p['reference_project_id']} split column disagrees with the manifest")

    # Duplicate and near-duplicate feature vectors, across every split boundary.
    feature_cols = ["project_type", "delivery_method", "region", "gross_area_m2",
                    "length_km", "capacity_units", "floors", "complexity_index",
                    "design_completeness", "location_factor", "baseline_cost_usd",
                    "baseline_duration_days"]
    exact: dict[tuple, list[str]] = collections.defaultdict(list)
    for p in projects:
        exact[tuple(p[c] for c in feature_cols)].append(p["reference_project_id"])
    duplicates = {k: v for k, v in exact.items() if len(v) > 1}
    rows.append({"check": "leakage", "project_id": "", "period_id": "",
                 "quantity": "duplicate_feature_vectors", "recomputed": len(duplicates),
                 "stored": 0, "agrees": not duplicates})
    if duplicates:
        bad.append(f"duplicate feature vectors: {list(duplicates.values())[:3]}")

    numeric = ["gross_area_m2", "length_km", "capacity_units", "floors",
               "complexity_index", "design_completeness", "location_factor",
               "baseline_cost_usd", "baseline_duration_days"]
    scale = {}
    for col in numeric:
        values = [float(p[col]) for p in projects]
        lo, hi = min(values), max(values)
        scale[col] = (lo, hi - lo if hi > lo else 1.0)
    vectors = [
        (p["reference_project_id"], split[p["reference_project_id"]],
         tuple((float(p[c]) - scale[c][0]) / scale[c][1] for c in numeric))
        for p in projects
    ]
    near = []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            if vectors[i][1] == vectors[j][1]:
                continue
            distance = math.dist(vectors[i][2], vectors[j][2])
            if distance < 1e-3:
                near.append((vectors[i][0], vectors[j][0], round(distance, 6)))
    rows.append({"check": "leakage", "project_id": "", "period_id": "",
                 "quantity": "near_duplicate_cross_split_pairs", "recomputed": len(near),
                 "stored": 0, "agrees": not near})
    if near:
        bad.append(f"near-duplicate projects across splits: {near[:3]}")

    # Analogous pairs: an analog may only come from the development split, whichever split
    # the target sits in. This is checked over every pair, not holdout to holdout.
    crossing = collections.Counter()
    for pair in pairs:
        target, analog = pair["target_project_id"], pair["analog_project_id"]
        if target == analog:
            bad.append(f"analogous pair joins {target} to itself")
        crossing[(split[target], split[analog])] += 1
        if split[analog] != "DEVELOPMENT":
            bad.append(f"analog {analog} for {target} is in {split[analog]}")
    for key, count in sorted(crossing.items()):
        rows.append({"check": "leakage", "project_id": f"{key[0]}->{key[1]}", "period_id": "",
                     "quantity": "analogous_pairs", "recomputed": count,
                     "stored": "analog must be DEVELOPMENT",
                     "agrees": key[1] == "DEVELOPMENT"})

    # Target and ground-truth leakage: outcome quantities must not be reused as features,
    # and the stored analog outcome must equal that analog's own recorded outcome.
    outcome_by_id = {o["reference_project_id"]: o for o in outcomes}
    outcome_cols = {"final_cost_usd", "final_duration_days", "cost_overrun_pct",
                    "schedule_overrun_pct", "outcome_class", "known_anomaly_label"}
    leaked = outcome_cols & set(feature_cols)
    rows.append({"check": "leakage", "project_id": "", "period_id": "",
                 "quantity": "outcome_columns_in_feature_set", "recomputed": len(leaked),
                 "stored": 0, "agrees": not leaked})
    if leaked:
        bad.append(f"outcome columns used as features: {sorted(leaked)}")
    for pair in pairs:
        analog = outcome_by_id[pair["analog_project_id"]]
        if not _close(float(pair["analog_cost_overrun_pct"]),
                      float(analog["cost_overrun_pct"]), 1e-6):
            bad.append(f"analog outcome for {pair['analog_project_id']} disagrees with "
                       "its own outcome row")

    # Identical-seed or equivalent-row leakage: no two projects share a record hash.
    hashes = collections.Counter(p["record_hash"] for p in projects)
    repeated = [h for h, n in hashes.items() if n > 1]
    rows.append({"check": "leakage", "project_id": "", "period_id": "",
                 "quantity": "repeated_record_hashes", "recomputed": len(repeated),
                 "stored": 0, "agrees": not repeated})
    if repeated:
        bad.append(f"repeated record hashes: {repeated[:3]}")
    return rows, bad
