# Run 143 — period removal, and carry-forward as a general rule

**`SIMULATION_VERSION` moves `sim-2026.09-v70` → `sim-2026.09-v71`**, appended to the history
tuple with no prior row edited. The superseded marker is left at its Run-49 value, which is not
this run's to move. **No migration was written for either part**, and each agent said why before
not writing one. Part 1 did not move the stamp; it deletes data rather than changing what a module
computes.

Starting commit `bdaa11b`, ending `4459c45`, pushed, tree clean.

---

## The closing question, answered plainly

**Yes. A reader can tell a carried reading from a current one on the card without clicking.**

Measured in a browser against two stored rows differing only in the fields the carry step writes,
with the disclosure element asserted **closed**:

```
current   Schedule Performance  Amber
carried   Schedule Performance  Amber  1 of 1 reading is carried from an
                                       earlier period, not this one
```

Three independent signals, so no single theme or colour-vision difference erases it: the note
itself at **5.90:1** against the background actually painted behind it, a chip reading
**"Carried from P1"**, and a dashed left border with a tinted ground where a current row has
neither. **The band pill is byte-identical in both** — a carried Amber is an Amber and votes as
one.

---

# Part 1 — period removal

## Your table list was an undercount, and the two it missed were the ones that bite

I enumerated the schema myself rather than trusting the report. **Five tables declare a foreign
key to documents; two more reference a document with no declared key at all:** the supersede
pointer on the upload link, and the source-document list stored as JSON on every computed result.
That second one is read by the staleness check, so orphaning a document still named there would
have silently broken staleness detection **for a period that was staying**.

The orphan rule runs **after** the period's own rows are deleted and flushed, which is what makes
it simple enough to be right: every reference it then finds belongs to another period or another
project, so it names shared content, and anything unnamed is unreachable. The JSON column has no
portable operator across both databases, so it is scanned in Python — the honest cost of a
reference the schema does not declare, paid on a delete rather than a read.

## Your supersede warning applied to three chains, not one

Computed results, **specification readings** and **the mitigation store** each carry their own
supersede pointer. Two of those are beyond your list. All three are deleted whole.

**Nine per-period stores are deleted:** computed results, specification readings, module
mitigations, observations, schedule activities, project risks, project notices, upload attempts,
document upload links.

**Three are deliberately kept**, each with its reason in the code. One turned out not to be a
per-reporting-period store at all: its period column is a **calendar** key, so matching a
reporting number against it would match nothing or something unrelated. I independently checked
two further period-bearing tables the agent did not mention and confirmed both are scenario-scoped
research tables, not project stores. The recognition cache has no period column at all and
deleting from it would break replay for periods that are staying.

## A third unsafe state, beyond the two you ordered

**A submitted research decision points at a stored result row.** Deleting the chain would leave it
dangling. Refused separately with its own reason. A period holding nothing at all is also refused
rather than reported as a successful no-op.

The decision guard reads the append-only governance rows themselves, not a proxy for them.

## The period list was not already correct

Established by observation before any code was written. The list was **generated** from the
highest period number rather than read from a table, so it **could not represent a gap**. With
period 3 genuinely removed from a project holding 1, 2, 3, 4 it answered `[1, 2, {period 3}, 4]`
— fabricating the removed period back — while the computed periods correctly showed the gap.

**The fix is on the server and no client change was made.** The client renders what it is handed,
and its own comment claims the offered choices always match what the server would accept, which
with a gap was false. The list now reads the periods the upload table actually holds. For a
gapless project the answer is byte-identical to the range it replaces.

**This reproduces your PRJ-002 symptom exactly**: deleting only the document rows leaves the list
at 1, 2, 3, 4, because the list reads the upload links rather than the documents.

**Remaining periods are not renumbered.** 1, 2, 3, 4 minus 3 renders 1, 2, 4; a second removal
renders 1, 4; and the next period stays 5 rather than refilling a gap.

## The six proofs — 74 of 74, re-run by me

1. **Clean removal** — uploads, the whole result chain, all four projection stores, specification
   readings, mitigations and upload attempts at zero; the period gone from both lists.
2. **Shared document survives** — constructed twice. The agent reports that **its first attempt
   failed and the code was right, not the test**: it used bytes another *project* had uploaded, and
   removal correctly kept the row. That cross-project case is now asserted rather than assumed.
3. **Decided period refused**, reason stated verbatim.
4. **No renumbering.**
5. **No dangling supersede reference**, on all three chained stores, proved able to fail.
6. **Guard-removal injection** — a decided period holding one upload, one result and ten
   observations became removable and went to zero on all three. The governance audit row survived
   even then; append-only held. Guard restored, a freshly decided period refused again.

## What removal adds to the recomputation

Removing a period changes what the project's *other* periods were computed alongside, since every
cross-period series reads earlier periods. **Every period later than a removed one now holds a
result computed against a project state that no longer exists.** The endpoint returns that fact,
says so in its note, and stamps it into the audit row. For PRJ-002 specifically, removing period 3
leaves nothing later, so the addition there is nil.

## One decision for you

**No user-interface control calls the removal endpoints yet.** Both exist and are proven; that was
outside what the order gave and the agent did not invent it. The natural place is beside the
archive control in the document dialog.

---

# Part 2 — carry-forward as a general rule

## The stance change

**Dated 2026-09-06. Origin: Run 143.** A module abstaining in the current period now displays and
votes with its most recent non-abstaining reading from an earlier period of the same project,
marked as carried, naming the period it came from, and stating that period's own evidence sentence
unaltered.

## The forbidden defect was the default behaviour, not a risk

I verified this before the build began. The client accessor every surface uses to render a module
band returns the band colour **and nothing else**. Append a carried row and it renders as current
everywhere, with no marker, no code change and no error. **The marker work was therefore the
majority of the run, not a finishing touch**, and it was briefed and built that way. The accessor
is deliberately unchanged and a second accessor asks the second question beside it, so no existing
call site moved. Markers land on the ledger row, the **collapsed** category head, the specification
panel's collapsed head, the network tooltip and the top of the decision card.

## Your prediction about the missed sentence was right, and understated

The survey found the one a naive search misses, emitted **for six of the thirty modules** because
the Category-9 gate refuses before the module runs. **The build then found nine more the survey
had not listed** — sentences that make no substitution promise at all and were merely *incomplete*
once the stance changed, which is worse, because a reader who has learned that abstentions carry
cannot tell whether those do. They include the default insufficient-data sentence, which is the
one a participant most often reads.

**28 emitted sites now end with a single shared clause**, defined once and imported, so they cannot
drift. **Shared builders were fixed once; module-local text was fixed each.**

**The keeping sentences kept their substance and each gained a clause saying why it does not
carry** — otherwise a reader who has learned the new rule reads them as inconsistent rather than
principled.

**One site must keep its promise and does.** The failure path says that for a module that raised,
nothing is substituted, no default, no band, **no last-known value**. I verified that wording. It
now says the abstention path is exempt from that promise and the failure path is not.

**C1.5 was a trap the build caught.** It abstains through the *shared* structure-absent builder,
which cannot know it is exempt, so it was publishing the carrying promise on a measure that can
never band. Corrected in one place, so any module added to the exemption list can never make the
wrong promise.

**A check fails the run** if a carrying measure omits the rule or a keeping measure refuses without
saying why.

## Rule 5 is a property of the abstention arm, not the module

**This was the largest implementation risk and your phrasing invites the wrong shape.** Safety
Performance needs **carrying on two arms and blocking on two others**: block the exposure floor,
whose own words are that no rate is published as though it were stable, and block the near-miss arm
where no calibrated ladder exists, but carry the two arms where exposure data is genuinely absent.
The forecast module splits the same way, and the build found **a second short-history arm the
survey had not named**.

**Exemption is never matched on sentence text** — this run rewrites those sentences, and an
exclusion keyed on wording would fail *open* the moment someone rephrased one. Arms declare
themselves.

**Measured: 24 of 31 in-service modules eligible, 7 exempt.**

## A correction the build made to the survey, and it was load-bearing

The survey said to read the abstained bucket. Your order says *"abstained **or produced no
band**"*, and calibration-pending rows are routed into the computed bucket with no band —
**which is exactly where Safety Performance's two excluded arms land.** A build reading only the
abstained bucket would have made this run's per-arm exclusions dead code and passed its own tests.

## Rule 4 was violated by default until guarded

Stored rows written before the Run 96 retirement still hold retired module identifiers with their
bands. The look-back never dispatches, so nothing raises. **The candidate set is intersected with
the live registry**, and a retired module with a stored band is proved not to resurrect.

## The posture arithmetic needed no change

Your preference was achievable. A carried reading enters as a band and the arithmetic is identical;
nothing in the category or project rollup knows or needs to know. **No band, boundary, posture
rule, weight or threshold moved.**

## The hook I had to write myself

**Part 2 landed correct, proven and completely inert.** Nothing supplied the look-back, so the carry
step was a no-op on the production path — every surface, sentence and export change in place and
doing nothing. The build could not write it because it does not own that file. I wrote it and
proved it.

**Two stores, not one**, and this is the half a look-back over computed results alone would miss.
The serving layer takes a category from the specification store where that layer answered it and
from the computed store where it did not, so the same module's readings can sit in either
**depending on category**. A one-store look-back would miss readings **asymmetrically by
category**, which reads like a data problem rather than a code one. Specification rows are
normalised through the existing shared function rather than re-derived, so both stores arrive in
one shape.

**The ordering tiebreak is stated rather than left to the database:** period descending, then the
timestamp, then the row identifier, because that identifier is monotonic and the timestamp is a
server default two rows in one transaction can share.

**Live rows only, which is also the whole answer to your rule 3.** Removal supersedes rather than
deletes, so a removed period is simply **absent** from the look-back and it reaches past to the
most recent period the project still has. **No gap logic exists because none is needed** — and it
is why a carried reading names the period it came from rather than "the previous period", which
after a removal is reliably a different thing.

**Proved end to end by me through the real compute path**: a module abstaining at period 3 with an
Amber stored at period 1 carries that Amber, keeps period 1's evidence sentence verbatim, gives its
category a posture, and **remains in the abstained list**, which is your rule 6. With no history
the carried count is zero.

## The proofs

| # | result |
|---|---|
| 7 | **PASS** — carried, with source period, age, the original sentence, this period's reason beside it, and the period's own record stored |
| 8 | **PASS** — category posture moves from none to a band; contributors 0 to 1. A **current** reading of the same band gives the identical posture |
| 9 | **PASS** — no earlier reading stays unassessed; an earlier *bandless* reading also does not carry, because the band test is a band test |
| 10 | **PASS** — every excluded module refuses to carry an earlier band |
| 11 | **PASS, by browser observation with the collapsed state asserted** |
| 12 | **PASS** — exports carry the distinction |
| 13 | **PASS** — four injections, each observed producing the defect, each restored and the restore asserted |

Plus: cannot cross projects, cannot resurrect a retired module, and **with no history the run is
byte-identical to the pre-carry behaviour**.

## Counts that moved

On the measured fixture with one full earlier period:

| | no history | with a full earlier period |
|---|---|---|
| modules with a band | 0 | **25** |
| stored abstentions | 31 | **30** |
| categories with a posture | 0 | **4** |
| carried readings | 0 | **24** |

Banded rises by 25 while carried is 24, because the twenty-fifth is the weighted-voting module: it
is exempt from carrying but is *recomputed* from the postures carry-forward created. That is also
why stored abstentions fall by exactly one rather than by twenty-four — **rule 6 keeps the other
twenty-four in place.**

**The information-completeness figure does not move.** It counts document and field pairs and never
reads a module reading. **Your consequence 2 is half wrong**, and the honest result is that a
project can now publish a full status beside a completeness caveat that still correctly says it
rests on a fraction of the required information. That juxtaposition was made **more** prominent
rather than reconciled away: the card banner sits above the finding and says how many readings were
not taken from this period.

## One check regressed, and it is the one asserting the stance you replaced

Regression sweep on merged main: period removal 74/74, both Run 142 suites passing, mitigation
gate 20/20, card render 55/55, assembly 83/83, actual-cost selection 31/31, band contract 54/54.

**Period scoping went 74/77 to 73/77.** I measured both sides on fresh databases and diffed the
check lists. **Exactly one check was lost:**

> *"period 2: A3.2 still abstains — the period half is absent and nothing invents it"*

That check asserts the old stance. Under the new rule the module no longer abstains in that period;
it carries its earlier reading, marked. **I did not re-point it**, because what the correct new
expectation should be is a judgment about your decision rather than a mechanical repair, and because
leaving it failing shows the cost of the stance change rather than hiding it. It is a stale
expectation, not a defect, and it is the smallest possible follow-up.

---

## Three things needing your ruling

1. **The Category-9 gate arm is excluded, and I measured the cost of my own conservatism.** With
   it excluded: 4 of 5 required categories, status **Awaiting analysis**, not official. With it
   included: **5 of 5, official, a published band**. So the exclusion is not a detail —
   **Delivery Quality has no other arm on an ungoverned package, so with this exclusion a project
   can never reach an official status through carry-forward alone.** Reversible by deleting one
   entry from a list.
2. **Mitigation composition excludes carried readings entirely** — my direction. The fingerprint
   covers band and evidence but not the period, so a carried reading would **replay the earlier
   period's mitigation verbatim** with nothing saying the finding is stale. The alternative
   composes a fresh provider call for a finding that did not move.
3. **There is no horizon on the look-back, and none was invented.** The staleness gate refuses
   stale *evidence*; a carried *reading* is re-admitted without the gate seeing it again. The age
   in periods is surfaced on every row, in the status basis, in the card banner and in the brief's
   limitations — the gate's judgment made visible where it can no longer be applied. **A horizon
   is your number.**

## What this adds to the outstanding recomputation

The v70 recomputation was already outstanding. This adds to it **and changes its character**: v70
moved *figures* on two modules; **v71 changes which readings exist at all.**

Until a project is recomputed under v71 every carry-forward surface renders nothing, because no
stored row carries the marker. After recomputation, every project with more than one live period
shows **more banded modules, fewer displayed abstentions, more categories with a posture**, and
some move from *Awaiting analysis* to an official band. Every stored module-results export checksum
is invalidated twice over, by the new columns and by the rows themselves changing; the mismatch
message now names the stamp and the recomputation so that "checksum verification failed" is not
read as the platform accusing itself of tampering. **Rows stamped v70 and earlier are not
comparable with v71 rows on any abstention or banded count.**

## Iteration log

No finding needed more than one attempt in either part; nothing reached the cap and nothing was
reverted. The exceptions worth recording are the corrections rather than retries: the build's
correction to the survey about which bucket to read; the agent's own failed shared-document test
where the code was right and the test wrong; my own two false premises, the guard's line number and
the look-back function's name, both caught before they propagated; and one procedure error of mine,
where a baseline comparison left old files staged in the working tree and I restored from HEAD
before continuing.
