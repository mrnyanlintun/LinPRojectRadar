# Chart-data and abstention suites: both findings checked, neither stands

**No test was rebuilt and no behaviour was changed, because neither defect exists.** This report
is the evidence for that, not an account of work avoided.

The brief asked me to rebuild two suites that "assert things that cannot fail" and to stop and
report if the premise turned out to be wrong. It did, in both cases, so this is that report.

The brief also says both findings come from `REPORT_2026-08-02_full-audit-part2.md`. The file is
`REPORT_2026-08-03_full-audit-part2.md` (same date slip as the previous brief). Searching it:
**"abstention" appears zero times, `_result_view` appears zero times, and the only match for
"chart" is `charts3d.js` in an em-dash count table.** Part 2's findings were the theme contrast
token list, the unasserted Arora folder names, the dual-dialect migration trap, and the 20 suites
with no crash wrapper. Neither of these two findings is among them.

That alone would not settle it, since a real defect can exist whether or not a report named it.
So both were checked against the code by execution.

---

## Finding A: the chart-data suite does not exist

Searched the whole repository, excluding `.venv` and `node_modules`:

| Searched for | Result |
|---|---|
| A JavaScript reimplementation of `_result_view` | **None.** Zero matches for `_result_view` or `resultView` in any `.js` or `.html` file |
| A chart-data suite | **None.** No test file mentions charts |
| Any assertion on `spi` / `cpi` reaching a chart | **None.** The only `spi`/`cpi` mention in either harness is `cpi: null, spi: null` inside one fixture, and nothing asserts on them |
| "ensemble scatter" | Exists only as `ensembleTally` / `ensembleHtml` in `assets/js/detail.js`, a render function. **No test covers it** |
| `chartData` | Appears only in `assets/js/deepdive.js`, which `index.html` does not load |

The complete test inventory is 30 Python suites under `server/tools/` plus `tests.html` and
`tests_render.html`. There is no third harness.

### The nearest real thing, and whether it has the defect

The closest analogue is `slimOf()` at `tests_render.html:438` — a hand-written JavaScript object
mirroring a server projection, maintained beside the Python. It matches the *shape* of the
concern. It differs on every material point:

- It mirrors `slim_row`, **not** `_result_view`.
- The thing under test is `LinStore.hydratePortfolio`, a **client** function: does a background
  slim refresh clobber locally-held fields the projection cannot express (coordinates, matched
  address)? The fixture supplies the input; the client merge is the subject. That is a legitimate
  use of a fixture, not a copy of the logic standing in for the logic.
- Server output is already asserted directly. The over-the-wire group added on 2026-08-03 calls
  `listslim`, `list` and `projectresults` through the real transport and asserts the delivered
  status against an independent witness.

**Fault-proven non-vacuous.** Faulting `graftUnmodelledFields` in `assets/js/store.js` so it stops
carrying unmodelled fields forward:

```js
if (!isSlimRow(row) || !local) return merged;
return merged;  // FAULT INJECTION: stop grafting unmodelled fields
```

turned three checks red, precisely the ones that claim coordinates survive a refresh:

```
refresh: a slim row does not strip coordinates off a located project
refresh: the matched address survives too (the map note reads it)
refresh: a located project STILL produces a marker after a portfolio refresh
```

68/68 → 65/68. Restored with `git checkout --`, re-run, 68/68.

**A first attempt at this fault did not prove what I intended, and is recorded because it is the
failure mode this project keeps hitting.** I first made `hydrate` return `projects.slice()`
early. The fault applied and was live in the loaded source, but it made `hydrate` a *no-op* on
`LIN_PROJECTS` rather than a stripping operation, so the coordinate checks stayed green and a
different check went red. Had I stopped there I would have reported the coordinate checks as
vacuous, wrongly. The fault must reproduce the defect's shape, not merely change the file.

One reporting correction on my own method: I probed `faultLive` by string-matching
`hydratePortfolio`'s source, which returned `false` for the second fault because the fault was in
the inner `graftUnmodelledFields`. The behavioural evidence — three specific, correct checks going
red — is the proof the fault took effect, not that string probe.

### Can the hand-maintained mirror be removed?

**No.** `slimOf()` is the input to the test, not the thing under test. Removing it removes the
ability to test client-side merge behaviour at all. There is a residual gap worth stating: if the
server's `slim_row` gained or lost a field, `slimOf()` would not notice, because it is written by
hand. For the one field that matters most, `status`, the over-the-wire group does cover it against
the live endpoint. The remaining slim fields (`cpi`, `spi`, `docRiskScore`, `simModuleCount`,
`docCount`) are asserted nowhere against the server. That is a genuine, narrow coverage gap — it
is not the defect described, and closing it was not in scope.

---

## Finding B: the abstention checks already assert the abstention

The claim was that these tests "assert the number a module produces" and "do not assert that a
module denied its inputs declines to produce a number", so a reintroduced fabrication would leave
them green.

`server/tools/test_d1_module_inputs.py` asserts the opposite of that, explicitly:

```python
def abstains(out: dict) -> bool:
    """The abstention contract from models.insufficient: no colour, and it says why."""
    return out.get("status_color") is None and out.get("insufficient_data") is True
```

- **Section 1 is the anti-vacuity control the brief asks for**, and says so in its own output:
  *"PRECONDITION: with every key present, all twelve COMPUTE. Without this, section 2's
  abstentions would prove nothing: a module that abstained for an unrelated reason would pass
  every check there."*
- **Section 2** asserts, for each of the twelve modules D1 put into the abstaining set, that
  removing its required input produces the abstention **and** that it says why.
- **Section 3** is headed *"The fabrication paths are gone from the source, not merely
  unreached."*
- Both directions are covered: an **empty** event log is evidence and is reported; an **absent**
  one abstains. C1.7 is asserted to **compute** on a real log rather than abstain.

### The fault the brief specifies, executed

I reintroduced a fabrication for the abstaining modules — `insufficient()` patched to return a
confident Green instead of declining, which is exactly the regression D1 closed. **Nothing under
`server/app/simulation/` was modified on disk**; the patch is applied in memory to the imported
module objects before the suite runs, so the suite exercises the real `run_module` call path with
one fabricating helper beneath it.

**The fault was confirmed to take effect before any result was believed:**

```
PATCHED MODULES: app.simulation.models, models_dq, models_evc, models_gov
B2.4 on empty signalInputs now returns:
   status_color = green      insufficient = False
   evidence     = nominal (fabricated by fault injection)
FAULT TOOK EFFECT: True
```

**Result: 100/100 → 60/100. Forty checks went red**, including every one of the twelve abstention
assertions:

```
****  A1.2 abstains without spiHistory      [green / nominal (fabricated by fault injection)]
****  B2.1 abstains without evm+mc+cusum+doc
****  B2.2 / B2.3 / B2.5 / B2.6 / B2.7      [same]
****  B2.4 abstains without evm
****  B2.8 abstains without evm
****  B2.9 abstains without evm+cusum+doc
****  C1.4 abstains without events
****  C1.7 abstains without events
****  A1.2 abstains on a signalInputs with no D1 keys at all   [green]
...
```

Baseline re-run without the patch: **100/100**.

These checks are the opposite of vacuous. They are among the most precisely aimed in the
repository, and they fail exactly when a module fabricates instead of abstaining — the scenario
the brief says they would miss.

### One incidental observation

This suite marks a failure with `****`, not `FAIL`. Every other suite uses `FAIL`. A runner or a
reader grepping for `FAIL` sees nothing from this suite even when 40 checks are red. It still
prints a correct `RESULT: 60/100` line and exits non-zero, so it is not the crash-with-no-result
class from part 2 section 5.5 — but it is the same family, and worth knowing before someone greps
across suites. Not changed; reporting only.

---

## Verify

Counts before and after are identical, because nothing was changed:

| Suite | Before | After |
|---|---|---|
| Server suite, 30 suites | 1649/1649 | 1649/1649 |
| `tests_render.html` | 68/68 | 68/68 |
| `tests.html` | 51/51 | 51/51 |

**The counts are not the evidence.** The evidence is the four fault proofs: 100 → 60 under the
fabrication, 68 → 65 under the grafting fault, each with the fault confirmed to have taken effect,
each restored via `git checkout --` and each baseline re-measured afterwards. The working tree is
clean.

`tests_render.html` reports 68 when run with a signed-in session in the same tab and 63 without
one, because the over-the-wire group reports a **failing** row rather than skipping silently when
it has no token. That behaved correctly and unprompted during this session: opening the harness
cold produced `62/63` with the single failure *"production read path: exercised against the
server"*.

## What I did not do, and why

I did not rebuild either suite. Rewriting `test_d1_module_inputs.py` would have replaced a suite
with a working anti-vacuity control and twelve fault-proven abstention checks with something new
and unproven, and rewriting a chart-data suite would have meant inventing one and then describing
it as a repair. Either would have destroyed or fabricated coverage on a premise the code
contradicts.

If the intent was to close the narrow gap this did surface — the slim-row fields other than
`status` are asserted nowhere against the live server — that is a real and small piece of work,
and I can do it on request. It is not what either finding described.
