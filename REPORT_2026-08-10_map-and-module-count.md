# The detail page map, and 101 modules where a project has 96

**Date:** 2026-08-10
**Branch:** `claude/period-recompute-new-docs-1nfjnx`, from `origin/main` at `0067a80`
**Model:** the session ran on `claude-opus-5`; the brief asked for Sonnet, which is not something
a session can switch itself to. Flagged rather than left unsaid.

**Verification:** server suite **54 suites, 2970/2970**, fresh migrated SQLite per test file (the
new `test_map_and_module_count.py` adds 33). `tests.html` **51/51**. `tests_render.html`
**257/258**, 23 net new checks, the one red the pre-existing auth-gated row. Real-browser drive
of the detail page, **20/20**, plus a separate drive of a project with no coordinates. Four
faults injected, each hash-confirmed applied and reverted.

**No migration was added.** Unapplied in production, unchanged: **0020, 0021, 0022, 0023, 0024,
0025.** No `DATABASE_URL` pointed anywhere but throwaway SQLite. Production was neither inspected
nor queried. Nothing under `server/app/simulation/` was touched.

---

## LEAD: what else depended on MapLibre

**Nothing live.** Four files referenced it. Traced, not taken from the comments:

| File | What it had | Live? |
|---|---|---|
| `index.html` | `<link>` + `<script>` for the vendored CSS and JS, loaded unconditionally on every page view | **Yes — removed** |
| `assets/js/detail.js` | the project detail Location section built a `maplibregl.Map` | **Yes — removed** |
| `assets/js/app.js` | a ~400-line portfolio MapLibre stage | **No — unreachable** |
| `assets/js/atlas.js` | the word, in one comment | No |

**The app.js stage is genuinely dead, and I verified it rather than trusting its own note.**
`scheduleMapWarmup()` has no callers. `buildMap()` has exactly one other reference,
`if (mapBuilt) buildMap()` at app.js:2822, and `mapBuilt` is assigned true in only two places,
both *inside* `buildMap()` — so it cannot become true unless `buildMap()` has already run, and
nothing else runs it. The path is closed.

It is **left in place**, as its own note asks: removing it touches ~400 lines, two vendored files
(837 KB) and the map markup, and that is a separate change with separate verification. It guards
on `typeof maplibregl === "undefined"` and returns, so it is harmless now the library is not
loaded, and the new suite pins both the orphan marker and that guard so it cannot quietly come
back into service.

**`tiles.openfreemap.org` also came off the CSP.** Nothing requests it any more, and a policy
that permits a host nothing uses is a standing permission for nothing. It has the side benefit of
making "no external request" enforceable by the browser rather than only by inspection.

### Does the portfolio Map view have the same problem? No.

Established and **not changed**, as instructed. The portfolio's view switch (`app.js:1196-1203`)
hides the MapLibre container unconditionally and calls `buildAtlasStage()`, which renders
`LinAtlas`. It has shown the atlas since T11. It is **not the same code path** as the detail page:
the portfolio goes through `buildAtlasStage` in `app.js`, the detail page through the `d-globe`
lazy init in `detail.js`. Two separate call sites; only one was broken.

### What the detail page does now

The atlas renders as the map on first open, from geometry that ships with the application. Driven
in a real browser:

```
map: {"atlasSvg": true, "markers": 3, "maplibreCanvas": false,
      "note": "Matched to: 1600 Pennsylvania Ave NW, Washington, DC"}
off-origin requests: ['https://accounts.google.com/gsi/client']   <- the SSO script, aborted
PASS  the atlas renders as the map, on first open
PASS  and no MapLibre canvas is mounted
PASS  with the project marked
PASS  the matched address line is kept beneath it
PASS  no request to a tile host or for the maplibre library
```

A project with no coordinates, driven separately:

```
{"markers": 0, "hostEmpty": true,
 "note": "No map position. Add a site address to place this project.",
 "badge": "no location"}
page errors: []
```

No marker, an honest note, and nothing thrown.

---

## Where the 101 came from

`LIN_CATEGORIES` is the whole taxonomy. Measured:

```
ALL categories: 12   modules: 101
PROJECT-level : 11   modules:  96
PORTFOLIO-only: D1 Portfolio Health (5)
```

Every count on the detail page was `LIN_CATEGORIES.length` or
`LIN_CATEGORIES.reduce((n, c) => n + c.modules.length, 0)` — the whole taxonomy, on a page that
shows one project. Group D is portfolio level: its five modules all declare
`required: ['portfolioVectors']` and it needs more than one project by definition.

The page was therefore disagreeing with itself. The Signal Flow diagram inside it already called
`projectLevelCategories()` and read **96 modules, 11 categories**; the section badge above that
same diagram read **101 modules**.

### Every surface with the error

All of them on the project detail page, plus one row in the shared ledger builder. Twelve sites:

| Site | What it did |
|---|---|
| `detail.js:930-931` | the section badges: "101 modules" on Signal Flow and Signal Web, "12 categories" on Project Signal Network |
| `detail.js:327` | Signal Web sphere subtitle and footnote |
| `detail.js:405` | Ensemble Scatter header, "N total" |
| `detail.js:186` | `catPointFor` spaced the spider-web axes over **12** slots |
| `detail.js:1500` | Executive Brief prose: "101 signal modules across 12 analytical categories" |
| `detail.js:1785`, `:1852` | Executive Brief status and subtitle |
| **`detail.js:330`, `:381`** | **iterated** all categories building the Signal Web |
| **`detail.js:803`** | **iterated** for the "also elevated" list, so a portfolio module could be named on a project |
| **`detail.js:2116`, `:2136`** | **iterated** building the 3D module list and its axis labels |
| **`detail.js:2279`, `:2337`, `:2433`** | **iterated** the Ensemble Scatter, plotting D1's five modules as a twelfth column with its own legend pill |
| `detail.js:802` | a fallback filtered on `!c.parked` — **which does not exclude Portfolio Health, because it is not parked** |
| `app.js:1663-1674` | the Signal Ledger rendered a Portfolio Health row |

The six marked **iterated** are worse than a wrong number: they drew portfolio-level modules onto
a single project's charts.

The `!c.parked` fallback is worth its own line. `parked` and `level` are different questions, and
D1 is `parked: false`. Anything filtering on parked keeps Portfolio Health. Asserted:

```
PASS  filtering on 'parked' would NOT exclude Portfolio Health, which is why every filter
      here uses the level
```

**The fix is one pair of helpers** in `detail.js`, `projectCats()` and `projectModuleCount()`,
used by every count, axis and iteration on the page, so it cannot disagree with itself again. The
ledger's Portfolio Health row is gone; the ledger's only host is the detail page.

### Swept and clean

`deepdive.js`, `neural_flow.js`, `projectnet2d.js`, `knowledge.js`, `export.js`, `signals.js`,
`decision.js` and the research pages carry no unfiltered `LIN_CATEGORIES.length` or `.reduce`.
`neural_flow.js` and `projectnet2d.js` already call `projectLevelCategories()`.

**Two things found and deliberately not changed:**

- `app.js:1517 activeModuleTotal()` counts the whole taxonomy and falls back to a literal 103.
  It has **no callers** — dead. Reported, not fixed, per the standing policy on dead code.
- `detail.js buildModuleAxes()` still sums the whole taxonomy. Also **no callers** — dead, and
  already recorded as such in an earlier report. The new suite asserts it stays uncalled, so if
  anyone revives it the check goes red rather than the defect coming back with it.

### Portfolio Health is untouched where it belongs

Still 12 categories and 101 modules in the taxonomy; still five modules on D1. On the portfolio
it is the **"Portfolio health" card** (`index.html`, filled by `renderPortfolio` in
`workspace.js`), which reads it from each project's own stored result.

**A correction to my own work.** My first draft of these code comments said Portfolio Health was
reached through "the Health dialog (`ingest.js openHealthModal`)". That is wrong:
`openHealthModal` **does not exist anywhere in this codebase**. `deepdive.js:2260` reaches for it
behind a guard, so that call is a permanent no-op. I found this because my drive script asserted
the dialog was reachable and it failed. Both comments now name the card, which I verified.

---

## Tests: neither defect had any coverage

Both browser suites were green with the detail page advertising 101 modules and rendering a
Portfolio Health row. That is why this change adds checks rather than adjusting one.

- **`tests_render.html` group 20 / 20b / 20c**, 23 checks: the counts, the ledger rows, the atlas
  in the Location section, and the no-coordinates case.
- **`server/tools/test_map_and_module_count.py`**, 33 checks, no database: the file-level
  properties.

### One of my own checks could not fail, and I caught it by injecting the fault

Group 20 originally asserted `typeof window.maplibregl === "undefined"`. I restored the maplibre
script tag to `index.html` and **the harness stayed green at 256/257** — because
`tests_render.html` has its own script list and never loads `index.html`. The assertion was
vacuous: it would have passed no matter what the application page did.

It was replaced with what that harness *can* see (the atlas renders into the Location section,
no MapLibre canvas is mounted, the Location badge reads "located"), and the file-level property
moved to the server suite, where reading the file **is** the check. Re-running the same fault
there now fails:

```
FAIL  index.html loads no maplibre script  [['<script src="assets/vendor/maplibre-gl.min.js"']]
```

### Faults injected

| Fault | Detected by | Result |
|---|---|---|
| Restore the unfiltered badge count | 4 checks | "no badge says 101 modules" → found at index 16; the 96/11 checks went false |
| Restore the Portfolio Health ledger row | 4 checks | row count 11 → 12, the health row and `d1` reappeared, the portfolio note came back |
| Restore the maplibre script tag to `index.html` | **0 at first** | the vacuity above; **1** after the suite was corrected |
| Reintroduce a `maplibregl` use in `detail.js` | 1 check | `['maplibregl !==']` |

Each was hash-confirmed applied and hash-confirmed reverted, with the baseline re-run green after
each.

### Red tests

**None of the existing suites went red.** The three red tests recorded in earlier sessions do not
recur here: nothing asserted the old counts or the old map, because nothing tested either. The
only failures during this work were **three in my own drive script** — two wrong CSS selectors
(`.collapse-badge` is the real badge class) and one assertion about a function that does not
exist. All three were measurement bugs on my side, found by checking the markup, and none was a
defect in the application.

## Not done

- The ~400-line orphaned MapLibre stage in `app.js` and the two vendored files (837 KB) are still
  on disk. Removing them is the clean follow-up its own note describes.
- The portfolio Map view was not changed. It never had this problem.
- `activeModuleTotal()` and `buildModuleAxes()` are dead and were left dead.
