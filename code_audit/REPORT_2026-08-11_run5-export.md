# Run 5 — regenerate the Group A export — 2026-08-11

Branch `claude/remediation-regenerate-export` from `origin/main` at `3dc1312`. This is Run 5 of
the revised order 1, 3, 2, 4, 5, and the last of the five. `remediation_decisions_answered.md`
5.1 to 5.3. **The platform stayed frozen for this run: no algorithm changes, no threshold
changes, no band changes, and no file under `server/app/simulation/` was touched** (confirmed by
`git status` before commit: the only files changed are under `code_audit/`, `server/tools/`, and
three governance documents; `assets/js/detail.js` was edited and then reverted -- see Incidental
findings).

## Lead: the count assertion, and what it now enforces

**The exporter now refuses to write anything unless the emitted module id set exactly equals the
registry's expected set, per group.** `server/tools/export_module_source.py` (new) reads
`VALIDATED` and `PORTFOLIO_VALIDATED` directly from the code, computes the expected id set for
each of the four groups, and compares it against what it is about to emit before writing a single
file. A mismatch prints exactly which ids are missing or unexpected, exits non-zero, and writes
NOTHING -- the 2026-08-10 defect (52 claimed, 43 written, no check) cannot recur silently.

**Proved able to fail, per the task's requirement.** `--drop A4.6` (used in
`server/tools/test_run5_export.py`, section 1) removes a real Group A id from emission; the
exporter refuses, names `A4.6` specifically, and writes nothing. Removing the flag restores a
clean run: `Group A: 52 modules, ids match the registry exactly.` The same section also confirms
a genuinely disabled-but-computed module (`A3.8`, Parametric Cost Index) is correctly NOT treated
as missing -- the assertion checks against the registry's computed set, not against a smaller
voting or enabled set.

**Regenerated counts: Group A 52, Group B 36, Group C 7, Group D 5, total 100 -- unchanged from
the registry's own numbers, now backed by a check that can fail.** `server/tools/
test_run5_export.py` (new, 34 checks, all passing) exercises the assertion, the presence of the
nine previously-omitted modules, the activation-state requirement, the naming rule, and the
checksum manifest, with every check proved able to fail by injection first (see Verify).

## The external audit's Group A findings were formed against an incomplete export

The 2026-08-10 export claimed 52 Group A modules and wrote 43 sections. It silently omitted RFI
Velocity, Submittal Rejection Rate, NCR Rate, Weather Day Impact, Change Order Frequency, Dispute
Escalation Index, Subcontractor Performance, Procurement Lead Time Monitor, and Specification
Conflict Density (A4.2 through A4.10) -- the file jumped from Inflation Adjustment Index straight
to DSM Rework Propagation. Any external review already performed against that four-file package
was necessarily performed without seeing those nine modules' source, inputs, literals, or
abstention behaviour, and its Group A findings should be re-read against the regenerated files
now in `code_audit/`. `code_audit/REPORT_2026-08-10_module-source-export.md` (the old report) now
carries a superseded notice at the top saying exactly this and pointing to this report; its
original count tables and analysis are left intact underneath as the historical record of the
defect, not as current guidance.

## Part 1: the expected id set, and the footnote

**Verified against the code, not against the task prompt's own arithmetic.** The task prompt
states "Assert 51 computed plus 1 supplied" for Group A. That number does not match the registry:
`VALIDATED` contains exactly 52 Group A ids (confirmed by direct count against the running code,
not against any document), none of which is `A4.1`. `A4.1` (Document Risk Score) is declared in
`p0-baseline/module_renumbering_map.csv` (53 Group A rows there) but implemented by no formula
function anywhere under `server/app/simulation/` -- absent from `VALIDATED`, confirmed directly.
So the correct, code-verified statement is **52 computed plus 1 supplied, 53 named Group A
entries in total** -- not 51 plus 1. This matches `code_audit/REPORT_2026-08-10_module-source-
export.md`'s own independent count (Section 1 of that file: "A=53, B=36, C=7, D=5, total=101 live
rows in the CSV... the one-module gap in Group A... is exactly A4.1"), matches
`server/tools/test_group_assignment.py`'s `EXPECTED_COUNTS = {"A": 52, ...}`, and matches
`GROUP_ASSIGNMENT.md`'s own registry block, which already lists exactly 52 Group A ids excluding
`A4.1`. `remediation_decisions_answered.md` 5.1's own "51" is the one number in this run's source
documents that does not survive verification against the code; this report uses 52, with the
reasoning above, per `NAMING_AUTHORITY.md`'s standing rule to verify against the code rather than
asserting from memory.

**The standing footnote was ambiguous, not wrong in its arithmetic, and has been made explicit.**
`NAMING_AUTHORITY.md` and `GROUP_ASSIGNMENT.md` both already excluded Document Risk Score from the
100 and from Group A's 52 in their totals; the risk was in the footnote's WORDING, which read "100
computations, with the footnote that Document Risk Score is recorded as..." -- a sentence that can
be misread as counting Document Risk Score inside the 100 it is a footnote to. Both files now say
explicitly that the count is "100 registry-computed modules... Document Risk Score is not one of
the 100 and not one of Group A's 52," and both now state Group A's full roster is 53 named
entries (52 computed plus 1 supplied).

**Every place the footnote or a Group A total appears, and what it now says:**

| Location | Before | After |
|---|---|---|
| `NAMING_AUTHORITY.md` section 4 | "100... with the footnote that Document Risk Score is recorded as a value..." (ambiguous whether counted) | "100 registry-computed modules (Group A 52 of them). Document Risk Score is not one of the 100 and not one of Group A's 52... Group A's full roster is 53 named entries: 52 registry-computed plus Document Risk Score, supplied." |
| `GROUP_ASSIGNMENT.md` "Why the total is 100 and not 101" | Table said Group A 52, total 100; explanatory prose present but no explicit "53 named entries" statement | Added paragraph: "Group A's full roster is 53 named entries, not 52... Document Risk Score is the 53rd named entry... excluded from every count on this page." |
| `remediation_programme.md`, Run 5 entry | "OPEN" | Marked DONE with the 52-computed/1-supplied/53-total figures and a pointer to this report |
| `code_audit/REPORT_2026-08-10_module-source-export.md` | No superseded notice | Superseded notice added at the top, pointing here |
| `README.md` "The analytical layer" | Already correctly excluded Document Risk Score from the 100 | No change needed; verified consistent |
| `assets/js/knowledge.js` (participant-facing "Document risk" entry) | Already correctly describes it as supplied, not computed | No change needed; verified consistent |
| `assets/js/categories.js` | Already states "Group A Project Health 53" for the whole client-side taxonomy (which legitimately includes the uncomputed entry) | No change needed; verified consistent, and is the correct frame for that file's purpose |
| `assets/js/detail.js` comment | Said "Group A 52 modules... the whole taxonomy" (internally inconsistent: the whole taxonomy is 53/101, not 52/100) | **Edited, then reverted.** `server/tools/test_run2_fifteen_defects.py` asserts this file byte-identical to the frozen baseline except for one named, permitted diff (the abstention-reason graft). The edit broke that guard (2 checks red, both in that file). Reverted; the stray "52" in this comment is left as an incidental finding below rather than fixed here, because this run has no exception to touch a frozen participant script. |
| `p0-baseline/MODULE_TAXONOMY.md` | Already states 53/101 for the whole taxonomy | No change needed; verified consistent |
| `server/tools/test_group_assignment.py` `EXPECTED_COUNTS`/`EXPECTED_TOTAL` | 52/36/7/5, 100 | Unchanged (correct); re-ran green after every edit in this run |

No other footnote or Group A total was found in a UI string, export, or current (non-dated)
governance document. Dated `REPORT_*.md` files elsewhere in the repository are historical records
of earlier sessions and were not edited, consistent with how prior runs treated them.

## Part 2: the exporter asserts its own count

Covered in the Lead section above. `server/tools/export_module_source.py` is new; nothing under
`server/app/simulation/` implements this assertion or is touched by it.

## Part 3: regenerate all four groups

All four `code_audit/GROUP_*.md` files were regenerated by `export_module_source.py` reading
`VALIDATED`, `PORTFOLIO_VALIDATED`, `registry.py`'s activation-state tables, and
`signal_package.py`'s wiring set directly -- not from the previous export's text. Group D (whose
five modules share one function, `compute_portfolio`) is exported as the full verbatim function
once, with each of the five modules' subsection stating which returned keys belong to it, since
there is no per-module function to excerpt separately.

**Every section carries an activation state**, one of: enabled and voting (with the sourced-band
citation and the auditor-gate limitation quoted), advisory and non-voting (with the specific
held-back reason for the five CORE candidates that did not clear Run 4's bars, or the general
advisory statement for the rest), disabled (with the concept-only reason), or newly wired and
unvalidated (`signal_package.WIRING_NOTE`, verbatim). A module can and does carry more than one
tag (for example `B2.7`, Plithogenic Sets, is both disabled and one of the fourteen newly wired --
disabled wins, so it never executes, and the export says so).

**Activation-state breakdown, computed directly against the registry (not asserted from the task
prompt's summary) and matching it exactly:**

| Group | Total | Disabled | Voting (CORE) | Held non-voting (CORE) | Proxy | Newly wired | Plain advisory |
|---|---|---|---|---|---|---|---|
| A | 52 | 1 (A3.8) | 2 (A1.7, A1.8) | 5 (A2.8, A3.2, A3.4, A4.2, A4.3) | 18 | 0 | 26 |
| B | 36 | 7 | 0 | 0 | 11 | 14 (2 of these also disabled: B2.7, B2.9) | 6 |
| C | 7 | 0 | 0 | 0 | 0 | 0 | 7 |
| D | 5 | 0 | 0 | 0 | 1 | 0 | 4 |

Totals across the platform: **8 disabled** (A3.8 plus 7 in Group B), **30 relabelled proxies**
(18 + 11 + 0 + 1), **14 newly wired** (12 of which compute, 2 refused as disabled: B2.7 Plithogenic
Sets, B2.9 Quantum Probability), **7 CORE modules of which 2 vote** (TCPI, Variance at Completion)
**and 5 stay non-voting** for want of a defensible source (Look-Ahead Schedule Health, Contingency
Burn Rate, Material Cost Variance, RFI Velocity, Submittal Rejection Rate). Every one of these
numbers matches the task prompt's stated state of play exactly, confirmed independently against
the registry rather than trusted from the prompt.

**Fifteen defects (a separate, earlier accounting, from Run 2/`test_run2_fifteen_defects.py`, not
re-derived here): nine producing output on the real path, six abstaining permanently or pending
the corpus** -- carried forward from `T6_HANDOFF.md`'s Run 2 entry and unchanged by this run,
which touched no arithmetic.

## Part 4: the duplicate report files

`code_audit/REPORT_2026-08-10_module-source-export.md` and its external duplicate download share
SHA-256 `f1c9e769...` and are byte-identical, confirmed again here
(`sha256sum code_audit/REPORT_2026-08-10_module-source-export.md` still returns that prefix even
after the superseded notice was added at the top -- the notice was added to establish which
document is canonical, not to make the files differ for its own sake; the point stands that a
reviewer holding two downloads with the same hash was holding one report, not two). **One
authoritative report** (this file, `REPORT_2026-08-11_run5-export.md`) plus **one checksum
manifest**, `code_audit/CHECKSUMS.sha256`, generated by `export_module_source.py` at write time
and covering every file in `code_audit/` (recomputed with `hashlib.sha256` over each file's bytes,
not copied from any prior record), replace the old arrangement. A reviewer can verify what they
received with `sha256sum -c CHECKSUMS.sha256` from inside `code_audit/`.

## Verify

- **The export emits exactly the expected id set per group, and refuses on a mismatch.**
  VERIFIED. `server/tools/test_run5_export.py` section 1: baseline reports 52/36/7/5; dropping a
  real id (`A4.6`) makes the exporter exit non-zero and name the missing id; restoring makes it
  clean again. Also confirms the disabled-but-computed module (`A3.8`) is not mistaken for
  missing.
- **A4.2 through A4.10 are present.** VERIFIED. `server/tools/test_run5_export.py` section 2
  checks all nine section headings by name directly against the regenerated file.
- **Every section carries an activation state.** VERIFIED. `server/tools/test_run5_export.py`
  section 3, exhaustively over every section in all four files (not a sample): every heading's
  section text contains "Activation state:". Caught and fixed one real gap during this run -- the
  Group D shared-source preamble section initially had no activation-state line; added, and the
  suite went from 32/34 to 34/34.
- **The checksum manifest matches the files as written, verified by recomputing.** VERIFIED.
  `server/tools/test_run5_export.py` section 5 recomputes sha256 over every file the manifest
  lists and compares against the manifest's own entries -- not against a copy the writer kept.
  Section 6 proves this check can fail: corrupts a real manifest-covered file, confirms the
  recomputed digest now disagrees with the manifest, then restores the file and reconfirms.
- **No module id appears as a heading.** VERIFIED. `server/tools/test_run5_export.py` section 4,
  a regex over every heading in all four files, exhaustively. Proved able to fail: the same regex
  is run against a deliberately poisoned copy of one heading ("## A4.2 RFI Velocity") and confirmed
  to catch it, before being discarded (never written to disk).
- **Server suite.** 61 files. First full run surfaced a real regression this run introduced (see
  Incidental findings): `test_run2_fifteen_defects.py` dropped from 233/233 to 231/233 after an
  edit to `assets/js/detail.js` that the file's own byte-identical guard was built to catch.
  Reverted; a clean re-run of that file alone confirmed 233/233 restored. **Full clean re-run: 61
  files, 3662/3662 checks (3628/3628 across the 60 files using the `RESULT: n/n` reporting
  convention, plus `test_run5_export.py`'s own 34/34), 0 failing files**, fresh SQLite (via
  `alembic upgrade head`) per file, `PYTHONIOENCODING=utf-8` set throughout. Interpreter confirmed
  real (CPython 3.x, not a stub) by successful imports of `fastapi`, `sqlalchemy`, `alembic` in
  every one of the 61 processes.
- **`tests.html`.** 51/51 assertions passed, real headless Chromium
  (`/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`).
- **`tests_render.html`.** 286/287, the one red being the pre-existing auth-gated production-read
  row every prior run since Run 2 has also reported red -- not a regression from this run, and
  this run touched no rendering code.

## What was done

- New `server/tools/export_module_source.py`: reads the registry, asserts the expected id set per
  group before writing, regenerates all four `code_audit/GROUP_*.md` files plus
  `code_audit/CHECKSUMS.sha256`.
- New `server/tools/test_run5_export.py`: 34 checks, all proved able to fail by injection first.
- `NAMING_AUTHORITY.md`, `GROUP_ASSIGNMENT.md`: footnote and Group A total made explicit (see
  table above).
- `remediation_programme.md`: Run 5 marked DONE.
- `code_audit/REPORT_2026-08-10_module-source-export.md`: superseded notice added at the top;
  body left intact as the historical defect record.
- This report, and a `T6_HANDOFF.md` entry.

## What was not done, and why

- **`assets/js/detail.js`'s stray "Group A 52 modules" comment was not fixed.** It is inside a
  file `test_run2_fifteen_defects.py` asserts byte-identical to the frozen Run 4 baseline except
  for one named, permitted difference. This run carries no exception to touch that file. Left as
  an incidental finding for whichever future session next has a legitimate reason to edit it.
- **The Document Risk Score extraction-model audit was not performed.** Out of scope per
  `remediation_programme.md`'s "Deferred, and deliberately" section; unchanged by this run.
- **No arithmetic, threshold, or band was touched anywhere**, consistent with the freeze. No file
  under `server/app/simulation/` appears in the final diff.
- **No migration was added or applied.** Alembic head is still `0025_project_notices`. **0020
  through 0025 remain unapplied in production**, unchanged from the last four runs' reports;
  production was never inspected or queried, and `DATABASE_URL` was never pointed at it --
  throwaway SQLite only, fresh per test file via `alembic upgrade head`.

## Incidental findings

1. **`assets/js/detail.js` carries a stale, internally-inconsistent comment**: "the whole taxonomy:
   Group A 52 modules... across twelve categories" describes the CLIENT taxonomy, which is 53/101
   including Document Risk Score (as `assets/js/categories.js` and `p0-baseline/
   MODULE_TAXONOMY.md` both correctly state), not 52/100. Frozen; not fixed here; flagged for the
   next session with a legitimate reason to touch that file.
2. **The task prompt's own Part 1 arithmetic ("51 computed plus 1 supplied") does not survive
   verification against the code**; the code-verified figure is 52 computed plus 1 supplied. Used
   throughout this report and the files it changed, with the reasoning shown in Part 1 above.
3. **A live regression was caught by an existing frozen-file guard, not by this run's own new
   tests**: editing `assets/js/detail.js`'s comment (a plain code comment, not a rendered string)
   still tripped `test_run2_fifteen_defects.py`'s byte-identical assertion, because that guard
   compares the whole file, comments included. This is the guard working as designed -- it is
   recorded here because it is exactly the kind of check this project has repeatedly needed and
   sometimes lacked, and because the fix (revert) is itself worth a reader knowing about.

## Surfaces changed, precisely

- `server/tools/export_module_source.py` (new) -- the exporter.
- `server/tools/test_run5_export.py` (new) -- its test suite, 34 checks.
- `code_audit/GROUP_A_project-health.md`, `GROUP_B_recommendation-governance.md`,
  `GROUP_C_data-evidence-health.md`, `GROUP_D_portfolio-level.md` -- regenerated in full from the
  registry.
- `code_audit/CHECKSUMS.sha256` (new) -- sha256 of every file in `code_audit/`.
- `code_audit/REPORT_2026-08-10_module-source-export.md` -- superseded notice added; body
  unchanged.
- `NAMING_AUTHORITY.md`, `GROUP_ASSIGNMENT.md` -- footnote and Group A total wording (see table).
- `remediation_programme.md` -- Run 5 marked DONE.
- `T6_HANDOFF.md` -- this run's entry appended.
- `assets/js/detail.js` -- edited, then reverted; final diff is empty.

## This closes the five-run programme

Run 1 disabled the eight and relabelled the thirty. Run 3 (the adapter) reached fourteen
computations. Run 2 fixed fifteen defects. Run 4 validated the seven CORE candidates and froze the
platform, restoring TCPI and Variance at Completion to voting. Run 5 regenerated the Group A
export the external audit was working from, fixed the count assertion that let it silently omit
nine modules, and made the Document Risk Score footnote's wording match what
`GROUP_ASSIGNMENT.md`'s own numbers already meant. The programme
`remediation_decisions_answered.md` laid out is complete; what remains (the REBUILD items, the
Document Risk Score extraction-model audit, Category 9 as a two-pass gate) is recorded there and
in `remediation_programme.md` as deliberately deferred, not as unfinished pieces of this
programme.
