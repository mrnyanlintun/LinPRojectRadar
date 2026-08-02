# D1: the module inputs nothing can produce

**STOPPED WITHOUT CHANGING CODE, on the stop condition the task set.** Every fabrication path is
deliberate and documented, in three places each. The task said to stop and tell you rather than
remove any that turned out to be. All of them did.

No file under `server/app/simulation/` was modified. Nothing in `assets/` was touched.

---

## 1. The colour change, which is the thing you asked for first

**Project colour does not move. One category does.**

Measured by executing `compute_project` twice on identical inputs, once as shipped and once with
all twelve non-abstaining modules forced to abstain, changing nothing else:

| Case | Project status now | If they abstain | Category changes |
|---|---|---|---|
| healthy, cpi 1.05 | Green | **Green** | B2 Evidence Combination: **Amber to Green** |
| on-budget, cpi 1.00 | Green | **Green** | none |
| distressed, cpi 0.83 | Red | **Red** | B2 Evidence Combination: **Amber to Red** |

One of eight categories moves, and it moves **in both directions**. That is the most useful
result in this report: the fabricated Amber was pulling B2 toward the middle regardless of the
evidence, making a healthy project's evidence-combination look worse than it was and a distressed
project's look better. Abstaining does not soften or harden the picture. It makes B2 agree with
the evidence in both directions.

Modules abstaining per computation goes from **48 to 60** of 95. Note the baseline: **more than
half of the analytical layer already abstains** on a typical single-document project, so twelve
more is a change in degree, not in kind.

**Size of the visible change**: any surface showing category status would show B2 differently, and
B2 currently reports a colour on every project. Project colour, the radar, the map and the
portfolio list are all driven by `project_status`, which does not move on these cases. I did not
test every input combination, so **I cannot say project colour never moves**, only that it did not
on the three canonical cases the platform ships fixtures for.

**Stored results carrying a fabricated verdict, locally reachable:**

```
stored computed_results rows reachable locally : 20
rows carrying >=1 verdict from a fabricated path: 20   (100%)
individual fabricated verdicts stored           : 237
```

Every stored result in every local database carries at least one. **Production was not inspected
or queried** and no stored data was altered.

## 2. Why I stopped

The task: *"If any turns out to be deliberate and documented somewhere, stop and tell me rather
than removing it."*

Each of the three named failure shapes is documented as a deliberate reproduction of the
JavaScript, in the module docstring, in `VALIDATION.md`'s per-module note, and in
`VALIDATION.md`'s input-contract section.

**Rough Sets and the whole B2.2 to B2.9 family**, `models_evc.py` docstring:

> These modules never abstain with the standard stub: when no signal contributes they emit the
> AMBER "Insufficient signal data" result the JavaScript emits (BRB and Quantum always compute,
> via a fallback rule / default amplitudes). **That is the instrument's behaviour, reproduced.**

**Audit Trail and Reporting Frequency**, `models_dq.py` docstring:

> Both emit non-abstaining stubs on sparse input (Red-band completeness and the Yellow "upload
> more documents" stub) **the instrument's behaviour, reproduced.**

`VALIDATION.md` C1.7: *"below 2 extraction events emits the Yellow stub the JS emits, **not an
abstention**"*. B2.9: *"always computes (default amplitudes when signals missing)"*.

**CUSUM's synthesised series**, `derive_series` docstring: *"A short deterministic metric series
when none was supplied. The JavaScript hashes a string to seed this; here the caller supplies the
seed derived from (scenario_id, period)"*. A faithful port, with the seeding made scenario-aware
rather than input-aware on purpose.

Authored in `8402f38` (batch 7b), `88536bb` (batch 9) and `d895954` (batch 1). Deliberate at
authoring, recorded at authoring, and validated against the JavaScript afterwards.

**The distinction that matters, and why I do not think this closes the question.** What was
decided deliberately was *"reproduce the JavaScript faithfully."* What was never decided is
whether the input contract those decisions assume would ever be satisfied server-side. In the
browser the blob arrived and the fallback was a genuine edge case. Server-side the blob never
arrives, so **the fallback is the only path that ever executes**. The decision was sound for the
port and is unsound for the deployment, and nothing recorded anywhere shows that transition being
noticed. That is a decision for you, not a defect I should quietly reverse.

## 3. Corrections to my own audit

The pipeline audit undercounted, because it scanned for `si.get("key")` and `si["key"]` textually
and missed helper indirection. I re-established this by executing every module with a recording
dict rather than reading it.

**Twelve unobtainable keys, not eleven.** `cpiHistory` was missed; it is read through
`_history(si, "cpiHistory", "cpi")` in `models_evm.py`.

**Twenty-one modules touch one, not eleven. Nine of those already abstain correctly**, which the
audit did not establish:

| Already abstains, correctly | Reads |
|---|---|
| A1.4 Kalman_Filter, A1.5 ARIMA_Forecast, A1.10 Regression_To_Mean | the history series |
| **A2.7 Milestone_Trend** | `milestoneHistory` |
| B1.1, B1.2, B1.3, B1.4, B3.1 | `signals`, `simulationSignals` |

**A2.7's behaviour was recorded as unknown in the audit. It is now established: it abstains
correctly.** It needs no change.

**Twelve modules do not abstain**, one more than the audit's eleven, and the membership differs:

| Module | Emits with the key absent | Group | Votes in status |
|---|---|---|---|
| A1.2 CUSUM | `red`, 12 fabricated periods, breached | A | yes |
| B2.1 DST_Evidence_Combination | Green | B | yes |
| B2.2 Rough_Sets_Classification | Amber | B | yes |
| B2.3 Neutrosophic_Logic | Amber | B | yes |
| **B2.4 Interval_Fuzzy_Sets** | Amber | B | yes |
| B2.5 Z_Numbers | Amber | B | yes |
| B2.6 PLTS | Amber | B | yes |
| B2.7 Plithogenic_Sets | Amber | B | yes |
| B2.8 Belief_Rule_Base | Amber | B | yes |
| B2.9 Quantum_Probability | Green | B | yes |
| C1.4 Audit_Trail_Completeness | Red | C | no |
| C1.7 Reporting_Frequency_Index | Yellow | C | no |

B2.1 and B2.4 were absent from the audit's list. Ten of the twelve vote in status, not nine.

## 4. Unwired versus permanently unobtainable

You asked specifically which is which. **None of the twelve keys is permanently unobtainable. All
are unwired**, though they differ sharply in how much work wiring would be.

| Key | Status | Evidence |
|---|---|---|
| `events` | **Unwired, and the data already exists in the right shape** | `writes._append_event` writes `{"event": ..., "at": ...}` into `project.doc["events"]`, which is exactly the `{event, at}` list `models_dq` documents. Nothing passes it into `signalInputs`. |
| `spiHistory`, `cpiHistory` | **Unwired, reconstructible from stored data** | Every `ComputedResult` stores `signal_inputs` with `cpi` and `spi` per period. A per-project series across periods is assemblable from rows that already exist. |
| `evm`, `mc`, `cusum`, `doc` | **Unwired, derivable within the same run** | These are the browser's `existingSignals`, i.e. the outputs of A1.1, A1.2 and the document-risk value. They are products of the same computation, so wiring is an intra-run ordering problem, not missing evidence. |
| `signals`, `simulationSignals`, `decision` | **Unwired, assembled-project shapes** | The modules reading them already abstain, so nothing is currently wrong. |
| `milestoneHistory` | **Unwired**; source UNKNOWN | A2.7 abstains correctly today. I did not establish what would populate it. |
| `fairnessSensitive` | **UNKNOWN** | Read by `models_decision.py`. I did not establish whether anything stores it. |

**`events` is the clearest case.** The platform records exactly what C1.4 and C1.7 want, in the
shape they document, and C1.4 reports "0 events recorded" on every project as a result. That one
is a wiring gap, not a design limit, and wiring it would make C1.4 report something true instead
of a permanent Red.

## 5. What I did not do, and what I would need from you

I did not write the abstention changes, the tests, or the `VALIDATION.md` note, because all three
presuppose the removal you asked me to stop before making.

**The decision is between two defensible positions**, and it is yours:

- **Faithfulness.** The port reproduces the instrument. Changing it means the server no longer
  matches the JavaScript, and `VALIDATION.md`'s exact-match records stop being true for twelve
  modules. If the research design depends on the instrument behaving as the instrument behaved,
  that matters.
- **Correctness.** The instrument's fallback was an edge case; here it is the only path. B2 reports
  a colour derived from zero evidence on every project, and section 1 shows it is wrong in both
  directions.

**My recommendation, for whatever it is worth: abstain, and wire `events`.** Section 1 shows the
cost is one category moving to agree with the evidence and no project colour change on the
canonical cases, which is a small price for removing 237 fabricated verdicts from the local record
alone. But it is a research-instrument decision and I am not going to make it inside a task that
told me to stop if I found what I found.

**If you want me to proceed**, the useful thing to tell me is which of the three you want:

1. **Abstain everywhere**, accepting divergence from the JavaScript, with `VALIDATION.md` annotated
   to say the exact-match records do not speak to the input contract.
2. **Abstain only where the fallback is provably unreachable in the browser too**, which needs the
   JavaScript examined rather than assumed, and which I have not done.
3. **Wire the keys instead of abstaining**, starting with `events` and the history series, which
   removes the fabrication by supplying the evidence rather than by refusing.

These are not exclusive: 3 for `events` and the histories, 1 for the rest, is coherent.

---

## Verification

No behavioural change was made, so the suites are unchanged from the last session's baseline and
I did not re-run them: **1013 checks across 21 suites, `tests_render.html` 26/26** as of `ce73d6d`.
Everything in this report was produced by executing modules in throwaway processes against
`assemble_signal_inputs` output and local throwaway databases.

**Nothing was committed to `server/app/simulation/`. No stored data was altered. Production was
not inspected or queried. `assets/` was not touched, so the parallel Map and Globe session is
unaffected.**
