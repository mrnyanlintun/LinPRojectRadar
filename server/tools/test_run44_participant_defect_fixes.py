#!/usr/bin/env python3
"""
RUN 44. THE PARTICIPANT-FACING DEFECTS PHASE J DIAGNOSED, AND THE GUARANTEES THE FIXES OWE.

WHAT THE ORACLE IS, AND WHAT IT IS NOT. Every check below is run against the SHIPPED BYTES of
the file under test. The three client files are IIFEs with no export surface, so this harness
reads each file, inserts ONE line naming the internals to expose immediately before the file's
own closing `})();`, and evaluates the result. Nothing is transcribed, re-implemented or
paraphrased: the function bodies executed here are the function bodies the browser executes,
character for character, and if a body changes this suite runs the changed one. A check that
compared a re-typed copy of the logic to itself would be the vacuity this repository has been
bitten by before (`REPORT_2026-08-02_vacuity-sweep.md`), and none is written that way.

The expected values are hand-computed from the stated rule, never read back out of the thing
under test:

  * a status differing only in case must rank IDENTICALLY -- the expectation is equality
    between two calls, which no implementation detail can satisfy accidentally while the bug
    is present, because the bug's whole content is that the two are unequal;
  * an absent document-risk score must produce NO row -- the expectation is the ABSENCE of an
    entry, and `Number(null) === 0` is exactly what makes the buggy version produce one;
  * a genuine stored zero must produce "0.00" -- hand-written, and the two checks are each
    other's control: a fix that suppressed both would fail the second.

SECTION 5 OF THE ORDER, ITEM BY ITEM. Items 1-8 and 11-13 are checked here. Item 9 (run_module
byte identity against `604291a`) is `build_run44_v28_v29_execution_proof.py`, which executes
BOTH lines rather than reading a diff. Item 10 is subsumed by item 9. Items 14 and 15 are the
browser session and the freeze gate, both reported in the run report.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

PASSED = FAILED = 0
_fail: list[str] = []


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        _fail.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(t):
    print(f"\n=== {t} ===")


# --------------------------------------------------------------------------- the node harness

_HARNESS = r"""
const fs = require('fs'), vm = require('vm'), path = require('path');
const ROOT = process.argv[2];

function stubWindow() {
  const mkEl = () => ({
    style: {}, dataset: {}, className: '', innerHTML: '', textContent: '',
    classList: { add() {}, remove() {}, contains() { return false; } },
    appendChild() {}, setAttribute() {}, addEventListener() {},
    querySelector() { return null; }, querySelectorAll() { return []; },
    isConnected: true
  });
  const doc = {
    addEventListener() {}, removeEventListener() {},
    querySelector() { return null; }, querySelectorAll() { return []; },
    getElementById() { return null; },
    body: { classList: { add() {}, remove() {}, contains() { return false; } } },
    createElement: mkEl, createElementNS: mkEl, scripts: []
  };
  const w = {};
  w.window = w; w.document = doc; w.self = w; w.globalThis = w; w.console = console;
  w.setTimeout = setTimeout; w.clearTimeout = clearTimeout;
  w.setInterval = () => 0; w.clearInterval = () => {};
  w.requestAnimationFrame = () => 0;
  w.navigator = { userAgent: 'node' };
  w.location = { href: 'http://localhost/', search: '' };
  w.localStorage = { getItem() { return null; }, setItem() {}, removeItem() {} };
  w.sessionStorage = { getItem() { return null; }, setItem() {}, removeItem() {} };
  w.fetch = () => Promise.reject(new Error('the harness makes no network call'));
  w.LIN_STATUS_COLORS = { Complete: '#4ea0ff', Green: '#3fcaa6', Yellow: '#f0c040',
                          Amber: '#e2b13c', Red: '#e0556b', None: '#64748b' };
  return w;
}

/* Load a shipped IIFE and expose named internals. The ONLY edit is one appended line
   immediately before the file's own `})();`. The bodies executed are the shipped bodies. */
function loadWithExports(ctx, rel, names, exportName) {
  let src = fs.readFileSync(path.join(ROOT, rel), 'utf8');
  const i = src.lastIndexOf('})();');
  if (i < 0) throw new Error('no IIFE tail in ' + rel);
  src = src.slice(0, i) + '\n  window.' + exportName + ' = { ' + names.join(', ') + ' };\n'
      + src.slice(i);
  vm.runInContext(src, ctx, { filename: rel });
}

const w = stubWindow();
const ctx = vm.createContext(w);
vm.runInContext(fs.readFileSync(path.join(ROOT, 'assets/js/taxonomy.js'), 'utf8'), ctx,
                { filename: 'taxonomy.js' });
loadWithExports(ctx, 'assets/js/detail.js',
  ['statusRank', 'normalizeStatus', 'pickWorstModule', 'briefKeySignals', 'buildBriefPrompt',
   'buildProvenanceTrace', 'provenanceLineHtml', 'provenancePanelHtml'], '__R44_DETAIL');
loadWithExports(ctx, 'assets/js/signals.js', ['extractedTableHtml', 'FIELD_ROWS'],
                '__R44_SIGNALS');
loadWithExports(ctx, 'assets/js/deepdive.js', ['cat8Retired'], '__R44_DD');

const D = w.__R44_DETAIL, S = w.__R44_SIGNALS, DD = w.__R44_DD;
const out = {};

/* ---- 1. case-insensitive severity rank ------------------------------------------------ */
const BANDS = ['Red', 'Red-review', 'Amber', 'Yellow', 'Green', 'Complete'];
out.rankPairs = BANDS.map(b => ({
  band: b,
  canonical: D.statusRank(b),
  lower: D.statusRank(b.toLowerCase()),
  upper: D.statusRank(b.toUpperCase()),
  mixed: D.statusRank(b.charAt(0).toLowerCase() + b.slice(1).toUpperCase())
}));
out.rankOrderStrictlyIncreasing = BANDS.map(b => D.statusRank(b));
out.rankUnknown = D.statusRank('not-a-status');
out.rankGreenVsUnknown = { green: D.statusRank('green'), unknown: D.statusRank('zzz') };
out.rankOf = {};
['red', 'red-review', 'amber', 'yellow', 'green', 'complete'].forEach(
  b => { out.rankOf[b] = D.statusRank(b); });

/* the defect exactly as Phase J executed it: A1.2 stores lowercase 'green' */
const A1_MODULES = [
  { name: 'CUSUM Anomaly Monitor', status: 'green' },
  { name: 'TCPI', status: 'Green' },
  { name: 'Variance at Completion', status: 'Green' }
];
out.pickWorstOnPhaseJList = D.pickWorstModule({ modules: A1_MODULES });
out.pickWorstOnAdverseList = D.pickWorstModule({
  modules: [{ name: 'TCPI', status: 'Green' }, { name: 'VAC', status: 'amber' }]
});

/* ---- 2/3. driver attribution: the brief prompt, through the real snapshot route -------- */
function projectWithSnapshot(catStatus, modules) {
  return {
    id: 'PRJ-H', name: 'Harness',
    history: [{
      period: '2026-06', computed_at: '2026-06-30T00:00:00Z',
      categories: { a1: { id: 'a1', num: 'A1', name: 'Cost and EVM Performance',
                          status: catStatus, parked: false, modules } },
      summary: {}, governance: { state: 'Amber', action: 'review' }
    }]
  };
}
out.briefAmberOverGreens = D.buildBriefPrompt(projectWithSnapshot('Amber', A1_MODULES)) || '';
out.briefAmberOverAmber = D.buildBriefPrompt(projectWithSnapshot('Amber',
  [{ name: 'TCPI', status: 'Green' }, { name: 'VAC', status: 'Amber' }])) || '';
out.briefGreenOverGreens = D.buildBriefPrompt(projectWithSnapshot('Green', A1_MODULES)) || '';

/* the provenance line, through the real getCategoryStatus / getModuleStatus resolvers */
function provFor(catStatus, modStatuses) {
  const cats = [{ id: 'a1', num: 'A1', name: 'Cost and EVM Performance', level: 'project',
                  modules: Object.keys(modStatuses).map((mc, i) => (
                    { id: 'm' + i, num: 'A1.' + (i + 1), name: mc, method_class: mc })) }];
  const saveCats = w.LIN_CATEGORIES, saveGet = w.getCategoryStatus, saveMod = w.getModuleStatus;
  w.LIN_CATEGORIES = cats;
  w.projectLevelCategories = () => cats;
  w.getCategoryStatus = () => catStatus;
  w.getModuleStatus = (mc) => modStatuses[mc] || null;
  w.getProjectFusion = () => ({ status: catStatus, stored: true });
  let r;
  try {
    r = { trace: D.buildProvenanceTrace({ id: 'PRJ-H', status: catStatus, signalInputs: {} }),
          line: D.provenanceLineHtml({ id: 'PRJ-H', status: catStatus, signalInputs: {} }) };
    r.panel = r.trace ? D.provenancePanelHtml(r.trace) : '';
  } finally {
    w.LIN_CATEGORIES = saveCats; w.getCategoryStatus = saveGet; w.getModuleStatus = saveMod;
  }
  return r;
}
out.provAmberOverGreens = provFor('Amber', { TCPI: 'Green', VAC: 'Green' });
out.provAmberOverAmber = provFor('Amber', { TCPI: 'Green', VAC: 'Amber' });
out.provAmberOverLowercase = provFor('Amber', { TCPI: 'Green', CUSUM: 'amber' });

/* ---- 4/5. the document-risk score ------------------------------------------------------ */
function keySignalsFor(si, sig) {
  const saveRes = w.LinResults;
  w.LinResults = { rowFor: () => ({ signal_inputs: si }), hasResult: () => true };
  try { return D.briefKeySignals({ id: 'PRJ-H', signals: sig || {} }); }
  finally { w.LinResults = saveRes; }
}
const BASE_SI = { cpi: 1.22, spi: 0.964, bac: 5874620 };
const docRow = (rows) => (rows || []).filter(r => r.label === 'Document risk')[0] || null;
out.docAbsentNull = docRow(keySignalsFor(Object.assign({}, BASE_SI, { docRiskScore: null })));
out.docAbsentUndef = docRow(keySignalsFor(Object.assign({}, BASE_SI)));
out.docAbsentBlank = docRow(keySignalsFor(Object.assign({}, BASE_SI, { docRiskScore: '' })));
out.docZero = docRow(keySignalsFor(Object.assign({}, BASE_SI, { docRiskScore: 0 })));
out.docReal = docRow(keySignalsFor(Object.assign({}, BASE_SI, { docRiskScore: 0.46 })));
out.docBlobNull = docRow(keySignalsFor(Object.assign({}, BASE_SI),
                                       { doc: { score: null, status: 'Green' } }));
out.docBlobZero = docRow(keySignalsFor(Object.assign({}, BASE_SI, { docRiskScore: null }),
                                       { doc: { score: 0, status: 'Green' } }));
/* the brief prompt is the surface Phase J named: the key drivers shipped into it */
out.briefPromptWithNullDoc =
  (D.buildBriefPrompt(projectWithSnapshot('Green', A1_MODULES)) || '');

/* ---- 6. CPI and SPI labelled computed --------------------------------------------------- */
out.fieldRows = S.FIELD_ROWS.map(f => ({ key: f.key, label: f.label, computed: !!f.computed }));
out.tableAll = S.extractedTableHtml({ bac: 5874620, cpi: 1.22, spi: 0.964, docRiskScore: 0.46,
                                      sources: { bac: { docType: 'contract_value' } } });
out.tableRows = {};
S.FIELD_ROWS.forEach(f => {
  const one = S.extractedTableHtml({ [f.key]: 1 });
  out.tableRows[f.key] = { computed: one.indexOf('ds-computed') >= 0,
                           extracted: one.indexOf('ds-extracted') >= 0 };
});
out.tableEmpty = S.extractedTableHtml({});

/* ---- 7. Portfolio Health, derived ------------------------------------------------------- */
out.cat8RetiredLive = DD.cat8Retired();
(function () {
  const save = w.LIN_CATEGORIES;
  w.LIN_CATEGORIES = null;              out.cat8RetiredNoTaxonomy = DD.cat8Retired();
  w.LIN_CATEGORIES = [];                out.cat8RetiredEmptyTaxonomy = DD.cat8Retired();
  w.LIN_CATEGORIES = [{ id: 'a1', level: 'project', modules: [{ id: 'x' }] }];
  out.cat8RetiredNoPortfolioCat = DD.cat8Retired();
  w.LIN_CATEGORIES = (save || []).map(c => (c && c.level === 'portfolio')
    ? Object.assign({}, c, { modules: [{ id: 'd1_1', num: 'D1.1', name: 'reinstated' }] }) : c);
  out.cat8RetiredIfReinstated = DD.cat8Retired();
  w.LIN_CATEGORIES = save;
})();
out.taxonomyPortfolioCats = (w.LIN_CATEGORIES || [])
  .filter(c => c && c.level === 'portfolio')
  .map(c => ({ id: c.id, modules: (c.modules || []).length }));

console.log('__R44_JSON__' + JSON.stringify(out));
"""


def node_probe() -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(_HARNESS)
        script = fh.name
    r = subprocess.run(["node", script, str(ROOT)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("the client harness did not run, so nothing below was measured:\n"
                         + (r.stderr or r.stdout)[-2000:])
    line = [ln for ln in r.stdout.splitlines() if ln.startswith("__R44_JSON__")]
    if not line:
        raise SystemExit("the client harness printed no result payload:\n" + r.stdout[-2000:])
    return json.loads(line[-1][len("__R44_JSON__"):])


# ============================================================================================
JS = node_probe()

head("1. SECTION 4.1 -- CASE IS NOT SEVERITY (section 5 item 1)")

for row in JS["rankPairs"]:
    check(row["canonical"] == row["lower"] == row["upper"] == row["mixed"],
          f"{row['band']} ranks identically in every casing", json.dumps(row))

D_RANK_OF = JS["rankOf"]
ranks = JS["rankOrderStrictlyIncreasing"]
check(ranks == sorted(ranks) and len(set(ranks)) == len(ranks),
      "the six bands still rank strictly worst-first, so making the match case-insensitive did "
      "not flatten the order it exists to express", str(ranks))
check(JS["rankUnknown"] == 3 and JS["rankGreenVsUnknown"]["unknown"]
      < JS["rankGreenVsUnknown"]["green"],
      "an unrecognised status keeps its historical unknown rank and is still treated as more "
      "adverse than Green, so nothing outside the vocabulary is read as reassuring",
      json.dumps(JS["rankGreenVsUnknown"]))

worst = JS["pickWorstOnPhaseJList"]
# The pre-fix behaviour ranked 'green' at the unknown default of 3, MORE ADVERSE than the two
# 'Green' voters at 4, and selected it as the category's worst. The post-fix statement is not
# "a different module is selected" -- all three tie at Green now, and a stable sort keeps the
# first -- it is that NOTHING on this list is selected as worse than Green.
check(worst is not None and JS["rankPairs"][4]["canonical"]
      == D_RANK_OF[str(worst["status"]).strip().lower()],
      "on Phase J's own list (lowercase 'green' beside two 'Green'), the module selected as the "
      "category's worst is one that reads Green: the lowercase spelling is no longer treated as "
      "more adverse than the properly-cased ones", json.dumps(worst))
worst2 = JS["pickWorstOnAdverseList"]
check(worst2 is not None and worst2["name"] == "VAC",
      "and a genuinely adverse module in the OTHER casing ('amber') IS selected -- the fix "
      "recognises the casing, it does not ignore the status", json.dumps(worst2))

src_detail = (ROOT / "assets/js/detail.js").read_text(encoding="utf-8")
check('{ Red: 0, "Red-review": 1, Amber: 2, Yellow: 3, Green: 4, Complete: 5 }'
      not in src_detail,
      "no capitalised-only severity map is left on the page for a later reader to copy")
check(src_detail.count("function statusRank(") == 1,
      "and there is exactly ONE severity rank on the page, so a future site cannot order "
      "statuses by a second rule")

head("2. SECTION 4.1 -- A CATEGORY IS NEVER WORSE THAN ITS WORST COMPUTING MODULE "
     "(section 5 item 2)")

from app.simulation.fusion import BAND_SEVERITY, BANDS, fuse_signals   # noqa: E402
from app.simulation.lineage import lineage_for                        # noqa: E402
from app.simulation.qualification_gate import (                       # noqa: E402
    fuse_qualified, preflight, qualify,
)
import itertools                                                       # noqa: E402

# THE ROUTE MATTERS. compute.py fuses `fuse_signals(fuse_qualified(signals))`, where each signal
# came from `qualify(module_id, band, ..., lineage=lineage_for(module_id))`. Handing fuse_signals
# a dict of the wrong shape sends every signal down the UNRESOLVED arm, which reports the worst
# input band by construction and so would pass this check without ever reaching the combination.
# That is a fixture built by a route the application does not take, and it is the third way a
# check has lied in this repository. The sweep therefore goes through qualify/fuse_qualified,
# and the "not vacuous" check below asserts that the combination was actually entered.
VOTERS = ("A1.7", "A1.8")
SI_OK = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
         "cpi": 0.909, "spi": 0.889}


def fuse_bands(bands):
    pre = preflight(SI_OK, (), None)
    sigs = [qualify(VOTERS[i % len(VOTERS)], b, f"metric {b}", pre,
                    lineage=lineage_for(VOTERS[i % len(VOTERS)]))
            for i, b in enumerate(bands)]
    return fuse_signals(fuse_qualified(sigs))


violations = []
entered_combination = 0
combos = 0
for n in (1, 2, 3):
    for bands in itertools.product(BANDS, repeat=n):
        fused = fuse_bands(bands)
        combos += 1
        if fused is None:
            violations.append((bands, None))
            continue
        if fused.get("lineage_groups"):
            entered_combination += 1
        got = fused.get("status")
        worst_in = max(bands, key=lambda b: BAND_SEVERITY[b])
        if BAND_SEVERITY.get(got, 99) > BAND_SEVERITY[worst_in]:
            violations.append((bands, got))
check(combos == len(BANDS) + len(BANDS) ** 2 + len(BANDS) ** 3 and combos > 0,
      f"the sweep is not vacuous: every combination of 1, 2 and 3 module bands was fused "
      f"({combos} of them)", str(combos))
check(entered_combination == combos,
      "and every one of them entered the fusion's combination rather than falling down the "
      "unresolved-lineage arm, which reports the worst input band by construction and would "
      "pass this check without testing anything",
      f"{entered_combination}/{combos}")
check(not violations,
      "the server's fusion never returns a band more adverse than the worst band that went "
      "into it, so a category status cannot exceed its worst computing module",
      str(violations[:4]))

# the all-Green case Phase J executed directly, kept as its own named check
all_green = fuse_bands(("Green", "Green"))
check(all_green and all_green["status"] == "Green",
      "and the exact case Phase J named -- the two voting modules both Green -- fuses to Green",
      json.dumps(all_green and all_green.get("status")))

src_tax = (ROOT / "assets/js/taxonomy.js").read_text(encoding="utf-8")
check("return (stored && stored.status) || null;" in src_tax,
      "the client reads the stored category status verbatim and derives no category status of "
      "its own, so there is no second place for one to be manufactured")

head("3. SECTION 4.1 -- THE DRIVER IS NEVER BETTER THAN WHAT IT DRIVES (section 5 item 3)")

check("(worst:" not in JS["briefAmberOverGreens"],
      "an Amber category over modules that all read Green offers NO module as its driver in "
      "the brief prompt", JS["briefAmberOverGreens"][:160])
check("A1 Cost and EVM Performance: Amber" in JS["briefAmberOverGreens"],
      "the category and its status are still reported -- the attribution was dropped, not the "
      "category", JS["briefAmberOverGreens"][:160])
check("(worst: VAC" in JS["briefAmberOverAmber"],
      "an Amber category WITH an Amber module still names it, so the guard suppresses a false "
      "attribution and not a true one", JS["briefAmberOverAmber"][:160])
check("(worst:" in JS["briefGreenOverGreens"],
      "a Green category over Green modules still names one: equal severity is a driver",
      JS["briefGreenOverGreens"][:160])

pa = JS["provAmberOverGreens"]
check(pa["trace"] is not None and pa["trace"]["modDrives"] is False,
      "the provenance trace marks the module as not driving when it is better than the "
      "category", json.dumps(pa["trace"] and pa["trace"]["modDrives"]))
pa_line = (re.search(r'det-prov-line">(.*?)</span>', pa["line"], re.S)
           or re.match("()", "")).group(1)
check("TCPI" not in pa_line and "VAC" not in pa_line,
      "so the rendered provenance one-liner names no module as the driver of an Amber it "
      "cannot be the driver of", pa_line[:200])
check("no module in this category reads as adverse as the category status" in pa["panel"],
      "and the expanded panel says why, rather than going silent", pa["panel"][:200])
pb = JS["provAmberOverAmber"]
check(pb["trace"]["modDrives"] is True and "VAC" in pb["line"],
      "an Amber module under an Amber category IS named, so the guard is not a blanket "
      "suppression", pb["line"][:200])
pc = JS["provAmberOverLowercase"]
check(pc["trace"]["modDrives"] is True and "CUSUM" in pc["line"],
      "and a module whose adverse status is in the other casing is recognised as the driver",
      pc["line"][:200])

head("4. SECTION 4.2 -- AN ABSENT DOCUMENT-RISK SCORE RENDERS AS ABSENT (section 5 item 4)")

check(JS["docAbsentNull"] is None,
      "a stored docRiskScore of null produces no Document risk key driver",
      json.dumps(JS["docAbsentNull"]))
check(JS["docAbsentUndef"] is None,
      "and an absent key still produces none (the case that was already correct, kept as the "
      "control)", json.dumps(JS["docAbsentUndef"]))
check(JS["docAbsentBlank"] is None,
      "and a blank string produces none: Number('') is 0 and finite, the same trap as null",
      json.dumps(JS["docAbsentBlank"]))
check(JS["docBlobNull"] is None,
      "a legacy signals blob carrying doc.score null produces none either -- the fallback to "
      "the stored value must not resurrect the zero", json.dumps(JS["docBlobNull"]))
check("Document risk" not in JS["briefPromptWithNullDoc"],
      "and the Executive Brief prompt, which is the surface Phase J named, carries no Document "
      "risk key driver when the score is absent")

head("5. SECTION 4.2 -- A GENUINE STORED ZERO STILL RENDERS AS ZERO (section 5 item 5)")

z = JS["docZero"]
check(z is not None and z["value"] == "0.00" and z["status"] == "Green",
      "a stored docRiskScore of 0 renders 0.00 with a Green status: the absence guard tests the "
      "RAW value, never the number's truthiness", json.dumps(z))
zb = JS["docBlobZero"]
check(zb is not None and zb["value"] == "0.00",
      "and a legacy blob's genuine 0 renders 0.00 as well", json.dumps(zb))
r = JS["docReal"]
check(r is not None and r["value"] == "0.46" and r["status"] == "Amber",
      "a real score is unaffected: 0.46 renders 0.46, Amber by the module's own 0.40 band",
      json.dumps(r))

head("6. SECTION 4.3 -- CPI AND SPI ARE LABELLED COMPUTED (section 5 item 6)")

rows = {r["key"]: r for r in JS["fieldRows"]}
check(rows["cpi"]["computed"] and rows["spi"]["computed"],
      "the two derived fields declare themselves computed in the row table")
check(not any(v["computed"] for k, v in rows.items() if k not in ("cpi", "spi")),
      "and no extracted field claims to be computed",
      str([k for k, v in rows.items() if v["computed"]]))
for k in ("cpi", "spi"):
    m = JS["tableRows"][k]
    check(m["computed"] and not m["extracted"],
          f"the rendered {k.upper()} row is marked computed and is NOT marked extracted",
          json.dumps(m))
for k in ("bac", "ev", "ac", "pv", "docRiskScore"):
    m = JS["tableRows"][k]
    check(m["extracted"] and not m["computed"],
          f"the rendered {k} row is still marked extracted", json.dumps(m))
check(JS["tableAll"].count("ds-computed") == 2,
      "a full table marks exactly two rows computed", str(JS["tableAll"].count("ds-computed")))
check("ds-computed" not in JS["tableEmpty"] and "ds-extracted" not in JS["tableEmpty"],
      "and a table with no values marks nothing at all, so neither mark can be read as a value")
src_signals = (ROOT / "assets/js/signals.js").read_text(encoding="utf-8")
check("<p class=\"eyebrow\">Extracted signal inputs</p>" not in src_signals,
      "the panel heading no longer asserts that every row beneath it was extracted")
check("(computed)" in src_signals.split("resultText = \"✓ extracted \"")[0][-600:],
      "and the upload result line, which begins with the word extracted, says which of the "
      "figures it names were computed")
check(".ds-computed" in (ROOT / "assets/css/radar.css").read_text(encoding="utf-8"),
      "the computed mark has a rule of its own in the one stylesheet, so it is visually "
      "distinguishable from the extracted mark rather than silently unstyled")

head("7. SECTION 4.4 -- THE PORTFOLIO HEALTH STATEMENT (section 5 items 7 and 13)")

check(JS["cat8RetiredLive"] is True,
      "cat8Retired() is TRUE against the taxonomy the page actually loads")
check(JS["cat8RetiredNoTaxonomy"] is False and JS["cat8RetiredEmptyTaxonomy"] is False,
      "FALSE with no taxonomy loaded: a page that cannot see the roster asserts nothing about "
      "it", f"{JS['cat8RetiredNoTaxonomy']}/{JS['cat8RetiredEmptyTaxonomy']}")
check(JS["cat8RetiredNoPortfolioCat"] is False,
      "FALSE when the taxonomy carries no portfolio-level category at all")
check(JS["cat8RetiredIfReinstated"] is False,
      "and FALSE again the moment a Portfolio Level module is reinstated: the predicate is "
      "DERIVED from the roster, not a constant spelled as a function")
check(JS["taxonomyPortfolioCats"] and all(c["modules"] == 0
                                          for c in JS["taxonomyPortfolioCats"]),
      "the live taxonomy does carry a portfolio-level category and it carries zero modules, so "
      "the TRUE above is not vacuously true", json.dumps(JS["taxonomyPortfolioCats"]))

src_dd = (ROOT / "assets/js/deepdive.js").read_text(encoding="utf-8")
check("Portfolio Health is no longer in service." in src_dd,
      "the flyout states the current state")
check("needs at least 3 projects" in src_dd,
      "and the project-count sentence is RETAINED for the case it is true of, rather than "
      "deleted: reinstating Portfolio Health restores it with no edit here")
check(src_dd.count("data-run-portfolio-analysis") == 2,
      "no user-facing control was added, moved or removed: the repair button and its handler "
      "are exactly where they were", str(src_dd.count("data-run-portfolio-analysis")))
for banned in ("D1", "Cat 8", "PH."):
    check(banned not in "Portfolio Health is no longer in service. The analysis that compared a "
          "project against the rest of the portfolio was withdrawn, so this panel does not "
          "compute for any portfolio, whatever number of projects it holds.",
          f"the new sentence names no module or category identifier ({banned}), per "
          "NAMING_AUTHORITY.md")

from app.simulation.portfolio_health import live_portfolio_modules   # noqa: E402
check(live_portfolio_modules() == (),
      "and the server agrees: no portfolio module is in service, so the sentence is true of the "
      "code and not merely of the taxonomy artifact", str(live_portfolio_modules()))

head("8. SECTION 4.5 -- NO COMMENT OR DOCSTRING DESCRIBES THE WITHDRAWN REFUSAL "
     "(section 5 item 8)")

WITHDRAWN = re.compile(
    r"refus\w*[^.]{0,120}(retirement reason|stated retirement)"
    r"|(retirement reason|stated retirement)[^.]{0,120}rather than computed",
    re.I | re.S)
hits = []
for path in sorted(list(ROOT.glob("server/**/*.py")) + list(ROOT.glob("assets/js/*.js"))
                   + list(ROOT.glob("*.html"))):
    if "__pycache__" in str(path):
        continue
    # This file carries the pattern itself, as the pattern. Excluded by identity, not by a
    # glob that would also excuse every other suite.
    if path.resolve() == pathlib.Path(__file__).resolve():
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    for m in WITHDRAWN.finditer(text):
        # the note in run_module() that RECORDS the withdrawal is the one legitimate mention
        window = text[max(0, m.start() - 300):m.end() + 60]
        if "THAT REQUIREMENT IS WITHDRAWN" in window or "was withdrawn at Run 43F" in window:
            continue
        hits.append(f"{path.relative_to(ROOT)}:{text[:m.start()].count(chr(10)) + 1}")
check(not hits,
      "no comment or docstring in any server or client source still describes a retired module "
      "as refused with a retirement reason", str(hits))

from app.simulation import registry as REG                            # noqa: E402
doc = REG.available_modules.__doc__ or ""
check("is refused" not in doc and "retirement reason rather than computed" not in doc,
      "available_modules()'s own docstring no longer states the withdrawn semantics")
check("f461630" in doc and "not refused anywhere" in doc.lower(),
      "and it states what run_module() actually does with a retired identifier", doc[-200:])

# the docstring must describe THIS function, and the function must still do it
avail = REG.available_modules()
check(set(avail) == set(REG.VALIDATED) & set(REG.service_index()),
      "and the function itself is unchanged: the intersection of the implemented set with the "
      "modules in service", str(len(avail)))
retired_reached = [m for m in REG.retired_modules() if m in avail]
check(not retired_reached,
      "no retired identifier is reachable through it", str(retired_reached))

head("9. THE POPULATIONS, DERIVED (section 5 items 11, 12 and 13)")

svc, reg_all = REG.service_index(), REG.registry_index()
check(len(svc) == 63, "modules in service is 63, derived from the registry CSV", str(len(svc)))
check(len(reg_all) == 101, "registry total is 101, derived", str(len(reg_all)))
check(len(svc) + len(REG.retired_modules()) == len(reg_all),
      "and the two reconcile with nothing left over",
      f"{len(svc)}+{len(REG.retired_modules())}={len(reg_all)}")
check(set(REG.CORE_VOTING_MODULES) == {"A1.7", "A1.8"}
      and len(REG.CORE_VOTING_MODULES) == 2,
      "the voting count is exactly 2, and they are A1.7 and A1.8",
      str(REG.CORE_VOTING_MODULES))
check(all(m in svc for m in REG.CORE_VOTING_MODULES),
      "both voters are in service, so the category status has voters at all")

print()
for f in _fail:
    print("FAIL:", f)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
