# Run 58 — the document conflict audit. READ-ONLY. NOTHING RESOLVED.

**Repository:** the Linux clone at `/home/user/LinPRojectRadar`.
**Interpreter:** `python3` 3.11.15 at `/usr/local/bin/python3`. **No `.venv` exists** (`ls -d .venv`
→ "No such file or directory"), so the documented fallback was used, as `T6_HANDOFF.md:939-941`
records.
**Branch:** `run58-document-conflict-audit`, rooted at `f4c1dbf`. **NOT merged to `main`.**

## 0. THE STATEMENT THE ORDER REQUIRES AT THE TOP

**No file other than this report was changed, and nothing other than this report was committed.**

One qualification, stated because it is true and not because it is a defect: running
`server/run_all_suites.sh` to verify the check total (§1) caused the suite to rewrite **26**
committed audit artefacts in the working tree. This is the known carry-forward recorded at
`T6_HANDOFF.md:13601-13603` ("The full suite still rewrites 18 committed audit artifacts …
Restore all 18; commit none"). Every one was restored with `git checkout --` naming each path,
and `git status --porcelain` returned **empty** before the report was written. **The count is now
26, not 18** — see incidental finding I1.

`git add -A` and `git add .` were never run. The only `git add` names this report's path.

---

## 1. §9.1 — THE TREE AT THE START AND AT THE END

### Start

| Claim (order §3) | Verified? | Command and output |
|---|---|---|
| `git status --porcelain` empty | **YES** | empty output |
| `main == origin/main == f4c1dbf` | **YES** | `git rev-parse HEAD main origin/main` → `f4c1dbfddde280f2856c539f2ed7120be189e316` ×3 |
| stamp `sim-2026.08-v38` | **YES** | `server/app/simulation/models.py:718` → `SIMULATION_VERSION = "sim-2026.08-v38"` |
| package `og-participant-2026.08-v23` | **YES** | `server/tools/participant_packages.py:610` |
| 203 suites | **YES** | `ls server/tools/test_*.py \| wc -l` = 193; `ls server/tests/test_*.py \| wc -l` = 10; 193+10 = 203 |
| 15,307 green | **YES** | `bash server/run_all_suites.sh` → `Suites run: 203   Total checks: 15307/15307` / `ALL SUITES GREEN` |
| gate 34/34 | **YES** | `python3 tools/test_run37_freeze_gate.py` → `RESULT: 34/34 checks passed` |
| 254 tracked `.md` | **YES** | `git ls-files '*.md' \| wc -l` = 254 |

**Unlike Runs 55, 56 and 57, every starting-point claim in this order is CORRECT.** Not one had
to be corrected. That is itself worth recording.

### End

`git status --porcelain` → **empty**, apart from the untracked report file before it was
committed. `HEAD` on branch `run58-document-conflict-audit` = one commit above `f4c1dbf`,
containing exactly one file. `main` is untouched at `f4c1dbf`.

**Nothing else changed.**

---

## 2. §9.2 — THE CLASSIFICATION OF ALL 254 MARKDOWN DOCUMENTS

The enumeration is `git ls-files '*.md'`, which returned **254** paths, matching the order's own
figure. **Nothing was capped and nothing was truncated**; every path below is accounted for, and
the group totals sum to 254.

### 2.1 The evidence families, tabled as groups (§5's permitted collapse), with exact membership and count

| Group | Exact membership rule | Count | Class | Basis for the classification |
|---|---|---|---|---|
| **E1** | `REPORT_*.md` at the repository root | **154** | EVIDENCE | Each records what was true at one stamp and was the basis on which that mint was accepted. `git ls-files 'REPORT_*.md' \| wc -l` = 154. The heads of 12 spread across the range (2026-08-01 through 2026-08-24) were read; every one opens with a run/date/branch/stamp header and closes on measured results. **Exception, reported at §5 below: `REPORT_2026-08-18_run34-portfolio-health-calibration.md` is read as an authority by four live suites.** |
| **E2** | `code_audit/REPORT_*.md` | **11** | EVIDENCE | Same shape; cycle reports of Runs 5, 13 and 20. `git ls-files 'code_audit/REPORT_*.md' \| wc -l` = 11. |
| **E3** | `research/freeze/*.md` | **15** | EVIDENCE | Sealed successor-freeze and freeze-candidate records. The freeze gate's six `predecessor_release_preserved` rows (gate rows 21–26) read them. Heads of `RUN41`, `RUN55`, `RUN56` and `RUN57` read individually. |
| **E4** | `research_fixtures/**/*.md` | **27** | EVIDENCE (24) / AUTHORITY (3) | The 6 `VALIDATION_SUMMARY.md` and the `AUDIT_RESOLUTION_*`/`CLAUDE_CODE_HANDOFF_*` files record a fixture package's validation at a moment → EVIDENCE. The three **live-corpus** READMEs — `research_fixtures/README.md`, and `OG-SYNTH-0.5/README.md`, `OG-SYNTH-0.6/README.md` — state standing rules about the synthetic corpus; `OG-SYNTH-0.6/README.md` is named in code at `server/tools/synthetic_packages.py:146` and `research_fixtures/README.md` is cited as a rule source at `server/tools/run38_dryrun.py:8`. |

**E-total: 207.** Not one of these 207 is proposed for merging (§6 of this report).

### 2.2 The remaining 47, classified individually

| Path | Class | Last commit | Bytes | What it claims authority over |
|---|---|---|---|---|
| `NAMING_AUTHORITY.md` | **AUTHORITY** | 2026-08-23 | 8,333 | What the platform and its taxonomy are called, and the standing description every surface quotes verbatim. |
| `GROUP_ASSIGNMENT.md` | **AUTHORITY** | 2026-08-11 | 4,296 | The verified group taxonomy and the "100, not 101" computation count; declares itself "the authority for how the analytical layer is described". |
| `T6_HANDOFF.md` | **MIXED** | 2026-08-24 | 940,853 | Lines 1–10 and the top dated section are live standing authority (what to read first, current stamp/gate state); everything from line 113 downward is the run history. **The mixture is itself a finding — see §4.2.** |
| `MODULE_RETIREMENT_DECISIONS.md` | **AUTHORITY** | 2026-08-22 | 39,641 | The 38 retirements, their reasons, and the roster mechanism. |
| `FIELD_CLASSIFICATION_DECISIONS.md` | **AUTHORITY** | 2026-08-22 | 5,996 | The canonical field classification implemented in `server/app/field_registry.py`. |
| `DISCLAIMERS_DRAFT.md` | **AUTHORITY** | 2026-08-04 | 6,660 | The live disclaimer text by account type. Filename says "DRAFT"; line 1 says "APPROVED AND LIVE" and lines 3–5 explain the filename is historical. Not a conflict. |
| `COPY_GLOSSARY.md` | **AUTHORITY** | 2026-08-04 | 5,232 | The vocabulary the platform uses for its own concepts, and American-English spelling with two named exclusions. |
| `README.md` | **AUTHORITY** | 2026-08-04 | 5,213 | What the repository is; quotes `NAMING_AUTHORITY.md`'s short form verbatim. |
| `remediation_programme.md` | **MIXED** | 2026-08-11 | 30,378 | **The order named this as the trap and the order is right.** §§"Run 1"–"Run 5" (lines 15–160) are closed history, all marked DONE, the newest dated 2026-08-11. §§"Working conventions", "Container quirks", "Test discipline", "Naming rules", "Settled decisions, do not re-raise", "Production re-entry acceptance gate" (lines 216–498) are **live standing authority** and are cited as such — line 248 is one of the four places recording that `window.confirm` returns false in this container. |
| `remediation_decisions_answered.md` | **MIXED** | 2026-08-10 | 7,107 | Owner answers to twenty decisions (live rulings) plus Claude recommendations explicitly marked "open to correction". Its two named source documents are absent from the repository — finding I3. |
| `SECURITY_SCAN.md` | **EVIDENCE, and UNREAD** | 2026-08-04 | 9,698 | A scan report dated 2026-07-08 against `backend/main.py`. **Nothing anywhere references it** (§7). Its subject still exists (`backend/main.py`, 13 `@app.post` routes), so it does **not** meet the order's DEAD test, which requires all three conditions. |
| `BACKEND_CHANGES_NEEDED.md` | **MIXED** | 2026-08-04 | 32,358 | Apps Script `Code.gs` items the front end is ready for. Describes an era before the FastAPI server; retains item-by-item specifications a session could still act on. **Undetermined whether any item is still wanted** — see §4.2 finding U1. |
| `training_mode_roadmap.md` | **AUTHORITY** | 2026-08-04 | 10,596 | The training-mode product decisions and status markers. Explicitly "Product, not praxis." |
| `training_pmp_upgrade_roadmap.md` | **AUTHORITY** | 2026-08-04 | 8,250 | Training-simulation PMP-area thread coverage and its constraints. |
| `training_us_contract_regimes.md` | **AUTHORITY** | 2026-08-04 | 6,142 | The three US contract forms the training briefs are written against, and the copyright constraint on quoting them. |
| `p0-baseline/MODULE_TAXONOMY.md` | **AUTHORITY** | 2026-08-04 | 4,864 | Module numbering and grouping; names `module_renumbering_map.csv` as "the single source of truth". **Production-tree manifest member.** |
| `p0-baseline/contracts/INVENTORY_FINDINGS.md` | **EVIDENCE** | 2026-08-04 | 7,486 | Migration-phase-M0 action inventory findings. **Production-tree manifest member**, so it cannot be moved without a mint. |
| `p0-baseline/reconciliation/README.md` | **AUTHORITY** | 2026-08-04 | 568 | The rule that an import is not successful until a report shows zero unexplained discrepancies. **Production-tree manifest member.** |
| `server/app/simulation/VALIDATION.md` | **AUTHORITY** | 2026-08-17 | 31,796 | One row per module: what was compared against the JavaScript and matched. **Production-tree manifest member.** |
| `assets/vendor/ASSETS.md` | **AUTHORITY** | 2026-08-10 | 5,598 | Sources, licences and sizes of every vendored runtime asset, and the no-CDN rule. **Production-tree AND participant-package manifest member — the only `.md` in the participant package.** |
| `server/README.md` | **AUTHORITY** | 2026-08-04 | 42,876 | The FastAPI service, its endpoints and the fact that no traffic is pointed at it. |
| `backend/README.md` | **EVIDENCE** | 2026-08-04 | 2,548 | The v9-era FastAPI prototype at `apiVersion lin-project-radar-backend-v2.0`. `server/README.md:6-7` records that `backend/` is untouched and superseded. |
| `research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md` | **AUTHORITY** | 2026-08-13 | 102,006 | The controlling supervisory method specification. **Authority-tree manifest member; read by 13 Python files.** See conflict 6.1-5. |
| `research/methodology/run34_portfolio_calibration_protocol.md` | **AUTHORITY** | 2026-08-18 | 11,745 | The Portfolio Health calibration protocol. **Authority-tree member**; read by `server/tests/test_run34_holdout_provenance.py:43`. |
| `research/methodology/run35_empirical_validation_protocol.md` | **AUTHORITY** | 2026-08-18 | 11,232 | The empirical-validation protocol and its "0 of 100" limitation. **Authority-tree member.** |
| `research/methodology/run38_frozen_analysis_dataset_contract.md` | **AUTHORITY** | 2026-08-19 | 7,194 | The frozen analysis dataset contract. **Authority-tree member.** |
| `research/methodology/run38_research_data_contract.md` | **AUTHORITY** | 2026-08-19 | 9,780 | The research data contract. **Authority-tree member.** |
| `research/methodology/run39_dataset_classification_contract.md` | **AUTHORITY** | 2026-08-19 | 4,990 | Dataset classification. **Authority-tree member.** |
| `research/study_execution/STUDY_ADMINISTRATION_RUNBOOK.md` | **AUTHORITY** | 2026-08-19 | 10,370 | How the study is administered. **Quoted inside a live check:** `server/tools/test_run39_launch_gate.py:784` reads it. |
| `research/study_execution/MAIN_STUDY_DATA_FREEZE_PROCEDURE.md` | **AUTHORITY** | 2026-08-19 | 5,331 | The data-freeze procedure for the main study. |
| `research/study_execution/MAIN_STUDY_LAUNCH_CHECKLIST.md` | **AUTHORITY** | 2026-08-19 | 3,970 | The launch checklist. |
| `research/study_execution/OWNER_WEBSITE_ACCEPTANCE_CHECKLIST.md` | **AUTHORITY** | 2026-08-19 | 7,786 | What the owner must accept before launch. |
| `research/study_execution/PILOT_EXECUTION_PROTOCOL.md` | **AUTHORITY** | 2026-08-19 | 7,015 | The pilot execution protocol. |
| `code_audit/GROUP_A_project-health.md` | **EVIDENCE, but READ BY A GUARD** | 2026-08-11 | 130,183 | A Run-5 module source export. `server/tools/test_run5_export.py:89` reads it. Regenerable from the registry by `server/tools/export_module_source.py`. |
| `code_audit/GROUP_B_recommendation-governance.md` | **EVIDENCE** | 2026-08-11 | 80,373 | Same, Group B. |
| `code_audit/GROUP_C_data-evidence-health.md` | **EVIDENCE** | 2026-08-11 | 11,865 | Same, Group C. |
| `code_audit/GROUP_D_portfolio-level.md` | **EVIDENCE** | 2026-08-11 | 11,834 | Same, Group D. |
| `code_audit/SHARED_MACHINERY.md` | **EVIDENCE** | 2026-08-10 | 9,456 | Common code quoted once, referenced by name from the four group files. |
| `code_audit/RUN20_HANDOFF_AFTER_CYCLE6.md` | **EVIDENCE** | 2026-08-13 | 5,092 | The state of Run 20 after cycle 6 of 12. Superseded by Run 20's own completion. |
| `code_audit/run12_release_freeze.md` | **EVIDENCE** | 2026-08-12 | 2,488 | The Run-12 release and refreeze record; states itself ADDITIVE. |
| `code_audit/run45_field_classification_proposal.md` | **EVIDENCE** | 2026-08-23 | 22,530 | A PROPOSAL, ruled on by `FIELD_CLASSIFICATION_DECISIONS.md`. **Correctly annotated rather than rewritten** by Run 54 at lines 11–14 — the model for how a superseded quotation is handled. |
| `apps_script/BACKEND_PROVENANCE.md` | **AUTHORITY** | 2026-08-04 | 5,327 | What is known and unknown about the deployed Apps Script backend, and the rule that source comments are not evidence of what is deployed. |
| `apps_script/reference/README.md` | **AUTHORITY** | 2026-08-04 | 1,421 | That `Code_v10.36_editor_head.gs` is editor HEAD and must not be checksummed as a deployment artifact. |
| `apps_script/deployed/README.md` | **AUTHORITY** | 2026-08-04 | 211 | What lands in that directory and that it is empty at M0. |
| `apps_script/head/README.md` | **AUTHORITY** | 2026-08-04 | 46 | Same, for editor HEAD snapshots. |
| `tools/contract-fixtures/README.md` | **AUTHORITY** | 2026-08-04 | 2,849 | The Apps Script response-contract capture tool and the D2 gate. |
| `server/tools/run17/categories/WORKER_BRIEF.md` | **AUTHORITY** | 2026-08-13 | 9,332 | The binding brief for a Run-19 category worker: what the controlling authority is and the house style. |

**Count check: 207 (E1–E4) + 47 = 254.** ✔

---

## 3. §9.3 — EVERY §6.1 CONFLICT: AUTHORITY AGAINST AUTHORITY

Seven. Numbered for reference only; **they are not ranked and no resolution is recommended.**

### CONFLICT 6.1-1 — displayed module identifiers: NAMING_AUTHORITY vs GROUP_ASSIGNMENT

**Subject:** whether "Cat 4", "1.7", "PH.2" and "A4.2" may appear in user-facing text.

`NAMING_AUTHORITY.md:96-99` (commit `2457fa1`, **2026-08-23**, the NEWER):

> **Displayed identifiers are acceptable.** "Cat 4", "1.7", "PH.2" and "A4.2" may appear in
> user-facing text. The owner ruled the former prohibition SUPERSEDED on 2026-08-23, and Run 54
> records the ruling here so that this file and the handoff agree. Groups and purposes remain the
> better default where the identifier adds nothing, but an identifier is no longer a defect.

`GROUP_ASSIGNMENT.md:17-18` (last commit **2026-08-11**, the OLDER):

> - **Refer to groups by group and purpose, never by module id or number.** "Cat 4", "1.7", "PH.2"
>   and "A4.2" do not belong in anything a user reads. The ids below are keys, not names.

**The same four example strings, ruled opposite ways.** The two files were never reconciled:
`git log --oneline -- NAMING_AUTHORITY.md` shows `2457fa1` (Run 54 phase D) touched only that
file. Run 54's own commit message enumerates "the six quoting sites" it reconciled;
`GROUP_ASSIGNMENT.md` is **not among them**.

**Later owner ruling elsewhere:** yes — the 2026-08-23 ruling recorded at `NAMING_AUTHORITY.md:97`
and at `T6_HANDOFF.md`'s Run 54 section. `GROUP_ASSIGNMENT.md` predates it and does not carry it.

**Weight:** `GROUP_ASSIGNMENT.md` is one of the most load-bearing documents in the repository —
`server/tools/test_group_assignment.py:42` parses its fenced ```` ```group-assignment ```` block
and asserts it against `VALIDATED | PORTFOLIO_VALIDATED`.

### CONFLICT 6.1-2 — the same rule, in `remediation_programme.md`

`remediation_programme.md:279` (last commit **2026-08-11**), under a heading `## Naming rules`:

> - No module ids or numbers in user-facing text. Groups by name and purpose.

Against `NAMING_AUTHORITY.md:96-99` as quoted above. Also not among Run 54's six sites.

### CONFLICT 6.1-3 — the same rule, in `training_pmp_upgrade_roadmap.md`

`training_pmp_upgrade_roadmap.md:140` (last commit **2026-08-04**):

> - No module ids or numbers in user-facing text.

Against `NAMING_AUTHORITY.md:96-99`. Not among Run 54's six sites.

### CONFLICT 6.1-4 — the same rule, in the Run-19 worker brief

`server/tools/run17/categories/WORKER_BRIEF.md:119-121` (last commit **2026-08-13**), under
`## HOUSE STYLE FOR ANY USER-FACING OR REPORT PROSE`:

> No module ids or numbers in participant-facing text. No em dashes. "and", not "&".
> PCEIF and PDAF are retired as product names. Write plainly and specifically.

Against `NAMING_AUTHORITY.md:96-99`. The brief describes itself as **"(binding)"** at line 1. Not
among Run 54's six sites.

### CONFLICT 6.1-5 — PCEIF: retired framing vs CONTROLLING authority

`NAMING_AUTHORITY.md:10-13` (**2026-08-23**):

> Those are stale. **PCEIF is retired. So is PDAF.** The code has not caught up with a
> research-direction change.
>
> Do not use either name in anything you write, and do not reason from the framing they carry.

`server/tools/run17/categories/WORKER_BRIEF.md:4-7` (**2026-08-13**):

> ## THE CONTROLLING AUTHORITY
> `/home/user/LinPRojectRadar/research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md`
> (3,600 lines, SHA-256 328b50133f1d2a8d710d3cca787c24c22e2cdad0b09fe92ae2c7b7a55b8d299e).

and `server/tools/production_tree.py:103-106`, the code that defines the authority tree:

> ("research/methodology", True,
>  "the controlling supervisory method specification and its metadata record. CONTROLLING "
>  "status: where this and the implementation disagree, this governs what the method ought "
>  "to be"),

**A document whose framing one authority forbids reasoning from is designated CONTROLLING by
another authority and by the code.** The specification is pinned in the authority-tree manifest
(sha256 `b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a8170704dc1596`) and read by **13**
Python files.

The order's own §5 lists `WORKER_BRIEF.md` nowhere and `NAMING_AUTHORITY.md:22` does say
"`PCEIF_*` on development-era artifacts | Nobody sees these. Leave them." — which may or may not
extend to a file explicitly named CONTROLLING. **The owner rules; this run does not.**

### CONFLICT 6.1-6 — 100 computations vs 101 computations

`GROUP_ASSIGNMENT.md:3` (**2026-08-11**):

> **100 computations, in four groups.** This file is the authority for how the analytical layer is
> described.

`p0-baseline/MODULE_TAXONOMY.md:1-4` (**2026-08-04**):

> # Module taxonomy: 101 distinct computations across four groups
>
> `module_renumbering_map.csv` in this directory is the single source of truth for module numbering
> and grouping.

Two documents, each declaring itself the source of truth, differ on the count of "computations" —
100 against 101. `NAMING_AUTHORITY.md:75-86` reconciles the pair explicitly (101 registered, 100
computed, the difference being `A4.1` Document Risk Score), but **neither of the two documents
carries that reconciliation, and `MODULE_TAXONOMY.md` uses the word "computations" for the 101.**

`MODULE_TAXONOMY.md` is a **production-tree manifest member** and is read by
`server/tools/test_run28_closure.py:132`, so it cannot be edited without a mint.

### CONFLICT 6.1-7 — the handoff's own T13b against the naming authority

`T6_HANDOFF.md:7882` (a heading in the historic T-numbered block):

> # T13b — THE TAXONOMY IS SETTLED AND COMMITTED. 100, not 101.

`NAMING_AUTHORITY.md:66`:

> **101 registered modules**, verified against the code and recorded in `GROUP_ASSIGNMENT.md`:

Reported with the caveat the file's own rule supplies: line 10 says "The historic T-numbered
sections below keep their names as history." Whether a heading in the history block is an
authority claim is exactly the sort of question the owner rules and this run does not.

### NIL RETURNS, HONESTLY REPORTED

I found **no** authority-against-authority conflict on: the standing description (§3 of
`NAMING_AUTHORITY.md` is quoted verbatim and identically by `README.md:8-10` and by
`test_disclaimers.py:335-342`); the ampersand rule; the em-dash rule; the Group C
non-contribution rule; the group counts A 53 / B 36 / C 7 / D 5.

---

## 4. §9.4 — EVERY §6.2 CONFLICT: AUTHORITY AGAINST CODE

### 4.0 THE ORDER'S KNOWN INSTANCE: THE PREMISE IS FALSE, ON BOTH HALVES

The order §6.2 states, "to be verified rather than assumed":

> `NAMING_AUTHORITY.md:96-97` states that module identifiers are never used in user-facing text,
> while the application renders them and the owner has ruled that acceptable.

**Established by reading the whole file and by `git log -p`. Both halves are false.**

**(a) Lines 96-97 do not state the prohibition. They state its reversal.** The full text of
lines 96-99 is quoted at conflict 6.1-1 above. `git show 2457fa1 -- NAMING_AUTHORITY.md` shows the
exact replacement made by **Run 54 phase D on 2026-08-23**:

> ```
> -**Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> -"A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.
> +**Displayed identifiers are acceptable.** "Cat 4", "1.7", "PH.2" and "A4.2" may appear in
> +user-facing text. The owner ruled the former prohibition SUPERSEDED on 2026-08-23, …
> ```

**(b) The application does not currently render them.** `REPORT_2026-08-22_run51_delivery.md:652`
records Run 51's measured guarantee 1 on the rendered DOM of six participant pages and the
deep-dive surface, SVG text nodes and accessible names included: **"8,031 strings read, 0
candidate hits, 0 survivors … NOT MET for three runs; MET now."** `NAMING_AUTHORITY.md:101-105`
says so in terms: "**This ruling does not change one word of rendered text.**"

**How established, and its limit:** by **reading**, not by execution. Re-measuring would need
`server/tools/drive_run51_browser.py` or `server/tools/run52_rendered_text_capture.py`, both of
which drive a real browser against a served application; no rendered-text capture artefact is
committed (`git ls-files | grep -i rendered_text` returns only the tool). **I therefore report
the rendering half as ESTABLISHED BY READING A PRIOR MEASUREMENT, not re-measured this run.**

**So the conflict as the order states it does not stand.** Run 56 reported it as standing; on the
evidence above it did not stand at that time either, since Run 54 had already superseded it on
2026-08-23. **That is itself a finding, and it is reported as one.**

**But a stale restatement of the superseded rule survives, in six documents and five code files.**
Inside `NAMING_AUTHORITY.md` itself it is conflict 6.3-1; in the other documents, conflicts
6.1-1 through 6.1-4; in code, conflicts 6.2-1 and 6.2-2 below.

### CONFLICT 6.2-1 — production code cites the section that reversed the rule as the source of the rule

**The document's claim.** `NAMING_AUTHORITY.md` section 4 is lines 64–110, and lines 96-99 within
it declare the identifier prohibition SUPERSEDED (quoted in full above).

**The code that contradicts it.** `server/app/simulation/portfolio_health.py:97`:

> `#: NAMING_AUTHORITY section 4 governs this sentence: no module id and no module number appears`

**Section 4 is precisely where the prohibition was removed.** The citation now points at its own
reversal.

**How established:** by **reading** both files, and by `git show 2457fa1` for the date on which
section 4 changed.

### CONFLICT 6.2-2 — production code cites "rule 6" of the naming authority, and rule 6 still says the superseded thing

**The code.** `server/app/research_export.py:182`:

> `# NAMING_AUTHORITY.md rule 6 ("never a module id or number in user-facing text") — this sheet`

**The document.** `NAMING_AUTHORITY.md:144`, the sixth-from-last bullet of `## 6. Standing rules`:

> - No module ids or numbers in user-facing text.

The code's citation is **accurate to the document**. The document is what is wrong (conflict
6.3-1). It is reported here because it shows the surviving line 144 is not inert text: **live
production code is written against it.**

Three further code sites cite the same superseded rule without a line number:
`server/app/document_evidence.py:52` ("NAMING_AUTHORITY: no module ids, no numbers, no \"Cat N\"."),
`server/app/evm_consistency.py:44`, and `assets/js/decision-ui.js:47-49` ("the analytical layer's
ids (A1.1, B4.4) must **never** appear in participant-facing text"). All are comments, none is an
executable check.

**How established:** by **reading** each file at the line named.

### CONFLICT 6.2-3 — `MODULE_RETIREMENT_DECISIONS.md` says the *registered* count fell to 63; the code says it did not

**The document's claim.** `MODULE_RETIREMENT_DECISIONS.md:17`:

> | Retirement of 38 modules, registry 101 -> 63 | `b37f133` |

and `MODULE_RETIREMENT_DECISIONS.md:82-83`:

> 38 modules. Registered count falls from 101 to 63 (Group A 53 -> 44, B 36 -> 12, C 7 -> 7,
> D 5 -> 0).

**The code that contradicts it.** Executed from `server/`:

```
python3 -c "from app.simulation import registry as R; print(len(R.registry_index()), len(R.service_index()), len(R.retired_modules()))"
→ 101 63 38
```

and by group: `registry_index()` → `{'A': 53, 'B': 36, 'C': 7, 'D': 5}`; `service_index()` →
`{'A': 44, 'B': 12, 'C': 7}`.

**The registered count did not fall. It is still 101.** What is 63 is `service_index()`. The
group-by-group figures the document gives (53→44, 36→12, 7→7, 5→0) are **exactly right** — it is
the word "Registered" that is wrong.

**How established: BY EXECUTION.**

### CONFLICT 6.2-4 — `MODULE_RETIREMENT_DECISIONS.md` describes a file that no longer exists as live

**The document's claim.** `MODULE_RETIREMENT_DECISIONS.md:622-624`:

> `assets/js/deepdive.js:2373` tells a participant that Portfolio Health "needs at least 3 projects";
> … verified, then reverted: `deepdive.js` is one of the six `SEQUENCE_BEARING_FILES`, and every

**The code that contradicts it.** `ls assets/js/deepdive.js` → "No such file or directory";
`git ls-files | grep deepdive` returns nothing. Run 54 phase B deleted it, as
`NAMING_AUTHORITY.md:120-122` records.

**Nuance, so the finding is not overstated:** the constant `participant_packages.py:972-976`
`SEQUENCE_BEARING_FILES` **does** still list six names including `assets/js/deepdive.js`; the
current operative constant is `SEQUENCE_BEARING_FILES_FROM_V21` at lines 707-710, which lists
**five** and does not. So "six `SEQUENCE_BEARING_FILES`" is true of a historical constant while
the file it names is gone from the tree.

**How established: BY EXECUTION** (`ls`, `git ls-files`) and by reading `participant_packages.py`.

### CONFLICT 6.2-5 — two more documents cite `deepdive.js` as live

**`BACKEND_CHANGES_NEEDED.md:251`:**

> render client-side under the new numbering (`simulations.js`, `deepdive.js`,

**`p0-baseline/contracts/INVENTORY_FINDINGS.md:56`:**

> `deepdive.js:2330` consumes `LinStore.getPortfolioHealth()`, so the Health dialog is calling an

Both name a file that does not exist. **`INVENTORY_FINDINGS.md` is a member of
`code_audit/run57_production_tree.sha256`**, so correcting it is a mint, not an edit.

**How established: BY EXECUTION** (`ls`), and by `awk '{print $2}' code_audit/run57_production_tree.sha256 | grep '\.md$'` for the manifest membership.

### CONFLICT 6.2-6 — the handoff's live "WHAT THE OWNER MUST DECIDE" list states two things the code has since made false

**The document's claim.** `T6_HANDOFF.md:203-211`:

> ## WHAT THE OWNER MUST DECIDE
>
> 1. **Two controls still clear stored signals on the detail page.** Leave both; **MERGE** them
>    (give one the union of the two handler bodies, the only removal that loses nothing, then
>    remove the other); or relabel one. Merging is real work on a handler and was not ordered.
> 2. **`.detail-reset` asks nothing** while `.pe-reset` beside it now does. Extend the same
>    confirmation to it?
> 3. **The freeze gate's four release pins need deriving, not hand-editing.** Three sat stale for
>    five runs and passed the whole time.

**The code that contradicts it.** `grep -rn "detail-reset" assets/ index.html` returns **only
comments recording its removal** — `assets/js/detail.js:1061-1067` ("`.detail-reset` … AND ITS
aria-live SPAN ARE REMOVED") and `assets/js/ingest.js:402-411`. There is no `.detail-reset`
element, handler or CSS rule. Item 3 was actioned by Run 57
(`T6_HANDOFF.md:40-49`: the four pins "are now computed from `participant_packages.CURRENT`").

**The mitigating fact, stated so the finding is honest:** these lines sit inside the dated section
`# 2026-08-22 - Run 56: …` (line 113), which the file's own rule at line 10 preserves as history.
**But the heading says "WHAT THE OWNER MUST DECIDE", the file carries no marker closing it, and a
session scanning for open decisions would find it.** Whether an open-decision list inside a
history section is history is the owner's call.

**How established: BY EXECUTION** (grep over `assets/` and `index.html`) plus reading.

### CONFLICT 6.2-7 — the handoff's stamp line numbers have drifted

`T6_HANDOFF.md:935-936` and `T6_HANDOFF.md:13369-13370` both state the stamp is at
`server/app/simulation/models.py:475`. It is at **line 718**
(`sed -n '718p' server/app/simulation/models.py` → `SIMULATION_VERSION = "sim-2026.08-v38"`).

Reported at low confidence as a conflict, because **both passages are correct in their essential
claim** — they exist precisely to correct prompts that cite `server/app/models.py`, which does
exist but does not hold the stamp — and both sit in dated historical sections where line 475 was
right at the time. **The directory half is right; only the line number has drifted.**

**How established: BY EXECUTION** (`sed -n '718p'`, `ls server/app/models.py`).

### NIL RETURNS, HONESTLY REPORTED

Checked and **found NOT to conflict**, so reported as clean rather than padded into the list:

- `NAMING_AUTHORITY.md:116-122` — "`sim.js`, `simulations.js` and `categories.js` load on NO route
  this service serves … Run 54 deleted `research/deepdive.html`". **True.** `grep -n` on
  `index.html` returns one hit, and it is the comment at line 1289 recording their removal;
  `ls research/deepdive.html` → not found; `ls tests.html tools/export_lib.html` → both present,
  exactly as the passage says.
- `GROUP_ASSIGNMENT.md:3` "100 computations" — **true against the code.**
  `len(VALIDATED)` = 95 and `len(PORTFOLIO_VALIDATED)` = 5, and
  `server/tools/test_group_assignment.py:44-45` pins `EXPECTED_TOTAL = 100` with
  `EXCLUDED_ID = "A4.1"`. My first reading of `len(VALIDATED)` = 95 looked like a conflict; it is
  not, and it is reported here rather than left out.
- `NAMING_AUTHORITY.md:68-73` group counts A 53 / B 36 / C 7 / D 5 — **exactly the code's**
  `registry_index()` by group.
- `NAMING_AUTHORITY.md:83-86` — `A4.1` absent from `VALIDATED`: confirmed by execution, `False`.
- `remediation_programme.md:248` on `window.confirm` — consistent with
  `T6_HANDOFF.md:108`, which records `assets/js/ingest.js:590` still gating on it. **No document
  in this repository instructs the use of `window.confirm`**; every mention records that it
  returns false here. Checked because the brief flagged it.
- `DISCLAIMERS_DRAFT.md` against `index.html` — asserted live by `server/tools/test_disclaimers.py`,
  which passed in the 15307/15307 run.
- **No document was found describing Run 57's superseded shapes** (typed release pins, a
  `CANDIDATE` the mint does not check, two reset controls) **as current, other than conflict
  6.2-6.**

---

## 5. §9.5 — EVERY §6.3 CONFLICT: AUTHORITY AGAINST ITSELF

### CONFLICT 6.3-1 — `NAMING_AUTHORITY.md` supersedes a rule in §4 and restates it unchanged in §6

**This is the live core of the whole audit.**

`NAMING_AUTHORITY.md:96-99`, in `## 4. The analytical taxonomy`:

> **Displayed identifiers are acceptable.** "Cat 4", "1.7", "PH.2" and "A4.2" may appear in
> user-facing text. The owner ruled the former prohibition SUPERSEDED on 2026-08-23, and Run 54
> records the ruling here so that this file and the handoff agree. Groups and purposes remain the
> better default where the identifier adds nothing, but an identifier is no longer a defect.

`NAMING_AUTHORITY.md:144`, in `## 6. Standing rules`, **48 lines later in the same file**:

> - No module ids or numbers in user-facing text.

`git show 2457fa1 -- NAMING_AUTHORITY.md` shows Run 54 phase D rewrote lines 93-105 and **touched
nothing below line 110.** Line 144 was left standing. Line 107 of the same file says which
neighbouring rules survive —

> **The dash rules and the ampersand rule below are NOT superseded and STAND.**

— naming the dash and ampersand rules and **not** the identifier rule, which is consistent with
the intent to supersede it and inconsistent with line 144 remaining.

**`server/app/research_export.py:182` calls line 144 "rule 6" and is written against it** (conflict
6.2-2), so this is not a dead line.

**Run 54's inventory missed it.** Its commit message enumerates six quoting sites, all outside this
file; it did not re-read its own §6.

### CONFLICT 6.3-2 — `T6_HANDOFF.md`: Run 46 and Run 47 sit at the bottom, against the file's own rule (THE KNOWN INSTANCE — CONFIRMED, AND LEFT)

**The rule**, `T6_HANDOFF.md:6-10`:

> **SECTION NUMBERING IS RETIRED, from 2026-08-02.** Five sessions collided on T-numbers in one
> day (T21 taken twice, T23 renumbered from T21, T24 taken twice, T26 renumbered from T24 at
> merge time). New sections are headed **`# <yyyy-mm-dd> — <task name>`** and appended at the TOP,
> newest first. Never renumber an existing section; on a merge conflict keep both sections whole.
> The historic T-numbered sections below keep their names as history.

**The content the rule forbids.** `grep -n "^#" T6_HANDOFF.md` places the last two entries at the
very bottom of a 13,619-line file:

> `13533:## Run 46 — the CPI trace (2026-08-22, report-only)`
> `13558:## Run 47 — the EVM consistency check, gated and merged (2026-08-22)`

**Two separate breaches, not one.** They are at the **bottom** rather than the top, and they are
`##` rather than the mandated `#` — so they do not appear in the file's own top-level section list
at all. Run 47's entry ends at line 13619, the last line of the file.

**Verified still holding. NOT MOVED, and deliberately** — Runs 48 through 57 each left it, and
moving it rewrites history.

### CONFLICT 6.3-3 — `T6_HANDOFF.md`: nineteen dated sections sit below the historic T-numbered block

The rule at line 10 preserves "the historic T-numbered sections **below**". They are at lines
7809–8543. But **nineteen dated `# 2026-…` and `# Run …` sections sit BELOW them**, at lines
9405 through 13558 — Runs 1 to 13, 21, 22, 27, 28, 29, 42, 43D, 46 and 47, dated 2026-08-10
through 2026-08-22. Under the file's own rule every one of these should be **above** the T-block.

**Reported as structure, not proposed for repair** — repairing it moves history.

### CONFLICT 6.3-4 — `T6_HANDOFF.md`: "READ FIRST" is at line 8005

> `8005:# READ FIRST — check the browser pane before planning any visual work`

A section headed READ FIRST sits 8,005 lines into the file, below 7,900 lines of newer material
and inside the historic block. It cannot be read first by anyone reading top to bottom.

### CONFLICT 6.3-5 — `T6_HANDOFF.md`: "newest first" is not date-monotonic

The top six `#` sections are, in file order: Run 57 (2026-08-24), Run 56 (2026-08-22), Run 55
(2026-08-22), Run 54 (**2026-08-23**), Run 52 (**2026-08-23**), Run 51 (2026-08-22). The ordering
is by **run number**, not by the date the heading carries, so a reader taking "newest first"
literally reads two 08-23 sections below two 08-22 sections.

**Reported as an ambiguity in the rule as much as a breach of it.** Which of the two orderings the
rule means is not determinable from the text, and I do not guess.

### CONFLICT 6.3-6 — `MODULE_RETIREMENT_DECISIONS.md` contradicts itself on registered vs in service

`MODULE_RETIREMENT_DECISIONS.md:82-83`:

> 38 modules. Registered count falls from 101 to 63 (Group A 53 -> 44, B 36 -> 12, C 7 -> 7,
> D 5 -> 0).

`MODULE_RETIREMENT_DECISIONS.md:584`, in the same document:

> `service_index()`, and the populations derived from them. Registry 101, in service 63, both derived.

**Line 584 is right and lines 17 and 83 are wrong**, and the code agrees with line 584 (conflict
6.2-3). The distinction the document itself draws at line 584 is the one lines 17 and 83 collapse.

### CONFLICT 6.3-7 — `WORKER_BRIEF.md` names PCEIF as controlling and PCEIF as retired

`server/tools/run17/categories/WORKER_BRIEF.md:4-5`:

> ## THE CONTROLLING AUTHORITY
> `/home/user/LinPRojectRadar/research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md`

`server/tools/run17/categories/WORKER_BRIEF.md:121`:

> PCEIF and PDAF are retired as product names.

Reported at low confidence, because "retired as **product names**" may be intended to leave a
filename untouched. **Not determinable from the text alone; the owner rules.**

### NIL RETURN

`DISCLAIMERS_DRAFT.md` is **not** a §6.3 conflict despite its filename: lines 3-5 state that the
word "draft" is historical and the content is "APPROVED AND LIVE". The file resolves its own
apparent contradiction in its first paragraph.

---

## 6. §9.6 — THE DEPENDENCY TABLE: WHAT DEPENDS ON WHAT

Path references were swept **uncapped** across the whole tree with
`grep -rl --exclude-dir=.git`. "Guards that assert its content" was established separately, by
finding every `.md` opened for reading inside a `test_*.py`:
`grep -rn 'read_text' --include=test_*.py server/tools/ server/tests/ | grep '\.md'`.

| Authority document | Suites that read it | Guards that **assert its content** (load-bearing) | Manifest membership | Told to read it first? |
|---|---|---|---|---|
| `NAMING_AUTHORITY.md` | 6 test files + 9 non-test `.py` + 5 `.js` + 46 `.md` | **YES — `server/tools/test_disclaimers.py:335-342`** parses the `**Short form, one sentence:**` blockquote out of this file and asserts `index.html`'s meta description equals it **verbatim**. `test_disclaimers.py` also quotes §2's "deliberately no framework name" and §4's ampersand rule. Editing §3 turns a live check **red**; deleting §3's heading makes the parse fail with `short is None` and the check **red**, not vacuous. | **None.** Named in `test_run38_frozen_immutability.py:532`'s PERMITTED_MODIFICATIONS list, i.e. a run **may** modify it. | **YES, twice.** `T6_HANDOFF.md:1-4` ("READ `NAMING_AUTHORITY.md` BEFORE ANY CONTENT WORK … Read it before this handoff, not after") and `README.md:12-14`. |
| `GROUP_ASSIGNMENT.md` | `test_group_assignment.py`, `test_run26_counts_and_wiring.py`, 6 `.py`, 2 `.js`, 17 `.md` | **YES, the most load-bearing in the repository.** `test_group_assignment.py:42,63-68` parses the fenced ```` ```group-assignment ```` block; **`raise SystemExit("FATAL: no ```group-assignment block")` if it is absent** — so merging this file away aborts a suite outright. `EXPECTED_COUNTS = {"A":52,"B":36,"C":7,"D":5}`, `EXPECTED_TOTAL = 100`. `test_run26_counts_and_wiring.py:256` asserts Group C's non-contribution "because GROUP_ASSIGNMENT.md positively denies that dependency". | None. | `NAMING_AUTHORITY.md:66` points at it as the record of the taxonomy. |
| `DISCLAIMERS_DRAFT.md` | `test_disclaimers.py`, `test_export_workbook.py`, 3 `.py`, 2 `.js`, 10 `.md` | **YES.** `test_disclaimers.py:32` sets `SOURCE = ROOT / "DISCLAIMERS_DRAFT.md"` and extracts the §1/§2 blockquotes, failing if `index.html` diverges **by a single character**; `test_export_workbook.py:287` reads it too. The file says so itself at lines 11-14. | None. | The file itself: "**Edit here first.**" |
| `T6_HANDOFF.md` | 6 test files, 14 `.py`, 79 `.md` | **YES, two.** `test_run32_qualifier_count_closure.py:148-150` reads it and requires the string `expected 30`; `test_run35_closure_voter_identities.py:344-348` requires `DECLARED_STRUCTURE_UNCONSUMED_AND_REACHABLE_PARAMETER_UNRESOLVED` **and** `costDriverDistributions` to be present. **Any consolidation that dropped those strings turns two checks red.** | None. Named in `test_run38_frozen_immutability.py`'s PERMITTED_MODIFICATIONS. | It instructs itself to be read second, after `NAMING_AUTHORITY.md`. |
| `MODULE_RETIREMENT_DECISIONS.md` | **0 test files.** 1 `.py`, 3 `.md` | **NO.** Nothing asserts its content. | None. | No. |
| `FIELD_CLASSIFICATION_DECISIONS.md` | **0 test files.** 3 `.md` | **NO.** Its ruling is implemented in `server/app/field_registry.py`, which is asserted at import; the document itself is not read. | None. | No. |
| `COPY_GLOSSARY.md` | **0 test files.** 3 `.md`, 1 other | **NO.** Its companion tool `tools/copy_inventory.py` exists but does not read it. | None. | No. |
| `remediation_programme.md` | 7 test files, 10 `.py`, 2 `.js`, 7 `.md` | **Not established.** The seven suites (`test_run1_disable_and_relabel.py`, `test_run2_fifteen_defects.py`, `test_run3_adapter.py`, `test_run4_validate_seven.py`, `test_run5_export.py`, `test_d1_module_inputs.py`, `test_training_detail.py`) **name it in prose**; none appears in the `read_text` sweep, so none parses it. | None. | No. |
| `remediation_decisions_answered.md` | 11 `.py`, 3 `.js`, 7 `.md` — all by name | **NO** (not in the `read_text` sweep). | None. | No. |
| `README.md` | 6 `.py`, 14 `.md` — many of these match other `README.md` files | **NO.** | None. | No, but it points at `NAMING_AUTHORITY.md`. |
| `training_us_contract_regimes.md` | `test_training_regimes.py`, `test_training_loop.py`, 4 `.py`, 6 `.md` | **Not established** — named, not parsed. | None. | No. |
| `training_mode_roadmap.md` | **0.** 2 `.md` | **NO.** | None. | No. |
| `training_pmp_upgrade_roadmap.md` | **0.** 3 `.md` | **NO.** | None. | No. |
| `BACKEND_CHANGES_NEEDED.md` | **0 `.py`.** 1 `.js`, 2 `.md` | **NO.** | None. | No. |
| `SECURITY_SCAN.md` | **ZERO, everywhere.** See §8. | **NO.** | None. | No. |
| `p0-baseline/MODULE_TAXONOMY.md` | `test_run28_closure.py` | **YES.** `test_run28_closure.py:132` does `(ROOT/"p0-baseline"/"MODULE_TAXONOMY.md").read_text()`. | **PRODUCTION TREE** (`code_audit/run57_production_tree.sha256`, 242 members). **Cannot be moved without a mint.** | No. |
| `p0-baseline/contracts/INVENTORY_FINDINGS.md` | 0 | **NO.** | **PRODUCTION TREE.** **Cannot be moved without a mint.** | No. |
| `p0-baseline/reconciliation/README.md` | 0 | **NO.** | **PRODUCTION TREE.** | No. |
| `server/app/simulation/VALIDATION.md` | 0 in the `read_text` sweep | **NO.** | **PRODUCTION TREE.** | No. |
| `assets/vendor/ASSETS.md` | 0 in the `read_text` sweep | **NO.** | **PRODUCTION TREE *and* PARTICIPANT PACKAGE** (`code_audit/run57_participant_package_v23_checksums.sha256`, 69 members). **The only `.md` in the participant package.** Moving it changes the package identity. | No. |
| `research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md` | **13 Python files** | **YES.** `test_run22_production_tree_completeness.py:283` reads its `.metadata.json` sidecar and pins its sha256 (`328b5013…`). `server/tools/production_tree.py:103-106` declares it CONTROLLING. | **AUTHORITY TREE** (`code_audit/run51_authority_tree.sha256`, 9 members, manifest sha256 `b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a8170704dc1596` — **verified this run by `sha256sum`, unmoved for four runs**). | **YES** — `WORKER_BRIEF.md:8` orders it read "IN FULL, BEFORE OPENING ANY PRODUCTION FILE." |
| `research/methodology/run34_portfolio_calibration_protocol.md` | `server/tests/test_run34_holdout_provenance.py`, `test_run34_fault_campaign.py` | **YES.** `test_run34_holdout_provenance.py:43` reads it; `:129` asserts its **first commit** via `git_first_commit`, so its history is pinned as well as its content. | **AUTHORITY TREE.** | No. |
| `research/methodology/run35_empirical_validation_protocol.md` | via `test_run35_validation_governance.py` | Named, not parsed in the sweep. | **AUTHORITY TREE.** | No. |
| `research/methodology/run38_research_data_contract.md`, `run38_frozen_analysis_dataset_contract.md`, `run39_dataset_classification_contract.md` | referenced by the Run 38/39 tools | Named, not parsed in the sweep. | **AUTHORITY TREE.** | No. |
| `research/study_execution/STUDY_ADMINISTRATION_RUNBOOK.md` | `test_run39_launch_gate.py` | **YES.** `test_run39_launch_gate.py:784` reads it. | None. | No. |
| `research/study_execution/` — the other four | 0 in the sweep | **NO.** | None. | No. |
| `server/tools/run17/categories/WORKER_BRIEF.md` | 0 | **NO.** | None. | It **is** a "read this first" instruction, for a Run-19 worker. |
| `apps_script/*` (4), `tools/contract-fixtures/README.md`, `server/README.md`, `backend/README.md` | 0 in the sweep | **NO.** | None. | No. |

**`test_suite_identity` holds no markdown at all.** Verified by loading
`research/freeze/run57_freeze_candidate_identity.json` and filtering every group's `members` for
`.md`: **zero across all eleven groups**, and `test_suite_identity` reports `files: 203`,
matching §1.

### The blunt answer §7 asks for

- **Six guards quote content and would go red or abort on a merge:** `NAMING_AUTHORITY.md`,
  `GROUP_ASSIGNMENT.md` (aborts with `SystemExit`), `DISCLAIMERS_DRAFT.md`, `T6_HANDOFF.md` (two
  string assertions), `p0-baseline/MODULE_TAXONOMY.md`,
  `research/methodology/run34_portfolio_calibration_protocol.md`, plus the PCEIF specification via
  its sha-pinned sidecar and `STUDY_ADMINISTRATION_RUNBOOK.md`.
- **Five markdown files are inside a manifest and cannot be moved without a mint:**
  `assets/vendor/ASSETS.md` (two manifests), `p0-baseline/MODULE_TAXONOMY.md`,
  `p0-baseline/contracts/INVENTORY_FINDINGS.md`, `p0-baseline/reconciliation/README.md`,
  `server/app/simulation/VALIDATION.md` — plus the six `research/methodology/*.md` in the
  authority tree.
- **Nine authority documents nothing reads at all:** `MODULE_RETIREMENT_DECISIONS.md`,
  `FIELD_CLASSIFICATION_DECISIONS.md`, `COPY_GLOSSARY.md`, `BACKEND_CHANGES_NEEDED.md`,
  `SECURITY_SCAN.md`, `training_mode_roadmap.md`, `training_pmp_upgrade_roadmap.md`,
  `WORKER_BRIEF.md`, and four of the five `research/study_execution/` files. **These are a
  different problem from the first group and are named as such.**

---

## 7. §9.7 — THE REPORTS ARE EVIDENCE, AND NONE IS PROPOSED FOR MERGING

**Stated for the record so a later run cannot mistake it.**

**207 of the 254 markdown documents are evidence**: the 154 root `REPORT_*.md`, the 11
`code_audit/REPORT_*.md`, the 15 `research/freeze/*.md`, the 24 fixture records under
`research_fixtures/`, and the individually-classified `SECURITY_SCAN.md`,
`p0-baseline/contracts/INVENTORY_FINDINGS.md`, `backend/README.md`, the four `code_audit/GROUP_*.md`,
`code_audit/SHARED_MACHINERY.md`, `code_audit/RUN20_HANDOFF_AFTER_CYCLE6.md`,
`code_audit/run12_release_freeze.md` and `code_audit/run45_field_classification_proposal.md`.

**NOT ONE of them is proposed for merging, consolidation, deletion or correction by this run.**
This run proposes nothing at all.

Each `REPORT_*.md` records what was true at a specific stamp and was the basis on which that mint
was accepted. The freeze gate's six `predecessor_release_preserved` rows — verified green this run
for v25, v26, v27, v28, v30 and v31 — depend on sealed records staying sealed. **Consolidating
them would destroy the record of what each mint was accepted on.**

`research/freeze/RUN55_SUCCESSOR_FREEZE_REPORT.md` ships headed `# Run-52 successor freeze report`
for `sim-2026.08-v35`. **This is ALREADY KNOWN and DELIBERATELY UNREWRITTEN** — Run 56 recorded it
(`T6_HANDOFF.md:199-201`) and Run 57 confirmed it. It is that release's evidence. Rediscovered by
this run's sweep and reported here as known, not as new.

### THE FINDING OF THE FIRST ORDER §8 DEMANDS BE REPORTED PROMINENTLY

**AN EVIDENCE DOCUMENT IS BEING READ AS AN AUTHORITY BY FOUR LIVE SUITES.**

`REPORT_2026-08-18_run34-portfolio-health-calibration.md` — a `REPORT_*.md`, evidence by the
order's own §8 definition — is opened and parsed by four members of `test_suite_identity`:

| Suite | Line | What it does with the report |
|---|---|---|
| `server/tests/test_run34_parameter_count_closure.py` | 42, **223-234** | `_text = REPORT.read_text()`, then **"AND THE REPORT'S DISTRIBUTION EQUALS THE ARTIFACT'S, class for class"** — the report's published distribution is asserted equal to `code_audit/run34_portfolio_parameter_provenance.csv`. |
| | **279-302** | `git_show(...)` reads the report **out of the merged commit** and asserts the distribution already agreed there. |
| `server/tests/test_run34_holdout_provenance.py` | 42 | Reads the same report. |
| `server/tests/test_run34_count_fault_campaign.py` | 50, **186** | Uses the report as a **fault-injection target**: `fault(5, "the Run-34 report", "REPORT_2026-08-18_run34-portfolio-health-calibration.md", …)` — it mutates the report to prove the guard above can go red. |
| `server/tests/test_run34_provenance_fault_campaign.py` | 45 | Same report named as a target. |

**Consequence, stated without recommendation:** this one evidence document is load-bearing in
exactly the way §7 warns about. Editing, merging or consolidating it turns
`test_run34_parameter_count_closure.py` red; the commit-history assertion at line 279 means even
a *correct* edit cannot make it green again without touching git history. `code_audit/GROUP_A_project-health.md`
is a second, milder case (`test_run5_export.py:89`).

---

## 8. §9.8 — DOCUMENTS CLASSIFIED DEAD, WITH THE GREP

**NONE.**

The order's DEAD test has three conjunctive conditions: nothing reads it, nothing depends on it,
**and** it describes something that no longer exists. **No document in this repository meets all
three**, and I decline to classify anything DEAD on two out of three.

The one document that meets the first two:

```
$ grep -rn "SECURITY_SCAN" --exclude-dir=.git . | grep -v "^./SECURITY_SCAN.md"
$ echo $?
1
```

**Zero references, anywhere in the tree, of any kind.** `SECURITY_SCAN.md` is completely unread.

**But its third condition fails.** It describes `backend/main.py`, which still exists:
`ls backend/main.py` → present; `grep -c "@app.post" backend/main.py` → **13**. Its CRITICAL
finding C1 ("No server-side authentication on any write endpoint") names seven of those routes.
**Classified EVIDENCE-and-UNREAD, not DEAD.** Whether the findings still stand was not tested —
that would be a security assessment, which this read-only audit was not ordered to perform, and
guessing would be a plausible reconstruction. **Reported as undetermined.**

The closest other candidates, and why each is not DEAD:

- `code_audit/RUN20_HANDOFF_AFTER_CYCLE6.md` — describes a state ("Cycles complete: 6 of 12") that
  no longer exists, but it is a handoff record of that state, i.e. evidence, and evidence is
  supposed to describe a state that no longer exists.
- `backend/README.md` — describes the superseded v9 prototype, but `backend/main.py` still exists.
- `apps_script/head/README.md` (46 bytes, "Editor HEAD snapshots land here. Empty at M0.") — the
  directory still exists and is still empty, so the statement is still true.

---

## 9. §9.9 — INCIDENTAL FINDINGS

**I1. The full suite now rewrites 26 committed artefacts, not 18.** `T6_HANDOFF.md:13601-13603`
records eighteen. `bash server/run_all_suites.sh` followed by `git status --porcelain` produced
**26** modified paths: 24 under `code_audit/`, plus `server/tools/run17/coverage.csv` — the one
the handoff singles out as being outside `code_audit/`. All 26 were restored by name with
`git checkout --`; none was committed. The handoff's count has drifted by eight.

**I2. Run 54's site inventory was incomplete, and the incompleteness is measurable.** Run 54's
commit message (`2457fa1`) states "THE SITE INVENTORY IS SMALLER THAN RUN 53 FEARED" and
enumerates **six** quoting sites. This run's sweep
(`grep -rn "module id\|module ids\|module identifier\|ids or numbers" --include=*.md .`) found the
superseded rule still restated in **five documents Run 54 did not name** — `NAMING_AUTHORITY.md`
itself at line 144, `GROUP_ASSIGNMENT.md:17-18`, `remediation_programme.md:279`,
`training_pmp_upgrade_roadmap.md:140`, `WORKER_BRIEF.md:120` — and in **five code files**:
`server/app/research_export.py:182`, `server/app/document_evidence.py:52`,
`server/app/evm_consistency.py:44`, `server/app/simulation/portfolio_health.py:97`,
`assets/js/decision-ui.js:47-49`. Run 54's claim that "NOT ONE of them asserts the superseded
IDENTIFIER rule" was true of the *guard* files it read; it did not hold across the document set.

**I3. Two live authority documents rest on four source documents that are not in the repository.**
`remediation_programme.md:3-5` cites `PCEIF_Claude_Module_Arithmetic_Audit_2026-08-10.md` and
`PCEIF_Claude_Arithmetic_Status_and_Remediation_Matrix_2026-08-10.md` as the origin of its
"Verdict: 0 of 101 reviewed units approved". `remediation_decisions_answered.md:3-4` cites
`REMEDIATION_DECISIONS_ALL_RUNS.md` and `RUN1_DECISIONS_REQUIRED.md`. `git ls-files` returns
**zero matches for all four**. The basis of both documents is outside the repository and
unverifiable from inside it.

**I4. `code_audit/run45_field_classification_proposal.md:11-14` is the model for how a superseded
quotation should be handled**, and it is the *only* place in the repository where it was done:

> ```
> <!-- RUN 54, PHASE D: the sentence quoted below was SUPERSEDED by the owner on 2026-08-23.
>      Displayed identifiers are acceptable. This is a historical audit document and is
>      ANNOTATED rather than rewritten: it records what the authority said when the
>      proposal was written, and rewriting it would falsify that record. -->
> ```

Recorded because §9's rules forbid me proposing a structure, but not from reporting that one
already exists in the tree.

**I5. `SEQUENCE_BEARING_FILES` and `SEQUENCE_BEARING_FILES_FROM_V21` disagree in the code.**
`server/tools/participant_packages.py:972-976` lists **six** files including the deleted
`assets/js/deepdive.js`; `:707-710` lists **five** and does not. Both are live constants in one
file. This is a code-against-code observation, not a document conflict, and no run ordered its
reconciliation; it is recorded because conflict 6.2-4 turns on it.

**I6. `server/app/models.py` exists.** The repeated warning in prompts and in `T6_HANDOFF.md` is
that the stamp is not there, which is correct; but the file itself is real (`ls` confirms), so
`T6_HANDOFF.md:8516`'s "Geocoding is referenced in `app.js`, `ingest.js` and
`server/app/models.py`" is **not** a broken reference. Checked because the brief flagged the path.

**I7. `p0-baseline/module_renumbering_map.csv` is confirmed unchanged in its role.** Its
`new_id`/`old_id` columns are a renumbering pair and never cross the wire;
`test_group_assignment.py:43,84-86` reads it as one of its two independent sources of truth.
**Not a naming survivor and not a finding** — recorded so a later run does not re-raise it.

**I8. `REG.method_label(m)` returning `None` for 96 of 101 was not re-derived this run**, because
nothing in the order required asserting it. It is carried forward from prior runs unverified here
and should not be quoted from this report as verified.

---

## 10. §9.10 — THE DECISIONS THE OWNER MUST MAKE

Stated as questions with options. **No recommendation is offered on any of them, and they are
deliberately in conflict-number order rather than any order of severity.**

**D1 (conflict 6.3-1).** `NAMING_AUTHORITY.md:144` still reads "No module ids or numbers in
user-facing text" while `:96-99` of the same file declares that rule SUPERSEDED. Which is the
authority?
(a) §6 line 144 is the survivor and §4's supersession is to be narrowed; (b) §4's supersession
governs and line 144 is a leftover a later run removes; (c) both stand, meaning §4 permits and §6
discourages, and the file should say so; (d) something else.

**D2 (conflict 6.2-2).** `server/app/research_export.py:182` is production code written against
"NAMING_AUTHORITY.md rule 6". If D1 removes line 144, does that citation change, or does the
research export sheet keep the behaviour under a different reason?
(a) change the citation only; (b) change the citation and re-examine the sheet; (c) leave it.

**D3 (conflict 6.1-1).** `GROUP_ASSIGNMENT.md:17-18` bans the same four identifier strings that
`NAMING_AUTHORITY.md:96-99` permits. It is a mint-free file but its fenced block is parsed by a
suite that aborts if the block is absent.
(a) reconcile it to the 2026-08-23 ruling; (b) leave it as the stricter local rule for prose
written against the taxonomy; (c) annotate rather than rewrite, as
`code_audit/run45_field_classification_proposal.md` was.

**D4 (conflicts 6.1-2, 6.1-3, 6.1-4).** The same superseded rule survives in
`remediation_programme.md:279`, `training_pmp_upgrade_roadmap.md:140` and
`WORKER_BRIEF.md:120`. Are these three to be treated the same way as D3, or differently — noting
that `WORKER_BRIEF.md` calls itself "(binding)" and the other two are partly history?
(a) all three the same as D3; (b) each individually; (c) leave all three untouched as documents of
their date.

**D5 (conflict 6.2-1).** `server/app/simulation/portfolio_health.py:97` cites
"NAMING_AUTHORITY section 4" as the source of a prohibition that section 4 removed.
(a) re-point the comment at whatever survives D1; (b) delete the citation and state the reason
directly; (c) leave it.

**D6 (conflict 6.1-5).** `research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md`
is CONTROLLING per `production_tree.py:103-106` and per `WORKER_BRIEF.md:4-7`, while
`NAMING_AUTHORITY.md:10-13` says PCEIF is retired and "do not reason from the framing they carry".
(a) the specification's CONTROLLING status is unaffected because the retirement is of product
names only, and `NAMING_AUTHORITY.md:22` should say so explicitly; (b) the specification is
demoted from CONTROLLING; (c) the specification is renamed — **noting that it is pinned by sha256
in `code_audit/run51_authority_tree.sha256` and read by 13 Python files, so a rename is a mint**;
(d) leave both as they are.

**D7 (conflict 6.1-6).** `GROUP_ASSIGNMENT.md:3` says "100 computations"; `p0-baseline/MODULE_TAXONOMY.md:1`
says "101 distinct computations". Both call themselves a source of truth. `MODULE_TAXONOMY.md` is
a production-tree manifest member.
(a) carry `NAMING_AUTHORITY.md:75-86`'s reconciliation into one or both — **a mint if
`MODULE_TAXONOMY.md` moves**; (b) declare one of the two the authority on the count and the other
silent on it; (c) leave both.

**D8 (conflict 6.1-7).** Is a claim inside `T6_HANDOFF.md`'s historic T-numbered block (here
T13b's "100, not 101") an authority claim or history?
(a) history, and the block should carry a banner saying so; (b) authority, and it must be
reconciled; (c) undetermined, and the handoff should be split.

**D9 (conflict 6.2-3, 6.3-6).** `MODULE_RETIREMENT_DECISIONS.md` lines 17 and 83 say the
*registered* count fell from 101 to 63; line 584 of the same file and the executed code both say
registered stayed 101 and *in service* is 63.
(a) correct lines 17 and 83; (b) annotate them; (c) leave the record as the run wrote it. **Note:
nothing reads this document, so no check moves either way.**

**D10 (conflicts 6.2-4, 6.2-5).** Three documents cite `assets/js/deepdive.js`, deleted by Run 54:
`MODULE_RETIREMENT_DECISIONS.md:622-624`, `BACKEND_CHANGES_NEEDED.md:251`, and
`p0-baseline/contracts/INVENTORY_FINDINGS.md:56`. **The third is a production-tree manifest member,
so touching it is a mint.**
(a) annotate all three; (b) annotate the two free ones and leave the manifest member; (c) leave
all three; (d) correct all three at the next mint.

**D11 (conflict 6.2-6).** `T6_HANDOFF.md:203-211` is headed "WHAT THE OWNER MUST DECIDE" and its
items 1, 2 and 3 were resolved by Run 57, but nothing in the file marks them closed.
(a) later "WHAT THE OWNER MUST DECIDE" lists carry a closure marker written by the next run;
(b) the top banner gains a line saying only the newest such list is open; (c) each superseded list
is struck through in place — **noting that two live checks assert specific strings inside this
file, so any structural edit must preserve them**; (d) leave it, on the ground that a dated
section is history.

**D12 (conflicts 6.3-2 through 6.3-5).** `T6_HANDOFF.md` breaks its own line 6-10 rule in four
distinct ways: Run 46 and Run 47 at the bottom and using `##` (the known instance, left again this
run); nineteen dated sections below the historic block; a "READ FIRST" section at line 8005; and
an ordering that is by run number rather than by date.
(a) leave every one of them, as Runs 48–57 did, because moving them rewrites history; (b) fix only
the heading level of Run 46 and 47 so they appear in the file's own section list, without moving
them; (c) restate the rule at lines 6-10 to describe what the file actually does; (d) something
else.

**D13 (§7, first-order finding).** `REPORT_2026-08-18_run34-portfolio-health-calibration.md` is
evidence that four live suites read as an authority, one of which reads it **out of a git commit**.
Is that intended?
(a) yes — evidence may be load-bearing and this is the record working as designed; (b) no — the
assertions should move to a non-report artefact; (c) yes, but the report should carry a banner
saying it is guard-read and must not be edited.

**D14 (§8).** `SECURITY_SCAN.md` has zero references anywhere in the tree, and its subject
`backend/main.py` still exists with 13 unauthenticated-looking POST routes.
(a) commission a run to re-test whether its findings still stand; (b) mark it superseded because
`backend/` carries no traffic; (c) leave it.

**D15 (incidental I1).** The full suite rewrites 26 committed artefacts, not the 18
`T6_HANDOFF.md:13601` records.
(a) correct the handoff's count; (b) commission a run to stop the suites writing into the tree;
(c) leave it as a documented ritual.

**D16 (incidental I3).** `remediation_programme.md` and `remediation_decisions_answered.md` rest on
four source documents absent from the repository.
(a) bring the four in; (b) record in both documents that the sources are external and
unverifiable; (c) leave it.

---

## 11. STOP CONDITIONS

**Stop condition 1 (resolving a conflict would be required to answer a question) — NOT TRIGGERED,
but observed once.** Classifying `T6_HANDOFF.md` required knowing whether its historic block is
authority or history, which is conflict 6.3-3 / decision D8. **I classified the file MIXED and
reported the conflict rather than resolving it**, which is what the rule requires.

**Stop condition 2 (a file other than the report would have to change) — TRIGGERED, repeatedly,
and obeyed every time.** Sixteen distinct items would have been one-line corrections:
`NAMING_AUTHORITY.md:144`, `GROUP_ASSIGNMENT.md:17-18`, `remediation_programme.md:279`,
`training_pmp_upgrade_roadmap.md:140`, `WORKER_BRIEF.md:120`,
`MODULE_RETIREMENT_DECISIONS.md:17,83,622-624`, `BACKEND_CHANGES_NEEDED.md:251`,
`INVENTORY_FINDINGS.md:56`, `T6_HANDOFF.md:203-211,936,13370`,
`portfolio_health.py:97`, `research_export.py:182`, `decision-ui.js:47-49`. **Not one was
touched.** The 26 suite-rewritten artefacts were restored to their committed bytes, not edited.

**Stop condition 3 (a classification cannot be made honestly) — TRIGGERED THREE TIMES, and each is
reported as undetermined rather than reconstructed:**

- **U1.** `BACKEND_CHANGES_NEEDED.md` — I could not determine whether any of its items is still
  wanted. It specifies Apps Script `Code.gs` work for a backend the repository has since replaced,
  but the items are written as outstanding and nothing marks them abandoned. Classified **MIXED**;
  whether it is entirely history is **not determinable** from the tree.
- **U2.** `WORKER_BRIEF.md:121` "PCEIF and PDAF are retired as **product names**" against its own
  line 5 naming a PCEIF file as CONTROLLING — **not determinable** whether the word "product" was
  chosen to exempt filenames or is a coincidence. Reported at conflict 6.3-7 with that caveat.
- **U3.** `SECURITY_SCAN.md`'s findings — **not determinable** whether they still stand without a
  security assessment this run was not ordered to perform.

Two further things are reported as read-established rather than execution-established, and are
labelled as such above: the "0 identifiers rendered" measurement (§4.0(b), from Run 51's browser
campaign, not re-run) and `REG.method_label` (incidental I8, not re-derived).

---

## 12. WHAT THIS RUN DID NOT DO

No merge. No consolidation. No deletion. No correction. **No mint. No fault campaign.** No branch
merged to `main`. No `git add -A` and no `git add .`. No `DATABASE_URL` was set at any point. No
file outside the repository root was moved or deleted. Nothing outside
`REPORT_2026-08-25_run58_document_conflict_audit.md` was committed.

**No resolution is recommended for any of the twenty-one conflicts (seven under 6.1, seven under 6.2, seven under 6.3). No merge structure is proposed.
The conflicts are not ranked. They are numbered so the owner can rule on each one.**
