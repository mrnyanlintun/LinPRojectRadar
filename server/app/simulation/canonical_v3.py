"""
THE v3 CANONICAL METHOD LAYER FOR CATEGORIES 1, 2 AND 3.

WHY THIS FILE EXISTS. The supervisory method contract supplied for Run 28 states, for each of
the twenty-eight remaining Category 1 to 3 targets, the canonical method that module is named
for, the data structure that method is defined on, and a hand-checkable known answer. Run 27
established that most of those modules were computing a transparent proxy because the defining
structure was not in the platform at all. This file supplies the structures and the canonical
arithmetic, and the module runners in models.py, models_evm.py and models_ext.py call into it.

THE RULES THIS FILE ENFORCES.

1. A canonical method computes ONLY from its defining structure. When the structure is absent
   the caller ABSTAINS -- Not Estimable -- and reports no substitute figure. There is no proxy
   fallback anywhere below.
2. NO BAND IS INVENTED. Every function here returns numbers and nothing else. Where the v3
   quantity is not the same quantity the v2 band was drawn over, the caller emits the number
   with calibration pending and asserts no colour. Run 33 owns calibration.
3. NOTHING HERE READS A FILE, A CLOCK OR A DATABASE. Every structure arrives on the caller's
   signal inputs, exactly as every scalar does, so no operational path can reach a fixture.
4. NOTHING HERE IS DERIVED FROM THE v2 IMPLEMENTATION. Each function was written from the
   supplied contract; the oracles in server/tools/test_run28_canonical_oracles.py carry the
   contract's own numbers, not numbers read back out of this file.
5. PROVENANCE TRAVELS. Every structure carries the source of its own figures and every result
   carries it back out, because Run 31 implements the Category-9 qualification gate over these
   same rows and cannot qualify what has no lineage. Run 28 does not close a LINEAGE finding.

THE STRUCTURE CONTRACT is a plain dictionary on the signal inputs under the key named in
V3_STRUCTURE_KEYS, the same shape canonical.py already uses for the six v2 structures, so an
absent structure is the ordinary absent-input case rather than a special one.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Sequence

from .canonical import StructureAbsent
from .rng import num

# =================================================================================================
# THE GOVERNED v3 STRUCTURES.
#
# One structure per shared need, not one per module: the schedule network serves five Category-2
# methods, the time-phased baseline serves Earned Schedule and the S-curve, the reference class
# serves both the shrinkage forecast and reference class forecasting. That is the point of
# building structures rather than twenty-eight one-off patches.
# =================================================================================================

#: Module id -> the signal-inputs key carrying its defining v3 structure.
V3_STRUCTURE_KEYS: dict[str, str] = {
    "A1.1": "costDriverDistributions",
    "A1.3": "bayesianEacModel",
    "A1.4": "kalmanStateSpaceModel",
    "A1.6": "timePhasedBaseline",
    "A1.9": "expenditureBaseline",
    "A1.10": "cpiReferenceClass",
    "A1.11": "independentEacPair",
    "A2.1": "scheduleNetwork",
    "A2.4": "scheduleNetwork",
    "A2.5": "scheduleNetwork",
    "A2.6": "timePhasedBaseline",
    "A2.7": "milestoneForecastHistory",
    "A2.8": "lookAheadSchedule",
    "A2.9": "resourceProfile",
    "A2.10": "scheduleNetwork",
    "A2.11": "scheduleNetwork",
    "A3.1": "referenceClassPopulation",
    "A3.3": "productionOutputRecord",
    "A3.5": "overheadAllocationBase",
    "A3.6": "costRiskModel",
    "A3.7": "analogEstimate",
    "A3.8": "parametricCostModel",
    "A3.9": "externalCostIndex",
}

#: The plain words for what each structure IS. These reach a reader in the abstention sentence,
#: so they carry no module id, no key name and no reason code, per the naming rules.
V3_STRUCTURE_WORDS: dict[str, str] = {
    "A1.1": "a declared set of uncertain cost drivers, each with the distribution it is believed "
            "to follow and where those figures came from",
    "A1.3": "a stated prior for the cost at completion, with its source, and a stated "
            "observation model with the uncertainty of the observation",
    "A1.4": "a state space model for the schedule index: a starting estimate, its uncertainty, "
            "the process and measurement variances, and the readings taken",
    "A1.6": "a time phased baseline: the cumulative value of work planned to be complete at the "
            "end of each period",
    "A1.9": "an approved time phased expenditure baseline: the amount planned to be spent by the "
            "end of each period",
    "A1.10": "a governed reference population of comparable projects with the cost performance "
             "they achieved, and the weight to place on this project's own reading",
    "A1.11": "two separately prepared forecasts of the cost at completion, one from the project "
             "management team and one prepared independently of it",
    "A2.1": "the project's activity network: the activities, the logic between them, and a "
            "duration for each",
    "A2.4": "the project's activity network: the activities, the logic between them, and a "
            "duration for each",
    "A2.5": "the project's activity network: the activities, the logic between them, and a "
            "duration for each",
    "A2.6": "a time phased baseline: the cumulative value of work planned to be complete at the "
            "end of each period",
    "A2.7": "a milestone forecast history: each milestone's committed date and the date it was "
            "forecast for in each reporting period since",
    "A2.8": "a look ahead schedule: the window it covers, the activities planned in it, and "
            "whether each one still carries an open constraint",
    "A2.9": "a time phased resource profile: for each period and each kind of resource, the "
            "amount of work demanded and the amount available",
    "A2.10": "the project's activity network: the activities, the logic between them, and a "
             "duration for each",
    "A2.11": "the project's activity network: the activities, the logic between them, and a "
             "duration for each",
    "A3.1": "a reference class of completed comparable projects, with the criteria that put them "
            "in it and the overrun each of them finished with",
    "A3.3": "a record of production: the quantity of work installed, the quantity planned, and "
            "the labour hours each of those took",
    "A3.5": "an overhead allocation base: the planned and actual overhead and the planned and "
            "actual amount of the base it is absorbed over",
    "A3.6": "a cost risk model: the base cost components, the risk events that could occur, how "
            "likely each is and what it would cost",
    "A3.7": "an identified analogous project with its cost, why it is comparable, and the "
            "factors that adapt it to this project",
    "A3.8": "a parametric cost model: the drivers, their units, and coefficients fitted to a "
            "named dataset",
    "A3.9": "a named external price index with its authority, geography, base period and the "
            "period being adjusted to",
}


def require_v3_structure(si: dict, module_id: str) -> dict:
    """The v3 structure, or StructureAbsent carrying the sentence the ledger will show."""
    key = V3_STRUCTURE_KEYS[module_id]
    words = V3_STRUCTURE_WORDS[module_id]
    structure = si.get(key)
    if structure is None:
        raise StructureAbsent(
            f"Awaiting {words}. This measure is named for a method that cannot be carried out "
            f"without it, so no reading is reported and no other figure is used in its place.")
    if not isinstance(structure, dict):
        raise StructureAbsent(
            f"The information provided for this project in place of {words} is not in a form "
            f"this measure can read, so no reading is taken from it.")
    return structure


# ------------------------------------------------------------------------------ shared helpers


def _f(container: Any, field: str, words: str) -> float:
    """A finite number from a mapping, or the structure is not usable."""
    v = num((container or {}).get(field), None)
    if v is None or not math.isfinite(v):
        raise StructureAbsent(
            f"The {words} provided for this project is incomplete or carries a figure that is "
            f"not a number, so no reading is taken from it.")
    return float(v)


def _rows(structure: dict, key: str, words: str) -> list[dict]:
    rows = structure.get(key)
    if not isinstance(rows, list) or not rows:
        raise StructureAbsent(
            f"No {words} has been provided for this project, so the method this measure is "
            f"named for cannot be carried out. No substitute reading is reported in its place.")
    for r in rows:
        if not isinstance(r, dict):
            raise StructureAbsent(
                f"The {words} provided for this project is not in a form this measure can read, "
                f"so no reading is taken from it.")
    return rows


def _provenance(structure: dict, words: str, *fields: str) -> dict[str, str]:
    """
    The lineage fields every governed structure must carry, refused when absent.

    A structure with no stated source cannot be qualified by the Category-9 gate Run 31 builds,
    and a result whose inputs cannot be traced is not interpretable later. Absence is refused
    here rather than defaulted, because a blank source silently reads as an unsourced number.
    """
    out: dict[str, str] = {}
    for field in fields:
        value = str(structure.get(field) or "").strip()
        if not value:
            raise StructureAbsent(
                f"The {words} provided for this project does not say where its figures came "
                f"from, so a reading taken from it could not be interpreted later and none is "
                f"taken.")
        out[field] = value
    return out


def empirical_quantile(values: Sequence[float], p: float) -> float:
    """
    THE FROZEN EMPIRICAL QUANTILE CONVENTION for the whole v3 line, stated once here.

    Right-continuous inverse of the empirical distribution function: with the sample sorted
    ascending and n observations, the p quantile is the observation at index ceil(p*n) - 1,
    floored at 0. This is the convention the supplied contract's Cost Risk Analysis oracle
    requires -- a two-point sample {100, 120} each with weight one half has P80 = 120, because
    the empirical distribution function only reaches 0.80 at 120 -- and the same convention is
    therefore used for Reference Class Forecasting and Schedule Risk Analysis so that one
    definition governs every percentile this platform reports.

    It is NOT an interpolating quantile. On the five-point overrun sample of the Reference Class
    oracle {0.00, 0.10, 0.20, 0.30, 0.40} the median is ceil(0.5*5) - 1 = index 2 = 0.20, which
    is also what interpolation gives on an odd sample, so the contract's median oracle is
    satisfied under this convention as well.
    """
    ordered = sorted(float(v) for v in values)
    if not ordered:
        raise StructureAbsent(
            "No observations were provided to take a percentile of, so none is reported.")
    if not (0.0 <= p <= 1.0):
        raise ValueError("a percentile must lie between nought and one")
    idx = max(0, math.ceil(p * len(ordered)) - 1)
    return ordered[min(idx, len(ordered) - 1)]


# =================================================================================================
# CATEGORY 1
# =================================================================================================

# ------------------------------------------------------------ 1.1 Monte Carlo EAC Forecast


def beta_pert_moments(a: float, m: float, b: float, lam: float = 4.0) -> dict[str, float]:
    """
    Beta-PERT moments for the laboratory oracle, with the contract's lambda of 4.

    mean = (a + lambda*m + b) / (lambda + 2). At lambda 4 that is the classical PERT expected
    value (a + 4m + b) / 6, which is the number the supplied contract states for a=80, m=100,
    b=140: 103.333333... The shape parameters that generate a Beta on [a, b] with that mean are
    alpha = 1 + lambda*(m - a)/(b - a) and beta = 1 + lambda*(b - m)/(b - a), and the variance
    follows from the Beta scaled onto the support.
    """
    if not (a <= m <= b):
        raise ValueError("a Beta-PERT needs optimistic <= most likely <= pessimistic")
    if b <= a:
        return {"mean": float(m), "variance": 0.0, "alpha": 1.0, "beta": 1.0}
    mean = (a + lam * m + b) / (lam + 2.0)
    alpha = 1.0 + lam * (m - a) / (b - a)
    beta = 1.0 + lam * (b - m) / (b - a)
    unit_var = alpha * beta / (((alpha + beta) ** 2) * (alpha + beta + 1.0))
    return {"mean": mean, "variance": unit_var * (b - a) ** 2, "alpha": alpha, "beta": beta}


_DECLARED_FAMILIES = ("BETA_PERT", "TRIANGULAR", "UNIFORM", "NORMAL")


def declared_cost_driver_model(structure: dict) -> dict[str, Any]:
    """
    Read and validate a declared cost-driver distribution set. No sampling happens here.

    THE CONTRACT'S REQUIREMENTS, each refused when absent rather than defaulted: explicitly
    declared uncertain variables, a distribution family with its parameters, the provenance of
    those parameters, the dependence structure where one applies, an iteration count and a seed
    so the run is reproducible, and a convergence criterion tied to the reported percentile.
    """
    words = V3_STRUCTURE_WORDS["A1.1"]
    drivers = _rows(structure, "drivers", words)
    meta = _provenance(structure, words, "parameter_source", "model_version")
    declared = []
    for d in drivers:
        family = str(d.get("distribution_family") or "").upper()
        if family not in _DECLARED_FAMILIES:
            raise StructureAbsent(
                "A cost driver provided for this project does not say which distribution its "
                "uncertainty follows, so nothing can be drawn from it and no forecast is made.")
        driver_id = str(d.get("driver_id") or "")
        if not driver_id:
            raise StructureAbsent(
                "A cost driver provided for this project has no identity, so the forecast could "
                "not say which driver it came from and none is made.")
        params = d.get("parameters")
        if not isinstance(params, dict) or not params:
            raise StructureAbsent(
                "A cost driver provided for this project declares a distribution with no "
                "figures for it, so nothing can be drawn from it and no forecast is made.")
        if family in ("BETA_PERT", "TRIANGULAR"):
            a = _f(params, "optimistic", words)
            m = _f(params, "most_likely", words)
            b = _f(params, "pessimistic", words)
            if not (a <= m <= b):
                raise StructureAbsent(
                    "A cost driver provided for this project has an optimistic figure above its "
                    "most likely figure, or a most likely figure above its pessimistic one, so "
                    "the three do not describe one distribution and no forecast is made.")
        elif family == "UNIFORM":
            lo = _f(params, "low", words)
            hi = _f(params, "high", words)
            if hi < lo:
                raise StructureAbsent(
                    "A cost driver provided for this project has an upper bound below its lower "
                    "bound, so the pair does not describe one distribution.")
        else:
            _f(params, "mean", words)
            sd = _f(params, "standard_deviation", words)
            if sd < 0:
                raise StructureAbsent(
                    "A cost driver provided for this project has a spread below zero, which no "
                    "spread can be, so no forecast is made from it.")
        declared.append({"driver_id": driver_id, "family": family, "parameters": dict(params)})
    iterations = int(_f(structure, "iterations", words))
    if iterations < 1000:
        raise StructureAbsent(
            "The declared cost driver set asks for fewer draws than a percentile of the "
            "resulting forecast can be read from, so no forecast is made from it.")
    seed = int(_f(structure, "seed", words))
    tolerance = _f(structure, "convergence_tolerance", words)
    if not tolerance > 0:
        raise StructureAbsent(
            "The declared cost driver set states no tolerance the reported percentile must "
            "settle within, so there is no basis on which to call the forecast converged.")
    correlation = structure.get("correlation_matrix")
    if correlation is not None and not isinstance(correlation, list):
        raise StructureAbsent(
            "The dependence between the cost drivers was provided in a form this measure "
            "cannot read, so no forecast is made from it.")
    return {
        "drivers": declared,
        "driver_count": len(declared),
        "iterations": iterations,
        "seed": seed,
        "convergence_tolerance": tolerance,
        "dependence_declared": correlation is not None,
        **meta,
    }


def monte_carlo_convergence(samples: Sequence[float], p: float,
                            tolerance: float) -> dict[str, Any]:
    """
    Convergence evidence for a reported percentile, which the contract requires and v2 had none of.

    The percentile is recomputed on the first half of the sample and on the whole sample. The
    forecast is called converged when the two agree within the declared tolerance, expressed as a
    fraction of the whole-sample percentile. This is a stated criterion the reader can check, not
    an assertion that the run converged.
    """
    ordered = list(samples)
    if len(ordered) < 2:
        raise StructureAbsent(
            "Too few draws were made for a percentile to be checked for convergence.")
    half = empirical_quantile(ordered[: len(ordered) // 2], p)
    full = empirical_quantile(ordered, p)
    spread = abs(full - half) / abs(full) if full else abs(full - half)
    return {"half_sample": half, "full_sample": full, "relative_movement": spread,
            "tolerance": tolerance, "converged": spread <= tolerance}


# ------------------------------------------------------------ 1.2 CUSUM design record


def cusum_design_record(structure: Any) -> dict[str, Any] | None:
    """
    The Control Chart Design Record, when one is supplied. The frozen design is NOT retuned.

    The supplied contract freezes k = 0.5 sigma and h = 5 sigma and forbids retuning them in
    Run 28, and Run 15's calibration record already selected exactly that design. So this reads
    provenance only: the in-control window the process standard deviation was estimated from, the
    number of observations behind it, and the shift the chart is designed to detect. It changes
    no constant and no boundary. A project with no such record still charts on the frozen design;
    what it does not get is a claim that the design was estimated from its own in-control period.
    """
    if structure is None:
        return None
    if not isinstance(structure, dict):
        raise StructureAbsent(
            "The control chart design provided for this project is not in a form this measure "
            "can read, so no design record is attached to the reading.")
    words = "control chart design"
    meta = _provenance(structure, words, "in_control_window", "sigma_source")
    n = int(_f(structure, "in_control_observations", words))
    if n < 2:
        raise StructureAbsent(
            "The control chart design provided rests on fewer than two observations, so no "
            "process spread can have been estimated from it.")
    return {"in_control_observations": n,
            "target_shift_sigma": _f(structure, "target_shift_sigma", words),
            "k_sigma_multiple": 0.5, "h_sigma_multiple": 5.0,
            "design_frozen_by": "Run 15 calibration record; not retuned in Run 28", **meta}


# ------------------------------------------------------------ 1.3 Bayesian EAC


def normal_normal_posterior(prior_mean: float, prior_var: float,
                            observation: float, observation_var: float) -> dict[str, float]:
    """
    Conjugate normal-normal update. posterior proportional to likelihood times prior.

    Posterior precision is the sum of the precisions:
        1/posterior_var = 1/prior_var + 1/observation_var
    Posterior mean is the precision-weighted average:
        posterior_mean = posterior_var * (prior_mean/prior_var + observation/observation_var)

    The supplied contract's oracle: prior N(100, 100), y = 120, sigma^2 = 100.
        posterior_var  = 1 / (1/100 + 1/100) = 50
        posterior_mean = 50 * (100/100 + 120/100) = 50 * 2.2 = 110.
    The 95 per cent credible interval is the posterior mean plus and minus 1.959963985 posterior
    standard deviations, which is the normal quantile, not a fitted band.
    """
    if not (prior_var > 0 and observation_var > 0):
        raise StructureAbsent(
            "A variance of zero or below was stated for the prior or the observation, and no "
            "belief can be updated on one, so no posterior is reported.")
    posterior_var = 1.0 / (1.0 / prior_var + 1.0 / observation_var)
    posterior_mean = posterior_var * (prior_mean / prior_var + observation / observation_var)
    sd = math.sqrt(posterior_var)
    z = 1.959963985
    return {"posterior_mean": posterior_mean, "posterior_variance": posterior_var,
            "posterior_sd": sd,
            "credible_low": posterior_mean - z * sd, "credible_high": posterior_mean + z * sd,
            "credible_mass": 0.95}


def bayesian_eac_model(structure: dict) -> dict[str, Any]:
    """The governed Bayesian model record, refusing anything it does not state."""
    words = V3_STRUCTURE_WORDS["A1.3"]
    prior = structure.get("prior")
    likelihood = structure.get("likelihood")
    if not isinstance(prior, dict) or not isinstance(likelihood, dict):
        raise StructureAbsent(
            "The Bayesian model provided for this project does not state both a prior belief "
            "and an observation model, so no belief can be updated and none is reported.")
    _provenance(prior, words, "source")
    _provenance(likelihood, words, "source")
    parameter = str(structure.get("parameter") or "").strip()
    if not parameter:
        raise StructureAbsent(
            "The Bayesian model provided for this project does not say which quantity it is "
            "estimating, so no posterior for it is reported.")
    out = normal_normal_posterior(
        _f(prior, "mean", words), _f(prior, "variance", words),
        _f(likelihood, "observation", words), _f(likelihood, "variance", words))
    out.update({
        "parameter": parameter,
        "prior_mean": _f(prior, "mean", words),
        "prior_variance": _f(prior, "variance", words),
        "prior_source": str(prior.get("source")),
        "observation": _f(likelihood, "observation", words),
        "observation_variance": _f(likelihood, "variance", words),
        "observation_model": str(likelihood.get("source")),
        "variance_basis": str(likelihood.get("variance_basis") or likelihood.get("source")),
    })
    return out


# ------------------------------------------------------------ 1.4 Kalman filter


def kalman_scalar_step(x_prev: float, p_prev: float, q: float, r: float,
                       z: float) -> dict[str, float]:
    """
    One step of the scalar random-walk Kalman recursion, exactly as the contract states it.

        x_pred = x_prev
        P_pred = P_prev + Q
        K      = P_pred / (P_pred + R)
        x_post = x_pred + K * (z - x_pred)
        P_post = (1 - K) * P_pred

    Oracle: x0 = 1, P0 = 1, Q = 0, R = 1, z1 = 2 gives P_pred = 1, K = 0.5, x1 = 1.5, P1 = 0.5.
    """
    if q < 0 or r <= 0:
        raise StructureAbsent(
            "The state space model provided has a process variance below zero or a measurement "
            "variance of zero or below, and no filter can run on either, so no smoothed reading "
            "is reported.")
    x_pred = x_prev
    p_pred = p_prev + q
    k = p_pred / (p_pred + r)
    return {"x_pred": x_pred, "p_pred": p_pred, "gain": k,
            "x_post": x_pred + k * (z - x_pred), "p_post": (1.0 - k) * p_pred}


def kalman_filter_run(x0: float, p0: float, q: float, r: float,
                      observations: Sequence[float]) -> dict[str, Any]:
    """The full recursion over a series, carrying every gain so the run is hand-checkable."""
    if not observations:
        raise StructureAbsent(
            "No readings were provided for the state space model to filter, so no smoothed "
            "reading is reported.")
    x, p = float(x0), float(p0)
    if p < 0:
        raise StructureAbsent(
            "The state space model provided states a starting uncertainty below zero, which no "
            "variance can be, so no smoothed reading is reported.")
    gains, path = [], []
    for z in observations:
        step = kalman_scalar_step(x, p, q, r, float(z))
        x, p = step["x_post"], step["p_post"]
        gains.append(step["gain"])
        path.append(x)
    return {"x_post": x, "p_post": p, "gains": gains, "path": path,
            "observations": len(observations),
            "innovation_last": float(observations[-1]) - path[-2] if len(path) > 1 else None}


def kalman_state_space_model(structure: dict) -> dict[str, Any]:
    """The governed state-space record: Q and R must state where they came from."""
    words = V3_STRUCTURE_WORDS["A1.4"]
    meta = _provenance(structure, words, "process_variance_source", "measurement_variance_source")
    observations = structure.get("observations")
    if not isinstance(observations, list) or len(observations) < 1:
        raise StructureAbsent(
            "The state space model provided carries no readings to filter, so no smoothed "
            "reading is reported.")
    series = []
    for v in observations:
        value = num(v, None)
        if value is None or not math.isfinite(value):
            raise StructureAbsent(
                "A reading in the state space model provided is not a number, so the series is "
                "not filterable and no smoothed reading is reported.")
        series.append(float(value))
    run = kalman_filter_run(_f(structure, "initial_state", words),
                            _f(structure, "initial_variance", words),
                            _f(structure, "process_variance", words),
                            _f(structure, "measurement_variance", words), series)
    run.update({"process_variance": _f(structure, "process_variance", words),
                "measurement_variance": _f(structure, "measurement_variance", words), **meta})
    return run


# ------------------------------------------------------------ 1.5 ARIMA


def _ols(design: list[list[float]], y: list[float]) -> list[float] | None:
    """Ordinary least squares by Gaussian elimination on the normal equations. None if singular."""
    k = len(design[0])
    xtx = [[sum(row[i] * row[j] for row in design) for j in range(k)] for i in range(k)]
    xty = [sum(row[i] * yi for row, yi in zip(design, y)) for i in range(k)]
    for i in range(k):
        pivot = max(range(i, k), key=lambda r: abs(xtx[r][i]))
        if abs(xtx[pivot][i]) < 1e-12:
            return None
        xtx[i], xtx[pivot] = xtx[pivot], xtx[i]
        xty[i], xty[pivot] = xty[pivot], xty[i]
        for r in range(i + 1, k):
            factor = xtx[r][i] / xtx[i][i]
            for c in range(i, k):
                xtx[r][c] -= factor * xtx[i][c]
            xty[r] -= factor * xty[i]
    beta = [0.0] * k
    for i in range(k - 1, -1, -1):
        beta[i] = (xty[i] - sum(xtx[i][j] * beta[j] for j in range(i + 1, k))) / xtx[i][i]
    return beta


def _difference(series: Sequence[float], d: int) -> list[float]:
    out = list(series)
    for _ in range(d):
        out = [out[i] - out[i - 1] for i in range(1, len(out))]
    return out


def arima_one_step(series: Sequence[float], p: int, d: int, q: int,
                   phi: Sequence[float], theta: Sequence[float],
                   c: float = 0.0) -> float:
    """
    One-step-ahead forecast from a SUPPLIED fixed ARIMA(p,d,q) model, hand-checkable.

    The differenced series w_t = (1-B)^d y_t is modelled as
        w_t = c + sum_i phi_i w_(t-i) + e_t + sum_j theta_j e_(t-j).
    Residuals are recovered by running the model forward over the observed differences with
    e_t = w_t - fitted_t, then the one-step forecast of w is
        w_hat = c + sum_i phi_i w_(n+1-i) + sum_j theta_j e_(n+1-j),
    and the forecast of y is w_hat re-integrated d times onto the last observed levels.
    """
    w = _difference(series, d)
    if len(w) < max(p, q) + 1:
        raise StructureAbsent(
            "The cost performance history is too short for the model stated to be run over it, "
            "so no forecast is reported.")
    errors: list[float] = []
    for t in range(len(w)):
        fitted = c
        for i in range(p):
            fitted += phi[i] * (w[t - 1 - i] if t - 1 - i >= 0 else 0.0)
        for j in range(q):
            fitted += theta[j] * (errors[t - 1 - j] if t - 1 - j >= 0 else 0.0)
        errors.append(w[t] - fitted)
    w_hat = c
    for i in range(p):
        w_hat += phi[i] * w[len(w) - 1 - i]
    for j in range(q):
        w_hat += theta[j] * errors[len(errors) - 1 - j]
    level = w_hat
    tail = list(series)
    for _ in range(d):
        level = level + tail[-1]
        tail = _difference(series, 0)
    return level


def identify_arima(series: Sequence[float], max_p: int = 2, max_q: int = 1,
                   min_history: int = 8) -> dict[str, Any]:
    """
    A genuine identification, estimation and diagnostic workflow, not an AR(1) under an ARIMA name.

    d is chosen by a VARIANCE REDUCTION RULE, stated here rather than assumed: the series is
    differenced once when the variance of its first differences is strictly below the variance of
    the series itself, which is the condition under which differencing removes rather than adds
    structure, and it holds exactly when the lag-one autocorrelation exceeds one half. A cost
    performance index is a bounded ratio, so the differencing budget is one and d above one is
    not entertained. A deterministic ramp differences to a constant under this rule, where a
    lag-one autocorrelation threshold would have left it undifferenced and then rejected the
    resulting near-unit-root fit as non-stationary.

    Candidate (p, q) pairs up to the stated maxima are estimated by conditional least squares on
    the differenced series -- the AR terms by ordinary least squares, the MA terms by iterating
    the residual recursion -- and the model is SELECTED by AICc, which is the small-sample
    correction and is the right criterion for the short histories this platform holds:
        AICc = n*ln(SSE/n) + 2k + 2k(k+1)/(n-k-1).
    Parsimony therefore wins on short series by construction rather than by preference.

    Residual diagnostics are reported, not asserted: the Ljung-Box statistic at lag one and the
    residual lag-one autocorrelation travel with the result so a reader can see whether the
    residuals still carry structure.

    Below min_history observations this raises: NOT ESTIMABLE. Non-finite or non-positive
    readings raise for the same reason -- a cost performance index cannot be zero or below.
    """
    values = []
    for v in series or ():
        value = num(v, None)
        if value is None or not math.isfinite(value):
            raise StructureAbsent(
                "The cost performance history carries a reading that is not a number, so the "
                "series is not forecastable and no forecast is reported.")
        values.append(float(value))
    if len(values) < min_history:
        raise StructureAbsent(
            "The cost performance history is too short for a time series model to be identified "
            "from it, so no forecast is reported and no shorter substitute is used.")
    if any(v <= 0 for v in values):
        raise StructureAbsent(
            "The cost performance history contains a reading of zero or below, which no cost "
            "performance index can be, so the series is not forecastable.")

    def acf1(x: Sequence[float]) -> float:
        n = len(x)
        if n < 3:
            return 0.0
        mean = sum(x) / n
        den = sum((v - mean) ** 2 for v in x)
        if den <= 0:
            return 0.0
        return sum((x[i] - mean) * (x[i - 1] - mean) for i in range(1, n)) / den

    def variance(x: Sequence[float]) -> float:
        if len(x) < 2:
            return 0.0
        mean = sum(x) / len(x)
        return sum((v - mean) ** 2 for v in x) / (len(x) - 1)

    d = 0
    work = list(values)
    if len(work) > 3 and variance(_difference(work, 1)) < variance(work):
        work = _difference(work, 1)
        d = 1
    if all(abs(v - work[0]) < 1e-12 for v in work):
        # A constant series after differencing: the parsimonious model is a drift-free
        # random walk or a constant mean, and it is reported as such rather than fitted.
        return {"p": 0, "d": d, "q": 0, "phi": [], "theta": [], "c": (work[0] if d == 0 else 0.0),
                "aicc": float("-inf"), "n": len(work), "constant_series": True,
                "residual_acf1": 0.0, "ljung_box_lag1": 0.0,
                "sigma2": 0.0, "history": len(values),
                "forecast": values[-1] + (work[0] if d == 1 else 0.0)}

    best: dict[str, Any] | None = None
    for p in range(0, max_p + 1):
        for q in range(0, max_q + 1):
            fit = _fit_arma(work, p, q)
            if fit is None:
                continue
            n = fit["n"]
            k = p + q + 1
            if n - k - 1 <= 0 or fit["sse"] <= 0:
                continue
            aic = n * math.log(fit["sse"] / n) + 2 * k
            aicc = aic + (2 * k * (k + 1)) / (n - k - 1)
            fit.update({"p": p, "q": q, "aicc": aicc})
            if best is None or aicc < best["aicc"] - 1e-12:
                best = fit
    if best is None:
        raise StructureAbsent(
            "No time series model could be estimated from the cost performance history "
            "supplied, so no forecast is reported.")

    # Stationarity and invertibility, on the first-order cases the short histories admit.
    phi, theta = best["phi"], best["theta"]
    if best["p"] == 1 and abs(phi[0]) >= 1.0:
        raise StructureAbsent(
            "The model identified from the cost performance history is not stationary, so a "
            "forecast from it would not be interpretable and none is reported.")
    if best["q"] == 1 and abs(theta[0]) >= 1.0:
        raise StructureAbsent(
            "The model identified from the cost performance history is not invertible, so a "
            "forecast from it would not be interpretable and none is reported.")

    residuals = best["residuals"]
    n = len(residuals)
    r1 = acf1(residuals)
    ljung = n * (n + 2) * (r1 ** 2) / (n - 1) if n > 1 else 0.0
    w_hat = best["c"]
    for i in range(best["p"]):
        w_hat += phi[i] * best["w"][-1 - i]
    for j in range(best["q"]):
        w_hat += theta[j] * residuals[-1 - j]
    forecast = w_hat + values[-1] if d == 1 else w_hat
    sigma2 = best["sse"] / max(1, n - best["p"] - best["q"] - 1)
    half = 1.959963985 * math.sqrt(sigma2)
    return {"p": best["p"], "d": d, "q": best["q"], "phi": list(phi), "theta": list(theta),
            "c": best["c"], "aicc": best["aicc"], "n": n, "constant_series": False,
            "residual_acf1": r1, "ljung_box_lag1": ljung, "sigma2": sigma2,
            "history": len(values), "forecast": forecast,
            "interval_low": forecast - half, "interval_high": forecast + half,
            "interval_mass": 0.95}


def _fit_arma(w: Sequence[float], p: int, q: int) -> dict[str, Any] | None:
    """Conditional least squares for ARMA(p, q) with an intercept, iterating on the residuals."""
    start = max(p, 1)
    if len(w) - start < p + q + 2:
        return None
    errors = [0.0] * len(w)
    beta: list[float] | None = None
    for _ in range(25):
        design, y = [], []
        for t in range(start, len(w)):
            row = [1.0]
            row += [w[t - 1 - i] for i in range(p)]
            row += [errors[t - 1 - j] for j in range(q)]
            design.append(row)
            y.append(w[t])
        beta = _ols(design, y)
        if beta is None:
            return None
        new_errors = list(errors)
        for idx, t in enumerate(range(start, len(w))):
            fitted = sum(b * v for b, v in zip(beta, design[idx]))
            new_errors[t] = w[t] - fitted
        if max(abs(a - b) for a, b in zip(errors, new_errors)) < 1e-12:
            errors = new_errors
            break
        errors = new_errors
    if beta is None:
        return None
    residuals = [errors[t] for t in range(start, len(w))]
    return {"c": beta[0], "phi": beta[1:1 + p], "theta": beta[1 + p:],
            "residuals": residuals, "sse": sum(e * e for e in residuals),
            "n": len(residuals), "w": list(w)}


# ------------------------------------------------------------ 1.6 Earned Schedule


def earned_schedule(cumulative_pv: Sequence[float], ev: float, at: float) -> dict[str, Any]:
    """
    Earned Schedule by interpolation on the cumulative time-phased planned value curve.

    Find C, the last period whose cumulative PV is at or below EV, then
        ES     = C + (EV - PV_C) / (PV_(C+1) - PV_C)
        SV(t)  = ES - AT
        SPI(t) = ES / AT.

    Oracle: PV = [0, 20, 40, 60] indexed from period 0, EV = 50, AT = 3.
        PV_2 = 40 <= 50 < 60 = PV_3, so C = 2
        ES     = 2 + (50-40)/(60-40) = 2.5
        SV(t)  = 2.5 - 3 = -0.5
        SPI(t) = 2.5 / 3 = 0.8333333333.

    Actual percent complete over planned percent complete is NOT Earned Schedule and is not
    computed anywhere here. Without the cumulative curve this raises: NOT ESTIMABLE.
    """
    pv = [float(num(v, None)) if num(v, None) is not None else None for v in (cumulative_pv or ())]
    if len(pv) < 2 or any(v is None or not math.isfinite(v) for v in pv):
        raise StructureAbsent(
            "The time phased baseline provided does not carry a cumulative planned value for at "
            "least two periods, so there is no curve to place the work performed on.")
    if any(pv[i] < pv[i - 1] for i in range(1, len(pv))):
        raise StructureAbsent(
            "The time phased baseline provided falls over time, and a cumulative planned value "
            "cannot decrease, so no schedule position is read from it.")
    if at is None or not math.isfinite(at) or at <= 0:
        raise StructureAbsent(
            "No actual time elapsed above zero was provided, so no time based schedule index "
            "can be formed.")
    if ev is None or not math.isfinite(ev) or ev < 0:
        raise StructureAbsent(
            "The value of work performed was not provided as a figure at or above zero, so it "
            "cannot be placed on the planned value curve.")
    if ev < pv[0]:
        return {"earned_schedule": 0.0, "period_index": 0, "actual_time": float(at),
                "schedule_variance_time": 0.0 - float(at), "spi_time": 0.0,
                "at_or_beyond_curve": False, "periods": len(pv)}
    if ev >= pv[-1]:
        # The curve is fully earned: earned schedule is the last period on it. Interpolating
        # beyond the curve would invent planned value that the baseline does not contain.
        es = float(len(pv) - 1)
        return {"earned_schedule": es, "period_index": len(pv) - 1, "actual_time": float(at),
                "schedule_variance_time": es - float(at), "spi_time": es / float(at),
                "at_or_beyond_curve": True, "periods": len(pv)}
    c = max(i for i in range(len(pv) - 1) if pv[i] <= ev)
    span = pv[c + 1] - pv[c]
    fraction = 0.0 if span <= 0 else (ev - pv[c]) / span
    es = c + fraction
    return {"earned_schedule": es, "period_index": c, "interpolated_fraction": fraction,
            "actual_time": float(at), "schedule_variance_time": es - float(at),
            "spi_time": es / float(at), "at_or_beyond_curve": False, "periods": len(pv)}


def time_phased_baseline(structure: dict, value_field: str = "cumulative_pv") -> dict[str, Any]:
    """The governed time-phased baseline: cumulative planned value by period, with provenance."""
    words = V3_STRUCTURE_WORDS["A1.6"]
    periods = _rows(structure, "periods", words)
    meta = _provenance(structure, words, "baseline_version", "approval_source")
    ordered = sorted(periods, key=lambda r: _f(r, "period_index", words))
    curve = [_f(r, value_field, words) for r in ordered]
    return {"curve": curve, "period_labels": [str(r.get("period") or "") for r in ordered],
            "periods": len(curve), **meta}


# ------------------------------------------------------------ 1.9 Budget Execution Rate


def budget_execution(expected_spend: float, ac: float) -> dict[str, float]:
    """
    ExecutionRatio(t) = AC(t) / ExpectedSpend(t), and ExecutionDeviation(t) = ratio - 1.

    Oracle: ExpectedSpend = 50, AC = 60 gives 1.20 and +0.20. ExpectedSpend must come from an
    approved time-phased expenditure baseline; manufacturing it from BAC times a generic percent
    complete is explicitly not this method and is not done anywhere here.
    """
    if not (expected_spend is not None and math.isfinite(expected_spend) and expected_spend > 0):
        raise StructureAbsent(
            "The approved expenditure baseline provides no amount planned to have been spent by "
            "this point above zero, so no execution ratio can be formed.")
    if ac is None or not math.isfinite(ac) or ac < 0:
        raise StructureAbsent(
            "The actual cost was not provided as an amount at or above zero, so no execution "
            "ratio is measurable.")
    ratio = ac / expected_spend
    return {"execution_ratio": ratio, "execution_deviation": ratio - 1.0,
            "expected_spend": float(expected_spend), "actual_cost": float(ac)}


def expenditure_baseline_to_date(structure: dict, period_index: float) -> dict[str, Any]:
    """The approved expenditure profile, read at the governed status period."""
    words = V3_STRUCTURE_WORDS["A1.9"]
    periods = _rows(structure, "periods", words)
    meta = _provenance(structure, words, "baseline_version", "approval_source")
    ordered = sorted(periods, key=lambda r: _f(r, "period_index", words))
    at = None
    for row in ordered:
        if _f(row, "period_index", words) <= period_index:
            at = _f(row, "expected_spend", words)
    if at is None:
        raise StructureAbsent(
            "The approved expenditure baseline provided does not reach the period being "
            "reported, so it states no amount planned to have been spent by this point.")
    return {"expected_spend": at, "periods": len(ordered), **meta}


# ------------------------------------------------------------ 1.10 CPI Shrinkage Forecast


def cpi_shrinkage(cpi_project: float, mu_reference: float, weight: float) -> dict[str, float]:
    """
    Partial pooling toward a governed reference-class expectation.

        CPI_shrunk = w * CPI_project + (1 - w) * mu_reference,   0 <= w <= 1.

    Oracle: 0.60 * 0.80 + 0.40 * 1.00 = 0.48 + 0.40 = 0.88.

    THIS IS NOT AN ASSUMPTION THAT COST PERFORMANCE REGRESSES TOWARD ONE. mu_reference is the
    reference population's mean, whatever it is; the coincidence that a reference mean can equal
    1.00 is a property of that population, not of the estimator. A hard-coded weight is refused:
    the weight must be estimated and must say how.
    """
    for value, what in ((cpi_project, "this project's cost performance"),
                        (mu_reference, "the reference population's cost performance"),
                        (weight, "the weight placed on this project's own reading")):
        if value is None or not math.isfinite(value):
            raise StructureAbsent(
                f"No figure was provided for {what}, so no pooled forecast is reported.")
    if not (0.0 <= weight <= 1.0):
        raise StructureAbsent(
            "The weight placed on this project's own reading falls outside nought to one, so it "
            "is not a share and no pooled forecast is formed from it.")
    return {"cpi_shrunk": weight * cpi_project + (1.0 - weight) * mu_reference,
            "weight": float(weight), "cpi_project": float(cpi_project),
            "mu_reference": float(mu_reference)}


def cpi_reference_class(structure: dict) -> dict[str, Any]:
    """The governed reference population and the estimated shrinkage weight, with provenance."""
    words = V3_STRUCTURE_WORDS["A1.10"]
    members = _rows(structure, "members", words)
    meta = _provenance(structure, words, "class_membership_basis", "weight_estimation_method",
                       "data_vintage")
    readings = [_f(m, "cpi_outcome", words) for m in members]
    if len(readings) < 2:
        raise StructureAbsent(
            "The reference population provided holds fewer than two comparable projects, so it "
            "has no spread for a pooled forecast to be drawn toward.")
    ids = {str(m.get("reference_project_id") or "") for m in members}
    if "" in ids:
        raise StructureAbsent(
            "A project in the reference population provided has no identity, so the population "
            "cannot be audited and no pooled forecast is drawn toward it.")
    evaluated = str(structure.get("evaluated_project_id") or "")
    if evaluated and evaluated in ids:
        raise StructureAbsent(
            "The project being assessed is itself part of the reference population it would be "
            "pooled toward, so the comparison would be of the project with itself.")
    weight = _f(structure, "shrinkage_weight", words)
    if str(structure.get("weight_estimation_method")).strip().upper() in ("HARD_CODED", "FIXED"):
        raise StructureAbsent(
            "The weight placed on this project's own reading was fixed in advance rather than "
            "estimated, so no pooled forecast is reported from it.")
    mean = sum(readings) / len(readings)
    var = sum((v - mean) ** 2 for v in readings) / (len(readings) - 1)
    return {"mu_reference": mean, "reference_variance": var, "members": len(readings),
            "shrinkage_weight": weight, "project_stage": str(structure.get("project_stage") or ""),
            **meta}


# ------------------------------------------------------------ 1.11 Independent EAC Reconciliation


#: The lineage fields that must DIFFER between the two forecasts before either may be called
#: independent of the other. Two transformations of one BAC/CPI/EV/AC vector share all of them.
_IER_LINEAGE_FIELDS = ("source", "method", "assumptions", "model_version", "responsible_party")


def independent_eac_reconciliation(management: dict, independent: dict) -> dict[str, Any]:
    """
    IER = IndependentEAC / ManagementEAC, Divergence = (Independent - Management) / Management.

    Oracle: 120 / 100 = 1.20 and (120 - 100) / 100 = 0.20.

    INDEPENDENCE IS CHECKED, NOT ASSERTED. Both forecasts must state source, method,
    assumptions, model version and responsible party, and the two must differ on the method AND
    on the responsible party. Two transformations of the same evidence vector prepared by the
    same party are not two estimates, and the module refuses rather than reporting a ratio that
    would read as corroboration.
    """
    words = V3_STRUCTURE_WORDS["A1.11"]
    for side, label in ((management, "management"), (independent, "independent")):
        if not isinstance(side, dict):
            raise StructureAbsent(
                "Two separately prepared forecasts of the cost at completion were not provided, "
                "so there is nothing to reconcile and no reading is reported.")
        _provenance(side, words, *_IER_LINEAGE_FIELDS)
    m = _f(management, "eac", words)
    i = _f(independent, "eac", words)
    if not m > 0:
        raise StructureAbsent(
            "The management forecast of the cost at completion is zero or below, and no "
            "reconciliation can be measured against it.")
    if str(management.get("method")).strip().lower() == \
            str(independent.get("method")).strip().lower():
        raise StructureAbsent(
            "The two forecasts of the cost at completion were prepared by the same method, so "
            "they are two transformations of one estimate rather than two estimates, and no "
            "reconciliation between them is reported.")
    if str(management.get("responsible_party")).strip().lower() == \
            str(independent.get("responsible_party")).strip().lower():
        raise StructureAbsent(
            "The two forecasts of the cost at completion were prepared by the same party, so "
            "the second is not independent of the first and no reconciliation is reported.")
    return {"ier": i / m, "divergence": (i - m) / m,
            "management_eac": m, "independent_eac": i,
            "management_lineage": {f: str(management.get(f)) for f in _IER_LINEAGE_FIELDS},
            "independent_lineage": {f: str(independent.get(f)) for f in _IER_LINEAGE_FIELDS}}


# =================================================================================================
# CATEGORY 2 -- ALL FIVE NETWORK METHODS READ ONE GOVERNED SCHEDULE NETWORK.
# =================================================================================================


def parse_schedule_network(structure: dict) -> dict[str, Any]:
    """
    The governed activity network: identities, logic, durations, and the status basis.

    Refused when: no activities, a duplicate identity, a predecessor that names no activity in
    the network, a negative duration, or a cycle in the logic. A network with a cycle has no
    forward pass, so there is nothing to compute and nothing is reported.
    """
    words = V3_STRUCTURE_WORDS["A2.1"]
    rows = _rows(structure, "activities", words)
    meta = _provenance(structure, words, "schedule_version", "status_basis")
    activities: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for r in rows:
        aid = str(r.get("activity_id") or "")
        if not aid:
            raise StructureAbsent(
                "An activity in the schedule network provided has no identity, so the logic "
                "between the activities cannot be followed and no reading is taken.")
        if aid in activities:
            raise StructureAbsent(
                "The schedule network provided names one activity twice, so the logic between "
                "the activities is ambiguous and no reading is taken.")
        duration = _f(r, "current_duration", words)
        if duration < 0:
            raise StructureAbsent(
                "An activity in the schedule network provided has a duration below zero, which "
                "no duration can be, so no reading is taken.")
        preds = r.get("predecessors") or []
        if not isinstance(preds, list):
            raise StructureAbsent(
                "An activity in the schedule network provided states its predecessors in a form "
                "this measure cannot read, so no reading is taken.")
        activities[aid] = {
            "activity_id": aid,
            "predecessors": [str(p) for p in preds],
            "current_duration": duration,
            "baseline_duration": (num(r.get("baseline_duration"), None)
                                  if r.get("baseline_duration") is not None else None),
            "remaining_duration": (num(r.get("remaining_duration"), None)
                                   if r.get("remaining_duration") is not None else None),
            "baseline_total_float": (num(r.get("baseline_total_float"), None)
                                     if r.get("baseline_total_float") is not None else None),
            "calendar": str(r.get("calendar") or ""),
            "optimistic": num(r.get("optimistic_duration"), None),
            "most_likely": num(r.get("most_likely_duration"), None),
            "pessimistic": num(r.get("pessimistic_duration"), None),
            # RUN 28. The supplied contract's laboratory oracle for Schedule Risk Analysis is a
            # single activity distributed Uniform(0, 10) with a true P80 of 8, so the network
            # must be able to carry a declared distribution family rather than assuming every
            # activity is triangular on its three-point estimate. TRIANGULAR is the default
            # because a three-point estimate is what a schedule normally supplies; UNIFORM draws
            # flat between the optimistic and pessimistic bounds and ignores the mode, which is
            # what "uniform" means and is stated here so it is not inferred.
            "duration_distribution": str(r.get("duration_distribution") or "TRIANGULAR").upper(),
        }
        order.append(aid)
    for aid, a in activities.items():
        for p in a["predecessors"]:
            if p not in activities:
                raise StructureAbsent(
                    "An activity in the schedule network provided depends on an activity that "
                    "is not in the network, so the logic is incomplete and no reading is taken.")
    # Topological order; a cycle leaves activities unplaced.
    placed: list[str] = []
    remaining = set(order)
    while remaining:
        ready = [a for a in order if a in remaining
                 and all(p in placed for p in activities[a]["predecessors"])]
        if not ready:
            raise StructureAbsent(
                "The logic in the schedule network provided runs in a circle, so the activities "
                "have no order to be worked through and no reading is taken.")
        for a in ready:
            placed.append(a)
            remaining.discard(a)
    successors: dict[str, list[str]] = {a: [] for a in order}
    for aid, a in activities.items():
        for p in a["predecessors"]:
            successors[p].append(aid)
    return {"activities": activities, "order": placed, "successors": successors,
            "count": len(order), **meta}


def cpm_forward_backward(network: dict, durations: dict[str, float] | None = None
                         ) -> dict[str, Any]:
    """
    The critical path method's forward and backward pass, and total float from the two.

        ES_i = max over predecessors of EF_p, zero when there are none
        EF_i = ES_i + d_i
        project finish = max EF
        LF_i = min over successors of LS_s, project finish when there are none
        LS_i = LF_i - d_i
        TF_i = LS_i - ES_i = LF_i - EF_i

    Oracle: A=3 -> C=2 and B=4 -> C=2. Path A-C = 5, path B-C = 6, project finish 6. B and C are
    critical at zero total float and A carries one day of float.
    """
    acts = network["activities"]
    d = {a: (durations or {}).get(a, acts[a]["current_duration"]) for a in acts}
    es: dict[str, float] = {}
    ef: dict[str, float] = {}
    for a in network["order"]:
        preds = acts[a]["predecessors"]
        es[a] = max((ef[p] for p in preds), default=0.0)
        ef[a] = es[a] + d[a]
    finish = max(ef.values()) if ef else 0.0
    lf: dict[str, float] = {}
    ls: dict[str, float] = {}
    for a in reversed(network["order"]):
        succs = network["successors"][a]
        lf[a] = min((ls[s] for s in succs), default=finish)
        ls[a] = lf[a] - d[a]
    total_float = {a: ls[a] - es[a] for a in acts}
    critical = sorted(a for a in acts if abs(total_float[a]) < 1e-9)
    free_float = {a: (min((es[s] for s in network["successors"][a]), default=finish) - ef[a])
                  for a in acts}
    return {"early_start": es, "early_finish": ef, "late_start": ls, "late_finish": lf,
            "total_float": total_float, "free_float": free_float,
            "project_finish": finish, "critical_activities": critical}


# ------------------------------------------------------------ 2.1 PERT network criticality


def pert_moments(o: float, m: float, p: float) -> dict[str, float]:
    """
    Classical PERT moments: E[T] = (O + 4M + P)/6 and Var[T] = ((P - O)/6)^2.
    """
    if not (o <= m <= p):
        raise StructureAbsent(
            "An activity in the schedule network provided has three point durations that do not "
            "run from optimistic through most likely to pessimistic, so no distribution is "
            "formed from them.")
    return {"mean": (o + 4.0 * m + p) / 6.0, "variance": ((p - o) / 6.0) ** 2}


def pert_criticality(network: dict, rand: Callable[[], float] | None = None,
                     trials: int = 2000) -> dict[str, Any]:
    """
    Stochastic criticality: the share of trials in which each activity lies on the critical path.

        CriticalityIndex_i = trials where i is critical / total trials.

    Every trial resamples every activity duration and RECOMPUTES the whole network, which is what
    makes this criticality rather than a ranking of one deterministic pass.

    The deterministic collapse the contract states as its oracle is what happens when every
    activity's three-point estimate is a point: A duration 3, B duration 2, C duration 1, with
    A -> C and B -> C. Path A-C is 4 and path B-C is 3, so A and C are critical in every trial
    and B in none. That case is reached here with rand = None, which runs one deterministic pass.
    """
    acts = network["activities"]
    three_point = {a: (acts[a]["optimistic"], acts[a]["most_likely"], acts[a]["pessimistic"])
                   for a in acts}
    moments = {}
    for a, (o, m, p) in three_point.items():
        if o is None or m is None or p is None:
            moments[a] = None
        else:
            moments[a] = pert_moments(float(o), float(m), float(p))
    if rand is None or any(v is None for v in moments.values()):
        base = cpm_forward_backward(network)
        counts = {a: (1.0 if a in base["critical_activities"] else 0.0) for a in acts}
        return {"criticality_index": counts, "trials": 1, "deterministic": True,
                "project_finish": base["project_finish"],
                "critical_activities": base["critical_activities"],
                "activity_moments": moments}
    if trials < 1:
        raise ValueError("a criticality index needs at least one trial")
    counts = {a: 0 for a in acts}
    finishes: list[float] = []
    for _ in range(trials):
        drawn = {}
        for a in acts:
            o, m, p = (float(v) for v in three_point[a])
            drawn[a] = _draw(acts[a]["duration_distribution"], o, m, p, rand)
        pas = cpm_forward_backward(network, drawn)
        finishes.append(pas["project_finish"])
        for a in pas["critical_activities"]:
            counts[a] += 1
    return {"criticality_index": {a: counts[a] / trials for a in acts}, "trials": trials,
            "deterministic": False, "finishes": finishes,
            "activity_moments": moments,
            "project_finish_p80": empirical_quantile(finishes, 0.80)}


def _draw(family: str, a: float, m: float, b: float,
          rand: Callable[[], float]) -> float:
    """One draw from a declared activity duration distribution."""
    if family == "UNIFORM":
        return a + rand() * (b - a)
    if family == "TRIANGULAR":
        return _triangular_draw(a, m, b, rand)
    raise StructureAbsent(
        "An activity in the schedule network provided declares a duration distribution this "
        "measure does not hold, so the network cannot be simulated and no percentile is "
        "reported.")


def _triangular_draw(a: float, m: float, b: float, rand: Callable[[], float]) -> float:
    """Exact inverse-CDF triangular sampler; degenerate support returns the point."""
    if b <= a:
        return float(m)
    f = (m - a) / (b - a)
    u = rand()
    if u < f:
        return a + math.sqrt(u * (b - a) * (m - a))
    return b - math.sqrt((1 - u) * (b - a) * (b - m))


# ------------------------------------------------------------ 2.2 Line of Balance production rates


def lob_production_rates(structure: dict) -> dict[str, Any]:
    """
    Planned and actual production rates by line of work, and the deterioration between them.

        rate = change in units / change in time.

    Oracle: three locations planned complete on days 1, 2, 3 and actually complete on days 1,
    2.25, 3.5. The planned rate is (3-1)/(3-1) = 1.0 locations per day and the actual rate is
    (3-1)/(3.5-1) = 0.8 locations per day, so the actual production slope has deteriorated
    relative to plan and the ratio is 0.8.
    """
    words = "line of balance"
    rows = _rows(structure, "unit_progress", words)
    by_activity: dict[str, list[dict]] = {}
    for r in rows:
        aid = str(r.get("activity_id") or "")
        if not aid:
            raise StructureAbsent(
                "A line of work in the repetitive production record provided has no identity, "
                "so no production rate is measured from it.")
        by_activity.setdefault(aid, []).append(r)
    out = {}
    for aid, unit_rows in sorted(by_activity.items()):
        ordered = sorted(unit_rows, key=lambda r: _f(r, "location_sequence", words))
        if len(ordered) < 2:
            raise StructureAbsent(
                "A line of work in the repetitive production record provided covers a single "
                "location, so there is no run of locations for a production rate to be "
                "measured over.")
        first, last = ordered[0], ordered[-1]
        units = _f(last, "location_sequence", words) - _f(first, "location_sequence", words)
        planned_span = _f(last, "planned_finish_day", words) - _f(first, "planned_finish_day",
                                                                  words)
        actual_span = _f(last, "actual_finish_day", words) - _f(first, "actual_finish_day", words)
        if units <= 0 or planned_span <= 0 or actual_span <= 0:
            raise StructureAbsent(
                "A line of work in the repetitive production record provided finishes no later "
                "at its last location than at its first, so no production rate is measurable.")
        planned_rate = units / planned_span
        actual_rate = units / actual_span
        out[aid] = {"planned_rate": planned_rate, "actual_rate": actual_rate,
                    "rate_ratio": actual_rate / planned_rate,
                    "deteriorating": actual_rate < planned_rate,
                    "locations": len(ordered)}
    return {"by_activity": out, "activities": len(out)}


# ------------------------------------------------------------ 2.3 CCPM buffer consumption


def ccpm_buffer_consumption(original: float, remaining: float) -> dict[str, float]:
    """
    BC = B0 - Bt and BCR = (B0 - Bt) / B0.

    Oracle: B0 = 10 days, Bt = 6 days gives BC = 4 and BCR = 0.40. CPM float is not a buffer and
    is not substituted for one anywhere here.
    """
    if original is None or not math.isfinite(original) or original <= 0:
        raise StructureAbsent(
            "The critical chain provided has no project buffer sized above zero, so there is no "
            "buffer for a consumption to be a share of.")
    if remaining is None or not math.isfinite(remaining) or remaining < 0 or remaining > original:
        raise StructureAbsent(
            "The project buffer provided has more days remaining than it was sized for, or "
            "fewer than none, so the pair does not describe one buffer.")
    consumed = original - remaining
    return {"buffer_consumed_days": consumed, "buffer_consumption_ratio": consumed / original,
            "original_buffer_days": float(original), "remaining_buffer_days": float(remaining)}


# ------------------------------------------------------------ 2.4 Schedule Compression Index


def schedule_compression_index(network: dict) -> dict[str, Any]:
    """
    SCI = sum of baseline remaining durations / sum of current remaining durations, over the
    activities that reconcile between the two schedules at one governed status basis.

    SCI = 1 is equal remaining-duration demand. Below one is greater current demand, which is
    increasing compression pressure. Above one is a more relaxed demand. This is the PCEIF
    transparent contract and it is not claimed to be a universal industry statistical index.
    """
    acts = network["activities"]
    reconciled = [a for a, v in acts.items()
                  if v["baseline_duration"] is not None and v["remaining_duration"] is not None]
    if not reconciled:
        raise StructureAbsent(
            "No activity in the schedule network provided carries both a baseline duration and "
            "a current remaining duration, so the two schedules cannot be reconciled and no "
            "compression is measured.")
    baseline_sum = sum(float(acts[a]["baseline_duration"]) for a in reconciled)
    current_sum = sum(float(acts[a]["remaining_duration"]) for a in reconciled)
    if current_sum <= 0:
        raise StructureAbsent(
            "The activities that reconcile between the two schedules carry no remaining "
            "duration at all, so there is nothing left to compress and no ratio is reported.")
    return {"schedule_compression_index": baseline_sum / current_sum,
            "baseline_remaining_total": baseline_sum, "current_remaining_total": current_sum,
            "reconciled_activities": len(reconciled), "status_basis": network["status_basis"]}


# ------------------------------------------------------------ 2.5 Float Consumption Rate


def float_consumption(baseline_float: float, current_float: float,
                      previous_float: float | None = None,
                      delta_time: float | None = None) -> dict[str, Any]:
    """
    Float from the network, and its consumption.

        FC  = TF_baseline - TF_current
        FCR = FC / TF_baseline
        FDV = (TF_previous - TF_current) / delta_time, where a history exists.

    Oracle: baseline TF = 5 days, current TF = 2 days gives FC = 3 and FCR = 0.60.

    Zero baseline float is handled explicitly rather than divided by: an activity that began with
    no float was already critical, so the consumption FRACTION is undefined and is reported as
    such while the consumed amount is still reported.
    """
    for v, what in ((baseline_float, "the baseline total float"),
                    (current_float, "the current total float")):
        if v is None or not math.isfinite(v):
            raise StructureAbsent(
                f"No figure was provided for {what}, so no float consumption is measurable.")
    consumed = float(baseline_float) - float(current_float)
    out: dict[str, Any] = {"float_consumed_days": consumed,
                           "baseline_total_float": float(baseline_float),
                           "current_total_float": float(current_float)}
    if baseline_float > 0:
        out["float_consumption_ratio"] = consumed / float(baseline_float)
        out["already_critical_at_baseline"] = False
    else:
        out["float_consumption_ratio"] = None
        out["already_critical_at_baseline"] = True
    if previous_float is not None and delta_time is not None and delta_time > 0:
        out["float_depletion_velocity"] = (float(previous_float)
                                           - float(current_float)) / float(delta_time)
    return out


def network_float_consumption(network: dict) -> dict[str, Any]:
    """Total float from the CPM passes, compared with the baseline float the network carries."""
    passes = cpm_forward_backward(network)
    acts = network["activities"]
    rows = []
    for a in sorted(acts):
        base = acts[a]["baseline_total_float"]
        if base is None:
            continue
        rows.append({"activity_id": a,
                     **float_consumption(float(base), passes["total_float"][a])})
    if not rows:
        raise StructureAbsent(
            "No activity in the schedule network provided carries the float it began with, so "
            "no float consumption can be measured against it.")
    total_base = sum(r["baseline_total_float"] for r in rows)
    total_consumed = sum(r["float_consumed_days"] for r in rows)
    return {"activities": rows, "activity_count": len(rows),
            "baseline_total_float": total_base, "float_consumed_days": total_consumed,
            "float_consumption_ratio": (total_consumed / total_base) if total_base > 0 else None,
            "network_derived": True, "project_finish": passes["project_finish"]}


# ------------------------------------------------------------ 2.6 S-Curve deviation


def s_curve_deviation(planned: Sequence[float], actual: Sequence[float]) -> dict[str, Any]:
    """
    Deviation of the actual cumulative series from the planned one on a common measurement basis.

        SD_t      = Actual_t - Planned_t
        SDR_t     = (Actual_t - Planned_t) / Planned_t, where Planned_t > 0
        DeltaSD_t = SD_t - SD_(t-1)

    Oracle: planned 0.60 and actual 0.50 gives SD = -0.10.

    A single pair yields a point deviation and NO trend: `longitudinal` is False and the trend
    fields are absent, so a point reading cannot be presented as an S-curve trend.
    """
    p = [float(num(v, None)) for v in (planned or ()) if num(v, None) is not None]
    a = [float(num(v, None)) for v in (actual or ()) if num(v, None) is not None]
    if len(p) != len(planned or ()) or len(a) != len(actual or ()):
        raise StructureAbsent(
            "The planned or actual cumulative series carries a reading that is not a number, so "
            "no deviation is measured from it.")
    if not p or not a:
        raise StructureAbsent(
            "No cumulative planned and actual series on a common basis was provided, so no "
            "deviation from the planned curve is measured.")
    n = min(len(p), len(a))
    sd = [a[i] - p[i] for i in range(n)]
    out: dict[str, Any] = {"deviation": sd[-1], "planned": p[n - 1], "actual": a[n - 1],
                           "points": n, "longitudinal": n >= 2,
                           "relative_deviation": (sd[-1] / p[n - 1]) if p[n - 1] > 0 else None}
    if n >= 2:
        out["deviation_series"] = sd
        out["trend"] = sd[-1] - sd[-2]
        out["trend_direction"] = ("deteriorating" if sd[-1] < sd[-2]
                                  else "improving" if sd[-1] > sd[-2] else "unchanged")
    return out


# ------------------------------------------------------------ 2.7 Milestone Trend Analysis


def milestone_trend(structure: dict) -> dict[str, Any]:
    """
    Milestone variance against the committed baseline, and drift between successive forecasts.

        MV_m,t = ForecastDate_m,t - BaselineDate_m
        MD_m,t = ForecastDate_m,t - ForecastDate_m,t-1

    Oracle: baseline day 100 with successive forecasts 104, 108, 111 gives slips of 4, 8 and 11
    days against the ORIGINAL commitment, and the direction is deteriorating because each
    variance exceeds the one before it.

    The original commitment is retained separately from the current approved baseline, so a
    rebaseline cannot erase the commitment history: both variances are reported.
    """
    words = V3_STRUCTURE_WORDS["A2.7"]
    rows = _rows(structure, "milestones", words)
    _provenance(structure, words, "schedule_version")
    by_id: dict[str, dict] = {}
    for r in rows:
        mid = str(r.get("milestone_id") or "")
        if not mid:
            raise StructureAbsent(
                "A milestone in the forecast history provided has no identity, so it cannot be "
                "followed across reporting periods and no trend is reported.")
        by_id.setdefault(mid, {"original": None, "approved": None, "forecasts": []})
        by_id[mid]["original"] = _f(r, "original_baseline_day", words)
        if r.get("approved_baseline_day") is not None:
            by_id[mid]["approved"] = _f(r, "approved_baseline_day", words)
        forecasts = r.get("forecasts")
        if not isinstance(forecasts, list):
            raise StructureAbsent(
                "A milestone in the forecast history provided states its forecasts in a form "
                "this measure cannot read, so no trend is reported.")
        for f in forecasts:
            by_id[mid]["forecasts"].append(
                (_f(f, "report_index", words), _f(f, "forecast_day", words)))
    out = []
    for mid, rec in sorted(by_id.items()):
        series = [d for _, d in sorted(rec["forecasts"], key=lambda pair: pair[0])]
        if len(series) < 2:
            raise StructureAbsent(
                "A milestone in the forecast history provided has been forecast only once, so "
                "there is no run of forecasts for a trend to be read from.")
        variances = [d - rec["original"] for d in series]
        drifts = [series[i] - series[i - 1] for i in range(1, len(series))]
        direction = ("deteriorating" if variances[-1] > variances[-2]
                     else "improving" if variances[-1] < variances[-2] else "stable")
        out.append({"milestone_id": mid, "original_baseline_day": rec["original"],
                    "approved_baseline_day": rec["approved"],
                    "forecast_days": series, "variance_days": variances,
                    "period_drift_days": drifts,
                    "current_variance_days": variances[-1],
                    "current_drift_days": drifts[-1], "direction": direction,
                    "rebaselined": rec["approved"] is not None
                    and rec["approved"] != rec["original"]})
    return {"milestones": out, "milestone_count": len(out),
            "worst_variance_days": max(m["current_variance_days"] for m in out),
            "deteriorating_count": sum(1 for m in out if m["direction"] == "deteriorating")}


# ------------------------------------------------------------ 2.8 Look-Ahead Schedule Health


def look_ahead_ready_fraction(structure: dict) -> dict[str, Any]:
    """
    ReadyFraction = (P - C) / P = 1 - C/P, over the activities in a governed look-ahead window.

    Oracle: 10 planned and 3 constrained gives 0.70.

    This is readiness grounded in constraint removal. Percent Plan Complete is a different
    measurement -- the share of committed tasks actually finished -- and is not substituted for
    it here. Each activity must carry its own identity and constraint status, so the counts are
    derived from an inventory rather than asserted as two numbers.
    """
    words = V3_STRUCTURE_WORDS["A2.8"]
    rows = _rows(structure, "activities", words)
    _provenance(structure, words, "horizon", "status_date")
    seen = set()
    constrained = 0
    categories: dict[str, int] = {}
    for r in rows:
        aid = str(r.get("activity_id") or "")
        if not aid:
            raise StructureAbsent(
                "An activity in the look ahead schedule provided has no identity, so the "
                "constraints on it cannot be counted and no readiness is reported.")
        if aid in seen:
            raise StructureAbsent(
                "The look ahead schedule provided names one activity twice, so its readiness "
                "would be counted twice and no readiness is reported.")
        seen.add(aid)
        status = str(r.get("constraint_status") or "").upper()
        if status not in ("OPEN", "CLEARED"):
            raise StructureAbsent(
                "An activity in the look ahead schedule provided does not say whether its "
                "constraints have been cleared, so its readiness is not known and none is "
                "reported for the window.")
        if status == "OPEN":
            constrained += 1
            category = str(r.get("constraint_category") or "")
            if not category:
                raise StructureAbsent(
                    "A constrained activity in the look ahead schedule provided does not say "
                    "what kind of constraint it carries, so the inventory is not reliable and "
                    "no readiness is reported.")
            categories[category] = categories.get(category, 0) + 1
    planned = len(seen)
    if planned <= 0:
        raise StructureAbsent(
            "The look ahead schedule provided plans no activities in its window, so there is "
            "nothing whose readiness can be measured.")
    return {"ready_fraction": (planned - constrained) / planned, "planned": planned,
            "constrained": constrained, "constraint_categories": categories,
            "horizon": str(structure.get("horizon"))}


# ------------------------------------------------------------ 2.9 Resource Loading Index


def resource_loading(structure: dict) -> dict[str, Any]:
    """
    LoadRatio_t = Demand_t / AvailableCapacity_t, for each time bucket and resource type.

    Oracle: demand 120 labour-hours against capacity 100 gives 1.20.

    A project-total planned-versus-actual labour ratio is not this index and is not computed
    here: the structure must be time-phased and must state the capacity, not only the demand.
    """
    words = V3_STRUCTURE_WORDS["A2.9"]
    rows = _rows(structure, "buckets", words)
    _provenance(structure, words, "resource_plan_version")
    out = []
    for r in rows:
        bucket = str(r.get("time_bucket") or "")
        resource = str(r.get("resource_type") or "")
        if not bucket or not resource:
            raise StructureAbsent(
                "A row in the resource profile provided does not say which period or which kind "
                "of resource it describes, so no load ratio is formed from it.")
        demand = _f(r, "demand", words)
        capacity = _f(r, "available_capacity", words)
        if demand < 0:
            raise StructureAbsent(
                "A row in the resource profile provided demands less than no work, which is not "
                "a quantity of demand, so no load ratio is formed from it.")
        if capacity <= 0:
            raise StructureAbsent(
                "A row in the resource profile provided states no capacity above zero, so there "
                "is nothing for the demand to be a share of and no load ratio is formed.")
        out.append({"time_bucket": bucket, "resource_type": resource,
                    "demand": demand, "available_capacity": capacity,
                    "load_ratio": demand / capacity,
                    "deployed": num(r.get("deployed"), None)})
    peak = max(out, key=lambda r: r["load_ratio"])
    return {"buckets": out, "bucket_count": len(out), "peak": peak,
            "peak_load_ratio": peak["load_ratio"],
            "over_capacity_buckets": sum(1 for r in out if r["load_ratio"] > 1.0)}


# ------------------------------------------------------------ 2.10 Schedule Risk Analysis P80


def schedule_risk_p80(network: dict, rand: Callable[[], float], trials: int = 2000,
                      p: float = 0.80) -> dict[str, Any]:
    """
    Monte Carlo over the network: every trial redraws every duration and RECOMPUTES the network.

    The reported figure is the empirical p quantile of the simulated project finish times, under
    the frozen convention in empirical_quantile.

    Laboratory oracle: a single activity with duration Uniform(0, 10) has a true P80 of 8, and
    the simulation must converge to it within a tolerance DECLARED BEFORE EXECUTION -- see
    server/tools/test_run28_canonical_oracles.py, which states its tolerance in the check name
    before the run. A deterministic normal z-score uplift is not this method and is computed
    nowhere here.
    """
    acts = network["activities"]
    for a, v in acts.items():
        if v["optimistic"] is None or v["most_likely"] is None or v["pessimistic"] is None:
            raise StructureAbsent(
                "An activity in the schedule network provided carries no duration distribution, "
                "so the network cannot be simulated and no percentile is reported.")
    if trials < 1:
        raise ValueError("a schedule risk analysis needs at least one trial")
    finishes = []
    for _ in range(trials):
        drawn = {a: _draw(acts[a]["duration_distribution"],
                          float(acts[a]["optimistic"]), float(acts[a]["most_likely"]),
                          float(acts[a]["pessimistic"]), rand) for a in acts}
        finishes.append(cpm_forward_backward(network, drawn)["project_finish"])
    deterministic = cpm_forward_backward(network)["project_finish"]
    return {"p_quantile": p, "p80_finish": empirical_quantile(finishes, p),
            "p50_finish": empirical_quantile(finishes, 0.50),
            "deterministic_finish": deterministic, "trials": trials,
            "mean_finish": sum(finishes) / len(finishes)}


# ------------------------------------------------------------ 2.11 Critical Path Index


def critical_path_status(network: dict) -> dict[str, Any]:
    """
    Actual CPM critical-path status and margin, from the forward and backward passes.

    A weighted schedule-index-and-progress average is not a critical-path method and is computed
    nowhere here.
    """
    passes = cpm_forward_backward(network)
    acts = network["activities"]
    critical = passes["critical_activities"]
    non_critical = [a for a in sorted(acts) if a not in set(critical)]
    return {"project_finish": passes["project_finish"],
            "critical_activities": critical,
            "critical_count": len(critical),
            "activity_count": len(acts),
            "critical_fraction": len(critical) / len(acts) if acts else 0.0,
            "total_float": {a: passes["total_float"][a] for a in sorted(acts)},
            "minimum_non_critical_float": (min(passes["total_float"][a] for a in non_critical)
                                           if non_critical else None)}


# =================================================================================================
# CATEGORY 3
# =================================================================================================

# ------------------------------------------------------------ 3.1 Reference Class Forecasting


def reference_class_forecast(structure: dict, inside_view: float,
                             p: float = 0.50) -> dict[str, Any]:
    """
    The outside view: an empirical uplift read off a governed reference class.

        U_p              = Quantile_p({r_i}) over the historical proportional overruns
        AdjustedForecast = InsideViewForecast * (1 + U_p)

    Oracle: overruns {0.00, 0.10, 0.20, 0.30, 0.40} have a median uplift of 0.20 under the frozen
    quantile convention. An embedded fixed multiplier is not this method and is used nowhere.
    """
    words = V3_STRUCTURE_WORDS["A3.1"]
    members = _rows(structure, "members", words)
    meta = _provenance(structure, words, "inclusion_criteria", "exclusion_criteria",
                       "outcome_definition", "normalization", "data_vintage")
    ids, overruns = set(), []
    for m in members:
        pid = str(m.get("reference_project_id") or "")
        if not pid:
            raise StructureAbsent(
                "A project in the reference class provided has no identity, so the class cannot "
                "be audited and no outside view is taken from it.")
        if pid in ids:
            raise StructureAbsent(
                "The reference class provided names one project twice, so it would be counted "
                "twice and no outside view is taken from it.")
        ids.add(pid)
        overruns.append(_f(m, "proportional_overrun", words))
    evaluated = str(structure.get("evaluated_project_id") or "")
    if evaluated and evaluated in ids:
        raise StructureAbsent(
            "The project being assessed is itself in the reference class it would be compared "
            "against, so the comparison would be of the project with itself.")
    if len(overruns) < 3:
        raise StructureAbsent(
            "The reference class provided holds fewer than three completed comparable projects, "
            "so it carries no distribution of outcomes to place this project against.")
    if inside_view is None or not math.isfinite(inside_view) or inside_view <= 0:
        raise StructureAbsent(
            "No inside view forecast above zero was provided for the outside view to adjust, so "
            "no adjusted forecast is reported.")
    uplift = empirical_quantile(overruns, p)
    return {"uplift": uplift, "percentile": p, "sample_size": len(overruns),
            "inside_view": float(inside_view),
            "adjusted_forecast": float(inside_view) * (1.0 + uplift),
            "min_overrun": min(overruns), "max_overrun": max(overruns), **meta}


# ------------------------------------------------------------ 3.2 Contingency Burn Rate


def contingency_burn(original: float, remaining: float,
                     progress_fraction: float | None) -> dict[str, Any]:
    """
        C              = (OriginalContingency - RemainingContingency) / OriginalContingency
        NormalizedBurn = C / ProgressFraction, when ProgressFraction > 0.

    Oracle: original 100, remaining 60, progress 0.50 gives a consumed fraction of 0.40 and a
    normalized burn of 0.80. No universal bands are supplied for either figure.
    """
    if original is None or not math.isfinite(original) or original <= 0:
        raise StructureAbsent(
            "No original contingency above zero was provided, so the share consumed has no "
            "denominator and none is reported.")
    if remaining is None or not math.isfinite(remaining) or remaining < 0 or remaining > original:
        raise StructureAbsent(
            "The remaining contingency provided is below nothing or above the original amount, "
            "so the two figures do not describe one contingency and no share is reported.")
    consumed = (original - remaining) / original
    out: dict[str, Any] = {"consumed_fraction": consumed,
                           "original_contingency": float(original),
                           "remaining_contingency": float(remaining),
                           "normalized_burn": None}
    if progress_fraction is not None and math.isfinite(progress_fraction) \
            and progress_fraction > 0:
        out["normalized_burn"] = consumed / float(progress_fraction)
        out["progress_fraction"] = float(progress_fraction)
    return out


# ------------------------------------------------------------ 3.3 Labor Productivity Index


def labor_productivity(structure: dict) -> dict[str, Any]:
    """
    Productivity is output per labour input, on a comparable earned/installed quantity.

        ActualProductivity  = EarnedOutput  / ActualLaborHours
        PlannedProductivity = PlannedOutput / PlannedLaborHours
        ProductivityIndex   = ActualProductivity / PlannedProductivity

    Oracle: planned 10 units/hour against actual 8 units/hour gives an index of 0.80.

    Planned hours over actual hours alone is NOT this metric and is computed nowhere here: the
    structure must state the quantities installed and planned, and the unit they are counted in,
    or nothing is reported.
    """
    words = V3_STRUCTURE_WORDS["A3.3"]
    unit = str(structure.get("output_unit") or "").strip()
    if not unit:
        raise StructureAbsent(
            "The production record provided does not say what unit the work is counted in, so "
            "the quantities cannot be compared and no productivity is reported.")
    _provenance(structure, words, "quantity_source")
    earned = _f(structure, "earned_output", words)
    planned_output = _f(structure, "planned_output", words)
    actual_hours = _f(structure, "actual_labor_hours", words)
    planned_hours = _f(structure, "planned_labor_hours", words)
    if earned < 0 or planned_output <= 0:
        raise StructureAbsent(
            "The production record provided states no planned quantity above zero, or a "
            "quantity installed below nothing, so no productivity is measurable from it.")
    if actual_hours <= 0 or planned_hours <= 0:
        raise StructureAbsent(
            "The production record provided states no labour hours above zero on one of its two "
            "sides, so no output per hour is measurable from it.")
    actual_p = earned / actual_hours
    planned_p = planned_output / planned_hours
    return {"actual_productivity": actual_p, "planned_productivity": planned_p,
            "productivity_index": actual_p / planned_p, "output_unit": unit,
            "earned_output": earned, "planned_output": planned_output,
            "actual_labor_hours": actual_hours, "planned_labor_hours": planned_hours}


# ------------------------------------------------------------ 3.5 Overhead Absorption Rate


def overhead_absorption(structure: dict) -> dict[str, Any]:
    """
    Absorption rates over an explicit allocation base, and the variance between them.

        PlannedRate   = PlannedOverhead / PlannedDriver
        ActualRate    = ActualOverhead  / ActualDriver
        RateVariance  = ActualRate - PlannedRate
        RelativeRateVariance = (ActualRate - PlannedRate) / PlannedRate

    Oracle: planned 100 over 1000 is 0.10, actual 120 over 1000 is 0.12, so the rate variance is
    0.02 and the relative variance is 0.20.

    Indirect actual over indirect plan with no allocation base is not overhead absorption and is
    computed nowhere here.
    """
    words = V3_STRUCTURE_WORDS["A3.5"]
    base = str(structure.get("allocation_base") or "").strip()
    if not base:
        raise StructureAbsent(
            "The overhead record provided names no allocation base for the overhead to be "
            "absorbed over, so no absorption rate is measurable from it.")
    _provenance(structure, words, "driver_source")
    planned_oh = _f(structure, "planned_overhead", words)
    actual_oh = _f(structure, "actual_overhead", words)
    planned_driver = _f(structure, "planned_driver", words)
    actual_driver = _f(structure, "actual_driver", words)
    if planned_driver <= 0 or actual_driver <= 0:
        raise StructureAbsent(
            "The overhead record provided states no amount of the allocation base above zero on "
            "one of its two sides, so no absorption rate is measurable from it.")
    if planned_oh < 0 or actual_oh < 0:
        raise StructureAbsent(
            "The overhead record provided states an overhead amount below zero, which no cost "
            "can be, so no absorption rate is measurable from it.")
    planned_rate = planned_oh / planned_driver
    actual_rate = actual_oh / actual_driver
    if planned_rate <= 0:
        raise StructureAbsent(
            "The overhead record provided plans no overhead to absorb, so there is no planned "
            "rate for the actual rate to be compared against.")
    return {"planned_rate": planned_rate, "actual_rate": actual_rate,
            "rate_variance": actual_rate - planned_rate,
            "relative_rate_variance": (actual_rate - planned_rate) / planned_rate,
            "allocation_base": base, "planned_driver": planned_driver,
            "actual_driver": actual_driver}


# ------------------------------------------------------------ 3.6 Cost Risk Analysis P80


def cost_risk_simulation(structure: dict, rand: Callable[[], float],
                         trials: int = 20000, p: float = 0.80) -> dict[str, Any]:
    """
    TotalCost = BaseCostComponents + RealizedRiskEvents, simulated to an empirical distribution.

    Each risk event occurs with its stated probability; when it occurs its impact is drawn from
    its stated distribution. The reported figure is the empirical p quantile under the frozen
    right-continuous convention.

    Oracle: BaseCost 100 with one Bernoulli event at probability 0.5 and impact 20 gives a
    two-point distribution, 100 and 120 with weight one half each, mean 110 and P80 = 120 under
    that convention. A deterministic CPI uplift is not this method and is computed nowhere here.
    """
    words = V3_STRUCTURE_WORDS["A3.6"]
    components = _rows(structure, "cost_components", words)
    _provenance(structure, words, "model_version", "estimate_source")
    base = sum(_f(c, "base_amount", words) for c in components)
    if base <= 0:
        raise StructureAbsent(
            "The cost risk model provided carries no base cost above zero, so there is nothing "
            "for the risks to be added to and no distribution is formed.")
    events = structure.get("risk_events")
    if not isinstance(events, list):
        raise StructureAbsent(
            "The cost risk model provided states its risk events in a form this measure cannot "
            "read, so no distribution is formed from it.")
    parsed = []
    for e in events:
        if not isinstance(e, dict):
            raise StructureAbsent(
                "A risk event in the cost risk model provided is not in a form this measure can "
                "read, so no distribution is formed from it.")
        prob = _f(e, "probability", words)
        if not (0.0 <= prob <= 1.0):
            raise StructureAbsent(
                "A risk event in the cost risk model provided states a likelihood outside "
                "nought to one, which is not a probability, so no distribution is formed.")
        family = str(e.get("impact_distribution") or "POINT").upper()
        params = e.get("impact_parameters") if isinstance(e.get("impact_parameters"), dict) else {}
        if family == "POINT":
            impact = (_f(e, "impact", words),) * 3
        elif family in ("TRIANGULAR", "BETA_PERT"):
            impact = (_f(params, "optimistic", words), _f(params, "most_likely", words),
                      _f(params, "pessimistic", words))
            if not (impact[0] <= impact[1] <= impact[2]):
                raise StructureAbsent(
                    "A risk event in the cost risk model provided has three point impacts that "
                    "do not run from least to greatest, so no distribution is formed from them.")
        else:
            raise StructureAbsent(
                "A risk event in the cost risk model provided states an impact distribution "
                "this measure does not hold, so no distribution is formed from it.")
        parsed.append((prob, impact))
    # RUN 28 CLOSURE. THE DEPENDENCE POLICY, DECLARED WHERE IT IS MATERIAL RATHER THAN ASSUMED.
    #
    # The supplied contract requires "a declared dependence policy where material". The loop
    # below draws every event from its own uniform, which IS a dependence policy -- mutual
    # independence -- and Run 28 applied it silently. Silently assuming independence across
    # correlated risks understates the upper tail, which is exactly the quantity A3.6 reports,
    # so the assumption must be stated by the SOURCE of the model rather than by this file.
    #
    # It is material only with more than one event: a single Bernoulli has nothing to be
    # dependent with. With two or more, a model that does not say how they relate is refused.
    dependence = str(structure.get("dependence_policy") or "").strip()
    if len(parsed) > 1 and not dependence:
        raise StructureAbsent(
            "The cost risk model provided carries more than one risk event but does not say "
            "whether those events are related to one another, and how far the total cost can "
            "run depends on that, so no percentile is reported.")
    if not dependence:
        dependence = "not material: a single risk event has nothing to be dependent with"
    if trials < 1:
        raise ValueError("a cost risk analysis needs at least one trial")
    totals = []
    for _ in range(trials):
        total = base
        for prob, impact in parsed:
            if rand() < prob:
                total += (impact[1] if impact[0] == impact[2]
                          else _triangular_draw(impact[0], impact[1], impact[2], rand))
        totals.append(total)
    return {"base_cost": base, "risk_event_count": len(parsed), "trials": trials,
            "dependence_policy": dependence,
            "p_quantile": p, "p80_total_cost": empirical_quantile(totals, p),
            "p50_total_cost": empirical_quantile(totals, 0.50),
            "mean_total_cost": sum(totals) / len(totals)}


# ------------------------------------------------------------ 3.7 Analogous Estimating Ratio


def analogous_estimate(structure: dict) -> dict[str, Any]:
    """
    Genuine analogous estimating: an identified analog, adapted by stated factors.

        AdaptedEstimate = AnalogCost * product of the adaptation factors.

    Example from the contract: 100 * 1.20 * 1.10 = 132.

    A preloaded analog overrun percentage with no identified analog is not this method and is
    computed nowhere here.
    """
    words = V3_STRUCTURE_WORDS["A3.7"]
    analog_id = str(structure.get("analog_project_id") or "").strip()
    if not analog_id:
        raise StructureAbsent(
            "No analogous project was identified for this project, so there is nothing to adapt "
            "and no analogous estimate is reported.")
    _provenance(structure, words, "source", "comparability_criteria", "normalization")
    cost = _f(structure, "analog_cost", words)
    if cost <= 0:
        raise StructureAbsent(
            "The analogous project identified carries no cost above zero, so nothing can be "
            "adapted from it.")
    factors = structure.get("adaptation_factors")
    if not isinstance(factors, list) or not factors:
        raise StructureAbsent(
            "No adaptation factors were provided to carry the analogous project's cost across "
            "to this one, so no analogous estimate is reported.")
    adapted = cost
    named = []
    for f in factors:
        if not isinstance(f, dict):
            raise StructureAbsent(
                "An adaptation factor provided is not in a form this measure can read, so no "
                "analogous estimate is reported.")
        name = str(f.get("factor_name") or "")
        value = _f(f, "factor_value", words)
        if not name:
            raise StructureAbsent(
                "An adaptation factor provided does not say what it adapts for, so no "
                "analogous estimate is reported from it.")
        if value <= 0:
            raise StructureAbsent(
                "An adaptation factor provided is zero or below, which no multiplier onto a "
                "cost can be, so no analogous estimate is reported.")
        adapted *= value
        named.append({"factor_name": name, "factor_value": value})
    return {"analog_project_id": analog_id, "analog_cost": cost,
            "adaptation_factors": named, "adapted_estimate": adapted,
            "combined_factor": adapted / cost}


# ------------------------------------------------------------ 3.8 Parametric Cost Index


def parametric_cost(structure: dict, drivers: dict[str, float]) -> dict[str, Any]:
    """
    A fitted linear parametric cost model. LABORATORY ONLY: the module stays disabled in Run 28.

        Cost = beta0 + beta1*x1 + ... + betap*xp

    Oracle: 10 + 2*4 + 3*5 = 33.

    Comparing two EAC formulas is not parametric estimating and is computed nowhere here. Every
    coefficient must state its units and the dataset it was fitted to, and a driver the model
    does not carry, or a driver the model carries and the project does not supply, both refuse:
    an omitted driver silently valued at zero is exactly the failure this refusal exists for.
    """
    words = V3_STRUCTURE_WORDS["A3.8"]
    _provenance(structure, words, "coefficient_source", "fit_dataset", "model_version")
    intercept = _f(structure, "intercept", words)
    coefficients = structure.get("coefficients")
    if not isinstance(coefficients, list) or not coefficients:
        raise StructureAbsent(
            "The parametric cost model provided carries no fitted coefficients, so no cost is "
            "predicted from it.")
    declared: dict[str, dict] = {}
    for c in coefficients:
        if not isinstance(c, dict):
            raise StructureAbsent(
                "A coefficient in the parametric cost model provided is not in a form this "
                "measure can read, so no cost is predicted from it.")
        name = str(c.get("driver") or "")
        unit = str(c.get("unit") or "")
        if not name or not unit:
            raise StructureAbsent(
                "A coefficient in the parametric cost model provided does not name its driver "
                "or the unit that driver is measured in, so no cost is predicted from it.")
        declared[name] = {"coefficient": _f(c, "coefficient", words), "unit": unit}
    supplied = set(drivers or {})
    if supplied != set(declared):
        raise StructureAbsent(
            "The drivers supplied for this project do not match the drivers the parametric cost "
            "model was fitted on, so a prediction from it would rest on a driver nobody "
            "measured and none is made.")
    cost = intercept
    terms = []
    for name in sorted(declared):
        x = num(drivers[name], None)
        if x is None or not math.isfinite(x):
            raise StructureAbsent(
                "A driver supplied for this project is not a number, so no cost is predicted.")
        contribution = declared[name]["coefficient"] * float(x)
        cost += contribution
        terms.append({"driver": name, "value": float(x),
                      "coefficient": declared[name]["coefficient"],
                      "unit": declared[name]["unit"], "contribution": contribution})
    return {"predicted_cost": cost, "intercept": intercept, "terms": terms,
            "driver_count": len(terms), "design_row_length": len(terms) + 1}


# ------------------------------------------------------------ 3.9 Inflation Adjustment Index


def inflation_adjustment(structure: dict, base_cost: float) -> dict[str, Any]:
    """
    Escalation from a governed EXTERNAL price index.

        EscalationFactor = Index_current / Index_base
        AdjustedCost     = BaseCost * EscalationFactor

    Oracle: base index 200 and current index 220 give a factor of 1.10, and a base cost of 100
    gives an adjusted cost of 110.

    A baseline-to-current project material price ratio is NOT an external index and is computed
    nowhere here. No index value is hard-coded anywhere in this file: every figure comes off the
    supplied structure, which must name the series, its authority, geography, scope, base period,
    observation period and vintage.
    """
    words = V3_STRUCTURE_WORDS["A3.9"]
    meta = _provenance(structure, words, "index_name", "authority", "geography", "scope",
                       "base_period", "observation_period", "vintage")
    base_index = _f(structure, "base_index_value", words)
    current_index = _f(structure, "current_index_value", words)
    if base_index <= 0 or current_index <= 0:
        raise StructureAbsent(
            "The price index provided carries a value of zero or below in one of its two "
            "periods, which no index level can be, so no escalation factor is formed.")
    if base_cost is None or not math.isfinite(base_cost) or base_cost < 0:
        raise StructureAbsent(
            "No cost exposure at or above zero was provided for the index to be applied to, so "
            "no adjusted cost is reported.")
    factor = current_index / base_index
    return {"escalation_factor": factor, "base_index_value": base_index,
            "current_index_value": current_index, "base_cost": float(base_cost),
            "adjusted_cost": float(base_cost) * factor,
            "escalation_amount": float(base_cost) * (factor - 1.0), **meta}
