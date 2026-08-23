#!/usr/bin/env python3
"""
RUN 36 CLOSURE FAULT CAMPAIGN. Fifteen focused failure modes, one per item of the closure
contract's section-14 list, each injected into a real file, confirmed applied by re-reading the
bytes from disk, and each expected to turn ONE NAMED ORACLE in test_run36_closure_guards.py red
for its own reason.

RULES THIS CAMPAIGN ENFORCES ON ITSELF, unchanged from Runs 35 and 36:
 * baseline must be GREEN before anything is injected;
 * an injection that does not change the bytes on disk is NOT_APPLIED and is not counted;
 * A CRASH IS NOT ACCEPTED AS RED -- the guard must print its own RESULT line and its own named
   failure, and a crashing guard is recorded as CRASH and credited to nothing;
 * a RED somewhere else is not evidence: the named oracle must be the one that fails AND its
   failure line must carry the intended-reason fragment;
 * __pycache__ is dropped on BOTH sides of every injection;
 * every file is restored from the bytes captured before injection, re-verified byte-for-byte,
   and the oracle must be GREEN again afterwards.

Writes code_audit/run36_closure_fault_results.csv.
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
_cs_arm(_cs_pl.Path(ROOT), "run36_closure_fault_campaign.py",
        allow=[])
# -------------------------------------------------------------------------------------------
AUDIT = ROOT / "code_audit"
GUARD = HERE / "test_run36_closure_guards.py"
S = ROOT / "server" / "app" / "simulation"
JS = ROOT / "assets" / "js"
PKG = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.2"
       / "Opus_Gubernatio_Synthetic_Programme_v0.2" / "package_A_project_structures")


def text(path, old, new, all_=False):
    return ("text", path, (old, new, all_))


def csvcell(path, key_col, key, col, new):
    return ("csv", path, (key_col, key, col, new))


def droprow(path, key_col, key):
    return ("droprow", path, (key_col, key))


def duprow(path, key_col, key, keycol2=None, key2=None):
    return ("duprow", path, (key_col, key, keycol2, key2))


def newfile(path, body):
    return ("newfile", path, (body,))


FAULTS = [
    (1, "the retained scalar adaptation becomes a production fallback",
     # REPOINTED. The first anchor -- the bare `if new_id in DISABLED_...` line -- occurs TWICE
     # in registry.py, and the FIRST occurrence is in `activation_state`, not in `run_module`.
     # A single-occurrence replace therefore edited the label function and left the production
     # gate untouched, so the fault was not the fault it claimed to be and the oracle was right
     # to stay green. The anchor now carries the line that follows it inside `run_module`, which
     # is unique to the gate itself.
     text(S / "registry.py",
          "    if new_id in DISABLED_CANONICAL_INPUT_NOT_GOVERNED:\n        return {\n",
          "    if False and new_id in DISABLED_CANONICAL_INPUT_NOT_GOVERNED:\n        return {\n"),
     "run36c.fault01", "cannot become a fallback when the canonical inputs are absent"),
    (2, "A1.1 emits a numeric canonical result without the structure or the mapping",
     text(S / "registry.py",
          '            "retained_adaptation": "preserved in app.simulation.models_sim',
          '            "p80_eac": 1121044.4168552589,\n'
          '            "retained_adaptation": "preserved in app.simulation.models_sim'),
     "run36c.fault02", "emits no numeric canonical result"),
    (3, "A1.1 emits a status colour",
     text(S / "registry.py",
          '            "method_class": VALIDATED[new_id][0] if new_id in VALIDATED else None,\n'
          '            "status_color": None,\n            "band_asserted": False,',
          '            "method_class": VALIDATED[new_id][0] if new_id in VALIDATED else None,\n'
          '            "status_color": "red",\n            "band_asserted": False,'),
     "run36c.fault03", "emits no status colour"),
    (4, "A1.1 becomes a voter",
     text(S / "registry.py",
          'CORE_VOTING_MODULES: frozenset[str] = frozenset({\n    "A1.7",   # TCPI',
          'CORE_VOTING_MODULES: frozenset[str] = frozenset({\n    "A1.1",   # injected\n'
          '    "A1.7",   # TCPI'),
     "run36c.fault04", "A1.1 does not vote"),
    (5, "defensibility calls the retained adaptation the canonical method",
     text(JS / "ds_defensibility_evidence.js",
          'operationalState: "DISABLED_INSUFFICIENT_INPUT"',
          'operationalState: "COMPUTES_FROM_AVAILABLE_EVIDENCE"'),
     "run36c.fault05", "does not describe the retained adaptation as the canonical method"),
    (6, "the v24 predecessor stamp is rewritten in the live history",
     text(S / "models.py",
          '    "sim-2026.08-v22", "sim-2026.08-v23", "sim-2026.08-v24", "sim-2026.08-v25",',
          '    "sim-2026.08-v22", "sim-2026.08-v23", "sim-2026.08-v25",'),
     "run36c.fault06", "appended beside it rather than over it"),
    (7, "the version-boundary proof claims a divergence that did not happen",
     csvcell(AUDIT / "run36_v24_v25_a1_1_execution_proof.csv", "module_id", "A1.7",
             "observed", "DIVERGED"),
     "run36c.fault07", "claims divergence only where both executed lines actually diverged"),
    (8, "one Run35/Run36 parsimony discrepancy is silently dropped",
     droprow(AUDIT / "run36_parsimony_crossrun_reconciliation.csv", "module_id", "A1.6"),
     "run36c.fault08", "one has been silently dropped"),
    (9, "the reconciler treats shared lineage as automatically identical method",
     text(HERE / "build_run36_parsimony_reconciliation.py",
          'overlap[m] = (("COMMON_LINEAGE_ONLY", peers_lin) if peers_lin',
          'overlap[m] = (("IDENTICAL_ANALYTICAL_FUNCTION", peers_lin) if peers_lin'),
     "run36c.fault09", "never as identity of analytical function"),
    (10, "the reconciler treats unknown lineage as independent lineage",
     text(HERE / "build_run36_parsimony_reconciliation.py",
          'else "LINEAGE_UNRESOLVED"', 'else "LINEAGE_ESTABLISHED_INDEPENDENT"', True),
     "run36c.fault10", "never as independent"),
    (11, "one project is omitted from the controlled study population",
     droprow(PKG / "projects.csv", "project_id", "PRJ-WTR"),
     "run36c.fault11", "one has been omitted"),
    (12, "one period is omitted from a project",
     droprow(PKG / "reporting_periods.csv", "period_id", "P06"),
     "run36c.fault12", "one has been omitted"),
    (13, "a duplicate project-period is introduced",
     duprow(PKG / "reporting_periods.csv", "project_id", "PRJ-AIR", "period_id", "P01"),
     "run36c.fault13", "a duplicate has been introduced"),
    (14, "the record claims a 6x6x36 design the enumerated stimuli do not carry",
     csvcell(AUDIT / "run36_controlled_study_population.csv", "name_or_metric",
             "UNIQUE PROJECT-PERIOD COMBINATIONS", "value", "42"),
     "run36c.fault14", "the record claims a design the stimuli do not carry"),
    (15, "a freeze candidate is created while a blocking defect remains",
     ("multi", None, (
         csvcell(AUDIT / "run36_100_target_scientific_reaudit.csv", "module_id", "A2.5",
                 "blocking_defect", "YES - injected for fault 15"),
         newfile(ROOT / "research" / "freeze" / "INSTRUMENT_FREEZE_CANDIDATE_MANIFEST.json",
                 '{"label": "FREEZE_CANDIDATE", "injected_by": "run36 closure fault 15"}\n'))),
     "run36c.fault15", "the freeze gate has been opened with a defect standing"),
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
    if kind == "multi":
        for sub in mut[2]:
            ok, why = apply_one(sub)
            if not ok:
                return False, why
        return True, ""
    if kind == "text":
        old, new, all_ = mut[2]
        s = path.read_text(encoding="utf-8")
        if old not in s:
            return False, "the anchor text is not present"
        path.write_text(s.replace(old, new, -1 if all_ else 1), encoding="utf-8")
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
    if kind == "newfile":
        (body,) = mut[2]
        if path.exists():
            return False, "the file already exists, so creating it proves nothing"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return True, ""
    raise ValueError(kind)


def files_of(mut):
    if mut[0] == "multi":
        out = []
        for sub in mut[2]:
            out += files_of(sub)
        return out
    return [(mut[1], mut[0] == "newfile")]


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
    if base != "GREEN":
        print(f"BASELINE NOT GREEN, refusing to run the campaign: {detail}")
        return 1
    print(f"baseline {detail}\n")

    rows_out = []
    counts = {"applied": 0, "red": 0, "restored": 0, "not_applied": 0, "crashed": 0}
    for num, desc, mut, guard, fragment in FAULTS:
        targets = files_of(mut)
        before = {p: (None if created else p.read_bytes()) for p, created in targets}
        drop_pycache()
        ok, why = apply_one(mut)
        landed = ok and any((p.exists() if created else p.read_bytes() != before[p])
                            for p, created in targets)
        if not landed:
            for p, created in targets:
                if created:
                    if p.exists():
                        p.unlink()
                elif before[p] is not None:
                    p.write_bytes(before[p])
            drop_pycache()
            rows_out.append([num, desc, "NOT_APPLIED", guard, "", "", why, "", "NOT_COUNTED"])
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
        for p, created in targets:
            if created:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(before[p])
        drop_pycache()
        restored = all((not p.exists()) if created else p.read_bytes() == before[p]
                       for p, created in targets)
        state2, _ = run_guard(guard)
        good = restored and state2 == "GREEN"
        if good:
            counts["restored"] += 1
        rows_out.append([num, desc, "APPLIED", guard, state, "YES" if intended else "NO",
                         detail[:400], "YES" if good else "NO",
                         "COUNTED" if intended and good else "NOT_COUNTED"])
        print(f"fault {num:2d}  applied  guard {state:5s}  intended-reason "
              f"{'YES' if intended else 'NO ':3s}  restored-green {'YES' if good else 'NO'}")

    with (AUDIT / "run36_closure_fault_results.csv").open("w", encoding="utf-8",
                                                          newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["fault", "failure_mode", "injection", "named_guard", "guard_state",
                    "red_for_intended_reason", "guard_output", "restored_green", "counted"])
        w.writerows(rows_out)
    counted = len([r for r in rows_out if r[8] == "COUNTED"])
    print(f"\nfaults declared {len(FAULTS)}; applied {counts['applied']}; "
          f"intended RED {counts['red']}; restored GREEN {counts['restored']}; "
          f"NOT_APPLIED {counts['not_applied']}; guards that CRASHED {counts['crashed']}; "
          f"crash accepted as RED 0; COUNTED {counted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
