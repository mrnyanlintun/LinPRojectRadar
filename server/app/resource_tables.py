"""
RUN 69. THE RESOURCE HISTOGRAM AND THE PRODUCTION RECORD, READ FROM THE DOCUMENTS THAT PRINT THEM.

WHAT THIS CLOSES, and it is Run 68's finding applied to a second and third table.

  A2.9 Resource Loading Index abstained on "a time phased resource profile: for each period and
  each kind of resource, the amount of work demanded and the amount available". The platform
  asked the resource report for FOUR SCALARS -- planned and actual labour hours, planned and
  actual equipment days -- and `canonical_v3.resource_loading` states in its own words that "a
  project-total planned-versus-actual labour ratio is not this index and is not computed here:
  the structure must be time-phased and must state the capacity, not only the demand."

  A resource report IS that histogram. The table a resource-loaded schedule prints has one row
  per period per trade, the hours demanded in it, and the hours available. So the table is asked
  for as a table, on exactly the precedent `baseline_curve_json` set, and this reader maps its
  printed headings onto demand and capacity.

WHAT IS REFUSED, AND EACH REFUSAL IS THE POINT

  * DEMAND IS NEVER READ AS CAPACITY. They are different quantities -- work asked for against
    work available -- and a row printing only one of them is dropped rather than completed. The
    heading tables below are disjoint and no heading appears in both.
  * A ROW THAT DOES NOT SAY WHICH PERIOD OR WHICH TRADE IT DESCRIBES IS DROPPED. `resource_loading`
    refuses such a row itself; dropping it here means the profile the module receives is the set
    of rows that actually stated both, and never a row with a manufactured label.
  * NOTHING IS SUMMED, SORTED OR INTERPOLATED. The rows are passed in the order the document
    printed them.

A3.3 Labor Productivity is NOT a table. `canonical_v3.labor_productivity` is defined on four
scalars and a unit -- the quantity installed, the quantity planned, the hours each took, and the
unit both quantities are counted in -- and a production report states each of those on its face
under its own label. So they are asked for as scalars, and `production_output_record` below only
assembles what the document stated. Two of the four hours figures the platform ALREADY extracts
(`planned_labor_hours`, `actual_labor_hours`); what was missing was the output basis, which is
precisely why the module refused: hours over hours is not productivity.
"""
from __future__ import annotations

import re
from typing import Any

#: Column headings, normalised, that carry each quantity of the resource histogram. Preference
#: order. DEMAND AND CAPACITY SHARE NO HEADING -- see the module docstring.
_HEADINGS: dict[str, tuple[str, ...]] = {
    "time_bucket": (
        "period", "period ending", "period label", "month", "week", "time bucket", "bucket",
        "period number", "period no", "time period", "date",
    ),
    "resource_type": (
        "resource type", "resource", "trade", "craft", "discipline", "labour type",
        "labor type", "resource category", "crew",
    ),
    # WORK ASKED FOR IN THE PERIOD.
    "demand": (
        "demand", "demand hours", "required hours", "hours required", "resource demand",
        "planned hours", "demanded hours", "workload", "required", "loaded hours",
        "hours demanded",
    ),
    # WORK THE PROJECT CAN ACTUALLY SUPPLY IN THE PERIOD.
    "available_capacity": (
        "available capacity", "capacity", "available hours", "hours available",
        "capacity hours", "resource availability", "availability", "available",
        "supply", "capacity available",
    ),
    "deployed": ("deployed", "deployed hours", "actual hours", "hours deployed", "actual"),
}


def _norm(heading: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(heading).lower()).split())


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


def _pick(row: dict, field: str) -> Any:
    """The first heading in preference order this row carries; exact match before containment,
    so an exact heading can never lose to a longer one that merely contains a shorter name."""
    normalised = {_norm(k): v for k, v in row.items()}
    for candidate in _HEADINGS[field]:
        if candidate in normalised:
            return normalised[candidate]
    for candidate in _HEADINGS[field]:
        for norm_heading, value in normalised.items():
            if candidate in norm_heading:
                return value
    return None


def read_resource_profile(profile: Any) -> list[dict]:
    """
    `resource_profile_json` (a list of row objects keyed by the table's own headings) -> buckets.

    Each returned bucket is `{time_bucket, resource_type, demand, available_capacity}` and
    optionally `deployed`, which is what `canonical_v3.resource_loading` reads. A row that does
    not state ALL FOUR of those is dropped: the module refuses such a row itself, and dropping it
    here is the difference between a shorter true profile and a completed false one.
    """
    if not isinstance(profile, list):
        return []
    out: list[dict] = []
    for raw_row in profile:
        if not isinstance(raw_row, dict):
            continue
        bucket = _pick(raw_row, "time_bucket")
        resource = _pick(raw_row, "resource_type")
        demand = _number(_pick(raw_row, "demand"))
        capacity = _number(_pick(raw_row, "available_capacity"))
        bucket = str(bucket).strip() if bucket is not None else ""
        resource = str(resource).strip() if resource is not None else ""
        if not bucket or not resource or demand is None or capacity is None:
            # A TOTALS ROW, A BLANK ROW, OR A TABLE THAT PRINTS DEMAND WITHOUT CAPACITY. It does
            # not state a load, so no load is formed from it and none is invented for it.
            continue
        row = {"time_bucket": bucket, "resource_type": resource,
               "demand": demand, "available_capacity": capacity}
        deployed = _number(_pick(raw_row, "deployed"))
        if deployed is not None:
            row["deployed"] = deployed
        out.append(row)
    return out


def production_output_record(extraction: dict, *, planned_hours: Any, actual_hours: Any) -> dict | None:
    """
    A3.3's `productionOutputRecord` from the figures a production report states on its face, or
    None where it states less than the whole of it.

    `canonical_v3.labor_productivity` requires the unit, the two quantities, the two hours
    figures and a stated `quantity_source` -- `_provenance` REFUSES to default the last, on the
    ground that "a blank source silently reads as an unsourced number". Every one of those is a
    printed figure; not one is derived here. Where any is absent the record is not assembled and
    the module goes on abstaining, which is the correct outcome.
    """
    unit = str(extraction.get("quantity_unit") or "").strip()
    source = str(extraction.get("quantity_source") or "").strip()
    installed = _number(extraction.get("quantity_installed_to_date"))
    planned_qty = _number(extraction.get("quantity_planned_to_date"))
    ph = _number(planned_hours)
    ah = _number(actual_hours)
    if not unit or not source or installed is None or planned_qty is None \
            or ph is None or ah is None:
        return None
    return {
        "output_unit": unit,
        "quantity_source": source,
        # THE QUANTITY INSTALLED IS THE EARNED OUTPUT. That is what the canonical function is
        # defined on ("a comparable earned or installed quantity"), and it is the figure the
        # document prints under its own heading. No percentage is scaled into it -- that is
        # precisely the v2 form `run_labor_productivity` names as forbidden.
        "earned_output": installed,
        "planned_output": planned_qty,
        "actual_labor_hours": ah,
        "planned_labor_hours": ph,
        "assembled_by": "document extraction",
        "source_document_type": "resource_report",
    }


def overhead_allocation_base(extraction: dict) -> dict | None:
    """
    A3.5's `overheadAllocationBase` from the figures a cost report states, or None.

    `canonical_v3.overhead_absorption` states in its own words that "indirect actual over
    indirect plan with no allocation base is not overhead absorption and is computed nowhere
    here". The two indirect figures the platform already extracts are the OVERHEAD; what was
    missing is the BASE it is absorbed over, which a cost report carrying an overhead schedule
    prints beside them -- the base named, and the planned and actual amount of it.
    """
    base = str(extraction.get("overhead_allocation_base") or "").strip()
    source = str(extraction.get("overhead_driver_source") or "").strip()
    planned_oh = _number(extraction.get("indirect_cost_plan"))
    actual_oh = _number(extraction.get("indirect_cost_actual"))
    planned_driver = _number(extraction.get("planned_allocation_base_quantity"))
    actual_driver = _number(extraction.get("actual_allocation_base_quantity"))
    if not base or not source or planned_oh is None or actual_oh is None \
            or planned_driver is None or actual_driver is None:
        return None
    return {
        "allocation_base": base,
        "driver_source": source,
        "planned_overhead": planned_oh,
        "actual_overhead": actual_oh,
        "planned_driver": planned_driver,
        "actual_driver": actual_driver,
        "assembled_by": "document extraction",
        "source_document_type": "cost_report",
    }
