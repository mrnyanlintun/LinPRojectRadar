"""
RUN 68. THE TIME-PHASED BASELINE TABLE, READ FROM THE DOCUMENT THAT PRINTS IT.

WHAT THIS CLOSES. Three modules are defined on a CURVE and every one of them abstained, each
printing the curve's name in the document's own words:

  A1.6 Earned Schedule      "a time phased baseline: the cumulative value of work planned to be
                             complete at the end of each period"
  A2.6 S-Curve Deviation     the same structure, plus the matching actual series
  A1.9 Budget Execution Rate "an approved time phased expenditure baseline: the amount planned
                             to be spent by the end of each period"

The gap was never that the fact is unavailable. A time-phased baseline document IS this table --
that is the entire document -- and until this run the only thing asked of it was the single
cumulative figure standing at its data date (`planned_value_to_date`). One point is not a curve.
`earned_schedule` says so in its own guard ("does not carry a cumulative planned value for at
least two periods"), and `canonical_v3` refuses to interpolate past the end of the curve because
"interpolating beyond the curve would invent planned value that the baseline does not contain".

SO THIS READER TAKES THE ROWS AND NOTHING ELSE. It is `schedule_activities.read_activity_table`
applied to a second table: the model returns `baseline_curve_json` as one object per printed row
keyed by the table's own headings, and this maps those headings onto the two quantities the
canonical structures are defined on. Every rule below exists to stop a figure being manufactured.

WHAT IS REFUSED, AND WHY EACH REFUSAL IS THE POINT

  * A PERIODIC COLUMN IS NEVER READ AS A CUMULATIVE ONE. A baseline commonly prints both -- the
    value planned IN each period and the value planned complete BY the end of it -- and they are
    different quantities that differ by a running sum. Summing the periodic column here would
    produce a curve the document does not print, so any heading marked periodic, incremental,
    monthly, "this period" or "in period" is rejected outright rather than converted. Where the
    document prints only the periodic column, no curve is assembled and the three modules go on
    abstaining, which is correct.

  * A FALLING CURVE IS NOT REPAIRED. `earned_schedule` refuses a baseline that decreases, on the
    ground that a cumulative planned value cannot. This reader does not sort the figures into
    order to satisfy that guard: it passes the rows as printed and lets the canonical module
    refuse them, because a curve that falls means the column was misread and the honest response
    is the abstention, not a curve reordered until it passes.

  * A ROW WITH NO FIGURE IS DROPPED, NOT INTERPOLATED. A baseline with a blank period is a
    baseline with a blank period. Filling it from its neighbours is the invented value that is
    forbidden, and the shortened curve the caller receives is a true account of what was printed.

  * NO PERIOD INDEX IS INVENTED. Where the table prints an index or a period column it is used.
    Where it does not, the ROWS' OWN PRINTED ORDER is used, and the assembled structure SAYS SO
    (`period_index_basis`), because reading the order a table is printed in is reading the
    document, while assigning periods to unordered rows would not be.
"""
from __future__ import annotations

import re
from typing import Any

#: Column headings, normalised, that carry each quantity. Order is preference order.
_HEADINGS: dict[str, tuple[str, ...]] = {
    "period_index": (
        "period index", "period number", "period no", "period", "month number", "month no",
        "month", "time period", "reporting period", "index", "no", "seq",
    ),
    # CUMULATIVE PLANNED VALUE. "to date" and "cumulative" are the two ways a baseline prints
    # that a figure is a running total; BCWS is the earned-value name for the same quantity.
    "cumulative_pv": (
        "cumulative planned value", "cumulative pv", "planned value cumulative",
        "planned value to date", "cumulative bcws", "bcws cumulative",
        "cumulative budgeted cost of work scheduled", "cumulative earned value baseline",
        "cumulative baseline value", "planned value", "bcws",
    ),
    # CUMULATIVE PLANNED SPEND. The expenditure baseline is a different curve from the value
    # baseline -- money planned to LEAVE against value planned to be EARNED -- and A1.9 is
    # defined on the first. They are matched separately and never substituted for one another.
    "expected_spend": (
        "cumulative planned spend", "cumulative planned cost", "cumulative expenditure",
        "cumulative planned expenditure", "planned spend to date", "planned cost to date",
        "cumulative spend", "cumulative cost", "planned expenditure", "planned spend",
        "planned cost", "budgeted spend",
    ),
    "period_label": ("period label", "period name", "label", "period ending", "date", "ending"),
}

#: A heading carrying any of these describes what happens WITHIN a period, not by the end of it.
#: Such a column is refused for both cumulative quantities. See the module docstring.
_PERIODIC_MARKERS = (
    "periodic", "incremental", "increment", "this period", "in period", "per period",
    "monthly", "in month", "this month", "current period", "non cumulative",
    "period value", "period spend", "period cost",
)


def _norm(heading: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(heading).lower()).split())


def _is_periodic(heading_norm: str) -> bool:
    return any(m in heading_norm for m in _PERIODIC_MARKERS)


def _number(value: Any) -> float | None:
    """A finite number from a printed cell, or None. Never a default and never a zero-fill."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value == value and abs(value) != float("inf") else None
    text = str(value).strip()
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    cleaned = re.sub(r"[^0-9.\-]", "", text)
    if cleaned in ("", "-", ".", "-."):
        return None
    try:
        out = float(cleaned)
    except ValueError:
        return None
    if out != out or abs(out) == float("inf"):
        return None
    return -out if (negative and out > 0) else out


def _pick(row: dict, field: str) -> tuple[str, Any] | None:
    """The first heading in preference order this row actually carries. Cumulative fields skip
    any column whose heading marks it periodic -- see the module docstring."""
    cumulative = field in ("cumulative_pv", "expected_spend")
    normalised = {_norm(k): (k, v) for k, v in row.items()}
    for candidate in _HEADINGS[field]:
        hit = normalised.get(candidate)
        if hit is not None:
            if cumulative and _is_periodic(candidate):
                continue
            return hit
    # A heading the table spells slightly differently ("Cumulative Planned Value (USD)") still
    # names the quantity, so a containment pass follows the exact pass -- never before it, so an
    # exact match can never lose to a longer heading that merely contains a shorter name.
    for candidate in _HEADINGS[field]:
        for norm_heading, hit in normalised.items():
            if candidate in norm_heading:
                if cumulative and _is_periodic(norm_heading):
                    continue
                return hit
    return None


def read_baseline_curve(curve: Any) -> list[dict]:
    """
    `baseline_curve_json` (a list of row objects keyed by the table's own headings) -> rows.

    Each returned row is a dict with a stable schema:

      period_index      the period this row states, as a number
      period            the row's printed period label, where the table carries one, else None
      cumulative_pv     the cumulative planned value the row prints, or None
      expected_spend    the cumulative planned spend the row prints, or None
      index_basis       "stated" when the table printed a period index, "printed order" when the
                        rows' own order supplied it

    A row carrying NEITHER cumulative figure states nothing this reader is for and is dropped.
    Rows are returned in the order the document printed them; nothing is sorted, summed,
    interpolated or filled.
    """
    if not isinstance(curve, list):
        return []
    out: list[dict] = []
    position = 0
    for raw_row in curve:
        if not isinstance(raw_row, dict):
            continue
        position += 1
        pv_hit = _pick(raw_row, "cumulative_pv")
        spend_hit = _pick(raw_row, "expected_spend")
        pv = _number(pv_hit[1]) if pv_hit else None
        spend = _number(spend_hit[1]) if spend_hit else None
        if pv is None and spend is None:
            # A TOTALS ROW, A BLANK ROW OR A HEADING REPEATED MID-TABLE. It states no figure on
            # either curve, so there is nothing to place on one and nothing is placed.
            continue
        index_hit = _pick(raw_row, "period_index")
        stated_index = _number(index_hit[1]) if index_hit else None
        label_hit = _pick(raw_row, "period_label")
        row = {
            "period_index": stated_index if stated_index is not None else float(position),
            "index_basis": "stated" if stated_index is not None else "printed order",
            "period": (str(label_hit[1]).strip() if label_hit and label_hit[1] is not None
                       else (str(index_hit[1]).strip() if index_hit and index_hit[1] is not None
                             else None)),
        }
        if pv is not None:
            row["cumulative_pv"] = pv
        if spend is not None:
            row["expected_spend"] = spend
        out.append(row)
    return out
