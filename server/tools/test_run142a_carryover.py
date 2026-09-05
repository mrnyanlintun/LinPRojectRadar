"""Run 142A. A category whose every module abstained must carry its module rows to the card.

Standalone check-script, not pytest. Run with cwd = <worktree>/server.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import spec_projection as sp

# --- fixture -------------------------------------------------------------------------------
# A3 Cost Risk: four modules RAN and ABSTAINED, each with a stated reason. Because no module
# banded, compute.py builds no A3 key in category_statuses -- exactly PRJ-002 period 2's shape.
A3_ABSTAINED = [
    {"module_id": "A3.1", "category": "A3", "abstention_reason": "awaiting a cost risk model"},
    {"module_id": "A3.2", "category": "A3",
     "abstention_reason": "beneath the configured exposure floor"},
    {"module_id": "A3.3", "category": "A3",
     "abstention_reason": "awaiting a contingency drawdown history"},
    {"module_id": "A3.4", "category": "A3", "abstention_reason": "awaiting a risk register"},
]
A1_COMPUTED = [{"module_id": "A1.1", "category": "A1", "status_color": "Green"}]
ROW_CATS_WITH_A1 = {"A1": {"status": "Green", "state": "computed",
                           "contributes_to_project_status": True}}


def case(name, row_cats, row_modules, row_abstained):
    merged = sp.merge_python_row(None, row_modules, row_abstained, row_cats, None)
    a3_mods = [m for m in merged["module_results"]
               if sp._python_category_of(m, m.get("module_id")) == "A3"]
    a3_abs = [a for a in merged["abstained"]
              if sp._python_category_of(a, a.get("module_id")) == "A3"]
    basis = merged["project_status_basis"]
    det = {d["category"]: d for d in basis["required_missing_detail"]}
    print("--- %s" % name)
    print("    A3 module rows projected: %d" % len(a3_mods))
    print("    A3 abstention rows projected: %d  reasons=%s"
          % (len(a3_abs), [a.get("abstention_reason") for a in a3_abs]))
    print("    A3 carries a posture: %s"
          % bool((merged["category_statuses"].get("A3") or {}).get("status")))
    print("    project_status: %r  official=%s" % (merged["project_status"], basis["official"]))
    print("    A3 required_missing_detail: %s" % (det.get("A3"),))
    print("    status_reason: %r" % (basis["status_reason"],))
    return merged, len(a3_abs), det.get("A3")


fail = 0
# CASE 1: every A3 module ran and abstained. A1 banded, so `filled` is non-empty.
m1, n1, d1 = case("CASE 1  A3: four modules ran and abstained",
                  ROW_CATS_WITH_A1, A1_COMPUTED, A3_ABSTAINED)
# CASE 2: no A3 module dispatched at all.
m2, n2, d2 = case("CASE 2  A3: no module dispatched", ROW_CATS_WITH_A1, A1_COMPUTED, [])

print()
if n1 != 4:
    print("FAIL requirement 1: A3's four abstentions projected %d rows, expected 4" % n1)
    fail += 1
else:
    print("PASS requirement 1: all four abstention rows with reasons reach the projection")
if n2 != 0:
    print("FAIL: case 2 should project no A3 rows, got %d" % n2)
    fail += 1
if (m1["category_statuses"].get("A3") or {}).get("status") or \
   (m2["category_statuses"].get("A3") or {}).get("status"):
    print("FAIL requirement 4: a posture was manufactured for A3")
    fail += 1
else:
    print("PASS requirement 4a: no posture manufactured for A3 in either case")
if m1["project_status"] != m2["project_status"] or m1["project_status_basis"]["official"]:
    print("FAIL requirement 4: project status differs or became official: %r vs %r"
          % (m1["project_status"], m2["project_status"]))
    fail += 1
else:
    print("PASS requirement 4b: project status withheld and identical in both cases (%r)"
          % (m1["project_status"],))
if d1 == d2:
    print("FAIL requirement 2: the two cases are indistinguishable in "
          "required_missing_detail:\n    %s" % (d1,))
    fail += 1
else:
    print("PASS requirement 2: the two cases differ in required_missing_detail")
    print("    abstained : %s" % (d1,))
    print("    never ran : %s" % (d2,))

# ------------------------------------------------- THE THREE INVARIANTS THAT COULD BREAK THIS
#
# INVARIANT A -- NO DOUBLE-COUNTING. The one way this fix could go wrong is by carrying Python
# rows for a category the SPECIFICATION LAYER ANSWERED, which section 2.3 makes the source. The
# carry-over set excludes `answered` by construction; this measures it. A3 is given a stored
# specification reading that ABSTAINED -- a stated refusal, which is a reading -- while the
# Python row still holds its four abstentions.
SPEC_A3_ANSWERED = {"module_results": [], "abstained": [],
                    "category_statuses": {"A3": {"state": sp.sa.ABSTAINED,
                                                 "reason": "the specification declined"}},
                    "specification_categories_called": ["A3"]}
mA = sp.merge_python_row(SPEC_A3_ANSWERED, A1_COMPUTED, A3_ABSTAINED, ROW_CATS_WITH_A1, None)
aA = [a for a in mA["abstained"]
      if sp._python_category_of(a, a.get("module_id")) == "A3"]
print()
print("INVARIANT A -- a category the specification layer ANSWERED is not carried:")
print("    A3 spec state: %r; Python abstention rows carried into it: %d"
      % ((mA["category_statuses"]["A3"] or {}).get("state"), len(aA)))
print("    A3 entry still the specification's own: %s"
      % (not mA["category_statuses"]["A3"].get("modules_ran_without_band")))
if aA:
    print("FAIL invariant A: %d Python rows were carried into a category the specification "
          "layer answered -- the reading is being doubled" % len(aA))
    fail += 1
elif mA["category_statuses"]["A3"].get("modules_ran_without_band"):
    print("FAIL invariant A: the specification layer's answered entry was annotated"); fail += 1
else:
    print("PASS invariant A: answered categories are excluded; nothing is doubled")

# INVARIANT B -- NO CARRIED ROW CAN BECOME AN ADVERSE READING. `_adverse_readings` whitelists
# Yellow/Amber/Red on `module_results`. `registry.record` files a module to `abstained` only
# when it is insufficient OR its status_color is None, and the entry it builds copies neither
# status_color nor any band field, so a carried abstention cannot carry one. Measured, not
# assumed -- models.py:383-384 records a historical case of a status_color without a band.
from app.decision_brief import _adverse_readings                      # noqa: E402
advB = _adverse_readings(m1["category_statuses"], m1["module_results"])
carried_bands = [a.get("status_color") for a in m1["abstained"]
                 if sp._python_category_of(a, a.get("module_id")) == "A3"]
print()
print("INVARIANT B -- a carried abstention cannot become an adverse reading:")
print("    status_color on the four carried A3 rows: %r" % (carried_bands,))
print("    adverse readings composed from this projection: %d" % len(advB))
if any(b for b in carried_bands):
    print("FAIL invariant B: a carried abstention carries a band"); fail += 1
elif advB:
    print("FAIL invariant B: %d adverse readings appeared: %s" % (len(advB), advB)); fail += 1
else:
    print("PASS invariant B: no band on any carried row, no adverse reading composed")

# INVARIANT C -- THE COUNTS THAT DELIBERATELY MOVE, stated rather than left to be discovered.
print()
print("INVARIANT C -- counts that grow BECAUSE the rows now travel (reported, not hidden):")
print("    projected abstained rows, all-abstained case : %d (was %d before the carry-over)"
      % (len(m1["abstained"]), len(m2["abstained"])))
print("    projected module_results                     : %d (unchanged)"
      % len(m1["module_results"]))
print("    None of these is a band, threshold, weight or rule. The abstained count the card")
print("    prints, the brief gate's admissible-figure counts and decision_brief's")
print("    modules_computed read these lists, so each grows by the number of rows carried.")

print()
print("RESULT:", "FAIL" if fail else "PASS", "(%d failing checks)" % fail)
sys.exit(1 if fail else 0)
