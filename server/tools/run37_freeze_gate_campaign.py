#!/usr/bin/env python3
"""
RUN 37 FREEZE-GATE NON-VACUITY CAMPAIGN. Fifteen faults, one per blocker class, each injected into
a real file and each expected to turn ITS OWN NAMED BLOCKER red in `test_run37_freeze_gate.py`.

WHY THIS EXISTS. A freeze gate that cannot refuse is worth nothing, and an acceptance built on it
would be worth nothing either. Fault 15 is the load-bearing one: it mutates CANDIDATE ANALYTICAL
BEHAVIOUR after the candidate identity has been established, and requires the gate to refuse
release even though the mutation is in a file whose digest the campaign then restores.

RULES ENFORCED ON ITSELF, unchanged from Runs 35, 36 and the Run-36 closure:
 * baseline GREEN before anything is injected;
 * an injection that does not change bytes on disk is NOT_APPLIED and is not counted;
 * A CRASH IS NOT ACCEPTED AS RED;
 * the NAMED blocker must be the one that goes red, and its line must carry the intended fragment;
 * __pycache__ dropped on BOTH sides;
 * restored byte-for-byte and re-verified GREEN.

Writes research/freeze/run37_freeze_gate_campaign.csv.
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
_cs_arm(_cs_pl.Path(ROOT), "run37_freeze_gate_campaign.py",
        allow=[])
# -------------------------------------------------------------------------------------------
FREEZE = ROOT / "research" / "freeze"
AUDIT = ROOT / "code_audit"
GUARD = HERE / "test_run37_freeze_gate.py"
S = ROOT / "server" / "app" / "simulation"
JS = ROOT / "assets" / "js"
STIM = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.2"
        / "Opus_Gubernatio_Synthetic_Programme_v0.2" / "package_A_project_structures")


def text(path, old, new):
    return ("text", path, (old, new))


def csvcell(path, key_col, key, col, new):
    return ("csv", path, (key_col, key, col, new))


def droprow(path, key_col, key):
    return ("droprow", path, (key_col, key))


def duprow(path, key_col, key, k2=None, v2=None):
    return ("duprow", path, (key_col, key, k2, v2))


FAULTS = [
    (1, "the candidate identity is made dirty: a governed file moves after the digest was taken",
     text(S / "qualification_gate.py", '"""', '"""\n# run37 fault 1 probe\n'),
     "run37.gate.B01", "dirty candidate identity"),
    (2, "the scientific population is changed",
     text(S / "registry.py", '    "A3.4": "Material Cost Variance",\n', ''),
     "run37.gate.B02", "population mismatch"),
    (3, "a controlled stimulus period is removed",
     droprow(STIM / "reporting_periods.csv", "period_id", "P06"),
     "run37.gate.B03", "controlled-stimulus mismatch"),
    (4, "a participant sequence-bearing file drifts",
     text(JS / "decision-ui.js", "/*", "/* run37 fault 4 probe */\n/*"),
     "run37.gate.B04", "participant-sequence drift"),
    (5, "a served defensibility statement is made false",
     # REPOINTED. The first injection ADDED a second operationalState key ahead of the real one.
     # The served object is parsed into a dict, so the LAST key wins and the injected value was
     # silently overwritten by the genuine one -- the mutation landed in the bytes and changed
     # nothing the oracle could see. The EXISTING value is now overwritten in place, which is
     # what a false served statement actually looks like.
     text(JS / "ds_defensibility_evidence.js",
          'operationalState: "DISABLED_INSUFFICIENT_INPUT"',
          'operationalState: "COMPUTES_FROM_AVAILABLE_EVIDENCE"'),
     "run37.gate.B05", "false defensibility statement"),
    (6, "a scientific target raises instead of abstaining",
     text(S / "models_evm.py", "def run_tcpi(", "def run_tcpi(*_a, **_k):\n"
          "    raise RuntimeError('run37 fault 6 probe')\n\n\ndef _run_tcpi_orig("),
     "run37.gate.B06", "unexpected execution exception"),
    (7, "Category 9 is made a contributor to project status",
     text(S / "compute.py", "def contributes_to_project_status(group: str) -> bool:",
          "def contributes_to_project_status(group: str) -> bool:\n    return True  # fault 7"),
     "run37.gate.B07", "Category-9 bypass"),
    (8, "a Category-10 output is made human-authoritative",
     text(S / "canonical_v7.py", '"human_authorization_required": True',
          '"human_authorization_required": False'),
     "run37.gate.B08", "Category-10 authority violation"),
    (9, "a third voter is added",
     text(S / "registry.py",
          'CORE_VOTING_MODULES: frozenset[str] = frozenset({\n    "A1.7",   # TCPI',
          'CORE_VOTING_MODULES: frozenset[str] = frozenset({\n    "A1.2",   # fault 9\n'
          '    "A1.7",   # TCPI'),
     "run37.gate.B09", "voting count is not exactly 2"),
    (10, "a second taxonomy authority is created by unhooking a generated mirror",
     text(JS / "categories.js", "build_client_taxonomy.py", "hand_maintained_second_authority"),
     "run37.gate.B10", "current taxonomy dual authority"),
    (11, "a sealed predecessor participant package record is rewritten in place",
     text(AUDIT / "run33_participant_package_v11_checksums.sha256",
          "# OPUS GUBERNATIO PARTICIPANT PACKAGE og-participant-2026.08-v11",
          "# OPUS GUBERNATIO PARTICIPANT PACKAGE og-participant-2026.08-v11 (rewritten)"),
     "run37.gate.B11", "package or predecessor mutation"),
    (12, "a browser qualification surface is recorded as failed",
     csvcell(AUDIT / "run37_browser_qualification.csv", "surface", "final lock", "result",
             "FAIL"),
     "run37.gate.B12", "browser qualification failure"),
    (13, "an unresolved Run-36 blocking defect is reintroduced",
     csvcell(AUDIT / "run36_100_target_scientific_reaudit.csv", "module_id", "A2.5",
             "blocking_defect", "YES - injected for run37 fault 13"),
     "run37.gate.B13", "unresolved blocking Run-36 defect"),
    (14, "an empirical field-validation claim is asserted",
     text(HERE / "build_run37_acceptance.py", '"NOT_EMPIRICALLY_FIELD_VALIDATED",',
          '"EMPIRICALLY_FIELD_VALIDATED",'),
     "run37.gate.B14", "unsupported final empirical-validation claim"),
    # THE LOAD-BEARING ONE. Analytical behaviour is changed AFTER candidate identity was
    # established. No file digest in the identity record covers models_cat89, so B01 does not
    # see it; only the BEHAVIOUR digest does.
    (15, "candidate ANALYTICAL BEHAVIOUR is changed after the candidate identity was established",
     text(S / "models_cat89.py",
          '        row["status_color"] = None          # re-asserted after the update; '
          'no band is invented',
          '        row["status_color"] = "amber"       # run37 fault 15 probe'),
     "run37.gate.B15", "candidate behaviour changed during Run 37"),
]


def drop_pycache():
    for d in ROOT.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


def _read(path):
    with path.open(encoding="utf-8", newline="") as fh:
        r = list(csv.DictReader(fh))
    return r, list(r[0]) if r else []


def _write(path, hdr, r):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, hdr, lineterminator="\n")
        w.writeheader()
        w.writerows(r)


def apply_one(mut):
    kind, path = mut[0], mut[1]
    if kind == "text":
        old, new = mut[2]
        s = path.read_text(encoding="utf-8")
        if old not in s:
            return False, "the anchor text is not present"
        path.write_text(s.replace(old, new, 1), encoding="utf-8")
        return True, ""
    if kind == "csv":
        key_col, key, col, new = mut[2]
        r, hdr = _read(path)
        hit = False
        for row in r:
            if row[key_col] == key:
                row[col] = new
                hit = True
        if not hit:
            return False, f"no row keyed {key}"
        _write(path, hdr, r)
        return True, ""
    if kind == "droprow":
        key_col, key = mut[2]
        r, hdr = _read(path)
        keep = [x for x in r if x[key_col] != key]
        if len(keep) == len(r):
            return False, f"no row keyed {key}"
        _write(path, hdr, keep)
        return True, ""
    if kind == "duprow":
        key_col, key, k2, v2 = mut[2]
        r, hdr = _read(path)
        hits = [x for x in r if x[key_col] == key and (k2 is None or x[k2] == v2)]
        if not hits:
            return False, f"no row keyed {key}"
        _write(path, hdr, r + [dict(hits[0])])
        return True, ""
    raise ValueError(kind)


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
    # THE BASELINE MUST BE FULLY GREEN, not merely free of one named failure. The first version
    # asked run_guard for a blocker name that never appears, so ANY failing baseline was reported
    # as GREEN and the campaign ran against a broken starting point.
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
    for num, desc, mut, guard, fragment in FAULTS:
        path = mut[1]
        before = path.read_bytes()
        # RESTORE IN A `finally` THAT CANNOT BE SKIPPED. The restore below was straight-line
        # code before Run 54: any raise inside apply_one() or run_guard() left the fault on
        # disk. Hygiene, not the fix -- see server/tools/campaign_safety.py.
        with restore_guard({path: before}, after=drop_pycache):
            drop_pycache()
            ok, why = apply_one(mut)
            landed = ok and path.read_bytes() != before
            if not landed:
                out.append([num, desc, "NOT_APPLIED", guard, "", "", why, "", "NOT_COUNTED"])
                counts["not_applied"] += 1
                print(f"fault {num:2d}  NOT_APPLIED  ({why})")
                continue
            counts["applied"] += 1
            state, detail = run_guard(guard)
            intended = state == "RED" and fragment in detail
            if state == "CRASH":
                counts["crashed"] += 1
            if intended:
                counts["red"] += 1
        restored = path.read_bytes() == before
        state2, _ = run_guard(guard)
        good = restored and state2 == "GREEN"
        if good:
            counts["restored"] += 1
        out.append([num, desc, "APPLIED", guard, state, "YES" if intended else "NO",
                    detail[:400], "YES" if good else "NO",
                    "COUNTED" if intended and good else "NOT_COUNTED"])
        print(f"fault {num:2d}  applied  blocker {state:5s}  intended-reason "
              f"{'YES' if intended else 'NO ':3s}  restored-green {'YES' if good else 'NO'}")

    FREEZE.mkdir(parents=True, exist_ok=True)
    with (FREEZE / "run37_freeze_gate_campaign.csv").open("w", encoding="utf-8",
                                                          newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["fault", "blocker_class", "injection", "named_blocker", "gate_state",
                    "red_for_intended_reason", "gate_output", "restored_green", "counted"])
        w.writerows(out)
    counted = len([r for r in out if r[8] == "COUNTED"])
    print(f"\nfaults declared {len(FAULTS)}; applied {counts['applied']}; "
          f"intended RED {counts['red']}; restored GREEN {counts['restored']}; "
          f"NOT_APPLIED {counts['not_applied']}; gates that CRASHED {counts['crashed']}; "
          f"crash accepted as RED 0; COUNTED {counted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
