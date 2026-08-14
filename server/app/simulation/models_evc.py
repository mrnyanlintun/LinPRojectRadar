"""
B2.2–B2.9 evidence-combination models, ported from assets/js/simulations.js (Modules 11–18).

Input contract (recorded in VALIDATION.md): these consume the assembled signal keys directly
from si — si["evm"] ({cpi, spi}), si["mc"] ({p80DeltaPct}), si["cusum"] ({breached}),
si["doc"] ({score}) — the browser's `existingSignals`. Presence is `is not None`, matching JS
object truthiness where an empty {} is a PRESENT signal. Scores use `or 0`, matching `|| 0`.

D1: THESE MODULES NOW ABSTAIN WHEN NO SIGNAL CONTRIBUTES, AND THE JAVASCRIPT COMPARISON NO
LONGER APPLIES TO THEM. They used to emit the AMBER "Insufficient signal data" result the
JavaScript emits, with BRB falling back to rule R0 and Quantum to default amplitudes. That was
a faithful port of a browser edge case; server-side it was the ONLY path, because `evm`, `mc`,
`cusum` and `doc` are the browser's `existingSignals` and nothing on the server assembles them.
Every project therefore received an evidence-combination colour derived from an empty evidence
set. Measured, that colour was wrong in both directions: it pulled a healthy project's
combination down and a distressed project's up. The fallbacks are removed rather than gated.
See VALIDATION.md and REPORT_2026-08-02_d1-implementation.md.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .arm_lineage import ARM_LINEAGE_BY_KEY, one_reading_per_body
from .fusion import BAND_SEVERITY


def _band(g: float, a: float, r: float) -> str:
    """The band a Green/Amber/Red distribution asserts: the state carrying most of it.

    Read off the distribution rather than recorded beside it at the branch that chose it, so an
    oracle and an implementation cannot both derive the expected band from one expression. Ties
    keep the more adverse state, matching the aggregations' own comparisons.
    """
    return "Red" if r >= a and r >= g else "Amber" if a >= g else "Green"
from .models import insufficient
from .rng import js_round, round2


# ------------------------------------------------------------------- RUN 20 CYCLE 9, ARCH.5
#
# EVERY MODULE IN THIS FILE READS THE SAME FOUR ASSEMBLED ARMS AND AGGREGATED THEM WITH EQUAL
# WEIGHT PER ARM. Three of those four arms are readings of ONE earned-value measurement, which
# cycle 7 established by execution and arm_lineage.py records. Equal weight per arm therefore
# gave one measurement three quarters of the vote.
#
# The correction introduces NO WEIGHT. The present arms are separated into independent bodies by
# the existing lineage contract and each body contributes ONE reading, the most adverse of its
# members, which is idempotent. Each module then runs ITS OWN arithmetic, unchanged, over the
# surviving readings. No band, membership, reliability, rule weight or boundary in this file is
# altered by any of it: what changed is which readings are aggregated against each other.
#
# THE SILENT REWEIGHTING IS DISCLOSED AT THE SAME TIME. Every aggregator here divides by the
# number of arms it happens to have, so an absent arm silently redistributes its share over the
# remainder and the same evidence gives a different answer according to how many arms exist. The
# division is kept -- a mean over the bodies actually in hand is the honest reading, and the
# alternative is a fabricated neutral for an absent arm, which this programme refuses -- but the
# counts are now REPORTED on every result, so a reader can see how many bodies stood behind the
# figure rather than inferring it from an arm count that says nothing about dependence.


def _dedupe(si, entries):
    """
    Reduce a module's present arms to one reading per independent body of evidence.

    `entries` is a list of (assembled-signal-key, band, payload) in the module's own evaluation
    order. Returns the surviving payloads in that same order, plus the audit trail. Order in,
    order out: the aggregations below are all sums, products or maxima and are therefore
    permutation invariant, and this function does not become the one place that is not.
    """
    records = [ARM_LINEAGE_BY_KEY[k] for k, _band, _p in entries]
    bands = [b for _k, b, _p in entries]
    sep = one_reading_per_body(records, bands, si)
    return [entries[i][2] for i in sep["kept"]], sep


def _lineage_fields(sep):
    """The audit trail every module in this file now carries."""
    return {
        "arms_present": sep["arms_present"],
        "bodies_of_evidence": sep["bodies_of_evidence"],
        "arms_suppressed_as_duplicate": sep["arms_suppressed_as_duplicate"],
        "evidence_bodies": sep["bodies"],
    }


def _evm(si):
    evm = si.get("evm")
    cpi = evm.get("cpi") if evm is not None else None
    spi = evm.get("spi") if evm is not None else None
    return cpi, spi


# ------------------------------------------------------------ B2.2 Rough Sets


def run_rough_sets(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    states = ["Green", "Amber", "Red"]
    entries: list[tuple[str, str, str]] = []
    cpi, spi = _evm(si)
    if cpi and spi:
        evm_min = min(cpi, spi)
        b = "Green" if evm_min >= 0.95 else "Amber" if evm_min >= 0.90 else "Red"
        entries.append(("evm", b, b))
    mc = si.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        b = "Green" if p80 <= 5 else "Amber" if p80 <= 10 else "Red"
        entries.append(("mc", b, b))
    cusum = si.get("cusum")
    if cusum is not None:
        b = "Red" if cusum.get("breached") else "Green"
        entries.append(("cusum", b, b))
    doc = si.get("doc")
    if doc is not None:
        score = doc.get("score") or 0
        b = "Green" if score < 0.30 else "Amber" if score < 0.70 else "Red"
        entries.append(("doc", b, b))

    # ARCH.5. The ratio below is a count of classes against the class TOTAL, so an earned-value
    # measurement read three ways occupied three quarters of it. On the cycle 7 fixture that is
    # exactly 0.75, the boundary the lower-approximation test sits on: the duplication decided
    # the band. One class per body of evidence now, and the denominator is the number of bodies.
    classes, _sep = _dedupe(si, entries)

    if not classes:
        # D1. The `or 1` that used to stand in for the denominator here made every ratio 0/1,
        # which put every state outside the lower approximation and produced "Indeterminate"
        # Amber from nothing. An empty evidence set has no classification.
        return insufficient("Rough_Sets_Classification")

    counts = {"Green": 0, "Amber": 0, "Red": 0}
    for c in classes:
        counts[c] += 1
    total = len(classes)

    lower = [s for s in states if counts[s] / total > 0.75]
    upper = [s for s in states if counts[s] > 0]
    boundary = [s for s in upper if s not in lower]

    if len(lower) == 1:
        classification = "Definite " + lower[0]
        status = lower[0]
    elif boundary:
        classification = "Borderline: " + " / ".join(boundary)
        status = "Red" if "Red" in boundary else "Amber"
    else:
        classification = "Indeterminate"
        status = "Amber"

    return {
        "method_class": "Rough_Sets_Classification",
        "status_color": status,
        "lower_approximation": lower,
        "upper_approximation": upper,
        "boundary_region": boundary,
        "classification": classification,
        "signal_votes": counts,
        "total_signals": total,
        **_lineage_fields(_sep),
        "evidence_metric": (
            f"{classification} (Green {counts['Green']}, Amber {counts['Amber']}, "
            f"Red {counts['Red']} of {total} signals)"
        ),
    }


# ------------------------------------------------------------ B2.3 Neutrosophic Logic


def run_neutrosophic(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    entries: list[tuple[str, str, dict]] = []
    cpi, spi = _evm(si)
    if cpi and spi:
        evm_min = min(cpi, spi)
        if evm_min >= 0.95:
            entries.append(("evm", "Green", {"T": 0.85, "I": 0.10, "F": 0.05, "source": "EVM", "state": "Green"}))
        elif evm_min >= 0.90:
            entries.append(("evm", "Amber", {"T": 0.70, "I": 0.20, "F": 0.10, "source": "EVM", "state": "Amber"}))
        else:
            entries.append(("evm", "Red", {"T": 0.75, "I": 0.15, "F": 0.10, "source": "EVM", "state": "Red"}))
    mc = si.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        if p80 <= 5:
            entries.append(("mc", "Green", {"T": 0.80, "I": 0.10, "F": 0.10,
                        "source": "Forecast", "state": "Green"}))
        elif p80 <= 10:
            entries.append(("mc", "Amber", {"T": 0.65, "I": 0.25, "F": 0.10,
                        "source": "Forecast", "state": "Amber"}))
        else:
            entries.append(("mc", "Red", {"T": 0.75, "I": 0.15, "F": 0.10,
                        "source": "Forecast", "state": "Red"}))
    cusum = si.get("cusum")
    if cusum is not None:
        if cusum.get("breached"):
            entries.append(("cusum", "Red", {"T": 0.90, "I": 0.05, "F": 0.05,
                        "source": "CUSUM", "state": "Red"}))
        else:
            entries.append(("cusum", "Green", {"T": 0.80, "I": 0.10, "F": 0.10,
                        "source": "CUSUM", "state": "Green"}))
    doc = si.get("doc")
    if doc is not None:
        s = doc.get("score") or 0
        if s < 0.30:
            entries.append(("doc", "Green", {"T": 0.85, "I": 0.10, "F": 0.05,
                        "source": "DocRisk", "state": "Green"}))
        elif s < 0.70:
            entries.append(("doc", "Amber", {"T": 0.65, "I": 0.25, "F": 0.10,
                        "source": "DocRisk", "state": "Amber"}))
        else:
            entries.append(("doc", "Red", {"T": 0.75, "I": 0.15, "F": 0.10,
                        "source": "DocRisk", "state": "Red"}))

    # ARCH.5. The three earned-value readings each contributed a T, an I and an F of their own,
    # and the T aggregation is a probabilistic OR: three readings of one measurement drove T
    # toward 1 on evidence of one measurement. One component per body of evidence now.
    components, _sep = _dedupe(si, entries)

    if not components:
        return insufficient("Neutrosophic_Logic")

    t = 0.0
    for c in components:
        t = 1 - (1 - t) * (1 - c["T"])
    i = 1.0
    for c in components:
        i = i * c["I"]
    f = 1.0
    for c in components:
        f = f * c["F"]
    total = (t + i + f) or 1
    t = round2(t / total)
    i = round2(i / total)
    f = round2(f / total)

    red_count = sum(1 for c in components if c["state"] == "Red")
    amber_count = sum(1 for c in components if c["state"] == "Amber")
    # RUN 20 CYCLE 9, ARCH.5, AND THIS IS A CORRECTION OF THE SILENT REWEIGHTING, NOT A NEW
    # THRESHOLD. The rule was `>= 2`, an ABSOLUTE count written when four arms were counted, so
    # it meant two of four: one half. Left as an absolute count it would mean two of two --
    # unanimity -- once the three earned-value readings became one body, and a project reading
    # Red on its earned value with a clean document score would have reported GREEN. That is
    # false suppression, and it is the failure this cycle is least willing to introduce. The
    # threshold is therefore expressed as the SHARE IT ALWAYS WAS, one half of the components
    # counted, which reproduces `>= 2` exactly on four components and is stable under any other
    # number. It also repairs the pre-existing reweighting: with three arms present the old
    # absolute count silently demanded two thirds, and with two it demanded unanimity.
    n_components = len(components)
    status = ("Red" if red_count / n_components >= 0.5
              else "Amber" if amber_count / n_components >= 0.5 else "Green")
    if i > 0.30:
        status = "Amber" if status == "Green" else status
    level = "High" if i > 0.30 else "Moderate" if i > 0.15 else "Low"

    return {
        "method_class": "Neutrosophic_Logic",
        "status_color": status,
        "T": t, "I": i, "F": f,
        "indeterminacy_level": level,
        "signal_components": components,
        **_lineage_fields(_sep),
        "evidence_metric": (
            f"T={_num_str(t)} I={_num_str(i)} F={_num_str(f)}, Indeterminacy: {level}"
        ),
    }


# ------------------------------------------------------------ B2.4 Interval Fuzzy Sets


def _mem_amber(v):
    if v <= 0.85 or v >= 0.98:
        return 0
    if v <= 0.92:
        return (v - 0.85) / (0.92 - 0.85)
    return (0.98 - v) / (0.98 - 0.92)


def _mem_red(v):
    if v >= 0.92:
        return 0
    if v <= 0.85:
        return 1
    return (0.92 - v) / (0.92 - 0.85)


def _mem_green(v):
    if v <= 0.92:
        return 0
    if v >= 0.97:
        return 1
    return (v - 0.92) / (0.97 - 0.92)


def _mem_interval(fn, lo, hi):
    a, b = fn(lo), fn(hi)
    return [min(a, b), max(a, b)]


def run_interval_fuzzy(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    ev_unc, ac_unc = 0.02, 0.01
    # RUN 20 CYCLE 9, ARCH.5, AND THIS MODULE'S DUPLICATION IS INSIDE A SINGLE ARM. It reads no
    # forecast, trend or document arm at all: it reads the cost index and the schedule index, and
    # those are TWO READINGS OF ONE EARNED-VALUE MEASUREMENT, sharing the earned value outright.
    # The aggregation below is a per-band MAX over the intervals, so the two readings could
    # contribute to DIFFERENT bands and produce an aggregate membership profile that neither
    # index asserts on its own -- a fabricated third reading of one measurement.
    #
    # The idempotent operator applies here without needing the body separation, because there is
    # only ever one body: the MORE ADVERSE of the two index readings is kept and the other is
    # suppressed. A tie keeps the cost index, which is the module's own evaluation order. No
    # membership function, no boundary and no uncertainty band is altered.
    candidates = []
    cpi, spi = _evm(si)
    if cpi:
        candidates.append(("cost index", cpi, cpi - ev_unc - ac_unc, cpi + ev_unc + ac_unc))
    if spi:
        candidates.append(("schedule index", spi, spi - ev_unc, spi + ev_unc))
    # The band an index reading asserts, read off the same membership functions the aggregation
    # uses rather than recorded beside them, so an oracle cannot be compared against itself.
    def _index_band(lo, hi):
        g = sum(_mem_interval(_mem_green, lo, hi)) / 2
        a = sum(_mem_interval(_mem_amber, lo, hi)) / 2
        r = sum(_mem_interval(_mem_red, lo, hi)) / 2
        return "Red" if r >= a and r >= g else "Amber" if a >= g else "Green"

    intervals = []
    suppressed = []
    if candidates:
        ranked = [(BAND_SEVERITY[_index_band(lo, hi)], k, name, lo, hi)
                  for k, (name, _v, lo, hi) in enumerate(candidates)]
        worst = max(r[0] for r in ranked)
        keep = next(r for r in ranked if r[0] == worst)
        suppressed = [r[2] for r in ranked if r is not keep]
        _sev, _k, _name, lo, hi = keep
        intervals.append({"green": _mem_interval(_mem_green, lo, hi),
                          "amber": _mem_interval(_mem_amber, lo, hi),
                          "red": _mem_interval(_mem_red, lo, hi),
                          "source": _name})

    if not intervals:
        return insufficient("Interval_Fuzzy_Sets")

    def agg(key, idx):
        out = 0
        for it in intervals:
            out = max(out, it[key][idx])
        return out

    agg_green = [agg("green", 0), agg("green", 1)]
    agg_amber = [agg("amber", 0), agg("amber", 1)]
    agg_red = [agg("red", 0), agg("red", 1)]

    green_mid = (agg_green[0] + agg_green[1]) / 2
    amber_mid = (agg_amber[0] + agg_amber[1]) / 2
    red_mid = (agg_red[0] + agg_red[1]) / 2
    status = ("Red" if red_mid >= amber_mid and red_mid >= green_mid
              else "Amber" if amber_mid >= green_mid else "Green")

    width = round2((agg_red[1] - agg_red[0]) + (agg_amber[1] - agg_amber[0]))

    def fmt(interval):
        return ", ".join(str(x) for x in
                         [_num_str(round2(interval[0])), _num_str(round2(interval[1]))])

    return {
        "method_class": "Interval_Fuzzy_Sets",
        "status_color": status,
        "green_interval": agg_green,
        "amber_interval": agg_amber,
        "red_interval": agg_red,
        "uncertainty_width": width,
        "uncertainty_level": ("High" if width > 0.3 else
                              "Moderate" if width > 0.15 else "Low"),
        # ARCH.5 audit trail. Both indices are ONE body of evidence, so the module reports which
        # reading it kept and which it suppressed rather than presenting an aggregate profile as
        # though two sources had spoken.
        "arms_present": 1,
        "bodies_of_evidence": 1,
        "index_readings_present": len(candidates),
        "index_reading_used": intervals[0]["source"],
        "index_readings_suppressed_as_same_body": suppressed,
        "evidence_metric": (
            f"Green [{fmt(agg_green)}] Amber [{fmt(agg_amber)}] Red [{fmt(agg_red)}]"
        ),
    }


def _num_str(n) -> str:
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return str(n)


# ------------------------------------------------------------ B2.5 Z-numbers


def run_z_numbers(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    entries: list[tuple[str, str, dict]] = []
    cpi, spi = _evm(si)
    if cpi and spi:
        evm_min = min(cpi, spi)
        restriction = "Green" if evm_min >= 0.95 else "Amber" if evm_min >= 0.90 else "Red"
        entries.append(("evm", restriction,
                        {"source": "EVM", "restriction": restriction, "reliability": 0.85}))
    cusum = si.get("cusum")
    if cusum is not None:
        restriction = "Red" if cusum.get("breached") else "Green"
        entries.append(("cusum", restriction,
                        {"source": "CUSUM", "restriction": restriction, "reliability": 0.90}))
    doc = si.get("doc")
    if doc is not None:
        score = doc.get("score") or 0
        restriction = "Red" if score >= 0.70 else "Amber" if score >= 0.30 else "Green"
        entries.append(("doc", restriction,
                        {"source": "DocRisk", "restriction": restriction, "reliability": 0.65}))
    mc = si.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        restriction = "Red" if p80 > 10 else "Amber" if p80 > 5 else "Green"
        entries.append(("mc", restriction,
                        {"source": "MonteCarlo", "restriction": restriction,
                         "reliability": 0.88}))

    # ARCH.5. The comparison below is a SUM of reliabilities per band, so three readings of one
    # earned-value measurement summed three reliabilities against the document score's one and
    # the measurement won on count rather than on evidence. One reading per body now; the kept
    # reading brings its own reliability and no reliability is combined, discounted or invented.
    signals, _sep = _dedupe(si, entries)

    if not signals:
        return insufficient("Z_Numbers")

    total_red = sum(s["reliability"] for s in signals if s["restriction"] == "Red")
    total_amber = sum(s["reliability"] for s in signals if s["restriction"] == "Amber")
    total_green = sum(s["reliability"] for s in signals if s["restriction"] == "Green")
    avg_rel = sum(s["reliability"] for s in signals) / len(signals)

    status = ("Red" if total_red >= total_amber and total_red >= total_green
              else "Amber" if total_amber >= total_green else "Green")

    return {
        "method_class": "Z_Numbers",
        "status_color": status,
        "weighted_red": round2(total_red),
        "weighted_amber": round2(total_amber),
        "weighted_green": round2(total_green),
        "avg_reliability": round2(avg_rel),
        "signal_count": len(signals),
        "signals": signals,
        **_lineage_fields(_sep),
        "evidence_metric": (
            f"Reliability-weighted: Red {_num_str(round2(total_red))} · "
            f"Amber {_num_str(round2(total_amber))} · "
            f"Green {_num_str(round2(total_green))} · "
            f"Avg reliability {int(js_round(avg_rel * 100))}%"
        ),
    }


# ------------------------------------------------------------ B2.6 PLTS


def run_plts(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    entries: list[tuple[str, str, dict]] = []
    cpi, spi = _evm(si)
    if cpi and spi:
        evm_min = min(cpi, spi)
        if evm_min >= 0.97:
            g, a, r = 0.90, 0.08, 0.02
        elif evm_min >= 0.95:
            g, a, r = 0.70, 0.25, 0.05
        elif evm_min >= 0.92:
            g, a, r = 0.15, 0.70, 0.15
        elif evm_min >= 0.90:
            g, a, r = 0.05, 0.65, 0.30
        elif evm_min >= 0.87:
            g, a, r = 0.02, 0.28, 0.70
        else:
            g, a, r = 0.02, 0.08, 0.90
        entries.append(("evm", _band(g, a, r),
                        {"source": "EVM", "Green": g, "Amber": a, "Red": r}))
    cusum = si.get("cusum")
    if cusum is not None:
        if cusum.get("breached"):
            entries.append(("cusum", _band(0.02, 0.13, 0.85),
                        {"source": "CUSUM", "Green": 0.02, "Amber": 0.13, "Red": 0.85}))
        else:
            entries.append(("cusum", _band(0.80, 0.15, 0.05),
                        {"source": "CUSUM", "Green": 0.80, "Amber": 0.15, "Red": 0.05}))
    doc = si.get("doc")
    if doc is not None:
        s = doc.get("score") or 0
        if s < 0.30:
            entries.append(("doc", _band(0.85, 0.12, 0.03),
                        {"source": "DocRisk", "Green": 0.85, "Amber": 0.12, "Red": 0.03}))
        elif s < 0.70:
            entries.append(("doc", _band(0.10, 0.70, 0.20),
                        {"source": "DocRisk", "Green": 0.10, "Amber": 0.70, "Red": 0.20}))
        else:
            entries.append(("doc", _band(0.03, 0.17, 0.80),
                        {"source": "DocRisk", "Green": 0.03, "Amber": 0.17, "Red": 0.80}))
    mc = si.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        if p80 <= 5:
            entries.append(("mc", _band(0.80, 0.15, 0.05),
                        {"source": "MC", "Green": 0.80, "Amber": 0.15, "Red": 0.05}))
        elif p80 <= 10:
            entries.append(("mc", _band(0.08, 0.67, 0.25),
                        {"source": "MC", "Green": 0.08, "Amber": 0.67, "Red": 0.25}))
        else:
            entries.append(("mc", _band(0.03, 0.17, 0.80),
                        {"source": "MC", "Green": 0.03, "Amber": 0.17, "Red": 0.80}))

    # ARCH.5. The aggregation below is a MEAN over the sources, so three distributions derived
    # from one earned-value measurement pulled the mean three times as hard as the document
    # score. One distribution per body of evidence now, and the mean is over the bodies.
    plts, _sep = _dedupe(si, entries)

    if not plts:
        return insufficient("PLTS")

    n = len(plts)
    agg_g = sum(p["Green"] for p in plts) / n
    agg_a = sum(p["Amber"] for p in plts) / n
    agg_r = sum(p["Red"] for p in plts) / n
    status = ("Red" if agg_r >= agg_a and agg_r >= agg_g
              else "Amber" if agg_a >= agg_g else "Green")
    return {
        "method_class": "PLTS",
        "status_color": status,
        "p_green": int(js_round(agg_g * 100)),
        "p_amber": int(js_round(agg_a * 100)),
        "p_red": int(js_round(agg_r * 100)),
        "sources": plts,
        **_lineage_fields(_sep),
        "evidence_metric": (
            f"P(Green)={int(js_round(agg_g * 100))}% · "
            f"P(Amber)={int(js_round(agg_a * 100))}% · "
            f"P(Red)={int(js_round(agg_r * 100))}%"
        ),
    }


# ------------------------------------------------------------ B2.7 Plithogenic Sets


def run_plithogenic(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    attributes = []
    cpi, spi = _evm(si)
    if cpi and spi:
        evm_min = min(cpi, spi)
        state = "Green" if evm_min >= 0.95 else "Amber" if evm_min >= 0.90 else "Red"
        membership = 0.85 if evm_min >= 0.95 else 0.70 if evm_min >= 0.90 else 0.80
        contradiction = 0.0 if state == "Red" else 1.0 if state == "Green" else 0.5
        attributes.append({"name": "EVM", "state": state,
                           "membership": membership, "contradiction": contradiction})
    cusum = si.get("cusum")
    if cusum is not None:
        state = "Red" if cusum.get("breached") else "Green"
        attributes.append({"name": "CUSUM", "state": state, "membership": 0.88,
                           "contradiction": 0.0 if state == "Red" else 1.0})
    doc = si.get("doc")
    if doc is not None:
        s = doc.get("score") or 0
        state = "Red" if s >= 0.70 else "Amber" if s >= 0.30 else "Green"
        contradiction = 0.0 if state == "Red" else 1.0 if state == "Green" else 0.5
        attributes.append({"name": "DocRisk", "state": state, "membership": 0.75,
                           "contradiction": contradiction})
    mc = si.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        state = "Red" if p80 > 10 else "Amber" if p80 > 5 else "Green"
        contradiction = 0.0 if state == "Red" else 1.0 if state == "Green" else 0.5
        attributes.append({"name": "MC", "state": state, "membership": 0.82,
                           "contradiction": contradiction})

    if not attributes:
        return insufficient("Plithogenic_Sets")

    red_s = amber_s = green_s = 0.0
    for a in attributes:
        w = a["membership"] * (1 - a["contradiction"] * 0.5)
        if a["state"] == "Red":
            red_s += w
        elif a["state"] == "Amber":
            amber_s += w
        else:
            green_s += w

    avg_c = sum(a["contradiction"] for a in attributes) / len(attributes)
    status = ("Red" if red_s >= amber_s and red_s >= green_s
              else "Amber" if amber_s >= green_s else "Green")
    return {
        "method_class": "Plithogenic_Sets",
        "status_color": status,
        "red_score": round2(red_s),
        "amber_score": round2(amber_s),
        "green_score": round2(green_s),
        "avg_contradiction": round2(avg_c),
        "contradiction_level": ("High" if avg_c > 0.6 else
                                "Moderate" if avg_c > 0.3 else "Low"),
        "attributes": attributes,
        "evidence_metric": (
            f"Plithogenic scores, Red: {_num_str(round2(red_s))} · "
            f"Amber: {_num_str(round2(amber_s))} · "
            f"Green: {_num_str(round2(green_s))} · "
            f"Contradiction: {int(js_round(avg_c * 100))}%"
        ),
    }


# ------------------------------------------------------------ B2.8 Belief Rule Base


def run_brb(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    cpi, spi = _evm(si)
    cusum = si.get("cusum")
    breached = bool(cusum.get("breached")) if cusum is not None else False
    doc = si.get("doc")
    doc_score = (doc.get("score") or 0) if doc is not None else 0
    mc = si.get("mc")
    p80 = (mc.get("p80DeltaPct") or 0) if mc is not None else 0

    evm_state = (None if not cpi or not spi
                 else "Green" if min(cpi, spi) >= 0.95
                 else "Amber" if min(cpi, spi) >= 0.90 else "Red")
    doc_state = "Red" if doc_score >= 0.70 else "Amber" if doc_score >= 0.30 else "Green"
    mc_state = "Red" if p80 > 10 else "Amber" if p80 > 5 else "Green"

    # ---------------------------------------------------------- RUN 20 CYCLE 9, ARCH.5
    #
    # THIS MODULE'S DUPLICATION IS BUILT INTO THE RULE ANTECEDENTS THEMSELVES, WHICH IS WHY IT
    # NEEDS ITS OWN DETERMINATION AND NOT THE SHARED HELPER. Four rules -- R1, R3 and R6 -- fire
    # on an EVM state CONJOINED WITH a cumulative-sum breach, and R2, R5, R7 and R8 on the same
    # state conjoined with the ABSENCE of one. The breach is treated as a second, corroborating
    # fact. It is not: cycle 7 established by execution that the cumulative sum runs over the
    # SCHEDULE INDEX HISTORY whose last point is this period's index, so the breach flag and the
    # EVM state are two readings of one earned-value measurement. A rule base that conditions on
    # both is counting one measurement twice, and it is doing so at the point where it decides
    # which rule fires at all.
    #
    # THE WEIGHT-FREE REPAIR IS THE SAME IDEMPOTENT OPERATOR, APPLIED TO THE ANTECEDENT RATHER
    # THAN TO THE AGGREGATION. The earned-value body reads ONE band: the more adverse of the EVM
    # state and the trend reading. That band is what the rules condition on, and the breach stops
    # acting as a separate antecedent. No rule, belief mass or rule weight is edited: R1, R3 and
    # R6 simply stop being reachable while an EVM state exists, which is every case in which any
    # rule fires at all, because every rule in the base conditions on an EVM state.
    #
    # NO EVIDENCE IS LOST BY THIS. A breach with a Green index no longer selects R6's "Green plus
    # breach" mass; it makes the earned-value body read RED and selects R2, which is MORE adverse
    # rather than less. The direction matters: this cycle will not introduce a repair that lets a
    # module read greener than its evidence.
    trend_state = "Red" if breached else "Green"
    body_state = evm_state
    if evm_state is not None:
        body_state = ("Red" if "Red" in (evm_state, trend_state)
                      else "Amber" if "Amber" in (evm_state, trend_state) else "Green")
    evm_state, breached = body_state, False

    rules = [
        {"id": "R1", "desc": "Earned-value body Red, with a trend breach as a separate antecedent "
                 "(unreachable since Run 20 cycle 9: the breach is a reading of that same body)",
         "condition": evm_state == "Red" and breached,
         "belief": {"Green": 0.02, "Amber": 0.08, "Red": 0.90}, "weight": 1.00},
        {"id": "R2", "desc": "Earned-value body Red",
         "condition": evm_state == "Red" and not breached,
         "belief": {"Green": 0.05, "Amber": 0.25, "Red": 0.70}, "weight": 0.85},
        {"id": "R3", "desc": "Earned-value body Amber, with a trend breach as a separate antecedent "
                 "(unreachable since Run 20 cycle 9)",
         "condition": evm_state == "Amber" and breached,
         "belief": {"Green": 0.05, "Amber": 0.30, "Red": 0.65}, "weight": 0.90},
        {"id": "R4", "desc": "Earned-value body Amber, document evidence Red",
         "condition": evm_state == "Amber" and not breached and doc_state == "Red",
         "belief": {"Green": 0.08, "Amber": 0.42, "Red": 0.50}, "weight": 0.80},
        {"id": "R5", "desc": "Earned-value body Amber, document evidence not Red",
         "condition": evm_state == "Amber" and not breached and doc_state != "Red",
         "belief": {"Green": 0.10, "Amber": 0.70, "Red": 0.20}, "weight": 0.75},
        {"id": "R6", "desc": "Earned-value body Green, with a trend breach as a separate antecedent "
                 "(unreachable since Run 20 cycle 9)",
         "condition": evm_state == "Green" and breached,
         "belief": {"Green": 0.15, "Amber": 0.55, "Red": 0.30}, "weight": 0.85},
        {"id": "R7", "desc": "Earned-value body Green, document evidence Green",
         "condition": evm_state == "Green" and not breached and doc_state == "Green",
         "belief": {"Green": 0.85, "Amber": 0.12, "Red": 0.03}, "weight": 0.90},
        {"id": "R8", "desc": "Earned-value body Green, document evidence not Green",
         "condition": evm_state == "Green" and not breached and doc_state != "Green",
         "belief": {"Green": 0.50, "Amber": 0.40, "Red": 0.10}, "weight": 0.70},
    ]
    matched = [r for r in rules if r["condition"]]
    if not matched:
        # D1. Every rule above is conditioned on an EVM state, so no EVM means no rule fires.
        # The R0 fallback then supplied a near-uniform belief mass and a colour drawn from it.
        # A rule base with no activated rule has concluded nothing.
        return insufficient("Belief_Rule_Base")

    total_w = sum(r["weight"] for r in matched)
    agg_g = sum(r["belief"]["Green"] * r["weight"] for r in matched) / total_w
    agg_a = sum(r["belief"]["Amber"] * r["weight"] for r in matched) / total_w
    agg_r = sum(r["belief"]["Red"] * r["weight"] for r in matched) / total_w

    status = ("Red" if agg_r >= agg_a and agg_r >= agg_g
              else "Amber" if agg_a >= agg_g else "Green")
    return {
        "method_class": "Belief_Rule_Base",
        "status_color": status,
        "belief_green": int(js_round(agg_g * 100)),
        "belief_amber": int(js_round(agg_a * 100)),
        "belief_red": int(js_round(agg_r * 100)),
        "rules_matched": len(matched),
        "matched_rules": [{"id": m["id"], "desc": m["desc"], "weight": m["weight"]}
                          for m in matched],
        "mc_state": mc_state,
        # ARCH.5 audit trail. The trend arm is a reading of the earned-value body, never a
        # second body, so the rule base sees two bodies at most: earned value and document.
        "arms_present": 4 - sum(1 for x in (si.get("mc"), si.get("cusum"), si.get("doc"))
                                if x is None),
        "bodies_of_evidence": 2 if si.get("doc") is not None else 1,
        "earned_value_body_state": body_state,
        "trend_reading_folded_into_earned_value_body": trend_state,
        "evidence_metric": (
            f"BRB belief: Green {int(js_round(agg_g * 100))}% · "
            f"Amber {int(js_round(agg_a * 100))}% · Red {int(js_round(agg_r * 100))}% · "
            f"{len(matched)} rule(s) activated"
        ),
    }


# ------------------------------------------------------------ B2.9 Quantum Probability


def run_quantum_probability(si: dict, rand: Callable[[], float],
                            period_cutoff) -> dict[str, Any]:
    cpi, spi = _evm(si)
    cusum = si.get("cusum")
    doc = si.get("doc")
    if not (cpi and spi) and cusum is None and doc is None:
        # D1. The defaults below are not neutral: an absent EVM defaulted evm_min to 1.0, an
        # absent CUSUM to "no breach" and an absent doc risk to 0. All three read as good news,
        # so with no evidence at all the amplitudes resolved Green. Removed.
        return insufficient("Quantum_Probability")

    breached = bool(cusum.get("breached")) if cusum is not None else False
    doc_score = (doc.get("score") or 0) if doc is not None else 0

    evm_min = min(cpi, spi) if (cpi and spi) else 1.0
    p_green_evm = 0.80 if evm_min >= 0.95 else 0.10 if evm_min >= 0.90 else 0.05
    p_red_evm = 0.05 if evm_min >= 0.95 else 0.20 if evm_min >= 0.90 else 0.80
    p_green_cusum = 0.05 if breached else 0.80
    p_red_cusum = 0.85 if breached else 0.05
    p_green_doc = 0.85 if doc_score < 0.30 else 0.10 if doc_score < 0.70 else 0.03
    p_red_doc = 0.03 if doc_score < 0.30 else 0.20 if doc_score < 0.70 else 0.80

    alpha_green = math.sqrt((p_green_evm + p_green_cusum + p_green_doc) / 3)
    gamma_red = math.sqrt((p_red_evm + p_red_cusum + p_red_doc) / 3)

    red_count = sum(1 for p in (p_red_evm, p_red_cusum, p_red_doc) if p > 0.5)
    green_count = sum(1 for p in (p_green_evm, p_green_cusum, p_green_doc) if p > 0.5)
    theta = (abs(red_count - green_count) / 3) * math.pi
    interference = 2 * alpha_green * gamma_red * math.cos(theta)

    p_red_q = max(0, min(1, gamma_red * gamma_red + interference * 0.3))
    p_green_q = max(0, min(1, alpha_green * alpha_green - interference * 0.3))
    p_amber_q = max(0, 1 - p_red_q - p_green_q)

    itype = ("Constructive" if math.cos(theta) > 0.3
             else "Destructive" if math.cos(theta) < -0.3 else "Neutral")
    status = ("Red" if p_red_q >= p_amber_q and p_red_q >= p_green_q
              else "Amber" if p_amber_q >= p_green_q else "Green")
    deg = int(js_round(theta * 180 / math.pi))
    return {
        "method_class": "Quantum_Probability",
        "status_color": status,
        "p_green": int(js_round(p_green_q * 100)),
        "p_amber": int(js_round(p_amber_q * 100)),
        "p_red": int(js_round(p_red_q * 100)),
        "interference_type": itype,
        "interference_magnitude": round2(abs(interference)),
        "phase_angle_deg": deg,
        "alpha_green": round2(alpha_green),
        "gamma_red": round2(gamma_red),
        "evidence_metric": (
            f"Q-P(Green)={int(js_round(p_green_q * 100))}% · "
            f"Q-P(Amber)={int(js_round(p_amber_q * 100))}% · "
            f"Q-P(Red)={int(js_round(p_red_q * 100))}% · "
            f"{itype} interference · Phase {deg}°"
        ),
    }


EVC_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "B2.2": ("Rough_Sets_Classification", run_rough_sets),
    "B2.3": ("Neutrosophic_Logic", run_neutrosophic),
    "B2.4": ("Interval_Fuzzy_Sets", run_interval_fuzzy),
    "B2.5": ("Z_Numbers", run_z_numbers),
    "B2.6": ("PLTS", run_plts),
    "B2.7": ("Plithogenic_Sets", run_plithogenic),
    "B2.8": ("Belief_Rule_Base", run_brb),
    "B2.9": ("Quantum_Probability", run_quantum_probability),
}
