# Run 140 — mitigation suggestions for every non-Green reading

**`SIMULATION_VERSION` did not move**, and did not need to. It is `sim-2026.09-v70` before and
after, and `git diff` over `server/app/simulation/` across the whole run is empty. No band,
threshold, weight or posture rule moved. **One migration was added and it was genuinely
required**; head moves `0033_recognition_matches` → `0034_module_mitigations`.

Starting commit `ae6734e`. Ending commit `ffc0057`, pushed. Tree clean. Every figure below was
re-taken by me on merged main.

---

## The stance change

**Dated 2026-09-05. Origin: Run 140.** Until this run the platform stated a finding and asked a
question, and said so in eleven places. From this run the Suggested Decision card also offers
candidate mitigations for each reading that is not Green, aimed one band up: Red toward Amber,
Amber toward Yellow, Yellow toward Green.

**What is still refused, and is now stated positively rather than by omission:** no deadline, no
approval authority, no assigned owner, no corrective-action template, no invented figure, no
cross-module remedy the evidence does not support, and no unvalidated text stored or rendered.

**The reason a mitigation is now permissible is not that the platform acquired an approved
knowledge base.** It did not. The defence is that a composition is *recorded, replayable and
attributable*: composed once against a code-built context, validated before storage, stored with
its date, model and provider, replayed verbatim thereafter. A deadline or an authority would not
be defensible on that basis, which is why those stay refused.

### Where the wording was updated

Ten sites were amended and one was deliberately left alone. Two of them were not in my survey and
were found during the build.

| # | site | what changed |
|---|---|---|
| 1 | `decision_brief.py:6-10` | "does not produce an action recommendation… because each requires an approved knowledge base" → produces a finding, a question **and candidate mitigations**; the knowledge-base reason is kept for exactly the four things still refused |
| 2 | `decision_brief.py:13-16` | "prescribes an action" struck from the no-model list; a carve-out added — a model composes candidate sentences only, choosing no status, driver, threshold or authority |
| 3 | `decision_brief.py:18-20` | the counter-example "Resequence work now" replaced, because it had become close to a real mitigation bullet. The line is now **who and when**, not imperative mood |
| 4 | `decision_brief.py:615` | "no remedy is offered" was becoming false; the question itself is unchanged and stated as deliberately so, and "names no authority, because the platform holds none" is kept verbatim |
| 5 | `document_evidence.py:58` | kept and **scoped** — still true of that module, no longer a platform-wide claim |
| 6 | `decision-ui.js:839-843` | **the load-bearing one.** The old wording is quoted so what it forbade still binds; the clause "it is not composed from any figure" is withdrawn as now false |
| 7 | `decision-ui.js:590-593` | amended identically to (1), with an instruction to amend the pair together |
| 8 | `decision-ui.js:596-598` | "an action" struck, same carve-out |
| 9 | `export.js:84-87` | Run 98's history kept; the general clause narrowed; the workbook now carries what the card showed |
| 10 | `decision.js:334-338`, `:350-353` | Run 98's *reasons* kept as this feature's design constraint; only "never issues an action" amended |
| — | `simulation/models_cat10.py:156` | **not touched**, correctly scoped to its own module. The stance check asserts it still reads as before, so the sweep is provably complete rather than merely claimed |

**Two sites found during the build that my survey missed.**

- **The card footer**, `app.js:1580`. It read "The platform states a finding and a question." That
  sentence became false three inches above a mitigation block. It now reads: *"The platform states
  a finding, asks a question, and offers candidate mitigations for each reading that is not Green.
  A candidate is a suggestion to weigh, not an instruction: it names no owner, no authority and no
  date."* The following sentence, that a named human reviewer records the decision and nothing
  here triggers any action on its own, is untouched because it remains exactly true. **This is the
  footer the order required be updated.**
- **The note beside the reveal screen's Owner and By-when inputs**, `decision-ui.js:1120-1125`. It
  now states explicitly that those boxes are the reviewer's own response and **nothing composed by
  a model is ever written into them.**

---

## THE DECISION THE OWNER MUST MAKE — mitigations are reveal-gated, by my decision

**This is the most consequential thing in the run and it was not in the order.**

`documents.py:4275-4279` stated, in terms, that the decision brief is **not** gated by the reveal,
and gave its reason: the card is composed from the project's own computed readings, which the
project manager is already shown, while the researcher-authored recommendation package is the
separate thing the gate withholds.

**That reason stops being true the moment the card carries composed remedies.** I verified the
mechanism myself: `_redact_module_actions` strips only the action-bearing keys from module rows,
and the brief is composed *after* redaction from those already-redacted rows, so nothing
downstream redacts it. Shipping as specified would have put platform-composed corrective actions
in front of a participant **before their pre-judgment was locked** — the exact contamination
`documents.py:4063-4083` was written to close, and a compromise of the praxis' controlled
repeated-measures design.

**I gated the mitigations behind the same predicate that already gates the recommendation
package, and left the rest of the brief exactly as it was.** A withheld read carries no
`mitigations` key at all — absent, not empty — is not in the block order, and makes **zero model
calls**. The finding and the question are served unchanged. The comment at `documents.py:4275`
now says what is true, and names the reversibility.

**The decision for you: are mitigations treatment?** If you rule they are not, and should be
visible before lock, it is one predicate. Building it ungated first and discovering this after
data collection began would not have been recoverable, which is why I chose the conservative side
without waiting.

---

## The library population, and each entry's basis

**30 modules, not 28 and not 31.** `registry.service_index()` holds 31 and none is retired; the
orrery's 28 is the A-series subset. **C1.5 is excluded**: `models_cat89.py:402-403` returns
`(None, None, None, None)` for anything outside A6.1–A6.4, so Category 9 is metadata and casts no
vote. It can never band. I verified that myself.

The operative population is not a hardcoded list at all: it is whatever
`decision_brief._adverse_readings` returns — every served row whose `status_color` lowercases to
yellow, amber or red. Shape is then established **from each row's own stored flags**, not from a
table of module ids, so a module added or renamed later needs no edit here.

### Threshold-, override- and worst-wins-shaped

| shape | count | modules |
|---|---|---|
| threshold only | 5 | A1.5, A1.7, A1.8, A2.9, A3.3 |
| threshold **+ hard override** | 14 | A1.6, A1.9, A1.11, A2.1, A2.8, A3.2, A3.5, A4.3, A4.4, A4.5, A4.9, A6.1, A6.2, A6.3 |
| worst-of components, each with its own ladder | 4 | A2.7, A2.12, A4.6, A4.7 |
| categorical / ordinal — **no continuous gap exists** | 3 | A6.4 (CPARS words), A4.8 (reported ratings plus PM disposition), A4.7 route 2 |
| derived from other modules' bands | 2 | B1.1, B1.2 |

**Overrides are the majority, not the exception.** The order named three; **17 of 30** carry a
hard override or a floor arm. All four override flags are consulted on every module.

### Four cases where "one band up" is not what it looks like

Each would have printed a boundary that does not exist, and each is proved individually:

- **A6.1's project-target path bands Green or Red only.** A Red's next band up is **Green**, not
  Amber. The next band is read out of the module's own boundary sentence rather than assumed from
  a four-rung ladder.
- **A1.2 (CUSUM) has no Yellow rung and returns lowercase band strings.** Bands are normalised, so
  an exact comparison cannot silently drop it, and Amber's next band up resolves to Green. **This
  exposed a real defect during the build:** the boundary sentence *says* "there is no Yellow
  rung", and a plain word scan read that as naming one. Fixed by refusing a rung named only
  inside a negation.
- **A6.2's near-miss Amber has no ladder at all.** The gap states that no continuous gap is
  defined and none is invented.
- **A4.7 route 1's boundaries are derived per project** from its own working calendar. Handled by
  the same rule as everything else: whatever the row stored is what is read.

### Where the boundary comes from

**From the stored row, with zero reads into `server/app/simulation/`** — proved by tokenising the
engine and asserting the package name appears nowhere in its code. For 19 of 30 modules the
deciding constant is a module-local literal or a per-project derivation, but `models.banded`
refuses to store a band without its boundary sentence, basis and threshold source, so the
deciding constant is already on the row in the module's own words. **This satisfies the order's
"never copied" rule more strictly than importing a private literal would**, and needed no edit
under the restricted package.

---

## The recomposition trigger, and where reading-identity lives

**There is no reading id, and that is structural.** `documents._result_view` merges per category:
a category the specification layer answered is served from `specification_readings`, one it did
not from `computed_results`. Identity is therefore content, not a foreign key.

`reading_fingerprint` is a sha256 over the module id, the normalised band, the evidence sentence,
the boundary, the basis and basis id, the threshold source, both provenance classes, all four
override flags, the override words, the components, the whole code-built context, the template
version, the provider and the model.

That gives the order's three triggers exactly — a new period, a reassembly moving the band, the
module's figures changing underneath — plus a fourth for free: **switching model recomposes and
keeps both answers**, which is `recognition.py`'s own reasoning.

**Handoff to the v70 reassembly.** The reassembly moves bands and figures, so it changes those
fingerprints, so it **will** recompose every affected mitigation on the next visible read, and
only those. Superseded rows are kept and pointed at by `superseded_by`. Nothing about v70 was
folded into this run; it remains outstanding and untriggered.

---

## The migration, and why it was genuinely required

`0034_module_mitigations`, revising `0033_recognition_matches`, applied against a throwaway SQLite
file. Three reasons, recorded in the migration:

1. The composition is keyed finer than any existing row — project, period, **module**, **reading
   fingerprint**.
2. It must be append-only, and **a column on `computed_results` cannot be**, because a recompute
   replaces that row and the superseded text would go with it.
3. The key must be a content fingerprint, not a foreign key, for the reason above.

Fifteen columns, a uniqueness constraint on the four-part key, and an index on project and period.
Never updated except to set the supersede pointer.

---

## The proofs

All eight, re-run by me together on merged main.

| proof | result |
|---|---|
| 1 · resolver | nothing set → **anthropic / `claude-opus-5`**; role variable wins over account variable wins over code default; an invalid name raises. **The other four roles: I loaded the pre-change file as a separate module and compared 32 role-by-environment resolutions. Zero differences.** |
| 2 · reading, boundary and gap match | for every entry, the reading, next band, gap, every candidate and the composed-on line are found **verbatim** in the rendered HTML, with an explicit assertion that no figure was reformatted |
| 3 · validator | one output carrying an invented figure, a named role and a date → **all three refused in one pass**. The refused text is never stored: the row holds the absence line instead. A figure that *was* supplied is accepted, so rule three is not a blanket ban on numbers |
| 4 · replay | first composition **1 call**; second render of the same reading **0 calls**, with the entire served entry identical, not just the prose. Through the real view path: 1 call, then still 1. **Counted, not assumed** |
| 5 · unbanded | a floor case and an abstention each produce no context, no block and **0 calls** |
| 6 · override-driven Red | the gap names what fired and what clears it, and states there is no threshold gap to close |
| 7 · failed call | 1 call, serves and **stores** the absence line, and a re-render makes **0 calls** — never silently retried, because the absence is a recorded answer rather than a hole. Groq is not a fallback |
| 8 · exports | every mitigation field compared field-by-field against the fixture in both exports |

**Counts on merged main, taken by me:**

| check | result |
|---|---|
| provider role | 34/34 |
| mitigation engine | 55/55 |
| reveal gate | 20/20 |
| card render | 55/55 |
| exports | 138/138 |
| stance sweep | 40/40 |
| provider switch (regression) | 75/75 |
| actual-cost selection (regression) | 31/31 |
| assembly and precision (regression) | 83/83 |

**The cross-check neither agent could run.** The engine and the surface were built in separate
worktrees against a fixed contract. I verified on merged main that the engine emits exactly the
eleven contract keys, that the renderer and both exports read only keys the engine emits, and
that the absence line matches on both sides. **No mismatch.**

**Injections, each observed and restored:** routing the role to the wrong provider (34 → 24);
changing a different role's model string (34 → 31, localising rather than smearing); truncating a
gap figure in the renderer, which I ran myself (three failures including the character-for-
character assertion, restored to 55/55); the validator's three-at-once refusal.

---

## What the exports now carry

**Audit JSON.** A mitigations list copied through unchanged. **Absent is absent, not empty**: with
no key, the record has no mitigations field at all. Run 98's removals stand and are asserted, and
no entry may carry an owner, assignee, due date, deadline or documentation field.

**XLSX.** A fifth sheet, nine columns, one row per candidate. Where a composition is absent the
sheet writes the fixed absence line rather than leaving a blank to interpret. With no mitigations
the workbook has four sheets, not five with one empty. The other four are unchanged.

**Research export: deliberately not widened.** Its column tuples are checksum-covered, and adding
a column would invalidate every historical committee export. A committee export carrying
mitigations needs a **new export kind**, which is beyond this order. Reported, not built.

**Downstream readers:** none inside the tree; both are browser downloads. Both changes are
additive. Whether an external script of the owner's reads either file is **unproven** and only he
can settle it.

---

## Iteration log

| finding | attempts | proof | disposition |
|---|---|---|---|
| the `mitigation` role and its Opus entry | 1 | resolver executed on every rung; 32 before/after comparisons | RESOLVED |
| the missing Opus string | 1 | table carried none; `claude-opus-5` added, marked catalogue-unverified | RESOLVED |
| a role missing from the other providers' tables | 1 | would have raised on a deliberate reroute; filled from each provider's own spec default | RESOLVED |
| context builder, five shapes | 1 | each shape proved on its own fixture | RESOLVED |
| the A1.2 negated-rung defect | 2 | a rung named only inside a negation is refused | RESOLVED |
| validator, five rules | 1 | three refusals in one pass | RESOLVED |
| storage and supersede | 1 | migration applied; append-only asserted | RESOLVED |
| replay | 1 | call counts 1 then 0 | RESOLVED |
| the reveal gate | 1 | both directions, zero calls when withheld | RESOLVED |
| render and drawer split | 1 | one definition of the three shown, read by both sites | RESOLVED |
| stance sweep | 1 | superseded sentence gone and narrowed wording present, per site | RESOLVED |
| two wording sites the survey missed | 1 | footer and reveal-input note amended | RESOLVED |
| two fixture corrections the validator caught | 2 | "authority" names a party even when external; "approve" narrowed to "approval" | RESOLVED |

Nothing reached the cap. Nothing is BLOCKED.

---

## Not exercised, stated plainly

**No API key exists in this environment. The live composition — the single request to Anthropic —
was not exercised and was not simulated.** What served in its place: a counting fake passed at a
`caller` parameter **in the checks only**; production never passes it. The resolver, context
builder, prompt and its hash, fingerprint, validator, storage, supersede, replay, absence path,
gate, served shape, rendering and both exports all ran against the real code.

`temperature` is never passed. It appears twice in the engine, both times in comments saying so,
and the clients attach it only when a caller asks.

---

## Items found but not fixed

1. **The second adverse-findings drawer.** `detail.js:2924` and `:3109`, on the evidence brief, is
   a second surface listing adverse findings, and two stance sentences there
   (`detail.js:2033`, `:2137`) are now partly stale. **Smallest decision: does the evidence brief
   carry mitigations too, or stay finding-only?** If finding-only, those two comments need the
   same scoping clause the evidence module's sentence received.
2. **`_reading_figure` picks the module's own figure by taking the first numeric `band_*` field in
   sorted key order.** Unambiguous on every row tested, but **whether all 30 modules have exactly
   one numeric `band_*` field is unproven** — no computed corpus exists here. The gap line always
   names which figure it used and which boundary it compared against, so the card stays traceable
   either way.
3. **`claude-opus-5` is catalogue-unverified.** Settled by running, on the deployment:
   `curl -s https://api.anthropic.com/v1/models -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01"`.
   If it disagrees, `AI_MITIGATION_MODEL` re-points it with no code change.
4. **Nothing was rendered in a real browser.** The renderer is proved in a sandbox against a
   fixture and by syntax check; the block's appearance with the real stylesheet at a real viewport
   is **unproven**.
5. **Three suites could not reach a result line here** — they need a seeded participant a bare
   throwaway database does not have. An environment limitation, not a regression; their state is
   unproven.
6. **B1.1 and B1.2 are derived readings** whose mitigation would restate their inputs'. They are
   in the population by the card's own filter. Whether they should be excluded is worth a ruling.
7. **The disposition set stays open**, as the order requires. `research_decision.py:484-494` is
   untouched.

## Confirmations

`SIMULATION_VERSION` `sim-2026.09-v70`, unchanged. Migration head `0034_module_mitigations`.
`git status --porcelain` was checked before every commit and showed only intended files; `git add`
by explicit path throughout. All work ran against throwaway SQLite files in the scratchpad;
production Postgres was never contacted. The v70 recomputation remains outstanding and
untriggered. Three agent branches merged `--no-ff` after I re-took their figures myself.
