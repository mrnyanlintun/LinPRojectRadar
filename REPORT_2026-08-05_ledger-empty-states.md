# Two empty states for the Signal Ledger: "No data" and "Not relevant"

**Date:** 2026-08-05
**Branch:** `claude/ledger-empty-states-s5s90m` (merged to `main`, PR #221, merge commit `69b37c8`)
**Model:** Sonnet
**Note on process:** this task took three attempts. The first session completed only Part 3
(storing the abstention message) and stopped early on session budget pressure, not a real
blocker. A second attempt failed on a worktree collision with the first session's leftover
worktree; the worktree was confirmed clean, matched origin exactly, and was removed. The third
attempt resumed the same branch and finished Parts 1, 2, and the rest of Part 3.

---

## LEAD FINDING — how many modules fall into each situation, on a real project

| Situation | Count | Notes |
|---|---|---|
| **Not relevant** (blue) | 6 of 101 taxonomy modules | Construction-phase-only on a Design-sector project. 0 in the reverse direction — no Design-only modules exist today. |
| **No data** (grey) | 78 of 95 runnable modules | On a thin-evidence fixture; all 78 carried their own abstention message. |
| **Computed** | 17 of 95 | Real verdicts (the fixture resolves Green overall). |
| Not ported to this taxonomy version | 1 | Document Risk Score. |

This confirms the shape the task described: on a project with real but thin evidence, the large majority of empty rows are genuinely "no data," a small fixed set is "not relevant" by sector, and previously all of them looked identical.

---

## PART 3 — the abstention message, storage and render

A prior session on this branch already changed `server/app/simulation/registry.py`'s `run_all()` to retain the abstention message alongside the module id, instead of keeping only the bare id:

```python
if out.get("insufficient_data") or out.get("status_color") is None:
    abstained.append({"module_id": new_id, "reason": out.get("evidence_metric")})
```

**No computation was changed** — this only retains an output the module already produced and previously discarded. Confirmed independently: `server/app/simulation/compute.py`'s rollup reads only `run["computed"]` (verified directly in the merged code, lines 45 and 71), never `run["abstained"]`, so retaining the message cannot affect any category or project status.

This session finished the render side:
- **New Alembic migration `0020_abstained_modules`** adds a nullable JSON column `computed_results.abstained`, so the message persists on the stored row rather than existing only transiently inside a single request. **This migration was run only against throwaway SQLite in the agent's worktree. Production has not been migrated, and `DATABASE_URL` was never pointed at production Postgres.**
- `server/app/documents.py`'s `run_and_store` and `_result_view` persist and serve the reason.
- The Signal Ledger (`assets/js/app.js` `categoryLedgerHtml`) renders it verbatim beside a "No data" module, in a new `.cat-mod-reason` block, only when a message exists. **A module that produced no message shows the state and nothing more — no reason was invented for it.**

---

## PART 1 — the two new states, and their non-voting property

The five verdicts (Complete, Green, Yellow, Amber, Red) are unchanged. Two new states were added, and both read as *reasons a row is empty*, not further verdicts:

- **`NODATA`** — the module ran (the project has been computed for this period) but abstained: a figure or series it needed was not in the documents.
- **`NA`** — the module's sector tag excludes it from this project (a construction-phase module on a Design-sector project, or the reverse).

`assets/js/taxonomy.js`'s `getModuleStatus` was extended to distinguish `'NODATA'` from a plain `null` (the project has never been computed at all) and from the pre-existing `'NA'` (sector exclusion) — verified directly in the merged code (`taxonomy.js` lines 391–412).

**Neither state contributes to a category or project status.** This is enforced structurally, not by convention: the server-side rollup in `compute.py` only ever reads `run["computed"]`, so `NODATA` and `NA` rows are invisible to it by construction, and this was **proven with a fault-injected test**, not merely asserted — a fabricated vote inserted into the fusion input for a `NODATA`/`NA` module moved the category status, confirming the exclusion is load-bearing rather than accidental.

---

## PART 2 — everywhere the states are shown, with measured contrast

New CSS tokens, declared for both themes, distinct from the existing five verdict colours:

| Token | Theme | Hex | Contrast vs surface | Contrast vs page background |
|---|---|---|---|---|
| `--status-notrelevant-text` | light | `#5b3dd6` | 6.17 | 6.34 |
| `--status-nodata-mod-text` | light | `#55606f` | 5.79 | 5.94 |
| `--status-notrelevant-text` | dark | `#9d8cff` | 7.00 | 7.27 |
| `--status-nodata-mod-text` | dark | `#a6afc2` | 8.75 | 9.08 |

**All four combinations clear the 4.5:1 AA floor**, measured directly from the actual declared colour values (verified present in the merged stylesheet), the same floor the existing five verdict colours meet.

**Status does not depend on hue alone.** The five verdict pills are borderless; the two new states carry a distinct border style — `.pill-nodata` dashed, `.pill-notrelevant` dotted — so a reader who cannot separate hue can still tell every state apart.

Wired into:
- The Signal Ledger (module rows).
- The Signal Sphere legend (`detail.js`).
- The Signal Flow legend and node colouring (`neural_flow.js`, plus `LIN_STATUS_COLORS` in `config.js`).

**The Signal Network (`projectnet2d.js`) was deliberately left untouched.** It renders at the category level only, and a category can never itself read `NODATA` or `NA` — those are module-level states that do not propagate upward, per the non-voting property above. There was nothing there to wire.

---

## VERIFICATION

New server suite `server/tools/test_ledger_empty_states.py`: **21/21**, including the fusion-fault-injection proof of the non-voting property described above.

New `tests_render.html` **Group 18**, **12 checks**, driving the real production render functions (`categoryLedgerHtml`, the Signal Sphere and Signal Flow legend builders) against realistic fixtures in headless Chromium, not a synthetic stand-in.

Every new check was fault-injected and confirmed to fail, then reverted with the baseline re-confirmed:
- Pill border style swapped between the two new states — turned the shape-distinction check red.
- Pill CSS class swapped — turned three checks red.
- A fabricated vote inserted into the fusion input for an excluded module — moved the category status, turning the non-voting check red.

All reverted; full suites green afterward.

**Full suites on the merged result:** server **42 suites, 2290/2290** (fresh SQLite DB per file), `tests.html` **51/51**, `tests_render.html` **169/170** (the one red is the pre-existing auth-gated "production read path" check, unchanged and red on `main` too).

---

## HONEST GAP

No fully interactive, login-driven browser session against seeded Design and Construction projects was run end to end. Verification instead drove the real production render functions against realistic fixtures in headless Chromium — the same method the codebase's own prior Group 16 verification used. This is weaker than a live logged-in session but stronger than a unit test in isolation, since the actual rendering code that ships is what was exercised.

---

## FILES CHANGED

`server/alembic/versions/0020_abstained_modules.py` (new), `server/app/documents.py`, `server/app/research_models.py`, `server/tools/test_ledger_empty_states.py` (new), `assets/js/taxonomy.js`, `assets/js/app.js`, `assets/js/detail.js`, `assets/js/neural_flow.js`, `assets/js/config.js`, `assets/css/radar.css`, `tests_render.html`, `T6_HANDOFF.md`, this report. No module id or number appears in any user-facing string; no em dashes. Nothing recomputes in the browser.
