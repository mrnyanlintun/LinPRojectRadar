# The risk register, the notices, and three forecasting modules that generate from nothing

**Date:** 2026-08-10
**Branch:** `claude/period-recompute-new-docs-1nfjnx`, from `origin/main` at `c212b16`
**Model:** Opus

**Verification:** server suite **53 suites, 2937/2937**, fresh migrated SQLite per test file (the
new `test_risk_register_and_notices.py` adds 114). `tests.html` **51/51**. `tests_render.html`
**233/234**, twelve net new checks, the one red the pre-existing auth-gated row. Two faults
injected, each hash-confirmed applied, detected and reverted. Real-browser drive of the card with
a register and two notices.

**Migrations 0024 (`project_risks`) and 0025 (`project_notices`) are new and UNAPPLIED IN
PRODUCTION.** Also unapplied, unchanged: **0020, 0021, 0022, 0023.** All migrations were run
against throwaway SQLite only. Production was neither inspected nor queried.

**The real document sets were not reachable.** They are on the owner's Windows machine and this
container cannot read them. Section 11 of the new suite is env-gated on `REAL_RISK_REGISTER` and
`REAL_NOTICE_DOC`, the same hook `REAL_SCHEDULE_DOCX` uses, and prints that the real checks did
not run rather than passing silently. **Run it locally before trusting any of this against the
corpus** — two defects on the schedule path were found on real documents and missed by fixtures,
and one was found here the same way (below).

---

## LEAD: what the three forecasting modules do now

**None of the three changed, and two of them fire the stop condition you set.** Reading each
one's arithmetic:

### Cost Risk Analysis P80 (`models_ext.py:483`, `Cost_Risk_Analysis`) — STOP AND REPORT

```python
eac = si["bac"] / si["cpi"]
uncertainty = max(0.03, abs(1 - si["cpi"])) * 0.5
p80_eac = eac * (1 + uncertainty * 1.28)
```

**What it needs:** a distribution of cost outcomes.
**What it has:** three literals. `0.03` is a floor on the coefficient of variation, `0.5` halves
the CPI deviation to make a "sigma", `1.28` is the normal z at the eightieth percentile. There is
no sample, no distribution object and no percentile computation anywhere in it. The entire spread
is derived from CPI, which is a cost-performance ratio and not a measure of dispersion.
**Can the register supply it:** yes in principle — probability and cost impact per risk is real
calibration data.
**Does it now compute or abstain:** **neither, and it is unchanged.** `uncertainty` is a scalar
multiplied into `eac` as a *fraction*; a register gives absolute dollars. Consuming it means
replacing that line with something like `mean = Σ pᵢ·impactᵢ`, `sigma = sqrt(Σ pᵢ(1−pᵢ)·impactᵢ²)`,
`p80 = eac + mean + 1.28·sigma` — which changes line 488 from multiplicative to additive, deletes
two of the three literals, and still asserts a normal approximation over a sum of Bernoullis that
is wrong for a handful of large risks. **That is its arithmetic changing, so I stopped.**

**Reproduced, not asserted.** The suite drives the real module and gets the reported figure back:

```
PASS  and reproduces the reported figure exactly: 10,555,811 at 79.7 per cent over budget
PASS  serving the register changes NOTHING in its answer: it has no slot for the data
```

The inputs that produce it are `cpi = 0.673`, `bac ≈ 5,874,620`. Note the 79.7 per cent is
measured against the platform's BAC, not against the authored 4,835,600 estimate at completion.

### Reference Class Forecasting (`models.py:184`, `Reference_Class_Forecasting`) — STOP AND REPORT

```python
ordered = sorted([1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52])
p50 = pctile(ordered, 0.50)   # -> 1.15, always
p80 = pctile(ordered, 0.80)   # -> 1.38, always
```

**What it needs:** outturn-to-estimate ratios from other completed comparable projects.
**What it has:** nine literal multipliers with no calibration file, no provenance record and no
data source anywhere in the repository. `pctile` is index-based and non-interpolating, so with
nine elements P80 is always index 6.

**Its overrun is +38.0 per cent on every project and every period, forever.** Asserted:

```
PASS  Reference Class Forecasting's percentiles are fixed literals  [1.15 / 1.38]
PASS  so its overrun is +38 per cent on EVERY project, whatever the inputs  [38.0 and 38.0]
PASS  and with NO budget at all it still returns a colour rather than abstaining  [Red]
```

**Can the register supply it:** **no, and this is the important one.** A reference class is the
OUTSIDE view: what happened on other projects. A risk register is this project's INSIDE view,
which is precisely the thing reference-class forecasting exists to replace. Feeding it the
register would invert the method while keeping its name and its Flyvbjerg citation. Its only
honest inputs are real comparable-project outturn data, which does not exist in this repository,
or abstention. **Unchanged, and reported.**

Note also that it cannot abstain today: `num(si.get("bac"), 0.0)` defaults a missing budget to
zero and still returns a colour into fusion.

### Parametric Cost Index (`models_ext.py:528`, `Parametric_Cost`) — THE PREMISE IS WRONG

```python
eac_cpi = si["bac"] / cpi
eac_parametric = si["ac"] + (si["bac"] - si["ev"])
index = eac_cpi / eac_parametric
```

**What it needs:** BAC, CPI, AC, EV. **What it has:** all four, extracted from real documents.
**It invents nothing.** There is no distribution, no sigma, no percentile and no prior; the only
literals are the RAG thresholds. It is a divergence ratio between two standard EAC conventions,
which is what its own evidence metric says.

Asserted, so this is a measurement and not an opinion:

```
PASS  and its answer MOVES with a real extracted figure, unlike a literal prior  [1.203 -> 0.995]
PASS  and it already abstains when its inputs are absent
```

**Including it in the fabricating set was a misdiagnosis.** Its *name* oversells it — it is not a
parametric estimate — but that is a naming question, not a data or abstention one. A risk
register has no place in this arithmetic and inserting one would make it a different quantity
under a misleading name. **Unchanged, deliberately.**

### One module outside the three that will bite

`Monte_Carlo` (`models_sim.py`) stores the same `p80_eac` key and the card fell back to it when
Cost Risk Analysis was absent. Its spread is `0.5·(1−cpi) + 0.3·(1−spi) + 0.2·doc_score`, a 0.15
CUSUM penalty and a 0.10/0.40 Beta-PERT spread — a *larger* invented-parameter surface. Making
Cost Risk Analysis abstain and doing nothing else would have re-sourced the same sentence from a
worse module.

### What protects the reader in the meantime

`server/app/simulation/` was out of bounds, but the card is not. **No eightieth percentile is
printed any more, from either module.** What the card prints instead is the exposure the register
supports: the sum of probability times cost impact over the risks that state both, with the count
of how many that was. On the drive below that is **170,250 dollars**, which is exactly
`0.35 × 450,000 + 0.15 × 85,000` from two named risks. Every figure has an input behind it.

The exposure is also **served** to the analytical layer as `si["registerExposure"]`, by the same
route `milestoneHistory` uses, so the data is in place the moment the arithmetic change is
authorised. No module consumes it today, and the code says so rather than leaving it to be
discovered.

---

## What the recommendation can say that it could not

Before: a register was a document risk score and a date, so the card could say only that a
register was present and unread. Now, quoted verbatim from the rendered card on the drive:

> **What the risk register records**
>
> 3 open risks in the register for this period. Bands are quoted as the register wrote them and
> are never turned into numbers.
>
> - R-002, Utility relocation delayed by a third party is open: scored 20 by the register,
>   likelihood **High**, cost impact 120,000 dollars, time impact 45 days. The register records it
>   owned by **M. Chen**, response **Transfer**, residual position High.
> - R-001, Unforeseen ground conditions at the apron slab is open: scored 12 by the register,
>   likelihood **35 per cent**, cost impact 450,000 dollars, time impact 30 days. The register
>   records it owned by J. Alvarez, response Mitigate, residual position Medium.
> - R-004, Night work productivity shortfall is open: scored 6 by the register, likelihood 15 per
>   cent, cost impact 85,000 dollars, time impact 10 days. The register records it owned by
>   S. Okafor, response Mitigate, residual position Low.
>
> **Notices served this period**
>
> - A notice was served on 2026-04-18. **Not established: the notice does not name a contract form
>   this platform holds periods for, so no deadline is derived.** Read from
>   Notice of Delay 2026-04-18.pdf.
> - A Contractor, LLC served notice on North Concourse Authority on 2026-04-18. It claims a
>   differing site condition encountered at the apron slab subgrade. It references RFI 214 and
>   Risk R-001 of the Project Risk Register. **The deadline it starts is 2026-05-02 (A201-2017
>   Section 3.7.4).** Read from Consequence Correspondence 2026-04-18.docx.

And in the courses of action, where an eightieth percentile used to sit:

> It closes off nothing, and it spends a reporting period during which the position is unchanged:
> **a risk exposure of 170,250 dollars, being the sum of probability times cost impact across the
> 2 risks in the register that state both.**

Three things worth noting in that output. **R-002 is ordered first because the register scored it
20**, not because this platform ranked anything. **Its likelihood reads "High"** because that is
what the register wrote; R-001's reads "35 per cent" because that is what *it* wrote. And the two
notices differ exactly as they should: the one naming a form gets a derived date, the one naming
none gets a stated reason.

---

## Part 1: what is read, what refuses

**The rows come from the document, not from the model.** `risk_register.find_risk_table` resolves
the columns once per table and takes the rows; the table is elided from the prompt with its
header row left standing. Measured:

```
PASS  self-test: un-elided, a 500-row register is far larger than a 20-row one  [1584 vs 40584]
PASS  elided, the text sent to the model differs by at most the row-count digits
      [1030 vs 1031 chars, delta 1]
PASS  and all five hundred rows are read  [500]
```

**Per risk, stored:** id, description, category, probability (numeric) or band, cost impact, time
impact in days, score, owner, response strategy, mitigation status, residual position, open or
closed, refusals, and whether the row is usable for exposure.

**Handled and refused, as asked:**

| Shape | Example | Outcome |
|---|---|---|
| percentage | `30%`, `30 per cent` | read, 0.30 |
| fraction | `0.3`, `.3` | read, 0.30 |
| bare number, `%` in the heading | `40` under "Probability (%)" | read, 0.40 |
| **bare number, no unit anywhere** | `40` | **refuses**, naming the ambiguity |
| **word** | `High`, `Remote`, `Likely` | **band recorded, refused as a number** |
| **ordinal** | `4 of 5`, `3/5` | **band recorded, refused as a number** |
| **banded range** | `Medium (30-50%)` | **band recorded; the midpoint is not taken** |
| money | `$120,000`, `1.2M`, `450k`, `(45,000)` | read (negative preserved) |
| **money, other currency** | `£90,000` | **refuses** rather than being summed as dollars |
| duration | `10 days`, `2 weeks`, `1 month` | read into days |
| **bare duration** | `14` with no unit | **refuses** unless the heading states the unit |
| status | `Open`, `Closed` | read |
| **`Mitigated`** | | **refuses**: it states treatment, not whether the risk is carried |

**Why a word is never converted.** "High" has no numeric value the document states. Mapping it to
0.7, or to the midpoint of a stated range, imports a number from outside the document and then
presents it as read — which is the same class of act as an eightieth percentile with no
distribution. The band is kept and quoted; it simply cannot enter a cost distribution.

**A refusal never drops the row.** A register of two hundred risks that yielded ninety usable
probabilities has to say which hundred and ten refused and why.

**The P1 invariant, proven with a later period's register in place:**

```
PASS  each period holds its own account of the register, not a merged one  [period 1: 4, period 2: 3]
PASS  the SAME risk in two periods is two rows with the two periods' own values  [0.35 then 0.8]
PASS  RECOMPUTING PERIOD 1 AFTER A LATER PERIOD'S REGISTER EXISTS IS BYTE-IDENTICAL
PASS  and the recompute inserted no duplicate risk rows  [4]
PASS  and period 1's card still reports period 1's register, not period 2's  [3]
```

That check is not vacuous: the exposure genuinely reaches the stored `signal_inputs`
(`registerExposure`, asserted present with `usable_count` 1 and the sum the register implies).

**A defect found the way the brief predicted.** The first realistic register tried had a column
headed `Schedule Impact (days)`. Exact heading matching, which is what the schedule reader uses,
resolved it to no field at all and **every time impact in the table was silently dropped**. The
register reader now tolerates a trailing unit qualifier and reads the unit from it, exact match
first so a bare "Cost" cannot steal an exact "Cost Impact" column. **The same brittleness exists
in `schedule_activities._HEADINGS`** — a column headed "Baseline finish (date)" would resolve to
nothing there — and I did not touch it, because the schedule has its own suite and its own P1
invariant. Worth a follow-up.

---

## Part 4: the notice as an event

Extracted from the notice's prose: who served it, on whom, what it claims, the date served, the
contract form it names, what kind of notice it is, and what it references. **The deadline is not
among them** — a model-stated deadline is a date with no rule behind it. It is derived in code by
`contract_notices.deadline_for` from the form the document named, and stored with its clause
citation and the basis sentence.

The three traps from `training_us_contract_regimes.md` are encoded as behaviour:

| | Encoded as |
|---|---|
| A201 differing site conditions is **14 days**, not the 2007 edition's 21 | `A201-2017 §3.7.4`, pinned by a check that 18 April yields 2 May |
| ConsensusDocs is a **two-step** clock: 14 days' notice, then 21 days for documentation **measured from the notice** | a separate `second_step` field with its own base date, so a single deadline cannot silently drop it |
| The federal **20 days is a lookback, not a deadline** | `kind = "lookback"`, carries its day count and **no date**; the card prints "This bars no claim" |

Where the form is not established, no deadline is stated and the reason is carried instead —
demonstrated on the drive above by the two notices side by side. The date that starts the clock
uses `parse_schedule_date`, which refuses rather than inferring a year, and its refusal is stored.

Periods are transcribed with their provenance caveat intact: A201 and ConsensusDocs figures come
from secondary summaries rather than the licensed documents, and contract periods are routinely
amended in negotiation. That caveat is attached to every derived deadline, not buried here.

**Commissioning Report was left alone**, as instructed.

---

## Tests that went red, and which kind each was

Three, and they are three different kinds:

1. **`"the stored completion estimate is quoted exactly"`** (`tests_render.html` group 15) —
   asserted that `15,748,571 dollars, 31.2 per cent above budget` appears. That figure is the
   fabricated percentile. **It recorded the defect.** Replaced by two checks that no eightieth
   percentile and no such figure appears, and the percentile came off the numeric allowlist so
   its reappearance anywhere in the block now fails.

2. **`"the figure scan actually saw figures"`** — an anti-vacuity guard on the allowlist scan.
   **It protects a real property** and went red only because the fixture had fewer numbers once
   the percentile went. Threshold adjusted; the guard stands.

3. **`"a document whose content is not stored is reported by name, not omitted"`**
   (`test_period_picker_and_evidence.py`) — **a third kind: a property whose mechanism moved.**
   The property is real and is kept: a document present in the period must never be silently
   absent. What changed is that a notice's content *is* stored now, so asserting the card still
   calls it unread would pin a limitation that has been removed. Re-pointed to assert the notice
   is listed as read and is no longer reported as unreadable.

## Faults injected

| Fault | Detected by | Result |
|---|---|---|
| Map a likelihood band to a number (`High` → 0.7) | **11 checks** | including the two self-tests, every band case, the stored row, and the exposure usability flag |
| Remove the period bound on the risk reader | 1 check | period 1's card reported 6 open risks instead of 3 |

Both hash-confirmed applied and hash-confirmed reverted, with the baseline re-run green after each.

Note what the second fault did **not** move: the byte-identical check stayed green, because that
reader feeds display only. The stored-row invariant is protected separately, by the period bound
in `_persist_project_risks` and by `_period_risks` being period-equal rather than period-bounded.

## Not done

- **No module arithmetic changed.** `server/app/simulation/` carries only what it carried.
- No fee-basis vocabulary, no changes to `field_registry.py`, no changes to Commissioning Report.
- The real document sets were not run against. Section 11 is waiting for the two paths.
