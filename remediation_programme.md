# Opus Gubernatio — Remediation Programme

From the external arithmetic audit of 2026-08-10:
`PCEIF_Claude_Module_Arithmetic_Audit_2026-08-10.md` and
`PCEIF_Claude_Arithmetic_Status_and_Remediation_Matrix_2026-08-10.md`.

**Verdict: 0 of 101 reviewed units approved for project-impacting status.**

Triage: CORE 7, PROXY 30, FIX 15, WIRE 14, REBUILD 26, WITHDRAW 8, EXTERNAL 1.

Status key: OPEN / RUNNING / DONE. Update after every session report.

---

## Run 1 — disable and relabel — Sonnet

DONE 2026-08-10. `REPORT_2026-08-10_run1-disable-and-relabel.md`.

**Disable the 8 concept-only modules.** Non-executable in production, non-voting, excluded from
fusion and rollups.

1. Parametric Cost Index
2. Plithogenic Sets
3. Quantum Probability
4. Hypersoft Sets
5. Multi-Objective Optimization
6. Linear Programming
7. Decision Sensitivity Matrix
8. Pareto Frontier Analysis

**Relabel the 30 proxies** to what each actually computes. Advisory, non-voting, accurate label on
every surface: page, export, API.

| # | Module | What it actually computes, per the audit |
|---|---|---|
| 1 | CUSUM Anomaly Monitor | Two-sided CUSUM on real SPI history; k, H, sigma floor and Amber band uncalibrated |
| 2 | Bayesian EAC | Normal-normal updating with designed constant variances, not a governed Bayesian model |
| 3 | Kalman Filter SPI Smoother | Scalar Kalman recursion with fixed Q and R, short history, no calibrated filtering claim |
| 4 | Budget Execution Rate | An expenditure-versus-progress control ratio, not a standardised statistical test |
| 5 | Regression to Mean CPI | Fixed 50 per cent shrinkage toward historical mean; coefficient not estimated |
| 6 | Schedule Compression Index | Custom compression ratio; no network-based crashing model or calibrated bands |
| 7 | S-Curve Deviation | A single planned versus actual snapshot, not a longitudinal S-curve analysis |
| 8 | Milestone Trend Analysis | Simplified shift summary on real milestone history, bands uncalibrated |
| 9 | Labor Productivity Index | A labour-hours ratio, not an earned-output productivity model |
| 10 | Overhead Absorption Rate | Transparent ratio; validity depends on whether indirect plan is total or period-to-date |
| 11 | Analogous Estimating Ratio | An analogous-cost ratio; project selection, normalisation and adaptation ungoverned |
| 12 | Inflation Adjustment Index | A material-escalation ratio with no external price index, time base or geography |
| 13 | Weather Day Impact | Lost-days over available-float proxy with fallback behaviour and ungoverned bands |
| 14 | Change Order Frequency | Contract growth plus raw count; no time or exposure denominator |
| 15 | Dispute Escalation Index | Ad hoc 0.3 / 0.3 / 0.4 weighted sum; weights and dependence uncalibrated |
| 16 | Subcontractor Performance | Uses a precomputed compliance score; provenance and construction unvalidated |
| 17 | Sensitivity Analysis | Local CPI perturbation plus deviations, not calibrated multivariate sensitivity |
| 18 | Tornado Risk Ranking | Ranks four present-state deviations; no outcome-response ranges estimated |
| 19 | Pythagorean Fuzzy Sets | Hard-coded transformations of raw CPI, SPI and document risk |
| 20 | Picture Fuzzy Sets | Hard-coded memberships consuming raw metrics; no calibration evidenced |
| 21 | Hesitant Fuzzy Sets | Designed perturbations, not elicited or observed hesitant assessments |
| 22 | Type-2 Fuzzy Sets | Membership intervals are designed constants |
| 23 | Maximum Entropy | Entropy over designed state probabilities; measures the lookup, not the project |
| 24 | Possibility Theory | Fixed mappings from raw metrics; no governed possibility distribution |
| 25 | Spherical Fuzzy Sets | Algebraically bounded but fixed memberships on raw unqualified inputs |
| 26 | Fermatean Fuzzy Sets | Formula-shaped with designed memberships, no empirical or elicitation basis |
| 27 | Contract Modification Frequency | Raw modification count; not a frequency without a denominator |
| 28 | Constraint Satisfaction Analysis | An explainable four-rule checklist, not a constraint-satisfaction solver |
| 29 | What-If Scenario Matrix | Four deterministic EAC variants; not an action-by-scenario matrix or optimiser |
| 30 | Portfolio Outlier Detection | Empirical CPI and SPI percentile rank; small-n behaviour and bands unvalidated |

This is the finding that does most damage to a defence: a canonical name claiming a method the
arithmetic does not implement. The architecture master already required exactly this, so it is
implementing the design rather than retreating from it.

**One decision is the owner's, not the prompt's:** what a user sees where the eight disabled modules
currently appear. Options are that the row disappears entirely, or the row remains with a state
saying the method is not available for production use. The platform already has a not-relevant state
distinct from no-data, which may serve.

## Run 2 — the 15 defects — Opus

DONE 2026-08-11. Recorded in `T6_HANDOFF.md` under "the fifteen defects". All fifteen fixed, none
disabled: nine produce output on the real path and six abstain because the remedy required data the
corpus does not carry. The Dempster-Shafer fix moved project status in two of four periods on the
measured project, evidenced rather than avoided. Defect 1 was extended to the three voting
ensembles per the adapter run's handover.

1. Conservative Dominance compares lowercase strings against a capitalised vocabulary, so two Red
   inputs can return Green.
2. Dempster-Shafer treats ignorance as a disjoint singleton, so Θ becomes conflict.
3. Quality Compliance Index produces negative scores when failed exceeds inspected.
4. Procurement Lead Time ratio can reach 1.8 through double counting.
5. Cost Risk P80 divides by zero when CPI is zero.
6. Signal Trajectory Classifier divides by observations rather than intervals.
7. Cross-project Pattern Detector cannot return Green whenever any match exists.
8. Anomaly Score injects a constant 0.5 placeholder.
9. Monte Carlo EAC falls back to DEMO_BAC = 100 on a falsy BAC.
10. Float Consumption Rate fabricates 50 per cent completion when absent.
11. NCR Rate: undefined cohort or backlog denominator.
12. Weather Day Impact: fabricated fallbacks.
13. Scenario Modeling: unguarded EVM domains.
14. Contractor Performance Score: ignores an available quality rating.
15. Environmental Compliance Rate: synthetic `100 - 5 × issues` score.

## Run 3 — the adapter — Opus

DONE 2026-08-11. `REPORT_2026-08-11_run2-adapter.md`. Twelve of the fourteen compute on the normal
path; the other two are the concept-only pair Run 1 disabled. Category 9 remains a recorded
deviation: the fourteen consume unqualified signals.

**One flat-to-nested adapter** so the 14 unreachable Group B modules run on the normal path, with
reachability tests on `documents.run_and_store`.

The normal path passes a flat `signalInputs` dictionary. B1.1 to B1.4, B2.1 to B2.9 and B3.1 expect
nested assembled objects, so they abstain on every real run. One adapter, not fourteen jobs.

## Run 4 — validate the seven — Opus

DONE 2026-08-11. `REPORT_2026-08-11_run4-validate-seven.md`. **THE PLATFORM IS FROZEN FROM THIS
RUN: no algorithm changes, no threshold changes, no band changes.**

**Two of the seven vote, not seven.** TCPI and Variance at Completion have band boundaries a
published source specifies (PMI's definitions of both measures, plus Christensen and Heise 1993
on cumulative cost index stability, applied by an inference stated beside the band). The other
five have guards and passing boundary tests and no source for their numbers, so they stay
non-voting. No citation was stretched.

**The eighth HOLD module is the Document Risk Score, and it is not CORE.** It is a value the
extraction model supplies, not a measure this platform computes; its validation question is
precision and recall of a text-scoring model on labelled documents, which is the evidence the
programme records as absent; and its description is already known not to match its implementation.
Non-voting, and unable to vote by construction.

**Consequences that belong in the methods chapter.** Project status is now a cost statement:
both voting measures sit in one category, so schedule, contingency and document-derived condition
no longer contribute. Project-level conflict is structurally zero, meaning "one source" rather
than "sources agree".

The only seven the audit calls CORE. Each needs a sourced band, an abstention guard where a
denominator can be zero, and boundary tests.

1. TCPI
2. Variance at Completion
3. Look-Ahead Schedule Health
4. Contingency Burn Rate
5. Material Cost Variance
6. RFI Velocity
7. Submittal Rejection Rate

## Run 5 — regenerate the Group A export — Sonnet

OPEN

The export wrote 43 sections while its report claimed 52, omitting A4.2 through A4.10. Regenerate
from the registry, and make the exporter compare emitted IDs against expected before declaring
success.

Also: the two export report files are byte-identical duplicates, not independent reports.

---

## Deferred, and deliberately

**The 26 REBUILD items are a research programme, not a fix.** Each needs data the platform has never
held: an activity network with dependencies and three-point durations, a location and crew
production dataset, a multi-project training population. None of it exists in the document sets, and
generating it is a second corpus programme.

**Document Risk Score** needs a separate extraction-model audit with labelled holdout documents:
precision, recall, false-positive and false-negative rates, calibration, provenance.

**Category 9 as a two-pass gate** is required by the architecture and not implemented. Larger than
run 3 and it depends on the qualified-signal package existing.

---

## Context worth carrying

The architecture master v0.2 already required proxy labels where the defining structures are absent,
Category 9 run twice, and lineage groups so correlated outputs are not counted as independent
evidence. **The audit is largely finding that the code never implemented its own design.** That is a
better position than needing new design.

It also settles the count question: 96 project-level in the current registry, after removing a
duplicate Category 1 document-risk module, removing a duplicate Category 3 DSM module, and
separating the portfolio layer. 96 and 100 are both right in different senses, which is why four
different numbers appear in the code.

**What the praxis actually needs.** The study measures how project managers respond to AI decision
support. It does not require the support to be state of the art. It requires it to be honest about
what it is and identical across participants. Seven validated measures, thirty accurately labelled
proxies, fifteen defects fixed, eight disabled, and the platform saying plainly which is which, is
defensible now. The full programme is a year that is not available before submission.

---

# Part 2 — Full working context

Everything a fresh session needs. Nothing below is optional background.

## The platform

**Opus Gubernatio**, descriptor Project Decision Support. FastAPI and Postgres on Render at
`https://linprojectradar.onrender.com`. Frontend is vendored JavaScript, no build step. Repository
`https://github.com/mrnyanlintun/LinPRojectRadar`, local path
`C:\Users\NTUN\OneDrive - Arora Engineers, LLC\DEng\LinPRojectRadar`.

It is the instrument for a D.Eng. praxis at GWU: a controlled repeated-measures study of how project
managers respond to AI decision support. The factor is `post_ai`, comparing a locked preliminary
judgment against the final decision. There is deliberately no framework name.

**Standing description, quoted verbatim wherever it appears:** "Opus Gubernatio analyses the
documents a project produces each reporting period and presents a recommendation that a project
manager records a decision against, keeping the evidence, the recommendation, and the judgment as
one reproducible record."

## Working conventions, all of them

**Permissions.** Claude Code works freely under `DEng`, including commit, merge and push without
asking. Push to `main` triggers a Render deploy. Never delete or move anything outside
`DEng\LinPRojectRadar`, since the parent is OneDrive and holds unrelated doctoral work. Never point
`DATABASE_URL` at production Postgres. Never modify anything under `server/app/simulation/` unless a
task grants a named exception.

**Sequential only.** Two sessions share one working directory, so a reset in one wipes uncommitted
work in the other regardless of which files each touches. This has happened. `T6_HANDOFF.md` is the
file that collides.

**Merging.** Sessions merge their own work rather than leaving a draft PR. Exception: a task with an
explicit stop condition leaves the branch unmerged and says so.

**Reports.** Every task writes `REPORT_<yyyy-mm-dd>_<task>.md` at the repository root and commits it,
covering what was done, what was not and why, every guarantee marked verified or not met, incidental
findings, and what the next session needs. Update `T6_HANDOFF.md`, which is now `# <date> — <task>`
with no numbering.

**Migrations.** Written and run against throwaway SQLite only. Production migrations are applied by
hand in the Render Shell: `alembic upgrade head`. A push that assumed an unapplied schema took
sign-in down once.

**Prompts to Claude Code** are delivered as copy-ready files, never pasted inline.

## Container quirks that have each cost a session

- `preview_start` resolves `launch.json` from `DEng\Demo`, a dead repository, and silently serves the
  wrong app. The tell is `api.js` and `boot.js` in sources with zero `.page` sections in the DOM.
- **Headless Chromium CAN composite WebGL** with `--use-gl=swiftshader --enable-webgl
  --ignore-gpu-blocklist`. Two sessions wrongly believed it could not and asserted against a fake.
- `window.confirm` returns false, so a confirm-gated action silently no-ops here **and in any browser
  that suppresses dialogs**.
- The proxy blackholes the parser-blocking Google SSO script; abort that request when driving the DOM.
- `PYTHONIOENCODING=utf-8` is required or `test_simulation.py` dies printing no result line.
- Suppress CSS transitions before reading computed styles, or a frozen timeline returns the previous
  theme's values.
- Run the server suite with a fresh database per test file. `run_all_suites.sh` once ran every suite
  with a non-existent interpreter and reported "no RESULT line" rather than failing.
- OneDrive sync lag has made files appear deleted when they were not.

## Test discipline, learned the hard way

**A test that cannot fail is worse than no test.** Prove every check can fail by injecting the fault,
then restore and recheck the baseline after every single fault.

Failure modes found repeatedly in this project:

1. A check that crashes rather than fails prints no result line and looks clean.
2. An injection that silently fails to apply reports a false clean.
3. A fixture that builds state by a route the application does not take. The render fixture never
   crossed the API; the chart suite asserted against a hand-maintained JavaScript copy of the server
   logic.
4. A test asserting the defect's own sentence verbatim. **Three suites turned out to encode a defect
   as expected behaviour and had passed for months.** If a test goes red, establish whether it
   protects a property or records the old defect.
5. A check asserting what `index.html` loads is vacuous in `tests_render.html`, which never loads it.

Roughly a dozen vacuous checks have been found, every one by injection and none by review.

## Naming rules

- No module ids or numbers in user-facing text. Groups by name and purpose.
- No em dashes in user-facing text.
- User-facing text uses "and", not the ampersand the code constants use. Do not rename code
  constants.
- PCEIF and PDAF are retired names. `PCEIF_*` survives only as an internal file prefix.
- Do not describe capability the platform does not have.
- Do not adopt liability or consent language unilaterally.

**Retired string keys have killed six things**, each found separately: `cat1..cat11` keys after ids
became `a1..d1` killed the Signal Network and the decision card's action plan; `submittal` after the
type became `submittal_register` killed a diagram row; a `cat.id === "cat9"` comparison in `app.js`;
plus two more. Sweep every string key against the current vocabulary when in that code.

## Merged pull requests, in order

| PR | What it did |
|---|---|
| #196 | Judgment prose: About tab, assistant, README, disclaimers drafted |
| #197 | Disclaimer alignment across four upload panels, `test_disclaimers.py` |
| #198 | Map and globe hydration: `hydrate()` dropped location fields on slim refresh |
| #199 | Stages 7 and 8 audit, vacuity sweep, read only |
| #200 | Notice and copyright revision across nine surfaces |
| #201 | D1 implementation: twelve fabrications removed, three keys wired, eight abstaining |
| #202 | Document risk score range guard at four entry points |
| #203 | PM at project creation, admin consolidated to two tabs, unmembered gap closed |
| #204 | Storage redesign, observations store, migration 0014; then D2 malformed numerics |
| #205 | Export: selector, four sheets, `analysis_long`, determinism fix |
| #206 | Logo sweep animation across six locations |
| #207 | Training run 1: flag, gate, data isolation |
| #208 | Training run 2: the deterministic loop |
| #209 | Training run 3: effect-table corrections, discrete events, narration |
| #210 | Training run 4: contract regimes, debrief, disclaimer |
| #211 | Training run 5: signal ledger, full recommendation, naming fixes |
| #212 | Training upgrade run 1: quality thread |
| #213 | Training upgrade run 2: resources thread and the spacing rule |
| #214 | Files tab: Arora J-Drive tree, automatic filing, migration 0016 |
| #215 | Signal display: `detail.js` never called `projectresults`; map zoom |
| #216 | Charts and portfolio: three dead charts removed, lists consolidated |
| #217 | Six dead surfaces wired to the primed row, extraction display, admin dropdowns |
| #218 | Map and globe fly to the selected project |
| #219 | Ledger calculations rendered on every module row |
| #220 | Period series across reporting periods |
| #221 | Courses of action: operational redaction removed |
| #222 | Unbounded schedule rows, upload results, all-periods compute |
| #223 | Project delete, admin only |
| #224 | Schedule activity table elision, 500 rows cost the same as 29 |
| #225 | Archived Projects modal: delete beside restore, archive filtering |
| #226 | Module source export to `code_audit/` |

## Defects fixed, and what each taught

**D1, twelve fabrication paths.** Twelve keys nothing could write. CUSUM synthesised its own history
from a seed and reported drift over twelve periods on a project in its first. Rough Sets returned
Amber from an empty evidence set through `len(classes) or 1`. Audit Trail Completeness returned a
permanent Red. All now abstain. `VALIDATION.md` records every one as matching the JavaScript to zero
error, which was true and meaningless: the comparison validated the port while the input contract was
broken underneath both.

**The status contradiction.** `project_status` and `lifecycle_stage` are two different questions
rendered under one word. Not a data defect, a vocabulary defect.

**The blank detail page.** `detail.js:894` referenced `populated`, deleted by the `hasSignals` sweep,
inside a template literal, so `render` threw before assigning. `showPage`'s try/catch swallowed it
and the console stayed clean. Live for two days.

**Unauthenticated writes.** All ten legacy facade actions accepted with no credential. Then
unauthenticated reads: every GET returned any project's full document. Both closed. The cause was a
fail-open guard written to keep one client working that was itself a bug.

**Append-only violations.** `w_resetsignals` and `w_save` both truncated the legacy event log.

**The storage redesign.** Both document versions reached computation and a content hash arbitrated
per field, so an RFI log revised from 10 to 12 assembled to 22. Deterministic, which is worse than
random because it reproduced.

**Extraction substitution.** The model returned the reporting period as the project baseline because
nothing forbade substitution. Fixed in the prompt: return null rather than the nearest plausible
value.

**The unbounded schedule.** A 29-activity table truncated the model's output. Rows now appear in
neither input nor output: the elision note is 352 characters at 29 rows, 353 at 500, 354 at 5000.

**Period partitioning.** 84 documents across several periods computed as one.

## Open items outside the audit

1. **The map.** Google Maps is on the project detail page, keyed by `GOOGLE_MAPS_BROWSER_KEY`, and
   works. **The portfolio Map view still uses the flat atlas** and should move to Google from the
   same key and code path. Prompt written.
2. **The globe.** Gone from the portfolio in all themes while its tab remains. Broken by a recent
   Claude Code change; which one is not established. Prompt written.
3. **Training projects appear in the portfolio** and count in its tallies. They should be filtered
   out; the Train item is already on the menu bar. Prompt written.
4. **A section navigator** on the project detail page, left side, jumping to and expanding sections.
   Prompt written.
5. **The upload modal is too narrow**, and the period picker should be a number rather than a
   calendar date. Prompt written.
6. **Cost Risk P80 and Reference Class Forecasting** both hit a stop condition: they cannot consume
   register data without changing their arithmetic, and RCF would be inverted by it since a risk
   register is the inside view.
7. **`schedule_activities` heading brittleness**, the same shape that silently dropped a time-impact
   column from the risk register.
8. **The DRAFT consent text is live in the product.** To be revised after the praxis committee.
9. **The auditor dock button** shows when the flag is off.
10. **Two dead functions** counting the whole taxonomy: `activeModuleTotal()` and `buildModuleAxes()`.
11. **Reference Class Forecasting cannot abstain** at all in its current form.
12. **PDF schedules** still take the old path and can truncate.

## Document sets

Three verified sets, four periods each, arithmetic checked and accepted: Project A design Albany NY,
Project B construction Richmond VA, Project C hybrid Columbus OH. Every document carries a canonical
title and a geocodable street address. Control reports carry one preparation date and the label
`RESEARCHER CONTROL — NOT PARTICIPANT EVIDENCE`.

**Missing types being produced by ChatGPT:** Quality Audit Report and Environmental Compliance Report
for all projects and periods, RFA or Approval Log for Projects 2 and 3. Project 1 is delivered.

**The target is fifteen sets**, three project types by five statuses, worldwide.

**Three types are correctly absent** and should read as not applicable rather than missing: Past
Performance Report, Historical Project Data, Test and Commissioning Report.

**The sets were never calibrated to a status.** ChatGPT confirmed only set-level targets were
specified, no period-level statuses, and the final audit treated those as hard-coded rather than
recomputing. The authored CPI and SPI sit between 0.94 and 1.01; the platform showed 0.673 and 0.701
and an eightieth percentile of 10,555,811 against an authored 4,835,600.

## Training mode

Five runs merged plus two upgrade runs. Operational accounts only, research refused server-side,
training data excluded from the export by construction. Effect table, discrete stop-work events,
three US contract regimes (A201, ConsensusDocs 200, Federal FAR) with real notice periods, and a
debrief that refuses to estimate a counterfactual it cannot compute honestly.

Open: the spacing rule supports exactly three live secondary threads and run 4 needs three; a
reusable browser-drive fixture should be built before the next thread run; `ev_factor *=
crew_adequacy` is a multiplier and compounds, so an error in it is a wrong trajectory.

## Settled decisions, do not re-raise

- The site starts completely fresh. No projects or documents to migrate. Backfills and production
  data queries are permanently moot.
- Only registers and logs arrive. Individual RFIs, submittals and RFAs route to unmapped.
- Change orders arrive already executed; approval happens outside the platform.
- OAC minutes are dated meeting records; correspondence is individual instruments.
- The `fairnessSensitive` gate is removed, not wired.
- Admin means the owner personally. There is no separate ResearchAdmin role.
- Delete removes everything; archive is retention before deletion.
- Recommendations are generated at display time on all three surfaces, including research.
- Fairbanks is the default theme; research participants are pinned to New York.

## The 8/7 incident

A prompt was written for project delete without knowing what it was doing: it invented the placement
"admin only, on the administration surface", never asked where the control should go, and did not
require the report to state placement, so afterwards nobody could say where it was. It turned out to
be on Project Membership; it belonged in the Archived Projects modal.

**Rules from it:** never decide the placement of a user-facing control silently, ask first; every
prompt adding a control must require the report to state where it was placed; act on what the owner
reports rather than interrogating them about it.

---

# Part 3 — The audit findings in full

Reproduced so this file stands alone. Source: the external arithmetic audit of 2026-08-10 and its
status and remediation matrix. Release disposition: **FAIL — block production status,
recommendation, governance and compliance use until the P0 findings are remediated and validated.**

## Audit scorecard

| Area | Result | Evidence |
|---|---|---|
| Server-path reachability | FAIL | 14 registered Group B modules require nested objects the normal path never constructs |
| Category 9 eligibility gate | FAIL | Group C is excluded from project status, but its results do not gate downstream execution |
| Arithmetic domain safety | FAIL | Zero-division paths, negative scores, ratios above 1, stale presence gates, changing composite denominators |
| Named-method fidelity | FAIL | Labels describe methods not present: Earned Schedule, SRA and CRA P80, Critical Path, Queueing, ABM, DES, MOO, LP, Pareto |
| Fusion and evidence combination | FAIL | Unknown combined as a disjoint singleton; correlated outputs multiplied as independent evidence |
| Threshold and weight calibration | FAIL | 96 of 96 parameter records uncalibrated and blank |
| Legacy parity and reproducibility | PARTIAL PASS | Seeded stochastic parity and deterministic cutoffs are strengths, but parity is not validity |
| Supplied audit-package integrity | FAIL | Group A says 52 modules, contains 43; the two report files are byte-identical duplicates |

## The ten P0 release blockers

1. **Fourteen registered modules are unreachable.** B1.1 to B1.4, B2.1 to B2.9 and B3.1 require
   nested assembled signals; extraction and `documents.py` supply a flat dictionary. A normal run
   returns at most 81 of 95 registered arithmetic modules.
2. **Category 9 is not a gate.** `run_all` executes modules independently and `compute_project`
   merely excludes Group C from the vote, so low-quality evidence feeds synthesis and governance.
3. **Conservative Dominance is case-broken.** Compares exact lowercase strings against a capitalised
   vocabulary, so two Red signals can produce Green.
4. **Dempster-Shafer is not Dempster's rule over ignorance.** Unknown is treated as a mutually
   exclusive singleton, so ignorance becomes conflict.
5. **Correlated evidence is multiplied repeatedly.** No lineage or dependence control; ten identical
   Green masses yield Green belief about 0.9999999999.
6. **Deterministic constants masquerade as project analytics.** RCF always +38 per cent and Red; DSM
   always 2.72 and Amber; regret always 11, 5, 8.
7. **Named methods are absent.** Earned Schedule, SRA and CRA P80, Critical Path Index, Queueing,
   ABM, DES, MOO, LP, Pareto.
8. **Concept-only modules execute and can be fused.**
9. **Domain and denominator failures.** CPI and SPI zero division, negative quality scores,
   procurement ratio 1.8, portfolio trend divisor error.
10. **No approved threshold or weight set exists.** All parameter rows blank and uncalibrated.

## Production re-entry acceptance gate

A module may perform its role only when: the normal path supplies its declared input contract and it
is reachable; the implementation matches the canonical name or every surface uses an approved
narrower label; invalid, missing, stale or out-of-domain inputs cause explicit abstention;
thresholds and weights are versioned, sourced, calibrated, approved and monitored; known-answer,
boundary, metamorphic, reachability and lineage tests pass; false-positive and false-negative
performance is measured on labelled holdout cases; Category 9 qualification and the human-authority
boundary are enforced end to end.

**Arithmetic correctness alone is insufficient. Literature support alone is insufficient. A
successful test on a bypass path is insufficient.**

## Activation states the auditor requires

`ENABLED_QUALIFIED`, `ADVISORY_ONLY`, `SHADOW_VALIDATION`, `RESEARCH_ONLY`, `DISABLED_UNSAFE`,
`ABSTAINED`. Re-entry is layer-specific: permission to enter the qualified-signal package does not
grant permission to combine, to issue a review flag, or to structure options.
