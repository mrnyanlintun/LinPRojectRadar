# Globe visual verification, off-origin vendoring, dead code

Branch `t10-globe-treatments`. `main` at `5ccc395`. 854 checks across 17 suites pass.

**Task 1 was not done. The browser pane was not visible, so nothing rendered, and the branch is
not merged.** Tasks 2 and 3 are complete and verified.

---

## 1. What I did, and what I did not

### Not done — Task 1, visual verification and merge

The session brief asked me to confirm at the start that the pane was visible and rAF firing, and
to stop rather than repeat the previous outcome if it was not. It was not:

| Check | Result |
|---|---|
| `document.visibilityState` | `"hidden"` |
| rAF frames in 1 second | **0** |
| `computer{action:"screenshot"}` | fails — "the Browser pane is not displayed, so the page is not compositing frames" |

I tried three ways before concluding: the existing tab, `tabs_select` to front it, and a brand new
tab opened by `preview_start({url})`, which reported "Browser pane opened" and still gave
`visibilityState: "hidden"` and 0 frames. A `PostToolUse` hook also reported the file "is now
visible in the Browser pane"; I re-tested on that signal and it was still hidden, so that message
does not mean the page is compositing.

globe.gl builds its scene inside the rAF loop, so with 0 frames the scene graph never populates.
That blocks **all five** parts of Task 1: seeing either treatment, judging marker legibility,
measuring frame rate, capturing the three widths, and seeing the tilt.

**I did not merge.** Merging would mean shipping two visual treatments no one has ever looked at.

### Done — Task 2, off-origin dependencies

- **Google Fonts: vendored.** 18 woff2 files (Archivo 500/700/800, Inter 400/500/600, IBM Plex
  Mono 400/500/600) plus a generated `assets/vendor/fonts.css`, all same-origin. Latin and
  latin-ext only.
- **`tiles.openfreemap.org`: reported, not vendorable.** Degradation path verified live.
- **`accounts.google.com`: reported, not removable.** Password path verified live with the Google
  global absent.

### Done — Task 3, dead code

Removed the `querySelectorAll('[data-set-theme]')` sweep from `applyTheme`, replaced by a comment
naming `openThemeFlyout()` as the real switcher and recording that the dead selector is what led a
previous session to report the switcher missing.

### Found and fixed, not part of the task — see §5

A dev-server cache gap that was actively hiding my own font change.

---

## 2. Guarantees

| # | Guarantee | Status |
|---|---|---|
| 1 | NYC abstract, Miami/Maria photographic | **Verified by measurement only.** Treatment, texture URL, 177 hex polygons, halo counts and atmosphere all switch correctly through the real buttons. **Never seen rendering.** |
| 2 | Four statuses legible on both photographic themes over terrain, ocean, cloud | **NOT MET.** The contrast arithmetic passes (below) but this is an analytic argument, not evidence. It has not been looked at. |
| 3 | Status colours unchanged across themes | **Verified by measurement.** Byte-identical on all three. |
| 4 | Theme switch updates the globe without reload, both directions | **Verified by measurement.** `liveCount` steady at 1 across every switch — a repaint, never a remount. |
| 5 | Nothing loads from a CDN | **Verified by measurement, now materially better.** Google Fonts eliminated. Only `accounts.google.com` remains on the sign-in page, plus `tiles.openfreemap.org` if the map is opened. Both justified in §1 and neither is vendorable. |
| 6 | Previously proven behaviour still holds | **Partly.** Empty state (0 points, autoRotate 0.35), teardown, treatment switching and `rgba()` freedom re-verified by measurement. **Tilt not seen** — `palette()` returns `tiltDeg: null` under a hidden pane because the group is never built. |
| 7 | Frame rate measured on both treatments | **NOT MET.** Impossible at 0 fps. |

---

## 3. Frame rate

**Not measured. 0 rAF frames per second — there was no frame rate to measure.**

I am not going to estimate it. The hex-dot resolution is still 3, still chosen conservatively
without measurement, and the question of whether there is headroom to raise it is still open.

---

## 4. Screenshots

**None. Screenshot capture fails in this environment** with "the Browser pane is not displayed,
so the page is not compositing frames." No image files accompany this report.

---

## 5. Found along the way, not part of the task

**A dev-server cache gap that was hiding my own change, and would have hidden the next one.**

After editing `index.html` to use the vendored fonts, the browser kept loading
`fonts.googleapis.com`. The served bytes matched disk, so this was the cache trap the handoff
already documents — but with a new cause worth recording.

`dev_serve.py` set `Cache-Control: no-store` for paths starting `/assets` **or ending `.html`**.
`index.html` served at `/` matches neither. Confirmed directly: `cache-control` was `null` on the
root document while every asset had `no-store`.

Fixed by also keying on the response content type, so any `text/html` response is covered. Now
verified: `cache-control: no-store, must-revalidate` on `/`. This is dev-only; Render runs uvicorn
directly and never imports the module.

**Two smaller observations:**

- The stage buttons on the portfolio are now `Radar` and `Globe` — there is no user-facing Map
  button. The MapLibre map is reachable as the globe's WebGL-off fallback rather than as a stage a
  user picks. That makes `tiles.openfreemap.org` a fallback-of-a-fallback, which lowers its
  priority, but it is also why its failure path mattered enough to verify.
- Only **4 of the 18** vendored font files actually transfer on the sign-in page (142 KB), because
  the `unicode-range` declarations were preserved. The latin-ext faces are fetched only if a page
  actually uses those characters.

---

## 6. What the next session needs to know

**The one thing that matters: get the pane visible, then do Task 1.** Everything else is ready.

1. Confirm `document.visibilityState === "visible"` and rAF > 0 **before anything else**. If it is
   hidden, stop — two sessions have now been spent discovering this late.
2. Then: look at both treatments, judge the halo over ocean / light terrain / cloud, measure fps on
   each, capture 1280 / 1920 / 3840 in all three themes, confirm the 23.4° tilt.
3. If the abstract globe is expensive, lower `hexPolygonResolution` from 3 or raise
   `hexPolygonMargin`. If there is headroom, raise the resolution and report the cost.

**Do not re-derive these — they are settled and measured:**

- The tilt is correct at `fe4f59b`. `palette()` returning `tiltDeg: null` while the pane is hidden
  is expected, not a regression.
- **Do not "fix" marker legibility by dimming the texture.** It was measured and it does not work:
  worst case 1.02:1 undimmed (Yellow over Sahara), 1.01:1 dimmed (Red over dark sand). Dimming
  moves which status fails. That is why the dark halo exists and why the texture ships undimmed.
- Theme mapping: Miami → `light`, NYC → `newyork`, Maria → `maria`; `dark` (Gotham) is unused.
- A scene walk over the abstract globe enumerates thousands of hex objects and will time the tool
  out. Keep probes shallow, and keep sleeps well under the 30-second tool cap.

**Marker contrast, for reference when judging it by eye** — against the halo `#05080b`: Red 4.9,
Amber 7.5, Green 10.5, Yellow 13.4. All clear 3:1. The numbers are not the question; whether it
*looks* right is.

---

## Regression

854 checks across 17 suites, unchanged.

| Suite | | Suite | |
|---|---|---|---|
| `test_admin_ops_t7t8` | 59/59 | `test_membership` | 46/46 |
| `test_assignment_blinding` | 44/44 | `test_pre_lock_guard` | 20/20 |
| `test_auth_session` | 52/52 | `test_research_identity` | 41/41 |
| `test_decision_sequence` | 60/60 | `test_simulation` | 27/27 |
| `test_decision_ui_t4` | 73/73 | `test_transitions` | 58/58 |
| `test_documents_b7b` | 66/66 | `test_workspace_t3t5` | 50/50 |
| `test_drive_import` | 37/37 | `test_writes_a1b` | 57/57 |
| `test_expert_reference_t6` | 59/59 | `test_export` | 64/64 |
| `test_features` | 41/41 | | |

Each suite gets its own freshly migrated throwaway SQLite in the scratchpad, per `T6_HANDOFF.md`.

## Vendor total

**4.5 MB → 5.9 MB.** The globe added 769 KB last session (texture 529 KB, GeoJSON 240 KB); the
fonts add 679 KB this session. Sources and licences in `assets/vendor/ASSETS.md`.
