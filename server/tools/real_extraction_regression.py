#!/usr/bin/env python3
"""
Optional LIVE re-verification of the substitution fix against the two real documents.

Run (from server/):

    ANTHROPIC_API_KEY=... PYTHONIOENCODING=utf-8 python tools/real_extraction_regression.py \
        "<path to Contract Value Summary P01.docx>" "<path to Design Activity Status U03.docx>"

DELIBERATELY NOT NAMED `test_*`. If it were, every future session's "run the server suite" step
(`tools/test_*.py`) would either fail without a key and two files nobody committed, or need
special-case skip logic that some future runner script forgets — silently downgrading "the server
suite passed" from a fact into an approximation. This script is not swept into that glob on
purpose. `tools/test_extraction_prompt.py` is the suite that always runs; this is what re-proves
the suite's tripwire is actually still tripwiring something real, on demand.

WHY THE TWO FILES ARE NOT CHECKED INTO THIS REPOSITORY

They are real project documents (Project A design set), supplied from the owner's own machine
outside this repository. Committing them would put project financial and schedule figures into
git history for a reason no part of this task asked for. Pass their paths as arguments.

WHAT THIS ASSERTS

The exact six pass conditions recorded against a real model call in
`REPORT_2026-08-05_extraction-substitution.md`:

  1. project_start_date and project_end_date are both null on the contract value summary.
  2. original_contract_sum is still 5,874,620.
  3. The two pending authorizations ($86,740 + $34,980) are still excluded from that sum.
  4. activities_planned is 9 on the activity status.
  5. milestones_json carries all nine activity rows.
  6. The six genuinely-absent schedule_update fields are still null, and the one genuinely
     present one (data_date) is still extracted — so the fix does not overcorrect into refusing
     real content out of new-found caution.

It refuses to run without a key, the same as `real_extraction_probe.py`, and writes nothing to
any database.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def finish() -> None:
    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    sys.exit(1 if failed else 0)


CONTRACT_VALUE = 5874620.0
PENDING_AUTHORIZATIONS = 86740 + 34980  # excluded from the current agreement, per the document

SCHEDULE_ABSENT_FIELDS = [
    "planned_percent_complete", "planned_value_to_date", "total_float", "consumed_float",
    "activities_constrained", "lookahead_weeks",
]


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    cv_path, sched_path = Path(sys.argv[1]), Path(sys.argv[2])

    from app.extraction_client import ExtractionError, build_extractor
    from app.extraction_fields import extraction_fields_for

    try:
        extractor = build_extractor(require_real=True)
    except ExtractionError as exc:
        print(f"REFUSED: {exc}")
        print("This script never falls back to the stub. Set ANTHROPIC_API_KEY and re-run.")
        sys.exit(2)
    print(f"extractor: {type(extractor).__name__}  model: {extractor.model_id}\n")

    print("=" * 78)
    print("CONTRACT VALUE SUMMARY")
    print("=" * 78)
    raw = cv_path.read_bytes()
    doc_type, extraction, confidence = extractor.extract_with_confidence(raw, "", cv_path.name)
    print(f"classified: {doc_type}  confidence: {confidence}")
    print(extraction)
    check(doc_type == "contract_value", "classified as contract_value", doc_type)
    check(extraction.get("project_start_date") is None,
          "1. project_start_date is null", repr(extraction.get("project_start_date")))
    check(extraction.get("project_end_date") is None,
          "1. project_end_date is null", repr(extraction.get("project_end_date")))
    got_sum = extraction.get("original_contract_sum")
    check(got_sum is not None and abs(float(got_sum) - CONTRACT_VALUE) < 0.005,
          "2. original_contract_sum is 5,874,620", repr(got_sum))
    check(got_sum is not None and abs(float(got_sum) - (CONTRACT_VALUE + PENDING_AUTHORIZATIONS))
          > 0.005,
          "3. the pending authorizations are NOT folded into the sum",
          f"got {got_sum}, would be {CONTRACT_VALUE + PENDING_AUTHORIZATIONS} if leaked")

    print("\n" + "=" * 78)
    print("DESIGN ACTIVITY STATUS")
    print("=" * 78)
    raw2 = sched_path.read_bytes()
    doc_type2, extraction2, confidence2 = extractor.extract_with_confidence(
        raw2, "", sched_path.name)
    print(f"classified: {doc_type2}  confidence: {confidence2}")
    print(extraction2)
    check(doc_type2 == "schedule_update", "classified as schedule_update", doc_type2)
    check(extraction2.get("activities_planned") == 9,
          "4. activities_planned is 9", repr(extraction2.get("activities_planned")))
    ms = extraction2.get("milestones_json")
    check(isinstance(ms, list) and len(ms) == 9,
          "5. milestones_json carries all nine activity rows",
          f"type={type(ms).__name__} len={len(ms) if isinstance(ms, list) else '?'}")
    if isinstance(ms, list) and ms:
        first_keys = set(ms[0].keys()) if isinstance(ms[0], dict) else set()
        check(bool({"Activity", "Baseline start", "Baseline finish"} & first_keys) or
              any("baseline" in k.lower() for k in first_keys),
              "and each row carries the table's own baseline columns",
              str(sorted(first_keys)))
    for f in SCHEDULE_ABSENT_FIELDS:
        check(extraction2.get(f) is None,
              f"6. {f} is still null (genuinely absent from the document)",
              repr(extraction2.get(f)))
    check(extraction2.get("data_date") is not None,
          "6. data_date is still extracted (genuinely present) -- no overcorrection",
          repr(extraction2.get("data_date")))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        check(False, f"script crashed: {type(exc).__name__}: {exc}")
    finish()
