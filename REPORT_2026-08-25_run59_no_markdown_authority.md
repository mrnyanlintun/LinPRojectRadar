# Run 59 — no markdown document carries authority

**Repository:** the Linux clone at `/home/user/LinPRojectRadar`.
**Interpreter:** `python3`, CPython **3.11.15** — the documented fallback. There is no `.venv` in
this checkout, so `run_all_suites.sh` took its own fallback branch, and every suite was run with
`PYTHONIOENCODING=utf-8`.
**No browser session was opened**, so there is no browser cwd to report.

---

## 1. The tree at the start, and every premise in the order I found false

### 1.1 The start

```
git status --porcelain                       EMPTY
git rev-parse main origin/main               f4c1dbfddde280f2856c539f2ed7120be189e316 (both)
git branch --show-current (on entry)         run58-document-conflict-audit  (3ba789a)
```

The working tree was checked out on Run 58's branch. This run branched
`run59-no-markdown-authority` **from `f4c1dbf`**, so Run 58's commit arrived at phase C, where the
order puts it, and not early.

Re-derived by execution rather than carried over:

| fact | derived how | value |
|---|---|---|
| stamp | `server/app/simulation/models.py:718` | `sim-2026.08-v38` |
| package | `participant_packages.CURRENT` | `og-participant-2026.08-v23` |
| registry / in service / retired | `registry_index()`, `service_index()` | **101 / 63 / 38** |
| registry by group | `Counter(k[0] for k in registry_index())` | `{'A':53,'B':36,'C':7,'D':5}` |
| in service by group | same over `service_index()` | `{'A':44,'B':12,'C':7}` |
| voting | `registry.CORE_VOTING_MODULES` | `frozenset({'A1.7','A1.8'})` — **2** |
| unported | `unported_modules()` | `['A4.1']` |
| suite at `f4c1dbf` | full pass | **203 suites, 15307/15307, ALL SUITES GREEN** |
| behaviour digest | gate row B15 | `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` |
| authority manifest | `pt.manifest_sha256(None, AUTHORITY_ROOTS)` | `b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a8170704dc1596` |

Every one of the order's starting-point claims is **CORRECT**.

### 1.2 FALSE PREMISE 1 — the superseded rule survives in EIGHT documents, not five

§6.2 and Run 58 name five: `NAMING_AUTHORITY.md:144`, `GROUP_ASSIGNMENT.md:17-18`,
`remediation_programme.md:279`, `training_pmp_upgrade_roadmap.md:140`, `WORKER_BRIEF.md:120`.

**How I established the truth.** Two uncapped sweeps, the second deliberately widened after the
first missed sites the phrasing did not match:

```
grep -rniE '(never|no|not|avoid|do not|must not|bars?|forbid|prohibit)[^.!?]{0,80}
            module (id|ids|identifier|identifiers|number|numbers)[^.!?]{0,80}
          | module (id|ids|identifier|identifiers|number|numbers)[^.!?]{0,60}
            (never|not|must not|do not|never appear|never used)'
      --include=*.md .
```

Three further documents carry the rule, all missed by Run 58's five-site inventory:

- **`COPY_GLOSSARY.md:89`** — "**Module ids never appear in user-facing text.**"
- **`README.md:85`** — "No module ids or numbers in user-facing text, and no em dashes."
- **`BACKEND_CHANGES_NEEDED.md:322`** — "Never mention module numbers (no "Module 09", "M10",
  "DST", etc)." **This one was missed by my own first sweep as well**, because it says "module
  numbers" without "user-facing", and it is reported here as a caught near-miss rather than as a
  clean find. A truncated or narrow grep reads exactly like a complete one.

All eight are corrected. §2 gives every before and after.

### 1.3 FALSE PREMISE 2 — `test_group_assignment.py`'s `A:52` against registry `A:53` is not a discrepancy

The order asks me to "establish what that difference is before acting". Established by execution:

```
len(set(VALIDATED) | set(PORTFOLIO_VALIDATED))          = 100
Counter(k[0] for k in registry_index())                 = {'A': 53, ...}
unported_modules()                                      = ['A4.1']
```

They are **two different populations**. `registry_index()` counts 101 REGISTERED computations,
including `A4.1` Document Risk Score, which is **supplied and not computed** and is therefore
absent from `VALIDATED`. `EXPECTED_COUNTS` counts the 100 the server both registers and computes.
`NAMING_AUTHORITY.md:84-86` already states this. Nothing was wrong and nothing needed correcting;
the suite holds `A4.1` out explicitly and asserts its exclusion three separate ways.

### 1.4 FALSE PREMISE 3 — the CANDIDATE fixed point is not HEAD

Not a premise of the order but of the mint machinery, and it cost a pass. `build_run59_candidate_identity.py`
defaults its `--candidate` to `HEAD`. The fixed point `build_run37_acceptance.py` computes is
**the oldest commit in the unbroken run back from HEAD whose tree agrees with the working tree on
all 263 member paths**. When the last commit moves no identity member — as `bcd4221` did not, it
moved only two documents — HEAD and the fixed point diverge and the mint refuses. Resolved by
re-taking the identity with `--candidate f679b976`, the commit the identity actually describes.

### 1.5 PREMISES VERIFIED TRUE, stated so the nil returns are on the record

- `NAMING_AUTHORITY.md:107` does name the dash and ampersand rules as **NOT superseded and
  STANDING**, and `:144` is the surviving identifier prohibition inside `## 6. Standing rules`.
  §6.1.2's premise is TRUE.
- The PCEIF specification is read by **13 Python files** — verified by
  `grep -rln 'PCEIF_100_MODULE' --include=*.py`, which returns exactly 13. A narrower grep on the
  full filename returns 11; the count of 13 is correct and the narrower grep was the one that
  would have been wrong.
- `production_tree.py:103-106` does designate the specification CONTROLLING; `WORKER_BRIEF.md:4-8`
  does order it read in full first.
- `MODULE_RETIREMENT_DECISIONS.md:17` and `:83` do say *registered* fell 101 to 63, and `:584`
  does say it correctly.
- The eight guards of §7 are all present and all do what the table says.
- The suite rewrites **26** committed artifacts, not the 18 the handoff records. Measured twice.
- `test_suite_identity` holds **203** files and no markdown at all.

---

## 2. PHASE A — every document corrected, before and after

Committed as `e1e335b`. The uncapped sweep's full result is at §1.2.

| document | before | after |
|---|---|---|
| `NAMING_AUTHORITY.md:144` | `- No module ids or numbers in user-facing text.` | **line removed.** The dash and ampersand rules at `:107` are untouched. |
| `GROUP_ASSIGNMENT.md:17-18` | "Refer to groups by group and purpose, **never by module id or number**. … do not belong in anything a user reads." | "Groups and purposes are the better default; **displayed identifiers are acceptable**. The owner ruled the former prohibition SUPERSEDED on 2026-08-23 … an identifier is no longer a defect." |
| `remediation_programme.md:279` | "No module ids or numbers in user-facing text. Groups by name and purpose." | "Groups by name and purpose where the identifier adds nothing. Displayed module ids and numbers are acceptable: the former prohibition was SUPERSEDED … on 2026-08-23." |
| `training_pmp_upgrade_roadmap.md:140` | "No module ids or numbers in user-facing text." | "Groups and purposes are the better default. Displayed module ids and numbers are acceptable; the former prohibition was SUPERSEDED …" |
| `WORKER_BRIEF.md:120` | "No module ids or numbers in participant-facing text." | "Groups and purposes are the better default in participant-facing text; displayed module ids and numbers are acceptable …" |
| **`COPY_GLOSSARY.md:89`** (new) | "**Module ids never appear in user-facing text.** `A1.1` is a key, not a name." | "**Module ids are acceptable in user-facing text, and a name is usually better.** `A1.1` is a key; "Monte Carlo EAC" is the name." |
| **`README.md:85`** (new) | "No module ids or numbers in user-facing text, and no em dashes." | "No em dashes in user-facing text. Displayed module ids and numbers are acceptable; the former prohibition was SUPERSEDED …" |
| **`BACKEND_CHANGES_NEEDED.md:322`** (new) | "Never mention module numbers (no "Module 09", "M10", "DST", etc)." | "Module numbers may be mentioned; prefer the name where the number adds nothing. … The retired "Module 09"/"M10"/"DST" notation stays retired, which is a separate decision about what the categories are called." |
| `MODULE_RETIREMENT_DECISIONS.md:17` | "Retirement of 38 modules, **registry** 101 -> 63" | "Retirement of 38 modules, **in service** 101 -> 63 (registry stays 101)" |
| `MODULE_RETIREMENT_DECISIONS.md:83` | "38 modules. **Registered count** falls from 101 to 63 …" | "38 modules. The **IN-SERVICE** count falls from 101 to 63 … The REGISTERED count does not fall: `registry_index()` is 101 and `service_index()` is 63, both derived by execution. Line 584 of this file states it correctly." |
| `GROUP_ASSIGNMENT.md:3` | "**100 computations, in four groups.** This file is **the authority** for how the analytical layer is described … a check in the test suite fails if the code and this file stop agreeing." | "**100 computations, in four groups: the figure at 2026-08-25, not a settled fact.** … 101 are registered, 63 are in service … **This file carries no authority.** … a check in the test suite compares the code against the registry CSV, not against this file." |
| `p0-baseline/MODULE_TAXONOMY.md:1` | "# Module taxonomy: **101 distinct computations** across four groups" | "# Module taxonomy: four groups" + "**101 registered and 63 in service at 2026-08-25: the figure at a date, not a settled fact.** … this document carries no authority." |
| `WORKER_BRIEF.md:4-8` | "## THE CONTROLLING AUTHORITY" / "READ THE SECTIONS THAT DEFINE YOUR MODULES, IN FULL, BEFORE OPENING ANY PRODUCTION FILE." | "## THE SUPERVISORY SPECIFICATION (NOT AN AUTHORITY)" / "The framework has changed. This specification is NOT an authority and does not govern: it floats until a new specification exists. It is not to be read before opening a production file, and where it and the implementation disagree, the implementation is what is true." |
| `production_tree.py:103-106` | "the **controlling** supervisory method specification … **CONTROLLING status: where this and the implementation disagree, this governs** what the method ought to be" | "… RUN 59: the framework has changed and this specification is **NO LONGER CONTROLLING**. It floats until a new specification exists. Where it and the implementation disagree, **THE IMPLEMENTATION IS WHAT IS TRUE.** It stays walked and pinned so a silent edit is still detected" |
| `T6_HANDOFF.md` | — | **ONE addition at the top**, which the file's own rule permits. It states the file is history and carries no authority, and records that the four ordering breaks are left exactly where Runs 48 to 58 left them. **Nothing below it is edited**, proved by `git diff f4c1dbf HEAD -- T6_HANDOFF.md` showing insertions only. |

**No new number was invented anywhere.** 100 and 101 are marked as figures at a date; neither is
replaced with a third figure of mine.

**MODULE_TAXONOMY.md is a production-tree manifest member**, so correcting it is a mint. Phase D
carried it, exactly as §6.5 anticipated. `test_run28_closure.py:132`'s two required strings —
"single source of truth" and "module_renumbering_map.csv" — were preserved by the edit and then
retired in phase B for a separate reason.

### 2.1 A correction of my own, reported rather than hidden

The "figure at a date" sentences I wrote into `GROUP_ASSIGNMENT.md` and `MODULE_TAXONOMY.md`
originally used an **em dash**, which §6.1.2 keeps standing. Nothing was failing —
`run51_dash_sweep.py` sweeps `assets/` only — so no check caught it. I found it reading my own
diff and replaced both with a colon (`bcd4221`), which cost a production-manifest re-take and one
mint pass. **`run51_dash_sweep.py` is byte-identical to `f4c1dbf` and was not weakened.**

---

## 3. PHASE A — the five code citations: what I did with each, and why

**The ruling asks first whether the code needs to cite a document at all. Established by
execution: it does not.** `grep -rn 'NAMING_AUTHORITY' --include=test_*.py server/tools/ server/tests/`
returns fourteen lines and **not one of them reads any of these five files**. No check anywhere
asserts any of these comment strings. Every one of the five comments states a property of the
code itself — what a particular string contains — which is true independently of any document.

**So in all five the citation is DROPPED and the reason stated directly.** All five edits are
comments; **not one executable byte moved**, which is why the behaviour digest is re-derived
unchanged.

| file | what it cited | what I did |
|---|---|---|
| `server/app/research_export.py:182` | "`NAMING_AUTHORITY.md` **rule 6**" **by number** — and rule 6 is the line §6.1 removed, so the citation would have become a dangling pointer the moment phase A ran | Citation dropped. The reason now stands alone: this sheet reaches a committee, a name and a group are what a committee can read, an internal key is not. Ends "THIS IS A PROPERTY OF THE COLUMNS BELOW, not of a document." |
| `server/app/document_evidence.py:52` | "NAMING_AUTHORITY: no module ids, no numbers, no "Cat N"" | Dropped. The reason stands alone: the string is read by someone deciding what to do about a document, and a key tells them nothing. Records that identifiers are permitted and simply not useful here. |
| `server/app/evm_consistency.py:44` | "NAMING_AUTHORITY **governs** it: no module identifier and no number-scheme label …" | Dropped. What governs is now stated directly — no em dash; state what disagrees and by how much; do not tell the project manager what to conclude. **The em-dash half of the rule is kept**, because that half stands. |
| `server/app/simulation/portfolio_health.py:97` | "**NAMING_AUTHORITY section 4** governs this sentence" | Dropped, and this is the sharpest of the five: **section 4 is where the prohibition was RECORDED AS SUPERSEDED on 2026-08-23**, so the code was citing the reversal as the source of the rule. The comment now says the sentence carries no identifier "not because either is forbidden, but because neither would tell a reader of the portfolio card anything." **The file is corrected, not deleted** — D5 withdrawn. |
| `assets/js/decision-ui.js:47-49` | the rule restated without naming a document: "the analytical layer's ids (A1.1, B4.4) **must never appear** in participant-facing text" | Dropped. The comment now records that displayed identifiers are acceptable and that the table holds NAMES because a name is what a participant can read. **This file is SEQUENCE-BEARING**, so the move carries a **named exception of record** in `V23_TO_V24_SEQUENCE_EXCEPTION`. |

### 3.1 Incidental: the five are at least twelve

The same uncapped sweep found the superseded rule restated in production comments well beyond the
five: `server/app/recommendation_basis.py:52`, `server/app/simulation/models_decision.py:234`,
`assets/js/detail.js:1698` (which cites `NAMING_AUTHORITY.md:96` — the supersession — by line),
`assets/js/charts3d.js:2542`, `assets/js/recommendation_options.js:67`,
`assets/js/projectnet2d.js:37,398,448`, `assets/js/knowledge.js:2695,2877`. **These are not
corrected**, because the order names five and §14.3 asks what I did with those five.
`server/tools/participant_packages.py:372` and `server/tools/run51_production_changes.py:68`
also carry it and **must not be corrected**: they are sealed release records, and rewriting one
is what B11 exists to catch.

---

## 4. PHASE A — the specification's thirteen readers

Committed as part of `e1e335b`. What each of the thirteen does with
`research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md`:

| reader | what it does with it |
|---|---|
| `server/tools/run19_prior_21_consistency.py:41` | **Reads its full text** and cross-checks Run 17's scientific results and the prior suite against it. |
| `server/tools/build_run26_authoritative_edges.py:14,48` | Names it "THE ARCHITECTURE MASTER" and derives category-to-category dependency edges from it. The one reader whose *output* is shaped by the document. |
| `server/tools/test_run22_production_tree_completeness.py:276-292` | **Pins its sha256** (`328b5013…`), asserts the sidecar `.metadata.json` claims the same digest, asserts `controlling_status` starts with `CONTROLLING`, and asserts the `.gitattributes` `-text` rule that stops a checkout filter rewriting its line endings. |
| `server/tools/test_run39_frozen_immutability.py:44` | Lists it among the frozen paths that must not move. Integrity only. |
| `server/tools/test_run19_category_2.py:7` | Names it as "the controlling theory" in its docstring; the executable oracle is `run17/oracle/oracles_cat_2.py`, which self-proves against the specification's worked answers **at import**. Prose reference. |
| `server/app/simulation/canonical_v5.py:38` | Prose only: cites the specification's own line numbers for the Karnik-Mendel and RIMER DOIs to justify that supervisory artifacts do not freeze. The only reader inside `server/app/`. |
| `server/tools/build_run27_remediation_matrix.py:278` | Writes its path as the `authority` column of a matrix row. Record-keeping. |
| `server/tools/build_run22_freeze.py:112-118`, `build_run24_freeze.py`, `build_run25_freeze.py`, `build_run26_freeze.py:182`, `build_run28_freeze.py:208`, `build_run30_freeze.py:250`, `build_run30_closure_freeze.py:284`, `build_run30_final_closure_freeze.py:257` | **Sealed release builders.** Each names the specification and its sidecar in the release it wrote. **Not touched** — rewriting a sealed predecessor record is what B11 catches. |

**What I did.** The CONTROLLING designation is removed from `production_tree.py`'s
`AUTHORITY_ROOTS` reason string and the read-first order from `WORKER_BRIEF.md:4-8`. **Neither
change touches any of the thirteen.** The `_why` reason strings are prose that nothing hashes:
`test_run22` walks `AUTHORITY_ROOTS` as `for _r, _rec, _why in …` and uses only `_r`.

**The specification is NOT deleted, NOT renamed and NOT removed from the authority tree.** Proved:
`pt.compare(None, None, AUTHORITY_ROOTS, PINNED_AUTHORITY)` reports `added=0 removed=0 changed=0
renamed=0`, and the manifest sha256 recomputed from the tree is
`b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a8170704dc1596`, **byte for byte the sha256 of
the pinned file and unmoved for a fifth consecutive run**.

**STOPPED under §11.3, and this is exactly the stop the order anticipated:** the sidecar
`PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.metadata.json` still carries
`controlling_status: "CONTROLLING…"`. Changing it would require changing what
`test_run22_production_tree_completeness.py` — **one of the thirteen** — does, at line 288. §11.3
says stop and report. It is left exactly as it is. See §8.

---

## 5. PHASE B — every guard: what it asserted, what it asserts now, and the injection

Committed as `eb56684`. **No check was deleted.** Every retired body is present in its file and
runs again if its flag is cleared. Injection discipline throughout: snapshot taken from a
**committed reference** (`git show e1e335b:<path>`), the injection **re-read back from disk** to
confirm it landed, restore inside a `finally`, `git status --porcelain` checked at **start and
end**, and the baseline re-taken after every injection.

### 5.1 RE-POINTED — real subject is production. Every one proved able to fail by breaking PRODUCTION.

**1. `test_group_assignment.py:42,63-68` — the sharp one.**

*Asserted:* the group→ids map parsed out of GROUP_ASSIGNMENT.md's ```` ```group-assignment ````
fence, against `VALIDATED | PORTFOLIO_VALIDATED` and against the registry CSV. **It did not fail
when the fence went missing — it called `raise SystemExit` and ABORTED THE SUITE.**

*Now:* `artifact_groups()` builds the map from **`p0-baseline/module_renumbering_map.csv`**, which
is the file the taxonomy itself names as the single source of truth for numbering and grouping.
The `SystemExit` is gone with the parse. A CSV read here against two Python registries imported
there is still two independent sources, which is the property the file's own docstring says makes
it non-vacuous.

*Injection, breaking production:* removed `"A2.3": ("CCPM_Buffer_Health", run_ccpm),` from
`VALIDATED` in `server/app/simulation/models.py`.

```
START TREE CLEAN
BASELINE : RESULT: 16/16 checks passed
INJECTED into server/app/simulation/models.py, verified by re-reading the bytes from disk
FAULTED  : RESULT: 12/16 checks passed
   RED: the artifact lists nothing the server does not register (extra: ['A2.3'])
   RED: the server registers 100 (registers 99)
   RED: unported_modules() reports exactly A4.1 (found: ['A2.3', 'A4.1'])
   RED: and the CSV minus what the server registers agrees (found: ['A2.3', 'A4.1'])
RESTORED from e1e335b
END TREE CLEAN
REBASELINE: RESULT: 16/16 checks passed
```

*§13.4, proved separately:* both fenced blocks removed from `GROUP_ASSIGNMENT.md` in a tracked
injection → `RESULT: 16/16 checks passed | exit 0`. **It no longer aborts, and it no longer even
notices.**

**2. `test_disclaimers.py` — the meta description.**

*Asserted:* `index.html`'s `<meta name="description">` equals the `**Short form, one sentence:**`
blockquote parsed out of `NAMING_AUTHORITY.md`, **verbatim**. Deleting that heading turned the
check red.

*Now:* the same sentence read from **`assets/js/knowledge.js`**, which ships it as the glossary
definition of "Opus Gubernatio", **plus a new third check** that `index.html`'s own About panel
carries the same sentence. Three production surfaces, one sentence, no markdown. The file gains a
check: 147 → 148.

*Injection, breaking production:* shortened the meta description in `index.html`.
`BASELINE 148/148 → FAULTED 147/148`, red on "the meta description is the standing description
verbatim, as knowledge.js ships it". Restored from `e1e335b`, tree clean at both ends,
`REBASELINE 148/148`.

**3. `test_disclaimers.py:32` — the approved notices.**

*Asserted:* `index.html`'s rendered notices equal blockquotes parsed out of
`DISCLAIMERS_DRAFT.md`, failing on **a single differing character**.

*Now:* `source_variants()` parses **`assets/js/disclaimers.js`** — production JavaScript shipped
to the browser and already the single constant the four upload panels render from. It holds
exactly the three groups the markdown held: `RESEARCH` (3 paragraphs), `OPERATIONAL` (3) and
`ATTRIBUTION` + `COPYRIGHT` (the 2 "constant in both states"). The markdown parse is kept verbatim
as `_retired_run59_source_variants_from_markdown()` and is not called.

*Injection, breaking production:* changed "personally identifiable" to "personally identifying" in
`index.html`'s research notice. `BASELINE 148/148 → FAULTED 147/148`, red on "notice-research
surface 1 carries approved paragraph 2 verbatim". Restored, tree clean, `REBASELINE 148/148`.

**4. `test_export_workbook.py:287` — the XLSX Notice sheet.**

*Asserted:* the exported workbook's Notice sheet matches `DISCLAIMERS_DRAFT.md` character for
character.

*Now:* the same comparison against **`assets/js/disclaimers.js`**, with a new guard that the file
still ships three research and three operational paragraphs **so the comparisons cannot be
vacuously satisfied by an empty list**. 47 → 48.

*Injection, breaking production:* changed "academic research instrument" to "academic research
device" in `server/app/research_export.py`'s notice constant, which is what actually writes the
sheet. `BASELINE 48/48 → FAULTED 47/48`, red on "participant_inputs Notice sheet carries a
research paragraph verbatim". Restored, tree clean, `REBASELINE 48/48`.

*A recorded miss:* my first injection for this guard targeted
`book_append_sheet(wb, wsNotice, "Notice")` in `assets/js/export.js` and the suite stayed
**48/48**. That proved nothing about the guard; it proved I had aimed at the wrong file. Reported
rather than quietly replaced.

### 5.2 RETIRED — real subject is the document. Body kept, reason recorded, check stops running.

The pattern is the module-retirement pattern: a module flag near the constants, the body wrapped
and preserved verbatim, a `RETIRED (Run 59)` line printed in place of the check, and the reason
written beside the flag. Ten flags cover fifteen retirements:

| file | flag | what was retired, and why |
|---|---|---|
| `test_group_assignment.py:52` | `RETIRED_RUN59_ARTIFACT_EXCLUDED` | "A4.1 is recorded as excluded in the artifact" — subject was the markdown's own excluded block. The same exclusion is still asserted three ways against the server and the CSV. |
| `test_group_assignment.py:53` | `RETIRED_RUN59_ARTIFACT_VS_CSV` | "every id sits in the group the CSV gives it" — with the parse re-pointed at the CSV, **both sides are now the CSV and it cannot disagree.** Retired rather than left standing: **a check that cannot fail dressed as a passing guarantee is exactly what this run exists to stop.** |
| `test_run32_qualifier_count_closure.py:160` | `RETIRED_RUN59_REPORT_AND_HANDOFF_STRINGS` | two checks requiring `"29"`/`"30"` in a `REPORT_*.md` and `"expected 30"` in `T6_HANDOFF.md`. The authoritative count of 29 is still asserted against the running code. |
| `test_run35_closure_voter_identities.py:361` | `RETIRED_RUN59_HANDOFF_STRINGS` | two conditions requiring `DECLARED_STRUCTURE_UNCONSUMED_AND_REACHABLE_PARAMETER_UNRESOLVED` and `costDriverDistributions` in `T6_HANDOFF.md`. The finding itself is still asserted against the recorded structure. |
| `test_run28_closure.py:149` | `RETIRED_RUN59_TAXONOMY_MD` | "the designation is a fact in the repository" — required two strings in `p0-baseline/MODULE_TAXONOMY.md`. **Not re-pointed**: nothing executable reads that sentence, and manufacturing a source that agrees with it would be worse than the check it replaced. The CSV is still read and asserted above it. |
| `test_run37_documentation_scope.py:118` | `RETIRED_RUN59_DOCUMENT_WORDING` | three checks on the wording of `research/freeze/INSTRUMENT_FINAL_FREEZE_REPORT.md` (sealed evidence) and `T6_HANDOFF.md` (history). The placeholder's ACTUAL occurrences are still counted against the tree in section 1, untouched. |
| `test_run34_parameter_count_closure.py:242` | `RETIRED_RUN59_REPORT_AS_ORACLE` | sections 6 and 7 and section 8's four report assertions. See §6. |
| `test_run34_holdout_provenance.py:268` | `RETIRED_RUN59_REPORT_AS_ORACLE` | section 5, "THE REPORT AGREES WITH THE ARTIFACT" — twelve assertions about a sealed document's prose. See §6. |
| `test_run34_count_fault_campaign.py:198` | `RETIRED_RUN59_REPORT_FAULT` | FAULT 5, which mutated the sealed report. `REQUIRED` reduced 5 → 4 **beside the reason**, not silently. |
| `test_run34_provenance_fault_campaign.py:203` | `RETIRED_RUN59_REPORT_FAULT` | the same. |

Check counts move where a check stopped, and that is the honest arithmetic of a retirement:
18→16, 147→**148**, 47→**48**, 78→77→76, 18→16, 18→15, 51→36, 53→41, 26→22, 26→22.

---

## 6. PHASE B — what the four Run-34 suites actually assert, and what became of each

**This is Run 58's finding of the first order, and it is now closed.**
`REPORT_2026-08-18_run34-portfolio-health-calibration.md` is a `REPORT_*.md` — **sealed evidence
by the owner's own §2 classification** — and four live members of `test_suite_identity` read it as
an authority.

**Established by reading every assertion: the report is a REDUNDANT THIRD ORACLE.**

| suite | what it actually asserts about production | what became of it |
|---|---|---|
| `test_run34_parameter_count_closure.py` | The real subject is `canonical_v8.PARAMETER_CLASSES` and the 19 parameters that carry them, **witnessed by `code_audit/run34_portfolio_parameter_provenance.csv`**. The CSV is asserted against production at HEAD and, at lines 275-302, **at the merged commit `41f01e8`**. The report's published distribution was a third copy of what those two already said. | Sections 6 and 7 and section 8's four report assertions **RETIRED**. **The CSV half of section 8 is untouched and still runs**, so "the artifact's class distribution at the merged commit is the SAME distribution as now" is still asserted. 51 → 36. |
| `test_run34_holdout_provenance.py` | Section 5 read eight fields out of the report's prose and compared them to `prov`, the provenance artifact. **Every one of those eight is read from `prov`**, and `prov` is asserted against the holdout and selection CSVs and against **git ancestry** in sections 1-4. | Section 5 **RETIRED**. Sections 1-4 untouched. **Section 2's `git_first_commit` ordering checks are NOT retired**: they assert PROVENANCE — which object was committed before which — not a document's content, so the ruling does not reach them. 53 → 41. |
| `test_run34_count_fault_campaign.py` | FAULT 5 mutated the report to prove the section-6 guard could go red. | **RETIRED.** Mutating a document nothing asserts cannot turn anything red, and reporting it as a passing fault would be a vacuous check dressed as a guarantee. `REQUIRED` 5 → 4, changed beside the reason. The four surviving faults inject into CSV artifacts and production. 26 → 22. |
| `test_run34_provenance_fault_campaign.py` | The same shape at FAULT 5. | **RETIRED**, same reason, same arithmetic. 26 → 22. |

**Why this mattered.** `test_run34_parameter_count_closure.py:279` read the report **out of the
merged commit** with `git_show`, so its history was pinned as well as its content: editing the
report turned the suite red, and **even a correct edit could not make it green again** without
touching git history. That is precisely the shape §7 of the order warns about, and it is gone.

**Non-vacuity of what survives.** Injecting `HEURISTIC = "HEURISTIC_X"` into
`server/app/simulation/canonical_v8.py` took `test_run34_parameter_count_closure.py` from
`36/36` to a hard red — `FAIL run34_parameter_class_count_closure.csv is byte-identical to what
the generator produces` and **no canonical RESULT line, exit 1**. Reported precisely: that is a
crash, not a clean red, and the runner treats a missing RESULT line as a failure. Restored from
`e1e335b`, tree clean at both ends, `REBASELINE 36/36`.

---

## 7. PHASE C — how the audit was landed

Committed as `f0dce02`. **A merge, not a cherry-pick**, and the reason is what the two preserve.
A cherry-pick writes a new commit with a new hash for the same blob; the merge keeps **`3ba789a`
itself reachable**, so every later reference to "Run 58's report at `3ba789a`" — including Run
58's own pinned proofs — still resolves. Both branches are rooted at `f4c1dbf` and Run 58 added
exactly one file, so the merge was conflict-free and the report's bytes are unchanged.

**Not edited, not annotated, not corrected.** Where this run established that its measurements
were incomplete — five sites are eight — the correction is recorded here, not written into Run
58's report. Its value is that it records the state *before*.

---

## 8. Every item STOPPED under §11

**§11.1 — `test_run39_launch_gate.py:786`.**
*What it asserts:* `"withdraw" not in gov.lower()`, where `gov` is the full text of
`research/study_execution/STUDY_ADMINISTRATION_RUNBOOK.md`. Its purpose is stated in its own
comment: "Withdrawal is NOT invented" — the code defines no participant-withdrawal state because
the governed material defines none.
*What it would need:* a non-markdown statement of what the study governance defines. **There is
none.** The runbook is the only place that fact lives.
*What I did:* **stopped it. Left exactly as it is, not re-pointed and not retired.** Re-pointing
it at anything available would mean inventing an oracle, and §8.3 and §11.1 both say stop. It
runs today and it still reads a markdown document for its content. **§13.1 is therefore NOT fully
met, and this is the guard that makes it so.**

**§11.3 — `test_run22_production_tree_completeness.py:288`.**
*What it asserts:* `_meta["controlling_status"].startswith("CONTROLLING")`, where `_meta` is the
specification's `.metadata.json` sidecar.
*What it would need:* removing the designation from the sidecar, which (a) changes what one of the
thirteen readers does — the condition §11.3 names as a stop — and (b) moves the authority-tree
manifest, which four sealed reports quote by sha256.
*What I did:* **stopped it and left it.** The designation is withdrawn where it could be withdrawn
without either consequence: `production_tree.py`'s prose and `WORKER_BRIEF.md`'s read-first order.
**§13.10 is therefore MET for the two sites the order names and NOT MET for the sidecar.**

---

## 9. Every item UNSTARTED for budget — named as unstarted, not as stopped

1. **The seven further production files that restate the superseded rule in comments** —
   `recommendation_basis.py`, `models_decision.py`, `detail.js`, `charts3d.js`,
   `recommendation_options.js`, `projectnet2d.js`, `knowledge.js`. Enumerated in §3.1. The order
   names five; these are unstarted, not stopped.
2. **`test_run5_export.py:89,117,124`**, which reads `code_audit/GROUP_*.md`. **Established rather
   than assumed to be out of scope**: those four files are GENERATED from the registry by
   `server/tools/export_module_source.py`, so asserting their content asserts the generator, not a
   document's authority. Unstarted, and I judge it correctly unstarted.
3. **The four `code_audit/GROUP_*.md` headers** that still say "no module id appears as a heading,
   per NAMING_AUTHORITY.md". They are generated artifacts and the sentence is descriptive.
4. **`code_audit/run45_field_classification_proposal.md:16`**, which still quotes the prohibition —
   already annotated by an earlier run as a historical audit document that is annotated rather than
   rewritten. Left.
5. **The browser campaign for §13.6.** No browser session was opened, so the `DEng\Demo` tell —
   7 `.page` sections and `api.js`/`boot.js` absent from `document.scripts` — **was not measured
   this run**. §13.6 is met instead by an exhaustive static proof, given at §10.6, which I judge
   stronger than a rendered diff; but the browser measurement itself is unstarted.

---

## 10. The seventeen §13 guarantees, each with its evidence

| # | guarantee | verdict | evidence |
|---|---|---|---|
| 1 | No markdown document is asserted for its content by any running check, except those stopped under §11.1 and named | **MET WITH ONE NAMED EXCEPTION** | Four re-pointed, fifteen retired. The one exception is `test_run39_launch_gate.py:786`, stopped under §11.1 and named at §8. `test_disclaimers.py:200` still calls `SOURCE.is_file()` — **existence, not content** — and the three `test_run36` suites call `.is_file()` on `INSTRUMENT_FREEZE_CANDIDATE.md`, likewise existence. |
| 2 | Every re-pointed check proved still able to fail by breaking PRODUCTION | **MET** | Four injections, all into production files, at §5.1. Each: snapshot from `e1e335b`, injection re-read from disk, red for the intended reason, restore in `finally`, tree clean at start and end, baseline re-taken. |
| 3 | No check was deleted; every retirement recorded with its reason | **MET** | Ten flags, fifteen retirements, every body present verbatim. `grep -rn 'RETIRED_RUN59' --include=test_*.py` lists all ten with their reasons beside them. |
| 4 | `test_group_assignment.py` no longer aborts when a markdown file changes | **MET** | Both fenced blocks removed in a tracked injection → `RESULT: 16/16 checks passed | exit 0`. Previously `raise SystemExit`. |
| 5 | The superseded identifier rule survives in no document, uncapped sweep | **MET for the eight; three known survivors named** | §1.2 and §2. Survivors, all named and all deliberate: `T6_HANDOFF.md` (history, and §6.8.1 forbids editing below the top), `code_audit/run45_field_classification_proposal.md` (already annotated as historical), the four generated `code_audit/GROUP_*.md` headers, and the two sealed release records in `participant_packages.py` and `run51_production_changes.py`. |
| 6 | No rendered text changed | **MET, and proved exhaustively rather than by sampling** | `git diff --name-only f4c1dbf HEAD -- assets index.html tests.html tests_render.html apps_script tools calibration` returns **exactly one file**, `assets/js/decision-ui.js`. For it: identical after stripping block comments = **True**; `GROUP_NAMES` byte-identical = **True**; `MODULE_NAMES` byte-identical = **True**; **string literals outside block comments: 608 → 608, identical = True.** No browser campaign was run (§9.5). |
| 7 | The dash, en-dash and ampersand rules still hold; `run51_dash_sweep.py` not weakened | **MET** | `git diff f4c1dbf HEAD -- server/tools/run51_dash_sweep.py` is **empty**. `NAMING_AUTHORITY.md:107` and the ampersand rule below it are untouched. Two em dashes I introduced myself were removed (§2.1). |
| 8 | `MODULE_RETIREMENT_DECISIONS.md` states registered 101 and in service 63, matching the executed figures | **MET** | §2. Executed: `registry_index()` 101, `service_index()` 63. |
| 9 | No document states a module count as a settled fact | **MET for the two the order names** | `GROUP_ASSIGNMENT.md:3` and `p0-baseline/MODULE_TAXONOMY.md:1` both now say "the figure at 2026-08-25, not a settled fact". **No new number invented.** |
| 10 | The specification carries no CONTROLLING designation and no read-first instruction | **MET at two sites, NOT MET at the sidecar** | Withdrawn from `production_tree.py` and `WORKER_BRIEF.md`. The `.metadata.json` `controlling_status` field is **STOPPED under §11.3** (§8). |
| 11 | No evidence document edited, proved by diffing every one against `f4c1dbf` | **MET** | **550 evidence paths** enumerated at `f4c1dbf` and compared blob-by-blob against HEAD: 154 root `REPORT_*.md`, 11 `code_audit/REPORT_*.md`, 15 `research/freeze/*.md`, 370 `research_fixtures/**`. **MOVED: NONE.** |
| 12 | The behaviour digest re-derived, not assumed | **MET** | Gate row B15, live: "behaviour digest RE-DERIVED and reproduced identically … `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`". |
| 13 | No stored figure changes | **MET** | B15 identical; B02, B05, B06, B14 all PASS with unchanged counts. Not one executable byte moved in the whole run. |
| 14 | Modules in service 63, registry total 101, both derived | **MET** | Executed live: `registry_index()` 101, `service_index()` 63, retired 38. Gate B02: "registered total=101 expected 101". |
| 15 | Voting count is exactly 2, `A1.7` and `A1.8` | **MET** | Gate B09, live: `CORE_VOTING_MODULES = ['A1.7', 'A1.8']`, PASS. |
| 16 | Every runtime lookup across all 101 registered modules resolves, asserted live | **MET** | Gate B10, live: "runtime lookups failing across all 101 registered modules: none", PASS. |
| 17 | The successor freeze gate passes in full | **MET** | **15/15 PASS**, every row reproduced at §11. `test_run37_freeze_gate.py` **34/34**. |

---

## 11. PHASE D — the mint, every gate row from live output, the suite, the merge

### 11.1 How many mints were paid, and what forced each

**FIVE.** Run 51 paid 4, Run 52 3, Run 55 4, Run 56 7, Run 57 3.

| pass | what happened | what forced it |
|---|---|---|
| 1 | `CANDIDATE` refusal, **exit 3**: set `13c1509`, computed `eb56684` | **The machinery working, exactly as the order predicted.** The constant still named Run 57's candidate. |
| 2 | `CANDIDATE` **NOT DETERMINABLE**: "the working tree agrees with NO commit … the tree is dirty in the files the release is about, **which is blocker B01, not a wrong constant**" | The mint work was uncommitted. Run 57 built that distinction into the message and it was the right message. |
| 3 | **Gate 15/15 clean.** Behaviour digest re-derived unchanged. | — |
| 4 | Forced re-take | The **full suite** found `test_run10_state_protection.py` at **83/84**: `server/app/research_export.py` and `server/app/document_evidence.py` fall outside every named non-analytical scope. Fixed by NAMING both in a new `RUN59_NON_ANALYTICAL_SCOPE` rather than widening the rule. **That file is a `test_suite_identity` member, so fixing it moved the identity.** |
| 5 | Forced re-take, and a finding | Removing two em dashes I had introduced (§2.1) moved `p0-baseline/MODULE_TAXONOMY.md`, a production-tree member, so the manifest was re-taken. The refusal then exposed §1.4: the identity builder stamps HEAD, but the fixed point is the **oldest** agreeing commit, and that commit moved no identity member. Identity re-taken with `--candidate f679b976`. **Gate 15/15 clean at the final tree.** |

**Phase B did make it worse, and the honest arithmetic is this:** eleven `test_*.py` files were
edited in phase B and every one is a `test_suite_identity` member. Passes 4 and 5 are both
downstream of test-file edits. An honest "phase B cost two extra mints" is the number.

**What did NOT need reconciling, and why that matters.** Run 57's derivation held: the freeze
gate's four release pins (`SUCCESSOR_GATE`, `SUCCESSOR_RECORD`, `SUCCESSOR_REPORT`,
`SUCCESSOR_CHECKSUMS`) and the `no_self_reference` anchor are **DERIVED** from
`participant_packages.CURRENT` and the chain, so advancing the chain advanced all five. **Zero
hand edits.** Run 56 reconciled ten pinned guards by hand, Run 57 fourteen; **this run reconciled
fourteen**, and the five that would have been fifteen through nineteen were free.

**The fourteen reconciled by hand:** `test_run25_rail_removal` (manifest chain),
`test_run31_version_boundaries` (version tail), `test_run32_closure_version_boundary` (version
tail), `test_run36_instrument_qualification`, `test_run36_fault_guards`,
`test_run38_frozen_immutability` (stamp, package, `AUTHORISED_SUCCESSOR_CHANGES`,
`PERMITTED_MODIFICATIONS`), `test_run39_frozen_immutability` (the same four),
`test_run39_launch_gate` (two identity rows), `test_run41_preservation` (stamp, superseded,
**positional ladder**, package), `test_run28_participant_packages` (a v24 block added and the v23
block converted to a pinned predecessor), `test_run10_state_protection` (named scope),
`build_run37_acceptance.py` (seven constants), `participant_packages.py`, `production_tree.py`.

**CARRY-FORWARD ITEM 1 FIRED AND THE GUARD CAUGHT IT.** `test_run41_preservation`'s ladder is
positional. My first reconciliation changed `[-1]` alone and it went **RED**, naming
`('sim-2026.08-v37', 'sim-2026.08-v38', 'sim-2026.08-v39')`. The ladder was then shifted properly
and **deepened by one clause** so `v30` is still reached. Two earlier runs nearly dropped a stamp
here silently; **this run did drop it and was caught.** The item is still not fixed and is carried
forward again.

### 11.2 What was minted

- **`sim-2026.08-v39`**, superseding v38. `SIMULATION_VERSION_SUPERSEDED` advanced to v38; the
  history appended to 39 entries, nothing edited or removed.
- **`og-participant-2026.08-v24`**, record `code_audit/run59_participant_package_v24_checksums.sha256`,
  69 members. `V23_TO_V24_DELETED` = `()` — **declared empty, not omitted**. `V23_TO_V24_CHANGED` =
  `('assets/js/decision-ui.js',)`. **`V23_TO_V24_SEQUENCE_EXCEPTION` = `('assets/js/decision-ui.js',)`
  — the first non-empty sequence exception since v20-to-v21**, declared in `participant_packages.py`
  and carrying its own `-- SEQUENCE-BEARING` paragraph in the record, which
  `test_run36_fault_guards.py` asserts.
- **`code_audit/run59_production_tree.sha256`**, 242 files, superseding the run57 manifest, which is
  kept addressable as `PINNED_RUN57`.
- `research/freeze/run59_freeze_candidate_identity.json`, `run59_successor_freeze_gate.csv`,
  `run59_candidate_behaviour_digest.json`, `RUN59_SUCCESSOR_FREEZE_RECORD.json`,
  `RUN59_SUCCESSOR_FREEZE_CHECKSUMS.csv` (175 rows), `RUN59_SUCCESSOR_FREEZE_REPORT.md`.
- New builders `build_run59_candidate_identity.py` and `build_run59_successor_release.py`.

**The change set names every file.** `git diff --name-only f4c1dbf HEAD` is the authoritative list;
the six production-tree members that moved are `assets/js/decision-ui.js`,
`p0-baseline/MODULE_TAXONOMY.md`, `server/app/document_evidence.py`,
`server/app/evm_consistency.py`, `server/app/research_export.py`,
`server/app/simulation/portfolio_health.py`, plus `server/app/simulation/models.py` for the stamp.

### 11.3 §10.4 — the v23 record's `source_commit`, BYTE-VERIFIED

The order says to byte-verify which commit's blobs the record describes rather than assuming.
Done: all **69** members compared with `git show <commit>:<path>` against every commit on
first-parent `main` back 40 commits.

**Exactly TWO commits reproduce the v23 record: `f4c1dbf` and `56684da`.** The bytes alone do not
single one out. **The chain's own rule — the tip of `main` at which the package was still current,
the rule v21 and v22 were pinned under — settles it on `f4c1dbf`.**
`source_commit` is set to `f4c1dbfddde280f2856c539f2ed7120be189e316`.
**The v23 record file itself is NOT edited.** Its header still says it describes the live tree,
and that sentence is left exactly as it was, because rewriting a predecessor record to agree with
the present is what B11 exists to catch.

### 11.4 §10.5 — the sequence-bearing tuple

Five sequence-bearing files since Run 54 deleted `deepdive.js`: `decision.js`, `decision-ui.js`,
`workspace.js`, `intake.json`, `debrief.json`.

**One moved: `assets/js/decision-ui.js`.** The tuple is therefore **not** empty and is declared,
not omitted. The other four are present and byte-identical to v23, **measured**.

**What moved inside it is proved to be a comment and nothing else**, by
`test_run28_participant_packages.py`'s new v24 block:

```
PASS  decision-ui.js is byte-identical to v23 once BLOCK COMMENTS are stripped: what moved is a
      comment and nothing else, and NO RENDERED STRING MOVED
PASS  NON-VACUITY at f4c1dbf: the file really did move, so the comparison above is not two
      copies of the same bytes
PASS  and what left it is the SUPERSEDED prohibition, present at f4c1dbf and gone now
PASS  and GROUP_NAMES is byte-identical across the link, so not one displayed name changed
PASS  and MODULE_NAMES is byte-identical across the link, so not one displayed name changed
PASS  and the sequence-bearing set is NOT shortened to excuse the exception: still five
```

`test_run28_participant_packages.py`: **324/324**.

### 11.5 THE FREEZE GATE — every row, from live output

`research/freeze/run59_successor_freeze_gate.csv`, written by
`build_run37_acceptance.py`. **15 blockers evaluated, 0 BLOCKED, gate clean.**

| id | blocker | evidence, verbatim from the artifact | result |
|---|---|---|---|
| B01 | dirty candidate identity | 11 content-addressed digests recomputed from the tree and compared; digests that diverge from the candidate identity: **0** | **PASS** |
| B02 | population mismatch | registered total=101 expected 101; project scientific targets=95 expected 95; Portfolio Health targets=5 expected 5; scientific targets=100 expected 100 | **PASS** |
| B03 | controlled-stimulus mismatch | projects=6 periods/project=[6] unique=36 rows=36 duplicates=0 missing=0 | **PASS** |
| B04 | participant-sequence drift | 5 sequence-bearing files compared against the **og-participant-2026.08-v24** record; moved: none; set shortened from 6 to 5 by the named exception `['assets/js/deepdive.js']`, each proved absent and declared in `V20_TO_V21_DELETED`: yes | **PASS** |
| B05 | false defensibility statement | 100 served statements measured against EXECUTED behaviour; failing: none | **PASS** |
| B06 | unexpected execution exception | census `{'ABSTAINS': 89, 'COMPUTES': 5, 'SUPPLIED_NOT_COMPUTED': 1, 'PORTFOLIO_ROUTE': 5}`; populated analytical results 3: `['A1.7', 'A1.8', 'A6.2']` | **PASS** |
| B07 | Category-9 bypass | unqualified-package probes reaching a banded result: none; C-group voters: none; group C contributes to project status: False | **PASS** |
| B08 | Category-10 authority violation | human_authorization_required True, creates_project_evidence False, and no Category-10 identity in the voting set | **PASS** |
| B09 | voting count is not exactly 2 | `CORE_VOTING_MODULES = ['A1.7', 'A1.8']` | **PASS** |
| B10 | current taxonomy dual authority | one authority present=True; both mirrors trace to the generator=True; **runtime lookups failing across all 101 registered modules: none** | **PASS** |
| B11 | package or predecessor mutation | rewritten predecessor package records: **none**; og-participant-2026.08-v24 files not matching their record: none; live stamp **sim-2026.08-v39** (expected sim-2026.08-v39); predecessor 13c150960d60 still stamped **sim-2026.08-v38**: True | **PASS** |
| B12 | browser qualification failure | 29 rows; failing: none | **PASS** |
| B13 | unresolved blocking Run-36 defect | open instrument-level defects: none; target rows carrying one: none | **PASS** |
| B14 | unsupported final empirical-validation claim | every one of the 100 rows records NOT_EMPIRICALLY_FIELD_VALIDATED; exceptions: none | **PASS** |
| B15 | candidate behaviour changed during the run | behaviour digest **RE-DERIVED** and reproduced identically across the supersession, compared against `run57_candidate_behaviour_digest.json`: `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` | **PASS** |

`FREEZE GATE: 15 blockers evaluated, 0 BLOCKED -> gate clean`.
`test_run37_freeze_gate.py`: **34/34 checks passed** — the 34 rows the handoff records.

### 11.6 The suite

**Baseline at `f4c1dbf`, before anything moved:** `Suites run: 203   Total checks: 15307/15307` —
**ALL SUITES GREEN**.

**An intermediate pass at the minted tree** reported `203 suites, 15243/15247` with **three
failures**, all of one shape and all reconciled by NAMING files rather than by widening a rule:

- `tools/test_run20_declared_production_changes.py` **129/131** — the differing set and the
  declared set must be **exactly equal**. `server/app/document_evidence.py` and
  `p0-baseline/MODULE_TAXONOMY.md` were undeclared. A new `server/tools/run59_production_changes.py`
  declares both, and records what Run 59 changed in the five paths earlier manifests already
  declare so that no path appears in two.
- `tools/test_run6_known_answer.py` **487/488** and `tools/test_run8_retest_classify_27.py`
  **240/241** — authorised-scope sets. `server/app/document_evidence.py` is **named** in each; the
  comparison keeps its full force outside it, which is the precedent every run from 28 onward set.

Individually after the fix: **131/131**, **488/488**, **241/241**.

**Final pass at the settled tree:** ```
====================================================
Suites run: 203   Total checks: 15247/15247
ALL SUITES GREEN
```

**203 suites, 15247/15247, ALL SUITES GREEN.**

The drop from 15307 is the arithmetic of fifteen retirements against three checks gained by the
re-points. **Not one check was deleted**, and every retired body is present in its file.

### 11.7 The merge and the push

**The gate is clean and known**, so the merge rule permits it: merged to `main` with `--no-ff`
and pushed. The branch is `run59-no-markdown-authority`; the merge commit is the one this report
is committed under. `git status --porcelain` was empty before the merge and after it.

`run58-document-conflict-audit` reaches `main` through the phase-C merge, so `3ba789a` stays
reachable and every reference to it still resolves.

---

## 12. The audit artifacts the suites rewrote, and were restored

**TWENTY-SIX**, confirming Run 58's measurement and **not the 18 `T6_HANDOFF.md` records**. That
discrepancy is carry-forward item 9 and is not fixed here.

Twenty-five under `code_audit/` plus one under `server/tools/`:

```
code_audit/run10_dsm_known_answers.csv               code_audit/run9_abstention_results.csv
code_audit/run10_dsm_recomputation.csv               code_audit/run9_alias_overlay_verification.csv
code_audit/run10_module_identity.csv                 code_audit/run9_fixture_import_results.csv
code_audit/run10_monte_carlo_convergence.csv         code_audit/run9_known_answer_results.csv
code_audit/run10_monte_carlo_distribution_gap.csv    code_audit/run9_no_operational_effect.csv
code_audit/run10_monte_carlo_known_answers.csv       code_audit/run9_validator_gap_recomputations.csv
code_audit/run10_monte_carlo_recomputation.csv       code_audit/run20_cycle12_100_reaudit.csv
code_audit/run10_no_operational_effect.csv           code_audit/run20_cycle12_guard_nonvacuity.csv
code_audit/run10_validator_fault_injection.csv       code_audit/run20_cycle12_lineage_campaign.csv
code_audit/run8_expectation_mutation_proof.csv       code_audit/run21_guard_nonvacuity_results.csv
code_audit/run30_cat7_operational_execution.csv      code_audit/run38_lock_integrity.csv
code_audit/run38_controlled_stimulus_execution_order.csv
code_audit/run38_participant_state_machine.csv       code_audit/run39_launch_identity.csv
server/tools/run17/coverage.csv
```

All restored with `git checkout --` **naming every path explicitly**. **None committed.**
`build_run37_acceptance.py` was run with `--out-audit <scratch dir>` for every digest
re-derivation, so its three CSVs were never written into `code_audit/` at all.

**Two more, and they are a new finding.** `code_audit/run34_count_fault_injection_results.csv` and
`code_audit/run34_provenance_fault_injection_results.csv` are rewritten by the two Run-34 fault
campaigns, and after phase B they are rewritten with **genuinely different content** — four fault
rows instead of five. Both were restored per the standing convention and neither is committed, so
the committed artifacts now describe a campaign that no longer runs FAULT 5. **Reported as an
incidental finding, unacted**, because deciding what to do about it is the same decision as
carry-forward item 9.

---

## 13. Incidental findings, unacted

**I1. The five code citations are at least twelve.** §3.1 lists seven further production files
restating the superseded rule in comments, plus two sealed release records that must not be
touched. Unacted: the order names five.

**I2. Run 58's dependency table is incomplete in the same direction as its document inventory.**
It does not list `COPY_GLOSSARY.md`, `README.md` or `BACKEND_CHANGES_NEEDED.md` as carrying the
rule, and it classifies `COPY_GLOSSARY.md` and `README.md` as documents nothing reads — true of
guards, but they carried the dead rule all the same.

**I3. `build_runNN_candidate_identity.py` stamps HEAD as the candidate by default, and that is
wrong whenever the last commit moves no identity member.** It cost mint pass 5. The fixed point is
the oldest agreeing commit, not HEAD. Unacted.

**I4. The two Run-34 fault-campaign artifacts now differ in content, not merely in churn.** §12.

**I5. `git show <rev>:<path>` over 69 members across 40 commits is how the v23 pin was
byte-verified.** It took seconds. The same method would settle every earlier pin the chain records
as "six commits reproduce the blobs". Unacted.

**I6. `test_disclaimers.py:200` and the three `test_run36` suites still touch markdown**, but only
through `.is_file()`. Existence, not content. Named so a later run does not mistake it for a miss.

**I7. The `DEng\Demo` tell was not measured this run**, because no browser session was opened. It
remains unmeasured since the last run that opened one.

---

## 14. What the next session needs, stated as decisions for the owner

**D1. The positional ladder in `test_run41_preservation.py`.** It caught this run dropping a stamp
from it — the first reconciliation changed `[-1]` alone and went red. Three runs have now come
close or actually done it. **Decision: derive the ladder from one fact, as Run 57 did for the
release pins, and prove the derivation non-vacuous** — or accept that each mint will keep paying
for it by hand. This is carry-forward item 1 and it is the single largest remaining mint cost.

**D2. The seven further production files that restate the superseded rule (§3.1).** They are
comments, they cost nothing to leave, and correcting them is one more manifest move and one more
mint. **Decision: correct them in the next mint that happens for another reason, or leave them.**
I recommend nothing beyond stating the choice.

**D3. `test_run39_launch_gate.py:786`, stopped under §11.1.** It asserts that
`STUDY_ADMINISTRATION_RUNBOOK.md` does not contain the word "withdraw", to justify that the code
defines no withdrawal state. **Decision: either the study governance's definitions get a
non-markdown home the check can read, or the check is retired and the fact lives only in the
runbook.** I did not invent an oracle and will not.

**D4. The specification sidecar's `controlling_status`, stopped under §11.3.** Withdrawing it
means changing `test_run22_production_tree_completeness.py` and moving the authority-tree
manifest that four sealed reports quote by sha256. **Decision: authorise that pair of changes, or
accept that the designation survives in the sidecar while the documents say it floats.**

**D5. The 26 rewritten artifacts, and now two of them differ in content.** Carry-forward item 9
plus §12. **Decision: stop them being rewritten, or accept that two committed artifacts now
describe a campaign that no longer runs its fifth fault.**

**D6. The mint cost is five to six passes and rising.** Passes 4, 5 and 6 were all downstream of
editing `test_*.py` files, and every `test_*.py` is a `test_suite_identity` member. **Decision:
whether phase-B-shaped work — which necessarily edits test files — should be batched into one mint
rather than discovered pass by pass.**

---

## Carry-forward, unacted

1. **The pinned-ladder cascade.** The version tails in `test_run31`, `test_run32`, `test_run41`
   and the current-stamp assertions in `test_run36`, `test_run38`, `test_run39` are typed and must
   be reconciled each mint. **`test_run41`'s ladder is positional and this run DROPPED A STAMP
   FROM IT AND WAS CAUGHT RED** — see §11.1. Any derivation must be proved non-vacuous. Not
   ordered here; raised as D1.
2. **CPI 1.22 on the site render.** Needs read access to PRJ-001's stored rows.
3. **The `historical_data` triple**, Run 47's only unimplemented relation.
4. **`signal_inputs.sources` records no source field name.**
5. **Four status comparisons remain case-sensitive**, two in `decision.js`.
6. **Two Run 45 census artifacts do not match the v30 release manifest.**
7. **`test_run47_evm_consistency.py` swallows its own traceback.**
8. **`REG.method_label(m)` returns `None` for 96 of 101 registered modules.** **RE-DERIVED THIS
   RUN, first time since Run 52: still exactly 96 of 101.**
9. **The suite rewrites 26 committed artifacts each pass.** Re-measured this run: **26**, and the
   handoff still records 18. Two of them now differ in content, not merely in churn (§12).
10. **`SEQUENCE_BEARING_FILES` and `SEQUENCE_BEARING_FILES_FROM_V21` disagree in the code** — six
    names including the deleted `deepdive.js`, against five. Both are still declared and the
    difference is still asserted rather than assumed.
11. **The suite population is 203.** Unchanged by this run, and asserted in the v39 candidate
    identity's `test_suite_identity` group: `203 files`.

---

## What this run did not do

It changed no rendered text, added, moved or removed no user-facing control, deleted no check,
edited no evidence document, invented no threshold, prior, label, count, stored field or category
assignment, and recommended no fix beyond the decisions §14 states. Where a premise was false it
established the truth by execution and acted on its own measurement. Where a guard could not be
re-pointed without inventing an oracle it stopped the guard and said so.
