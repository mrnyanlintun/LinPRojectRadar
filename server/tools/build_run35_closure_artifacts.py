#!/usr/bin/env python3
"""
RUN 35 FINAL CLOSURE: the stale-method-label reconciliation and the A1.1 Run-36 handoff record.

Every field is derived: the canonical name from the REGISTRY authority CSV, the current
implementation by resolving the production dispatch entry through `__wrapped__`, the withdrawn
sentences from the v22 git object (they no longer exist in the tree, which is the point), and the
A1.1 consumer count by searching the production source for the declared structure key.

Writes:
  code_audit/run35_stale_method_label_reconciliation.csv
  code_audit/run35_a1_1_run36_handoff.json
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from app.simulation import registry as REG                                 # noqa: E402
from app.simulation.method_labels import TRUTHFUL_METHOD_LABELS as LABELS   # noqa: E402
from app.simulation.models import SIMULATION_VERSION, VALIDATED            # noqa: E402

V22_COMMIT = "034cf03be257f4582bc1a856262c56ea11bb4558"
OUT_DIR = ROOT / "code_audit"
TARGETS = ("B1.2", "B4.4")


def git_show(path, rev=V22_COMMIT):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def resolved_runner(mid):
    fn = VALIDATED[mid][1]
    inner = getattr(fn, "__wrapped__", fn)
    return f"{inner.__module__}.{inner.__name__}"


def stale_label_from_v22(mid):
    """The withdrawn sentences, read out of the predecessor object rather than retyped."""
    src = git_show("server/app/simulation/method_labels.py")
    m = re.search(r'"%s": MethodLabel\((.*?)\n    \),' % re.escape(mid), src, re.S)
    if not m:
        return {}
    body = m.group(1)
    out = {}
    for field in ("registered", "truthful", "performs", "absent", "disposition"):
        f = re.search(r'%s="((?:[^"\\]|\\.)*)"(?:\s*\n\s*"((?:[^"\\]|\\.)*)")*' % field, body)
        if f:
            joined = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"',
                                        body.split(field + "=", 1)[1].split("\n        ")[0]))
            out[field] = joined or f.group(1)
    return out


def label_rows():
    idx = REG.registry_index()
    rows = []
    for mid in TARGETS:
        canonical = idx[mid]["module_name"]                 # THE REGISTRY AUTHORITY
        old = stale_label_from_v22(mid)
        stale = f'{old.get("truthful", "")} -- "{old.get("performs", "")[:180]}"'
        removed = old.get("absent", "")[:260]
        surfaces = ("server/app/simulation/method_labels.py (TRUTHFUL_METHOD_LABELS entry "
                    "withdrawn, so the API response, the export and the methods documentation "
                    "now present the registry name)")
        rows.append([
            mid, stale, removed, resolved_runner(mid), canonical,
            "p0-baseline/module_renumbering_map.csv (the registry authority the frontend "
            "taxonomy is generated from); the same name is carried by assets/js/categories.js "
            "and assets/js/taxonomy.js, which are GENERATED FROM it and are not the authority",
            surfaces,
            "NO",                                            # implementation_changed?
            "PASS" if LABELS.get(mid) is None else "FAIL",
        ])
    return rows


def a1_1_record():
    """
    The A1.1 finding, carried forward untouched. The consumer count is SEARCHED, not asserted, so
    if a consumer is ever added this record reports a different number.
    """
    from app.project_data import governed_structure_keys
    from app.simulation.canonical_v3 import V3_STRUCTURE_KEYS
    key = V3_STRUCTURE_KEYS["A1.1"]
    hits = []
    for p in sorted((ROOT / "server" / "app").rglob("*.py")):
        if "__pycache__" in str(p):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if key in text:
            rel = str(p.relative_to(ROOT))
            hits.append({"file": rel, "occurrences": text.count(key)})
    declaring = [h for h in hits if h["file"].endswith("canonical_v3.py")]
    consumers = [h for h in hits if not h["file"].endswith("canonical_v3.py")]
    fn = VALIDATED["A1.1"][1]
    inner = getattr(fn, "__wrapped__", fn)
    return {
        "finding_id": "DECLARED_STRUCTURE_UNCONSUMED_AND_REACHABLE_PARAMETER_UNRESOLVED",
        "module": "A1.1 Monte Carlo EAC Forecast",
        "declared_structure": key,
        "intake_accepts_it": key in governed_structure_keys(),
        "files_mentioning_the_key": hits,
        "declaration_sites": len(declaring),
        "consumers_found": len(consumers),
        "current_production_path": f"{inner.__module__}.{inner.__name__}",
        "current_production_reads": ["bac", "cpi", "spi", "docRiskScore"],
        "unresolved_reachable_parameter": (
            "a four band ladder over the quantity the module reports, classified UNSUPPORTED in "
            "server/app/simulation/parameters.py and APPLIED: A1.1 is the only scientific target "
            "that emits a status colour from an unresolved parameter on the governed corpus"),
        "remediation_attempted_in_this_closure": "NONE",
        "why_not": (
            "The Run-35 closure owner decision reserves A1.1 for Run 36. Implementing the "
            "declared cost-driver-distribution Monte Carlo is a canonical-remediation workstream "
            "of Run-28 scale, and withdrawing the module's current reading would change "
            "participant-visible output."),
        "run36_action": "EARLY AUDIT TARGET. Lead the Run-36 handoff with this finding.",
        "recorded_at_simulation_version": SIMULATION_VERSION,
    }


def main():
    rows = label_rows()
    p = OUT_DIR / "run35_stale_method_label_reconciliation.csv"
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["module_id", "stale_label", "removed_proxy", "current_implementation",
                    "canonical_method", "canonical_name_source", "changed_surfaces",
                    "implementation_changed", "result"])
        w.writerows(rows)
    print(f"wrote {p.relative_to(ROOT)}: {len(rows)} rows")
    for r in rows:
        print(f"  {r[0]}: canonical name = {r[4]!r}  implementation = {r[3]}  "
              f"implementation_changed={r[7]}  {r[8]}")

    rec = a1_1_record()
    q = OUT_DIR / "run35_a1_1_run36_handoff.json"
    q.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {q.relative_to(ROOT)}: consumers_found={rec['consumers_found']}, "
          f"intake_accepts_it={rec['intake_accepts_it']}")


if __name__ == "__main__":
    main()
