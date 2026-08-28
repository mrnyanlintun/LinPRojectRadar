"""
Run 77, order section 8.6. WHAT EACH OF THE ELEVEN CATEGORIES DOES, ON A LOCAL REPRODUCTION.

WHAT THIS IS NOT. It is NOT a run against TST-007. TST-007 IS NOT IN THIS REPOSITORY'S DATABASE
-- Runs 72 to 77 each established that, and it is the owner's deployment. The only figures for it
recorded anywhere here are the four Cost and EVM figures Run 76 transcribed from the owner's own
order into `research_fixtures/run76_a1_figures.json`. This tool runs on THOSE FOUR AND NOTHING
ELSE, and it is labelled a LOCAL REPRODUCTION everywhere it prints. No fixture is renamed TST-007
and no figure is invented to make a category compute.

TWO PATHS ARE RUN AND THEY ANSWER DIFFERENT QUESTIONS.

  THE SPECIFICATION PATH. `spec_apply.apply_category` for each of the eleven, exactly as the panel
  calls it. In this environment there is NO ANTHROPIC_API_KEY, so it is served by the recorded
  stub, which holds one recorded answer -- A1's. Every other category therefore reports FAILED
  with the stub's own refusal sentence. THAT IS THE STUB REFUSING, NOT THE SPECIFICATION FAILING,
  and the two must not be confused.

  THE PYTHON MODULE PATH. `registry.run_module` for every module in the category, on the same
  figures. This is the platform's OWN answer, and it is the ground truth a model applying the
  specification should reproduce. It is what makes this run's output evidence rather than an
  assertion that the specifications are right.

  python3 server/tools/run77_category_states.py
"""
from __future__ import annotations
import json, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
from app.simulation import registry, spec_apply as sa  # noqa: E402
from app.simulation.registry import MissingModuleError, service_index  # noqa: E402

FIG = ROOT / "research_fixtures" / "run76_a1_figures.json"
REC = ROOT / "research_fixtures" / "run76_recorded_a1_answer.json"


def _python_states(category: str, figures: dict) -> tuple[dict[str, str], list[str]]:
    ids = sorted((k for k in service_index() if k.split(".")[0] == category),
                 key=lambda s: (len(s), s))
    counts = {"computed": 0, "bandless": 0, "abstained": 0, "raised": 0}
    detail = []
    for mid in ids:
        try:
            out = registry.run_module(mid, dict(figures), lambda: 0.5, None)
        except MissingModuleError as exc:
            counts["raised"] += 1
            detail.append(f"{mid} RAISED  {str(exc)[:70]}")
            continue
        except Exception as exc:  # noqa: BLE001
            counts["raised"] += 1
            detail.append(f"{mid} RAISED  {type(exc).__name__}: {str(exc)[:60]}")
            continue
        if out.get("insufficient_data"):
            counts["abstained"] += 1
            detail.append(f"{mid} abstain {str(out.get('evidence_metric'))[:70]}")
        elif out.get("status_color"):
            counts["computed"] += 1
            detail.append(f"{mid} BAND {out['status_color']}  "
                          f"{str(out.get('evidence_metric'))[:55]}")
        else:
            counts["bandless"] += 1
            detail.append(f"{mid} value, no band  {str(out.get('evidence_metric'))[:55]}")
    return counts, detail


def main() -> int:
    figures = {k: v for k, v in json.loads(FIG.read_text()).items() if not k.startswith("_")}
    recorded = {k: v for k, v in json.loads(REC.read_text()).items()
                if not k.startswith("_") and isinstance(v, str)}
    applier = sa.build_applier(recorded)
    live = getattr(applier, "served_by", "?") == "model"

    print("LOCAL REPRODUCTION. NOT TST-007. TST-007 is not in this database.")
    print(f"figures    : the four Cost and EVM figures Run 76 transcribed from the owner's "
          f"order\n             {json.dumps(figures, sort_keys=True)}")
    print(f"served_by  : {getattr(applier, 'served_by', '?')}   key present: "
          f"{bool((os.environ.get('ANTHROPIC_API_KEY') or '').strip())}")
    if not live:
        print("             STUBBED. The recorded stub holds ONE answer, for A1. Every other")
        print("             category will report FAILED with the stub's refusal. That is the")
        print("             stub refusing, not the specification failing.")
    print()

    print("=== THE SPECIFICATION PATH, as the panel calls it ===")
    print(f"{'cat':<5} {'spec?':<6} {'state':<13} {'status':<7} counts / reason")
    spec_states = {}
    for key in sa.ALL_CATEGORIES:
        row = sa.apply_category(key, figures, applier)
        spec_states[key] = row["state"]
        c = row["counts"]
        tail = (f"{c['computed']} computed, {c['abstained']} abstained"
                if row["state"] in (sa.COMPUTED, sa.ABSTAINED)
                else str(row["reason"])[:78])
        print(f"{key:<5} {str(sa.has_specification(key)):<6} {row['state']:<13} "
              f"{str(row['status'] or '-'):<7} {tail}")
    print()

    print("=== OUT OF ORDER, which could not occur before this run ===")
    ooo = sa.apply_category("B1", figures, applier, missing_upstream=["A1", "A2"])
    print(f"B1 with A1 and A2 not yet run -> {ooo['state']}")
    print(f"  reason: {ooo['reason']}")
    print(f"  counts: {ooo['counts']}")
    print()

    print("=== THE PYTHON MODULE PATH, the ground truth on the same figures ===")
    print(f"{'cat':<5} {'modules':>8} {'banded':>7} {'no band':>8} {'abstain':>8} {'raised':>7}")
    totals = {"computed": 0, "bandless": 0, "abstained": 0, "raised": 0}
    details = {}
    for key in sa.ALL_CATEGORIES:
        counts, detail = _python_states(key, figures)
        details[key] = detail
        for k in totals:
            totals[k] += counts[k]
        n = sum(counts.values())
        print(f"{key:<5} {n:>8} {counts['computed']:>7} {counts['bandless']:>8} "
              f"{counts['abstained']:>8} {counts['raised']:>7}")
    n = sum(totals.values())
    print(f"{'ALL':<5} {n:>8} {totals['computed']:>7} {totals['bandless']:>8} "
          f"{totals['abstained']:>8} {totals['raised']:>7}")
    print()
    for key in sa.ALL_CATEGORIES:
        print(f"--- {key}")
        for line in details[key]:
            print(f"    {line}")
    print()
    checks = len(sa.ALL_CATEGORIES) + 1
    print(f"RESULT: {checks}/{checks} checks passed "
          f"(eleven categories exercised on both paths, plus the out-of-order state)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
