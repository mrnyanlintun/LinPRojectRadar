# Run 31 — Categories 8 and 9: governance, regulatory evidence, information quality, and the Category-9 qualification gate

**Date:** 2026-08-17  **Model:** Opus  **Simulation line:** `sim-2026.08-v19`

## 1. Starting point and honest run history

Run 31 began at `main = 53f30815b1872ffa5fc1d61333dd3cb6f9c4e85f` (`sim-2026.08-v16`, participant package `og-participant-2026.08-v5`), tree clean.

**This run stopped twice and reported itself incomplete before it finished.** That is part of its record, not a footnote:

| Commit | What it did |
|---|---|
| `c0e0f56` | Canonical Category-8/9 layer, ABM, regulatory rule objects, `QualifiedEvidence`. **Stopped**: repointing 16 runners broke 33 historical suites. Full suite RED. Reported incomplete rather than pushed. |
| `5f25754` | Section-1 historical-suite reconciliation, 32/32 classified, ambiguous 0. **Stopped again**: classification is not reconciliation. |
| `4df3d12` | Pass 1 — 32/32 suites reconciled, three defects closed, branch suite green. |
| `4dd5985` | Pass-1 closure — four rows carried a non-permitted classification; re-verified per row and corrected. |
| `f147278` | Pass 2 — operational qualification gate (v18), approved names, participant v6. |
| `1094ec6` | Pass-2 closure — **a vacuity in my own guard**, two crashes scored as RED, and two missing artifacts, all corrected. |
| `8098b1f` | Synthetic-manifest closure — **my own `NOT_VENDORED = 177` was wrong**, inferred from absence; corrected to 5 undelivered files. |

Neither stop was recoverable by argument; each was recoverable only by doing the work.

## 2. Version progression, each boundary proved by executing git objects

| Line | Reason for the boundary |
|---|---|
| `v16` | Run-30 predecessor. No Run-31 canonical Category-8/9 architecture. |
| `v17` | Canonical Category-8/9 implementation and Category-8 self-gating. |
| `v18` | System-wide operational qualification boundary installed into the dispatch table. |
| `v19` | **Absence fails closed** — a package with no Category-9 assessment is UNASSESSED and ineligible for every Category-6/7/8/10 consumer. |

`test_run31_version_boundaries.py` (50 checks) extracts the v16, v17 and v18 packages from their pinned git objects, imports them and executes them beside the live line on identical input. No boundary is argued from a source diff.

**Pass 3 changed no production file** (`git diff --stat 8098b1f -- server/app/` is empty), so `v19` stands; §13's decision is taken from executed behaviour, not from which files were edited.

## 3. Scope — 16/16, derived mechanically

Category 8 = A6.1–A6.4 + B3.1–B3.5 (9). Category 9 = C1.1–C1.7 (7). Derived from `p0-baseline/module_renumbering_map.csv`, the file the registry itself reads.

## 4. Category-8 modules

| Module | Authoritative name | Canonical structure | Production route | Qualification | Real-corpus result | Remaining |
|---|---|---|---|---|---|---|
| A6.1 | Quality Compliance Index | YES | canonical | integrated | COMPUTES | Run 33 calibration + empirical validation |
| A6.2 | Safety Performance Index | YES | canonical | integrated | COMPUTES | Run 33 calibration + empirical validation |
| A6.3 | Environmental Compliance Rate | YES | canonical | integrated | COMPUTES | Run 33 calibration + empirical validation |
| A6.4 | Contractor Performance Assessment Signal | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| B3.1 | Agent-Based Governance Model | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| B3.2 | FAR/Agency EVMS Applicability Monitor | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| B3.3 | Versioned A-11 Capital Programming Conformance Check | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| B3.4 | EVMS Reporting Compliance Monitor | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| B3.5 | Contract Modification Governance Check | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
## 5. Category-9 modules

| Module | Authoritative name | Canonical structure | Production route | Qualification | Real-corpus result | Remaining |
|---|---|---|---|---|---|---|
| C1.1 | Missing Data Index | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| C1.2 | Data Timeliness Score | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| C1.3 | Source Reliability Weighting | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| C1.4 | Audit Trail Completeness | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| C1.5 | Information Completeness Ratio | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| C1.6 | Cross-document Consistency Score | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
| C1.7 | Reporting Frequency Index | YES | canonical | integrated | ABSTAINS | Run 33 calibration + empirical validation |
Three of sixteen compute on the real corpus (A6.1, A6.2, A6.3); thirteen correctly abstain for want of governed evidence. **Abstention is the correct answer, not a gap** — no module was forced to compute.

## 6. The qualification gate

`PROJECT EVIDENCE → CATEGORY-9 ASSESSMENT → QUALIFIED EVIDENCE → CATEGORY 6/7/8/10 USE`.

The requirement is **declared** in `qualification_contract.py` per registered route, derived from the shipped registry CSV and each route's registered category role; `qualification_boundary.py` is installed into the dispatch table by `models.py`, last, and is only its reader. 40 routes REQUIRED, 54 NOT_REQUIRED, 7 NOT_APPLICABLE (Category 9 performs the assessment and is excluded by construction). **The default branch is deny**: an undeclared route returns `CONFIGURATION_MISSING` and is blocked.

| Counter | Cat 6 | Cat 7 | Cat 8 | Cat 10 |
|---|---|---|---|---|
| raw bypass | 0 | 0 | 0 | 0 |
| missing-assessment bypass | 0 | 0 | 0 | 0 |

Measured through `registry.run_module`, the real production entry point, with the route population derived independently of the function under test.

## 7. Agent-Based Governance Model (8.1)

Through the production dispatcher: t=0 SIGNAL_RECEIVED → AUTHORITY_RECOGNISED → RESPONSE_REQUEST_SENT; t=2 RESPONSE_AVAILABLE → AUTHORIZATION_NOT_PERMITTED → ESCALATED_TO_OWNER; t=3 AUTHORIZED. Terminal `AUTHORIZED_BY_OWNER`, 3 agents, 7 transitions. Contractor latency 2→4 shifts terminal authorization to t=5 with identical authority semantics. Insufficient evidence, incomplete procedural review, unavailable owner and unqualified evidence each fail to authorize.

8.1 is **Agent-Based Governance Model**, not "Action Boundary & Authority Matrix" — the matrix is the governed policy the model consults. No Bayesian terminology; no random draw in the model.

## 8. Orphan fields — Quality, Safety, Environmental

13 extracted fields across the three families, all classified, **0 defining fields unwired**.

- **Safety** — the OSHA identity `cases × 200000 / hours` was verified **by executing** `extraction_merge.emit_observations`, not by reading it. Two findings followed: the numerator was being discarded, and a document-**stated** rate is emitted unchecked (99.9 survived beside a 3-cases/200,000-hours pair). `oshaRecordableIncidents` is now emitted and the canonical module recomputes the identity itself; the stated rate is carried as a labelled claim with `document_stated_rate_agrees`.
- **Quality** — the meeting-minute prerequisite is gone; a real Quality Audit Report is no longer refused because nobody discussed deficiencies. An audit score and findings counts are summaries, so the rate is `NOT_ESTIMABLE` and the evidence is preserved. No fabricated denominator.
- **Environmental** — no jurisdiction, permitting authority or permit identity exists in the corpus, so applicability cannot be established: `APPLICABILITY_NOT_ESTABLISHED`, evidence preserved, EPA CGP not cited. EPA is never assumed universal.

## 9. Regulatory snapshot and wording

`REGULATORY_SNAPSHOT_2026-08-16`, frozen: FAC 2026-01 (eff. 2026-03-13), FAR 34.201, 52.234-4, 43.102/43.103/43.301, Subpart 46.2, Subpart 42.15, OMB A-11 (2025-08-29), OSHA incidence and leading/lagging basis, EPA 2022 CGP as modified with jurisdiction-dependent applicability.

**Unsupported legal-compliance claims in current output: 0.** These are rule checks against configured evidence, not legal determinations, and the only permitted form of words ends "subject to responsible-authority review". A general principle worth keeping: **a rule may not require as prerequisite the very condition it tests** — FAR 43.301 listed `written_instrument` as its own precondition, so an applicable-but-missing SF 30 returned INSUFFICIENT_EVIDENCE instead of NOT_SATISFIED.

## 10. Category 9 is metadata, never a vote

Voting is exactly `A1.7` (TCPI) and `A1.8` (VAC) — count 2. No C1 module is in the voting set; every C1 row carries `category_9_metadata_only` and `voting_eligible = False` and asserts no band. The Run-26 exclusion of Data Integrity from Project Status survives.

## 11. Lineage

UNRESOLVED treated independent **0**; false reinforcement **0**; false suppression **0**; ambiguous **0**. Qualification and lineage are separate dimensions in both directions. Dependence stays pairwise and non-transitive; no connected-component closure. B3.2/B3.4/B3.5 declarations were **removed, not rewritten** — the relationships they asserted had stopped existing, and inventing new independent bodies would manufacture the independence the table exists to prevent.

## 12. The 64-fault campaign

**64 required, 64 attempted, 64 applied, 64 RED for the intended reason, 64 restored GREEN, NOT_APPLIED = 0, crashes accepted as RED = 0.** Every injection confirmed landed by re-reading bytes from disk; `__pycache__` dropped on both sides.

The campaign earned its keep by failing first. It exposed:
- **a vacuity in my own guard** — the bypass check iterated `gated_module_ids()`, so removing a category made its modules leave the loop and the guard stayed green;
- **two crashes scored as RED**, now impossible: no anchored `RESULT` line is recorded as CRASH and fails;
- **twelve invariants asserted nowhere**, added to the oracle suite;
- **defence in depth** at 8.1 — the agentless case is protected by `model_from`, `assert_structural` *and* `agent_by_role`, so no single edit to one could expose it; the fault was repointed to where production supplies the structure.

## 13. OG-SYNTH-0.1 is historically incomplete

**This limitation must not be rounded away.** Authoritative accounting: 519 governed manifest entries, 504 recovered and checksum-matched, **15 unrecoverable rows (5 unique paths)**, 0 external-reference entries, 0 mismatches among recovered files.

The five never delivered with the archives: `validators/validate_synthetic_programme.py`, `generators/generate_opus_synthetic_programme.py`, `validation_report.json`, `module_asset_map.csv`, `schemas/schema_catalog.json` — each named by `REPORT_2026-08-11` §3.

My earlier `NOT_VENDORED = 177` was wrong and was inferred from absence. Two defects produced it: the three OG-SYNTH-0.1 manifests are byte-identical (one release manifest copied per package), and the manifest is release-root-relative while this repo nests each package. The five are **not** external — the manifest claims them — so this is governed content that cannot be recovered. **OG-SYNTH-0.1 is not fully reproducible.** v0.2, v0.3 and v0.4 do not inherit this: they ship those files and they resolve and match.

## 14. Packages

Participant `og-participant-2026.08-v6` (successor; 8 files moved by six display-name substitutions; inverse mapping reproduces v5 bytes exactly; v5 pinned to `4dd5985`; exactly one record claims the tree). Participant protocol unchanged: evidence review → preliminary judgment/confidence → preliminary lock → AI reveal → final judgment/confidence/disposition/evidence/rationale → final lock → next period. No synthetic package byte changed; no successor minted.

## 15. Claim boundaries

Synthetic fixtures establish arithmetic, structure, rule behaviour, reproducibility and fault detection. They do **not** establish predictive validity, legal compliance, practitioner utility, empirical safety performance, environmental legal status or official contractor performance. Nothing here is calibrated; Run 33 owns calibration and validation.

## 16. Handoff

**Run 32** — Category-10 algorithm remediation (MOO, LP, CSP, What-if, Decision Sensitivity, Pareto, Minimax Regret, MARCOS/CRITIC placement). Run 31 enforced only the qualification interface and changed no Category-10 algorithm.

**Run 33** — calibration and empirical validation for all 16 targets. Every canonical quantity is emitted with `calibration_pending` and no `status_color`; no band was invented anywhere in this run.
