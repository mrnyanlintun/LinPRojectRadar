"""
One document's activity/milestone table, read into structured rows.

TWO GAPS CLOSED HERE, both established rather than assumed.

GAP 1, WRONG KEYS. `milestones_json` is returned by the extraction model using the TABLE'S OWN
COLUMN HEADINGS as keys, because that is what the prompt tells it to do and that instruction is
correct: reformatting a heading is the model inventing a schema. The real design activity table
returned `Activity`, `Description`, `Baseline start`, `Baseline finish`, `Complete`,
`Current finish / actual` (`REPORT_2026-08-05_extraction-substitution.md` section 1.2), while
Milestone Trend Analysis reads `name` and `forecast`. The mapping from headings to fields
belongs on THIS side of the boundary, where it is code that can be read and tested, not inside
a prompt where it would be a model's judgement.

GAP 2, DATES. See `schedule_dates.py`. A row whose current finish will not parse is unusable
for a trend and is recorded as such, by name, with the reason.

WHAT IS NOT DONE HERE. Nothing is invented for a row that did not carry it. A missing baseline
is None, not a copy of the forecast. A missing percent complete is None, not zero. An
unrecognised heading contributes nothing rather than being guessed into the nearest field.
"""

from __future__ import annotations

import re
from typing import Any

from .schedule_dates import DateRefusal, ScheduleDate, parse_schedule_date

# Headings, normalised (lowercased, non-alphanumerics collapsed to single spaces). Ordered
# within each field by preference: the first heading present in the row wins, so a table with
# both "current finish" and "finish" uses the more specific one.
_HEADINGS: dict[str, tuple[str, ...]] = {
    "activity_key": (
        "activity", "activity id", "id", "activity code", "task id",
        "milestone id", "wbs", "milestone", "task",
    ),
    "description": (
        "description", "activity description", "description of work",
        "activity name", "task name", "milestone description", "name", "title",
    ),
    "baseline_start": (
        "baseline start", "baseline start date", "planned start", "original start",
        "target start", "bl start",
    ),
    "baseline_finish": (
        "baseline finish", "baseline finish date", "baseline end", "planned finish",
        "original finish", "target finish", "bl finish",
    ),
    "current_finish": (
        "current finish actual", "current finish", "forecast finish", "actual finish",
        "current forecast finish", "forecast date", "finish date", "finish",
        "end date", "forecast", "actual", "completion date",
    ),
    "percent_complete": (
        "complete", "percent complete", "pct complete", "progress",
        "percentage complete", "activity complete", "complete",
    ),
}


def _norm(heading: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(heading).lower()).split())


def _pick(row: dict, field: str) -> Any:
    normalised = {_norm(k): v for k, v in row.items()}
    for candidate in _HEADINGS[field]:
        if candidate in normalised:
            return normalised[candidate]
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    s = " ".join(str(value).split())
    return s or None


def parse_percent_complete(value: Any) -> float | None:
    """
    A percent-complete cell, or None where the row did not carry a readable one.

    `100%`, `100`, `1 00 %` and `45.5%` read; `TBD`, an empty cell and a bare `-` do not and
    return None rather than 0. A cell out of the 0-100 range is refused for the same reason
    `validate_doc_risk_score` refuses an out-of-range score: it is not a percentage.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        n = float(value)
    else:
        s = " ".join(str(value).split()).replace("%", "").replace(",", "").strip()
        if not s:
            return None
        try:
            n = float(s)
        except ValueError:
            return None
    # A tool that writes fractions (0.45) is not distinguishable from one that writes 0.45%,
    # so no rescaling happens here: the value is read as printed or refused.
    if n < 0 or n > 100:
        return None
    return n


def _date_fields(prefix: str, raw: Any) -> tuple[dict, DateRefusal | None]:
    parsed = parse_schedule_date(raw)
    if parsed is None:
        return {prefix: None, prefix + "_kind": None}, None
    if isinstance(parsed, DateRefusal):
        return {prefix: None, prefix + "_kind": None}, parsed
    return {prefix: parsed.iso, prefix + "_kind": parsed.kind}, None


def read_activity_table(milestones: Any) -> list[dict]:
    """
    `milestones_json` (a list of row objects keyed by the table's own headings) -> activity rows.

    Each returned row is a dict with a stable schema:

      activity_key       the row's own identifier, e.g. "D100"; falls back to the description
                         when the table has no identifier column, because identity across
                         periods is what a trend matches on and a table with only descriptions
                         still has identity.
      description        the row's text, where the table carries one, else None
      baseline_start / baseline_finish / current_finish   ISO strings or None
      *_kind             "actual" or "forecast" for each parsed date, else None
      percent_complete   number or None
      unparsed           [{"field", "raw", "reason"}] for every cell that REFUSED
      usable_for_trend   False when the current finish did not parse; such a row is a missing
                         row, not a slip of zero

    A row with neither an identifier nor a description has no identity and is dropped: it
    cannot be matched to itself in the next period, and matching it positionally would compare
    two different activities.
    """
    if not isinstance(milestones, list):
        return []
    out: list[dict] = []
    for raw_row in milestones:
        if not isinstance(raw_row, dict):
            continue
        key = _text(_pick(raw_row, "activity_key"))
        description = _text(_pick(raw_row, "description"))
        identity = key or description
        if not identity:
            continue
        row: dict[str, Any] = {
            "activity_key": identity,
            "description": description,
            "percent_complete": parse_percent_complete(_pick(raw_row, "percent_complete")),
        }
        unparsed: list[dict] = []
        for field in ("baseline_start", "baseline_finish", "current_finish"):
            fields, refusal = _date_fields(field, _pick(raw_row, field))
            row.update(fields)
            if refusal is not None:
                unparsed.append({"field": field, **refusal.as_dict()})
        row["unparsed"] = unparsed
        row["usable_for_trend"] = row["current_finish"] is not None
        out.append(row)
    return out


def refusal_lines(rows: list[dict]) -> list[str]:
    """
    One human-readable line per refused cell, NAMING THE ROW.

    "loud refusal over quiet approximation": a schedule read with three unusable rows must say
    which three and why, not report six activities as though nine were read.
    """
    lines: list[str] = []
    for row in rows:
        for u in row.get("unparsed") or []:
            lines.append(
                f"{row['activity_key']}: {u['field']} {u['raw']!r} not read ({u['reason']})"
            )
    return lines


__all__ = [
    "read_activity_table",
    "parse_percent_complete",
    "refusal_lines",
    "ScheduleDate",
    "DateRefusal",
]
