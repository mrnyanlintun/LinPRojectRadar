# Training mode, run 5: module detail, recommendation depth, two naming fixes

2026-08-04. Branched from `origin/main` at `6b7eec8`, with runs 1 to 4 all merged (#207 to
#210). No migration; nothing under `server/app/simulation/` modified. Production still lacks
0018 and 0019, unchanged by this run.

## The recommendation, quoted in full, as it renders

Period one, AIA A201-2017, exacting conditions, standard facility, 12,000,000 dollar contract.
Read back from the DOM in a browser, not reconstructed:

> **Serve notice of claim for the unforeseen utility conflict**
>
> **What** — Serve written notice of claim for the unforeseen utility conflict, with the
> current cost record attached, for an estimated 180,000 dollars.
>
> **Why** — Cost performance stands at 1.0 and schedule performance at 1.0, with 12 days of
> float remaining; 11 days remain of the 21 day period in Section 15.1.3.1. Notice now
> preserves the entitlement whatever the final quantum proves.
>
> **Who acts** — The project manager prepares and signs the notice; the project executive is
> informed, not asked. Waiting for an executive decision spends days the window does not have.
>
> **To whom** — the architect and the owner's representative
>
> **By what means** — certified or registered mail, or a courier with proof of delivery, as
> Article 15 requires for a claim. Email is not service.
>
> **Next step** — Serve the notice by 2026-02-04; the period closes the window after that.
>
> **By when** — 2026-02-04

Every figure is the state's own: `180,000` is `dispute.estimated_cost`, `1.0`/`1.0` are
`ev/ac` and `ev/pv` at the engine's own rounding, `12` is `float_total_days -
float_consumed_days`, `11` and `21` come from `notice_position`, and `2026-02-04` is the
period calendar's decision day plus the days remaining. Asserted field by field against the
state in the same payload, so the screen cannot show two different numbers.

It changes when the state changes. Once the window closes it stops recommending a notice and
recommends closing the matter out from contingency instead. The service route differs by form:
ConsensusDocs carries the second step (documentation within 21 days of the notice, Section
8.4); FAR goes to the Contracting Officer, reasons from the cost lookback rather than a bar,
and raises certification at 100,000 dollars.

### How it is allowed to be wrong

It follows one fixed policy, `entitlement first, maximal correction`, carried on the payload as
`policy` so the bias is inspectable. That policy is confident, defensible, and **not always the
best call**: it recommends serving notice on any live matter regardless of size, so a 5,000
dollar impact under a collaborative owner still draws a formal claim recommendation when
absorbing it is cheaper and better for the relationship. During a stoppage it always recommends
the full correction package, even where float is rich enough to make the minimal response
arguably economic. That is the classic contracts-first habit, and a trainee who follows it
every time is not thinking. A check exercises exactly that case.

**Nothing on the rendered surface hedges.** No "this may be wrong", no confidence score. An
oracle that announces its own unreliability is no longer something the trainee has to weigh,
and weighing it is the exercise. The fallibility is disclosed here and in the policy field, to
you, not to them.

## A measured correction: the category rollup is not worst-status-wins

The brief asks to show "which one drove the category's status under worst-status-wins".
**The platform does not do worst-status-wins.** `dst_fuse` (simulation/fusion.py) is
Dempster-Shafer belief combination with a Red source applied at 1.5x, and the category status
is the highest-belief band. Measured across a full ten period run: the category status differs
from its worst contributor in **47 of 80 categories**, including categories where a Red
contributor fuses to Green:

| category | contributors | worst | fused |
|---|---|---|---|
| Cost Risk | Red, Green, Green, Green | Red | **Green** |
| Data Integrity | Green, Green, Red, Green, Green | Red | **Green** |
| Schedule Performance | Amber, Yellow, Green ×6 | Amber | **Green** |

So a display that named a "driver under worst-status-wins" would teach a falsehood about the
instrument. What the ledger does instead:

- names the **most severe contributor** as the most severe contributor, which is true and is
  what a PM scans for;
- and where the category status differs from it, says so in place: *"Combined from 8
  computations by evidence combination, not by taking the worst: PERT Network Criticality
  reports Amber."*

That divergence line is now the most instructive thing on the screen, and it is asserted by
checks in both halves so it cannot quietly regress into an implied maximum.

## Part 1: the two naming fixes

**Module ids are gone from the training surface.** The signals table rendered the raw category
key (`A1`, `A2`, `C1`) and the raw group letter. It now renders through the platform's own
name tables at every level: group by purpose (`Project Health`, `Data & Evidence Health`),
category by purpose (`Cost & EVM Performance`, `Cost Risk`), computation by name (`Monte Carlo
EAC`, `Reference Class Forecasting`). Verified at the DOM level by a leaf-label scan over the
whole training surface, driven in a browser: zero ids.

**The stale line is removed.** "This build does not yet generate one" is gone from
`index.html`; a check asserts its absence and that the training page itself survived.

## Part 2: the chain, through the platform's own render path

Reused, not rebuilt. `workspace.js`'s project detail builder was extracted as
`buildProjectDetailHtml(result, opts)` and exported; training mode calls it. Same name tables,
same row markup, same status dots, same provenance footer. The trainee is reading the
instrument they will actually use.

The drill-down was added **to that shared builder** rather than to training, so it is a
property of the instrument. `opts.expandable` renders each category as a disclosure carrying
its contributors, each with its own evidence output; `opts.abstained` renders the abstentions.
Read back from the browser, one category expanded:

```
  [value]    Monte Carlo EAC (most severe contributor)  P80 EAC 12000000 vs BAC 12000000 (+0.0%); 5000 iterations
  [value]    ICE Ratio          ICE ratio: 1 (CPI-EAC $12,000,000 vs parametric $12,000,000)
  [value]    Earned Schedule    ES SPI(t): 1
  [value]    TCPI               TCPI: 1, achievable to finish within budget
  [value]    Variance at Completion   VAC: $0 under budget (0%)
  [value]    Budget Execution Rate    Budget execution rate: 1 (spending on plan)
  [abstains] Regression to Mean CPI   abstained: no usable input this period
  [abstains] CUSUM Anomaly Monitor    abstained: no usable input this period
  [abstains] Bayesian EAC             abstained: no usable input this period
  [abstains] Kalman Filter SPI Smoother   abstained: no usable input this period
  [abstains] ARIMA CPI Forecast       abstained: no usable input this period
```

**An abstention is a named absence.** No value, no colour, **no status dot** — asserted by
counting dots on abstaining rows in the real DOM (zero). The abstention set is derived from the
simulation registry server-side: a registered computation that produced no result, excluding
unported ones (`A4.1`) and excluding group D, whose exclusion is structural (the registry
refuses it on a single-project path) rather than a per-period abstention. Group C's exclusion
from project status is rendered as "does not contribute to project status", not left to
inference.

The default (non-expandable) rendering is byte-unchanged, so the real project detail panel is
untouched and its 70 checks still pass. The drill-down is available there by passing one flag;
enabling it on that surface is a product decision I did not make unilaterally inside a training
task.

## Verify

**`server/tools/test_training_detail.py`, 65 checks**, plus **17 new DOM checks in
`tests_render.html` group 10**, which renders the real builder with a fixture and reads the
text back. Full server suite **1898/1898 across 35 suites**. `tests.html` 51/51.
`tests_render.html` **80/81 — the single red is the same pre-existing gap** recorded since run
1 (the "production read path" check needing a session token pasted into that tab), identical by
name and text; the group count rose from 63 to 81 because group 10 is new.

**Eight faults, each detected, each reverted byte-identical, baseline rechecked after every
one:**

| Fault | Detected by |
|---|---|
| D1 render the raw category key again | render 78/81 (id scan names `A1 \| A3 \| C1`) |
| D2 give abstentions a status dot and colour | server 64/65, render 78/81 |
| D3 drop the most-severe marking | server 64/65, render 79/81 |
| D4 hardcode a claim figure instead of reading state | server 62/65 |
| D5 offset the days-remaining in the prose | server 64/65 |
| D6 A201 service becomes "by email" | server 64/65 |
| D7 restore the stale line | server 64/65 |
| D8 stop reporting abstentions | server 63/65 |

**Three defects in my own verification, found by the campaign and fixed** — the pattern every
run since run 2 has hit:

1. **A check that could not fail.** The first id scan ran a `\b`-anchored regex over
   `host.textContent`, which concatenates labels into `"Project HealthA3show the
   computations"` — destroying the word boundaries the regex needs. It matched nothing
   regardless of content, and fault D1 walked straight past it. Rewritten to scan **leaf
   elements**, where one element is one visual label. D1 then reported `A1 | A3 | C1`.
2. **A check that matched its own prose.** The static "most severe contributor" assertion was
   satisfied by a *comment* containing that phrase, so deleting the real marker left it green
   under D3. Rewritten to match the emitted markup (`ws-worst` class plus the literal). This is
   the same failure the handoff records from the notices work.
3. **A false positive in the detector.** The browser drive flagged `AIA A201-2017` — the
   contract form name — because `[A-D]\d+` matches `A201`. A category id is a letter plus
   **exactly one** digit, so the pattern now disqualifies a second digit. Verified against
   `AIA A201-2017`, `ConsensusDocs 200`, `Section 15.1.3.1` and `FAR 52.243-4(d)` (all clean)
   versus `Cost Risk A3` and `A1.1` (both caught). Without this the check would have fired on
   every legitimate mention of the governing contract.

**One defect of my own in the product**, caught by the same sweep: the "most severe
contributor" marker I first wrote used an em dash, which `NAMING_AUTHORITY.md` forbids in
user-facing text. It is now a parenthetical, and a check asserts that no string the detail
*emits* carries an em dash — scoped to quoted literals, because a first version of that check
went red on an em dash inside a comment, which renders to nobody. (Pre-existing em dashes in
`workspace.js` are its null-value placeholder `"—"`, untouched and out of scope.)

## Still open

Unchanged by this run: roadmap items 1 to 3 (the designed figures await your correction), item
14 (A201 and ConsensusDocs periods still rest on law-firm summaries, not the licensed
documents), items 16 to 18 (deferred deliberately), and **production migrations 0018 and 0019
before the first training run**.

New, and yours to decide: whether the category drill-down should be enabled on the real project
detail panel, where it is one flag away.
