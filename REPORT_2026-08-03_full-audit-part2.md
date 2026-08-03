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

---

# Section 6: user-facing strings against NAMING_AUTHORITY.md

Method: the application was driven signed-in with a real computed project, and the **visible text
of each surface** was extracted from the DOM by tree-walking text nodes and discarding anything
whose parent is not rendered. That is stronger than grepping source, because it only sees what a
user sees. Source greps were used afterwards to locate what the probe found and to reach strings
the probe could not render.

## 6.1 A retired framework name reaches a user-obtainable file (probed)

`buildAuditRecord()` in `assets/js/decision.js:422` returns, as its **first key**:

```json
{ "pceif_version": "L2-v0.5-demo", "data_boundary": "...", ... }
```

`decision.js` **is** loaded on the participant-facing page, and the button that downloads this
is rendered. Verified by calling the real render path against the real project fetched from
`?action=get`:

```
renderDecisionCard(project, host) -> exportButtonRendered: true, label: "Export audit JSON"
```

The card renders "Governance decision / Recommended action / Green / Authority ...", and
`app.js:1704` wires that button to serialise the record above to
`audit_<project>_<period>.json`. So a retired name, and a version string for a retired framework,
leave the platform inside a file the user keeps.

This is the only place a retired name was found in anything a user can see or obtain. Everything
else matching `PCEIF`/`PDAF` is a code comment or an internal identifier (`PCEIF_STATUS_HEX`,
`PCEIF_VERSION`), which `NAMING_AUTHORITY.md` §2 explicitly permits: *"Internal file prefix
`PCEIF_*` on development-era artifacts. Nobody sees these. Leave them."*

## 6.2 Ampersands in the taxonomy names, on the Signals tab (probed)

`GROUP_ASSIGNMENT.md`: *"Write 'and', not an ampersand. The code constants spell two of these
names with '&'. User facing text says 'Recommendation and Governance' and 'Data and Evidence
Health'. Do not rename the code constants to match."*

The code constants are being rendered directly. Probed on the Signals tab of a computed project:

```
Cost & EVM Performance · System Dynamics & Complexity · Recommendation & Governance
Regulatory & Authority Thresholds · Data & Evidence Health
```

Source: `assets/js/taxonomy.js:30` (`window.LIN_CATEGORIES`), which **is** loaded on the
participant route. `assets/js/categories.js` carries the same strings but is not loaded, so
taxonomy.js is the live one. Two of these are the exact two names the authority calls out by
name; three more follow the same pattern.

## 6.3 Em dashes

**Rendered, on the portfolio (probed):**

```
Portfolio too small for anomaly detection — need at least 3 projects with signal data
```

Its source is `server/app/simulation/portfolio.py:58`, **inside `server/app/simulation/`**, which
this and other sessions are forbidden to modify. Worth flagging: this one cannot be corrected
under the standing permissions without an explicit exception.

**In source (source-read):** 111 em dashes inside quoted string literals across 17 files,
comments excluded:

```
signals.js 21 · detail.js 17 · auditor.js 12 · admin.js 11 · admin-ops.js 8 · deepdive.js 6
workspace.js 6 · app.js 5 · decision-ui.js 5 · export.js 4 · charts3d.js 3 · forcenet.js 3
projectnet2d.js 3 · atlas.js 2 · neural_flow.js 2 · ingest.js 1 · store.js 1 · index.html 1
```

Samples that are unambiguously user-facing (all render in the admin Create-user dialog, seen in
the section 1 walkthrough):

```
admin.js:178  '<option value="Participant">Participant — research subject</option>'
admin.js:179  '<option value="ResearchAdmin">Admin — manages users, membership, export</option>'
admin.js:60   'again — write it down or copy it now.</p>'
admin.js:71   "Copy failed — select the field and copy manually"
```

**This count is a lower bound and is not comparable to the handoff's figure of 84.** My method
counts single- and double-quoted literals only, so it misses template literals entirely, and it
does not attempt to separate user-facing strings from internal ones. The handoff's 84 counted
"prose em dashes" on a named set of files. Notably `assistant.js`, which the handoff lists at 7,
returns zero under my method — that is likelier to be template literals than a fix, and I did not
establish which.

## 6.4 The Fairbanks label and the `plain` key diverge in front of the user (probed)

The rename was deliberately label-only. It shows:

```
themeset {theme: "fairbanks"}
  -> "unknown theme: fairbanks; recognized themes are plain, light, newyork, maria"
themeget
  -> themes: ["plain", "light", "newyork", "maria"]
```

A user who types the only name the interface has ever shown them is told it is not recognised,
and offered four names **none of which appears anywhere in the interface** (the switcher shows
Fairbanks, Miami, NYC, Maria). Source: `server/app/theme.py:38` `THEMES` and `:155` the refusal
message, which interpolates the key tuple directly.

Where the divergence exists, by location:

| Location | Value | User-visible |
|---|---|---|
| `assets/js/app.js:2067` `THEME_META` | `key:"plain"`, `label:"Fairbanks"` | label only |
| `server/app/theme.py:38` `THEMES` | `"plain"` | **yes**, via `themeget`/`themeset` |
| `server/app/theme.py:155` refusal text | `', '.join(THEMES)` | **yes** |
| `assets/css/radar.css` | `body[data-theme="plain"]`, 10 selectors | no |
| `participants.theme` stored value | `"plain"` | no |
| `server/tools/test_theme_plain.py` | filename | no |
| `REPORT_2026-08-02_light-theme.md`, `server/app/theme.py` docstring | "the plain theme" | no |

## 6.5 Same class, worth recording: internal keys shown as text

Not a NAMING_AUTHORITY rule, but the same defect shape as 6.4. The upload panel reports document
types by their internal snake_case keys (probed):

```
1 document(s) present for period 1. Still expected: contract_value, pay_application, schedule_update
```

and the Document library lists `monthly_report` as the document's type.

## 6.6 What is clean, verified

- **No retired name in any rendered text**, on portfolio, project detail/Signals, Files, Period
  documents, Document library, Period decision, Handbook, Technical Auditor, Administration.
- **No module id or number in any rendered text** on those surfaces. Searched for `Cat N`,
  `A4.2`-style ids, and `PH.N`; zero hits.
- **The standing description is quoted verbatim**, not paraphrased, in three places in
  `index.html`: the short form in prose, the long form's opening, and the `<meta name=
  "description">` tag, which matches the short form character for character.
- **The "browser computes nothing" claim holds.** `sim.js`, `simulations.js`, `categories.js` and
  `deepdive.js` are **not** among the 31 scripts `index.html` loads.
- **Handbook "framework" mentions are correct**: they state there is deliberately no named
  framework, which is what the authority prescribes.
- **Files tab, Period documents, Document library, Period decision and the mobile desktop-only
  notices are clean** of retired names, module ids and em dashes. The three mobile notices read
  "This needs a desktop browser. Open Opus Gubernatio on a laptop or desktop to use it." and the
  administration variant.

## 6.7 Flagged, not asserted as violations

- **"From multi-model signals to a governed decision"** (`index.html:472`, the portfolio H1). One
  AI model exists. But in project controls "multi-model" most naturally denotes multiple
  forecasting models, and the analytical layer genuinely runs many (Monte Carlo, Bayesian,
  parametric, reference-class, PERT). Defensible on that reading; recorded because it is the kind
  of phrase the authority asks be checked, and it is the most prominent line on the platform.
- **Arora template folder names contain "&"** (`3_DESIGN/2_CODE & STANDARDS`). These are verbatim
  transcriptions of an external source document, deliberately preserved including its own
  inconsistencies. The ampersand rule in `GROUP_ASSIGNMENT.md` is about the taxonomy group names,
  not transcribed folder names. Not treated as a violation.

## 6.8 Not swept

The assistant's replies, the decision sequence while in flight (its controls are hidden without
an assignment), the consent screen (all bracketed placeholders, correctly labelled DRAFT), the
expert surface, the knowledge library's body content, error and refusal strings other than the
theme one probed above, and the export workbook's own cell text.

---

# Section 7: deferred items, open or not

## The six named in the brief

### 7.1 The label-only Fairbanks rename — STILL OPEN, and it is visible

Covered in 6.4 with probed evidence. The divergence is not merely internal: `themeset` refuses
the name the interface shows and offers four key names it never shows. Seven locations tabulated
in 6.4.

### 7.2 The CSV export notice — STILL OPEN

`research_export.py:1075`: `notice_in_payload = (record.format or "json") != "csv"`. JSON and
XLSX carry the approved notice (XLSX as its own Notice sheet); **CSV carries none**, and the
response says so honestly rather than pretending otherwise. The open question is what a CSV
should do, since it has no natural place for a notice block. Recorded at handoff line 810 as
Lin's, and unchanged.

Related and also still open (handoff line 2102): the sign-in page's attribution and copyright
lines are shorter forms that do not match section 3 of `DISCLAIMERS_DRAFT.md`. Neither was part
of the approval, so neither was changed.

### 7.3 The percent scale contract, 0..1 versus 0..100 — STILL OPEN

Handoff line 585: *"NO percent upper bounds: the 0..1-vs-0..100 scale question is unresolved and
was not guessed at."* Still true. `field_registry`'s range contract makes numeric fields
non-negative with a named signed set, and deliberately sets **no upper bound** on percentages, so
a value of `52.5` and a value of `0.525` are both accepted for `actualPctComplete` and nothing
distinguishes them. Observed in this session's own fixture: the stub emits
`actual_percent_complete: 52.5`, i.e. the 0..100 reading, but that is a fixture convention, not
an enforced contract.

### 7.4 JS-built surfaces never verified under the light theme — NOW LARGELY CLOSED, with one new finding

The theme session recorded: *"Project detail, administration, the Files tab, the assistant and
the knowledge pages were NOT verified by computed style."* **Verified this session** (executed,
transitions suppressed, `data-theme="plain"`, contrast computed against each element's resolved
background):

| Surface | Elements sampled | Worst contrast | Verdict |
|---|---|---|---|
| Signals (project detail) | 94 | **5.78** | passes AA |
| Files tab | 25 | **5.28** | passes AA |
| Assistant panel | 12 | **5.28** | passes AA |
| Administration | 93 | **3.71** | **below AA 4.5** |

The administration failure is specific and reproducible: `.admin-pill.admin-pill-on` (the
"Active" account-status pill), `color: rgb(18,112,58)` on `rgba(46,230,107,0.15)`, 11px, ratio
**3.71**. It is a status pill on the account table, so it carries meaning, and 11px text below AA
is the combination the theme's own contrast guarantee exists to prevent. It sits outside the ten
tokens that guarantee measures (see 5.1), which is how it survived.

The knowledge pages were not reached and remain unverified.

### 7.5 The favicon — CLOSED BY DECISION, not open

Handoff line 458: *"The favicon cannot be animated and was left alone. It is browser tab chrome;
the only way would be swapping `href` on a timer, which is an animation library by another
name."* That is a decision with a stated reason, not an outstanding task. Nothing to carry.

### 7.6 The deploy-before-migration window — STILL OPEN, unchanged and untouched

A push deploys immediately; migrations are applied by hand afterwards. This took sign-in down on
2026-08-02 when code expecting `participants.theme` deployed before the column existed.

What exists today: `/readyz` reports schema-at-head and answers 503 when the schema is behind
(verified this session — it reported `"schema at head 0017_participant_theme"`). What does not
exist: any gate. There is **no `.github/workflows/` directory**, so nothing blocks a deploy on
migrations, and nothing alerts on the 503. The signal exists and is still unwatched, which is
exactly what the outage report called the second finding. The 2026-08-03 session's own fixes were
deliberately migration-free for this reason.

## 7.7 The stuck instance — the brief misidentifies it

The brief names **AUD-P-002**. Queried directly in the audit database:

```
AUD-P-001  scenario AUDIT-S1  evidence NULL              locked=1  revealed=0   <- STUCK
AUD-P-002  scenario AUDIT-S2  evidence PRJ-91ZWNKZVSY    locked=1  revealed=1   <- completed
```

**The stuck instance is AUD-P-001**, whose scenario had no evidence. AUD-P-002 completed the
sequence normally. Both live only in a throwaway audit database in the scratchpad, not in the
repository and not in production. Nothing was altered. Whether production holds an equivalent is
**unknown and unknowable from here**: production was not inspected. Since 2026-08-03 the
condition that creates one is refused at both scenario creation and assignment, so no new one can
be made this way.

## 7.8 Other deferred items found, with status

| Item | Recorded | Status today |
|---|---|---|
| Migration 0013 applied to production | Lin's | **Unknown from here.** Production not inspected. Head is now 0017; whether production is at head is not establishable locally |
| Production `docRiskScore` range query before the first real run | Lin's | **Still open.** Nothing locally out of range; production deliberately not queried |
| General shape of `w_overwritesignal` | Deferred | **Partly resolved.** The field NAME is now validated against `field_registry.ALL_SI_FIELDS` (probed in section 3 of part 1: `Unknown signal field: 'nonsense_field'`). The **value** is still unvalidated beyond the `docRiskScore` range and the malformed-numeric guard. Per-field contracts still need Lin |
| Step 6, real extraction against a real document | Lin's, blocked | **Still blocked.** Needs a real document and a live `ANTHROPIC_API_KEY` together; `render.yaml` marks the key `sync: false` so it exists only in the Render dashboard |
| Person-level intake fields not exported | Lin's | **Still open.** `experience_level`, `industry`, `certifications`, `organizational_role`, `risk_attitude`, raw intake/debrief responses stored, unexported |
| Individual submittals: register-with-nulls or UNMAPPED | Lin's | **Resolved as UNMAPPED.** Verified in part 1 section 5 of the fixes report: `rfi`/`rfa`/`submittal` absent from `DOC_TYPES`, the logs/registers present |
| D2 malformed numerics before the observation store | Deferred | **Resolved.** The parser guard landed and `test_malformed_numerics` passes 46/46 |
| ~40 hardcoded shadows and scrims | Open | **Largely resolved.** Now **8** black scrim/shadow literals in `radar.css` (`rgba(0,0,0,…)` ×6, `#000` ×2), not ~40 |
| `.theme-switch` dead code | Open | **Still open.** 8 occurrences remain in `radar.css`; zero in `index.html` and `app.js`, so it is still dead |
| "Framework" in the "Methods and Framework" tab label | Lin's | **Still open.** Present at `index.html:839` |
| Branch `t15-local-unpushed`, `unported_modules()` correction | Open | **Resolved on main.** `server/app/simulation/registry.py:50` carries the Group D subtraction and its rationale |
| Green project status with a Red contributing category (A3, conflict 0.94) | Raised 2026-08-03 | **Still open and undiagnosed.** Not investigated this session |
| Finding 5, the withdrawn scenario UI | Owner deciding | **Still open by design.** Explicitly out of scope for this and the previous session |

---

# What could not be established, and what remains unaudited

- **Whether production is at schema head, holds a stuck instance, or holds an out-of-range
  `docRiskScore`.** Production was never inspected or queried, by instruction. Every statement
  about production in this report is explicitly an unknown.
- **Whether the Postgres trigger bodies work.** Every local run is SQLite. `0003` and `0009` each
  carry a separate `PG_*` body that no local check exercises, and section 5.3 shows a fault in one
  of them is invisible locally. These are the bodies that will run in production.
- **Whether `assistant.js` still carries the 7 em dashes the handoff records.** My counting method
  does not read template literals, and it returned zero for that file.
- **End-to-end click of "Export audit JSON".** The button was confirmed to render and
  `buildAuditRecord()` was confirmed to return `pceif_version` first, both against the live page;
  the download itself was not triggered.
- **Fourteen suites were not fault-injected at all** (listed in 5.8), and within the seventeen
  that were, only one or two guarantees each.
- **Unaudited surfaces**: the knowledge library body, the expert surface, the assistant's replies,
  the decision sequence in flight, the consent screen beyond confirming it is placeholder text,
  and the export workbook's cell text.

The working tree is clean at the end of this audit and the full server suite is **1649/1649
across 30 suites**, `tests.html` 51/51, matching the state at the start.
