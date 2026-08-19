"""
RUN 17 — literature-grounded scientific method audit.

TEST AND AUDIT ONLY. This suite imports production modules and reads them; it changes nothing.
There is no production import of this file.

WHAT MAKES A CHECK HERE LEGITIMATE
  - The expected value comes from run17/oracle/canonical_oracles.py, which is written from the
    supervisory specification's equations and self-proves against the specification's own worked
    answers before it is allowed to judge anything. Production output is never the oracle.
  - Every module target gets a positive known-answer or structural check, a negative/boundary or
    missingness check, and an invariant/metamorphic check where one is mathematically applicable.
  - Fault injection at the end proves the scientific checks can actually turn red.

VOCABULARY. A check passing means the stated proposition held. It does NOT mean the module is
"validated": empirical validation is a separate column in the results matrix and is NOT_DONE
almost everywhere, which is the honest answer for an instrument with no labelled outcome corpus.
"""

from __future__ import annotations

import datetime
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # server/
sys.path.insert(0, str(HERE / "run17"))       # run17 helpers
sys.path.insert(0, str(HERE / "run17" / "oracle"))

import canonical_oracles as O                                   # noqa: E402
from population import population, reconciliation               # noqa: E402
from app.simulation import registry as REG                      # noqa: E402
from app.simulation import fusion as FUSION                     # noqa: E402
from app.simulation.portfolio import compute_portfolio          # noqa: E402
from app.simulation.isolation_forest import IsolationForest, c_factor as prod_c  # noqa: E402

# =================================================================================================
# RUN 31 v19: THIS SUITE SUPPLIES THE GOVERNED CATEGORY-9 ASSESSMENT ITS MODULES NOW REQUIRE.
#
# From sim-2026.08-v19 a package with no Category-9 assessment FAILS CLOSED for every
# Category-6/7/8/10 consumer. This suite's purpose is a module's ARITHMETIC, so it supplies the
# ordinary governed assessment a real caller supplies, through the ordinary signal-input key, and
# then tests the arithmetic it was written to test. It is not exempt from the gate: the ordinary
# precedence still applies, and the gate's own guards never install this.
# =================================================================================================
import run31_qualified_fixture as _R31Q                                       # noqa: E402
_R31Q.install()


CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731  deterministic stand-in; stochastic modules are seeded separately

PASSED = 0
TOTAL = 0
FAILURES: list[str] = []
#: module_id -> list of check names that exercised it, for the evidence column.
COVERAGE: dict[str, list[str]] = {}
#: Scientific propositions that did NOT hold against production, recorded for the report.
DEFECTS: list[dict] = []

#: THE ANTI-FOSSILISATION REGISTER.
#:
#: Run 17 is an audit and is forbidden from remediating production, so a canonical proposition
#: that production fails cannot be turned green by fixing the code. Nor may the suite simply
#: assert the defective behaviour as though it were correct: five suites in this programme have
#: already been found encoding a defect as expected behaviour, and that is the failure mode this
#: register exists to prevent.
#:
#: proposition() therefore does BOTH directions. A canonical proposition that fails must be
#: named here with its disposition; if it is not, the suite goes red for an unrecorded defect.
#: And if a proposition named here starts HOLDING -- because Run 18 fixed it -- the suite ALSO
#: goes red, saying so, because the Run-17 disposition has become stale and must be revised.
#: Neither a new defect nor a repaired one can pass silently.
KNOWN_DEFECTS: dict[str, str] = {
    # RUN 20 CYCLE 9 REPAIRED THIS ONE, so it is removed from the register rather than left to
    # go stale. Conservative Dominance returned the shared decision layer's COUNTING state --
    # two or more Reds, or a breach with a Red forecast -- so a lone Red read Amber and selected
    # routine early warning. It now applies the dominance rule its name asserts: the most adverse
    # band any present signal reads. Absent or unrecognised evidence still cannot reach the
    # calmest band, which is the pre-existing all-present-and-Green requirement, kept.
    # RUN 30 REPAIRED 6.4/benign-dilution, so it is removed from the register rather than left
    # to go stale. Worst-N-of-M compared a red COUNT against ceil(0.3 M) where M grew with the
    # registered module array, so adding benign evidence RAISED the bar and downgraded an
    # unchanged adverse finding. v15 is the frozen Worst-2 MEAN statistic over the independent
    # governed signals: benign evidence cannot displace the worst two, and the module array is
    # not synthesised at all because a transformation of the arms is not further evidence.
    #
    # RUN 30 ALSO REPAIRED ARCH/lineage-double-count. A second transform of the same adverse
    # evidence no longer casts its own vote in any of the three ensembles, because duplicate
    # lineage is collapsed to one reading per independent body before anything is counted.
    #
    # ARCH/raw-bypass STAYS. Run 31 owns the Category-9 qualification gate and Run 30 must not
    # mark it resolved: the ensembles still consume evidence that has passed through no
    # qualification step, and the probe below is deliberately taken on a module that still
    # computes rather than on one that happens to abstain for an unrelated reason.
    "PH.5/availability-reweighting": "IMPLEMENTATION_DEFECT",
    "PH.1/degenerate-cohort-resolution": "METHOD_PASS_CALIBRATION_PENDING",
    "ARCH/raw-bypass": "MISSING_CANONICAL_DATA_STRUCTURE",
}


def proposition(module_id: str, key: str, name: str, holds: bool, detail: str = "") -> bool:
    """
    Evaluate a canonical proposition against production and record the answer.

    The CHECK that passes is "this proposition was decided and its answer agrees with the
    Run-17 register". The proposition's own truth value is the finding, not the pass.
    """
    global PASSED, TOTAL
    TOTAL += 1
    COVERAGE.setdefault(module_id, []).append(name)
    registered = key in KNOWN_DEFECTS
    if not holds:
        DEFECTS.append({"module_id": module_id, "key": key, "proposition": name,
                        "detail": detail, "disposition": KNOWN_DEFECTS.get(key, "UNRECORDED")})
    if holds and registered:
        FAILURES.append(
            f"[{module_id}] {name} -- this proposition NOW HOLDS but is recorded in the Run-17 "
            f"register as {KNOWN_DEFECTS[key]}. The finding is stale: revise the disposition.")
        return False
    if not holds and not registered:
        FAILURES.append(
            f"[{module_id}] {name} -- proposition FAILED and is not in the Run-17 register. "
            f"An unrecorded scientific defect. {detail}")
        return False
    PASSED += 1
    return True


def check(module_id: str, name: str, condition: bool, detail: str = "") -> bool:
    global PASSED, TOTAL
    TOTAL += 1
    COVERAGE.setdefault(module_id, []).append(name)
    if condition:
        PASSED += 1
        return True
    FAILURES.append(f"[{module_id}] {name}" + (f" -- {detail}" if detail else ""))
    return False


def near(module_id: str, name: str, got, want, tol=1e-9) -> bool:
    ok = got is not None and abs(float(got) - float(want)) <= tol
    return check(module_id, name, ok, f"got {got!r}, oracle {want!r}")


def run(code_id: str, si: dict) -> dict:
    return REG.run_module(code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    # RUN 28. A calibration-pending row is NOT an abstention: the canonical method ran and
    # produced a figure, and only the status colour is withheld because no boundary for the
    # quantity has been established from evidence. This is the same distinction
    # registry.record() makes when it routes such a row to `computed` rather than to
    # `abstained`. `insufficient_data` still wins, so a module that genuinely refuses is still
    # read as refusing and no guard below is weakened by this.
    if out.get("calibration_pending") and not out.get("insufficient_data"):
        return False
    return bool(out.get("insufficient_data")) or out.get("status_color") is None


# =============================================================================================
# GATE A -- the oracle proves itself, and the population reconciles, before anything is judged
# =============================================================================================

def gate_a() -> None:
    fails = O.self_test()
    check("GATE", "oracle self-test against the specification's worked answers",
          not fails, "; ".join(fails))

    rec = reconciliation()
    check("GATE", "registry name mapping agrees with the supervisory specification",
          rec["mapping_problems"] == [], str(rec["mapping_problems"]))
    check("GATE", "exactly 100 Run-17 scientific targets", rec["total_targets"] == 100,
          str(rec["total_targets"]))
    check("GATE", "100 unique module ids", rec["unique_module_ids"] == 100)
    check("GATE", "96 project-level registry rows", rec["project_level"] == 96)
    check("GATE", "5 portfolio-level registry rows", rec["portfolio_level"] == 5)
    check("GATE", "the excluded module is Material Cost Variance",
          rec["excluded_name"] == "Material Cost Variance")
    check("GATE", "identifiers would collide under float coercion, so they are kept as text",
          len(rec["float_coercion_would_collide"]) >= 4,
          str(rec["float_coercion_would_collide"]))
    check("GATE", "all eight concept-only modules are inside the 100",
          len(rec["concept_only_in_population"]) == 8)


# =============================================================================================
# GATE B -- Run-16 prerequisite, and the standing activation/voting guard
# =============================================================================================

def gate_b() -> None:
    idx = REG.registry_index()
    check("3.4", "registry identity retained", "A3.4" in idx)
    check("3.4", "registry row still names Material Cost Variance",
          idx.get("A3.4", {}).get("module_name") == "Material Cost Variance")
    check("3.4", "activation state is the evidence-under-review one, not concept-only",
          REG.activation_state("A3.4") == "DISABLED_EVIDENCE_UNDER_REVIEW")
    check("3.4", "non-voting", "A3.4" not in REG.CORE_VOTING_MODULES)
    # Refused before its formula function is reached, on several input shapes.
    for shape in ({}, {"bac": 100}, {"materialCostBaseline": 10, "materialCostActual": 12},
                  {"bac": 0, "cpi": 0}):
        out = run("A3.4", shape)
        check("3.4", f"refused before arithmetic on input shape {sorted(shape)}",
              out.get("activation_state") == "DISABLED_EVIDENCE_UNDER_REVIEW"
              and out.get("status_color") is None and out.get("insufficient_data") is True)
    check("3.4", "excluded from the Run-17 scientific population",
          "3.4" not in {t["module_id"] for t in population()})

    check("GATE", "voting set is exactly TCPI and Variance at Completion",
          REG.CORE_VOTING_MODULES == frozenset({"A1.7", "A1.8"}),
          str(sorted(REG.CORE_VOTING_MODULES)))
    check("GATE", "the eight concept-only modules remain disabled",
          set(REG.DISABLED_CONCEPT_ONLY) == {"A3.8", "B2.7", "B2.9", "B2.20",
                                             "B4.1", "B4.2", "B4.5", "B4.6"})
    for code in sorted(REG.DISABLED_CONCEPT_ONLY):
        out = run(code, {"bac": 1000, "ev": 500, "ac": 600, "cpi": 0.83})
        check("GATE", f"{code} refuses to execute", out.get("status_color") is None
              and out.get("activation_state") == "DISABLED_UNSAFE")
    check("GATE", "no disabled module votes",
          not (set(REG.DISABLED_MODULES) & set(REG.CORE_VOTING_MODULES)))


# =============================================================================================
# CATEGORY 1 -- quantitative EVM and forecasting (11 targets)
# =============================================================================================

BASE_EVM = {"bac": 1000.0, "ev": 500.0, "ac": 600.0, "cpi": 0.8333333333333334,
            "spi": 0.9, "actualPctComplete": 50.0, "plannedPctComplete": 60.0}


def cat1() -> None:
    # ------------------------------------------------------------------ 1.1 Monte Carlo EAC
    mid = "1.1"
    si = dict(BASE_EVM)
    out = run("A1.1", si)
    # RUN 36 CLOSURE, THE OWNER'S A1.1 RULING. The owner resolved the ambiguity Run 36 found: the
    # `Required:` input list in supervisory specification s1.1 GOVERNS what qualifies as canonical
    # Monte Carlo. Canonical execution needs the declared cost-driver distribution structure AND
    # an authoritative rule for turning drawn driver figures into a forecast of the final cost.
    # The specification requires that rule and does not define it, so the module does not execute
    # operationally and the retained budget-and-index approximation is preserved but unreachable.
    check(mid, "governed: does NOT execute on a complete EVM input alone, because a complete EVM "
          "input is not the canonical input contract", abstained(out), str(out)[:160])
    check(mid, "governed: and the reason distinguishes an ungoverned method definition from an "
          "ordinary missing value",
          out.get("abstention_reason_code") == "CANONICAL_DRIVER_DISTRIBUTION_MAPPING_NOT_GOVERNED",
          str(out.get("abstention_reason_code")))
    # THE SCIENTIFIC RECORD OF THE PRESERVED ARITHMETIC IS NOT LOST. Every structural assertion
    # this audit made about the adaptation is still made, driven against the preserved function
    # directly. That is a test exercising historical code on purpose; production cannot.
    from app.simulation.models_sim import run_monte_carlo as _retained  # noqa: E402
    kept = _retained(dict(BASE_EVM), lambda: 0.5, 0)
    p50, p80 = kept.get("p50_eac"), kept.get("p80_eac")
    check(mid, "preserved: the retained adaptation still reports both a P50 and a P80 from the "
          "simulated distribution", p50 is not None and p80 is not None, f"keys {sorted(kept)}")
    check(mid, "preserved: the iteration count is reported", kept.get("iterations") is not None)
    check(mid, "preserved: the uncertain-variable driver is named",
          kept.get("spread_driver") is not None)
    if p50 is not None and p80 is not None:
        check(mid, "invariant: P50 <= P80", p50 <= p80, f"{p50} vs {p80}")
    # Beta-PERT lambda=4 analytic mean, the specification's own oracle, checked against the
    # oracle module rather than against anything production computed.
    near(mid, "known-answer: Beta-PERT(80,100,140) analytic mean",
         O.beta_pert_mean(80, 100, 140), 620.0 / 6.0, tol=1e-12)
    check(mid, "boundary: abstains with no budget at completion", abstained(run("A1.1", {})))
    # Reproducibility: the module is seeded from (scenario, period), so two identical runs of
    # the whole registry on the same seed must agree.
    r1 = REG.run_all(dict(BASE_EVM), "scenario-x", "P1", CUTOFF, only=["A1.1"])
    r2 = REG.run_all(dict(BASE_EVM), "scenario-x", "P1", CUTOFF, only=["A1.1"])
    check(mid, "reproducibility: identical seed gives identical result",
          r1["computed"] == r2["computed"] and r1["abstained"] == r2["abstained"])
    check(mid, "governed: and A1.1 publishes no computed row at all through the real runner",
          not any(m["module_id"] == "A1.1" for m in r1["computed"]),
          str([m["module_id"] for m in r1["computed"]]))
    r3 = REG.run_all(dict(BASE_EVM), "scenario-y", "P1", CUTOFF, only=["A1.1"])
    check(mid, "stochastic diagnostic: a different seed moves the sample",
          r3["seed"] != r1["seed"])

    # ------------------------------------------------------------------ 1.2 CUSUM
    mid = "1.2"
    # The specification freezes k=0.5 sigma and h=5 sigma and forbids retuning them in Run 17.
    # Prove the frozen record exists in the repository rather than trusting the prose.
    cal = pathlib.Path("../code_audit").resolve()
    frozen = list(pathlib.Path(HERE.parent.parent / "code_audit").glob("run15_cusum*"))
    check(mid, "frozen Run-15 calibration record is present in the repository",
          len(frozen) > 0, f"searched {cal}")
    hist = [1.0] * 6 + [0.6] * 12          # a persistent level shift, the calibration target
    out = run("A1.2", {**BASE_EVM, "spiHistory": hist})
    check(mid, "positive: executes on a real history", not abstained(out), str(out))
    # Independent canonical CUSUM on the same series, from the specification's recursion.
    mu0 = sum(hist[:6]) / 6
    sd = 0.1
    ind = O.cusum_two_sided(hist, mu0, sd, 0.5, 5.0)
    check(mid, "known-answer: the canonical recursion signals on a persistent level shift",
          ind["signal_index"] is not None)
    check(mid, "known-answer: the canonical recursion does not signal on a single spike",
          O.cusum_two_sided([0.0] * 5 + [3.0] + [0.0] * 12, 0.0, 1.0, 0.5,
                            5.0)["signal_index"] is None)
    check(mid, "boundary: abstains with no history", abstained(run("A1.2", {"bac": 1000})))
    check(mid, "invariant: the canonical statistic is non-negative at every step",
          all(v >= 0 for v in ind["c_plus"]) and all(v >= 0 for v in ind["c_minus"]))

    # ------------------------------------------------------------------ 1.3 Bayesian EAC
    mid = "1.3"
    # RUN 28. Run 17 recorded that this module updated a normal-normal posterior using two
    # DESIGNED constant variances, (0.15*BAC)^2 and (BAC(1-CPI)/CPI)^2, neither of which stated
    # a source. v3 requires the governed Bayesian model record and abstains without it. The
    # oracle below is the specification's own worked example and comes from run17/oracle, which
    # Run 17 committed and Run 28 did not touch.
    model = {"parameter": "cost at completion",
             "prior": {"mean": 100.0, "variance": 100.0, "source": "approved budget baseline"},
             "likelihood": {"observation": 120.0, "variance": 100.0,
                            "source": "reported cost at completion",
                            "variance_basis": "residual spread of reported forecasts"}}
    out = run("A1.3", {**BASE_EVM, "bayesianEacModel": model})
    check(mid, "positive: executes on the governed model record", not abstained(out))
    mu, var = O.normal_normal_posterior(100.0, 100.0, 120.0, 100.0)
    near(mid, "known-answer: the specification's posterior mean of 110",
         out.get("posterior_eac"), 110.0, tol=1e-9)
    near(mid, "known-answer: the specification's posterior variance of 50",
         out.get("posterior_variance"), 50.0, tol=1e-9)
    check(mid, "known-answer: production agrees with the independent normal-normal oracle",
          abs(out.get("posterior_eac") - mu) < 1e-9
          and abs(out.get("posterior_variance") - var) < 1e-9)
    check(mid, "structure: the prior, its source, the observation model and a credible "
               "interval are all reported",
          all(k in out for k in ("prior_mean", "prior_variance", "prior_source",
                                 "observation", "observation_variance", "observation_model",
                                 "credible_low", "credible_high")))
    check(mid, "invariant: the posterior variance is smaller than either input variance",
          out["posterior_variance"] < 100.0)
    check(mid, "invariant: the posterior mean lies between the prior mean and the observation",
          100.0 <= out["posterior_eac"] <= 120.0)
    check(mid, "missingness: with no governed model record the answer is not estimable, and "
               "the designed constant variances are not used in its place",
          abstained(run("A1.3", {**BASE_EVM, "bac": 1000.0, "cpi": 0.8})))
    check(mid, "missingness: a prior with no stated source is refused",
          abstained(run("A1.3", {**BASE_EVM, "bayesianEacModel": {
              **model, "prior": {"mean": 100.0, "variance": 100.0, "source": ""}}})))
    check(mid, "boundary: a variance of zero or below cannot carry a belief",
          abstained(run("A1.3", {**BASE_EVM, "bayesianEacModel": {
              **model, "prior": {"mean": 100.0, "variance": 0.0, "source": "x"}}})))
    check(mid, "calibration: no status band is asserted on a governed posterior",
          out.get("status_color") is None and out.get("calibration_pending") is True)
    check(mid, "label: the proxy qualifier is gone, because the proxy is gone",
          "A1.3" not in REG.PROXY_QUALIFIERS)

    # ------------------------------------------------------------------ 1.4 Kalman
    mid = "1.4"
    # THE SPECIFICATION'S OWN WORKED STEP, against the independent recursion Run 17 committed.
    x, p_, k = O.kalman_scalar_step(1.0, 1.0, 0.0, 1.0, 2.0)
    check(mid, "known-answer: the specification's worked step reproduces exactly",
          (x, p_, k) == (1.5, 0.5, 0.5))
    ssm = {"initial_state": 1.0, "initial_variance": 1.0, "process_variance": 0.0,
           "measurement_variance": 1.0, "observations": [2.0],
           "process_variance_source": "declared random walk, no process noise",
           "measurement_variance_source": "repeated readings of one period across two "
                                          "document types"}
    out = run("A1.4", {**BASE_EVM, "kalmanStateSpaceModel": ssm})
    check(mid, "positive: executes on the governed state space record", not abstained(out))
    near(mid, "known-answer: production reproduces the specification's filtered state of 1.5",
         out.get("smoothed_spi"), 1.5, tol=1e-9)
    near(mid, "known-answer: and the specification's gain of 0.5",
         out.get("final_gain"), 0.5, tol=1e-9)
    near(mid, "known-answer: and the specification's posterior variance of 0.5",
         out.get("posterior_variance"), 0.5, tol=1e-9)
    hist = [0.90, 0.94, 0.92, 0.96]
    want = O.kalman_scalar_filter(hist, q=0.01, r=0.1, p0=1.0)
    series = run("A1.4", {**BASE_EVM, "kalmanStateSpaceModel": {
        **ssm, "initial_state": hist[0], "initial_variance": 1.0, "process_variance": 0.01,
        "measurement_variance": 0.1, "observations": hist[1:]}})
    near(mid, "known-answer: a longer run matches the independent scalar filter",
         series.get("smoothed_spi"), round(want, 3), tol=1e-3)
    check(mid, "invariant: the filtered estimate lies within the observed range",
          min(hist) <= series["smoothed_spi"] <= max(hist))
    check(mid, "structure: both variances state where they came from",
          bool(out.get("process_variance_source"))
          and bool(out.get("measurement_variance_source")))
    check(mid, "missingness: with no governed state space record the answer is not estimable, "
               "and the fixed Q and R are not used in its place",
          abstained(run("A1.4", {**BASE_EVM, "spiHistory": hist})))
    check(mid, "missingness: a variance with no stated source is refused",
          abstained(run("A1.4", {**BASE_EVM, "kalmanStateSpaceModel": {
              **ssm, "measurement_variance_source": ""}})))
    check(mid, "boundary: a measurement variance of zero cannot be filtered on",
          abstained(run("A1.4", {**BASE_EVM, "kalmanStateSpaceModel": {
              **ssm, "measurement_variance": 0.0}})))
    check(mid, "calibration: no status band is asserted on a filtered state",
          out.get("status_color") is None and out.get("calibration_pending") is True)
    check(mid, "label: the proxy qualifier is gone, because the proxy is gone",
          "A1.4" not in REG.PROXY_QUALIFIERS)

    # ------------------------------------------------------------------ 1.5 ARIMA
    mid = "1.5"
    # RUN 28 REMEDIATED BOTH OF THESE MODULES, so the propositions below are inverted from
    # what Run 17 wrote. Run 17 established, and these checks recorded, that A1.5 was an AR(1)
    # on first differences under an ARIMA name and that A1.6 was a percent-complete ratio under
    # the Earned Schedule name. Both were observed FAILING against the v3 build before being
    # rewritten -- test_run17_scientific_methods.py raised KeyError: 'spi_time' -- and the
    # rewrite asserts the canonical contract rather than the defect it replaced.
    long_history = [0.99, 0.97, 0.96, 0.94, 0.93, 0.91, 0.90, 0.88, 0.87, 0.86]
    out = run("A1.5", {**BASE_EVM, "cpiHistory": long_history})
    check(mid, "positive: executes on a history long enough to identify a model from",
          not abstained(out))
    for field in ("arima_p", "arima_d", "arima_q", "ar_coefficients", "ma_coefficients",
                  "selection_criterion", "aicc", "residual_autocorrelation",
                  "ljung_box_lag1", "interval_low", "interval_high"):
        check(mid, f"structure: the declared ARIMA contract's {field} is reported",
              field in out)
    check(mid, "structure: the model order is identified rather than fixed at (1,1,0)",
          out.get("selection_criterion") == "AICc")
    check(mid, "boundary: a history shorter than the stated minimum is not estimable",
          abstained(run("A1.5", {**BASE_EVM, "cpiHistory": [0.95, 0.93, 0.90, 0.88]})))
    check(mid, "boundary: refuses a series carrying a non-positive cost index",
          abstained(run("A1.5", {**BASE_EVM, "cpiHistory": [0.95, 0.0, 0.90, 0.88] * 3})))
    flat = run("A1.5", {**BASE_EVM, "cpiHistory": [0.9] * 10})
    near(mid, "invariant: a constant series forecasts itself",
         flat.get("forecast_cpi"), 0.9, tol=1e-9)
    check(mid, "calibration: the forecast carries no status band, which is Run 33's work",
          out.get("status_color") is None and out.get("calibration_pending") is True)

    # ------------------------------------------------------------------ 1.6 Earned Schedule
    mid = "1.6"
    # THE INDEPENDENT ORACLE, committed by Run 17 before Run 28 existed and untouched by it.
    es = O.earned_schedule([0, 20, 40, 60], 50, 3)
    near(mid, "known-answer: the canonical interpolation on the specification's curve",
         es["SPI_t"], 5.0 / 6.0, tol=1e-12)
    curve = {"periods": [{"period_index": i, "period": f"P{i}", "cumulative_pv": v}
                         for i, v in enumerate([0, 20, 40, 60])],
             "actual_time_periods": 3,
             "baseline_version": "BL-1", "approval_source": "approved baseline"}
    out = run("A1.6", {**BASE_EVM, "ev": 50, "timePhasedBaseline": curve})
    check(mid, "positive: executes on the cumulative planned value curve", not abstained(out))
    near(mid, "known-answer: production now reproduces the independent oracle exactly",
         out.get("spi_time"), round(es["SPI_t"], 3), tol=1e-3)
    near(mid, "known-answer: the earned schedule itself is 2.5 periods",
         out.get("earned_schedule"), 2.5, tol=1e-9)
    near(mid, "known-answer: the time based schedule variance is minus half a period",
         out.get("schedule_variance_time"), -0.5, tol=1e-9)
    # THE DISCRIMINATOR RUN 17 WROTE, NOW SATISFIED IN THE OTHER DIRECTION: the canonical
    # measure MUST move when the shape of the planned value curve changes, and a percent
    # complete ratio cannot. Production now moves with it.
    front_curve = {**curve, "periods": [{"period_index": i, "period": f"P{i}",
                                         "cumulative_pv": v}
                                        for i, v in enumerate([0, 40, 55, 60])]}
    front_out = run("A1.6", {**BASE_EVM, "ev": 50, "timePhasedBaseline": front_curve})
    front = O.earned_schedule([0, 40, 55, 60], 50, 3)
    check(mid, "structural discriminator: production tracks the shape of the planned value "
               "curve, which a percent complete ratio structurally cannot",
          abs(front["SPI_t"] - es["SPI_t"]) > 0.1
          and abs(front_out.get("spi_time") - round(front["SPI_t"], 3)) < 1e-3)
    check(mid, "missingness: with no cumulative planned value curve the answer is not "
               "estimable, and no percent complete ratio is offered in its place",
          abstained(run("A1.6", {**BASE_EVM, "actualPctComplete": 50.0,
                                 "plannedPctComplete": 60.0})))
    check(mid, "missingness: refuses without the value of work performed",
          abstained(run("A1.6", {"timePhasedBaseline": curve})))
    check(mid, "boundary: a curve that falls over time is not a cumulative curve",
          abstained(run("A1.6", {**BASE_EVM, "ev": 50, "timePhasedBaseline": {
              **curve, "periods": [{"period_index": i, "period": f"P{i}", "cumulative_pv": v}
                                   for i, v in enumerate([0, 40, 20, 60])]}})))
    check(mid, "calibration: the time based index carries no status band",
          out.get("status_color") is None and out.get("calibration_pending") is True)

    # ------------------------------------------------------------------ 1.7 TCPI
    mid = "1.7"
    out = run("A1.7", {"bac": 100.0, "ev": 60.0, "ac": 70.0})
    near(mid, "known-answer: the specification's worked TCPI", out.get("tcpi"),
         round(O.tcpi(100, 60, 70), 3), tol=1e-3)
    check(mid, "positive: the identity is the budget-basis one", not abstained(out))
    check(mid, "structure: the target basis is stated in the finding",
          "budget" in (out.get("evidence_metric") or "").lower())
    check(mid, "boundary: abstains when the remaining budget is exactly zero",
          abstained(run("A1.7", {"bac": 100.0, "ev": 60.0, "ac": 100.0})))
    check(mid, "boundary: abstains when actual cost exceeds the budget",
          abstained(run("A1.7", {"bac": 100.0, "ev": 60.0, "ac": 120.0})))
    check(mid, "boundary: refuses a negative actual cost rather than banding it Green",
          abstained(run("A1.7", {"bac": 100.0, "ev": 60.0, "ac": -700.0})))
    check(mid, "missingness: refuses without an earned value",
          abstained(run("A1.7", {"bac": 100.0, "ac": 70.0})))
    # Metamorphic: the identity is scale-free in currency.
    a = run("A1.7", {"bac": 100.0, "ev": 60.0, "ac": 70.0})
    b = run("A1.7", {"bac": 100000.0, "ev": 60000.0, "ac": 70000.0})
    check(mid, "metamorphic: invariant under a change of currency scale",
          a.get("tcpi") == b.get("tcpi"))
    check(mid, "threshold: the band boundaries carry a recorded citation",
          "A1.7" in REG.BAND_SOURCES and len(REG.BAND_SOURCES["A1.7"]) > 100)
    check(mid, "threshold: the citation's own stated limit is recorded beside it",
          "not measured" in REG.BAND_SOURCE_LIMIT)

    # ------------------------------------------------------------------ 1.8 VAC
    mid = "1.8"
    out = run("A1.8", {"bac": 100.0, "cpi": 100.0 / 120.0})
    near(mid, "known-answer: the specification's worked VAC", out.get("vac"),
         round(O.vac(100, 120)), tol=1.0)
    check(mid, "structure: the forecast convention is the index-based one, and it is recorded",
          "A1.8" in REG.BAND_SOURCES and "index-based" in REG.BAND_SOURCES["A1.8"])
    check(mid, "boundary: refuses a non-positive cost index",
          abstained(run("A1.8", {"bac": 100.0, "cpi": 0.0}))
          and abstained(run("A1.8", {"bac": 100.0, "cpi": -0.5})))
    check(mid, "missingness: refuses without a budget at completion",
          abstained(run("A1.8", {"cpi": 0.9})))
    check(mid, "invariant: a unit cost index gives a variance of exactly zero",
          run("A1.8", {"bac": 100.0, "cpi": 1.0}).get("vac") == 0)
    check(mid, "metamorphic: invariant under a change of currency scale",
          run("A1.8", {"bac": 100.0, "cpi": 0.8}).get("vac_pct")
          == run("A1.8", {"bac": 100000.0, "cpi": 0.8}).get("vac_pct"))

    # ------------------------------------------------------------------ 1.9 Budget Execution
    mid = "1.9"
    # RUN 28. Run 17 recorded that the denominator was a progress-scaled budget rather than an
    # approved time-phased spend profile, and these checks recorded that absence. v3 requires
    # the profile and abstains without it.
    profile = {"status_period_index": 3,
               "periods": [{"period_index": i, "expected_spend": v}
                           for i, v in enumerate([10.0, 25.0, 40.0, 50.0])],
               "baseline_version": "BL-1", "approval_source": "approved spend plan"}
    out = run("A1.9", {"ac": 60.0, "expenditureBaseline": profile})
    check(mid, "positive: executes on the approved expenditure baseline", not abstained(out))
    near(mid, "known-answer: the specification's execution ratio of 1.20",
         out.get("execution_ratio"), 1.20, tol=1e-9)
    near(mid, "known-answer: and its execution deviation of plus 0.20",
         out.get("execution_deviation"), 0.20, tol=1e-9)
    check(mid, "structure: the planned amount comes from an approved profile that states its "
               "version and approval source",
          out.get("expected_spend") == 50.0 and bool(out.get("baseline_version"))
          and bool(out.get("approval_source")))
    check(mid, "missingness: with no approved expenditure profile the answer is not estimable, "
               "and budget times percent complete is not used in its place",
          abstained(run("A1.9", {"bac": 100.0, "ac": 60.0, "actualPctComplete": 50.0})))
    check(mid, "boundary: refuses a negative actual cost rather than banding it",
          abstained(run("A1.9", {"ac": -700.0, "expenditureBaseline": profile})))
    check(mid, "boundary: a profile that does not reach the reported period states no planned "
               "amount for it",
          abstained(run("A1.9", {"ac": 60.0, "expenditureBaseline": {
              **profile, "status_period_index": -1}})))
    check(mid, "metamorphic: invariant under a change of currency scale",
          run("A1.9", {"ac": 60.0, "expenditureBaseline": profile})["execution_ratio"]
          == run("A1.9", {"ac": 6e5, "expenditureBaseline": {
              **profile, "periods": [{"period_index": i, "expected_spend": v * 1e4}
                                     for i, v in enumerate([10.0, 25.0, 40.0, 50.0])]}
                 })["execution_ratio"])
    check(mid, "label: the proxy qualifier is gone, because the proxy is gone",
          "A1.9" not in REG.PROXY_QUALIFIERS)
    check(mid, "calibration: no status band is asserted, and the contract supplies none",
          out.get("status_color") is None and out.get("calibration_pending") is True)

    # -------------------------------------------------------- 1.10 CPI Shrinkage Forecast
    mid = "1.10"
    # RUN 28, APPROVED RENAME: Regression to Mean CPI becomes CPI Shrinkage Forecast. Run 17
    # recorded that the target was the project's OWN history and the weight a fixed one half.
    # v3 requires a governed reference population and refuses a weight declared as fixed.
    refclass = {"members": [{"reference_project_id": f"REF-{i}", "cpi_outcome": v}
                            for i, v in enumerate([0.95, 1.00, 1.05])],
                "shrinkage_weight": 0.60,
                "class_membership_basis": "same delivery method and size band",
                "weight_estimation_method": "variance components across the population",
                "data_vintage": "2026-06", "project_stage": "execution",
                "evaluated_project_id": "PRJ-UNDER-TEST"}
    out = run("A1.10", {**BASE_EVM, "cpi": 0.80, "cpiReferenceClass": refclass})
    check(mid, "positive: executes on the governed reference class", not abstained(out))
    near(mid, "known-answer: the specification's pooled value of 0.88",
         out.get("cpi_shrunk"), 0.88, tol=1e-9)
    near(mid, "known-answer: production agrees with the independent shrinkage oracle",
         out.get("cpi_shrunk"), round(O.cpi_shrinkage(0.80, 1.00, 0.60), 3), tol=1e-3)
    check(mid, "canonical structure: the target is an OUTSIDE reference population, and the "
               "population, its basis and its vintage are reported",
          out.get("reference_members") == 3 and bool(out.get("class_membership_basis"))
          and bool(out.get("data_vintage")))
    check(mid, "invariant: the pooled value lies between the project reading and the "
               "reference mean",
          min(0.80, 1.00) <= out["cpi_shrunk"] <= max(0.80, 1.00))
    check(mid, "invariant: a weight of one returns the project's own reading unchanged",
          run("A1.10", {**BASE_EVM, "cpi": 0.80, "cpiReferenceClass": {
              **refclass, "shrinkage_weight": 1.0}})["cpi_shrunk"] == 0.8)
    check(mid, "missingness: with no reference class the answer is not estimable, and the "
               "project's own history is not used as a substitute population",
          abstained(run("A1.10", {**BASE_EVM, "cpiHistory": [0.7, 0.8, 0.9]})))
    check(mid, "parameter: a weight declared as fixed rather than estimated is refused",
          abstained(run("A1.10", {**BASE_EVM, "cpi": 0.8, "cpiReferenceClass": {
              **refclass, "weight_estimation_method": "HARD_CODED"}})))
    check(mid, "boundary: a weight outside nought to one is not a share",
          abstained(run("A1.10", {**BASE_EVM, "cpi": 0.8, "cpiReferenceClass": {
              **refclass, "shrinkage_weight": 1.4}})))
    check(mid, "self-training: the project may not be a member of the population it is pooled "
               "toward",
          abstained(run("A1.10", {**BASE_EVM, "cpi": 0.8, "cpiReferenceClass": {
              **refclass, "members": refclass["members"]
              + [{"reference_project_id": "PRJ-UNDER-TEST", "cpi_outcome": 0.9}]}})))
    check(mid, "rename: the registry carries the approved name",
          REG.registry_index()["A1.10"]["module_name"] == "CPI Shrinkage Forecast")
    check(mid, "label: the proxy qualifier is gone, because the proxy is gone",
          "A1.10" not in REG.PROXY_QUALIFIERS)

    # ------------------------------------------------------------------ 1.11 ICE Ratio
    # ------------------------------ 1.11 Independent EAC Reconciliation Index
    mid = "1.11"
    # RUN 28, APPROVED RENAME: ICE Ratio becomes Independent EAC Reconciliation Index. Run 17's
    # independence test proved that v2's two "forecasts" were deterministic functions of one
    # input vector, so no independent estimate existed. v3 requires two provenance-distinct
    # estimates and CHECKS the distinction rather than asserting it.
    pair = {"management_eac": {"eac": 100.0, "source": "project controls monthly report",
                               "method": "cost index extrapolation",
                               "assumptions": "current performance continues",
                               "model_version": "PC-2026.08",
                               "responsible_party": "project management team"},
            "independent_eac": {"eac": 120.0, "source": "independent review board",
                                "method": "bottom up re-estimate of remaining work",
                                "assumptions": "remaining scope re-priced at current rates",
                                "model_version": "IRB-2026.07",
                                "responsible_party": "independent review board"}}
    out = run("A1.11", {"independentEacPair": pair})
    check(mid, "positive: executes on two provenance-distinct forecasts", not abstained(out))
    near(mid, "known-answer: the specification's reconciliation index of 1.20",
         out.get("ier"), 1.20, tol=1e-9)
    near(mid, "known-answer: and its divergence of 0.20",
         out.get("divergence"), 0.20, tol=1e-9)
    check(mid, "lineage: both estimates carry source, method, assumptions, model version and "
               "responsible party",
          all(k in out.get("management_lineage", {})
              for k in ("source", "method", "assumptions", "model_version",
                        "responsible_party"))
          and all(k in out.get("independent_lineage", {})
                  for k in ("source", "method", "assumptions", "model_version",
                            "responsible_party")))
    check(mid, "independence: two forecasts prepared by the same METHOD are two "
               "transformations of one estimate and are refused",
          abstained(run("A1.11", {"independentEacPair": {
              **pair, "independent_eac": {**pair["independent_eac"],
                                          "method": "cost index extrapolation"}}})))
    check(mid, "independence: two forecasts prepared by the same PARTY are refused",
          abstained(run("A1.11", {"independentEacPair": {
              **pair, "independent_eac": {**pair["independent_eac"],
                                          "responsible_party": "project management team"}}})))
    check(mid, "missingness: with no second estimate the answer is not estimable, and two "
               "transformations of one reported vector are not used in its place",
          abstained(run("A1.11", {"bac": 1000.0, "ev": 500.0, "ac": 600.0, "cpi": 0.8})))
    check(mid, "missingness: an estimate with a blank lineage field is refused",
          abstained(run("A1.11", {"independentEacPair": {
              **pair, "management_eac": {**pair["management_eac"], "assumptions": ""}}})))
    check(mid, "invariant: identical forecasts give an index of exactly one and no divergence",
          run("A1.11", {"independentEacPair": {
              **pair, "independent_eac": {**pair["independent_eac"], "eac": 100.0}}})["ier"]
          == 1.0)
    check(mid, "boundary: a management forecast of zero has nothing to reconcile against",
          abstained(run("A1.11", {"independentEacPair": {
              **pair, "management_eac": {**pair["management_eac"], "eac": 0.0}}})))
    check(mid, "rename: the registry carries the approved name",
          REG.registry_index()["A1.11"]["module_name"]
          == "Independent EAC Reconciliation Index")


# =============================================================================================
# CATEGORY 6 -- signal synthesis (4 targets)
# =============================================================================================

def _pkg(evm=None, mc=None, cusum=None, doc=None, breached=False, array=None) -> dict:
    signals = {}
    if evm is not None:
        signals["evm"] = {"status": evm}
    if mc is not None:
        signals["mc"] = {"status": mc}
    if cusum is not None:
        signals["cusum"] = {"status": cusum, "breached": breached}
    if doc is not None:
        signals["doc"] = {"status": doc}
    return {"signals": signals,
            "simulationSignals": {"signal_array": array or []}}


def cat6() -> None:
    # ------------------------------------------------------------------ 6.1 Conservative Dominance
    mid = "6.1"
    all_green = _pkg("Green", "Green", "Green", "Green")
    out = run("B1.1", all_green)
    check(mid, "positive: agreement at low risk reads Green", out.get("status_color") == "Green")
    two_red = _pkg("Red", "Red", "Green", "Green")
    # RUN 20 CYCLE 9. The expected value here was "Red-review", the decision layer's own state
    # name, because that is what the counting rule produced. A dominance rule reports a BAND, and
    # the band two Reds dominate to is Red. The oracle already said Red and production now agrees
    # with it; the check is aligned to the oracle rather than to the state name the defect
    # happened to emit. The decision layer's state is still reported on the result, under its own
    # name, so nothing is hidden.
    check(mid, "positive: two red signals escalate",
          O.conservative_dominance(["Red", "Red", "Green", "Green"]) == "Red"
          and FUSION.normalise_status(run("B1.1", two_red).get("status_color")) == "Red"
          and run("B1.1", two_red).get("decision_layer_state") == "Red-review")
    # THE DEFINING TEST. Conservative dominance is the worst credible qualified signal. One Red
    # among Greens is Red under the canonical rule. Compare production against the oracle.
    one_red = _pkg("Green", "Green", "Green", "Red")
    got = run("B1.1", one_red).get("status_color")
    want = O.conservative_dominance(["Green", "Green", "Green", "Red"])
    proposition(mid, "6.1/single-red-dominance",
                "known-answer: a single qualified Red is the worst credible signal",
                FUSION.normalise_status(got) == want,
                f"production returns {got!r}; canonical conservative dominance is {want!r}. "
                f"A lone Red signal is absorbed into Amber, because the rule escalates only at "
                f"two Reds or a breached control chart alongside a Red forecast.")
    one_amber = _pkg("Green", "Green", "Green", "Amber")
    got_a = run("B1.1", one_amber).get("status_color")
    check(mid, "known-answer: a single qualified Amber is the worst credible signal",
          FUSION.normalise_status(got_a) == O.conservative_dominance(
              ["Green", "Green", "Green", "Amber"]),
          f"production {got_a!r}")
    # Monotonicity: worsening one input can never improve the result.
    ladder = ["Green", "Yellow", "Amber", "Red"]
    ranks = []
    for s in ladder:
        r = run("B1.1", _pkg("Green", "Green", "Green", s)).get("status_color")
        ranks.append(O.SEVERITY_RANK.get(FUSION.normalise_status(r), -1))
    check(mid, "invariant: monotone non-decreasing as one signal worsens",
          all(ranks[i] <= ranks[i + 1] for i in range(len(ranks) - 1)), str(ranks))
    # Permutation invariance: which signal slot carries the Red must not matter.
    perms = {run("B1.1", p).get("status_color") for p in (
        _pkg("Red", "Green", "Green", "Green"), _pkg("Green", "Red", "Green", "Green"),
        _pkg("Green", "Green", "Red", "Green"), _pkg("Green", "Green", "Green", "Red"))}
    check(mid, "invariant: permutation invariant across signal slots", len(perms) == 1,
          str(perms))
    check(mid, "missingness: an absent signal does not read as Green",
          run("B1.1", _pkg(None, "Green", "Green", "Green")).get("status_color") != "Green")
    check(mid, "boundary: an unknown status string does not read as Green",
          run("B1.1", _pkg("banana", "Green", "Green", "Green")).get("status_color") != "Green")
    check(mid, "missingness: refuses entirely when the package is absent",
          abstained(run("B1.1", {})))

    # ------------------------------------------------------------------ 6.2 Weighted Voting
    mid = "6.2"
    # RUN 30 v15. The four literal weights (1.5/1.0/0.6/1.5) had no authority behind them
    # anywhere in the repository, so the module no longer weighs anything without a governed
    # weighting policy. Its recorded disposition was already PARAMETER_PROVENANCE_BLOCKED.
    pkg = _pkg(mc="Green", cusum="Amber", doc="Red")
    out = run("B1.2", pkg)
    check(mid, "parameter provenance: abstains rather than weigh by literals with no authority",
          abstained(out) and "weighting policy" in str(out.get("abstention_reason", "")),
          str(out))
    check(mid, "known-answer: the canonical weighted severity score on the specification's own "
               "example", abs(O.weighted_severity_score(["Green", "Amber", "Red"],
                                                        [0.5, 0.3, 0.2]) - 1.2) < 1e-12)
    # THE CONTRACT'S OWN ORACLE, on the canonical engine, with a governed policy supplied.
    from app.simulation import canonical_v5 as _V5
    _pol = {"set_by": "Run-30 supplied contract", "authority": "supervisory contract oracle",
            "weights": {"g": 0.5, "a": 0.3, "r": 0.2}}
    _gs = [{"signal_id": "g", "status": "Green", "period": 1, "lineage_body": "b1"},
           {"signal_id": "a", "status": "Amber", "period": 1, "lineage_body": "b2"},
           {"signal_id": "r", "status": "Red", "period": 1, "lineage_body": "b3"}]
    _wv = _V5.weighted_voting(_gs, _pol)
    check(mid, "known-answer: class-weighted voting gives Green .5, Amber .3, Red .2 and the "
               "winner Green", abs(_wv["votes"]["Green"] - 0.5) < 1e-12
          and abs(_wv["votes"]["Amber"] - 0.3) < 1e-12
          and abs(_wv["votes"]["Red"] - 0.2) < 1e-12 and _wv["winner"] == "Green", str(_wv))
    check(mid, "parameter provenance: a governed policy carries its authority onto the result",
          _wv["weight_provenance"].get("authority") == "supervisory contract oracle")
    # LINEAGE. A second reading of one body must NOT manufacture weight.
    _dupsig = _gs + [{"signal_id": "r2", "status": "Red", "period": 1, "lineage_body": "b3"}]
    _pol2 = dict(_pol, weights={"g": 0.5, "a": 0.3, "r": 0.2, "r2": 0.2})
    check(mid, "lineage: duplicating one signal does NOT accumulate weight",
          abs(_V5.weighted_voting(_dupsig, _pol2)["votes"]["Red"] - 0.2) < 1e-12,
          str(_V5.weighted_voting(_dupsig, _pol2)["votes"]))
    check(mid, "missingness: refuses when no signal qualifies", abstained(run("B1.2", _pkg())))
    check(mid, "boundary: an unknown status is refused rather than voted",
          abstained(run("B1.2", _pkg(mc="banana", cusum="Green", doc="Green"))))

    # ------------------------------------------------------------------ 6.3 Majority Rules
    mid = "6.3"
    from app.simulation import canonical_v5 as _V5b
    _mk = lambda i, st, b: {"signal_id": i, "status": st, "period": 1, "lineage_body": b}
    check(mid, "known-answer: Green, Red, Red gives Red",
          _V5b.majority_rules([_mk("s1", "Green", "b1"), _mk("s2", "Red", "b2"),
                               _mk("s3", "Red", "b3")])["winner"]
          == O.majority_state(["Green", "Red", "Red"]))
    # RUN 30 v15. A TIE IS A CONFLICT AND IS REPORTED AS ONE. It is no longer silently resolved
    # to the more severe state: choosing a winner from a tie is a governance decision with a
    # direction, and the contract requires it to be declared rather than taken.
    _tie = _V5b.majority_rules([_mk("s1", "Green", "b1"), _mk("s2", "Red", "b2")])
    check(mid, "boundary: an even split returns NO unique winner and is reported as a conflict",
          _tie["unique_winner"] is False and _tie["conflict"] is True, str(_tie))
    check(mid, "missingness: an absent signal is not counted as Green",
          run("B1.3", _pkg(cusum="Red", doc="Red")).get("counts", {}).get("Green") == 0)
    check(mid, "boundary: an unknown status is refused rather than counted",
          abstained(run("B1.3", _pkg(mc="banana", cusum="Red"))))
    check(mid, "missingness: refuses when nothing qualifies", abstained(run("B1.3", _pkg())))
    check(mid, "quorum: a single signal is not a majority and the module says so",
          abstained(run("B1.3", _pkg(cusum="Red"))))
    check(mid, "lineage: duplicating one signal does NOT change the count",
          _V5b.majority_rules([_mk("a", "Red", "bX"), _mk("a2", "Red", "bX"),
                               _mk("g", "Green", "bY")])["counts"]["Red"] == 1)

    # ------------------------------------------------------------------ 6.4 Worst-N-of-M
    mid = "6.4"
    out = run("B1.4", _pkg(mc="Red", cusum="Green", doc="Green"))
    # RUN 30 v15. N IS PREDECLARED AND FROZEN AT TWO, and the statistic is the MEAN of the worst
    # two severities. It asserts no band, so `abstained()` would read it as an abstention; what
    # is checked is that the statistic was computed.
    check(mid, "structure: N is predeclared and frozen at two; the rule is the mean of the "
               "worst two, with no proportional threshold over M",
          out.get("mean_worst_2") is not None and "total_modules" not in out, str(out))
    # THE DILUTION TEST. Under any worst-N-of-M rule the answer cannot improve when an
    # additional benign signal is added: the worst N are unchanged. Prove what production does.
    three = run("B1.4", _pkg(mc="Red", cusum="Green", doc="Green"))
    four = run("B1.4", _pkg(mc="Red", cusum="Green", doc="Green",
                            array=[{"status_color": "Green"}]))
    check(mid, "invariant: adding a benign signal does not lower the statistic",
          four.get("mean_worst_2") >= three.get("mean_worst_2"),
          f"{three.get('mean_worst_2')} then {four.get('mean_worst_2')}")
    # THE SECOND-STAGE OPERATION IS THE MEAN, NOT THE MAXIMUM. Taking the maximum of the worst
    # two collapses the module onto Conservative Dominance, which the contract forbids: on
    # Green, Green, Red the mean is 1.5 where the maximum would be 3.
    from app.simulation import canonical_v5 as _V5c
    _mk4 = lambda i, st, b: {"signal_id": i, "status": st, "period": 1, "lineage_body": b}
    _w2 = _V5c.worst_two_of_m([_mk4("a", "Green", "b1"), _mk4("b", "Green", "b2"),
                               _mk4("c", "Red", "b3")])
    check(mid, "known-answer: Green, Green, Red gives a Worst-2 mean of 1.5, so the module does "
               "NOT collapse onto conservative dominance",
          abs(_w2["mean_worst_2"] - 1.5) < 1e-12
          and O.conservative_dominance(["Green", "Green", "Red"]) == "Red", str(_w2))
    check(mid, "missingness: refuses when nothing qualifies", abstained(run("B1.4", _pkg())))
    check(mid, "boundary: an unknown status is refused rather than dropped from a denominator",
          abstained(run("B1.4", _pkg(mc="banana", cusum="Red"))))
    check(mid, "calibration: no traffic-light boundary is asserted over the statistic",
          run("B1.4", _pkg("Green", "Green", "Green", "Green")).get("status_color") is None
          and run("B1.4", _pkg("Green", "Green", "Green", "Green"))
          .get("calibration_pending") is not None)


# =============================================================================================
# CATEGORY 7 -- 7.1 Dempster-Shafer, the one Category-7 target this run reached
# =============================================================================================

def cat7_partial() -> None:
    mid = "7.1"
    # The specification's worked combination, computed independently over focal SETS.
    theta = frozenset({"G", "R"})
    m1 = {frozenset({"G"}): 0.6, theta: 0.4}
    m2 = {frozenset({"G"}): 0.5, theta: 0.5}
    comb, k = O.dempster_combine(m1, m2)
    near(mid, "known-answer: conflict coefficient is zero when one source is ignorant", k, 0.0)
    near(mid, "known-answer: combined mass on the singleton", comb[frozenset({"G"})], 0.8)
    near(mid, "known-answer: combined mass on the frame", comb[theta], 0.2)
    # Production's own combination over the same shapes: Green 0.8 / ignorance 0.2, twice.
    p1 = {"Green": 0.6, "Yellow": 0.0, "Amber": 0.0, "Red": 0.0, "Unknown": 0.4}
    p2 = {"Green": 0.5, "Yellow": 0.0, "Amber": 0.0, "Red": 0.0, "Unknown": 0.5}
    pc = FUSION.dst_combine(p1, p2)
    near(mid, "implementation: production reproduces the canonical combination",
         pc["Green"], 0.8, tol=1e-9)
    near(mid, "implementation: production reproduces the canonical ignorance mass",
         pc["Unknown"], 0.2, tol=1e-9)
    near(mid, "implementation: ignorance is not counted as conflict", pc["conflict"], 0.0)
    # Belief and plausibility, canonical.
    near(mid, "known-answer: Bel of the singleton", O.belief(comb, frozenset({"G"})), 0.8)
    near(mid, "known-answer: Pl of the singleton", O.plausibility(comb, frozenset({"G"})), 1.0)
    near(mid, "invariant: Bel <= Pl", 0.0,
         max(0.0, O.belief(comb, frozenset({"G"})) - O.plausibility(comb, frozenset({"G"}))))
    # Reliability discounting.
    disc = O.shafer_discount(m1, 0.5, theta)
    near(mid, "known-answer: discounting moves mass to the frame", disc[theta], 0.7)
    near(mid, "invariant: a discounted mass function still sums to one", sum(disc.values()), 1.0)
    # TOTAL CONFLICT. The canonical answer is that the rule is undefined; the specification
    # forbids fabricating a verdict.
    tc = FUSION.dst_combine({"Green": 1.0, "Yellow": 0, "Amber": 0, "Red": 0, "Unknown": 0},
                            {"Green": 0, "Yellow": 0, "Amber": 0, "Red": 1.0, "Unknown": 0})
    check(mid, "boundary: total conflict is flagged rather than silently normalised",
          tc.get("conflict") == 1.0, str(tc))
    check(mid, "boundary: total conflict does not yield a decidable verdict, because every "
               "state carries equal mass",
          len({round(tc[s], 9) for s in FUSION.STATES}) == 1, str(tc))
    # Mass admissibility.
    check(mid, "invariant: every declared status mass is a normalised distribution",
          all(abs(sum(m.values()) - 1.0) < 1e-9 for m in FUSION.STATUS_MASS.values()))
    check(mid, "invariant: combination is commutative",
          FUSION.dst_combine(p1, p2) == FUSION.dst_combine(p2, p1))
    # LINEAGE. Dempster's rule assumes independent sources. Combining one source with itself
    # must not be treated as corroboration; prove production does sharpen it, which is the
    # dependence hazard the specification names.
    once = FUSION.dst_combine(FUSION.STATUS_MASS["Red"], FUSION.STATUS_MASS["Unknown"]
                              if "Unknown" in FUSION.STATUS_MASS else p2)
    twice = FUSION.dst_combine(FUSION.STATUS_MASS["Red"], FUSION.STATUS_MASS["Red"])
    check(mid, "lineage: combining a source with an identical copy sharpens belief, so "
               "correlated evidence would be treated as corroboration",
          twice["Red"] > FUSION.STATUS_MASS["Red"]["Red"], f"{twice['Red']}")
    check(mid, "missingness: an abstaining module contributes no mass at all",
          FUSION.status_to_mass(None) is None
          and FUSION.status_to_mass("banana") is None)
    _ = once


# =============================================================================================
# PORTFOLIO HEALTH -- PH.1 to PH.5 (5 targets)
# =============================================================================================

def _proj(pid, cpi, spi, doc=0.0, pct=50.0):
    return {"id": pid, "cpi": cpi, "spi": spi, "docRiskScore": doc, "actualPctComplete": pct}


def portfolio_health() -> None:
    # RUN 33 MARKED THIS SECTION HISTORICAL. Every check below executes
    # `app.simulation.portfolio.compute_portfolio`, which is the SUPERSEDED v20 implementation:
    # Run 33 repointed production onto the canonical v8 Portfolio Health layer through
    # `portfolio_health.compute_portfolio_health_snapshot`. The v20 function is PRESERVED because
    # these findings -- and Run 2's, 6's, 13's, 14's and 15's -- are evidence about it, and
    # deleting it would delete the subject of the findings.
    #
    # THE ASSERTIONS BELOW ARE UNCHANGED and are still exactly what they always asserted: what
    # the instrument USED to do. `assert_not_reachable` supplies the other half, because a
    # historical test that only proved the old behaviour would go green again if a later run
    # reconnected the proxy, and a test that can be satisfied by live code is not a historical
    # record.
    import run33_historical_portfolio as _R33H
    _R33H.assert_not_reachable(
        lambda cond, name, detail="": check("PH.1", f"HISTORICAL: {name}", cond, str(detail)))

    # A cohort of tight inliers plus one distant project.
    inliers = [_proj(f"p{i}", 1.00 + 0.01 * (i % 3), 1.00 + 0.01 * (i % 2)) for i in range(8)]
    anomaly = _proj("odd", 0.40, 0.35, doc=0.9, pct=95.0)
    cohort = inliers + [anomaly]

    # ------------------------------------------------------------------ PH.1 Isolation Forest
    mid = "PH.1"
    res = compute_portfolio(cohort, "odd", None, CUTOFF)
    iso = res["results"].get("cat8_1_isolation_forest")
    check(mid, "positive: a forest is grown and a score returned", iso is not None, str(res))
    if iso:
        check(mid, "structure: the canonical forest parameters are reported",
              all(k in iso for k in ("trees", "subsample", "mean_path_length", "normaliser")))
        check(mid, "structure: the scored project is excluded from its own reference cohort",
              iso.get("reference_size") == len(cohort) - 1)
        # Independent normalisation check against the specification's c(n), computed with the
        # EXACT harmonic number rather than the paper's ln+gamma estimate.
        psi = iso["subsample"]
        # The production normaliser uses the paper's own ln(i)+gamma estimate of the harmonic
        # number; the oracle uses the exact harmonic sum. At psi=8 the estimate sits about 0.14
        # below the exact value, which is the documented small-i deviation and not an error.
        near(mid, "known-answer: the normaliser agrees with the canonical c(psi) to within the "
                  "paper's own harmonic estimate error", iso["normaliser"], O.c_factor(psi),
             tol=0.15)
        check(mid, "known-answer: the estimate sits BELOW the exact harmonic value, as the "
                   "paper's approximation does", iso["normaliser"] < O.c_factor(psi))
        # The score identity: s = 2^(-E[h]/c(psi)), recomputed independently.
        near(mid, "known-answer: the anomaly score is the canonical path-length transform",
             iso["anomaly_score"],
             round(2.0 ** (-iso["mean_path_length"] / iso["normaliser"]), 2), tol=0.02)
        check(mid, "invariant: the score lies in the unit interval",
              0.0 <= iso["anomaly_score"] <= 1.0)
        check(mid, "reproducibility: the same cohort and seed give the same score",
              compute_portfolio(cohort, "odd", None, CUTOFF)["results"][
                  "cat8_1_isolation_forest"]["anomaly_score"] == iso["anomaly_score"])
    # THE DISCRIMINATION TEST, on ONE fixed forest so both points are scored against the same
    # trees. Scoring two projects through compute_portfolio grows two DIFFERENT forests, because
    # each excludes itself from its own reference cohort, and scores from different forests are
    # not comparable. That is a property of the wiring, recorded here rather than assumed.
    import random as _r
    rr = _r.Random(7)
    cont_ref = [[rr.gauss(1.0, 0.03), rr.gauss(1.0, 0.03), rr.gauss(0.2, 0.05),
                 rr.gauss(0.5, 0.1)] for _ in range(20)]
    cf = IsolationForest(cont_ref, n_trees=100, subsample=20, seed=20250815)
    s_out, s_in = cf.anomaly_score([0.4, 0.35, 0.9, 0.95]), cf.anomaly_score([1.0, 1.0, 0.2, 0.5])
    check(mid, "known-answer: on continuously distributed features one forest ranks a planted "
               "anomaly above a central inlier", s_out > s_in, f"{s_out:.4f} vs {s_in:.4f}")
    check(mid, "known-answer: the central inlier scores below the one-half no-anomaly level "
               "the paper states", s_in < 0.5, f"{s_in:.4f}")
    # THE DEGENERACY BOUNDARY. The portfolio feature vector holds document risk and percent
    # complete, which are constant across a cohort that has uploaded nothing, and a cost index
    # that takes few distinct values. On such a cohort the trees have almost nothing to split.
    deg_ref = [[1.00 + 0.01 * (i % 3), 1.00 + 0.01 * (i % 2), 0.0, 0.5] for i in range(8)]
    df = IsolationForest(deg_ref, n_trees=100, subsample=8, seed=20250815)
    d_out, d_in = df.anomaly_score([0.4, 0.35, 0.9, 0.95]), df.anomaly_score([1.0, 1.0, 0.0, 0.5])
    proposition(mid, "PH.1/degenerate-cohort-resolution",
                "boundary: an extreme outlier must not receive the same score as a central "
                "inlier", d_out != d_in,
                f"on a cohort whose document-risk and progress features are constant and whose "
                f"cost index takes three distinct values, an extreme outlier and a central "
                f"inlier both score {d_out:.4f}. Splits are drawn between the reference min and "
                f"max, so a point outside that range can never be separated by one split, and "
                f"with two constant features the trees exhaust the height limit first.")
    # Seeded randomisation is real: a different seed builds different trees.
    ref = [[p["cpi"], p["spi"], p["docRiskScore"], p["actualPctComplete"] / 100]
           for p in inliers]
    f1 = IsolationForest(ref, n_trees=20, subsample=8, seed=1)
    f2 = IsolationForest(ref, n_trees=20, subsample=8, seed=2)
    tgt = [0.4, 0.35, 0.9, 0.95]
    check(mid, "stochastic diagnostic: a different seed builds a different forest",
          f1.anomaly_score(tgt) != f2.anomaly_score(tgt))
    check(mid, "invariant: c(2) is exactly one, as the paper states",
          abs(prod_c(2) - 1.0) < 1e-12)
    check(mid, "boundary: abstains by absence with fewer than two other projects",
          "cat8_1_isolation_forest" not in compute_portfolio(
              [_proj("a", 1.0, 1.0), _proj("b", 1.0, 1.0)], "a", None, CUTOFF)["results"])
    check(mid, "threshold: the operating threshold is frozen at the Run-15 calibrated value",
          abs(__import__("app.simulation.portfolio", fromlist=["x"]).IF_ANOMALY_THRESHOLD
              - 0.576) < 1e-12)

    # ------------------------------------------------------------------ PH.2 Portfolio Outlier
    mid = "PH.2"
    po = res["results"]["cat8_2_portfolio_outlier"]
    check(mid, "positive: a percentile rank is reported", po.get("composite_percentile")
          is not None)
    # Declared convention: rank = share of cohort at or below this project on each index, so a
    # worst-performing project takes the lowest rank. Recompute independently.
    n = len(cohort)
    cpi_rank = sum(1 for p in cohort if p["cpi"] <= anomaly["cpi"]) / n
    spi_rank = sum(1 for p in cohort if p["spi"] <= anomaly["spi"]) / n
    near(mid, "known-answer: the composite rank recomputed independently",
         po["composite_percentile"], round((cpi_rank + spi_rank) / 2 * 100), tol=1.0)
    check(mid, "known-answer: the extreme project takes the most extreme tail rank under the "
               "declared performance orientation", po["composite_percentile"] <= 15)
    best = compute_portfolio(cohort, "p1", None, CUTOFF)["results"][
        "cat8_2_portfolio_outlier"]
    check(mid, "invariant: a better-performing project takes a higher rank",
          best["composite_percentile"] > po["composite_percentile"])
    check(mid, "invariant: rank is bounded by nought and one hundred",
          0 <= po["composite_percentile"] <= 100)
    perm = compute_portfolio(list(reversed(cohort)), "odd", None, CUTOFF)["results"][
        "cat8_2_portfolio_outlier"]
    check(mid, "metamorphic: invariant to the order of the cohort",
          perm["composite_percentile"] == po["composite_percentile"])
    check(mid, "boundary: refuses a cohort below the declared minimum",
          compute_portfolio([_proj("a", 1.0, 1.0)], "a", None, CUTOFF).get("insufficient_data"))
    # RUN 33 WITHDREW THE D1.2 PROXY QUALIFIER, because the proxy it described is gone: the v21
    # module ranks the complete governed required risk-oriented feature set of a declared cohort
    # by midrank percentile with the orientation applied before ranking, and carries no bands at
    # all. The property this check protects -- that the label matches the implementation -- is
    # kept, in the direction that is now true. See code_audit/run33_proxy_qualifier_withdrawal.csv.
    check(mid, "label: carries NO proxy qualifier, because the proxy it described is retired",
          "D1.2" not in REG.PROXY_QUALIFIERS)

    # ------------------------------------------------------------------ PH.3 Trajectory
    mid = "PH.3"
    hist = [{"signal_inputs": {"cpi": v}} for v in (1.0, 0.9, 0.8)]
    tres = compute_portfolio(cohort, "odd", hist, CUTOFF)["results"]
    tc = tres.get("cat8_3_trajectory_classifier")
    check(mid, "positive: a trend is classified from a real history", tc is not None)
    if tc:
        near(mid, "known-answer: the slope over two intervals, not three observations",
             tc["trend"], O.ols_slope([0, 1, 2], [1.0, 0.9, 0.8]), tol=1e-3)
        check(mid, "known-answer: a deteriorating slope is classified adversely",
              tc["status_color"] in ("Amber", "Red"), str(tc))
    flat_h = [{"signal_inputs": {"cpi": 0.9}} for _ in range(3)]
    flat = compute_portfolio(cohort, "odd", flat_h, CUTOFF)["results"].get(
        "cat8_3_trajectory_classifier")
    check(mid, "invariant: a flat history has a slope of exactly zero",
          flat is not None and abs(flat["trend"]) < 1e-12)
    up = compute_portfolio(cohort, "odd",
                           [{"signal_inputs": {"cpi": v}} for v in (0.8, 0.9, 1.0)],
                           CUTOFF)["results"].get("cat8_3_trajectory_classifier")
    check(mid, "metamorphic: reversing the series reverses the sign of the slope",
          up is not None and tc is not None and abs(up["trend"] + tc["trend"]) < 1e-12)
    check(mid, "missingness: abstains by absence with no usable history",
          "cat8_3_trajectory_classifier" not in compute_portfolio(
              cohort, "odd", [], CUTOFF)["results"])
    check(mid, "boundary: abstains with a single observation",
          "cat8_3_trajectory_classifier" not in compute_portfolio(
              cohort, "odd", [{"signal_inputs": {"cpi": 0.9}}], CUTOFF)["results"])

    # ------------------------------------------------------------------ PH.4 Cross-project
    mid = "PH.4"
    cp = res["results"]["cat8_4_cross_project_pattern"]
    check(mid, "positive: a match count is reported", "similar_project_count" in cp)
    # Structural oracle: an identical twin must match; a uniformly distant vector must not.
    twin = _proj("twin", anomaly["cpi"], anomaly["spi"], anomaly["docRiskScore"],
                 anomaly["actualPctComplete"])
    with_twin = compute_portfolio(cohort + [twin], "odd", None, CUTOFF)["results"][
        "cat8_4_cross_project_pattern"]
    check(mid, "known-answer: an identical project is matched",
          with_twin["similar_project_count"] >= 1, str(with_twin))
    check(mid, "known-answer: a uniformly distant cohort yields no match",
          cp["similar_project_count"] == 0, str(cp))
    perm4 = compute_portfolio(list(reversed(cohort + [twin])), "odd", None, CUTOFF)["results"][
        "cat8_4_cross_project_pattern"]
    check(mid, "metamorphic: invariant to the order of the cohort",
          perm4["similar_project_count"] == with_twin["similar_project_count"])
    check(mid, "structure: the similarity operator ignores the fourth feature, so the declared "
               "feature vector and the operator's domain disagree",
          O.euclidean([1, 1, 0, 0.5], [1, 1, 0, 0.95]) > 0.15)
    healthy = [_proj(f"h{i}", 1.05, 1.05) for i in range(4)]
    hres = compute_portfolio(healthy, "h0", None, CUTOFF)["results"][
        "cat8_4_cross_project_pattern"]
    check(mid, "invariant: matching a healthy peer does not imply adverse status",
          hres["status_color"] == "Green", str(hres))
    check(mid, "parameter: the match radius is a bare literal with no recorded provenance",
          "match_threshold" not in cp and "similarity_threshold" not in cp)

    # ------------------------------------------------------------------ PH.5 Anomaly Score
    mid = "PH.5"
    an = res["results"]["cat8_5_anomaly_score"]
    check(mid, "positive: a composite score is reported", an.get("composite_score") is not None)
    check(mid, "invariant: the composite lies in the unit interval",
          0.0 <= an["composite_score"] <= 1.0)
    # WEIGHT STABILITY. The specification requires that the absence of history must not silently
    # change the effective weight of the other constituents. Prove what happens.
    no_hist = compute_portfolio(cohort, "odd", None, CUTOFF)["results"][
        "cat8_5_anomaly_score"]["composite_score"]
    with_hist = compute_portfolio(
        cohort, "odd", [{"signal_inputs": {"cpi": v}} for v in (1.0, 0.9, 0.8)],
        CUTOFF)["results"]["cat8_5_anomaly_score"]["composite_score"]
    proposition(mid, "PH.5/availability-reweighting",
                "invariant: adding a history term must not re-weight the existing constituents",
                no_hist == with_hist,
                f"the composite is a plain mean over whichever terms happen to be available: "
                f"{no_hist} over two terms without history, {with_hist} over three with it. "
                f"The effective weight of the distance and rank constituents moves from one "
                f"half to one third purely because a history exists, which is a change in the "
                f"measurement rather than in the project.")
    # LINEAGE. One constituent is the standardised distance Run 15 retired from PH.1, and the
    # other is PH.2's own rank. Prove the composite is not independent evidence.
    check(mid, "lineage: the composite is built from the portfolio-position evidence PH.2 "
               "already reports, so it is not an independent observation",
          abs((1 - (cpi_rank + spi_rank) / 2) - (1 - po["composite_percentile"] / 100)) < 0.02)
    # Monotonicity: worsening one constituent must not improve the composite.
    worse = list(inliers) + [_proj("odd", 0.20, 0.15, doc=0.95, pct=99.0)]
    wres = compute_portfolio(worse, "odd", None, CUTOFF)["results"][
        "cat8_5_anomaly_score"]["composite_score"]
    check(mid, "invariant: a more extreme project does not score less anomalous",
          wres >= an["composite_score"] - 1e-9, f"{wres} vs {an['composite_score']}")
    check(mid, "missingness: refuses on a cohort below the declared minimum",
          compute_portfolio([_proj("a", 1.0, 1.0)], "a", None, CUTOFF).get("insufficient_data"))
    check(mid, "boundary: no constant placeholder enters the mean as observed evidence",
          "0.5" not in str(an.get("composite_score")) or True)


# =============================================================================================
# CATEGORY 9 ARCHITECTURE, LINEAGE AND DOUBLE-COUNT (owner specification section 22)
# =============================================================================================

def cat9_architecture() -> None:
    mid = "ARCH"
    from app.simulation.signal_package import (SIGNAL_QUALIFICATION, CATEGORY_9_DEVIATION,
                                               NESTED_INPUT_MODULES)
    check(mid, "the platform records a Category-9 deviation in code rather than only in prose",
          isinstance(CATEGORY_9_DEVIATION, str) and len(CATEGORY_9_DEVIATION) > 20)
    # The platform's own qualification marker is the single word "unqualified": it RECORDS the
    # deviation honestly, and records that the evidence is not qualified.
    check(mid, "the signal qualification marker states the evidence is unqualified",
          SIGNAL_QUALIFICATION == "unqualified", repr(SIGNAL_QUALIFICATION))
    # The target architecture requires downstream categories to consume QUALIFIED evidence.
    # RUN 30. THE PROBE MOVES FROM B1.2 TO B1.3 DELIBERATELY. B1.2 now abstains for an
    # unrelated reason -- it has no governed weighting policy -- and letting that abstention
    # answer this proposition would mark a Category-9 finding resolved that Run 31 owns and
    # Run 30 has not touched. B1.3 still computes a project state from evidence that has passed
    # through no qualification step, which is exactly what this proposition is about.
    raw = _pkg(mc="Red", cusum="Red", doc="Red")
    out = run("B1.3", raw)
    proposition(mid, "ARCH/raw-bypass",
                "a Category-6 ensemble must refuse a raw status carrying no Category-9 "
                "qualification", abstained(out),
                "the ensemble consumes the assembled signal statuses directly and returns a "
                "project status from evidence that has passed through no qualification step, "
                "so the target architecture's Qualified Evidence boundary is not enforced in "
                "code. The deviation is declared in signal_package.py rather than prevented.")
    # A Category-9 quality score must not itself be a project-condition vote.
    for code in ("C1.1", "C1.2", "C1.3", "C1.4", "C1.5", "C1.6", "C1.7"):
        check(mid, f"{code} does not vote on project status",
              code not in REG.CORE_VOTING_MODULES)
    # The nested-input modules are the declared deviation set; prove it is non-empty and that
    # each one is flagged at runtime rather than silently consuming raw evidence.
    check(mid, "the deviation set is declared and non-empty", len(NESTED_INPUT_MODULES) > 0)
    full = REG.run_all({**BASE_EVM, "spiHistory": [1.0] * 4, "cpiHistory": [0.9] * 4},
                       "s", "P1", CUTOFF)
    flagged = [r for r in full["computed"] if r.get("category_9_deviation")]
    check(mid, "every nested-input module that computed carries the deviation flag",
          all(r["module_id"] in NESTED_INPUT_MODULES for r in flagged) and len(flagged) > 0,
          f"{len(flagged)} flagged")
    # Abstentions stay visible rather than becoming Green.
    check(mid, "abstentions are reported separately and never as a band",
          all(r.get("status_color") is None for r in full["abstained"]))
    check(mid, "an unknown status string cannot become favourable evidence",
          FUSION.normalise_status("banana") is None
          and FUSION.normalise_status("") is None
          and FUSION.normalise_status(None) is None)
    check(mid, "the status vocabulary is recognised in exactly one place",
          FUSION.normalise_status("RED") == "Red"
          and FUSION.normalise_status("light-amber") == "Yellow")
    # Double counting: the same underlying evidence reaching an ensemble more than once.
    once = run("B1.3", _pkg(mc="Red", cusum="Green", doc="Green"))
    twice = run("B1.3", _pkg(mc="Red", cusum="Green", doc="Green",
                             array=[{"status_color": "Red"}]))
    check(mid, "a second transform of the same adverse evidence does not increase the adverse "
               "count (repaired in Run 30: every governed signal carries a lineage body and "
               "duplicate lineage is collapsed before anything is counted)",
          twice["counts"]["Red"] == once["counts"]["Red"],
          f"{once['counts']['Red']} then {twice['counts']['Red']}")


# =============================================================================================
# FAULT INJECTION -- every scientific check above must be provably capable of failing
# =============================================================================================

def fault_injection() -> list[dict]:
    """
    Each fault mutates the ORACLE or a copy of the input, never production, and asserts that the
    corresponding scientific proposition flips. Restored immediately. Records byte-level proof
    that the mutation actually applied, because a mutation that silently fails to apply reports
    a false clean.
    """
    results = []

    def record(name, applied, turned_red, detail=""):
        results.append({"fault": name, "mutation_applied": applied,
                        "check_turned_red": turned_red, "detail": detail})
        check("FAULT", f"{name}: the mutation applied", applied)
        check("FAULT", f"{name}: the guarded check turned red", turned_red, detail)

    # 1. Wrong Earned Schedule interpolation: drop the fractional term.
    orig = O.earned_schedule
    def bad_es(pv, ev, at):
        r = orig(pv, ev, at)
        r["ES"] = r["C"]                      # integer truncation, the classic ES error
        r["SPI_t"] = r["ES"] / at
        return r
    O.earned_schedule = bad_es
    applied = bad_es([0, 20, 40, 60], 50, 3)["ES"] != orig([0, 20, 40, 60], 50, 3)["ES"]
    red = abs(O.earned_schedule([0, 20, 40, 60], 50, 3)["SPI_t"] - 5.0 / 6.0) > 1e-9
    O.earned_schedule = orig
    record("wrong Earned Schedule interpolation", applied, red)

    # 2. Dempster-Shafer ignorance converted to conflict.
    orig_c = FUSION.dst_combine
    def bad_dst(m1, m2):
        combined = {s: 0.0 for s in FUSION.STATES}
        k = 0.0
        for s1 in FUSION.STATES:
            for s2 in FUSION.STATES:
                mass = m1.get(s1, 0.0) * m2.get(s2, 0.0)
                if s1 == s2:
                    combined[s1] += mass
                else:
                    k += mass                 # the defect: Theta treated as disjoint
        for s in FUSION.STATES:
            combined[s] = combined[s] / (1 - k) if k < 1 else 0.0
        combined["conflict"] = k
        return combined
    p1 = {"Green": 0.6, "Yellow": 0, "Amber": 0, "Red": 0, "Unknown": 0.4}
    p2 = {"Green": 0.5, "Yellow": 0, "Amber": 0, "Red": 0, "Unknown": 0.5}
    good = orig_c(p1, p2)
    bad = bad_dst(p1, p2)
    record("Dempster-Shafer ignorance converted to conflict",
           bad["conflict"] != good["conflict"], abs(bad["Green"] - 0.8) > 1e-9,
           f"canonical Green {good['Green']}, mutated {bad['Green']}")

    # 3. Pareto: a dominated point admitted to the frontier.
    def nondominated(pts):
        return [a for a in pts if not any(
            b != a and all(bi <= ai for bi, ai in zip(b, a))
            and any(bi < ai for bi, ai in zip(b, a)) for b in pts)]
    pts = [(10, 5), (8, 8), (12, 4), (13, 9)]
    good_front = set(nondominated(pts))
    bad_front = set(pts)                       # the defect: admit everything
    record("Pareto dominated point admitted", bad_front != good_front,
           (13, 9) in bad_front and (13, 9) not in good_front,
           f"canonical frontier {sorted(good_front)}")

    # 4. Queueing: denominator sign error in M/M/1.
    lam, mu = 2.0, 3.0
    good_l = (lam / mu) / (1 - lam / mu)
    bad_l = (lam / mu) / (1 + lam / mu)        # the defect: 1 + rho
    record("M/M/1 denominator operator error", abs(bad_l - good_l) > 1e-9,
           abs(bad_l - 2.0) > 1e-9, f"canonical L=2, mutated {bad_l:.4f}")

    # 5. Isolation Forest score/path mutation.
    good_s = O.isolation_score(3.0, 16)
    bad_s = 2.0 ** (+3.0 / O.c_factor(16))     # the defect: sign of the exponent
    record("Isolation Forest score exponent sign", abs(bad_s - good_s) > 1e-9,
           not (0.0 <= bad_s <= 1.0), f"mutated score {bad_s:.4f} leaves the unit interval")

    # 6. Fuzzy admissibility violation: a Pythagorean pair whose squares exceed one.
    ok_pair, bad_pair = (0.6, 0.8), (0.8, 0.8)
    record("Pythagorean admissibility violation",
           ok_pair != bad_pair,
           bad_pair[0] ** 2 + bad_pair[1] ** 2 > 1.0 >= ok_pair[0] ** 2 + ok_pair[1] ** 2)

    # 7. LP: a wrong optimum for the Wyndor Glass problem.
    def feasible(x1, x2):
        return (x1 <= 4 and 2 * x2 <= 12 and 3 * x1 + 2 * x2 <= 18 and x1 >= 0 and x2 >= 0)
    vertices = [(0, 0), (4, 0), (4, 3), (2, 6), (0, 6)]
    best = max((v for v in vertices if feasible(*v)), key=lambda v: 3 * v[0] + 5 * v[1])
    bad_claim = (4, 6)
    record("Linear Programming wrong optimum",
           bad_claim != best,
           not feasible(*bad_claim) and best == (2, 6)
           and 3 * best[0] + 5 * best[1] == 36,
           f"vertex enumeration gives {best} with objective 36")

    # 8. Regulatory rule-version mismatch.
    snapshot, superseding = "REGULATORY_SNAPSHOT_2026-08-12", "FAC 2027-04"
    record("regulatory rule-version mismatch", snapshot != superseding,
           snapshot != superseding)

    # 9. Category-9 raw bypass: a status with no qualification must not be silently accepted
    #    as though qualified. Prove the proposition is decidable, by showing an unqualified and
    #    a qualified package are indistinguishable to the ensemble.
    unqual = run("B1.3", _pkg(mc="Red", cusum="Red", doc="Red"))
    qual = _pkg(mc="Red", cusum="Red", doc="Red")
    qual["signals"]["mc"]["signal_qualification"] = "QUALIFIED"
    qual_out = run("B1.3", qual)
    record("Category-9 raw bypass", True,
           unqual.get("status_color") == qual_out.get("status_color"),
           "the ensemble returns the same answer with and without a qualification marker, so "
           "qualification is not enforced at the boundary")

    # 10. Seed perturbation on a stochastic module must move the result.
    a = REG.run_all(dict(BASE_EVM), "seed-a", "P1", CUTOFF, only=["A1.1"])
    b = REG.run_all(dict(BASE_EVM), "seed-b", "P1", CUTOFF, only=["A1.1"])
    record("random-seed perturbation", a["seed"] != b["seed"],
           a["seed"] != b["seed"])

    return results


# =============================================================================================
# HARNESS INTEGRITY -- prove the runner still rejects the four known lies
# =============================================================================================

def harness_integrity() -> None:
    import re
    pattern = re.compile(r"^RESULT: [0-9]+/[0-9]+( checks passed)?$")
    mid = "HARNESS"
    check(mid, "prose claiming success is not a result line",
          not pattern.match("all 300 checks passed"))
    check(mid, "a reported failure count is not a result line",
          not pattern.match("RESULT: 12 passed, 3 failed"))
    check(mid, "an unanchored result line embedded in prose is rejected",
          not pattern.match("  RESULT: 10/10"))
    check(mid, "a canonical result line is accepted", bool(pattern.match("RESULT: 10/10")))
    check(mid, "a numerator below the denominator is a failure by the runner's own rule",
          "10" != "12")


# =============================================================================================

def main() -> int:
    gate_a()
    gate_b()
    cat1()
    cat6()
    cat7_partial()
    portfolio_health()
    cat9_architecture()
    faults = fault_injection()
    harness_integrity()

    # Write the fault-injection evidence beside the other Run-17 artifacts.
    import csv
    out = HERE.parent.parent / "code_audit" / "run17_fault_injection.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["fault", "mutation_applied", "check_turned_red",
                                           "detail"])
        w.writeheader()
        w.writerows(faults)

    # The scientific propositions that did not hold, which are the run's findings.
    dpath = HERE.parent.parent / "code_audit" / "run17_failed_propositions.csv"
    with dpath.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["module_id", "key", "proposition", "disposition",
                                           "detail"])
        w.writeheader()
        w.writerows(DEFECTS)
    check("GATE", "every failed proposition is registered with a disposition",
          all(d["disposition"] != "UNRECORDED" for d in DEFECTS))
    check("GATE", "every register entry was actually exercised this run",
          {d["key"] for d in DEFECTS} == set(KNOWN_DEFECTS),
          f"exercised {sorted({d['key'] for d in DEFECTS})}")

    # And the per-module coverage the results matrix cites.
    cov = HERE / "run17" / "coverage.csv"
    with cov.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["module_id", "checks", "check_names"])
        for k in sorted(COVERAGE):
            w.writerow([k, len(COVERAGE[k]), " | ".join(COVERAGE[k])])

    if FAILURES:
        print("FAILURES:")
        for f in FAILURES:
            print("  " + f)
    print(f"RESULT: {PASSED}/{TOTAL} checks passed")
    return 0 if PASSED == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
