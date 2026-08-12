#!/usr/bin/env python3
"""
RUN 12, GATES 1 TO 3. The evidence qualification object: what it reports, what it may gate, and
the things it must never be able to do.

The third block is the one that matters. A qualification object is exactly the kind of artefact
that drifts into fabricating confidence: an unknown becomes a default, a default becomes a pass,
and a reader ends up looking at a healthy-looking evidence state that nothing measured. Every
property below is stated as a thing that MUST NOT happen and is exercised against the real
functions, not against a copy of their logic.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run12_category9_qualification.py
"""

from __future__ import annotations

import datetime
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS  # noqa: E402
from app.simulation.compute import compute_project  # noqa: E402
from app.simulation.qualification import (  # noqa: E402
    FAIL, NOT_APPLICABLE, NOT_ESTIMABLE, PARTIAL, PASS, QUALIFICATION_STATES,
    QUALIFICATION_VERSION, build_qualification, module_qualification,
    qualification_for_stored_result,
)

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")


CUTOFF = datetime.date(2026, 1, 31)

FULL_SI = {
    "bac": 1000.0, "ev": 400.0, "ac": 500.0, "pv": 450.0,
    "cpi": 0.8, "spi": 0.9, "docRiskScore": 40,
    "actualPctComplete": 40, "plannedPctComplete": 45,
    "sources": {"cpi": {"docType": "monthly_report"}, "spi": {"docType": "monthly_report"}},
}


def qual(si, period="P1", cutoff=CUTOFF):
    run = compute_project(dict(si), "SC-RUN12", period, cutoff)
    return run["evidence_qualification"], run


# ------------------------------------------------------------------ 1. SHAPE AND VOCABULARY

REQUIRED_KEYS = (
    "project_id", "reporting_period", "evidence_package", "qualification_version",
    "required_inputs_status", "missing_required_inputs",
    "canonical_structure_status", "missing_canonical_structures",
    "period_applicability_status", "provenance_status", "provenance_evidence",
    "timeliness_status", "timeliness_basis",
    "revision_resolution_status", "revision_resolution_reason",
    "overall_qualification_state", "generated_at",
)

print("=" * 78)
print("1. SHAPE, VOCABULARY AND THE ABSENCE OF A SCORE")
print("=" * 78)

q, run = qual(FULL_SI)
for k in REQUIRED_KEYS:
    check(k in q, f"the object carries {k}")
check(q["qualification_version"] == QUALIFICATION_VERSION, "the object carries its own version")

for k in ("required_inputs_status", "canonical_structure_status", "period_applicability_status",
          "provenance_status", "timeliness_status", "revision_resolution_status",
          "overall_qualification_state"):
    check(q[k] in QUALIFICATION_STATES, f"{k} is one of the controlled states")

# No composite number anywhere. A float or int on a dimension would be a score by another name.
def _numeric_leaves(obj, path=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += _numeric_leaves(v, f"{path}.{k}")
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append(path)
    return out

nums = _numeric_leaves({k: v for k, v in q.items()
                        if k not in ("provenance_evidence", "timeliness_basis")})
check(not nums, f"no numeric value sits on any dimension or on the overall state ({nums})")
check(not any(("score" in str(k).lower() or "confidence" in str(k).lower()) for k in q),
      "no key in the object is named as a score or a confidence")

# ------------------------------------------------------------------ 2. THE TWELVE CASES

print("=" * 78)
print("2. THE REQUIRED CASES")
print("=" * 78)

# all required inputs present, for the modules that carry a machine-checkable requirement
q_full, _ = qual(FULL_SI)
check(q_full["required_inputs_status"] in (PASS, PARTIAL),
      "a fully supplied period yields a stated required-input state")

# one required input missing: strictly more modules go silent than before
si_missing = dict(FULL_SI)
si_missing.pop("cpi")
q_missing, _ = qual(si_missing)
check(len(q_missing["missing_required_inputs"]) > len(q_full["missing_required_inputs"]),
      "removing a required input names strictly more modules as missing their inputs")
check(q_missing["required_inputs_status"] == PARTIAL,
      "a missing required input reports PARTIAL on the required-input dimension")

# canonical structures absent, then present
check(q_full["canonical_structure_status"] == PARTIAL and q_full["missing_canonical_structures"],
      "absent canonical structures are named, not silently passed")
si_canon = dict(FULL_SI)
for _mid, _key in CANONICAL_STRUCTURE_KEYS.items():
    si_canon[_key] = {"present": True}
q_canon, _ = qual(si_canon)
check(q_canon["canonical_structure_status"] == PASS
      and q_canon["missing_canonical_structures"] == [],
      "with every canonical structure supplied the dimension reads PASS")

# applicable and not-applicable period
check(q_full["period_applicability_status"] == PASS, "an applicable period reads PASS")
q_na = build_qualification(FULL_SI, run, project_id="P", reporting_period=None,
                           period_cutoff=None)
check(q_na["period_applicability_status"] == NOT_APPLICABLE,
      "a period that does not apply reads NOT_APPLICABLE")
check(q_na["overall_qualification_state"] == NOT_APPLICABLE,
      "a not-applicable period carries through to the overall state")

# provenance: partial (type only) and complete (identity and version present)
check(q_full["provenance_status"] == PARTIAL,
      "a document type without a document identity is PARTIAL provenance, not PASS")
si_prov = dict(FULL_SI)
si_prov["sources"] = {k: {"docType": "monthly_report", "documentId": "DOC-1",
                          "documentVersion": "3"} for k in ("cpi", "spi")}
q_prov, _ = qual(si_prov)
check(q_prov["provenance_status"] == PASS,
      "a document identity and version on every sourced field is PASS provenance")
si_nosrc = {k: v for k, v in FULL_SI.items() if k != "sources"}
q_nosrc, _ = qual(si_nosrc)
check(q_nosrc["provenance_status"] == NOT_ESTIMABLE,
      "no source record at all is NOT_ESTIMABLE provenance, never PASS")

# timeliness: known cutoff without per-field dates, and with them
check(q_full["timeliness_status"] == PARTIAL,
      "a period cutoff without per-field as-of dates is PARTIAL timeliness")
check(q_full["timeliness_basis"]["period_cutoff"] == str(CUTOFF),
      "the timeliness basis names the cutoff it actually used")
si_dated = dict(FULL_SI)
si_dated["sources"] = {k: {"docType": "monthly_report", "asOf": "2026-01-30"}
                       for k in ("cpi", "spi")}
q_dated, _ = qual(si_dated)
check(q_dated["timeliness_status"] == PASS, "an as-of date on every sourced field is PASS")
q_nocut = build_qualification(FULL_SI, run, project_id="P", reporting_period="P1",
                              period_cutoff=None)
check(q_nocut["timeliness_status"] == NOT_ESTIMABLE,
      "no cutoff is NOT_ESTIMABLE timeliness")

# revision resolution is never anything but NOT_ESTIMABLE in this repository
for label, si in (("full", FULL_SI), ("dated", si_dated), ("identified", si_prov),
                  ("canonical", si_canon), ("missing", si_missing)):
    qq, _ = qual(si)
    check(qq["revision_resolution_status"] == NOT_ESTIMABLE,
          f"revision resolution is NOT_ESTIMABLE on the {label} case")
check("upload order" in q_full["revision_resolution_reason"],
      "the revision reason states plainly that upload order is not evidence of currency")

# malformed input
q_bad = build_qualification("not a dictionary", run, project_id="P", reporting_period="P1",
                            period_cutoff=CUTOFF)
check(q_bad["overall_qualification_state"] == NOT_ESTIMABLE and q_bad.get("malformed_input"),
      "a malformed qualification input is refused as NOT_ESTIMABLE, not defaulted")
q_bad2 = build_qualification(FULL_SI, None, project_id="P", reporting_period="P1",
                            period_cutoff=CUTOFF)
check(q_bad2["overall_qualification_state"] == NOT_ESTIMABLE,
      "a malformed run result is refused as NOT_ESTIMABLE")

# per-module face
mq = module_qualification(si_canon, "A2.2")
check(mq["canonical_structure_status"] == PASS, "a module can inspect its structure as present")
mq2 = module_qualification(FULL_SI, "A2.2")
check(mq2["canonical_structure_status"] == FAIL, "a module can inspect its structure as absent")
mq3 = module_qualification(FULL_SI, "A1.7")
check(mq3["canonical_structure_status"] == NOT_APPLICABLE,
      "a module needing no canonical structure reads NOT_APPLICABLE, not PASS")

# ------------------------------------------------------------------ 3. NO FABRICATED CONFIDENCE

print("=" * 78)
print("3. THE PROPERTIES THAT MUST NEVER HOLD")
print("=" * 78)

RANK = {PASS: 3, PARTIAL: 2, NOT_APPLICABLE: 1, NOT_ESTIMABLE: 0, FAIL: 0}

# Removing evidence can never improve any dimension. Exhaustive over every removable key.
worse_ok = True
for key in list(FULL_SI):
    si_less = {k: v for k, v in FULL_SI.items() if k != key}
    q_less, _ = qual(si_less)
    for dim in ("required_inputs_status", "canonical_structure_status", "provenance_status",
                "timeliness_status", "revision_resolution_status",
                "overall_qualification_state"):
        if RANK[q_less[dim]] > RANK[q_full[dim]]:
            worse_ok = False
            print(f"     removing {key} improved {dim}: {q_full[dim]} -> {q_less[dim]}")
check(worse_ok, "removing any single piece of evidence improves no dimension (exhaustive)")

# Missing provenance cannot become verified provenance; missing timeliness cannot become current.
check(q_nosrc["provenance_status"] != PASS, "absent provenance never reads as verified")
check(q_nocut["timeliness_status"] != PASS, "absent timeliness never reads as current")
check(all(q["revision_resolution_status"] != PASS for q in (q_full, q_prov, q_dated)),
      "unknown revision state never reads as a resolved latest revision")

# PARTIAL cannot silently become PASS at the overall state.
check(RANK[q_full["overall_qualification_state"]] <= min(
    RANK[q_full[d]] for d in ("required_inputs_status", "canonical_structure_status",
                              "provenance_status", "timeliness_status",
                              "revision_resolution_status")),
      "the overall state is never better than the weakest dimension")

# NOT_ESTIMABLE survives a store-and-read round trip.
q_read = qualification_for_stored_result(
    signal_inputs=FULL_SI, module_results=run["modules"], abstained=run["abstained"],
    project_id=None, period="P1", period_cutoff=CUTOFF)
check(q_read["revision_resolution_status"] == NOT_ESTIMABLE,
      "NOT_ESTIMABLE is preserved through the stored-row read path")
check(q_read["provenance_status"] == q_full["provenance_status"]
      and q_read["timeliness_status"] == q_full["timeliness_status"]
      and q_read["overall_qualification_state"] == q_full["overall_qualification_state"],
      "the read path and the compute path agree on every state")

# The qualification cannot create a vote or change a status.
base = compute_project(dict(FULL_SI), "SC-RUN12", "P1", CUTOFF)
check(base["voting_module_ids"] == ["A1.7", "A1.8"],
      "the voting set is exactly the two cost lineage modules with the qualification present")
check("evidence_qualification" not in str(base["category_statuses"]),
      "no category status carries the qualification")
for si_variant, label in ((si_prov, "complete provenance"), (si_dated, "complete timeliness"),
                          (si_nosrc, "no provenance at all")):
    r = compute_project(dict(si_variant), "SC-RUN12", "P1", CUTOFF)
    check(r["project_status"] == base["project_status"],
          f"changing only qualification evidence ({label}) does not change project status")
    check(r["voting_module_ids"] == base["voting_module_ids"],
          f"changing only qualification evidence ({label}) does not change who votes")

# A required input that IS a voting module's own input legitimately changes status by the
# module's own abstention, not by the qualification.
si_novote = {k: v for k, v in FULL_SI.items() if k not in ("cpi", "spi", "ev", "ac", "pv")}
r_novote = compute_project(dict(si_novote), "SC-RUN12", "P1", CUTOFF)
check(r_novote["project_status"] != base["project_status"] or r_novote["project_status"] is None,
      "a voting module losing its own required evidence is what moves the status, and it does")
check(r_novote["evidence_qualification"]["required_inputs_status"] == PARTIAL,
      "and the qualification reports that as a required-input shortfall")

total = len(results)
passed = sum(1 for ok, _ in results if ok)
print()
for ok, label in results:
    if not ok:
        print(f"FAILED: {label}")
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
