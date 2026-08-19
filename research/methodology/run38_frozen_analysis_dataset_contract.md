# Run 38 frozen analysis dataset contract

The statistical workflow for this praxis consumes **one frozen, deidentified, checksummed CSV**.
This document is that CSV's contract. It is implemented by
`server/tools/run38_analysis_export.py` and enforced by
`research/study_execution/run38_ingest_qualification.R`.

**Schema version:** `og-analysis-2026.08-v1` (constant `ANALYSIS_SCHEMA_VERSION`).

**This run produced only a dry-run/test export.** No final study dataset exists and none was
created. Every dry-run row carries `record_class = TEST_ONLY`.

---

## 1. Row grain

**One row per participant × project × period.**

Derived, not assumed: a research observation is a `decisions` row keyed by
`(assignment_id, period)`; an assignment is `(participant, scenario)`; a scenario is one
controlled project. A complete participant therefore contributes 6 projects × 6 periods = 36
rows. The dry run produced exactly 36 rows with 36 distinct keys for the completing participant.

**Unique key:** `(study_participant_id, scenario_id, period)`.

## 2. Ordering

Rows are sorted by `(study_participant_id, sequence_number, period)`. Column order is the
literal order of `ANALYSIS_COLUMNS` and never derived from a dict iteration order.

## 3. Encoding and null semantics

| property | value |
|---|---|
| encoding | UTF-8, no BOM |
| line terminator | LF (`\n`) |
| null representation | the literal `NA` |
| boolean representation | `TRUE` / `FALSE` |
| quoting | RFC 4180 minimal, via `csv.DictWriter` |

`NA` was chosen because it is R's own missing token, so `read.csv(..., na.strings = "NA")`
ingests the file with no manual cleanup — which is the property section 15 requires and which
the R script proves rather than assumes.

## 4. Columns

Provenance (present on every row, identical across rows of one export):
`schema_version`, `simulation_version`, `participant_package`, `synthetic_package`,
`freeze_candidate_commit`, `record_class`, `exported_at`.

Keys: `study_participant_id`, `instance_id`, `scenario_id`, `scenario_version`,
`evidence_project_id`, `sequence_number`, `period`.

Design: `order_group`, `config_code`.

Preliminary: `pre_action`, `pre_confidence`, `pre_submitted_at`, `pre_locked_at`,
`pre_assessment_present`, `pre_assessment_chars`.

Disclosed AI treatment: `reveal_at`, `package_id`, `package_version`, `package_hash`,
`ai_recommended_action`, `ai_detected_condition`, `ai_output_type`, `ai_model_version`.

Final: `final_action`, `disposition`, `final_confidence`, `final_submitted_at`, `reason_code`,
`evidence_items_count`, `rationale_present`, `rationale_chars`, `residual_risk_present`,
`escalation_level`, `owner_role`, `authority_role`, `resource_constraint`, `deadline_present`.

Derived: `action_revised`, `revision_direction`, `pre_matches_ai`, `final_matches_ai`,
`confidence_change`, `confidence_direction`.

Timing: `deliberation_seconds`, `pre_assessment_seconds`, `time_on_instance_seconds`,
`pre_committed_before_disclosure`, `completion_state`, `session_break`.

Transition: `branch_id`, `next_state_id`, `transition_displayed_at`.

## 5. Types

- integers: `sequence_number`, `pre_confidence`, `final_confidence`, `confidence_change`,
  `evidence_items_count`, `pre_assessment_chars`, `rationale_chars`, `action_revised` (0/1)
- reals: `deliberation_seconds`, `pre_assessment_seconds`, `time_on_instance_seconds`
- booleans (`TRUE`/`FALSE`): `pre_assessment_present`, `rationale_present`,
  `residual_risk_present`, `deadline_present`, `pre_matches_ai`, `final_matches_ai`,
  `pre_committed_before_disclosure`, `session_break`
- ISO-8601 timestamps: all `*_at` columns
- everything else: character

## 6. Allowed values (closed vocabularies)

| column | levels |
|---|---|
| `record_class` | `TEST_ONLY`, `STUDY` |
| `revision_direction` | `none`, `toward_ai`, `away_from_ai`, `lateral` |
| `confidence_direction` | `increase`, `decrease`, `unchanged` |
| `completion_state` | `complete`, `pre_only`, `revealed_not_decided`, `not_started` |
| `disposition` | the 8 values of `research_decision.DISPOSITIONS` |
| `reason_code` | the 8 values of `research_decision.REASON_CODES` |
| `period` | `P1`..`P6` |

`pre_action` and `final_action` are **deliberately open**. The server does not close that
vocabulary (see the extended comment on `PARTICIPANT_ACTIONS`), and closing it here would
misrepresent the instrument.

## 7. Derived-variable rules

```
action_revised        = (pre_action != final_action)                        [NA if either NA]
revision_direction    = "none"        if not action_revised
                      = "toward_ai"   if final_action == ai_recommended_action
                      = "away_from_ai"if pre_action   == ai_recommended_action
                      = "lateral"     otherwise                             [NA if AI NA]
confidence_change     = final_confidence - pre_confidence
confidence_direction  = sign(confidence_change) -> increase/decrease/unchanged
pre_matches_ai        = (pre_action   == ai_recommended_action)
final_matches_ai      = (final_action == ai_recommended_action)
deliberation_seconds  = final_submitted_at - reveal_at
```

**No correctness label is defined and none may be added** without a governed reference standard
that this repository does not currently contain. `revision_direction` measures movement relative
to the AI, which is the study's construct; it is not accuracy.

## 8. Free text

`pre_assessment`, `rationale` and `residual_risk` are **absent from this dataset by
construction**. Only presence flags and character counts appear. See
`run38_research_data_contract.md` §6 for the measurement that motivated this.

## 9. Checksum procedure

```
sha256sum <dataset>.csv
```
over the exact bytes of the file. The value is recorded in the sidecar manifest
`<dataset>.manifest.json` under `sha256`, together with `row_count`, `column_count`, the column
list, the categorical levels, and the four provenance identities.

`exported_at` is the only column that varies between two exports of identical database state.
The freeze procedure therefore stamps it once, writes the file, and never regenerates it: a
frozen dataset is a file, not a query.

## 10. Freeze procedure

1. Build the export with `run38_analysis_export.build_analysis_rows` + `serialise_csv`.
2. Write `<name>.csv` and `<name>.manifest.json` into the study's frozen-dataset directory.
3. `sha256sum <name>.csv` and confirm it equals the manifest's `sha256`.
4. Run `Rscript research/study_execution/run38_ingest_qualification.R <name>.csv
   <name>.manifest.json`. It must print `RESULT: N/N checks passed` and exit 0.
5. Commit both files together. **Neither is ever edited afterwards.** A correction is a new
   dataset with a new checksum, never an edit in place.

## 11. Provenance fields

`simulation_version`, `participant_package`, `synthetic_package` and `freeze_candidate_commit`
are stamped at export time from the running instrument and the accepted freeze record — not read
from the research rows, which do not carry them. **The export must therefore be taken on the
same frozen release under which the data was collected.** The runbook states this as a rule the
administrator must not break.
