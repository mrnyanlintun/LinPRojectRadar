"""
RUN 32. THE HISTORICAL RESOLUTION MECHANISM FOR THE SUPERSEDED CATEGORY-10 IMPLEMENTATIONS.

WHY THIS EXISTS, and it is the Run-30 and Run-31 precedent applied unchanged. Run 32 supersedes
seven Category-10 implementations and does NOT delete them, because Run 19's Category-10 audit,
Run 14's disabled-method functional suite and Run 20's truthful-label work are EVIDENCE ABOUT
THOSE IMPLEMENTATIONS. Deleting the code would delete the findings' subject and make the
scientific record unreconstructable.

The legacy functions stay exactly where they were -- `models_gov.py` and `models_decision.py` --
and their extension maps are still built and still updated into `VALIDATED`. What changed is that
`models.py` overwrites every B4.x key with the canonical route LAST, so nothing in production
resolves to them.

HOW A HISTORICAL TEST USES THIS. It asks for the LEGACY runner by module id and executes it
directly, which is what it was always really asserting about. It must ALSO call
`assert_not_reachable`, because a historical test that only proved the old behaviour would go
green again if a later run accidentally reconnected the proxy -- and a test that can be satisfied
by live code is not a historical record.

THE MAPS ARE READ LIVE, NOT COPIED, so a legacy implementation that is edited or removed changes
what these tests execute rather than silently diverging from a transcribed copy.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Any, Callable

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from app.simulation.models_cat10 import CAT10_CANONICAL          # noqa: E402
from app.simulation.models_decision import DECISION_EXTENSIONS   # noqa: E402
from app.simulation.models_gov import GOV_BATCH_A, GOV_BATCH_B   # noqa: E402

#: The seven Run-32 identities, derived from the canonical route table rather than typed out, so
#: this module cannot drift from what production actually repointed.
CAT10_IDS: tuple[str, ...] = tuple(sorted(CAT10_CANONICAL))


def _legacy_maps() -> dict[str, tuple[str, Callable]]:
    """Every legacy Category-10 runner, read live from the modules that still export them."""
    merged: dict[str, tuple[str, Callable]] = {}
    for m in (GOV_BATCH_A, GOV_BATCH_B, DECISION_EXTENSIONS):
        for k, v in m.items():
            if k in CAT10_CANONICAL:
                merged[k] = v
    return merged


LEGACY_CAT10: dict[str, tuple[str, Callable]] = _legacy_maps()


class NoHistoricalImplementation(KeyError):
    """Asked for a legacy runner this repository no longer preserves."""


def legacy_runner(module_id: str) -> Callable:
    """
    The SUPERSEDED implementation of one Category-10 module, for historical assertions only.

    A test calling this is asserting what the instrument USED to do. It is not a statement about
    current production and must never be read as one.
    """
    if module_id not in LEGACY_CAT10:
        raise NoHistoricalImplementation(
            f"{module_id} has no preserved legacy implementation; a historical assertion about "
            f"it cannot be reconstructed and must not be silently skipped")
    return LEGACY_CAT10[module_id][1]


def run_legacy(module_id: str, si: dict, rand: Callable[[], float] | None = None,
               period_cutoff: Any = None) -> dict[str, Any]:
    """Execute the superseded implementation directly, bypassing the registry on purpose."""
    return legacy_runner(module_id)(si, rand or (lambda: 0.5), period_cutoff)


def assert_not_reachable(check: Callable[..., None]) -> None:
    """
    THE OTHER HALF OF EVERY HISTORICAL TEST. Prove current production does not resolve to the
    legacy implementation for ANY of the seven identities.

    Derived from the shipped dispatch table rather than from a list: `VALIDATED` is what the
    dispatcher actually consults, so this compares the function object production would call
    against the legacy function object, for every id, mechanically.

    THE BOUNDARY WRAPPER IS UNWRAPPED BEFORE COMPARING. Every Category-10 entry is wrapped by the
    qualification boundary, and `functools.wraps` copies `__name__` and `__module__` onto the
    wrapper -- so comparing names would compare the wrong thing and pass for the wrong reason.
    The identity comparison follows `__wrapped__` to the runner that actually executes.
    """
    from app.simulation.models import VALIDATED

    def inner(fn: Callable) -> Callable:
        return getattr(fn, "__wrapped__", fn)

    reachable = []
    for mid in CAT10_IDS:
        live = VALIDATED.get(mid)
        legacy = LEGACY_CAT10.get(mid)
        if live and legacy and inner(live[1]) is legacy[1]:
            reachable.append(mid)
    check(not reachable,
          "current production resolves NO Category-10 identity to its superseded implementation, "
          "so this historical assertion describes the past and cannot be satisfied by live code",
          str(reachable))
    canonical = [mid for mid in CAT10_IDS
                 if VALIDATED.get(mid) and inner(VALIDATED[mid][1]) is CAT10_CANONICAL[mid][1]]
    check(len(canonical) == len(CAT10_IDS),
          f"and all {len(CAT10_IDS)} resolve to the canonical v7 route instead",
          f"{len(canonical)}/{len(CAT10_IDS)}")
