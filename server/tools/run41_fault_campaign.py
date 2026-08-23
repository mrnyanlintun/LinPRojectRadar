#!/usr/bin/env python3
"""
RUN 41 SECTION 17 FAULT CAMPAIGN. Twelve faults, one per named failure mode of the S1/S2 closure.

Same discipline as the Run-39 campaign, and for the same reasons:

  * baseline GREEN on every oracle before anything is injected;
  * an injection that does not change bytes on disk is NOT_APPLIED and credited to nothing;
  * A CRASH IS NOT ACCEPTED AS RED. The oracle must print its canonical RESULT line AND name a
    failing check; one that dies without doing so is CRASH and credited to nothing;
  * an unrelated RED is not evidence: the intended-reason fragment must appear in the oracle's
    own failing line;
  * __pycache__ dropped on both sides of every injection;
  * every file restored from bytes captured before injection, re-verified byte for byte, and the
    oracle must be GREEN again afterwards.

TWO FAULTS TOUCH PRODUCTION FILES (1-3 touch server/app/main.py, 4-8 and 11 touch the migration),
each for a single oracle invocation before being restored and re-verified. They have to: the
blocker classes are "the S1 serving policy was undone" and "the S2 trigger was weakened", and the
only honest way to show those are detected is to undo them and watch the guard refuse.

FAULT 12 IS THE ONE THAT PROTECTS EVERY VERSION CLAIM THIS PROGRAMME MAKES. If the instrument's
behaviour changes while the stamp stays at v25, every boundary this repository has ever asserted
is unenforced. It is injected by reverting the stamp with the behaviour change still in place, and
the version-boundary guard must refuse.

Writes code_audit/run41_fault_campaign_results.csv.
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
_cs_arm(_cs_pl.Path(ROOT), "run41_fault_campaign.py",
        allow=[])
# -------------------------------------------------------------------------------------------
AUDIT = ROOT / "code_audit"

MAIN = ROOT / "server" / "app" / "main.py"
MIGRATION = ROOT / "server" / "alembic" / "versions" / "0026_final_lock_guard.py"
MODELS = ROOT / "server" / "app" / "simulation" / "models.py"

S1_GUARD = HERE / "test_run40_serve_content_security.py"
S2_GUARD = HERE / "test_run41_final_lock_guard.py"
MIG_GUARD = HERE / "test_run41_migration_integrity.py"
PRESERVE = HERE / "test_run41_preservation.py"

TEMPLATE_DB = os.environ.get("RUN41_TEMPLATE_DB", "")


def text(path, old, new, all_=False):
    return ("text", path, (old, new, all_))


def remove(path):
    """Delete a file outright. Restored from the bytes captured before injection, like any other
    mutation."""
    return ("remove", path, None)


def multi(*subs):
    return ("multi", subs[0][1], subs)


#: (number, fault class, mutation, oracle, intended-reason fragment)
#:
#: The fragment must appear in the oracle's own failing line. It is drawn from the CHECK LABEL the
#: guard prints, never from the defect's own sentence, so a guard that merely echoed the fault
#: back could not satisfy it.
FAULTS = [
    # ---------------------------------------------------------------- S1, faults 1-3 and 10
    (1, "restore unsafe stored MIME behavior",
     text(MAIN,
          "        served_type, disposition = _safe_serve_type(doc.mime_type, doc.filename)",
          "        served_type, disposition = (doc.mime_type or 'application/octet-stream'), 'inline'"),
     "s1", "text/html is NOT echoed as Content-Type"),
    (2, "remove the S1 safe disposition and content handling",
     text(MAIN,
          '                    "X-Content-Type-Options": "nosniff",\n',
          ''),
     "s1", "X-Content-Type-Options: nosniff present"),
    (3, "permit script/HTML inline execution",
     text(MAIN,
          '    "application/pdf",\n    "image/png", "image/jpeg", "image/jpg", "image/gif", '
          '"image/webp",\n    "text/plain",',
          '    "application/pdf",\n    "image/png", "image/jpeg", "image/jpg", "image/gif", '
          '"image/webp",\n    "text/plain", "text/html", "image/svg+xml",'),
     "s1", "active content served as opaque octet-stream"),

    # ---------------------------------------------------------------- S2, faults 4-9 and 11
    (4, "remove the final-lock trigger entirely",
     text(MIGRATION,
          "    elif dialect == \"sqlite\":\n        op.execute(SQLITE_TRIGGER)",
          "    elif dialect == \"sqlite\":\n        pass"),
     "s2", "migration 0026 created trg_decisions_final_lock_guard"),
    (5, "omit final_action from the protected set",
     text(MIGRATION, '    "final_action",\n', ''),
     "s2", "[guard] final_action: raw SQL mutation REFUSED after the final lock"),
    (6, "omit final_confidence from the protected set",
     text(MIGRATION, '    "final_confidence",\n', ''),
     "s2", "[guard] final_confidence: raw SQL mutation REFUSED after the final lock"),
    (7, "omit rationale from the protected set",
     text(MIGRATION, '    "rationale",\n', ''),
     "s2", "[guard] rationale: raw SQL mutation REFUSED after the final lock"),
    # FAULT 8. The trigger is narrowed so it fires only for a write shaped like the
    # application's own (one that also touches an operational column), while a bare raw-SQL
    # UPDATE of the protected columns slips past. This is the "protects API-shaped writes but
    # raw SQL succeeds" class, and it is the exact shape a plausible-looking but useless guard
    # would have.
    (8, "trigger only protects API-shaped writes but raw SQL succeeds",
     text(MIGRATION,
          "WHEN OLD.{LOCK_COLUMN} IS NOT NULL\n     AND ({_SQLITE_CHANGED})",
          "WHEN OLD.{LOCK_COLUMN} IS NOT NULL\n     AND NEW.period IS NOT OLD.period\n"
          "     AND ({_SQLITE_CHANGED})"),
     "s2", "every protected field refuses raw mutation after lock"),
    (9, "trigger blocks legitimate pre-lock final response entry",
     text(MIGRATION,
          f"WHEN OLD.{{LOCK_COLUMN}} IS NOT NULL\n",
          "WHEN 1 = 1\n"),
     "s2", "final response entered and final-locked in the governed path"),

    # ---------------------------------------------------------------- collateral damage
    (10, "the S1 fix accidentally breaks legitimate document retrieval",
     text(MAIN,
          '    if normalized in _INLINE_SAFE:\n        return normalized, "inline"',
          '    if False:\n        return normalized, "inline"'),
     "s1", "genuine PDF still served as application/pdf"),
    # FAULT 11 WAS REPOINTED, AND THE REASON IS RECORDED RATHER THAN HIDDEN.
    # It first renamed the migration's revision id. That changes bytes on disk and changes
    # nothing else: the file is still in the versions directory and still chains from 0025, so
    # `alembic upgrade head` still ran it and the trigger was still there. The oracle stayed
    # green - a NOT_APPLIED in substance dressed up as an APPLIED, which is exactly what this
    # campaign refuses to credit. The blocker class is "the S2 migration is ABSENT on a fresh
    # database", so the honest injection makes it absent.
    (11, "the S2 migration is absent on a fresh database",
     remove(MIGRATION),
     "mig", "trg_decisions_final_lock_guard exists after a fresh migration"),

    # ---------------------------------------------------------------- the version discipline
    # FAULT 12. Behaviour has changed and the stamp is put back to v25. If this is not detected,
    # every version boundary claim this repository makes is unenforced.
    (12, "simulation remains falsely stamped v25 after the behaviour change",
     multi(text(MODELS, 'SIMULATION_VERSION = "sim-2026.08-v26"',
                'SIMULATION_VERSION = "sim-2026.08-v25"'),
           text(MODELS, '    "sim-2026.08-v26",\n', '')),
     "preserve", "the live stamp is sim-2026.08-v26"),
]


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
    if kind == "remove":
        if not path.is_file():
            return False, "the file is already absent"
        path.unlink()
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


def _verdict(out: str) -> tuple[str, str, str]:
    result = [ln for ln in out.splitlines() if ln.startswith("RESULT: ")]
    if not result:
        return "CRASH", (out.strip().splitlines() or ["no output"])[-1][:200], ""
    failed = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("FAIL  ")]
    passed, total = result[-1].removeprefix("RESULT: ").split(" ")[0].split("/")
    if passed == total and not failed:
        return "GREEN", result[-1], ""
    return "RED", result[-1], " | ".join(failed)


def _run_suite(script: pathlib.Path, fresh_db: bool = True) -> tuple[str, str, str]:
    drop_pycache()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="run41-fault-"))
    env = {**os.environ, "PYTHONIOENCODING": "utf-8",
           "SESSION_SECRET": "run41-fault-campaign"}
    if fresh_db:
        db = tmp / "gate.db"
        # A FRESH MIGRATED DATABASE PER INVOCATION, built by alembic from the tree as it stands
        # at this instant. That is essential here: faults 4-9 and 11 mutate the MIGRATION, and a
        # cached or copied template database would still carry the unmutated trigger, so the
        # oracle would report on a database the mutation never reached.
        rc = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                            cwd=str(ROOT / "server"), capture_output=True, text=True,
                            env={**env, "DATABASE_URL": f"sqlite:///{db}"})
        if rc.returncode != 0:
            # A migration that will not run IS the observable effect of faults like 11. It is
            # reported to the oracle rather than swallowed, so the oracle - not this harness -
            # decides the verdict.
            shutil.rmtree(tmp, ignore_errors=True)
            return "RED", "RESULT: 0/1 checks passed", \
                   f"FAIL  alembic upgrade head succeeds on a fresh database -- " \
                   f"{(rc.stdout + rc.stderr).strip().splitlines()[-1][:160]}"
        env["DATABASE_URL"] = f"sqlite:///{db}"
    p = subprocess.run([sys.executable, str(script)], cwd=str(HERE), capture_output=True,
                       text=True, env=env)
    shutil.rmtree(tmp, ignore_errors=True)
    return _verdict(p.stdout + p.stderr)


ORACLES = {
    "s1": lambda: _run_suite(S1_GUARD),
    "s2": lambda: _run_suite(S2_GUARD),
    "mig": lambda: _run_suite(MIG_GUARD),
    "preserve": lambda: _run_suite(PRESERVE),
}


def main() -> int:
    drop_pycache()
    print("baselines:")
    for name, fn in ORACLES.items():
        v, e, _ = fn()
        print(f"  {name:10s} {v}  {e}")
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
        # RESTORE IN A `finally` THAT CANNOT BE SKIPPED. Before Run 54 both restore paths were
        # straight-line code, so any raise in apply_one() or in an oracle left the fault on disk.
        # Hygiene, not the fix -- see server/tools/campaign_safety.py.
        with restore_guard(before_all, after=drop_pycache):
            drop_pycache()
            ok, why = apply_one(mut)
            landed = ok and any((not q.is_file()) or q.read_bytes() != before_all[q]
                                for q in paths)
            if not landed:
                rows.append([num, blocker, ";".join(str(q.relative_to(ROOT)) for q in paths),
                             oracle_name, "NOT_APPLIED", "", "", "", "NOT_COUNTED", why, ""])
                counts["not_applied"] += 1
                print(f"fault {num:2d}  NOT_APPLIED  ({why})")
                continue
            counts["applied"] += 1

            matched = ""
            verdict, evidence, failed = ORACLES[oracle_name]()
            if verdict == "CRASH":
                counts["crashed"] += 1
                outcome = "CRASH_NOT_COUNTED_AS_RED"
            elif verdict == "RED" and fragment and fragment in failed:
                counts["red"] += 1
                outcome = "RED_FOR_INTENDED_REASON"
                # RECORD THE EXACT LINE THAT CARRIED THE FRAGMENT, UNTRUNCATED. The full
                # failing-line list is truncated in the artefact for readability, and a truncated
                # list cannot support the verdict written beside it - a reader (or
                # test_run41_fault_campaign.py) checking the evidence would find the fragment
                # missing from its own record.
                matched = next((ln for ln in failed.split(" | ") if fragment in ln), "")
            elif verdict == "RED":
                counts["unrelated"] += 1
                outcome = "RED_BUT_UNRELATED_NOT_COUNTED"
            else:
                counts["undetected"] += 1
                outcome = "STILL_GREEN_FAULT_UNDETECTED"
        for q in paths:
            assert q.is_file() and q.read_bytes() == before_all[q], f"restore failed for {q}"
        v2, _e2, _f2 = ORACLES[oracle_name]()
        if v2 == "GREEN":
            counts["restored"] += 1
        rows.append([num, blocker, ";".join(str(q.relative_to(ROOT)) for q in paths),
                     oracle_name, "APPLIED", verdict, failed[:300], v2, outcome, fragment,
                     matched])
        print(f"fault {num:2d}  {blocker[:52]:52s} {oracle_name:9s} {verdict:6s} "
              f"-> restored {v2:6s}  {outcome}")

    with (AUDIT / "run41_fault_campaign_results.csv").open("w", encoding="utf-8",
                                                           newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["fault", "fault_class", "mutated_file", "oracle", "applied",
                    "oracle_verdict", "oracle_failed_lines", "restored_verdict", "outcome",
                    "intended_reason_fragment", "matched_failing_line"])
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
