import sys, pathlib
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools")
sys.path.insert(0, str(HERE / "run17"))
from fault_harness import inject, write_faults, all_red

FAULTS = [
  # Specification 30 requires a regulatory rule-version mismatch among the injections. The
  # snapshot edition is mutated in the ORACLE, because the oracle is the only place in the
  # instrument that records which edition anything was evaluated against: production records
  # none, which is itself finding 8.3/edition-recorded.
  {"module_id": "8.3",
   "fault": "regulatory rule-version mismatch: the committed A-11 edition replaced by a superseded one",
   "file": "tools/run17/oracle/oracles_cat_8.py",
   "old": '"cite": "OMB Circular A-11, edition dated 2025-08-29",',
   "new": '"cite": "OMB Circular A-11, edition dated 2019-06-28",',
   "expect_red_contains": "8.3"},
  {"module_id": "8.7",
   "fault": "OSHA incidence-rate constant changed from 200,000 to 100,000 hours",
   "file": "tools/run17/oracle/oracles_cat_8.py",
   "old": 'return recordable_cases * 200000.0 / employee_hours_worked',
   "new": 'return recordable_cases * 100000.0 / employee_hours_worked',
   "expect_red_contains": "8.7"},
  {"module_id": "8.7",
   "fault": "the meeting-silence guard removed, so silence in a meeting becomes a record of no incidents again",
   "file": "app/simulation/models_doc.py",
   "old": '    if is_derived and si.get("oshaIncidentRate") is None \\\n            and not si["safetyIncidentsDiscussed"] > 0:',
   "new": '    if False:',
   "expect_red_contains": "8.7"},
  {"module_id": "8.9",
   "fault": "the worst contractor rating replaced by the mean, so a bad quality rating is averaged away",
   "file": "app/simulation/models_doc.py",
   "old": '    worst = min(rated)',
   "new": '    worst = sum(rated) / len(rated)',
   "expect_red_contains": "8.9"},
  {"module_id": "8.6",
   "fault": "the inspected-count default of twenty restored, fabricating a denominator for every project",
   "file": "app/simulation/models_doc.py",
   "old": '    inspected = si.get("itemsInspected")\n    failed = si.get("itemsFailed")',
   "new": '    inspected = si.get("itemsInspected", 20) or 20\n    failed = si.get("itemsFailed", 0) or 0',
   "expect_red_contains": "8.6"},
  {"module_id": "8.8",
   "fault": "the environmental compliance rate domain guard removed, so a rate outside nought to a hundred bands",
   "file": "app/simulation/models_doc.py",
   "old": '    if rate < 0 or rate > 100:',
   "new": '    if False:',
   "expect_red_contains": "8.8"},
  {"module_id": "8.2",
   "fault": "the negative cost index guard removed, restoring the negative-overrun-reads-green defect",
   "file": "app/simulation/models_gov.py",
   "old": '    if si["cpi"] <= 0:\n        return insufficient(\n            "FAR_Threshold",',
   "new": '    if si["cpi"] == 0:\n        return insufficient(\n            "FAR_Threshold",',
   "expect_red_contains": "8.2"},
  {"module_id": "8.1",
   "fault": "the escalation authority replaced by the routine one, so a high-impact action bypasses the required human authority",
   "file": "app/simulation/models_decision.py",
   "old": '        authority = "Program director / PMO lead"',
   "new": '        authority = "Project manager / Controls lead"',
   "expect_red_contains": "8.1"},
]

rows = inject(FAULTS, "test_run19_category_8.py")
write_faults(pathlib.Path("/home/user/LinPRojectRadar/server/tools/run17/categories/category_8_faults.csv"), rows)
for r in rows:
    print(r["module_id"], r["test_turned_red"], "|", r["bytes_changed"], "|", r["red_test_name"][:110])
print("ALL RED:", all_red(rows))
