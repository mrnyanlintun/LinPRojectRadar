"""
Run 76, order section 8. THE REPRODUCIBILITY MEASUREMENT.

THE QUESTION IT ANSWERS. Reproducibility is no longer guaranteed by construction. A model
applying a written formula to the same figures will almost certainly return the same number, but
almost certainly is not provably, and the place it can vary is at a band boundary. So: call one
category repeatedly on IDENTICAL inputs and report how many times each module's value changed and
how many times its band changed.

A VALUE MOVING IN THE LAST DECIMAL PLACE WHILE THE BAND HOLDS IS ACCEPTABLE. A BAND MOVING IS THE
FINDING, and this tool names exactly which module and which threshold.

WHAT THIS TOOL MEASURES DEPENDS ENTIRELY ON WHICH CLIENT SERVES IT, AND IT SAYS SO ON EVERY RUN:

  served_by=model     the answer to section 8. Requires ANTHROPIC_API_KEY.
  served_by=recorded  A DETERMINISTIC FIXTURE. It returns identical output by construction, so a
                      zero-variance result MEASURES THIS HARNESS AND NOT THE MODEL. It is not
                      evidence about reproducibility and must never be reported as if it were.

    python3 server/tools/run76_variance.py --iterations 20 --category A1
"""
from __future__ import annotations
import argparse, json, os, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
from app.simulation import spec_apply as sa  # noqa: E402

FIX = ROOT / "research_fixtures"


class _JitterApplier:
    """Moves A1.7 across the sourced 1.00 boundary on alternate calls, and nothing else."""

    served_by = "selftest-jitter"
    model_id = "selftest-jitter"

    def __init__(self, base: str) -> None:
        self._base = json.loads(base)
        self._n = 0

    def apply(self, category_key: str, prompt: str) -> str:
        self._n += 1
        out = json.loads(json.dumps(self._base))
        for m in out.get("modules", []):
            if m.get("module_id") == "A1.7":
                # 0.9981... on one call, 1.0018... on the next. Same module, same figures,
                # opposite sides of the definitional boundary.
                m["value"] = 0.9981051867436896 if self._n % 2 else 1.0018948132563104
                m["band"] = "Green" if self._n % 2 else "Amber"
        return json.dumps(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=20)
    ap.add_argument("--category", default="A1")
    ap.add_argument("--figures", default=str(FIX / "run76_a1_figures.json"))
    ap.add_argument("--recorded", default=str(FIX / "run76_recorded_a1_answer.json"))
    ap.add_argument("--selftest", action="store_true",
                    help="NON-VACUITY PROOF. Substitutes an applier that deliberately moves "
                         "A1.7 across the 1.00 boundary on alternate calls. If this run does "
                         "not report a band move, the measurement above is incapable of "
                         "finding one and its zero means nothing.")
    args = ap.parse_args()

    figures = {k: v for k, v in json.loads(pathlib.Path(args.figures).read_text()).items()
               if not k.startswith("_")}
    recorded = {}
    p = pathlib.Path(args.recorded)
    if p.is_file():
        recorded = {k: v for k, v in json.loads(p.read_text()).items()
                    if not k.startswith("_")}
    applier = sa.build_applier(recorded)
    if args.selftest:
        applier = _JitterApplier(recorded.get(args.category, "{}"))
    live = getattr(applier, "served_by", "unknown") == "model"

    print(f"category   : {args.category}")
    print(f"iterations : {args.iterations}")
    print(f"served_by  : {getattr(applier, 'served_by', '?')}   "
          f"model_id: {getattr(applier, 'model_id', '?')}")
    print(f"key present: {bool((os.environ.get('ANTHROPIC_API_KEY') or '').strip())}")
    if args.selftest:
        print("NOTE       : SELF-TEST. The applier deliberately moves A1.7 across the 1.00 "
              "boundary.\n             If no band move is reported below, the measurement "
              "cannot find one.")
    elif not live:
        print("WARNING    : this run is served by a DETERMINISTIC RECORDED FIXTURE. A zero here "
              "measures\n             this harness, NOT the model, and is not evidence about "
              "reproducibility.")
    print()

    values: dict[str, list] = {}
    bands: dict[str, list] = {}
    states: dict[str, list] = {}
    failures = 0
    t0 = time.time()
    for i in range(args.iterations):
        row = sa.apply_category(args.category, figures, applier)
        if row["state"] == sa.FAILED:
            failures += 1
            print(f"  iteration {i + 1:>3}: FAILED -- {row['reason'][:100]}")
            continue
        for m in row["modules"]:
            values.setdefault(m["module_id"], []).append(m["value"])
            bands.setdefault(m["module_id"], []).append(m["band"])
            states.setdefault(m["module_id"], []).append(m["state"])
    elapsed = time.time() - t0

    ok = args.iterations - failures
    print(f"completed  : {ok}/{args.iterations} calls in {elapsed:.1f}s "
          f"({failures} failed)")
    print()
    print(f"{'module':<8} {'runs':>5} {'value changed':>14} {'band changed':>13} "
          f"{'state changed':>14}  modal band")
    band_moves = []
    for mid in sorted(values, key=lambda s: (len(s), s)):
        vs, bs, ss = values[mid], bands[mid], states[mid]
        vchg = sum(1 for a, b in zip(vs, vs[1:]) if a != b)
        bchg = sum(1 for a, b in zip(bs, bs[1:]) if a != b)
        schg = sum(1 for a, b in zip(ss, ss[1:]) if a != b)
        modal = max(set(bs), key=bs.count)
        print(f"{mid:<8} {len(vs):>5} {vchg:>14} {bchg:>13} {schg:>14}  {modal}")
        if bchg:
            band_moves.append((mid, sorted(set(str(b) for b in bs))))
    print()
    if band_moves:
        print("BANDS MOVED. This is the finding of section 8:")
        for mid, seen in band_moves:
            print(f"  {mid}: bands seen across the run -> {seen}")
    else:
        print("No band moved across the run.")
        if args.selftest:
            print("  SELF-TEST FAILED: the measurement did not detect a band move that was "
                  "deliberately introduced. Its zero above means nothing.")
        elif not live:
            print("  BUT: served by the recorded fixture, so this states nothing about the "
                  "model.")
    print()
    print(f"RESULT: {ok}/{args.iterations} calls completed, "
          f"{len(band_moves)} module(s) moved band")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
