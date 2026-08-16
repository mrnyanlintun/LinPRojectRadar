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
        # RUN 28. The supplied Category-2 contract requires BOTH the planned and the actual
        # production rate, so the deterioration of the actual slope against plan is visible
        # rather than being folded invisibly into the separation between two lines. The v0.3
        # package already carries both rates and both start days per work package; the finish
        # day of a location is its line's start plus its sequence divided by that line's rate,
        # which is the same rate = change in units / change in time the contract states, read in
        # the other direction. Nothing is invented here: every figure below is a column of
        # lob_work_packages.csv or arithmetic on two of them.
        "unit_progress": [{
            "activity_id": w["work_type_id"],
            "location_sequence": int(_f(w, "location_sequence")),
            "quantity": _f(w, "quantity"),
            "crew_id": w["crew_id"],
            "planned_finish_day": (
                _f(w, "planned_start_day")
                + int(_f(w, "location_sequence")) / _f(w, "planned_production_rate_locations_per_day")),
            "actual_finish_day": (
                _f(w, "actual_start_day")
                + int(_f(w, "location_sequence")) / _f(w, "actual_production_rate_locations_per_day")),
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


def decision_alternatives(decision_problem_id: str, split: str = "DEVELOPMENT") -> dict:
    """
    THE RUN-30 SHARED ALTERNATIVES-AND-CRITERIA OBJECT, imported from the SAME package rows
    `decision_matrix` reads.

    Run 30's closure repointed B2.18 MARCOS and B2.19 CRITIC-TOPSIS onto one governed decision
    structure, so the synthetic package's own decision problem has to arrive in that shape or it
    would never reach the canonical production runner -- and a structurally canonical fixture
    that never reaches the canonical runner is exactly the gap the closure exists to close.

    NOTHING IS INVENTED HERE. The alternatives, the criteria and every value are the package's
    own rows, unchanged. The only translation is the orientation vocabulary: the package writes
    MIN and MAX, and the canonical structure names the same fact benefit or cost. NO WEIGHT IS
    SUPPLIED, because CRITIC derives its weights and MARCOS's must be externally governed; a
    weight invented here would be exactly the fabrication the contract forbids.
    """
    raw = decision_matrix(decision_problem_id, split)
    if not raw:
        return {}
    return {
        "data_origin": ORIGIN,
        "not_for_empirical_validation": True,
        "context_id": decision_problem_id,
        "asset_version": raw["asset_version"],
        "split": raw["split"],
        "evaluated_project_id": raw["evaluated_project_id"],
        "reference_member_project_ids": list(raw["reference_member_project_ids"]),
        "source": f"synthetic research package {FL.PROGRAMME_VERSION}, decision optimisation "
                  f"reference set",
        "period": None,
        "criteria": [{"criterion_id": c["criterion_id"], "label": c["criterion_id"],
                      "orientation": "cost" if c["direction"] == "MIN" else "benefit",
                      "units": None}
                     for c in raw["criteria"]],
        "alternatives": [{"alternative_id": a["alternative_id"],
                          "label": a["alternative_id"], "values": dict(a["values"])}
                         for a in raw["alternatives"]],
    }


# =================================================================================================
# RUN 29 CLOSURE: THE CANONICAL CATEGORY-4 AND CATEGORY-5 SHAPES.
#
# The three importers above -- `audited_nonconformance_cohort`, `queues` and `agents` -- shape the
# OG-SYNTH-0.3 tables into the forms the PREVIOUS analytical line read. Run 29's supplied
# contracts name all three as not being the method:
#
#   a backlog over an audited findings total is a ratio of two different populations, not a rate
#   over a governed exposure; a share of occupied server time is a measurement, not a queueing
#   model; and a state history whose decision rules are named and never executed is a table read,
#   not a simulation.
#
# They are KEPT, unchanged, because Run-19 and Run-10B suites read them as the historical record
# of what the previous line was integrated against, and rewriting them would destroy that record.
# The importers below are the canonical successors, and they read the SAME OG-SYNTH-0.3 tables:
# the package already carried real nonconformance events, real inspection totals and real queue
# events with arrival times, service durations, servers and a discipline. Nothing is invented
# here, and nothing in OG-SYNTH-0.3 is modified.
#
# WHAT THE PACKAGE COULD NOT SUPPLY, stated rather than worked around: its forty-eight agents are
# every one of them of type SUPPLIER, under a single decision rule, with no carrier and no project
# agent, so it cannot express the one-supplier / one-carrier / one-project model the supplied
# contract defines. That model, and the contract's own known-answer figures for all three
# measures, live in the successor package OG-SYNTH-0.4 and are read by `known_answer_*` below.
# =================================================================================================

KA_PACKAGE_ROOT = (FL.FIXTURE_ROOT / "OG-SYNTH-0.4" / "package_A_project_structures")
KA_PROGRAMME_VERSION = "OG-SYNTH-0.4"


def _ka_rows(name: str) -> list[dict]:
    """Read a successor known-answer table, refusing anything not marked synthetic."""
    import csv
    path = (KA_PACKAGE_ROOT / name).resolve()
    if not str(path).startswith(str(KA_PACKAGE_ROOT.resolve())):
        raise FL.FixtureError(f"{name} escapes the successor package root")
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if r.get("data_origin") != ORIGIN or r.get("not_for_empirical_validation") != "True":
            raise FL.FixtureError(
                f"{name} carries a row that is not marked as a synthetic research fixture")
        if r.get("programme_version") != KA_PROGRAMME_VERSION:
            raise FL.FixtureError(
                f"{name} carries a row stamped {r.get('programme_version')!r}, which is not this "
                f"package's own programme version: a current file may not carry a predecessor id")
    return rows


def ncr_exposure_record(project_id: str, period_id: str) -> dict:
    """
    The canonical A4.4 shape: nonconformance EVENTS over a governed exposure.

    Both halves are real columns of OG-SYNTH-0.3. The events are `ncr_events.csv`, each with its
    own identity, issue date, close date and severity. The exposure is `inspections_completed`
    from `quality_audits.csv`, which is a governed exposure in the supplied contract's own words
    and is the same unit its worked example uses. Nothing is derived from anything else.
    """
    events = [e for e in FL.load_table(f"{PACKAGE_A}/ncr_events.csv")
              if e["project_id"] == project_id and e["issue_period_id"] <= period_id]
    audits = [a for a in FL.load_table(f"{PACKAGE_A}/quality_audits.csv")
              if a["project_id"] == project_id and a["period_id"] <= period_id]
    if not events or not audits:
        return {}
    exposure = sum(_f(a, "inspections_completed") for a in audits)
    if exposure <= 0:
        return {}
    origin = min(e["issue_date"] for e in events)

    def _day(value: str) -> float:
        import datetime as _dt
        return float((_dt.date.fromisoformat(value) - _dt.date.fromisoformat(origin)).days)

    return {
        "data_origin": ORIGIN,
        "not_for_empirical_validation": True,
        "asset_version": FL.PROGRAMME_VERSION,
        "source": "the synthetic programme's nonconformance log and its quality audit records",
        "exposure_unit": "inspections",
        "exposure_quantity": exposure,
        "as_of_day": max(_day(e["issue_date"]) for e in events) + 1.0,
        "ncrs": [{
            "ncr_id": e["ncr_id"],
            "issue_day": _day(e["issue_date"]),
            "close_day": _day(e["close_date"]) if e["close_date"] else None,
            "severity": e["severity"],
            "reporting_period": e["issue_period_id"],
        } for e in events],
    }


def queue_model(project_id: str) -> dict:
    """
    The canonical A5.6 shape: an arrival process, a service process, servers and a discipline.

    The rates are the textbook estimators taken from the SAME `queue_events.csv` rows the
    occupancy importer reads: lambda is the number of entities that arrived divided by the span
    between the first arrival and the last service end, and mu is the reciprocal of the mean
    service duration. Both are estimates OF THE PROCESSES THE LOG OBSERVED, which is what a
    queueing model is fitted from; neither is a different quantity wearing the name of a rate.
    The server count and the discipline are columns, not estimates.
    """
    events = [e for e in FL.load_table(f"{PACKAGE_A}/queue_events.csv")
              if e["project_id"] == project_id]
    if not events:
        return {}
    by_queue: dict[str, list] = {}
    for e in events:
        by_queue.setdefault(e["queue_id"], []).append(e)
    out = []
    for qid, rows in sorted(by_queue.items()):
        first = min(_f(r, "arrival_time_day") for r in rows)
        last = max(_f(r, "service_end_day") for r in rows)
        span = last - first
        mean_service = sum(_f(r, "service_duration_days") for r in rows) / len(rows)
        if span <= 0 or mean_service <= 0:
            continue
        out.append({
            "queue_id": qid,
            "arrival_rate": len(rows) / span,
            "service_rate": 1.0 / mean_service,
            "servers": len({r["server_id"] for r in rows}),
            "discipline": "FIFO" if rows[0]["queue_discipline"] == "FCFS"
                          else rows[0]["queue_discipline"],
        })
    if not out:
        return {}
    return {
        "data_origin": ORIGIN,
        "not_for_empirical_validation": True,
        "asset_version": FL.PROGRAMME_VERSION,
        "source": "arrival and service processes estimated from the synthetic programme's own "
                  "queue event log",
        "model_version": "OG-SYNTH-0.3 queue events",
        "queues": out,
    }


def known_answer_ncr_exposure_record() -> dict:
    """The supplied contract's own worked example: four nonconformances over one hundred."""
    rows = _ka_rows("ncr_exposure_known_answer.csv")
    first = rows[0]
    return {
        "data_origin": ORIGIN, "not_for_empirical_validation": True,
        "asset_version": KA_PROGRAMME_VERSION,
        "source": "the OG-SYNTH-0.4 canonical known-answer table for nonconformance rate",
        "exposure_unit": first["exposure_unit"],
        "exposure_quantity": float(first["exposure_quantity"]),
        "as_of_day": float(first["as_of_day"]),
        "ncrs": [{"ncr_id": r["ncr_id"], "issue_day": float(r["issue_day"]),
                  "close_day": float(r["close_day"]) if r["close_day"] else None,
                  "severity": r["severity"], "reopened": r["reopened"] == "True"}
                 for r in rows],
    }


def known_answer_queue_model(case_id: str = "QUEUE-KA-STABLE") -> dict:
    """The supplied contract's own M/M/1 case, or one of its two unstable cases."""
    rows = [r for r in _ka_rows("queue_model_known_answer.csv") if r["case_id"] == case_id]
    if not rows:
        raise FL.FixtureError(f"no queue known-answer case named {case_id!r}")
    return {
        "data_origin": ORIGIN, "not_for_empirical_validation": True,
        "asset_version": KA_PROGRAMME_VERSION,
        "source": "the OG-SYNTH-0.4 canonical known-answer table for the queueing measure",
        "model_version": KA_PROGRAMME_VERSION,
        "queues": [{"queue_id": r["queue_id"], "arrival_rate": float(r["arrival_rate"]),
                    "service_rate": float(r["service_rate"]), "servers": int(r["servers"]),
                    "discipline": r["discipline"]} for r in rows],
    }


def known_answer_agent_supply_chain_model(case_id: str = "ABM-KA-1") -> dict:
    """The supplied contract's deterministic one supplier, one carrier, one project model."""
    agents_rows = [r for r in _ka_rows("abm_agents_known_answer.csv")
                   if r["case_id"] == case_id]
    env_rows = [r for r in _ka_rows("abm_environment_known_answer.csv")
                if r["case_id"] == case_id]
    if not agents_rows or not env_rows:
        raise FL.FixtureError(f"no agent known-answer case named {case_id!r}")
    env = env_rows[0]
    built = []
    for r in agents_rows:
        agent = {"agent_id": r["agent_id"], "agent_type": r["agent_type"], "state": r["state"],
                 "behaviour_rule": r["behaviour_rule"],
                 "interaction_links": r["interaction_links"].split("|")}
        if r["inventory"]:
            agent["inventory"] = float(r["inventory"])
        if r["demand"]:
            agent["demand"] = float(r["demand"])
        built.append(agent)
    return {
        "data_origin": ORIGIN, "not_for_empirical_validation": True,
        "asset_version": KA_PROGRAMME_VERSION,
        "source": "the OG-SYNTH-0.4 canonical known-answer table for the agent based model",
        "model_version": KA_PROGRAMME_VERSION,
        "environment": env["environment"],
        "time_steps": int(env["time_steps"]),
        "travel_delay_steps": int(env["travel_delay_steps"]),
        "disruption_probability": float(env["disruption_probability"]),
        "agents": built,
    }


def known_answer_expectations(name: str) -> list[dict]:
    """The expected figures the successor package records beside each known-answer case."""
    return _ka_rows(name)
