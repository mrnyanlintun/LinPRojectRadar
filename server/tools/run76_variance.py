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

RUN 77 EXTENSION: --project and --period. Run 76's tool could only measure the one category whose
figures were captured in a fixture. All eleven categories now have specifications, so the owner
needs to measure ANY of them, on HIS OWN stored figures rather than on a fixture. With --project
and --period the figures are read from `computed_results.signal_inputs` for that project and
period -- the same row the panel reads, unfiltered and unrenamed -- so the measurement runs on
exactly what the panel ran on:

    DATABASE_URL=... python3 server/tools/run76_variance.py \
        --project TST-007 --period 1 --category A4 --iterations 20

Without --project the fixture path is unchanged and Run 76's invocation still works.
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


def _figures_from_database(project_ref: str, period: int):
    """
    The project's OWN stored figures for one period, read from the same row the panel reads.

    Returns (figures, description) or (None, the reason it could not be read). Nothing is
    selected, filtered or renamed: a specification names its inputs by their exact
    `signal_inputs` field names and it must see the row exactly as stored.
    """
    if not (os.environ.get("DATABASE_URL") or "").strip():
        return None, ("DATABASE_URL is not set, so the stored figures cannot be read. Set it to "
                      "the same database the panel reads.")
    try:
        from sqlalchemy import select
        from app.db import SessionLocal
        from app.models import ComputedResult, Project
    except Exception as exc:  # noqa: BLE001
        return None, f"the server package could not be imported: {type(exc).__name__}: {exc}"
    with SessionLocal() as session:
        # MATCHED ON `legacy_id`, which is the display id the owner types and the only
        # identifier that appears in an /exec request. `Project.id` is a UUID and comparing it
        # against a typed string is a database error, not a miss.
        project = session.scalars(
            select(Project).where(Project.legacy_id == project_ref)).first()
        if project is None:
            return None, (f"no project matches {project_ref!r} in this database. The measurement "
                          f"reads real stored figures and invents none.")
        result = session.scalars(
            select(ComputedResult).where(
                ComputedResult.project_id == project.id,
                ComputedResult.period == period,
                ComputedResult.superseded_by.is_(None))).first()
        if result is None:
            return None, (f"{project_ref} has no live computed result for period {period}, so "
                          f"there are no stored figures to measure against.")
        figures = dict(result.signal_inputs or {})
    return figures, f"{project_ref} period {period} stored signal_inputs"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=20)
    ap.add_argument("--category", default="A1")
    ap.add_argument("--figures", default=str(FIX / "run76_a1_figures.json"))
    ap.add_argument("--recorded", default=str(FIX / "run76_recorded_a1_answer.json"))
    ap.add_argument("--project", default=None,
                    help="Read the figures from this project's stored signal_inputs instead of "
                         "from a fixture. Takes the display id, e.g. TST-007. Requires "
                         "DATABASE_URL and --period.")
    ap.add_argument("--period", type=int, default=None,
                    help="The reporting period to read figures for. Required with --project.")
    ap.add_argument("--selftest", action="store_true",
                    help="NON-VACUITY PROOF. Substitutes an applier that deliberately moves "
                         "A1.7 across the 1.00 boundary on alternate calls. If this run does "
                         "not report a band move, the measurement above is incapable of "
                         "finding one and its zero means nothing.")
    args = ap.parse_args()

    if args.project:
        if args.period is None:
            print("--project requires --period", file=sys.stderr)
            return 2
        figures, source = _figures_from_database(args.project, args.period)
        if figures is None:
            print(source, file=sys.stderr)
            return 2
    else:
        figures = {k: v for k, v in json.loads(pathlib.Path(args.figures).read_text()).items()
                   if not k.startswith("_")}
        source = f"fixture {pathlib.Path(args.figures).name}"
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
    print(f"figures    : {source}   ({len(figures)} stored fields)")
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
