#!/usr/bin/env python3
"""
RUN 37 DOCUMENTATION-CLOSURE FAULT CAMPAIGN. Four faults, one per failure mode the closure
contract names, each expected to turn ITS OWN NAMED CHECK in
`test_run37_documentation_scope.py` red.

FAULT 2 IS THE ONE THAT MATTERS. It restores the exact overstatement this closure was written to
correct. If the guard cannot detect that sentence coming back, the correction is unguarded and
will drift back in, and the whole closure accomplished nothing.

RULES ENFORCED ON ITSELF, unchanged from every earlier campaign in this programme:
 * baseline fully GREEN before anything is injected -- RESULT: N/N, not merely free of one name;
 * an injection that does not change bytes on disk is NOT_APPLIED and is not counted;
 * A CRASH IS NOT ACCEPTED AS RED;
 * the NAMED check must be the one that fails, and its line must carry the intended fragment;
 * restored byte-for-byte and re-verified GREEN.

Writes research/freeze/run37_documentation_scope_campaign.csv.
"""
from __future__ import annotations

import csv
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FREEZE = ROOT / "research" / "freeze"
GUARD = HERE / "test_run37_documentation_scope.py"
RECORD = FREEZE / "INSTRUMENT_FINAL_FREEZE_RECORD.json"
REPORT = FREEZE / "INSTRUMENT_FINAL_FREEZE_REPORT.md"

PH = "PENDING" + "_FINAL_COMMIT"

FAULTS = [
    (1, "the placeholder is put back into the FINAL RELEASE RECORD",
     (RECORD, '"release_disposition": "FINAL_FREEZE_ACCEPTED",',
      '"release_disposition": "FINAL_FREEZE_ACCEPTED",\n  "exact_final_git_commit": "'
      + PH + '",'),
     "run37doc.record_has_no_placeholder",
     "the FINAL RELEASE RECORD contains no placeholder"),
    (2, "the false repository-wide zero-occurrence sentence is restored to the report",
     (REPORT, "### Scope of the placeholder statement",
      "No `" + PH + "` placeholder is used anywhere in this release.\n\n"
      "### Scope of the placeholder statement"),
     "run37doc.report_makes_no_repository_wide_claim",
     "does not claim the whole repository is free of the placeholder"),
    (3, "the explanation of the historical candidate placeholder is removed",
     # REPOINTED. The first injection removed the tail of the explanatory sentence, but the report
     # carries a SECOND self-reference sentence about the release record, and the check's substring
     # matched that one instead -- so the fault landed in the bytes and the guard stayed green. The
     # injection now removes the explanatory sentence's subject, which is what the check is about.
     (REPORT, "The historical Run-36 freeze-candidate manifest keeps its documented placeholder "
      "because", "The historical manifest is left as it is because"),
     "run37doc.report_explains_the_historical_placeholder",
     "EXPLAINS why the historical Run-36 candidate manifest keeps its placeholder"),
    (4, "one of the final release identity mechanisms is removed",
     (RECORD, '"release_content_digest":', '"removed_release_content_digest":'),
     "run37doc.identity_release_content_digest",
     "final release identity retains the content-addressed release digest"),
]


def drop_pycache():
    for d in ROOT.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


def run_guard(name):
    drop_pycache()
    p = subprocess.run([sys.executable, str(GUARD)], cwd=str(HERE), capture_output=True,
                       text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = p.stdout + p.stderr
    if "RESULT: " not in out:
        return "CRASH", out[-400:]
    lines = [ln for ln in out.splitlines() if ln.startswith(f"FAIL  {name}")]
    result = [ln for ln in out.splitlines() if ln.startswith("RESULT:")][0]
    return ("RED" if lines else "GREEN"), (lines[0] if lines else result)


def main():
    drop_pycache()
    base, detail = run_guard("__baseline__")
    if base == "GREEN" and "/" in detail:
        _p, _t = detail.replace("RESULT: ", "").split(" ")[0].split("/")
        if _p != _t:
            base = "NOT_FULLY_GREEN"
    if base != "GREEN":
        print(f"BASELINE NOT GREEN, refusing to run the campaign: {detail}")
        return 1
    print(f"baseline {detail}\n")

    out, counts = [], {"applied": 0, "red": 0, "restored": 0, "not_applied": 0, "crashed": 0}
    for num, desc, (path, old, new), guard, fragment in FAULTS:
        before = path.read_bytes()
        s = path.read_text(encoding="utf-8")
        if old not in s:
            out.append([num, desc, "NOT_APPLIED", guard, "", "",
                        "the anchor text is not present", "", "NOT_COUNTED"])
            counts["not_applied"] += 1
            print(f"fault {num:2d}  NOT_APPLIED (anchor absent)")
            continue
        path.write_text(s.replace(old, new, 1), encoding="utf-8")
        if path.read_bytes() == before:
            path.write_bytes(before)
            out.append([num, desc, "NOT_APPLIED", guard, "", "",
                        "the injection changed no bytes", "", "NOT_COUNTED"])
            counts["not_applied"] += 1
            print(f"fault {num:2d}  NOT_APPLIED (no byte change)")
            continue
        counts["applied"] += 1
        state, detail = run_guard(guard)
        intended = state == "RED" and fragment in detail
        if state == "CRASH":
            counts["crashed"] += 1
        if intended:
            counts["red"] += 1
        path.write_bytes(before)
        drop_pycache()
        restored = path.read_bytes() == before
        state2, _ = run_guard(guard)
        good = restored and state2 == "GREEN"
        if good:
            counts["restored"] += 1
        out.append([num, desc, "APPLIED", guard, state, "YES" if intended else "NO",
                    detail[:400], "YES" if good else "NO",
                    "COUNTED" if intended and good else "NOT_COUNTED"])
        print(f"fault {num:2d}  applied  guard {state:5s}  intended-reason "
              f"{'YES' if intended else 'NO ':3s}  restored-green {'YES' if good else 'NO'}")

    FREEZE.mkdir(parents=True, exist_ok=True)
    with (FREEZE / "run37_documentation_scope_campaign.csv").open(
            "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["fault", "failure_mode", "injection", "named_guard", "guard_state",
                    "red_for_intended_reason", "guard_output", "restored_green", "counted"])
        w.writerows(out)
    counted = len([r for r in out if r[8] == "COUNTED"])
    print(f"\nfaults declared {len(FAULTS)}; applied {counts['applied']}; "
          f"intended RED {counts['red']}; restored GREEN {counts['restored']}; "
          f"NOT_APPLIED {counts['not_applied']}; guards that CRASHED {counts['crashed']}; "
          f"crash accepted as RED 0; COUNTED {counted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
