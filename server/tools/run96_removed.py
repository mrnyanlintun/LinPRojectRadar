"""
THE SEVENTY-ONE MODULES REMOVED FROM THIS REGISTRY, STATED BY NAME: RUN 96'S FIFTY-ONE AND
RUN 97'S TWENTY.

WHY THIS LIST IS WRITTEN OUT WHEN EVERY OTHER POPULATION IN THIS INSTRUMENT IS DERIVED.

Every count of modules IN SERVICE is derived from `p0-baseline/module_renumbering_map.csv`,
because a stated live population drifts from the computed one and this programme has made that
mistake nine times. This list is the opposite case and the reasoning inverts.

A check that asks the registry which modules are absent, and then asserts that those modules are
absent, cannot fail. Run 96 measured exactly that: with `A1.1` written back into the CSV, both
`test_run6_known_answer` and `test_run17_scientific_methods` went GREEN, because each had derived
its expectation of absence from the very file the restoration changed. The suites adapted to the
regression instead of reporting it.

So the ORACLE for a removal must be independent of the thing it audits, and for a removal the only
independent oracle is the record of what was removed. This file is that record. It is a historical
fact about one run, it does not change when the registry changes, and it is what makes putting a
retired row back a FAILURE rather than a silent widening.

It states nothing about which modules are in service. Nothing derives a live count from it.
"""
from __future__ import annotations

#: The identifiers whose registry rows, dispatch entries and specifications Run 96 deleted.
#: Established at run time from `registry.retired_modules()` at commit e852c46, less Group D.
REMOVED_AT_RUN96: tuple[str, ...] = (
    "A1.1", "A1.3", "A1.4", "A1.10",
    "A2.2", "A2.3", "A2.4", "A2.5", "A2.6", "A2.10", "A2.11",
    "A3.1", "A3.4", "A3.7", "A3.8", "A3.9",
    "A4.1", "A4.10",
    "A5.1", "A5.2", "A5.3", "A5.4", "A5.5", "A5.6", "A5.7", "A5.8",
    "B2.1", "B2.2", "B2.3", "B2.4", "B2.5", "B2.6", "B2.7", "B2.8", "B2.9",
    "B2.10", "B2.11", "B2.12", "B2.13", "B2.14", "B2.15", "B2.16", "B2.17",
    "B2.19", "B2.20",
    "B4.1", "B4.2", "B4.4", "B4.5", "B4.6", "B4.7",
)

#: The five Group D rows RUN 97 REMOVED, with the category D1 Portfolio Health itself.
#:
#: Run 96 stopped short of removing them and left them resolving, retired. The owner ruled in
#: Run 97 that the category goes: it computed nothing, rendered nowhere, and existed only
#: because code and checks were keyed to it. Its five modules compare projects against each
#: other -- they all required `portfolioVectors` -- which is outside the unit of analysis this
#: platform measures.
#:
#: THIS IS ALSO WHY THE LIST IS WRITTEN OUT. After Run 97 the registry holds NO retired module
#: at all, so `registry.retired_modules()` returns an empty mapping and every check that took
#: it as an oracle became one that cannot fail. These five names, here, are the oracle instead.
REMOVED_AT_RUN97: tuple[str, ...] = (
    # D1 Portfolio Health -- the five retired rows and the category, from goal one.
    "D1.1", "D1.2", "D1.3", "D1.4", "D1.5",
    # THE ADDENDUM: everything in service outside the five weighted performance categories,
    # less the three the owner named by function. B1.1 Conservative Dominance sets the official
    # status; B1.2 Weighted Voting is the comparison-only diagnostic the weight profile drives;
    # C1.5 Information Completeness Ratio is the Data Integrity eligibility gate. Those three
    # STAY. Everything below went, with its category where the category emptied.
    "B1.3", "B1.4",                                   # B1 Signal Synthesis (B1.1, B1.2 stay)
    "B2.18",                                          # B2 Evidence Combination -- category gone
    "B3.1", "B3.2", "B3.3", "B3.4", "B3.5",           # B3 Regulatory -- category gone
    "B4.3",                                           # B4 Decision Optimisation -- category gone
    "C1.1", "C1.2", "C1.3", "C1.4", "C1.6", "C1.7",   # C1 Data Integrity (C1.5 stays)
)

#: The categories removed with them. A category holding no module in service is not a category.
REMOVED_CATEGORIES_AT_RUN97: tuple[str, ...] = ("B2", "B3", "B4", "D1")

#: The three retained outside the five weighted performance categories, and the reason each is.
#: Written here so a reader of the removal roster can see what the boundary was.
RETAINED_OUTSIDE_THE_WEIGHTED: dict[str, str] = {
    "B1.1": "Conservative Dominance -- the rule that sets the official project status",
    "B1.2": "Weighted Voting -- comparison-only, in spec_projection.COMPARISON_ONLY_MODULES",
    "C1.5": "Information Completeness Ratio -- the Data Integrity eligibility gate; C1 is in "
            "models_gov.WEIGHTED_VOTING_EXCLUDED_CATEGORIES and does not reach the status",
}

#: Everything this registry has removed, from either run. Callers that only care that an
#: identifier is gone read this.
REMOVED: tuple[str, ...] = REMOVED_AT_RUN96 + REMOVED_AT_RUN97


def assert_removed(check, registry) -> None:
    """
    Assert the removal against the stated roster. `check(name, condition, detail)`.

    This is the check that goes red if a removed row is ever written back.
    """
    idx = registry.registry_index()
    back = sorted(m for m in REMOVED_AT_RUN96 if m in idx)
    check("every module Run 96 removed is still absent from the registry", not back,
          f"BACK IN THE REGISTRY: {back}" if back else "")
    check("the Run 96 removal roster is the fifty-one it records -- not silently shortened",
          len(REMOVED_AT_RUN96) == 51 and len(set(REMOVED_AT_RUN96)) == 51,
          str(len(REMOVED_AT_RUN96)))
    back97 = sorted(m for m in REMOVED_AT_RUN97 if m in idx)
    check("and every Group D row Run 97 removed is absent from the registry too",
          not back97, f"BACK IN THE REGISTRY: {back97}" if back97 else "")
    check("the Run 97 removal roster is the twenty it records -- D1's five and the addendum's "
          "fifteen -- not silently shortened",
          len(REMOVED_AT_RUN97) == 20 and len(set(REMOVED_AT_RUN97)) == 20,
          str(len(REMOVED_AT_RUN97)))
    # AND THE THREE RETAINED ONES ARE STILL THERE. Asserting only absences would pass on an
    # empty registry; this is the half that fails if the removal took one too many.
    gone = sorted(m for m in RETAINED_OUTSIDE_THE_WEIGHTED if m not in idx)
    check("and the three modules retained outside the five weighted categories all resolve: "
          + ", ".join(f"{m} ({why.split(' -- ')[0]})"
                      for m, why in RETAINED_OUTSIDE_THE_WEIGHTED.items()),
          not gone, f"MISSING: {gone}" if gone else "")
    # AND THE CATEGORY ITSELF. A registry that held a D1 module would have a D1 category; a
    # registry that holds a D1 CATEGORY with no module would still be D1 surviving. Both are
    # asserted, because only checking the modules lets the container come back empty.
    cats = {row.get("category") for row in idx.values()}
    back_cats = sorted(c for c in REMOVED_CATEGORIES_AT_RUN97 if c in cats)
    check("none of the removed categories is declared in the registry: "
          + ", ".join(REMOVED_CATEGORIES_AT_RUN97), not back_cats, str(sorted(cats)))
    # THE CONSEQUENCE OF ALL OF THE ABOVE, STATED SO THAT NO OTHER CHECK MAY TAKE THE RETIRED
    # SET AS AN ORACLE WITHOUT NOTICING IT IS EMPTY.
    check("the registry holds no retired module at all, which is why this file exists",
          registry.retired_modules() == {}, str(registry.retired_modules()))
    refused = []
    for mid in REMOVED:
        try:
            registry.run_module(mid, {}, lambda: 0.5, "2025-06-30")
        except registry.MissingModuleError:
            refused.append(mid)
        except Exception:                                              # noqa: BLE001
            pass
    check("and the dispatcher refuses every one of them by name",
          len(refused) == len(REMOVED),
          f"did not refuse: {sorted(set(REMOVED) - set(refused))}")
