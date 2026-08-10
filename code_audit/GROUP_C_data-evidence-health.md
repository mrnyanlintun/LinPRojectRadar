# Group C — Data and Evidence Health

7 modules. Purpose: "how trustworthy the evidence is." **Group C does not contribute to project
status** (`compute.py`'s `contributes_to_project_status(group)` returns `False` for `"C"`) — it is
a quality gate on the evidence base, not a property of the project. Source file:
`server/app/simulation/models_dq.py`.

---

## Missing Data Index

Purpose: Missing Data Index, category "Data Integrity". Notes column in the registry CSV:
"authoring-time quality gate; not participant-facing; must not enter project status aggregation."

Source (`models_dq.py`):

```python
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
```

**Inputs.** Presence-only check (`si.get(f) is not None`) over eleven named "core" fields: `bac`,
`ev`, `ac`, `pv`, `cpi`, `spi`, `docRiskScore`, `actualPctComplete`, `plannedPctComplete`,
`baselineStart`, `baselineEnd`. All eleven are present in `field_registry.FIELD_KINDS`
(SNAPSHOT/PERMANENT).

**Availability.** All eleven core fields are emittable.

**Literals:** the eleven-field `_CORE_FIELDS` tuple itself is a curated list, no comment on why
these eleven and not others (e.g. `ncrOpen`, `rfiCount` are excluded even though they are
emittable). Banding `<=0.10/0.25/0.45` (missing ratio) — no comment.

**Output / banding.** `missing_count`, `total_fields` (always 11), `completeness_pct`.

**Abstains:** never — this module has no `insufficient()` call and always returns a concrete
result, even at 0% completeness (which would band Red, not abstain).

---

## Data Timeliness Score

Purpose: Data Timeliness Score, category "Data Integrity". Same registry notes as above.

Source (`models_dq.py`):

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

**Inputs.** `docDate` (compared against `period_cutoff`, never the wall clock — this module's
module-level docstring documents that it is "the one module in the instrument that read the wall
clock" in the original JavaScript, `new Date()` at `simulations.js:2377`, and that the port
substitutes `period_cutoff` for reproducibility).

**Availability.** `docDate` is listed in `field_registry.UNEMITTABLE_FIELDS` (alongside
`rfiNumber`, `rfiResponseTimeDays`) as "no longer a written field at all" — **but the same file's
comment clarifies it is not genuinely dead**: "it is DERIVED at selection as the latest `as_of`
among selected observations, the same rule `_derive_cutoff` uses, so the pipeline has ONE answer
to 'as of when'." So `docDate` should in practice be populated by that derivation step for any
project with at least one selected observation; this audit did not trace `_derive_cutoff` itself
(outside `server/app/simulation/`) to confirm it always succeeds.

**Literals:** banding `<=30/60/90` days — no comment.

**Output / banding.** `days_since_last_doc`, `last_doc_date`.

**Abstains** when `docDate` is falsy, or when either date fails to parse via `_js_date_ms`.

---

## Source Reliability Weighting

Purpose: Source Reliability Weighting, category "Data Integrity". Same registry notes.

Source (`models_dq.py`), with its private lookup table and helper:

```python
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

**Inputs.** `sources` — a dict keyed by field name, each value describing which document type
(`docType`) supplied that field's value. This is metadata attached to `si` by the merge/assembly
layer, not itself a `field_registry.FIELD_KINDS` entry.

**Availability.** Depends on the assembly layer populating `si["sources"]`; not covered by
`field_registry.py` directly (that file governs the field *values*, not the provenance metadata).

**Literals — twelve fixed document-type reliability weights, no cited source or methodology for
any of them:** `pay_application 0.90`, `contract_value 0.95`, `schedule_of_values 0.85`,
`time_phased_schedule 0.80`, `monthly_report 0.75`, `change_order 0.90`, `rfi 0.65`,
`submittal 0.65`, `field_report 0.60`, `oac_minutes 0.55`, `inspection_report 0.70`,
`derived 0.40`, plus a fallback `0.50` for any unrecognized `docType`. Banding `>=0.80/0.65/0.50`
— no comment.

**Output / banding.** `avg_reliability`, `derived_fields` count, `total_sources`.

**Abstains** when `sources` is missing/empty, or when none of the sources present has a
recognized `docType`.

---

## Audit Trail Completeness

Purpose: Audit Trail Completeness, category "Data Integrity". Same registry notes. **The event
log is now supplied — see D1 note below.**

Source (`models_dq.py`):

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

**Inputs.** `si["events"]` — a list of `{event, at}` dicts. **File-level docstring documents the
history**: "D1: THE EVENT LOG IS NOW SUPPLIED AND THE STUBS ARE GONE. Until D1 nothing assembled
`si["events"]`, so C1.4 reported '0 events recorded' and a Red band on every project... `documents.py`
now passes the project's event log in."

**Availability.** Per that docstring, `si["events"]` is now populated by `documents.py` (outside
`server/app/simulation/`, not independently audited here beyond this note); an **absent** log
abstains (treated as "the caller said nothing about the project"), while an **empty** list (`[]`)
is treated as real evidence of zero events, not an abstention — `isinstance(events, list)` passes
for `[]`.

**Literals:** required-event list `["project_created", "signals_extracted"]` (with
`signals_extracted` satisfied by an actual logged event named `simulation_run` — a naming
alias not otherwise commented). Banding: Green requires **both** 100% completeness **and**
`total >= 3` events (a compound condition unique among Group C modules) — the `3` event-count
floor is uncommented. Yellow `>=0.75`, Amber `>=0.50` — no comment.

**Output / banding.** `completeness_pct`, `total_events`, `has_decision_record`.

**Abstains** when `si["events"]` is absent or not a list (an empty list does not abstain).

---

## Information Completeness Ratio

Purpose: Information Completeness Ratio, category "Data Integrity". Same registry notes.

Source (`models_dq.py`):

```python
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
```

**Inputs.** Nineteen named fields (a superset of C1.1's eleven, adding `workPeriodFrom/To`,
`totalFloat`, `consumedFloat`, `originalContingency`, `rfiCount`, `changeOrderCount`,
`subcontractorComplianceScore`), plus `si["sources"]` to distinguish measured-from-document vs.
derived/estimated values.

**Availability.** All nineteen fields are in `field_registry.FIELD_KINDS` (emittable).

**Literals:** the nineteen-field list itself, uncommented choice (why these and not, e.g., the
RFA/NCR fields C1.1 also excludes). `ratio = measured / total` counts only "measured" (non-derived)
fields toward completeness — a value present but flagged `derived` counts as `estimated`, not
`measured`, and does not count toward `ratio` at all (note: `ratio` uses `measured`, not
`measured + estimated`, so a fully "estimated" project reports a low completeness ratio despite
having values for every field — this is a real behavior worth the reviewer's attention, not a
bug this audit is diagnosing). Banding `>=0.75/0.55/0.35` — no comment.

**Output / banding.** `measured`/`estimated`/`missing`/`total`, `completeness_ratio`.

**Abstains:** never — no `insufficient()` call in this function.

---

## Cross-document Consistency Score

Purpose: Cross-document Consistency Score, category "Data Integrity". Same registry notes.

Source (`models_dq.py`):

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

**Inputs.** `ev`, `ac` (required as an entry gate), and conditionally `cpi`, `spi`,
`actualPctComplete`, `pv`, `bac` for the three cross-checks — recomputes CPI/SPI/percent-complete
from their EVM component parts and compares against the extracted values for the same fields.

**Availability.** All fields emittable.

**Literals:** tolerance `0.005` (CPI/SPI derived-vs-extracted discrepancy threshold) and `5`
(percentage points, for actualPctComplete) — no comment on why these specific tolerances. Banding
`>=1.0/0.67/0.33` (fraction of checks passing) — no comment.

**Output / banding.** `consistency_score` (%), `inconsistencies` count, `checks_performed`
(0-3, depending which of the three cross-checks had enough data).

**Abstains** when `ev`/`ac` missing, or when none of the three cross-checks has enough data
(`checks == 0`).

---

## Reporting Frequency Index

Purpose: Reporting Frequency Index, category "Data Integrity". Same registry notes. **Depends on
the same event log D1 note as C1.4, with an additional abstention rule.**

Source (`models_dq.py`):

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

**Inputs.** `si["events"]`, filtered to `event in ("signals_extracted", "simulation_run")` —
i.e. this module (unlike C1.4) does **not** treat `"signals_extracted"` and `"simulation_run"` as
aliases requiring translation; it filters for either literal event name directly.

**Availability.** Same D1 note as C1.4: `si["events"]` now assembled by `documents.py`. Per this
module's own docstring: "C1.7 additionally abstains below two extraction events, since one point
establishes no interval."

**Literals:** minimum extraction count `2` (documented rationale: one point establishes no
interval — a genuine methodological necessity, not an arbitrary tuning constant). Banding
`<=14/30/60` days — no comment.

**Output / banding.** `avg_interval_days`, `uploads` (count of qualifying events).

**Abstains** when `events` missing/not-a-list, fewer than 2 qualifying extraction events, or any
event's `at` timestamp fails to parse.
