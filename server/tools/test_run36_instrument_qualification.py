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
check(_a11.get("__state__") == "COMPUTES", "A1.1 still computes on the controlled corpus",
      _a11.get("__state__"))
check(_a11.get("status_color") is None and _a11.get("band_asserted") is False
      and _a11.get("calibration_pending") is True,
      "and asserts NO BAND, explicitly, rather than falling silent",
      f"{_a11.get('status_color')!r}/{_a11.get('band_asserted')!r}/"
      f"{_a11.get('calibration_pending')!r}")
check(repr(_a11.get("overrun_pct_p80")) == "12.104441685525892",
      "and its FIGURE is the same one the v23 line produced, so only the colour moved",
      repr(_a11.get("overrun_pct_p80")))
# PRODUCTION CANNOT REACH THE PRESERVED LADDER. The function is kept as scientific history and
# must be unreachable, which is the historical-only precedent this programme uses.
_src = (ROOT / "server" / "app" / "simulation" / "models_sim.py").read_text(encoding="utf-8")
check(_src.count("mc_status(") == 1,
      "mc_status is PRESERVED but production cannot reach it: exactly one occurrence, its own "
      "definition, and no call site anywhere", str(_src.count("mc_status(")))
check(MS.mc_status(12.0) == "red" and MS.mc_status(7.0) == "amber" and MS.mc_status(1.0) == "green",
      "and the preserved ladder still behaves as it historically did, so the record is intact "
      "rather than gutted")
# THE STRUCTURE IS STILL DECLARED, STILL ACCEPTED, AND STILL UNCONSUMED. This is the residual
# blocking defect, and it is asserted POSITIVELY so it cannot be quietly forgotten.
check("costDriverDistributions" in governed_structure_keys(),
      "costDriverDistributions is still accepted by the governed intake")
_qual = load("run36_instrument_qualification.csv")
_instr = [r for r in _qual if r["row_type"] == "INSTRUMENT_BLOCKING_DEFECT"]
check(len(_instr) == 1 and _instr[0]["module_id"] == "A1.1",
      "and the instrument-qualification artefact carries exactly ONE instrument-level blocking "
      "defect row, naming A1.1", str([r["module_id"] for r in _instr]))
check(len([r for r in _committed if r["blocking_defect"] != "NO"]) == 0,
      "while the 100 TARGET rows carry no blocking defect, so the two are not conflated",
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
check(SIMULATION_VERSION == "sim-2026.08-v24", "the simulation stamp is sim-2026.08-v24",
      SIMULATION_VERSION)
check(SIMULATION_VERSION_HISTORY[-2:] == ("sim-2026.08-v23", "sim-2026.08-v24"),
      "and v24 directly follows v23 in an append-only history",
      str(SIMULATION_VERSION_HISTORY[-2:]))
check(PP.CURRENT.identifier == "og-participant-2026.08-v12",
      "the current participant package is v12", PP.CURRENT.identifier)
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
_blocking = len(_instr) + len([r for r in _committed if r["blocking_defect"] != "NO"])
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
check(_blocking == 1,
      "and Run 36's honest count is exactly ONE instrument-level blocking defect, so this run "
      "reports FREEZE_BLOCKED", str(_blocking))

# =================================================================================================
head("10b. SECTIONS 11 AND 17: ONE ENGINE PER IDENTITY, AND ALL 101 THROUGH THE REAL LOOKUP")
# =================================================================================================
import collections                                                # noqa: E402
_eng = collections.Counter()
for _m, _e in REG.VALIDATED.items():
    _fn = _e[1]
    _inner = getattr(_fn, "__wrapped__", _fn)   # functools.wraps hides identity from naive checks
    _eng[f"{_inner.__module__}.{_inner.__name__}"] += 1
_dups = {k: v for k, v in _eng.items() if v > 1}
check(not _dups,
      "no analytical engine is shared by two registered module identities, so no duplicate "
      "implementation was introduced. Read through __wrapped__, because functools.wraps masks "
      "route identity from naive introspection", str(_dups))
for _mid, _name in (("B2.18", "MARCOS"), ("B2.19", "CRITIC_TOPSIS")):
    _e = REG.VALIDATED.get(_mid)
    _inner = getattr(_e[1], "__wrapped__", _e[1]) if _e else None
    check(bool(_e) and _e[0] == _name and _eng[f"{_inner.__module__}.{_inner.__name__}"] == 1,
          f"{_mid} has ONE stable identity and ONE engine", str(_e[0]) if _e else "missing")
_lookup_bad = []
for _m in _idx:
    try:
        REG.method_label(_m)
        REG.group_of(_m)
        REG.parameter_provenance(_m)
    except Exception as _exc:                                     # noqa: BLE001
        _lookup_bad.append((_m, f"{type(_exc).__name__}"))
check(not _lookup_bad and len(_idx) == 101,
      "all 101 registered modules resolve through the real lookup paths with no silent undefined "
      "and no recursion", str(_lookup_bad))

# =================================================================================================
head("11. SECTION 18: THE AUTHENTICATED BROWSER QUALIFICATION ARTEFACT")
# =================================================================================================
_bq = load("run36_authenticated_browser_qualification.csv")
check(bool(_bq), "the authenticated browser qualification artefact exists", len(_bq))
_bfail = [r for r in _bq if r["result"] == "FAIL"]
check(not _bfail, "no participant surface FAILED in the real browser",
      str([r["surface"] for r in _bfail]))
_bnv = [r for r in _bq if r["result"] == "NOT_VERIFIED"]
check(all(r["surface_reached"] == "NO" for r in _bnv),
      "and any NOT_VERIFIED row really did fail to REACH its surface, so it is a recorded "
      "limitation rather than a quiet pass", str([r["surface"] for r in _bnv]))
for _need in ("participant authentication", "preliminary judgment lock", "AI reveal",
              "final lock", "next-period transition", "evidence and rationale capture",
              "no JavaScript console crash"):
    _hit = [r for r in _bq if r["surface"] == _need]
    check(bool(_hit) and all(r["result"] == "PASS" for r in _hit),
          f"the study path surface '{_need}' was reached and passed; an unreachable study path "
          f"would itself be a blocking defect",
          str([(r["result"], r["surface_reached"]) for r in _hit]))

# =================================================================================================
head("11b. SECTION 15: PARSIMONY, AND THE DISCREPANCY IT REPORTS")
# =================================================================================================
_pars = load("run36_parsimony_reconciliation.csv")
_ptargets = [r for r in _pars if r["row_type"] == "TARGET"]
check(len(_ptargets) == 100 and {r["module_id"] for r in _ptargets} == _scientific,
      "the parsimony reconciliation covers exactly the 100 scientific targets",
      f"{len(_ptargets)} rows")
_OVERLAP = {"NONE", "SHARED_GOVERNED_STRUCTURE (same primitive source object)",
            "IDENTICAL_PRIMITIVE_SOURCE_SET", "PRIMITIVE_SOURCE_SUBSET"}
check({r["overlap_type"] for r in _ptargets} <= _OVERLAP,
      "and every overlap value is one Run 35 established; the vocabulary was not extended",
      str({r["overlap_type"] for r in _ptargets} - _OVERLAP))
_disc = [r for r in _pars if r["row_type"] == "REPORTED_DISCREPANCY"]
check(len(_disc) == 1 and "22" in _disc[0]["current_operational_necessity"],
      "and the disagreement with Run 35's figure of 22 is REPORTED as a discrepancy rather than "
      "reconciled away or padded to match", str(len(_disc)))

# =================================================================================================
head("12. SECTION 21: THE REPRODUCIBILITY INVENTORY, AND THE HISTORICAL INCOMPLETENESS")
# =================================================================================================
_repro = load("run36_reproducibility_inventory.csv")
check(bool(_repro), "the reproducibility inventory exists", len(_repro))
check(not [r for r in _repro if r["sha256"] == "MISSING"],
      "every freeze-candidate component named in the inventory is present",
      str([r["role"] for r in _repro if r["sha256"] == "MISSING"]))
import hashlib as _hl                                             # noqa: E402
_drift = [r["file_path"] for r in _repro
          if r["sha256"] not in ("MISSING", "directory")
          and _hl.sha256((ROOT / r["file_path"]).read_bytes()).hexdigest() != r["sha256"]]
check(not _drift, "and every recorded checksum still matches the file on disk", str(_drift))
_synth01 = [r for r in _repro if "OG-SYNTH-0.1" in r["file_path"]]
check(len(_synth01) == 1 and "HISTORICALLY INCOMPLETE" in _synth01[0]["reproducibility_status"]
      and "504" in _synth01[0]["reproducibility_status"],
      "OG-SYNTH-0.1's historical incompleteness stays VISIBLE: 519 manifest entries against 504 "
      "recovered, and no completeness is claimed for it",
      str(_synth01)[:200])

print()
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
raise SystemExit(1 if FAILED else 0)
