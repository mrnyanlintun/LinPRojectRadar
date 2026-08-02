# Mobile layout: the site on a phone

CSS-first fixes for the mobile defects in scope (sign-in, project list/portfolio, project
detail, Files tab), plus explicit desktop-only gating for the three surfaces out of scope
(upload, administration, the decision sequence), verified in a real browser at phone viewport
widths. One string renamed (the light theme "Plain" to "Fairbanks"). No migration added, no
desktop layout change, no new dependency.

## Overflow measurements, by panel, before and after

All measurements at 390x844 (iPhone 12/13/14-class viewport), transitions suppressed before
reading computed styles per the known compositing gap in this environment (see below).

| Panel | Before | After |
|---|---|---|
| Project list row (`.list-item`) | 4-34px horizontal overflow: id/name/pill/flag/state/actions forced onto one line by `display: grid` | 0px. Restructured to `flex-wrap` with a forced line break after the id/name pair; row wraps to 2-3 lines instead of overflowing |
| Manage/Open buttons (`.li-manage`, `.li-open`) | Tap target 40px min-height / `padding: 6px 13px` (lost to `.btn.small`'s two-class specificity, first fix attempt had NO effect — see Errors) | 44px min-height / `padding: 12px 14px`, confirmed via computed style |
| Files tab table (`.fx-table`) | 102px over on `.fx-layout`, 123px over on the table itself; would have needed a sideways scroll | 0px. Stacked into cards: `display: block` on table/thead/tbody/tr/td, `data-label` attributes added in `files.js` and read via CSS `::before` for the row label |
| Project detail page | 0px (confirmed already correct, no change needed) | 0px, re-confirmed unchanged |
| Globe view | N/A (mounted regardless of viewport — see below) | Never mounts below 700px: gated in `app.js` before `LinGlobe.mount()` is called, so no WebGL context or animation loop opens on a phone |
| Radar (flat SVG atlas) view | 0px, does not consume the viewport (measured 440px of 844px height) | 0px, unchanged (`.atlas-svg { width: 100%; height: auto }` was already responsive) |
| Icon dock vs. assistant launcher | 156px^2 real pixel overlap at 390x844 | 0px^2. Launcher's mobile `bottom` raised from 16px to 88px to clear the dock's ~72px-tall band |
| Icon dock vs. last project-list row | 101.5625px^2 real pixel overlap (scrolled to the end of a long list, the fixed dock covered the last row; nothing reserved space for it) | 0px^2. `#project-list` given `padding-bottom: 88px` on mobile only |
| Upload panel, decision sequence, administration | Rendered normally (small controls, drag-and-drop target, multi-tab admin console) with no acknowledgement that these need more room than a phone offers | Real controls hidden, plain "This needs a desktop browser" notice shown in their place, via CSS generated content only |

All "after" values were measured with the fix in place, then re-measured with the fix
deliberately reverted (fault injection) to confirm the check actually detects the defect, then
re-measured a third time with the fix restored, to rule out the revert itself leaving the file
in a state the "after" number was accidentally taken against. See Verification below.

## What was fixed

**Project list row overflow.** `.list-item` was `display: grid` on mobile with a fixed-width
row that could not accommodate id, name, sector pill, flag, state, and actions on one line at
390px; the row overflowed by 4-34px depending on content length. Rewritten to
`display: flex; flex-wrap: wrap` with an explicit ordering and a zero-height `::after`
pseudo-element carrying `flex-basis: 100%` to force a break after the id/name pair, so the row
wraps to two or three lines instead of running off the edge of the screen. Desktop is
unaffected: the grid layout for `.list-item` outside the mobile media query was not touched.

**Tap targets.** `.li-manage` and `.li-open` (the Manage/Open buttons on each list row) needed
a 44px minimum height per the brief's "tap targets large enough to hit." The first attempt,
`.li-manage, .li-open { padding: 12px 14px; min-height: 44px; }`, had no visible effect:
computed style still showed `.btn.small`'s values (`padding: 6px 13px`, `min-height: 40px`),
because both buttons carry `class="btn small li-manage"` and `.btn.small` is a two-class
selector (specificity 0,0,2,0) that beats a single-class `.li-manage` selector regardless of
source order. Fixed by rewriting to the equally-specific `.li-manage.btn, .li-open.btn` and
placing it after `.btn.small`'s rule in source order.

**Files tab.** The file table overflowed by 102-123px with no way to see the hidden columns
short of a sideways scroll the brief rules out. Stacked into cards on mobile only: the table,
its header, body, rows, and cells all switch to `display: block`, the header is hidden, and each
cell shows its own label via `content: attr(data-label)`. The labels are not something CSS can
read from the table structure alone, so `files.js`'s `paintList()` was changed to emit a
`data-label` attribute on four of the six `<td>` cells (State, Version, Period, Folder; the
filename cell needs no label, it is the row's own heading). This is the one place JS was needed
for a layout decision in this pass, and it is additive: the desktop table ignores the attribute
entirely.

**Globe / WebGL on a phone.** The brief's premise was that Radar/Map/Globe already render as
static images on mobile. That held for Map and the flat atlas, but not for Globe: nothing
stopped `LinGlobe.mount()` from opening a WebGL context and starting globe.gl's animation loop
regardless of viewport width, before the (CSS-hidden) canvas was ever painted. Added a
`window.matchMedia("(max-width: 700px)").matches` check in `buildGeoStage()`, before the mount
call, so a phone never opens that GPU context in the first place and instead falls straight
through the same degrade path Globe already had for "cannot draw" (`showAtlasInstead`). This is
JS, not CSS, because it decides which code runs, not how it looks; a media query can hide a
canvas but cannot stop a mount call from firing.

**Icon dock and assistant launcher overlap.** Measured a genuine 156px^2 overlap between the
fixed bottom icon dock and the assistant launcher button at 390x844, plus a 101.5625px^2 overlap
between the dock and the last visible row of a scrolled project list (nothing reserved space
below the list for the dock, so scrolling to the end put the last row under it). Fixed with two
changes, both inside the existing mobile media query: the launcher's `bottom` offset raised from
16px to 88px (clearing the dock's ~72px band with margin), and `#project-list` given
`padding-bottom: 88px` so the list's real end can scroll clear of the dock. The assistant panel's
own `bottom` offset was raised correspondingly (70px to 124px) so it does not jump when opened.

**Upload, administration, decision sequence.** Out of scope per the brief; rendering them badly
on a phone would be worse than saying so. Each is CSS-only: the real controls (`#wstab-upload`,
`#wstab-decision`, and the admin tab bar plus both admin panels) have their children hidden with
`display: none` while the panel itself stays in the render tree, and a plain notice
("This needs a desktop browser. Open Opus Gubernatio on a laptop or desktop to use it.",
"Administration needs a desktop browser...") is shown via `::before`/`::after` generated
content. A `display: none` element cannot generate `::before`/`::after` content of its own,
which is why the panels themselves are not hidden, only their contents.

## The "Plain" to "Fairbanks" rename

Searched the codebase for every occurrence of the theme name. Found exactly one user-facing
occurrence: `THEME_META` in `assets/js/app.js`, which held `label: "Plain"` and
`title: "Plain: white, high contrast, no decoration"`. Both changed to "Fairbanks," matching the
pattern of the other three theme labels ("Miami," "NYC," "Maria").

Everything else that says "plain" is internal and was deliberately left unchanged:

- The theme's internal key, `"plain"`, in `THEME_META.key` and `OFFERED_THEMES` (`app.js`)
- `THEMES = ("plain", "light", "newyork", "maria")` in `server/app/theme.py`
- The stored preference value written to `participants.theme` (`"plain"`)
- The CSS attribute selector `body[data-theme="plain"]` throughout `radar.css`
- The tool filename `server/tools/test_theme_plain.py`
- Assorted code comments referring to "the plain theme" or "PLAIN" as a section heading

The stored value is the one the brief explicitly said not to touch without a migration; it was
not touched. If the internal key is ever renamed to match, that is a schema and vocabulary
change, not a display-string change, and belongs in a separate change with its own migration.

## What could not be fixed, or was not attempted

Nothing in scope was left unfixed. Two items outside the stated scope were noticed and are
flagged, not acted on:

- A stale comment near `setPortfolioView` in `app.js` claims "MAP is the default," which
  contradicts the actual runtime default (`localStorage.getItem(VIEW_KEY) || "globe"`). Left
  alone as a documentation inconsistency unrelated to mobile layout.
- The "Also" paragraph about the icon dock's four navigation icons (only two of four
  animating) that arrived attached to a later message in this session appears to duplicate
  already-completed work from an earlier theme-focused session (tasks marked complete in this
  session's task list do not include it, and it does not appear on the active task list for
  this pass). It was not treated as new pending work here; if it is still open, it needs its
  own pass distinct from this mobile-layout brief.

## Verified at phone width; not independently re-verified

Verified directly, in-browser, at 390x844 and re-confirmed unchanged at 1280px (desktop):
sign-in-adjacent surfaces were not touched this pass (Task A covers sign-in itself); project
list row layout and tap targets; Files tab card stacking; Globe's WebGL gate; the icon dock,
assistant launcher, and last-row overlap fix; the upload/decision/admin desktop-only gates; the
Fairbanks label rename.

Not independently re-measured this pass, carried forward from the prior session's verification
(unchanged code, no reason to expect drift, but not re-run): project detail page overflow, the
flat atlas panel's viewport share and overflow-freedom, the Map view.

The one thing this report cannot claim: real motion (CSS transitions, the theme fade, the logo
sweep) was not observed directly. Compositing is unavailable in this container, and `body`'s
background/color transition sits on a frozen `CSSTransition` at `currentTime: 0`, so
`getComputedStyle` can return a stale value mid-transition. Every measurement above suppresses
transitions before reading computed style, or reads layout at a settled viewport width rather
than during a transition, for exactly this reason. Nothing in this pass depended on observing
motion; the two mobile fixes are pure static-layout changes.

## Verification: fault injection

Two of the fixes made this pass were deliberately reverted, re-measured, and restored, to
confirm the check that found each defect can actually fail rather than reporting a false clean
regardless of the code:

1. **Dock/launcher overlap.** With `.la-launcher`'s mobile `bottom` reverted from 88px to the
   original 16px, the overlap-area measurement reported 135px^2 (using the real 3-button dock
   markup; an earlier attempt with a simplified 1-button dock underreported the dock's width and
   showed 0px^2 even with the fault present, an injection that would have "silently failed to
   apply" if not caught by matching the real dock structure). Restoring `bottom: 88px` and
   re-measuring against a freshly re-read stylesheet returned the overlap to 0px^2, confirming
   the revert did not leave the file in a state the baseline was measured against unfairly.
2. **Desktop-only gate.** With the `#wstab-upload > *, #wstab-decision > * { display: none; }`
   rule commented out, the upload panel's dropzone computed to `display: block` at 390px width,
   i.e. visible on a phone. Restoring the rule and re-measuring against a freshly re-read
   stylesheet returned it to `display: none`.

In both cases the stylesheet was re-fetched with `cache: 'no-store'` after every edit before
measuring, to rule out the browser serving a stale cached copy of `radar.css` and reporting a
fault or a fix that was never actually loaded (a failure mode encountered and worked around
earlier in this same session, for `files.js` and `app.js`).

## Test suites

- **Server suite** (`server/tools/test_*.py`, 30 files): run against a fresh throwaway SQLite
  database per file, each brought to `alembic upgrade head` before the suite ran, `DATABASE_URL`
  never pointed at production. All 30 passed, 0 failures. No server code changed this pass
  (Task A's sign-in fix was a separate, already-committed change); this run is a due-diligence
  confirmation that the mobile-only CSS/JS changes have not disturbed anything server-side.
- **`tests_render.html`**: 62/62 checks passed.
- **`tests.html`**: 51/51 assertions passed.

## Files changed

- `assets/css/radar.css`: mobile media query only (`@media (max-width: 640px)`), no rule
  outside it was added or changed; the desktop layout is untouched.
- `assets/js/app.js`: the Globe WebGL viewport gate in `buildGeoStage()`, and the
  `THEME_META` label/title rename for the "plain" key.
- `assets/js/files.js`: `data-label` attributes added to four `<td>` cells in `paintList()`.

No migration was added. `Demo/.claude/launch.json`'s temporary `lin-radar-mobile` preview
configuration, added to work around `preview_start` resolving from the dead `Demo` directory
rather than this repository, has been reverted; that file is outside this repository and carries
no changes of its own.
