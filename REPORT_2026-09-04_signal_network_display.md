# Run 131 — the Project Signal Network: the status box, and a missing legend

Presentation only. `SIMULATION_VERSION` did not move and did not need to.

- Starting commit: `f580d36` (= `origin/main`), tree clean.
- Ending commit: **see the closing section**; two goal commits plus this report.
- Migration head: `server/alembic/versions/0033_recognition_matches.py`, unchanged. No migration.
- `SIMULATION_VERSION = "sim-2026.09-v67"` at `server/app/simulation/models.py:1031`, unchanged.
- Nothing under `server/` was touched at all.

---

## 0. THE ONE CORRECTION TO THE ORDER, AND IT DECIDES BOTH FIXES

**The order names the wrong file.** It says "The surface is the Project Signal Network panel,
`assets/js/neural_flow.js`." Those are two different panels, and the code says so plainly.

`assets/js/detail.js:1080-1081` builds them as adjacent sections:

```
${cs("d-projnet", "Project Signal Network", `<div class="detail-projnet2d"></div>`, ...)}
${cs("d-neural",  "Signal Flow",            `<div class="detail-neural-flow" ...></div>`, ...)}
```

- **Project Signal Network** is `assets/js/projectnet2d.js` — a `<canvas>` orrery: a central sun
  carrying the project status, category planets, module moons.
- **Signal Flow** is `assets/js/neural_flow.js` — the SVG mind-map tree, which is where Run 128's
  DOM measurements (76 SVG text elements, one band word, the `.lnf-legend` strip) came from.

Both of the owner's descriptions were checked against the rendered page, not against the source:

| The order says | Where it actually is |
|---|---|
| "PROJECT STATUS over Amber, both on a dark filled rectangle … pasted over the node" | `projectnet2d.js:833-838` — `ctx.fillRect` at `alpha(TH.surface, 0.86)`, sized with `measureText`. **Photographed. Exactly as described.** |
| "a large bright orange disc" | `projectnet2d.js`'s sun, filled with the band colour |
| "192 node circles that state their band by colour alone" with no legend | `projectnet2d.js` — **no legend of any kind exists in that file** |
| "`.lnf-legend` swatches at `neural_flow.js:1668-1691`" | correct, but that strip is the **Signal Flow** panel's, not this one's |

**There is no plate `rect` anywhere in `neural_flow.js`.** I grepped every `se('rect', …)` in it:
three exist, all three are the full-frame background washes at lines 949-950 and the helper at 323.
Its central node paints `Project` / `Status` as plain white text on the disc and the band word below
it — I photographed that too, on `dark`, `light` and `newyork`, at 6× device scale. No box.

So: **the owner is looking at the panel they named, and Run 128 measured the panel beside it.**
Both fixes were done on `projectnet2d.js`, the panel the owner is actually looking at.
`neural_flow.js` was **not modified** — see §3 for the `.lnf-legend` decision and why.

---

## 1. FIX 1 — the plate behind the project status label

**Removed.** `assets/js/projectnet2d.js`, in `draw()`, the block that painted the sun's words.

### What was there

```js
ctx.fillStyle = alpha(TH.surface, 0.86);
var lw = Math.max(ctx.measureText("PROJECT STATUS").width,
                  ctx.measureText(String(sys.health || "no status")).width) + 16;
ctx.fillRect(hp.x - lw / 2, hp.y - 18, lw, 36);
```

An opaque scrim sized to the wider of the two lines. No other label on that canvas has one.

### The contrast, measured in the rendered canvas

Method, following Run 128's lesson: **painted pixel, never the stylesheet.** Rendered in headless
Chromium, read back with `getImageData` over a box hugging each text line, pixels within a small
colour distance of the glyph ink discarded, modal remaining colour taken as the background.
Foreground read from the live theme (`getComputedStyle(body)` for `--text`;
`window.LIN_STATUS_COLORS.Amber` for the band word) — never assumed.

Theme measured: **`newyork`**, an Amber row. Repeated on `dark`.

| line | before (on the plate) | plate removed, nothing put back | **after (halo)** |
|---|---|---|---|
| `PROJECT STATUS` — `#f2e7c9` | bg `rgb(49,38,25)` → **12.99:1** | bg **`rgb(255,140,26)`** (the sun) → **1.89:1** | bg `rgb(17,24,27)` → **14.57:1** |
| band word `Amber` — `#ff8c1a` | bg `rgb(49,38,25)` → **6.34:1** | bg **`rgb(255,140,26)`** → **1.00:1** | bg `rgb(24,27,28)` → **7.44:1** |

On `dark`: before 13.95 / 6.86 → after 16.92 / 8.04.

### The finding that decided the fix

**A bare removal is not shippable, and the reason is structural, not marginal.** The sun body
gradient's mid stop *is* `hcol` (`projectnet2d.js:622`, `sbody.addColorStop(0.45, hcol)`), and the
band word is painted in that same `hcol`. Remove the plate and paint on the disc and the word is
**rendered in its own background — 1.00:1, measured, not argued. It disappears entirely.** That is
the order's "establish before removing" clause coming back positive.

The band word's colour is not negotiable either: it is the status token, and recolouring it would
make this surface disagree with every status pill on the page.

So the **fill is gone** — no rectangle is painted, the label sits on the node, both lines are kept,
the band word keeps its exact colour — and the legibility is carried instead by the second of the
order's three named alternatives: **a text shadow**. `ctx.shadowColor = alpha(TH.surface, 0.95)`,
`shadowBlur = 5`, six accumulating passes (one pass is far too faint against a lit disc; the shadow
deepens, the glyph does not move). This is the canvas equivalent of `.lnf-halo`, which
`neural_flow.js:371` already strokes under every glyph on the sibling panel for exactly this reason.

Contrast is **higher after than before** on both lines and both themes.

---

## 2. FIX 2 — a legend inside the chart area

**Built.** The order's third case: *"If none exists on this panel: add one."*

Established first, as instructed: **`projectnet2d.js` contains no legend at all** — grep for
`legend` in the file returns nothing, and the rendered panel has no `.lnf-legend` child
(`document.querySelector('#host2 .lnf-legend')` → `false`, checked on the rendered page). The
`.lnf-legend` strip the order refers to belongs to the Signal Flow panel; see §3.

### What it states — every treatment the surface paints

Taken from the drawing code's own five branches (`projectnet2d.js:771-819`) plus `bandColor()`:

| swatch | entry | what the chart paints it for |
|---|---|---|
| filled disc `C.Green` | Green | a body that asserted that band |
| filled disc `C.Yellow` | Yellow | " |
| filled disc `C.Amber` | Amber | " |
| filled disc `C.Red` | Red | " |
| filled disc `C.Complete` | Complete | `bandColor("complete"/"blue")`; a published project status, not a severity — listed after the four bands for that reason |
| rimmed body, `TH.muted` | Computed, no band asserted | `state === "computed_unbanded"` |
| dark filled body, `C.None` | Nothing to report | `state === "abstained"` |
| dashed outline, `C.NotRelevant` | Not relevant to this project | `state === "not_relevant"` |
| dotted outline, `TH.line` | Not called | `state === "not_called"` |

**Nine entries; nothing left out.** The order asked after "no data, not relevant, not called" — all
three are present, plus the fourth non-band state the surface actually paints (*computed, no band
asserted*), which is distinct from all of them.

**On `Complete`, which the briefing flagged: yes, it is covered, and yes it can be painted here.**
`bandColor()` maps `complete`/`blue` to `C.Complete`, and `C.Complete` is additionally the fallback
fill for any computed moon whose band does not resolve (`bandColor(m.band) || C.Complete`). It is
now named. (The briefing's related claim about `neural_flow.js`'s `.lnf-legend` omitting
`COL.Complete` is **correct** — I confirmed it: nine keys in `COL`, and `Complete` is the one with
no legend row. It is not fixed here, because that strip is the other panel's and this run did not
touch it; it is flagged in §5.)

The sun's own unlit state is the same "no band was issued" fact as *computed, no band asserted*, and
is not given a tenth row; the sun states it in words on the node.

### Colours come from the same source the nodes take them from

Every entry reads `C` (from `colors()`, which reads `window.LIN_STATUS_COLORS`) or `TH` (the runtime
`getComputedStyle` theme read). **There is not one literal hex in the legend.** `bandColor()` and the
moon, planet and sun painters read the same two objects. A token that moves moves in the chart and
in the key, or in neither.

### Placement

Bottom-left of the canvas, in **screen space** (drawn after the scene, so pan and zoom do not move
it). That is the corner the centred system does not occupy; the summary sentence is a DOM
`<p class="projnet2d-note">` **below** the canvas, so it is not crossed either. Verified by
screenshot on `newyork`, `dark`, `light` and `miami`: no overlap with any node or with the sentence.

**Stated rather than defended, per the order's clause:** this is *not* collision-proof under user
interaction. The chart can be dragged and zoomed by hand, and a reader who drags a planet into the
bottom-left corner will put it behind the key. The alternative — a legend that moves when the chart
is dragged — is worse. At rest, at every width tested, it does not collide.

### Proof — both sides read from the rendered page

Legend swatch pixels sampled from the canvas with `getImageData`; chart bodies sampled the same way;
each body then classified to its **nearest legend swatch** and compared with the `status` the scene
graph (`LinProjectNet2D.lastScene()`) says it was drawn for. Neither side was read from source.

```
legend swatch painted pixels:   Green [46,230,107]  Yellow [255,224,102]  Amber [255,140,26]
                                Red   [255,59,48]   Complete [78,160,255]
tokens (LIN_STATUS_COLORS):     #2ee66b  #ffe066  #ff8c1a  #ff3b30  #4ea0ff     ← exact match

  chart         A4 status=Red       painted=[219,50,41]   -> nearest swatch = Red       MATCH
  chart         A3 status=Amber     painted=[217,119,22]  -> nearest swatch = Amber     MATCH
  chart         A6 status=Complete  painted=[67,137,218]  -> nearest swatch = Complete  MATCH
  chart         A2 status=Yellow    painted=[216,190,87]  -> nearest swatch = Yellow    MATCH
  chart         A1 status=Green     painted=[40,197,92]   -> nearest swatch = Green     MATCH
  chart    __sun__ status=Amber     painted=[228,125,23]  -> nearest swatch = Amber     MATCH
ALL MATCH
```

Repeated on `dark`, `light` and `miami`: ALL MATCH on each.

**Proved able to fail.** The Green row was pointed at `C.Red` and the panel re-rendered: two rows
went `MISMATCH` (A4 Red → Green, A1 Green → Complete) and the run reported `MISMATCH PRESENT`. The
fault was then removed and the run returned to `ALL MATCH`.

---

## 3. THE `.lnf-legend` STRIP — established, and deliberately left alone

The briefing's premise here is **correct**, and I measured it on the rendered page:

- `.lnf-legend` exists, is a `<div>` child of `.lnf-diagram`, and is the **third** child, after the
  `<svg>` and after `.lnf-summary`.
- Rendered geometry at 1280px: SVG occupies y `0 → 836.70`; the legend strip occupies
  y `899.48 → 950.48`, full width. **It renders below the chart frame, outside it** — the order's
  first case.

I did **not** move it, and this is a judgement call the owner should overrule if they disagree:

1. It is not the panel the owner is looking at. Fix 2's stated defect — "192 node circles that state
   their band by colour alone", no key — is `projectnet2d.js`, which now has one.
2. It does not fit inside `neural_flow.js`'s frame without a layout change. `neural_flow.js:859,
   872-873`: `H = 940`, `BODY_BOTTOM = H - 44 = 896`, and nodes are drawn **at** `BODY_BOTTOM`. That
   leaves 44 viewBox units (≈39 CSS px at 1280) of clearance below the bottom node row, against a
   strip that measures **51px tall at 1280 and wraps taller at narrower widths**. Moving it in as-is
   collides with the bottom row of document and module nodes. That is the order's own
   "say so rather than shipping one that collides" clause, and this is me saying so.
3. Making it fit needs the viewBox grown — a layout change to a panel the owner did not report a
   problem with, in a file whose comments record three separate occasions where a text-metric
   assumption on that surface shipped a defect.

**It is unchanged, and no second copy of it was made.**

---

## 4. FILES TOUCHED

**`assets/js/projectnet2d.js`** — the only source file changed. 108 insertions, 7 deletions.

- *Changed, goal 1:* the sun's label block. The `ctx.fillStyle = alpha(TH.surface, 0.86)` /
  `measureText` / `fillRect` plate is deleted; the two `fillText` calls are wrapped in
  `save()`/`restore()` with `shadowColor`/`shadowBlur` and repeated six times each.
- *Changed, goal 2:* a new `drawBandKey()` IIFE added immediately before `ctx.textAlign = "left";
  LAST_SCENE = scene;` at the end of `draw()`.
- *Left alone:* every geometry, projection, orbit, state predicate, `colors()`, `bandColor()`,
  `storedRow()`, `buildSystem()`, `placeSystem()`, the scene graph and all `data-*` attributes, the
  summary sentence, and every interaction handler. No status is computed, re-derived, defaulted or
  re-worded. The words `"PROJECT STATUS"` and `String(sys.health || "no status")` are byte-identical
  to what they were.

**`REPORT_2026-09-04_signal_network_display.md`** — this file, at repo root.

**Not touched:** `assets/js/neural_flow.js`, anything under `server/`, `assets/css/radar.css`,
`T6_HANDOFF.md`, any migration, any specification.

`T6_HANDOFF.md` was read (top block only, per its own header: it carries no authority and the code is
true where they disagree). It is stale — newest section is Run 89 — and is left as every run since
Run 90 has left it. Its rule is that it governs nothing, so a run that only changed two canvas
drawing calls has nothing there to correct.

---

## 5. NO CHECK WAS COMMITTED, AND WHY

Same reasoning Run 128 recorded, and it applies more strongly here. Both fixes live in `<canvas>`
drawing calls. A source-reading check would assert on the same literals the code contains and could
not fail for the reason that matters (the `--heading` lesson: the source read green while the text
was invisible) — Run 121 named that class of check. A rendered-page check would drag a headless
browser harness into the repo for one assertion, and `server/tools/` holds check-*scripts*, not
pytest modules. The harness that produced every number in this report was built in the scratchpad,
used, proved able to fail, and deleted; it is not committed.

**Two things worth a future run, neither in this run's scope:**

1. `neural_flow.js`'s `.lnf-legend` has no `Complete` row. `COL` (line 265-272) has nine keys and
   `Complete` is the only one the strip does not name, while `STATUS_RANK` ranks it alongside Green
   and `ESTIMABLE` admits it. That surface can paint a treatment its own key does not name.
2. On the `light` theme, `projectnet2d.js` renders the category label "Document-Derived Condition
   Signals" near-white on the cream ground — photographed, legible only by its shadow. Pre-existing,
   unrelated to this run, and the same family as the `--heading` defect Run 94 recorded at
   `projectnet2d.js:161`.

---

## 6. CLOSING

`git status --porcelain` before the goal-1 commit (harness files are scratch, never added, since
deleted):

```
 M assets/js/projectnet2d.js
?? _h_contrast.py  ?? _h_contrast2.py  ?? _h_crop.py  ?? _h_harness.html
?? _h_pn.py  ?? _h_shot.py  ?? _h_themes.py  ?? _h_zoom.py
```

`git status --porcelain` before the goal-2 commit:

```
 M assets/js/projectnet2d.js
?? _h_contrast.py  ?? _h_contrast2.py  ?? _h_crop.py  ?? _h_harness.html
?? _h_legcheck.py  ?? _h_pn.py  ?? _h_shot.py  ?? _h_themes.py  ?? _h_zoom.py
```

Every `git add` was by explicit path. No `git add -A`, no `git add .`. Nothing was pushed.

- Goal 1: `ae29ae1` — the status label sits on the node, not on a plate.
- Goal 2: `d4cf108` — the Project Signal Network gets a band key inside its frame.
- Report: the commit this file lands in.

Rendered in a real browser: **yes.** Headless Chromium via Playwright for Python, offline, loading
the real `radar.css`, `config.js`, `data.js`, `taxonomy.js`, `neural_flow.js` and `projectnet2d.js`
with `LinAuth.init()` stubbed to `false` (the `tests_render.html` trick), calling the production
entry points `LinNeuralFlow.render(p, host)` and `LinProjectNet2D.render(host, p)`. Zero page errors.
Screenshots before and after, both fixes, on four themes.

One environment note for the next run: `playwright.chromium.launch()` fails out of the box —
`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` holds `chromium-1194`, but Playwright's Python package
expects `chromium-1140` and the 1194 `chrome` binary refuses `--headless=old`. Pass
`executable_path="/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"` and it
launches. Do not run `playwright install`.
