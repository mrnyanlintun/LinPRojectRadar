# Run 139 — signal network legend, and Signal Flow label alignment

**`SIMULATION_VERSION` did not move and did not need to.** It is `sim-2026.09-v70` before and
after. No migration. Nothing under `server/app/simulation/` was opened, and nothing under
`server/app/` at all. Presentation only, on two files: `assets/js/projectnet2d.js` and
`assets/js/neural_flow.js`. `assets/css/radar.css` was not touched.

Starting commit `c9f0a9b`. Ending commit below. Migration head `0033_recognition_matches`,
unchanged. Every figure in this report was re-taken by me on merged main, not copied from an
agent, and both panels were measured together after the merge.

**Two premises in the order were false and both mattered.** They are stated in place below rather
than buried: the Signal Flow module column was not ragged, and the longest module name is not the
one the order names.

---

# Panel 1 — the Project Signal Network orrery

## Which file renders it, and how it was confirmed

Confirmed by tracing the registration, not by name similarity. `detail.js:1080` emits the
collapsible section titled "Project Signal Network" carrying `<div class="detail-projnet2d">`, and
`detail.js:1102` dispatches `LinProjectNet2D.render(root.querySelector(".detail-projnet2d"), p)`
on first expand. `LinProjectNet2D` is defined in `assets/js/projectnet2d.js`. The adjacent
"Signal Flow" panel is `detail.js:1081` → `detail.js:1103` → `LinNeuralFlow` in `neural_flow.js`,
which is the second panel of this run and a different file. I checked both dispatch lines myself
before dispatching any work.

## Question 1 — do both legends fit? Not as two columns. Both were kept, stacked in one.

The free space was measured rather than estimated, and measured over time: the satellites orbit,
so a corner clear in one frame is not clear. The measurement samples every painted body — each
moon out to its halo, each planet to its corona, the sun, and each drawn category label's box —
41 to 45 times over 30 to 33 seconds, longer than one orbital period of 28.6 seconds, and unions
them into an occupancy grid.

| viewport | canvas | clean width across full height | clean height in a 240px strip |
|---|---|---:|---:|
| 1440 | 1304 × 620 | **312 px** | **624 px** |
| 1280 | 1151 × 620 | **232 px** | 264 px |
| 1024 | 905 × 561 | **112 px** | 88 px |
| 768 | 659 × 409 | **8 px** | 24 px |

Text widths from the panel's own drawing context: the widest module name is
`Contractor Performance Assessment Signal` at 227.7 px at 10.5, 206.0 at 9.5, about 167 at 8.5.
The widest key-plus-name heading is 211 px. The existing colour key's widest row,
`Not relevant to this project`, is 152.8 px.

**A two-column legend measures about 430 px wide and fits at no tested width** — even at 1440,
only 112 px of height is clean once you are 440 px across. So the build is **one narrow column
carrying both**: the nine-row colour key first, then the five categories with their modules under
each.

**The colour key was not removed.** Where the module names cannot fit, the module names are what
is dropped, the colour key still draws, and the container publishes
`data-legend-modules="omitted"` so the omission is visible to a reader and to a check.

Rendered geometry: **223 × 571 px at (10, 39), 9.5 px type, 43 entries** at 1440 and 1280, inside
the measured clean rectangle at both. At 1024 it settles at 8.5 px and 200 × 511, which is 200 px
against 112 px of clean width, **so it does cross the halos and dotted outlines of the nearest
moons at that width**. It stays legible there on the strength of the shadow, measured below, and
that is stated rather than hidden. At 768 the module names are omitted and only the colour key
draws; that corner was already not free before this run, since Run 131's key sat in it, so the
overlap at 768 is the canvas being too small for the system rather than something this key
introduced.

## Question 2 — how many modules, and does it vary by project?

**28, and it does not vary.** The panel publishes `data-modules` as 28, and the roster read back
from the registry is A1 seven, A2 five, A3 four, A4 eight, A6 four. The system builder maps every
entry of a category's module array to a moon regardless of state: a module not relevant to the
project is drawn as a dashed outline, never omitted. Proved by a second render with the project
sector set to `design`, which produced **six modules not relevant and still exactly 28 legend
entries and 28 moons**. Only the numerator in "n of 28" varies by project.

## Question 3 — where the names and the colours come from

Module names are the `name` on the same moon objects the moon painter draws, built from each
category's own module array. Category headings are the key and name on the same planet objects
the planet painter labels. Both trace to the generated client registry, so a module renamed or
retired in the registry changes the legend on the next build with nothing edited in this file.
That is exactly the drift `test_run35_closure_voter_identities` was written for.

Colours: bands from the shared status-colour map and the runtime theme object, the same ones every
painter reads; each module's swatch rim from the identity palette entry for that module id, which
is the very rim its moon is drawn with.

**Verified by me on the merged diff: zero literal hex values added, and zero hardcoded module
names added.** Both counts are zero over the whole change.

## Question 4 — satellite order is deterministic, but order is not the matching rule

**The ordering rule, for the next reader:** categories in registry order (A1, A2, A3, A4, A6), and
within each category the modules in that category's own array order. That rule holds identically
where the moon keys are built and where the moons themselves are built, and the legend is emitted
from the same arrays in the same order.

**But it does not survive to the screen, and selling it as the matching rule would have been
false.** The painter sorts drawable bodies back to front by depth, and the scene read back from
the rendered page comes out A4.8, A4.9, A3.6, A4.7, A3.2, A4.2 and so on, not declaration order.
On top of that every moon is on a moving orbit at 0.22 radians per second, so its position and
depth change continuously. "The nth entry is the nth dot" would have been wrong.

This was not a stop condition, because a stronger invariant was available. **The match is by the
swatch.** Each entry is drawn exactly as its moon is drawn: the state's fill and dash, rimmed in
that module's own identity colour, which the palette generator holds at least ΔE\*ab 25 from every
band colour and from every other module's. That holds under the depth sort and under the orbit.
The check asserts, per theme, that every entry's swatch equals the identity rim of the moon with
that id and every entry's treatment equals that moon's state, read from the rendered page rather
than from source.

## Contrast, measured from the painted pixel

There is no DOM to walk on a canvas, so the sampler reads the canvas image, crops the rectangle
each text run was painted in, and computes the ratio between the modal ground and the pixel
furthest from it in luminance. An element screenshot never settles on an animating canvas, which
is why the image is taken from the canvas itself.

Minimums per theme at 1440, across six headings, 28 module names and nine colour-key rows:

| theme | headings | module names | colour-key rows |
|---|---|---|---|
| plain | 16.50–17.05 | **6.50** min | **6.53** min |
| light | 13.94–14.16 | **6.34** min | **6.40** min |
| newyork | 14.34–15.02 | **5.64** min | **7.57** min |
| maria | 14.27–14.49 | **6.49** min | **6.56** min |
| dark | 16.82–17.33 | **5.41** min | **5.57** min |

At 768, names omitted, key only: headings 13.77–16.89, key rows minimum 5.76 on dark. At 1024
module-name minima run 5.56 to 6.41. The full sweep is four viewports by five themes, and I
re-took it on merged main: **70 checks, 0 failed**, worst element 5.41:1.

**Two defects were found by measuring rather than assuming, and both were fixed.** At 768 on the
newyork theme the colour-key rows read **2.02:1** and on dark **2.94:1**, because the key lands on
a planet at that width. The shadow was raised from Run 131's four passes at blur 4 to six at blur
6, which is the treatment the status label already uses; newyork went from 2.02 to 7.14. No plate
was added, because a plate hides the body behind it, which is why Run 131 chose a shadow. Then one
dark row reported 1.9:1, which turned out to be a fault in the sampler rather than the paint: with
six shadow passes a tight crop can be more than half ink, so the modal colour was the ink. The
ground is now read from a box 16 px taller than the glyphs while the ink is still taken from the
tight box, and that row measures 5.79:1.

## Proved able to fail

The agent pointed one entry at another module's name and the check named both the entry and the
mismatch, with the wrong name appearing twice in the rendered canvas.

**I ran my own injection on merged main, and the first one taught me something.** Injecting a
wrong name on the not-relevant branch left the check at 70 of 70 — because this fixture has no
not-relevant module, so that branch is never taken. That is a dead path for this fixture, not a
check that cannot fail. Re-injecting on the not-called path, which 24 of the 28 modules take, the
check failed and named all 24, listing each module id with the injected string against its true
registry name. Restored, it returns to 70 of 70 with a clean tree.

## Nothing computed moved

The same project fixture was rendered before and after, and every figure the panel publishes is
identical: 28 modules, 1 lit, 0 unbanded, 3 dark, 0 not relevant, 24 not called, 5 categories, 1
lit, health "Awaiting analysis", 34 scene bodies. The summary sentence under the canvas compares
byte-identical. The version stamp is unchanged and the diff touches no file under `server/app/`.

---

# Panel 2 — Signal Flow label alignment

## The order's premise about this column is false

**The module column was not ragged and already had one left edge.** Every module label was drawn
at a constant column position, and measured, all 28 sat at x 442 with the in-port dot at 430, at
every width tested. Nothing followed the dots horizontally.

**What was actually wrong was vertical.** The labels used a font-middle baseline rather than the
glyph box, so all 28 sat **1.25 px high** of their own dots at 1280 and 1.225 px high at 380.

## Which reading was implemented, and why

**Reading 1.** Each label is now centred on its own dot's centre, measured from the rendered box,
and the left edge is expressed as a named constant indent from the column rather than from the
dots. Worst residual across all 28 labels is **0.001 px** at 1280 and 380, and 0.0007 px at 320.
The horizontal change moves nothing today, since the rendered x stays 442, but the column no
longer follows the dots by construction.

Centring runs as a deferred pass after the panel is appended, retrying on animation frames while
the box reports zero height, because a collapsed panel measures nothing. Only each label's own y
is written.

**Reading 2 is unbuildable here, and this is the part worth your attention.** The gap between the
document and category columns runs 300 to 828, but the module nodes sit inside it at 430 and 768.
A 312.7 px block centred in 300 to 828 starts at x ≈ **407**, left of the in-port dot at 430 and on
top of the dots and the incoming document branches. Centred instead within 430 to 768 it starts at
**442.6**, six tenths of a pixel from where the labels already are. So reading 2 is either a
collision or a non-change.

## The widest label — the order names the wrong one

| label | advance at 1280 | at 380 | at 320 |
|---|---:|---:|---:|
| **Contractor Performance Assessment Signal**, 40 chars | **312.689 px** | 311.008 | 311.225 |
| Independent EAC Reconciliation Index, 36 chars | 281.430 | 279.915 | — |

The longest module name is **31.3 px wider** than the one the order names. I confirmed the name in
the registry independently. Column width required is 312.7 plus the 12 px indent, so 324.7 px from
the in-port dot; the painter allocates 338 px, leaving the widest label's right edge at 754.7,
**13.3 px clear** of the out-port dot at 768. The measured advance is 7.817 px per character
against the code's 8.0 estimate, so the estimate errs safe. The character-width constant was not
changed, because changing it moves the out-port dot, which is forbidden.

Measurement method: real rendered `getComputedTextLength()` and box geometry from the SVG in a
browser, after expanding the section, which renders lazily on first expand. 76 text elements and
201 paths, confirming Run 128's count of 76.

## Nothing moved, verified against my own baseline

I did not take this on trust. I checked out the pre-change file, captured the geometry myself,
restored, and diffed:

- **no node dot moved** — all 56 node elements identical in both coordinates;
- **no flow line moved** — 201 paths, count equal, **both endpoints of every path identical to
  three decimals**, which is 402 endpoints;

at both 1280 and 380. Re-taken again on merged main after both panels landed: all checks pass.

**The check can fail, proved twice.** The agent nudged the column by 3 px and the diff reported
both failures, naming 28 in-port elements and giving a moved endpoint. Independently, I diffed the
pre-change capture against itself and it failed on exactly the right things: labels off by 1.25 px,
the dimmed labels the same, and the legend not naming Complete.

## The dimmed labels

All **27** dimmed labels obey the same rule, worst residual 0.001 px. They were verified
explicitly rather than assumed.

## The narrowest viewport

The panel has no minimum width of its own: it is full-width with a fixed view box and automatic
height, so it scales uniformly. The narrowest measured is **320 px**, where the panel's box is
245.19 px at a scale of 0.171. Because the scaling is uniform, overflow is answered in diagram
units and is width-independent: at 320 the widest label is 311.2 px and its right edge is 757.1
against the out-port at 768. **No overflow at any width.** Legibility degrades at 320, where 13 px
type renders at about 2.2 px, which is pre-existing and out of scope.

## `COL.Complete` gained its legend row

Added between Red and No data, drawn as a **hollow ring** rather than a filled dot, because the
shape function returns a ring for Complete on this very surface while the other four verdicts are
filled. A filled dot would have misstated the render.

Measured to fit: the strip height is **51 px at 1280 and 207 px at 380, identical before and
after**. At 1280 the first legend row previously ended at x 1043 with the strip's right edge at
1215, so the new entry took 172 px of already-free space. No entry overflows at either width. The
strip was not moved, resized or restyled, and Run 131's geometry is untouched. No CSS rule was
needed, so the shared stylesheet was not opened.

## Nothing computed moved

The whole change is two front-end files plus five new standalone scripts under `server/tools/`.
No file under `server/app/` was touched, so no stored value, band, threshold, weight or rule can
have moved. The version stamp is unchanged. The empirical proof is the endpoint diff above.

---

# The handoff document

The order asked that `T6_HANDOFF.md` be read and updated if stale. **It was stale by fifty runs:**
its last section is Run 89, dated 2026-08-30, and nobody has appended since. The file has declared
since Run 59 that it carries no authority, but it did not say it is **incomplete as history**, so a
reader taking its last section as the current state would be fifty runs wrong about the version
stamp, the module roster, the category weights and the status rules alike.

A block was added at the top recording that, and pointing at the 226 root report files where the
history since Run 89 actually lives. **No run sections were back-filled.** Writing fifty of them
now from the reports would manufacture a record nobody kept, which is a worse defect than the
staleness it would hide. Nothing below the block was edited and the four deliberate ordering breaks
are untouched. This is an addition at the top of exactly the kind Run 59 made, which the file's own
rule permits.

---

# Items found and not fixed

1. **Pre-existing, confirmed still present, out of scope.** On the light theme a failed or Red
   category's planet label is drawn with an ink that resolves to near-white on cream, so the
   category name under A4 is barely legible. This is Run 131's finding on pre-existing text. The
   new legend text is measured above and is not affected.
2. **Unproven.** The old build's colour-key contrast at 768 was not measured, so no before figure
   can be stated there. The free-space measurement of 8 px clean at that width makes it near
   certain the old key overlapped too, but that number was not taken.
3. **Unproven.** Whether "centred" in the order meant something other than reading 1's vertical
   centring — for instance each label centred within the gutter, which would make the column
   ragged on both edges and contradict the same order's "one left edge". That was not built.
4. **At 1024 the orrery legend crosses the nearest moons' halos.** Stated plainly above rather
   than hidden. If that is unacceptable, the alternatives are omitting the module names at 1024 as
   they already are at 768, or moving the key outside the canvas frame, which is a larger change
   than this order authorises.

# Confirmations

Starting commit `c9f0a9b`. Migration head `0033_recognition_matches`, unchanged; no migration.
`SIMULATION_VERSION` `sim-2026.09-v70`, unchanged. `git status --porcelain` was checked before
every commit and showed only the intended files; `git add` was by explicit path throughout, and
no `git add -A` or `git add .` was used. All work ran against throwaway SQLite files in the
scratchpad; production Postgres was never contacted. Both agent branches were merged `--no-ff`
after I re-took their figures myself, and both panels were then measured together on merged main:
the orrery check at 70 of 70, and the Signal Flow diff passing every check against my own
pre-change baseline.
