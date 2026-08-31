# Run 90 — the two charts, and what the surfaces say

**Repository:** `/home/user/LinPRojectRadar`, branch `main`.
**Starting commit:** `4857a82` ("Run 89 report: the status architecture"), clean tree, and
`main == origin/main` re-verified by me at start (`git rev-parse HEAD origin/main` returned the
same hash twice).
**Interpreter:** system `python3` 3.11.15 at `/usr/local/bin/python3`. There is no repo venv and
none was created. **NO MIGRATION WAS ADDED.**
**`SIMULATION_VERSION` is UNMOVED at `sim-2026.08-v43`.** Nothing under `server/app/` changed at
all this run (`git diff --name-only 4857a82 HEAD -- server/app/` is empty), so no module computes
anything differently and the stamp must not move.
**Sequence-bearing files moved: NONE. The empty tuple, declared explicitly: `()`.**
`assets/js/decision.js`, `assets/js/decision-ui.js`, `assets/js/workspace.js`,
`assets/questionnaires/intake.json`, `assets/questionnaires/debrief.json` — all five untouched.
**NOT MERGED. NOT PUSHED.**

---

## 1. The owner's deployment sequence

Everything below is on `main` at the ending commit. There is no migration and no rebuild step;
the two charts are client files, so a hard refresh is the whole deployment.

```
git fetch origin
git checkout main
git log --oneline -3          # expect the Run 90 report commit on top
# no alembic step: python -m alembic current still reads 0030_extraction_contract
```

Open a project detail page on a period that has stored readings, and hard-refresh
(**Ctrl/Cmd + Shift + R**) so the changed JavaScript is not served from cache.

**Project Signal Network** — the section badge now reads **"6 categories drawn"**.

* You should see **six planets and no others**: A1 Cost and EVM Performance, A2 Schedule
  Performance, A3 Cost Risk, A4 Document-Derived Condition Signals, A5 System Dynamics and
  Complexity, A6 Delivery Quality Performance. Data Integrity, Signal Synthesis, Evidence
  Combination, Regulatory and Authority Thresholds and Decision Optimisation are gone from the
  picture; they still run.
* The **sun at the centre is DARK** on any row whose status is Indeterminate, with the words
  `PROJECT STATUS / Indeterminate` painted over everything else so no planet can cover them. On a
  row that does carry a band the sun is filled in that band's colour and has a corona.
* A category with no posture is a **dashed, unfilled** circle captioned **"not assessed"**. It is
  not any band colour.
* Moons: a filled haloed dot has a band; a **plain rimmed dot with no colour computed and asserted
  no band**; a dark dot with a solid rim reported nothing; a dotted outline was never called; a
  dashed purple outline is not relevant to this project.
* Drag on the canvas to rotate, wheel to zoom. **Every planet is the same size, every moon ring is
  the same width, every moon turns at the same speed.** Nothing geometric means anything.

**Signal Flow** — the section badge now reads **"42 modules drawn"**.

* You should see **three concentric rings converging on one centre**: 27 document types outermost,
  the 42 modules in service in those six categories next, the six categories inside them, the
  project status in the middle.
* On an Indeterminate row the centre node reads **"Indeterminate"** (it used to read "Not
  estimable" there).
* **Count the streams reaching the centre.** Only a category that carries a posture arrives, with
  an arrowhead. A category with no posture runs inward and **stops, short of the centre, with a
  small blunt dot** and no arrowhead. On the row measured below, two arrive and four stop.
* The sentence under the diagram now says it draws the six weighted performance categories and
  that the platform's other categories still run and are not drawn here.

**What to expect if something is wrong.** If the module roster fails to load, the Signal Flow now
prints "The module roster did not load, so this diagram is not drawn." instead of drawing a 2024
roster from a stale hard-coded fallback.

---

## 2. Every specification edit, before and after, verbatim

### 2.1 `specifications/A5_system_dynamics.md`

**BEFORE (line 3):**
```
Seven modules in service: A5.1, A5.2, A5.4, A5.5, A5.6, A5.7, A5.8. (A5.3 Tornado Risk Ranking is
implemented but is **not in service** and is not specified here.)
```
**AFTER:**
```
Five modules in service: A5.2, A5.4, A5.6, A5.7, A5.8. (A5.3 Tornado Risk Ranking is
implemented but is **not in service** and is not specified here.)

**A5.1 DSM Rework Propagation and A5.5 Rework Feedback Loop were retired at Run 89**, by the note
their rows carry in the registry (`p0-baseline/module_renumbering_map.csv`), for the reason that
registry states: *the module is defined on a structure (the DSM rework matrix / the rework feedback
loop) prepared for a method rather than a thing a project document prints.* Retirement is removal
from service, not removal from existence: their identifiers still resolve and their specifications
below are kept readable, marked retired at the head of each. They are absent from the category tree
the interface renders (`assets/js/taxonomy.js`, whose A5 list begins at `a5_2`) and they are not
dispatched.
```

**BEFORE:** `**All seven are bandless.** Each reports calibration-pending with the standard note verbatim: *"The`
**AFTER:** `**All five in service are bandless**, as were the two retired. Each reports`
`calibration-pending with the standard note verbatim: *"The method this measure is named for`

**BEFORE:** `## The abstention sentences all seven share`
**AFTER:** `## The abstention sentences all seven specified here share`

**BEFORE:** `All seven take their structure through \`canonical_v4.require_v4_structure\`. Writing \`W\` for the`
**AFTER:** `All seven specified here take their structure through \`canonical_v4.require_v4_structure\`.`

**BEFORE:** `## A5.1 — DSM Rework Propagation`
**AFTER:** `## A5.1 — DSM Rework Propagation — RETIRED at Run 89, not in service`

**BEFORE:** `## A5.5 — Rework Feedback Loop`
**AFTER:** `## A5.5 — Rework Feedback Loop — RETIRED at Run 89, not in service`

**BEFORE:**
```
None. All seven modules in service in this category have unambiguous sources and are specified
above.
```
**AFTER:**
```
None. All five modules in service in this category have unambiguous sources and are specified
above, as are the two retired at Run 89.
```

**BEFORE:**
```
Seven governed structures, none of which any supported document type carries:
`dsmDependencyModel`, `sensitivityModel`, `scenarioSet`, `systemDynamicsModel`, `queueModel`,
`agentSupplyChainModel`, `desProcessModel`. Every one of them is a **model of relationships**
```
**AFTER:**
```
Five governed structures for the modules in service, none of which any supported document type
carries: `sensitivityModel`, `scenarioSet`, `queueModel`, `agentSupplyChainModel`,
`desProcessModel`. (`dsmDependencyModel` and `systemDynamicsModel` were the structures A5.1 and
A5.5 waited for; both modules were retired at Run 89 for waiting on them.) Every one of them is
a **model of relationships** rather than
```

### 2.2 `specifications/B4_decision_optimisation.md`

**BEFORE (line 3):**
```
**Two modules are in service: B4.3 Constraint Satisfaction Analysis and B4.4 What-If Scenario
Matrix.** The category declares seven identities; five are not in service and are not specified
here.
```
**AFTER:**
```
**One module is in service: B4.3 Constraint Satisfaction Analysis.** The category declares seven
identities; five have never been in service and are not specified here.

**B4.4 What-If Scenario Matrix was retired at Run 89**, by the note its row carries in the registry
(`p0-baseline/module_renumbering_map.csv`), for the reason that registry states: *the module is
defined on a structure (the what-if scenario matrix) prepared for a method rather than a thing a
project document prints.* Retirement is removal from service, not removal from existence: its
identifier still resolves and its specification below is kept readable, marked retired at its head.
It is absent from the category tree the interface renders (`assets/js/taxonomy.js`, whose B4 list
holds `b4_3` alone) and it is not dispatched.
```

**BEFORE:** `## B4.4 — What-If Scenario Matrix`
**AFTER:** `## B4.4 — What-If Scenario Matrix — RETIRED at Run 89, not in service`

**BEFORE:** `None. Both modules in service in this category have unambiguous sources and are specified above.`
**AFTER:**
```
None. The one module in service in this category has unambiguous sources and is specified above,
as is the module retired at Run 89.
```

**The vocabulary is the registry's, not a new one.** `registry.RETIRED_NOTE_PREFIX = "RETIRED "`
and the note on each row in `p0-baseline/module_renumbering_map.csv`; the wording "*the module is
defined on a structure (…) prepared for a method rather than a thing a project document prints*"
is quoted from those three rows verbatim. Run 43D's ruling — retirement is removal from service,
not removal from existence — is stated and obeyed: **no section was deleted**, both retired module
specifications remain readable, and their identifiers still resolve. No tombstone, no refusal
state, no new error class. (The A1 specification's precedent DELETES its retired module's section;
I did not follow that half of it, because §5.1 asks for the modules to be *recorded as retired*,
and Run 43D asks for them to stay readable.)

---

## 3. Per goal: reached or not, and every iteration

### Goal one — the Signal Network as a solar system. **REACHED.**

**Iteration 1.**
*Measured:* the chart at `4857a82` is already a 3D solar system — Run 82 Part D built it, in the
pure-canvas projection idiom of `charts3d.js`. It drew **eleven** planets and 60 moons; planet
size was `20 + min(10, moduleCount*0.9)`, moon orbit radius was `planetRadius + 16 +
min(16, moduleCount*1.1)`, orbital rate was `0.34 / sqrt(moduleCount)`; a module that computed and
asserted no band fell through `bandColor(null) || C.Complete` and was painted **Complete blue**.
*Hypothesised:* the goal is not a rebuild but a change of population, of the sun's rule, and of
what the geometry claims.
*Changed:* population to `window.performanceCategories()` (new, in `taxonomy.js`, derived from the
generated roster: project-level, group A — exactly A1…A6, asserted at six); planet size, orbit
radius and orbital rate all to constants; a new drawn state `computed_unbanded`, unlit; a category
with no posture always dashed and captioned "not assessed"; the sun given a corona only when a band
was issued and a dark centre otherwise; the pass-one→pass-two edge class removed, since no
pass-two category is drawn.
*Measured after, in Chromium at 1280px:* 6 planets `[A4 Red, A3 none, A5 none, A2 none, A6 none,
A1 Green]`; sun `state=unlit status=Indeterminate`; 42 moons; **retired modules drawn: none**;
canvas ink 46,835 px, hash changed under a real drag. **FAILED on two counts:** (a) my check
asserted on the DRAWN planet radii `[28,32,41,42,49]` and called it an encoding — it is not, it is
the perspective divide, and the check was wrong, not the chart; (b) `modules-unbanded` was **0**,
so §3.3's common case was not exercised at all.

**Iteration 2.**
*Hypothesised:* expose the MODEL radii in the scene graph so the constraint can be proved from what
was drawn, and store a reading that actually contains computed-bandless modules.
*Changed:* `baseR`, `orbitR` and `orbitRate` added to the scene-graph bodies; the driver stores an
A5 reading with three computed, bandless modules — which is what A5's own specification requires of
every module in it, not an invented state.
*Measured after:* `MODEL planet radii: [17]` — one value. `MODEL moon orbit radii: [63]` — one
value. `orbital rates: [0.22]` — one value. Moons by state:
`{computed 6, computed_unbanded 3, abstained 11, not_called 16, not_relevant 6}`.
**FAILED on legibility:** in the screenshot the near half of the ring projected in FRONT of the sun
and A1 and A4 covered the words `PROJECT STATUS / Indeterminate` — on the very state the order says
to get right first.

**Iteration 3.**
*Hypothesised:* the ring lay too deep in z; and the sun's words were painted before the bodies.
*Changed:* ring plane moved towards the screen plane; the sun's words painted **last**, over
everything, on a small scrim.
*Measured after:* words readable. **FAILED partially:** the new plane made the ellipse TALL, and A2
and A6 fell outside the 620px canvas.

**Iteration 4.**
*Changed:* ring made wide and shallow (`y ×0.34, z ×0.16`).
*Measured after, at 1280px and 1024px:* all six planets in frame, sun words readable, everything
else unchanged. **GOAL MET.** Final measurement, both viewports identical:

```
attrs: modules 42, modules-lit 6, modules-unbanded 3, modules-dark 11, modules-na 6,
       modules-notcalled 16, categories 6, categories-lit 2, health Indeterminate
SUN  : state=unlit  status=Indeterminate
MODEL planet radii [17]   moon orbit radii [63]   orbital rates [0.22]
MOONS by state: not_relevant 6, abstained 11, not_called 16, computed 6, computed_unbanded 3
moon categories drawn: A1 A2 A3 A4 A5 A6      RETIRED MODULES DRAWN: []
canvas 1151×620 (1280px) / 905×561 (1024px), ink 32,329 px, hash moves under a real drag
```

### Goal two — the Signal Flow as convergence. **REACHED.**

**Iteration 1.**
*Measured:* `neural_flow.js` drew four left-to-right columns (documents, modules, categories,
status). Structurally convergent, but it read as a pipeline, it drew **eleven** categories, and —
the defect §4.2 names — **every category drew a line all the way to the status node**, a category
with no posture separated only by opacity 0.14 against 0.35.
*Hypothesised:* the layout must be radial and inward, and an unresolved stream must physically stop.
*Changed:* the whole geometry replaced with three concentric rings on one centre; population
restricted to the six; a category with no posture terminates at 45% of the way in, blunt-capped,
dashed, no arrowhead, with a drawn terminus dot and `data-edge-terminates="short"`; the centre
prints `Indeterminate` when that is the stored status; the stale `FB_CATS`/`RAW_MODS` fallback made
unreachable.
*Measured after, at 1280px:* six categories, 42 modules, 27 document rows, four streams `short` and
two `at-centre`, centre text `['Project','Status','Indeterminate']`, no retired module label drawn.
**FAILED on legibility:** my first arc control point was `(cos of the outer angle, sin of the inner
angle)` — not a point on any circle. Every edge swung across the middle and the six category
streams were invisible inside a hairball. Reported, not quietly corrected.

**Iteration 2.**
*Changed:* one helper, `arcPath(a1,r1,a2,r2)`, putting the control point on the angular bisector
(short way round) just outside the mid-radius, so every edge stays inside its own annulus.
*Measured after, both viewports:* the edges read as an inward swirl; the four blunt-ended streams
and the two arriving streams are distinguishable in the screenshot. **GOAL MET.**

```
headers: 27 SUPPORTED DOCUMENT TYPES / 4 UPLOADED ON THIS PROJECT
         42 MODULES IN SERVICE / 6 WITH A CURRENT RESULT
         6 WEIGHTED PERFORMANCE CATEGORIES / 2 CARRY A POSTURE
         GOVERNED PROJECT STATUS / INDETERMINATE
Cost and EVM Performance             terminates=at-centre  arrowhead=yes
Schedule Performance                 terminates=short      arrowhead=no
Cost Risk                            terminates=short      arrowhead=no
Document-Derived Condition Signals   terminates=at-centre  arrowhead=yes
System Dynamics and Complexity       terminates=short      arrowhead=no
Delivery Quality Performance         terminates=short      arrowhead=no
drawn blunt termini: Schedule Performance, Cost Risk, System Dynamics and Complexity,
                     Delivery Quality Performance
centre node text: ['Project', 'Status', 'Indeterminate']
RETIRED MODULE LABELS DRAWN: []
```

### Goal three — the category list and the surfaces agree with the roster. **REACHED.**

**Iteration 1.** *Measured:* the registry at runtime gives 101 registered, 41 retired, **60 in
service**, per category `A1 10, A2 6, A3 7, A4 10, A5 5, A6 4, B1 4, B2 1, B3 5, B4 1, C1 7`;
`is_retired` is true for A5.1, A5.5 and B4.4. The two specifications still described all three as
in service. *Changed:* both specifications, as quoted in §2. *Measured after:* the specifications
now state five in A5 and one in B4, matching `registry.service_index()` exactly.

**Iteration 2.** *Measured:* `python3 server/tools/build_client_taxonomy.py --check` was **already
red at `4857a82`**, on BOTH client artifacts, over a trailing comma left in the B4 module list when
Run 89 retired B4.4. Content was right; the bytes were not. *Changed:* regenerated both from the
authorities (not hand-edited). *Measured after:* `--check` prints "both client artifacts are
exactly what the authorities generate".

### Goal four — the Indeterminate brief, seen. **REACHED (as a measurement).**

One iteration. Rendered in Chromium at 1280px and 1024px on a stored row whose
`project_status` is `Indeterminate`. **Nothing about the brief was changed.** §4 below is what it
says.

---

## 4. What the Indeterminate brief looks like in the browser

This is the rendered text, at 1280px, on the row whose stored `project_status` is `Indeterminate`
(`required_assessed ['A1']`, `required_missing ['A2','A3','A6']`):

```
EXECUTIVE BRIEF: RUN 76 REPRODUCTION
Reporting period: 2026-08 · grouped analysis across 11 signal categories
RECOMMENDATION
INDETERMINATE no course follows from the bands this period. The posture is Indeterminate,
set by A1.7 in A1, reading TCPI: 0.998, the cost efficiency the remaining work must achieve
to finish within budget, within the efficiency already planned, band Green; A1.8 in A1,
reading VAC: $256,175 under budget (1.4%), band Green; A4.7 in A4, reading no figure stated,
band Red. The cost performance index is 0.952, read from the pay_application. The schedule
performance index is 0.98, read from the pay_application and schedule_update. 9 modules
produced a figure this period, 12 produced none, 4 categories carry no status (A2, A5, B1, B2).
SIGNAL PATTERN
RED (1 category): A4.
GREEN (1 category): A1.
NO BAND (4 categories): A2, A5, B1, B2.
KEY DRIVERS
CPI: 0.952 (no band stated)
SPI: 0.980 (no band stated)
CPI came from the pay_application.
SPI came from the pay_application and schedule_update.
REQUIRED ACTIONS
Routine monitoring appears sufficient this cycle
It may be helpful to confirm the latest earned-value inputs are current
Generated from stored log · Aug 30, 2026 · 51 modules · LOW confidence
```

**Do the unassessed categories read as absences rather than failures?** Partly, and this is the
worst thing on the page. They are named under "NO BAND (4 categories): A2, A5, B1, B2" — the word
is *absence*, not *failure*, so as far as it goes it reads correctly. **But the list is the wrong
list.** It names only the categories that have a stored reading with no band. **A3 and A6 — two of
the four required categories, and two of the three that are the actual reason the status is
Indeterminate — are not mentioned anywhere in the brief.** They were never called, so they have no
stored reading, so they fall out of the count. A participant reading this brief would not learn
that Cost Risk and Delivery Quality Performance were never assessed. It also names B1 and B2, which
under the Run 90 ruling are not performance categories at all and are not on either chart, so the
brief's list and the charts' populations disagree with each other in both directions.

**Is the sentence "The posture is Indeterminate, set by A1.7 in A1 …" right?** No, and it reads
badly. Indeterminate is not *set by* A1.7, A1.8 and A4.7 — those are the three modules that DID
assert a band. Indeterminate is set by the ABSENCE of A2, A3 and A6. The sentence reuses the
band-driver phrasing built for a real status and applies it to a status whose whole meaning is
that no driver exists.

**Are the assessed adverse conditions legible?** Yes. A4 Red is named in the recommendation
sentence with the module (A4.7) that set it, and again under SIGNAL PATTERN. A1 Green likewise, with
both figures and their units. CPI 0.952 and SPI 0.980 appear under KEY DRIVERS with the document
each was read from. That half of the brief is clear and sourced.

**Two counts in it are stale.** The header says "grouped analysis across **11** signal categories"
and the footer "**51** modules" — the row has readings for six categories, and 42 modules are in
service in the six the charts draw. Neither figure corresponds to anything the reader can see.

**Does REQUIRED ACTIONS read acceptably?** No. On a row where the platform has positively refused
to certify a posture and one assessed category is Red, it says *"Routine monitoring appears
sufficient this cycle"*. That is reassurance issued on top of a refusal to judge, and it is the
single line most likely to mislead a participant.

**Is the decision card reachable from the brief?** **No.** The brief contains exactly two controls:
its own collapse header and "Regenerate ↺". Its text never mentions a decision or a
recommendation card (measured: `briefMentionsDecision = false`). The Governance Decision section
IS on the same page — `#section-d-decision`, heading "GOVERNANCE DECISION", badge "No data" — but
it is collapsed, it exposed **no controls at all** in this state, and nothing in the brief points
to it. A participant reaching the end of the brief is given no route onward.

**None of this was changed. §6 of the order makes this a measurement, and the fixes are the
owner's to order.**

---

## 5. Every surface that lists categories or modules

| Surface | Population or lookup | Agreed with the registry? |
|---|---|---|
| `assets/js/taxonomy.js` `LIN_CATEGORIES` | **population** | Content yes; **bytes no** — `build_client_taxonomy.py --check` was red at `4857a82`. Regenerated. |
| `assets/js/categories.js` `LIN_CATEGORIES` | **population** | Same defect, same fix. I did not otherwise touch it. |
| `window.LIN_TAXONOMY_COUNTS` (both files) | **counts** | Already correct: 101 / 60 / 41 / 59 / 1, matching `registry_index()`, `modules_in_service()`, `retired_modules()`. |
| `assets/js/projectnet2d.js` (Signal Network) | **population** | Was eleven categories, 60 moons. Now the six, 42 moons, via `performanceCategories()`. |
| `assets/js/neural_flow.js` `buildModel()` | **population** | Was eleven categories. Now the six. |
| `assets/js/neural_flow.js` `FB_CATS` / `RAW_MODS` | **population (fallback)** | **DID NOT AGREE.** Ten legacy categories, 98 legacy module names — "Cat 1 Quantitative EVM", "Monte Carlo EAC Forecast", "DSM Propagation", "Rework Feedback", "Tornado Chart" — written against the retired Cat 1-10 scheme and never updated through Run 43's or Run 89's retirements. It ran whenever `LIN_CATEGORIES` failed to load and would have drawn retired modules. Made unreachable; arrays kept, unreferenced. |
| `assets/js/detail.js` section badges | **counts** | Read `projectCats()` / `projectModuleCount()` — correct against the registry, but they named 11 and 60 over charts drawing 6 and 42. Re-derived as `chartCatCount` / `chartModuleCount` from `performanceCategories()`. |
| `assets/js/detail.js` category panel | **population** | Already correct — reads `LIN_CATEGORIES` at runtime. |
| `assets/js/knowledge.js` handbook prose | **counts** | Figures correct (all `taxCounts()`-derived). **One sentence did not agree:** "The 41 modules not in service were retired at Run 43" — 38 were, three were retired at Run 89. Changed to "at Run 43 and Run 89". |
| `assets/js/app.js` About page `[data-taxcount]` | **counts** | Already correct — filled from `LIN_TAXONOMY_COUNTS`. |
| `assets/js/app.js`, `signals.js`, `export.js`, `decision.js` module lists | **population** | Already correct — all iterate `LIN_CATEGORIES` at runtime. |
| `assets/js/decision-ui.js` module label table | **lookup** | Carries A5.1, A5.5, B4.4. **Left alone**, per §5.3 and Run 43D — and it is sequence-bearing. |
| `assets/js/ds_defensibility_data.js` / `_evidence.js` | **lookup** | Carry all three retired ids and their evidence. **Left alone**, per §5.3. |
| `assets/js/charts3d.js` per-module renderers | **lookup** | Carry DSM Rework Propagation and Rework Feedback Loop renderers. **Left alone.** |
| `specifications/A5_system_dynamics.md` | **population** | **DID NOT AGREE.** Fixed, §2.1. |
| `specifications/B4_decision_optimisation.md` | **population** | **DID NOT AGREE.** Fixed, §2.2. |

---

## 6. Every premise in the order that proved false against the tree

1. **§3, "Three.js is available at r128" — FALSE, and more comprehensively than the briefing
   suspected.** There is no three.js in the tree at any revision. `find` for `*three*` outside
   `.git` returns nothing. `assets/vendor/globe.gl.min.js` is **globe.gl 2.34.4**, which bundles
   three internally but exports **only `window.Globe`** — no `THREE` global — and it is lazy-loaded
   by `globe.js` for the globe view alone; `index.html` never loads it. So `THREE.OrbitControls`
   and `THREE.CapsuleGeometry` are absent not because r128 lacks them but because `THREE` does not
   exist on the page. Nothing was added: `assets/vendor/ASSETS.md` states "**Nothing loads from a
   CDN**", and the tree already has its own 3D idiom — the pure-canvas rotate-then-perspective
   projection in `charts3d.js`, which is what both Run 82 and this run use.
2. **§3, "Rebuild the Signal Network chart in 3D as a solar system" — the premise that it is not
   one is FALSE.** Run 82 Part D already built it as a 3D solar system with planets, moons, orbits
   and a centre. The work this run needed was population, the sun's rule, the not-assessed states,
   and stripping the meanings out of the geometry — not a rebuild.
3. **§2's exclusion list is INCOMPLETE.** It names Data Integrity, Signal Synthesis and Decision
   Optimisation. It omits **B2 Evidence Combination (1 module in service)** and **B3 Regulatory and
   Authority Thresholds (5 in service)**, both of which are project-level categories that would
   otherwise have rendered. The catch-all "and any other category in service" covers them, so the
   rule is unambiguous and I excluded them; the enumeration is not.
4. **§2's category names are loose.** Resolved against the tree, not the order: "Schedule" is
   **A2 Schedule Performance**; "Document Signals" is **A4 Document-Derived Condition Signals**;
   "Systems and Dynamics" is **A5 System Dynamics and Complexity**; "Delivery Quality" is
   **A6 Delivery Quality Performance**. The six are exactly `A1 A2 A3 A4 A5 A6`, which is exactly
   the key set of `models_gov.WEIGHTED_VOTING_CATEGORY_WEIGHTS` with C1 held out by an executable
   assert — and exactly the project-level group-A categories in the generated client roster, which
   is how `performanceCategories()` derives them rather than writing them out.
5. **The briefing's registry CSV path is wrong.** There is no
   `server/app/simulation/module_registry.csv`. The registry CSV is
   **`p0-baseline/module_renumbering_map.csv`**, and that is where the three `RETIRED Run 89` notes
   live.
6. **§2's "so the charts cannot drift from the roster the way the counts did before Run 89" assumes
   the roster is hand-maintained on the client. It is not.** `assets/js/taxonomy.js` and
   `assets/js/categories.js` carry a GENERATED block written by
   `server/tools/build_client_taxonomy.py` from `registry.service_index()`. Retired modules were
   **already absent** from both before this run — 60 modules, A5 with five, B4 with one, and no
   `A5.1`, `A5.5` or `B4.4` anywhere in either array. The charts read that block, so establishing
   retirement "from the registry at runtime" was already satisfied; what I added is the derivation
   of the six from it.
7. **§5.2's implied premise that the surfaces are the problem is mostly false.** Every runtime
   surface I found already read `LIN_CATEGORIES`. The two that did not agree were the two
   specifications §5.1 already names, one stale sentence in `knowledge.js`, and one unreachable
   fallback roster in `neural_flow.js`.

---

## 7. Real versus harness measurements, and which suites were not run

**There is no `ANTHROPIC_API_KEY` in this environment. No model behaviour is reported anywhere in
this document.**

**REAL.** Everything about the two charts and the brief. Chromium at
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome` (`playwright install` was not run), viewports
**1280×3200** and **1024×3200**, driving the real FastAPI application over a real HTTP port against
a **scratchpad copy of `server/dev.db`** — never production Postgres. Every figure quoted is read
back off the drawn scene graph, the rendered SVG's own attributes, the rendered DOM text, or the
canvas pixels. The canvas non-vacuity test is real: 32,329 ink pixels and a hash that CHANGES when
the system is rotated through the canvas's own drag handler. `PAGE ERRORS: []` in all four
viewport passes. Driver: `server/tools/drive_run90_charts.py`, log kept.

**HARNESS.** The stored row itself. Its documents are stub-extracted PDFs and three of its category
readings (A2 abstained, A5 computed-bandless, B1 out-of-order, B2 failed, A4 computed Red) are
written directly with `store_reading`, following Run 81's and Run 82's stated precedent, so that
every state renders on one page. **A1 was pressed for real** through
`projectcategoryapply` and computed Green from the two voting modules. The project status
`Indeterminate` and its `project_status_basis` are the server's own, derived by Run 89's gate from
that mixture; they are not written by the driver.

**Suites run, and the result of each:**

| Suite | Baseline `4857a82` | This run |
|---|---|---|
| `test_run16_final_flow_and_rail` | 74/74 | 70/74 → re-pointed → **74/74** |
| `test_run24_empty_project_diagram` | 53/53 | 50/53 → re-pointed → **53/53** |
| `test_run23_signal_flow_truthfulness` | 36/37 | **37/37** (improved) |
| `test_run25_rail_removal` | 55/56 | **56/56** (improved) |
| `test_run6_known_answer` | 487/489 | **488/489** (improved) |
| `test_run20_declared_production_changes` | 126/131 | **128/131** (improved) |
| `test_run26_counts_and_wiring` | 53/54 | 53/54 (unchanged) |
| `test_run63_four_charts` | 20/24 | 20/24, **failure list byte-identical** |
| `test_run10_state_protection` | 83/84 | 83/84 (known pre-existing) |
| `test_run38_frozen_immutability` | **10/17, measured at the real `4857a82`** | 10/17 (identical) |
| `test_run39_frozen_immutability` | **13/19, measured at the real `4857a82`** | 13/19 (identical) |
| `test_document_rows`, `test_run21_reset_disclosure`, `test_run32_client_authority`, `test_run36_instrument_qualification` | — | 38/38, 31/31, 18/18, 76/76 |
| `test_run22_production_tree_completeness` | 45/48 | 45/48 — standing manifest drift from Runs 79-89 |
| `node server/tools/test_run89_indeterminate_brief.js` | ALL PASS | **ALL PASS**, unmodified |
| `build_client_taxonomy.py --check` | **RED** | **GREEN** |

A methodological note, reported because it nearly misled me: I first took the baseline by
materialising `4857a82` into a scratchpad directory with `git ls-files --with-tree` + `git show`.
**That baseline is not trustworthy for any git-aware suite** — with no `.git` present,
`test_run38` and `test_run39` aborted on "the freeze candidate is present in this repository" and
scored 14/17 and 15/19, which looked like a regression against my 10/17 and 13/19. I re-measured
by committing my work and `git checkout 4857a82` in the real repository: **10/17 and 13/19**,
identical. The apparent regression was an artefact of my own baseline method.

**Suites NOT run, stated plainly.** I ran the 24 suites that name `projectnet2d`, `neural_flow` or
`build_client_taxonomy`, plus the freeze gate, plus the Run 89 brief harness. **I did not run the
rest of the ~200-suite corpus**, including everything covering extraction, the document contracts,
the participant package, portfolio health, and the simulation layer. Nothing under `server/app/`
changed, so the simulation suites had nothing to see, but I did not run them and I am not claiming
they are green.

**THE FREEZE GATE WAS NOT REACHED.**
* `server/tools/run37_freeze_gate_campaign.py` **refused to start**: "BASELINE NOT GREEN, refusing
  to run the campaign: RESULT: 32/34 checks passed". That is the standing pre-existing
  `test_run37_freeze_gate.py` state, not this run's doing.
* `server/tools/build_run37_acceptance.py` **refused with exit 3 at Run 57's CANDIDATE fixed
  point**, before evaluating any of the 15 blocker classes:
  ```
  CANDIDATE as set in this file : 6ccb650cf8de57c8a09afb114dea0b6d70710368
  CANDIDATE as computed         : 9145db21f886b980627a73fc7dadd13272e4b3b8
  REFUSING TO PROCEED. ... This generator does not edit the constant: the assignment is the
  owner's, and only the guesswork is removed.
  ```
  **I did not set it.** The tool states the assignment is the owner's, and this order does not name
  it. So I cannot report a B01–B15 tally this run; I can only report that the gate refused before
  producing one. **Committed to the branch. NOT MERGED. NOT PUSHED.**
  `V26_TO_V27_SEQUENCE_EXCEPTION` remains uncomposed; it is the owner's to write.

---

## 8. Anything found and not fixed

1. **The Indeterminate brief, all of §4.** The omission of A3 and A6, the "set by A1.7" sentence,
   the "11 signal categories" and "51 modules" counts, "Routine monitoring appears sufficient this
   cycle", and the absence of any route from the brief to the decision card. §6 of the order makes
   goal four a measurement; none of it was touched.
2. **The Governance Decision section exposed no controls at all** on this row. Consistent with the
   briefing's warning that `recommendation_options.js:149` returns `available: false` on every
   current row. Not investigated further; not in scope.
3. **`test_run37_freeze_gate.py` is 32/34** and blocks the gate campaign from starting. Standing.
4. **`test_run22_production_tree_completeness` 45/48** — the pinned production manifest has not
   been re-taken since Runs 79-89 added twelve files and changed twenty-four. Standing.
5. **`test_run38` 10/17 and `test_run39` 13/19** — the frozen-package guards still expect
   `sim-2026.08-v41`; the tree is at v43. Standing, and byte-identical at `4857a82`.
6. **`registry.modules_in_service()`'s docstring still says "The 63 modules in service"** and
   `detail.js:3013` still carries the pre-Run-89 per-category roster "A5 7 … B4 2 -- 63" in a
   comment. Both are comments, neither renders, neither was changed.
7. **Label crowding on the Signal Flow.** At 1280px some module and document labels overlap in the
   upper-left and upper-right of the outer rings. The chart is legible and every node is present,
   but it is not tidy. Not fixed; it would want a label-collision pass, which is more than this
   order names.
8. **The Signal Network screenshots are post-drag.** The non-vacuity probe rotates the system
   through the canvas's own drag handler before the screenshot is taken, so the saved PNG is not
   the default camera. The scene-graph measurements are taken both before and after and agree.

---

## 9. Every guarantee, verified or not met

| Guarantee | State |
|---|---|
| `main == origin/main`, clean tree, starting commit `4857a82` | **VERIFIED** by me at start |
| Only what the order names was edited | **VERIFIED** — 11 files, listed in §7's commit set |
| Every specification edit quoted before and after, verbatim | **VERIFIED**, §2 |
| The retirement wording is the registry's own, not a new vocabulary | **VERIFIED** — quoted from `p0-baseline/module_renumbering_map.csv` |
| `SIMULATION_VERSION` moved only if a module computes differently | **VERIFIED NOT MOVED** — no file under `server/app/` changed |
| No migration added | **VERIFIED** — head remains `0030_extraction_contract` |
| Both charts rendered in a real browser at 1280px and 1024px | **VERIFIED** — four passes, `PAGE ERRORS: []`, screenshots and computed-DOM measurements kept |
| Only the six categories render, in either chart | **VERIFIED** from the drawn scene graph and the rendered SVG |
| No retired module renders, in either chart | **VERIFIED** — `RETIRED MODULES DRAWN: []` in both, asserted on drawn node ids and drawn label text, not on a grep of the file |
| Nothing is encoded in radius, size, orbital speed or rings | **VERIFIED** — model radii `[17]`, orbit radii `[63]`, rates `[0.22]`, one value each, read from the scene graph |
| An Indeterminate row draws an unlit sun with its assessed categories still coloured | **VERIFIED** — sun `state=unlit`, A1 Green and A4 Red both drawn |
| No stream is drawn arriving at the centre from a category with no posture | **VERIFIED** — four `terminates=short`, no arrowhead, blunt termini drawn |
| The three recommendation checks are untouched and still pass | **VERIFIED** — `test_run89_indeterminate_brief.js` ALL PASS, `detail.js` brief code unmodified |
| The Indeterminate brief was not restyled | **VERIFIED** — no change to `scriptedBrief`, `briefGate`, `briefEvidence` |
| No sequence-bearing file moved | **VERIFIED** — the empty tuple, `()`, declared explicitly |
| `scope_signal_inputs`, Run 79's wiring, Run 81's precedence, `computed_results`, Conservative Dominance, Run 89's gate, Run 87's seam and `COMPARISON_ONLY_MODULES` untouched | **VERIFIED** — all live under `server/app/`, which has zero changed files |
| No more than five iterations on any goal | **VERIFIED** — 4, 2, 2, 1 |
| Every failed iteration reported | **VERIFIED** — three failures reported in §3, plus my own mis-measurement of the planet radii and my own untrustworthy first baseline |
| The freeze gate ran | **NOT MET — and I say so plainly rather than arguing it.** The campaign refused on a non-green pre-existing baseline; the acceptance generator refused at Run 57's CANDIDATE fixed point, which is the owner's constant to set. No B01–B15 tally exists for this run. |
| Every suite green | **NOT MET, and not claimed.** §7 lists what ran, what improved, what is standing, and what was not run. |
| A query against the owner's own data | **NOT RUN.** Nothing this run needed one. |
