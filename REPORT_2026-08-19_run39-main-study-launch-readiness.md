# Run 39: controlled pilot launch gate and study-data collection qualification

**Date:** 2026-08-19
**Disposition:** `MAIN_STUDY_LAUNCH_READY`
**Blocking defects:** 0
**Frozen behaviour changed:** NO

> **Pilot and test observations in this run are not study findings.** Every identity exercised
> was synthetic. No real participant was enrolled, contacted or consented, and **no primary study
> data collection was begun.** Empirical field validation remains **0/100** and will remain so
> until real study observations are collected.

---

## 1. Frozen instrument identity

Re-established mechanically from live authorities, not read from the Run-38 report.
`code_audit/run39_launch_identity.csv` — 15 rows.

| identity | value | live authority |
|---|---|---|
| freeze candidate | `6142d877856ea651ef8d7e905f6d27604b3244f1` | freeze record |
| accepted release | `f983bb020f7a184a5742e1fff09d690b0170f0de` | git |
| freeze disposition | `FINAL_FREEZE_ACCEPTED` | freeze record |
| simulation | `sim-2026.08-v25` | `app.simulation.models.SIMULATION_VERSION` |
| participant package | `og-participant-2026.08-v13` | `tools/participant_packages.CURRENT` |
| synthetic package | `OG-SYNTH-0.6` | freeze record |
| analysis export schema | `og-analysis-2026.08-v1` | `run38_analysis_export` |
| analysis columns | **59** | `ANALYSIS_COLUMNS` and the Run-38 manifest, derived on both sides |
| controlled study | 6 × 6 = 36 | governed design contract |

**Identity drift = 0.**

One identity is recorded `NOT_VERIFIED_HERE` rather than asserted: the voting count is not
exposed as a single live constant, so Run 39 does not re-derive it and does not restate the
number as if it had. It remains carried by the Run-37/38 gates.

### An erratum this run raised

The Run-38 report's prose said the analysis dataset has "58 columns". The live
`ANALYSIS_COLUMNS` tuple holds **59**, and the machine-generated Run-38 readiness manifest
independently recorded `export_column_count: 59`. **The error was in prose only** — every
executable path (manifest, CSV header, R validator) reads the live tuple and used 59 throughout.

Cause: a count was typed instead of derived. Run 39 found it by asserting the number
mechanically and getting a mismatch. The Run-38 report body is left as the historical record with
an erratum appended; `T6_HANDOFF.md` is corrected because that is what later runs read; and the
Run-39 gate now derives the count from the live authority **on both sides of the comparison**, so
the same error cannot recur. This is the seventh occurrence of the count-from-prose class in this
programme.

## 2. Run-38 readiness identity

`STUDY_EXECUTION_READY`, blockers 0, at commit `dd2e355b55008fe08f440c8a9e87378db98ad399`.
Confirmed from `STUDY_EXECUTION_READINESS_MANIFEST.json`, and both Run-38 gates were re-run green
on this tree.

## 3. Run 39 made no scientific modification

No scientific formula, module implementation, Category-9 gate, Category-10 boundary, voting rule,
controlled stimulus, project/period ordering, AI recommendation, participant decision sequence,
participant treatment, research response semantic, analysis variable definition or frozen export
schema was changed.

Proved by `server/tools/test_run39_frozen_immutability.py` (18/18) — see section 15.

## 4. Dataset-class contract

`research/methodology/run39_dataset_classification_contract.md`.

Three governed classes, **closed vocabulary**: `TEST_ONLY` · `PILOT` · `MAIN_STUDY`.
A participant the registry does not name is `UNCLASSIFIED` — the **absence** of a class, not a
fourth class — and can never be exported as anything.

**The authority is a registry, not a name.**
`research/study_execution/dataset_class_registry.csv` maps study identifier → class, with a date,
a registering authority and a note. `run39_dataset_class.classify()` reads that file and nothing
else: not a code prefix, not a label, not a date, not any property of the row.

This is a deliberate departure from Run 38's frozen `record_class` column, which **is**
prefix-derived. That column is frozen and Run 39 does not touch it — but it is not the
classification authority, and the gate proves the two can disagree: `R39-PILOT-A` yields
`record_class = "STUDY"` from the frozen prefix rule and `PILOT` from the governed registry.

**Where the class lives in an artifact.** The frozen CSV's 59 columns are unchanged; the class is
carried in the sidecar `<artifact>.class.json` together with the registry digest that produced
it. An export contains exactly one class and says which. This satisfies the specification's
"retained **or provenance-linkable**" without widening a frozen categorical vocabulary, which the
hard boundary forbids and which section 21 forbids resolving by minting a successor.

## 5. Main-study zero state

`code_audit/run39_main_study_zero_state.csv`.

| property | required | observed |
|---|---|---|
| MAIN_STUDY registrations before launch | 0 | **0** |
| MAIN_STUDY observations persisted before launch | 0 | **0** |
| MAIN_STUDY rows in the analysis export | 0 | **0** |
| pilot observations wrongly counted as MAIN_STUDY | 0 | **0** |

Measured from the database — participants → assignments → decisions for registry MAIN_STUDY
codes — not from the registry alone. Reading only the registry would prove that nobody is
*registered*, which is a weaker claim than that no main-study observation *exists*.

**Nothing was deleted to achieve zero.** Pilot evidence is retained and segregated: 47 PILOT
observations exist and are classified as such. Asking the governed selector for MAIN_STUDY
returns nothing.

## 6. Pilot/main segregation

`code_audit/run39_pilot_main_segregation.csv` — every property PASS.

- A PILOT account cannot create MAIN_STUDY rows: exact-match selection, no promotion path.
- No MAIN_STUDY account can be misclassified PILOT: there are no MAIN_STUDY registrations at all.
- **Changing a display label cannot change dataset class.** The pilot participant was renamed to
  `MAIN-STUDY-P0001` through the database and still classified `UNCLASSIFIED`, not eligible.
- Export filtering uses the governed classification, demonstrated against the frozen
  prefix-derived column giving a different answer for the same participant.
- **Prefix-confusable identifiers do not contaminate**: `R39-PILOT-A` and `R39-PILOT-A-2`
  classify independently, because matching is exact and never prefix-based.
- A class outside the closed vocabulary is refused: a registry naming `SEMI_PILOT` raises rather
  than minting a value.

## 7. Administrative authority boundary

`code_audit/run39_administrative_authority_boundary.csv` — 11 capabilities.

**The launch condition is met:** routine study administration does not require direct database
mutation of participant responses. Proved by a mechanical census of every `a_admin*` action in
`server/app/` — **zero administrative routes write any participant response column**, and the
sole application writer of every response column is the guarded route `research_decision.py`.

**The residual risk, stated without dressing it up as immutability.** `render.yaml` provisions
exactly **one** `DATABASE_URL` and **no** read-only or otherwise restricted role, and `app/db.py`
builds one engine from it. Whoever operates the deployment therefore holds unrestricted write
access to participant responses. The control against using it is the runbook prohibition. That is
an **operational** control, not a technical one, and it is recorded as
`OPERATIONALLY_PROHIBITED ONLY`.

Under the stated blocker list this is not blocking: blocker 18 is "administrative procedure
*requires* substantive answer modification", and it does not.

## 8. Final-lock auditability

Measured by actually tampering with a pilot row through raw SQL and then restoring it.

| field | classification | why |
|---|---|---|
| `pre_action`, `pre_confidence` | **PREVENTED** | database trigger `trg_decisions_pre_lock_guard` refuses the UPDATE |
| `disposition` | **DETECTABLE** | the `final_decision_submitted` audit event records the original value, so a changed row contradicts the audit trail |
| `final_action`, `final_confidence`, `rationale` | **OPERATIONALLY_PROHIBITED** | no trigger, no `updated_at`, no row version, no audit metadata carrying the original, and the tamper writes **no audit row** |

**Stated plainly, because the study needs to know it:** a post-final-lock raw-SQL change to
`final_action`, `final_confidence` or `rationale` is **wholly undetectable from every governed
record**. `decisions` carries no `updated_at` and no version column; the audit event carries only
`disposition` and `sequence_number`; and the audit row count was measured before and after a
tamper and did not move.

No audit trail was invented to paper over this. It is not an application-path bypass, so it is
not a launch blocker; closing it needs a migration on the participant data path, which is
**successor-candidate work**, not a Run-39 repair.

## 9. Pilot browser execution

`code_audit/run39_pilot_browser_execution.csv` — **33/33 checks; 25 steps recorded, 23 PASS,
1 NOT_VERIFIED, 1 RECORDED_NOT_BLOCKING.**

Real Chromium headless shell, real served application, throwaway SQLite, one isolated synthetic
PILOT-equivalent identity governed-classified `PILOT`. Driven in the browser for the first
controlled periods, every control the participant actually touches: start · evidence review ·
preliminary entry · confidence · preliminary lock · AI reveal · final entry · confidence ·
disposition · rationale and evidence interaction · final lock · next-period transition. Then all
**36** project-period route identities were reached and completion confirmed, with exactly 36
persisted observations and none duplicated. Zero JavaScript console errors. Resume and
re-authentication both land exactly where the rows say.

### The Run-38 `NOT_VERIFIED`, re-tested and preserved

An in-place navigation of an already-loaded workspace page was re-tested as section 9 requires.
**It took 180.0 s and did not complete.** The server was probed immediately before and answered
at once, so the cost is client rendering under this container's swiftshader software
rasterisation; this environment has no GPU and the run cannot distinguish "slow only in software
rendering" from "slow everywhere". **The limitation persists and the `NOT_VERIFIED` is preserved,
not converted to PASS by wording.**

Does it block launch? No. The complete governed sequence executed, all 36 identities were
reached, the study completed, no persisted record was affected, and a fresh page resumes
correctly and immediately. The runbook instructs administrators to have participants reopen the
tab rather than reload it.

### A leakage question that had to be measured, not guessed

The first browser run failed a pre-lock leakage check at period 2. Three separate questions were
then measured separately, because they have different answers:

1. **Does the server emit AI content before the period's lock?** No — measured against
   `researchevidenceget`, `researchsequencestate` and `researchreveal` at P1 and P2.
2. **Is any AI content visible to the participant?** No — computed by walking leaf elements and
   checking every ancestor's computed `display`/`visibility`/`opacity`, not by trusting
   `innerText` alone.
3. **Is AI content present but hidden in the DOM?** From period 2, yes. `render()` hides
   `#dc-reveal` with `display:none` rather than emptying it, so the previous period's package
   markup remains.

The residue is **this participant's own prior legitimate reveal**. It is not a future period, not
another project's treatment, and not anything the server sent this period. Recorded as
`RECORDED_NOT_BLOCKING`.

### A frozen design property this surfaced

Verified mechanically from Run 38's own stimulus artifact: **the AI package is attached per
assignment, so all six periods of a project disclose the identical recommendation** — PRJ-AIR's
six periods carry one package identity and one checksum. A participant therefore forms a
genuinely blind preliminary judgment only in period 1; from period 2 they already know that
project's AI recommendation, independently of any DOM residue.

This is a property of the **accepted frozen design**, present since Run 38 and visible in its own
artifact. Run 39 records it and changes nothing. It has analytic implications the analysis plan
should account for, and any change to it would require a successor freeze candidate.

## 10. Pilot export

Produced through the **exact frozen export path**, never called the study dataset.

- schema `og-analysis-2026.08-v1`; **59 columns**, the frozen list in frozen order;
- deterministic bytes under identical source state;
- direct identifiers = **0** (exact column-name census; no live token hash or raw participant
  primary key appears in the bytes);
- free text excluded as governed;
- participant × project × period key unique;
- version provenance complete on every row;
- the artifact declares `artifact_dataset_class: PILOT` and pins the registry digest;
- no non-PILOT observation leaked in;
- the written file reproduces its recorded checksum.

## 11. R pipeline rehearsal

`research/study_execution/run38_ingest_qualification.R` executed against the pilot export:
**RESULT: 35/35 checks passed**, exit 0, no manual cleanup. Base R only.

Checksum · schema version · required columns · types · categorical vocabulary · key uniqueness ·
6×6 population · participant completeness · missingness · impossible transitions · version
provenance — all verified, plus the dependent variables re-derived in R.

**No inferential statistics.** The validator was additionally scanned for `t.test`, `wilcox`,
`lm(`, `aov(`, `confint`, `chisq.test`, `cor.test` and p-value references and contains none. No
hypothesis test, effect estimate, confidence interval or p-value was computed anywhere in this
run.

The rehearsal used the **complete** pilot participant. The deliberately incomplete one is
reported by the completeness classification and was not smuggled into the validator to make it
pass.

## 12. Primary-outcome reconstructability

From pilot records only, all reconstructed: preliminary action · final action · action revision ·
movement toward AI · movement away from AI · preliminary confidence · final confidence ·
confidence change · AI disposition · evidence variables · rationale variables (governed:
presence and length only) · timing variables.

Revision direction and confidence change were **re-derived independently** from the raw columns
rather than trusted from the exporter; 0 mismatches.

**No correctness label exists and none was introduced.** `AI agreement is not accuracy`, and no
governed reference standard in this repository supports one.

## 13. Main-study data freeze procedure

`research/study_execution/MAIN_STUDY_DATA_FREEZE_PROCEDURE.md`, implemented as executable code in
`server/tools/run39_main_study_freeze.py`, so the document describes something that runs.

Executed and verified in this run:

- asked for MAIN_STUDY today it **refuses** with `EmptyDatasetError` — an empty artifact that
  looked like a study dataset would be worse than none;
- rehearsed on the PILOT class: 10 invariants checked **before** the checksum is taken, all zero;
- the artifact re-verifies from disk alone;
- the checksum reproduces from the written file (re-read from disk, not trusted from memory);
- the freeze record carries complete schema/version/package provenance;
- **two independent freezes of identical source state produce identical bytes** apart from the
  single documented timestamp column.

Analysis runs against the frozen artifact only, never against the live operational database.

## 14. Data-exclusion boundary

Exclusion is a **classification**, never an edit. Every analysis row falls into exactly one
category, and the categories sum to the row total.

`TEST_ONLY` · `PILOT` · `MAIN_STUDY complete` · `MAIN_STUDY incomplete` · `technically invalid
record` · `UNCLASSIFIED (fail-closed, excluded)`

**No participant-withdrawal state is defined**, because no governed document in this repository
establishes one, and Run 39 did not invent one. **No substantive observation was deleted**, and
the deliberately incomplete pilot session was left incomplete.

## 15. Frozen-instrument immutability

`server/tools/test_run39_frozen_immutability.py` — **18/18**, run before and after.

Byte-identical to freeze candidate `6142d877`: `server/app/`, `assets/`, `index.html`,
`research_fixtures/synthetic/`, the frozen methodology specification, and the participant sequence
authority. No file named by the governed freeze checksum manifest differs from the Run-38
readiness commit.

**Scientific/client behaviour changes = 0.** Run 39 modified only three pre-existing files, each
named explicitly in the gate: `T6_HANDOFF.md`, the Run-38 report (erratum), and the Run-38
immutability gate's own permitted-modification set. None is executable production or client code,
none is inside a frozen surface, and none is named by the freeze checksum manifest.

**No successor was minted** for launch documentation, pilot provenance, audit artifacts,
validators or pilot data — which is everything this run produced.

## 16. Launch blockers

All twenty blocker classes were fault-injected and every one is detected.
`code_audit/run39_fault_campaign_results.csv`.

**faults = 20 · applied = 20 · intended RED = 20 · restored GREEN = 20 · NOT_APPLIED = 0 ·
crash accepted as RED = 0 (crashes observed 0) · unrelated RED = 0 · undetected = 0.**

The four the owner named specifically:

- **Fault 5** — a PILOT row made eligible for MAIN_STUDY export → gate RED, restored GREEN.
- **Fault 7** — main-study zero state given one prelaunch observation → gate RED.
- **Fault 9** — information needed to reconstruct action revision removed → gate RED.
- **Fault 19** — the deterministic/checksummed freeze procedure broken → gate RED.

Faults 2, 3 and 14 are the only ones that touch a frozen file, each for a single oracle
invocation, restored and re-verified byte for byte. They have to: blockers 2, 3 and 14 are about
frozen and application-path behaviour, and the honest way to prove those are detected is to
change such a byte and watch the gate refuse.

**The campaign was not 20/20 on the first attempt, and the difference was real work.**
It ran five times. Across those runs it exposed **six genuine defects, all in Run 39's own
machinery, none in the frozen instrument**:

1. **The campaign read the wrong RESULT line.** `test_run39_launch_gate.py` prints the R
   validator's canonical `RESULT: N/M checks passed` verbatim, which matches the same pattern the
   gate's own line does. The campaign took the last one it saw — sometimes R's — and so reported
   three faults "undetected" and three "unrelated" when the gate had actually died before
   printing its own summary. The gate now emits `RUN39_GATE_SUMMARY_BEGIN`; the campaign parses
   only what follows it; **a missing sentinel is a CRASH, never a GREEN.**
2. **The helper raised where the gate should have judged.** `build_class_export` raised on schema
   or column-count drift, killing the gate mid-run. A process that dies without a verdict is a
   crash, not a detection. The helper now builds; the gate judges.
3. **`.get(k, 0)` returns `None` when the key exists with value `None`** — the default only
   applies to a *missing* key. A nulled confidence column therefore raised `TypeError` instead of
   failing.
4. **A detail string still indexed the freeze record directly**, so a correctly-refused freeze
   raised `KeyError` while formatting the message for the check that was already failing.
5. **An empty class selection was unguarded**, so a promotion bug produced an `IndexError`
   instead of a named failure.
6. **Fault 14 was ill-posed and is recorded as repointed.** It added `"period"` to the writer
   census tuple, but `period` is set as a *constructor keyword* in `research_decision.py`, never
   as `decision.period = ...`, so the mutation landed in the file and changed nothing — a
   NOT_APPLIED dressed as an APPLIED. It now introduces a real second application writer.

Five of the six are the same defect class this programme keeps finding: **a check that crashes
has not detected anything.** Run 38's gate had it too. None was found by reading; all were found
by injecting the fault.

## 17. Final disposition

`MAIN_STUDY_LAUNCH_READY` — blockers = 0.

**What this authorises and what it does not.** It authorises beginning primary data collection on
this frozen instrument, following `MAIN_STUDY_LAUNCH_CHECKLIST.md`. It does **not** constitute
ethical approval: no governed document in this repository establishes an IRB approval, a protocol
number or an approved consent text, and none is asserted anywhere in this run's output.

**Run 39 did not begin collection of the primary study dataset**, and the main-study dataset
remains at zero rows.

**Not claimed.** Pilot and test observations are not study findings. Nothing here is empirical
validation; empirical field validation remains **0/100**. No hypothesis test, effect estimate,
confidence interval or p-value was computed.

---

## Artifacts

| path | contents |
|---|---|
| `code_audit/run39_launch_identity.csv` | 15 identity rows |
| `code_audit/run39_main_study_zero_state.csv` | zero-state proof |
| `code_audit/run39_pilot_main_segregation.csv` | segregation properties |
| `code_audit/run39_administrative_authority_boundary.csv` | 11 capabilities, classified |
| `code_audit/run39_pilot_browser_execution.csv` | 25 browser steps |
| `code_audit/run39_fault_campaign_results.csv` | 20 faults |
| `research/methodology/run39_dataset_classification_contract.md` | the class contract |
| `research/study_execution/dataset_class_registry.csv` | the governed registry |
| `research/study_execution/PILOT_EXECUTION_PROTOCOL.md` | pilot protocol |
| `research/study_execution/MAIN_STUDY_DATA_FREEZE_PROCEDURE.md` | freeze procedure |
| `research/study_execution/MAIN_STUDY_LAUNCH_CHECKLIST.md` | launch checklist |
| `research/study_execution/STUDY_INCIDENT_LOG_TEMPLATE.csv` | incident log template |
| `research/study_execution/MAIN_STUDY_LAUNCH_MANIFEST.json` | the machine-readable record |
| `server/tools/test_run39_launch_gate.py` | the launch gate (99 checks) |
| `server/tools/test_run39_frozen_immutability.py` | the section-20 gate (18 checks) |
| `server/tools/run39_dataset_class.py` | the classification layer |
| `server/tools/run39_launch_gate.py` | pilot export machinery |
| `server/tools/run39_main_study_freeze.py` | the executable freeze procedure |
| `server/tools/run39_fault_campaign.py` | the 20-fault campaign |
| `server/tools/drive_run39_pilot_browser.py` | the browser driver |
| `server/tools/run39_build_launch_manifest.py` | the manifest builder |
