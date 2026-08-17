"""
RUN 32'S PRODUCTION-CHANGE MANIFEST, THE CATEGORY-10 DECISION-OPTIMIZATION REMEDIATION.

Same construction and same property as every manifest before it: the union of all runs' manifests
must equal the differing set EXACTLY, no path may appear in two manifests, and one change may
never be counted as two.

THIS RUN IS OWNER-DIRECTED, on the same footing as Runs 28 through 31. The owner's supplied
Run-32 supervisory contract authorises implementing the supplied Category-10 canonical decision
contracts, extending the existing governed project-data intake with the decision structures those
methods are defined on, and abstaining where a project does not possess them -- for the
Category-10 scope and no wider.

THE GUARD WAS TURNED RED FIRST AND OBSERVED, before any of these declarations was written. It
reported exactly

    and no OTHER file has appeared in the simulation package undeclared:
        ['server/app/simulation/canonical_v7.py', 'server/app/simulation/models_cat10.py']

and the production-tree freeze guard reported

    {'added': ['server/app/simulation/canonical_v7.py',
               'server/app/simulation/models_cat10.py'],
     'removed': [], 'changed': ['server/app/project_data.py',
                                'server/app/simulation/models.py'], 'renamed': []}

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner supervisory method contract of 2026-08-17 for Run 32: implement the supplied "
          "Category-10 canonical decision-optimization contracts in the new analytical line, "
          "supply the governed decision structures those methods are defined on, hold the "
          "authority boundary so that no algorithm exercises human approval authority, and "
          "abstain where a project does not possess a governed decision problem")

#: EMPTY, AND THAT IS THE GUARD WORKING RATHER THAN A GAP. Both baseline-covered files Run 32
#: edited -- `models.py` and `project_data.py` -- are already declared by an earlier run's
#: manifest (Run 28 and Run 30 respectively), and no path may appear in two.
RUN32_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {}

#: Files Run 32 changed that the Run-20 freeze CANNOT cover, because they did not exist when it
#: was taken. EMPTY for the same reason as above.
RUN32_CHANGES_TO_POST_BASELINE_FILES: dict[str, tuple[str, str, str]] = {}

#: Production files Run 32 CREATED. The byte comparison structurally cannot reach these: a file
#: that did not exist when the Run-20 freeze was taken has no baseline row to differ from, so
#: without this declaration a new production file could appear in the simulation package with
#: nothing anywhere recording it. The guard reads this list alongside the earlier runs'.
RUN32_NEW_PRODUCTION_FILES: dict[str, str] = {
    "server/app/simulation/canonical_v7.py":
        "THE CANONICAL CATEGORY-10 DECISION LAYER, v20. Every one of the seven measures was "
        "named for a decision method it was not carrying out: Multi-Objective Optimization was a "
        "weighted blend of the cost index, the schedule index and a document risk score, with no "
        "alternatives and no feasible region; Linear Programming was a fixed rule score over a "
        "model with no decision variables and no constraint matrix; Constraint Satisfaction was "
        "a checklist of fixed index thresholds with no variables and no domains; the What-If "
        "Scenario Matrix was several completion-estimate formulas carrying no action identity, "
        "so nothing was being compared under anything; the Decision Sensitivity Matrix ranked "
        "today's deviations without perturbing or recomputing anything; and Pareto Frontier "
        "Analysis reported threshold booleans over a single project, when one point is not a "
        "trade space. This file implements each method as the method: dominance over an explicit "
        "alternative set, exact vertex enumeration over rationals for the linear program, a real "
        "variable/domain/constraint network, a complete action-by-scenario matrix, exact "
        "ranking-crossover solving, and the minimax regret rule. It REUSES the shared decision "
        "structure `canonical_v5.decision_problem` already defines for B2.18 MARCOS and B2.19 "
        "CRITIC-TOPSIS rather than minting a parallel model, so a decision result cannot drift "
        "from the alternatives it came from. NO PARAMETER IS INVENTED: preference weights, "
        "scenario probabilities, sensitivity ranges and tie-breaks must arrive in the governed "
        "structure or the method abstains, which is why no single best alternative is ever named "
        "and a tie returns its tie set rather than a winner.",
    "server/app/simulation/models_cat10.py":
        "THE SEVEN THIN OPERATIONAL RUNNERS. A correct canonical library behind an unchanged "
        "ledger is a failed remediation -- Run 30 proved that at cost, with `canonical_v5` "
        "reached on zero of twenty routes while every direct-call proof stayed green -- so this "
        "file is what makes the layer above operational. Each runner reads its module's governed "
        "structure, hands it to the canonical function and renders the answer; it performs NO "
        "arithmetic of its own and reads no cost index, schedule index or document risk score, "
        "so there is nowhere for a proxy to live. Every row it emits carries "
        "`result_class = ANALYTICAL_RESULT`, `human_authorization_required = True` and "
        "`creates_project_evidence = False`, and no row carries a status colour: a decision "
        "recommendation is not an observation about the project, it must not enter fusion, and "
        "no algorithm here may exercise the approval authority that remains the reviewer's.",
}
