# A non-WebGL geographic view, and the globe demoted

Branch `t10-globe-treatments`. 854 checks across 17 suites pass.

**All eight guarantees hold and are verified.** The pane still does not composite, but that no
longer blocks anything: the whole point of this change is a view that renders without a frame, and
that property is directly measurable.

---

## 1. What I did

**A new flat map, `assets/js/atlas.js` (~9 KB), is the default geographic view.** SVG, no WebGL, no
3D library, no animation loop, no new downloads — it draws the country geometry already vendored
for the globe.

**SVG rather than canvas**, chosen for the thing this change is about: every mark is a DOM node the
instant `render()` returns, so the drawing is inspectable without a compositor, stays crisp at any
width without redrawing, and follows the theme through the CSS cascade with no JavaScript at all.

**Equirectangular projection**, chosen over Natural Earth for a reason that outweighs how the
coastlines read: it is linear, so a marker sits at exactly `(lon+180)/360` and `(90-lat)/180` of
the frame and a misplaced pin cannot be blamed on the projection. It is also the projection the
source data is already in. Verified arithmetically — London (51.5, −0.1) lands at x=499.72 against
a frame half-width of 500; Sydney (−33.9, 151.2) at x=920.00, y=344.17.

**The globe is kept and demoted.** It is a third stage button. Its assets load only when selected.
If WebGL is missing, or the mount fails, **or the scene has not actually been built within 4
seconds**, it falls back to the atlas.

That watchdog is the substantive addition. `mount()` resolving is *not* the same as the globe
drawing — globe.gl assembles its scene inside the animation loop, so on a machine where that loop
does not run, `mount()` resolves `ok` and the panel stays black. That is precisely the
"black sphere in front of a director" risk. `LinGlobe` now exposes `hasScene()`, and the watchdog
asks it rather than trusting the resolve.

**Project detail's Location section uses the atlas too**, with the project's own marker emphasised.

**The MapLibre background warm-up is gone.** It used to fetch maplibre-gl (773 KB + 64 KB CSS) and
open a connection to `tiles.openfreemap.org` on idle, on the default path, for a view nobody had
asked for. It was the single largest reason the default path touched an off-origin host.

## What I did not do

**I did not delete MapLibre.** It is now unreachable from any user path — see §4. Removing it
touches ~400 lines, two vendored files (837 KB), the CSP and the map markup; that is its own change
with its own verification burden. It is inert where it stands and costs the default path nothing.
I marked the block clearly as orphaned so nobody wires a caller back to it.

**I did not commit an image file.** See §3.

---

## 2. Guarantees

| # | Guarantee | Status |
|---|---|---|
| 1 | Default view renders without WebGL and without a compositing browser | **VERIFIED.** 177 country paths, 4 markers, 215 nodes, rendered in 11 ms with **`rafFramesDuringRender: 0`** and `visibilityState: "hidden"`. Also verified at the pixel level — see §3. |
| 2 | Points at geocoded positions, status from the stored row | **VERIFIED.** Projection checked arithmetically (above). Status comes from `getProjectFusion()`; a project with no stored row renders `--status-nodata` and the title "Awaiting analysis" — nothing is derived here. |
| 3 | All four statuses legible against the map background | **VERIFIED by measurement.** Figures below. |
| 4 | Theme switching updates the view without a reload | **VERIFIED.** Driven through the real theme pills: ocean `rgb(14,48,73)` → `rgb(11,17,22)` → back, land likewise, with marker and country counts unchanged — a cascade repaint, not a re-render. |
| 5 | Selecting a point opens project detail via the existing path | **VERIFIED.** Clicking a marker moved the visible page from `portfolio` to `detail` for `PRJ-D17HNYWDFA`, through `openDetail`. Markers are `tabindex="0"`, `role="button"`, and respond to Enter/Space. |
| 6 | Unplaced projects listed and reachable, count shown | **VERIFIED.** A 5-project probe with one lacking coordinates returned `{placed: 4, unplaced: 1}`, and the note reads "N project(s) placed. 1 have no location yet and are listed below." |
| 7 | Globe assets do not load unless the globe is selected | **VERIFIED by resource timing.** On the default path: `globe.gl`, `earth-blue-marble-clouds.jpg`, `maplibre-gl` → **NONE**. On clicking Globe, all three appear. |
| 8 | Nothing loads off-origin on the default path | **VERIFIED, with one known exception.** MapLibre and `tiles.openfreemap.org` are gone. The only remaining off-origin request is `accounts.google.com/gsi/client`, which is the Google sign-in script loaded once at page load — pre-existing, required, and confirmed last session not to lock anyone out when blocked. See §5. |

### Guarantee 3 — the contrast figures, and why the halo exists

Every marker sits on a dark disc (`--atlas-marker-halo`, `#05080b`), the same treatment the globe
uses. Measured WCAG ratios:

| Status | vs halo (all themes) | vs Miami/Maria land | vs Miami/Maria ocean | vs NYC land |
|---|---|---|---|---|
| Green | **12.09** | 1.26 | 8.22 | 9.67 |
| Yellow | **15.40** | **1.01** | 10.47 | 12.31 |
| Amber | **8.62** | 1.76 | 5.86 | 6.89 |
| Red | **5.66** | 2.68 | 3.85 | 4.53 |

The middle column is the point. **Without the halo, Yellow on the pale land of Miami and Maria is
1.01:1 — invisible.** With it, every status is ≥5.66:1 in every theme, because contrast becomes a
property of the marker's own surround rather than of what is behind it. Status colours are
untouched; a Red project is `#ff3b30` on every theme.

The ring is 2.4 units of a 1000-unit frame — about **2.8 CSS px** at the 1183 px render width.
Each marker also carries the platform's existing colour-blind-safe letter (G/Y/A/R/C from
`config.js`), inked by luminance: light `#f5f8ff` on Red, dark `#0b1220` on the rest.

---

## 3. Proof it renders without a frame

**Structural.** `LinAtlas.stats()` on the live default view: `{countries: 177, markers: 1,
halos: 1, nodes: 203}`. A fresh probe render with five projects: `{countries: 177, markers: 4,
halos: 4, nodes: 215}`, `renderMs: 11`, and **`rafFramesDuringRender: 0`** while
`document.visibilityState === "hidden"`. First country path `d` attribute is 967 characters of
real geometry.

**Pixel.** The rendered SVG was serialised with its computed fills inlined, rasterised through a
blob URL into a 1000×500 canvas, and sampled with `getImageData` — all of which works without
compositing:

| Sample | Read | Expected |
|---|---|---|
| Marker centre (291, 139) | `#26344f` | `--status-nodata` `#26344f` ✓ |
| Halo ring at ±6 px | `#05080b` | `--atlas-marker-halo` `#05080b` ✓ |
| Just outside halo (+9 px) | `#0e3049` | `--atlas-ocean` `#0e3049` ✓ |
| Sahara (530, 180) | `#cfe3ef` | `--atlas-land` `#cfe3ef` ✓ |
| Amazon (330, 290) | `#cfe3ef` | `--atlas-land` ✓ |

That is the marker's full structure — status dot, dark ring, ocean beyond — confirmed as actual
rasterised pixels, not as an argument.

One thing worth recording so it is not mistaken for a defect: ocean samples taken at y=250 read
`#1f3f56` rather than `#0e3049`. y=250 **is** the equator graticule line, and the graticule is
white at 14% opacity. The arithmetic is consistent.

**Widths.** SVG box 1183×592 at 1280, 1238×619 at 1920 and 3840 (clamped by the existing 1280
container), no horizontal overflow at any width, identical node counts — it scales rather than
redraws.

**No image file is committed.** Screenshot capture fails in this environment, and there is no path
to write browser-held bytes to disk without moving ~170 KB of serialised SVG through the session.
The pixel sampling above is offered instead, and it is evidence rather than an argument, but it is
not a picture and I am not going to present it as one. Nobody has *looked* at this map.

---

## 4. Is MapLibre still needed? No.

After this change nothing routes to it:

- `scheduleMapWarmup()` — its only caller was the startup path, now removed. **No callers.**
- `buildMap()` — reachable only from `if (mapBuilt) buildMap()`, and `mapBuilt` is set nowhere but
  inside `buildMap()` itself. **Unreachable.**
- `showMapInstead()` — replaced by `showAtlasInstead()`.

`maplibre-gl.min.js` (773 KB) and `maplibre-gl.min.css` (64 KB) are still vendored but never
fetched. Removing them, the map markup, the `map-wrap` stage and the `connect-src` CSP entry for
`tiles.openfreemap.org` would be a clean follow-up worth about 837 KB of vendored weight.

---

## 5. Found along the way

- **The globe watchdog fired for real, and the fallback worked.** Selecting Globe in this
  non-compositing browser loaded all three globe assets, never built a scene, and after 4 seconds
  hid the globe, released the WebGL context (`liveCount` 0) and showed the atlas with its note
  intact. That is the exact failure mode this change was commissioned to prevent, demonstrated
  end to end rather than reasoned about.
- **A persisted `"globe"` preference survives from earlier sessions.** Anyone who selected Globe
  before will still land on it, hit the watchdog, and be shown the atlas. Correct behaviour, but it
  means "the default is Map" is only true for a user with no stored preference — worth knowing
  before reading a demo as broken.
- **`accounts.google.com/gsi/client` is still unconditional.** It loads on every page load,
  including for an already-signed-in user who will never use it. Deferring it until the sign-in
  form is actually shown would make the authenticated default path genuinely zero off-origin. Not
  done here — it touches the auth path and deserves its own change.

---

## 6. For the next session

1. **Look at the map.** Everything above is measured and none of it is a picture. The projection,
   colours and marker structure are confirmed numerically and at pixel level; whether it *reads*
   well — coastline weight, marker size, graticule strength — has not been judged by eye.
2. The globe is unchanged and still unseen. Its verification checklist is in the previous report.
3. Deleting MapLibre is queued and scoped in §4.
4. The pane check at the top of `T6_HANDOFF.md` still applies to any globe work. It no longer
   blocks the default view, which is the change.

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

Each suite gets its own freshly migrated throwaway SQLite in the scratchpad.
