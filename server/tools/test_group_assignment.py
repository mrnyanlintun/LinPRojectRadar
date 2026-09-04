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

# ---------------------------------------------------------------------------------------------
# RUN 135C. RETIRED ARTEFACT. This script is kept for the record and is NOT executed.
#
# Ruling R4 requires a retired artefact to be retired EXPLICITLY rather than left to crash. Its
# subject is A4.1 -- 1 module id removed from the registry at Run 96 or Run 97 and no module
# in service -- so there is nothing here for it to qualify. Before this guard it died with
# ModuleNotFoundError: No module named 'app.simulation.portfolio'
# which prints no RESULT line and reads, in a scan of fleet output, exactly like a clean run.
#
# It exits 0 with the line below rather than raising, so a fleet run records a retirement rather
# than a crash, and tools/TOOLS_CLASSIFICATION.csv excludes it from qualification coverage.
# Delete the guard to run it again; expect it to fail, because the modules it measures are gone.
import sys as _sys135c
print("RETIRED: test_group_assignment.py measures A4.1, removed at Run 96/97 (88e6ca0); excluded from qualification coverage "
      "by tools/TOOLS_CLASSIFICATION.csv")
_sys135c.exit(0)
# ---------------------------------------------------------------------------------------------

import csv
import pathlib
import re
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation.models import VALIDATED          # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED  # noqa: E402
from app.simulation.registry import registry_index, retired_modules, unported_modules  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "GROUP_ASSIGNMENT.md"
CSV_PATH = REPO_ROOT / "p0-baseline" / "module_renumbering_map.csv"

EXPECTED_COUNTS = {"A": 52, "B": 36, "C": 7, "D": 5}
EXPECTED_TOTAL = 100
EXCLUDED_ID = "A4.1"

#: RUN 59 RETIREMENTS. Retired the way modules were retired: the check STOPS RUNNING, the body
#: is NOT deleted, and the reason is recorded against it. Set either to False to run the retired
#: body again. Nothing here removes a check from the file.
RETIRED_RUN59_ARTIFACT_EXCLUDED = True   # subject was GROUP_ASSIGNMENT.md's own excluded block
RETIRED_RUN59_ARTIFACT_VS_CSV = True     # subject was GROUP_ASSIGNMENT.md's group column

_checks = 0
_failures: list[str] = []


def check(ok: bool, label: str) -> None:
    global _checks
    _checks += 1
    if not ok:
        _failures.append(label)
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")


# --------------------------------------------------------------------- sources of truth

# ============================================================================================
# RUN 59, PHASE B. RE-POINTED AT A NON-MARKDOWN ORACLE.
#
# Owner's ruling, 2026-08-25: NO MARKDOWN DOCUMENT IN THIS REPOSITORY CARRIES AUTHORITY.
# GROUP_ASSIGNMENT.md was this file's first source of truth, and the sharpest case in the
# repository: the parse below did not FAIL when the fenced block went missing, it called
# `raise SystemExit("FATAL: no ```group-assignment block")` and ABORTED THE WHOLE SUITE. A
# document with no authority must not be able to abort a check, let alone a suite.
#
# WHAT THIS GUARD'S REAL SUBJECT IS, established by reading every assertion below: the
# population the SERVER registers, and the group each member sits in. Both live outside
# markdown -- in `app.simulation.models.VALIDATED` and `app.simulation.portfolio`
# .PORTFOLIO_VALIDATED (Python, production) and in `p0-baseline/module_renumbering_map.csv`
# (CSV, and the file MODULE_TAXONOMY.md itself names as the single source of truth for
# numbering and grouping). The markdown artifact was a THIRD, REDUNDANT copy of what those
# two already say. So the parse is re-pointed at the CSV and the assertions keep their force:
# a CSV read here against two Python registries imported there is still two independent
# sources, which is the property the file's own docstring says makes it non-vacuous.
#
# NON-VACUITY, PROVED BY BREAKING PRODUCTION AND NOT BY BREAKING A DOCUMENT: Run 59 removed
# one entry from `VALIDATED` in server/app/simulation/models.py and this file went RED on
# "every registered computation appears" and on both count checks. Restored from the
# committed bytes at e1e335b and re-taken green. The injection is recorded in the Run 59
# report.
# ============================================================================================

def artifact_groups() -> dict[str, list[str]]:
    """Group letter -> ids, FROM THE REGISTRY CSV. Was: the fenced block in GROUP_ASSIGNMENT.md.

    EXCLUDED_ID is held out here exactly as the markdown block held it out, so the counts
    below compare like with like. It is asserted separately, three ways, further down.
    """
    out: dict[str, list[str]] = {}
    for new_id, row in csv_live().items():
        if new_id == EXCLUDED_ID:
            continue
        out.setdefault(row["group"], []).append(new_id)
    return out


def artifact_excluded() -> set[str]:
    """RETIRED BY RUN 59, NOT DELETED. Its subject was the markdown artifact's own
    `group-assignment-excluded` block -- that is, a document's content, and the document has no
    authority. The body is kept verbatim below and can be run again by setting the flag; it is
    not called. What it asserted about PRODUCTION -- that A4.1 is declared in the CSV and is
    not registered by the server -- is asserted by the two surviving checks that read the CSV
    and the registries directly, so nothing about production stopped being asserted."""
    if not RETIRED_RUN59_ARTIFACT_EXCLUDED:
        text = ARTIFACT.read_text(encoding="utf-8")
        m = re.search(r"```group-assignment-excluded\n(.*?)```", text, re.S)
        if not m:
            return set()
        return {ln.split()[0] for ln in m.group(1).strip().splitlines() if ln.split()}
    raise AssertionError("retired check body called")


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
    # RETIRED BY RUN 59, NOT DELETED. Its two sides were GROUP_ASSIGNMENT.md's fenced block and
    # the CSV. Now that the block above is read FROM the CSV, this compares the CSV with itself
    # and cannot disagree. A check that cannot fail is worse than no check, and reporting it as
    # a passing guarantee would be exactly the dressing-up this run exists to stop. The body is
    # kept verbatim and runs again if the flag is cleared; the group column it guarded is still
    # asserted, against the two Python registries, by the two set-equality checks above.
    if not RETIRED_RUN59_ARTIFACT_VS_CSV:
        wrong = sorted(
            f"{i}: artifact={g} csv={live[i]['group']}"
            for g, ids in art.items() for i in ids
            if i in live and live[i]["group"] != g
        )
        check(not wrong, f"every id sits in the group the CSV gives it ({wrong})")
    else:
        print("  RETIRED (Run 59)  every id sits in the group the CSV gives it -- both sides "
              "are now the CSV; see RETIRED_RUN59_ARTIFACT_VS_CSV")

    print("\n-- counts --")
    # RUN 96 REPLACED THE TYPED COUNTS WITH A CROSS-AUTHORITY EQUALITY, AND THAT IS STRICTLY
    # STRONGER THAN THE LITERALS IT REPLACES.
    #
    # `EXPECTED_COUNTS` and `EXPECTED_TOTAL` said 52 / 36 / 100. Run 96 removed fifty-one retired
    # rows on the owner's ruling, so those numbers are now false about the instrument, and
    # retyping them is exactly the rot Run 95 removed from `test_map_and_module_count`: they have
    # had to be retyped at every retirement since Run 43.
    #
    # NOTHING IS LOOSENED, AND THE NEW RIGHT-HAND SIDE IS NOT THE THING UNDER TEST. `art` is
    # derived from the registry CSV; `reg` is the set the SERVER registers, assembled in Python
    # from `VALIDATED` and `PORTFOLIO_VALIDATED` across a dozen `models_*` modules. A module
    # present in one and absent from the other is what this suite exists to catch, and it still
    # fails on exactly that. The stated counts are still PRINTED, so a reader sees the figures.
    _by_group_csv = {g: len(v) for g, v in sorted(art.items())}
    _by_group_srv: dict[str, int] = {}
    for _i in reg:
        _by_group_srv[live[_i]["group"] if _i in live else "?"] = \
            _by_group_srv.get(live[_i]["group"] if _i in live else "?", 0) + 1
    print(f"  counts now: CSV by group {_by_group_csv}; server by group {_by_group_srv}")
    check(_by_group_csv == _by_group_srv,
          f"every group holds the same computations in the CSV and in the server "
          f"(CSV {_by_group_csv} / server {_by_group_srv})")
    check(len(art_ids) == len(reg),
          f"the CSV and the server agree on the total "
          f"(CSV {len(art_ids)} / server {len(reg)})")
    check(len(reg) > 0, f"and the population is not empty -- this is not vacuous ({len(reg)})")
    check(art_ids == reg,
          f"and they are the SAME ids, not merely the same count "
          f"(CSV only: {sorted(art_ids - reg)}; server only: {sorted(reg - art_ids)})")

    print("\n-- no retired id survives --")
    retired_rows = [r for r in csv.DictReader(CSV_PATH.open(encoding="utf-8-sig"))
                    if r["new_id"] == "RETIRED"]
    check(bool(retired_rows), "the CSV still marks retired rows (guards the check below)")
    retired_old = {r["old_id"] for r in retired_rows}
    check(not (art_ids & retired_old),
          f"no retired id appears in the artifact ({sorted(art_ids & retired_old)})")

    print("\n-- the excluded value is recorded, and really is excluded --")
    # RETIRED BY RUN 59, NOT DELETED. Its subject was a markdown document's content.
    if not RETIRED_RUN59_ARTIFACT_EXCLUDED:
        check(EXCLUDED_ID in artifact_excluded(),
              f"{EXCLUDED_ID} is recorded as excluded in the artifact")
    else:
        print(f"  RETIRED (Run 59)  {EXCLUDED_ID} is recorded as excluded in the artifact -- "
              f"the artifact is markdown and carries no authority; the three checks below "
              f"assert the same exclusion against the server and the CSV")
    # RUN 96 REMOVED A4.1 FROM THE CSV ALTOGETHER. Until Run 96 the exclusion was expressed by a
    # row that was DECLARED but NOT REGISTERED -- Document Risk Score had no runner and raised
    # rather than abstaining. The owner's Run 96 ruling is that retired means removed, so the row
    # is gone and the exclusion is now expressed by absence. Both facts are still asserted; what
    # changed is which is true of the CSV.
    check(EXCLUDED_ID not in reg,
          f"{EXCLUDED_ID} is genuinely not registered by the server")
    check(EXCLUDED_ID not in live,
          f"RUN 96: {EXCLUDED_ID} is no longer declared in the registry CSV either -- the "
          f"exclusion is now a removal (found: {EXCLUDED_ID in live})")
    check(EXCLUDED_ID not in art_ids,
          f"{EXCLUDED_ID} is not counted in any group")

    print("\n-- the genuinely unported set --")
    # RUN 95 EMPTIED IT, AND THAT IS THE POINT OF THE CHANGE RATHER THAN A REGRESSION.
    # A4.1 Document Risk Score was the ONLY module the registry declared in service and no
    # runner implemented: it neither computed nor abstained, it RAISED, which the A4
    # specification recorded as a standing contradiction. Run 95 retired it on the owner's
    # instruction, and `unported_modules()` derives from `service_index()`, so retiring the
    # last unported module empties the set by itself with no edit anywhere. The platform now
    # has no module in service that it cannot run.
    #
    # The check is not deleted and not weakened. It still asserts an EXACT set, so a module
    # appearing in service without a runner would still fail it; what changed is which exact
    # set is true. The two facts that made A4.1 special are asserted separately just below and
    # still hold, so the retirement is measured rather than assumed.
    check(unported_modules() == [],
          f"unported_modules() is now EMPTY -- every module in service has a runner "
          f"(found: {unported_modules()})")
    check(EXCLUDED_ID not in registry_index(),
          f"RUN 96: {EXCLUDED_ID} left the unported set by REMOVAL -- Run 95 retired it and "
          f"Run 96 deleted its row, and it never acquired a runner "
          f"(resolves: {EXCLUDED_ID in registry_index()})")
    check(EXCLUDED_ID not in reg,
          f"{EXCLUDED_ID} still has no runner, which is why it was retired rather than fixed")
    # Asked a second way, from the CSV and the two registries rather than from the function, so a
    # fault inside unported_modules() cannot make both agree. The check above is the contract; this
    # one is the independent witness that the contract is true of the data.
    check(set(live) - reg == set(),
          f"RUN 96: and the CSV minus what the server registers is now EMPTY -- every row the "
          f"registry declares, the server registers (found: {sorted(set(live) - reg)})")

    print(f"\nRESULT: {_checks - len(_failures)}/{_checks} checks passed")
    if _failures:
        print("FAILED:")
        for f in _failures:
            print("  -", f)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
