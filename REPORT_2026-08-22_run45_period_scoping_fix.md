# Run 45: retrieval by field kind. The period-scoping fall-through is closed.

**Branch:** `run45-classification`, rooted at `2c4171d`. **Merged to `main`.**
**Stamp:** `sim-2026.08-v30`, minted at `server/app/simulation/models.py`.
**Suites:** 190 suites, **14,357 / 14,357**, 0 red, 0 aborting. **Freeze gate 32/32**, 15
blocker classes, **0 blocked**.
**Decision record:** `FIELD_CLASSIFICATION_DECISIONS.md`. **Classification proposal:**
`code_audit/run45_field_classification_proposal.md`.

The run executed its **mandatory pause**: section 5.1 produced the classification, committed it
at `38328c7`, and **stopped**. Nothing was implemented until the owner's ruling arrived.

---

## 1. The signed-off classification, as implemented

| kind | count | retrieval |
|---|---|---|
| IDENTITY | **13** | the latest value **at or before** the period being computed, declared document-type precedence holding **across** the carry-forward |
| PERIOD | **62** | the period's own documents and nothing else — **byte-identical to v29** |
| UNDETERMINED | **2** | retrieved as period fields, which is the unchanged behaviour |
| total emittable | **77** | asserted at import to partition `FIELD_KINDS` exactly |

Identity: `bac`, `baselineContractSum`, `baselineEnd`, `baselineStart`, `revisedContractSum`,
`originalContingency`, `analogousBac`, `analogousFinalCost`, `analogousOverrunPct`,
`overallRating`, `scheduleRating`, `costRating`, `qualityRating`.
Undetermined: `totalFloat`, `consumedFloat`.

**The 77-field arithmetic closes: 13 + 62 + 2 = 77.** The owner's ruling 1.5 says "period 61 …
= 76; confirm the seventy-seventh". **The difference is that the period count is 62, not 61**,
and the derivation is in section 2 of the decision record: the proposal's 60 period fields gain
**two** from the ruled set — `remainingContingency` (ruling 1.2) and `changeOrderCount` (ruling
1.3) — not one. No field is unaccounted for. The partition is asserted at import in
`server/app/field_registry.py` and checked again by the new suite, so it cannot drift.

**Ruling 1.1** approved the split as proposed, the four ratings included. **Ruling 1.2** split
the contingency pair. **Ruling 1.3** left `changeOrderCount` PERIOD; the event-accumulation gap
is recorded as a known limitation at section 8 below and in the decision record. **Ruling 1.4**
left the float pair UNDETERMINED; the contradiction is recorded at section 8 and in the decision
record. **Ruling 2.1** — the class is all 77 fields, not sixteen — is what the implementation
delivers: `WRITER_TIERS` names 16 because those are the fields where the fall-through is visible
through a lower-tier substitution; the other 61 fell through silently to absence.

## 2. Every retrieval site changed, file and line

| file | what changed |
|---|---|
| `server/app/field_registry.py:210-296` | the canonical classification: `IDENTITY_FIELDS`, `UNDETERMINED_FIELDS`, `PERIOD_FIELDS` (derived), `retrieval_kind()`, and the import-time partition assertions |
| `server/app/documents.py:391-424` | `_identity_observations_before()` — the earlier periods' identity observations, built by reusing `_period_documents` per earlier period so supersession, deduplication and the B7b shape are unchanged |
| `server/app/documents.py:1265-1269` | `_compute_and_store` passes them to `select_signal_inputs` |
| `server/app/documents.py:2299-2303` | the `extractsignals` display path passes the same, so a display cannot show a figure the computation would not have used |
| `server/app/extraction_merge.py:897-955` | `select_signal_inputs(..., *, carried=None)` — only IDENTITY-classified observations are taken from `carried`, resolved by the SAME per-field rule as the period's own |
| `server/app/simulation/models.py:531-561` | the `sim-2026.08-v30` stamp and its boundary note |

**`_period_documents` itself is untouched**, and so are `source_documents`, the staleness
fingerprint and the document-evidence table: those remain the period's own set. `docDate` is
deliberately still derived from the period's own observations alone — a carried contract must
not be able to date a period, least of all one whose own documents are undated.

## 3. The census, before and after, every change attributed

`server/tools/build_run45_census.py` drives the **real routes** — upload, extract, compute, read
back — over three corpora and writes one row per (corpus, project, period, module) and per
signal input. Run on the predecessor tree and on this one:
`code_audit/run45_census_before.csv`, `code_audit/run45_census_after.csv`. **1,581 rows each,
21 rows differ.**

**The two lines the ruling requires:**

**Line 1 — modules moving because `bac` became visible across periods: `A1.7` and `A1.8`.**
Expected, and exactly those.

| module | period | before | after |
|---|---|---|---|
| A1.7 TCPI | 3 | `tcpi 0.949` | `tcpi 0.972` |
| A1.7 TCPI | 4 | `tcpi 0.936` | `tcpi 0.969` |
| A1.8 VAC | 3 | `VAC $171,665` | `VAC $234,615` |
| A1.8 VAC | 4 | `VAC $146,762` | `VAC $200,580` |

Hand-computed independently from the stated formulae at period 3: TCPI = (BAC − EV)/(BAC − AC)
= (6,100,000 − 2,600,000)/(6,100,000 − 2,500,000) = **0.9722**; CPI = 2,600,000/2,500,000 =
1.04, EAC = BAC/CPI = 5,865,384.62, VAC = BAC − EAC = **234,615.38**. Both match.

**Line 2 — modules moving because `originalContingency` became visible across periods: `A3.2`.
IT MOVED.** At periods 3 and 4 it goes from **abstaining** (`missing_required_input`, "the
original and remaining contingency amounts are needed, and at least one of them has not been
reported for this period") to **computing**: consumed fraction 0.50 and 0.67, normalized burn
1.14 and 1.31. Hand-computed from `canonical_v3.contingency_burn`'s own two sentences:
(300,000 − 150,000)/300,000 = **0.50**, 0.50/0.44 = **1.136 → 1.14**. Both match. The ruling's
alternative — that A3.2 does not move, and 1.2's reasoning should be re-examined — **does not
arise**.

**No module moved for a third reason. Stop condition 9.2 did not fire.** The remaining 15
differing rows are all signal inputs, every one an identity field newly visible:
`baselineContractSum` at periods 2, 3, 4 (and at period 2 it CORRECTS 6,100,000 to 5,874,620),
`baselineStart` at 2, 3, 4, `originalContingency` at 2, 3, 4, `bac` at 3 and 4 (4,463,290 →
6,100,000), `baselineEnd` at 3 and 4, `revisedContractSum` at 3 and 4.

**The controls.** The `dev_fixtures` corpus (the repository's own documents, one period) and the
`four_period` corpus (a monthly report in every period, so nothing needs carrying) are
**byte-identical before and after, every row**. That is the evidence that period-field retrieval
did not change — stop condition 9.3 did not fire.

## 4. The eleven guarantees, each with the injection that proved its check can fail

Protocol per injection: apply → **re-read the bytes from disk** → run against a fresh migrated
SQLite → observe red **for the intended reason** → restore from git → re-run → confirm 77/77.
The new suite is `server/tools/test_run45_period_scoping.py`, **77 checks**.

| # | guarantee | verdict | the injection |
|---|---|---|---|
| 1 | an identity field uploaded at period 1 is retrieved at periods 2, 3, 4 | **VERIFIED** | **I1** — `_identity_observations_before` made to iterate the empty set. 77 → **53**. Restored 77 |
| 2 | an identity field superseded at period 2 keeps the old value before it and the new one after | **VERIFIED** | **I1** covers the carry; **I4** (below) covers the ordering that decides which value wins |
| 3 | a period field never carries forward | **VERIFIED** | **I2** — the identity filter defeated. 77 → **72**: `ev`, `ac`, `remainingContingency` and `actualPctComplete` all appeared at period 2, and A3.2 computed there. Restored 77 |
| 4 | upload order does not affect retrieval for either kind | **VERIFIED** | **I4** — `_snap_pick` made to return `group[0]`, i.e. whatever the database yielded first. 77 → **70**, and the order check itself went red: *"period 1: reversed upload order reports identical figures [['bac']]"*. Restored 77 |
| 5 | declared precedence holds across periods; the 6,100,000 inversion is dead | **VERIFIED** | **I3** — the tier term of `_snap_pick` zeroed. 77 → **71**: the pay application's 4,463,290 won `bac` at every period. Restored 77. The inversion case itself is asserted directly: contract at period 1 vs change order at period 2 yields **5,874,620** |
| 6 | no cross-project leakage | **VERIFIED** | **I5** — the project predicate removed from `_period_documents`. 77 → **74**: the other project reported this project's contract sum and borrowed its contingency. Restored 77 |
| 7 | every fixture result change is attributable to an identity field newly visible | **VERIFIED** | **I10b** — `ac` misclassified as identity. The census then moved **ten** modules (`A1.5`, `A1.7`, `A1.8`, `A1.9`, `A3.2`, `B1.1`-`B1.4`, `B3.1`) instead of three. Restored; the accepted classification moves exactly `A1.7`, `A1.8`, `A3.2` |
| 8 | voting count is exactly 2, `A1.7` and `A1.8` | **VERIFIED** | **I7** — a third identifier added to `CORE_VOTING_MODULES`. 77 → **76**. Restored 77. Gate B09 reports 0 independently |
| 9 | modules in service is 63, registry total 101, both derived | **VERIFIED** | **I8** — `service_index()` made to stop subtracting the retired roster. 77 → **74**. Restored 77 |
| 10 | Portfolio Health computes nowhere on any production path | **VERIFIED** | **I9** — a Group D identity forced back into `live_portfolio_modules()`. 77 → **76**. Restored 77. **I8** independently turned it non-empty, which is a second, unplanned proof |
| 11 | the successor freeze gate passes in full | **VERIFIED** | **32/32**, 15 blocker classes, 0 blocked. Proved failable **without contrivance**: when the candidate identity was stale against the tree, B01 counted 1 and the suite reported **26/32**. Rebuilt against the true tree, it is 32/32 |

**Three injections did not land as behaviour changes, and are reported as that rather than
counted as passes.**

1. **I2 first attempt** defeated the identity filter in `select_signal_inputs` only, and the
   suite stayed 77/77. **The filter is applied twice** — in `_identity_observations_before` as
   well — so neither site alone decides. Re-anchored on both; it then landed.
2. **I5 first attempt** removed the project predicate from the earlier-periods query only, and
   stayed 77/77, because `_period_documents` filters by project again inside the loop.
   Re-anchored on that filter.
3. **I9 first attempt** injected `PH.1`, which is not a Group D identifier the dispatcher reads;
   re-anchored on `D1.1`.

A fourth, **I10 (`ev` as identity)**, landed in the bytes and moved **no** module on these
corpora — at period 2 `ac` is still absent, so no index derives — so it does not discharge
guarantee 7. **I10b** (`ac`) does.

## 5. Sequence-bearing files, exception records, manifests

**No sequence-bearing file moved.** All six are byte-identical to the
`og-participant-2026.08-v15` record; gate **B04** reports `moved: none`, and the participant
package is **RETAINED**, not superseded. **No user-facing control was added, moved or removed.**

Manifests re-taken to **true bytes**, none disabled, weakened or widened:

| manifest | reconciliation |
|---|---|
| `code_audit/run45_production_tree.sha256` | the pin moves from the Run-44 manifest, which is kept addressable as its parent and is not rewritten. The guard was observed reporting **exactly four changed files, nothing added, nothing removed**, before the manifest was written |
| `test_run38/39_frozen_immutability` | `RUN45_AUTHORISED_SUCCESSOR_CHANGES = {"server/app/field_registry.py"}` — the one path no earlier run's set names. Named, not widened: anything else on a frozen surface is still red |
| `test_run25_rail_removal` | the accepted-pin chain **extended** by `run45_production_tree.sha256`; a pin at an unnamed file is still red |
| `test_run37_freeze_gate` | the parent check re-anchored onto Run 44's candidate `e6889ad5`, exactly as Run 44 re-anchored it onto Run 43's. Still refuses a record that points at itself or silently reparents |
| six version pins (`test_run31`, `test_run32`, `test_run38`, `test_run39` ×2, `test_run41`) | repointed to `sim-2026.08-v30`; the history assertions are append-only and Run 41's boundary is preserved |

`server/tools/test_run20_declared_production_changes.py` needed **no new manifest**: all four
changed production files are already declared by an earlier run's manifest, and no path may
appear in two.

## 6. Audit artifacts the suites rewrote and were restored

**18, every time, restored every time, none committed**: 17 under `code_audit/` plus
`server/tools/run17/coverage.csv` **outside** it. Restored after the baseline run, after the
first after-change run, and after each of the two final runs, each by explicit `git checkout --`
with every path named. `git add -A` and `git add .` were never used; every `git add` in this run
names its paths.

## 7. Counts reconciled exactly

| | baseline `2c4171d` | Run 45 |
|---|---|---|
| suites | 189 | **190** (+1: `test_run45_period_scoping.py`) |
| checks | 14,280 / 14,280 | **14,357 / 14,357** (+77, the new suite's own) |
| red | 0 | **0** |
| freeze gate | 32/32 | **32/32** |
| modules in service / registry / voting | 63 / 101 / 2 | **63 / 101 / 2**, all derived |

Nothing is left over.

## 8. Two things recorded so a later session does not rediscover them

**KNOWN LIMITATION — event accumulation (`changeOrderCount`).** It is declared `EVENT`, and an
event population **accumulates**: nothing supersedes it, and earlier periods' executed change
orders have not stopped existing, so it is **strictly neither identity nor period**. The correct
retrieval would be a third rule — a **union at or before the period, latest-per-entity**. On the
owner's ruling 1.3 that rule is **not defined**, section 4 is **not widened**, and the field
stays PERIOD as today. It is not needed today because A4.6 abstains for want of exposure rather
than for want of a count.

**RECORDED CONTRADICTION — the float pair (`totalFloat`, `consumedFloat`).**
`field_registry.py:56` calls both a progress snapshot; `field_registry.py:202` says
`schedule_update` **revises what** `time_phased_schedule` **established**, which is the same
grammar `baselineEnd` was classified identity on. Both are in the same file and neither is
subordinate. They remain **UNDETERMINED** and are retrieved as period fields. No module in
service consumes either value, so the ambiguity costs nothing today.

## 9. Incidental findings, unacted

1. **`BRIEF_CAT_LABEL` still carries the retired "Cat N" scheme** against `NAMING_AUTHORITY.md:96`
   ("No 'Cat 4' … Groups and purposes only"). Run 44 found it; Run 45 did not act on it and
   **carries it forward as unacted**, as its section 7 item 7 requires.
2. **The identity filter is enforced twice**, in `documents.py` and in `extraction_merge.py`.
   That is defensible defence in depth and was left, but it means a single-site injection proves
   nothing — recorded here because it cost this run one injection attempt.
3. **`_identity_observations_before` re-reads each earlier period's documents on every compute**,
   so a compute at period N does O(N) period reads. Correct, and negligible at four periods; a
   project with many periods would want the earlier periods' observations read from the
   `observations` store instead. Not acted on: it is a performance shape, not a defect, and
   changing the read path would put a second retrieval mechanism beside the one just proved.
4. **Ten unconsumed extraction fields** (Run 43J section 15) are still unconsumed. Unchanged.

## 10. What the next session needs, stated as a decision for the owner

1. **`totalFloat` and `consumedFloat` are still UNDETERMINED.** They cost nothing while no
   module in service consumes them. The moment one does, the contradiction at section 8 has to
   be ruled on. **Decision: rule now, or leave until a consumer appears?**
2. **The event-accumulation rule is undefined.** `changeOrderCount` is retrieved as a period
   field, which under-reports a cumulative ledger whenever a period holds no change order.
   **Decision: define the third rule, or accept the under-report and record it as the intended
   behaviour?**
3. **The four past-performance ratings rest on the weakest evidence in the classification.**
   Ruling 1.1 accepted that because no module consumes them. **Decision: revisit if a module
   comes to consume them — nothing else triggers a review.**
4. **`BRIEF_CAT_LABEL`** (section 9 item 1) is a one-line naming fix carried forward unacted
   since Run 44. **Decision: schedule it, or leave it.**
