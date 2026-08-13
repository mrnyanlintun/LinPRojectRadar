import sys, pathlib
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools")
sys.path.insert(0, str(HERE / "run17"))
from fault_harness import inject, write_faults, all_red
FAULTS = [
  {"module_id":"2.3","fault":"buffer penetration denominator changed from the original buffer to what remains",
   "file":"app/simulation/canonical.py",
   "old":'"pct_buffer_consumed": (original - remaining) / original * 100.0,',
   "new":'"pct_buffer_consumed": (original - remaining) / max(remaining, 1e-9) * 100.0,',
   "expect_red_contains":"2.3"},
  {"module_id":"2.11","fault":"critical path index operator swapped from mean to sum",
   "file":"app/simulation/models_ext.py",
   "old":"index = _round3((progress_ratio + cpi_schedule) / 2)",
   "new":"index = _round3(progress_ratio + cpi_schedule)",
   "expect_red_contains":"2.11"},
  {"module_id":"2.6","fault":"S-curve domain guard on planned progress removed, restoring the out-of-domain banding",
   "file":"app/simulation/models_ext.py",
   "old":'(si["plannedPctComplete"], lambda v: 0 <= v <= 100,',
   "new":'(si["plannedPctComplete"], lambda v: True or 0 <= v <= 100,',
   "expect_red_contains":"2.6"},
  {"module_id":"2.5","fault":"negative consumed float guard removed, so the schedule may hand float back",
   "file":"app/simulation/models_ext.py",
   "old":'if num(si.get("consumedFloat"), None) is None or si["consumedFloat"] < 0:',
   "new":'if False:',
   "expect_red_contains":"2.5"},
  {"module_id":"2.2","fault":"line of balance separation minimum replaced by its maximum",
   "file":"app/simulation/canonical.py",
   "old":"minimum, at_location = min(separations, key=lambda pair: pair[0])",
   "new":"minimum, at_location = max(separations, key=lambda pair: pair[0])",
   "expect_red_contains":"2.2"},
]
rows = inject(FAULTS, "test_run19_category_2.py")
write_faults(pathlib.Path("/home/user/LinPRojectRadar/server/tools/run17/categories/category_2_faults.csv"), rows)
for r in rows: print(r["module_id"], r["test_turned_red"], "|", r["bytes_changed"], "|", r["red_test_name"][:110])
print("ALL RED:", all_red(rows))
