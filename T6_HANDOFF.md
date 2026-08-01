# T13b — THE TAXONOMY IS SETTLED AND COMMITTED. 100, not 101.

`GROUP_ASSIGNMENT.md` at the repository root is the authority. Merged to `main`.

| Group | Name in user-facing text | Count |
|---|---|---|
| A | Project Health | 52 |
| B | Recommendation and Governance | 36 |
| C | Data and Evidence Health | 7 |
| D | Portfolio Level | 5 |
| | **Total** | **100** |

**Document Risk Score is not counted.** It is a value the extraction model supplies and the server
carries through, not a computation the analytical server performs. **100 is current, not
permanent**: if it is ever implemented server-side the count becomes 101 and Group A becomes 53.

**Do not describe the registry refusal as a Document Risk Score exclusion.** It is a generic
catch-all for anything absent from `VALIDATED`, and its message is the wording of work outstanding.
Whether the value is unported by design or by accident is still unestablished.

**User-facing text uses "and", not the ampersand the code constants use.** Do not rename the
constants.

`server/tools/test_group_assignment.py` fails if the code and the artifact diverge. If it goes red,
the published taxonomy and the code have parted company and no sweep should run until that is
understood.

**`unported_modules()` is still wrong and is deliberately not fixed.** It counts the five Group D
modules as unported although `portfolio.py` implements them, reporting six where exactly one is.
The fix is inside `server/app/simulation/`, which the task forbade modifying. Both new checks
compute the genuinely unported set themselves and assert the over-report explicitly, so nothing
inherits the error. **This needs a decision: lift the prohibition for that function, or leave it.**

**STEP 4, THE MECHANICAL SWEEP, HAS NOT STARTED.** The naming authority document has now failed to
reach three consecutive sessions, and step 4 stops without it by its own terms: it rewrites
surfaces that must quote that document's standing description wording verbatim, and the task
summary carries the taxonomy but not the wording.

**A tenth hasSignals instance was found, and it was the root.** `statusKey()` still had the legacy
gate; the T12 legend fix had added a parallel `storedStatusKey()` beside it rather than correcting
it. It drives eight call sites, so an analysed project was placed on the radar's neutral mid-ring
and given the wrong marker colour, not merely mislabelled. Fixed, duplicate removed.

**`tests_render.html` now exists** and is the regression net for that whole family. 22 assertions,
every one proven able to fail by reverting its gate. It is NOT part of the 854 and will not run
itself: open `http://127.0.0.1:8010/tests_render.html` with the dev server up, after any change to
`app.js`, `detail.js`, `decision.js` or `taxonomy.js`. `dev_serve.py` serves it and `tests.html` by
exact name; `app/main.py` is unchanged and still refuses to mount StaticFiles at `/`.

**Two more vacuous checks found.** `test_simulation.py:49-50` asserts
`len(unported_modules()) == 101 - len(VALIDATED)`, a tautology that cannot detect the A4.1 gap. And
`unported_modules()` itself counts D1.1 to D1.5 as unported although they are implemented in
`portfolio.py`, reporting 6 where 1 is genuine.

---

# T11a — THE GLOBE HAS BEEN SEEN, AND IT RENDERS

The researcher confirmed by eye: hex-dot continents, cyan rim, atmosphere and the 23.4° tilt all
visible. After three sessions of measurement-only evidence, the globe is verified visually. Two
bugs came out of that first look, both fixed — see
`REPORT_2026-08-01_globe-view-sticks-and-rotates.md`.

**The watchdog asked once and broke the working case.** `mount()` resolves in ~40 ms; globe.gl does
not build its scene group until ~1 s later. A single `hasScene()` check at resolve always saw
false, so four seconds later the watchdog destroyed a healthy globe and switched to the atlas — the
symptom being "Globe switches back to Map on its own". It now **polls to a 6 s deadline** and stands
down the moment a scene appears. Do not return it to a single check.

**The globe was never rotating where it mattered.** `autoRotate` was only enabled for the empty
state and the non-interactive detail globe, so the portfolio globe *with projects on it* — the one
case a director sees — had rotation off by construction. It now rotates in every state.

**"Verified rotating at 0.35" was a property read, never a look.** three.js turns at 6°/s per unit
of `autoRotateSpeed`, so 0.35 was ~171 seconds per revolution: a still image. It is now `1.0`,
6°/s, one revolution a minute, and it respects `prefers-reduced-motion`. **Check motion by watching
it, not by reading the property** — that is precisely how this survived three sessions.

**The globe does place points.** Confirmed with two located projects: `points: 2, unplaceable: 0`,
tilt 23.4 after reload. A portfolio showing "0 project(s) placed" is a data condition — projects
without coordinates — not a globe fault.

**View selection sticks.** Radar, Map and Globe each persist and restore correctly, and globe assets
stay unloaded unless Globe is the restored view.

**The default is Map** for a user with no stored preference. A stored preference always wins, so
anyone who has selected Globe will keep landing on Globe. Moving the default to Globe is now a
defensible product decision rather than a safety question, but it has not been made.

---

# T11 — the default geographic view is now the flat SVG atlas, and it is MERGED

`assets/js/atlas.js`. SVG, no WebGL, no 3D library, **no animation loop**. It is the default on the
portfolio and on project detail, and it draws the country geometry already vendored for the globe,
so it needed no new assets.

**This is the view that cannot fail to render**, and that is why it exists: two sessions could not
verify the globe because the pane does not composite, and a globe that resolves `ok` while drawing
nothing is a black panel in front of a director. Verified with **0 rAF frames**: 177 country paths,
markers, 215 nodes, 11 ms — and at pixel level, marker centre `#26344f`, halo ring `#05080b`,
ocean beyond `#0e3049`, all exactly their variables. Full detail in
`REPORT_2026-08-01_flat-atlas-default-view.md`.

**The globe is kept, demoted to a third stage button, and now has a watchdog.** `mount()` resolving
is not the same as the globe drawing, so `LinGlobe` exposes `hasScene()` and the caller falls back
to the atlas after 4 s if the scene was never built. That watchdog fired for real in this session
and the fallback worked end to end.

**Marker legibility is solved by the halo, not by the background.** Without the dark disc, Yellow on
Miami/Maria land is **1.01:1** — invisible. With it, every status is ≥5.66:1 in every theme. Do not
"simplify" the halo away, and do not try to fix legibility by darkening the land; that was measured
on the globe's texture and only changes which status fails.

**MapLibre is now orphaned** — `scheduleMapWarmup()` has no callers and `buildMap()` is unreachable.
It is left in place, clearly marked, and deleting it (~400 lines, 837 KB of vendored files, the map
markup, and the `tiles.openfreemap.org` CSP entry) is a clean scoped follow-up.

**Nobody has looked at the atlas.** Everything above is measurement and pixel sampling, not a
picture. That is the first thing to do with a visible pane.

---

# READ FIRST — check the browser pane before planning any visual work

**Two consecutive sessions have now been lost to this.** Before anything else:

```js
document.visibilityState            // must be "visible"
// and count rAF frames over 1s     // must be > 0
```

If it is `"hidden"` with 0 frames, **globe.gl never builds its scene**, screenshots fail, and no
visual check or frame-rate measurement is possible. Say so and stop; do not spend the session
discovering it late. **This now applies only to GLOBE work** — since T11 the default geographic
view is the flat atlas, which renders fully with 0 rAF frames and is checkable either way. `preview_start` reporting "Browser pane opened", and the `PostToolUse` hook
saying a file "is now visible in the Browser pane", **both appear even when the pane is hidden** —
neither is evidence. Only the two checks above are.

Everything measurable works fine while hidden: `performance.getEntriesByType('resource')`,
`LinGlobe.palette()`, DOM state, the action API. That is how everything below was verified.

## Per-session report files

From 2026-08-01 onward every session writes `REPORT_<yyyy-mm-dd>_<short-task-name>.md` at the
repository root and commits it. The most recent is
`REPORT_2026-08-01_globe-verification-and-vendoring.md`.

## Dev-server caching — now fixed at the source

`dev_serve.py` sent `no-store` for `/assets` **or** paths ending `.html`. `index.html` served at
`/` matches neither, so the root document was still being cached — it hid an `index.html` edit in
this session exactly as the old `/assets` gap hid `detail.js`. It now also keys on a `text/html`
content type. If a page-level edit still seems not to apply, compare
`performance.getEntriesByType('resource')` `encodedBodySize` against what `curl` returns before
suspecting the code.

---

# T10 — two globe treatments. Built, NOT merged, and here is exactly what is missing.

Branch `t10-globe-treatments` at `3b5ee7d`. `main` is at `5ccc395`. 854 checks across 17 suites
pass. **Not merged**, for one reason: nothing was ever seen rendering.

## The blocker, and how to clear it

`document.visibilityState` was `"hidden"` for the whole session and `requestAnimationFrame`
produced **0 frames per second**. globe.gl builds its scene inside that loop, so the scene graph
never populated: no screenshot, no visual confirmation of either treatment, and **no frame rate**.

**Guarantee 7 is unmet.** The hex-dot resolution (3) was chosen conservatively *because* it could
not be measured, not because a measurement supported it.

**What the next session must do, with the pane visible:**

1. Look at both treatments. Nothing below has been seen.
2. Measure frame rate on each. If the abstract globe costs more than a few fps against the plain
   sphere, lower `hexPolygonResolution` from 3, or raise `hexPolygonMargin`.
3. Confirm the marker halo actually reads. The argument for it is analytic (below) and I believe
   it is sound, but it is not evidence.
4. Capture the three themes at 1280 / 1920 / 3840.

**Diagnostic that saves time:** `performance.getEntriesByType('resource')` and
`LinGlobe.palette()` work regardless of compositing — that is how everything below was verified.
But `globe.scene()` will show only a bare `Mesh` and `palette()` will return `tiltDeg: null` while
the pane is hidden. **That is not a bug.** Do not go chasing the tilt again; it is verified at
`fe4f59b` and unchanged.

Also: a scene walk over the abstract globe enumerates thousands of hex objects and will time the
tool out. Keep probes shallow.

## Marker legibility — the reasoning, so it is not re-litigated

The obvious fix does not work, and this was measured rather than assumed. Sampling the real
texture at six sites and computing WCAG contrast per status:

| Variant | Worst case |
|---|---|
| Texture as-is | **1.02:1** — Yellow over the Sahara |
| Dimmed to 62% brightness / 72% saturation | **1.01:1** — Red, once the sand is dark |

**Dimming only changes which status fails.** A single background brightness cannot serve four
colours at four different luminances. That is why the texture ships undimmed — do not "fix" it by
dimming.

What ships instead is a dark disc under every marker (`--globe-marker-halo`, `#05080b`), so
contrast is a property of the marker's own surround and is identical over ocean, desert, ice and
cloud: Red 4.9, Amber 7.5, Green 10.5, Yellow 13.4. Status colours are untouched.

It is a **labels layer with empty text**, not a second points layer — globe.gl allows only one
`pointsData`. Both are real 3D layers, so the disc is depth-tested. An HTML-overlay marker was
rejected: it would float in front of the far side of the planet.

## Verified by measurement (these do not need redoing)

| | |
|---|---|
| Treatment follows theme, both directions, real buttons | NYC abstract (177 hex polygons, cyan rim) ↔ Miami/Maria photographic |
| Repaint, not remount | `liveCount` steady at 1 across every switch |
| Texture only where used | 0 bytes under NYC; 529 KB same-origin on the photographic themes |
| Status colours across themes | byte-identical on all three |
| `rgba()` audit | all **14** variables the globe reads, all three themes — none |
| Empty state | still rotates at 0.35 with zero points |

## Guarantee 5 — Google Fonts is now vendored; two dependencies remain by necessity

**Fonts are done.** 18 woff2 (Archivo, Inter, IBM Plex Mono; latin + latin-ext) plus a generated
`assets/vendor/fonts.css`, all same-origin, SIL OFL 1.1. `unicode-range` is preserved so only 4
files / 142 KB actually transfer on the sign-in page. Vendor total **4.5 MB → 5.9 MB**.

Two remain and neither can be vendored. **Both failure paths are verified live, so neither needs
re-testing:**

- **`accounts.google.com`** — with the Google global deleted, the username and password form still
  renders, stays enabled, and authenticates. A blocked network does not lock anyone out.
- **`tiles.openfreemap.org`** — with `maplibregl` deleted, the map degrades to a muted panel
  reading "Map tiles unavailable: check connection" with the project list still present. Not a
  blank panel. A 9-second watchdog in `app.js` covers the style-never-loads case.

Note the portfolio stage buttons are now **Radar** and **Globe** only — the MapLibre map is the
globe's WebGL-off fallback rather than a stage the user picks, which makes the tile host a
fallback-of-a-fallback.

## The `[data-set-theme]` trap is gone

`applyTheme` no longer sweeps `[data-set-theme]`; nothing ever carried it. A comment now names
`openThemeFlyout()` as the real switcher, so the next grep does not repeat the false negative.

---

# T9 — the detail globe is VERIFIED. Read this section first.

## Task 1 is settled. The detail globe renders, and the fault was never in detail.js

All three checks pass, measured live on a clean profile at `fe4f59b`:

| Check | Result |
|---|---|
| `LinDetail.teardown` exists | **function** |
| Location section renders on a project with coordinates | **yes** — badge "located", note "Matched to: …" |
| `LinGlobe.liveCount()` 2 with both globes, 1 on leaving detail | **1 → 2 → 1**, detail canvas released |

**The cause of the previous session's failure was a stale HTTP cache entry, not the code.**
Do not go looking at the section markup again; it was always correct.

- The browser held `detail.js` at **111,064 bytes** with `transferSize: 0` and
  `deliveryType: "cache"`, while the server served **112,583 bytes**.
- That entry was stored **before** `no-store` was added, so it carried the old freshness
  lifetime and the browser reused it **without revalidating**. A new tab does not help: the HTTP
  disk cache is per profile, not per tab.
- `globe.js` was first fetched *after* `no-store` landed, so it never had a cacheable entry and
  always updated. That is the whole of the "same directory, different behaviour" mystery.
- **The fix that works:** `fetch(url, {cache:'reload'})` once, then reload. That overwrites the
  poisoned entry. After that `no-store` keeps it correct.
- **Diagnostic to reach for first:** compare `performance.getEntriesByType('resource')`
  `encodedBodySize` against the bytes `curl` gets from the server. If they differ, it is the
  cache, whatever the response headers currently say.

## Two traps found while verifying, both of which cost time

- **`requestAnimationFrame` does not fire when the pane is not displayed.** The automated
  browser does not composite frames unless the Browser pane is visible, so rAF callbacks never
  run — and screenshots fail with "not compositing" for the same reason. globe.gl still builds
  its scene, because it uses its own timers. Anything that must run after a library finishes
  building should be on `setTimeout`, not rAF. This silently left the globe upright.
- **`[data-view]` is not `[data-nav]`.** `[data-view="globe"]` is the portfolio's radar/globe
  toggle. Leaving the detail page — and therefore `LinDetail.teardown` — is `showPage`, driven
  by `[data-nav]` (`app.js:1704`). Clicking the wrong one looks like a teardown leak.
- Automated typing of `!` into the password field was rejected by the server while the identical
  credentials succeeded through `LinStore.postWithTimeout`. A typing artefact, not a product
  fault, but it will cost you a detour.

## Running the suite: migrate first

`854 checks across 17 suites` reproduced exactly at `fe4f59b`. The suites need a **freshly
migrated** database and do not migrate themselves — run `python -m alembic upgrade head` against
each throwaway SQLite before the suite, or every one of them dies on `no such table:
participants` and reports nothing. A Git Bash `mktemp -d` path is not a valid SQLite URL on
Windows; use a Windows-style absolute path.

## What T9 completed, and what is untouched

| Task | State |
|---|---|
| 1 — verify the detail globe | **Done, measured** |
| 3 — axial tilt + empty state | **Done, measured** (`fe4f59b`) |
| 2 — rewrite the About page | **Not started** |
| 4 — globe follows the theme | **Colour done, measured** (`9dbf5c3`) |
| 4 — the Miami-only beach motif | **Not started** — the one part of Task 4 still outstanding |
| 5 — the 84 em dashes | **Not started**, deliberately: a partial pass is worse than none |

### Task 4, before anyone starts it

One real bug was found and fixed on the way to Task 3, and it is the mechanism Task 4 depends on:
**`three.js` `Color.set()` cannot parse `rgba()`**, and several theme surfaces are declared with
alpha (`newyork`'s `--surface-soft` is `rgba(21,28,32,.86)`). `Color.set` threw, the `try/catch`
swallowed it, and the globe kept globe.gl's default material. `stripAlpha()` in `globe.js` now
handles this. **Every further theme variable piped into the globe must go through `themeColor()`**,
or it will hit the same wall.

**Both of the questions raised here have since been answered, and Task 4's colour work is done
(`9dbf5c3`). The claim that there was no theme switcher was WRONG — corrected below.**

1. **The switcher exists.** It is built in JS as fly-out pills (`app.js:2065`, opened from
   `.dock-menu`), whose `onClick` calls `applyTheme` directly. **Nothing carries
   `[data-set-theme]`** — the `querySelectorAll` for it inside `applyTheme` matches nothing and is
   dead code. Grepping for that attribute is what produced the false negative. Grep `THEME_META`
   or `openThemeFlyout` instead.
2. **The mapping**, from `THEME_META` (`app.js:1845`) and confirmed by clicking all three pills:

   | Button | `data-theme` |
   |---|---|
   | Miami | `light` |
   | NYC | `newyork` (default) |
   | Maria | `maria` |

   **`dark` is Gotham and is the unused fourth** — archived, still renders if forced, not offered
   and not the default; a persisted `"dark"` falls through to `newyork` (`app.js:2658`).

   So `app.js:1653` and the brief never actually disagreed: Miami's identifier *is* `light`.

`LIN_STATUS_COLORS.refresh()` (`config.js`) is already the established "re-resolve the palette
after a theme change" hook, and `applyTheme` already calls it. A globe repaint belongs there
rather than in a new listener.

### Screenshots were not possible this session

The Browser pane is not displayed in a non-interactive session, so `computer{action:"screenshot"}`
fails with "not compositing frames". Everything above is **measurement**, not a picture. Tasks 3
and 4 ask for the globe to be shown at 1280 / 1920 / 3840 in three themes; that needs a session
with the pane visible.

---

# T6 handoff — Part 4 (the copy audit) is all that remains

| | Status | Where |
|---|---|---|
| Part F — expert reference lock | Merged | `main` @ `8c1d67a` |
| Parts A–E — the fold | Merged, browser-verified | `main` @ `dbdd261` |
| Project-creation gate, admin projects/assignment | Merged | `main` @ `dbdd261` |
| Part 3 — the compute rewrite | **Merged, proven** | `main` @ `dbdd261` |
| **Part 4 — the copy audit** | **Inventoried, not rewritten** | — |

`main` is at `dbdd261`. 843 checks across 17 suites pass. No migration is pending; the schema
stays at 0012 and `/readyz` is unaffected by anything merged since.

The false-Red defect that dominated the last two sessions is **fixed and merged**. What follows in
§1 is kept as the record of what it was, because it explains why the architecture is now what it
is. §4 is the outstanding work.

---

## 1. The defect that is now fixed (record, not a to-do)

Two computations existed for the same project. The server computed status from documents and
stored it; the legacy dashboard recomputed it in the browser. They disagreed:

| Case | CPI | Server | Legacy browser | |
|---|---|---|---|---|
| healthy | 1.05 | Green | **Red — 40 of 40 seeds** | deterministic |
| on-budget | 1.00 | Green | **Green 38 / Amber 2** | seed-dependent |
| distressed | 0.833 | Red | Red | agreed |

**Mechanism.** `LinSim.buildSignals` expects a time series; `ingest.js` never passed one, so it
fell through to `deriveSeries(metricValue, seed)` and invented one from a single value plus a
seed. That fabricated series tripped the CUSUM Anomaly Monitor. The seed derived from the project
id, so two identical projects could differ. On the healthy case the browser reported
`evm: green, mc: green, doc: green, cusum: red`, and the fusion promoted that one red to Red.

**After the rewrite, re-measured:** stored, `getProjectFusion` and `deriveHealthState` all return
Green for cpi 1.05, Green for cpi 1.00, Red for cpi 0.833. There is one computation now.

---

## 2. How Part 3 was done, and what to preserve

**Four functions, not 79 edits.** The split counted 79 call sites across eight files. Rather than
edit them, `getModuleStatus`, `getCategoryStatus` and `getProjectFusion` kept their names and
signatures and changed where the answer comes from: they read the stored `computed_results` row.
Every call site became correct without being touched.

- **`assets/js/taxonomy.js`** replaces `categories.js` on the application. The taxonomy is
  carried over unchanged, because it is data. The derivation is not.
- **`LinResults.prime(projectId, row)`** is how a stored row reaches the accessors. The loaders
  that already fetch `projectresults` call it. **The cache deliberately cannot fetch**: a module
  that could fetch would eventually fetch during a render, and a render that issues a request can
  audit an evidence view the participant never asked for. Note the row is `resp.result`, not
  `resp` — priming the envelope silently yields `undefined` statuses.
- **`deriveHealthState` has no fallback derivation.** No stored row now means "Awaiting analysis".
  Restoring a fallback would restore the defect.
- **Enforced by absence.** `index.html` loads none of `sim.js`, `simulations.js`,
  `categories.js`, `deepdive.js`. Verified by resource timing across all six page sections.

**`research/deepdive.html`** is the one surface that computes in the browser, on purpose: it
re-runs the models live to show the working. Nothing links to it, it holds no data of its own, and
every action it would call is refused server-side without the right role. It is not a security
boundary and does not claim to be — the guarantee is that no participant-facing route loads a
client-side model.

---

## 3. Verified in a browser (all merged)

| Guarantee | Result |
|---|---|
| Full workflow, no page load | Verified — `navigation` entries stayed at 1 |
| Profile once, no questionnaire nav | Verified — absent on reload and fresh sign-in |
| Nav sets | Verified — participant topbar `[]`, admin `["Admin"]`, dock identical |
| Platform theme | Verified — `radar.css` the only palette |
| No raw ULIDs | Verified — zero across every page section |
| Every field labelled | Verified — zero unlabelled fields |
| No module ids in text | Verified — zero across every page section |
| **Compute libraries absent** | **Verified — resource timing, all six sections** |
| Layout | Verified — clamps to 1280px at 1920 and 3840, no overflow |

**Known open design gap** (not a bug, and Part 3 does not address it): the decision sequence is
keyed to **assignments**, not projects. A participant can no longer create an unassigned project,
so the dead end is closed for them, but Part B's workflow is still not one continuous chain — a
participant uploads to a project and decides against an assigned scenario, and nothing links the
two.

---

## 4. PART 4 — the outstanding work

Inventoried, not rewritten. **Do not rewrite before re-reading the inventory**, and note that a
partial sweep is worse than none: half-converted spelling is more jarring than uniform British.

Run `python tools/copy_inventory.py` from the repository root to regenerate these numbers. It
separates user-facing copy from comments, which matters more than it sounds.

### Em dashes: 212 in user-facing copy

The naive repository-wide count is **1015**. The count in copy a user can read is **212**. A sweep
driven by the first number rewrites a great deal of prose nobody reads and reports success.

| Count | File | | Count | File |
|---|---|---|---|---|
| 53 | `assets/js/detail.js` | | 8 | `assets/js/store.js` |
| 30 | `assets/js/signals.js` | | 7 | `assets/js/app.js` |
| 21 | `index.html` | | 7 | `assets/js/assistant.js` |
| 16 | `assets/js/auditor.js` | | 7 | `assets/js/decision-ui.js` |
| 14 | `assets/js/workspace.js` | | 6 | `assets/js/deepdive.js` |
| 11 | `assets/js/admin.js` | | 3 each | `tests.html`, `charts3d.js`, `export.js`, `forcenet.js`, `projectnet2d.js` |
| 10 | `assets/js/admin-ops.js` | | 1–2 each | `neural_flow.js`, `documents.py`, `extraction_client.py`, `ingest.js`, `research/deepdive.html` |

### Spelling: American English, decided

Raw tally in strings is British 55 / American 162, but the headline is misleading and **two
exclusions are load-bearing**:

- **`center` (122 occurrences) is CSS and geometry**, not prose. Not a spelling decision.
- **`analyze` is an `/exec` action name** — `writes.py:441` `DEFERRED_AI_ACTIONS`, and
  `store.js:519` sends `action: "analyze"`. **Renaming it breaks the facade contract.**

Excluding those, prose leans British: `authorised` 26, `recognised` 10, `behaviour` 8,
`organisation` 4, `summarised` 1. **American English is confirmed as the convention** — GWU is the
institution and the directors work US federal and commercial projects — so roughly **55 prose
instances change**, and no technical token is touched.

### Still to do, none of it started

- The em dash sweep (212), the phrasing and redundancy pass, and the empty-state, error-message
  and confirmation-dialog review across portfolio, project detail, upload, decision sequence,
  admin, profile and expert workflow.
- **The glossary** of the platform's own terms, applied consistently.
- **The sign-in page**, the named worst offender: "authorisation" two lines from "authorized";
  "Access is restricted to authorized users only" beside a sign-in form; "Need an account, or
  forgot your password?" as one control asking two questions; copyright sitting above the access
  notice when the order should be notice, attribution, copyright.
- **The two-audience notice.** T1a built a conditional notice keyed on `account_type`. Verify it
  still works after the fold. The research variant should be protective; the operational variant
  should be accurate about responsibility without implying the platform is a toy; the
  pre-sign-in state, where account type is unknown, must keep the restrictive text.
  **Draft both variants for the researcher's review. Do not adopt liability wording, and treat
  consent text as requiring IRB approval.**

Constraints for that work: **no behavioural change**, no layout change beyond what text length
forces, and no change to a string a test asserts against without updating the test and saying so.

---

## 5. Traps and environment

- **`preview_start` resolves `launch.json` from the shell's working directory.** From `Demo` it
  starts the dead `opus-gubernatio` app on 8099 — same brand, same title. It was started twice in
  one session and stopped both times. The tell: `api.js`/`boot.js` in the sources and **zero
  `.page` sections**. **Check `preview_list`'s `cwd` before trusting any browser session.** The
  working route is `preview_start({url: "http://127.0.0.1:8010"})` attached to a server started
  separately.
- **`server/tools/dev_serve.py`** runs the real app: fills `DATABASE_URL` only if unset, defaults
  to a gitignored repo-local file, migrates to head, and seeds B7b's StubExtractor with three
  recordings (`healthy`, `on-budget`, `distressed`) written to `server/dev_fixtures/`. The
  `on-budget` fixture has earned value exactly equal to actual cost, so the pathological cpi = 1.0
  case is reproducible on demand. Never on Render's path.
- **Duplicate function declarations silently win.** `decision-ui.js` had an internal `render()`
  and an exported wrapper also named `render()`; hoisting bound the export to the wrong one and
  the decision tab threw on open. Check for name collisions when adding a module export.
- **Browser caching bit once.** After editing a JS file the page kept the old copy while the
  server served the new one. Check `String(window.LinX.fn).includes(...)` if behaviour disagrees
  with the source; a fresh tab clears it.
- **`window.confirm` auto-dismisses** in the automated browser, so `commitPreJudgment` silently
  returns. Stub it to `true` when driving the decision sequence.
- **Re-renders clear programmatically set field values.** Set and submit in the same tick.
- **Every account in every existing suite is `account_type: "operational"`** — so any gate keyed
  on `account_type` is invisible to the suite by default. That is how the project-creation gate
  initially had no coverage while the full suite passed.
- **No `DATABASE_URL` default exists** (`settings.py:69-74`). Throwaway SQLite outside the
  repository, never production. One freshly migrated database per suite. Read counts from each
  suite's own `RESULT: n/n` line, never by grepping `PASS`/`FAIL`.
- `test_simulation` exits 1 on Windows from a `charmap` error printing mu; 27/27 under
  `PYTHONIOENCODING=utf-8`. `test_decision_ui_t4` prints a line containing `FAIL` that is the
  label of its own self-test.

---

## 6. Regression

**843 checks across 17 suites, all passing**, verified after the merge to `main`.

Both changes from the 838 baseline, stated where they happened:
- `test_features` 36 → **41**: five checks covering the project-creation gate.
- `test_decision_ui_t4` holds at 73/73; its guarantee-10 scan was repointed from the deleted
  `decision.html` to `index.html` and indexed by filename rather than list position.

---

# PART A (copy) — progress, and exactly what is left

Branch `t7-copy-and-globe`. **Not merged**: Part A merges only when complete, and 84 prose em
dashes remain. 843 checks pass at every commit.

## Done

| | |
|---|---|
| `218618d` | American spelling (79 words), the sign-in page, `index.html` em dashes (17) |
| `6cf2122` | Participant-facing em dashes (25) |
| `84f74d4` | `detail.js` em dashes (35), including the assistant prompt |
| `54d7338` | `COPY_GLOSSARY.md`, and the pre-judgment commit wording |

**Spelling is finished.** 79 words, British to American, in strings only. The sweep only ever
rewrites British into American, so it cannot touch `center` (CSS) or `analyze` (an `/exec` action
name). Three tests asserted `"not authorised"` against server refusals and were updated:
`test_assignment_blinding:244`, `test_export:302`, `test_research_identity:131`. They failed
first, which is how they were found.

**The assistant was instructed to write em dashes.** `detail.js:1155` told the model to put
`' — '` on the same line as a group heading, so the platform generated them at runtime. Fixing
static strings alone would have left that in place. Worth checking for again if new prompts land.

**The conditional notice works** after the fold and the Part 3 rewrite. Verified in a browser:
research is the pre-sign-in default with operational hidden, and they swap only when
`og-account-operational` resolves. Footer order is now notice, attribution, copyright.

## Left: 84 prose em dashes

Run `python tools/copy_inventory.py`, and the classifier distinguishes prose from placeholders.
**Of the original 212, only 165 were ever prose**; the other 47 are the standalone `—` meaning
"no value" in a table cell, which must stay.

| Count | File |
|---|---|
| 24 | `assets/js/signals.js` |
| 14 | `assets/js/auditor.js` |
| 11 | `assets/js/admin.js` |
| ~11 | `assets/js/detail.js` (remainder) |
| 7 | `assets/js/assistant.js` |
| 4 | `assets/js/deepdive.js` |
| 3 each | `tests.html`, `assets/js/export.js` |
| 1–2 each | `projectnet2d.js`, `charts3d.js`, `forcenet.js`, `neural_flow.js`, `research/deepdive.html` |

These are the legacy dashboard and researcher surfaces. The participant-facing path is done.

**Method that worked:** dump the strings with the emdash script, write explicit before/after pairs
in a script, run it, re-measure. Do not apply a blanket rule. A mechanical hyphen is its own tell,
and a mechanical comma reads only slightly better; each sentence wants a specific mark.

## Also left in Part A

- Task 7 across the remaining screens: empty states, refusal messages a participant can actually
  trigger, and tooltips on portfolio, project detail, upload, admin and the expert workflow.
  The pre-judgment confirmation and "Awaiting analysis" are done.
- Apply `COPY_GLOSSARY.md` consistently. The glossary exists; the sweep that enforces it does not.

---

# PART B (globe) — investigated, not started, awaiting approval

The brief requires the library choice to be approved before building. Findings:

## 1. What exists today

**MapLibre GL 4.7.1, CDN-loaded from cdnjs**, in `assets/js/app.js` only:

- `GL_CSS_URL` / `GL_JS_URL` at `app.js:591-592`
- `loadMapLibre()` at `app.js:598` injects the tag and rejects on `onerror`
- `showMapFailure()` at `app.js:714` is the existing fallback when the CDN is blocked or offline
- markers built at `app.js:849`, popup at `app.js:905`, `hideMapCard()` at `app.js:890`
- double-clicking a marker calls `openDetail(p.id)` (`app.js:856`) — that is the existing
  selection behavior the globe must reproduce rather than replace

**There is already a graceful-degradation path.** `app.js:733` checks `typeof maplibregl ===
"undefined"` and calls `showMapFailure()`. Any globe should reuse this shape rather than invent
one, and the existing map is the natural fallback target.

## 2. Coordinates

`hasCoords(p)` at `app.js:668` already gates on `p.lat`/`p.lng` being finite, and `app.js:845`
already warns when latitude exceeds ±90 (a lat/lng ordering mistake). So **projects without
coordinates are already a handled case on the map**, and the globe inherits the same question:
they must remain listed and reachable, not silently dropped.

Geocoding is referenced in `app.js`, `ingest.js` and `server/app/models.py`. **Confirm before
building** whether geocoding actually runs at project creation on the current server path
(`projectcreate` in `workspace.py`), because the projects created during Part 3 testing had no
coordinates and still rendered in the project list.

## 3. Library recommendation, for approval

**Recommend: `globe.gl` or raw `three.js`, CDN-loaded, with the existing MapLibre map as the
fallback.** Reasoning to weigh:

- It matches the existing delivery model. MapLibre is already CDN-loaded with a working failure
  path, so the globe adds no new *kind* of risk, only another asset on the same CDN.
- The repository has been bitten twice by dependency availability, so **vendoring the library
  into `assets/vendor/` is the safer option** and I would lean that way despite the size: it
  removes the CDN from the critical path entirely and makes the fallback about WebGL only.
- Fallback chain: WebGL unavailable or library fails → render the existing MapLibre map →
  MapLibre also unavailable → the plain project list. No blank panel at any step.
- Performance constraints from the brief are real on a single small instance: do not block page
  load, stop the animation loop when the tab is hidden or the view is left, and release the WebGL
  context on teardown. `hideMapCard()` and the existing view-switch are where that hooks in.

**Decide before I build:** vendored or CDN, and `globe.gl` or `three.js` directly.

Nothing in Part B has been written.

---

# T8 — geocoding, vendoring, and the globe

Branch `t8-geocode-globe`, **not merged**. `main` is at `c17e4fd`. 854 checks across 17 suites
pass at every commit. No migration anywhere in this branch.

| Stage | Status |
|---|---|
| Server-side geocoding (Nominatim) | Done, tested, live-verified |
| Near-miss handling (`Matched to:`) | Done, browser-verified |
| Stage 1 — vendor MapLibre | Done, verified served |
| Stage 2 — verify the four insertions | Done, found and fixed a colour bug |
| Stage 3 — vendor globe.gl | Done, verified served |
| **Stage 3 — build the globe** | **NOT STARTED** |

## What was learned about Nominatim, from live calls

Response shape: always HTTP 200 with a JSON array. No match is `[]`, not a 404. A match carries
`lat`, **`lon`** (not `lng`), `display_name`, `class`, `type`, `importance`.

Verified plausible: PHL `39.87397, -75.24382`; BNA `36.11958, -86.68266`.

**Two failure modes matter more than the not-found case:**

1. **A street address and a facility name concatenated returns `[]`.** "8000 Essington Avenue,
   Philadelphia International Airport, Philadelphia, PA 19153" finds nothing, though each half
   alone resolves. The original error message advised adding city and state, which that query
   already had; it now says to try one or the other, not both.

2. **The top hit is often nearby but wrong.** "Philadelphia International Airport, Philadelphia,
   PA" returns a Hampton Inn 1.5 km away. "8000 Essington Ave" returns "Mezzogiorno", a business
   at that street number. Both are correct for the string typed and wrong for the project.

   This is why `formattedAddress` (the geocoder's `display_name`) is surfaced at create, in the
   project list, on the project page and in the admin create flow. **Do not remove it.** A blank
   map invites a fix; a pin on the wrong building signals nothing.

   Deliberately NOT solved by raising `limit` and filtering on `class`/`type`: airports resolve
   as aeroway, but a postal facility, an office fit-out or a highway package will not, and that
   filter would encode an assumption that holds for one project type and fails for the rest.

## Colour carries meaning

Stage 2 found the create confirmation rendering a **successful** match in `--status-red`, because
it reused the error slot. Fixed: `ws-note` for a match, `ws-note ws-geo-warn` (amber) for a
missing position, `ws-error` only for an actual failure. Amber rather than red for "no map
position" because the project is fine and only its position is missing.

## Stage 3 — building the globe

Everything below is investigated but unwritten.

**Dependency is in place.** `assets/vendor/globe.gl.min.js`, 1.48 MB, verified served and
exposing `window.Globe` as a function. It bundles three.js, so there is no second file and no
version-compatibility question. `assets/vendor/` totals 2.3 MB with MapLibre; both load on demand.

**Where the map lives**, all in `assets/js/app.js`:

| | |
|---|---|
| `app.js:565` | the block comment describing the map view |
| `app.js:591-592` | `GL_CSS_URL` / `GL_JS_URL`, now `assets/vendor/` |
| `app.js:598` | `loadMapAssets()`, on-demand injection with an `onerror` reject |
| `app.js:714` | `showMapFailure()` — the existing no-blank-panel path, reuse it |
| `app.js:733` | the `typeof maplibregl === "undefined"` guard |
| `app.js:849` | marker construction |
| `app.js:856` | **`openDetail(p.id)` on double-click — the selection behaviour to reproduce** |
| `app.js:890` | `hideMapCard()`, where teardown hooks in |
| `app.js:668` | `hasCoords(p)` — projects without coordinates are already a handled case |

**Data.** `workspaceprojects` already returns `address`, `formattedAddress`, `geocodeError`,
`lat`, `lng` per project. Status comes from the stored row via `getProjectFusion(p)` in
`taxonomy.js`, which reads `computed_results` and computes nothing. **The globe must not compute
a status**, and `sim.js` / `simulations.js` / `categories.js` must still not load on any
participant-facing route.

**Degradation chain, no blank panel at any step:** WebGL unavailable or `Globe` fails to load →
the existing MapLibre map → MapLibre unavailable → the plain project list. Test WebGL with a
throwaway canvas and `getContext('webgl2') || getContext('webgl')` before constructing anything.

**Lifecycle, which is where this kind of thing usually goes wrong:**
- do not block page load — load on first open of the view, as the map already does
- stop the animation loop on `document.visibilitychange` when hidden
- stop it and release the WebGL context when the view is left; `hideMapCard()` and the
  radar/globe toggle are the hooks
- guarantee 6 asks you to *demonstrate* the loop stopping, so instrument it in a way that can be
  observed from the console rather than asserted

**Projects without coordinates stay listed and reachable.** They are not dropped because they
cannot be placed. The project list already shows them with "No map position".

**Theme variables only.** No private palette, same rule as every other screen. Status colours come
from `--status-green` / `--status-amber` / `--status-red` / `--status-nodata`.

**The radar is not to be touched.** Guarantee 1 is that it renders identically before and after.

## Remaining Part A copy work, unchanged

84 prose em dashes in the legacy dashboard and researcher surfaces: `signals.js` 24, `auditor.js`
14, `admin.js` 11, `detail.js` ~11, `assistant.js` 7, then singles. The participant-facing path is
done. Method that worked: dump the strings, write explicit before/after pairs in a script, run it,
re-measure. Never a blanket rule.

## Also worth knowing

- **The browser caches edited JS** while the server serves the new file. It bit this session
  again. Check `String(window.LinX.fn).includes(...)` if behaviour disagrees with the source; a
  fresh tab clears it.
- **PDF.js and SheetJS are still CDN-loaded** at `index.html:1060` and `:1062`. The same corporate
  network that would have blocked MapLibre will block those, breaking client-side PDF extraction
  and the audit export. Not in scope for T8, but the same argument applies.
- The geocoding tests stub `app.geocode.geocode`, so the suite stays offline and never spends
  Nominatim's rate limit. Keep it that way.
