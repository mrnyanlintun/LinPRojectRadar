"""
RUN 32 FINAL CLOSURE. THE TEN-FAULT NON-VACUITY CAMPAIGN FOR THE DEFENSIBILITY GUARDS.

A GREEN GUARD PROVES NOTHING BY ITSELF. `test_run11_defensibility_claims.py` was green for two
runs while twenty-two modules were served a false statement about their own structure
requirement, because it compares the generated file against the generator that generated it: if
the derivation is wrong, both sides are wrong together and the check still passes. So every guard
this closure relies on is broken on purpose here and required to go RED FOR THE INTENDED REASON.

THE SAME DISCIPLINE AS THE 32-FAULT CAMPAIGN, and for the same reasons:

  * a CRASH IS NOT RED -- a guard that dies without printing an anchored `RESULT: n/m` line is
    recorded as a crash and the fault is NOT counted;
  * an UNRELATED FAILURE IS NOT EVIDENCE -- the intended property must appear among the guard's
    OWN failing check sentences, so a passing line carrying the same words cannot be credited;
  * the MUTATION IS VERIFIED BY RE-READING THE BYTES FROM DISK, never assumed to have landed;
  * `__pycache__` is cleared on BOTH sides, because a restore inside the same clock second changes
    neither mtime nor size and a cached mutant would survive it;
  * every file is restored BYTE FOR BYTE and the baseline is re-run and required to be GREEN.

Writes code_audit/run32_closure_fault_injection.csv. Run with PYTHONIOENCODING=utf-8.
"""

from __future__ import annotations

import csv
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SERVER = HERE.parent
ROOT = SERVER.parent

TRUTH = "test_run32_defensibility_truth.py"
PACKAGES = "test_run28_participant_packages.py"

EVIDENCE = ROOT / "assets" / "js" / "ds_defensibility_evidence.js"
CATEGORIES = ROOT / "assets" / "js" / "categories.js"
V7_RECORD = ROOT / "code_audit" / "run32_participant_package_v7_checksums.sha256"


def clear_pycache() -> None:
    for d in SERVER.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


_TEMPLATE = None


def template_db() -> pathlib.Path:
    global _TEMPLATE
    if _TEMPLATE is None:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="run32closure-"))
        db = tmp / "template.db"
        env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}",
                   SESSION_SECRET="test-secret-do-not-use-in-prod")
        r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                           cwd=SERVER, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("alembic upgrade head FAILED:\n" + r.stdout + r.stderr)
        _TEMPLATE = db
    return _TEMPLATE


def run_guard(suite: str) -> tuple[int, str, str | None]:
    tmpl = template_db()
    db = tmpl.parent / f"{suite}.{os.getpid()}.db"
    shutil.copy(tmpl, db)
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}",
               SESSION_SECRET="test-secret-do-not-use-in-prod", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, suite], cwd=HERE, env=env,
                       capture_output=True, text=True, timeout=1800)
    out = (r.stdout or "") + (r.stderr or "")
    result = None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("RESULT: ") and "/" in s:
            result = s
    db.unlink(missing_ok=True)
    return r.returncode, out, result


def failing_lines(out: str) -> list[str]:
    lines = []
    for raw in out.splitlines():
        s = raw.strip()
        if s.startswith("FAIL: ") or s.startswith("FAILED: "):
            lines.append(s.split(": ", 1)[1])
        elif s.startswith("FAIL "):
            lines.append(s[5:])
        elif s.startswith("**** "):
            lines.append(s[5:].strip())
        elif s.startswith("- "):
            lines.append(s[2:])
    return lines


def is_green(result: str | None) -> bool:
    if not result:
        return False
    a, b = result.split("RESULT: ", 1)[1].split()[0].split("/")
    return a == b


def field(mid: str, name: str, value: str) -> tuple[pathlib.Path, str, str]:
    """
    A mutation that rewrites ONE field of ONE module in the served evidence object.

    THE ANCHOR IS THE WHOLE MODULE ENTRY, not the field. Field text is shared across modules --
    seventy-seven of them carry the same conditional-execution sentence and eight carry
    DISABLED_CONCEPT_ONLY -- so anchoring on the field alone matches many places and the campaign
    correctly refused to apply it. The entry line is unique because the module id is.
    """
    txt = EVIDENCE.read_text(encoding="utf-8")
    m = re.search(r'"%s": \{.*?\},\n' % re.escape(mid), txt, re.S)
    if m is None:
        raise SystemExit(f"{mid} not found in the served object")
    entry = m.group(0)
    fm = re.search(r'(\b%s: )("(?:[^"\\]|\\.)*"|true|false|null)' % re.escape(name), entry)
    if fm is None:
        raise SystemExit(f"{mid}.{name} not found")
    mutated = entry.replace(fm.group(0), fm.group(1) + value, 1)
    return EVIDENCE, entry, mutated


#: (id, system, invariant, target, old bytes, new bytes, guard, intended RED reason)
def faults() -> list[tuple]:
    F = []

    # 1 -- B4.7's CURRENT CLIENT NAME PUT BACK TO THE SUPERSEDED IDENTIFIER.
    F.append((1, "assets/js/categories.js, B4.7 taxonomy row",
              "the participant-facing taxonomy carries B4.7's CURRENT method-class identifier, "
              "the one the runner actually emits",
              CATEGORIES,
              "method_class: 'Minimax_Regret_Decision_Rule'",
              "method_class: 'Regret_Minimization'",
              TRUTH,
              "assets/js/categories.js: and its method class is the identifier the runner "
              "actually emits"))

    # 2 -- B4.7 DESCRIBED AS CURRENTLY COMPUTING DESPITE ITS MISSING PAYOFF MATRIX.
    t, o, n = field("B4.7", "implementation",
                    '"the current production runner computes the canonical method from the '
                    'governed evidence the platform already holds"')
    F.append((2, "B4.7 Minimax Regret Decision Rule, served execution statement",
              "a module that returns Not Estimable for want of its governed action-by-scenario "
              "matrix is never described as currently computing a project reading",
              t, o, n, TRUTH,
              "every served execution statement is the one the module's current route supports"))

    # 3 -- A CANONICAL CONDITIONAL METHOD MARKED AS REQUIRING NO STRUCTURE.
    t, o, n = field("B4.3", "canonicalStructureRequired", "false")
    F.append((3, "B4.3 Constraint Satisfaction Analysis, canonicalStructureRequired",
              "the machine-readable structure-requirement flag agrees with the sentence beside "
              "it and with the canonical layer that declares the structure",
              t, o, n, TRUTH,
              "and the machine-readable canonicalStructureRequired agrees with it"))

    # 4 -- A DISABLED METHOD DESCRIBED AS OPERATIONAL.
    t, o, n = field("B4.1", "operationalState", '"COMPUTES_FROM_AVAILABLE_EVIDENCE"')
    F.append((4, "B4.1 Multi-Objective Optimization, a disabled concept-only module",
              "a disabled module produces no live project reading and is never served as one "
              "that computes",
              t, o, n, TRUTH,
              "every served operationalState matches the derived state"))

    # 5 -- QUANTUM PROBABILITY DESCRIBED AS RUNNABLE.
    t, o, n = field("B2.9", "operationalState", '"CONDITIONAL_ON_GOVERNED_STRUCTURE"')
    F.append((5, "B2.9 Quantum Probability, archived future research",
              "an archived method is kept as part of the research record and is never presented "
              "as a runnable current capability",
              t, o, n, TRUTH,
              "B2.9 Quantum Probability is served as archived research and not as a runnable "
              "capability"))

    # 6 -- A SUPPLIED VALUE DESCRIBED AS SERVER-COMPUTED.
    t, o, n = field("A4.1", "operationalState", '"COMPUTES_FROM_AVAILABLE_EVIDENCE"')
    F.append((6, "A4.1 Document Risk Score, a supplied value",
              "the platform consumes this value; it does not compute it, and the object must not "
              "claim an analytical module behind it",
              t, o, n, TRUTH,
              "A4.1 Document Risk Score is served as a supplied value and not as a server "
              "computation"))

    # 7 -- THE CURRENT CANONICAL RUNNER REPLACED IN METADATA BY ITS HISTORICAL PROXY.
    #      THIS IS THE RUN-30 LESSON: a correct library behind an unchanged route.
    t, o, n = field("B4.7", "canonicalRunner",
                    '"app.simulation.models_gov.run_regret_minimization"')
    F.append((7, "B4.7 canonicalRunner, swapped for the preserved v19 proxy",
              "the served runner is the implementation a production dispatch actually reaches, "
              "resolved past the Category-9 boundary, and not a historical proxy",
              t, o, n, TRUTH,
              "every served canonicalRunner is the implementation a production dispatch actually "
              "reaches"))

    # 8 -- A CURRENT REGISTRY MODULE OMITTED FROM THE OBJECT.
    txt = EVIDENCE.read_text(encoding="utf-8")
    m = re.search(r'    "B3\.3": \{.*?\},\n', txt, re.S)
    F.append((8, "B3.3, omitted from the served defensibility object",
              "every current registry identity has a served defensibility record; a module cannot "
              "disappear from the object while remaining in the registry",
              EVIDENCE, m.group(0), "", TRUTH,
              "every current registry identity has a served defensibility record"))

    # 9 -- A MODULE THAT DOES NOT EXIST ADDED TO THE OBJECT.
    F.append((9, "a fabricated identity added to the served object",
              "the served object invents no module the registry does not declare",
              EVIDENCE, '  modules: {\n',
              '  modules: {\n    "B9.9": { name: "Fabricated Capability", implementation: "x", '
              'operationalState: "COMPUTES_FROM_AVAILABLE_EVIDENCE", '
              'canonicalStructureRequired: false, definingStructure: null, canonicalRunner: "x", '
              'knownAnswer: "x", boundary: "x", calibration: "x", empirical: "x", '
              'canonicalStructure: "x", voting: "x", permittedClaim: "x", qualification: "x" },\n',
              TRUTH,
              "and the served object invents no module the registry does not declare"))

    # 10 -- A PREDECESSOR PARTICIPANT PACKAGE REGENERATED TO AGREE WITH THE PRESENT.
    #       THIS PROGRAMME HAS COMMITTED THIS DEFECT BEFORE, in the v2 record at the Run-28
    #       closure, and had to undo it.
    old_line = [l for l in V7_RECORD.read_text(encoding="utf-8").splitlines()
                if l.strip().endswith("assets/js/categories.js")][0]
    import hashlib
    live = hashlib.sha256((ROOT / "assets/js/categories.js").read_bytes()).hexdigest()
    F.append((10, "og-participant-2026.08-v7, a predecessor record",
              "a predecessor package is never regenerated to match the current tree; it stays "
              "pinned to the commit whose blobs it describes",
              V7_RECORD, old_line, f"{live}  assets/js/categories.js", PACKAGES,
              "every one of v7's seventy checksums holds against commit"))
    return F


def main() -> int:
    HDR = ["fault_id", "module/system", "invariant", "baseline command", "mutation target",
           "mutation description", "mutation applied?", "fault command", "process exit code",
           "anchored RESULT present?", "expected RED reason", "actual RED reason", "crash?",
           "unrelated failure?", "restored?", "restored GREEN?", "final status", "notes"]
    rows = []
    tally = dict(attempted=0, applied=0, intended=0, restored=0, not_applied=0,
                 crashes=0, unrelated=0)

    for fid, system, invariant, target, old, new, guard, reason in faults():
        tally["attempted"] += 1
        cmd = f"cd server/tools && python3 {guard}"
        clear_pycache()
        brc, bout, bres = run_guard(guard)
        if not is_green(bres):
            rows.append([fid, system, invariant, cmd, str(target), "-", "NO", cmd, brc,
                         "YES" if bres else "NO", reason, "-", "NO", "NO", "n/a", "NO",
                         "NOT_ATTEMPTED_BASELINE_RED", f"baseline was not green ({bres})"])
            tally["not_applied"] += 1
            continue
        baseline = bres

        original = target.read_bytes()
        text = original.decode("utf-8")
        if text.count(old) != 1:
            rows.append([fid, system, invariant, cmd, str(target.relative_to(ROOT)),
                         "anchor not unique", "NO", cmd, "-", "YES", reason, "-", "NO", "NO",
                         "n/a", "n/a", "NOT_APPLIED",
                         f"anchor occurs {text.count(old)} times, not once"])
            tally["not_applied"] += 1
            continue

        clear_pycache()
        target.write_bytes(text.replace(old, new, 1).encode("utf-8"))
        on_disk = target.read_bytes().decode("utf-8")
        applied = (new in on_disk if new else old not in on_disk) and on_disk != text
        if not applied:
            target.write_bytes(original)
            clear_pycache()
            rows.append([fid, system, invariant, cmd, str(target.relative_to(ROOT)),
                         "byte replacement", "NO", cmd, "-", "YES", reason, "-", "NO", "NO",
                         "YES", "n/a", "NOT_APPLIED",
                         "the mutation did not survive a re-read from disk"])
            tally["not_applied"] += 1
            continue
        tally["applied"] += 1

        frc, fout, fres = run_guard(guard)
        crash = fres is None
        red = (fres is not None) and (not is_green(fres))
        fails = failing_lines(fout)
        hit = [f for f in fails if reason.strip().lower() in f.strip().lower()]
        intended = red and bool(hit)
        actual = ("no RESULT line (crash)" if crash else
                  ("; ".join(dict.fromkeys(f.strip()[:110] for f in fails)) or fres) if red
                  else "GREEN - guard did not notice")

        clear_pycache()
        target.write_bytes(original)
        restored = target.read_bytes() == original
        clear_pycache()
        rrc, rout, rres = run_guard(guard)
        rgreen = is_green(rres) and rres == baseline

        notes = []
        if crash:
            tally["crashes"] += 1
            status = "CRASH_NOT_ACCEPTED_AS_RED"
            notes.append("the guard died without an anchored RESULT line; a crash is NOT red")
        elif not red:
            status = "GUARD_DID_NOT_FIRE"
            notes.append("the guard stayed green under the mutation")
        elif not intended:
            tally["unrelated"] += 1
            status = "RED_FOR_AN_UNRELATED_REASON"
            notes.append("red, but its output did not name the intended property")
        else:
            tally["intended"] += 1
            status = "RED_FOR_THE_INTENDED_REASON"
        if rgreen:
            tally["restored"] += 1
        else:
            notes.append(f"baseline did not return to {baseline} (got {rres})")

        rows.append([fid, system, invariant, cmd, str(target.relative_to(ROOT)),
                     f"replace {old.strip().splitlines()[0][:70]!r}", "YES", cmd, frc,
                     "NO" if crash else "YES", reason, actual, "YES" if crash else "NO",
                     "YES" if (red and not intended) else "NO", "YES" if restored else "NO",
                     "YES" if rgreen else "NO", status, "; ".join(notes) or "clean"])
        print(f"fault {fid:2d}  {status:32s}  {actual[:88]}")

    out = ROOT / "code_audit" / "run32_closure_fault_injection.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HDR)
        w.writerows(rows)
    print()
    print("attempted        ", tally["attempted"])
    print("applied          ", tally["applied"])
    print("intended RED     ", tally["intended"])
    print("restored GREEN   ", tally["restored"])
    print("NOT_APPLIED      ", tally["not_applied"])
    print("crashes as RED   ", 0, f"({tally['crashes']} recorded, NOT counted)")
    print("unrelated as RED ", 0, f"({tally['unrelated']} recorded, NOT counted)")
    print("wrote", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
