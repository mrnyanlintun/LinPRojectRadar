#!/usr/bin/env python3
"""
POST-RUN-22 UI CORRECTION. THE SOURCE-LEVEL GUARDS FOR SIGNAL-FLOW EMPTY-STATE TRUTHFULNESS
AND FOR THE SIGNALS NAVIGATION.

WHAT THIS FILE IS FOR, AND WHAT IT IS NOT. The behaviour itself is qualified in a real browser
by `tools/drive_run23_signal_flow_ui.py`, which drives an empty project, a one-document project,
a multi-document project, a reset, a hard reload and a project switch, reads the shipped
active-state markers out of the served DOM, and proves its own guard RED against a forced
active node. That driver needs Chromium and therefore cannot live in the `test_*.py` glob. This
file is the part that CAN run in every suite sweep: it pins, in the shipped source, the rules
the browser evidence established, so a later edit that reintroduces the defect fails here even
when no browser is available.

THE DEFECT BEING PINNED. On a brand-new EMPTY project the Signal Flow lit nine module dots at
the active opacity tier with a glow filter, and three document rows at 0.75, because the
illumination was keyed on `status !== 'None'`. 'NotRelevant' -- a module disabled platform-wide
or excluded by sector, and a document type editorially marked as absent from the corpus -- is
not 'None'. Those are REGISTRY facts. The rule is now `isEstimable(status)`: a current stored
verdict, and nothing else, reaches the active tier.

Every check below is written so that reverting the production change fails it.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
FLOW = (ROOT / "assets" / "js" / "neural_flow.js").read_text(encoding="utf-8")
DETAIL = (ROOT / "assets" / "js" / "detail.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "css" / "radar.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")

passed = 0
total = 0
failures: list[str] = []


def check(cond: bool, name: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if cond:
        passed += 1
    else:
        failures.append(name + (f"  [{detail}]" if detail else ""))


# ---------------------------------------------------------------- 1. activity is estimability

check("function isEstimable(s)" in FLOW,
      "the diagram still defines the single estimability predicate the whole file decides "
      "activity with")

# The four node kinds, each read as its own slice of the file so a rule proved for one cannot
# stand in for another.
mod_block = FLOW[FLOW.index("var modNodeEls = MODULES.map"):FLOW.index("// Category nodes")]
check("var live = isEstimable(info.status);" in mod_block,
      "a module dot's active state is decided by isEstimable, not by a registry fact")
check("info.status !== 'None' ? 'url(#lnf-glow-" not in mod_block,
      "and the old status-is-not-None illumination rule is gone from the module dots")
check("var glow = live ? 'url(#lnf-glow-'" in mod_block,
      "a module dot glows only when it is live")
check(re.search(r"opacity:live \? '0\.85'", mod_block) is not None,
      "and only a live module dot reaches the active opacity tier")
check("'data-active':live ? 'true' : 'false'" in mod_block,
      "the module dot records its activity decision in the DOM as data-active")

cat_block = FLOW[FLOW.index("var catNodeEls = CATS.map"):FLOW.index("// Project Status node")]
check("var catLive = isEstimable(cs);" in cat_block,
      "a category node is active only when the app's own fusion returns a current verdict")
check("cs==='None'?'0.28':'0.88'" not in cat_block,
      "and a registered-but-silent category no longer reaches the active tier")
check("'data-active':catLive ? 'true' : 'false'" in cat_block,
      "the category node records its activity decision as data-active")

# RUN 26. The block boundary moved with the governance feedback arc, which was removed. The
# marker used here is the next section the file actually contains.
prj_block = FLOW[FLOW.index("// Project Status node"):FLOW.index("// Document nodes (rendered last")]
check("prjEstimable ? 'url(#lnf-glow-'" in prj_block,
      "the governed decision node glows only when the rollup it shows is estimable")
check("opacity:prjEstimable ? '0.92' : '0.26'" in prj_block,
      "and it is dimmed when the project has no current result")

doc_block = FLOW[FLOW.index("// Document nodes (rendered last"):FLOW.index("8. Architecture-versus-activity summary")]
check("uploaded?'0.88':(notApplicable?'0.34':'0.30')" in doc_block,
      "a document row that was never uploaded stays below the active tier, including the "
      "not-applicable rows that were drawn at 0.75")
# RUN 26, OWNER-DIRECTED CONTRACT CHANGE, 2026-08-14. The tier above still governs a project
# that HAS evidence. On an EMPTY project the not-applicable branch is not reached at all: the
# owner's instruction forbids a purple document square there, so `notApplicable` is additionally
# gated on the project not being empty. The old contract is not loosened, it is inverted for the
# one case the owner named. Recorded in run20_anti_fossilization_register.csv.
check("!uploaded && !projectIsEmpty && !!DOC_NOT_APPLICABLE[key]" in doc_block,
      "and on an empty project the not-applicable branch is not reached, so no purple square "
      "is drawn where there is no evidence for it to be a distinction from")
check("'data-active':uploaded ? 'true' : 'false'" in doc_block,
      "a document row's activity is its upload state and says so in the DOM")
check("uploaded ? 'url(#lnf-glow-DocOn)' : null" in doc_block,
      "and only an uploaded document row glows")

# The upload window is still the reset-bounded one Run 18 established: activity must never be
# reintroduced from the whole event log.
check("sinceReset" in FLOW and "signals_reset" in FLOW,
      "the current-activity window is still bounded by the last reset")

# NON-VACUITY OF THE SOURCE GUARDS THEMSELVES. Each rule above is checked against the exact
# string the defect had, so a revert cannot pass by rewording.
for old in ("opacity:info.status==='None'?'0.20':'0.85'",
            "cs !== 'None' ? 'url(#lnf-glow-'+cs+')' : null",
            "prjStatus !== 'None' ? 'url(#lnf-glow-'+prjStatus+')' : null",
            "uploaded?'0.88':(notApplicable?'0.75':'0.30')",
            # RUN 26. The two the owner's 2026-08-14 empty-project rule retires: the
            # ungated not-applicable branch, and the red governance arc.
            "notApplicable = !uploaded && !!DOC_NOT_APPLICABLE[key]",
            "stroke:COL.Red, 'stroke-width':'1.5', opacity:'0.30'"):
    check(old not in FLOW,
          f"the pre-correction illumination rule {old!r} is absent from the shipped diagram")

# ---------------------------------------------------------------- 2. selected is not active

# RUN 25, OWNER-DIRECTED CONTRACT CHANGE, 2026-08-14. Sections 2 and 3 of this suite guarded
# the rail's selection vocabulary (`selected`/`aria-current`, never `active`) and its mobile
# layout. The owner then ordered the LEFT RAIL REMOVED ENTIRELY, reversing the earlier
# instruction that it stays, so there is no rail to publish a selection and no rail to
# survive mobile. The vocabulary property those sections protected is preserved in its only
# remaining form: no rail code exists at all, so no navigation state can ever be spelt with
# the Signal Flow's analytical word. Recorded in run20_anti_fossilization_register.csv;
# browser-level absence proof at five widths is drive_run25_rail_removal.py.
check("buildSectionNav" not in DETAIL and "data-secnav-target" not in DETAIL,
      "the rail builder and its selection machinery are gone from detail.js")
check("detail-secnav" not in CSS,
      "and every rail style, desktop and mobile, is gone from the stylesheet")
check("detail-secnav" not in INDEX,
      "and the served page carries no rail element")
# The reset must not blank the append-only event log client-side: that mask made the live page
# deny retained documents the reloaded page correctly disclosed. Unrelated to the rail and
# kept exactly as Run 23 wrote it.
check("p.events = [];" not in DETAIL and "p.history = []; p.events" not in DETAIL,
      "the reset no longer blanks the event log in the browser copy")
# No collapse or paging control has appeared anywhere in the two files that carried the rail.
for token in ("secnav-toggle", "secnav-collapse", "secnav-hide", "nav-page", "section-pager"):
    check(token not in DETAIL and token not in CSS, f"no {token} control exists")
# NON-VACUITY: a copy of the stylesheet with one rail rule reinserted fails the exact
# predicate used above.
_css_mut = CSS + "\n.detail-secnav { position: fixed; }\n"
check("detail-secnav" in _css_mut and _css_mut != CSS,
      "INJECTION TOOK EFFECT: the mutated stylesheet carries a rail rule")
check(not ("detail-secnav" not in _css_mut),
      "and the absence predicate goes RED on that copy, so it can fail")

# ---------------------------------------------------------------- 4. the superseding freeze

import hashlib  # noqa: E402
import subprocess  # noqa: E402

_run22 = ROOT / "code_audit" / "run22_production_tree.sha256"
_run23 = ROOT / "code_audit" / "run23_production_tree.sha256"
check(_run22.is_file() and _run23.is_file(),
      "both the Run-22 manifest and the superseding one exist")
_git22 = subprocess.run(["git", "-C", str(ROOT), "show",
                         "7226a59:code_audit/run22_production_tree.sha256"],
                        capture_output=True, text=True)
check(_git22.returncode == 0 and _git22.stdout == _run22.read_text(encoding="utf-8"),
      "the Run-22 manifest is preserved byte-for-byte as it stood at the starting commit: the "
      "supersession does not rewrite historical evidence")


def _rows(path):
    return {ln.partition("  ")[2]: ln.partition("  ")[0]
            for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}


_a, _b = _rows(_run22), _rows(_run23)
check(set(_a) == set(_b),
      "the superseding manifest names exactly the same production files: this correction added "
      "and removed none", str(sorted(set(_a) ^ set(_b))))
_moved = sorted(k for k in _a if _a[k] != _b[k])
check(_moved == ["assets/css/radar.css", "assets/js/detail.js", "assets/js/neural_flow.js"],
      "and the ONLY files whose bytes moved are the three declared UI files", str(_moved))

for f in failures:
    print("FAILED:", f)
print(f"RESULT: {passed}/{total} checks passed")
raise SystemExit(0 if passed == total else 1)
