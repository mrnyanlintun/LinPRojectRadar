# Group C: Data and Evidence Health -- module source export

Regenerated from the registry (Run 5, post-freeze; see code_audit/REPORT_2026-08-11_run5-export.md). Every section below carries its activation state. Headings are canonical module names; no module id appears as a heading, per NAMING_AUTHORITY.md.

**7 modules in this group.**

---

## Missing Data Index

Purpose: Missing Data Index, category "Data Integrity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Missing_Data_Index`

```python
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
```

---

## Data Timeliness Score

Purpose: Data Timeliness Score, category "Data Integrity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Data_Timeliness_Score`

```python
def run_data_timeliness(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not si.get("docDate"):
        return insufficient("Data_Timeliness_Score")
    doc_ms = _js_date_ms(si["docDate"])
    now_ms = _js_date_ms(str(period_cutoff))
    if doc_ms is None or now_ms is None:
        return insufficient("Data_Timeliness_Score")
    days = math.floor((now_ms - doc_ms) / 86400000)
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
```

---

## Source Reliability Weighting

Purpose: Source Reliability Weighting, category "Data Integrity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Source_Reliability_Weighting`

```python
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
    avg = round2(sum(weights) / len(weights))
    derived_count = sum(1 for k in sources if _doc_type(sources[k]) == "derived")
    color = ("Green" if avg >= 0.80 else "Yellow" if avg >= 0.65
             else "Amber" if avg >= 0.50 else "Red")
    return {
        "method_class": "Source_Reliability_Weighting",
        "status_color": color,
        "avg_reliability": avg,
        "derived_fields": derived_count,
        "total_sources": len(weights),
        "evidence_metric": (
            f"Avg source reliability: {int(js_round(avg * 100))}%"
            + (f" ({derived_count} estimated fields)" if derived_count > 0 else ", all measured")
        ),
    }
```

---

## Audit Trail Completeness

Purpose: Audit Trail Completeness, category "Data Integrity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Audit_Trail_Completeness`

```python
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
```

---

## Information Completeness Ratio

Purpose: Information Completeness Ratio, category "Data Integrity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Information_Completeness_Ratio`

```python
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
```

---

## Cross-document Consistency Score

Purpose: Cross-document Consistency Score, category "Data Integrity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Cross_Doc_Consistency`

```python
def run_cross_doc_consistency(si: dict, rand: Callable[[], float],
                              period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("ev", "ac")):
        return insufficient("Cross_Doc_Consistency")
    inconsistencies = 0
    checks = 0
    if (si.get("cpi") is not None and si.get("ev") is not None
            and si.get("ac") is not None and si["ac"] != 0):
        derived_cpi = _round3(si["ev"] / si["ac"])
        if abs(derived_cpi - si["cpi"]) > 0.005:
            inconsistencies += 1
        checks += 1
    if (si.get("spi") is not None and si.get("ev") is not None
            and si.get("pv") is not None and si["pv"] != 0):
        derived_spi = _round3(si["ev"] / si["pv"])
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
    score = (checks - inconsistencies) / checks
    color = ("Green" if score >= 1.0 else "Yellow" if score >= 0.67
             else "Amber" if score >= 0.33 else "Red")
    pct = int(js_round(score * 100))
    return {
        "method_class": "Cross_Doc_Consistency",
        "status_color": color,
        "consistency_score": pct,
        "inconsistencies": inconsistencies,
        "checks_performed": checks,
        "evidence_metric": (
            f"{checks - inconsistencies} of {checks} cross-document checks consistent ({pct}%)"
            + ("; verify figures across uploaded documents" if inconsistencies > 0 else "")
        ),
    }
```

---

## Reporting Frequency Index

Purpose: Reporting Frequency Index, category "Data Integrity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Reporting_Frequency_Index`

```python
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
    color = ("Green" if avg <= 14 else "Yellow" if avg <= 30
             else "Amber" if avg <= 60 else "Red")
    word = ("high frequency reporting" if avg <= 14
            else "monthly reporting cycle" if avg <= 30
            else "infrequent updates" if avg <= 60 else "reporting gap, data may be stale")
    return {
        "method_class": "Reporting_Frequency_Index",
        "status_color": color,
        "avg_interval_days": int(js_round(avg)),
        "uploads": len(extracts),
        "evidence_metric": (
            f"{int(js_round(avg))} day avg interval between document uploads, {word}"
        ),
    }
```

---
