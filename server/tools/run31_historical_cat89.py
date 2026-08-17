"""
RUN 31. THE HISTORICAL RESOLUTION MECHANISM FOR THE SUPERSEDED CATEGORY-8/9 IMPLEMENTATIONS.

WHY THIS EXISTS, and it is the Category-7 precedent applied unchanged. Run 30 repointed twenty
Category-7 identities onto the canonical layer and did NOT delete the implementations it
superseded, because Run 19's audit, Run 27's parsimony proofs and Run 14's disabled-method suite
are EVIDENCE ABOUT THOSE IMPLEMENTATIONS. Deleting the code would delete the findings' subject
and make the scientific record unreconstructable.

Run 31 supersedes sixteen Category-8/9 implementations and does the same thing. The legacy
functions remain exactly where they were -- `models_doc.py` (A6.x), `models_gov.py` and
`models_decision.py` (B3.x), `models_dq.py` (C1.x) -- and their extension maps are still built
and still updated into `VALIDATED`. What changed is that `models.py` overwrites every A6/B3/C1
key with the canonical route LAST, so nothing in production resolves to them.

HOW A HISTORICAL TEST USES THIS. It asks for the LEGACY runner by module id and executes it
directly, which is what it was always really asserting about. It must ALSO assert that current
production does not reach that runner -- `assert_not_reachable` below -- because a historical
test that only proves the old behaviour would go green again if a later run accidentally
reconnected the proxy.

THE MAPS ARE READ LIVE, NOT COPIED. `legacy_runner` resolves out of the extension dictionaries
the modules themselves export, so a legacy implementation that is edited or removed changes what
these tests execute rather than silently diverging from a transcribed copy.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Any, Callable

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from app.simulation.models_cat89 import CAT89_CANONICAL      # noqa: E402
from app.simulation.models_decision import DECISION_EXTENSIONS  # noqa: E402
from app.simulation.models_doc import A6_EXTENSIONS          # noqa: E402
from app.simulation.models_dq import DQ_EXTENSIONS           # noqa: E402
from app.simulation.models_gov import GOV_BATCH_A, GOV_BATCH_B  # noqa: E402

#: The sixteen Run-31 identities, derived from the canonical route table rather than typed out,
#: so this module cannot drift from what production actually repointed.
CAT89_IDS: tuple[str, ...] = tuple(sorted(CAT89_CANONICAL))


def _legacy_maps() -> dict[str, tuple[str, Callable]]:
    """Every legacy Category-8/9 runner, read live from the modules that still export them."""
    merged: dict[str, tuple[str, Callable]] = {}
    for m in (A6_EXTENSIONS, GOV_BATCH_A, GOV_BATCH_B, DQ_EXTENSIONS, DECISION_EXTENSIONS):
        for k, v in m.items():
            if k in CAT89_CANONICAL:
                merged[k] = v
    return merged


LEGACY_CAT89: dict[str, tuple[str, Callable]] = _legacy_maps()


class NoHistoricalImplementation(KeyError):
    """Asked for a legacy runner this repository no longer preserves."""


def legacy_runner(module_id: str) -> Callable:
    """
    The SUPERSEDED implementation of one Category-8/9 module, for historical assertions only.

    A test calling this is asserting what the instrument USED to do. It is not a statement about
    current production and must never be read as one.
    """
    if module_id not in LEGACY_CAT89:
        raise NoHistoricalImplementation(
            f"{module_id} has no preserved legacy implementation; a historical assertion about "
            f"it cannot be reconstructed and must not be silently skipped")
    return LEGACY_CAT89[module_id][1]


def run_legacy(module_id: str, si: dict, rand: Callable[[], float] | None = None,
               period_cutoff: Any = None) -> dict[str, Any]:
    """Execute the superseded implementation directly, bypassing the registry on purpose."""
    return legacy_runner(module_id)(si, rand or (lambda: 0.5), period_cutoff)


def assert_not_reachable(check: Callable[..., None]) -> None:
    """
    THE OTHER HALF OF EVERY HISTORICAL TEST. Prove current production does not resolve to the
    legacy implementation for ANY of the sixteen identities.

    Derived from the shipped registry rather than from a list: `VALIDATED` is what the dispatcher
    actually consults, so this compares the function object production would call against the
    legacy function object, for every id, mechanically.
    """
    from app.simulation.models import VALIDATED

    reachable = []
    for mid in CAT89_IDS:
        live = VALIDATED.get(mid)
        legacy = LEGACY_CAT89.get(mid)
        if live and legacy and live[1] is legacy[1]:
            reachable.append(mid)
    check(not reachable,
          "current production resolves NO Category-8/9 identity to its superseded "
          "implementation, so this historical assertion describes the past and cannot be "
          "satisfied by live code",
          str(reachable))
    canonical = [mid for mid in CAT89_IDS
                 if VALIDATED.get(mid) and VALIDATED[mid][1] is CAT89_CANONICAL[mid][1]]
    check(len(canonical) == len(CAT89_IDS),
          f"and all {len(CAT89_IDS)} resolve to the canonical v6 route instead",
          f"{len(canonical)}/{len(CAT89_IDS)}")


# =================================================================================================
# THE THREE LINEAGE DECLARATIONS RUN 31 REMOVED, PRESERVED AS HISTORICAL RECORDS.
#
# `lineage.py` no longer declares B3.2, B3.4 or B3.5, because all three now route through
# canonical_v6 and read no cost index, no schedule index and no change-order count -- so the
# relationships those records described have stopped existing, and leaving them would assert a
# dependence into the earned-value and contract-change bodies that is false. They were REMOVED
# rather than rewritten, on the Run-30 closure's reasoning, because what a governed applicability,
# reporting or modification record rests on is whatever its assessor read and this platform does
# not know that.
#
# THE RECORDS THEMSELVES ARE STILL EVIDENCE. Run 20's cycle-8 cluster proofs and its advisory
# lineage disclosure use them to exercise the lineage machinery -- pair dependence, evidence
# resolution, shared-body detection -- and deleting them outright would delete the subject of
# those proofs. They are reproduced here verbatim as they stood, and `install_historical_lineage`
# lets a historical suite resolve them without current production being able to.
# =================================================================================================
from app.simulation.lineage import (  # noqa: E402
    CONTRACT_CHANGE_BODY, CORRELATED, COST_INDEX, EARNED_VALUE_BODY, SAME_SOURCE_TRANSFORM,
    SCHEDULE_INDEX, lineage_record,
)

HISTORICAL_LINEAGE_RUN31: dict[str, dict] = {
    "B3.2": lineage_record(
        "B3.2", source_fact_ids=(),
        derived_index_reads=(COST_INDEX,),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("the cost performance index",
                          "cost performance index = ev / ac",
                          "forecast overrun as a percentage of the budget, which is "
                          "scale-invariant in the budget",
                          "comparison against an internal review level")),
    "B3.4": lineage_record(
        "B3.4", source_fact_ids=(),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=CORRELATED,
        derivation_chain=("the cost and schedule performance indices",
                          "deviation of each index from one",
                          "comparison against an internal reporting level")),
    "B3.5": lineage_record(
        "B3.5",
        source_fact_ids=("baseline_contract_sum", "change_order_count", "revised_contract_sum"),
        lineage_group_ids=(CONTRACT_CHANGE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("change order log", "count of contract modifications",
                          "scope growth = (revised contract sum - baseline contract sum) "
                          "/ baseline contract sum")),
}


def install_historical_lineage() -> None:
    """Resolve the three removed declarations, for historical assertions only."""
    from app.simulation import lineage as _lin
    _live = _lin.lineage_for

    def _resolve(module_id, *a, **k):
        rec = _live(module_id, *a, **k)
        if rec is None and module_id in HISTORICAL_LINEAGE_RUN31:
            return HISTORICAL_LINEAGE_RUN31[module_id]
        return rec

    _lin.lineage_for = _resolve


def assert_lineage_not_declared(check) -> None:
    """Current production declares none of the three. The other half of the assertion."""
    from app.simulation import lineage as _lin
    still = [m for m in HISTORICAL_LINEAGE_RUN31
             if _lin.LINEAGE_DECLARATIONS.get(m) is not None] \
        if hasattr(_lin, "LINEAGE_DECLARATIONS") else []
    check(not still,
          "current production declares no lineage record for B3.2, B3.4 or B3.5, so these "
          "historical relationships cannot be satisfied by live code", str(still))


def historical_lineage_for(module_id, *a, **k):
    """`lineage_for` with the three removed records resolvable, for historical suites that
    imported the name directly and therefore cannot be reached by patching the module."""
    from app.simulation import lineage as _lin
    rec = _lin.lineage_for(module_id, *a, **k)
    if rec is None and module_id in HISTORICAL_LINEAGE_RUN31:
        return HISTORICAL_LINEAGE_RUN31[module_id]
    return rec


def historical_validated() -> dict:
    """
    `VALIDATED` with the sixteen Category-8/9 identities resolved to their SUPERSEDED
    implementations, for suites that look modules up in the routing table or inspect their
    source. Everything else is the live entry, so a suite covering other categories keeps
    testing current production there.
    """
    from app.simulation.models import VALIDATED
    merged = dict(VALIDATED)
    merged.update(LEGACY_CAT89)
    return merged
