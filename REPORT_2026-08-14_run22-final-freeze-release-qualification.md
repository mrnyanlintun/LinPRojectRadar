# Run 22 — Final Freeze / Release Qualification

Actual starting commit: ba5bfaf0e1c7d517abd0563119c9aa36c072f251
Final merged-main commit: FINAL_COMMIT_PLACEHOLDER

Inherited Run-22 queue: 9
Closed: 5 — items 5, 6, 7, 8 and 9
Safely unresolved/non-blocking: 4 — items 1, 2, 3 and 4, all owner or research decisions
Release-blocking unresolved: 0

Production-tree completeness guard: PASS
Reload-latency qualification: PASS
Clean-checkout reproducibility: PASS
Scientific-baseline integrity: PASS
Category-9 integrity: PASS
Lineage integrity: PASS
Instrument/browser qualification: PASS
Participant qualification: PASS
Guard non-vacuity: PASS

Scientific targets: 100/100
Voting: 2
Expected: 2
Concept-only activation: 0
Expected: 0
Material Cost Variance enabled: NO
Expected: NO
Participant protocol changed: NO
Expected: NO
Production Postgres accessed: NO
Expected: NO

Final suites: 121
Final checks: 10411/10411

Freeze identifier: OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN22
Freeze manifest SHA-256: FREEZE_SHA_PLACEHOLDER

FINAL RELEASE STATUS:

**RELEASE_QUALIFIED**

---

## 1. Git-baseline reconciliation

The owner's section 0 records an apparent inconsistency between three commit references. It is
not an inconsistency. All three are correct facts about one linear history, and no repair was
needed.

| reference | what it actually is | ancestor of main |
|---|---|---|
| `ba5bfaf` | HEAD, `main` and `origin/main`, all three identical | yes |
| `dc02fe8` | the commit carrying the final Run-21 report — the **parent** of `ba5bfaf` | yes |
| `a1c5509` | the Run-20 closure reconciliation, committed before qualification work began | yes |

`ba5bfaf` is the one-line follow-up that stamps `dc02fe8`'s own hash into the report and the
handoff. **A report cannot contain the hash of the commit that introduces it**, so the stamp is
necessarily a later commit. Run 20 used the same two-stage pattern (`9e1b8d7` report, `7cb5d8c`
handoff, `e73f3c9` stamp). All eight Run-21 commits are ancestors of `main`.

**The actual Run-22 starting commit is `ba5bfaf`.** Full detail in
`code_audit/run22_git_baseline_reconciliation.csv`.

The starting state was independently reproduced rather than accepted: `run_all_suites.sh` at
`ba5bfaf` gives **119 suites, 10335/10335, ALL SUITES GREEN**, exactly Run 21's figure.

### One instrument error in this run, recorded because the standing rule requires it

A suite launch was written `ls .venv/bin/python && nohup ./run_all_suites.sh > log`. There is no
virtualenv, the `&&` short-circuited, nothing ran, and a **pre-existing scratchpad log** reporting
115 suites / 10060 checks was read as the Run-22 baseline. 115 did not match the 119 files on
disk; following the rule to suspect this run's own instruments first, the log's timestamp was
checked and predated the Run-21 suite files. 115/10060 is the Run-20 baseline at `e73f3c9`.
Caught before it reached any conclusion. `run_all_suites.sh` is not at fault — it falls back to
the interpreter on `PATH` by design.

## 2. The inherited nine-item queue, reconciled mechanically

Read from `code_audit/run21_run22_freeze_queue.csv`, not from the narrative. Full register at
`code_audit/run22_freeze_qualification_register.csv`.

| id | item | queue's blocking column | Run-22 outcome |
|---|---|---|---|
| 1 | participant-surface rename | blocking only *for a release that renames* | **OPEN, OWNER** — not blocking; this release renames nothing |
| 2 | B1.4 Worst-N-of-M has no source for N | not blocking: advisory, non-voting | **OPEN, OWNER/RESEARCH** — verified safe from the registry |
| 3 | PH.5 anomaly-score weights uncalibrated | not blocking: advisory, non-voting | **OPEN, OWNER/RESEARCH** — verified safe from the registry |
| 4 | empirical validation as a programme | blocking only *for a validated-performance claim* | **OPEN, RESEARCH** — this release makes no such claim |
| 5 | freeze enumerates a fixed 143-file list | **BLOCKING FOR A FREEZE** | **CLOSED** |
| 6 | four suites crash rather than fail | not blocking | **CLOSED AS ANSWERED**, deliberately unchanged |
| 7 | ~195-second browser reload | **BLOCKING IF REAL** | **CLOSED — characterized, not real** |
| 8 | reset contract stated only in a tooltip | not blocking | **CLOSED AS CONSIDERED**, deliberately unchanged |
| 9 | freeze and release qualification itself | **BLOCKING** | **CLOSED by this run** |

**A correction to the controlling prompt, stated plainly.** Section 8 describes item 9 as the
"OWNER / RESEARCH BLOCKER". The committed queue does not say that: item 9 is *"freeze and release
qualification itself"*, owner `RUN 22`. The owner/research items are 1, 2, 3 and 4. Section 5
directs that the CSV be reconciled mechanically rather than inferred from the summary, and this
register follows the CSV.

## 3. Item 5 — the freeze blind spot. It was real, and it was large.

Every freeze this programme has taken — `run18_production_baseline.sha256`,
`run20_production_baseline.sha256`, the immovable `run20_production_freeze.sha256` — is a list of
**143 named paths**, and the guard's own first check asserts `len(baseline) == 143`. A file absent
from the list cannot be reported, because the guard never asks the filesystem what is there.

Walking the deployed roots at `ba5bfaf` and subtracting those names leaves **83 production
files**:

| file | lines | why it is production |
|---|---|---|
| `server/app/simulation/lineage.py` | 907 | imported by `research_export`, `writes`, `fusion`, `compute`, `registry` |
| `server/app/simulation/method_labels.py` | 426 | imported by the registry |
| `server/app/simulation/parameters.py` | 412 | imported by `models_sim`, `registry` |
| `server/app/simulation/qualification_gate.py` | 335 | imported by `compute` |
| `server/app/simulation/arm_lineage.py` | 162 | imported by `models_evc`, `models_gov` |
| all 25 `server/alembic/versions/*.py` | — | define the production database schema |
| `server/requirements.txt` | — | changes the running code without changing a source line |
| `render.yaml` | — | the deployment blueprint |
| `logo.png`, `research/deepdive.html` | — | served **by name** from `app.main` |
| every vendored font, the country geojson | — | `app.main` mounts `assets/` **wholesale** |

**About 2,240 lines of the backend Run 20 spent twelve cycles qualifying — the entire Category-9
lineage layer and the qualification gate — sat outside every freeze this programme has taken.**

`server/tools/production_tree.py` holds **roots and exclusions, not files**, and walks. Roots are
derived from `app.main` and `render.yaml`, not chosen by taste; every exclusion is a generated
cache and carries its reason. The walk reads the **filesystem, not git**, because `app.main`
mounts `assets/` with `StaticFiles` and an untracked file dropped there is served to a participant
exactly like a tracked one. `code_audit/run22_production_tree.sha256` is the **record** of what
the walk found — the expected value, never the source of the names.

**226 files. Manifest SHA-256 `bff7b4fc2460580494efb1eac4fba350b1ba39d8b2cb08f095bbdbe109f47a92`.
A strict superset: all 143 of the old freeze's paths are still protected.**

## 4. Production-file completeness — mutation evidence

Proved red four ways against the **real repository tree**, restored green after each, with the
manifest hash returning to `bff7b4f`:

| mutation | guard output | exit |
|---|---|---|
| add `assets/js/run22_temp_fake.js` | `ADDED assets/js/run22_temp_fake.js` | 1 |
| append a byte to `lineage.py` | `CHANGED server/app/simulation/lineage.py` | 1 |
| delete `assets/js/neural_flow.js` | `REMOVED assets/js/neural_flow.js` | 1 |
| rename `signals.js` | `RENAMED …`, **and** one `ADDED` + one `REMOVED` | 1 |
| restore | 226 files, `bff7b4f…` | 0 |

A rename is reported *both* as a rename and as an add plus a remove, so it can never net off to
nothing. A vanished root **raises** rather than being skipped. The suite repeats all of it in a
faithful copy of the tree so the campaign leaves nothing mutated: `42/42`.

The guard's own first run caught a lazy justification in my exclusion list (`.pyo` had the reason
"as above"), which is the guard doing its job on its author.

## 5. Item 7 — the reload, diagnosed rather than excused

No timeout was widened. Run 21's ~195 s came from a loop polling `page.evaluate` every two
seconds, and its own note records **1 successful read and 1 evaluate error in 212 seconds**.
`page.evaluate` cannot answer while the renderer main thread is busy, so that figure is the moment
the harness was next *willing to look*, not the moment the page was ready. Run 22 measured from
browser events and the document's own `performance` timeline, neither of which needs an execution
context.

**Three explanations died.**

| hypothesis | measurement | verdict |
|---|---|---|
| the server | `responseStart` 12 ms, `responseEnd` 21 ms; every subresource < 53 ms | refuted |
| third-party resources (owner's option A) | aborted **54.13 s** vs allowed **59.06 s** | refuted — 5 s of 54 |
| the `reload()` primitive | `goto` **58.54 s** vs `reload` **54.13 s** | refuted |

What remains is `responseEnd` → `domInteractive`. A DevTools CPU profile attributes **51,913 ms of
52,202 samples — 99.4% — to `(program)`**, V8's label for time spent *outside* JavaScript in
native browser code. Application JavaScript is under 0.4% of the interval, so **option B, required
application or API work, is refuted too.**

Three GL configurations differing in nothing else settle it:

| configuration | responseEnd → domInteractive | app usable |
|---|---|---|
| `--use-gl=swiftshader` (exactly the Run-21 driver's flags) | **61,111 ms** | 61.27 s |
| browser default, no GL flags forced | **62,726 ms** | 62.85 s |
| `--disable-webgl --disable-gpu` | **288 ms** | **0.54 s** |

Independently confirmed by project state: a reload with **no 3D surface open** is usable in
**0.78 s** (`domInteractive` 531 ms), while an **empty** project with the detail open costs 61.9 s
— as much as a fully populated one's 54.1 s. **The cost does not scale with data.** It appears
only when a 3D surface must be rasterised.

**This is the owner's option C.** The instrument's own cost to become usable after a reload is
**288 ms** of main-thread work on top of a 12 ms server response. The 54–195 s is a GPU-less
container emulating the GL pipeline on its CPU, a path a machine with hardware graphics
acceleration does not execute. The browser default is *also* slow here precisely because there is
no GPU to fall back to.

Further corroboration arrived unlooked-for: the Run-21 driver re-run on the candidate recorded
**149 s, 173 s and 405 s** under identical flags where the isolated probe read 54–62 s. A fixed
server or application cost does not vary by a factor of seven with container load. CPU-bound
software rasterisation does.

**Residual risk, recorded rather than dismissed.** What is proved is that the cost is borne
entirely by the GL pipeline. It follows that a participant with hardware acceleration does not pay
it. It does **not** follow that a participant whose browser falls back to software WebGL — old
hardware, a blocklisted driver, WebGL disabled by policy — would have an acceptable experience on
the detail view. That is a screening question for participant machines, bounded to the 3D surfaces
on that one view, and it is a known limitation of this release.

### Two defects in the Run-21 driver, found while reading it

- A third-party-abort disclosure and a second `return` sat **after** `return verdict`. The driver
  documented an evidence row in a comment that its code never emitted, and
  `run21_reset_reload_results.csv` has no such row. Both hoisted; dead return removed. **The rows
  now appear**, which is how the fix was verified.
- Both reload checks read `check(did != "no")`, which **passes for `"not determined"`** — the case
  where the page could not be read at all — under a label asserting the document was destroyed.
  Tightened to `did == "yes"`. Failing to observe survival is not evidence of destruction.

## 6. Item 9, and items 6 and 8

Item 9 is this run. Items 6 and 8 were re-verified at the starting commit rather than accepted
from Run 21's summary, and both were **deliberately left unchanged**: the four crashing suites
have no correctness consequence under a runner that anchors `^RESULT: N/M$` and fails a green line
with a nonzero exit, and rewriting them would remove the stack trace that makes a crash
diagnosable; and the reset tooltip is presentation only, with the truthfulness defect — the page
asserting the project had no documents while the server held and used them — already fixed by
Run 21. Adding an unforced participant-visible change during a freeze run, with no defect behind
it, is not an improvement.

## 7. Period transition — resolved against the actual design

There is **no study-wide period constant in production**. `period_count` is a nullable integer
supplied per scenario. `code_audit/run12_participant_provisioning.csv` freezes the project
packages at `period_count=2`; the locked praxis design describes one sequence per scenario ending
at "next-period project state, follow-up decision" — an opening period and one follow-up; and the
praxis decision log carries *"whether the observation count needs raising via reporting periods"*
as an **open advisor question**, not a settled three-period design.

**So no third period was invented**, exactly as section 10 directs. The participant driver's
behaviour confirms it independently: it works PERIOD 1 and PERIOD 2 and then breaks because the
server confirms the participant has **rolled to the next assignment**.

What was added is generalisation evidence about the *instrument*, not a protocol claim:
`test_run22_period_generalization.py` creates a `period_count=3` scenario and drives P1 → P2 → P3
through the full locked sequence at every period — reveal refused before the preliminary lock,
preliminary locked, second submission refused, final locked, second submission refused — and
requires the server to refuse the advance out of P3 **naming three periods**, which proves the
limit came from the data and not from a constant. `33/33`. Proved non-vacuous: mutating the
scenario to `period_count=2` gives **24/33**.

## 8. Owner and research items

Four remain open; none blocks. Full analysis in `code_audit/run22_owner_decisions_remaining.csv`.
Items 2 and 3 were verified safe **from the registry**, not from prose: neither B1.4 nor PH.5 is
in `CORE_VOTING_MODULES`, both are `ADVISORY_ONLY` and non-voting in the Run-20 re-audit, so
neither can produce an unsupported authoritative participant-visible status. Neither may be closed
by inventing a number, and **Tavily and live web were unavailable in this session**, so no external
source could be sought; that is recorded as the reason rather than treated as a blocker.

The one item worth the owner's attention now is **item 1**. It does not block this release, but
the praxis constraint is that no participant session begins before the instrument gates are green
— and those gates are now green. **If the owner intends to rename anything a participant reads,
the only clean moment is before the first session**, because after that a rename is a protocol
change rather than a cosmetic one.

## 9. Scientific integrity

Derived from the registry and the committed re-audit at freeze time, not copied from a report.

| quantity | required | observed |
|---|---|---|
| registered project modules (groups A+B+C) | 96 | **96** |
| Material Cost Variance excluded | 1 | **1** |
| project scientific targets | 95 | **95** |
| portfolio targets (group D) | 5 | **5** |
| total scientific targets | 100 | **100** |
| unique canonical IDs | 100 | **100** |
| `NOT_REACHED` | 0 | **0** |
| `NOT_ASSESSED` | 0 | **0** |
| `IMPLEMENTATION_DEFECT` | 0 | **0** |
| `METHOD_LABEL_MISMATCH` | 0 | **0** |
| `MISSING_CANONICAL_DATA_STRUCTURE` | 0 | **0** |

Truthful lesser dispositions are preserved, not converted: `CORRECT_PROXY_ONLY` 44,
`METHOD_PASS_CALIBRATION_PENDING` 23, `CORRECT_ABSTENTION` 16, `FUTURE_RESEARCH_ONLY` 8,
`SCIENTIFIC_PASS` 3, and one each of the blocked classes.

**A trap avoided and pinned.** `server/tools/run17/scientific_results.csv` still carries
`METHOD_LABEL_MISMATCH` 23, `IMPLEMENTATION_DEFECT` 6 and `MISSING_CANONICAL_DATA_STRUCTURE` 13.
It is the **Run-17 historical record**, superseded by `code_audit/run20_cycle12_100_reaudit.csv`.
Both are frozen so the history is auditable, and the freeze manifest **names which is which** so
the superseded one can never be mistaken for the current baseline.

## 10. Voting and activation

Derived from `registry.CORE_VOTING_MODULES`, not hard-coded: **exactly 2 — A1.7 (TCPI) and A1.8
(Variance at Completion)**. Concept-only activation **0** across the eight disabled modules.
`DISABLED_MODULES` totals 9.

**Material Cost Variance is canonically `A3.4`.** The owner's prompt calls it "3.4"; that is not
its canonical identifier and its `old_id` is in fact **3.5**. The standing rule that
`module_renumbering_map.csv`'s `old_id` column is not canonical identity is applied throughout.
It is disabled, in its own `DISABLED_EVIDENCE_UNDER_REVIEW` set, deliberately separate from the
concept-only eight because it is **not** classified as algorithmically invalid.

## 11. Category-9 and lineage

All nine campaigns re-executed on the candidate, all green: category-9 gate 61/61, lineage
declaration truth 288/288, voting lineage 100/100, cycle-12 lineage and guards 33/33, re-audit
30/30, primitive lineage 149/149, B2.1 DST lineage 69/69, ARCH.3 clusters 115/115, ARCH.5 siblings
108/108.

All **14** campaign properties HOLD, including the bridge case A={X}, B={X,Y}, C={Y} **in all six
orderings** with dependence *not* closed transitively.

**False reinforcement 0. False suppression 0. Declaration identity defects 0.**

## 12–14. Instrument, participant, reset/reload qualification

Both real-browser drivers re-run against the candidate freeze in a real Chromium:
**instrument 78/78, participant 77/77, zero failures.**

The participant total is 77 where Run 21 recorded 78. The reason is recorded rather than smoothed
over: the PERIOD IDENTITY section emits one check per prior-period snapshot row, so **the total is
data-dependent and two runs of the same driver are not comparable by count**. Every check that ran
passed.

Lock enforcement re-proved in the browser: no AI in the served page or the sequence-state route
before the lock; the server refuses `researchreveal` before the lock; the server refuses a route
edit of the locked preliminary; the reveal control appears only after the lock; the server refuses
both an edit of the final action and a change of the final confidence after the final lock; the
database itself refuses an edit when the application is bypassed; and session and participant
isolation hold across a second participant in a second session.

Empty, populated, reset, post-reset new evidence, hard reload, fresh context and project switch
all exercised. **Run 21's truthful reset language survives**: after a reset the strip reads
`0 UPLOADED SINCE THE RESET, 24 RETAINED`, the server still holds all 24 upload events, and
nothing claims the retained documents were deleted.

Run-21's own committed artifacts were **restored** after the re-run rather than overwritten; this
run's evidence is captured under `run22_final_*`.

## 15. Clean-checkout reproducibility

See `code_audit/run22_clean_checkout_reproducibility.csv`. A `git worktree` at the release commit
in a temporary directory — committed content only, verified zero untracked entries — with the
environment rebuilt from committed configuration alone, no secret and no production credential,
and a throwaway SQLite database from `alembic upgrade head`. Production manifest, authority
manifest, freeze-manifest digest and the complete suite all verified there.

## 16. Guard non-vacuity

`code_audit/run22_final_guard_nonvacuity.csv`. Each mutation edits **real production** and
requires the suite that should notice to go red; every file's SHA-256 is checked byte-identical
after restore, and the whole tree is re-walked at the end to catch a leak in a file the campaign
never named.

| invariant | mutation | suites | result |
|---|---|---|---|
| voting = 2 | a **third** voting module | 100/100→95/100, 50/50→48/50, 28/28→25/28 | **NON-VACUOUS** |
| concept-only activation = 0 | B4.6 released from the disabled set | 50/50→48/50, 111/111→107/111, 189/189→179/182 | **NON-VACUOUS** |
| MCV disabled | A3.4 re-enabled | 78/78→63/78, 28/28→26/28 | **NON-VACUOUS** |
| production-tree completeness | add / change / delete / rename / vanished root | red on each, green on restore | **NON-VACUOUS** |
| supervisory-spec hash | an edit to the controlling specification | red | **NON-VACUOUS** |
| preliminary lock, AI pre-lock, final lock | `period_count` 3→2 | 33/33 → 24/33 | **NON-VACUOUS** |

### The supervisory specification had no executable guard at all

Its SHA-256 `328b5013…` appears in four reports, in `T6_HANDOFF.md` and in its own metadata file,
and **nothing executable checked any of them**. A hash that lives only in prose cannot fail.
`research/methodology` and `.gitattributes` — which carries the `-text` rule without which a
checkout filter can change the specification's bytes with nobody editing it — are now walked and
pinned exactly as production is, and checked three independent ways.

### The campaign caught something nobody staged

`test_run12_final_verification.py` invoked the defensibility generator in its default **WRITE**
mode against `assets/js/ds_defensibility_evidence.js` — a **served production file** — then
compared it to its previous contents. On a healthy tree that write is a no-op and invisible. When
they disagree the suite reports it correctly and **leaves production overwritten**. A reverted
registry mutation therefore survived in a file the campaign never touched, and **the new tree
guard caught it**. That is the strongest non-vacuity evidence in this run, because the guard
caught a real unintended mutation rather than a staged one.

Fixed by switching to the generator's existing `--stdout` mode, which
`test_run11_defensibility_claims.py` already used. The check keeps its exact meaning and gains no
side effect, plus a new check that it did not itself rewrite the file. **A test suite must not be
able to modify what the freeze protects.**

## 17. Anti-fossilization

Six Run-22 entries appended to `code_audit/run20_anti_fossilization_register.csv` (25 → 31): the
freeze blind spot; the driver's documented-but-never-emitted evidence; the guard that passed on
absence of evidence; Run 21's measurement artefact reported as a quantity; the suite that wrote
the production file it checks; and this run's own stale-log misread. No expected result was
changed to match production.

## 18. Final suite

**121 suites, 10411/10411, ALL SUITES GREEN on the final merged commit.** No carry-forward.
The total reconciles exactly against the 10335 baseline: **+33** period generalisation, **+42**
production-tree completeness, **+1** for the new no-side-effect check in `test_run12`.

## 19–20. Hashes and version identities

Complete in `code_audit/run22_hash_manifest.csv`,
`research/freeze/FINAL_RESEARCH_INSTRUMENT_FREEZE_2026-08-14.json` (226 production files with
per-file digests) and `code_audit/run22_production_inventory.csv`.

| artifact | SHA-256 |
|---|---|
| production tree manifest (hash **of the manifest**) | `bff7b4fc2460580494efb1eac4fba350b1ba39d8b2cb08f095bbdbe109f47a92` |
| authority tree manifest | `91f1856cbd3750947c16ebd81d69fee46e71d1eb7912d359c6996f850fae64e7` |
| supervisory specification | `328b50133f1d2a8d710d3cca787c24c22e2cdad0b09fe92ae2c7b7a55b8d299e` |
| final scientific results (Run-20 re-audit) | `9d5757c703cbca35eca2902fa7015b14e07fe4480100ab97543bdda760e8ebad` |
| freeze manifest (stage 1) | `FREEZE_SHA_PLACEHOLDER` |

**The self-reference is handled honestly rather than by an impossible guarantee.** A file cannot
contain its own digest, and a manifest cannot contain the hash of the commit that introduces it.
Stage 1 writes the manifest with `manifest_sha256` and `final_commit` explicitly `null` and says
why; stage 2 records the digest of that now-immutable file in a companion `.sha256`. Verification
is `sha256sum -c`. No circularity is claimed.

## 21. Known limitations

1. **Item 1** — the participant-surface rename is an open owner decision. This release renames
   nothing a participant reads.
2. **Item 2** — B1.4's fixed N has no source. `PARAMETER_PROVENANCE_BLOCKED`, advisory,
   non-voting.
3. **Item 3** — PH.5's weights have no calibration evidence. `THRESHOLD_CALIBRATION_BLOCKED`,
   advisory, non-voting.
4. **Item 4** — empirical validation is an unstarted research programme. **No module in this
   instrument is empirically validated, and this release claims no validated performance.**
5. **Reload residual** — a participant machine falling back to software WebGL would meet the same
   CPU rasterisation this container does, bounded to the 3D surfaces on the detail view.
6. **Live web unavailable** — no item was closed by guessing an external fact.

## 22. Release determination

**RELEASE_QUALIFIED.**

Both unconditional blockers are closed. Item 5's blind spot was real, was measured, and is now
covered by a guard that discovers the production surface instead of enumerating it and has been
proved red five ways. Item 7's latency was diagnosed to a specific mechanism with three
independent lines of evidence and is a property of a GPU-less qualification container, not of the
instrument; the instrument's own cost is 288 ms. Item 9 is this run.

None of the four remaining items can produce an unsupported authoritative status, corrupted
participant treatment, untrustworthy persistence, invisible production code outside the freeze, an
unreproducible baseline, or a materially unusable participant instrument. Two are safe by
enforced, registry-derived non-voting advisory state; one is conditional on a rename this release
does not make; one is conditional on a claim this release does not make.

## 23. Final T6 handoff

This is the final planned run. No Run 23 is launched. The baseline is frozen, hashed, verified
from a clean checkout, merged and pushed.
