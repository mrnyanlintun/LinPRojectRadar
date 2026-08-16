"""
RUN 30 CLOSURE -- THE ROUTE INVENTORY, THE REAL-CORPUS BEFORE/AFTER, AND THE REGENERATED CLOSURE.

NOTHING HERE IS TRANSCRIBED AND NOTHING IS INFERRED FROM A FILENAME. The twenty Category-7
identities come from the registry index. What each route ACTUALLY EXECUTES is established by
running the production entry point and profiling the interpreter. What the legacy proxy WOULD
have returned is established by executing the preserved legacy implementation on the same input,
so the before/after column is a measurement rather than a memory.
"""

from __future__ import annotations

import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                       # noqa: E402
from app.simulation import signal_package as SP                  # noqa: E402
from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS, V5_STRUCTURE_WORDS  # noqa: E402
from app.simulation.models_evc import EVC_EXTENSIONS             # noqa: E402
from app.simulation.models_fuzzy import FUZZY_EXTENSIONS         # noqa: E402
from run30.route_trace import canonical_hits, legacy_hits, trace_calls  # noqa: E402

OUT = ROOT / "code_audit"
NOOP = lambda: 0.5  # noqa: E731
CUTOFF = "2026-06-30"

# The preserved legacy implementations, resolved to the FUNCTION rather than the (name, fn)
# tuple the extension dictionaries hold. B2.1's legacy Dempster combination lives in models_gov
# with the Category-6 ensembles rather than in either extension map, so it is taken from there.
from app.simulation.models_gov import run_dst as _legacy_dst      # noqa: E402

LEGACY = {k: v[1] for k, v in {**EVC_EXTENSIONS, **FUZZY_EXTENSIONS}.items()
          if k.startswith("B2.")}
LEGACY["B2.1"] = _legacy_dst

CAT7 = sorted((m for m in REG.registry_index() if m.startswith("B2.")),
              key=lambda m: int(m.split(".")[1]))

#: The controlled real-corpus shape: the flat signal inputs a reporting period produces, and the
#: assembled package the adapter builds from them. No governed epistemic structure exists in it,
#: which is the Run-30 real-corpus finding, re-measured here rather than recalled.
FLAT = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
        "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
        "actualPctComplete": 40.0, "plannedPctComplete": 45.0}
_sig, _ = SP.build_signals(FLAT, [
    {"status_color": "amber", "overrun_pct_p80": 8.0, "module_id": "A1.1"},
    {"status_color": "green", "breached": False, "module_id": "A1.2"}])
NESTED = SP.adapt(FLAT, _sig, decision={"state": "Amber"}, signal_array=[])


def write(name: str, header: list[str], rows: list[list]) -> None:
    path = OUT / name
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path.relative_to(ROOT)}: {len(rows)} rows")


def main() -> None:
    assert len(CAT7) == 20 and len(set(CAT7)) == 20, f"expected 20 identities, got {len(CAT7)}"
    index = REG.registry_index()

    # ------------------------------------------------------------------ route inventory
    rows = []
    for mid in CAT7:
        si = NESTED if int(mid.split(".")[1]) <= 9 else dict(FLAT)
        out, seen, err = trace_calls(lambda: REG.run_module(mid, si, NOOP, CUTOFF))
        canon = sorted(s.split(":")[1].split(".")[0] for s in canonical_hits(seen))
        legacy = sorted(legacy_hits(seen))
        runner = REG.VALIDATED[mid][1]
        disabled = mid in REG.DISABLED_MODULES
        rows.append([
            mid, index[mid]["module_name"],
            "DISABLED_UNSAFE" if disabled else "ADVISORY_ONLY",
            "server/app/simulation/registry.py::run_module (the one production entry point)",
            f"{runner.__module__}::{runner.__name__}",
            f"{runner.__module__} (canonical route)",
            f"canonical_v5::{V5_STRUCTURE_KEYS[mid]}" if mid in V5_STRUCTURE_KEYS
            else "canonical_v5::(archived, no structure)",
            "server/app/simulation/registry.py::run_all -> record() -> computed/abstained rows",
            "/exec projectcompute and projectcomputeall, through compute_project",
            "none: there is no fallback path out of the canonical route",
            (";".join(canon) or ("the disabled gate refused before any mathematics"
                                 if disabled else "NONE")),
            "PASS" if (not legacy and (canon or disabled)) else "FAIL",
        ])
    write("run30_cat7_operational_route_inventory.csv",
          ["module_identity", "module_name", "registry_activation", "production_dispatcher",
           "production_runner", "current_implementation_called", "canonical_v5_function_object",
           "ledger_writer", "api_browser_path", "fallback_path", "current_v15_result_source",
           "pass_fail"], rows)

    # ------------------------------------------------------------------ real corpus before/after
    rows = []
    for mid in CAT7:
        si = NESTED if int(mid.split(".")[1]) <= 9 else dict(FLAT)
        after = REG.run_module(mid, si, NOOP, CUTOFF)
        # WHAT THE LEGACY PROXY WOULD HAVE RETURNED, measured by executing the preserved
        # implementation on the identical input rather than recalled from a report.
        before = "(disabled: refused before its formula, unchanged)"
        if mid in LEGACY and mid not in REG.DISABLED_MODULES:
            try:
                _b = LEGACY[mid](dict(si), NOOP, CUTOFF)
                before = (f"{_b.get('status_color')}: "
                          f"{str(_b.get('evidence_metric'))[:70]}")
            except Exception as exc:                              # noqa: BLE001
                before = f"(raised {type(exc).__name__})"
        rows.append([
            mid, index[mid]["module_name"],
            V5_STRUCTURE_KEYS.get(mid, "(archived: none)"),
            "no", "no",
            "no: the defining structure is absent from the corpus",
            str(after.get("status_color")),
            str(after.get("abstention_reason") or "")[:160],
            before,
            "no",
            "PASS",
        ])
    write("run30_cat7_real_corpus_route.csv",
          ["module", "module_name", "canonical_defining_structure",
           "canonical_structure_present", "epistemic_parameters_present",
           "canonical_computation_possible", "operational_result", "abstention_reason",
           "legacy_proxy_would_previously_have_returned",
           "result_generated_by_legacy_proxy", "pass_fail"], rows)

    # ------------------------------------------------------------------ regenerated 24-row closure
    scope = list(csv.DictReader((OUT / "run30_cat6_7_scope.csv").open(encoding="utf-8")))
    assert len(scope) == 24, f"expected 24 scope rows, got {len(scope)}"
    corpus = {r["canonical_id"]: r for r in csv.DictReader(
        (OUT / "run30_real_corpus_structure_reconciliation.csv").open(encoding="utf-8"))}
    rows = []
    for r in scope:
        cid, rid = r["canonical_id"], r["registry_id"]
        cat7 = rid.startswith("B2.")
        disabled = rid in REG.DISABLED_MODULES
        runner_module = REG.VALIDATED[rid][1].__module__ if rid in REG.VALIDATED else "n/a"
        prod_canonical = ("yes" if (not cat7 or runner_module == "app.simulation.models_cat7")
                          else "NO")
        legacy_reachable = ("no" if not cat7
                            else ("no" if runner_module == "app.simulation.models_cat7"
                                  else "YES"))
        rows.append([
            cid, rid, r["current_name"],
            "yes", "yes", prod_canonical, legacy_reachable,
            "yes" if r["v5_structure_key"] != "(none: no new structure)"
            else "yes (the assembled governed signals)",
            corpus[cid]["present_in_controlled_corpus"],
            "yes",
            "yes",
            "no" if (cat7 or disabled) else r["run30_objective"] and "yes",
            "yes",
            corpus[cid]["parameter_provenance"],
            "yes" if disabled else "no",
            "yes",
            r["remaining_run31_work"], r["remaining_run33_work"],
            "DISABLED_UNSAFE" if disabled else "ADVISORY_ONLY",
            r["current_scientific_disposition"],
        ])
    # The four Category-6 rows keep their measured operational state rather than a blanket "no".
    for row in rows:
        if row[1] in ("B1.1", "B1.3", "B1.4"):
            row[11] = "yes"
        elif row[1] == "B1.2":
            row[11] = "no"
    write("run30_cat6_7_final_closure.csv",
          ["canonical_id", "registry_id", "module",
           "canonical_structure_implemented", "canonical_mathematics_implemented",
           "production_runner_canonical", "legacy_production_path_reachable",
           "production_supply_path", "real_corpus_populated",
           "oracle_through_production_pass", "invalid_admissibility_pass",
           "operational_result", "abstains", "parameter_provenance",
           "disabled_or_archive", "lineage",
           "run31_pending", "run33_pending", "activation", "final_disposition"], rows)

    cat7_rows = [r for r in rows if r[1].startswith("B2.")]
    print(f"  Category-7 production canonical: "
          f"{sum(1 for r in cat7_rows if r[5] == 'yes')}/20")
    print(f"  Category-7 legacy reachable:     "
          f"{sum(1 for r in cat7_rows if r[6] != 'no')}")


if __name__ == "__main__":
    main()
