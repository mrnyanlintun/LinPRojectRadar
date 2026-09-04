# Run 128 — two display corrections

**Date:** 2026-09-04 · **Branch:** `main` · **Not pushed.**

Presentation only. `SIMULATION_VERSION` did **not** move and did not need to: nothing here
reaches a computed value or a stored row. Nothing under `server/app/simulation/` was opened for
edit. No migration. Migration head is still `server/alembic/versions/0033_recognition_matches.py`.

---

## Ledger

| | |
|---|---|
| Starting commit | `754f6e3` (= `origin/main`), tree clean |
| Fix 1 commit | `54cca33` |
| Report commit | see the last line of this file's own commit |
| `SIMULATION_VERSION` | `sim-2026.09-v66`, unchanged, `server/app/simulation/models.py:1021` |
| Migration head | `0033_recognition_matches.py`, unchanged |
| Fix 2 | **STOPPED, not removed.** Reason below. |

`git status --porcelain` before the fix-1 commit — exactly the one intended file:

```
 M assets/css/radar.css
```

---

## How both surfaces were observed

Both surfaces were **rendered in a browser and read**, not inferred from the stylesheet.
Run 121's lesson is taken literally: every number below comes from a painted page.

* Headless Chromium at `/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`,
  driven by Python Playwright. (The Playwright python package expects `chromium-1140` and the
  full `chromium-1194` build refuses old-headless, so the headless-shell binary is named
  explicitly. `playwright install` was **not** run.)
* An offline harness page was written to the repo root, used, and deleted — it was never
  committed and does not exist in the tree. It is modelled on `tests_render.html`: it stubs
  `LinAuth.init() -> false` so `app.js` exports `window.LinApp` without booting, loads the real
  `config/data/taxonomy/module_charts/recommendation_options/decision/store/gmap/app/detail/
  projectnet2d/files/workspace/neural_flow` scripts and the real `assets/css/radar.css`, plants
  one project carrying a `storedResult` the way `facade.with_stored_status` delivers it, then
  calls the production entry points `LinDetail.render(id)` and `LinNeuralFlow.render(p, host)`.
  No network, no fixture invention, no private function reached into.
* The rendered headline read, byte for byte, the sentence in the order:
  `0 of 31 modules produced a status for this period. 31 did not. 0 of 7 categories have been processed.`
  That is the confirmation that the surface under the microscope is the surface the owner is
  looking at.

**Contrast method.** Foreground from `getComputedStyle(el).color` on the live element.
Background **from the painted pixels**: a style rule painting every glyph in the panel
`color: transparent` is injected, the element is screenshotted, and the modal pixel of that
screenshot is taken as the background it actually renders on. That composites the whole real
stack — translucent panel over translucent surface over the body gradient over the page — which
walking `background-color` up the DOM does **not**; an earlier pass that did walk the DOM read
the NYC headline background as `rgb(37,40,45)` when the painted pixel is `rgb(9,13,19)`. Ratio
is WCAG 2.x relative luminance. Semi-transparent foregrounds are composited onto that background
before the ratio is taken.

---

## Fix 1 — the module count was unreadable. Fixed.

### Was the faint treatment deliberate?

**The size and weight were deliberate. The colour was not — it is a defect, not a watermark.**

The rule sits under a comment that says the figure "is the largest thing in the panel, because it
is the thing the owner ruled must be read first" (Run 82, Part A). A watermark is the opposite of
that intent. What actually happened is a token leak:

* `.detail-catspecs .dcat-headline-figure` asked for `color: var(--heading, var(--text))`.
* `--heading` **is** declared — on bare `:root`, as `#141a26`, a near-black ink tuned for the warm
  light field (the `:root` comment says so in as many words).
* Neither `body[data-theme="newyork"]` nor `body[data-theme="dark"]` redeclares `--heading`.
* So the `var(--text)` fallback **never fires** on a dark theme, and a near-black numeral is
  painted on a near-black panel.

That is exactly the distinction the order drew: the rule was written for the light field it was
authored on, and renders on a field it was never checked against. The fix therefore raises **only
the colour**; font-size (22px), font-weight (700), font-family (mono) and letter-spacing are
untouched, and the figure is still the largest thing in the panel.

### Which theme the owner is seeing

`app.js init()` offers Fairbanks (`plain`), Miami (`light`), NYC (`newyork`) and Maria; Gotham
(`dark`) is archived and a persisted `"dark"` falls through to the default. **NYC is the offered
theme on which this panel fails**, so the owner is on NYC. On Fairbanks the same line measures
17.36:1 and reads perfectly — which is why a stylesheet reading alone would have found nothing.

### Every text element in the panel, measured on the background it actually renders on

Ratios are before → after. `FAIL` marks below 4.5:1.

| element | Fairbanks (plain) | Miami (light) | **NYC (newyork)** | Maria | Gotham (dark, archived) |
|---|---|---|---|---|---|
| `.dcat-headline-figure` *(the invisible one)* | 17.36 → 15.61 | 15.82 → 14.15 | **1.11 FAIL → 15.69** | 16.12 → 14.43 | 1.11 FAIL → 17.71 |
| `.dcat-name` *(the module/category name)* | 16.46 → 14.80 | 14.24 → 12.74 | **1.01 FAIL → 14.29** | 14.37 → 12.86 | 1.15 FAIL → 17.68 |
| `.dcat-produced` *(the per-row figure)* | 16.46 → 14.80 | 14.24 → 12.74 | **1.01 FAIL → 14.29** | 14.37 → 12.86 | 1.15 FAIL → 17.68 |
| `.dcat-headline-words` | 15.61 (unchanged) | 14.15 | 15.81 | 14.43 | 17.71 |
| `.dcat-headline-rest` | 6.34 | 6.36 | 9.28 | 6.65 | 6.52 |
| `.dcat-status` (the band chip, "No band") | 6.00 | 5.96 | 8.39 | 6.01 | 6.50 |
| `.dcat-state` | 5.07 | 4.73 | **4.06 — quiet, not fixed** | 4.78 | 3.81 — quiet, not fixed |
| `.dcat-hint` | 6.34 | 6.57 | 9.23 | 6.75 | 6.53 |
| `.dcat-call-all` (Process all) | 18.26 | 18.26 | 18.26 | 18.26 | 18.26 |

**The owner was right that the module name has the same problem.** `.dcat-name` measured
**1.01:1 on NYC** — worse than the headline figure. So did the per-row `0 of 7 produced a status`
figure (`.dcat-produced`), which the order did not name. All three carried the identical
`var(--heading, var(--text))` and all three are fixed by the same one-token change.

**What was deliberately NOT restyled.** `.dcat-state` measures 4.06:1 on NYC — under AA for
11px text, but legible, and it is painted in `--faint`, the site-wide de-emphasis token used
by many surfaces. That is a chip that is quiet by choice, not a figure nobody can read, and
raising it means moving a shared token across the whole site. Reported, left alone.
`.dcat-headline-rest`, `.dcat-hint` and `.dcat-status` all clear 4.5:1 on every theme and were
likewise left alone.

### Files touched by fix 1

**`assets/css/radar.css`** — three declarations, one token each, plus explanatory comments.

* `.detail-catspecs .dcat-headline-figure` (was line 4682): `color: var(--heading, var(--text))`
  → `color: var(--text)`.
* `.detail-catspecs .dcat-produced` (was line 4691): same substitution.
* `.detail-catspecs .dcat-name` (was line 4728): same substitution.
* **Left alone:** every `font-size`, `font-weight`, `font-family`, `letter-spacing`, `margin`,
  `padding`, `border`, `grid-template-columns` and `display` in the block; the entire
  `.dcat-status[data-status=...]` band-colour set; `.dcat-state`; `.dcat-hint`;
  `.dcat-headline-rest`; `.dcat-headline-words`; the `:root` and per-theme palette blocks —
  `--heading` itself was **not** redefined, because doing so would have moved `.ws-table th`,
  `.fx-node-label`, `.fx-droprow-name` and several headings on other surfaces. The change is
  scoped to the three rules that fail.

`assets/js/detail.js` was **read and not modified**. The markup (`specHeadlineHtml`,
`assets/js/detail.js:3482-3491`) is correct; the defect was entirely in the stylesheet.

### Proof the measurement can fail

It did fail, on the object it describes, before the change: 1.11 / 1.01 / 1.01 on NYC in the
rendered page, and 15.69 / 14.29 / 14.29 in the same rendered page afterwards, with nothing
between the two runs but the three-token edit. The failing state is the pre-fix repository, not
a fault introduced to satisfy the rule. **No check was committed:** a contrast check that reads
the stylesheet is precisely the check Run 121 warned about, and a rendered-page check would have
to carry this browser harness into the repository for one assertion. Reported rather than added.

---

## Fix 2 — the signal network colour box. **STOPPED. Nothing removed.**

### The surface, found

`assets/js/neural_flow.js` (`window.LinNeuralFlow.render`, loaded by `index.html:1340`). It was
rendered in the same harness and read.

### What the colour box actually encodes

It is a **legend key**, and it is the **only** statement of the band encoding on that surface.

Rendered NYC, the surface contains:

* **192 SVG `<circle>` nodes** — one per module/category/document node. Each states its band by
  **colour alone**. There is no band word on any node.
* **76 SVG `<text>` elements.** Exactly **one** of them contains a band word: `Amber`, and that
  is the single `PROJECT STATUS` node — the project's overall status, not any signal's.
* **One `.lnf-legend` strip** (`neural_flow.js:1659-1712`), the only DOM colour swatches on the
  whole surface. Each entry is a swatch beside a word:
  `Green · Yellow · Amber · Red · No data · Not relevant · Registered, not active on this project ·
  Uploaded · Not uploaded`, then three line samples for the connection layers.

So the swatch beside `Green` **is** the sentence "the colour #12703a means Green". Remove it and
the word `Green` is left standing next to nothing, while 192 nodes on the same surface go on
stating their band in a colour the reader now has no key for. The file says the same thing about
itself at `neural_flow.js:818` — the dot "still carries its band colour and its band shape" — and
at `:1343`.

### The ambiguity in the brief, resolved

The brief flagged that `neural_flow.js:1668-1691` might be either a legend swatch or a per-signal
band dot, and that removing the wrong one is a real error. Rendered and read: **there is no
per-signal DOM swatch anywhere on this surface.** Lines 1668, 1673 and 1691 are `legDot`,
`legSquare` and the registered-not-active sample, all three inside the legend strip built at
1659. The per-signal marks are SVG circles in the node layer (section 7, from line 1296) and are
not styled by these functions at all. There is nothing else the owner could be pointing at.

### Verdict

**The stop condition in the order fires.** Removing the swatch would take the only statement of a
band on that surface, and the surface is a study stimulus. Nothing was changed in
`assets/js/neural_flow.js`; it was read only.

**What would be lost if it were removed anyway:** the colour→band mapping for Green, Yellow,
Amber and Red, and with it the readability of all 192 node marks; plus the `Not relevant` square
(a sector exclusion, deliberately a different shape from the five severity dots) and the
`Registered, not active on this project` dim dot. **What is stated elsewhere on the view:** only
the project's own overall status, once, in words, on the `PROJECT STATUS` node. Per-module and
per-category bands are stated nowhere in text on this surface.

**If the owner still wants the swatch gone,** the honest route is to put the band in words beside
each node first, and that is a change to what the surface states — not a display correction. It
needs its own order.

---

## `T6_HANDOFF.md`

Read (top block). It is **stale** — its newest section is Run 89 and 38 runs have landed since —
but it was left untouched, which is what every one of Runs 90 through 127 did: `git log` shows no
commit touching it in that range. The file's own header says it carries no authority, that the
code is true where they disagree, and that its ordering is not to be rewritten. Adding one Run 128
section would not make a 38-run gap less stale and would break the practice the last 38 runs
established. Flagged here rather than edited.

---

## Corrections to the brief

The brief was accurate on every checkable point. Confirmed independently: HEAD `754f6e3` and a
clean tree; `SIMULATION_VERSION = "sim-2026.09-v66"` at `models.py:1021`; migration head
`0033_recognition_matches.py`; the markup at `detail.js:3482-3491`; the rules at
`radar.css:4672-4691` and `:4728`; `--heading` as the defect; the size-and-weight comment;
`neural_flow.js` as the signal-network surface. Three things to add:

1. **`--heading` is not merely absent on the dark themes — it is present and wrong.** It is
   declared on bare `:root` as `#141a26`. That is why the `var(--heading, var(--text))` fallback
   the rules were written to rely on never fires, and why a stylesheet reading that stops at
   "there is a fallback" concludes the rule is safe. It is not.
2. **The panel has three failing elements, not one.** `.dcat-produced` — the per-row
   `0 of 7 produced a status` figure — carries the same token and measured 1.01:1 on NYC. The
   brief named the headline figure and asked about the module name; it did not name this one.
3. **The failing theme is NYC, an offered theme, not the archived Gotham.** The brief listed
   three candidate palettes; the one that matters is `body[data-theme="newyork"]`
   (`radar.css:3443`), which redeclares `--text` and `--muted` but not `--heading`. Gotham fails
   identically but is unreachable through the switcher.
