# Validate the seven, restore voting: the freeze point

Branch `claude/remediation-validate-seven` from `origin/main` at `640c355`. This is Run 4 of five,
executed fourth under the revised order 1, 3, 2, 4, 5 (`remediation_decisions_answered.md` 2.2).
**After this run the platform is frozen for the study: no algorithm changes, no threshold changes,
no band changes.**

---

## 1. LEAD: the eighth HOLD module, and the ruling on it

**It is the Document Risk Score, and it is NOT one of the CORE seven. It stays non-voting.**

**How it was identified.** The audit matrix itself is not in the repository, so the eighth row was
established from the triage the programme reproduces and from the code. The triage is CORE 7,
PROXY 30, FIX 15, WIRE 14, REBUILD 26, WITHDRAW 8, EXTERNAL 1, which is 101 units. Of those
dispositions, the ones that produce a `HOLD, non-voting` row are the seven CORE, held pending
validation, and the single EXTERNAL unit, held pending an audit the platform cannot perform on
itself. Eight rows, and the arithmetic admits no other combination: WITHDRAW is disabled rather
than held, PROXY is advisory rather than held, and FIX, WIRE and REBUILD are all
remediate-then-reconsider. The EXTERNAL unit is the Document Risk Score, identified independently
in the code: it is declared in the registry, implemented by no formula function on this server,
and is the one genuinely unported declaration `unported_modules()` returns. The programme's own
deferred list names it separately for the same reason, requiring "a separate extraction-model
audit with labelled holdout documents: precision, recall, false-positive and false-negative rates,
calibration, provenance".

**The ruling, and the reasoning.** It is not CORE and it does not join the seven.

1. **It is not a measure the platform computes.** It is a value the extraction model supplies with
   the document set. The other seven take figures out of documents and perform arithmetic on them
   that can be read, banded and tested. This one arrives already scored. There is no formula in
   this codebase to validate, no band in this codebase to source, and no guard in this codebase to
   write, because the thing being judged happens in a model this platform calls rather than in
   this platform.
2. **Its validation question is a different question.** The seven need a threshold traced to a
   source. This one needs precision, recall and calibration of a text-scoring model measured on
   labelled documents. That is the very evidence the programme records as absent, and it is a
   research programme rather than a run.
3. **Its description and its implementation are already known not to match.** `VALIDATION.md`
   records the discrepancy: the methods documentation describes it as a transparent keyword and
   pattern score, and the extraction pipeline that actually produces it does something else.
   Restoring a vote to a value whose description is known to be wrong is the exact fault the whole
   remediation exists to correct.
4. **Nothing can route a vote through it in any case**, which is asserted in the suite rather than
   argued: it is absent from the implemented-module table, so no vote can be cast by it even if
   the voting set named it.

Verified in `server/tools/test_run4_validate_seven.py` section 1: it is declared in the registry,
absent from the implemented table, reported as the one unported declaration, and absent from the
voting set.

---

## 2. The seven, one row each

**A module votes only when all three hold: its band is sourced, its guard exists, and its boundary
tests pass.** Two clear all three. Five have guards and passing boundary tests and no source for
their boundaries, so they stay non-voting. That is the run's result, not a failure of it, and no
citation was stretched to make a number defensible.

| Measure | Band | Citation | Guard | Boundary tests | Votes |
|---|---|---|---|---|---|
| **TCPI** | Green at or below **1.00**, Amber at or below **1.10**, Red above | 1.00 definitional, PMI PMBOK Guide 6th ed. 2017 section 7.4.2.2 and PMI Practice Standard for EVM 2nd ed. 2011. 1.10 applies Christensen and Heise 1993 (0.10 cumulative index stability) by a stated inference | New. Remaining budget zero or below abstains, where it manufactured a Red | Exhausted 0.500 to 1.599 in thousandths; both edges hit exactly, above and below | **YES** |
| **Variance at Completion** | Green at or above **0 per cent**, Amber at or above **minus 11.11 per cent**, Red below | 0 definitional, PMI as above. Minus 11.11 per cent is exactly an index of 0.90, applying Christensen and Heise 1993 by a stated inference | Extended. A zero index already abstained; a negative index now does too | Exhausted over indices 0.500 to 1.499 in thousandths; both edges hit exactly | **YES** |
| Look-Ahead Schedule Health | 10 / 25 / 40 per cent constrained, unchanged | **None found.** The lean construction plan-reliability benchmarks (Ballard 2000) measure a different quantity | New. Zero planned activities abstains, where it substituted a rate of zero and read Green; a constrained count outside the planned count abstains | Every edge, above and below | no |
| Contingency Burn Rate | 1.0 / 1.3 / 1.6 burn stress, unchanged | **None found.** No source states a burn-against-progress threshold, and the proportional-drawdown premise the first boundary rests on is not what the contingency literature describes | New. Zero reported progress abstains, where it substituted the raw burn share; a remaining contingency outside zero to the original abstains | Every edge, above and below | no |
| Material Cost Variance | 5 / 12 / 20 per cent, unchanged | **None found.** AACE estimate accuracy ranges describe estimate accuracy at preparation, not a mid-execution control limit | New. Absent reported progress abstains, where it compared cost to date against the WHOLE baseline, that is, assumed the project finished; zero expected cost abstains | Every edge, above and below, both signs | no |
| RFI Velocity | 2 / 4 / 8 a week and 10 / 20 / 35 per cent overdue, unchanged | **None found.** Published studies report counts per project and response times, not per-week rate thresholds | New. An absent log period abstains, where it substituted thirty days and then stated "over 30 days" as though the document had said so; zero or negative period abstains; an overdue count above the total abstains | Every edge on both ladders | no |
| Submittal Rejection Rate | 5 / 15 / 25 per cent, unchanged | **None found.** No recommended practice or study located states a rejection-share threshold | New. A rejected count above the total abstains, where it produced a share above one. The empty-register guard already existed and is shown to have survived | Every edge, above and below | no |

**On the two inferences, stated plainly because a committee will press on them.** The 1.00 and
0 per cent boundaries are definitional: the sources define the measures around exactly those
points. The 1.10 and minus 11.11 per cent boundaries are not stated by any source as bands. What
is stated by a source is the number 0.10: Christensen and Heise found the cumulative cost
performance index does not move by more than that after the twenty per cent completion point.
The inference drawn here is that a demand for more improvement than the index is observed to make
is a demand the remaining work is not supported in meeting. That inference is written beside the
band in the code, in the methods documentation, in the export and here, so that a reader weighs it
rather than discovers it. **The known limit of the second citation is also recorded beside it:**
the stability finding is conditional on the project being past twenty per cent complete, and
neither measure reads percent complete, so the condition is not enforced.

**The five held back are the honest outcome, not an incomplete one.** Each was examined against
the literature that plausibly covers it, and in each case the published numbers measure a
different quantity from the one the module computes. Borrowing them would have been the same fault
as the canonical names claiming methods the arithmetic does not implement, which is the finding
the audit called most damaging.

---

## 3. The freeze record

| Item | Value |
|---|---|
| Commit at the freeze | `4292bafb6df6ecc99c130de17726433258bfee5b` on `claude/remediation-validate-seven`, merged to `main` as the commit that follows it |
| Branch cut from | `origin/main` at `640c355` |
| Analytical layer version | `sim-2026.08-v2` (was `sim-2026.07-v1` through all four remediation runs; moved once, here) |
| Voting modules | A1.7 TCPI, A1.8 Variance at Completion |
| Held non-voting, sourced band absent | A2.8, A3.2, A3.4, A4.2, A4.3 |
| Disabled, concept-only | A3.8, B2.7, B2.9, B2.20, B4.1, B4.2, B4.5, B4.6 |
| Relabeled proxies | 30, unchanged from Run 1 |
| Newly wired, unvalidated | 14, unchanged from Run 3 |
| Registry declarations | 101 live rows, 1 unported (the document risk score) |
| Migration head in the repository | `0025_project_notices` |
| Unapplied in production | 0020, 0021, 0022, 0023, 0024, 0025. **This run adds none.** |

**Band values with citations**, held in code at `server/app/simulation/registry.py` `BAND_SOURCES`,
mirrored in `server/app/research_export.py`, and carried on every stored result of a voting module
as `band_source`, alongside `band_source_limit`:

- **TCPI.** Green at or below 1.00, Amber at or below 1.10, Red above. Project Management
  Institute, *A Guide to the Project Management Body of Knowledge*, 6th edition, 2017, section
  7.4.2.2; PMI, *Practice Standard for Earned Value Management*, 2nd edition, 2011; Christensen,
  D. S. and Heise, S. R., "Cost Performance Index Stability", *National Contract Management
  Journal*, 25(1), 1993, pages 7 to 15.
- **Variance at Completion.** Green at or above 0 per cent, Amber at or above minus 11.11 per cent,
  Red below. Same three sources; minus 11.11 per cent is the exact restatement of an index of 0.90.

**Dependency versions.** Python 3.12 on Render, 3.11.15 in this container. Pinned server packages:
`fastapi==0.115.6`, `uvicorn[standard]==0.34.0`, `sqlalchemy==2.0.36`, `psycopg[binary]==3.2.13`,
`alembic==1.14.0`, `google-auth==2.37.0`, `google-api-python-client==2.155.0`,
`google-auth-httplib2==0.2.0`, `openpyxl==3.1.5`. Vendored JavaScript, with the sha256 prefix of
the file as it stands at the freeze: globe.gl 1.15.0 (`46c6a2a9d1faa609`), PDF.js 3.11.174
(`5b5799e6f8c68066`), SheetJS 0.18.5 (`c9506197caf809a0`), plus the vendored fonts and the
Natural Earth country geometry (`feabdf309770ed24`). No build step, no package manager on the
frontend.

---

## 4. What was done

**Bands.** Two ladders re-banded onto sourced boundaries, with the citation and the inference
written beside the band in the module's own file. Five ladders left exactly as they were, each
with a comment recording what was looked for, what was found, and why what was found does not
cover the number. **No formula was changed**, asserted directly: the number each measure produces
is byte-identical to the number the shipped code produced on the same input, and only the band it
falls in moved.

**Guards.** Eleven new abstention guards across all seven, plus two pre-existing ones shown to
have survived the re-banding rather than being quietly relaxed. Every guard is proved by injecting
the absent or zero input and confirming the full abstention contract: no band, `insufficient_data`
set, a reason in words carrying no module id, no key name and no em dash, and no exception raised.
Each is then run against the ACTUAL shipped code extracted from the pinned baseline commit, so
each reads "the code that shipped substituted a value and produced a band; this branch abstains".

**The case the run names.** TCPI divides by (BAC minus AC), which is zero at completion. The
shipped code returned Red with no ratio: a status manufactured from a division it could not
perform, indistinguishable downstream from a measured Red. It now abstains and says why.

**Voting restored, to two.** `CORE_VOTING_MODULES` is `{A1.7, A1.8}`. The five held back carry
their reason in `HELD_NON_VOTING_UNSOURCED_BANDS`, on the stored result as
`held_non_voting_reason`, in the export's new `band_source` column, and in the methods
documentation. They compute, and their findings render on the ledger exactly as before.

**The version stamp moved.** `SIMULATION_VERSION` had not changed across three remediation runs
that fixed fifteen defects, wired fourteen computations and rebanded two measures. It is now
`sim-2026.08-v2`, so results collected before and after the freeze are distinguishable in the data
rather than only in a report.

---

## 5. What was NOT done, and why

- **No formula was touched**, which the run forbade. No stop condition fired: nothing among the
  seven needed a formula change to be banded or guarded.
- **Five of the seven do not vote.** Not for want of effort but for want of a source. Stated in
  full in section 2.
- **The auditor's gate is not met and this run does not claim it is.** See section 7.
- **The 4-band ladder was not preserved for the two voting measures.** Three bands, because two
  boundaries are sourced and a fourth level would need a third boundary that does not exist.
  Yellow is simply not emitted by those two now.
- **The browser instrument was not brought into line.** `sim.js` and `simulations.js` still carry
  the pre-remediation arithmetic and the old ladders, and `research/deepdive.html` loads both.
  That divergence was raised by the previous run and remains an owner decision.
- **Nothing outside the seven and the eighth was reconsidered.**
- **No migration.**

---

## 6. Guarantees, each marked

- **Every band edge tested above and below.** VERIFIED. Both voting ladders are additionally
  exhausted across their whole range in thousandths, so the bands are contiguous with no gap or
  overlap anywhere, not merely correct at the points chosen.
- **Each abstention guard proved by injecting the absent or zero input.** VERIFIED, fifteen
  injections, each asserting no crash, no band, and a speakable reason, and each compared against
  the shipped code's behaviour on the identical input.
- **A module whose band lacks a source is non-voting, verified rather than asserted.** VERIFIED on
  the stored row from a real four-period upload: `votes` is false, `band_source` is null and
  `held_non_voting_reason` is present for all five.
- **The voting modules and no others vote, across all three exclusion layers.** VERIFIED. Layer
  one: the category rollup opens only for the categories carrying a voting module, asserted as set
  equality on the stored row. Layer two: the module that scores the courses of action carries
  `votes:false`, which is the field the recommendation builder gates on. Layer three: the decision
  card reads the fused project status, which layer one restricts.
- **Project status computed from the voting set is stable across recomputation and byte-identical
  for an unchanged project.** VERIFIED: three recomputations of the same stored inputs are
  byte-identical including every module result and every category rollup, and equal to what the
  row already holds. Proved able to fail by moving a voting module's own input.
- **The rollup baseline established fresh, not remembered.** VERIFIED, section 7 below.
- **Both themes driven in a real browser.** VERIFIED, Fairbanks and NYC, backgrounds genuinely
  different off computed style, transitions suppressed, no uncaught page error on any of three
  projects in either theme.
- **Nothing qualifier-like renders on the participant surface.** VERIFIED by scanning the rendered
  Signal Ledger and the Governance Decision card in both themes for twelve strings, including
  "validated", "Christensen", "PMBOK", "citation" and "concept-only".
- **Nothing describes these modules as validated without qualification.** VERIFIED in code by a
  scan of the participant scripts and the registry that ignores comments and reads only what a
  file can put in front of a reader.
- **Every check proved able to fail, restored, baseline rechecked.** VERIFIED.

---

## 7. The rollup baseline, measured against the current one

The previous run moved it, so it was established here rather than remembered. The "before" is the
same `compute_project` over the same stored inputs with the pinned baseline's own seven formula
functions swapped into the registry table and the baseline's seven-module voting set restored.
Both had to be rebound: the registry captures formula functions by value at import, and without
the second rebinding the comparison would have been of this branch with itself. The swap is proved
to have taken before anything is read from it, and the "after" is checked to equal what the real
path actually stored.

On a four-period project with cost performance deteriorating from 0.98 to 0.87:

| Period | Status before | after | Conflict before | after |
|---|---|---|---|---|
| 1 | Amber | Amber | 0.812951 | 0.0 |
| 2 | Amber | Amber | 0.812951 | 0.0 |
| 3 | Red | **Amber** | 0.665104 | 0.0 |
| 4 | Red | Red | 0.721441 | 0.0 |

**Read it plainly.** Project status moved in one of four periods. Project conflict is now zero in
every period, and that is not a fix: it is the arithmetic of a single voting category. Both voting
measures sit in the cost and earned value category, so exactly one category rolls up and the
project-level fusion combines one status with nothing. **A conflict figure of zero at project level
now means "one source", not "sources agree", and anything reading it as agreement will be wrong.**
That is the single most consequential consequence of this run and it is stated here rather than
left to be discovered.

**A second consequence, of the same kind.** Schedule, contingency and document-derived condition
no longer contribute to project status at all. Project status is now a cost statement. The
measures for the other three still compute and still show their findings on the ledger, which is
the visibility the owner's decision preserves, but they do not move the status a participant is
shown. A methods chapter has to say this in as many words.

---

## 8. The auditor gate, in terms a methods chapter can quote

> The band boundaries used by the two measures that contribute to project status are traced to
> published sources: the Project Management Institute's definitions of the two earned value
> measures, and a peer-reviewed finding on the stability of the cumulative cost performance index.
> Where a boundary is not stated by a source but is inferred from one, the inference is recorded
> beside the boundary rather than presented as the source's own statement.
>
> This establishes the provenance of the thresholds. It does not establish their accuracy. The
> platform's own external arithmetic audit sets a production re-entry gate requiring, among other
> conditions, that false-positive and false-negative performance be measured on labelled holdout
> cases. No labelled corpus exists for this platform and no expert reference standard has been
> established, so no such measurement has been made and none is claimed. How often a project the
> instrument places on one side of a boundary differs in outcome from one placed on the other is
> unknown.
>
> The remaining five measures examined carry boundaries for which no source specifying those
> numbers was found. They compute, their findings are shown, and they are excluded from project
> status, from the generated recommendation and from the decision record. Nothing in the platform,
> its export, its interface or its documentation describes any measure as validated.

The same limit is carried in the code (`BAND_SOURCE_LIMIT`), on every voting module's stored
result (`band_source_limit`), in the committee-facing export's new `band_source` column on every
row, and in the methods documentation.

---

## 9. Verification performed

Server suite, fresh SQLite per file, `PYTHONIOENCODING=utf-8`, interpreter confirmed real.
Baseline on `origin/main` first: **3394/3394 across 59 files**. After: **3628/3628 across 60
files**, new `test_run4_validate_seven.py` 228/228. Browser drive
`drive_run4_validate_seven.py` **84/84**, three projects on one server in two themes.
`tests.html` **51/51**. `tests_render.html` **286/287**, the one red being the pre-existing
auth-gated production-read row that requires a signed-in session in the same tab.

**Three existing suites went red and each is recorded as what it was.**

1. `test_run1_disable_and_relabel.py` asserted a voting set of seven and injected a fault through
   RFI Velocity to prove its most important check could fail. **It protects a real property** (the
   voting set is exactly what is intended, and status moves only with a voting module's own
   input). Re-pointed: the set is asserted by exact ids rather than by count, and the injection
   now moves the cost index, because moving request velocity correctly moves nothing any more and
   would have made the injection prove nothing. Its regression case was widened to move all five
   newly held-back measures' inputs at once.
2. `test_run2_fifteen_defects.py` asserted the same seven-module set, and separately asserted every
   participant script byte-identical to its baseline. **Both protect real properties.** The first
   is re-pointed. For the second, the two files this run legitimately changed are named
   individually and the permitted difference in each is asserted exactly, rather than the check
   being loosened to let any change through.
3. `test_run3_adapter.py` proved its exclusion check non-vacuous by letting three of the fourteen
   vote and asserting the status moved. **It protects a real property and its sample space had
   become insufficient**, which is precisely the failure the previous run warned about. Exhausting
   the space shows something worth reporting: **adding any one non-voting module to the voting set
   moves project status for none of the forty-eight computed modules**, because the fused Red on
   that fixture is not near a boundary. Replacing the voting set with a single module moves it for
   28 of 50. The check now replaces rather than extends, and exhausts.

---

## 10. Incidental findings

1. **THE LARGEST ONE, and it made three runs' work invisible: abstention reasons have never
   rendered on the Signal Ledger.** The ledger has had code to print a module's own reason under a
   silent row since the reasons were written. It reads `row.abstained`; the row the page actually
   reads is the list projection; the projection does not carry `abstained`; and the detail page
   grafts `module_results`, `signal_inputs` and `recommendation_basis` onto it but not that. Every
   abstaining module has shown a bare "No data" pill and nothing else. Two previous runs wrote
   careful sentences saying what each silent module was waiting for, asserted them on the stored
   row, and recorded that the ledger renders them. It did not. **Fixed here** with the same graft
   as the other three fields, and confirmed in a real browser: the required-efficiency row on a
   project at completion now reads its reason in words. This is the fourth instance of the same
   defect shape in one file.
2. **A rate is banded after it is rounded.** RFI Velocity rounds requests per week to one decimal
   before banding, so a rate of 2.01 a week is banded as 2.0 and reads Green. The effective step
   either side of the boundary is a tenth, not a hundredth. Recorded in the boundary tests
   explicitly rather than worked around.
3. **The defensibility handbook is live and it makes calibration and validation claims across the
   whole taxonomy that the audit contradicts.** `assets/js/ds_defensibility_data.js` is loaded by
   `index.html`. Its entries for the two voting measures stated the old ladders, called them
   "calibrated control limits" and said they were "validated by the tests.html band harness". Both
   entries are corrected here, boundaries and claims. **The other ninety-odd entries carry the same
   boilerplate and were not touched**: the file is written around the retired framing and needs its
   own pass. This is now the largest remaining source of overclaim on a live surface.
4. **The substitution pattern the guards close is not confined to the seven.** The neighbouring
   Inflation Adjustment Index divides by an expected material cost and substitutes zero when it is
   not positive, exactly as Material Cost Variance did. It is a relabeled proxy and non-voting, so
   it is out of this run's scope, but the class is wider than the seven.
5. **Project-level conflict is now structurally zero** on any project whose voting measures share a
   category. See section 7. Nothing currently reads it as agreement, and something might.
6. The `_derived` source flag still never fires on the server, so the "assumed" notes that would
   have marked a substituted input were unreachable, which is why the RFI period substitution was
   silent on the real path rather than flagged.

---

## 11. Which surfaces changed, and how

**No new control anywhere.** Placement of everything that existed is unchanged.

1. **Signal Ledger.** Two rows band differently for the same figures: the required-efficiency row
   and the variance-at-completion row. Seven rows can now show no finding where they previously
   showed one, in each case because the figure they needed was absent or outside its domain.
   **New on this surface: a silent row now prints its own reason underneath the "No data" pill**,
   in the same place the ledger already had markup for, for every abstaining module and not only
   the seven. The category status pills for schedule, cost risk and document-derived condition
   change value, because those categories no longer roll up.
2. **Governance Decision card.** Inherits the status change through the fused status. No change to
   the card itself, except that its courses-of-action explanation no longer uses the word
   "validated": it now says the scoring analysis is not one of the measures that contribute to
   project status. The substance a participant reads is the same.
3. **Methods tab.** The two voting entries have new bands, new abstention conditions and rewritten
   grounding paragraphs carrying the citations and the stated inference. The five held-back entries
   have new abstention conditions and a new "Band boundaries" line saying the boundaries are
   uncalibrated and uncited and the measure does not contribute to project status. One entry's
   sources line no longer claims a thirty-day fallback that no longer exists.
4. **Defensibility handbook.** Two entries corrected, per incidental finding 3.
5. **Export workbook.** One new column, `band_source`, filled on every row: the citation and its
   limit for a voting computation, the reason for a held one, and a plain statement of
   uncalibrated and uncited for everything else.
6. **API.** Additive `band_source`, `band_source_limit`, `held_non_voting_reason`. `votes` changes
   value for five modules. No existing key changed shape or meaning.
7. **Participant-visible qualifiers: still none.** Confirmed in a real browser in both themes.

---

## 12. What the next session needs

1. **Run 5 regenerates the Group A export.** It should assert 51 computed plus 1 supplied, revise
   the standing footnote and the Group A total, replace the byte-identical duplicate report files
   with one report plus a checksum manifest, and export all 52 with activation state on each. The
   export gained a column here, so the expected header list has moved.
2. **THE FREEZE IS IN FORCE FROM THIS COMMIT.** No algorithm, threshold or band changes. Run 5 is
   a packaging run and must not become a band conversation.
3. **The two consequences in section 7 belong in the methods chapter**, not only in this report:
   project status is a cost statement, and project-level conflict of zero means one source.
4. **The defensibility handbook is the largest remaining overclaim surface** and it is live.
5. **0020 through 0025 remain unapplied in production.** This run adds no migration.
6. If the owner wants schedule or document-derived evidence to contribute to project status again,
   the route is a sourced threshold or an expert elicitation, and elicitation would make the
   instrument partly a product of the panel that also scores it, which is why it was declined.

**Files changed.** `server/app/simulation/models_evm.py`, `models_ext.py`, `models_doc.py`,
`models.py`, `registry.py`; `server/app/research_export.py`; `assets/js/knowledge.js`,
`assets/js/recommendation_options.js`, `assets/js/detail.js`,
`assets/js/ds_defensibility_data.js`; `server/tools/test_run4_validate_seven.py` (new),
`server/tools/drive_run4_validate_seven.py` (new), `server/tools/test_run1_disable_and_relabel.py`,
`server/tools/test_run2_fifteen_defects.py`, `server/tools/test_run3_adapter.py`;
`remediation_programme.md`; this report; `T6_HANDOFF.md`. No file outside the repository was
touched. Production was never inspected or queried; throwaway SQLite only.
