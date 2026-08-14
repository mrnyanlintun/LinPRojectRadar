# An empty project must look empty on the Signal Flow diagram

Date: 2026-08-14. Starting commit `21a6db1`. Final merged-main commit `26597e8`.
Freeze `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN24-EMPTY-DIAGRAM-1`.

This file is the report named by the run instruction. Its text is identical to the copy
held in `T6_HANDOFF.md`, which was written first because the authoring session could not
create this path directly.


## 1. What an empty project now renders, and how it differs from a computed one

Read from the served DOM in headless Chromium against a throwaway SQLite database
(`server/tools/drive_run24_empty_project_diagram.py`; facts in
`code_audit/run24_empty_project_diagram_baseline.csv` and `..._after.csv`).

| what is on screen | empty project, before | empty project, after | computed project, after |
|---|---|---|---|
| rendered node shapes | 144 | **0** | 144 |
| rendered link paths | 323 | **0** | 323 |
| configured-but-idle links drawn | 229 | **0** | 129 |
| nodes at the active tier | 0 | 0 | 58 |
| nodes carrying `data-active="true"` | 0 | 0 | 116 |
| animated / `.lnf-active` edges | 0 / 0 | 0 / 0 | 100 / 100 |
| empty-state statement | absent | **present** | absent |
| explicit reveal control | absent | **present** | absent |
| column headers | 0 uploaded, 0 with a current result, 0 estimable, NOT ESTIMABLE | unchanged | 24 uploaded, 41 with a current result, 10 estimable, CURRENT |

An empty project now leads with this, and nothing else:

> NOTHING TO SHOW ON THIS PROJECT YET
> This project has no uploaded documents and no current results, so the project status is not
> estimable. Once documents are uploaded and signals are generated, this view will show which
> document types arrived, which analytical groups they reached, and which of those produced a
> current status.
> [ Show the registered architecture ]
> The architecture view is what the platform can do, not what this project has done. Nothing on
> it will be active until this project has evidence.

Pressing the control draws exactly the diagram that was there before: 144 node shapes, 323 link
paths, 229 idle links, every document type, every module row, every category, every link, and
zero active markers. `aria-expanded` flips to `true`, the label becomes "Hide the registered
architecture", and `aria-controls` names the diagram element. A project with any current evidence
never sees any of this: the gate returns early and the diagram is drawn directly, as before.

The observed difference between the two projects is now categorical rather than tonal. Before, it
was 144 shapes and 323 paths on both, distinguished only by opacity tiers and a caption.

Screenshots: `code_audit/run24_baseline_A-empty.png`, `code_audit/run24_after_A-empty.png`,
`code_audit/run24_after_A2-empty-revealed.png`, `code_audit/run24_after_C-computed.png`.

## 2. The three options, evaluated against what was actually measured

**Option A, the links do not draw at all until something is uploaded.** Rejected. Measured on the
empty project before any change, the links are 323 of the 467 rendered elements; removing them
leaves 144 shapes including every one of the 96 module rows, all 11 category nodes, all 27
document rows and the project node, still laid out as the same four-column architecture. It
reduces the count without changing the impression, and it degrades the architecture view for a
reader who legitimately wants it. It also fails the second half of the instruction: it still does
not distinguish capability from activity, it just draws capability with fewer strokes.

**Option B, the rows draw but at a weight that plainly reads as inactive.** Already shipped, and
re-verified here as working exactly as designed. The inactive tiers measured on the empty project
are 0.20 for no-data module dots (87 nodes), 0.28 for categories (11), 0.30 for unlit document
rows (24), 0.34 for the registered-not-active rows (12) and 0.26 for the project node; links sit
at 0.12 to 0.16 and only live paths animate. Zero nodes reach the active tier. **The owner is
looking at that build and still reads it as dense.** That is the evidence that weight alone does
not carry the distinction, and why this option is not sufficient on its own. It is kept: it is
what makes the revealed architecture view honest.

**Option C, replace the diagram with a short statement, with the full architecture behind an
explicit control.** Chosen and implemented. It is the only one of the three where the absence, and
not the architecture, is what the page leads with, and the only one where the separation between
"what the platform can do" and "what this project has done" is made by an act of the reader rather
than by a shade of grey. The diagram is not removed: it is built by the same code, from the same
model, and is one press away.

**Recommendation and what was implemented: option C, layered on top of option B.** The gate keys
on the single predicate the summary sentence already used, so the two readings cannot disagree.

## 3. The state of each item BEFORE this run

**Item 1, an empty project reads as empty. NOT SATISFIED.** The diagram drew 144 node shapes and
323 link paths, every supported document type, every registered module row, every category and
every configured link, with "0 UPLOADED ON THIS PROJECT / 0 WITH A CURRENT RESULT / 0 ESTIMABLE
NOW / NOT ESTIMABLE" above it. This is the item this run exists for.

**Item 2, the registered-but-inactive marker. ALREADY SATISFIED BY PRIOR WORK, not by this run.**
The owner read three highlighted document rows as lit. They were, at merge `92138e3`: the
post-Run-22 UI correction found them at opacity 0.75, brighter than every other unlit row, and
fixed it. **The owner's report predates that fix.** Measured here on 21a6db1, before this run
changed anything: Past Performance Report, Historical Project Data and Test & Commissioning Report
each render as a **square** in the platform's blue not-relevant colour `#5b3dd6` at opacity
**0.34**, with `data-active="false"` and no glow filter, against an uploaded row's **circle** in
`#a0bcd8` at opacity **0.88** with `url(#lnf-glow-DocOn)`. Colour, shape, opacity, glow and the
DOM activity flag all differ. The legend already carries "Registered, not active on this project".
The platform's blue not-relevant state does apply here and is already in use. **No credit is
claimed for this item.** What this run added is a `data-state` attribute naming the three states
(`uploaded` / `registered-not-active` / `not-uploaded`) and a guard proved to go red when the
distinction is removed.

**Item 3, the header count. ALREADY CORRECT.** See section 4.

**Item 4, the paging control. ALREADY ABSENT.** See section 5.

## 4. The header count: where it comes from, its value, and every other place a count appears

**Where it comes from.** `assets/js/neural_flow.js` `buildModel()` reads `window.LIN_CATEGORIES`
(`assets/js/taxonomy.js`), filters out any category at `level === 'portfolio'` via
`projectLevelCategories()`, and flattens the survivors' `modules` arrays. The header is
`MODULES.length + ' REGISTERED PROJECT MODULES'` and `CATS.length + ' REGISTERED CATEGORIES'`.
No figure is typed in.

**The verified numeric value**, read three independent ways:

| how | project categories | project modules | whole taxonomy |
|---|---|---|---|
| `LIN_CATEGORIES` evaluated in the running browser | **11** | **96** | 12 / **101** |
| the served diagram's own headers, read from the DOM | **11** | **96** | n/a |
| `taxonomy.js` re-parsed independently by the new suite | **11** | **96** | 12 / **101** |

So **96 is correct and was already correct.** The owner's "95 computed plus 1 supplied" is the
same 96: exactly one project-level registry entry, Document Risk Score (`Doc_Risk_Cat4`), is a
value the extraction model supplies rather than a computation the analytical server runs, and it
is a registered module like the other 95. The word on the header is "registered", which is exactly
what 96 counts. **No count was changed by this run**, and changing it to 95 would have made the
header disagree with the registry.

**Every other place a module count appears, and whether it agrees:**

| place | states | agrees |
|---|---|---|
| Signal Flow column header (`neural_flow.js`) | 96 project modules, 11 categories | yes, read from the registry |
| Signal Flow summary sentence (`neural_flow.js`) | 96 registered project modules and 11 registered categories | yes, same variables |
| Signal Flow section badge (`detail.js`, `projectModuleCount()`) | "96 registered" | yes |
| Signal Web section badge (`detail.js`, same function) | "96 registered" | yes |
| categories section badge (`detail.js`) | "11 registered" | yes, the category figure |
| `knowledge.js` lines 585, 600, 617, 2450, 2492 | "100 registered computations" | **yes, once scoped** |
| `ds_defensibility_data.js` lines 2, 13 | "100 registered computations, plus one value the extraction model supplies" | yes |
| `categories.js:4`, `signals.js:23`, `simulations.js:993, 3176`, `projectnet2d.js:281` | 101 distinct computations | yes, whole taxonomy |

**Resolving the `knowledge.js` "100/101" sentence.** It reads: "All 100 registered computations are
executable ... One further value, the document risk score, is supplied by the extraction model
rather than computed by the analytical server, and is not counted in the 100; if it is later
implemented server-side the count becomes 101." That is the **whole taxonomy**, project-level plus
Portfolio Health: 96 project-level plus 5 Portfolio Health equals 101 registry entries, of which
one is the supplied document risk value, leaving 100 computations. The Signal Flow's 96 is the
**project-level** subset of the same 101, because Portfolio Health is portfolio-scale and is not
part of a project-level diagram. **The two figures agree; they are different scopes of the same
registry.** All three arithmetic relations (96 + 5 = 101, 101 - 1 = 100, 96 - 1 = 95) are asserted
in `test_run24_empty_project_diagram.py` against a figure parsed from `taxonomy.js`, so the
reconciliation cannot silently rot. Nothing was rewritten to make this true; it already was.

## 5. The `◀ | ▶` control

**It does not exist and did not exist at 21a6db1.** Searched in the browser on both an empty and a
computed project, over every interactive element and every element carrying a pager-shaped class
or id, counting only elements the browser actually lays out: **0 hits**. The section navigator
itself is present with **10** controls and publishes `aria-current` on its selection. Searched in
source across `neural_flow.js`, `detail.js` and `radar.css` for the glyphs and for
`nav-page` / `secnav-(page|prev|next|toggle|collapse|hide)` / `section-pager`: **none**.

The post-Run-22 correction records the same finding and guards it in three files, so this is a
second independent confirmation, not a discovery. **Nothing was removed and nothing was broken,
because there was nothing there.** Two false leads worth recording: the diagram legend renders
`&#9656;` (▸) three times as an arrowhead *sample* in the flow-class key, and `radar.css` uses `›`
as the list bullet of `.eb-drivers li::before`. The first version of this run's browser reader
matched both and reported three "paging controls" on a page that has none; the reader was scoped
to interactive elements and the source scan excludes `‹ ›`, with the reason recorded in both
files. A guard that can never be green proves nothing.

## 6. What changed in production

One file: **`assets/js/neural_flow.js`**.

* The previous `render` is unchanged in what it draws and is now `drawDiagram`. It returns the
  emptiness decision it already computed for its own summary sentence.
* `var projectIsEmpty = (uploadedDocCount === 0 && modWithResult === 0 && catEstimable === 0)` is
  now defined **once** and drives both the sentence and the gate. The suite fails if a second copy
  of that expression appears anywhere in the file.
* A new `render` draws into a host element and, only when that predicate is true, hides the host
  and inserts the statement and the `.lnf-reveal` control.
* `data-kind` on every node group (`module` / `category` / `project` / `document`) and
  `data-state` on every document row (`uploaded` / `registered-not-active` / `not-uploaded`).
* The legend strip gained the class `lnf-legend` so it is addressable.

Not a deployed file, changed because it is the guard's own pointer:
**`server/tools/production_tree.py`** repoints `PINNED` from `run23_production_tree.sha256` to
`run24_production_tree.sha256` and keeps the run23 manifest addressable as `PINNED_RUN23`.

`assets/js/neural_flow.js` is deliberately **not** declared in a new production-changes manifest:
Run 21 already declares it, and the declared-changes guard requires that no path appear in two
manifests, so declaring it again would let one change be counted as two. Same reasoning the
post-Run-22 correction recorded.

One wording change was forced by a guard. The empty panel's retained-documents sentence is
deliberately **not** the summary strip's sentence verbatim. Written verbatim, it gave the Run-21
reset-disclosure guard a second copy to find, and reverting the real one in the summary strip no
longer turned that guard red: measured, `test_run21_reset_disclosure.py` went 31/32 with the true
defect present and the duplicate absorbing the mutation. The panel now says "still held and will
be read the next time signals are generated" and the guard is 32/32 and still red under the real
revert.

## 7. Non-vacuity proofs

Browser, `drive_run24_empty_project_diagram.py`, **31/31**:

| guard | injection | injection confirmed by | result |
|---|---|---|---|
| `GUARD_EMPTY_PROJECT_READS_EMPTY` | reveal the architecture on the empty project and force one node to `filter=url(#lnf-glow-Green)`, `opacity=0.88`, `data-active="true"` | re-reading the node's own attributes and the document's `[data-active="true"]` count, both non-zero, before judging | **RED** (`activeNodes=1, verdictGlowNodes=1, brightNodes=1, drawnShapes=144, drawnPaths=323`), GREEN again after re-render |
| `GUARD_INACTIVE_DOC_MARKER_DISTINCT_FROM_ACTIVE` | copy a live uploaded row's exact fill, opacity, glow filter and `data-active` onto a registered-not-active row on the computed project | re-reading the target row and requiring its fill and opacity to equal the source's | **RED**, GREEN again after re-render |
| `GUARD_NO_PAGING_CONTROL` | insert a real laid-out `◀`/`▶` control under the section navigator | `getElementById` plus a non-zero bounding rect | **RED** (count 2), GREEN again after removal |
| `GUARD_HEADER_COUNT_MATCHES_REGISTRY` | assert a figure one higher than the registry against the same header string, and separately require that header string to be present | the header string is asserted non-empty and to contain "REGISTERED PROJECT MODULES" | discriminating |

After every fault, all three guards were re-read on freshly rebuilt diagrams and were green. The
empty-state guard is additionally proved not-always-green in the ordinary path: the same function
is run on the **revealed** empty project and is required to report `drawnShapes=` and
`drawnPaths=`, so a guard returning green unconditionally would fail that check.

Source, `test_run24_empty_project_diagram.py`, **49/49**. Eleven mutations, each applied to a copy
of the shipped file, each asserted to have really changed the text before the guard is consulted,
each required to produce a *named* failure from the same `scan()` the green assertion uses: remove
the gate's hide; delete the reveal control; stop `drawDiagram` reporting emptiness; write a second
copy of the emptiness predicate; apply the gate to computed projects too; stop building the
diagram at all; revert module illumination to `status !== 'None'`; brighten the
registered-not-active rows to the lit tier; draw them with the active shape; stop naming the
document row's state; stop naming the document nodes by kind. All eleven go red on the named
property and only on it. The registry parse is proved to be really counting the registry: an extra
module is injected into a copy of `taxonomy.js` and the parsed project-module figure is required to
move from 96 to 97, then the shipped figure is required to be restored.

Two guards were caught being vacuous during construction and are recorded rather than quietly
fixed. The browser reader initially counted the two full-panel background rects and the six
arrowhead markers inside `<defs>` as "bright nodes", which no empty project could ever satisfy;
node metrics are now scoped to `#lnf-nodes`. The source gate check initially matched
`host.style.display = 'none'` anywhere, which the toggle handler also contains, so deleting the
gate left it green; it now matches the gate's own two-statement form.

## 8. Suites

Complete repository suite on merged `main`, fresh migrated SQLite per test file,
`PYTHONIOENCODING=utf-8` throughout, interpreter confirmed real:

```
Suites run: 123   Total checks: 10511/10511   ALL SUITES GREEN
```

Before this run, at 21a6db1: 122 suites, 10458/10462, the four failures being
`test_run21_reset_disclosure.py` 31/32 and `test_run22_production_tree_completeness.py` 39/42,
both caused by this run's own in-progress production edit being present in the tree at the time.
Both are 32/32 and 42/42 on the merged commit. The new suite accounts for 49 of the 53 added
checks.

## 9. Freeze

Superseding freeze identifier:
**`OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN24-EMPTY-DIAGRAM-1`**.
Parent `...-POSTRUN22-UI-1`, preserved unchanged.
Stage 1 `research/freeze/RUN24_EMPTY_PROJECT_DIAGRAM_FREEZE_2026-08-14.json`, stage 2 its
companion `.sha256`. Production surface 226 files, manifest
`code_audit/run24_production_tree.sha256`, manifest sha256
`a6424d585412d88c1767e7c8ddbdfd01a6aeb80268a997b12563f7314b3bb109`.
The scientific authority tree is byte-identical to the parent's. `registry.py` unchanged, voting
count 2 unchanged, concept-only activations 0, Material Cost Variance still disabled.

The self-rewriting hash manifests `code_audit/run9_no_operational_effect.csv`,
`code_audit/run10_no_operational_effect.csv` and `code_audit/run20_cycle12_100_reaudit.csv`
rewrote themselves during the suite runs and were restored to their recorded state rather than
committed.

## 10. What was not completed

1. **The report could not be written as `REPORT_2026-08-14_empty-project-diagram.md`.** The
   session harness running this task refuses to let a subagent write a report `.md` file into the
   repository. The report is therefore reproduced here verbatim, the freeze record names the
   intended path and records `report_present_in_tree: false`, and a later run should land the file
   at that path from this text.
2. **Items 2, 3 and 4 were already satisfied before this run started** and no credit is claimed.
3. **The empty-state gate builds the diagram and then hides it.** It does not skip the work. That
   is deliberate: the emptiness decision is a product of the draw, so building and hiding is what
   makes the gate and the summary sentence provably agree rather than being two predicates that
   can drift. The cost is one hidden SVG build on an empty project.
4. **One open finding is carried forward untouched from the post-Run-22 report**: across a
   populated to empty to populated project switch, two module dots and the governed rollup move
   amber to red, because one render reads the period-1 row `detail.js` primes and a later render
   reads the list projection, which carries the latest period. Both are server rows for different
   periods. A period-selection artefact outside this run's display-only scope.
