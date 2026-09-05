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

import json
from datetime import date
from typing import Any

from .extraction_fields import UNMAPPED, canonical_doc_type, is_mapped
from .field_registry import (
    DELTA, EVENT, FIELD_KINDS, IDENTITY_FIELDS, NEEDS, PERMANENT, RAW, SNAPSHOT,
    UNEMITTABLE_FIELDS, is_raw_field, raw_field_name, writer_tier,
)

__all__ = [
    "assemble_signal_inputs",
    "assembly_report",
    "document_ordering_key",
    "emit_observations",
    "select_signal_inputs",
    "unresolved_value_conflicts",
    "DOC_RISK_DOC_TYPES",
    "DOC_RISK_SCORE_MAX",
    "DOC_RISK_SCORE_MIN",
    "DocRiskScoreRangeError",
    "MalformedNumericError",
    "NumericRangeError",
    "RegisterRowCountError",
    "SIGNAL_INPUT_KEYS",
    "ratio_scaled_extraction_keys",
    "CPARS_RATING_SCALE",
    "ORDINAL_WORD_SCALES",
    "ordinal_scale_prompt_lines",
    "read_ordinal_word",
    "validate_doc_risk_score",
    "validate_numeric_fields",
    "validate_register_row_counts",
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
    # RUN 81. `oshaRecordableIncidents` was the ONE field in the whole registry that carried a
    # declared kind (field_registry SNAPSHOT), was emitted by a real branch of
    # `emit_observations` (Run 31 added it precisely so the count would stop being discarded)
    # and was STORED as observations -- and was then dropped again here, because
    # `select_signal_inputs` iterates `_KEY_ORDER` and this key was never added to it. The
    # observations existed in the database and never reached a module.
    #
    # WHAT IT COST, established by executing A6.2's assembly rather than reading it.
    # `models_cat89` reads `si.get("oshaRecordableIncidents")` as the NUMERATOR of the OSHA
    # identity (recordable cases * 200,000 / employee hours worked) and its own docstring
    # asserts "the corpus carries `oshaRecordableIncidents` (Run 31 stopped discarding it)".
    # It did not. The key resolved to None on every project ever computed, so
    # `recordable_cases` never appeared on the A6.2 structure, the canonical module could
    # never compute the identity from the two defining quantities, and the module was left
    # with the document-STATED rate that the same docstring says must never be used as the
    # incidence rate. Run 31's repair was undone by an omission one line long.
    #
    # APPENDED, NOT INSERTED. `select_signal_inputs` builds `signalInputs` in this order and
    # the comment at the assembly says the simulation layer iterates insertion order; adding
    # the key at the end leaves every existing key in the position it has always held.
    "oshaRecordableIncidents",
)

#: Public, stable view of the signalInputs key order (excluding "sources"/"cpi"/"spi").
SIGNAL_INPUT_KEYS: tuple[str, ...] = _KEY_ORDER


# --------------------------------------------------------------------------- ratio-scaled keys
#
# RUN 72. THE EXTRACTION KEYS WHOSE QUANTITY IS A SHARE OF ONE, NOT A PERCENTAGE OF A HUNDRED.
#
# WHY THIS EXISTS. `build_prompt` tells the model "Percentages as numbers 0-100." and says
# nothing else about scale. That sentence is true of `actualPctComplete`, `qualityAuditScore`
# and every other 0..100 quantity in the vocabulary, and it is FALSE of a compliance rate, which
# `BOUNDED_MAX_SI_FIELDS` bounds at 1.0. A document printing "Environmental compliance rate
# 1.000" therefore gives the model an instruction under which 100 is the compliant answer, and
# the numeric contract then refuses the whole document for exceeding its own bound. The document
# was right, the guard was right, and the instruction was wrong.
#
# WHY IT IS DERIVED AND NOT WRITTEN OUT. The bound is already declared once, per field, in
# `field_registry.BOUNDED_MAX_SI_FIELDS`, and the raw-key-to-field mapping is already declared
# once in `_NUMERIC_EMISSIONS`. A hand-written list of ratio fields in the prompt would be a
# second authority for the same fact, which is how a range statement drifts away from the range
# check that enforces it. Adding a field bounded at 1.0 to the registry now changes the prompt
# with it, and no one has to remember.
def ratio_scaled_extraction_keys() -> tuple[str, ...]:
    from .field_registry import BOUNDED_MAX_SI_FIELDS

    ratio_fields = {f for f, upper in BOUNDED_MAX_SI_FIELDS.items() if upper == 1.0}
    keys = {raw for pairs in _NUMERIC_EMISSIONS.values()
            for raw, field in pairs if field in ratio_fields}
    return tuple(sorted(keys))


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


class RegisterRowCountError(ValueError):
    """
    A register the model returned disagrees with the row count the SAME REPLY stated for it.

    RUN 126. WHAT THIS CATCHES THAT NOTHING ELSE COULD. An UNDER-READ register -- the model
    closes the JSON array early on its own -- is complete JSON, well-formed, in range, readable
    by every reader, and WRONG IN THE REASSURING DIRECTION: a 26-row inspection register read as
    eighteen rows produces a higher compliance rate and a calmer band, and leaves a stored row
    that looks whole to any later audit. `parse_json_response` cannot see it, the provider's
    stop_reason cannot see it, `describe_json_truncation` cannot see it and
    `validate_numeric_fields` cannot see it. Run 125 proved that and proved that comparing the
    register against a total the DOCUMENT states is unsound (absent on thirteen of eighteen real
    registers, a different population on four of the remaining five).

    WHY IT RAISES RATHER THAN REPORTING AN UNREADABLE FIELD. This is the `NumericRangeError`
    side of the split, not the `unreadable_fields` side, and for that class's own stated reason:
    the Run 80 override is about a field that CANNOT BE READ, where absence is honest and
    abstention follows. An under-read register can be read perfectly; it is simply a different,
    smaller population than the one the reply says it is returning. Carrying it on as "one bad
    field" would let the shortened register assemble and band. The whole document is refused
    before any `Document` row exists.
    """


def _row_count_of(value: Any) -> int | None:
    """
    The number of rows the model RETURNED, or None if this value is not a returned array.

    `len(the parsed array)`, PRE-READ, and that is deliberate. Every reader below drops rows it
    cannot use -- `documents._json_rows` drops a non-object row, `compliance_register`'s readers
    drop the same, and `trade_attribution` drops a row printing no `record_reference` and counts
    it in `rows_unusable`. Those drops are a REAL and REPORTED property of a register that was
    incomplete as authored, and comparing a post-drop count against the model's stated count
    would refuse documents for a fault the platform already reports honestly elsewhere. What is
    compared here is what the model handed over, nothing later.

    A JSON STRING OF AN ARRAY IS ACCEPTED, because `documents._json_rows` accepts one and so a
    register arriving in that shape is a register that assembles.
    """
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return None
    return len(value) if isinstance(value, list) else None


def validate_register_row_counts(extraction: Any, *, filename: str | None = None) -> None:
    """
    Refuse a reply whose register does not hold the number of rows the same reply states for it.
    Returns None, or raises `RegisterRowCountError`.

    THREE FAULTS, ALL REFUSED, AND THE SYMMETRY IS DELIBERATE:

      SHORT -- stated 26, returned 18. The failure this instrument exists for.

      LONG -- stated 18, returned 26. Refused too, and refused for a reason rather than for
      symmetry's sake: one of the two numbers is wrong and this reply does not say which, so
      accepting the array would be choosing. Accepting the longer array would also make the
      contract one-sided, and a one-sided contract is satisfiable by stating a low count and
      returning whatever was produced -- which is the check that cannot fail, again.

      MISSING -- an array returned with no count stated for it. Refused, because this is exactly
      the shape an ignored instruction takes, and a register that carries no count is a register
      with no defence at all. The prompt asks for the count on EVERY register returned,
      including an empty one, so a compliant reply never reaches this branch.

    NOT COUNTED, AND THE ABSENCE IS NOT A FAULT: a register returned as null (the document has
    no such table) needs no count and is skipped; the eight fields in
    `extraction_fields.UNCOUNTED_REGISTERS` are never looked at, and the six override tables
    among them MUST NOT BE, because there `[]` and absent are different claims. A count stated
    for a register that is not counted, or for a field the type never asked for, is ignored --
    it decides nothing, and refusing on it would refuse a reply that volunteered more than it
    was asked for.
    """
    from .extraction_fields import COUNTED_REGISTERS, REGISTER_ROW_COUNT_FIELD

    ex = extraction if isinstance(extraction, dict) else {}
    stated_raw = ex.get(REGISTER_ROW_COUNT_FIELD)
    if isinstance(stated_raw, str):
        try:
            stated_raw = json.loads(stated_raw)
        except (ValueError, TypeError):
            stated_raw = None
    stated = stated_raw if isinstance(stated_raw, dict) else {}
    where = f" in {filename}" if filename else ""

    for register in sorted(COUNTED_REGISTERS):
        returned = _row_count_of(ex.get(register)) if register in ex else None
        has_count = register in stated
        if returned is None and not has_count:
            continue
        if returned is None:
            # A count stated for a register no array was returned for. Zero is the one honest
            # reading of "no rows returned", so a stated zero agrees and passes; any other
            # number is a reply claiming rows it did not hand over.
            n = _stated_count(stated.get(register))
            if n in (None, 0):
                continue
            raise RegisterRowCountError(
                f"the extraction{where} states that {register} holds {n} "
                f"{'row' if n == 1 else 'rows'}, but the answer returned no rows for it at all. "
                f"The reply contradicts itself, so the register cannot be trusted to be "
                f"complete. Nothing was stored for this document and no figures from it were "
                f"used. Re-run the extraction."
            )
        if not has_count:
            raise RegisterRowCountError(
                f"the extraction{where} returned {returned} "
                f"{'row' if returned == 1 else 'rows'} for {register} but stated no row count "
                f"for it, so there is no way to tell whether the register is complete. Nothing "
                f"was stored for this document and no figures from it were used. Re-run the "
                f"extraction."
            )
        n = _stated_count(stated.get(register))
        if n is None:
            raise RegisterRowCountError(
                f"the extraction{where} states the row count of {register} as "
                f"{stated.get(register)!r}, which is not a whole number of rows. Nothing was "
                f"stored for this document and no figures from it were used. Re-run the "
                f"extraction."
            )
        if n != returned:
            shortfall = ("stopped short of" if returned < n else "went beyond")
            raise RegisterRowCountError(
                f"the extraction{where} states that {register} holds {n} "
                f"{'row' if n == 1 else 'rows'}, but the answer returned {returned}: it "
                f"{shortfall} the register it said it was returning. A register that is not the "
                f"size the reply claims cannot be read as the whole population, and the figures "
                f"drawn from it would be measured against the wrong number of rows. Nothing was "
                f"stored for this document and no figures from it were used. Re-run the "
                f"extraction."
            )


def _stated_count(v: Any) -> int | None:
    """A stated count as a whole non-negative number of rows, or None if it is not one.
    `True` is not 1 here: a boolean is not a count and reading it as one would let a reply
    state `true` and pass a one-row register."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, int):
        return v if v >= 0 else None
    if isinstance(v, float):
        return int(v) if v.is_integer() and v >= 0 else None
    if isinstance(v, str):
        t = v.strip()
        if t.isdigit():
            return int(t)
    return None


# --------------------------------------------------------------- ordinal word scales
#
# RUN 80, FIX TWO. CPARS PRINTS WORDS AND THE PLATFORM REQUIRED NUMBERS.
#
# A past performance evaluation (CPARS) states its ratings as adjectives, not as figures. The
# four rating keys are declared numeric in `_NUMERIC_EMISSIONS` because A6.4
# (`run_contractor_performance`, models_doc.py) reads them as numbers on a five-point scale and
# refuses anything outside 0..5. So the document arrived stating exactly what it is required by
# regulation to state, and the platform could not read a word of it.
#
# OWNER RULING (Run 80 order, section 3): accept the word ratings, under the standard CPARS
# scale. The mapping is stated ONCE, here, and is also printed for a human in
# `specifications/A6_delivery_quality.md`, which is generated from THIS dictionary by
# `ordinal_scale_prompt_lines` rather than transcribed beside it.
#
# NOTHING IS INVENTED BEYOND THE FIVE NAMED WORDS. The scale is the published CPARS scale and
# the five adjectives are its five levels, mapped onto the five-point scale A6.4 already
# enforces. A word that is NOT one of the five is NOT coerced: `read_ordinal_word` hands it back
# untouched, `_parse_numeric` calls it malformed, and the field is dropped as unreadable with a
# sentence saying the rating was not recognised. Guessing at "Above Average" would be inventing
# a level the evaluation does not have, which is precisely what standing rule 4 forbids.
CPARS_RATING_SCALE: dict[str, float] = {
    "exceptional": 5.0,
    "very good": 4.0,
    "satisfactory": 3.0,
    "marginal": 2.0,
    "unsatisfactory": 1.0,
}

# Which extraction keys are read on which word scale. Keyed by the RAW extraction key, so the
# validation boundary and the emission boundary both consult the same map with the same key --
# they are the two call sites of `read_ordinal_word` and there is no third.
ORDINAL_WORD_SCALES: dict[str, dict[str, float]] = {
    "overall_rating": CPARS_RATING_SCALE,
    "schedule_rating": CPARS_RATING_SCALE,
    "cost_rating": CPARS_RATING_SCALE,
    "quality_rating": CPARS_RATING_SCALE,
}


def read_ordinal_word(src_key: str, v: Any) -> Any:
    """
    The value with a recognised rating word replaced by its number; otherwise `v` unchanged.

    Unchanged is the important half. A word outside the scale leaves here exactly as it
    arrived, so the numeric contract sees it, calls it unreadable, and the field is recorded
    as not recognised rather than quietly turned into a figure.
    """
    scale = ORDINAL_WORD_SCALES.get(src_key)
    if scale is None or not isinstance(v, str):
        return v
    return scale.get(" ".join(v.strip().lower().split()), v)


def ordinal_scale_prompt_lines() -> tuple[str, ...]:
    """One human-readable line per word scale, derived from the mapping itself. Used to state
    the scale in the specification prose so the two cannot drift."""
    out: list[str] = []
    for key in sorted(ORDINAL_WORD_SCALES):
        scale = ORDINAL_WORD_SCALES[key]
        pairs = ", ".join(f"{w.title()} = {_fmt_num(n)}"
                          for w, n in sorted(scale.items(), key=lambda kv: -kv[1]))
        out.append(f"{key}: {pairs}")
    return tuple(out)


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
    and that is now REACHABLE and is the mechanism: since Run 80 an unreadable field is
    reported by `validate_numeric_fields` rather than refusing the document, and this None is
    what makes it absent instead of stored."""
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
    # RUN 80, FIX THREE. The numeric figures of the three A3 structures. They are NOT in
    # `_NUMERIC_EMISSIONS` because none of them is a signal-input field: each is read straight
    # off the extraction by an assembler in `documents.py` into a governed structure. They are
    # declared HERE so the numeric contract still sees them -- a negative index level or a
    # negative adjustment factor is refused at the boundary rather than reaching a structure --
    # which is exactly what `_EXTRA_NUMERIC_KEYS` exists for.
    "historical_data": (("analogous_adjustment_factor", None),
                        ("cost_index_base_value", None),
                        ("cost_index_current_value", None),
                        ("cost_index_cost_exposure", None),
                        ("reference_class_governed_percentile", None)),
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
    from .field_registry import BOUNDED_MAX_SI_FIELDS, SIGNED_SI_FIELDS
    if si_field == "docRiskScore":
        return
    if (si_field is None or si_field not in SIGNED_SI_FIELDS) and n < 0:
        where = f" in {filename}" if filename else ""
        raise NumericRangeError(
            f"{src}{where} is {_fmt_num(n)}, and this field cannot be negative. Nothing was "
            f"stored for this document and no figures from it were used. Check the document, "
            f"or re-run the extraction."
        )
    # RUN 14. The other end of the same contract. Refused, never clamped: clamping ten thousand
    # per cent complete to one hundred manufactures a finished project out of a typing mistake,
    # and the repair would be in the reassuring direction, which is the one nothing downstream
    # can trace. Only fields whose own definition supplies a ceiling are bounded here.
    upper = BOUNDED_MAX_SI_FIELDS.get(si_field or "")
    if upper is not None and n > upper:
        where = f" in {filename}" if filename else ""
        raise NumericRangeError(
            f"{src}{where} is {_fmt_num(n)}, and this field cannot be above {_fmt_num(upper)}. "
            f"Nothing was stored for this document and no figures from it were used. Check the "
            f"document, or re-run the extraction."
        )


def _fmt_num(n: float | int) -> str:
    return str(int(n)) if isinstance(n, float) and n.is_integer() else str(n)


def validate_numeric_fields(doc_type: str, extraction: Any, *,
                            filename: str | None = None) -> list[dict]:
    """
    Check every numeric field this document type declares. Returns the list of fields that
    could not be read (possibly empty); raises NumericRangeError for a value that reads as a
    number but sits outside the field's permitted range.

    RUN 80, FIX TWO, ITEM 3. WHAT CHANGED AND WHAT DID NOT.

    This function used to raise MalformedNumericError for an unreadable field, and its contract
    said so in these words: "Called at EVERY entry point, before anything from the document is
    stored or emitted, so the refusal is whole-document by construction: no observation row, no
    Document row, no partial write." That was a deliberate design ruling and it is the ruling
    the owner has overridden (Run 80 order, section 3, item 3): "A document must not be
    discarded whole because one field fails ... a field that cannot be read is absent, and the
    rest of the document still contributes."

    So UNREADABLE is now FIELD-LEVEL. The field is reported here and is never emitted --
    `_coerce_numeric` already returns None for a value `_parse_numeric` calls malformed, so the
    field is absent at the emission boundary exactly as an omitted field is, and absence has
    always meant abstention. No coerced zero can appear: nothing is substituted anywhere on
    this path.

    OUT OF RANGE STILL REFUSES THE WHOLE DOCUMENT, and deliberately. Run 14's ruling is about a
    value that IS a number and is wrong -- ten thousand per cent complete, a negative count --
    where "the repair would be in the reassuring direction, which is the one nothing downstream
    can trace". A readable but impossible figure is evidence that the document or the reading of
    it is wrong in a way that is not confined to one field. The owner ruled on the field that
    "cannot be read"; he did not rule on the field that reads as an impossible number, and this
    run does not decide that for him.

    Absent values (None, "") pass, unchanged.
    """
    doc_type = canonical_doc_type(str(doc_type or ""))
    ex = extraction if isinstance(extraction, dict) else {}
    unreadable: list[dict] = []
    for src, si_field in _numeric_keys_for(doc_type):
        raw = read_ordinal_word(src, ex.get(src))
        status, n = _parse_numeric(raw)
        if status == "absent":
            continue
        if status == "malformed":
            where = f" in {filename}" if filename else ""
            if src in ORDINAL_WORD_SCALES:
                # THE UNRECOGNISED RATING. Said in its own words, because "cannot be read as a
                # number" would be misleading about a field that is not supposed to be a number.
                words = ", ".join(w.title() for w, _ in
                                  sorted(ORDINAL_WORD_SCALES[src].items(), key=lambda kv: -kv[1]))
                reason = (f"{src}{where} is {ex.get(src)!r}, which is not a rating on the scale "
                          f"this evaluation uses ({words}). The rating was not recognised, so "
                          f"this field is treated as absent and no figure is used in its place. "
                          f"The rest of the document still contributes.")
            else:
                reason = (f"{src}{where} is {raw!r}, which cannot be read as a number. This "
                          f"field is treated as absent and no figure is used in its place; the "
                          f"rest of the document still contributes. If the document does not "
                          f"state this value, the extraction should leave it blank rather than "
                          f"write {raw!r}.")
            unreadable.append({"field": src, "si_field": si_field,
                               "value": ex.get(src), "reason": reason})
            continue
        _range_check(si_field, n, src, filename)
    return unreadable


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
    from .field_registry import BOUNDED_MAX_SI_FIELDS, SIGNED_SI_FIELDS
    if field not in SIGNED_SI_FIELDS and n < 0:
        raise NumericRangeError(
            f"{field} cannot be set to {_fmt_num(n)}: this field cannot be negative. "
            f"Nothing was changed."
        )
    # RUN 14. The same upper domain as the document boundary, on the legacy direct-write path,
    # so the two entry points cannot disagree about what the field may hold.
    upper = BOUNDED_MAX_SI_FIELDS.get(field)
    if upper is not None and n > upper:
        raise NumericRangeError(
            f"{field} cannot be set to {_fmt_num(n)}: this field cannot be above "
            f"{_fmt_num(upper)}. Nothing was changed."
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
        # RUN 132. NO ``ac`` EMISSION. ``amount_paid_to_date`` is the sum RELEASED to the
        # contractor -- completed-to-date LESS RETAINAGE (ten per cent on the corpus). It is
        # not what the work cost, and the difference is not noise: on PRJ-002 period 1 it
        # made CPI read 1.111 (under cost) where the stated actual cost gives 0.955 (over).
        # The error is one-directional and reassuring, which is the direction nothing
        # downstream can catch. Nothing on a G702 is an actual cost: completed_to_date is
        # earned value, amount_paid_to_date is earned value net of retention, and adding the
        # retention back would compute a figure no document states. So the pay application
        # does not write ``ac`` AT ALL -- not even as a fallback. A period with no document
        # stating actual cost now has no ``ac`` and the EVM modules ABSTAIN, which is the
        # visible answer; a ten-per-cent-optimistic CPI is the invisible one.
        ("percent_complete_verified", "actualPctComplete"),
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
        # RUN 78. The cost report is the document that accounts for contingency; see the note
        # beside `cost_report` in `extraction_fields._EXTRACTION_FIELDS`.
        ("original_contingency", "originalContingency"),
        ("remaining_contingency", "remainingContingency"),
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


def document_as_of(doc_type: str, extraction: Any) -> date | None:
    """
    The date this document speaks about, by the same rule `emit_observations` uses for an
    observation's `as_of`: the document type's own date field, falling back to
    `document_date`, and None when neither parses.

    Public because filing needs it too — a document is filed into a dated folder of the Arora
    tree, and that folder must be named for the date the DOCUMENT carries, never the upload
    clock. Exposed here rather than reimplemented in the filing step so the two can never
    disagree about what a document's date is.
    """
    doc_type = canonical_doc_type(str(doc_type or ""))
    ex = extraction if isinstance(extraction, dict) else {}
    key = _AS_OF_KEYS.get(doc_type)
    as_of = _parse_as_of(ex.get(key)) if key else None
    if as_of is None and "document_date" in ex:
        as_of = _parse_as_of(ex.get("document_date"))
    return as_of


def document_ordering_key(doc: dict) -> tuple:
    """
    THE BUSINESS-KEY ORDER FOR A SET OF DOCUMENTS. Ascending, so the MOST AUTHORITATIVE
    document sorts LAST and a last-writer-wins consumer takes it.

    RUN 135, M4. `documents._period_documents` returned its rows in whatever order the database
    happened to hand back -- the query carried no `ORDER BY` -- and four Run-69 structures walk
    that list writing last-writer-wins. Two `oac_minutes` differing only in UPLOAD ORDER
    therefore produced a different `disputeRecord` and, worse, a different `as_of_day`, which is
    A4.7's duration input. `documents.py`'s own header promises byte-identical `signalInputs`
    for the same evidence; an undefined list order cannot keep that promise.

    The key is the one the owner's order names, in that sequence:

      1. WRITER TIER, as the document-level `_doc_rank` already declares it -- baseline first,
         ordinary next, revision last, so a revision beats what it revises.
      2. DATED OVER UNDATED. An undated document must never displace a dated one, so undated
         sorts FIRST and loses.
      3. `as_of`, by `document_as_of` -- the same date rule emission uses, so "which document is
         later" has ONE answer on this platform.
      4. DOCUMENT TYPE, lexical, a declared and readable key.
      5. sha256, AND ONLY HERE. Under ruling R3 a content hash may STABILISE an order and may
         never SELECT a value. Two documents that reach this position are identical on every
         business key above, and the hash decides only which of them is written second. Where
         two such documents state DIFFERENT values for one field, that disagreement is reported
         rather than settled silently -- see `unresolved_value_conflicts` below.
    """
    doc_type = str(doc.get("doc_type") or "")
    as_of = document_as_of(doc_type, doc.get("extraction"))
    return (
        _doc_rank(doc_type),
        1 if as_of is not None else 0,
        as_of or date.min,
        doc_type,
        str(doc.get("sha256") or ""),
    )


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
        # RUN 80. `read_ordinal_word` is the SECOND and LAST call site of the word scale; the
        # first is `validate_numeric_fields`. Both consult the same map with the same raw key,
        # so a rating this boundary would emit is exactly a rating that boundary accepted, and
        # a word neither of them recognises is malformed at both -- `_coerce_numeric` returns
        # None for it, so the field is simply not emitted.
        v = _coerce_numeric(read_ordinal_word(src, ex.get(src)))
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
        # RUN 31. THE RECORDABLE-CASE COUNT IS NOW EMITTED, and it was not before: the tier map
        # above sends `osha_recordable_incidents` to None, so the NUMERATOR of the OSHA identity
        # never reached signal inputs while the derived rate and the denominator both did.
        #
        # WHY THAT MATTERED, found by EXECUTING this branch rather than reading it. When the
        # extractor supplies `incident_rate` directly, it is emitted AS-IS and is never checked
        # against the identity: a document stating 99.9 alongside a recorded 3-cases/200,000-hours
        # pair emits 99.9. A downstream consumer reading `oshaIncidentRate` therefore cannot tell
        # a rate this platform DERIVED from the identity from a rate a document ASSERTED.
        #
        # Emitting the count lets the canonical Safety Performance module compute
        # RecordableCases * 200000 / EmployeeHoursWorked itself, from the two defining
        # quantities, and treat a document-stated rate as a document-stated rate rather than as
        # an exposure-normalised measurement. Nothing is fabricated here and no rate is changed;
        # one already-extracted field stops being discarded.
        if _coerce_numeric(ex.get("osha_recordable_incidents")) is not None:
            emit("oshaRecordableIncidents",
                 _coerce_numeric(ex.get("osha_recordable_incidents")))

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

    # ------------------------------------------------------- RUN 110, SECTION 2.1: EVIDENCE
    #
    # EVERY EXTRACTED VALUE BECOMES EVIDENCE, INCLUDING THE ONES NO REGISTRY DECLARES.
    #
    # Everything above this line is the DECLARED vocabulary: a fixed map from a document type's
    # key to a `signalInputs` field, gated a second time by `field_registry.FIELD_KINDS`. A
    # value the model extracted and the document stated, for which no such mapping exists, was
    # simply dropped -- not refused, not reported, dropped. Run 110 measured seventy-four such
    # (document type, key) pairs on a twenty-one document fixture, among them the six weather
    # fields Run 107 added to `oac_minutes` for A4.5 and the four rating fields it added to
    # `subcontractor_report` for A4.8. Both sets reached `documents.extraction` and stopped.
    #
    # From here every key in the extraction is ALSO emitted verbatim, as a RAW row carrying the
    # four things the owner's ruling names: WHICH DOCUMENT (document_id, sha256, doc_type),
    # WHICH PERIOD (the caller's, at persistence), WHAT THE DOCUMENT CALLED IT (the label, kept
    # exactly as extracted) and THE VALUE (untouched -- not coerced, not rounded, not renamed).
    #
    # IT IS ADDITIVE AND IT CHANGES NO READING. A RAW row's field name is
    # `evidence:<doc_type>:<label>`, which contains a colon and therefore cannot equal any name
    # in `field_registry.ALL_SI_FIELDS`; `select_signal_inputs` iterates `_KEY_ORDER` and so
    # cannot select one. Every declared emission above is untouched, and a key that WAS consumed
    # above is deliberately still transcribed here rather than skipped: "what the document said"
    # and "what the platform made of it" are two different records, and keeping the first
    # complete is what makes the second checkable.
    #
    # WHAT IT IS NOT. It is not a matching layer and it does not serve a module. Nothing here
    # decides that `weather_days_approved` is the quantity A4.5 asks for. That recognition is
    # the model-driven step of the owner's ruling, and it is NOT built: there is no model key in
    # this environment. This is the evidence the step would read, and nothing more.
    for label in sorted(ex):
        if is_raw_field(str(label)):
            continue          # cannot happen from an extraction; refuses a doubly-prefixed name
        out.append({**base, "field": raw_field_name(doc_type, str(label)),
                    "value": ex[label], "kind": RAW, "tier": None, "as_of": as_of,
                    "entity_key": "", "entity_state": None})

    return out


# --------------------------------------------------------------------------- selection


# RUN 135, H3 + M4, UNDER RULING R3: SHA-256 STABILISES AN ORDER AND NEVER SELECTS A VALUE.
#
# `_snap_pick` and `_perm_pick` are UNCHANGED IN WHAT THEY RETURN. Every business key they ever
# used is used in the same sequence and the same direction; sha256 remains the final element and
# still decides the same ties it decided before. What changes is that THE CONDITION IN WHICH
# SHA-256 DECIDES IS NOW A NAMED, ENUMERABLE THING rather than an accident of a comparison
# tuple: `_snap_business_key` and `_perm_business_key` are the keys WITHOUT the hash, and the
# set of observations sharing the winning business key is the tie set the hash then breaks.
#
# That factoring is what makes `unresolved_value_conflicts` below possible, and it is the whole
# of the fix. R3 does not forbid the hash from breaking a tie -- it forbids the hash from
# QUIETLY deciding which of two conflicting material figures a module reads. So the hash keeps
# breaking the tie, the selection keeps returning a value rather than abstaining and blanking a
# field, and every case in which the hash decided between DIFFERENT values is reported as a
# material conflict on the period's Category-9 record. The disagreement becomes visible; it is
# no longer settled in silence by a property of the bytes.
def _snap_business_key(o: dict) -> tuple:
    """The SNAPSHOT precedence keys, hash excluded. Larger wins."""
    return (
        -int(o.get("tier") or 0),
        1 if o.get("as_of") is not None else 0,
        o.get("as_of") or date.min,
        int(o.get("rank") or 0), str(o.get("doc_type") or ""),
    )


def _perm_business_key(o: dict) -> tuple:
    """The PERMANENT precedence keys, hash excluded. Smaller wins."""
    return (
        int(o.get("tier") or 0),
        o.get("as_of") or date.max,
        int(o.get("rank") or 0), str(o.get("doc_type") or ""),
    )


def _snap_pick(group: list[dict]) -> dict:
    """SNAPSHOT winner: lowest tier; within it, dated beats undated, latest as_of wins;
    remaining ties resolve by the historical (rank, doc_type, sha256) last-write order."""
    best = max(_snap_business_key(o) for o in group)
    tied = [o for o in group if _snap_business_key(o) == best]
    return max(tied, key=lambda o: str(o.get("sha256") or ""))


def _perm_pick(group: list[dict]) -> dict:
    """PERMANENT winner: lowest tier; within it the EARLIEST dated observation, and nothing
    later ever replaces it. Undated observations lose to dated ones; wholly undated ties
    resolve by the historical first-non-null order (min rank/doc_type/sha)."""
    best = min(_perm_business_key(o) for o in group)
    tied = [o for o in group if _perm_business_key(o) == best]
    return min(tied, key=lambda o: str(o.get("sha256") or ""))


def _comparable(value: Any) -> Any:
    """A value in a form two observations can be compared by. Scalars as they are; anything
    structured by its canonical JSON, so a dict is not compared by object identity."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    return json.dumps(value, sort_keys=True, default=str)


def unresolved_value_conflicts(observations: list[dict]) -> list[dict]:
    """
    THE FIELDS WHERE THE DECLARED BUSINESS KEYS ARE EXHAUSTED AND THE VALUES STILL DISAGREE.

    RUN 135, ruling R3. This is the report the ruling requires. For each declared field it takes
    the SAME group `select_signal_inputs` would take, applies the SAME precedence key that
    field's kind uses -- `_snap_business_key` for SNAPSHOT and EVENT, `_perm_business_key` for
    PERMANENT -- and looks at the observations left tied on that key. If they all state the same
    value, sha256 is choosing between records that are identical in the only respect that
    matters, which R3 expressly permits and which needs no report. If they state DIFFERENT
    values, sha256 is deciding which figure a module reads, and that is the case the ruling says
    must be reported rather than settled.

    It reports; it does not refuse. The selection still returns a value, because blanking a
    field on a disagreement would replace a wrong figure with no figure and take every module
    that reads it dark -- a false refusal, which this programme has repeatedly recorded as being
    as much a defect as a false pass. The record travels to the caller, and
    `documents._evidence_qualification` puts it on the period's Category-9
    `material_conflicts`, where a REVIEW_REQUIRED assessment is already the platform's declared
    answer to documents that contradict each other.

    RAW evidence rows and the per-document self-descriptive fields are not shared assertions and
    are excluded, for the reasons `_evidence_qualification` sets out at length.

    Pure. Takes the observation set, returns records; knows nothing of projects or periods.
    """
    by_field: dict[str, list[dict]] = {}
    for o in observations:
        field = str(o.get("field") or "")
        if not field or field not in FIELD_KINDS or is_raw_field(field):
            continue
        by_field.setdefault(field, []).append(o)

    out: list[dict] = []
    for field in sorted(by_field):
        group = by_field[field]
        if FIELD_KINDS.get(field) == PERMANENT:
            best = min(_perm_business_key(o) for o in group)
            tied = [o for o in group if _perm_business_key(o) == best]
        else:
            best = max(_snap_business_key(o) for o in group)
            tied = [o for o in group if _snap_business_key(o) == best]
        values = {_comparable(o.get("value")) for o in tied}
        if len(values) <= 1:
            continue
        out.append({
            "field": field,
            "writer_tier": min(int(o.get("tier") or 0) for o in tied),
            "distinct_values": len(values),
            "documents": sorted({str(o.get("doc_type")) for o in tied}),
            "reason": "the declared business keys -- writer tier, dated over undated, as-of, "
                      "document rank and document type -- are exhausted and these documents "
                      "still state different values for this field. A content hash breaks the "
                      "remaining tie so a figure is still published, and under ruling R3 that "
                      "hash may order records but may not decide between conflicting values, "
                      "so the disagreement is reported here rather than settled silently",
        })
    return out


def _source_entry(w: dict) -> dict:
    """
    The per-field source record: WHICH ARTEFACT PRODUCED THIS FIELD, not merely what type it was.

    RUN 42. Until now this recorded ``{"docType", "value"}`` only, and the document identity was
    dropped even though the winning observation has always carried it -- ``emit_observations``
    puts ``document_id``, ``sha256``, ``revision_of`` and ``as_of`` on every record, and the
    stored result's ``source_documents`` lists the same identity per document. The loss was in
    this one path, not in the data.

    What it cost: ``qualification._provenance`` counts a field as traced only when it carries
    BOTH ``documentId`` and ``documentVersion``, so it counted zero on every project ever
    computed and the provenance dimension was pinned to PARTIAL; ``_timeliness`` counts
    ``asOf`` and was pinned the same way. ``_overall`` is the weakest of the dimensions, so
    those two alone held ``overall_qualification_state`` at NOT_ESTIMABLE for every period,
    which is the C1/Category-9 state the downstream categories read.

    ``documentVersion`` IS the sha256. Storage is content-addressed (documents.py stores
    ``Document.sha256`` as the key), so two revisions of one artefact are two different hashes
    and the hash is the version identity rather than a stand-in for one.

    Keys are omitted rather than written as null when the observation does not carry them, so a
    document that genuinely has no identity or no date still produces an honest record and the
    qualification dimension still reports PARTIAL for it.
    """
    entry: dict = {"docType": w["doc_type"], "value": w["value"]}
    document_id = w.get("document_id")
    if document_id:
        entry["documentId"] = str(document_id)
    sha = w.get("sha256")
    if sha:
        entry["documentVersion"] = str(sha)
    as_of = w.get("as_of")
    if as_of is not None:
        entry["asOf"] = as_of.isoformat()
    revision_of = w.get("revision_of")
    if revision_of:
        entry["revisionOf"] = str(revision_of)
    return entry


def select_signal_inputs(observations: list[dict], cutoff: date | None = None, *,
                         carried: list[dict] | None = None) -> dict:
    """The flat ``signalInputs`` dict, selected from observations at a cutoff. Pure.

    Every selection is ``as_of <= cutoff`` (undated observations pass — refusing them would
    silently blank most fields; D3 remains the open item it was). Recomputing an earlier
    period with its stored cutoff therefore reproduces it even after later-dated evidence
    arrives.

    RUN 45. ``carried`` is the observation set the project's EARLIER periods hold, supplied by
    the caller because only the caller knows what a project or a period is — this function
    stays pure and knows neither. Only IDENTITY-classified fields are taken from it
    (``field_registry.IDENTITY_FIELDS``), so a period field cannot carry forward however a
    caller fills the argument, and the default of None reproduces the pre-Run-45 selection
    exactly. Carried observations are resolved by the SAME per-field rule as the period's own,
    which is what makes declared document-type precedence hold ACROSS periods: a contract's
    tier-0 ``baselineContractSum`` from period 1 beats a change order's tier-1 account of it in
    period 2, and no period term enters ``_snap_pick``'s key, so the result stays order
    independent in the sense Run 42 proved.

    ``docDate`` is DELIBERATELY derived from the period's own observations only. It answers "as
    of when does this period speak", and a carried contract from an earlier period must not be
    able to date it — least of all in a period whose own documents are undated, where it would
    otherwise move a date that is currently absent.
    """
    eligible = [
        o for o in observations
        if cutoff is None or o.get("as_of") is None or o["as_of"] <= cutoff
    ]
    carried_eligible = [
        o for o in (carried or [])
        if str(o.get("field")) in IDENTITY_FIELDS
        and (cutoff is None or o.get("as_of") is None or o["as_of"] <= cutoff)
    ]

    by_field: dict[str, list[dict]] = {}
    for o in eligible + carried_eligible:
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
            sources[field] = _source_entry(w)
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
                sources[field] = _source_entry(w)
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
            sources[field] = _source_entry(w)

    # docDate is DERIVED: the latest as_of among the period's eligible observations — the
    # same rule `_derive_cutoff` applies to the document set, so "as of when" has one answer.
    dated = [o for o in eligible if o.get("as_of") is not None]
    if dated:
        w = max(dated, key=lambda o: (o["as_of"], int(o.get("rank") or 0),
                                      str(o.get("doc_type") or ""), str(o.get("sha256") or "")))
        si["docDate"] = w["as_of"].isoformat()
        sources["docDate"] = {**_source_entry(w), "value": si["docDate"]}

    # ---- derived indices, .gs 1065-1070. Several modules BAND on si["cpi"] and si["spi"].
    #
    # RUN 135, FINDING H1. THESE THREE LINES CARRIED `_round3` AND THEY NO LONGER DO.
    #
    # `_round3` is `floor(n*1000 + 0.5)/1000` -- half-up at the third decimal, a PRESENTATION
    # helper. Rounding here rounded the stored ANALYTICAL field, and A1.8 (`models_evm.py`,
    # `run_vac`) bands on exactly that stored field. The consequence was a wrong band, not a
    # wrong-looking number:
    #
    #   true CPI 0.9995 -> stored 1.0   -> A1.8 Green, where the true index gives Yellow
    #   true CPI 0.8995 -> stored 0.9   -> A1.8 Amber, where the true index gives Red
    #
    # BOTH ERRORS ARE FAVOURABLE, and they are favourable systematically: half-up widens the
    # favourable side of every edge by half a rounding step, so every true index in
    # [0.9995, 1.0) published as 1.00. Run 35 fixed the SAME defect one layer downstream, inside
    # the module -- it separated the module's band from the module's display -- but it never
    # reached the field the module reads, so the rounding simply moved upstream of the repair.
    #
    # THE RULE THIS ESTABLISHES, and it is the rule the whole Group-1 family rests on: a stored
    # analytical field is never a rounded one. Rounding is a property of a rendered sentence, it
    # is applied at the point of rendering, and no band ever reads its result. Nothing is stored
    # rounded here in its place: the display helpers already round at render, so a second stored
    # "rounded CPI" field would only be a second thing that could be banded on by mistake.
    cpi = None
    spi = None
    if si["ev"] is not None and si["ac"] is not None and si["ac"] != 0:
        cpi = si["ev"] / si["ac"]
    if si["ev"] is not None and si["pv"] is not None and si["pv"] != 0:
        spi = si["ev"] / si["pv"]
    if (
        spi is None
        and si["actualPctComplete"] is not None
        and si["plannedPctComplete"] is not None
        and si["plannedPctComplete"] != 0
    ):
        spi = si["actualPctComplete"] / si["plannedPctComplete"]

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
    # RUN 132. PRE-EXISTING BREAKAGE, FIXED HERE BECAUSE IT HID THE DEFECT THIS RUN CAME FOR.
    # This read == ["bac", "baselineContractSum", "baselineStart", "baselineEnd"] and had been
    # failing at every commit since ``evidence:<doc_type>:<key>`` pseudo-fields joined
    # fields_by_doc -- so the self-check DIED HERE and assertions 6 through 9 never ran, which
    # is exactly how ``a["ac"] == 4400000`` (assertion 7) survived unexamined. The signal-input
    # fields are asserted as before; the evidence pseudo-fields are asserted as a set.
    assert [f for f in rep["fields_by_doc"]["aaa"] if not f.startswith("evidence:")] == [
        "bac", "baselineContractSum", "baselineStart", "baselineEnd"]
    assert {f for f in rep["fields_by_doc"]["aaa"] if f.startswith("evidence:")} == {
        "evidence:contract_value:original_contract_sum",
        "evidence:contract_value:project_end_date",
        "evidence:contract_value:project_start_date"}
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
    # RUN 132. THIS ASSERTION ENCODED THE DEFECT. It read ``a["ac"] == 4400000`` and
    # ``a["cpi"] == 0.909`` -- an ``ac`` taken from the pay application's amount-paid-to-date,
    # i.e. a figure net of retainage read as a cost. It is RE-POINTED, not deleted: ``base``
    # holds no document stating an actual cost, so ``ac`` is absent and cpi does not compute.
    assert a["ev"] == 4000000, a["ev"]
    assert a["ac"] is None, "a pay application must not supply actual cost"
    assert a["cpi"] is None, a["cpi"]
    assert "ac" not in a["sources"]
    # ...and a monthly report in the same evidence set does supply it, and decides cpi.
    with_mr = assemble_signal_inputs(
        base + [doc("mmm", "monthly_report", {"actual_cost": 4400000,
                                              "report_period": "2024-09-30"})])
    assert with_mr["ac"] == 4400000, with_mr["ac"]
    assert with_mr["sources"]["ac"]["docType"] == "monthly_report"
    # RUN 138. RE-POINTED, NOT DELETED. This read ``== 0.909`` -- the value the assembler
    # stored back when it rounded, ``_round3(ev/ac)``. Run 135 H1 removed that rounding
    # ("a stored analytical field is never a rounded one") and this assertion was left
    # behind, so ``python -m app.extraction_merge`` had been failing on the very defect H1
    # fixed: 4000000/4400000 is 0.9090909090909091, not its three-place presentation. The
    # expectation is now the quotient of the fixture's OWN STATED FIGURES -- 4000000 above
    # and the 4400000 actual cost on the monthly report -- and not a transcribed literal,
    # so it cannot drift away from them again.
    assert with_mr["cpi"] == 4000000 / 4400000, with_mr["cpi"]
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
