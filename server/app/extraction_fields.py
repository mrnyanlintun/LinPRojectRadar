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

# The "Planning & Governance Documents" optgroup from assets/js/signals.js DOC_TYPE_GROUPS
# (lines 59-75). These 15 types are offered to the PM in the upload dropdown, but they appear in
# NO extraction mapping, NO validTypes, and NO filename heuristic — a PM can select "BIM Execution
# Plan", upload it, get a success response, and have contributed exactly nothing to signalInputs.
# Silence there reads as "ingested and understood". This tuple exists so the upload response can
# say so out loud: accepted, stored, but no project-controls signal was derived.
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
        "schedule_baseline_finish_day", "schedule_imposed_finish_day", "schedule_version",
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
    "correspondence_notice": [
        "document_risk_score", "document_date",
        "notice_served_by", "notice_served_on", "notice_claim", "notice_date_served",
        "notice_contract_form", "notice_kind", "notice_references",
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
    ],
    "field_report": [
        "document_risk_score", "document_date", "weather_days_lost", "float_remaining",
        "quality_deficiencies_noted", "safety_observations", "environmental_observations",
        "subcontractor_observations",
    ],
    "commissioning_report": ["document_risk_score", "document_date"],
    "safety_report": [
        "osha_recordable_incidents", "total_manhours", "incident_rate", "report_period",
    ],
    # RUN 87. THE SAME TABLE OFF THE QUALITY AUDIT REPORT, for the same reason: an audit score
    # and a findings count are the summaries the specification names, and the audit's own
    # findings/requirements schedule is the population it summarises.
    "quality_audit_report": [
        "total_findings", "critical_findings", "deficiency_count", "audit_score", "audit_date",
        "quality_requirements_json", "quality_register_id", "quality_register_period",
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
    ],
    "ncr_log": [
        "ncr_issued", "ncr_closed", "ncr_open", "ncr_overdue", "report_period",
        # RUN 106, SECTION 3. The denominator the owner's ladder is drawn over, and which of the
        # two it is, stated by the document rather than assumed by this platform.
        "inspections_performed", "active_work_packages", "ncr_denominator_basis",
        "open_critical_ncr_json", "hold_point_or_turnover_blocking_ncr_json",
        "max_repeat_ncrs_one_root_cause_or_trade", "ncr_open_past_contractual_closure_json",
    ],
    "subcontractor_report": [
        "scheduled_deliveries", "on_time_deliveries", "compliance_score", "report_period",
    ],
    "procurement_log": [
        "long_lead_items_total", "on_schedule", "at_risk", "delayed", "report_date",
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
