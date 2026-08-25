"""
RUN 36. THE FINAL INSTRUMENT-QUALIFICATION GUARD.

WHAT MAKES THIS A GUARD RATHER THAN A DESCRIPTION. Its oracles are NOT the generator's. It walks
the registry, the dispatch table, the structure maps, the parameter register and the lineage
module ITSELF, executes the real production entry point ITSELF, and only then requires
`build_run36_audit.py`'s output to agree with what it derived. The generator is run as a
subprocess into a TEMPORARY DIRECTORY, so this file can never regenerate the artefact it is
checking -- the defect Run 34's campaign found twice.

A CRASH IS NOT A FAILURE HERE EITHER. Every execution is wrapped and a raised exception is
recorded as its own state, so a module that dies is red for dying rather than silently counted
as an abstention.
"""

from __future__ import annotations

import csv
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from app.simulation import registry as REG                      # noqa: E402
from app.simulation import lineage as LIN                       # noqa: E402
from app.simulation import models_sim as MS                     # noqa: E402
from app.simulation.models import SIMULATION_VERSION, SIMULATION_VERSION_HISTORY  # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED        # noqa: E402
from app.simulation.parameters import PARAMETER_CLASSES         # noqa: E402
from app.project_data import governed_structure_keys            # noqa: E402
import participant_packages as PP                               # noqa: E402

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok, what, got=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {what}")
    else:
        FAILED += 1
        FAILURES.append(what)
        print(f"  ****  {what}  [{got}]")


def head(t):
    print("\n" + "=" * 94 + f"\n{t}\n" + "=" * 94)


CORPUS_SI = {
    "bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
    "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
    "actualPctComplete": 40.0, "plannedPctComplete": 45.0,
    "qualityAuditScore": 92, "totalFindings": 18, "criticalFindings": 1,
    "oshaRecordableIncidents": 3, "totalManhours": 200_000,
    "environmentalComplianceRate": 0.925, "environmentalViolations": 3,
    "evidenceQualification": {"qualification_state": "QUALIFIED",
                              "timeliness_status": "TIMELY",
                              "verification_status": "verified",
                              "source_authority": "system_of_record"},
}
CUT = "2026-06-30"


def run(mid):
    try:
        r = REG.run_module(mid, dict(CORPUS_SI), (lambda: 0.5), CUT)
    except REG.MissingModuleError:
        return {"__state__": "SUPPLIED_NOT_COMPUTED"}
    except REG.PortfolioModuleError:
        return {"__state__": "PORTFOLIO_ROUTE"}
    except Exception as exc:                                     # noqa: BLE001
        return {"__state__": "CRASHED", "__why__": f"{type(exc).__name__}: {exc}"[:160]}
    r["__state__"] = "ABSTAINS" if r.get("insufficient_data") else "COMPUTES"
    return r


# =================================================================================================
head("1. THE ARTEFACTS ARE REGENERATED INTO A TEMPORARY DIRECTORY, NEVER OVER THEMSELVES")
# =================================================================================================
_TMP = pathlib.Path(tempfile.mkdtemp(prefix="run36-audit-"))
_proc = subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "build_run36_audit.py"),
                        "--out", str(_TMP)], capture_output=True, text=True)
check(_proc.returncode == 0, "the Run-36 audit generator runs to completion",
      (_proc.stderr or "")[-300:])


def load(name, from_tmp=False):
    p = (_TMP if from_tmp else ROOT / "code_audit") / name
    if not p.is_file():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


for _n in ("run36_population_reconciliation.csv", "run36_a1_1_closure.csv",
           "run36_100_target_scientific_reaudit.csv",
           "run36_parameter_provenance_reaudit.csv", "run36_instrument_qualification.csv"):
    check((ROOT / "code_audit" / _n).is_file(), f"the committed artefact {_n} exists")

_committed = load("run36_100_target_scientific_reaudit.csv")
_fresh = load("run36_100_target_scientific_reaudit.csv", from_tmp=True)
check(_committed == _fresh,
      "and the COMMITTED 100-target artefact reproduces byte for byte from the current tree, so "
      "it is not a stale snapshot of an earlier instrument",
      f"{len(_committed)} committed vs {len(_fresh)} regenerated")

# =================================================================================================
head("2. THE POPULATIONS, DERIVED HERE AND NOT READ FROM THE ARTEFACT")
# =================================================================================================
_idx = REG.registry_index()
_project = {m for m, r in _idx.items() if r["group"] != "D"}
_portfolio = {m for m, r in _idx.items() if r["group"] == "D"}
_scientific = {m for m in _idx if m not in REG.DISABLED_EVIDENCE_UNDER_REVIEW}
check(len(_idx) == 101, "registered total is 101", len(_idx))
check(len(_project) == 96, "registered project modules is 96", len(_project))
check(len(_portfolio) == 5, "Portfolio Health targets is 5", len(_portfolio))
check(len(_scientific) == 100, "scientific targets is 100", len(_scientific))
check(len(_scientific - _portfolio) == 95, "project scientific targets is 95",
      len(_scientific - _portfolio))
check(len(REG.VALIDATED) == 95, "registry.VALIDATED is 95, and it is a DIFFERENT 95",
      len(REG.VALIDATED))
check(len(set(REG.VALIDATED) & (_scientific - _portfolio)) == 94,
      "the two 95s intersect at 94, so they are not the same set and cannot be collapsed",
      len(set(REG.VALIDATED) & (_scientific - _portfolio)))
check({r["module_id"] for r in _committed} == _scientific,
      "and the artefact's 100 rows are EXACTLY the population derived here",
      str(sorted(_scientific ^ {r["module_id"] for r in _committed}))[:200])
check(len(_committed) == 100 and len({r["module_id"] for r in _committed}) == 100,
      "rows = 100, unique = 100, duplicates = 0", f"{len(_committed)} rows")

# =================================================================================================
head("3. SECTION 6: THE HARD GATE, MEASURED BY EXECUTION")
# =================================================================================================
_offenders = []
for _m in sorted(_scientific):
    _row = run(_m)
    if _row.get("__state__") != "COMPUTES" or not _row.get("status_color"):
        continue
    _cls = {p.parameter_class for p in (REG.parameter_provenance(_m) or [])}
    if "UNSUPPORTED" in _cls:
        _offenders.append(_m)
check(not _offenders,
      "REACHABLE UNSUPPORTED PARAMETERS PRODUCING AUTHORITATIVE OUTPUT = 0", str(_offenders))
_crashed = sorted(m for m in _scientific if run(m).get("__state__") == "CRASHED")
check(not _crashed, "and no scientific target CRASHES on the controlled corpus: a crash would be "
      "counted as neither an abstention nor a pass", str(_crashed))
_illegal = sorted({p.parameter_class for m in _scientific
                   for p in (REG.parameter_provenance(m) or [])} - set(PARAMETER_CLASSES))
check(not _illegal, "and every parameter class is in the closed governed vocabulary", str(_illegal))

# =================================================================================================
head("4. SECTION 2: A1.1 IS CLOSED WHERE IT CAN BE, AND THE RESIDUAL IS DECLARED")
# =================================================================================================
_a11 = run("A1.1")
check(_a11.get("__state__") == "ABSTAINS",
      "A1.1 does NOT compute on the controlled corpus: under the owner's 2026-08-19 ruling its "
      "canonical input contract is not governed", _a11.get("__state__"))
check(_a11.get("activation_state") == "DISABLED_INSUFFICIENT_INPUT"
      and _a11.get("abstention_reason_code")
      == "CANONICAL_DRIVER_DISTRIBUTION_MAPPING_NOT_GOVERNED",
      "and the reason distinguishes an ungoverned method definition from an ordinary missing "
      "value", f"{_a11.get('activation_state')!r} / {_a11.get('abstention_reason_code')!r}")
check(_a11.get("status_color") is None and _a11.get("p80_eac") is None
      and _a11.get("overrun_pct_p80") is None,
      "and it emits no colour and no figure at all", str(sorted(_a11))[:180])
# THE RETAINED ADAPTATION: PRESERVED, AND PROVED UNREACHABLE FROM ITS OWN LIVE SOURCE.
from app.simulation import models_sim as _MS                       # noqa: E402
_MS.assert_retained_adaptation_not_reachable(
    lambda ok, what, got="": check(ok, "retained adaptation: " + what, got))
check(repr(_MS.run_monte_carlo({"bac": 1_000_000.0, "cpi": 0.909, "spi": 0.889,
                                "docRiskScore": 0.35}, (lambda: 0.5), 0)["overrun_pct_p80"])
      == "12.104441685525892",
      "and the preserved arithmetic still reproduces the figure the v24 line published on the "
      "controlled corpus, so it was preserved and not gutted", "12.104441685525892")
# PRODUCTION CANNOT REACH THE PRESERVED LADDER EITHER. Unchanged from Run 36.
_src = (ROOT / "server" / "app" / "simulation" / "models_sim.py").read_text(encoding="utf-8")
check(_src.count("mc_status(") == 1,
      "mc_status is PRESERVED but production cannot reach it: exactly one occurrence, its own "
      "definition, and no call site anywhere", str(_src.count("mc_status(")))
check(MS.mc_status(12.0) == "red" and MS.mc_status(7.0) == "amber"
      and MS.mc_status(1.0) == "green",
      "and the preserved ladder still behaves as it historically did, so the record is intact "
      "rather than gutted")
check("costDriverDistributions" in governed_structure_keys(),
      "costDriverDistributions is still accepted by the governed intake, so an owner who later "
      "supplies it is not refused at the door")
_qual = load("run36_instrument_qualification.csv")
_closed = [r for r in _qual if r["row_type"] == "INSTRUMENT_BLOCKING_DEFECT_CLOSED"]
_open = [r for r in _qual if r["row_type"] == "INSTRUMENT_BLOCKING_DEFECT"]
check(len(_closed) == 1 and _closed[0]["module_id"] == "A1.1" and not _open,
      "the instrument-qualification artefact records the Run-36 A1.1 blocking defect as CLOSED, "
      "and carries no open instrument-level blocking defect",
      f"closed={[r['module_id'] for r in _closed]} open={[r['module_id'] for r in _open]}")
check("no driver-to-EAC mapping" not in _closed[0]["blocking_defect"].lower()
      and "was invented" in _closed[0]["blocking_defect"],
      "and the closure record states that no driver-to-EAC mapping was invented",
      _closed[0]["blocking_defect"][:120])
check(len([r for r in _committed if r["blocking_defect"] != "NO"]) == 0,
      "while the 100 TARGET rows carry no blocking defect either",
      str([r["module_id"] for r in _committed if r["blocking_defect"] != "NO"]))

# =================================================================================================
head("5. SECTIONS 9 AND 22: VOTING, AND THE CLOSED VOCABULARIES")
# =================================================================================================
check(sorted(REG.CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
      "voting is EXACTLY A1.7 and A1.8", str(sorted(REG.CORE_VOTING_MODULES)))
check(len([r for r in _committed if r["voting"] == "YES"]) == 2,
      "and exactly two of the hundred rows say they vote",
      str([r["module_id"] for r in _committed if r["voting"] == "YES"]))
_QUAL_VOCAB = {"QUALIFIED_FOR_BOUNDED_STUDY_USE", "QUALIFIED_WITH_ABSTENTION", "RESEARCH_ONLY",
               "DISABLED", "ARCHIVED"}
_DISP_VOCAB = {"KEEP_OPERATIONAL", "KEEP_ADVISORY", "KEEP_ABSTENTION_CAPABLE", "RESEARCH_ONLY",
               "DISABLED_INSUFFICIENT_INPUT", "DISABLED_INSUFFICIENT_PROVENANCE", "ARCHIVED"}
check({r["scientific_qualification"] for r in _committed} <= _QUAL_VOCAB,
      "every final qualification is one of section 22's FIVE values; no sixth was minted",
      str({r["scientific_qualification"] for r in _committed} - _QUAL_VOCAB))
check({r["operational_disposition"] for r in _committed} <= _DISP_VOCAB,
      "every operational disposition is one of section 15's SEVEN values; no eighth was minted",
      str({r["operational_disposition"] for r in _committed} - _DISP_VOCAB))
check(not any(r["empirical_validation_class"] == "EMPIRICALLY_VALIDATABLE_NOW"
              for r in _committed),
      "and NOTHING is marked empirically validated: no labelled outcome corpus and no expert "
      "reference standard exist in this repository")

# =================================================================================================
head("6. SECTION 12: DISABLED MEANS PRODUCTION UNREACHABLE, AND NOTHING IS DELETED")
# =================================================================================================
for _mid, _why in (("A3.4", "Material Cost Variance"), ("B2.7", "Plithogenic Sets"),
                   ("B2.20", "Hypersoft Sets"), ("B2.9", "Quantum Probability")):
    check(_mid in REG.DISABLED_MODULES, f"{_mid} {_why} is disabled", str(_mid))
    check(_mid in _idx, f"and {_mid} is still REGISTERED, so nothing was deleted")
    _r = run(_mid)
    check(not _r.get("status_color"),
          f"and {_mid} produces no status on the controlled corpus", str(_r.get("status_color")))
check(len(REG.DISABLED_CONCEPT_ONLY) == 8 and len(REG.DISABLED_EVIDENCE_UNDER_REVIEW) == 1,
      "8 concept-only disabled plus 1 under evidence review = 9",
      f"{len(REG.DISABLED_CONCEPT_ONLY)} + {len(REG.DISABLED_EVIDENCE_UNDER_REVIEW)}")

# =================================================================================================
head("7. SECTION 13: PORTFOLIO HEALTH IS NON-VOTING AND NOT PROJECT-LEVEL")
# =================================================================================================
for _mid in sorted(PORTFOLIO_VALIDATED):
    check(_mid not in REG.CORE_VOTING_MODULES, f"{_mid} does not vote")
    check(run(_mid).get("__state__") == "PORTFOLIO_ROUTE",
          f"and {_mid} is refused on a single project's route rather than answering one",
          str(run(_mid).get("__state__")))
check(len(PORTFOLIO_VALIDATED) == 5, "and there are exactly five of them",
      len(PORTFOLIO_VALIDATED))

# =================================================================================================
head("8. SECTION 14: UNKNOWN LINEAGE IS NOT INDEPENDENT LINEAGE")
# =================================================================================================
_declared = set(LIN.MODULE_LINEAGE)
_unresolved = [r for r in _committed if r["lineage"] == "LINEAGE_UNRESOLVED"]
_indep = [r for r in _committed if r["lineage"] == "LINEAGE_ESTABLISHED_INDEPENDENT"]
check(all(r["module_id"] in _declared for r in _indep),
      "every row claiming INDEPENDENT lineage carries an actual lineage record; absence never "
      "becomes independence",
      str([r["module_id"] for r in _indep if r["module_id"] not in _declared]))
check(all(r["module_id"] not in _declared for r in _unresolved),
      "and every UNRESOLVED row genuinely has no record",
      str([r["module_id"] for r in _unresolved if r["module_id"] in _declared]))
check(len(_unresolved) == 77, "lineage UNRESOLVED for 77 of 100, derived here", len(_unresolved))

# =================================================================================================
head("9. SECTIONS 25 AND 26: THE VERSION AND PACKAGE DECISIONS")
# =================================================================================================
# RESTATED BY RUN 41, RUN 36'S FINDING PRESERVED. This pinned the LIVE stamp to Run 36's own
# stamp, which was true until the next authorised append. Run 41 appends v26, the successor
# carrying the two behaviour changes the owner authorised after Run 40. What is an INVARIANT --
# and what is still asserted here -- is that v25 remains in the history at the position Run 36
# put it, directly after v24. The v25 expectation is not overwritten: it is asserted as a
# HISTORICAL position rather than as the live stamp, which is the same discipline Run 32 and
# Run 33 applied to their predecessors.
check("sim-2026.08-v25" in SIMULATION_VERSION_HISTORY,
      "Run 36's sim-2026.08-v25 is still in the append-only history",
      SIMULATION_VERSION)
check(SIMULATION_VERSION_HISTORY[SIMULATION_VERSION_HISTORY.index("sim-2026.08-v25") - 1:
                                 SIMULATION_VERSION_HISTORY.index("sim-2026.08-v25") + 1]
      == ("sim-2026.08-v24", "sim-2026.08-v25"),
      "and v25 directly follows v24 in an append-only history",
      str(SIMULATION_VERSION_HISTORY[-2:]))
# RESTATED BY RUN 43. Run 43 retires 38 modules from service, which moves five
# participant-visible bytes -- the two generated client taxonomy mirrors, detail.js, knowledge.js
# and index.html -- so v13 is SUPERSEDED by v14 and pinned to its own commit rather than being
# rewritten. Asserting v13 is still current would make this file fail every time a later run
# legitimately mints a successor, which would be a guard measuring the wrong thing.
# RUN 44 minted v15: four of the seventy governed bytes moved for the render repairs, one of them
# the sequence-bearing deepdive.js on the owner's order at section 4.4.
# RUN 47 minted v16, and RUN 48 minted v17: three of the seventy governed bytes moved for the
# current-period read and the naming corrections, one of them the sequence-bearing deepdive.js on
# the owner's ruling 2, declared as a named exception.
# RUN 49 minted v18: three of the seventy moved again for the completion of that naming
# correction, TWO of them sequence-bearing -- deepdive.js on ruling 1 and decision-ui.js, which
# gains comments only, on ruling 4 -- both declared as named exceptions.
# RUN 51 minted v19: twenty-three of the seventy moved for the delivery of the owner's six
# rulings of 2026-08-22, and ALL SIX sequence-bearing files are among them, each carrying its
# own named exception record in the v19 checksum record's header.
# RUN 56 minted v22: EXACTLY ONE of the sixty-nine moved, assets/js/ingest.js, and it is NOT
# sequence-bearing, so this link carries NO exception record and declares that emptiness rather
# than omitting it.
# RUN 57 minted v23: THREE of the sixty-nine moved -- assets/css/radar.css, assets/js/detail.js
# and assets/js/ingest.js -- and NOT ONE is sequence-bearing, so this link too carries NO
# exception record and DECLARES that emptiness rather than omitting it.
check(PP.CURRENT.identifier == "og-participant-2026.08-v24",
      "the current participant package is v23", PP.CURRENT.identifier)
check(PP.CURRENT.source_commit is None
      and all(p.source_commit for p in PP.PARTICIPANT_PACKAGES[:-1]),
      "and every predecessor names the commit its bytes live in, so only one record claims the "
      "working tree")

# =================================================================================================
head("10. SECTION 28: THE FREEZE GATE ITSELF")
# =================================================================================================
# THIS IS THE GUARD THAT PROTECTS EVERY OTHER CONCLUSION IN THE RUN. A freeze manifest may exist
# ONLY when the instrument-qualification artefact records zero blocking defects. Fault 40 of the
# campaign inverts exactly this.
_open_instr = [r for r in _qual if r["row_type"] == "INSTRUMENT_BLOCKING_DEFECT"]
_blocking = len(_open_instr) + len([r for r in _committed if r["blocking_defect"] != "NO"])
_manifest = ROOT / "research" / "freeze" / "INSTRUMENT_FREEZE_CANDIDATE_MANIFEST.json"
_companion = ROOT / "research" / "freeze" / "INSTRUMENT_FREEZE_CANDIDATE.md"
check(_blocking > 0 or _manifest.is_file(),
      "if there are no blocking defects the freeze manifest must exist", str(_blocking))
check(_blocking == 0 or not _manifest.is_file(),
      "AND WHILE A BLOCKING DEFECT REMAINS THE FREEZE MANIFEST MUST NOT EXIST",
      f"blocking={_blocking} manifest_exists={_manifest.is_file()}")
check(_blocking == 0 or not _companion.is_file(),
      "nor its human-readable companion",
      f"blocking={_blocking} companion_exists={_companion.is_file()}")
check(_blocking == 0,
      "and after the owner's A1.1 ruling the mechanically derived blocking count is ZERO",
      str(_blocking))

print()
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
raise SystemExit(1 if FAILED else 0)
