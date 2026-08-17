"""
Per-field behaviour declarations for the observation storage layer.

THE RULE ATTACHES TO A FIELD, NOT TO A DOCUMENT TYPE. That is the change that makes the
document table expressible: a pay application emits `ac` as a SNAPSHOT and a change order
record as an EVENT from the same extraction. The registry, not the document branch, owns the
declaration — a merge branch cannot quietly decide that a count accumulates.

FOUR KINDS, matching the four behaviours the storage has to hold:

  * SNAPSHOT  — the latest revision within a period is that period's observation (register
                replace). Across periods, each period's selection is one point of a series.
  * EVENT     — dated records with identity; a revision supersedes THAT record, never the
                population. Aggregation is over latest-per-entity.
  * DELTA     — summed within a period, never across, never mixed with a SNAPSHOT of the
                same quantity. Declared for completeness; NO FIELD DECLARES IT TODAY. The
                two accumulating branches (individual-RFI counts, implicit change-order
                increments) died with the individual forms — see WRITERS below.
  * PERMANENT — never superseded or replaced by anything later. The original baseline.

WRITER PRECEDENCE IS DECLARED, NOT AN ACCIDENT OF SORT ORDER. The legacy fold resolved
multi-writer fields by alphabetical doc_type within rank, which produced the documented
defects: `"rfi" < "rfi_log"` was the only thing preventing a double count, and a change order
overwrote `bac` because rank 2 folds last. Here each field lists its writers in PRECEDENCE
tiers: a lower tier always beats a higher one, and WITHIN a tier the latest `as_of` wins —
recency on the value's own date, never on a content hash. Undated observations never beat
dated ones and fall back to the fold's historical (rank, doc_type, sha256) order, which keeps
selection fully deterministic and order independent.
"""

from __future__ import annotations

SNAPSHOT = "SNAPSHOT"
EVENT = "EVENT"
DELTA = "DELTA"
PERMANENT = "PERMANENT"

KINDS = frozenset({SNAPSHOT, EVENT, DELTA, PERMANENT})


# --------------------------------------------------------------------------- field kinds
#
# Every signalInputs field the emission layer can produce, and its kind. A field absent from
# this dict cannot be emitted — emit_observations refuses it — so a new field is a visible,
# reviewed addition here rather than a line in a merge branch.
FIELD_KINDS: dict[str, str] = {
    # -- contract baseline: the original persists, whatever arrives later ------------------
    "baselineStart": PERMANENT,
    "baselineContractSum": PERMANENT,
    # -- effective contract state: amendments layered on the baseline ----------------------
    "bac": SNAPSHOT,
    "baselineEnd": SNAPSHOT,          # original preserved as contract_value's observation
    "revisedContractSum": SNAPSHOT,
    # -- change orders: an event ledger; a revision supersedes that CO, not the count ------
    "changeOrderCount": EVENT,
    # -- EVM / progress snapshots -----------------------------------------------------------
    "ev": SNAPSHOT, "ac": SNAPSHOT, "pv": SNAPSHOT,
    "actualPctComplete": SNAPSHOT, "plannedPctComplete": SNAPSHOT,
    "docRiskScore": SNAPSHOT,
    "workPeriodFrom": SNAPSHOT, "workPeriodTo": SNAPSHOT,
    "totalFloat": SNAPSHOT, "consumedFloat": SNAPSHOT,
    "originalContingency": SNAPSHOT, "remainingContingency": SNAPSHOT,
    # -- registers and logs: latest revision within the period is the observation ----------
    "rfiCount": SNAPSHOT, "rfiPeriodDays": SNAPSHOT,
    "rfiOpen": SNAPSHOT, "rfiOverdue": SNAPSHOT,
    "rfiAvgResponseDays": SNAPSHOT, "rfiOldestOpenDays": SNAPSHOT,
    "submittalsTotal": SNAPSHOT, "submittalsRejected": SNAPSHOT,
    "rfaTotal": SNAPSHOT, "rfaApproved": SNAPSHOT, "rfaRejected": SNAPSHOT,
    "rfaResubmit": SNAPSHOT, "rfaOpen": SNAPSHOT, "rfaAvgReviewDays": SNAPSHOT,
    "ncrIssued": SNAPSHOT, "ncrClosed": SNAPSHOT, "ncrOpen": SNAPSHOT,
    # -- everything else: one writer, snapshot semantics ------------------------------------
    "weatherDaysLost": SNAPSHOT, "floatRemaining": SNAPSHOT,
    "oshaIncidentRate": SNAPSHOT, "totalManhours": SNAPSHOT,
    "oshaRecordableIncidents": SNAPSHOT,
    "qualityAuditScore": SNAPSHOT, "totalFindings": SNAPSHOT, "criticalFindings": SNAPSHOT,
    "environmentalComplianceRate": SNAPSHOT, "environmentalViolations": SNAPSHOT,
    "subcontractorComplianceScore": SNAPSHOT,
    "longLeadItemsTotal": SNAPSHOT, "longLeadAtRisk": SNAPSHOT, "longLeadDelayed": SNAPSHOT,
    "activitiesPlanned": SNAPSHOT, "activitiesConstrained": SNAPSHOT, "lookaheadWeeks": SNAPSHOT,
    "plannedLaborHours": SNAPSHOT, "actualLaborHours": SNAPSHOT,
    "indirectCostPlan": SNAPSHOT, "indirectCostActual": SNAPSHOT,
    "materialCostBaseline": SNAPSHOT, "materialCostCurrent": SNAPSHOT,
    "overallRating": SNAPSHOT, "scheduleRating": SNAPSHOT,
    "costRating": SNAPSHOT, "qualityRating": SNAPSHOT,
    "analogousOverrunPct": SNAPSHOT, "analogousBac": SNAPSHOT, "analogousFinalCost": SNAPSHOT,
    "subcontractorIssuesDiscussed": SNAPSHOT, "outstandingActionItems": SNAPSHOT,
    "subcontractorDisputes": SNAPSHOT, "safetyIncidentsDiscussed": SNAPSHOT,
    "safetyActionsOpen": SNAPSHOT, "environmentalIssuesDiscussed": SNAPSHOT,
    "qualityIssuesDiscussed": SNAPSHOT, "weatherDaysDiscussed": SNAPSHOT,
    "qualityDeficienciesNoted": SNAPSHOT, "itemsInspected": SNAPSHOT, "itemsFailed": SNAPSHOT,
    "criticalDeficiencyCount": SNAPSHOT,
}

# Fields that exist in the legacy key order but that NOTHING can emit any more. They stay in
# the output dict as None forever (the computations that read them abstain), and they are
# listed here so their absence is a recorded decision, not drift:
#   rfiNumber, rfiResponseTimeDays — written only by the individual `rfi` form, which no
#   longer arrives (registers and logs only; individual forms route to unmapped).
#   docDate — no longer a written field at all: it is DERIVED at selection as the latest
#   `as_of` among selected observations, the same rule `_derive_cutoff` uses, so the
#   pipeline has ONE answer to "as of when".
UNEMITTABLE_FIELDS: frozenset[str] = frozenset({"rfiNumber", "rfiResponseTimeDays", "docDate"})


# --------------------------------------------------------------------------- numeric contract
#
# D2. Which signalInputs fields are NUMERIC, and which of those may legitimately be negative.
# The rule is per FIELD, like everything else in this registry: a value that is present but
# not readable as a number is a contract violation by the extraction model and is REFUSED at
# every entry point (see extraction_merge.validate_numeric_fields), never coerced to 0.0.
#
# Four date-string fields are the only non-numeric emittable fields; cpi and spi are derived
# but reachable through the legacy overwritesignal action, so they carry the contract too.
DATESTR_SI_FIELDS: frozenset[str] = frozenset(
    {"baselineStart", "baselineEnd", "workPeriodFrom", "workPeriodTo"})

NUMERIC_SI_FIELDS: frozenset[str] = (
    frozenset(FIELD_KINDS) - DATESTR_SI_FIELDS) | frozenset({"cpi", "spi"})

# THE COMPLETE SET OF NAMES A signalInputs FIELD MAY HAVE. Every emittable field (FIELD_KINDS),
# every date-string field, the three keys nothing can emit any more but that the computation
# layer still reads (UNEMITTABLE_FIELDS), and the two derived indices reachable through the
# legacy overwritesignal action. This is the single declared vocabulary: a name outside it is
# not a field this platform has ever read from or computed into, and writing one would be a
# key nothing cleans up and no computation reads. `w_overwritesignal` refuses by this set
# rather than carrying its own list, so the two can never drift apart.
ALL_SI_FIELDS: frozenset[str] = (
    frozenset(FIELD_KINDS) | DATESTR_SI_FIELDS | UNEMITTABLE_FIELDS | frozenset({"cpi", "spi"})
)

# Fields where a NEGATIVE value is a real project condition, not a contract violation:
#   totalFloat / consumedFloat / floatRemaining — negative float is a genuine schedule state;
#   analogousOverrunPct — a reference project that UNDERRAN is a negative overrun.
# Everything else numeric is a count, a sum, an hour figure, a rate or a score, and a
# negative one is out of contract. docRiskScore additionally has its own 0..1 guard
# (validate_doc_risk_score), which stays the authority for its range.
SIGNED_SI_FIELDS: frozenset[str] = frozenset(
    {"totalFloat", "consumedFloat", "floatRemaining", "analogousOverrunPct"})

# RUN 14. THE UPPER END OF THE DOMAIN, PER FIELD, FOR THE FIELDS THAT HAVE ONE.
#
# Run 13 recorded five modules that read an impossible figure as evidence of health, and the
# reason was the same in all five: the numeric contract bounded values from BELOW only, so a
# percent complete of ten thousand was stored, reached the analytical layer, and banded Green
# because the arithmetic it feeds is monotone in the favourable direction. The fix belongs
# here, with the field, because the bound is a property of the quantity and not of any module.
#
# ONLY FIELDS WHOSE QUANTITY IS BOUNDED BY ITS OWN DEFINITION ARE LISTED. A percent complete
# cannot exceed one hundred; a compliance RATE expressed as a share cannot exceed one; an audit
# SCORE on a hundred point scale cannot exceed one hundred. A cost index, an hour figure, a
# count, a sum and a reference project's overrun have no upper limit their definition supplies,
# and NO limit is invented for them: an implausible figure is not an impossible one, and a
# blanket percentage ceiling over semantically different quantities would refuse real projects.
#
# The membership of this table is not new to Run 14. It is the bounded set Run 13's own
# evidence builder declared when it classified which out-of-domain values were findings
# (tools/build_run13_evidence.py, BOUNDED_MAX), so the production guard and the audit that
# found the defect agree by construction rather than by coincidence.
#
# docRiskScore is deliberately ABSENT: validate_doc_risk_score is and stays the authority for
# its 0..1 range, and two authorities for one field is how a range check drifts.
BOUNDED_MAX_SI_FIELDS: dict[str, float] = {
    "actualPctComplete": 100.0,
    "plannedPctComplete": 100.0,
    "environmentalComplianceRate": 1.0,
    "qualityAuditScore": 100.0,
    "subcontractorComplianceScore": 100.0,
}


# --------------------------------------------------------------------------- writer tiers
#
# field -> {doc_type: tier}. Lower tier wins outright; within a tier, latest as_of.
# A (field, doc_type) pair absent here has tier DEFAULT_TIER. Only multi-writer fields need
# an entry, and each entry records WHY the precedence is what it is.
DEFAULT_TIER = 0

WRITER_TIERS: dict[str, dict[str, int]] = {
    # A change order is the authoritative amendment to the contract sum; the contract
    # establishes it; SoV / pay app / monthly report are progressively weaker fallbacks.
    # (Legacy: contract_value wrote first, fallbacks first-non-null, change_order overwrote
    # by folding last — same outcome, now stated instead of emergent.)
    "bac": {"change_order": 0, "contract_value": 1, "schedule_of_values": 2,
            "pay_application": 3, "monthly_report": 4},
    # The ORIGINAL baseline: the contract's own figure beats a change order's account of it.
    # Legacy could not express this — baselineContractSum existed only if a CO carried it.
    "baselineContractSum": {"contract_value": 0, "change_order": 1},
    # The effective completion date: the latest executed amendment, else the contract.
    "baselineEnd": {"change_order": 0, "contract_value": 1},
    "ev": {"schedule_of_values": 0, "pay_application": 1, "monthly_report": 2},
    "pv": {"schedule_update": 0, "time_phased_schedule": 1, "monthly_report": 2},
    "ac": {"pay_application": 0, "monthly_report": 1},
    "actualPctComplete": {"pay_application": 0, "monthly_report": 1},
    "plannedPctComplete": {"schedule_update": 0, "time_phased_schedule": 1,
                           "monthly_report": 2},
    # Two different quantities share this slot (the A7 collision). The field report's own
    # count keeps winning, as it always has — preserved deliberately, now visible here.
    "qualityDeficienciesNoted": {"field_report": 0, "inspection_report": 1},
    # RFA figures stand in for submittal totals only when no register supplied them.
    "submittalsTotal": {"submittal_register": 0, "rfa_log": 1},
    "submittalsRejected": {"submittal_register": 0, "rfa_log": 1},
    # schedule_update revises what time_phased_schedule established.
    "totalFloat": {"schedule_update": 0, "time_phased_schedule": 1},
    "consumedFloat": {"schedule_update": 0, "time_phased_schedule": 1},
    "activitiesPlanned": {"schedule_update": 0, "lookahead_schedule": 1},
    "activitiesConstrained": {"schedule_update": 0, "lookahead_schedule": 1},
    "lookaheadWeeks": {"schedule_update": 0, "lookahead_schedule": 1},
}


def writer_tier(field: str, doc_type: str) -> int:
    return WRITER_TIERS.get(field, {}).get(doc_type, DEFAULT_TIER)


# --------------------------------------------------------------------------- needs
#
# Layer 3: what the analytical layer needs, in shapes. The assembler serves these; a
# computation that cannot obtain what it needs ABSTAINS (the standing default) rather than
# receiving a substitute. Enforcement inside the simulation registry would mean changing
# `server/app/simulation/`, which is out of scope; these declarations are the app-side half:
# documents.py serves exactly what is declared servable and fabricates nothing.
SCALAR = "SCALAR"
SERIES = "SERIES"
EVENT_SET = "EVENT_SET"

NEEDS: dict[str, dict] = {
    # Served by `_period_history` from earlier periods' stored live results — strictly
    # earlier periods, minimum two points. Do not regress.
    "cpiHistory": {"shape": SERIES, "min_points": 2, "servable": True},
    "spiHistory": {"shape": SERIES, "min_points": 2, "servable": True},
    # SERVABLE SINCE 0021. One snapshot per reporting period, assembled by
    # `documents._milestone_history` from the `schedule_activities` store — strictly earlier
    # periods plus the one being computed, minimum two snapshots. It was declared unservable
    # for two real reasons, both now closed on the app side: the extraction returned the source
    # table's own column headings (mapped in `schedule_activities.py`) and its dates parsed with
    # nothing (`schedule_dates.py`, which REFUSES rather than guessing a year). A period that
    # read no schedule contributes no snapshot, and fewer than two snapshots means the key is
    # absent and Milestone Trend Analysis abstains on its own guard.
    "milestoneHistory": {"shape": SERIES, "min_points": 2, "servable": True},
    # Change orders arrive executed; the ledger is filtered to that state by declaration.
    "changeOrderCount": {"shape": EVENT_SET, "states": {"executed"}, "servable": True},
}


def unservable_needs() -> list[str]:
    """The declared needs nothing can serve. These must abstain, never be synthesised."""
    return sorted(k for k, v in NEEDS.items() if not v.get("servable"))
