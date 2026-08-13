"""
Run 19 fault-injection harness.

Supervisory specification sections 9 and 30 require that every important scientific check be
PROVEN capable of failing, that each fault change execution or bytes, that it cause a named red
test, that it occur only in a scratch copy or a controlled mutation harness, that it be restored,
and that the suite return green afterwards.

WHY A SCRATCH COPY. Run 19 is forbidden from modifying production, and prior runs in this
programme were misled by an injection that silently failed to apply, so a mutation that does not
change bytes must be detected as a harness failure rather than reported as a passing fault. This
copies the whole server tree to a temporary directory, applies the mutation there, verifies the
bytes actually changed, runs the category suite against the copy, and requires the copy to go
red. The real tree is never touched, so there is nothing to restore in it; that is proved by
hashing it before and after.

USAGE. inject(...) returns a dict of evidence rows suitable for category_<N>_faults.csv.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import subprocess
import tempfile

SERVER = pathlib.Path(__file__).resolve().parents[2]
#: The repository root. The scratch copy must include it, not merely server/, because the
#: population module resolves the registry CSV at p0-baseline/ relative to the repository root.
#: Copying server/ alone made every suite die with FileNotFoundError before its first check,
#: and a suite that CRASHES prints no RESULT line and exits nonzero, which this harness would
#: otherwise have scored as a successful red. That is a false red: the mutation was never
#: reached. Every fault below is therefore additionally required to leave the suite RUNNING,
#: printing its canonical RESULT line, with a NAMED failing check.
REPO = SERVER.parent


def _hash_tree(root: pathlib.Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        h.update(p.relative_to(root).as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def inject(faults: list[dict], suite: str) -> list[dict]:
    """
    Apply each fault to its own scratch copy of the server tree and require the suite to go red.

    Each fault is {"module_id", "fault", "file", "old", "new", "expect_red_contains"}.
    `file` is relative to server/. `old` must occur EXACTLY ONCE in that file, so a mutation
    cannot half-apply or apply somewhere unintended.
    """
    before = _hash_tree(SERVER / "app")
    rows: list[dict] = []
    for f in faults:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "repo"
            shutil.copytree(REPO, root,
                            ignore=shutil.ignore_patterns("__pycache__", ".venv", "*.pyc",
                                                          "*.db", ".pytest_cache", ".git",
                                                          "node_modules"))
            scratch = root / "server"
            target = scratch / f["file"]
            original = target.read_text(encoding="utf-8")
            occurrences = original.count(f["old"])
            if occurrences != 1:
                rows.append({
                    "module_id": f["module_id"], "fault": f["fault"], "file_mutated": f["file"],
                    "bytes_changed": "NO", "test_turned_red": "HARNESS_FAILURE",
                    "red_test_name": "",
                    "restored": "n/a (scratch copy discarded)",
                    "notes": (f"the anchor text occurs {occurrences} times, not once, so the "
                              f"mutation could not be applied unambiguously and no red is "
                              f"claimed from it"),
                })
                continue
            mutated = original.replace(f["old"], f["new"])
            target.write_text(mutated, encoding="utf-8")
            changed = len(mutated.encode()) != len(original.encode()) or mutated != original
            if not changed:
                rows.append({
                    "module_id": f["module_id"], "fault": f["fault"], "file_mutated": f["file"],
                    "bytes_changed": "NO", "test_turned_red": "HARNESS_FAILURE",
                    "red_test_name": "",
                    "restored": "n/a (scratch copy discarded)",
                    "notes": "the mutation left the file byte-identical, so it did not apply",
                })
                continue

            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            proc = subprocess.run(
                ["python3", suite], cwd=str(scratch / "tools"), env=env,
                capture_output=True, text=True, timeout=900)
            out = proc.stdout + proc.stderr
            result_line = next((ln for ln in out.splitlines()
                                if ln.startswith("RESULT:")), "")
            # A crash is NOT a red. The mutation must be reached, the suite must complete and
            # print its canonical RESULT line, and a named check must be the thing that failed.
            crashed = not result_line
            red = proc.returncode != 0 and not crashed
            named = ""
            for line in out.splitlines():
                if line.strip().startswith("- [") and f["expect_red_contains"] in line:
                    named = line.strip()[:300]
                    break
            if not named:
                for line in out.splitlines():
                    if line.strip().startswith("- [") and f["module_id"] in line:
                        named = line.strip()[:300]
                        break
            differing = sum(1 for a, b in zip(original, mutated) if a != b) \
                + abs(len(original) - len(mutated))
            rows.append({
                "module_id": f["module_id"], "fault": f["fault"], "file_mutated": f["file"],
                "bytes_changed": str(differing),
                "test_turned_red": ("YES" if (red and named) else
                                    "NO_CRASHED_INSTEAD" if crashed else "NO"),
                "red_test_name": named or "(no named check reported)",
                "restored": "n/a (scratch copy discarded; the real tree was never written to)",
                "notes": (f"exit {proc.returncode}; "
                          + (result_line or "NO RESULT LINE, the suite crashed rather than "
                                            "failing, so this is not a valid red")),
            })
    after = _hash_tree(SERVER / "app")
    for r in rows:
        r["notes"] += ("; production tree hash unchanged across the campaign"
                       if before == after else "; PRODUCTION TREE CHANGED, INVESTIGATE")
    return rows


def write_faults(path: pathlib.Path, rows: list[dict]) -> None:
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ["module_id", "fault", "file_mutated", "bytes_changed", "test_turned_red",
            "red_test_name", "restored", "notes"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def all_red(rows: list[dict]) -> bool:
    return bool(rows) and all(r["test_turned_red"] == "YES" for r in rows)
