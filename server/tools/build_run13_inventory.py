#!/usr/bin/env python3
"""
RUN 13 GATE 1 — derive the canonical 101-module inventory mechanically.

Nothing here is copied from a prompt or a report. Every column is read from the governed
registry CSV, the implementation tables (VALIDATED, PORTFOLIO_VALIDATED), the disabled set,
the voting set, the canonical-structure and reference-object contracts, and the module source.

Writes code_audit/run13_master_101_inventory.csv (exactly 101 rows).
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import inspect
import pathlib
import re
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation import canonical  # noqa: E402
from app.simulation.models import SIMULATION_VERSION, STOCHASTIC, VALIDATED  # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, PROXY_QUALIFIERS, load_registry,
)
from app.simulation.signal_package import NESTED_INPUT_MODULES  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "code_audit" / "run13_master_101_inventory.csv"

KEY_RE = re.compile(r"""si(?:\w*)?\.get\(\s*["'](\w+)["']|si\[\s*["'](\w+)["']\s*\]""")

COLUMNS = [
    "module_id", "canonical_name", "category", "layer", "implementation_path",
    "registry_status", "enabled", "disabled", "executable", "voting", "advisory",
    "concept_only", "synthetic_fixture_available", "canonical_structure_required",
    "reference_dataset_required", "expected_runtime_behavior", "simulation_version",
]

FIXTURE_DIR = ROOT / "server" / "tests" / "synthetic_fixtures"


def read_keys(fn) -> list[str]:
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        return []
    keys = set()
    for m in KEY_RE.finditer(src):
        keys.add(m.group(1) or m.group(2))
    return sorted(k for k in keys if k)


def fixture_ids() -> set[str]:
    ids: set[str] = set()
    if not FIXTURE_DIR.exists():
        return ids
    for p in FIXTURE_DIR.rglob("*"):
        if p.is_file() and p.suffix in {".csv", ".json"}:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for mid in re.findall(r"\b([ABCD]\d+\.\d+)\b", text):
                ids.add(mid)
    return ids


def main() -> int:
    rows = load_registry()
    fixtures = fixture_ids()
    out_rows = []
    for r in rows:
        mid = r["new_id"]
        group = r["group"]
        layer = "PORTFOLIO" if group == "D" else "PROJECT"
        disabled = mid in DISABLED_CONCEPT_ONLY
        voting = mid in CORE_VOTING_MODULES
        if layer == "PORTFOLIO":
            impl = "server/app/simulation/portfolio.py"
            executable = mid in PORTFOLIO_VALIDATED
        elif mid in VALIDATED:
            fn = VALIDATED[mid][1]
            impl = fn.__module__.replace("app.simulation.", "server/app/simulation/") + ".py"
            impl = impl.replace(".", "/", 0)
            impl = f"server/app/simulation/{fn.__module__.rsplit('.', 1)[1]}.py::{fn.__name__}"
            executable = not disabled
        else:
            impl = ""
            executable = False
        if disabled:
            behaviour = ("short-circuited in registry.run_module before the formula function is "
                         "called; returns insufficient_data with DISABLED_UNSAFE")
            status = "DISABLED_UNSAFE"
        elif layer == "PORTFOLIO":
            behaviour = ("computed only by portfolio.compute_portfolio over a project list; "
                         "registry.run_module raises PortfolioModuleError on the single-project "
                         "path")
            status = "PORTFOLIO_EXECUTABLE"
        elif mid not in VALIDATED:
            behaviour = ("not ported; registry.run_module raises MissingModuleError rather than "
                         "approximating")
            status = "REGISTERED_NOT_PORTED"
        else:
            behaviour = ("executed on the single-project path; computes or abstains with a "
                         "reader sentence")
            status = "ENABLED_QUALIFIED" if voting else "ADVISORY_ONLY"
        out_rows.append({
            "module_id": mid,
            "canonical_name": r["module_name"],
            "category": r["category"],
            "layer": layer,
            "implementation_path": impl,
            "registry_status": status,
            "enabled": "NO" if disabled or not executable else "YES",
            "disabled": "YES" if disabled else "NO",
            "executable": "YES" if executable else "NO",
            "voting": "YES" if voting else "NO",
            "advisory": "NO" if (voting or disabled) else "YES",
            "concept_only": "YES" if disabled else "NO",
            "synthetic_fixture_available": "YES" if mid in fixtures else "NO",
            "canonical_structure_required": canonical.CANONICAL_STRUCTURE_KEYS.get(mid, ""),
            "reference_dataset_required": canonical.REFERENCE_OBJECT_KEYS.get(mid, ""),
            "expected_runtime_behavior": behaviour,
            "simulation_version": SIMULATION_VERSION,
        })

    artifact_out(OUT.parent).mkdir(exist_ok=True)
    with artifact_out(OUT).open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out_rows)

    proj = [r for r in out_rows if r["layer"] == "PROJECT"]
    port = [r for r in out_rows if r["layer"] == "PORTFOLIO"]
    dis = [r for r in out_rows if r["disabled"] == "YES"]
    print(f"rows                     {len(out_rows)}")
    print(f"unique module ids        {len({r['module_id'] for r in out_rows})}")
    print(f"PROJECT                  {len(proj)}")
    print(f"PORTFOLIO                {len(port)}")
    print(f"disabled (project)       {len([r for r in dis if r['layer'] == 'PROJECT'])}")
    print(f"non-disabled project     {len([r for r in proj if r['disabled'] == 'NO'])}")
    print(f"non-disabled portfolio   {len([r for r in port if r['disabled'] == 'NO'])}")
    print(f"non-disabled total       {len([r for r in out_rows if r['disabled'] == 'NO'])}")
    print(f"voting                   {sorted(r['module_id'] for r in out_rows if r['voting'] == 'YES')}")
    print(f"executable project       {len([r for r in proj if r['executable'] == 'YES'])}")
    print(f"stochastic               {sorted(STOCHASTIC)}")
    print(f"nested-input modules     {len(NESTED_INPUT_MODULES)}")
    print(f"proxy-qualified          {len(PROXY_QUALIFIERS)}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
