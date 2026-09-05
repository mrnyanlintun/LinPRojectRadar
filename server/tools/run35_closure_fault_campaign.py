#!/usr/bin/env python3
"""
RUN 35 CLOSURE FAULT CAMPAIGN. Fifteen failure modes, each injected into a real file, confirmed
applied by re-reading the bytes from disk, each expected to turn ONE NAMED GUARD red for its own
reason, restored byte-for-byte and re-verified green.

Baseline must be GREEN first. An injection that changes no byte is NOT_APPLIED and is not
credited. A crash is NOT accepted as RED. A red in some other guard is not evidence: the named
guard must fail and its text must contain the intended-reason fragment. __pycache__ is dropped on
BOTH sides of every injection, because a restore inside the same clock second changes neither
mtime nor size and a cached mutant survives.

Writes code_audit/run35_closure_fault_injection.csv.
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
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
_cs_arm(_cs_pl.Path(ROOT), "run35_closure_fault_campaign.py",
        allow=[])
# -------------------------------------------------------------------------------------------
SERVER = ROOT / "server"
AUDIT = ROOT / "code_audit"
GUARD = HERE / "test_run35_closure_voter_identities.py"
S = SERVER / "app" / "simulation"


def text(path, old, new):
    return ("text", path, (old, new))


def csvcell(path, key_col, key, col, old, new):
    return ("csv", path, (key_col, key, col, old, new))


def jsonkey(path, dotted, new):
    return ("json", path, (dotted, new))


FAULTS = [
    (1, "A1.7 bands from the rounded value",
     text(S / "models_evm.py",
          "    tcpi = remaining_work / remaining_budget\n    color = (\"Green\" if tcpi <= "
          "_TCPI_PLANNED_EFFICIENCY",
          "    tcpi = remaining_work / remaining_budget\n    tcpi = _round3(tcpi)\n"
          "    color = (\"Green\" if tcpi <= _TCPI_PLANNED_EFFICIENCY"),
     "run35c.fault01.tcpi_bands_from_full_precision", "banded Green, not Amber"),
    (2, "the A1.7 canonical value is itself rounded before downstream use",
     text(S / "models_evm.py", '        "tcpi": tcpi,\n        "tcpi_display": tcpi_display,',
          '        "tcpi": tcpi_display,\n        "tcpi_display": tcpi_display,'),
     "run35c.fault02.tcpi_canonical_not_rounded", "is not the identity"),
    (3, "the A1.7 display value is used as the vote input",
     text(S / "models_evm.py",
          '    tcpi_display = _round3(tcpi)\n    return {\n        "method_class": "TCPI",\n'
          '        "status_color": color,',
          '    tcpi_display = _round3(tcpi)\n    color = ("Green" if tcpi_display <= '
          '_TCPI_PLANNED_EFFICIENCY else "Amber" if tcpi_display <= _TCPI_BEYOND_OBSERVED '
          'else "Red")\n    return {\n        "method_class": "TCPI",\n'
          '        "status_color": color,'),
     "run35c.fault03.display_is_not_the_vote_input", "follows the DISPLAY value"),
    (4, "the A1.7 boundary population receives the wrong band",
     text(S / "models_evm.py", "    _TCPI_PLANNED_EFFICIENCY = 1.00" if False else
          "_TCPI_PLANNED_EFFICIENCY = 1.00", "_TCPI_PLANNED_EFFICIENCY = 1.01"),
     "run35c.fault04.boundary_population_bands_correctly", "expected Amber"),
    (5, "the canonical VAC is rounded before downstream use",
     text(S / "models_evm.py", '        "vac": vac,\n        "vac_pct": vac_pct,',
          '        "vac": float(int(js_round(vac))),\n        "vac_pct": vac_pct,'),
     "run35c.fault05.vac_canonical_not_rounded", "is not the identity"),
    (6, "the A1.8 display value replaces the analytical VAC",
     text(S / "models_evm.py", '        "vac_display": int(js_round(vac)),',
          '        "vac_display": vac,'),
     "run35c.fault06.vac_display_separate", "same object"),
    (7, "the canonical VAC identity is perturbed",
     text(S / "models_evm.py", "    vac = si[\"bac\"] - eac", "    vac = si[\"bac\"] - eac * 1.0001"),
     "run35c.fault07.vac_identity_holds", "!="),
    (8, "a third voting module is introduced",
     text(S / "registry.py", '    "A1.8",   # Variance at Completion\n})',
          '    "A1.8",   # Variance at Completion\n    "A1.9",\n})'),
     "run35c.fault08.voting_is_exactly_two", "the voting set is"),
    (9, "Cost Recovery Status reads a formatted string instead of the analytical result",
     text(S / "models_evm.py",
          '    tcpi_display = _round3(tcpi)\n    return {\n        "method_class": "TCPI",\n'
          '        "status_color": color,',
          '    tcpi_display = _round3(tcpi)\n    color = ("Green" if float('
          '_js_str(tcpi_display)) <= _TCPI_PLANNED_EFFICIENCY else "Amber" if float('
          '_js_str(tcpi_display)) <= _TCPI_BEYOND_OBSERVED else "Red")\n    return {\n'
          '        "method_class": "TCPI",\n        "status_color": color,'),
     "run35c.fault09.cost_recovery_reads_analytical", "which is the band the FORMATTED value"),
    (10, "the v22 predecessor is rewritten to the corrected behaviour",
     text(HERE / "test_run35_closure_voter_identities.py",
          'V22_COMMIT = "034cf03be257f4582bc1a856262c56ea11bb4558"',
          'V22_COMMIT = "HEAD"'),
     "run35c.fault10.v22_predecessor_not_rewritten", "no longer stamps itself v22"),
    (11, "the v22->v23 execution proof claims divergence where the outputs are equal",
     csvcell(AUDIT / "run35_v22_v23_voter_execution_proof.csv", "record_type", "NON_DIVERGENCE",
             "divergence", "NO", "YES"),
     "run35c.fault11.execution_proof_divergences_real", "claims divergence with identical"),
    (12, "the B1.2 stale proxy label is restored",
     text(S / "method_labels.py", 'TRUTHFUL_METHOD_LABELS: dict[str, MethodLabel] = {',
          'TRUTHFUL_METHOD_LABELS: dict[str, MethodLabel] = {\n'
          '    "B1.2": MethodLabel(\n'
          '        registered="Weighted Voting",\n'
          '        truthful="Fixed-weight signal band tally",\n'
          '        performs="tallies the bands of the assembled signals under four fixed '
          'weights",\n'
          '        absent="provenance for the four weights",\n'
          '        disposition="CORRECT_PROXY_ONLY",\n'
          '    ),'),
     "run35c.fault12.b1_2_label_withdrawn", "carries a truthful-method label again"),
    (13, "the B4.4 stale proxy label is restored",
     text(S / "method_labels.py", 'TRUTHFUL_METHOD_LABELS: dict[str, MethodLabel] = {',
          'TRUTHFUL_METHOD_LABELS: dict[str, MethodLabel] = {\n'
          '    "B4.4": MethodLabel(\n'
          '        registered="What-If Scenario Matrix",\n'
          '        truthful="Earned value completion forecast range",\n'
          '        performs="computes four completion forecasts by perturbing the cost index",\n'
          '        absent="candidate actions with identity as the rows",\n'
          '        disposition="CORRECT_PROXY_ONLY",\n'
          '    ),'),
     "run35c.fault13.b4_4_label_withdrawn", "carries a truthful-method label again"),
    (14, "the label oracle is fed a generated client artifact instead of the registry authority",
     ("registryname", ROOT / "p0-baseline" / "module_renumbering_map.csv",
      ("B1.2", "Weighted Voting", "Signal Band Tally")),
     "run35c.fault14.label_expectation_from_authority",
     "presents B1.2 under a name the registry authority does not carry"),
    (15, "the A1.1 Run-36 finding disappears from the handoff",
     text(ROOT / "T6_HANDOFF.md",
          "DECLARED_STRUCTURE_UNCONSUMED_AND_REACHABLE_PARAMETER_UNRESOLVED",
          "RESOLVED_IN_RUN_35_CLOSURE"),
     "run35c.fault15.a1_1_finding_carried_forward", "does not carry the finding"),
]


# --------------------------------------------------------------------------- mechanics
def drop_pycache():
    for d in SERVER.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


def apply_text(path, old, new):
    s = path.read_text(encoding="utf-8")
    if old not in s:
        return False, "the anchor text is not present"
    path.write_text(s.replace(old, new, 1), encoding="utf-8")
    return True, ""


def apply_csvcell(path, key_col, key, col, old, new):
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
        hdr = list(rows[0])
    hit = False
    for r in rows:
        if r[key_col] == key and r[col] == old:
            r[col] = new
            hit = True
            break
    if not hit:
        return False, f"no {key} row carrying {old!r} in {col}"
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, hdr, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return True, ""


def apply_registryname(path, mid, old, new):
    s = path.read_text(encoding="utf-8-sig")
    line = f"{mid},{old},"
    if line not in s:
        return False, f"{mid} does not carry the name {old!r} in the registry authority"
    path.write_text(s.replace(line, f"{mid},{new},", 1), encoding="utf-8")
    return True, ""


def apply_one(mut):
    kind = mut[0]
    if kind == "text":
        return apply_text(mut[1], *mut[2])
    if kind == "csv":
        return apply_csvcell(mut[1], *mut[2])
    if kind == "registryname":
        return apply_registryname(mut[1], *mut[2])
    raise ValueError(kind)


def run_guard(name):
    drop_pycache()
    p = subprocess.run([sys.executable, str(GUARD)], cwd=str(HERE), capture_output=True,
                       text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = p.stdout + p.stderr
    if "RESULT: " not in out:
        return "CRASH", out[-400:]
    lines = [ln for ln in out.splitlines() if ln.startswith(f"FAIL  {name}")]
    return ("RED" if lines else "GREEN"), (lines[0] if lines else
                                           [ln for ln in out.splitlines()
                                            if ln.startswith("RESULT:")][0])


def main():
    drop_pycache()
    base, detail = run_guard("__baseline__")
    if base != "GREEN":
        print(f"BASELINE NOT GREEN: {detail}")
        return 1
    print(f"baseline {detail}")

    rows = []
    counts = {"applied": 0, "red": 0, "restored": 0, "not_applied": 0, "crash_as_red": 0}
    for num, desc, mut, guard, fragment in FAULTS:
        f = mut[1]
        before = f.read_bytes()
        # RESTORE IN A `finally` THAT CANNOT BE SKIPPED. The restore below was straight-line
        # code before Run 54: any raise inside apply_one() or run_guard() left the fault on
        # disk. Hygiene, not the fix -- see server/tools/campaign_safety.py.
        with restore_guard({f: before}, after=drop_pycache):
            drop_pycache()
            ok, why = apply_one(mut)
            landed = ok and f.read_bytes() != before
            if not landed:
                rows.append([num, desc, "NOT_APPLIED", guard, "", "", why, "", "NOT_COUNTED"])
                counts["not_applied"] += 1
                print(f"fault {num:2d}  NOT_APPLIED  ({why})")
                continue
            counts["applied"] += 1
            state, detail = run_guard(guard)
            intended = state == "RED" and fragment in detail
            if state == "CRASH":
                counts["crash_as_red"] += 0            # never accepted
            if intended:
                counts["red"] += 1
        restored = f.read_bytes() == before
        state2, detail2 = run_guard(guard)
        good = restored and state2 == "GREEN"
        if good:
            counts["restored"] += 1
        rows.append([num, desc, "APPLIED", guard, state, "YES" if intended else "NO",
                     detail[:400], "YES" if good else "NO",
                     "COUNTED" if intended and good else "NOT_COUNTED"])
        print(f"fault {num:2d}  applied  guard {state:5s}  intended-reason "
              f"{'YES' if intended else 'NO '}  restored-green {'YES' if good else 'NO'}")

    with (artifact_out(AUDIT / "run35_closure_fault_injection.csv")).open("w", encoding="utf-8",
                                                           newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["fault", "failure_mode", "injection", "named_guard", "guard_state",
                    "red_for_intended_reason", "guard_output", "restored_green", "counted"])
        w.writerows(rows)
    print(f"\nfaults declared 15; applied {counts['applied']}; intended RED {counts['red']}; "
          f"restored GREEN {counts['restored']}; NOT_APPLIED {counts['not_applied']}; "
          f"crash accepted as RED {counts['crash_as_red']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
