# Category B2 — Evidence Combination

**One module is in service: B2.18 MARCOS Ranking.** The category's registry declares twenty
identities, B2.1 through B2.20; nineteen of them are not in service and are not specified here.

---

## B2.18 — MARCOS Ranking

**Identity.** Live id `B2.18`. Method class `MARCOS`. Multi-criteria ranking of an explicit set of
alternatives, in the published MARCOS steps.

**Required inputs.** `decisionAlternatives` — a mapping, and the only input read. It must carry the
alternatives being compared, the criteria they are compared on, **which way each criterion is
better** (`benefit` or `cost`), and a **weight for every criterion**, externally governed. The
weights are refused when absent: `decision_problem(..., require_weights=True)`.

**Method — the published steps, in order.**

```
Extended matrix
  AAI_j = the worst value of criterion j across the alternatives
  AI_j  = the best  value of criterion j across the alternatives
  (best and worst taken according to that criterion's declared orientation)

Normalisation, against the IDEAL
  benefit criterion:  n_ij = x_ij  / x_AI,j
  cost    criterion:  n_ij = x_AI,j / x_ij

Weighted sum
  S_i = sum over j of ( w_j * n_ij ),   with w normalised to sum to one

Utility degrees
  K_i^- = S_i / S_AAI
  K_i^+ = S_i / S_AI

Utility functions
  f(K_i^-) = K_i^+ / (K_i^+ + K_i^-)
  f(K_i^+) = K_i^- / (K_i^+ + K_i^-)

Utility function of the alternative
  f(K_i) = (K_i^+ + K_i^-) /
           ( 1 + (1 - f(K_i^+)) / f(K_i^+) + (1 - f(K_i^-)) / f(K_i^-) )

Ranked descending on f(K_i).
```

The reported result is the ranking, the rank of each alternative, the utility of each, and the
ideal and anti-ideal rows, with the decision lineage.

**Bands.** **None. This module asserts no band and none may be attached.** The route sets
`status_color: None` and carries, in `calibration_pending`, the words verbatim: *"no boundary has
been established for this platform that would turn this reading into a state, so none is
asserted"*.

**Interpretation.** The reading is an **order**, not a score to be compared between projects. The
evidence sentence is of the form *"Of the options compared, the order is A then B then C"*. It
compares the alternatives that were supplied against the criteria that were supplied, and says
nothing about any alternative that was not.

**Abstention.**
1. `decisionAlternatives` absent: `"Awaiting an explicit decision problem: the alternatives being
   compared, the criteria they are compared on, and which way each criterion is better. This
   measure is named for a method that cannot be carried out without it, so no reading is reported
   and no other figure is used in its place."`
2. Present but not a mapping: `"The information provided for this project in place of an explicit
   decision problem: the alternatives being compared, the criteria they are compared on, and which
   way each criterion is better is not in a form this measure can read, so no reading is taken from
   it."`
3. Weights absent: `decision_problem` refuses in the words it raises for the missing weights.
   **Weights are externally governed and none is invented.**
4. A benefit criterion on which the best alternative scores nothing: `"The decision problem
   provided for this project has a criterion on which the best alternative scores nothing, so this
   ranking is not defined on it and none is carried out."`
5. A cost criterion on which an alternative costs nothing: `"The decision problem provided for this
   project has an alternative costing nothing on a criterion, so this ranking is not defined on it
   and none is carried out."`

**One property a reader must be told.** **Nothing in this module's route reads `cpi`, `spi` or
`docRiskScore`.** A crisp performance index is not a decision problem, and the route that reaches
this function cannot see those fields. The result also carries `signal_qualification:
"unqualified"`, the platform's own disclosed state for signals reaching this layer.

---

## Stopped specifications

None. The single module in service in this category has an unambiguous source and is specified
above.
