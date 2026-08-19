# Opus Gubernatio — Instrument Final Freeze Report

**Disposition: `FINAL_FREEZE_ACCEPTED`.** Blocking defects: **0** across fifteen independently
evaluated blocker classes.

Machine-readable record: `research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json`.
Checksum manifest: `research/freeze/INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv` (43 files, 0 untracked).

---

## What this run did, and did not do

Run 37 **did not improve the instrument.** No formula, threshold, calibration, qualification rule,
voting entry, controlled stimulus or participant-sequence byte was changed. It executed the Run-36
candidate and recorded what it found. Had any of those needed to change, the answer would have been
`FINAL_FREEZE_BLOCKED` and a successor candidate — that is what the gate reports, and fault 15 of
the campaign proves it can.

Two defects were found and both were **in this run's own instruments, not in the candidate**:

1. The first defensibility oracle assumed "structure not supplied by an owner" meant "structure
   absent", and raised a false positive against A6.2. A6.2's `safetyPerformanceRecord` is
   **assembled** by the platform from the project's own extracted Safety Report evidence — the same
   governed pattern used for the milestone history and the cost risk model. The structure is
   required and present; it arrives by assembly rather than upload. The oracle now asks the
   assembly path itself.
2. The freeze gate suite was **vacuous**: all fifteen faults stayed green because its per-blocker
   checks read the committed artefact rather than the freshly regenerated one. And the campaign's
   own baseline check asked for a name that never appears, so any failing baseline read as green.
   Both are fixed, and the campaign then went red fifteen times for fifteen reasons.

---

## The frozen instrument

| | |
|---|---|
| Freeze-candidate commit | `6142d877856ea651ef8d7e905f6d27604b3244f1` |
| Candidate identity digest | `60236d1cac6e2ca900d8f64e67202f558788989978b86c29c4cda3580d8c42e4` |
| Candidate behaviour digest | recorded in the release record |
| Simulation | `sim-2026.08-v25` — unchanged, not bumped for release records |
| Participant package | `og-participant-2026.08-v13` — unchanged |
| Synthetic package | `OG-SYNTH-0.6` — unchanged |

**Controlled study**, enumerated from the corpus that exists: **6 projects × 6 periods = 36** unique
project-periods, duplicates 0, missing 0. PRJ-AIR, PRJ-DCT, PRJ-HSP, PRJ-HWY, PRJ-RAL, PRJ-WTR over
P01–P06. No stimulus was created or modified.

**Scientific population:** 101 registered · 95 project scientific · 5 Portfolio Health ·
**100 scientific targets** · voting **exactly 2** (A1.7 TCPI, A1.8 VAC).

**Execution census**, all 100 through their real governed routes: 89 abstain · 5 compute ·
5 portfolio-route refusals · 1 supplied-not-computed · **3 populated analytical results**
(A1.7, A1.8, A6.2) · **0 unexpected exceptions** · 0 legacy-route reachability.

**Final qualification:** `QUALIFIED_WITH_ABSTENTION` 87 · `DISABLED` 8 ·
`QUALIFIED_FOR_BOUNDED_STUDY_USE` 3 · `RESEARCH_ONLY` 1 · `ARCHIVED` 1.

**Parsimony**, independently reproduced under the Run-36 rule set: established redundancy **0** ·
structural overlap 19 · shared inputs 5 · subset/superset 1 · targets producing a reading 5. All
five reproduced, none carried forward on trust.

> **0 established redundancy does not mean 0 possible redundancy.** Most scientific targets abstain
> on the controlled corpus, and absence of execution evidence can establish neither redundancy nor
> independence nor uniqueness. The four categories are different things and are not collapsed.

**Gates:** Category-9 bypasses 0 · Category-10 authority violations 0 · one taxonomy authority with
both client mirrors traceable to it · all 101 registered modules resolve through runtime lookup with
no crash and no stale-method population.

**Browser:** 28/28, executed fresh. **Fault campaign:** 15/15 applied, RED for intent, restored
GREEN; crashes accepted as RED 0.

---

## The limitation contract

These are stated plainly because they are the defensible part of the instrument, not footnotes.

- **Empirical field validation is 0 of 100.** No scientific target has been validated against an
  independent observed real-world outcome.
- **Portfolio Health empirical validation is PENDING for all five** (PH.1–PH.5).
- **Nothing is calibrated.** No calibration set exists here: no labelled outcome corpus and no
  expert reference standard. **No band anywhere has a measured false-positive or false-negative
  rate.**
- **Lineage is unresolved for 77 of 100 targets.** Unknown lineage was never treated as independent.
- **Most scientific targets abstain on the controlled corpus** — 3 of 100 produce a populated
  analytical result. That is the instrument being honest about absent evidence, not a fault.
- **OG-SYNTH-0.1 is historically incomplete**: 519 manifest entries against 504 recovered, 15
  unrecoverable rows over 5 unique paths. It is not repaired and no completeness is claimed.
- **A1.1 Monte Carlo EAC Forecast is disabled for insufficient canonical input.** Its
  driver-to-EAC mapping is defined by no authority and none was invented.
- **This freeze qualifies the instrument for bounded controlled-study use only.**

> ### FINAL FREEZE IS NOT A CLAIM OF VALIDATED REAL-WORLD PREDICTIVE EFFECTIVENESS.
> It is not field validation. It is not calibration. It is not evidence that any band, threshold or
> forecast in this instrument is accurate about real projects. It states that the instrument does
> what it says it does, abstains where it should, and is reproducible.

---

## How the release is identified

A file cannot contain the hash of the commit that contains it. This record therefore distinguishes:

- **`freeze_candidate_commit`** — `6142d877856ea651ef8d7e905f6d27604b3244f1`, the reviewed candidate;
- **`release_content_digest`** — content-addressed over the checksum manifest, reproducible from the
  tree alone;
- **`release_commit_recording_method`** — the commit containing this record is **established
  externally by repository history**. The repository has no release-tagging convention (its single
  tag, `pre-consolidation-v1`, is a UI-history marker), so **no tag is created**.

No `PENDING_FINAL_COMMIT` placeholder is used anywhere in this release.
