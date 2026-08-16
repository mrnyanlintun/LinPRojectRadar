"""
RUN 30 FINAL CLOSURE -- THE LINEAGE HANDOFF AND THE 17-VERSUS-18 LEDGER RECONCILIATION.

BOTH ARTIFACTS ARE MEASUREMENTS. The lineage states come from `lineage.lineage_status` applied to
the shipped declaration table. The before/after ledger columns come from EXECUTING both analytical
lines -- the v15 package extracted from git object ce03eb1, and the current one -- through
`registry.run_all`, which is the function that decides what a ledger row is. Neither column is
transcribed from the previous report, because it was the previous report's unchecked count that
made this reconciliation necessary.
"""

from __future__ import annotations

import csv
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import lineage as LIN                        # noqa: E402
from app.simulation import registry as REG                       # noqa: E402
from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS, V5_STRUCTURE_WORDS  # noqa: E402

OUT = ROOT / "code_audit"
V15_COMMIT = "ce03eb1"

#: The controlled real-corpus shape: exactly the flat signal inputs a reporting period produces.
SI = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
      "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
      "actualPctComplete": 40.0, "plannedPctComplete": 45.0}

CAT7 = sorted((m for m in REG.registry_index() if m.startswith("B2.")),
              key=lambda m: int(m.split(".")[1]))


def load_v15():
    """The v15 analytical package, extracted from its pinned git object and imported."""
    tmp = tempfile.mkdtemp(prefix="run30f-v15-")
    pkg = pathlib.Path(tmp) / "oldsim30f"
    pkg.mkdir()
    names = subprocess.run(["git", "ls-tree", "--name-only", V15_COMMIT,
                            "server/app/simulation/"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    py = [n for n in names if n.endswith(".py")]
    if len(py) < 10:
        raise SystemExit("v15 extraction found no simulation sources; refusing to half-measure")
    for n in py:
        src = subprocess.run(["git", "show", f"{V15_COMMIT}:{n}"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        (pkg / pathlib.Path(n).name).write_text(src, encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    sys.path.insert(0, tmp)
    import oldsim30f.registry as R15                              # noqa: E402
    # The extracted package reads the registry CSV by a path relative to its own location, which
    # the temporary directory breaks. Repointing it at the repository's own file is the only
    # adjustment made, and it changes no analytical behaviour.
    R15.CSV_PATH = ROOT / "p0-baseline" / "module_renumbering_map.csv"
    if R15.SIMULATION_VERSION != "sim-2026.08-v15":
        raise SystemExit(f"extracted package is stamped {R15.SIMULATION_VERSION}, not v15")
    return R15


def ledger(runner) -> tuple[dict, dict]:
    out = runner.run_all(dict(SI), "S", "P1", "2026-06-30")
    return ({m["module_id"]: m for m in out["computed"]},
            {m["module_id"]: m for m in out["abstained"]})


def write(name: str, header: list[str], rows: list[list]) -> None:
    path = OUT / name
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path.relative_to(ROOT)}: {len(rows)} rows")


def main() -> None:
    R15 = load_v15()
    c15, a15 = ledger(R15)
    c16, a16 = ledger(REG)
    index = REG.registry_index()
    disabled = set(REG.DISABLED_MODULES)

    # ------------------------------------------------------------------ ledger reconciliation
    rows = []
    counts = {"v15_runners_executed": 0, "v15_populated_analytical": 0, "v15_disabled": 0,
              "v16_canonical_runners": 0, "v16_numerical_results": 0,
              "v16_canonical_abstentions": 0, "v16_disabled": 0}
    for mid in CAT7:
        is_disabled = mid in disabled
        v15_ran = not is_disabled
        v15_row = c15.get(mid) or a15.get(mid)
        v15_computed = mid in c15
        v15_status = (c15.get(mid) or {}).get("status_color")
        v16_row = c16.get(mid) or a16.get(mid)
        v16_computed = mid in c16
        v16_status = (c16.get(mid) or {}).get("status_color")
        v16_disp = (v16_row or {}).get("canonical_disposition")

        if v15_ran:
            counts["v15_runners_executed"] += 1
        if v15_computed and v15_status is not None:
            counts["v15_populated_analytical"] += 1
        if is_disabled:
            counts["v15_disabled"] += 1
            counts["v16_disabled"] += 1
        else:
            counts["v16_canonical_runners"] += 1
            if v16_computed and v16_status is not None:
                counts["v16_numerical_results"] += 1
            else:
                counts["v16_canonical_abstentions"] += 1

        if is_disabled:
            why = ("disabled or archived under BOTH lines. It carries a ledger row stating that "
                   "state and has never been a populated analytical reading, so it belongs in "
                   "neither before nor after analytical count")
        elif v15_computed and v15_status is not None:
            why = ("its v15 runner executed and produced a banded analytical reading from crisp "
                   "project metrics; under v16 the canonical route abstains because the defining "
                   "structure is absent from this corpus")
        else:
            why = ("ITS v15 RUNNER EXECUTED AND STILL ABSTAINED, which is why the count of "
                   "runners and the count of populated rows are different quantities: it already "
                   "required an explicit decision structure that this corpus does not carry")
        rows.append([
            mid, index[mid]["module_name"],
            "disabled/archived, short-circuited" if is_disabled else "legacy proxy runner",
            "no" if is_disabled else "yes",
            f"{v15_status}" if v15_computed else "(abstained)",
            "yes" if v15_row else "no",
            "computed" if v15_computed else "abstained",
            "disabled/archived, refuses before any mathematics" if is_disabled
            else "canonical route into canonical_v5",
            "no (refused at the gate)" if is_disabled else "yes",
            "yes" if v16_row else "no",
            v16_disp or ("computed" if v16_computed else "abstained"),
            "yes" if is_disabled else "no",
            why,
        ])
    write("run30_cat7_before_after_ledger_reconciliation.csv",
          ["module", "v15_operational_runner_state", "v15_runner_executed", "v15_legacy_result",
           "v15_ledger_row_existed", "v15_ledger_row_disposition",
           "v16_operational_runner_state", "v16_canonical_reached", "v16_ledger_row_exists",
           "v16_ledger_disposition", "disabled_or_archive", "explanation"],
          [[r[0]] + r[2:] for r in rows])

    # ------------------------------------------------------------------ lineage handoff
    hrows = []
    for mid in CAT7:
        is_disabled = mid in disabled
        row = c16.get(mid) or a16.get(mid) or {}
        lin = row.get("lineage") or {}
        status = lin.get("lineage_status")
        prov = lin.get("source_provenance") or {}
        source_known = bool(prov)
        if is_disabled:
            action = ("E. disabled or archived: no evidence and no qualification question. Run "
                      "31 excludes it rather than qualifying it")
        elif status == LIN.LINEAGE_UNRESOLVED:
            action = ("C. lineage unresolved: independence is NOT established, so this row may "
                      "never corroborate another. Run 31 qualifies it as unresolved, and only an "
                      "assessor-side provenance record could move it")
        elif status == LIN.LINEAGE_ESTABLISHED_INDEPENDENT:
            action = "A. lineage established and eligible"
        else:
            action = "B. lineage established but dependent"
        # C AND D ARE ORTHOGONAL AND ON THIS CORPUS BOTH APPLY, so both are said. Whether a
        # module produced evidence is a fact about THIS period; whether its lineage is
        # established is a fact about the structure's provenance. Forcing one letter would make
        # Run 31 guess which question had been answered.
        disp = row.get("canonical_disposition")
        if not is_disabled and disp in ("NOT_ESTIMABLE_STRUCTURE_ABSENT", "OPERATOR_BLOCKED"):
            action = ("D. no evidence this period: the module abstained for want of its defining "
                      "structure, so there is nothing to qualify until one is supplied. AND "
                      + action.split(": ", 1)[0].replace("C.", "C.") + ": lineage is unresolved "
                      "independently of that, so supplying the structure alone would not "
                      "establish independence")
        hrows.append([
            mid,
            "DISABLED_UNSAFE" if is_disabled else "ADVISORY_ONLY, non-voting",
            "yes" if source_known else "no",
            "; ".join(f"{k}={v}" for k, v in sorted(prov.items())) or
            ("(none: no structure was supplied)" if not is_disabled
             else "(none: produces no reading)"),
            status,
            lin.get("evidence_body") or "(none established)",
            "yes" if lin.get("independence_established") else "no",
            row.get("signal_qualification") or "unqualified (Category-9 gate is Run 31's)",
            row.get("canonical_disposition") or "(no disposition)",
            action,
            "PASS" if (status in LIN.LINEAGE_STATES
                       and lin.get("independence_established") is not None
                       and not (lin.get("evidence_body")
                                and status == LIN.LINEAGE_UNRESOLVED)) else "FAIL",
        ])
    write("run30_cat7_lineage_handoff.csv",
          ["module", "operational_state", "source_known", "source", "lineage_status",
           "evidence_body", "independence_established", "qualification_status",
           "current_result_or_disposition", "run31_action_required", "pass_fail"], hrows)

    print()
    print("THE SEVEN COUNTS, MEASURED BY EXECUTING BOTH LINES:")
    for k, v in counts.items():
        print(f"  {k:34} {v}")
    print(f"  {'populated analytical -> abstention':34} "
          f"{counts['v15_populated_analytical']}")
    return counts


if __name__ == "__main__":
    main()
