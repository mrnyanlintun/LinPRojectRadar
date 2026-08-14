# POST-RUN-22 UI CORRECTION — SIGNAL FLOW EMPTY-STATE TRUTHFULNESS + SIGNALS NAVIGATION

Date: 2026-08-14
Starting commit: **7226a59** (main = origin/main = HEAD at launch, working tree clean)
Parent freeze: `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN22`

---

## 1. Starting commit and posture

`7226a59`, the Run-22 release-qualified baseline. Run 21 reported "FINAL FLOW qualification:
PASS" and Run 22 re-verified it. The owner then reproduced false activity on the Signal Flow of
an empty project in a real browser. **The prior PASS was not defended.** The first action of this
correction was to reproduce the defect in a real browser, before changing a line of production
code.

## 2. Exact reproduction of the false Signal Flow activity

Driver: `server/tools/drive_run23_signal_flow_ui.py`, headless Chromium at
`/opt/pw-browsers/chromium_headless_shell-1194`, driving the real served application against a
throwaway SQLite database. State A is a project created with no upload, no compute and no
synthetic data.

Read from the served DOM on the EMPTY project, BEFORE the fix
(`code_audit/run16_final_flow_run23_signal_flow_ui.csv`, rows `A-empty`, `F-switch-empty`,
`D-reset-same-session`):

| observation | before |
|---|---|
| headers | `0 UPLOADED ON THIS PROJECT`, `0 WITH A CURRENT RESULT`, `0 ESTIMABLE NOW`, `NOT ESTIMABLE` |
| nodes carrying a verdict glow filter | **9** |
| nodes at the active opacity tier (>= 0.7) | **13** |
| animated edges / `.lnf-active` edges | 0 / 0 |
| bright node list | 9 x `circle:#5b3dd6:0.85`, 3 x `rect:#5b3dd6:0.75`, 1 x `circle:#9aa2ae:0.92` |

On a project with zero documents and zero results: nine analytical module dots painted at the
same opacity tier a computed module uses, each carrying a glow filter; three DOCUMENT rows drawn
as lit squares at 0.75, brighter than every other unlit document row; and the governed project
decision node at 0.92. The headers and the summary sentence were correct throughout, which is
exactly why the earlier drivers passed: **they asserted on the words and merely recorded the
pixels as an unasserted fact.** The same 9 + 13 reading was reproduced on the reset project and
on the empty project reached by a project switch.

## 3. Root cause

`assets/js/neural_flow.js` decided illumination with `status !== 'None'`:

```js
var glow = info.status !== 'None' ? 'url(#lnf-glow-'+info.status+')' : null;   // module dots
opacity: info.status === 'None' ? '0.20' : '0.85'
var glow = cs !== 'None' ? 'url(#lnf-glow-'+cs+')' : null;                     // category nodes
opacity: uploaded ? '0.88' : (notApplicable ? '0.75' : '0.30')                 // document rows
opacity: '0.92'                                                               // project node, always
```

`'NotRelevant'` is not `'None'`. It is the status of a module **disabled platform-wide** (nine of
them) or excluded by the project's sector, and on the document column the state of a document
type editorially marked as absent from this corpus. Those are REGISTRY facts: the module exists,
the type is supported. The diagram was keying illumination on the existence of the architecture
rather than on current project evidence, which is what section 2 of the instruction forbids.
Corroborating detail: the glow filter that branch asked for, `lnf-glow-NotRelevant`, is not
defined in the SVG `defs` at all, so that code path was never intended to light anything.

The EDGES were already correct (Run 16 made them key on `isEstimable`); only the NODES were not.
The reset boundary (Run 18) and the retained-document disclosure (Run 21) were already correct
and are untouched: no count, no wording and no reset semantic changed here.

**The fix.** Every node kind now uses the predicate the edges already used, `isEstimable(status)`
— a current stored verdict and nothing else — and records the decision as `data-active` in the
DOM so it is nameable rather than inferred from an opacity. Registered-but-inactive architecture
keeps its geometry, shape and colour hint at an inactive opacity tier, and a new legend entry
says so in words: "Registered, not active on this project".

## 4. The exact navigation defect

Three defects in the left-hand numbered Signal rail:

1. **SELECTED and ACTIVE were the same word.** The rail marked its chosen entry with the class
   `active`, the Signal Flow's own word for a category carrying current evidence. Section 6
   requires the two to be represented independently; in the shipped code they were not
   distinguishable at all, and nothing prevented a stylesheet from making them look the same.
2. **A click on a section already in view selected nothing.** The selection was set ONLY by the
   scroll-spy `IntersectionObserver`. The rail also published no `aria-current`, so assistive
   technology was never told what was selected.
3. **Below 700px the rail was `display: none`.** Every numbered control was unreachable at mobile
   width: the navigation was removed rather than adapted.

No collapse control (the obsolete grey `◀ | ▶`) exists, before or after. Its absence is guarded
in three files.

## 5. Production files changed

| file | change |
|---|---|
| `assets/js/neural_flow.js` | activity = `isEstimable(status)` for module, category, document and project nodes; `data-active` on every node; legend entry for registered-not-active |
| `assets/js/detail.js` | rail selection is `selected` + `aria-current`, never `active`; the click sets the selection itself |
| `assets/css/radar.css` | rail opaque; selected-state rules key on `selected`/`aria-current` only; mobile rail becomes a horizontal bottom row instead of `display: none` |

Declared in `server/tools/run23_production_changes.py` and enforced by the existing
declared-changes guard (`test_run20_declared_production_changes.py`), extended to read the third
manifest and to require that no path is declared by two manifests. `assets/js/neural_flow.js` is
deliberately NOT re-declared: Run 21 already declares it, and declaring it twice would let one
change be counted as two.

Also fixed, found by this correction's own reload state and in scope under section 2 ("the UI
truthfully describes that state"): `detail.js` blanked `p.events` in the browser copy after a
reset. The live page therefore reported "0 UPLOADED ON THIS PROJECT" and "This project has no
uploaded documents" — the exact sentence Run 21 proved false — while the SAME project reloaded
from the same server seconds later correctly reported "0 UPLOADED SINCE THE RESET, 24 RETAINED".
The mask made the live page less truthful than the reloaded one; it is removed. No activity
figure changes: the diagram's window is still bounded by the last `signals_reset`.

## 6. Empty project, before and after (real browser)

| observation | before | after |
|---|---|---|
| verdict-glow nodes | 9 | **0** |
| document-glow nodes | 0 | **0** |
| nodes at the active tier (>= 0.7 opacity) | 13 | **0** |
| red-pulse nodes | 0 | 0 |
| `.lnf-active` / animated edges | 0 / 0 | 0 / 0 |
| architecture still drawn (`.lnf-static` edges) | 229 | **229** |
| headers | 0 uploaded / 0 with a current result / 0 estimable / NOT ESTIMABLE | unchanged |

Architecture remains fully visible: the same 229 configured edges and every node are still
drawn, now uniformly neutral.

## 7. One document

`1 UPLOADED ON THIS PROJECT`, `35 WITH A CURRENT RESULT`, `9 ESTIMABLE NOW`. Exactly **1**
document node lit, **45** analytical nodes carrying a current verdict, **71** live edges and
**158** configured-but-idle edges. Only the evidence actually present is lit.

## 8. Multiple documents

24 documents across 6 types: **6** document nodes lit, **52** analytical nodes lit, **100** live
edges, **129** idle. Strictly more than the one-document case in documents and in reached
analysis, and matching the server's own row (41 modules with a result, 10 estimable categories).

## 9. Reset and hard reload

Reset, same session: 0 / 0 / 0 lit, 0 animated edges, 229 idle, "NOT ESTIMABLE".
Hard reload (a brand-new browser and context, sharing no memory or cache with the session that
performed the reset — proved by the first browser's window sentinel being absent): identical.
The reloaded page reconstructs `0 UPLOADED SINCE THE RESET, 24 RETAINED`, and after the mask fix
the live page says exactly the same thing.

Reload cost, measured again in this run: the swiftshader configuration exceeded a 180 s
navigation budget and was abandoned; with WebGL disabled (the Run-22 `webgl_disabled` flags) the
whole rebuild took **10.4 s** including an 8 s settle wait. This confirms Run 22's attribution of
the reload cost to the GL pipeline and is not an application defect.

## 10. Project switching

Populated -> empty -> populated. The empty project shows zero lit nodes and zero live edges (the
named guard is asserted there, not merely recorded). The populated project returns with the same
6 document nodes lit and the same 100 live edges. **No cross-project illumination leakage.**

OPEN FINDING, NOT FIXED HERE AND NOT A LEAK. Across that round trip two module dots and the
governed rollup move amber -> red. Both readings are server rows for DIFFERENT PERIODS: the
first render reads the period-1 row `detail.js` primes, a later render reads the list projection,
which carries the LATEST period. Measured on the server for the seeded project: periods 1-3 Amber,
period 4 Red. That is a period-selection artefact in code this correction was instructed not to
redesign. It is reported rather than papered over, and the State-F assertion checks the leakage
property (same evidence lit, same paths carrying) rather than an exact colour histogram.

## 11. Navigation behaviour (real browser)

- **10** numbered controls present; **1** rail in the DOM (no duplicate); rail opacity **1**.
- Every control is the element the browser delivers its own click to at its centre — no
  invisible overlay or hitbox, at every width tested.
- Clicking control 4: `aria-current="true"` and `.selected` **immediately**, still selected
  2.6 s later once the smooth scroll settled, exactly one control selected, and the target
  section opened.
- `activeCls: false` on the selected control: the rail no longer uses the analytical word at all.
- With a category SELECTED on the EMPTY project, the empty-state guard still holds — zero lit
  nodes, zero live edges. **SELECTED is not ACTIVE**, proved rather than asserted.
- Obsolete grey collapse control `◀ | ▶`: **absent**, at every width, by a DOM-wide search for
  arrow glyphs, collapse/hide labels and `secnav-(toggle|collapse|hide)` classes.

## 12. Responsive widths

| width | controls | display | reachable (own hit) | collapse suspects |
|---|---|---|---|---|
| 1920 wide desktop | 10 | flex | 10/10 | none |
| 1440 normal desktop | 10 | flex | 10/10 | none |
| 1024 tablet | 10 | flex | 10/10 | none |
| 760 narrow | 10 | flex | 10/10 | none |
| 390 mobile | 10 | flex | 10/10 | none |

At 390px the first attempt at a mobile rail (bottom: 10px) was measured with **0 of 10**
controls reachable — the icon dock and its emblem image owned every hit. Moved to bottom: 152px,
clearing the dock band (12-72px) and the Ask Lin launcher (88-140px), and re-measured: 10 of 10.
That failure and its fix are both in the browser evidence.

## 13. Non-vacuity proof

Named guard: **`GUARD_EMPTY_PROJECT_NO_ACTIVE_MARKER`**. It reads the SHIPPED active-state
markers — the `lnf-glow-*` filter reference, the node opacity tier, `lnf-red-pulse`, the
`.lnf-active` class and the four `.lnf-flow-*` animation classes — not text and not counts.

In the real browser, on the empty project, in one uninterrupted sequence:

1. GREEN before the mutation (0 active markers);
2. one empty-project node forced active in the DOM (`filter=url(#lnf-glow-Green)`,
   `opacity=0.88`) — the guard **fails RED**, reporting `verdictGlowNodes=1, brightNodes=1`;
3. the diagram re-rendered — the guard is **GREEN again**.

The same guard function is what states A, D, E, F and the navigation-selection state are checked
with, so what was proved red is the assertion the acceptance rests on, not a copy of it.

The source-level suite `test_run23_signal_flow_truthfulness.py` (44 checks) was also proved red
and green by really reverting two production rules in the working tree — the module-dot opacity
rule and the mobile `display: none` — which took it to 38/41 at the time, then restoring them.

## 14. Complete repository suite

Run 1, before the guard scopes were updated (this is the honest record of what the correction
broke and had to declare):

| suite | result | why |
|---|---|---|
| `test_run10_state_protection.py` | 83/84 | `detail.js` and `radar.css` were outside the named browser scope |
| `test_run2_fifteen_defects.py` | 235/237 | the participant-surface freeze names every added and removed line in `detail.js` |
| `test_run6_known_answer.py` | 487/489 | `radar.css` outside the named production scope |
| `test_run8_retest_classify_27.py` | 272/274 | the same |
| `test_run22_production_tree_completeness.py` | 39/42 | production changed, so the pinned tree manifest no longer matched |

Every one of those is a guard doing its job. None was loosened. Each run's scope list was
extended by NAMING the new files and the exact lines, in the convention the repository already
uses, and the tree manifest was SUPERSEDED rather than regenerated in place (see section 16).

Run 2, after the scopes were named: **10461/10462**, one remaining failure in
`test_run2_fifteen_defects.py` because two block comments this correction added to `detail.js`
produced continuation lines the participant-surface freeze cannot classify. The comments were
rewritten in the file's prevailing `//` style rather than the guard being loosened.

Run 3, pre-commit, on the corrected tree: **122 suites, 10462/10462, ALL SUITES GREEN.**

## 15. Merged-main verification

Merge commit on `main`: **92138e3** — this is the tree the complete suite and the browser suite
were verified on. Two documentation-only commits follow it: **ebe0dd3**/**cdd9076**/**7ad4df7**
carry the superseding freeze, the handoff and this report, and the head that stamps these hashes
into the report is the last commit on main. No production file changed after 92138e3.

- Targeted Signal Flow + navigation browser suite, re-run on merged main:
  **34/34** (`code_audit/run23_browser_facts_merged.csv`) — empty, one document, multi-document,
  reset, hard reload, project switch, navigation selection and five widths, with the
  non-vacuity mutation proved red and restored green again on the merged tree.
- Complete repository suite on merged main: recorded below.
- Production-tree freeze guard: `test_run22_production_tree_completeness.py` 42/42 against the
  SUPERSEDING manifest, and `test_run23_signal_flow_truthfulness.py` additionally proves the
  Run-22 manifest is byte-identical to its state at the starting commit and that the only files
  whose bytes moved are the three declared UI files.
- Voting: exactly **2** — `A1.7`, `A1.8`, read from the registry.
- Concept-only activation: **0** (8 concept-only modules remain disabled).
- Material Cost Variance `A3.4`: **disabled**.

Complete repository suite on merged main: **122 suites, 10462/10462 checks, ALL SUITES GREEN.**

## 16. Superseding freeze

| | |
|---|---|
| new freeze identifier | `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-POSTRUN22-UI-1` |
| parent (preserved, not rewritten) | `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN22` |
| freeze record | `research/freeze/POST_RUN22_UI_CORRECTION_FREEZE_2026-08-14.json` |
| manifest SHA-256 (stage 2) | `3e27ae0b27569d383ae2bb4dfce1f3eefeda4ed02b4b7438f38ced51e2884d05` |
| companion file | `research/freeze/POST_RUN22_UI_CORRECTION_FREEZE_2026-08-14.sha256` |
| production inventory | 226 files, `code_audit/run23_production_tree.sha256` |
| production manifest SHA-256 | `879ff5e56f22beb1492be656329395f7caa4a5bef141be28dffa39e8a3c322cf` |
| parent production manifest | `code_audit/run22_production_tree.sha256`, unchanged |
| reason | Signal Flow empty-state truthfulness + Signals navigation correction |

The two-stage construction is Run 22's, for its reason: a manifest cannot contain its own digest,
so `manifest_sha256` and `final_commit` are null in the stage-1 file and its digest is recorded in
the companion `.sha256`, verifiable with `sha256sum -c`.

## Deviations, limits and what was NOT done

- The amber → red period-selection instability in section 10 is REPORTED, not fixed. It is
  outside the two named defects and touches period selection, which this correction was told not
  to redesign.
- The swiftshader reload could not be driven inside a 180 s navigation budget, so state E is
  driven in a second browser with WebGL disabled. That is a stronger reload (no shared memory or
  cache), and the GL attribution is Run 22's measured, carried-forward fact.
- Both Run-9/Run-10 self-rewriting manifests were restored to their recorded bytes rather than
  committed with this tree's digest.
- Tavily and live web were unavailable; nothing here depended on an external fact.
- No production Postgres, credential or secret was touched. Throwaway SQLite only.
