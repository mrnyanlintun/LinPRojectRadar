import sys, pathlib
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools")
sys.path.insert(0, str(HERE / "run17"))
from fault_harness import inject, write_faults, all_red

FAULTS = [
  {"module_id": "3.2",
   "fault": "contingency consumed fraction denominator changed from the original amount to what remains",
   "file": "app/simulation/models_ext.py",
   "old": 'burn_rate = burned / si["originalContingency"]',
   "new": 'burn_rate = burned / max(si["remainingContingency"], 1e-9)',
   "expect_red_contains": "3.2"},
  # NOTE. The first fault attempted here removed the zero cost-index guard. That restores the
  # original crash, so the suite died before printing a RESULT line, and the harness scored it
  # NO_CRASHED_INSTEAD rather than a red. A crash is not a named red test, and treating one as
  # a passing fault is a failure mode this programme has already been bitten by, so the fault
  # was replaced with one that leaves the suite running and turns a NAMED check red.
  {"module_id": "3.6",
   "fault": "P80 uplift direction reversed, so the eightieth percentile falls below the point forecast",
   "file": "app/simulation/models_ext.py",
   "old": 'p80_eac = eac * (1 + uncertainty * 1.28)',
   "new": 'p80_eac = eac * (1 - uncertainty * 1.28)',
   "expect_red_contains": "3.6"},
  {"module_id": "3.5",
   "fault": "progress requirement removed so the unscaled indirect plan is the denominator again",
   "file": "app/simulation/models_ext.py",
   "old": '    pct = si["actualPctComplete"] / 100\n    planned = si["indirectCostPlan"] * pct',
   "new": '    pct = 1.0\n    planned = si["indirectCostPlan"]',
   "expect_red_contains": "3.5"},
  {"module_id": "3.9",
   "fault": "negative material cost domain guard removed, restoring the floor-to-green defect",
   "file": "app/simulation/models_ext.py",
   "old": '        (si["materialCostCurrent"], lambda v: v >= 0,',
   "new": '        (si["materialCostCurrent"], lambda v: True or v >= 0,',
   "expect_red_contains": "3.9"},
  {"module_id": "3.3",
   "fault": "earned-hours rate numerator and denominator swapped",
   "file": "app/simulation/models_ext.py",
   "old": 'rate = round2(((pct / 100) * planned) / actual)',
   "new": 'rate = round2(actual / ((pct / 100) * planned))',
   "expect_red_contains": "3.3"},
]

rows = inject(FAULTS, "test_run19_category_3.py")
write_faults(pathlib.Path("/home/user/LinPRojectRadar/server/tools/run17/categories/category_3_faults.csv"), rows)
for r in rows:
    print(r["module_id"], r["test_turned_red"], "|", r["bytes_changed"], "|", r["red_test_name"][:110])
print("ALL RED:", all_red(rows))
