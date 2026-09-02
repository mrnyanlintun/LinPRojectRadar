"""
RUN 108, GOAL 2. THE PROJECT'S OWN WORKING CALENDAR, AND THE ONE CONVERSION THAT USES IT.

WHY THIS FILE EXISTS AT ALL. Three arms across the eight modules are specified in APPROVED
CALENDAR WORKING DAYS and none of them could form that quantity before this run:

  * A1.6 Earned Schedule -- the time-variance component divides SV(t), converted to working
    days, by the remaining planned working duration.
  * A4.9 Procurement Lead-Time -- lateness is banded "in approved-calendar working days", and a
    register that counts calendar days was Not Assessed rather than converted.
  * A4.5 Weather-Day Impact -- the float-consumed component divides forecast delay days by the
    remaining total float on the affected path, and float is a working-day quantity.

Before this run the platform held a calendar's NAME and nothing else: `schedule_calendar` was a
string such as "5-day work week" and `schedule_calendars_json` a list of such strings. A name
cannot count a day.

THE OWNER'S RULING, WHICH THIS FILE IMPLEMENTS LITERALLY. "The calendar comes from the project,
not from the platform. A project in Alaska and one in Florida do not share holidays; a six-day
week is not a five-day week. There is no default calendar and none is to be assumed."

So there is NO DEFAULT ANYWHERE IN THIS FILE. There is no five-day week, no Saturday-Sunday
weekend, no holiday list and no fallback to calendar days. A project whose documents state no
calendar gets `None` from `read_project_calendar` and every caller states what it needs.

ONE IMPLEMENTATION, NOT THREE. The three arms must not each count days their own way, so every
working-day count in the analytical layer goes through `working_days_between` here. That is the
same reason Run 107 put the component-aggregation rule in `owner_bands.py` rather than repeating
it in eight modules.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping, Sequence

#: The seven day names a calendar may state, mapped to `date.weekday()`. The words are matched
#: case-insensitively and with surrounding space stripped; NOTHING ELSE IS ACCEPTED, because a
#: word this platform does not hold is a day it cannot count and guessing which day was meant is
#: exactly the inference rule 1 forbids.
WEEKDAY_NUMBERS: dict[str, int] = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

#: THE SHAPE THE SCHEDULE DOCUMENT MUST STATE, printed here so it can be quoted verbatim and so
#: the extraction contract and this reader cannot drift apart. One object per calendar the
#: export defines. `holidays` is a LIST OF ISO DATES and an EMPTY LIST IS A STATEMENT -- it says
#: this calendar observes no non-working holidays in the exported horizon -- whereas a MISSING
#: `holidays` key is silence and is not read as an empty list.
PROJECT_CALENDAR_CONTRACT: dict[str, Any] = {
    "extraction_field": "schedule_calendar_json",
    "document_type": "schedule_update",
    "structure_key": "projectCalendar",
    "shape": [
        {
            "calendar_id": "the calendar's own name or id exactly as the export prints it",
            "working_days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "holidays": ["2026-07-03", "2026-09-07"],
        }
    ],
    "rules": [
        "One object per calendar the export DEFINES. Return every calendar it defines.",
        "working_days_of_week is the list of day names the calendar marks as working. It is "
        "read from the calendar definition the export prints and is never inferred from the "
        "calendar's NAME: a calendar called '5-day work week' states nothing about WHICH five.",
        "holidays is the list of non-working exception dates the calendar defines, as ISO "
        "dates. An empty list means the export defines the calendar with no holidays. Omit the "
        "key entirely if the export prints no holiday table for that calendar.",
        "Return null for the whole field where the export defines no calendar. Do not "
        "construct a calendar, do not assume a five-day week and do not assume a weekend.",
    ],
}

#: What a caller prints when the calendar it needs is not there. Composed here so the same
#: absence reads the same way in all three arms.
CALENDAR_ABSENT_WORDS = (
    "no approved working calendar reaches this module. The project's schedule update states "
    "no calendar definition -- the working days of the week and the holiday set -- so working "
    "days cannot be counted. A calendar NAME alone is not a calendar. No five-day week is "
    "assumed, no weekend is assumed, no holiday set is assumed, and calendar days are not "
    "substituted for working days. WHAT IS NEEDED: a schedule update whose export defines its "
    "calendars, each with its working days of the week and its holiday dates."
)


def normalise_calendar(raw: Any) -> dict[str, Any] | None:
    """
    One stated calendar, or None where what was stated is not a calendar this can count on.

    A calendar is usable only when it states AT LEAST ONE WORKING DAY OF THE WEEK. Everything
    else -- the id, the holidays -- may be absent and the calendar still counts; a calendar with
    no stated working day counts nothing and is refused rather than defaulted.
    """
    if not isinstance(raw, Mapping):
        return None
    days = raw.get("working_days_of_week")
    if not isinstance(days, Sequence) or isinstance(days, (str, bytes)):
        return None
    numbers: set[int] = set()
    unknown: list[str] = []
    for d in days:
        key = str(d or "").strip().lower()
        if key in WEEKDAY_NUMBERS:
            numbers.add(WEEKDAY_NUMBERS[key])
        elif key:
            unknown.append(key)
    if not numbers:
        return None
    holidays_raw = raw.get("holidays")
    holidays: set[int] = set()
    holidays_stated = isinstance(holidays_raw, Sequence) and not isinstance(
        holidays_raw, (str, bytes))
    unreadable_holidays: list[str] = []
    if holidays_stated:
        for h in holidays_raw:
            try:
                holidays.add(date.fromisoformat(str(h).strip()).toordinal())
            except ValueError:
                unreadable_holidays.append(str(h))
    return {
        "calendar_id": str(raw.get("calendar_id") or "").strip() or None,
        "working_weekdays": sorted(numbers),
        "working_days_per_week": len(numbers),
        "holiday_ordinals": sorted(holidays),
        "holidays_stated": bool(holidays_stated),
        "holiday_count": len(holidays),
        "unreadable_day_names": unknown,
        "unreadable_holiday_dates": unreadable_holidays,
    }


def read_project_calendar(si: Mapping[str, Any] | None,
                          calendar_id: str | None = None) -> dict[str, Any] | None:
    """
    THE PROJECT'S CALENDAR, or None. This is the only door into a calendar in this platform.

    `calendar_id` selects a named calendar where the caller has one -- a weather record names
    the contract calendar it was written against -- and where that name matches no calendar the
    project defines, NONE IS RETURNED. A near-match is not taken: reading a schedule against the
    wrong calendar is a wrong answer that looks like a right one.
    """
    if not isinstance(si, Mapping):
        return None
    pc = si.get("projectCalendar")
    if not isinstance(pc, Mapping):
        return None
    cals = pc.get("calendars")
    if not isinstance(cals, list) or not cals:
        return None
    normalised = [c for c in (normalise_calendar(c) for c in cals) if c]
    if not normalised:
        return None
    if calendar_id:
        want = str(calendar_id).strip().lower()
        for c in normalised:
            if (c["calendar_id"] or "").strip().lower() == want:
                return c
        return None
    default_id = str(pc.get("default_calendar_id") or "").strip().lower()
    if default_id:
        for c in normalised:
            if (c["calendar_id"] or "").strip().lower() == default_id:
                return c
    # EXACTLY ONE DEFINED CALENDAR IS UNAMBIGUOUS AND IS USED. Two or more with no stated
    # default is AMBIGUOUS, and picking the first would be choosing a calendar the project did
    # not choose, so nothing is returned and the caller says what it needs.
    return normalised[0] if len(normalised) == 1 else None


def is_working_day(cal: Mapping[str, Any], ordinal: int) -> bool:
    """One day, on this calendar. A holiday is never a working day whatever weekday it falls on."""
    if int(ordinal) in set(cal["holiday_ordinals"]):
        return False
    return date.fromordinal(int(ordinal)).weekday() in set(cal["working_weekdays"])


def working_days_between(cal: Mapping[str, Any], start_ordinal: float,
                         end_ordinal: float) -> float:
    """
    THE ONE CONVERSION. Working days from `start_ordinal` to `end_ordinal` on this calendar.

    SIGNED, and the sign is the direction of travel: forward is positive, backward negative,
    the same day is zero. The start day is EXCLUSIVE and the end day INCLUSIVE, which is the
    convention that makes "required day 100, forecast day 110" read as ten days of travel and
    makes a slack of zero mean the two dates are the same day.

    Both arguments are day ordinals -- `date.toordinal()` -- which is what `canonical_v4._day`
    already produces from an ISO date, so a register that prints dates needs no second parser.
    """
    a, b = int(round(float(start_ordinal))), int(round(float(end_ordinal)))
    if a == b:
        return 0.0
    step = 1 if b > a else -1
    count = 0
    d = a
    while d != b:
        d += step
        if is_working_day(cal, d):
            count += 1
    return float(count * step)


def working_days_in_span(cal: Mapping[str, Any], first_ordinal: int,
                         last_ordinal: int) -> int:
    """Working days in a closed span, BOTH ENDS INCLUSIVE. A period is a closed span."""
    a, b = int(first_ordinal), int(last_ordinal)
    if b < a:
        return 0
    return sum(1 for d in range(a, b + 1) if is_working_day(cal, d))


# ---------------------------------------------------------------------------------------------
# PERIOD LABELS. A1.6's curve is in PERIODS and its ladder is in WORKING DAYS, so the conversion
# needs to know what span of dates a period covers. THAT IS READ FROM THE LABEL THE BASELINE
# ITSELF PRINTS and from nothing else. A label of "2026-07" is that calendar month; a label of
# "2026-07-31" is a period ENDING that date, and its start is the day after the previous row's
# date. A label that is neither -- "Period 3", "July", a blank -- STATES NO SPAN, and the arm
# that needs one is Not Assessed. No period is assumed to be a month and none is assumed to be
# any number of days.


def _month_span(label: str) -> tuple[int, int] | None:
    parts = label.split("-")
    if len(parts) != 2:
        return None
    try:
        y, m = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if not (1 <= m <= 12) or not (1900 <= y <= 2999):
        return None
    first = date(y, m, 1)
    last = date(y + (m == 12), (m % 12) + 1, 1).toordinal() - 1
    return first.toordinal(), last


def period_spans(labels: Sequence[Any]) -> list[tuple[int, int]] | None:
    """
    The closed date span of each period, read from the labels the baseline printed, or None.

    ALL labels must be readable and of ONE kind. A curve whose labels are half months and half
    dates states no consistent period, and a curve with one unreadable label states no span for
    that period, so in either case NOTHING is returned rather than a partial answer.
    """
    texts = [str(x or "").strip() for x in labels]
    if not texts or any(not t for t in texts):
        return None
    months = [_month_span(t) for t in texts]
    if all(m is not None for m in months):
        return [m for m in months if m is not None]
    days: list[int] = []
    for t in texts:
        try:
            days.append(date.fromisoformat(t).toordinal())
        except ValueError:
            return None
    spans: list[tuple[int, int]] = []
    for i, end in enumerate(days):
        if i == 0:
            # The first row's period has no earlier row to start after, so its span is the day
            # itself. It is never assumed to reach back any number of days.
            spans.append((end, end))
        else:
            if end <= days[i - 1]:
                return None
            spans.append((days[i - 1] + 1, end))
    return spans


def working_days_per_period(cal: Mapping[str, Any],
                            labels: Sequence[Any]) -> dict[str, Any] | None:
    """
    The mean working days per period of this baseline's own periods, or None.

    A1.6's SV(t) is a number of PERIODS off the planned value curve, and the owner's ladder is a
    share of the remaining planned WORKING duration. Converting one to the other needs a working
    days per period figure, and this is it: counted on the project's own calendar over the spans
    the baseline's own labels state. It is a MEAN over the stated periods because SV(t) is a
    fractional position on the whole curve rather than a position inside one named period.
    """
    spans = period_spans(labels)
    if not spans:
        return None
    counts = [working_days_in_span(cal, a, b) for a, b in spans]
    if not counts or sum(counts) <= 0:
        return None
    return {
        "working_days_per_period": sum(counts) / len(counts),
        "period_working_days": counts,
        "period_count": len(counts),
        "period_span_basis": ("the date span each period's own printed label states, counted on "
                              "this project's stated working calendar"),
    }
