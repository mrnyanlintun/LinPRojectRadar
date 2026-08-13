import sys, pathlib
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools")
sys.path.insert(0, str(HERE / "run17"))
from fault_harness import inject, write_faults, all_red

FAULTS = [
  {"module_id": "4.2",
   "fault": "the request-log period default of thirty days restored, so an absent exposure is silently invented",
   "file": "app/simulation/models_doc.py",
   "old": '    if days is None:\n        return insufficient(\n            "RFI_Velocity",',
   "new": '    days = 30 if days is None else days\n    if False:\n        return insufficient(\n            "RFI_Velocity",',
   "expect_red_contains": "4.2"},
  {"module_id": "4.3",
   "fault": "the rejected-within-total guard removed, so a rate above one is banded",
   "file": "app/simulation/models_doc.py",
   "old": '    if rejected < 0 or rejected > total:\n        return insufficient(\n            "Submittal_Rejection",',
   "new": '    if False:\n        return insufficient(\n            "Submittal_Rejection",',
   "expect_red_contains": "4.3"},
  {"module_id": "4.4",
   "fault": "the audited cohort requirement removed, restoring the backlog stock over one period's intake flow",
   "file": "app/simulation/models_doc.py",
   "old": '    if cohort is None or cohort <= 0:\n        return insufficient(\n            "NCR_Rate",',
   "new": '    cohort = cohort if cohort else max(open_, 1)\n    if False:\n        return insufficient(\n            "NCR_Rate",',
   "expect_red_contains": "4.4"},
  {"module_id": "4.5",
   "fault": "the absent-float worst case restored, so one lost day with unknown float asserts the worst ratio",
   "file": "app/simulation/models_doc.py",
   "old": '    if flt is None:\n        return insufficient(\n            "Weather_Impact",\n            "Awaiting the schedule float available to absorb the lost days: without it there "\n            "is nothing to measure the impact against")',
   "new": '    if flt is None:\n        flt = float(lost) if lost > 0 else 1.0',
   "expect_red_contains": "4.5"},
  {"module_id": "4.7",
   "fault": "the dispute escalation missing-source guard removed, so withholding a log improves the reading again",
   "file": "app/simulation/models_doc.py",
   "old": '    missing = [words for key, words in required if si.get(key) is None]',
   "new": '    si = {"rfiCount": 0, "changeOrderCount": 0, **si}\n    missing = [words for key, words in required if si.get(key) is None]',
   "expect_red_contains": "4.7"},
  {"module_id": "4.9",
   "fault": "procurement double count restored: a delayed item counted once at risk and again at double weight",
   "file": "app/simulation/models_doc.py",
   "old": 'risk_ratio = (delayed + 0.5 * (at_risk - delayed)) / total',
   "new": 'risk_ratio = (at_risk + 2 * delayed) / total',
   "expect_red_contains": "4.9"},
  # NOTE. Removing the no-exposure abstention was tried first: it divides by the square root of
  # zero and CRASHES, so no RESULT line is printed and the harness refused to score it a red.
  # Replaced with the document-risk domain guard, which leaves the suite running.
  {"module_id": "4.10",
   "fault": "the document risk domain guard removed, so a score outside nought to one is multiplied into the band ladder",
   "file": "app/simulation/models_doc.py",
   "old": '    if doc is None or doc < 0 or doc > 1:\n        return insufficient(\n            "Spec_Conflict_Density",',
   "new": '    if doc is None:\n        return insufficient(\n            "Spec_Conflict_Density",',
   "expect_red_contains": "4.10"},
  {"module_id": "4.8",
   "fault": "subcontractor score band direction reversed, so a worse score reads better",
   "file": "app/simulation/models_doc.py",
   "old": 'color = ("Green" if score_pct >= 85 else "Yellow" if score_pct >= 70\n             else "Amber" if score_pct >= 55 else "Red")',
   "new": 'color = ("Red" if score_pct >= 85 else "Amber" if score_pct >= 70\n             else "Yellow" if score_pct >= 55 else "Green")',
   "expect_red_contains": "4.8"},
]

rows = inject(FAULTS, "test_run19_category_4.py")
write_faults(pathlib.Path("/home/user/LinPRojectRadar/server/tools/run17/categories/category_4_faults.csv"), rows)
for r in rows:
    print(r["module_id"], r["test_turned_red"], "|", r["bytes_changed"], "|", r["red_test_name"][:110])
print("ALL RED:", all_red(rows))
