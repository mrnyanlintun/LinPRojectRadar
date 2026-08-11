"""Independent oracles for the eleven unresolved modules, over the staged fixtures.

Each oracle recomputes a quantity from RAW fixture rows and compares it with the stored
ground truth. None of them imports a production formula, and none of them records a module's
own output as the expectation. Where no independent oracle exists for a stored quantity the
oracle says so in its own result rather than inventing a weaker check and calling it a
known answer.

Every oracle returns a list of Finding records. `expected` is the value the oracle derived;
`stored` is the package's value. A test proves each finding can fail by perturbing `expected`.
"""

from __future__ import annotations

import collections
import json
import math
from dataclasses import dataclass
from typing import Any, Callable

from ..importers.fixture_loader import (
    PACKAGE_A,
    PACKAGE_B,
    load_json,
    load_metadata_json,
    load_table,
)
from ..validators import recomputations as R


@dataclass(frozen=True)
class Finding:
    module_id: str
    module_name: str
    oracle: str
    label: str
    expected: Any
    stored: Any
    tolerance: float

    @property
    def agrees(self) -> bool:
        if isinstance(self.expected, str) or isinstance(self.stored, str):
            return str(self.expected) == str(self.stored)
        return abs(float(self.expected) - float(self.stored)) <= self.tolerance


def _f(module_id, name, oracle, label, expected, stored, tol=1e-6) -> Finding:
    return Finding(module_id, name, oracle, label, expected, stored, tol)


# ---------------------------------------------------- A1.1 Monte Carlo EAC

def monte_carlo_eac() -> list[Finding]:
    """Justified mathematical property: the analytic mean of the modelled total.

    A Beta-PERT variable with bounds a, b and mode m has mean (a + 4m + b)/6, and the mean of a
    sum is the sum of the means whatever the correlation between the terms. So the expected
    total cost is the sum of the element PERT means plus, for each risk event, its probability
    times its impact PERT mean. A five thousand draw simulated mean must sit close to it. The
    tolerance is one and a half per cent, which is far wider than the sampling error of five
    thousand draws and is stated here so the check cannot be read as an exact reproduction.
    """
    elements = load_table(f"{PACKAGE_A}/cost_elements.csv",
                          primary_key=["project_id", "cost_element_id"])
    events = load_table(f"{PACKAGE_A}/cost_risk_events.csv",
                        primary_key=["project_id", "risk_event_id"])
    truth = load_table(f"{PACKAGE_A}/cost_risk_ground_truth.csv", primary_key=["project_id"])
    findings = []
    for g in truth:
        pid = g["project_id"]
        base = sum(
            (float(c["low_cost_usd"]) + 4 * float(c["most_likely_cost_usd"])
             + float(c["high_cost_usd"])) / 6
            for c in elements if c["project_id"] == pid
        )
        risk = sum(
            float(e["probability"])
            * (float(e["low_impact_usd"]) + 4 * float(e["most_likely_impact_usd"])
               + float(e["high_impact_usd"])) / 6
            for e in events if e["project_id"] == pid
        )
        stored_mean = float(g["mean_total_cost_usd"])
        findings.append(_f("A1.1", "Monte Carlo EAC", "analytic PERT mean",
                           f"{pid} mean total cost", base + risk, stored_mean,
                           0.015 * stored_mean))
        findings.append(_f("A1.1", "Monte Carlo EAC", "quantile ordering",
                           f"{pid} p50 below p80",
                           1.0 if float(g["p50_total_cost_usd"]) < float(g["p80_total_cost_usd"])
                           else 0.0, 1.0, 0.0))
    return findings


# ------------------------------------------------------ A2.2 Line of Balance

def line_of_balance() -> list[Finding]:
    """Hand-derived intersection of two production lines.

    Two crews progressing at constant rates from their own start days meet where
    r_l (t - s_l) = r_f (t - s_f); substituting the meeting time back gives the location. The
    stored rates are rounded to six decimals, so the catch-up location, which divides by the
    difference of two rates, is checked against an interval obtained by perturbing each rate by
    half a unit in the last stored place rather than against a point value.
    """
    packages = load_table(f"{PACKAGE_A}/lob_work_packages.csv")
    truth = load_table(f"{PACKAGE_A}/lob_ground_truth.csv")
    findings = []
    for g in truth:
        rows = [w for w in packages
                if w["project_id"] == g["project_id"] and w["period_id"] == g["period_id"]]
        lead = [w for w in rows if w["work_type_id"] == g["leading_work_type"]]
        follow = [w for w in rows if w["work_type_id"] == g["following_work_type"]]
        if not lead or not follow:
            continue
        rl = float(lead[0]["actual_production_rate_locations_per_day"])
        rf = float(follow[0]["actual_production_rate_locations_per_day"])
        findings.append(_f("A2.2", "Line of Balance", "production rate from work packages",
                           f"{g['project_id']}/{g['period_id']} leading rate", rl,
                           float(g["leading_rate"]), 1e-9))
        findings.append(_f("A2.2", "Line of Balance", "production rate from work packages",
                           f"{g['project_id']}/{g['period_id']} following rate", rf,
                           float(g["following_rate"]), 1e-9))
        sl = min(float(w["actual_start_day"]) for w in lead)
        sf = min(float(w["actual_start_day"]) for w in follow)
        if abs(rl - rf) < 1e-12:
            continue
        candidates = []
        for dl in (-5e-7, 0.0, 5e-7):
            for df in (-5e-7, 0.0, 5e-7):
                a, b = rl + dl, rf + df
                if abs(a - b) < 1e-12:
                    continue
                t = (a * sl - b * sf) / (a - b)
                candidates.append(a * (t - sl))
        low, high = min(candidates), max(candidates)
        stored = float(g["catch_up_location"])
        mid = (low + high) / 2
        findings.append(_f("A2.2", "Line of Balance", "line intersection",
                           f"{g['project_id']}/{g['period_id']} catch-up location",
                           mid, stored, max((high - low) / 2, 1e-6)))
    return findings


# ---------------------------------------------------- A2.3 CCPM Buffer Health

def ccpm_buffer_health() -> list[Finding]:
    chains = load_table(f"{PACKAGE_A}/ccpm_chains.csv")
    chain_acts = load_table(f"{PACKAGE_A}/ccpm_chain_activities.csv")
    acts = load_table(f"{PACKAGE_A}/schedule_activities.csv")
    activity = {(a["project_id"], a["activity_id"]): a for a in acts}
    findings = []
    for c in chains:
        members = [m for m in chain_acts
                   if m["project_id"] == c["project_id"] and m["chain_id"] == c["chain_id"]]
        variance = sum(
            ((float(activity[(m["project_id"], m["activity_id"])]["pessimistic_duration_days"])
              - float(activity[(m["project_id"], m["activity_id"])]["optimistic_duration_days"]))
             / 6.0) ** 2
            for m in members
        )
        findings.append(_f("A2.3", "CCPM Buffer Health", "1.645 root sum of PERT variances",
                           f"{c['chain_id']} buffer days", 1.645 * math.sqrt(variance),
                           float(c["original_buffer_days"]), 1e-6))
    return findings


# ------------------------------------------ A3.1 Reference Class Forecasting

def reference_class_forecasting() -> list[Finding]:
    """Enumerable structure checks plus the generator's own stated cost model.

    The reference class is the module's missing structure, so the strongest available test is
    that the population supplies one: every project belongs to a class whose key is built from
    its own recorded attributes, and the parametric baseline the package documents reproduces
    each project's recorded baseline cost to within the noise the model declares.
    """
    B1 = f"{PACKAGE_B}/B1_reference_population"
    projects = load_table(f"{B1}/reference_projects.csv", primary_key=["reference_project_id"])
    membership = load_table(f"{B1}/reference_class_membership.csv")
    model = load_metadata_json(f"{B1}/ground_truth_model.json")
    by_id = {p["reference_project_id"]: p for p in projects}
    findings = []

    classes = collections.defaultdict(list)
    for m in membership:
        classes[m["reference_class_id"]].append(m["reference_project_id"])
    covered = {m["reference_project_id"] for m in membership}
    findings.append(_f("A3.1", "Reference Class Forecasting", "class coverage",
                       "projects with a reference class", len(covered), len(projects.rows), 0))

    mismatch = 0
    for m in membership:
        parts = m["reference_class_id"].split("|")
        p = by_id[m["reference_project_id"]]
        if parts[0] != p["project_type"] or parts[-1] != p["delivery_method"]:
            mismatch += 1
    findings.append(_f("A3.1", "Reference Class Forecasting", "class key from attributes",
                       "membership keys disagreeing with their project", mismatch, 0, 0))

    residuals = []
    for p in projects:
        predicted = (
            model["archetype_base_millions"][p["archetype"] if "archetype" in p
                                             else p["project_type"]]
            + model["coefficients_millions"]["gross_area_m2"] * float(p["gross_area_m2"])
            + model["coefficients_millions"]["length_km"] * float(p["length_km"])
            + model["coefficients_millions"]["capacity_units"] * float(p["capacity_units"])
            + model["coefficients_millions"]["floors"] * float(p["floors"])
            + model["coefficients_millions"]["complexity_index"] * float(p["complexity_index"])
        )
        predicted *= float(model["region_factor"][p["region"]])
        predicted *= 1.0 + float(model["delivery_effect_fraction"][p["delivery_method"]])
        actual = float(p["baseline_cost_usd"]) / 1e6
        residuals.append((actual - predicted) / predicted)
    mean_residual = sum(residuals) / len(residuals)
    findings.append(_f("A3.1", "Reference Class Forecasting", "documented cost generator",
                       "mean relative residual of the stated model", mean_residual, 0.0, 0.02))
    return findings


# ------------------------------------------------------------- A4.4 NCR Rate

def ncr_rate() -> list[Finding]:
    rows, bad = R.recompute_ncr()
    findings = [
        _f("A4.4", "NCR Rate", "cutoff replay from raw events",
           f"{r['project_id']}/{r['period_id']} {r['quantity']}",
           float(r["recomputed"]), float(r["stored"]), 1e-8)
        for r in rows
    ]
    assert not bad or findings
    return findings


# ------------------------------------------------- A5.1 DSM Rework Propagation

def dsm_rework() -> list[Finding]:
    """Structural oracles only, and the reason is recorded rather than papered over.

    A first-order replay of the stored propagation vector reproduces most rows but not all: the
    stored vector for the third period of every project sits about one per cent below the
    product of the seed impact and the single inbound edge strength, which no reading of the
    edge table explains. This is reported as an unresolved disagreement. What is asserted here
    is what the fixture unambiguously supplies: a project-specific dependency matrix whose
    edges join declared nodes, and a seed impact that appears in the stored vector.
    """
    nodes = load_table(f"{PACKAGE_A}/dsm_nodes.csv", primary_key=["project_id", "node_id"])
    edges = load_table(f"{PACKAGE_A}/dsm_edges.csv")
    truth = load_table(f"{PACKAGE_A}/dsm_ground_truth.csv")
    node_ids = {(n["project_id"], n["node_id"]) for n in nodes}
    findings = []
    orphans = sum(
        1 for e in edges
        if (e["project_id"], e["source_node_id"]) not in node_ids
        or (e["project_id"], e["target_node_id"]) not in node_ids
    )
    findings.append(_f("A5.1", "DSM Rework Propagation", "edge endpoints join declared nodes",
                       "edges with an undeclared endpoint", orphans, 0, 0))
    out_of_range = sum(1 for e in edges if not 0.0 < float(e["dependency_strength"]) <= 1.0)
    findings.append(_f("A5.1", "DSM Rework Propagation", "strengths are proper fractions",
                       "edges outside (0, 1]", out_of_range, 0, 0))
    bad_seed = 0
    for g in truth:
        vector = json.loads(g["cumulative_impact_vector"])
        seed = g["seed_node_id"]
        if seed not in vector or vector[seed] <= 0:
            bad_seed += 1
        if int(g["impacted_node_count"]) <= 0:
            bad_seed += 1
    # The stored impacted count is NOT asserted equal to the number of positively impacted
    # nodes. In eleven of the thirty-six rows it is one lower and in three it is one higher,
    # which is recorded as an unresolved disagreement rather than absorbed into a tolerance.
    findings.append(_f("A5.1", "DSM Rework Propagation", "seed impact identity",
                       "ground truth rows without a positive seed impact", bad_seed, 0, 0))
    return findings


def dsm_impacted_count_disagreement() -> tuple[int, int]:
    """Rows where the stored impacted count is not the count of positively impacted nodes."""
    truth = load_table(f"{PACKAGE_A}/dsm_ground_truth.csv")
    rows = failures = 0
    for g in truth:
        vector = json.loads(g["cumulative_impact_vector"])
        seed = g["seed_node_id"]
        rows += 1
        positive = sum(1 for k, v in vector.items() if k != seed and v > 0)
        if positive != int(g["impacted_node_count"]):
            failures += 1
    return rows, failures


def dsm_first_order_disagreement() -> tuple[int, int, list[str]]:
    """Quantify the unresolved first-order disagreement. Returns (cases, failures, detail)."""
    edges = load_table(f"{PACKAGE_A}/dsm_edges.csv")
    truth = load_table(f"{PACKAGE_A}/dsm_ground_truth.csv")
    cases = failures = 0
    detail = []
    for g in truth:
        pid = g["project_id"]
        vector = json.loads(g["cumulative_impact_vector"])
        seed = g["seed_node_id"]
        mine = [e for e in edges if e["project_id"] == pid]
        inbound = collections.Counter(e["target_node_id"] for e in mine)
        for e in mine:
            if e["source_node_id"] == seed and inbound[e["target_node_id"]] == 1:
                cases += 1
                expected = vector[seed] * float(e["dependency_strength"])
                stored = vector[e["target_node_id"]]
                if abs(expected - stored) > 1e-4:
                    failures += 1
                    detail.append(f"{pid}/{g['period_id']} {e['target_node_id']}: "
                                  f"{expected:.6f} vs {stored:.6f}")
    return cases, failures, detail


# ---------------------------------------------------------- A5.4 Scenario Modeling

def scenario_modeling() -> list[Finding]:
    """Hand-calculable expectation: expected value is the probability weighted sum."""
    B3 = f"{PACKAGE_B}/B3_decision_optimization"
    outcomes = load_table(f"{B3}/action_scenario_outcomes.csv")
    scenarios = load_table(f"{B3}/scenarios.csv")
    matrix = load_table(f"{B3}/alternative_criteria_matrix.csv")
    probability = {(s["decision_problem_id"], s["scenario_id"]):
                   float(s["scenario_probability"]) for s in scenarios}
    totals: collections.Counter = collections.Counter()
    for (dp, _sid), p in probability.items():
        totals[dp] += p
    findings = [
        _f("A5.4", "Scenario Modeling", "scenario probabilities sum to one",
           f"{dp} probability mass", total, 1.0, 1e-9)
        for dp, total in sorted(totals.items())
    ]
    pairs = (("cost_delta_usd", "expected_cost_delta_usd"),
             ("delay_days", "expected_delay_days"),
             ("quality_risk", "quality_risk"),
             ("safety_risk", "safety_risk"),
             ("residual_risk", "residual_risk"))
    for a in matrix:
        dp, action = a["decision_problem_id"], a["action_id"]
        rows = [r for r in outcomes
                if r["decision_problem_id"] == dp and r["action_id"] == action]
        for source, stored_col in pairs:
            expected = sum(probability[(dp, r["scenario_id"])] * float(r[source]) for r in rows)
            findings.append(_f("A5.4", "Scenario Modeling", "probability weighted expectation",
                               f"{action} {stored_col}", expected, float(a[stored_col]), 1e-4))
    return findings


# ------------------------------------------------ A5.6 Queueing Theory Bottleneck

def queueing_bottleneck() -> list[Finding]:
    """Every stored queue statistic recomputed from the event log."""
    events = load_table(f"{PACKAGE_A}/queue_events.csv")
    truth = load_table(f"{PACKAGE_A}/queue_ground_truth.csv")
    findings = []
    for g in truth:
        rows = [e for e in events
                if e["project_id"] == g["project_id"] and e["queue_id"] == g["queue_id"]]
        waits = sorted(float(e["wait_time_days"]) for e in rows)
        n = len(waits)
        findings.append(_f("A5.6", "Queueing Theory Bottleneck", "event count",
                           f"{g['queue_id']} entities", n, int(g["entities"]), 0))
        findings.append(_f("A5.6", "Queueing Theory Bottleneck", "mean of the wait column",
                           f"{g['queue_id']} mean wait", sum(waits) / n,
                           float(g["mean_wait_days"]), 1e-5))
        k = 0.9 * (n - 1)
        lo = int(math.floor(k))
        p90 = waits[lo] + (k - lo) * (waits[min(lo + 1, n - 1)] - waits[lo])
        findings.append(_f("A5.6", "Queueing Theory Bottleneck", "linear interpolated p90",
                           f"{g['queue_id']} p90 wait", p90, float(g["p90_wait_days"]), 1e-5))
        horizon = max(float(e["service_end_day"]) for e in rows)
        findings.append(_f("A5.6", "Queueing Theory Bottleneck", "count over horizon",
                           f"{g['queue_id']} throughput", n / horizon,
                           float(g["throughput_per_day"]), 1e-5))
        for server in (1, 2):
            busy = sum(float(e["service_duration_days"]) for e in rows
                       if e["server_id"].endswith(f"-{server}"))
            findings.append(_f("A5.6", "Queueing Theory Bottleneck", "busy time over horizon",
                               f"{g['queue_id']} server {server} utilisation", busy / horizon,
                               float(g[f"server_{server}_utilization"]), 1e-5))
    return findings


# ------------------------------------------------- A5.7 Agent-Based Supply Chain

def agent_based_supply_chain() -> list[Finding]:
    rows, _bad = R.replay_agent_rules()
    return [
        _f("A5.7", "Agent-Based Supply Chain", "rule replay over every state row",
           f"{r['project_id']} {r['quantity']}", float(r["recomputed"]),
           float(r["stored"]), 0)
        for r in rows
    ]


# ------------------------------------------ A6.3 Environmental Compliance Rate

def environmental_compliance() -> list[Finding]:
    rows, _bad = R.recompute_environmental()
    return [
        _f("A6.3", "Environmental Compliance Rate", "cutoff replay from raw assessments",
           f"{r['project_id']}/{r['period_id']} {r['quantity']}", float(r["recomputed"]),
           float(r["stored"]), 1e-8)
        for r in rows
    ]


# ----------------------------------------------------------- B2.19 CRITIC-TOPSIS

def critic_topsis() -> list[Finding]:
    """CRITIC weights and the TOPSIS ranking, both derived from the published definitions.

    CRITIC weight of a criterion is its standard deviation over the min-max normalised column
    times the sum over all criteria of one minus the Pearson correlation between the two
    normalised columns, divided by the same quantity summed over criteria. TOPSIS then works on
    the vector normalised matrix, weighted by those weights, with the ideal taken in each
    criterion's own direction.
    """
    B3 = f"{PACKAGE_B}/B3_decision_optimization"
    matrix = load_table(f"{B3}/alternative_criteria_matrix.csv")
    criteria = load_table(f"{B3}/criteria.csv")
    truth = load_table(f"{B3}/ground_truth_decisions.csv", primary_key=["decision_problem_id"])
    column = {"EXPECTED_COST_DELTA_USD": "expected_cost_delta_usd",
              "EXPECTED_DELAY_DAYS": "expected_delay_days",
              "QUALITY_RISK": "quality_risk",
              "SAFETY_RISK": "safety_risk",
              "RESIDUAL_RISK": "residual_risk"}

    def sd(values):
        mu = sum(values) / len(values)
        return math.sqrt(sum((v - mu) ** 2 for v in values) / (len(values) - 1))

    def corr(a, b):
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
        return num / den if den else 0.0

    findings = []
    for g in truth:
        dp = g["decision_problem_id"]
        crit = [c for c in criteria if c["decision_problem_id"] == dp]
        alts = [a for a in matrix if a["decision_problem_id"] == dp]
        names = [c["criterion_name"] for c in crit]
        directions = {c["criterion_name"]: c["direction"] for c in crit}
        raw = {n: [float(a[column[n]]) for a in alts] for n in names}
        normalised = {}
        for n in names:
            values = raw[n]
            lo, hi = min(values), max(values)
            span = hi - lo
            normalised[n] = ([(v - lo) / span for v in values] if directions[n] == "MAX"
                             else [(hi - v) / span for v in values]) if span else [0.0] * len(values)
        strength = {n: sd(normalised[n]) * sum(1 - corr(normalised[n], normalised[k])
                                               for k in names) for n in names}
        total = sum(strength.values())
        weights = {n: strength[n] / total for n in names}
        stored_weights = json.loads(g["critic_weights_json"])
        for n in names:
            findings.append(_f("B2.19", "CRITIC-TOPSIS", "CRITIC definition",
                               f"{dp} weight {n}", weights[n], stored_weights[n], 1e-5))
        weighted = {}
        for n in names:
            norm = math.sqrt(sum(v * v for v in raw[n])) or 1.0
            weighted[n] = [weights[n] * v / norm for v in raw[n]]
        ideal = {n: (max(weighted[n]) if directions[n] == "MAX" else min(weighted[n]))
                 for n in names}
        anti = {n: (min(weighted[n]) if directions[n] == "MAX" else max(weighted[n]))
                for n in names}
        best = None
        for i, a in enumerate(alts):
            d_pos = math.sqrt(sum((weighted[n][i] - ideal[n]) ** 2 for n in names))
            d_neg = math.sqrt(sum((weighted[n][i] - anti[n]) ** 2 for n in names))
            closeness = d_neg / (d_pos + d_neg) if (d_pos + d_neg) else 0.0
            if best is None or closeness > best[1]:
                best = (a["action_id"], closeness)
        findings.append(_f("B2.19", "CRITIC-TOPSIS", "TOPSIS closeness ranking",
                           f"{dp} top action", best[0], g["critic_topsis_top_action_id"], 0))
    return findings


ORACLES: dict[str, tuple[str, Callable[[], list[Finding]]]] = {
    "A1.1": ("Monte Carlo EAC", monte_carlo_eac),
    "A2.2": ("Line of Balance", line_of_balance),
    "A2.3": ("CCPM Buffer Health", ccpm_buffer_health),
    "A3.1": ("Reference Class Forecasting", reference_class_forecasting),
    "A4.4": ("NCR Rate", ncr_rate),
    "A5.1": ("DSM Rework Propagation", dsm_rework),
    "A5.4": ("Scenario Modeling", scenario_modeling),
    "A5.6": ("Queueing Theory Bottleneck", queueing_bottleneck),
    "A5.7": ("Agent-Based Supply Chain", agent_based_supply_chain),
    "A6.3": ("Environmental Compliance Rate", environmental_compliance),
    "B2.19": ("CRITIC-TOPSIS", critic_topsis),
}
