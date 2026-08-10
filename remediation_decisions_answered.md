# Opus Gubernatio remediation — decisions, answered

Companion to `remediation_programme.md`. Answers the twenty decisions raised in
`REMEDIATION_DECISIONS_ALL_RUNS.md` and `RUN1_DECISIONS_REQUIRED.md`.

**Owner answers are marked OWNER. Everything else is Claude's recommendation and is open to
correction, but no prompt is blocked on it.**

---

## Cross-run

**X1. Freeze point — OWNER: freeze after Run 4.** The full programme, seven validated. Freeze on the
run, not the calendar. Runs 1 to 4 are weeks, and a participant seeing status computed from
arithmetic the audit blocked release over is not defensible.

**X2. Deploy cadence — OWNER: each run merges and deploys as it completes.** Auto-merge, per standing
permissions. Staging until the freeze means nothing is exercised until everything lands, which is how
defects went unseen for weeks.

**X3. Does the participant see the remediation — OWNER: no.** It is background computation. The
advisory-versus-voting distinction lives in the export and the methods documentation, not on the
participant surface.

**Consequence, settled:** the interim status under 1.1 carries **no visible caveat on the participant
surface**. The caveat-wording question falls away.

**Still open and OWNER's:** whether the operational surface differs from the participant one, since
operational users are not part of the study.

---

## Run 1 — disable and relabel

**1.1 Voting scope — Option C.** The seven CORE modules vote on an interim basis; the other 94 do
not. Option A leaves no instrument during Runs 2 to 4. Option B is indefensible if a reviewer reads
the matrix beside the code. C is what the programme's closing argument implies.

**1.2 What non-voting excludes — all three layers.** Category rollup and project status fusion, the
generated recommendation text and courses of action, and the decision card. A module that cannot vote
on status cannot appear in the recommendation either, or the exclusion is cosmetic. **Ledger
visibility stays**: the row still shows its finding, marked advisory.

**1.3 Display of the 8 disabled — reuse the existing not-relevant state.** It exists, it is already
distinct from no-data, and the ledger renders both. Code IDs: A3.8, B2.7, B2.9, B2.20, B4.1, B4.2,
B4.5, B4.6.

**1.4 Label form — canonical name plus a proxy qualifier, on every surface.** "Pythagorean Fuzzy Sets
(proxy: hard-coded transformations of raw CPI, SPI and document risk. Advisory, non-voting.)" No
split by surface: two names for one row is how this codebase acquired three taxonomies. The
auditor's objection is to an unqualified claim, and a qualifier answers it while keeping the row
traceable to the literature review.

**1.5 Weather Day Impact in both runs — enumerate the full overlap first.** It is unlikely to be the
only row Run 2 will change after Run 1 labels it.

---

## Run 2 — the 15 defects

**2.1 Fix or withdraw — case by case, and the prompt must report which category each landed in.**
Several become permanent abstentions because the remedy requires data the corpus does not carry:
Monte Carlo EAC without `DEMO_BAC`, Float Consumption without network-derived float, Cost Risk P80
without a real CRA, Weather Day Impact without verified lost days, Environmental Compliance without
audited permit data, NCR Rate without a defined cohort denominator.

**2.2 Ordering — move Run 3 before Run 2.** Defects 1 and 2 are Conservative Dominance and
Dempster-Shafer, both among the 14 modules Run 3 makes reachable, and the matrix's own remedy for
Conservative Dominance begins "build the qualified-signal adapter". **Revised order: 1, 3, 2, 4, 5.**

**2.3 Corpus dependency — Run 2 proceeds; NCR Rate and Environmental Compliance Rate abstain until
the corpus lands.** Quality Audit and Environmental Compliance documents exist for Project 1 only.

**2.4 Dempster-Shafer scope — fix both, and treat the rollup change as requiring its own regression
evidence.** `dst_combine` is shared between the module and the category-to-project rollup, so fixing
Θ handling changes project status for every project. That is correct and must be evidenced, not
avoided.

---

## Run 3 — the adapter

**3.1 What the adapter feeds — build on raw signals now, and record the Category 9 gap explicitly as
a known deviation.** A minimal Category 9 pass first is the better engineering and it is scope that
is not available. The deviation is stated, not hidden.

**3.2 Reachable and voting — reachable, shown, and explicitly marked as newly wired and
unvalidated.** Under 1.1 they are non-voting anyway.

---

## Run 4 — validate the seven

**4.1 What validated means — literature-sourced bands, with the gap stated in the methods chapter.
OWNER decision, recommendation given.** Thresholds cited to PMI, AACE or peer-reviewed sources, with
boundary tests and abstention guards. It does not meet the auditor's gate, which requires
false-positive and false-negative performance on labelled holdout cases that do not exist.
Expert-elicited bands would make the instrument partly a product of the panel that also scores it.

**4.2 The eighth HOLD module — identify and rule on it before Run 4 is prompted.** The matrix carries
eight `HOLD — non-voting` rows; the programme names seven CORE.

**4.3 Does Run 4 restore voting — yes, restoring the seven to voting is Run 4's acceptance
criterion**, not a side effect.

---

## Run 5 — regenerate the Group A export

**5.1 The expected ID set — assert 51 computed plus 1 supplied, and revise the standing footnote and
the Group A total.** The matrix is right that a value the extraction model supplies is not a
registry-computed arithmetic module. The current footnote counts A4.1 inside the 100 and therefore
inside Group A's 52, and that is the text to change.

**5.2 Disabled modules in the export — export all 52 with activation state recorded on each.** The
export is audit evidence; omitting the disabled hides what was disabled.

**5.3 The duplicate report files — Run 5 does it.** Both downloads share SHA-256 `f1c9e769...`. One
authoritative report plus a checksum manifest.

---

## Standing exceptions the prompts carry

- **Runs 1 to 4 require editing `server/app/simulation/`.** Each prompt carries an exception scoped
  to that run only. Run 1: label strings, the activation-state field, and the fusion-exclusion list,
  with no arithmetic touched. Runs 2 to 4: the named modules only.
- **Every prompt requires the report to state where each user-facing change landed**, per the 8/7
  incident.
- **Every check proven able to fail by injection, then restored and the baseline rechecked.**
- **Sequential only.** One session at a time against the shared working directory.
- **Auto-merge**, per X2.

## Revised run order

1. **Run 1** — disable the 8, relabel the 30. Sonnet.
2. **Run 3** — the flat-to-nested adapter. Opus. *Moved ahead of Run 2 per 2.2.*
3. **Run 2** — the 15 defects. Opus.
4. **Run 4** — validate the seven, restore voting. Opus.
5. **Run 5** — regenerate the Group A export. Sonnet.

**Freeze after Run 4.**
