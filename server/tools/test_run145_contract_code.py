"""
RUN 145 -- THE FOURTH REASON CODE, `QUALIFICATION_CONTRACT_MISSING`, RULED.

Every figure this file prints was TAKEN by this file; nothing is transcribed. Run from `server/`:

    PYTHONPATH=. python tools/test_run145_contract_code.py

WHAT IT IS. `qualification_boundary.py:288` -- the FIRST test in every gated runner. When
`requirement_for(mid)` returns `CONFIGURATION_MISSING`, the route has no governed
qualification-requirement declaration at all, and `_refuse_missing` is called with the reason
code `CONTRACT_MISSING`.

HOW IT IS RULED, by the owner's own test: does the code mean NO ASSESSMENT HAPPENED, or does it
mean EVIDENCE WAS WEIGHED AND FOUND UNFIT? It means the first, and the codebase says so itself:

  * it goes through `_refuse_missing`, whose docstring is "The governed abstention for a route
    blocked BEFORE ANY EVIDENCE COULD BE ASSESSED";
  * it fires BEFORE `declared_evidence(...)` is ever called, so no evidence object exists;
  * it sets `qualification_state = UNASSESSED` and `consumer_executed = False`;
  * `_refuse`, the code-2 path, by contrast TAKES the evidence object and republishes its
    qualification reasons.

The codebase groups codes 1 and 4 on one primitive and separates code 2 onto another. So code 4
is a missing input and IT CARRIES, exactly like code 1. It is deliberately NOT on
`NEVER_CARRY_REASON_CODES`.

THE COUNTER-ARGUMENT, weighed rather than ignored. The call site says "An undeclared route is a
configuration failure and is blocked rather than allowed through. The default branch is deny."
One could read a deny-by-default as something that should not carry either. It does not change
the answer: the deny governs whether the CONSUMER EXECUTES THIS PERIOD, not what an earlier
period lawfully established under a declared contract. And note what the shape of the state
implies -- a missing contract is a PLATFORM-CONFIGURATION fact, not a per-period evidence fact,
so it refuses every period alike. An earlier banded reading can therefore only exist if the
contract was DECLARED then and WITHDRAWN since, which is precisely the case where the earlier
reading was lawfully taken and there is nothing about this period's evidence to defeat it.

EXPOSURE: LATENT. This file counts the in-service routes with no declared contract. It then
withdraws one declaration in-process to exercise the path anyway, so the ruling is demonstrated
rather than asserted, and restores it.
"""
from __future__ import annotations

import datetime
import sys

from app.simulation import qualification_contract as QC
from app.simulation.carry_forward import NEVER_CARRY_REASON_CODES, is_carry_eligible
from app.simulation.compute import compute_project
from app.simulation.qualification_contract import (CONFIGURATION_MISSING, CONTRACT_MISSING,
                                                   requirement_for)
from app.simulation.registry import run_all, service_index

CUTOFF = datetime.date(2026, 6, 30)
FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


CLEAN = {"evidenceQualification": {"declared": True, "material_conflicts": []}}
PRIOR = [
    {"module_id": "A1.6", "category": "A1", "status_color": "Green", "evidence_metric": "P1 A1.6."},
    {"module_id": "A2.1", "category": "A2", "status_color": "Amber", "evidence_metric": "P1 A2.1."},
    {"module_id": "A3.3", "category": "A3", "status_color": "Green", "evidence_metric": "P1 A3.3."},
    {"module_id": "A4.4", "category": "A4", "status_color": "Green", "evidence_metric": "P1 A4.4."},
    {"module_id": "A6.1", "category": "A6", "status_color": "Green", "evidence_metric": "P1 A6.1."},
]
HISTORY = [{"period": "P1", "modules": PRIOR}]
SERVICE = set(service_index())


def drive(si: dict, pid: str) -> dict:
    res = compute_project(dict(si), "run145", "P2", CUTOFF, project_id=pid,
                          prior_readings=HISTORY)
    basis = res["project_status_basis"]
    return {"status": res["project_status"], "voting": res["categories_voting"],
            "assessed": list(basis.get("required_assessed") or []),
            "carried": sorted(m["module_id"] for m in res["modules"] if m.get("carried"))}


def codes(si: dict, code: str) -> list[str]:
    r = run_all(dict(si), "run145", "P2", CUTOFF)
    return sorted(x["module_id"] for x in r["abstained"]
                  if x.get("abstention_reason_code") == code and x["module_id"] in SERVICE)


# ------------------------------------------------------------------ the trap: two constants, one string
check("the two constants share one string and are NOT interchangeable in meaning: "
      "CONFIGURATION_MISSING is the requirement lookup's sentinel, CONTRACT_MISSING the reason code",
      CONTRACT_MISSING == CONFIGURATION_MISSING == "QUALIFICATION_CONTRACT_MISSING",
      f"{CONFIGURATION_MISSING!r} / {CONTRACT_MISSING!r}")

# ---------------------------------------------------------------------------- the ruling itself
check("RULED: the fourth code CARRIES -- it is not on the never-carry list",
      CONTRACT_MISSING not in NEVER_CARRY_REASON_CODES, str(sorted(NEVER_CARRY_REASON_CODES)))
check("and is_carry_eligible agrees, with no exemption reason",
      is_carry_eligible({"module_id": "A6.1",
                         "abstention_reason_code": CONTRACT_MISSING}) == (True, None))

# ---------------------------------------------- PROOF 6: the fourth code, ruled and exercised
undeclared = [m for m in sorted(SERVICE) if requirement_for(m) == CONFIGURATION_MISSING]
print(f"\nin-service routes: {len(SERVICE)}   with NO declared contract: {len(undeclared)} "
      f"{undeclared}")
check("proof 6: the fourth code's exposure is LATENT -- every in-service route has a declared "
      "contract, so nothing in service can reach it today",
      undeclared == [], str(undeclared))

# ...and it is exercised anyway, by withdrawing A6.1's declaration, so the ruling is
# demonstrated rather than asserted. The withdrawal is the ONLY way an earlier banded reading
# can coexist with this code: a missing contract refuses every period alike.
_real_contract = QC.qualification_contract
try:
    def _without_a61() -> dict[str, str]:
        c = dict(_real_contract())
        c.pop("A6.1", None)
        return c
    QC.qualification_contract = _without_a61
    check("proof 6: with A6.1's declaration withdrawn, requirement_for reports "
          "CONFIGURATION_MISSING", requirement_for("A6.1") == CONFIGURATION_MISSING)
    pop4 = codes(CLEAN, CONTRACT_MISSING)
    print(f"contract withdrawn for A6.1 -> {CONTRACT_MISSING} on {pop4}")
    check("proof 6: A6.1 is refused on the fourth code, on a package whose evidence is clean",
          pop4 == ["A6.1"], str(pop4))
    four = drive(CLEAN, "PRJ-R145-CONTRACT")
    print(f"fourth code driven: carried={four['carried']} voting={four['voting']} "
          f"status={four['status']!r}")
    check("proof 6: it CARRIES, as ruled -- nothing was weighed, so an earlier reading answers it",
          "A6.1" in four["carried"], str(four["carried"]))
finally:
    QC.qualification_contract = _real_contract
check("proof 6: the contract is restored after the injection",
      requirement_for("A6.1") != CONFIGURATION_MISSING)

print()
if FAILS:
    print(f"{len(FAILS)} CHECK(S) FAILED: {FAILS}")
    sys.exit(1)
print("ALL CHECKS PASSED")
