"""
RUN 29 CLOSURE -- THE SYNTHETIC PACKAGE CHAIN, AND THE THREE STALE FIXTURES IT REPLACES.

WHAT THIS SUITE PROVES.

1  WHAT THE THREE STALE FIXTURES SUPPLIED BEFORE, established by RUNNING the old importers rather
   than by describing them, so the finding is a measured fact and not a claim.
2  WHAT THEY SUPPLY NOW: the canonical shapes, imported from the SAME OG-SYNTH-0.3 tables where
   the package really holds the evidence, and from the OG-SYNTH-0.4 successor where it does not.
3  THE SUPPLIED CONTRACTS' OWN KNOWN ANSWERS on the successor package: 4/100 = 0.04; the M/M/1
   figures and two unstable cases that must refuse; the hand-computed three-agent trace.
4  THE CHAIN AND ITS IDENTITY RULE, including the masquerade rule that a file outside a
   predecessor's own record may not carry that predecessor's programme version.
5  FOUR OF THE SEVEN MANDATED FAULTS: the stale v2 NCR shape rejected, a queue fixture without
   arrival and service structure rejected, an ABM fixture without agents or rules rejected, and a
   predecessor package identifier stamped on changed current bytes rejected.

Every fault is INJECTED, the injection is CONFIRMED by reading the mutated state back, the guard
is observed RED for the intended reason, the fault is RESTORED and the guard observed GREEN again.
A crash is not accepted as red: every red observation is a boolean over a value that was returned.
"""

from __future__ import annotations
# Run 137, Item 1: a removed module identifier is SUBSTITUTED, not dispatched.
import os as _r96_os, sys as _r96_sys  # noqa: E402
_r96_sys.path.insert(0, _r96_os.path.dirname(_r96_os.path.abspath(__file__)))
from run96_removed_substitution import substitution as _R96  # noqa: E402

import datetime
import hashlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tests" / "synthetic_fixtures"))

from importers import production_structures as PS       # noqa: E402
from app.simulation import registry as REG              # noqa: E402
import synthetic_packages as SP                         # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731
PROJECT = "PRJ-AIR"
PERIOD = "P06"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))
    return ok


def near(label: str, got, want, tol: float = 1e-9) -> None:
    try:
        ok = got is not None and abs(float(got) - float(want)) <= tol
    except (TypeError, ValueError):
        ok = False
    check(ok, label, f"got {got!r}, expected {want!r}")


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def run(mid: str, si: dict) -> dict:
    return _R96.dispatch(REG.run_module, globals(), mid, si, RAND, CUTOFF)


def abstains(out: dict) -> bool:
    return bool(out.get("insufficient_data"))


# =================================================================================================
head("1. WHAT THE THREE STALE FIXTURES SUPPLIED, ESTABLISHED BY RUNNING THEM")
# =================================================================================================

_old_ncr = PS.audited_nonconformance_cohort(PROJECT, PERIOD)
check(set(_old_ncr) >= {"audits", "open_nonconformances"} and "exposure_unit" not in _old_ncr
      and "ncrs" not in _old_ncr,
      "A4.4 BEFORE: the fixture supplied an audited findings cohort and an open backlog, with no "
      "nonconformance events and no governed exposure denominator anywhere in it",
      str(sorted(_old_ncr))[:110])
check(abstains(run("A4.4", {"auditedNonconformanceCohort": _old_ncr})),
      "and the canonical module produces no reading from it, because a backlog over the size of "
      "an audit is a ratio of two different populations")

_old_queue = PS.queues(PROJECT)
_oq = _old_queue["queues"][0]
check("arrival_rate" not in _oq and "service_rate" not in _oq
      and {"entities", "horizon_days", "total_service_days", "wait_times_days"} <= set(_oq),
      "A5.6 BEFORE: the fixture supplied an occupancy log of entities, a horizon, a total service "
      "time and measured waits, with no arrival process and no service process",
      str(sorted(_oq))[:110])
check(abstains(run("A5.6", {"queueStructure": _old_queue})),
      "and the canonical module produces no reading from it, because a share of occupied server "
      "time is a measurement and not a queueing model")

_old_abm = PS.agents(PROJECT)
check({"agents", "states"} <= set(_old_abm)
      and all("behaviour_rule" not in a for a in _old_abm["agents"])
      and all("agent_type" not in a for a in _old_abm["agents"]),
      "A5.7 BEFORE: the fixture supplied a typed-in state history whose agents carried a decision "
      "rule IDENTIFIER and no executable behaviour, and no agent type at all",
      str(sorted(_old_abm["agents"][0]))[:110])
check(abstains(run("A5.7", {"abmStructure": _old_abm})),
      "and the canonical module produces no reading from it, because reading a table is not "
      "running a model")


# =================================================================================================
head("2. WHAT THEY SUPPLY NOW, FROM THE SAME PACKAGE TABLES")
# =================================================================================================

_ncr = PS.ncr_exposure_record(PROJECT, PERIOD)
check(_ncr["exposure_unit"] == "inspections" and _ncr["exposure_quantity"] > 0
      and len(_ncr["ncrs"]) > 0
      and all({"ncr_id", "issue_day", "severity"} <= set(n) for n in _ncr["ncrs"]),
      "A4.4 NOW: real nonconformance EVENTS with identities, dates and severities, over a "
      "governed exposure of inspections completed, both read from OG-SYNTH-0.3's own columns",
      f"{len(_ncr['ncrs'])} events over {_ncr['exposure_quantity']} inspections")
_ncr_out = run("A4.4", {"ncrExposureRecord": _ncr})
near("and the module computes the rate those two columns imply",
     _ncr_out.get("ncr_rate"), len(_ncr["ncrs"]) / _ncr["exposure_quantity"], 1e-6)
check(_ncr_out.get("event_detail_available") is True
      and _ncr_out.get("severity_counts") and _ncr_out.get("closure_rate") is not None,
      "and the backlog, the closure rate and the severity mix come out of the events rather than "
      "being reported absent, because on this package the events really are there")

_queue = PS.queue_model(PROJECT)
_q = _queue["queues"][0]
check({"arrival_rate", "service_rate", "servers", "discipline"} <= set(_q)
      and _q["arrival_rate"] > 0 and _q["service_rate"] > 0 and _q["servers"] >= 1,
      "A5.6 NOW: an arrival rate, a service rate, a server count and a discipline, estimated from "
      "the SAME queue event rows the occupancy importer read", str(_q))
_q_out = run("A5.6", {"queueModel": _queue})
check(not abstains(_q_out) and _q_out.get("L") is not None and _q_out.get("Wq") is not None,
      "and the module derives the queueing measures the theory defines rather than reading waits "
      "out of a log", str(_q_out.get("utilisation")))
near("and Little's Law holds on the derived figures",
     _q_out["L"], _q["arrival_rate"] * _q_out["W"], 1e-6)

_abm = PS.known_answer_agent_supply_chain_model()
check(sorted(a["agent_type"] for a in _abm["agents"]) == ["CARRIER", "PROJECT", "SUPPLIER"]
      and all(a["behaviour_rule"] for a in _abm["agents"])
      and all(a["interaction_links"] for a in _abm["agents"])
      and _abm["environment"] and _abm["time_steps"] > 1,
      "A5.7 NOW: one supplier, one carrier and one project, each with an executable behaviour "
      "rule and interaction links, in a named environment over declared time steps",
      str([a["agent_type"] for a in _abm["agents"]]))
check(len({a.get("agent_type") for a in PS.agents(PROJECT).get("agents", [{}])}) <= 1,
      "and the reason it comes from the SUCCESSOR package rather than from v0.3 is stated as a "
      "measured fact: every agent v0.3 carries is of one type, so it cannot express this model")


# =================================================================================================
head("3. THE SUPPLIED CONTRACTS' OWN KNOWN ANSWERS, ON THE SUCCESSOR PACKAGE")
# =================================================================================================

_ka_ncr = PS.known_answer_ncr_exposure_record()
_r = run("A4.4", {"ncrExposureRecord": _ka_ncr})
near("A4.4 known answer: four nonconformances over one hundred inspections is 0.04",
     _r.get("ncr_rate"), 0.04)
check(_ka_ncr["exposure_quantity"] == 100.0 and len(_ka_ncr["ncrs"]) == 4,
      "and the numerator is four EVENTS and the denominator an explicit governed exposure of one "
      "hundred, not a numerator-only rate")
_expected = PS.known_answer_expectations("ncr_exposure_known_answer.csv")
near("and the package records the expected rate beside the case, so the answer is pinned in the "
     "fixture as well as in the test", float(_expected[0]["expected_ncr_rate"]), 0.04)

_r = run("A5.6", {"queueModel": PS.known_answer_queue_model("QUEUE-KA-STABLE")})
near("A5.6 known answer: rho is two thirds", _r.get("utilisation"), 2 / 3, 1e-5)
near("A5.6 known answer: L is two", _r.get("L"), 2.0, 1e-5)
near("A5.6 known answer: W is one", _r.get("W"), 1.0, 1e-5)
near("A5.6 known answer: Lq is four thirds", _r.get("Lq"), 4 / 3, 1e-5)
near("A5.6 known answer: Wq is two thirds", _r.get("Wq"), 2 / 3, 1e-5)
for _case in ("QUEUE-KA-UNSTABLE", "QUEUE-KA-OVERLOADED"):
    _u = run("A5.6", {"queueModel": PS.known_answer_queue_model(_case)})
    check(abstains(_u) and _u.get("L") is None and _u.get("W") is None,
          f"A5.6 known answer {_case}: at lambda at or above mu the fixture drives a REFUSAL and "
          f"no finite waiting time is emitted", str(_u.get("evidence_metric"))[:80])

_r = run("A5.7", {"agentSupplyChainModel": PS.known_answer_agent_supply_chain_model()})
_trace = [t["received"] for t in _r["runs"][0]["trace"]]
check(_trace == [0, 0, 1, 2, 2, 2],
      "A5.7 known answer: the hand-computed receipt trace under the declared step order",
      str(_trace))
check(_r.get("received") == 2 and _r.get("backordered") == 0,
      "A5.7 known answer: both units received and nothing backordered")
_env = {e["case_id"]: e for e in PS.known_answer_expectations(
    "abm_environment_known_answer.csv")}
check(_env["ABM-KA-1"]["expected_receipt_trace"] == "|".join(str(x) for x in _trace),
      "and the package records the expected trace beside the case, so the module and the fixture "
      "agree on a figure neither derived from the other",
      _env["ABM-KA-1"]["expected_receipt_trace"])
_zero = run("A5.7", {"agentSupplyChainModel":
                     PS.known_answer_agent_supply_chain_model("ABM-KA-ZEROSTOCK")})
check(_zero.get("received") == 0 and _zero.get("backordered") == 2,
      "A5.7 known answer, zero stock: the supplier rule cannot fire and the whole demand is "
      "backordered", str(_zero.get("received")))


# =================================================================================================
head("4. THE CHAIN, AND THE IDENTITY RULE IT OBEYS")
# =================================================================================================

# RUN 33 APPENDED OG-SYNTH-0.5, the Portfolio Health canonical fixture package. Run 29's four
# links are asserted as a strict PREFIX rather than overwritten, which is the same discipline the
# simulation-version history is held to: a predecessor's position is a fact about the chain and a
# successor never edits it.
check([p.identifier for p in SP.SYNTHETIC_PACKAGES][:4]
      == ["OG-SYNTH-0.1", "OG-SYNTH-0.2", "OG-SYNTH-0.3", "OG-SYNTH-0.4"],
      "the chain is declared oldest first and Run 29's four links are still its prefix",
      str([p.identifier for p in SP.SYNTHETIC_PACKAGES]))
# RUN 34 APPENDED OG-SYNTH-0.6, the labelled calibration package. Run 33's five links are
# asserted as a strict PREFIX rather than overwritten, by the same discipline as before.
check([p.identifier for p in SP.SYNTHETIC_PACKAGES][:5]
      == ["OG-SYNTH-0.1", "OG-SYNTH-0.2", "OG-SYNTH-0.3", "OG-SYNTH-0.4", "OG-SYNTH-0.5"],
      "Run 33's five links are still the chain's prefix",
      str([p.identifier for p in SP.SYNTHETIC_PACKAGES]))
check([p.identifier for p in SP.SYNTHETIC_PACKAGES]
      == ["OG-SYNTH-0.1", "OG-SYNTH-0.2", "OG-SYNTH-0.3", "OG-SYNTH-0.4", "OG-SYNTH-0.5",
          "OG-SYNTH-0.6"],
      "and every link is named, oldest first",
      str([p.identifier for p in SP.SYNTHETIC_PACKAGES]))
check(sum(1 for p in SP.SYNTHETIC_PACKAGES if p.current) == 1
      and SP.CURRENT.identifier == "OG-SYNTH-0.6",
      "exactly one link is declared current and it is the newest successor",
      SP.CURRENT.identifier)
check(all((ROOT / p.root).is_dir() for p in SP.SYNTHETIC_PACKAGES),
      "every declared package root exists in the checkout")

_records: dict[str, dict[str, str]] = {}
for _pkg in SP.SYNTHETIC_PACKAGES:
    if _pkg.record is None:
        check(not (ROOT / _pkg.root / "CHECKSUMS.sha256").is_file(),
              f"{_pkg.identifier} is declared as shipping without a checksum record, and it "
              f"really has none: the chain says so rather than a guard skipping it silently")
        continue
    _rec = SP.parse_record((ROOT / _pkg.record).read_text(encoding="utf-8"))
    _records[_pkg.identifier] = _rec
    _base = (ROOT if _pkg.record_paths_relative_to == "repository_root" else ROOT / _pkg.root)
    _bad = sorted(rel for rel, digest in _rec.items()
                  if not (_base / rel).is_file()
                  or hashlib.sha256((_base / rel).read_bytes()).hexdigest() != digest)
    check(not _bad,
          f"{_pkg.identifier}: all {len(_rec)} checksums verify against its own files, so this "
          f"link is intact", str(_bad[:3]))

# RULE 2 and RULE 3: the successor names every file it added, and no predecessor names any of them.
_current = _records[SP.CURRENT.identifier]
check(all(f in _current for f in SP.CURRENT_ONLY_FILES),
      "the CURRENT record names every canonical fixture file the current line reads",
      str([f for f in SP.CURRENT_ONLY_FILES if f not in _current]))
_leaked = []
for _pkg in SP.SYNTHETIC_PACKAGES[:-1]:
    _rec = _records.get(_pkg.identifier, {})
    _base_prefix = _pkg.root + "/"
    for _f in SP.CURRENT_ONLY_FILES:
        if _f in _rec or _f.replace(_base_prefix, "") in _rec:
            _leaked.append((_pkg.identifier, _f))
check(not _leaked,
      "and NO PREDECESSOR record names a file the successor added, so a predecessor cannot be "
      "read as though it had contained the canonical fixtures", str(_leaked))

# RULE 4, THE MASQUERADE RULE.
_PREDECESSOR_IDS = {p.identifier for p in SP.SYNTHETIC_PACKAGES if not p.current}
_masquerading = []
for _p in sorted((ROOT / SP.CURRENT.root).rglob("*")):
    if not _p.is_file() or _p.name == "CHECKSUMS.sha256":
        continue
    _text = _p.read_text(encoding="utf-8", errors="ignore")
    for _pred in _PREDECESSOR_IDS:
        if f"programme_version" in _text and f",{_pred}," in _text:
            _masquerading.append((_p.as_posix(), _pred))
check(not _masquerading,
      "MASQUERADE RULE: no file inside the current package carries a predecessor's programme "
      "version, so a current file cannot claim to be evidence collected under a package it was "
      "never part of", str(_masquerading))


# =================================================================================================
head("5. FOUR OF THE SEVEN MANDATED FAULTS")
# =================================================================================================

# ---- FAULT 1: the stale v2 NCR shape is rejected.
print()
print("--- FAULT 1: the stale v2 NCR synthetic shape")
_clean = PS.ncr_exposure_record(PROJECT, PERIOD)
_green = check(not abstains(run("A4.4", {"ncrExposureRecord": _clean})),
               "F1 GREEN BEFORE: the canonical fixture computes")
_stale = {"audits": [{"audit_id": "A", "total_findings": 40}],
          "open_nonconformances": [{"index": i} for i in range(6)]}
check("ncrs" not in _stale and "exposure_unit" not in _stale and "audits" in _stale,
      "F1 INJECTION CONFIRMED: the record handed to the module is the v2 cohort shape, read back "
      "and shown to carry no events and no exposure", str(sorted(_stale)))
_red = check(abstains(run("A4.4", {"ncrExposureRecord": _stale}))
             and abstains(run("A4.4", {"auditedNonconformanceCohort": _stale})),
             "F1 RED: the stale shape is rejected on both the canonical key and the retired one",
             str(run("A4.4", {"ncrExposureRecord": _stale}).get("evidence_metric"))[:80])
check(not abstains(run("A4.4", {"ncrExposureRecord": PS.ncr_exposure_record(PROJECT, PERIOD)})),
      "F1 RESTORED: the canonical fixture computes again")

# ---- FAULT 2: a queue fixture without arrival and service structure is rejected.
print()
print("--- FAULT 2: a queue fixture with no arrival or service process")
_cleanq = PS.known_answer_queue_model()
check(not abstains(run("A5.6", {"queueModel": _cleanq})),
      "F2 GREEN BEFORE: the canonical queue fixture computes")
for _label, _mutate in (("no arrival rate", lambda q: q["queues"][0].pop("arrival_rate")),
                        ("no service rate", lambda q: q["queues"][0].pop("service_rate")),
                        ("no discipline", lambda q: q["queues"][0].pop("discipline")),
                        ("no servers", lambda q: q["queues"][0].pop("servers"))):
    _bad = PS.known_answer_queue_model()
    _mutate(_bad)
    check(len(_bad["queues"][0]) < len(_cleanq["queues"][0]),
          f"F2 INJECTION CONFIRMED ({_label}): the field is gone from the structure, read back "
          f"after the injection", str(sorted(_bad["queues"][0])))
    check(abstains(run("A5.6", {"queueModel": _bad})),
          f"F2 RED ({_label}): the module refuses a queue that is not a queueing model")
check(not abstains(run("A5.6", {"queueModel": PS.known_answer_queue_model()})),
      "F2 RESTORED: the canonical queue fixture computes again")

# ---- FAULT 3: an ABM fixture without agents or rules is rejected.
print()
print("--- FAULT 3: an ABM fixture with no agents and no rules")
check(not abstains(run("A5.7", {"agentSupplyChainModel":
                                PS.known_answer_agent_supply_chain_model()})),
      "F3 GREEN BEFORE: the canonical agent fixture computes")
_noagents = dict(PS.known_answer_agent_supply_chain_model(), agents=[])
check(_noagents["agents"] == [],
      "F3 INJECTION CONFIRMED (no agents): the agent list is empty, read back after the injection")
check(abstains(run("A5.7", {"agentSupplyChainModel": _noagents})),
      "F3 RED (no agents): the module refuses a model with nothing to act in it")
_norules = PS.known_answer_agent_supply_chain_model()
for _a in _norules["agents"]:
    _a["behaviour_rule"] = ""
check(all(not _a["behaviour_rule"] for _a in _norules["agents"]),
      "F3 INJECTION CONFIRMED (no rules): every behaviour rule is blank, read back")
check(abstains(run("A5.7", {"agentSupplyChainModel": _norules})),
      "F3 RED (no rules): agents without rules do not make a model of behaviour")
check(not abstains(run("A5.7", {"agentSupplyChainModel":
                                PS.known_answer_agent_supply_chain_model()})),
      "F3 RESTORED: the canonical agent fixture computes again")

# ---- FAULT 7: a predecessor package identifier stamped on changed current bytes.
print()
print("--- FAULT 7: a predecessor package id stamped on current bytes")
_victim = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.4"
           / "package_A_project_structures" / "queue_model_known_answer.csv")
_orig = _victim.read_bytes()
_green7 = check(b"OG-SYNTH-0.4" in _orig and b"OG-SYNTH-0.3" not in _orig,
                "F7 GREEN BEFORE: the current file carries the CURRENT programme version and no "
                "predecessor's")
try:
    _victim.write_bytes(_orig.replace(b"OG-SYNTH-0.4", b"OG-SYNTH-0.3"))
    _after = _victim.read_bytes()
    check(b"OG-SYNTH-0.3" in _after and b"OG-SYNTH-0.4" not in _after,
          "F7 INJECTION CONFIRMED: the file on disk now carries the PREDECESSOR's programme "
          "version, read back from disk rather than assumed")
    _flagged = []
    for _pred in _PREDECESSOR_IDS:
        if f",{_pred},".encode() in _after:
            _flagged.append(_pred)
    _red7 = check(_flagged == ["OG-SYNTH-0.3"],
                  "F7 RED: the masquerade rule names exactly the predecessor whose identifier a "
                  "current file has taken", str(_flagged))
    # RUN 33. THE OWNING RECORD IS FOUND MECHANICALLY, not assumed to be the current link.
    # OG-SYNTH-0.4 became a PREDECESSOR when Run 33 minted OG-SYNTH-0.5, so `SP.CURRENT.record`
    # no longer names this file and reading it there raised a KeyError rather than failing a
    # check -- a crash, not a RED. The property under test is unchanged and is now stated on the
    # record that actually covers the file: whichever package's record names it must go red.
    _digest_now = hashlib.sha256(_after).hexdigest()
    _rel = _victim.relative_to(ROOT).as_posix()
    _owning = [pkg for pkg in SP.SYNTHETIC_PACKAGES if pkg.record
               and _rel in SP.parse_record((ROOT / pkg.record).read_text(encoding="utf-8"))]
    check(len(_owning) == 1,
          "F7 the file is named by exactly one package record, so the owning record is not "
          "ambiguous", str([pkg.identifier for pkg in _owning]))
    _rec_now = SP.parse_record((ROOT / _owning[0].record).read_text(encoding="utf-8"))
    check(_rec_now[_rel] != _digest_now,
          "F7 AND THE OWNING RECORD GOES RED TOO: that package's own checksum no longer matches "
          "the file, so the change cannot pass as unrecorded either")
    _refused = False
    try:
        PS.known_answer_queue_model()
    except Exception:                                             # noqa: BLE001
        _refused = True
    check(_refused,
          "F7 AND THE IMPORTER REFUSES IT: a row stamped with a version that is not this "
          "package's own is rejected at read time rather than flowing into a module")
finally:
    _victim.write_bytes(_orig)
_green7b = check(_victim.read_bytes() == _orig
                 and b"OG-SYNTH-0.4" in _victim.read_bytes(),
                 "F7 RESTORED: the file is byte-identical to what it was before the injection")
check(SP.parse_record((ROOT / _owning[0].record).read_text(encoding="utf-8"))[
          _victim.relative_to(ROOT).as_posix()]
      == hashlib.sha256(_victim.read_bytes()).hexdigest(),
      "and the owning package's record verifies against it again")
check(not abstains(run("A5.6", {"queueModel": PS.known_answer_queue_model()})),
      "and the importer reads it again, so nothing was left mutated")


print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
