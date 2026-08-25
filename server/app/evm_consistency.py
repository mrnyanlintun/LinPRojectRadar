"""
THE EVM CONSISTENCY CHECK.

THE DEFECT THIS EXISTS TO CLOSE. A Time-phased Schedule states a planned value to date and a
planned percent complete in the same document. Against a known budget at completion the two
determine each other, and on the render that prompted this run they did not agree: a stated
planned value of 824,370 against a budget at completion of 5,874,620 and a planned percent
complete of 18.47, which implies 1,085,042. The platform extracted both figures, stored both,
and never compared them. Schedule performance is earned value over planned value, so a planned
value that low reads a project as ahead of schedule when the document's own percentages say it
is behind.

WHAT THIS MODULE DOES, AND WHAT IT REFUSES TO DO.

  * IT COMPARES. Where one document states both a value and the percentage that determines it
    against a known budget at completion, the implied value is computed and the two are
    compared. A relative difference above the tolerance is reported as a finding.
  * IT DERIVES NOTHING INTO STORAGE. The document takes precedence. `pv` and `ev` remain
    exactly what the document said. No figure is corrected, substituted, clamped or bounded.
    This module is pure and is called on the READ path, from the stored row, so it cannot
    change a stored figure even in principle.
  * IT CARRIES NO BAND, NO COLOUR, NO SEVERITY AND NO STATUS. A finding is a statement that
    two figures disagree and by how much. It votes on nothing, it cannot move a category, and
    no module reads it. The project manager judges it.

TWO CONDITIONS ON EVERY CHECK.

  1. THE BUDGET AT COMPLETION MUST BE KNOWN. Absence is stored as present-and-null
     (`extraction_merge.select_signal_inputs` initialises every key to None), so an absent
     budget at completion is a None, not a zero. The check does not run and reports nothing.
     An absent budget at completion is not a disagreement.
  2. BOTH FIGURES MUST COME FROM THE SAME DOCUMENT. `signal_inputs.sources` records a
     `documentId` per field (`extraction_merge._source_entry`), which is what establishes it.
     Where a value and its percentage were written by different documents the relation is a
     different situation and is NOT reported here.

THE DENOMINATOR OF THE RELATIVE DIFFERENCE IS THE IMPLIED VALUE, stated once here so no
reader has to infer it: `|stated - implied| / |implied|`. That is the figure the owner's order
quotes (824,370 against an implied 1,085,042.314 is 24.02 per cent), and the tolerance is read
against it. The other reading, relative to the stated value, gives 31.62 per cent for the same
pair; it is not used, and the wording on every surface says "differ by" rather than naming a
base, so nothing on a surface depends on which was chosen.

WORDING. RUN 59: no markdown document governs this, and the identifier prohibition once cited
here was SUPERSEDED on 2026-08-23. What governs is stated directly: no em dash; state what
disagrees and by how much; do not tell the project manager what to conclude and do not assert
which figure is wrong. A module identifier would be permitted and is simply not used, because
the sentence names the two figures rather than the computation that compared them.
"""
from __future__ import annotations

from typing import Any

__all__ = [
    "CONSISTENCY_RELATIONS",
    "TOLERANCE",
    "consistency_findings",
]

#: A relative difference ABOVE this is a disagreement. At or below it, nothing is reported.
#: The owner's ruling 2.3, as a fraction rather than a percentage so no conversion sits
#: between the ruling and the comparison.
TOLERANCE = 0.02

#: The document types that can state one of these pairs, named as a reader sees them. Mirrors
#: the participant-facing labels in `assets/js/signals.js`; a type absent here prints its own
#: key rather than being dropped, so a new writer is visible instead of silently unnamed.
_DOC_TYPE_LABEL: dict[str, str] = {
    "time_phased_schedule": "Time-phased Schedule / Baseline",
    "schedule_update": "Schedule Update / Look-ahead",
    "monthly_report": "Monthly Progress Report",
    "pay_application": "Pay Application (G702)",
    "schedule_of_values": "Schedule of Values",
    "contract_value": "Contract / Original Agreement",
    "change_order": "Change Order",
}

#: The relations checked. Each is a (value, percentage) pair that ONE document states together
#: and that determine each other against the budget at completion:
#:
#:   pv  x  plannedPctComplete   time_phased_schedule, schedule_update, monthly_report
#:   ev  x  actualPctComplete    pay_application, monthly_report
#:
#: Both were established by reading `extraction_merge._NUMERIC_EMISSIONS` document type by
#: document type; the sweep and every pair it rejected are recorded in the Run 47 report.
CONSISTENCY_RELATIONS: tuple[dict[str, str], ...] = (
    {
        "value_field": "pv",
        "pct_field": "plannedPctComplete",
        "value_label": "planned value to date",
        "pct_label": "planned percent complete",
    },
    {
        "value_field": "ev",
        "pct_field": "actualPctComplete",
        "value_label": "earned value to date",
        "pct_label": "actual percent complete",
    },
)


def _num(v: Any) -> float | None:
    """A readable number, or None. `bool` is not a number here; None stays None."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    f = float(v)
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def _money(v: float) -> str:
    return f"{v:,.0f}"


def _pct_stated(v: float) -> str:
    """A stated percentage as the document gave it, trailing zeroes trimmed, never rounded up."""
    s = f"{v:,.2f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def _pct_diff(v: float) -> str:
    """The relative difference. Two decimals below ten so 2.01 is not printed as 2.0."""
    return f"{v:,.2f}" if v < 10 else f"{v:,.1f}"


def _same_document(sources: dict, a: str, b: str) -> tuple[bool, str | None, str | None, str | None]:
    """(both from one document, documentId, docType, documentVersion).

    `_source_entry` omits `documentId` when the observation carried none, so two records that
    BOTH lack one are not thereby the same document. Absence is never treated as a match.
    """
    sa = sources.get(a) if isinstance(sources, dict) else None
    sb = sources.get(b) if isinstance(sources, dict) else None
    if not isinstance(sa, dict) or not isinstance(sb, dict):
        return False, None, None, None
    ida, idb = sa.get("documentId"), sb.get("documentId")
    if not ida or not idb or str(ida) != str(idb):
        return False, None, None, None
    return True, str(ida), sa.get("docType"), sa.get("documentVersion")


def consistency_findings(signal_inputs: dict | None,
                         period: int | None = None) -> list[dict[str, Any]]:
    """Every disagreement this row holds, in relation order. Pure; reads, never writes.

    Each finding carries the field, the stated value as stored, the implied value as computed,
    the relative difference as a percentage, the document that stated both figures by type and
    identity, the period, and the sentence the surfaces print. No band, no colour, no severity.
    Returns [] when there is nothing to report, which is also what an absent budget at
    completion, an absent figure, and a value-and-percentage split across two documents give.
    """
    si = signal_inputs or {}
    if not isinstance(si, dict):
        return []
    sources = si.get("sources") or {}
    bac = _num(si.get("bac"))
    # Condition 1: the budget at completion must be known. A zero cannot determine a value
    # either, and dividing by an implied zero is not a disagreement, so both are refusals.
    if bac is None or bac == 0:
        return []

    out: list[dict[str, Any]] = []
    for rel in CONSISTENCY_RELATIONS:
        stated = _num(si.get(rel["value_field"]))
        pct = _num(si.get(rel["pct_field"]))
        if stated is None or pct is None:
            continue
        # Condition 2: both figures from the SAME document.
        same, document_id, doc_type, document_version = _same_document(
            sources, rel["value_field"], rel["pct_field"])
        if not same:
            continue
        implied = bac * pct / 100.0
        if implied == 0:
            continue
        rel_diff = abs(stated - implied) / abs(implied)
        if rel_diff <= TOLERANCE:
            continue

        diff_pct = rel_diff * 100.0
        doc_name = _DOC_TYPE_LABEL.get(str(doc_type), str(doc_type))
        sentence = (
            (f"In period {period}, t" if period is not None else "T")
            + f"he {doc_name} states a {rel['value_label']} of {_money(stated)} and a "
              f"{rel['pct_label']} of {_pct_stated(pct)}. Applied to the budget at completion "
              f"of {_money(bac)}, that percentage implies a {rel['value_label']} of "
              f"{_money(implied)}. The stated and implied figures differ by "
              f"{_pct_diff(diff_pct)} percent. Both figures were read from the same document, "
              f"and both are reported as the document stated them."
        )
        out.append({
            "field": rel["value_field"],
            "fieldLabel": rel["value_label"],
            "percentField": rel["pct_field"],
            "percentLabel": rel["pct_label"],
            "statedValue": stated,
            "impliedValue": implied,
            "percentStated": pct,
            "bac": bac,
            "differencePct": diff_pct,
            "documentType": doc_type,
            "documentLabel": doc_name,
            "documentId": document_id,
            "documentVersion": document_version,
            "period": period,
            "sentence": sentence,
        })
    return out
