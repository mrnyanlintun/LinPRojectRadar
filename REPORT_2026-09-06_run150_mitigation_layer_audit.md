# Run 150 — the mitigation layer: audit, and a real defect in the boundary read

**`SIMULATION_VERSION` did not move** — `sim-2026.09-v73`, and `git diff` over `server/app/simulation/`
is empty. The provider routing, the mitigation role and every other role are untouched. **No
migration**: `0034` already carried what the design needs.

Starting commit `4ba774d`, ending `01de335`, pushed, tree clean.

---

## The correction, first: the layer already existed

The order states that the survey and the layer do not exist. **They do, and I verified that before
spending the run on a rebuild.** Run 140 built and merged all of it:

`mitigation.py` at 763 lines — the context builder, validator, storage, replay and fingerprint. The
`0034` migration, already head. Six check suites. The brief composing and serving a `mitigations`
key, the renderer, both exports and the stance sweep. **Run 140's report at the repository root is
Part 2's survey**, carrying the population, the shape counts, the per-module constant locations,
reading identity, exclusions, storage and the render path.

**So this run became an audit against your twelve proofs — and the audit found something.**

## The defect: the boundary read returned the rung *below*

Two sentence forms are in service. **Name-first** — *"Green at or above 0.90; Yellow at or above
0.75"* — used 26 times. **Name-last** — *"at or above 0.95 is Green; at or above 0.9 and below 0.95
is Yellow"* — used by **eight modules, and it is the majority form by module count**.

The extraction took the nearest number **after** the band's name. On the name-last form the figure
sits *before* its name, so the read ran past it into the next clause and returned the **next rung
down**.

**I reproduced this myself against the pre-fix code:**

```
PRE-FIX,  name-last, Yellow boundary -> 0.8      <-- the Amber floor
FIXED,    name-last, Yellow boundary -> 0.9      <-- correct
FIXED,    name-first, Yellow boundary -> 0.75    <-- correct
FIXED,    ordinal ladder             -> None     <-- correctly no number
```

**What that meant in practice:** a module banded Amber at a real 0.85 reported its Yellow boundary
as **0.8** — a figure its reading had **already passed** — presented to a reviewer as the edge to
reach. Every Run 140 fixture happened to use the name-first form, which is why 342 checks passed
over it.

Fixed by scoping to the clause naming the band, then taking the figure after its inclusive entry
phrase. Correct on both forms; ordinal ladders still correctly yield no number.

## Your proof 3, which is where this was found

You asked for the boundary read from the deciding constant, and for a demonstration that breaking
that read is caught. **Run 140's design is sound and is not one remove**: for constants resident in
the reference data, the sentence is built by interpolating the accessor directly, so the sentence
*carries* the constant rather than a copy of it.

**What was never proved is that the extraction returns it.** The new check compares the extracted
figure against the constant read independently through the same accessor the emitting module uses,
across real emissions at three real readings and all ten configured band sets on both sentence
forms. **It points one boundary at a stale copy, shows the comparison fail, and restores.**
Reverting the fix yields 25 failures, so it is not a check that cannot fail.

## The twelve proofs

| # | | |
|---|---|---|
| 1 survey | **already satisfied** — Run 140's report; 30 modules, one excluded structurally, shape counts, per-module constants |
| 2 four parts, programmatic | **already satisfied**, re-proved in-browser |
| **3 break the constant read** | **GAP CLOSED — and it found the defect above** |
| 4 override form, not a threshold gap | **already satisfied** |
| 5 unbanded or abstaining, zero calls | **already satisfied**, counted |
| 6 carried reading, zero calls | **already satisfied**, counted at the injection point |
| 7 validator refuses figure, role, date | **already satisfied**, all three in one pass |
| 8 replay byte-identical, zero second calls | **already satisfied**; **newly proved through the browser** |
| 9 failed call stores the absence line | **already satisfied** |
| 10 recomposition fires only on change, history kept | **already satisfied** |
| **11 browser, contrast, two themes** | **GAP CLOSED** — Run 140 proved strings, not a rendered page |
| 12 exports carry what the card showed | **already satisfied**; **newly proved** through the browser's own exporter |

**Counts, taken by me on merged main:** the two new suites at **36/36** and **35/35**; the six Run
140 suites unchanged at **342/342** in total, including the engine at 55/55, the exports at 138/138,
the stance sweep at 40/40 and the reveal gate at 20/20.

Contrast measured on two themes: values at 15.61 and 15.59 to one, labels at 5.35 and 5.79.

## Storage, render path, cost

**`0034` sufficed and no migration was written.** It carries the fingerprint, band, shape, context,
provider, model, prompt hash, template version, the mitigations, the composition date and the
supersede pointer, unique on project, period, module and fingerprint.

**The render path was traced, not taken from the filename** — one renderer, registered and reached
through a single call site. **Participant and researcher surfaces get identical content.**

**Cost, measured rather than estimated:** the prompt is **977 input tokens** against a 900-token
output cap. At Opus rates that is about **$0.008 per reading**, ceiling $0.027. Per period per
project: five readings is roughly **$0.04**; the full population of thirty is about **$0.24
typical, $0.81 worst case.** Once ever per reading-fingerprint — **every later render is free.**

**No stance-wording site needed changing.** Run 142's line is accurate and complete after this
build, and the sweep still passes.

---

## Will a mitigation appear on PRJ-002's card on the next render? **No.** Three things first, in order

**1. Rule on the reveal gate. This is yours and it is still open.** The mitigations key is served
only where the recommendation package is visible; **on a withheld read it is absent entirely, and
the card shows no blocks at all** — measured in the browser with five compositions stored. I made
that call at Run 140 to stop a composed treatment reaching a participant before their pre-judgment
is locked, reported it as that run's open decision, and no ruling came back. **Reversing it is one
line.** I did not change it.

**2. Deploy this run's boundary fix before any composition is stored.** Compositions are stored once
and replayed for ever. **Anything composed against the old read stores the wrong boundary
permanently**, and only recomposes if the reading itself changes. This is the ordering that matters
most.

**3. Confirm the deployment serves the post-Run-148 client.** A mitigation cannot render on a card
that renders nothing, and Run 148 established the deployed commit cannot be determined from the
tree.

Then the first revealed render composes. Your Anthropic key is set on the deployment, so it can
work there.

## The live composition is untested, and no key exists here

**No key of any kind is present in this container.** What served in its place: the real engine with
a counting fake injected at the composer's own caller parameter — a parameter production never
passes. **Nothing was simulated**, and the single live call to Anthropic remains unexercised.

## One thing worth knowing about earlier evidence

The agent noticed that Run 147's "the page is whole" screenshot shows a different instrument, not
the detail page. **Its DOM measurements were valid and its 24/24 stands, but its visual claim was
weaker than it read.** This run's contrast figures rest on computed styles and DOM reads rather
than on the image, which is the stronger basis, and I am recording the observation rather than
leaving it for someone to find.

## Iteration log

No finding needed more than one attempt. The correction worth recording is the order's own premise:
**the layer existed, and the run's value came from auditing it rather than building it again.** Had
it been rebuilt as instructed, the boundary defect would have been rebuilt with it or masked by new
fixtures in the same name-first form that hid it the first time.
