# Category B4 — Decision Optimisation

**Two modules are in service: B4.3 Constraint Satisfaction Analysis and B4.4 What-If Scenario
Matrix.** The category declares seven identities; five are not in service and are not specified
here.

## The authority boundary, and it is the point of this category

Every row either module emits — **computed or abstaining** — carries these fields, set by
`models_cat10._route` and **re-asserted after the canonical result merges in**, so that no
canonical payload can introduce a band or claim an authority by overwriting them:

```
result_class                = "ANALYTICAL_RESULT"
human_authorization_required = True
creates_project_evidence     = False
status_color                 = None
band_asserted                = False
calibration_pending          = True
authority_note               = (verbatim)
  "This is an analytical result. It does not approve, authorise, execute or lock any action,
   and it does not exercise the judgment of the responsible reviewer. Final selection remains
   human-authorised."
```

**An abstention carries the boundary too.** A reader who sees only "no result" still needs the row
to say that this measure could not have approved anything even if it had produced a number.

**A decision recommendation is not an observation about the project.** It must not enter fusion, it
must not become new project-condition evidence, and it must not read as an approval. **Neither
module in this category has a band and neither may be given one.**

## Two prohibitions that hold across the category

1. **Nothing in these routes reads `cpi`, `spi` or `docRiskScore`.** Those three fields are
   precisely what the earlier Category-10 implementations blended into an "optimization" score, and
   a route that cannot see them cannot rebuild one.
2. **There is no corpus-assembly fallback.** A decision problem is a statement of what the owner is
   choosing between; the controlled corpus holds no candidate action set, so assembling one would
   be inventing the alternatives. Inventing the parameters is forbidden and **inventing the
   alternatives themselves would be worse.**

## The shared abstention sentences

From `canonical_v7.v7_structure`, writing `W` for the module's plain-words structure description:

- **Absent:** `"Awaiting W. This measure is named for a method that cannot be carried out without
  it, so no reading is reported and no other figure is used in its place."`
- **Present but not a mapping:** `"The information provided for this project in place of W is not
  in a form this measure can read, so no reading is taken from it."`

Every abstention here carries the decision-structure reason code
`canonical_decision_structure_absent`, not the generic structure code, because every module in this
category is a decision method by definition.

---

## B4.3 — Constraint Satisfaction Analysis

**Identity.** Live id `B4.3`. Method class `Constraint_Satisfaction`. Which complete assignments of
the declared variables satisfy every declared constraint.

**Required inputs.** `constraintSatisfactionProblem` — a mapping, and the only input read. It must
carry a `variables` list, each with a `variable_id` and a non-empty `domain`, and a `constraints`
list of governed rules each with a `constraint_id`.

**Method — exhaustive enumeration.**
```
for every combination in the Cartesian product of the variables' domains:
    assignment = that complete assignment of every variable
    failed     = [ constraint_id for every constraint that does not hold on the assignment ]
    failed empty  -> feasible
    otherwise     -> infeasible, recording which constraints it violated
satisfiable = at least one feasible assignment exists
```
**A solution assigns EVERY variable while satisfying EVERY applicable constraint.** Every rule is
evaluated against every complete assignment; **no rule may be skipped.** Constraints are declared
as governed rules, including the implication form. The result reports the variables, their domains,
the constraint ids, the number of assignments examined, and both the feasible and infeasible sets
with their violations.

**Bands.** **None**, and the authority boundary above applies in full.

**Interpretation.** The reading says how many of the ways the project could set its declared
variables actually survive its declared constraints — and, for each that does not, exactly which
constraint killed it. The infeasible set with its violations is usually the more useful half:
it names the binding constraint.

**Abstention.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed
   constraint-satisfaction problem: variables, their domains, and the constraints over them"*.
2. No variables: `"Awaiting a governed constraint-satisfaction problem: variables, their domains,
   and the constraints over them. No entries are recorded, so there is nothing to solve and no
   figure is produced in place of one."`
3. A variable with no identity: `"A variable in the a governed constraint-satisfaction problem:
   variables, their domains, and the constraints over them provided has no identity."`
4. A variable with no domain: `"Variable <id> in the a governed constraint-satisfaction problem:
   variables, their domains, and the constraints over them provided for this project has no domain,
   so there is nothing for it to be assigned from."`
5. A variable named twice: `"The a governed constraint-satisfaction problem: variables, their
   domains, and the constraints over them provided names variable <id> twice."`
6. No constraints: `"The a governed constraint-satisfaction problem: variables, their domains, and
   the constraints over them provided for this project declares no constraints, so every assignment
   would be a solution and there is no satisfaction problem to analyse."`

**One property a reader must be told.** **A fixed-threshold checklist is not a constraint
satisfaction problem** and is not preserved under this route: a checklist has no variables and no
domains, so there is nothing to assign.

---

## B4.4 — What-If Scenario Matrix

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

**Abstention.**
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

## Stopped specifications

None. Both modules in service in this category have unambiguous sources and are specified above.
