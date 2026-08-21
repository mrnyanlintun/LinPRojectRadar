# Run-43 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v28`.

## Why there is a successor at all

Run 42 accepted a successor freeze of the v27 instrument. The owner then ruled, on 2026-08-21,
that **38 of the 101 registered modules are retired from service**.

Retirement is a statement about the taxonomy and the explanation burden. It is **not** a claim
that any module's arithmetic is wrong, and nothing is deleted: every retired module keeps its
registry entry, its formula function and its audit lineage, and asking `run_module()` for one by
name still resolves and still returns exactly what it returned under v27. What changes is which
modules the production paths **enumerate**, and therefore which reach a participant.

The single authority for which modules are in service is the `notes` column of
`p0-baseline/module_renumbering_map.csv`. **No list of retired identifiers is written anywhere
else in the tree**, so reinstating a module there restores it to service with no other edit.

Which modules a participant sees is executable behaviour, so v27 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 successor -> Run 42 mechanism repair -> v27 successor
    -> owner's retirement ruling -> v28 successor

## The populations after the retirement

| Population | Count | Derived from |
|---|---|---|
| Registered in the registry | 101 | `registry.registry_index()` |
| Retired from service | 38 | the `notes` column of the registry map |
| In service | 63 | `registry.service_index()` |
| Computed by the analytical server | 62 | `registry.available_modules()` |
| Group D (Portfolio Health) in service | 0 | `portfolio_health.live_portfolio_modules()` |

## What did NOT change, proved by execution

| Subject | Result |
|---|---|
| Registered module population | 101, identical |
| `run_module()` over all 101 identifiers | **0 diff lines** against a worktree at v27 |
| Modules in service whose computed result moved | **0** |
| Voting set | `A1.7`, `A1.8`, unchanged |
| Group C contributes to project status | No, unchanged |
| Portfolio Health contributes to project status | No -- it never did |
| `canonical_v8`, the Portfolio Health computation | untouched, and its oracles still execute |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

This is not inferred from a source diff. The comparison was **proved failable**: re-injecting a
retirement short-circuit into `run_module()` produced 1,530 diff lines, and removing it returned
the diff to 0.

## The scientific position

No input was invented, no fact fabricated, no qualification rule relaxed and no scientific method
changed. The 38 retired formulas are kept as the research record. The modules in service that
abstain for want of their governed structure still abstain, with the same reasons and the same
stable codes. `revision_resolution_status` remains NOT_ESTIMABLE by the deliberate fail-closed
decision Run 42 reported, and Run 43 did not overturn it either.

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run43_successor_freeze_gate.csv`.

The v25, v26 and v27 release records are preserved unchanged and still record their own stamps.
