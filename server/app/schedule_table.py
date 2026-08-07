"""
The activity table, taken from the document by the reader instead of retyped by the model.

THE DEFECT THIS EXISTS FOR, measured rather than supposed. A real schedule status document
carrying twenty-nine Level 3 activities in an eleven-column table failed extraction three times
with the same message, `model response was not JSON`, on a response that was valid JSON cut off
mid-key. `milestones_json` asked the model to serialise the whole table into one field of the
same response that carries the scalar fields, and the response ran out of output tokens at the
seventh key, before it reached the table at all.

Twenty-nine is small. A real construction schedule carries hundreds or thousands of activities,
so NO output cap is large enough: the input is unbounded, and raising the cap buys one document
and fails on the next.

THE FIX IS STRUCTURAL. The activities are already rows and columns in the source, and the docx
reader already renders tables as grids with merged cells expanded. The only judgement the table
needs is WHICH COLUMN CARRIES WHAT, and that is one decision per table rather than one per row.
This module makes it, from the heading vocabulary in `schedule_activities.map_headings`, and
then takes the rows directly. A hundred rows and a hundred thousand rows cost the same, because
neither is sent to the model and neither is asked back from it.

A SECOND CONSEQUENCE, worth stating because nothing would have caught it. A model retyping five
hundred rows will get some of them wrong, silently, and the platform has no way to notice: the
rows would be well-formed, in-range and plausible. Rows the reader takes are the document's own
cells.

WHAT IS NOT DONE HERE. Nothing is invented. A table whose headings do not resolve an identity
column and a finish column is not the activity table and is not guessed at; the caller is told
no activity table was recognised, and the document's other fields extract as normal.
"""
from __future__ import annotations

from typing import Any

from .schedule_activities import map_headings

# A table has to resolve an identity AND a finish date before it is treated as the activity
# table. Both, because a two-column contact list resolves a name and a summary block resolves a
# date, and neither is a schedule. This is the recognition rule, stated once.
_IDENTITY_FIELDS = ("activity_key", "description")
_REQUIRED_WITH_IDENTITY = ("current_finish", "baseline_finish")

# A header row and a single data row is a summary line, not a table of activities. Two data rows
# is the smallest thing that can honestly be called a list.
MIN_DATA_ROWS = 2


class ActivityTable:
    """One recognised activity table: where it sat, what its columns mean, and its rows."""

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
        """
        Rows keyed by the table's own column headings.

        This is exactly the shape `schedule_activities.read_activity_table` already consumes, so
        the parser, the refusal reporting and the storage projection are unchanged: only where
        the rows come from has changed. A row longer than the header is truncated to the header
        and a shorter one is padded, because a cell with no heading has no meaning to record.
        """
        out: list[dict] = []
        width = len(self.headings)
        for row in self.rows:
            cells = list(row[:width]) + [""] * max(0, width - len(row))
            out.append({h: c for h, c in zip(self.headings, cells) if str(h).strip()})
        return out

    def descriptor(self, source: str) -> dict:
        """
        The small, BOUNDED record of what was read, safe to store on the extraction.

        It names the table, its columns and how many rows it had. It does NOT contain the rows:
        the rows go to the per-activity store, one row each, which is the only place a schedule
        of unknown size can live without a JSON field growing without limit.
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

        The header row survives so the model can still see the document HAS a schedule and can
        still answer a scalar field about it; the rows do not, because they are the unbounded
        part and the platform has already read them.
        """
        return (
            "| " + " | ".join(self.headings) + " |\n"
            f"[ACTIVITY TABLE: {self.row_count} data row(s) under the headings above. The "
            "platform read these rows directly from the document, so they are not reproduced "
            "here and must not be returned in your answer.]"
        )


def _score(headings: list[str]) -> tuple[int, dict[str, str]] | None:
    column_map = map_headings(headings)
    if not any(f in column_map for f in _IDENTITY_FIELDS):
        return None
    if not any(f in column_map for f in _REQUIRED_WITH_IDENTITY):
        return None
    return len(column_map), column_map


def find_activity_table(tables: list[list[list[str]]]) -> ActivityTable | None:
    """
    The activity table among a document's tables, or None when none is recognised.

    The FIRST row of each table is read as its headings. That is the same convention
    `docx_text._table_text` states and it is a convention rather than a fact about any document;
    a table whose first row is not headings simply fails to resolve and is passed over, which is
    the safe direction.

    Where more than one table qualifies, the one resolving the most columns wins, and an exact
    tie goes to the earlier table. A document with a summary milestone block and a full activity
    extract should be read from the extract, and the extract is the one carrying more of the
    columns this store keeps.
    """
    best: ActivityTable | None = None
    best_score = -1
    for index, grid in enumerate(tables or []):
        if len(grid) < MIN_DATA_ROWS + 1:
            continue
        headings = [str(c).strip() for c in grid[0]]
        scored = _score(headings)
        if scored is None:
            continue
        score, column_map = scored
        if score > best_score:
            best, best_score = ActivityTable(index, headings, grid[1:], column_map), score
    return best


def activity_table_from_document(raw: bytes, mime_type: str = "",
                                 filename: str = "") -> ActivityTable | None:
    """
    The activity table in a document the reader can open, or None.

    Only a .docx is opened here, and that is stated rather than quietly true: `docx_text` is the
    platform's one local document reader, and it is what already renders tables as grids with
    horizontal merges expanded. A PDF is sent to the model as a document block and its tables
    are not available to this side of the boundary at all; that limit is real and is reported,
    not worked around by guessing at layout.
    """
    from .docx_text import DocxReadError, docx_tables, is_docx

    if not is_docx(raw, mime_type, filename):
        return None
    try:
        tables = docx_tables(raw)
    except DocxReadError:
        return None
    return find_activity_table(tables)


def activity_rows_from_document(raw: bytes, mime_type: str = "",
                                filename: str = "") -> list[dict]:
    """The document's activity rows, parsed, or [] where no activity table was recognised."""
    from .schedule_activities import read_activity_table

    table = activity_table_from_document(raw, mime_type, filename)
    if table is None:
        return []
    return read_activity_table(table.as_row_dicts())


def descriptor_row_count(descriptor: Any) -> int | None:
    """The row count a stored descriptor claims, or None when it is not one."""
    if isinstance(descriptor, dict):
        n = descriptor.get("row_count")
        if isinstance(n, int) and n >= 0:
            return n
    return None


__all__ = [
    "ActivityTable",
    "activity_rows_from_document",
    "activity_table_from_document",
    "descriptor_row_count",
    "find_activity_table",
    "descriptor_row_count",
]
