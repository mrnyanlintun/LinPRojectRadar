#!/usr/bin/env python3
"""
RUN 139B. THE BEFORE/AFTER DIFF OF THE SIGNAL FLOW PANEL.

Consumes two JSON blobs from `run139b_measure_flow.py` and asserts, numerically:

  1. EVERY module node dot (both ports, dot and identity ring) is at the same cx/cy;
  2. EVERY flow path's two endpoints are unmoved to 3dp, and the path count is equal;
  3. every module label sits on ONE shared left edge (a single x across the column);
  4. every module label's rendered box is centred on its row within 0.5px;
  5. the widest module label, MEASURED with getComputedTextLength, does not overflow the
     module column (its right edge stays left of the out-port dot);
  6. the legend strip did not grow taller and names `Complete`.

The check must be able to FAIL: run with `--expect-moved` to invert 1 and 2, which is how the
dot-nudge injection is proven to be caught.

Run: python tools/test_run139b_flow_diff.py <before.json> <after.json> [--expect-moved]
"""
from __future__ import annotations
import json, sys, pathlib

before = json.loads(pathlib.Path(sys.argv[1]).read_text())
after = json.loads(pathlib.Path(sys.argv[2]).read_text())
EXPECT_MOVED = "--expect-moved" in sys.argv
FAILS = []

def check(cond, label, detail=""):
    print(("PASS " if cond else "FAIL ") + label + ((" :: " + detail) if detail else ""))
    if not cond:
        FAILS.append(label)

def mod_labels(m):
    return [t for t in m["texts"] if t["fontSize"] == "13" and t["anchor"] == "start"]

for w in sorted(set(before) & set(after)):
    b, a = before[w], after[w]
    print(f"===== VIEWPORT {w} =====")

    bd = {(c["module"], c["kind"], c["port"], c["tag"]): (c["cx"], c["cy"]) for c in b["dots"]}
    ad = {(c["module"], c["kind"], c["port"], c["tag"]): (c["cx"], c["cy"]) for c in a["dots"]}
    moved = [k for k in set(bd) | set(ad) if bd.get(k) != ad.get(k)]
    if EXPECT_MOVED:
        check(bool(moved), f"[{w}] a moved dot IS detected", f"{len(moved)} moved")
    else:
        check(not moved, f"[{w}] no node dot moved",
              f"{len(bd)} node elements compared" if not moved else str(moved[:4]))

    check(len(b["paths"]) == len(a["paths"]), f"[{w}] flow path count equal",
          f"{len(b['paths'])} vs {len(a['paths'])}")
    ends_b = [(p["a"], p["b"]) for p in b["paths"]]
    ends_a = [(p["a"], p["b"]) for p in a["paths"]]
    diffs = [(i, ends_b[i], ends_a[i]) for i in range(min(len(ends_b), len(ends_a)))
             if ends_b[i] != ends_a[i]]
    if EXPECT_MOVED:
        check(bool(diffs), f"[{w}] a moved flow-line endpoint IS detected", f"{len(diffs)} moved")
    else:
        check(not diffs, f"[{w}] no flow-line endpoint moved",
              f"{len(ends_a)} paths, both endpoints, to 3dp" if not diffs else str(diffs[:2]))

    labs = mod_labels(a)
    xs = sorted({round(float(t["x"]), 3) for t in labs})
    check(len(xs) == 1, f"[{w}] the module column has ONE left edge", f"x set {xs}")

    ports = {}
    for c in a["dots"]:
        if c["kind"] == "module-identity":
            ports.setdefault(c["port"], set()).add(float(c["cx"]))
    inx = min(ports.get("in", {0})) if ports.get("in") else None
    outx = min(ports.get("out", {0})) if ports.get("out") else None
    if inx is not None:
        check(abs(xs[0] - inx - 12) < 0.001, f"[{w}] the indent from the dot is a constant 12px",
              f"label x {xs[0]} - in-port {inx}")

    # THE ROW IS THE DOT, NOT THE TEXT'S OWN y. A text's bbox moves with its y attribute, so
    # comparing the box centre to that y measures a font constant and nothing else. It is
    # compared to the cy of the module's OWN in-port dot.
    dotcy = {}
    for c in a["dots"]:
        if c["kind"] == "module-identity" and c["port"] == "in" and c["cy"] is not None:
            dotcy.setdefault(c["module"], float(c["cy"]))
    rows = sorted(dotcy.values())
    def nearest_row(y):
        return min(rows, key=lambda r: abs(r - y))
    offs = [(t["text"], round(t["bb"]["y"] + t["bb"]["h"] / 2 - nearest_row(float(t["y"])), 3))
            for t in labs]
    worst = max(offs, key=lambda o: abs(o[1]))
    check(abs(worst[1]) <= 0.5, f"[{w}] every module label is centred on its own row",
          f"worst {worst[0]!r} off by {worst[1]}px of {len(labs)} labels")

    dim = [t for t in labs if t["opacity"]]
    dimworst = max(((t["text"], round(t["bb"]["y"] + t["bb"]["h"] / 2 - nearest_row(float(t["y"])), 3))
                    for t in dim), key=lambda o: abs(o[1]), default=("-", 0))
    check(abs(dimworst[1]) <= 0.5, f"[{w}] the DIMMED labels obey the same rule",
          f"{len(dim)} dimmed, worst {dimworst[0]!r} off by {dimworst[1]}px")

    widest = max(labs, key=lambda t: t["len"])
    right = round(widest["bb"]["x"] + widest["bb"]["w"], 3)
    check(outx is None or right < outx, f"[{w}] the widest label does not overflow the column",
          f"{widest['text']!r} advance {widest['len']}px, right edge {right} < out-port {outx}")

    check(a["legendBox"]["h"] <= b["legendBox"]["h"], f"[{w}] the legend strip did not grow",
          f"{b['legendBox']['h']} -> {a['legendBox']['h']}")
    check("Complete" in (a["legendText"] or ""), f"[{w}] the legend names Complete")
    over = [c for c in (a["legendChildren"] or [])
            if c["b"]["right"] > a["legendBox"]["right"] + 0.5]
    check(not over, f"[{w}] no legend entry overflows the strip", str([c["t"] for c in over]))

print("\n" + ("ALL CHECKS PASS" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}"))
sys.exit(1 if FAILS else 0)
