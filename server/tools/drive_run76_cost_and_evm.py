"""
Run 76, order section 10 item 3. CALL COST AND EVM ON THE ORDER'S FIGURES AND REPORT WHAT CAME
BACK, and hand-compute TCPI beside it.

WHAT IS EXERCISED FOR REAL: the specification file, the prompt build, the client selection, the
answer parse, every state check in `normalise_module`, the four-state counts, and the Python
fusion. WHAT IS NOT: the model. There is no ANTHROPIC_API_KEY here, so the recorded applier
serves a hand-authored fixture and every row is stamped served_by "recorded". The line this
prints says which.
"""
from __future__ import annotations
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
from app.simulation import spec_apply as sa  # noqa: E402

FIX = ROOT / "research_fixtures"
recorded = json.loads((FIX / "run76_recorded_a1_answer.json").read_text())
figures = json.loads((FIX / "run76_a1_figures.json").read_text())
figures = {k: v for k, v in figures.items() if not k.startswith("_")}

applier = sa.build_applier({k: v for k, v in recorded.items() if not k.startswith("_")})
print(f"applier      : {type(applier).__name__}  served_by={applier.served_by}  "
      f"model_id={applier.model_id}")
print(f"specification: {sa.specification_path('A1')}")
print(f"figures      : {json.dumps(figures, sort_keys=True)}")
print()

row = sa.apply_category("A1", figures, applier)
print(f"category state : {row['state']}")
print(f"category status: {row['status']}   (fused in Python by fusion.worst_band)")
print(f"counts         : {json.dumps(row['counts'])}")
print(f"served_by      : {row['served_by']}")
print()
for m in row["modules"]:
    if m["state"] == "computed":
        print(f"  {m['module_id']:<6} COMPUTED   value={m['value']!r}  display={m['display']}  "
              f"band={m['band']}")
    else:
        print(f"  {m['module_id']:<6} ABSTAINED  {m['reason'][:88]}")
print()

BAC, EV, AC = 18441300, 2217200, 2186400
hand = (BAC - EV) / (BAC - AC)
returned = next(m for m in row["modules"] if m["module_id"] == "A1.7")
print("--- section 10 item 3, the hand computed TCPI check ---")
print(f"  hand     : ({BAC} - {EV}) / ({BAC} - {AC}) = {BAC-EV} / {BAC-AC} = {hand!r}")
print(f"  returned : {returned['value']!r}")
print(f"  order's expected value: 0.998   returned display: {returned['display']}")
print(f"  identical: {hand == returned['value']}   band: {returned['band']}  "
      f"(<= 1.00, the sourced definitional boundary)")

print()
print("--- the four states, all four produced, none of them the same thing ---")
states = {}
states["computed/abstained"] = row
states["out_of_order"] = sa.apply_category("A1", figures, applier,
                                           missing_upstream=["A1", "A2"])
states["failed(no specification)"] = sa.apply_category("A2", figures, applier)
states["failed(unusable answer)"] = sa.apply_category(
    "A1", figures, sa.RecordedSpecApplier({"A1": "the model said something that is not JSON"}))
for label, r in states.items():
    print(f"  {label:<26} state={r['state']:<13} counts={json.dumps(r['counts'])} "
          f"reason={(r['reason'] or '')[:60]}")

print()
print("--- section 3, the two passes, and how a pass one failure reaches pass two ---")
broken = sa.RecordedSpecApplier({})            # A1 has a spec but no recorded answer -> FAILED
full = sa.run_two_pass(figures, broken)
print(f"  pass one A1 state : {full['categories']['A1']['state']}")
print(f"  what pass two is told about A1:")
print(f"    {json.dumps(full['upstream_report']['A1'], indent=4)}")
print(f"  project status    : {full['project_status']}")
ok = sa.run_two_pass(figures, applier)
print(f"  with A1 applied   : A1={ok['categories']['A1']['state']}  "
      f"status={ok['categories']['A1']['status']}  project={ok['project_status']}")
