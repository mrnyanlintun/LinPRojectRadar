import sys, pathlib
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools")
sys.path.insert(0, str(HERE / "run17"))
from fault_harness import inject, write_faults, all_red

# The oracle faults are injected into the ORACLE, not into production, because for the four
# concept-only modules the oracle IS the scientific object under test: production never runs.
# Specification 30 requires a wrong LP optimum, a dominated Pareto point admitted and a regret
# defect to each turn a named test red, and those live in the oracle here.
FAULTS = [
  {"module_id": "10.2",
   "fault": "wrong LP optimum: feasibility tolerance widened so infeasible vertices are admitted",
   "file": "tools/run17/oracle/oracles_cat_10.py",
   "old": 'return all(sum(c * v for c, v in zip(coef, pt)) <= rhs + 1e-9 for coef, rhs in rows)',
   "new": 'return all(sum(c * v for c, v in zip(coef, pt)) <= rhs + 1e3 for coef, rhs in rows)',
   "expect_red_contains": "10.2"},
  {"module_id": "10.6",
   "fault": "dominated Pareto point admitted: the strictness requirement dropped from the dominance relation",
   "file": "tools/run17/oracle/oracles_cat_10.py",
   "old": 'return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))',
   "new": 'return all(x <= y for x, y in zip(a, b))',
   "expect_red_contains": "10.6"},
  {"module_id": "10.7",
   "fault": "minimax regret turned into maximax regret, so the worst hedge is chosen",
   "file": "tools/run17/oracle/oracles_cat_10.py",
   "old": 'best = min(max_regret, key=lambda a: (max_regret[a], a))',
   "new": 'best = max(max_regret, key=lambda a: (max_regret[a], a))',
   "expect_red_contains": "10.7"},
  {"module_id": "10.4",
   "fault": "what-if earned-value-exceeds-budget guard removed, so a position with no remaining work is forecast from",
   "file": "app/simulation/models_gov.py",
   "old": '    if si["ev"] > si["bac"]:',
   "new": '    if False:',
   "expect_red_contains": "10.4"},
  {"module_id": "10.7",
   "fault": "regret minimisation made to emit a fixed project-independent choice instead of abstaining",
   "file": "app/simulation/models_gov.py",
   "old": '    return insufficient(\n        "Regret_Minimization",',
   "new": '    return {"method_class": "Regret_Minimization", "status_color": "Amber", "choice": "investigate"} if si.get("cpi") else insufficient(\n        "Regret_Minimization",',
   "expect_red_contains": "10.7"},
  {"module_id": "10.3",
   "fault": "constraint satisfaction boundary made exclusive, so a project exactly on a rule boundary fails it",
   "file": "app/simulation/models_gov.py",
   "old": '{"name": "Cost constraint (CPI ≥ 0.90)", "satisfied": si["cpi"] >= 0.90},',
   "new": '{"name": "Cost constraint (CPI ≥ 0.90)", "satisfied": si["cpi"] > 0.90},',
   "expect_red_contains": "10.3"},
]

rows = inject(FAULTS, "test_run19_category_10.py")
write_faults(pathlib.Path("/home/user/LinPRojectRadar/server/tools/run17/categories/category_10_faults.csv"), rows)
for r in rows:
    print(r["module_id"], r["test_turned_red"], "|", r["bytes_changed"], "|", r["red_test_name"][:110])
print("ALL RED:", all_red(rows))
