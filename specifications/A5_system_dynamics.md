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
calibration-pending with the standard note verbatim: *"The
method this measure is named for has been carried out and the figure is reported. No status colour
is offered with it, because no boundary for this quantity has been established from evidence, and a
colour drawn from an unestablished boundary would read as a judgement nobody has made."*

**No band may be attached to any module in this category.**

## The abstention sentences all seven specified here share

All seven specified here take their structure through `canonical_v4.require_v4_structure`. Writing `W` for the
module's own plain-words description:

- **Absent:** `"Awaiting W. This measure is named for a method that cannot be carried out without
  it, so no reading is reported and no other figure is used in its place."`
- **Present but not a mapping:** `"The information provided for this project in place of W is not
  in a form this measure can read, so no reading is taken from it."`

---

## A5.1 — DSM Rework Propagation — RETIRED at Run 89, not in service

**Identity.** Live id `A5.1`. Method class `DSM_Rework_Cat5`. How rework started in one part of the
design spreads to the rest of it through the dependencies between them.

**Required inputs.** `dsmDependencyModel` — a mapping, and the only input read. It must carry named
nodes, a directed dependency matrix `D`, a **declared matrix orientation**, edge strengths, a seed
rework vector, and a stopping or cycle policy.

**Method.**
```
R(k+1) = D * R(k)          under the declared orientation
```
Oracle from the source: with `D = [[0, 0.5], [0, 0]]` and `R0 = [0, 1]`, then `R1 = [0.5, 0]` and
`R2 = [0, 0]`. The module reports the propagated rework per node, the number of waves, the most
affected node (ties broken by node name), the total propagated rework, and **why the propagation
stopped** — either `CONVERGED` or having reached the step limit the model declares.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.
**No ladder was ever drawn over propagated rework** and inventing one is a decision to be made from
evidence, not here.

**Interpretation.** The reading says which part of the design absorbs the most consequence when
rework starts somewhere else. It is a property of the *topology*, so it identifies structural
fragility that no schedule or cost figure would show.

**Nothing to report.** The two sentences above, with `W` = *"a dependency matrix for the design: the parts
of the design, which of them depend on which others and how strongly, and the rework the
propagation starts from"*.

**What it is waiting for, stated plainly.** A governed design structure matrix. **`cpi` and `spi`
may not be substituted for dependency topology** and are not read. Before Run 7 this module held
nine coefficients and an initiating wave as literals: handed an empty dictionary it read Amber, and
handed a complete project it read the same Amber, because nothing about a project could reach the
arithmetic.

---

## A5.2 — Sensitivity Analysis

**Identity.** Live id `A5.2`. Method class `Sensitivity_Analysis`. A declared response recomputed
with each declared input moved.

**Required inputs.** `sensitivityModel` — a mapping, and the only input read. It must carry a
**named response function**, its version, the **base state** it is evaluated at, and the inputs to
be moved with the range each is moved across.

**Method.** For each declared input `Xi`, perturb it from the base point by its declared fraction
and **recompute the response**:
```
S_i = (dY / Y) / (dXi / Xi)
```
Oracle from the source: with `Y = x1^2 + x2` at `x1 = 2, x2 = 1` the response is 5; raising `x1` by
ten per cent gives 5.84, so the normalised sensitivity is `(0.84/5) / (0.2/2) = 1.68`. The reported
headline is the input with the largest absolute normalised sensitivity, ties broken by input
identifier.

**The method scope is declared and must be repeated.** This is a **local, one-at-a-time**
sensitivity. The result carries `method_scope` and the evidence sentence states in words *"This is
a local one at a time sensitivity and is not a global one."* A specification applying this module
repeats that and never describes the result as global.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.

**Interpretation.** A normalised sensitivity of 1.68 says a one per cent move in that input moves
the response by 1.68 per cent, at this base point. **Ranking currently bad variables is not
sensitivity**: the model must perturb the input and recompute the response, which is what makes
this a statement about the model's structure rather than about the project's present condition.

**Nothing to report.** The two sentences above, with `W` = *"a sensitivity model: a named response
function, the state it is evaluated at, and the inputs to be moved with the range each is moved
across"*.

**What it is waiting for, stated plainly.** A declared response function with a declared base state
and declared input ranges. Before Run 29 this module perturbed `cpi` by 0.05 either way and
recomputed `bac / cpi` — a genuine elasticity, but of one hard-coded response to one hard-coded
input, with no way for a project to name the inputs it wanted moved. **None of `cpi`, `spi` or
`docRiskScore` is read here.**

---

## A5.4 — Scenario Modeling

**Identity.** Live id `A5.4`. Method class `Scenario_Modeling`. Named, internally coherent
multi-variable states, each evaluated through one governed response model.

**Required inputs.** `scenarioSet` — a mapping, and the only input read. It must carry, per
scenario, an identity and version, a **rationale**, every input it changes **jointly**, and the
consistency constraints; and for the set as a whole, one governed response model and its version.

**Method.**
```
X(s) = { x1(s), ..., xp(s) }        the scenario's jointly changed inputs
Y(s) = f( X(s) )                    evaluated through the governed response model
```
Oracle from the source: with `Y = 2*x1 + x2`, the three states BASE (2, 1), ADVERSE (3, 2) and
RECOVERY (1.5, 1) give 5, 8 and 4 exactly. The module reports every scenario's response and the
minimum and maximum across them.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.

**Interpretation.** The reading is the range the response takes across coherent states of the
world. **No state is recommended over any other**, and the module's own evidence sentence says so:
*"No state is recommended over any other, because choosing between them is a different question."*

**Nothing to report.** The two sentences above, with `W` = *"a scenario set: named scenarios, each stating
every input it changes together, the reasoning behind it, and the response model they are all
evaluated through"*.

**One property a reader must be told.** **This is not a decision method.** The question here is
*what happens under this condition*, not *which intervention to choose*; the latter belongs to B4.
Before Run 29 this module read an actions-by-scenarios payoff matrix and returned a recommended
action and its expected cost — a decision output that the module's own contract names as the
confusion to avoid. The decision structure is no longer this module's defining structure and the
recommendation is no longer its output. **A specification applying this module must not recommend
a scenario.**

---

## A5.5 — Rework Feedback Loop — RETIRED at Run 89, not in service

**Identity.** Live id `A5.5`. Method class `Rework_Feedback`. A genuine time-dependent stock and
flow model of work coming back.

**Required inputs.** `systemDynamicsModel` — a mapping, and the only input read. It must carry the
stock of work in the backlog, the work arriving and completed each step, and the share of completed
work that returns as rework.

**Method.**
```
Backlog(t+1)       = Backlog(t) + NewWork(t) + ReworkGenerated(t) - WorkCompleted(t)
ReworkGenerated(t) = ErrorRate(t) * WorkCompleted(t)
```
Oracle from the source: `Backlog0 = 10`, `NewWork = 5`, `WorkCompleted = 8`, `ErrorRate = 0.25`
gives `ReworkGenerated = 2` and `Backlog1 = 9`. The module reports the initial and final backlog,
the number of steps run, the full per-step trace, the totals of new work, completed work and rework
generated, the rework share of completed work, and an **accounting residual** so a reader can check
the stock balanced.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.

**Interpretation.** A backlog that rises while work is being completed is the signature of a
feedback loop: the project is generating work faster than it clears it, and the rework share says
how much of that is self-inflicted.

**Nothing to report.** The two sentences above, with `W` = *"a system dynamics rework model: the stock of
work in the backlog, the work arriving and completed each step, and the share of completed work
that returns as rework"*.

**What it is waiting for, stated plainly.** A stock-and-flow model with a time step. **A weighted
CPI/RFI/change-order score is not a feedback loop.** Before Run 29 this module computed exactly
that: a capped request count at 0.3, a capped change order count at 0.3 and the shortfall of the
cost index at 0.4 — no stock, no flow, no time and no feedback. **None of those three inputs is
read here.**

---

## A5.6 — Queueing Theory Bottleneck

**Identity.** Live id `A5.6`. Method class `Queueing_Bottleneck`. A genuine queue model: an arrival
rate, a service rate, servers and a discipline.

**Required inputs.** `queueModel` — a mapping, and the only input read. It must carry the rate work
arrives at, the rate it is served at, how many servers there are and the order they take work in.

**Method.**
```
rho = lambda / mu
L   = rho / (1 - rho)
W   = 1 / (mu - lambda)
Lq  = rho^2 / (1 - rho)
Wq  = rho / (mu - lambda)
```
Oracle from the source: with `lambda = 2` and `mu = 3`, `rho = 2/3`, `L = 2`, `W = 1`, `Lq = 4/3`,
`Wq = 2/3`, and Little's Law holds. Where several queues are supplied the module reports the
**busiest** as the bottleneck, with every queue's figures beside it and a declared `stability`.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.

**Interpretation.** Utilisation approaching 1 is the finding: queueing time rises without bound as
`rho` approaches 1, so a queue at 0.95 of capacity is a qualitatively different place from one at
0.7, and no linear reading of "95 per cent busy" conveys that.

**Nothing to report.** The two sentences above, with `W` = *"a queue model: the rate work arrives at, the
rate it is served at, how many servers there are and the order they take work in"*.

**The instability rule, and it is a refusal.** **If `lambda >= mu`, do not emit a reassuring
steady-state result.** There is no steady state to report and a colour would imply there is. Before
Run 29 an unstable queue was banded Red; it is now refused. A specification applying this module
must not compute `L`, `W`, `Lq` or `Wq` on an unstable queue, and must not present the algebraic
values those formulas would produce.

**What it is waiting for, stated plainly.** An arrival process and a service process.
`ActivitiesConstrained / ActivitiesPlanned` is not queueing theory. A **queue observation log** —
entities, a horizon and measured waiting times — is also not enough: that yields a measured
occupancy, with no arrival process, no service process and no stability condition in it.

---

## A5.7 — Agent-Based Supply Chain

**Identity.** Live id `A5.7`. Method class `Agent_Supply_Chain`. Agents, states, behaviour rules,
interaction rules, an environment and time — **actually stepped**.

**Required inputs.** `agentSupplyChainModel` — a mapping, and the only input read. It must carry
the agents, the state each starts in, the rule each follows, who they are connected to, and the
steps the model runs over. All six elements are required: a true agent-based model needs agents,
states, behaviour rules, interaction rules, an environment and time.

**Method — a simulation.** The agents are stepped in a declared `step_order` over the declared
number of time steps, each following its declared rule. The minimum deterministic laboratory model
the contract states is: a supplier that ships one unit when it has stock and a request is pending;
a carrier that collects a shipped unit and delivers it after a declared travel delay; and a project
with demand, received quantity and backorder. The module reports the demand, the quantity received
and the quantity backordered at the end of the run, with the agents, rules, environment and step
order that produced them.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.

**Interpretation.** The reading says what the supply chain, following its own declared rules,
actually delivered against what was asked for. The backorder is the finding; the rules are the
explanation.

**Nothing to report.** The two sentences above, with `W` = *"an agent based supply chain model: the
agents, the state each starts in, the rule each follows, who they are connected to, and the steps
the model runs over"*.

**What it is waiting for, stated plainly.** Executable rules. A long-lead at-risk ratio is not an
agent-based model. Before Run 29 this module read a supplied state history and counted how many
agents were in a state other than normal at the last step: the decision rules were required to be
**named** but were never **executed**, so the states came out exactly as they were typed in. **That
is a table read, not a simulation.**

**One property a reader must be told, and it bears on reproducibility.** The model may be declared
stochastic. Where it is, the result carries `stochastic: true`, the `seed` and the number of
`replications`, and the evidence sentence gains the clause *"The run is stochastic and was repeated
N times from seed S."* The module is nonetheless **absent from `models.STOCHASTIC`**, which names
only `{"A1.1", "A1.2", "A2.1"}`, so a stochastic run here does not receive the result set's seed
record; the seed travels on the reading instead. **A specification applying this module cannot
reproduce a stochastic run and must report the platform's figures, not a re-simulation.**

---

## A5.8 — Discrete Event Simulation

**Identity.** Live id `A5.8`. Method class `Discrete_Event_Sim`. A real discrete event simulation:
entities, events, a clock, resources, queues and routing.

**Required inputs.** `desProcessModel` — a mapping, and the only input read. It must carry the
entities and when they arrive, the resources that serve them, how long service takes, and the order
simultaneous events are taken in.

**Method — a simulation with an explicit event-order policy.** Entities are advanced through the
resource according to the declared queue discipline, with a declared `event_order_policy` for
simultaneous events and a declared `termination_condition`. Oracle from the source: with one
server, job A arriving at 0 with a service of 2 and job B arriving at 1 with a service of 2 — A
starts at 0 and ends at 2 having waited 0; B starts at 2 and ends at 4 having waited 1; **the mean
wait is 0.5**. The module reports the mean wait, the clock end, every entity and every event.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.

**Interpretation.** The mean wait is time the work spent existing but not being worked on. Unlike a
queueing formula it comes from a specific arrival pattern rather than from a steady state, so it
answers what happened to *these* entities in *this* order.

**Nothing to report.** The two sentences above, with `W` = *"a discrete event model: the entities and when
they arrive, the resources that serve them, how long service takes, and the order simultaneous
events are taken in"*.

**What it is waiting for, stated plainly.** An event stream. **A progress or schedule index
algebraic index is not DES.** Before Run 29 this module formed an interruption term from the
progress shortfall and the schedule index shortfall and reported the reciprocal of one plus it as a
throughput index; Run 27 proved it a function of the schedule index and the progress ratio alone.
There is no entity, no event, no clock, no resource and no queue in that, and **none of its inputs
is read here.**

**One property a reader must be told.** As with A5.7, the model may be declared stochastic, the
seed and replication count travel on the reading, and the module is absent from `models.STOCHASTIC`.
The same reproducibility caution applies.

---

## Stopped specifications

None. All five modules in service in this category have unambiguous sources and are specified
above, as are the two retired at Run 89.

## What this category is collectively waiting for

Five governed structures for the modules in service, none of which any supported document type
carries: `sensitivityModel`, `scenarioSet`, `queueModel`, `agentSupplyChainModel`,
`desProcessModel`. (`dsmDependencyModel` and `systemDynamicsModel` were the structures A5.1 and
A5.5 waited for; both modules were retired at Run 89 for waiting on them.) Every one of them is a **model of relationships**
rather than a set of reported figures, and none can be extracted from a monthly report, a cost
report, a schedule export or a register. Lighting this category is a question of supplying models,
not of improving extraction.
