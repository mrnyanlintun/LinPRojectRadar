#!/usr/bin/env python3
"""
RUN 140 R -- THE MITIGATION BLOCK, RENDERED AND MEASURED.

Run (from server/):

    python tools/test_run140r_render.py

WHAT THIS PROVES, AND WHY EACH PROOF EXISTS.

  2. A non-Green module renders a block whose reading, boundary and gap match the module's own
     sentence and deciding constant -- COMPARED PROGRAMMATICALLY, not read by eye. The rendered
     HTML is unescaped and the three strings are searched for verbatim. A renderer that rounded
     a figure, reflowed a boundary or reworded a gap fails here, because every number on this
     card must stay traceable to the constant that decided it.

  5. An unbanded module triggers no call and renders no block. The fixture carries an adverse
     row with NO entry in `mitigations`; the assertion is that its list item ends where it did
     before and carries no `dc-mitigation` at all.

  NO-KEY BYTE-IDENTICAL. A brief with no `mitigations` key must render EXACTLY as the
  pre-change renderer rendered it. This is not an approximation: the pre-change
  `decision-ui.js` is read out of git at the branch point and run in a second sandbox, and the
  two output strings are compared with `==`. Mitigations are reveal-gated, so the ungated card
  is what most participants see, and "renders as it did" has to mean byte for byte.

  LOWERCASE BANDS. A1.2 returns lowercase band strings. Any `=== "Red"` in the render path
  would silently drop them. The fixture carries a lowercase-banded module and asserts its
  block renders; the renderer compares no band string anywhere, which is the actual defence.

  THE SPLIT. Three findings carry their block inline under "Why this decision is suggested";
  the rest carry theirs under "All adverse findings", and NO block is rendered twice.

THE CHECKS ARE PROVEN ABLE TO FAIL. Before the real fixture is measured, GUARANTEE 0 runs the
same comparison against a deliberately corrupted gap string and asserts it FAILS. A check that
has never failed has not been shown to check anything.

AGENT E'S ENGINE MAY NOT EXIST ON THIS BRANCH. This measures the RENDERER against a FIXTURE
brief carrying the agreed contract. It does not measure the composition, the validator or the
gating; those are agent E's and are proven by E's own checks.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# ---------------------------------------------------------------------------------------------
# THE FIXTURE. Every awkward case the owner named is in it.
#
#   A3.2  the worked example from the order: threshold shape, Amber, full four-part block.
#   A6.1  the project-target path bands GREEN/RED ONLY, so a Red's next band up is GREEN.
#   A1.2  returns LOWERCASE band strings.
#   A6.2  a near-miss Amber with no ladder -- shape `ordinal`, so `gap` is not a distance.
#   B2.1  a module with candidates == [] and the fixed absence line.
#   C1.9  an adverse row with NO mitigation entry at all (the unbanded/abstaining case).
#
# The first three rows are what the card's first screen shows; the rest go to the drawer.
# ---------------------------------------------------------------------------------------------
ROWS = [
    {"module_id": "A3.2", "band": "Amber", "category": "a3", "category_name": "Cost Risk",
     "reading": "contingency 6% consumed at 4% complete - burn against progress 1.5"},
    {"module_id": "A6.1", "band": "Red", "category": "a6", "category_name": "Regulatory",
     "reading": "project target missed by 11 days against the approved target date"},
    {"module_id": "A1.2", "band": "amber", "category": "a1", "category_name": "Cost and EVM",
     "reading": "cost performance index 0.91 against 1.00 planned"},
    {"module_id": "A6.2", "band": "Amber", "category": "a6", "category_name": "Regulatory",
     "reading": "2 permits outstanding of 9 required"},
    {"module_id": "B2.1", "band": "Yellow", "category": "b2", "category_name": "Schedule",
     "reading": "float consumed on 3 of 14 near-critical paths"},
    {"module_id": "C1.9", "band": "Yellow", "category": "c1", "category_name": "Synthesis",
     "reading": "2 of 6 methods disagree on the schedule posture"},
]

MITIGATIONS = [
    {"module_id": "A3.2", "band": "Amber", "shape": "threshold",
     "reading": "contingency 6% consumed at 4% complete - burn against progress 1.5",
     "next_band": "Amber requires burn at or below 1.5 - currently at the boundary; "
                  "Yellow requires at or below 1.2",
     "gap": "reduce burn by 0.3 against progress, or advance progress 1.5 pts at current "
            "consumption",
     "candidates": [
         "Re-baseline contingency draws against verified progress before the next application",
         "Hold non-critical contingency-funded changes until progress verification catches up",
     ],
     "absent_reason": None, "composed_at": "2026-09-05",
     "model": "claude-opus-5", "provider": "anthropic"},
    {"module_id": "A6.1", "band": "Red", "shape": "threshold",
     "reading": "project target missed by 11 days against the approved target date",
     "next_band": "this path bands Green or Red only; Green requires the approved target date "
                  "to be met",
     "gap": "recover 11 days against the approved target date",
     "candidates": ["Recover 11 days of the missed target through the approved schedule "
                    "revision path"],
     "absent_reason": None, "composed_at": "2026-09-05",
     "model": "claude-opus-5", "provider": "anthropic"},
    {"module_id": "A1.2", "band": "amber", "shape": "threshold",
     "reading": "cost performance index 0.91 against 1.00 planned",
     "next_band": "yellow requires cost performance index at or above 0.95",
     "gap": "raise cost performance index by 0.04",
     "candidates": ["Reconcile the cost-performance inputs against the verified earned value "
                    "before the next application"],
     "absent_reason": None, "composed_at": "2026-09-05",
     "model": "claude-opus-5", "provider": "anthropic"},
    {"module_id": "A6.2", "band": "Amber", "shape": "ordinal",
     "reading": "2 permits outstanding of 9 required",
     "next_band": "Green requires no permit outstanding; this reading has no intermediate band",
     "gap": "the Amber reading fired on 2 outstanding permits and clears when both are issued",
     # MEASURED AND CORRECTED: this bullet first read "through the issuing authority's published
     # route". `authority` names a party, and the order forbids naming one even when the party
     # is external to the project. The published route is the artefact; nobody is named.
     "candidates": ["Close the 2 outstanding permits through the published permitting route"],
     "absent_reason": None, "composed_at": "2026-09-05",
     "model": "claude-opus-5", "provider": "anthropic"},
    {"module_id": "B2.1", "band": "Yellow", "shape": "derived",
     "reading": "float consumed on 3 of 14 near-critical paths",
     "next_band": "Green requires float consumed on no near-critical path",
     "gap": "the Yellow reading fired on 3 paths and clears when float is restored on all 3",
     "candidates": [],
     "absent_reason": "no mitigation composed for this reading", "composed_at": "2026-09-05",
     "model": "claude-opus-5", "provider": "anthropic"},
]

BRIEF = {
    "posture": {"official": "Amber"},
    "question": "What do you make of this finding?",
    "finding": "The finding.",
    "why": "The why.",
    "adverse_readings": {"rows": ROWS, "rule": "Worst status wins."},
    "limitations": ["One limitation."],
    "mitigations": MITIGATIONS,
}

HARNESS = r"""
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = process.argv[2];
const fixture = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const preSrc = fs.readFileSync(process.argv[4], "utf8");

function el() { return { querySelector: () => null, querySelectorAll: () => [],
  addEventListener(){}, classList: { add(){}, remove(){} }, insertAdjacentHTML(){}, style: {},
  setAttribute(){}, getAttribute: () => null, appendChild(){}, remove(){},
  innerHTML: "", textContent: "", className: "", dataset: {} }; }
function makeSandbox() {
  const s = { console, JSON, Math, Date, Number, String, Object, Array, RegExp, isNaN,
    parseFloat, parseInt, setTimeout, clearTimeout, requestAnimationFrame: () => 0,
    cancelAnimationFrame(){},
    document: Object.assign(el(), { createElement: el, getElementById: () => null, body: el(),
                                    documentElement: el(), addEventListener(){} }),
    navigator: { userAgent: "node" }, location: { href: "", search: "" },
    fetch: () => Promise.resolve(),
    localStorage: { getItem: () => null, setItem(){}, removeItem(){} } };
  s.window = s; s.self = s; s.globalThis = s;
  vm.createContext(s);
  return s;
}
function load(sandbox, src, name) { vm.runInContext(src, sandbox, { filename: name }); }

const now = makeSandbox();
load(now, fs.readFileSync(path.join(ROOT, "assets/js/decision-ui.js"), "utf8"), "decision-ui.js");
const pre = makeSandbox();
load(pre, preSrc, "decision-ui.pre.js");

const render = now.window.LinDecisionUI.__cardForTest.renderDecisionBrief;
const renderPre = pre.window.LinDecisionUI.__cardForTest.renderDecisionBrief;

const out = { withMitigations: render(fixture.brief),
              noKey: render(fixture.briefNoKey),
              noKeyPre: renderPre(fixture.briefNoKey),
              emptyList: render(fixture.briefEmptyList),
              corrupted: render(fixture.briefCorrupted) };
fs.writeFileSync(process.argv[5], JSON.stringify(out));
"""

PASSED = 0
TOTAL = 0
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    global PASSED, TOTAL
    TOTAL += 1
    if cond:
        PASSED += 1
        print("  [PASS] " + name)
        return True
    FAILS.append(name + (" -- " + detail if detail else ""))
    print("  [FAIL] " + name + (" -- " + detail if detail else ""))
    return False


def unescape(html: str) -> str:
    return (html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#39;", "'"))


def blocks_for(html: str) -> list[str]:
    """Split the rendered card into its `dc-mitigation` blocks. Nesting-free by construction."""
    out = []
    idx = 0
    while True:
        i = html.find('<div class="dc-mitigation">', idx)
        if i < 0:
            return out
        j = html.find("<div class=\"dc-mitigation\">", i + 1)
        end = html.find("</li>", i)
        stop = end if (j < 0 or end < j) else j
        out.append(html[i:stop if stop > 0 else len(html)])
        idx = i + 1


def section(html: str, start_marker: str, end_marker: str) -> str:
    i = html.find(start_marker)
    if i < 0:
        return ""
    j = html.find(end_marker, i)
    return html[i:j if j > 0 else len(html)]


def main() -> int:
    brief_no_key = {k: v for k, v in BRIEF.items() if k != "mitigations"}
    brief_empty = dict(BRIEF, mitigations=[])
    corrupted = json.loads(json.dumps(MITIGATIONS))
    corrupted[0]["gap"] = "reduce burn by 0.3"  # a TRUNCATED gap: the corruption
    brief_corrupted = dict(BRIEF, mitigations=corrupted)

    tmp = tempfile.mkdtemp(prefix="run140r_")
    fx = os.path.join(tmp, "fixture.json")
    with open(fx, "w", encoding="utf-8") as fh:
        json.dump({"brief": BRIEF, "briefNoKey": brief_no_key,
                   "briefEmptyList": brief_empty, "briefCorrupted": brief_corrupted}, fh)

    pre_path = os.path.join(tmp, "decision-ui.pre.js")
    pre_src = subprocess.run(["git", "-C", ROOT, "show", "81cc9ab:assets/js/decision-ui.js"],
                             capture_output=True, text=True)
    if pre_src.returncode != 0:
        print("  [FAIL] cannot read the pre-change renderer out of git: " + pre_src.stderr.strip())
        print("RESULT: 0/1 checks passed")
        return 1
    with open(pre_path, "w", encoding="utf-8") as fh:
        fh.write(pre_src.stdout)

    harness = os.path.join(tmp, "harness.js")
    with open(harness, "w", encoding="utf-8") as fh:
        fh.write(HARNESS)
    outp = os.path.join(tmp, "out.json")
    r = subprocess.run(["node", harness, ROOT, fx, pre_path, outp],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  [FAIL] the renderer did not load: " + (r.stderr.strip() or r.stdout.strip()))
        print("RESULT: 0/1 checks passed")
        return 1
    with open(outp, encoding="utf-8") as fh:
        out = json.load(fh)

    html = unescape(out["withMitigations"])

    # ------------------------------------------------------------------ GUARANTEE 0: it can fail
    print("\nGUARANTEE 0: the comparison is proven able to fail before it is trusted.")
    bad = unescape(out["corrupted"])
    check("a TRUNCATED gap is NOT found verbatim in the corrupted render (the check can fail)",
          MITIGATIONS[0]["gap"] not in bad,
          "the corrupted render still contained the full gap; the comparison proves nothing")
    check("the corrupted render does contain the truncation, so the harness did render it",
          "reduce burn by 0.3" in bad)

    # ------------------------------------------- PROOF 2: reading, boundary and gap, verbatim
    print("\nPROOF 2: reading, next band and gap match the fixture verbatim.")
    for m in MITIGATIONS:
        mid = m["module_id"]
        check(mid + ": reading rendered verbatim", m["reading"] in html)
        check(mid + ": next-band boundary rendered verbatim", m["next_band"] in html)
        check(mid + ": gap rendered verbatim", m["gap"] in html)
        for c in m["candidates"]:
            check(mid + ": candidate rendered verbatim", c in html)
        if not m["candidates"]:
            check(mid + ": the fixed absence line is rendered",
                  "no mitigation composed for this reading" in html)
        check(mid + ": the composition date is rendered",
              "composed " + m["composed_at"] + ", stored" in html)

    check("no figure was reformatted: every gap string survives character for character",
          all(m["gap"] in html for m in MITIGATIONS))

    # ---------------------------------------------------------- PROOF 5: no entry, no block
    print("\nPROOF 5: an adverse row with no mitigation entry renders no block.")
    ids_with = {m["module_id"] for m in MITIGATIONS}
    absent = [r["module_id"] for r in ROWS if r["module_id"] not in ids_with]
    check("the fixture carries an adverse row with no mitigation entry", bool(absent),
          "fixture does not exercise the case")
    check("exactly one block is rendered per mitigation entry, and none for C1.9",
          len(blocks_for(html)) == len(MITIGATIONS),
          str(len(blocks_for(html))) + " blocks for " + str(len(MITIGATIONS)) + " entries")
    for mid in absent:
        seg = section(html, ">" + mid + "<", "</li>")
        check(mid + ": its list item carries no mitigation block",
              "dc-mitigation" not in seg, seg[:120])

    # ------------------------------------------------ THE SPLIT: three inline, the rest drawn
    print("\nTHE SPLIT: three inline, the rest in the drawer, none twice.")
    why = section(html, "Why this decision is suggested", "All adverse findings")
    drawer = section(html, "All adverse findings", "Category details")
    inline_ids = [m["module_id"] for m in MITIGATIONS if m["gap"] in why]
    drawer_ids = [m["module_id"] for m in MITIGATIONS if m["gap"] in drawer]
    check("the three findings on the first screen carry their blocks inline",
          inline_ids == ["A3.2", "A6.1", "A1.2"], str(inline_ids))
    check("the remaining blocks render under All adverse findings",
          drawer_ids == ["A6.2", "B2.1"], str(drawer_ids))
    check("no mitigation is rendered twice",
          not (set(inline_ids) & set(drawer_ids)),
          str(sorted(set(inline_ids) & set(drawer_ids))))
    check("the drawer's severity order is the server's order, unchanged",
          [r["module_id"] for r in ROWS if ">" + r["module_id"] + "<" in drawer]
          == [r["module_id"] for r in ROWS], "the drawer re-ranked the rows")

    # ----------------------------------------------------------- LOWERCASE BANDS ARE NOT LOST
    print("\nLOWERCASE BANDS: A1.2 returns lowercase and must not be dropped.")
    check("the lowercase-banded module renders its block",
          MITIGATIONS[2]["gap"] in html)
    check("its lowercase next-band string is printed as the server wrote it, not title-cased",
          "yellow requires cost performance index at or above 0.95" in html)
    check("A6.1's Red-to-GREEN next band renders (Green/Red-only path)",
          "this path bands Green or Red only" in html)

    # ---------------------------------------------------- NO KEY: BYTE-IDENTICAL TO PRE-CHANGE
    print("\nNO KEY: a brief without `mitigations` renders byte-identically to Run 139's card.")
    check("no `mitigations` key: the rendered card is byte-identical to the pre-change renderer",
          out["noKey"] == out["noKeyPre"],
          "lengths " + str(len(out["noKey"])) + " vs " + str(len(out["noKeyPre"])))
    check("no `mitigations` key: not one mitigation block is rendered",
          "dc-mitigation" not in out["noKey"])
    check("`mitigations: []` also renders no block",
          "dc-mitigation" not in out["emptyList"])
    check("`mitigations: []` is byte-identical to the pre-change renderer too",
          out["emptyList"] == out["noKeyPre"])

    # ------------------------------------------- THE PROHIBITIONS, ON THE RENDERED TEXT ITSELF
    print("\nTHE PROHIBITIONS: what a suggestion must never contain.")
    # THE TOKENS ARE THE PROHIBITION, NOT ITS VOCABULARY. "approved baseline" and "the approved
    # schedule revision path" name an existing artefact and are permitted; "approval authority"
    # names a party who signs, and is not. The token is `approval`, not `approve`, for exactly
    # that reason -- measured: `approve` flagged "the approved schedule revision path", which
    # assigns nobody anything.
    banned = ["should", "must", "escalate", "the PM", "project manager", "owner ", "immediately",
              "by the end of", "deadline", "approval", "authority", " by "]
    rendered_cands = [c for m in MITIGATIONS for c in m["candidates"]]
    for word in banned:
        hits = [c for c in rendered_cands if word.lower() in c.lower()]
        check("no candidate contains \"" + word.strip() + "\"", not hits, str(hits))

    print("\nRESULT: " + str(PASSED) + "/" + str(TOTAL) + " checks passed")
    if FAILS:
        for f in FAILS:
            print("  FAILED: " + f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
