# Shared machinery

Common code that many modules call, quoted once here and referenced by name from the group
files. Source: `server/app/simulation/`.

## Abstention contract — `insufficient()`

`server/app/simulation/models.py`:

```python
def insufficient(method_class: str, message: str | None = None) -> dict[str, Any]:
    """
    The abstention contract, matching the JavaScript helper exactly.

    A module with missing inputs abstains. It does not fall back to a neutral value: a fabricated
    Green is indistinguishable from a measured one once it reaches fusion.
    """
    return {
        "method_class": method_class,
        "status_color": None,
        "insufficient_data": True,
        "evidence_metric": message or "Insufficient data: upload required documents",
    }


def check_inputs(si: dict, required: tuple[str, ...]) -> bool:
    return all(si.get(k) is not None for k in required)
```

A module "abstains" when it returns this shape: `status_color: None`, `insufficient_data: True`.
`run_all()` in `registry.py` treats `out.get("insufficient_data") or out.get("status_color") is
None` as abstention, records `{"module_id": ..., "reason": out.get("evidence_metric")}` in the
`abstained` list, and the module contributes nothing to fusion.

## Numeric / JS-compatibility helpers — `rng.py`

```python
def js_round(value: float) -> float:
    """
    JavaScript Math.round: ties go toward positive infinity.
    """
    if math.isnan(value) or math.isinf(value):
        return value
    return math.floor(value + 0.5)


def round1(v: float) -> float:
    return js_round(v * 10) / 10


def round2(v: float) -> float:
    return js_round(v * 100) / 100


def pctile(sorted_asc, q: float) -> float:
    """
    Index-based percentile, matching the JavaScript helper.

    Deliberately not interpolated and deliberately not numpy.percentile, which interpolates and
    returns a different P80 for the same sample.
    """
    if not sorted_asc:
        return float("nan")
    i = max(0, min(math.floor(q * (len(sorted_asc) - 1)), len(sorted_asc) - 1))
    return sorted_asc[i]


def num(value, default):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    return n if math.isfinite(n) else default


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def as_percent(value, default):
    if value is None:
        return default
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(n):
        return default
    return n * 100 if n <= 1 else n
```

`make_rng(seed)` is a mulberry32 PRNG reproduced bit-for-bit from the JavaScript; `seed_from(*parts)`
derives a 32-bit seed from `(scenario_id, period)` only — never from `participant_id`. Only three
modules draw from it: A1.1 Monte Carlo EAC, A1.2 CUSUM (indirectly, no — CUSUM is deterministic
given a series; it is listed in `STOCHASTIC` for the seed record but does not call `rand`), and
A2.1 PERT. `STOCHASTIC = frozenset({"A1.1", "A1.2", "A2.1"})` — note CUSUM is flagged stochastic in
the registry's output record even though `run_cusum` performs no random draw; it is deterministic
given `spiHistory`.

## Date parsing — `_js_date_ms` (`models_ext.py`)

```python
def _js_date_ms(value) -> float | None:
    """
    Milliseconds since the epoch as `new Date(value).getTime()` would produce, or None where the
    JavaScript would produce NaN. Date-only strings are UTC midnight.
    """
    if value is None:
        return None
    s = str(value)
    m = _DATE_RE.match(s)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return float(_days_from_epoch(y, mo, d) * 86400000)
```

Used by any module comparing baseline/date fields (A1.6, A2.4, A2.10, A2.7, C1.2, C1.7).

## Derived-field marker — `_derived()` (`models_ext.py`)

```python
def _derived(si: dict, *fields: str) -> bool:
    """The JavaScript `si.sources && sources[f].docType === 'derived'` guard, over any field."""
    sources = si.get("sources")
    if not sources:
        return False
    for f in fields:
        src = sources.get(f)
        if src and src.get("docType") == "derived":
            return True
    return False
```

Several modules append an "(estimated; upload X for precise figures)" clause to their evidence
string when the field that fed them was itself derived rather than extracted from a specific
document (A2.8, A3.2, A3.4, A3.5, A3.9, A4.2, A4.3, A4.6, A4.8, B3.5).

## String/formatting helpers (`models_ext.py`)

`_js_str` (integers render without a decimal point, matching JS string concatenation),
`_grouped`/`_money` (thousands separator and `$` prefix), `_or_default` (JS `value || default`
truthiness — 0, NaN, null, undefined all fall back), `_round3` (three-decimal `js_round`),
repeated locally in several files as `_round3 = lambda v: js_round(v * 1000) / 1000`.

## Dempster-Shafer fusion — `fusion.py`

```python
STATUS_MASS: dict[str, dict[str, float]] = {
    "Green":  {"Green": 0.80, "Yellow": 0.08, "Amber": 0.06, "Red": 0.04, "Unknown": 0.02},
    "Yellow": {"Green": 0.10, "Yellow": 0.70, "Amber": 0.13, "Red": 0.05, "Unknown": 0.02},
    "Amber":  {"Green": 0.05, "Yellow": 0.12, "Amber": 0.70, "Red": 0.11, "Unknown": 0.02},
    "Red":    {"Green": 0.03, "Yellow": 0.05, "Amber": 0.14, "Red": 0.76, "Unknown": 0.02},
}


def status_to_mass(status) -> dict[str, float] | None:
    s = "" if status is None else str(status).lower()
    if not s:
        return None
    if "red" in s:
        return STATUS_MASS["Red"]
    if "yellow" in s or "light-amber" in s:
        return STATUS_MASS["Yellow"]
    if "amber" in s or "orange" in s:
        return STATUS_MASS["Amber"]
    if "green" in s:
        return STATUS_MASS["Green"]
    if "complete" in s or "blue" in s:
        return STATUS_MASS["Green"]
    return None


def dst_combine(m1: dict[str, float], m2: dict[str, float]) -> dict[str, float]:
    """Dempster's rule. Returns the normalised combination plus the conflict coefficient K."""
    combined = {s: 0.0 for s in STATES}
    k = 0.0
    for s1 in STATES:
        for s2 in STATES:
            mass = m1.get(s1, 0.0) * m2.get(s2, 0.0)
            if s1 == s2:
                combined[s1] += mass
            else:
                k += mass
    norm = 1 - k
    if norm <= 0:
        out = {s: 0.2 for s in STATES}
        out["conflict"] = 1.0
        return out
    for s in STATES:
        combined[s] = combined[s] / norm
    combined["conflict"] = k
    return combined
```

`STATUS_MASS`'s per-state probability figures (0.80/0.08/0.06/0.04/0.02 etc.) carry no comment
tying them to any calibration data or source; they are simply the belief masses assigned to each
input status label. `dst_fuse()` additionally applies a documented 1.5x weighting to a
Red-dominant source (full combine once, then a half-strength Shafer-discounted re-combine),
commented as deliberate so "a single Red cannot silently sink a set of greens". `compute.py`'s
`contributes_to_project_status()` and `dst_fuse` together are the category-then-project two-stage
fusion; B2.1 (Dempster-Shafer, a *module*) is a separate, per-project evidence-combination
computation over `{evm, mc, cusum, doc}` signal packages, distinct from this category/project
rollup fusion, though it shares `dst_combine`.

## Vote bucketing — `_vote_bucket()` (`models_gov.py`, used by B1.2–B1.4)

```python
def _vote_bucket(status) -> str | None:
    """Anything containing 'Red' -> Red; exactly Amber/Yellow -> themselves; else Green."""
    if not status:
        return None
    if "Red" in status:
        return "Red"
    if status == "Amber":
        return "Amber"
    if status == "Yellow":
        return "Yellow"
    return "Green"
```

Documented as deliberately not "fixed": anything not exactly "Amber"/"Yellow" and not containing
"Red" — including odd strings like "light-amber" or "Complete" — buckets to Green.

## JS-style division — `_jsdiv()` (`models_gov.py`, used by B4.2 Linear Programming and B2.18
MARCOS)

```python
def _jsdiv(a: float, b: float) -> float:
    """JavaScript division: x/0 is +-Infinity (NaN for 0/0), never an exception."""
    if b == 0:
        if a == 0:
            return float("nan")
        return math.inf if a > 0 else -math.inf
    return a / b
```

## Period-series assembly and merge precedence

The signalInputs (`si`) dict each module receives is assembled server-side by the document
pipeline before the registry ever runs; the simulation layer (everything referenced above) is
read-only over whatever keys land in `si`. Field behaviour (SNAPSHOT/EVENT/DELTA/PERMANENT), writer
precedence across document types, and which higher-level "needs" (`cpiHistory`, `spiHistory`,
`milestoneHistory`, `changeOrderCount` as an event set) can actually be served are declared in
`server/app/field_registry.py`; see the REPORT file for which module inputs that declares
servable vs. dead-on-arrival. This audit did not re-derive the merge/period-assembly code path
itself (`documents.py`, outside `server/app/simulation/`) beyond what `field_registry.py`
declares, per the task's read-only, registry-focused scope; module-by-module "Inputs" sections
below name the `si` keys each module reads and cross-reference `field_registry.py` for whether
that key can be populated today.
