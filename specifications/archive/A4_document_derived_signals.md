# Retired module specifications — A4

Run 95. This file holds the specifications of modules in category A4 that have been RETIRED
from service. It exists so the history can still be read.

ARCHIVING IS NOT DELETION, and that is Run 43D's ruling applied to the written record rather than
to the registry. A retired module keeps its identifier — `registry.retired_modules()` still lists
it and every reference to it still resolves — and it keeps its specification too. The live
specification for this category keeps ONE LINE per retired module, recording that it was retired
and pointing here. Nothing else about the module's specification is changed: the sections below are
the text as it stood in the live specification, moved verbatim.

THE CONVENTION IS RUN 91'S, NOT A NEW ONE. Run 91 established `specifications/archive/<file>.md`,
mirroring the live filename. This run follows it exactly and invents nothing.

A4.1 IS NOT A SPECIFICATION. It never had one. What is archived below is the STOPPED note that
stood under "Stopped specifications" in the live file, moved verbatim. It is kept because it
records why no method was ever written, and because it states a contradiction — a module in
service that neither computed nor abstained — that the Run 95 retirement resolves. Its text
describes the state before this run and is not corrected here; correcting it would make it a
composition rather than a record.

## A4.10 — Specification Conflict Density — RETIRED at Run 95, not in service

**Identity.** Live id `A4.10`. Method class `Spec_Conflict_Density`. Verified specification
conflicts per unit of declared specification exposure.

**Required inputs.** `specificationConflictRegister` — a mapping, and the only input read.

**Method.** `canonical_v4.specification_conflict_density`:
```
conflict_density        = verified conflicts / exposure quantity
conflicts_per_thousand  = conflict_density * 1000
```
Five verified conflicts over two hundred and fifty requirements reads 0.02 conflicts a
requirement, or twenty per thousand. The exposure must be explicit and is reported with its unit.
Each conflict retains the two places in the specification that disagree. **Candidate conflicts
that have not been confirmed are reported separately and are not counted in the density.**

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. What it replaced was `docRiskScore * rfiCount / sqrt(rfiCount)`, capped at
one and banded — the expression the supplied contract names as not being this method. **Neither
`docRiskScore` nor `rfiCount` is read here.**

**Interpretation.** The density says how internally contradictory the issued specification is per
unit of the specification. It is the upstream cause of much of what A4.2 measures downstream as
request velocity, and the two are reported separately so the causal reading stays available rather
than being asserted.

**Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a specification conflict
register: each identified conflict, the two places in the specification that disagree, whether it
has been confirmed, and the exposure the conflicts are counted over"*.

---

### A4.1 — Document Risk Score. STOPPED. Not specified. — RETIRED at Run 95, not in service

A4.1 is **in service** — `registry.service_index()` contains it — and is **not implemented**:
`registry.unported_modules()` returns exactly `['A4.1']`, and `registry.run_module("A4.1", ...)`
raises `MissingModuleError` with the words *"A4.1 (Document Risk Score) has not been ported and
validated against the JavaScript implementation; this server refuses to compute it"*.

`canonical_v4` declares a structure key for it — `documentRiskEvidence` — and plain words for that
structure, so the intent to implement it is recorded. **No runner exists.** There is therefore no
source from which to derive a method, and writing one would be inventing a method this module
never had, which section 3.1 of this run's order forbids.

**The contradiction, stated:** a module that is in service must either compute or abstain, and
A4.1 does neither — it raises. Nothing in this run changes that; a specification cannot be
written for it until a runner exists, and applying a specification to it now would make the model
produce a reading the platform itself refuses to produce.
