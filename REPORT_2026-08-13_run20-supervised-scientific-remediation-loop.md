Run 20 — Supervised Scientific Remediation Loop
Run-19 starting baseline: 772ad8f
Run-20 ending merge commit: recorded in T6_HANDOFF.md at the tip of this run
Run-19 scientific targets: 100/100
Run-19 remediation findings: 94 queued items plus 2 architectural targets, 96
Remediation cycles completed: 1 of 12 planned
P0A fixed: 0/0
P0B fixed: 4/4
P0C fixed: 0/4
P0D fixed: 0/4
Implementation defects fixed: 4/10
Method-label mismatches resolved: 0/23
Canonical structures implemented: 0/7
Correct abstentions introduced: 3 modules gained an abstention path that did not exist
Parameter provenance gaps resolved: 0/11
Threshold/calibration gaps resolved: 0/14
Owner decisions remaining: 4
Category-9 qualification enforced: NOT YET — ARCH.1 open
Raw qualification bypasses remaining: not reduced and not widened
Lineage controls enforced: NOT YET — ARCH.2 open
Uncontrolled duplicate-evidence reinforcement remaining: 1, unchanged
Voting set: 2    Expected: 2
Concept-only methods activated: 0
Material Cost Variance activated: NO
Final 100-module re-audit rows: NOT PERFORMED
NOT_REACHED: 0
NOT_ASSESSED: 0
IMPLEMENTATION_DEFECT remaining: 6
METHOD_LABEL_MISMATCH remaining: 23
MISSING_CANONICAL_DATA_STRUCTURE remaining: 10
PARAMETER_PROVENANCE_BLOCKED remaining: 11
THRESHOLD_CALIBRATION_BLOCKED remaining: 6
FUTURE_RESEARCH_ONLY remaining: 3
OWNER_DECISION_REQUIRED remaining: 3
Full suite: 8353/8353 across 97 suites
Production Postgres accessed: NO

**Run 20 is incomplete and this report says so at the top rather than at the bottom.** One
remediation cycle of twelve was completed, verified and committed. The remaining eleven are open,
with an exact resumption point. A truthful partial remediation is a valid Run-20 outcome and this
is one; a guessed pass is not, and there are none here.

## 1. Handoff audit

`T6_HANDOFF.md` was read from the Run-17 entry forward. Its chronology agrees with the committed
`REPORT_*` files and with Git history: Run 17, Run 18, Run 19 and Run 19's four post-merge
corrections each appear with the commit hashes Git reports. No entry was found missing and none
was invented. The Run-19 entry's closing paragraph states that its own final hash cannot be
contained in the commit that records it, which Git confirms: `772ad8f` is the tip and the entry
was written into the commit that became it.

A Run-20 working entry was added in commit 1 and updated after cycle 1. It carries date, run,
commit, simulation version `sim-2026.08-v10`, synthetic package OG-SYNTH-0.3, participant package
unchanged, scope, files changed, voting effect, activation effect, checks, deviations, defects
fixed, unresolved findings, owner decisions, stop conditions and next requirements.

## 2. Run-19 baseline ingestion

Verified mechanically, not read from the prompt:

- `server/tools/run17/scientific_results.csv`: 100 rows, 100 unique canonical ids.
- NOT_REACHED 0; NOT_ASSESSED 0.
- Run-19 disposition counts reproduce the recorded figures exactly: METHOD_LABEL_MISMATCH 23,
  CORRECT_PROXY_ONLY 17, PARAMETER_PROVENANCE_BLOCKED 11, IMPLEMENTATION_DEFECT 10,
  METHOD_PASS_CALIBRATION_PENDING 8, MISSING_CANONICAL_DATA_STRUCTURE 7, CORRECT_ABSTENTION 6,
  THRESHOLD_CALIBRATION_BLOCKED 6, REGULATORY_VERSION_BLOCKED 4, OWNER_DECISION_REQUIRED 3,
  FUTURE_RESEARCH_ONLY 3, SCIENTIFIC_PASS 2.
- The Run-19 merged-main commit is `d22e430`, with post-merge corrections `d93ea30`, `5d958fd`,
  `fddc38f`, `bc73360` and the pushed tip `772ad8f`. Run 20 branched from `772ad8f`.
- The controlling specification hashes to
  `328b50133f1d2a8d710d3cca787c24c22e2cdad0b09fe92ae2c7b7a55b8d299e`, byte-identical to the
  committed value. It was read in full, in successive chunks.
- Complete suite rerun before any change: 96 suites, 8298/8298, all green.
- The production tree was hashed over exactly the file list Run 18 froze and is byte-identical to
  `code_audit/run18_production_baseline.sha256`.

Run 19 completed 100/100, so Run 20 proceeded.

## 3. Master remediation register

`code_audit/run20_master_remediation_register.csv`, 102 rows, built by
`server/tools/build_run20_register.py`. Nothing in it is typed per module: every field is derived
from the committed Run-19 results table, the Run-19 queue and a frozen copy of the Run-19
dispositions taken from `772ad8f`, so the register cannot drift from the audit it summarises and
a fix cannot rewrite its own baseline. The 102 rows are the 100 scientific targets plus ARCH.1 and
ARCH.2, which have no scientific row of their own and would otherwise be lost.

**Authorized versus blocked: 71 authorized, 31 blocked.** Blocked means the correction requires
something this run cannot lawfully obtain. The blocked 31 are the 11 PARAMETER_PROVENANCE_BLOCKED,
the 6 THRESHOLD_CALIBRATION_BLOCKED, the 8 METHOD_PASS_CALIBRATION_PENDING, the 3
OWNER_DECISION_REQUIRED and the 3 FUTURE_RESEARCH_ONLY. By priority: P0B 4 authorized, P0C 4
authorized, P0D 4 authorized, P1 27 authorized, P2 8 authorized, P3 16 authorized and 28 blocked,
FUTURE 3 blocked, and 8 modules with no Run-19 finding open.

## 4. Remediation cycle 1 — P0B, invalid or missing evidence producing a coloured result

Root causes, classified before any code was opened: METHOD_IMPLEMENTATION_DEFECT,
DOMAIN_VALIDATION_DEFECT and MISSINGNESS_DEFECT.

**3.7 Analogous Estimating Ratio.** A budget at completion of zero or below never gated the band,
so a budget of minus one thousand reached Yellow while the band read the overrun percent alone.
It now goes through the shared positive preflight, the same one that closed this pattern in eleven
other modules, and abstains on the invalid denominator.

**8.7 Safety Performance Index.** Two mentions of safety in meeting minutes became an incident
rate of 20.0 through a multiplication by ten with no source anywhere, and the project banded Red
on it. Specification 8.7 forbids using incidents discussed in meeting minutes as an OSHA
incidence-rate substitute in those terms. The multiplier was removed at the root rather than
fenced off in the derived case, so no incident count from any document becomes a rate; only a
reported incidence rate does.

**9.2 Data Timeliness Score.** There was no lower guard on the document age at all. A document
dated a year after the period cutoff reported an age of minus 365 days, banded Green, the freshest
reading the module has, and told the reader the document was minus 365 days ago. Future-dated
records now abstain as malformed, which is the explicit invalid or review handling specification
9.2 requires.

**9.7 Reporting Frequency Index.** Only the intervals between observed reports were measured, so
the period cutoff was never compared to the last report and cessation was invisible: a project
that uploaded twice ten days apart and then stopped for seventeen months reported a ten-day
average interval and banded Green. The gap from the last report to the end of the period is now
measured on the module's own existing ladder, introducing no new threshold, and the band is taken
from whichever of the two readings is worse. The mean interval the project once kept is still
reported truthfully beside the gap.

## 5. The Run-19 finding that could not be reproduced as specified

One, and it is recorded rather than quietly closed.

Run 19's proposition `3.7/domain-guarded` required **both** a negative overrun percent and a
negative budget to be refused. The budget half reproduced exactly and is fixed. The overrun half
reproduced as described but its prescribed correction conflicts with a committed production
contract: `server/app/field_registry.py` declares `analogousOverrunPct` one of exactly four fields
in `SIGNED_SI_FIELDS` where a negative value is a real project condition, with the reason stated
in the file — a reference project that underran is a negative overrun. The supervisory
specification's Category 3 authority requires analogs be selected and adapted, not filtered by the
sign of their outcome, and refusing a negative overrun would discard a legitimate analog.

Two committed artifacts disagreed. The field contract was followed, because it is explicit and
reasoned about this exact field and the specification is silent on the sign. What was genuinely
wrong in that case is what the module said: it reported minus five hundred as a BAC exposure,
which reads as a negative quantity of money at risk, and no such quantity exists. The exposure is
now nought, the signed comparison is kept beside it under its own name so nothing is lost, and the
sentence names the underrun. The Green band on an underrunning analog is truthful and stands.

The Run-19 proposition was **amended in place, not deleted**, to require the part that was
genuinely wrong, and the conflict is recorded in the production comment, the test comment, the
transition log and this report.

## 6. Neighbour sweep — what Run 19's sampling missed

`code_audit/run20_neighbour_sweep_results.csv`. Three patterns swept clean. The fourth found a new
defect class, and it is the important one.

**Four suites were asserting the superseded behaviour as their expected answer.** They were found
by running the complete suite after the fix, not by reading the suites, which is why Run 19's
sampling did not find them.

- `test_run10_bucket2_corrections.py` asserted "A6.2 still bands a derived count above nought",
  fixing the 8.7 defect in place as expected behaviour.
- `test_run6_known_answer.py`, `test_run7_fix_now_defects.py` and `test_run8_retest_classify_27.py`
  each asserted a safety index and an incident rate derived from the uncited multiplier. All three
  **crashed with a KeyError rather than failing** — the failure mode this programme has recorded
  before, caught only because the strict runner refuses a missing RESULT line.
- `test_run8` had even documented the defect in a comment as "THE FALLBACK IS STILL STANDING"
  while asserting its output.
- `test_run6` additionally asserted the 9.7 mean-interval band on a project that had not reported
  for 160 days.

Every assertion was rewritten to the corrected contract with the superseded reading stated at the
point it changed. None was deleted. This brings the programme's count of suites found encoding a
defect as expected behaviour from five to nine.

## 7. Canonical oracle evidence

No production logic was copied into any oracle. Expected values came from hand calculation stated
in the check itself — 535 days from 2025-01-11 to 2026-06-30, 160 days from 2025-01-21 to
2025-06-30, both computed by month — and from the committed Run-19 category oracles, which
self-prove against the specification's worked answers at import:
`oracles_cat_9.cadence_report` for cessation and `oracles_cat_9.timeliness_state` for the
future-dated case.

## 8. Mutation proof

Six injections, `code_audit/run20_fault_injection_results.csv`. Each was confirmed to alter bytes,
each produced a named red, each was restored and reproved green. None was absorbed, none crashed,
none changed nothing.

## 9. Category-9 enforcement

`code_audit/run20_category9_enforcement_results.csv`. **Raw bypass is NOT closed.** ARCH.1 is
open: the Category 9 qualification gate does not exist as an object and cycle 1 did not build it
and does not claim to. What cycle 1 did do is strictly reduce the unqualified evidence reaching
fusion: three of the four modules now abstain in cases where they previously produced a coloured
band, and none emits more than before.

## 10. Lineage and double counting

`code_audit/run20_lineage_results.csv`. **Unchanged.** ARCH.2 is open. Run 19's finding that one
body of evidence combined twice sharpens belief from 0.70 to 0.93 stands, with the same number
before and after this run, because cycle 1 did not touch the combination rule. None of the four
corrected modules is a combination rule and none feeds another module as evidence; all four are
leaf indicators.

## 11. Calibration and provenance

`code_audit/run20_calibration_results.csv`. One parameter was removed and none was invented. The
multiplier of ten in 8.7 was classified UNSUPPORTED and deleted. The benchmark of 3.0 in 8.7, the
30/60/90 ladder in 9.2, the 14/30/60 ladder in 9.7 and the 3/7/12 ladder in 3.7 are all
HEURISTIC_UNCALIBRATED and were left untouched. The 9.7 correction was deliberately measured on
the module's existing ladder precisely so that closing a P0B defect did not smuggle in a new
uncalibrated threshold.

## 12. Regulatory remediation

`code_audit/run20_regulatory_results.csv`. **No superseded authority was found, because none was
looked for.** No web retrieval was attempted in this run and no rule-version claim is made. The
only regulatory content enforced was the specification's own prohibition on substituting meeting
minutes for the OSHA incidence rate, which needs no version claim. 8.2, 8.3, 8.4, 8.8 and 10.3
remain REGULATORY_VERSION_BLOCKED and untouched.

## 13. Disabled and concept-only methods

**None was repaired in the laboratory in this run, and none was activated.** The eight concept-only
methods remain DISABLED_UNSAFE and Material Cost Variance 3.4 remains
DISABLED_EVIDENCE_UNDER_REVIEW, both verified directly from `registry.activation_state` rather
than asserted. Verified in this run: voting set exactly `{A1.7, A1.8}`; concept-only disabled set
exactly `{A3.8, B2.7, B2.9, B2.20, B4.1, B4.2, B4.5, B4.6}`; evidence-under-review set exactly
`{A3.4}`.

## 14. Owner decision register

`code_audit/run20_owner_decisions_required.csv`, four items. The three Run-19 items (2.4 schedule
compression metric definition; 5.4 category placement and the shared decision object; PH.4 pattern
definition) plus one raised by cycle 1: whether 3.7 keeps the analogous estimating name or is
renamed to the transparent indicator it is. That decision did **not** block the P0B fix, which was
delivered independently of it. The safe default under every option is NON-VOTING and ADVISORY,
which is the current state, so nothing is waiting on the owner to stay safe.

## 15. Anti-fossilization

`server/tools/test_run20_p0b_evidence_domain.py` pins the exact historical defective output of all
four modules as the thing that must **not** come back, never as an expected answer, with the
scientific reason beside each. Four suites that had fossilized the defect were corrected. The
transition log `code_audit/run20_disposition_transitions.csv` records from-disposition,
to-disposition, cycle and evidence for each move.

A structural anti-fossilization improvement was also made. The results table is rebuilt from the
eight category result files by `run19_consolidate.py`, so an earlier version of this run's
disposition script, which edited the table directly, would have been silently overwritten. The
dispositions now live in the category suites beside the propositions that justify them, one
declared manifest `server/tools/run20_production_changes.py` names every module Run 20 changed in
production, and both the category suites and the consolidator check every row against it. An
undeclared production change and a declared fix that was never delivered now both fail loudly.

## 16. Before and after disposition table

| Disposition | Run 19 | After cycle 1 |
|---|---|---|
| METHOD_LABEL_MISMATCH | 23 | 23 |
| CORRECT_PROXY_ONLY | 17 | 18 |
| PARAMETER_PROVENANCE_BLOCKED | 11 | 11 |
| IMPLEMENTATION_DEFECT | 10 | **6** |
| METHOD_PASS_CALIBRATION_PENDING | 8 | 8 |
| MISSING_CANONICAL_DATA_STRUCTURE | 7 | **10** |
| CORRECT_ABSTENTION | 6 | 6 |
| THRESHOLD_CALIBRATION_BLOCKED | 6 | 6 |
| REGULATORY_VERSION_BLOCKED | 4 | 4 |
| OWNER_DECISION_REQUIRED | 3 | 3 |
| FUTURE_RESEARCH_ONLY | 3 | 3 |
| SCIENTIFIC_PASS | 2 | 2 |
| **Total** | **100** | **100** |

Four modules moved. 3.7 IMPLEMENTATION_DEFECT to CORRECT_PROXY_ONLY. 8.7, 9.2 and 9.7
IMPLEMENTATION_DEFECT to MISSING_CANONICAL_DATA_STRUCTURE. **None moved to SCIENTIFIC_PASS, and
that is the honest result**: in each case the arithmetic defect is closed and a structural gap the
specification names remains — employee hours worked for 8.7, a governed source-class freshness
allowance for 9.2, a governed expected cadence for 9.7, analog selection and adaptation factors
for 3.7. Every transition cites its evidence in the transition log.

## 17. Voting and production hash proofs

Voting set read directly from `registry.CORE_VOTING_MODULES`: exactly `{A1.7, A1.8}`, two, before
and after. No module was added, removed or reweighted.

`code_audit/run20_production_baseline.sha256` covers exactly the file list Run 18 froze. Against
that baseline, **exactly three files differ**: `server/app/simulation/models_doc.py`,
`server/app/simulation/models_dq.py` and `server/app/simulation/models_ext.py`. Every other
production file is byte-identical. The three are exactly the files named in
`server/tools/run20_production_changes.py`.

## 18. Complete suite

97 suites, **8353/8353**, all green, on the branch tip. The baseline was 96 suites and 8298 checks;
the new suite adds 47 checks and the corrected suites account for the remainder. No suite was
skipped, no suite printed a prose summary, and no suite exited nonzero.

## 19. Unresolved limitations, stated plainly

- **Eleven of twelve remediation cycles are not started.** P0C, P0D, P1, P2 and P3 are open.
- **The mandatory complete 100-module re-audit of section 19 was not performed.** It is the final
  cycle of Run 20 and the earlier cycles are not complete, so running it now would produce a
  re-audit of a half-remediated instrument and present it as a final one.
- **Category 9 raw bypass is open** and **lineage double counting is open**. Neither was widened.
- **No web retrieval was attempted.** No primary source is claimed to have been read in this run.
  The committed specification was the theoretical authority throughout, which it is sufficient to be.
- **No browser was driven.** The four corrected modules now abstain in cases where they previously
  banded, and that rendering path is unverified in this run.
- The two hash-manifest CSVs `code_audit/run9_no_operational_effect.csv` and
  `run10_no_operational_effect.csv` are rewritten by their own suites on every execution and were
  restored to their committed state, as prior runs did.

## 20. Exact Run-21 queue

`code_audit/run20_run21_instrument_queue.csv`. It says at the top that items 3 and 4 are unfinished
**Run-20** work, not Run-21 work, so that the next session resumes the remediation loop rather than
starting instrument qualification over a half-remediated instrument.

**Resumption point.** Take `code_audit/run20_master_remediation_register.csv`, filter
`status == OPEN`, order by `priority`, and begin with P0C. Everything a cycle needs is in the
register row, the Run-19 queue row it derives from, and the category suite proposition that
records the defect.
