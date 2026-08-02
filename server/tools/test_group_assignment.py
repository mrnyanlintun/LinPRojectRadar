#!/usr/bin/env python3
"""
The group assignment artifact must keep matching the code.

Run (from server/):

    python tools/test_group_assignment.py

GROUP_ASSIGNMENT.md is the authority every user-facing surface is written against. An artifact
that silently goes stale is worse than no artifact, because the next sweep rewrites real prose
against it and nothing complains.

THE unported_modules() WORKAROUND IS GONE.

This file used to compute the unported set itself and assert its disagreement with
registry.unported_modules(), because that function was `set(registry_index()) - set(VALIDATED)`
and counted the five Group D modules as unported although portfolio.py implements them: six where
exactly one is. The function now subtracts PORTFOLIO_VALIDATED and is asked directly.

It is still asked a second way, from the CSV minus the two registries, because a check that only
consults the function cannot tell a correct function from a broken one that agrees with itself.
The two are independent: one goes through registry.py, the other reads the CSV here.

THIS FILE MUST BE ABLE TO FAIL. Every assertion below was proven by breaking it: an id was moved
between groups in the artifact, an id was deleted from it, and a fake unported module was added to
the CSV index. Each produced a red check. See the report for which assertion caught which fault.
"""
from __future__ import annotations

import csv
import pathlib
import re
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation.models import VALIDATED          # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED  # noqa: E402
from app.simulation.registry import unported_modules  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "GROUP_ASSIGNMENT.md"
CSV_PATH = REPO_ROOT / "p0-baseline" / "module_renumbering_map.csv"

EXPECTED_COUNTS = {"A": 52, "B": 36, "C": 7, "D": 5}
EXPECTED_TOTAL = 100
EXCLUDED_ID = "A4.1"

_checks = 0
_failures: list[str] = []


def check(ok: bool, label: str) -> None:
    global _checks
    _checks += 1
    if not ok:
        _failures.append(label)
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")


# --------------------------------------------------------------------- sources of truth

def artifact_groups() -> dict[str, list[str]]:
    """Parse the fenced group-assignment block. One line per group: letter then ids."""
    text = ARTIFACT.read_text(encoding="utf-8")
    m = re.search(r"```group-assignment\n(.*?)```", text, re.S)
    if not m:
        raise SystemExit("FATAL: no ```group-assignment block in GROUP_ASSIGNMENT.md")
    out: dict[str, list[str]] = {}
    for line in m.group(1).strip().splitlines():
        parts = line.split()
        if not parts:
            continue
        out[parts[0]] = parts[1:]
    return out


def artifact_excluded() -> set[str]:
    text = ARTIFACT.read_text(encoding="utf-8")
    m = re.search(r"```group-assignment-excluded\n(.*?)```", text, re.S)
    if not m:
        return set()
    return {ln.split()[0] for ln in m.group(1).strip().splitlines() if ln.split()}


def csv_live() -> dict[str, dict]:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    return {r["new_id"]: r for r in rows if r["new_id"] != "RETIRED"}


def registered() -> set[str]:
    return set(VALIDATED) | set(PORTFOLIO_VALIDATED)


# --------------------------------------------------------------------- checks

def main() -> int:
    live = csv_live()
    reg = registered()
    art = artifact_groups()
    art_ids = {i for ids in art.values() for i in ids}

    print("\n-- the artifact matches what the server registers --")
    # Set equality both ways, reported separately so a failure names the direction.
    missing = sorted(reg - art_ids)
    extra = sorted(art_ids - reg)
    check(not missing, f"every registered computation appears in the artifact (missing: {missing})")
    check(not extra, f"the artifact lists nothing the server does not register (extra: {extra})")

    print("\n-- each computation appears exactly once --")
    flat = [i for ids in art.values() for i in ids]
    dupes = sorted({i for i in flat if flat.count(i) > 1})
    check(not dupes, f"no id appears twice in the artifact (duplicates: {dupes})")

    print("\n-- group membership matches the registry CSV --")
    wrong = sorted(
        f"{i}: artifact={g} csv={live[i]['group']}"
        for g, ids in art.items() for i in ids
        if i in live and live[i]["group"] != g
    )
    check(not wrong, f"every id sits in the group the CSV gives it ({wrong})")

    print("\n-- counts --")
    for g, want in EXPECTED_COUNTS.items():
        check(len(art.get(g, [])) == want,
              f"group {g} has {want} computations (artifact has {len(art.get(g, []))})")
    check(len(art_ids) == EXPECTED_TOTAL,
          f"total is {EXPECTED_TOTAL} (artifact has {len(art_ids)})")
    check(len(reg) == EXPECTED_TOTAL,
          f"the server registers {EXPECTED_TOTAL} (registers {len(reg)})")

    print("\n-- no retired id survives --")
    retired_rows = [r for r in csv.DictReader(CSV_PATH.open(encoding="utf-8-sig"))
                    if r["new_id"] == "RETIRED"]
    check(bool(retired_rows), "the CSV still marks retired rows (guards the check below)")
    retired_old = {r["old_id"] for r in retired_rows}
    check(not (art_ids & retired_old),
          f"no retired id appears in the artifact ({sorted(art_ids & retired_old)})")

    print("\n-- the excluded value is recorded, and really is excluded --")
    check(EXCLUDED_ID in artifact_excluded(),
          f"{EXCLUDED_ID} is recorded as excluded in the artifact")
    check(EXCLUDED_ID not in reg,
          f"{EXCLUDED_ID} is genuinely not registered by the server")
    check(EXCLUDED_ID in live,
          f"{EXCLUDED_ID} is still declared in the registry CSV (so the exclusion is real, "
          f"not a missing row)")
    check(EXCLUDED_ID not in art_ids,
          f"{EXCLUDED_ID} is not counted in any group")

    print("\n-- the genuinely unported set --")
    check(unported_modules() == [EXCLUDED_ID],
          f"unported_modules() reports exactly {EXCLUDED_ID} "
          f"(found: {unported_modules()})")
    # Asked a second way, from the CSV and the two registries rather than from the function, so a
    # fault inside unported_modules() cannot make both agree. The check above is the contract; this
    # one is the independent witness that the contract is true of the data.
    check(set(live) - reg == {EXCLUDED_ID},
          f"and the CSV minus what the server registers agrees "
          f"(found: {sorted(set(live) - reg)})")

    print(f"\nRESULT: {_checks - len(_failures)}/{_checks} checks passed")
    if _failures:
        print("FAILED:")
        for f in _failures:
            print("  -", f)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
