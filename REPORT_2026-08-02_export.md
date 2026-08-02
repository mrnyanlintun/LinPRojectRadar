# The export: two kinds, and the workbook

**Server 1517/1517 across 28 suites, `tests_render.html` 49/49, `tests.html` 51/51, green on
merged `main`.** Both admin controls (kind selector, conditional banner, xlsx create/fetch)
driven end to end in a real browser and confirmed by DOM read. Seven faults injected for the
new suite, every one detected with a distinct signature, every one reverted byte-identical,
baseline re-run after every single fault.

---

# Part 2. What the platform stores, before any field set was built

Grouped by level, as asked, so it can be struck against the analysis plan directly. **Stored**
means a real column; **derived** means computed at export time from stored data; **exported
before** means it was already in `EXPORT_COLUMNS` prior to this task; **new** means this task
added it to a sheet; **available** means stored but this task did not surface it anywhere —
your call, not assumed.

## Person level — collected once at enrolment

| Field | Stored / derived | Status |
|---|---|---|
| `pseudonymous_code` | stored (`participants`) | exported before |
| `order_group` | stored | exported before |
| `role`, `account_type` | stored | available (not exported — both are platform-internal, not a study variable) |
| `eligibility_status`, `scenario_set`, `condition_sequence` | stored | available |
| `completion_status` | stored | available (see note below: nothing currently transitions it) |
| `current_stage` | **derived**, live, from the decisions/assignments state machine | available; never stored, so it can only ever be as-of-export-time, not historical |
| `experience_level`, `years_experience`, `industry`, `certifications`, `organizational_role` | stored (`participant_profiles`, narrow columns) | `years_experience` is **new**, in `analysis_long`. The rest are **available**, not yet exported anywhere |
| `ai_familiarity` | stored (`participant_profiles`, Likert 1-5, stored as text) | **new**, in `analysis_long`, coerced to a float |
| `risk_attitude` | stored, JSONB, multiple named items (the scale is still being selected with the committee) | available |
| `demand_effect_items` | stored, JSONB | available |
| `intake_responses` (raw, every item, lossless) | stored, JSONB | available — this is the definition-agnostic record; the narrow columns above are an analyst convenience copied from it |
| `intake_captured_at`, `debrief_responses`, `debrief_captured_at` | stored | available |

## Instance level — per participant per project period: what was shown, what was decided

Everything in the existing 39-column `EXPORT_COLUMNS` (design: `scenario_id`, `scenario_version`,
`sequence_number`, `period`, `config_code`; preliminary: `pre_action`, `pre_confidence`,
`pre_assessment`, `pre_submitted_at`, `pre_locked_at`; reveal: `reveal_at`, `package_id`,
`package_version`, `package_hash`; final: `final_action`, `disposition`, `final_confidence`,
`final_submitted_at`, `escalation_level`, `owner_role`, `authority_role`,
`resource_constraint`, `evidence_items`, `reason_code`, `deadline`, `rationale`,
`residual_risk`; transition: `branch_id`, `branch_version`, `transition_seed`,
`transition_probability`, `next_state_id`, `transition_displayed_at`; derived:
`judgment_shift_action`, `confidence_shift`, `deliberation_seconds`, `pre_assessment_seconds`)
was already exported before this task, all stored on `decisions`/`transitions` except the four
named "derived."

New in this task, all **derived**, all in the Decisions sheet (Part 5 — for judging a case, not
for the model):

| Field | Derivation |
|---|---|
| `instance_id` | `decision.decision_id` — the join key across every sheet |
| `time_on_instance_seconds` | latest of (`final_submitted_at`, `reveal_at`, `pre_submitted_at`) minus the assignment's start (first `evidence_viewed` audit event) |
| `pre_committed_before_disclosure` | `pre_locked_at <= reveal_at`, or `None` before reveal. Structurally always true when both exist (a database CHECK constraint enforces it), exposed anyway as an explicit boolean so a reviewer never has to compare two timestamps by eye |
| `completion_state` | `research_decision.derive_stage(decision)` — the same stage the participant-facing UI computes, reused rather than reimplemented |
| `session_break` | **a stated heuristic**: whether a `research_login`/`sso_login` audit event falls strictly between the instance's start and its end. `None`, not `False`, while the instance has no end yet — a reviewer can tell "no break detected" from "not yet judgeable" |

`Assignment.status` is stored and is **available**, not currently exported.

## Stimulus level — per instance, identical across participants who share it

**The frozen package** (`decision_support_packages`). `package_id`, `package_version`,
`package_hash` were exported before (Decisions sheet). **New**, in the Stimulus sheet, all
**stored**, none derived — exactly the fields `decision-ui.js` renders to a participant on
reveal, nothing the analytical layer produces: `model_version`, `use_case`, `output_type`,
`data_cutoff`, `detected_condition`, `alternatives`, `uncertainty`, `limitations`,
`applicability_boundary`, `expiration_trigger`, `provenance`, `recommended_action`,
`frozen_at`. (`config_id`, `provider_id`, `approval_status` are stored and **available**, not
exported — internal to package management, not part of what a participant saw.)

**Module results** (`computed_results`). Nothing from this table was in any prior export. New
in this task, in the Module results sheet: `project`, `period`, `computed_at`, `computation`
(module name), `group` (group name — never the id or number, per `NAMING_AUTHORITY.md`),
`status_color`, `evidence_metric`, and `result_json` (everything else the module returned,
serialised, since module-specific fields vary by computation and enumerating every one by name
would mean maintaining ~100 column lists). `signal_inputs`, `category_statuses`,
`project_status`, `portfolio_snapshot`, `source_documents` and `simulation_version`/`seed` are
stored on `computed_results` and are **available**, not exported — they describe the whole
project/period, not one computation, and would need a different sheet shape (one row per
project-period, not per computation) to carry sensibly.

## The third join: scenario-domain familiarity, per participant per project

**Established, not assumed: it is not stored anywhere.** `ai_familiarity` on
`participant_profiles` is person-level and general ("familiar with AI-based decision support
tools"), not scenario-specific. `research_expert.py`'s `realism_review` is the EXPERT panel's
judgement of whether a scenario is plausible, not a participant's own familiarity with the
domain. Neither `intake.json` nor `debrief.json` (the only two questionnaire definitions in the
repository) contains an item asking a participant how familiar they are with a specific
scenario's domain. No column on `assignments` or `decisions` carries it either. If this
variable is wanted, it does not exist to export yet; it would need a new instrument item, most
naturally per-scenario at the point evidence is first shown, alongside (or as part of) a
comprehension check — which the analysis plan already calls for and which also does not exist
yet.

## The expert reference standard

`expert_references` exists as a table (categorical `preferred_action`,
`acceptable_alternatives`, `unsupported_actions`, `rationale`, `confidence`,
`realism_review`) — built for the panel, T6 — but **there is no numeric rubric score column
anywhere in the schema.** The six-dimension continuous composite the analysis plan specifies
(action appropriateness, correct interpretation, uncertainty recognition, dominant-risk
identification, response proportionality, written-justification quality, 0-4 each, summed to
0-24) has never been implemented as a stored field. `analysis_long.expert_reference_score` is
therefore reserved and always empty by construction — see Part 4 below for why that is the
correct posture rather than a defect to fix now.

---

# Part 1. The selector

**Established, not assumed: the two kinds have genuinely different scopes, and the platform's
own existing reasoning for participant_inputs already argued the case for project_health.**

`participant_inputs` stays exactly what the export was before this task: per participant,
filtered to research accounts unconditionally (`_eligible_instances`'s `account_type !=
"research"` guard, unchanged), a date window over `final_submitted_at` — a decision belongs to
the window it was **completed** in, not started in, so a participant who paused across the
boundary is not split across two exports.

`project_health` is new: per project, reading `computed_results` directly. **The date window
there is over `computed_at`, not any decision timestamp — stated on the surface, not left for
the user to guess** (`date_window_field` in every response; the "From"/"To" labels in the UI
change text when the kind changes). A reporting period is an integer, not a range a date window
can bound; `computed_at` is the one real timestamp this scope has.

**The banner is now conditional, not a standing claim.** `research_account_filtered(kind)`
returns `True` only for `participant_inputs`. `ComputedResult` belongs to a project, and a
project carries no `account_type` of its own — an operational project's real (non-synthetic)
analytical results are exactly as reachable through `project_health` as a research project's.
Verified directly: the test fixture seeds an operational-only project with no research
participant anywhere near it, and its result appears in the `project_health` workbook.

**The Notice text follows the same reasoning, and it is the same decision the codebase already
makes everywhere else it switches text on account type — not a new judgement call invented for
this task.** `participant_inputs` carries the research variant verbatim (true: everything in it
is synthetic, research-account data). `project_health` carries the **operational** variant
verbatim — the one that makes no "all synthetic" claim — because that scope can genuinely
include real operational project data. Both are quoted whole from `DISCLAIMERS_DRAFT.md`;
neither is shortened or composed. `test_disclaimers.py`'s existing check that asserted
`research_export.py` must NOT carry the operational variant was updated to assert the opposite,
with the reasoning recorded in the check itself — the premise that justified the old assertion
(only one scope ever existed) no longer holds.

---

# Part 3 and 4. The workbook

One XLSX workbook per kind, sheets named explicitly (never relying on position):

- **`participant_inputs`**: Notice, Decisions, Stimulus, Module results, analysis_long.
- **`project_health`**: Notice, Module results. No Decisions/Stimulus/analysis_long — there is
  no participant dimension in this scope, and inventing placeholder participant rows would
  misrepresent what this kind reports.

**Notice** is the approved text, verbatim, appended first so it is the sheet that opens.
**Decisions** is one row per participant per instance, the full 44-column allowlist (the
original 39 plus the five identity/judgement additions above). **Stimulus** is one row per
instance, the frozen package as disclosed, labelled by its own column names (`data_cutoff`,
`frozen_at`, `reveal_at`) as what was shown and when. **Module results** is one row per
project, period and computation, referred to by name and group — never id or number.
**analysis_long** is Part 4: long format, one row per participant per instance per `post_ai`
level (0 preliminary, 1 final), **always exactly two rows per instance**, verified directly
against an instance whose final decision does not exist yet (the second row still exists, with
null action/confidence/timestamp — Part 5's "do not filter" rule applied literally). Columns:
`participant_id`, `instance_id`, `post_ai`, `action`, `confidence`, `scenario`, `project`,
`period`, `years_experience`, `ai_familiarity`, `timestamp`, `expert_reference_score` (always
empty — see Part 2). No free-text column exists in this list; verified that none of
`FREE_TEXT_COLUMNS` intersects it, and that no participant-authored string (a rationale
containing a name) reaches it.

**Module results is scoped differently per kind.** For `participant_inputs` it is restricted to
the projects the eligible instances' scenarios actually point at (`scenario.evidence_package_id`)
— the analytical record behind what those participants were shown, carried alongside their
decisions. For `project_health` it is every live (`superseded_by IS NULL`) result, bounded only
by the date window.

## Two things established, not assumed

**Whether adding sheets breaks earlier checksums: yes, exactly as the earlier notice work found,
and handled the same way.** `a_adminexportfetch` re-derives the payload and, on a mismatch,
checks a second time against the `include_notice=False` serialisation (now covering xlsx too —
`build_workbook(..., include_notice=False)` drops the Notice sheet and reproduces the pre-notice
sheet set). A record that matches the legacy serialisation is reported `predates_notice: true`
and still served with the current sheets; a record that matches neither is a real mismatch and
is still refused. Verified directly, including for xlsx.

**Whether openpyxl output is byte-deterministic: measured, and it is not, without work.**
Two workbooks built from identical rows a second apart differ byte-for-byte: `docProps/core.xml`
stamps `created`/`modified` at the wall clock, and — this is the part setting
`workbook.properties` alone does not fix — every zip entry's own timestamp is stamped at the
wall clock too. `_normalize_xlsx_bytes` rewrites the archive with every entry's timestamp pinned
to a fixed constant, the `docProps/core.xml` timestamps textually pinned to the same value, and
entries reordered by name so write order cannot introduce a difference either. Verified: two
independent builds of identical data, a second apart, now produce byte-identical output —
proven directly (`test_export_workbook.py` Part 6), not assumed from reading the library's
documentation.

**Whether the export can be produced before the reference standard exists: yes, trivially — the
column is never read from `expert_references` at all.** `expert_reference_score` is a literal
`None` written into every row by construction; nothing queries the expert table for it. The
column exists now so a later implementation does not change every earlier export's shape.

**What a row looks like when a participant has consented but decided nothing: there is no
row, for that instance, in any sheet — because there is no instance yet.** An "instance" is
anchored on a `Decision` row, and a `Decision` row is created only when the preliminary
judgment is submitted (the INSERT that also locks it, in the same statement). A participant who
has consented, completed intake, and been assigned, but has not yet opened the evidence or
submitted a preliminary judgment, produces **zero rows**, in every sheet, and the export as a
whole is still a valid, openable file — verified directly (fixture participant WB-B; the
five-sheet, header-only, zero-data-row file for an out-of-range window; both proven by opening
the file with `openpyxl.load_workbook` and reading it back, not only asserted against the code
that wrote it).

---

# Part 5. Fields for judgement

Added to Decisions: `time_on_instance_seconds`, `pre_committed_before_disclosure`,
`completion_state`, `session_break` — see Part 2 above for each one's derivation.

**Nothing is filtered, excluded, or cleaned.** Verified directly: the abandoned mid-instance
fixture (preliminary judgment submitted, never revealed, never decided) appears in Decisions
with `completion_state` reflecting exactly that state, and in analysis_long with its post_ai=1
row present and null rather than omitted. The participant who never started appears nowhere,
which is not a filter — there is nothing to represent.

---

# Verification

- Server suites: 1470 baseline → **1517/1517 across 28 suites**, fresh migrated sqlite per
  suite, `PYTHONIOENCODING=utf-8`. New suite `test_export_workbook.py`, 47 checks. Existing
  `test_export.py` (77 checks) passes **completely unmodified** — `build_rows`,
  `EXPORT_COLUMNS`, `serialise` all keep their names and default behaviour, proving the
  extension is additive. `test_disclaimers.py` updated (146→147) to assert the new, deliberate
  two-variant reality instead of the old single-variant one, with the reasoning for the change
  recorded in the check itself.
- `tests_render.html` 49/49, `tests.html` 51/51, unaffected.
- **Both admin controls driven end to end in a real browser**: signed in through the real login
  form, navigated via the real Admin nav and the real "Monitoring and export" tab, read the
  banner and window-label text change live when the kind selector changes, created a real xlsx
  export through the real button, fetched and verified it through the real "Fetch & verify"
  button, and read "Checksum verified" and the correct conditional scope sentence back from the
  DOM.
- **The produced workbook was opened and read back** with `openpyxl.load_workbook`, not only
  asserted against the code that wrote it: sheet names, header rows, cell values, merged-cell
  ranges, and leading-row emptiness were all read from the actual file bytes.
- **Seven faults injected, all confirmed applied (anchor must match exactly once), all
  detected, all reverted byte-identical, baseline re-run green after every single fault:**

| Fault | Result |
|---|---|
| analysis_long stops emitting the post_ai=1 row for an incomplete instance | 43/47 |
| `rationale` (free text) added to the long sheet's column list | 4/8 (crashed; wrapped as red) |
| xlsx byte-normalisation removed | 46/47 |
| project_health starts filtering to research accounts | 46/47 |
| Notice sheet stops being first | 43/47 |
| project_health workbook grows a Decisions sheet | 46/47 |
| an empty-range export returns an error instead of a valid file | 36/39 |

# Files changed

- `server/alembic/versions/0015_export_kind.py` — `research_exports.kind`, NOT NULL,
  server-defaulted to `participant_inputs` (the only kind that existed before this column, so
  the default correctly describes every prior row with no backfill script).
- `server/app/research_models.py` — the `kind` column.
- `server/app/research_export.py` — the two kinds, the workbook builder, byte normalisation,
  the second notice variant, all extended without changing `build_rows`'s name, signature, or
  default behaviour.
- `server/requirements.txt` — `openpyxl==3.1.5`, pure-python, no C extension.
- `index.html`, `assets/js/admin-ops.js` — the kind selector, the conditional banner and window
  labels, xlsx as a format option, base64-decoded binary download for xlsx (the existing
  textarea display stays for json/csv).
- `server/tools/test_export_workbook.py` — new, 47 checks.
- `server/tools/test_disclaimers.py` — one check's assertion and reasoning updated to the
  two-variant reality; no wording anywhere composed or shortened.
- `server/app/simulation/` untouched; no stored data altered; production not inspected.

# Still open, flagged rather than decided

- Every field listed **available** in Part 2 is a genuine choice, not an oversight: adding it
  is a column-list edit once you tell me which ones the analysis plan needs.
- Scenario-domain familiarity and the expert reference numeric score both need new instrument
  work before they can be collected at all — this report only establishes that they are
  currently absent, per the task's instruction not to invent them.
- `Assignment.status`, `ComputedResult.signal_inputs`/`category_statuses`/`project_status`/
  `portfolio_snapshot`/`source_documents`, and the DecisionSupportPackage management fields
  (`config_id`, `provider_id`, `approval_status`) remain unexported; noted above with the reason
  each was left out of the current sheet shapes.
