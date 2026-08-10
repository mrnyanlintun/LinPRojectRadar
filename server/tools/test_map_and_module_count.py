#!/usr/bin/env python3
"""
MapLibre is gone from the pages, and a project page counts only what a project has.

Run (from server/):

    PYTHONIOENCODING=utf-8 python tools/test_map_and_module_count.py

No database and no model key: every check reads a file in the repository, or the taxonomy the
browser reads, and asserts a property of it.

WHY THIS SUITE EXISTS RATHER THAN MORE CHECKS IN tests_render.html. The browser harness has its
own script list and never loads `index.html`, so an assertion there that `typeof maplibregl` is
"undefined" passes no matter what `index.html` does. That was MEASURED, not assumed: the maplibre
script tag was restored to `index.html` and the harness stayed green at 256/257. A check that
cannot fail is worse than no check, so the browser group now asserts what it can actually see
(the atlas renders into the Location section) and the file-level properties are pinned here,
where reading the file is the check.

THE TWO DEFECTS THIS GUARDS.

  The detail page showed no map. MapLibre was there to draw streets, streets come from
  `tiles.openfreemap.org`, and that host is refused at CONNECT by the network this platform runs
  on. Every reader downloaded 837 KB of library and got an empty panel. The atlas is the map now:
  vendored geometry, no tile host, no key, no external request.

  The detail page advertised 101 modules across 12 categories. That is the whole taxonomy. Group
  D is portfolio level, needs more than one project by definition, and its five modules all
  require `portfolioVectors`. A project has 96 across 11, which is what the Signal Flow diagram
  in the same page already read.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

ROOT = pathlib.Path(__file__).resolve().parents[2]

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def finish() -> None:
    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    sys.exit(1 if failed else 0)


def section(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# A live <script>/<link> reference to the library, as opposed to the word appearing in a comment.
_SCRIPT_TAG = re.compile(r"""<script[^>]+src\s*=\s*["'][^"']*maplibre[^"']*["']""", re.I)
_LINK_TAG = re.compile(r"""<link[^>]+href\s*=\s*["'][^"']*maplibre[^"']*["']""", re.I)
# A live use of the global, as opposed to the word in prose. `maplibregl.` or `maplibregl !==`
# or `new maplibregl`.
_GLOBAL_USE = re.compile(r"""(?<![\w.])maplibregl\s*(?:\.|\[|!==|===|==|\))""")


def strip_js_comments(src: str) -> str:
    """Source with // and /* */ comments removed, so prose cannot satisfy a code check."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", src)


def main() -> None:
    section("0. SELF-TESTS: EVERY DETECTOR IS PROVEN ABLE TO FAIL FIRST")

    check(bool(_SCRIPT_TAG.search('<script src="assets/vendor/maplibre-gl.min.js"></script>')),
          "the script-tag detector CATCHES a planted maplibre script tag")
    check(not _SCRIPT_TAG.search('<!-- maplibre-gl.min.js is not loaded -->'),
          "and does NOT fire on the word appearing in a comment")
    check(bool(_LINK_TAG.search('<link rel="stylesheet" href="assets/vendor/maplibre-gl.min.css">')),
          "the stylesheet detector catches a planted maplibre link tag")
    check(bool(_GLOBAL_USE.search("if (typeof maplibregl !== 'undefined') {}")),
          "the global-use detector catches a real use of the global")
    check(not _GLOBAL_USE.search("// MapLibre is not loaded; maplibregl is gone"),
          "and does NOT fire on prose mentioning it")
    check("x" not in strip_js_comments("/* x */\n// x\n"),
          "the comment stripper removes both comment forms")

    section("1. MAPLIBRE IS NOT LOADED BY THE APPLICATION PAGE")

    index = read("index.html")
    check(not _SCRIPT_TAG.search(index),
          "index.html loads no maplibre script",
          str(_SCRIPT_TAG.findall(index)))
    check(not _LINK_TAG.search(index),
          "and no maplibre stylesheet", str(_LINK_TAG.findall(index)))

    # The tile host has no business in the policy either, once nothing requests it. A CSP that
    # permits a host nothing uses is a standing permission for nothing.
    csp = next((ln for ln in index.splitlines() if "connect-src" in ln), "")
    check(bool(csp), "the page still declares a connect-src policy (the scan is not vacuous)",
          csp.strip()[:70])
    check("openfreemap" not in csp,
          "and it no longer permits the tile host", csp.strip()[:110])

    section("2. THE DETAIL PAGE CONSTRUCTS NO MAPLIBRE MAP")

    detail_src = strip_js_comments(read("assets/js/detail.js"))
    check(not _GLOBAL_USE.search(detail_src),
          "detail.js contains no live use of the maplibregl global",
          str(_GLOBAL_USE.findall(detail_src)[:4]))
    check("LinAtlas.render" in detail_src,
          "and it renders the atlas instead")
    # The atlas must be the map, not the thing reached after a failure. A `catch`-only path
    # would satisfy the check above while still needing something to fail first.
    # Anchored on the lazy-init entry, NOT the first '"d-globe"' in the file: that one is the
    # section MARKUP higher up, and slicing from it grabbed the wrong region entirely.
    globe_section = detail_src[detail_src.index('"d-globe": () =>'):]
    globe_section = globe_section[:globe_section.index('"d-docsignals"')]
    check("LinAtlas.render" in globe_section,
          "the Location section itself renders the atlas, on its own path")
    check("hasCoordsFor" in globe_section,
          "and still refuses to draw a marker for a project with no coordinates")

    section("3. THE PORTFOLIO WAS NEVER AFFECTED, AND STILL IS NOT")

    app_src = read("assets/js/app.js")
    # app.js keeps an unreachable MapLibre stage (see its "ORPHANED AS OF T11" note). It is not
    # removed here -- that is ~400 lines and its own change -- but it MUST stay unreachable, and
    # it must keep the guard that makes it harmless now the library is not loaded.
    check("ORPHANED AS OF T11" in app_src,
          "app.js still marks its MapLibre stage as orphaned")
    check('typeof maplibregl === "undefined"' in app_src,
          "and that dead path still guards on the global being absent, so it bails rather than "
          "throwing now that nothing loads it")
    stripped_app = strip_js_comments(app_src)
    check(stripped_app.count("buildMap()") <= 2,
          "buildMap has no new callers", str(stripped_app.count("buildMap()")))
    check("buildAtlasStage()" in stripped_app,
          "and the portfolio Map view still renders the atlas")

    section("4. A PROJECT PAGE COUNTS ONLY WHAT A PROJECT HAS")

    node = subprocess.run(
        ["node", "-e", """
        global.window = global;
        require(process.argv[1]);
        const all = LIN_CATEGORIES;
        const proj = window.projectLevelCategories();
        const sum = cs => cs.reduce((n,c)=>n+((c&&c.modules)||[]).length,0);
        console.log(JSON.stringify({
          allCats: all.length, allMods: sum(all),
          projCats: proj.length, projMods: sum(proj),
          projHasPortfolio: proj.some(c => c.level === 'portfolio' || c.portfolioLevel),
          parkedFilterKeepsD1: all.filter(c=>!c.parked).some(c=>c.id==='d1'),
          d1Modules: (all.filter(c=>c.id==='d1')[0]||{modules:[]}).modules.length
        }));
        """, str(ROOT / "assets/js/taxonomy.js")],
        capture_output=True, text=True)
    check(node.returncode == 0, "the taxonomy loads under node", node.stderr.strip()[:120])
    tx = json.loads(node.stdout.strip().splitlines()[-1])

    check(tx["allCats"] > tx["projCats"] and tx["allMods"] > tx["projMods"],
          "the taxonomy genuinely has a portfolio-level category to exclude "
          "(so the checks below are not vacuous)", json.dumps(tx))
    check(tx["projMods"] == 96, "a project has 96 modules", str(tx["projMods"]))
    check(tx["projCats"] == 11, "across 11 categories", str(tx["projCats"]))
    check(tx["allMods"] == 101 and tx["allCats"] == 12,
          "and the whole taxonomy is still 101 across 12, unchanged",
          f"{tx['allMods']}/{tx['allCats']}")
    check(tx["d1Modules"] == 5, "Portfolio Health keeps its five modules", str(tx["d1Modules"]))
    check(not tx["projHasPortfolio"],
          "and no portfolio-level category is in the project-level set")
    # The discriminator is the LEVEL, not `parked`. A fallback in detail.js used `!parked` and
    # therefore leaked Portfolio Health; this records why that was wrong.
    check(tx["parkedFilterKeepsD1"],
          "filtering on 'parked' would NOT exclude Portfolio Health, which is why every filter "
          "here uses the level")

    section("5. NO PROJECT SURFACE COUNTS THE WHOLE TAXONOMY")

    # The defect was `LIN_CATEGORIES.length` / `LIN_CATEGORIES.reduce(...modules...)` on a page
    # that shows ONE project. detail.js is that page.
    detail_raw = read("assets/js/detail.js")
    stripped_detail = strip_js_comments(detail_raw)
    bad_len = re.findall(r"LIN_CATEGORIES\.length", stripped_detail)
    bad_sum = re.findall(r"LIN_CATEGORIES\.reduce", stripped_detail)
    # Self-test: the pattern really does match the shape it is looking for.
    check(bool(re.findall(r"LIN_CATEGORIES\.length", "x = LIN_CATEGORIES.length;")),
          "self-test: the unfiltered-count pattern matches the shape it hunts")
    check(not bad_len,
          "detail.js counts no categories off the whole taxonomy", str(bad_len))
    # One `reduce` survives, inside `buildModuleAxes`, which is DEAD: it is defined and never
    # called anywhere in the repository. Left alone deliberately, and named here so it is a
    # recorded fact rather than an oversight.
    check(len(bad_sum) <= 1,
          "and at most the one known dead site sums modules off it", str(bad_sum))
    if bad_sum:
        called = subprocess.run(
            ["grep", "-rn", "buildModuleAxes", str(ROOT / "assets/js")],
            capture_output=True, text=True).stdout
        callers = [ln for ln in called.splitlines()
                   if "function buildModuleAxes" not in ln and "//" not in ln.split(":", 2)[-1]]
        check(not callers,
              "and that site is unreachable: buildModuleAxes has no callers",
              str(callers)[:150])

    check("projectCats()" in stripped_detail and "projectModuleCount()" in stripped_detail,
          "the page routes its counts through the project-level helpers instead")

    section("6. THE LEDGER RENDERS NO PORTFOLIO-LEVEL ROW ON A PROJECT PAGE")

    check("cat-row-health" not in stripped_app,
          "app.js builds no Portfolio Health row in the project ledger")
    check("rest of the portfolio" not in stripped_app,
          "and no 'rest of the portfolio' note is emitted from live code")
    check("projectLevelCategories" in stripped_app,
          "the ledger still selects project-level categories explicitly")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — a crash must print a FAILING result line
        import traceback
        traceback.print_exc()
        check(False, f"suite crashed: {type(exc).__name__}: {exc}")
    finish()
