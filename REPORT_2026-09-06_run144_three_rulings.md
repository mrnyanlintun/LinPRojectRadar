# Run 144 — the three rulings Run 143 left open

**`SIMULATION_VERSION` moved to `sim-2026.09-v72`**, and it had to. Ruling 1 changes which
readings vote: on a package carrying no Category-9 assessment the same project goes from four of
five required categories and a withheld status to five of five and a published band. A stamp that
did not move would leave v71 and v72 rows looking comparable when their banded counts, abstention
counts and published status differ. The history tuple is **appended** to; v71 is untouched, and the
superseded marker is left at its Run-49 value. **No migration.**

Starting commit `2383bbd`, ending `9131403`, pushed, tree clean.

---

## What the Category-9 gate actually is

The question Run 123 left open is now answered, and I traced it myself before any ruling was
applied. The gate declares four verdicts by **what each does**, not what it says:

| verdict | what it does |
|---|---|
| **ALLOWED** | may be used, including as a vote on project status |
| **DEGRADED** | computed, stays on the ledger, and **may not vote** — stale against its source class's freshness requirement, or provenance incomplete |
| **ABSTAINED** | no value exists; the evidence required is absent |
| **REJECTED** | a value exists and **must not be used at all** |

**Degradation drops the vote entirely.** It does not weaken it and does not merely annotate. The
gate says so in terms: *"A degraded signal does not vote at nine tenths of a vote; it does not
vote."* The consumer side agrees: a signal the gate rejects or degrades has no band to offer and
therefore casts no vote.

## Whether tracing should have stopped ruling 1 — no, and here is why

**There are two refusal paths with two different reason codes**, and only one was on the block
list. I executed the eligibility test on all four codes rather than reading them:

| code | condition | carry-eligible |
|---|---|---|
| `module_execution_failed` | the module raised | **No** — and it stays blocked |
| `CATEGORY9_ASSESSMENT_MISSING` | **no assessment exists at all** | was No, now **Yes** — this is ruling 1 |
| `evidence_not_qualified_for_use` | evidence exists and the gate judged it unfit | **Yes** — never was blocked |
| `QUALIFICATION_CONTRACT_MISSING` | no declared route | **Yes** — never was blocked |

**What lifting the exclusion lets through is only the case where nothing was ever assessed.** That
refusal is documented as the governed abstention for a route blocked before any evidence could be
assessed; it marks the state unassessed, records that the consumer never executed, and is built on
the same primitive every missing-input module uses. **Nothing was degraded, nothing judged unfit,
nothing rejected — there was no verdict to defeat.** That is the missing-input shape, which is
exactly what the stance change says should carry. A degraded reading never reaches this code, so
**no degraded vote can count as a full one** and the stop condition does not fire.

The refusal site's own sentence promised that an earlier reading would not be shown either.
Leaving it would have shipped a lie, so it was rewritten. The neighbouring registry wording needed
no edit because it derives itself from the eligibility test and self-corrected.

---

## The finding the trace surfaced — and it is LIVE, not latent

**The `evidence_not_qualified_for_use` path is carry-eligible, was carry-eligible at v71 before
this run, and its own sentence promises the opposite verbatim:** *"No earlier reading is carried
forward in its place either: the refusal is about whether this evidence may be used at all, not
about a missing input."*

**The code makes a promise it does not keep.** I asked whether anything can actually reach that
path, because latent and active are different problems. **It is active, and I reproduced it
myself.** The evidence-qualification record is written on every document path, and it carries
material conflicts whenever two equal-precedence documents of the same date disagree on a field.
With a clean declaration, **no** module refuses on that code. With **one** material conflict, six
do:

```
clean declaration      -> []
one material conflict  -> ['A6.1', 'A6.2', 'A6.3', 'A6.4', 'B1.1', 'B1.2']
```

Two of those six are exempt from carrying by module identity anyway, so **the real exposure is the
four Delivery Quality modules** — the same category that gates the fifth vote. Driven end to end,
one of them carries a Green from an earlier period while the abstention sentence on the same
ledger says no earlier reading is carried.

**Not fixed, because the order says nothing else is in scope and this defect is not created by any
of the three rulings.** The fix is one entry added to the same list ruling 1 removed one from,
plus its own sentence rather than borrowing the failure path's. **`QUALIFICATION_CONTRACT_MISSING`
is adjacent and also unruled**: its sentence makes no carry promise, so it is not a contradiction,
but an undeclared route is documented as a configuration failure whose default branch is deny, and
carrying a band over it may not be wanted either.

**This is the run's open decision.**

---

## The six proofs

**1 — Ruling 1, before and after.** I re-ran this myself on merged main rather than accepting it:

| | required assessed | missing | project status |
|---|---|---|---|
| exclusion in place | 4 of 5 | `['A6']` | `Awaiting analysis` |
| **exclusion lifted** | **5 of 5** | `[]` | **`Yellow`** |

Delivery Quality is load-bearing exactly as your ruling says: all four of its in-service arms
refuse with the lifted code on an ungoverned package, which is asserted in the check rather than
quoted from the earlier run.

**2 — Ruling 1, failure.** Restoring the code to the list returns four categories, the category
missing, the module not carried and the status withheld. Reverted and re-asserted. **I ran this
injection myself and got the same three-way result.**

**3 — Ruling 2, counted not assumed.** The exclusion is **unedited**; only its comment moved from
"reported for an owner ruling" to the ruling. Counted at the injectable boundary: a carried adverse
reading builds no context and makes **zero** provider calls; an identical current row composes and
makes **exactly one**; a mixed card composes one block and one call, and the carried module gets no
block at all rather than an empty one. **All twelve carried adverse rows across the four modules
ruling 1 newly lets carry make zero calls.** The fault case — the same row with the marker removed
— composes and makes one call, so the zeros are about the exclusion rather than about the fixture.

**4 — Ruling 3, browser observation with the disclosure asserted closed.**

| theme | resolved token | age 1 | age 8 | age 40 | at 390px |
|---|---|---|---|---|---|
| dark | `#a6afc2` | 8.81:1 | 8.63:1 | 8.81:1 | 8.63:1 |
| light | `#55606f` | 5.90:1 | 5.90:1 | 5.90:1 | 5.90:1 |

Collapsed head text, verbatim: *"Schedule Performance Amber 1 of 1 reading is carried from an
earlier period, not this one, the oldest 8 stored periods back"*. A current reading renders no
note, no chip and no age.

**The agent caught its own first attempt being wrong**, which is worth recording: setting the theme
attribute on the served body does not survive, because the app's own bootstrap rewrites it, so all
three themes resolved to one palette at an identical ratio. The check now sets the theme after load
and **asserts the resolved palette tokens differ before trusting any contrast number**.

**No threshold was added.** Ages 1, 8 and 40 were compared on colour, background, font family,
size, weight and style, border and text decoration, and are byte-identical on every theme. There is
no cap, no warning word and no colour change. A reading at age **600** carries unclamped.

**5 — Ruling 3, exports.** The age was already a declared flat column, so nothing was added. Every
carried row states it, the ages are the stored ones rather than recomputed, a current row's column
is empty rather than zero, and the named period travels beside it so no subtraction is needed. The
decision brief printed *"1 stored periods back"* at age one; fixed, because the age is the whole
safeguard now and does not get to look like an unfilled template.

**What ruling 3 actually changed**, each surface checked before anything was added: the carried
label held the age only in a hover attribute, which is not a reading, so it moved into the label
and that gave the card and the network from one change; the ledger summary and the specification
panel head are the **only** carrying words a closed disclosure shows and stated a count with no
age, so both now state the oldest; the card banner suppressed the age at exactly one and now states
it at every value. The wording is **"stored periods back"** rather than "periods ago" — after Run
143's period removal those differ, and the shorter phrase is the more confident and the wrong one.

**6 — Nothing else moved.** The only production logic change is one entry removed from a frozen
set. No band boundary, ladder, threshold, weight or posture rule was touched. Confirmed by running
on merged main: the A1/A3 band contract 54/54, the Category-9 and no-band suite 21/21 including its
fault case, both Run 143 carry suites passing, period removal 74/74, assembly and precision 83/83,
and the Run 143 fault suite reporting every injection producing its defect and every restore
holding.

One Run 143 assertion was **re-pointed, not deleted**: it asserted that a Delivery Quality module
does not carry, which is the exclusion this ruling lifts, so asserting it would assert the reversed
stance. It is replaced by the ruling-1 check asserting the new behaviour, commented at the site.

---

## A finding reported and not applied

On one theme the age measures **2.92 to 2.97 to 1**, under the accessibility bar. That theme paints
a dark page while leaving the relevant colour token at the light default, so **every element
painted with that token is under the bar on that theme** — the no-data chip, the abstention reason
line, and Run 143's own carried note included. All predate this run. **The age inherits the gap; it
does not cause it.** The one-line fix is to declare the token in that theme's own block, and it was
not applied because repainting a theme's palette is outside the three rulings.

## The period-scoping check is still failing, and was left failing

**73 of 77 on merged main**, the same count as before this run, so Run 144 neither fixed nor
worsened it. The Run 143 line asserts that a module *still abstains* where the period half is
absent — an expectation that encodes the pre-carry stance. It is left failing deliberately: the
correct new expectation is a judgment about the stance change, and a failing check shows the cost
where a silent re-point would hide it. Three older stale population counts in the same suite
predate Run 143 and are untouched.

## What the recomputation must now cover

Not triggered. The outstanding list gains **every stored result at v71 or earlier, for every
project and period, on any package whose Category-9 assessment is absent for a gated measure.** Per
affected period a recompute converts up to four abstentions into carried banded readings, raising
the banded count, lowering the abstained count, and potentially moving a project from a withheld
status to a published band.

**One thing to flag, and it is the kind of gap this codebase keeps finding.** The staleness check
keys on the document set and on the presence of the qualification record. **It does not compare
simulation versions.** So this stamp move will **not** mark any row stale, and a recompute-all will
skip every one of them. **The recomputation has to be triggered deliberately; it will not happen as
a side effect of the deploy.** That is precisely the shape of an earlier run's note about a fix
never reaching an already-computed deployment.

## Iteration log

No finding needed more than one attempt. What is worth recording is the corrections rather than
retries: the browser check's first theme attempt measured one palette three times and was caught
and fixed before any number was trusted; the decision brief's singular-plural template was found
while proving the export; and one Run 143 assertion had to be re-pointed because the ruling
reverses what it asserted.
