# Training projects leave the portfolio, and a section navigator lands on project detail

2026-08-10. Branch `claude/training-projects-portfolio-jrorzf`.

## Part 1 — every portfolio surface that was counting/listing training projects

The training-gating report (`REPORT_2026-08-04_training-gating.md`) built the flag, the gate, and
isolation for the research export and research chain, and explicitly flagged the portfolio as
**not decided**: "whether a training project should appear in an *operational* cross-project view
... is a product decision ... and is flagged here rather than decided." This run makes that
decision: training projects leave the portfolio entirely.

**One fix closes every surface at once**, because every portfolio-facing surface reads from the
same two server actions. `a_list` and `a_listslim` (and `a_listarchived`) all call the shared
`_ordered()` helper in `server/app/facade.py`, and the client's `window.LIN_PROJECTS` — the single
in-memory mirror every rendering surface reads — is populated *only* from those two actions'
responses (`assets/js/store.js`'s `hydrate()`). So the training filter was added once, at the
source:

```python
return session.scalars(
    select(Project)
    .where(Project.archived == archived, Project.is_training.is_(False))
    .order_by(Project.created_at, Project.legacy_id)
).all()
```

**Surfaces this closes, all of them fed from `LIN_PROJECTS` and traced by source-read before the
fix, confirmed absent after it, in a real browser:**

- The project list (rows/cards) on the portfolio page.
- The status legend counts (Green/Yellow/Amber/Red/Awaiting analysis tallies) — `signals.js` and
  `app.js` compute these by iterating `LIN_PROJECTS`.
- The map, radar, and globe stage views — all three read project location/category data from
  `LIN_PROJECTS`; a training project can no longer be placed, counted as placed, or counted as
  unplaced.
- Portfolio Health's client-built aggregate snapshot (`buildPortfolioHealthSnapshot()` in
  `signals.js`) — it filters `window.LIN_PROJECTS`, so a training project can no longer appear in
  the stored `portfolio_health.json` snapshot or its `projectCount`.
- The archived-projects listing (`listarchived`), for the same reason, for archived training
  projects.

**Portfolio Health's "too small for anomaly detection" pool threshold: it WAS counting training
projects, and now it is not.** `runPortfolioAnalysis()` in `signals.js` builds its pool from
`window.LIN_PROJECTS` (`list.map(portfolioVector).filter(Boolean)`) and refuses to run
(`cat8Insufficient("Need 3+ projects with signal data for portfolio analysis")`) when that pool has
fewer than 3 entries. Before this fix, a training project with `signalInputs.cpi` set (which the
training loop produces through the normal computation path per `REPORT_2026-08-04_training-loop.md`)
counted toward that pool exactly like a real project — so a portfolio with two real projects and
one training project would clear the 3+ threshold and run anomaly detection using training data as
one of its three inputs. The single-source-of-truth fix above closes this the same way it closes
everything else: the training project never enters `LIN_PROJECTS`, so it never enters the pool.

**What stayed untouched, deliberately:** the research-export isolation filter in
`server/app/research_export.py` (`build_module_results_rows`'s unconditional `if project.is_training:
continue`), which is a *different* filter for a *different* surface (the research export, not the
portfolio) and was proven still working, independently, in the new test below.

**Reachability:** the Train tab (`[data-nav="training"]`) does not go through `a_list`/`a_listslim`
at all — it drives its own `trainingstate` action and the training page's own state machine — so it
was never touched by this fix and remains reachable exactly as before.

## Part 2 — the detail-page section navigator

Added `#detail-secnav`, a second, left-side floating menu bar on the project detail page, styled
and positioned the same way the existing right-side `.icon-dock` already is: `position: fixed`,
outside the `.app` container's own width calculation, so it adds zero pixels to `.app`'s
`max-width: min(2100px, 96vw)` on desktop. Verified in a real browser: `.app`'s bounding box is
identical (`x: 28.8px, width: 1382.4px` at a 1440px-wide viewport) whether the nav is present or
not.

**What it is:** a slim rail of numbered circular dots — one per collapsible section, in page
order — collapsed by default so it never has to be wide enough to sit over real content; each
dot's label appears as a transient hover/focus flyout (the same `.dock-label` pattern the existing
dock already uses), not a permanently-open panel.

**Built from the live DOM, not a hand-maintained list.** `buildSectionNav()` in `assets/js/detail.js`
reads `.collapse-section` elements straight out of the rendered `#detail-root` and their
`.collapse-title` text after `render()` builds them, so the navigator can never drift out of sync
with the sections `render()` actually produced, whatever order or set they end up as. It also means
labels are exactly what each section already displays — the purpose-only names `cs()` calls were
passing (Location, Project Signal Network, Signal Flow, Executive Brief, Governance Decision,
Signal Web, Signal Inputs, Documents & Extracted Signals, Ensemble Analysis, Period Comparison; 10
sections as currently rendered — the "Signal Stack" section named in
`REPORT_2026-08-05_surface-inventory.md` no longer exists in the source, confirmed by grep before
building this) — never a module id or number, per `NAMING_AUTHORITY.md`.

**Click behaviour:** expands the section first if folded (calling the existing `toggleSection()`),
then `scrollIntoView({behavior: "smooth", block: "start"})`.

**Scroll-spy:** an `IntersectionObserver` over all `.collapse-section` elements
(`rootMargin: "-15% 0px -60% 0px"`) tracks which section is most in view and highlights its dot.

**Mobile:** `@media (max-width: 700px) { .detail-secnav { display: none; } }` — the same breakpoint
`.icon-dock` already repositions at — collapses/hides the navigator entirely rather than reserving
any width, per the brief (mobile decision-sequence work elsewhere was desk-only; this one had to
handle mobile explicitly).

**Sections do not reorder or rename.** No section's `cs()` call, position, or title text was
touched.

## Verify

**A new suite, `server/tools/test_training_portfolio_isolation.py`, 13/13**, proving:

1. A training project (marked `is_training=True`, with a real `ComputedResult` row, with explicit
   membership so the only reason it could be absent is the training filter) is absent from `list`,
   `listslim`, and `listarchived`, while a real project in the same account is present in all
   three.
2. **The check can fail**: unmarking the training project (`is_training=False`) makes it appear in
   `listslim`; re-marking it makes it disappear again — proven against the live server, not read
   from source.
3. Research-export isolation (`build_module_results_rows`) still excludes the training project and
   still includes the real one, independently of the portfolio-list fix.
4. `trainingstate` still answers for the operational caller — the Train tab's route stays open.

**Fault injection, confirmed red then reverted clean.** Removed the `is_training.is_(False)` clause
from `_ordered()`: 4 distinct checks went red (`list`/`listslim`/`listarchived` all showed the
training project, and the re-mark-absent check failed because the project stayed visible) — 9/13.
Reverted byte-identical (`diff` against a pre-fault backup, clean); suite back to 13/13.

**Full server suite: 55 files, 3022/3022**, fresh SQLite per file, `alembic upgrade head`
including migration 0025. `tests.html`: **51/51**. `tests_render.html`: **286/287** — the one red
is `production read path: exercised against the server`, the same pre-existing gap
`REPORT_2026-08-04_training-gating.md` and `REPORT_2026-08-10_map-and-module-count.md` both
documented (it needs a real signed-in session token pasted manually into that tab; not caused by
this run, not a defect this run introduced). No test in any of the three suites went red for a
reason other than a fault this run deliberately injected and then reverted — no real defect was
caught and left unresolved.

**Driven in a real headless-Chromium browser (Playwright, SwiftShader WebGL), both themes, against
the actual dev server**, not inferred from code:

- Seeded three real projects and one training project (with a computed result) under one
  operational account. The portfolio list showed exactly the three real projects; the status
  legend's "Awaiting analysis" tally read 3, not 4; `console.log` from the app itself confirmed
  `Projects loaded: 3 [DEMO-001, DEMO-002, DEMO-003]`.
- Clicked into the Train tab: the training page rendered its own content
  ("Training mode... A practice project to decide against, separate from any real project and
  never part of the research record"), confirming the Train tab reaches the training surface
  independent of the portfolio list.
- Opened a real project's detail page: the navigator showed 10 dots for 10 sections; clicking dot
  4 expanded "Executive Brief" and scrolled it into view (`class="collapse-section open"`,
  landed within the viewport); `.app`'s bounding box was unchanged from the portfolio page's.
- Repeated in the operational light theme (Fairbanks/plain) and the NYC (dark) theme — the
  navigator uses the same CSS custom properties (`--surface`, `--line`, `--phosphor`, etc.) the
  existing `.icon-dock` already uses, and rendered correctly, gold-highlighted active dot, in
  both.
- At a 390x844 mobile viewport, `#detail-secnav` computed `display: none` — hidden, not narrowed.

## Files touched

- `server/app/facade.py` — the single-source-of-truth training filter in `_ordered()`.
- `server/tools/test_training_portfolio_isolation.py` — new suite (13 checks).
- `index.html` — added `<nav id="detail-secnav">` beside `#detail-root`.
- `assets/js/detail.js` — `buildSectionNav()`, wired at the end of `render()`.
- `assets/css/radar.css` — `.detail-secnav` and related rules.

## Git state

Branch already contained the latest `origin/main` (fast-forward check passed:
`git merge-base --is-ancestor origin/main HEAD`). All three suites green (modulo the one
pre-existing, unrelated gap). Merged and pushed per the standing instructions; see the PR opened
for this branch for the final state.
