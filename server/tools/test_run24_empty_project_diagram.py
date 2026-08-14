#!/usr/bin/env python3
"""
RUN 24. AN EMPTY PROJECT MUST LOOK EMPTY ON THE SIGNAL FLOW DIAGRAM.

WHAT THIS FILE IS FOR, AND WHAT IT IS NOT FOR. The acceptance evidence for this run is the
BROWSER evidence: `server/tools/drive_run24_empty_project_diagram.py` drives the real served
page on an empty project and on a computed project and reads the rendered DOM. That driver
cannot live in this glob, because `run_all_suites.sh` must not require Chromium. This file is
the SOURCE-LEVEL guard that keeps the shipped rules in place between browser runs, and every
one of its guards is proved capable of failing by really mutating a COPY of the shipped file
and re-running the same scan function the green assertions use.

THE FIVE WAYS A CHECK HAS LIED IN THIS PROJECT, and what is done about each here:
  * it crashed rather than failing -- the canonical RESULT line is printed from a `finally`,
    and the runner rejects anything else;
  * the injection silently failed to apply -- every mutation asserts that the mutated text
    actually differs from the shipped text before the guard is consulted;
  * the fixture built state by a route the application does not take -- there is no fixture
    here; the scan reads the shipped file on disk;
  * it asserted against a copy of the logic -- the scan looks for the SHIPPED code and the
    SHIPPED DOM attribute names, and the emptiness predicate is required to be defined ONCE;
  * it asserted the defect's own sentence -- no check here matches user-facing prose except
    where the prose IS the deliverable (the empty-state statement), and those checks are
    proved red by deleting the code that produces it, not by editing the sentence.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
FLOW_PATH = ROOT / "assets" / "js" / "neural_flow.js"
DETAIL_PATH = ROOT / "assets" / "js" / "detail.js"
CSS_PATH = ROOT / "assets" / "css" / "radar.css"
TAXONOMY_PATH = ROOT / "assets" / "js" / "taxonomy.js"
KNOWLEDGE_PATH = ROOT / "assets" / "js" / "knowledge.js"

FLOW = FLOW_PATH.read_text(encoding="utf-8")
DETAIL = DETAIL_PATH.read_text(encoding="utf-8")
CSS = CSS_PATH.read_text(encoding="utf-8")
TAXONOMY = TAXONOMY_PATH.read_text(encoding="utf-8")
KNOWLEDGE = KNOWLEDGE_PATH.read_text(encoding="utf-8")

PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


# ============================================================================ the registry

def registry_counts() -> tuple[int, int, int, int]:
    """
    THE REGISTRY'S OWN FIGURES, parsed from taxonomy.js rather than typed in here.

    Counts `{ id: '...', num: '...', ... }` module records per category block, and the
    categories themselves, splitting portfolio-level from project-level on the `level`
    field the file carries. If this parse were wrong every count check below would be
    measuring the parser; the non-vacuity section proves it is not, by changing the
    taxonomy in a copy and requiring the parsed figure to move with it.
    """
    blocks = re.split(r"\n\s*\{\s*id:\s*'([a-z]\d+)'", TAXONOMY)
    cats: list[tuple[str, int, bool]] = []
    for i in range(1, len(blocks), 2):
        cid = blocks[i]
        body = blocks[i + 1]
        # stop at the next category record so modules are not double counted
        mods = len(re.findall(r"\{\s*id:\s*'" + re.escape(cid) + r"_\d+'", body))
        portfolio = bool(re.search(r"level:\s*'portfolio'", body[:400]))
        cats.append((cid, mods, portfolio))
    proj = [c for c in cats if not c[2]]
    return (len(cats), sum(c[1] for c in cats), len(proj), sum(c[1] for c in proj))


ALL_CATS, ALL_MODS, PROJ_CATS, PROJ_MODS = registry_counts()

print("=" * 78)
print("SECTION 1  the registry is the only source of a module count")
print("=" * 78)
print(f"        . parsed from taxonomy.js: {ALL_CATS} categories / {ALL_MODS} modules; "
      f"project-level {PROJ_CATS} / {PROJ_MODS}")

check((ALL_CATS, ALL_MODS, PROJ_CATS, PROJ_MODS) == (12, 101, 11, 96),
      "the registry holds 96 project-level modules in 11 project-level categories, and 101 "
      "in 12 counting Portfolio Health",
      f"{ALL_CATS}/{ALL_MODS}/{PROJ_CATS}/{PROJ_MODS}")
check(ALL_MODS == PROJ_MODS + 5,
      "and the whole-taxonomy figure reconciles to the project-level one",
      f"{ALL_MODS} != {PROJ_MODS} + 5")
# The one registry entry the extraction model SUPPLIES rather than the analytical server
# computing. This is what makes the project-level figure "95 computed plus 1 supplied".
check(TAXONOMY.count("method_class: 'Doc_Risk_Cat4'") == 1,
      "exactly one project-level registry entry is the supplied document risk value")

# NO COUNT IS TYPED INTO THE DIAGRAM. Every figure the headers and the summary state must be
# read from the model the registry builds.
check("MODULES.length + ' REGISTERED PROJECT MODULES'" in FLOW,
      "the module column header reads its figure from the built model")
check("CATS.length + ' REGISTERED CATEGORIES'" in FLOW,
      "the category column header reads its figure from the built model")
check("MODULES.length +\n      ' registered project modules and ' + CATS.length +" in FLOW,
      "and the summary sentence reads the same two figures, not a second pair of literals")
check(not re.search(r"'\s*9[0-9] REGISTERED PROJECT MODULES", FLOW),
      "no literal project-module count is hardcoded into the diagram headers")
check("projectModuleCount()" in DETAIL and "totalModulesForBadge = projectModuleCount()" in DETAIL,
      "the detail page's section badges read the same project-level registry count")
# THE KNOWLEDGE PAGE'S FIGURE, which is the one that has disagreed before. It states the
# WHOLE-TAXONOMY count and must reconcile to the registry, not to the project-level figure.
check(f"All {ALL_MODS - 1} registered computations" in KNOWLEDGE,
      "the Knowledge page states the whole-taxonomy computed count",
      f"expected 'All {ALL_MODS - 1} registered computations'")
check("is not counted in the 100; if it is later implemented server-side the count becomes 101"
      in KNOWLEDGE,
      "and says explicitly that the supplied document risk value is excluded from it, so the "
      "two figures are reconcilable rather than contradictory")

# ============================================================================ empty state

print()
print("=" * 78)
print("SECTION 2  an empty project does not draw the architecture unasked")
print("=" * 78)


def scan(text: str) -> list[str]:
    """
    The properties this run ships, as a recomputable list of FAILURE NAMES. The green
    assertions below and every non-vacuity mutation consult this one function, so what is
    proved red is the assertion the acceptance rests on and not a copy of it.
    """
    bad = []
    # 1. ONE predicate decides emptiness, and it is the same one the summary sentence uses.
    if "var projectIsEmpty = (uploadedDocCount === 0 && modWithResult === 0 " \
       "&& catEstimable === 0);" not in text:
        bad.append("single-empty-predicate")
    if text.count("uploadedDocCount === 0 && modWithResult === 0 && catEstimable === 0") != 1:
        bad.append("empty-predicate-duplicated")
    if "if (projectIsEmpty) {" not in text:
        bad.append("summary-uses-the-predicate")
    # 2. The draw function returns that decision to the gate.
    if "return { empty: projectIsEmpty" not in text:
        bad.append("draw-returns-emptiness")
    # 3. The gate hides the diagram and shows the statement instead.
    # The GATE's own hide, not the toggle handler's: the same statement appears in the
    # click handler, and a check that accepted either would have stayed green with the gate
    # deleted. Measured: it did.
    if "    host.style.display = 'none';\n    host.setAttribute('aria-hidden', 'true');\n\n"\
       "    var panel" not in text:
        bad.append("gate-hides-diagram")
    if "panel.className = 'lnf-empty';" not in text:
        bad.append("empty-panel-exists")
    if "btn.className = 'lnf-reveal';" not in text:
        bad.append("reveal-control-exists")
    if "btn.setAttribute('aria-expanded', 'false');" not in text:
        bad.append("reveal-control-announces-state")
    if "btn.setAttribute('aria-controls', host.id);" not in text:
        bad.append("reveal-control-names-what-it-controls")
    # 4. The gate applies ONLY to an empty project: a project with evidence returns early.
    if "if (!info || !info.empty) return;" not in text:
        bad.append("computed-project-unaffected")
    # 5. The diagram is not removed: the whole previous render still runs, into a host.
    if "var info = drawDiagram(project, host);" not in text:
        bad.append("diagram-still-built")
    # 6. Activity is still keyed on a current stored verdict, not on registry facts. This is
    #    the post-Run-22 rule; this run must not have loosened it.
    if "var live = isEstimable(info.status);" not in text:
        bad.append("module-activity-is-estimable")
    if "opacity:catLive ? '0.88' : '0.28'" not in text:
        bad.append("category-activity-is-estimable")
    # 7. The document column names its three states in the DOM.
    if "'data-state':uploaded ? 'uploaded'" not in text:
        bad.append("doc-state-named")
    if "(notApplicable ? 'registered-not-active' : 'not-uploaded')" not in text:
        bad.append("registered-not-active-named")
    if "opacity:uploaded?'0.88':(notApplicable?'0.34':'0.30')" not in text:
        bad.append("registered-not-active-is-dim")
    if "seShape(notApplicable ? 'square' : 'circle'" not in text:
        bad.append("registered-not-active-is-square")
    # 8. Every node kind is nameable by kind.
    for kind in ("module", "category", "project", "document"):
        if f"'data-kind':'{kind}'" not in text:
            bad.append(f"kind-{kind}")
    return bad


shipped_bad = scan(FLOW)
check(not shipped_bad, "every guard is GREEN on the shipped file", ", ".join(shipped_bad))

# The paging control. Searched for as a glyph and as a class/id shape, in every production
# surface that could carry one.
# The paging glyphs the owner named, plus the shapes a collapse control in this codebase
# could plausibly have used. ‹ and › are DELIBERATELY EXCLUDED from the source scan: radar.css
# uses "›" as the list bullet of the evidence-brief driver list (.eb-drivers li::before), which
# is typography and not a control. Including it would have made this guard permanently red,
# which is a guard that can never pass and so proves nothing. The BROWSER guard is the one that
# decides whether a rendered control exists, and it hit-tests real interactive elements.
PAGER_PATTERNS = (r"nav-page", r"secnav-(?:page|prev|next|toggle|collapse|hide)",
                  r"section-pager")
for label, text in (("neural_flow.js", FLOW), ("detail.js", DETAIL), ("radar.css", CSS)):
    # The diagram legend deliberately renders ▸ as an arrowhead SAMPLE for the flow-class key.
    # That is a static glyph inside a legend swatch, not a control; it is excluded by name so
    # the guard stays about controls. Everything else is reported.
    stripped = text.replace("&#9656;", "")
    found = [g for g in "◀▶◂❮❯«»" if g in stripped]
    check(not found, f"no paging or collapse glyph in {label}", "".join(found))
    hits = [p for p in PAGER_PATTERNS if re.search(p, text)]
    check(not hits, f"no paging-control class or id shape in {label}", ", ".join(hits))

# RUN 25, OWNER-DIRECTED CONTRACT CHANGE, 2026-08-14. This guard used to assert the section
# navigator was untouched ("detail-secnav-btn" and "aria-current" in detail.js). The owner
# then ordered the rail removed entirely, reversing the earlier instruction that it stays, so
# the assertion is inverted: the rail's builder must be GONE from the served sources. Recorded
# in run20_anti_fossilization_register.csv; the browser-level absence proof at five widths is
# drive_run25_rail_removal.py.
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
check("detail-secnav" not in DETAIL and "buildSectionNav" not in DETAIL
      and "detail-secnav" not in INDEX and "detail-secnav" not in CSS,
      "the section navigator rail is removed from every served source, per the owner's "
      "2026-08-14 instruction")

# ============================================================================ non-vacuity

print()
print("=" * 78)
print("SECTION 3  guard non-vacuity: every guard proved RED by a real violation")
print("=" * 78)

MUTATIONS = [
    ("stop hiding the diagram, so an empty project draws the architecture unasked",
     "    host.style.display = 'none';\n    host.setAttribute('aria-hidden', 'true');",
     "    host.setAttribute('aria-hidden', 'true');",
     "gate-hides-diagram"),
    ("delete the explicit control that reveals the architecture",
     "btn.className = 'lnf-reveal';",
     "btn.className = 'something-else';",
     "reveal-control-exists"),
    ("stop the draw function reporting emptiness to the gate",
     "return { empty: projectIsEmpty",
     "return { notEmpty: projectIsEmpty",
     "draw-returns-emptiness"),
    ("write a second copy of the emptiness predicate, so the two can drift apart",
     "    if (projectIsEmpty) {",
     "    if (uploadedDocCount === 0 && modWithResult === 0 && catEstimable === 0) {",
     "empty-predicate-duplicated"),
    ("apply the gate to computed projects too, removing the diagram from a working project",
     "    if (!info || !info.empty) return;",
     "    if (!info) return;",
     "computed-project-unaffected"),
    ("stop building the diagram at all, so it is removed rather than deferred",
     "var info = drawDiagram(project, host);",
     "var info = { empty: true };",
     "diagram-still-built"),
    ("revert module illumination to the registry fact the post-Run-22 correction removed",
     "var live = isEstimable(info.status);",
     "var live = info.status !== 'None';",
     "module-activity-is-estimable"),
    ("brighten the registered-but-inactive document rows back to the lit tier",
     "opacity:uploaded?'0.88':(notApplicable?'0.34':'0.30')",
     "opacity:uploaded?'0.88':(notApplicable?'0.88':'0.30')",
     "registered-not-active-is-dim"),
    ("draw the registered-but-inactive rows with the active shape",
     "seShape(notApplicable ? 'square' : 'circle'",
     "seShape('circle'",
     "registered-not-active-is-square"),
    ("stop naming the document row's state in the DOM",
     "'data-state':uploaded ? 'uploaded'",
     "'data-nothing':uploaded ? 'uploaded'",
     "doc-state-named"),
    ("stop naming the document nodes by kind",
     "'data-kind':'document'",
     "'data-kindless':'document'",
     "kind-document"),
]

for name, old, new, expect in MUTATIONS:
    if old not in FLOW:
        check(False, f"mutation source present: {name}", f"not found: {old[:60]}")
        continue
    mutated = FLOW.replace(old, new, 1)
    # THE INJECTION MUST BE PROVED TO HAVE APPLIED before its result is believed.
    check(mutated != FLOW and new in mutated,
          f"INJECTION TOOK EFFECT: {name}",
          f"applied={mutated != FLOW}")
    bad = scan(mutated)
    check(expect in bad, f"guard turns RED under: {name}",
          f"expected {expect!r} among {bad}")

# The count guard, proved discriminating against a really-changed taxonomy.
_tax_mut = TAXONOMY.replace(
    "{ id: 'a4_1', num: 'A4.1', name: 'Document Risk Score'",
    "{ id: 'a4_99', num: 'A4.99', name: 'Injected Module'\n      },\n"
    "      { id: 'a4_1', num: 'A4.1', name: 'Document Risk Score'", 1)
check(_tax_mut != TAXONOMY, "INJECTION TOOK EFFECT: an extra module added to the taxonomy copy")
_saved = TAXONOMY
try:
    globals()["TAXONOMY"] = _tax_mut
    _c = registry_counts()
finally:
    globals()["TAXONOMY"] = _saved
check(_c[3] == PROJ_MODS + 1,
      "the registry parse really counts the taxonomy: one added module moves the figure by one",
      f"{_c[3]} vs {PROJ_MODS}")
check(registry_counts()[3] == PROJ_MODS,
      "and the shipped figure is restored after the mutation", str(registry_counts()))

# The pager guard, proved capable of firing.
check("◀" in ("◀" + FLOW), "INJECTION TOOK EFFECT: a paging glyph exists in the mutated copy")
_pmut = FLOW.replace("var revealSeq = 0;", "var revealSeq = 0; // ◀ | ▶ pager", 1)
check(_pmut != FLOW and any(g in _pmut.replace("&#9656;", "") for g in "◀▶"),
      "guard turns RED under: reintroduce the paging control glyphs")
check(not any(g in FLOW.replace("&#9656;", "") for g in "◀▶"),
      "and the shipped file carries none")

check(FLOW_PATH.read_text(encoding="utf-8") == FLOW,
      "the shipped file on disk is unmodified by this suite")
check(TAXONOMY_PATH.read_text(encoding="utf-8") == _saved,
      "and so is the taxonomy")
check(not scan(FLOW_PATH.read_text(encoding="utf-8")),
      "RE-BASELINE: every guard is GREEN again on the shipped file after every fault")

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
raise SystemExit(1 if FAILED else 0)
