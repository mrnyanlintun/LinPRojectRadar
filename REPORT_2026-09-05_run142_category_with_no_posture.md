# Run 142 — a category with no posture must not reach the card as nothing

**`SIMULATION_VERSION` did not move**, and it did not need to. It is `sim-2026.09-v70`.
**No band, threshold, weight, posture rule or category rule changed.** No migration. A category
with no banded module still carries no posture, and the required-core gate still withholds the
project status exactly as before.

Starting commit `0cf8271`, ending `7465081`, pushed, tree clean.

---

## The owner's closing question, answered plainly

**Yes. A reader can now tell the two apart from the card alone, without clicking and without
querying the database.**

On the collapsed category row, a category whose modules ran and abstained reads
*"4 of 4 modules ran and had nothing to report — each says why below"*. A category whose modules
never dispatched reads *"no module in this category has a stored result for this period"*.
Expanding gives each module's own reason verbatim. The Awaiting-analysis brief states the
distinction in the sentence the server composed.

Before this run the two cases were **byte-identical** in the projection, in the sentence and on
the card.

---

## A premise I gave the build was wrong, and correcting it made the run cheaper

I briefed the build that fixing the sentence would change stored output and therefore move the
version stamp, and that this was expensive with the v70 recomputation outstanding. **That was
false.** The survey caught it and I verified the correction myself:

`ComputedResult` has **no column for the basis**. Its columns are the result id, project, period,
signal inputs, module results, category statuses, project status, portfolio snapshot, version,
seed, cutoff, timestamp, supersede pointer, source documents and the abstained list. The store
function writes exactly that set, and **no migration anywhere mentions `status_reason`,
`required_missing_detail` or `project_status_basis`.**

**The basis is recomputed at read time on every request.** So the sentence changes no stored byte,
needs no stamp move, and does not touch the outstanding recomputation. Two consequences follow.
The fix could be made properly at the single authority rather than worked around. And because the
sentence is regenerated on every read rather than stored, **fixing the code fixes every past
period at once** — no recomputation will ever have been needed, and none is needed now.

---

## Where the rows were dropped

`server/app/spec_projection.py`, in `merge_python_row`:

```python
    if filled:
        wanted = set(filled)
        for m in (row_module_results or []):
            ...
            if _python_category_of(m, m.get("module_id")) in wanted:
```

`filled` is built only from categories present in the Python row's `category_statuses`, and
`simulation/compute.py:432-440` builds that mapping from computed modules alone. A category where
nothing banded therefore has no key, no posture, and its rows were dropped at projection.

## The rows do exist in storage — established by execution, not inference

`registry.record` files an abstaining module to the abstained list **with its reason**, and
`compute_project` stores that list on the row. Executed: a throwaway-database row round-tripped
all four abstentions with their reasons, and the research export returned all four **while the
card showed zero**. Run 141's reading is confirmed: **recorded in storage, dropped at projection.**

**A finding that follows: before this fix the export and the card disagreed about the same
period.** They now agree.

## One of my pre-checked facts was falsified by the build, and it matters

I told the build that the served `required_missing_detail` already distinguished the two cases
with a three-way split. **On this path it did not.** A category with no posture had no entry in
the merged mapping in *either* case, so both took the same branch and produced byte-identical
output. The richer field could not help until the carry-over gave the category an entry.

---

## The change, and why it is the smallest

**1. The projection** (`spec_projection.py`). The carry-over set becomes the categories with a
posture **plus** those that ran without banding, and each of the latter gets a **postureless**
entry. The test is *no posture*, not *no key* — on the keyless route an entry is stored for all
ten categories, so a key test would have dropped the rows again. An unanswered specification entry
is **annotated, never replaced**. The posture-layer marker is deliberately not set, because the
brief reads it as "this category's posture came from here" and this category produced none.

**2. The sentence** (`simulation/compute.py`), the two strings fixed **in place at the one
authority and not forked**. This is the only edit under the restricted package, and it is two
string literals plus their reasoning. Forking would have recreated the two-authorities-for-one-fact
defect that the comment beside the call exists to forbid.

**3. The collapsed row** (`assets/js/app.js`, plus one stylesheet rule). Without this the fix
would have shipped looking correct and being invisible — see below.

**Requirement 3 is satisfied because of change 1**, not merely by rewording: the sentence tests
key presence, and the key now exists exactly when the category was in fact called, so the test and
the words say the same thing.

## Sentence variants, before and after

| site | before | after |
|---|---|---|
| absent from the mapping | "no module in this category was run for this period" — **asserts a fact about dispatch that nothing checked**, and was false on the case Run 141 diagnosed | "no reading of any kind is held for this category this period, so nothing is recorded about whether its modules ran" |
| present in the mapping | "the category was called and no module in it asserted a band" — **flatly false on the served path** for a category whose specification reading failed or was never asked, which with no key present is every category | "a reading is held for this category and no module in it asserted a band" |
| collapsed card row, ran and abstained | nothing distinguished it | "N of N modules ran and had nothing to report — each says why below" |
| collapsed card row, never dispatched | nothing distinguished it | "no module in this category has a stored result for this period" |

**A fifth site remains and is reported rather than fixed.** `simulation/compute.py` holds a second
copy of the missing-detail structure carrying the same over-claiming wording. It is on the compute
**response**, not the stored row, so there is no stamp implication. It was outside the clearance I
gave and is left for a ruling. **It is the identical false claim one surface over and should be
closed.**

---

## The finding that would have made this run ship broken

**Carrying the rows through was not sufficient**, and it would have looked sufficient to anyone
inspecting the served data or expanding a row while testing.

Both renderers that could show the distinction hide it by default. The specification panel puts
every module row and every reason inside an element set to `display:none`, opened only by a
toggle. The signal ledger — the renderer that actually prints a module's abstention reason — sits
inside a disclosure element opened by default for exactly one category and closed for A1 through
A6. Without change 3, a reader who did not click would have seen the same thing in both cases:
a heading, a "no band" word, a state chip, a count of zero produced, and a closed triangle. The
reasons would have existed in the page and been invisible.

---

## The seven proofs

| # | proof | result |
|---|---|---|
| 1 | a category where every module abstains renders each row with its reason | **PASS** — 4 of 4, at the merge and through the served view |
| 2 | a category where none dispatched renders distinctly | **PASS** — distinct in the detail field, in the sentence, and **on the collapsed row** |
| 3 | the sentence matches the condition | **PASS** — condition and wording shown side by side, both directions |
| 4 | the project status is unchanged | **PASS** — "Awaiting analysis", not official, identical in both cases; the category posture is `None`; no substituted value |
| 5 | the fix can fail | **PASS, and I ran this myself.** Reverting the carry-over gate to the old set drops the rows 4 → **0** and the check names the requirement. Restored, it passes. The renderer injection collapsed both rows to the identical text and failed six checks |
| 6 | the exports carry what the card shows | **PASS**, with the finding that the export read the stored row all along, so before the fix the two disagreed |
| 7 | PRJ-002 period 2's shape | **Constructed fixture, and said so plainly.** The stored rows are unreachable: production is never contacted and the only local database is the stale August one at the v42 stamp with no PRJ-002. The fixture is that period's exact shape using the registry's real A3 roster of four modules, and it renders all four with their reasons |

**Rendered and confirmed by observation**, not by reading the stylesheet: headless Chromium, the
real renderer and stylesheet, the disclosure element asserted closed, and the new line measured at
**5.90:1** against its painted background.

---

## Counts that moved, deliberately

The projected abstention list grows by exactly the number of carried rows — zero to four in the
fixture. The projected module-results list is **unchanged**, because an all-abstaining category
contributes nothing to it. So the three published figures the survey identified each grow by the
abstention count only: the abstained count printed in three places on the card, the brief gate's
admissible-figure counts, and the modules-computed figure in the brief.

**None is a band, threshold, weight or rule, so requirement 4 holds.** They are recorded here as
deliberately moved so that a reviewer comparing two exports of the same period across this fix
does not discover them unexplained.

## Downstream consumers

**No consumer assumed emptiness.** Most are safe structurally: the research export, the
qualification dimensions and the audit record read the **stored** row rather than the projection,
so a projection change cannot reach them, and the checksum-covered export columns are untouched.
The status-gated readers all gate on a `status` field the new entry does not carry.

**Two invariants were checked explicitly because they were the ways this could have gone wrong.**
A category the specification layer genuinely answered receives **zero** carried rows and keeps its
own entry unannotated, so nothing double-counts. And no carried row can enter the adverse readings:
the abstained entries carry no band colour, measured as four `None` values, and the mitigation
layer composed **zero** — so no new model call can be attempted. Structurally, a module that banded
would have given its category a posture and was already carried under the old rule.

## Regression, taken by me on merged main

| suite | result |
|---|---|
| the three new Run 142 checks | PASS, no failing checks |
| mitigation render / gate / engine | 55/55, 20/20, 55/55 |
| assembly and precision | 83/83 |
| actual-cost selection | 31/31 |
| A1/A3 band contract | 54/54 |
| scientific methods | 222/222 |
| fault guards | 42/43, the known A6.2 residual |
| preservation | 32/33, the known undeclared-bytes residual |
| stance sweep / exports | 40/40, 138/138 |
| period scoping | **74/77, up from 73/77** |

The build reported the wider regression as unproven, so I ran it. **One suite moved, and it moved
up.** I measured period scoping at 73 of 77 on the pre-change files and 74 of 77 after, so the
change fixed a check rather than breaking one. Every other figure matches its known baseline.

## Iteration log

| finding | attempts | proof | disposition |
|---|---|---|---|
| rows dropped at the projection seam | 1 | 4 → 0 reproduced on main, then 0 → 4 after | RESOLVED |
| the carry-over set must test posture, not key | 2 | a key test dropped the rows again on the keyless route | RESOLVED |
| the sentence asserts what it did not check | 1 | condition and wording compared side by side | RESOLVED |
| the distinction was invisible while collapsed | 1 | both rows collapsed to identical text before the change | RESOLVED |
| my stamp-cost premise | 1 | no column, no migration, recomputed at read | RESOLVED, premise withdrawn |
| my "already three-way" premise | 1 | both cases took the same branch | RESOLVED, premise withdrawn |

Nothing reached the cap. Nothing is BLOCKED.

## Items found and not fixed

1. **The second copy of the missing-detail structure** in the simulation package still carries the
   over-claiming wording. Response-only, no stamp implication, outside the clearance given. **The
   identical false claim one surface over.**
2. **One stylesheet rule** was added outside the stated file ownership, reusing an
   already-measured token, because the new line would otherwise have been unstyled.
3. **Run 141's open question is untouched**, as this order required. Why A3 was empty on PRJ-002
   period 2 is settled by the three queries in that report, not here. What this run changes is
   that the next such case explains itself on the card instead of costing a diagnostic run.
