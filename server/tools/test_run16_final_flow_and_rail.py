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
for wanted in ("SUPPORTED DOCUMENT TYPES", "UPLOADED ON THIS PROJECT",
               "REGISTERED PROJECT MODULES", "WITH A CURRENT RESULT",
               "REGISTERED CATEGORIES", "ESTIMABLE NOW"):
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

rows = list(csv.DictReader(
    (ROOT / "p0-baseline" / "module_renumbering_map.csv").open(encoding="utf-8-sig")))
live = [r for r in rows if r["new_id"].strip().upper() != "RETIRED"]
project_level = [r for r in live if r["group"] != "D"]
check(len(project_level) == 96,
      "the registry declares 96 project-level modules, which is what the label now names",
      str(len(project_level)))

# ---------------------------------------------------------------- A3: edges show activity only
check("function flowAnim(el, cls, active)" in FLOW,
      "an edge's animation takes an explicit activity argument")
check("if (!active) { el.classList.add('lnf-static'); return; }" in FLOW,
      "and an inactive edge is marked static and never animated")
calls = re.findall(r"flowAnim\((\w+), '([\w-]+)'(.*?)\);", FLOW)
check(len(calls) >= 5, "every connection class routes through it", str(len(calls)))
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
check("registered architecture" in FLOW,
      "which names what the shapes on screen are")
check("not what this project has done" in FLOW,
      "and says plainly that architecture is not activity")
check("no uploaded documents and no current results" in FLOW,
      "with an explicit empty-project sentence")
for banned in ("—", " & "):
    check(banned not in FLOW[FLOW.index("var archSentence"):FLOW.index("container.appendChild(sum)")],
          f"the summary prose obeys the naming rules ({banned!r})")

# ---------------------------------------------------------------- A5: the section badges
check('totalModulesForBadge} registered' in DETAIL,
      "the Signal Flow badge names a registry count rather than a tally of what ran")
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
check('id="detail-secnav"' in INDEX, "the Signal navigation rail element is served")
check(".detail-secnav {" in CSS, "and is styled as a permanently positioned rail")
check("position: fixed; left: 12px" in CSS, "fixed to the left edge")
check("function buildSectionNav" in DETAIL, "and populated from the rendered sections")
check(".collapse-section" in DETAIL and "hand-maintained" in DETAIL,
      "from the sections actually rendered, not a duplicate list")

# NO COLLAPSE OR HIDE CONTROL, in the rail or anywhere the rail could acquire one. Run 16 found
# none present on the served desktop route; this is the guard that keeps it that way.
nav_css_start = CSS.index(".detail-secnav {")
nav_css = CSS[nav_css_start:nav_css_start + 3000]
for arrow in ("◀", "▶", "◂", "▸", "‹", "›", "❮", "❯"):
    check(arrow not in nav_css, f"the rail's styles introduce no {arrow} control")
    # detail.js's one use of a triangle is inside a bullet-stripping character class in a text
    # helper, which renders nothing; the check is on what the file BUILDS.
    built = re.findall(r'"[^"\n]*' + arrow + r'[^"\n]*"', DETAIL) + \
        re.findall(r"'[^'\n]*" + arrow + r"[^'\n]*'", DETAIL)
    check(not [b for b in built if "<" in b or "button" in b.lower()],
          f"and detail.js builds no {arrow} control", str(built)[:120])
for token in ("secnav-toggle", "secnav-collapse", "secnav-hide", "detail-secnav-toggle"):
    check(token not in DETAIL and token not in CSS and token not in INDEX,
          f"no {token} control exists")
navbuild = DETAIL[DETAIL.index("function buildSectionNav"):DETAIL.index("// Scroll-spy")]
check("<button" in navbuild and navbuild.count("<button") == 1,
      "the rail renders exactly one kind of button: a numbered section target",
      str(navbuild.count("<button")))
check("data-secnav-target" in navbuild,
      "and every one of them targets a section")
check("nav.hidden = false" in DETAIL,
      "the rail is shown whenever the page has sections")
# The one place the rail hides is the pre-existing mobile breakpoint, which is deliberate and
# out of scope: the run must not have touched it.
check("@media (max-width: 700px)" in CSS[nav_css_start:nav_css_start + 3000],
      "the existing mobile behaviour is preserved")

for f in failures:
    print("FAILED:", f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
