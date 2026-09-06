#!/usr/bin/env python3
"""
RUN 150, PROOFS 11 AND 12 AND THE REVEAL GATE'S COST, TAKEN IN A REAL BROWSER.

Run with cwd = <worktree>/server, against a THROWAWAY database only:

    PYTHONPATH=$(pwd) DATABASE_URL=sqlite:///<throwaway>.db python tools/test_run150_card_browser.py

Run 140 proved its render against RENDERED HTML STRINGS. That is not what the order's proof 11
asks for -- "the card renders the blocks, BROWSER OBSERVATION, contrast measured, on at least two
themes" -- and a string assertion cannot see a block that the page lays out at zero height, hides
behind a collapsed section, or paints in a colour nobody can read. This file opens the real front
end in headless Chromium and reads what the browser LAID OUT and PAINTED.

THE HARNESS IS RUN 147'S, LOADED NOT RETYPED, exactly as Run 148 loaded it -- its `seed()`, its
`free_port()` and its uvicorn boot are the instrument that produced Run 147's 24/24 and Run 148's
passes. Only the page reader is new, because what is being read is new: the mitigation blocks,
their computed colours and their contrast ratios.

THE FIXTURE IS CONSTRUCTED AND THIS FILE SAYS SO PLAINLY. PRJ-002 and its database are not
reachable from this container.

NO API KEY EXISTS AND NO CALL IS SIMULATED. Mitigations are STORED before the page is opened,
through the real `compose_one` with a counting fake at its `caller=` parameter -- the parameter
production never passes. The SERVER then renders them through the real, unmodified request path,
which passes no caller at all: every block the browser shows is a REPLAY out of
`module_mitigations`, and the call count is read back afterwards to prove the render made none.
That is proof 8 taken through the browser rather than through a function.
"""
from __future__ import annotations

import json as _json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# ---------------------------------------------------------------- reuse Run 147's harness
_H = os.path.join(HERE, "test_run147_surfacing.py")
_src = open(_H, encoding="utf-8").read()
assert _src.rstrip().endswith("main()"), "run147 harness no longer ends in main(); check it"
_src = _src.rstrip()[: -len("main()")]
H: dict = {"__name__": "run147_harness", "__file__": _H}
exec(compile(_src, _H, "exec"), H)  # noqa: S102 -- the run's own checked-in harness

seed = H["seed"]
free_port = H["free_port"]
LEGACY = H["LEGACY"]
CHROME = H["CHROME"]
SHOTS = os.path.join(os.path.dirname(H["SHOTS"]), "run150")
os.makedirs(SHOTS, exist_ok=True)

RESULTS: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    RESULTS.append((bool(ok), label))
    print(("  [PASS] " if ok else "  [FAIL] ") + label)


def section(t: str) -> None:
    print("\n" + t)


# --------------------------------------------------------------------------- contrast
def _lin(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb) -> float:
    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(fg, bg) -> float:
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def parse_rgb(text: str):
    nums = [float(n) for n in __import__("re").findall(r"[\d.]+", text or "")]
    return tuple(nums[:3]) if len(nums) >= 3 else None


# ============================================================ store the mitigations first
def store_mitigations():
    """
    Compose ONCE into the real store with a fake caller, so the page can only be a replay.

    Returns (calls_made, stored_module_ids, the served entries) -- every one of them counted
    rather than assumed.
    """
    from sqlalchemy import select

    import app.main as main
    from app import ai_provider, mitigation
    from app.decision_brief import _adverse_readings
    from app.models import Project
    from app.research_models import ComputedResult

    Session = main.SessionFactory
    calls = {"n": 0}

    def fake(blocks, cfg, environ=None):
        """THE FAKE LIVES HERE, IN THE CHECK. Production never passes `caller`."""
        calls["n"] += 1
        _ = blocks  # the fake reads nothing; it exists only to be COUNTED
        return ("- Raise the constraint-free proportion of the look-ahead window by clearing "
                "open constraints on planned activities ahead of the due window.\n"
                "- Re-inspect the items that failed on first presentation so the first-pass "
                "population is measured on a corrected basis.\n"
                "- Record the acceptance evidence for items already passed so the measured "
                "denominator matches the inspected population.")

    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == LEGACY))
        res = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == proj.id, ComputedResult.period == 2,
            ComputedResult.superseded_by.is_(None)))
        modules = list(res.module_results or [])
        cats = dict(res.category_statuses or {})
        adverse = _adverse_readings(cats, modules)
        cfg = ai_provider.load_provider("mitigation", {})
        store = mitigation.MitigationStore(s, proj.id)
        by_id = {str(m.get("module_id")): m for m in modules if m.get("module_id")}
        served = []
        for row in adverse:
            mod = by_id.get(str(row.get("module_id")))
            if mod is None:
                continue
            e = mitigation.compose_one(mod, store=store, period=2, cfg=cfg, environ={},
                                       caller=fake)
            if e is not None:
                served.append(e)
        s.commit()
    return calls["n"], [e["module_id"] for e in served], served


def stored_count():
    from sqlalchemy import func, select

    import app.main as main
    from app.research_models import ModuleMitigation
    with main.SessionFactory() as s:
        return s.scalar(select(func.count()).select_from(ModuleMitigation)) or 0


# ============================================================================ the reader
def observe(base: str, token: str, theme: str, label: str) -> dict:
    """Open the real detail page as the PM, in one theme, and read what was PAINTED."""
    from playwright.sync_api import sync_playwright

    out: dict = {"label": label, "theme": theme}
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1280, "height": 1200})
        errors: list[str] = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base + "/index.html", wait_until="load")
        pg.evaluate("t => sessionStorage.setItem('og-session-token', t)", token)
        pg.goto(base + "/index.html", wait_until="load")
        pg.wait_for_timeout(2500)
        pg.evaluate("t => { document.body.dataset.theme = t; }", theme)
        pg.evaluate("id => window.LinApp.openDetail(id)", LEGACY)
        pg.wait_for_timeout(4000)
        # BOTH RENDERERS HIDE DETAIL BY DEFAULT, so a page read without expanding shows
        # nothing whatever it holds. This is why proof 11 must be a browser observation.
        pg.evaluate("""() => {
            document.querySelectorAll('[id^="body-"]').forEach(b => {
                if (b.style.display === 'none') {
                    try { window.toggleSection(b.id.slice(5)); } catch (e) {}
                }
            });
        }""")
        pg.wait_for_timeout(2500)
        pg.evaluate("() => document.querySelectorAll('details').forEach(d => { d.open = true; })")
        pg.wait_for_timeout(1500)
        pg.evaluate("t => { document.body.dataset.theme = t; }", theme)
        pg.wait_for_timeout(400)

        out["theme_applied"] = pg.evaluate("() => document.body.dataset.theme")
        out["blocks"] = pg.evaluate("""() => {
            function bg(el) {
                let n = el;
                while (n && n !== document.documentElement) {
                    const c = getComputedStyle(n).backgroundColor;
                    if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') return c;
                    n = n.parentElement;
                }
                const bodyBg = getComputedStyle(document.body).backgroundColor;
                if (bodyBg && bodyBg !== 'rgba(0, 0, 0, 0)' && bodyBg !== 'transparent')
                    return bodyBg;
                const htmlBg = getComputedStyle(document.documentElement).backgroundColor;
                if (htmlBg && htmlBg !== 'rgba(0, 0, 0, 0)' && htmlBg !== 'transparent')
                    return htmlBg;
                /* Nothing in the stack paints, so the block sits on the browser's own canvas.
                   Chromium paints that white, and that is what a reader actually sees. */
                return 'rgb(255, 255, 255)';
            }
            return Array.from(document.querySelectorAll('.dc-mitigation')).map(m => {
                const r = m.getBoundingClientRect();
                const val = m.querySelector('.dc-mit-value');
                const lab = m.querySelector('.dc-mit-label');
                const li  = m.querySelector('.dc-mit-list li');
                const lines = Array.from(m.querySelectorAll('.dc-mit-line'))
                                   .map(x => x.innerText.trim());
                return {
                    width: r.width, height: r.height,
                    visible: r.width > 0 && r.height > 0,
                    text: m.innerText,
                    lines: lines,
                    candidates: Array.from(m.querySelectorAll('.dc-mit-list li'))
                                     .map(x => x.innerText.trim()),
                    absent: (m.querySelector('.dc-mit-absent') || {}).innerText || null,
                    value_fg: val ? getComputedStyle(val).color : null,
                    label_fg: lab ? getComputedStyle(lab).color : null,
                    cand_fg: li ? getComputedStyle(li).color : null,
                    bg: bg(m)
                };
            });
        }""")
        out["body_text"] = pg.evaluate("() => document.body.innerText")
        out["errors"] = errors[:3]
        pg.screenshot(path=os.path.join(SHOTS, f"run150-{label}.png"), full_page=False)
        b.close()
    return out


def export_record(base: str, token: str):
    """
    THE EXPORT AS THE REVIEWER GETS IT. Run 140's export proof compared Python fixtures; the
    audit JSON is actually assembled IN THE BROWSER by `decision.js:buildAuditRecord`, handed the
    same `LinResults.rowFor(p).decision_brief` the card renders from. This calls that function in
    the page with the same arguments `app.js:1853` passes, and returns the record.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1280, "height": 1200})
        pg.goto(base + "/index.html", wait_until="load")
        pg.evaluate("t => sessionStorage.setItem('og-session-token', t)", token)
        pg.goto(base + "/index.html", wait_until="load")
        pg.wait_for_timeout(2500)
        pg.evaluate("id => window.LinApp.openDetail(id)", LEGACY)
        pg.wait_for_timeout(4000)
        rec = pg.evaluate("""(id) => {
            const p = LinStore.getCached(id);
            if (!p || typeof window.buildAuditRecord !== 'function') return null;
            const row = (window.LinResults && LinResults.rowFor) ? LinResults.rowFor(p) : null;
            /* `deriveDecision` is module-local to app.js's IIFE and is NOT on LinApp -- the
               first attempt passed null and buildAuditRecord threw on `decision.healthState`,
               which is a defect in this check, not in the export. The record's mitigations arm
               reads ONLY `brief`, so a stub carrying the fields the record copies is enough and
               keeps this proof about the brief the card rendered from. */
            const d = {healthState: "(stub)", conflictType: null, state: null};
            try {
                return window.buildAuditRecord(
                    p, d, {rationale: "(check)", recordedAt: new Date().toISOString()},
                    row && row.decision_brief);
            } catch (e) { return {__error: String(e)}; }
        }""", LEGACY)
        b.close()
    return rec


def main() -> None:
    os.chdir(os.path.dirname(HERE))

    section("0. SEED, THEN COMPOSE ONCE INTO THE STORE WITH A COUNTED FAKE.")
    token, (n_mod, n_abs) = seed()
    print(f"    fixture: {n_mod} module rows, {n_abs} abstentions at period 2")
    calls, ids, served = store_mitigations()
    print(f"    composed: {len(served)} entries over {ids}")
    check(calls == len(served) and calls > 0,
          f"composition made exactly one call per stored reading ({calls} calls, "
          f"{len(served)} entries) -- counted at the `caller=` boundary")
    check(stored_count() == len(served),
          f"{stored_count()} rows are in `module_mitigations` before the browser opens")
    check(any(e.get("candidates") for e in served),
          "at least one stored entry carries candidates, so there is a block to look at")

    import uvicorn

    import app.main as main_mod

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    # THE BOOT IS RUN 147'S, IN-THREAD. A uvicorn SUBPROCESS was tried first and the detail
    # page rendered NOTHING in it -- zero collapse sections -- so every measurement below would
    # have been taken against a page that never drew. The instrument that produced Run 147's
    # 24/24 is the one used here.
    cfg_u = uvicorn.Config(main_mod.app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(cfg_u)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(200):
        if server.started:
            break
        time.sleep(0.1)

    try:
        before = stored_count()

        # =================================================================================
        section("A. THE REVEAL GATE'S COST, OBSERVED RATHER THAN ASSERTED.")
        # =================================================================================
        # `documents.py` composes and serves the `mitigations` key ONLY when
        # `include_recommendation` is true, and on a withheld read the key is ABSENT from the
        # brief entirely. That was Run 140's own decision and the owner has not ruled on it.
        # Its COST is this: on a withheld surface the card shows NOTHING AT ALL -- not an
        # explanation, not a placeholder. Measured here in the browser, with the rows already
        # stored and the page otherwise whole.
        withheld = observe(base, token, "plain", "a-withheld")
        check(len(withheld["blocks"]) == 0,
              f"WITHHELD: the card lays out {len(withheld['blocks'])} mitigation blocks -- the "
              f"gate's cost is that {stored_count()} stored rows render as nothing at all")
        check("Suggested Decision" in withheld["body_text"]
              or "Decision" in withheld["body_text"],
              "WITHHELD: the rest of the card is whole, so the blank is the gate and not a "
              "broken page")

        # THE GATE IS OPENED IN THE FIXTURE'S DATA, NOT IN THE CODE. Nothing in `documents.py`
        # is edited: the participant's preliminary judgment is locked, which is the real
        # condition `recommendation_visible` reads.
        from sqlalchemy import select

        import app.main as _m
        from app.research_models import Decision as _D
        with _m.SessionFactory() as s:
            d = s.scalar(select(_D))
            d.pre_judgment_locked = True
            s.commit()
        check(True, "the fixture's preliminary judgment is now LOCKED -- the same condition "
                    "`recommendation_visible` reads, with no code changed")

        observations = {}
        for theme in ("plain", "light"):
            section(f"THEME {theme!r}. BROWSER OBSERVATION.")
            o = observe(base, token, theme, theme)
            observations[theme] = o
            check(o["theme_applied"] == theme, f"the page is laid out under theme {theme!r}")
            check(not o["errors"], f"{theme}: no page error was raised ({o['errors']})")
            blocks = o["blocks"]
            check(len(blocks) > 0,
                  f"{theme}: the browser LAID OUT {len(blocks)} mitigation block(s) on the card")
            if not blocks:
                continue
            check(all(b["visible"] for b in blocks),
                  f"{theme}: every block has non-zero width and height -- it is not a "
                  f"zero-height element the DOM merely contains")

            # All four required parts, read out of what the browser laid out.
            for b in blocks[:3]:
                joined = " ".join(b["lines"])
                check(any(l.startswith("Current:") for l in b["lines"]),
                      f"{theme}: part 1, the reading, is laid out")
                check(any(l.startswith("Next band:") for l in b["lines"]),
                      f"{theme}: part 2, the next band's boundary, is laid out")
                check(any(l.startswith("Gap:") for l in b["lines"]),
                      f"{theme}: part 3, the gap, is laid out")
                check(bool(b["candidates"]) or bool(b["absent"]),
                      f"{theme}: part 4, the stored candidates or the absence line, is laid out")
                if b["candidates"]:
                    check("composed" in b["text"],
                          f"{theme}: the composition date is laid out beside the candidates")
                break

            # CONTRAST, MEASURED. The order asks for it measured, not asserted.
            for b in blocks[:1]:
                bg = parse_rgb(b["bg"])
                for name, key, floor in (("value", "value_fg", 4.5),
                                         ("label", "label_fg", 3.0),
                                         ("candidate", "cand_fg", 4.5)):
                    fg = parse_rgb(b.get(key))
                    if fg is None or bg is None:
                        check(False, f"{theme}: could not read the {name} colour")
                        continue
                    ratio = contrast(fg, bg)
                    check(ratio >= floor,
                          f"{theme}: the {name} text measures {ratio:.2f}:1 against its own "
                          f"painted background (floor {floor}) -- fg {b[key]} on {b['bg']}")

        # PROOF 8, THROUGH THE BROWSER: two full renders in two themes, and no second call.
        section("REPLAY, COUNTED THROUGH THE REAL SERVER PATH.")
        check(stored_count() == before,
              f"the browser renders stored no new row ({stored_count()} == {before}) -- the "
              f"server composed nothing at render time")
        a = observations.get("plain", {}).get("blocks") or []
        c = observations.get("light", {}).get("blocks") or []
        check(len(a) == len(c) and [x["text"] for x in a] == [x["text"] for x in c],
              "the two themes laid out BYTE-IDENTICAL mitigation text -- the same replay, "
              "differently painted")

        # PROOF 12 through the browser: the export carries what the card showed.
        section("PROOF 12. THE EXPORT CARRIES WHAT THE BROWSER SHOWED.")
        shown = set()
        for b in a:
            for cand in b["candidates"]:
                shown.add(cand)
        record = export_record(base, token)
        blob = _json.dumps(record) if record is not None else ""
        _err = (record or {}).get("__error")
        check(record is not None and not _err,
              "the browser's OWN `buildAuditRecord` produced an audit record -- the exports are "
              "built client-side, so this is the export path the reviewer actually gets"
              + (f" [threw: {_err}]" if _err else ""))
        if shown:
            missing = [x for x in shown if x not in blob]
            check(bool(record) and not missing,
                  f"every one of the {len(shown)} candidate sentence(s) the BROWSER laid out is "
                  f"present VERBATIM in the audit record ({len(missing)} missing)")
            mits = (record or {}).get("mitigations")
            check(isinstance(mits, list) and len(mits) == len(a),
                  f"the record carries one mitigation entry per block the card showed "
                  f"({len(mits) if isinstance(mits, list) else None} vs {len(a)})")
        else:
            check(False, "no candidate was laid out, so the export could not be compared "
                         "against what the card showed")
    finally:
        server.should_exit = True
        t.join(timeout=10)

    passed = sum(1 for ok, _ in RESULTS if ok)
    print(f"\nScreenshots: {SHOTS}")
    print("NO API KEY EXISTS AND NO CALL WAS SIMULATED. The blocks the browser painted are "
          "REPLAYS of rows stored before it opened, through the real server path, which passes "
          "no caller. The live composition -- the one HTTPS request -- is untested.")
    print(f"RESULT: {passed}/{len(RESULTS)} checks passed")
    sys.exit(0 if passed == len(RESULTS) else 1)


main()
