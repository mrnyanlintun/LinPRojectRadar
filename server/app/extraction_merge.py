"""Observation emission and selection: ``signalInputs`` as the OUTPUT of a pure selection.

WHAT CHANGED, AND WHY (the storage redesign, REPORT_2026-08-02_document-reconciliation.md
Part F). The previous version of this module was a pure fold transcribed 1:1 from the Apps
Script if/else-if chain: last-write-wins in ``(rank, doc_type, sha256)`` sort order, two
additive accumulators, and one direct dictionary write. The fold was deterministic and order
independent — properties this module keeps — but *which* value won a field was decided by
alphabetical accidents (``"rfi" < "rfi_log"`` was the only thing preventing a double count),
by content-hash tiebreaks between revisions (a corrected document won or lost each field on
its sha256), and by a change order destroying the contract baseline because rank 2 folds
last.

The merge is now TWO stages, both pure:

1. ``emit_observations(doc)`` — one document's extraction becomes observation records:
   ``(field, value, kind, entity_key, entity_state, as_of)``. The KIND comes from
   ``field_registry.FIELD_KINDS`` — the rule attaches to the FIELD, not the document type.
   ``as_of`` is the date the value speaks about, from the document's own date fields, or
   None when none parses. Nothing here reads a clock.

2. ``select_signal_inputs(observations, cutoff)`` — the same flat dict the computation
   layer has always consumed, produced by per-field selection:

   * SNAPSHOT — lowest writer tier wins (declared precedence, ``field_registry.WRITER_TIERS``,
     not sort order); within a tier the latest ``as_of`` wins. A dated observation always
     beats an undated one; wholly undated groups fall back to the fold's historical
     ``(rank, doc_type, sha256)`` last-write order, so selection stays deterministic and
     order independent. RECENCY IS NEVER DECIDED BY A CONTENT HASH between dated values.
   * PERMANENT — the EARLIEST wins and nothing later replaces it. The original baseline
     persists (``baselineStart``, ``baselineContractSum``).
   * EVENT — grouped by entity; the latest non-superseded observation per entity is that
     entity's record (a revision supersedes THAT record, never the population); entities are
     then aggregated. An explicit stated total still beats counting.
   * DELTA — summed within the period, never across. No field declares it today; the two
     accumulating branches died with the individual forms.

   ``docDate`` is no longer a written field: it is DERIVED as the latest ``as_of`` among the
   period's eligible observations — the same rule ``_derive_cutoff`` uses — so the pipeline
   has ONE answer to "as of when" instead of two.

WHAT DID NOT CHANGE. The output dict: same keys, same ``_KEY_ORDER`` insertion order (the
simulation layer iterates insertion order — DO NOT SORT), same ``sources`` shape, same
``cpi``/``spi`` derivation, same doc-risk refusal. (One legacy quirk is deliberately DEAD:
``_num_or_null``'s malformed-text-becomes-0.0 — D2's numeric contract refuses such a value
at every entry point before any coercion could run; see the numeric-contract section.) ``assemble_signal_inputs(documents)`` keeps its signature and its three properties:

    assemble_signal_inputs(docs) == assemble_signal_inputs(docs)            (determinism)
    assemble_signal_inputs(shuffle(docs)) == assemble_signal_inputs(docs)   (order independence)
    assemble_signal_inputs([d, d]) == assemble_signal_inputs([d])           (idempotence)

REGISTERS AND LOGS ONLY. Individual submittals, RFIs and RFAs do not arrive; the PM sees the
register. The individual ``rfi`` form routes to UNMAPPED (see extraction_fields.py), so its
accumulating ``add()`` branch is gone, and with it the undocumented ``"rfi" < "rfi_log"``
ordering dependency: ``rfiCount`` has exactly one writer, the log's absolute total.

CONTRACT VALUE BASELINE PRESERVATION. ``contract_value`` emits ``baselineContractSum``
(PERMANENT — the original sum survives every later document) alongside ``bac``; a change
order's ``revised_contract_sum`` wins ``bac`` by declared tier, as the executed amendment
layered on that baseline. ``baselineEnd`` follows the same declared precedence — the direct
dictionary write that bypassed ``set_field`` no longer exists, and the contract's original
end date is retained as its own observation, readable from the observation store.

PURITY. No network, no filesystem, no database, no clock — both stages. Persistence of
observation rows is documents.py's job.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .extraction_fields import UNMAPPED, canonical_doc_type, is_mapped
from .field_registry import (
    DELTA, EVENT, FIELD_KINDS, NEEDS, PERMANENT, SNAPSHOT, UNEMITTABLE_FIELDS, writer_tier,
)

__all__ = [
    "assemble_signal_inputs",
    "assembly_report",
    "emit_observations",
    "select_signal_inputs",
    "DOC_RISK_DOC_TYPES",
    "DOC_RISK_SCORE_MAX",
    "DOC_RISK_SCORE_MIN",
    "DocRiskScoreRangeError",
    "MalformedNumericError",
    "NumericRangeError",
    "SIGNAL_INPUT_KEYS",
    "validate_doc_risk_score",
    "validate_numeric_fields",
    "validate_signal_value",
]


# --------------------------------------------------------------------------- doc risk
# The doc types whose extraction carries `document_risk_score`. The individual `rfi` form is
# gone — registers and logs only — so it is no longer in this set.
DOC_RISK_DOC_TYPES: frozenset[str] = frozenset(
    {
        "submittal_register",
        "oac_minutes",
        "correspondence_notice",
        "risk_register",
        "inspection_report",
        "field_report",
        "commissioning_report",
    }
)

# --------------------------------------------------------------------------- key order
# Verbatim transcription of the si initializer, .gs lines 812-832, in source order.
# DO NOT SORT and DO NOT REORDER: the simulation layer iterates insertion order.
# `rfiNumber` and `rfiResponseTimeDays` remain as keys — always None now that the individual
# rfi form routes to unmapped — because the computation layer expects the keys to exist.
_KEY_ORDER: tuple[str, ...] = (
    "bac", "ev", "ac", "pv", "actualPctComplete", "plannedPctComplete",
    "docRiskScore", "baselineStart", "baselineEnd", "workPeriodFrom", "workPeriodTo", "docDate",
    "totalFloat", "consumedFloat", "originalContingency", "remainingContingency",
    "rfiCount", "rfiPeriodDays", "submittalsTotal", "submittalsRejected",
    "changeOrderCount", "baselineContractSum", "revisedContractSum",
    "weatherDaysLost", "floatRemaining", "oshaIncidentRate", "totalManhours",
    "qualityAuditScore", "totalFindings", "criticalFindings",
    "environmentalComplianceRate", "environmentalViolations",
    "ncrIssued", "ncrClosed", "ncrOpen", "subcontractorComplianceScore",
    "longLeadItemsTotal", "longLeadAtRisk", "longLeadDelayed",
    "activitiesPlanned", "activitiesConstrained", "lookaheadWeeks",
    "plannedLaborHours", "actualLaborHours", "indirectCostPlan", "indirectCostActual",
    "materialCostBaseline", "materialCostCurrent", "overallRating", "scheduleRating",
    "costRating", "qualityRating", "analogousOverrunPct", "analogousBac", "analogousFinalCost",
    "subcontractorIssuesDiscussed", "outstandingActionItems", "subcontractorDisputes",
    "safetyIncidentsDiscussed", "safetyActionsOpen", "environmentalIssuesDiscussed",
    "qualityIssuesDiscussed", "weatherDaysDiscussed", "rfiNumber", "rfiResponseTimeDays",
    "qualityDeficienciesNoted", "itemsInspected", "itemsFailed", "criticalDeficiencyCount",
    "rfiOpen", "rfiOverdue", "rfiAvgResponseDays", "rfiOldestOpenDays",
    "rfaTotal", "rfaApproved", "rfaRejected", "rfaResubmit", "rfaOpen", "rfaAvgReviewDays",
)

#: Public, stable view of the signalInputs key order (excluding "sources"/"cpi"/"spi").
SIGNAL_INPUT_KEYS: tuple[str, ...] = _KEY_ORDER


# --------------------------------------------------------------------------- primitives


def _num_or_null(v: Any) -> float | int | None:
    """Port of ``numOrNull_`` (.gs 1135-1139), quirks included.

    JS:
        if (v === null || v === undefined || v === '') return null;
        var n = Number(String(v).replace(/[^0-9.\\-]/g,''));
        return isNaN(n) ? null : n;

    Consequences reproduced on purpose:
      * ``"N/A"`` strips to ``""`` and ``Number("")`` is ``0`` -> returns 0.0, NOT None.
        Downstream this lands in the "0 is falsy, treated as absent" bucket, which is
        exactly how the instrument has always behaved.
      * ``"$1,200,000"`` -> 1200000.0 (currency/comma stripping).
      * ``"1.2.3"`` or ``"--5"`` -> Number(...) is NaN -> None.
      * ``False`` -> "False" -> "" -> 0.0. Booleans are not special-cased in JS either.
    """
    if v is None or v == "":
        return None
    # bool is an int subclass in Python; JS would stringify it, so mirror that.
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, (int, float)):
        # Fast path: already numeric. JS String(1e21) would be "1e+21" and strip to
        # "121" — a pathological magnitude we do not expect from a currency extractor,
        # and mangling it here would be strictly worse than passing it through.
        return v
    else:
        s = str(v)
    stripped = "".join(ch for ch in s if ch.isdigit() or ch in ".-")
    if stripped == "":
        return 0.0  # Number("") === 0 in JS. Deliberate; see docstring.
    try:
        n = float(stripped)
    except ValueError:
        return None  # isNaN(n) -> null
    if n != n:  # NaN guard
        return None
    return n


# --------------------------------------------------------------------------- doc risk range

DOC_RISK_SCORE_MIN = 0.0
DOC_RISK_SCORE_MAX = 1.0


class DocRiskScoreRangeError(ValueError):
    """``document_risk_score`` outside its 0..1 contract."""


def validate_doc_risk_score(raw: Any, *, filename: str | None = None) -> None:
    """
    Refuse a ``document_risk_score`` outside 0..1 inclusive. Returns None, or raises.

    REFUSE, NOT CLAMP, AND NOT STORE-AND-FLAG. This is a decision, recorded here because the
    alternatives are each worse in a way that is easy to argue for and hard to detect later:

      * Clamping turns -3 into a confident 0.0, which reads as the BEST band. Nothing
        downstream could trace that Green back to a bad input, and the project would look
        healthier than the evidence supports. A silent repair in the reassuring direction is
        the worst of the three.
      * Store-and-flag keeps the wrong number in the research record and relies on somebody
        reading the flag. The value would still reach fusion.
      * Refusing says what happened, at the moment it happened, to the person who can act.

    Out of range is a contract violation by the extraction model, not a data condition of the
    project, so the platform states it rather than repairing it. "Loud refusal over quiet
    approximation" is the standing rule and this is the case it was written for.

    NOT a range violation, and deliberately allowed through:
      * ``None`` / absent. The field is optional; most doc types never carry it.
      * A value that does not parse as a number at all (``"1.2.3"``). ``_num_or_null`` returns
        None for those and the merge stores nothing, which is already the honest outcome.
      * ``"N/A"`` and other unparseable strings, which ``_num_or_null`` coerces to 0.0 by a
        documented legacy quirk. In range, so THIS guard leaves them alone — but they no
        longer reach it at any guarded boundary: D2's ``validate_numeric_fields`` refuses a
        present-but-unreadable value first, so the coerced 0.0 is dead at every entry point.

    0 and 1 are both VALID. 0 is a genuine "no concern" reading and must survive to storage
    (there is a standing assertion at the bottom of this module that a genuine 0 is stored),
    and the prompt asks the model for a number "between 0 and 1 inclusive".
    """
    if raw is None or raw == "":
        return
    value = _num_or_null(raw)
    if value is None:
        return
    if DOC_RISK_SCORE_MIN <= value <= DOC_RISK_SCORE_MAX:
        return
    where = f" in {filename}" if filename else ""
    raise DocRiskScoreRangeError(
        f"document_risk_score{where} is {value}, which is outside the required range "
        f"{DOC_RISK_SCORE_MIN} to {DOC_RISK_SCORE_MAX} inclusive. It is a risk rating on a "
        f"0 to 1 scale, not a percentage and not a count. Nothing was stored for this "
        f"document and no figures from it were used. Re-run the extraction, or supply the "
        f"document again, and if it keeps happening the extraction model is returning the "
        f"wrong scale for this document type."
    )


# --------------------------------------------------------------------------- numeric contract
#
# D2. A model returning "TBD" for earned value used to yield 0.0 — the worst possible cost
# performance, asserted confidently — because `_num_or_null` reproduces the legacy JS quirk
# Number("") === 0. Under the observation store a wrong value is no longer transient: it
# persists as a row and is selected on every later computation, so a single malformed
# extraction poisons a project until someone notices. The fix is the risk-score pattern:
# REFUSE at every point a numeric value can enter, so nothing out of contract reaches storage
# or computation by any path.
#
# Three cases, treated differently:
#   ABSENT     — None or "". The field was not in the document. The observation is simply not
#                emitted and the computation abstains. Unchanged.
#   MALFORMED  — present but not readable as a number ("TBD", "N/A", "unknown", "1.2.3", a
#                boolean). Refused: if the document genuinely lacks the value the extraction
#                should return null, not prose.
#   OUT OF CONTRACT — readable, but outside the field's permitted range (a negative count or
#                sum; a docRiskScore outside 0..1, which keeps its own guard). Refused.
#
# THE PARSING RULE, deliberately more careful than both alternatives. A strict float() parse
# would refuse legitimate real-world figures: currency ("$1,200,000"), thousands separators
# ("1,200"), percentages written with the symbol ("45%"), and accountants' negatives
# ("(500)"). The legacy `numOrNull_` stripped every non-numeric character first, which is why
# "TBD" became 0 and why "(500)" silently became POSITIVE 500. This parser accepts exactly the
# recognised decorations — currency symbol, comma separators, spaces, one trailing %, and
# parentheses meaning negative (honoured, not stripped) — and refuses anything else.

_CURRENCY_CHARS = "$€£"


class MalformedNumericError(ValueError):
    """A numeric extraction field is present but cannot be read as a number."""


class NumericRangeError(ValueError):
    """A numeric extraction field parses, but sits outside the field's permitted range."""


def _parse_numeric(v: Any) -> tuple[str, float | int | None]:
    """('absent' | 'ok' | 'malformed', value). The single numeric-reading rule."""
    if v is None or v == "":
        return "absent", None
    if isinstance(v, bool):
        return "malformed", None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
            return "malformed", None
        return "ok", v
    s = str(v).strip()
    if not s:
        return "absent", None
    negative = False
    if s.startswith("(") and s.endswith(")") and len(s) > 2:
        negative = True
        s = s[1:-1].strip()
    for ch in _CURRENCY_CHARS:
        s = s.replace(ch, "")
    s = s.replace(",", "").replace(" ", "")
    if s.endswith("%"):
        s = s[:-1]
    if not s:
        return "malformed", None
    try:
        n = float(s)
    except ValueError:
        return "malformed", None
    if n != n:
        return "malformed", None
    return "ok", -n if negative else n


def _coerce_numeric(v: Any) -> float | int | None:
    """Emission-side coercion: the parsed value, or None for absent. Malformed is None too,
    but is unreachable at emission because `validate_numeric_fields` refuses first."""
    status, n = _parse_numeric(v)
    return n if status == "ok" else None


# Numeric extraction keys per doc type that do NOT flow through _NUMERIC_EMISSIONS below —
# the derivation inputs and the special change-order branch. (src_key, si_field or None);
# None means the key feeds a derivation only and takes the default non-negative rule.
_EXTRA_NUMERIC_KEYS: dict[str, tuple[tuple[str, str | None], ...]] = {
    "change_order": (("revised_contract_sum", "bac"),
                     ("change_order_count", "changeOrderCount"),
                     ("baseline_contract_sum", "baselineContractSum")),
    "safety_report": (("incident_rate", "oshaIncidentRate"),
                      ("osha_recordable_incidents", None),
                      ("total_manhours", "totalManhours")),
    "subcontractor_report": (("compliance_score", "subcontractorComplianceScore"),
                             ("on_time_deliveries", None),
                             ("scheduled_deliveries", None)),
}


def _numeric_keys_for(doc_type: str) -> tuple[tuple[str, str | None], ...]:
    pairs: list[tuple[str, str | None]] = list(_NUMERIC_EMISSIONS.get(doc_type, ()))
    pairs.extend(_EXTRA_NUMERIC_KEYS.get(doc_type, ()))
    if doc_type in DOC_RISK_DOC_TYPES:
        pairs.append(("document_risk_score", "docRiskScore"))
    return tuple(pairs)


def _range_check(si_field: str | None, n: float | int, src: str,
                 filename: str | None) -> None:
    """Refuse a readable value outside the field's permitted range. docRiskScore keeps its
    own 0..1 authority (validate_doc_risk_score, run separately at the same boundaries)."""
    from .field_registry import SIGNED_SI_FIELDS
    if si_field == "docRiskScore":
        return
    if (si_field is None or si_field not in SIGNED_SI_FIELDS) and n < 0:
        where = f" in {filename}" if filename else ""
        raise NumericRangeError(
            f"{src}{where} is {_fmt_num(n)}, and this field cannot be negative. Nothing was "
            f"stored for this document and no figures from it were used. Check the document, "
            f"or re-run the extraction."
        )


def _fmt_num(n: float | int) -> str:
    return str(int(n)) if isinstance(n, float) and n.is_integer() else str(n)


def validate_numeric_fields(doc_type: str, extraction: Any, *,
                            filename: str | None = None) -> None:
    """
    Refuse a document whose extraction carries a malformed or out-of-range numeric value.
    Returns None, or raises MalformedNumericError / NumericRangeError.

    Called at EVERY entry point, before anything from the document is stored or emitted, so
    the refusal is whole-document by construction: no observation row, no Document row, no
    partial write. Absent values (None, "") pass — a missing observation means abstention,
    which is the standing default and is not changed here.
    """
    doc_type = canonical_doc_type(str(doc_type or ""))
    ex = extraction if isinstance(extraction, dict) else {}
    for src, si_field in _numeric_keys_for(doc_type):
        raw = ex.get(src)
        status, n = _parse_numeric(raw)
        if status == "absent":
            continue
        if status == "malformed":
            where = f" in {filename}" if filename else ""
            raise MalformedNumericError(
                f"{src}{where} is {raw!r}, which cannot be read as a number. Nothing was "
                f"stored for this document and no figures from it were used. If the document "
                f"does not state this value, the extraction should leave it blank rather "
                f"than write {raw!r}; re-run the extraction, or correct the document."
            )
        _range_check(si_field, n, src, filename)


def validate_signal_value(field: str, value: Any) -> None:
    """
    The same contract for a value entering a signalInputs FIELD directly (the legacy facade:
    overwritesignal, and changed fields on save). None passes — clearing a field is not a
    malformed one. docRiskScore delegates its range to validate_doc_risk_score.
    """
    from .field_registry import NUMERIC_SI_FIELDS
    if field not in NUMERIC_SI_FIELDS or value is None:
        return
    status, n = _parse_numeric(value)
    if status == "absent":
        return
    if status == "malformed":
        raise MalformedNumericError(
            f"{field} cannot be set to {value!r}: it is not readable as a number. "
            f"Nothing was changed."
        )
    if field == "docRiskScore":
        validate_doc_risk_score(value)
        return
    from .field_registry import SIGNED_SI_FIELDS
    if field not in SIGNED_SI_FIELDS and n < 0:
        raise NumericRangeError(
            f"{field} cannot be set to {_fmt_num(n)}: this field cannot be negative. "
            f"Nothing was changed."
        )


def _round3(n: float) -> float:
    """Port of ``round3_`` (.gs 1140). Math.round is half-up, unlike Python's banker's."""
    import math

    return math.floor(n * 1000 + 0.5) / 1000


def _is_blank_date(v: Any) -> bool:
    """``setDate`` guard, .gs 875: null/undefined/'' and the literal string 'null'."""
    return v is None or v == "" or str(v).lower() == "null"


def _parse_as_of(raw: Any) -> date | None:
    """The observation's own date, strictly parsed. None when it cannot be read — an undated
    value is stored as undated, NEVER stamped with the clock (that is D3, not extended here)."""
    if _is_blank_date(raw):
        return None
    try:
        return date.fromisoformat(str(raw).strip()[:10])
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- ordering
#
# The document ROLE rank, kept as the deterministic LAST tiebreak (after tier and as_of) so
# that wholly undated groups resolve exactly as the historical fold did. It no longer decides
# contested fields on its own — declared writer tiers do that.
_RANK_BASELINE = 0
_RANK_DEFAULT = 1
_RANK_REVISION = 2

_DOC_TYPE_RANK: dict[str, int] = {
    "contract_value": _RANK_BASELINE,
    "schedule_of_values": _RANK_BASELINE,
    "time_phased_schedule": _RANK_BASELINE,
    "change_order": _RANK_REVISION,
    "schedule_update": _RANK_REVISION,
}


def _doc_rank(doc_type: str) -> int:
    return _DOC_TYPE_RANK.get(doc_type, _RANK_DEFAULT)


def _ordered_docs(documents: list[dict]) -> list[dict]:
    """Sort by (rank, doc_type, sha256) and de-duplicate by sha256.

    Emission order does not affect selection (selection sorts observations itself), but the
    de-duplication here is the safety net against the legacy double-count bug, and the sort
    keeps ``assembly_report`` output and ``sources`` construction deterministic.
    """
    ordered = sorted(
        documents,
        key=lambda d: (
            _doc_rank(str(d.get("doc_type") or "")),
            str(d.get("doc_type") or ""),
            str(d.get("sha256") or ""),
        ),
    )
    seen: set[str] = set()
    out: list[dict] = []
    for d in ordered:
        sha = str(d.get("sha256") or "")
        if sha and sha in seen:
            continue
        if sha:
            seen.add(sha)
        out.append(d)
    return out


# --------------------------------------------------------------------------- emission
#
# Per doc type: which extraction date field is the document's own "as of". The observation's
# as_of comes from here, falling back to `document_date` where a type carries one.
_AS_OF_KEYS: dict[str, str] = {
    "schedule_of_values": "period_to_date",
    "pay_application": "application_date",
    "time_phased_schedule": "data_date",
    "schedule_update": "data_date",
    "monthly_report": "report_date",
    "submittal_register": "document_date",
    "oac_minutes": "document_date",
    "correspondence_notice": "document_date",
    "risk_register": "document_date",
    "inspection_report": "document_date",
    "field_report": "document_date",
    "commissioning_report": "document_date",
    "change_order": "change_order_date",
    "safety_report": "report_period",
    "quality_audit_report": "audit_date",
    "environmental_report": "report_date",
    "ncr_log": "report_period",
    "subcontractor_report": "report_period",
    "procurement_log": "report_date",
    "lookahead_schedule": "report_date",
    "cost_report": "report_date",
    "rfi_log": "log_date",
    "rfa_log": "log_date",
    # contract_value, resource_report, past_performance_report, historical_data: no as-of
    # date. historical_data's completion_year ("2019") is a year, not an as-of date — under
    # the old fold it leaked into docDate as a bare "2019"; it does not any more.
}

# Straightforward numeric emissions: doc_type -> ((extraction_key, field), ...).
# Emitted when `_num_or_null` yields a number (the setField guard: None/'' skipped, 0 kept).
_NUMERIC_EMISSIONS: dict[str, tuple[tuple[str, str], ...]] = {
    "contract_value": (
        ("original_contract_sum", "bac"),
        # THE BASELINE PRESERVATION. The contract's own sum is also the original baseline,
        # PERMANENT: it survives every change order, which previously destroyed it.
        ("original_contract_sum", "baselineContractSum"),
    ),
    "schedule_of_values": (("completed_to_date", "ev"), ("scheduled_value_total", "bac")),
    "pay_application": (
        ("amount_paid_to_date", "ac"), ("percent_complete_verified", "actualPctComplete"),
        ("original_contract_sum", "bac"), ("completed_to_date", "ev"),
        ("original_contingency", "originalContingency"),
        ("remaining_contingency", "remainingContingency"),
    ),
    "time_phased_schedule": (
        ("planned_value_to_date", "pv"), ("planned_percent_complete", "plannedPctComplete"),
        ("total_float", "totalFloat"), ("consumed_float", "consumedFloat"),
    ),
    "monthly_report": (
        ("earned_value", "ev"), ("actual_cost", "ac"), ("planned_value", "pv"),
        ("actual_percent_complete", "actualPctComplete"),
        ("planned_percent_complete", "plannedPctComplete"),
        ("budget_at_completion", "bac"),
    ),
    "oac_minutes": (
        ("subcontractor_issues_discussed", "subcontractorIssuesDiscussed"),
        ("outstanding_action_items", "outstandingActionItems"),
        ("subcontractor_disputes", "subcontractorDisputes"),
        ("safety_incidents_discussed", "safetyIncidentsDiscussed"),
        ("safety_actions_open", "safetyActionsOpen"),
        ("environmental_issues_discussed", "environmentalIssuesDiscussed"),
        ("quality_issues_discussed", "qualityIssuesDiscussed"),
        ("weather_days_discussed", "weatherDaysDiscussed"),
    ),
    "submittal_register": (
        ("submittals_total", "submittalsTotal"), ("submittals_rejected", "submittalsRejected"),
    ),
    "field_report": (
        ("weather_days_lost", "weatherDaysLost"), ("float_remaining", "floatRemaining"),
        ("quality_deficiencies_noted", "qualityDeficienciesNoted"),
    ),
    "inspection_report": (
        ("items_inspected", "itemsInspected"), ("items_failed", "itemsFailed"),
        # A7: two different quantities share this slot; the field report's own count wins by
        # declared tier (field_registry), preserved from the historical behaviour.
        ("deficiency_count", "qualityDeficienciesNoted"),
        ("critical_deficiency_count", "criticalDeficiencyCount"),
    ),
    "quality_audit_report": (
        ("audit_score", "qualityAuditScore"), ("total_findings", "totalFindings"),
        ("critical_findings", "criticalFindings"),
    ),
    "environmental_report": (
        ("compliance_rate", "environmentalComplianceRate"),
        ("violations", "environmentalViolations"),
    ),
    "ncr_log": (
        ("ncr_issued", "ncrIssued"), ("ncr_closed", "ncrClosed"), ("ncr_open", "ncrOpen"),
    ),
    "procurement_log": (
        ("long_lead_items_total", "longLeadItemsTotal"), ("at_risk", "longLeadAtRisk"),
        ("delayed", "longLeadDelayed"),
    ),
    "lookahead_schedule": (
        ("activities_planned", "activitiesPlanned"),
        ("activities_constrained", "activitiesConstrained"),
        ("lookahead_weeks", "lookaheadWeeks"),
    ),
    "resource_report": (
        ("planned_labor_hours", "plannedLaborHours"), ("actual_labor_hours", "actualLaborHours"),
    ),
    "cost_report": (
        ("indirect_cost_plan", "indirectCostPlan"), ("indirect_cost_actual", "indirectCostActual"),
        ("material_cost_baseline", "materialCostBaseline"),
        ("material_cost_current", "materialCostCurrent"),
    ),
    "past_performance_report": (
        ("overall_rating", "overallRating"), ("schedule_rating", "scheduleRating"),
        ("cost_rating", "costRating"), ("quality_rating", "qualityRating"),
    ),
    "historical_data": (
        ("analogous_overrun_pct", "analogousOverrunPct"),
        ("similar_project_bac", "analogousBac"),
        ("similar_project_final_cost", "analogousFinalCost"),
    ),
    "rfi_log": (
        # THE ONLY WRITER of rfiCount. The individual `rfi` form routes to unmapped, so the
        # accumulating add() is gone and nothing depends on "rfi" sorting before "rfi_log".
        ("rfi_total", "rfiCount"),
        ("rfi_open", "rfiOpen"), ("rfi_overdue", "rfiOverdue"),
        ("avg_response_days", "rfiAvgResponseDays"), ("rfi_period_days", "rfiPeriodDays"),
        ("oldest_open_days", "rfiOldestOpenDays"),
    ),
    "rfa_log": (
        ("rfa_total", "rfaTotal"), ("rfa_approved", "rfaApproved"),
        ("rfa_rejected", "rfaRejected"), ("rfa_resubmit", "rfaResubmit"),
        ("rfa_open", "rfaOpen"), ("avg_review_days", "rfaAvgReviewDays"),
        # RFA totals stand in for submittal totals when no register supplied them (tier 1).
        ("rfa_total", "submittalsTotal"), ("rfa_rejected", "submittalsRejected"),
    ),
    "schedule_update": (
        ("planned_percent_complete", "plannedPctComplete"), ("planned_value_to_date", "pv"),
        ("total_float", "totalFloat"), ("consumed_float", "consumedFloat"),
        ("activities_planned", "activitiesPlanned"),
        ("activities_constrained", "activitiesConstrained"),
        ("lookahead_weeks", "lookaheadWeeks"),
    ),
}

# Date-string emissions (values stay strings, `setDate` semantics: blank-guarded, String(v)).
_DATESTR_EMISSIONS: dict[str, tuple[tuple[str, str], ...]] = {
    "contract_value": (
        ("project_start_date", "baselineStart"), ("project_end_date", "baselineEnd"),
    ),
    "pay_application": (
        ("work_period_from", "workPeriodFrom"), ("work_period_to", "workPeriodTo"),
    ),
}


def emit_observations(doc: dict) -> list[dict]:
    """One stored document -> observation records. Pure; raises DocRiskScoreRangeError only.

    ``doc`` is ``{"sha256", "doc_type", "filename", "extraction"}`` plus optional
    ``document_id`` and ``supersedes`` (promoted to ``revision_of``). An unmapped type emits
    nothing. Each record carries what selection needs (field, value, kind, tier, as_of,
    entity_key, entity_state) and what provenance needs (doc_type, sha256, document_id,
    revision_of, rank).
    """
    doc_type = canonical_doc_type(str(doc.get("doc_type") or ""))
    if not doc_type or doc_type == UNMAPPED or not is_mapped(doc_type):
        return []
    ex = doc.get("extraction") or {}
    if not isinstance(ex, dict):
        return []

    # D2. The whole document is validated BEFORE anything is emitted, so a refusal is
    # all-or-nothing: a document with one malformed numeric field contributes no observation
    # at all, never a partial set. This is the backstop for rows stored before the extraction
    # boundary guard existed or written by any other route; a document uploaded today is
    # refused earlier, in extract_many, before a row exists.
    validate_numeric_fields(doc_type, ex, filename=str(doc.get("filename") or "") or None)

    sha = str(doc.get("sha256") or "")
    base = {
        "doc_type": doc_type,
        "sha256": sha,
        "document_id": doc.get("document_id"),
        "revision_of": doc.get("supersedes") or None,
        "rank": _doc_rank(doc_type),
        "entity_key": "",
        "entity_state": None,
    }
    as_of_key = _AS_OF_KEYS.get(doc_type)
    as_of = _parse_as_of(ex.get(as_of_key)) if as_of_key else None
    if as_of is None and "document_date" in ex:
        as_of = _parse_as_of(ex.get("document_date"))

    out: list[dict] = []

    def emit(field: str, value: Any, *, kind: str | None = None,
             entity_key: str = "", entity_state: str | None = None) -> None:
        declared = FIELD_KINDS.get(field)
        if declared is None:
            raise ValueError(f"field {field!r} has no kind declared in field_registry")
        out.append({**base, "field": field, "value": value,
                    "kind": kind or declared, "tier": writer_tier(field, doc_type),
                    "as_of": as_of, "entity_key": entity_key, "entity_state": entity_state})

    # Doc risk: refuse out-of-range before anything from this document is emitted.
    if doc_type in DOC_RISK_DOC_TYPES:
        validate_doc_risk_score(ex.get("document_risk_score"))
        risk = _coerce_numeric(ex.get("document_risk_score"))
        if risk is not None:
            emit("docRiskScore", risk)

    for src, field in _NUMERIC_EMISSIONS.get(doc_type, ()):
        v = _coerce_numeric(ex.get(src))
        if v is not None:
            emit(field, v)
    for src, field in _DATESTR_EMISSIONS.get(doc_type, ()):
        v = ex.get(src)
        if not _is_blank_date(v):
            emit(field, str(v))

    if doc_type == "change_order":
        # The executed amendment. Effective values win by declared tier; the ORIGINAL
        # baseline persists as contract_value's PERMANENT observations.
        if _coerce_numeric(ex.get("revised_contract_sum")) is not None:
            emit("bac", _coerce_numeric(ex.get("revised_contract_sum")))
            emit("revisedContractSum", _coerce_numeric(ex.get("revised_contract_sum")))
        if _coerce_numeric(ex.get("baseline_contract_sum")) is not None:
            emit("baselineContractSum", _coerce_numeric(ex.get("baseline_contract_sum")))
        new_end = ex.get("revised_completion_date")
        if not _is_blank_date(new_end):
            # Through the same emission path as every other field. The direct dictionary
            # write that bypassed set_field is gone with the fold.
            emit("baselineEnd", str(new_end))
        # The event ledger row: one executed change order. Entity identity is the document
        # (no CO number is extracted); a revision carries revision_of and supersedes THIS
        # record, never the population. Arrives executed — approval happens off-platform.
        explicit = _coerce_numeric(ex.get("change_order_count"))
        if explicit is not None:
            # A stated ledger total. SNAPSHOT-kind observation on an EVENT field: selection
            # lets a stated total beat counting, reproducing the legacy setField semantics.
            emit("changeOrderCount", explicit, kind=SNAPSHOT)
        else:
            emit("changeOrderCount", 1, kind=EVENT,
                 entity_key=str(doc.get("document_id") or sha), entity_state="executed")

    elif doc_type == "safety_report":
        incident_rate = _coerce_numeric(ex.get("incident_rate"))
        if (
            incident_rate is None
            and _coerce_numeric(ex.get("osha_recordable_incidents")) is not None
            and _coerce_numeric(ex.get("total_manhours")) is not None
        ):
            mh = _coerce_numeric(ex.get("total_manhours"))
            if mh:
                incident_rate = _round3(
                    (_coerce_numeric(ex.get("osha_recordable_incidents")) / mh) * 200000)
        if incident_rate is not None:
            emit("oshaIncidentRate", incident_rate)
        if _coerce_numeric(ex.get("total_manhours")) is not None:
            emit("totalManhours", _coerce_numeric(ex.get("total_manhours")))

    elif doc_type == "subcontractor_report":
        comp = _coerce_numeric(ex.get("compliance_score"))
        if (
            comp is None
            and _coerce_numeric(ex.get("on_time_deliveries")) is not None
            and _coerce_numeric(ex.get("scheduled_deliveries")) is not None
            and _coerce_numeric(ex.get("scheduled_deliveries")) != 0
        ):
            comp = _round3(_coerce_numeric(ex.get("on_time_deliveries"))
                           / _coerce_numeric(ex.get("scheduled_deliveries")))
        if comp is not None:
            emit("subcontractorComplianceScore", comp)

    return out


# --------------------------------------------------------------------------- selection


def _snap_pick(group: list[dict]) -> dict:
    """SNAPSHOT winner: lowest tier; within it, dated beats undated, latest as_of wins;
    remaining ties resolve by the historical (rank, doc_type, sha256) last-write order."""
    return max(group, key=lambda o: (
        -int(o.get("tier") or 0),
        1 if o.get("as_of") is not None else 0,
        o.get("as_of") or date.min,
        int(o.get("rank") or 0), str(o.get("doc_type") or ""), str(o.get("sha256") or ""),
    ))


def _perm_pick(group: list[dict]) -> dict:
    """PERMANENT winner: lowest tier; within it the EARLIEST dated observation, and nothing
    later ever replaces it. Undated observations lose to dated ones; wholly undated ties
    resolve by the historical first-non-null order (min rank/doc_type/sha)."""
    return min(group, key=lambda o: (
        int(o.get("tier") or 0),
        o.get("as_of") or date.max,
        int(o.get("rank") or 0), str(o.get("doc_type") or ""), str(o.get("sha256") or ""),
    ))


def select_signal_inputs(observations: list[dict], cutoff: date | None = None) -> dict:
    """The flat ``signalInputs`` dict, selected from observations at a cutoff. Pure.

    Every selection is ``as_of <= cutoff`` (undated observations pass — refusing them would
    silently blank most fields; D3 remains the open item it was). Recomputing an earlier
    period with its stored cutoff therefore reproduces it even after later-dated evidence
    arrives.
    """
    eligible = [
        o for o in observations
        if cutoff is None or o.get("as_of") is None or o["as_of"] <= cutoff
    ]

    by_field: dict[str, list[dict]] = {}
    for o in eligible:
        by_field.setdefault(str(o["field"]), []).append(o)

    si: dict[str, Any] = {k: None for k in _KEY_ORDER}
    sources: dict[str, dict] = {}

    for field in _KEY_ORDER:
        group = by_field.get(field)
        if not group:
            continue
        kind = FIELD_KINDS.get(field)
        if kind == PERMANENT:
            w = _perm_pick(group)
            si[field] = w["value"]
            sources[field] = {"docType": w["doc_type"], "value": w["value"]}
        elif kind == EVENT:
            snaps = [o for o in group if o.get("kind") != EVENT]
            events = [o for o in group if o.get("kind") == EVENT]
            need = NEEDS.get(field) or {}
            states = need.get("states")
            if states:
                events = [o for o in events if o.get("entity_state") in states]
            if snaps:
                # A stated total beats counting, as the legacy setField did.
                w = _snap_pick(snaps)
                si[field] = w["value"]
                sources[field] = {"docType": w["doc_type"], "value": w["value"]}
            elif events:
                # Latest non-superseded record per entity IS that entity's record; the
                # aggregate is over entities, so a revision never becomes a second event.
                latest: dict[str, dict] = {}
                for o in sorted(events, key=lambda o: (
                        o.get("as_of") or date.min, str(o.get("sha256") or ""))):
                    latest[str(o.get("entity_key") or "")] = o
                si[field] = len(latest)
                # Deliberately NO sources entry for a counted ledger, matching the legacy
                # additive branches that bypassed setField (models_dq weighting unchanged).
        elif kind == DELTA:
            # Summed within the period, never across, never mixed with a SNAPSHOT of the
            # same quantity. No field declares DELTA today; kept so the declaration is real.
            si[field] = sum(o["value"] for o in group
                            if isinstance(o["value"], (int, float)))
        else:  # SNAPSHOT
            w = _snap_pick(group)
            si[field] = w["value"]
            sources[field] = {"docType": w["doc_type"], "value": w["value"]}

    # docDate is DERIVED: the latest as_of among the period's eligible observations — the
    # same rule `_derive_cutoff` applies to the document set, so "as of when" has one answer.
    dated = [o for o in eligible if o.get("as_of") is not None]
    if dated:
        w = max(dated, key=lambda o: (o["as_of"], int(o.get("rank") or 0),
                                      str(o.get("doc_type") or ""), str(o.get("sha256") or "")))
        si["docDate"] = w["as_of"].isoformat()
        sources["docDate"] = {"docType": w["doc_type"], "value": si["docDate"]}

    # ---- derived indices, .gs 1065-1070, unchanged: several modules read si["cpi"].
    cpi = None
    spi = None
    if si["ev"] is not None and si["ac"] is not None and si["ac"] != 0:
        cpi = _round3(si["ev"] / si["ac"])
    if si["ev"] is not None and si["pv"] is not None and si["pv"] != 0:
        spi = _round3(si["ev"] / si["pv"])
    if (
        spi is None
        and si["actualPctComplete"] is not None
        and si["plannedPctComplete"] is not None
        and si["plannedPctComplete"] != 0
    ):
        spi = _round3(si["actualPctComplete"] / si["plannedPctComplete"])

    # ---- Final assembly in FIXED key order. Do not sort, do not reorder: the simulation
    # ---- layer iterates insertion order. sources is rebuilt in key order too, so it is a
    # ---- pure function of the observation set rather than of fold sequence.
    out: dict[str, Any] = {}
    for k in _KEY_ORDER:
        out[k] = si[k]
    out["sources"] = {k: sources[k] for k in _KEY_ORDER if k in sources}
    out["cpi"] = cpi
    out["spi"] = spi
    return out


# --------------------------------------------------------------------------- public API


def assemble_signal_inputs(documents: list[dict], cutoff: date | None = None) -> dict:
    """Assemble ``signalInputs`` from a set of stored per-document extractions.

    ``documents`` items are ``{"sha256", "doc_type", "filename", "extraction"}``.
    Pure: no clock, no I/O. Deterministic, order independent, idempotent — the same three
    properties the fold guaranteed, now via emission + selection. ``cutoff`` bounds every
    selection at ``as_of <= cutoff``; None means no bound (the historical behaviour).

    Unmapped doc types contribute nothing (see ``assembly_report`` to surface them).
    """
    observations: list[dict] = []
    for d in _ordered_docs(documents):
        observations.extend(emit_observations(d))
    return select_signal_inputs(observations, cutoff)


def assembly_report(documents: list[dict]) -> dict:
    """Explain which documents contributed which signalInput fields, and which did not.

    The upload response uses this to tell the PM, explicitly, that a document they
    uploaded changed nothing — the single most common source of "why is my dashboard
    still grey?" confusion. Same de-duplication rules as ``assemble_signal_inputs``, so the
    two views can never disagree. ``fields`` per document are the fields the document EMITS
    observations for — what it brings to selection, whether or not it wins each field.

    Returns ``{"contributed": [...], "unmapped": [...], "fields_by_doc": {sha256: [...]}}``.
    A mapped document that produced no fields (extraction all nulls) appears in
    ``contributed`` with an empty field list — it IS a recognised type, it just carried
    no usable values, which is a different remedy for the PM than an unmapped type.
    """
    contributed: list[dict] = []
    unmapped: list[dict] = []
    fields_by_doc: dict[str, list[str]] = {}

    for d in _ordered_docs(documents):
        sha = str(d.get("sha256") or "")
        doc_type = canonical_doc_type(str(d.get("doc_type") or ""))
        filename = str(d.get("filename") or "")
        if not doc_type or doc_type == UNMAPPED or not is_mapped(doc_type):
            unmapped.append({"sha256": sha, "doc_type": doc_type or UNMAPPED,
                             "filename": filename, "reason": "doc_type has no merge branch"})
            fields_by_doc[sha] = []
            continue
        ex = d.get("extraction") or {}
        if not isinstance(ex, dict):
            unmapped.append({"sha256": sha, "doc_type": doc_type, "filename": filename,
                             "reason": "extraction payload is not an object"})
            fields_by_doc[sha] = []
            continue
        emitted = emit_observations(d)
        seen: set[str] = set()
        fields = [o["field"] for o in emitted
                  if not (o["field"] in seen or seen.add(o["field"]))]
        fields_by_doc[sha] = fields
        contributed.append({"sha256": sha, "doc_type": doc_type, "filename": filename,
                            "fields": fields})

    return {"contributed": contributed, "unmapped": unmapped, "fields_by_doc": fields_by_doc}


# --------------------------------------------------------------------------- self-check

if __name__ == "__main__":
    import random

    def doc(sha, dt, ex):
        return {"sha256": sha, "doc_type": dt, "filename": sha + ".pdf", "extraction": ex}

    base = [
        doc("aaa", "contract_value", {"original_contract_sum": "$10,000,000",
                                      "project_start_date": "2024-01-01",
                                      "project_end_date": "2025-12-31"}),
        doc("bbb", "schedule_of_values", {"completed_to_date": 4000000,
                                          "scheduled_value_total": 9500000,
                                          "period_to_date": "2024-09-30"}),
        doc("ccc", "pay_application", {"amount_paid_to_date": 4400000,
                                       "percent_complete_verified": 40}),
        doc("ddd", "rfi_log", {"rfi_total": 3, "rfi_open": 2, "log_date": "2024-09-15"}),
        doc("fff", "change_order", {"revised_contract_sum": 10400000,
                                    "revised_completion_date": "2026-03-31",
                                    "change_order_date": "2024-06-01"}),
        doc("ggg", "change_order", {"revised_contract_sum": 10600000,
                                    "change_order_date": "2024-08-01"}),
    ]

    # 1. determinism
    assert assemble_signal_inputs(base) == assemble_signal_inputs(base)
    a = assemble_signal_inputs(base)
    assert list(a.keys()) == list(_KEY_ORDER) + ["sources", "cpi", "spi"], "key order drift"

    # 2. order independence (reversed AND randomly shuffled)
    assert assemble_signal_inputs(list(reversed(base))) == a
    for seed in range(25):
        shuffled = base[:]
        random.Random(seed).shuffle(shuffled)
        assert assemble_signal_inputs(shuffled) == a, f"order dependence at seed {seed}"
        assert list(assemble_signal_inputs(shuffled).keys()) == list(a.keys())

    # 3. idempotence vs the legacy double-count bug
    one = assemble_signal_inputs([base[4]])
    twice = assemble_signal_inputs([base[4], base[4]])
    assert one == twice, "same document twice must not double-count"
    assert one["changeOrderCount"] == 1

    # 4. the event ledger: two DISTINCT change orders are two events; a stated total wins
    assert a["changeOrderCount"] == 2, a["changeOrderCount"]
    stated = assemble_signal_inputs(
        base + [doc("hhh", "change_order", {"change_order_count": 7})])
    assert stated["changeOrderCount"] == 7, "a stated ledger total must beat counting"

    # 5. an unmapped doc_type contributes zero keys — including the individual rfi form,
    # which routes to unmapped (registers and logs only).
    blank = assemble_signal_inputs([])
    with_unmapped = assemble_signal_inputs(
        [doc("zzz", "wedding_invitation", {"document_risk_score": 0.99, "bac": 1}),
         doc("yyy", "rfi", {"document_risk_score": 0.5, "rfi_count": 3})]
    )
    assert with_unmapped == blank, "unmapped doc type leaked into signalInputs"
    assert with_unmapped["sources"] == {}
    rep = assembly_report([doc("zzz", "wedding_invitation", {"x": 1}), base[0]])
    assert [u["sha256"] for u in rep["unmapped"]] == ["zzz"]
    assert rep["fields_by_doc"]["zzz"] == []
    assert rep["fields_by_doc"]["aaa"] == ["bac", "baselineContractSum",
                                           "baselineStart", "baselineEnd"]
    assert assembly_report(list(reversed(base))) == assembly_report(base)

    # 6. quirks that the analytical layer depends on
    assert _num_or_null("N/A") == 0.0, "JS Number('') === 0 quirk lost"
    assert _num_or_null("$1,200,000.50") == 1200000.50
    assert _num_or_null("") is None and _num_or_null(None) is None
    zero_risk = assemble_signal_inputs([doc("q", "field_report", {"document_risk_score": 0})])
    assert zero_risk["docRiskScore"] == 0, "a genuine 0 must be STORED (sim treats it as absent)"
    assert (zero_risk["sources"] or {}).get("docRiskScore", {}).get("docType") == "field_report"
    # counted event ledgers deliberately write no source entry (legacy additive parity)
    assert "changeOrderCount" not in a["sources"]

    # 7. baseline preservation: the original survives the executed amendments, both readable
    assert a["bac"] == 10600000, a["bac"]                       # amended, latest by as_of
    assert a["baselineContractSum"] == 10000000.0, "original baseline must persist"
    assert a["revisedContractSum"] == 10600000
    assert a["baselineEnd"] == "2026-03-31", a["baselineEnd"]   # effective end: the amendment
    assert a["ev"] == 4000000 and a["ac"] == 4400000
    assert a["cpi"] == 0.909, a["cpi"]
    # recency by the value's own date, not by content hash: "fff" < "ggg" alphabetically,
    # but swap their dates and the earlier-hash CO wins on its later as_of.
    swapped = [dict(d) for d in base]
    swapped[4] = doc("fff", "change_order", {"revised_contract_sum": 10400000,
                                             "change_order_date": "2024-08-01"})
    swapped[5] = doc("ggg", "change_order", {"revised_contract_sum": 10600000,
                                             "change_order_date": "2024-06-01"})
    assert assemble_signal_inputs(swapped)["bac"] == 10400000, "as_of must decide, not sha"

    # 8. docDate is derived, one rule: the latest as_of in the evidence
    assert a["docDate"] == "2024-09-30", a["docDate"]

    # 9. the cutoff bounds every selection
    cut = assemble_signal_inputs(base, cutoff=date(2024, 7, 1))
    assert cut["bac"] == 10400000, "a post-cutoff amendment must not be selected"
    assert cut["docDate"] == "2024-06-01"

    print("extraction_merge self-check: OK")
