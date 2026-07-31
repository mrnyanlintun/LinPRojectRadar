"""
The module registry: which of the 101 computations this server can actually perform.

The registry reads p0-baseline/module_renumbering_map.csv, the same source of truth the frontend
registry is generated from, so the two cannot drift.

It refuses loudly. A module that has not been ported and numerically validated against the
JavaScript is NOT computed and NOT silently omitted: asking for it raises. An unvalidated module
producing a confident wrong number is the failure this design cannot tolerate, and a shorter
signal array that nobody notices is the same failure wearing a quieter coat.
"""

from __future__ import annotations

import csv
import pathlib
from typing import Any, Callable

from .models import SIMULATION_VERSION, STOCHASTIC, VALIDATED  # noqa: F401
from .rng import make_rng, seed_from

CSV_PATH = pathlib.Path(__file__).resolve().parents[3] / "p0-baseline" / "module_renumbering_map.csv"


class MissingModuleError(RuntimeError):
    """Raised when a caller asks for a module this server cannot compute."""


class PortfolioModuleError(RuntimeError):
    """Raised when a single-project computation reaches a Group D module."""


def load_registry() -> list[dict[str, str]]:
    """Every live module from the CSV, in file order."""
    with CSV_PATH.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    return [r for r in rows if r["new_id"].strip().upper() != "RETIRED"]


def registry_index() -> dict[str, dict[str, str]]:
    return {r["new_id"]: r for r in load_registry()}


def available_modules() -> list[str]:
    """New ids this server can compute today."""
    return sorted(VALIDATED)


def unported_modules() -> list[str]:
    """Everything declared but not yet ported and validated."""
    return sorted(set(registry_index()) - set(VALIDATED))


def group_of(new_id: str) -> str:
    row = registry_index().get(new_id)
    return row["group"] if row else ""


def run_module(new_id: str, si: dict, rand: Callable[[], float]) -> dict[str, Any]:
    """
    Compute one module. Raises rather than approximating.

    Group D is a hard error here rather than an abstention: those modules need three or more
    projects, so a single-project path reaching one is a routing mistake, not missing data, and
    reporting it as "insufficient data" would hide the mistake.
    """
    index = registry_index()
    if new_id not in index:
        raise MissingModuleError(f"{new_id} is not in the module registry")
    if index[new_id]["group"] == "D":
        raise PortfolioModuleError(
            f"{new_id} is a Group D portfolio-level module and requires 3 or more projects; "
            f"it cannot be computed on a single project"
        )
    if new_id not in VALIDATED:
        raise MissingModuleError(
            f"{new_id} ({index[new_id]['module_name']}) has not been ported and validated "
            f"against the JavaScript implementation; this server refuses to compute it"
        )
    _, fn = VALIDATED[new_id]
    return fn(si, rand)


def run_all(si: dict, scenario_id: str, period: str,
            only: list[str] | None = None) -> dict[str, Any]:
    """
    Run every module this server can compute, on one project's signalInputs.

    The generator is seeded once from (scenario_id, period) and shared, so the sequence a
    stochastic model draws depends only on the scenario and period, never on the participant or on
    how many modules ran before it.
    """
    seed = seed_from(scenario_id, period)
    rand = make_rng(seed)
    # The sim.js pair derive their own streams from the seed rather than sharing this generator,
    # so they need the seed value itself. Published here so every module keeps one call signature.
    from .models import SEED_HOLDER
    SEED_HOLDER["seed"] = seed

    index = registry_index()
    ids = only if only is not None else available_modules()

    results = []
    abstained = []
    for new_id in ids:
        out = run_module(new_id, si, rand)
        if out.get("insufficient_data") or out.get("status_color") is None:
            abstained.append(new_id)
            continue
        out = dict(out)
        out["module_id"] = new_id
        out["group"] = index[new_id]["group"]
        out["category"] = index[new_id]["category"]
        if new_id in STOCHASTIC:
            out["seed"] = seed
        results.append(out)

    return {
        "simulation_version": SIMULATION_VERSION,
        "seed": seed,
        "scenario_id": scenario_id,
        "period": period,
        "computed": results,
        "abstained": abstained,
        "unported": unported_modules(),
    }
