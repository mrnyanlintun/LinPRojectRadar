# Run 39 dataset classification contract

**Status:** operational provenance. This contract governs which dataset an observation belongs
to. It does **not** touch the frozen analytical semantics: no scientific formula, no analysis
variable definition, no export column, no categorical level and no derivation rule is changed by
it.

---

## 1. The three governed classes

The vocabulary is **closed**. A value that fits none of these is a governance error, not a new
class, and `run39_dataset_class.load_registry` raises rather than accepting one.

| class | meaning |
|---|---|
| `TEST_ONLY` | Synthetic dry-run/qualification data. Created by an automated run to exercise the instrument. Never a study observation. |
| `PILOT` | A bounded pilot-equivalent session used for operational qualification. **Excluded from the primary study dataset.** |
| `MAIN_STUDY` | A primary study observation, collected from a consented participant under the governed protocol. |

## 2. `UNCLASSIFIED` is the absence of a class, not a fourth class

A participant the registry does not name classifies `UNCLASSIFIED`. It is deliberately **not** a
member of the vocabulary and is never exportable as anything.

**The default is exclusion.** Forgetting to classify a participant removes them from the main
study; it can never silently add them. The opposite default would mean that the day an account is
created by accident, its rows join the primary dataset.

## 3. The authority is a registry, never a name

```
research/study_execution/dataset_class_registry.csv
study_participant_id,dataset_class,registered_on,registering_authority,note
```

`run39_dataset_class.classify()` reads this file and **nothing else**. It does not look at:

- the participant's pseudonymous code or any prefix of it;
- a display label;
- a creation date;
- any property of the observation row.

This is a deliberate departure from how Run 38 populated the frozen `record_class` column, which
**is** prefix-derived (`run38_analysis_export.TEST_ONLY_CODE_PREFIX`). That column is frozen and
Run 39 does not change it — but it is **not** the classification authority, and the launch gate
proves the two can disagree: `R39-PILOT-A` yields `record_class = "STUDY"` from the frozen
prefix rule and `PILOT` from the governed registry, and every Run-39 selection uses the registry.

Matching is **exact**, never prefix-based, so `R39-PILOT-A` and `R39-PILOT-A-2` classify
independently and can hold different classes without contaminating each other.

## 4. Where the class lives in an exported artifact

The frozen CSV's 59 columns are unchanged. The governed class is carried in the **sidecar**
`<artifact>.class.json`, which records:

- `artifact_dataset_class` — the single class of every row in the artifact;
- `classification_registry_sha256` — the exact registry bytes that produced it;
- `participants` — the study identifiers included;
- `dataset_sha256` — the artifact checksum.

An export therefore contains **exactly one** class and says which. A `PILOT` artifact and a
`MAIN_STUDY` artifact can never be confused, because they are different files with different
sidecars and different checksums.

This satisfies the specification's "dataset class **retained or provenance-linkable**" without
widening a frozen categorical vocabulary, which the hard frozen boundary forbids and which
section 21 forbids resolving by minting a successor schema.

## 5. Required non-contamination properties

Enforced by `run39_dataset_class.select()` and asserted by `test_run39_launch_gate.py`:

| required | how it holds |
|---|---|
| `TEST_ONLY → MAIN_STUDY = 0` | selection is exact-match on the registry; a TEST_ONLY registration can never satisfy `== MAIN_STUDY` |
| `PILOT → MAIN_STUDY = 0` | same mechanism |
| `MAIN_STUDY → pilot/test export = 0` | a pilot export selects `== "PILOT"`; a main-study row is never `== "PILOT"` |
| unregistered → nothing | `UNCLASSIFIED` is not an exportable class; `select()` refuses it as a target |
| relabelling cannot reclassify | the registry is keyed by identifier and read independently of any label change |

## 6. Registering a participant

Adding a row to the registry is an **explicit, auditable, reviewable act** performed by a named
authority with a date and a note. It is the moment a participant's data becomes eligible for the
primary dataset, and it is intended to be visible in version control as its own change.

Registration does **not** create, alter or validate any participant response. It records a
classification and nothing else.

## 7. What this contract cannot do

It is a **governance control over the export**, not a technical control over the database. It
determines what an export emits. It does not and cannot prevent someone holding the database
credential from writing rows directly. That separate question is answered, without claiming
immutability, in `code_audit/run39_administrative_authority_boundary.csv` and section 7 of the
Run-39 report.
