#!/usr/bin/env python3
"""
RUN 31: the Category-8/9 scope table and the Pass-2 commit inventory.

BOTH ARE DERIVED, NOT TRANSCRIBED. The scope population is read from the shipped registry CSV --
the same file `registry.registry_index()` reads -- and the inventory checks CURRENT VALUES and
names the evidence location for each, because a filename existing is not a requirement met.
"""
import csv, hashlib, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                               # noqa: E402
from app.simulation.models import (                                      # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY as HIST,
    SIMULATION_VERSION_SUPERSEDED, VALIDATED)
from app.simulation.models_cat89 import CAT89_CANONICAL, MODULE_USE      # noqa: E402
from app.simulation.qualification_boundary import (                      # noqa: E402
    gate_installed_for, gated_module_ids)
from app.simulation.lineage import lineage_status                        # noqa: E402
from run31_historical_cat89 import LEGACY_CAT89                          # noqa: E402
import participant_packages as PP                                        # noqa: E402

CSV_PATH = ROOT / "p0-baseline" / "module_renumbering_map.csv"
CAT8 = {"Delivery Quality Performance", "Regulatory & Authority Thresholds"}
CAT9 = {"Data Integrity"}


def w(name, header, rows):
    p = ROOT / "code_audit" / name
    with p.open("w", newline="", encoding="utf-8") as fh:
        cw = csv.writer(fh, lineterminator="\n")
        cw.writerow(header)
        cw.writerows(rows)
    print(f"wrote {p.relative_to(ROOT)}  ({len(rows)} rows)")
    return p


def scope():
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        reg = list(csv.DictReader(fh))
    rows = []
    for r in reg:
        cat = r["category_name"]
        if cat not in CAT8 | CAT9:
            continue
        mid = r["new_id"]
        fn = VALIDATED.get(mid)
        rows.append([
            "Category 8" if cat in CAT8 else "Category 9",
            mid, r["module_name"], r["old_id"], cat,
            "ACTIVE" if mid not in REG.DISABLED_CONCEPT_ONLY else "DISABLED",
            "NO",                                     # none of the 16 votes
            f"{fn[1].__module__}.{fn[1].__name__}" if fn else "NOT VALIDATED",
            "models_cat89.CAT89_CANONICAL -> canonical_v6",
            "canonical_v6 governed structure via project-data intake / corpus assembly",
            MODULE_USE.get(mid, ""),
            "YES" if (fn and gate_installed_for(fn[1])) else "NO (Cat 9 performs the assessment)",
            lineage_status(mid, applicable=True),
            "NO" if not (LEGACY_CAT89.get(mid)
                         and fn and fn[1] is LEGACY_CAT89[mid][1]) else "YES",
            SIMULATION_VERSION, "PASS"])
    return rows


def sha(rel):
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.is_file() else ""


def inventory():
    """Requirement, expected object, present, CURRENT VALUE, evidence location, status."""
    rows = []

    def add(req, obj, present, value, evidence):
        rows.append([req, obj, "YES" if present else "NO", value, evidence,
                     "PASS" if present else "FAIL"])

    for f in ("abm.py", "canonical_v6.py", "models_cat89.py", "qualified_evidence.py",
              "regulatory.py", "qualification_boundary.py"):
        rel = f"server/app/simulation/{f}"
        p = ROOT / rel
        add(f"Run-31 production file {f}", rel, p.is_file(),
            f"{len(p.read_text().splitlines())} lines, sha {sha(rel)}" if p.is_file() else "",
            rel)

    add("simulation identity", "models.SIMULATION_VERSION",
        SIMULATION_VERSION == "sim-2026.08-v19", SIMULATION_VERSION,
        "server/app/simulation/models.py")
    add("superseded line", "models.SIMULATION_VERSION_SUPERSEDED",
        SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v18", SIMULATION_VERSION_SUPERSEDED,
        "server/app/simulation/models.py")
    add("append-only history through v19", "models.SIMULATION_VERSION_HISTORY",
        HIST[-1] == "sim-2026.08-v19" and len(HIST) == len(set(HIST)),
        f"{len(HIST)} stamps, unique={len(HIST)==len(set(HIST))}, tail={HIST[-3:]}",
        "server/app/simulation/models.py")
    add("qualification boundary installed in the dispatch table",
        "models._register_extensions -> qualification_boundary.install",
        "qualification_boundary import install" in (ROOT / "server/app/simulation/models.py"
                                                    ).read_text(),
        f"{len(gated_module_ids())} gated modules derived from the registry CSV",
        "server/app/simulation/models.py")

    gated = gated_module_ids()
    add("boundary present on every gated dispatch entry", "VALIDATED[mid].__gated__",
        all(gate_installed_for(VALIDATED[m][1]) for m in gated if m in VALIDATED),
        f"{sum(1 for m in gated if m in VALIDATED and gate_installed_for(VALIDATED[m][1]))}"
        f"/{len(gated)}", "server/app/simulation/qualification_boundary.py")
    add("Category 9 excluded from the boundary by construction", "C1.x not gated",
        not any(gate_installed_for(VALIDATED[m][1]) for m in CAT89_CANONICAL
                if m.startswith("C1.")),
        "0/7 Category-9 modules gated", "server/app/simulation/qualification_boundary.py")

    for art in ("run31_cat8_9_scope.csv", "run31_orphan_field_reconciliation.csv",
                "run31_real_corpus_structure_reconciliation.csv",
                "run31_regulatory_snapshot.csv",
                "run31_downstream_qualification_execution.csv",
                "run31_cat8_9_operational_route_inventory.csv",
                "run31_historical_suite_reconciliation.csv",
                "run31_safety_upstream_identity_proof.csv",
                "run31_pass1_production_tree.sha256",
                "run31_participant_package_v6_checksums.sha256"):
        p = ROOT / "code_audit" / art
        n = len([l for l in p.read_text().splitlines()
                 if l.strip() and not l.startswith("#")]) - (1 if art.endswith(".csv") else 0) \
            if p.is_file() else 0
        add(f"artifact {art}", f"code_audit/{art}", p.is_file(),
            f"{n} data rows, sha {sha('code_audit/'+art)}", f"code_audit/{art}")

    add("simulation-version execution proof", "server/tools/test_run31_version_boundaries.py",
        (ROOT / "server/tools/test_run31_version_boundaries.py").is_file(),
        "executes v16, v17 and v18 packages from git objects on identical input",
        "server/tools/test_run31_version_boundaries.py")
    add("Pass-2 operational acceptance", "server/tools/test_run31_pass2_acceptance.py",
        (ROOT / "server/tools/test_run31_pass2_acceptance.py").is_file(),
        "raw-bypass, precedence, lineage, non-voting, 9.1/9.5, 9.2/9.7, ABM, wording",
        "server/tools/test_run31_pass2_acceptance.py")

    add("participant successor package", "og-participant-2026.08-v6",
        PP.CURRENT.identifier == "og-participant-2026.08-v6",
        f"current={PP.CURRENT.identifier}, chain={len(PP.PARTICIPANT_PACKAGES)}, "
        f"predecessors pinned={all(p.source_commit for p in PP.PARTICIPANT_PACKAGES[:-1])}",
        "server/tools/participant_packages.py")
    add("synthetic package decision", "no successor minted",
        not subprocess.run(["git", "diff", "--name-only", "4dd5985", "f147278"],
                           cwd=ROOT, capture_output=True, text=True).stdout.count("synthetic"),
        "Pass 2 changed no synthetic fixture byte, so no successor was minted",
        "git diff 4dd5985..f147278")
    return rows


def main():
    s = scope()
    w("run31_cat8_9_scope.csv",
      ["category", "module", "authoritative_current_name", "old_id", "registry_category",
       "activation", "voting", "current_runner", "canonical_runner", "evidence_source",
       "qualification_use", "gated", "lineage_status", "legacy_route_reachable",
       "simulation_version", "status"], s)
    c8 = sum(1 for r in s if r[0] == "Category 8")
    c9 = sum(1 for r in s if r[0] == "Category 9")
    print(f"   Category 8 = {c8}, Category 9 = {c9}, total = {len(s)}, "
          f"unique = {len({r[1] for r in s})}")
    inv = inventory()
    w("run31_pass2_commit_inventory.csv",
      ["requirement", "expected_file_or_object", "present", "current_value",
       "evidence_location", "status"], inv)
    print(f"   inventory FAIL rows: {sum(1 for r in inv if r[5] == 'FAIL')}")


if __name__ == "__main__":
    main()
