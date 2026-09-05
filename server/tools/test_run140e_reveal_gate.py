#!/usr/bin/env python3
"""
RUN 140, AGENT E. THE REVEAL GATE ON THE MITIGATIONS, PROVED BOTH WAYS.

Run (from server/):

    DATABASE_URL=sqlite:///<throwaway>.db python tools/test_run140e_reveal_gate.py

WHY THIS GATE EXISTS AT ALL.

`documents.py` stated in terms that the decision brief is NOT reveal-gated, and the justification
given was sound while it was true: the card carried only the project's own computed readings,
which the project manager is already shown. THAT JUSTIFICATION STOPS BEING TRUE THE MOMENT THE
CARD CARRIES COMPOSED REMEDIES. A mitigation is a TREATMENT, in exactly the sense
`_redact_module_actions` and `_WITHHELD_NARRATIVE` exist to withhold -- and redaction cannot
catch it, because it strips keys from MODULE ROWS while the brief is composed AFTER redaction.

Serving it ungated would put a composed remedy in front of a participant BEFORE their preliminary
judgment is locked, which is the contamination the reveal gate was written to close and which
would compromise the controlled repeated-measures design.

SO: the finding and the question stay ungated and unchanged; the mitigations are gated on the
SAME predicate that already gates the recommendation package. A WITHHELD READ CARRIES NO
`mitigations` KEY AT ALL -- not an empty list, which would be the different and false statement
"mitigations were composed and none applied".
"""
from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timezone

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import app.main as main  # noqa: F401
from app import documents
from app.models import Project
from app.research_models import ComputedResult

Session = main.SessionFactory
results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))
    print(("PASS  " if ok else "FAIL  ") + label)


CALLS = {"n": 0}


def counting_caller(blocks, cfg, environ=None):
    """The fake transport, IN THE CHECK ONLY. Production passes no `caller` at all."""
    CALLS["n"] += 1
    return ("Re-baseline the contingency draws against the current exposure.\n"
            "Retire closed risks from the exposure model.")


ADVERSE_MODULE = {
    "module_id": "A3.3", "method_class": "Cost_Contingency_Adequacy", "status_color": "Amber",
    "band_asserted": True, "category": "A3",
    "evidence_metric": "Contingency covers 0.62 of the P80 exposure at this period.",
    "band_boundary": "Green at or above 0.90; Yellow at or above 0.75; Amber at or above 0.60; "
                     "Red below 0.60.",
    "band_basis": "the owner's configured contingency adequacy ladder",
    "threshold_source": "owner_default", "band_provenance_class": "owner_calibrated",
    "band_coverage_fraction": 0.62,
}

PROJECT_ID = uuid.uuid4()
session = Session()
try:
    session.add(Project(id=PROJECT_ID, legacy_id=f"R140G-{PROJECT_ID.hex[:8]}",
                        doc={"name": "Run 140 E gate fixture"}, record_version=1,
                        archived=False, is_training=False))
    row = ComputedResult(
        project_id=PROJECT_ID, period=2,
        signal_inputs={}, module_results=[ADVERSE_MODULE],
        category_statuses={"A3": {"status": "Amber", "status_set_by": ["A3.3"]}},
        project_status="Amber", simulation_version="fixture", seed="0",
        period_cutoff=date(2026, 1, 1), computed_at=datetime.now(timezone.utc))
    session.add(row)
    session.flush()

    # ---------------------------------------------------------------- the withheld read
    withheld = documents._result_view(
        row, include_recommendation=False, package=None,
        session=session, project_id=PROJECT_ID, mitigation_caller=counting_caller)
    brief_w = withheld["decision_brief"]
    check("mitigations" not in brief_w,
          "A WITHHELD READ CARRIES NO `mitigations` KEY -- absent, not empty")
    check("mitigations" not in (brief_w.get("order") or []),
          "the withheld card's render order does not name a mitigations block")
    check(CALLS["n"] == 0,
          f"A WITHHELD READ MAKES NO MODEL CALL AT ALL (counted: {CALLS['n']})")
    check(brief_w.get("finding") and brief_w.get("question"),
          "THE REST OF THE BRIEF IS UNCHANGED: the finding and the question are still served "
          "on a withheld read, exactly as before this run")
    check(withheld.get("recommendation") is None,
          "the recommendation package is withheld on the same read, as it always was")

    # ---------------------------------------------------------------- the visible read
    visible = documents._result_view(
        row, include_recommendation=True, package=None,
        session=session, project_id=PROJECT_ID, mitigation_caller=counting_caller)
    brief_v = visible["decision_brief"]
    check("mitigations" in brief_v, "A VISIBLE READ CARRIES THE `mitigations` KEY")
    check(CALLS["n"] == 1,
          f"the visible read composed exactly once (calls counted: {CALLS['n']})")
    check("mitigations" in (brief_v.get("order") or []),
          "the visible card's render order names the mitigations block, after adverse_readings")
    check((brief_v["order"].index("mitigations")
           == brief_v["order"].index("adverse_readings") + 1),
          "the mitigations block sits immediately after the adverse readings it answers")

    entry = brief_v["mitigations"][0]
    check(entry["module_id"] == "A3.3" and entry["band"] == "Amber"
          and entry["shape"] == "threshold",
          f"the served entry carries the contract's keys: {entry['module_id']} "
          f"{entry['band']} {entry['shape']}")
    check(set(entry) == {"module_id", "band", "shape", "reading", "next_band", "gap",
                         "candidates", "absent_reason", "composed_at", "model", "provider"},
          f"the served shape is exactly the fixed contract: {sorted(entry)}")
    # AGENT R'S EXPORTS COPY THESE THROUGH UNCHANGED, so the types are checked, not assumed.
    check(isinstance(entry["candidates"], list)
          and all(isinstance(c, str) for c in entry["candidates"]),
          "`candidates` is a list of strings on an accepted composition")
    check(entry["candidates"] and entry["absent_reason"] is None,
          "`absent_reason` is null whenever `candidates` is non-empty")
    check(isinstance(entry["next_band"], str) and isinstance(entry["gap"], str)
          and entry["next_band"] and entry["gap"],
          "`next_band` and `gap` are non-empty strings, rendered verbatim by the surface")

    # THE FIGURES ON THE CARD ARE COMPARED PROGRAMMATICALLY AGAINST THE MODULE'S OWN ROW.
    check(entry["reading"] == ADVERSE_MODULE["evidence_metric"],
          "the reading on the card IS the module's own evidence sentence, compared verbatim")
    check(ADVERSE_MODULE["band_boundary"] in entry["next_band"],
          "the boundary on the card IS the module's own stored boundary sentence")
    check("0.62" in entry["gap"] and "0.75" in entry["gap"]
          and repr(abs(0.62 - 0.75)) in entry["gap"],
          f"the gap on the card is the two stored figures and their difference: {entry['gap']}")
    check(entry["provider"] == "anthropic" and entry["model"] == "claude-opus-5",
          "the entry names the provider and model that composed it")

    # ---------------------------------------------------------------- replay through the view
    again = documents._result_view(
        row, include_recommendation=True, package=None,
        session=session, project_id=PROJECT_ID, mitigation_caller=counting_caller)
    check(CALLS["n"] == 1,
          f"A SECOND VISIBLE RENDER MADE NO SECOND CALL (calls still counted: {CALLS['n']})")
    check(again["decision_brief"]["mitigations"] == brief_v["mitigations"],
          "the second render's mitigations are byte-identical to the first")

    session.rollback()
finally:
    session.close()

passed = sum(1 for ok, _ in results if ok)
print()
print("NOTE: no ANTHROPIC_API_KEY exists in this environment. The gate, the composition path, "
      "the storage, the replay and the served shape all ran against the real code; the single "
      "live HTTPS request is the only thing not exercised, and it is not simulated.")
print(f"RESULT: {passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
