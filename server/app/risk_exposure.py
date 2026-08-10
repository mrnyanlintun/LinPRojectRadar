"""
The register's cost exposure, in the shape a forecasting module would read, and nothing more.

WHAT THIS IS FOR. Part 2 of the task that created it says the three cost-forecasting modules
should read the register or abstain, and that where the register supplies what a module needs,
the input should be SERVED. This builds that input. It is attached to the signal inputs the
analytical layer receives, beside `milestoneHistory`, which is the precedent for serving a
shaped, non-scalar input to modules that want it.

NO MODULE CONSUMES IT TODAY, AND THAT IS REPORTED RATHER THAN QUIETLY TRUE. Every one of the
three modules would need its own arithmetic changed to use this, and changing a module's
arithmetic was explicitly out of scope. See `REPORT_2026-08-10_risk-register-and-notices.md` for
what each would need. The input is served so that the data is already in place when that change
is authorised, and so that the claim "the register cannot reach these modules" is false rather
than permanent.

WHAT IT DELIBERATELY DOES NOT DO. It computes no percentile, no distribution, no sigma and no
forecast. `expected_value` is the sum of probability times cost impact over the rows that carry
both numbers, which is arithmetic the register itself implies and not a model of anything. There
is no variance here, because a variance needs a distributional assumption about each risk that
the register does not state, and inventing one is the defect this whole change exists to end.

A ROW SCORED ONLY IN BANDS CONTRIBUTES NOTHING AND IS NAMED. `refused` lists every risk that was
left out and why, by key, so a reader can see that an exposure of two risks out of forty is an
exposure of two risks out of forty.
"""

from __future__ import annotations

from typing import Any


def register_exposure(risks: list[dict] | None) -> dict[str, Any]:
    """
    The exposure the register supports, or an empty one that says why it is empty.

    `risks` is `risk_register.read_risk_table`'s shape, or the equivalent read back from the
    `project_risks` store.

    Returns:
      risk_count     rows considered (open rows only; a closed risk is not a live exposure)
      usable_count   rows carrying BOTH a numeric probability and a numeric cost impact
      expected_value sum of probability times cost impact over the usable rows, or None when
                     there are none. NEVER a partial sum presented as a total.
      contributors   the usable rows, by key, with the two numbers each contributed
      refused        the rows left out, by key, with the reason
    """
    rows = [r for r in (risks or []) if isinstance(r, dict)]
    # A closed risk is not a live exposure. It stays in the store and it is not summed.
    live = [r for r in rows if r.get("is_open") is not False]

    contributors: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []
    for r in live:
        key = str(r.get("risk_key") or "")
        probability = r.get("probability")
        cost = r.get("cost_impact")
        if isinstance(probability, (int, float)) and isinstance(cost, (int, float)):
            contributors.append({"risk_key": key, "probability": float(probability),
                                 "cost_impact": float(cost),
                                 "expected_value": float(probability) * float(cost)})
            continue
        if probability is None and r.get("probability_band"):
            reason = (f"probability is stated as the band {r['probability_band']!r}, which is "
                      f"not a number this platform will turn into one")
        elif probability is None:
            reason = "no probability this platform could read"
        else:
            reason = "no cost impact this platform could read"
        refused.append({"risk_key": key, "reason": reason})

    total = sum(c["expected_value"] for c in contributors) if contributors else None
    return {
        "risk_count": len(live),
        "usable_count": len(contributors),
        "expected_value": total,
        "contributors": contributors,
        "refused": refused,
    }


__all__ = ["register_exposure"]
