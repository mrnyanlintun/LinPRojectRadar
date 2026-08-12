# Run 16 — Low-Hanging Instrument Cleanup

```
Run 16 — Low-Hanging Instrument Cleanup
Starting commit: 9b55824
Ending commit: PENDING_MERGE
Previous simulation version: sim-2026.08-v9
New simulation version: sim-2026.08-v10
Synthetic package: OG-SYNTH-0.3 (unchanged)
Participant package: unchanged
FINAL FLOW empty-project truthfulness: PASS
Clear-all state invalidation: PASS
Project-switch state isolation: PASS
Browser/server parity: PASS
Signal navigation rail: PRESENT
Collapse/hide control removed: NOT PRESENT IN THIS BASELINE (nothing to remove; see part 14)
Signal navigation functional: PASS
Material Cost Variance operational state: DISABLED
Material Cost Variance voting: NO
Material Cost Variance registry retained: YES
Voting set: 2
Expected voting set: 2
Previously disabled academic methods still disabled: 8/8
Participant decision sequence changed: NO
Production Postgres accessed: NO
Full suite: 6957/6957 across 87 suites
```

Three authorised changes, all three closed. The 100-module literature audit was not begun and no
unrelated analytical module was repaired.

## 1. Handoff audit

`T6_HANDOFF.md` was read end to end before any substantive work. Every remediation run from
Run 1 through Run 15 carries an entry, and each entry has a matching `REPORT_*.md` at the
repository root:

| Run | Handoff entry | Report |
|---|---|---|
| 1 | "Remediation Run 1: disable the 8, relabel the 30" | `REPORT_2026-08-10_run1-disable-and-relabel.md` |
| 2 | "the flat-to-nested adapter" | `REPORT_2026-08-11_run2-adapter.md` |
| 3 | "the fifteen defects" | `REPORT_2026-08-11_run3-fifteen-defects.md` |
| 4 | "validate the seven, restore voting, and the freeze" | `REPORT_2026-08-11_run4-validate-seven.md` |
| 5 | "Regenerate the Group A export, and the freeze programme closes" | (no run-numbered report; the entry is self-contained) |
| 6 | branch `claude/known-answer-tests` | `REPORT_2026-08-11_run6-known-answer-tests.md` |
| 7 | "the fix-now defects" | `REPORT_2026-08-11_run7-fix-now-defects.md` |
| 8 | "the 27 unresolved modules retested and classified" | `REPORT_2026-08-11_run8-retest-and-classify-27.md` |
| 9 | "the false-clean harness closed" | `REPORT_2026-08-11_run9-test-only-synthetic-integration.md` |
| 10, 10B | two entries | two reports |
| 11 to 15 | one entry each | one report each |

No chronological entry is missing and nothing was invented. `9b55824` is present as the tip of
`origin/main` and is this run's starting commit; it is the Run 15 push, and its parent `66d7993`
is the Run 15 merge. No repair to the handoff was required.

## 2. Baseline state (Gate 0)

| Item | Value at `9b55824` |
|---|---|
| Starting commit | `9b55824` |
| Simulation version | `sim-2026.08-v9` |
| Synthetic package | `OG-SYNTH-0.3` |
| Participant package | unchanged from Run 12; no participant-facing change in this run |
| Voting set | exactly two, TCPI and Variance at Completion, both cost lineage |
| Disabled set | the eight concept-only academic methods |
| Governed project label | Cost Recovery Status |
| Full suite | 84 suites, 6780 of 6780, all green, each against its own freshly migrated database |

The baseline was green before any edit, so the run proceeded.

## 3. Empty-project reproducer

`server/tools/drive_run16_final_flow.py` drives the SERVED application: a real server, a real
headless Chromium, a real signed-in project manager session, three projects created through the
ordinary routes, and the Project Detail page a participant opens. It reads the same four states
the owner named plus a one-document control, and for each it records both what the DOM says and
what the server says through the participant's own session, so the two can be compared rather
than assumed. It is deliberately NOT in the `test_*.py` glob: it needs a browser, and
`run_all_suites.sh` must not depend on one being installed.

It was run twice against identical fixtures, once with the three fixed files stashed and once
with them applied, so the before and after are the same experiment and not two different ones.
The two fact files are `code_audit/run16_final_flow_before.csv` and
`code_audit/run16_final_flow_after.csv`, with screenshots beside them.

No synthetic package data entered operational storage. The evidence is a stub extractor over
documents the harness itself creates, which is how every browser drive in this programme has
been fixtured since Run 9.

## 4. The exact FINAL FLOW root cause

**MULTIPLE_CAUSES: two DISPLAY_ONLY faults and one genuine STALE_SERVER_STATE fault.** They are
separate defects with separate fixes, and the third is the one that matters most.

**Cause 1, DISPLAY_ONLY: the column headers report the registry as if it were the project.**
`assets/js/neural_flow.js` built its four column headings as `DOC_KEYS.length + ' DOCUMENTS'`,
`MODULES.length + ' MODULES'` and `CATS.length + ' CATEGORIES'`. Each of those lengths is a
property of the platform, not of the project on screen. On a brand-new project with nothing
uploaded and nothing computed the served page read, verbatim:

```
27 DOCUMENTS | 96 MODULES | 11 CATEGORIES | PROJECT STATUS
```

**Cause 2, DISPLAY_ONLY: every edge animated unconditionally.** All 229 connection paths carried
a streaming-dash animation class whichever state the project was in, so the configured
architecture looked like traffic. On the empty project the browser drive counted
`animated_paths = 229` with nothing uploaded and no stored result, identical to the populated
project's 229. The status node additionally printed the internal word `None` as though it were a
verdict.

**Cause 3, STALE_SERVER_STATE: clear-all never invalidated the derived result.** This is not
presentation. `w_resetsignals` in `server/app/writes.py` emptied `signals`, `signalInputs` and
`simulationSignals` on the project document and left the `computed_results` table untouched.
That table is where every surface actually reads from. After the supported clear-all workflow,
the participant's own session still received, from the server:

```
C-cleared-server / live_row       = True
C-cleared-server / modules        = 42
C-cleared-server / project_status = Amber
```

and the same-session DOM still drew 31 green, 9 amber, 7 yellow and 6 red module nodes with the
status node reading Amber. It survived a reload because it was never a browser fact. The
portfolio list's status reads the same live row through `live_statuses`, so it was stale there
too.

**What was NOT the cause.** Not STALE_BROWSER_STATE and not CACHE_INVALIDATION: the switch
sequence populated, empty, populated returned each project's own reading both times, and the
empty project never once read as the populated one. Not BACKEND_DEFAULT_RESULT: an empty project
had no stored row at all and the server correctly said so.

## 14. Signal navigation rail root cause

**The obsolete collapse and hide control does not exist on the current served desktop Project
Detail route, and no removal was invented to claim one.**

The rail is `#detail-secnav` in `index.html`, built by `buildSectionNav` in `assets/js/detail.js`
and styled from `.detail-secnav` in `assets/css/radar.css`. It was added on 2026-08-10
(`REPORT_2026-08-10_training-separation-and-nav.md`, commit `d2107f4`) and, as that report says,
it was designed as a permanently slim rail of numbered dots so it never has to be wide enough to
cover content. The word "collapsed" in that design note describes the rail's own narrow resting
form; it never described a control a reader could press.

The served page was searched for one, not the source only. The browser drive scans every button,
link and element with a button role, at every state, for a left-pointing or right-pointing
triangle or chevron glyph, for an accessible name or title containing collapse or hide, and for
any class named like a rail toggle, and it keeps only elements with a non-zero rendered box. The
result at every state, empty, populated, cleared and after a project switch, before and after
this run:

```
collapse_suspects = []
```

A whole-repository sweep for the glyph shapes the owner described found three occurrences in
shipped code: two decorative `content:` markers on list bullets in the stylesheet, one chevron in
the researcher-side deep-dive category header, and one triangle inside a bullet-stripping regular
expression in a text helper. None is on the desktop Project Detail route and none is a control
that hides the rail.

**What was done instead of a fabricated removal.** The rail's required properties are now
asserted as regression, so the control cannot appear later without a suite going red: the rail
element is served, it is fixed to the left edge, it is populated from the sections actually
rendered rather than a duplicate list, it is shown whenever the page has sections, it renders
exactly one kind of button and every one of them targets a section, no glyph control exists in
its styles or in the file that builds it, and no toggle, collapse or hide class name exists
anywhere in the three files. The pre-existing mobile breakpoint that hides the rail below 700
pixels is preserved untouched, as instructed.

**If the owner is seeing a control, it is not on this route in this baseline.** The likeliest
candidates worth a look next time are a browser-drawn scrollbar on a narrow viewport or a
surface outside Project Detail. A screenshot with the control visible would settle it in one
step, and nothing in this run should be read as a claim that the owner did not see something.

## 17. Material Cost Variance disablement rationale

Recorded in the repository at `registry.EVIDENCE_UNDER_REVIEW_REASON` and mirrored in the export,
in the owner's own terms and not paraphrased into an algorithmic criticism.

Material Cost Variance cannot be treated as a universally interpretable automatic material-market
detector. A construction project can contain thousands of distinct materials, and a meaningful
reading of a material variance depends on evidence this platform does not collect: a contractual
material baseline; the schedule of values or approved contract rates; material specifications;
planned quantities; approved and current procurement data; procurement timing; sourcing location;
supplier conditions; regional availability; freight and logistics; currency; tariff and duty;
approved substitutions; escalation provisions; and trade disruption where it applies. Those
conditions differ by region and by date. A material readily available in New York can be scarce
or import-dependent in Singapore. The current implementation cannot infer that context from
generic project inputs.

**No claim is made that its arithmetic is wrong.** Its activation state is
`DISABLED_EVIDENCE_UNDER_REVIEW`, deliberately not the `DISABLED_UNSAFE` state the eight
concept-only modules carry, and the recorded reason is checked by the suite for the absence of
the words invalid, wrong, defect, incorrect and concept-only. The Run 14 domain fix that took it
from Red to Yellow at a progress figure of 100.5 stays in the file, untouched and unreached.

The owner's decision, deferred and NOT made in this run, is whether the module is ultimately
retained behind a purpose-built Contract Material Baseline plus Current Procurement Report
evidence design, or removed because the external market-research burden outweighs its value.

## 18. The exact exclusion protections

| Requirement | Where it is enforced | How it is proved |
|---|---|---|
| Not executed in a production analytical run | `registry.run_module` short-circuits before the formula function | the formula is wrapped in a tripwire and driven on four input shapes; it is never entered |
| Non-voting | `CORE_VOTING_MODULES` is unchanged at two, and it was never in it | the voting set is asserted equal to the two cost-lineage modules, and the intersection of the disabled union with the voting set is empty |
| Excluded from Cost Recovery Status | the rollup reads only voting modules, and an abstaining module contributes nothing to a category | it returns `status_color: None` and `insufficient_data: True` on every shape |
| Excluded from recommendation generation and courses of action | both read the fusion inputs, which an abstaining module is absent from | same abstention, at the one place the answer is produced |
| Excluded from participant decision card influence | the card reads the stored row; the module has no entry in `module_results` | it is recorded in `abstained` with its reason instead |
| Cannot silently reactivate through browser code | the refusal is the server's; nothing under `app/` resolves the browser taxonomy file | asserted directly, by sweeping every server source file |
| Registry and audit identity retained | its registry row, name and held-non-voting record all stay | asserted individually |
| Reason documented | `registry.EVIDENCE_UNDER_REVIEW_REASON`, mirrored in the export label | asserted, including the absence of algorithmic-fault wording |
| Presented as unavailable in the browser | `disabled: true` on its taxonomy entry, the same flag the eight carry | the taxonomy is parsed and exactly nine module entries carry the flag |

**No other module was affected.** The registry names exactly three modules containing material or
cost: this one, Cost Risk Analysis P80 and Parametric Cost Index. Parametric Cost Index was
already disabled by Run 1 for a different reason and keeps that reason. Cost Risk Analysis P80 is
checked directly and is not disabled. Sweeping every module the server can compute, exactly nine
are refused: the original eight and this one.

## 19. Voting and activation verification

- Voting set: exactly 2, TCPI and Variance at Completion, unchanged.
- Material Cost Variance does not vote, and did not before this run: it was one of the five CORE
  modules held non-voting since Run 4 for want of a sourced band. Disabling it therefore touched
  nothing in the voting or status semantics, which is what the stop condition required.
- The five held-non-voting records are still five; the Material Cost Variance entry stays, because
  the band it lacks is still the band it lacks.
- The eight previously disabled academic methods: all eight still disabled, each checked
  individually rather than counted, each still carrying `DISABLED_UNSAFE`, and none reclassified
  into this run's reason.
- The registry still declares 101 modules, 96 project-level and 5 portfolio-level. The next
  campaign's candidate population is 100: Material Cost Variance leaves the candidate list for
  audit-lineage reasons, and every one of the eight remains in it, because currently disabled
  operationally is not excluded from scientific review.

## 5. Architecture versus activity: what changed

The diagram still draws the whole registered architecture on every project, which is what makes
it useful. What changed is that it now says which of the shapes on screen are capability and
which are this project's current activity, in three independent ways, so the distinction does not
depend on a reader noticing any single cue.

1. **Two-line column headers.** Line one is the registry count and says so. Line two is this
   project's own figure.
2. **A summary strip in prose**, above the legend, stating the architecture sentence and then the
   activity sentence, with an explicit empty-project form.
3. **Motion means traffic.** An edge animates only when data currently travels it; otherwise it
   keeps its geometry, loses its motion and is marked static.

Every figure is a tally over statuses the SERVER produced and the browser read through the stored
row accessors. No arithmetic, no inference, no defaults; the suite asserts the tally block
contains no arithmetic operator, no rounding call and no status resolver.

## 6. Document-count semantics

`27 DOCUMENTS` meant twenty-seven **supported document types**: the length of the diagram's
document-key list, which is the set the extraction layer recognises. It never meant twenty-seven
uploaded documents, on any project, ever.

It now reads `27 SUPPORTED DOCUMENT TYPES` on line one and `N UPLOADED ON THIS PROJECT` on line
two, where N is counted from the project's own extraction events, unioned with the surviving
signal-input sources so a partially cleared event log cannot undercount. On a genuinely empty
project N is 0. The 27 is still derived from the list rather than typed in, and the suite fails if
a literal 27 appears in the header block.

## 7. Module-count semantics

`96 MODULES` meant ninety-six **registered project-level modules**: the registry's own count,
which the suite independently rederives from `p0-baseline/module_renumbering_map.csv` as 96
non-portfolio rows. It never meant ninety-six executed modules.

It now reads `96 REGISTERED PROJECT MODULES` and `N WITH A CURRENT RESULT`. The summary strip
carries the full breakdown the owner asked for and keeps the five states apart: modules with a
current result, modules with no current result, modules not applicable to this project, modules
disabled, and estimable categories. The collapsed detail page badges that read `96 modules` and
`11 categories` now read `96 registered` and `11 registered`.

## 8. Active-edge semantics

| Edge class | Active when |
|---|---|
| evidence into a module | this project has uploaded that document type |
| module into a category | that module has a current result in one of the five verdicts |
| category into the governed rollup | that category has a current estimable result |
| category into category | the source category has a current estimable result |
| governance feedback | the governed rollup has a current estimable value |

Anything that is not one of the five verdicts is an absence of a result, not a result: neither the
no-data state nor the not-relevant state lights a path. Active edges also carry an `lnf-active`
class so the state is nameable in the DOM rather than only visible.

## 9. Clear-all server-state evidence

The invalidation is performed at the authoritative layer, in `w_resetsignals`, and nothing about
it is hidden in the browser.

**The row is not deleted and not edited.** `computed_results` is append-only and a submitted
decision that references a row must still resolve years from now. The reset marks every LIVE row
for the project superseded, which is the one update the database permits on a referenced row
(migration 0009) and the same mechanism a recompute already uses. `superseded_by` carries a fresh
identifier that no row bears, because nothing replaced this result: the evidence behind it was
withdrawn. The row stays readable by its own `result_id` forever.

Because `_live_result`, the portfolio list's `live_statuses` and the research export all filter on
`superseded_by IS NULL`, one write moves every surface at once. Every live period is invalidated,
not only the latest, because the reset clears the project's evidence entirely.

The write is verified, in the same style as the rest of the module: the handler re-queries after
the commit and returns an error rather than reporting a success it did not check. It also reports
which results it invalidated, and the reset event records how many and for which periods, by
shape, on the same footing as the rest of that record.

`server/tools/test_run16_clear_all_invalidation.py`, 21 of 21, proves against the real write and
read paths: a live row exists before; the clear-all reports the one result it invalidated; no
derived result is live afterwards; the read path serves nothing at all rather than something
stale, and says to run a computation; the table still holds the row; the superseded row is still
resolvable by `result_id` with its module results intact; the project's signal blocks and inputs
are cleared; the reset is recorded as an event rather than by deleting one; another project's live
result is untouched; the cleared project can be computed again into a NEW row; and a second
clear-all on an already-cleared project succeeds and invalidates nothing.

**The suite was proved to detect the defect.** With the invalidation removed and the byte change
confirmed, it fails 7 of 21 checks, including the read path serving the stale Amber row.

## 21. Simulation-version transition

`sim-2026.08-v9` to `sim-2026.08-v10`.

The repository's convention is that the simulation version names the analytical layer's
behaviour, and it moves when what the layer produces changes. It moves here for one reason and
one only: Material Cost Variance no longer executes, so a project that used to carry a result for
it now carries an abstention. That is a change in the stored row's content and it must be
distinguishable in already-collected data, which is exactly what this field exists for. Every
historical version is preserved in the freeze record rather than replaced; nothing before v10 is
rewritten.

The two presentation fixes do not by themselves move the version. The Signal Flow diagram and the
detail-page badges are browser presentation, and the clear-all invalidation changes which row is
live, not what any computation produces.

The synthetic package (`OG-SYNTH-0.3`) and the participant package are unchanged. The participant
decision sequence is unchanged.

## 23. The exact next-run requirement

**FULL LITERATURE-BACKED SCIENTIFIC VERIFICATION OF THE REMAINING 100 MODULES**, beginning from
the merged baseline commit recorded above and from no other point.

The candidate population is 100: the 101 registered modules minus Material Cost Variance, which is
retained for audit lineage and removed from the candidate list only. The eight academic methods
disabled since Run 1 are IN that 100, with their Run 15 root causes
(`code_audit/run15_disabled_methods_root_cause.csv`) as the starting evidence; currently disabled
operationally is not excluded from scientific review.

The 100-module audit was NOT begun in this run, and no unrelated analytical module was repaired.

## 20. Regression results

`server/run_all_suites.sh`, every suite against its own freshly migrated database, with
`PYTHONIOENCODING=utf-8` set and the canonical anchored result line the only accepted evidence of
a pass.

Three suites are added by this run:

| Suite | Checks | What it holds |
|---|---|---|
| `test_run16_clear_all_invalidation.py` | 21 | the clear-all invalidation, at the real write and read paths |
| `test_run16_material_cost_variance_disabled.py` | 78 | the disablement, its exclusions, the untouched neighbours, and the eight |
| `test_run16_final_flow_and_rail.py` | 78 | the labels, the edge semantics, the single computational authority, and the rail |

**Every one of the three was proved to fail on the defect it guards.** The clear-all suite drops
to 14 of 21 with the invalidation removed; the disablement suite to 63 of 78 with the module taken
out of the disabled set; the labels suite to 75 of 78 with the old header string and an
unconditional animation restored. Each injection was confirmed to have altered bytes before the
result was believed, and each file was restored from a copy taken before the injection.

`tests.html` and `tests_render.html` are unchanged by this run and neither is treated as evidence
about the served page.

## 10. Same-session browser evidence

The served page, at state C, before and after this run. Same fixtures, same experiment.

| Reading | Before | After |
|---|---|---|
| column headers | `27 DOCUMENTS  96 MODULES  11 CATEGORIES  PROJECT STATUS` | `27 SUPPORTED DOCUMENT TYPES / 0 UPLOADED ON THIS PROJECT`, `96 REGISTERED PROJECT MODULES / 0 WITH A CURRENT RESULT`, `11 REGISTERED CATEGORIES / 0 ESTIMABLE NOW`, `PROJECT STATUS / NOT ESTIMABLE` |
| status node | `Amber` | `Not estimable` |
| animated paths | 229 | 0 |
| module node fills | 31 green, 9 amber, 7 yellow, 6 red, 47 no-data | no green, no amber, no yellow, no red, 99 no-data |
| server live row | `True`, 42 modules, `Amber` | `False` |

The cleared project now reads exactly as a brand-new empty project does, node for node.

**It took two halves, and the second was found by the browser.** The server invalidation alone was
not enough: this tab still held the stored row it had primed earlier, and every stored-row
accessor reads from that cache, so the first post-fix browser run still showed 41 modules with a
current result and a rollup of Amber on a project the server had already emptied. The cache is
now dropped in the same action. That is a second stale-state fault, in the browser, that no
server test would have caught, and it is the fourth run in a row where the served page carried a
defect the harnesses did not.

## 11. Reload evidence

**Before the fix, a reload made it worse, not better.** The reloaded page re-primed itself from
the server and came back with the uploaded document nodes lit again and a rollup of Red:

```
C-cleared-reloaded  headers            27 DOCUMENTS | 96 MODULES | 11 CATEGORIES | PROJECT STATUS
C-cleared-reloaded  project_status     Red
C-cleared-reloaded  node_fill_counts   31 green, 7 amber, 7 yellow, 8 red, 6 uploaded documents
```

**After the fix the server has nothing to serve**, which is what a reloaded page reads:

```
A-empty-reload      server_live_row    False
C-cleared-reloaded  server_live_row    False
```

**An honest limitation, stated rather than dressed up.** There is no way to reload the served page
inside this container that returns in reasonable time. `page.reload()`, a repeated `goto`, a
scheduled `location.reload()`, a second page in the same browser and a second browser in the same
Playwright context all stall for minutes, because the served page holds requests open (the
parser-blocking sign-in script is aborted and the map tile host is refused at CONNECT) and every
Playwright navigation primitive waits on them. The pre-fix run captured the reloaded DOM before
that stall was hit and it is the record above. The post-fix reload evidence is the server's own
answer, read through the participant's session, which is the layer a reloaded page reads and the
layer the defect lived at. The container fact is written into the harness so no future session
spends time rediscovering it.

## 12. Project-switch evidence

Populated, then empty, then populated again, in one session:

- the populated project reads identically before and after the switch, node fill for node fill
- the empty project never reads as the populated one
- the empty project's reading is byte-identical to the first time it was opened

No visual or project state leaks across projects, before or after this run. The switch was never
the fault.

## 13. One-document control

A project holding exactly one recognised monthly report, computed:

```
onedoc  headers    27 SUPPORTED DOCUMENT TYPES | 1 UPLOADED ON THIS PROJECT
                   96 REGISTERED PROJECT MODULES | 35 WITH A CURRENT RESULT
                   11 REGISTERED CATEGORIES | 9 ESTIMABLE NOW | COST RECOVERY STATUS | CURRENT
onedoc  animated_paths       71
onedoc  active_marked_paths  71
```

**This is the check that proves the fix did not simply suppress the visualization**, and it lands
between the two extremes on every measure: 1 uploaded document against 24 for the fully populated
project and 0 for the empty one; 35 modules with a current result against 41 and 0; 9 estimable
categories against 10 and 0; 71 active paths against 100 and 0; one lit document node against six
and none. Activation is selective, not all-or-nothing, and it tracks the evidence.

## 15. Signal rail, before and after

No production change, so there is nothing to show as a difference. What the served page reports,
identically before and after and at every state:

```
rail_visible       True
rail_buttons       10          (one per rendered section, in page order)
collapse_suspects  []
```

## 16. Real-browser Signal navigation evidence

Verified on the actual Project Detail route at 1680 pixels, on the empty project, the populated
project, the cleared project and across a project switch: the rail is present and visible in every
state; it carries one numbered entry per rendered section; no collapse or hide control is present
in any state; and the page reported no JavaScript errors in any state.

Partially verified rather than claimed complete: the per-entry click-through to each section, the
behaviour at the very bottom of the page and the behaviour across several desktop widths were
verified in an earlier probe of the same route rather than in the recorded evidence run, and the
scroll-spy is exercised by the application itself rather than asserted here. The rail's structural
properties are held by regression in `test_run16_final_flow_and_rail.py`.

## 22. Final merged baseline commit

Recorded below the report skeleton at merge time and in `T6_HANDOFF.md`. **The next campaign must
begin from that exact commit and no other point.**

## Stop conditions

None was hit.

- Empty-project behaviour needed no formula modification and none was made.
- Clear-all needed no production data migration: the fix uses the supersede mechanism the schema
  already has, and migrations 0020 through 0025 remain unapplied in production.
- The Signal rail needed no application redesign; it needed no change at all.
- Disabling Material Cost Variance altered nothing in the voting or status semantics beyond
  removing a module that was already non-voting, which is what the carried-forward note said it
  should do.
- No production Postgres, no production credentials, no production migration, no production
  deployment, no real participant data.
- Voting did not need to expand, and none of the eight disabled academic methods needed
  activation.

## Unresolved and worth the owner's attention

1. **The collapse control the owner described is not on this route in this baseline.** A
   screenshot with it visible would settle in one step whether it is a different surface, a
   different width or a browser-drawn scrollbar.
2. **The owner decision on Material Cost Variance is deferred and still owed**: retain it behind a
   purpose-built contract material baseline and current procurement report evidence design, or
   remove it.
3. **The Signal Flow diagram still draws three document rows as not applicable from a hardcoded
   editorial list**, because the platform has no per-document-type applicability signal to derive
   it from. That predates this run and is untouched by it, but it is the one place on the diagram
   where a colour is not derived from data.
4. All decisions outstanding from Runs 10B, 11, 12, 14 and 15 remain open.
