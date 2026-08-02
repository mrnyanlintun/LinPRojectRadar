# The Methods tab: the sweep the syntax error hid

873 checks across 18 suites pass. `tests_render.html` passes 22/22 in a real browser. The Methods
tab now **renders** and measures clean: all 51 topics, 645,818 characters of rendered text, zero
PCEIF, zero PDAF, zero em dashes, zero module ids, zero "Cat N", zero "PH.N", zero page errors,
with the standing description present verbatim in both its short and long forms.

PR #196 is updated and left unmerged for your review.

---

## Part 1. The real scope, measured before rewriting

You were right that the earlier figures were an estimate. Here is what was actually in there.

| | Reported before | Actually found | Note |
|---|---|---|---|
| PCEIF, `knowledge.js` | 37 | **40 occurrences on 37 lines** | the earlier number counted lines, not occurrences |
| PCEIF, `ds_defensibility_data.js` | 49 | **49** | matched |
| PDAF | not stated | **0 in the whole repository** | confirms `NAMING_AUTHORITY.md` |
| "Cat N" scheme | not counted | **405 occurrences** (knowledge.js 361, defensibility 44) | far larger than the PCEIF count |
| Module ids rendered to the user | not counted | **101**, via one line in `modDoc` | see below |
| Em dashes | not counted | **0 in both files** | already swept |
| Bare export paths | flagged | **still bare, 0 notices** | unchanged, out of scope, see Part 5 |

**Two findings change the shape of the job.**

**The "Cat N" scheme was ten times the PCEIF problem, not a footnote to it.** 405 occurrences
against 89 for the name. Removing the name alone would have left every topic titled
"Cat 7.4: Interval-valued Fuzzy Sets" and every cross-reference reading "requires Cat 6.1
corroboration".

**Module ids reached the user through one line of code, not through prose.** `modDoc()` rendered
`<strong>${esc(m.n)}</strong> ${esc(m.name)}` as the heading of every one of the 101 module
entries, and the nav prefixed every module topic with a `CAT_LABEL_BY_ID` lookup. This is why the
count of ids in the source (101) was almost exactly the count a reader would have seen. Three
render paths, not 101 strings, were the actual defect.

## Part 2. Whether the same mechanical error happened elsewhere

**Checked, and the answer is no. The two entries in `knowledge.js` were the only ones.**

The renumbering commit `e34fa50` touched 13 files. Method and result:

- **All 10 JavaScript files it modified parse.** `node --check` on `app.js`, `categories.js`,
  `deepdive.js`, `detail.js`, `ds_defensibility_data.js`, `forcenet.js`, `knowledge.js`,
  `projectnet2d.js`, `signals.js`, `simulations.js`: all clean. (`knowledge.js` only because of
  the step-5 fix; it was the sole casualty.)
- **The diff's own arithmetic confirms it.** The commit removed 103 `{ n: ...` opening lines and
  added 101. The two-entry difference is exactly the two truncations, and both were in
  `knowledge.js`.
- **The surviving structure is intact.** `knowledge.js` now holds exactly 101 module objects, all
  ids distinct, matching the registry's declared count.
- **`ds_defensibility_data.js` was edited by a different, safe mechanism.** Its diff only rewrites
  the *value* of `"id_display"` fields in place. No line was deleted, so this class of error could
  not occur there.

I could not find any other truncation, and I am reasonably confident there is none: the parse check
is decisive for a syntax-breaking cut, and the 103-to-101 arithmetic accounts for both deletions.
What a parse check **cannot** rule out is a cut that left valid syntax, for example a deleted entry
whose absence merely shortens a list. The registry cross-check (101 entries, ids distinct, matching
`GROUP_ASSIGNMENT.md`'s 100 registered plus the excluded document risk score) is what covers that
case, and it agrees.

**Nothing tests any of this in a browser**, which is why a fatal error in a 3,000-line file
survived for weeks. A one-line `window.LIN_KNOWLEDGE` assertion in `tests_render.html` would have
caught it on day one. I did not add it, because adding a check to the render harness is a new
surface and the brief scoped this session to content; it remains the cheapest available insurance.

## Part 3. What was swept and rewritten

Mechanical replacements were applied completely first, then the passages needing judgement.

### Mechanical, driven by `p0-baseline/module_renumbering_map.csv`

The CSV is an old-id to new-id to name to group mapping, which made the id sweep verifiable rather
than a guess. Every one of the 33 distinct `Cat X.Y` tokens present resolved to a method name with
no misses. Applied in order: ranges first (`Cat 7.1-Cat 7.9` to "the evidence-combination
methods"), then `Cat X.Y (Name)` collapsed to the name alone so no sentence read "Name (Name)",
then compound `Cat 6.1/Cat 8.1` forms, then bare ids, then bare `Cat N` category numbers to the
family name from the CSV's `category_name` column.

Three render paths were changed so ids cannot reappear from the data:

- `modDoc()` renders `m.name` only. The `n:` keys stay in the source as keys.
- The nav's `modNavBtn()` strips any leading ordinal or `Cat X.Y:` prefix; `CAT_LABEL_BY_ID` is
  deleted.
- `renderDsDefensibility()` renders `cat.name` without `cat.num`, since the names
  ("Cost / EVM Forecasting") already read as purposes.

`CATEGORY_NAV`'s `num` field now carries the **group** a category's modules belong to, by name, so
the nav reads "Project Health / Quantitative EVM" instead of "Cat 1 / Quantitative EVM".
Twenty topic titles and twenty-one eyebrows were rewritten. Portfolio Health topics lost their
`PH.N` prefixes. Ampersands in rendered group labels became "and".

### Judgement, rewritten against the standing description

- **"What is PCEIF"** is now **"What Opus Gubernatio is"**, opening with the long-form standing
  description quoted verbatim. The two-layer architecture section, the 103-module flow diagram,
  and the "what's different from standard EVM" comparison were replaced with the evidence-to-
  decision sequence and the four groups by purpose.
- **"PCEIF Framework Overview"** is now **"The governance architecture"**, and it says plainly
  that there is deliberately no named framework and why, then describes the mechanism. The
  seven "architectural principles" were cut to the five that are true of the shipped system; the
  "four-layer governance architecture" and the "conformance" section (which defined what it means
  for a third-party implementation to conform to a framework that does not exist) were removed.
- **The flow diagram's box labels** were rewritten; they were rendered SVG text, not comments.
- **The praxis chapter list** in the defensibility data lost the chapter titled "The PCEIF
  Governance Framework", now "The Governance Architecture", and its lead now states the
  contribution as empirical evidence about professional response, not a framework.

### Removed rather than caveated, because the code does not support them

Per your instruction. Each was checked against the server before deletion.

| Claim | What the code says |
|---|---|
| The eight-code **override taxonomy** (`data_doubt`, `context_knowledge`, `timing`, `authority_directed`, `evidence_escalation`, `evidence_reduction`, `fairness_gate`, `emergency`) | **None of these strings exists anywhere in the repository.** Replaced with the two real closed vocabularies, `DISPOSITIONS` and `REASON_CODES` in `research_decision.py`, both server-validated. |
| **"Learning governance"** analysing override patterns to drive framework revision | Nothing implements it. Section deleted. |
| The **`redReview` advisory** raised when conflict K reaches 0.55 | `taxonomy.js` reads `row.red_review`, and **the server never writes that field**, so the flag is permanently false. Deleted. |
| **Portfolio Health votes in project status** ("fusing all eleven registry category statuses") | `compute.py` fuses only categories whose group contributes, and `contributes_to_project_status()` excludes **C and D**. Rewritten to say which groups vote and why the other two do not. |
| The **document risk threshold row** (Green below 0.30, Red at or above 0.70) | `docRiskScore` is an **input** the extraction model supplies, not a server computation; it has no server-side threshold to quote. Row removed, with a note saying why. |
| The **"48 business hours" response deadline** presented as a platform-wide rule with a regulatory basis | The only 48-hour values in the code are per-category rows in `CATEGORY_ACTIONS`, alongside "10 business days" and "next monthly cycle" for other categories. Restated as category-specific, and the "Why 48 hours" and "Why Program Director" sections, which argued from FAR Part 34 and OMB Circular A-11 for a specific named official and clock, were removed. |
| The **six-row authority matrix** including a "Critical" state routed to a Contracting Officer / Executive Board | `deriveDecision()` produces four branches, and `Critical` is a normalised-away alias, not a state the analytical layer emits. Replaced with the four branches as implemented. |
| **"Mandatory rationale"** | The decision **form** requires it; the **server** stores it as an optional unvalidated field. Restated precisely, which also keeps it consistent with the About tab's "a rationale field captured". |
| **"101 distinct computations"** in three places | The registered count is 100. Corrected, with the document-risk-score footnote. |

The `insufficientData()` / `sim.js` / `simulations.js` references were also removed from the status
rules topic, because those are client-side files that do not load on any participant-facing route;
the server is the ground truth and the topic now says so.

## Part 4. Verification

A parse check was explicitly not enough, so the tab was rendered and its DOM measured.

| Check | Result |
|---|---|
| Server suites, each on a freshly migrated SQLite | **873/873 across 18 suites**, 0 suite failures |
| `tests_render.html`, headless Chromium against the dev server | **22/22** |
| Methods tab renders | **51 topics, 51 nav buttons, 11 groups, 0 failed to render** |
| Rendered text measured | **645,818 characters** across all topics with every collapsible expanded |
| PCEIF / PDAF in the rendered DOM | **0 / 0** |
| Em dashes in the rendered DOM | **0** |
| Module ids (`[ABCD]N.N`) in the rendered DOM | **0** |
| "Cat N" and "PH.N" in the rendered DOM | **0 / 0** |
| Standing description, short and long form, verbatim | **both present** |
| "deliberately no named framework" present | **yes** |
| Page errors on load and render | **none** |
| Cross-tab consistency: groups by name, no ampersand forms, footnote present | **both tabs agree** |
| "103" as a computation count, either tab | **0** |

The one surviving `PH.1` string in the source is the **search key** of `DSD_ID_REWRITES`, the
render-time scrubber whose entire purpose is to remove that id from output. Flagging it would be
flagging the fix as the defect, the same exemption the module-id test already grants to
`MODULE_NAMES`.

## Part 5. Not done, and why

- **Export paths still carry no notice, attribution, or copyright.** Unchanged and deliberate:
  adding one means adopting liability wording, which is yours to approve. It stays flagged in
  `DISCLAIMERS_DRAFT.md`.
- **The live operational notice is still unreviewed but can display.** Unchanged, same reason.
- **The em dash sweep on `auditor.js` and the legacy researcher surfaces** is untouched. Both
  Methods tab files were already at zero.
- **A `window.LIN_KNOWLEDGE` assertion in `tests_render.html`** was not added, for the reason in
  Part 2.
- **`taxonomy.js` carries a stale comment block** stating the project rollup fuses "all 11 registry
  category statuses (10 project categories + Portfolio Health)" and that "Portfolio Health still
  votes here". That is the same false claim I removed from the Methods tab, and it is wrong for the
  same reason. It is a code comment, not user-facing text, and `taxonomy.js` was outside this
  brief, so I left it and am reporting it instead. It will mislead the next reader of that file.

## Claims I could not verify against the code

- **The five-status vocabulary including Complete.** Confirmed as far as fusion: `status_to_mass`
  maps a Complete source to best-case Green evidence, and Complete is handled as a project-end flag
  rather than a fused band. I did not trace which server path first sets it.
- **The fairness gate's blocking behaviour.** The gate is present in `deriveDecision()` as
  `fairnessGateRequired`, and `project.fairnessSensitive` drives it. I did not drive the UI to
  confirm the control actually blocks recording this session; the description rests on the code as
  read.
- **Method-level thresholds inside individual module entries.** Two were verified directly against
  the server and are stated in the status rules topic: the Monte Carlo bands (5% / 10%) and the
  CUSUM constants (target 1.00, k = 0.5σ, H = 5σ, amber at 60% of H). The remaining per-module
  `bands` values in the module reference were **not** individually re-derived from
  `server/app/simulation/`. They are carried over from the pre-existing entries.
- **The regulatory citations that remain** (OMB Circular A-11, FAR Part 34, NIST AI RMF, ISO/IEC
  42001 and the rest of the standards crosswalk) are subject-matter assertions about external
  documents. They are not verifiable from this repository, and the crosswalk already says it is not
  a certification claim.

## Handoff

`T6_HANDOFF.md` updated.

---

## Judgement calls to review

1. **Group names became the nav's category label.** `CATEGORY_NAV`'s `num` now reads "Project
   Health", "Recommendation and Governance" and so on. Where a legacy category's modules split
   across two groups, the label follows the majority: the old Cat 8 holds five Group B modules and
   four Group A, and is labelled "Recommendation and Governance". A reader expanding it finds four
   delivery-quality methods that belong to Project Health. The alternative was splitting the
   category in two, which is a restructure, not a sweep.
2. **The legacy category structure was kept, only relabelled.** The Methods tab still navigates by
   the ten old categories, now under group names. Rebuilding the tab around the four groups is the
   structurally correct end state and a much larger job; I did the sweep you asked for rather than
   starting it.
3. **The "Why Program Director" and "Why 48 hours" sections were deleted, not rewritten.** They
   were the most confidently argued prose in the file, citing FAR Part 34 and OMB Circular A-11 to
   justify a named official and a specific clock. Nothing in the code names a Program Director as
   the required approver or sets a 48-hour deadline platform-wide. If those are real agency policy
   commitments you intend to make, they should come back in your words, sourced.
4. **The six-row authority matrix became four rows.** Removing "Critical / Contracting Officer /
   Executive Board / Immediate" removes the most severe escalation tier from a governance
   description. It is not a state the analytical layer emits.
5. **The override taxonomy was replaced, not deleted outright.** I substituted the real
   `DISPOSITIONS` and `REASON_CODES` vocabularies, which are genuinely closed and server-validated,
   so the section still says something true about how judgement is classified. If you would rather
   the Methods tab not enumerate the research instrument's response vocabulary at all, say so.
6. **Method thresholds inside the module reference were left as written.** I removed thresholds
   from the assistant's answers in step 5 because I could not verify them; here I left the module
   reference's `bands` intact, because a module reference with no thresholds is not a reference.
   The two thresholds I did verify are stated; the rest are carried. This is an inconsistency
   between two surfaces and it is deliberate, but you may disagree.
7. **The praxis lead in the defensibility data now states the research contribution** as empirical
   evidence about professional response rather than a framework closing the signal-to-action gap.
   That is your research positioning, rewritten by me to match `NAMING_AUTHORITY.md`. Worth reading
   in your own voice.
8. **The Isolation Forest, Linear Programming and Pareto Frontier descriptions were kept**, with
   their method names, in the decision-optimization and portfolio overviews. Your own refactor
   register lists these among the fourteen label-to-algorithm mismatches needing rename or
   reimplementation before a formal defense. The register is rendered on the same tab and says so
   in its own section, so the caveat is present and adjacent, but a reader browsing only the
   overview sees the method name uncaveated. Removing them would have removed the description of
   capability that does exist under a label that overstates it, which is a rename decision, not an
   editing one.
9. **`taxonomy.js`'s stale comment was left in place** rather than corrected in passing. It is
   outside the Methods tab and I chose the reporting boundary over the fix.
10. **`ds_defensibility_data.js` boilerplate was edited across all occurrences at once.** Twenty
    identical `accreditationBasis` strings, twelve `assumptionsLimitations`, eleven more, and eight
    `uncertaintyMethod` strings were replaced by exact-match global substitution. They were
    byte-identical duplicates, so the edit is uniform, but it touched 51 module entries in one pass.
