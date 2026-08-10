"""
A notice is an event, not a score: what it claims, when it was served, and what clock it started.

WHY THIS FILE EXISTS. `correspondence_notice` extracted a document risk score and a date, so a
notice served on a project was, to this platform, a number between zero and one. A notice is not
a number. Someone served it, on someone, it asserts something, and under the contract form it
starts a clock that can extinguish a right. That is the same discrete-event treatment change
orders already have, and it is what this module supplies the vocabulary for.

THE DEADLINE IS DERIVED FROM THE NAMED FORM, NEVER INVENTED. `deadline_for` returns a date only
when the document itself named a contract form this table knows and a notice type that form puts
a fixed period on. Where the form is not established, no deadline is stated and the reason is
carried instead. A deadline is the kind of number a reader will act on, and one derived from a
form the document never named would be the same fabrication as an eightieth percentile with no
distribution behind it.

PERIODS ARE TRANSCRIBED FROM `training_us_contract_regimes.md`, WITH ITS CAVEATS INTACT.
Clause numbers are cited and no clause text is reproduced: A201 and ConsensusDocs are licensed
documents. That file also records, and this file inherits, that the A201 and ConsensusDocs
periods come from secondary law-firm summaries rather than the licensed documents, and that
contract periods are routinely amended in negotiation, so a real project may not match its own
form. Both statements are carried into `PERIOD_CAVEAT` and are printed wherever a deadline is.

THREE TRAPS FROM THAT DOCUMENT ARE ENCODED AS BEHAVIOUR, NOT AS COMMENTS.

  1. A201's differing-site-conditions period is FOURTEEN days, not twenty-one. It was twenty-one
     in the 2007 edition and was shortened in 2017, and the document says experienced people get
     this wrong from memory. The table carries 14 and a check pins it.

  2. ConsensusDocs is a TWO-STEP clock: notice within fourteen days, then supporting
     documentation within twenty-one days AFTER THE NOTICE, not after the occurrence. A single
     deadline would silently drop the second step, so the second step is its own field with its
     own base date.

  3. The federal twenty-day figure is NOT a notice deadline. It is a cost LOOKBACK: nothing is
     time-barred, but costs incurred more than twenty days before written notice are
     unrecoverable. Returning it as a deadline would tell a reader their claim dies on a date
     when it does not. It is a separate kind, labelled as a lookback, and `deadline_for` returns
     no deadline for the federal form.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

# What a notice is ABOUT, which is what decides which clock applies.
CLAIM = "claim"
DIFFERING_SITE_CONDITION = "differing_site_condition"
NOTICE_TYPES = (CLAIM, DIFFERING_SITE_CONDITION)

# Carried onto every derived deadline. The provenance limit is real and a reader acting on a
# date needs it beside the date, not in a footnote somewhere else.
PERIOD_CAVEAT = (
    "Periods are the published defaults for the named form and are routinely amended in "
    "negotiation, so the executed contract governs. The A201 and ConsensusDocs periods are "
    "taken from secondary summaries rather than the licensed documents."
)


@dataclass(frozen=True)
class NoticePeriod:
    """One clock a contract form starts, with the clause it comes from."""

    days: int | None
    citation: str
    # 'deadline' is a date by which something must be done. 'lookback' is a cost cutoff measured
    # BACKWARD from the notice, which bars no claim and must never be printed as a deadline.
    kind: str
    note: str = ""


DEADLINE = "deadline"
LOOKBACK = "lookback"

# The forms this platform recognises, and what each puts on a notice. A form absent from here is
# a form whose periods this platform does not hold, and a notice naming it gets no deadline.
CONTRACT_FORMS: dict[str, dict[str, Any]] = {
    "A201-2017": {
        "label": "AIA A201-2017",
        "periods": {
            CLAIM: NoticePeriod(21, "A201-2017 Section 15.1.3.1", DEADLINE),
            # TRAP 1. Fourteen, not the 2007 edition's twenty-one.
            DIFFERING_SITE_CONDITION: NoticePeriod(
                14, "A201-2017 Section 3.7.4", DEADLINE,
                "Measured from first observance, and shortened from 21 days in the 2007 "
                "edition."),
        },
        "second_step": None,
    },
    "ConsensusDocs 200": {
        "label": "ConsensusDocs 200",
        "periods": {
            CLAIM: NoticePeriod(14, "ConsensusDocs 200 Section 8.4", DEADLINE),
            # The form requires affected work to stop and prompt written notice, and puts no
            # day count on it. No count means no derived date, which is stated rather than
            # filled in with a neighbouring form's number.
            DIFFERING_SITE_CONDITION: NoticePeriod(
                None, "ConsensusDocs 200 Section 3.16.2", DEADLINE,
                "The form requires affected work to stop and prompt written notice, and states "
                "no fixed day count."),
        },
        # TRAP 2. The second step runs from the NOTICE, not from the occurrence.
        "second_step": {
            "days": 21, "of": CLAIM, "from": "notice",
            "citation": "ConsensusDocs 200 Section 8.4",
            "what": "supporting documentation",
        },
    },
    "Federal FAR": {
        "label": "Federal (FAR)",
        "periods": {
            # TRAP 3. Twenty days is a cost cutoff, not a deadline. Nothing is time-barred.
            CLAIM: NoticePeriod(
                20, "FAR 52.243-4(d)", LOOKBACK,
                "Not a notice deadline. The changes clause sets no fixed notice period; costs "
                "incurred more than 20 days before written notice are not recoverable."),
            DIFFERING_SITE_CONDITION: NoticePeriod(
                None, "FAR 52.236-2(a)", DEADLINE,
                "Promptly, and before the conditions are disturbed. No fixed day count."),
        },
        "second_step": None,
    },
}

# How a document might name each form. Matched against the notice's own text, lowercased. Kept
# deliberately tight: "federal" alone is not enough to name a contract form, and a false match
# would produce a confident deadline from the wrong regime.
_FORM_PHRASES: dict[str, tuple[str, ...]] = {
    "A201-2017": ("a201", "aia a201", "aia document a201", "general conditions of the contract "
                  "for construction"),
    "ConsensusDocs 200": ("consensusdocs 200", "consensusdocs200", "consensus docs 200",
                          "consensusdocs"),
    "Federal FAR": ("far 52.243", "far 52.236", "federal acquisition regulation", "far clause",
                    "48 cfr"),
}

_TYPE_PHRASES: dict[str, tuple[str, ...]] = {
    DIFFERING_SITE_CONDITION: ("differing site condition", "differing site conditions",
                               "concealed condition", "unforeseen ground condition",
                               "changed condition"),
    CLAIM: ("notice of claim", "claim for additional", "claim for an extension",
            "request for change order", "notice of delay", "change in the work", "claim"),
}


def identify_form(text: Any) -> str | None:
    """
    Which contract form the document NAMES, or None.

    Read from the document's own words. A project-level default is deliberately not consulted,
    because this platform holds none, and inventing one here would put a deadline on a notice
    from a form nobody stated.
    """
    lowered = str(text or "").lower()
    for form, phrases in _FORM_PHRASES.items():
        if any(phrase in lowered for phrase in phrases):
            return form
    return None


def identify_notice_type(text: Any) -> str | None:
    """
    What the notice is about, or None. Differing site conditions is tested first because it is
    the more specific reading of a document that says both.
    """
    lowered = str(text or "").lower()
    for notice_type in (DIFFERING_SITE_CONDITION, CLAIM):
        if any(phrase in lowered for phrase in _TYPE_PHRASES[notice_type]):
            return notice_type
    return None


def deadline_for(form: str | None, notice_type: str | None,
                 served: date | None) -> dict[str, Any]:
    """
    The clock this notice started, or a statement of why none can be given.

    Returns `{stated, date, days, citation, kind, basis, caveat}` where `stated` is False
    whenever any of the three inputs is missing or the form puts no fixed count on this notice
    type. `date` is only ever present when `stated` is True AND the period is a DEADLINE: a
    lookback has a day count and no deadline date, and conflating the two would tell a reader a
    claim expires when it does not.
    """
    def unstated(reason: str) -> dict[str, Any]:
        return {"stated": False, "date": None, "days": None, "citation": None,
                "kind": None, "basis": reason, "caveat": None}

    if form is None:
        return unstated("the notice does not name a contract form this platform holds periods "
                        "for, so no deadline is derived")
    spec = CONTRACT_FORMS.get(form)
    if spec is None:
        return unstated(f"this platform holds no periods for the form {form!r}")
    if notice_type is None:
        return unstated(f"the notice names {spec['label']} but what it is a notice OF could not "
                        f"be established, and the period depends on that")
    period = spec["periods"].get(notice_type)
    if period is None:
        return unstated(f"{spec['label']} sets no period this platform holds for this kind of "
                        f"notice")
    if period.days is None:
        return {"stated": False, "date": None, "days": None, "citation": period.citation,
                "kind": period.kind,
                "basis": f"{spec['label']} states no fixed day count here. {period.note}".strip(),
                "caveat": PERIOD_CAVEAT}
    if period.kind == LOOKBACK:
        # A cost cutoff, and it is reported as one. No date, because nothing expires.
        return {"stated": True, "date": None, "days": period.days,
                "citation": period.citation, "kind": LOOKBACK,
                "basis": (f"{spec['label']} sets no fixed notice period. {period.note}").strip(),
                "caveat": PERIOD_CAVEAT}
    if served is None:
        return unstated(f"{spec['label']} sets {period.days} days ({period.citation}), but the "
                        f"date the notice was served could not be read, so no date is derived")
    return {
        "stated": True,
        "date": (served + timedelta(days=period.days)).isoformat(),
        "days": period.days,
        "citation": period.citation,
        "kind": DEADLINE,
        "basis": (f"{period.days} days from {served.isoformat()} under {period.citation}."
                  + (" " + period.note if period.note else "")),
        "caveat": PERIOD_CAVEAT,
    }


def second_step_for(form: str | None, notice_type: str | None,
                    served: date | None) -> dict[str, Any] | None:
    """
    The SECOND clock, where the form has one, or None.

    ConsensusDocs is the case: notice within fourteen days, then supporting documentation within
    twenty-one days after THAT NOTICE. Reporting only the first would tell a reader they were
    safe once they had given notice, which the document names as the trap that loses the right.
    """
    spec = CONTRACT_FORMS.get(form or "")
    if not spec or not spec.get("second_step"):
        return None
    step = spec["second_step"]
    if notice_type != step["of"]:
        return None
    if served is None:
        return {"stated": False, "date": None, "days": step["days"],
                "citation": step["citation"], "what": step["what"],
                "basis": (f"{step['days']} days for {step['what']} after the notice, but the "
                          f"date the notice was served could not be read"),
                "caveat": PERIOD_CAVEAT}
    return {
        "stated": True,
        "date": (served + timedelta(days=step["days"])).isoformat(),
        "days": step["days"], "citation": step["citation"], "what": step["what"],
        "basis": (f"{step['days']} days for {step['what']} after the notice served "
                  f"{served.isoformat()}, under {step['citation']}. The clock runs from the "
                  f"notice, not from the occurrence."),
        "caveat": PERIOD_CAVEAT,
    }


__all__ = [
    "CLAIM", "CONTRACT_FORMS", "DEADLINE", "DIFFERING_SITE_CONDITION", "LOOKBACK",
    "NOTICE_TYPES", "NoticePeriod", "PERIOD_CAVEAT", "deadline_for", "identify_form",
    "identify_notice_type", "second_step_for",
]
