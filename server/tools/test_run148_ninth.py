#!/usr/bin/env python3
"""
RUN 148: THE NINTH EXIT. WHICH WAYS CAN THE MODULE PAYLOAD FAIL TO REACH THE PAGE WITHOUT
EITHER OF RUN 147'S SURFACED EXITS FIRING?

Run with cwd = <worktree>/server, against a THROWAWAY database only:

    DATABASE_URL=sqlite:///<throwaway>.db python tools/test_run148_ninth.py

THE FIXTURE IS CONSTRUCTED AND THIS FILE SAYS SO PLAINLY. PRJ-002 and its database are not
reachable from this container. This file REUSES Run 147's harness verbatim -- its seed, its
uvicorn boot and its `observe()` browser reader are loaded out of
tools/test_run147_surfacing.py rather than rewritten, so every measurement below is taken by
the same instrument that produced Run 147's 24/24.

THE STATE BEING HUNTED, and every candidate is judged against ALL FOUR parts of it:

    (a) the module rows are absent from the page,
    (b) the Signal Network line reads "0 of N modules in service assert a band ... N have not
        been called",
    (c) the five category postures and the project status still publish,
    (d) THERE IS NO BANNER.

A candidate that raises Run 147's banner is DISCARDED -- it is one of the eight already
surfaced and cannot be what the owner is looking at. A candidate that leaves the page whole is
DISCARDED -- it does not produce the symptom.

THE PASSES.

  N0  Control. The code as shipped, page whole, no banner. Establishes the baseline counts
      every other pass is compared against.

  N1  RUN 147'S OWN FIRST SUSPECT: an UNHANDLED EXCEPTION inside the projectresults route.
      Run 147 named this class -- "an unhandled exception becomes a not-ok body at HTTP 200
      carrying only a type name, dropped in silence" -- and said it is where it would look
      first. Measured here.

  N2  A SHAPE CHANGE THE CLIENT CANNOT READ: the response is ok:true, `result` is present, the
      period agrees -- but `module_results` arrives as an OBJECT instead of an ARRAY. Every
      guard in `primeAndRefresh` is satisfied, the graft applies, `graftSucceeded` fires and
      CLEARS any banner, and every consumer that does `Array.isArray(row.module_results)`
      finds nothing.

  N3  A RENAMED KEY: `module_results` arrives as `modules`. Same class as N2, different shape.

  N4  A POST-RESPONSE EXCEPTION. `primeAndRefresh(id, p)` is called at detail.js:1242 WITHOUT
      `await` and WITHOUT `.catch()`. Anything that throws after the response has been read
      becomes an unhandled promise rejection: no banner, no page state, and the sections never
      re-run. Injected in the browser by making the very first thing the graft touches throw.

  N5  FINDING B, MEASURED RATHER THAN ASSUMED: a STALE `detail.js`. index.html references
      every script by a bare path with no version query and no content hash, and the service
      sets no cache headers at all, so a browser or a CDN may execute a pre-Run-147 file
      against a post-Run-147 server. This pass serves the pre-147 detail.js (81e5e32) from the
      same tree and reads the page. It is the direct test of "the surfacing is live on the
      server and the browser is not running it".

  N6  Restore. The tree is back as shipped and the page is whole again -- the "prove it can
      fail" partner for N0.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# ---------------------------------------------------------------- reuse Run 147's harness
# The file calls main() on its last line, so it cannot simply be imported. Everything ABOVE
# that call -- seed(), free_port(), observe(), describe() -- is exactly the instrument this run
# needs, and re-typing it would be a second instrument to keep honest. It is loaded here with
# the trailing call removed, and nothing else about it is changed.
_H = os.path.join(HERE, "test_run147_surfacing.py")
_src = open(_H, encoding="utf-8").read()
assert _src.rstrip().endswith("main()"), "run147 harness no longer ends in main(); check it"
_src = _src.rstrip()[: -len("main()")]
H: dict = {"__name__": "run147_harness", "__file__": _H}
exec(compile(_src, _H, "exec"), H)  # noqa: S102 -- reusing this run's own checked-in harness

seed = H["seed"]
free_port = H["free_port"]
observe = H["observe"]
describe = H["describe"]
LEGACY = H["LEGACY"]

SHOTS = os.path.join(os.path.dirname(H["SHOTS"]), "run148")
os.makedirs(SHOTS, exist_ok=True)
H["SHOTS"] = SHOTS

RESULTS: list[tuple[bool, str, str]] = []
DETAIL_JS = os.path.join(ROOT, "assets", "js", "detail.js")
TAXONOMY_JS = os.path.join(ROOT, "assets", "js", "taxonomy.js")
PRE_147 = "81e5e32"  # the commit immediately before Run 147's surfacing landed
PRE_148 = "4ba23b8"  # main as this run found it: Run 147's eight exits, and the ninth open


# The working tree's own bytes, taken once before anything is swapped. restore() puts THESE
# back -- deliberately not `git checkout --`, which would silently discard an uncommitted
# change under test and make this suite measure the wrong file. That is not hypothetical: it
# happened on this run's first execution and cost a pass.
_ORIGINAL: dict[str, bytes] = {}


def keep(path: str) -> None:
    _ORIGINAL[path] = open(path, "rb").read()


def restore(path: str) -> None:
    if path in _ORIGINAL:
        with open(path, "wb") as fh:
            fh.write(_ORIGINAL[path])


def inject_throw(path: str, needle: str, replacement: str) -> None:
    src = open(path, encoding="utf-8").read()
    assert src.count(needle) == 1, f"injection anchor not unique in {path}"
    open(path, "w", encoding="utf-8").write(src.replace(needle, replacement))


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def section(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def verdict(o: dict, base_status, base_cats, n_mod: int) -> dict:
    """The four-part test, applied to one observation."""
    r = o.get("client_row") or {}
    line = o.get("network_line") or ""
    v = {
        "rows_gone": r.get("module_results") in (None, 0),
        "network_zero": line.startswith("0 of "),
        "categories_publish": (r.get("project_status") == base_status
                               and r.get("categories") == base_cats),
        "no_banner": o.get("alert") is None,
        "rows": r.get("module_results"),
        "line": line,
    }
    v["reproduces"] = (v["rows_gone"] and v["network_zero"]
                       and v["categories_publish"] and v["no_banner"])
    print(f"    VERDICT rows_absent={v['rows_gone']} network_zero={v['network_zero']} "
          f"categories_publish={v['categories_publish']} no_banner={v['no_banner']} "
          f"-> REPRODUCES={v['reproduces']}")
    return v


def swap_js(path: str, rev: str) -> None:
    """Serve that revision's copy of the file. restore() puts the tree's own back."""
    rel = os.path.relpath(path, ROOT)
    out = subprocess.run(["git", "-C", ROOT, "show", f"{rev}:{rel}"],
                         check=True, capture_output=True)
    with open(path, "wb") as fh:
        fh.write(out.stdout)


def main() -> None:
    import uvicorn

    import app.documents as D
    import app.main as main_mod

    keep(DETAIL_JS)
    keep(TAXONOMY_JS)
    token, (n_mod, n_abs) = seed()
    print(f"  CONSTRUCTED FIXTURE (Run 147's, reused unchanged): the stored period-2 row holds "
          f"{n_mod} module rows and {n_abs} abstentions")

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    cfg = uvicorn.Config(main_mod.app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(cfg)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)

    REAL = D.DOCUMENT_ACTIONS["projectresults"]
    discarded: list[str] = []

    try:
        # ------------------------------------------------------------------ N0
        section("N0. CONTROL. The code as shipped: the page is whole and carries no banner.")
        whole = observe(base, token, "n0-control")
        describe(whole)
        wr = whole["client_row"] or {}
        BASE_STATUS, BASE_CATS = wr.get("project_status"), wr.get("categories")
        check(wr.get("module_results") == n_mod,
              f"control: the page holds all {n_mod} module rows",
              str(wr.get("module_results")))
        check(whole.get("alert") is None, "control: and no banner", str(whole.get("alert")))
        BASE_NO_DATA = whole["no_data_count"]

        # ------------------------------------------------------------------ N1
        section("N1. AN UNHANDLED EXCEPTION IN THE projectresults ROUTE -- Run 147's own first "
                "suspect. Does it reach the page as a banner, or in silence?")

        def _boom(s, p, sec, ttl):
            raise RuntimeError("run148 injected: unhandled exception inside projectresults")

        D.DOCUMENT_ACTIONS["projectresults"] = _boom
        try:
            n1 = observe(base, token, "n1-route-raises")
        finally:
            D.DOCUMENT_ACTIONS["projectresults"] = REAL
        describe(n1)
        v1 = verdict(n1, BASE_STATUS, BASE_CATS, n_mod)
        check(not v1["reproduces"],
              "N1 DISCARDED: an unhandled exception in the route does NOT reproduce the "
              "reported state -- Run 147's surfacing catches it",
              f"banner={bool(n1.get('alert'))}")
        if not v1["reproduces"]:
            discarded.append("N1 unhandled exception in the projectresults route")

        # ------------------------------------------------------------------ N2 / N3
        for tag, label, mutate in [
            ("n2-array-to-object",
             "N2. THE SHAPE THE CLIENT CANNOT READ: module_results arrives as an OBJECT.",
             lambda r: {**r, "module_results": {m.get("module_id", str(i)): m
                                                for i, m in enumerate(r.get("module_results")
                                                                      or [])}}),
            ("n3-renamed-key",
             "N3. THE RENAMED KEY: module_results arrives as `modules`.",
             lambda r: {k: v for k, v in
                        {**r, "modules": r.get("module_results")}.items()
                        if k != "module_results"}),
        ]:
            section(label)

            def _shaped(s, p, secx, ttl, _m=mutate):
                out = REAL(s, p, secx, ttl)
                if isinstance(out, dict) and out.get("ok") and isinstance(out.get("result"),
                                                                         dict):
                    out = {**out, "result": _m(out["result"])}
                return out

            D.DOCUMENT_ACTIONS["projectresults"] = _shaped
            try:
                o = observe(base, token, tag)
            finally:
                D.DOCUMENT_ACTIONS["projectresults"] = REAL
            describe(o)
            v = verdict(o, BASE_STATUS, BASE_CATS, n_mod)
            check(True, f"{tag}: measured", f"reproduces={v['reproduces']}")
            if not v["reproduces"]:
                discarded.append(f"{tag} shape change")

        # ------------------------------------------------------------------ N4
        section("N4. A POST-RESPONSE EXCEPTION. primeAndRefresh is called WITHOUT await and "
                "WITHOUT .catch(): anything that throws after the response is read is an "
                "unhandled rejection -- silent by construction.")
        # Injected in the served file itself: LinResults.prime is the first thing the graft
        # touches after the response has been read. Making it throw is the smallest possible
        # stand-in for ANY exception on that path, and it is injected the same way N5 swaps a
        # file -- written, served, then restored from git.
        #
        # N4a RUNS IT AGAINST THE TREE AS THIS RUN FOUND IT (4ba23b8), where the call site is a
        # floating promise. THIS IS THE REPRODUCTION: all four parts of the reported state,
        # including the reported sentence verbatim, with NO banner.
        swap_js(DETAIL_JS, PRE_148)
        inject_throw(TAXONOMY_JS,
                     "prime: function (projectId, row) {",
                     "prime: function (projectId, row) { throw new Error("
                     "'run148 injected: exception after the response was read');")
        try:
            n4a = observe(base, token, "n4a-pre-fix-floating-promise")
        finally:
            restore(DETAIL_JS)
        describe(n4a)
        v4a = verdict(n4a, BASE_STATUS, BASE_CATS, n_mod)
        check(v4a["reproduces"],
              "N4a IS THE REPRODUCTION: on the tree as found, an exception raised after the "
              "response empties the page with NO BANNER while the categories still publish",
              f"rows={v4a['rows']} banner={n4a.get('alert')!r}")
        _line = n4a.get("network_line") or ""
        check(_line.startswith("0 of 28 modules in service assert a band")
              and _line.endswith("28 have not been called."),
              "and the Signal Network line reads the owner's reported sentence VERBATIM",
              str(_line))
        check(not (n4a.get("graft_console") or []),
              "and Run 147's surfacing says NOTHING on the console either -- the ninth exit is "
              "invisible to it", str(n4a.get("graft_console")))

        # N4b: THE SAME INJECTION AGAINST THIS RUN'S FIX. Same throw, same page, same fixture.
        section("N4b. THE SAME EXCEPTION WITH RUN 148'S .catch IN PLACE. The ninth exit must "
                "now name itself exactly as the eight surfaced ones do.")
        try:
            n4b = observe(base, token, "n4b-post-fix-surfaced")
        finally:
            restore(TAXONOMY_JS)
        describe(n4b)
        check(bool(n4b.get("alert")) and "could not be applied" in (n4b.get("alert") or ""),
              "N4b: THE SURFACING GAP IS CLOSED -- the page names the failure",
              str(n4b.get("alert"))[:160])
        check("run148 injected" in (n4b.get("alert") or ""),
              "carrying the raised error's own message verbatim")
        check(any("could not be applied" in c for c in n4b.get("graft_console") or []),
              "and the same is on the console as an error",
              str(n4b.get("graft_console"))[:160])
        r4b = n4b["client_row"] or {}
        check(r4b.get("project_status") == BASE_STATUS and r4b.get("categories") == BASE_CATS,
              "the category postures and the project status are unchanged by the surfacing",
              f"{r4b.get('project_status')!r}/{r4b.get('categories')}")

        # ------------------------------------------------------------------ N5
        section("N5. FINDING B, MEASURED: a STALE detail.js. The server is running THIS tree; "
                "the browser is served the pre-147 file (81e5e32), which is exactly what a "
                "cache in front of an unversioned bare-path asset can do.")
        swap_js(DETAIL_JS, PRE_147)
        try:
            n5 = observe(base, token, "n5-stale-detail-js")
        finally:
            restore(DETAIL_JS)
        describe(n5)
        v5 = verdict(n5, BASE_STATUS, BASE_CATS, n_mod)
        check(not v5["reproduces"],
              "N5 DISCARDED ON ITS OWN: a stale detail.js against a healthy server renders the "
              "page WHOLE. Old code is not by itself a blank page",
              f"rows={v5['rows']}")
        if not v5["reproduces"]:
            discarded.append("N5 stale detail.js on its own (the page renders whole)")

        # ------------------------------------------------------------------ N5b
        section("N5b. FINDING B IN ITS ONLY HONEST FORM: a stale pre-147 detail.js AND a "
                "server-side refusal at the same time. This is what 'the browser is running "
                "yesterday's file' would actually have to look like.")
        swap_js(DETAIL_JS, PRE_147)
        D.DOCUMENT_ACTIONS["projectresults"] = (
            lambda s, p, secx, ttl: {"ok": False,
                                     "error": "run148 injected refusal (stale-asset pass)"})
        try:
            n5b = observe(base, token, "n5b-stale-js-and-refusal")
        finally:
            D.DOCUMENT_ACTIONS["projectresults"] = REAL
            restore(DETAIL_JS)
        describe(n5b)
        v5b = verdict(n5b, BASE_STATUS, BASE_CATS, n_mod)
        check(v5b["reproduces"],
              "N5b: a stale asset DOES reproduce the state -- but ONLY with a server-side "
              "failure underneath it, which Run 147 measured as absent on this tree",
              f"rows={v5b['rows']} banner={n5b.get('alert')!r}")

        # ------------------------------------------------------------------ N6
        section("N6. RESTORE. The tree is as shipped again and the page is whole.")
        n6 = observe(base, token, "n6-restored")
        describe(n6)
        r6 = n6["client_row"] or {}
        check(r6.get("module_results") == n_mod,
              f"all {n_mod} module rows are back", str(r6.get("module_results")))
        check(n6.get("alert") is None, "and no banner", str(n6.get("alert")))
        check(r6.get("project_status") == BASE_STATUS and r6.get("categories") == BASE_CATS,
              "and the category postures and the project status never moved across all passes",
              f"{r6.get('project_status')!r}/{r6.get('categories')}")
        print(f"    baseline 'No data' occurrences: {BASE_NO_DATA}; restored: "
              f"{n6['no_data_count']}")

        section("ENUMERATION RESULT")
        print("  candidates measured: 6 (N1, N2, N3, N4, N5, N5b)")
        print(f"  DISCARDED ({len(discarded)}):")
        for d in discarded:
            print(f"    - {d}")
        print(f"    screenshots: {SHOTS}")
    finally:
        D.DOCUMENT_ACTIONS["projectresults"] = REAL
        restore(DETAIL_JS)
        restore(TAXONOMY_JS)
        server.should_exit = True
        t.join(timeout=10)

    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for ok, label, detail in failed:
        print(f"  FAILED: {label}  [{detail}]")
    sys.exit(1 if failed else 0)


main()
