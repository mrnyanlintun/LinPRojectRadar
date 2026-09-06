"""
RUN 145 -- the carry-forward leak on `evidence_not_qualified_for_use` is closed, and the fourth
reason code is ruled on.

Every figure this file prints was TAKEN by this file; nothing is transcribed. Run from `server/`:

    PYTHONPATH=. python tools/test_run145_carry_leak.py

THE FOUR REASON CODES AND WHAT EACH MEANS, which is the whole of the ruling:

  1 CATEGORY9_ASSESSMENT_MISSING   `_refuse_missing`, `ev is None`. No assessment exists at all.
                                   Nothing was weighed -> MISSING INPUT -> IT CARRIES (ruling 1).
  2 evidence_not_qualified_for_use `_refuse`, `not ev.eligible_for(use)`. Evidence exists and the
                                   gate judged it unfit -> JUDGMENT -> IT MUST NOT CARRY. That is
                                   this run's ruling, and its own sentence already said so.
  3 module_execution_failed        the module raised. Never substituted for. Unchanged.
  4 QUALIFICATION_CONTRACT_MISSING `_refuse_missing`, the route has no governed requirement
                                   declaration. Ruled separately, in
                                   `tools/test_run145_contract_code.py`.
"""
from __future__ import annotations

import datetime
import sys

from app.simulation import carry_forward as CF
from app.simulation.carry_forward import (NEVER_CARRY_MODULES, NEVER_CARRY_REASON_CODES,
                                          is_carry_eligible)
from app.simulation.compute import compute_project
from app.simulation.models import SIMULATION_VERSION, SIMULATION_VERSION_HISTORY
from app.simulation.qualification_boundary import ABSTAIN_UNQUALIFIED
from app.simulation.qualification_contract import ASSESSMENT_MISSING
from app.simulation.registry import MODULE_FAILED_CODE, run_all, service_index

CUTOFF = datetime.date(2026, 6, 30)
FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


# THE REPRODUCTION CASE. ONE material conflict between TWO equal-precedence documents. The
# package DECLARES a Category-9 assessment, so code 1 cannot fire: the gate sees evidence, and
# judges it. That is the whole point -- this is code 2's path, not code 1's.
CONFLICT = {"evidenceQualification": {"declared": True, "material_conflicts": [
    {"topic": "contract value", "documents": ["DOC-A", "DOC-B"], "precedence": "equal",
     "material": True,
     "description": "two equal-precedence documents state different contract values"}]}}
CLEAN = {"evidenceQualification": {"declared": True, "material_conflicts": []}}
# NO `evidenceQualification` AT ALL -- `ev is None`, which is code 1's path.
UNGOVERNED: dict = {}

# One banded reading per required category, one period back, including all four A6 arms.
PRIOR = [
    {"module_id": "A1.6", "category": "A1", "status_color": "Green", "evidence_metric": "P1 A1.6."},
    {"module_id": "A2.1", "category": "A2", "status_color": "Amber", "evidence_metric": "P1 A2.1."},
    {"module_id": "A3.3", "category": "A3", "status_color": "Green", "evidence_metric": "P1 A3.3."},
    {"module_id": "A4.4", "category": "A4", "status_color": "Green", "evidence_metric": "P1 A4.4."},
    {"module_id": "A6.1", "category": "A6", "status_color": "Green", "evidence_metric": "P1 A6.1."},
    {"module_id": "A6.2", "category": "A6", "status_color": "Green", "evidence_metric": "P1 A6.2."},
    {"module_id": "A6.3", "category": "A6", "status_color": "Green", "evidence_metric": "P1 A6.3."},
    {"module_id": "A6.4", "category": "A6", "status_color": "Green", "evidence_metric": "P1 A6.4."},
]
HISTORY = [{"period": "P1", "modules": PRIOR}]
SERVICE = set(service_index())


def drive(si: dict, pid: str) -> dict:
    res = compute_project(dict(si), "run145", "P2", CUTOFF, project_id=pid,
                          prior_readings=HISTORY)
    basis = res["project_status_basis"]
    return {
        "status": res["project_status"],
        "voting": res["categories_voting"],
        "assessed": list(basis.get("required_assessed") or []),
        "missing": list(basis.get("required_missing") or []),
        "carried": sorted(m["module_id"] for m in res["modules"] if m.get("carried")),
    }


def codes(si: dict, code: str) -> list[str]:
    r = run_all(dict(si), "run145", "P2", CUTOFF)
    return sorted(x["module_id"] for x in r["abstained"]
                  if x.get("abstention_reason_code") == code and x["module_id"] in SERVICE)


# ------------------------------------------------------------------- the stamp moved, and why
check("the stamp moved to sim-2026.09-v73 -- which readings carry, and therefore which vote, "
      "changed on this run", SIMULATION_VERSION == "sim-2026.09-v73", SIMULATION_VERSION)
check("the history APPENDS and never edits: v72 is still the second-to-last row",
      SIMULATION_VERSION_HISTORY[-1] == "sim-2026.09-v73"
      and SIMULATION_VERSION_HISTORY[-2] == "sim-2026.09-v72",
      str(SIMULATION_VERSION_HISTORY[-2:]))

# --------------------------------------------------------------- the four codes, distinguished
check("the three codes this file rules on are three distinct literals",
      len({ASSESSMENT_MISSING, ABSTAIN_UNQUALIFIED, MODULE_FAILED_CODE}) == 3,
      f"{ASSESSMENT_MISSING!r} {ABSTAIN_UNQUALIFIED!r} {MODULE_FAILED_CODE!r}")
check("the exclusion list holds exactly the failure code and the not-qualified code",
      set(NEVER_CARRY_REASON_CODES) == {MODULE_FAILED_CODE, ABSTAIN_UNQUALIFIED},
      str(sorted(NEVER_CARRY_REASON_CODES)))
check("the three module-id exemptions are untouched by this run",
      set(NEVER_CARRY_MODULES) == {"C1.5", "B1.1", "B1.2"}, str(sorted(NEVER_CARRY_MODULES)))

# -------------------------------------------- PROOF 1 / 2: the reproduction, and the two codes
pop_clean = codes(CLEAN, ABSTAIN_UNQUALIFIED)
pop_conf = codes(CONFLICT, ABSTAIN_UNQUALIFIED)
print(f"\nclean declaration     -> {pop_clean}")
print(f"one material conflict -> {pop_conf}")
check("proof 1: one material conflict flips exactly six modules onto the not-qualified code",
      pop_clean == [] and pop_conf == ["A6.1", "A6.2", "A6.3", "A6.4", "B1.1", "B1.2"],
      str(pop_conf))
check("proof 1: two of the six are exempt by id anyway, so the exposure is the four A6 arms",
      {m for m in pop_conf} - NEVER_CARRY_MODULES == {"A6.1", "A6.2", "A6.3", "A6.4"})

# ------------------------------------------ PROOF 3: THE TWO CODES SIDE BY SIDE, AFTER THE FIX
c1 = is_carry_eligible({"module_id": "A6.1", "abstention_reason_code": ASSESSMENT_MISSING})
c2 = is_carry_eligible({"module_id": "A6.1", "abstention_reason_code": ABSTAIN_UNQUALIFIED})
print(f"\ncode 1 {ASSESSMENT_MISSING:32s} carries={c1[0]}")
print(f"code 2 {ABSTAIN_UNQUALIFIED:32s} carries={c2[0]}  {c2[1]}")
print(f"code 3 {MODULE_FAILED_CODE:32s} "
      f"carries={is_carry_eligible({'module_id': 'A1.1', 'abstention_reason_code': MODULE_FAILED_CODE})[0]}")
check("proof 3: code 1 still carries -- ruling 1 is unaffected", c1 == (True, None))
check("proof 3: code 2 does not carry, and brings its OWN words rather than the failure's",
      c2[0] is False and "not qualified for this use" in (c2[1] or "")
      and "failed while computing" not in (c2[1] or ""), str(c2[1]))
check("proof 3: code 3 still does not carry, with the failure's own words",
      is_carry_eligible({"module_id": "A1.1", "abstention_reason_code": MODULE_FAILED_CODE})
      == (False, "the module failed while computing; a failure is never substituted for"))

# -------------------------------- PROOF 2 and 4, DRIVEN END TO END: the published status moves
after = drive(CONFLICT, "PRJ-R145-CONF")
ungov = drive(UNGOVERNED, "PRJ-R145-UNGOV")
print(f"\nCONFLICT   status={after['status']!r} voting={after['voting']} "
      f"assessed={after['assessed']} missing={after['missing']} carried={after['carried']}")
print(f"UNGOVERNED status={ungov['status']!r} voting={ungov['voting']} "
      f"assessed={ungov['assessed']} carried={ungov['carried']}")
check("proof 2: on the reproduction case no A6 arm carries -- the sentence and the behaviour "
      "now agree", [m for m in after["carried"] if m.startswith("A6.")] == [],
      str(after["carried"]))
check("proof 2: the category posture reflects the absence -- A6 is unassessed",
      "A6" not in after["assessed"] and after["missing"] == ["A6"], str(after["missing"]))
check("proof 4: the published status changes with it -- four of five categories vote and no "
      "governed band is published", after["voting"] == 4
      and after["status"] in (None, "", "Awaiting analysis"), f"status {after['status']!r}")
check("proof 3 driven: on a package with NO Category-9 assessment, A6 still carries and still "
      "votes -- ruling 1's behaviour is intact",
      "A6" in ungov["assessed"] and any(m.startswith("A6.") for m in ungov["carried"])
      and ungov["voting"] == 5,
      f"voting {ungov['voting']} carried {ungov['carried']}")

# ------------------------------------------------- PROOF 5, FAULT INJECTION: remove the entry
_real = CF.NEVER_CARRY_REASON_CODES
try:
    CF.NEVER_CARRY_REASON_CODES = frozenset({MODULE_FAILED_CODE})
    leaked = drive(CONFLICT, "PRJ-R145-LEAK")
    print(f"\nWITH THE ENTRY REMOVED: status={leaked['status']!r} voting={leaked['voting']} "
          f"carried={leaked['carried']}")
    check("proof 5: removing the entry brings the leak back -- the four A6 arms carry Greens "
          "again and a band is published",
          [m for m in leaked["carried"] if m.startswith("A6.")]
          == ["A6.1", "A6.2", "A6.3", "A6.4"] and leaked["voting"] == 5
          and leaked["status"] not in (None, "", "Awaiting analysis"),
          f"status {leaked['status']!r} carried {leaked['carried']}")
finally:
    CF.NEVER_CARRY_REASON_CODES = _real
check("proof 5: the entry is restored after the injection",
      set(CF.NEVER_CARRY_REASON_CODES) == {MODULE_FAILED_CODE, ABSTAIN_UNQUALIFIED})

print()
if FAILS:
    print(f"{len(FAILS)} CHECK(S) FAILED: {FAILS}")
    sys.exit(1)
print("ALL CHECKS PASSED")
