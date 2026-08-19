# Opus Gubernatio — Instrument Freeze Candidate

**Label: `FREEZE_CANDIDATE`.** This is not a final immutable release. No existing owner authority
defines that transition, so none is claimed here.

Machine-readable companion: `research/freeze/INSTRUMENT_FREEZE_CANDIDATE_MANIFEST.json`.

---

## What was blocking, and what closed it

Run 36 ended `FREEZE_BLOCKED` on one defect: **A1.1 Monte Carlo EAC Forecast declared the governed
structure `costDriverDistributions`, canonical theory required it, the intake accepted it, and no
route read it.** Run 36 refused to close it by invention, because the supervisory specification
requires a *deterministic mapping from sampled cost drivers to EAC* and does not define one.

**The owner ruled on 2026-08-19.** The `Required:` input list in specification §1.1 governs what
qualifies as canonical Monte Carlo. The permission to "retain" the scalar BAC/CPI/SPI/document-risk
adaptation preserves it as scientific and historical code; it does **not** waive the input contract
and does **not** authorize the adaptation to stand in for canonical execution.

So A1.1 is now **operationally disabled for insufficient canonical input**, reason code
`CANONICAL_DRIVER_DISTRIBUTION_MAPPING_NOT_GOVERNED`. **No mapping was invented.** This is a
scientific-input limitation, not a software failure, and the participant-facing sentence says so in
words.

The retained adaptation is **preserved and unreachable**: `registry.run_module` short-circuits A1.1
before the dispatch table is consulted, and `models_sim.assert_retained_adaptation_not_reachable`
proves it from the live source of the gate and then executes A1.1 on inputs the adaptation would
happily have computed from.

---

## The exact final state

| | |
|---|---|
| Simulation | `sim-2026.08-v25` (v24 preserved and pinned at `822d8092`) |
| Participant package | `og-participant-2026.08-v13` (v12 pinned at `822d8092`) |
| Synthetic package | `OG-SYNTH-0.6`, retained unchanged |
| Registered modules | **101** |
| Scientific targets | **100** |
| Voting | **exactly 2** — A1.7 TCPI, A1.8 VAC |
| Blocking defects | **0** |

**Final scientific qualification:** `QUALIFIED_WITH_ABSTENTION` 87 · `DISABLED` 8 ·
`QUALIFIED_FOR_BOUNDED_STUDY_USE` 3 · `RESEARCH_ONLY` 1 · `ARCHIVED` 1.

**Operational dispositions:** `KEEP_ABSTENTION_CAPABLE` 87 · `DISABLED_INSUFFICIENT_INPUT` 6 ·
`KEEP_OPERATIONAL` 2 · `DISABLED_INSUFFICIENT_PROVENANCE` 2 · `KEEP_ADVISORY` 1 ·
`RESEARCH_ONLY` 1 · `ARCHIVED` 1.

**Controlled study population, enumerated from the actual stimuli and not written down first:**
6 projects (PRJ-AIR, PRJ-DCT, PRJ-HSP, PRJ-HWY, PRJ-RAL, PRJ-WTR) × 6 periods (P01–P06) =
**36 unique project-periods**, duplicates 0, missing 0.

**Category-9 bypasses 0. Category-10 authority violations 0. Disabled/archive production leakage 0.**

**Browser:** 28/28 on the real authenticated participant route. **Faults:** 40/40 and 15/15, every
one applied, RED for its intended reason and restored GREEN; crashes accepted as RED 0.

---

## What this candidate does NOT claim

- **Nothing is empirically field-validated. 0 of 100.** No labelled outcome corpus and no expert
  reference standard exist in this repository, and no band anywhere has a measured false-positive
  or false-negative rate.
- **Nothing is calibrated.** No calibration set exists.
- **95 of 100 targets produce nothing on the controlled corpus.** The intake works; the corpus
  carries no governed structures.
- **Lineage is unresolved for 77 of 100.** Unknown lineage was never treated as independent.
- **Parsimony: 0 targets ESTABLISHED as adding no distinct analytical function** — which is not a
  claim that the instrument is free of redundancy. Only five targets leave the abstention branch,
  so execution can establish redundancy for none. Run 35's 22 and Run 36's 17 were both measuring
  structural overlap, which is recorded separately and is not zero.
- **A1.1's canonical driver-to-EAC mapping remains undefined by any authority.** The module is
  disabled rather than approximated.
- **OG-SYNTH-0.1 is historically incomplete**: 519 manifest entries against 504 recovered, 15
  unrecoverable rows over 5 unique paths. No completeness is claimed for it.
- **The design contract binds the stimulus corpus and the participant sequence**, not the number of
  assignments in any participant database, which is operator configuration.

Qualification here is for **bounded controlled-study use**, not universal field validity.
