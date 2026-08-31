# Retired module specifications — B4

Run 91. This file holds the specifications of modules in category B4 that have been RETIRED
from service. It exists so the history can still be read.

ARCHIVING IS NOT DELETION, and that is Run 43D's ruling applied to the written record rather than
to the registry. A retired module keeps its identifier — `registry.retired_modules()` still lists
it and every reference to it still resolves — and it now keeps its specification too. The live
specification for this category keeps ONE LINE per retired module, recording that it was retired
and pointing here. Nothing else about the module's specification is changed: the sections below are
the text as it stood in the live specification, moved verbatim.

THERE WAS NO ARCHIVE CONVENTION IN `specifications/` TO FOLLOW. Before this run the directory held
the eleven category specifications, `RATING_WORD_SCALES.md` and `README.md`, and nothing archived,
retired or deprecated anywhere in it. The convention used here is the directory's OWN convention,
one file per category, mirrored under `archive/` with the same filename. That is invented, and it
is said plainly rather than presented as precedent.

A1'S PRECEDENT WENT THE OTHER WAY AND IS NOT FOLLOWED. `A1_cost_and_evm.md` records that A1.1
Monte Carlo EAC Forecast was retired at Run 43 and states that "A1.1 is deliberately absent from
this document". Its section was DELETED, not archived, and this run does not attempt to
reconstruct it — a reconstruction would be a composition, not a record.

## B4.4 — What-If Scenario Matrix — RETIRED at Run 89, not in service

**Identity.** Live id `B4.4`. Method class `WhatIf_Scenario_Matrix`. Candidate actions compared
across scenarios.

**Required inputs.** `actionScenarioMatrix` — a mapping, and the only input read. It must carry the
**actions** being compared (each with an identity), the **scenarios** they are compared under, an
outcome for **every** action-scenario pair, the declared `orientation`, the `units` and the
`model_version`. Optionally, scenario probabilities.

**Method — a comparison, not a choice.**
```
rows    = candidate ACTIONS
columns = SCENARIOS
cells   = the declared outcome for each (action, scenario) pair
matrix[a][s] = cell(a, s)          for every action a and every scenario s
```
Where — and **only** where — the governed structure states scenario probabilities:
```
ExpectedValue(a) = sum over s of  cell(a, s) * P(s)
```
Otherwise `expected_values` is `null`. **No probability is invented, so no expected value is
computed unless the governed structure states the probabilities.**

**Bands.** **None**, and the authority boundary above applies in full.

**The refusal to choose, and it is on the result.** `recommended_action` is **always `None`**, and
the result carries `recommendation_reason` verbatim: *"this measure compares alternatives under
scenarios and applies no decision rule; it names no action"*. The evidence sentence says the same
thing: *"N actions are compared across M scenarios; this measure applies no decision rule and names
no action."* **A specification applying this module must not name a preferred action, must not rank
the actions, and must not describe any action as best, safest or recommended.** Applying a decision
rule to this same matrix is a different module's work, and a human authorises the selection.

**Interpretation.** The matrix says what each action is expected to produce under each scenario, in
the declared units and the declared orientation. It is the material for a decision; it is not the
decision.

**Nothing to report.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed
   action-by-scenario matrix: the actions being compared, the scenarios they are compared under,
   and an outcome for every pair"*.
2. No actions or no scenarios recorded: `"Awaiting a governed action-by-scenario matrix: the
   actions being compared, the scenarios they are compared under, and an outcome for every pair.
   No entries are recorded, so there is nothing to solve and no figure is produced in place of
   one."`
3. **An action without an identity refuses**, in the words `canonical_v7` raises for it. Several
   forecast formulas with no action identity are not a what-if matrix, which is why that case is a
   refusal rather than a default naming.
4. A missing cell: the matrix must be complete, and an incomplete one refuses in the words
   `canonical_v7` raises for the missing pair.

---

