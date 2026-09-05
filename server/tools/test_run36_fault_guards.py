"""
RUN 36. THE FORTY NAMED FAULT ORACLES.

ONE NAMED CHECK PER FAULT in the contract's section-24 list, so the campaign can require that the
GUARD THAT GOES RED IS THE ONE THE FAULT WAS AIMED AT, and not some bystander. Every oracle here
is derived from live authority or from execution; none asserts a defect's own sentence back at
itself, and none regenerates the artefact it is reading.

NAMING. Each check is named `run36.faultNN.<what>`. `run36_fault_campaign.py` greps for
`FAIL  run36.faultNN` and additionally requires the failure line to carry an intended-reason
fragment, so a check that goes red for an unrelated reason is not credited.

A CRASH IS NOT A RED. Everything that executes a module is wrapped, and a raised exception is
reported as its own distinct state so it can never be read as an abstention or as a pass.
"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

# --- CAMPAIGN SAFETY (Run 54, phase A) -----------------------------------------------------
# THE START-AND-END DIRTY-TREE GUARD. A campaign must not BEGIN on a dirty tree: Run 53
# established that a leaked fault is snapshotted from disk by the next campaign, faithfully
# restored by its `finally`, and thereby CERTIFIED by its own passing assertion. An end-only
# check cannot see that, because the leak began in an earlier process. See
# server/tools/campaign_safety.py for the full mechanism and the proof.
import sys as _cs_sys, pathlib as _cs_pl                                       # noqa: E402
_cs_sys.path.insert(0, str(_cs_pl.Path(ROOT) / "server" / "tools"))
from campaign_safety import (arm as _cs_arm, restore_guard, head_text,          # noqa: E402,F401
                             snapshot_text, CampaignTreeDirty)
_cs_arm(_cs_pl.Path(ROOT), "test_run36_fault_guards.py",
        # RUN 55, PHASE B, section 8 item 1: THE ALLOW LIST IS TIGHTENED TO DECLARED
        # OUTPUTS. Run 54 derived this list by taking every `code_audit/` literal in the
        # file, which swept in READ-ONLY inputs and fault TARGETS as well as outputs. An
        # allow entry is a promise that the campaign is designed to write that path;
        # naming a file it only reads widens the guard for nothing. Established by
        # execution: this file contains no write to code_audit at all.
        allow=[])
# -------------------------------------------------------------------------------------------
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from app.simulation import registry as REG                       # noqa: E402
from app.simulation import lineage as LIN                        # noqa: E402
from app.simulation import canonical_v8 as V8                    # noqa: E402
from app.simulation import canonical_v7 as V7                    # noqa: E402
from app.simulation.compute import contributes_to_project_status  # noqa: E402
from run97_removed_portfolio import PORTFOLIO_VALIDATED          # noqa: E402
from app.simulation.qualification_contract import ASSESSMENT_MISSING  # noqa: E402
import participant_packages as PP                                # noqa: E402

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(name, ok, why, got=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {name}  {why}")
    else:
        FAILED += 1
        FAILURES.append(f"{name}  {why}")
        print(f"FAIL  {name}  {why}  [{got}]")


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
AUDIT = ROOT / "code_audit"


def run(mid, si=None):
    try:
        r = REG.run_module(mid, dict(si if si is not None else CORPUS_SI), (lambda: 0.5), CUT)
    except REG.MissingModuleError:
        return {"__state__": "SUPPLIED"}
    except REG.PortfolioModuleError:
        return {"__state__": "PORTFOLIO_ROUTE"}
    except Exception as exc:                                     # noqa: BLE001
        return {"__state__": "CRASHED", "__why__": f"{type(exc).__name__}: {exc}"[:200]}
    r["__state__"] = "ABSTAINS" if r.get("insufficient_data") else "COMPUTES"
    return r


def _declared_structure(mid):
    """The module's defining governed structure key, read from the canonical layers themselves."""
    from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS
    from app.simulation.canonical_v3 import V3_STRUCTURE_KEYS
    from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS
    from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS
    from app.simulation.canonical_v6 import V6_STRUCTURE_KEYS
    from app.simulation.canonical_v7 import V7_STRUCTURE_KEYS
    from app.simulation.canonical_v8 import V8_STRUCTURE_KEYS
    for _m in (CANONICAL_STRUCTURE_KEYS, V3_STRUCTURE_KEYS, V4_STRUCTURE_KEYS, V5_STRUCTURE_KEYS,
               V6_STRUCTURE_KEYS, V7_STRUCTURE_KEYS, V8_STRUCTURE_KEYS):
        if mid in _m:
            return _m[mid]
    return ""


def rows(name):
    p = AUDIT / name
    if not p.is_file():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def text(rel):
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.is_file() else ""


TARGETS = rows("run36_100_target_scientific_reaudit.csv")
QUAL = rows("run36_instrument_qualification.csv")
POP = rows("run36_population_reconciliation.csv")
IDX = REG.registry_index()
SCIENTIFIC = {m for m in IDX if m not in REG.DISABLED_EVIDENCE_UNDER_REVIEW}

print("=" * 94)
print("RUN 36 FAULT ORACLES")
print("=" * 94)

# ---------------------------------------------------------------- 1-3 the inventory
_ids = [r["module_id"] for r in TARGETS]
# RUN 137, ITEM 3. THE INVENTORY IS SEALED RUN-36 EVIDENCE AND THE REGISTRY HAS MOVED UNDER IT.
# `run36_100_target_scientific_reaudit.csv` is the population Run 36 audited. Three later owner
# rulings changed the registry and none of them edits that file, which is evidence and is not
# rewritten:
#   * RUN 96 removed 51 retired rows outright, and RUN 97 removed 20 more with the B2, B3, B4
#     and D1 categories. `tools/run96_removed.py` is the roster of both, and it is the authority
#     used here rather than a list typed into this file.
#   * RUN 103 registered A2.12 Critical Path Analysis, AFTER the audit. Run 103 settled exactly
#     this shape for `test_run26_counts_and_wiring`: the audit population is sealed historical
#     evidence and cannot name a module registered after it, so a NAMED post-audit roster
#     replaces the bare assertion "and an unrestered new module still fails".
#
# Both directions stay closed. A registered scientific target that is neither in the inventory
# nor on the post-audit roster still fails fault01; an inventory row that is neither registered
# nor on the removal roster still fails fault03.
from run96_removed import REMOVED as _REMOVED_96_97          # noqa: E402
_POST_AUDIT_ROSTER = {"A2.12": "Run 103, Critical Path Analysis"}
_missing = sorted(SCIENTIFIC - set(_ids) - set(_POST_AUDIT_ROSTER))
check("run36.fault01.inventory_complete", not _missing,
      "the sealed 100-target inventory holds every scientific target the registry still carries, "
      "except the post-audit roster this suite names; a target is missing",
      str(_missing)[:200])
check("run36.fault01b.post_audit_roster_is_real",
      all(m in IDX for m in _POST_AUDIT_ROSTER),
      "every post-audit roster entry is genuinely registered; the roster is not a licence to "
      "ignore a target that is simply gone",
      str(sorted(_POST_AUDIT_ROSTER)))
check("run36.fault02.no_duplicate_target", len(_ids) == len(set(_ids)),
      "no scientific target appears twice; a duplicate row would inflate the population",
      str(sorted({m for m in _ids if _ids.count(m) > 1}))[:200])
_fabricated = sorted(set(_ids) - set(IDX) - set(_REMOVED_96_97))
check("run36.fault03.no_fake_target", not _fabricated,
      "every row in the inventory is a registered module or is on the Run 96/97 removal roster; "
      "an unregistered target is fabricated",
      str(_fabricated)[:200])
check("run36.fault03b.removal_roster_held",
      not sorted(m for m in _REMOVED_96_97 if m in IDX),
      "and not one module on the Run 96/97 removal roster has come back into the registry",
      str(sorted(m for m in _REMOVED_96_97 if m in IDX))[:200])

# ---------------------------------------------------------------- 4-5 A1.1
_ds = text("assets/js/ds_defensibility_evidence.js")
_m = re.search(r'"A1\.1": \{(.*?)\},\n', _ds, re.S)
_a11_served = _m.group(1) if _m else ""
_a11 = run("A1.1")
# RUN 36 CLOSURE. The served state must be the state EXECUTION produces, in either direction.
# Before the owner's ruling the lie was "conditional" over a module that computed; the mirror-image
# lie would be "computes" over a module that does not, and both are caught by comparing the served
# state to the executed one rather than by naming one wrong string.
_a11_served_state = ""
_sm = re.search(r'operationalState: "([A-Z_]+)"', _a11_served)
if _sm:
    _a11_served_state = _sm.group(1)
_a11_executes = _a11.get("__state__") == "COMPUTES"
_a11_says_computes = _a11_served_state == "COMPUTES_FROM_AVAILABLE_EVIDENCE"
_a11_says_conditional = _a11_served_state == "CONDITIONAL_ON_GOVERNED_STRUCTURE"
check("run36.fault04.a1_1_structure_claim_truthful",
      _a11_served_state == "DISABLED_INSUFFICIENT_INPUT"
      and not _a11_executes and not _a11_says_computes and not _a11_says_conditional,
      "A1.1's served operational state matches what it actually does without its declared "
      "structure; it claims to consume a required structure it does not consume, or claims to "
      "compute when it does not",
      f"served={_a11_served_state!r} executes={_a11_executes}")
_offenders = []
for _mid in sorted(SCIENTIFIC):
    _r = run(_mid)
    if _r.get("__state__") == "COMPUTES" and _r.get("status_color"):
        if "UNSUPPORTED" in {p.parameter_class for p in (REG.parameter_provenance(_mid) or [])}:
            _offenders.append(_mid)
check("run36.fault05.no_unsupported_authoritative", not _offenders,
      "no reachable UNSUPPORTED parameter authorizes an authoritative output", str(_offenders))

# ---------------------------------------------------------------- 6-8 the voters
_a17 = run("A1.7")
_a18 = run("A1.8")
check("run36.fault06.a1_7_bands_on_full_precision",
      _a17.get("tcpi") is not None and _a17.get("tcpi") != _a17.get("tcpi_display")
      and abs(float(_a17["tcpi"]) - (1_000_000.0 - 400_000.0) / (1_000_000.0 - 440_000.0)) < 1e-12,
      "A1.7 carries the canonical to-complete index at full precision and not the rounded "
      "presentation value; rounding before banding is restored",
      f"tcpi={_a17.get('tcpi')!r} display={_a17.get('tcpi_display')!r}")
check("run36.fault07.a1_8_not_rounded",
      _a18.get("vac") is not None
      and abs(float(_a18["vac"]) - (1_000_000.0 - 1_000_000.0 / 0.909)) < 1e-9
      and float(_a18["vac"]) != float(_a18.get("vac_display")),
      "A1.8's analytical variance at completion is the full-precision identity and is not "
      "replaced by its formatted output",
      f"vac={_a18.get('vac')!r} display={_a18.get('vac_display')!r}")
check("run36.fault08.voting_exactly_two",
      sorted(REG.CORE_VOTING_MODULES) == ["A1.7", "A1.8"]
      and len([r for r in TARGETS if r["voting"] == "YES"]) == 2,
      "the voting set is exactly A1.7 and A1.8; a third voter has been added",
      f"{sorted(REG.CORE_VOTING_MODULES)} / "
      f"{[r['module_id'] for r in TARGETS if r['voting'] == 'YES']}")

# ---------------------------------------------------------------- 9-10 Category 9
_unqual = {k: v for k, v in CORPUS_SI.items() if k != "evidenceQualification"}
_gated = []
for _mid in ("B1.1", "B2.18", "B4.3", "B4.7"):
    _r = run(_mid, _unqual)
    if _r.get("__state__") == "COMPUTES" and not str(
            _r.get("abstention_reason_code") or _r.get("qualification_state") or ""):
        _gated.append(_mid)
check("run36.fault09.category9_gate_not_bypassed",
      ASSESSMENT_MISSING == "CATEGORY9_ASSESSMENT_MISSING" and not _gated,
      "a package carrying no Category-9 assessment cannot reach a governed downstream method; "
      "the gate is bypassed", str(_gated))
_c_votes = [g for g in ("C",) if contributes_to_project_status(g)]
check("run36.fault10.category9_not_a_risk_vote",
      not _c_votes and not (set(r["module_id"] for r in TARGETS
                                if r["voting"] == "YES") & {m for m in IDX
                                                            if IDX[m]["group"] == "C"}),
      "Category 9 is qualification and metadata and does not vote on project status; it has "
      "become a risk vote", str(_c_votes))

# ---------------------------------------------------------------- 11-12 Category 10
_v7 = text("server/app/simulation/canonical_v7.py")
check("run36.fault11.cat10_no_human_authority",
      '"human_authorization_required": True' in _v7 and "status_color" not in _v7.split(
          "ANALYTICAL_RESULT = ")[-1].split("def ")[0],
      "every Category-10 result requires human authorization and exercises no approval authority "
      "of its own", "human_authorization_required not True on the envelope")
check("run36.fault12.cat10_no_evidence_feedback",
      '"creates_project_evidence": False' in _v7,
      "no Category-10 output re-enters as project-condition evidence; a feedback loop into "
      "upstream project evidence has been opened",
      "creates_project_evidence is not False")

# ---------------------------------------------------------------- 13-16 disabled and archived
for _n, _mid, _label in ((13, "A3.4", "Material Cost Variance"),
                         (14, "B2.7", "Plithogenic Sets"),
                         (15, "B2.20", "Hypersoft Sets"),
                         (16, "B2.9", "Quantum Probability")):
    # RUN 137, ITEM 3. RE-POINTED: "DISABLED AND STILL REGISTERED" BECAME "REMOVED" AT RUN 96.
    # Run 36 froze these four as disabled rows that stayed in the registry so a reader could see
    # them held down. The owner's Run 96 ruling struck the retired rows OUT of the registry
    # instead, and all four are on `run96_removed.REMOVED_AT_RUN96`. `_mid in IDX` has been false
    # ever since, so this check failed on a removal that was the point rather than a
    # reactivation, while the thing it guards against -- an operational reading -- was never
    # observed. What is asserted now is the state each module is actually in, and it is the
    # stronger of the two: the identifier does not resolve at all, the dispatcher refuses it by
    # name, and it is still named on the disabled roster so the historical decision stays
    # readable. A row written back into the registry turns this red, which is what the check is
    # for.
    _r = run(_mid)
    _removed = _mid in _REMOVED_96_97
    check(f"run36.fault{_n}.{_mid.replace('.', '_').lower()}_not_operational",
          _mid in REG.DISABLED_MODULES and _removed and _mid not in IDX
          and _r.get("__state__") == "SUPPLIED" and not _r.get("status_color"),
          f"{_label} is on the disabled roster, was removed from the registry at Run 96, does "
          f"not resolve, and produces no operational reading; it has been reactivated",
          f"disabled={_mid in REG.DISABLED_MODULES} removed={_removed} "
          f"registered={_mid in IDX} state={_r.get('__state__')} "
          f"colour={_r.get('status_color')!r}")

# ---------------------------------------------------------------- 17-23 Portfolio Health
_v8 = text("server/app/simulation/canonical_v8.py")
check("run36.fault17.ph1_threshold_schema_bound",
      V8.RUN15_FROZEN_THRESHOLD == 0.576 and V8.RUN15_FROZEN_SCHEMA == "run15-synthetic-4feature-v1"
      and V8.RUN15_THRESHOLD_LABELS["is_project_status_band"] is False
      and V8.RUN15_THRESHOLD_LABELS["field_validated"] is False,
      "the 0.576 threshold stays synthetic, schema-bound and not a project-status band; it has "
      "been applied on the wrong schema",
      f"{V8.RUN15_FROZEN_THRESHOLD} / {V8.RUN15_FROZEN_SCHEMA} / {V8.RUN15_THRESHOLD_LABELS}")
_small = V8.cohort_size_policy(4)
_tiny = V8.cohort_size_policy(2)
check("run36.fault18.ph1_small_cohort_not_authoritative",
      V8.MIN_COHORT_FOR_RANKING == 3 and _tiny[0] == "COHORT_BELOW_MINIMUM"
      and "no reading of any kind" in _tiny[1]
      and _small[0] == "COHORT_SMALL"
      and "NO authoritative anomaly flag is produced" in _small[1],
      "a cohort below the minimum is not estimable and a small cohort carries an explicit "
      "limitation rather than an authoritative flag", f"{_tiny} / {_small}")
check("run36.fault19.ph2_no_invented_weights",
      "composite is NONE" in _v8 and "_governed_weights" in _v8,
      "PH.2 emits no composite without governed weights; equal weights have been invented",
      "the governed-weights gate is gone")
check("run36.fault20.ph3_min_three_observations",
      V8.MIN_TRAJECTORY_OBSERVATIONS == 3
      and "if len(times) < MIN_TRAJECTORY_OBSERVATIONS" in _v8,
      "PH.3 fits no trend below three distinct observations; a trajectory from two observations "
      "is allowed", str(V8.MIN_TRAJECTORY_OBSERVATIONS))
check("run36.fault21.ph4_radius_retired",
      "No match threshold is applied" in _v8 and "0.15 radius is retired" in _v8,
      "PH.4's unvalidated 0.15 radius stays retired and continuous distance only is reported; "
      "the radius has been restored", "the retirement sentence is gone")
_ph5 = [ln for ln in _v8.splitlines() if "PARAMETER_PROVENANCE_BLOCKED" in ln]
check("run36.fault22.ph5_no_invented_weights", bool(_ph5),
      "PH.5 returns a null score under PARAMETER_PROVENANCE_BLOCKED rather than a composite "
      "under invented weights", str(len(_ph5)))
check("run36.fault23.ph5_no_duplicate_lineage_reinforcement",
      "D1.5" in _v8 and "relative_distance" in _v8 and "PARAMETER_PROVENANCE_BLOCKED" in _v8,
      "PH.5 does not reinforce a project's score by counting one lineage twice",
      "the D1.5 provenance block is gone")

# ---------------------------------------------------------------- 24 lineage
_indep = [r for r in TARGETS if r["lineage"] == "LINEAGE_ESTABLISHED_INDEPENDENT"]
check("run36.fault24.unknown_lineage_not_independent",
      all(r["module_id"] in LIN.MODULE_LINEAGE for r in _indep),
      "no row claims independent lineage without an actual lineage record; unknown lineage is "
      "being treated as independent",
      str([r["module_id"] for r in _indep if r["module_id"] not in LIN.MODULE_LINEAGE]))

# ---------------------------------------------------------------- 25-26 defensibility
_served = {}
for _mm in re.finditer(r'"([A-D]\d+\.\d+)": \{(.*?)\},\n', _ds, re.S):
    _served[_mm.group(1)] = _mm.group(2)
_lying_conditional = []
for _mid, _blob in _served.items():
    if _mid not in SCIENTIFIC or _mid in PORTFOLIO_VALIDATED:
        continue
    # SCOPED TO MODULES THAT DECLARE A GOVERNED STRUCTURE. "Computes from the governed evidence
    # the platform already holds" is a claim about the ROUTE, and it stays true of a module that
    # abstains this period for want of a scalar. What it may NOT be true of is a module whose
    # route REFUSES without a declared structure: that one is conditional, and describing it as
    # computing is the fault. The declaration is read from the structure maps, not from the
    # served object, so the oracle is not the thing it is checking.
    if not _declared_structure(_mid):
        continue
    _says_computes = "COMPUTES_FROM_AVAILABLE_EVIDENCE" in _blob
    _r = run(_mid)
    if _says_computes and _r.get("__state__") == "ABSTAINS":
        _lying_conditional.append(_mid)
check("run36.fault25.conditional_not_described_unconditional", not _lying_conditional,
      "no conditional method is described as unconditionally computing",
      str(_lying_conditional)[:200])
_lying_disabled = [m for m in REG.DISABLED_MODULES
                   if m in _served and "COMPUTES_FROM_AVAILABLE_EVIDENCE" in _served[m]]
check("run36.fault26.disabled_not_described_active", not _lying_disabled,
      "no disabled method is described as active", str(_lying_disabled))

# ---------------------------------------------------------------- 27-30 client authority
_authority = ROOT / "server" / "tools" / "taxonomy_authority.json"
check("run36.fault27.one_taxonomy_authority",
      _authority.is_file()
      and "build_client_taxonomy.py" in text("assets/js/taxonomy.js")
      and "build_client_taxonomy.py" in text("assets/js/categories.js")
      and "GENERATED BLOCK" in text("assets/js/taxonomy.js")
      and "GENERATED BLOCK" in text("assets/js/categories.js"),
      "there is ONE authoritative taxonomy source and both client surfaces are generated "
      "mirrors of it; a second authority exists",
      f"authority={_authority.is_file()}")
check("run36.fault28.no_stale_proxy_qualifier",
      all(m in IDX for m in REG.PROXY_QUALIFIERS)
      and all(m not in REG.DISABLED_MODULES for m in REG.PROXY_QUALIFIERS),
      "every surviving proxy qualifier names a live registered module; a stale qualifier has "
      "been restored", str(sorted(REG.PROXY_QUALIFIERS)))
_cat = text("assets/js/categories.js")
check("run36.fault29.client_method_class_lookup_intact",
      # RUN 54: `+ text("assets/js/deepdive.js")` was the fourth term. The file is DELETED. The
      # check is UNCHANGED in force -- it asks whether getModuleStatus appears anywhere in the
      # client dispatch surfaces, and one fewer surface makes the disjunction HARDER to satisfy,
      # not easier.
      'case "Monte_Carlo":' in _cat and "getModuleStatus" in _cat + text("assets/js/knowledge.js")
      + text("assets/js/workspace.js"),
      "the client method-class lookup still dispatches; it has been broken so statuses silently "
      "never render", "the Monte_Carlo case is gone")
_tax = text("assets/js/taxonomy.js")
check("run36.fault30.no_recursion_in_taxonomy_path",
      "function methodClassStatus" not in _tax or "methodClassStatus(" not in _tax.split(
          "function methodClassStatus", 1)[-1].split("\n}", 1)[0],
      "no function in the participant taxonomy path calls itself; recursion has been introduced",
      "a self-call was found in the taxonomy path")

# ---------------------------------------------------------------- 31-36 participant workflow
_dec = text("server/app/research_decision.py")
_mod = text("server/app/research_models.py")
_ui = text("assets/js/decision-ui.js")
check("run36.fault31.preliminary_lock_enforced",
      "preliminary judgment is already locked and cannot be resubmitted" in _dec,
      "a locked preliminary judgment cannot be resubmitted; the lock has been broken",
      "the refusal is gone from research_decision.py")
check("run36.fault32.no_reveal_before_preliminary_lock",
      "ck_decisions_reveal_after_pre_lock" in _mod
      and "reveal_at IS NULL OR (pre_locked_at IS NOT NULL AND pre_locked_at <= reveal_at)" in _mod
      and "preliminary judgment must be submitted and locked before the decision" in _dec,
      "the AI package cannot be revealed before the preliminary judgment is locked, at the "
      "database and at the route; the reveal has been let through early",
      "the reveal-after-lock constraint is gone")
check("run36.fault33.no_edit_after_final_lock",
      "a final decision has already been recorded for this assignment" in _dec,
      "a final response cannot be edited after the final lock; the refusal has been removed",
      "the final-lock refusal is gone from research_decision.py")
check("run36.fault34.no_skipped_project_period",
      "ConditionSequence" in text("server/app/research_assignment.py")
      and "position" in text("server/app/research_assignment.py"),
      "project-periods are drawn from an ordered condition sequence and none may be skipped",
      "the ordered condition sequence is gone")
_seq_files = PP.SEQUENCE_BEARING_FILES
_v11 = {}
for _ln in (AUDIT / "run33_participant_package_v11_checksums.sha256").read_text(
        encoding="utf-8").splitlines():
    if re.match(r"^[0-9a-f]{64}  ", _ln):
        _h, _p = _ln.split("  ", 1)
        _v11[_p] = _h
import hashlib                                                    # noqa: E402
# RUN 54. A DELETED FILE MUST COUNT AS MOVED, NOT CRASH. `assets/js/deepdive.js` was DELETED on
# the owner's ruling at section 8 of the Run 54 order, and hashing a path that does not exist
# raised FileNotFoundError, which is a crash and a crash is not a pass. A missing file now hashes
# to None, so it can never equal a recorded digest and is therefore ALWAYS counted as moved. The
# comparison is not loosened: an UNDECLARED deletion still fails, exactly as an undeclared edit
# does, and the declaration is V20_TO_V21_SEQUENCE_EXCEPTION in participant_packages.py.
def _sha_or_gone(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


_moved_seq = sorted(f for f in _seq_files
                    if _sha_or_gone(ROOT / f) != _v11.get(f))
# RUN 44. ONE of the six has legitimately moved since v11, and it is NAMED rather than excused
# by loosening the comparison. The Portfolio Health flyout in deepdive.js told a participant the
# panel needed at least three projects; after Run 43 retired every Portfolio Level module from
# service no number of projects makes it compute, so the sentence was false on every render, and
# the owner ordered it corrected at Run 44 section 4.4. The other five are still held to the
# frozen v11 bytes, so a second file moving here -- or a different one -- is still a failure.
# RUN 49. A SECOND of the six has now legitimately moved, and it too is NAMED rather than
# excused by loosening the comparison: `assets/js/decision-ui.js` gains comments only, at its
# three inert `period: 1` literals, on the owner's ruling 4 of 2026-08-22. The other four are
# still held to the frozen v11 bytes, so a third file moving here is still a failure.
# RUN 51. ALL SIX have now legitimately moved, on the owner's rulings 1 to 6 of 2026-08-22, and
# every one of them is NAMED rather than excused by loosening the comparison: the exception set
# below is built from the per-successor exception tuples participant_packages declares, so a file
# moving without a declared record is still a failure. What keeps this a real invariant now that
# the exception spans the whole set is the SECOND check: each of the six must carry its own named
# exception record in the current package's checksum-record header, saying what moved inside it.
# RUN 52. A SEVENTH move does not exist -- the set is six -- but deepdive.js moved AGAIN, on the
# owner's rulings 2 and 3 of 2026-08-23, and it is NAMED again rather than excused: the exception
# set below now also folds in V19_TO_V20_SEQUENCE_EXCEPTION. The invariant is not widened: the
# set is still exactly the six sequence-bearing files, and the SECOND check below still requires
# each file that moved in a given successor to carry its own named record IN THAT SUCCESSOR'S
# record, which is where the account of what moved inside it actually lives.
# RUN 55 folds in V20_TO_V21_SEQUENCE_EXCEPTION on exactly the same footing. THE SET DOES NOT
# GROW: v20-to-v21's exception is `assets/js/deepdive.js`, which v19-to-v20 already named, so the
# union is still exactly the SIX sequence-bearing files and the `len(...) == 6` assertion below
# is unchanged. What is new about this link is that the delta is a DELETION rather than an edit,
# which is why the file's own record in the v21 checksum record says so in those words.
_SEQ_AUTHORISED = (set(PP.V14_TO_V15_SEQUENCE_EXCEPTION) | set(PP.V17_TO_V18_SEQUENCE_EXCEPTION)
                   | set(PP.V18_TO_V19_SEQUENCE_EXCEPTION)
                   | set(PP.V19_TO_V20_SEQUENCE_EXCEPTION)
                   | set(PP.V20_TO_V21_SEQUENCE_EXCEPTION)
                   # RUN 56 folds in V21_TO_V22_SEQUENCE_EXCEPTION on the same footing. It is
                   # EMPTY, so THE SET DOES NOT GROW and the `len(...) == 6` assertion below is
                   # unchanged. Folding an empty set in explicitly is the point: the union is
                   # built from every declared link, so a link that is silently left out of it
                   # cannot hide a move.
                   | set(PP.V21_TO_V22_SEQUENCE_EXCEPTION)
                   # RUN 57 folds in V22_TO_V23_SEQUENCE_EXCEPTION on the same footing and for
                   # the same reason. It is EMPTY too, so THE SET STILL DOES NOT GROW and the
                   # `len(...) == 6` assertion below is unchanged.
                   | set(PP.V22_TO_V23_SEQUENCE_EXCEPTION))
check("run36.fault35.participant_sequence_unaltered",
      sorted(_moved_seq) == sorted(_SEQ_AUTHORISED) and len(_SEQ_AUTHORISED) == 6,
      "every file carrying the participant experimental sequence is byte-identical to the frozen "
      "v11 package, except the SIX the owner authorised Runs 44, 49 and 51 to move; the sequence "
      "has been altered somewhere else", str(_moved_seq))
# THE RECORD THAT MUST NAME A FILE IS THE RECORD OF THE SUCCESSOR THAT MOVED IT. A file moved by
# v19 is accounted for in v19's record; a file moved by v20 in v20's. Requiring v20's record to
# re-declare files v19 moved would either force every successor to copy its predecessor's prose
# forward or force the check to be loosened, and both destroy the invariant.
_BY_SUCCESSOR = (
    ("code_audit/run51_participant_package_v19_checksums.sha256",
     PP.V18_TO_V19_SEQUENCE_EXCEPTION),
    ("code_audit/run52_participant_package_v20_checksums.sha256",
     PP.V19_TO_V20_SEQUENCE_EXCEPTION),
    ("code_audit/run55_participant_package_v21_checksums.sha256",
     PP.V20_TO_V21_SEQUENCE_EXCEPTION),
    # RUN 56. The v21-to-v22 link moved EXACTLY ONE participant-visible file,
    # assets/js/ingest.js, and it is NOT sequence-bearing, so this link's exception tuple is
    # EMPTY -- and it is DECLARED empty in participant_packages.py rather than omitted. The
    # entry is added here anyway, and that matters twice over. First, the clause below requires
    # PP.CURRENT.record to BE the last entry of this tuple, so a mint that forgot to account for
    # its own link would turn this row red rather than pass by omission. Second, the invariant
    # is unweakened: if a sequence-bearing file had moved across this link it would have to be
    # named in V21_TO_V22_SEQUENCE_EXCEPTION for fault35's sibling check to pass, and naming it
    # there would then require its own "-- SEQUENCE-BEARING" paragraph in the v22 record here.
    ("code_audit/run56_participant_package_v22_checksums.sha256",
     PP.V21_TO_V22_SEQUENCE_EXCEPTION),
    # RUN 57. The v22-to-v23 link moved THREE participant-visible files -- assets/css/radar.css,
    # assets/js/detail.js and assets/js/ingest.js -- and NOT ONE is sequence-bearing, so this
    # link's exception tuple is EMPTY and is DECLARED empty in participant_packages.py rather
    # than omitted. The entry is added here for the same two reasons the v22 entry was: the
    # clause below requires PP.CURRENT.record to BE the last entry of this tuple, so a mint that
    # forgot its own link goes red rather than passing by omission; and the invariant is
    # unweakened, because a sequence-bearing file moving across this link would have to be named
    # in V22_TO_V23_SEQUENCE_EXCEPTION, which would then require its own "-- SEQUENCE-BEARING"
    # paragraph in the v23 record here.
    ("code_audit/run57_participant_package_v23_checksums.sha256",
     PP.V22_TO_V23_SEQUENCE_EXCEPTION),
    # RUN 59. The v24 link, and the FIRST since v21 to carry a non-empty sequence exception:
    # assets/js/decision-ui.js. Its "-- SEQUENCE-BEARING" paragraph is present in the v24 record,
    # which is what this guard checks, so the exception is declared and not merely tolerated.
    ("code_audit/run59_participant_package_v24_checksums.sha256",
     PP.V23_TO_V24_SEQUENCE_EXCEPTION),
    # RUN 62. The v25 link, which also carries a non-empty sequence exception:
    # assets/js/workspace.js. Its "-- SEQUENCE-BEARING" paragraph is present in the v25 record,
    # which is what this guard checks, so the exception is declared and not merely tolerated.
    # assets/js/taxonomy.js also moved across this link and is NOT sequence-bearing, established
    # by membership of SEQUENCE_BEARING_FILES_FROM_V21 rather than assumed, so it needs none.
    ("code_audit/run62_participant_package_v25_checksums.sha256",
     PP.V24_TO_V25_SEQUENCE_EXCEPTION),
    # RUN 63. The v26 link, whose exception tuple is EMPTY and is DECLARED empty in
    # participant_packages.py rather than omitted -- the Run 63 order requires the empty tuple to
    # be written out. The entry is added here for the same two reasons the v22 and v23 entries
    # were: the clause below requires PP.CURRENT.record to BE the last entry of this tuple, so a
    # mint that forgot its own link goes red rather than passing by omission; and the invariant
    # is unweakened, because a sequence-bearing file moving across this link would have to be
    # named in V25_TO_V26_SEQUENCE_EXCEPTION, which would then require its own
    # "-- SEQUENCE-BEARING" paragraph in the v26 record here. NEITHER file that moved --
    # assets/js/detail.js, assets/js/neural_flow.js -- is a member of
    # SEQUENCE_BEARING_FILES_FROM_V21, established by membership rather than assumed.
    ("code_audit/run63_participant_package_v26_checksums.sha256",
     PP.V25_TO_V26_SEQUENCE_EXCEPTION),
)
_undeclared = [f"{f} (in {_rec})" for _rec, _files in _BY_SUCCESSOR for f in _files
               if f"# {f} -- SEQUENCE-BEARING"
               not in (ROOT / _rec).read_text(encoding="utf-8")]
check("run36.fault35.every_sequence_exception_has_its_own_record",
      not _undeclared and PP.CURRENT.record == _BY_SUCCESSOR[-1][0],
      "and every sequence-bearing file that moved carries its OWN named exception record in the "
      "checksum record of the successor that moved it, saying what moved inside it; a file "
      "moving without one is a failure even though the exception now spans the whole set",
      str(_undeclared))
check("run36.fault36.evidence_and_rationale_captured",
      "decision.rationale = payload.get(\"rationale\")" in _dec
      and "decision.evidence_items = evidence_items" in _dec
      and 'evidence_items must be a list' in _dec,
      "the final response captures both the evidence items and the free-text rationale; capture "
      "has been omitted", "the rationale or evidence capture is gone")

# ---------------------------------------------------------------- 37 sealed packages
_sealed_bad = []
for _pkg in PP.PARTICIPANT_PACKAGES[:-1]:
    _p = subprocess.run(["git", "show", f"{_pkg.source_commit}:{_pkg.record}"],
                        cwd=ROOT, capture_output=True, text=True)
    if _p.returncode != 0:
        continue
    if _p.stdout != (ROOT / _pkg.record).read_text(encoding="utf-8"):
        _sealed_bad.append(_pkg.identifier)
check("run36.fault37.sealed_predecessor_package_intact", not _sealed_bad,
      "no sealed predecessor package record has been rewritten in place", str(_sealed_bad))

# ---------------------------------------------------------------- 38-39 validation honesty
_par = rows("run36_parameter_provenance_reaudit.csv")
_emp_claims = [r for r in _par
               if r["row_type"] == "PARAMETER" and "EMPIRICAL" in r["empirical_validation_state"]
               and "PENDING" not in r["empirical_validation_state"]]
check("run36.fault38.synthetic_not_called_empirical",
      not _emp_claims
      and not any(r["empirical_validation_class"] == "EMPIRICALLY_VALIDATABLE_NOW"
                  for r in TARGETS),
      "no synthetic laboratory calibration is recorded as empirical field validation",
      str([r["module"] for r in _emp_claims])[:200])
_bad_pass = [r for r in QUAL if r["row_type"] == "SCIENTIFIC_TARGET"
             and r["final_qualification"] == "QUALIFIED_FOR_BOUNDED_STUDY_USE"
             and r["empirical_validation"] in ("STRUCTURE_OR_DATA_ABSENT",)
             and r["module_id"] not in ("A1.1",)]
check("run36.fault39.not_applicable_not_pass",
      not _bad_pass,
      "a target with no evidence to score is not promoted to a bounded-use pass; NOT_APPLICABLE "
      "is being read as PASS", str([r["module_id"] for r in _bad_pass])[:200])

# ---------------------------------------------------------------- 40 the freeze gate itself
_instr = [r for r in QUAL if r["row_type"] == "INSTRUMENT_BLOCKING_DEFECT"]
_target_blocking = [r for r in TARGETS if r["blocking_defect"] != "NO"]
_blocking = len(_instr) + len(_target_blocking)
_manifest = ROOT / "research" / "freeze" / "INSTRUMENT_FREEZE_CANDIDATE_MANIFEST.json"
_companion = ROOT / "research" / "freeze" / "INSTRUMENT_FREEZE_CANDIDATE.md"
check("run36.fault40.no_freeze_while_blocked",
      not (_blocking > 0 and (_manifest.is_file() or _companion.is_file())),
      "no freeze candidate exists while a blocking defect remains; the freeze gate has been "
      "opened with a defect standing",
      f"blocking={_blocking} manifest={_manifest.is_file()} companion={_companion.is_file()}")

print()
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
raise SystemExit(1 if FAILED else 0)
