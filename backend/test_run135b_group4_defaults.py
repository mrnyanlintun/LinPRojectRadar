"""Run 135B — executable proof for Group 4 (favourable defaults and zero-as-absent).

Each check names the defect it forbids. Run with:  python backend/test_run135b_group4_defaults.py
Exit status 0 = all checks pass; 1 = at least one failed. No network, no model key.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from governance import PCEIFGovernanceRouter  # noqa: E402

FAILED = []


def check(ok, label):
    print(("PASS  " if ok else "FAIL  ") + label)
    if not ok:
        FAILED.append(label)


# ---------------------------------------------------------------- S2
# backend/governance.py:24 — sig.get("status_color", "Green") made {} Green, and a
# lowercase "red" counted under counts["red"] which the ladder never read.
r = PCEIFGovernanceRouter().synthesize([{}])
check(r["final_status"] != "Green", "S2: a signal with no status_color does not publish Green")
check(r["final_status"] == "Indeterminate", "S2: a signal with no status_color abstains")
check(bool(r.get("needs")), "S2: the abstention says what it needs")

r = PCEIFGovernanceRouter().synthesize([{"status_color": "red", "method_class": "X"}])
check(r["final_status"] != "Green", "S2: a lowercase 'red' signal does not publish Green")
check(r["final_status"] == "Indeterminate", "S2: a non-canonical status abstains")

r = PCEIFGovernanceRouter().synthesize([{"status_color": "Red", "method_class": "X"},
                                        {"status_color": "Amber", "method_class": "Y"}])
check(r["final_status"] == "Red-Review", "S2: canonical Red+Amber still routes Red-Review")
r = PCEIFGovernanceRouter().synthesize([{"status_color": "Green", "method_class": "X"}])
check(r["final_status"] == "Green", "S2: an all-Green canonical array still routes Green")
r = PCEIFGovernanceRouter().synthesize([{"status_color": "Green"}],
                                       human_override={"target_status": "Fuchsia"})
check(r["final_status"] == "Indeterminate", "S2: an override naming an undefined status abstains, not Green")


if __name__ == "__main__":
    print("\n%d checks, %d failed" % (8, len(FAILED)))
    sys.exit(1 if FAILED else 0)
