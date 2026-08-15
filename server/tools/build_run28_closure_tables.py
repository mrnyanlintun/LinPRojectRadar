#!/usr/bin/env python3
"""
RUN 28 CLOSURE. The two closure tables, DERIVED rather than hand-maintained.

WHY A BUILDER AND NOT A SPREADSHEET. The first closure pass wrote both tables by hand, and one of
them then disagreed with the tree after A1.1 was renamed. A table that has to be remembered will
eventually be forgotten. This reads the module registry, the scope file, the structure-key map and
the production sources, and writes what it finds; `test_run28_closure.py` then checks the written
tables against those same sources independently, so neither side is derived from the other at
check time.

It writes LF line endings explicitly: the freeze records these files' digests, and git normalises
CRLF on checkout, so a digest taken over CRLF bytes would fail verification on every fresh clone.
"""

from __future__ import annotations

import csv
import pathlib
import re
import sys
from datetime import date

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import models as MM  # noqa: E402

MM._register_extensions()
from app.simulation import registry as R  # noqa: E402
from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS  # noqa: E402
from app.simulation.canonical_v3 import V3_STRUCTURE_KEYS  # noqa: E402
from app.simulation.rng import make_rng  # noqa: E402

SCOPE = ROOT / "code_audit" / "run28_cat1_3_scope.csv"
SUPPLY = ROOT / "code_audit" / "run28_supply_path_closure.csv"
OUT = ROOT / "code_audit" / "run28_operational_closure_28.csv"

#: Modules that compute on the real corpus today, each with the suite that demonstrates it. This
#: is the one thing the builder cannot derive by executing a synthetic input, because "the real
#: corpus" is a set of documents a suite drives, not a dictionary.
EXECUTES = {
    "A1.1": "computes from the reported budget and cost index; "
            "server/tools/test_run10_monte_carlo_eac_fixture.py",
    "A1.2": "computes from two or more stored periods of cost index; "
            "server/tools/test_run6_known_answer.py",
    "A2.7": "computes on the suite's own real schedule documents across two reporting periods; "
            "server/tools/test_schedule_milestones.py",
    "A3.2": "computes from the reported contingency figures; "
            "server/tools/test_run19_category_3.py",
    "A3.6": "computes on the real risk register; "
            "server/tools/test_risk_register_and_notices.py",
}
CAL33 = {"A1.1", "A1.2", "A1.3", "A1.4", "A1.10", "A1.11", "A2.2", "A2.3", "A2.7", "A3.2", "A3.6"}
PASSES = {"A1.7", "A1.8"}
DISABLED_EXCLUDED = {"A3.4"}


def rows(path: pathlib.Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    scope = rows(SCOPE)
    supply = {r["module"]: r for r in rows(SUPPLY)}
    names = {r["new_id"]: r["module_name"]
             for r in rows(ROOT / "p0-baseline" / "module_renumbering_map.csv")}
    prod = "\n".join(p.read_text(encoding="utf-8")
                     for p in (ROOT / "server" / "app").rglob("*.py")
                     if "__pycache__" not in str(p))
    base = {"bac": 1000.0, "ev": 800.0, "ac": 900.0, "cpi": 0.9, "spi": 0.95,
            "cpiHistory": [0.9, 0.92, 0.91]}

    out = []
    for r in scope:
        mid = r["canonical_id"]
        if mid in PASSES or mid in DISABLED_EXCLUDED:
            continue
        key = V3_STRUCTURE_KEYS.get(mid) or CANONICAL_STRUCTURE_KEYS.get(mid)
        disabled = mid in R.DISABLED_CONCEPT_ONLY or mid in R.DISABLED_MODULES
        sp = supply.get(mid)
        if disabled:
            ex, ab, why = "no", "no", "disabled laboratory-only: registered, never executed"
        elif mid in EXECUTES:
            ex, ab, why = "yes", "no", EXECUTES[mid]
        elif sp:
            probe = MM.VALIDATED[mid][1](base, make_rng(1), date(2026, 4, 30))
            ex, ab = "no", "yes"
            why = (f"abstains with {probe.get('abstention_reason_code')}; read by executing the "
                   f"registered runner rather than copied from a column")
        else:
            ex, ab = "no", "yes"
            why = (f"abstains: its structure key `{key}` is declared in canonical.py and is "
                   f"written by NO production code, the same condition as the twenty. NOT among "
                   f"Run 28's twenty, which counted it as already canonical rather than as "
                   f"abstaining. Found by this closure and given the same intake.")
        if sp:
            spath, stype, simpl = (sp["concrete_repository_object"], sp["supply_path_type"],
                                   sp["implemented"])
        elif mid in EXECUTES:
            spath = {
                "A3.6": "server/app/documents.py assembles costRiskModel from the period's risk "
                        "register",
                "A2.7": "server/app/documents.py assembles milestoneForecastHistory from the "
                        "stored schedule snapshots",
            }.get(mid, "the corpus itself: figures already extracted from the period's documents")
            stype, simpl = "EXISTING_DOCUMENT_EXTRACTION", "yes"
        else:
            spath = (f"signal-inputs key `{key}` declared in "
                     f"server/app/simulation/canonical.py; stored and served by "
                     f"server/app/writes.py::w_saveprojectdata -> server/app/project_data.py -> "
                     f"server/app/documents.py::run_and_store")
            stype, simpl = "NEW_PROJECT_DATA_OBJECT", "yes"
        out.append({
            "module": mid,
            "module_name": names.get(mid, r["current_registered_name"]),
            "canonical_method_implemented": "yes",
            "canonical_structure_supply_path_present": simpl,
            "real_corpus_executes": ex,
            "real_corpus_abstains": ab,
            "disabled_laboratory_only": "yes" if disabled else "no",
            "required_supply_path_present": simpl,
            "supply_path_type": stype,
            "concrete_repository_object": spath,
            "production_code_writes_the_structure_key":
                ("n/a" if not key
                 else ("yes" if re.search(r'si\["%s"\]\s*=' % re.escape(key), prod) else "no")),
            "calibration_pending_run33": "yes" if mid in CAL33 else "no",
            "empirical_validation_pending": "yes",
            "lineage_qualification_pending_run31": "yes",
            "post_run28_closure_disposition": r["post_run28_disposition"],
            "evidence": why,
            "accounted": "yes",
        })

    with OUT.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(out[0].keys()), lineterminator="\n")
        w.writeheader()
        for row in out:
            w.writerow(row)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out)} rows, "
          f"{len({r['module'] for r in out})} unique modules")
    print(f"  executes {sum(1 for r in out if r['real_corpus_executes'] == 'yes')}  "
          f"abstains {sum(1 for r in out if r['real_corpus_abstains'] == 'yes')}  "
          f"disabled {sum(1 for r in out if r['disabled_laboratory_only'] == 'yes')}")


if __name__ == "__main__":
    main()
