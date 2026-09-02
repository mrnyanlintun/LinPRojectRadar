"""
Document-type vocabulary and per-type extraction field lists, ported from Apps Script.

WHY THIS FILE EXISTS AT ALL. The legacy extraction pipeline lives in
`apps_script/reference/Code_v10.36_editor_head.gs`, where the document-type list, the per-type
field list, the filename heuristic and the classifier prompt are four separate literals scattered
across ~400 lines of a single .gs file. They drifted: field names appear in `extractionFieldsFor_`
that are absent from the 86-key `allFields` superset, and the frontend dropdown offers doc types
that no extraction mapping has ever heard of. Porting them into one pure-data module makes the
drift visible and testable instead of latent. Nothing here does I/O, calls a model, or imports
another app module — that is deliberate, so this can be imported from a request handler, a test,
or a migration script without dragging in settings, a database session, or a network client.

FIDELITY OVER TIDINESS. Every field list below is a verbatim transcription of the legacy switch,
in legacy order, including names the legacy never populated. Reordering or "correcting" a field
name here silently changes what the extractor is asked for, and therefore changes the numbers a
PM sees, with no test able to catch it — the prompt is the contract. If a name looks wrong, it
should be fixed as an explicit, reviewed behaviour change, not as a cleanup.

THE ONE DELIBERATE DIVERGENCE is `guess_type_from_filename`, which returns None where the legacy
returned 'monthly_report'. See the comment at that function; it was a real defect, not a style
preference.

UNMAPPED is the vocabulary this module contributes for the "we do not know what this is" case,
which the legacy had no way to express.
"""

from __future__ import annotations

# The sentinel a caller records when classification produced nothing usable. The legacy had no
# such state — every document became *some* type — so this string is new, not a port.
UNMAPPED: str = "unmapped"

# `validTypes`, verbatim and in legacy order (Code_v10.36 lines 691-695 and 758-762 — the literal
# is duplicated in identifyOnly_ and extractAuto_; both copies are identical, checked).
# REGISTERS AND LOGS ONLY (storage redesign, 2026-08-02). The individual `rfi` form is gone
# from this list: individual submittals, RFIs and RFAs do not arrive on this platform — the PM
# sees the register — and a single RFI classified as a log would be asked for totals it cannot
# supply. It routes to UNMAPPED instead, the same decision already made for the individual
# submittal form. Its accumulating merge branch (the `add()` on rfiCount) died with it, and so
# did the undocumented dependency on `"rfi" < "rfi_log"` sorting.
DOC_TYPES: tuple[str, ...] = (
    "pay_application",
    "monthly_report",
    "oac_minutes",
    "schedule_update",
    "change_order",
    "field_report",
    "inspection_report",
    "ncr_log",
    "subcontractor_report",
    "procurement_log",
    "lookahead_schedule",
    "resource_report",
    "cost_report",
    "past_performance_report",
    "safety_report",
    "quality_audit_report",
    "environmental_report",
    "historical_data",
    "time_phased_schedule",
    "contract_value",
    "schedule_of_values",
    "submittal_register",
    "correspondence_notice",
    "risk_register",
    "commissioning_report",
    "rfi_log",
    "rfa_log",
)

# `allFields` from extractAuto_ (line 763), verbatim. The legacy used this as a single 86-key
# kitchen-sink prompt for "auto" mode: ask for everything, keep whatever comes back. That is the
# opposite of the per-type approach and produced a lot of hallucinated nulls-turned-numbers, so it
# is kept here for reference and for tests that check per-type lists against the historical
# vocabulary — NOT for building prompts.
ALL_FIELDS: tuple[str, ...] = (
    "activities_constrained", "activities_planned", "actual_cost", "actual_labor_hours",
    "actual_percent_complete", "amount_paid_to_date", "analogous_overrun_pct", "application_date",
    "at_risk", "audit_date", "audit_score", "baseline_contract_sum", "budget_at_completion",
    "change_order_count", "completed_to_date", "completion_year", "compliance_rate",
    "compliance_score", "consumed_float", "cost_rating", "critical_deficiency_count",
    "critical_findings", "data_date", "deficiency_count", "delayed", "document_date",
    "document_risk_score", "earned_value", "environmental_issues_discussed", "float_remaining",
    "incident_rate", "indirect_cost_actual", "indirect_cost_plan", "items_failed",
    "items_inspected",
    # RUN 102, SECTION 4.1. The two figures the owner's first-pass acceptance measure is defined
    # on, and the critical-item table its hard override reads. `items_passed` was ALREADY here
    # and is NOT what this measure needs: it does not say whether an item passed on FIRST
    # inspection or on a re-inspection after rework, and those are different quantities. So a
    # field is added that says so on its face rather than reinterpreting one that does not.
    "items_passing_first_inspection", "critical_quality_failures_json",
    # RUN 107, SECTION 2. TWO DOCUMENTS GAIN FIELDS, AND NEITHER IS A NEW DOCUMENT TYPE:
    # `oac_minutes` and `subcontractor_report` both already exist.
    #
    # A4.5 WEATHER-DAY IMPACT. The owner's ruling: "A weather day is claimed by the contractor
    # and approved by the owner, and that approval is recorded in OAC meeting minutes. The
    # module reads the approved figure, not a weather log alone." The minutes already carried
    # `weather_days_discussed`, which is a COUNT OF A CONVERSATION and is not an approval; it is
    # left exactly as it is and is not reinterpreted, for the same reason `items_passed` was not
    # reinterpreted as first-pass acceptance. What the band needs is stated on its face: the
    # days CLAIMED, the days APPROVED, the PERIOD the approval covers, the ALLOWANCE the
    # contract calendar grants, and whether a time extension was granted and for how long.
    "weather_days_claimed", "weather_days_approved", "weather_approval_period",
    "weather_allowance_days", "weather_time_extension_granted", "weather_time_extension_days",
    #
    # A4.8 SUBCONTRACTOR PERFORMANCE, MVP. The module reads ONE document and normalises the
    # rating already in it. The report already carried `compliance_score`, a single opaque
    # project-wide number with no firm, no period and no scale behind it; it is left as it is
    # and is NOT read as a per-firm rating. A rating is per FIRM, so it is asked for as a TABLE
    # -- the same decision `submittal_decisions_json` records -- carrying, per row, the firm,
    # the assessment period, the rating label or numeric score, and the scale it is on. The
    # scale, the report date and the report version are asked for once for the whole report.
    "subcontractor_ratings_json", "subcontractor_rating_scale", "subcontractor_report_date",
    "subcontractor_report_version",
    # RUN 106, SECTION 3. THE TWO OWNER-SUPPLIED BANDS NEED FIELDS THE CONTRACT DID NOT ASK FOR.
    #
    # A4.3 First-review submittal rejection is defined on submittals RECEIVING A FIRST REVIEW,
    # excluding later resubmittal outcomes. `submittals_total` and `submittals_rejected` are
    # bare totals with no revision structure, so the first-review population cannot be recovered
    # from them at all -- the module therefore does not band on that path. What the measure needs
    # is the DECISION TABLE the register prints: one row per decision, carrying the submittal, the
    # revision and the decision date, so the earliest decision for each submittal is identifiable.
    "submittal_decisions_json", "submittal_disposition_legend_json",
    "submittal_reporting_period",
    # RUN 115, GOAL 3. THE DISPUTES THE OAC MEETING MINUTES RECORD, AND WHY THEY ARE NOT
    # `subcontractor_disputes`.
    #
    # `subcontractor_disputes` was already here and is NOT inert: `field_registry` declares
    # `subcontractorDisputes` a SNAPSHOT, `extraction_merge` emits it, and `document_evidence`
    # prints it with the bearing "open disputes". It is SUBCONTRACTOR-SCOPED. The owner's Run
    # 115 measure is a count of the disputes the minutes record, with no qualification, and a
    # project whose only dispute is with the designer or the owner would count zero on the
    # subcontractor field. Reusing it would quietly change what a stored figure means, so a
    # SECOND field is asked for beside it and neither is substituted for the other.
    #
    # Two forms, because minutes print disputes either way, and the register wins where both
    # are present: a list of the disputes the minutes actually record is the thing recorded,
    # and a stated total is the minutes' own count of it.
    "disputes_json", "disputes_recorded",
    # A4.3's three Red overrides, each a printed table rather than a judgement.
    "rejected_critical_or_long_lead_late_json", "rejected_blocking_past_deadline_json",
    "critical_package_rejected_resubmittals",
    # A4.4 NCR rate is a percentage of INSPECTIONS PERFORMED in the period, or of ACTIVE WORK
    # PACKAGES where inspections cannot be reliably identified. `items_inspected` on an
    # inspection report is the count of ITEMS inspected, which is a different denominator, so
    # the NCR log is asked for its own.
    "inspections_performed", "active_work_packages", "ncr_denominator_basis",
    # A4.4's four Red overrides.
    "open_critical_ncr_json", "hold_point_or_turnover_blocking_ncr_json",
    "max_repeat_ncrs_one_root_cause_or_trade", "ncr_open_past_contractual_closure_json",
    "long_lead_items_total", "lookahead_weeks", "material_cost_baseline",
    "material_cost_current", "ncr_closed", "ncr_issued", "ncr_open", "on_time_deliveries",
    "original_contingency", "original_contract_sum", "osha_recordable_incidents",
    "outstanding_action_items", "overall_rating", "percent_complete_verified", "period_to_date",
    "planned_labor_hours", "planned_percent_complete", "planned_value", "planned_value_to_date",
    "project_end_date", "project_start_date", "quality_deficiencies_noted",
    "quality_issues_discussed", "quality_rating", "remaining_contingency", "report_date",
    "report_period", "response_time_days", "revised_completion_date", "revised_contract_sum",
    "rfi_count", "rfi_number", "rfi_period_days", "safety_actions_open",
    "safety_incidents_discussed", "schedule_rating", "scheduled_deliveries",
    "scheduled_value_total", "similar_project_bac", "similar_project_final_cost",
    "subcontractor_disputes", "subcontractor_issues_discussed", "submittals_rejected",
    "submittals_total", "total_findings", "total_float", "total_manhours", "violations",
    "weather_days_discussed", "weather_days_lost", "work_period_from", "work_period_to",
)

# The content-sniffing hints from the identifyOnly_ classifier prompt (line 709-711), verbatim
# apart from the two additions noted below. Ten of the 27 types now get a hint; the rest rely on
# the model's priors. Kept as one string rather than a dict because it is a prompt fragment, and
# splitting it would invite someone to reassemble it in a different order and change classifier
# behaviour by accident.
#
# ADDITION 1 (2026-08-09): the RFI log clause now names the design-engagement titling this
# corpus actually uses. One project names the document a "Design Query and Owner Decision Log";
# the others name it "RFI Log" or "RFI and Design Query Log" — same request/response/decision
# content, different title. Without the added wording the model has only the bare "RFI log"
# framing to go on and nothing tying "design query" or "owner decision" vocabulary to rfi_log.
#
# ADDITION 2 (2026-08-09): a schedule_of_values clause naming its structure — a line-item
# breakdown of the contract sum with a scheduled value and percent/amount complete per line, no
# application number, no amount paid — set directly against pay_application's own hint, which was
# previously the classifier's ONLY signal for either document and describes pay_application only.
# A schedule of values is a breakdown of the contract sum; a pay application is a request for
# payment against it, so the two clauses are written to name what is present in one and absent in
# the other, not just to describe each document in isolation.
CLASSIFY_HINTS: str = (
    "Match on content: pay application has contract sum, amount paid to date and a billing "
    "period, and is a numbered request for payment; "
    "a schedule of values breaks the contract sum into line items, each with its own scheduled "
    "value and percent or amount complete, and unlike a pay application carries no amount paid "
    "and no billing period; "
    "monthly report has EV/AC/PV; "
    "an RFI log lists requests for information with totals, whatever it is titled — a document "
    "titled a design query log or an owner decision log records the same request, response and "
    "decision content and is the same type; "
    "OAC minutes has meeting attendees; "
    "change order has revised contract sum; "
    "NCR log has non-conformance; cost report has indirect/material cost; "
    "safety report has OSHA incidents."
)

# RUN 114, GOAL 2. THESE FIFTEEN ARE NO LONGER OFFERED TO ANYONE. The tuple is KEPT, and keeps
# its name, because it is the pin: `tools/test_document_rows.py` reads it to prove the upload
# dropdown in assets/js/signals.js offers no type the server will never classify into, and that
# check is now the stronger one -- the dropdown must be exactly DOC_TYPES, and not one of these
# fifteen may appear in it.
#
# WHAT THEY WERE. The "Planning and Governance Documents" optgroup from assets/js/signals.js
# DOC_TYPE_GROUPS. These 15 types were offered to the PM in the upload dropdown, but they appear
# in NO extraction mapping, NO validTypes, and NO filename heuristic — a PM could select "BIM
# Execution Plan", upload it, get a success response, and have contributed exactly nothing to
# signalInputs. Silence there reads as "ingested and understood".
#
# THE OWNER'S RULING, RUN 114: they come out of the picker. He does not want drawings read; his
# words are that even a quantitative document goes haywire, so not the drawings. A user must
# never be able to select a type that produces nothing.
#
# A STORED DOCUMENT ALREADY CARRYING ONE OF THESE TYPES IS UNAFFECTED AND STILL RENDERS. Nothing
# in this file, in `documents.py` or in the API looks a doc_type up in a table that can refuse
# it: `is_mapped()` returns False (as it always did for these), `extraction_fields_for()` falls
# back to `_DEFAULT_FIELDS`, and every listing endpoint emits the stored string as it stands. The
# only lookup that could have printed a raw snake_case key at a reader is the frontend label map,
# and signals.js keeps all fifteen labels in `RETIRED_DOC_TYPE_LABEL`, merged into
# DOC_TYPE_LABEL and into neither DOC_TYPE_GROUPS nor DOC_TYPES.
UI_ONLY_DOC_TYPES: tuple[str, ...] = (
    "airport_layout_plan",
    "airport_master_plan",
    "project_delivery_charter",
    "owners_project_requirements",
    "grant_assurances",
    "bim_execution_plan",
    "front_end_project_manual",
    "technical_specifications",
    "schematic_design",
    "design_development",
    "construction_documents",
    "basis_of_design",
    "construction_safety_phasing",
    "project_execution_plan",
    "as_built_drawings",
)

# Verbatim port of extractionFieldsFor_ (lines 1102-1134). A dict rather than a chain of ifs
# because the legacy switch has no ordering semantics — unlike the filename heuristic below, which
# does. Several names here are NOT in ALL_FIELDS (milestones_json, items_passed, change_order_date,
# ncr_overdue, on_schedule, constraint_rate, permit_conditions_total, the rfi_log/rfa_log keys,
# planned_equipment_days, actual_equipment_days, safety_observations, environmental_observations,
# subcontractor_observations, analogous_project_type, submitted_date, response_date, source). That
# is legacy drift, faithfully preserved: the per-type prompt asked for them regardless.
_EXTRACTION_FIELDS: dict[str, list[str]] = {
    # RUN 69. WHAT THE CONTRACT STATES ABOUT ITS OWN REGULATORY REGIME.
    #
    # B3.2 FAR/Agency EVMS Applicability abstained on "governed acquisition, agency and clause
    # applicability evidence". `canonical_v6.evms_applicability` states that NOTHING in it reads
    # BAC, CPI, SPI, EV or AC and that applicability "is a question about the acquisition, the
    # agency, the agency procedure and the contract clause, and it is answered from that evidence
    # or not at all". Each field below is printed on the face of a contract or award document
    # under its own label; none is inferred from a performance figure, and where the document
    # states none of them the structure is not assembled at all.
    "contract_value": [
        "original_contract_sum", "project_start_date", "project_end_date",
        "federal_acquisition", "contracting_agency", "acquisition_designation",
        "major_acquisition", "agency_procedure_requires_evms", "evms_clause_id", "award_date",
        "acquisition_id",
    ],
    "schedule_of_values": ["completed_to_date", "scheduled_value_total", "period_to_date"],
    "pay_application": [
        "amount_paid_to_date", "percent_complete_verified", "original_contract_sum",
        "completed_to_date", "work_period_from", "work_period_to", "application_date",
        "original_contingency", "remaining_contingency",
    ],
    # RUN 68. THE BASELINE DOCUMENT'S OWN TABLE, ASKED FOR AS A TABLE.
    #
    # A time-phased baseline document IS a period-by-period table -- that is the whole document
    # -- and until this run the only thing asked of it was the single cumulative figure standing
    # at its data date (`planned_value_to_date`). Three modules are defined on the CURVE and not
    # on that one point: A1.6 Earned Schedule interpolates the work performed onto it, A2.6
    # S-Curve Deviation compares it against the actual series, and A1.9 Budget Execution Rate
    # reads the planned SPEND off it at the status period. All three abstained, and the census
    # sentence each printed named the curve in the document's own words.
    #
    # `baseline_curve_json` follows `milestones_json` exactly: a table is not a scalar, so it is
    # asked for as one field carrying one object per printed row, keyed by the table's own column
    # headings, with the shape named explicitly in the prompt (`extraction_client`). Nothing is
    # derived by the model -- every figure is a cell the document prints.
    #
    # `baseline_version` and `baseline_approval_source` are the provenance `canonical_v3`
    # REFUSES to default (`_provenance`: "a blank source silently reads as an unsourced number").
    # A baseline document states both on its face. Where it does not, they come back absent, the
    # structure is not assembled, and all three modules go on abstaining -- which is the correct
    # outcome and not a gap to be filled with a placeholder.
    "time_phased_schedule": [
        "planned_value_to_date", "planned_percent_complete", "data_date", "total_float",
        "consumed_float", "baseline_curve_json", "baseline_version",
        "baseline_approval_source",
    ],
    # RUN 103. THE FLATTENED SCHEDULE EXPORT, AND THE TWO SCALARS THE SLIP RATIO NEEDS.
    #
    # A2.12 Critical Path Analysis and A2.1 PERT Network Criticality both read
    # `scheduleNetwork`, and Run 102 measured that NOTHING SUPPLIED IT: the structure had no
    # document path at all, so both modules abstained on a network the project's own schedule
    # update prints. `schedule_network_json` asks for that export as a table on the
    # `lookahead_activities_json` precedent -- one object per printed activity row, keyed by the
    # export's own column headings -- and `schedule_calendar`, `schedule_calendars_json`,
    # `schedule_baseline_finish_day` and `schedule_imposed_finish_day` are the provenance and
    # the two reference dates the analysis is measured against. NONE is derived: the baseline
    # finish is the APPROVED baseline the contract states, and the imposed finish is a required
    # or contractual completion date where the schedule states one. Where the export states no
    # imposed date the float rule is not evaluable and says so; nothing is inferred for it.
    #
    # THE TWO SCALARS. Run 102 recorded that A2.7 Milestone Trend's slip-ratio denominator --
    # remaining planned duration -- is stated by NO DOCUMENT, so the ratio was never formed.
    # `remaining_planned_duration_days` is that figure as the schedule update states it on its
    # face, and `remaining_duration_basis` is the provenance beside it: the date it was measured
    # from and to. Both are printed cells. No denominator is derived from a clock and none is
    # invented, so a document stating neither leaves the module abstaining exactly as it does
    # today.
    "schedule_update": [
        "planned_percent_complete", "planned_value_to_date", "data_date", "total_float",
        "consumed_float", "activities_planned", "activities_constrained", "lookahead_weeks",
        "milestones_json",
        "schedule_network_json", "schedule_calendar", "schedule_calendars_json",
        # RUN 108, GOAL 2. THE CALENDAR DEFINITION, not the calendar's NAME. Run 103 asked for
        # `schedule_calendar` (a string such as "5-day work week") and `schedule_calendars_json`
        # (a list of such names), and Run 108 measured that a name is all the platform held: it
        # states nothing about WHICH days are worked or WHICH days are holidays, so no working
        # day could be counted and three arms across the eight modules could not be formed.
        # `schedule_calendar_json` asks the export for the DEFINITIONS it prints -- one object
        # per calendar, each with its working days of the week and its holiday dates. The two
        # older name fields are kept and still stored, because a project whose export names a
        # calendar but defines none should still show the name it stated.
        "schedule_calendar_json",
        "schedule_baseline_finish_day", "schedule_imposed_finish_day", "schedule_version",
        # RUN 108. The APPROVED baseline finish as a CALENDAR DATE where the export prints one.
        # `schedule_baseline_finish_day` is a working-day NUMBER on the schedule's own axis, and
        # a number on an axis cannot be counted against a calendar. A1.6's remaining planned
        # WORKING duration is the working days from the data date to this date, counted on the
        # project's stated calendar by the one conversion function. Where the export prints no
        # such date the arm is Not Assessed; nothing is converted from the day number.
        "schedule_baseline_finish_date",
        "remaining_planned_duration_days", "remaining_duration_basis",
    ],
    # RUN 69. THE MODIFICATION REGISTER, WHICH IS A TABLE AND NOT A COUNT.
    #
    # B3.5 Contract Modification Governance asks whether an AUTHORIZED official executed each
    # modification, whether the unilateral/bilateral distinction is honoured, and whether the
    # governing written instrument exists. `canonical_v6.modification_governance` states that
    # "signature existence is never authority" and that a change COUNT is a different measure
    # (A4.6 owns it). `change_order_count` is that count and answers none of those questions.
    # A modification register prints one row per modification carrying exactly what is asked.
    "change_order": [
        "revised_contract_sum", "revised_completion_date", "change_order_date",
        "change_order_count", "baseline_contract_sum", "modifications_json",
        # RUN 114, GOAL 1. THE CHANGE EVENT REGISTER, AND THE EXPOSURE IT IS MEASURED OVER.
        #
        # `modifications_json` above is B3.5's GOVERNANCE register -- who executed each
        # modification and under what instrument -- and it is a different table from this one.
        # A4.6 Change Order Frequency is defined on a change EVENT register:
        # `canonical_v4.change_frequency` needs each change's identity, issue date, type, cause,
        # value and DIRECTION (whether it adds to or takes away from the contract, because an
        # omission is never adverse), plus two structure-level figures it refuses to default --
        # the baseline contract value, which `baseline_contract_sum` above already supplies, and
        # the EXPOSURE IN DAYS the register covers, which Run 111 measured as having no declared
        # field anywhere in this contract. `change_exposure_days` is that field. Without it the
        # recipe is all-or-nothing and the structure is not written at all.
        # RUN 115, GOAL 2. The register's rows now also state APPROVAL STATUS. No new field
        # name is needed for it -- it is a COLUMN on `change_events_json`, printed per change --
        # and Run 115 measured the Run 114 assembler reading identity, issue day, type, cause,
        # value and direction and nothing else, so a pending change and an approved one were
        # indistinguishable once stored. A1.11's redefined measure is pending exposure against
        # the approved budget, and it cannot be taken without that column.
        "change_events_json", "change_exposure_days",
        # A4.6's SCHEDULE HALF, which abstains rather than assuming zero float. Each is stated by
        # the register or absent; nothing here is inferred from the cost half.
        "change_related_delay_days", "change_available_total_float_days",
        "original_contract_duration_days", "change_time_extension_approved",
        "change_forecast_completion_moved",
    ],
    "monthly_report": [
        "earned_value", "actual_cost", "planned_value", "actual_percent_complete",
        "planned_percent_complete", "budget_at_completion", "report_date", "milestones_json",
    ],
    "submittal_register": [
        "document_risk_score", "document_date", "submittals_total", "submittals_rejected",
        # RUN 106, SECTION 3. See ALL_FIELDS for why the bare totals cannot answer the owner's
        # first-review measure and a decision table is asked for instead.
        "submittal_decisions_json", "submittal_disposition_legend_json",
        "submittal_reporting_period",
        "rejected_critical_or_long_lead_late_json", "rejected_blocking_past_deadline_json",
        "critical_package_rejected_resubmittals",
    ],
    "oac_minutes": [
        "document_risk_score", "document_date", "subcontractor_issues_discussed",
        "outstanding_action_items", "subcontractor_disputes", "safety_incidents_discussed",
        "safety_actions_open", "environmental_issues_discussed", "quality_issues_discussed",
        "weather_days_discussed",
        # RUN 107, SECTION 2. The owner-approved weather-day facts. See ALL_FIELDS for why
        # `weather_days_discussed` is not reinterpreted as an approval.
        "weather_days_claimed", "weather_days_approved", "weather_approval_period",
        "weather_allowance_days", "weather_time_extension_granted",
        "weather_time_extension_days",
        # RUN 115, GOAL 3. THE DISPUTES THE MINUTES RECORD. See ALL_FIELDS for why these sit
        # BESIDE `subcontractor_disputes` above rather than replacing it.
        "disputes_json", "disputes_recorded",
        # RUN 114, GOAL 1. THE WEATHER EVENT TABLE, ASKED FOR AS A TABLE.
        #
        # Run 112 measured that no document could serve A4.5 Weather Day Impact: the OAC minutes
        # carried the owner-APPROVED day figures Run 107 added, and not one field shaped to carry
        # the EVENTS. `canonical_v4.weather_day_impact` is defined on a per-event record -- each
        # event, the activity and schedule path it stopped, the days actually lost on it, the
        # float remaining on that path, and the evidence that the weather caused it -- and it
        # refuses a bare count of weather days in those words: "WEATHER OCCURRENCE IS NOT
        # SCHEDULE IMPACT". So `weather_events_json` asks for the table on the
        # `lookahead_activities_json` precedent: one object per printed row, keyed by the
        # minutes' own column headings.
        #
        # THE THREE SCALARS BESIDE IT ARE THE ONES THE STRUCTURE REFUSES TO DEFAULT.
        # `weather_allowance_days_remaining` is the allowance the contract calendar still has
        # left, which the arithmetic absorbs lost days into before float; `weather_calendar_id`
        # is the provenance `canonical_v3._provenance` refuses to invent; `weather_day_basis`
        # says whether the days are working or calendar days, which Run 108 made the record
        # state rather than have the platform guess.
        "weather_events_json", "weather_allowance_days_remaining", "weather_calendar_id",
        "weather_day_basis", "weather_approval_source",
        # The three facts A4.5's HARD OVERRIDE needs, each STATED by the minutes or absent. An
        # absent field is NOT EVALUATED; it is never read as the condition failing to hold.
        "weather_time_extension_incorporated_in_baseline", "weather_milestone_forecast_late",
        "weather_milestone_class",
    ],
    # THE LEGACY FALL-THROUGH IS OVER, and the two types have parted for different reasons.
    #
    # `case 'correspondence_notice':` had no body and fell through to `case 'risk_register':`,
    # on the reading that both were narrative documents with no structured project-controls
    # content. That reading was wrong about both of them.
    #
    # A NOTICE IS AN EVENT. Someone served it, on someone, it asserts something, and under the
    # contract form it starts a clock that can extinguish a right. Reducing that to a number
    # between zero and one threw away every part of it a project manager acts on. The fields
    # below are the ones a notice states in prose, which is why they are asked of the model;
    # the DEADLINE is not among them, because a deadline is derived in code from the form the
    # document named (`contract_notices.deadline_for`) and a model-stated deadline would be a
    # number with no rule behind it.
    #
    # A REGISTER IS A TABLE, so it gains no fields at all. Its rows are read from the document
    # by `risk_register`, one decision per table rather than one per row, and asking the model
    # for them is the unbounded-output failure `milestones_json` already demonstrated.
    # RUN 117, SECTION 4.1. THE ENFORCEMENT CONSEQUENCE, WHICH IS WHAT A STOP-WORK ORDER IS.
    #
    # The seven `notice_*` fields above describe a CONTRACTUAL notice -- who served it, on whom,
    # what it claims, and which form's clock it starts. Run 116 measured that they reach a notice
    # ledger and no module. The owner's ruling is that "correspondence notice is where a
    # stop-work order or a fine arrives, for safety and for environmental".
    #
    # A6.2 AND A6.3 BOTH ALREADY CARRY THE OVERRIDE, AND BOTH OVERRIDES WERE UNREACHABLE.
    # Measured at this head, not cited: `models_cat89._severe_safety_events` reads
    # `structure["severe_events"]` and `_environmental_override_findings` reads
    # `structure["environmental_findings"]`, and NOTHING IN THE TREE WROTE EITHER KEY. The
    # override machinery the owner is asking a notice to fire was complete code with no supply
    # path. These four fields are that supply path and nothing else: no band, no threshold and
    # no ladder is added anywhere by this run.
    #
    # THE SEVERITY WORD IS READ, NEVER MAPPED. `_SAFETY_OVERRIDE_WORDS` and `_ENV_OVERRIDE` are
    # closed vocabularies already in the tree; a word that is none of them matches nothing and is
    # carried onto the record unranked, which is the behaviour both functions already have for a
    # severity word they do not recognise. This run does not add a word to either set.
    #
    # THE DOMAIN IS THE DOCUMENT'S OWN. A notice does not become a safety notice because this
    # platform guessed; the document says which regime issued it, and a notice that says neither
    # reaches neither module and is reported as an unrouted enforcement action.
    "correspondence_notice": [
        "document_risk_score", "document_date",
        "notice_served_by", "notice_served_on", "notice_claim", "notice_date_served",
        "notice_contract_form", "notice_kind", "notice_references",
        "notice_enforcement_domain", "notice_enforcement_severity",
        "notice_enforcement_authority", "notice_enforcement_reference",
    ],
    "risk_register": ["document_risk_score", "document_date"],
    # RUN 87. THE INSPECTION ITEM TABLE, ASKED FOR AS A TABLE.
    #
    # A6.1 Quality Compliance Index is "the share of the applicable quality requirements that
    # were assessed and found satisfied", and section 13 of its specification "forbids
    # substituting a summary for a denominator". `items_inspected` / `items_passed` /
    # `items_failed` are exactly such summaries: they give a total, not a population with
    # per-item applicability, assessment and outcome, and no critical exception can be told
    # apart inside them. An inspection report PRINTS the population -- one row per inspection
    # item, with whether it applied, whether it was checked and whether it passed -- so it is
    # asked for on the `lookahead_activities_json` precedent. `quality_register_id` is the
    # report's own identifier, carried onto the structure as `register_id`. Where the document
    # states less than a readable table, no register is assembled and A6.1 goes on abstaining.
    "inspection_report": [
        "document_risk_score", "document_date", "items_inspected", "items_passed", "items_failed",
        # RUN 102, SECTION 4.1. See ALL_FIELDS for why `items_passed` is not reused for this.
        "items_passing_first_inspection", "critical_quality_failures_json",
        "deficiency_count", "critical_deficiency_count",
        "quality_requirements_json", "quality_register_id", "quality_register_period",
        # RUN 117, SECTION 3. See `_TRADE_ATTRIBUTION_NOTE`.
        "trade_attribution_json",
        # RUN 118, SECTION 1.4. See `_TRADE_DENOMINATOR_NOTE`: the factor
        # ladders need a population and this is the table that states it.
        "trade_denominators_json",
    ],
    # RUN 117, MAP ROW 17. THE WEATHER EVENT TABLE, ASKED OF THE DOCUMENT THAT RECORDS THE DAY.
    #
    # The owner's ruling: A4.5 Weather Day Impact "must also read the field report -- weather
    # days recorded on site". Run 116 measured `weather_days_lost` reaching the signal inputs
    # and A4.5 never looking at it, and called it the clearest category-(2) case on the platform.
    #
    # A COUNT IS NOT THE RECORD, AND THIS RUN DOES NOT PRETEND IT IS. `canonical_v4.weather_day_
    # impact` is defined on EVENTS -- for each event the day, the activity, the schedule path,
    # the days lost, the float available on that activity and the causal evidence -- and
    # `weather_days_lost` is one number with none of that behind it. Nothing here converts the
    # count into an event, because an event this platform invented would carry an activity and a
    # path nobody recorded. The count stays exactly where it is, unread by A4.5, and the TABLE is
    # asked for beside it on the `weather_events_json` precedent the OAC minutes already set.
    #
    # THE READER IS THE ONE ALREADY IN THE TREE. `documents._run69_structures` reads the OAC
    # minutes' event table into `weatherImpactEvents` with a named column vocabulary and an
    # all-or-nothing recipe; the field report is read by that same code with the same vocabulary
    # and the same refusals. A field report printing only some of it assembles NOTHING and A4.5
    # goes on abstaining, which is the correct outcome.
    "field_report": [
        "document_risk_score", "document_date", "weather_days_lost", "float_remaining",
        "quality_deficiencies_noted", "safety_observations", "environmental_observations",
        # RUN 119, SECTION 2. THE OWNER'S RULING: A4.4's rate "averages across the NCR log, the
        # quality audit report and the field report -- audit findings and site-observed defects
        # are the same evidence of the same thing". A rate needs a DENOMINATOR, and this
        # document type stated none, so the SAME TWO the owner's ladder is already drawn over
        # are asked of it: inspections performed, or -- only where inspections cannot be
        # reliably identified -- active work packages. The field names are `ncr_log`'s own,
        # reused rather than duplicated under new spellings, so the pooled denominator cannot
        # come to mean two different things.
        "inspections_performed", "active_work_packages",
        "subcontractor_observations",
        "weather_events_json", "weather_allowance_days_remaining", "weather_calendar_id",
        "weather_day_basis",
        "trade_attribution_json",
        # RUN 118, SECTION 1.4. See `_TRADE_DENOMINATOR_NOTE`: the factor
        # ladders need a population and this is the table that states it.
        "trade_denominators_json",
    ],
    # RUN 117, SECTION 4.2 and SECTION 3. The attribution column is added; the CLOSEOUT FACTS
    # are NOT. See the run report: it proposes what a commissioning report must state to close a
    # project and deliberately ships no replacement for the cost test.
    #
    # RUN 119, SECTION 5. THE CLOSEOUT FACTS, NOW -- AND THERE ARE TWO OF THEM, NOT SEVEN.
    # The owner's ruling is that "when every item on the commissioning report is cleared for
    # testing, the project is Complete". The question is "is every item cleared", and exactly
    # two facts answer it: how many items the report covers and how many are cleared for
    # testing. Run 117's other five proposed fields -- status, completion date, certifying
    # party, certificate reference, a blocking flag on the punch list -- are provenance and
    # narrative, not the test, and a field this platform does not need is a field the owner's
    # generating model can get wrong. `document_date` already dates the reading and is not asked
    # for twice. The outstanding count is DERIVED (total minus cleared) rather than asked for,
    # so the two figures can never disagree with a third. See
    # `simulation.compute.COMMISSIONING_CLEARANCE_CONTRACT` for the words the model is given.
    "commissioning_report": [
        "document_risk_score", "document_date",
        "commissioning_items_total", "commissioning_items_cleared",
        # RUN 117, SECTION 3. See `_TRADE_ATTRIBUTION_NOTE`.
        "trade_attribution_json",
        # RUN 118, SECTION 1.4. See `_TRADE_DENOMINATOR_NOTE`: the factor
        # ladders need a population and this is the table that states it.
        "trade_denominators_json",
    ],
    "safety_report": [
        "osha_recordable_incidents", "total_manhours", "incident_rate", "report_period",
        # RUN 117, SECTION 3. See `_TRADE_ATTRIBUTION_NOTE`.
        "trade_attribution_json",
        # RUN 118, SECTION 1.4. See `_TRADE_DENOMINATOR_NOTE`: the factor
        # ladders need a population and this is the table that states it.
        "trade_denominators_json",
    ],
    # RUN 87. THE SAME TABLE OFF THE QUALITY AUDIT REPORT, for the same reason: an audit score
    # and a findings count are the summaries the specification names, and the audit's own
    # findings/requirements schedule is the population it summarises.
    "quality_audit_report": [
        "total_findings", "critical_findings", "deficiency_count", "audit_score", "audit_date",
        # RUN 119, SECTION 2. THE OWNER'S RULING: A4.4's rate "averages across the NCR log, the
        # quality audit report and the field report -- audit findings and site-observed defects
        # are the same evidence of the same thing". A rate needs a DENOMINATOR, and this
        # document type stated none, so the SAME TWO the owner's ladder is already drawn over
        # are asked of it: inspections performed, or -- only where inspections cannot be
        # reliably identified -- active work packages. The field names are `ncr_log`'s own,
        # reused rather than duplicated under new spellings, so the pooled denominator cannot
        # come to mean two different things.
        "inspections_performed", "active_work_packages",
        "quality_requirements_json", "quality_register_id", "quality_register_period",
        # RUN 117, SECTION 3. See `_TRADE_ATTRIBUTION_NOTE`.
        "trade_attribution_json",
        # RUN 118, SECTION 1.4. See `_TRADE_DENOMINATOR_NOTE`: the factor
        # ladders need a population and this is the table that states it.
        "trade_denominators_json",
    ],
    # RUN 87. THE FACTS THAT ESTABLISH ENVIRONMENTAL APPLICABILITY, AND THE OBSERVATION TABLE.
    #
    # A6.3 reached APPLICABILITY_NOT_ESTABLISHED on every corpus project because the assembly
    # "deliberately supplies no jurisdiction, no permitting authority and no permit id, because
    # the corpus carries none". The corpus carries none because NOTHING EVER ASKED. A permit
    # holder's environmental compliance report states the issuing authority, the jurisdiction
    # and the permit number on its face, in words; `environmental_jurisdiction` and
    # `permitting_authority` are the two the canonical function requires before it will assess
    # conformance, and `permit_id`, `permit_version`, `permit_site_id` and `operator_status` are
    # the identity it carries beside them. `environmental_requirements_json` is the
    # permit-condition or observation schedule, and it is what carries closure: a row printing
    # "Closed" is a satisfied condition, a row printing "Open" is an unsatisfied one, and a row
    # printing neither is outstanding and enters no ratio (see `compliance_register`).
    # Authority is READ, never assumed: only the exact word EPA reaches the EPA CGP rule.
    "environmental_report": [
        "permit_conditions_total", "violations", "compliance_rate", "report_date",
        "environmental_jurisdiction", "permitting_authority", "permit_id", "permit_version",
        "permit_site_id", "operator_status", "environmental_requirements_json",
        # RUN 102, SECTION 4.3. THE CORRECTIVE-ACTION REGISTER, ASKED FOR AS A REGISTER.
        # The owner's measure is corrective actions closed BY THEIR REQUIRED DEADLINE over
        # corrective actions requiring closure. `environmental_requirements_json` carries permit
        # CONDITIONS and their closure WORD; it carries no deadline and no closure date, so it
        # cannot answer a timeliness question. A separate table is asked for, and it must state
        # each action, its required deadline, its closure date and its severity.
        "environmental_corrective_actions_json",
        # RUN 117, SECTION 3. See `_TRADE_ATTRIBUTION_NOTE`.
        "trade_attribution_json",
        # RUN 118, SECTION 1.4. See `_TRADE_DENOMINATOR_NOTE`: the factor
        # ladders need a population and this is the table that states it.
        "trade_denominators_json",
    ],
    "ncr_log": [
        "ncr_issued", "ncr_closed", "ncr_open", "ncr_overdue", "report_period",
        # RUN 106, SECTION 3. The denominator the owner's ladder is drawn over, and which of the
        # two it is, stated by the document rather than assumed by this platform.
        "inspections_performed", "active_work_packages", "ncr_denominator_basis",
        "open_critical_ncr_json", "hold_point_or_turnover_blocking_ncr_json",
        "max_repeat_ncrs_one_root_cause_or_trade", "ncr_open_past_contractual_closure_json",
        # RUN 117, SECTION 3. See `_TRADE_ATTRIBUTION_NOTE`.
        "trade_attribution_json",
        # RUN 118, SECTION 1.4. See `_TRADE_DENOMINATOR_NOTE`: the factor
        # ladders need a population and this is the table that states it.
        "trade_denominators_json",
    ],
    "subcontractor_report": [
        "scheduled_deliveries", "on_time_deliveries", "compliance_score", "report_period",
        # RUN 107, SECTION 2. The Subcontractor Performance Report's own per-firm ratings, as a
        # TABLE. `compliance_score` is a single opaque number with no firm, no period and no
        # scale behind it and is NOT read as a rating.
        "subcontractor_ratings_json", "subcontractor_rating_scale", "subcontractor_report_date",
        "subcontractor_report_version",
    ],
    # RUN 114, GOAL 1. THE PROCUREMENT REGISTER, WHICH IS A TABLE AND NOT FIVE COUNTS.
    #
    # Run 112 measured this document type as five scalars and no table, and A4.9 Procurement
    # Lead Time as unservable by any document. The five below are counts of items in three
    # states; `canonical_v4.procurement_slack` is defined on an ITEM-LEVEL register -- for each
    # item the date it is required on site, the date it is forecast to arrive, the float on the
    # activity it feeds and the criticality the register itself states -- and the supplied
    # contract's own words are that "a count ratio alone is not the canonical item-level
    # monitor". The five scalars are LEFT EXACTLY AS THEY WERE and the table is asked for
    # beside them, on the `lookahead_activities_json` precedent.
    #
    # THE REGISTER STATES ITS OWN CRITICALITY. Run 112 established this and it is why no field
    # here reaches toward A2.12 Critical Path Analysis: no path exists in this platform from one
    # module's reading to another module's runner, so an item's criticality is a column the
    # register prints or a fact this platform does not have.
    "procurement_log": [
        "long_lead_items_total", "on_schedule", "at_risk", "delayed", "report_date",
        "procurement_items_json", "procurement_day_basis",
        # RUN 117, SECTION 3. See `_TRADE_ATTRIBUTION_NOTE`.
        "trade_attribution_json",
        # RUN 118, SECTION 1.4. See `_TRADE_DENOMINATOR_NOTE`: the factor
        # ladders need a population and this is the table that states it.
        "trade_denominators_json",
    ],
    # RUN 86. THE LOOK-AHEAD ACTIVITY TABLE, ASKED FOR AS A TABLE.
    #
    # A2.8 Look-Ahead Schedule Health is defined on an INVENTORY: each planned activity with its
    # own identity and its own constraint status, so the counts are derived from the rows rather
    # than asserted as two numbers (`canonical_v3.look_ahead_ready_fraction` refuses a bare
    # count). A look-ahead document PRINTS that inventory -- one row per planned activity, a
    # constraint column saying OPEN or CLEARED, and the constraint kind where open -- so
    # `lookahead_activities_json` asks for it on the `milestones_json` precedent: one object per
    # printed row, keyed by the table's own column headings. `lookahead_horizon` and
    # `lookahead_status_date` are the provenance the canonical function refuses to default: the
    # window the document says it covers, and the date it stood at. Where the document states
    # less than all of it, no structure is assembled and the module goes on abstaining.
    "lookahead_schedule": [
        "activities_planned", "activities_constrained", "constraint_rate", "lookahead_weeks",
        "lookahead_activities_json", "lookahead_horizon", "lookahead_status_date",
    ],
    # RUN 69. THE RESOURCE HISTOGRAM AND THE PRODUCTION BASIS, both off the same document type.
    #
    # A2.9 Resource Loading abstained on "a time phased resource profile: for each period and
    # each kind of resource, the amount of work demanded and the amount available". Four
    # project-total scalars are not that profile, and `canonical_v3.resource_loading` says so in
    # its own words. A resource-loaded report PRINTS the histogram, so `resource_profile_json`
    # asks for it as a table on the `baseline_curve_json` precedent, and `resource_plan_version`
    # is the provenance `_provenance` refuses to default.
    #
    # A3.3 Labor Productivity abstained because hours over hours is not productivity: it needs an
    # output basis. `quantity_installed_to_date`, `quantity_planned_to_date` and `quantity_unit`
    # are the three figures a production or quantities report states on its face beside the hours
    # already extracted, and `quantity_source` is that record's provenance. None is derived; each
    # is a printed cell. Where the document states less than all of them, no record is assembled
    # and the module goes on abstaining.
    "resource_report": [
        "planned_labor_hours", "actual_labor_hours", "planned_equipment_days",
        "actual_equipment_days", "resource_profile_json", "resource_plan_version",
        "quantity_installed_to_date", "quantity_planned_to_date", "quantity_unit",
        "quantity_source",
    ],
    # RUN 69. THE ALLOCATION BASE THE OVERHEAD IS ABSORBED OVER.
    #
    # A3.5 Overhead Absorption has had `indirect_cost_plan` and `indirect_cost_actual` all along
    # and still refused, because `canonical_v3.overhead_absorption` states that "indirect actual
    # over indirect plan with no allocation base is not overhead absorption and is computed
    # nowhere here". The base is not a missing calculation, it is a missing FACT, and a cost
    # report carrying an overhead schedule prints it: the base named, and the planned and actual
    # amount of it.
    # RUN 78. THE CONTINGENCY PAIR, ASKED OF THE DOCUMENT THAT PRINTS IT.
    #
    # `original_contingency` and `remaining_contingency` have been declared in ALL_FIELDS and
    # mapped by the merge since the pair was introduced, but they were REQUESTED FROM
    # `pay_application` ONLY. A cost report states them plainly -- an original contingency, an
    # amount drawn this period, an amount drawn to date, and a remaining balance -- and was
    # never asked, so A3.2 Contingency Burn Rate abstained saying the amounts had not been
    # reported for the period while the document on the page stated them. Nothing about the
    # module changed; the prompt was not asking. The precedence between the two writers is
    # declared in `field_registry.WRITER_TIERS`, because two writers of one field at the same
    # tier is exactly the unresolved material conflict the Category-9 assessment records.
    "cost_report": [
        "indirect_cost_plan", "indirect_cost_actual", "material_cost_baseline",
        "material_cost_current", "report_date", "overhead_allocation_base",
        "planned_allocation_base_quantity", "actual_allocation_base_quantity",
        "overhead_driver_source",
        # RUN 103, SECTION 4. THE FACTS THE OWNER'S ABSORPTION-VARIANCE BAND NEEDS, AND THEY ARE
        # FACTS, NOT ARITHMETIC. The variance is (actual overhead incurred - planned overhead
        # absorbed) / planned overhead absorbed, for THE SAME PERIOD and THE SAME COST-CODE
        # POPULATION. `indirect_cost_plan` and `indirect_cost_actual` are the two amounts and
        # were already asked for; what the platform could never establish is whether they cover
        # the same period and the same cost codes, and the owner's ruling is that where they do
        # not, the answer is Not Assessed rather than a posture. So the two periods are asked
        # for separately -- a cost report prints them on its face -- with the cost-code
        # population each side covers and the documented mapping where they differ, and the
        # PROGRESS BASIS that aligns planned absorption, which is what makes a planned figure a
        # figure for THIS period rather than a whole-project budget.
        #
        # `substantial_completion_declared` and `unabsorbed_overhead_amount` are the two facts
        # the owner's substantial-completion floor turns on. Neither is inferred from a percent
        # complete: substantial completion is a DECLARED contractual state, and a platform that
        # decided it for itself would be deciding a contract question.
        "overhead_actual_period", "overhead_planned_period", "overhead_progress_basis",
        "overhead_cost_code_population", "overhead_cost_code_mapping",
        "substantial_completion_declared", "unabsorbed_overhead_amount",
        "original_contingency", "remaining_contingency",
    ],
    "past_performance_report": [
        "overall_rating", "schedule_rating", "cost_rating", "quality_rating", "source",
    ],
    # RUN 80, FIX THREE. THREE MEASURES ASKED FOR NOTHING AND SO RECEIVED NOTHING.
    #
    # A3.1 Reference Class Forecasting, A3.7 Analogous Estimating and A3.9 Inflation Adjustment
    # each require a governed structure (`canonical_v3`), and the owner's historical-data and
    # past-performance documents STATE what those structures need. Nothing asked for it. The
    # five keys above are the whole of what this document type was ever asked, and none of them
    # is an analogue's NAME, an adaptation FACTOR, a reference CLASS, or an external INDEX -- so
    # every one of the three abstained on a structure the document was carrying on its face.
    #
    # WHAT EACH NEW KEY IS FOR, and which refusal in `canonical_v3` it answers:
    #
    #   A3.7 `analogous_estimate`. `analog_project_id` -> `analogous_project_name`;
    #        `analog_cost` -> the analogue's FINAL cost, already asked for; the adaptation
    #        factors -> `analogous_adjustment_factor`; and `_provenance` refuses without
    #        `source`, `comparability_criteria` and `normalization`, which are
    #        `analogous_source`, `analogous_comparability_basis` and
    #        `analogous_normalization_basis`. Every one is a sentence or a figure a historical
    #        comparison document prints; none is derived and none is defaulted.
    #
    #   A3.9 `external_cost_index`. `_provenance` refuses without index_name, authority,
    #        geography, scope, base_period, observation_period and vintage, and the reading
    #        needs the two index LEVELS. All nine are asked for by name. A document that names
    #        the series and its two levels but not its geography or scope yields NO structure
    #        and the module goes on abstaining -- correctly, because an index applied outside
    #        the geography it was published for is the wrong index.
    #
    #   A3.1 `reference_class_forecast`. A reference class is a TABLE of completed projects, so
    #        it follows `milestones_json` / `baseline_curve_json` / `modifications_json`
    #        exactly: one field carrying one object per printed row, shape named in
    #        `extraction_client.build_prompt`, assembled in `documents.py`. The five provenance
    #        fields it refuses without are asked for beside it.
    "historical_data": [
        "analogous_overrun_pct", "analogous_project_type", "completion_year",
        "similar_project_bac", "similar_project_final_cost",
        # A3.7
        "analogous_project_name", "analogous_adjustment_factor", "analogous_source",
        "analogous_comparability_basis", "analogous_normalization_basis",
        # A3.9
        "cost_index_name", "cost_index_authority", "cost_index_geography", "cost_index_scope",
        "cost_index_base_period", "cost_index_base_value",
        "cost_index_observation_period", "cost_index_current_value", "cost_index_vintage",
        "cost_index_cost_exposure",
        # A3.1
        "reference_class_json", "reference_class_inclusion_criteria",
        "reference_class_exclusion_criteria", "reference_class_outcome_definition",
        "reference_class_normalization", "reference_class_vintage",
        "reference_class_governed_percentile",
    ],
    "rfi_log": [
        "rfi_total", "rfi_open", "rfi_answered", "rfi_overdue", "avg_response_days",
        "rfi_period_days", "oldest_open_days", "log_date",
    ],
    "rfa_log": [
        "rfa_total", "rfa_approved", "rfa_rejected", "rfa_resubmit", "rfa_open",
        "avg_review_days", "log_date",
    ],
}

#: RUN 117, SECTION 3. THE COLUMN THAT NAMES THE FIRM, AND WHY IT HAD TO BE ADDED.
#:
#: THE ESTABLISH-FIRST QUESTION THE ORDER ASKED WAS ANSWERED BY READING THE TREE, AND THE ANSWER
#: WAS NO. At the start of this run the eight trade document types the owner's ruling names --
#: `ncr_log`, `inspection_report`, `safety_report`, `environmental_report`, `quality_audit_report`,
#: `procurement_log`, `field_report`, `commissioning_report` -- declared, between them, NOT ONE
#: field that names a firm. `ncr_log` carried `max_repeat_ncrs_one_root_cause_or_trade`, which is a
#: COUNT and attributes nothing, and `field_report` carried `subcontractor_observations`, which is
#: narrative prose that Run 112 measured as mapped to nothing. The other six carried nothing at all.
#: So a defect on an NCR log told this platform that a defect happened and never whose it was, and
#: A4.8 Subcontractor Performance could not have read a trade record however it was written.
#:
#: THE ROW SHAPE, which is the contract the generating model must print to:
#:
#:   record_reference   the record's own identifier on its own document -- an NCR number, an
#:                      inspection item, a permit condition, a purchase order. REQUIRED. A row
#:                      without it is unusable and is dropped.
#:   subcontractor      the FIRM THE DOCUMENT NAMES as responsible for that record. OPTIONAL, and
#:                      its absence is the whole point of this field: a row stating a record and
#:                      NO firm is an UNATTRIBUTED record. It is carried through, counted, and
#:                      reported as unattributed. It is never distributed across firms, never
#:                      assigned to the worst firm, and never allowed to move any firm's posture.
#:   record_kind        what kind of record it is, in the document's own word -- nonconformance,
#:                      inspection failure, safety incident, permit violation, late delivery,
#:                      audit finding, commissioning defect. OPTIONAL; carried as printed.
#:   record_status      open / closed / accepted / rejected, as printed. OPTIONAL.
#:   record_severity    the severity word the record prints, if it prints one. OPTIONAL. NOTHING
#:                      in this run ranks it, bands it, or maps it to a colour.
#:   record_date        the date the record carries. OPTIONAL.
#:
#: HEADINGS THE PARSER RECOGNISES, per column, matched case-insensitively after trimming (see
#: `documents._first_of`), in this order:
#:   record_reference : record_reference, reference, record, record_id, ref, id, number, no,
#:                      ncr_number, ncr_no, item, item_id, finding, finding_id, po, po_number
#:   subcontractor    : subcontractor, sub, firm, company, trade_contractor, trade, vendor,
#:                      supplier, responsible_firm, responsible_party, contractor, name
#:   record_kind      : record_kind, kind, type, record_type, category, classification
#:   record_status    : record_status, status, state, disposition, outcome, result
#:   record_severity  : record_severity, severity, criticality, class, level
#:   record_date      : record_date, date, raised, raised_on, issued, issued_on, reported
#:
#: WHAT MAKES A ROW UNUSABLE: it is not an object; or it states no `record_reference` under any
#: of the headings above. Such a row is DROPPED, is counted in `rows_unusable` on the assembled
#: record, and is never repaired, defaulted or guessed at.
#:
#: WHAT THIS RUN DOES **NOT** DO WITH THESE ROWS, and the reason is section 3's own instruction.
#: No trade record moves any firm's band. The owner has not stated how an NCR, a failed
#: inspection or a safety incident weighs against a firm's STATED rating, and any weight this run
#: chose would be an invented threshold. The rows are assembled, attributed where the document
#: named a firm, reported as unattributed where it did not, and carried onto A4.8's reading as
#: EVIDENCE beside the band it already asserts. See the run report, section "Subcontractor
#: attribution", for the question the owner must answer before a weight can exist.
#: ============================================================================================
#: RUN 118, SECTION 1.4. FIVE MORE COLUMNS ON THE SAME ROW, AND A SECOND TABLE FOR THE
#: DENOMINATORS. Run 117 asked the document who a record belongs to. The owner's eight factor
#: ladders need to know, for each record, WHICH ARM OF ITS FACTOR IT IS IN, and they need a
#: DENOMINATOR that Run 117 never asked for. Both are grown here.
#:
#: THE FIVE NEW OPTIONAL COLUMNS ON `trade_attribution_json`, each traceable to one owner
#: sentence in section 1.2 and to nothing else. Every one is OPTIONAL, and a row that omits one
#: is NOT counted into the arm that needs it -- never counted in by default, and never dropped:
#: the exclusion is reported on the factor.
#:
#:   record_new_this_period            "NEWLY OPENED ONLY -- an older NCR is not counted again
#:                                     for remaining open." A row not stating it is excluded
#:                                     from the nonconformance numerator and counted in
#:                                     `rows_newness_not_stated`.
#:   record_is_reinspection            "First outcome only -- a reinspection neither expands the
#:                                     denominator nor counts again", and "failing FIRST
#:                                     acceptance test". A row marked as a reinspection or a
#:                                     retest enters neither numerator.
#:   record_confirmed                  "CONFIRMED defect observations ... not every comment --
#:                                     only confirmed defect observations after review." A field
#:                                     observation not marked confirmed is not counted.
#:   record_days_late                  the days-late FLOOR arm of the procurement factor: "1 to
#:                                     5 working days at least Yellow; 6 to 10 at least Amber;
#:                                     more than 10 Red". WORKING DAYS, as the owner states it.
#:   record_milestone_forecast_late    the procurement hard override: "Red if any late delivery
#:                                     causes a contractual, turnover or approved critical-path
#:                                     milestone to forecast late."
#:   record_repeat_after_closed_action the nonconformance hard override's last clause: "a repeat
#:                                     NCR for the same root cause after a corrective action was
#:                                     recorded closed."
#:
#: HEADINGS RECOGNISED for the six, matched the same way as the first six columns:
#:   record_new_this_period            : record_new_this_period, new_this_period, newly_opened,
#:                                       new, opened_this_period, newly_raised
#:   record_is_reinspection            : record_is_reinspection, reinspection, is_reinspection,
#:                                       retest, is_retest, reinspection_flag
#:   record_confirmed                  : record_confirmed, confirmed, verified, confirmed_defect,
#:                                       review_outcome
#:   record_days_late                  : record_days_late, days_late, days_overdue,
#:                                       working_days_late, late_days, delay_days
#:   record_milestone_forecast_late    : record_milestone_forecast_late, milestone_forecast_late,
#:                                       milestone_late, critical_path_impact, milestone_impact
#:   record_repeat_after_closed_action : record_repeat_after_closed_action, repeat_ncr,
#:                                       repeat_after_closure, repeat_root_cause, repeat
#:
#: `record_kind` NOW DECIDES WHICH FACTOR COUNTS THE ROW, so the words matter and are listed
#: here. A row whose kind is none of them is counted by NO factor -- never spread across them
#: and never assigned to the nearest -- and is reported in `rows_of_no_factor`:
#:   nonconformance / non_conformance / ncr / nonconformity     -> Nonconformances
#:   inspection_failure / failed_inspection / inspection_fail   -> Failed inspections
#:   environmental_action / environmental / permit_violation    -> Environmental
#:   audit_finding / finding / quality_audit_finding            -> Quality audit
#:   late_delivery / delivery / procurement / procurement_item  -> Procurement
#:   defect_observation / field_observation / site_observation / observation / defect
#:                                                              -> Field observations
#:   commissioning_defect / commissioning_failure / acceptance_test_failure
#:                                                              -> Commissioning
#: SAFETY IS THE EXCEPTION AND READS NO KIND: its rate is a formula over two numbers on the
#: denominator table, and its override reads every open record's severity word.
#:
#: ============================================================================================
#: `trade_denominators_json` -- THE DENOMINATORS, ONE ROW PER FIRM. This is the field Run 117
#: did not ask for and without which not one of the owner's eight ladders can be evaluated: a
#: rate needs a population, and a population is a number the DOCUMENT counts, never one this
#: platform derives from the rows it happened to be shown. A firm with records and no
#: denominator row gets NO RATE BANDING and its hard overrides only -- which is section 1.3's
#: "a zero denominator never produces a rate", reached honestly.
#:
#:   subcontractor                 REQUIRED, and it must be the SAME NAME the attribution rows
#:                                 use. A row without it is unusable and is dropped.
#:   inspections_performed         inspections of THAT FIRM'S work this period, EXCLUDING
#:                                 reinspections. The denominator of BOTH the nonconformance
#:                                 factor and the failed-inspection factor -- the owner names
#:                                 the same population for both.
#:   exposure_hours                hours worked by that firm, ROLLING TWELVE MONTHS. The safety
#:                                 factor's denominator.
#:   recordable_incidents          that firm's OSHA recordables over the same rolling twelve
#:                                 months. The safety factor's numerator -- it is a COUNT the
#:                                 safety report states, not a row-count of attribution records.
#:   environmental_actions_due     that firm's environmental actions DUE this period.
#:   audits_covering_firm          the number of audits covering that firm.
#:   items_due                     that firm's procurement items DUE.
#:   field_reports_covering_firm   field reports covering that firm's ACTIVE WORK.
#:   systems_tested                that firm's systems or items TESTED.
#:
#: HEADINGS RECOGNISED, per column:
#:   subcontractor               : subcontractor, sub, firm, company, trade_contractor, trade,
#:                                 vendor, supplier, responsible_firm, contractor, name
#:   inspections_performed       : inspections_performed, inspections, inspections_of_firm_work,
#:                                 inspection_count, inspections_this_period
#:   exposure_hours              : exposure_hours, hours_worked, manhours, man_hours,
#:                                 total_manhours, hours, labour_hours, labor_hours
#:   recordable_incidents        : recordable_incidents, recordables, osha_recordables,
#:                                 recordable_count, osha_recordable_incidents
#:   environmental_actions_due   : environmental_actions_due, environmental_actions,
#:                                 actions_due, environmental_due
#:   audits_covering_firm        : audits_covering_firm, audits, audit_count, audits_covering
#:   items_due                   : items_due, procurement_items_due, items, deliveries_due,
#:                                 scheduled_deliveries
#:   field_reports_covering_firm : field_reports_covering_firm, field_reports, reports_covering,
#:                                 field_report_count
#:   systems_tested              : systems_tested, items_tested, systems, tests_performed,
#:                                 acceptance_tests
#:
#: DENOMINATORS FOR THE SAME FIRM ON SEVERAL DOCUMENTS ARE SUMMED PER COLUMN, and which
#: documents contributed is recorded. They are never averaged and never overwritten: two
#: inspection reports covering one firm inspected that firm twice over.
_TRADE_ATTRIBUTION_NOTE = "trade_attribution_json"
_TRADE_DENOMINATOR_NOTE = "trade_denominators_json"


# The legacy `default:` arm. Note it is the same pair as risk_register — an unknown type is
# treated as narrative, which is the conservative choice: ask for a risk score and a date, never
# for numbers that would flow into CPI/SPI.
_DEFAULT_FIELDS: list[str] = ["document_risk_score", "document_date"]


def extraction_fields_for(doc_type: str) -> list[str]:
    """Fields to request from the extractor for `doc_type`.

    Returns a fresh list each call — callers historically mutated the result (appending a
    project-specific key before prompting), and a shared list would corrupt the table.
    """
    return list(_EXTRACTION_FIELDS.get(canonical_doc_type(doc_type), _DEFAULT_FIELDS))


def guess_type_from_filename(filename: str) -> str | None:
    """Filename heuristic, ported from guessTypeFromFilename_ (lines 731-755).

    Order is load-bearing, not incidental — three pairs of rules overlap and the legacy resolved
    them by position. Preserved exactly:
      * 'rfa'+'log' before 'rfi'+'log'  (an "RFI/RFA log" filename resolves to rfa_log)
      * 'rfi'+'log' before bare 'rfi'   (a log is a register, not a single request)
      * 'schedule'+'look' before bare 'schedule'  (a lookahead is not a schedule update)
    Rewriting this as a data-driven table would lose the ordering guarantee, so it stays as a
    sequence of ifs.

    DELIBERATE DIVERGENCE FROM LEGACY: the legacy final line was `return 'monthly_report'`. Every
    unrecognised filename — a contract, a photo log, a scanned letter — was therefore labelled a
    monthly progress report, and the monthly_report extraction mapping asks for EV, AC, PV, BAC
    and percent-complete. The model, told the document *is* a monthly report, obligingly produced
    numbers, and those fabricated project-controls inputs flowed into CPI/SPI. That is a
    correctness defect, not a UX wrinkle. Returning None instead lets the caller record the
    document as UNMAPPED and extract nothing, which is the honest outcome.
    """
    f = str(filename).lower()
    if "pay" in f or "payapp" in f:
        return "pay_application"
    if "monthly" in f or "progress" in f:
        return "monthly_report"
    if "rfa" in f and "log" in f:
        return "rfa_log"
    if "rfi" in f and "log" in f:
        return "rfi_log"
    # A bare "rfi" filename used to resolve to the individual `rfi` form. That form no longer
    # arrives (registers and logs only), and guessing "rfi_log" for a single RFI would ask it
    # for totals it cannot supply — the exact fabrication this heuristic's None arm exists to
    # avoid. An individual RFI is UNMAPPED and contributes nothing.
    if "oac" in f or "minutes" in f:
        return "oac_minutes"
    if "schedule" in f and "look" in f:
        return "lookahead_schedule"
    if "schedule" in f:
        return "schedule_update"
    if "change" in f or "_co_" in f:
        return "change_order"
    if "field" in f:
        return "field_report"
    if "inspect" in f:
        return "inspection_report"
    if "ncr" in f:
        return "ncr_log"
    if "subcontractor" in f or "subcon" in f:
        return "subcontractor_report"
    if "procurement" in f:
        return "procurement_log"
    if "resource" in f:
        return "resource_report"
    if "cost" in f:
        return "cost_report"
    if "past" in f or "performance" in f:
        return "past_performance_report"
    if "safety" in f:
        return "safety_report"
    if "quality" in f or "audit" in f:
        return "quality_audit_report"
    if "environ" in f:
        return "environmental_report"
    if "historic" in f:
        return "historical_data"
    return None


# --------------------------------------------------------------------------- legacy aliases
#
# THE SUBMITTAL SPLIT. "submittal" named two documents that behave differently.
#
# An individual submittal is one item moving through review: it has a state (submitted, under
# review, approved, revise-and-resubmit, rejected), it is an EVENT, and a corrected resubmission
# is a NEW event about the same item. A submittal register is the log of all of them: it is a
# SNAPSHOT, and a later revision of the register REPLACES the earlier one.
#
# The extraction mapping only ever asked for `submittals_total` and `submittals_rejected`, which
# are register fields. The individual form has no fields, no state, and no item identity anywhere
# in this pipeline, so it was never actually supported: a document that is one submittal produced
# either nulls or, worse, the model's guess at a total. The register is what the platform keeps.
#
# The canonical name is now `submittal_register`, so the type says which of the two it is.
# `submittal` REMAINS ACCEPTED and normalises to the register, because `Document.doc_type` rows
# already carry the old string and dropping it would make every stored submittal silently stop
# contributing at the next recompute. Silent loss is the failure mode this codebase refuses.
LEGACY_TYPE_ALIASES: dict[str, str] = {
    "submittal": "submittal_register",
}


def canonical_doc_type(doc_type: str) -> str:
    """The current name for a possibly-legacy type string. Identity for everything else."""
    return LEGACY_TYPE_ALIASES.get(doc_type, doc_type)


def is_mapped(doc_type: str) -> bool:
    """True iff `doc_type` is one the extraction pipeline recognises.

    Deliberately checks DOC_TYPES rather than the _EXTRACTION_FIELDS keys: the two happen to
    coincide today, but DOC_TYPES is what the classifier prompt offers, and a type the classifier
    cannot emit is not "mapped" no matter what the field table says.

    Legacy aliases resolve first, so a stored `submittal` row is still mapped.
    """
    return canonical_doc_type(doc_type) in DOC_TYPES


if __name__ == "__main__":
    for _t in DOC_TYPES:
        _fields = extraction_fields_for(_t)
        assert _fields, f"empty field list for doc type {_t!r}"
        for _f in _fields:
            assert isinstance(_f, str), f"non-str field {_f!r} for {_t!r}"

    # The divergence itself, asserted so nobody "restores" the monthly_report fallback.
    assert guess_type_from_filename("totally-unknown-thing.pdf") is None

    # The ordering traps, resolving the legacy way — and the individual RFI routing to
    # unmapped rather than being asked for a register's totals.
    assert guess_type_from_filename("project-rfa-log.pdf") == "rfa_log"
    assert guess_type_from_filename("project-rfi-log.pdf") == "rfi_log"
    assert guess_type_from_filename("rfi-0042.pdf") is None
    assert "rfi" not in DOC_TYPES and not is_mapped("rfi")
    assert guess_type_from_filename("weekly-lookahead-schedule.pdf") == "lookahead_schedule"
    assert guess_type_from_filename("schedule-update-may.pdf") == "schedule_update"

    # THE LEGACY FALL-THROUGH IS DELIBERATELY BROKEN. This assertion used to require the two
    # lists to stay equal, which was the right tripwire while both types were treated as
    # narrative. A notice is an event and now carries the fields an event needs, so the
    # assertion is inverted: what has to stay true is that the notice carries MORE than the
    # narrative default and that the register carries exactly it, since the register's rows are
    # read from the document rather than asked for.
    _notice = extraction_fields_for("correspondence_notice")
    _register = extraction_fields_for("risk_register")
    assert _register == ["document_risk_score", "document_date"], _register
    assert set(_register).issubset(set(_notice)) and len(_notice) > len(_register)
    assert "notice_date_served" in _notice and "notice_contract_form" in _notice
    # A DEADLINE IS NEVER ASKED OF THE MODEL. It is derived in code from the named form.
    assert not any("deadline" in f for f in _notice), _notice

    print("extraction_fields self-check: OK")
