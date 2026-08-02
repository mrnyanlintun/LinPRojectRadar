# A second theme: Plain

A fourth `data-theme`, keyed `plain` and labelled Plain. White surfaces, neutral greys, one blue
accent, no decoration. It is a variable set: no component was rewritten.

Server 1634 checks across 30 suites, `tests_render.html` 62/62, `tests.html` 51/51, on merged
`main`. Nine faults injected against the new checks, every one detected, every one reverted and
rechecked byte for byte.

---

## 1. The contrast ratios, measured

Every number below is computed by `server/tools/test_theme_plain.py`, which reads the hex values
**out of `radar.css`** and calculates the ratio. A comment claiming a ratio cannot make it pass;
changing a hex changes the number the suite computes.

Text, against both the panel surface (`#ffffff`) and the page (`#f5f6f8`). AA is 4.5.

| Token | Value | On surface | On page |
|---|---|---|---|
| `--text` | `#1a1d23` | **16.88** | 15.61 |
| `--heading` | `#0f1216` | **18.78** | 17.36 |
| `--muted` | `#545b66` | **6.85** | 6.34 |
| `--faint` | `#5f6672` | **5.78** | 5.35 |
| `--phosphor` (accent, links, focus) | `#0b6bcb` | **5.28** | 4.88 |
| `--status-green-text` | `#12703a` | **6.17** | 5.70 |
| `--status-yellow-text` | `#6f5200` | **7.28** | 6.74 |
| `--status-amber-text` | `#9a4700` | **6.41** | 5.93 |
| `--status-red-text` | `#b81420` | **6.65** | 6.15 |
| `--status-complete-text` | `#1060a8` | **6.44** | 5.96 |

Every one clears AA on both backgrounds, and seven of the ten clear AAA (7:1) on the surface.
`--faint` is darker than the shared `#5c6678` specifically because that value lands at 4.25 on
`--surface-soft`, which is a real panel colour on this theme.

Graphical objects need 3:1, not 4.5:1. Against the globe's sea (`#a9c6da`):

| | Ratio |
|---|---|
| Globe land `#3f6478` on sea (coastlines legible) | **3.56** |
| Globe graticule `#41637a` on sea | **3.58** |
| Worst status marker on sea (green, the palest) | **3.46** |

White ink on a filled status pill is 6.17 at worst (green) and 6.65 at best (red).

**What I did not measure.** Contrast of text over the photographic map tiles, and over the globe's
land dots, is not a fixed pair of colours and is not asserted. Nothing on this theme puts body
text on either.

---

## 2. Every hardcoded colour found

**77 colour literals outside token definitions, across 48 distinct values.** Counted mechanically:
comments stripped, `var(--x, #fallback)` fallbacks excluded (those read the variable and are not
hardcodes), and declarations of a token's own value excluded.

They fall into four groups.

**Group A, already theme-scoped and correct (about 30).** Miami's sand gradient, Maria's blush
gradient, the NYC gold and verdigris accents. These sit inside a `body[data-theme="..."]` block
and only ever apply to their own theme. No action.

**Group B, already carrying a `body.t-light` override (at least 4).** `.sw-axis`,
`.sw-ring-outer`, `.kn-h-art .kn-num`, `.kn-sec-num`. `applyTheme()` adds `t-light` for this theme
as it does for Miami and Maria, so these corrected themselves. No action, and this is why the
class exists.

**Group C, theme-blind and broken on a white page. Fixed.**

| Where | Literal | Why it breaks | Fix |
|---|---|---|---|
| `.nav-logo-img` | `drop-shadow(... rgba(63,202,166,.28))` | a teal glow tuned for a dark field, reads as a smudge on white | `filter: none` on this theme |
| `.blip.selected .blip-label` | `fill: #eef1f7` | near-white label on a now-white stage: invisible | `fill: var(--heading)` |
| `.scatter-legend-pill.active` | `background: rgba(255,255,255,.04)` | a white wash on white is no wash at all | `var(--surface-soft)` plus a border |

All three are corrected **scoped to `body[data-theme="plain"]`**, not in the shared rule. Changing
the shared rule would alter Miami and Maria, and nobody should find their interface changed
because a theme was added for somebody else.

**Group D, theme-blind and still hardcoded, not fixed (about 40).** Mostly shadows and scrims:
`rgba(0,0,0,.35)`, `rgba(0,0,0,.5)`, `rgba(3,10,20,.55)`, `rgba(0,0,0,.6)` text-shadow, and the
`#64748b` slate used for parked spider labels. They are dark-on-anything, so they are legible on
this theme; they are simply heavier than a plain theme wants. Also `#fff` in twelve places, mostly
ink on a filled control, which is correct here. **These are a finding, not a defect**, and they are
listed so the next pass has the inventory rather than re-deriving it. The one to look at first is
`.theme-switch button.active { color: #fff }`, which is dead code: the switcher has been the
fly-out pills since the dock was built.

---

## 3. Status does not depend on hue

The platform already had the machinery and this theme leans on it rather than inventing a second
scheme: `linStatusLetter()` gives C/G/Y/A/R, `linStatusShape()` gives circle, triangle, diamond,
square, ring, and both are already consumed by the map pins, the flow diagrams and the category
dots.

What the suite asserts, and what a fault proved:

- **Five statuses, five distinct shapes.** The check compares the five `.status-dot-*` shape
  declarations against each other rather than asserting any particular one, so it fails if any two
  collapse. Giving Yellow the Amber diamond drops it to four distinct and the suite goes red.
- **The legend names each status in words.** Read out of `LEGEND_BANDS` in `app.js`, so blanking
  "Amber" turns it red.
- Yellow `#6f5200` and Amber `#9a4700` remain close, as they must once both are darkened enough
  to pass AA on white. That is exactly why the label is mandatory and why nothing here shows a
  bare coloured dot.

---

## 4. Research participants cannot change theme

Enforced in three places, and the redundancy is deliberate.

1. **`gate_action`, before dispatch.** `themeset` is in `RESEARCH_FORBIDDEN_ACTIONS`, refused for
   a research account, audited as `theme_change_denied`. `themeget` is deliberately **not** gated:
   a participant may ask what it renders and is told the fixed theme.
2. **`a_themeset` itself** refuses again. A handler that assumes an upstream gate is a handler
   that breaks silently the day the gate is refactored.
3. **`resolve_theme` ignores the stored column entirely** for a research account. A row written
   before this existed, written by an administrator, or left behind when an account changed type,
   is not honoured.

The fixed theme is `newyork`, the existing default, not the new one: participants have been
seeing it throughout and the study's stimulus should not move because a theme was added for
operational users.

The interface leaves the pills out when the server says `fixed`, and `themeFixed` **defaults to
true**, so a failed or pending round trip hides the control rather than offering four buttons that
would be refused.

**A refactor this required.** The pre-dispatch gate wrote one audit event and one sentence for
every forbidden action. A refused theme change would have been recorded as `project_creation_denied`
and the participant told about projects. The gate now looks the reason up per action, with a
fallback for anything added to the set later.

### The check that could not fail, and how it was found

Removing `themeset` from `RESEARCH_FORBIDDEN_ACTIONS` left the whole suite **green**, because the
handler's own refusal caught it. That is defence in depth working correctly and a check that
cannot see half of what it claims to cover. Two checks were added: one asserting the outer gate
structurally, and one calling `a_themeset` **directly**, which is the only way to reach the inner
layer with the gate bypassed. Both now go red under their own fault.

---

## 5. What else changed

**The caption above Radar, Map and Globe is removed, with no replacement.** It read:

> Each project is a blip on the scope. Distance from center is drift from baseline; angle is
> delivery sector. Select a project to see its signal ledger, the signal-conflict classification,
> and the governance decision, with explicit authority, documentation, and a contractor fairness
> gate where required.

It sat above the stage, so all three views showed it, and distance and angle mean nothing on the
Map or the Globe. It also promised capability that does not exist: the decision card it pointed at
was dead code keyed on retired category ids, and the fairness gate was removed on 2026-08-02
because it read a field nothing writes. Confirmed gone from the rendered text, both phrases.

**The globe's sea.** The other light themes tint the photographic Earth with `#0e3049`, and
`material.color` multiplies the texture, so a near-black tint darkens it further: on a white page
that is the hole the brief describes. This theme uses the abstract treatment instead, so the sea
is a flat colour the stylesheet controls rather than a texture multiplied into darkness. Sea
`#a9c6da`, land `#3f6478` (3.56), graticule `#41637a` (3.58), worst marker 3.46. **Nothing outside
this theme's block was touched, so the dark themes are unchanged by construction.**

**The logo sweep needs no change, and that is a measured result rather than an assumption.** I
sampled the artwork under the sweep's own radius, 576 points across its full extent: **zero
transparent samples**, mean `rgb(81,84,99)`, luminance 0.09. The sweep lies entirely on the
wheel's own dark radar face, which is a raster that does not vary with the theme, so its backdrop
is identical in every theme and the bright core sits at 6.83:1 against it. The page colour behind
the logo never shows through the sweep.

**The dock: all four icons now animate.** All four already had an ambient rule declared, running
and infinite. Two of them animated a property whose visible amplitude was near zero.

- **Handbook.** `dock-book-breathe` was `rotateY(-13deg)` with no perspective, which is not a
  hinge: it degenerates to `scaleX(cos 13°)`. Measured, not argued: computed matrix
  `a=0.9744 b=0 c=0 d=1`, bounding box 12.000px to 11.692px. **The entire animation was 0.308
  pixels.** Adding `perspective(70px)` makes it a real swing about the spine, the same gesture as
  the hover page-turn, and opening the angle to 26 degrees gives **1.891 pixels**, about 7.3% of
  the icon.
- **Menu emblem.** The blip dot renders about 3.3px across and `dock-amb-blip` moved it 0.36 of
  alpha. It now uses `dock-amb-pulse`: the same blip gesture with the alpha opened to 0.38 to 1.0
  and a slight scale, which is what a return on a scope does.

Both are transform and opacity only, so they are theme independent, and both were already covered
by the existing `prefers-reduced-motion` block, which sets `animation: none` on `.book-closed` and
on the menu emblem circle.

---

## 6. What I verified, and what I could not

**Compositing is unavailable in this container**, as recorded: the document timeline reads 0 and
`requestAnimationFrame` does not fire. **I did not see this theme. Nothing below is a claim about
how it looks.**

### A trap worth recording: transitions freeze computed values

`body` carries `transition: background .35s, color .35s`. With the timeline frozen, both
`CSSTransition` objects sit at `currentTime: 0` **and never advance**, so `getComputedStyle(body)`
returned the *previous* theme's background and colour indefinitely. My first surface read reported
`rgb(10,14,18)` on a white theme and looked like a straightforward failure. It was not: with
`transition: none` the same element snaps to `rgb(245,246,248)` and `rgb(26,29,35)`, exactly the
theme.

**Any computed-style read of a transitioned property in this container is stale.** Every reading
below was taken with transitions suppressed. A session that skips this will report a false failure,
or worse, a false pass in the other direction.

### Verified by computed style, with the theme applied

`body`, sign-in panel, sign-in title, sign-in subtitle, the approved research notice, access-denied
panel, consent panel, consent draft banner, topbar and its border, nav logo filter, portfolio intro
heading and eyebrow, the radar panel, stage buttons in both resting and active states, the status
legend, the decision card, the handbook panel, the workspace panel, tables, form inputs, primary
buttons, and the footer copyright and attribution.

### Not observed

- **How any of it looks.** No screenshot, no rendering. Contrast is arithmetic on the declared
  colours, not a judgement about the result.
- **Project detail, administration, the Files tab, the assistant, and the knowledge pages.** Their
  panels are built by JavaScript at run time and were not in the DOM without authentication and
  data. They read the same `--surface` / `--text` / `--line` tokens as the panels that were
  verified, but I did not confirm that by computed style and am not claiming it.
- **The exports' own surfaces.** The XLSX workbook has no CSS; the notice sheet it carries is
  unchanged by this work.
- **Map tiles.** `onMapThemeChange()` swaps an OpenFreeMap style and this theme now resolves to
  the light one, but the map was never mounted here.
- **That the dock icons and the logo sweep move.** Their amplitudes are measured; their motion is
  not observed.

---

## 7. Verification

`server/tools/test_theme_plain.py`, **63 checks**, four guarantees: the contrast, the status
encoding, the fixed theme for research accounts, and the server refusal.

| Fault injected | Detected |
|---|---|
| A status colour lightened until it fails AA | yes, 1.30 against 4.5 |
| Body text lightened until it fails AA | yes, 2.58 |
| Yellow given the Amber shape, so only hue separates them | yes, 4 distinct of 5 |
| The legend stops naming Amber in words | yes |
| A research account served its stored theme instead of the fixed one | yes |
| The pre-dispatch gate stops listing `themeset` | yes |
| The handler's own refusal removed, gate bypassed | yes |
| The globe sea returned to near-black | yes, 4 checks red |
| The archived theme becomes storable | yes |

Every fault was confirmed to have applied before the result was believed, and the baseline was
re-run after each one.

**Two harness faults, both of the kind this run keeps hitting.** A needle written with `\n` matched
nothing in a CRLF file and reported "found 0" rather than patching something adjacent. And the
globe fault's **revert** needle, `#0e3049`, already existed in the Miami and Maria blocks: it
matched three places, the harness refused, and it left the fault applied. The abort is what caught
it; the file was repaired and the fault rewritten with a marker value that exists nowhere else.
A revert needle has to be as unique as the injection needle.

### Suites

- **Server: 30 suites, 1634 checks, 0 failures**, against a throwaway SQLite built by
  `alembic upgrade head`. Never pointed at production.
- **`tests_render.html` 62/62** and **`tests.html` 51/51**, in the browser.

---

## Files changed

- `assets/css/radar.css` — the `plain` token block, the page and topbar rules, three theme-blind
  colour corrections, the dock keyframe fixes.
- `assets/js/app.js` — theme registered and offered, `t-light` extended, the server sync, the
  fly-out persisting and standing down when fixed.
- `index.html` — the caption removed.
- `server/app/theme.py` — new. Vocabulary, resolution, `themeget` and `themeset`.
- `server/app/features.py` — `themeset` gated; per-action refusal reasons.
- `server/app/main.py`, `server/app/research_models.py` — dispatch and the column.
- `server/alembic/versions/0017_participant_theme.py` — new, one nullable column.
- `server/tools/test_theme_plain.py` — new, 63 checks.

## Flagged

- **The remaining hardcoded shadows and scrims (Group D).** Legible on this theme, heavier than it
  wants. An inventory, not a defect.
- **`.theme-switch` is dead code.** The switcher has been the dock fly-out for some time.
- **Miami's globe sea is still `#0e3049`.** It has the same near-black sphere on a pale page that
  prompted this work, but changing it would alter an existing theme's appearance and its own
  comment records a Red contrast floor that the value was chosen for. Yours to decide.
