# Run 146 — the page renders nothing while the stored row is complete

**`SIMULATION_VERSION` does not move.** It stays `sim-2026.09-v73`. This is a serving fault against
correct data: no band, threshold, weight, posture rule or category rule changed, no migration, no
writes. **No recomputation follows from it.** Deploying the code is the whole remedy — the pages
repopulate on the next read.

Starting commit `03555dc`, ending `7a40f5b`, pushed, tree clean.

---

## The seam, named exactly

**`documents._resolve_period`, and the refusal it causes in the results route.**

**Not the projection.** My own leading diagnosis was wrong, and I want that on the record before
anything else, because I dispatched the run pointing at the wrong seam.

For a project carrying a research assignment the period is derived server-side and the request's
own period is ignored. That derivation asked for the current period **without the scenario**, and
the scenario is the only thing that caps it. Uncapped, the cap collapses into a no-op and the
derived period **advances past the last period the scenario has**, the moment that period's
decision is submitted and transitioned. Three lines above, in the same module, the decision-state
call *does* pass the scenario — so one module derived two different current periods for one
assignment, and only the uncapped one reached the read route.

The route then found no live row for that period, refused, and the client **drops a refusal
silently**: a response that is not `ok` returns early with nothing grafted. The row never arrived.

## Why the category postures survive

**Because they never travel that path.** The list projection that the page attaches carries exactly
six keys, measured rather than read: the category statuses, the period, the posture layers, the
project status, the fallback categories and the result id. It **deliberately omits the module
rows** — a project list is not where that predicate has been evaluated.

So a page whose graft never ran still renders the postures, the project status, the header driver
and the Signal Flow diagram, and nothing else. That is exactly the split you observed.

## One fault, not three

**The signal inputs and the disposition list are the same seam.** Both live on the served row and
both reach the client only through the graft that never ran. Confirmed in the browser with the
fault injected: the client row carries no module rows, no abstentions, no signal inputs and no
dispositions, while still holding seven categories and a project status.

## The evidence that settled it against my diagnosis

**The card's own branch test.** It picks the "has not been read back yet" sentence on whether the
module rows are an **array**. My projection theory yields an **empty array**, which is still an
array and takes a different branch. **You saw the first branch, so the module rows were absent, not
empty — the whole row never arrived.** I verified that line myself. A drop inside the projection
cannot produce what you saw.

## Attribution — none of Runs 142 to 145, and not the projection either

The actual fault is in the period derivation and is not in the projection at all. Runs 142 to 145
are all on the writer side and are innocent.

**But the projection finding I reproduced before dispatching is real, and it is a separate latent
defect.** A category the specification layer *answers* has its Python module rows discarded, so if
that reading carries no module rows of its own the category publishes a posture with no evidence
beneath it. Reproduced by execution: answered with no rows gives zero module rows, the failing 403
state gives 28, no specification readings gives 28, and answered carrying one row gives one.

**Its attribution is confirmed and it is old.** The same exclusion exists in the file immediately
before Run 142, and the line's origin traces to **Run 102**. Run 142 *widened* the carry-over; it
did not create the exclusion. On your fourth exclusion: you are right that a **failing**
specification layer does not withhold module rows. A **succeeding** one does — but that is this
latent defect, and **it is not what emptied your page.**

**It was fixed, measured working, and then deliberately reverted.** The repair — serving the Python
rows beneath an answered category that supplied none, marked by layer — restored 28 rows and left
the posture untouched. It was reverted because it makes an invariant of Run 142's own check fail:
that run explicitly measured and asserted the opposite rule, that a category the specification
layer answered is not carried and nothing is doubled. **Amending that check so the change could
pass would be suppressing a failing check.** It is recorded with its evidence in a check that
asserts only what is true of the code as it stands. **This needs your ruling, not a patch.**

## The fix

Both halves in one file, nothing else.

**One: the derivation passes the scenario**, restoring the cap. Authority does not move — the
period is still derived server-side and the payload still ignored under an assignment. The
derivation is only *bounded*, never loosened.

**Two: the read no longer refuses** when the derived period holds no live row. This covers what the
cap cannot: a period the scenario still counts but the project no longer holds — PRJ-002 after Run
143 removed period 3. This is a **read**, and the derivation's own docstring says the rule exists so
that a participant cannot *write* into a period they have not reached. The latest period holding a
live result is served, and the response says so: that a substitution happened, which period was
requested, and why. **It discloses nothing new** — the list projection already publishes that same
row's period and status to that same reader — and the reveal gate is applied unchanged.

## The six proofs

**Which fixture: an equivalent constructed one, and both scripts say so plainly.** PRJ-002 is
unreachable — production is out of bounds and the only local database is the stale August one. The
scripts build the *state* through the real endpoints: two computed periods, a scenario, an
assignment, and a submitted and transitioned decision in the last period.

| # | proof | result |
|---|---|---|
| 1 | drop reproduced first | **PASS** — the derivation returned period 3 on a two-period scenario, and the route refused with "no computed result for period 3" |
| 2 | after the fix the row is served whole | **PASS** — module rows, abstentions, signal inputs and dispositions all present, at the fixture's own counts rather than your 28 and 3 |
| 3 | confirmed on the rendered page | **PASS** — see below |
| 4 | postures and project status unchanged | **PASS** — identical before and after, and the served postures equal the list projection's exactly |
| 5 | proved able to fail | **PASS** — both halves removed, the route refuses and the page empties; restored, the row is served whole |
| 6 | blast radius | **PASS** — established below |

**Proof 3 is a browser observation, not a payload check**, because both renderers hide detail by
default and Runs 142 and 144 both established that a payload check can pass while the page shows
nothing. With the fault injected the page reproduces **your sentence verbatim**:

> *"0 of 28 modules in service assert a band; 0 computed without asserting one, 0 have nothing to
> report, 0 are not relevant to this project, and 28 have not been called."*

Fixed, on the same fixture, the line reads real counts, the "No data" cells fall from 39 to 34, the
disposition control appears where it was absent, and both the "has not been read back yet" and the
"no extracted values cached this session" sentences are gone.

## The blast radius

**The condition is: the project carries a research assignment, and the period that assignment
derives to holds no live computed row.** That is **every study project whose participant has
recorded and transitioned a decision in its last period** — every period, every simulation version,
not specific to PRJ-002, to period 2, or to v73.

**Operational projects have no assignment**, so their requested period is honoured and they are
unaffected. That is why this was never seen outside the instrument. **Period 1 of an affected
project is equally blank**, because the fault is in which period is served, not which period is
asked for.

## Regression

Eight suites on merged main, all on fresh throwaway databases: the three new Run 146 checks
(16/16, 6/6, 16/16), period removal 74/74, both Run 142 carry suites passing, the Run 145 leak
check, the reveal gate 20/20, and Run 144's mitigation exclusion. One participant-cycle driver
reports 50 of 56 **both with and without the change**, measured on main rather than assumed.

## The production query that confirms it

Read-only, and the report carries the full statement. It joins the project to its scenario and
assignment and the latest decision, and reports the scenario's period count beside the periods that
actually hold a live result with module rows.

**What the result means.** Derive the period: if the decision is unsubmitted or untransitioned it
is the decision's own period, otherwise one past it, then capped at the scenario's period count. If
that number **is not among the periods holding a result**, the diagnosis is confirmed on the
deployment. A period count of two confirms the first half was the cause; a count of three with
results only at periods one and two confirms the second half was needed too. Running it without the
project filter sizes the blast radius across the study.

## Items for a ruling

1. **The answered-category evidence drop**, above. Old, latent, real, reverted rather than patched
   because fixing it contradicts an invariant Run 142 deliberately asserted. **The smallest decision
   is whether a category the specification layer answered should still show the Python module rows
   beneath it, marked by layer.** My view is that it should — a posture with no evidence beneath it
   is the shape Run 142 was written to close — but the check says otherwise and the check was
   written on purpose.
2. **The client drops a refusal silently.** That is what turned a server refusal into a blank page
   with no error anywhere. Out of scope here and not touched, but it is why this cost a run to find.

## Iteration log

No finding needed more than one attempt. The correction worth recording is mine: **I dispatched
this run naming the projection as the seam, having reproduced a real drop there, and the seam was
elsewhere.** The agent contradicted the dispatch with a discriminator I could check in one line —
absent versus empty module rows — and it was right. The projection finding survives as a separate
latent defect rather than as this fault's cause.
