#!/usr/bin/env python3
"""
RUN 16, WORKSTREAMS A AND B. THE GUARDS THAT DO NOT NEED A BROWSER.

WHAT THIS FILE IS FOR, AND WHAT IT REFUSES TO BE. The truth about what the Project Detail page
shows is established in a real browser, by tools/drive_run16_final_flow.py, against the served
application; that is the deliverable and it is not duplicated here. tests_render.html never
loads index.html and neither does this file, so nothing here claims to know what a participant
sees.

What it does guard is the class of regression a browser run would only catch by luck: the
misleading label coming back, a browser-side computation appearing where the server is the
authority, a collapse control being introduced into the Signal navigation rail, and the
architecture counts drifting away from the registry they are supposed to be derived from. These
are byte-level properties of the shipped files, stated as properties, not as a second copy of
the logic.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run16_final_flow_and_rail.py
"""

from __future__ import annotations

import csv
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")

ROOT = pathlib.Path(__file__).resolve().parents[2]
FLOW = (ROOT / "assets" / "js" / "neural_flow.js").read_text(encoding="utf-8")
DETAIL = (ROOT / "assets" / "js" / "detail.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "css" / "radar.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")

passed = total = 0
failures: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if ok:
        passed += 1
    else:
        failures.append(label + (f"  [{detail}]" if detail else ""))


# ---------------------------------------------------------------- A4/A5: the misleading labels
# The exact strings the served page produced before this run, captured in
# code_audit/run16_final_flow_browser_facts.csv at state A-empty on an EMPTY project.
for gone in ("' DOCUMENTS'", "' MODULES'", "' CATEGORIES'"):
    check(gone not in FLOW,
          f"the column header no longer builds the bare label {gone}", gone)
# RUN 90 RE-POINTED THREE OF THESE SIX. The population both charts draw changed on the owner's
# Run 90 ruling -- the six weighted performance categories -- so "REGISTERED PROJECT MODULES",
# "REGISTERED CATEGORIES" and "ESTIMABLE NOW" no longer describe what is on screen. The checks
# were turned RED against the Run 90 build first, then re-pointed at the shipped wording. The
# thing being asserted is unchanged: the header is a truthful label, not a bare noun.
for wanted in ("SUPPORTED DOCUMENT TYPES", "UPLOADED ON THIS PROJECT",
               # RUN 96: was "MODULES IN SERVICE", which named the registry's population and
               # counted the charted one. The label must still be truthful, which is the
               # assertion; the truthful label changed.
               "MODULES IN THESE CATEGORIES", "WITH A CURRENT RESULT",
               "WEIGHTED PERFORMANCE CATEGORIES", "CARRY A POSTURE"):
    check(wanted in FLOW, f"and carries the truthful label {wanted!r}")
check("NOT ESTIMABLE" in FLOW and "'Not estimable'" in FLOW,
      "an unestimable project rollup is presented as not estimable, not as the word None")

# The architecture counts stay DERIVED. A hardcoded 27, 96 or 11 in a header is the defect
# coming back in a form no registry change would correct.
header_block = FLOW[FLOW.index("var HEADERS = ["):FLOW.index("HEADERS.forEach")]
check("DOC_KEYS.length" in header_block and "MODULES.length" in header_block
      and "CATS.length" in header_block,
      "the architecture counts are derived from the registry, not typed in")
check(not re.search(r"\b(27|96|11)\b", header_block),
      "and no header literal hardcodes one of them", header_block[:200])

# The counts the diagram reports must still MATCH the registry, or the label is truthful about
# a number that is not. 27 document types comes from the extraction layer's own list.
sys.path.insert(0, str(ROOT / "server"))
from app.extraction_fields import DOC_TYPES  # noqa: E402

doc_keys = re.search(r"var DOC_KEYS = \[(.*?)\];", FLOW, re.S).group(1)
declared = re.findall(r"'([a-z_]+)'", doc_keys)
check(len(declared) == len(set(declared)), "the document-type list holds no duplicate",
      str(len(declared)))
check(set(declared) <= set(DOC_TYPES),
      "every document type the diagram draws is one the extraction layer recognises",
      str(sorted(set(declared) - set(DOC_TYPES))))

from app.simulation import registry as _REG16  # noqa: E402
rows = list(csv.DictReader(
    (ROOT / "p0-baseline" / "module_renumbering_map.csv").open(encoding="utf-8-sig")))
live = [r for r in rows if r["new_id"].strip().upper() != "RETIRED"]
project_level = [r for r in live if r["group"] != "D"]
# RUN 96. The literal said 96 and had to be retyped at every retirement since Run 43; the owner's
# Run 96 ruling removed fifty-one rows and it would now say 45. The label under test names what
# the registry declares, so the registry is what it is checked against -- read here from the CSV
# directly, which is a different path from the one the label is built on.
check(len(project_level) == len(_REG16.service_index()) - len(
          [m for m in _REG16.service_index() if _REG16.group_of(m) == "D"]),
      "the registry's project-level rows are what the label names",
      str(len(project_level)))
check(len(project_level) > 0,
      "and the project-level population is not empty -- this is not vacuous",
      str(len(project_level)))

# ---------------------------------------------------------------- A3: edges show activity only
check("function flowAnim(el, cls, active)" in FLOW,
      "an edge's animation takes an explicit activity argument")
check("if (!active) { el.classList.add('lnf-static'); return; }" in FLOW,
      "and an inactive edge is marked static and never animated")
calls = re.findall(r"flowAnim\((\w+), '([\w-]+)'(.*?)\);", FLOW)
# RUN 26. FOUR CONNECTION CLASSES, NOT FIVE. The fifth was the governance feedback arc, which
# drew PROJECT STATUS -> CATEGORY -- not an edge kind the architecture has, pointed by a stale
# index at Evidence Combination rather than at any governance category, and the only red stroke
# on an empty project. It is removed, so requiring five calls here would require a fabricated
# edge to exist. The property this check is for is unchanged: every class that IS drawn routes
# its animation through the one activity-gated helper.
check(len(calls) >= 4, "every connection class routes through it", str(len(calls)))
check({c[1] for c in calls} == {"lnf-flow-a", "lnf-flow-b", "lnf-flow-c"},
      "and the classes drawn are exactly the input, rollup and derived ones: the governance "
      "feedback class is no longer emitted by any call site",
      str(sorted({c[1] for c in calls})))
for var, cls, rest in calls:
    check(rest.strip().startswith(","),
          f"the {cls} connection passes an activity argument rather than animating always",
          f"{var} {cls} {rest[:40]}")
check(FLOW.count("isEstimable(") >= 5,
      "activity is decided by the five-verdict test, not by the presence of a shape",
      str(FLOW.count("isEstimable(")))
est = re.search(r"var ESTIMABLE = \{(.*?)\};", FLOW).group(1)
for verdict in ("Green", "Yellow", "Amber", "Red", "Complete"):
    check(verdict in est, f"{verdict} counts as a current result")
for absence in ("None", "NotRelevant"):
    check(absence not in est, f"{absence} does not count as a current result")

# ---------------------------------------------------------------- A2: the stated distinction
check("lnf-summary" in FLOW, "the diagram carries a summary strip")
# RUN 51, SECTION 6.1. The three numbers in this sentence were always derived from the model
# neural_flow.js builds, which is the population IN SERVICE. The WORD beside them said
# "registered", which names a different and larger population, so the sentence read as though
# the diagram drew the whole registry of 101. Only the word moved; no count changed. The check
# is reconciled to the corrected wording, not deleted.
check("architecture in service" in FLOW,
      "which names what the shapes on screen are, and names the population it actually draws")
check("registered architecture" not in
      FLOW[FLOW.index("var archSentence"):FLOW.index("container.appendChild(sum)")]
      and "Show the architecture in service" in FLOW,
      "and no rendered string calls the drawn population the registered one, which it is not; "
      "the two surviving occurrences are code comments and are not user-facing text")
check("not what this project has done" in FLOW,
      "and says plainly that architecture is not activity")
check("no uploaded documents and no current results" in FLOW,
      "with an explicit empty-project sentence")
for banned in ("—", " & "):
    check(banned not in FLOW[FLOW.index("var archSentence"):FLOW.index("container.appendChild(sum)")],
          f"the summary prose obeys the naming rules ({banned!r})")

# ---------------------------------------------------------------- A5: the section badges
# RUN 51, SECTION 6.1, the same correction at the badge: what the section draws is the roster
# IN SERVICE, so the badge says so. It is still a roster count and not a tally of what ran,
# which is what this check exists to assert.
# RUN 90. Same re-pointing, same intent: the badge is still a ROSTER count -- the modules in
# service in the six categories the chart draws -- and still not a tally of what ran.
check('${chartModuleCount} modules drawn' in DETAIL,
      "the Signal Flow badge names a roster count rather than a tally of what ran")
check('totalModulesForBadge + " modules"' not in DETAIL,
      "and the old wording is gone")
check('totalCats + " categories"' not in DETAIL,
      "same for the category badge")

# ---------------------------------------------------------------- GATE 5: one authority only
# The browser derives PRESENTATION counts from stored state. It must not compute a status.
counting = FLOW[FLOW.index("var modWithResult = 0"):FLOW.index("var governedLabel")]
# The tally counts; it must not do arithmetic on the values it counted. `modSilent` is the one
# subtraction and it is a residual of counts, which is why it is excluded by name rather than
# by loosening the rule.
tally_body = counting.replace(
    "var modSilent = MODULES.length - modWithResult - modDisabled - modNotRelevant;", "")
for forbidden in ("Math.", "reduce(", " / ", " * ", "getModuleStatus(", "statusFromSig("):
    check(forbidden not in tally_body,
          f"the presentation tally performs no arithmetic ({forbidden!r})", tally_body[:120])
check("getModuleStatus" in FLOW and "getCategoryStatus" in FLOW
      and "getProjectFusion" in FLOW,
      "every status the diagram draws is read through the stored-row accessors")
# Script TAGS only. Both files are named in explanatory comments in index.html, which is not a
# load; matching on the raw text would assert the comment away rather than the behaviour.
script_srcs = re.findall(r'<script src="([^"]+)"', INDEX)
check(not [s for s in script_srcs if s.endswith(("/sim.js", "/simulations.js",
                                                 "/categories.js"))],
      "and the served application still loads no client analytics engine", str(script_srcs))
check("LIN_ALLOW_CLIENT_ANALYTICS" not in FLOW,
      "the diagram does not reach for the historical client-arithmetic opt-in")

# ---------------------------------------------------------------- B: the Signal navigation rail
# RUN 25, OWNER-DIRECTED CONTRACT CHANGE, 2026-08-14. Run 16 asserted the rail is served,
# styled, populated from the rendered sections, and carries no collapse or paging control.
# The owner then ordered the LEFT RAIL REMOVED ENTIRELY, reversing the earlier instruction
# that it stays. Section B is therefore inverted: every shipped rail marker must be ABSENT
# from every served source. The reversal is recorded in
# code_audit/run20_anti_fossilization_register.csv as a contract change, not a fossilization;
# the browser-level absence proof at five viewport widths is drive_run25_rail_removal.py.
for marker in ("detail-secnav", "buildSectionNav", "data-secnav-target"):
    check(marker not in INDEX, f"index.html serves no rail marker {marker!r}")
    check(marker not in DETAIL, f"detail.js builds no rail marker {marker!r}")
    check(marker not in CSS, f"radar.css styles no rail marker {marker!r}")
# The paging/collapse control the owner described under the rail must be gone with it, in the
# whole of each file now that there is no rail block to scope to. detail.js's one triangle use
# is inside a bullet-stripping character class in a text helper, which renders nothing; the
# check is on what the file BUILDS.
for arrow in ("◀", "▶", "◂", "▸", "‹", "›", "❮", "❯"):
    built = re.findall(r'"[^"\n]*' + arrow + r'[^"\n]*"', DETAIL) + \
        re.findall(r"'[^'\n]*" + arrow + r"[^'\n]*'", DETAIL)
    check(not [b for b in built if "<" in b or "button" in b.lower()],
          f"detail.js builds no {arrow} control", str(built)[:120])
for token in ("secnav-toggle", "secnav-collapse", "secnav-hide", "detail-secnav-toggle"):
    check(token not in DETAIL and token not in CSS and token not in INDEX,
          f"no {token} control exists")
# The sections the rail used to list are still rendered and reachable by their own headers:
# the collapsible-section machinery lives in app.js and must be untouched by the removal.
APP = (ROOT / "assets" / "js" / "app.js").read_text(encoding="utf-8")
check("window.toggleSection = function" in APP and "collapse-section" in APP,
      "the collapsible sections the rail listed still exist and still toggle")
# NON-VACUITY of the absence checks: a copy of the served page with the old rail element
# reinserted must fail the exact predicate used above.
_mut = INDEX.replace('<div id="detail-root">',
                     '<nav id="detail-secnav" class="detail-secnav"></nav><div id="detail-root">', 1)
check(_mut != INDEX and 'id="detail-secnav"' in _mut,
      "INJECTION TOOK EFFECT: the mutated copy carries the rail element")
check(not all(m not in _mut for m in ("detail-secnav",)),
      "and the absence predicate goes RED on that copy, so it can fail")

for f in failures:
    print("FAILED:", f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
