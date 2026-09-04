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


# ---------------------------------------------------------------- S3
# backend/simulations.py:21 — `signal_inputs.get("spi") or 1.0` and its siblings
# read a real zero as absent, so run_all({}) and run_all(all-zeros) both returned
# the same fully-scored Red/Green/Green/Red/Amber verdict.
import simulations  # noqa: E402

empty = simulations.run_all({})
colors_empty = [s["status_color"] for s in empty]
check(colors_empty != ["Red", "Green", "Green", "Red", "Amber"],
      "S3: run_all({}) no longer returns the old fully-scored verdict")
check(all(s["status_color"] == "Indeterminate" for s in empty if s["method_class"] != "DSM_Rework_Propagation"),
      "S3: every input-dependent model abstains on run_all({})")
check(all(s.get("needs") for s in empty if s["method_class"] != "DSM_Rework_Propagation"),
      "S3: each abstention says what it needs")

zeros = simulations.run_all({"spi": 0, "bac": 0, "actualPctComplete": 0})
colors_zeros = [s["status_color"] for s in zeros]
check(colors_zeros != colors_empty,
      "S3: a real zero is not the same as a missing input")
check(all(s["status_color"] != "Indeterminate" for s in zeros),
      "S3: valid zeros are scored, not abstained")
ccpm = next(s for s in zeros if s["method_class"] == "CCPM_Buffer_Health")
check(ccpm["pct_chain_complete"] == 0.0 and ccpm["status_color"] == "Red",
      "S3: actualPctComplete 0 with spi 0 reads 0% complete and bands Red (was 37% via the invented default)")
rcf = next(s for s in zeros if s["method_class"] == "Reference_Class_Forecasting")
check(rcf["rcf_p80_adjusted"] == 0, "S3: BAC 0 gives a zero P80, not the bac=1 stand-in")

# a fully supplied set still scores
full = simulations.run_all({"spi": 0.8, "bac": 10_000_000, "actualPctComplete": 40})
check(all(s["status_color"] in ("Green", "Amber", "Red") for s in full),
      "S3: a complete input set still produces canonical bands")


if __name__ == "__main__":
    print("\n%d checks, %d failed" % (16, len(FAILED)))
    sys.exit(1 if FAILED else 0)
