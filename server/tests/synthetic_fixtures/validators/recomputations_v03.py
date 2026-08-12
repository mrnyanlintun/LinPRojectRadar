"""Independent recomputation of the v0.3 Monte Carlo and DSM ground truth.

Independent means: every expected quantity here is derived from a stated definition applied
to the raw stochastic inputs and the raw dependency structure. Nothing here reads a stored
total and compares it with itself, and nothing here imports the generator.

The two stated definitions, in full, are:

MONTE CARLO. Each cost element is a triangular variable on (low, most likely, high), so its
expectation is (a + m + b) / 3. Element dependence is induced by a Gaussian copula, which
changes the joint distribution and leaves every marginal, and therefore every marginal
expectation, alone; the expectation of the total is the sum of the element expectations
whatever the correlation. Each risk event is an independent Bernoulli occurrence times a
triangular impact, so its expected contribution is probability times (a + m + b) / 3. The
expected total is the sum of both. A simulated mean is judged against z times the standard
error of the mean, not against a percentage.

DSM. matrix[target, source] carries the rework strength of the edge from source to target.
The seed vector holds the seed magnitude at the seed node and zero elsewhere. Step k is the
matrix applied to step k minus one, starting from the seed vector. The propagated vector is
the sum of the step vectors and excludes the seed. The cumulative state is the seed plus the
propagated vector. Counts are reported twice, once including the seed node and once
excluding it, and the material counts apply the stored threshold. Propagation is truncated
at the stored number of steps; the graphs contain a cycle and the stored state is a partial
sum, not the limit of the series.
"""

from __future__ import annotations

import json
import math
from typing import Any

from ..importers import fixture_loader_v03 as FL

PACKAGE_A = FL.PACKAGE_A


def triangular_mean(low: Any, mode: Any, high: Any) -> float:
    return (float(low) + float(mode) + float(high)) / 3.0


def beta_pert_mean(low: Any, mode: Any, high: Any, lamb: float = 4.0) -> float:
    """Present only so the report can quantify the family the oracle must not assume."""
    return (float(low) + lamb * float(mode) + float(high)) / (2.0 + lamb)


def _close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= tol


# --------------------------------------------------------------- Monte Carlo


def recompute_monte_carlo() -> tuple[list[dict[str, Any]], list[str]]:
    elements = FL.load_table(f"{PACKAGE_A}/cost_elements.csv",
                             primary_key=["project_id", "cost_element_id"])
    events = FL.load_table(f"{PACKAGE_A}/cost_risk_events.csv",
                           primary_key=["project_id", "risk_event_id"])
    components = FL.load_table(f"{PACKAGE_A}/cost_risk_component_ground_truth.csv",
                               primary_key=["project_id", "component_id"])
    truth = FL.load_table(f"{PACKAGE_A}/cost_risk_ground_truth.csv",
                          primary_key=["project_id"])
    contract = FL.load_json(f"{PACKAGE_A}/monte_carlo_contract.json")
    z = float(contract["acceptance_rule"]["z"])

    rows: list[dict[str, Any]] = []
    bad: list[str] = []

    declared = {row["cost_distribution_type"] for row in elements}
    if declared != {"TRIANGULAR"}:
        bad.append(f"cost elements declare {declared}, not TRIANGULAR")
    declared_impact = {row["impact_distribution_type"] for row in events}
    if declared_impact != {"TRIANGULAR"}:
        bad.append(f"risk impacts declare {declared_impact}, not TRIANGULAR")
    if {row["occurrence_model"] for row in events} != {"BERNOULLI"}:
        bad.append("risk occurrence is not declared Bernoulli")

    for row in elements:
        low, mode, high = (float(row["low_cost_usd"]), float(row["most_likely_cost_usd"]),
                           float(row["high_cost_usd"]))
        if not low <= mode <= high:
            bad.append(f"{row['cost_element_id']}: low, mode, high are out of order")
    for row in events:
        low, mode, high = (float(row["low_impact_usd"]),
                           float(row["most_likely_impact_usd"]),
                           float(row["high_impact_usd"]))
        if not low <= mode <= high:
            bad.append(f"{row['risk_event_id']}: impact bounds are out of order")
        if not 0.0 <= float(row["probability"]) <= 1.0:
            bad.append(f"{row['risk_event_id']}: probability outside zero to one")

    component_by_id = {(r["project_id"], r["component_id"]): r for r in components}
    for row in elements:
        key = (row["project_id"], row["cost_element_id"])
        stored = component_by_id.get(key)
        if stored is None:
            bad.append(f"no component row for {key}")
            continue
        expected = triangular_mean(row["low_cost_usd"], row["most_likely_cost_usd"],
                                   row["high_cost_usd"])
        ok = _close(expected, float(stored["analytic_expected_value_usd"]), 1e-4)
        rows.append({"check": "mc_component", "project_id": row["project_id"],
                     "key": row["cost_element_id"], "quantity": "analytic_expected_value_usd",
                     "recomputed": round(expected, 6),
                     "stored": stored["analytic_expected_value_usd"], "agrees": ok})
        if not ok:
            bad.append(f"element expectation {key}")
    for row in events:
        key = (row["project_id"], row["risk_event_id"])
        stored = component_by_id.get(key)
        if stored is None:
            bad.append(f"no component row for {key}")
            continue
        expected = float(row["probability"]) * triangular_mean(
            row["low_impact_usd"], row["most_likely_impact_usd"], row["high_impact_usd"])
        ok = _close(expected, float(stored["analytic_expected_value_usd"]), 1e-4)
        rows.append({"check": "mc_component", "project_id": row["project_id"],
                     "key": row["risk_event_id"], "quantity": "analytic_expected_value_usd",
                     "recomputed": round(expected, 6),
                     "stored": stored["analytic_expected_value_usd"], "agrees": ok})
        if not ok:
            bad.append(f"risk contribution {key}")

    for row in truth:
        pid = row["project_id"]
        element_sum = sum(
            triangular_mean(e["low_cost_usd"], e["most_likely_cost_usd"], e["high_cost_usd"])
            for e in elements if e["project_id"] == pid
        )
        risk_sum = sum(
            float(e["probability"]) * triangular_mean(
                e["low_impact_usd"], e["most_likely_impact_usd"], e["high_impact_usd"])
            for e in events if e["project_id"] == pid
        )
        analytic = element_sum + risk_sum
        iterations = int(row["monte_carlo_iterations"])
        sd = float(row["simulated_sd_total_cost_usd"])
        se = sd / math.sqrt(iterations)
        error = abs(float(row["simulated_mean_total_cost_usd"]) - analytic)

        for quantity, recomputed, stored in [
            ("analytic_expected_element_cost_usd", element_sum,
             row["analytic_expected_element_cost_usd"]),
            ("analytic_expected_risk_contribution_usd", risk_sum,
             row["analytic_expected_risk_contribution_usd"]),
            ("analytic_expected_total_cost_usd", analytic,
             row["analytic_expected_total_cost_usd"]),
            ("simulated_standard_error_usd", se, row["simulated_standard_error_usd"]),
            ("acceptance_threshold_usd", z * se, row["acceptance_threshold_usd"]),
            ("absolute_mean_error_usd", error, row["absolute_mean_error_usd"]),
            ("mean_error_in_standard_errors", error / se,
             row["mean_error_in_standard_errors"]),
        ]:
            ok = _close(recomputed, float(stored), max(1e-2, abs(float(stored)) * 1e-9))
            rows.append({"check": "mc_project", "project_id": pid, "key": pid,
                         "quantity": quantity, "recomputed": round(recomputed, 6),
                         "stored": stored, "agrees": ok})
            if not ok:
                bad.append(f"{pid} {quantity}: {recomputed} != {stored}")

        within = error <= z * se
        rows.append({"check": "mc_project", "project_id": pid, "key": pid,
                     "quantity": "mean_within_z_standard_errors",
                     "recomputed": within, "stored": row["mean_check_passed"],
                     "agrees": within and str(row["mean_check_passed"]).lower() == "true"})
        if not within:
            bad.append(f"{pid}: simulated mean is {error / se:.2f} standard errors from the "
                       f"analytic mean, outside z = {z}")
        if not (float(row["p50_total_cost_usd"]) <= float(row["p80_total_cost_usd"])
                <= float(row["p90_total_cost_usd"])):
            bad.append(f"{pid}: quantiles are out of order")
        if iterations <= 0:
            bad.append(f"{pid}: iteration count is not positive")
        if not str(row["rng_implementation"]).startswith("numpy.random"):
            bad.append(f"{pid}: the random number generator is not declared")

    return rows, bad


def monte_carlo_pert_gap() -> list[dict[str, Any]]:
    """How far a Beta-PERT oracle would have been from the triangular truth, per project.

    This is the Run 9 finding, quantified. It is reported, not asserted away.
    """
    elements = FL.load_table(f"{PACKAGE_A}/cost_elements.csv")
    events = FL.load_table(f"{PACKAGE_A}/cost_risk_events.csv")
    truth = FL.load_table(f"{PACKAGE_A}/cost_risk_ground_truth.csv")
    out: list[dict[str, Any]] = []
    for row in truth:
        pid = row["project_id"]
        triangular = sum(
            triangular_mean(e["low_cost_usd"], e["most_likely_cost_usd"], e["high_cost_usd"])
            for e in elements if e["project_id"] == pid
        ) + sum(
            float(e["probability"]) * triangular_mean(
                e["low_impact_usd"], e["most_likely_impact_usd"], e["high_impact_usd"])
            for e in events if e["project_id"] == pid
        )
        pert = sum(
            beta_pert_mean(e["low_cost_usd"], e["most_likely_cost_usd"], e["high_cost_usd"])
            for e in elements if e["project_id"] == pid
        ) + sum(
            float(e["probability"]) * beta_pert_mean(
                e["low_impact_usd"], e["most_likely_impact_usd"], e["high_impact_usd"])
            for e in events if e["project_id"] == pid
        )
        mean = float(row["simulated_mean_total_cost_usd"])
        out.append({
            "project_id": pid,
            "triangular_analytic_mean": round(triangular, 2),
            "beta_pert_analytic_mean": round(pert, 2),
            "simulated_mean": round(mean, 2),
            "error_against_triangular_pct": round((mean / triangular - 1) * 100, 6),
            "error_against_beta_pert_pct": round((mean / pert - 1) * 100, 6),
        })
    return out


def monte_carlo_known_answers() -> tuple[list[dict[str, Any]], list[str]]:
    cases = FL.load_table(f"{PACKAGE_A}/monte_carlo_known_answer_cases.csv")
    truth = FL.load_table(f"{PACKAGE_A}/monte_carlo_known_answer_ground_truth.csv",
                          primary_key=["case_id"])
    contract = FL.load_json(f"{PACKAGE_A}/monte_carlo_contract.json")
    z = float(contract["acceptance_rule"]["z"])
    rows: list[dict[str, Any]] = []
    bad: list[str] = []
    for row in truth:
        case_id = row["case_id"]
        parts = [c for c in cases if c["case_id"] == case_id]
        if not parts:
            bad.append(f"{case_id}: no case components")
            continue
        analytic = 0.0
        for part in parts:
            weight = (1.0 if part["component_kind"] == "COST_ELEMENT"
                      else float(part["occurrence_probability"]))
            analytic += weight * triangular_mean(part["low"], part["most_likely"], part["high"])
        stored_analytic = float(row["analytic_expected_total_usd"])
        ok = _close(analytic, stored_analytic, 1e-6)
        rows.append({"case_id": case_id, "quantity": "analytic_expected_total_usd",
                     "recomputed": round(analytic, 6), "stored": stored_analytic,
                     "agrees": ok})
        if not ok:
            bad.append(f"{case_id}: hand expectation {analytic} != stored {stored_analytic}")
        error = abs(float(row["simulated_mean_total_usd"]) - analytic)
        deterministic = str(row["deterministic_case"]).lower() == "true"
        threshold = 1e-9 if deterministic else z * float(row["simulated_standard_error_usd"])
        inside = error <= threshold
        rows.append({"case_id": case_id, "quantity": "simulated_mean_within_threshold",
                     "recomputed": round(error, 9), "stored": round(threshold, 9),
                     "agrees": inside})
        if not inside:
            bad.append(f"{case_id}: simulated mean outside its threshold")
    return rows, bad


# --------------------------------------------------------------- DSM


def _matrix(node_ids: list[str], edges: list[dict[str, Any]], key: str, value: str):
    index = {node: position for position, node in enumerate(node_ids)}
    size = len(node_ids)
    matrix = [[0.0] * size for _ in range(size)]
    for edge in edges:
        matrix[index[edge["target_node_id"]]][index[edge["source_node_id"]]] = float(
            edge["dependency_strength"]
        )
    return index, matrix


def _apply(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(matrix[i][j] * vector[j] for j in range(len(vector))) for i in range(len(vector))]


def propagate(matrix: list[list[float]], seed_vector: list[float], steps: int):
    current = list(seed_vector)
    step_vectors = []
    for _ in range(steps):
        current = _apply(matrix, current)
        step_vectors.append(list(current))
    propagated = [sum(step[i] for step in step_vectors) if step_vectors else 0.0
                  for i in range(len(seed_vector))]
    cumulative = [seed_vector[i] + propagated[i] for i in range(len(seed_vector))]
    first_order = step_vectors[0] if step_vectors else [0.0] * len(seed_vector)
    return first_order, propagated, cumulative


def _check_dsm_rows(truth, nodes, edges, key_column: str, label: str):
    rows: list[dict[str, Any]] = []
    bad: list[str] = []
    for row in truth:
        key = row[key_column]
        node_ids = [n["node_id"] for n in nodes if n[key_column] == key]
        my_edges = [e for e in edges if e[key_column] == key]
        index, matrix = _matrix(node_ids, my_edges, key_column, "dependency_strength")
        seed_vector = [0.0] * len(node_ids)
        seed_vector[index[row["seed_node_id"]]] = float(row["seed_magnitude"])
        first_order, propagated, cumulative = propagate(
            matrix, seed_vector, int(row["propagation_steps"])
        )
        threshold = float(row["materiality_threshold"])
        stored_first = json.loads(row["first_order_impact_vector"])
        stored_prop = json.loads(row["propagated_impact_vector"])
        stored_cum = json.loads(row["cumulative_state_vector"])
        stored_seed = json.loads(row["seed_impact_vector"])
        period = row.get("period_id", "KNOWN_ANSWER")

        quantities = [
            ("total_first_order_impact", sum(first_order), row["total_first_order_impact"]),
            ("total_propagated_impact_excluding_seed", sum(propagated),
             row["total_propagated_impact_excluding_seed"]),
            ("total_state_including_seed", sum(cumulative),
             row["total_state_including_seed"]),
            ("positive_impacted_node_count_excluding_seed",
             sum(1 for n, i in index.items()
                 if n != row["seed_node_id"] and propagated[i] > 0),
             row["positive_impacted_node_count_excluding_seed"]),
            ("positive_state_node_count_including_seed",
             sum(1 for value in cumulative if value > 0),
             row["positive_state_node_count_including_seed"]),
            ("material_impacted_node_count_excluding_seed",
             sum(1 for n, i in index.items()
                 if n != row["seed_node_id"] and propagated[i] > threshold),
             row["material_impacted_node_count_excluding_seed"]),
            ("material_state_node_count_including_seed",
             sum(1 for value in cumulative if value > threshold),
             row["material_state_node_count_including_seed"]),
        ]
        for quantity, recomputed, stored in quantities:
            ok = _close(recomputed, float(stored), 1e-5)
            rows.append({"check": label, "key": key, "period": period, "quantity": quantity,
                         "recomputed": round(float(recomputed), 6), "stored": stored,
                         "agrees": ok})
            if not ok:
                bad.append(f"{label} {key}/{period} {quantity}: {recomputed} != {stored}")
        for name, computed, stored_vector in [
            ("seed_impact_vector", seed_vector, stored_seed),
            ("first_order_impact_vector", first_order, stored_first),
            ("propagated_impact_vector", propagated, stored_prop),
            ("cumulative_state_vector", cumulative, stored_cum),
        ]:
            ok = all(_close(stored_vector[node], computed[i], 1e-5)
                     for node, i in index.items())
            rows.append({"check": label, "key": key, "period": period, "quantity": name,
                         "recomputed": "recomputed vector", "stored": "stored vector",
                         "agrees": ok})
            if not ok:
                bad.append(f"{label} {key}/{period} {name} disagrees")
        if str(row["seed_included_in_cumulative_state"]).lower() != "true":
            bad.append(f"{label} {key}/{period}: seed inclusion flag is not declared true")
        if str(row["seed_included_in_propagated_impact"]).lower() != "false":
            bad.append(f"{label} {key}/{period}: propagated impact claims to include the seed")
    return rows, bad


def recompute_dsm() -> tuple[list[dict[str, Any]], list[str]]:
    nodes = FL.load_table(f"{PACKAGE_A}/dsm_nodes.csv",
                          primary_key=["project_id", "node_id"])
    edges = FL.load_table(f"{PACKAGE_A}/dsm_edges.csv")
    truth = FL.load_table(f"{PACKAGE_A}/dsm_ground_truth.csv",
                          primary_key=["project_id", "period_id"])
    rows, bad = _check_dsm_rows(truth, nodes, edges, "project_id", "dsm_programme")
    contract = FL.load_json(f"{PACKAGE_A}/dsm_contract.json")
    threshold = float(contract["materiality_threshold"])
    for row in truth:
        if not _close(float(row["materiality_threshold"]), threshold, 1e-12):
            bad.append(f"{row['project_id']}/{row['period_id']}: threshold differs from the "
                       "declared contract")
    if not contract.get("cycle_handling"):
        bad.append("the contract does not state how cycles are handled")
    return rows, bad


def recompute_dsm_known_answers() -> tuple[list[dict[str, Any]], list[str]]:
    nodes = FL.load_table(f"{PACKAGE_A}/dsm_known_answer_nodes.csv",
                          primary_key=["case_id", "node_id"])
    edges = FL.load_table(f"{PACKAGE_A}/dsm_known_answer_edges.csv")
    truth = FL.load_table(f"{PACKAGE_A}/dsm_known_answer_ground_truth.csv",
                          primary_key=["case_id"])
    return _check_dsm_rows(truth, nodes, edges, "case_id", "dsm_known_answer")
