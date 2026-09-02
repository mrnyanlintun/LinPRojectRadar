"""
RUN 107. THE OWNER'S EIGHT LADDERS, THE WORST-OF RULE, AND THE HARD OVERRIDES.

WHY THIS FILE EXISTS RATHER THAN EIGHT COPIES OF THE SAME ARITHMETIC. The owner's Run 107 order
states one aggregation rule for every module in it -- "the most adverse component posture --
never average a band" -- and one place where hard overrides are applied -- "after component
banding". Eight separate implementations of one rule are eight places for it to drift, and the
drift would be invisible: a module that averaged two components would still return a colour.

WHAT THIS FILE DOES NOT DO. It holds NO threshold. Every boundary is passed in by the module
that owns it, from the owner's order, at the call site, in the module's own file where a reader
looking at the measure can see the number beside the measure. This file decides only:

  - which side of a boundary is inclusive, once, so a module cannot get it wrong quietly;
  - which of two bands is the more adverse;
  - that a component with no denominator is ABSENT rather than Green;
  - that an override is applied AFTER the components and may only worsen, never improve.

THE ABSENT COMPONENT IS THE POINT. The order's common rule is that "a missing numerator,
denominator, baseline or schedule reference returns Not Assessed, never inferred or filled". A
component that cannot be formed carries `band=None` and a SENTENCE saying what it needed. It is
not Green, it is not counted in the worst-of, and where NO component could be formed the module
returns Not Assessed rather than a colour.
"""
from __future__ import annotations

from typing import Any, Sequence

#: Least to most adverse. The one ordering in this file; `worst` is defined on it.
BAND_ORDER: tuple[str, ...] = ("Green", "Yellow", "Amber", "Red")

_RANK = {b: i for i, b in enumerate(BAND_ORDER)}


def worst(bands: Sequence[str | None]) -> str | None:
    """The most adverse band present. `None` entries are ABSENT, not favourable, and are skipped.

    Returns None when nothing was banded at all -- which the caller must render as Not Assessed
    and never as Green.
    """
    present = [b for b in bands if b in _RANK]
    if not present:
        return None
    return max(present, key=lambda b: _RANK[b])


def at_least_as_adverse_as(band: str | None, floor: str) -> str:
    """An override that may only WORSEN a band, never improve it. The order applies hard
    overrides AFTER component banding, and an override that could improve a reading would let a
    Red component be cancelled by a condition the owner named as a reason for concern."""
    if band is None:
        return floor
    return band if _RANK[band] >= _RANK[floor] else floor


def descending(value: float, green_at_or_above: float, yellow_at_or_above: float,
               amber_at_or_above: float) -> str:
    """A ladder whose direction of favourability is UPWARD -- more is better -- with every
    boundary INCLUSIVE ON ITS LOWER SIDE. Green >= g; Yellow >= y and < g; Amber >= a and < y;
    Red < a. This is the shape of the owner's SPI(t) and CPI ladders."""
    if value >= green_at_or_above:
        return "Green"
    if value >= yellow_at_or_above:
        return "Yellow"
    if value >= amber_at_or_above:
        return "Amber"
    return "Red"


def ascending(value: float, green_at_or_below: float, yellow_at_or_below: float,
              amber_at_or_below: float) -> str:
    """A ladder whose direction of favourability is DOWNWARD -- less is better -- with every
    boundary INCLUSIVE ON ITS UPPER SIDE. Green <= g; Yellow > g and <= y; Amber > y and <= a;
    Red > a. This is the shape of the owner's budget-execution, spread and consumption ladders.

    THE LADDER IS ONE-SIDED BY CONSTRUCTION and that is not an accident of the arithmetic: a
    value far BELOW the Green boundary is Green. Where the owner has ruled that under-execution
    is not adverse -- A1.9 -- this is the ladder that says so."""
    if value <= green_at_or_below:
        return "Green"
    if value <= yellow_at_or_below:
        return "Yellow"
    if value <= amber_at_or_below:
        return "Amber"
    return "Red"


def component(name: str, *, value: Any = None, band: str | None = None,
              boundary: str = "", absent_reason: str | None = None) -> dict[str, Any]:
    """One component of a worst-of reading, recorded whether or not it could be formed.

    The order requires each component's VALUE and BAND on every reading. A component that could
    not be formed records what it needed instead, in words, so the reading says which arms were
    evaluated and which were not."""
    return {"component": name, "value": value, "band": band, "boundary": boundary,
            "assessed": band is not None,
            "not_assessed_reason": absent_reason if band is None else None}


def aggregate(components: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """The worst-of over the components that were formed, with the rule recorded beside it.

    `posture` is None when no component was formed. The caller returns Not Assessed on that and
    must not substitute a colour."""
    bands = [c.get("band") for c in components]
    posture = worst(bands)
    assessed = [c for c in components if c.get("band")]
    absent = [c for c in components if not c.get("band")]
    return {
        "band_components": list(components),
        "band_components_assessed": [c["component"] for c in assessed],
        "band_components_not_assessed": [c["component"] for c in absent],
        "band_posture_before_override": posture,
        "band_aggregation_rule": "worst-of",
        "band_aggregation_words": (
            "the most adverse component posture governs. Component bands are NEVER averaged: a "
            "favourable component does not offset an adverse one, and a component that could "
            "not be formed is ABSENT from the aggregation rather than counted as favourable."),
    }
