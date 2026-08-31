# Retired module specifications — A2

Run 95. This file holds the specifications of modules in category A2 that have been RETIRED
from service. It exists so the history can still be read.

ARCHIVING IS NOT DELETION, and that is Run 43D's ruling applied to the written record rather than
to the registry. A retired module keeps its identifier — `registry.retired_modules()` still lists
it and every reference to it still resolves — and it keeps its specification too. The live
specification for this category keeps ONE LINE per retired module, recording that it was retired
and pointing here. Nothing else about the module's specification is changed: the sections below are
the text as it stood in the live specification, moved verbatim.

THE CONVENTION IS RUN 91'S, NOT A NEW ONE. Run 91 established `specifications/archive/<file>.md`,
mirroring the live filename, for `A5_system_dynamics.md` and `B4_decision_optimisation.md`. This
run follows it exactly and invents nothing.

A1'S PRECEDENT WENT THE OTHER WAY AND IS NOT FOLLOWED. `A1_cost_and_evm.md` records that A1.1
Monte Carlo EAC Forecast was retired at Run 43 and states that "A1.1 is deliberately absent from
this document". Its section was DELETED, not archived, and this run does not attempt to
reconstruct it — a reconstruction would be a composition, not a record.

## A2.2 — Line of Balance — RETIRED at Run 95, not in service

**Identity.** Live id `A2.2`. Method class `Line_of_Balance_Velocity`. Repetitive,
location-based production: whether the crews following are catching the crews leading.

**Required inputs.** `lobStructure` — a mapping, and the only input read. It must carry the
locations in sequence, the crews working them, and for each line of work the activity, the location
or unit, the quantity, the crew, the **planned** production rate, the **actual** production rate,
and the sequence.

**Method.**
```
rate                    = change in units / change in time
minimum_separation_days = the smallest gap in time between the leading and the following line
                          across all locations
```
A line of work is **deteriorating** when its actual production rate is below its planned rate. Both
slopes are reported per line of work, and the count of deteriorating lines is reported.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. The minimum separation is the quantity the module's old boundaries were
drawn over and it is still computed; the production-rate ratio the module now also reports has no
established boundary in this platform. No colour is asserted on either.

**Interpretation.** The minimum separation is the buffer between trades: when it reaches zero the
following crew is standing on the leading crew and production stops. The planned-against-actual
slopes say whether that buffer is closing because of the crew ahead or the crew behind — a
distinction the module could not make before Run 28, when only actual rates were read and a crew
running at half its planned rate was indistinguishable from one running exactly to plan.

**Nothing to report.** The two sentences above, with `W` = *"a line of balance: locations in sequence, the
crews working them, and a production rate and start for each line of work"*.

---

## A2.3 — CCPM Buffer Health — RETIRED at Run 95, not in service

**Identity.** Live id `A2.3`. Method class `CCPM_Buffer_Health`. How much of the project buffer has
been eaten, against how much of the critical chain has been completed.

**Required inputs.** `ccpmStructure` — a mapping, and the only input read. It must carry the
critical chain with its activities and a **sized** project buffer. **A buffer derived from a
performance index is not a sized buffer** and no such derivation is performed here.

**Method.**
```
BC  = B0 - Bt                       buffer consumed, in days
BCR = (B0 - Bt) / B0                buffer consumption ratio
```
reported alongside the percentage of the chain complete and the percentage of the buffer consumed,
the feeding buffer count and the chain activity count.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note.

**The two policy lines, and why they are not bands.** The module computes and reports two
positions on the fever chart:
```
amber_policy_line = pct_chain_complete
red_policy_line   = pct_chain_complete + (100 - pct_chain_complete) / 3
```
and a `zone_relative_to_policy_lines` which takes exactly one of three values —
`"beyond the red policy line"`, `"beyond the amber policy line"`, `"inside both policy lines"`. The
module carries its own note on them verbatim: *"the amber line is chain completion, which is
definitional; the red line adds a third of the chain remaining, which is a policy choice no source
in this repository establishes"*. **These are reported as policy positions and must never be
emitted as `band`.** A specification applying this module reports the zone in the evidence
sentence, with `band: null` and `band_asserted: false`.

**Interpretation.** Buffer consumption ahead of chain completion means the project is spending its
protection faster than it is earning it. The zone says where that sits relative to two lines the
project's own policy drew, one of which is definitional and one of which is a choice.

**Nothing to report.** The two sentences above, with `W` = *"a critical chain with its activities and a
sized project buffer"*.

---

