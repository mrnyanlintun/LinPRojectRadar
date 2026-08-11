# The fifteen defects: what each landed as, and what fixing ignorance did to project status

Branch `claude/remediation-fifteen-defects` from `origin/main` at `c2c609e`. This is the run the programme calls **Run 2 the 15 defects**, executed third under the revised order 1, 3, 2, 4, 5. Audit P0 findings 3, 4 and 9.

## 1. LEAD: the three-way categorisation of all fifteen

Every one is **fixed**. **None was moved to the disabled set.** Nine produce output on the real path and six abstain, and the six abstentions are the correct outcome: in each the remedy was to delete a fabricated input and require a real one the corpus does not carry.

Measured, not declared: sections 4 and 4b of the new suite drive a project through `/exec` and read the categorisation off the stored row and the stored portfolio snapshot.

| # | Computation | Category | What it now does |
|---|---|---|---|
| 1 | Conservative Dominance | **Fixed and producing** | Red review on the audit's own case, which read Green |
| 2 | Dempster-Shafer | **Fixed and producing** | Ignorance no longer becomes conflict |
| 3 | Quality Compliance Index | **Fixed and producing** | Computes from a real inspection pair; refuses an out-of-domain one |
| 4 | Procurement Lead Time | **Fixed and producing** | 0.65 on the audit's figures, where it was 1.8 |
| 5 | Cost Risk P80 | **Fixed and producing** | Same arithmetic, guarded; zero index abstains instead of raising |
| 6 | Signal Trajectory Classifier | **Fixed and producing** | 0.1 where it was 0.066667 |
| 7 | Cross-project Pattern Detector | **Fixed and producing** | Green reachable with matches present |
| 8 | Anomaly Score | **Fixed and producing** | 0 on the audit's case, where the 0.5 placeholder gave 0.166667 |
| 9 | Monte Carlo EAC | **Fixed and producing** where a budget exists | The hundred-unit placeholder budget is gone |
| 10 | Float Consumption Rate | **Fixed and permanently abstaining** | Needs network-derived float and reported completion |
| 11 | NCR Rate | **Fixed and permanently abstaining** | Needs an audited cohort from a Quality Audit Report |
| 12 | Weather Day Impact | **Fixed and permanently abstaining** | Needs verified lost days and a real float figure |
| 13 | Scenario Modeling, and its sibling What-If Scenario Matrix | **Fixed and producing** | Guarded earned value domains |
| 14 | Contractor Performance Score | **Fixed and producing** where the evaluation exists | Reads the quality rating; Red where it was Green |
| 15 | Environmental Compliance Rate | **Fixed and permanently abstaining** | Needs audited permit data |

**Three of the six abstentions resolve when the corpus lands** (Quality Audit and Environmental Compliance reports, Project 1 only today). **Two will not on any timetable this programme controls**: float consumption and weather day impact both need schedule float derived from an activity network, and the programme's own deferred list records building one as a second corpus programme rather than a fix.

**Two produce or abstain according to the document rather than the fix.** Monte Carlo computes wherever a positive budget is reported. Contractor Performance reads a Past Performance Report, which the programme records as one of the three types **correctly absent** from the corpus; supplied with one it produces the corrected Red, without one it abstains for want of a document rather than a fix.

Real-path output at period four:

```
producing   Monte Carlo EAC: red -- P80 EAC 13944652 vs BAC 12000000 (+16.2%)
producing   Cost Risk Analysis P80: Red -- CRA P80 EAC: $14,940,690 (+24.5% BAC)
producing   Procurement Lead Time: Red -- 8 at-risk + 5 delayed of 10 (weighted disruption 0.65)
producing   Scenario Modeling: Amber -- best $12900k / likely $13797k / worst $13797k
producing   Quality Compliance Index: Green -- 95/100, 2 deficiencies noted
producing   Contractor Performance: Red -- overall 4.5, schedule 4.2, cost 4.4, quality 2 (worst 2/5)
producing   Conservative Dominance: Red-review -- Multi-signal red-review
producing   Dempster-Shafer: Red -- Green 1%, Amber 2%, Red 96%, conflict mass 90%
producing   Signal Trajectory Classifier: Red -- CPI trend: -4.2% per period
producing   Cross-project Pattern Detector: Red -- 1 project(s) show similar signal pattern
producing   Anomaly Score: Amber -- Composite anomaly score: 61%
abstaining  Float Consumption Rate: no schedule float in this corpus at all
abstaining  NCR Rate: Awaiting an audited nonconformance cohort ...
abstaining  Weather Day Impact: Awaiting the schedule float available to absorb the lost days ...
abstaining  Environmental Compliance Rate: Awaiting audited permit compliance data ...
```

Every abstention states what it is waiting for, in words, with no module id, no key name and no em dash, asserted on the stored row, because the ledger renders it.

## 2. THE ROLLUP EVIDENCE: before and after the Dempster's rule fix

The "before" is the same `compute_project` over the same stored inputs with the baseline commit's own `dst_combine` extracted by `git show` and swapped in. One changed function and nothing else. The "after" is additionally checked to equal what the real path actually stored.

**Project level**

| Period | Status before | after | Conflict before | after |
|---|---|---|---|---|
| 1 | Red | **Amber** | 0.83337 | 0.812951 |
| 2 | Red | **Amber** | 0.83337 | 0.812951 |
| 3 | Red | Red | 0.483921 | **0.665104** |
| 4 | Red | Red | 0.599853 | **0.721441** |

**Category level** (four voting categories, four periods): status did not move once in sixteen category-periods; conflict moved in twelve of sixteen and **fell every time**. Cost and EVM Performance 0.348 to 0.3088, 0.8538 to 0.8146, 0.8141 to 0.7749, 0.4806 to 0.4414. Cost Risk 0.9328 to 0.8936 (twice), 0.9054 to 0.8662 (twice). Document-Derived Condition Signals 0.8141 to 0.7749 (twice), 0.945771 to 0.887799 (twice). Schedule Performance stayed at 0.0 throughout: it carries a single voting computation, and one source records no conflict either way.

**Read it plainly.** Project status moved in two of four periods, both Red to Amber, a real change to what a project manager is shown, and the change the fix is supposed to make. Category conflict fell every time it moved; project conflict *rose* in two of four. That looks like a contradiction and is not.

**The monotonicity property, and where it stops.** One application of the rule can never record more conflict, because the fix only moves terms out of the conflict sum. Asserted over 4,000 random mass pairs: fell in every one, rose in none. **A whole fusion is different**, because `dst_fuse` renormalises between combinations, so mass formerly discarded as conflict survives to disagree later. Over all 340 status sequences up to length four: **falls in 287, rises in 49, unchanged in 4.**

Worth reading twice: **the first version of that check asserted fused conflict never rises, passed on the handful of sequences first chosen, and was false.** Caught by exhausting the space, not by review. The suite now measures the real distribution and records explicitly that this run does not claim monotonicity at the fusion level.

## 3. Guarantees, each marked

- **Every audit proof reproduced as a check failing on the old code and passing on the new, both directions demonstrated.** VERIFIED, by the strongest available means: the suite extracts the **actual** pre-run simulation sources with `git show` from a **pinned baseline commit** into a throwaway package and calls the same functions. Not a hand copy; not an injection that might silently fail to apply. Section 0 first proves the baseline reproduces the audit's own figures (pass rate -60, ratio 1.8, conflict 0.32, Green 0.941176), and **the suite refuses to run if the extraction fails** rather than testing one direction and reporting clean. The baseline is pinned by sha, not `origin/main`, because otherwise this merge would have made every "fails on the old code" half compare the fix with itself.
- **Two Red inputs to Conservative Dominance return Red-review.** VERIFIED in four casings.
- **An unknown status string does not bucket to Green**, in Conservative Dominance and the three ensembles. VERIFIED for five values, each shown bucketing to Green on the old code first.
- **Dempster-Shafer with ignorance returns conflict 0, Green 0.96, Theta 0.04.** VERIFIED.
- **A negative quality score refuses.** VERIFIED; the old code's -60 shown first.
- **The procurement ratio cannot exceed its domain.** VERIFIED exhaustively over every consistent count triple up to eleven items, not at one point.
- **Project status change from `dst_combine` measured and reported.** VERIFIED (section 2).
- **No fixed module votes.** VERIFIED: CORE set unchanged, none of the fifteen among them, all carry `votes:false`.
- **Nothing changed about what a participant sees regarding the remediation.** VERIFIED by a stronger check than a keyword scan: every participant-facing script is byte for byte identical to the baseline.
- **Every check proved able to fail by injection, restored, baseline rechecked.** VERIFIED, fourteen injections, each putting the real old function back in the live module.
- **The browser drive proved able to fail end to end.** VERIFIED. Two projects, one server, identical documents; one computed on this branch, one with the baseline's module functions swapped in. **The registry captures formula functions by value at import, so the swap also rebinds the registry table. Without that the drive would have compared a project with itself and reported clean.** The swap is proved to have taken before anything is read from a page.
- **Both themes driven in a real browser.** VERIFIED, Fairbanks and NYC via the app's own theme flyout, transitions suppressed, backgrounds genuinely different.
- **Weather Day Impact's label revisited after the arithmetic changed.** VERIFIED and revised.

## 4. Verification performed

Server suite, fresh SQLite per file, `PYTHONIOENCODING=utf-8`, interpreter confirmed real. Baseline before any change **3167/3167 across 58 files** (matching the previous run exactly). After: **3394/3394 across 59 files**, new suite 227/227. `tests.html` **51/51**. `tests_render.html` **286/287** (the one red is the pre-existing auth-gated production-read row). Browser drive **40/40**. All re-run on merged `main` before pushing.

What the browser shows on the Signal Ledger, both themes: the procurement row reads "weighted disruption 0.65" here and "1.8" on the shipped code from the same document; the contractor row names the quality rating and reads Red; "12 open of 2 NCRs issued (open ratio 6)" is gone; "3 weather days lost" with no float figure is gone; "Environmental compliance: 90%" is gone. No qualifier text of any kind, no em dash, no page errors.

**Only one existing check went red across 3167, and it did both things at once.** `test_period_series.py`'s trajectory check protects a real property (the figure must be derivable from the stored periods, recomputed from stored rows) **and its hand-maintained copy of the arithmetic divided by observations rather than intervals**, which is failure mode 4. The property is kept; the divisor is corrected and written as an explicit interval count. No other suite needed any change.

**That single red is the most uncomfortable finding here.** Fifteen arithmetic defects were fixed and 3,166 of 3,167 existing checks did not notice. The suites verified reachability, storage, periods, abstention contracts and rollup scope, and almost never the numbers.

## 5. Which surfaces changed, and how

**No new control anywhere.**

1. **Signal Ledger.** Same rows, same place, same shape; four computations show an abstention where they showed a number, one shows Red where it showed Green, three show different numbers.
2. **Governance Decision card.** Inherits the two-period Red to Amber movement via the fused status; no change to the card.
3. **Methods tab.** `formula`, `abstain` and `sources` lines of thirteen entries rewritten because they described arithmetic that no longer exists.
4. **Export workbook.** One qualifier string changed (Weather Day Impact); no new column or sheet.
5. **API.** Additive `audited_cohort`, `quality_rating`, `ratings_read`; `pass_rate` is now `null` rather than a substituted figure when no inspection pair was recorded.
6. **Abstention reason text** on six computations.

**Weather Day Impact's label**, revisited as required: it said "fallback behaviour"; the fallbacks are gone, so the label was inaccurate in the opposite direction from the one the labelling exercise was correcting. It now reads "a lost-days over available-float ratio with ungoverned bands, computed only from verified lost days and a reported float figure", in both `registry.py` and `research_export.py`.

## 6. Incidental findings

1. **The browser instrument still contains every one of these fifteen defects.** `sim.js` still defines `DEMO_BAC = 100`; `simulations.js` still carries the twenty-item inspection default and the synthetic environmental score. Neither loads on a participant route, but **`research/deepdive.html` loads both, so the researcher deep-dive route still shows the defective arithmetic**. Out of scope here.
2. **The status vocabulary really is mixed in stored results.** Monte Carlo stores `"red"` lowercase while nearly everything else stores `"Red"`. Any new case-sensitive status comparison will be silently wrong about at least one computation.
3. `p80DeltaPct` swept; the contract is intact.
4. Portfolio results are keyed `cat8_1_*` to `cat8_5_*`, a retired numbering, but consistent end to end (`workspace.js` maps all five). Left as found, recorded.
5. **The zero-intake nonconformance arm was the worst single thing found, and the audit did not name it**: "No NCRs issued this period" as a **Green** finding on a project carrying an open backlog of any size.
6. **A negative worst-case forecast was classified Green** by the scenario computation, same structural cause.
7. **`_derived` never fires on the server.** Nothing writes a source `docType` of `"derived"`, so derived-input guards are correct but currently unreachable.

## 7. What was not done, and why

Browser copies not fixed (finding 1, a real owner decision). Cost Risk P80 not rebuilt: only the crash fixed, live figure proved unchanged. Nothing disabled. Nothing made to vote. **Bands not calibrated**: several fixes changed which side of an uncalibrated band a project lands on, so the arithmetic is now right and the boundaries are still unsourced. **No migration.** The last run recorded 0020 to 0023 unapplied in production, and the repo head is now `0025_project_notices`, so **0024 and 0025 should be checked alongside them**. Throwaway SQLite only; production never inspected or queried.

## 8. What the next session needs

1. **The rollup baseline has moved.** Run 4 must measure against the new one, not a figure remembered from before this run.
2. The band ladders of the seven are Run 4's subject; none of the fifteen is CORE, so nothing in its scope had arithmetic changed here.
3. **`fusion.normalise_status` is the one place the status vocabulary is recognised.** Anything comparing a status should go through it rather than writing a fifth comparison.
4. The two permanent abstentions blocked on an activity network need a corpus programme, not a threshold.
5. **The browser instrument is now a genuine divergence, not a lag.** `VALIDATION.md`'s parity claims for these fifteen are parity with a defect. Somebody should decide whether it is annotated or the browser copies are brought into line.

**Files changed:** `server/app/simulation/{fusion,models_decision,models_doc,models_ext,models_gov,models_sim,portfolio,registry}.py`, `server/app/research_export.py`, `assets/js/knowledge.js`, `server/tools/test_run2_fifteen_defects.py` (new), `server/tools/drive_run2_fifteen_defects.py` (new), `server/tools/test_period_series.py`, `remediation_programme.md`, `T6_HANDOFF.md`. No file outside the repository was touched.
