# Taxonomy artifact, the halted merge, and two checks that could not fail

Branch `t13-fixture-and-taxonomy`, merged to `main`. **873 checks across 18 suites**, up from 854
across 17. `tests_render.html` 22/22.

**Step 4, the mechanical sweep, was not started.** Its own instruction says to stop if the naming
authority document is not attached. It was not, for the third consecutive session. See section 6.

---

## 1. Part 1: the group assignment artifact

`GROUP_ASSIGNMENT.md` at the repository root, generated from `VALIDATED` plus
`PORTFOLIO_VALIDATED` rather than from any document.

| Group | Name in user-facing text | Count |
|---|---|---|
| A | Project Health | 52 |
| B | Recommendation and Governance | 36 |
| C | Data and Evidence Health | 7 |
| D | Portfolio Level | 5 |
| | **Total** | **100** |

It records, in plain terms, that Document Risk Score is excluded because the analytical server does
not compute it: both places that assemble the value take the number straight from the extraction
model's field, with no arithmetic and no derivation from other extracted figures.

It records the open caveat as instructed: nobody has established whether that value is unported by
design or by accident, the registry's refusal is the wording of work outstanding, and **100 is
current rather than permanent.**

It also states, per the standing rules, that the refusal is **a generic catch-all** for anything
absent from the validated set and must not be described as a Document Risk Score specific
exclusion.

The artifact carries the usage rules that the step 4 sweep will need: groups by group and purpose
never by id or number, "and" rather than the ampersand the code constants use, and that Group C
does not contribute to project status.

## 2. The drift check, and proof it can fail

`server/tools/test_group_assignment.py`, 17 checks. It parses the fenced block in the artifact and
compares it against what the server registers.

Proven able to fail three ways **before** being trusted:

| Fault introduced | Assertions that went red |
|---|---|
| Deleted an id from the artifact | every registered computation appears in the artifact (named the missing id); group A count; total |
| Moved an id into the wrong group, counts still plausible | every id sits in the group the CSV gives it (named `C1.7: artifact=B csv=C`); group B count; group C count |
| Injected a second genuinely unported module into the CSV | exactly one declared computation is unported (found both) |

The second fault is why group membership is asserted separately from counts: a swap that keeps the
totals believable is exactly the failure a count-only check would miss.

The CSV was restored after each fault and `git diff` confirmed clean.

## 3. Part 3: the two bad checks

### 3.1 The tautology, and a correction to how it was described

`test_simulation.py` asserted `len(unported_modules()) == 101 - len(VALIDATED)`.
`unported_modules()` is `set(registry_index()) - set(VALIDATED)`, and `registry_index()` is exactly
the 101 live CSV rows, so the left side **is** the right side by construction.

**A correction to the previous session's report, which I should state plainly.** That report called
it "a tautology that cannot detect the gap it appears to guard". When I injected an extra CSV row
the old check did in fact fail, because the literal `101` no longer matched the row count. So it is
not vacuous in every direction.

The fault it genuinely cannot see is a module silently ceasing to be validated, with the row count
unchanged. Demonstrated:

```
drop  1 from VALIDATED -> unported= 7, old check passes=True, genuinely unported=2
drop  5 from VALIDATED -> unported=11, old check passes=True, genuinely unported=6
drop 20 from VALIDATED -> unported=26, old check passes=True, genuinely unported=21
```

It passes in all of those. The replacement asserts the genuinely unported set is exactly
`["A4.1"]`, and fails on the first dropped module.

### 3.2 A latent fragility fixed alongside it

`still_unported = unported_modules()[0]` passed only because "A" sorts before "D". Had Document
Risk Score ever been ported, `[0]` would have become a Group D id, and `run_module` would raise
`PortfolioModuleError`, which that `except MissingModuleError` clause does not catch. The test
would have errored rather than failed cleanly. It now takes the id from the genuinely unported set.

### 3.3 `unported_modules()` itself: NOT FIXED, and why

**This part of the task was refused rather than approximated.**

The task asks me to correct `unported_modules()` so its count reflects what is actually unported.
That function is at `server/app/simulation/registry.py:49`, and the same instruction says **"Do not
modify anything under server/app/simulation/."** I did not silently pick one instruction over the
other.

What I did instead: both new checks compute the genuinely unported set themselves, from the two
registries plus the CSV, so neither inherits the error. And the over-report is now **asserted
explicitly**:

> `unported_modules()` over-reports by exactly the Group D set (known defect, not yet fixed)

That means the defect is documented in a place that runs, and if the function is ever corrected
this check fails loudly and is updated deliberately rather than drifting.

**Your decision.** Either lift the `server/app/simulation/` prohibition for that one function, or
leave it and keep the assertion as the record.

## 4. Part 4: the contradiction in `ds_defensibility_data.js`

Line 3717 asserted:

> No capability claims a statistical property it does not have.

Line 18 lists fourteen label-to-algorithm mismatches that "should be renamed or reimplemented
before a formal defense", including Isolation Forest, Linear Programming and Pareto Frontier.

I changed the assertion rather than weakening the finding, because the finding is the true half. It
now points at the refactor register instead of claiming the problem does not exist. I verified the
register exists (`ds_defensibility_data.js:120`) and renders **above** that section
(`knowledge.js:2604` against `2637`) rather than asserting it did. Two lines, no wider rewrite.

## 5. Part 2: the merge

`main` was at `062731b`. The halted branch is merged and pushed, which triggers a Render deploy.
The server suite was confirmed green before pushing.

## 6. What I did not do, and why

- **Step 4, the mechanical sweep: not started.** The instruction is explicit that it stops if the
  naming authority document is not attached, because the sweep rewrites surfaces that must quote
  its standing description wording verbatim, and the summary carries the taxonomy but not that
  wording. It was not attached. I did not work from the summary.
- **`unported_modules()`: not corrected.** Section 3.3.
- **No content sweep, no PCEIF removal, no em dash sweep**, beyond the single two-line fix in
  Part 4.
- **Nothing under `server/app/simulation/` was modified.**

## 7. Guarantees

| Guarantee | Status |
|---|---|
| Artifact maps every registered computation to exactly one group | **Verified**, asserted both directions |
| Artifact states the verified counts | **Verified**, 52 / 36 / 7 / 5, total 100 |
| Artifact records why Document Risk Score is excluded | **Verified** |
| Artifact records the open caveat and that 100 is current not permanent | **Verified** |
| A check fails if the code stops matching the artifact | **Verified**, proven failable three ways |
| Tautology replaced with a check that can fail | **Verified**, proven against a dropped module |
| `unported_modules()` count corrected | **NOT MET.** Refused: the fix is inside a directory this task forbids modifying. Section 3.3 |
| Contradiction in `ds_defensibility_data.js` resolved | **Verified**, and the register it now cites was confirmed to exist and render above |
| Branch merged, suite green before push | **Verified** |
| Step 4 not started | **Verified** |

## 8. Found along the way, not part of the task

- **`knowledge.js:2638` renders a section heading "How PCEIF Is Accredited".** That is a
  user-visible retired framing sitting directly above the text I corrected. It belongs to the step 4
  sweep and I left it, but it is worth knowing that the section I just fixed still has a retired
  name at the top of it.
- **The old `test_simulation` check was not as vacuous as previously reported.** Section 3.1. I
  would rather correct that in writing than let a slightly wrong claim stand in a report.

## 9. For the next session

1. **The naming authority document still has not reached a session.** Three consecutive now. Step 4
   cannot start without it, by its own terms.
2. **`unported_modules()` needs your decision**, section 3.3.
3. `tests_render.html` is not part of the 873 and will not run itself. Open
   `http://127.0.0.1:8010/tests_render.html` with the dev server up, after any change to `app.js`,
   `detail.js`, `decision.js` or `taxonomy.js`.
4. `test_group_assignment.py` is the guard on the artifact. If it fails, the code and the published
   taxonomy have diverged and no sweep should run until that is understood.

## Regression

**873 checks across 18 suites**, all passing. Change from 854 across 17, stated where it happened:

- `test_group_assignment` **+17**, a new suite.
- `test_simulation` **27 to 29**, where one tautological check became three real ones.

No other suite changed.
