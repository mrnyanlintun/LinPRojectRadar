#!/usr/bin/env python3
"""Run 135 ruling R4: classify every script in server/tools and server/tests into exactly one kind.

  active     - active qualification test: asserts on behaviour the platform has TODAY
  reader     - historical evidence reader: reads a sealed artefact / measurement and reports it
  migration  - one-time run-scoped tool: builds an artefact, seeds, applies, exports
  retired    - retired artefact: its SUBJECT is a feature that no longer exists

DECISION ORDER (fixed; the applied rule is written into `reason` so the counts are reproducible):

  3. RETIRED  - the script references simulation module ids, EVERY id it references was removed
                (Run 96's 51 or Run 97's 20, per tools/run96_removed.py), AND it does not complete
                when run. Both halves are required. Referencing a removed feature is not on its
                own retirement -- test_simulation.py names PortfolioModuleError but 20 of its 23
                checks are about live behaviour, so it is an ACTIVE suite with a broken reference
                (H9). And a script that still runs to completion is still measuring something,
                whatever ids it happens to mention, so it is not retired either.
  2. MIGRATION - name marks a one-time run-scoped builder/seeder/exporter.
  3. READER    - name marks a measurement/reconciliation/census over sealed artefacts.
  4. READER    - does not import app.* at all: it can only be reporting on files or text.
  5. MIGRATION - imports app.* but makes no assertion: a procedural tool.
  6. ACTIVE    - imports app.* and asserts.

Only kind=active counts toward current qualification coverage.
"""
from __future__ import annotations

import csv
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRATCH = pathlib.Path(
    "/tmp/claude-0/-home-user-LinPRojectRadar/56ab0a7f-4e21-5061-8b33-396724907fe8/scratchpad/run135/C"
)
if len(sys.argv) > 1:
    ROOT = pathlib.Path(sys.argv[1])

sys.path.insert(0, str(ROOT))

MIGRATION_PREFIXES = ("build_", "apply_", "seed_", "import_", "bootstrap_", "export_",
                      "campaign_", "dev_", "participant_", "production_", "synthetic_",
                      "taxonomy_", "leak_")
MIGRATION_SUBSTR = ("_freeze", "_artifacts", "_fixtures", "_fixture", "_calibration",
                    "_manifest", "_register", "_inventory", "_curation", "_propagate")
READER_PREFIXES = ("measure_", "probe_", "real_")
READER_SUBSTR = ("_reconciliation", "_census", "_hashes", "_consolidate", "_report",
                 "_historical", "_comparison", "_capture")

MODULE_ID = re.compile(r"\b([A-D]\d{1,2}\.\d{1,2})\b")


def removed_ids() -> set[str]:
    import importlib.util as _il
    _s = _il.spec_from_file_location("run96_removed", ROOT / "tools" / "run96_removed.py")
    run96_removed = _il.module_from_spec(_s); _s.loader.exec_module(run96_removed)
    return set(run96_removed.REMOVED)


def live_ids() -> set[str]:
    from app.simulation import available_modules  # type: ignore
    return set(available_modules())


def run_number(name: str) -> str:
    m = re.search(r"run(\d+)", name)
    return m.group(1) if m else ""


def main() -> int:
    removed = removed_ids()
    live = live_ids()

    exits: dict[str, int] = {}
    tsv = SCRATCH / "fleet2_exit.tsv"
    if tsv.exists():
        for line in tsv.read_text().splitlines():
            if "\t" in line:
                p, c = line.rsplit("\t", 1)
                exits[p] = int(c)

    rows = []
    for p in sorted(ROOT.glob("tools/*.py")) + sorted(ROOT.glob("tests/*.py")):
        key = str(p.relative_to(ROOT))
        rel = f"server/{key}"
        src = p.read_text(errors="replace")
        name = p.name
        ids = set(MODULE_ID.findall(src))
        ids_removed = ids & removed
        ids_live = ids & live
        imports_app = bool(re.search(r"^\s*(from|import)\s+app[\s.]", src, re.M))
        asserts = bool(re.search(r"\bcheck\(|\bassert\b|\brequire\(", src))
        hardcoded = "/home/user/LinPRojectRadar/server" in src
        code = exits.get(key)

        if name.startswith("run135c_") or name == "test_run135c_active_suite_completes.py":
            kind, reason = "reader", ("rule0 Run 135C classification harness: it reports on the "
                                      "fleet rather than qualifying the platform, so it is "
                                      "excluded from coverage like any other reader")
        elif name.startswith(MIGRATION_PREFIXES) or any(s in name for s in MIGRATION_SUBSTR):
            kind, reason = "migration", "rule1 one-time run-scoped builder/seeder/exporter by name"
        elif name.startswith(READER_PREFIXES) or any(s in name for s in READER_SUBSTR):
            kind, reason = "reader", "rule2 measurement/reconciliation/census over sealed artefacts"
        elif ids_removed and not ids_live and code not in (0, None):
            kind = "retired"
            reason = ("rule3 subject is removed modules only: references " +
                      ",".join(sorted(ids_removed)[:6]) + " and no module in service, "
                      f"and it does not complete (exit {code})")
        elif not imports_app:
            kind, reason = "reader", "rule4 does not import app.*; reports on files or text only"
        elif not asserts:
            kind, reason = "migration", "rule5 imports app.* but asserts nothing; procedural tool"
        else:
            kind, reason = "active", "rule6 imports app.* and asserts on live behaviour"

        if hardcoded:
            reason += "; hardcodes /home/user/LinPRojectRadar/server on sys.path"

        err_path = SCRATCH / "fleet2" / (key.replace("/", "_") + ".err")
        err = err_path.read_text(errors="replace") if err_path.exists() else ""
        rows.append({
            "path": rel, "kind": kind, "reason": reason, "last_run_referenced": run_number(name),
            "exit_code": "" if code is None else code,
            "first_error": err.strip().splitlines()[-1][:180] if err.strip() else "",
        })

    out = ROOT / "tools" / "TOOLS_CLASSIFICATION.csv"
    with out.open("w", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "kind", "reason", "last_run_referenced",
                                           "exit_code", "first_error"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    c = Counter(r["kind"] for r in rows)
    print("total", len(rows))
    for k in ("active", "reader", "migration", "retired"):
        print(k, c[k])
    return 0


if __name__ == "__main__":
    sys.exit(main())
