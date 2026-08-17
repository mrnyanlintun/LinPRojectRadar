"""
RUN 32 FINAL CLOSURE. THE SEVEN CATEGORY-10 HELP ENTRIES, REWRITTEN FROM THE CANONICAL LAYER.

WHY THIS EXISTS. `assets/js/knowledge.js` is the reader-facing method handbook. Its seven
Category-10 entries still described the v19 PROXIES as though they were the current methods:
B4.1 as "normalises cost performance, schedule performance and document risk onto a common 0-1
scale", B4.3 as "checks the project against four fixed governance constraints", B4.7 as a fixed
regret matrix over monitor/investigate/escalate with a hard CPI/SPI override. None of that is
what the module does any more, and every one of those sentences was being presented to a reader
as current. That is the same defect class as the defensibility object's, on a different surface.

WHAT IS DERIVED AND WHAT IS NOT. The structure key and the reader's words for it come from
`canonical_v7.V7_STRUCTURE_KEYS` and `V7_STRUCTURE_WORDS`; the operational state comes from the
regenerated defensibility object's own derivation. The `ground` citations are LEFT UNCHANGED
where they were already citing the real method -- Savage 1951 for minimax regret, Pareto 1906 for
the frontier, Dantzig 1963 for linear programming -- because the canonical implementations now
actually perform those methods, so those citations became MORE accurate rather than less.

`bands` IS REMOVED FROM ALL SEVEN, and that is the point rather than a tidy-up. Every Category-10
row carries `status_color = None` and cannot reach status fusion, so a Red/Amber/Green ladder
beside it described a colour the module does not emit. The key is deleted rather than set to an
empty array, because `m.bands ? ... : ""` treats `[]` as truthy and would render an empty table.

Idempotent: running it twice changes nothing the second time.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "server"))

from app.simulation.canonical_v7 import V7_STRUCTURE_KEYS  # noqa: E402

TARGET = ROOT / "assets" / "js" / "knowledge.js"

NO_ACTION = ("It names no action and authorises nothing: the row is an analytical result, it "
             "carries no status colour, it cannot reach the governed status, and the decision "
             "remains the reviewer's.")

ENTRIES: dict[str, dict[str, str]] = {
    "B4.1": {
        "mc": "Multi_Objective_Optimization",
        "purpose": ("Reports which of an explicitly declared set of candidate alternatives are "
                    "non-dominated across the declared objectives, so the trade-offs stay "
                    "visible instead of being collapsed into a single score. It does not choose "
                    "between them."),
        "formula": ("Dominance over the declared alternative set: alternative a dominates b when "
                    "a is no worse than b on every objective and strictly better on at least "
                    "one, with each objective's benefit/cost orientation read from the declared "
                    "structure rather than assumed. Alternatives declared infeasible are "
                    "excluded before dominance is computed. No single best alternative is "
                    "selected, because choosing one from a non-dominated set requires preference "
                    "information that is not governed here."),
        "interp": ("A larger non-dominated set means the declared objectives genuinely conflict "
                   "and the choice is a trade-off rather than an optimisation. " + NO_ACTION),
    },
    "B4.2": {
        "mc": "Linear_Programming",
        "purpose": ("Solves a declared linear program exactly and reports the optimal vertex, the "
                    "objective value attained there, and which constraints are binding at it."),
        "formula": ("Exact vertex enumeration over rationals. An optimum of a bounded feasible "
                    "region lies at a vertex, and a vertex solves a square subsystem of the "
                    "binding constraints, so every candidate is solved with exact fraction "
                    "arithmetic and tested for feasibility against all declared constraints and "
                    "bounds, including non-negativity. There is no tolerance to choose and no "
                    "floating-point tie to resolve. An infeasible program is reported as "
                    "infeasible rather than as a number."),
        "interp": ("The binding constraints are the ones actually limiting the objective; "
                   "relaxing a non-binding constraint changes nothing. " + NO_ACTION),
    },
    "B4.3": {
        "mc": "Constraint_Satisfaction",
        "purpose": ("Classifies every complete assignment of the declared variables over their "
                    "declared domains as feasible or infeasible against the declared constraint "
                    "network, and reports which constraints each infeasible assignment violates."),
        "formula": ("A constraint satisfaction problem: variables, their domains, and constraints "
                    "over them. Every complete assignment is evaluated against every declared "
                    "constraint; no constraint may be skipped, and a constraint stated in a rule "
                    "form this method does not evaluate is refused rather than treated as "
                    "satisfied."),
        "interp": ("An empty feasible set means the declared constraints cannot all be met at "
                   "once, which is a statement about the declared problem and not a project "
                   "condition. " + NO_ACTION),
    },
    "B4.4": {
        "mc": "WhatIf_Scenario_Matrix",
        "purpose": ("Compares declared candidate actions against declared scenarios cell by cell, "
                    "so the outcome of each action under each future is visible side by side. It "
                    "applies no decision rule and recommends no action."),
        "formula": ("A complete action-by-scenario matrix: rows are candidate actions, columns "
                    "are scenarios, cells are outcomes. Every action must carry an identity and "
                    "every cell must be present -- an incomplete matrix is refused, because a "
                    "comparison across it would silently treat an unknown outcome as a known one. "
                    "Scenario probabilities are carried only where the structure supplies them, "
                    "and no expected value is computed without them."),
        "interp": ("A wide spread across a row means that action's outcome depends heavily on "
                   "which scenario occurs. " + NO_ACTION),
    },
    "B4.5": {
        "mc": "Decision_Sensitivity_Matrix",
        "purpose": ("Perturbs a declared decision model across a declared range and recomputes "
                    "the ranking of alternatives, reporting the exact parameter values at which "
                    "the ranking reverses."),
        "formula": ("A weighted-additive model over the declared criteria with one declared swept "
                    "parameter. The difference between two alternatives' scores is linear in that "
                    "parameter, so each crossover is solved exactly as a linear equation and "
                    "reported as an exact fraction rather than detected by sampling a grid. No "
                    "default weight and no default range is supplied: both arrive in the declared "
                    "structure or the method reports nothing."),
        "interp": ("A crossover inside the declared range means the preferred alternative depends "
                   "on a parameter value that has not been settled; no crossover means the "
                   "ranking is stable across the whole declared range. " + NO_ACTION),
    },
    "B4.6": {
        "mc": "Pareto_Frontier",
        "purpose": ("Reports which of the declared alternatives lie on the Pareto frontier of the "
                    "declared trade space and which are dominated, together with what dominates "
                    "each dominated point."),
        "formula": ("The same dominance relation as B4.1, asked of the trade space. An "
                    "alternative is on the frontier exactly when no other alternative dominates "
                    "it, which does not depend on the order the alternatives were offered in. "
                    "Identical objective vectors do not dominate one another, because dominance "
                    "requires a strict improvement somewhere, so duplicate points both remain on "
                    "the frontier."),
        "interp": ("A single point is not a trade space and produces no frontier. The frontier is "
                   "a property of the declared alternative set, not of the project. " + NO_ACTION),
    },
    "B4.7": {
        "mc": "Minimax_Regret_Decision_Rule",
        "purpose": ("Applies the minimax regret decision rule to a declared payoff or cost matrix "
                    "over candidate actions and future states, reporting each action's maximum "
                    "regret and which action minimises it."),
        "formula": ("Regret is the gap between an outcome and the best outcome available in the "
                    "same future state. For a payoff matrix R(a,s) = max_a P(a,s) - P(a,s); for a "
                    "cost matrix the best in a state is the minimum, so R(a,s) = P(a,s) - min_a "
                    "P(a,s). The reported alternative is argmin over actions of max over states "
                    "of R. The matrix's orientation is declared and never assumed. Where several "
                    "actions share the lowest maximum regret, all of them are returned and none "
                    "is chosen, because breaking the tie requires a preference that is not "
                    "governed here."),
        "interp": ("A low maximum regret means the action performs acceptably across every "
                   "declared future, not that it is best in any of them. " + NO_ACTION),
    },
}


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    changed = []
    for mid, spec in ENTRIES.items():
        key = V7_STRUCTURE_KEYS[mid]
        start = src.index(f'{{ n: "{mid}"')
        end = src.index('{ n: "', start + 10) if '{ n: "' in src[start + 10:] else None
        # The last entry of a list has no following entry; stop at the list terminator instead.
        stop = src.index("\n  ];", start) if end is None else end
        entry = src[start:stop]

        def repl(field: str, value: str, text: str) -> str:
            pat = re.compile(r'(\b%s: )"(?:[^"\\]|\\.)*"' % field, re.S)
            if not pat.search(text):
                return text
            return pat.sub(lambda m: m.group(1) + _js(value), text, count=1)

        new = entry
        new = re.sub(r'(mc: )"(?:[^"\\]|\\.)*"',
                     lambda m: m.group(1) + _js(spec["mc"]), new, count=1)
        for f in ("purpose", "formula", "interp"):
            new = repl(f, spec[f], new)
        new = repl("abstain",
                   f"the governed decision structure `{key}` is absent from the project, so the "
                   f"module returns Not Estimable rather than a reading.", new)
        new = repl("sources",
                   f"the governed `{key}` supplied through the project-data intake. The "
                   f"controlled document corpus does not carry a decision problem, so this "
                   f"module currently returns Not Estimable on real projects.", new)
        # REMOVE the band ladder entirely: this module emits no status colour.
        # The bands value is a LIST OF LISTS, so a non-greedy `\[.*?\],` stops at the first
        # inner `],` and leaves the remaining elements stranded as syntax garbage. Match the
        # outer array explicitly.
        new = re.sub(r'\n\s*bands: \[\[.*?\]\],', "", new, count=1, flags=re.S)
        if new != entry:
            src = src[:start] + new + src[stop:]
            changed.append(mid)
    TARGET.write_text(src, encoding="utf-8")
    print("rewritten:", ", ".join(changed) if changed else "(nothing; already current)")
    return 0


def _js(s: str) -> str:
    import json
    return json.dumps(s)


if __name__ == "__main__":
    raise SystemExit(main())
