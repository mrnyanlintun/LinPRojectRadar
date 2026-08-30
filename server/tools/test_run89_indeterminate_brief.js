/* Run 89, goal three: THE INDETERMINATE BRIEF PASSES THE THREE RUN 70 CHECKS UNWEAKENED.
 *
 * The checks are NOT reimplemented here and NOT relaxed. `assets/js/detail.js` is loaded whole
 * and its OWN `briefGate` is called through `LinDetail.__briefForTest`, so what is measured is
 * the production gate on the production brief text.
 *
 * Proof that the harness can fail: section 4 feeds the SAME evidence a brief that asserts a
 * condition with no figure, and the same gate rejects it.
 *
 * Run (from repo root):  node server/tools/test_run89_indeterminate_brief.js
 */
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.resolve(__dirname, "..", "..");
let FAILURES = [];
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  console.log("  [" + (ok ? "PASS" : "FAIL") + "] " + label + ": got " + JSON.stringify(got)
              + ", want " + JSON.stringify(want));
  if (!ok) FAILURES.push(label);
}

/* A DOM stub thin enough that nothing is faked into working: detail.js only needs `document`
   and `window` to EXIST at load time; every function measured below is pure over its arguments. */
const el = () => ({ querySelector: () => null, querySelectorAll: () => [], addEventListener(){},
                    classList: { add(){}, remove(){} }, insertAdjacentHTML(){}, style: {},
                    setAttribute(){}, getAttribute: () => null, appendChild(){}, remove(){},
                    innerHTML: "", textContent: "", className: "", dataset: {} });
const sandbox = {
  console, JSON, Math, Date, Number, String, Object, Array, RegExp, isNaN, parseFloat, parseInt,
  setTimeout, clearTimeout, requestAnimationFrame: (f) => 0, cancelAnimationFrame(){},
  document: Object.assign(el(), { createElement: el, getElementById: () => null, body: el(),
                                  documentElement: el(), addEventListener(){} }),
  navigator: { userAgent: "node" }, location: { href: "", search: "" }, fetch: () => Promise.resolve(),
  localStorage: { getItem: () => null, setItem(){}, removeItem(){} },
};
sandbox.window = sandbox; sandbox.self = sandbox; sandbox.globalThis = sandbox;
vm.createContext(sandbox);
for (const f of ["assets/js/config.js", "assets/js/taxonomy.js", "assets/js/detail.js"]) {
  try { vm.runInContext(fs.readFileSync(path.join(ROOT, f), "utf8"), sandbox, { filename: f }); }
  catch (e) { console.log("  [load] " + f + ": " + e.message); }
}
const T = sandbox.window.LinDetail && sandbox.window.LinDetail.__briefForTest;
if (!T) { console.log("FATAL: detail.js did not load its brief pipeline"); process.exit(1); }

/* THE ROW. Built to the shape of the richest STORED row measured this run
   (computed_results 01M11XEYX5V5S6CQSCSJBHBV6T, project 507be211..., period 8): A1 Red set by
   A1.7/A1.8, A4 Red set by A4.2, A2/A3/A6 carrying modules and NO band, A5 never called. */
const ROW = {
  project_status: "Indeterminate",
  project_status_basis: {
    required_categories: ["A1", "A2", "A3", "A6"], supporting_categories: ["A4", "A5"],
    required_assessed: ["A1"], required_missing: ["A2", "A3", "A6"],
    required_missing_detail: [
      { category: "A2", state: "computed",
        missing: "the category was called and no module in it asserted a band" },
      { category: "A3", state: "computed",
        missing: "the category was called and no module in it asserted a band" },
      { category: "A6", state: "computed",
        missing: "the category was called and no module in it asserted a band" }],
    supporting_assessed: ["A4"], supporting_not_assessed: ["A5"],
    fused_band: "Red", official: false, status: "Indeterminate"
  },
  category_statuses: {
    A1: { status: "Red", status_set_by: ["A1.7", "A1.8"], contributes_to_project_status: true },
    A2: { status: null, status_set_by: [], contributes_to_project_status: true },
    A3: { status: null, status_set_by: [], contributes_to_project_status: true },
    A4: { status: "Red", status_set_by: ["A4.2"], contributes_to_project_status: true },
    A6: { status: null, status_set_by: [], contributes_to_project_status: true }
  },
  module_results: [
    { module_id: "A1.7", status_color: "Red", evidence_metric: "TCPI 1.34", value: 1.34 },
    { module_id: "A1.8", status_color: "Red", evidence_metric: "VAC -412000", value: -412000 },
    { module_id: "A2.7", status_color: null, evidence_metric: "no band", value: 0.91 },
    { module_id: "A3.2", status_color: null, evidence_metric: "no band", value: 0.4 },
    { module_id: "A4.2", status_color: "Red", evidence_metric: "document risk 0.66", value: 0.66 },
    { module_id: "A6.1", status_color: null, evidence_metric: "no band", value: 0.75 }
  ],
  abstained: [{ module_id: "A2.8" }],
  signal_inputs: { cpi: 0.82, spi: 0.91, sources: { cpi: { docType: "evm_report" } } }
};
const PROJECT = { id: "p89", name: "Run 89 fixture", signals: {} };
sandbox.window.LinResults = { rowFor: () => ROW, prime(){} };

console.log("1. THE BRIEF IS THE INDETERMINATE BRIEF");
const text = T.scriptedBrief(PROJECT);
const parsed = T.parseBrief(text);
const ev = T.briefEvidence(PROJECT);
check("the server's verdict reached the client", !!ev.statusBasis, true);
check("the recommendation leads with INDETERMINATE",
      /^INDETERMINATE/.test(String(parsed.recommendation || "")), true);
console.log("\n--- the brief as rendered ---\n" + text + "\n--- end ---\n");

console.log("2. THE FIVE THINGS THE OWNER REQUIRED, EACH MEASURED IN THE TEXT");
check("(1) states Indeterminate with insufficient evidence for an official posture",
      /insufficient evidence for an official project posture/.test(text), true);
check("(2) names EVERY required category that could not be assessed",
      ["A2", "A3", "A6"].every((k) => text.indexOf("(" + k + ") could not be assessed") >= 0), true);
check("(3) shows every assessed category and its posture, INCLUDING the Reds",
      /A1 Cost and EVM Performance: Red/.test(text) && /A4[^\n]*: Red/.test(text), true);
check("(4) shows every supporting category, assessed or not",
      /A4[^\n]*\(supporting\)/.test(text) && /A5[^\n]*\(supporting\)/.test(text), true);
check("(4b) a supporting category not assessed says so and produces NO Green",
      /A5[^\n]*\(supporting\): not assessed\. A supporting category that was not assessed never produces a Green\./
        .test(text), true);
check("(5) escalates the assessed adverse conditions rather than waiting for the status",
      /Escalate now, without waiting for an official posture: A1/.test(text)
      && /Escalate now, without waiting for an official posture: A4/.test(text), true);
check("(5b) the recommendation is about evidence acquisition and verification",
      /Acquire the evidence/.test(text) && /Verify the figures already on file/.test(text), true);
check("(5c) no fabricated health recommendation: no routine-monitoring or review-the-trend line",
      /maintain routine monitoring|review the cost and schedule trend/.test(text), false);
check("(6) a concrete course the participant can accept, reject or modify, naming the real "
      + "control and its real vocabulary",
      /Record how you treated this recommendation on the decision card - accept, accept with conditions, modify, reject, defer, request evidence, escalate or transfer authority/
        .test(text), true);

console.log("3. THE THREE RUN 70 CHECKS, UNMODIFIED, ON THIS BRIEF");
const gate = T.briefGate(parsed, ev);
if (!gate.ok) gate.failures.forEach((f) =>
  console.log("      REJECTED by " + f.check + " [" + f.section + "]: " + f.sentence
              + "\n         -> " + f.reason));
check("the production gate accepts the Indeterminate brief", gate.ok, true);

console.log("4. THE HARNESS CAN FAIL -- the same gate on a brief that asserts without a figure");
const bad = T.parseBrief([
  "### Recommendation",
  "INDETERMINATE · the evidence suggests meaningful risk that may warrant a closer look.",
  "### Signal Pattern", "none", "### Key Drivers", "- none", "### Required Actions", "- none"
].join("\n"));
const badGate = T.briefGate(bad, ev);
check("a figureless condition claim is REJECTED by check 1", badGate.ok, false);
check("...and the rejection names check 1",
      (badGate.failures[0] || {}).check, "1. Every claim names the figure behind it");

console.log("\n" + (FAILURES.length ? FAILURES.length + " FAILURES: " + FAILURES : "ALL PASS"));
process.exit(FAILURES.length ? 1 : 0);
