# Run-42 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v27`.

## Why there is a successor at all

Run 41 accepted a successor freeze of the v26 instrument. Run 42 was then instructed to fix the
background data-processing and calculation mechanism, on the rule that the reporting period a
person SELECTS at upload is authoritative and that nothing else -- upload order, document date,
filename, database insertion order, extraction completion order -- may decide it.

The mechanism was traced end to end and **most of it was already correct**. The selected period
binds correctly; extraction cannot reach the period because the period is bound before extraction
runs; there is no cross-period or cross-project retrieval; and the longitudinal series are ordered
by reporting-period identity, never by upload or computation time. Uploading four periods out of
order produces a byte-identical analytical state.

Two defects were proved, and both were losses in the PATH rather than absences in the data:

1. **The per-field source record dropped the document identity.** Every observation has always
   carried `document_id`, `sha256`, `revision_of` and `as_of`, and the stored result has always
   listed the same identity per document. The per-field record kept only the document TYPE. The
   qualification layer counts a field as traced only when it carries both an identity and a
   version, so it counted **zero on every project ever computed**, and the provenance and
   timeliness dimensions were structurally pinned to PARTIAL.

2. **The qualification record named a null project.** The compute path read the identity from a
   signal-inputs key that does not exist, and the read path hard-coded `None`, while both callers
   held the project the whole time.

Repairing either moves bytes inside a frozen surface, so v26 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 successor -> Run 42 mechanism repair -> v27 successor

## What did NOT change, proved by execution

| Subject | Result |
|---|---|
| Registered module population | 101, identical |
| Module emitted rows across the boundary | **0 of 101 moved** |
| Signal inputs other than the source record | byte-identical |
| `revision_resolution_status` | NOT_ESTIMABLE, unchanged |
| `overall_qualification_state` | NOT_ESTIMABLE, unchanged |
| Participant package | RETAINED `og-participant-2026.08-v13`, 70 of 70 bytes identical |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

This is not inferred from a source diff. Both lines were extracted from their own pinned git
objects and executed on identical inputs: `code_audit/run42_v26_v27_execution_proof.csv`.

## The scientific position

No input was invented, no fact fabricated, no qualification rule relaxed and no scientific method
changed. The instrument still abstains wherever the governed structure is absent, and that is the
correct answer rather than a failure. The revision dimension remains NOT_ESTIMABLE by deliberate
decision, so the overall qualification state remains NOT_ESTIMABLE; that is reported to the owner
as a decision to take, not quietly relaxed to make categories light up.

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run42_successor_freeze_gate.csv`.

The v25 and v26 release records are preserved unchanged and still record their own stamps.
