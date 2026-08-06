"""
The date shapes a real project schedule actually carries, and the ones it refuses.

WHY THIS FILE EXISTS. `date.fromisoformat` was the only date parser anywhere in `server/app`,
and it accepts strict `YYYY-MM-DD` only. A real design activity table
(`REPORT_2026-08-05_extraction-substitution.md` section 4) carried `29-May`, `14 August 2026`
and `24-Mar-26 A` in ONE column of nine rows. None of the three parsed, so the schedule could
not be read at all, and Milestone Trend Analysis has never computed.

TWO RULES GOVERN THIS FILE, AND THEY MATTER MORE THAN HOW MANY SHAPES IT COVERS.

1. A DATE THAT CANNOT BE PARSED REFUSES. It never guesses.

   `29-May` states no year. The year is NOT resolved from the document's reporting period or
   its data date, and this function takes no context argument at all, so no caller can offer
   one. That is deliberate, and it is the same class of defect the extraction prompt was
   already fixed for: a value of the right type sitting nearby is not a source for a value the
   document does not state. A March 2026 status report may legitimately carry a `29-May` that
   means May 2025 (an activity that finished late in the previous year, still listed) or May
   2026 (the next forecast). Nothing in the row distinguishes them. A row whose current finish
   will not parse is UNUSABLE and says so, by name, rather than contributing a guessed date to
   a slip calculation.

   Expanding a TWO-DIGIT year (`26` in `24-Mar-26`) is NOT the same thing and is done: the
   document states a year, abbreviated by a convention the scheduling tool applies to every
   row. The window is fixed (00-69 -> 2000s, 70-99 -> 1900s) and stated here rather than
   derived from any document.

2. AN ACTUAL DATE AND A FORECAST DATE ARE DIFFERENT FACTS, AND THE DISTINCTION SURVIVES.

   The trailing `A` in `24-Mar-26 A` is standard Primavera P6 / Microsoft Project export
   notation: the date is an ACTUAL, the activity finished on it, and it will not move again.
   Every other date in that column is a forecast, which is exactly the thing that can slip.
   Stripping the `A` would turn a recorded fact into a prediction. `ScheduleDate.kind` carries
   it, storage keeps it, and a reader can tell the two apart.

An unrecognised trailing marker is refused rather than ignored: a scheduling tool that marks
something we have not established the meaning of is telling us something, and dropping the
marker to salvage the date is the same guess as inventing a year.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

ACTUAL = "actual"
FORECAST = "forecast"

# The two-digit-year window. Stated once, applied to every row, never document-derived.
_CENTURY_PIVOT = 70

_MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Values that are present in the cell but are plainly not dates. These REFUSE (they are a
# statement that no date is known) rather than being treated as an empty cell.
_NON_DATES = {"tbd", "tba", "n/a", "na", "none", "-", "--", "?", "unknown", "pending"}

_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_DAY_MON_YEAR = re.compile(r"^(\d{1,2})[-/ ]([A-Za-z]{3,9})\.?[-/ ](\d{2}|\d{4})$")
_MON_DAY_YEAR = re.compile(r"^([A-Za-z]{3,9})\.?[-/ ](\d{1,2}),?[-/ ](\d{2}|\d{4})$")
_DAY_MON_ONLY = re.compile(r"^(\d{1,2})[-/ ]([A-Za-z]{3,9})\.?$")
_MON_DAY_ONLY = re.compile(r"^([A-Za-z]{3,9})\.?[-/ ](\d{1,2})$")
_ALL_NUMERIC = re.compile(r"^\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}$")


@dataclass(frozen=True)
class ScheduleDate:
    """A date the document stated, and whether the document called it actual or forecast."""

    value: date
    kind: str
    raw: str

    @property
    def iso(self) -> str:
        return self.value.isoformat()

    def as_dict(self) -> dict:
        return {"date": self.iso, "kind": self.kind, "raw": self.raw}


@dataclass(frozen=True)
class DateRefusal:
    """A cell that held something, which this parser will not turn into a date."""

    raw: str
    reason: str

    def as_dict(self) -> dict:
        return {"raw": self.raw, "reason": self.reason}


def _month(name: str) -> int | None:
    return _MONTHS.get(name.strip().lower().rstrip("."))


def _expand_year(text: str) -> int:
    n = int(text)
    if len(text) == 4:
        return n
    return 1900 + n if n >= _CENTURY_PIVOT else 2000 + n


def _build(y: int, m: int, d: int, kind: str, raw: str) -> ScheduleDate | DateRefusal:
    try:
        return ScheduleDate(date(y, m, d), kind, raw)
    except ValueError:
        return DateRefusal(raw, f"no such calendar date: day {d} of month {m}, {y}")


def _split_marker(text: str) -> tuple[str, str, str | None]:
    """
    Peel a scheduling tool's trailing status marker off the date.

    Returns (date_text, kind, refusal_reason). `A` means actual (P6 and Project both write it).
    Anything else trailing is refused: we have not established what it means, and dropping it
    to salvage the date would discard a fact the document stated.
    """
    parts = text.split()
    if len(parts) == 1:
        return text, FORECAST, None
    body, marker = " ".join(parts[:-1]), parts[-1]
    if marker.upper() == "A":
        return body, ACTUAL, None
    # A spelled-out month makes the last token part of the date, not a marker.
    if _month(marker) is not None or marker.isdigit():
        return text, FORECAST, None
    return text, FORECAST, f"unrecognised schedule marker {marker!r}"


def parse_schedule_date(raw) -> ScheduleDate | DateRefusal | None:
    """
    Read one schedule date cell exactly as the document printed it.

    Returns `ScheduleDate` when the document states a full date, `DateRefusal` when the cell
    holds something this parser will not guess at, and `None` when the cell is EMPTY — an
    absent value is not a refusal, it is simply a column the row did not fill in.

    NO CONTEXT ARGUMENT, ON PURPOSE. See the module docstring: a year the document does not
    state is not available from anywhere else.
    """
    if raw is None:
        return None
    text = " ".join(str(raw).split())
    if not text:
        return None
    if text.lower() in _NON_DATES:
        return DateRefusal(text, "not a date: the cell states no date")

    body, kind, marker_problem = _split_marker(text)
    if marker_problem:
        return DateRefusal(text, marker_problem)

    m = _ISO.match(body)
    if m:
        return _build(int(m.group(1)), int(m.group(2)), int(m.group(3)), kind, text)

    m = _DAY_MON_YEAR.match(body)
    if m:
        mo = _month(m.group(2))
        if mo is None:
            return DateRefusal(text, f"unrecognised month name {m.group(2)!r}")
        return _build(_expand_year(m.group(3)), mo, int(m.group(1)), kind, text)

    m = _MON_DAY_YEAR.match(body)
    if m:
        mo = _month(m.group(1))
        if mo is None:
            return DateRefusal(text, f"unrecognised month name {m.group(1)!r}")
        return _build(_expand_year(m.group(3)), mo, int(m.group(2)), kind, text)

    if _DAY_MON_ONLY.match(body) or _MON_DAY_ONLY.match(body):
        return DateRefusal(
            text,
            "no year stated: the year is not inferred from the reporting period or data date",
        )

    if _ALL_NUMERIC.match(body):
        return DateRefusal(
            text, "all-numeric date: day and month order is ambiguous and is not guessed"
        )

    return DateRefusal(text, "unrecognised date format")
