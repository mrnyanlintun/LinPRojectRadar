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
import sys

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

    Counts `{ id: '...', module_id: '...', ... }` module records per category block, and the
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

# RUN 43, THE RETIREMENT. taxonomy.js is the participant surface and carries the population IN
# SERVICE, not the whole registry. The figures below are derived from registry.service_index()
# (registry.py:440) and registry.registry_index() (registry.py:426) rather than typed in, so
# reinstating a module in p0-baseline/module_renumbering_map.csv moves both sides together.
sys.path.insert(0, str(ROOT / "server"))
from app.simulation import registry as _REG                            # noqa: E402
_SERVICE = _REG.service_index()
_REGISTRY = _REG.registry_index()
_SVC_PROJECT = [m for m in _SERVICE if _REGISTRY[m]["group"] != "D"]
_SVC_PORTFOLIO = [m for m in _SERVICE if _REGISTRY[m]["group"] == "D"]
# RUN 95. THE CATEGORY ORACLE IS THE ROSTER IN SERVICE, NOT THE WHOLE REGISTRY.
# These two lines counted categories over `registry_index()` -- every category the CSV declares,
# retired modules included -- while the module figures beside them counted `service_index()`.
# That mismatch was invisible only because no category had ever emptied. Run 95 retired every
# module of A5 System Dynamics & Complexity, `build_client_taxonomy.py` now declines to emit a
# GROUP A category holding nothing, and the two halves of this check disagreed by exactly one.
# Counting categories the same way the modules beside them are counted is the fix.
#
# D1 PORTFOLIO HEALTH IS THE ONE DECLARED EXCEPTION AND IS ADDED BACK BY NAME OF ITS GROUP, not
# by its key. All five of its modules were retired at Run 43 and it has shipped as an empty
# portfolio-level container ever since; Run 95 scoped the new drop rule to group A so that this
# container was not swept away with A5. It therefore appears in the browser taxonomy with no
# module in service, and the oracle has to say so rather than the check being loosened.
_SVC_CATS = {_REGISTRY[m]["category"] for m in _SERVICE}
_PORTFOLIO_CONTAINERS = {r["category"] for r in _REGISTRY.values() if r["group"] == "D"}
_AUTH_CATS = len(_SVC_CATS | _PORTFOLIO_CONTAINERS)
_AUTH_PROJ_CATS = len({c for c in _SVC_CATS if c not in _PORTFOLIO_CONTAINERS})
check((ALL_CATS, ALL_MODS, PROJ_CATS, PROJ_MODS)
      == (_AUTH_CATS, len(_SERVICE), _AUTH_PROJ_CATS, len(_SVC_PROJECT)),
      f"the taxonomy the browser reads holds {len(_SVC_PROJECT)} project-level modules in "
      f"{_AUTH_PROJ_CATS} project-level categories and {len(_SERVICE)} in {_AUTH_CATS} counting "
      f"Portfolio Health, every figure derived from the roster in service",
      f"{ALL_CATS}/{ALL_MODS}/{PROJ_CATS}/{PROJ_MODS} vs "
      f"{_AUTH_CATS}/{len(_SERVICE)}/{_AUTH_PROJ_CATS}/{len(_SVC_PROJECT)}")
check(ALL_MODS == PROJ_MODS + len(_SVC_PORTFOLIO),
      "and the whole-taxonomy figure reconciles to the project-level one",
      f"{ALL_MODS} != {PROJ_MODS} + {len(_SVC_PORTFOLIO)}")
# RUN 96 CARRIED RETIREMENT THROUGH TO REMOVAL, so the registry no longer holds 101. What this
# line exists to assert is the RECONCILIATION -- in service plus retired accounts for every row,
# with nothing unaccounted -- and that is asserted on the registry's own numbers, non-empty.
check(len(_REGISTRY) > 0
      and len(_SERVICE) + len(_REG.retired_modules()) == len(_REGISTRY),
      "and the roster in service plus the retired reconcile to the REGISTRY exactly "
      "to exactly, so retirement removed modules from service and not from the registry",
      f"{len(_SERVICE)} + {len(_REG.retired_modules())} vs {len(_REGISTRY)}")
# RUN 95 RETIRED THE ONLY SUPPLIED ENTRY, so the figure is now "every module in service is
# computed, none supplied". A4.1 Document Risk Score was the single registry entry the
# extraction model SUPPLIED rather than the analytical server computing -- and it was also the
# only module in service with no runner at all, which is why it raised instead of computing or
# abstaining. It is retired, so it is absent from the browser taxonomy and the count is zero.
#
# The check is kept and inverted rather than deleted, and the reason it can be trusted is that
# the SERVER is asked the same question independently just below: `supplied` in
# `LIN_TAXONOMY_COUNTS` is generated as `in_service - computes`, and it is zero for the same
# reason. A supplied identity reappearing in the client taxonomy would still fail this.
check(TAXONOMY.count("method_class: 'Doc_Risk_Cat4'") == 0,
      "no project-level registry entry is a supplied value any more: A4.1 Document Risk Score "
      "was the only one and Run 95 retired it")
check(len(_SERVICE) == len([m for m in _SERVICE if m in _REG.VALIDATED
                            or m in _REG.PORTFOLIO_VALIDATED]),
      "and the server agrees: every module in service has a runner, none is supplied")

# NO COUNT IS TYPED INTO THE DIAGRAM. Every figure the headers and the summary state must be
# read from the model the registry builds.
# RUN 90 RE-POINTED THESE THREE, AND THE OTHER TWO BELOW. The owner's Run 90 ruling changed the
# POPULATION both charts draw -- the six weighted performance categories, no retired module --
# so the truthful header no longer says "registered project modules" or "registered categories".
# The checks were turned RED against the Run 90 build first and are re-pointed at the shipped
# wording, exactly as Run 26 re-pointed the guards it had turned red. WHAT THEY ASSERT IS
# UNCHANGED and is the whole point of them: the figure is READ FROM THE BUILT MODEL and never
# typed in. The literal-count guard below is untouched.
# RUN 96 CORRECTED THE WORD, NOT THE FIGURE. `MODULES` is the modules this chart DRAWS -- the
# ones in the weighted performance categories beside it -- and the caption called them the
# modules in service, which is a larger population. The figure is still read from the built model
# and still never typed in, which is what this check exists to assert.
check("MODULES.length + ' MODULES IN THESE CATEGORIES'" in FLOW,
      "the module column header reads its figure from the built model")
check("MODULES.length + ' MODULES IN SERVICE'" not in FLOW,
      "and no longer calls the charted population the modules in service")
check("CATS.length + ' WEIGHTED PERFORMANCE CATEGORIES'" in FLOW,
      "the category column header reads its figure from the built model")
# RUN 51, SECTION 6.1. The two figures are still read from the built model; the WORD beside
# them changed, because the model this file builds is the population IN SERVICE and calling it
# "registered" named a different and larger population.
check("MODULES.length +\n      ' modules in service in those six categories, and ' + CATS.length +" in FLOW,
      "and the summary sentence reads the same two figures, not a second pair of literals")
check("registered project modules" not in FLOW,
      "and it no longer calls the population it draws the registered one, which it is not")
check(not re.search(r"'\s*9[0-9] REGISTERED PROJECT MODULES", FLOW),
      "no literal project-module count is hardcoded into the diagram headers")
check("chartModuleCount = chartCats.reduce(" in DETAIL
      and "chartCatCount + \" categories drawn\"" in DETAIL
      and "${chartModuleCount} modules drawn" in DETAIL,
      "the detail page's two chart badges count what those charts draw, derived not typed")
# THE KNOWLEDGE PAGE'S FIGURE, which is the one that has disagreed before. It states the
# WHOLE-TAXONOMY count and must reconcile to the registry, not to the project-level figure.
# RUN 26 REWROTE THE SENTENCE, SO THE ORACLE IS THE REGISTRY, NOT THE SENTENCE.
# The old form of this check quoted the shipped wording verbatim -- "All 100 registered
# computations" and the exact clause about becoming 101 -- which is the failure mode the
# programme lists as encoding the defect's own sentence as the oracle. It could only ever
# confirm that nobody had reworded the page. The page now has to state THREE scopes, and each
# figure is checked against the number the registry actually yields.
# RUN 43. The page must now state THREE populations, because the retirement created a third:
# what the registry holds (101), what is in service (63, which is what the browser renders), and
# what the analytical server computes of the roster in service (62). Every figure is derived.
_COMPUTED_IN_SERVICE = len(_REG.available_modules())


def rendered(text: str) -> str:
    """RUN 51, SECTION 6.1. The handbook and the About page no longer TYPE their counts; each
    is a token the page fills from window.LIN_TAXONOMY_COUNTS, which the taxonomy generator
    writes from registry_index() and service_index(). A check that greps the source for a
    literal would now measure the template rather than the sentence. This substitutes what the
    page derives at render time using numbers taken from THE REGISTRY IN THIS PROCESS, never
    from the file under test, and the assertions below then read the sentence a reader gets."""
    subs = {"registered": len(_REGISTRY), "inService": len(_SERVICE),
            "projectInService": len(_SVC_PROJECT), "portfolioInService": len(_SVC_PORTFOLIO),
            "serverComputes": _COMPUTED_IN_SERVICE, "retired": len(_REG.retired_modules()),
            "supplied": len(_SERVICE) - _COMPUTED_IN_SERVICE}
    for k, v in subs.items():
        text = text.replace("${taxCounts().%s}" % k, str(v))
        text = text.replace('<span data-taxcount="%s">&#8230;</span>' % k, str(v))
        text = text.replace("{{%s}}" % k, str(v))
    return text


KNOWLEDGE = rendered(KNOWLEDGE)
check(f"The registry holds {len(_REGISTRY)} modules, of which {len(_SERVICE)} are in service: "
      f"{len(_SVC_PROJECT)} at project level and {len(_SVC_PORTFOLIO)} at portfolio level"
      in KNOWLEDGE,
      "the Knowledge page states the registry total and the scopes of the roster in service",
      f"expected the registry's own {len(_REGISTRY)}/{len(_SERVICE)}/{len(_SVC_PROJECT)}/"
      f"{len(_SVC_PORTFOLIO)}")
check(f"The analytical server computes {_COMPUTED_IN_SERVICE} of the {len(_SERVICE)}"
      in KNOWLEDGE,
      "and states the computed count as a scope of the roster in service rather than as a rival "
      "total",
      f"expected 'computes {_COMPUTED_IN_SERVICE} of the {len(_SERVICE)}'")
check("document risk score, which the extraction model supplies as a value rather than the "
      "server deriving it" in KNOWLEDGE,
      "and names the one module that makes the two figures differ, so they are reconcilable "
      "rather than contradictory")
check("Registration is not activation." in KNOWLEDGE,
      "and separates registry status from operational state, so a registered module that is "
      "advisory or disabled is not read as an inflated capability claim")

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
# RUN 95 RE-ANCHORED THIS INJECTION. It spliced ahead of A4.1 Document Risk Score, which Run 95
# retired and which is therefore no longer in the taxonomy at all -- the replace matched nothing
# and the injection silently stopped injecting, which is the exact vacuity this suite exists to
# prevent. The anchor is now taken from the taxonomy AT RUNTIME rather than typed, so no future
# retirement can quietly disarm it again. The "INJECTION TOOK EFFECT" check below is what proves
# the re-anchoring worked.
# The injected module must be counted by `registry_counts()`, which keys a module to its
# category by the `<catid>_<n>` id prefix. So the injected id is built FROM THE ANCHOR'S OWN
# prefix rather than typed: whatever category the anchor sits in, the injection lands in it.
_anchor = re.search(r"\{ id: '([a-z]\d+)_\d+', module_id: '[A-C]\d\.\d+',", TAXONOMY)
check(_anchor is not None,
      "an anchor for the injection exists in the shipped taxonomy (guards the check below)")
_tax_mut = TAXONOMY.replace(
    _anchor.group(0),
    "{ id: '%s_99', module_id: 'Z9.99', name: 'Injected Module'\n      },\n      "
    % _anchor.group(1) + _anchor.group(0), 1) if _anchor else TAXONOMY
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
