"""Deterministic assembly of ``signalInputs`` from stored per-document extractions.

WHY THIS MODULE EXISTS
----------------------
The legacy instrument (``apps_script/reference/Code_v10.36_editor_head.gs``,
``extractSignals_``, lines 790-1101) merges ONE freshly extracted document into a
persisted ``project.signalInputs`` object each time a PM uploads a file. That design has
two properties that are fatal for this backend:

1. It is NON-IDEMPOTENT. Line ~916 does
       ``si.rfiCount = (si.rfiCount || 0) + rfiCount``
   and line ~949 does
       ``si.changeOrderCount = (si.changeOrderCount || 0) + 1``.
   Both mutate a persisted accumulator. Replaying the same document twice double-counts.

2. It is ORDER-DEPENDENT. Many branches are guarded by ``if (si.bac === null) ...``
   (lines 884, 889, 890, 903-908, 950, 1050-1051), so which document "wins" a field
   depends on the sequence in which the PM happened to upload files.

This backend re-derives ``signalInputs`` FROM STORED EXTRACTIONS ON EVERY RECOMPUTE. A
mutating accumulator cannot survive that: the second recompute would report twice the
RFIs. So this module reframes the merge as a **pure fold over a SET of documents**:

    assemble_signal_inputs(docs) == assemble_signal_inputs(docs)            (determinism)
    assemble_signal_inputs(shuffle(docs)) == assemble_signal_inputs(docs)   (order independence)
    assemble_signal_inputs([d, d]) == assemble_signal_inputs([d])           (idempotence)

Additive semantics are PRESERVED across DISTINCT documents — three RFI documents still
sum to three RFIs. They are simply computed by folding over the *deduplicated, sorted*
document set rather than by mutating a stored counter, so a recompute cannot double-count.

HOW ORDER INDEPENDENCE IS ACHIEVED
----------------------------------
Documents are sorted internally by ``(doc_type, sha256)`` before folding. Deliberately NOT
by upload time: two different projects that hold the identical document set must produce
byte-identical ``signalInputs`` regardless of the order or date each PM uploaded them.
Upload time is an accident of the user's workflow, not a property of the evidence. Sorting
by content hash makes the fold a function of the SET alone. With the input sorted, the
legacy sequential semantics ("first non-null wins", "last write wins", "+= 1") become
well-defined pure functions of the set, so the fold below is written sequentially — that
is the most faithful reproduction of the .gs chain — while still being order independent.

DOC-TYPE PRECEDENCE, AND WHY IT IS NOT PART OF THE SORT KEY BY ACCIDENT
-----------------------------------------------------------------------
Several branches write UNCONDITIONALLY rather than first-non-null — ``contract_value``
writes ``bac``/``baselineStart``/``baselineEnd`` with no ``=== null`` guard (.gs 879-881) —
so "which document folds last" decides the value. Sorting by ``doc_type`` alone put
``change_order`` before ``contract_value``, which meant an approved EOT date and revised
contract sum were overwritten by the original contract: a change order silently losing to
the very contract it amends. The legacy avoided this only because the contract was normally
uploaded first, i.e. by upload order, which a fold over a set cannot and should not
reproduce.

``_DOC_TYPE_RANK`` below resolves it by the document's ROLE rather than its arrival time:
baselines fold first, then everything else, then instruments that revise a baseline. Rank is
a property of the doc TYPE, so order independence and cross-project identity are preserved
exactly.

KEY INSERTION ORDER IS LOAD-BEARING
-----------------------------------
``server/app/simulation/models_dq.py`` line ~101 iterates ``si["sources"]`` with the
comment "insertion order; do not sort", and ``models_gov.py`` line ~31 says "The
Object.keys reductions in the voting modules iterate insertion order. DO NOT SORT."
JavaScript object key order for the legacy ``si`` is the order of the initializer at .gs
lines 811-833 (later assignment to an existing key does not reorder it). ``_KEY_ORDER``
below reproduces that initializer order exactly, and the output dict is always built in
that order — never sorted, never in "fields we happened to fill" order. ``cpi``/``spi``
are appended last because the legacy assigns them at line 1070, after the initializer.

JS TRUTHINESS QUIRKS ARE REPRODUCED, NOT FIXED
----------------------------------------------
The analytical layer depends on them (e.g. ``si.get("docRiskScore") or 0`` treats a
genuine 0.0 as absent). Each quirk is reproduced and commented at its site. In particular
``_num_or_null`` reproduces ``numOrNull_`` (.gs line 1135) including its most surprising
behaviour: a non-numeric string strips to ``""`` and ``Number("")`` is ``0``, so
``numOrNull_("N/A") === 0``, not null.

PURITY
------
No network, no filesystem, no database, no clock. The legacy stamps every ``sources``
entry with ``at: new Date().toISOString()``; that is omitted here because a clock read
would break determinism, and nothing in the simulation layer reads it (``models_dq``
and ``models_ext`` only ever read ``docType``).
"""

from __future__ import annotations

from typing import Any

# Sibling module (written in parallel) owns the doc-type registry. UNMAPPED is the label
# used for doc types the legacy chain has no branch for; is_mapped(doc_type) -> bool.
from .extraction_fields import UNMAPPED, canonical_doc_type, is_mapped

__all__ = [
    "assemble_signal_inputs",
    "assembly_report",
    "DOC_RISK_DOC_TYPES",
    "DOC_RISK_SCORE_MAX",
    "DOC_RISK_SCORE_MIN",
    "DocRiskScoreRangeError",
    "SIGNAL_INPUT_KEYS",
    "validate_doc_risk_score",
]


# --------------------------------------------------------------------------- doc risk
# The whitelist at .gs line ~910 whose branch copies `document_risk_score` straight to
# si.docRiskScore, plus commissioning_report which does the same at .gs line ~1061.
#
# NOTE (A4.1): "Document Risk Score" is NOT computed by the analytical layer — the
# registry raises MissingModuleError for it. The value is emitted by the extraction model
# itself and merely copied through by this function. It is expected in 0..1 because the
# legacy sim.js clamps it to [0,1] and bands it at 0.30 / 0.70. A model that returns a
# 0-100 percentage will pin every project to the worst band; that is an extraction-side
# contract, not something this module rescales (rescaling here would silently diverge
# from the instrument being reproduced).
#
# THAT CONTRACT IS NOW ENFORCED BY REFUSAL. See validate_doc_risk_score below.
DOC_RISK_DOC_TYPES: frozenset[str] = frozenset(
    {
        "rfi",
        "submittal_register",
        "oac_minutes",
        "correspondence_notice",
        "risk_register",
        "inspection_report",
        "field_report",
        "commissioning_report",
    }
)

# The doc types in the shared branch at .gs line 910 (docRiskScore + docDate, then
# type-specific sub-blocks). commissioning_report is NOT in this list — it has its own
# terminal branch that sets docRiskScore but deliberately NOT docDate.
_RISK_BRANCH_TYPES: frozenset[str] = frozenset(
    {
        "rfi",
        "submittal_register",
        "oac_minutes",
        "correspondence_notice",
        "risk_register",
        "inspection_report",
        "field_report",
    }
)

# --------------------------------------------------------------------------- key order
# Verbatim transcription of the si initializer, .gs lines 812-832, in source order.
# DO NOT SORT and DO NOT REORDER: see module docstring.
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
        documented legacy quirk. That lands in range and is left alone: changing it would
        alter behaviour the instrument has always had, which is a separate decision.

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


def _round3(n: float) -> float:
    """Port of ``round3_`` (.gs 1140). Math.round is half-up, unlike Python's banker's."""
    import math

    return math.floor(n * 1000 + 0.5) / 1000


def _is_blank_date(v: Any) -> bool:
    """``setDate`` guard, .gs 875: null/undefined/'' and the literal string 'null'."""
    return v is None or v == "" or str(v).lower() == "null"


# --------------------------------------------------------------------------- ordering


# Explicit application precedence. Documents are folded in RANK order first, then by
# (doc_type, sha256) within a rank.
#
# This exists because several branches write unconditionally rather than first-non-null, so
# "which document is applied last" decides the value. The legacy resolved that by upload
# order, which is an accident of the user's workflow and cannot be reproduced by a fold over
# a set. Ranking by the DOCUMENT'S ROLE reproduces the legacy's *intent* deterministically:
# a baseline is established, then instruments that revise it are applied on top.
#
# Concretely, the case that forced this: contract_value writes bac / baselineStart /
# baselineEnd unconditionally (.gs 879-881). Sorted alphabetically, change_order folds
# BEFORE contract_value, so an approved EOT date and revised sum were overwritten by the
# original contract — a change order silently losing to the contract it amends. Ranking
# contract_value as a baseline (0) and change_order as a revision (2) fixes that without
# reintroducing upload-time ordering.
#
# Anything unlisted defaults to rank 1: it neither establishes nor revises the baseline.
_RANK_BASELINE = 0
_RANK_DEFAULT = 1
_RANK_REVISION = 2

_DOC_TYPE_RANK: dict[str, int] = {
    # Baselines — establish the contract and the as-planned schedule.
    "contract_value": _RANK_BASELINE,
    "schedule_of_values": _RANK_BASELINE,
    "time_phased_schedule": _RANK_BASELINE,
    # Revisions — amend a baseline established above, so they must land afterwards.
    "change_order": _RANK_REVISION,
    "schedule_update": _RANK_REVISION,
}


def _doc_rank(doc_type: str) -> int:
    return _DOC_TYPE_RANK.get(doc_type, _RANK_DEFAULT)


def _ordered_docs(documents: list[dict]) -> list[dict]:
    """Sort by (rank, doc_type, sha256) and de-duplicate by sha256.

    Sorting by content identity, never by upload time: two projects holding the same
    evidence must yield byte-identical signalInputs regardless of when each was uploaded.
    The rank prefix is a property of the document TYPE, not of the upload, so it preserves
    that guarantee while making revisions beat the baselines they revise.

    De-duplication by sha256 is the second safety net against the legacy double-count
    bug — even if a caller hands us the same stored extraction twice (re-upload of an
    identical file, or a retry that wrote two rows), the additive branches see it once.
    First occurrence in sorted order wins; because the sort key contains the sha256, the
    surviving record is deterministic even if two records share a hash but differ in
    filename or extraction payload.
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


# --------------------------------------------------------------------------- the fold


class _Acc:
    """Working accumulator mirroring the mutable legacy ``si`` for one fold pass.

    Kept internal: the value returned to callers is rebuilt in ``_KEY_ORDER`` at the end,
    so no caller can accidentally depend on the order fields happened to be filled in.
    """

    def __init__(self) -> None:
        # Every legacy key starts at None (JS null), exactly like the .gs initializer.
        self.si: dict[str, Any] = {k: None for k in _KEY_ORDER}
        self.sources: dict[str, dict] = {}
        self.applied_by_doc: dict[str, list[str]] = {}
        self._doc_key: str = ""
        self._doc_type: str = ""

    def begin(self, doc_key: str, doc_type: str) -> None:
        self._doc_key = doc_key
        self._doc_type = doc_type
        self.applied_by_doc.setdefault(doc_key, [])

    def _note(self, key: str, value: Any) -> None:
        # sources is keyed by signalInput FIELD NAME and records the contributing docType;
        # models_dq.run_source_reliability weights by that docType and counts a "derived"
        # docType as an estimated field. Last contributor wins, matching the legacy
        # overwrite at .gs 872. `at` is intentionally absent (no clock in a pure fn).
        self.sources[key] = {"docType": self._doc_type, "value": value}
        self.applied_by_doc[self._doc_key].append(key)

    def set_field(self, key: str, val: Any) -> None:
        """Port of ``setField`` (.gs 870-873).

        The guard rejects null/undefined/'' but NOT 0 — a genuine zero IS stored. The
        simulation layer then re-reads it through JS-truthy idioms like
        ``si.get("docRiskScore") or 0`` and treats it as absent anyway. Both halves of
        that quirk are load-bearing; do not "fix" either one.
        """
        if val is None or val == "":
            return
        self.si[key] = val
        self._note(key, val)

    def set_date(self, key: str, val: Any) -> None:
        """Port of ``setDate`` (.gs 874-877). Stores ``String(val)``; last write wins."""
        if _is_blank_date(val):
            return
        s = str(val)
        self.si[key] = s
        self._note(key, s)

    def add(self, key: str, amount: float) -> None:
        """Additive branch, expressed as a fold over the deduplicated SET.

        The legacy ``si.rfiCount = (si.rfiCount || 0) + rfiCount`` mutated persisted
        state, so a replay double-counted. Here the accumulator lives for the duration of
        one call and the input set is deduplicated, so N distinct RFI documents still sum
        to N while re-running over the same set is a no-op change.

        ``(si.x || 0)`` is reproduced literally: a stored 0 or None both start from 0.
        """
        base = self.si.get(key) or 0
        self.si[key] = base + amount
        # NOTE: the legacy pushes the key onto `applied` but does NOT write si.sources
        # for the additive branches (.gs 916, 949 bypass setField). Reproduced: an
        # rfi-derived rfiCount contributes no source-reliability weight, while an
        # rfi_log-derived rfiCount does. models_dq's average shifts accordingly.
        self.applied_by_doc[self._doc_key].append(key)

    def keep_max(self, key: str, val: float) -> None:
        """``Math.max(si.rfiNumber || 0, n)`` (.gs 917). Max is order independent by
        construction, so this needs no special handling beyond reproducing ``|| 0``."""
        self.si[key] = max(self.si.get(key) or 0, val)
        self.applied_by_doc[self._doc_key].append(key)


def _merge_one(acc: _Acc, doc_type: str, ex: dict) -> None:
    """One iteration of the .gs if/else-if chain, lines 878-1064.

    Branch order and guards are transcribed 1:1. The only structural change is that the
    "if (si.X === null)" fallbacks now resolve against sorted-set order instead of upload
    order, which makes them deterministic.
    """
    si = acc.si
    n = _num_or_null

    if doc_type == "contract_value":  # .gs 878
        acc.set_field("bac", n(ex.get("original_contract_sum")))
        acc.set_date("baselineStart", ex.get("project_start_date"))
        acc.set_date("baselineEnd", ex.get("project_end_date"))

    elif doc_type == "schedule_of_values":  # .gs 882
        acc.set_field("ev", n(ex.get("completed_to_date")))
        if si["bac"] is None:  # fallback: only if no contract_value supplied one
            acc.set_field("bac", n(ex.get("scheduled_value_total")))
        acc.set_date("docDate", ex.get("period_to_date"))

    elif doc_type == "pay_application":  # .gs 886
        acc.set_field("ac", n(ex.get("amount_paid_to_date")))
        acc.set_field("actualPctComplete", n(ex.get("percent_complete_verified")))
        if si["bac"] is None:
            acc.set_field("bac", n(ex.get("original_contract_sum")))
        if si["ev"] is None:
            acc.set_field("ev", n(ex.get("completed_to_date")))
        acc.set_date("workPeriodFrom", ex.get("work_period_from"))
        acc.set_date("workPeriodTo", ex.get("work_period_to"))
        acc.set_date("docDate", ex.get("application_date"))
        if n(ex.get("original_contingency")) is not None:
            acc.set_field("originalContingency", n(ex.get("original_contingency")))
        if n(ex.get("remaining_contingency")) is not None:
            acc.set_field("remainingContingency", n(ex.get("remaining_contingency")))

    elif doc_type == "time_phased_schedule":  # .gs 896
        acc.set_field("pv", n(ex.get("planned_value_to_date")))
        acc.set_field("plannedPctComplete", n(ex.get("planned_percent_complete")))
        acc.set_date("docDate", ex.get("data_date"))
        if n(ex.get("total_float")) is not None:
            acc.set_field("totalFloat", n(ex.get("total_float")))
        if n(ex.get("consumed_float")) is not None:
            acc.set_field("consumedFloat", n(ex.get("consumed_float")))

    elif doc_type == "monthly_report":  # .gs 902 — every EVM field is a FALLBACK here:
        # a monthly report never overrides a primary source (SoV / pay app / schedule).
        if si["ev"] is None:
            acc.set_field("ev", n(ex.get("earned_value")))
        if si["ac"] is None:
            acc.set_field("ac", n(ex.get("actual_cost")))
        if si["pv"] is None:
            acc.set_field("pv", n(ex.get("planned_value")))
        if si["actualPctComplete"] is None:
            acc.set_field("actualPctComplete", n(ex.get("actual_percent_complete")))
        if si["plannedPctComplete"] is None:
            acc.set_field("plannedPctComplete", n(ex.get("planned_percent_complete")))
        if si["bac"] is None:
            acc.set_field("bac", n(ex.get("budget_at_completion")))
        acc.set_date("docDate", ex.get("report_date"))

    elif doc_type in _RISK_BRANCH_TYPES:  # .gs 910 — shared risk-document branch
        # Last line before the value reaches storage and fusion. The extraction boundary
        # refuses first (extract_many), so a document uploaded today cannot arrive here out of
        # range; this catches a row that reached the database by some other route, including
        # one stored before the guard existed.
        validate_doc_risk_score(ex.get("document_risk_score"))
        risk = n(ex.get("document_risk_score"))
        if risk is not None:
            acc.set_field("docRiskScore", risk)
        acc.set_date("docDate", ex.get("document_date"))

        if doc_type == "rfi":  # .gs 914
            rfi_count = n(ex.get("rfi_count"))
            if rfi_count is not None:
                # THE canonical accumulation. Set-fold, not stored counter.
                acc.add("rfiCount", rfi_count)
            if n(ex.get("rfi_number")) is not None:
                acc.keep_max("rfiNumber", n(ex.get("rfi_number")))
            if n(ex.get("rfi_period_days")) is not None:
                acc.set_field("rfiPeriodDays", n(ex.get("rfi_period_days")))
            if n(ex.get("response_time_days")) is not None:
                acc.set_field("rfiResponseTimeDays", n(ex.get("response_time_days")))

        if doc_type == "oac_minutes":  # .gs 921
            for src, dst in (
                ("subcontractor_issues_discussed", "subcontractorIssuesDiscussed"),
                ("outstanding_action_items", "outstandingActionItems"),
                ("subcontractor_disputes", "subcontractorDisputes"),
                ("safety_incidents_discussed", "safetyIncidentsDiscussed"),
                ("safety_actions_open", "safetyActionsOpen"),
                ("environmental_issues_discussed", "environmentalIssuesDiscussed"),
                ("quality_issues_discussed", "qualityIssuesDiscussed"),
                ("weather_days_discussed", "weatherDaysDiscussed"),
            ):
                # Last-in-sorted-order wins. NOT summed in the legacy either: two OAC
                # minutes documents do not add their action-item counts.
                if n(ex.get(src)) is not None:
                    acc.set_field(dst, n(ex.get(src)))

        if doc_type == "submittal_register":  # .gs 931
            if n(ex.get("submittals_total")) is not None:
                acc.set_field("submittalsTotal", n(ex.get("submittals_total")))
            if n(ex.get("submittals_rejected")) is not None:
                acc.set_field("submittalsRejected", n(ex.get("submittals_rejected")))

        if doc_type == "field_report":  # .gs 935
            if n(ex.get("weather_days_lost")) is not None:
                acc.set_field("weatherDaysLost", n(ex.get("weather_days_lost")))
            if n(ex.get("float_remaining")) is not None:
                acc.set_field("floatRemaining", n(ex.get("float_remaining")))
            if n(ex.get("quality_deficiencies_noted")) is not None:
                acc.set_field("qualityDeficienciesNoted", n(ex.get("quality_deficiencies_noted")))

        if doc_type == "inspection_report":  # .gs 940
            if n(ex.get("items_inspected")) is not None:
                acc.set_field("itemsInspected", n(ex.get("items_inspected")))
            if n(ex.get("items_failed")) is not None:
                acc.set_field("itemsFailed", n(ex.get("items_failed")))
            # NOTE: inspection_report's deficiency_count lands in the SAME field that
            # field_report's quality_deficiencies_noted uses. Whichever doc type sorts
            # later ("inspection_report" < "field_report" is false, so field_report wins)
            # takes the field. Legacy had the same collision, resolved by upload order.
            if n(ex.get("deficiency_count")) is not None:
                acc.set_field("qualityDeficienciesNoted", n(ex.get("deficiency_count")))
            if n(ex.get("critical_deficiency_count")) is not None:
                acc.set_field("criticalDeficiencyCount", n(ex.get("critical_deficiency_count")))

    elif doc_type == "change_order":  # .gs 946
        if n(ex.get("revised_contract_sum")) is not None:
            # A change order DOES override bac — unlike monthly_report, it is authoritative.
            acc.set_field("bac", n(ex.get("revised_contract_sum")))
        if n(ex.get("change_order_count")) is not None:
            # Explicit count REPLACES (setField), it does not add. Reproduced.
            acc.set_field("changeOrderCount", n(ex.get("change_order_count")))
        else:
            # ...but a change order with no stated count increments by one. This is the
            # second legacy accumulator (.gs 949). Same treatment as rfiCount: it folds
            # over the deduplicated set, so two distinct COs give 2 and a replay gives 2.
            acc.add("changeOrderCount", 1)
        if n(ex.get("baseline_contract_sum")) is not None and si["baselineContractSum"] is None:
            acc.set_field("baselineContractSum", n(ex.get("baseline_contract_sum")))
        if n(ex.get("revised_contract_sum")) is not None:
            acc.set_field("revisedContractSum", n(ex.get("revised_contract_sum")))
        new_end = ex.get("revised_completion_date")
        if not _is_blank_date(new_end) and str(new_end) != si["baselineEnd"]:
            # .gs 952-960: an EOT rewrites the baseline end date. The legacy also appends
            # a `baseline_adjusted_eot` entry to project.events; that is project-level
            # state, not signalInputs, and is therefore out of scope for this function.
            si["baselineEnd"] = str(new_end)
            acc._note("baselineEnd", str(new_end))

    elif doc_type == "safety_report":  # .gs 961
        incident_rate = n(ex.get("incident_rate"))
        if (
            incident_rate is None
            and n(ex.get("osha_recordable_incidents")) is not None
            and n(ex.get("total_manhours")) is not None
        ):
            # Derived OSHA TRIR per 200k hours. Legacy does NOT guard total_manhours == 0;
            # in JS that yields Infinity. Guarded here only against a hard ZeroDivisionError
            # (Python has no Infinity literal from int division), producing None instead.
            mh = n(ex.get("total_manhours"))
            if mh:
                incident_rate = _round3((n(ex.get("osha_recordable_incidents")) / mh) * 200000)
        if incident_rate is not None:
            acc.set_field("oshaIncidentRate", incident_rate)
        if n(ex.get("total_manhours")) is not None:
            acc.set_field("totalManhours", n(ex.get("total_manhours")))
        acc.set_date("docDate", ex.get("report_period"))

    elif doc_type == "quality_audit_report":  # .gs 968
        if n(ex.get("audit_score")) is not None:
            acc.set_field("qualityAuditScore", n(ex.get("audit_score")))
        if n(ex.get("total_findings")) is not None:
            acc.set_field("totalFindings", n(ex.get("total_findings")))
        if n(ex.get("critical_findings")) is not None:
            acc.set_field("criticalFindings", n(ex.get("critical_findings")))
        acc.set_date("docDate", ex.get("audit_date"))

    elif doc_type == "environmental_report":  # .gs 973
        if n(ex.get("compliance_rate")) is not None:
            acc.set_field("environmentalComplianceRate", n(ex.get("compliance_rate")))
        if n(ex.get("violations")) is not None:
            acc.set_field("environmentalViolations", n(ex.get("violations")))
        acc.set_date("docDate", ex.get("report_date"))

    elif doc_type == "ncr_log":  # .gs 977
        if n(ex.get("ncr_issued")) is not None:
            acc.set_field("ncrIssued", n(ex.get("ncr_issued")))
        if n(ex.get("ncr_closed")) is not None:
            acc.set_field("ncrClosed", n(ex.get("ncr_closed")))
        if n(ex.get("ncr_open")) is not None:
            acc.set_field("ncrOpen", n(ex.get("ncr_open")))
        acc.set_date("docDate", ex.get("report_period"))

    elif doc_type == "subcontractor_report":  # .gs 982
        comp = n(ex.get("compliance_score"))
        if (
            comp is None
            and n(ex.get("on_time_deliveries")) is not None
            and n(ex.get("scheduled_deliveries")) is not None
            and n(ex.get("scheduled_deliveries")) != 0
        ):
            comp = _round3(n(ex.get("on_time_deliveries")) / n(ex.get("scheduled_deliveries")))
        if comp is not None:
            acc.set_field("subcontractorComplianceScore", comp)
        acc.set_date("docDate", ex.get("report_period"))

    elif doc_type == "procurement_log":  # .gs 988
        if n(ex.get("long_lead_items_total")) is not None:
            acc.set_field("longLeadItemsTotal", n(ex.get("long_lead_items_total")))
        if n(ex.get("at_risk")) is not None:
            acc.set_field("longLeadAtRisk", n(ex.get("at_risk")))
        if n(ex.get("delayed")) is not None:
            acc.set_field("longLeadDelayed", n(ex.get("delayed")))
        acc.set_date("docDate", ex.get("report_date"))

    elif doc_type == "lookahead_schedule":  # .gs 993
        if n(ex.get("activities_planned")) is not None:
            acc.set_field("activitiesPlanned", n(ex.get("activities_planned")))
        if n(ex.get("activities_constrained")) is not None:
            acc.set_field("activitiesConstrained", n(ex.get("activities_constrained")))
        if n(ex.get("lookahead_weeks")) is not None:
            acc.set_field("lookaheadWeeks", n(ex.get("lookahead_weeks")))
        # .gs 997 falls back to `new Date()` when report_date is absent. A clock read is
        # forbidden here (it would break determinism AND make the value meaningless on a
        # recompute months later), so an absent report_date simply sets no docDate.
        acc.set_date("docDate", ex.get("report_date"))

    elif doc_type == "resource_report":  # .gs 998 — note: sets no docDate in the legacy.
        if n(ex.get("planned_labor_hours")) is not None:
            acc.set_field("plannedLaborHours", n(ex.get("planned_labor_hours")))
        if n(ex.get("actual_labor_hours")) is not None:
            acc.set_field("actualLaborHours", n(ex.get("actual_labor_hours")))

    elif doc_type == "cost_report":  # .gs 1001
        for src, dst in (
            ("indirect_cost_plan", "indirectCostPlan"),
            ("indirect_cost_actual", "indirectCostActual"),
            ("material_cost_baseline", "materialCostBaseline"),
            ("material_cost_current", "materialCostCurrent"),
        ):
            if n(ex.get(src)) is not None:
                acc.set_field(dst, n(ex.get(src)))
        acc.set_date("docDate", ex.get("report_date"))

    elif doc_type == "past_performance_report":  # .gs 1007 — no docDate in the legacy.
        for src, dst in (
            ("overall_rating", "overallRating"),
            ("schedule_rating", "scheduleRating"),
            ("cost_rating", "costRating"),
            ("quality_rating", "qualityRating"),
        ):
            if n(ex.get(src)) is not None:
                acc.set_field(dst, n(ex.get(src)))

    elif doc_type == "historical_data":  # .gs 1012
        if n(ex.get("analogous_overrun_pct")) is not None:
            acc.set_field("analogousOverrunPct", n(ex.get("analogous_overrun_pct")))
        if n(ex.get("similar_project_bac")) is not None:
            acc.set_field("analogousBac", n(ex.get("similar_project_bac")))
        if n(ex.get("similar_project_final_cost")) is not None:
            acc.set_field("analogousFinalCost", n(ex.get("similar_project_final_cost")))
        # completion_year is stringified into docDate — a bare "2019", not an ISO date.
        acc.set_date("docDate", str(ex["completion_year"]) if ex.get("completion_year") else None)

    # ---- the .gs chain restarts as a SEPARATE if/else-if block at line 1035, so these
    # ---- types are reachable in addition to (not instead of) the block above. In
    # ---- practice a document has exactly one doc_type, so they are elif-chained here.

    elif doc_type == "rfi_log":  # .gs 1035
        # rfi_log sets rfiCount ABSOLUTELY (setField), while individual rfi docs ADD to
        # it. Under (doc_type, sha256) sorting, "rfi" < "rfi_log", so the log's authoritative
        # total always lands last and wins. That is a deliberate, stable resolution of a
        # collision that the legacy resolved by upload order.
        if n(ex.get("rfi_total")) is not None:
            acc.set_field("rfiCount", n(ex.get("rfi_total")))
        for src, dst in (
            ("rfi_open", "rfiOpen"),
            ("rfi_overdue", "rfiOverdue"),
            ("avg_response_days", "rfiAvgResponseDays"),
            ("rfi_period_days", "rfiPeriodDays"),
            ("oldest_open_days", "rfiOldestOpenDays"),
        ):
            if n(ex.get(src)) is not None:
                acc.set_field(dst, n(ex.get(src)))
        acc.set_date("docDate", ex.get("log_date"))

    elif doc_type == "rfa_log":  # .gs 1043
        for src, dst in (
            ("rfa_total", "rfaTotal"),
            ("rfa_approved", "rfaApproved"),
            ("rfa_rejected", "rfaRejected"),
            ("rfa_resubmit", "rfaResubmit"),
            ("rfa_open", "rfaOpen"),
            ("avg_review_days", "rfaAvgReviewDays"),
        ):
            if n(ex.get(src)) is not None:
                acc.set_field(dst, n(ex.get(src)))
        # RFA totals stand in for submittal totals when no submittal doc supplied them.
        if si["submittalsTotal"] is None and n(ex.get("rfa_total")) is not None:
            acc.set_field("submittalsTotal", n(ex.get("rfa_total")))
        if si["submittalsRejected"] is None and n(ex.get("rfa_rejected")) is not None:
            acc.set_field("submittalsRejected", n(ex.get("rfa_rejected")))
        acc.set_date("docDate", ex.get("log_date"))

    elif doc_type == "schedule_update":  # .gs 1053 — no docDate, despite requesting data_date.
        acc.set_field("plannedPctComplete", n(ex.get("planned_percent_complete")))
        for src, dst in (
            ("planned_value_to_date", "pv"),
            ("total_float", "totalFloat"),
            ("consumed_float", "consumedFloat"),
            ("activities_planned", "activitiesPlanned"),
            ("activities_constrained", "activitiesConstrained"),
            ("lookahead_weeks", "lookaheadWeeks"),
        ):
            if n(ex.get(src)) is not None:
                acc.set_field(dst, n(ex.get(src)))

    elif doc_type == "commissioning_report":  # .gs 1061 — docRiskScore only, no docDate.
        validate_doc_risk_score(ex.get("document_risk_score"))  # same guard as the risk branch
        crisk = n(ex.get("document_risk_score"))
        if crisk is not None:
            acc.set_field("docRiskScore", crisk)

    # No `else`. An unrecognised doc_type must contribute NOTHING — it must never fall
    # through into a merge branch. Callers reach this function only via is_mapped().


# --------------------------------------------------------------------------- public API


def assemble_signal_inputs(documents: list[dict]) -> dict:
    """Assemble ``signalInputs`` from a set of stored per-document extractions.

    ``documents`` items are ``{"sha256", "doc_type", "filename", "extraction"}``.
    Pure: no clock, no I/O. Deterministic, order independent, idempotent. See the module
    docstring for why those three properties are non-negotiable here.

    Unmapped doc types contribute nothing (see ``assembly_report`` to surface them).
    """
    acc = _Acc()
    for d in _ordered_docs(documents):
        # Canonicalised, so a row stored as the retired "submittal" still reaches the
        # submittal_register branch instead of silently contributing nothing.
        doc_type = canonical_doc_type(str(d.get("doc_type") or ""))
        if not doc_type or doc_type == UNMAPPED or not is_mapped(doc_type):
            continue  # contributes nothing; reported by assembly_report()
        ex = d.get("extraction") or {}
        if not isinstance(ex, dict):
            continue
        acc.begin(str(d.get("sha256") or ""), doc_type)
        _merge_one(acc, doc_type, ex)

    # ---- derived indices, .gs 1065-1070. Computed here (not by the sim layer) because
    # ---- the legacy stored cpi/spi ON signalInputs and several modules read si["cpi"].
    si = acc.si
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
        # Percent-complete fallback for SPI. Note the legacy uses `!== 0` here, so a
        # planned % of exactly 0 abstains rather than dividing.
        spi = _round3(si["actualPctComplete"] / si["plannedPctComplete"])

    # ---- Final assembly in FIXED key order. Do not sort, do not reorder: models_dq and
    # ---- models_gov iterate insertion order (see module docstring).
    out: dict[str, Any] = {}
    for k in _KEY_ORDER:
        out[k] = si[k]
    out["sources"] = acc.sources  # own insertion order = order of first contribution
    out["cpi"] = cpi
    out["spi"] = spi
    return out


def assembly_report(documents: list[dict]) -> dict:
    """Explain which documents contributed which signalInput fields, and which did not.

    The upload response uses this to tell the PM, explicitly, that a document they
    uploaded changed nothing — the single most common source of "why is my dashboard
    still grey?" confusion. Same sorting and de-duplication rules as
    ``assemble_signal_inputs``, so the two views can never disagree.

    Returns ``{"contributed": [...], "unmapped": [...], "fields_by_doc": {sha256: [...]}}``.
    A mapped document that produced no fields (extraction all nulls) appears in
    ``contributed`` with an empty field list — it IS a recognised type, it just carried
    no usable values, which is a different remedy for the PM than an unmapped type.
    """
    acc = _Acc()
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
        acc.begin(sha, doc_type)
        _merge_one(acc, doc_type, ex)
        # De-duplicate the applied list while preserving first-touch order (a branch can
        # write the same key twice, e.g. change_order writing bac then revisedContractSum).
        seen: set[str] = set()
        fields = [k for k in acc.applied_by_doc.get(sha, []) if not (k in seen or seen.add(k))]
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
        doc("ddd", "rfi", {"document_risk_score": 0.42, "rfi_count": 3, "rfi_number": 17,
                           "document_date": "2024-09-15"}),
        doc("eee", "rfi", {"document_risk_score": 0.61, "rfi_count": 2, "rfi_number": 22,
                           "document_date": "2024-09-20"}),
        doc("fff", "change_order", {"revised_contract_sum": 10400000,
                                    "revised_completion_date": "2026-03-31"}),
        doc("ggg", "change_order", {"revised_contract_sum": 10600000}),
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
    one = assemble_signal_inputs([base[3]])
    twice = assemble_signal_inputs([base[3], base[3]])
    assert one == twice, "same document twice must not double-count"
    assert one["rfiCount"] == 3

    # 4. additivity across DISTINCT documents (legacy semantics preserved)
    two_rfis = assemble_signal_inputs([base[3], base[4]])
    assert two_rfis["rfiCount"] == 5, two_rfis["rfiCount"]
    assert two_rfis["rfiNumber"] == 22, "rfiNumber must keep the max"
    # ...and the implicit change_order += 1 accumulator
    assert a["changeOrderCount"] == 2, a["changeOrderCount"]
    assert assemble_signal_inputs([base[5], base[5], base[6]])["changeOrderCount"] == 2

    # 5. an unmapped doc_type contributes zero keys
    blank = assemble_signal_inputs([])
    with_unmapped = assemble_signal_inputs(
        [doc("zzz", "wedding_invitation", {"document_risk_score": 0.99, "bac": 1})]
    )
    assert with_unmapped == blank, "unmapped doc type leaked into signalInputs"
    assert with_unmapped["sources"] == {}
    rep = assembly_report([doc("zzz", "wedding_invitation", {"x": 1}), base[0]])
    assert [u["sha256"] for u in rep["unmapped"]] == ["zzz"]
    assert rep["fields_by_doc"]["zzz"] == []
    assert rep["fields_by_doc"]["aaa"] == ["bac", "baselineStart", "baselineEnd"]
    assert assembly_report(list(reversed(base))) == assembly_report(base)

    # 6. quirks that the analytical layer depends on
    assert _num_or_null("N/A") == 0.0, "JS Number('') === 0 quirk lost"
    assert _num_or_null("$1,200,000.50") == 1200000.50
    assert _num_or_null("") is None and _num_or_null(None) is None
    zero_risk = assemble_signal_inputs([doc("q", "rfi", {"document_risk_score": 0})])
    assert zero_risk["docRiskScore"] == 0, "a genuine 0 must be STORED (sim treats it as absent)"
    assert (zero_risk["sources"] or {}).get("docRiskScore", {}).get("docType") == "rfi"
    # additive branches deliberately write no source entry (legacy bypasses setField)
    assert "rfiCount" not in one["sources"]

    # 7. cross-checks on the assembled economics
    # A change order REVISES the contract, so it must fold after it. contract_value is a
    # baseline (rank 0) and change_order a revision (rank 2), so the revised sum and the
    # approved EOT date both survive. Sorting on doc_type alone put change_order first and
    # let the original contract overwrite them — see the precedence note in the docstring.
    assert a["bac"] == 10600000, a["bac"]
    assert a["revisedContractSum"] == 10600000, a["revisedContractSum"]
    assert a["ev"] == 4000000 and a["ac"] == 4400000
    assert a["cpi"] == 0.909, a["cpi"]
    assert a["baselineEnd"] == "2026-03-31", a["baselineEnd"]
    eot_only = assemble_signal_inputs([base[5]])
    assert eot_only["baselineEnd"] == "2026-03-31", "EOT must rewrite baselineEnd"
    # and the precedence must not depend on input order
    assert assemble_signal_inputs(list(reversed(base))) == a

    print("extraction_merge self-check: OK")
