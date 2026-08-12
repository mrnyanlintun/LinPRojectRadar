"""
B2.10–B2.20 fuzzy-set / MCDM extensions, ported from assets/js/simulations.js
(Cat 7 evidence-combination extensions). Flat signalInputs in, result dict out; none draws
from the generator. Validated against the JavaScript in a browser; see VALIDATION.md.

Porting notes: Fermatean's `while (mu³+nu³ > 1) { mu *= 0.95; nu *= 0.95 }` renormalization
loop is reproduced verbatim — IEEE doubles make the iteration count identical in both
languages. MARCOS's score formula divides by f_ideal and f_anti; at the extremes JavaScript's
Infinity arithmetic yields a finite 0, reproduced via _jsdiv rather than refused.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .models import check_inputs, insufficient
from .models_ext import _js_str
from .models_gov import _jsdiv
from .rng import js_round, round2

_round3 = lambda v: js_round(v * 1000) / 1000  # noqa: E731


def _clamp01(v):
    return min(1, max(0, v))


# ------------------------------------------------------------ B2.10 Pythagorean Fuzzy Sets


def run_pythagorean_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Pythagorean_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    mu = _clamp01((evm_min - 0.85) / 0.15)
    nu = _clamp01((0.95 - evm_min) / 0.15)
    if mu * mu + nu * nu > 1:
        norm = math.sqrt(mu * mu + nu * nu)
        mu /= norm
        nu /= norm
    pi = math.sqrt(max(0, 1 - mu * mu - nu * nu))
    doc = si.get("docRiskScore") or 0
    adj_mu = mu * (1 - doc * 0.3)
    adj_nu = min(1, nu + doc * 0.3)
    score = adj_mu - adj_nu
    color = ("Green" if score >= 0.3 else "Yellow" if score >= 0.0
             else "Amber" if score >= -0.3 else "Red")
    return {
        "method_class": "Pythagorean_Fuzzy",
        "status_color": color,
        "membership": round2(adj_mu),
        "non_membership": round2(adj_nu),
        "hesitancy": round2(pi),
        "evidence_metric": (
            f"PFS: μ={_js_str(round2(adj_mu))} ν={_js_str(round2(adj_nu))} "
            f"π={_js_str(round2(pi))}"
        ),
    }


# ------------------------------------------------------------ B2.11 Picture Fuzzy Sets


def run_picture_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Picture_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    positive = max(0, min(0.95, (evm_min - 0.85) / 0.15))
    negative = max(0, min(0.95, (0.95 - evm_min) / 0.15)) * (1 + si["docRiskScore"] * 0.5)
    negative = min(0.95, negative)
    neutral = max(0, 0.6 - positive - negative) * 0.3
    refusal = max(0, 1 - positive - neutral - negative)
    score = positive - negative
    color = ("Green" if score >= 0.30 else "Yellow" if score >= 0.00
             else "Amber" if score >= -0.30 else "Red")
    return {
        "method_class": "Picture_Fuzzy",
        "status_color": color,
        "positive": round2(positive),
        "neutral": round2(neutral),
        "negative": round2(negative),
        "refusal": round2(refusal),
        "evidence_metric": (
            f"PicFS: +{_js_str(round2(positive))} 0{_js_str(round2(neutral))} "
            f"-{_js_str(round2(negative))} r{_js_str(round2(refusal))}"
        ),
    }


# ------------------------------------------------------------ B2.12 Hesitant Fuzzy Sets


def run_hesitant_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi")):
        return insufficient("Hesitant_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    evm_max = max(si["cpi"], si["spi"])
    memberships = [
        _clamp01((evm_min - 0.85) / 0.15),
        _clamp01((evm_max - 0.85) / 0.15),
        _clamp01(((evm_min + evm_max) / 2 - 0.85) / 0.15),
    ]
    score = sum(memberships) / len(memberships)
    hesitancy = max(memberships) - min(memberships)
    color = ("Green" if score >= 0.7 else "Yellow" if score >= 0.5
             else "Amber" if score >= 0.3 else "Red")
    return {
        "method_class": "Hesitant_Fuzzy",
        "status_color": color,
        "memberships": [round2(m) for m in memberships],
        "average_membership": round2(score),
        "hesitancy_degree": round2(hesitancy),
        "evidence_metric": (
            f"HFS: avg membership {_js_str(round2(score))}, "
            f"hesitancy {_js_str(round2(hesitancy))}"
        ),
    }


# ------------------------------------------------------------ B2.13 Type-2 Fuzzy Sets


def run_type2_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi")):
        return insufficient("Type2_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    primary = _clamp01((evm_min - 0.85) / 0.15)
    uncertainty = abs(si["cpi"] - si["spi"]) * 2
    lower = max(0, primary - uncertainty * 0.5)
    upper = min(1, primary + uncertainty * 0.5)
    centroid = (lower + upper) / 2
    footprint = upper - lower
    color = ("Green" if centroid >= 0.7 and footprint <= 0.2
             else "Yellow" if centroid >= 0.5
             else "Amber" if centroid >= 0.3 else "Red")
    return {
        "method_class": "Type2_Fuzzy",
        "status_color": color,
        "lower_membership": round2(lower),
        "upper_membership": round2(upper),
        "centroid": round2(centroid),
        "footprint_of_uncertainty": round2(footprint),
        "evidence_metric": (
            f"T2FS: centroid {_js_str(round2(centroid))}, FOU {_js_str(round2(footprint))}"
        ),
    }


# ------------------------------------------------------------ B2.14 Maximum Entropy


def run_maximum_entropy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Maximum_Entropy")
    evm_min = min(si["cpi"], si["spi"])
    raw = [
        max(0.01, 0.70 if evm_min >= 0.95 else 0.20 if evm_min >= 0.90 else 0.05),
        max(0.01, 0.20 if evm_min >= 0.95 else 0.50 if evm_min >= 0.90 else 0.20),
        max(0.01, 0.07 if evm_min >= 0.95 else 0.25 if evm_min >= 0.90 else 0.60),
        max(0.01, 0.02 if evm_min >= 0.95 else 0.05 if evm_min >= 0.90 else 0.15),
    ]
    total = sum(raw)
    probs = [p / total for p in raw]
    doc = si.get("docRiskScore") or 0
    probs[2] = min(0.95, probs[2] + doc * 0.2)
    probs[3] = min(0.95, probs[3] + doc * 0.1)
    total = sum(probs)
    probs = [p / total for p in probs]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    normalized = entropy / math.log2(4)
    labels = ["Green", "Yellow", "Amber", "Red"]
    dominant = labels[probs.index(max(probs))]
    return {
        "method_class": "Maximum_Entropy",
        "status_color": dominant,
        "probabilities": {
            "Green": int(js_round(probs[0] * 100)),
            "Yellow": int(js_round(probs[1] * 100)),
            "Amber": int(js_round(probs[2] * 100)),
            "Red": int(js_round(probs[3] * 100)),
        },
        "entropy": round2(normalized),
        "evidence_metric": f"MaxEnt: {dominant} (entropy {_js_str(round2(normalized))})",
    }


# ------------------------------------------------------------ B2.15 Possibility Theory


def run_possibility_theory(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Possibility_Theory")
    evm_min = min(si["cpi"], si["spi"])
    doc = si.get("docRiskScore") or 0
    possibility = {
        "Green": min(1, max(0, (evm_min - 0.85) / 0.10) * (1 - doc * 0.5)),
        "Amber": min(1, max(0, 1 - (evm_min - 0.88) / 0.10) * (1 + doc * 0.3)),
        "Red": min(1, max(0, (0.92 - evm_min) / 0.10) + doc * 0.4),
    }
    necessity = {k: max(0, v - 0.3) for k, v in possibility.items()}
    dominant = "Green"
    for b in list(possibility)[1:]:  # JS reduce with `>`: later key wins ties
        dominant = dominant if possibility[dominant] > possibility[b] else b
    return {
        "method_class": "Possibility_Theory",
        "status_color": dominant,
        "possibility": {k: round2(v) for k, v in possibility.items()},
        "necessity": {k: round2(v) for k, v in necessity.items()},
        "evidence_metric": (
            f"Possibility: {dominant} (Π={_js_str(round2(possibility[dominant]))}, "
            f"N={_js_str(round2(necessity[dominant]))})"
        ),
    }


# ------------------------------------------------------------ B2.16 Spherical Fuzzy Sets


def run_spherical_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Spherical_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    mu = max(0, min(0.95, (evm_min - 0.82) / 0.18))
    nu = max(0, min(0.95, (0.98 - evm_min) / 0.18)) * (1 + (si.get("docRiskScore") or 0) * 0.5)
    nu = min(0.95, nu)
    constraint = mu * mu + nu * nu
    if constraint > 1:
        sc = math.sqrt(constraint)
        mu /= sc
        nu /= sc
    pi = math.sqrt(max(0, 1 - mu * mu - nu * nu))
    score = mu - nu
    color = ("Green" if score >= 0.4 else "Yellow" if score >= 0.1
             else "Amber" if score >= -0.2 else "Red")
    return {
        "method_class": "Spherical_Fuzzy",
        "status_color": color,
        "mu": round2(mu),
        "nu": round2(nu),
        "pi": round2(pi),
        "score": round2(score),
        "evidence_metric": (
            f"SFS: μ={_js_str(round2(mu))} ν={_js_str(round2(nu))} π={_js_str(round2(pi))}"
        ),
    }


# ------------------------------------------------------------ B2.17 Fermatean Fuzzy Sets


def run_fermatean_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi")):
        return insufficient("Fermatean_Fuzzy")
    evm_min = min(si["cpi"], si["spi"])
    mu = max(0, min(0.99, (evm_min - 0.80) / 0.20))
    nu = max(0, min(0.99, (1.00 - evm_min) / 0.20))
    while mu ** 3 + nu ** 3 > 1:
        mu *= 0.95
        nu *= 0.95
    pi = (max(0, 1 - mu ** 3 - nu ** 3)) ** (1 / 3)
    score = mu - nu
    color = ("Green" if score >= 0.35 else "Yellow" if score >= 0.05
             else "Amber" if score >= -0.25 else "Red")
    return {
        "method_class": "Fermatean_Fuzzy",
        "status_color": color,
        "mu": round2(mu),
        "nu": round2(nu),
        "pi": round2(pi),
        "evidence_metric": (
            f"FFS: μ={_js_str(round2(mu))} ν={_js_str(round2(nu))} π={_js_str(round2(pi))}"
        ),
    }


# ------------------------------------------------------------ B2.18 MARCOS Ranking


def run_marcos(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("MARCOS")
    criteria = [
        {"value": si["cpi"], "ideal": 1.05, "anti": 0.80, "weight": 0.40},
        {"value": si["spi"], "ideal": 1.05, "anti": 0.80, "weight": 0.35},
        {"value": 1 - (si.get("docRiskScore") or 0), "ideal": 1.00, "anti": 0.30,
         "weight": 0.25},
    ]
    # RUN 10, BUCKET 2. The module set the anti-ideal utility to one minus the ideal utility, so
    # the two summed to one by construction, the score collapsed to an expression symmetric about
    # a half and bounded above by a third, and a perfect project divided by zero and scored
    # nothing. No input could produce a healthy reading and the ladder's top two rungs were
    # unreachable. That is not a threshold problem and no threshold is moved here: the band
    # boundaries below are exactly the ones the module already carried.
    #
    # The correction restores the method's own structure. In the published ranking method the two
    # utility degrees are the alternative's weighted sum measured against the ideal and against
    # the anti-ideal SEPARATELY, so they are two independent ratios rather than a number and its
    # complement. Each criterion is normalised against its own ideal, the weighted sum is formed
    # once for the project, once for the ideal reference and once for the anti-ideal reference,
    # and the utility functions and the score follow from those three sums.
    s_project = 0.0
    s_anti = 0.0
    for c in criteria:
        ideal = c["ideal"]
        if not ideal > 0:
            return insufficient("MARCOS")
        s_project += _clamp01(c["value"] / ideal) * c["weight"]
        s_anti += _clamp01(c["anti"] / ideal) * c["weight"]
    s_ideal = sum(c["weight"] for c in criteria)
    if not (s_ideal > 0 and s_anti > 0):
        return insufficient("MARCOS")
    k_ideal = s_project / s_ideal
    k_anti = s_project / s_anti
    denom_k = k_ideal + k_anti
    if not denom_k > 0:
        return insufficient("MARCOS")
    f_ideal = k_anti / denom_k
    f_anti = k_ideal / denom_k
    utility_ideal = k_ideal
    score = _jsdiv(denom_k,
                   1 + _jsdiv(1 - f_ideal, f_ideal) + _jsdiv(1 - f_anti, f_anti))
    score = _round3(score)
    color = ("Green" if score >= 0.65 else "Yellow" if score >= 0.50
             else "Amber" if score >= 0.35 else "Red")
    return {
        "method_class": "MARCOS",
        "status_color": color,
        "marcos_score": score,
        "utility_ideal": round2(utility_ideal),
        "evidence_metric": (
            f"MARCOS score: {_js_str(score)} "
            f"(utility vs ideal: {_js_str(round2(utility_ideal))})"
        ),
    }


# ------------------------------------------------------------ B2.19 CRITIC-TOPSIS


def run_critic_topsis(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("CRITIC_TOPSIS")
    criteria = [si["cpi"], si["spi"], 1 - (si.get("docRiskScore") or 0)]
    mean = sum(criteria) / len(criteria)
    stddev = math.sqrt(sum((v - mean) ** 2 for v in criteria) / len(criteria))
    weights = [abs(v - mean) / stddev if stddev > 0 else 1 / 3 for v in criteria]
    w_sum = sum(weights)
    weights = [w / w_sum for w in weights]
    ideal = [1.05, 1.05, 1.00]
    anti = [0.80, 0.80, 0.30]
    d_ideal = math.sqrt(sum(weights[i] * (criteria[i] - ideal[i]) ** 2
                            for i in range(len(criteria))))
    d_anti = math.sqrt(sum(weights[i] * (criteria[i] - anti[i]) ** 2
                           for i in range(len(criteria))))
    topsis = _round3(d_anti / (d_ideal + d_anti + 0.0001))
    color = ("Green" if topsis >= 0.65 else "Yellow" if topsis >= 0.50
             else "Amber" if topsis >= 0.35 else "Red")
    return {
        "method_class": "CRITIC_TOPSIS",
        "status_color": color,
        "topsis_score": topsis,
        "distance_ideal": _round3(d_ideal),
        "distance_anti": _round3(d_anti),
        "evidence_metric": (
            f"CRITIC-TOPSIS: {_js_str(topsis)} (d+ {_js_str(_round3(d_ideal))}, "
            f"d- {_js_str(_round3(d_anti))})"
        ),
    }


# ------------------------------------------------------------ B2.20 Hypersoft Sets


_HYPERSOFT = {
    "good-good-low": 0.90, "good-good-medium": 0.75, "good-good-high": 0.55,
    "good-fair-low": 0.70, "good-fair-medium": 0.55, "good-fair-high": 0.40,
    "fair-good-low": 0.70, "fair-good-medium": 0.55, "fair-good-high": 0.40,
    "fair-fair-low": 0.55, "fair-fair-medium": 0.40, "fair-fair-high": 0.30,
    "good-poor-low": 0.50, "poor-good-low": 0.50, "poor-poor-low": 0.30,
    "poor-fair-low": 0.35, "fair-poor-low": 0.35,
    "good-poor-medium": 0.35, "poor-good-medium": 0.35,
    "poor-poor-medium": 0.20, "poor-poor-high": 0.10,
    "fair-poor-high": 0.20, "poor-fair-high": 0.20,
    "good-poor-high": 0.25, "poor-good-high": 0.25,
}


def run_hypersoft_sets(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Hypersoft_Sets")
    doc = si.get("docRiskScore") or 0
    cost = "poor" if si["cpi"] < 0.90 else "fair" if si["cpi"] < 0.95 else "good"
    schedule = "poor" if si["spi"] < 0.90 else "fair" if si["spi"] < 0.95 else "good"
    risk = "high" if doc > 0.70 else "medium" if doc > 0.30 else "low"
    key = f"{cost}-{schedule}-{risk}"
    score = _HYPERSOFT.get(key, 0.35)
    color = ("Green" if score >= 0.70 else "Yellow" if score >= 0.50
             else "Amber" if score >= 0.30 else "Red")
    return {
        "method_class": "Hypersoft_Sets",
        "status_color": color,
        "attribute_combination": key,
        "score": score,
        "evidence_metric": f"Hypersoft [{key}]: score {_js_str(score)}",
    }


FUZZY_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "B2.10": ("Pythagorean_Fuzzy", run_pythagorean_fuzzy),
    "B2.11": ("Picture_Fuzzy", run_picture_fuzzy),
    "B2.12": ("Hesitant_Fuzzy", run_hesitant_fuzzy),
    "B2.13": ("Type2_Fuzzy", run_type2_fuzzy),
    "B2.14": ("Maximum_Entropy", run_maximum_entropy),
    "B2.15": ("Possibility_Theory", run_possibility_theory),
    "B2.16": ("Spherical_Fuzzy", run_spherical_fuzzy),
    "B2.17": ("Fermatean_Fuzzy", run_fermatean_fuzzy),
    "B2.18": ("MARCOS", run_marcos),
    "B2.19": ("CRITIC_TOPSIS", run_critic_topsis),
    "B2.20": ("Hypersoft_Sets", run_hypersoft_sets),
}
