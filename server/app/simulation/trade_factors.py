"""
RUN 118. THE TRADE RECORDS REACH THE FIRM -- the owner's factor ladders, in one place.

WHAT RUN 117 STOPPED SHORT OF, AND WHY IT WAS RIGHT TO. Run 117 assembled the trade records,
attributed them to the firm the document names, carried them onto A4.8's reading and moved no
band, because "how a nonconformance weighs against a stated rating" was a threshold nobody had
stated. The owner has now stated every one of them. THIS MODULE HOLDS THEM AND NOTHING ELSE
HOLDS THEM: no ladder below is repeated in `documents.py`, in `models_doc.py` or on a surface.

EIGHT FACTORS, NOT SEVEN. The order calls them "the seven trade factors" in section 1.1 and
then lists EIGHT under section 1.2 -- Nonconformances, Failed inspections, Safety,
Environmental, Quality audit, Procurement, Field observations, Commissioning. The count is
wrong; the list is not. All eight are built, each with the ladder the order gives it, and the
discrepancy is reported rather than resolved by dropping one. Nothing here invents a ninth.

HOW A FACTOR BAND BECOMES A FIRM POSTURE, and this is a READING of the order, recorded as one.

  * The SOURCE RATING sets the starting band (`canonical_v4.subcontractor_reported_ratings`
    already normalises it; it is passed in, never recomputed here).
  * SEVEN of the eight factors produce a band directly from their own rate on their own ladder.
  * NONCONFORMANCES is the odd one, and it is the only ladder on this platform expressed as a
    DISPLACEMENT rather than a band: "down one band", "down two bands". Down from WHAT is not
    stated anywhere else in the order, and the only band in scope to be displaced is the
    starting band the same section has just defined. So the nonconformance factor is seeded
    from the starting band and displaced, which yields a band like the other seven.
  * The eight bands then AVERAGE, on `category_posture.BAND_SCORE` and
    `category_posture.band_average` -- the same scale and the same cuts the category
    arithmetic already uses, imported rather than copied, on Run 106's `project_posture`
    precedent. The order's instruction is "establish those cuts from `category_posture` and use
    the same function if it fits". IT FITS: `band_average` takes an iterable of scores and
    returns a band, and it is called here unchanged. What does NOT come from
    `category_posture` is the SUBJECT of the average -- that module averages modules inside a
    category, this averages factors inside a firm -- so the function and its constants are
    reused and its `category_posture()` entry point is not.
  * THE SOURCE RATING ENTERS THE AVERAGE THROUGH THE NONCONFORMANCE FACTOR AND NOWHERE ELSE.
    That is the sense in which the eight factors "adjust" it. This is the weakest joint in the
    reading and it is stated plainly rather than buried: the order defines an adjustment
    operation for exactly one factor and calls the other seven "adjustments" without saying to
    what. No second combination rule was invented to fill the gap; where NO factor produces a
    band at all the starting band is carried through unchanged, which is exactly the Run 107
    behaviour and is why this run cannot move the census backwards.

A HARD OVERRIDE BYPASSES THE AVERAGE. A factor that fires its override sets the firm Red
outright and is not one voice among eight. A STOP-WORK ORDER is stronger still: the owner's
words are that it is an emergency, it impacts everything, and if there were a band above Red he
would give it one. It sets the firm Red, it bypasses the average, and NO other factor pulls it
back -- which on this platform means it is recorded as its own class of override so a reader can
tell it apart from the seven ordinary ones.

THE SMALL-DENOMINATOR SAFEGUARD, section 1.3, applies to every rate factor EXCEPT safety, which
has the owner's own exposure-hours rule instead. Twenty-five or more: band normally. Ten to
twenty-four: band and label LIMITED EXPOSURE. Fewer than ten: NO RATE BANDING -- the overrides
still fire and the raw count is shown. A zero denominator never produces a rate. One failed
inspection out of two never produces Red on its own, and the finding stays visible.

A CLOSED RECORD STOPS COUNTING IMMEDIATELY, section 1.4. Only open records weigh. The word is
read off the record's own `record_status` and is never inferred.

NO SEVERITY WORD IS INVENTED. The safety and environmental overrides read
`models_cat89._SAFETY_OVERRIDE_WORDS` and `_ENV_OVERRIDE`, the closed sets Run 101/102 built
and Run 117 declined to widen. They are not widened here either. The other six overrides carry
their own vocabularies, drawn word for word from the owner's own sentences in section 1.2, and
a severity word matching none of them fires nothing rather than being dropped to the nearest.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .category_posture import AVERAGE_CUTS, BAND_SCORE, band_average
from .models_cat89 import _ENV_OVERRIDE, _SAFETY_OVERRIDE_WORDS

#: Adverse-first ordering, the platform's existing one.
_ORDER: tuple[str, ...] = ("Green", "Yellow", "Amber", "Red")
_RANK: dict[str, int] = {b: i for i, b in enumerate(_ORDER)}

#: THE OWNER'S BAND BASIS IDENTIFIER, section 1.2, for every threshold in this module except
#: the TRIR formula. It is an owner string and it goes where owner strings go -- `band_basis_id`
#: -- and NOT into `THRESHOLD_SOURCES`, which stays exactly three values wide.
OWNER_BASIS_ID = "owner_configured_construction_quality_tolerance"

#: THE ONE CODIFIED THING IN THIS MODULE. The recordable incident rate formula is OSHA's, not
#: the owner's: recordables x 200,000 / hours worked. The CUTS ON IT (1.0 / 2.0 / 3.0) are the
#: owner's. That split is exactly Run 107's `band_basis_provenance_class` /
#: `band_boundary_provenance_class` distinction and is recorded per factor below.
OSHA_TRIR_BASIS_ID = "osha_recordable_incident_rate_formula"
OSHA_TRIR_CONSTANT = 200_000.0

#: Section 1.3. The three exposure classes, and the counts that separate them. The owner's.
SMALL_DENOMINATOR_FULL = 25
SMALL_DENOMINATOR_LIMITED = 10

#: Section 1.2, safety. The owner's exposure floor below which the rate is shown WITH A WARNING
#: and is NOT replaced by a raw count. It does not suppress the band; the order says so in terms.
SAFETY_SMALL_EXPOSURE_HOURS = 10_000.0

EXPOSURE_FULL = "full"
EXPOSURE_LIMITED = "limited_exposure"
EXPOSURE_TOO_FEW = "no_rate_banding"
EXPOSURE_NO_DENOMINATOR = "no_denominator"


def _n(v) -> float | None:
    """A number the document printed, or None. Never a default and never a coercion of prose."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v) if v == v and abs(v) != float("inf") else None
    s = str(v).strip().replace(",", "")
    if not s:
        return None
    for junk in ("%", "$", "days", "day", "hrs", "hours", "hr"):
        if s.lower().endswith(junk):
            s = s[: -len(junk)].strip()
    try:
        f = float(s)
    except ValueError:
        return None
    return f if f == f and abs(f) != float("inf") else None


def _w(v) -> str:
    """A word the record printed, normalised for matching only. Never mapped to another word."""
    return str(v or "").strip().lower().replace("-", "_").replace(" ", "_")


def _ladder(value: float, rungs: Iterable[tuple[float, str]], floor_band: str) -> str:
    """Walk a worst-first ladder of (at-or-above this cut -> this band). Inclusive lower side."""
    for cut, band in rungs:
        if value >= cut:
            return band
    return floor_band


def _downgrade(start: str, steps: int) -> str:
    """Move `steps` bands adverse from `start`, stopping at Red. Red has no rung below it."""
    return _ORDER[min(_RANK[start] + steps, len(_ORDER) - 1)]


def worst(bands: Iterable[str]) -> str | None:
    """The most adverse of some bands, or None over an empty set."""
    vals = [b for b in bands if b in _RANK]
    return max(vals, key=lambda b: _RANK[b]) if vals else None


# =================================================================================================
# THE OVERRIDE VOCABULARIES
#
# Every word below is lifted from the owner's own section 1.2 sentence for that factor. A record
# whose severity, kind or status word is none of them fires NOTHING; it is reported unranked, on
# the `_SAFETY_OVERRIDE_WORDS` precedent, rather than being dropped to the nearest word that
# would have fired. No word here is a synonym this platform decided on.
# =================================================================================================

#: "life-safety or structural nonconformance; code or permit compliance failure; critical
#: inspection or hold-point failure; commissioning or turnover-blocking nonconformance"
_NCR_OVERRIDE: frozenset = frozenset({
    "life_safety", "life_safety_nonconformance", "structural", "structural_nonconformance",
    "code_compliance_failure", "permit_compliance_failure", "code_or_permit_compliance_failure",
    "critical_inspection_failure", "hold_point_failure", "hold_point",
    "commissioning_blocking", "turnover_blocking", "commissioning_or_turnover_blocking",
})

#: "any failed life-safety, structural, code-required, hold-point or turnover-blocking inspection"
_INSPECTION_OVERRIDE: frozenset = frozenset({
    "life_safety", "structural", "code_required", "code", "hold_point", "turnover_blocking",
})

#: "any critical finding affecting life safety, structural integrity, code compliance, a hold
#: point, or commissioning and turnover"
_AUDIT_OVERRIDE: frozenset = frozenset({
    "critical", "critical_finding", "life_safety", "structural", "structural_integrity",
    "code_compliance", "hold_point", "commissioning", "turnover",
})

#: "any reported and verified structural, life-safety, code or work-stoppage condition"
_FIELD_OVERRIDE: frozenset = frozenset({
    "structural", "life_safety", "code", "work_stoppage", "stop_work", "stop_work_order",
})

#: "a critical life-safety, functional-performance, regulatory or turnover acceptance test"
_COMMISSIONING_OVERRIDE: frozenset = frozenset({
    "critical", "life_safety", "functional_performance", "regulatory", "turnover",
})

#: THE HIGHEST SEVERITY THIS PLATFORM HAS, section 1.1. These three words are ALREADY in
#: `_SAFETY_OVERRIDE_WORDS`; they are named here so the stop-work class can be told apart from
#: the ordinary safety override, and the membership test still runs against the closed set.
_STOP_WORK_WORDS: frozenset = frozenset({"stop_work", "stop_work_order", "cease_and_desist"})

#: The status words that mean a record has stopped counting. Section 1.4: once closed, its
#: impact washes off. A record printing NO status is treated as OPEN -- it is not closed until
#: the document says so, and assuming closure would silently discard evidence.
_CLOSED_WORDS: frozenset = frozenset({
    "closed", "close", "resolved", "complete", "completed", "cleared", "accepted", "verified_closed",
})


def is_open(rec: Mapping[str, Any]) -> bool:
    """Section 1.4. Only open records weigh; a closed one stops counting IMMEDIATELY."""
    return _w(rec.get("record_status")) not in _CLOSED_WORDS


def _words_of(rec: Mapping[str, Any]) -> set[str]:
    """Every word a record printed that an override may be looking for, normalised."""
    return {_w(rec.get(k)) for k in ("record_severity", "record_kind", "record_status")} - {""}


def stop_work_hits(records: Iterable[Mapping[str, Any]]) -> list[str]:
    """
    The stop-work orders among these records. OPEN ONLY, and read off the record's own words.

    The membership test is `_SAFETY_OVERRIDE_WORDS`, the closed set Run 101 built. Nothing is
    added to it; `_STOP_WORK_WORDS` only says which of its members are of THIS class.
    """
    hits = []
    for r in records:
        if not is_open(r):
            continue
        for w in _words_of(r):
            if w in _STOP_WORK_WORDS and w in _SAFETY_OVERRIDE_WORDS:
                hits.append(f"{r.get('record_reference')}: {w}")
    return sorted(set(hits))


# =================================================================================================
# THE RECORD KINDS EACH FACTOR COUNTS
#
# Read off `record_kind`, the column Run 117 already asks for, in the document's own word. A row
# whose kind matches no factor is counted by NO factor -- it is not spread across them and it is
# not assigned to the nearest -- and it is reported in `rows_of_no_factor`.
# =================================================================================================

_KIND_NCR: frozenset = frozenset({
    "nonconformance", "non_conformance", "ncr", "nonconformity", "non_conformity"})
_KIND_INSPECTION_FAIL: frozenset = frozenset({
    "inspection_failure", "failed_inspection", "inspection_fail", "failed_inspection_item"})
_KIND_ENVIRONMENTAL: frozenset = frozenset({
    "environmental_action", "environmental", "permit_violation", "environmental_corrective_action"})
_KIND_AUDIT: frozenset = frozenset({"audit_finding", "finding", "quality_audit_finding"})
_KIND_PROCUREMENT: frozenset = frozenset({
    "late_delivery", "delivery", "procurement", "procurement_item", "late_item"})
_KIND_FIELD: frozenset = frozenset({
    "defect_observation", "field_observation", "site_observation", "observation", "defect"})
_KIND_COMMISSIONING: frozenset = frozenset({
    "commissioning_defect", "commissioning_failure", "acceptance_test_failure", "commissioning"})

#: The status words that mean an environmental action is past its date. The owner's factor is
#: "actions OVERDUE over actions DUE"; overdue is a state the register prints, never a date this
#: platform computes from a deadline it was not given.
_OVERDUE_WORDS: frozenset = frozenset({"overdue", "past_due", "late", "missed", "expired"})

#: Section 1.2, quality audit: "MAJOR findings ... minor documentation observations are not
#: counted". Both words are read; a finding printing neither is counted by NEITHER arm and is
#: reported, because guessing which it is would decide the factor.
_MAJOR_WORDS: frozenset = frozenset({"major", "critical", "significant"})
_MINOR_WORDS: frozenset = frozenset({"minor", "observation", "documentation", "informational"})


def _truthy(v) -> bool | None:
    """Yes / no as a document prints it, or None where it printed nothing. Never defaulted."""
    w = _w(v)
    if w in ("", "n/a", "na", "none", "not_stated", "unknown"):
        return None
    if w in ("y", "yes", "true", "t", "1", "1.0", "confirmed", "verified", "new", "first"):
        return True
    # RUN 118, ITERATION 2. `reinspection`, `retest` and `repeat` were in this list and are
    # AFFIRMATIVE VALUES of the columns that ask for them -- a `record_is_reinspection` cell
    # printing "retest" means YES, and reading it as "no" silently counted every retest into a
    # first-outcome numerator. Measured by `drive_run118.py` section 8 before this fix.
    if w in ("n", "no", "false", "f", "0", "0.0", "unconfirmed", "not_confirmed", "first_test",
             "first_inspection"):
        return False
    if w in ("reinspection", "retest", "repeat", "re_inspection", "re_test"):
        return True
    return None


def _exposure_class(denominator: float | None) -> str:
    """Section 1.3, and safety does not come through here."""
    if denominator is None or denominator <= 0:
        return EXPOSURE_NO_DENOMINATOR
    if denominator >= SMALL_DENOMINATOR_FULL:
        return EXPOSURE_FULL
    if denominator >= SMALL_DENOMINATOR_LIMITED:
        return EXPOSURE_LIMITED
    return EXPOSURE_TOO_FEW


_EXPOSURE_WORDS = {
    EXPOSURE_FULL: "",
    EXPOSURE_LIMITED: (" LIMITED EXPOSURE: the denominator is between 10 and 24, so the ladder "
                       "is applied and the result is labelled limited exposure."),
    EXPOSURE_TOO_FEW: (" NO RATE BANDING: fewer than 10 in the denominator. The owner's "
                       "safeguard is that one failure out of two must never produce Red on its "
                       "own, so the rate does not band. The count stays visible and the hard "
                       "overrides still apply."),
    EXPOSURE_NO_DENOMINATOR: (" NO RATE: this document states no denominator for this firm, so "
                              "no rate is formed and none is assumed. The count stays visible "
                              "and the hard overrides still apply."),
}


def _rate_factor(*, factor: str, measure: str, numerator: int, denominator: float | None,
                 denominator_field: str, rungs: tuple[tuple[float, str], ...],
                 floor_band: str, scale: float, boundary: str,
                 override_hits: list[str], override_words: str,
                 extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    One rate factor: its rate, its exposure class, its band and whether its override fired.

    THE OVERRIDE IS EVALUATED WHATEVER THE EXPOSURE CLASS. Section 1.3's words are "apply only
    the hard overrides and show the raw count" -- the safeguard suppresses the RATE, never the
    finding.
    """
    exposure = _exposure_class(denominator)
    rate = None
    band = None
    if exposure in (EXPOSURE_FULL, EXPOSURE_LIMITED):
        rate = (numerator / float(denominator)) * scale
        band = _ladder(rate, rungs, floor_band)
    out = {
        "factor": factor,
        "measure": measure,
        "numerator": numerator,
        "denominator": denominator,
        "denominator_field": denominator_field,
        "rate": None if rate is None else round(rate, 4),
        "rate_scale": "per 100" if scale == 100.0 else "a ratio",
        "exposure_class": exposure,
        "limited_exposure": exposure == EXPOSURE_LIMITED,
        "band_from_rate": band,
        "override_fired": bool(override_hits),
        "override_hits": override_hits,
        "override_words": override_words,
        "band": "Red" if override_hits else band,
        "band_basis_id": OWNER_BASIS_ID,
        "boundary": boundary + _EXPOSURE_WORDS[exposure]
                    + (" HARD OVERRIDE FIRED, and it bypasses the average: " + override_words
                       if override_hits else ""),
    }
    if extra:
        out.update(extra)
    return out


# =================================================================================================
# THE EIGHT FACTORS. Every cut below is the owner's, section 1.2, verbatim, inclusive on its
# LOWER side, and none of them appears anywhere else in this tree.
# =================================================================================================

_NCR_RUNGS = ((10.0, "Red"), (5.0, "down_two"), (2.0, "down_one"))
_PCT_2_5_10 = ((10.0, "Red"), (5.0, "Amber"), (2.0, "Yellow"))
_TRIR_RUNGS = ((3.0, "Red"), (2.0, "Amber"), (1.0, "Yellow"))
_ZERO_5_10 = ((10.0, "Red"), (5.0, "Amber"))     # plus the "above 0" Yellow arm, handled inline
_AUDIT_RUNGS = ((2.0, "Red"), (1.0, "Amber"))    # plus the "above 0" Yellow arm


def _zero_is_green(value: float, rungs) -> str:
    """The owner's shape for environmental, procurement rate, quality audit and commissioning:
    exactly 0 is Green, ANYTHING ABOVE 0 is at least Yellow, then the stated cuts."""
    for cut, band in rungs:
        if value >= cut:
            return band
    return "Yellow" if value > 0 else "Green"


def factor_nonconformances(records, denom, *, starting_band: str | None,
                           newness) -> dict[str, Any]:
    """
    New NCRs attributed to the firm this period / inspections of that firm's work this period.

    NEWLY OPENED ONLY. The owner's words: an older NCR is not counted again for remaining open.
    A row that states neither newness nor a date inside the period is EXCLUDED from the
    numerator and reported in `rows_newness_not_stated` -- counting it would be inferring that
    an undated record is new, and dropping it silently would hide that the document was thin.

    THE DISPLACEMENT. This is the only ladder on this platform that produces a MOVE rather than
    a band, and it moves from the starting band the source rating set. With no starting band --
    a firm with trade records and no stated rating, section 1.4 -- the two displacement rungs
    produce NO band and the factor contributes nothing to the average; the Red rung still
    fires, because it is stated absolutely.
    """
    rows = [r for r in records if _w(r.get("record_kind")) in _KIND_NCR and is_open(r)]
    new_rows, unstated = [], 0
    for r in rows:
        v = newness(r)
        if v is True:
            new_rows.append(r)
        elif v is None:
            unstated += 1
    hits = sorted({f"{r.get('record_reference')}: {w}"
                   for r in rows for w in _words_of(r) if w in _NCR_OVERRIDE})
    hits += sorted({f"{r.get('record_reference')}: repeat NCR for the same root cause after a "
                    f"corrective action was recorded closed"
                    for r in rows if _truthy(r.get("record_repeat_after_closed_action")) is True})
    exposure = _exposure_class(denom)
    rate = band = None
    displacement = None
    if exposure in (EXPOSURE_FULL, EXPOSURE_LIMITED):
        rate = (len(new_rows) / float(denom)) * 100.0
        rung = _ladder(rate, _NCR_RUNGS, "none")
        displacement = rung
        if rung == "Red":
            band = "Red"
        elif rung in ("down_one", "down_two") and starting_band:
            band = _downgrade(starting_band, 1 if rung == "down_one" else 2)
        elif rung == "none":
            band = starting_band
    return {
        "factor": "nonconformances",
        "measure": ("new NCRs attributed to the firm this period / inspections of that firm's "
                    "work this period x 100"),
        "numerator": len(new_rows), "denominator": denom,
        "denominator_field": "inspections_performed",
        "rate": None if rate is None else round(rate, 4), "rate_scale": "per 100",
        "exposure_class": exposure, "limited_exposure": exposure == EXPOSURE_LIMITED,
        "open_records_considered": len(rows),
        "rows_newness_not_stated": unstated,
        "starting_band": starting_band,
        "displacement": displacement,
        "band_from_rate": band,
        "override_fired": bool(hits), "override_hits": sorted(set(hits)),
        "override_words": ("Red for any open life-safety or structural nonconformance, code or "
                           "permit compliance failure, critical inspection or hold-point "
                           "failure, commissioning or turnover-blocking nonconformance, or a "
                           "repeat NCR for the same root cause after a corrective action was "
                           "recorded closed."),
        "band": "Red" if hits else band,
        "band_basis_id": OWNER_BASIS_ID,
        "boundary": ("under 2 per 100 no downgrade; 2 to under 5 down one band from the rating "
                     "the report stated; 5 to under 10 down two bands; 10 or more Red. Each "
                     "boundary is INCLUSIVE ON ITS LOWER SIDE. Newly opened NCRs only."
                     + _EXPOSURE_WORDS[exposure]
                     + ("" if starting_band else
                        " NO STARTING BAND: this firm states no rating, so a displacement rung "
                        "has nothing to move and produces no band. Only the Red rung, which is "
                        "stated absolutely, can band this factor here.")),
    }


def factor_failed_inspections(records, denom) -> dict[str, Any]:
    """
    Inspections of that firm failed on FIRST inspection / inspections performed x 100.

    A REINSPECTION NEITHER EXPANDS THE DENOMINATOR NOR COUNTS AGAIN. The denominator is the
    document's own `inspections_performed` for that firm, which the contract states must exclude
    reinspections; the numerator excludes any row the document marks as a reinspection.
    """
    rows = [r for r in records if _w(r.get("record_kind")) in _KIND_INSPECTION_FAIL and is_open(r)]
    first = [r for r in rows if _truthy(r.get("record_is_reinspection")) is not True]
    hits = sorted({f"{r.get('record_reference')}: {w}"
                   for r in first for w in _words_of(r) if w in _INSPECTION_OVERRIDE})
    return _rate_factor(
        factor="failed_inspections",
        measure="inspections of that firm failed on first inspection / inspections performed x 100",
        numerator=len(first), denominator=denom,
        denominator_field="inspections_performed",
        rungs=_PCT_2_5_10, floor_band="Green", scale=100.0,
        boundary=("under 2 per cent Green; 2 to under 5 per cent Yellow; 5 to under 10 per cent "
                  "Amber; 10 per cent or more Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. "
                  "First outcome only: a reinspection neither expands the denominator nor "
                  "counts again."),
        override_hits=hits,
        override_words=("Red for any failed life-safety, structural, code-required, hold-point "
                        "or turnover-blocking inspection."),
        extra={"reinspections_excluded": len(rows) - len(first)})


def factor_safety(records, recordables, hours) -> dict[str, Any]:
    """
    Firm TRIR = recordables x 200,000 / hours worked by that firm, ROLLING TWELVE MONTHS.

    THE FORMULA IS CODIFIED AND THE CUTS ARE THE OWNER'S, and this module records that split
    rather than blurring it: `band_basis_id` names the OSHA formula, `boundary_basis_id` names
    the owner's tolerance. This is the same distinction Run 107 built as
    `band_basis_provenance_class` / `band_boundary_provenance_class`.

    THE SMALL-EXPOSURE RULE IS NOT SECTION 1.3'S. The owner's words for safety are "below 10,000
    exposure hours, SHOW THE RATE with a small-exposure warning -- do not replace it with a raw
    count". So the band stands and the warning rides with it.
    """
    hits = sorted({f"{r.get('record_reference')}: {w}"
                   for r in records if is_open(r)
                   for w in _words_of(r) if w in _SAFETY_OVERRIDE_WORDS})
    rate = band = None
    small = None
    if hours is not None and hours > 0 and recordables is not None:
        rate = (float(recordables) * OSHA_TRIR_CONSTANT) / float(hours)
        band = _ladder(rate, _TRIR_RUNGS, "Green")
        small = hours < SAFETY_SMALL_EXPOSURE_HOURS
    return {
        "factor": "safety",
        "measure": "recordables x 200,000 / hours worked by that firm, rolling twelve months",
        "numerator": recordables, "denominator": hours,
        "denominator_field": "exposure_hours",
        "rate": None if rate is None else round(rate, 4), "rate_scale": "TRIR",
        "exposure_class": (EXPOSURE_NO_DENOMINATOR if rate is None
                           else ("small_exposure" if small else EXPOSURE_FULL)),
        "limited_exposure": bool(small),
        "small_exposure_hours_warning": (
            ("This firm worked fewer than 10,000 exposure hours in the rolling twelve months, so "
             "the rate rests on a small exposure base and a single recordable moves it a long "
             "way. The rate is shown rather than replaced by a raw count, which is the owner's "
             "own instruction.") if small else None),
        "band_from_rate": band,
        "override_fired": bool(hits), "override_hits": hits,
        "override_words": ("Red for a fatality, a serious life-threatening event, a stop-work "
                           "order, or an unresolved high-severity safety violation."),
        "band": "Red" if hits else band,
        "band_basis_id": OSHA_TRIR_BASIS_ID,
        "boundary_basis_id": OWNER_BASIS_ID,
        "boundary": ("under 1.0 Green; 1.0 to under 2.0 Yellow; 2.0 to under 3.0 Amber; 3.0 or "
                     "more Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. THE FORMULA IS "
                     "OSHA'S -- recordables x 200,000 / hours worked -- and is codified; THE "
                     "CUTS ON IT ARE THE OWNER'S CONFIGURED TOLERANCE and are not published "
                     "anywhere. The two provenances are recorded separately."
                     + (" NO RATE: no exposure hours are stated for this firm, so no rate is "
                        "formed and none is assumed." if rate is None else "")),
    }


def factor_environmental(records, denom) -> dict[str, Any]:
    """Firm environmental actions overdue / firm environmental actions due x 100."""
    rows = [r for r in records if _w(r.get("record_kind")) in _KIND_ENVIRONMENTAL and is_open(r)]
    overdue = [r for r in rows if _w(r.get("record_status")) in _OVERDUE_WORDS]
    # THE VOCABULARY IS `_ENV_OVERRIDE`, Run 102's closed set, UNWIDENED.
    hits = sorted({f"{r.get('record_reference')}: {w}"
                   for r in rows for w in _words_of(r) if w in _ENV_OVERRIDE})
    exposure = _exposure_class(denom)
    rate = band = None
    if exposure in (EXPOSURE_FULL, EXPOSURE_LIMITED):
        rate = (len(overdue) / float(denom)) * 100.0
        band = _zero_is_green(rate, _ZERO_5_10)
    return {
        "factor": "environmental",
        "measure": "firm environmental actions overdue / firm environmental actions due x 100",
        "numerator": len(overdue), "denominator": denom,
        "denominator_field": "environmental_actions_due",
        "rate": None if rate is None else round(rate, 4), "rate_scale": "per 100",
        "exposure_class": exposure, "limited_exposure": exposure == EXPOSURE_LIMITED,
        "band_from_rate": band,
        "override_fired": bool(hits), "override_hits": hits,
        "override_words": ("Red for any open critical permit violation, enforcement notice, "
                           "spill, stop-work condition, or overdue high-severity corrective "
                           "action."),
        "band": "Red" if hits else band,
        "band_basis_id": OWNER_BASIS_ID,
        "boundary": ("0 per cent Green; above 0 to under 5 per cent Yellow; 5 to under 10 per "
                     "cent Amber; 10 per cent or more Red. Each boundary is INCLUSIVE ON ITS "
                     "LOWER SIDE and exactly nought is the only Green."
                     + _EXPOSURE_WORDS[exposure]),
    }


def factor_quality_audit(records, denom) -> dict[str, Any]:
    """
    MAJOR findings attributed to the firm / audits covering the firm.

    MINOR DOCUMENTATION OBSERVATIONS ARE NOT COUNTED, and neither is a finding that states no
    severity at all: it enters no arm and is reported, because deciding for it would decide the
    factor. This is a RATIO, not a percentage -- the owner's cuts are 0 / above 0 / 1.0 / 2.0.
    """
    rows = [r for r in records if _w(r.get("record_kind")) in _KIND_AUDIT and is_open(r)]
    major = [r for r in rows if _w(r.get("record_severity")) in _MAJOR_WORDS]
    minor = [r for r in rows if _w(r.get("record_severity")) in _MINOR_WORDS]
    hits = sorted({f"{r.get('record_reference')}: {w}"
                   for r in rows for w in _words_of(r) if w in _AUDIT_OVERRIDE})
    exposure = _exposure_class(denom)
    rate = band = None
    if exposure in (EXPOSURE_FULL, EXPOSURE_LIMITED):
        rate = len(major) / float(denom)
        band = _zero_is_green(rate, _AUDIT_RUNGS)
    return {
        "factor": "quality_audit",
        "measure": "major findings attributed to the firm / audits covering the firm",
        "numerator": len(major), "denominator": denom,
        "denominator_field": "audits_covering_firm",
        "rate": None if rate is None else round(rate, 4), "rate_scale": "a ratio",
        "exposure_class": exposure, "limited_exposure": exposure == EXPOSURE_LIMITED,
        "minor_findings_not_counted": len(minor),
        "findings_stating_no_severity": len(rows) - len(major) - len(minor),
        "band_from_rate": band,
        "override_fired": bool(hits), "override_hits": hits,
        "override_words": ("Red for any critical finding affecting life safety, structural "
                           "integrity, code compliance, a hold point, or commissioning and "
                           "turnover."),
        "band": "Red" if hits else band,
        "band_basis_id": OWNER_BASIS_ID,
        "boundary": ("0 Green; above 0 to under 1.0 Yellow; 1.0 to under 2.0 Amber; 2.0 or more "
                     "Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. Minor documentation "
                     "observations are not counted." + _EXPOSURE_WORDS[exposure]),
    }


def factor_procurement(records, denom) -> dict[str, Any]:
    """
    TWO ARMS, WORST OF THEM, which is the owner's own word for how they combine.

    THE RATE ARM is items delivered after their required-on-site date over items due. THE DAYS-
    LATE ARM is a FLOOR on any single item: 1 to 5 working days at least Yellow, 6 to 10 at
    least Amber, more than 10 Red. A floor is not a band of its own -- it cannot make the factor
    better than the rate arm made it, only worse -- which is why `worst` and not an average.

    THE FLOOR SURVIVES THE SMALL-DENOMINATOR SAFEGUARD. Section 1.3 suppresses a RATE; the
    days-late arm is not a rate, it is a property of one item, and one item eleven working days
    late is eleven days late whether the register holds three items or three hundred.
    """
    rows = [r for r in records if _w(r.get("record_kind")) in _KIND_PROCUREMENT and is_open(r)]
    late = [r for r in rows if (_n(r.get("record_days_late")) or 0) > 0]
    hits = sorted({f"{r.get('record_reference')}: a late delivery causes a contractual, turnover "
                   f"or approved critical-path milestone to forecast late"
                   for r in rows if _truthy(r.get("record_milestone_forecast_late")) is True})
    floor = None
    worst_days = None
    for r in late:
        d = _n(r.get("record_days_late"))
        if d is None:
            continue
        worst_days = d if worst_days is None else max(worst_days, d)
        f = "Red" if d > 10 else ("Amber" if d >= 6 else "Yellow")
        floor = f if floor is None else worst([floor, f])
    exposure = _exposure_class(denom)
    rate = rate_band = None
    if exposure in (EXPOSURE_FULL, EXPOSURE_LIMITED):
        rate = (len(late) / float(denom)) * 100.0
        rate_band = _zero_is_green(rate, _ZERO_5_10)
    band = worst([b for b in (rate_band, floor) if b])
    return {
        "factor": "procurement",
        "measure": ("firm items delivered after their required-on-site date / firm items due "
                    "x 100, and a days-late floor on any single item; the worst of the two"),
        "numerator": len(late), "denominator": denom,
        "denominator_field": "items_due",
        "rate": None if rate is None else round(rate, 4), "rate_scale": "per 100",
        "exposure_class": exposure, "limited_exposure": exposure == EXPOSURE_LIMITED,
        "rate_arm_band": rate_band,
        "days_late_floor_band": floor,
        "worst_single_item_days_late": worst_days,
        "band_from_rate": band,
        "override_fired": bool(hits), "override_hits": hits,
        "override_words": ("Red if any late delivery causes a contractual, turnover or approved "
                           "critical-path milestone to forecast late."),
        "band": "Red" if hits else band,
        "band_basis_id": OWNER_BASIS_ID,
        "boundary": ("RATE ARM: 0 per cent Green; above 0 to under 5 per cent Yellow; 5 to "
                     "under 10 per cent Amber; 10 per cent or more Red. DAYS-LATE ARM, a FLOOR "
                     "on any single item: 1 to 5 working days at least Yellow; 6 to 10 at least "
                     "Amber; more than 10 Red. The worst of the two arms governs. Each boundary "
                     "is INCLUSIVE ON ITS LOWER SIDE. The days-late floor is not suppressed by "
                     "the small-denominator safeguard, which suppresses rates."
                     + _EXPOSURE_WORDS[exposure]),
    }


def factor_field_observations(records, denom) -> dict[str, Any]:
    """
    CONFIRMED defect observations attributed to the firm / field reports covering that firm's
    active work x 100. Not every comment -- only confirmed defect observations after review, so
    a row that does not state confirmation is not counted and is reported.
    """
    rows = [r for r in records if _w(r.get("record_kind")) in _KIND_FIELD and is_open(r)]
    confirmed = [r for r in rows if _truthy(r.get("record_confirmed")) is True]
    hits = sorted({f"{r.get('record_reference')}: {w}"
                   for r in confirmed for w in _words_of(r) if w in _FIELD_OVERRIDE})
    return _rate_factor(
        factor="field_observations",
        measure=("confirmed defect observations attributed to the firm / field reports covering "
                 "that firm's active work x 100"),
        numerator=len(confirmed), denominator=denom,
        denominator_field="field_reports_covering_firm",
        rungs=_PCT_2_5_10, floor_band="Green", scale=100.0,
        boundary=("under 2 Green; 2 to under 5 Yellow; 5 to under 10 Amber; 10 or more Red. Each "
                  "boundary is INCLUSIVE ON ITS LOWER SIDE. Only CONFIRMED defect observations "
                  "after review are counted; not every comment."),
        override_hits=hits,
        override_words=("Red for any reported AND VERIFIED structural, life-safety, code or "
                        "work-stoppage condition attributable to the firm."),
        extra={"observations_not_confirmed": len(rows) - len(confirmed)})


def factor_commissioning(records, denom) -> dict[str, Any]:
    """Firm systems or items failing FIRST acceptance test / systems or items tested x 100."""
    rows = [r for r in records if _w(r.get("record_kind")) in _KIND_COMMISSIONING and is_open(r)]
    first = [r for r in rows if _truthy(r.get("record_is_reinspection")) is not True]
    hits = sorted({f"{r.get('record_reference')}: {w}"
                   for r in first for w in _words_of(r) if w in _COMMISSIONING_OVERRIDE})
    exposure = _exposure_class(denom)
    rate = band = None
    if exposure in (EXPOSURE_FULL, EXPOSURE_LIMITED):
        rate = (len(first) / float(denom)) * 100.0
        band = _zero_is_green(rate, _ZERO_5_10)
    return {
        "factor": "commissioning",
        "measure": ("firm systems or items failing first acceptance test / systems or items "
                    "tested x 100"),
        "numerator": len(first), "denominator": denom,
        "denominator_field": "systems_tested",
        "rate": None if rate is None else round(rate, 4), "rate_scale": "per 100",
        "exposure_class": exposure, "limited_exposure": exposure == EXPOSURE_LIMITED,
        "retests_excluded": len(rows) - len(first),
        "band_from_rate": band,
        "override_fired": bool(hits), "override_hits": hits,
        "override_words": ("Red if a system fails a critical life-safety, functional-"
                           "performance, regulatory or turnover acceptance test."),
        "band": "Red" if hits else band,
        "band_basis_id": OWNER_BASIS_ID,
        "boundary": ("0 per cent Green; above 0 to under 5 per cent Yellow; 5 to under 10 per "
                     "cent Amber; 10 per cent or more Red. Each boundary is INCLUSIVE ON ITS "
                     "LOWER SIDE. FIRST acceptance test only." + _EXPOSURE_WORDS[exposure]),
    }


FACTOR_NAMES: tuple[str, ...] = (
    "nonconformances", "failed_inspections", "safety", "environmental",
    "quality_audit", "procurement", "field_observations", "commissioning")


# =================================================================================================
# THE FIRM POSTURE
# =================================================================================================

AVERAGE_WORDS = (
    "The trade factors weigh EQUALLY and average. Each factor that produced a band scores "
    "Green +2, Yellow +1, Amber -1, Red -2 -- the platform's existing scale, imported from "
    "`category_posture` rather than restated -- and the mean is banded on the platform's "
    "existing cuts: at or above 1.5 Green, at or above 0.5 Yellow, at or above -0.5 Amber, "
    "below -0.5 Red. A factor that produced NO band (no denominator, too few in the "
    "denominator, or nothing to measure) is not in the mean and is NOT counted as zero, on the "
    "same reasoning `category_posture` records: a fabricated middling reading is "
    "indistinguishable from a measured one once it reaches the arithmetic.")

STOP_WORK_WORDS = (
    "A STOP-WORK ORDER IS THE HIGHEST SEVERITY THIS PLATFORM HAS. The owner's words: it means "
    "an emergency, it impacts everything, and if there were a band above Red he would give it "
    "one. It sets the firm Red, it bypasses the average, and no other factor pulls it back. It "
    "is recorded as its own class of override so that a reader can tell it apart from the "
    "ordinary hard overrides, which also set Red but are not described in those terms.")


def firm_posture(*, subcontractor: str, starting_band: str | None, records, denominators,
                 newness) -> dict[str, Any]:
    """
    One firm's adjusted posture: eight factors, the average, the overrides and the stop-work bypass.

    `starting_band` is the posture the Subcontractor Performance Report's own rating normalised
    to, or None where the firm states no rating -- section 1.4, "a firm with trade records and
    no stated rating is assessed from the records". THE SOURCE RATING IS NEVER ALTERED: it is
    carried through on the record beside the adjusted posture, never over it.
    """
    d = denominators if isinstance(denominators, Mapping) else {}
    recs = [r for r in records if isinstance(r, Mapping)]
    factors = [
        factor_nonconformances(recs, _n(d.get("inspections_performed")),
                               starting_band=starting_band, newness=newness),
        factor_failed_inspections(recs, _n(d.get("inspections_performed"))),
        factor_safety(recs, _n(d.get("recordable_incidents")), _n(d.get("exposure_hours"))),
        factor_environmental(recs, _n(d.get("environmental_actions_due"))),
        factor_quality_audit(recs, _n(d.get("audits_covering_firm"))),
        factor_procurement(recs, _n(d.get("items_due"))),
        factor_field_observations(recs, _n(d.get("field_reports_covering_firm"))),
        factor_commissioning(recs, _n(d.get("systems_tested"))),
    ]
    by_name = {f["factor"]: f for f in factors}

    stop = stop_work_hits(recs)
    overrides = [f["factor"] for f in factors if f["override_fired"]]
    banded_factors = [f for f in factors if f["band"]]
    mean = (sum(BAND_SCORE[f["band"]] for f in banded_factors) / len(banded_factors)
            if banded_factors else None)
    averaged = band_average([BAND_SCORE[f["band"]] for f in banded_factors])

    if stop:
        posture, rule = "Red", "stop_work_order"
    elif overrides:
        posture, rule = "Red", "hard_override"
    elif averaged is not None:
        posture, rule = averaged, "average_of_factor_bands"
    else:
        # NO FACTOR PRODUCED A BAND. The firm is exactly what its report said it was, which is
        # the Run 107 behaviour, unchanged. This is the arm that keeps the census from moving
        # backwards on every project that carries no trade records at all.
        posture, rule = starting_band, "source_rating_unadjusted"

    adjustment = None
    if starting_band and posture and starting_band != posture:
        adjustment = ("down " if _RANK[posture] > _RANK[starting_band] else "up ") + str(
            abs(_RANK[posture] - _RANK[starting_band])) + " band(s) from the stated rating"
    elif starting_band and posture:
        adjustment = "no movement from the stated rating"

    return {
        "subcontractor": subcontractor,
        "source_rating_band": starting_band,
        "adjusted_posture": posture,
        "adjustment": adjustment,
        "adjustment_rule": rule,
        "factor_bands": {f["factor"]: f["band"] for f in factors},
        "factor_rates": {f["factor"]: f.get("rate") for f in factors},
        "factors": factors,
        "factors_banded": [f["factor"] for f in banded_factors],
        "factors_not_banded": [f["factor"] for f in factors if not f["band"]],
        "factor_mean_score": None if mean is None else round(mean, 4),
        "overrides_fired": overrides,
        "override_detail": {f["factor"]: f["override_hits"] for f in factors
                            if f["override_fired"]},
        "stop_work_orders": stop,
        "stop_work_bypass": bool(stop),
        "limited_exposure_factors": [f["factor"] for f in factors if f.get("limited_exposure")],
        "no_rate_banding_factors": [f["factor"] for f in factors
                                    if f.get("exposure_class") == EXPOSURE_TOO_FEW],
        "open_record_count": sum(1 for r in recs if is_open(r)),
        "closed_records_not_counted": sum(1 for r in recs if not is_open(r)),
        "denominators": dict(d),
        "average_words": AVERAGE_WORDS,
        "stop_work_words": STOP_WORK_WORDS if stop else None,
        "band_basis_id": OWNER_BASIS_ID,
        "rule_version": "run118.subcontractor_trade_factors.v1",
        "by_name": by_name,
    }


def governing(postures: list[dict[str, Any]]) -> dict[str, Any] | None:
    """ACROSS FIRMS, THE MOST ADVERSE POSTURE GOVERNS -- Run 115's rule, unchanged."""
    rated = [p for p in postures if p.get("adjusted_posture") in _RANK]
    if not rated:
        return None
    return max(rated, key=lambda p: (_RANK[p["adjusted_posture"]], str(p["subcontractor"])))
