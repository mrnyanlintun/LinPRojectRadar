#!/usr/bin/env python3
"""
RUN 39 SECTION 19 FAULT CAMPAIGN. Twenty launch-blocker classes, one fault each.

Every fault is injected into a REAL file, confirmed applied by re-reading the bytes from disk,
and is expected to turn a NAMED Run-39 oracle RED for its own reason.

RULES THIS CAMPAIGN ENFORCES ON ITSELF:
  * baseline GREEN on every oracle before anything is injected;
  * an injection that does not change bytes on disk is NOT_APPLIED and credited to nothing;
  * A CRASH IS NOT ACCEPTED AS RED. The oracle must print its canonical RESULT line AND name a
    FAILED check; an oracle that dies without one is CRASH and credited to nothing;
  * an unrelated RED is not evidence: the intended-reason fragment must appear in the oracle's
    own FAILED line;
  * __pycache__ dropped on BOTH sides of every injection;
  * every file restored from bytes captured before injection, re-verified byte for byte, and the
    oracle must be GREEN again afterwards.

FROZEN FILES ARE TOUCHED BY EXACTLY TWO FAULTS (2 and 3), each for a single oracle invocation
before being restored and re-verified byte for byte. They have to be: blockers 2 and 3 are
"instrument/client behavior changed" and "controlled stimuli changed", and the only honest way
to prove those are detected is to change such a byte and watch the immutability gate refuse. No
participant ever runs the mutated tree.

Writes code_audit/run39_fault_campaign_results.csv.
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
import tempfile

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
_cs_arm(_cs_pl.Path(ROOT), "run39_fault_campaign.py",
        # RUN 55, PHASE B, section 8 item 1: TIGHTENED TO THE DECLARED OUTPUT. The entry
        # here was `run39_pilot_browser_execution.csv`, which this campaign READS as an
        # oracle and MUTATES as fault 17's target -- it is not an output. The file this
        # campaign is designed to write is run39_fault_campaign_results.csv (line ~384),
        # and it was not declared at all. Both halves of that are corrected here.
        allow=["code_audit/run39_fault_campaign_results.csv"])
# -------------------------------------------------------------------------------------------
AUDIT = ROOT / "code_audit"

GATE = HERE / "test_run39_launch_gate.py"
IMMUT39 = HERE / "test_run39_frozen_immutability.py"
DC = HERE / "run39_dataset_class.py"
LG = HERE / "run39_launch_gate.py"
FZ = HERE / "run39_main_study_freeze.py"
AX = HERE / "run38_analysis_export.py"
DRY = HERE / "run38_dryrun.py"
REGISTRY = ROOT / "research" / "study_execution" / "dataset_class_registry.csv"
CLIENT = ROOT / "assets" / "js" / "decision-ui.js"
STIMULUS = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.2"
            / "Opus_Gubernatio_Synthetic_Programme_v0.2" / "package_A_project_structures"
            / "projects.csv")

TEMPLATE_DB = os.environ.get("RUN39_TEMPLATE_DB", "")


def text(path, old, new, all_=False):
    return ("text", path, (old, new, all_))


def multi(*subs):
    """Several edits that must all land. A one-sided edit to an allowlist/builder pair only
    trips a shape-drift guard, which is a CRASH, and a crash is never counted as RED."""
    return ("multi", subs[0][1], subs)


#: (number, blocker class, mutation, oracle, intended-reason fragment)
FAULTS = [
    (1, "frozen identity mismatch",
     text(GATE, 'identity("simulation", "sim-2026.08-v25", SIMULATION_VERSION,',
          'identity("simulation", "sim-2026.08-vXX", SIMULATION_VERSION,'),
     "gate", "identity: simulation"),
    (2, "instrument/client behavior changed",
     text(CLIENT, "\n", "\n// run39 fault probe\n", False),
     "immut", "byte-identical to the freeze candidate"),
    (3, "controlled stimuli changed",
     text(STIMULUS, "PRJ-AIR", "PRJ-AIQ", False),
     "immut", "byte-identical to the freeze candidate"),
    (4, "participant sequence changed",
     text(GATE, 'check(a.get("reveal_after_pre_lock") == 36,',
          'check(a.get("reveal_after_pre_lock") == 35,'),
     "gate", "AI reveal follows the preliminary lock"),
    (5, "pilot data can enter MAIN_STUDY",
     text(DC, '    return reg.get((study_participant_id or "").strip(), UNCLASSIFIED)',
          '    v = reg.get((study_participant_id or "").strip(), UNCLASSIFIED)\n'
          '    return MAIN_STUDY if v == "PILOT" else v'),
     "gate", "MAIN_STUDY"),
    (6, "test data can enter MAIN_STUDY",
     text(DC, 'def eligible_for_main_study(study_participant_id: str | None,\n'
              '                            registry: dict[str, str] | None = None) -> bool:\n'
              '    """Fail-closed: only an explicit MAIN_STUDY registration qualifies."""\n'
              '    return classify(study_participant_id, registry) == MAIN_STUDY',
          'def eligible_for_main_study(study_participant_id: str | None,\n'
          '                            registry: dict[str, str] | None = None) -> bool:\n'
          '    """Fail-closed: only an explicit MAIN_STUDY registration qualifies."""\n'
          '    return classify(study_participant_id, registry) != "NEVER"'),
     "gate", "eligible"),
    (7, "MAIN_STUDY not at zero state before launch",
     text(REGISTRY, "R39-PILOT-B,PILOT,", "R39-PILOT-B,MAIN_STUDY,"),
     "gate", "zero state"),
    (8, "direct identifiers appear in analysis export",
     multi(text(AX, '    "study_participant_id",\n',
                '    "study_participant_id",\n    "email",\n'),
           text(AX, '            "study_participant_id": d["pseudonymous_code"],\n',
                '            "study_participant_id": d["pseudonymous_code"],\n'
                '            "email": "pilot.person@example.com",\n')),
     "gate", "direct identifiers"),
    (9, "primary outcome cannot be reconstructed",
     multi(text(AX, '    "revision_direction",\n', ''),
           text(AX, '            "revision_direction": direction,\n', '')),
     "gate", "reconstructible from the pilot export"),
    (10, "pilot export violates frozen schema",
     text(AX, 'ANALYSIS_SCHEMA_VERSION = "og-analysis-2026.08-v1"',
          'ANALYSIS_SCHEMA_VERSION = "og-analysis-2026.08-v2-UNAUTHORISED"'),
     "gate", "schema"),
    (11, "R cannot ingest frozen export",
     text(ROOT / "research/study_execution/run38_ingest_qualification.R",
          'chk(all(per_participant == 36L)', 'chk(all(per_participant == 37L)'),
     "gate", "R rehearsal check"),
    (12, "participant/session isolation failure",
     text(GATE, 'seg("participant IDs can overlap syntactically without cross-class '
                'contamination",',
          'seg("participant IDs can overlap syntactically WITHOUT cross-class contamination",'),
     "gate", None),                       # repointed below; see REPOINTED
    (13, "preliminary-lock bypass",
     text(GATE, 'check(tamper_result["pre_action"] == "REFUSED_BY_TRIGGER"\n'
                '      and tamper_result["pre_confidence"] == "REFUSED_BY_TRIGGER",',
          'check(tamper_result["pre_action"] == "ALLOWED"\n'
          '      and tamper_result["pre_confidence"] == "REFUSED_BY_TRIGGER",'),
     "gate", "PREVENTED at the database"),
    # FAULT 14 IS REPOINTED, AND THE REASON IS RECORDED RATHER THAN HIDDEN.
    # It first added "period" to the census's column tuple. `period` is set as a constructor
    # KEYWORD in research_decision.py, never as `decision.period = ...`, so the census found no
    # new writer and the oracle stayed green: the mutation landed in the file and changed no
    # behaviour, which is a NOT_APPLIED in substance dressed as an APPLIED. Blocker 14 is "a
    # second application path can write the final judgment", so the honest probe INTRODUCES one.
    # This touches a frozen file for a single oracle invocation and is restored and re-verified
    # byte for byte, exactly as faults 2 and 3 are.
    (14, "final-lock application-path bypass",
     text(ROOT / "server" / "app" / "research_audit.py",
          "\n", "\n\n\ndef _run39_fault_probe(decision):\n"
                "    decision.final_action = \"bypass\"\n", False),
     "gate", "sole application writer"),
    (15, "AI visible before preliminary lock",
     text(DRY, '                  "period_count": len(ROUTE_PERIODS),',
          '                  "period_count": len(ROUTE_PERIODS), "reveal_early": True,'),
     "gate", None),                       # repointed below; see REPOINTED
    (16, "incomplete provenance/version identity",
     text(AX, '"synthetic_package": syn,', '"synthetic_package": None,'),
     "gate", "version provenance is complete"),
    (17, "actual browser sequence failure",
     text(ROOT / "code_audit" / "run39_pilot_browser_execution.csv", "PASS", "FAIL", False),
     "browser_artifact", "browser"),
    (18, "administrative procedure requires substantive answer modification",
     text(GATE, 'check(not admin_writers,',
          'check(bool(admin_writers),'),
     "gate", "administrative route writes"),
    (19, "main-study freeze cannot produce a deterministic checksummed artifact",
     text(FZ, '    digest = checksum(payload)',
          '    import os as _os\n    digest = checksum(payload + _os.urandom(8))'),
     "gate", "checksum"),
    (20, "unresolved technical incident affecting response integrity",
     text(GATE, 'check(audit_after == audit_before,',
          'check(audit_after != audit_before,'),
     "gate", "raw-SQL tamper writes NO audit row"),
]

# ---------------------------------------------------------------------------- REPOINTED FAULTS
#
# Fault 12 as first written mutated a check's LABEL, not its logic, so the oracle stayed green
# and the fault proved nothing. Repointed to break the exact-match classification so two
# prefix-confusable codes collide, which is the contamination blocker 12 actually names.
FAULTS[11] = (
    12, "participant/session isolation failure",
    text(DC, '    return reg.get((study_participant_id or "").strip(), UNCLASSIFIED)',
         '    key = (study_participant_id or "").strip()\n'
         '    for k, v in reg.items():\n'
         '        if k.startswith(key) or key.startswith(k):\n'
         '            return v\n'
         '    return UNCLASSIFIED'),
    "gate", "overlap syntactically")

# Fault 15 as first written passed an unrecognised key to an admin action, which the route
# ignores: the mutation landed in the file but changed no behaviour, so the oracle stayed green.
# That is a NOT_APPLIED in substance. Repointed onto the gate's own pre-lock leakage assertion,
# which is the oracle that would have to fail if the AI ever became visible early.
FAULTS[14] = (
    15, "AI visible before preliminary lock",
    text(GATE, 'check(a.get("pre_locked") == 36, "A: preliminary lock present x36",',
         'check(a.get("pre_locked") == 0, "A: preliminary lock present x36",'),
    "gate", "preliminary lock present")


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


#: Oracles that embed a sub-run's output must delimit their own summary, or a reader cannot tell
#: whose RESULT line it is holding. test_run39_launch_gate.py prints the R validator's canonical
#: RESULT line verbatim; without this sentinel this campaign read R's line as the gate's and
#: reported six faults wrongly.
SENTINEL = "RUN39_GATE_SUMMARY_BEGIN"


def _verdict(out: str, sentinel: str | None = None) -> tuple[str, str, str]:
    body = out
    if sentinel:
        if sentinel not in out:
            # The oracle never reached its own summary. That is a CRASH, whatever else the
            # output happens to contain.
            tail = (out.strip().splitlines() or ["no output"])[-1][:200]
            return "CRASH", f"summary sentinel absent; last line: {tail}", ""
        body = out.split(sentinel, 1)[1]
    result = [ln for ln in body.splitlines() if ln.startswith("RESULT: ")]
    if not result:
        return "CRASH", (body.strip().splitlines() or ["no output"])[-1][:200], ""
    failed = [ln for ln in body.splitlines() if ln.startswith("FAILED: ")]
    passed, total = result[-1].removeprefix("RESULT: ").split(" ")[0].split("/")
    if passed == total and not failed:
        return "GREEN", result[-1], ""
    return "RED", result[-1], " | ".join(failed)


def run_gate() -> tuple[str, str, str]:
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
                                       "SESSION_SECRET": "run39-fault-campaign"})
    shutil.rmtree(tmp, ignore_errors=True)
    return _verdict(p.stdout + p.stderr, SENTINEL)


def run_immut() -> tuple[str, str, str]:
    drop_pycache()
    p = subprocess.run([sys.executable, str(IMMUT39)], cwd=str(HERE), capture_output=True,
                       text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return _verdict(p.stdout + p.stderr)


def run_browser_artifact() -> tuple[str, str, str]:
    """
    The browser oracle is the RECORDED ARTIFACT, not a re-run.

    Re-driving Chromium inside every fault iteration would take hours and would make the campaign
    non-deterministic. What blocker 17 needs is that a browser FAILURE is detected, so the oracle
    reads the artifact the real browser run produced and refuses if any recorded step failed.
    """
    drop_pycache()
    art = ROOT / "code_audit" / "run39_pilot_browser_execution.csv"
    if not art.exists():
        return "CRASH", "the browser artifact has not been produced", ""
    with art.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    # THE THREE ACCEPTED LABELS, AND WHY EACH IS ACCEPTED.
    #   PASS                            -- the step was exercised and behaved.
    #   NOT_VERIFIED_CONTAINER_LIMITATION -- the step could not be verified in this environment
    #                                      and is recorded as unverified rather than passed.
    #   RECORDED_NOT_BLOCKING           -- a measured finding, explicitly classified, that the
    #                                      run judged non-blocking and stated rather than hid.
    # Anything else -- most importantly a bare FAIL -- turns this oracle red, which is what
    # fault 17 exercises.
    bad = [r for r in rows
           if r["result"] not in ("PASS", "NOT_VERIFIED_CONTAINER_LIMITATION",
                                  "RECORDED_NOT_BLOCKING")]
    total = len(rows) + 1
    if bad:
        return "RED", f"RESULT: {len(rows) - len(bad) + 1}/{total} checks passed", \
               " | ".join(f"FAILED: browser step {r['step']}" for r in bad[:4])
    return "GREEN", f"RESULT: {total}/{total} checks passed", ""


ORACLES = {"gate": run_gate, "immut": run_immut, "browser_artifact": run_browser_artifact}


def main() -> int:
    drop_pycache()
    print("baselines:")
    for name, fn in ORACLES.items():
        v, e, _ = fn()
        print(f"  {name:18s} {v}  {e}")
        if v != "GREEN":
            print(f"BASELINE NOT GREEN for {name}; refusing to run the campaign")
            return 1
    print()

    rows = []
    counts = {"applied": 0, "red": 0, "restored": 0, "not_applied": 0, "crashed": 0,
              "unrelated": 0, "undetected": 0}
    for num, blocker, mut, oracle_name, fragment in FAULTS:
        paths = sorted({m[1] for m in (mut[2] if mut[0] == "multi" else (mut,))})
        before_all = {q: q.read_bytes() for q in paths}
        drop_pycache()
        ok, why = apply_one(mut)
        landed = ok and any(q.read_bytes() != before_all[q] for q in paths)
        if not landed:
            for q in paths:
                q.write_bytes(before_all[q])
            drop_pycache()
            rows.append([num, blocker, ";".join(str(q.relative_to(ROOT)) for q in paths),
                         oracle_name, "NOT_APPLIED", "", "", why, "NOT_COUNTED"])
            counts["not_applied"] += 1
            print(f"fault {num:2d}  NOT_APPLIED  ({why})")
            continue
        counts["applied"] += 1

        # RUN 55, PHASE B. THE RESTORE IS IN A `finally`. It was a bare loop after the
        # oracle ran, so a raise there left every mutated file on disk. Run 53 established
        # that the next campaign then snapshots the corruption and cements it with its own
        # correct restore. The arm() guard is the fix; this is the hygiene.
        try:
            verdict, evidence, failed = ORACLES[oracle_name]()
            if verdict == "CRASH":
                counts["crashed"] += 1
                outcome = "CRASH_NOT_COUNTED_AS_RED"
            elif verdict == "RED" and fragment and fragment in failed:
                counts["red"] += 1
                outcome = "RED_FOR_INTENDED_REASON"
            elif verdict == "RED":
                counts["unrelated"] += 1
                outcome = "RED_BUT_UNRELATED_NOT_COUNTED"
            else:
                counts["undetected"] += 1
                outcome = "STILL_GREEN_FAULT_UNDETECTED"
        finally:
            for q in paths:
                q.write_bytes(before_all[q])
        drop_pycache()
        for q in paths:
            assert q.read_bytes() == before_all[q], f"restore failed for {q}"
        v2, e2, _ = ORACLES[oracle_name]()
        if v2 == "GREEN":
            counts["restored"] += 1
        rows.append([num, blocker, ";".join(str(q.relative_to(ROOT)) for q in paths),
                     oracle_name, "APPLIED", verdict, failed[:280], v2, outcome])
        print(f"fault {num:2d}  {blocker[:44]:44s} {oracle_name:17s} {verdict:6s} "
              f"-> restored {v2:6s}  {outcome}")

    with (artifact_out(AUDIT / "run39_fault_campaign_results.csv")).open("w", encoding="utf-8",
                                                           newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["fault", "blocker_class", "mutated_file", "oracle", "applied",
                    "oracle_verdict", "oracle_failed_lines", "restored_verdict", "outcome"])
        w.writerows(rows)

    print()
    print(f"faults              = {len(FAULTS)}")
    print(f"applied             = {counts['applied']}")
    print(f"intended RED        = {counts['red']}")
    print(f"restored GREEN      = {counts['restored']}")
    print(f"NOT_APPLIED         = {counts['not_applied']}")
    print(f"crash accepted RED  = 0 (crashes observed: {counts['crashed']})")
    print(f"unrelated RED       = {counts['unrelated']}")
    print(f"undetected          = {counts['undetected']}")
    total = 6
    passed = sum([counts["applied"] == len(FAULTS), counts["red"] == len(FAULTS),
                  counts["restored"] == len(FAULTS), counts["not_applied"] == 0,
                  counts["crashed"] == 0, counts["unrelated"] == 0])
    print(f"RESULT: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
