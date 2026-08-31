/*
 * RUN 96 -- THE GOVERNANCE DECISION CARD AGAINST THE THREE RUN 70 RECOMMENDATION CHECKS.
 *
 * The card is composed in Python by `app/decision_brief.py`. Its sentences are claims about a
 * project, so they are subject to the same three checks every other brief is, and the checks are
 * used UNMODIFIED: this file loads `assets/js/detail.js` whole and calls its own exported
 * `briefGate` and `briefEvidence`. Nothing here reimplements or relaxes them.
 *
 *   1. Every claim names the figure behind it.
 *   2. The posture agrees with its drivers.
 *   3. Nothing is asserted that no module computed.
 *
 * The card's prose is rendered into the brief's section shape so `parseBrief` reads it, which is
 * how the gate is reached. If a composed sentence cannot pass, the SENTENCE changes -- never the
 * check.
 */
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..", "..");

let PASSED = 0, TOTAL = 0;
const FAILS = [];
function check(name, cond, detail) {
  TOTAL += 1;
  if (cond) { PASSED += 1; console.log("  [PASS] " + name); return true; }
  FAILS.push(name + (detail ? " -- " + detail : ""));
  console.log("  [FAIL] " + name + (detail ? " -- " + detail : ""));
  return false;
}

const card = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const row = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));

// ---------------------------------------------------------------- load detail.js whole
/* The same sandbox Run 89 used, for the same reason: thin enough that nothing is faked into
   working. detail.js needs `document` and `window` to EXIST at load; every function called
   below is pure over its arguments. `LinResults.rowFor` is the ONE thing supplied, and it
   returns the STORED row read out of the database, not a constructed one. */
const vm = require("vm");
const el = () => ({ querySelector: () => null, querySelectorAll: () => [], addEventListener(){},
                    classList: { add(){}, remove(){} }, insertAdjacentHTML(){}, style: {},
                    setAttribute(){}, getAttribute: () => null, appendChild(){}, remove(){},
                    innerHTML: "", textContent: "", className: "", dataset: {} });
const sandbox = {
  console, JSON, Math, Date, Number, String, Object, Array, RegExp, isNaN, parseFloat, parseInt,
  setTimeout, clearTimeout, requestAnimationFrame: () => 0, cancelAnimationFrame(){},
  document: Object.assign(el(), { createElement: el, getElementById: () => null, body: el(),
                                  documentElement: el(), addEventListener(){} }),
  navigator: { userAgent: "node" }, location: { href: "", search: "" },
  fetch: () => Promise.resolve(),
  localStorage: { getItem: () => null, setItem(){}, removeItem(){} },
};
sandbox.window = sandbox; sandbox.self = sandbox; sandbox.globalThis = sandbox;
vm.createContext(sandbox);
for (const f of ["assets/js/config.js", "assets/js/taxonomy.js", "assets/js/detail.js"]) {
  try { vm.runInContext(fs.readFileSync(path.join(ROOT, f), "utf8"), sandbox, { filename: f }); }
  catch (e) { console.log("  [load] " + f + ": " + e.message); }
}
/* Supplied AFTER the files load: config.js/taxonomy.js/detail.js define their own globals, and
   a stub set before them is overwritten. Measured -- set first, `briefEvidence` saw one figure;
   set after, it sees the stored row. */
sandbox.LinResults = { rowFor: () => row };

const T = sandbox.window.LinDetail && sandbox.window.LinDetail.__briefForTest;
check("detail.js exports the brief test seam", !!(T && T.briefGate && T.briefEvidence && T.parseBrief),
      T ? Object.keys(T).join(",") : "no seam");
if (!T) { console.log("RESULT: " + PASSED + "/" + TOTAL + " checks passed"); process.exit(1); }

// ---------------------------------------------------------------- the card as a brief
function driverLine(d) {
  const band = d.band ? " (" + d.band + ")" : "";
  return "- " + (d.category_name || d.category) + (d.module_id ? " " + d.module_id : "") +
         (d.reading ? ": " + d.reading : "") + band;
}
const drivers = [].concat(card.drivers ? card.drivers.collapsed : [],
                          card.drivers ? card.drivers.expanded : []);
const text = [
  "## Recommendation",
  card.finding || "",
  card.why || "",
  "## Signal pattern",
  (card.limitations || []).join(" "),
  "## Key drivers",
  drivers.map(driverLine).join("\n"),
].join("\n");

const parsed = T.parseBrief(text);
check("the card's prose parses into the brief section shape the gate reads",
      !!parsed && parsed.recommendation.length > 0, JSON.stringify(parsed && Object.keys(parsed)));

const project = { id: "run96", project_id: "run96", status: card.posture && card.posture.status };
const ev = T.briefEvidence(project);
check("the evidence view carries the figures the stored result holds",
      ev && ev.allowedFigures && Object.keys(ev.allowedFigures).length > 0,
      ev ? String(Object.keys(ev.allowedFigures || {}).length) : "none");

const gate = T.briefGate(parsed, ev);
const failures = (gate && gate.failures) || (Array.isArray(gate) ? gate : []);
check("THE THREE RECOMMENDATION CHECKS PASS ON THE COMPOSED CARD, UNMODIFIED",
      failures.length === 0, JSON.stringify(failures, null, 1));

// ---------------------------------------------------------------- the card's own boundary
const prose = [card.finding, card.why, card.question].concat(card.limitations || []).join(" ");
const IMPERATIVES = [
  /\bresequenc\w*/i, /\byou must\b/i, /\bshould be\b/i, /\bimmediately\b/i,
  /\brecommend\w*\s+(?:that|to)\b/i, /\btake action\b/i, /\bescalate to\b/i,
  /\bby (?:next|the end of)\b/i, /\bdeadline\b/i, /\bapprov\w*/i, /\bauthoris\w*/i,
  /\bauthoriz\w*/i, /\bauthority\b/i, /\bcorrective action\b/i, /\bremed(?:y|ial|iate)\w*/i,
  /\brequires that\b/i, /\bmust be\b/i, /\bbefore the next\b/i, /\bwithin \d+ days\b/i,
];
const hits = IMPERATIVES.filter((re) => re.test(prose)).map(String);
check("the card prescribes no action, deadline, authority or remedy", hits.length === 0,
      hits.join(" | "));
check("no block prints a placeholder such as 'not established' or 'not available'",
      !/not established|not available|none identified|n\/a/i.test(JSON.stringify(card)),
      "placeholder text found");
check("alternatives and comparative effects is not present at all",
      !("alternatives" in card) && (card.order || []).indexOf("alternatives") < 0);
check("the reviewer block is absent when no assigned reviewer is on the record",
      !("reviewer" in card));
check("the decision question is a question", /\?$/.test(String(card.question || "")),
      String(card.question || "").slice(-40));
check("the collapsed driver view shows at most four",
      !card.drivers || card.drivers.collapsed.length <= 4,
      card.drivers ? String(card.drivers.collapsed.length) : "none");
check("no driver is called contradictory unless a disagreement was computed",
      !/contradict/i.test(JSON.stringify(card)));

// ---------------------------------------------------------------- PROOF THE HARNESS CAN FAIL
/* The same gate, the same evidence, fed a sentence of the kind the card must never produce.
   Without this the four checks above would pass on a gate that accepted anything. */
const badFigure = T.parseBrief([
  "## Recommendation",
  "The project is in a materially adverse cost condition of 41.7 percent against baseline.",
].join("\n"));
const badGate = T.briefGate(badFigure, ev);
const badFailures = (badGate && badGate.failures) || (Array.isArray(badGate) ? badGate : []);
check("INJECTED: the same gate REJECTS a condition asserted on a figure no module computed",
      badFailures.length > 0, JSON.stringify(badFailures));

const badImperative = "The Schedule category requires that work be resequenced immediately, " +
                      "with approval by the deciding authority before the next reporting cycle.";
const impHits = IMPERATIVES.filter((re) => re.test(badImperative));
check("INJECTED: the boundary test REJECTS a prescribed action, deadline and authority",
      impHits.length >= 3, String(impHits.length));

if (FAILS.length) { console.log("FAILURES:"); FAILS.forEach((f) => console.log("  " + f)); }
console.log("RESULT: " + PASSED + "/" + TOTAL + " checks passed");
process.exit(PASSED === TOTAL ? 0 : 1);
