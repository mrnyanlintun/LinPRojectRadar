# Map and globe zoom, verified for real, and the one real bug that was there

**Date:** 2026-08-05
**Branch:** `claude/map-zoom-real-s5s90m` (merged to `main`, commit `914f46a`)
**Model:** Sonnet

## The cause, stated plainly

The prior session's globe check ran against a faked `LinGlobe`, believing real globe.gl "needs a
compositing browser this container's headless Chromium lacks." **That premise was false.** Launched
with `--use-gl=swiftshader --enable-webgl --ignore-gpu-blocklist`, this container's Chromium
composites WebGL and runs globe.gl's real animation loop (confirmed: `hasScene()` true, the real
`pointOfView()` readable and drivable).

Driving the real globe: the camera **did** move on selection, but it overshot and drifted about
4.7 degrees west of the target over roughly the next eight seconds before settling. The cause:
OrbitControls' default `enableDamping` — never touched by `globe.js` — read the direct
`pointOfView()` tween as user input and kept applying inertia after the tween had finished. A real,
previously unverified bug, distinct from anything the prior report described.

The atlas and its `app.js` wiring had **no defect**: the selection handler is reached on the real
click path, mutates the one live `.atlas-svg`'s `viewBox`, and there is a single `portfolioGlobe`
reference with no race on scene-readiness. The candidate causes named in the task brief (dead click
path, wrong DOM element, race condition) were tested for real and ruled out for the atlas.

**`#215`'s `NavigationControl` fix is confirmed dead code.** `#216` orphaned `glMap`/MapLibre
entirely in favour of the flat SVG atlas as the "Map" stage; no live path constructs `glMap` since.
That earlier fix has never done anything on the live site. Left untouched — reviving MapLibre is an
owner decision, not a mechanical fix, and is out of scope here.

## What changed

One line in `assets/js/globe.js`: `controls.enableDamping = false` at mount, alongside the existing
`autoRotate` settings. No changes were needed to `app.js` or `atlas.js` — both were already correct.

## Correctness requirements, reverified against real state

1. **No coordinates:** seeded a real no-coordinate project, selected it after a coordinate project
   was already focused — neither the atlas's `viewBox` nor the globe's `pointOfView()` changed, and
   no console errors were raised.
2. **Deselect:** returns the atlas to `0 0 1000 500` and the globe to its mount-time
   `pointOfView()`.

## Which viewer was observed moving for real

**Both** — this is the point of the task, and neither was asserted against a stub.

- **Atlas:** `viewBox` read live off the actual DOM element rendering it.
- **Globe:** `pointOfView()` read live off the real globe.gl instance
  (`LinApp.getPortfolioGlobe().globe`), driven with real WebGL compositing via the Chromium flags
  above.

Both were fault-injected and confirmed able to fail: commenting out the damping fix reintroduced the
drift and the globe check went red; a `return` inserted at the top of `LinAtlas.focus()` made the
atlas check go red. Both reverted to green afterward.

**No manual owner confirmation is required for the globe** — this environment can verify it directly
once the correct browser flags are used; that was the actual gap in the prior session, not an
inherent limitation of the container.

## Likely explanation for the live report

If the owner's live projects were never successfully geocoded (no stored `lat`/`lng`), both
`focus()` functions correctly no-op by design — the same behaviour required for the "no coordinates"
correctness requirement, and indistinguishable from broken fly-to code to a viewer. **Worth checking
the live deployment's project records for missing coordinates** before assuming the fix in this
session didn't take.

## Verification

- **Server suite:** 39/39 files, fresh SQLite DB per file. No server file changed.
- **`tests.html`:** 51/51.
- **`tests_render.html`:** 117/118 — the one FAIL is the pre-existing auth-gated production-read
  check, red on `main` too.

## Files changed

`assets/js/globe.js`, `T6_HANDOFF.md`. No `server/` change; nothing under `server/app/simulation/`
touched.
