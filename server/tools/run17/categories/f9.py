import sys, pathlib
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools")
sys.path.insert(0, str(HERE / "run17"))
from fault_harness import inject, write_faults, all_red

FAULTS = [
  {"module_id": "9.1",
   "fault": "a field holding zero treated as missing, breaking the rule that zero is a value",
   "file": "app/simulation/models_dq.py",
   "old": 'present = sum(1 for f in _CORE_FIELDS if si.get(f) is not None)',
   "new": 'present = sum(1 for f in _CORE_FIELDS if si.get(f))',
   "expect_red_contains": "9.1"},
  {"module_id": "9.2",
   "fault": "timeliness reference date moved off the period cutoff",
   "file": "app/simulation/models_dq.py",
   "old": 'now_ms = _js_date_ms(str(period_cutoff))',
   "new": 'now_ms = _js_date_ms("2026-08-30")',
   "expect_red_contains": "9.2"},
  {"module_id": "9.3",
   "fault": "source reliability monotonicity reversed, so a derived field outranks a measured one",
   "file": "app/simulation/models_dq.py",
   "old": 'avg = round2(sum(weights) / len(weights))',
   "new": 'avg = round2(1.0 - sum(weights) / len(weights))',
   "expect_red_contains": "9.3"},
  {"module_id": "9.4",
   "fault": "an absent event log made to report rather than abstain, so silence becomes evidence",
   "file": "app/simulation/models_dq.py",
   "old": '    events = si.get("events")\n    if not isinstance(events, list):\n        return insufficient("Audit_Trail_Completeness")\n    required = ["project_created", "signals_extracted"]',
   "new": '    events = si.get("events") or []\n    required = ["project_created", "signals_extracted"]',
   "expect_red_contains": "9.4"},
  {"module_id": "9.6",
   "fault": "consistency denominator renormalised over the checks that could be run, restoring the defect where deleting the disagreeing document makes the documents agree",
   "file": "app/simulation/models_dq.py",
   "old": 'score = consistent / DECLARED_CONSISTENCY_CHECKS',
   "new": 'score = consistent / checks',
   "expect_red_contains": "9.6"},
  # NOTE. The first fault tried here relaxed the two-upload guard so one upload could establish
  # an interval. That divides by an empty interval list and CRASHES, so no RESULT line is
  # printed and the harness correctly scored it NO_CRASHED_INSTEAD rather than a red. It was
  # replaced by the interval-count defect the specification itself warns about at PH.3: three
  # observations contain two adjacent intervals, and dividing by the wrong count is the error.
  {"module_id": "9.7",
   "fault": "mean interval divided by the number of observations rather than the number of intervals between them",
   "file": "app/simulation/models_dq.py",
   "old": 'avg = sum(intervals) / len(intervals)',
   "new": 'avg = sum(intervals) / len(dates)',
   "expect_red_contains": "9.7"},
  {"module_id": "ARCH",
   "fault": "the Category 9 raw-input bypass marker flipped to claim the signal package is qualified when no gate exists",
   "file": "app/simulation/signal_package.py",
   "old": 'SIGNAL_QUALIFICATION = "unqualified"',
   "new": 'SIGNAL_QUALIFICATION = "qualified"',
   "expect_red_contains": "ARCH"},
]

rows = inject(FAULTS, "test_run19_category_9.py")
write_faults(pathlib.Path("/home/user/LinPRojectRadar/server/tools/run17/categories/category_9_faults.csv"), rows)
for r in rows:
    print(r["module_id"], r["test_turned_red"], "|", r["bytes_changed"], "|", r["red_test_name"][:110])
print("ALL RED:", all_red(rows))
