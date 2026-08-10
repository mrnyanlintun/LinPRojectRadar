# Remediation Run 1: disable the 8, relabel the 30

Branch `claude/remediation-run1-disable-relabel` from `origin/main`. Run 1 of the 5-run
remediation programme in `remediation_programme.md` (order 1, 3, 2, 4, 5, per
`remediation_decisions_answered.md` 2.2). This run only.

## Lead findings

### 1. The Signal Ledger IS reachable from the participant decision sequence

Checked directly rather than assumed. `assets/js/detail.js` builds the project detail page with
two sibling sections rendered by the same `render()` call: `#d-ledger` ("Signal Inputs", drawn by
`LinApp.renderLedger`) and `#d-decision` ("Governance Decision", drawn by
`LinApp.renderDecisionCard`). There is no participant/operational gating anywhere in `detail.js`
that hides one from the other, and both are on the one page a project's PM lands on to read
evidence, then judge, then see the recommendation, then decide. The Signal Ledger is that
evidence step. It is reachable from the participant decision sequence.

**Consequence for qualifier placement, exactly as the run's Part 4 anticipated:** the proxy
qualifier and the disabled note are NOT rendered on the ledger. They render only in the export,
the API response (a new field, not a rendered one), and the methods documentation (the Methods
tab, a separate navigation surface driven by `assets/js/knowledge.js`, not the decision
sequence). The ledger keeps the canonical module name and the module's own stored finding,
unchanged. This was the run's own instruction (Part 4) and matches
`remediation_decisions_answered.md` X3 ("the participant does not see the remediation") and 1.4
("no split by surface" -- read here as: every surface the qualifier is ALLOWED on carries the
identical form; the ledger is not one of those surfaces at all, so there is no split to make).

**A second, adjacent finding, not asked for but load-bearing:** the participant's own
"Export Report (XLSX)" button on the decision card (`assets/js/export.js`) is ALSO reachable from
the decision sequence, and reads module names from the same canonical taxonomy the ledger reads
(`m.name` off `LIN_CATEGORIES`/`taxonomy.js`). That taxonomy's canonical `name` field was left
untouched by this run (only a new `disabled: true` flag was added to eight entries), so this
button's export carries no qualifier either, correctly, without any extra work being needed. The
qualifier lives instead in `server/app/research_export.py`'s workbook, the committee-facing
export that is not reachable from a participant's own screen. **If the owner ever wants the
participant's own XLSX button to carry the qualifier too, that is a real, separate decision** --
it currently does not, by the same reasoning that keeps it off the ledger.

### 2. Cross-run module overlap, all five runs

Cross-referenced every module code id named in `remediation_programme.md`'s five run
descriptions (Run 5's own module identifiers are the ones its text names explicitly: A4.1, the
footnote/count module, and the omitted range A4.2 through A4.10). Twelve modules recur:

| Module | Runs | Note |
|---|---|---|
| A4.5 Weather Day Impact | 1, 2, 5 | Relabeled here; Run 2 changes its arithmetic next; Run 5 re-exports it. Named explicitly in the run-1 prompt as expected overlap. |
| A4.6 Change Order Frequency | 1, 5 | Relabeled here; Run 5 re-exports it (A4.2-A4.10 was the export's omitted range). |
| A4.7 Dispute Escalation Index | 1, 5 | Same as above. |
| A4.8 Subcontractor Performance | 1, 5 | Same as above. |
| A4.4 NCR Rate | 2, 5 | Run 2 defect #11; Run 5 re-exports it. |
| A4.9 Procurement Lead Time Monitor | 2, 5 | Run 2 defect #4; Run 5 re-exports it. |
| A4.2 RFI Velocity | 4, 5 | One of the seven CORE modules Run 4 validates; Run 5 re-exports it. |
| A4.3 Submittal Rejection Rate | 4, 5 | Same as above. |
| B2.7 Plithogenic Sets | 1, 3 | **Disabled here (concept-only). Also on Run 3's 14-module unreachable list.** A real conflict, resolved by construction -- see below. |
| B2.9 Quantum Probability | 1, 3 | Same conflict, same resolution. |
| B1.1 Conservative Dominance | 2, 3 | Run 2 defect #1; also on Run 3's 14-module list, which is why `remediation_decisions_answered.md` 2.2 moved Run 3 ahead of Run 2. |
| B2.1 Dempster-Shafer | 2, 3 | Run 2 defect #2; same reasoning. |

**The one overlap that needed a decision, not just a note: B2.7 and B2.9.** Run 1 disables them
(concept-only, non-executable). Run 3's job is to build the flat-to-nested adapter so all
fourteen Group B1/B2/B3.1 modules -- including these two -- become reachable on the normal path.
Resolved by construction, not by coordination between sessions: `registry.run_module()` checks
`DISABLED_CONCEPT_ONLY` and returns the abstention **before** it ever checks whether the module
is in `VALIDATED` or attempts to call its formula function. Run 3's adapter can supply B2.7 and
B2.9 a perfectly-shaped nested input and they will still abstain, because the disable check runs
first regardless of input shape. **Run 3 needs to know this**: build the adapter for all
fourteen modules as planned, but do not expect B2.7 or B2.9 to start producing a status color
once it lands -- they will keep abstaining with the `DISABLED_UNSAFE` reason, correctly, until a
later run outside this programme's five (un-disabling a concept-only module is not a
data-adapter question) revisits whether either has since been given a real implementation.

## What changed, per module

### The 8 disabled (Part 1)

A3.8 Parametric Cost Index, B2.7 Plithogenic Sets, B2.9 Quantum Probability, B2.20 Hypersoft
Sets, B4.1 Multi-Objective Optimization, B4.2 Linear Programming, B4.5 Decision Sensitivity
Matrix, B4.6 Pareto Frontier Analysis.

- **`server/app/simulation/registry.py`**: added `DISABLED_CONCEPT_ONLY` (the eight ids and
  names). `run_module()` now short-circuits on membership, BEFORE the `VALIDATED` lookup and
  before any formula function is called: returns `status_color=None`,
  `insufficient_data=True`, `activation_state="DISABLED_UNSAFE"`, and an `evidence_metric`
  naming the module and explaining the exclusion. The formula functions themselves are
  untouched and still registered in `VALIDATED` (nothing deleted; the short-circuit sits in
  front of them) -- this is what keeps `test_simulation.py`'s "available == validated" guarantee
  intact.
- **`run_all()`**: these eight always land in the `abstained` list (never `computed`), so they
  are structurally excluded from every category rollup and fusion input -- `compute.py`'s
  `by_category` loop only ever sees `run["computed"]`.
- **Display, participant surface**: `assets/js/taxonomy.js` -- the live, participant-facing
  taxonomy (NOT `assets/js/categories.js`, which is dead on the main app and loaded only by the
  researcher deep-dive route) -- gained `disabled: true` on the eight matching entries and a new
  `window.isModuleDisabled(methodClass)` helper. `getModuleStatus()` checks it first and returns
  `"NA"`, the platform's existing not-relevant state (blue, square, distinct from grey no-data) --
  the same state a sector-excluded module already carries. No new state was invented, per the
  run's instruction and per `remediation_decisions_answered.md` 1.3.
- **The row does not disappear.** It still renders in its category, with its number and
  canonical name, now pilled "Not relevant" with a tooltip reading "Not available for production
  use..." rather than the sector sentence (`assets/js/app.js`'s `statusPill()` and the ledger's
  `modRows` now branch on `window.isModuleDisabled` to pick the right sentence -- the sector
  sentence would have been actively misleading here, since this is not a sector question).
- **Methods documentation**: `assets/js/knowledge.js`'s `modDoc()` now prints a "Status:
  Disabled..." line for these eight, above the existing Purpose/Computation sections (which are
  left as written -- the module's description is not rewritten, only annotated).
- **Export**: `server/app/research_export.py`'s Module results sheet now labels these eight
  `"<name> (disabled: concept-only, no production implementation of the analytical structure its
  name claims. Not executed, non-voting.)"` in the `computation` column, and a new
  `activation_state` column reads `DISABLED_UNSAFE`.

### The 30 relabeled (Part 2)

Every one of the thirty modules in the run's table. Implementation:

- **`server/app/simulation/registry.py`**: added `PROXY_QUALIFIERS` (module id -> the exact
  qualifier clause from the run's table) and `proxy_label()`/`activation_state()` helpers.
  `run_all()` now stamps every computed module's result dict with `activation_state` (one of
  `DISABLED_UNSAFE`, `ENABLED_QUALIFIED`, `ADVISORY_ONLY`) and, for the thirty, two new keys:
  `proxy_qualifier` (the clause alone) and `proxy_label` (the full
  `"<name> (proxy: <clause>. Advisory, non-voting.)"` string). **These are new keys on the
  stored result dict only** -- `module_id`, `status_color`, `evidence_metric` (what the ledger
  renders) are untouched, and `assets/js/taxonomy.js`'s four status accessors never read the new
  keys, which is what keeps the qualifier off the participant surface while still reaching the
  API response the same JSON payload carries.
- **Arithmetic**: unchanged, verified by a byte-identical reproducibility check in the new test
  suite (see Verify, below) and by the fact that no line in any `models_*.py` formula file was
  touched -- only `registry.py` (orchestration) and `compute.py` (rollup) changed under
  `server/app/simulation/`.
- **Export**: `server/app/research_export.py`'s Module results sheet's `computation` column now
  reads `"<name> (proxy: <clause>. Advisory, non-voting.)"` for these thirty (mirrored constant
  table, `_RUN1_PROXY_QUALIFIERS`, matching `registry.py`'s -- the file deliberately keeps no
  import dependency on `server/app/simulation/`, a pre-existing design choice this run continued
  rather than broke). `activation_state` reads `ADVISORY_ONLY`.
- **Methods documentation**: `assets/js/knowledge.js`'s `modDoc()` prints a "Status: Proxy:
  <clause>. Advisory, non-voting." line for these thirty, above Purpose/Computation.
- **Participant page (ledger, decision card, module charts)**: unchanged. Canonical name only.

### Voting scope (Part 3)

- **`server/app/simulation/registry.py`**: added `CORE_VOTING_MODULES` (the seven ids). Every
  computed module now carries a `votes` boolean (`True` only for the seven).
- **Layer (a), category rollup and project status fusion**: `server/app/simulation/compute.py`'s
  `by_category` loop now skips any module not in `CORE_VOTING_MODULES` before building
  `category_statuses`. A category with no CORE contributor gets no rollup entry at all -- a
  stricter exclusion than the pre-existing Group C exclusion (which still marks
  `contributes_to_project_status=False` but leaves the entry present); here the entry is simply
  absent. `project_status` fuses only the categories that DO have a rollup, i.e. only the
  CORE-carrying ones. This is what `getCategoryStatus`/`getProjectFusion` in `taxonomy.js`
  read directly (they read the STORED backend row, not a browser-side recomputation --
  `categories.js`, which recomputes client-side, is dead on the participant app), so the
  restriction reaches the ledger's category pills and the decision card's health state without
  any frontend change beyond what's already described.
- **Layer (b), generated recommendation text and courses of action**: found that
  `assets/js/recommendation_options.js` (the file both the operational Governance Decision card
  and the research decision-support surface call) builds its courses of action from the
  `Regret_Minimization` module (B4.7) alone -- a module that is neither CORE, disabled, nor one
  of the thirty relabeled proxies, i.e. it was going to keep voting on the recommendation
  regardless of the category-rollup change above. Added an explicit gate: `build()` now checks
  the new `votes` field on that module's stored result and, when `false`, returns
  `available:false` with a stated reason ("...not one of the modules validated to vote on
  project status on an interim basis...") instead of scoring courses of action. This is the
  layer-(b) exclusion Part 3 asked for, applied at the one place courses of action are actually
  generated.
- **Layer (c), the decision card**: the health state / action / authority block already reads
  `getProjectFusion` -> the now-restricted `project_status`, so it inherits the restriction with
  no separate change needed. The "Signal-Traced Action Plan" sub-block
  (`assets/js/decision.js`'s `deriveActionPlan`) was checked and found to already be dead code --
  its own comment documents that `CATEGORY_ACTIONS` is keyed `cat1..cat11` while `LIN_CATEGORIES`
  ids are `a1..d1`, so its lookup never matches and it has returned `[]` unconditionally since
  `taxonomy.js` replaced `categories.js`. Left as found: this is a pre-existing, unrelated defect
  (a stale-key mismatch of exactly the kind `NAMING_AUTHORITY.md` warns about), not something
  this run's scope covers, and it happens to already comply with the exclusion by being inert.
- **Ledger visibility (unchanged, verified)**: `run["modules"]` (what gets stored as
  `module_results` and what the ledger reads) is built from `run["computed"]`, which this run
  never filters by voting scope -- only `compute.py`'s SEPARATE `by_category` loop does. A
  non-voting module's number, status and finding render exactly as before.

## Where every user-facing change landed (per the 8/7 incident rule)

This run changes existing displays; it adds no new control. Precisely:

- The "Not relevant" pill already existed (sector abstention) on the Signal Ledger, per project
  category, per module row. The eight disabled modules now ALSO render that pill, on that same
  row, in that same place, with a different tooltip sentence. No new pill, no new row shape.
- The category-header status pill on the Signal Ledger, and the health-state badge / action /
  authority text on the Governance Decision card, both change VALUE (not placement or shape) for
  any category without a CORE-voting module and for any project whose status differs once only
  the seven CORE modules vote.
- The "courses of action" block inside the Governance Decision card now sometimes reads
  "not available" instead of three scored options, in the same place that block always occupied,
  when the scoring module is non-voting (which is every project's every period, since
  `Regret_Minimization` is not CORE).
- The Methods tab gained one new sentence per module for the thirty-eight modules this run
  concerns (eight disabled, thirty relabeled), inserted at the same fixed position (directly
  under "Purpose", above "Computation") in every module's existing collapsible entry. No new
  entries, no new tab.
- The committee-facing export workbook's Module results sheet gained one new column
  (`activation_state`) and changed the text of the `computation` column for thirty-eight of the
  (up to) 96 rows per period. No new sheet.
- The API response (the JSON a project's stored result already returns) gained three new keys
  per affected module result (`activation_state`, and for the thirty, `proxy_qualifier` and
  `proxy_label`; `votes` on every computed module). No existing key changed shape or meaning.

## Guarantees verified

- **Each of the 8 disabled modules is non-executable and appears in no fusion input.** Verified
  in `server/tools/test_run1_disable_and_relabel.py`: `run_module()` returns the abstention
  contract for all eight on a fully-populated input (proving the short-circuit fires regardless
  of data completeness, not because the modules would have abstained anyway); their formula
  functions remain registered in `VALIDATED` (nothing deleted); none appears in
  `run["computed"]`; all eight appear in `run["abstained"]`.
- **Each of the 30 relabeled modules renders its qualifier in the export and the API, not the
  participant ledger.** Verified: `activation_state()` returns `ADVISORY_ONLY` for all thirty;
  `research_export.py`'s `_run1_label()` produces the qualified string for all thirty (unit-level
  check against the mirrored table); `taxonomy.js`'s four status accessors read only
  `status_color`/`evidence_metric`/`module_id` off the stored row, never the new
  `proxy_qualifier`/`proxy_label` keys (read by inspection of every call site in
  `categoryLedgerHtml`, `statusPill`, `module_charts.js`).
- **The seven CORE modules still vote; the other 94 do not (all three exclusion layers).**
  Verified: layer (a) by asserting `category_statuses.keys()` equals exactly the CORE-carrying
  categories on a full run; layer (b) by asserting every non-CORE module's stored result carries
  `votes:false` (what `recommendation_options.js`'s new gate reads) and every CORE module carries
  `votes:true`; layer (c) is the same project-status restriction the decision card already reads,
  covered by the layer-(a) check plus the courses-of-action gate directly.
- **A non-voting module's number and finding still render in the ledger.** Verified: at least
  one non-CORE module in a full run carries a populated `evidence_metric` inside
  `run["modules"]`, unfiltered by voting scope.
- **No arithmetic result changed anywhere.** Verified two ways: (1) two independent calls to
  `run_module("A1.2", ...)` (CUSUM, one of the thirty) with identical inputs and RNG state
  produce byte-identical JSON; (2) the full server suite's pre-existing arithmetic-sensitive
  suites (`test_simulation.py`, `test_six_fixes.py`, `test_d1_module_inputs.py`,
  `test_storage_redesign.py`, and all EVM/period suites) pass unchanged in their numeric
  assertions -- only two suites needed updating, and both updates are about ROLLUP SCOPE
  (which categories get a fused status) or FIXTURE COMPOSITION (which modules a test's table
  includes), never about a changed number from an unchanged formula. See "Server suite" below
  for exactly what changed in each and why that is the correct fix, not a loosened check.
- **THE SINGLE MOST IMPORTANT CHECK, proved able to fail before it is shown to pass.** In
  `test_run1_disable_and_relabel.py`: baseline project status computed on a Green fixture;
  perturbing a CORE module's own input (RFI Velocity's `rfiCount`) DOES change status (proving
  the check is not vacuous); perturbing only a non-CORE module's input (Weather Day Impact's
  `weatherDaysLost`) does NOT change status; the actual regression assertion moves four
  different non-CORE modules' inputs at once (`docRiskScore`, `changeOrderCount`,
  `weatherDaysLost`, `subcontractorComplianceScore`) with the seven CORE modules' own inputs
  held fixed, and status is unchanged. All three run against the real `compute_project()`, not a
  mock.
- **Browser-driven verification (ledger, export, methods doc surface, both themes) -- NOT
  performed, and this is a real gap, not an oversight.** This container has Playwright installed
  but no downloaded Chromium binary (`playwright install` was not run within this session's time
  budget). `node --check` confirms every changed JS file (`taxonomy.js`, `app.js`,
  `knowledge.js`, `recommendation_options.js`) parses. The full server suite (57 files) drives
  the same code paths the browser would exercise end-to-end over HTTP (`test_training_detail.py`
  in particular posts to `/exec` and reads the JSON a browser would render), but nothing here
  actually rendered a DOM, read computed CSS, or looked at both themes. **A follow-up session
  with a working Chromium binary should run `tests_render.html` and `tests.html` in both themes
  and confirm the "Not relevant" pill, the qualifier's absence from the ledger, and its presence
  in the Methods tab, by eye.**

## Server suite

57 files (was 55; `test_run1_disable_and_relabel.py` added), fresh SQLite per file:
**3109/3109**. Two pre-existing suites needed updating because they encoded the pre-Run-1 rollup
scope as an assumption, not because anything they protected regressed:

- **`server/tools/test_d1_module_inputs.py`**: removed B2.7 and B2.9 from its `TWELVE` fixture
  (they are now permanently disabled, so "computes on a complete input" and "abstains
  specifically because this key is absent" are no longer meaningful assertions about them -- a
  disabled module abstains unconditionally). Added a new section 1b asserting exactly that
  (unconditional abstention, `DISABLED_UNSAFE`, even on the complete fixture) so their D1
  fabrication-fix history is not silently dropped from coverage, only re-pointed at what is now
  true about them.
- **`server/tools/test_training_detail.py`**: the "every category with contributors has a
  rollup" assertion is the pre-Run-1 scope by definition; rewritten to assert exactly the CORE-
  restricted scope (`voting_cats == set(cats.keys())`), plus a new assertion that a category
  WITHOUT a CORE contributor still shows its modules in `by_cat` (ledger visibility) with no
  rollup of its own. The Group C exclusion check was rewritten similarly -- Group C now has no
  rollup entry at all rather than a `contributes_to_project_status: False` entry, checked
  against the registry directly since `category_statuses` can no longer answer the question by
  construction. The "category status differs from its worst contributor" property (evidence
  combination, not worst-status-wins) is demonstrated directly against `fusion.py`'s own
  combination on a synthetic `["Yellow", "Green"]` pair (still true, `fusion.py` untouched)
  rather than required to be observable on this fixture's now much sparser (1-2 CORE members
  per category) rollup, where it may or may not show up depending on which specific statuses
  the fixture happens to produce that period.

## What Run 3 needs to know

1. **B2.7 and B2.9 will keep abstaining after the adapter lands**, and that is correct, not a
   bug in the adapter -- see the overlap section above. Do not spend time making them reachable;
   `registry.run_module()` refuses them before your adapter's output would ever be consulted.
2. **`CORE_VOTING_MODULES`, `DISABLED_CONCEPT_ONLY`, and `PROXY_QUALIFIERS` now live in
   `server/app/simulation/registry.py`.** Any of the fourteen adapter-target modules that turn
   out to also be CORE, disabled, or proxy-labeled should be checked against these three sets
   before assuming they vote once reachable. (Checked here: none of the fourteen are CORE or
   disabled beyond B2.7/B2.9; none are in the thirty-proxy list either -- the adapter's fourteen
   and this run's thirty-eight are disjoint except for that one pair.)
3. **`compute.py`'s category rollup now iterates `run["computed"]` filtered to
   `CORE_VOTING_MODULES`.** Once the adapter makes B1.1-B1.4, B2.1-B2.9 (minus the two disabled)
   and B3.1 reachable, they will appear in `run["computed"]` and in the ledger, but --
   correctly, under the still-open interim voting scope -- they will not vote, exactly like
   every other non-CORE module today. `remediation_decisions_answered.md` 3.2 already
   anticipated this ("reachable, shown, and explicitly marked as newly wired and unvalidated...
   under 1.1 they are non-voting anyway").

## Files changed

`server/app/simulation/registry.py`, `server/app/simulation/compute.py`,
`server/app/research_export.py`, `assets/js/taxonomy.js`, `assets/js/app.js`,
`assets/js/knowledge.js`, `assets/js/recommendation_options.js`,
`server/tools/test_d1_module_inputs.py`, `server/tools/test_training_detail.py`,
`server/tools/test_run1_disable_and_relabel.py` (new), `remediation_programme.md` (new),
`remediation_decisions_answered.md` (new), this report, `T6_HANDOFF.md`.

No migration. No `DATABASE_URL` pointed at anything but throwaway SQLite. No file outside
`DEng\LinPRojectRadar` touched.
