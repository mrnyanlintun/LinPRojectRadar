"""
The risk register's table, taken from the document by the reader instead of retyped by the model.

THE SAME TREATMENT THE SCHEDULE GOT, AND FOR THE SAME REASON. A real register carries hundreds of
risks. Asking a model to serialise them into one field of its response costs output tokens in
proportion to the row count and stops working somewhere above a few dozen, which is exactly how
`milestones_json` failed on a twenty-nine row schedule. The rows are already rows and columns in
the source. The only judgement the table needs is WHICH COLUMN CARRIES WHAT, and that is one
decision per table rather than one per row. This module makes it, in code, and then takes the
rows directly. Twenty rows and five hundred rows cost the same model call, because neither is
sent to the model and neither is asked back from it.

WHY THE COLUMN MAPPING IS CODE AND NOT A PROMPT. `schedule_activities` states this and it holds
here: a mapping inside a prompt is a model's judgement, unreviewable and untestable, and it
changes silently between runs. Here it is a table of heading vocabulary that a person can read
and a check can pin.

ONE MODULE RATHER THAN TWO. The schedule splits recognition (`schedule_table`) from row parsing
(`schedule_activities`) because the second predated the first. There is no such history here, so
recognition and parsing sit together; the boundary that actually matters, between reading a
document and deciding anything about a project, is still absolute. Nothing in this file computes,
scores, ranks or forecasts.

WHAT IS NOT DONE HERE. Nothing is invented for a cell that did not carry it. A probability stated
as a word stays a word (see `risk_values`), a missing owner is None rather than "unassigned", and
a table whose headings do not resolve an identity and a likelihood or an impact is not a risk
register and is not guessed at.
"""

from __future__ import annotations

import re
from typing import Any

from .risk_values import (
    RiskProbability, ValueRefusal, is_blank, parse_duration_days, parse_money,
    parse_open_closed, parse_probability, parse_score,
)

# Headings, normalised (lowercased, non-alphanumerics collapsed to single spaces). Ordered
# within each field by preference: the first heading present in the row wins, so a table with
# both "residual score" and "score" uses the more specific one for the residual position.
_HEADINGS: dict[str, tuple[str, ...]] = {
    "risk_key": (
        "risk id", "risk no", "risk number", "risk ref", "ref", "id", "no", "number",
        "risk code", "item", "risk item",
    ),
    "description": (
        "risk description", "description", "risk", "risk event", "event", "description of risk",
        "risk statement", "title", "name", "threat",
    ),
    "category": (
        "risk category", "category", "type", "risk type", "classification", "area",
        "discipline",
    ),
    "probability": (
        "probability", "likelihood", "probability of occurrence", "chance",
        "likelihood rating", "probability rating", "p",
    ),
    "cost_impact": (
        "cost impact", "cost", "cost consequence", "financial impact", "impact cost",
        "cost exposure", "value at risk", "estimated cost impact", "cost effect",
    ),
    "time_impact": (
        "time impact", "schedule impact", "delay", "programme impact", "program impact",
        "duration impact", "time consequence", "days impact",
    ),
    "score": (
        "risk score", "score", "rating", "risk rating", "severity", "exposure",
        "risk exposure", "pi score", "p i score",
    ),
    "owner": (
        "risk owner", "owner", "assigned to", "responsible", "responsibility", "action owner",
        "accountable",
    ),
    "response_strategy": (
        "response strategy", "response", "strategy", "risk response", "treatment",
        "treatment strategy", "action", "response type", "mitigation strategy",
    ),
    "mitigation_status": (
        "mitigation status", "mitigation", "mitigation actions", "action status",
        "mitigation plan", "controls", "current controls", "progress",
    ),
    "residual_position": (
        "residual risk", "residual", "residual score", "residual rating", "post mitigation",
        "post mitigation score", "residual position", "net risk",
    ),
    "status": (
        "status", "open closed", "open or closed", "risk status", "state", "current status",
    ),
}

# A table must resolve an identity AND something that makes it a RISK register rather than any
# other list, which is a likelihood or an impact or a score. Both, because a two-column contact
# list resolves a name and an owner, and neither is a register. This is the recognition rule.
_IDENTITY_FIELDS = ("risk_key", "description")
_RISK_BEARING_FIELDS = ("probability", "cost_impact", "time_impact", "score")

# A header row and a single data row is a summary line, not a register.
MIN_DATA_ROWS = 2


def _norm(heading: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(heading).lower()).split())


# Trailing words that state a UNIT or CURRENCY and nothing else. A register heading is very
# often "Cost Impact (USD)" or "Schedule Impact (days)", and an exact-match table misses both:
# measured on the first realistic register tried here, "Schedule Impact (days)" resolved to no
# field at all and every time impact in the table was silently dropped. The unit is not noise --
# it is what makes a bare number in that column readable at all -- so it is tolerated in the
# match AND read by `_heading_unit`.
#
# Deliberately units only. A qualifier like "rating" or "score" CHANGES what a column means, so
# it is not in this set and "Probability Rating" does not collapse onto "Probability".
_UNIT_QUALIFIERS = {
    "days", "day", "weeks", "week", "months", "month", "hours", "hrs",
    "usd", "us", "dollars", "dollar", "percent", "pct", "per", "cent", "s",
    "000", "k", "m",
}


def map_headings(headings: list[str]) -> dict[str, str]:
    """
    Which of this table's headings carries which field. One decision per table.

    Returns `{field: the heading verbatim}` for every field resolved, and omits the rest. A
    heading that matches nothing contributes nothing rather than being guessed into the nearest
    field, and a field with no heading is simply absent.

    Matching is exact first, across every field, and only then falls back to allowing a trailing
    unit qualifier. Exact-first matters: it stops "Cost" claiming the "Cost Impact (USD)" column
    while an exact "Cost Impact" heading sits unclaimed later in the same row.
    """
    normalised = {_norm(h): h for h in headings if str(h).strip()}
    out: dict[str, str] = {}
    taken: set[str] = set()

    for field, candidates in _HEADINGS.items():
        for candidate in candidates:
            if candidate in normalised and normalised[candidate] not in taken:
                out[field] = normalised[candidate]
                taken.add(normalised[candidate])
                break

    for field, candidates in _HEADINGS.items():
        if field in out:
            continue
        for candidate in candidates:
            for norm_heading, original in normalised.items():
                if original in taken or not norm_heading.startswith(candidate + " "):
                    continue
                remainder = norm_heading[len(candidate):].split()
                if remainder and all(word in _UNIT_QUALIFIERS for word in remainder):
                    out[field] = original
                    taken.add(original)
                    break
            if field in out:
                break
    return out


def _heading_says_percent(heading: str) -> bool:
    """Does the column heading itself state that its numbers are percentages?"""
    h = str(heading).lower()
    return "%" in h or "per cent" in h or "percent" in h or "pct" in h


def _heading_unit(heading: str) -> str | None:
    """The duration unit the column heading states, or None."""
    h = _norm(heading)
    for unit in ("days", "day", "weeks", "week", "months", "month"):
        if unit in h.split():
            return unit
    return None


class RiskTable:
    """One recognised risk register table: where it sat, what its columns mean, and its rows."""

    def __init__(self, index: int, headings: list[str], rows: list[list[str]],
                 column_map: dict[str, str]) -> None:
        self.index = index
        self.headings = headings
        self.rows = rows
        self.column_map = column_map

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def as_row_dicts(self) -> list[dict]:
        """Rows keyed by the table's own column headings."""
        out: list[dict] = []
        width = len(self.headings)
        for row in self.rows:
            cells = list(row[:width]) + [""] * max(0, width - len(row))
            out.append({h: c for h, c in zip(self.headings, cells) if str(h).strip()})
        return out

    def descriptor(self, source: str) -> dict:
        """
        The small, BOUNDED record of what was read, safe to store on the extraction.

        Names the table, its columns and how many rows it had. It does NOT contain the rows: the
        rows go to the per-risk store, one row each, which is the only place a register of
        unknown size can live without a JSON field growing without limit.
        """
        return {
            "source": source,
            "table_index": self.index,
            "headings": list(self.headings),
            "column_map": dict(self.column_map),
            "row_count": self.row_count,
        }

    def elision_note(self) -> str:
        """
        What stands where the table stood in the text sent to the model.

        The header row survives so the model can still see the document HAS a register and can
        still answer a scalar field about it; the rows do not, because they are the unbounded
        part and the platform has already read them.
        """
        return (
            "| " + " | ".join(self.headings) + " |\n"
            f"[RISK REGISTER TABLE: {self.row_count} data row(s) under the headings above. The "
            "platform read these rows directly from the document, so they are not reproduced "
            "here and must not be returned in your answer.]"
        )


def _score_table(headings: list[str]) -> tuple[int, dict[str, str]] | None:
    column_map = map_headings(headings)
    if not any(f in column_map for f in _IDENTITY_FIELDS):
        return None
    if not any(f in column_map for f in _RISK_BEARING_FIELDS):
        return None
    return len(column_map), column_map


def find_risk_table(tables: list[list[list[str]]]) -> RiskTable | None:
    """
    The risk register table among a document's tables, or None when none is recognised.

    The FIRST row of each table is read as its headings, the same convention the schedule reader
    states. Where more than one table qualifies the one resolving the most columns wins, and an
    exact tie goes to the earlier table: a document with a summary count block and a full
    register should be read from the register, and the register carries more of these columns.
    """
    best: RiskTable | None = None
    best_score = -1
    for index, grid in enumerate(tables or []):
        if len(grid) < MIN_DATA_ROWS + 1:
            continue
        headings = [str(c).strip() for c in grid[0]]
        scored = _score_table(headings)
        if scored is None:
            continue
        score, column_map = scored
        if score > best_score:
            best, best_score = RiskTable(index, headings, grid[1:], column_map), score
    return best


def risk_table_from_document(raw: bytes, mime_type: str = "",
                             filename: str = "") -> RiskTable | None:
    """
    The risk table in a document the reader can open, or None.

    Only a .docx is opened here, stated rather than quietly true: a PDF is sent to the model as
    a document block and its tables are not available on this side of the boundary at all. That
    limit is real and is reported, not worked around by guessing at layout.
    """
    from .docx_text import DocxReadError, docx_tables, is_docx

    if not is_docx(raw, mime_type, filename):
        return None
    try:
        tables = docx_tables(raw)
    except DocxReadError:
        return None
    return find_risk_table(tables)


def _text_or_none(value: Any) -> str | None:
    cleaned = " ".join(str(value if value is not None else "").split()).strip()
    return None if is_blank(cleaned) else cleaned


def read_risk_table(rows: list[dict], column_map: dict[str, str] | None = None) -> list[dict]:
    """
    Parsed risks, one dict per row, in the table's own order.

    Every value goes through `risk_values`, so a cell that cannot be read REFUSES and is recorded
    in `unparsed` with its reason and the field it was refused for. A row's refusals never remove
    the row: a register of two hundred risks that yielded ninety usable probabilities has to be
    able to say which hundred and ten refused and why, and a dropped row cannot.

    `usable_for_exposure` is the one derived flag, and it derives nothing: it is true when the
    row carries BOTH a numeric probability and a numeric cost impact, which is precisely the pair
    a cost distribution needs. A row scored only in bands is not usable for exposure and says so,
    which is what makes the forecasting modules abstain honestly rather than inventing a number.

    A row with no identity at all (no id and no description) is skipped: it is a spacer or a
    section heading inside the table, not a risk.
    """
    cmap = column_map or {}
    prob_heading = cmap.get("probability", "")
    time_heading = cmap.get("time_impact", "")
    prob_is_percent = _heading_says_percent(prob_heading)
    time_unit = _heading_unit(time_heading)

    out: list[dict] = []
    for position, row in enumerate(rows or []):
        normalised = {_norm(k): v for k, v in row.items()}

        def cell(field: str) -> Any:
            heading = cmap.get(field)
            if heading is not None:
                return normalised.get(_norm(heading))
            for candidate in _HEADINGS[field]:
                if candidate in normalised:
                    return normalised[candidate]
            return None

        risk_key = _text_or_none(cell("risk_key"))
        description = _text_or_none(cell("description"))
        if risk_key is None and description is None:
            continue

        unparsed: list[dict] = []

        def take(field: str, parser, **kwargs):
            raw = cell(field)
            result = parser(raw, **kwargs)
            if isinstance(result, ValueRefusal):
                entry = result.as_dict()
                entry["field"] = field
                unparsed.append(entry)
                return None
            return result

        probability = take("probability", parse_probability, column_is_percent=prob_is_percent)
        cost_impact = take("cost_impact", parse_money)
        time_impact = take("time_impact", parse_duration_days, column_unit=time_unit)
        score = take("score", parse_score)
        is_open = take("status", parse_open_closed)

        prob_value = probability.value if isinstance(probability, RiskProbability) else None
        prob_band = probability.band if isinstance(probability, RiskProbability) else None
        prob_raw = probability.raw if isinstance(probability, RiskProbability) else None

        out.append({
            # A register that numbers its rows is keyed by its own numbers. One that does not is
            # keyed by position in the table, prefixed so the two can never be confused. Position
            # is stable for a content-addressed document, which is what makes recomputation of an
            # earlier period byte-identical.
            "risk_key": risk_key or f"row-{position + 1}",
            "keyed_by_position": risk_key is None,
            "description": description,
            "category": _text_or_none(cell("category")),
            "probability": prob_value,
            "probability_band": prob_band,
            "probability_raw": prob_raw,
            "cost_impact": cost_impact,
            "time_impact_days": time_impact,
            "score": score,
            "owner": _text_or_none(cell("owner")),
            "response_strategy": _text_or_none(cell("response_strategy")),
            "mitigation_status": _text_or_none(cell("mitigation_status")),
            "residual_position": _text_or_none(cell("residual_position")),
            "is_open": is_open,
            "unparsed": unparsed or None,
            "usable_for_exposure": prob_value is not None and cost_impact is not None,
        })
    return out


def risk_rows_from_document(raw: bytes, mime_type: str = "",
                            filename: str = "") -> list[dict]:
    """The document's risk rows, parsed, or [] where no register table was recognised."""
    table = risk_table_from_document(raw, mime_type, filename)
    if table is None:
        return []
    return read_risk_table(table.as_row_dicts(), table.column_map)


__all__ = [
    "MIN_DATA_ROWS",
    "RiskTable",
    "find_risk_table",
    "map_headings",
    "read_risk_table",
    "risk_rows_from_document",
    "risk_table_from_document",
]
