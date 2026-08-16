"""
RUN 29 -- THE CANONICAL TEST FIXTURES for the eighteen Category-4 and Category-5 structures.

WHAT THESE ARE AND ARE NOT. Every structure below is a SYNTHETIC known-answer fixture whose
figures are chosen to make the supplied contract's own oracles hand-checkable. They are laboratory
material for verifying an implementation. They are NOT empirical validation, they are NOT a supply
path, and no production code imports this file: the production supply path for every one of these
structures is `server/app/project_data.py` through the `saveprojectdata` action, which is what
`code_audit/run29_supply_path_reconciliation.csv` records and what
`test_run29_supply_path_guard.py` enforces.
"""

from __future__ import annotations


def rfi_event_log(count: int = 12, exposure_days: float = 30.0,
                  duplicate: bool = False) -> dict:
    """Contract 4.2 oracle: twelve requests over thirty days is 0.4 a day."""
    events = [{"rfi_id": f"RFI-{i:03d}", "created_day": float(i), "status": "CLOSED",
               "topic": "coordination", "responsible_party": "design team",
               "reporting_period": 6, "response_day": float(i) + 3.0,
               "close_day": float(i) + 4.0}
              for i in range(count)]
    if duplicate:
        events = events + [dict(e) for e in events]
    return {"source": "the project's request register export", "register_id": "RFI-REG-1",
            "exposure_days": exposure_days, "events": events}


def submittal_register(rejected: int = 3, approved: int = 17) -> dict:
    """Contract 4.3 oracle: three rejected of twenty assessed is 0.15."""
    decisions = []
    for i in range(approved):
        decisions.append({"submittal_id": f"SUB-{i:03d}", "revision_id": "A",
                          "disposition": "APPROVED", "decision_day": 10.0,
                          "reviewer": "the architect of record", "reporting_period": 6})
    for i in range(rejected):
        decisions.append({"submittal_id": f"SUB-{approved + i:03d}", "revision_id": "A",
                          "disposition": "REJECTED", "decision_day": 11.0,
                          "reviewer": "the architect of record", "reporting_period": 6})
    return {"source": "the project's submittal register export",
            "taxonomy_version": "sub-tax-1.0", "reporting_period": 6, "decisions": decisions}


def ncr_record(count: int = 4, exposure: float = 100.0,
               unit: str = "inspections") -> dict:
    """Contract 4.4 oracle: four nonconformances over one hundred inspections is 0.04."""
    return {"source": "the quality manager's nonconformance log",
            "exposure_unit": unit, "exposure_quantity": exposure, "as_of_day": 200.0,
            "ncrs": [{"ncr_id": f"NCR-{i:03d}", "issue_day": 100.0 + i, "severity": "MAJOR",
                      "reporting_period": 6} for i in range(count)]}


def weather_events(lost: float = 2.0, available_float: float = 0.0,
                   allowance: float = 0.0) -> dict:
    """Contract 4.5 oracle: two lost days on a zero-float critical activity is two days."""
    return {"source": "the daily field reports", "weather_calendar_id": "WX-CAL-1",
            "allowance_days_remaining": allowance,
            "events": [{"event_id": "WX-001", "event_day": 120.0, "activity_id": "A-140",
                        "schedule_path_id": "CRITICAL", "planned_work": "roof deck placement",
                        "actual_lost_days": lost, "available_float_days": available_float,
                        "causal_evidence": "the daily report records the crew stood down",
                        "mitigation_days": 0.0}]}


def change_register(count: int = 6, exposure_days: float = 180.0) -> dict:
    """Contract 4.6 oracle: six changes over one hundred and eighty days is 6/180."""
    return {"source": "the project's change order log", "exposure_days": exposure_days,
            "baseline_contract_value": 1000000.0,
            "changes": [{"change_id": f"CO-{i:03d}", "issue_day": 20.0 * i,
                         "change_type": "SCOPE", "cause": "OWNER_REQUEST",
                         "value": 10000.0, "direction": "ADDITIVE", "reporting_period": 6}
                        for i in range(count)]}


#: THE LABORATORY DISPUTE LADDER. The supplied contract is explicit that these labels are a TEST
#: FIXTURE and not a universal production taxonomy: production reads the project's own governed
#: process off the structure, which is why the ranks live here and not in `canonical_v4.py`.
LAB_DISPUTE_STAGES = [
    {"stage_id": "S0_ISSUE_NOTICED", "rank": 0},
    {"stage_id": "S1_CLAIM_SUBMITTED", "rank": 1},
    {"stage_id": "S2_FORMAL_DETERMINATION", "rank": 2},
    {"stage_id": "S3_NEGOTIATION", "rank": 3},
    {"stage_id": "S4_MEDIATION", "rank": 4},
    {"stage_id": "S5_LITIGATION", "rank": 5},
]


def dispute_register(stage: str = "S1_CLAIM_SUBMITTED") -> dict:
    return {"source": "the contract administrator's claim register",
            "process_id": "LAB-DISPUTE-PROCESS", "process_version": "1.0", "as_of_day": 300.0,
            "process_stages": [dict(s) for s in LAB_DISPUTE_STAGES],
            "issues": [{"issue_id": "CLM-001", "current_stage_id": stage, "stage_day": 250.0,
                        "raised_day": 200.0, "notice_given": True, "claim_value": 125000.0,
                        "evidence_source": "the notice letter of 20 March and its reply"}]}


def subcontractor_assessment(ratings=(0.80, 0.90, 0.70)) -> dict:
    """Contract 4.8 oracle: 0.80, 0.90 and 0.70 under equal weights is 0.80."""
    third = 1.0 / 3.0
    return {"source": "the quarterly subcontractor evaluation forms",
            "weights_version": "sub-weights-1.0",
            "weights": {"quality": third, "schedule": third, "safety": 1.0 - 2 * third},
            "assessments": [{"subcontractor_id": "SUB-MECH", "period": "2026-Q2",
                             "evaluator": "the construction manager",
                             "rating_provenance": "the signed evaluation form of 30 June",
                             "critical_violation": False,
                             "ratings": {"quality": ratings[0], "schedule": ratings[1],
                                         "safety": ratings[2]}}]}


def procurement_items(required: float = 100.0, forecast: float = 110.0) -> dict:
    """Contract 4.9 oracle: required day 100 against forecast 110 is minus ten days."""
    return {"source": "the procurement expediting report",
            "items": [{"item_id": "AHU-01", "required_on_site_day": required,
                       "forecast_delivery_day": forecast, "order_day": 10.0,
                       "available_float_days": 0.0, "criticality": "LONG_LEAD",
                       "procurement_status": "IN_FABRICATION",
                       "schedule_activity_id": "A-320",
                       "forecast_uncertainty_days": 5.0}]}


def conflict_register(verified: int = 5, exposure: float = 250.0) -> dict:
    """Contract 4.10 oracle: five verified conflicts over 250 requirements is 0.02."""
    return {"source": "the specification coordination review",
            "specification_document_id": "SPEC-ISSUE-4", "specification_revision": "R4",
            "exposure_unit": "requirements", "exposure_quantity": exposure,
            "conflicts": [{"conflict_id": f"SC-{i:03d}",
                           "evidence_location_a": f"section 07 52 00 clause {i}",
                           "evidence_location_b": f"section 03 30 00 clause {i}",
                           "state": "CONFIRMED", "reviewer": "the specification writer",
                           "discipline": "ARCHITECTURAL",
                           "cross_reference_id": f"XR-{i:03d}"} for i in range(verified)]}


def dsm_model() -> dict:
    """Contract 5.1 oracle: D = [[0, 0.5], [0, 0]] and R0 = [0, 1]."""
    return {"source": "the design dependency workshop of 12 May", "model_version": "dsm-1.0",
            "matrix_orientation": "ROW_RECEIVES_FROM_COLUMN",
            "nodes": [{"node_id": "n1"}, {"node_id": "n2"}],
            "edges": [{"source": "n2", "target": "n1", "strength": 0.5}],
            "seed_rework_vector": {"n1": 0.0, "n2": 1.0},
            "stopping_rule": {"max_iterations": 5, "epsilon": 0.0}}


def sensitivity_model() -> dict:
    """Contract 5.2 oracle: Y = x1^2 + x2 at (2, 1), x1 raised ten per cent, S = 1.68."""
    return {"source": "the cost model the estimator maintains",
            "method": "LOCAL_ONE_AT_A_TIME",
            "response_model": {"model_id": "LAB-QUADRATIC", "version": "1.0",
                               "terms": [{"coefficient": 1.0, "powers": {"x1": 2}},
                                         {"coefficient": 1.0, "powers": {"x2": 1}}]},
            "base_state": {"x1": 2.0, "x2": 1.0},
            "inputs": [{"input_id": "x1", "low": 1.8, "high": 2.2,
                        "perturbation_fraction": 0.10, "units": "index"}]}


def tornado_model() -> dict:
    """Contract 5.3 oracle: impacts 30, 7 and 30 put A and C tied above B."""
    return {"source": "the cost model the estimator maintains",
            "method": "LOCAL_ONE_AT_A_TIME",
            "response_model": {"model_id": "LAB-ADDITIVE", "version": "1.0",
                               "terms": [{"coefficient": 1.0, "powers": {"A": 1}},
                                         {"coefficient": 1.0, "powers": {"B": 1}},
                                         {"coefficient": 1.0, "powers": {"C": 1}}]},
            "base_state": {"A": 100.0, "B": 100.0, "C": 100.0},
            "inputs": [{"input_id": "A", "low": 90.0, "high": 120.0,
                        "perturbation_fraction": 0.10, "units": "days"},
                       {"input_id": "B", "low": 98.0, "high": 105.0,
                        "perturbation_fraction": 0.10, "units": "days"},
                       {"input_id": "C", "low": 80.0, "high": 110.0,
                        "perturbation_fraction": 0.10, "units": "days"}]}


def scenario_set() -> dict:
    """Contract 5.4 oracle: Y = 2*x1 + x2 gives 5, 8 and 4."""
    return {"source": "the scenario workshop of 3 June", "scenario_set_version": "scn-1.0",
            "response_model": {"model_id": "LAB-LINEAR", "version": "1.0",
                               "terms": [{"coefficient": 2.0, "powers": {"x1": 1}},
                                         {"coefficient": 1.0, "powers": {"x2": 1}}]},
            "consistency_constraints": [
                {"constraint_id": "C1", "variable": "x1", "minimum": 0.0, "maximum": 10.0},
                {"constraint_id": "C2", "variable": "x2", "minimum": 0.0, "maximum": 10.0}],
            "scenarios": [
                {"scenario_id": "BASE", "name": "Base", "version": "1.0",
                 "rationale": "the plan as approved", "variables": {"x1": 2.0, "x2": 1.0}},
                {"scenario_id": "ADVERSE", "name": "Adverse", "version": "1.0",
                 "rationale": "the two drivers move together against the project",
                 "variables": {"x1": 3.0, "x2": 2.0}},
                {"scenario_id": "RECOVERY", "name": "Recovery", "version": "1.0",
                 "rationale": "the recovery plan is achieved",
                 "variables": {"x1": 1.5, "x2": 1.0}}]}


def system_dynamics_model() -> dict:
    """Contract 5.5 oracle: backlog 10, new 5, completed 8, error 0.25 gives 9."""
    return {"source": "the weekly work in progress report", "model_version": "sd-1.0",
            "time_step": 1.0, "initial_backlog": 10.0,
            "steps": [{"step": 0, "new_work": 5.0, "work_completed": 8.0,
                       "error_rate": 0.25}]}


def queue_model(arrival: float = 2.0, service: float = 3.0, servers: int = 1) -> dict:
    """Contract 5.6 oracle: lambda 2, mu 3 gives rho 2/3, L 2, W 1, Lq 4/3, Wq 2/3."""
    return {"source": "the review workflow measurements", "model_version": "q-1.0",
            "queues": [{"queue_id": "RFI_REVIEW", "arrival_rate": arrival,
                        "service_rate": service, "servers": servers, "discipline": "FIFO"}]}


def agent_model(inventory: float = 2.0, demand: float = 2.0, delay: int = 1,
                steps: int = 6, disruption: float = 0.0, seed: int | None = None,
                replications: int | None = None) -> dict:
    """Contract 5.7 oracle: one supplier, one carrier, one project, hand-computed."""
    model = {
        "source": "the supply chain mapping workshop", "model_version": "abm-1.0",
        "environment": "a single delivery lane between one supplier and the site",
        "time_steps": steps, "travel_delay_steps": delay,
        "disruption_probability": disruption,
        "agents": [
            {"agent_id": "SUP-1", "agent_type": "SUPPLIER", "state": "NORMAL",
             "behaviour_rule": "SUPPLIER_SHIP_ONE_IF_STOCK_AND_REQUEST",
             "interaction_links": ["CAR-1"], "inventory": inventory},
            {"agent_id": "CAR-1", "agent_type": "CARRIER", "state": "AVAILABLE",
             "behaviour_rule": "CARRIER_COLLECT_ONE_AND_DELIVER_AFTER_DELAY",
             "interaction_links": ["SUP-1", "PRJ-1"]},
            {"agent_id": "PRJ-1", "agent_type": "PROJECT", "state": "NORMAL",
             "behaviour_rule": "PROJECT_POST_DEMAND_AND_COUNT_RECEIPTS",
             "interaction_links": ["SUP-1"], "demand": demand}]}
    if seed is not None:
        model["seed"] = seed
    if replications is not None:
        model["replications"] = replications
    return model


def des_model() -> dict:
    """Contract 5.8 oracle: A at 0 for 2 and B at 1 for 2 give a mean wait of 0.5."""
    return {"source": "the inspection queue observations", "model_version": "des-1.0",
            "queue_discipline": "FIFO", "termination_condition": "ALL_ENTITIES_DEPARTED",
            "resources": [{"resource_id": "INSPECTOR", "capacity": 1}],
            "entities": [{"entity_id": "A", "entity_type": "INSPECTION",
                          "arrival_time": 0.0, "service_time": 2.0},
                         {"entity_id": "B", "entity_type": "INSPECTION",
                          "arrival_time": 1.0, "service_time": 2.0}]}


def document_risk_evidence() -> dict:
    """Two findings under the confidence-weighted rule score 1.0 / 1.5 = 0.6667."""
    return {"source": "the document classification run of 30 June",
            "classifier_version": "rules-1.0", "taxonomy_id": "risk-taxonomy-1.0",
            "aggregation_rule": "SEVERITY_CONFIDENCE_WEIGHTED_MEAN", "coverage": 1.0,
            "findings": [
                {"finding_id": "F-001", "document_id": "DOC-1",
                 "document_type": "monthly_report",
                 "evidence_span": "the roofing works remain incomplete and are unresolved",
                 "risk_class": "SCHEDULE_SLIP", "extracted_candidate": "roofing incomplete",
                 "severity": 0.8, "confidence": 1.0, "effective_date": "2026-06-30"},
                {"finding_id": "F-002", "document_id": "DOC-1",
                 "document_type": "monthly_report",
                 "evidence_span": "a minor snag was noted at the east elevation",
                 "risk_class": "QUALITY", "extracted_candidate": "east elevation snag",
                 "severity": 0.4, "confidence": 0.5, "effective_date": "2026-06-30"}]}


#: Every Run-29 structure keyed by its signal-inputs key, for sweeps that need all of them.
ALL_STRUCTURES = {
    "documentRiskEvidence": document_risk_evidence,
    "rfiEventLog": rfi_event_log,
    "submittalDecisionRegister": submittal_register,
    "ncrExposureRecord": ncr_record,
    "weatherImpactEvents": weather_events,
    "changeEventRegister": change_register,
    "claimDisputeRegister": dispute_register,
    "subcontractorAssessments": subcontractor_assessment,
    "procurementItems": procurement_items,
    "specificationConflictRegister": conflict_register,
    "dsmDependencyModel": dsm_model,
    "sensitivityModel": sensitivity_model,
    "scenarioSet": scenario_set,
    "systemDynamicsModel": system_dynamics_model,
    "queueModel": queue_model,
    "agentSupplyChainModel": agent_model,
    "desProcessModel": des_model,
}
