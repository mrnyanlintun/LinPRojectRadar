#!/usr/bin/env python3
"""
RUN 63. THE FOUR CHARTS: SOURCE-LEVEL GUARDS OVER WHAT EACH ONE READS.

The browser-side behaviour is measured live by server/tools/drive_run63_four_charts.py, which
builds a fixture in PRJ-001's shape -- documents uploaded, `resetsignals`, then
`projectcomputeall`, which writes a fresh live row WITHOUT appending any new
`signals_extracted` event -- and reads the rendered DOM. This file guards the things a browser
harness can silently stop exercising.

EVERY CHECK IS PINNED TO THE SITE IT IS ABOUT, not to a name that appears anywhere in the file.
Run 61's F7 and Run 62's first draft were both caught staying green when the real render site
was deleted, so each check below was proved by deleting the exact construct it names.
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


NF = text("assets/js/neural_flow.js")
DET = text("assets/js/detail.js")
PN = text("assets/js/projectnet2d.js")


def strip_js_comments(src: str) -> str:
    out = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    return re.sub(r"//[^\n]*", "", out)


NF_CODE = strip_js_comments(NF)
DET_CODE = strip_js_comments(DET)

# ============================================================================================
# ORDER SECTION 8, GUARANTEE 2. THE SIGNAL FLOW AND THE DOCUMENTS PANEL COUNT ONE SET.
# ============================================================================================
# Pinned to the CALL, on an executable line. A mention in a comment is not a call, and the old
# private counter is what this replaced, so its absence is asserted too.
check("the Signal Flow calls the Documents panel's own document reader",
      "currentDocs = LinDetail.uploadedDocEvents(project) || [];" in NF_CODE,
      "neural_flow.js no longer calls LinDetail.uploadedDocEvents; it is counting its own set")
check("detail.js exports that reader on LinDetail",
      "window.LinDetail = { render, teardown, __resetMapForTest, uploadedDocEvents };" in DET_CODE,
      "detail.js no longer exports uploadedDocEvents, so the diagram cannot share its source")
check("the Signal Flow no longer counts documents from the since-the-reset event window",
      "if (ty !== 'signals_extracted') return;\n        uploadedDocCount++;" not in NF_CODE,
      "the reset-window document counter is back in neural_flow.js")
check("the Signal Flow's document count is gated on a LIVE stored row, not on the reset marker",
      "hasCurrentRow = !!(window.LinResults && LinResults.rowFor(project));" in NF_CODE,
      "neural_flow.js no longer decides currency from the stored row")
check("a project with no live row still reports no current documents (Run 18 stays fixed)",
      "if (hasCurrentRow) {" in NF_CODE,
      "the document set is filled unconditionally; a cleared, un-recomputed project would light")

# ORDER SECTION 8, GUARANTEE 1. The type count is derived from that same document list.
check("the document TYPE set is filled only from the current document list",
      "if (e && e.docType) uploadedNorm[normKey(e.docType)] = true;" in NF_CODE,
      "neural_flow.js no longer derives its document types from the shared document list")
check("the type set is no longer seeded from the absent legacy client blob",
      "if (project.signalInputs && project.signalInputs.sources) {\n      Object.values"
      not in NF_CODE,
      "neural_flow.js is seeding uploadedNorm from project.signalInputs again; that blob is "
      "absent on every server-computed project, which is why the type count read zero")

# ============================================================================================
# ORDER SECTION 8, GUARANTEE 3. THE THREE ACCOUNTS OF STATUS AGREE, BECAUSE THEY READ ONE ROW.
# ============================================================================================
# Pinned to the arm that replaced the browser-side fusion. Deleting the `return 'None';` line
# (or restoring worstStatus in its place) fails this check.
_cat_arm = re.search(
    r"var catStatuses = CATS\.map\(function\(cat, ci\) \{(.*?)\n    \}\);", NF_CODE, re.S)
check("the Signal Flow derives no category status the stored row does not carry",
      _cat_arm is not None and "worstStatus(" not in _cat_arm.group(1)
      and "return 'None';" in _cat_arm.group(1),
      "neural_flow.js recomputes a category status in the browser again; the Project Signal "
      "Network reads the row and the two surfaces would disagree about one row")
check("the Project Signal Network still reads the stored category status and derives nothing",
      "if (window.getCategoryStatus) return window.getCategoryStatus(catId, project) || null;" in PN,
      "projectnet2d.js no longer reads getCategoryStatus")
check("both surfaces take their category list from the same derivation",
      "window.projectLevelCategories ? window.projectLevelCategories()" in NF_CODE
      and "window.projectLevelCategories ? window.projectLevelCategories()" in PN,
      "the two surfaces no longer build their category list the same way")

# ============================================================================================
# ORDER SECTION 8, GUARANTEE 5. EVERY CHART READS THE PERIOD THE PAGE HOLDS.
# ============================================================================================
# rowFor(project) asks taxonomy.js for `project.storedResult.period` and refuses any other, so
# a surface that reads a row through rowFor reads the page's period by construction. The two
# surfaces that had never been on that path are pinned here.
check("the Signal Flow reaches the stored row through LinResults.rowFor",
      "LinResults.rowFor(project)" in NF_CODE,
      "neural_flow.js does not go through the period-aware row reader")
check("the served source_documents record is grafted so rowFor can answer with it",
      "p.storedResult.source_documents = resp.result.source_documents;" in DET_CODE,
      "detail.js no longer grafts source_documents; rowFor(p).source_documents is undefined "
      "on every detail page, which the Run 63 driver measured in the browser")

# ============================================================================================
# ORDER SECTION 8, GUARANTEE 4. NO TYPED LITERAL WHERE A DERIVED COUNT BELONGS.
# ============================================================================================
for rel, src in (("assets/js/neural_flow.js", NF_CODE),
                 ("assets/js/projectnet2d.js", strip_js_comments(PN)),
                 ("assets/js/detail.js", DET_CODE)):
    hits = [f"{rel}:{i}" for i, line in enumerate(src.splitlines(), 1)
            if re.search(r"['\"]\s*(63|101|11|27)\s+(modules?|categor|supported|in service)",
                         line, re.I)]
    check(f"no typed platform count in a rendered string in {rel}", not hits, "; ".join(hits))

# The 27 document types the Signal Flow announces are the server's list, not a client opinion.
sys.path.insert(0, str(ROOT / "server"))
from app.extraction_fields import DOC_TYPES  # noqa: E402
_m = re.search(r"var DOC_KEYS = \[(.*?)\];", NF, re.S)
_keys = re.findall(r"'([a-z_]+)'", _m.group(1)) if _m else []
check("the Signal Flow's document-type list is exactly the server's DOC_TYPES",
      sorted(_keys) == sorted(DOC_TYPES),
      f"client {len(_keys)} vs server {len(DOC_TYPES)}; "
      f"only-client={sorted(set(_keys) - set(DOC_TYPES))} "
      f"only-server={sorted(set(DOC_TYPES) - set(_keys))}")
check("and its rendered count is that list's length, not a number",
      "DOC_KEYS.length + ' SUPPORTED DOCUMENT TYPES'" in NF_CODE,
      "the Signal Flow no longer derives its document-type count from DOC_KEYS")

# ============================================================================================
# ORDER SECTION 8, GUARANTEES 10 - 12. THE DERIVED PLATFORM FIGURES, ASSERTED LIVE.
# ============================================================================================
from app.simulation.registry import (registry_index, service_index,  # noqa: E402
                                     CORE_VOTING_MODULES)
check("registry total is 101", len(registry_index()) == 101, str(len(registry_index())))
check("modules in service is 63", len(service_index()) == 63, str(len(service_index())))
check("voting modules are exactly A1.7 and A1.8",
      sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"], str(sorted(CORE_VOTING_MODULES)))
_unresolved = [mid for mid in registry_index() if registry_index().get(mid) is None]
check("every runtime lookup across all 101 registered modules resolves",
      not _unresolved and len(registry_index()) == 101, str(_unresolved))

# ============================================================================================
# ORDER SECTION 8, GUARANTEE 6. THE RUN 61 RULE STILL BINDS THIS RUN'S OWN DRIVER.
# ============================================================================================
DRV = text("server/tools/drive_run63_four_charts.py")
check("this run's browser driver does not prime a row before rendering",
      not [1 for line in strip_js_comments(DRV).splitlines()
           if re.search(r"LinResults\s*\.\s*prime\s*\(", line)],
      "drive_run63_four_charts.py primes before rendering, the one order in which the defect "
      "cannot appear")
check("this run's browser driver drives the real load path",
      "LinDetail && LinDetail.render(id)" in DRV,
      "drive_run63_four_charts.py no longer renders through LinDetail.render")
check("this run's browser driver opens the WebGL panels one at a time",
      "for sec in ORDER:" in DRV and "page.wait_for_timeout(6000)" in DRV,
      "the driver opens panels together; Run 61 lost a session to three at once")

print(f"checks: {CHECKS}")
print(f"RESULT: {CHECKS - len(FAILURES)}/{CHECKS} checks passed")
if FAILURES:
    print(f"FAILURES: {len(FAILURES)}")
    for f in FAILURES:
        print("  " + f)
sys.exit(1 if FAILURES else 0)
