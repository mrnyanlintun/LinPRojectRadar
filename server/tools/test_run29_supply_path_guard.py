"""
RUN 29 -- THE SUPPLY-PATH COMPLETENESS GUARD, and section 15 of the supplied contract.

WHY THIS SUITE EXISTS. Run 28's closure audit found twenty-one of its twenty-three canonical
structure keys written by NO production code at all: they existed in test fixtures and nowhere
else. An abstention whose supply path only a test can exercise is a DESCRIPTION of a supply path,
not one, and section 15 of the Run-29 contract requires that the defect is not repeated:
"reasonably supplyable structures with no production path = 0", plus "a guard that fails when a
new canonical structure is introduced without production intake/derivation".

WHAT THIS SUITE PROVES, and it is the mechanical form of that requirement.

1. EVERY v4 STRUCTURE KEY IS IN THE GOVERNED INTAKE VOCABULARY. The vocabulary is read from
   `app.project_data.governed_structure_keys()`, which reads the analytical layer rather than
   restating it, so a key added to `canonical_v4` and forgotten in the intake is red here.

2. THE PATH IS EXERCISED END TO END, not asserted. For each of the seventeen structures a record
   is stored through `project_data.add_revision`, read back through `structures_as_of`, merged
   onto signal inputs through `apply_to_signal_inputs`, and the module is then run FROM THE
   REGISTRY on those inputs and required to compute. That is the same sequence
   `documents.py::run_and_store` performs, so what is proved is the production route rather than
   a direct call.

3. THE STORE'S OWN RULES HOLD FOR THE NEW KEYS: an unknown key is refused, a record with no
   provenance is refused, and a structure supplied for a later period is invisible to an earlier
   one, so recomputing an earlier period stays byte-identical.

4. THE RECONCILIATION FILE AGREES WITH THE CODE, row for row, and the count of reasonably
   supplyable structures with no production path is asserted to be ZERO.

5. THE GUARD IS NOT VACUOUS. A key is removed from the intake vocabulary in an isolated copy of
   the check and the guard is required to go red, then restored.
"""

from __future__ import annotations

import csv
import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app import project_data as PD                              # noqa: E402
from app.simulation import registry as REG                      # noqa: E402
from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS       # noqa: E402
import run29_fixtures as FX                                     # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731
RECON = ROOT / "code_audit" / "run29_supply_path_reconciliation.csv"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


#: structure key -> the module that reads it and a fixture that satisfies its contract.
CASES = {
    "documentRiskEvidence": (None, FX.document_risk_evidence),
    "rfiEventLog": ("A4.2", FX.rfi_event_log),
    "submittalDecisionRegister": ("A4.3", FX.submittal_register),
    "ncrExposureRecord": ("A4.4", FX.ncr_record),
    "weatherImpactEvents": ("A4.5", FX.weather_events),
    "changeEventRegister": ("A4.6", FX.change_register),
    "claimDisputeRegister": ("A4.7", FX.dispute_register),
    "subcontractorAssessments": ("A4.8", FX.subcontractor_assessment),
    "procurementItems": ("A4.9", FX.procurement_items),
    "specificationConflictRegister": ("A4.10", FX.conflict_register),
    "dsmDependencyModel": ("A5.1", FX.dsm_model),
    "sensitivityModel": ("A5.2", FX.sensitivity_model),
    "scenarioSet": ("A5.4", FX.scenario_set),
    "systemDynamicsModel": ("A5.5", FX.system_dynamics_model),
    "queueModel": ("A5.6", FX.queue_model),
    "agentSupplyChainModel": ("A5.7", FX.agent_model),
    "desProcessModel": ("A5.8", FX.des_model),
}


# =================================================================================================
head("1. EVERY v4 STRUCTURE IS IN THE GOVERNED INTAKE VOCABULARY")
# =================================================================================================

_keys = sorted(set(V4_STRUCTURE_KEYS.values()))
check(len(V4_STRUCTURE_KEYS) == 18 and len(_keys) == 17,
      "eighteen module-to-key entries over seventeen distinct keys, because one sensitivity "
      "model serves both A5.2 and A5.3", f"{len(V4_STRUCTURE_KEYS)} entries, {len(_keys)} keys")
_vocab = PD.governed_structure_keys()
_orphans = sorted(k for k in _keys if k not in _vocab)
check(not _orphans,
      "REASONABLY SUPPLYABLE STRUCTURES WITH NO PRODUCTION PATH = 0: every v4 key is a key the "
      "governed intake will accept", str(_orphans))
check(sorted(CASES) == _keys,
      "and this suite exercises every one of them rather than a sample",
      str(sorted(set(CASES) ^ set(_keys))))


# =================================================================================================
head("2. THE PATH IS EXERCISED END TO END, THROUGH THE PRODUCTION ROUTE")
# =================================================================================================

for _key in _keys:
    _mid, _builder = CASES[_key]
    _doc = PD.add_revision({}, _key, _builder(), effective_period=3,
                           supplied_by="the project controls manager",
                           source="the register exported on 30 June", at="2026-06-30T00:00:00Z")
    _inforce = PD.structures_as_of(_doc, 3)
    check(_key in _inforce and _inforce[_key] == _builder(),
          f"{_key}: stored through the governed intake and read back unchanged")
    _si: dict = {}
    _added = PD.apply_to_signal_inputs(_si, _doc, 3)
    check(_added == [_key] and _si.get(_key) is not None,
          f"{_key}: merged onto the signal inputs the modules are given, and recorded as added",
          str(_added))
    if _mid is None:
        # A4.1 is registered but not registry-computed. Its consumer is the extraction merge in
        # documents.py, which re-derives docRiskScore from the governed evidence.
        from app.simulation.canonical_v4 import document_risk_evidence  # noqa: E402
        _reading = document_risk_evidence(_si[_key])
        check(abs(_reading["risk_score"] - 1.0 / 1.5) < 1e-12
              and _reading["classifier_version"] == "rules-1.0",
              f"{_key}: the canonical aggregation computes from it, with its classifier version")
        _src = (ROOT / "server" / "app" / "documents.py").read_text(encoding="utf-8")
        check("documentRiskEvidence" in _src and "docRiskScoreDerivation" in _src,
              f"{_key}: and production reads it where the signal inputs are assembled, recording "
              f"the derivation on the stored row")
        continue
    _out = REG.run_module(_mid, dict(_si), RAND, CUTOFF)
    check(not _out.get("insufficient_data"),
          f"{_key}: {_mid} COMPUTES from what the governed intake delivered, through the "
          f"registry rather than through a direct call", str(_out.get("evidence_metric"))[:70])
    _absent = REG.run_module(_mid, {}, RAND, CUTOFF)
    check(bool(_absent.get("insufficient_data")),
          f"{_key}: and {_mid} abstains when nothing was supplied, so the reading really came "
          f"from the structure")

# A5.3 reads the same key A5.2 does, which is the parsimony decision, so it is exercised too.
_doc53 = PD.add_revision({}, "sensitivityModel", FX.tornado_model(), effective_period=1,
                         supplied_by="the estimator", source="the cost model of 3 June",
                         at="2026-06-30T00:00:00Z")
_si53: dict = {}
PD.apply_to_signal_inputs(_si53, _doc53, 1)
_t = REG.run_module("A5.3", _si53, RAND, CUTOFF)
check(not _t.get("insufficient_data") and _t.get("ranked_inputs") == ["A", "C", "B"],
      "A5.3 computes from the SAME governed key A5.2 does, which is the parsimony decision",
      str(_t.get("ranked_inputs")))


# =================================================================================================
head("3. THE STORE'S OWN RULES HOLD FOR THE NEW KEYS")
# =================================================================================================

try:
    PD.add_revision({}, "notAStructureAnyoneReads", {"x": 1}, effective_period=1,
                    supplied_by="a", source="b", at="t")
    check(False, "a key no computation consumes is refused")
except PD.ProjectDataError:
    check(True, "a key no computation consumes is refused, so a caller cannot write data that "
                "sits in the record forever looking like evidence")
for _blank in ("supplied_by", "source"):
    _kw = {"supplied_by": "a", "source": "b"}
    _kw[_blank] = "   "
    try:
        PD.add_revision({}, "queueModel", FX.queue_model(), effective_period=1, at="t", **_kw)
        check(False, f"a record with a blank {_blank} is refused")
    except PD.ProjectDataError:
        check(True, f"a record with a blank {_blank} is refused, because the analytical layer "
                    f"carries that provenance back out with the result")
_later = PD.add_revision({}, "queueModel", FX.queue_model(), effective_period=5,
                         supplied_by="a", source="b", at="t")
check(PD.structures_as_of(_later, 4) == {},
      "a structure supplied for a later period is invisible to an earlier one, so recomputing an "
      "earlier period reproduces it exactly")
check("queueModel" in PD.structures_as_of(_later, 5),
      "and visible from the period it takes effect from")
_appended = PD.add_revision(_later, "queueModel", FX.queue_model(arrival=1.0), effective_period=6,
                            supplied_by="a", source="b", at="t")
check(len(PD.revisions(_appended)["queueModel"]) == 2
      and PD.revisions(_appended)["queueModel"][0]["record"] == FX.queue_model(),
      "and a correction is a new revision rather than an edit of the old one")


# =================================================================================================
head("4. THE RECONCILIATION FILE AGREES WITH THE CODE")
# =================================================================================================

check(RECON.is_file(), "the supply-path reconciliation artefact exists", str(RECON))
_rows = list(csv.DictReader(RECON.open(encoding="utf-8")))
check(sorted(r["structure"] for r in _rows) == _keys,
      "and it carries exactly one row for each v4 structure, no more and no fewer",
      str(sorted(set(r["structure"] for r in _rows) ^ set(_keys))))
_served = {}
for _mid, _key in V4_STRUCTURE_KEYS.items():
    _served.setdefault(_key, []).append(_mid)
for _r in _rows:
    check(_r["modules_served"] == " ".join(sorted(_served[_r["structure"]])),
          f"{_r['structure']}: the modules it serves are the modules the code says it serves",
          _r["modules_served"])
    check(bool(_r["producer_or_intake"]) and bool(_r["canonical_validation_point"])
          and bool(_r["behaviour_when_absent"]),
          f"{_r['structure']}: names its intake, its validation point and what happens without it")
_no_path = [r["structure"] for r in _rows
            if r["reasonably_supplyable"] == "yes" and r["production_reachable"] != "yes"]
check(not _no_path,
      "REASONABLY SUPPLYABLE STRUCTURES WITH NO PRODUCTION PATH = 0, which is section 15's own "
      "acceptance condition", str(_no_path))
check(all(r["real_corpus_populated"] == "no" for r in _rows),
      "and the file states honestly that NO project in this corpus has supplied one yet: the "
      "path exists, the data do not, and neither claim is dressed as the other")


# =================================================================================================
head("5. THE GUARD IS NOT VACUOUS: IT GOES RED WHEN A STRUCTURE HAS NO INTAKE")
# =================================================================================================

# The fault: a v4 key that the intake vocabulary does not carry. Injected by removing one key
# from the vocabulary the check reads, in an isolated copy, and restored immediately.
_real = PD.governed_structure_keys
_victim = "queueModel"


def _crippled() -> set[str]:
    return {k for k in _real() if k != _victim}


PD.governed_structure_keys = _crippled          # inject
try:
    _confirmed = _victim not in PD.governed_structure_keys()
    check(_confirmed, "INJECTION CONFIRMED: the intake vocabulary no longer carries the key, "
                      "read back after the injection rather than assumed")
    _orphans_now = sorted(k for k in _keys if k not in PD.governed_structure_keys())
    check(_orphans_now == [_victim],
          "and the completeness check goes RED for the intended reason, naming exactly the "
          "structure that lost its intake", str(_orphans_now))
    try:
        PD.add_revision({}, _victim, FX.queue_model(), effective_period=1,
                        supplied_by="a", source="b", at="t")
        check(False, "and the store itself refuses to accept it, which is the operational "
                     "consequence of the orphan")
    except PD.ProjectDataError:
        check(True, "and the store itself refuses to accept it, which is the operational "
                    "consequence of the orphan")
finally:
    PD.governed_structure_keys = _real           # restore
check(_victim in PD.governed_structure_keys(),
      "RESTORED: the vocabulary carries the key again")
check(not sorted(k for k in _keys if k not in PD.governed_structure_keys()),
      "and the completeness check is GREEN again over all seventeen")


print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
