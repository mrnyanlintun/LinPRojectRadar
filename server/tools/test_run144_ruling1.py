"""
RUN 144 RULING 1 -- the Category-9 exclusion on carry-forward is lifted.

Every figure this file prints was TAKEN by this file; nothing is transcribed. Run from `server/`:

    PYTHONPATH=. python tools/test_run144_ruling1.py

WHAT IS BEING PROVED, AND WHY THIS SHAPE. Run 143 put `CATEGORY9_ASSESSMENT_MISSING` on
`NEVER_CARRY_REASON_CODES` and measured the cost: on a package carrying no Category-9
assessment, category A6 has no arm that is not refused by that code, so A6 could never be
assessed, only four of the five required categories ever voted, and no governed status was ever
published. The owner lifted the exclusion. This file proves the before, the after, and that the
before returns the moment the exclusion is put back -- so the check can fail, and is shown
failing, rather than merely passing today.

THE DISTINCTION THE RULING RESTS ON, asserted here so a later reader cannot lose it: there are
TWO Category-9 refusal paths in `qualification_boundary.py` with TWO reason codes.
  `CATEGORY9_ASSESSMENT_MISSING`      `ev is None` -- nothing was ever assessed. A missing input.
  `evidence_not_qualified_for_use`    evidence existed and the gate judged it not qualified.
Only the first was ever on the list, and only the first is lifted.
"""
from __future__ import annotations

import datetime
import sys

from app.simulation import carry_forward as CF
from app.simulation.carry_forward import (NEVER_CARRY_MODULES, NEVER_CARRY_REASON_CODES,
                                          carry_candidates, is_carry_eligible)
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


# THE HISTORY. One banded reading in each of the five REQUIRED categories, one period back.
# A6.1 is the load-bearing row: it is the only one of the five whose abstention this period is
# the Category-9 code, and A6 is the category with no other arm on an ungoverned package.
PRIOR = [
    {"module_id": "A1.6", "category": "A1", "status_color": "Green", "evidence_metric": "P1 A1.6."},
    {"module_id": "A2.1", "category": "A2", "status_color": "Amber", "evidence_metric": "P1 A2.1."},
    {"module_id": "A3.3", "category": "A3", "status_color": "Green", "evidence_metric": "P1 A3.3."},
    {"module_id": "A4.4", "category": "A4", "status_color": "Green", "evidence_metric": "P1 A4.4."},
    {"module_id": "A6.1", "category": "A6", "status_color": "Green", "evidence_metric": "P1 A6.1."},
]
HISTORY = [{"period": "P1", "modules": PRIOR}]


def run_once() -> dict:
    """One live compute of the same project against the same empty current package."""
    res = compute_project({}, "run144", "P2", CUTOFF, project_id="PRJ-R144",
                          prior_readings=HISTORY)
    basis = res["project_status_basis"]
    return {
        "status": res["project_status"],
        "voting": res["categories_voting"],
        "assessed": list(basis.get("required_assessed") or []),
        "missing": list(basis.get("required_missing") or []),
        "carried": sorted(m["module_id"] for m in res["modules"] if m.get("carried")),
    }


# ------------------------------------------------------------- the two codes are distinguished
check("the two Category-9 refusal paths carry different reason codes",
      ASSESSMENT_MISSING != ABSTAIN_UNQUALIFIED,
      f"{ASSESSMENT_MISSING!r} vs {ABSTAIN_UNQUALIFIED!r}")
check("the exclusion list now holds the failure code only",
      set(NEVER_CARRY_REASON_CODES) == {MODULE_FAILED_CODE},
      f"list = {sorted(NEVER_CARRY_REASON_CODES)}")
check("MODULE_FAILED_CODE stays excluded -- registry.py's promise is kept",
      is_carry_eligible({"module_id": "A1.1",
                         "abstention_reason_code": MODULE_FAILED_CODE}) == (
          False, "the module failed while computing; a failure is never substituted for"))
check("a crashed module stays excluded by the failure flag too, whatever its code",
      is_carry_eligible({"module_id": "A1.1", "module_failed": True})[0] is False)
check(f"{ASSESSMENT_MISSING} is now carry-eligible",
      is_carry_eligible({"module_id": "A6.1",
                         "abstention_reason_code": ASSESSMENT_MISSING}) == (True, None))
check("the three module-id exemptions are untouched by ruling 1",
      set(NEVER_CARRY_MODULES) == {"C1.5", "B1.1", "B1.2"},
      str(sorted(NEVER_CARRY_MODULES)))

# ---------------------------------------------------------------- the population on this package
base = run_all({}, "run144", "P2", CUTOFF)
service = set(service_index())
c9 = sorted(r["module_id"] for r in base["abstained"]
            if r.get("abstention_reason_code") == ASSESSMENT_MISSING
            and r.get("module_id") in service)
print(f"\nmodules refused by {ASSESSMENT_MISSING} on an ungoverned package: {c9}")
check("A6 has no arm on this package that is not refused by the Category-9 code -- "
      "which is why the exclusion withheld the status",
      {m for m in c9 if m.startswith("A6.")} ==
      {r["module_id"] for r in base["abstained"]
       if r.get("module_id", "").startswith("A6.") and r["module_id"] in service},
      f"A6 refused: {[m for m in c9 if m.startswith('A6.')]}")

# ------------------------------------------------------- PROOF 1: the after, on the live code
after = run_once()
print(f"\nAFTER  (exclusion lifted): status={after['status']!r}  "
      f"categories_voting={after['voting']}  assessed={after['assessed']}  "
      f"missing={after['missing']}")
check("proof 1: all five required categories are assessed",
      after["voting"] == 5 and after["missing"] == [],
      f"voting {after['voting']}, missing {after['missing']}")
check("proof 1: A6 is assessed, and it is assessed by a carried reading",
      "A6" in after["assessed"] and "A6.1" in after["carried"], str(after["carried"]))
check("proof 1: a governed band is published, not withheld",
      after["status"] not in (None, "", "Awaiting analysis"), f"status {after['status']!r}")

# ------------------- PROOF 2, THE FAULT INJECTION: put the exclusion back, the status is withheld
_saved = CF.NEVER_CARRY_REASON_CODES
CF.NEVER_CARRY_REASON_CODES = frozenset(set(_saved) | {ASSESSMENT_MISSING})
try:
    before = run_once()
finally:
    CF.NEVER_CARRY_REASON_CODES = _saved
print(f"\nBEFORE (exclusion restored): status={before['status']!r}  "
      f"categories_voting={before['voting']}  assessed={before['assessed']}  "
      f"missing={before['missing']}")
check("proof 2: with the exclusion restored only four categories vote",
      before["voting"] == 4 and before["missing"] == ["A6"],
      f"voting {before['voting']}, missing {before['missing']}")
check("proof 2: with the exclusion restored A6.1 does not carry",
      "A6.1" not in before["carried"], str(before["carried"]))
check("proof 2: with the exclusion restored no governed status is published",
      before["status"] == "Awaiting analysis", f"status {before['status']!r}")
check("proof 2: the injection was reverted -- the live list is the lifted one",
      set(CF.NEVER_CARRY_REASON_CODES) == {MODULE_FAILED_CODE})
check("proof 2: the two runs differ ONLY in the exclusion, and they differ",
      before != after)

# --------------------------------------------------------------------------------- the stamp
check("the stamp moved to sim-2026.09-v72", SIMULATION_VERSION == "sim-2026.09-v72",
      SIMULATION_VERSION)
check("the history tuple ends at the new stamp and v71 is still in it, unedited",
      SIMULATION_VERSION_HISTORY[-1] == "sim-2026.09-v72"
      and "sim-2026.09-v71" == SIMULATION_VERSION_HISTORY[-2],
      str(SIMULATION_VERSION_HISTORY[-2:]))

# ------------------------------------------------- the site's own sentence no longer contradicts
row = next(r for r in base["abstained"]
           if r.get("abstention_reason_code") == ASSESSMENT_MISSING)
sentence = row.get("reason") or ""
check("the Category-9 refusal sentence no longer promises that nothing is carried",
      "exceptions to carry-forward" not in sentence and "not shown here" not in sentence,
      sentence[:80])
check("it states the carrying behaviour instead", "carried" in sentence, sentence[-90:])

# ---------------------------- NOTHING ELSE MOVED: no history means no change of any kind at all
none_hist = compute_project({}, "run144", "P2", CUTOFF, project_id="PRJ-R144-NOHIST",
                            prior_readings=[])
check("a project with no history publishes no carried row and no status it did not have",
      not any(m.get("carried") for m in none_hist["modules"])
      and none_hist["project_status"] == "Awaiting analysis",
      none_hist["project_status"])

print()
if FAILS:
    print(f"{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("ALL CHECKS PASSED")
