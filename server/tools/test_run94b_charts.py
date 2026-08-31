#!/usr/bin/env python3
"""
RUN 94b. THE PALETTE IS GENERATED, THE COLUMN IS DERIVED, AND THE POPULATION IS THE REGISTRY'S.

WHAT THIS SUITE CAN AND CANNOT PROVE. It runs the SHIPPED generator -- the real bytes of
`assets/js/config.js`, evaluated in node -- against the REAL roster read from
`registry.service_index()`, and asserts on the colours it actually returns. It does NOT render
a browser: the drawn-geometry measurements (no truncated label, the module column clearing the
category column, 0 overlapping label pairs, 42 moons each carrying a distinct identity colour)
are made by `drive_run94_charts.py` in Chromium at 1280px and 1024px in four storable themes
plus the archived one, and the report cites that log. A check here that asserted "the string
trunc does not appear" would be worthless, so no check here does that.
"""
from __future__ import annotations
import json, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
from app.simulation import registry  # noqa: E402

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {name}")
    else:    FAIL += 1; print(f"  FAIL  {name}  {detail}")

SIX = ("A1", "A2", "A3", "A4", "A5", "A6")
si = registry.service_index()
in_service = {k: v for k, v in si.items() if v["category"] in SIX}
ORDER = [k for k in si if k in in_service]

NODE = """
global.window = global; global.document = { body: null, documentElement: null };
global.getComputedStyle = () => ({ getPropertyValue: () => '' });
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const at = src.indexOf('RUN 94b. IDENTITY COLOURS');
if (at < 0) { console.log(JSON.stringify({ error: 'generator block not found in config.js' })); process.exit(0); }
eval(src.slice(src.lastIndexOf('/* ====', at)));
window.LIN_STATUS_COLORS = JSON.parse(process.argv[4]);
const keys = JSON.parse(process.argv[3]);
const p = window.LIN_IDENTITY_PALETTE(keys, 'module');
console.log(JSON.stringify({ list: p.list, formula: p.formula,
  minAdjacentDeltaE: p.minAdjacentDeltaE, minAnyDeltaE: p.minAnyDeltaE,
  minBandDeltaE: p.minBandDeltaE, minBandPair: p.minBandPair, bandMinRequired: p.bandMinRequired }));
"""

# The band colours as the light default theme resolves them, read from radar.css rather than
# typed here, so a theme edit moves this input instead of being contradicted by it.
CSS = (ROOT / "assets" / "css" / "radar.css").read_text(encoding="utf-8")
import re
def cssvar(name, default):
    m = re.search(r"--" + name + r"\s*:\s*([^;]+);", CSS)
    return m.group(1).strip() if m else default
BANDS = {
    "Complete": cssvar("status-complete", "#4ea0ff"),
    "Green":    cssvar("status-green", "#2ee66b"),
    "Yellow":   cssvar("status-yellow", "#ffe066"),
    "Amber":    cssvar("status-amber", "#ff8c1a"),
    "Red":      cssvar("status-red", "#ff3b30"),
    "None":     cssvar("status-nodata", "#26344f"),
    "NotRelevant": cssvar("status-notrelevant-text", "#5b3dd6"),
}

print("=" * 96)
print("RUN 94b -- identity palette, generated from the registry roster")
print("=" * 96)
print(f"  roster: {len(in_service)} modules in service in {', '.join(SIX)}; band inputs {BANDS}")

with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
    f.write(NODE); script = f.name
out = subprocess.run(["node", script, str(ROOT / "assets" / "js" / "config.js"),
                      json.dumps(ORDER), json.dumps(BANDS)],
                     capture_output=True, text=True)
data = json.loads(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else {"error": out.stderr[:400]}
check("the generator in config.js runs and returns a palette", "error" not in data, str(data)[:300])
if "error" in data:
    print(f"RESULT: {PASS}/{PASS+FAIL} checks passed"); sys.exit(1)

lst = data["list"]
check("one colour per module in service, none missing",
      len(lst) == len(ORDER) and all(o["hex"] for o in lst), f"{len(lst)} vs {len(ORDER)}")
check("every module's colour is its own (no two identical)",
      len({o["hex"] for o in lst}) == len(lst),
      f"{len({o['hex'] for o in lst})} distinct of {len(lst)}")
check("the colour difference measure is named and is CIE76 in CIE L*a*b*",
      data["formula"] == "CIE76 dE*ab (CIE L*a*b*, D65)", data["formula"])
check("no identity colour is confusable with a band colour (dE*ab >= 25)",
      data["minBandDeltaE"] >= data["bandMinRequired"],
      f"min {data['minBandDeltaE']:.2f} at {data['minBandPair']}")
check("adjacent modules are distinguishable (dE*ab >= 20 between drawn neighbours)",
      data["minAdjacentDeltaE"] >= 20, f"min {data['minAdjacentDeltaE']:.2f}")
print(f"  MEASURED  smallest dE*ab between ADJACENT module colours: {data['minAdjacentDeltaE']:.2f}")
print(f"  MEASURED  smallest dE*ab between ANY TWO module colours:  {data['minAnyDeltaE']:.2f}")
print(f"  MEASURED  smallest dE*ab between a module and a band:     {data['minBandDeltaE']:.2f} "
      f"{data['minBandPair']}")

# THE POPULATION IS THE REGISTRY'S, AND THE OWNER'S FIFTEEN ARE IN IT.
OWNER_RETIRED = ["Bayesian EAC", "Kalman Filter SPI Smoother", "CPI Shrinkage Forecast",
                 "Line of Balance", "CCPM Buffer Health", "Reference Class Forecasting",
                 "Analogous Estimating Ratio", "Inflation Adjustment Index",
                 "Document Risk Score", "Specification Conflict Density", "Sensitivity Analysis",
                 "Scenario Modeling", "Queueing Theory Bottleneck", "Agent-Based Supply Chain",
                 "Discrete Event Simulation"]
live = {v["module_name"]: k for k, v in in_service.items()}
still = [(n, live[n]) for n in OWNER_RETIRED if n in live]
print(f"  RECORDED  modules the owner reported as retired that the registry still has IN "
      f"SERVICE: {len(still)} of {len(OWNER_RETIRED)}")
for n, mid in still:
    print(f"            {mid:<6} {n}")
check("the palette is keyed on registry module ids, so a retirement removes a colour by itself",
      all(o["key"] in si for o in lst), "a key is not a registry module id")

# The palette is a PURE FUNCTION of the roster: drop a module and its colour goes with it,
# with nothing to edit by hand. This is section 4.4, proved rather than asserted.
short = ORDER[:-1]
out2 = subprocess.run(["node", script, str(ROOT / "assets" / "js" / "config.js"),
                       json.dumps(short), json.dumps(BANDS)], capture_output=True, text=True)
d2 = json.loads(out2.stdout.strip().splitlines()[-1])
check("a module leaving service needs no colour removed by hand",
      len(d2["list"]) == len(ORDER) - 1
      and {o["key"] for o in d2["list"]} == set(short),
      f"{len(d2['list'])} colours for {len(short)} modules")

print("=" * 96)
print(f"RESULT: {PASS}/{PASS+FAIL} checks passed")
sys.exit(0 if FAIL == 0 else 1)
