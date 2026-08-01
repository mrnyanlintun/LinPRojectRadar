# Steps 1 and 2: regression fixture, and the group assignment

Branch `t13-fixture-and-taxonomy`. **Not merged, deliberately: step 2 hit its stop condition.**

Step 1 is complete and proven. Step 2 is complete as an audit and its answer is that the proposed
table does not match the code. Per the brief I have not reconciled the difference, not touched the
naming authority document, and not merged.

---

## Before anything else: the naming authority document was not attached

I asked for it at the start of the session and it was not attached, so I worked from the table
reproduced in the task. That is sufficient to verify counts and to trigger the stop condition. It
is **not** sufficient if that document also fixes the group *names*, because the names in the code
differ from the names in the table (section 2.3). Treat the naming question as open.

---

## Step 1. Regression fixture for the stored-result shape

### What existed, and why the bugs got through

The 854 checks are Python driving FastAPI's `TestClient`. They cannot render a DOM. The frontend
checks that do exist, in `test_decision_ui_t4.py`, are **source-text greps** over `index.html` and
`decision-ui.js`. A grep cannot show that the ledger draws its rows, so nine `hasSignals()` bugs and
one live `TypeError` passed a fully green suite.

`tests.html` is an in-browser harness, but it covers signal **math**: it loads `categories.js`,
`decision.js`, `sim.js` and `simulations.js`, which is the researcher-side stack, and asserts on
band thresholds.

Neither could catch a render regression. So the new harness is a sibling to `tests.html`, not an
extension of the Python suites.

### What was added

**`tests_render.html`**, at the repository root. Zero dependency, offline, 22 assertions.

The fixture is one project with a stored `computed_results` row and **no** `p.signals` blob. It
omits `signals` entirely rather than setting it empty, because an empty object would let a careless
`p.signals.cusum` read succeed one level in and hide the exact `TypeError` the harness exists to
catch.

It boots deterministically by stubbing `window.LinAuth = { init: () => false }` before `app.js`
loads. `app.js`'s `boot()` only runs the application when `LinAuth.init()` returns true, so this
gives `window.LinApp` with no network, no portfolio fetch, and no UI.

It loads `taxonomy.js`, not `categories.js`: taxonomy is what the participant-facing application
loads, and it reads status from the stored row rather than deriving it.

**`dev_serve.py`** now serves `tests.html` and `tests_render.html` by exact name. `app/main.py`
serves a short list of exact paths and explicitly refuses to mount `StaticFiles` at `/`
(`main.py:273`); I did not weaken that. Render never imports `dev_serve`, so no harness is reachable
in production, and the two files are named individually rather than globbed so dropping a file into
the repository root cannot make it web-reachable by accident.

**`app.js`** now exports `stateLabel`, `buildFallbackList` and `renderStatusLegend` on `LinApp`.
All three were unreachable from outside the module, which is part of why the bugs survived.

### The fail-proving loop, and which assertion caught which gate

Every gate was individually reverted, the harness re-run, and the gate restored.

| Reverted gate | Assertions that went red |
|---|---|
| `renderLedger` stored-row gate | ledger: renders category rows; ledger: awaiting panel absent |
| `renderDecisionCard` stored-row gate | decision card: state badge present; badge shows the stored status; awaiting panel absent |
| `stateLabel` stored-row gate | detail State badge: shows stored status; does not say "Awaiting ingest"; **plus** list row: word carries a colour; word is the stored status |
| `statusKey` stored-row gate | legend: counts under stored band; legend: not counted as awaiting; **plus** list row: `state-` class (after the rewrite below) |
| list row `hasStatus` gate | list row: status word carries an inline colour |
| `classifyConflict` abstention | classifyConflict: returns its abstention value; does not fall through to a specific finding (returned "Mixed early warning") |
| `classifyConflict` cusum guard | ledger: does not throw; decision card: does not throw; classifyConflict: does not throw. All three reported **"Cannot read properties of undefined (reading 'cusum')"**, which is the original live crash reproduced exactly |

`stateLabel` legitimately catches four assertions rather than two, because the list row takes its
status text from it. That is reported as observed rather than tidied.

### One assertion was vacuous and was rewritten

Reverting `statusKey` left **every list row assertion green** while silently restoring the muted
`state-empty` class. The row's inline colour comes through `hasStatus` and `stateLabel`; its
`state-` CSS class comes from `statusKey`, a different path that nothing asserted on.

A new assertion was added, `list row: state- class reflects the stored status, not state-empty`, and
confirmed red against the still-reverted gate before the gate was restored. Reporting this rather
than quietly correcting it, per the standing rule.

### Found while doing it: a tenth instance, and it is the root

The harness failed on first run with `hasSignals is not defined`, and the list row silently fell
back to its minimal catch-block form.

**`statusKey()` still had the legacy gate.** The T12 legend fix had added a *parallel*
`storedStatusKey()` helper beside it instead of correcting it, so the legend read the stored row
while everything else kept reading `"empty"`.

It drives eight call sites, and they are not cosmetic:

- `proxyHealth()` places the project's **radar blip** by it, so an analysed project sat on the
  neutral mid-ring instead of its real band
- `statusColorFor()` colours **markers** by it
- the project list row takes its `state-` CSS class from it
- the map card pill and three other surfaces

Fixed at the root, and the duplicate `storedStatusKey()` removed so the legend and everything else
now share one path. In the real application `store.js` defines `hasSignals`, so this never threw
there; it silently returned the wrong band.

### Step 1 guarantees

| Guarantee | Status |
|---|---|
| Fixture carries a stored result and no legacy blob | **Verified.** Asserted explicitly as checks 1 to 3 |
| Signal ledger renders its category rows | **Verified**, and proven failable |
| Governance decision card renders a state | **Verified**, and proven failable |
| Detail page State badge renders | **Verified**, and proven failable |
| List row is coloured | **Verified**, and proven failable |
| Legend counts the project as analysed | **Verified**, and proven failable |
| `classifyConflict` abstains rather than throwing or inventing | **Verified**, both halves proven failable separately |
| Every assertion proven able to fail | **Verified**, one found vacuous and rewritten |
| 854 server checks unchanged | **Verified**, 854 across 17 suites |

`tests_render.html`: **22/22**. Server suites: **854/854 across 17**.

---

## Step 2. Group assignment: STOP CONDITION TRIGGERED

### The answer

The proposed table matches the **CSV declaration**. It does not match the **code**.

| Group | Name in code | Proposed | CSV | Code |
|---|---|---|---|---|
| A | `Project Health` | 53 | 53 | **52** |
| B | `Recommendation & Governance` | 36 | 36 | 36 |
| C | `Data & Evidence Health` | 7 | 7 | 7 |
| D | `Portfolio Level` | 5 | 5 | 5 |
| | **Total** | **101** | **101** | **100** |

Counted directly from `VALIDATED` (`models.py:278`, 95 after `_register_extensions`) plus
`PORTFOLIO_VALIDATED` (`portfolio.py:36`, 5), cross-referenced against the CSV. No id is registered
twice, and no registered id is missing from the CSV.

### Is the CSV current? Yes, with exactly one exception

`p0-baseline/module_renumbering_map.csv` is **not** a historical artifact. `registry.py:22` and
`:35-36` open and parse it at runtime, on every `group_of`, `run_module` and `run_all` call, with no
caching. If it were missing, every computation would raise `FileNotFoundError`.

103 rows, 2 marked `RETIRED` (old 1.3 Document Risk Extraction, old 3.2 DSM Rework Propagation),
filtered out at `registry.py:37`. 101 live. **No retired id survives into the live set.**

The single divergence: **`A4.1` is declared in the CSV and is not registered in code.**
`grep -rn "A4\.1\b" server/app/simulation/*.py` returns nothing; the document extension dict starts
at `A4.2` (`models_doc.py:647`). `registry.py:76-80` refuses it by name rather than omitting it
silently.

I did not regenerate the CSV, because it is current. The disagreement is not staleness.

### The ambiguity, unresolved as instructed

**`A4.1 Document Risk Score` is ambiguous and I have not assigned it.**

It is a *signal* but not a *computation the analytical server performs*. `extraction_merge.py:106-108`
states this as intent, not oversight: the value is emitted by the extraction model itself and copied
through, and the registry raises `MissingModuleError` for it.

So "Group A has 53" is true of the declared registry, and "Group A has 52" is true of what the
server computes. Both are defensible and **the code does not choose between them.** That choice
determines what every surface says after the step 4 sweep, which is why it is yours.

### Three further anomalies, reported not fixed

1. **`unported_modules()` (`registry.py:49-51`) conflates two different things.** It is
   `set(registry_index()) - set(VALIDATED)`, so it counts D1.1 to D1.5 as unported even though they
   are implemented in `portfolio.py`. It reports 6 unported; exactly 1 genuinely is.
2. **`test_simulation.py:49-50` asserts a tautology.** It checks
   `len(unported_modules()) == 101 - len(VALIDATED)`, which is true by the definitions above
   regardless of whether A4.1 exists. It cannot detect the gap it appears to guard. This is a sixth
   vacuous check, alongside the five already found.
3. **Group names use an ampersand in the source**, not the word "and": `Recommendation & Governance`
   and `Data & Evidence Health`. The proposed table spells both with "and". Since step 4 rewrites
   every surface against this authority, the spelling needs deciding too.

### Why there is no artifact file

The brief asks for a checked artifact mapping every registered computation to exactly one group,
passing three checks. It cannot pass: the counts do not match, and one computation is ambiguous.

I did not commit a group-assignment file anyway. An artifact asserting an assignment is precisely
what is in dispute, and a file of that name sitting in the repository would be read as settled by
the next session even with a caveat inside it. The verified per-group tally is in the table above,
regenerable from the code in one command, and that is the evidence without the false authority.

---

## What I did not do

- Did not update the naming authority document, reconcile the count, or adjust any group.
- Did not merge. The branch is left for your decision.
- Did not start steps 3 to 10: no content rewrite, no PCEIF removal, no em dash sweep.
- Did not touch `server/app/simulation/`.

## For the next session

1. **The A4.1 decision is the gate on step 4.** Until it is made, no sweep should rewrite a count.
2. `tests_render.html` runs at `http://127.0.0.1:8010/tests_render.html` with the dev server up. Run
   it after any change to `app.js`, `detail.js`, `decision.js` or `taxonomy.js`. It is not part of
   the 854 and will not run itself.
3. The `statusKey()` fix in this branch is a real behaviour change beyond the reported bug list:
   radar blip placement and marker colours were wrong for analysed projects, not just the legend.
4. `test_simulation.py:49-50` should be rewritten to compare against an explicit expected set.
