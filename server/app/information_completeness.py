"""
HOW MUCH OF WHAT THIS ASSESSMENT NEEDS THE PLATFORM ACTUALLY HOLDS.

THE OWNER'S RUN 115 RULING. "The measure is data extracted / data required. If every document
is provided and everything extracts, it is complete." It never feeds the project status, it
abstains from its category and casts no vote -- that is how C1.5 is already routed and it stays.
What it does instead is put a CAVEAT at the bottom of the recommendation: this assessment is
based on XX per cent of the information required.

IT IS A STATEMENT OF RELIABILITY AND NOT A FINDING. A project at 60 per cent is not a project in
trouble; it is a project this platform knows less about. Nothing here carries a band, a colour,
a severity or an action, and nothing here can change `project_status`.

-------------------------------------------------------------------------------------------
WHAT "DATA REQUIRED" IS COUNTED AS, AND WHY. The order named two candidate denominators and
required the caveat to say which it counted.

  CANDIDATE A -- every field every supported document type asks for. Measurable directly from
  `extraction_fields._EXTRACTION_FIELDS`. REJECTED. Run 112 measured that the extractor asks for
  254 (document type, field) pairs across 27 types, that only 32 of the 158 pairs it measured
  move a module's band, and that 64 were inert end to end. A caveat reading "based on 40 per
  cent of the information required" while the missing 60 per cent reaches nothing at all would
  be actively misleading -- it would report a project as poorly evidenced for failing to supply
  figures this platform does nothing with.

  CANDIDATE B -- the fields the modules in service actually need. CHOSEN, and made measurable
  rather than hand-listed: a (document type, field) pair is REQUIRED where this platform has a
  path from it to a module. There are exactly two such paths and both are declared in code:

    1. the field is EMITTED AS A SIGNAL INPUT -- it appears in `extraction_merge`'s numeric or
       date emission tables for that document type, or is that type's as-of date;
    2. the field is READ BY A STRUCTURE ASSEMBLER in `documents.py`, which turns it into a
       canonical structure a module reads.

  A field on neither path is inert: extracting it changes no reading, so not having it costs
  the assessment nothing and it is not counted against the project. `_ASSEMBLER_FIELDS` below
  is the declaration for path 2; `drive_run115.py` section 0 pins every name in it to the
  extraction contract AND to the text of `documents.py`, so a field renamed in either place
  turns that check red instead of quietly shrinking the denominator.

THE NUMERATOR is the required pairs for which this period's live documents hold a value that is
neither None nor blank. A document type not provided contributes nothing to the numerator and
its full share to the denominator, which is what makes "if every document is provided and
everything extracts, it is complete" true.

NO THRESHOLD IS APPLIED ANYWHERE IN THIS FILE. There is no rung, no colour and no cut-off: the
percentage is reported and nothing is decided from it.
"""
from __future__ import annotations

from typing import Any

from .extraction_fields import DOC_TYPES, extraction_fields_for
from .extraction_merge import _AS_OF_KEYS, _DATESTR_EMISSIONS, _NUMERIC_EMISSIONS

# --------------------------------------------------------------------------- path 2, declared
#
# The extraction fields `documents.py` reads into a canonical structure, by document type. One
# entry per field the assembler actually reads; a field the assembler ignores is NOT here, and a
# field here that the assembler stops reading turns the Run 115 check red.
_ASSEMBLER_FIELDS: dict[str, tuple[str, ...]] = {
    "change_order": ("modifications_json", "change_events_json", "change_exposure_days",
                     "baseline_contract_sum", "change_related_delay_days",
                     "change_available_total_float_days", "original_contract_duration_days",
                     "change_time_extension_approved", "change_forecast_completion_moved",
                     "trade_attribution_json", "trade_denominators_json"),
    "oac_minutes": ("weather_events_json", "weather_allowance_days_remaining",
                    "weather_calendar_id", "weather_day_basis", "weather_allowance_days",
                    "weather_days_claimed", "weather_days_approved", "weather_approval_period",
                    "weather_approval_source", "weather_time_extension_granted",
                    "weather_time_extension_days",
                    "weather_time_extension_incorporated_in_baseline",
                    "weather_milestone_forecast_late", "weather_milestone_class",
                    "disputes_json", "disputes_recorded"),
    "procurement_log": ("procurement_items_json", "procurement_day_basis",
                        "trade_attribution_json", "trade_denominators_json"),
    "submittal_register": ("submittal_decisions_json", "submittal_disposition_legend_json",
                           "submittal_reporting_period",
                           "rejected_critical_or_long_lead_late_json",
                           "rejected_blocking_past_deadline_json",
                           "critical_package_rejected_resubmittals",
                           "trade_attribution_json", "trade_denominators_json"),
    "ncr_log": ("inspections_performed", "active_work_packages", "ncr_denominator_basis",
                "ncr_issued", "ncr_open", "ncr_closed", "report_period",
                "open_critical_ncr_json", "hold_point_or_turnover_blocking_ncr_json",
                "ncr_open_past_contractual_closure_json",
                "max_repeat_ncrs_one_root_cause_or_trade",
                "trade_attribution_json", "trade_denominators_json"),
    "subcontractor_report": ("subcontractor_ratings_json", "subcontractor_rating_scale",
                             "subcontractor_report_date", "subcontractor_report_version"),
    # RUN 120, SECTION 6. Four more types now carry the trade attribution and denominator
    # tables, because A6.4's four factors read firm-attributed delivery records off them.
    # Declared here so the completeness denominator counts the path: a project whose
    # schedule update states no firm packages is genuinely less complete for A6.4.
    "schedule_update": ("schedule_network_json", "trade_attribution_json",
                        "trade_denominators_json"),
    "contract_value": ("federal_acquisition", "agency_procedure_requires_evms",
                       "major_acquisition", "contracting_agency", "acquisition_designation",
                       "evms_clause_id", "award_date", "acquisition_id"),
    # RUN 117. THE THREE NEW SUPPLY PATHS, DECLARED so the denominator counts them.
    # `correspondence_notice` reaches A6.2's and A6.3's hard overrides; `field_report` reaches
    # A4.5 through the OAC minutes' own event reader; `trade_attribution_json` reaches A4.8 on
    # eight document types. Leaving any of them undeclared would let the completeness caveat
    # report a project as more complete than the evidence it actually rests on.
    #
    # `notice_enforcement_domain` IS DECLARED EVEN THOUGH A NOTICE MAY HONESTLY STATE NO REGIME.
    # It has a path -- it is what routes the notice -- and the denominator counts paths, not
    # obligations. A project whose notice states no domain is genuinely less complete for the
    # purpose of the two overrides, and the caveat says so rather than hiding it.
    "correspondence_notice": ("notice_enforcement_domain", "notice_enforcement_severity",
                              "notice_enforcement_authority", "notice_enforcement_reference"),
    # RUN 119, SECTION 2. The three fields the pooled NCR rate reads off a field report: what it
    # observed, and the exposure it observed it over. Declared because the assembler really does
    # read them; leaving them out would let the caveat report a project as more complete than
    # the evidence its rate actually rests on.
    "field_report": ("weather_events_json", "weather_allowance_days_remaining",
                     "weather_calendar_id", "weather_day_basis", "trade_attribution_json",
                     "trade_denominators_json",
                     "quality_deficiencies_noted", "inspections_performed",
                     "active_work_packages"),
    # RUN 120. The RFI log had no declared assembler path at all before this run; it has one
    # now, because A6.4's commercial and administration factor reads RFI responses as
    # commitments off exactly these two tables.
    "rfi_log": ("trade_attribution_json", "trade_denominators_json"),
    "inspection_report": ("trade_attribution_json", "trade_denominators_json"),
    "safety_report": ("trade_attribution_json", "trade_denominators_json"),
    # RUN 119, SECTION 2. The same three off a quality audit report.
    "quality_audit_report": ("trade_attribution_json", "trade_denominators_json",
                             "total_findings", "inspections_performed",
                             "active_work_packages"),
    "environmental_report": ("trade_attribution_json", "trade_denominators_json"),
    # RUN 119, SECTION 5. The two closeout figures the commissioning completion path reads.
    # Declared here so the denominator counts the path: a project whose commissioning report
    # states neither is genuinely less complete for the purpose of that path.
    "commissioning_report": ("trade_attribution_json", "trade_denominators_json",
                             "commissioning_items_total", "commissioning_items_cleared"),
}


def _required_pairs() -> dict[str, frozenset[str]]:
    """(document type -> the fields this platform has a path from, to a module)."""
    out: dict[str, set[str]] = {}
    for doc_type in DOC_TYPES:
        declared = set(extraction_fields_for(doc_type))
        reaching: set[str] = set()
        for src, _si in _NUMERIC_EMISSIONS.get(doc_type, ()):
            reaching.add(src)
        for src, _si in _DATESTR_EMISSIONS.get(doc_type, ()):
            reaching.add(src)
        as_of = _AS_OF_KEYS.get(doc_type)
        if as_of:
            reaching.add(as_of)
        reaching.update(_ASSEMBLER_FIELDS.get(doc_type, ()))
        # A declared path to a field the type does not ask for is not counted: the denominator
        # is what a document of this type could actually state.
        kept = reaching & declared
        if kept:
            out[doc_type] = kept
    return {k: frozenset(v) for k, v in sorted(out.items())}


#: Computed once at import. It is a property of the code, not of any project.
REQUIRED_PAIRS: dict[str, frozenset[str]] = _required_pairs()

#: The denominator, in one number.
REQUIRED_TOTAL: int = sum(len(v) for v in REQUIRED_PAIRS.values())

#: The words the caveat uses to say WHICH denominator it counted. Printed, not summarised.
DENOMINATOR_WORDS: str = (
    "the information required is every figure this platform has a path from, to one of the "
    "measures it runs: the fields that become signal inputs, and the fields a document reader "
    "turns into a structure a measure reads. Fields the extractor asks for and nothing "
    "consumes are not counted, because not having them changes no reading."
)


def _stated(value: Any) -> bool:
    """A field is held where the document stated something other than nothing."""
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def information_completeness(documents: list[dict] | None) -> dict[str, Any]:
    """
    The proportion of the required information this period's live documents hold.

    Pure. Reads the documents this response already carries, writes nothing, decides nothing.
    """
    held: dict[str, set[str]] = {}
    for doc in documents or []:
        doc_type = str((doc or {}).get("doc_type") or "")
        wanted = REQUIRED_PAIRS.get(doc_type)
        if not wanted:
            continue
        ex = (doc or {}).get("extraction")
        if not isinstance(ex, dict):
            continue
        got = held.setdefault(doc_type, set())
        for field in wanted:
            if _stated(ex.get(field)):
                got.add(field)
    extracted = sum(len(v) for v in held.values())
    total = REQUIRED_TOTAL
    ratio = (extracted / total) if total else None
    percent = None if ratio is None else int(round(ratio * 100))
    missing_types = sorted(t for t in REQUIRED_PAIRS if t not in held)
    return {
        "extracted": extracted,
        "required": total,
        "percent": percent,
        "document_types_counted": len(REQUIRED_PAIRS),
        "document_types_absent": missing_types,
        "denominator_basis": DENOMINATOR_WORDS,
        # THE SENTENCE THE CARD PRINTS, composed here so the browser cannot compose a different
        # one. It states reliability and never a condition: no colour word, no severity, no
        # action, and no claim that a lower figure is an adverse finding.
        "caveat": (
            None if percent is None else
            f"This assessment is based on {percent} per cent of the information required. "
            f"That is {extracted} of {total} figures this platform can use, read from the "
            f"documents provided for this period. A lower figure is not an adverse finding "
            f"about the project: it is the extent of what this platform holds."),
    }
