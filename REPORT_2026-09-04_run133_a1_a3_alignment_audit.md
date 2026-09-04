# Run 133 — A1/A3 Specification-to-Code Alignment Audit

**`server/app/simulation/` WAS NOT MODIFIED. `SIMULATION_VERSION` DID NOT MOVE and remains
`sim-2026.09-v68`.** No module, band, threshold, constant, weight or category rule was changed by
this run. The only tracked files added are one new check script and this report.

**OUTCOME B — ALIGNMENT BLOCKED, INVENTORY COMPLETE.** Not because the evidence is thin, but
because it is decisive in the opposite direction from the order's provisional hierarchy, and
acting on it requires one owner decision this run is not authorised to take for him.

---

## Goal and scope

To determine, for A1.6 Earned Schedule, A1.7 TCPI, A1.8 Variance at Completion, A1.9 Budget
Execution, A3.2 Contingency Burn and A3.5 Overhead Absorption, whether the written specification
and the running instrument describe the same thing; and where they do not, to establish which of
them is authoritative before touching either.

The order's own governing principle required that a different formal source-of-truth hierarchy,
if the repository establishes one, be reported with evidence before being applied. The repository
establishes one. It is reported below and it inverts the order's. That is the finding of this run.

---

## Repository and environment

| Item | Value |
|---|---|
| Repository root | `/home/user/LinPRojectRadar` |
| Branch | `main` |
| Starting commit | `e853cb2da1db147b9eedc0edce6ae91a79a57dbe` |
| `HEAD == origin/main` | **Yes**, both `e853cb2` |
| Worktree at start | Clean — `git status --porcelain` produced no output |
| `SIMULATION_VERSION` | `sim-2026.09-v68`, `server/app/simulation/models.py:1047`. **Unmoved.** |
| Migration head | `server/alembic/versions/0033_recognition_matches.py`. **No migration added; none required.** |
| Python | `/usr/local/bin/python`, no `.venv` |
| Test command | Check scripts run with cwd = `server/`, e.g. `/usr/local/bin/python tools/test_run133_a1_a3_band_contract.py` |
| Data stores contacted | **None.** Every check in this run executes pure module functions on constructed dictionaries. No database session was opened, no `DATABASE_URL` was read, no HTTP route was called. |
| Model keys | Absent, all three. `StubExtractor` serves. **No model call was made or simulated.** |
| Production Postgres | **Never contacted.** No participant-facing store was read or written. |

**Owner's pre-checked facts: all six verified correct.** Commit, branch, remote parity, clean
worktree, `SIMULATION_VERSION` location and value, migration head, and the existence and line
counts of the specification files were each confirmed independently. Nothing in the briefing was
found to be wrong on the facts. Two things in it were found to be **incomplete**, and both
enlarge the finding rather than contradict it — see §"What the briefing did not know".

---

## Source-of-truth evidence — CRUX 1 resolved

### The two documents in conflict

**`T6_HANDOFF.md` lines 1–7**, the owner's ruling of 2026-08-25, Run 59, verbatim:

> **THIS FILE IS HISTORY. IT CARRIES NO AUTHORITY.** … No markdown document in this repository
> carries authority: production code is the truth, `REPORT_*.md` / `code_audit/REPORT_*.md` /
> `research/freeze/*.md` / the fixture records are sealed evidence, and everything else — this
> file included — is transport or history and governs nothing. Where this file and the code
> disagree, THE CODE IS TRUE.

The owner's briefing observed correctly that `specifications/*.md` is **not** in the sealed-evidence
list, and asked whether the sweeping sentence overreaches.

**It does not overreach, and the specification folder answers the question about itself.**
`specifications/README.md`, written at Run 76, states its own status in terms:

> These specifications are **DERIVED, not composed**. Every formula, every threshold, every
> citation and every sentence of refusal below is **transcribed from the module's own Python
> source in `server/app/simulation/`, which is the record of what the module was meant to do**.
> … **Nothing here changes what a module computes.**

That is not a document claiming authority over the code. It is a document declaring itself a
**transcription of the code**, disclaiming any power to change what a module computes, and naming
the Python source as "the record of what the module was meant to do". The two documents therefore
do not conflict at all. `specifications/` is omitted from Run 59's sealed-evidence list because it
is not evidence of a decision — it is derived commentary, and its own README says so.

### Verdict on CRUX 1

**The code governs.** The hierarchy the repository actually establishes is:

```
production code in server/app/simulation/
  > sealed evidence (REPORT_*.md, code_audit/REPORT_*.md, research/freeze/*.md, fixture records)
    > everything else, including specifications/, which is DERIVED transcription
```

This is the exact inverse of the order's provisional hierarchy, which placed "explicit approved
specification" first and "implementation" fourth. **The order's own governing principle instructed
me to report this with evidence before applying it, and that is what this section does.** I have
applied the repository's hierarchy, not the order's, on three grounds:

1. Run 59 is an explicit, dated owner ruling on precisely this question.
2. `specifications/README.md` independently disclaims specification authority, in its own words,
   and names the Python source as the record.
3. It is corroborated by observed practice — see CRUX 2, where the specifications demonstrably
   trail owner decisions by weeks and were never updated to record them.

This is **not** the order's first stop condition. There are no conflicting specification versions;
there is one specification, and the repository has settled that it does not govern. What is
blocked is something narrower and is stated in §"Blockers and owner decisions".

---

## CRUX 2 — is there a documented later owner decision? **Yes. Two of them, and they are decisive.**

The briefing's session note about "a Run 107 order titled the eight thresholds" was hearsay. It is
now a finding, proved from the repository, and there is a second one the note did not contain.

### Run 107, 2026-09-02 — "the eight thresholds"

`REPORT_2026-09-02_run107.md` exists at repository root and is sealed evidence under Run 59. Its
own table records the outcome, and the modules it names are exactly the ones in dispute:

| module | Run 107 outcome |
|---|---|
| A1.5 ARIMA CPI Forecast | bands, worst-of three forecast periods |
| **A1.6 Earned Schedule** | **bands** — SPI(t) ladder 0.95/0.90/0.85 plus a time-variance arm |
| **A1.9 Budget Execution Rate** | **bands** |
| A1.11 Independent EAC Reconciliation | bands |
| A4.5, A4.7, A4.8, A4.9 | band |

The code carries the decision's identity, not merely its numbers.
`server/app/simulation/models_evm.py:49` defines
`_RUN107_BASIS_ID = "owner_configured_construction_control_tolerance"`, and `_run107_basis()`
attaches to every one of those readings the sentence *"the owner's Run 107 order, section 1,
A1.x … OWNER-CALIBRATED: no published standard fixes these … They are a documented owner
tolerance, stated as the owner's own decision and not presented as a construction standard."*
A1.6's own code comment quotes the order: *"The owner's order: 'Forecast CPI for the next three
periods; band the worst of the three… A near-term Green does not offset a third-period Red.'"*

### Run 114, 2026-09-02 — the two Yellow rungs

`git log -S"_TCPI_OWNER_YELLOW"` and `git log -S"_VAC_OWNER_YELLOW_PCT"` both return **exactly one
commit**: `fc9d60c` — *"Run 114: the document fields, the picker, and two Yellow rungs"*. The code
comment at `models_evm.py:592` quotes the owner directly:

> **1.05 IS THE OWNER'S RULING, stated in his Run 114 order in these words: "A1.7 TCPI — Green
> <= 1.00, Yellow > 1.00 to 1.05, Amber > 1.05 to 1.10, Red > 1.10."**

`REPORT_2026-09-02_run114.md` §345 tabulates it, and §354 records that A1.8's Yellow rung is the
**same ruling carried across by an exact identity** — `VAC% = (1 − 1/CPI) × 100`, so a CPI
boundary *is* a percentage boundary — placing the rung at CPI 0.95, the planned index moved by
half the Christensen and Heise stability margin, recorded OWNER-CALIBRATED and expressly **not**
inheriting the CONVENTION class the 1.10 and the −11.11 carry. Both reports state the existing
Green and Red edges did not move: the rung was *inserted*, not a re-banding.

### The decisive corroboration the briefing did not have

```
$ grep -rln "Run 107\|RUN 107" specifications/   →  (no matches)
$ grep -rln "Run 114\|RUN 114" specifications/   →  (no matches)
```

**No specification file mentions Run 107 or Run 114 anywhere.** And the omission is uniform:
`specifications/A4_document_derived_signals.md` lines 370, 464, 499 and 533 — A4.5, A4.7, A4.8 and
A4.9, the other four modules Run 107 banded — *still* read **"Bands. None. This module asserts no
band and none may be attached."** The A4 spec's last content commit is Run 106; A1's is Run 96.

Contrast A3, which is **current**: `specifications/A3_cost_risk.md:54` reads *"Bands. RUN 101, THE
OWNER'S ORDER, SECTION 3.1"*, and line 189 records that *"THE OWNER SUPPLIED THE BASIS AT RUN 103
AND THIS MODULE BANDS"*. The A3 specification was updated when the owner supplied bands. The A1
and A4 specifications were not.

**Verdict on CRUX 2: there is a documented, dated, owner-authorised later decision — two of them —
and the specification is the stale artefact.** This is the order's last stop condition, met
squarely: *"the code's alternate bands have a documented approved rationale that contradicts the
specification's."*

---

## Disagreement inventory

Complete, and recorded before any change was contemplated. No implementation change was made.

| Metric | Divergence type | User-visible effect | Affected code/tests | Affected corpus scope | Smallest safe correction | Validation proof |
|---|---|---|---|---|---|---|
| A1.6 Earned Schedule | **Specification defect** — spec §162 stale since Run 107 | None. Code is right. | `specifications/A1_cost_and_evm.md:162` only | None | Rewrite the spec's Bands section to record the Run 107 ladder | `tools/test_run133_a1_a3_band_contract.py`; Run 107 report; `_RUN107_BASIS_ID` on the row |
| A1.9 Budget Execution | **Specification defect** — spec §382 stale since Run 107 | None. Code is right. | `specifications/A1_cost_and_evm.md:382` only | None | As above | As above |
| A1.7 TCPI | **Specification defect** — spec predates Run 114 | None. Code is right. | Spec only | None | Record the Yellow rung at 1.05, OWNER-CALIBRATED | 10 executed boundary checks |
| A1.8 VAC | **Specification defect** — spec predates Run 114 | None on the band contract. | Spec only | None | Record the Yellow rung at CPI 0.95 | 9 executed boundary checks |
| **A1.8 VAC (second, separate)** | **REAL IMPLEMENTATION DEFECT — floating-point boundary** | **A project at CPI exactly 0.95 reads Amber where the owner's ruling says Yellow. A1.8 is a CORE VOTING MODULE, so this moves a project status.** | `server/app/simulation/models_evm.py:793` vs `:818–824` | Any project landing exactly on CPI 0.95 | Compare on the index, or build the constant by the module's own arithmetic path — **inside the forbidden tree** | Measured; see §Tests |
| A1.5, A1.11, A4.5, A4.7, A4.8, A4.9 | **Specification defect, same cause, OUT OF THIS RUN'S SCOPE** | None | Spec files only | None | Same correction, separate run | `grep` for Run 107/114 in `specifications/` returns nothing |
| A3.2 Contingency Burn | **Aligned** | — | — | — | **None. Changed nothing.** | 10 executed boundary checks |
| A3.5 Overhead Absorption | **Aligned; the prior manual reading was the error** | — | — | — | **None. Changed nothing.** | 10 executed checks including a decisive discriminator |

---

## Metric-by-metric dispositions

| Metric | Spec formula/basis | Spec bands | Code formula/basis | Code bands and boundaries | Test contract | PRJ-002 P1 output | Agreement | Provenance | Required action |
|---|---|---|---|---|---|---|---|---|---|
| **A1.6 Earned Schedule** | ES by interpolation on the cumulative PV curve; `SV(t)=ES−AT`; `SPI(t)=ES/AT` | *"None, and none may be attached"* (line 162) | **Identical formula** | SPI(t): ≥0.95 Green, ≥0.90 Yellow, ≥0.85 Amber, else Red — **inclusive on the lower side**, adverse downward; plus a time-variance-share arm; worst-of aggregation | New: basis-id check | Not computable — no time-phased baseline reaches the module; abstains | **Formula agrees; bands disagree** | Code = Run 107 order, `_RUN107_BASIS_ID`. Spec = Run 76/96, stale. | **Correct the specification.** Code is right. |
| **A1.7 TCPI** | `(BAC−EV)/(BAC−AC)` | Green ≤1.00, Amber to 1.10, Red above; no Yellow | **Identical formula**, plus domain guards and an abstention when `BAC−AC ≤ 0` | Green ≤1.00; **Yellow ≤1.05**; Amber ≤1.10; Red above. Band taken from the **full-precision** value; `tcpi_display` is presentation only | 10 boundary checks | **TCPI 1.077273 → Amber** | **Formula agrees; a Yellow rung the spec predates** | Code = Run 114 order quoted verbatim, commit `fc9d60c`. Run 35 full-precision ruling **still holds — verified executably.** | **Correct the specification.** Code is right. |
| **A1.8 VAC** | `EAC=BAC/CPI`, `VAC=BAC−EAC`, `VAC%=VAC/BAC×100` | Green ≥0, Amber to −11.11%, Red below; no Yellow | **Identical formula** | Green ≥0; **Yellow ≥ −5.263157894736842%** (CPI 0.95); Amber ≥ **−11.11111111111111%**, which is **computed as `(1 − 1/0.90) × 100`, not written as a rounded literal — verified**; Red below | 9 boundary checks | **VAC −4.683196% → Yellow** | **Formula agrees; Yellow rung the spec predates; PLUS a real float defect at the Yellow edge** | Code = Run 114, carried by the exact CPI identity | **Correct the specification; and the owner must rule on the float defect.** |
| **A1.9 Budget Execution** | `ExecutionRatio = AC(t)/ExpectedSpend(t)` off the approved expenditure baseline | *"None, and none may be attached"* (line 382) | **Identical formula** | Bands on the ratio, cumulative and period arms, Run 107 ladder | New: basis-id check | Not computable — no approved expenditure baseline; abstains | **Formula agrees; bands disagree** | Code = Run 107 | **Correct the specification.** Code is right. |
| **A3.2 Contingency Burn** | `C=(Orig−Rem)/Orig`; `NormalisedBurn = C/ProgressFraction` | Run 101 §3.1: ≤1.0 Green; >1.0–1.2 Yellow; **>1.2–1.5 Amber**; >1.5 Red, or contingency exhausted while work remains | **Identical** | **Exactly as specified**, every boundary inclusive on its upper side; band on the progress-normalised burn **only**, never on the consumed share alone; exhaustion arm applied against reported percent complete with the limitation printed on the row | 10 boundary checks | **Burn 0.66 at 60.5% complete → Green** | **ALIGNED IN FULL** | Spec and code both cite Run 101 §3.1 | **NONE. Changed nothing.** |
| **A3.5 Overhead Absorption** | Run 103 §4: bands on **absorption variance** = `(actual overhead incurred − planned overhead absorbed)/planned overhead absorbed`; positive is unfavourable | ≤5% Green; >5–10 Yellow; >10–15 Amber; >15 Red; a favourable variance is Green | **Bands the absorption variance.** The **rate** variance is computed and reported but expressly does **not** band — the code says so in terms: *"Attaching his bands to the rate variance would be attaching a band to a quantity it was not drawn over."* Thresholds come from `band_reference_data.json` → `overhead_absorption_variance_bands` (0.05/0.10/0.15), plus a substantial-completion floor that lifts Green/Yellow to Amber only on a **declared** contractual state and a **stated** unabsorbed amount | 10 checks incl. a discriminator | Not computable — no overhead allocation base record; abstains | **ALIGNED IN FULL** | Spec §189 and code both cite Run 103 §4 | **NONE. The prior manual reading that used rate variance was the error, exactly as the order suspected. Code untouched.** |

### Classification, per the order's five-way taxonomy

| Finding | Class |
|---|---|
| A1.6 spec says unbanded, code bands | **2 — specification defect** |
| A1.9 spec says unbanded, code bands | **2 — specification defect** |
| A1.7 Yellow rung | **2 — specification defect** (spec predates the ruling) |
| A1.8 Yellow rung | **2 — specification defect** |
| A1.8 float boundary at CPI 0.95 | **1 — real implementation defect** |
| A3.2 at 1.5 | **5 — correctly implemented rule; the reported behaviour was correct and is confirmed** |
| A3.5 rate vs absorption variance | **3 — documentation/reading error**, exactly as the order anticipated |
| A1.5, A1.11, A4.5, A4.7–A4.9 stale prohibition | **2 — specification defect, out of scope** |

**Not one implementation defect was found in the band ladders.** The four divergences the order
listed are all real divergences, and in every case the **specification** is the stale side.

---

## Tests and boundary proofs

New file, added: **`server/tools/test_run133_a1_a3_band_contract.py`** — 53 checks, **53 passed, 0
failed**. It executes the modules themselves on constructed inputs. No database, no model call, no
route. It is the executable band contract the order asked for, and it is the regression test that
catches any future drift between a written band and the executable constant.

```
$ cd server && /usr/local/bin/python tools/test_run133_a1_a3_band_contract.py
53 passed, 0 failed
```

**A1.7 TCPI** — 1.00 Green · 1.0001 Yellow · 1.05 Yellow · 1.0501 Amber · 1.10 Amber · 1.1001 Red.
Constants pinned at 1.00/1.05/1.10. **Run 35's standing ruling re-proved executably**: at TCPI
1.0004 — which `_round3` renders as 1.0 — the module reads **Yellow**, so the band is still taken
from the full-precision value and never from the rounded one.

**A1.8 VAC** — driven by the cost performance index itself, since the percentage is an exact
restatement of it, so the check introduces no round-trip of its own. CPI 1.00 Green (exactly 0.00
per cent) · 0.99999999 Yellow · **0.95 Amber (the defect)** · 0.9499999 Amber · 0.90 Amber ·
0.8999999 Red. The Amber edge is verified equal to `(1 − 1/0.90) × 100` and verified **not** equal
to the literal −11.11.

**A3.2** — every boundary built from exactly representable inputs. 1.0 Green · 1.0204 Yellow ·
**1.2 Yellow** · just above Amber · **1.5 Amber** · just above Red · 1.6 Red. **The order's
question is answered: the code already produces Amber at 1.5, every boundary matches, and it is
recorded as aligned with nothing changed.**

**A3.5** — 5% Green · 5.01% Yellow · 10% Yellow · 10.01% Amber · 15% Amber · 15.01% Red · −30%
(favourable) Green. **The decisive discriminator**: a case constructed with a 5 per cent absorption
variance but a **110 per cent rate variance**, by halving the allocation-base driver. The module
reports the rate variance as 1.1 and **still reads Green**. Had it banded the rate variance it
would have read Red. This proves the banded quantity is the absorption variance.

### Every new check proved able to fail

Three faults were introduced into the working copy, observed, and removed:

| Fault introduced | Checks that failed |
|---|---|
| `_TCPI_OWNER_YELLOW` collapsed 1.05 → 1.00 (i.e. "remove Yellow") | 4, incl. the constant pin and the full-precision check |
| A3.2 Amber made exclusive at 1.5 (`<=` → `<`) | 2, incl. the 1.5-is-Amber check by name |
| A3.5 banded on `relative_rate_variance` instead of the absorption variance | 1 — the discriminator |

Fault run: **46 passed, 7 failed**. Both module files were then restored from copies taken before
the edit, and `git status --porcelain` confirmed the working tree carried no modification to any
tracked file. **`server/app/simulation/` is byte-identical to `e853cb2`.**

### Neighbouring suites, re-run at final state

```
tools/test_run132_actual_cost_selection.py   31 passed, 0 failed
tools/test_run34_version_boundary.py         RESULT: 18/18 checks passed
```

`tools/test_run34_holdout_provenance.py` still fails on the pre-existing
`ImportError: portfolio_health`. **Confirmed pre-existing and not this run's** — no file it
imports was touched.

---

## PRJ-002 Period 1 readout

Independently re-derived from the figures the documents state, as pinned in
`server/tools/test_run132_actual_cost_selection.py` §24 and computed by executing the modules.

**Inputs and provenance.** BAC $3,000,000 · PV $1,900,000 · EV $1,815,000 · **AC $1,900,000**.
The actual cost is the **monthly report's stated `actual_cost`** — this is the Run 132 selection,
under which a pay application's `amount_paid_to_date` ($1,633,500, net of ten per cent retainage)
is no longer emitted to `ac` at all. Provenance is internally consistent: EV $1,815,000 equals the
pay application's `completed_to_date`, and 60.5 per cent complete is stated on both documents.

**A1.**
- CPI = 1,815,000 / 1,900,000 = **0.955263** (over cost)
- **A1.7 TCPI** = (3,000,000 − 1,815,000)/(3,000,000 − 1,900,000) = 1,185,000/1,100,000 =
  **1.077273** → **AMBER** (above 1.05, at or below 1.10). Band from the full-precision value.
- **A1.8 VAC** — EAC = BAC/CPI = $3,140,495.87; VAC = **−$140,495.87**; VAC% =
  **−4.683196%** → **YELLOW** (at or above −5.263158%). **This is the Run 114 rung doing work on a
  real project**: under the specification's stale ladder the same figure reads Amber.
- **A1.6 Earned Schedule** — **abstains.** No `timePhasedBaseline` reaches the module. Withheld
  with its stated sentence, not coerced into a posture.
- **A1.9 Budget Execution** — **abstains.** No approved expenditure baseline. Withheld likewise.

**A3.**
- **A3.2 Contingency Burn** — original $150,000, remaining $90,000 → consumed fraction **0.40**;
  progress 60.5% → normalised burn **0.66** → **GREEN** (at or below 1.0). The exhaustion arm did
  not fire: remaining contingency is above zero.
- **A3.5 Overhead Absorption** — **abstains.** No `overheadAllocationBase` record reaches it.

**Before and after: IDENTICAL.** No band, no value, no posture and no rendered word changed,
because **this run changed no code.** The A1 and A3 category postures, the official project
posture, the Weighted Voting diagnostic and the rendered Decision Brief are therefore also
unchanged from `e853cb2`. The full-corpus category roll-up was deliberately **not** recomputed:
recomputation is authorised only once a correction lands, and none did.

---

## Changes made

| File | Change | Status |
|---|---|---|
| `server/tools/test_run133_a1_a3_band_contract.py` | **New.** 53-check executable band contract for all six in-scope metrics, plus the PRJ-002 P1 readout. Read-only over the modules. | Added |
| `REPORT_2026-09-04_run133_a1_a3_alignment_audit.md` | **New.** This report. | Added |

**No other file was modified.** No code, no specification, no fixture, no version stamp, no
migration. In particular the specifications were **not** rewritten to match the code, even though
the evidence says the code is right — because rewriting them destroys the only surviving record of
the divergence before the owner has seen it, and because the correct scope of that rewrite spans
six further modules outside this run.

---

## v68 corpus / study-use implication

**The v68 corpus is NOT blocked by this run, and reassembly may proceed on the band contract.**

The order's decision rule freezes the release on *any* alignment change affecting an input, a
band, a posture, a category contribution or a displayed finding. **No such change was made.** The
band contract executing at `e853cb2` is unchanged, and it is now pinned by 53 executable checks.
Every band in scope is traceable to a dated owner order — Run 101, Run 103, Run 107, Run 114 — and
none rests on the stale specification text.

Two qualifications the owner should carry into the corpus decision:

1. **The A1.8 float defect is live in v68.** It changes a reading only for a project landing on
   CPI *exactly* 0.95. No project in the corpus is known to; PRJ-002 P1 is at 0.955263 and is
   unaffected. If the owner authorises the repair, it is a **band-contract change** and the rule
   then bites: v68 would need recomputation, and periods computed under the two contracts must not
   be mixed. **Deciding this before reassembly is materially cheaper than after.**
2. Correcting the specifications is a **documentation** change and requires no recomputation, no
   reassembly, no Decision Brief regeneration, no new fixture qualification and **no simulation
   version increment** — the instrument does not change. `SIMULATION_VERSION` correctly stays at
   `sim-2026.09-v68`.

---

## Blockers and owner decisions

**One decision is needed, and it is small.**

> **The A1.8 Yellow edge is not attainable.** `_VAC_OWNER_YELLOW_PCT` is built as
> `(1 − 1/0.95) × 100` = `-5.263157894736836`. The module builds its percentage by a different
> arithmetic path — `((BAC − BAC/CPI)/BAC) × 100` — which at CPI exactly 0.95 and BAC $1,000,000
> yields `-5.263157894736855`, a few units in the last place **below** the constant. The `>=` test
> fails and the reading is **Amber where the owner's Run 114 ruling says Yellow**. It is
> BAC-dependent, which is the signature: at BAC 1.0 the two paths coincide and the same project
> reads Yellow. The 0.90 Amber edge happens to fall the other way and is correctly inclusive.
>
> **Risk of proceeding without a decision:** low frequency, high consequence. A1.8 is one of the
> two `CORE_VOTING_MODULES`, so this moves a project's official status, not a displayed number —
> the same class of defect Run 35 found in A1.7 and repaired. **Risk of repairing it casually:**
> the repair lands in `server/app/simulation/models_evm.py`, which this run is forbidden to touch,
> and it is a band-contract change that would freeze v68 under the order's own rule.
>
> **The decision required:** may a follow-up run repair the A1.8 Yellow-edge comparison — by
> banding on the index rather than the derived percentage, or by building the constant through the
> module's own arithmetic — and does that repair carry a `SIMULATION_VERSION` increment and v68
> recomputation? **I have taken no action on it.**

**Two secondary decisions, each cheap:**

- **May the stale specifications be corrected to record the code?** The evidence says the code is
  right and the specification is a derived transcription that fell behind. The correct scope is
  **ten** modules, not four: A1.5, A1.6, A1.9, A1.11 (Run 107), A1.7, A1.8 (Run 114) and A4.5,
  A4.7, A4.8, A4.9 (Run 107). Four of those sit outside this run's scope, so I stopped rather than
  extending it silently, as the order directs.
- **Should the Run 59 ruling be amended to name `specifications/` explicitly?** It currently
  reaches the folder only through the catch-all "everything else", and this run cost real effort
  establishing that. One sentence would prevent the next audit repeating it.

**No stop condition beyond these was hit.** The specification has no conflicting versions; no
unbanded metric is required by category mathematics (the question is moot — the code bands them);
the harness runs entirely outside production; PRJ-002's raw inputs are available and internally
consistent; no source methodology, dissertation commitment, participant material or ethics
approval is implicated; and no official posture changed at corpus scale.

---

## What the briefing did not know

Stated plainly, as the owner asked.

1. **Nothing in the briefing was wrong on the facts.** Every pre-checked fact verified. Both
   cruxes were correctly identified, and the "hearsay" Run 107 lead is real.
2. **The briefing under-stated the scope of the specification staleness.** It flagged A1.5 and
   A1.11 as carrying the same prohibition. In fact **A4.5, A4.7, A4.8 and A4.9 carry it too**, and
   **no specification file mentions Run 107 or Run 114 at all**. This is not four stale lines; it
   is a systematic failure to update the derived specifications after two owner orders, spanning
   ten modules across two categories. That uniformity is itself the strongest evidence for CRUX 2:
   an omission this consistent is an omission, not ten separate deliberate decisions.
3. **The briefing did not anticipate the A1.8 float defect**, and neither did the order — though
   the order's instruction *"do not introduce floating-point boundary defects through visually
   approximate comparisons"* pointed straight at it. The defect was already there. It was found by
   executing the boundary rather than reading it, which is exactly why the order forbids treating
   a passing suite as proof.
4. **The order's own scope list would have missed six of the ten stale modules.** Working strictly
   inside it would have produced a correct but incomplete picture.

---

## Iteration log

| # | Falsifiable premise | Narrowest check | Result | Classification |
|---|---|---|---|---|
| 1 | HEAD is `e853cb2`, clean, equal to origin/main | `git status --porcelain`, `git rev-parse` | Confirmed, all three | Aligned |
| 2 | Run 59 makes the code authoritative over `specifications/` | Read `T6_HANDOFF.md:1-7` **and** `specifications/README.md` | **README disclaims its own authority and names the Python source as the record.** No conflict. | **CRUX 1 resolved: code governs** |
| 3 | A Run 107 owner order banded A1.5/1.6/1.9/1.11 | `REPORT_2026-09-02_run107.md`; `_RUN107_BASIS_ID` in code | Both confirmed; the report tabulates the postures | **CRUX 2, part 1: confirmed** |
| 4 | The Yellow constants come from an owner decision | `git log -S` on both constants | **One commit each: `fc9d60c` Run 114**, order quoted verbatim in the comment | **CRUX 2, part 2: confirmed** |
| 5 | The spec text really says "None, and none may be attached" for A1.6/A1.9 | Read lines 162 and 382 in full context | Confirmed verbatim, and also at A1.5 §125 and A1.11 §432 | Specification defect |
| 6 | The specs were updated for Runs 107/114 | `grep -rln "Run 107\|Run 114" specifications/` | **No matches anywhere.** A4.5/4.7/4.8/4.9 still say "none may be attached" | **Decisive: specification is stale** |
| 7 | A3's spec is current where A1's is not | Read `A3_cost_risk.md:54,189` | Cites Run 101 §3.1 and Run 103 §4 — current | Confirms the omission is specific |
| 8 | A3.5 bands the rate variance | Read `models_ext.py:1078-1100`, then execute the discriminator | **Bands the ABSORPTION variance.** Code forbids the rate variance in terms | **Reading error, code correct** |
| 9 | A3.2 includes 1.5 in Amber | Execute six exact boundaries | Confirmed inclusive; every boundary matches | **Aligned — changed nothing** |
| 10 | The boundary checks are exact | First run: 2 failures at 1.5 and −11.11 | **My own round-trip artefacts, not code defects.** Rebuilt on exactly representable inputs | Test defect, mine, repaired |
| 11 | Rebuilt A1.8 check on the index | Execute CPI 0.95 | **FAIL — Amber, not Yellow.** BAC-dependent | **Real implementation defect** |
| 12 | Run 35's full-precision ruling still holds for A1.7 | Execute TCPI 1.0004 (rounds to 1.0) | **Yellow** — ruling holds | Aligned |
| 13 | The new checks can fail | Introduce 3 faults, observe, restore | **46/7 under fault; 53/0 restored; tree byte-identical** | Verified |
| 14 | Nothing regressed | Run132 tool, Run34 boundary tool | 31/31 and 18/18 | Aligned |

**No check failed and was left unexplained. No assertion was unreachable** — every check in the new
file executes on every run, which was confirmed by the fault injection reaching checks throughout
the file, not merely the first. The Run 132 precedent failure mode the order warns of (a stale
assertion raising early and stranding later ones) does not arise: this file uses no module-level
setup that can raise.

---

## Verification, commit, and final state

`git status --porcelain` immediately before the commit:

```
?? REPORT_2026-09-04_run133_a1_a3_alignment_audit.md
?? server/tools/test_run133_a1_a3_band_contract.py
```

Two untracked additions and **no modification to any tracked file** — the mechanical proof that
`server/app/simulation/` was not touched and that `SIMULATION_VERSION` did not move.

`T6_HANDOFF.md` was **not** updated. It carries no authority by its own first line, this run
changed no code, and nothing in it was made stale. Its four ordering breaks were left alone.

**Confirmed: no production system, production Postgres, participant-facing store or participant
material was contacted at any point. No model call was made or simulated. No key was printed.**

**Outcome B. The instrument and the specification do not agree, the disagreement is fully
inventoried and evidenced, the code is established as the authority on the repository's own
ruling, one real implementation defect was found that neither the order nor the briefing
anticipated, and one small owner decision is required before anything else is touched.**
