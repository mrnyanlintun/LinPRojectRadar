"""
RUN 87. THE QUALITY AND ENVIRONMENTAL REQUIREMENT REGISTERS, READ FROM THE DOCUMENTS THAT
PRINT THEM.

WHAT THIS CLOSES.

  A6.1 Quality Compliance Index is defined on a POPULATION -- "the share of the applicable
  quality requirements that were assessed and found satisfied" -- and the only thing the
  platform ever asked a quality or inspection document for was SUMMARIES: an audit score, a
  findings count, a critical-findings count, an items-inspected/items-failed pair. The
  specification's own words: "An audit score, a findings count and a critical-findings count
  are summaries, and section 13 forbids substituting a summary for a denominator." So A6.1
  computed NOT_ESTIMABLE on every corpus project. An inspection report and a quality audit
  report both PRINT the population -- one row per requirement or inspection item, with whether
  it applied, whether it was checked, and whether it passed -- so the table is asked for as a
  table on the `milestones_json` / `lookahead_activities_json` precedent, and this reader maps
  the printed headings onto the field names `canonical_v6.quality_compliance` reads.

  A6.3 Environmental Compliance Rate reached APPLICABILITY_NOT_ESTABLISHED on every corpus
  project because the corpus-assembled structure "deliberately supplies no jurisdiction, no
  permitting authority and no permit id". A jurisdiction, a permitting authority and a permit
  number are things an environmental compliance report STATES ON ITS FACE, in words -- they are
  not a governed structure and asking for them invents nothing. They are now asked for by name,
  beside the permit-condition/observation table that carries the closure semantics.

WHAT IS NOT ASKED FOR. `provenance` in the governed sense is not requested of any document and
is not synthesised: the assembler stamps its own `assembled_by` / `source_document_type` the way
every Run-69 structure does. Neither canonical function requires `provenance` to compute --
A6.1 reads it only to carry it onto a critical exception, A6.3 only to echo it -- so its absence
costs no measurement and inventing a provenance sentence for a document would be worse than
leaving it out. This is the specification's own instruction applied: ask only for what the
document states.

WHAT IS REFUSED, AND EACH REFUSAL IS THE POINT

  * AN UNRECOGNISED OUTCOME WORD SETS NOTHING. The canonical functions read `applicable`,
    `assessed` and `satisfied` as booleans. A cell printing a word this reader does not
    recognise leaves the key ABSENT rather than guessing a direction, and the canonical
    function then puts the row in `unassessed_applicable` -- which is exactly the honest place
    for a requirement whose outcome the document did not state. Nothing defaults to satisfied.
  * ASSESSED IS NOT INVENTED, IT IS READ. Where the document prints its own assessed/inspected
    column, that column decides. Where it does not, a row is `assessed` exactly when it prints
    a RECOGNISED outcome word in its result or status column -- because a row that states an
    outcome is a row that was checked. A row printing a blank, a dash or "not inspected" is
    NOT assessed, enters neither numerator nor denominator, and is reported outstanding.
  * APPLICABILITY IS NEVER MANUFACTURED. Where a row prints no applicability column the key is
    absent, and `canonical_v6` skips a row only on `applicable is False` -- so an absent column
    means the row counts, which is the document's own silence read as "this is on the register",
    not as an exclusion. A row printing "not applicable" is skipped, by the canonical rule.
  * A ROW WITH NO IDENTITY IS PASSED THROUGH. Dropping it would silently shrink the population
    the rate is measured over; it travels with `requirement_id: None`, which is visible in the
    result's own lists.
"""
from __future__ import annotations

import re
from typing import Any

_HEADINGS: dict[str, tuple[str, ...]] = {
    "requirement_id": (
        "requirement id", "requirement no", "requirement number", "requirement ref",
        "requirement", "condition id", "condition no", "permit condition", "condition",
        "observation id", "observation no", "observation", "item id", "item no", "item",
        "inspection item", "checklist item", "clause", "spec section", "id", "no", "ref",
    ),
    "description": (
        "requirement description", "description", "requirement text", "condition description",
        "observation description", "item description", "scope", "detail", "details",
    ),
    "applicable": (
        "applicable", "applicability", "applies", "in scope", "relevant",
    ),
    "assessed": (
        "assessed", "inspected", "verified", "checked", "reviewed", "tested", "witnessed",
        "evaluated",
    ),
    "satisfied": (
        "satisfied", "result", "outcome", "conformance", "conformity", "compliant",
        "compliance", "conforms", "pass fail", "pass or fail", "verdict", "disposition",
        "finding", "closure", "closure status", "status",
    ),
    "criticality": (
        "criticality", "critical", "severity", "priority", "risk level", "classification",
        "grade", "category",
    ),
    "source": (
        "source", "reference", "specification reference", "spec reference", "authority",
        "basis", "origin", "raised by",
    ),
    "status": (
        "status", "state", "closure status", "current status", "disposition",
    ),
    "corrective_action": (
        "corrective action", "corrective actions", "action", "actions", "remedy",
        "remedial action", "action taken", "corrective measure",
    ),
    "period": (
        "period", "reporting period", "report period", "assessment period",
    ),
}

# The outcome vocabulary. These are the words a quality, inspection or environmental document
# actually prints in a result, conformance or closure column. They are ORTHOGRAPHY for two
# states, not a scale, and nothing outside these two lists is mapped in either direction.
_AFFIRMATIVE = frozenset({
    "yes", "y", "true", "satisfied", "satisfactory", "compliant", "in compliance", "conforming",
    "conformed", "conformance", "conforms", "pass", "passed", "passing", "accept", "accepted",
    "acceptable", "closed", "closed out", "complete", "completed", "met", "ok", "okay", "good",
    "resolved", "cleared", "no exception", "no exceptions", "no finding", "no findings",
})
_NEGATIVE = frozenset({
    "no", "n", "false", "unsatisfied", "unsatisfactory", "non compliant", "noncompliant",
    "not compliant", "out of compliance", "non conforming", "nonconforming", "not conforming",
    "nonconformance", "non conformance", "fail", "failed", "failing", "reject", "rejected",
    "open", "outstanding", "unmet", "not met", "incomplete", "unresolved", "overdue",
    "deficient", "deficiency", "violation", "in violation", "exception", "breach",
})
# Words that state, in the document's own terms, that a row was NOT looked at. These make a row
# unassessed; they never make it unsatisfied.
_NOT_ASSESSED = frozenset({
    "not assessed", "not inspected", "not verified", "not checked", "not reviewed",
    "not tested", "pending", "tbd", "to be determined", "scheduled", "deferred", "n a", "na",
    "not yet assessed", "not yet inspected", "awaiting", "not applicable yet", "future",
})


def _norm(value: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value).lower()).split())


def _pick(row: dict, field: str) -> Any:
    normalised = {_norm(k): v for k, v in row.items()}
    for candidate in _HEADINGS[field]:
        if candidate in normalised:
            return normalised[candidate]
    for candidate in _HEADINGS[field]:
        for heading, value in normalised.items():
            if heading.startswith(candidate + " ") or heading.endswith(" " + candidate):
                return value
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    out = " ".join(str(value).split()).strip()
    return out or None


def _tri(value: Any) -> bool | None:
    """True, False, or None where the cell states neither. None is never a direction."""
    if isinstance(value, bool):
        return value
    word = _norm(value) if value is not None else ""
    if not word:
        return None
    if word in _NOT_ASSESSED:
        return None
    if word in _AFFIRMATIVE:
        return True
    if word in _NEGATIVE:
        return False
    return None


def _row(raw: dict) -> dict:
    entry: dict = {"requirement_id": _text(_pick(raw, "requirement_id"))}

    applicable = _tri(_pick(raw, "applicable"))
    if applicable is not None:
        entry["applicable"] = applicable

    outcome_cell = _pick(raw, "satisfied")
    satisfied = _tri(outcome_cell)
    if satisfied is not None:
        entry["satisfied"] = satisfied

    assessed_cell = _pick(raw, "assessed")
    assessed = _tri(assessed_cell)
    if assessed is None and assessed_cell is None:
        # The document printed no assessed column. A row that states a recognised outcome is a
        # row that was checked; a row that states none is not assessed, and is not made so.
        assessed = satisfied is not None
    entry["assessed"] = bool(assessed)

    for key in ("criticality", "source", "status", "corrective_action", "period", "description"):
        text = _text(_pick(raw, key))
        if text is not None:
            entry[key] = text.lower() if key == "criticality" else text
    return entry


def read_requirement_rows(raw: Any) -> list[dict]:
    """
    The requirement, inspection-item, permit-condition or observation rows a document printed,
    mapped onto the field names `canonical_v6.quality_compliance` and
    `canonical_v6.environmental_compliance` read. One dict per printed row, in the table's own
    order. Both canonical functions read the same row shape, so one reader serves both.
    """
    if not isinstance(raw, list):
        return []
    return [_row(r) for r in raw if isinstance(r, dict)]


# =============================================================================================
# RUN 102, SECTION 4.3. THE CORRECTIVE-ACTION REGISTER, WITH ITS DEADLINES AND ITS CLOSURE DATES.
#
# WHY IT IS A SECOND READER AND NOT THE ONE ABOVE. `read_requirement_rows` maps a closure WORD
# onto a satisfied/unsatisfied boolean. A timeliness question cannot be answered from a word: it
# needs the date the action was required to be closed by and the date it was closed. Those are
# two columns the reader above does not look for and would have nowhere to put. So this reader
# maps the register's own headings onto the field names `canonical_v6._timely_closure` reads.
#
# NO DEADLINE IS SUPPLIED, DERIVED OR DEFAULTED HERE. An action whose row prints no required
# deadline reaches the canonical function without one, and the canonical function puts it in
# neither the numerator nor the denominator and counts it separately. That is the honest place
# for an action nobody committed a date to, and the EPA Construction General Permit's seven-day
# figure is NOT substituted for it: it is a fact about one permit regime, not about this
# project's commitments.
#
# NO DATE ARITHMETIC IS PERFORMED HERE OR ANYWHERE ON THIS PATH. The two dates travel as the
# document printed them and the comparison happens once, in the canonical function, on ISO
# strings. No clock is read.
_ACTION_HEADINGS: dict[str, tuple[str, ...]] = {
    "action_id": (
        "corrective action id", "corrective action no", "corrective action number",
        "action id", "action no", "action number", "action ref", "car no", "car id", "car",
        "finding id", "ncr no", "ncr id", "item id", "item no", "id", "no", "ref", "action",
    ),
    "required_deadline": (
        "required deadline", "deadline", "required closure date", "due date", "due",
        "required by", "close by", "closure required by", "corrective action due",
        "required completion date", "target date", "required date",
    ),
    "closure_date": (
        "closure date", "closed date", "date closed", "actual closure date", "completed date",
        "date completed", "resolved date", "date resolved", "closeout date",
    ),
    "severity": (
        "severity", "criticality", "critical", "priority", "risk level", "classification",
        "grade",
    ),
    "deadline_source": (
        "deadline source", "requirement source", "permit reference", "permit condition",
        "authority", "basis", "source", "reference",
    ),
    "description": (
        "description", "finding", "observation", "detail", "details", "corrective action "
        "description", "issue",
    ),
    "status": ("status", "state", "closure status", "disposition", "current status"),
}

#: Words a register prints to say a deadline is not discretionary. Read, never inferred: an
#: action is treated as carrying a mandatory deadline only where the document says so.
_MANDATORY_WORDS = frozenset({
    "mandatory", "regulatory", "permit", "statutory", "required by permit", "enforceable",
    "regulatory deadline", "permit deadline", "non negotiable", "yes",
})


def _action_pick(row: dict, field: str) -> Any:
    wanted = _ACTION_HEADINGS[field]
    normalised = {_norm(k): v for k, v in row.items()}
    for heading in wanted:
        if heading in normalised:
            return normalised[heading]
    for key, value in normalised.items():
        for heading in wanted:
            if heading and heading in key:
                return value
    return None


def _iso(value: Any) -> str | None:
    """A date as the document printed it, kept only when it is already an ISO date."""
    text = _text(value)
    if text is None:
        return None
    text = text.strip()[:10]
    return text if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) else None


def read_corrective_action_rows(raw: Any) -> list[dict]:
    """
    The corrective-action rows a document printed, in the shape `canonical_v6._timely_closure`
    reads. One dict per printed row, in the register's own order.

    A ROW WHOSE DATES ARE NOT ISO DATES CARRIES NO DATE. It is not reformatted or guessed at, so
    it reaches the canonical function as an action with no stated deadline and is counted
    separately rather than being judged on a date this reader invented a reading of.
    """
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        entry: dict[str, Any] = {
            "action_id": _text(_action_pick(r, "action_id")),
            "required_deadline": _iso(_action_pick(r, "required_deadline")),
            "closure_date": _iso(_action_pick(r, "closure_date")),
        }
        for key in ("severity", "deadline_source", "description", "status"):
            text = _text(_action_pick(r, key))
            if text is not None:
                entry[key] = text.lower() if key == "severity" else text
        _src = _norm(entry.get("deadline_source") or "")
        _sev = _norm(entry.get("severity") or "")
        if any(w in _src for w in _MANDATORY_WORDS) or _sev in ("critical", "high"):
            entry["deadline_is_mandatory"] = True
        # THE CLOSURE OUTCOME, WHERE THE STATUS COLUMN STATES IT AND THE DATES DO NOT. A row
        # printing "Open"/"Overdue" with a deadline and no closure date says the action is
        # unclosed; whether its deadline has passed is a further fact and only the word
        # "overdue" states it. Nothing here reads a clock to decide.
        _status = _norm(entry.get("status") or "")
        if _status in ("overdue", "past due", "late", "delinquent"):
            entry["deadline_passed"] = True
        elif _status in ("open", "outstanding", "in progress", "ongoing"):
            entry["deadline_passed"] = False
        out.append(entry)
    return out


def read_critical_failure_rows(raw: Any) -> list[dict]:
    """
    RUN 102, SECTION 4.1. The FAILED items an inspection document itself designates critical, a
    hold point, a life-safety requirement or a commissioning acceptance test.

    NOTHING IS DESIGNATED CRITICAL HERE. The extraction instruction tells the model to include a
    row only where the document designates it, and this reader passes those rows through with
    their identity, the kind stated and the status printed. A row this reader cannot read at all
    is skipped; a row with no identity travels with `item_id: None`, visible in the result.
    """
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        out.append({
            "item_id": _text(_action_pick(r, "action_id")),
            "kind": _text(_pick(r, "criticality")),
            "description": _text(_action_pick(r, "description")),
            "status": _text(_action_pick(r, "status")),
        })
    return out


__all__ = ["read_requirement_rows", "read_corrective_action_rows",
           "read_critical_failure_rows"]
