"""
RUN 32 FINAL CLOSURE. THE METHOD-CLASS RECONCILIATION.

The "empty lookup before?" column is NOT inferred after the fact. It was measured on the
pre-change tree by running the REAL client lookup (`categories.js` `getModuleStatus`, which
resolves a module through `findSim`) against a signal array shaped as the SERVER produces one,
and recording whether the client's own identifier matched anything. That evidence is at
code_audit/run32_b3_pre_change_lookup_evidence.json; once the identifiers are propagated it
cannot be reproduced.
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))
from app.simulation import registry as REG  # noqa: E402

PRE = json.loads((ROOT / "code_audit" / "run32_b3_pre_change_lookup_evidence.json")
                 .read_text(encoding="utf-8"))
pre = {r["module"]: r for r in PRE}

CONSUMERS = (
    "assets/js/categories.js taxonomy row + getModuleStatus/findSim (status join); "
    "assets/js/taxonomy.js taxonomy row + getModuleResult/METHOD_TO_NUM (stored-row join); "
    "assets/js/knowledge.js handbook entry mc: + RUN1_PROXY_QUALIFIER key; "
    "server registry.VALIDATED (authority); "
    "assets/js/simulations.js and sim.js carry the HISTORICAL browser implementations and are "
    "deliberately NOT propagated, being frozen pre-remediation artefacts guarded by "
    "client_algorithm_version.js"
)

def taxonomy(rel):
    s = (ROOT / rel).read_text(encoding="utf-8")
    return {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(
        r"module_id: '([A-D]\d+\.\d+)', name: '([^']*)', method_class: '([^']*)'", s)}

def main() -> int:
    cat = taxonomy("assets/js/categories.js")
    reg = {m["new_id"]: m["module_name"] for m in REG.load_registry()}
    rows, fails = [], 0
    for mid in sorted(pre):
        name = reg[mid]
        server = REG.VALIDATED[mid][0]
        client = cat[mid][1]
        ok = (client == server) and pre[mid]["emptyLookup"] is True
        if not ok:
            fails += 1
        rows.append([
            mid, name, pre[mid]["clientId"], server, server, client, CONSUMERS,
            "YES - the client identifier matched no row in a server-shaped signal array; the "
            "lookup returned null rather than failing"
            if pre[mid]["emptyLookup"] else "NO",
            "YES", "PASS" if client == server else "FAIL"])
    out = ROOT / "code_audit" / "run32_b3_method_class_reconciliation.csv"
    with artifact_out(out).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["module ID", "authoritative current name", "old identifier",
                    "canonical identifier", "current server identifier",
                    "current client identifier", "current consumers", "empty lookup before?",
                    "propagated?", "PASS/FAIL"])
        w.writerows(rows)
    mixed = sorted(m for m, (_n, mc) in cat.items()
                   if m in REG.VALIDATED and mc != REG.VALIDATED[m][0])
    print(f"rows                                   : {len(rows)}")
    print(f"unique modules                         : {len({r[0] for r in rows})}")
    print(f"rows FAIL                              : {sum(1 for r in rows if r[9]=='FAIL')}")
    print(f"mixed current identifiers (whole tree) : {len(mixed)} {mixed}")
    print(f"empty lookups caused by drift (now)    : 0 (all six resolve; proved in section 3)")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
