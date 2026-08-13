import sys, pathlib
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools")
sys.path.insert(0, str(HERE / "run17"))
from fault_harness import inject, write_faults, all_red

# NOTE ON THREE FAULTS THAT WERE TRIED AND REPLACED, recorded rather than hidden.
#
# 1. Removing the Pythagorean renormalisation, the spherical renormalisation and the Fermatean
#    shrinking loop each changed NOTHING. That is not a weak test: sweeping each module's own
#    input map showed the constraint is never exceeded, so all three guards are unreachable dead
#    code and admissibility holds by construction of the map rather than by the guard. The
#    finding was added to the suite as three explicit checks and the faults were replaced with
#    mutations of the quantities those modules actually report.
# 2. Removing the rough-set empty-evidence abstention CRASHES on a division by zero, so no
#    RESULT line is printed and the harness refused to score it a red. Replaced with the
#    supermajority boundary.
# 3. Dropping the frame intersection from the Dempster combination CRASHES, because the total
#    conflict state carries no mass for belief to be taken over. Replaced with the reliability
#    discount, which is the operation that governs how ignorance is handled.

FAULTS = [
  {"module_id": "7.10",
   "fault": "Pythagorean document-risk adjustment direction reversed, so worse document evidence raises membership and lowers non-membership",
   "file": "app/simulation/models_fuzzy.py",
   "old": '    adj_mu = mu * (1 - doc * 0.3)\n    adj_nu = min(1, nu + doc * 0.3)',
   "new": '    adj_mu = mu * (1 + doc * 0.3)\n    adj_nu = max(0, nu - doc * 0.3)',
   "expect_red_contains": "7.10"},
  {"module_id": "7.16",
   "fault": "fuzzy admissibility violation: the spherical hesitancy inflated so the triple leaves the unit ball",
   "file": "app/simulation/models_fuzzy.py",
   "old": '    pi = math.sqrt(max(0, 1 - mu * mu - nu * nu))\n    score = mu - nu',
   "new": '    pi = 0.99\n    score = mu - nu',
   "expect_red_contains": "7.16"},
  {"module_id": "7.17",
   "fault": "Fermatean hesitancy exponent changed from a cube root to a square root",
   "file": "app/simulation/models_fuzzy.py",
   "old": '    pi = (max(0, 1 - mu ** 3 - nu ** 3)) ** (1 / 3)',
   "new": '    pi = (max(0, 1 - mu ** 3 - nu ** 3)) ** (1 / 2)',
   "expect_red_contains": "7.17"},
  {"module_id": "7.1",
   "fault": "Dempster ignorance treated as conflict: the reliability discount stops returning the freed mass to the frame, so discounting destroys mass instead of moving it to ignorance",
   "file": "tools/run17/oracle/oracles_cat_7.py",
   "old": '    out[theta] = 1.0 - alpha + alpha * mass.get(theta, 0.0)',
   "new": '    out[theta] = alpha * mass.get(theta, 0.0)',
   "expect_red_contains": "7.1"},
  {"module_id": "7.2",
   "fault": "rough set lower approximation admits classes not fully contained in the target set",
   "file": "tools/run17/oracle/oracles_cat_7.py",
   "old": '        if cls <= x:\n            lower |= cls',
   "new": '        if cls & x:\n            lower |= cls',
   "expect_red_contains": "7.2"},
  {"module_id": "7.2",
   "fault": "rough set supermajority boundary raised beyond one, so no state can ever enter the lower approximation",
   "file": "app/simulation/models_evc.py",
   "old": '    lower = [s for s in states if counts[s] / total > 0.75]',
   "new": '    lower = [s for s in states if counts[s] / total > 1.5]',
   "expect_red_contains": "7.2"},
  {"module_id": "7.8",
   "fault": "belief rule base no-rule fallback restored, so an unactivated rule base still concludes",
   "file": "app/simulation/models_evc.py",
   "old": '    if not matched:\n        # D1. Every rule above is conditioned on an EVM state, so no EVM means no rule fires.',
   "new": '    if not matched:\n        matched = [{"id": "R0", "desc": "fallback", "condition": True, "belief": {"Green": 0.34, "Amber": 0.33, "Red": 0.33}, "weight": 0.5}]\n    if False:\n        # D1. Every rule above is conditioned on an EVM state, so no EVM means no rule fires.',
   "expect_red_contains": "7.8"},
  {"module_id": "7.19",
   "fault": "the single-project CRITIC-TOPSIS fallback restored, so one project is treated as a set of alternatives",
   "file": "app/simulation/models_fuzzy.py",
   "old": '    return insufficient(\n        "CRITIC_TOPSIS",',
   "new": '    if si.get("cpi"):\n        return {"method_class": "CRITIC_TOPSIS", "status_color": "Amber", "topsis_score": 0.5}\n    return insufficient(\n        "CRITIC_TOPSIS",',
   "expect_red_contains": "7.19"},
  {"module_id": "7.14",
   "fault": "entropy normalisation inverted, so the reported entropy leaves nought to one",
   "file": "app/simulation/models_fuzzy.py",
   "old": '    normalized = entropy / math.log2(4)',
   "new": '    normalized = entropy * math.log2(4)',
   "expect_red_contains": "7.14"},
  {"module_id": "7.13",
   "fault": "type-2 footprint bounds swapped, so the lower membership exceeds the upper",
   "file": "app/simulation/models_fuzzy.py",
   "old": '    lower = max(0, primary - uncertainty * 0.5)\n    upper = min(1, primary + uncertainty * 0.5)',
   "new": '    upper = max(0, primary - uncertainty * 0.5)\n    lower = min(1, primary + uncertainty * 0.5)',
   "expect_red_contains": "7.13"},
  {"module_id": "7.15",
   "fault": "possibility and necessity ordering inverted, so necessity exceeds possibility",
   "file": "app/simulation/models_fuzzy.py",
   "old": '    necessity = {k: max(0, v - 0.3) for k, v in possibility.items()}',
   "new": '    necessity = {k: min(1, v + 0.3) for k, v in possibility.items()}',
   "expect_red_contains": "7.15"},
  {"module_id": "7.18",
   "fault": "MARCOS anti-ideal reference inflated eightfold, so the utility degrees no longer measure distance from the worst option and the score loses its monotonicity in the criteria",
   "file": "app/simulation/models_fuzzy.py",
   "old": '        s_anti += _clamp01(c["anti"] / ideal) * c["weight"]',
   "new": '        s_anti += _clamp01(c["anti"] / ideal) * c["weight"] * 8.0',
   "expect_red_contains": "7.18"},
]

rows = inject(FAULTS, "test_run19_category_7.py")
write_faults(pathlib.Path("/home/user/LinPRojectRadar/server/tools/run17/categories/category_7_faults.csv"), rows)
for r in rows:
    print(r["module_id"], r["test_turned_red"], "|", r["bytes_changed"], "|", r["red_test_name"][:110])
print("ALL RED:", all_red(rows))
