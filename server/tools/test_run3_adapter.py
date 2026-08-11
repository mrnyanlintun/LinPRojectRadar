#!/usr/bin/env python3
"""
The flat-to-nested adapter (remediation_programme.md "Run 3 -- the adapter";
remediation_decisions_answered.md 3.1 and 3.2). Audit P0 finding 1.

WHAT THIS SUITE HAS TO PROVE, and why each part is built the way it is:

1. REACHABILITY ON THE REAL PATH, NOT A HARNESS. Every check below drives a project through
   `/exec` -- upload documents, state periods, compute -- which is `documents._compute_and_store`
   into `documents.run_and_store` into `compute_project`. A test that assembled a nested package
   itself and handed it to a module would prove the module can add up, which was never in doubt;
   what was in doubt is whether the application's own path ever constructs one. That is failure
   mode 3 in the project's standing test discipline (a fixture that builds state by a route the
   application does not take), and it is the specific mistake this suite exists to avoid.

2. A MODULE THAT STILL ABSTAINS SAYS WHY. Not "insufficient data" alone: the stored abstention
   reason must name which assembled signals it was given and which it was not, so a reader can
   tell a data gap from a wiring gap. That distinction is exactly what hid this defect.

3. NONE OF THE FOURTEEN VOTES, AND PROJECT STATUS IS UNCHANGED BY THE RUN. This is the check
   that matters most and it is proved able to fail first: fourteen modules going from silent to
   producing a status is precisely the change that could move a project's status by accident.
   The "before" is not a remembered number and not a stashed checkout: it is the same
   `compute_project` run with `NESTED_INPUT_MODULES` emptied, which puts the fourteen back on
   pass 1 with the flat dictionary -- byte for byte the pre-adapter behaviour, because that is
   what the pre-adapter code did.

4. THE ADAPTER CHANGED NOTHING ELSE. Every other module's result is compared byte for byte
   between the adapter-on and adapter-off runs, including the stochastic ones, which is what
   proves the deferred passes did not move any other module's position in the shared random
   stream.

Run:
    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_run3_adapter.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
import app.simulation.registry as registry  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import ComputedResult, Participant  # noqa: E402
from app.simulation import compute_project  # noqa: E402
from app.simulation.registry import CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY  # noqa: E402
from app.simulation.signal_package import (  # noqa: E402
    ADAPTER_TIERS, NESTED_INPUT_MODULES, SIGNAL_KEYS, build_signals, doc_status, evm_status,
)

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0
ROOT = pathlib.Path(__file__).resolve().parents[2]


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


# The fourteen, by canonical name, so the per-module report reads as something other than ids.
FOURTEEN = {
    "B1.1": "Conservative Dominance", "B1.2": "Weighted Voting", "B1.3": "Majority Rules",
    "B1.4": "Worst N of M", "B2.1": "Dempster-Shafer evidence combination",
    "B2.2": "Rough Sets", "B2.3": "Neutrosophic Logic", "B2.4": "Interval Fuzzy Sets",
    "B2.5": "Z Numbers", "B2.6": "PLTS", "B2.7": "Plithogenic Sets",
    "B2.8": "Belief Rule Base", "B2.9": "Quantum Probability", "B3.1": "ABM Governance",
}

ADMIN = "r3-admin"
PRJ = "PRJ-R3-ADAPTER"

# Four monthly reports, one per period, with cost performance deteriorating so the schedule and
# cost indices, their histories, and therefore the forecast and the trend signals are all real.
MONTHS = {
    1: ("2026-03-15", "2026-03-31", 3_000_000, 3_050_000, 3_050_000, 25.0, 25.0),
    2: ("2026-04-15", "2026-04-30", 4_000_000, 4_250_000, 4_150_000, 33.0, 34.0),
    3: ("2026-05-15", "2026-05-31", 5_000_000, 5_500_000, 5_300_000, 42.0, 44.0),
    4: ("2026-06-15", "2026-06-30", 6_000_000, 6_900_000, 6_500_000, 50.0, 54.0),
}


def fields(d, ev, ac, pv, apc, ppc):
    return {"earned_value": ev, "actual_cost": ac, "planned_value": pv,
            "budget_at_completion": 12_000_000, "actual_percent_complete": apc,
            "planned_percent_complete": ppc, "report_date": d, "document_date": d,
            "document_risk_score": 0.45}


def doc(tag: str) -> bytes:
    return f"%PDF-1.4 RUN3 ADAPTER {tag}\n".encode()


REC = {hashlib.sha256(doc(f"M{p}")).hexdigest(): ("monthly_report", fields(m[0], *m[2:]))
       for p, m in MONTHS.items()}
set_extractor_override(StubExtractor(REC))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R3-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
        s.add(Project(legacy_id=PRJ, doc={"id": PRJ, "name": PRJ, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R3-PM", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PRJ,
      "participant_id": created["participant_id"], "project_role": "PM"})


def stored(period: int) -> dict:
    """The stored row, read back the way the API serves it. Never a computation done here."""
    return post({"action": "projectresults", "session_token": pm, "id": PRJ,
                 "period": period})["result"]


def by_id(result: dict) -> tuple[dict, dict]:
    comp = {m.get("module_id"): m for m in (result.get("module_results") or [])}
    abst = {a.get("module_id"): a for a in (result.get("abstained") or [])}
    return comp, abst


try:
    print("=" * 78)
    print("1. The real path: four periods uploaded and computed through /exec")
    print("=" * 78)

    for p in (1, 2, 3, 4):
        post({"action": "projectupload", "session_token": pm, "id": PRJ,
              "period": p, "period_end": MONTHS[p][1],
              "documents": [{"filename": f"M{p}.pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(doc(f"M{p}"))}]})
    allr = post({"action": "projectcomputeall", "session_token": pm, "id": PRJ})
    check(allr.get("periods") == [1, 2, 3, 4] and allr.get("computed") == 4,
          "four stated periods compute as four results on the document path", str(allr)[:160])

    r4 = stored(4)
    comp4, abst4 = by_id(r4)
    check(bool(comp4), "the stored row carries module results", str(len(comp4)))
    # THE DEFECT ITSELF: before the adapter, all fourteen were in `abstained` on every real run.
    reached = [m for m in FOURTEEN if m in comp4]
    check(len(reached) == 12,
          "twelve of the fourteen nested-input computations now produce a finding at period four",
          f"reached={sorted(reached)}")
    check(all(m in comp4 or m in abst4 for m in FOURTEEN),
          "and every one of the fourteen is accounted for, computed or abstained")

    print()
    print("  per module, at period four:")
    for mid, name in sorted(FOURTEEN.items()):
        if mid in comp4:
            print(f"    computes   {name}: {comp4[mid].get('status_color')} -- "
                  f"{str(comp4[mid].get('evidence_metric'))[:70]}")
        else:
            print(f"    abstains   {name}: {str(abst4[mid].get('reason'))[:110]}")

    print()
    print("=" * 78)
    print("2. The two disabled concept-only computations stay refused, adapter or not")
    print("=" * 78)

    for mid in ("B2.7", "B2.9"):
        check(mid not in comp4 and "disabled" in str(abst4[mid].get("reason", "")),
              f"{FOURTEEN[mid]} is refused before any adapter input is consulted",
              str(abst4.get(mid)))
        check("assembled signal package" not in str(abst4[mid].get("reason", "")),
              f"and its reason is the disabled one, not an assembly note ({FOURTEEN[mid]})")

    print()
    print("=" * 78)
    print("3. A module that still abstains states why, in words, on the stored row")
    print("=" * 78)

    r1 = stored(1)
    comp1, abst1 = by_id(r1)
    # Period one has no earlier period, so there is no index history: the trend computation
    # abstains, and the two governance projections that require a trend signal abstain with it.
    for mid in ("B1.1", "B3.1"):
        reason = str(abst1.get(mid, {}).get("reason") or "")
        check(mid in abst1 and "assembled signal package" in reason,
              f"{FOURTEEN[mid]} abstains at period one naming the package it was given", reason[:120])
        check("performance trend" in reason,
              f"and names the signal that was missing ({FOURTEEN[mid]})", reason[:160])
        check("B1." not in reason and "B3." not in reason and "--" not in reason,
              f"and the reason carries no module id and no em dash ({FOURTEEN[mid]})", reason[:160])

    print()
    print("=" * 78)
    print("4. The adapter did not change what is stored as this period's inputs")
    print("=" * 78)

    si4 = r4.get("signal_inputs") or {}
    check(all(k not in si4 for k in ("signals", "simulationSignals", "decision")),
          "the stored signal inputs carry no assembled objects: the adapter copies, never mutates",
          str([k for k in ("signals", "simulationSignals", "decision") if k in si4]))
    check(all(k not in si4 for k in SIGNAL_KEYS),
          "and none of the four assembled signal keys leaked into the stored inputs")

    print()
    print("=" * 78)
    print("5. None of the fourteen votes: rollup, recommendation text, decision card")
    print("=" * 78)

    check(all(comp4[m].get("votes") is False for m in reached),
          "every one of the fourteen that computed carries votes:false")
    cats = r4.get("category_statuses") or {}
    voting_cats = {registry.registry_index()[m]["category"] for m in CORE_VOTING_MODULES}
    check(set(cats.keys()) <= voting_cats,
          "no category rollup exists for a category carried only by the fourteen",
          f"{sorted(set(cats.keys()) - voting_cats)}")
    fourteen_cats = {registry.registry_index()[m]["category"] for m in FOURTEEN}
    check(not (set(cats.keys()) & (fourteen_cats - voting_cats)),
          "and none of their categories reaches project status fusion")
    # Layer (b) and (c): the courses of action and the decision card read the `votes` field and
    # the fused status respectively, both covered by the two checks above plus this one.
    check(all(m not in CORE_VOTING_MODULES for m in FOURTEEN),
          "none of the fourteen is in the interim voting set")

    print()
    print("=" * 78)
    print("6. Newly wired and unvalidated is marked in the API row, not on the ledger")
    print("=" * 78)

    check(all(comp4[m].get("newly_wired_unvalidated") is True for m in reached),
          "every computed one of the fourteen is marked newly wired and unvalidated in the row")
    check(all(comp4[m].get("signal_qualification") == "unqualified" for m in reached),
          "and records that it consumed unqualified signals (the Category 9 deviation)")
    other = next(m for m in comp4 if m not in FOURTEEN)
    check(comp4[other].get("newly_wired_unvalidated") is None,
          "and no other computation carries the marking", other)

    PARTICIPANT_JS = ("assets/js/taxonomy.js", "assets/js/app.js", "assets/js/detail.js",
                      "assets/js/module_charts.js", "assets/js/export.js")
    for rel in PARTICIPANT_JS:
        text = (ROOT / rel).read_text(encoding="utf-8")
        check("newly_wired_unvalidated" not in text and "wiring_note" not in text,
              f"the participant surface never reads the marking ({rel})")
    knowledge = (ROOT / "assets/js/knowledge.js").read_text(encoding="utf-8")
    check("RUN3_NEWLY_WIRED" in knowledge and "Newly wired and unvalidated" in knowledge,
          "the methods documentation does carry it")
    check(len([1 for line in knowledge.splitlines() if "RUN3_NEWLY_WIRED[" in line]) >= 1,
          "and reads it when rendering a module's entry")
    export_py = (ROOT / "server/app/research_export.py").read_text(encoding="utf-8")
    check("_RUN3_NEWLY_WIRED" in export_py and "signal_qualification" in export_py,
          "and so does the committee-facing export")

    print()
    print("=" * 78)
    print("7. THE CHECK THAT MATTERS MOST: project status is unchanged by this run")
    print("=" * 78)
    print("   'Before' is the same compute_project with the adapter's module set emptied, which")
    print("   returns the fourteen to pass one on the flat dictionary: the pre-adapter path.")

    def run_without_adapter(si: dict, cutoff: str) -> dict:
        saved = registry.NESTED_INPUT_MODULES
        registry.NESTED_INPUT_MODULES = frozenset()
        try:
            return compute_project(dict(si), PRJ, "P4", cutoff)
        finally:
            registry.NESTED_INPUT_MODULES = saved

    def run_with_adapter(si: dict, cutoff: str) -> dict:
        return compute_project(dict(si), PRJ, "P4", cutoff)

    CUTOFF = str(r4.get("period_cutoff"))[:10]
    before = run_without_adapter(si4, CUTOFF)
    after = run_with_adapter(si4, CUTOFF)

    check(before["project_status"] == after["project_status"],
          "project status is identical with the adapter and without it",
          f"{before['project_status']} vs {after['project_status']}")
    check(before["project_conflict"] == after["project_conflict"],
          "and so is the conflict mass the status was fused with")
    check(json.dumps(before["category_statuses"], sort_keys=True)
          == json.dumps(after["category_statuses"], sort_keys=True),
          "and so is every category rollup")
    check(after["project_status"] == r4.get("project_status"),
          "and the stored row on the real path agrees with both",
          f"{after['project_status']} vs {r4.get('project_status')}")

    # It can fail. Let one of the fourteen vote and the status moves -- shown, not asserted from
    # reasoning -- then put it back and confirm the baseline is identical again.
    def status_if_voting(module_id: str) -> str | None:
        saved = registry.CORE_VOTING_MODULES
        import app.simulation.compute as compute_mod
        saved_c = compute_mod.CORE_VOTING_MODULES
        registry.CORE_VOTING_MODULES = frozenset(saved | {module_id})
        compute_mod.CORE_VOTING_MODULES = registry.CORE_VOTING_MODULES
        try:
            return compute_project(dict(si4), PRJ, "P4", CUTOFF)["project_status"]
        finally:
            registry.CORE_VOTING_MODULES = saved
            compute_mod.CORE_VOTING_MODULES = saved_c

    moved = {m: status_if_voting(m) for m in ("B2.2", "B1.4", "B2.1")}
    check(any(v != after["project_status"] for v in moved.values()),
          "FAULT: letting one of the fourteen vote DOES move project status, so the check above "
          "is not vacuous", str(moved))
    restored = run_with_adapter(si4, CUTOFF)
    check(restored["project_status"] == after["project_status"]
          and json.dumps(restored["category_statuses"], sort_keys=True)
          == json.dumps(after["category_statuses"], sort_keys=True),
          "and the baseline is byte-identical again once the fault is removed")

    print()
    print("=" * 78)
    print("8. Nothing else moved: every other module's result, byte for byte")
    print("=" * 78)

    def others(run: dict) -> str:
        return json.dumps([m for m in run["modules"] if m["module_id"] not in NESTED_INPUT_MODULES],
                          sort_keys=True, default=str)

    check(others(before) == others(after),
          "every module outside the fourteen produces an identical result with the adapter, "
          "including the stochastic ones (so the shared generator was not disturbed)")
    ab_before = {a["module_id"] for a in before["abstained"]} - NESTED_INPUT_MODULES
    ab_after = {a["module_id"] for a in after["abstained"]} - NESTED_INPUT_MODULES
    check(ab_before == ab_after, "and the same modules abstain outside the fourteen")
    check(NESTED_INPUT_MODULES <= {a["module_id"] for a in before["abstained"]},
          "FAULT DIRECTION CONFIRMED: without the adapter all fourteen abstain, which is the "
          "defect this run fixes",
          str(sorted(NESTED_INPUT_MODULES - {a['module_id'] for a in before['abstained']})))

    print()
    print("=" * 78)
    print("9. The adapter assembles from evidence only, and never invents a signal")
    print("=" * 78)

    signals, absence = build_signals({"cpi": 0.9, "spi": 0.9, "docRiskScore": 0.5}, [])
    check(set(signals) == {"evm", "doc"},
          "with no forecast and no trend computed, only the two evidence-backed signals exist",
          str(sorted(signals)))
    check("abstained" in absence["mc"] and "abstained" in absence["cusum"],
          "and the absent two say the computation behind them abstained")
    signals2, absence2 = build_signals({"cpi": 0.9}, [])
    check("evm" not in signals2 and "schedule index" in absence2["evm"],
          "one index alone assembles no index pair: no substituted 1.0, no fabrication",
          str(absence2.get("evm")))
    signals3, _ = build_signals({"cpi": 0.9, "spi": 0.9, "docRiskScore": 0.5}, [
        {"module_id": "A1.1", "status_color": "red", "overrun_pct_p80": 12.5, "p80_eac": 9e6,
         "p50_eac": 8e6},
        {"module_id": "A1.2", "status_color": "amber", "breached": False, "max_stat": 0.2,
         "H": 0.3},
    ])
    check(signals3["mc"]["p80DeltaPct"] == 12.5 and signals3["mc"]["status"] == "red",
          "the forecast signal is the forecast computation's own figure and its own status")
    check(signals3["cusum"]["breached"] is False and signals3["cusum"]["status"] == "amber",
          "and the trend signal is the trend computation's own")
    check(evm_status(0.99, 0.99) == "green" and evm_status(0.94, 0.99) == "amber"
          and evm_status(0.89, 0.99) == "red",
          "the index status thresholds match the instrument's own assembler, all three bands")
    check(doc_status(0.29) == "green" and doc_status(0.30) == "amber"
          and doc_status(0.70) == "red",
          "and so do the document risk bands, exactly at each boundary")
    check(len(NESTED_INPUT_MODULES) == 14
          and NESTED_INPUT_MODULES == set(FOURTEEN),
          "the adapter names exactly the fourteen the audit named")
    check(sum(len(t) for t in ADAPTER_TIERS) == 14,
          "and every one of them is placed in exactly one assembly tier")

    print()
    print("=" * 78)
    print("10. Fault injection on the reachability check itself")
    print("=" * 78)

    # If the adapter stopped supplying the assembled package, section 1's reachability check
    # must go red rather than quietly reporting fewer modules.
    saved_tiers = registry.ADAPTER_TIERS
    registry.ADAPTER_TIERS = ((), (), ())
    broken = compute_project(dict(si4), PRJ, "P4", CUTOFF)
    registry.ADAPTER_TIERS = saved_tiers
    broken_reached = [m for m in FOURTEEN if m in {x["module_id"] for x in broken["modules"]}]
    check(len(broken_reached) == 0,
          "FAULT: with the adapter's tiers emptied nothing of the fourteen computes, which is "
          "what the reachability check would catch", str(broken_reached))
    rerun = compute_project(dict(si4), PRJ, "P4", CUTOFF)
    check(len([m for m in FOURTEEN if m in {x["module_id"] for x in rerun["modules"]}]) == 12
          and rerun["project_status"] == after["project_status"],
          "and the baseline is restored after the fault, status included")

finally:
    set_extractor_override(None)

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED}")
sys.exit(0 if FAILED == 0 else 1)
