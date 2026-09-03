"""
RUN 120. A CONTRACTOR IS A DELIVERY ACTOR -- the owner's four factors, in one place.

WHAT RUN 119 REFUSED TO DECIDE, AND WHAT THE OWNER'S RULING DID TO IT. Run 119 established
Goal 4's blocker and correctly declined to choose a side: A6.4 Contractor Performance cannot
average the postures of A6.1 Quality Compliance, A6.2 Safety and A6.3 Environmental while
sitting inside A6 Delivery Quality, because that category is WORST-WINS and those three would
count twice -- once directly, once through the contractor's average -- and it would import
schedule and cost adversity into a category where schedule and cost already vote in their own
right.

THE OWNER'S RULING DISSOLVES THE BLOCKER RATHER THAN CHOOSING A SIDE. Contractor Performance
reads FIRM-LEVEL PROJECT RECORDS, not module postures. Nothing is counted twice, no adversity
leaks between categories, and Contractor Performance stays inside Delivery Quality. NO MODULE
POSTURE IS READ ANYWHERE IN THIS FILE -- that is checkable by reading it, and section 7.2 of the
order asks for exactly that confirmation.

THE OWNER'S REASONING, RECORDED AS THE BASIS: a contractor is a delivery actor, not a quality
signal. A firm that misses planned workfront dates, cannot staff planned work, delays material
release or fails to complete predecessor work moves the controlling path directly. SCHEDULE
RELIABILITY IS THEREFORE THE DOMINANT FACTOR, not an NCR count -- which is why it carries 0.40
of the weight and quality execution carries 0.25.

THE CHAIN: firm-level records -> four factors -> firm posture -> worst active firm -> the
module -> Delivery Quality.

=================================================================================================
THE SEVERITY SCALE, AND WHY IT IS NOT A SECOND SCALE AFTER ALL
=================================================================================================

The order's section 3 asks whether `category_posture`'s constants can be reused for "Green 0,
Yellow 1, Amber 2, Red 3", and warns that a second scale silently disagreeing with the first
would be worse than an honest separate one. BOTH HALVES OF THAT QUESTION WERE MEASURED AGAINST
THE TREE AND THE ANSWER IS IN TWO PARTS.

  `category_posture.BAND_SCORE` CANNOT BE REUSED, and not because of a rescaling. It is
  {Green +2.0, Yellow +1.0, Amber -1.0, Red -2.0}: HIGHER IS BETTER, the magnitudes are not
  proportional to 0/1/2/3, it straddles zero, and its cuts (`AVERAGE_CUTS`, at 1.5 / 0.5 / -0.5)
  are read as "at or above this cut is this band" on a scale where above means better. The
  owner's severity here is the opposite direction with different magnitudes and different cut
  semantics. Importing it and negating it is exactly the silent disagreement the order warns
  about, and it is not done.

  BUT THE OWNER'S SCALE IS NOT NEW EITHER, and this is the part the order did not anticipate.
  `fusion.BAND_SEVERITY` is ALREADY {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3} -- the
  owner's four numbers, verbatim, shipped, and already imported by `category_posture`,
  `pm_review` and `project_posture` as the platform's one severity ordering. So no second scale
  is written here. `BAND_SEVERITY` is IMPORTED and used as the factor score, and the distance
  between two bands cannot come to mean one thing in this module and another in the hold that
  reviews it.

  WHAT IS GENUINELY NEW AND OWNER-CONFIGURED is the WEIGHTING (0.40 / 0.25 / 0.20 / 0.15) and
  the CUTS ON THE WEIGHTED RESULT (0.50 / 1.25 / 2.00). Those are the owner's own numbers, they
  appear nowhere else in this tree, and they are below.

=================================================================================================
THE ELIGIBILITY RULE -- ALL FOUR OR NONE. Section 4, and it is the guardrail.
=================================================================================================

A four-factor firm posture is eligible ONLY where ALL FOUR factor values can be calculated from
firm-attributed records for the SAME reporting period. Otherwise the project-supplied source
rating is used, unchanged. If neither is available, Not Assessed.

THE TWO ARE NEVER BLENDED. A partial four-factor calculation combined with a source rating
counts the same evidence twice and makes a contractor look better than the evidence supports. A
missing safety or commercial factor must not quietly improve a firm's posture. A factor that
cannot be calculated is marked UNAVAILABLE and is never treated as Green.

=================================================================================================
WHERE THE NUMBERS COME FROM, AND WHY NO NUMERATOR IS DERIVED FROM SILENCE
=================================================================================================

Every factor's numerator AND denominator is a figure the DOCUMENT counts, read off
`trade_denominators_json` per firm -- the table Run 118 built, extended by this run with the two
populations it did not carry. This follows Run 118's safety factor exactly, where BOTH
`recordable_incidents` and `exposure_hours` are stated figures, and it follows Run 118's
recorded refusal to derive a denominator from how many attribution rows happened to arrive.

A DERIVED QUALITY NUMERATOR WAS CONSIDERED AND REJECTED. Passed-on-first could be computed as
`inspections_performed` minus the firm's failed-first inspection rows. On a document that states
an inspection count and carries NO inspection rows that arithmetic yields "every inspection
passed" -- a MANUFACTURED GREEN out of silence, which is the same defect Run 118 iteration 5
caught when a denominator row alone created a clean firm. So the numerator is stated or the
factor is unavailable.

THE ATTRIBUTION ROWS ARE WHAT THE OVERRIDES READ, and the evidence references behind each
factor. They are never a population.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

#: THE PLATFORM'S ONE SEVERITY ORDERING -- {Green 0, Yellow 1, Amber 2, Red 3}. IMPORTED, not
#: restated, and it is already exactly the scale the owner's section 3 states. See the module
#: docstring for why `category_posture.BAND_SCORE` is NOT the thing imported here.
from .fusion import BAND_SEVERITY

#: THE CODIFIED HALF OF THE SAFETY FACTOR, shared with Run 118's engine rather than copied: one
#: OSHA formula, one constant, one basis identifier on this platform. The CUTS on it are the
#: owner's and are defined below, in this module, because they are A6.4's own configuration.
from .trade_factors import OSHA_TRIR_BASIS_ID, OSHA_TRIR_CONSTANT

#: THE SAFETY OVERRIDE VOCABULARY, Run 101's closed set, IMPORTED AND NOT WIDENED. The owner's
#: A6.4 sentence -- "a fatality, a life-threatening event, a stop-work order, or an unresolved
#: severe safety violation" -- is the same condition Run 101 built this set for. A severity word
#: matching none of its members fires nothing rather than being dropped to the nearest.
from .models_cat89 import _SAFETY_OVERRIDE_WORDS

_ORDER: tuple[str, ...] = ("Green", "Yellow", "Amber", "Red")

#: THE OWNER'S BAND BASIS IDENTIFIER for every threshold in this module except the OSHA formula.
#: It is an owner string and it goes where owner strings go -- `band_basis_id` -- and NOT into
#: `THRESHOLD_SOURCES`, which stays exactly three values wide. Run 103's precedent, which the
#: order names in terms.
OWNER_BASIS_ID = "owner_configured_contractor_delivery_tolerance"

#: Section 3. The owner's weights. Schedule reliability is DOMINANT by the owner's own reasoning.
WEIGHTS: dict[str, float] = {
    "schedule_reliability": 0.40,
    "quality_execution": 0.25,
    "safety": 0.20,
    "commercial_administration": 0.15,
}

#: Section 3. The cuts on the weighted severity, ADVERSE FIRST, each read as "at or above this
#: cut". Green is the open bottom (0.00 to under 0.50). Nothing else in this tree holds them.
WEIGHTED_CUTS: tuple[tuple[float, str], ...] = ((2.00, "Red"), (1.25, "Amber"), (0.50, "Yellow"))

WEIGHTED_BOUNDARY_WORDS = (
    "Each factor's band scores a SEVERITY -- Green 0, Yellow 1, Amber 2, Red 3, the platform's "
    "existing `fusion.BAND_SEVERITY` ordering, imported rather than restated -- and the four "
    "severities are weighted 0.40 schedule reliability, 0.25 quality execution, 0.20 safety, "
    "0.15 commercial and administration. HIGHER IS WORSE on this scale, which is the inverse of "
    "the +2/+1/-1/-2 scale the category arithmetic averages on; the two are not the same scale "
    "and neither is derived from the other. The weighted result bands: 0.00 to under 0.50 "
    "Green; 0.50 to under 1.25 Yellow; 1.25 to under 2.00 Amber; 2.00 to 3.00 Red. Each "
    "boundary is INCLUSIVE ON ITS LOWER SIDE.")

OVERRIDE_WORDS = (
    "OVERRIDES APPLY AFTER THE WEIGHTED CALCULATION, and the final posture is the WORSE of the "
    "weighted result and any override that fired. A contractor with a severe safety incident or "
    "a controlling-path delay must not receive an acceptable grade because it is otherwise "
    "strong. An override never improves a posture: it can only make it worse or leave it "
    "unchanged.")

ELIGIBILITY_WORDS = (
    "ALL FOUR OR NONE. A four-factor firm posture is eligible only where all four factor values "
    "can be calculated from firm-attributed records for the same reporting period. Where any "
    "one of them cannot, the four-factor calculation is DISCARDED ENTIRELY and the "
    "project-supplied source rating is used in its place, unchanged. The two are NEVER blended: "
    "a partial four-factor calculation combined with a source rating counts the same evidence "
    "twice and makes a contractor look better than the evidence supports. A factor that cannot "
    "be calculated is marked UNAVAILABLE and is never treated as Green. Where neither a "
    "complete four-factor calculation nor a source rating is available the firm is Not Assessed.")

ACTIVE_WORK_WORDS = (
    "ACROSS FIRMS THE WORST FINAL POSTURE GOVERNS, among firms with ACTIVE WORK in the "
    "reporting period. Active work is read from the `active_work` column the firm's own "
    "denominator row states, and from nowhere else -- it is never inferred from the presence of "
    "records or of a population. A firm the documents state has NO active work this period is "
    "excluded from the comparison and the exclusion is reported. A firm that STATES NOTHING is "
    "carried in the comparison, because excluding on silence would let an adverse firm vanish "
    "from a project's reading, and that is the one direction of error this platform will not "
    "take. Which firms stated it, and which did not, is on the record.")

#: Section 5. This is a LOCAL calculation inside the module. It does not touch the
#: project-level weighted voting profile, and nothing here reads a category or a module posture.
SCOPE_WORDS = (
    "This is a LOCAL calculation inside A6.4. It reads firm-level project records and NO module "
    "posture: not A6.1's, not A6.2's, not A6.3's, and no category's. Nothing is counted twice "
    "and no adversity is imported from another category. It does not touch the project-level "
    "weighted voting profile.")

RULE_VERSION = "run120.contractor_delivery_factors.v1"

FACTOR_NAMES: tuple[str, ...] = (
    "schedule_reliability", "quality_execution", "safety", "commercial_administration")


# =================================================================================================
# READING WHAT A DOCUMENT PRINTED. Never a default, never a coercion of prose.
# =================================================================================================


def _n(v) -> float | None:
    """A number the document printed, or None."""
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


def _truthy(v) -> bool | None:
    """Yes / no as a document prints it, or None where it printed nothing. Never defaulted."""
    w = _w(v)
    if w in ("", "n/a", "na", "none", "not_stated", "unknown", "tbd"):
        return None
    if w in ("y", "yes", "true", "t", "1", "1.0", "active", "working", "on_site", "mobilised",
             "mobilized", "in_progress"):
        return True
    if w in ("n", "no", "false", "f", "0", "0.0", "inactive", "not_active", "demobilised",
             "demobilized", "complete", "completed", "no_active_work", "off_site"):
        return False
    return None


def _words_of(rec: Mapping[str, Any]) -> set[str]:
    """Every word a record printed that an override may be looking for, normalised."""
    return {_w(rec.get(k)) for k in ("record_severity", "record_kind", "record_status")} - {""}


#: The status words that mean a record has stopped counting. Run 118's set, imported in spirit
#: and restated here ONLY because A6.4's quality override is defined over an OPEN nonconformance
#: and must not change meaning when Run 118's own section 1.4 sentence is next amended.
_CLOSED_WORDS: frozenset = frozenset({
    "closed", "close", "resolved", "complete", "completed", "cleared", "accepted",
    "verified_closed",
})


def is_open(rec: Mapping[str, Any]) -> bool:
    """A record printing NO status is treated as OPEN: it is not closed until the document
    says so, and assuming closure would silently discard evidence."""
    return _w(rec.get("record_status")) not in _CLOSED_WORDS


# =================================================================================================
# THE FOUR OVERRIDE VOCABULARIES
#
# Every word below is lifted from the owner's own section 2 sentence for that factor. A record
# whose severity, kind or status word is none of them fires NOTHING; it is reported unranked
# rather than being dropped to the nearest word that would have fired.
#
# THESE ARE A6.4's OWN SETS AND NOT RUN 118's, EXCEPT FOR SAFETY. Run 118's `_NCR_OVERRIDE` was
# written from a DIFFERENT owner sentence in a different order for a different module. The two
# overlap heavily and they are not the same set, and binding them together would mean that
# amending one owner sentence silently amends the other module. Safety is the exception because
# there the closed set IS the platform's one safety vocabulary, Run 101's, and it is imported.
# =================================================================================================

#: "an open CRITICAL STRUCTURAL, LIFE-SAFETY, CODE, HOLD-POINT or COMMISSIONING-BLOCKING
#: nonconformance"
_QUALITY_OVERRIDE: frozenset = frozenset({
    "critical", "critical_nonconformance", "structural", "structural_nonconformance",
    "life_safety", "life_safety_nonconformance", "code", "code_compliance_failure",
    "code_required", "hold_point", "hold_point_failure",
    "commissioning_blocking", "commissioning_or_turnover_blocking",
})

#: The kinds that ARE nonconformances, for the quality override's population.
_KIND_NCR: frozenset = frozenset({
    "nonconformance", "non_conformance", "ncr", "nonconformity", "non_conformity"})

#: Section 2, schedule reliability: the record kinds that are a firm's WORK PACKAGE OR MILESTONE
#: commitment. These are the evidence references behind the schedule factor and the population
#: the schedule override reads; they are never a denominator.
_KIND_SCHEDULE: frozenset = frozenset({
    "work_package", "workpackage", "package", "milestone", "schedule_activity", "activity",
    "workfront", "planned_workfront", "predecessor", "schedule_commitment"})

#: Section 2, commercial and administration. The owner's own list of what a COMMITMENT is: "a
#: required submittal, an RFI response, a procurement release or delivery, a corrective-action
#: closure, or a required change-document response." Each word below sits under one of those five.
_KIND_COMMITMENT: frozenset = frozenset({
    "submittal", "required_submittal", "submittal_response",
    "rfi", "rfi_response", "rfi_answer",
    "procurement", "procurement_release", "procurement_item", "delivery", "material_release",
    "late_delivery", "late_item",
    "corrective_action", "corrective_action_closure", "capa",
    "change_document", "change_document_response", "change_order_response", "change_response",
    "commitment", "administrative_commitment"})


def _ladder_high_is_good(pct: float | None,
                         cuts: tuple[tuple[float, str], ...], floor: str) -> str | None:
    """A percentage ladder where MORE IS BETTER, walked best-first, inclusive on the lower side."""
    if pct is None:
        return None
    for cut, band in cuts:
        if pct >= cut:
            return band
    return floor


def _ladder_low_is_good(rate: float | None,
                        cuts: tuple[tuple[float, str], ...], floor: str) -> str | None:
    """A rate ladder where LESS IS BETTER, walked worst-first, inclusive on the lower side."""
    if rate is None:
        return None
    for cut, band in cuts:
        if rate >= cut:
            return band
    return floor


#: Section 2. The owner's four ladders. Every cut is his; none of them appears anywhere else.
_SCHEDULE_CUTS = ((95.0, "Green"), (90.0, "Yellow"), (80.0, "Amber"))
_QUALITY_CUTS = ((98.0, "Green"), (95.0, "Yellow"), (90.0, "Amber"))
_COMMERCIAL_CUTS = ((95.0, "Green"), (90.0, "Yellow"), (80.0, "Amber"))
_SAFETY_CUTS = ((3.0, "Red"), (2.0, "Amber"), (1.0, "Yellow"))


def _pct(num: float | None, den: float | None) -> float | None:
    """A percentage, or None. A zero or absent denominator NEVER produces a rate."""
    if num is None or den is None or den <= 0:
        return None
    return (float(num) / float(den)) * 100.0


def _factor(*, factor: str, measure: str, numerator, denominator,
            numerator_field: str, denominator_field: str,
            value: float | None, value_name: str, band: str | None,
            boundary: str, override_hits: list[str], override_words: str,
            unavailable_reason: str | None,
            evidence_references: list[str],
            band_basis_id: str = OWNER_BASIS_ID,
            extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    One factor's whole working. `band` is the ladder's band BEFORE any override; the override is
    recorded beside it and applied at the FIRM level, after the weighted calculation, which is
    the owner's section 3 in terms. A factor with no band is UNAVAILABLE and says why.
    """
    out: dict[str, Any] = {
        "factor": factor,
        "measure": measure,
        "numerator": numerator,
        "denominator": denominator,
        "numerator_field": numerator_field,
        "denominator_field": denominator_field,
        value_name: None if value is None else round(value, 4),
        "value": None if value is None else round(value, 4),
        "value_name": value_name,
        "band": band,
        "available": band is not None,
        "unavailable_reason": None if band is not None else unavailable_reason,
        "weight": WEIGHTS[factor],
        "severity": None if band is None else BAND_SEVERITY[band],
        "override_fired": bool(override_hits),
        "override_hits": sorted(set(override_hits)),
        "override_words": override_words,
        "evidence_references": sorted(set(evidence_references)),
        "band_basis_id": band_basis_id,
        "boundary": boundary + (
            " HARD OVERRIDE FIRED: " + override_words if override_hits else ""),
    }
    if extra:
        out.update(extra)
    return out


# =================================================================================================
# THE FOUR FACTORS
# =================================================================================================


def factor_schedule_reliability(records, denominators) -> dict[str, Any]:
    """
    Firm work packages or milestones completed on or before their committed date / firm packages
    due in the period x 100.

    THE OVERRIDE: Red if the firm causes a CONTROLLING-PATH ACTIVITY or a CONTRACTUAL MILESTONE
    to forecast late. That is read off `record_milestone_forecast_late`, the column Run 118
    already asks for and whose recognised headings already include `critical_path_impact`. It is
    not rebuilt.

    THE OVERRIDE IS EVALUATED WHATEVER THE FACTOR'S AVAILABILITY. A controlling-path delay is a
    finding whether or not the document also stated a package population.
    """
    d = denominators
    num = _n(d.get("packages_completed_on_time"))
    den = _n(d.get("packages_due"))
    rows = [r for r in records if _w(r.get("record_kind")) in _KIND_SCHEDULE]
    hits = [f"{r.get('record_reference')}: causes a controlling-path activity or a contractual "
            f"milestone to forecast late"
            for r in records if _truthy(r.get("record_milestone_forecast_late")) is True]
    pct = _pct(num, den)
    band = _ladder_high_is_good(pct, _SCHEDULE_CUTS, "Red")
    why = None
    if band is None:
        missing = [n for n, v in (("packages_completed_on_time", num), ("packages_due", den))
                   if v is None]
        why = ("this project's documents state no "
               + " and no ".join(missing or ["usable package population"])
               + " for this firm in this reporting period, so the schedule reliability factor "
                 "cannot be calculated. It is UNAVAILABLE and is not treated as Green."
               if missing else
               "the stated package population for this firm is zero, so no completion "
               "percentage is formed and none is assumed.")
    return _factor(
        factor="schedule_reliability",
        measure=("firm work packages or milestones completed on or before their committed date "
                 "/ firm packages due in the period x 100"),
        numerator=num, denominator=den,
        numerator_field="packages_completed_on_time", denominator_field="packages_due",
        value=pct, value_name="completion_percent", band=band,
        boundary=("95 per cent or more Green; 90 to under 95 Yellow; 80 to under 90 Amber; "
                  "under 80 Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. This is the "
                  "DOMINANT factor at 0.40 of the weight, on the owner's own reasoning: a firm "
                  "that misses planned workfront dates, cannot staff planned work, delays "
                  "material release or fails to complete predecessor work moves the controlling "
                  "path directly."),
        override_hits=hits,
        override_words=("Red if the firm causes a controlling-path activity or a contractual "
                        "milestone to forecast late."),
        unavailable_reason=why,
        evidence_references=[str(r.get("record_reference")) for r in rows],
        extra={"schedule_records_considered": len(rows)})


def factor_quality_execution(records, denominators) -> dict[str, Any]:
    """
    Firm inspections passed on FIRST inspection / firm inspections performed x 100.

    FIRST OUTCOME ONLY: a reinspection neither expands the denominator nor counts again. Both
    figures are the DOCUMENT'S OWN counts -- see the module docstring for why the numerator is
    never derived as `inspections_performed` minus the failed rows that happened to arrive.
    """
    d = denominators
    num = _n(d.get("inspections_passed_first"))
    den = _n(d.get("inspections_performed"))
    ncrs = [r for r in records if _w(r.get("record_kind")) in _KIND_NCR and is_open(r)]
    hits = [f"{r.get('record_reference')}: {w}"
            for r in ncrs for w in _words_of(r) if w in _QUALITY_OVERRIDE]
    pct = _pct(num, den)
    band = _ladder_high_is_good(pct, _QUALITY_CUTS, "Red")
    why = None
    if band is None:
        missing = [n for n, v in (("inspections_passed_first", num),
                                  ("inspections_performed", den)) if v is None]
        why = ("this project's documents state no "
               + " and no ".join(missing or ["usable inspection population"])
               + " for this firm in this reporting period, so the quality execution factor "
                 "cannot be calculated. It is UNAVAILABLE and is not treated as Green."
               if missing else
               "the stated inspection population for this firm is zero, so no first-pass "
               "percentage is formed and none is assumed.")
    return _factor(
        factor="quality_execution",
        measure=("firm inspections passed on first inspection / firm inspections performed "
                 "x 100"),
        numerator=num, denominator=den,
        numerator_field="inspections_passed_first", denominator_field="inspections_performed",
        value=pct, value_name="first_pass_percent", band=band,
        boundary=("98 per cent or more Green; 95 to under 98 Yellow; 90 to under 95 Amber; "
                  "under 90 Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. FIRST OUTCOME "
                  "ONLY: a reinspection neither expands the denominator nor counts again."),
        override_hits=hits,
        override_words=("Red for an open critical structural, life-safety, code, hold-point or "
                        "commissioning-blocking nonconformance."),
        unavailable_reason=why,
        evidence_references=[str(r.get("record_reference")) for r in ncrs],
        extra={"open_nonconformances_considered": len(ncrs)})


def factor_safety(records, denominators) -> dict[str, Any]:
    """
    Firm recordables x 200,000 / firm hours worked.

    THE FORMULA IS CODIFIED AND THE CUTS ARE THE OWNER'S, and the record says which is which:
    `band_basis_id` names the OSHA formula, `boundary_basis_id` names the owner's tolerance.
    That split is Run 107's `band_basis_provenance_class` / `band_boundary_provenance_class`
    distinction, and the order asks for it "the way the platform already does".
    """
    d = denominators
    num = _n(d.get("recordable_incidents"))
    den = _n(d.get("exposure_hours"))
    hits = [f"{r.get('record_reference')}: {w}"
            for r in records if is_open(r)
            for w in _words_of(r) if w in _SAFETY_OVERRIDE_WORDS]
    rate = None
    if num is not None and den is not None and den > 0:
        rate = (float(num) * OSHA_TRIR_CONSTANT) / float(den)
    band = _ladder_low_is_good(rate, _SAFETY_CUTS, "Green")
    why = None
    if band is None:
        missing = [n for n, v in (("recordable_incidents", num), ("exposure_hours", den))
                   if v is None]
        why = ("this project's documents state no "
               + " and no ".join(missing or ["usable exposure base"])
               + " for this firm in this reporting period, so the safety factor cannot be "
                 "calculated. It is UNAVAILABLE and is not treated as Green."
               if missing else
               "the stated exposure hours for this firm are zero, so no rate is formed and none "
               "is assumed.")
    return _factor(
        factor="safety",
        measure="firm recordables x 200,000 / firm hours worked",
        numerator=num, denominator=den,
        numerator_field="recordable_incidents", denominator_field="exposure_hours",
        value=rate, value_name="trir", band=band,
        boundary=("under 1.0 Green; 1.0 to under 2.0 Yellow; 2.0 to under 3.0 Amber; 3.0 or "
                  "more Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. THE FORMULA IS "
                  "OSHA'S -- recordables x 200,000 / hours worked -- and is CODIFIED; THE CUTS "
                  "ON IT ARE THE OWNER'S CONFIGURED TOLERANCE and are published nowhere. The two "
                  "provenances are recorded separately and are not blurred."),
        override_hits=hits,
        override_words=("Red for a fatality, a life-threatening event, a stop-work order, or an "
                        "unresolved severe safety violation."),
        unavailable_reason=why,
        evidence_references=[str(r.get("record_reference")) for r in records
                             if any(w in _SAFETY_OVERRIDE_WORDS for w in _words_of(r))],
        band_basis_id=OSHA_TRIR_BASIS_ID,
        extra={"boundary_basis_id": OWNER_BASIS_ID})


def factor_commercial_administration(records, denominators) -> dict[str, Any]:
    """
    Firm commitments met on time / firm commitments due x 100.

    A COMMITMENT IS THE OWNER'S OWN LIST: a required submittal, an RFI response, a procurement
    release or delivery, a corrective-action closure, or a required change-document response.
    `_KIND_COMMITMENT` holds exactly those five families and nothing else.

    THE OVERRIDE: Red if an UNFULFILLED administrative or procurement commitment DIRECTLY BLOCKS
    a controlling-path activity. Both halves are read: the record must be one of the commitment
    kinds, must still be OPEN, and must state the controlling-path impact.
    """
    d = denominators
    num = _n(d.get("commitments_met_on_time"))
    den = _n(d.get("commitments_due"))
    rows = [r for r in records if _w(r.get("record_kind")) in _KIND_COMMITMENT]
    unfulfilled = [r for r in rows if is_open(r)]
    hits = [f"{r.get('record_reference')}: an unfulfilled administrative or procurement "
            f"commitment directly blocks a controlling-path activity"
            for r in unfulfilled
            if _truthy(r.get("record_milestone_forecast_late")) is True]
    pct = _pct(num, den)
    band = _ladder_high_is_good(pct, _COMMERCIAL_CUTS, "Red")
    why = None
    if band is None:
        missing = [n for n, v in (("commitments_met_on_time", num), ("commitments_due", den))
                   if v is None]
        why = ("this project's documents state no "
               + " and no ".join(missing or ["usable commitment population"])
               + " for this firm in this reporting period, so the commercial and administration "
                 "factor cannot be calculated. It is UNAVAILABLE and is not treated as Green."
               if missing else
               "the stated commitment population for this firm is zero, so no on-time "
               "percentage is formed and none is assumed.")
    return _factor(
        factor="commercial_administration",
        measure="firm commitments met on time / firm commitments due x 100",
        numerator=num, denominator=den,
        numerator_field="commitments_met_on_time", denominator_field="commitments_due",
        value=pct, value_name="on_time_percent", band=band,
        boundary=("95 per cent or more Green; 90 to under 95 Yellow; 80 to under 90 Amber; "
                  "under 80 Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. A COMMITMENT is "
                  "a required submittal, an RFI response, a procurement release or delivery, a "
                  "corrective-action closure, or a required change-document response."),
        override_hits=hits,
        override_words=("Red if an unfulfilled administrative or procurement commitment directly "
                        "blocks a controlling-path activity."),
        unavailable_reason=why,
        evidence_references=[str(r.get("record_reference")) for r in rows],
        extra={"commitment_records_considered": len(rows),
               "unfulfilled_commitments": len(unfulfilled)})


# =================================================================================================
# THE FIRM POSTURE
# =================================================================================================


def band_weighted(severity: float) -> str:
    """Band a weighted severity on the owner's cuts. Worst-first, inclusive on the lower side."""
    for cut, band in WEIGHTED_CUTS:
        if severity >= cut:
            return band
    return "Green"


def worse_of(a: str | None, b: str | None) -> str | None:
    """The more adverse of two bands. `None` is ABSENT, not favourable."""
    vals = [x for x in (a, b) if x in BAND_SEVERITY]
    return max(vals, key=lambda x: BAND_SEVERITY[x]) if vals else None


def firm_posture(*, firm: str, records: Iterable[Mapping[str, Any]],
                 denominators: Mapping[str, Any] | None,
                 source_posture: str | None = None,
                 source_rating: Any = None,
                 reporting_period: Any = None) -> dict[str, Any]:
    """
    One firm's posture: four factors, the eligibility rule, the weighted severity, the overrides
    applied AFTER it, and the audit record section 5 enumerates.

    `source_posture` is the band the project-supplied SOURCE RATING normalised to -- Run 115's
    ladder, unchanged, computed by the caller and never recomputed here. It is used in exactly
    two ways and no third: as the FALLBACK where the four-factor calculation is ineligible, and
    as the STARTING BAND a lift is measured against where it is eligible. IT IS NEVER BLENDED
    INTO THE ARITHMETIC.
    """
    d = dict(denominators) if isinstance(denominators, Mapping) else {}
    recs = [r for r in records if isinstance(r, Mapping)]
    factors = [
        factor_schedule_reliability(recs, d),
        factor_quality_execution(recs, d),
        factor_safety(recs, d),
        factor_commercial_administration(recs, d),
    ]
    by_name = {f["factor"]: f for f in factors}
    unavailable = [f["factor"] for f in factors if not f["available"]]
    eligible = not unavailable

    overrides = [f["factor"] for f in factors if f["override_fired"]]
    override_band = "Red" if overrides else None

    weighted = None
    weighted_band = None
    arithmetic = None
    if eligible:
        weighted = sum(WEIGHTS[f["factor"]] * BAND_SEVERITY[f["band"]] for f in factors)
        weighted_band = band_weighted(weighted)
        arithmetic = ("; ".join(
            f"{f['factor']} {f['band']} severity {BAND_SEVERITY[f['band']]} x "
            f"{WEIGHTS[f['factor']]:.2f}" for f in factors)
            + f" -- weighted severity {round(weighted, 4)}, which bands {weighted_band}.")

    # ------------------------------------------------------------------- THE ELIGIBILITY RULE
    if eligible:
        basis = "four_factor_calculation"
        # OVERRIDES APPLY AFTER THE WEIGHTED CALCULATION and the final posture is the WORSE of
        # the two. An override can only make a posture worse or leave it unchanged.
        posture = worse_of(weighted_band, override_band)
    elif source_posture in BAND_SEVERITY:
        basis = "source_rating_fallback"
        # THE FALLBACK IS THE SOURCE RATING, UNCHANGED. No factor, no override and no partial
        # calculation touches it: section 4 says the two are NEVER blended, and an override
        # applied on top of a fallback would be exactly the blend it forbids. The overrides that
        # fired are still REPORTED on the record, so nothing is hidden -- they simply move
        # nothing, because the calculation they belong to was discarded.
        posture = source_posture
    else:
        basis = "not_assessed"
        posture = None

    return {
        "firm": firm,
        "reporting_period": reporting_period,
        "active_work": _truthy(d.get("active_work")),
        "active_work_stated": _truthy(d.get("active_work")) is not None,
        "factors": factors,
        "by_name": by_name,
        "factor_bands": {f["factor"]: f["band"] for f in factors},
        "factor_values": {f["factor"]: f["value"] for f in factors},
        "factors_available": [f["factor"] for f in factors if f["available"]],
        "factors_unavailable": unavailable,
        "eligible_for_four_factor": eligible,
        "eligibility_words": ELIGIBILITY_WORDS,
        "weighted_severity": None if weighted is None else round(weighted, 4),
        "weighted_posture": weighted_band,
        "weighted_arithmetic": arithmetic,
        "weights": dict(WEIGHTS),
        "overrides_fired": overrides,
        "override_detail": {f["factor"]: f["override_hits"] for f in factors
                            if f["override_fired"]},
        "override_posture": override_band,
        "override_words": OVERRIDE_WORDS,
        "posture_basis": basis,
        "final_posture": posture,
        "source_rating": source_rating,
        "source_rating_posture": source_posture,
        "denominators": d,
        "records_considered": len(recs),
        "open_records": sum(1 for r in recs if is_open(r)),
        "band_basis_id": OWNER_BASIS_ID,
        "boundary_words": WEIGHTED_BOUNDARY_WORDS,
        "scope_words": SCOPE_WORDS,
        "rule_version": RULE_VERSION,
    }


def governing(postures: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    THE WORST FINAL POSTURE AMONG FIRMS WITH ACTIVE WORK. See `ACTIVE_WORK_WORDS`: a firm the
    documents STATE has no active work is out of the comparison; a firm that states nothing is
    in it.
    """
    active = [p for p in postures if p.get("active_work") is not False
              and p.get("final_posture") in BAND_SEVERITY]
    if not active:
        return None
    return max(active, key=lambda p: (BAND_SEVERITY[p["final_posture"]], str(p["firm"])))


def across_firms(postures: list[dict[str, Any]]) -> dict[str, Any]:
    """The comparison, and who was in it. Returned rather than recomputed by any surface."""
    gov = governing(postures)
    return {
        "contractor_firm_postures": postures,
        "contractor_governing_firm": (gov or {}).get("firm"),
        "contractor_governing_posture": (gov or {}).get("final_posture"),
        "contractor_governing_basis": (gov or {}).get("posture_basis"),
        "contractor_firms_excluded_no_active_work": sorted(
            str(p["firm"]) for p in postures if p.get("active_work") is False),
        "contractor_firms_active_work_not_stated": sorted(
            str(p["firm"]) for p in postures if not p.get("active_work_stated")),
        "contractor_firms_not_assessed": sorted(
            str(p["firm"]) for p in postures if p.get("final_posture") is None),
        "contractor_active_work_rule": ACTIVE_WORK_WORDS,
        "contractor_factor_rule_version": RULE_VERSION,
        "contractor_scope_words": SCOPE_WORDS,
    }
