"""
RUN 86. THE LOOK-AHEAD ACTIVITY TABLE, READ FROM THE DOCUMENT THAT PRINTS IT.

WHAT THIS CLOSES. A2.8 Look-Ahead Schedule Health abstained on "a governed look ahead
schedule", and the only thing the platform ever asked a look-ahead document for was a pair of
COUNTS (`activities_planned`, `activities_constrained`). `canonical_v3.look_ahead_ready_fraction`
states in its own words that "each activity must carry its own identity and constraint status,
so the counts are derived from an inventory rather than asserted as two numbers". A look-ahead
document PRINTS that inventory -- one row per planned activity -- so the table is asked for as a
table on the `milestones_json` / `modifications_json` precedent, and this reader maps its
printed headings onto the fields the canonical function reads.

WHAT IS REFUSED, AND EACH REFUSAL IS THE POINT

  * A STATUS IS PASSED THROUGH UPPERCASED, NEVER GUESSED. The canonical function reads exactly
    OPEN or CLEARED and refuses the whole window on anything else. A row printing "pending" or
    a blank states no constraint status, and none is manufactured for it -- the module's own
    guard then says so in its abstention sentence.
  * A ROW WITH NO ACTIVITY IDENTITY IS PASSED THROUGH EMPTY, NOT DROPPED. Dropping it would
    silently shrink the window the readiness fraction is measured over; the canonical function
    refuses an identityless row with its reason, which is the honest outcome.
  * NO CATEGORY IS INVENTED FOR AN OPEN CONSTRAINT. Where the row does not say what kind of
    constraint it carries, the key is absent and the module refuses the inventory as
    unreliable, in its own words.
"""
from __future__ import annotations

import re
from typing import Any

_HEADINGS: dict[str, tuple[str, ...]] = {
    "activity_id": (
        "activity id", "activity no", "activity number", "activity code", "activity ref",
        "task id", "task no", "id", "no", "ref", "activity",
    ),
    "description": (
        "activity description", "description", "activity name", "task", "task description",
        "work description", "scope",
    ),
    "constraint_status": (
        "constraint status", "constraint", "constraints", "constraint state",
        "constraint open or cleared", "readiness", "status of constraint",
    ),
    "constraint_category": (
        "constraint category", "constraint type", "constraint kind", "category of constraint",
        "type of constraint",
    ),
}


def _norm(heading: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(heading).lower()).split())


def _pick(row: dict, field: str) -> Any:
    normalised = {_norm(k): v for k, v in row.items()}
    for candidate in _HEADINGS[field]:
        if candidate in normalised:
            return normalised[candidate]
    for candidate in _HEADINGS[field]:
        for norm_heading, value in normalised.items():
            if norm_heading.startswith(candidate + " ") or norm_heading.endswith(" " + candidate):
                return value
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    out = " ".join(str(value).split()).strip()
    return out or None


def read_lookahead_activities(raw: Any) -> list[dict]:
    """
    The activity rows a look-ahead document printed, mapped onto the canonical field names.

    One dict per printed row, in the table's own order. Every value is the row's own cell
    passed through: the status is uppercased (the document's "Open" IS the status OPEN; case is
    orthography, not content) and nothing else is transformed, defaulted or dropped. A row that
    is not a dict at all is skipped as transport noise; every dict row is passed through so the
    canonical function's own guards can refuse it with their reasons.
    """
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        entry: dict = {}
        aid = _text(_pick(row, "activity_id"))
        if aid is not None:
            entry["activity_id"] = aid
        status = _text(_pick(row, "constraint_status"))
        if status is not None:
            entry["constraint_status"] = status.upper()
        category = _text(_pick(row, "constraint_category"))
        if category is not None:
            entry["constraint_category"] = category
        description = _text(_pick(row, "description"))
        if description is not None:
            entry["description"] = description
        if entry:
            out.append(entry)
    return out


__all__ = ["read_lookahead_activities"]
