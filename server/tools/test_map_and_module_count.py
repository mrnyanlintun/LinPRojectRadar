#!/usr/bin/env python3
"""
MapLibre is gone from the pages entirely, BOTH map surfaces are Google Maps keyed from the
environment (the detail street map and the portfolio Map view, sharing one loader), the flat atlas
is removed, and a project page counts only what a project has.

Run (from server/):

    PYTHONIOENCODING=utf-8 python tools/test_map_and_module_count.py

No database and no model key: every check reads a file in the repository, or the taxonomy the
browser reads, and asserts a property of it.

WHY THIS SUITE EXISTS RATHER THAN MORE CHECKS IN tests_render.html. The browser harness has its
own script list and never loads `index.html`, so an assertion there that `typeof maplibregl` is
"undefined" passes no matter what `index.html` does. That was MEASURED, not assumed: the maplibre
script tag was restored to `index.html` and the harness stayed green at 256/257. A check that
cannot fail is worse than no check, so the browser group asserts what it can actually see (the
map host renders into the Location section) and the file-level properties are pinned here, where
reading the file is the check.

WHAT CHANGED 2026-08-10, AND ONE RED THAT RECORDED A DEFECT RATHER THAN A PROPERTY. The previous
session left MapLibre as an unreachable ~400-line stage in app.js, guarded so it could not run,
plus 837 KB of vendored library on disk. This session removed the stage, the vendored files, the
CSS and the `.map-wrap` markup outright, and gave the detail page a real street map through the
Google Maps JavaScript API keyed from `GOOGLE_MAPS_BROWSER_KEY`. Section 3 here USED to assert
"app.js still marks its MapLibre stage as orphaned" and "still guards on the global being absent"
— it went red because the stage it was protecting no longer exists. That red recorded the
intermediate state, not a property worth keeping: full removal is a strictly stronger guarantee
than a guarded dead stage. Section 3 now asserts the stronger property (the stage and its files
are gone), which is why it reads differently from the run that preceded it.

THE DEFECTS THIS GUARDS.

  The detail page showed no map. MapLibre was there to draw streets, streets come from
  `tiles.openfreemap.org`, and that host is refused at CONNECT by the network this platform runs
  on. Every reader downloaded 837 KB of library and got an empty panel. The map is now Google
  Maps where the deployment sets a browser key, and a note that the map is unavailable where it
  does not: no key, no request to Google, and no broken frame.

  The portfolio globe went blank (2026-08-10, second session). The same MapLibre removal deleted
  `const mapWrap` from setPortfolioView but left `buildGeoStage(globeWrap, mapWrap, atlasWrap)`
  referencing it; strict mode threw a ReferenceError on the globe branch, so the globe drew
  nothing while Map still worked. Section 3c guards the fix. The portfolio Map view is Google Maps
  now too (same loader as the detail page), and the flat atlas both views fell back to is removed;
  the globe keeps its vendored country geojson, which was never the atlas's file.

  The browser map key is exposed on purpose and read from the environment, never a committed
  file. It is a DIFFERENT key from the server-side geocoding one and carries a different
  restriction (HTTP referrer, not IP). `map_config.py` and the `/mapconfig` endpoint are pinned
  here so the key plumbing cannot silently regress to reading a hard-coded value.

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
    # The stray-mapWrap detector (section 3c) must catch a standalone token and NOT fire on the
    # real variable gmapWrap, or the globe-regression guard is vacuous either way.
    _STRAY = re.compile(r"(?<![A-Za-z])mapWrap(?![A-Za-z])")
    check(bool(_STRAY.search("buildGeoStage(globeWrap, mapWrap, atlasWrap)")),
          "the stray-mapWrap detector CATCHES the exact reference the globe defect left behind")
    check(not _STRAY.search("const gmapWrap = document.querySelector('.gmap-wrap');"),
          "and does NOT fire on the real variable gmapWrap")

    section("1. MAPLIBRE IS NOT LOADED BY THE APPLICATION PAGE")

    index = read("index.html")
    check(not _SCRIPT_TAG.search(index),
          "index.html loads no maplibre script",
          str(_SCRIPT_TAG.findall(index)))
    check(not _LINK_TAG.search(index),
          "and no maplibre stylesheet", str(_LINK_TAG.findall(index)))

    # The tile host has no business in the policy either, once nothing requests it. A CSP that
    # permits a host nothing uses is a standing permission for nothing.
    #
    # The directive LINE, not the first line that mentions the word: the comment above the meta
    # tag says "connect-src" too, and selecting on the substring picked it up, which made the
    # openfreemap check pass against a comment rather than the policy. A directive line, after
    # stripping, begins with the directive name; the comment line begins with "-".
    def directive(name: str) -> str:
        for ln in index.splitlines():
            s = ln.strip()
            if s.startswith(name + " ") and ("'self'" in s or "https://" in s):
                return s
        return ""
    csp = directive("connect-src")
    script_src = directive("script-src")
    check(bool(csp) and bool(script_src),
          "the page declares real connect-src and script-src directives (the scan is not vacuous)",
          (csp[:50] + " || " + script_src[:50]))
    check("openfreemap" not in csp,
          "connect-src no longer permits the tile host", csp[:110])
    # Google Maps is loaded as a script and talks to Google's map hosts, so the policy must now
    # permit exactly those, or the map is dead on arrival behind the CSP.
    check("maps.googleapis.com" in script_src,
          "script-src permits the Google Maps script host", script_src[:120])
    check("maps.googleapis.com" in csp and "maps.gstatic.com" in csp,
          "and connect-src permits the Google Maps data hosts", csp[:140])

    section("2. THE DETAIL PAGE DRAWS GOOGLE MAPS ON A KEY, A NOTE WITHOUT ONE")

    detail_src = strip_js_comments(read("assets/js/detail.js"))
    check(not _GLOBAL_USE.search(detail_src),
          "detail.js contains no live use of the maplibregl global",
          str(_GLOBAL_USE.findall(detail_src)[:4]))
    # The client seams: the shared module for the key and the loader, the render path, and the
    # no-key note that replaced the atlas. Named individually so a regression that drops one is
    # caught.
    for needle, label in [
        ("getMapConfig", "detail.js asks whether a browser map key is set"),
        ("ensureGoogleMaps", "and loads the Google Maps JavaScript API on demand"),
        ("renderGoogleMap", "and has a Google-Maps render path"),
        ("setMapUnavailable", "and says the map is unavailable when there is no key, not the atlas"),
        ("LinGMap", "through the SHARED gmap.js module (same key and path as the portfolio map)"),
    ]:
        check(needle in detail_src, label)
    check("LinAtlas" not in detail_src,
          "detail.js no longer falls back to the removed flat atlas")
    # The Google path must open at street level, or the whole change is pointless (a framed map
    # already shows a region). Seventeen is a block, not a nation.
    gmap_zoom = re.search(r"zoom:\s*17\b", detail_src)
    check(bool(gmap_zoom), "the Google map opens at street zoom (17)")
    # No key -> no request to Google. The API script URL is owned by the SHARED loader (gmap.js),
    # not built here, so detail.js contains no maps.googleapis.com URL at all.
    check(detail_src.count("maps.googleapis.com/maps/api/js") == 0,
          "detail.js builds no Google Maps script URL itself (the shared loader owns it)")
    # The no-key note must be reachable on its OWN branch, not only after a failure.
    globe_section = detail_src[detail_src.index('"d-globe": () =>'):]
    globe_section = globe_section[:globe_section.index('"d-docsignals"')]
    check("setMapUnavailable(" in globe_section,
          "the Location section says the map is unavailable on its own no-key path, not only on failure")
    check("hasCoordsFor" in globe_section,
          "and still refuses to draw a marker for a project with no coordinates")

    # The shared loader is the one place the Maps API script URL is built, for BOTH surfaces.
    gmap_src = strip_js_comments(read("assets/js/gmap.js"))
    check(gmap_src.count("maps.googleapis.com/maps/api/js") == 1,
          "the Google Maps script URL is built in exactly one place — the shared loader gmap.js")
    for needle in ["function config", "function ensure", "function statusColor"]:
        check(needle in gmap_src, f"gmap.js exposes {needle.split()[1]} for both surfaces to share")

    section("3. MAPLIBRE IS REMOVED OUTRIGHT — STAGE, FILES, CSS, MARKUP")

    app_src = read("assets/js/app.js")
    stripped_app = strip_js_comments(app_src)
    # The stage is GONE, not merely guarded. This is a strictly stronger property than the
    # previous "orphaned but present" one, and it is what replaced the red that recorded the old
    # intermediate state. Each removed identifier is a live-code check (comments are stripped).
    for dead in ["buildMap(", "createGlMap(", "loadMapAssets(", "scheduleMapWarmup(",
                 "addGlMarkers(", "maplibregl"]:
        check(dead not in stripped_app,
              f"app.js has no live '{dead}' — the MapLibre stage is gone, not just unreachable",
              dead)
    # The vendored library is off disk. 837 KB that drew nothing.
    for rel in ["assets/vendor/maplibre-gl.min.js", "assets/vendor/maplibre-gl.min.css"]:
        check(not (ROOT / rel).exists(), f"the vendored file {rel} is deleted")
    # The CSS that dressed the stage is gone too, so it cannot rot as unused rules.
    css = read("assets/css/radar.css")
    for sel in [".map-wrap", "#map-gl", ".gl-pin", "maplibregl"]:
        check(sel not in css, f"radar.css carries no '{sel}' rule")
    # And the portfolio Map view is Google Maps now — the same implementation as the detail page —
    # not the flat atlas, which is removed.
    check("buildGoogleMapStage(" in stripped_app,
          "the portfolio Map view builds a Google map")
    check("renderPortfolioGoogleMap(" in stripped_app,
          "and draws one marker per placed project")

    section("3c. THE GLOBE RENDERS, AND THE FLAT ATLAS IS REMOVED")

    # THE DEFECT: the previous session's MapLibre removal deleted `const mapWrap = …` from
    # setPortfolioView but left the call `buildGeoStage(globeWrap, mapWrap, atlasWrap)` referencing
    # it. app.js is strict mode, so reading the undeclared `mapWrap` threw a ReferenceError on the
    # globe branch only — the globe went blank while Map still worked. The guard: no standalone
    # `mapWrap` token survives (gmapWrap, the real variable, is not matched by the boundary).
    stray_mapwrap = re.search(r"(?<![A-Za-z])mapWrap(?![A-Za-z])", stripped_app)
    check(stray_mapwrap is None,
          "app.js references no undeclared 'mapWrap' — the globe branch cannot throw on it again",
          stray_mapwrap.group(0) if stray_mapwrap else "")
    check("buildGeoStage(globeWrap)" in stripped_app,
          "and setPortfolioView calls buildGeoStage with only the arguments it declares")
    # The atlas is gone: its module deleted, its markup out of the page, and no live LinAtlas use.
    check(not (ROOT / "assets/js/atlas.js").exists(),
          "assets/js/atlas.js is deleted")
    check("LinAtlas" not in stripped_app,
          "app.js makes no live use of the removed LinAtlas")
    index = read("index.html")
    check("atlas-wrap" not in index and 'assets/js/atlas.js' not in index,
          "index.html carries no atlas markup and does not load atlas.js")
    check('assets/js/gmap.js' in index,
          "index.html loads the shared gmap.js")
    # The globe keeps drawing its country outlines from the vendored geojson — that STAYS; it was
    # never the atlas's file. Pinned so a later "remove the atlas assets" sweep does not take it.
    check((ROOT / "assets/vendor/ne_110m_admin_0_countries.geojson").exists(),
          "the globe's vendored country geojson is still on disk (the globe reads it)")
    check("ne_110m_admin_0_countries.geojson" in read("assets/js/globe.js"),
          "and globe.js still references it")

    section("3b. THE BROWSER MAP KEY IS READ FROM THE ENVIRONMENT, NOT A COMMITTED FILE")

    mc = read("server/app/map_config.py")
    check('GOOGLE_MAPS_BROWSER_KEY' in mc,
          "map_config.py reads the browser key from GOOGLE_MAPS_BROWSER_KEY")
    check("os.environ" in mc,
          "and reads it from the environment at the point of use")
    # The key must not be a committed constant anywhere a page could read it.
    config_js = read("assets/js/config.js")
    check("GOOGLE_MAPS_BROWSER_KEY" not in config_js and "maps_browser_key" not in config_js.lower(),
          "config.js holds no browser map key (it comes from the environment via /mapconfig)")
    main_py = read("server/app/main.py")
    check("/mapconfig" in main_py,
          "main.py serves the /mapconfig endpoint the page fetches the key from")
    # Behaviour, not just presence: no key -> present False and no apiKey; a key -> both set.
    sys.path.insert(0, str(ROOT / "server"))
    import importlib
    mcmod = importlib.import_module("app.map_config")
    import os as _os
    _saved = _os.environ.pop("GOOGLE_MAPS_BROWSER_KEY", None)
    try:
        cfg_absent = mcmod.map_config()
        _os.environ["GOOGLE_MAPS_BROWSER_KEY"] = "AIza-test-key"
        cfg_present = mcmod.map_config()
    finally:
        if _saved is None:
            _os.environ.pop("GOOGLE_MAPS_BROWSER_KEY", None)
        else:
            _os.environ["GOOGLE_MAPS_BROWSER_KEY"] = _saved
    check(cfg_absent["present"] is False and cfg_absent["apiKey"] is None,
          "with no key the config reports present False and no apiKey", json.dumps(cfg_absent))
    check(cfg_present["present"] is True and cfg_present["apiKey"] == "AIza-test-key",
          "with a key set it reports present True and the key", json.dumps(cfg_present))

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
