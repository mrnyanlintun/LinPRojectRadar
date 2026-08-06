# The Signal Ledger shows the calculation behind every module

**Date:** 2026-08-05
**Branch:** `claude/ledger-calculations-s5s90m` (merged to `main`, PR #219, merge commit `a56d175`)
**Model:** Sonnet

**Verification:** server suite **41 suites, 2269/2269** (fresh SQLite DB per test file; no server file was touched), `tests.html` **51/51**, `tests_render.html` **152/153** (new group 16, 9 checks, all green; the one red is the pre-existing auth-gated "production read path" check, red on `origin/main` too). Two faults injected, each confirmed applied, each detected, each reverted with the baseline re-run green.

---

## LEAD FINDING — does every module's stored result carry the finding text?

**Every module that actually computed carries it. No computed module is missing it.**

Established against real data, not assumed: a real `compute_project()` output and a real project driven through the live `/exec` API were both inspected. **29 of 29 computed modules carried `evidence_metric`; zero were missing it.** So the brief's premise was right: this was a display gap, not a data gap, and the fix is to render what is already stored.

**But the set of modules that reach the stored result is smaller than the set the ledger draws.** On the project examined, **66 modules abstained and never reach `module_results` at all.** `server/app/simulation/registry.py` `run_all()` filters them out before storage:

```python
if out.get("insufficient_data") or out.get("status_color") is None:
    abstained.append(new_id)
```

Only the bare module id is appended to an `abstained` list. **The abstention message itself is discarded server-side and never stored.**

This has a consequence the brief anticipated but which is worth stating exactly. The brief asked that "a module that abstains shows its abstention, not a fabricated finding." The platform cannot currently show an abstention *message*, because it does not keep one. What it can do, and now does, is show **nothing** beside such a module rather than inventing a line for it. That is the honest behaviour available within this task's scope.

**Closing that gap is out of scope here and would require a `server/app/simulation/` change** (retaining the abstention message through `run_all()` into storage), which this task explicitly prohibits. Flagged for the owner as the one remaining step if abstention messages are wanted on screen.

### The three-way split as it renders

| Module state | Stored | Ledger now shows |
|---|---|---|
| Computed | `evidence_metric` present, always | the finding text, verbatim |
| Abstained | filtered out before storage; message discarded | nothing beside the name |
| Not applicable to the sector | skipped | nothing beside the name |
| No computed result for the project at all | no row | no findings anywhere |

---

## THE COURSES OF ACTION ANSWER

**None of the three hypotheses in the brief was exactly right.** The truth is a fourth thing, and it was reproduced live rather than reasoned from source.

The block said the scoring analysis "did not compute for this project." In fact **it computed** — the module resolves a real `status_color` (Amber on the print the owner saw, Red on the project reproduced here), which is why the ledger row renders a colour. What is missing is not the computation but the **course set**, which is **withheld server-side**, deliberately, by `_redact_module_actions` in `server/app/documents.py`.

The gate is `recommendation_visible()` in `server/app/research_membership.py`:

```python
return decision is not None and bool(decision.pre_judgment_locked)
```

A `Decision` row exists only where a research `Scenario` is attached. **An ordinary operational project never gets one**, so `decision is None`, so the predicate is False permanently, so the course set is redacted on every read forever. The module's action fields are stripped and the server leaves a `recommendation_withheld` flag on the object to mark the difference between withheld and absent.

So the answer is closest to **(c), the message was stale**, but for a reason none of the three options named: the block was reporting "did not compute" for a module that computed and was then redacted.

**Fixed, because the fix was contained and obvious:** `assets/js/recommendation_options.js` now distinguishes *withheld pending the preliminary judgment lock* from *did not compute*, using the `recommendation_withheld` flag the server already sets. No new field, no server change, no guess.

### Left open for the owner, reported and not fixed

**Should ordinary operational projects be gated behind the research reveal predicate at all?** Nothing in that code path branches on `account_type`. The predicate was written for the research protocol, where withholding the recommendation until the participant's preliminary judgment is locked is the entire point of the instrument. Applying it to an operational project means a project manager can never see the scored course set on their own project, which is unlikely to be the intent but is a policy question, not a defect. **This needs an owner decision and was deliberately not touched.**

---

## WHAT WAS BUILT

`assets/js/app.js` `categoryLedgerHtml` renders each module's stored finding in a new `.cat-mod-finding` block beneath its status pill, read through the existing `getModuleResult(...)` accessor (added by the module-charts session, untouched here). `assets/css/radar.css` carries the styling.

The stored text is rendered **verbatim**: not shortened, reworded, summarised or reformatted. The check asserts full-string equality, not `contains`, so a truncated or reflowed finding fails.

**The seven inline charts from the module-charts session were not touched**, as required. This task added text only.

Nothing recomputes in the browser: the ledger reads the primed stored row and calls no model.

---

## VERIFICATION

The ledger was driven in a **live headless Chromium against a real server and database**, not a fixture, and read back:

- 29 findings render exactly, character for character, against the stored values.
- Abstained and not-applicable rows render no finding line.
- A project with no computed result renders no findings at all.

`tests_render.html` **group 16** (new, 9 checks) asserts the same against the production ledger builder, including full-string equality of the rendered finding against the stored `evidence_metric`.

**Faults proven**, each confirmed to have taken effect before the run and reverted afterwards with the baseline re-confirmed green:

| Fault | Result |
|---|---|
| fabricate a finding line on every row, including abstained ones | red |
| force the stale "did not compute" Courses of action message back | red |

---

## FILES CHANGED

`assets/js/app.js`, `assets/css/radar.css`, `assets/js/recommendation_options.js`, `tests_render.html`, `T6_HANDOFF.md`, this report.

**No server file was modified.** Nothing under `server/app/simulation/` was touched. No module id or number appears in anything added; no em dashes.

---

## OPEN ITEMS HANDED TO THE OWNER

1. **Abstention messages are discarded before storage** (`registry.py` `run_all()`). If an abstaining module should state *why* it abstained on screen, the message must be retained through to `module_results`, which is a `server/app/simulation/` change.
2. **The research reveal predicate gates operational projects.** Decide whether `recommendation_visible()` should branch on account type, so a project manager can see the scored course set on their own operational project.
