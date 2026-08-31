# Retired module specifications — A5

Run 91. This file holds the specifications of modules in category A5 that have been RETIRED
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

