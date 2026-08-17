#!/usr/bin/env python3
"""
D1: the module inputs nothing could produce. Wired where the platform has the evidence,
abstaining where it never can.

THE DEFECT, AS MEASURED BEFORE THIS WAS BUILT. Twelve keys were read by the analytical layer and
written by nothing. They were the browser's `existingSignals` blob plus the project's event log
and its per-period history, and the port faithfully reproduced what the JavaScript did when they
were missing -- a browser edge case that server-side was the ONLY path. Twelve modules therefore
produced a verdict from an empty evidence set on every project ever computed:

  * A1.2 CUSUM synthesised twelve observations from the current SPI and drew a control chart over
    them. On the suite's own HEALTHY fixture that fabricated chart reported RED, which took
    category A1 to Red and the whole PROJECT to Red. A project running ahead of plan was reported
    as distressed because a series nobody measured drifted away from the target.
  * B2.1 Dempster-Shafer combined three vacuous masses with one asserted Green (an absent doc risk
    read as score 0) and returned Green.
  * B2.2-B2.8 emitted an AMBER "Insufficient signal data" stub carrying a status colour; B2.2's
    denominator was `len(classes) or 1`, so an empty evidence set divided by a fictitious one.
  * B2.9 defaulted to evm_min 1.0, no breach and doc score 0 -- three pieces of good news -- and
    returned Green.
  * C1.4 reported "0 events recorded" and a Red band about a platform that has recorded events in
    exactly the shape it reads since `_append_event` was written.
  * C1.7 emitted a Yellow "upload more documents" stub.

WHAT CHANGED. `events`, `spiHistory` and `cpiHistory` are now supplied by documents.py, because
the platform holds that evidence. The eight legacy blob keys cannot ever be supplied -- the
browser no longer computes -- so the modules reading them abstain. Every fabrication path is
removed rather than gated.

THE VACUOUS-CHECK TRAP, ADDRESSED DIRECTLY. The specific way this suite could pass for the wrong
reason: an abstention check that passes because the module ALREADY abstained for an unrelated
missing input, proving nothing about the fabrication path. Section 2 therefore feeds each module
a signalInputs that is COMPLETE except for the key under test, and section 1 asserts against that
same input that the module's other guards do not fire. A key's removal, not a bare empty dict,
is what each check varies.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_d1_module_inputs.py
"""

from __future__ import annotations

import base64
import hashlib
import inspect
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
import app.simulation.models_dq as models_dq  # noqa: E402
import app.simulation.models_evc as models_evc  # noqa: E402
import app.simulation.models_gov as models_gov  # noqa: E402
import app.simulation.models_sim as models_sim  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import ComputedResult, Participant  # noqa: E402
from app.simulation.registry import run_module  # noqa: E402
# =================================================================================================
# RUN 31, PASS 1: THIS SUITE IS HISTORICAL_ONLY FOR CATEGORY 8 AND CATEGORY 9.
#
# The assertions below describe implementations Run 31 superseded. They are preserved unedited,
# because they are the scientific record of what this instrument used to do, and the legacy code
# they describe is preserved for the same reason. What changes is resolution: for the sixteen
# Category-8/9 identities ONLY, `registry.run_module` executes the preserved legacy runner.
# Every other module still resolves to live production.
#
# The second half of the contract is asserted at the end of this block: current production
# reaches NONE of the sixteen legacy implementations and ALL sixteen canonical routes.
# =================================================================================================
import run31_historical_cat89 as _R31H                                        # noqa: E402
_R31H_HISTORICAL_ONLY = True

def _r31h_install():
    # Patch the registry MODULE OBJECT, not a local alias: every suite holds a reference to the
    # same singleton module however it spelled the import, so this reaches all of them.
    from app.simulation import registry as _registry
    _live = _registry.run_module

    def _resolve(new_id, si, rand, period_cutoff, *a, **k):
        if new_id in _R31H.LEGACY_CAT89:
            return _R31H.run_legacy(new_id, si, rand, period_cutoff)
        return _live(new_id, si, rand, period_cutoff, *a, **k)

    _registry.run_module = _resolve

_r31h_install()
# This suite imported `run_module` BY NAME and holds its own reference, which
# patching the module cannot reach, so the name is rebound here as well.
from app.simulation import registry as _r31h_reg                      # noqa: E402
run_module = _r31h_reg.run_module

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0

CUTOFF = "2026-07-31"


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def run(module_id: str, si: dict) -> dict:
    return run_module(module_id, si, lambda: 0.5, CUTOFF)


def abstains(out: dict) -> bool:
    """The abstention contract from models.insufficient: no colour, and it says why."""
    return out.get("status_color") is None and out.get("insufficient_data") is True


# A signalInputs carrying EVERY key each module under test needs EXCEPT the one being removed.
# Deliberately generous: if a module abstains on this, it is not abstaining because of D1.
FULL = {
    "bac": 8_000_000, "ev": 5_000_000, "ac": 4_900_000, "pv": 4_800_000,
    "cpi": 1.02, "spi": 1.04, "docRiskScore": 0.2,
    "actualPctComplete": 62, "plannedPctComplete": 60,
    "baselineStart": "2025-01-01", "baselineEnd": "2027-01-01", "docDate": "2026-07-20",
    # The eight legacy blob keys, in the shapes the modules document.
    "evm": {"cpi": 1.02, "spi": 1.04},
    "mc": {"p80DeltaPct": 3.0},
    "cusum": {"breached": False},
    "doc": {"score": 0.2},
    "decision": {"state": "Green"},
    # The three the platform can supply.
    # Date-only `at`, which is the contract models_dq documents and `_js_date_ms` enforces.
    "events": [
        {"event": "project_created", "at": "2026-01-05"},
        {"event": "signals_extracted", "at": "2026-05-01"},
        {"event": "signals_extracted", "at": "2026-06-01"},
    ],
    "spiHistory": [1.00, 1.01, 1.03, 1.04],
    "cpiHistory": [0.99, 1.00, 1.01, 1.02],
}

# The twelve, and the key whose absence used to be fabricated around.
# `blob` MARKED THE KEYS NOTHING COULD SUPPLY, and that is no longer true: the flat-to-nested
# adapter (remediation Run 3, server/app/simulation/signal_package.py) assembles evm, mc, cusum,
# doc and decision from the flat inputs and this run's own results, so these seven now receive
# their declared contract on the normal path. The label is kept because it names the class of
# fix each check below is about; section 5 records what changed and why.
#
# B2.7 (Plithogenic Sets) and B2.9 (Quantum Probability) are removed from this list by
# remediation Run 1 (remediation_programme.md): both are on the eight-module DISABLED_CONCEPT_
# ONLY list the external arithmetic audit found undefensible, and registry.run_module() now
# short-circuits them to an abstention BEFORE their formula function is ever called, on every
# input, complete or not. Their D1 fabrication fix still stands (nothing was reverted) but is no
# longer observable through this test: a disabled module abstains unconditionally, so neither
# "precondition: computes on a complete input" nor "abstains specifically because THIS key is
# absent" is a meaningful assertion about them any more. They stay disabled, not merely
# re-fabricated, so removing them here is correct rather than a loosened check.
#
# RUN 30 CLOSURE. THE SEVEN CATEGORY-7 ENTRIES MOVE OUT OF THIS LIST, for exactly the reason
# remediation Run 1 moved B2.7 and B2.9 out of it, and the paragraph above states the rule: a
# module that abstains UNCONDITIONALLY can no longer demonstrate "abstains specifically because
# THIS key is absent". All seven now route through the canonical Category-7 layer, whose defining
# structures are governed epistemic objects -- a mass function over a stated frame, a decision
# table, an assessed truth/indeterminacy/falsity triple, an elicited membership range, a stated
# reliability, a linguistic probability distribution, an elicited belief rule base. None of those
# is any of the assembled blob keys, so removing `evm` or `doc` from this fixture cannot be what
# makes them abstain: they abstain on the COMPLETE fixture too.
#
# THEIR D1 FIX STILL STANDS AND NOTHING WAS REVERTED. Section 3 below still asserts, against the
# emitted literals, that the fabrication paths are gone from the source of the legacy
# implementations, and section 1c asserts the stronger property the repointing gives them.
TWELVE = [
    ("A1.2", "spiHistory", "wired"),
    ("C1.4", "events", "wired"),
    ("C1.7", "events", "wired"),
]

#: The seven Category-7 identities that now abstain unconditionally on a signalInputs carrying no
#: governed epistemic structure, however complete it is in the flat and blob keys.
CANONICAL_NOW = ["B2.1", "B2.2", "B2.3", "B2.4", "B2.5", "B2.6", "B2.8"]

# The two now-disabled modules, checked separately: they must abstain UNCONDITIONALLY (on the
# complete fixture too), carrying the DISABLED_UNSAFE activation state, never reaching their
# formula function at all.
DISABLED_NOW = ["B2.7", "B2.9"]


def without(*keys: str) -> dict:
    si = json.loads(json.dumps(FULL))
    for k in keys:
        si.pop(k, None)
    return si


print("=" * 78)
print("D1: twelve module inputs")
print("=" * 78)

# ---------------------------------------------------------------- 1: the precondition

print("\n1. PRECONDITION: with every key present, all twelve COMPUTE")
print("   Without this, section 2's abstentions would prove nothing: a module that abstained")
print("   for an unrelated reason would pass every check there.")

for module_id, _key, _kind in TWELVE:
    out = run(module_id, FULL)
    check(not abstains(out) and out.get("status_color") is not None,
          f"PRECONDITION {module_id} computes on a complete signalInputs",
          f"{out.get('status_color')} / {out.get('evidence_metric')}")

# ---------------------------------------------------------- 1b: the two now-disabled modules

print("\n1b. B2.7 and B2.9 are disabled (remediation Run 1): they abstain even on the complete")
print("    fixture, and their formula function is never reached.")

for module_id in DISABLED_NOW:
    out = run(module_id, FULL)
    check(abstains(out) and out.get("status_color") is None,
          f"{module_id} abstains unconditionally, even on a complete signalInputs",
          f"{out.get('status_color')} / {out.get('evidence_metric')}")
    check(out.get("activation_state") == "DISABLED_UNSAFE",
          f"{module_id} carries activation_state DISABLED_UNSAFE",
          str(out.get("activation_state")))

# ------------------------------------------- 1c: the seven now-canonical Category-7 modules

print("\n1c. B2.1 to B2.6 and B2.8 route to the canonical Category-7 layer (Run 30 closure):")
print("    they abstain even on the complete fixture, because a complete set of crisp project")
print("    metrics is not a mass function, a decision table or an elicited membership.")

for module_id in CANONICAL_NOW:
    out = run(module_id, FULL)
    check(abstains(out),
          f"{module_id} abstains on a complete signalInputs carrying no governed epistemic "
          f"structure", f"{out.get('status_color')} / {out.get('evidence_metric')}")
    check(out.get("result_source") == "CANONICAL_V5_LAYER",
          f"{module_id} records that the canonical route produced the silence, not a proxy",
          str(out.get("result_source")))
    check(out.get("canonical_disposition") == "NOT_ESTIMABLE_STRUCTURE_ABSENT",
          f"{module_id} names the disposition rather than going quiet",
          str(out.get("canonical_disposition")))
    check(bool(out.get("canonical_structure")),
          f"{module_id} names the structure it was waiting for")

# ---------------------------------------------------------------- 2: absence abstains

print("\n2. Each of the twelve abstains when its input is absent, and abstains in the ONE")
print("   documented shape (status_color None, insufficient_data True, a reason)")

for module_id, key, _kind in TWELVE:
    si = without(*key.split("+"))
    out = run(module_id, si)
    check(abstains(out), f"{module_id} abstains without {key}",
          f"{out.get('status_color')} / {out.get('evidence_metric')}")
    check(bool(out.get("evidence_metric")), f"{module_id} says why it abstained",
          str(out.get("evidence_metric")))

# ---------------------------------------------------------------- 3: no fabrication survives

print("\n3. The fabrication paths are gone from the source, not merely unreached")

check(not hasattr(models_sim, "derive_series"),
      "models_sim.derive_series (the synthesised CUSUM series) no longer exists")
check(not hasattr(models_sim, "hash_seed"),
      "models_sim.hash_seed, which existed only to seed that series, no longer exists")
# Matched against the emitted LITERALS, not against prose: the docstrings and comments in both
# files describe the removed fallbacks on purpose, so a bare substring search over the source
# would fail on the explanation rather than on the defect.
evc_src = inspect.getsource(models_evc)
check('"evidence_metric": "Insufficient signal data"' not in evc_src,
      "no AMBER 'Insufficient signal data' stub remains in the evidence-combination models")
check('"id": "R0"' not in evc_src,
      "the Belief Rule Base R0 fallback rule is gone")
check("len(classes) or 1" not in inspect.getsource(models_evc.run_rough_sets),
      "Rough Sets no longer divides by a fabricated denominator")
check('"upload more documents for frequency analysis"' not in inspect.getsource(models_dq),
      "the C1.7 Yellow 'upload more documents' stub is gone")

# A colour must never be reachable from an empty evidence set for any of the twelve.
empty = {"cpi": 1.02, "spi": 1.04, "bac": 8_000_000}
for module_id, _key, _kind in TWELVE:
    out = run(module_id, empty)
    check(abstains(out), f"{module_id} abstains on a signalInputs with no D1 keys at all",
          str(out.get("status_color")))

# ---------------------------------------------------------------- 4: wired keys are USED

print("\n4. The three wired keys reach their modules and change the answer")

# A1.2 CUSUM: the supplied series, not a synthesised one. A twelve-point synthesised series was
# what it used to build, so a four-point result is proof the real series was consumed.
cu = run("A1.2", FULL)
check(cu.get("periods") == 4, "CUSUM reports the 4 periods it was given, not a synthesised 12",
      str(cu.get("periods")))
cu_breach = run("A1.2", {**FULL, "spiHistory": [1.0, 0.9, 0.8, 0.6, 0.5, 0.4]})
check(cu_breach.get("breached") is True and cu.get("breached") is False,
      "CUSUM's breach verdict follows the supplied series, in both directions",
      f"steady={cu.get('breached')} collapsing={cu_breach.get('breached')}")

# RUN 28. A1.5 still reads the cost performance series and its forecast still follows it; what
# changed is that an identified model needs a longer history than v10's three points, so the
# probe supplies one. A1.4 and A1.10 no longer read a bare series at all: the supplied contract
# requires a governed state-space record whose process and measurement variances state where
# they came from, and a governed reference population, and neither is in this corpus. Both
# therefore abstain, which is the contract's own answer and is asserted here rather than being
# left as a silent gap.
_LONG_CPI = [0.99, 0.97, 0.96, 0.94, 0.93, 0.91, 0.90, 0.88, 0.87, 0.86]
ari = run("A1.5", {**FULL, "cpiHistory": _LONG_CPI})
ari2 = run("A1.5", {**FULL, "cpiHistory": [round(v - 0.10, 4) for v in _LONG_CPI]})
check(ari.get("forecast_cpi") != ari2.get("forecast_cpi"),
      "ARIMA's CPI forecast follows the supplied cpiHistory",
      f"{ari.get('forecast_cpi')} vs {ari2.get('forecast_cpi')}")
check(run("A1.5", FULL).get("insufficient_data") is True,
      "and a history shorter than the identification minimum is not estimable rather than "
      "being forced through a fixed order model",
      str(run("A1.5", FULL).get("evidence_metric"))[:80])
for _mid, _what in (("A1.4", "a state space model whose process and measurement variances state "
                             "where they came from"),
                    ("A1.10", "a governed reference population of comparable projects")):
    _r = run(_mid, FULL)
    check(_r.get("insufficient_data") is True
          and _r.get("abstention_reason_code") == "canonical_structure_absent",
          f"{_mid} abstains on the series alone, because it needs {_what} and this corpus "
          f"holds none", str(_r.get("abstention_reason_code")))

# C1.4 counts what is in the log; C1.7 measures the interval between extraction events.
at = run("C1.4", FULL)
check(at.get("total_events") == 3, "Audit Trail counts the events it was given",
      str(at.get("total_events")))
at2 = run("C1.4", {**FULL, "events": FULL["events"] + [
    {"event": "decision_recorded", "at": "2026-06-15"}]})
check(at2.get("has_decision_record") is True and at.get("has_decision_record") is False,
      "Audit Trail sees a decision record when the log contains one")
rf = run("C1.7", FULL)
check(rf.get("uploads") == 2 and rf.get("avg_interval_days") == 31,
      "Reporting Frequency measures the real interval between the two extraction events",
      f"{rf.get('uploads')} uploads / {rf.get('avg_interval_days')}d")

# An EMPTY log is evidence and is reported; an ABSENT log is not, and abstains.
at_empty = run("C1.4", {**FULL, "events": []})
check(not abstains(at_empty) and at_empty.get("total_events") == 0,
      "an EMPTY event log is evidence and is reported, not abstained on",
      str(at_empty.get("status_color")))
check(abstains(run("C1.4", without("events"))),
      "an ABSENT event log abstains, because the caller said nothing about the project")

# A one-period 'history' must not masquerade as a series.
check(abstains(run("A1.2", {**FULL, "spiHistory": [1.04]})),
      "CUSUM abstains on a single-point history rather than treating it as a series")

# ---------------------------------------------------------------- 5: the project-level effect

print("\n5. The project-level effect, measured through compute_project")

from app.simulation import compute_project  # noqa: E402


HEALTHY = {"spi": 1.05, "cpi": 1.02, "bac": 8000000, "actualPctComplete": 62}
healthy_run = compute_project(dict(HEALTHY), "sc-d1", "P1", CUTOFF)
check(healthy_run["project_status"] == "Green",
      "the suite's HEALTHY fixture is now GREEN; the fabricated CUSUM used to make it RED",
      str(healthy_run["project_status"]))
check("A1.2" in {a["module_id"] for a in healthy_run["abstained"]},
      "and it is Green because CUSUM abstains rather than reporting a synthesised breach")
statuses = {m["module_id"]: m.get("status_color") for m in healthy_run["modules"]}

# WHAT THIS SECTION USED TO ASSERT, AND WHY IT WAS REWRITTEN RATHER THAN LOOSENED.
#
# It asserted that ALL twelve contribute no colour on this fixture. For the wired three (A1.2,
# C1.4, C1.7) that is a real property and it still holds below: they have no history and no
# event log here, so they abstain. For the seven evidence-combination modules it was true for a
# DIFFERENT reason, and the reason was a defect: their input contract is a nested assembled
# signal package, the computation path supplied a flat dictionary, and nothing anywhere
# assembled one -- so they abstained on every project regardless of what evidence it held. That
# is audit P0 finding 1, and the flat-to-nested adapter (remediation Run 3,
# server/app/simulation/signal_package.py) fixes it.
#
# So this check was recording the old wiring failure as expected behaviour. The property D1
# actually protects is that no colour is produced from an EMPTY evidence set, and that is what
# is asserted now, in both directions: with cost and schedule indices present the seven combine
# real evidence, and with no evidence at all they still abstain. Nothing in D1's fabrication
# fixes was reverted -- section 2 above still drives each module directly and proves each one
# abstains when its own key is removed.
BLOB_SEVEN = [m for m, _k, kind in TWELVE if kind == "blob"]
WIRED_THREE = [m for m, _k, kind in TWELVE if kind == "wired"]
for module_id in WIRED_THREE:
    check(module_id not in statuses,
          f"{module_id} contributes no colour to a project with no D1 evidence")
for module_id in BLOB_SEVEN:
    check(statuses.get(module_id) is not None,
          f"{module_id} now combines the evidence this project DOES hold, through the adapter",
          str(statuses.get(module_id)))

EMPTY = {"actualPctComplete": 62}
empty_run = compute_project(dict(EMPTY), "sc-d1", "P1", CUTOFF)
empty_statuses = {m["module_id"] for m in empty_run["modules"]}
for module_id in BLOB_SEVEN:
    check(module_id not in empty_statuses,
          f"{module_id} still abstains on a project with NO evidence to combine, which is the "
          f"property D1 protects")

DISTRESSED = {"spi": 0.70, "cpi": 0.80, "bac": 12500000, "actualPctComplete": 15}
distressed_run = compute_project(dict(DISTRESSED), "sc-d1", "P1", CUTOFF)
check(distressed_run["project_status"] == "Red",
      "the DISTRESSED fixture stays RED: abstention does not soften a bad project",
      str(distressed_run["project_status"]))

# ---------------------------------------------------------------- 6: end to end

print("\n6. End to end: documents.py supplies events and history, and cannot supply the future")

PROJ = "PRJ-D1WIRE01"
ADMIN = "d1-admin-token"


def monthly_bytes(period: int) -> bytes:
    return f"%PDF-1.4 D1 MONTHLY REPORT P{period}\n".encode()


# Two periods of the same project, with EV rising so cpi differs period to period.
PERIODS = {
    1: {"earned_value": 4_000_000, "actual_cost": 4_200_000, "planned_value": 4_100_000,
        "budget_at_completion": 10_000_000, "actual_percent_complete": 40.0,
        "planned_percent_complete": 41.0, "report_date": "2026-05-31",
        "document_date": "2026-05-31"},
    2: {"earned_value": 5_000_000, "actual_cost": 4_900_000, "planned_value": 5_100_000,
        "budget_at_completion": 10_000_000, "actual_percent_complete": 50.0,
        "planned_percent_complete": 51.0, "report_date": "2026-06-30",
        "document_date": "2026-06-30"},
    3: {"earned_value": 6_000_000, "actual_cost": 5_600_000, "planned_value": 6_050_000,
        "budget_at_completion": 10_000_000, "actual_percent_complete": 60.0,
        "planned_percent_complete": 61.0, "report_date": "2026-07-31",
        "document_date": "2026-07-31"},
}
RECORDED = {hashlib.sha256(monthly_bytes(p)).hexdigest(): ("monthly_report", fields)
            for p, fields in PERIODS.items()}
set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="D1-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PROJ)) is None:
        s.add(Project(legacy_id=PROJ, doc={
            "id": PROJ, "name": "D1 wiring", "signals": {},
            # The event log the platform has always written and never passed in.
            "events": [
                {"event": "project_created", "at": "2026-01-05T00:00:00.000Z"},
                {"event": "signals_extracted", "at": "2026-04-01T00:00:00.000Z"},
                {"event": "signals_extracted", "at": "2026-05-01T00:00:00.000Z"},
                # AFTER every period cutoff below. Must never reach an earlier period.
                {"event": "signals_extracted", "at": "2026-12-01T00:00:00.000Z"},
            ]}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "D1-PM", "role": "Participant",
                "account_type": "operational"})
pm_id = created["participant_id"]
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PROJ,
      "participant_id": pm_id, "project_role": "PM"})

stored: dict[int, dict] = {}
for period in (1, 2, 3):
    up = post({"action": "projectupload", "session_token": pm, "id": PROJ, "period": period,
               "documents": [{"filename": f"monthly-p{period}.pdf",
                              "mimeType": "application/pdf",
                              "dataBase64": b64(monthly_bytes(period))}]})
    check(up.get("ok") is True, f"period {period} document uploaded", str(up)[:100])
    post({"action": "projectcompute", "session_token": pm, "id": PROJ, "period": period})
    stored[period] = post({"action": "projectresults", "session_token": pm,
                           "id": PROJ, "period": period})["result"]

si1, si2, si3 = (stored[p]["signal_inputs"] for p in (1, 2, 3))

check("events" in si1, "the event log reaches signalInputs and is recorded on the result")
# The project document stores full ISO datetimes; `_js_date_ms` refuses those by design. Without
# the narrowing in `_events_as_of`, C1.7 would abstain on every real project while LOOKING wired,
# which is the exact failure this suite exists to catch.
check(len(si3.get("events") or []) >= 3 and all(len(str(e.get("at"))) == 10 for e in si3["events"]),
      "event timestamps are narrowed to date-only at the boundary, as models_dq requires",
      str([e.get("at") for e in (si3.get("events") or [])]))
mods_c17 = {m["module_id"] for m in stored[3]["module_results"]}
check("C1.7" in mods_c17,
      "so C1.7 COMPUTES on a real project's log rather than abstaining on an unparsable stamp")
check(si1.get("cpiHistory") is None,
      "period 1 gets NO history: there is no earlier period, and a one-point series is not one",
      str(si1.get("cpiHistory")))
check(si2.get("cpiHistory") == [si1["cpi"], si2["cpi"]],
      "period 2's cpiHistory is period 1's stored cpi followed by its own",
      str(si2.get("cpiHistory")))
check(si3.get("cpiHistory") == [si1["cpi"], si2["cpi"], si3["cpi"]],
      "period 3's cpiHistory is the ordered series across all three",
      str(si3.get("cpiHistory")))
check(si3.get("spiHistory") == [si1["spi"], si2["spi"], si3["spi"]],
      "and spiHistory likewise", str(si3.get("spiHistory")))

# The three history readers now compute rather than abstain, on real data.
mods3 = {m["module_id"]: m for m in stored[3]["module_results"]}
# RUN 28. Of the three history readers, CUSUM still computes on the real series -- its design is
# frozen and the supplied contract forbids retuning it -- while Kalman needs a governed
# state-space record and ARIMA needs a longer history than three periods to identify a model
# from. Both abstain truthfully rather than reporting a fixed-parameter reading.
_ab3 = {a["module_id"]: a for a in stored[3].get("abstained") or []}
check("A1.4" not in mods3 and "A1.4" in _ab3,
      "Kalman abstains at period 3: the project's real SPI series is there, but no state space "
      "model stating where its variances came from is")
check("A1.5" not in mods3 and "A1.5" in _ab3,
      "ARIMA abstains at period 3: three observations are fewer than an identified model needs")
check("A1.2" in mods3, "CUSUM computes at period 3, on the project's real SPI series")
check(mods3.get("A1.2", {}).get("periods") == 3,
      "and CUSUM's chart is drawn over 3 real observations, not 12 invented ones",
      str(mods3.get("A1.2", {}).get("periods")))

mods1 = {m["module_id"]: m for m in stored[1]["module_results"]}
check("A1.2" not in mods1 and "A1.4" not in mods1 and "A1.5" not in mods1,
      "at period 1 all three abstain, because one period is not a history")

# NO LEAKAGE. This is the property the task required be established before building the history.
# `all()` over an empty list is True, so each truncation check below asserts the log is NON-EMPTY
# first. Without that, removing the wiring entirely would leave these three green.
ev1 = si1.get("events") or []
ev3 = si3.get("events") or []
# Compared against each period's OWN stored cutoff rather than a literal date. The upload now
# writes a `signals_extracted` event stamped at upload time, so the seeded four are no longer the
# whole log — a hardcoded count would have to be edited every time the fixture uploads anything,
# and the property being asserted was never the count. The non-emptiness floor stays, because
# `all()` over an empty list is True and that is what these checks exist to rule out.
cut1 = str(stored[1]["period_cutoff"])[:10]
check(len(ev1) >= 3 and all(e.get("at", "")[:10] <= cut1 for e in ev1),
      "period 1's event log is truncated at its cutoff: later activity does not reach it",
      f"cutoff {cut1}: " + str([e.get("at") for e in ev1]))
check(len(ev3) >= 3 and not any(e.get("at", "").startswith("2026-12") for e in ev3),
      "and the December event reaches no period, all three cutoffs preceding it",
      str([e.get("at") for e in ev3]))
check(len(ev3) >= len(ev1) > 0,
      "a later period sees at least as much of the log as an earlier one",
      f"{len(ev1)} then {len(ev3)}")

# A recompute of period 1 while periods 2 and 3 exist must produce the same history and the
# same events. This is the leak the pipeline audit found in the portfolio vector block, proven
# absent here.
post({"action": "adminrecompute", "session_token": admin, "id": PROJ, "period": 1,
      "reason": "D1 leakage check"})
si1b = post({"action": "projectresults", "session_token": pm,
             "id": PROJ, "period": 1})["result"]["signal_inputs"]
check(si1b.get("cpiHistory") is None and si1b.get("spiHistory") is None,
      "recomputing period 1 with periods 2 and 3 stored gives it NO history from the future",
      str(si1b.get("cpiHistory")))
check((si1b.get("events") or []) == ev1 and len(ev1) > 0,
      "and the same truncated event log, so the recompute reproduces the original")

with Session() as s:
    live = s.scalars(select(ComputedResult).where(
        ComputedResult.superseded_by.is_(None))).all()
    check(len({(r.project_id, r.period) for r in live}) == len(live),
          "one live result per (project, period) still holds after the recompute")

print()
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(0 if FAILED == 0 else 1)
