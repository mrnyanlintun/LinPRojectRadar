# The flat-to-nested adapter: fourteen registered computations reach the normal path

Branch `claude/remediation-adapter-run` from `origin/main` at `9e3bc84`. This is the run the
programme file calls **Run 3 - the adapter**, executed second under the revised order 1, 3, 2, 4, 5
(`remediation_decisions_answered.md` 2.2). Audit P0 finding 1.

---

## 1. Lead finding: twelve of the fourteen now compute, two stay refused

Before this run, all fourteen abstained on **every** real run, on every project, in every period.
They declare a nested assembled signal package as their input; extraction and `documents.py` supply
a flat dictionary of figures; nothing on the server ever built the nested one. The abstention was
indistinguishable from missing data, which is why it survived.

Measured on the real path: a four period project uploaded through `/exec` and computed through
`documents.run_and_store`, cost performance deteriorating from 0.98 to 0.87 across the periods.

| Computation | What it expects | What the adapter supplies | Result |
|---|---|---|---|
| Conservative Dominance | The four assembled signals, each with a status; refuses without a trend signal | Indices, forecast, trend, document risk, with the statuses the instrument's own assembler produces | **Computes** from period two: "Red-review: Multi-signal red-review". **Abstains at period one**, stating that the performance trend was not available because the trend computation abstained, which is true: a first period has no index history |
| Weighted Voting | Forecast, trend and document risk statuses, the conservative decision state, and the array of this run's module results | All five, with the decision state taken from Conservative Dominance's own output one tier earlier | **Computes**: "Weighted vote: Red (38 per cent of weighted signals)" |
| Majority Rules | Forecast, trend, document risk, and the results array | Same, minus the decision state it does not read | **Computes**: "Red by majority (21 of 56 modules)" |
| Worst-N-of-M | Forecast, trend, document risk, and the results array | Same | **Computes**: "21 Red and 18 Amber of 56 total modules" |
| Dempster-Shafer evidence combination | Indices, forecast overrun, trend breach flag, document risk score, and the conservative decision state for its agreement field | All five | **Computes**: "Belief: Green 3 per cent, Amber 25 per cent, Red 72 per cent, conflict mass 82 per cent" |
| Rough Sets | Indices, forecast overrun, trend breach flag, document risk score | All four | **Computes**: "Borderline: Green / Amber / Red" |
| Neutrosophic Logic | Same four | All four | **Computes**: "T=1 I=0 F=0, indeterminacy low" |
| Interval Fuzzy Sets | Indices, plus the other three where present | All four | **Computes**: interval memberships per state |
| Z-numbers | Same four | All four | **Computes**: "Reliability-weighted: Red 1.73, Amber 0.65, Green 0.9" |
| PLTS | Same four | All four | **Computes**: "P(Green)=24 per cent, P(Amber)=32 per cent, P(Red)=44 per cent" |
| Plithogenic Sets | Same four | Nothing: it never reaches its input | **Abstains, correctly.** Disabled as concept-only by the previous run; `run_module()` refuses it before any adapter output is consulted. Its stated reason is the disabled one, not an assembly note |
| Belief Rule Base | Indices plus the other three | All four | **Computes**: "BRB belief: Green 5 per cent, Amber 25 per cent, Red 70 per cent" |
| Quantum Probability | Same four | Nothing: it never reaches its input | **Abstains, correctly**, for the same reason as Plithogenic Sets |
| ABM Governance Layer | The four assembled signals with statuses; refuses without a trend signal | Same as Conservative Dominance, of which it is the second projection | **Computes** from period two: "Red-review: Recovery-plan review and management escalation (Program director / PMO lead)". **Abstains at period one**, same stated reason |

**Every abstention states a reason in words.** The two disabled ones say they are disabled and why.
The two that abstain in a first period say which assembled signals they were given, which they were
not, and why each missing one was missing. Nothing abstains silently, and nothing abstains with only
"insufficient data".

**Which abstentions are data gaps and which are not.** The only remaining abstentions among the
fourteen are: the two disabled modules, permanently, until a run outside this programme revisits
them; and the two governance projections in a project's **first** reporting period, because they
refuse without a performance trend and a trend needs at least two periods of index history. That
second one resolves itself on the next period with no further work.

---

## 2. The Category 9 deviation, stated rather than hidden

**These fourteen computations consume raw, unqualified signals.** That is audit P0 finding 2 and a
reviewer will ask about it, so it is written here, in the code, in the methods documentation and in
the export rather than only in a decision log.

The architecture requires Group B to read a versioned **qualified-signal package** produced by a
Category 9 eligibility gate, so that evidence judged untrustworthy cannot feed synthesis and
governance. **That gate does not exist anywhere in this platform.** `run_all` executes modules
independently, and `compute_project` merely excludes the evidence-health group from the vote, which
is a different thing entirely: it stops evidence quality from being read as project condition, and
it does not stop poor evidence from being combined. Nothing qualifies any module's inputs before it
reads them.

The adapter is therefore built on raw signals **by decision** (`remediation_decisions_answered.md`
3.1), not by oversight. A minimal gate first would be better engineering and is scope that is not
available. The deviation is recorded three ways:

- every result and every abstention of the fourteen carries `signal_qualification: "unqualified"`,
  and every computed one carries the sentence explaining what is missing, in the API response;
- the committee-facing export has a new `signal_qualification` column, filled **on every row**, not
  only the fourteen, because the gate is absent for every computation and marking only these would
  imply the rest are qualified;
- the methods documentation states it on each newly wired entry.

It is deliberately **not** on the participant surface, per the settled owner decision that the
participant does not see the remediation (`remediation_decisions_answered.md` X3).

---

## 3. What was built

**One adapter, in one file, called from one place.** `server/app/simulation/signal_package.py`
assembles the nested package; `registry.run_all()` calls it once and hands the result to exactly
those fourteen modules. There are no per-module shims. Because `run_all` is inside the one
computation tail both assembly paths share (`documents.run_and_store`, used by the document path and
by training period generation), there is no second path to drift.

**It routes evidence; it does not manufacture any.**

- The **indices** come from the flat `cpi` and `spi`. Absent unless both are present: an index pair
  built on one index and a substituted 1.0, which is what the browser did, is a fabrication of the
  class D1 removed.
- The **forecast** signal is this run's own Monte Carlo result, not a second simulation. If that
  computation abstained, there is no forecast signal.
- The **trend** signal is this run's own control-chart result, same rule. A first period has no
  history, so it has no trend signal rather than an invented one.
- The **document risk** signal is the score the extraction model supplied, carried through.
- The **decision** signal is Conservative Dominance's own output, computed in the tier before the
  modules that read it, which is the order the browser used.
- The **results array** the voting ensembles read is what this same run has already computed.

**The only arithmetic in the adapter** is the two status-band functions transcribed from the
instrument's own assembler (`assets/js/sim.js` `evmStatus` and `docStatus`). They classify an
assembled signal. **No module's formula was changed, reached differently, or touched.** The forecast
and trend statuses are not recomputed at all: they are the statuses those modules already produced.

**The stored inputs are unchanged.** The adapter copies; it never mutates. `signal_inputs` on the
row carries no assembled objects, so every other module receives byte for byte what it received
before, and the stored evidence record is what it always was.

**Ordering and the shared generator.** The fourteen now run in three deferred tiers after the flat
modules. None of them draws from the shared random generator (verified: no `rand()` call in any of
the three files), so deferring them cannot move any other module's position in the stream. That is
asserted, not assumed: every other module's result is compared byte for byte with and without the
adapter, stochastic ones included.

---

## 4. Activation state: reachable, shown, marked, and still not voting

Per `remediation_decisions_answered.md` 3.2 and 1.1. The fourteen are reachable and shown, and
**none of them votes**: not in the category rollup or project status fusion, not in the generated
recommendation text or courses of action, not on the decision card. They are not in the interim
voting set, and the previous run's three exclusion layers already cover them; this run adds nothing
to that machinery and asserts the result.

They are marked **newly wired and unvalidated** in the API response, the export and the methods
documentation, and **not on the participant surface**, exactly as the proxy qualifier is. The
previous run established that the Signal Ledger is reachable from the participant decision sequence;
that finding was honoured, and a browser drive confirms no wiring qualifier and no proxy qualifier
renders anywhere on that page.

---

## 5. Precisely which surfaces changed, and how (the 8/7 placement rule)

**No new control was added anywhere.** No new page, no new panel, no new pill, no new row.

1. **The Signal Ledger, project detail page, participant-reachable.** The fourteen rows already
   existed and already rendered; twelve of them now read a status and a finding where they read
   "No data" before. Same rows, same place, same shape. Two rows keep the "Not relevant" state the
   previous run gave them. Nothing was added to the row.
2. **The Methods tab, module reference entries.** One new sentence per entry, headed "Wiring.", at a
   fixed position directly under "Purpose" and under the "Status" line where the previous run put
   one, for the twelve newly wired non-disabled entries. It states that the computation could not
   run before, that its output is unvalidated, that it is advisory and non-voting, and that no
   eligibility gate qualifies its inputs. No new entries, no new tab, no new navigation.
3. **The committee-facing export workbook, Module results sheet.** The `computation` column now
   carries the newly-wired clause for the fourteen, in the same fixed form the previous run's
   qualifier uses. One new column, `signal_qualification`, filled on every row. No new sheet.
4. **The API response** (the JSON the stored result already returns) gains
   `newly_wired_unvalidated`, `wiring_note`, `signal_qualification` and `category_9_deviation` on
   the fourteen's results, and the first three on their abstention records. No existing key changed
   shape or meaning.
5. **Abstention reason text**, which the ledger renders, now names the assembled signals a module was
   given and those it was not, in plain words. It carries no module id, no numbering, no key names
   and no em dash.

---

## 6. Guarantees, each marked

- **Each of the fourteen executes on `documents.run_and_store` against a real project.** VERIFIED.
  `server/tools/test_run3_adapter.py` uploads four periods through `/exec` and computes them through
  the document path; twelve produce a finding, two are the concept-only pair refused before their
  input. Nothing in the suite assembles a package itself and hands it to a module.
- **A module that still abstains does so for a stated reason.** VERIFIED, on the stored row read back
  through the API, including that the reason names the missing signal and carries no module id.
- **None of the fourteen votes in the rollup, the recommendation text or the decision card.**
  VERIFIED: every one carries `votes:false`; no category rollup exists for any category carried only
  by them; none is in the interim voting set, which is what the courses-of-action gate and the
  decision card's health state both read.
- **Project status for a project is unchanged by this run.** VERIFIED, and **proved able to fail
  first.** The "before" is not a remembered number: it is the same `compute_project` with the
  adapter's module set emptied, which returns the fourteen to the flat dictionary and reproduces the
  pre-adapter path exactly. Project status, project conflict and every category rollup are
  identical, and the stored row from the real path agrees with both. The fault: letting one of the
  fourteen vote **does** move project status, shown red before the check is shown green, then
  removed and the baseline reconfirmed identical.
- **Nothing else moved.** VERIFIED: every module outside the fourteen produces a byte-identical
  result with and without the adapter, stochastic ones included, and the same modules abstain.
- **The adapter never invents a signal.** VERIFIED: one index alone assembles no index pair; an
  abstaining forecast or trend computation yields no forecast or trend signal; the status bands
  match the instrument's own assembler at every boundary.
- **The qualifier reaches the export, the API and the methods documentation and not the participant
  surface.** VERIFIED twice: by source inspection of every participant-facing script, and by driving
  the real page in a real browser in two themes.
- **Browser verification, both themes.** VERIFIED. See section 7; the previous run could not do this
  and flagged it, and the container turns out to have a usable browser after all.
- **No arithmetic changed.** VERIFIED by the byte-identical comparison above and by the fact that no
  formula line in any module was edited. One display string was edited and it is declared in
  section 8.

---

## 7. Verification performed

**Server suite:** fresh SQLite per file, `PYTHONIOENCODING=utf-8`, interpreter confirmed real.
Baseline on `origin/main` before any change: **3109/3109 across 57 files**. After:
**3167/3167 across 58 files**, including the new `test_run3_adapter.py` (51/51).

**`tests.html`:** 51/51, in a real browser.
**`tests_render.html`:** 286/287, in a real browser. The one red is the pre-existing auth-gated
production-read row, red in the previous sessions' baselines too and unrelated to this run.

**Real browser, real server, both themes** (Fairbanks and New York, the default and the research
pin, driven through the application's own theme switcher, transitions suppressed before reading
computed styles, the blackholed sign-in script aborted): a four period project uploaded and computed
through the API, then the project detail page and the Methods tab driven. 45 of 47 checks green; the
two reds were both faults in the drive script itself (a misspelled module name, and a content
assertion made before the ledger's nested rows were expanded), each then confirmed by hand against
the live DOM. What the browser shows:

- the Signal Ledger renders all twelve newly reachable computations with their statuses and their
  findings, in both themes, for example "Belief: Green 99 per cent, Amber 0 per cent, Red 0 per
  cent, conflict mass 27 per cent" and "Green by majority (32 of 42 modules)";
- no wiring qualifier and no proxy qualifier appears anywhere on that page;
- no em dash appears anywhere on that page;
- no uncaught page error in either theme;
- the Methods tab carries the wiring sentence on the newly wired entries and states that no
  eligibility gate qualifies the signals;
- the two themes really do render differently, checked on computed style rather than asserted.

**The browser check was proved able to fail end to end,** which is the strongest evidence in this
report: a second server was started with the adapter's module set emptied, the same documents
uploaded and computed, and the same page driven. Every one of those rows read **"No data"**. With
the adapter, the same rows read a status and a finding. That is the defect and its fix, observed on
the surface a person looks at, not inferred.

**Every check proved able to fail.** Beyond the two above: emptying the adapter's tiers takes the
reachability checks to zero and the baseline is restored afterwards, status included; letting one of
the fourteen vote moves project status; the "without the adapter all fourteen abstain" direction is
asserted positively rather than left implicit.

**One suite went red and it was rewritten rather than loosened**, and the diagnosis matters:

- **`server/tools/test_d1_module_inputs.py`**, section 5, asserted that seven evidence-combination
  modules "contribute no colour" on a healthy project. **That check was recording the old wiring
  failure as expected behaviour** - the fifth failure mode in the project's own test discipline.
  They contributed no colour because they could not run at all, not because the project held no
  evidence. The property D1 actually protects is that no colour comes from an **empty** evidence
  set, and that is what is asserted now, in both directions: with indices present the seven combine
  the evidence the project does hold, and with no evidence at all they still abstain. Nothing in
  D1's fabrication fixes was reverted, and the per-key direct-drive checks in section 2 of that file
  are untouched and still green.
- No other suite needed any change.

---

## 8. Incidental findings, all of them

1. **A key mismatch inside the instrument's own assembler, of the class that has killed six things
   here.** The browser's `buildSignals` emits the forecast overrun as `p80eacOverrunPct`, and every
   consuming module reads `p80DeltaPct`. In the browser that arm therefore read undefined, fell
   through `|| 0`, and put every project in the calmest forecast branch regardless of its forecast.
   The adapter supplies the key the modules actually read, and carries the other name alongside it
   for traceability. **This is a deliberate divergence from what the JavaScript produced**, and it is
   the right direction: the contract the module declares is the contract, and parity with a defect
   is not validity.
2. **The case defect is wider than Conservative Dominance.** The instrument emits assembled signal
   statuses in lowercase, and the server's forecast and trend computations do the same, so
   Conservative Dominance and ABM Governance, which compare in lowercase, classify correctly. But
   the three voting ensembles bucket statuses against a **capitalised** vocabulary, so the three
   primary signals they read fall through to the Green bucket. That is audit finding 3's exact
   mechanism appearing in three more computations than the audit named. **The adapter deliberately
   does not normalise the casing**: doing so would change those modules' arithmetic from outside,
   which this run's exception forbids, and would hide the defect. **The defect run should extend
   finding 3 to cover the three voting ensembles.**
3. **The voting ensembles are dominated by the results array.** Each of about fifty module results
   carries a weight of 0.6, against 1.5 for the forecast and trend signals and 1.0 for document
   risk, so the three primary signals contribute a few per cent of the vote. Uncalibrated, like
   every weight in this layer, and worth a line in whatever calibrates them.
4. **In the browser the voting ensembles read the previous run's results array**, because the array
   is assigned after the batch returns. The server reads this run's own. That is a deviation from
   the JavaScript and it is the defensible direction.
5. **One em dash was removed from a module's finding string** (Conservative Dominance's
   `evidence_metric`, now a colon). It had never reached a screen because the module could not run;
   the moment this run made it reachable it became user-facing text, which the standing naming rule
   covers. No arithmetic, no state name, no classification touched.
6. **This container does have a usable Chromium.** The previous run reported none and skipped
   browser verification. It is at `/opt/pw-browsers`, and the reason it looks absent is a version
   mismatch: the installed Playwright expects `chromium-1140` and the container has `1194`. Two
   things are needed, both recorded here so no session loses time on it again: pass
   `executable_path=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`, and
   use the headless shell rather than `chromium-1194/chrome-linux/chrome`, whose old headless mode
   has been removed from the binary. WebGL composites with the documented flags.
7. **The results-array composition is a choice this run made and states.** It is every module this
   run has computed so far, which is the closest server equivalent of what the browser's batch
   produced. A narrower set is arguable; it is recorded here rather than left implicit.

---

## 9. What was not done, and why

- **The Category 9 gate was not built.** Out of scope by decision, recorded above as a known
  deviation rather than quietly worked around. It remains the largest single gap between this
  platform and its own architecture.
- **No module's arithmetic was changed**, including the two defects the next run owns
  (Conservative Dominance's casing, Dempster-Shafer's treatment of ignorance). Both now execute on
  the normal path, which is the point of doing this run first: they can be fixed and tested where
  they actually run.
- **The eight disabled concept-only modules were left disabled**, two of which are among the
  fourteen. The previous run predicted this and it held exactly as predicted.
- **The participant's own export button was not changed**, consistent with the previous run's
  finding that it is reachable from the decision sequence.
- **No migration.** No column, no table. Unapplied in production and unchanged by this run: 0020,
  0021, 0022, 0023. Throwaway SQLite only; production was never inspected or queried.

---

## 10. What the next session needs

1. **The defect run can now proceed as written.** Its first two items execute on the normal path and
   can be tested where they run.
2. **Extend defect 1 to the three voting ensembles**, per finding 2 above. It is the same mechanism
   and the audit named only one of the four places it occurs.
3. **Dempster-Shafer's fix now has visible consequences.** It computes on every project, and
   `dst_combine` is shared with the category rollup, so the change needs its own regression evidence
   as `remediation_decisions_answered.md` 2.4 already requires.
4. **Nothing about the fourteen votes yet**, and nothing should until the interim voting scope is
   revisited in the validation run.
5. **Browser verification is available in this container.** See finding 6.

---

## Files changed

`server/app/simulation/signal_package.py` (new), `server/app/simulation/registry.py`,
`server/app/simulation/models_decision.py` (one display string, declared above),
`server/app/research_export.py`, `assets/js/knowledge.js`,
`server/tools/test_run3_adapter.py` (new), `server/tools/test_d1_module_inputs.py`,
this report, `T6_HANDOFF.md`.

No file outside `DEng\LinPRojectRadar` was touched. `DATABASE_URL` pointed only at throwaway
SQLite.
