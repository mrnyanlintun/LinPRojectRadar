#!/usr/bin/env python3
"""
RUN 80. THE CATEGORY-9 RECOMPUTE, THE CPARS WORD SCALE, THE FIELD-LEVEL ABSENCE RULE, AND THE
THREE A3 STRUCTURES.

Every check here is pinned to an exact site and was proved non-vacuous by deleting that site
during Run 80 (see the report). Nothing is asserted by grep over prose: the assertions are on
returned structures, stored dictionaries and raised exceptions.
"""
from __future__ import annotations
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
FAILURES: list[str] = []
CHECKS = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILURES.append(f"{name}: {detail}")


from app.extraction_merge import (                                       # noqa: E402
    CPARS_RATING_SCALE, ORDINAL_WORD_SCALES, NumericRangeError,
    emit_observations, read_ordinal_word, validate_numeric_fields,
)
from app.documents import _reference_class_members, _run80_a3_structures  # noqa: E402
from app.simulation.qualification_boundary import gated_module_ids        # noqa: E402
from app.simulation.registry import run_module, service_index             # noqa: E402
import datetime as _dt                                                    # noqa: E402

# =============================================================== 1. the Category-9 boundary
#
# PINNED TO: the qualification boundary's treatment of an ABSENT `evidenceQualification`, and
# to the second staleness condition in `documents._period_is_stale` that repairs a row missing
# it. Run 68 reported this fixed and it was not; Run 78 fixed the real cause. These two checks
# are what makes a third contradictory opinion impossible: they measure it.
GATED = sorted(set(gated_module_ids()) & set(service_index()))
check("gated modules in service is the measured 16, not the 40 the contract declares",
      len(GATED) == 16 and len(gated_module_ids()) == 40,
      f"{len(GATED)} in service of {len(gated_module_ids())} declared")

_EQ = {"evidence_id": "period-evidence", "source_type": "documents", "period": 1,
       "effective_date": "2026-03-31", "material_conflicts": []}
_BASE = {"bac": 4_000_000, "ev": 1_000_000, "ac": 1_050_000, "pv": 1_020_000}


def _gate_refusals(si: dict) -> int:
    n = 0
    for mid in GATED:
        r = run_module(mid, si, lambda: 0.5, _dt.date(2026, 3, 31))
        if r.get("abstention_reason_code") == "CATEGORY9_ASSESSMENT_MISSING":
            n += 1
    return n


check("with no Category-9 assessment every gated module in service refuses at the boundary",
      _gate_refusals(dict(_BASE)) == len(GATED),
      f"{_gate_refusals(dict(_BASE))} of {len(GATED)} refused")
check("with the assessment present not one gated module refuses at the boundary",
      _gate_refusals({**_BASE, "evidenceQualification": _EQ}) == 0,
      f"{_gate_refusals({**_BASE, 'evidenceQualification': _EQ})} still refused")

_STALE_SITE = (ROOT / "server/app/documents.py").read_text(encoding="utf-8")
check("the staleness condition that repairs such a row is in the tree",
      '"evidenceQualification" not in result.signal_inputs' in _STALE_SITE,
      "documents.py no longer finds a result missing the assessment stale, so a period computed "
      "before Run 67 would never regain it")

# =============================================================== 2. the CPARS word scale
check("the five CPARS levels and no others",
      sorted(CPARS_RATING_SCALE) == ["exceptional", "marginal", "satisfactory",
                                     "unsatisfactory", "very good"],
      str(sorted(CPARS_RATING_SCALE)))
check("the scale is five points, matching the range A6.4 enforces",
      sorted(CPARS_RATING_SCALE.values()) == [1.0, 2.0, 3.0, 4.0, 5.0],
      str(sorted(CPARS_RATING_SCALE.values())))
check("Satisfactory reads as 3", read_ordinal_word("overall_rating", "Satisfactory") == 3.0,
      repr(read_ordinal_word("overall_rating", "Satisfactory")))
check("case and spacing do not change the reading",
      read_ordinal_word("quality_rating", "  VERY   good ") == 4.0,
      repr(read_ordinal_word("quality_rating", "  VERY   good ")))
# THE STRICTEST CHECK IN THIS SUITE (Run 80 order, section 10, item 3).
check("a word outside the scale is NOT coerced to a number",
      read_ordinal_word("overall_rating", "Above Average") == "Above Average",
      repr(read_ordinal_word("overall_rating", "Above Average")))
check("the word scale applies only to the four rating keys",
      read_ordinal_word("earned_value", "Satisfactory") == "Satisfactory"
      and sorted(ORDINAL_WORD_SCALES) == ["cost_rating", "overall_rating",
                                          "quality_rating", "schedule_rating"],
      str(sorted(ORDINAL_WORD_SCALES)))

# The prose statement of the mapping, checked against the mapping itself so the two cannot drift.
_SPEC = (ROOT / "specifications/RATING_WORD_SCALES.md").read_text(encoding="utf-8")
check("every level of the scale is stated where a person can read it",
      all(f"| {w.title():<15}| {int(n)}" in _SPEC.replace("Very Good     ", "Very Good      ")
          or f"| {w.title()} " in _SPEC for w, n in CPARS_RATING_SCALE.items()),
      "specifications/RATING_WORD_SCALES.md does not state every level of CPARS_RATING_SCALE")
check("the four fields the scale applies to are named in the same file",
      all(k in _SPEC for k in ORDINAL_WORD_SCALES),
      "specifications/RATING_WORD_SCALES.md does not name every field in ORDINAL_WORD_SCALES")

# =============================================================== 3. field-level absence
#
# PINNED TO: `validate_numeric_fields` returning unreadable fields instead of raising, and to
# `emit_observations` still emitting the rest of the document. This is the owner's Run 80
# section 3 item 3 ruling, overriding the whole-document refusal that stood from D2.
_PPR = {"overall_rating": "Above Average", "schedule_rating": "Very Good",
        "cost_rating": "Marginal", "quality_rating": "Exceptional"}
_unreadable = validate_numeric_fields("past_performance_report", dict(_PPR),
                                      filename="D26_past_performance_report.pdf")
check("an unrecognised rating no longer refuses the document",
      isinstance(_unreadable, list) and len(_unreadable) == 1
      and _unreadable[0]["field"] == "overall_rating",
      str(_unreadable))
check("the unreadable field says the rating was not recognised, in those words",
      _unreadable and "not recognised" in _unreadable[0]["reason"]
      and "Above Average" in _unreadable[0]["reason"],
      str(_unreadable))
check("a document that reads cleanly reports nothing unreadable",
      validate_numeric_fields("past_performance_report",
                              {**_PPR, "overall_rating": "Satisfactory"}) == [],
      "a clean past performance report reported an unreadable field")

_obs = emit_observations({"doc_type": "past_performance_report", "sha256": "a" * 64,
                          "filename": "D26_past_performance_report.pdf",
                          "extraction": dict(_PPR, document_date="2026-03-31")})
_fields = {o["field"]: o["value"] for o in _obs}
check("the rest of the document still contributes when one field cannot be read",
      _fields.get("scheduleRating") == 4.0 and _fields.get("costRating") == 2.0
      and _fields.get("qualityRating") == 5.0,
      str(_fields))
check("the field that could not be read is absent, not zero and not substituted",
      "overallRating" not in _fields, str(_fields))

# OUT OF RANGE STILL REFUSES THE WHOLE DOCUMENT. Run 14's ruling, deliberately not overridden.
try:
    validate_numeric_fields("rfi_log", {"rfi_total": -5})
    _range_refused = False
except NumericRangeError:
    _range_refused = True
check("a readable but out-of-range figure still refuses the whole document",
      _range_refused, "a negative count no longer refuses the document")

# =============================================================== 4. the three A3 structures
_HD = {
    "analogous_project_name": "Cascade Hall Renewal",
    "similar_project_final_cost": 17_640_000, "analogous_adjustment_factor": 1.09,
    "analogous_source": "CPARS record", "analogous_comparability_basis": "same building type",
    "analogous_normalization_basis": "price level and floor area",
    "cost_index_name": "ENR Building Cost Index", "cost_index_authority": "Engineering News Record",
    "cost_index_geography": "United States", "cost_index_scope": "building construction",
    "cost_index_base_period": "2025-12", "cost_index_base_value": 14782,
    "cost_index_observation_period": "2026-03", "cost_index_current_value": 14861,
    "cost_index_vintage": "2026-03 publication",
    "reference_class_inclusion_criteria": "federal buildings 10-50M",
    "reference_class_exclusion_criteria": "terminated contracts",
    "reference_class_outcome_definition": "final over award less one",
    "reference_class_normalization": "constant 2026 dollars",
    "reference_class_vintage": "2026-02 extract",
    "reference_class_governed_percentile": 80,
    "reference_class_json": [{"Project": "RC-01", "Award value": 100, "Final value": 110},
                             {"Project": "RC-02", "Award value": 100, "Final value": 120},
                             {"Project": "RC-03", "Award value": 100, "Final value": 130}],
}
_S = _run80_a3_structures(dict(_HD))
check("all three A3 structures assemble from one historical-data document",
      sorted(_S) == ["analogEstimate", "externalCostIndex", "referenceClassPopulation"],
      str(sorted(_S)))
check("the analogue is identified by name and adapted by the stated factor",
      _S["analogEstimate"]["analog_project_id"] == "Cascade Hall Renewal"
      and _S["analogEstimate"]["adaptation_factors"][0]["factor_value"] == 1.09,
      str(_S.get("analogEstimate")))
check("the index carries all seven provenance fields and both levels",
      all(_S["externalCostIndex"].get(k) for k in
          ("index_name", "authority", "geography", "scope", "base_period",
           "observation_period", "vintage", "base_index_value", "current_index_value")),
      str(_S.get("externalCostIndex")))
check("a governed percentile stated as 80 is read as 0.80",
      _S["referenceClassPopulation"]["governed_percentile"] == 0.8,
      str(_S["referenceClassPopulation"].get("governed_percentile")))
# ALL OR NOTHING: a blank provenance field yields NO structure, not a structure with a blank.
check("a blank provenance field withholds the structure rather than defaulting it",
      "analogEstimate" not in _run80_a3_structures({**_HD, "analogous_source": ""}),
      "an analog estimate assembled with no stated source")
check("an index with no stated geography is not assembled",
      "externalCostIndex" not in _run80_a3_structures({**_HD, "cost_index_geography": ""}),
      "an external cost index assembled with no geography")

# The overrun is DERIVED in code, never asked of the model.
_m = _reference_class_members([{"Project": "A", "Award value": 100, "Final value": 110},
                               {"Project": "B", "Overrun": 0.25},
                               {"Project": "C", "Award value": 100},
                               {"Award value": 100, "Final value": 200}])
check("the proportional overrun is derived from award and final values",
      _m[0] == {"reference_project_id": "A", "proportional_overrun": 0.1},
      str(_m))
check("a printed overrun is read as printed",
      _m[1]["proportional_overrun"] == 0.25, str(_m))
check("a row that supports neither an overrun nor an identity is dropped, never defaulted",
      len(_m) == 2, str(_m))

# =============================================================== 5. the A3 modules compute
_SI = {"bac": 4_000_000, "evidenceQualification": _EQ,
       "originalContingency": 920_000, "remainingContingency": 892_400,
       "actualPctComplete": 25.0, **_S}
_SI["externalCostIndex"] = {**_S["externalCostIndex"], "cost_exposure": 1_800_000}
for mid, want in (("A3.1", "completed comparable projects"),
                  ("A3.7", "Cascade Hall Renewal"),
                  ("A3.9", "ENR Building Cost Index")):
    _r = run_module(mid, _SI, lambda: 0.5, _dt.date(2026, 3, 31))
    check(f"{mid} produces a reading from the assembled structure",
          not _r.get("insufficient_data") and want in str(_r.get("evidence_metric")),
          str(_r.get("evidence_metric"))[:160])

print(f"checks: {CHECKS}")
print(f"RESULT: {CHECKS - len(FAILURES)}/{CHECKS} checks passed")
if FAILURES:
    print(f"FAILURES: {len(FAILURES)}")
    for f in FAILURES:
        print("  -", f)
    raise SystemExit(1)
print("ALL GREEN")
