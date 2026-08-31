# Category A5 — System Dynamics and Complexity

Five modules in service: A5.2, A5.4, A5.6, A5.7, A5.8. (A5.3 Tornado Risk Ranking is
implemented but is **not in service** and is not specified here.)

**A5.1 DSM Rework Propagation and A5.5 Rework Feedback Loop were retired at Run 89**, by the note
their rows carry in the registry (`p0-baseline/module_renumbering_map.csv`), for the reason that
registry states: *the module is defined on a structure (the DSM rework matrix / the rework feedback
loop) prepared for a method rather than a thing a project document prints.* Retirement is removal
from service, not removal from existence: their identifiers still resolve and their specifications
below are kept readable, marked retired at the head of each. They are absent from the category tree
the interface renders (`assets/js/taxonomy.js`, whose A5 list begins at `a5_2`) and they are not
dispatched.

**Expect every module in this category to abstain**, and that abstention is the useful output.
Each of them needs a *relationship between things* — a dependency matrix, a response function, a
stock and flow, an arrival and service process, a set of agents and rules, an event stream — and
none of that is a figure that can be read off a document. **No supported document type carries any
of these structures.** The specification below states, per module, precisely what each is waiting
for; collectively that is the answer to "what would it take to light this category".

**All five in service are bandless**, as were the two retired. Each reports
calibration-pending with the standard note verbatim: *"The method this measure is named for has been carried out and the figure is reported. No status colour
is offered with it, because no boundary for this quantity has been established from evidence, and a
colour drawn from an unestablished boundary would read as a judgement nobody has made."*

**No band may be attached to any module in this category.**

## The abstention sentences all seven specified here share

All seven specified here take their structure through `canonical_v4.require_v4_structure`.
Writing `W` for the module's own plain-words description:

- **Absent:** `"Awaiting W. This measure is named for a method that cannot be carried out without
  it, so no reading is reported and no other figure is used in its place."`
- **Present but not a mapping:** `"The information provided for this project in place of W is not
  in a form this measure can read, so no reading is taken from it."`

---

## A5.1 — DSM Rework Propagation — RETIRED at Run 89, not in service. Its specification is archived verbatim at `specifications/archive/A5_system_dynamics.md`; the identifier still resolves and is still listed by `registry.retired_modules()`.

---

## A5.2 — Sensitivity Analysis — RETIRED at Run 95, not in service. Its specification is archived verbatim at `specifications/archive/A5_system_dynamics.md`; the identifier still resolves and is still listed by `registry.retired_modules()`.

## A5.4 — Scenario Modeling — RETIRED at Run 95, not in service. Its specification is archived verbatim at `specifications/archive/A5_system_dynamics.md`; the identifier still resolves and is still listed by `registry.retired_modules()`.

## A5.5 — Rework Feedback Loop — RETIRED at Run 89, not in service. Its specification is archived verbatim at `specifications/archive/A5_system_dynamics.md`; the identifier still resolves and is still listed by `registry.retired_modules()`.

---

## A5.6 — Queueing Theory Bottleneck — RETIRED at Run 95, not in service. Its specification is archived verbatim at `specifications/archive/A5_system_dynamics.md`; the identifier still resolves and is still listed by `registry.retired_modules()`.

## A5.7 — Agent-Based Supply Chain — RETIRED at Run 95, not in service. Its specification is archived verbatim at `specifications/archive/A5_system_dynamics.md`; the identifier still resolves and is still listed by `registry.retired_modules()`.

## A5.8 — Discrete Event Simulation — RETIRED at Run 95, not in service. Its specification is archived verbatim at `specifications/archive/A5_system_dynamics.md`; the identifier still resolves and is still listed by `registry.retired_modules()`.

## Stopped specifications

None. All five modules in service in this category have unambiguous sources and are specified
above, as are the two retired at Run 89.

## What this category is collectively waiting for

Five governed structures for the modules in service, none of which any supported document type
carries: `sensitivityModel`, `scenarioSet`, `queueModel`, `agentSupplyChainModel`,
`desProcessModel`. (`dsmDependencyModel` and `systemDynamicsModel` were the structures A5.1 and
A5.5 waited for; both modules were retired at Run 89 for waiting on them.) Every one of them is
a **model of relationships** rather than a set of reported figures, and none can be extracted from a monthly report, a cost
report, a schedule export or a register. Lighting this category is a question of supplying models,
not of improving extraction.
