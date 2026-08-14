#!/usr/bin/env python3
"""
RUN 28. THE NON-VACUITY CAMPAIGN: SIX FAULTS, EACH PROVEN TO TURN A GUARD RED.

WHY THIS FILE EXISTS. Sixteen-plus vacuous guards have been found in this programme's recent
runs, and the owner's Run-28 prompt names the five ways they go vacuous: a check crashed rather
than failing and printed no RESULT line; an injection silently failed to apply; a fixture built
state by a route the application does not take; a check asserted against a copy of the logic; a
check asserted the defect's own sentence verbatim. This campaign answers the first two directly
and is designed so the other three cannot hide in it.

THE DISCIPLINE, APPLIED TO EVERY FAULT WITHOUT EXCEPTION:

  1. RECHECK THE BASELINE. The target guard is run first and must be GREEN. A guard that was
     already red proves nothing when it is red again.
  2. INJECT into the real file on disk.
  3. CONFIRM THE INJECTION TOOK EFFECT by RE-READING THE FILE FROM DISK and requiring the bytes
     to have changed and the intended text to be present. An injection that silently failed to
     apply is the second failure mode on the owner's list, and it is the one that makes a whole
     campaign worthless.
  4. RUN THE GUARD and require it to be RED FOR THE INTENDED REASON. A crash is NOT red: the
     runner requires an anchored RESULT line, and a suite that dies without printing one is
     recorded as CRASHED and counted as a FAILURE of the campaign, not as a success.
  5. RESTORE the file from the bytes captured before the injection.
  6. RECHECK THE BASELINE AGAIN and require GREEN. This is what proves the restore was complete
     and that nothing later in the campaign runs against a mutated tree.

Every injection is made against a copy of the repository's own bytes and restored from them, and
the campaign asserts at the end that every touched file is byte-identical to how it started.

Run:  PYTHONIOENCODING=utf-8 python3 server/tools/run28_fault_campaign.py
Writes: code_audit/run28_fault_injection.csv
"""

from __future__ import annotations

import csv
import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "code_audit" / "run28_fault_injection.csv"

RESULT_RE = re.compile(r"^RESULT: (\d+)/(\d+)( checks passed)?$", re.M)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _drop_bytecode(path: pathlib.Path) -> None:
    """
    THE CAMPAIGN-INTEGRITY DEFECT THIS FUNCTION EXISTS FOR, AND IT WAS FOUND BY RUNNING THE
    CAMPAIGN RATHER THAN BY READING IT.

    The first run of this campaign restored the mutated source byte for byte -- the digest check
    at step 5 confirmed it -- and the baseline STILL came back red at step 6. The source on disk
    was correct and the behaviour was not, because CPython had cached the compiled mutant. Its
    cache is invalidated on the source's modification time and size, and an injection that
    replaces a line with one of similar length, restored inside the same clock second, changes
    neither. The stale bytecode was then imported in preference to the restored source.

    That is the owner's second failure mode wearing an unfamiliar coat: not an injection that
    failed to apply, but a RESTORE that failed to apply while every byte-level check said it had.
    A campaign that did not notice would have left a mutated analytical layer running under a
    green report, and every fault after it would have been measured against a corrupted tree.

    So the compiled cache for the touched file is removed on both sides of every injection. It is
    removed after the INJECTION too, not only after the restore, because the same staleness would
    otherwise let a mutant be written and the unmutated cache be executed -- which would show the
    guard staying green and be recorded as a vacuous guard that is nothing of the kind.
    """
    cache = path.parent / "__pycache__"
    if not cache.is_dir():
        return
    for pyc in cache.glob(f"{path.stem}.*.pyc"):
        pyc.unlink(missing_ok=True)


_TEMPLATE: pathlib.Path | None = None


def _template_db() -> pathlib.Path:
    """One migrated sqlite template, copied per suite run so no run reuses another's state."""
    global _TEMPLATE
    if _TEMPLATE is None:
        d = pathlib.Path(tempfile.mkdtemp(prefix="run28camp-"))
        db = d / "template.db"
        env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}", SESSION_SECRET="run28-campaign",
                   PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                           cwd=str(ROOT / "server"), env=env, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"alembic upgrade head failed:\n{r.stdout}\n{r.stderr}")
        _TEMPLATE = db
    return _TEMPLATE


def run_suite(name: str) -> tuple[str, str]:
    """
    Run one suite exactly as server/run_all_suites.sh does and classify the outcome.

    Returns (verdict, detail) where verdict is GREEN, RED or CRASHED. CRASHED means the suite
    produced no anchored RESULT line, which the owner's prompt names explicitly: a crash is not
    a red test, and this campaign refuses to count one as evidence.
    """
    template = _template_db()
    db = template.with_name(f"{name}.{os.getpid()}.db")
    shutil.copy(template, db)
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}", SESSION_SECRET="run28-campaign",
               PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, name], cwd=str(ROOT / "server" / "tools"),
                       env=env, capture_output=True, text=True, timeout=1800)
    out = (r.stdout or "") + (r.stderr or "")
    m = None
    for m in RESULT_RE.finditer(out):
        pass
    db.unlink(missing_ok=True)
    if m is None:
        tail = " | ".join(x for x in out.strip().splitlines()[-3:])
        return "CRASHED", f"no anchored RESULT line; exit {r.returncode}; tail: {tail[:220]}"
    passed, total = int(m.group(1)), int(m.group(2))
    if passed == total and r.returncode == 0:
        return "GREEN", f"{passed}/{total}"
    return "RED", f"{passed}/{total}, exit {r.returncode}"


ROWS: list[dict] = []
FAILURES: list[str] = []


def campaign(fault_id: str, what: str, rel: str, old: str, new: str, suite: str,
             expect_reason: str) -> None:
    """One fault, run through the six steps in the docstring above."""
    path = ROOT / rel
    before_bytes = path.read_bytes()
    before_sha = hashlib.sha256(before_bytes).hexdigest()

    baseline, baseline_detail = run_suite(suite)
    if baseline != "GREEN":
        FAILURES.append(f"{fault_id}: BASELINE NOT GREEN before injection ({baseline_detail}); "
                        f"a guard that was already red proves nothing when it is red again")

    text = before_bytes.decode("utf-8")
    if old not in text:
        FAILURES.append(f"{fault_id}: the text to be replaced is not in {rel}; the injection "
                        f"could not even be attempted")
        ROWS.append({"fault_id": fault_id, "what_was_broken": what, "file": rel,
                     "guard": suite, "baseline_before": baseline_detail,
                     "injection_applied": "NO", "observed": "NOT ATTEMPTED",
                     "expected_reason": expect_reason, "baseline_after": "n/a",
                     "bytes_restored": "n/a", "verdict": "CAMPAIGN FAILURE"})
        return
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    _drop_bytecode(path)

    # STEP 3. CONFIRM THE INJECTION TOOK EFFECT, by re-reading the file FROM DISK.
    reread = path.read_bytes()
    applied = (hashlib.sha256(reread).hexdigest() != before_sha
               and new in reread.decode("utf-8")
               and old not in reread.decode("utf-8"))
    if not applied:
        path.write_bytes(before_bytes)
        _drop_bytecode(path)
        FAILURES.append(f"{fault_id}: THE INJECTION DID NOT TAKE EFFECT on disk")
        ROWS.append({"fault_id": fault_id, "what_was_broken": what, "file": rel,
                     "guard": suite, "baseline_before": baseline_detail,
                     "injection_applied": "NO", "observed": "NOT RUN",
                     "expected_reason": expect_reason, "baseline_after": "n/a",
                     "bytes_restored": "yes", "verdict": "CAMPAIGN FAILURE"})
        return

    verdict, detail = run_suite(suite)

    path.write_bytes(before_bytes)
    _drop_bytecode(path)
    restored = sha(path) == before_sha
    after, after_detail = run_suite(suite)

    ok = verdict == "RED" and restored and after == "GREEN"
    if verdict == "CRASHED":
        FAILURES.append(f"{fault_id}: the guard CRASHED rather than failing ({detail}). A crash "
                        f"is not a red test and this counts as a campaign failure.")
    elif verdict != "RED":
        FAILURES.append(f"{fault_id}: the guard did not go red ({detail}); it is vacuous for "
                        f"this fault")
    if not restored:
        FAILURES.append(f"{fault_id}: {rel} was NOT restored byte for byte")
    if after != "GREEN":
        FAILURES.append(f"{fault_id}: the baseline is not green again after restore "
                        f"({after_detail})")

    ROWS.append({"fault_id": fault_id, "what_was_broken": what, "file": rel, "guard": suite,
                 "baseline_before": f"GREEN {baseline_detail}",
                 "injection_applied": "YES, confirmed by re-reading the file from disk",
                 "observed": f"{verdict} {detail}", "expected_reason": expect_reason,
                 "baseline_after": f"{after} {after_detail}",
                 "bytes_restored": "yes" if restored else "NO",
                 "verdict": "PROVEN NON-VACUOUS" if ok else "CAMPAIGN FAILURE"})
    print(f"  {fault_id}: baseline GREEN -> injected -> {verdict} ({detail}) -> restored -> "
          f"{after}")


def main() -> int:
    print("RUN 28 NON-VACUITY CAMPAIGN: six faults, each proven to turn a guard red\n")

    # ---------------------------------------------------------------- F1: a v2 frozen-byte
    # violation.
    #
    # WHERE THE FROZEN v2 BYTES ACTUALLY LIVE, WHICH IS WHY THIS FAULT TAKES THE FORM IT DOES.
    # There are two records of the frozen line and neither is a working-tree file that could be
    # edited by accident. The analytical package as it shipped at sim-2026.08-v2 is extracted
    # from GIT at the pinned commit 021d5e2 by test_run7_fix_now_defects.py, which imports and
    # EXECUTES it and compares it against the current line on identical inputs; a git object
    # cannot be mutated in place, and that is the point of pinning it there. The digests of the
    # frozen production tree live in code_audit/run20_production_freeze.sha256, which the
    # declared-changes guard describes as IMMOVABLE and which no run may regenerate: a baseline
    # rewritten to agree with production agrees with it by construction and can never catch an
    # undeclared edit.
    #
    # So the frozen-byte violation this campaign injects is a corruption of THAT record: the
    # recorded digest of a simulation source is altered, which is exactly what a run quietly
    # regenerating the freeze to make its own edits look clean would do. The guard carries a
    # check written for precisely this -- "the freeze is genuinely frozen: it still records the
    # pre-cycle-1 bytes of the file cycle 1 changed, so it has not been regenerated against
    # current production" -- and it must go red.
    campaign(
        "F1", "the immovable Run-20 production freeze's recorded digest for a simulation source",
        "code_audit/run20_production_freeze.sha256",
        "8911c9d86fc73fd913907cb9b489a5649d2b400cfaa7cc26dcdf9c66e65bb5d3  "
        "server/app/simulation/models_ext.py",
        "0000000000000000000000000000000000000000000000000000000000000000  "
        "server/app/simulation/models_ext.py",
        "test_run20_declared_production_changes.py",
        "the Run-20 freeze must still record the bytes it recorded, so it cannot have been "
        "regenerated against current production to make an undeclared edit look clean")

    # ---------------------------------------------------------------- F2: a v3 version mismatch
    campaign(
        "F2", "the new analytical line's version stamp",
        "server/app/simulation/models.py",
        'SIMULATION_VERSION = "sim-2026.08-v11"',
        'SIMULATION_VERSION = "sim-2026.08-v3"',
        "test_run6_known_answer.py",
        "the stamp must be the new line's, and must be the last of the recorded history, so a "
        "collision with an identifier results were already collected under is detectable")

    # ---------------------------------------------------------------- F3: a missing canonical
    # input reaching a reading. The Earned Schedule module must refuse without the cumulative
    # planned value curve. Making it fall back to the percent-complete ratio is the exact
    # substitution the supplied contract forbids by name.
    campaign(
        "F3", "Earned Schedule's refusal when the cumulative planned value curve is absent",
        "server/app/simulation/models_evm.py",
        '        structure = require_v3_structure(si, "A1.6")\n'
        '        baseline = time_phased_baseline(structure)',
        '        structure = si.get("timePhasedBaseline") or {\n'
        '            "baseline_version": "x", "approval_source": "x", "periods": [\n'
        '                {"period_index": 0, "period": "P0", "cumulative_pv": 0},\n'
        '                {"period_index": 1, "period": "P1", "cumulative_pv": 100}],\n'
        '            "actual_time_periods": 1}\n'
        '        baseline = time_phased_baseline(structure)',
        "test_run17_scientific_methods.py",
        "with no cumulative planned value curve the answer must be Not Estimable, and no "
        "percent-complete ratio may be offered in its place")

    # ---------------------------------------------------------------- F4: a fabricated default
    # result from absent data. The reference class forecast must refuse without a governed
    # population. Reinstating an embedded fixed multiplier is the defect Run 7 removed and the
    # supplied contract forbids in terms.
    campaign(
        "F4", "Reference Class Forecasting's refusal when no governed reference class is held",
        "server/app/simulation/models.py",
        '        structure = require_v3_structure(si, "A3.1")',
        '        structure = si.get("referenceClassPopulation") or {\n'
        '            "governed_percentile": 0.5, "inclusion_criteria": "x",\n'
        '            "exclusion_criteria": "x", "outcome_definition": "x",\n'
        '            "normalization": "x", "data_vintage": "x",\n'
        '            "members": [{"reference_project_id": f"R{i}",\n'
        '                         "proportional_overrun": 0.38} for i in range(9)]}',
        "test_risk_register_and_notices.py",
        "with no retrieved governed reference class the answer must be Not Estimable, and no "
        "embedded fixed multiplier may stand in for an outside view")

    # ---------------------------------------------------------------- F5: an unauthorised
    # rename. Only two Category 1-3 renames are authorised in Run 28. Renaming a third module in
    # the registry map must be caught.
    campaign(
        "F5", "an unauthorised rename of a third Category-1 module in the registry map",
        "p0-baseline/module_renumbering_map.csv",
        "A1.9,Budget Execution Rate,",
        "A1.9,PCEIF Expenditure Control Indicator,",
        "test_run17_scientific_methods.py",
        "the registry's name for every module must agree with the supervisory specification's "
        "own list, and only the two owner-approved renames may differ")

    # ---------------------------------------------------------------- F6: an oracle-breaking
    # production mutation. The normal-normal posterior is the arithmetic the supplied contract
    # states and hand-checks. Breaking the precision weighting must be caught by the oracle.
    campaign(
        "F6", "the normal-normal posterior's precision weighting",
        "server/app/simulation/canonical_v3.py",
        "    posterior_var = 1.0 / (1.0 / prior_var + 1.0 / observation_var)",
        "    posterior_var = 1.0 / (1.0 / prior_var - 0.5 / observation_var)",
        "test_run17_scientific_methods.py",
        "the posterior variance of a normal-normal update on the specification's own worked "
        "example must be 50 and its mean must be 110")

    # ------------------------------------------------------------------------ the write-out
    OUT.write_text("", encoding="utf-8")
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ROWS[0].keys()))
        w.writeheader()
        for row in ROWS:
            w.writerow(row)
    print(f"\nwrote {OUT.relative_to(ROOT)}: {len(ROWS)} faults")

    proven = sum(1 for r in ROWS if r["verdict"] == "PROVEN NON-VACUOUS")
    print(f"RESULT: {proven}/{len(ROWS)} checks passed")
    if FAILURES:
        print("\nCAMPAIGN FAILURES:")
        for f in FAILURES:
            print("  -", f)
    return 0 if proven == len(ROWS) and not FAILURES else 1


if __name__ == "__main__":
    raise SystemExit(main())
