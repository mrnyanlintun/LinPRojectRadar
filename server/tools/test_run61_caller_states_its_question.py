#!/usr/bin/env python3
"""
RUN 61. THE CALLER STATES WHAT IT IS ASKING FOR, AND THE ANSWER MATCHES THE QUESTION OR REFUSES.

Source-level guards over the client's stored-row layer and over the verification rule itself.
The browser-side behaviour of the three shapes is asserted in tests_render.html group 21 and
measured live by server/tools/drive_run61_caller_shapes.py; this file guards the things a
harness can silently stop exercising.

Every check here fails if its subject is removed. That is stated per check, and each was proved
by injection during Run 61 (see the report's section 11).
"""
from __future__ import annotations
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
FAILURES: list[str] = []
CHECKS = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILURES.append(f"{name}: {detail}")


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


TAX = text("assets/js/taxonomy.js")
WS = text("assets/js/workspace.js")
DET = text("assets/js/detail.js")

# ---------------------------------------------------------------- the three shapes exist
for fn in ("rowForPeriod", "latest", "rowsForPeriods", "primedPeriods"):
    check(f"LinResults exposes {fn}", f"{fn}:" in TAX or f"{fn}: function" in TAX,
          f"{fn} is not on the LinResults surface in taxonomy.js")

# SHAPE 1 IS STRICT. `primedFor` is the single place a primed row is chosen, and when a period
# was stated it may only return that period's slot. If this line is relaxed to fall back to
# another period, the defect Run 60 measured returns in full.
check("primedFor is strict when a period is stated",
      "if (want !== null) return b[want] || null;" in TAX,
      "the strict arm of primedFor is gone; a stated period could be answered with another one")

# THE CACHE IS KEYED BY PERIOD. One slot per project is what made two periods collide.
check("prime stores the row in its own period's slot",
      "b[periodKey(row.period)] = row;" in TAX,
      "LinResults.prime no longer keys the row by period")
check("ROWS is no longer a one-row-per-project slot",
      "ROWS[projectId] = row" not in TAX,
      "taxonomy.js still assigns a bare row to ROWS[projectId]")

# SHAPE 2 RETURNS THE PERIOD WITH THE ROW. A caller told only the row cannot check the answer.
check("latest() returns the period alongside the row",
      "{ row: row, period: bestKey }" in TAX,
      "LinResults.latest no longer reports which period it returned")

# rowFor asks for the period the PAGE holds.
check("rowFor derives the asked-for period from storedResult.period",
      "var want = stored ? periodKey(stored.period) : null;" in TAX,
      "rowFor no longer takes the page's period as the question")

# ---------------------------------------------------------------- no period-1 fallback survives
# RUN 48 removed `period: 1` from detail.js:1267 and it survived in workspace.js. Both files are
# pinned here so a third copy cannot appear unnoticed. `assets/js/decision-ui.js` is EXCLUDED BY
# NAME and for a stated reason: its three literals are inert -- documents._resolve_period derives
# the period from research_decision.current_period whenever a research assignment exists and
# ignores the payload entirely, which Run 48 established by execution (a request stating 1
# returned 3, and a request stating 4 also returned 3).
READ_PATH_FILES = ["assets/js/workspace.js", "assets/js/detail.js", "assets/js/signals.js",
                   "assets/js/app.js", "assets/js/categories.js", "assets/js/taxonomy.js",
                   "assets/js/decision.js", "assets/js/recommendation_options.js",
                   "assets/js/neural_flow.js", "assets/js/projectnet2d.js"]
def strip_js_comments(src: str) -> str:
    """Blank out // and /* */ comments, PRESERVING LINE NUMBERS so a hit can be located."""
    out = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    return re.sub(r"//[^\n]*", "", out)


LITERAL = re.compile(r"""period\s*:\s*(1\b|[A-Za-z_.$]+\s*\|\|\s*1\b)""")
for rel in READ_PATH_FILES:
    # COMMENTS ARE STRIPPED BEFORE SCANNING, not skipped line by line. Several of these files
    # carry a multi-line comment RECORDING the removed literal verbatim -- that record is
    # deliberate and must survive -- and a line-by-line skip misses its continuation lines.
    body = strip_js_comments(text(rel))
    hits = []
    for i, line in enumerate(body.splitlines(), 1):
        if LITERAL.search(line):
            hits.append(f"{rel}:{i}: {line.strip()[:100]}")
    check(f"no hard-coded period literal on a read path in {rel}", not hits, "; ".join(hits))

# ---------------------------------------------------------------- the provenance line rebuilds
# THE HOST MUST BE EMITTED BY render(), not merely mentioned by the rebuilder. An earlier form
# of this check tested for the attribute name anywhere in the file and stayed GREEN when the
# render-site host was deleted, because refreshProvenanceLine's own selector still carried the
# string. It was caught by injection F7 and is pinned to the render site here.
check("render() emits the provenance rebuild host",
      '<div data-provenance-host>${populated ? provenanceLineHtml(p) : ""}</div>' in DET,
      "detail.js no longer renders the provenance host, so the line cannot be rebuilt")
check("refreshProvenanceLine exists",
      "function refreshProvenanceLine(" in DET, "detail.js lost refreshProvenanceLine")
check("primeAndRefresh gives the provenance line its second pass",
      re.search(r"refreshBriefConsistency\(p\);.*?refreshProvenanceLine\(p\);", DET, re.S)
      is not None,
      "refreshProvenanceLine is not called after the row is primed; the first render's answer "
      "would stand exactly as it did before Run 61")

# ---------------------------------------------------------------- the portfolio loader
check("the portfolio loader asks for the latest computed period",
      'call("projectperiods", { id: p.project_id })' in WS
      and 'call("projectresults", { id: p.project_id, period: latest })' in WS,
      "workspace.js renderPortfolio no longer derives the period from projectperiods")

# ---------------------------------------------------------------- THE VERIFICATION RULE
# OWNER RULING, RUN 61 SECTION 5: a browser verification must drive the page the way a user does.
# The rule is enforced HERE, on the harnesses themselves, because a harness that primes a row
# before rendering measures a code path that cannot fail -- which is exactly why this defect
# survived ten runs of green browser verification.
#
# A NEW harness (Run 61 onwards) may not prime before rendering. The harnesses that already
# exist are EVIDENCE of what earlier runs measured and are NOT rewritten; they are named here,
# individually, as the closed set that predates the rule. A new file added to that set does not
# get grandfathered: it has to be added to this list deliberately, in a commit someone reads.
PRE_RULE_HARNESSES = {
    "drive_run44_browser.py", "drive_run48_browser.py", "drive_run52_browser.py",
    "drive_run52_premise.py", "run32_b3_browser_verification.py", "drive_run60.py",
}
PRIME_RX = re.compile(r"LinResults\s*\.\s*prime\s*\(")
RENDER_RX = re.compile(r"Lin(Detail|App)\s*\.\s*render\w*\s*\(")
offenders = []
for path in sorted((ROOT / "server" / "tools").glob("*.py")):
    if path.name in PRE_RULE_HARNESSES:
        continue
    body = path.read_text(encoding="utf-8", errors="replace")
    if not RENDER_RX.search(body):
        continue
    # Only executable lines count. A comment describing the rule is not a breach of it.
    for i, line in enumerate(body.splitlines(), 1):
        s = line.strip()
        if s.startswith("#") or s.startswith("//") or s.startswith("*"):
            continue
        if not PRIME_RX.search(line):
            continue
        # THE ONE PERMITTED PRIME, and it is the opposite of the forbidden one. A harness may
        # prime a DIFFERENT period's row on purpose in order to attack the page with it -- that
        # is the adversarial reproduction of the Run 60 defect, not a way of hiding it. The
        # exemption is marked ON THE LINE ITSELF so it is visible in the file it exempts, and it
        # cannot be applied to the row the page is about to render without saying so out loud.
        if "R61-ADVERSARIAL-PRIME" in line:
            continue
        offenders.append(f"{path.name}:{i}")
check("no browser harness written after Run 61 primes a row before rendering",
      not offenders,
      "primes before render, which is the one order in which the Run 60 defect cannot appear: "
      + ", ".join(offenders))

# The rule must be WRITTEN DOWN where the next run finds it, in a non-markdown production file
# (Run 59's ruling: no markdown document carries authority).
check("the verification rule is stated in the driver that follows it",
      "NO PRE-PRIMING" in text("server/tools/drive_run61_caller_shapes.py"),
      "the rule is not stated in server/tools/drive_run61_caller_shapes.py")
check("the driver that follows the rule uses a fixture whose period is not 1",
      "current period is not 1" in text("server/tools/drive_run61_caller_shapes.py").lower(),
      "the driver does not state the not-period-1 requirement")

# ---------------------------------------------------------------- derived platform figures
sys.path.insert(0, str(ROOT / "server"))
from app.simulation.registry import registry_index, service_index, CORE_VOTING_MODULES  # noqa: E402

check("registry total is 101", len(registry_index()) == 101, str(len(registry_index())))
check("modules in service is 63", len(service_index()) == 63, str(len(service_index())))
check("voting modules are exactly A1.7 and A1.8",
      sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"], str(sorted(CORE_VOTING_MODULES)))

print(f"checks: {CHECKS}")
# RUN 62. THE CANONICAL RESULT LINE, WHICH THIS SUITE DID NOT PRINT.
#
# server/run_all_suites.sh accepts ONE form -- "RESULT: <passed>/<total> checks passed" -- and
# says why in its own comment: a prose summary is not accepted because a suite that crashes
# before printing this, or that prints its own wording, must FAIL the runner rather than look
# clean. This suite printed "checks: 29" and "ALL GREEN", so the runner reported it as NO
# CANONICAL RESULT LINE and its twenty-nine checks counted for nothing in the pass total. The
# suite was green; the pass could not see it. The line is added; NOT ONE CHECK is changed,
# added or removed, and the existing output is kept beside it rather than replaced.
print(f"RESULT: {CHECKS - len(FAILURES)}/{CHECKS} checks passed")
if FAILURES:
    print(f"FAILURES: {len(FAILURES)}")
    for f in FAILURES:
        print("  -", f)
    raise SystemExit(1)
print("ALL GREEN")
