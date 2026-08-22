# Field Classification Decisions

Created by Run 45 on 2026-08-22. No file of this name existed before this run, so nothing is
superseded and nothing is amended. The owner's ruling of 2026-08-22 on the Run 45 section 5.1
proposal is the sole authority for what is recorded here.

**This is the canonical classification. It was decided ONCE, signed off BEFORE any code
changed, and it is recorded here so that a later session does not re-derive it.**

The proposal it rules on, with the declaration each kind was read off quoted per field, is
`code_audit/run45_field_classification_proposal.md`. The implementation is
`server/app/field_registry.py` (`IDENTITY_FIELDS`, `PERIOD_FIELDS`, `UNDETERMINED_FIELDS`,
`retrieval_kind`), asserted at import to partition `FIELD_KINDS` exactly.

Implementing commits:

| Decision | Commit |
|---|---|
| The classification proposal, stopped for sign-off | `38328c7` |
| Retrieval by kind, `sim-2026.08-v30` | `6e60875` |
| This decision record and the run report | the final commit on `run45-classification` |

---

## 1. The two kinds

| kind | meaning | retrieval |
|---|---|---|
| **IDENTITY** | a fact about the project that holds until superseded | the latest value **at or before** the period being computed, declared document-type precedence (`WRITER_TIERS`) holding **across** the carry-forward |
| **PERIOD** | a fact about one reporting period | the period's own documents and nothing else. **Unchanged from before Run 45.** Absent in its period means absent |

Supersession inside the identity class follows **document date and declared precedence**, never
upload timestamp, filename or insertion order. Carried observations go through the same
`_snap_pick` / `_perm_pick` Run 42 proved order independent; neither key has a period term.

## 2. The counts, and the seventy-seventh field

| kind | count |
|---|---|
| IDENTITY | 13 |
| PERIOD | **62** |
| UNDETERMINED | 2 |
| **total emittable (`FIELD_KINDS`)** | **77** |

**The arithmetic closes at 13 + 62 + 2 = 77, and it is asserted at import.** The owner's ruling
1.5 states "identity 13, period 61, undetermined 2 = 76" and asks for the seventy-seventh to be
confirmed or the difference explained. **The difference is in the period count: it is 62, not
61.** The derivation: the section 5.1 proposal classified 12 identity, 60 period and left 5
undetermined (12 + 60 + 5 = 77). Ruling 1.2 moved `originalContingency` to identity (13) and
`remainingContingency` to period (61); ruling 1.3 moved `changeOrderCount` to period (**62**);
ruling 1.4 left `totalFloat` and `consumedFloat` undetermined (2). Nothing is missing and no
field is unaccounted for — the period count simply gains two fields from the ruled set, not one.

## 3. The thirteen identity fields

`bac`, `baselineContractSum`, `baselineEnd`, `baselineStart`, `revisedContractSum`,
`originalContingency`, `analogousBac`, `analogousFinalCost`, `analogousOverrunPct`,
`overallRating`, `scheduleRating`, `costRating`, `qualityRating`.

Ruling 1.1 approved the twelve proposed, **including the four past-performance ratings** despite
their lower evidential weight: they are consumed by no module in service, so a misclassification
costs display and provenance only, never a computed result. **Revisit only if a module comes to
consume them.**

## 4. Ruling 1.2 — the contingency pair is SPLIT

`originalContingency` is **identity**: the original contingency is established at baseline and
holds until a document revises it; it cannot meaningfully differ per period.
`remainingContingency` is **period**: what remains is exactly a per-period fact.

On the conflicting evidence: `field_registry.py:56` groups both as snapshots, and
`models_ext.py:538-540` says the amount "has not been reported for this period". **The `:56`
grouping is the weaker evidence, because it groups by document section rather than by meaning.**
The `:538-540` sentence describes `remainingContingency`'s per-period character and is consistent
with this ruling.

This is what A3.2 requires: contingency burn is a stable original measured against a per-period
remaining. It is the one ruling that changes a computed result, and it does.

## 5. Ruling 1.3 — `changeOrderCount` stays PERIOD. KNOWN LIMITATION.

**Recorded so a later session finds it rather than rediscovering it.** An EVENT-declared field
**accumulates** and is strictly neither kind: nothing supersedes the population, and earlier
periods' executed change orders have not stopped existing. The correct retrieval would be a
third rule — a **union at or before the period with latest-per-entity**.

**That rule is not defined, section 4 of the Run 45 order is not widened, and it is not needed
today**, because A4.6 abstains for want of exposure rather than for want of a count, which Run
43J already classified D and correct.

## 6. Ruling 1.4 — `totalFloat` and `consumedFloat` stay UNDETERMINED. CONTRADICTION RECORDED.

**Recorded so it is not rediscovered.** `field_registry.py:56` calls both a progress snapshot,
while `field_registry.py:202` says `schedule_update` **revises what** `time_phased_schedule`
**established** — which is the same grammar `baselineEnd` was classified identity on. Both
declarations are in the same file and neither is subordinate to the other.

No module in service consumes either value, so the ambiguity costs nothing today. They are
retrieved as period fields, which is the unchanged behaviour. Stop condition 9.1 is discharged
for them by the owner's ruling; it remains **live** for any further field whose kind the sweep
cannot determine and which the owner has not ruled on.

## 7. What the classification is NOT

A kind was never read off what the implementation happened to do, and never off what would make
a module compute. Every kind rests on a declaration quoted with file and line in the proposal.
`_period_documents` scoping every field to its upload period was the defect under repair, and is
evidence of nothing about any field's kind.
