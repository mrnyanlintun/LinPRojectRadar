"""
RUN 30 -- SYNTHETIC RESEARCH FIXTURES FOR THE CATEGORY-6/7 CANONICAL STRUCTURES.

EVERY STRUCTURE BUILT HERE IS SYNTHETIC. Each carries `data_origin =
SYNTHETIC_RESEARCH_FIXTURE` and `not_for_empirical_validation = True`, because a synthetic
structure verifies MATHEMATICS AND ONLY MATHEMATICS. Nothing here is evidence about any project,
and a canonical success against one of these fixtures proves an implementation is correct, never
that a reading taken from it would be true in the field.

NOTHING HERE IS DERIVED FROM CPI, SPI OR A DOCUMENT RISK SCORE. That is the whole point of the
Run-30 contract: an epistemic object is supplied by whoever assessed it, or it does not exist.
"""

from __future__ import annotations

ORIGIN = {"data_origin": "SYNTHETIC_RESEARCH_FIXTURE", "not_for_empirical_validation": True}


def _base(**kw):
    out = dict(ORIGIN)
    out.update(kw)
    return out


# ------------------------------------------------------------------ 7.1 Dempster-Shafer
def dst_independent():
    """The contract's oracle pair, carried on two genuinely distinct evidence sources."""
    return _base(
        frame=["G", "R"],
        bodies=[
            {"body_id": "cost-review", "evidence_source": "independent cost review panel",
             "masses": [{"subset": ["G"], "mass": 0.6}, {"subset": ["G", "R"], "mass": 0.4}]},
            {"body_id": "site-inspection", "evidence_source": "site inspection report",
             "masses": [{"subset": ["G"], "mass": 0.5}, {"subset": ["G", "R"], "mass": 0.5}]},
        ])


def dst_same_source():
    """Two readings of ONE source. Dempster's rule may not be applied across them."""
    return _base(
        frame=["G", "R"],
        bodies=[
            {"body_id": "read-a", "evidence_source": "monthly cost report",
             "masses": [{"subset": ["G"], "mass": 0.6}, {"subset": ["G", "R"], "mass": 0.4}]},
            {"body_id": "read-b", "evidence_source": "monthly cost report",
             "masses": [{"subset": ["G"], "mass": 0.5}, {"subset": ["G", "R"], "mass": 0.5}]},
        ])


# ------------------------------------------------------------------ 7.2 Rough Sets
def rough_table():
    """U = {1,2,3,4}; the condition attributes give classes {1,2} and {3,4}; X = {1,3,4}."""
    return _base(
        condition_attributes=["a", "b"],
        decision_attribute="d",
        target_decision="X",
        cases=[
            {"case_id": "1", "a": "p", "b": "q", "d": "X"},
            {"case_id": "2", "a": "p", "b": "q", "d": "notX"},
            {"case_id": "3", "a": "r", "b": "s", "d": "X"},
            {"case_id": "4", "a": "r", "b": "s", "d": "X"},
        ])


def rough_single_row():
    t = rough_table()
    t["cases"] = t["cases"][:1]
    return t


def rough_no_decision():
    t = rough_table()
    del t["decision_attribute"]
    return t


# ------------------------------------------------------------------ 7.3 - 7.6
def neutrosophic(t, i, f):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 truth=t, indeterminacy=i, falsity=f)


def interval(lower, upper):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 lower=lower, upper=upper)


def z_number(a_term, b_term):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 restriction={"term": a_term}, reliability={"term": b_term})


def plts(pairs):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 terms=[{"term": t, "probability": p} for t, p in pairs])


# ------------------------------------------------------------------ 7.7 Plithogenic
def plithogenic(appurtenance=0.7):
    return _base(
        research_origin="Run-30 laboratory structure", source="synthetic research fixture",
        attributes=[
            {"attribute": "delivery", "dominant_value": "on-time",
             "values": [{"value": "on-time", "appurtenance": appurtenance,
                         "contradiction": 0.0},
                        {"value": "late", "appurtenance": 0.3, "contradiction": 1.0}]},
        ])


# ------------------------------------------------------------------ 7.8 Belief Rule Base
def brb_single_rule():
    return _base(
        elicited_from="research panel", source="synthetic elicitation exercise",
        consequents=["Green", "Amber", "Red"],
        attribute_weights={"cost_state": 1.0, "schedule_state": 1.0},
        rules=[{"rule_id": "R1", "rule_weight": 1.0, "activation": 1.0,
                "antecedents": {"cost_state": "good", "schedule_state": "good"},
                "beliefs": {"Green": 0.7, "Amber": 0.2, "Red": 0.1}}])


def brb_two_rules():
    s = brb_single_rule()
    s["rules"] = list(s["rules"]) + [
        {"rule_id": "R2", "rule_weight": 1.0, "activation": 0.6,
         "antecedents": {"cost_state": "poor", "schedule_state": "good"},
         "beliefs": {"Green": 0.1, "Amber": 0.3, "Red": 0.6}}]
    return s


def brb_invalid_distribution():
    s = brb_single_rule()
    s["rules"] = [dict(s["rules"][0], beliefs={"Green": 0.7, "Amber": 0.5, "Red": 0.3})]
    return s


def brb_no_attribute_weights():
    s = brb_single_rule()
    del s["attribute_weights"]
    return s


# ------------------------------------------------------------------ 7.10 - 7.17 fuzzy family
def pyth(mu, nu):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 membership=mu, non_membership=nu)


def picture(pos, neu, neg):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 positive=pos, neutral=neu, negative=neg)


def hesitant(degrees):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 degrees=list(degrees))


def type2(points):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 points=[{"x": x, "lower": lo, "upper": up} for x, lo, up in points])


def spherical(mu, nu, pi):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 membership=mu, non_membership=nu, hesitancy=pi)


def fermatean(mu, nu):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 membership=mu, non_membership=nu)


# ------------------------------------------------------------------ 7.14 Maximum Entropy
def maxent_two_states():
    """Oracle A: two states, normalisation only."""
    return _base(defined_by="research panel", source="synthetic research fixture",
                 states=[{"state": "s1"}, {"state": "s2"}], constraints=[])


def maxent_expectation(target):
    """Oracle B: x in {0,1,2} with a supplied expectation constraint."""
    return _base(defined_by="research panel", source="synthetic research fixture",
                 states=[{"state": "x0"}, {"state": "x1"}, {"state": "x2"}],
                 constraints=[{"constraint": "mean", "values": [0, 1, 2],
                               "expectation": target}])


# ------------------------------------------------------------------ 7.15 Possibility
def possibility(degrees):
    return _base(assessed_by="research panel", source="elicitation exercise",
                 states=[{"state": k, "possibility": v} for k, v in degrees.items()])


# ------------------------------------------------------------------ 7.18 / 7.19 decisions
def _criteria(weights=True, flip=False, no_orientation=False, no_source=False):
    c3 = "benefit" if flip else "cost"
    rows = [
        {"criterion_id": "C1", "label": "capability", "orientation": "benefit",
         "units": "points"},
        {"criterion_id": "C2", "label": "resilience", "orientation": "benefit",
         "units": "points"},
        {"criterion_id": "C3", "label": "whole-life cost", "orientation": c3,
         "units": "index"},
    ]
    if no_orientation:
        del rows[0]["orientation"]
    if weights:
        for row, w in zip(rows, (0.5, 0.3, 0.2)):
            row["weight"] = w
            if not no_source:
                row["weight_source"] = "supervisory benchmark weights, hand derived for Run 30"
    return rows


def marcos_benchmark():
    """HAND_DERIVED_CANONICAL_FIXTURE. 3 alternatives x 3 criteria, one cost criterion."""
    return _base(
        context_id="run30-marcos-benchmark", source="hand derived canonical fixture, Run 30",
        period=7, criteria=_criteria(weights=True),
        alternatives=[
            {"alternative_id": "A1", "label": "Option A",
             "values": {"C1": 4, "C2": 3, "C3": 2}},
            {"alternative_id": "A2", "label": "Option B",
             "values": {"C1": 2, "C2": 5, "C3": 4}},
            {"alternative_id": "A3", "label": "Option C",
             "values": {"C1": 3, "C2": 1, "C3": 1}},
        ])


def marcos_identical():
    s = marcos_benchmark()
    s["alternatives"] = list(s["alternatives"]) + [
        {"alternative_id": "A_copy", "label": "Option A again",
         "values": {"C1": 4, "C2": 3, "C3": 2}}]
    s["alternatives"][0]["alternative_id"] = "A"
    return s


def marcos_dominated():
    s = marcos_benchmark()
    s["alternatives"] = list(s["alternatives"]) + [
        {"alternative_id": "DOM", "label": "dominated on every criterion",
         "values": {"C1": 1, "C2": 1, "C3": 9}}]
    return s


def marcos_single_alternative():
    s = marcos_benchmark()
    s["alternatives"] = s["alternatives"][:1]
    return s


def marcos_criteria_as_alternatives():
    """cpi, spi and docRiskScore presented as three 'alternatives' on one 'criterion'."""
    return _base(
        context_id="bad", source="the defect this contract forbids", period=7,
        criteria=[{"criterion_id": "value", "orientation": "benefit", "weight": 1.0,
                   "weight_source": "none"}],
        alternatives=[
            {"alternative_id": "cpi", "values": {"value": 0.94}},
            {"alternative_id": "spi", "values": {"value": 0.91}},
            {"alternative_id": "docRiskScore", "values": {"value": 0.42}},
        ])


def marcos_no_orientation():
    s = marcos_benchmark()
    s["criteria"] = _criteria(weights=True, no_orientation=True)
    return s


def marcos_no_weight_source():
    s = marcos_benchmark()
    s["criteria"] = _criteria(weights=True, no_source=True)
    return s


def critic_benchmark(reverse=False, flip_orientation=False):
    """HAND_DERIVED_CANONICAL_FIXTURE. 4 alternatives x 3 criteria, C3 a cost criterion."""
    alts = [
        {"alternative_id": "A1", "label": "Option A", "values": {"C1": 8, "C2": 5, "C3": 3}},
        {"alternative_id": "A2", "label": "Option B", "values": {"C1": 6, "C2": 7, "C3": 5}},
        {"alternative_id": "A3", "label": "Option C", "values": {"C1": 9, "C2": 4, "C3": 6}},
        {"alternative_id": "A4", "label": "Option D", "values": {"C1": 5, "C2": 8, "C3": 2}},
    ]
    if reverse:
        alts = list(reversed(alts))
    return _base(
        context_id="run30-critic-benchmark", source="hand derived canonical fixture, Run 30",
        period=7, criteria=_criteria(weights=False, flip=flip_orientation), alternatives=alts)


def critic_identical():
    s = critic_benchmark()
    s["alternatives"][0]["alternative_id"] = "A"
    s["alternatives"] = list(s["alternatives"]) + [
        {"alternative_id": "A_copy", "label": "Option A again",
         "values": {"C1": 8, "C2": 5, "C3": 3}}]
    return s


def critic_single_row():
    s = critic_benchmark()
    s["alternatives"] = s["alternatives"][:1]
    return s


def critic_zero_variance():
    s = critic_benchmark()
    for a in s["alternatives"]:
        a["values"] = dict(a["values"], C2=5)
    return s


# ------------------------------------------------------------------ 7.20 Hypersoft
def hypersoft_complete():
    return _base(
        research_origin="Run-30 laboratory structure", source="synthetic research fixture",
        attributes=[{"attribute": "A1", "values": ["a1", "a2"]},
                    {"attribute": "A2", "values": ["b1", "b2"]}],
        mapping=[{"tuple": ["a1", "b1"], "approximation": ["u1"]},
                 {"tuple": ["a1", "b2"], "approximation": ["u2"]},
                 {"tuple": ["a2", "b1"], "approximation": ["u1", "u3"]},
                 {"tuple": ["a2", "b2"], "approximation": []}])


def hypersoft_missing():
    s = hypersoft_complete()
    s["mapping"] = [m for m in s["mapping"] if m["tuple"] != ["a2", "b2"]]
    return s


def hypersoft_overlapping():
    s = hypersoft_complete()
    s["attributes"] = [{"attribute": "A1", "values": ["a1", "shared"]},
                       {"attribute": "A2", "values": ["shared", "b2"]}]
    s["mapping"] = []
    return s
