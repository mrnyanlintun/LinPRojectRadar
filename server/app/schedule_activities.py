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
from datetime import date
from typing import Any

from .schedule_dates import ACTUAL, DateRefusal, ScheduleDate, parse_schedule_date

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
    # ORDER MATTERS, AND IS NOT ALPHABETICAL. A real schedule extract carries an "Actual finish"
    # column AND a "Forecast finish" column side by side, and exactly one of them is filled per
    # row: a finished activity has an actual and a blank forecast, a live one has a forecast and
    # a blank actual. The actual comes first because where both are present the actual is the
    # fact and the forecast is the prediction it has already overtaken. `_pick_all` then tries
    # the whole chain in order and takes the first candidate that yields a DATE, so the blank
    # column never wins by being listed first.
    "current_finish": (
        "current finish actual", "current finish", "actual finish", "forecast finish",
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


def _pick_all(row: dict, field: str) -> list[tuple[str, Any]]:
    """Every (normalised heading, value) in the row mapping to `field`, in preference order."""
    normalised = {_norm(k): v for k, v in row.items()}
    return [(c, normalised[c]) for c in _HEADINGS[field] if c in normalised]


def kind_from_heading(heading: str) -> str | None:
    """
    `actual` when the COLUMN ITSELF says the dates under it are actuals, else None.

    This reads a fact the document states, in the same way the trailing `A` marker on a cell
    does. A column headed "Actual finish" is the document saying every date in it is a recorded
    finish, not a prediction; taking the date and dropping that would turn a fact into a
    forecast, which is exactly what `schedule_dates` refuses to do at the cell level. A column
    headed "Current finish / actual" is NOT this: it is one column holding both kinds, and only
    the cell's own marker can say which a given row is.
    """
    n = _norm(heading)
    if n in ("actual finish", "actual"):
        return ACTUAL
    return None


def map_headings(headings) -> dict[str, str]:
    """
    A table's own column headings -> the fields this store keeps. `{field: heading}`.

    THE MAPPING LIVES HERE AND NOT IN A PROMPT. It is the one judgement the activity table
    needs, it is made once per table rather than once per row, and as code it can be read and
    tested. An unrecognised heading contributes nothing rather than being guessed into the
    nearest field. Where two headings map to the same field the earlier one in `_HEADINGS`
    wins, which is the same preference order `_pick_all` walks.
    """
    seen = {}
    for h in headings or []:
        n = _norm(h)
        if n and n not in seen:
            seen[n] = str(h)
    out: dict[str, str] = {}
    for field, candidates in _HEADINGS.items():
        for candidate in candidates:
            if candidate in seen:
                out[field] = seen[candidate]
                break
    return out


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
        for field in ("baseline_start", "baseline_finish"):
            fields, refusal = _date_fields(field, _pick(raw_row, field))
            row.update(fields)
            if refusal is not None:
                unparsed.append({"field": field, **refusal.as_dict()})
        # THE CURRENT FINISH MAY BE SPREAD OVER TWO COLUMNS. A real Level 3 extract has an
        # "Actual finish" and a "Forecast finish" and fills exactly one of them per row, the
        # other holding an em-dash placeholder that this parser correctly refuses. Reading only
        # the first mapped column would therefore lose the finish date of every completed
        # activity, or of every live one, depending on which column was listed first. The whole
        # chain is walked in preference order and the first candidate that yields a DATE wins.
        # If none does, the first candidate that held anything at all carries the refusal, so
        # the row still says why it is unusable rather than going quiet.
        candidates = _pick_all(raw_row, "current_finish")
        chosen: dict | None = None
        first_refusal: DateRefusal | None = None
        for heading, candidate in candidates:
            fields, refusal = _date_fields("current_finish", candidate)
            if fields["current_finish"] is not None:
                # The column's own heading can state the kind. The CELL's marker wins where it
                # said something, because a cell is more specific than a column.
                if fields["current_finish_kind"] != ACTUAL:
                    fields["current_finish_kind"] = (
                        kind_from_heading(heading) or fields["current_finish_kind"])
                chosen = fields
                break
            if refusal is not None and first_refusal is None:
                first_refusal = refusal
        if chosen is None:
            chosen = {"current_finish": None, "current_finish_kind": None}
            if first_refusal is not None:
                unparsed.append({"field": "current_finish", **first_refusal.as_dict()})
        row.update(chosen)
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


# --------------------------------------------------------------------- what gets drawn

# The near-term horizon: how many not-yet-finished activities are shown simply because they are
# next. Five is a working fortnight's worth of fronts on a real job and is a display choice, not
# a fact about any schedule.
NEXT_HORIZON = 5

# The hard ceiling on drawn rows. A schedule of two thousand activities and one of twenty draw
# the same amount of page, which is the point: the store is unbounded and the display is not.
MAX_DRAWN = 20

DISPLAY_RULE = (
    "Shown: every activity whose forecast finish moved later since the previous period, every "
    "activity forecast to finish later than its own baseline finish, the next five activities "
    "due to finish, and the last activity in the schedule. Ordered by how far each has moved, "
    "then by finish date, and capped at 20 rows. Everything else is stored and not drawn."
)


def select_for_display(rows: list[dict], previous: list[dict] | None = None) -> dict:
    """
    Which activities to draw, from a schedule of ANY size. Pure, so it can be tested directly.

    THE RULE IS STATED, NOT IMPLIED. A schedule with a thousand activities has a thousand rows
    worth reading and no screen worth putting them on, and a display that draws all of them is
    the same unbounded failure as an extraction that returns all of them. What earns a row here
    is movement, lateness against plan, imminence, or being the end of the job; everything else
    is in the store, is queryable, and is counted rather than drawn.

    `previous` is the same project's rows for the preceding period, used only to decide MOVEMENT.
    Absent, or absent for a given activity, no movement is claimed: an activity that was not
    there last period has not moved, it has arrived, and the two are not the same fact. That is
    the same rule Milestone Trend Analysis applies and it is applied for the same reason.
    """
    drawn: dict[str, dict] = {}
    reasons: dict[str, list[str]] = {}

    def mark(row: dict, reason: str) -> None:
        key = row["activity_key"]
        drawn.setdefault(key, row)
        reasons.setdefault(key, [])
        if reason not in reasons[key]:
            reasons[key].append(reason)

    prior = {r["activity_key"]: r for r in (previous or [])}
    slip_days: dict[str, int] = {}
    for row in rows:
        was = prior.get(row["activity_key"])
        if was and was.get("current_finish") and row.get("current_finish"):
            moved = (date.fromisoformat(row["current_finish"])
                     - date.fromisoformat(was["current_finish"])).days
            if moved > 0:
                slip_days[row["activity_key"]] = moved
                mark(row, "moved later since the previous period")
        if row.get("current_finish") and row.get("baseline_finish") \
                and row["current_finish"] > row["baseline_finish"]:
            mark(row, "later than its baseline finish")

    with_finish = [r for r in rows if r.get("current_finish")]
    unfinished = sorted(
        (r for r in with_finish
         if r.get("current_finish_kind") != ACTUAL and (r.get("percent_complete") or 0) < 100),
        key=lambda r: (r["current_finish"], r["activity_key"]),
    )
    for row in unfinished[:NEXT_HORIZON]:
        mark(row, "next to finish")
    if with_finish:
        mark(max(with_finish, key=lambda r: (r["current_finish"], r["activity_key"])),
             "the last activity in the schedule")

    ordered = sorted(
        drawn.values(),
        key=lambda r: (-slip_days.get(r["activity_key"], 0),
                       r.get("current_finish") or "9999-12-31", r["activity_key"]),
    )[:MAX_DRAWN]
    shown = [
        {**{k: r.get(k) for k in ("activity_key", "description", "baseline_finish",
                                  "current_finish", "current_finish_kind", "percent_complete",
                                  "usable_for_trend")},
         "slip_days": slip_days.get(r["activity_key"]),
         "shown_because": reasons[r["activity_key"]]}
        for r in ordered
    ]
    return {
        "shown": shown,
        "total": len(rows),
        "not_shown": max(0, len(rows) - len(shown)),
        "unusable": sum(1 for r in rows if not r.get("usable_for_trend")),
        "rule": DISPLAY_RULE,
    }


__all__ = [
    "DISPLAY_RULE",
    "map_headings",
    "select_for_display",
    "read_activity_table",
    "parse_percent_complete",
    "refusal_lines",
    "ScheduleDate",
    "DateRefusal",
]
