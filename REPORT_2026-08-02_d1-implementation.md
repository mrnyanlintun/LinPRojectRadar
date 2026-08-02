# D1 implemented: the obtainable keys wired, the rest abstaining

**1113 checks across 22 suites pass. `tests_render.html` 33/33.** No stored data was altered,
production was not inspected or queried, and nothing under `assets/` was touched.

---

## 1. Colour movement, which is the thing to read first

### Project colour DOES move. My previous report said it did not. That was wrong.

The D1 findings report concluded "project colour does not move on any canonical case". Measuring
the implemented change against the test suite's own fixtures, it moves on two of three. The
earlier figure came from a hand-built variant rather than from the fixtures the suite ships, and
it missed the largest single effect in this whole task:

| Case | Project before | Project after | Categories that move |
|---|---|---|---|
| **healthy** (spi 1.05, cpi 1.02) | **Red** | **Green** | A1 Red→Green, B2 Amber→Green |
| **on-budget** (spi 1.00, cpi 1.00) | **Amber** | **Green** | B2 Amber→Green |
| **distressed** (spi 0.70, cpi 0.80) | Red | **Red** | B2 Amber→**Red** |

**A healthy project was being reported as Red, and the cause was the fabricated CUSUM series.**
With no `spiHistory`, A1.2 synthesised twelve observations from the current SPI and drew a control
chart over them. A project running ahead of plan produces a series that drifts away from the
control target, so the chart breached, A1.2 returned Red, category A1 went Red, and the project
went Red. The chart was drawn over numbers nobody measured.

Direction is worth stating plainly: the healthy project improves, the distressed project's
evidence-combination gets **worse**, and the distressed project stays Red. Nothing here softens a
bad project. The fabrications were pulling every project toward the middle, and removing them lets
each read according to its own evidence.

### What a real project sees, measured end to end

The table above is a first period with no history and no event log. The realistic path is a
project uploading a document each period, computed through `projectupload` and `projectcompute`
against a throwaway database:

| | period 1 | period 2 | period 3 |
|---|---|---|---|
| Project status | Green → **Green** | Green → **Green** | Green → **Green** |
| Category B2 Evidence Combination | Amber → **Green** | Amber → **Green** | Amber → **Green** |
| Category C1 Data and Evidence Health | unchanged | Amber → **Yellow** | Amber → **Green** |
| **C1.4 Audit Trail** | Red → **Green** | Red → **Green** | Red → **Green** |
| A1.2 CUSUM | red → abstains | red → abstains | **red → amber** |
| A1.4 Kalman | abstains | **abstains → Green** | **abstains → Green** |
| A1.5 ARIMA | abstains | abstains | **abstains → Green** |
| A1.10 Regression to Mean | abstains | **abstains → Green** | **abstains → Green** |
| Modules reporting a colour | 47 → 37 | 47 → 40 | 47 → 41 |

Three things in that table matter more than the project colour, which does not move here:

- **C1.4 goes from a permanent Red to Green on every period.** It was reporting "0 events
  recorded" about a platform that has been recording events, in exactly the shape C1.4 reads,
  since `_append_event` was written. This is the single clearest case of a wiring gap presented as
  a finding about a project.
- **Four modules that never computed now compute**, on the project's own figures across periods.
  Kalman, ARIMA and Regression to Mean abstained on every project ever computed; CUSUM computed
  from an invention. At period 3 CUSUM disagrees with its own fabrication: **red becomes amber**.
- **Category C1 now improves as the record builds**, Amber to Yellow to Green. Evidence health was
  previously frozen by a Red that no amount of real evidence could move.

**Modules abstaining, against the two numbers in the previous report:** 48 of 95 before, and 60 if
everything abstained. The implemented result is **58 at period 1, 55 at period 2, 54 at period 3**
— the count falls as history accumulates, because wiring gives evidence back rather than only
taking verdicts away. Twelve verdicts per stored result were fabricated; two or three of the
twelve now compute from real evidence and the rest abstain.

### Stored results

**Every result stored before this change carries twelve fabricated verdicts**, and that is a
structural fact rather than a sample: B2.2 through B2.8 returned a status colour unconditionally,
so no stored result can be without them. Measured on the three-period fixture, exactly 12 of the
twelve emitted a colour in each stored result before, and 2 or 3 after.

**No stored data was altered.** Existing results keep the verdicts they were computed with, which
is what the append-only discipline requires: a decision recorded against a result must still
resolve to what the participant was shown. A recompute through `adminrecompute` writes a new row
with a stated reason and picks up the new behaviour. Production was not inspected or queried, so I
cannot give a production row count.

## 2. What was decided and built

Your instruction was option 3 where the data exists, option 1 everywhere else. That is what was
built, and the split fell as follows.

**Wired, because the platform already holds the evidence:**

| Key | Source | Modules it reaches |
|---|---|---|
| `events` | `project.doc["events"]`, written by `_append_event` since it was authored | C1.4, C1.7 |
| `spiHistory` | `signal_inputs.spi` from the project's earlier live results | A1.2, A1.4 |
| `cpiHistory` | `signal_inputs.cpi` from the project's earlier live results | A1.5, A1.10 |

Both are assembled in `documents.py` (`_events_as_of`, `_period_history`) rather than in
`assemble_signal_inputs`, which must stay pure, deterministic and order independent — it knows
nothing of projects, periods or the session, and those three properties are what make a recompute
reproducible. Both are stored on the row as part of `signal_inputs`, so a result records what the
modules actually saw.

**Abstaining, because nothing can ever supply them:** `cusum`, `decision`, `doc`, `evm`,
`fairnessSensitive`, `mc`, `signals`, `simulationSignals`. These are the browser's
`existingSignals`, and the browser no longer computes. Ten modules read them; the eight in B2 were
fabricating and now abstain, and B1.1/B3.1 (which read `fairnessSensitive`) already abstained
correctly through their `signals` guard and needed no change.

Each abstention uses `insufficient()` — the existing contract, the same one Kalman, ARIMA and
Regression to Mean have always used. No new abstention form was introduced. Every fabrication path
is deleted: `derive_series` and `hash_seed` are gone from `models_sim.py`, the R0 fallback rule is
gone from the Belief Rule Base, the five AMBER "Insufficient signal data" stubs are gone, and
Rough Sets' `or 1` denominator is gone. Nothing is behind a flag and nothing is retained for tests.

**Rough Sets specifically**, since you named it: `total = len(classes) or 1` made every ratio 0/1
on an empty evidence set, which put every state outside the lower approximation, produced
"Indeterminate", and returned Amber. The denominator is now `len(classes)` and an empty set
abstains before reaching it.

## 3. The history question, established before building as instructed

**A history can be supplied safely, and it does not enlarge P1.**

`_period_history` filters on `ComputedResult.period < period`, evaluated against the period being
computed. Recomputing period 1 while periods 2 and 3 exist reads neither of them. That is
different in kind from the portfolio vector block a few lines below it, which the pipeline audit
found reaching every project's most recent live result regardless of period — P1 is untouched,
neither widened nor fixed here.

Two further constraints fell out of building it:

- **Live rows only.** A superseded result has been replaced by a recompute of that same period and
  is no longer the project's account of it.
- **A one-element series is not supplied at all.** `_history` already synthesises `[si.spi]` from
  the scalar, so passing a single point would restate `si["spi"]` under a second name and let
  modules think they had a series. Period 1 therefore gets no history, and its three history
  readers abstain, which is true.

**The event log is truncated at the period cutoff**, for the same reason C1.2 takes its "now" from
the cutoff rather than the clock. Without it, recomputing an early period would see every event
logged since, and a later period's activity would decide an earlier period's audit-trail verdict.
The suite asserts this directly: a project fixture carries an event dated December, and no period
sees it.

**`milestoneHistory` cannot be supplied and A2.7 continues to abstain.** `milestones_json` is
requested from the extraction model for two document types, but it is not in `ALL_FIELDS`, so it
is never merged into `signalInputs` and no stored result carries it. A2.7 abstained correctly
before D1 and needed no change. Supplying it is a merge-layer task, not this one. This is the
legitimate "cannot be supplied today" outcome you allowed for.

## 4. A gap the wiring exposed, reported not fixed

**The server no longer records extraction events at all.** `signals_extracted` appears in imported
legacy project documents and in `w_signalsreset`'s preservation filter, but no current code path
writes one: `projectupload` and `projectcompute` append nothing. So C1.4 now reports truthfully on
what is recorded, and what is recorded for a server-created project is `project_created` and
whatever CRUD has happened.

I did not add the missing event write, and the reason is specific rather than caution:
`facade.py` derives the user-facing **docCount** from the number of `signals_extracted` events.
Adding one per upload would change docCount on every project, which is a visible change to a
number nobody asked me to touch, in a task about colours. It is a small change and I think it is
right, but it is yours to authorise.

**A second, smaller one.** `_js_date_ms` refuses datetime strings deliberately, because a `T` form
without a zone parses as local time in JavaScript. `_append_event` stamps a full ISO datetime.
Passing the raw stamp would have made C1.7 abstain on every real project while appearing wired, so
`_events_as_of` narrows `at` to its date part at the boundary rather than loosening a parser that
is strict on purpose. The suite has an explicit check for this, because it is exactly the kind of
thing that would have gone quietly green.

## 5. VALIDATION.md

The exact-match rows for all twelve are **kept, not corrected**, each with a `D1: DIVERGES` note
saying what it did, what it does now, and that the JavaScript comparison no longer describes it.
A banner at the top names the twelve and states the thing the file has been carrying implicitly:
**a matched row establishes that this server computes what the JavaScript computed, not that the
module is correct.** These twelve matched exactly on their no-signal cases, and that was the
problem rather than the reassurance. A new section, "D1 divergence: the fabricated no-evidence
verdicts", records the measurement and the reasoning. The Group B input-contract section is
amended, because it described a contract no caller could satisfy.

## 6. Tests, and proof they can fail

New suite `server/tools/test_d1_module_inputs.py`, **100 checks**, one section per property.

**The vacuous-check trap, addressed directly.** The specific way this suite could pass for the
wrong reason: an abstention check that passes because the module already abstained for an
unrelated missing input, proving nothing about the fabrication path. Every check therefore varies
**one key's removal** from a signalInputs that is otherwise complete, and section 1 asserts as a
precondition that all twelve **compute** on that complete input. If a module ever starts abstaining
for another reason, the precondition fails rather than the suite going green on a false positive.

Nine faults injected, each restored byte-identical:

| Fault | Result |
|---|---|
| CUSUM's synthesised series restored | 93/100, exit 1 |
| Rough Sets' `or 1` denominator restored | 96/100, exit 1 |
| Belief Rule Base R0 fallback restored | 96/100, exit 1 |
| C1.7 Yellow stub restored | 99/100, exit 1 |
| DST no longer abstains | 97/100, exit 1 |
| `events` wiring removed | 93/100, exit 1 |
| history wiring removed | 93/100, exit 1 |
| **date narrowing removed** (wired-looking but silently abstaining) | **98/100, exit 1** |
| **history reads all periods instead of earlier ones** (the leak) | **99/100, exit 1** |

The last two are the ones that matter most: both are faults that leave the code looking correct.

**Two vacuous checks were found and fixed while doing this.** Injecting the `events` fault showed
three truncation assertions passing on an empty list, because `all()` over `[]` is true. They now
assert the log is non-empty first. That is the fourth session running in which a check turned out
to pass for the wrong reason, and it was the fault injection rather than review that caught it.

## 7. Verification

| Check | Result |
|---|---|
| Server suite | **1113 checks across 22 suites, 0 failures** |
| `tests_render.html` | **33/33** |
| New suite proven able to fail | 9 independent faults, distinct signatures |
| Existing suites unchanged | 1013 → 1113 is exactly the 100 new checks |

**The existing 1013 checks passed with the changes in place before a single new test was written.**
That is worth stating as a finding rather than as reassurance: the suite could not detect the
removal of twelve fabricated verdicts, including one that was turning a healthy project Red.

---

## Judgement calls to review

1. **The event log is truncated at the period cutoff.** Reproducibility and non-leakage require
   it, but it means an event recorded after the last document's date does not count toward that
   period's audit trail. On a project whose documents are dated in the past, that can exclude
   `project_created`. I judged a reproducible understatement better than an unreproducible
   overstatement, but this is the call I would most like you to look at.
2. **No `signals_extracted` event is written on upload**, section 4. C1.4 is now truthful about a
   log that is thinner than it should be. Fixing it changes docCount.
3. **`signal_inputs` now carries `events`, `spiHistory` and `cpiHistory`** on stored results. It
   makes a result record what the modules saw, at the cost of a larger stored blob and a
   `signal_inputs` that is no longer purely `assemble_signal_inputs` output.
4. **A one-period history is not supplied.** Defensible, but it means period 1 of every project
   abstains from four modules where the JavaScript would have shown something.
5. **B2.1 DST abstains only when all four signals are absent**, not when any is. With a partial
   blob it would still take the vacuous-mass branches for the missing ones. No caller can produce
   a partial blob today, so this is unreachable, but it is a choice rather than an oversight.
