# Chart group labels: retiring the C1..C11 category scheme from every chart surface

**Date:** 2026-08-05
**Branch merged:** `claude/chart-group-labels-s5s90m` (merge commit `a67862b`, work commit `b641128`)
**Scope:** display-only relabelling of every chart surface. No code id, `method_class`, or stored
`module_id` was renamed.

This report was authored separately from the merged code change: the implementing session was
blocked by a subagent write-restriction from committing a new report file, so the code landed on
`main` with only a pointer appended to `T6_HANDOFF.md`. This file closes that gap in the report
trail.

## Where the retired C1..C11 scheme was found

The surface inventory (`REPORT_2026-08-05_surface-inventory.md`) did not catch these. Every one is a
user-facing chart label, axis, legend, tooltip, or export header built from the retired scheme.

| File | Surface | Defect |
|---|---|---|
| `assets/js/neural_flow.js` | Signal Flow (`d-neural`) | Category micro-labels, node labels, tooltips, "from:/to:" lines, and the document-feeds list all built `'C'+cat.id` strings. `cat.short` was a hardcoded array of retired names applied by array position. A literal `"Cat 8 loop"` appeared in the governance-feedback tooltip. |
| `assets/js/detail.js` | Signal Web sphere (`d-web`) | The 3D sphere axis label used `cat.num`, the current-scheme id (`A1`, `B2`, ...), which is also forbidden in user-facing text. |
| `assets/js/detail.js` | Ensemble Analysis (`d-ensemble`) | X-axis labels and legend pills literally read `"Cat "+(i+1)`; the hover tooltip showed the module id `d.num` (e.g. `A1.1`). |
| `assets/js/detail.js` | Provenance trace ("why?" line) | `t.worstCat.num`, `t.worstMod.num`, and `f.module.num` were prefixed onto every rendered explanation. |
| `assets/js/export.js` | Signal History XLSX export | Column headers literally read `"Cat 1 EVM"`, `"Cat 2 Schedule"`, and so on. |

All labels were switched to the category **names** already used by the Signal Ledger
(`assets/js/app.js` / `taxonomy.js`) — Cost and EVM Performance, Schedule Performance, Cost Risk,
etc. — reusing the existing naming source of truth rather than inventing new strings.

### Left alone, deliberately

- `assets/js/charts3d.js` contains a real `Cat 6` label, but it is dead code: never invoked outside
  the non-loaded `deepdive.js`. Out of scope; not touched.
- `assets/js/projectnet2d.js` and `assets/js/app.js` (the Signal Ledger, the naming source of truth)
  were already clean.
- Internal code ids `a1`, `b2`, `c1` and stored `module_id` values are unchanged. This was a
  display-only sweep.

## The collision that made this worth doing carefully

The retired scheme's `C1`..`C11` were project **categories**. In the current taxonomy, `C` is the
group **Data and Evidence Health**. A reader seeing a chart labelled `C3 Cost` beside a taxonomy that
defines `C` as evidence health would draw the wrong conclusion. Relabelling by group and purpose
removes the collision entirely.

## Counts

Established from `taxonomy.js` (the file `index.html` actually loads):

- 12 categories / 101 modules total.
- 100 distinct computations once Document Risk Score is excluded — matches `NAMING_AUTHORITY.md`
  and the existing text in `knowledge.js`.
- Signal Flow's header "96 MODULES · 11 CATEGORIES" was **already numerically correct**: it is
  computed dynamically by `projectLevelCategories()`, which excludes the single portfolio-level
  category `d1` (`101 - 5 = 96` modules, `12 - 1 = 11` categories). Only the labels were wrong; the
  numbers were not. No count was changed or dropped.

## Category description accuracy

`b1` (Signal Synthesis) and `b2` (Evidence Combination) share the identical role caption "what the
evidence collectively means" in `CAT_ROLE`. This is not a `NAMING_AUTHORITY.md` contradiction, so it
was **not** mechanically changed, but it erases the distinction between primary synthesis and
independent cross-check that is documented elsewhere in the code. **Flagged for owner decision.**

## Verification

- **Fault injection:** reverted one Signal Flow label back to `'C'+cat.id`; the headless-Chromium
  DOM scanner caught it live against a seeded computed project (`PRJ-CHARTLBL`); reverted; confirmed
  clean. The fault was proven to actually fire before trusting the green.
- **Charts still draw:** Signal Flow SVG rendered 468 shapes / 164 labels; Signal Sphere produced
  non-empty canvas pixels — both before and after relabelling.
- **Server suite:** 39/39 files, 2200/2200 checks green (fresh DB per file).
- **`tests.html`:** 51/51.
- **`tests_render.html`:** 106/107. The single failure is the pre-existing auth-gated "production
  read path" check, which is red on `main` too and is the stated acceptable exception.

## Files changed by the merged work

`assets/js/neural_flow.js`, `assets/js/detail.js`, `assets/js/export.js`, `T6_HANDOFF.md`.

## Open item handed to the owner

- The identical `b1` / `b2` role caption in `CAT_ROLE` (`assets/js/taxonomy.js`). Decide whether
  Signal Synthesis and Evidence Combination should carry distinct descriptions.
