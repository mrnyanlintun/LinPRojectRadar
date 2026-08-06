# Map and globe move to the selected project

**Date:** 2026-08-05
**Branch:** `claude/map-flyto-s5s90m` (merged to `main`, PR #218, merge commit `00d0da4`)
**Model:** Sonnet

## Could the globe be moved? Yes, with no new dependency.

The globe uses `globe.gl` (Three.js + OrbitControls underneath), already vendored. It exposes
`pointOfView()`, which the codebase previously called only once, at mount, for the single-project
detail globe. Wrapping it in `focus(lat, lng)` / `resetView()` moves the camera to the selected
project and back to the portfolio-wide view. **No dependency was added, and none was needed.** The
deferral noted in PR #215 was specifically about visible +/- zoom buttons (which would need DOM
injection into the renderer container); a camera move needs none of that.

## Stale premise in the brief, corrected

The brief described wiring MapLibre GL (`glMap`, from PR #215) as the map camera. That premise was
already stale: a later merged commit (#216, `ebc5493`) orphaned the entire MapLibre path. The "Map"
stage button now renders the flat SVG atlas (`assets/js/atlas.js`), and `app.js` carries an explicit
comment against reviving MapLibre: *"do not 'fix' it back into service by wiring a caller."*

MapLibre was therefore left untouched, and the camera move was implemented against the two surfaces
that are actually live today: the SVG atlas and the globe.

## What moved

- **Atlas** (`assets/js/atlas.js`) — new `LinAtlas.focus(host, project)` / `resetView(host)` animate
  the SVG `viewBox` (requestAnimationFrame tween, 700ms ease, instant under reduced-motion) from the
  full world frame down to a tenth-frame window centred on the selected project, so the project
  reads as a place, not a continent. No dependency.
- **Globe** (`assets/js/globe.js`) — new `handle.focus(lat, lng)` / `resetView()` wrap globe.gl's
  vendored `pointOfView()`. `resetView()` returns to the exact `pointOfView()` captured at mount. No
  dependency.
- **Wiring** (`assets/js/app.js`) — `maybeFlyToSelection()` moves whichever view is active;
  `selectProject()` with a falsy or unresolvable id is treated as a deselect and returns both views
  to the portfolio-wide view; the project-list row now toggles select/deselect on re-click (the
  concrete UI path that exercises deselect — nothing called `selectProject(null)` before).

## The two correctness requirements

1. **A project with no coordinates** leaves the camera untouched and throws nothing. Guarded in both
   `LinAtlas.focus()` and `focusGlobeProject()` — an absent lat/lon returns early, so the viewer
   stays exactly where it was.
2. **Deselecting, or selecting nothing,** returns to the portfolio-wide view rather than stranding
   the viewer at the last project. Implemented once, in `selectProject()`, so both views reset
   through the same path.

## Verification

A Playwright harness (not committed) drove the real DOM + `app.js` + `atlas.js` against a faked
`LinGlobe`. Real globe.gl needs a compositing browser that this container's headless Chromium lacks
— the same limitation the codebase's own globe notes already document — so the globe camera contract
(`focus`/`resetView` called with the right arguments, guarded on missing coordinates) was asserted
against the fake, while the atlas viewBox move was driven for real.

12/12 checks green. Every check was proven able to fail: stubbing `LinAtlas.focus()` to a no-op
turned 2 checks red (reverted); stubbing `focusGlobeProject()` turned 1 check red (reverted);
12/12 confirmed again after each revert. Faults targeted block elements and anchored matches.

- **Server suite:** 39 suites, 2200/2200, fresh DB per file. No server file changed.
- **`tests.html`:** 51/51.
- **`tests_render.html`:** 117/118 — the one FAIL is the pre-existing auth-gated production-read
  check, red on `main` too.

## Files changed

`assets/js/atlas.js`, `assets/js/globe.js`, `assets/js/app.js`, `T6_HANDOFF.md`.
No `server/` change; nothing under `server/app/simulation/` touched.

## Note on the globe verification limitation

The globe's camera move is wired to the vendored `pointOfView()` and guarded, and its contract is
asserted against a fake, but it was not driven end to end in a real compositing browser in this
container. A visual confirmation on a compositing browser is the one check this environment could
not perform; the codebase's existing globe notes document the same headless limitation.
