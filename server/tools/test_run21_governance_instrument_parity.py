#!/usr/bin/env python3
"""
RUN 21, QUEUE ITEM 3. THE BROWSER INSTRUMENT AGAINST THE SERVER, FOR THE FOUR GOVERNANCE
MODULES RUN 20 CYCLE 2 CORRECTED.

WHAT WENT WRONG, AND WHY A SUITE EXISTS NOW. Run 20 cycle 2 withdrew four regulatory claims from
the server because no cited provision states them: a FAR part number attached to an uncited 25%
overrun level, an OMB circular reduced to three thresholds and then said to make reporting
MANDATORY, an EVM reporting compliance said to be BREACHED when no cadence, due date or received
date is held anywhere, and a constraint rule NAMED after a regulation that states no such
threshold. The server was corrected. `assets/js/simulations.js`, which computes the same four
modules in the browser for `research/deepdive.html`, WAS NOT. It went on publishing all four
withdrawn claims to a researcher for the whole of Run 20, and Run 20 recorded it as queue item 3
rather than fixing it.

WHY THIS IS NOT A SECOND COPY OF THE LOGIC, WHICH SPECIFICATION 24 FORBIDS AS AN ORACLE. The
oracle here is the SERVER, executed. Section 2 runs the real shipped JavaScript in node and the
real shipped Python in this process ON THE SAME INPUTS and compares the two result dicts key by
key. Nothing in this file restates what either should compute. Section 1 additionally pins the
withdrawn SENTENCES as literals, because the sentence is what a researcher reads and a key-level
comparison would pass if both sides drifted together.

NON-VACUITY. Section 3 proves each guard RED by mutating the shipped instrument in a temporary
copy and showing the named check fails, then proves it GREEN again on the restored file. A guard
that cannot fail is not evidence, and Run 20 found nine that could not.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run21_governance_instrument_parity.py
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")

ROOT = pathlib.Path(__file__).resolve().parents[2]
SIM_JS = ROOT / "assets" / "js" / "simulations.js"

passed = total = 0
failures: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failures.append(f"{label}: {detail}")
        print(f"  FAIL  {label}  {detail}")


# ---------------------------------------------------------------- the node bridge

# Executes the SHIPPED file. The IIFE assigns to window.LinSimulations, so a window object is
# the only shim; no function is redefined and no arithmetic is restated here.
BRIDGE = r"""
const fs = require('fs');
globalThis.window = globalThis;
eval(fs.readFileSync(process.argv[2], 'utf8'));
const S = globalThis.LinSimulations;
const cases = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = {};
for (const [name, spec] of Object.entries(cases)) {
  out[name] = {};
  for (const [caseName, si] of Object.entries(spec)) {
    try { out[name][caseName] = S[name](si); }
    catch (e) { out[name][caseName] = { __error: String(e) }; }
  }
}
process.stdout.write(JSON.stringify(out));
"""

# The inputs. Chosen to land on BOTH sides of every boundary each of the four modules carries,
# so a sentence that only appears in one branch cannot escape comparison: above and below the
# 25% review level, above and below the ten-million budget level, cost index above and below
# 0.90, schedule index above and below 0.90, and a constraint case with violations and one
# without.
CASES: dict[str, dict[str, dict]] = {
    "runFARThreshold": {
        "below_review_level": {"bac": 12_000_000, "cpi": 0.97, "ev": 5_000_000, "ac": 5_154_639},
        "above_review_level": {"bac": 12_000_000, "cpi": 0.70, "ev": 5_000_000, "ac": 7_142_857},
    },
    "runOMBA11Check": {
        "large_budget_and_below": {"bac": 12_000_000, "cpi": 0.85, "actualPctComplete": 40},
        "small_budget_and_below": {"bac": 4_000_000, "cpi": 0.85, "actualPctComplete": 40},
        "at_or_above_level": {"bac": 12_000_000, "cpi": 0.98, "actualPctComplete": 40},
    },
    "runEVMReportingThreshold": {
        "both_below": {"bac": 12_000_000, "cpi": 0.80, "spi": 0.80},
        "neither_below": {"bac": 12_000_000, "cpi": 0.98, "spi": 0.98},
        "one_below": {"bac": 12_000_000, "cpi": 0.98, "spi": 0.80},
    },
    "runContractModFrequency": {
        "quiet": {"changeOrderCount": 1, "baselineContractSum": 10_000_000,
                  "revisedContractSum": 10_100_000},
        "busy": {"changeOrderCount": 12, "baselineContractSum": 10_000_000,
                 "revisedContractSum": 12_500_000},
    },
    "runConstraintSatisfaction": {
        "all_met": {"cpi": 0.99, "spi": 0.99, "bac": 12_000_000, "docRiskScore": 0.10},
        "violations": {"cpi": 0.75, "spi": 0.60, "bac": 12_000_000, "docRiskScore": 0.90},
    },
}

# The shipped server function behind each shipped browser function. The pairing is the only
# thing this file asserts about the mapping, and it is the pairing the registry itself uses.
PAIRS = {
    "runFARThreshold": "run_far_threshold",
    "runOMBA11Check": "run_omb_a11_check",
    "runEVMReportingThreshold": "run_evm_reporting_threshold",
    "runContractModFrequency": "run_contract_mod_frequency",
    "runConstraintSatisfaction": "run_constraint_satisfaction",
}


def run_js(path: pathlib.Path) -> dict:
    with tempfile.TemporaryDirectory() as td:
        b = pathlib.Path(td) / "bridge.js"
        c = pathlib.Path(td) / "cases.json"
        b.write_text(BRIDGE, encoding="utf-8")
        c.write_text(json.dumps(CASES), encoding="utf-8")
        r = subprocess.run(["node", str(b), str(path), str(c)],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(f"node failed rc={r.returncode}: {r.stderr[-2000:]}")
        return json.loads(r.stdout)


def run_py() -> dict:
    from app.simulation import models_gov as G
    out: dict = {}
    for js_name, py_name in PAIRS.items():
        fn = getattr(G, py_name)
        out[js_name] = {}
        for case_name, si in CASES[js_name].items():
            out[js_name][case_name] = fn(dict(si), lambda: 0.5, None)
    return out


# ---------------------------------------------------------------- section 1, the sentences

# The exact strings Run 20 cycle 2 withdrew from the server. Pinned as LITERALS. Each one is a
# claim about a regulation that the cited provision does not state.
WITHDRAWN = [
    "REPORTING REQUIRED",
    "MANDATORY REPORTING TRIGGERED",
    "far34_threshold_pct",
    "far_reporting_required",
    "major_program",
    "reporting_triggered",
    "cpi_breached",
    "spi_breached",
    "both_breached",
    "FAR threshold (overrun < 25%)",
    "FAR Part 34: ",
    "OMB A-11: CPI ",
    "EVM threshold: CPI ",
]

# The disclosures the corrected server publishes and the instrument must publish with it.
REQUIRED = [
    "UNCITED_INTERNAL_REVIEW_LEVEL",
    "NOT_MADE",
    "review_threshold_pct",
    "exceeds_review_threshold",
    "large_budget",
    "review_condition_met",
    "cpi_below_review_level",
    "spi_below_review_level",
    "both_below_review_level",
    "reporting_compliance_assessed",
    "Forecast overrun below 25% (CPI > 0.80)",
    "which no regulation states",
    "No requirement of the circular is evaluated here",
    "whether required reports were submitted is not assessed here",
]


def strip_comments(text: str) -> str:
    """
    Removes JavaScript comments, leaving string and template literals intact.

    WHY THIS EXISTS, recorded because the first version of this suite did not have it and was
    RIGHT to fail without it. The withdrawn sentences are quoted verbatim in the corrections'
    own explanatory comments, which is where a reader learns what was withdrawn and why. A raw
    substring scan cannot tell a quoted-and-withdrawn claim from a published one, and it flagged
    the corrected file. What a researcher reads is the EXECUTED code, so that is what the scan
    must read. This makes the guard sharper, not weaker: every mutation in section 3 restores a
    claim into executable code, and each is still proved RED below.
    """
    out = []
    i, n = 0, len(text)
    quote = None
    while i < n:
        c = text[i]
        if quote:
            out.append(c)
            if c == "\\":
                if i + 1 < n:
                    out.append(text[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "\"'`":
            quote = c
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def section1(text: str) -> list[str]:
    """Returns the labels that FAIL for this text. Used for the live file and for mutants."""
    code = strip_comments(text)
    bad = []
    for s in WITHDRAWN:
        if s in code:
            bad.append(f"withdrawn:{s}")
    for s in REQUIRED:
        if s not in code:
            bad.append(f"missing:{s}")
    return bad


print("=" * 78)
print("SECTION 1  the withdrawn regulatory sentences are absent, the disclosures are present")
print("=" * 78)
live = SIM_JS.read_text(encoding="utf-8")
live_code = strip_comments(live)
# The stripper must actually be doing something, or every check below is scanning the raw file
# and the distinction it claims to draw is imaginary.
check(len(live_code) < len(live), "the comment stripper removed commentary",
      f"raw={len(live)} code={len(live_code)}")
check("REPORTING REQUIRED" in live and "REPORTING REQUIRED" not in live_code,
      "a claim quoted only in commentary is seen as commentary, not as published text")
for s in WITHDRAWN:
    check(s not in live_code, f"withdrawn claim absent from executed simulations.js: {s!r}")
for s in REQUIRED:
    check(s in live_code, f"disclosure present in executed simulations.js: {s!r}")

print()
print("=" * 78)
print("SECTION 2  the shipped JavaScript executed against the shipped server, same inputs")
print("=" * 78)
js = run_js(SIM_JS)
py = run_py()
for js_name in PAIRS:
    for case_name in CASES[js_name]:
        a = js[js_name][case_name]
        b = py[js_name][case_name]
        check("__error" not in a, f"{js_name}/{case_name} executed in node", str(a)[:200])
        check(set(a) == set(b), f"{js_name}/{case_name} key set matches the server",
              f"js-only={sorted(set(a) - set(b))} server-only={sorted(set(b) - set(a))}")
        for k in sorted(set(a) & set(b)):
            av, bv = a[k], b[k]
            if isinstance(av, float) or isinstance(bv, float):
                same = abs(float(av) - float(bv)) < 1e-9
            else:
                same = av == bv
            check(same, f"{js_name}/{case_name}.{k} matches the server",
                  f"browser={av!r} server={bv!r}")

print()
print("=" * 78)
print("SECTION 3  guard non-vacuity: each guard proved RED by a real violation, then GREEN")
print("=" * 78)

# Every mutation restores exactly one withdrawn claim into a COPY of the shipped file. The
# guard must go red on that copy; the live file must stay green. A guard that does not go red
# is a guard that would not have caught the defect this suite exists for.
MUTATIONS = [
    ("restore the FAR part-number sentence",
     "% forecast overrun against an internal review level of ", "FAR Part 34: ",
     "withdrawn:FAR Part 34: "),
    ("restore the mandatory-reporting conclusion",
     ", below the internal review level of 0.90 on a budget of ten million or more, ",
     ": MANDATORY REPORTING TRIGGERED", "withdrawn:MANDATORY REPORTING TRIGGERED"),
    ("restore the breached-compliance wording",
     "cpi_below_review_level: cpiBreached", "cpi_breached: cpiBreached",
     "withdrawn:cpi_breached"),
    ("restore the regulation's name on the constraint rule",
     "Forecast overrun below 25% (CPI > 0.80)", "FAR threshold (overrun < 25%)",
     "withdrawn:FAR threshold (overrun < 25%)"),
    ("drop the regulatory_determination disclosure",
     "regulatory_determination: 'NOT_MADE',", "",
     "missing:NOT_MADE"),
    ("drop the threshold provenance disclosure",
     "threshold_provenance: 'UNCITED_INTERNAL_REVIEW_LEVEL',", "",
     "missing:UNCITED_INTERNAL_REVIEW_LEVEL"),
]

for label, find, repl, expect in MUTATIONS:
    check(find in live, f"mutation target present in the shipped file: {label}", find[:60])
    mutant = live.replace(find, repl)
    check(mutant != live, f"mutation actually changed bytes: {label}")
    bad = section1(mutant)
    check(expect in bad, f"guard turns RED under: {label}",
          f"expected {expect!r} among the failures, got {bad}")

# And GREEN on the restored, shipped file. Read from disk again rather than from the variable,
# so this cannot pass on a copy the mutations never touched.
restored = SIM_JS.read_text(encoding="utf-8")
check(restored == live, "the shipped file on disk is unmodified by this suite")
check(section1(restored) == [], "guard is GREEN on the shipped file",
      str(section1(restored)))

# Section 2 must also be capable of failing. Prove it: mutate a NUMBER the server pins and show
# the executed comparison diverges. This is the check that a key-level rename would slip past.
mutant_num = live.replace("var reviewThreshold = 25;", "var reviewThreshold = 30;")
check(mutant_num != live, "numeric mutation changed bytes")
with tempfile.TemporaryDirectory() as td:
    p = pathlib.Path(td) / "simulations.js"
    p.write_text(mutant_num, encoding="utf-8")
    mj = run_js(p)
diverged = (mj["runFARThreshold"]["below_review_level"]["review_threshold_pct"]
            != py["runFARThreshold"]["below_review_level"]["review_threshold_pct"])
check(diverged, "the executed comparison turns RED when the browser number is changed",
      f"browser={mj['runFARThreshold']['below_review_level']['review_threshold_pct']} "
      f"server={py['runFARThreshold']['below_review_level']['review_threshold_pct']}")

print()
if failures:
    print("FAILURES:")
    for f in failures:
        print("  " + f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
