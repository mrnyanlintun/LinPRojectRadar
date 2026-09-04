"""Run 135B / S6 — percentile parity across the Python/JS language boundary.

backend/simulations.py declares itself a "Python port of the five client-side JS
simulation models", so assets/js/simulations.js is the original and the backend is
the transcription. Before this check they disagreed: the backend's
`multipliers[int(len(multipliers) * 0.8)]` selected index 7 (multiplier 1.45) where
the browser's `pctile` selects index 6 (1.38) — on a BAC of 10,000,000 an
overstatement of about $700,000 in the P80 cost prior.

A helper cannot be shared across the language boundary, so instead this check
evaluates BOTH implementations on the same fixture grid and fails when they diverge.
It also pins the one figure the whole finding turned on: the RCF P80 on BAC
10,000,000.

Requires node on PATH (used only to evaluate assets/js/simulations.js in isolation —
no network, no browser). If node is absent the check reports SKIP and exits 2, which
is neither a pass nor a silent success.

Run:  python backend/test_run135b_percentile_parity.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JS = os.path.join(ROOT, "assets", "js", "simulations.js")

sys.path.insert(0, HERE)
import simulations  # noqa: E402

FAILED = []


def check(ok, label):
    print(("PASS  " if ok else "FAIL  ") + label)
    if not ok:
        FAILED.append(label)


# The shared fixture grid. Arrays chosen to exercise the boundaries the two
# definitions disagreed on: the RCF multiplier array itself, lengths where
# q*(n-1) lands exactly on an integer and where it does not, and n=1.
ARRAYS = [
    [1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52],   # the RCF multipliers
    [1.0],
    [1.0, 2.0],
    [1.0, 2.0, 3.0],
    [0.0, 0.25, 0.5, 0.75, 1.0],
    [float(i) for i in range(10)],
    [float(i) for i in range(11)],
    [float(i) * 0.1 for i in range(100)],
]
QUANTILES = [0.0, 0.1, 0.25, 0.5, 0.75, 0.8, 0.9, 0.95, 1.0]


def js_pctile_grid():
    """Evaluate assets/js/simulations.js's own pctile over the grid, via node."""
    script = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
// simulations.js is an IIFE that publishes onto `window`. Give it one, then reach
// pctile through the module's own runRCF is not possible (pctile is private), so
// evaluate the file and re-declare nothing: instead we extract the function source
// verbatim from the file and evaluate exactly that text. If the extraction fails the
// check fails loudly rather than falling back to a local reimplementation.
const m = src.match(/function pctile\(sortedAsc, q\)\s*\{[\s\S]*?\n  \}/);
if (!m) { console.error('MARKER_MOVED: could not locate pctile in ' + process.argv[1]); process.exit(3); }
const clampSrc = src.match(/function clamp\(v, lo, hi\)[^\n]*\n/);
if (!clampSrc) { console.error('MARKER_MOVED: could not locate clamp'); process.exit(3); }
const fn = new Function(clampSrc[0] + m[0] + '\nreturn pctile;')();
const grid = JSON.parse(process.argv[2]);
const out = [];
for (const arr of grid.arrays) {
  for (const q of grid.quantiles) {
    const v = fn(arr.slice().sort((a, b) => a - b), q);
    out.push(v);
  }
}
process.stdout.write(JSON.stringify(out));
"""
    payload = json.dumps({"arrays": ARRAYS, "quantiles": QUANTILES})
    p = subprocess.run(["node", "-e", script, "--", JS, payload],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("node failed (%d): %s" % (p.returncode, p.stderr.strip()))
    return json.loads(p.stdout)


def py_pctile_grid():
    out = []
    for arr in ARRAYS:
        s = sorted(arr)
        for q in QUANTILES:
            out.append(simulations._pctile(s, q))
    return out


if __name__ == "__main__":
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
    except Exception:
        print("SKIP  node is not available; percentile parity was NOT verified")
        sys.exit(2)

    js = js_pctile_grid()
    py = py_pctile_grid()

    check(len(js) == len(py) == len(ARRAYS) * len(QUANTILES),
          "S6: both implementations returned a value for every fixture point")
    diverged = [(i, a, b) for i, (a, b) in enumerate(zip(py, js)) if a != b]
    for i, a, b in diverged[:10]:
        print("      divergence at grid point %d: python %r vs js %r" % (i, a, b))
    check(not diverged,
          "S6: backend _pctile and browser pctile agree on every fixture point (%d points)"
          % (len(ARRAYS) * len(QUANTILES)))

    # The figure the finding turned on. 1.38 is the browser's index-6 multiplier;
    # the source is assets/js/simulations.js, not the backend function under test.
    r = simulations.run_rcf({"bac": 10_000_000})
    check(r["debiasing_factor"] == 1.38,
          "S6: RCF P80 multiplier is 1.38 (browser index 6), not 1.45 (backend index 7)")
    check(r["rcf_p80_adjusted"] == 13_800_000,
          "S6: RCF P80 on BAC 10,000,000 is $13,800,000, not $14,500,000")
    check(r["rcf_p50_adjusted"] == 11_500_000,
          "S6: RCF P50 on BAC 10,000,000 is unchanged at $11,500,000")

    print("\n%d checks, %d failed" % (5, len(FAILED)))
    sys.exit(1 if FAILED else 0)
