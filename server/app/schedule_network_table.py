"""
RUN 103. THE FLATTENED SCHEDULE EXPORT, READ FROM THE DOCUMENT THAT PRINTS IT.

WHAT THIS CLOSES. A2.1 PERT Network Criticality has abstained since Run 28 on "the project's
activity network: the activities, the logic between them, and a duration for each", because
NOTHING ASKED A DOCUMENT FOR ONE. Run 102 measured that `scheduleNetwork` had no supply path at
all. A schedule update PRINTS the export -- one row per activity, with its id, its duration, its
predecessor logic with relation type and lag, its calendar, and its baseline finish -- so
`schedule_network_json` asks for it as a table on the `lookahead_activities_json` precedent, and
this reader maps its printed headings onto the fields the canonical functions read.

NOTHING IS REPAIRED HERE AND NOTHING IS DROPPED. That is the whole discipline of the owner's
section 2.1: the platform names which rows made the export unreadable and the SCHEDULER corrects
the source. So:

  * A ROW WITH NO ACTIVITY IDENTITY IS PASSED THROUGH EMPTY, NOT DROPPED, so the diagnostics
    count it and name its row number.
  * A DURATION THAT IS NOT A NUMBER IS PASSED THROUGH AS IT WAS PRINTED, so the diagnostics
    report a missing duration on that row rather than a zero nobody wrote.
  * A RELATION TYPE THAT IS NOT ONE OF THE FOUR IS PASSED THROUGH AS IT WAS PRINTED. It is never
    coerced to Finish-to-Start. FS is used only where the row states NO type at all, which is
    what a bare predecessor list without a type column means.
  * A LAG THAT IS NOT READABLE AS A NUMBER IS PASSED THROUGH AS IT WAS PRINTED, so the
    diagnostics report an unreadable lag rather than treating it as zero.
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
    "current_duration": (
        "remaining duration", "current duration", "duration", "duration days",
        "original duration", "planned duration", "od", "rd",
    ),
    "baseline_duration": ("baseline duration", "bl duration", "baseline dur"),
    "predecessors": (
        "predecessors", "predecessor", "preds", "predecessor activities", "logic",
        "predecessor id", "driving predecessors",
    ),
    "successors": ("successors", "successor", "succs", "successor activities"),
    "calendar": ("calendar", "activity calendar", "calendar id", "calendar name"),
    "baseline_finish_day": (
        "baseline finish day", "baseline finish", "bl finish", "baseline finish working day",
        "approved baseline finish",
    ),
    "milestone_class": (
        "milestone class", "milestone type", "commitment class", "milestone category",
    ),
    "optimistic_duration": ("optimistic duration", "optimistic", "best case duration", "o"),
    "most_likely_duration": ("most likely duration", "most likely", "ml"),
    "pessimistic_duration": ("pessimistic duration", "pessimistic", "worst case duration", "p"),
}

#: The four relation types a logic tie may state. A "FS+3" style cell states both the type and
#: the lag in one string; both halves are read, and anything else is passed through as printed.
_REL_RE = re.compile(r"^\s*([A-Za-z]{2})?\s*([+-]?\d+(?:\.\d+)?)?\s*[dD]?\s*$")


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


def _read_link(raw: Any) -> dict[str, Any]:
    """
    One predecessor tie, as the export printed it.

    Accepts a bare id ("A100"), an id with the relation and lag in one cell ("A100 FS+3",
    "A100-SS-2"), or a mapping already carrying the three fields. Whatever cannot be read as a
    relation type or a lag is PASSED THROUGH AS PRINTED so the diagnostics can name it.
    """
    if isinstance(raw, dict):
        out: dict[str, Any] = {}
        pid = _text(raw.get("activity_id") or raw.get("predecessor_id") or raw.get("id"))
        if pid is not None:
            out["activity_id"] = pid
        rel = _text(raw.get("relation_type") or raw.get("type") or raw.get("relationship"))
        if rel is not None:
            out["relation_type"] = rel
        if raw.get("lag") is not None:
            out["lag"] = raw.get("lag")
        return out
    text = _text(raw)
    if text is None:
        return {}
    # Split off a trailing relation/lag token, e.g. "A100 FS+3" or "A100-SS-2".
    parts = re.split(r"[\s,;]+|(?<=\w)-(?=[A-Za-z]{2}\b)", text)
    parts = [p for p in parts if p]
    if len(parts) >= 2:
        m = _REL_RE.match(parts[-1])
        if m and (m.group(1) or m.group(2)):
            out = {"activity_id": " ".join(parts[:-1])}
            if m.group(1):
                out["relation_type"] = m.group(1)
            if m.group(2) is not None:
                out["lag"] = float(m.group(2))
            return out
    return {"activity_id": text}


def _read_links(raw: Any) -> list[dict] | Any:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [_read_link(x) for x in raw]
    if isinstance(raw, str):
        return [_read_link(x) for x in re.split(r"[,;]", raw) if x.strip()]
    return raw


def read_schedule_network(raw: Any) -> list[dict]:
    """One dict per printed activity row, in the export's own order. Nothing is dropped."""
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        entry: dict = {}
        for field in ("activity_id", "description", "calendar", "milestone_class"):
            value = _text(_pick(row, field))
            if value is not None:
                entry[field] = value
        for field in ("current_duration", "baseline_duration", "baseline_finish_day",
                      "optimistic_duration", "most_likely_duration", "pessimistic_duration"):
            value = _pick(row, field)
            if value is not None and value != "":
                # PASSED THROUGH AS PRINTED where it is not a number. The diagnostics report a
                # missing duration on that row; nothing is defaulted to zero here.
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    entry[field] = float(value)
                else:
                    try:
                        entry[field] = float(str(value).strip())
                    except ValueError:
                        entry[field] = value
        preds = _read_links(_pick(row, "predecessors"))
        if preds != []:
            entry["predecessors"] = preds
        succs = _pick(row, "successors")
        if succs is not None and succs != "":
            entry["successors"] = ([_text(s) for s in succs] if isinstance(succs, list)
                                   else [s.strip() for s in re.split(r"[,;]", str(succs))
                                         if s.strip()])
        if entry:
            out.append(entry)
    return out
