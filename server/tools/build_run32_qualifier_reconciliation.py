"""
RUN 32 FINAL CLOSURE. THE PROXY-QUALIFIER RECONCILIATION.

CLASSIFICATION IS NOT INFERRED FROM ABSENCE. A qualifier missing from the server is not evidence
that it was withdrawn; that inference is the error this programme has already paid for once. The
rule applied here is the one the runs themselves state and act on:

    Run 29: "removed six proxy qualifiers from registry.py BECAUSE THE SIX MODULES THEY DESCRIBED
             NOW PERFORM THEIR CANONICAL METHODS"
    Run 30: legacy-proxy markers "8 proxy qualifiers, 3 truthful labels" -> "none"

So a proxy qualifier is WITHDRAWN when the module it described was repointed onto its canonical
method, and that is established by the module's PRODUCTION ROUTE -- whether its runner resolves
into a canonical layer and requires a governed structure -- not by whether the server happens to
carry a string today.

The pre-change lookup behaviour is measured by EXECUTION and read from
code_audit/run32_pre_change_qualifier_measurement.json, captured before any edit.
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import registry as REG                                  # noqa: E402
from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS as K0         # noqa: E402
from app.simulation.canonical_v3 import V3_STRUCTURE_KEYS as K3             # noqa: E402
from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS as K4             # noqa: E402
from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS as K5             # noqa: E402
from app.simulation.canonical_v6 import V6_STRUCTURE_KEYS as K6             # noqa: E402
from app.simulation.canonical_v7 import V7_STRUCTURE_KEYS as K7             # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED as PV              # noqa: E402

LAYERS = (("canonical", K0), ("v3", K3), ("v4", K4), ("v5", K5), ("v6", K6), ("v7", K7))
REMEDIATED_BY = {"canonical": "Run 10B/earlier", "v3": "Run 28", "v4": "Run 29",
                 "v5": "Run 30", "v6": "Run 31", "v7": "Run 32"}

CONSUMER = ("assets/js/knowledge.js modDoc() -> RUN1_PROXY_QUALIFIER[m.mc], rendered as "
            "'Status. Proxy: <text>. Advisory, non-voting.' on the per-module method "
            "documentation; server registry.PROXY_QUALIFIERS is consumed by "
            "tools/build_run11_defensibility_evidence.py, which appends 'Stated proxy: <text>.' "
            "to the served defensibility object's qualification sentence")


def layer_of(mid):
    for name, m in LAYERS:
        if mid in m:
            return name, m[mid]
    return None, None


def main() -> int:
    pre = json.loads((ROOT / "code_audit" /
                      "run32_pre_change_qualifier_measurement.json").read_text(encoding="utf-8"))
    reg = {m["new_id"]: m["module_name"] for m in REG.load_registry()}
    rows, counts, problems = [], {}, []
    seen_keys = set()

    for key, info in sorted(pre["keys"].items()):
        mid = info["resolvesToModule"]
        if key in seen_keys:
            problems.append(f"duplicate client key {key}")
        seen_keys.add(key)
        layer, struct = layer_of(mid)
        # THE PRE-CHANGE SERVER STATE, pinned in the measurement file from commit
        # 19a7055. Reading the LIVE registry here would make this artifact
        # non-reproducible: once a stale entry is withdrawn the record of what was
        # withdrawn, and of the text it carried, would vanish from the very artifact
        # that exists to preserve it.
        srv = pre["serverQualifiersBeforeChange"].get(mid)
        mc = REG.VALIDATED[mid][0] if mid in REG.VALIDATED else (
            f"portfolio ({PV[mid]})" if mid in PV else "(no runner)")

        if layer is None and srv:
            cls = "CURRENT_REQUIRED"
            action = ("KEEP. The module has no canonical layer and still computes the proxy the "
                      "qualifier describes; the server holds it and the client key already "
                      "matches the current method class.")
        elif layer is not None:
            cls = "WITHDRAWN"
            why = REMEDIATED_BY[layer]
            action = (f"REMOVE from the client map. {why} repointed this module onto its "
                      f"canonical method (layer {layer}, governed structure "
                      f"{struct}), which is the condition under which Runs 29 and 30 withdrew "
                      f"proxy qualifiers in terms. The qualifier describes a proxy that no "
                      f"longer exists.")
            if srv:
                action += (" THE SERVER ENTRY IS ALSO STALE and is removed from "
                           "registry.PROXY_QUALIFIERS: it survived the remediation that "
                           "withdrew the method it describes.")
        elif layer is None and not srv:
            cls = "CURRENT_SERVER_QUALIFIER_MISSING"
            action = ("HOLD. The module has no canonical layer, so it may still be a proxy, but "
                      "the server carries no qualifier for it. Reported rather than invented.")
        else:                                                               # pragma: no cover
            problems.append(f"{mid} fits none of the permitted classifications")
            cls, action = "UNCLASSIFIED", "STOP AND REPORT"

        counts[cls] = counts.get(cls, 0) + 1
        rows.append([
            mid, reg.get(mid, "?"), mc, key, mid if srv else "",
            (srv[:160] if srv else "no current server qualifier"),
            CONSUMER,
            info["rendered"][:150] if info["rendered"] else "no Status line rendered",
            ("YES - the Run-1 qualifier and the run that withdrew it are preserved in the run "
             "reports and in this artifact" if cls == "WITHDRAWN" else "NO"),
            cls, action,
            "PASS" if cls != "UNCLASSIFIED" else "FAIL"])

    # Every current server qualifier must be accounted for by some row.
    accounted = {r[0] for r in rows}
    unaccounted = sorted(set(REG.PROXY_QUALIFIERS) - accounted)
    for mid in unaccounted:
        layer, struct = layer_of(mid)
        cls = "WITHDRAWN" if layer else "CURRENT_REQUIRED"
        counts[cls] = counts.get(cls, 0) + 1
        rows.append([mid, reg.get(mid, "?"),
                     REG.VALIDATED[mid][0] if mid in REG.VALIDATED else "(no runner)",
                     "(no client key)", mid, REG.PROXY_QUALIFIERS[mid][:160], CONSUMER,
                     "not reachable from the client map", "NO", cls,
                     "server-side entry with no client key; accounted for here", "PASS"])

    out = ROOT / "code_audit" / "run32_proxy_qualifier_reconciliation.csv"
    with artifact_out(out).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["module ID", "current authoritative module name", "current method class",
                    "client qualifier key", "current server qualifier key",
                    "server qualifier text/state", "current consumer(s)",
                    "current browser/API result", "historical evidence requiring preservation?",
                    "classification", "required action", "PASS/FAIL"])
        w.writerows(rows)

    print(f"client qualifier entries inspected : {len(pre['keys'])}")
    print(f"rows                               : {len(rows)}")
    print(f"duplicate current keys             : {len(pre['keys']) - len(seen_keys)}")
    print(f"unclassified                       : {sum(1 for r in rows if r[9] == 'UNCLASSIFIED')}")
    print(f"server qualifiers                  : {len(REG.PROXY_QUALIFIERS)} "
          f"(unaccounted: {len(unaccounted)})")
    for k, v in sorted(counts.items()):
        print(f"   {v:3d}  {k}")
    if problems:
        print("\nPROBLEMS REQUIRING A STOP:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
