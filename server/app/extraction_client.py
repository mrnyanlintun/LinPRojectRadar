"""
The document-extraction model call, and the concurrency around it.

ONE CALL PER UNIQUE DOCUMENT, EVER

Extraction is cached on the sha256 of the bytes (see `documents` in migration 0009), so this
module is only ever reached for a document the platform has genuinely never seen. That is why
it uses the most accurate model available rather than the fastest: a wrong EV figure does not
slow the study down, it corrupts a data point that a participant then judges. The cost of the
strong model is paid once per document for the lifetime of the platform.

WHY urllib AND NOT THE anthropic SDK

`server/requirements.txt` is pinned and the build has already been bitten twice by
interpreter-specific wheels (see the note above `new_ulid` in research_models.py). The API call
is one POST with a JSON body; the SDK would add a dependency and a version surface to a build
that gains nothing from either. `urllib.request` is stdlib and cannot break the Render build.

PER-DOC-TYPE FIELD LISTS, NOT ONE UNIVERSAL LIST

`extraction_fields.extraction_fields_for` returns a short list per document type. Asking a
pay application for all 87 known fields invites the model to fill in plausible values for
fields the document does not contain, and every one of those becomes a fabricated project
controls input. The narrow list is an accuracy measure, not a token-saving one.

PARALLELISM

Sequential extraction of 27 documents at ~5s each is over two minutes; ten concurrent is
roughly fifteen seconds. The work is entirely network-bound, so a thread pool is the right
tool and the GIL is irrelevant. This is in the first implementation rather than a later
optimisation because the sequential version is unusable at a realistic period's document count.

THE STUB

`ANTHROPIC_API_KEY` is set on Render but is not available in local verification. When it is
absent, `StubExtractor` serves recorded extractions keyed by sha256 and refuses anything it has
not been given. It exists so the caching, concurrency, assembly and storage paths can be
exercised deterministically; it is NOT a fallback that silently degrades production. A missing
key in an environment that expects real extraction is an error, not a quiet substitution — see
`build_extractor`.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from . import ai_provider
from .extraction_fields import (
    CLASSIFY_HINTS,
    DOC_TYPES,
    UNMAPPED,
    extraction_fields_for,
    guess_type_from_filename,
    is_mapped,
)

log = logging.getLogger("opus-gubernatio-server")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# Accuracy over speed, deliberately. See the module docstring.
# RUN 113. DERIVED FROM THE PROVIDER TABLE, NEVER RESTATED. Runs 93-112 left this a
# LITERAL COPY of the Anthropic default, so when Run 113 repointed the table this line
# would have silently gone stale -- a second, wrong answer to the question 'what model'.
# It is now the SAME OBJECT the table holds, so the divergence class cannot recur.
EXTRACTION_MODEL = ai_provider.PROVIDERS["anthropic"]["models"]["extraction"]

# Ten concurrent calls. Chosen to sit well inside the provider's per-minute limits while still
# collapsing a 27-document period from >2 minutes to well under half a minute.
DEFAULT_CONCURRENCY = 10

MAX_TOKENS = 1536
REQUEST_TIMEOUT_S = 120


class ExtractionError(RuntimeError):
    """Raised when a document could not be extracted. Never swallowed into a null result."""


class TruncatedResponseError(ExtractionError):
    """
    The model's answer was CUT OFF, not malformed. These are different failures and the
    difference is actionable.

    A real schedule document failed three times with `model response was not JSON: '{\\n
    "planned_percent_complete": null, ... "activities_planned": 29,\\n "activities_constrain'`.
    That response is valid JSON, truncated mid-key. "Not JSON" describes a model that answered
    with prose or with something else entirely, and the honest response to that is to look at
    what it said; the honest response to a cut-off answer is to ask for less, because retrying
    truncates in exactly the same place every time. Three retries were spent on the wrong one.
    """


def describe_json_truncation(text: str) -> str | None:
    """
    `None` if `text` is a complete JSON value; otherwise a sentence NAMING WHERE IT STOPPED.

    Scans once, tracking string state, escapes and bracket depth, and remembering the most
    recent object key. Unterminated structure at the end means the text ran out before the value
    did, which is truncation and not a syntax error.

    Reporting the key matters more than reporting the offset. "It stopped while reading
    activities_constrained" tells a reader which field ran the response out of budget; "invalid
    JSON at character 412" tells them nothing they can act on.
    """
    depth = 0
    in_string = False
    escaped = False
    current: list[str] = []
    last_string: str | None = None
    last_key: str | None = None
    expecting_key = False
    saw_value = False
    for ch in text or "":
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
                last_string = "".join(current)
                if expecting_key:
                    last_key = last_string
            else:
                current.append(ch)
            continue
        if ch == '"':
            in_string, current = True, []
            continue
        if ch in "{[":
            depth += 1
            expecting_key = ch == "{"
            saw_value = True
            continue
        if ch in "}]":
            depth -= 1
            expecting_key = False
            continue
        if ch == ":":
            expecting_key = False
            continue
        if ch == ",":
            expecting_key = depth > 0
            continue
        if not ch.isspace():
            saw_value = True
    if not saw_value:
        return None
    if in_string:
        partial = "".join(current)
        if expecting_key:
            return (
                "the model's answer was cut off while writing a field name, after "
                f"{last_key!r}; the name it had reached was {partial!r}"
                if last_key else
                f"the model's answer was cut off while writing a field name, {partial!r}"
            )
        target = last_key or last_string
        return (
            f"the model's answer was cut off while writing the value of {target!r}"
            if target else "the model's answer was cut off inside a quoted value"
        )
    if depth > 0:
        return (
            f"the model's answer was cut off after the field {last_key!r}"
            if last_key else "the model's answer was cut off before the object was closed"
        )
    return None


# --------------------------------------------------------------------------- prompt


def build_prompt(doc_type: str, fields: list[str]) -> str:
    """
    Port of the legacy per-type extraction prompt (.gs `extractSignals_`, lines 846-849).

    Three deliberate additions to the legacy text, each flagged here because it changes model
    behaviour:

    1. `document_risk_score` is constrained to 0..1. The legacy prompt never constrained it,
       while `sim.js` clamps it to [0,1] and bands at 0.30/0.70, and `decision.js:80` carries a
       standing comment that the field "carries inconsistent scales — raw counts as well". An
       unconstrained score is silently misread as a band by everything downstream.
    2. An explicit instruction to return null rather than guess. The legacy said "do not invent
       values"; this says what to do instead, which is the part a model actually acts on.
    3. LABEL-MATCHING, added 2026-08-05 after the first real-document run. "Never guess, infer,
       or carry a value over from a different field" was not enough on its own: run against a
       real contract value summary, the model took the header's reporting period ("Period | 1
       March 2026 through 31 March 2026", plainly labelled as the period, in the same block as
       the issue date and the data date) and returned it as `project_start_date` /
       `project_end_date`. The document has no project baseline dates at all. Both values were
       well-formed, in-range dates, so neither guard (`validate_doc_risk_score`,
       `validate_numeric_fields`) could have caught it — a malformed-numeric refusal only fires
       on a value that cannot be read as the requested TYPE, and a substituted date is a
       perfectly good date. The old instruction forbade carrying a value FROM a named field TO
       another named field; it never told the model that a value under NO matching label at all
       is equally not a source. This paragraph closes that gap, generalised across the whole
       field vocabulary rather than written for dates alone: the failure is "a value of the
       right type sitting nearby", and that shape is not specific to dates.

       No field in the vocabulary (`extraction_fields.ALL_FIELDS`) legitimately needs a value the
       model derives rather than one the document states. This was checked, not assumed: every
       name in that list is a total, a date, a rating, a percentage or a count a construction
       report states directly, and the platform's own standing description
       (`NAMING_AUTHORITY.md` section 3) already commits to "reads the reported figures", not
       "extracts" or "computes" them — `CPI`/`SPI` are the one place a value IS derived, and
       those are computed server-side, never asked of the model ("Do not compute indices",
       below, predates this change).

       ONE NAMED EXCEPTION, added alongside the same run: `milestones_json` is not a scalar, and
       the same run's second document showed the model returning null for a genuine activity
       table because nothing told it a document's own schedule table IS a milestones_json
       source or how to shape one field's value as a table. That is not the same failure as
       substitution — it is UNDER-application of "read what is there", not over-application —
       but the fix has to name the shape explicitly because a whole-table answer inside one
       JSON field is not something the general instructions describe.
    """
    milestones_hint = (
        " milestones_json, if requested and the document contains a schedule, activity or "
        "milestone table, is a JSON array with one object per row of that table, using the "
        "table's own column headings as keys and its values as printed (do not reformat or "
        "reinterpret a value inside this table — dates inside it are NOT required to be "
        "YYYY-MM-DD, unlike every other date field below); return an empty array only if the "
        "document has no such table."
    ) if "milestones_json" in fields else ""
    # RUN 68. THE SECOND TABLE FIELD, and it needs its own sentence for the same reason the
    # first one did: a whole-table answer inside one JSON field is not something the general
    # instructions describe, and without naming the shape the model returns null for a table
    # that is plainly printed on the page. The hint asks for the ROWS AS PRINTED and forbids
    # completing, extending or interpolating the curve, because a baseline period the document
    # does not print is exactly the invented value the extractor must never supply.
    baseline_hint = (
        " baseline_curve_json, if requested and the document contains a time-phased baseline "
        "table (a period-by-period profile of planned value, planned cost or planned spend), is "
        "a JSON array with one object per PRINTED ROW of that table, using the table's own column "
        "headings as keys and its values as printed; return every row the document prints and "
        "no others -- do not extend, complete or interpolate the profile, and do not compute a "
        "cumulative figure from a periodic one or the other way round unless the document "
        "prints both columns; return an empty array only if the document has no such table."
    ) if "baseline_curve_json" in fields else ""
    # RUN 69. THE THIRD AND FOURTH TABLE FIELDS. Same reason as the first two: a whole-table
    # answer inside one JSON field is not something the general instructions describe, and
    # without naming the shape the model returns null for a table that is plainly printed.
    resource_hint = (
        " resource_profile_json, if requested and the document contains a resource histogram or "
        "resource-loading table (a period-by-period profile of resource demand against resource "
        "availability), is a JSON array with one object per PRINTED ROW of that table, using the "
        "table's own column headings as keys and its values as printed; return every row the "
        "document prints and no others -- do not total, extend or interpolate the profile, and "
        "never repeat a demand figure as an availability figure or the other way round; return "
        "an empty array only if the document has no such table."
    ) if "resource_profile_json" in fields else ""
    modifications_hint = (
        " modifications_json, if requested and the document contains a contract modification or "
        "change register, is a JSON array with one object per PRINTED ROW of that register, "
        "using the register's own column headings as keys and its values as printed; return "
        "every row the document prints and no others. Do not infer that an official held "
        "authority because a document is signed, and do not supply an authority reference the "
        "register does not print; return an empty array only if the document has no such table."
    ) if "modifications_json" in fields else ""
    # RUN 80. THE FIFTH TABLE FIELD, and the same reason as the four before it. A reference
    # class is a population of COMPLETED projects with what each was awarded and what each
    # finished at; that is a table, and without naming the shape the model returns null for a
    # table the document plainly prints. The forbidden operations are named for this table
    # specifically: it must not add a project the document does not list, and it must not
    # compute an overrun the document does not print -- `documents.py` derives the proportional
    # overrun from the two figures the document DOES print, in code that can be read.
    reference_class_hint = (
        " reference_class_json, if requested and the document contains a table of completed "
        "comparable projects (a reference class, a comparable-project population, a historical "
        "benchmark set), is a JSON array with one object per PRINTED ROW of that table, using "
        "the table's own column headings as keys and its values as printed; return every row "
        "the document prints and no others. Do not add a project the document does not list, "
        "do not carry a project over from your own knowledge, and do not compute an overrun, a "
        "mean, a median or a percentile -- return only the cells printed; return an empty array "
        "only if the document has no such table."
    ) if "reference_class_json" in fields else ""
    # RUN 86. THE SIXTH TABLE FIELD, the look-ahead activity inventory, same reason as the five
    # before it: A2.8 is defined on rows, not on a pair of counts, and without naming the shape
    # the model returns null for a table the document plainly prints.
    lookahead_hint = (
        " lookahead_activities_json, if requested and the document contains a look-ahead "
        "activity table (one row per planned activity in the look-ahead window), is a JSON "
        "array with one object per PRINTED ROW of that table, using the table's own column "
        "headings as keys and its values as printed; return every row the document prints and "
        "no others. Do not add an activity the document does not list, do not decide for "
        "yourself whether a constraint is open or cleared -- return the status word the row "
        "prints -- and do not supply a constraint category a row does not print; return an "
        "empty array only if the document has no such table. lookahead_horizon, if requested, "
        "is the look-ahead window exactly as the document states it (for example '3 weeks'), "
        "and lookahead_status_date is the date the look-ahead stands at, as YYYY-MM-DD; return "
        "null for either the document does not state. Where the look-ahead table prints a "
        "critical-path column or a total-float column for a row, return those cells as printed "
        "too, under the table's own headings; do not decide for yourself whether an activity is "
        "critical and do not compute a float the table does not print."
    ) if "lookahead_activities_json" in fields else ""
    # RUN 103. THE FLATTENED SCHEDULE EXPORT. A2.1 and A2.12 are defined on a NETWORK -- rows
    # with logic between them -- and the platform has never asked a document for one. The shape
    # is named for the same reason as the six tables above: unnamed, the model returns null for
    # a table the schedule update plainly prints. NOTHING IS TO BE REPAIRED IN THE ANSWER: a
    # broken predecessor reference, a duplicate id or a missing duration is REPORTED by the
    # platform's diagnostics and corrected by the scheduler, so the model is told in terms not
    # to mend one.
    schedule_network_hint = (
        " schedule_network_json, if requested and the document contains an activity or schedule "
        "table with logic (one row per activity, carrying a duration and its predecessor or "
        "successor relationships), is a JSON array with one object per PRINTED ROW of that "
        "table, using the table's own column headings as keys and its values as printed; return "
        "every row the document prints and no others. Do not add an activity the document does "
        "not list, do not invent a predecessor, a relationship type or a lag a row does not "
        "print, and DO NOT CORRECT the logic: if a row names a predecessor that is not in the "
        "table, or two rows carry the same activity id, or a duration is blank, return them "
        "exactly as printed -- the platform reports those faults and the scheduler corrects the "
        "source. Return an empty array only if the document has no such table. "
        "schedule_calendar, if requested, is the project calendar the schedule states (for "
        "example '5-day work week'), schedule_calendars_json is the list of calendar names the "
        "export defines. schedule_calendar_json, if requested, is the CALENDAR DEFINITIONS the "
        "export prints, as a JSON array with one object per calendar it defines, each object "
        "carrying calendar_id (the calendar's own name or id exactly as printed), "
        "working_days_of_week (the list of day names that calendar marks as WORKING, for "
        "example [\"monday\",\"tuesday\",\"wednesday\",\"thursday\",\"friday\"]) and holidays (the "
        "list of non-working exception dates it defines, as ISO dates). Read the working days "
        "and the holidays FROM THE CALENDAR DEFINITION THE EXPORT PRINTS; a calendar NAME such "
        "as '5-day work week' states nothing about which five days, so do not infer the days "
        "from the name, do not assume a Saturday-Sunday weekend and do not supply a holiday "
        "list the export does not print. Give holidays as an empty array only where the export "
        "defines the calendar with no holidays, and omit the holidays key where it prints no "
        "holiday table at all. Return null for schedule_calendar_json where the export defines "
        "no calendar. schedule_version is the schedule's own revision identifier, "
        "schedule_baseline_finish_day is the APPROVED baseline finish and "
        "schedule_imposed_finish_day the required or contractual completion date, each as the "
        "working-day number the schedule states it on where it states one, and "
        "schedule_baseline_finish_date is that same approved baseline finish as an ISO CALENDAR "
        "DATE where the export prints one, and "
        "remaining_planned_duration_days is the remaining planned duration in working days as "
        "the document states it with remaining_duration_basis the dates it was measured between "
        "as printed; return null for any of these the document does not state, and do not "
        "compute, convert or estimate one it does not state."
    ) if "schedule_network_json" in fields else ""
    # RUN 87. THE TWO COMPLIANCE REGISTERS, named the same way and for the same reason: A6.1
    # and A6.3 are defined on a POPULATION of requirements, and without naming the shape the
    # model returns a summary for a table the document prints in full.
    quality_register_hint = (
        " quality_requirements_json, if requested and the document contains a requirement, "
        "inspection-item, checklist or audit-findings table (one row per item assessed), is a "
        "JSON array with one object per PRINTED ROW of that table, using the table's own column "
        "headings as keys and its values as printed; return every row the document prints and "
        "no others. Do not add an item the document does not list, do not decide for yourself "
        "whether an item passed -- return the word the row prints -- and do not mark an item "
        "assessed that the document leaves blank or marks pending; return an empty array only "
        "if the document has no such table. quality_register_id, if requested, is the report's "
        "or register's own identifier exactly as printed, and quality_register_period is the "
        "period it covers as the document states it; return null for either the document does "
        "not state."
    ) if "quality_requirements_json" in fields else ""
    environmental_hint = (
        " environmental_jurisdiction, permitting_authority, permit_id, permit_version, "
        "permit_site_id and operator_status, if requested, are stated on the face of an "
        "environmental compliance or permit document: the jurisdiction the site sits in, the "
        "authority that ISSUED the permit exactly as named (return the bare word EPA only where "
        "the document names the U.S. Environmental Protection Agency as the issuing authority; "
        "otherwise return the state, tribal, local or other authority as printed), the permit "
        "number, its version or revision, the site identifier and the operator's status under "
        "the permit. Do NOT infer any of them from the project's location, from the kind of "
        "work, or from your own knowledge of who usually permits such work -- return null for "
        "any the document does not state. environmental_requirements_json, if requested and the "
        "document contains a permit-condition, observation or corrective-action table, is a "
        "JSON array with one object per PRINTED ROW, using the table's own column headings as "
        "keys and its values as printed; return the closure or status word each row prints and "
        "do not close, open or resolve a row yourself; return an empty array only if the "
        "document has no such table."
    ) if "environmental_requirements_json" in fields else ""
    # RUN 102, SECTION 4.1. FIRST-PASS ACCEPTANCE, ASKED FOR IN THE WORDS THAT DISTINGUISH IT.
    # `items_passed` has been requested of inspection reports all along and cannot answer this:
    # an item that failed and passed on re-inspection is in `items_passed` and is NOT a
    # first-pass pass. The instruction says so in terms, and says to return null rather than
    # reuse the other figure, because a plausible substitution here would silently change what
    # the band means.
    first_pass_hint = (
        " items_passing_first_inspection, if requested, is the number of inspected items that "
        "were ACCEPTED ON THE FIRST INSPECTION, before any rework or re-inspection. It is NOT "
        "the same as items_passed: an item that failed and later passed on re-inspection counts "
        "in items_passed and does NOT count here. Return it only where the document itself "
        "distinguishes first-pass acceptance -- for example a 'first time right', 'first-pass "
        "yield', 'accepted on first inspection' or 'passed without rework' figure -- and return "
        "null where the document states only a total passed count. Do not compute it by "
        "subtracting rework, and do not copy items_passed into it. "
        "critical_quality_failures_json, if requested and the document records any FAILED item "
        "that it designates critical, a hold point, a life-safety requirement or a commissioning "
        "acceptance test, is a JSON array with one object per such PRINTED ROW, using the "
        "document's own column headings as keys and its values as printed; do not decide for "
        "yourself that an item is critical -- include a row only where the document designates "
        "it -- and return an empty array where the document designates none."
    ) if "items_passing_first_inspection" in fields else ""
    # RUN 106, SECTION 3. THE TWO OWNER-SUPPLIED BANDS AND THE DOCUMENT SHAPES THEY NEED.
    #
    # NEITHER INSTRUCTION LETS THE MODEL SUPPLY A JUDGEMENT. The first-review population is
    # recovered from the register's own printed decision rows, and every override is a row the
    # document itself designates. Where the document prints none, null and empty arrays are the
    # correct answers and the band is asserted on the rate alone with the absence disclosed.
    submittal_hint = (
        " submittal_decisions_json, if requested, is a JSON array with one object per DECISION ROW"
        "  the register prints, using the register's own column headings as keys and its "
        "values as printed. Each row must carry the submittal identifier, the revision "
        "identifier and the decision date as the document states them, because the first review "
        "of a submittal is identified as its earliest decision; do not merge revisions of one "
        "submittal into a single row, do not compute a first-review rate yourself, and do not "
        "reorder or renumber the revisions. submittal_disposition_legend_json, if requested, is "
        "the register's own legend or key mapping its disposition codes to their printed "
        "meanings, as a JSON object; return null where the register prints no legend rather "
        "than inventing one. submittal_reporting_period is the period the register declares it "
        "is reporting, as printed. rejected_critical_or_long_lead_late_json and "
        "rejected_blocking_past_deadline_json are JSON arrays of the printed rows the document "
        "itself designates as, respectively, a rejected critical-path or long-lead submittal "
        "whose forecast approval falls after its need-by date, and a rejected submittal "
        "unresolved beyond the stated review deadline and blocking planned work; include a row "
        "only where the document designates it, never where you infer it, and return an empty "
        "array where it designates none. critical_package_rejected_resubmittals is the count of "
        "rejected resubmittals for a critical work package where the document states that count "
        "or prints the rows to count; return null where it states neither."
    ) if "submittal_decisions_json" in fields else ""
    # RUN 114, GOAL 1. THE THREE TABLES THAT LET A DOCUMENT SERVE A4.5, A4.6 AND A4.9.
    #
    # Run 112 measured all three modules as unservable by any document: their document types
    # carried only scalars and no `*_json` field was shaped to carry what the module reads. Each
    # hint below names the shape for the same reason the eight before it do -- unnamed, the model
    # returns null for a table the document plainly prints -- and each forbids the same thing:
    # the model returns the cells the document printed and computes nothing.
    weather_events_hint = (
        " weather_events_json, if requested and the minutes contain a WEATHER EVENT table (one "
        "row per weather event, with the activity or schedule path it affected and the time "
        "lost on it), is a JSON array with one object per PRINTED ROW of that table, using the "
        "table's own column headings as keys and its values as printed; return every row the "
        "document prints and no others. Do not add an event the document does not list, do not "
        "decide for yourself which activity or path an event affected, and do not compute a "
        "float, a path effect or a total -- return only the cells printed. "
        "weather_allowance_days_remaining is the weather allowance the contract calendar still "
        "has REMAINING as the minutes state it, which is not the same figure as the allowance "
        "granted; weather_calendar_id is the identifier or name of the weather calendar the "
        "minutes cite; weather_day_basis is the minutes' own word for which kind of day the "
        "table counts, one of approved_calendar_working_days or calendar_days; "
        "weather_approval_source is the minutes the approval is recorded in, and their date. "
        "weather_time_extension_incorporated_in_baseline, weather_milestone_forecast_late and "
        "weather_milestone_class are stated by the minutes or null: whether a granted time "
        "extension has been incorporated into the baseline schedule, whether the minutes record "
        "a milestone as forecasting late, and whether that milestone is contractual or "
        "owner_committed. Return null for any of these the minutes do not state; never infer one "
        "and never read the days CLAIMED as the days APPROVED."
    ) if "weather_events_json" in fields else ""
    procurement_items_hint = (
        " procurement_items_json, if requested and the log contains an ITEM-LEVEL procurement "
        "table (one row per monitored item, with the date it is required on site and the date it "
        "is forecast to be delivered), is a JSON array with one object per PRINTED ROW of that "
        "table, using the table's own column headings as keys and its values as printed; return "
        "every row the document prints and no others. Do not add an item the document does not "
        "list, do not compute a slack, a lateness or a state -- the platform computes those from "
        "the two dates -- and do not decide for yourself whether an item is long lead or sits on "
        "controlling or near-critical work: return the criticality word and the long-lead cell "
        "the register prints, and omit them where it prints neither. procurement_day_basis is "
        "the register's own word for which kind of day its dates are counted in, one of "
        "approved_calendar_working_days or calendar_days; return null where it states neither."
    ) if "procurement_items_json" in fields else ""
    change_events_hint = (
        " change_events_json, if requested and the document contains a CHANGE EVENT register "
        "(one row per change, with its value and whether it adds to or takes away from the "
        "contract), is a JSON array with one object per PRINTED ROW of that register, using the "
        "register's own column headings as keys and its values as printed; return every row the "
        "document prints and no others. Return the DIRECTION cell exactly as the register prints "
        "it -- an addition or an omission -- and never decide the direction yourself from the "
        "sign of a number or from the wording of a description; where the register prints no "
        "direction for a row, return the row without one. Do not compute a frequency, a net "
        "change, a magnitude or a percentage. change_exposure_days is the span of time in DAYS "
        "the register covers, as the document states it; return null where it states none, and "
        "never compute one from the dates of the changes. change_related_delay_days, "
        "change_available_total_float_days, original_contract_duration_days, "
        "change_time_extension_approved and change_forecast_completion_moved are stated by the "
        "document or null: the delay days attributed to changes, the total float remaining on "
        "the affected path, the original contract duration in days, whether a time extension has "
        "been approved, and whether the forecast completion date has moved. Never assume a float "
        "of zero and never infer that completion has moved."
    ) if "change_events_json" in fields else ""
    ncr_hint = (
        " inspections_performed is the number of INSPECTIONS PERFORMED in the reporting period as "
        "the log or its covering report states it; it is not the number of items inspected and "
        "is not a count of nonconformances. active_work_packages is the number of work packages "
        "ACTIVE in the period, and is the fallback denominator to be returned only where the "
        "document states it. ncr_denominator_basis is the document's own words for which "
        "population it is reporting against; return null rather than choosing one. Return null "
        "for any of the three the document does not state -- do not derive one from the other, "
        "and do not substitute a total from a different document. open_critical_ncr_json, "
        "hold_point_or_turnover_blocking_ncr_json and ncr_open_past_contractual_closure_json are "
        "JSON arrays of the printed rows the document itself designates as, respectively, an "
        "open critical, life-safety, structural or code-compliance nonconformance; a "
        "nonconformance on a hold point, failed commissioning test or required inspection "
        "blocking turnover; and a nonconformance open beyond a documented contractual closure "
        "date. Include a row only where the document designates it; return an empty array where "
        "it designates none. max_repeat_ncrs_one_root_cause_or_trade is the largest number of "
        "repeat nonconformances the document attributes to a single root cause or trade in the "
        "period, where it states or prints that grouping; return null where it does not group "
        "them."
    ) if "inspections_performed" in fields or "submittal_decisions_json" in fields else ""
    # RUN 102, SECTION 4.3. THE ENVIRONMENTAL CORRECTIVE-ACTION REGISTER, WITH ITS DEADLINES.
    # A timeliness question needs a deadline and a closure date; a closure WORD cannot answer
    # it. The instruction refuses to let the model supply a deadline the document does not
    # print, because the deadline is the project's own permit or contract commitment and an
    # invented one would decide the band.
    corrective_hint = (
        " environmental_corrective_actions_json, if requested and the document contains a "
        "CORRECTIVE ACTION register or log, is a JSON array with one object per PRINTED ROW of "
        "that register, using the register's own column headings as keys and its values as "
        "printed. Each row must carry, where the document prints them: the action's own "
        "identifier, the DATE IT IS REQUIRED TO BE CLOSED BY, the DATE IT WAS ACTUALLY CLOSED, "
        "its severity as printed, and whether the document states the deadline is a mandatory "
        "regulatory or permit deadline. DO NOT SUPPLY A DEADLINE THE DOCUMENT DOES NOT PRINT -- "
        "not from the EPA Construction General Permit, not from any other permit, and not from "
        "your own knowledge -- and do not compute whether an action was late; return the dates "
        "as printed and leave the comparison to the platform. Return an empty array only if the "
        "document has no such register."
    ) if "environmental_corrective_actions_json" in fields else ""
    # RUN 117, SECTION 3. THE ATTRIBUTION COLUMN, AND THE INSTRUCTION NOT TO INVENT A FIRM.
    # The whole value of this table is that it says WHO, and the whole danger of it is a model
    # that would rather guess than leave a cell empty. Both halves are stated in terms: name the
    # firm the document names, and where the document names none, LEAVE IT NULL. An unattributed
    # record is a real and reportable state on this platform; a wrong attribution is not.
    trade_attribution_hint = (
        " trade_attribution_json, if requested and the document records individual items,"
        " findings, nonconformances, incidents, deliveries or defects, is a JSON array with one"
        " object per PRINTED RECORD, with these keys: record_reference (the record's own"
        " identifier as printed -- an NCR number, an inspection item, a permit condition, a"
        " purchase order), subcontractor (THE FIRM THE DOCUMENT NAMES as responsible for that"
        " record), record_kind, record_status, record_severity and record_date, each as printed."
        " record_reference is required; return no object for a record whose identifier the"
        " document does not print. DO NOT SUPPLY A SUBCONTRACTOR THE DOCUMENT DOES NOT NAME FOR"
        " THAT RECORD -- not from another row, not from the project's contractor list, not from"
        " your own knowledge, and never by choosing the firm that seems most likely. Where the"
        " record names no firm, return subcontractor as null: an unattributed record is carried"
        " through and reported as unattributed, and a guessed name would be attributed to a firm"
        " it does not belong to. Return an empty array where the document records no such items."
    ) if "trade_attribution_json" in fields else ""
    # RUN 118, SECTION 1.4. THE DENOMINATOR TABLE. A rate needs a population, and a population
    # is a number the DOCUMENT counts. The instruction below is written to make an absent
    # denominator an ACCEPTABLE answer, because a guessed one silently decides a firm's band.
    trade_denominator_hint = (
        " trade_denominators_json, if requested, is a JSON array with one object per FIRM the"
        " document states a population for, with these keys: subcontractor (required, and the"
        " SAME NAME used in trade_attribution_json), inspections_performed (inspections of that"
        " firm's work this period, EXCLUDING reinspections), exposure_hours (hours that firm"
        " worked, rolling twelve months), recordable_incidents (that firm's OSHA recordables"
        " over the same twelve months), environmental_actions_due, audits_covering_firm,"
        " items_due, field_reports_covering_firm and systems_tested, each as the document"
        " states it. OMIT ANY KEY THE DOCUMENT DOES NOT STATE FOR THAT FIRM -- do not compute"
        " it, do not total it from another table, do not carry it over from another firm and"
        " do not estimate it. A missing denominator is a correct and expected answer and the"
        " platform handles it; an invented one decides a firm's performance band. Return an"
        " empty array where the document states no per-firm population."
    ) if "trade_denominators_json" in fields else ""
    # RUN 72. THE SCALE OF A RATIO FIELD, NAMED, because the general sentence below is false
    # of it. "Percentages as numbers 0-100" is correct for every 0..100 quantity in the
    # vocabulary and WRONG for a compliance rate, which the numeric contract bounds at 1.0. A
    # real Environmental Compliance Report printing "Environmental compliance rate 1.000" was
    # refused whole because extraction returned 100 for it: under the instructions as they
    # stood, 100 was the compliant answer to a document that states 1.000. The guard did its
    # job -- the instruction was the defect. The field list comes from
    # `extraction_merge.ratio_scaled_extraction_keys()`, which reads the same
    # `BOUNDED_MAX_SI_FIELDS` table the refusal reads, so the prompt and the range check can
    # never disagree about which fields are shares.
    from .extraction_merge import ratio_scaled_extraction_keys, ORDINAL_WORD_SCALES

    # RUN 80, FIX TWO. THE RATING WORDS, ASKED FOR AS WORDS. A CPARS evaluation prints
    # "Satisfactory", not 3. Asking the model for a number here would make it do the mapping,
    # which is exactly the invention this platform refuses; it is told to return the word the
    # document prints, and `read_ordinal_word` -- one declared table, two call sites -- does the
    # mapping in Python where it can be read and checked. The permitted words are LISTED FROM
    # THAT TABLE, so the prompt cannot name a level the mapping does not hold.
    _ordinal = [k for k in sorted(ORDINAL_WORD_SCALES) if k in fields]
    _words = sorted({w for k in _ordinal for w in ORDINAL_WORD_SCALES[k]},
                    key=lambda w: -ORDINAL_WORD_SCALES[_ordinal[0]][w]) if _ordinal else []
    ordinal_hint = (
        " " + ", ".join(_ordinal) + (" is" if len(_ordinal) == 1 else " are") +
        " stated as a RATING WORD, not a number. Return the word exactly as the document "
        "prints it (" + ", ".join(w.title() for w in _words) + "). Do not convert a rating "
        "word into a number and do not substitute a word the document does not use; if the "
        "document states no rating for one of these, return null for it. "
    ) if _ordinal else ""

    _ratio = [k for k in ratio_scaled_extraction_keys() if k in fields]
    ratio_hint = (
        " " + ", ".join(_ratio) + (" is" if len(_ratio) == 1 else " are") +
        " a SHARE between 0 and 1 inclusive, not a percentage: return the figure exactly as the "
        "document prints it (a document stating 1.000 gives 1.000, and one stating 0.94 gives "
        "0.94), and never multiply it by one hundred. If the document prints only the counts "
        "behind such a share and never the share itself, return null -- do not divide one count "
        "by the other. "
    ) if _ratio else ""
    return (
        "You are a precise construction project-controls data extractor. Read this ONE document "
        f"(type: {doc_type}) and return ONLY these fields as clean JSON: "
        f"{json.dumps(fields)}. "
        "A field is returned ONLY when the document itself states that field, under a label or "
        "heading whose meaning matches the field's name. A different value sitting nearby, under "
        "a different label, is never a substitute, even if it is a plausible value of the right "
        "type and in a sensible range: a reporting period is not a project start or end date, an "
        "issue date or a data date is not a baseline date, and a schedule-progress percentage is "
        "not a cost-basis percentage. If you cannot point to the specific label in the document "
        "that names this field, return null for it. Counting entries in the document's own table "
        "is reading a stated fact, not inferring one, when the field name plainly refers to that "
        "table (for example, a count of rows in a schedule or activity table)." + milestones_hint + baseline_hint + resource_hint + modifications_hint + reference_class_hint + lookahead_hint + schedule_network_hint + quality_register_hint + environmental_hint + first_pass_hint + corrective_hint + trade_attribution_hint + trade_denominator_hint + submittal_hint + ncr_hint + weather_events_hint + procurement_items_hint + change_events_hint +
        " Use null for any field genuinely not present in the document. Never guess, invent, or "
        "carry a value over from a different field or a different document. Do not compute "
        "indices. "
        "Numbers as plain numbers (no currency symbols, no thousands separators). "
        "Return every number on the scale the document prints it on: never convert a ratio "
        "into a percentage or a percentage into a ratio, never rescale, and never restate a "
        "figure in different units from the ones the document uses. "
        "Percentages as numbers 0-100. Dates as YYYY-MM-DD. " + ratio_hint + ordinal_hint +
        "document_risk_score, if requested, is a number between 0 and 1 inclusive, where 0 is "
        "no concern and 1 is severe concern; never a count and never a percentage. "
        "Return JSON only, no markdown, no commentary."
    )


def extraction_contract_fingerprint(doc_type: str) -> str:
    """
    0030. The identity of the extraction contract for a document type: the sha256 of the exact
    prompt `build_prompt` issues for it today, field list included.

    This is the second cache key. The upload path stores it on `documents.extraction_contract`
    beside the extraction it stamps, and serves a known sha256 from the cache ONLY while the
    stored fingerprint equals the current one for the stored type. A contract change -- a field
    added to `extraction_fields_for`, or a change to the prompt text itself -- changes this
    value and invalidates every cached extraction made under the old contract, exactly once
    each; an upload with no contract change is still served from the cache. Derived at call
    time from the same functions that build the real prompt, so it cannot drift from what the
    model is actually asked.
    """
    import hashlib
    prompt = build_prompt(doc_type, extraction_fields_for(doc_type))
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def build_classify_prompt() -> str:
    """Port of `identifyOnly_` (.gs ~685), including its content-sniffing hints."""
    return (
        "Classify this construction project document. Return ONLY JSON of the form "
        '{"docType": "...", "confidence": 0.0}. '
        f"docType must be exactly one of {json.dumps(list(DOC_TYPES))}, or the string "
        f'"{UNMAPPED}" if it is none of them. ' + CLASSIFY_HINTS +
        "Do not force a match: if the document is not clearly one of the listed types, return "
        f'"{UNMAPPED}".'
    )


_FENCE = re.compile(r"```(?:json)?", re.IGNORECASE)


def parse_json_response(raw: str) -> dict:
    """
    De-fence and parse. The legacy stripped ``` markers with a regex and called JSON.parse;
    the API is not schema-constrained, so the same defence is still required.
    """
    text = _FENCE.sub("", raw or "").strip()
    if not text:
        raise ExtractionError("model returned an empty response")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # TRUNCATION IS CHECKED FIRST, and it is checked before the salvage attempt below.
        # A cut-off response is not malformed JSON and calling it that sent three retries at a
        # failure that reproduces identically every time. See TruncatedResponseError.
        cut = describe_json_truncation(text)
        if cut is not None:
            raise TruncatedResponseError(
                "the model ran out of output space before it finished answering: " + cut +
                ". Retrying will stop in the same place; the answer has to be made smaller."
            ) from None
        # A model that wrapped the object in prose. Take the outermost braces rather than
        # failing the whole document.
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ExtractionError(f"model response was not JSON: {text[:200]!r}") from None
        try:
            parsed = json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            raise ExtractionError(f"model response was not JSON: {text[:200]!r}") from None
    if not isinstance(parsed, dict):
        raise ExtractionError(f"model returned {type(parsed).__name__}, expected an object")
    return parsed


# --------------------------------------------------------------------------- real client


class ProviderExtractor:
    """
    One HTTPS POST per document, through whichever provider is configured. Stateless, so it is
    safe to share across threads.

    Run 93: the endpoint, the authentication header and the request/response shapes moved to
    `app.ai_provider`. This class keeps the extraction-specific behaviour -- the content block,
    the classify/extract prompts, and the truncation distinction -- and knows nothing about
    which provider answered beyond the `provider` and `model_id` it reports for the stored row.
    """

    def __init__(self, api_key: str = "", model: str = EXTRACTION_MODEL,
                 url: str = ANTHROPIC_URL, client=None) -> None:
        self._api_key = api_key
        self.model = model
        self._url = url
        if client is None:
            cfg = ai_provider.ProviderConfig(
                role="extraction", provider="anthropic", wire="anthropic", model=model,
                url=url, key_env="ANTHROPIC_API_KEY")
            client = ai_provider.AnthropicClient(cfg, api_key, REQUEST_TIMEOUT_S)
        self._client = client

    # ``model_id`` is recorded on every document row so a later reader can tell which weights
    # produced a stored figure; ``provider`` says which provider served those weights, because
    # a model identifier alone does not.
    @property
    def model_id(self) -> str:
        return self._client.model_id

    @property
    def provider(self) -> str:
        return self._client.provider

    def _post(self, prompt: str, content_block: dict, max_tokens: int) -> str:
        try:
            return self._client.complete(
                [content_block, {"type": "text", "text": prompt}], max_tokens=max_tokens)
        except ai_provider.ProviderTruncated as exc:
            # THE API SAYS SO ITSELF -- `stop_reason`/`finish_reason` is the authoritative
            # statement that the answer was cut off by the output cap rather than finished.
            # `describe_json_truncation` is the fallback for a caller that never sees it.
            cut = describe_json_truncation("")
            raise TruncatedResponseError(
                str(exc) + (": " + cut if cut else "") +
                " Retrying will stop in the same place; the answer has to be made smaller."
            ) from None
        except ai_provider.ProviderCallError as exc:
            raise ExtractionError(str(exc)) from None

    @staticmethod
    def _content_block(raw: bytes, mime_type: str, filename: str = "",
                       elide_tables: dict[int, str] | None = None) -> dict:
        """
        A .docx is read locally into text and tables; PDFs go as a document block; anything
        else is decoded as text.

        THE DOCX BRANCH IS FIRST, AND IT IS DECIDED FROM THE BYTES. A .docx is a ZIP archive, so
        before this branch existed it fell through to the raw-decode below and became 12000
        characters of deflate-compressed binary — measured on a real file, 5071 U+FFFD
        replacement characters, with the truncation consumed by ZIP headers before the body was
        reached. It is tested before the PDF branch rather than after because `signals.js` sends
        `file.type || "application/pdf"`, so a docx the browser did not type arrives CLAIMING to
        be a PDF and a mime-first test would send the archive as a PDF document block.

        See `docx_text` for why reading it locally is the better route for these documents and
        not a workaround: the tables survive as structure rather than as guessed layout, and
        there is no OCR step.

        The legacy split PDF-versus-text the same way (`claudePdfExtract_` vs `claudeChat_`) and
        truncated text at 12000 characters. That truncation is preserved for the raw-bytes
        branch: it bounds a prompt built from an unknown blob. The docx branch carries its own,
        larger bound, because that text has already been parsed and a pay application's summary
        rows can sit past 12000 characters.
        """
        from .docx_text import docx_content_block, is_docx

        if is_docx(raw, mime_type, filename):
            return docx_content_block(raw, elide_tables)
        if (mime_type or "").lower() == "application/pdf":
            return {
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf",
                           "data": base64.b64encode(raw).decode("ascii")},
            }
        text = raw.decode("utf-8", "replace")[:12000]
        return {"type": "text", "text": "DOCUMENT TEXT:\n" + text}

    def classify(self, raw: bytes, mime_type: str, filename: str) -> str:
        """
        Return a doc_type, or UNMAPPED.

        NEVER inherits confidence from a rejected classification. The legacy did
        (`confidence: parsed.confidence != null ? parsed.confidence : 0.7` at .gs 788), which
        meant a document whose type had just been thrown away still carried the model's
        certainty about that discarded answer. The filename heuristic is consulted only as a
        fallback, and if it too declines, the document is UNMAPPED rather than relabelled.

        THE CONFIDENCE IS NOW KEPT, AND THE RULE ABOVE IS UNCHANGED. The prompt has always
        asked for `{"docType", "confidence"}` and this method has always parsed it and then
        dropped it, so no caller had ever seen it. `classify_with_confidence` returns both, and
        returns confidence ONLY when the model's own claim is the thing that decided the type.
        A filename fallback or an UNMAPPED outcome carries None, which is exactly the
        "rejected classification" case this docstring already refuses to inherit from. This
        method keeps its single-value signature because every existing caller wants a type.
        """
        return self.classify_with_confidence(raw, mime_type, filename)[0]

    def classify_with_confidence(self, raw: bytes, mime_type: str,
                                 filename: str) -> tuple[str, float | None]:
        """(doc_type, confidence). Confidence is None unless the model's own claim was used."""
        block = self._content_block(raw, mime_type, filename)
        try:
            answer = parse_json_response(self._post(build_classify_prompt(), block, 256))
        except ExtractionError:
            guessed = guess_type_from_filename(filename)
            return (guessed if guessed else UNMAPPED), None
        claimed = str(answer.get("docType") or "").strip().lower()
        if is_mapped(claimed):
            raw_confidence = answer.get("confidence")
            try:
                confidence = float(raw_confidence) if raw_confidence is not None else None
            except (TypeError, ValueError):
                # Unreadable is not confident. Same posture as the numeric contract: a value
                # that cannot be read is never silently treated as a good one.
                confidence = None
            if confidence is not None and not 0.0 <= confidence <= 1.0:
                confidence = None
            return claimed, confidence
        guessed = guess_type_from_filename(filename)
        return (guessed if guessed else UNMAPPED), None

    def extract(self, raw: bytes, mime_type: str, filename: str,
                doc_type: str | None = None) -> tuple[str, dict]:
        """Return (doc_type, extracted_fields). Raises ExtractionError on failure."""
        resolved, fields, _confidence = self.extract_with_confidence(
            raw, mime_type, filename, doc_type)
        return resolved, fields

    def extract_with_confidence(self, raw: bytes, mime_type: str, filename: str,
                                doc_type: str | None = None
                                ) -> tuple[str, dict, float | None]:
        """
        Return (doc_type, extracted_fields, classification_confidence).

        Confidence is None when this call did not classify — a caller-supplied type is taken as
        given, and the platform has no opinion about how sure someone else was.
        """
        resolved = (doc_type or "").strip().lower()
        confidence: float | None = None
        if not is_mapped(resolved):
            resolved, confidence = self.classify_with_confidence(raw, mime_type, filename)
        if resolved == UNMAPPED:
            # No field list applies, so there is nothing to ask for. Storing the document with
            # an empty extraction is honest; asking the generic two-field default would produce
            # a docRiskScore for a document type nothing knows how to interpret.
            return UNMAPPED, {}, confidence
        fields = extraction_fields_for(resolved)
        # PART 2, THE SEPARATION. Where the reader can take the activity table itself, the
        # table stops competing with the scalar fields for one response's output budget:
        # `milestones_json` is not asked for, and the table's rows are not sent either. The
        # scalar fields then have the whole budget, which is what they always needed and never
        # had — the response that failed three times died at its seventh scalar key.
        from .risk_register import risk_table_from_document
        from .schedule_table import activity_table_from_document

        table = activity_table_from_document(raw, mime_type, filename)
        elide: dict[int, str] | None = None
        if table is not None:
            fields = [f for f in fields if f != "milestones_json"]
            elide = {table.index: table.elision_note()}
        # THE SAME SEPARATION FOR THE RISK REGISTER, and it was never asked for as a field, so
        # there is nothing to drop from `fields` -- only the rows to keep out of the prompt. A
        # register of five hundred risks and one of twenty therefore cost the same call: the
        # header row survives so the model can still see the document HAS a register and answer
        # its scalar fields, and the unbounded part is read by `risk_register` from the document
        # itself.
        risks = risk_table_from_document(raw, mime_type, filename)
        if risks is not None and (table is None or risks.index != table.index):
            elide = dict(elide or {})
            elide[risks.index] = risks.elision_note()
        block = self._content_block(raw, mime_type, filename, elide)
        extracted = parse_json_response(self._post(build_prompt(resolved, fields), block,
                                                   MAX_TOKENS))
        # Keep only what was asked for. A model that volunteers extra keys must not be able to
        # widen the stored extraction beyond the type's declared field list.
        return resolved, {k: v for k, v in extracted.items() if k in set(fields)}, confidence


# --------------------------------------------------------------------------- stub


class StubExtractor:
    """
    Serves recorded extractions keyed by sha256, for environments without an API key.

    It REFUSES an unknown hash rather than inventing an extraction. A stub that quietly returns
    empty fields would let a test assert that caching and assembly work while the numbers being
    asserted came from nowhere.
    """

    model_id = "stub/recorded-v1"
    # Run 93. Not a provider name: the honest statement that no provider was asked.
    provider = "stub"

    def __init__(self, recorded: dict[str, tuple[str, dict]],
                 delay_s: float = 0.0) -> None:
        self._recorded = dict(recorded)
        # Lets a test demonstrate that N concurrent calls take ~1x rather than ~Nx the
        # single-document time, without waiting on a real network.
        self._delay_s = delay_s
        self.calls: list[str] = []

    def classify(self, raw: bytes, mime_type: str, filename: str) -> str:
        import hashlib
        return self._recorded.get(hashlib.sha256(raw).hexdigest(), (UNMAPPED, {}))[0]

    def extract(self, raw: bytes, mime_type: str, filename: str,
                doc_type: str | None = None) -> tuple[str, dict]:
        rec_type, fields, _confidence = self.extract_with_confidence(
            raw, mime_type, filename, doc_type)
        return rec_type, fields

    def extract_with_confidence(self, raw: bytes, mime_type: str, filename: str,
                                doc_type: str | None = None
                                ) -> tuple[str, dict, float | None]:
        """
        A recording may carry a confidence as a third element. One that does not returns None,
        which is the honest answer: a recording made before confidences were kept never had
        one, and inventing a high value would make every stub-backed check assert filing
        behaviour the real classifier had never demonstrated.
        """
        import hashlib
        sha = hashlib.sha256(raw).hexdigest()
        if self._delay_s:
            time.sleep(self._delay_s)
        self.calls.append(sha)
        if sha not in self._recorded:
            raise ExtractionError(
                f"stub extractor has no recording for sha256 {sha[:12]}…; refusing to invent "
                "an extraction. Record it, or run against the real model."
            )
        recording = self._recorded[sha]
        rec_type, fields = recording[0], recording[1]
        confidence = recording[2] if len(recording) > 2 else None
        return rec_type, dict(fields), confidence


AnthropicExtractor = ProviderExtractor


def build_extractor(*, require_real: bool = False,
                    recorded: dict[str, tuple[str, dict]] | None = None,
                    delay_s: float = 0.0):
    """
    The CONFIGURED provider's extractor if its key is set, otherwise the stub.

    Run 93: which provider that is comes from configuration (`AI_PROVIDER`, or
    `AI_EXTRACTION_PROVIDER`), defaulting to anthropic, which is what this returned before.
    There is NO fallback to a second provider: a configured provider with no key returns the
    stub in a verification environment and, under `require_real=True`, raises naming the
    provider and the variable that was empty.

    `require_real=True` turns a missing key into an error. Production passes it, so a
    misconfigured deployment fails loudly at the first upload instead of silently filling the
    research record with stub output.
    """
    cfg = ai_provider.load_provider("extraction")
    if cfg.key_present():
        return ProviderExtractor(
            model=cfg.model, url=cfg.url,
            client=ai_provider.build_client(cfg, timeout_s=REQUEST_TIMEOUT_S))
    if require_real:
        raise ExtractionError(str(ai_provider.ProviderNotConfigured(
            f"AI provider {cfg.provider!r} is configured for the extraction call site but "
            f"{cfg.key_env} is not set in this environment. Refusing to extract with the stub "
            f"in an environment that requires real extraction. Nothing is served by another "
            f"provider in its place.")))
    return StubExtractor(recorded or {}, delay_s=delay_s)


# --------------------------------------------------------------------------- concurrency


def extract_many(extractor, jobs: list[dict],
                 concurrency: int = DEFAULT_CONCURRENCY) -> list[dict]:
    """
    Extract `jobs` concurrently, preserving input order in the returned list.

    Each job: {"sha256", "content", "mime_type", "filename", "doc_type"}.
    Each result: {"sha256", "ok", "doc_type", "extraction", "error", "confidence",
    "elapsed_s"}.

    A failure is captured per job rather than raised, so one unreadable document in a batch of
    twenty-seven does not discard the twenty-six that extracted cleanly. The caller decides
    what to do with the failures; nothing is silently treated as an empty extraction.

    Order is preserved because the caller reports back to the PM per uploaded file, and a
    reordered result list would attribute one document's outcome to another's filename.
    """
    if not jobs:
        return []
    workers = max(1, min(concurrency, len(jobs)))

    # Imported inside the function, as documents.py does with the simulation package: it keeps
    # the module-level direction client -> fields only, and this is the one call site.
    from .extraction_merge import validate_doc_risk_score, validate_numeric_fields

    def run(job: dict) -> dict:
        started = time.monotonic()
        try:
            # Prefer the confidence-bearing call. An extractor predating it (a caller's own
            # stub in a test, for instance) still works and simply reports no confidence,
            # which `needs_review` treats as reviewable rather than as fine.
            if hasattr(extractor, "extract_with_confidence"):
                doc_type, extraction, confidence = extractor.extract_with_confidence(
                    job["content"], job.get("mime_type") or "", job.get("filename") or "",
                    job.get("doc_type"),
                )
            else:
                doc_type, extraction = extractor.extract(
                    job["content"], job.get("mime_type") or "", job.get("filename") or "",
                    job.get("doc_type"),
                )
                confidence = None
            # THE POINT THE VALUE ENTERS. Refusing here, before the caller writes a Document
            # row, is what makes "no out-of-range value reaches storage" true rather than
            # merely checked later: documents.py only persists results whose ok is True, so a
            # refusal leaves nothing behind to clean up. Raising rather than returning a
            # failure shape is deliberate — the except below already converts any exception
            # into the per-file {ok: False, error} the PM sees in the "Extraction failed"
            # dialog, so the reason reaches the uploader through machinery that exists.
            validate_doc_risk_score((extraction or {}).get("document_risk_score"),
                                    filename=job.get("filename") or None)
            # D2, same boundary. A value readable as a number but OUT OF CONTRACT (a negative
            # count, ten thousand per cent complete) still refuses the WHOLE document here —
            # before the caller writes a Document row — so nothing is half-stored and no
            # observation row can carry a coerced zero. The per-file {ok: False, error} shape
            # delivers the field name and the reason to the uploader through the existing
            # extraction-failure dialog.
            #
            # RUN 80, FIX TWO, ITEM 3. A field that cannot be READ no longer refuses the
            # document. `validate_numeric_fields` returns those fields instead of raising; they
            # are carried on the result as `unreadable`, reach the PM as a per-file notice, and
            # are absent from the emission because `_coerce_numeric` gives None for them. This
            # is the owner's ruling of Run 80 section 3 item 3, overriding the whole-document
            # refusal that stood here since D2. See `validate_numeric_fields` for what it costs.
            unreadable = validate_numeric_fields(doc_type, extraction,
                                                 filename=job.get("filename") or None)
            return {"sha256": job["sha256"], "ok": True, "doc_type": doc_type,
                    "extraction": extraction, "error": None,
                    "unreadable": unreadable,
                    "confidence": confidence,
                    "elapsed_s": round(time.monotonic() - started, 3)}
        except Exception as exc:  # noqa: BLE001 — one document must not sink the batch
            log.warning("extraction failed for %s: %s", job.get("filename"), exc)
            return {"sha256": job["sha256"], "ok": False, "doc_type": None,
                    "extraction": None, "error": str(exc), "unreadable": [], "confidence": None,
                    "elapsed_s": round(time.monotonic() - started, 3)}

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="extract") as pool:
        return list(pool.map(run, jobs))
