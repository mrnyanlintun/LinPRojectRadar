# Run 86 — work to the goal, up to five loops, aligned to architecture v2

No migration was added this run. The migration head is unchanged: `0030_extraction_contract`.

Repository `/home/user/LinPRojectRadar`, branch `main`, starting commit `c20cb35` (verified
clean, `main == origin/main`, both at `c20cb35bef88c5377d19b3534051b066b99d8458`). Venv: no
repository virtualenv exists; the system `python3` at `/usr/local/bin/python3` (3.11) was used
throughout. `ANTHROPIC_API_KEY` is unset (verified). Every extraction and specification call in
this run's proofs went through the StubExtractor or the recorded applier and is labelled as
harness, never as the model.

Commits this run: `f237172` (A2.8 route + committed test), `a211407` (panel harness + handoff),
plus this report's commit. T6_HANDOFF.md gained ONE dated Run 86 section, inserted above the
Run 59 section per the file's run-number ordering; nothing below it was edited.

---

## 1. FIRST SECTION — the owner's deployment sequence, verbatim runnable

```bash
# 1. Migrate. From the repository root, against the deployment database:
cd server
python -m alembic upgrade head

# 2. Verify (sqlite3 <db> — or psql, same SQL):
SELECT version_num FROM alembic_version;
--  expected: 0030_extraction_contract
SELECT COUNT(*) AS null_fingerprint_rows FROM documents WHERE extraction_contract IS NULL;
--  every NULL row re-extracts exactly once on its next identical-byte upload, then caches
```

**3. Re-upload, into the same project and period each document already lives in:**
- **D08 and peers** — the cost report carrying the contingency pair and every other document
  whose row still has a NULL fingerprint. Identical bytes are fine; the fingerprint mismatch
  alone triggers exactly one re-extraction and restamps the row.
- **The re-issued risk register (D15) as .docx** with per-risk probability and cost-impact
  columns in the table shape of section 3b. The rows are read from the .docx bytes on the
  platform side; no PDF table extraction exists or was built.
- **The regenerated look-ahead document** — its extraction contract GREW this run (activity
  table, horizon, status date; shape in section 3a), so its fingerprint moved
  (`d1cd40f8…` → `6885d651…`) and any cached look-ahead extraction re-extracts once,
  automatically, on re-upload.

```bash
# 4. After re-uploading the cost report, verify the contingency figures landed:
SELECT DISTINCT field, value FROM observations
 WHERE field IN ('originalContingency','remainingContingency') AND value IN (920000, 892400);
```

**5. One press of "Generate signals for every period" (projectcomputeall), then one press of
"Process all" on the category panel.** Expected outcomes per in-scope module:
- **A3.2** computes the contingency burn (measured this run on stored rows: burn 0.67).
- **A3.3** computes labor productivity (measured: 0.83 on the resource report's fields).
- **A2.7** computes the milestone trend (measured: 3 milestones, worst variance 37 days).
- **A2.8** computes the ready fraction from the re-uploaded look-ahead document's own table.
- **A3.6** computes a P80 from the .docx risk register plus the period's BAC.
- **A6.2** computes the recordable incidence rate (measured: 2.22 per 200,000 hours).
- **A6.1** computes bandless, disposition NOT_ESTIMABLE (specification — ruling required, §4).
- **A6.3** computes, disposition APPLICABILITY_NOT_ESTABLISHED (specification — ruling required).
- **A6.4** abstains awaiting `contractorAssessmentRecord` (specification — ruling required).
- **B1.2** abstains on its assembled-arms package / weight policy (specification — ruling required).

---

## 2. Per goal — reached or not, every iteration

### Goal one: the target modules produce readings on the architecture's terms — PARTLY REACHED; four modules are STOPs on their specifications

All ids were verified against the registries and dispatch tables before touching anything
(A2.7/A2.8 in `models_ext.py` A2_EXTENSIONS, A3.2/A3.3/A3.6 in A3_EXTENSIONS, A6.1–A6.4 in
`models_cat89.py`, B1.2 at `models_gov.py:944`). B4.4/B4.5 confirmed distinct
(`WhatIf_Scenario_Matrix`, `Decision_Sensitivity_Matrix`) and untouched.

**Baseline measurement (iteration 0).** `adminrecompute` of `PRJ-R73-1787844588-A` period 8 —
the full 14-doc-type period — on a byte-for-byte clone of `server/dev.db`, at current head:

```
COMPUTED A2.7 | 3 milestones followed; largest variance against original commitment 37 days
COMPUTED A3.2 | Contingency is 55 per cent consumed at 83 per cent complete, burn 0.67
COMPUTED A3.3 | 0.06 linear metres of conduit an hour against 0.08 planned, index 0.83
COMPUTED A6.1 | ...establishes no applicable, assessed and satisfied requirement population...
COMPUTED A6.2 | recordable incidence rate 2.2222222222222223 per 200,000 employee hours
COMPUTED A6.3 | the jurisdiction and permitting authority for this site are not established...
ABSTAIN  A2.8 | Awaiting a look ahead schedule...
ABSTAIN  A3.6 | Awaiting a cost risk model...    (this project's register is a PDF)
ABSTAIN  A6.4 | Awaiting a governed contractor assessment record.
ABSTAIN  B1.2 | Insufficient data... the cost forecast computation abstained this period.
```

A sub-finding on the way there: `projectcompute` first returned the CACHED live result for
that period (computed under an older head), on which A6.2 read "recordable cases and employee
hours worked are not both recorded" although both observations exist — the stored row predates
Run 81's `oshaRecordableIncidents` selection fix. The recompute at current head computes the
real rate. Append-only is a standing ruling, so this is by design, but the owner should know:
**stored readings reflect the head they were computed under until the period is recomputed** —
which is exactly what the deployment sequence's Process-all press does.

1. **A3.2 Contingency Burn Rate — VERIFIED** computing on stored rows (0.67 above).
   Deployment of the 0030 cache fix is goal three.
2. **A3.3 Labor Productivity — VERIFIED** computing on the resource report's quantity/hours
   fields (0.83 above).
3. **A2.7 Milestone Trend — VERIFIED** computing on stored rows. The milestone-table shape
   still matches the assembler: `schedule_activities._HEADINGS` recognises
   activity/milestone id, description, baseline start/finish, current/actual/forecast finish,
   percent complete — a document-stateable table, legitimate under rule 1. D05 untouched.
4. **A2.8 Look-Ahead Schedule Health — REACHED, built this run.** Three iterations:
   - *Iteration 1.* Measured baseline (fingerprint `d1cd40f8f9148cf3…`, A2.8 abstaining).
     Change: grew the `lookahead_schedule` extraction contract with
     `lookahead_activities_json`, `lookahead_horizon`, `lookahead_status_date`; added the
     prompt shape hint on the `milestones_json` precedent; new reader
     `server/app/lookahead_table.py` (maps the table's printed headings onto the canonical
     fields; a status is uppercased, never guessed; no category invented; no row dropped);
     `lookAheadSchedule` assembler in `_run69_structures` (all-or-nothing: rows + horizon +
     status date, longest inventory wins, `setdefault` so a governed-intake structure is
     never displaced). Measured: 11/13 — the module reading was not found because the
     harness read the HTTP response, which does not carry module results.
   - *Iteration 2.* Hypothesis: readings live on the stored `computed_results` row. Change:
     read `module_results` from the row. Measured: entries present but keyed
     `module_id`/`method_class`, not `model`/`name` — still 11/13. A wrong key guess, kept
     here as the order requires.
   - *Iteration 3.* Matcher fixed. Measured: **16/16.** A2.8 COMPUTED
     "7 of 10 activities planned in the 3 weeks look ahead window are free of open
     constraints, a ready fraction of 0.7" — through the real
     upload→extract→persist→assemble→compute route against stored rows. The fingerprint
     moved (`6885d6510cd93e16…` ≠ `d1cd40f8…`); a stale-fingerprint look-ahead row
     re-extracted exactly once and was restamped; the second identical upload served from
     cache with zero calls. Committed: `server/tools/test_run86_lookahead_and_risk_docx.py`
     at `f237172`. (The StubExtractor supplied the table content — harness, not the model;
     what is proven is the production contract, cache, persistence, assembly and module
     arithmetic.)
5. **A3.6 Cost Risk P80 — REACHED (synthetic-.docx proof committed; the PDF register's
   honest abstention documented).** Same committed test: a deterministic synthetic .docx
   (zip entry timestamps pinned — Run 73's lesson) with the recognised headings, uploaded
   through the real route; `_persist_project_risks` read 4 rows from the STORED BYTES (not
   from any model reply — the register is deliberately never asked for as a JSON field);
   `register_exposure` → `costRiskModel` → A3.6 COMPUTED: "Simulating 4 risk events against
   a base cost of $10,000,000 over 20000 trials puts the eightieth percentile total cost at
   $12,600,000". No PDF table extraction built. Table shape verified against
   `risk_register._HEADINGS` and printed in section 3b.
6. **A6.1 Quality Compliance — STOP.** It COMPUTES today (bandless, NOT_ESTIMABLE, measured
   above) on recorded audit evidence. The architecture's inspections-passed proportion is
   forbidden by the specification itself — quoted in section 4: an inspections-passed ratio
   is a summary, and "section 13 forbids substituting a summary for a denominator". The
   corpus path is specified to always reach NOT_ESTIMABLE.
7. **A6.4 Contractor Performance — STOP, with the composite's legs measured.** The legs
   verified from the registry: **A6.2 Safety_Performance** and **A6.3
   Environmental_Compliance** (`models_cat89.py:456–459`). A6.2 COMPUTES the OSHA rate on
   stored rows (2.22 above) — that leg is architecture-conformant already. A6.3 computes
   only the APPLICABILITY_NOT_ESTABLISHED disposition on the corpus path, and its
   specification states that path "always" reaches it (quoted, §4) — so the environmental
   leg cannot yield observations-closed-over-logged without a specification ruling. A6.4's
   own specification reads `contractorAssessmentRecord` and states "There is no
   corpus-assembled path" — the weighted quality/safety/environmental composite contradicts
   it directly. Both the specification (§5.1) and the module source (§5.5) are untouchable,
   so the composite is not built, and the cascade is reported: even after a ruling on A6.4,
   A6.3's leg needs its own ruling first.
8. **B1.2 Weighted Voting — STOP.** The specification defines a weighted vote over the four
   assembled ARMS with a mandatory `signalWeightPolicy` and expressly no default (quoted,
   §4) — not the architecture's weighted sum of CATEGORY statuses, and equal default
   weights are forbidden. Measured today it abstains earlier still: "Insufficient data …
   the cost forecast computation abstained this period", with parameter provenance
   UNSUPPORTED ("The weights are an ad hoc split with no source"). On comparison-only:
   `models_gov.py` states "All three remain ADVISORY_ONLY and non-voting. Voting is exactly
   A1.7 and A1.8" — B1.2 cannot vote on PROJECT status directly; but
   `contributes_to_project_status('B') == True`, so a computed B1.2 `status_color` would
   enter the B1 CATEGORY worst-of rollup, which feeds project worst-wins. Whether that
   satisfies "can never set or alter the project status" is part of the owner's ruling; it
   could not be exercised empirically because B1.2 cannot compute without a weight policy
   no project holds.

**Out of scope, as the architecture rules:** A5.2 and A5.4 not built. Run 85's printed
shapes for them could not be re-printed verbatim: no Run 71–85 report file exists in the
tree (see §5 and §8); they are reported superseded by the architecture's deferral of their
group, by reference.

### Goal two: the category panel reads at a glance — REACHED, one iteration, zero style changes

Every prior claim treated as unverified. One iteration: measured first
(`server/tools/drive_run86_panel_widths.py`, committed at `a211407`) in a real Chromium
(`/opt/pw-browsers/chromium-1194`, headless=new, over HTTP, nothing primed — the harness
never calls `LinResults.prime`), on a fresh scratch DB seeded through the real routes
(upload → computeall → category A1 applied by the recorded applier → one stored row per
remaining state). Measured at BOTH widths, all checks PASS, so no change was needed and
none was made:

```
AT 1280px (panel width 1151px, 11 category rows)   AT 1024px (panel width 905px)
 PASS 1. each row's headline is exactly one figure pair
      — A1:"2 of 10 produced a status"; A2:"0 of 6 produced a status"; …   (same at 1024px)
 PASS 2a. the five-figure breakdown is NOT in the collapsed head
 PASS 2b. the breakdown exists behind the expansion (not deleted)
 PASS 3a. every Process button's box lies inside its own row's box
 PASS 3b. every Process button vertically overlaps its row's name cell
 PASS 4a. no row overflows horizontally  — []
 PASS 4b. no row's head grew beyond single-line height (<=44px)  — []
 PASS 6. all four states present and distinguishable
      — {A1:computed, A2:abstained, B1:out_of_order, B2:failed, rest not_run}
 PASS 7. processing line bold, pulsing, Run-85 styling computed live
      — {"text":"Processing A1…","className":"dcat-status-line is-processing",
         "fontWeight":"700","color":"rgb(16, 96, 168)",
         "animationName":"dcat-processing-pulse","animationDuration":"1.2s"}
 PASS 5. explanation text byte-identical across widths
      — sha256 af6b1ae44e60bdd4c8089c3821486f7d493a5a54f1733e581f44dcf62ee4f0e1 (both widths)
RESULT: ALL CHECKS PASSED
```

Constraints: (1) explanation text byte-for-byte — verified by sha256 over the textContent of
every `.dcat-reason` and `.dcat-note`, identical at both widths, and no JS/CSS was edited at
all; (2) four states distinguishable inside the expansion — verified above; (3) modules report
what their evidence supports — the panel renders stored server rows only, unchanged; (4)
nothing outside the panel restyled — `git diff HEAD -- assets/css/radar.css assets/js/detail.js`
is EMPTY (no diff to assert over: zero bytes changed); (5) no control added/moved/removed —
none touched; button locations in §7; (6) Run 85 processing-line styling — computed styles
asserted live above, including the `dcat-processing-pulse` animation (the reduced-motion
off-switch remains in the stylesheet, unmodified).

### Goal three: the 0030 deployment path asserted end to end — REACHED

1. Clean throwaway SQLite, `python3 -m alembic upgrade head`:
   ```
   INFO ... Running upgrade 0029_observation_withdrawn -> 0030_extraction_contract,
        documents.extraction_contract: the fingerprint of the contract an extraction was made under
   sqlite> SELECT version_num FROM alembic_version;
   [('0030_extraction_contract',)]
   ```
2. `test_run85_extraction_contract.py` re-run against current head, AFTER this run's
   contract growth: **12/12** — first upload pays one call and stamps the fingerprint;
   identical re-upload cached, zero calls; a stale-fingerprint row re-extracts exactly once,
   still one documents row, restamped; the non-vacuity leg (comparison neutralised → the
   stale replay is detected) passes. This run's test extends the coverage to the grown
   look-ahead doc type: **16/16** (goal one item 4).
3. D08 on a byte-for-byte clone of `server/dev.db` — the row's fingerprint was NULL;
   identical-byte re-upload through `/exec`:
   ```
   before: fingerprint = None | doc_type = cost_report
   re-upload of identical bytes: was_cached = False | extraction calls = 1
   second identical upload:      was_cached = True  | extraction calls = 0
   after: fingerprint = 40aa817d5a73caae... == current contract fingerprint (match = True)
   SELECT ... FROM observations WHERE field IN ('originalContingency','remainingContingency')
     AND value IN (920000, 892400);
   -> ('originalContingency', 920000), ('remainingContingency', 892400)   [present; my
      verification query joined document_uploads and so repeated the rows — production
      should use the DISTINCT query in section 1]
   ```
   The stub replayed the row's OWN previously stored extraction — the invalidation decision,
   restamp and observation persistence are what was exercised, never the model.
4. The deployment sequence is section 1, first, verbatim runnable.

---

## 3. Document contracts for the owner's generating model, verbatim

### 3a. The look-ahead document's activity table (for A2.8)

The document must state, on its face:
- **Look-ahead horizon** — the window, e.g. `3 weeks` (extracted as `lookahead_horizon`).
- **Status date** — the date the look-ahead stands at, e.g. `2026-07-31`
  (`lookahead_status_date`, returned as YYYY-MM-DD).
- **One table, one row per planned activity**, with these columns (these exact headings are
  recognised; the listed variants also match):

| Activity ID | Activity Description | Constraint Status | Constraint Category |
|---|---|---|---|
| A-101 | Work package 1 | Open | Materials |
| A-102 | Work package 2 | Cleared | |

Recognised heading variants — Activity ID: activity id / activity no / activity number /
activity code / task id / id / no / ref. Description: activity description / description /
activity name / task / work description / scope. Constraint Status: constraint status /
constraint / constraints / constraint state / readiness. Constraint Category: constraint
category / constraint type / constraint kind / type of constraint.

Rules the module enforces (a broken row makes A2.8 abstain for the whole window, in its own
words — nothing is repaired or defaulted): every row a unique, non-blank Activity ID;
Constraint Status exactly the word **Open** or **Cleared** (any letter case); every **Open**
row states a Constraint Category (the document's own word — Materials, Engineering, Permits,
Labor, Equipment, …); at least one activity; horizon and status date both stated.

### 3b. The risk register .docx table (for A3.6, the re-issued D15)

A **.docx** — only .docx tables are read platform-side; a PDF register yields no rows and
says so. One table whose FIRST row is the headings. Recognised headings per field (any one
from each set; a trailing unit qualifier such as "($)", "(USD)", "(days)" is accepted):

| Field | Headings recognised |
|---|---|
| Risk id | **Risk ID**, risk no, risk number, risk ref, ref, id, no, number, risk code, item |
| Description | **Risk Description**, description, risk, risk event, event, risk statement, title, name, threat |
| Probability | **Probability**, likelihood, probability of occurrence, chance, probability rating, p — a number: `0.40` or `40%` |
| Cost impact | **Cost Impact ($)**, cost, cost consequence, financial impact, impact cost, cost exposure, value at risk, estimated cost impact — a currency amount |
| Status | **Status**, risk status, open closed, open or closed, state, current status |

Optional and also recognised: Category, Time Impact (days), Risk Score, Owner, Response
Strategy, Mitigation Status, Residual Risk. Example — exactly the shape proven end-to-end in
the committed test:

| Risk ID | Risk Description | Probability | Cost Impact ($) | Status |
|---|---|---|---|---|
| R-01 | Differing site conditions at the north abutment | 0.40 | 1,200,000 | Open |
| R-02 | Steel delivery slips past erection window | 0.25 | 2,000,000 | Open |
| R-03 | Permit renewal delayed by agency backlog | 0.10 | 800,000 | Open |
| R-04 | Design rework of MEP risers | 0.50 | 600,000 | Open |

A row enters the P80 only when BOTH probability and cost impact parse as numbers; a
band-worded row ("High") is stored with its refusal and A3.6 reports it rather than guessing.
The period must also carry a BAC (a monthly report) or A3.6 abstains on its base cost.

---

## 4. Specification-vs-architecture conflicts, module by module — the owner's rulings

The 63 specifications were not touched. Exact texts:

**A6.1 Quality Compliance** (`specifications/A6_delivery_quality.md`). Architecture intent:
proportion of inspections passed, fed by the inspection report and quality audit. The
specification:

> *Governed path.* `qualityRequirementRegister` — a mapping carrying a `requirements` list,
> each row with `requirement_id`, `applicable`, `assessed`, `satisfied`, `criticality`,
> `source`, `status`, `corrective_action`, `period` and `provenance`.
> *Corpus-assembled path*, used only when the governed structure is absent.
> `qualityAuditScore`, `totalFindings`, `criticalFindings` — any one of them present triggers
> assembly. **The assembly supplies no `requirements` list**; it carries these three onto the
> structure as `recorded_audit_evidence`.

> 3. **Structure present with `recorded_audit_evidence` and no `requirements`** — the corpus
> path — the module **computes** with `quality_compliance_rate: null` and
> `disposition: "NOT_ESTIMABLE"`, reason verbatim: `"the project's Quality Audit evidence is
> recorded below, but it establishes no applicable, assessed and satisfied requirement
> population, so no compliance rate is measurable and none is estimated"`. An audit score, a
> findings count and a critical-findings count are **summaries**, and section 13 forbids
> substituting a summary for a denominator.

An inspections-passed proportion is exactly such a summary ratio, and the specified corpus
path does not even read `items_inspected`/`items_passed`. STOP — the module computes
(bandless, NOT_ESTIMABLE) today, and the architecture's proportion needs the owner's ruling
on this text.

**A6.3 Environmental Compliance** (same file). Architecture intent: observations closed over
logged from the environmental compliance report (Run 72's D24 feed). The specification:

> *Corpus-assembled path*, used when the governed structure is absent.
> `environmentalComplianceRate` and `environmentalViolations` — either present triggers
> assembly, and they are carried as `recorded_environmental_evidence`. **The assembly
> deliberately supplies no jurisdiction, no permitting authority and no permit id**, because
> the corpus carries none and inventing any one of them would be inventing regulatory
> applicability.

> 3. **Authority or jurisdiction not established** — the module **computes**, with
> `environmental_compliance_rate: null`, `disposition: "APPLICABILITY_NOT_ESTABLISHED"`,
> reason verbatim: `"the jurisdiction and permitting authority for this site are not
> established, so environmental conformance is not assessed"`. This is the disposition the
> corpus-assembled path always reaches.

STOP — the architecture's rate cannot be produced by the corpus path the specification
defines; the composite's environmental leg is blocked on this ruling.

**A6.4 Contractor Performance** (same file). Architecture intent: a weighted composite
across quality, safety and environmental compliance. The specification:

> **Required inputs.** `contractorAssessmentRecord` — a mapping, and the only input read.
> There is no corpus-assembled path.

> **Bands.** **None. This module asserts no band and none may be attached.**
> Calibration-pending. **No aggregate is computed** unless a governed aggregation policy is
> supplied, because inventing contractor-assessment weights is forbidden; `aggregate` is
> otherwise `None`.

STOP — the composite is a different module from the one specified, and the specified module
itself forbids an aggregate without a governed weighting policy.

**B1.2 Weighted Voting** (`specifications/B1_signal_synthesis.md`). Architecture intent: a
weighted sum of CATEGORY statuses, comparison-only, equal weights acceptable only if the
specification permits a default. The specification:

> **Required inputs, by their exact `signal_inputs` field names.**
> `signals` — the assembled arms, read through `governed_signals_from_project`.
> `signalWeightPolicy` — a mapping carrying `weights` (a weight per signal id), `set_by` and
> `authority`. **Required. There is no default weight anywhere in this function**, so a
> project with no policy cannot be given one implicitly.

> 3. `signalWeightPolicy` absent or not a mapping: `"Awaiting a weighting policy for this
> project's governed signals. A weighted vote cannot be taken without stated weights, and
> none is assumed."`

And the untouchable module source (`server/app/simulation/models_gov.py`) matches: it votes
over the arms, and its block comment states "Weighted Voting now requires a GOVERNED
WEIGHTING POLICY and abstains without one, because the four literals it used had no
authority behind them and section 14 forbids inventing weights. … All three remain
ADVISORY_ONLY and non-voting. Voting is exactly A1.7 and A1.8." Equal default weights are
expressly forbidden. STOP.

---

## 5. Premises in this order that proved false against the tree

1. **"Run 85's panel goal, dispatched and never reported"** — the headline/breakdown/button
   layout was already built and committed (the code carries Run 81/82's comment blocks at
   `detail.js specCountsHtml`/`specCategoryRowHtml`); this run re-measured it all from the
   rendered DOM as ordered, at the two widths no prior run had measured.
2. **"Run 85 … stored row 507be211…/8"** — no such `computed_results` row exists in
   `server/dev.db`. The equivalent full-corpus row is `PRJ-R73-1787844588-A` period 8, which
   is what this run measured. Relatedly, NO report file for runs 71–85 is committed anywhere
   in the tree (repo-root `REPORT_*` ends at run 70), so every "Run 85 printed X" premise
   had to be re-derived from code.
3. **"run_weighted_voting refuses without signalWeightPolicy — the exact abstention Run 85
   measured"** — at current head on real stored rows B1.2 abstains EARLIER, on the assembled
   signal package ("… the cost forecast computation abstained this period"). The
   weight-policy refusal is real in the source but is not the abstention a real project
   currently shows.
4. **"test_run85_extraction_contract.py is committed"** in `server/tests/` — it lives in
   `server/tools/`; `server/tests/` ends at run 35.
5. The order's framing of A6.1 ("Run 85's qualityRequirementRegister demand … retired for
   this module under rule 1") understates the tree: A6.1 already computes on a corpus path
   without the register; the live block is the specification's summary-vs-denominator rule,
   not a missing input.
6. Minor: dev.db's D08 documents include both `D08_resource_report.pdf` and
   `D08_cost_report.pdf`; the contingency pair (920,000 / 892,400) lives on the cost-report
   document's extraction, and that is the row the goal-three proof re-extracted.

## 6. Real versus estimated measurements

**Real (executed, output pasted or committed):** every module reading in section 2 (stored
`computed_results` rows recomputed at current head on the dev-DB clone); the fingerprints
before and after; 16/16 and 12/12 test results; the alembic version query; the D08 clone
re-extraction with cache-hit/restamp/observation queries; the browser panel geometry,
computed styles and explanation-text hashes at 1280px and 1024px. **Harness, labelled, never
the model:** the extraction CONTENT in every proof (StubExtractor replay — the production
contract fingerprint, cache decision, persistence, assembly and module arithmetic are what
is exercised); the A1 category reading served by the recorded applier ("servedBy=recorded").
**Estimated: nothing.** Where only the owner's production data can settle a point, the
queries are written out in section 1.

## 7. Where every Process button and any touched control ended up

No control was added, moved or removed; no JS or CSS byte changed. Measured positions of all
eleven Process buttons (x, y, width, viewport): at **1280px** every button at x=1066, w=136,
one per category row at y = 888 (A1), 935 (A2), 982 (A3), 1029 (A4), 1076 (A5), 1123 (A6),
1170 (B1), 1217 (B2), 1264 (B3), 1311 (B4), 1358 (C1) — a single right-hand column, one
button inside each row. At **1024px** the same column at x=816, w=136, y = 949 … 1419 in the
same per-row order. "Process all" remains in the `.dcat-actions` bar above the list; the
processing status line remains between the actions bar and the list. The sequence-bearing
files — `decision.js`, `decision-ui.js`, `workspace.js`, `intake.json`, `debrief.json` —
carry the empty tuple: none moved.

## 8. Found and not fixed

1. The stale-live-result behaviour (§2 baseline): a period keeps readings computed under an
   older head until its documents change or an admin recompute; the owner's real projects
   will show pre-Run-81 A6.2 readings until recomputed. Left as designed (append-only);
   resolved per period by the deployment sequence's recompute.
2. No REPORT file for runs 71–85 is committed to the tree.
3. A6.3's corpus assembly cannot carry closure semantics for D24 observations — blocked on
   the §4 ruling.
4. The B1.2 category-rollup exposure: a computed B1.2 band would reach worst-wins through
   the B1 category status (`contributes_to_project_status('B') == True`) — flagged;
   simulation/ untouchable this run.
5. All 593 document rows in `server/dev.db` carry NULL fingerprints; each pays exactly one
   re-extraction on its next identical re-upload. Expected 0030 behaviour, not a defect.
6. The stray PM-membership rule ("this project already has an active PM; revoke them
   first") means deployment re-uploads must be done by each project's existing PM login —
   worth knowing for the owner's Process-all pass.

## 9. Guarantees

- A2.8, A3.6, A3.2, A3.3, A2.7, A6.2 computed readings on the canonical production route
  against real stored rows: **verified** (A2.8/A3.6 against rows created through the real
  upload route by the committed 16/16 test; the others on the dev-DB clone recompute).
- A6.1, A6.3, A6.4, B1.2 on the architecture's terms: **not met — STOP**, specification
  texts quoted in §4 for the owner's ruling (the order's sanctioned outcome).
- B1.2 "can never set or alter the project status": **could not be fully verified** — the
  ADVISORY_ONLY / non-voting rule is in the source, but the category-rollup path exists and
  B1.2 cannot currently compute to exercise it. Said plainly rather than argued.
- Goal 2 items 1–4 and constraints 1–6: **verified** by computed layout in a real browser at
  both widths (§2), with zero style changes; the CSS diff is empty, which is the strongest
  form of "nothing outside the panel restyled".
- Goal 3 items 1–4: **verified**, outputs pasted.
- 63 specifications untouched; `scope_signal_inputs` untouched; Run 79 wiring, Run 81
  precedence, computed_results-as-history untouched; fusion and recommendation checks
  untouched; `server/app/simulation/` untouched; SIMULATION_VERSION `sim-2026.08-v42`
  unmoved — **verified**: this run's changes are additive (a new extraction field set, a
  new assembler key) and the frozen fixture corpus carries no `lookahead_activities_json`,
  so nothing any module computes on the frozen corpus changes; no document type added (the
  27 stand — a field grew on an existing type, the Run 78/80 precedent); nothing renamed to
  the M/C/D scheme; no `git add -A`/`git add .`; `git status --porcelain` before every
  commit; no stub or harness result reported as the model's behaviour; the acceptance
  generator not run; THE MINT not attempted; no stray files left (scratch work confined to
  the session scratchpad); push left to the coordinator. **Budget note:** all goals were
  reached or stopped within their iteration limits (goal one item 4 used three iterations;
  goals two and three one measured pass each); nothing ran out.
