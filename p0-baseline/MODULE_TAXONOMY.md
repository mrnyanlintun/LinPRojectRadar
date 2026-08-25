# Module taxonomy: four groups

**101 registered and 63 in service at 2026-08-25: the figure at a date, not a settled fact.**
The module set is not settled and no count in this file is final. `registry_index()` and
`service_index()` are the executed figures; this document carries no authority.

`module_renumbering_map.csv` in this directory is the single source of truth for module numbering
and grouping. `assets/js/categories.js` is generated from it; every other reference is updated from
it. Nothing downstream should carry a hardcoded module list.

## The four groups

Modules are grouped by what their output is **for**, not by legacy category order.

| Group | Meaning | Count |
|---|---|---|
| **A** Project Health | What condition is the project in | 53 |
| **B** Recommendation & Governance | What should be done, by whom, under what authority | 36 |
| **C** Data & Evidence Health | How trustworthy is the evidence base | 7 |
| **D** Portfolio Level | Requires 3+ projects, parked on the portfolio page | 5 |
| | **Total** | **101** |

| Group | Category | Name | Modules |
|---|---|---|---|
| A | A1 | Cost & EVM Performance | 11 |
| A | A2 | Schedule Performance | 11 |
| A | A3 | Cost Risk | 9 |
| A | A4 | Document-Derived Condition Signals | 10 |
| A | A5 | System Dynamics & Complexity | 8 |
| A | A6 | Delivery Quality Performance | 4 |
| B | B1 | Signal Synthesis | 4 |
| B | B2 | Evidence Combination | 20 |
| B | B3 | Regulatory & Authority Thresholds | 5 |
| B | B4 | Decision Optimization | 7 |
| C | C1 | Data Integrity | 7 |
| D | D1 | Portfolio Health | 5 |

## Why the count changed from 103 to 101

**The earlier figure of 103 counted two aliases twice.** It was a count of registry *entries*, not
of distinct computations. Two entries were display duplicates of a single computation each, so the
registry showed 103 rows where 101 things are computed.

### Consolidation 1: old 1.3 and old 4.1 become A4.1

Old `1.3` Document Risk Extraction and old `4.1` Document Risk Score both resolve to the same
value. The evidence is in `getModuleStatus` in `assets/js/categories.js`, where both method classes
returned the same field:

```js
case "Doc_Risk":
case "Doc_Risk_Cat4":
case "doc_risk":               return s.doc ? s.doc.status : null;
```

Neither is computed by a simulation model; both read `project.signals.doc.status`, which is
produced once by the extraction pipeline. Old `1.3` is retired; `A4.1` carries `Doc_Risk_Cat4`.

### Consolidation 2: old 3.2 and old 5.1 become A5.1

Old `3.2` DSM Rework Propagation and old `5.1` DSM Rework Propagation are the same model surfaced
under two category numbers. `getModuleStatus` states it directly:

```js
// Cat 5.1 reuses the Cat 3 DSM result under a distinct method_class.
case "DSM_Rework_Cat5":        return findSim("DSM_Rework_Propagation");
```

One `runDSM()` call produces one result; the second entry re-read it. Old `3.2` is retired; `A5.1`
carries `DSM_Rework_Cat5`.

Both retired rows appear in the CSV with `new_id = RETIRED` so the history stays legible.

## The 8.6 to 8.9 reclassification

Old `8.6` Quality Compliance Index, `8.7` Safety Performance Index, `8.8` Environmental Compliance
Rate and `8.9` Contractor Performance Score sat in Governance & Compliance. They describe how the
work is being delivered, not who must authorise a response to it, so they move into Group A as
**A6 Delivery Quality Performance** (A6.1 to A6.4).

Governance retains only what determines authority: FAR thresholds, OMB A-11, EVM reporting
thresholds and contract modification frequency, now **B3 Regulatory & Authority Thresholds**.

## Group C does not describe project condition

This is the one behavioural change in the renumbering, and it is not cosmetic.

Group C measures the **evidence base**, not the project. A project with healthy EVM recorded on a
thin document trail is a healthy project recorded on thin evidence. Folding the thinness into the
project status conflates the two, and it does so in the direction that matters most for this study:
early reporting periods have the least evidence, so every early scenario would read worse than it
is for reasons that have nothing to do with the project.

Group C modules therefore **still compute** and still render in the authoring views. They are
excluded from `getProjectFusion` and from the red-flag list only. See the PR description for the
call paths and the before/after demonstration.

`C1.3 Source Reliability Weighting` was checked specifically, because its name suggests a fusion
weight. It is not one: it emits a `status_color` thresholded from an average reliability score, and
`dstFuse(statuses)` accepts no weight argument at all. It was a status contribution and is excluded
with the rest of Group C. Its `avg_reliability` figure remains available in the module result for
authoring use.

## Compute contract unchanged

This is a display and registry renumber. Every module's `method_class`, `active`, `required` and
`sectors` are carried over byte-for-byte from the previous registry. No computation was renamed,
added or removed.
