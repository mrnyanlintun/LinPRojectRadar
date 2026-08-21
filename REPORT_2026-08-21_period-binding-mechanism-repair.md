# Run 42: the period-binding and evidence-lineage mechanism

**Instruction.** Fix the background data-processing and calculation mechanism. The reporting
period a person SELECTS at upload is authoritative; upload order, document date, filename,
database insertion order and extraction completion order must never determine the analytical
period. Trace and repair the whole path: upload, selected period persistence, extraction, stored
facts, module input retrieval, C1/Data Integrity qualification, category calculation, project
status, brief and decision, longitudinal analysis, lineage.

**Outcome.** Two defects proved and fixed, both losses in the PATH rather than absences in the
data. Most of the mechanism was already correct, and that is reported as a finding rather than
padded into a defect list. Executable behaviour changed, so `sim-2026.08-v26` is superseded by
**`sim-2026.08-v27`**, proved by executing both pinned lines. Final suite: **188 suites,
14176/14176 checks, all green.**

---

## 1. What was already correct

Proved, not assumed. Each row was executed through the real `POST /exec` routes.

| Property | Result | Evidence |
|---|---|---|
| The selected period is the period the upload writes to | INTACT | suite section 1; fault F6 |
| Upload order does not reach the period | INTACT | `run42_outoforder_equivalence.json` |
| Document date and filename do not reach the period | INTACT | period is bound before extraction |
| Extraction completion order cannot reach the period | INTACT | the period is bound before extraction runs |
| No cross-period retrieval | INTACT | suite section 3, zero leaks |
| No cross-project retrieval | INTACT | suite section 3, zero leaks |
| Longitudinal ordering is by reporting-period identity | INTACT | `_earlier_live_results` orders by period with `period < period` |

**Out-of-order equivalence.** The same project id was uploaded into two separate freshly migrated
databases, differing in nothing but the order the four reporting periods were sent: `P1,P2,P3,P4`
against `P4,P1,P3,P2`. The complete derived analytical state is **byte-identical** after
normalising only row ULIDs and wall-clock stamps. Artifact:
`code_audit/run42_outoforder_equivalence.json`.

---

## 2. The defects

### D1 — the per-field source record dropped the document identity (FIXED)

**Baseline.** `code_audit/run42_baseline_state_chrono.json`: for a computed period,
`signal_inputs.sources.ev` was `{"docType": "monthly_report", "value": 6000000}` — while
`source_documents` for the same period carried `document_id` and `sha256`, and the qualification
record reported `fields_with_document_identity_and_version: 0` of `fields_with_source_type: 7`.

**Cause.** `extraction_merge.emit_observations` has always put `document_id`, `sha256`,
`revision_of` and `as_of` on **every** observation. The four sites that build a per-field
`sources` entry wrote `{docType, value}` and discarded all of it. `qualification._provenance`
counts a field as traced only when it carries BOTH a document identity and a document version, so
it counted **zero on every project ever computed**; `_timeliness` counts `asOf` and was pinned the
same way. Because `_overall` is the weakest of the dimensions, the two of them alone held the
record down. The evidence was in storage the whole time; one hop lost it.

**Fix.** `server/app/extraction_merge.py`: new `_source_entry(w)` carries `documentId`,
`documentVersion` (the content-addressed sha256 — storage is content-addressed, so the hash *is*
the version identity), `asOf` and `revisionOf`. Keys are omitted rather than written as null when
the observation does not carry them, so a document with no identity still produces an honest
record. `server/app/simulation/qualification.py`: the PARTIAL reason sentences are absolute
claims and would have been emitted beside a PASS, putting a false statement into the one object
downstream readers are entitled to trust; PASS reasons are added and selected on the PASS branch.

**Result.** 7 of 7 sourced fields now name the artefact they came from, every named artefact is
one of that period's own documents, provenance and timeliness reach PASS.

### D2 — the qualification record named a null project (FIXED)

**Baseline.** `evidence_qualification.project_id` was `null` for every period, while
`reporting_period` was correctly `"P3"`. Period identity survived the path; project identity did
not.

**Cause.** `compute.py` read `si.get("projectId") or si.get("id")`. The signal-inputs dict is
`extraction_merge._KEY_ORDER` — the reported figures — and has neither key, so the expression was
always `None`. The read path in `documents._result_view` hard-coded `project_id=None`. Both
callers held the project the whole time.

**Fix.** `compute_project` takes an explicit `project_id` and uses it as the fallback;
`documents.py` passes `project.legacy_id` on the compute path and threads `project_legacy_id`
into `_result_view` for the read path.

**An honest note on reachability.** The compute path's `evidence_qualification` is attached to
the run and **not persisted** — `_result_view` re-derives the record at read time. So the
compute-path half of D2 has no route-observable effect today; it is a correctness repair at the
function boundary and is tested there directly. This was discovered by fault injection: reverting
it left every route-level assertion green, which is exactly the "check that never reached the
boundary" failure this programme keeps finding. Section 7 of the regression suite exists because
of it.

### D3 — ten declared extraction fields are consumed by nothing (NEEDS_OWNER_DECISION)

Derived mechanically: `actual_equipment_days`, `analogous_project_type`, `constraint_rate`,
`environmental_observations`, `items_passed`, `on_schedule`, `planned_equipment_days`,
`rfi_answered`, `safety_observations`, `subcontractor_observations` — 10 of 118 declared
extraction fields appear nowhere in `server/app` outside their own declaration. The extractor is
asked for them and their values are stored, but nothing reads them.

**Not fixed, deliberately.** There is no "intended module input" they fail to reach — there is no
declared destination at all. Mapping them would be *designing new analytical inputs*, which is a
scientific change, not a mechanism repair. Artifact:
`code_audit/run42_unconsumed_extraction_fields.csv`.

### D4 — A4.1 neither computes nor abstains (CORRECT ABSTENTION)

`run_module("A4.1")` raises `MissingModuleError`: the module has not been ported and validated
against the JavaScript implementation and the server deliberately refuses it. A deliberate
fail-closed refusal, not a loss in the period-binding path.

### D5 — D1.1–D1.5 absent from a single-project compute (NOT APPLICABLE)

Portfolio Health is portfolio scope; the registry refuses group D on a single-project path. The
portfolio snapshot is computed separately and is present on the stored result.

---

## 3. C1 / Data Integrity: the finding, and what was NOT done

C1/Category-9 qualification was **not** blocking downstream categories. `compute.py` attaches it
after the status is fused, and it is metadata by construction: it adds no module, casts no vote,
moves no band and cannot change `project_status`. The real defect in this area was D1 — the
qualification layer was being fed a record stripped of the identity it is built to read.

`overall_qualification_state` **remains NOT_ESTIMABLE**, and that is correct rather than a
remaining bug. `_overall` is the weakest of six dimensions, and `revision_resolution_status` is
hard-coded NOT_ESTIMABLE. That is a deliberate, tested scientific decision:
`test_run12_category9_qualification.py` asserts across five distinct evidence cases that revision
resolution *is never anything but* NOT_ESTIMABLE in this repository. **Run 42 did not touch it.**
Relaxing it to let the overall state improve would undo a deliberate fail-closed choice rather
than repair a mechanism. It is raised here as an owner decision.

After the repair, revision lineage *is* now joined to the field (`revisionOf` is carried, and
superseded documents are already excluded from the period's live set by explicit `supersedes`
claims rather than by upload order). Whether that is sufficient to let the revision dimension
report anything other than NOT_ESTIMABLE is a scientific judgement, and it is the owner's.

---

## 4. Which categories compute, and why the rest do not

Derived mechanically from a live run: `code_audit/run42_category_disposition.csv`.

Of 101 registered modules on a single-project period carrying one monthly report: **3 compute, 92
abstain, 6 are not reached** (A4.1 refused as unported; D1.1–D1.5 portfolio scope). One category,
**A1 (Earned Value)**, carries a status.

**This is the instrument working correctly, not a failure.** The fixture supplies a monthly
report and nothing else, so the governed structures of the other categories are genuinely absent
from the corpus and the modules that read them abstain for exactly that reason. The abstention
reasons are recorded per category in the disposition artifact. Run 42 changed **no** module's
output: the execution proof shows all 101 emitted rows byte-identical across the v26→v27
boundary. Nothing was made to light up, and nothing that was lit went dark.

**Do any source documents need modification?** **No.** No evidence in this run points at a
document defect. Both proved defects were in the code path between storage and the module, and
both were repaired without touching a byte of any document. Categories that abstain do so because
their governed structure is not present in the corpus at all — the answer there is more kinds of
evidence, not corrected documents.

---

## 5. Lineage

Every sourced field now names the artefact that produced it: `documentId`, `documentVersion`,
`asOf`, and `revisionOf` where a supersession was declared. The regression suite asserts, for all
four periods, that every sourced field carries an identity **and** that the identity it names is
one of *that period's own* documents — so lineage that pointed at the wrong period would fail.

---

## 6. Version boundary and requalification

Executable behaviour changed, so the freeze is **superseded, not amended**: `sim-2026.08-v27`,
appended to `SIMULATION_VERSION_HISTORY`, superseding `sim-2026.08-v26`.

**The boundary was proved by EXECUTING both pinned lines**, not by reading a diff. The v26 line
was extracted from its own git object (`1b624d3e`) and imported as its own package.
`code_audit/run42_v26_v27_execution_proof.csv`:

| Subject | Expected | Observed |
|---|---|---|
| Registered population | identical | 101 = 101 |
| Module emitted rows | 0 move | **0 of 101 moved** |
| Signal inputs other than `sources` | identical | identical |
| `sources` record | diverges | diverges; gained `documentId`, `documentVersion`, `asOf`; lost nothing |
| `provenance_status` | improves | PARTIAL → PASS |
| `timeliness_status` | improves | PARTIAL → PASS |
| `revision_resolution_status` | unchanged | NOT_ESTIMABLE → NOT_ESTIMABLE |
| `overall_qualification_state` | unchanged | NOT_ESTIMABLE → NOT_ESTIMABLE |
| Traced fields | 0 → all | 0 → 7 of 7 |

Both the genuine divergences and the genuine non-divergences are recorded.

**Participant package: RETAINED, determined mechanically.** Not one of the 70 governed
participant-package bytes moved; the 6 sequence-bearing files are byte-identical to the v13
record; and none of the five production files Run 42 changed is named by that record. No
participant successor was minted. `OG-SYNTH-0.6` and `og-analysis-2026.08-v1` unchanged.

**Production blast radius, measured:** exactly five files changed, none added, none removed —
`extraction_merge.py`, `simulation/qualification.py`, `simulation/compute.py`, `documents.py`,
`simulation/models.py`. Pinned in `code_audit/run42_production_tree.sha256`.

**Gates re-executed, not copied.** Every one was run:

| Gate | Result |
|---|---|
| Run-37-equivalent freeze gate | 15 blocker classes, **0 blocked**; suite 30/30 |
| Run-38 study-execution readiness (frozen immutability) | 17/17 |
| Run-39 main-study launch readiness | 100/100; frozen immutability 19/19 |
| Run-40/41 functional-security acceptance | green in the full suite; findings S1/S2 remain closed |
| Run-41 preservation | 33/33, including a new check that v26 still reconstructs from its own git object as v26 |

The v25 and v26 release records are preserved unchanged and still record their own stamps. Where
a guard had to move, it moved by **naming** what changed, never by widening a comparison.

---

## 7. The regression suite, and proof that it bites

`server/tools/test_run42_period_binding_mechanism.py`, **131 checks**, wired into
`run_all_suites.sh` by its `tools/test_*.py` glob. It drives the real routes and pins the
deliberate abstentions as well as the computations, so a later run that makes a category compute
by relaxing a gate breaks it.

Fault campaign (`code_audit/run42_fault_campaign.csv`) — 6 faults, every one applied to the real
tree and then restored:

| Fault | Result |
|---|---|
| F1 drop the document identity again | CAUGHT (107/131) |
| F2 null the compute-path project identity | CAUGHT (130/131) — **only** by the direct compute-path section |
| F3 null the read-path project identity | CAUGHT (123/131) |
| F4 drop the as-of date | CAUGHT (123/131) |
| F5 inert no-op edit (control) | correctly GREEN (131/131) |
| F6 derive the period from upload order | CAUGHT (2/11) — reports "requested 4, got 1" |

The F5 control matters: a suite that fails on an inert edit is failing for reasons of its own.

**One harness error, found and fixed rather than shipped.** A first attempt to derive
"extracted-but-unreachable" fields compared extraction field names against signal-input field
names and reported `earned_value` as unconsumed — a field we already knew reaches `si["ev"]`. It
was replaced with a differential test (remove one declared field, re-emit, compare) cross-checked
against a whole-tree reference search. The false result is recorded here rather than quietly
dropped.

---

## 8. Classification summary

| Id | Classification | Subject |
|---|---|---|
| D1 | MECHANISM_DEFECT_FIXED | per-field source record dropped the document identity |
| D2 | MECHANISM_DEFECT_FIXED | qualification record named a null project |
| D3 | NEEDS_OWNER_DECISION | 10 declared extraction fields consumed by nothing |
| D4 | CORRECT_ABSTENTION | A4.1 refused as unported |
| D5 | NOT_APPLICABLE_DESIGN_PROJECT | D1.1–D1.5 are portfolio scope |
| — | NEEDS_OWNER_DECISION | `revision_resolution_status` pins `overall_qualification_state` to NOT_ESTIMABLE for every project, permanently |

## 9. Observations for the professionalization run

Recorded, not acted on:

- `_period_history`'s docstring still describes the P1 portfolio defect as "queued separately";
  it was fixed (`documents.py`, "Portfolio snapshot — CUTOFF-ALIGNED (P1)") and the prose is stale.
- `qualification.py` carries a `PROVENANCE_PARTIAL_REASON` phrased as an absolute claim; it is now
  correct only on the PARTIAL branch, which is why the PASS branch needed its own sentence.
- `code_audit/run39_administrative_authority_boundary.csv` was stale in the repository: it recorded
  `ALLOWED` for post-final-lock writes that Run 41's migration 0026 now refuses. Regenerated here.
