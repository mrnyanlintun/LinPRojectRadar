"""
RUN 33. THE HISTORICAL RESOLUTION MECHANISM FOR THE SUPERSEDED v20 PORTFOLIO IMPLEMENTATION.

WHY THIS EXISTS, and it is the Run-30/31/32 precedent applied unchanged. Run 33 supersedes
`portfolio.compute_portfolio` and does NOT delete it, because Run 2's fifteen-defects work, Run
6's known-answer tables, Run 13's module evidence, Run 14's anomaly-detector comparison, Run 15's
isolation-forest validation, Run 17's method audit and Run 20's cycle-12 re-audit are ALL
EVIDENCE ABOUT THAT FUNCTION. Deleting it would delete the subject of those findings and make the
scientific record unreconstructable.

The legacy function stays exactly where it was, in `app/simulation/portfolio.py`. What changed is
that production's single call site -- `documents.run_and_store` -- now routes Group D through
`portfolio_health.compute_portfolio_health_snapshot` and the canonical v8 layer.

HOW A HISTORICAL TEST USES THIS. It asks for the LEGACY entry point here and executes it
directly, which is what it was always really asserting about, and it must ALSO call
`assert_not_reachable`, because a historical test that only proved the old behaviour would go
green again if a later run reconnected the proxy -- and a test that can be satisfied by live
code is not a historical record.

THE ENTRY POINT IS READ LIVE, NOT COPIED, so a legacy implementation that is edited or removed
changes what these tests execute rather than silently diverging from a transcribed copy.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Any, Callable

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from app.simulation import portfolio as _legacy                      # noqa: E402
from app.simulation import portfolio_health as _current              # noqa: E402

#: The five Portfolio Health identities, read from the legacy module's own map rather than typed
#: out, so this file cannot drift from what was actually superseded.
PORTFOLIO_IDS: tuple[str, ...] = tuple(sorted(_legacy.PORTFOLIO_VALIDATED))


def legacy_compute_portfolio() -> Callable:
    """
    The SUPERSEDED v20 implementation, for historical assertions only.

    A test calling this is asserting what the instrument USED to do. It is not a statement about
    current production and must never be read as one.
    """
    fn = getattr(_legacy, "compute_portfolio", None)
    if not callable(fn):
        raise KeyError(
            "the v20 portfolio implementation is no longer preserved; the Run-2/6/13/14/15/17/20 "
            "findings about it cannot be reconstructed and must not be silently skipped")
    return fn


def run_legacy(portfolio: list[dict], current_id: Any, history: list[dict] | None,
               period_cutoff: Any) -> dict[str, Any]:
    """Execute the superseded implementation directly, bypassing production on purpose."""
    return legacy_compute_portfolio()(portfolio, current_id, history, period_cutoff)


def assert_not_reachable(check: Callable[..., None]) -> None:
    """
    THE OTHER HALF OF EVERY HISTORICAL PORTFOLIO ASSERTION. Proves current production cannot
    reach the v20 implementation, from production's own live source rather than from a list.
    """
    _current.assert_not_reachable(check)
