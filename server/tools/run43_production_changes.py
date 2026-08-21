"""
RUN 43. THE PRODUCTION FILES THIS RUN CHANGED, DECLARED.

WHY THIS FILE EXISTS, and it is the Run-28/29/30/31/32/33/36/41/42 precedent unchanged. The
Run-20 baseline freeze compares production bytes against a pinned baseline, and the
declared-changes guard requires the differing set and the declared set to be EXACTLY equal -- so
an undeclared production edit is red and a declared file that was never touched is red too.

IT IS DECLARED HERE AND NOT FOLDED INTO AN EARLIER RUN'S LIST. A run's manifest is the record of
what THAT run did, and merging them would falsify both.

RUN 43 IS THE RETIREMENT OF 38 MODULES FROM SERVICE. It declares only the production paths no
earlier manifest already names. `registry.py`, `models.py`, `documents.py`, `index.html`,
`assets/js/detail.js`, `assets/js/taxonomy.js`, `assets/js/categories.js`, `assets/js/knowledge.js`
and `p0-baseline/module_renumbering_map.csv` are NOT declared here, because earlier manifests
already declare each of them and no path may appear in two -- one change may never be counted as
two.

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner ruling of 2026-08-21, Run 43: 38 registered modules are RETIRED FROM SERVICE. "
          "Retirement is a statement about the taxonomy and the explanation burden, not a claim "
          "that any arithmetic is wrong. Every retired module keeps its registry entry, its "
          "formula function and its audit lineage; what changes is that no production path "
          "enumerates it and no participant surface renders it. The single authority for which "
          "modules are in service is the `notes` column of "
          "p0-baseline/module_renumbering_map.csv, and no list of retired identifiers is written "
          "anywhere in the tree")

# `server/app/simulation/portfolio_health.py` IS NOT DECLARED HERE, and its absence is a fact
# about the guard's contract rather than an omission. That file was CREATED by Run 33 and is
# recorded in RUN33_NEW_PRODUCTION_FILES; it is therefore not in the Run-20 baseline list at
# code_audit/run20_production_freeze.sha256, and the declared-changes guard's own scope is
# exactly that list. Declaring it here makes the guard RED in two directions at once -- "declared
# but unchanged" and "not in baseline" -- because the guard is asserting the equality of two sets
# neither of which can contain it. Run 34 changed the same file under the same constraint. What
# Run 43 changed in it is the Portfolio Health offload: all five Group D identities are retired
# from service, so `live_portfolio_modules()` -- which intersects `canonical_v8.RESULT_KEYS` with
# `registry.service_index()` -- returns the empty tuple and the dispatcher returns a retired
# snapshot before `assemble` is reached. `canonical_v8` is UNTOUCHED and still computes: the
# arithmetic is preserved as the research record and the Run-33 supplied oracles are still
# executed against it directly.

#: Production files Run 43 CREATED.
RUN43_NEW_PRODUCTION_FILES: dict[str, str] = {}

#: Production files Run 43 CHANGED.
RUN43_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "R2": (
        _OWNER,
        "server/app/research_export.py",
        "THE EXPORT'S ENUMERATED POPULATIONS. The export iterates stored `module_results` and "
        "never the registry, so no retired module can reach a row by that path. What changed "
        "here is the population the export DERIVES for its own summary and coverage columns, "
        "which is now taken from the roster in service rather than from the whole registry. The "
        "four B1 modules at the `_RUN3_NEWLY_WIRED` site are IN SERVICE and are untouched, and "
        "their reachability is asserted directly by the Phase H tests.",
    ),
    "R3": (
        _OWNER,
        "server/app/training.py",
        "THE TRAINING SURFACE'S ABSTENTION POPULATION. `_abstained_by_category()` enumerated the "
        "registry; it now enumerates `registry.service_index()`, so a retired module cannot "
        "appear as an abstention on a training project. Nothing about the training regimes, the "
        "gating or the recorded events changes.",
    ),
}
