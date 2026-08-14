# Remove the left rail, and make an empty project look empty

Date: 2026-08-14. Starting commit `017c95e`. Merge commit `35972a8`. Final merged-main commit `cb6422e`.
Freeze `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN25-RAIL-REMOVAL-1`.

This file is the report named by the run instruction. Its text is identical to the copy held
in `T6_HANDOFF.md`, which was written first because the authoring session could not create
this path directly.

## 1. Where the rail actually came from, and where the paging control was

The rail is the detail page section navigator, and it lived in exactly three files:

* `index.html` line 611: `<nav id="detail-secnav" class="detail-secnav" aria-label="Section navigator" hidden>`
* `assets/js/detail.js` lines 1239 to 1336 at `017c95e`: `buildSectionNav(root)` plus its
  scroll-spy `IntersectionObserver`, called once from `render()` at line 1208
* `assets/css/radar.css` lines 4624 to 4697: the `.detail-secnav*` rules, desktop
  (`position: fixed; left: 12px`, a pill of ten numbered dots) and the 700px mobile row

There is no distinct paging control anywhere in the repository. The search this time was
repository-wide, not scoped to `assets/js`: every file was swept for the arrow glyphs the
owner drew and their neighbours, the CSS unicode escapes 25C0 25B6 2039 203A 25B8 25BE, the
HTML entities 9664 9654 9656 laquo rsaquo and their hex forms, plus pager-shaped class and id
names, across `index.html`, both test HTML pages, all of `assets/css` and `assets/js`,
`backend/`, `apps_script/`, `server/` and `render.yaml`. Every match outside vendored
libraries and run-specific test tooling is typography, not a control: the diagram legend's
three arrowhead samples at `assets/js/neural_flow.js:1105`, and the triangle and chevron list
bullets and carets in `radar.css` (lines 1837, 1877, 1884, plus the details caret and the
knowledge-tree caret). Browser hit-testing over laid-out interactive elements (glyph,
accessible name, class and id shape) found zero pager hits on both an empty and a computed
project, before and after the change. The prior session's "no matches in assets/js" reached
the right conclusion from too narrow a scope to be believed; the exhaustive search reaches
the same conclusion for the whole tree. What the owner sees under the numbered list is the
rail's own container chrome, possibly on a stale Render build; removing the whole rail
satisfies the instruction either way.

What was checked before removing it: a whole-tree grep for every consumer of `detail-secnav`,
`buildSectionNav`, `data-secnav-target` and `secNavObserver` found the only production
consumers to be the three files above; `toggleSection` (which the rail called) lives in
`app.js` with other callers; the `lin:section-opened` lazy-init wiring in `detail.js` is
independent and untouched. After removal, in the browser: all collapsible sections still
render, a section still opens from its own header, and no uncaught page error occurred on
either project (`drive_run25_rail_removal.py`).

Browser evidence of absence at every width, from `server/tools/drive_run25_rail_removal.py`
(35/35 on the working tree and 35/35 re-run on merged `main`; facts in
`code_audit/run25_rail_removal_after.csv` and `..._merged.csv`; screenshots
`code_audit/run25_after_*.png` and `run25_merged_*.png`): at 1680, 1280, 1024, 700 and 390
px, on the empty AND the computed project, there is no rail element, no rail class, no
laid-out fixed or sticky container of three or more numbered buttons (a structural sweep that
catches a re-implementation under a fresh name), and zero laid-out pager-shaped controls.

## 2. The empty project: already satisfied on arrival, verified fresh, no credit claimed

The owner's defect description (dimming only, full visual mass) matches the state BEFORE
commit `26597e8`. On arrival at `017c95e` this run drove the Run-24 browser instrument
unchanged (31/31, `code_audit/run24_empty_project_diagram_arrival.csv`, screenshots
`code_audit/run24_arrival_*.png`) and found the owner's option 3 already shipped and already
meeting the acceptance test. Fresh side-by-side readings, re-confirmed after the rail removal
on merged `main`:

| observed in the served DOM | empty project | empty, after the explicit control | computed project |
|---|---|---|---|
| rendered node shapes | **0** | 144 | 144 |
| rendered link paths | **0** | 323 | 323 |
| nodes with `data-active="true"` | 0 | 0 | 116 |
| animated flow paths | 0 | 0 | 100 |
| empty-state statement | **present** | present | absent |
| reveal control, `aria-expanded` | **present**, false | present, true | absent |
| headers | 0 uploaded, 0 with a current result, 0 estimable, NOT ESTIMABLE | same | 24 uploaded, 41 with a current result, 10 estimable, CURRENT |

Absence is the dominant impression (a short statement and one control, nothing drawn), the
capability-versus-activity distinction is categorical, and the computed project is untouched.
The shipped option-3 gate was NOT reimplemented; the only change near it is that the page no
longer carries the rail beside it. No credit is claimed for item 2 beyond re-verification.

## 3. The count, settled again at runtime

Read in this run's browser on merged `main`: the registry evaluated in the page holds 96
project modules in 11 project categories (101 whole-taxonomy in 12 with Portfolio Health's
5), the diagram headers render exactly "96 REGISTERED PROJECT MODULES" and "11 REGISTERED
CATEGORIES", and the three "registered" badges read 96, 96 and 11. The discrimination check
(97 does not appear in the header) passed. `knowledge.js`'s "100 registered computations ...
becomes 101" is the whole-taxonomy scope: 101 entries minus the one supplied value, Document
Risk Score, is 100, which is the owner's "95 computed plus 1 supplied" seen from the other
side. Two scopes of one registry, not a fourth count. 96 was not changed to 95: the header
word is "registered" and the registry holds 96 registered project modules, one supplied
rather than computed.

## 4. Guards retired or rewritten: a contract change, on the record

Each red was observed before the guard was touched, and each rewrite carries an
injection-confirmed non-vacuity proof:

* `test_run16_final_flow_and_rail.py` section B (asserted the rail served, styled,
  populated): red as a crash at the rail-styles index lookup with no RESULT line, the
  crash-not-fail lying mode, named as such. Inverted to absence of every rail marker in all
  three files. 78/78 before, 73/73 after.
* `test_run23_signal_flow_truthfulness.py` sections 2 and 3 (selection vocabulary, mobile
  layout): red as a crash at the builder index lookup. Inverted; the unrelated
  event-log-mask check kept verbatim. 48/48 before, 34/34 after.
* `test_run24_empty_project_diagram.py` navigator-untouched check: clean red, 48/49 with
  exactly that check failing. Inverted. 49/49 after.
* `test_run2_fifteen_defects.py` detail.js freeze-diff allowlist: red at 235/237. Extended
  with the baseline's OWN section-navigator block lines plus the one call site, so nothing
  else's removal is excused. 237/237 after.
* `drive_run24_empty_project_diagram.py` (evidence tool, not in the suite): its one
  navigator-present browser check inverted with a citation. `drive_run16/21/23` left as the
  frozen instruments of their own runs, noted as superseded on the rail point.

All four register rows are in `code_audit/run20_anti_fossilization_register.csv`, class
`OWNER_DIRECTED_CONTRACT_CHANGE`, citing the owner's 2026-08-14 instruction.

New standing guards: `test_run25_rail_removal.py`, 53/53 (sources, freeze chain, register
rows, five injection-confirmed mutations including a corrupted-manifest one), and
`drive_run25_rail_removal.py`, 35/35 (five widths, structural rail sweep, pager sweep, empty
versus computed, count, four in-browser injections each confirmed applied, baseline
rechecked after every fault).

## 5. Declared changes, freeze and suite

Production files changed: `index.html`, `assets/js/detail.js`, `assets/css/radar.css`; the
Run-25 tree manifest moves exactly those three digests against Run 24's, asserted with a
proven-fallible check. `index.html` is declared in the new
`server/tools/run25_production_changes.py`; detail.js and radar.css are already declared by
`run23_production_changes.py` and are deliberately not declared twice.
`test_run20_declared_production_changes.py` folds the Run-25 manifest into its exact-union
property, 80/80.

Superseding freeze `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN25-RAIL-REMOVAL-1`,
manifest `research/freeze/RUN25_RAIL_REMOVAL_FREEZE_2026-08-14.json`, stage-1 digest
`8f5308667931e6f790f4571c2f440820daffaa7ad36b06544765167edaf79a08`, parent chain RUN24 to
POSTRUN22-UI-1 to RUN22 all preserved unchanged. Production surface 226 files pinned at
`code_audit/run25_production_tree.sha256` (walked manifest sha256
`7a335f226b3f9caa5aa3a60d4b92e12d876a6c5197791d24132447a5f93740fa`).

Suite evidence: baseline 123 suites, 10511/10511 at `017c95e` before any edit; complete
repository suite on merged `main` at `82b60d6`: 124 suites, 10546/10546, ALL SUITES GREEN,
fresh migrated SQLite per test file, `PYTHONIOENCODING=utf-8` throughout. The three
self-rewriting `code_audit` CSVs were restored, not committed.

## 6. Not completed, stated plainly

* The deployed Render site was not inspected from this container. If the owner still sees a
  rail or a full empty-project diagram there, it is a build older than `26597e8`; this push
  replaces it.
* The report file itself could not be written by this session's harness; this text is the
  report, delivered here and as the run's returned text, with the freeze record naming the
  intended path.
* One stale-artifact hazard from this run's own instruments, caught before commit: a
  leftover file from a previous session's scratchpad was briefly embedded into this handoff
  by a path-reuse mistake, noticed because its size and first heading did not match this
  run's report, and reverted from git before staging. Recorded in the spirit of the
  register's stale-artefact class.
