# The globe restored, and the portfolio map moved to Google

Date: 2026-08-10

---

## 1. Which commit broke the globe, and how

**The breaking commit is `bf2a2e9`** — *"Google Maps on the detail page, MapLibre removed, and a
site-wide copy sweep"*, the immediately preceding session's work. It was the MapLibre removal, not
the copy sweep or the ledger's module counting.

The exact fault: that commit removed `const mapWrap = document.querySelector(".map-wrap");` from
`setPortfolioView` in `app.js` (the `.map-wrap` element was part of the deleted MapLibre stage) but
left the call at the end of the same function still passing it:

```js
buildGeoStage(globeWrap, mapWrap, atlasWrap);   // mapWrap was no longer declared
```

`app.js` runs under `"use strict"`, so **reading the undeclared `mapWrap` threw a `ReferenceError`
before `buildGeoStage` was ever called.** The throw happened only on the `globe` branch — the
`map` and `radar` branches did not reference `mapWrap` — which is exactly why the Map view kept
working while the Globe view went blank. On load the default view is `globe`, so it threw
immediately and the panel stayed empty in every theme.

Reproduced before fixing: driving the real portfolio (seeded, signed-in) and clicking **Globe**
produced `globeWrapHidden: true`, `canvasCount: 0`, and the console error **`mapWrap is not
defined`**. After the fix the globe mounts a sized canvas in both themes; reintroducing the stray
`mapWrap` blanks it again and re-throws (fault-proven, §5).

The fix removes the stray argument and the now-single-argument `buildGeoStage(globeWrap)`. A
server-suite check (§5, section 3c) now fails if any standalone `mapWrap` token reappears in
`app.js`, and its self-test proves that guard both fires on the bug and does **not** fire on the
real variable `gmapWrap`.

---

## 2. The portfolio Map view is Google Maps, and the atlas is removed

There is now **one map implementation on the site**. The plumbing — the `/mapconfig` fetch, the
on-demand API loader, and the status-colour resolver — was extracted into a shared module
`assets/js/gmap.js` (`window.LinGMap`) that **both** the project detail street map and the
portfolio Map view use. Same environment key (`GOOGLE_MAPS_BROWSER_KEY`), same loader, same no-key
answer.

The portfolio Map view (`buildGoogleMapStage` / `renderPortfolioGoogleMap` in `app.js`):

- **One marker per placed project**, carrying the status colour and letter it carries elsewhere
  (Complete/Green/Yellow/Amber/Red and the awaiting state), resolved from the live theme so the
  markers recolour with a theme switch. Selecting a marker opens that project's detail view, which
  is what selecting a map marker has always done.
- **Frames the projects** with `fitBounds` (a portfolio, not one site); a single project gets a
  city zoom rather than the maximum. **Selecting a project in the list moves the map to it**
  (`panTo`), the same contract the globe's focus keeps.
- **Projects without coordinates stay listed below**, and the note reports the placed/unplaced
  count in the exact wording the atlas note used: *"N project(s) placed. M have no location yet and
  are listed below."*
- **With no key: no request to Google**, and the note says *"The map is unavailable."* with the
  count still beneath.

**No-key behaviour is now uniform.** The detail page's no-key state was the flat atlas; it is now a
note that the map is unavailable, matching the portfolio, so the site does not carry two different
no-key behaviours. Both surfaces make no Google request without a key (verified).

### What still depends on the atlas (the answer: nothing that isn't also removed)

Before removing it, every dependency was traced:

| Depended on the atlas | Resolution |
|---|---|
| Portfolio **Map view** (`buildAtlasStage`) | Now `buildGoogleMapStage` (Google Maps). |
| **Globe degrade** fallback (`showAtlasInstead`) | Now `showMapInstead` → the Google Map (or a no-key note). |
| Detail page **no-key** fallback (`renderAtlas`) | Now `setMapUnavailable` (a note). |
| `focusAtlasProject` / `resetAtlasView` / `atlasViewActive` | Replaced by the Google-map equivalents. |
| Render harness group 8 (`LinAtlas.render`) | Rewritten to render the Google map via a stub. |
| Server suite checks (`LinAtlas.render`, `buildAtlasStage`) | Rewritten to assert the new behaviour. |

Nothing else references it, so **`assets/js/atlas.js` is deleted**, its `.atlas-wrap` markup is out
of `index.html`, its script tag is gone, and its CSS (the `.atlas-*` rules and the 22 `--atlas-*`
theme variables) is removed.

**One thing that looked like an atlas asset but is NOT, and stays:**
`assets/vendor/ne_110m_admin_0_countries.geojson` — the vendored country outlines. `globe.js`
reads it to draw the globe's continents; it was never the atlas's file. It is kept, and a check
pins that it stays on disk and that `globe.js` still references it, so a later "remove the atlas
assets" sweep cannot take it by association.

---

## 3. Was the key or its plumbing wrong?

No. The key and its plumbing are correct and unchanged from the previous session — the detail map
already rendered streets with the provisioned key, and the portfolio map now uses the same key and
the same `/mapconfig` endpoint. **Nothing new is required of the owner.** The provisioning is as
reported previously: environment variable `GOOGLE_MAPS_BROWSER_KEY`, the **Maps JavaScript API**
enabled, and an **HTTP-referrer** restriction on the key (a browser map key is public by design;
the referrer restriction is its protection, unlike the IP-restricted server-side geocoding key).
The same key now serves both map surfaces.

---

## 4. Files changed

- **New:** `assets/js/gmap.js` (shared Google Maps module), `REPORT_2026-08-10_globe-and-map.md`
- **Deleted:** `assets/js/atlas.js`
- **`assets/js/app.js`** — globe fix (stray `mapWrap` removed); portfolio Map view is Google Maps
  (`buildGoogleMapStage`, `renderPortfolioGoogleMap`, marker/focus/reset/retheme helpers); globe
  degrades to the map; atlas helpers removed; a render-test hook exposed.
- **`assets/js/detail.js`** — uses the shared `LinGMap`; no-key state is a note, not the atlas.
- **`index.html`** — `.gmap-wrap` markup replaces `.atlas-wrap`; loads `gmap.js`, not `atlas.js`;
  stage-toggle and section comments updated.
- **`assets/css/radar.css`** — `.gmap-*` and `.detail-globe--unavailable` styles; atlas rules and
  `--atlas-*` variables removed.
- **`tests_render.html`** — group 8 rewritten to a Google-map marker test; GROUP 21 no-key asserts
  the note state; loads `gmap.js`.
- **`server/tools/test_map_and_module_count.py`** — sections 2/3 updated; new section 3c guards the
  globe fix and the atlas removal; self-test for the `mapWrap` detector.

---

## 5. Verification

Every new check was proven able to fail by introducing the fault, confirming the specific check
went red, reverting, and confirming the baseline came back green.

**In a real browser (seeded, signed-in, headless Chromium with WebGL via SwiftShader):**

- **Globe renders with project points in BOTH themes** (dark and light) — the headline fix. A
  sized canvas mounts; no `mapWrap` error. Reintroducing the exact bug blanks the globe
  (`canvasCount: 0`) and re-throws `mapWrap is not defined` — fault-proven, then reverted.
- **Keyed portfolio map** (Google API stubbed, since the container cannot reach `maps.gstatic.com`):
  one marker per placed project, each with its status colour and letter (G/R…), a click handler;
  the view frames the projects (`fitBounds`); selecting a project row moves the map to it
  (`panTo`).
- **Detail map still renders Google at street zoom 17** on the project's coordinates.
- **No key, both surfaces**: the section says the map is unavailable, no map is drawn, and **no
  request to any Google host is made** (counted). Projects without coordinates throw nothing and
  stay listed with the placed/unplaced count.

**Server suite** `test_map_and_module_count.py`: **72/72**, and the whole server suite **3009/3009**
on a fresh database per file. New section 3c pins the globe fix (no stray `mapWrap`;
`buildGeoStage(globeWrap)` arity), the atlas removal (`atlas.js` deleted, no live `LinAtlas`, no
atlas markup), the shared loader (`gmap.js` builds the Maps URL exactly once), and that the globe's
geojson stays. Fault-proven: reintroducing `mapWrap` → red; resurrecting `atlas.js` → red.

**Render harness** `tests_render.html`: **286/287**. The one red — *"production read path: exercised
against the server"* — is the pre-existing group that needs a signed-in session token, which a
headless tab does not have; it is an environment gate, not a defect, and was red at HEAD too. Group
8 (Google-map markers: colour, letter, two-status colour difference, framing, marker-click wiring)
and GROUP 21 (detail no-key note) were each fault-proven — constant marker colour, dropped letter,
removed framing, and an unmarked no-key host each turned their own check red, then reverted.

**A note on the "records-a-defect-not-a-property" caution.** No committed check went red in a way
that recorded a defect this time. The one adjustment of that kind is documented: the server suite's
section 3 assertion that the portfolio "still renders its atlas" (`buildAtlasStage()`) was replaced
by "builds a Google map" (`buildGoogleMapStage()`) because the atlas is intentionally removed — a
property change, made deliberately, not a red chased into a workaround.
