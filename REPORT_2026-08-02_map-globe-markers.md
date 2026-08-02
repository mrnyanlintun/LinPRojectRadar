# Projects missing from the Map and the Globe — 2026-08-02

**1013 checks across 21 suites pass. `tests_render.html` is 33/33, up from 26.**

---

## The cause

**`hydrate()` in `assets/js/store.js` read a field's absence from the slim projection as that
field's deletion.**

`facade.slim_row()` is a thirteen-field projection: id, name, sector, status, updatedAt, cpi,
spi, docRiskScore, actualPctComplete, simModuleCount, docCount, slim. It carries **nothing about
location** — no `lat`, no `lng`, no `address`, no `formattedAddress`, no `geocodeError`. It
cannot: those fields are not in its shape.

The geographic views know this. `hydrateProjectsForGeo()` in `app.js` exists precisely to swap
slim rows for full project JSON so that coordinates are present before the Map or the Globe
draws. That worked.

What then happened is that **every subsequent background portfolio refresh threw the coordinates
away again.** `loadSlim()` re-fetches the slim list and calls `hydrate()`, which reconciles each
incoming row against the local copy by grafting a **fixed allowlist** of client-built fields —
`simulationSignals`, `signals`, `signalInputs`, `status`, `history`, `milestoneHistory`,
`_localComputedAt` — and taking the incoming row for everything else. Location is not on that
list, so the hydrated coordinates were dropped and the in-memory mirror the views read went back
to having no positions.

`refreshPortfolio()` calls `loadSlim()` after **create, rename, archive, restore and
recompute-all**. So creating a second project silently un-placed the first.

Both views then behaved correctly on the data they were handed. They had nothing to place.

### The second, independent defect

`hydrateProjectsForGeo()` guarded itself with a single boolean, `mapHydrated`, latched on the
first geographic open. Once the coordinates had been stripped, **nothing ever re-fetched them**,
so the views stayed empty for the rest of the session until a page reload. The same latch also
means a geographic view opened before the portfolio had loaded latched with nothing fetched and
never tried again.

The two compound into the observed symptom: the Map works on first load, and is permanently
empty after the first thing the user does.

### Measured, before the fix

Seeded five projects — three geocoded, one whose address failed to geocode, one with no address —
and drove the real application in a real browser against a real server:

| | placed | markers drawn | note shown |
|---|---|---|---|
| first open of Map | 3 | 3 | "3 project(s) placed. 2 have no location yet…" |
| after one portfolio refresh | **0** | 3 (stale DOM) | unchanged until redraw |
| re-open Map | **0** | **0** | **"0 project(s) placed. 5 have no location yet…"** |

## Which projects

**Every project that has coordinates, uniformly.** Nothing about a project distinguishes an
affected one from an unaffected one — not how it was created, not whether it was analysed, not
its status. The distinguishing factor is **when you look**: before or after the first
portfolio-refreshing action in that browser session. A project with no coordinates was never
affected, because it had nothing to lose.

This is why `statusColorFor` and `proxyHealth` were not the cause. Both were checked: neither
skips a marker. The atlas draws one marker per project whose `lat`/`lng` are finite and in range,
resolves the fill through a `var()` that falls back to `--status-nodata`, and an unresolvable
status costs the marker its **letter**, never its **dot**. A project awaiting analysis places
exactly as well as an analysed one — verified with all five seeded projects unanalysed.

## What was not the cause, established rather than assumed

1. **The projects do have coordinates.** Geocoding runs server-side on create
   (`workspace.a_projectcreate`) and on an address change (`writes.w_save`), and
   `geocode.apply_to_doc` writes `lat`/`lng`/`formattedAddress` into the project document.
   Measured stored values for three seeded addresses.
2. **A failed geocode is not silent.** It clears the coordinate fields rather than leaving them
   stale and stores `geocodeError`, which `projectcreate` and `workspaceprojects` both return,
   and the atlas note counts the project under "have no location yet". *(Nominatim is unreachable
   from this container, so the geocoder itself was stubbed exactly as the existing suite stubs
   it; the failure **paths** were exercised, live geocoding was not.)*
3. **The API returns them.** `?action=get&id=…` returns the full document including `lat`/`lng`.
   That endpoint was never the problem — it is what `hydrateProjectsForGeo()` calls, successfully.
4. **It is not the view rather than the data.** The Globe genuinely mounted here:
   `LinGlobe.mount()` returned `{ok: true, points: 3, unplaceable: 2}`, `liveCount()` 1, one
   canvas, and the watchdog stood down rather than falling back — so the Globe was drawing, not
   the atlas standing in for it.
5. **The Radar is unaffected**, and was checked rather than assumed. It places by status, not by
   position, and rendered all five projects throughout.

## The fix

Both at root, in the two places that were actually wrong.

**`assets/js/store.js` — a projection cannot express deletion.** For a row carrying `slim: true`,
`hydrate()` now carries forward **every key the local copy has that the incoming row does not**.
Deliberately general rather than "also graft lat and lng": this was already fixed once as an
allowlist, and an allowlist only ever covers the fields somebody remembered. Confined to slim
rows — a **full** row omitting a field is a real deletion (clearing an address server-side does
drop `lat`/`lng`, and that must reach the client), so full rows still replace.

**`assets/js/app.js` — the latch is now a set of ids, not a boolean.** Work is still done at most
once per project per session, but a project that arrives later is no longer locked out of ever
being placed, and a failed fetch is retried on the next open instead of being remembered as done.

### After the fix, same measurement

| | placed | markers |
|---|---|---|
| first open of Map | 3 | 3 |
| after a portfolio refresh | 3 | 3 |
| re-open Map | 3 | 3 |
| Globe, after a portfolio refresh | 3 | `points: 3, unplaceable: 2` |

## The check that fails if it regresses

**`tests_render.html` group 8, seven assertions, 26 → 33.**

It is deliberately in two halves. Three assertions cover the **render site**: a project with
coordinates produces a marker, every located project produces one, and an unplaceable project
produces none without stopping the rest. Four cover the **round trip**: after
`hydratePortfolio()` is handed the real slim projection for those same projects, the coordinates
and the matched address survive, the slim row's own fields still win, and the located projects
**still produce markers**.

**Proven able to fail by reverting the fix.** With `graftUnmodelledFields` made a no-op — the
exact prior behaviour — the run is 30/33:

```
FAIL  refresh: a slim row does not strip coordinates off a located project   expected=2 actual=0
FAIL  refresh: the matched address survives too                     expected=Somewhere, USA actual=undefined
FAIL  refresh: a located project STILL produces a marker after a portfolio refresh  expected=2 actual=0
```

**The three render-site assertions stayed GREEN through that revert**, which is the point worth
keeping: a check written only at the render site would have passed through the entire defect,
because the render site was never wrong.

## Not covered by a test, stated rather than left implicit

The `app.js` latch fix has **no automated check**. `hydrateProjectsForGeo()` is not exported and
its failure mode is a browser lifecycle ordering, not a pure function. It was verified by driving
the real application; it is not defended against regression. Making it testable would mean
exporting it, which is a change to the module's surface and was not made as a side effect of this
task.

## Environment note, for whoever reads the handoff's warning

**The browser pane warning did not apply to this session.** There is no `preview_start` tooling
in this container at all; the app was driven with the pre-installed Chromium through Playwright,
which composites. `document.visibilityState` was `"visible"` and `requestAnimationFrame` produced
frames (~6/s under software WebGL — slow, but non-zero), which is why the Globe could be checked
here rather than only measured. Nominatim is not reachable through the proxy, so live geocoding
could not be exercised and was stubbed.

## No data was changed

The cause was a render-path defect, not missing or failed geocoding, so the instruction to stop
before backfilling did not come into play. Nothing was backfilled, recomputed or migrated.
Production was not inspected or queried. All work was against a local throwaway SQLite.
