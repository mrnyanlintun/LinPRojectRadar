# Category B4 — Decision Optimisation

**One module is in service: B4.3 Constraint Satisfaction Analysis.** The category declares seven
identities; five have never been in service and are not specified here.

**B4.4 What-If Scenario Matrix was retired at Run 89**, by the note its row carries in the registry
(`p0-baseline/module_renumbering_map.csv`), for the reason that registry states: *the module is
defined on a structure (the what-if scenario matrix) prepared for a method rather than a thing a
project document prints.* Retirement is removal from service, not removal from existence: its
identifier still resolves and its specification below is kept readable, marked retired at its head.
It is absent from the category tree the interface renders (`assets/js/taxonomy.js`, whose B4 list
holds `b4_3` alone) and it is not dispatched.

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

## The shared nothing-to-report sentences

From `canonical_v7.v7_structure`, writing `W` for the module's plain-words structure description:

- **Absent:** `"Awaiting W. This measure is named for a method that cannot be carried out without
  it, so no reading is reported and no other figure is used in its place."`
- **Present but not a mapping:** `"The information provided for this project in place of W is not
  in a form this measure can read, so no reading is taken from it."`

Every abstention from the runner itself carries the decision-structure reason code
`canonical_decision_structure_absent`, not the generic structure code, because every module in this
category is a decision method by definition. A refusal by the qualification boundary above carries
`evidence_not_qualified_for_use` instead, and the two must not be conflated.

**The runner does not repeat the qualification gate.** It does not need to: the boundary above
already wraps every entry in the dispatch table, and gating again inside the runner would put a
second copy of the rule in the tree, where two copies drift.

## The qualification boundary, and it fires BEFORE anything below

Every module in this category is wrapped, **in the dispatch table itself**, by
`qualification_boundary.install`. After that call there is no entry in `registry.VALIDATED` for a
gated module that reaches its runner without the boundary first, and `registry.run_module` looks
the runner up there — **so a consumer cannot route around it by hand-building a signal package.**

The boundary reads the project's declared Category-9 assessment from `signal_inputs` under the key
**`evidenceQualification`**, and asks it for this category's declared use: **`decision_optimization`**.

**Absence fails closed.** A package carrying no Category-9 assessment is UNASSESSED, and UNASSESSED
is ineligible. Nothing is inferred, nothing is imputed, and the consumer does not execute first and
get stamped afterwards. The refusals, in their exact words and in the order they are reached:

1. **No governed qualification requirement declared for the route** — a configuration failure:
   `"No governed qualification requirement is declared for this route, so it is not executed. An
   undeclared route is a configuration failure and is blocked rather than allowed through."`
2. **`evidenceQualification` absent** — the case a project with no declared assessment reaches:
   `"The evidence offered to this measure carries no Category-9 assessment, so it is unassessed and
   not eligible for this use. No reading is produced and no figure is used in its place."`
3. **Declared but not eligible for this use:** `"The evidence supplied for this measure has not been
   qualified for this use, so it is not read and no figure is produced in its place. "` followed by
   the qualification reasons, joined with `"; "`.

Every one of those carries the reason code `evidence_not_qualified_for_use` and is stamped
`QUALIFICATION_BOUNDARY_V18`, so a reader of the ledger can tell **a refusal by the gate** from **a
module's own abstention**.

**This is the abstention a project with no declared Category-9 assessment will actually see for
every module in this category, and it is reached before any input named below is looked at.** The
per-module abstentions specified further down are what the module says once the boundary has been
passed.


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

**Nothing to report.**
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

## B4.4 — What-If Scenario Matrix — RETIRED at Run 89, not in service. Its specification is archived verbatim at `specifications/archive/B4_decision_optimisation.md`; the identifier still resolves and is still listed by `registry.retired_modules()`.

---

## Stopped specifications

None. The one module in service in this category has unambiguous sources and is specified above,
as is the module retired at Run 89.
