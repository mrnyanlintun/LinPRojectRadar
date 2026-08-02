# The blank detail page fixed, and why the map and globe show nothing

**Driven with Playwright against the pre-installed Chromium** (`/opt/pw-browsers/chromium-1194`),
compositing proven before anything was concluded (61–62 rAF frames per second, `visibilityState`
"visible"). There is no `preview_start` tooling in this container, so the `Demo` trap could not
arise. Server: `dev_serve.py` on 8010 against a throwaway seeded `dev.db`.

**1159 checks across 22 suites, 0 failures. `tests.html` 51/51. `tests_render.html` 37/37**, up
from 33 by the four new render-path checks, every one proven able to fail.

---

## 1. The map and globe, leading as asked: the render path is healthy; the projects have nothing to place

**Of the three candidate causes, the evidence points to the third — no coordinates exist — and I
stopped there as instructed. No coordinate data was written anywhere but the throwaway dev.db, as
a test fixture.**

**Cause 1, the #198 fix regressed or was reverted: NO, verified twice.** By source: `store.js`
still carries `graftUnmodelledFields` with its "do not narrow it back to a list" comment, and
`app.js` still has `geoHydratedIds` as a Set. No commit since #198 touched either mechanism. By
browser, which is the proof that matters: two throwaway projects given fixture coordinates, the
Map placed both ("2 project(s) placed. 1 have no location yet"), then `LinApp.refreshPortfolio()`
— the exact slim refresh that used to strip locations — was forced, and afterwards **every store
row was `slim: true` and still carried its `lat`**, the Map still drew both markers, and the Globe
mounted (`liveCount` 1, one canvas) with the same two placed. The #198 graft is doing precisely
what its comment says.

**Cause 2, a second independent render defect: none found.** Markers render, survive refresh, and
survive the view switch to Globe. I did not observe any path that drops a project which has
coordinates.

**Cause 3, the projects have no coordinates: this is what everything points to.** Measured in this
container, end to end:

```
projectcreate with address "350 Fifth Avenue, New York, NY"
  -> lat: null, lng: null
  -> geocodeError: "The location service could not be reached, so this project has no
     map position yet. Saving the address again will retry it."
```

And through `w_save`: changing an address triggers a re-geocode, which failed and **cleared the
fixture coordinates I had just supplied** — so an unreachable geocoder does not merely fail to
add a position, a save that touches the address actively removes one. Nominatim is unreachable
through this container's proxy, exactly as the map/globe session reported, so **no session has
ever produced a live geocode**. Whether the deployed platform on Render can reach Nominatim, and
whether any production project carries `lat`/`lng`, I cannot establish: **production was not
inspected and must not be.** Both views' honest response to a coordinate-less portfolio is exactly
the reported symptom: "0 project(s) placed. N have no location yet."

**What would settle it, and it is Lin's to do, not a session's:** open one project on the deployed
platform and look for either a formatted "Matched to:" address or the geocode error message — both
are shown in the interface by design. If the projects have never geocoded, the fix is to re-save
an address (the stored error message itself says so), not to touch the render path, and **not to
backfill coordinates**, which I did not do.

## 2. The blank detail page: fixed, and what the deleted variable was

`assets/js/detail.js` — commit `062731b` deleted `const populated = hasSignals(p);` and rewrote
two of its three uses to the stored-row gate; the third, inside the `innerHTML` template literal
(`${populated ? provenanceLineHtml(p) : ""}`), kept the name and threw a `ReferenceError` before
anything was assigned.

**What it was doing:** gating the provenance line ("Red, driven by A1 Cost & EVM Performance →
…why?") on the legacy browser blob. **What the correct value is now:** the same stored-row gate
its two siblings were rewritten to, because `buildProvenanceTrace` reads the stored row through
`getProjectFusion`. The fix restores the variable with that meaning:

```javascript
const populated = !!(window.LinResults && LinResults.hasResult(p));
const stateKey = populated ? String(state).toLowerCase().replace("-review", "") : "empty";
```

so line 894 renders the provenance line for a project with a stored result and nothing for one
without, which is what the pre-T12b code meant. The reference is not deleted; the gate is
restored with its corrected meaning.

**Browser-verified for both account types:**

- **Operational (OPS-1):** the detail page renders in full — 10,213 characters, State badge
  "Red", the provenance line with its "why?" toggle, and all eleven collapsible sections.
  Screenshot inspected, not just captured.
- **Research (PM-R1):** renders in full — 8,121 characters, badge "Awaiting analysis", which is
  honest: the row clicked was a project the participant holds no primed result for. No errors.

## 3. The swallowed error: reported through two shapes the codebase already has

`showPage`'s catch keeps navigation working — that part of the old comment was right — and now
reports instead of hiding:

- **`console.error("Page render failed for", page, …)`** — the shape every per-item render guard
  in `app.js` already uses (`buildRadar` line 424, `buildFallbackList` line 1337: "… failed for
  project X — message").
- **`LinStore.banner("The <page> page failed to render: <message>. The rest of the application
  still works.", "warn")`** — the codebase's one user-visible non-fatal channel, the same
  `role="status"` banner that says "Couldn't reach the project store". Chosen over inventing an
  error panel because it already exists, is already styled, already announces to assistive tech,
  and a person *and* a browser-driving check can read it.

The banner call is itself wrapped so a failure inside it can never turn a render failure back
into a navigation failure.

**Proven live:** with a dangling reference injected into `detail.js`, clicking into a project
showed the banner verbatim — *"The detail page failed to render: definitelyNotDefined is not
defined. The rest of the application still works."* — the console carried the error, and
navigating to the Handbook still worked. Fault removed afterwards; `grep` count 0.

## 4. A check that actually calls render

`tests_render.html` now loads `detail.js` (it never did — the harness had a `#detail-root`
element and nothing to render into it) and gains **group 3b**, which calls `LinDetail.render(id)`
against the stored-only fixture and asserts: no throw, the panel is non-trivially populated
(> 500 characters), the rendered State badge shows the stored status, and the Governance Decision
section exists.

**Proven able to fail:** with the `populated` fix reverted, the harness went **33/37** — the four
new assertions red, everything else green, which is precisely the two-day blindness reproduced:

```
FAIL LinDetail.render: does not throw …        ReferenceError: populated is not defined
FAIL LinDetail.render: the panel has content   expected true, got false
FAIL LinDetail.render: the rendered State badge shows the stored status   (no badge rendered)
FAIL LinDetail.render: the Governance Decision section is present         false
```

**The misleading group 3 heading is corrected.** It claimed "The detail page State badge renders"
while calling `stateLabel(p)`, a pure function; it is now headed "The State LABEL helper returns
the stored status" with a note pointing to 3b for the page itself.

## 5. D1.3: an abstention no longer carries a colour

`server/app/simulation/portfolio.py` — with no usable history, the Trajectory Classifier is now
**absent from the snapshot's `results` entirely**, matching the project-level contract (an
abstaining module is absent from `module_results`, never present with a colour). No third shape
was invented. With a real history (≥ 2 periods with cpi values) it computes exactly as before:
verified directly, `Red | "CPI trend: -3.3% per period" | insufficient_data: false`.

The task named this file, which is why the standing "do not modify anything under
`server/app/simulation/`" rule was overridden **for this one file only**; nothing else under that
package was touched. The change diverges from the validated Apps Script deliberately, in the same
way and for the same reason as the D1 divergences recorded in `VALIDATION.md`, and the code
comment says so.

**On screen, browser-verified:** the operational portfolio panel now shows **four** rows per
project and zero Trajectory rows — the green dot beside "No history available" is gone. Note the
server path still always passes `history=None` (`documents.py:326`), so today D1.3 abstains on
every computed snapshot; it will start reporting if the portfolio path is ever given the same
`_period_history` treatment the project path got in D1.

**Test updated, and strengthened rather than loosened:** `test_workspace_t3t5.py` Guarantee 9
asserted `len(results) == 5`; it now asserts the four computable sub-results **by name**, that
`cat8_3` specifically is absent, and that **no** stored sub-result carries a colour and an
insufficiency flag together. All three proven able to fail by restoring the always-emit fault:
49/52, exit 1, with the old five-key list visible in the failure detail.

## 6. Verification

| Check | Result |
|---|---|
| Server suite, fresh migrated DB per suite | **1159 checks across 22 suites, 0 failures** |
| `tests.html` | **51/51** |
| `tests_render.html` | **37/37** (33 + 4) |
| New render checks proven to fail | fault restored → 33/37, the four new ones red |
| New workspace checks proven to fail | fault restored → 49/52, the three new ones red |
| Detail page renders, operational account | yes — full page, Red badge, provenance line, 11 sections |
| Detail page renders, research account | yes — full page, honest "Awaiting analysis" |
| Banner on injected render failure, nav intact | yes — verbatim message, Handbook still navigates |
| Map/globe with fixture coords, through a slim refresh | 2 placed before and after; Globe 2 placed |

The suite count moves 1157 → 1159: +3 in `test_workspace_t3t5` (49 → 52), −1 in
`test_document_versioning`? No — `test_document_versioning` printed 28/28 as it did at its last
run on this container; the +3/−1 arithmetic against the T25 baseline is not exact because two
suites' counts differ from the numbers recorded in T25's handoff on this container
(`test_disclaimers` 90, `test_export` 64). I am reporting what ran here, not reconciling counts
recorded on another machine.

## 7. Found while verifying, reported not fixed

- **Fixing the blank page brings D7.2 back.** The Governance Decision section now renders again,
  and its recommendation, authority and documentation are still the browser-derived four-branch
  `if` over the status band — seen live: badge Red beside an action plan reading "All categories
  Green → Routine monitoring", two derivations disagreeing on one card. The stages 7–8 audit's
  finding stands; it was moot only while the page was blank. Out of scope here and
  architecturally significant, so reported only.
- **The provenance line prints module and category ids** ("A1.1 Monte Carlo EAC Forecast",
  "A1 Cost & EVM Performance") in user-facing text, which `NAMING_AUTHORITY.md` forbids without
  exception. Pre-existing; visible again now the page renders.
- **An unreachable geocoder erases coordinates on address edit** (`w_save`: address changed →
  re-geocode → `apply_to_doc` overwrites `lat`/`lng` with null + error). Defensible as designed —
  stale pins are worse than absent ones — but worth knowing before anyone edits addresses on a
  deployment that cannot reach Nominatim.
- **Checks that cannot fail: none found among those I read this session**, and the two I touched
  were tightened (a bare count became named-key assertions; a pure-function call stopped claiming
  to render a page).

## What I could not establish

- **Whether production projects have coordinates**, which is the crux of part 5. Production was
  not inspected. The one-look test is in section 1.
- **Whether Render can reach Nominatim.** Unknowable from here.
- **The exact T25-baseline arithmetic for two suite counts**, noted in section 6.
