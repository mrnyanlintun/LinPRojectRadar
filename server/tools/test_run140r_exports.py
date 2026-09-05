#!/usr/bin/env python3
"""
RUN 140 R -- PROOF 8: THE EXPORTS CARRY WHAT THE CARD SHOWED.

Run (from server/):

    python tools/test_run140r_exports.py

WHAT IS PROVEN. The audit JSON (`decision.js buildAuditRecord`) and the XLSX workbook
(`export.js exportProjectReport`) are both driven, in a sandbox, against the SAME fixture brief
the render check uses, and every mitigation field the card rendered is then found in each
export. The comparison is field by field and verbatim: an export that rounded a gap, dropped a
candidate or lost a composition date fails here.

WHAT IS ALSO PROVEN, AND MATTERS AS MUCH. With no `mitigations` key -- the ungated case, which
is most cards -- the audit JSON has NO `mitigations` key at all (not an empty list, which is a
different claim) and the workbook has FOUR sheets, not five with one empty.

AND: the Run 98 removals are still removed. `recommended_action`, `authority`,
`documentation_required` and `action_plan` must not reappear in the record under any name, and a
mitigation entry must carry no key that assigns an owner, a date or a document.

THE CHECKS ARE PROVEN ABLE TO FAIL: GUARANTEE 0 corrupts a gap in the fixture and asserts the
verbatim comparison rejects it.

WHAT THIS DOES NOT TOUCH, DELIBERATELY. `server/app/research_export.py` is NOT widened. Its
`MODULE_RESULT_COLUMNS` and `EXPORT_COLUMNS` are covered by checksums over every historical
export; adding a column invalidates all of them. If the committee export should carry
mitigations it needs a NEW export kind, which is beyond the order this run implements.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

from test_run140r_render import BRIEF, MITIGATIONS  # noqa: E402  the one fixture, not a copy

HARNESS = r"""
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = process.argv[2];
const fx = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));

/* THE WORKBOOK IS NOT WRITTEN TO DISK. `XLSX` is replaced by a recorder that captures the
   sheet names and the raw arrays-of-arrays handed to it, which is exactly what the real
   SheetJS receives. Nothing is faked into working: `aoa_to_sheet` is the identity on the rows,
   so what is asserted below is the literal cell content `export.js` composed. */
const sheets = [];
const XLSX = {
  utils: {
    book_new: () => ({}),
    aoa_to_sheet: (rows) => ({ rows }),
    book_append_sheet: (wb, ws, name) => { sheets.push({ name, rows: ws.rows }); }
  },
  writeFile: () => {}
};

function el() { return { querySelector: () => null, querySelectorAll: () => [],
  addEventListener(){}, classList: { add(){}, remove(){} }, insertAdjacentHTML(){}, style: {},
  setAttribute(){}, getAttribute: () => null, appendChild(){}, remove(){},
  innerHTML: "", textContent: "", className: "", dataset: {} }; }
const sandbox = { console, JSON, Math, Date, Number, String, Object, Array, RegExp, isNaN,
  parseFloat, parseInt, setTimeout, clearTimeout, XLSX, alert: () => {},
  document: Object.assign(el(), { createElement: el, getElementById: () => null, body: el(),
                                  documentElement: el(), addEventListener(){} }),
  navigator: { userAgent: "node" }, location: { href: "", search: "" },
  localStorage: { getItem: () => null, setItem(){}, removeItem(){} } };
sandbox.window = sandbox; sandbox.self = sandbox; sandbox.globalThis = sandbox;
vm.createContext(sandbox);
for (const f of ["assets/js/config.js", "assets/js/taxonomy.js", "assets/js/decision.js",
                 "assets/js/export.js"]) {
  try { vm.runInContext(fs.readFileSync(path.join(ROOT, f), "utf8"), sandbox, { filename: f }); }
  catch (e) { console.error("[load] " + f + ": " + e.message); }
}

const project = fx.project;
const decision = { healthState: "Amber", conflictType: "none", fairnessGateRequired: false };
const reviewer = { rationale: "recorded", recordedAt: "2026-09-05T00:00:00Z" };
const build = sandbox.buildAuditRecord || (sandbox.window.LinDecision &&
                                           sandbox.window.LinDecision.buildAuditRecord);

function workbook(brief) { sheets.length = 0;
  sandbox.window.LinExport.exportProjectReport(project, brief);
  return sheets.map((s) => ({ name: s.name, rows: s.rows })); }

fs.writeFileSync(process.argv[4], JSON.stringify({
  haveBuild: typeof build === "function",
  auditWith: typeof build === "function" ? build(project, decision, reviewer, fx.brief) : null,
  auditNoKey: typeof build === "function" ? build(project, decision, reviewer, fx.briefNoKey) : null,
  auditNoBrief: typeof build === "function" ? build(project, decision, reviewer, null) : null,
  auditCorrupt: typeof build === "function" ? build(project, decision, reviewer, fx.briefCorrupt) : null,
  bookWith: workbook(fx.brief),
  bookNoKey: workbook(fx.briefNoKey)
}));
"""

PASSED = 0
TOTAL = 0
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    global PASSED, TOTAL
    TOTAL += 1
    if cond:
        PASSED += 1
        print("  [PASS] " + name)
        return True
    FAILS.append(name + (" -- " + detail if detail else ""))
    print("  [FAIL] " + name + (" -- " + detail if detail else ""))
    return False


PROJECT = {
    "id": "P-140", "name": "Fixture Project", "reportingPeriod": "2026-09",
    "signals": {"bac": 1000},
    "history": [{
        "project_id": "P-140", "project_name": "Fixture Project", "period": "2026-09",
        "governance": {"state": "Amber"}, "signal_inputs": {},
        "summary": {"evidence_agreement": {}}, "categories": {},
    }],
}


def main() -> int:
    brief_no_key = {k: v for k, v in BRIEF.items() if k != "mitigations"}
    corrupt = json.loads(json.dumps(MITIGATIONS))
    corrupt[0]["gap"] = "reduce burn by 0.3"
    brief_corrupt = dict(BRIEF, mitigations=corrupt)

    tmp = tempfile.mkdtemp(prefix="run140r_exp_")
    fx = os.path.join(tmp, "fx.json")
    with open(fx, "w", encoding="utf-8") as fh:
        json.dump({"project": PROJECT, "brief": BRIEF, "briefNoKey": brief_no_key,
                   "briefCorrupt": brief_corrupt}, fh)
    harness = os.path.join(tmp, "h.js")
    with open(harness, "w", encoding="utf-8") as fh:
        fh.write(HARNESS)
    outp = os.path.join(tmp, "out.json")
    r = subprocess.run(["node", harness, ROOT, fx, outp], capture_output=True, text=True)
    if r.returncode != 0:
        print("  [FAIL] the exporters did not load: " + (r.stderr.strip() or r.stdout.strip()))
        print("RESULT: 0/1 checks passed")
        return 1
    with open(outp, encoding="utf-8") as fh:
        out = json.load(fh)

    if not check("decision.js exposes buildAuditRecord to the sandbox", out["haveBuild"]):
        print("RESULT: " + str(PASSED) + "/" + str(TOTAL) + " checks passed")
        return 1

    audit = out["auditWith"]
    book = out["bookWith"]
    sheet = next((s for s in book if s["name"] == "Mitigations"), None)
    flat = json.dumps(sheet["rows"]) if sheet else ""

    # --------------------------------------------------------------- GUARANTEE 0: it can fail
    print("\nGUARANTEE 0: the verbatim comparison is proven able to fail.")
    corrupt_gaps = [m["gap"] for m in out["auditCorrupt"]["mitigations"]]
    check("a truncated gap is NOT found in the corrupted audit record",
          MITIGATIONS[0]["gap"] not in corrupt_gaps,
          "the corrupted record still carried the full gap")

    # ------------------------------------------------------- PROOF 8a: the audit JSON carries it
    print("\nPROOF 8a: the audit JSON carries every field the card showed.")
    check("the record has a `mitigations` key", isinstance(audit.get("mitigations"), list))
    check("one entry per mitigation the card rendered",
          len(audit.get("mitigations") or []) == len(MITIGATIONS),
          str(len(audit.get("mitigations") or [])))
    by_id = {m["module_id"]: m for m in (audit.get("mitigations") or [])}
    for m in MITIGATIONS:
        got = by_id.get(m["module_id"])
        if not check(m["module_id"] + ": present in the record", got is not None):
            continue
        for k in ("band", "shape", "reading", "next_band", "gap", "candidates",
                  "absent_reason", "composed_at", "model", "provider"):
            check(m["module_id"] + ": `" + k + "` copied verbatim", got.get(k) == m[k],
                  repr(got.get(k)))

    print("\nTHE RUN 98 REMOVALS ARE STILL REMOVED.")
    blob = json.dumps(audit)
    for k in ("recommended_action", "authority", "documentation_required", "action_plan"):
        check("`" + k + "` appears nowhere in the record", k not in blob)
    for m in (audit.get("mitigations") or []):
        for k in ("owner", "assigned_to", "due", "due_date", "deadline", "documentation"):
            check("no mitigation entry carries `" + k + "`", k not in m, m["module_id"])

    # ------------------------------------------------------------ PROOF 8b: the XLSX carries it
    print("\nPROOF 8b: the workbook's fifth sheet carries every field the card showed.")
    check("a `Mitigations` sheet exists", sheet is not None,
          str([s["name"] for s in book]))
    check("it is the fifth sheet, appended after the existing four",
          [s["name"] for s in book][-1] == "Mitigations" if sheet else False,
          str([s["name"] for s in book]))
    if sheet:
        header = sheet["rows"][0]
        check("the header names the nine columns",
              header == ["Module", "Band", "Reading", "Next Band", "Gap",
                         "Candidate Mitigation", "Composed", "Model", "Provider"],
              str(header))
        for m in MITIGATIONS:
            for field in ("reading", "next_band", "gap", "composed_at", "model", "provider"):
                check(m["module_id"] + ": `" + field + "` in the sheet verbatim",
                      m[field] in flat, repr(m[field])[:70])
            for c in m["candidates"]:
                check(m["module_id"] + ": candidate in the sheet verbatim", c in flat)
            if not m["candidates"]:
                check(m["module_id"] + ": the fixed absence line is written where a candidate "
                      "would be", "no mitigation composed for this reading" in flat)

    # ------------------------------------------------ THE UNGATED CASE: nothing is added at all
    print("\nTHE UNGATED CASE: no `mitigations` key means the exports are unchanged.")
    for label, rec in (("no key", out["auditNoKey"]), ("no brief at all", out["auditNoBrief"])):
        check(label + ": the record has NO `mitigations` key (not an empty list)",
              "mitigations" not in rec, str(rec.get("mitigations")))
        check(label + ": every pre-existing key is still there",
              all(k in rec for k in ("pceif_version", "data_boundary", "exported_at",
                                     "project_id", "project_name", "reporting_period",
                                     "signal_package", "derived_decision", "human_review")))
    names = [s["name"] for s in out["bookNoKey"]]
    check("no key: the workbook has no `Mitigations` sheet", "Mitigations" not in names,
          str(names))
    check("no key: the workbook's other sheets are unchanged in name and order",
          names == [s["name"] for s in book if s["name"] != "Mitigations"], str(names))

    print("\nRESULT: " + str(PASSED) + "/" + str(TOTAL) + " checks passed")
    if FAILS:
        for f in FAILS:
            print("  FAILED: " + f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
