"""
RUN 111. WHAT THE SIX WAITING MODULES ASK FOR, IN PLAIN TERMS, AND HOW A STRUCTURE IS COMPOSED.

`recognition.py` is the reader. This file is what it reads FOR: one `StructureRecipe` per module
that can be served, each naming its quantities the way section 4.1 requires -- what the quantity
is, its units, what it is a proportion of, and what disqualifies a candidate -- and a `build`
that PLACES the recognised values into the shape the canonical function already reads.

NO ARITHMETIC HAPPENS IN THIS FILE. No band, no threshold, no category posture and no project
status is decided here or anywhere downstream of a recognised value that was not already decided
in code before this run. A structure composed here is handed to exactly the same `canonical_v4`
function, and exactly the same ladder, that serves a structure typed in through the governed
intake.

ALL OR NOTHING, PER STRUCTURE, which is Run 80's rule applied here. Where any required quantity
is not recognised, `build` returns None, no key is written, and the module abstains on its own
guard with its own words -- the sentence that already names, in plain terms, what it looked for.
A partially assembled structure would make a canonical function refuse with a WORSE message than
the one the module already prints.

=================================================================================================
THE TWO MODULES THAT HAVE NO RECIPE HERE, AND WHY
=================================================================================================

A1.11 INDEPENDENT EAC RECONCILIATION. Section 4 of the owner's order rules it out and it is
right to. `independentEacPair` is not a figure a document states: it is the CLAIM that a second
forecast at completion was prepared independently of the first. Two numbers in the evidence store
do not establish that, and a model asked "which of these is the independent forecast" would be
answering a question about provenance from data that carries none. Nothing here attempts it.

A4.7 DISPUTE ESCALATION INDEX. The register of issues could in principle be recognised; the
PROCESS cannot. `canonical_v4.dispute_escalation` is explicit that the ladder "is not universal
and is not defined here" -- the stages, their order and their escalation class arrive on the
structure because whoever governs the process declares them. That is authority of the same kind
as `signalWeightPolicy`, and recognising it from a document would be inventing a governance
artefact. Where a project supplies the process through the governed intake, the issue register
becomes a candidate for a later run; it is not attempted from evidence alone.
"""

from __future__ import annotations

from typing import Any

from .recognition import Match, QuantitySpec, StructureRecipe

# =============================================================================================
# A4.8 SUBCONTRACTOR PERFORMANCE -- the one the evidence store already answers
# =============================================================================================

_A48 = (
    QuantitySpec(
        quantity_id="A4.8.firm_identity",
        what_it_is=("the name or identifier of each subcontracting firm whose performance was "
                    "assessed, one entry per firm, exactly as the assessment table names it"),
        units="a name or identifier, not a number",
        columnar=True,
        disqualifiers=(
            "it names a trade, a work package or a scope of work rather than a firm",
            "it is a score, a rating or a date rather than an identity",
        ),
    ),
    QuantitySpec(
        quantity_id="A4.8.assessment_period",
        what_it_is=("the period each firm's assessment covers, one entry per firm, as the "
                    "assessment table states it"),
        units="a period label such as a month or a quarter",
        columnar=True,
        disqualifiers=(
            "it is the date the report was written rather than the period assessed",
        ),
    ),
    QuantitySpec(
        quantity_id="A4.8.reported_rating",
        what_it_is=("the performance rating the assessment records for each firm, one entry per "
                    "firm, exactly as the assessment states it -- a rating word or a rating "
                    "score, whichever the assessment used"),
        units="a rating label, or a score out of one hundred",
        columnar=True,
        disqualifiers=(
            "it is a count of deliveries, incidents, defects or any other event",
            "it is a share, percentage or ratio computed from counts rather than a rating "
            "recorded by an assessor",
            "it is a comment, a narrative note or a recommendation",
        ),
    ),
    QuantitySpec(
        quantity_id="A4.8.rating_scale",
        what_it_is=("the name of the rating scale the assessment's ratings are recorded on, as "
                    "the assessment declares it"),
        units="the name of a scale",
        disqualifiers=("it is a rating rather than the name of the scale ratings are on",),
    ),
    QuantitySpec(
        quantity_id="A4.8.report_date",
        what_it_is="the date the subcontractor performance assessment itself was issued",
        units="a calendar date",
        disqualifiers=("it is the period assessed rather than the date of issue",),
    ),
    QuantitySpec(
        quantity_id="A4.8.report_version",
        what_it_is=("the version, revision or issue number of the subcontractor performance "
                    "assessment"),
        units="a version identifier",
        disqualifiers=("it is a version of some other document",),
    ),
)


def _column(m: Match) -> list:
    """A recognised column's values, in the table's own printed row order."""
    return list(m.value) if isinstance(m.value, list) else []


def _scalar_text(m: Match) -> str:
    return "" if m.value is None else str(m.value).strip()


def _build_a48(matches: dict[str, Match]) -> dict[str, Any] | None:
    """
    `subcontractorAssessments` in the shape `canonical_v4.subcontractor_reported_ratings` reads.

    THE ONLY DECISION MADE HERE IS A TYPE DECISION, and it is made on what the document printed:
    a rating that parses as a number is placed in `rating_score`, anything else in
    `rating_label`. That is transcription, not interpretation -- which of the four postures a
    label or a score maps onto stays entirely in `canonical_v4`, on the owner's Run 107 ladder,
    which this file does not read and cannot reach.
    """
    firms = _column(matches["A4.8.firm_identity"])
    periods = _column(matches["A4.8.assessment_period"])
    ratings = _column(matches["A4.8.reported_rating"])
    if not firms or not (len(firms) == len(periods) == len(ratings)):
        # THREE COLUMNS OF DIFFERENT LENGTHS ARE NOT ONE TABLE. Padding them to a common length
        # would attach a rating to a firm that was not rated it, so nothing is assembled.
        return None
    rows = []
    for name, period, rating in zip(firms, periods, ratings):
        if name is None or str(name).strip() == "":
            return None
        row: dict[str, Any] = {"subcontractor_id": str(name).strip(),
                               "assessment_period": str(period or "").strip()}
        try:
            row["rating_score"] = float(str(rating).strip())
        except (TypeError, ValueError):
            row["rating_label"] = str(rating or "").strip()
        rows.append(row)
    src = matches["A4.8.reported_rating"]
    return {
        "reported_ratings": rows,
        "rating_scale": _scalar_text(matches["A4.8.rating_scale"]),
        "report_date": _scalar_text(matches["A4.8.report_date"]),
        "report_version": _scalar_text(matches["A4.8.report_version"]),
        # THE SOURCE IS NOT RECOGNISED AND IS NOT INVENTED. It is the platform's own record of
        # WHICH DOCUMENT the recognised values were read out of, which is a fact this code knows
        # and no model was asked about.
        "source": (f"{src.doc_type or 'document'} {src.filename or ''} "
                   f"(document {src.document_id}, sha256 {str(src.sha256 or '')[:12]}), "
                   f"read by recognition of the labels it printed").strip(),
        "assembled_by": "run111 recognition of stored evidence",
        "source_document_type": src.doc_type,
        "source_document_id": src.document_id,
    }


# =============================================================================================
# A4.5, A4.6, A4.9 -- DECLARED, SO THE PLATFORM SAYS WHAT IT LOOKED FOR
# =============================================================================================
#
# Each of these is a REGISTER: a row per event, per change, per item. The census fixture's
# evidence store holds AGGREGATE COUNTS for all three -- a weather-day count, a change-order
# count, a count of long-lead items at risk -- and no register. A count is not a register, and
# turning one into the other would be inventing the rows, which section 4 forbids absolutely.
#
# They are declared here anyway, and asked, because the platform must SAY WHAT IT LOOKED FOR
# rather than be silent about six modules. On evidence that holds no register the recognition
# log records, per quantity, that nothing answered it -- which is the diagnosis the owner needs
# in order to know that the fix is a document that prints the register, not a change to this
# code.

_A45 = (
    QuantitySpec(
        quantity_id="A4.5.event_identity",
        what_it_is=("the identifier of each individual weather event recorded against the "
                    "project, one entry per event"),
        units="an identifier", columnar=True,
        disqualifiers=("it is a count of weather days rather than a list of events",),
    ),
    QuantitySpec(
        quantity_id="A4.5.event_lost_days",
        what_it_is="the working time actually lost to each individual weather event",
        units="days", columnar=True,
        disqualifiers=("it is a total across all events rather than a per-event figure",
                       "it is days claimed or days approved rather than time actually lost"),
    ),
    QuantitySpec(
        quantity_id="A4.5.event_activity",
        what_it_is="the schedule activity each individual weather event stopped work on",
        units="an activity identifier", columnar=True,
    ),
    QuantitySpec(
        quantity_id="A4.5.event_path",
        what_it_is=("the schedule path each stopped activity sits on, so events on one path can "
                    "be counted together"),
        units="a path identifier", columnar=True,
    ),
    QuantitySpec(
        quantity_id="A4.5.event_float",
        what_it_is="the float available on the path each stopped activity sits on",
        units="days", columnar=True,
    ),
    QuantitySpec(
        quantity_id="A4.5.allowance_remaining",
        what_it_is=("the weather allowance the contract calendar grants that has NOT yet been "
                    "used up"),
        units="days",
        disqualifiers=("it is the total allowance granted rather than what remains of it",
                       "it is days claimed, approved or lost"),
    ),
)

_A46 = (
    QuantitySpec(
        quantity_id="A4.6.change_identity",
        what_it_is="the identifier of each individual change recorded on the project",
        units="an identifier", columnar=True,
        disqualifiers=("it is a count of changes rather than a list of them",),
    ),
    QuantitySpec(
        quantity_id="A4.6.change_value",
        what_it_is="the value of each individual change, as the change register states it",
        units="currency", columnar=True,
        disqualifiers=("it is a running or revised contract total rather than one change",),
    ),
    QuantitySpec(
        quantity_id="A4.6.change_direction",
        what_it_is=("whether each individual change adds to or takes away from the contract"),
        units="a direction word", columnar=True,
    ),
    QuantitySpec(
        quantity_id="A4.6.change_type",
        what_it_is="the type each individual change is classified as",
        units="a type word", columnar=True,
    ),
    QuantitySpec(
        quantity_id="A4.6.change_cause",
        what_it_is="the cause recorded against each individual change",
        units="a cause word", columnar=True,
    ),
    QuantitySpec(
        quantity_id="A4.6.exposure_days",
        what_it_is=("the span of time the change register covers, over which a frequency of "
                    "changes is being measured"),
        units="days",
        disqualifiers=("it is a remaining duration or a total project duration rather than the "
                       "span the register covers",),
    ),
    QuantitySpec(
        quantity_id="A4.6.baseline_contract_value",
        what_it_is="the baseline contract value the change magnitude is measured against",
        units="currency", proportion_of="the value of the changes taken together",
        disqualifiers=("it is the revised or current contract sum rather than the baseline",),
    ),
)

_A49 = (
    QuantitySpec(
        quantity_id="A4.9.item_identity",
        what_it_is=("the identifier of each individual long-lead procurement item, one entry "
                    "per item"),
        units="an identifier", columnar=True,
        disqualifiers=("it is a count of items rather than a list of them",),
    ),
    QuantitySpec(
        quantity_id="A4.9.required_on_site",
        what_it_is="the date each individual item is required on site",
        units="a calendar date or a day number", columnar=True,
    ),
    QuantitySpec(
        quantity_id="A4.9.forecast_delivery",
        what_it_is="the date each individual item is currently forecast to arrive",
        units="a calendar date or a day number", columnar=True,
        disqualifiers=("it is the date originally promised rather than the current forecast",),
    ),
    QuantitySpec(
        quantity_id="A4.9.item_float",
        what_it_is="the float available on the activity each individual item feeds",
        units="days", columnar=True,
    ),
)


def _register_absent(_matches: dict[str, Match]) -> dict[str, Any] | None:
    """
    A4.5, A4.6 and A4.9 compose only from a REGISTER, and `_ask_all` never calls a builder unless
    every required quantity was recognised. Reaching here means the register's columns were all
    recognised, and composing them is a build this run does not have a document to exercise: it
    returns None rather than assemble a shape nothing has ever been run against.
    """
    return None


RECIPES: dict[str, StructureRecipe] = {
    "A4.8": StructureRecipe(
        module_id="A4.8", structure_key="subcontractorAssessments",
        what_the_module_needs=("each firm assessed, the period it was assessed for, the rating "
                               "recorded against it, and the scale that rating is on"),
        quantities=_A48, build=_build_a48),
    "A4.5": StructureRecipe(
        module_id="A4.5", structure_key="weatherImpactEvents",
        what_the_module_needs=("each weather event, the activity and path it stopped, the time "
                               "actually lost, and the weather allowance still remaining"),
        quantities=_A45, build=_register_absent),
    "A4.6": StructureRecipe(
        module_id="A4.6", structure_key="changeEventRegister",
        what_the_module_needs=("each change with its value, direction, type and cause, the span "
                               "of time the register covers, and the baseline contract value"),
        quantities=_A46, build=_register_absent),
    "A4.9": StructureRecipe(
        module_id="A4.9", structure_key="procurementItems",
        what_the_module_needs=("each long-lead item with the date it is required on site, the "
                               "date it is forecast to arrive, and the float on the activity it "
                               "feeds"),
        quantities=_A49, build=_register_absent),
}
