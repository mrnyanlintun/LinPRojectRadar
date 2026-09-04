#!/usr/bin/env python3
"""
RUN 135C. THE CHECK RULING R4 REQUIRES: NO SCRIPT CLASSIFIED ACTIVE MAY CRASH.

WHY THIS FILE EXISTS. H10 found 177 of the fleet's active qualification tests dying mid-run --
an ImportError, a MissingModuleError on a retired id, a KeyError in a hardcoded dict -- with the
checks below the crash point never reached. A crashed suite prints no RESULT line, and a suite
that prints no RESULT line reads, to anyone scanning output, exactly like one that had nothing to
say. That is the mechanism by which H8 survived twenty runs and by which tools/test_simulation.py
was dead for seventy-four commits without a single run noticing.

WHAT IT ASSERTS, AND WHAT IT DELIBERATELY DOES NOT. It asserts that every script classified
`active` in tools/TOOLS_CLASSIFICATION.csv RUNS TO COMPLETION: it either exits 0, or it exits
non-zero having printed a RESULT line, which is what a suite reporting its own failures looks
like. It does NOT assert that those suites pass. A red suite is a finding and belongs in a report;
a crashed suite is not a finding at all, because nobody knows what it would have said. Conflating
the two is what this check exists to stop.

  crash     -> FAIL here. The suite never reached its own verdict.
  failures  -> PASS here, and the failure count is printed. Someone else's problem, reported.
  exit 0    -> PASS here.

Readers, migration tools and retired artefacts are EXCLUDED, by kind, from the CSV -- not by
being edited, and not by being counted as failures. That is R4's instruction and the reason the
CSV exists.

RUNNING IT. Executing 237 scripts takes hours, so the default mode reads the exit codes and
captured output of a fleet run rather than performing one:

    python tools/test_run135c_active_suite_completes.py --fleet-dir <dir> [--exit-tsv <file>]

`--fleet-dir` holds `<path with / replaced by _>.out` / `.err` per script and `--exit-tsv` is
`<path>\\t<exit code>` per line, which is what a plain shell loop produces. With `--run` it runs
the active set itself, honouring `--timeout` and `--limit`, and writes the same layout so a later
invocation can re-read it.

A script that the fleet did not cover is a FAILURE, not a skip: an active qualification test that
nobody ran is indistinguishable in its consequences from one that crashed.
"""
from __future__ import annotations

import argparse
import csv
import os
import pathlib
import subprocess
import sys

SERVER = pathlib.Path(__file__).resolve().parent.parent
CSV_PATH = SERVER / "tools" / "TOOLS_CLASSIFICATION.csv"

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def active_paths() -> list[str]:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        return [r["path"] for r in csv.DictReader(fh) if r["kind"] == "active"]


def key_for(path: str) -> str:
    """`server/tools/x.py` -> `tools/x.py`, the key a run from server/ uses."""
    return path[len("server/"):] if path.startswith("server/") else path


def run_active(paths: list[str], fleet_dir: pathlib.Path, timeout: int,
               exit_tsv: pathlib.Path) -> None:
    fleet_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, p in enumerate(paths, 1):
        k = key_for(p)
        stem = k.replace("/", "_")
        print(f"  [{i}/{len(paths)}] {k}", flush=True)
        try:
            proc = subprocess.run([sys.executable, k], cwd=SERVER, timeout=timeout,
                                  capture_output=True, env=dict(os.environ))
            code, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            code, out, err = 124, exc.stdout or b"", exc.stderr or b""
        (fleet_dir / f"{stem}.out").write_bytes(out)
        (fleet_dir / f"{stem}.err").write_bytes(err)
        lines.append(f"{k}\t{code}")
    exit_tsv.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fleet-dir", default=None)
    ap.add_argument("--exit-tsv", default=None)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not CSV_PATH.exists():
        print(f"FAIL  {CSV_PATH} is missing; run tools/run135c_classify_tooling.py first")
        return 2
    paths = active_paths()
    if args.limit:
        paths = paths[:args.limit]

    fleet_dir = pathlib.Path(args.fleet_dir) if args.fleet_dir else None
    exit_tsv = pathlib.Path(args.exit_tsv) if args.exit_tsv else (
        fleet_dir.parent / "fleet_exit.tsv" if fleet_dir else None)

    if args.run:
        if fleet_dir is None:
            print("FAIL  --run requires --fleet-dir")
            return 2
        run_active(paths, fleet_dir, args.timeout, exit_tsv)

    if fleet_dir is None or exit_tsv is None or not exit_tsv.exists():
        print("FAIL  no fleet evidence: pass --fleet-dir and --exit-tsv, or --run")
        return 2

    exits: dict[str, int] = {}
    for line in exit_tsv.read_text().splitlines():
        if "\t" in line:
            k, c = line.rsplit("\t", 1)
            exits[k] = int(c)

    print("=" * 78)
    print(f"ACTIVE SET: {len(paths)} scripts classified active in {CSV_PATH.name}")
    print("=" * 78)
    crashed: list[tuple[str, str]] = []
    uncovered: list[str] = []
    completed_with_failures: list[str] = []
    clean = 0
    for p in paths:
        k = key_for(p)
        if k not in exits:
            uncovered.append(k)
            continue
        code = exits[k]
        stem = k.replace("/", "_")
        out_f = fleet_dir / f"{stem}.out"
        err_f = fleet_dir / f"{stem}.err"
        out = out_f.read_text(errors="replace") if out_f.exists() else ""
        err = err_f.read_text(errors="replace") if err_f.exists() else ""
        reported = "RESULT:" in out or "checks passed" in out or "passed," in out
        if code == 0:
            clean += 1
        elif code == 124:
            crashed.append((k, f"exceeded the {args.timeout}s cap without reporting"))
        elif reported:
            completed_with_failures.append(k)
        else:
            last = err.strip().splitlines()[-1] if err.strip() else f"exit {code}, no output"
            crashed.append((k, last[:150]))

    for k, why in crashed:
        print(f"  CRASHED  {k}\n           {why}")
    for k in uncovered:
        print(f"  NOT RUN  {k}")

    print()
    print(f"  exit 0                    : {clean}")
    print(f"  completed, reported failures: {len(completed_with_failures)}")
    print(f"  crashed or timed out      : {len(crashed)}")
    print(f"  not covered by the fleet  : {len(uncovered)}")
    print()

    check(not crashed,
          "no script classified ACTIVE crashes rather than completing",
          f"{len(crashed)} crashed: {[k for k, _ in crashed][:8]}")
    check(not uncovered,
          "every script classified ACTIVE was actually run",
          f"{len(uncovered)} not run: {uncovered[:8]}")

    passed = sum(1 for ok, _, _ in results if ok)
    print("=" * 78)
    print(f"RESULT: {passed}/{len(results)} checks passed")
    print("=" * 78)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
