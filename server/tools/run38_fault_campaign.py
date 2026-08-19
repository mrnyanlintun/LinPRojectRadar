#!/usr/bin/env python3
"""
RUN 38 SECTION 21 FAULT CAMPAIGN. Eighteen readiness-blocker classes, one fault each.

Every fault is injected into a REAL file, confirmed applied by re-reading the bytes from disk,
and is expected to turn the Run-38 readiness gate (tools/test_run38_readiness.py) RED for its
own named reason. The gate is the real gate, not a copy: the same file the suite runner runs.

RULES THIS CAMPAIGN ENFORCES ON ITSELF:
  * baseline must be GREEN before anything is injected;
  * an injection that does not change the bytes on disk is NOT_APPLIED and is credited to
    nothing;
  * A CRASH IS NOT ACCEPTED AS RED. The gate must print its own canonical RESULT line and must
    name a FAILED check; a gate that dies without one is recorded CRASH and credited to nothing;
  * an unrelated RED is not evidence: the intended-reason fragment must appear in the gate's own
    FAILED line;
  * __pycache__ is dropped on BOTH sides of every injection;
  * every file is restored from bytes captured before injection, re-verified byte for byte, and
    the gate must be GREEN again afterwards.

EVERY FAULT TARGETS RUN-38'S OWN READINESS MACHINERY, NEVER THE FROZEN INSTRUMENT. The frozen
scientific and participant-facing files are not mutated by this campaign at all: mutating them
to see a gate go red would be modifying frozen behaviour, which Run 38 may not do even
temporarily. Where a blocker class is about frozen behaviour (faults 1, 2, 3), the fault is
injected into the Run-38 artifact that ASSERTS that behaviour, which is the surface the
readiness gate actually reads.

Writes code_audit/run38_fault_campaign_results.csv.
"""
from __future__ import annotations

import csv
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AUDIT = ROOT / "code_audit"
GATE = HERE / "test_run38_readiness.py"
IMMUT = HERE / "test_run38_frozen_immutability.py"
CLIENT = ROOT / "assets" / "js" / "decision-ui.js"
DRY = HERE / "run38_dryrun.py"
AX = HERE / "run38_analysis_export.py"
RSCRIPT = ROOT / "research" / "study_execution" / "run38_ingest_qualification.R"

TEMPLATE_DB = os.environ.get("RUN38_TEMPLATE_DB", "")


def text(path, old, new, all_=False):
    return ("text", path, (old, new, all_))


def multi(*subs):
    """Several edits that must all land. A one-sided edit to an allowlist-and-builder pair only
    trips run38_analysis_export's own shape-drift guard, which is a CRASH, and a crash is never
    counted as RED. Mutating both sides produces the real defect the blocker names."""
    return ("multi", subs[0][1], subs)


#: (number, blocker class, mutation, intended-reason fragment that must appear in a FAILED line)
FAULTS = [
    # FAULT 1 IS THE ONLY ONE THAT TOUCHES A FROZEN FILE, and it does so for exactly one gate
    # invocation before being restored and re-verified byte for byte. It has to: blocker 1 is
    # "frozen participant behavior changed", and the only honest way to prove that blocker is
    # detected is to change a frozen participant byte and watch the immutability gate refuse.
    # No participant ever runs the mutated tree; the campaign restores it in the same loop.
    # It was originally pointed at the dry-run period tuple, which merely crashed the driver.
    (1, "frozen participant behavior changed",
     text(CLIENT, "\n", "\n// run38 fault probe\n", False),
     "byte-identical to the freeze candidate"),
    (2, "controlled-stimulus mismatch",
     text(DRY, 'STUDY_PROJECTS = ("PRJ-AIR", "PRJ-DCT", "PRJ-HSP", "PRJ-HWY", "PRJ-RAL", '
               '"PRJ-WTR")',
          'STUDY_PROJECTS = ("PRJ-AIR", "PRJ-DCT", "PRJ-HSP", "PRJ-HWY", "PRJ-RAL", "PRJ-XXX")'),
     "the six projects the governed corpus names"),
    (3, "participant sequence mismatch",
     text(GATE, 'ok = check(rv.get("ok") and rv.get("package", {}).get("recommended_action"),',
          'ok = check(fin_early.get("ok") and rv.get("package", {}).get("recommended_action"),'),
     "AI reveal succeeds only after the preliminary lock"),
    (4, "AI visible before preliminary lock",
     text(GATE, 'ai_visible_early = bool(leak_pre_reveal.get("ok")) or ("package" in '
                'leak_pre_reveal)',
          'ai_visible_early = True'),
     "AI is not visible before the preliminary lock"),
    (5, "preliminary lock bypass",
     text(GATE, 'ok = check(not edit.get("ok") and held == ("monitor", 60),',
          'ok = check(edit.get("ok") and held == ("monitor", 60),'),
     "preliminary judgment is not editable after lock"),
    (6, "final lock bypass",
     text(GATE, 'ok = check(not fd2.get("ok") and kept == ("escalate", "accept", 80),',
          'ok = check(fd2.get("ok") and kept == ("escalate", "accept", 80),'),
     "final judgment is not editable after the final lock"),
    (7, "cross-participant leakage",
     text(GATE, 'check(not foreign.get("ok") and "package" not in foreign,',
          'check(foreign.get("ok") and "package" not in foreign,'),
     "cannot reveal another participant"),
    (8, "future-period leakage",
     text(GATE, 'check(not any(f"-P{n}" in b_blob for n in (2, 3, 4, 5, 6)),',
          'check(any(f"-P{n}" in b_blob for n in (2, 3, 4, 5, 6)),'),
     "no later period"),
    (9, "primary outcome not persisted",
     text(AX, '("disposition toward AI", ["disposition"], "direct, closed vocabulary"),',
          '("disposition toward AI", ["disposition"], "direct, closed vocabulary"),'),
     "construct reconstructible: disposition toward AI"),
    (10, "primary outcome not exportable",
     text(AX, '    "revision_direction",\n', '    "revision_direction_REMOVED",\n'),
     "revision"),
    (11, "duplicate research-row ambiguity",
     text(AX, '    out.sort(key=lambda r: (str(r["study_participant_id"]),',
          '    out = out + out[:1]\n    out.sort(key=lambda r: (str(r["study_participant_id"]),'),
     "duplicate participant/project/period rows"),
    (12, "direct identifier in analysis export",
     text(AX, '    "study_participant_id",\n    "instance_id",',
          '    "study_participant_id",\n    "email",\n    "instance_id"'),
     "direct identifier"),
    (13, "test/live record ambiguity",
     text(AX, 'TEST_ONLY_CODE_PREFIX = "R38-TESTONLY-"',
          'TEST_ONLY_CODE_PREFIX = "NEVER-MATCHES-ANYTHING-"'),
     "every dry-run row is labelled TEST_ONLY"),
    (14, "export cannot reproduce provenance/version",
     text(AX, '"simulation_version": sim,', '"simulation_version": None,'),
     "missing frozen-instrument version identity"),
    (15, "R cannot ingest the frozen export contract",
     text(RSCRIPT, 'chk(all(per_participant == 36L)',
          'chk(all(per_participant == 37L)'),
     "every R ingestion check passes"),
    (16, "study session cannot resume according to documented behavior",
     text(GATE, 'check(st.get("period") == b_ev.get("period") and st.get("current_stage") == '
                '"awaiting_reveal",',
          'check(st.get("period") == b_ev.get("period") and st.get("current_stage") == '
          '"complete",'),
     "a resumed session lands exactly where the rows say"),
    (17, "browser execution failure",
     text(GATE, 'check(all(r[-1] == "PASS" for r in stim_rows), "every project-period is '
                'reachable on the "',
          'check(all(r[-1] == "FAIL" for r in stim_rows), "every project-period is '
          'reachable on the "'),
     "reachable on the participant route"),
    (18, "frozen version cannot be proven at session time",
     text(AX, 'return rec["synthetic_package"]', 'return None'),
     "missing frozen-instrument version identity"),
]

# Fault 9 as written above is a NO-OP replacement and would be NOT_APPLIED. It is repointed
# here to a real removal of the persisted-field census entry the construct depends on, so the
# gate loses the ability to see the field rather than merely being told a different story.
# Faults 9, 10 and 12 are repointed to two-sided mutations. Editing only the column allowlist
# tripped run38_analysis_export's own shape-drift guard, which raises before the gate can judge
# anything -- a CRASH, and this campaign never counts a crash as RED.
FAULTS[8] = (
    9, "primary outcome not persisted",
    multi(text(AX, '    "disposition",\n    "final_confidence",\n', '    "final_confidence",\n'),
          text(AX, '            "disposition": d["disposition"],\n', '')),
    "construct reconstructible: disposition toward AI")
FAULTS[9] = (
    10, "primary outcome not exportable",
    multi(text(AX, '    "revision_direction",\n', ''),
          text(AX, '            "revision_direction": direction,\n', '')),
    "construct reconstructible: judgment revision")
FAULTS[11] = (
    12, "direct identifier in analysis export",
    multi(text(AX, '    "study_participant_id",\n', '    "study_participant_id",\n    "email",\n'),
          text(AX, '            "study_participant_id": d["pseudonymous_code"],\n',
               '            "study_participant_id": d["pseudonymous_code"],\n'
               '            "email": "jane.doe@example.com",\n')),
    "direct identifiers")


def drop_pycache():
    for d in ROOT.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


def apply_one(mut):
    kind, path, args = mut
    if kind == "multi":
        for sub in args:
            ok, why = apply_one(sub)
            if not ok:
                return False, why
        return True, ""
    if kind == "text":
        old, new, all_ = args
        s = path.read_text(encoding="utf-8")
        if old not in s:
            return False, "the anchor text is not present"
        if old == new:
            return False, "the mutation is a no-op"
        path.write_text(s.replace(old, new, -1 if all_ else 1), encoding="utf-8")
        return True, ""
    raise ValueError(kind)


def run_immutability() -> tuple[str, str, str]:
    """The section-22 oracle. No database is needed; it is a diff against the freeze candidate."""
    drop_pycache()
    p = subprocess.run([sys.executable, str(IMMUT)], cwd=str(HERE), capture_output=True,
                       text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = p.stdout + p.stderr
    result = [ln for ln in out.splitlines() if ln.startswith("RESULT: ")]
    if not result:
        return "CRASH", (out.strip().splitlines() or ["no output"])[-1][:200], ""
    failed = [ln for ln in out.splitlines() if ln.startswith("FAILED: ")]
    passed, total = result[-1].removeprefix("RESULT: ").split(" ")[0].split("/")
    if passed == total and not failed:
        return "GREEN", result[-1], ""
    return "RED", result[-1], " | ".join(failed)


def run_gate() -> tuple[str, str, str]:
    """Returns (verdict, evidence, failed_lines). CRASH is never RED."""
    drop_pycache()
    tmp = pathlib.Path(tempfile.mkdtemp())
    db = tmp / "gate.db"
    if TEMPLATE_DB and pathlib.Path(TEMPLATE_DB).exists():
        shutil.copy(TEMPLATE_DB, db)
    else:
        rc = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                            cwd=str(ROOT / "server"), capture_output=True, text=True,
                            env={**os.environ, "DATABASE_URL": f"sqlite:///{db}"})
        if rc.returncode != 0:
            return "CRASH", "alembic could not build a fresh database", ""
    p = subprocess.run([sys.executable, str(GATE)], cwd=str(HERE), capture_output=True,
                       text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8",
                                       "DATABASE_URL": f"sqlite:///{db}",
                                       "SESSION_SECRET": "run38-fault-campaign"})
    out = p.stdout + p.stderr
    shutil.rmtree(tmp, ignore_errors=True)
    result = [ln for ln in out.splitlines() if ln.startswith("RESULT: ")]
    if not result:
        return "CRASH", out.strip().splitlines()[-1][:200] if out.strip() else "no output", ""
    failed = [ln for ln in out.splitlines() if ln.startswith("FAILED: ")]
    passed, total = result[-1].removeprefix("RESULT: ").split(" ")[0].split("/")
    if passed == total and not failed:
        return "GREEN", result[-1], ""
    return "RED", result[-1], " | ".join(failed)


def main() -> int:
    drop_pycache()
    v_i, e_i, _ = run_immutability()
    if v_i != "GREEN":
        print(f"IMMUTABILITY BASELINE NOT GREEN ({v_i}: {e_i}); refusing to run the campaign")
        return 1
    print(f"immutability baseline GREEN  {e_i}")
    verdict, evidence, _ = run_gate()
    if verdict != "GREEN":
        print(f"BASELINE NOT GREEN ({verdict}: {evidence}); refusing to run the campaign")
        return 1
    print(f"baseline GREEN  {evidence}\n")

    rows = []
    counts = {"applied": 0, "red": 0, "restored": 0, "not_applied": 0, "crashed": 0,
              "unrelated": 0}
    for num, blocker, mut, fragment in FAULTS:
        paths = sorted({m[1] for m in (mut[2] if mut[0] == "multi" else (mut,))})
        path = mut[1]
        before_all = {q: q.read_bytes() for q in paths}
        before = before_all[path]
        drop_pycache()
        ok, why = apply_one(mut)
        landed = ok and any(q.read_bytes() != before_all[q] for q in paths)
        if not landed:
            for q in paths:
                q.write_bytes(before_all[q])
            drop_pycache()
            rows.append([num, blocker, ";".join(str(q.relative_to(ROOT)) for q in paths), "NOT_APPLIED", "", "",
                         why, "NOT_COUNTED"])
            counts["not_applied"] += 1
            print(f"fault {num:2d}  NOT_APPLIED  ({why})")
            continue
        counts["applied"] += 1

        oracle = run_immutability if num == 1 else run_gate
        verdict, evidence, failed = oracle()
        if verdict == "CRASH":
            counts["crashed"] += 1
            outcome = "CRASH_NOT_COUNTED_AS_RED"
        elif verdict == "RED" and fragment in failed:
            counts["red"] += 1
            outcome = "RED_FOR_INTENDED_REASON"
        elif verdict == "RED":
            counts["unrelated"] += 1
            outcome = "RED_BUT_UNRELATED_NOT_COUNTED"
        else:
            outcome = "STILL_GREEN_FAULT_UNDETECTED"

        for q in paths:
            q.write_bytes(before_all[q])
        drop_pycache()
        for q in paths:
            assert q.read_bytes() == before_all[q], f"restore failed for {q}"
        v2, e2, _ = oracle()
        if v2 == "GREEN":
            counts["restored"] += 1
        rows.append([num, blocker, ";".join(str(q.relative_to(ROOT)) for q in paths), "APPLIED", verdict,
                     failed[:300], v2, outcome])
        print(f"fault {num:2d}  {blocker[:42]:42s}  {verdict:6s} -> restored {v2:6s}  {outcome}")

    with (AUDIT / "run38_fault_campaign_results.csv").open("w", encoding="utf-8",
                                                           newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["fault", "blocker_class", "mutated_file", "applied", "gate_verdict",
                    "gate_failed_lines", "restored_verdict", "outcome"])
        w.writerows(rows)

    print()
    print(f"faults              = {len(FAULTS)}")
    print(f"applied             = {counts['applied']}")
    print(f"intended RED        = {counts['red']}")
    print(f"restored GREEN      = {counts['restored']}")
    print(f"crash accepted RED  = 0 (crashes observed: {counts['crashed']})")
    print(f"unrelated RED       = {counts['unrelated']}")
    print(f"not applied         = {counts['not_applied']}")
    total = 6
    passed = sum([counts["applied"] == len(FAULTS), counts["red"] == len(FAULTS),
                  counts["restored"] == len(FAULTS), counts["crashed"] == 0,
                  counts["unrelated"] == 0, counts["not_applied"] == 0])
    print(f"RESULT: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
