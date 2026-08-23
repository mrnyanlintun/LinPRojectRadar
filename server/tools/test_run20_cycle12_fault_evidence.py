"""
RUN 20, CYCLE 12 -- the fault-injection evidence is complete, and the anti-fossilization register
is complete.

THE TWO EVIDENCE GAPS THIS RUN CARRIED OPEN SINCE CYCLE 3, CHECKED HERE RATHER THAN ASSERTED.

GAP ONE. The cycle-3 fault injections M13 to M21 existed only as narrative. The register says
plainly that transcribing the prose would not close it, because a transcription proves that
somebody typed it. run20_cycle12_cycle3_fault_battery.py reruns all nine against production,
confirms the bytes changed, runs the named suite in its own process, and emits the rows. THIS
suite proves the emitted rows are the nine, that every one landed, and that every one was
detected and restored. It reads the artifact; it does not rerun the battery, because the battery
edits production files and must never execute inside a full sweep.

GAP TWO. The anti-fossilization register held only cycle-8 entries and one open row. Cycles 1 to
7 were never back-transcribed. This suite requires an entry for every cycle from 1 to 12 and
requires the cycle-3 row to be CLOSED rather than OPEN, so the gap cannot be quietly reopened by
deletion either.

THE UNION OF THE FAULT EVIDENCE IS CHECKED ACROSS BOTH FILES. M1 to M28 must be present between
the Run-20 results file and the cycle-3 file, with no identifier appearing twice and none
missing, so a row cannot be lost by being moved.

TEST AND AUDIT ONLY.
"""

from __future__ import annotations

import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "run17"))

from audit_harness import Audit                                    # noqa: E402

ROOT = HERE.parents[1]

# --- CAMPAIGN SAFETY (Run 54, phase A) -----------------------------------------------------
# THE START-AND-END DIRTY-TREE GUARD. A campaign must not BEGIN on a dirty tree: Run 53
# established that a leaked fault is snapshotted from disk by the next campaign, faithfully
# restored by its `finally`, and thereby CERTIFIED by its own passing assertion. An end-only
# check cannot see that, because the leak began in an earlier process. See
# server/tools/campaign_safety.py for the full mechanism and the proof.
import sys as _cs_sys, pathlib as _cs_pl                                       # noqa: E402
_cs_sys.path.insert(0, str(_cs_pl.Path(ROOT) / "server" / "tools"))
from campaign_safety import (arm as _cs_arm, restore_guard, head_text,          # noqa: E402,F401
                             snapshot_text, CampaignTreeDirty)
_cs_arm(_cs_pl.Path(ROOT), "test_run20_cycle12_fault_evidence.py",
        # RUN 55, PHASE B, section 8 item 1: THE ALLOW LIST IS TIGHTENED TO DECLARED
        # OUTPUTS. Run 54 derived this list by taking every `code_audit/` literal in the
        # file, which swept in READ-ONLY inputs and fault TARGETS as well as outputs. An
        # allow entry is a promise that the campaign is designed to write that path;
        # naming a file it only reads widens the guard for nothing. Established by
        # execution: this file contains no write to code_audit at all.
        allow=[])
# -------------------------------------------------------------------------------------------
CYCLE3 = ROOT / "code_audit" / "run20_cycle12_cycle3_fault_injection.csv"
RUN20 = ROOT / "code_audit" / "run20_fault_injection_results.csv"
REGISTER = ROOT / "code_audit" / "run20_anti_fossilization_register.csv"

A = Audit("run 20 cycle 12 fault evidence and anti-fossilization completeness", {})

EXPECTED_CYCLE3 = [f"M{i}" for i in range(13, 22)]


def read(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    c3 = read(CYCLE3)
    A.check("GAP1", "the cycle-3 fault-injection artifact exists", bool(c3),
            f"{CYCLE3.name} is absent or empty")
    if c3:
        ids = [r["injection_id"] for r in c3]
        A.check("GAP1", "it holds exactly the nine cycle-3 injections M13 to M21",
                ids == EXPECTED_CYCLE3, f"got {ids}")
        not_landed = [r["injection_id"] for r in c3 if r["bytes_changed_confirmed"] != "yes"]
        A.check("GAP1", "every one of the nine changed bytes in production", not not_landed,
                f"did not land: {not_landed}")
        vacuous = [r["injection_id"] for r in c3
                   if "VACUOUS" in r["named_check_that_went_red"].upper()]
        A.check("GAP1", "no cycle-3 guard stayed green under its deliberate violation",
                not vacuous, f"vacuous: {vacuous}")
        unrestored = [r["injection_id"] for r in c3 if r["restored_and_green"] != "yes"]
        A.check("GAP1", "every injection was restored and the suite proved green again",
                not unrestored, f"not restored: {unrestored}")
        A.check("GAP1", "every row names the production file it edited",
                all(r.get("target_file") for r in c3))

    run20 = read(RUN20)
    A.check("GAP1", "the Run-20 fault-injection results file is present", bool(run20))
    union = [r["injection_id"] for r in run20] + [r["injection_id"] for r in c3]
    A.check("GAP1", "no injection identifier appears twice across the two files",
            len(union) == len(set(union)),
            f"duplicated: {sorted({i for i in union if union.count(i) > 1})}")
    missing = [f"M{i}" for i in range(1, 29) if f"M{i}" not in set(union)]
    A.check("GAP1", "M1 to M28 are all accounted for between the two files", not missing,
            f"missing: {missing}")

    reg = read(REGISTER)
    A.check("GAP2", "the anti-fossilization register is present", bool(reg))
    # RUN 21. The register is APPEND-ONLY across runs, and later runs do not have numbered
    # cycles: Run 21 is a single qualification pass and labels its cycle column with what it was.
    # This check is about RUN 20's twelve cycles, so it reads Run-20 rows, and the print at the
    # end no longer assumes every cycle label in the whole file parses as an integer -- which is
    # what it did, and it CRASHED the suite rather than failing it when Run 21's rows arrived.
    # The strict runner caught that as a FAIL because no canonical RESULT line was printed, which
    # is the Run-20 queue item 6 question answered by demonstration.
    run20_rows = [r for r in reg if str(r.get("run", "")).strip() == "20"]
    A.check("GAP2", "the register still carries the Run-20 rows", bool(run20_rows),
            f"{len(reg)} rows, {len(run20_rows)} of them Run 20")
    cycles = {str(r["cycle"]).strip() for r in run20_rows}
    all_cycle_labels = {str(r["cycle"]).strip() for r in reg}
    absent = [str(c) for c in range(1, 13) if str(c) not in cycles]
    A.check("GAP2", "every Run-20 cycle from one to twelve has at least one register entry",
            not absent, f"no entry for cycle(s): {absent}")
    open_rows = [r for r in reg if str(r["status"]).strip().upper() == "OPEN"]
    A.check("GAP2", "the cycle-3 evidence-only-in-prose row is no longer open",
            not [r for r in open_rows if "M13" in r["what_the_instrument_did"]
                 or "M13" in r.get("instrument", "")],
            f"still open: {[r.get('instrument') for r in open_rows]}")
    A.check("GAP2", "every register entry names the instrument, the defect class and the "
            "resolution",
            all(r.get("instrument") and r.get("defect_class") and r.get("resolution")
                for r in reg))
    vacuity_rows = [r for r in reg if r["defect_class"] not in ("GUARD_WORKED",)]
    A.check("GAP2", "the register records the vacuous guards this run found, not only the ones "
            "that worked", len(vacuity_rows) >= 9,
            f"only {len(vacuity_rows)} non-GUARD_WORKED entries")

    print(f"cycle-3 injections: {len(c3)}; Run-20 injections: {len(run20)}; "
          f"register entries: {len(reg)} covering Run-20 cycles "
          f"{sorted(cycles, key=lambda c: int(c))}; all cycle labels present in the register: "
          f"{sorted(all_cycle_labels)}")


if __name__ == "__main__":
    main()
    sys.exit(A.finish())
