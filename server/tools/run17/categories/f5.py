import sys, pathlib
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools")
sys.path.insert(0, str(HERE / "run17"))
from fault_harness import inject, write_faults, all_red

FAULTS = [
  # Specification 30 requires a queueing denominator or operator defect among the injections.
  {"module_id": "5.6",
   "fault": "queueing denominator defect: utilisation divided by the servers alone rather than by server time",
   "file": "app/simulation/canonical.py",
   "old": '"utilisation": service / (servers * horizon),',
   "new": '"utilisation": service / servers,',
   "expect_red_contains": "5.6"},
  # NOTE. Removing the M/M/1 stability guard was tried first and CRASHES on a division by
  # zero at a utilisation of exactly one, so the suite printed no RESULT line and the harness
  # correctly refused to score it a red. Replaced with an operator defect in the queue-length
  # formula, which leaves the suite running and breaks Little's Law by name.
  {"module_id": "5.6",
   "fault": "M/M/1 queue-length operator defect: the number in queue formula loses its square",
   "file": "tools/run17/oracle/oracles_cat_5.py",
   "old": '"Lq": rho ** 2 / (1 - rho), "Wq": rho / (mu - lam)}',
   "new": '"Lq": rho / (1 - rho), "Wq": rho / (mu - lam)}',
   "expect_red_contains": "5.6"},
  {"module_id": "5.1",
   "fault": "DSM propagation operator transposed, so the wave travels the wrong way down the dependency",
   "file": "tools/run17/oracle/oracles_cat_5.py",
   "old": 'return [sum(matrix[i][j] * vector[j] for j in range(len(vector)))\n            for i in range(len(matrix))]',
   "new": 'return [sum(matrix[j][i] * vector[j] for j in range(len(vector)))\n            for i in range(len(matrix))]',
   "expect_red_contains": "5.1"},
  {"module_id": "5.5",
   "fault": "rework feedback missing-count guard removed, so an absent count contributes zero again",
   "file": "app/simulation/models_doc.py",
   "old": '    if not check_inputs(si, ("cpi", "rfiCount", "changeOrderCount")):\n        return insufficient(\n            "Rework_Feedback",',
   "new": '    si = {"rfiCount": 0, "changeOrderCount": 0, **si}\n    if not check_inputs(si, ("cpi",)):\n        return insufficient(\n            "Rework_Feedback",',
   "expect_red_contains": "5.5"},
  {"module_id": "5.2",
   "fault": "sensitivity absent-driver guard removed, so a missing document risk score reads as zero sensitivity",
   "file": "app/simulation/models_doc.py",
   "old": '    if not check_inputs(si, ("bac", "ev", "ac", "pv", "cpi", "spi", "docRiskScore")):\n        return insufficient("Sensitivity_Analysis")',
   "new": '    si = {"docRiskScore": 0, **si}\n    if not check_inputs(si, ("bac", "ev", "ac", "pv", "cpi", "spi")):\n        return insufficient("Sensitivity_Analysis")',
   "expect_red_contains": "5.2"},
  {"module_id": "5.7",
   "fault": "the single-time-step guard removed, so a model with one point in time is accepted as a run over time",
   "file": "app/simulation/canonical.py",
   "old": '    if len(steps) < 2:',
   "new": '    if len(steps) < 1:',
   "expect_red_contains": "5.7"},
  # NOTE. Removing the locked-holdout refusal was tried first. It does NOT turn the suite red,
  # because a split of LOCKED_HOLDOUT is then caught one branch later by the rule that a split
  # the module does not recognise is refused, so the module still abstains and the check still
  # holds. That is defence in depth working as intended and it is recorded here rather than
  # presented as a red. Replaced with the expectation operator, which decides the recommendation.
  {"module_id": "5.4",
   "fault": "scenario expectation operator reversed, so the action with the HIGHEST expected cost is recommended",
   "file": "app/simulation/canonical.py",
   "old": '    best = min(expectations, key=lambda a: expectations[a])',
   "new": '    best = max(expectations, key=lambda a: expectations[a])',
   "expect_red_contains": "5.4"},
  {"module_id": "5.8",
   "fault": "discrete event throughput index inverted, so more interruption reads as more throughput",
   "file": "app/simulation/models_doc.py",
   "old": 'throughput = js_round((1 / (1 + interruption)) * 1000) / 1000',
   "new": 'throughput = js_round((1 + interruption) * 1000) / 1000',
   "expect_red_contains": "5.8"},
]

rows = inject(FAULTS, "test_run19_category_5.py")
write_faults(pathlib.Path("/home/user/LinPRojectRadar/server/tools/run17/categories/category_5_faults.csv"), rows)
for r in rows:
    print(r["module_id"], r["test_turned_red"], "|", r["bytes_changed"], "|", r["red_test_name"][:110])
print("ALL RED:", all_red(rows))
