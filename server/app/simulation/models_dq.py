"""
Group C data-integrity models (C1.1–C1.7), ported from assets/js/simulations.js Cat 9.

Group C computes but does NOT contribute to project status — that exclusion lives in
compute.py's category rollup and is asserted by Guarantee 4 of tools/test_simulation.py.

C1.2 Data Timeliness is the one module in the instrument that read the wall clock
(`new Date()` at simulations.js:2377). The port takes `period_cutoff` as its reference date —
the same documents must produce the same result on any day. The browser comparison patched the
Date constructor so a no-argument `new Date()` returned the cutoff, making the JS output a
fixed target; that patch and this substitution are recorded in VALIDATION.md.

C1.4 and C1.7 receive `(si, project)` in the browser and read `project.events`. Server
contract: the event log rides on si["events"], a list of {event, at} dicts.

D1: THE EVENT LOG IS NOW SUPPLIED AND THE STUBS ARE GONE. Until D1 nothing assembled
si["events"], so C1.4 reported "0 events recorded" and a Red band on every project, and C1.7
emitted the Yellow "upload more documents" stub on every project, both about a platform that
had been recording events in exactly this shape all along. `documents.py` now passes the
project's event log in. An ABSENT log abstains, because a caller that supplied no log has said
nothing about the project; an EMPTY log is evidence and is reported as such. C1.7 additionally
abstains below two extraction events, since one point establishes no interval. The JavaScript
comparison no longer applies to either module; see VALIDATION.md.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .band_display import band_figure
from .models import ABSTAIN_MALFORMED_INPUT, check_inputs, insufficient
from .models_ext import _js_date_ms, _js_str
from .rng import js_round, round2

_round3 = lambda v: js_round(v * 1000) / 1000  # noqa: E731


# ------------------------------------------------------------ C1.1 Missing Data Index


_CORE_FIELDS = ("bac", "ev", "ac", "pv", "cpi", "spi", "docRiskScore",
                "actualPctComplete", "plannedPctComplete", "baselineStart", "baselineEnd")


def run_missing_data_index(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    present = sum(1 for f in _CORE_FIELDS if si.get(f) is not None)
    missing_ratio = 1 - (present / len(_CORE_FIELDS))
    missing_count = len(_CORE_FIELDS) - present
    color = ("Green" if missing_ratio <= 0.10 else "Yellow" if missing_ratio <= 0.25
             else "Amber" if missing_ratio <= 0.45 else "Red")
    pct = int(js_round((1 - missing_ratio) * 100))
    return {
        "method_class": "Missing_Data_Index",
        "status_color": color,
        "missing_count": missing_count,
        "total_fields": len(_CORE_FIELDS),
        "completeness_pct": pct,
        "evidence_metric": (
            f"{missing_count} of {len(_CORE_FIELDS)} core fields missing ({pct}% complete)"
        ),
    }


# ------------------------------------------------------------ C1.2 Data Timeliness Score


def run_data_timeliness(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not si.get("docDate"):
        return insufficient("Data_Timeliness_Score")
    doc_ms = _js_date_ms(si["docDate"])
    now_ms = _js_date_ms(str(period_cutoff))
    if doc_ms is None or now_ms is None:
        return insufficient("Data_Timeliness_Score")
    days = math.floor((now_ms - doc_ms) / 86400000)
    # RUN 20, P0B. There was no lower guard on the age at all. A document dated a year after the
    # period cutoff reported an age of minus three hundred and sixty five days, banded Green,
    # which is the freshest reading the module can give, and told the reader the document was
    # "minus 365 days ago". A mistyped or forward-dated document therefore bought the best
    # possible evidence-quality reading. Specification 9.2 requires future-dated records to
    # receive explicit invalid or review handling, so they are refused rather than banded.
    if days < 0:
        return insufficient(
            "Data_Timeliness_Score",
            "The most recent document is dated after the end of this reporting period. A record "
            "cannot be newer than the period it is reported in, so its age is not read as "
            "evidence of freshness. Check the document date.",
            ABSTAIN_MALFORMED_INPUT)
    color = ("Green" if days <= 30 else "Yellow" if days <= 60
             else "Amber" if days <= 90 else "Red")
    return {
        "method_class": "Data_Timeliness_Score",
        "status_color": color,
        "days_since_last_doc": days,
        "last_doc_date": si["docDate"],
        "evidence_metric": (
            f"Last document: {si['docDate']} ({days} days ago"
            + (", data may be stale" if days > 60 else "") + ")"
        ),
    }


# ------------------------------------------------------------ C1.3 Source Reliability


_SOURCE_WEIGHTS = {
    "pay_application": 0.90, "contract_value": 0.95,
    "schedule_of_values": 0.85, "time_phased_schedule": 0.80,
    "monthly_report": 0.75, "change_order": 0.90,
    "rfi": 0.65, "submittal": 0.65, "field_report": 0.60,
    "oac_minutes": 0.55, "inspection_report": 0.70,
    "derived": 0.40,
}


def _doc_type(src):
    return src[-1].get("docType") if isinstance(src, list) else src.get("docType")


def run_source_reliability(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    sources = si.get("sources")
    if not sources or len(sources) == 0:
        return insufficient("Source_Reliability_Weighting")
    weights = []
    for key in sources:  # insertion order; do not sort
        dt = _doc_type(sources[key])
        if dt:
            weights.append(_SOURCE_WEIGHTS.get(dt) or 0.50)
    if not weights:
        return insufficient("Source_Reliability_Weighting")
    # RUN 135, FINDING S5. THE BAND CAME OFF A ROUNDED AVERAGE, so the rounding decided the
    # answer. `avg = round2(...)` ran before the ladder: 159 sources at 0.80 and one derived
    # field at 0.40 average to 0.7975, which is BELOW the 0.80 Green boundary, and half-up
    # rounding made it 0.80 and published GREEN. The same upward flip sits on the 0.65 and 0.50
    # edges. The error is favourable, and its direction is not incidental -- half-up moves a
    # figure toward the boundary above it, and on this ladder above is better.
    #
    # The band is now taken from the raw average. `avg_reliability` carries the raw average, for
    # the reason finding H1 established: a stored analytical field is never a rounded one. The
    # DISPLAYED figure carries the shared Run 135 rule -- the fewest decimals, never fewer than
    # the two `round2` gave, that keep it on the same side of every edge of this ladder as the
    # average itself -- and the per-cent sentence is rendered from that figure rather than from
    # a second, coarser rounding of its own, so the sentence and the band cannot disagree.
    avg = sum(weights) / len(weights)
    avg_display = band_figure(avg, (0.80, 0.65, 0.50), 2)
    derived_count = sum(1 for k in sources if _doc_type(sources[k]) == "derived")
    color = ("Green" if avg >= 0.80 else "Yellow" if avg >= 0.65
             else "Amber" if avg >= 0.50 else "Red")
    return {
        "method_class": "Source_Reliability_Weighting",
        "status_color": color,
        "avg_reliability": avg,
        "avg_reliability_display": avg_display,
        "derived_fields": derived_count,
        "total_sources": len(weights),
        "evidence_metric": (
            f"Avg source reliability: "
            f"{_js_str(band_figure(avg_display * 100, (80.0, 65.0, 50.0), 0))}%"
            + (f" ({derived_count} estimated fields)" if derived_count > 0 else ", all measured")
        ),
    }


# ------------------------------------------------------------ C1.4 Audit Trail Completeness


def run_audit_trail(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    events = si.get("events")
    if not isinstance(events, list):
        return insufficient("Audit_Trail_Completeness")
    required = ["project_created", "signals_extracted"]

    def has_event(name):
        for ev in events:
            if name == "signals_extracted" and ev.get("event") == "simulation_run":
                return True
            if ev.get("event") == name:
                return True
        return False

    present = [e for e in required if has_event(e)]
    completeness = len(present) / len(required)
    total = len(events)
    has_decision = any(e.get("event") == "decision_recorded" for e in events)
    color = ("Green" if completeness >= 1.0 and total >= 3
             else "Yellow" if completeness >= 0.75
             else "Amber" if completeness >= 0.50 else "Red")
    pct = int(js_round(completeness * 100))
    return {
        "method_class": "Audit_Trail_Completeness",
        "status_color": color,
        "completeness_pct": pct,
        "total_events": total,
        "has_decision_record": has_decision,
        "evidence_metric": (
            f"{pct}% audit trail completeness, {total} events recorded"
            + (", decision record present" if has_decision else ", no decision record yet")
        ),
    }


# ------------------------------------------------------------ C1.5 Information Completeness


_ALL_FIELDS = ("bac", "ev", "ac", "pv", "cpi", "spi", "docRiskScore",
               "actualPctComplete", "plannedPctComplete",
               "baselineStart", "baselineEnd", "workPeriodFrom", "workPeriodTo",
               "totalFloat", "consumedFloat", "originalContingency",
               "rfiCount", "changeOrderCount", "subcontractorComplianceScore")


def run_info_completeness(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    sources = si.get("sources")

    def field_dt(f):
        src = sources.get(f) if sources else None
        return None if src is None else _doc_type(src)

    measured = 0
    estimated = 0
    for f in _ALL_FIELDS:
        if si.get(f) is None:
            continue
        src = sources.get(f) if sources else None
        if src is None:
            measured += 1
        elif _doc_type(src) == "derived":
            estimated += 1
        else:
            measured += 1
    missing = len(_ALL_FIELDS) - measured - estimated
    ratio = measured / len(_ALL_FIELDS)
    color = ("Green" if ratio >= 0.75 else "Yellow" if ratio >= 0.55
             else "Amber" if ratio >= 0.35 else "Red")
    pct = int(js_round(ratio * 100))
    return {
        "method_class": "Information_Completeness_Ratio",
        "status_color": color,
        "measured": measured,
        "estimated": estimated,
        "missing": missing,
        "total": len(_ALL_FIELDS),
        "completeness_ratio": pct,
        "evidence_metric": (
            f"{measured} measured + {estimated} estimated + {missing} missing of "
            f"{len(_ALL_FIELDS)} fields ({pct}% from documents)"
        ),
    }


# ------------------------------------------------------------ C1.6 Cross-document Consistency

#: The cross-document agreements this method is defined over: cost performance against earned
#: value and actual cost, schedule performance against earned value and planned value, and
#: reported progress against earned value and the budget at completion. Three, declared here so
#: the score's denominator is the method's, and so adding a fourth check is one visible edit.
DECLARED_CONSISTENCY_CHECKS = 3


def run_cross_doc_consistency(si: dict, rand: Callable[[], float],
                              period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("ev", "ac")):
        return insufficient("Cross_Doc_Consistency")
    inconsistencies = 0
    checks = 0
    # RUN 135, FINDING H1, THE RE-EXAMINATION THE ORDER ASKED FOR. The two derived indices were
    # formed here through `_round3` and compared to the stored index at a tolerance of 0.005.
    #
    # THAT TOLERANCE WAS TEN TIMES THE ROUNDING STEP, which is why this module -- the one whose
    # whole purpose is to notice when two documents disagree -- could not see the defect H1
    # names: a stored index rounded half-up differs from the true quotient by at most 0.0005,
    # and this check allowed ten times that before it would say anything. The rounding is gone
    # from storage now, so `_round3` is gone from here too and the derived index is the quotient
    # itself, compared like with like.
    #
    # THE 0.005 STAYS AND ITS MEANING CHANGES, which is worth stating plainly. It is no longer a
    # rounding allowance -- there is no rounding step left for it to absorb -- it is the
    # CROSS-DOCUMENT AGREEMENT tolerance this method is defined over: where the index arrives
    # from a document rather than from this platform's own arithmetic, two documents stating
    # figures that agree to within half a per cent of index are not treated as contradicting
    # each other. Where the index WAS derived here, the comparison is now exact and any
    # disagreement is a real one. Narrowing it further is a question about what a document
    # disagreement is, not a rounding question, and it is left for the owner.
    if (si.get("cpi") is not None and si.get("ev") is not None
            and si.get("ac") is not None and si["ac"] != 0):
        derived_cpi = si["ev"] / si["ac"]
        if abs(derived_cpi - si["cpi"]) > 0.005:
            inconsistencies += 1
        checks += 1
    if (si.get("spi") is not None and si.get("ev") is not None
            and si.get("pv") is not None and si["pv"] != 0):
        derived_spi = si["ev"] / si["pv"]
        if abs(derived_spi - si["spi"]) > 0.005:
            inconsistencies += 1
        checks += 1
    if (si.get("actualPctComplete") is not None and si.get("ev") is not None
            and si.get("bac") is not None and si["bac"] != 0):
        derived_pct = js_round((si["ev"] / si["bac"]) * 1000) / 10
        if abs(derived_pct - si["actualPctComplete"]) > 5:
            inconsistencies += 1
        checks += 1
    if checks == 0:
        return insufficient("Cross_Doc_Consistency")
    # RUN 14. THE DENOMINATOR IS THE THREE CHECKS THIS METHOD IS DEFINED OVER, NOT THE SUBSET
    # THE CORPUS HAPPENED TO SUPPORT. Run 13 removed the reported percent complete from a
    # project whose progress disagreed with its earned value, and the reading went from Amber to
    # Green: the failing check left the numerator AND the denominator together, and the score
    # renormalised over the survivors. Deleting the document that carried the disagreement made
    # the documents agree. The quantity this module reports is how much cross-document
    # consistency has been DEMONSTRATED, so a check that could not be run is not consistent, and
    # it is not counted as inconsistent either: the sentence says how many could not be run, and
    # the reader is told which figure is missing rather than shown a score built on its absence.
    # The four band boundaries are untouched.
    consistent = checks - inconsistencies
    score = consistent / DECLARED_CONSISTENCY_CHECKS
    color = ("Green" if score >= 1.0 else "Yellow" if score >= 0.67
             else "Amber" if score >= 0.33 else "Red")
    pct = int(js_round(score * 100))
    not_performed = DECLARED_CONSISTENCY_CHECKS - checks
    return {
        "method_class": "Cross_Doc_Consistency",
        "status_color": color,
        "consistency_score": pct,
        "inconsistencies": inconsistencies,
        "checks_performed": checks,
        "checks_declared": DECLARED_CONSISTENCY_CHECKS,
        "checks_not_performed": not_performed,
        "evidence_metric": (
            f"{consistent} of {DECLARED_CONSISTENCY_CHECKS} cross-document checks consistent "
            f"({pct}%)"
            + (f"; {not_performed} could not be run because the figures they compare have not "
               f"all been reported" if not_performed > 0 else "")
            + ("; verify figures across uploaded documents" if inconsistencies > 0 else "")
        ),
    }


# ------------------------------------------------------------ C1.7 Reporting Frequency Index


def run_reporting_frequency(si: dict, rand: Callable[[], float],
                            period_cutoff) -> dict[str, Any]:
    events = si.get("events")
    if not isinstance(events, list):
        return insufficient("Reporting_Frequency_Index")
    extracts = [e for e in events
                if e.get("event") in ("signals_extracted", "simulation_run")]
    if len(extracts) < 2:
        return insufficient("Reporting_Frequency_Index",
                            "Awaiting history (2 document uploads needed)")
    raw_dates = [_js_date_ms(e.get("at")) for e in extracts]
    if any(d is None for d in raw_dates):
        return insufficient("Reporting_Frequency_Index")
    dates = sorted(raw_dates)
    intervals = [(dates[i] - dates[i - 1]) / 86400000 for i in range(1, len(dates))]
    avg = sum(intervals) / len(intervals)
    # RUN 20, P0B. Only the intervals BETWEEN observed reports were measured, so the period
    # cutoff was never compared to the last report and cessation was invisible. A project that
    # uploaded twice ten days apart in January of last year and then stopped reported a ten day
    # average interval and banded Green, the best cadence reading available, on evidence that
    # had stopped seventeen months earlier.
    #
    # The gap from the last report to the end of the period is an observed interval too, and it
    # is the one the reader is standing in: it is a lower bound on the interval currently
    # running, because that interval cannot end before the period does. It is measured on the
    # module's own existing ladder rather than a new one, and the band is taken from whichever of
    # the two readings is worse, so a cadence that has stopped cannot be reported by the cadence
    # it once kept. No new threshold is introduced. What the module still cannot do is compare
    # either figure to a GOVERNED expected cadence, which is a separate structural finding.
    now_ms = _js_date_ms(str(period_cutoff))
    if now_ms is None:
        return insufficient("Reporting_Frequency_Index")
    gap = max(0.0, (now_ms - dates[-1]) / 86400000)
    worst = max(avg, gap)

    def band(days: float) -> str:
        return ("Green" if days <= 14 else "Yellow" if days <= 30
                else "Amber" if days <= 60 else "Red")

    color = band(worst)
    word = ("high frequency reporting" if worst <= 14
            else "monthly reporting cycle" if worst <= 30
            else "infrequent updates" if worst <= 60 else "reporting gap, data may be stale")
    metric = f"{int(js_round(avg))} day avg interval between document uploads, {word}"
    if gap > avg:
        metric = (f"{int(js_round(avg))} day avg interval between document uploads, but nothing "
                  f"has been uploaded for {int(js_round(gap))} days, {word}")
    return {
        "method_class": "Reporting_Frequency_Index",
        "status_color": color,
        "avg_interval_days": int(js_round(avg)),
        "gap_since_last_report_days": int(js_round(gap)),
        "uploads": len(extracts),
        "evidence_metric": metric,
    }


DQ_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "C1.5": ("Information_Completeness_Ratio", run_info_completeness),
}
