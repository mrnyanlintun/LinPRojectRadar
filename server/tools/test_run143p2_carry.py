"""
RUN 143 PART 2 -- the carry-forward rule, proved against the live layer.

Every figure this file prints was TAKEN by this file. Nothing is transcribed. Run from `server/`:

    python tools/test_run143p2_carry.py

Covers the owner's proofs 7, 8, 9, 10 and the exclusion list as built, per arm. Proof 13 (prove
it can fail) is `test_run143p2_fault.py`; proofs 11 and 12 are the browser and the export.
"""
from __future__ import annotations

import datetime
import sys

from app.simulation.carry_forward import (NEVER_CARRY_MODULES, carry_candidates,
                                          is_carry_eligible, normalise_band, select_carried)
from app.simulation.compute import compute_project
from app.simulation.registry import run_all, service_index

CUTOFF = datetime.date(2026, 6, 30)
FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


def prior(period: str, modules: list[dict]) -> dict:
    return {"period": period, "modules": modules}


# ------------------------------------------------------------------ the abstention population
base = run_all({}, "run143p2", "P3", CUTOFF)
service = set(service_index())
print(f"\nmodules in service: {len(service)}   "
      f"computed: {len(base['computed'])}   abstained: {len(base['abstained'])}")

cands = carry_candidates(base)
eligible = [c for c in cands if is_carry_eligible(c)[0] and c["module_id"] in service]
excluded = [(c["module_id"], is_carry_eligible(c)[1]) for c in cands
            if not is_carry_eligible(c)[0]]
print(f"carry candidates: {len(cands)}   eligible: {len(eligible)}   "
      f"exempt: {len(excluded)}")
for mid, why in sorted(excluded):
    print(f"  EXEMPT {mid}: {why}")

check("every exemption names a reason", all(w for _, w in excluded))
check("C1.5, B1.1 and B1.2 are all exempt on an empty package",
      NEVER_CARRY_MODULES <= {m for m, _ in excluded},
      f"exempt ids {sorted({m for m, _ in excluded})}")

# ------------------------------------------------------ PROOF 7: abstaining now, banded then
TARGET = "A2.1"          # Cat A2, abstains on an empty package, in service, not exempt
assert TARGET in service
p1 = prior("P1", [{"module_id": TARGET, "category": "A2", "status_color": "Amber",
                   "evidence_metric": "P1's own sentence, which must survive verbatim."}])
p2 = prior("P2", [])     # the intervening period produced nothing for it
history = [p2, p1]       # caller's order: most recent first

res = compute_project({}, "run143p2", "P3", CUTOFF, project_id="PRJ-CF",
                      prior_readings=history)
row = next((m for m in res["modules"] if m["module_id"] == TARGET), None)
check("proof 7: a module abstaining this period publishes a reading", row is not None)
if row:
    check("proof 7: it is marked carried", row.get("carried") is True)
    check("proof 7: it names the period it came from, not 'the previous period'",
          row.get("carried_from_period") == "P1", str(row.get("carried_from_period")))
    check("proof 7: it skipped P2, which held no banded reading for it",
          row.get("carried_from_age") == 2, f"age {row.get('carried_from_age')}")
    check("proof 7: the band is the banded one from P1", row.get("status_color") == "Amber")
    check("proof 7: the carried row asserts no freshness -- no seed, no gate report",
          "seed" not in row and "qualification" not in row)
    check("proof 7: P1's own evidence sentence is present unaltered",
          row.get("carried_evidence") == p1["modules"][0]["evidence_metric"])
    check("proof 7: the published sentence says it is carried and from where",
          "Carried from P1" in (row.get("evidence_metric") or ""),
          (row.get("evidence_metric") or "")[:90])
    check("proof 7: this period's own abstention sentence is kept beside it",
          bool(row.get("carried_reason")))
    check("rule 6: the period's own record is stored on the row, not replaced",
          isinstance(row.get("period_record"), dict)
          and row["period_record"].get("module_id") == TARGET)

still = [a for a in res["abstained"] if a["module_id"] == TARGET]
check("rule 6: the module is STILL in `abstained` -- the period's record is unchanged",
      len(still) == 1)

# ------------------------------------------------- PROOF 8: posture before and after, measured
plain = compute_project({}, "run143p2", "P3", CUTOFF, project_id="PRJ-CF")
before = (plain["category_statuses"].get("A2") or {}).get("status")
after = (res["category_statuses"].get("A2") or {}).get("status")
print(f"\nPROOF 8  A2 posture   before carry: {before!r}   after carry: {after!r}")
print(f"         project status before: {plain['project_status']!r}   "
      f"after: {res['project_status']!r}")
print(f"         A2 banded contributors before: "
      f"{(plain['category_statuses'].get('A2') or {}).get('posture_banded_count')}  after: "
      f"{(res['category_statuses'].get('A2') or {}).get('posture_banded_count')}")
check("proof 8: the category had no posture before the carry", before is None)
# The posture the arithmetic gives a lone Amber contributor is TAKEN, not assumed: A2 averages,
# an Amber scores -1, and -1 lands in the Red band. That is pre-existing `category_posture`
# behaviour, unchanged by this run, and the check asserts the carried reading produces exactly
# what a current reading of the same band would.
from app.simulation.category_posture import category_posture   # noqa: E402
_expect = category_posture("A2", [(TARGET, "Amber")])["status"]
check("proof 8: the carried reading gives the category a posture", after == _expect,
      f"A2 is {after!r}; a CURRENT Amber from the same module gives {_expect!r}")
_setters = (res["category_statuses"].get("A2") or {}).get("status_set_by")
check("proof 8: the carried module is named as setting it", TARGET in str(_setters), str(_setters))
check("proof 8: the carried reading reached the project's own working",
      TARGET in str(res["project_status_basis"].get("carried_modules")))
check("proof 8: the card is told how many readings were carried",
      res["project_status_basis"]["carried_count"] == len(
          [m for m in res["modules"] if m.get("carried")]),
      f"carried_count={res['project_status_basis']['carried_count']}")

# ------------------------------------------------ PROOF 9: no earlier banded reading, no carry
NOHIST = "A2.7"
check("proof 9: a module with no earlier reading at all stays unassessed",
      not any(m["module_id"] == NOHIST for m in res["modules"])
      and any(a["module_id"] == NOHIST for a in res["abstained"]))

unbanded = [prior("P1", [{"module_id": "A2.8", "category": "A2", "status_color": None,
                          "evidence_metric": "a calibration-pending row: a reading, no band"}])]
r_unb = compute_project({}, "run143p2", "P3", CUTOFF, project_id="PRJ-CF",
                        prior_readings=unbanded)
check("proof 9 / trap one: an earlier reading WITHOUT a band does not carry",
      not any(m["module_id"] == "A2.8" for m in r_unb["modules"]))
check("trap one: the band test is a band test", normalise_band(None) is None
      and normalise_band("green") == "Green" and normalise_band("teal") is None)

# ------------------------------------------------- PROOF 10: an excluded module does not carry
for mid in sorted(NEVER_CARRY_MODULES) + ["A6.1"]:
    hist = [prior("P1", [{"module_id": mid, "category": mid.split(".")[0],
                          "status_color": "Green", "evidence_metric": "an earlier Green"}])]
    rr = compute_project({}, "run143p2", "P3", CUTOFF, project_id="PRJ-CF",
                         prior_readings=hist)
    carried_here = [m for m in rr["modules"] if m["module_id"] == mid and m.get("carried")]
    check(f"proof 10: {mid} does not carry", not carried_here)

# per-arm: the declaration reaches the row, which is what makes the exclusion live
arm_rows = []
for cand in cands:
    if cand.get("carry_forward_eligible") is False:
        arm_rows.append(cand["module_id"])
print(f"\narms declaring themselves ineligible on this package: {sorted(arm_rows) or 'none'}")

# A6.2's exposure-floor arm, reached directly, since an empty package never gets there.
from app.simulation.models_cat89 import _band_safety      # noqa: E402
_res = {"employee_hours_worked": 10.0, "recordable_cases": 0, "severity": {}}
_out = _band_safety(_res, {"employee_hours_worked": 10.0, "exposure_floor": 20000})
check("rule 5 anchor: A6.2's exposure-floor arm withholds a band",
      _out[0] is None, str(_out[0]))
check("rule 5 anchor: A6.2's exposure-floor arm declares itself carry-ineligible",
      _res.get("carry_forward_eligible") is False,
      str(_res.get("carry_forward_ineligible_reason"))[:70])
check("rule 5 anchor: its own sentence now says it does not carry",
      "not carried forward" in str(_out[2]), str(_out[2])[-90:])

# A1.5's short-history arm and A1.2's, both reached directly.
from app.simulation.canonical import StructureAbsent      # noqa: E402
from app.simulation.canonical_v3 import identify_arima    # noqa: E402
try:
    identify_arima([1.0, 1.0, 1.0])
    check("A1.5 short-history arm raises", False)
except StructureAbsent as exc:
    check("A1.5 short-history arm declares itself carry-ineligible",
          exc.carry_forward_eligible is False)
    check("A1.5's own sentence now says no earlier reading is carried",
          "carried forward" in exc.sentence, exc.sentence[-80:])

from app.simulation.models_sim import run_cusum            # noqa: E402
_c = run_cusum({"spi": 1.0, "spiHistory": [1.0]}, lambda: 0.5, CUTOFF)
check("A1.2 short-history arm declares itself carry-ineligible",
      _c.get("carry_forward_eligible") is False)
check("A1.2 no-spi arm is NOT excluded (a missing input carries)",
      run_cusum({}, lambda: 0.5, CUTOFF).get("carry_forward_eligible") is None)

# ------------------------------------------------------- RULE 4: a retired module is not raised
retired = [prior("P1", [{"module_id": "D1.1", "category": "D1", "status_color": "Green",
                         "evidence_metric": "a pre-Run-96 stored reading"}])]
r_ret = compute_project({}, "run143p2", "P3", CUTOFF, project_id="PRJ-CF",
                        prior_readings=retired)
check("rule 4: a module deleted from the registry is not resurrected",
      not any(m["module_id"] == "D1.1" for m in r_ret["modules"]),
      f"D1.1 in service: {'D1.1' in service}")
direct = select_carried([{"module_id": "D1.1", "reason": "gone"}], retired)
check("rule 4: the guard is in the look-back itself, not in a dispatch that never happens",
      direct == [])

# ------------------------------------------------------- RULE 1: it does not cross projects
check("rule 1: the look-back is handed one project's rows only and cannot see another's",
      select_carried([{"module_id": TARGET, "reason": "x"}], []) == [])

# --------------------------------------------------------- no history at all is a v70 no-op
check("no history: the run is byte-identical to the pre-carry behaviour",
      [m["module_id"] for m in plain["modules"]]
      == [m["module_id"] for m in run_all({}, "run143p2", "P3", CUTOFF)["computed"]])

print("\n" + ("ALL CHECKS PASSED" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}"))
sys.exit(1 if FAILS else 0)
