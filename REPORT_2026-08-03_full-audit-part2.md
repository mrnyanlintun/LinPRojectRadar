# Full platform audit, part 2: sections 5, 6 and 7

Read-only. No code, test or data changed. `REPORT_2026-08-02_full-audit.md` covered sections 1
to 4; this finishes the audit. (The brief names `REPORT_2026-08-02_audit-fixes-1-4.md`; the file
is dated `2026-08-03`, and that is the one read.)

Method per finding is marked **executed** (ran against a live server or suite), **probed**
(driven in a browser), or **source-read**, and trusted in that order.

Every fault below was injected into the source under test, the suite re-run, and the file
restored with `git checkout --` so the restore is byte-exact by construction. The baseline was
re-run after **every** fault, and the working tree was checked for dirt after every restore. At
the end of section 5 the tree is clean at `cb230e6` and the full suite is **1649/1649 across 30
suites**, identical to the pre-audit baseline.

---

# Section 5: the suite, proven able to fail

## Lead: three checks proven vacuous, and one whole guarantee with no check at all

### 5.1 The theme contrast guarantee measures 10 named tokens and misses text tokens beside them (VACUOUS, executed)

`tools/test_theme_plain.py` opens: *"CONTRAST. Every colour is read OUT OF radar.css and the
ratio is computed here, so a comment claiming a ratio cannot make this pass."* It does compute
real ratios, but only over a hardcoded list:

```python
TEXT_TOKENS = ["text", "heading", "muted", "faint", "phosphor",
               "status-green-text", ..., "status-complete-text"]
```

`--eyebrow` is not in it, and `--eyebrow` styles text in **9 CSS rules**. Setting it to
`#d9dde3` (near-white on a white theme, far below AA) left the suite at **63/63 green**.

This is not a mis-aimed fault: the **positive control** in the same batch, `--muted` set to the
same unreadable value, was **DETECTED** (63 → 62). So the measurement machinery works and the
coverage is the gap. `--gold-text` (2 rules) and `--scope-label` are in the same position.

The guarantee as written is "every colour"; the guarantee as implemented is "these ten". A theme
token added later inherits no contrast floor and nothing says so.

### 5.2 The Arora template's verbatim folder names have no check (VACUOUS, executed)

`REPORT_2026-08-02_files-tab.md` and the handoff both make a point of this: *"Folder names are
VERBATIM including the template's own inconsistencies: `C. PHOTOS` has a period where every
other lettered folder has an underscore ... Do not tidy them."*

Renaming `C. PHOTOS` to `C_PHOTOS` in `server/app/jdrive_tree.py` left `test_files_tab.py` at
**63/63 green**.

Searching every suite for literal template names returns exactly one assertion, on the **top
level only**:

```
tools/test_files_tab.py:172   names == ["0_PROJ-MGMNT", "1_PROJ INFO", "2_DELIVERABLES",
                                        "3_DESIGN", "4_QC", "5_CONST ADMIN", "6_RECEIVED",
                                        "NEWFORMA"]
```

Every nested name is unasserted, including all three inconsistencies the design explicitly
protects (`C. PHOTOS`, `YYYY_MM_DD XX% INFO`, `1_ACTIVE CONSTR. SET`). A future session tidying
them, which is exactly what the comment anticipates, passes the suite. The tree is transcribed
from a source PDF by column position and nothing checks the transcription still matches.

### 5.3 A dual-dialect migration lets a fault apply to the file and not to the code under test (executed)

Injecting into `PG_TRIGGER` in `0009_documents_and_results.py` reported **VACUOUS** — 74/74 with
the append-only trigger apparently disabled. It was not vacuous. Local runs are SQLite, and the
migration carries two independent trigger bodies; the fault landed on the Postgres one, which no
local run executes. Re-injecting into `SQLITE_TRIGGER` was immediately **DETECTED** (74 → 72).

Recorded because it is the "injection that silently fails to apply while reporting success"
class in its most convincing disguise: the needle matched, the file changed, the suite ran, and
the result was a confident false negative. **Every migration with `PG_*` and `SQLITE_*` bodies
has this property**, and the same asymmetry means the Postgres trigger bodies — the ones that
will actually run in production — are never exercised by any local check. That is a real
coverage gap, not only a fault-injection hazard.

### 5.4 The append-only guarantee is checked, but only behind a conditional (source-read + executed)

`test_documents_b7b.py:457` Guarantee 8 is real and, once aimed correctly, detects a disabled
trigger. But the whole block is gated:

```python
if decision_ok:
    check(db_refused, "database REJECTS a direct UPDATE of a referenced result", detail)
    ...
else:
    check(False, "could not seed a submitted decision referencing a result", ...)
```

The `else` is correct and turns a failed setup into a red check, which is the right pattern and
worth keeping. The point to record is the **denominator**: when the block is skipped the suite
reports a different total, and totals are quoted in the handoff as evidence of coverage. Observed
directly during this run — `test_pre_lock_guard` reported `20/20` at baseline and `8/16` under
fault, `test_export_workbook` `47/47` then `38/39`. A suite that says "39/39 checks passed" has
not necessarily run the same 47 checks it ran yesterday, and nothing surfaces the difference.

## 5.5 Crash rather than fail, printing no result line: 20 of 30 suites

`test_files_tab.py` and the render harness both wrap their body so a throw becomes a red check —
a lesson the handoff records from the Files tab session. **That fix was applied to those two and
nowhere else.** These 20 suites have no wrapper:

```
test_admin_ops_t7t8      test_assignment_blinding   test_auth_session       test_d1_module_inputs
test_decision_sequence   test_disclaimers           test_doc_risk_range     test_document_versioning
test_drive_import        test_expert_reference_t6   test_export             test_features
test_geocode_providers   test_group_assignment      test_pre_lock_guard     test_simulation
test_theme_plain         test_transitions           test_workspace_t3t5     test_writes_a1b
```

Demonstrated on five of them: faulting `resolve_caller`, `select_signal_inputs`,
`w_overwritesignal`, `a_admintransitionrulecreate` and the extraction cache each produced a
traceback and **no `RESULT:` line at all**.

**How dangerous this is, measured rather than assumed.** With `w_overwritesignal` stubbed,
`test_writes_a1b` produced:

```
EXIT CODE: 1
lines containing "RESULT:" : 0
lines containing "FAIL"    : 0
```

So a runner that checks exit codes catches it, and the full-suite runs in this and the previous
session did check exit codes. A human reading output, or any runner keying on the `RESULT:`
convention every one of these suites prints, sees nothing at all. The suite's own contract is a
result line; on a crash it does not emit one, and its checks vanish silently from any total.

## 5.6 What was proven to work

Fourteen faults, each aimed at the specific claim the check makes. **DETECTED** (baseline green,
fault red, restore green, tree clean):

| Guarantee | Suite | Baseline → fault |
|---|---|---|
| Locked pre-judgment immutable at the database | `test_pre_lock_guard` | 20/20 → 8/16 |
| Taxonomy doc matches what the server registers | `test_group_assignment` | 18/18 → 15/18 |
| Referenced computed result immutable (SQLite branch) | `test_documents_b7b` | 74/74 → 72/74 |
| Approved disclaimer wording equals what ships | `test_disclaimers` | 147/147 → 143/147 |
| xlsx normalised to be byte-deterministic | `test_export_workbook` | 47/47 → 38/39 |
| `config_id` absent from the participant projection | `test_assignment_blinding` | 50/50 → 47/50 |
| `--muted` contrast measured (control for 5.1) | `test_theme_plain` | 63/63 → 62/63 |
| PM-only write guard | `test_membership` | 46/46 → 41/46 |
| Research gate refuses before dispatch | `test_features` | 49/49 → 46/49 |
| `participant_inputs` filtered to research accounts | `test_export` | 77/77 → 75/77 |
| Observations emitted on upload | `test_storage_redesign` | 32/32 → 14/32 |
| EVM band thresholds | `tests.html` (probed) | 51/51 → 2 failed |

`tests.html` was fault-proven in the browser: moving the EVM red band from `cpi < 0.90` to
`cpi < 0.80` in `sim.js` turned "All 51 assertions passed" into "2 of 51 assertions FAILED", and
restoring returned it to 51/51.

`tests_render.html`'s over-the-wire group was fault-proven in the previous session and not
re-proven here.

## 5.7 Fixtures that build state by a route the application does not take

This was the named highest-value target. **No new instance was found beyond the two already
known** (the render harness's primed cache, fixed 2026-08-03; the files-tab stub recording,
fixed the same day). What the survey did find:

Seven suites make **zero** calls through `/exec`. Each was examined and each is defensible:

- `test_pre_lock_guard`, `test_simulation`, `test_group_assignment`, `test_geocode_providers`,
  `test_submittal_and_fairness`, `test_drive_import` test a layer below or beside the API on
  purpose. `test_pre_lock_guard` in particular tests the guarantee through three write paths
  (Core UPDATE, ORM, raw driver SQL) precisely because the point is that it holds *below* the
  application.
- `test_disclaimers` states plainly: *"Reads files only. No database, no server, no network."*
  It compares approved wording to shipped wording, which is a file-to-file question.

**One scope limitation worth recording, not a defect**: `test_disclaimers` proves the approved
text is *present in* `index.html`. It cannot prove a user is *shown* it, because it never renders
the page. A notice removed from view by CSS or JS while remaining in the markup would pass.

## 5.8 What was sampled and what was not

Sampled with an injected fault: `test_pre_lock_guard`, `test_group_assignment`,
`test_documents_b7b` (twice), `test_disclaimers` (twice), `test_theme_plain` (three times),
`test_files_tab`, `test_export_workbook`, `test_export`, `test_assignment_blinding`,
`test_membership`, `test_features`, `test_storage_redesign`, `test_auth_session`,
`test_d1_module_inputs`, `test_writes_a1b`, `test_transitions`, and `tests.html`. Nineteen faults
across 17 suites.

**Not fault-injected this session**: `test_admin_ops_t7t8`, `test_decision_sequence`,
`test_decision_ui_t4`, `test_document_versioning`, `test_doc_risk_range`, `test_drive_import`,
`test_expert_reference_t6`, `test_facade_and_user_lifecycle`, `test_geocode_providers`,
`test_malformed_numerics`, `test_research_identity`, `test_simulation`,
`test_submittal_and_fairness`, `test_workspace_t3t5`. Their checks are unproven here in either
direction; several were fault-proven in their own build sessions, per the handoff, but that is a
claim I did not re-verify.

Within a sampled suite only one or two guarantees were faulted, never all of them. A suite marked
DETECTED above has one proven check, not fifty.
