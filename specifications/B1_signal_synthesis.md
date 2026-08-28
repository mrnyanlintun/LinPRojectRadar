# Category B1 — Signal Synthesis

Four modules: B1.1, B1.2, B1.3, B1.4. These read **what the other categories produced**, not the
project's figures. Pressed before the categories they read have run, the platform reports them
**out of order** and names what is missing; that is a warning, not a failure, and it is decided in
Python before this specification is ever applied.

## What they synthesise, and what they deliberately do not

Three of the four (B1.2, B1.3, B1.4) read the **four assembled arms** the signal package carries —
`evm` the cost and schedule indices, `mc` the cost forecast, `cusum` the performance trend, `doc`
the document risk score — resolved through `canonical_v5.governed_signals_from_project`, each with
its identity, state, period, source provenance, evidence-lineage body, qualification state and
abstention reason.

**Every other module this run computed is deliberately excluded.** Those are not further evidence;
they are further **transformations of these same four arms**, and a transformation retains the
lineage of what produced it rather than becoming an independent project fact. Admitting them let
the count of registered modules decide the answer: identical adverse evidence read Red beside a
three-module array and Yellow beside a sixty-three-module array, because the adverse fraction was
diluted by modules that had learned nothing new. **Nothing is weighted or discounted to fix that**;
the arms that are actually distinct bodies are what is synthesised.

## Three shared rules

**1. Duplicate-lineage neutrality.** Signals resting on the **same declared evidence body** are
collapsed to one representative before any vote, weight or selection. Two readings of one body are
one body read twice; letting the second one vote manufactures corroboration nobody supplied. The
representative kept is the **most severe** reading of the body — the conservative direction and an
idempotent operator, so a third and fourth reading change nothing. Ties keep the earliest in the
supplied order. This is **pairwise over a declared body, not a transitive closure**: two signals
are the same evidence exactly when they name the same body, and nothing joins two bodies because a
third overlaps both. The suppressed ids are reported in `duplicate_lineage_suppressed`.

**2. An unrecognised status is refused, never bucketed.** A status the layer does not recognise
**raises** rather than becoming Green, Amber or an abstention, because an unrecognised string is a
defect in the supply path. The recognised severity order is
`Green 0 < Yellow 1 < Amber 2 < Red 3`. The states that mean *this signal did not speak* are
`Abstain`, `Unknown`, `Insufficient`, `NotEstimable`, `Not Estimable`; a signal in one of those is
visible in the result and **votes nowhere**.

**3. Missing evidence never defaults Green.** An abstaining signal casts no vote, carries no
weight, and cannot occupy a position among the worst.

## The shared nothing-to-report sentence

Where no governed signals were supplied at all, B1.2, B1.3 and B1.4 report nothing, in these words:

> `"No governed signals were supplied for this project, so there is nothing to synthesise and no
> reading is reported."`

Two further supply-path refusals share the same shape: `"One of the governed signals supplied for
this project is not in a form this measure can read, so no synthesis is carried out."` and
`"A governed signal was supplied without an identity, so it cannot be told apart from another and
no synthesis is carried out."`

**Every nothing-to-report sentence in this category carries the platform's own disclosed qualification state,
`"unqualified"`, on `signal_qualification`.** These modules consume raw signals: the Category 9
eligibility gate that would qualify a versioned signal package before evidence combination and
governance read it **is not implemented**, and nothing gates these inputs on evidence quality. A
specification applying them must not claim otherwise.

## The qualification boundary, and it fires BEFORE anything below

Every module in this category is wrapped, **in the dispatch table itself**, by
`qualification_boundary.install`. After that call there is no entry in `registry.VALIDATED` for a
gated module that reaches its runner without the boundary first, and `registry.run_module` looks
the runner up there — **so a consumer cannot route around it by hand-building a signal package.**

The boundary reads the project's declared Category-9 assessment from `signal_inputs` under the key
**`evidenceQualification`**, and asks it for this category's declared use: **`signal_synthesis`**.

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

## B1.1 — Conservative Dominance

**Identity.** Live id `B1.1`. Method class `Conservative_Dominance`. The decision is taken against
the **worst state the evidence supports**.

**Required inputs, by their exact `signal_inputs` field names.** `signals` — a mapping, and it
must carry `signals.cusum`; the module refuses outright otherwise. Within it, `signals.evm`,
`signals.mc`, `signals.cusum` and `signals.doc`, each carrying a `status`. Unlike B1.2–B1.4 this
module reads the assembled mapping directly rather than through the governed signal list.

**Method — a decision rule, and it has no parameter.**
```
bands      = each of (evm, mc, cusum, doc) normalised onto one band, or None where absent
             or outside the platform's status vocabulary
dominant   = the most severe band among those present, or None where none is present
all_green  = every one of the four is present AND every one is Green

dominant is None                    -> state = the decision layer's own health state
dominant == "Green" and not all_green -> state = "Amber"
otherwise                           -> state = dominant
```

**Bands.** This module **does** emit a band: `status_color` is the state above, in the platform's
capitalised vocabulary. **No threshold, weight or constant is introduced anywhere in the rule** —
it is a maximum over bands the signals themselves already assigned.

**Interpretation.** **Conservative dominance is not a count.** Before Run 20 this module returned
the shared decision-layer health state, which is a *counting* rule — two or more Red signals, or a
cumulative-sum breach with a Red forecast, reach Red-review; everything else not uniformly Green
reaches Amber. So a project whose worst signal was Red, **alone**, reported Amber and selected
routine early-warning review rather than escalation: adverse evidence was outvoted by the count of
signals that had nothing adverse to say. **A single adverse signal is enough, because that is
precisely what "conservative" means.** The rule is also idempotent, which matters because three of
the four signals are readings of one earned-value measurement — a counting rule was counting one
measurement up to three times, and a dominance rule cannot.

**The conservative treatment of absent evidence is part of the rule, not an exception to it.** A
dominance rule over the signals *present* would let an absent signal read as agreement: three
Greens and one missing would dominate to Green, which is the strongest claim available and the one
the missing signal never made. **The calmest band is reachable only on complete evidence, and
incomplete evidence cannot be calmer than Amber.** That is the middle branch above.

**What is reported alongside, and why.** `decision_layer_state` — the decision layer's own health
state — is reported **beside** the dominance state, never reconciled with it. B3.1 reads the same
decision layer to decide *which action and whose authority*, which is a different question from
*what the evidence most adversely supports*. The two states are shown side by side so a reader can
see both and is never shown one while believing it is the other. `evidence_complete` and
`signal_bands` travel with them.

**Nothing to report.** `signals` absent, or `signals.cusum` absent:
`"Insufficient data: upload required documents"`.

---

## B1.2 — Weighted Voting

**Identity.** Live id `B1.2`. Method class `Weighted_Voting`. Class-weighted voting over the
governed signals.

**Required inputs, by their exact `signal_inputs` field names.**
`signals` — the assembled arms, read through `governed_signals_from_project`.
`signalWeightPolicy` — a mapping carrying `weights` (a weight per signal id), `set_by` and
`authority`. **Required. There is no default weight anywhere in this function**, so a project with
no policy cannot be given one implicitly.

**Method.**
```
Vote(c) = sum over voting signals i of  w_i * I(s_i = c)
winner  = argmax over c of Vote(c)
```
Weights must be non-negative and are **normalised to sum to one over the eligible independent
signals actually voting**, which is what makes class votes comparable between projects with
different signal counts. The classes are the four severity classes in order.

**Bands.** The winner is emitted as `status_color`. Where there is no unique winner,
`status_color` is `None` and `tied_classes` names the tied classes.

**Interpretation.** The weighted vote says which state carries most of the authority-assigned
weight, and the normalised weights and their provenance travel with the reading so a reader can see
whose judgment produced them.

**Nothing to report.**
1. No governed signals: the shared sentence above.
2. Every governed signal abstained: `"every governed signal for this project abstained, so there
   is nothing to weigh and no vote is reported"`.
3. `signalWeightPolicy` absent or not a mapping: `"Awaiting a weighting policy for this project's
   governed signals. A weighted vote cannot be taken without stated weights, and none is
   assumed."`
4. The policy states no weights: `"The a weighting policy for the project's governed signals: a
   weight for each signal, and the authority that set it provided for this project states no
   weights, so no weighted vote is taken and no weight is assumed for any signal."`
5. The policy omits a weight for a voting signal: the same sentence stem ending `"...does not
   state a weight for every signal being voted on, so no weighted vote is taken and no weight is
   assumed for the signals it omits."`
6. A negative weight: the same stem ending `"...states a negative weight, which a vote is not
   defined on, so no weighted vote is taken."`
7. Every voting signal weighted zero: `"the weighting policy for this project gives every voting
   signal no weight at all, so no winner is reported"`.

**The tie policy is declared, not resolved.** A tie between classes returns **no winner** and says
so. Choosing a winner from a tie is a governance decision with a direction — the calmer class or
the more severe one — and it is not this module's to make.

---

## B1.3 — Majority Rules

**Identity.** Live id `B1.3`. Method class `Majority_Rules`. One vote per eligible independent
qualified signal, plurality winner.

**Required inputs.** `signals` — the assembled arms, read through
`governed_signals_from_project`. There is no policy input; every voting signal counts once.

**Method.**
```
counts(c) = the number of eligible independent signals reading class c
quorum    = 2
winner    = the unique class with the greatest count, or none where two or more tie
```

**Bands.** The winner is emitted as `status_color`; a tie emits `None`, sets `conflict: true` and
names the `tied_classes`.

**Interpretation.** **The quorum is the one structural minimum, not a tuned parameter**: a majority
over a single voter is that voter, which is not a majority rule and is not reported as one. **A tie
is a conflict and is reported as one**, not resolved.

**Nothing to report.**
1. No governed signals: the shared sentence above.
2. Every governed signal abstained: `"every governed signal for this project abstained, so no
   majority is reported and no state is assumed in place of one"`.
3. Fewer independent signals than the quorum: `"fewer independent signals spoke than a majority
   rule needs, so no majority is reported"`.

---

## B1.4 — Worst-N-of-M

**Identity.** Live id `B1.4`. Method class `Worst_N_of_M`. The frozen Worst-2 mean severity
statistic.

**Required inputs.** `signals` — the assembled arms, read through
`governed_signals_from_project`.

**Method.**
```
order the eligible independent signals by severity descending, ties by signal id ascending
MeanWorst2 = (severity(s1) + severity(s2)) / 2
```
over the two most severe eligible independent non-abstaining signals, on the severity scale
`Green 0, Yellow 1, Amber 2, Red 3`. The two selected signals are reported by id, status, severity
and lineage body. **A duplicate-lineage reading cannot occupy the second position**, because
duplicates are collapsed before the two are selected.

**Bands.** **None. `status_color` is `None` and no band may be attached.** The result carries
`classification: null` and, in `calibration_pending`, the module's own words verbatim: *"the
boundaries that would turn this statistic into a state have not been set for this platform, so
none is asserted"*. The number and the two signals it came from are exposed instead.

**Interpretation.** A mean of 3 is two Reds; a mean of 1.5 is an Amber and a Yellow. **Why not
`max` of the worst two:** it collapses to Conservative Dominance and the module stops being a
second regime at all. **Why not the earlier rule:** it compared a red *count* against a *fraction*
of the registered signal array, so registering more modules diluted the adverse fraction and
identical adverse evidence read Red beside three signals and Yellow beside sixty-three. **The
statistic above has no denominator that grows with the array.**

**Nothing to report.**
1. No governed signals: the shared sentence above.
2. Fewer than two independent signals spoke: `"fewer than two independent signals spoke for this
   project, so the worst two cannot be taken and no reading is reported"`.

---

## Stopped specifications

None. All four modules in this category have unambiguous sources and are specified above.

## One property of the whole category a reader must be told

The synthesis role is declared on every reading, verbatim: *"comparison and sensitivity regime;
not an independent project fact and not a voter"*. These four modules compare the arms; they do
not add evidence to the project.
