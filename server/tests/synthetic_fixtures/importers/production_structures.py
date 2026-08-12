"""
TEST-ONLY adapters: a synthetic v0.3 asset in, a production input contract out.

WHERE THIS SITS, AND WHY IT SITS THERE. The production canonical-structure layer takes its
structures off the signal inputs the caller assembled, exactly as it takes every scalar. It opens
no file and knows nothing about research fixtures. This module is the other half of that
arrangement: it reads the read-only v0.3 package through the existing fixture loader and shapes
each structure into the production contract, so a known-answer test can drive the real production
function on a real canonical structure without production ever gaining a path to a fixture.

Because this file lives under server/tests it is not importable from the application: the
application imports nothing from tests, which is the property that makes the separation real
rather than declared. The suite asserts that property rather than trusting this sentence.

Every structure produced here carries its origin and its version forward, so a result computed
from one can be identified as having come from a research fixture.
"""

from __future__ import annotations

from . import fixture_loader_v03 as FL

PACKAGE_A = FL.PACKAGE_A
PACKAGE_B = FL.PACKAGE_B
ORIGIN = "SYNTHETIC_RESEARCH_FIXTURE"


def _f(row, key):
    return float(row[key])


def line_of_balance(project_id: str, period_id: str) -> dict:
    """The lobStructure contract for one project period."""
    packages = [w for w in FL.load_table(f"{PACKAGE_A}/lob_work_packages.csv")
                if w["project_id"] == project_id and w["period_id"] == period_id]
    truth = [g for g in FL.load_table(f"{PACKAGE_A}/lob_ground_truth.csv")
             if g["project_id"] == project_id and g["period_id"] == period_id]
    if not packages or not truth:
        return {}
    g = truth[0]
    return {
        "data_origin": ORIGIN,
        "not_for_empirical_validation": True,
        "asset_version": FL.PROGRAMME_VERSION,
        "leading_work_type": g["leading_work_type"],
        "following_work_type": g["following_work_type"],
        "work_packages": [{
            "work_type_id": w["work_type_id"],
            "location_sequence": int(_f(w, "location_sequence")),
            "production_rate_locations_per_day":
                _f(w, "actual_production_rate_locations_per_day"),
            "start_day": _f(w, "actual_start_day"),
        } for w in packages],
    }


def ccpm(project_id: str, period_id: str) -> dict:
    chains = [c for c in FL.load_table(f"{PACKAGE_A}/ccpm_chains.csv")
              if c["project_id"] == project_id]
    buffers = [b for b in FL.load_table(f"{PACKAGE_A}/ccpm_buffers.csv")
               if b["project_id"] == project_id and b["period_id"] == period_id]
    if not chains or not buffers:
        return {}
    return {
        "data_origin": ORIGIN,
        "not_for_empirical_validation": True,
        "asset_version": FL.PROGRAMME_VERSION,
        "chains": [{"chain_id": c["chain_id"], "chain_type": c["chain_type"],
                    "activity_count": int(_f(c, "activity_count"))} for c in chains],
        "buffers": [{"chain_id": b["chain_id"], "buffer_type": b["buffer_type"],
                     "original_buffer_days": _f(b, "original_buffer_days"),
                     "remaining_buffer_days": _f(b, "remaining_buffer_days"),
                     "chain_progress_fraction": _f(b, "chain_progress_fraction")}
                    for b in buffers],
    }


def queues(project_id: str) -> dict:
    events = [e for e in FL.load_table(f"{PACKAGE_A}/queue_events.csv")
              if e["project_id"] == project_id]
    if not events:
        return {}
    by_queue: dict[str, list] = {}
    for e in events:
        by_queue.setdefault(e["queue_id"], []).append(e)
    out = []
    for qid, rows in sorted(by_queue.items()):
        horizon = max(_f(r, "service_end_day") for r in rows)
        out.append({
            "queue_id": qid,
            "entities": len(rows),
            "servers": len({r["server_id"] for r in rows}),
            "horizon_days": horizon,
            "total_service_days": sum(_f(r, "service_duration_days") for r in rows),
            "wait_times_days": [_f(r, "wait_time_days") for r in rows],
            "discipline": rows[0]["queue_discipline"],
        })
    return {"data_origin": ORIGIN, "not_for_empirical_validation": True,
            "asset_version": FL.PROGRAMME_VERSION, "queues": out}


def agents(project_id: str) -> dict:
    ag = [a for a in FL.load_table(f"{PACKAGE_A}/agents.csv")
          if a["project_id"] == project_id]
    states = [s for s in FL.load_table(f"{PACKAGE_A}/agent_state_history.csv")
              if s["project_id"] == project_id]
    if not ag or not states:
        return {}
    return {
        "data_origin": ORIGIN,
        "not_for_empirical_validation": True,
        "asset_version": FL.PROGRAMME_VERSION,
        "agents": [{"agent_id": a["agent_id"], "decision_rule_id": a["decision_rule_id"],
                    "network_group": a["network_group"]} for a in ag],
        "states": [{"time_step": int(_f(s, "time_step")), "agent_id": s["agent_id"],
                    "state": s["state"]} for s in states],
    }


def audited_nonconformance_cohort(project_id: str, period_id: str) -> dict:
    audits = [a for a in FL.load_table(f"{PACKAGE_A}/quality_audits.csv")
              if a["project_id"] == project_id and a["period_id"] <= period_id]
    truth = [t for t in FL.load_table(f"{PACKAGE_A}/ncr_ground_truth.csv")
             if t["project_id"] == project_id and t["period_id"] == period_id]
    if not audits or not truth:
        return {}
    open_count = int(_f(truth[0], "ncr_open_at_cutoff"))
    return {
        "data_origin": ORIGIN,
        "not_for_empirical_validation": True,
        "asset_version": FL.PROGRAMME_VERSION,
        "audits": [{"audit_id": a["audit_id"], "total_findings": int(_f(a, "total_findings"))}
                   for a in audits],
        "open_nonconformances": [{"index": i} for i in range(open_count)],
    }


def audited_permit_compliance(project_id: str, period_id: str) -> dict:
    assessments = [a for a in FL.load_table(f"{PACKAGE_A}/environmental_assessments.csv")
                   if a["project_id"] == project_id and a["period_id"] == period_id]
    violations = [v for v in FL.load_table(f"{PACKAGE_A}/environmental_violations.csv")
                  if v["project_id"] == project_id and v["period_id"] == period_id]
    if not assessments:
        return {}
    return {
        "data_origin": ORIGIN,
        "not_for_empirical_validation": True,
        "asset_version": FL.PROGRAMME_VERSION,
        "assessments": [{"requirement_id": a["requirement_id"], "result": a["result"]}
                        for a in assessments],
        "violations": len(violations),
    }


def scenario_decision(decision_problem_id: str, split: str = "DEVELOPMENT") -> dict:
    scenarios = [s for s in FL.load_table(f"{PACKAGE_B}/B3_decision_optimization/scenarios.csv")
                 if s["decision_problem_id"] == decision_problem_id]
    outcomes = [o for o in FL.load_table(
        f"{PACKAGE_B}/B3_decision_optimization/action_scenario_outcomes.csv")
        if o["decision_problem_id"] == decision_problem_id]
    if not scenarios or not outcomes:
        return {}
    return {
        "data_origin": ORIGIN,
        "not_for_empirical_validation": True,
        "decision_object_id": decision_problem_id,
        "asset_version": FL.PROGRAMME_VERSION,
        "split": split,
        "evaluated_project_id": "THE-PROJECT-UNDER-ASSESSMENT",
        "reference_member_project_ids": [],
        "scenarios": [{"scenario_id": s["scenario_id"],
                       "probability": _f(s, "scenario_probability")} for s in scenarios],
        "outcomes": [{"action_id": o["action_id"], "scenario_id": o["scenario_id"],
                      "cost_delta_usd": _f(o, "cost_delta_usd")} for o in outcomes],
    }


def decision_matrix(decision_problem_id: str, split: str = "DEVELOPMENT") -> dict:
    criteria = [c for c in FL.load_table(f"{PACKAGE_B}/B3_decision_optimization/criteria.csv")
                if c["decision_problem_id"] == decision_problem_id]
    matrix = [m for m in FL.load_table(
        f"{PACKAGE_B}/B3_decision_optimization/alternative_criteria_matrix.csv")
        if m["decision_problem_id"] == decision_problem_id]
    if not criteria or not matrix:
        return {}
    column = {"EXPECTED_COST_DELTA_USD": "expected_cost_delta_usd",
              "EXPECTED_DELAY_DAYS": "expected_delay_days",
              "QUALITY_RISK": "quality_risk",
              "SAFETY_RISK": "safety_risk",
              "RESIDUAL_RISK": "residual_risk"}
    names = [c["criterion_name"] for c in criteria]
    return {
        "data_origin": ORIGIN,
        "not_for_empirical_validation": True,
        "decision_object_id": decision_problem_id,
        "asset_version": FL.PROGRAMME_VERSION,
        "split": split,
        "evaluated_project_id": "THE-PROJECT-UNDER-ASSESSMENT",
        "reference_member_project_ids": [],
        "criteria": [{"criterion_id": c["criterion_name"], "direction": c["direction"]}
                     for c in criteria],
        "alternatives": [{"alternative_id": m["action_id"],
                          "values": {n: _f(m, column[n]) for n in names}} for m in matrix],
    }
