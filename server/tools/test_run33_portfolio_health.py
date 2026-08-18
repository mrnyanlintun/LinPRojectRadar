#!/usr/bin/env python3
"""
RUN 33. PORTFOLIO HEALTH PH.1-PH.5: canonical structure, canonical method, oracles, degenerate
cases, qualification, lineage and the governance boundary.

THE ORACLE IS THE SUPPLIED CONTRACT, NOT PRODUCTION OUTPUT. Every expected value in sections 2
to 6 is computed here from the contract's own definition -- in EXACT RATIONAL ARITHMETIC where
the contract states an exact figure -- and never read back from the module. The two figures the
owner supplied and verified in exact arithmetic before this run started are asserted literally:

    PH.2  midranks on [1, 2, 3, 10] = 1/8, 3/8, 5/8, 7/8
    PH.3  OLS slope on t=[0,1,2], x=[1.0,0.9,0.8] = -1/10; with q = -1, AdverseSlope = +1/10,
          so the classification is DETERIORATING

Run (from server/):
    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_run33_portfolio_health.py
"""

import json
import os
import pathlib
import sys
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.simulation import canonical_v8 as V8                        # noqa: E402
from app.simulation import portfolio_health as PH                    # noqa: E402
from app.simulation.qualified_evidence import ELIGIBLE_STATES, UNASSESSED  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.5" / "package_D_portfolio_health"

PASS = 0
TOTAL = 0
FAILURES = []


def check(cond, name, detail=""):
    global PASS, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
        print(f"  PASS  {name}" + (f"  [{detail}]" if detail else ""))
    else:
        FAILURES.append(name)
        print(f"  FAIL  {name}  [{detail}]")
    return bool(cond)


def head(t):
    print("\n" + "=" * 94 + f"\n{t}\n" + "=" * 94)


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def run(fx, histories=None):
    return V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"],
                                       fx["feature_records"],
                                       histories if histories is not None
                                       else fx.get("histories", []))


def feat(fid, orientation, required=True, units="ratio"):
    return {"feature_id": fid, "label": fid, "units": units, "orientation": orientation,
            "scaling_rule": "NONE_RAW_UNITS", "missingness_rule": "ABSTAIN_NEVER_IMPUTE",
            "source_module": "TEST", "qualification_requirement": "CATEGORY_9_ELIGIBLE",
            "required": required}


def cohort(cid, pids, sv="sv1", period="2026-01", model="m1"):
    return {"cohort_id": cid, "portfolio_id": "PF", "project_ids": list(pids), "period": period,
            "inclusion_rule": "all", "exclusion_rule": "none", "feature_schema_version": sv,
            "qualification_policy": "CATEGORY_9", "model_version": model}


def rec(pid, cid, values, sv="sv1", period="2026-01", state="QUALIFIED", missing=()):
    return {"project_id": pid, "cohort_id": cid, "period": period, "values": dict(values),
            "qualification_state": state, "missing_fields": list(missing), "invalid_fields": [],
            "source_lineage": f"L::{pid}", "source_provenance": f"P::{pid}",
            "feature_schema_version": sv}


# =================================================================================================
head("1. THE FIXTURE PACKAGE: synthetic, and saying so on every file")
# =================================================================================================
_fx_names = sorted(p.name for p in FIXTURES.glob("*.json"))
check(_fx_names == ["ph1_isolation_forest_fixture.json", "ph1_rank_agreement_fixture.json",
                    "ph2_midrank_percentile_fixture.json", "ph3_trajectory_slope_fixture.json",
                    "ph4_nearest_neighbour_fixture.json",
                    "ph5_component_profile_fixture.json"],
      "the five canonical Portfolio Health fixtures exist, plus the reference population the "
      "dev-only scikit-learn RANK-agreement oracle needs (the compact PH.1 structural fixture "
      "cannot measure rank agreement: nine of its ten points are near-tied)",
      str(_fx_names))
for _n in _fx_names:
    _f = fixture(_n)
    check(_f.get("data_origin") == "SYNTHETIC_RESEARCH_FIXTURE"
          and _f.get("not_for_empirical_validation") is True,
          f"{_n} states data_origin SYNTHETIC_RESEARCH_FIXTURE and not_for_empirical_validation",
          str([_f.get("data_origin"), _f.get("not_for_empirical_validation")]))


# =================================================================================================
head("2. PH.1 ISOLATION FOREST: canonical construction, ONE forest per cohort, degenerate cases")
# =================================================================================================
from app.simulation import isolation_forest as IF                    # noqa: E402


def harmonic_exact(i):
    return sum(Fraction(1, j) for j in range(1, i + 1))


# -- the published normalising constant, from the DEFINITION, not from the implementation -------
check(IF.c_factor(0) == 0.0 and IF.c_factor(1) == 0.0, "c(0) = c(1) = 0, as the contract states")
check(abs(IF.c_factor(2) - 1.0) < 1e-12, "c(2) = 1 exactly, as the contract states")
_gaps = [abs(IF.c_factor(n) - float(2 * harmonic_exact(n - 1) - Fraction(2 * (n - 1), n)))
         for n in (10, 50, 256, 1000, 10000)]
check(_gaps == sorted(_gaps, reverse=True),
      "c(n) = 2H(n-1) - 2(n-1)/n converges on the exact closed form as n grows; production uses "
      "the paper's own ln + Euler estimate of H and the DECLARED deviation shrinks monotonically",
      f"{_gaps[0]:.4f} -> {_gaps[-1]:.6f}")
check(_gaps[2] < 5e-3, "and agrees to three decimals by the published subsample psi = 256")

# -- the structural fixture ----------------------------------------------------------------------
ph1 = fixture("ph1_isolation_forest_fixture.json")
r1 = run(ph1)
d1 = r1["results"]["cat8_1_isolation_forest"]
check(d1.get("abstained") is False, "PH.1 computes on the canonical fixture",
      str(d1.get("abstention_reason"))[:120])
_scores = {k: v["anomaly_score"] for k, v in d1["projects"].items()}
_top = max(_scores, key=lambda k: _scores[k])
check(_top == ph1["expected"]["highest_anomaly_score_project_id"],
      "THE DISTANT ANOMALY RECEIVES THE HIGHEST ANOMALY SCORE",
      f"{_top} at {_scores[_top]:.4f} vs next {sorted(_scores.values())[-2]:.4f}")
check(d1["higher_score_is_more_anomalous"] is True, "and higher means more anomalous")
check(all(0.0 < s <= 1.0 for s in _scores.values()),
      "every score lies in (0, 1], as s(x, psi) = 2 ** (-E(h(x)) / c(psi)) requires")

# ONE FOREST PER COHORT -- the operational rule section 6 states, and the v20 defect.
_model = d1["model"]
check(_model["one_forest_per_cohort"] is True
      and sorted(_model["fitted_project_population"]) == sorted(d1["projects"]),
      "ONE governed forest is fitted on the whole eligible cohort and every member is scored by "
      "it, so no two reported scores come from different forests",
      f"psi={_model['subsample_psi']} trees={_model['n_trees']} "
      f"pop={len(_model['fitted_project_population'])}")
for _k in ("cohort_id", "feature_schema_version", "subsample_psi", "n_trees", "height_limit",
           "seed", "preprocessing_version", "model_version", "fitted_project_population"):
    check(_model.get(_k) not in (None, ""), f"model metadata carries {_k}", str(_model.get(_k))[:60])

# DETERMINISM and ORDER INDEPENDENCE.
r1b = run(ph1)
check({k: v["anomaly_score"] for k, v in
       r1b["results"]["cat8_1_isolation_forest"]["projects"].items()} == _scores,
      "the same seed reproduces the same trees and the same scores")
_shuffled = list(reversed(ph1["feature_records"]))
_r1c = V8.compute_portfolio_health(ph1["cohort"], ph1["feature_schema"], _shuffled, [])
check({k: v["anomaly_score"] for k, v in
       _r1c["results"]["cat8_1_isolation_forest"]["projects"].items()} == _scores,
      "PROJECT-ROW ORDER DOES NOT CHANGE THE PROJECT-TO-SCORE MAPPING")

# DECLARED AFFINE UNIT RESCALING. The published construction draws its split uniformly between
# the observed min and max of the chosen attribute, so an affine rescaling of a feature maps
# every split identically under the same seed. The substantive ordering is therefore preserved.
_scaled = [dict(r, values={k: v * 1000.0 + 7.0 for k, v in r["values"].items()})
           for r in ph1["feature_records"]]
_r1d = V8.compute_portfolio_health(ph1["cohort"], ph1["feature_schema"], _scaled, [])
_sc2 = {k: v["anomaly_score"] for k, v in
        _r1d["results"]["cat8_1_isolation_forest"]["projects"].items()}
check(sorted(_scores, key=lambda k: -_scores[k]) == sorted(_sc2, key=lambda k: -_sc2[k]),
      "A DECLARED AFFINE UNIT RESCALING UNDER THE FROZEN PREPROCESSING DOES NOT CHANGE THE "
      "SUBSTANTIVE ANOMALY ORDERING")

# THE FROZEN RUN-15 THRESHOLD, VERIFIED AND LABELLED, NOT RETUNED AND NOT EXTENDED.
_r15 = (ROOT / "code_audit" / "run15_isolation_forest_validation.csv").read_text(encoding="utf-8")
check("THRESHOLD,D1.1,Isolation Forest,selected,0.576" in _r15,
      "the frozen Run-15 threshold artifact exists and says 0.576")
check(V8.RUN15_FROZEN_THRESHOLD == 0.576,
      "and Run 33 carries that exact value, unretuned", str(V8.RUN15_FROZEN_THRESHOLD))
check("FIELD_EMPIRICAL_VALIDATION,NOT_CLAIMED" in _r15.replace(",D1.1,Isolation Forest,", ","),
      "and the artifact itself records FIELD_EMPIRICAL_VALIDATION as NOT_CLAIMED")
_lbl = d1["frozen_synthetic_threshold_labels"]
check(_lbl["threshold_basis"] == "SYNTHETIC_LABORATORY" and _lbl["is_project_status_band"] is False
      and _lbl["is_sole_trigger"] is False and _lbl["field_validated"] is False,
      "it is exposed as a synthetic/laboratory exploratory artefact: not a project-status band, "
      "not a sole trigger, not field validated")
check(all(v["exploratory_flag"] is None for v in d1["projects"].values()),
      "and NO flag is derived from it on a cohort whose feature schema is not the one it was "
      "fitted on, so its claim is not extended beyond its synthetic holdout")
check(all("status_color" not in v for v in d1["projects"].values())
      and "status_color" not in d1,
      "PH.1 carries no status colour anywhere")

# DEGENERATE AND SMALL-N CASES.
_sv, _cid = "sv1", "C"
_schema2 = {"version": _sv, "features": [feat("a", V8.HIGHER_IS_MORE_ADVERSE),
                                         feat("b", V8.LOWER_IS_MORE_ADVERSE)]}


def _if(pids, values, **kw):
    c = cohort(_cid, pids, **kw)
    return V8.compute_portfolio_health(
        c, _schema2, [rec(p, _cid, values[p]) for p in pids], [])["results"]


_one = _if(["P1"], {"P1": {"a": 1, "b": 1}})
check(_one["cat8_1_isolation_forest"]["abstained"] is True
      and _one["cat8_1_isolation_forest"]["disposition"] == V8.NOT_ESTIMABLE,
      "ONE PROJECT: PH.1 is NOT_ESTIMABLE and emits no authoritative anomaly flag")
# RUN 34 MOVED THIS GATE, and the move is the finding. v21 required two eligible projects --
# the minimum an isolation TREE needs -- and computed. Two projects cannot establish what is
# normal for a portfolio: each is the other's entire reference population. Section 6B of the
# calibration contract sets the minimum for a cross-project anomaly MODEL at three.
_two = _if(["P1", "P2"], {"P1": {"a": 1, "b": 1}, "P2": {"a": 9, "b": 0.1}})
check(_two["cat8_1_isolation_forest"]["abstained"] is True
      and _two["cat8_1_isolation_forest"]["disposition"] == V8.NOT_ESTIMABLE,
      "TWO PROJECTS: NOT_ESTIMABLE, because two projects are not a portfolio to compare within",
      _two["cat8_1_isolation_forest"]["abstention_reason"][:70])
_three = _if(["P1", "P2", "P3"], {"P1": {"a": 1, "b": 1}, "P2": {"a": 9, "b": 0.1},
                                  "P3": {"a": 2, "b": 0.9}})
_t3 = _three["cat8_1_isolation_forest"]
check(_t3["abstained"] is False and _t3["cohort_size_class"] == V8.COHORT_SMALL
      and _t3["limitation"]["small_sample"] is True
      and _t3["limitation"]["predictive_validity_claimed"] is False
      and _t3["authoritative_flag_permitted"] is False,
      "THREE PROJECTS: a continuous exploratory reading, with the small-cohort limitation "
      "EXPLICIT, no predictive validity claimed and NO authoritative flag permitted",
      _t3["limitation"]["small_sample_note"][:60])
_ident = _if(["P1", "P2", "P3"], {p: {"a": 1, "b": 1} for p in ("P1", "P2", "P3")})
_is = _ident["cat8_1_isolation_forest"]
check(_is["abstained"] is False and len(set(round(v["anomaly_score"], 12)
                                            for v in _is["projects"].values())) == 1,
      "ALL FEATURE VECTORS IDENTICAL: no project is more anomalous than another",
      str(sorted(round(v["anomaly_score"], 6) for v in _is["projects"].values())))
_zv = _if(["P1", "P2", "P3"], {"P1": {"a": 1, "b": 5}, "P2": {"a": 2, "b": 5},
                               "P3": {"a": 3, "b": 5}})
check(_zv["cat8_1_isolation_forest"]["abstained"] is False,
      "ONE ZERO-VARIANCE FEATURE: the forest still isolates on the informative attribute; the "
      "published construction never selects an attribute that admits no split")
_miss = V8.compute_portfolio_health(
    cohort(_cid, ["P1", "P2", "P3"]), _schema2,
    [rec("P1", _cid, {"a": 1}, missing=("b",)), rec("P2", _cid, {"a": 2, "b": 1}),
     rec("P3", _cid, {"a": 3, "b": 1})], [])["results"]
check(_miss["cat8_1_isolation_forest"]["abstained"] is True
      and "not replaced by zero" in _miss["cat8_1_isolation_forest"]["abstention_reason"],
      "MISSING QUALIFIED FEATURE: PH.1 abstains, and the missing value is NOT read as zero")
_mixp = V8.compute_portfolio_health(
    cohort(_cid, ["P1", "P2"]), _schema2,
    [rec("P1", _cid, {"a": 1, "b": 1}), rec("P2", _cid, {"a": 2, "b": 1}, period="2026-02")],
    [])["results"]
check(all(_mixp[k]["abstained"] and "Mixed reporting periods are rejected"
          in _mixp[k]["abstention_reason"] for k in _mixp),
      "MIXED PERIODS ARE REJECTED, for all five modules alike")
_mixs = V8.compute_portfolio_health(
    cohort(_cid, ["P1", "P2"]), _schema2,
    [rec("P1", _cid, {"a": 1, "b": 1}), rec("P2", _cid, {"a": 2, "b": 1}, sv="sv2")],
    [])["results"]
check(all(_mixs[k]["abstained"] and "Mixed feature schemas are rejected"
          in _mixs[k]["abstention_reason"] for k in _mixs),
      "MIXED FEATURE SCHEMA VERSIONS ARE REJECTED, for all five modules alike")


# =================================================================================================
head("3. PH.2 PORTFOLIO OUTLIER DETECTION: the supplied midrank oracle, in exact arithmetic")
# =================================================================================================
ph2 = fixture("ph2_midrank_percentile_fixture.json")
r2 = run(ph2)
d2 = r2["results"]["cat8_2_portfolio_outlier"]
check(d2["abstained"] is False, "PH.2 computes on the canonical fixture")
# RUN 34: THE SUPPLIED ORACLE MIDRANKS LIVE IN THE FEATURE PROFILE. Section 7B withdrew the
# equal-weighted composite -- equal weighting is an owner-policy choice, not a canonical fact --
# so the composite is None absent governed weights and the per-feature percentiles are what the
# module reports. Nothing is lost: the composite was averaging exactly these numbers.
_want = {"P-A": Fraction(1, 8), "P-B": Fraction(3, 8), "P-C": Fraction(5, 8),
         "P-D": Fraction(7, 8)}
for _p, _w in sorted(_want.items()):
    _got = d2["projects"][_p]["feature_percentiles_exact"]["f_adverse"]
    check(Fraction(_got) == _w,
          f"THE SUPPLIED ORACLE: value {ph2['feature_records'][sorted(_want).index(_p)]['values']['f_adverse']} "
          f"has midrank {_w}", f"{_got} = {float(_w)}")
check(all(d2["projects"][p]["portfolio_outlier_percentile"] is None for p in d2["projects"])
      and d2["disposition"] == V8.PARAMETER_PROVENANCE_BLOCKED
      and d2["result_type"] == "FEATURE_PERCENTILE_PROFILE",
      "and the COMPOSITE IS WITHHELD absent governed weights: equal weighting is not adopted as "
      "a default", d2["composite_weighting_note"][:70])
check(max(_want, key=lambda k: _want[k]) == "P-D",
      "10 IS THE MOST EXTREME ADVERSE PROJECT, by its own feature percentile of 7/8",
      d2["projects"]["P-D"]["feature_percentiles_exact"]["f_adverse"])
check(d2["is_learned_model"] is False and d2["is_probability_of_failure"] is False,
      "PH.2 declares itself NOT a learned ML model and NOT a probability of failure")
check(d2["composite_weighting_provenance"] is None and d2["composite_weights"] is None,
      "no weighting provenance is claimed, because no composite is produced",
      str(d2["composite_weighting_provenance"]))
check("status_color" not in d2 and all("status_color" not in v for v in d2["projects"].values()),
      "and no status colour is emitted")

# ties, ordering, units
_tie = V8.compute_portfolio_health(ph2["tie_cohort"], ph2["feature_schema"],
                                   ph2["tie_feature_records"], [])["results"][
    "cat8_2_portfolio_outlier"]
check(_tie["projects"]["T-A"]["feature_percentiles_exact"]
      == _tie["projects"]["T-B"]["feature_percentiles_exact"],
      "TIES RECEIVE THE SAME MIDRANK",
      str(_tie["projects"]["T-A"]["feature_percentiles_exact"]))
_rev = V8.compute_portfolio_health(ph2["cohort"], ph2["feature_schema"],
                                   list(reversed(ph2["feature_records"])), [])["results"][
    "cat8_2_portfolio_outlier"]
check({k: v["feature_percentiles_exact"] for k, v in _rev["projects"].items()}
      == {k: v["feature_percentiles_exact"] for k, v in d2["projects"].items()},
      "PROJECT ORDERING DOES NOT CHANGE RESULTS")
_units = V8.compute_portfolio_health(
    ph2["cohort"], ph2["feature_schema"],
    [dict(r, values={"f_adverse": r["values"]["f_adverse"] * 1000.0})
     for r in ph2["feature_records"]], [])["results"]["cat8_2_portfolio_outlier"]
check({k: v["feature_percentiles_exact"] for k, v in _units["projects"].items()}
      == {k: v["feature_percentiles_exact"] for k, v in d2["projects"].items()},
      "FEATURE UNITS DO NOT AFFECT THE PERCENTILE RANK")

# orientation reversal: the SAME numbers, declared lower-is-worse, must reverse the ranking.
_low = dict(ph2["feature_schema"],
            features=[dict(ph2["feature_schema"]["features"][0],
                           orientation=V8.LOWER_IS_MORE_ADVERSE)])
_lowr = V8.compute_portfolio_health(ph2["cohort"], _low, ph2["feature_records"], [])["results"][
    "cat8_2_portfolio_outlier"]
check(Fraction(_lowr["projects"]["P-A"]["feature_percentiles_exact"]["f_adverse"])
      == Fraction(7, 8),
      "LOWER-IS-WORSE ORIENTATION REVERSES THE RANK CORRECTLY: the value 1 becomes the most "
      "adverse at 7/8",
      _lowr["projects"]["P-A"]["feature_percentiles_exact"]["f_adverse"])

# missing required feature, and the cohort-size states
_pm = V8.compute_portfolio_health(
    cohort(_cid, ["P1", "P2", "P3"]), _schema2,
    [rec("P1", _cid, {"a": 1}, missing=("b",)), rec("P2", _cid, {"a": 2, "b": 1}),
     rec("P3", _cid, {"a": 3, "b": 1})], [])["results"]["cat8_2_portfolio_outlier"]
check(_pm["abstained"] is True and "NOT renormalised" in _pm["abstention_reason"],
      "A MISSING REQUIRED FEATURE CAUSES ABSTENTION: the feature is not dropped and the rest "
      "are not renormalised")
_n2 = _if(["P1", "P2"], {"P1": {"a": 1, "b": 1}, "P2": {"a": 2, "b": 1}})[
    "cat8_2_portfolio_outlier"]
check(_n2["abstained"] is True and _n2["disposition"] == V8.NOT_ESTIMABLE,
      "COHORT n < 3 PRODUCES AN EXPLICIT NOT_ESTIMABLE STATE", _n2["disposition"])
check(d2["limitation"]["small_sample"] is True
      and "Small-sample limitation" in (d2["limitation"]["small_sample_note"] or ""),
      "COHORT n < 10 CARRIES A SMALL-SAMPLE WARNING", str(d2["limitation"]["cohort_size"]))


# =================================================================================================
head("4. PH.3 SIGNAL TRAJECTORY CLASSIFIER: the supplied OLS oracle, in exact arithmetic")
# =================================================================================================
ph3 = fixture("ph3_trajectory_slope_fixture.json")
_c3 = cohort("C3", ["P-EVEN", "P-IRREGULAR", "P-CONSTANT"])
_r3 = V8.compute_portfolio_health(
    _c3, _schema2, [rec(p, "C3", {"a": 1, "b": 1}) for p in _c3["project_ids"]],
    ph3["histories"])
d3 = _r3["results"]["cat8_3_trajectory_classifier"]
check(d3["abstained"] is False, "PH.3 computes on the canonical fixture")
_even = d3["projects"]["P-EVEN"][0]
check(Fraction(_even["ols_slope_exact"]) == Fraction(-1, 10),
      "THE SUPPLIED ORACLE: OLS slope on t=[0,1,2], x=[1.0,0.9,0.8] is exactly -1/10",
      _even["ols_slope_exact"])
check(_even["orientation_multiplier_q"] == -1,
      "q = -1 for a lower-is-more-adverse feature")
check(Fraction(_even["adverse_slope_exact"]) == Fraction(1, 10),
      "AdverseSlope a = q * b = +1/10", _even["adverse_slope_exact"])
check(_even["classification"] == V8.DETERIORATING,
      "so the classification is DETERIORATING", _even["classification"])
# THREE OBSERVATIONS CONTAIN TWO ADJACENT INTERVALS. The endpoint change is -0.2 and the wrong
# answer -- dividing it by the number of OBSERVATIONS -- is -1/15.
check(Fraction(_even["ols_slope_exact"]) != Fraction(-2, 30),
      "and the endpoint change is NOT divided by the number of observations: -1/10, not -1/15",
      f"{_even['ols_slope_exact']} vs -1/15")
check(_even["magnitude_band"] is None and _even["is_trained_classifier"] is False
      and d3["status_bands"] is None,
      "no magnitude band and no status band exists, and PH.3 declares itself untrained")

_irr = d3["projects"]["P-IRREGULAR"][0]
check(_irr["time_units"] == "days" and _irr["distinct_reporting_times"] == 3
      and Fraction(_irr["ols_slope_exact"]) != Fraction(_even["ols_slope_exact"]),
      "IRREGULAR TIME INTERVALS enter the fit as they actually are, and give a different slope "
      "from the evenly spaced series with the same values",
      f"{_irr['ols_slope_exact']} per day")
_const = d3["projects"]["P-CONSTANT"][0]
check(_const["classification"] == V8.FLAT and Fraction(_const["ols_slope_exact"]) == 0,
      "A CONSTANT SERIES is FLAT, on an exactly zero slope", _const["ols_slope_exact"])

# reversed input order
_revh = [dict(h, observations=list(reversed(h["observations"]))) for h in ph3["histories"]]
_r3b = V8.compute_portfolio_health(_c3, _schema2,
                                   [rec(p, "C3", {"a": 1, "b": 1}) for p in _c3["project_ids"]],
                                   _revh)["results"]["cat8_3_trajectory_classifier"]
check(_r3b["projects"]["P-EVEN"][0]["ols_slope_exact"] == _even["ols_slope_exact"],
      "REVERSED INPUT ORDER gives the identical slope")


def _traj_abstains(entry, needle):
    body = V8.compute_portfolio_health(
        cohort("C3", ["P-X"]), _schema2, [rec("P-X", "C3", {"a": 1, "b": 1})],
        [entry])["results"]["cat8_3_trajectory_classifier"]
    reasons = " ".join(x["reason"] for v in body.get("signal_abstentions", {}).values()
                       for x in v)
    return body["abstained"] is True and needle in reasons


def _hist(**kw):
    base = {"project_id": "P-X", "signal_id": "s1", "units": "ratio",
            "orientation": V8.LOWER_IS_MORE_ADVERSE, "source": "T", "history_version": "h1",
            "observations": [{"reporting_time": t, "value": v, "qualification_state": "QUALIFIED"}
                             for t, v in ((0, 1.0), (1, 0.9), (2, 0.8))]}
    base.update(kw)
    return base


check(_traj_abstains(_hist(observations=[{"reporting_time": 0, "value": 1.0,
                                          "qualification_state": "QUALIFIED"}]),
                     "at least 3 are required"),
      "ONE OBSERVATION: abstains, at least three are required")
check(_traj_abstains(_hist(observations=[{"reporting_time": t, "value": v,
                                          "qualification_state": "QUALIFIED"}
                                         for t, v in ((0, 1.0), (1, 0.9))]),
                     "at least 3 are required"),
      "TWO OBSERVATIONS: abstains, two points are a line through two points and not a trend")
check(_traj_abstains(_hist(observations=[{"reporting_time": 0, "value": v,
                                          "qualification_state": "QUALIFIED"}
                                         for v in (1.0, 0.9, 0.8)]),
                     "distinct reporting time"),
      "DUPLICATE TIMESTAMPS: abstains, at least three DISTINCT reporting times are required")
check(_traj_abstains(_hist(observations=[
          {"reporting_time": 0, "value": 1.0, "qualification_state": "QUALIFIED"},
          {"reporting_time": 1, "value": 0.9, "qualification_state": "QUALIFIED",
           "signal_id": "OTHER"},
          {"reporting_time": 2, "value": 0.8, "qualification_state": "QUALIFIED"}]),
                     "never fitted as one trajectory"),
      "STABLE SIGNAL IDENTITY BROKEN: two different signals are never fitted as one trajectory")
check(_traj_abstains(_hist(observations=[
          {"reporting_time": 0, "value": 1.0, "qualification_state": "QUALIFIED"},
          {"value": 0.9, "qualification_state": "QUALIFIED"},
          {"reporting_time": 2, "value": 0.8, "qualification_state": "QUALIFIED"}]),
                     "List position is never used as time"),
      "MISSING PERIOD: abstains; list position is never used as time")
check(_traj_abstains(_hist(observations=[
          {"reporting_time": 0, "value": 1.0, "qualification_state": "QUALIFIED"},
          {"reporting_time": 1, "value": 0.9, "qualification_state": UNASSESSED},
          {"reporting_time": 2, "value": 0.8, "qualification_state": "QUALIFIED"}]),
                     "does not permit analytical use"),
      "MISSING QUALIFIED OBSERVATION: abstains rather than fitting the rest as a complete series")
check(_traj_abstains(_hist(observations=[
          {"reporting_time": 0, "value": 1.0, "qualification_state": "QUALIFIED"},
          {"reporting_time": 1, "qualification_state": "QUALIFIED"},
          {"reporting_time": 2, "value": 0.8, "qualification_state": "QUALIFIED"}]),
                     "never read as zero"),
      "A MISSING VALUE IS NEVER READ AS ZERO")


# =================================================================================================
head("5. PH.4 CROSS-PROJECT PATTERN DETECTOR: continuous nearest neighbour, no radius")
# =================================================================================================
ph4 = fixture("ph4_nearest_neighbour_fixture.json")
r4 = run(ph4)
d4 = r4["results"]["cat8_4_cross_project_pattern"]
check(d4["abstained"] is False, "PH.4 computes on the canonical fixture")
check(d4["projects"]["ID-A"]["nearest_neighbour_project_ids"] == ["ID-B"]
      and d4["projects"]["ID-A"]["distance"] == 0.0
      and d4["projects"]["ID-A"]["similarity"] == 1.0,
      "IDENTICAL VECTORS: distance 0, similarity 1")
check(d4["projects"]["ID-A"]["duplicate_of"] == ["ID-B"],
      "and duplicate points are handled EXPLICITLY, named rather than silently collapsed")
check(all(p not in v["nearest_neighbour_project_ids"] and p not in v["all_distances"]
          for p, v in d4["projects"].items()),
      "SELF-MATCH IS EXCLUDED from every project's neighbour set and distance table")
check("FAR-D" not in d4["projects"]["ID-A"]["nearest_neighbour_project_ids"]
      and "FAR-D" not in d4["projects"]["ID-B"]["nearest_neighbour_project_ids"]
      and "FAR-D" not in d4["projects"]["NEAR-C"]["nearest_neighbour_project_ids"],
      "A UNIFORMLY DISTANT VECTOR IS NOT THE NEAREST MATCH TO ANY MEMBER OF THE COMPACT CLUSTER")
check([e["feature_id"] for e in d4["excluded_features"]] == ["f_flat"]
      and d4["excluded_features"][0]["reason"] == "ZERO_VARIANCE_NON_INFORMATIVE",
      "THE ZERO-VARIANCE FEATURE IS RECORDED AND EXCLUDED as non-informative",
      str(d4["excluded_features"]))
# The v20 radius was a NUMBER a comparison was made against, and its output was a
# `similar_project_count` and a status ladder. Both are asserted gone STRUCTURALLY rather than by
# searching for the digits "0.15", which appear in the retirement note itself.
_d4_numbers = [v for v in d4.values() if isinstance(v, (int, float))
               and not isinstance(v, bool)]
check(d4["match_threshold"] is None and 0.15 not in _d4_numbers
      and "similar_project_count" not in d4
      and not any("radius" in k or "threshold" in k for k in d4["projects"]["ID-A"]),
      "THE UNVALIDATED 0.15 MATCH RADIUS IS GONE AND NOTHING REPLACES IT: no threshold value, "
      "no matched-count, no per-project radius field",
      str([d4["match_threshold"], _d4_numbers]))
check(d4["similarity_is_not_failure"] is True and "status_color" not in json.dumps(d4)
      and d4["peer_condition_reported_separately"] is True,
      "matching a peer implies no adverse status; peer condition is reported separately and no "
      "status colour exists")
_r4b = V8.compute_portfolio_health(ph4["cohort"], ph4["feature_schema"],
                                   list(reversed(ph4["feature_records"])), [])["results"][
    "cat8_4_cross_project_pattern"]
check({k: (v["nearest_neighbour_project_ids"], round(v["distance"], 12))
       for k, v in _r4b["projects"].items()}
      == {k: (v["nearest_neighbour_project_ids"], round(v["distance"], 12))
          for k, v in d4["projects"].items()},
      "PROJECT ORDERING DOES NOT CHANGE PAIRWISE DISTANCES OR THE NEIGHBOUR SET")
check(d4["tie_rule"] == V8.TIE_RULE and d4["projects"]["NEAR-C"]["nearest_neighbour_project_ids"]
      == sorted(d4["projects"]["NEAR-C"]["nearest_neighbour_project_ids"]),
      "the tie rule is DECLARED and applied: all tied neighbours, in ascending project-id order",
      d4["tie_rule"])
_flat = V8.compute_portfolio_health(
    cohort(_cid, ["P1", "P2", "P3"]), _schema2,
    [rec(p, _cid, {"a": 1, "b": 1}) for p in ("P1", "P2", "P3")], [])["results"][
    "cat8_4_cross_project_pattern"]
check(_flat["abstained"] is True and "non-informative" in _flat["abstention_reason"],
      "IF ALL FEATURES ARE NON-INFORMATIVE, PH.4 ABSTAINS")
check(_pm is not None and V8.compute_portfolio_health(
          cohort(_cid, ["P1", "P2", "P3"]), _schema2,
          [rec("P1", _cid, {"a": 1}, missing=("b",)), rec("P2", _cid, {"a": 2, "b": 1}),
           rec("P3", _cid, {"a": 3, "b": 1})], [])["results"][
          "cat8_4_cross_project_pattern"]["abstained"] is True,
      "A MISSING REQUIRED FEATURE CAUSES ABSTENTION in PH.4 too")


# =================================================================================================
head("6. PH.5 ANOMALY SCORE: a truthful profile, and NO SCALAR")
# =================================================================================================
ph5 = fixture("ph5_component_profile_fixture.json")
r5 = run(ph5)
d5 = r5["results"]["cat8_5_anomaly_score"]
check(d5["result_type"] == "PortfolioAnomalyProfile", "PH.5 emits a PortfolioAnomalyProfile")
check(d5["score"] is None and d5["disposition"] == V8.PARAMETER_PROVENANCE_BLOCKED,
      "THE SCALAR REMAINS NULL, under PARAMETER_PROVENANCE_BLOCKED", d5["disposition"])
check(all(v["score"] is None and v["disposition"] == V8.PARAMETER_PROVENANCE_BLOCKED
          and v["weights"] is None and v["effective_weights"] is None and v["confidence"] is None
          for v in d5["projects"].values()),
      "for every project, with no weights, no effective weights and no confidence")
check(list(d5["constituent_modules"]) == ["D1.1", "D1.2", "D1.3", "D1.4"]
      and d5["constituent_roles"]["D1.1"] == "isolation_forest_anomaly_score"
      and d5["constituent_roles"]["D1.2"] == "descriptive_outlier_percentile"
      and d5["constituent_roles"]["D1.3"] == "trajectory_slope_and_classification"
      and d5["constituent_roles"]["D1.4"] == "nearest_neighbour_pattern_result",
      "THE EXACT CONSTITUENT IDENTITIES ARE EXPOSED, by module id and by role")
_c1 = d5["projects"]["C-1"]
check(sorted(_c1["constituents"]) == ["D1.1", "D1.2", "D1.3", "D1.4"]
      and all(_c1["constituents"][m]["cohort_id"] == ph5["cohort"]["cohort_id"]
              and _c1["constituents"][m]["feature_schema_version"]
              == ph5["cohort"]["feature_schema_version"]
              and _c1["constituents"][m]["period"] == ph5["cohort"]["period"]
              for m in _c1["constituents"]),
      "COMPONENT LINEAGE IS PRESERVED: every constituent carries its cohort, period, schema and "
      "model version")
check(_c1["constituents"]["D1.1"]["value"].get("source_lineage") == "SYNTHETIC_LINEAGE::C-1",
      "and the project's own source lineage travels with the constituent",
      str(_c1["constituents"]["D1.1"]["value"].get("source_lineage")))

# MISSING PH.3 HISTORY DOES NOT CHANGE PH.1 / PH.2 / PH.4.
_no_hist = V8.compute_portfolio_health(ph5["cohort"], ph5["feature_schema"],
                                       ph5["feature_records"], [])["results"]
for _k in ("cat8_1_isolation_forest", "cat8_2_portfolio_outlier",
           "cat8_4_cross_project_pattern"):
    check(json.dumps(_no_hist[_k], sort_keys=True, default=str)
          == json.dumps(r5["results"][_k], sort_keys=True, default=str),
          f"MISSING PH.3 HISTORY DOES NOT CHANGE {_k}: byte-identical with and without it")
_c2 = d5["projects"]["C-2"]
check(_c2["missing_constituents"] == ["D1.3"] and "D1.3" not in _c2["constituents"]
      and _c2["missing_constituents_are_not_neutral"] is True,
      "a project with no history reports D1.3 as a MISSING CONSTITUENT and never as a neutral "
      "or favourable value")
check(_c1["constituents"]["D1.1"]["value"] == r5["results"]["cat8_1_isolation_forest"][
          "projects"]["C-1"],
      "and the constituents that ARE present carry the values their own modules produced, "
      "unweighted and untransformed")

# DUPLICATE LINEAGE CANNOT REINFORCE.
_dup = V8.anomaly_profile(
    V8.PortfolioCohort(ph5["cohort"], ph5["feature_schema"], ph5["feature_records"]),
    {"D1.1": r5["results"]["cat8_1_isolation_forest"],
     "D1.2": r5["results"]["cat8_1_isolation_forest"],   # the SAME result offered twice
     "D1.3": r5["results"]["cat8_3_trajectory_classifier"],
     "D1.4": r5["results"]["cat8_4_cross_project_pattern"]})
check(_dup["projects"]["C-1"]["distinct_evidence_bodies"]
      == _c1["distinct_evidence_bodies"]
      and _dup["projects"]["C-1"]["corroboration_established"] is False
      and _dup["projects"]["C-1"]["confidence"] is None,
      "DUPLICATE PH.1/PH.2 LINEAGE DOES NOT INCREASE CONFIDENCE: the evidence-body count is "
      "unchanged, corroboration stays false and confidence stays null",
      f"{_dup['projects']['C-1']['distinct_evidence_bodies']} evidence bodies")
check(all(v["independent"] is False for v in V8.PH5_INDEPENDENCE.values()),
      "PH.1 AND PH.2 ARE NOT COUNTED AS INDEPENDENT CORROBORATION: every constituent declares "
      "itself non-independent of the others")
# The v20 placeholder was a literal 0.5 pushed into the `scores` list that the composite mean
# was taken over. It is asserted gone STRUCTURALLY: there is no scores list, no composite mean,
# and no numeric field on the profile body at all except the evidence-body count.
_p_numeric = {k: v for k, v in _c1.items()
              if isinstance(v, (int, float)) and not isinstance(v, bool)}
check("scores" not in d5 and "composite_anomaly" not in d5
      and list(_p_numeric) == ["distinct_evidence_bodies"],
      "NO CONSTANT PLACEHOLDER of any kind survives in the profile: there is no score list, no "
      "composite mean, and the only number on a project profile is its evidence-body count",
      str(_p_numeric))
check("composite_score" not in json.dumps(d5) and "relative_distance" not in json.dumps(d5)
      and "1 - composite_rank" not in json.dumps(d5),
      "and neither the v20 composite_score, the retired Mahalanobis proxy, nor `1 - "
      "composite_rank` appears anywhere in it")


# =================================================================================================
head("7. THE GOVERNANCE BOUNDARY: non-voting, no project evidence, no authority")
# =================================================================================================
_all = dict(r5["results"])
_all.update(r1["results"])
check(V8.NON_VOTING is True and V8.CREATES_PROJECT_EVIDENCE is False,
      "the layer declares NON_VOTING and CREATES_PROJECT_EVIDENCE as named constants")
for _k, _v in sorted(_all.items()):
    check(_v["voting"] is False and _v["creates_project_evidence"] is False
          and _v["evidence_class"] == V8.PROGRAMME_CONTEXT_EVIDENCE
          and _v["use"] == V8.INFORM_ONLY and "status_color" not in _v,
          f"{_k}: non-voting, creates no project evidence, programme-context, inform-only, "
          f"no status colour")
    check(_v["calibration_pending"] is True and _v["empirical_validation_pending"] is True,
          f"{_k}: carries calibration_pending and empirical_validation_pending")
    check("never a sole" in _v["authority_note"],
          f"{_k}: states that it is never a sole contractual or escalation trigger")

# Portfolio Health must not appear in the vote, in fusion or in project status.
from app.simulation.registry import CORE_VOTING_MODULES                # noqa: E402

_ph_ids = set(V8.RESULT_KEYS)
check(len(CORE_VOTING_MODULES) == 2,
      "VOTING REMAINS EXACTLY 2 across the whole instrument", str(sorted(CORE_VOTING_MODULES)))
check(not (_ph_ids & set(CORE_VOTING_MODULES)),
      "PORTFOLIO HEALTH VOTING MODULES = 0: no D1 identity is in the voting set",
      str(sorted(_ph_ids & set(CORE_VOTING_MODULES))))

# THE STRUCTURAL PROOF, not a re-statement: the portfolio snapshot is stored on its OWN column
# and is never merged into module_results, category_statuses or project_status. Read from the
# live source of the one production call site.
import inspect                                                         # noqa: E402
from app import documents as DOCS                                      # noqa: E402

_src = inspect.getsource(DOCS.run_and_store)
check("portfolio_snapshot=snapshot" in _src,
      "the portfolio result is stored ONLY on its own portfolio_snapshot column")
check("module_results=run.get(\"modules\")" in _src
      and "snapshot" not in _src.split("module_results=")[1].split(",")[0],
      "and never into module_results, so it cannot reach fusion, the vote or Project Status")
check(_src.index("snapshot = compute_portfolio_health_snapshot(")
      > _src.index("run = compute_project("),
      "and the portfolio computation happens AFTER compute_project, so no portfolio output can "
      "become an input to the project computation that produced its own features -- there is no "
      "PH output -> portfolio feature -> same PH model cycle")
check("portfolio_snapshot" not in _src.split("run = compute_project(")[0],
      "and nothing reads a stored portfolio snapshot before the project computation runs")


# =================================================================================================
head("8. CATEGORY-9 QUALIFICATION: the current boundary, not a second framework")
# =================================================================================================
check(V8.ELIGIBLE_STATES is ELIGIBLE_STATES,
      "PH reads the CURRENT Category-9 ELIGIBLE_STATES object itself, so there is no separate "
      "Portfolio Health qualification framework to drift",
      str(ELIGIBLE_STATES))
check(UNASSESSED not in ELIGIBLE_STATES, "UNASSESSED evidence is ineligible")
_unq = V8.PortfolioCohort(
    cohort(_cid, ["P1", "P2", "P3"]), _schema2,
    [rec("P1", _cid, {"a": 1, "b": 1}, state=UNASSESSED),
     rec("P2", _cid, {"a": 2, "b": 1}), rec("P3", _cid, {"a": 3, "b": 1})])
check(_unq.project_ids == ("P2", "P3") and "P1" in [m["project_id"] for m in _unq.excluded],
      "RAW BYPASS = 0: an UNASSESSED record is excluded from the cohort entirely, never "
      "converted to QUALIFIED and never carried at reliability 1",
      str(_unq.identity()["excluded_reasons"]))
check("never converted to" in _unq.identity()["excluded_reasons"]["P1"],
      "and the exclusion states why, in the record itself")
for _bad in ("REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE"):
    _c = V8.PortfolioCohort(cohort(_cid, ["P1", "P2"]), _schema2,
                            [rec("P1", _cid, {"a": 1, "b": 1}, state=_bad),
                             rec("P2", _cid, {"a": 2, "b": 1})])
    check(_c.project_ids == ("P2",),
          f"MISSING-ASSESSMENT BYPASS = 0: a {_bad} record cannot be read analytically")
check(all(V8.PortfolioCohort(cohort(_cid, ["P1", "P2"]), _schema2,
                             [rec("P1", _cid, {"a": 1, "b": 1}, state=_ok),
                              rec("P2", _cid, {"a": 2, "b": 1})]).project_ids == ("P1", "P2")
          for _ok in ELIGIBLE_STATES),
      "and both eligible states ARE readable, so the gate is not simply refusing everything",
      str(ELIGIBLE_STATES))
check(all(V8.PH5_INDEPENDENCE[m]["independent"] is False for m in V8.PH5_CONSTITUENTS),
      "QUALIFICATION DOES NOT IMPLY INDEPENDENCE: every qualified constituent still declares "
      "itself non-independent of the others")


# =================================================================================================
head("9. THE REAL PRODUCTION ROUTE, and the superseded one it cannot reach")
# =================================================================================================
import run33_historical_portfolio as R33H                              # noqa: E402

R33H.assert_not_reachable(lambda cond, name, detail="": check(cond, name, detail))

# THE INTAKE IS THE REAL ONE. The four governed portfolio structures are in the vocabulary the
# governed project-data store reads from the analytical layer, so `saveprojectdata` can carry
# them and `apply_to_signal_inputs` merges them onto the signal inputs the modules are given.
from app.project_data import add_revision, apply_to_signal_inputs, governed_structure_keys  # noqa: E402

_vocab = governed_structure_keys()
for _k in PH.PORTFOLIO_STRUCTURE_KEYS:
    check(_k in _vocab, f"{_k} is in the governed intake vocabulary")

_doc = {}
_ph2 = fixture("ph2_midrank_percentile_fixture.json")
for _p, _r in zip(_ph2["cohort"]["project_ids"], _ph2["feature_records"]):
    pass
_doc = add_revision({}, "portfolioCohort", _ph2["cohort"], effective_period=1,
                    supplied_by="run33-test", source="synthetic fixture", at="2026-08-18")
_doc = add_revision(_doc, "portfolioFeatureSchema", _ph2["feature_schema"], effective_period=1,
                    supplied_by="run33-test", source="synthetic fixture", at="2026-08-18")
_doc = add_revision(_doc, "portfolioFeatureRecord", _ph2["feature_records"][0],
                    effective_period=1, supplied_by="run33-test", source="synthetic fixture",
                    at="2026-08-18")
_si = {}
_added = apply_to_signal_inputs(_si, _doc, 1)
check(sorted(_added) == ["portfolioCohort", "portfolioFeatureRecord", "portfolioFeatureSchema"],
      "THROUGH THE REAL INTAKE: the three structures arrive on the signal inputs the modules are "
      "given, by the same governed, period-effective, append-only route every canonical "
      "structure uses", str(sorted(_added)))

# THE REAL DISPATCHER, over the whole cohort assembled from per-project signal inputs.
_sis = {}
for _r in _ph2["feature_records"]:
    _d = add_revision({}, "portfolioCohort", _ph2["cohort"], effective_period=1,
                      supplied_by="t", source="s", at="2026-08-18")
    _d = add_revision(_d, "portfolioFeatureSchema", _ph2["feature_schema"], effective_period=1,
                      supplied_by="t", source="s", at="2026-08-18")
    _d = add_revision(_d, "portfolioFeatureRecord", _r, effective_period=1,
                      supplied_by="t", source="s", at="2026-08-18")
    _s = {}
    apply_to_signal_inputs(_s, _d, 1)
    _sis[_r["project_id"]] = _s

_cur = "P-D"
_snap = PH.compute_portfolio_health_snapshot(
    _cur, _sis[_cur], [(p, s) for p, s in sorted(_sis.items()) if p != _cur], "2026-01-31")
check(_snap["structure_absent"] is False and _snap["portfolio_size"] == 4,
      "THE REAL DISPATCHER assembles the four-project cohort from the projects' own stored "
      "signal inputs and computes", str(_snap["portfolio_size"]))
check(_snap["results"]["cat8_2_portfolio_outlier"]["projects"][_cur][
          "feature_percentiles_exact"]["f_adverse"] == "7/8",
      "and the supplied PH.2 oracle holds THROUGH THE PRODUCTION ROUTE, not only in the library",
      _snap["results"]["cat8_2_portfolio_outlier"]["projects"][_cur][
          "feature_percentiles_exact"]["f_adverse"])
check(_snap["voting"] is False and _snap["creates_project_evidence"] is False
      and _snap["route"] == "canonical_v8",
      "and the snapshot itself is stamped non-voting, creating no project evidence, on the "
      "canonical route")

# A PROJECT THAT IS NOT A DECLARED MEMBER CONTRIBUTES NOTHING, so the cohort is the governed
# population and not "the rows the query returned".
_intruder = dict(_sis["P-A"])
_intruder["portfolioFeatureRecord"] = dict(_ph2["feature_records"][0], project_id="INTRUDER")
_snap2 = PH.compute_portfolio_health_snapshot(
    _cur, _sis[_cur],
    [(p, s) for p, s in sorted(_sis.items()) if p != _cur] + [("INTRUDER", _intruder)],
    "2026-01-31")
check(_snap2["portfolio_size"] == 4
      and "INTRUDER" not in _snap2["cohort"]["eligible_project_ids"],
      "A PROJECT OUTSIDE THE DECLARED COHORT CONTRIBUTES NOTHING, even when it carries a "
      "feature record", str(_snap2["cohort"]["eligible_project_ids"]))

# NO GOVERNED COHORT -> a reported abstention, never an invented comparison.
_none = PH.compute_portfolio_health_snapshot("X", {}, [], "2026-01-31")
check(_none["structure_absent"] is True and len(_none["results"]) == 5
      and all(v["abstained"] and v["abstention_reason"] for v in _none["results"].values()),
      "WITH NO GOVERNED COHORT all five abstain, addressably, each carrying its reason")


print()
print("=" * 94)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  -", f)
sys.exit(1 if FAILURES else 0)
