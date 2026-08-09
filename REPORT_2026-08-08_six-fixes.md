# Six fixes: the period reaches the surface people use, and the recommendation states its rule

**Date:** 2026-08-08
**Branch:** `claude/six-fixes-1nfjnx`, from `origin/main` at `a9464da`
**Model:** Opus

**Verification:** server suite **50 suites, 2664/2664** (fresh migrated SQLite per test file; the
new `test_six_fixes.py` adds 38). `tests.html` **51/51**. `tests_render.html` **208/209**, four
net new checks, the one red being the pre-existing auth-gated "production read path" check that
is red on `origin/main` too. Real browser drives of all six. Two faults injected, each confirmed
applied, each detected, each reverted with a SHA-256 comparison and the baseline re-confirmed.

**No migration was added.** Unapplied in production, unchanged: **0020, 0021, 0022, 0023.** No
`DATABASE_URL` pointed anywhere but throwaway SQLite. Production was neither inspected nor
queried. **Nothing under `server/app/simulation/` was modified.**

---

## LEAD 1: why the period assignment did not land

**The selector was not on the upload surface people actually use, and my previous report said so
in as many words.**

The previous task placed the selector on the Workspace "Period documents" panel and the Files
tab, and recorded the third surface as *"the project detail single-document ingest — not
changed, and reported."* That third surface is the one a project manager reaches: the detail
page's **Upload documents** button calls `LinIngest.openUploadModal`, which mounts
`LinSignals.dropzoneHtml` and posts `extractsignals`. That dropzone had a project picker and no
period control, and the payload carried no period, so `_resolve_period` defaulted every document
to 1. The same page's own control then reported exactly what was observed:

```
1 period(s) recomputed: period 1 (27 document(s) added since the last computation)
```

So the recompute half worked correctly on a partition that had never happened. It was reporting
the truth about a period that wrongly held 27 second-period documents.

**The server was never the problem.** `a_extractsignals` does `upload = dict(payload)` before
delegating, so `period` and `period_end` travel the moment the client sends them. Confirmed
directly: `extractsignals` with `period: 2` files to period 2 and the store shows `{2: 1}`.

**The fix is on the client only:** the same two controls the other surfaces carry, added to
`dropzoneHtml` (which serves both the detail modal and the Signals tab), read per dropzone
container so the two instances do not read each other's fields, and sent with every document.

### What the project computes as now

Driven in a real browser through the detail page's own upload dialog: period 1 already computed,
then two documents stated to period 2.

```
DOCUMENTS PER PERIOD: {1: 1, 2: 2}
ALL-PERIODS: periods=[1, 2] computed=1 skipped=1
  period 1: documents unchanged since last computation; result left untouched
  period 2: computed for the first time
```

**Two periods, not one.** Period 1 keeps its single document and is skipped; period 2 computes
from its own two.

**The invariant holds, and it is proved rather than asserted.** `test_six_fixes.py` captures
period 1's stored bytes before the second period exists, computes period 2, and asserts period 1
is byte-identical afterwards **and keeps its `result_id`** — so it was genuinely left alone
rather than superseded and rewritten with identical content. That second half matters: an earlier
session found that a payload comparison alone passes even when a period is needlessly rewritten.

## LEAD 2: what actually sets the recommendation, and which option I took

**The rule is in `simulation/models_gov.py`'s regret module, and it is a threshold on the
period's own cost and schedule performance:**

```
1. score the three courses from a fixed payoff matrix over fixed future probabilities
2. take the lowest-scoring course
3. THEN OVERRIDE IT:
     cost or schedule performance below 0.88  -> escalate
     else either below 0.95                   -> investigate
```

**I took option 1: the rule is stored and stated.** It was retrievable, so the card now says why.

Driving the real module across the range establishes two things, the second of which is worse
than the brief supposed:

| cost / schedule | scores | recommended |
|---|---|---|
| 1.05 / 1.05 | `{monitor: 11, investigate: 5, escalate: 8}` | investigate |
| 0.92 / 0.99 | `{monitor: 11, investigate: 5, escalate: 8}` | investigate |
| 0.84 / 0.88 | `{monitor: 11, investigate: 5, escalate: 8}` | escalate |
| 0.50 / 0.50 | `{monitor: 11, investigate: 5, escalate: 8}` | escalate |

**The scores are identical for every project and every period.** The payoff matrix and the future
probabilities are literals with no input dependence, so `expected_regret` is `11 / 5 / 8` on
every result this platform has ever stored. The card called them *"the courses of action the
analysis scored for this period"*, which told a reader their own evidence produced those numbers.
Nothing did. They rank the courses; they are a property of the method, not a finding about the
project — and the recommendation is not taken from them at all.

So two corrections were needed, not one, and the second follows directly from establishing the
first: the card must state the rule, **and** stop presenting a constant as a per-period finding.
A card that explained its recommendation while still implying the scores were about this project
would have traded one false impression for another.

**Where the rule lives.** `server/app/recommendation_basis.py`, served on `projectresults` as
`recommendation_basis` and rendered by the card. The thresholds are **mirrored** rather than
imported, because they are inline literals inside the module's function body with nothing to
import and `simulation/` is out of scope for modification. A mirror is only honest with a
safeguard, so `test_six_fixes.py` section 3 drives the **real module** across each threshold —
including exactly *at* each boundary, since the comparison is `<` and not `<=` — and asserts the
branch this file predicts is the branch that actually fires. Fault 1 below proves that catches a
drift.

### The Courses of action block, as it now renders

Read back from the real page. Stored figures: cost performance 0.909, schedule performance 0.938,
eightieth percentile estimate at completion 13,970,165 at 16.4 per cent above budget.

```
Courses of action

These are the courses of action open to you, each with what it costs, what it closes off, and
what it protects. Where the platform does not hold what would be needed to state a consequence,
it says so instead of asserting one. The recommendation follows the options, so the choice stays
yours.

The scores below rank the courses by worst case and are the same for every project: they come
from the method, not from this period's evidence. What decides the recommendation is stated with
it.

Keep the project under routine monitoring

Carry the position into the next reporting period unchanged and record the signals as they stand.

What it costs. The analysis scores the worst case of this course at 11 out of 30, the highest of
the set, where a lower score means a smaller worst case.

What it forecloses. It closes off nothing, and it spends a reporting period during which the
position is unchanged: an eightieth percentile estimate at completion of 13,970,165 dollars,
16.4 per cent above budget.

What it protects. It protects the working relationship and the project's own authority over the
matter, and it adds no cost of its own.

Investigate before taking a formal step

Open the variance inside the project: test the figures behind the forecast and establish what is
driving them before any formal step is taken.

What it costs. The analysis scores the worst case of this course at 5 out of 30, the lowest of
the set, where a lower score means a smaller worst case. Not established: how long an
investigation takes, and what it costs, is not a figure the platform holds.

What it forecloses. It closes off nothing formally, and it spends a reporting period. The
forecast the period would close on is unchanged by investigating it: an eightieth percentile
estimate at completion of 13,970,165 dollars, 16.4 per cent above budget.

What it protects. It protects the decision from leaving the project before the figures behind it
have been tested, and it keeps the formal step available afterwards.

Escalate to management review

Put the position formally in front of management as a matter for review, rather than settling it
inside the project.

What it costs. The analysis scores the worst case of this course at 8 out of 30, between the
other two, where a lower score means a smaller worst case. Not established: the platform holds
no record of which authority an escalation moves this decision to.

What it forecloses. It closes off settling this inside the project. Not established: who it moves
the decision to is not recorded for this project.

What it protects. It protects the position from being carried further on the project's own
judgment: the figure that goes up is an eightieth percentile estimate at completion of
13,970,165 dollars, 16.4 per cent above budget.

Recommended: Investigate before taking a formal step

It scores 5 out of 30, against 11 for keep the project under routine monitoring and 8 for
escalate to management review. The recommendation is not taken from the scores. This period's
cost performance at 0.91 and schedule performance at 0.94 are below 0.95, and the analysis calls
for investigation whenever either figure falls below 0.95 without reaching the 0.88 escalation
point. Against this period's evidence, cost performance stands at 0.909 and schedule performance
at 0.938.
```

**No rationale was invented.** Where no basis is served the card falls back to saying the reason
is not established rather than guessing, and `tests_render.html` group 15 now asserts both
directions.

---

## 3. The project detail map zooms to street level

**MapLibre, because the flat atlas cannot do it and no tween makes it able to.** The atlas is a
2:1 equirectangular world drawing of coastlines and borders with **no street data**, so shrinking
its viewBox to street scale magnifies an empty vector field around a marker.

**What PR #216 actually did:** it removed MapLibre's `<script>` and `<link>` from `index.html`.
The vendored files stayed on disk and every caller survived, so `createGlMap` has been bailing on
`typeof maplibregl === "undefined"` and PR #215's `NavigationControl` has been unreachable ever
since. Restoring those two tags is most of the fix.

The detail map now builds a MapLibre map centred on the project at zoom 16 and flies to 17, with
the NavigationControl and a marker. **The atlas remains the fallback**, for the reason the
earlier session gave: a section headed "Location" that renders black is worse than none.

Both standing requirements hold, and both are checked: a project with no coordinates keeps the
existing no-position state and **throws nothing** (verified against a real coordinate-less
project, not a synthetic clone), and the camera is centred on the site before the flight, so a
flight that never runs leaves the viewer on the project rather than stranded.

**One limit, stated plainly: tiles could not be verified as painting here.** Street tiles come
from `tiles.openfreemap.org`, which this container's proxy blackholes. What was verified in real
headless Chromium is that MapLibre loads, a `.maplibregl-canvas` mounts at 1650px wide on the
detail map, and nothing throws. Whether the tiles render is a network question for a real
browser.

**A defect I introduced and then fixed.** The first cut threw `Cannot read properties of null` —
the detail page re-renders while the map is mounting (the full-project hydrate does exactly
that), `destroy` removes the map, and the pending `load` handler then touched a detached map.
I established it was mine rather than pre-existing by running the identical drive against
stashed `origin/main` assets, where the error does not appear. Fixed with a `dead` flag the
handler checks first.

## 4. The detail page is wider

Two constraints, both width, neither a redesign:

- **`.app { max-width: 1320px }`** capped the whole application, leaving a wide monitor showing a
  narrow strip. Raised to `min(2100px, 96vw)` — raised rather than removed, because an unbounded
  column turns paragraphs into unreadable single lines. **Measured at a 1800px viewport: the
  column went from 1320px to 1728px.**
- **`.collapse-body > .detail-grid { display: block }`** threw away the two columns
  `.detail-grid` defines, so every panel inside every open section stacked vertically. That is
  the "too tall" half. Only the margin reset is kept; the grid keeps its own columns, and its
  existing 940px breakpoint still collapses to one column on a small screen.

**What it now fits:** the paired panels in each collapsible section sit side by side rather than
stacked, so a section that showed one panel per screen height now shows two.

## 5. Create a project appears once

The portfolio page's `#ws-create-card` panel is removed; the menu bar keeps it.

**Confirmed before removing, as required.** Project creation is reached from the Portfolio
flyout's **+ New Project** (`app.js`, calling `LinIngest.openCreateModal`), which is independent
of the panel. The administration surface keeps its own form for ResearchAdmin. Both were verified
present in the browser after removal. Worth noting the two forms were not identical — the flyout
modal asks for a project number the portfolio panel did not, which is how two projects end up
created differently.

## 6. Reset signals and Rebuild signals

**They differ, substantially, so both are relabelled rather than one removed.**

| Was | Does | Now reads |
|---|---|---|
| **Reset signals** (project detail) | server write `resetsignals`: clears the legacy `signals`, `signalInputs` and `simulationSignals` blobs for **one project**. Destructive. Does not touch documents, and the event log is deliberately preserved. | **Clear stored signals for this project** |
| **Rebuild signals (repair)** (portfolio) | client loop over **every project**: re-runs `LinSignals.runModels` in the browser over extraction results already on file and refreshes Portfolio Health. Clears nothing. | **Recompute every project (repair)** |

Each title attribute now states scope and destructiveness explicitly.

**Worth flagging, and not changed:** "Rebuild signals" runs the legacy **in-browser** model
computation, which contradicts the platform's own standing description that computation is
server-side and the browser computes nothing. Neither control touches `computed_results`, the
actual analysis store. Relabelling makes the difference visible; whether a browser-side compute
control should exist at all is a decision beyond this brief.

---

## A test that went red, and which kind it was

`tests_render.html` group 15 asserted the card said *"It does not record the rule that set the
recommendation against the score"* — **the defect's own sentence, pinned as expected behaviour.**
It records the old defect.

But the property behind it is real: the card must never invent a rationale. So it was rewritten
rather than deleted, and sharpened to assert both directions — with a served basis the card
states the rule and names the threshold; with none it falls back to saying so. Four net new
checks.

## Proof each check can fail

| Fault | Result | What went red |
|---|---|---|
| the mirrored escalation threshold drifts from the module (0.88 → 0.80) | **37/38** | the exact-boundary check: the module still escalates where the mirror says it should not |
| the detail dropzone sends `period: 1` again (browser) | second period's document lands in **period 1** (`{1: 2, 2: 0}`) | the reported symptom, reproduced |

Baselines 38/38 and `{1: 1, 2: 1}` restored after both, each file SHA-256 identical to before.

**The interpreter was confirmed real before any green was believed**: `/readyz` reported
`schema at head 0023_upload_period_end`.

## Open, and flagged

- **The server still defaults a missing period to 1.** All three UI surfaces now state one, so
  the default is reachable only by direct API call. It is the mechanism all of this ran through
  and is asserted in the suite so it stays visible.
- **Existing projects are not backfilled.** Documents already filed to period 1 stay there;
  which document belongs to which period is the judgement the platform must not make.
- **MapLibre tiles are unverified in this container** (see fix 3).
- **"Recompute every project" computes in the browser** (see fix 6).

## Files changed

`server/app/recommendation_basis.py` (new), `server/app/documents.py`,
`server/tools/test_six_fixes.py` (new), `assets/js/signals.js`, `assets/js/detail.js`,
`assets/js/recommendation_options.js`, `assets/js/app.js`, `assets/css/radar.css`, `index.html`,
`tests_render.html`, `T6_HANDOFF.md`, this report.
