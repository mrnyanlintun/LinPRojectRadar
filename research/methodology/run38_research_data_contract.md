# Run 38 research data contract

**Status:** measured, not declared. Every statement below was derived from the live SQLAlchemy
models in `server/app/research_models.py`, the live `/exec` routes in
`server/app/research_decision.py`, `research_transitions.py` and `research_export.py`, and a
complete TEST_ONLY dry-run study driven through those routes by
`server/tools/test_run38_readiness.py`. Nothing here is transcribed from a methodology document.

**Frozen boundary.** Run 38 changed no scientific, participant-facing or client byte. The
measurements below describe the frozen instrument as it stands at release
`f983bb020f7a184a5742e1fff09d690b0170f0de`, freeze candidate
`6142d877856ea651ef8d7e905f6d27604b3244f1`, simulation `sim-2026.08-v25`, participant package
`og-participant-2026.08-v13`, synthetic package `OG-SYNTH-0.6`.

---

## 1. The measurement record

The single research observation is a row of `decisions`. Its identity is
`(assignment_id, period)`, where `assignment` is `(participant, scenario)`. A scenario is one
controlled project; `period` is `P1`..`P6`. That makes the natural analytical grain

> **one row per participant × project × period**

and the dry run confirmed it mechanically: one participant who completed the study produced
exactly 36 rows with 36 distinct `(participant, scenario, period)` keys and zero duplicates.

**A caveat that is recorded rather than repaired.** There is no database UNIQUE constraint on
`(assignment_id, period)`. Uniqueness holds because `current_period()` derives the period
server-side and `researchprejudgment` refuses a second preliminary judgment for it, so no route
can create a second row — but it is an application invariant, not a schema one. The export
invariant `duplicate participant/project/period rows = 0` is therefore checked at export time
and must stay checked.

## 2. Persisted fields, derived from the live model

`decisions` carries: `decision_id`, `assignment_id`, `package_id`, `package_hash`, `period`,
`result_id`, `pre_action`, `pre_confidence`, `pre_assessment`, `pre_submitted_at`,
`pre_locked_at`, `pre_judgment_locked`, `reveal_at`, `final_action`, `disposition`, `rationale`,
`final_confidence`, `final_submitted_at`, `escalation_level`, `owner_role`, `authority_role`,
`resource_constraint`, `evidence_items`, `reason_code`, `deadline`, `residual_risk`.

Every timestamp is `DateTime(timezone=True)` and **server-assigned via `func.now()`**. No client
clock is trusted anywhere. That is the clock source for the whole study record.

## 3. Construct-by-construct reconciliation

The machine-readable version is `code_audit/run38_research_field_reconciliation.csv`. In prose:

| construct | how it is carried | verdict |
|---|---|---|
| preliminary action / assessment | `pre_action`, `pre_assessment` | persisted, exportable |
| preliminary confidence | `pre_confidence` (0–100, validated) | persisted, exportable |
| final action | `final_action` | persisted, exportable |
| final confidence | `final_confidence` (0–100, validated) | persisted, exportable |
| **AI recommendation presented** | `package_id` + `package_hash` on the decision; content on `decision_support_packages` | persisted; **not in the governed flat CSV** — see §5 |
| agreement / disagreement | derived: `pre_action`/`final_action` vs the package's `recommended_action` | derivable |
| disposition toward AI | `disposition`, closed vocabulary of 8 | persisted, exportable |
| rationale | `rationale`, free text | persisted; **excluded from the analysis dataset** — see §6 |
| evidence use | `evidence_items` (labels the UI generated), `reason_code` (closed vocabulary of 8) | persisted, exportable |
| judgment revision | derived from the four judgment columns plus the package | derivable |
| timing / duration | `pre_submitted_at`, `pre_locked_at`, `reveal_at`, `final_submitted_at` | persisted, exportable |
| project | `assignment → scenario.evidence_package_id` | persisted, exportable |
| reporting period | `period` | persisted, exportable |
| participant identity | `assignment → participant.pseudonymous_code` | persisted, pseudonymous |
| **simulation / package version** | **not persisted on any research row** | stamped at export time — see §4 |
| treatment / AI identity | `package_id`, `package_hash` (hash copied at reveal) | persisted, exportable |
| lock timestamps | `pre_locked_at`; final lock is `final_submitted_at` | persisted, exportable |

**No primary study outcome is unreconstructible from persisted data.** That is the section-6
gate and it passes.

## 4. Frozen-instrument version identity

Measured fact: **no research table stores the simulation version, the participant package or a
schema version.** `EXPORT_COLUMNS` carries `scenario_version`, `config_code`, `package_version`
and `package_hash`, but nothing that names the instrument.

Consequence and remedy: the Run-38 analysis export stamps `simulation_version`,
`participant_package`, `synthetic_package`, `freeze_candidate_commit` and `schema_version` onto
**every row**, read at export time from `app.simulation.models.SIMULATION_VERSION`,
`tools/participant_packages.CURRENT` and `research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json`.
This proves *which instrument produced the dataset*; it does not retroactively prove which
instrument a historical row was collected under. **The administrator must therefore export
within the same frozen release the data was collected under**, and the runbook states that as a
hard rule.

## 5. Where the AI recommendation lives

`EXPORT_COLUMNS` — the governed flat CSV — contains **no AI recommendation column**. The
recommendation actually disclosed is on the Stimulus sheet of the xlsx workbook
(`build_stimulus_rows`), joinable to Decisions on `instance_id`.

Consequence: revision direction relative to the AI **cannot be derived from the governed flat
CSV alone**. The Run-38 analysis export performs the Stimulus join and carries
`ai_recommended_action`, `ai_detected_condition`, `ai_output_type`, `ai_model_version` as
columns, which is what makes the planned dependent variables derivable from one file.

## 6. Free text

Three columns are participant-authored: `pre_assessment`, `rationale`, `residual_risk`. The
governed export flags them (`review_required`, `free_text_columns`) in its JSON form; the CSV
form carries no flag because RFC 4180 has no comment syntax.

**Measured, not assumed:** an email address typed into `rationale` through the real
`researchdecision` route reaches the governed CSV verbatim. There is no automated removal, no
governed manual-review procedure in the repository, and no rationale coding protocol.

**Therefore the analysis dataset excludes free text by construction.** It carries only
non-identifying derivations — `rationale_present`, `rationale_chars`, `pre_assessment_present`,
`pre_assessment_chars`, `residual_risk_present` — plus the two structured, closed-vocabulary
fields (`reason_code`, `evidence_items_count`). This follows the precedent the repository
already set for the workbook's `analysis_long` sheet. No scrubber is claimed, because a
scrubber's efficacy cannot be proved.

The raw free text remains in the governed `participant_inputs` export, which is review-required
and is **not** the analysis dataset. Reading it is a separate, human-reviewed act.

## 7. Derived dependent variables

- `action_revised` = `pre_action != final_action`
- `revision_direction` ∈ {`none`, `toward_ai`, `away_from_ai`, `lateral`}, defined relative to
  `ai_recommended_action`. **This is not a correctness label.** No reference standard is
  asserted and AI agreement is not treated as accuracy.
- `confidence_change` = `final_confidence − pre_confidence`;
  `confidence_direction` ∈ {`increase`, `decrease`, `unchanged`}
- `pre_matches_ai`, `final_matches_ai`
- `deliberation_seconds` (reveal → final), `pre_assessment_seconds`, `time_on_instance_seconds`

All five are re-derived independently in R from the raw columns by
`research/study_execution/run38_ingest_qualification.R`, which is how their derivability is
proved rather than asserted.

## 8. Timing caveats

- Clock source: the database server, via `func.now()`. Never the participant's clock.
- Ordering is enforced in the schema: `CHECK (reveal_at IS NULL OR (pre_locked_at IS NOT NULL
  AND pre_locked_at <= reveal_at))`. Negative deliberation is therefore impossible by
  construction, not by convention.
- **Timezone:** the columns are declared `timezone=True`, which Postgres honours. On SQLite the
  offset is not stored and ISO strings render naive. The study database must be Postgres for
  timezone-aware timestamps; a SQLite dry run cannot demonstrate that property.
- Reload and resume do not touch any timestamp: the stage is derived from the row on every
  request and is never stored on the client.

## 9. Lock model, as measured

- **Preliminary lock: two layers.** The route refuses resubmission, *and* database trigger
  `trg_decisions_pre_lock_guard` (migration 0003) refuses an UPDATE to `pre_action` or
  `pre_confidence` after `pre_locked_at`. A raw SQL bypass was attempted and refused.
- **Final lock: one layer.** `researchdecision` refuses a second final decision, and a
  mechanically derived census of `server/app/` shows that route is the *only* application writer
  of `final_action`, `final_submitted_at`, `disposition` and `final_confidence`. There is **no**
  database trigger for the final lock: a raw SQL UPDATE succeeds.

This asymmetry is **recorded, not repaired**. It is not a server-boundary bypass — no API path
reaches it — so it is not a readiness blocker. Closing it would mean a new migration on the
participant data path, which requires a successor freeze candidate, not a Run-38 edit.
