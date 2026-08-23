"""
RUN 32 -- THE THIRTY-TWO FAULT INJECTION CAMPAIGN FOR THE CATEGORY-10 DECISION LAYER.

WHAT A FAULT PROVES, AND WHAT IT DOES NOT. A green guard proves nothing on its own: it may be
green because the property holds, or because the guard never looked. This campaign breaks the
property deliberately and requires the named guard to go RED FOR THE INTENDED REASON. Anything
else is recorded as a failure of the campaign, not smoothed over.

THE FIVE WAYS A CHECK HAS LIED IN THIS REPOSITORY are all defended against here:

  * CRASHED RATHER THAN FAILING. A guard that dies without printing an anchored
    `RESULT: n/m` line is NOT red. It is recorded as a crash and the fault is NOT counted.
  * INJECTION SILENTLY FAILED TO APPLY. Every mutation is verified by RE-READING THE BYTES FROM
    DISK after writing, and the fault is recorded NOT_APPLIED if the bytes do not carry it.
  * ASSERTED THE DEFECT'S OWN SENTENCE. The expected RED reason is matched against the guard's
    output, so an unrelated failure cannot be accepted as evidence.
  * A STALE CACHE SURVIVING THE RESTORE. `__pycache__` is cleared on BOTH sides of every
    injection. A restore inside the same clock second changes neither mtime nor size, so a
    cached mutant would otherwise keep running after the source was put back.
  * THE MUTATION LEAKING. Every file is restored BYTE FOR BYTE from the bytes read before the
    mutation, and the baseline is re-run and required to be GREEN again.

Run it with PYTHONIOENCODING=utf-8. It writes code_audit/run32_fault_injection_results.csv.
"""

from __future__ import annotations

import csv
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SERVER = HERE.parent
ROOT = SERVER.parent

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
_cs_arm(_cs_pl.Path(ROOT), "run32_fault_campaign.py",
        allow=["code_audit/run30_participant_package_v5_checksums.sha256", "code_audit/run32_fault_injection_results.csv"])
# -------------------------------------------------------------------------------------------

APP = SERVER / "app"
SIM = APP / "simulation"

V7 = SIM / "canonical_v7.py"
V5 = SIM / "canonical_v5.py"
CAT10 = SIM / "models_cat10.py"
REGISTRY = SIM / "registry.py"
MODELS = SIM / "models.py"
PROJECT_DATA = APP / "project_data.py"

ORACLE = "test_run32_cat10_oracles.py"
BOUNDARY = "test_run32_closure_version_boundary.py"
CAT7_ORACLE = "test_run30_canonical_oracles.py"
COA = "test_courses_of_action.py"
CAT9 = "test_run31_pass2_acceptance.py"
DISABLED = "test_run14_disabled_method_functional.py"
PARTICIPANT = "test_run28_participant_packages.py"
SUPPLY = "test_run32_cat10_oracles.py"
ROUTE7 = "test_run30_cat7_operational_route.py"
CYCLE8 = "test_run20_cycle8_arch3_clusters.py"


def clear_pycache() -> None:
    for d in SERVER.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


_TEMPLATE = None


def template_db() -> pathlib.Path:
    """One migrated SQLite template, copied per guard run. Never :memory:."""
    global _TEMPLATE
    if _TEMPLATE is None:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="run32faults-"))
        db = tmp / "template.db"
        env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}",
                   SESSION_SECRET="test-secret-do-not-use-in-prod")
        r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                           cwd=SERVER, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("alembic upgrade head FAILED:\n" + r.stdout + r.stderr)
        _TEMPLATE = db
    return _TEMPLATE


def run_guard(suite: str) -> tuple[int, str, str | None]:
    """Run one guard against its OWN freshly migrated database. Returns (rc, output, result)."""
    tmpl = template_db()
    db = tmpl.parent / f"{suite}.{os.getpid()}.db"
    shutil.copy(tmpl, db)
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}",
               SESSION_SECRET="test-secret-do-not-use-in-prod", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, suite], cwd=HERE, env=env,
                       capture_output=True, text=True, timeout=1800)
    out = (r.stdout or "") + (r.stderr or "")
    result = None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("RESULT: ") and "/" in s:
            result = s
    db.unlink(missing_ok=True)
    return r.returncode, out, result


def failing_lines(out: str) -> list[str]:
    """
    The guard's OWN failing-check sentences, in every shape the suites in this tree print them.

    The intended RED reason is matched against THESE and not against the whole output, so a
    PASSING line that happens to contain the same words cannot be read as evidence, and a guard
    that went red somewhere unrelated cannot be credited with catching the fault.
    """
    lines = []
    for raw in out.splitlines():
        s = raw.strip()
        if s.startswith("FAIL: ") or s.startswith("FAILED: "):
            lines.append(s.split(": ", 1)[1])
        elif s.startswith("FAIL "):
            lines.append(s[5:])
        elif s.startswith("**** "):
            lines.append(s[5:].strip())
        elif s.startswith("- "):
            lines.append(s[2:])
    return lines


def is_green(result: str | None) -> bool:
    if not result:
        return False
    nums = result.split("RESULT: ", 1)[1].split()[0]
    a, b = nums.split("/")
    return a == b


#: Each fault: (id, system, invariant, target file, old bytes, new bytes, guard, intended reason)
#: `old` must occur EXACTLY ONCE in the target, which is checked before anything is written.
FAULTS: list[tuple] = [

    # ---------------------------------------------------------------- 10.1 MULTI-OBJECTIVE
    (1, "B4.1 Multi-Objective Optimization (canonical_v7.multi_objective)",
     "an alternative set is REQUIRED; with fewer than two feasible alternatives there is no "
     "trade-off and the method abstains rather than reporting an optimisation",
     V7,
     '    words = V7_STRUCTURE_WORDS["B4.1"]\n'
     "    ctx = _context(structure, words)\n"
     "    criteria, alternatives, _p = _objective_vectors(structure, words)",
     '    words = V7_STRUCTURE_WORDS["B4.1"]\n'
     "    ctx = _context(structure, words)\n"
     "    try:\n"
     "        criteria, alternatives, _p = _objective_vectors(structure, words)\n"
     "    except StructureAbsent:\n"
     '        return _result("multi_objective_optimization", ctx, nondominated_set=[],\n'
     "                       dominated_set=[], selected_alternative=None)",
     ORACLE,
     "10.1 abstains with no structure"),

    (2, "B4.1 Multi-Objective Optimization (canonical_v7._dominates)",
     "a dominated alternative may never appear in the nondominated set: D=(13,9) is dominated "
     "and A, B, C are not",
     V7,
     "            if av > bv:\n                return False\n"
     "            if av < bv:\n                better_somewhere = True",
     "            if av > bv:\n                better_somewhere = True\n"
     "            if av < bv:\n                better_somewhere = True",
     ORACLE,
     "10.1 D is dominated"),

    (3, "B4.1 Multi-Objective Optimization (canonical_v7.multi_objective)",
     "no single best alternative is ever named: choosing one from a nondominated set requires "
     "supplied preference information, and none is governed",
     V7,
     "        selected_alternative=None,",
     "        selected_alternative=(front[0][\"alternative_id\"] if front else None),",
     ORACLE,
     "10.1 names no single best alternative"),

    # ---------------------------------------------------------------- 10.2 LINEAR PROGRAMMING
    (4, "B4.2 Linear Programming (canonical_v7.linear_program)",
     "the Wyndor optimum is exactly x1=2, x2=6 with objective 36",
     V7,
     "        if best is None or (value > best[0] if m[\"sense\"] == \"maximize\" else value < best[0]):",
     "        if best is None or (value < best[0] if m[\"sense\"] == \"maximize\" else value > best[0]):",
     ORACLE,
     "10.2 Wyndor objective = 36"),

    (5, "B4.2 Linear Programming (canonical_v7.linear_program)",
     "an infeasible vertex can never be returned: feasibility is tested at every candidate",
     V7,
     "        ok, _viol = _lp_feasible(m, point)\n        if not ok:\n            continue",
     "        ok, _viol = _lp_feasible(m, point)\n        if False:\n            continue",
     ORACLE,
     "10.2 infeasible model reports INFEASIBLE rather than a number"),

    (6, "B4.2 Linear Programming (canonical_v7._lp_feasible)",
     "the declared bounds, INCLUDING non-negativity, are part of the feasibility test rather "
     "than an afterthought",
     V7,
     '        lo = v.get("lower_bound", 0)\n'
     "        lower[vid] = None if lo is None else Fraction(str(lo))",
     '        lo = v.get("lower_bound", 0)\n'
     "        lower[vid] = None",
     ORACLE,
     "10.2 minimising the same model gives 0 at the origin"),

    # ---------------------------------------------------------------- 10.3 CSP
    (7, "B4.3 Constraint Satisfaction (canonical_v7.constraint_satisfaction)",
     "a CSP without variables or domains is not a CSP: there is nothing to assign, so the "
     "method abstains rather than running",
     V7,
     "        if not isinstance(dom, list) or not dom:\n"
     "            raise StructureAbsent(\n"
     "                f\"Variable {vid} in the {words} provided for this project has no domain, so \"\n"
     "                f\"there is nothing for it to be assigned from.\")",
     "        if not isinstance(dom, list) or not dom:\n"
     "            dom = [None]",
     ORACLE,
     "10.3 abstains when a variable has no domain"),

    (8, "B4.3 Constraint Satisfaction (canonical_v7.constraint_satisfaction)",
     "(A,1) is INFEASIBLE under the supplied constraint network and must never be reported "
     "feasible; (A,2), (B,1) and (B,2) are feasible",
     V7,
     "        failed = [c.get(\"constraint_id\") for c in constraints\n"
     "                  if not _csp_holds(c, assignment, words)]",
     "        failed = [c.get(\"constraint_id\") for c in constraints[:0]\n"
     "                  if not _csp_holds(c, assignment, words)]",
     ORACLE,
     "10.3 the single infeasible assignment is (A,1)"),

    (9, "B4.3 Constraint Satisfaction (canonical_v7.constraint_satisfaction)",
     "every declared rule is evaluated against every complete assignment; no rule may be "
     "skipped, and the old fixed-threshold checklist is not preserved",
     V7,
     "    raise StructureAbsent(\n"
     "        f\"A constraint in the {words} provided uses the rule form {kind!r}, which this method \"\n"
     "        f\"does not evaluate. It is not treated as satisfied, so no solution set is reported.\")",
     "    return True",
     ORACLE,
     "10.3 an unrecognised rule form is refused, never treated as satisfied"),

    # ---------------------------------------------------------------- 10.4 WHAT-IF
    (10, "B4.4 What-If Scenario Matrix (canonical_v7._matrix)",
     "an action without an identity is not an action: several EAC formulas carrying no action "
     "identity are not an action-by-scenario matrix",
     V7,
     "        if not aid:\n"
     "            raise StructureAbsent(\n"
     "                f\"An action in the {words} provided has no identity. Formulas with no action \"\n"
     "                f\"identity are not an action-by-scenario matrix.\")",
     "        if not aid:\n"
     "            continue",
     ORACLE,
     "10.4 an action with no identity is refused"),

    (11, "B4.4 What-If Scenario Matrix (canonical_v7._matrix)",
     "a matrix with a hole is not a complete matrix: a decision rule over an incomplete matrix "
     "would silently treat an unknown outcome as known",
     V7,
     "    if missing:\n        raise StructureAbsent(\n"
     "            f\"The {words} provided for this project has no outcome for \"",
     "    if False:\n        raise StructureAbsent(\n"
     "            f\"The {words} provided for this project has no outcome for \"",
     ORACLE,
     "10.4 an incomplete matrix is refused rather than partially compared"),

    # ---------------------------------------------------------------- 10.5 SENSITIVITY
    (12, "B4.5 Decision Sensitivity Matrix (canonical_v7.decision_sensitivity)",
     "a decision model must be PERTURBED and the ranking RECOMPUTED; ranking today's KPI "
     "deviations is not decision sensitivity",
     V7,
     "    swept = [p for p in params if p.get(\"perturbation\") == \"sweep\"]\n"
     "    if len(swept) != 1:",
     "    swept = [p for p in params if p.get(\"perturbation\") == \"sweep\"]\n"
     "    if False:",
     ORACLE,
     "10.5 abstains when nothing is declared as swept"),

    (13, "B4.5 Decision Sensitivity Matrix (canonical_v7.decision_sensitivity)",
     "the ranking crossover for A=(0.9,0.4) and B=(0.6,0.8) is EXACTLY w = 4/7, solved as a "
     "linear equation rather than detected by sampling",
     V7,
     "        w = -intercept / slope",
     "        w = -intercept / slope + Fraction(1, 1000)",
     ORACLE,
     "10.5 the crossover is exactly 4/7"),

    # ---------------------------------------------------------------- 10.6 PARETO
    (14, "B4.6 Pareto Frontier Analysis (canonical_v7.pareto_frontier)",
     "D=(13,9) is dominated and must never appear on the frontier",
     V7,
     "    front, dominated = _nondominated(feasible, criteria)\n"
     "    dupes: dict[str, list[str]] = {}",
     "    front, dominated = ([{\"alternative_id\": a[\"alternative_id\"],\n"
     "                          \"label\": a.get(\"label\", a[\"alternative_id\"]),\n"
     "                          \"objective_vector\": {}} for a in feasible], [])\n"
     "    dupes: dict[str, list[str]] = {}",
     ORACLE,
     "10.6 D is off the frontier"),

    (15, "B4.6 Pareto Frontier Analysis (canonical_v7._nondominated)",
     "a frontier that depends on the order the alternatives were offered in is not a frontier: "
     "the result is identical across all 24 orderings",
     V7,
     "        dominators = [b[\"alternative_id\"] for b in alternatives\n"
     "                      if b[\"alternative_id\"] != aid\n"
     "                      and _dominates(vecs[b[\"alternative_id\"]], vecs[aid], senses)]",
     "        dominators = [b[\"alternative_id\"] for b in alternatives[:1]\n"
     "                      if b[\"alternative_id\"] != aid\n"
     "                      and _dominates(vecs[b[\"alternative_id\"]], vecs[aid], senses)]",
     ORACLE,
     "10.6 frontier is identical under all 24 input orderings"),

    # ---------------------------------------------------------------- 10.7 MINIMAX REGRET
    (16, "B4.7 Minimax Regret Decision Rule (canonical_v7.minimax_regret)",
     "under the supplied matrix the minimax-regret alternative is B with value 4; A and C both "
     "carry a maximum regret of 8",
     V7,
     "    lowest = min(max_regret.values())",
     "    lowest = max(max_regret.values())",
     ORACLE,
     "10.7 minimax-regret alternative is B"),

    (17, "B4.7 Minimax Regret Decision Rule (canonical_v7.minimax_regret)",
     "orientation is DECLARED and never assumed: reading a cost matrix as payoffs inverts every "
     "regret",
     V7,
     "        best_in_scenario[s] = max(vals) if m[\"orientation\"] == BENEFIT else min(vals)",
     "        best_in_scenario[s] = max(vals)",
     ORACLE,
     "10.7 the same numbers read as costs give different regrets"),

    (18, "B4.7 / the Category-10 authority boundary (models_cat10._authority_fields)",
     "NO ALGORITHM EXERCISES HUMAN APPROVAL AUTHORITY. Every Category-10 row is an "
     "ANALYTICAL_RESULT with human_authorization_required True; it is never a HUMAN_DECISION",
     CAT10,
     "        \"result_class\": ANALYTICAL_RESULT,\n"
     "        \"human_authorization_required\": True,",
     "        \"result_class\": \"HUMAN_DECISION\",\n"
     "        \"human_authorization_required\": False,",
     BOUNDARY,
     "and it requires human authorisation, so no algorithm here exercises approval authority"),

    # ---------------------------------------------------------------- MARCOS / CRITIC-TOPSIS
    (19, "B2.18 MARCOS Ranking (canonical_v5.decision_problem)",
     "criteria and alternatives are DISTINCT declared sets; treating the criteria as the "
     "alternatives would rank the yardsticks instead of the options",
     V5,
     "    if len(criteria) < 2:\n"
     "        raise StructureAbsent(\n"
     "            f\"The {words} provided for this project compares on fewer than two criteria, so \"",
     "    if False:\n"
     "        raise StructureAbsent(\n"
     "            f\"The {words} provided for this project compares on fewer than two criteria, so \"",
     CAT7_ORACLE,
     "7.18 criteria presented as alternatives are refused (fewer than two criteria)"),

    (20, "B2.19 CRITIC-TOPSIS (canonical_v5.critic_topsis)",
     "CRITIC derives its weights from the DISPERSION of each criterion across the alternative "
     "set; a single row has no dispersion, so one project row is refused",
     V5,
     "    m = len(alts)\n    if m < 3:",
     "    m = len(alts)\n    if m < 2:",
     SUPPLY,
     "CRITIC-TOPSIS refuses two project rows"),

    # ---------------------------------------------------------------- PARTICIPANT ACTIONS
    (21, "Participant courses of action (models_cat10 route)",
     "a participant's course of action is a free-text intention, NOT a fully scored alternative; "
     "scoring one would invent the objective values",
     CAT10,
     "        try:\n"
     "            structure = v7_structure(si, module_id)\n"
     "        except StructureAbsent as exc:\n"
     "            return _abstain(module_id, method_class, exc.sentence)",
     "        try:\n"
     "            structure = v7_structure(si, module_id)\n"
     "        except StructureAbsent as exc:\n"
     "            _row = {\"method_class\": method_class,\n"
     "                    \"result_source\": RESULT_SOURCE,\n"
     "                    \"canonical_disposition\": DISPOSITION_COMPUTED,\n"
     "                    \"insufficient_data\": False,\n"
     "                    \"evidence_metric\": \"the course of action scores highest\"}\n"
     "            _row.update(_authority_fields())\n"
     "            return _row",
     COA,
     "and its stable reason names a missing structure, not a missing figure, on a project that "
     "is genuinely missing a figure"),

    # ---------------------------------------------------------------- CATEGORY-9 GATE
    (22, "Category-9 qualification boundary (qualification_boundary.install)",
     "RAW, UNASSESSED evidence may not reach a Category-10 decision method: the gate refuses it "
     "before any decision is computed",
     SIM / "qualification_boundary.py",
     "                if not ev.eligible_for(use):",
     "                if False and not ev.eligible_for(use):",
     CAT9,
     "Decision Optimization: raw bypass = 0 across 7 production routes"),

    (23, "Category-9 qualification boundary (qualification_boundary.install)",
     "a MISSING Category-9 assessment may not bypass the gate: ABSENCE FAILS CLOSED, because "
     "absence is not eligibility",
     SIM / "qualification_boundary.py",
     "                if ev is None:\n                    return _refuse_missing(",
     "                if ev is None:\n"
     "                    return inner(si, rand, period_cutoff)\n"
     "                if False:\n                    return _refuse_missing(",
     CAT9,
     "Decision Optimization: missing-assessment bypass = 0 across 7 routes"),

    # ---------------------------------------------------------------- FEEDBACK
    (24, "The Category-10 evidence boundary (models_cat10._authority_fields)",
     "A DECISION OUTPUT NEVER RE-ENTERS AS PROJECT-CONDITION EVIDENCE. creates_project_evidence "
     "is False on every row and no row carries a status_color, so nothing can reach fusion",
     CAT10,
     "        \"creates_project_evidence\": False,",
     "        \"creates_project_evidence\": True,",
     BOUNDARY,
     "and it creates no project evidence, so a decision output cannot re-enter as a "
     "project-condition observation"),

    # ---------------------------------------------------------------- DISABLED MODULES
    (25, "B4.1 Multi-Objective Optimization (registry.DISABLED_CONCEPT_ONLY)",
     "B4.1 is a DISABLED concept-only module and stays disabled. A canonical engine passing its oracle is not grounds for activation, and activation is not this run's to grant",
     REGISTRY, '    "B4.1": "Multi-Objective Optimization",\n', "",
     DISABLED,
     "and the registry's live disabled set is the same eight, so the population is one "
     "thing and not two"),

    (26, "B4.2 Linear Programming (registry.DISABLED_CONCEPT_ONLY)",
     "B4.2 is a DISABLED concept-only module and stays disabled",
     REGISTRY, '    "B4.2": "Linear Programming",\n', "",
     DISABLED,
     "and the registry's live disabled set is the same eight, so the population is one "
     "thing and not two"),

    (27, "B4.5 Decision Sensitivity Matrix (registry.DISABLED_CONCEPT_ONLY)",
     "B4.5 is a DISABLED concept-only module and stays disabled",
     REGISTRY, '    "B4.5": "Decision Sensitivity Matrix",\n', "",
     DISABLED,
     "and the registry's live disabled set is the same eight, so the population is one "
     "thing and not two"),

    (28, "B4.6 Pareto Frontier Analysis (registry.DISABLED_CONCEPT_ONLY)",
     "B4.6 is a DISABLED concept-only module and stays disabled",
     REGISTRY, '    "B4.6": "Pareto Frontier Analysis",\n', "",
     DISABLED,
     "and the registry's live disabled set is the same eight, so the population is one "
     "thing and not two"),

    # ---------------------------------------------------------------- LEGACY PROXY
    (29, "Category-10 operational route (registry.VALIDATED via models_cat10.CAT10_CANONICAL)",
     "NO PRODUCTION ROUTE REACHES A LEGACY CATEGORY-10 PROXY. All seven resolve to canonical_v7 "
     "through models_cat10; the v19 runners are preserved for historical resolution only",
     CAT10,
     '    "B4.3": ("Constraint_Satisfaction",\n'
     '             _route("B4.3", "Constraint_Satisfaction", V7.constraint_satisfaction)),',
     '    "B4.3": ("Constraint_Satisfaction",\n'
     '             __import__("app.simulation.models_gov", fromlist=["x"])'
     '.run_constraint_satisfaction),',
     CYCLE8,
     "B4.3: and the ladder confirms it, moving neither index"),

    # ---------------------------------------------------------------- VERSION STAMP
    (30, "The analytical version line (models.SIMULATION_VERSION_HISTORY)",
     "the version history is APPEND-ONLY and a stamp is never duplicated or overwritten; the "
     "history must remain a strict prefix extension",
     MODELS,
     'SIMULATION_VERSION = "sim-2026.08-v20"',
     'SIMULATION_VERSION = "sim-2026.08-v19"',
     BOUNDARY,
     "the current stamp is sim-2026.08-v20"),

    # ---------------------------------------------------------------- PARTICIPANT PACKAGE
    (31, "The participant package predecessor records (v5 checksum record)",
     "A PREDECESSOR PACKAGE IS NEVER REGENERATED to match current bytes. Every predecessor is "
     "preserved exactly as it was served, and a change of bytes mints a SUCCESSOR instead",
     ROOT / "code_audit" / "run30_participant_package_v5_checksums.sha256",
     "dd1c6a327ca6b657eb4c891e022fd8f2efcb1d7b9d42f8b9fc6951ad4c5abb14  assets/css/radar.css",
     "0000000000000000000000000000000000000000000000000000000000000000  assets/css/radar.css",
     PARTICIPANT,
     "every one of v5's seventy checksums holds against commit"),

    # ---------------------------------------------------------------- SUPPLY PATH
    (32, "The governed decision-structure supply path (project_data.governed_structure_keys)",
     "A DECISION STRUCTURE THAT EXISTS ONLY IN TEST FIXTURES IS NOT SUPPLIED. Every Category-10 "
     "structure key is admitted by the real production intake or it has no production route",
     PROJECT_DATA,
     "            | set(V6_STRUCTURE_KEYS.values()) | set(V7_STRUCTURE_KEYS.values()))",
     "            | set(V6_STRUCTURE_KEYS.values()))",
     SUPPLY,
     "every governed Category-10 decision structure is admitted by the production intake"),
]


def main() -> int:
    HDR = ["fault_id", "module/system", "invariant", "baseline command", "mutation target",
           "mutation description", "mutation applied?", "fault command", "process exit code",
           "anchored RESULT present?", "expected RED reason", "actual RED reason", "crash?",
           "unrelated failure?", "restored?", "restored GREEN?", "final status", "notes"]
    rows = []
    tally = dict(attempted=0, applied=0, intended_red=0, restored_green=0,
                 not_applied=0, crashes=0, unrelated=0)

    for fid, system, invariant, target, old, new, guard, reason in FAULTS:
        tally["attempted"] += 1
        base_cmd = f"cd server/tools && python3 {guard}"
        notes = []

        # ---- BASELINE MUST BE GREEN BEFORE ANYTHING IS TOUCHED.
        clear_pycache()
        brc, bout, bres = run_guard(guard)
        if not is_green(bres):
            rows.append([fid, system, invariant, base_cmd, str(target), "-", "NO", base_cmd,
                         brc, "YES" if bres else "NO", reason, "-", "NO", "NO", "n/a", "NO",
                         "NOT_ATTEMPTED_BASELINE_RED",
                         f"baseline was not green ({bres}); no mutation was applied"])
            tally["not_applied"] += 1
            continue
        baseline_result = bres

        if target is None or old is None:
            # Faults 22, 23 and 31 have no single-string mutation site in this tree.
            rows.append([fid, system, invariant, base_cmd, "n/a", "no single-string mutation site",
                         "NO", base_cmd, "-", "YES", reason, "-", "NO", "NO", "n/a", "n/a",
                         "NOT_APPLIED",
                         "no byte-level mutation site was identified for this fault in this tree; "
                         "reported honestly rather than manufactured"])
            tally["not_applied"] += 1
            continue

        original = target.read_bytes()
        text = original.decode("utf-8")
        if text.count(old) != 1:
            rows.append([fid, system, invariant, base_cmd, str(target.relative_to(ROOT)),
                         "anchor not unique", "NO", base_cmd, "-", "YES", reason, "-", "NO",
                         "NO", "n/a", "n/a", "NOT_APPLIED",
                         f"the mutation anchor occurs {text.count(old)} times, not once"])
            tally["not_applied"] += 1
            continue

        # ---- APPLY, THEN VERIFY BY RE-READING THE BYTES FROM DISK.
        clear_pycache()
        target.write_bytes(text.replace(old, new, 1).encode("utf-8"))
        on_disk = target.read_bytes().decode("utf-8")
        applied = (new in on_disk if new else old not in on_disk) and on_disk != text
        if not applied:
            target.write_bytes(original)
            clear_pycache()
            rows.append([fid, system, invariant, base_cmd, str(target.relative_to(ROOT)),
                         "byte replacement", "NO", base_cmd, "-", "YES", reason, "-", "NO", "NO",
                         "YES", "n/a", "NOT_APPLIED",
                         "the mutation did not survive a re-read from disk"])
            tally["not_applied"] += 1
            continue
        tally["applied"] += 1

        # ---- RUN THE GUARD.
        frc, fout, fres = run_guard(guard)
        crash = fres is None
        red = (fres is not None) and (not is_green(fres))
        # THE INTENDED REASON MUST BE ONE OF THE GUARD'S OWN FAILING CHECKS. Matching against the
        # whole output would accept a PASSING line carrying the same words, and matching loosely
        # would accept an unrelated failure -- both are ways a check has lied here before.
        fails = failing_lines(fout)
        key = reason.strip().lower()
        hit = [f for f in fails if key in f.strip().lower()]
        intended = red and bool(hit)
        actual = ("no RESULT line (crash)" if crash else
                  ("; ".join(dict.fromkeys(f.strip()[:110] for f in fails)) or fres) if red
                  else "GREEN - guard did not notice")

        # ---- RESTORE BYTE FOR BYTE, CLEARING CACHE ON BOTH SIDES.
        clear_pycache()
        target.write_bytes(original)
        restored = target.read_bytes() == original
        clear_pycache()
        rrc, rout, rres = run_guard(guard)
        rgreen = is_green(rres) and rres == baseline_result

        if crash:
            tally["crashes"] += 1
            status = "CRASH_NOT_ACCEPTED_AS_RED"
            notes.append("the guard died without printing an anchored RESULT line; a crash is "
                         "NOT red and this fault is not counted")
        elif not red:
            status = "GUARD_DID_NOT_FIRE"
            notes.append("the guard stayed green under the mutation")
        elif not intended:
            tally["unrelated"] += 1
            status = "RED_FOR_AN_UNRELATED_REASON"
            notes.append("the guard went red but its output did not name the intended property; "
                         "an unrelated failure is NOT evidence")
        else:
            tally["intended_red"] += 1
            status = "RED_FOR_THE_INTENDED_REASON"
        if rgreen:
            tally["restored_green"] += 1
        else:
            notes.append(f"baseline did not return to {baseline_result} after restore (got {rres})")

        rows.append([fid, system, invariant, base_cmd, str(target.relative_to(ROOT)),
                     f"replace {old.strip().splitlines()[0][:70]!r}", "YES", base_cmd, frc,
                     "NO" if crash else "YES", reason, actual, "YES" if crash else "NO",
                     "YES" if (red and not intended) else "NO",
                     "YES" if restored else "NO", "YES" if rgreen else "NO", status,
                     "; ".join(notes) or "clean"])
        print(f"fault {fid:2d}  {status:32s}  {actual}")

    out = ROOT / "code_audit" / "run32_fault_injection_results.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HDR)
        w.writerows(rows)
    print()
    print("attempted        ", tally["attempted"])
    print("applied          ", tally["applied"])
    print("intended RED     ", tally["intended_red"])
    print("restored GREEN   ", tally["restored_green"])
    print("NOT_APPLIED      ", tally["not_applied"])
    print("crashes as RED   ", 0, f"({tally['crashes']} crash(es) recorded and NOT counted)")
    print("unrelated as RED ", 0, f"({tally['unrelated']} unrelated failure(s) recorded and NOT counted)")
    print("wrote", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
