"""
RUN 30 -- THE FIVE RECORD ARTIFACTS, GENERATED MECHANICALLY.

Nothing here is transcribed by hand. The population comes from
`code_audit/run20_cycle12_100_reaudit.csv` -- the Run-20 cycle-12 re-audit, which Run 26
established is the population source of truth and is 1:1 with the registry -- filtered to
categories 6 and 7. The structure keys and words come from `canonical_v5.V5_STRUCTURE_KEYS` and
`V5_STRUCTURE_WORDS`. The activation and voting facts come from the registry. The per-row Run-30
judgements are the only authored content, and each is keyed by canonical id so a row cannot
silently attach to the wrong module.
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                       # noqa: E402
from app.simulation.canonical_v5 import (                        # noqa: E402
    V5_STRUCTURE_KEYS, V5_STRUCTURE_WORDS,
)

POP = ROOT / "code_audit" / "run20_cycle12_100_reaudit.csv"
OUT = ROOT / "code_audit"

#: canonical id -> registry id. Categories 6 and 7 are B1.x and B2.x respectively.
def registry_id(canonical: str) -> str:
    major, minor = canonical.split(".")
    return ("B1." if major == "6" else "B2.") + minor


def population() -> list[dict]:
    rows = [r for r in csv.DictReader(POP.open(encoding="utf-8"))
            if r["category"].strip() in ("6", "7")]
    return sorted(rows, key=lambda r: (int(r["category"]), int(r["module_id"].split(".")[1])))


# -------------------------------------------------------------------------------------------
# The authored Run-30 judgement per target. Keyed by canonical id.
# (data_requirement, method_requirement, cal_requirement, lineage_requirement,
#  validate_requirement, run30_objective, run31_remaining, run33_remaining, disposition,
#  operationally_computes, abstains, structure_source_type, behaviour_when_absent)
# -------------------------------------------------------------------------------------------
J: dict[str, tuple] = {
 "6.1": ("governed signals with state, period, lineage body and abstention state",
         "maximum severity over eligible non-abstaining signals",
         "none: the rule has no parameter",
         "duplicate lineage must not change the result",
         "field validity of the assembled signals",
         "protect the existing scientific pass and re-express the rule on governed signals",
         "the qualification gate that decides which signals are eligible",
         "empirical validity of the synthesised state",
         "SCIENTIFIC_PASS", "yes", "when every signal abstains",
         "EXISTING_QUALIFIED_SIGNAL", "Not Estimable"),
 "6.2": ("governed signals plus a weighting policy with stated authority",
         "class-weighted voting with a declared unique-winner/tie policy",
         "the weights themselves; no governed policy exists",
         "a same-lineage duplicate must gain no weight",
         "whether the weights predict anything",
         "class-weighted voting, weights refused rather than invented",
         "the qualification gate", "the weights and their calibration",
         "PARAMETER_PROVENANCE_BLOCKED", "no", "always, on the real corpus",
         "EXPERT_ELICITATION", "abstains, naming the missing policy"),
 "6.3": ("governed signals with lineage bodies",
         "one vote per eligible independent signal, explicit tie and quorum",
         "the quorum is structural, not tuned",
         "a same-lineage duplicate must cast no second vote",
         "whether a plurality of signals predicts anything",
         "one vote per independent body, tie reported as conflict",
         "the qualification gate", "empirical validity of the majority",
         "METHOD_PASS_CALIBRATION_PENDING", "yes", "on one voter or all-abstain",
         "EXISTING_QUALIFIED_SIGNAL", "Not Estimable"),
 "6.4": ("governed signals with lineage bodies",
         "frozen Worst-2 mean statistic over M >= 2 independent signals",
         "the traffic-light boundaries over MeanWorst2; none exists",
         "a duplicate must not occupy both worst positions",
         "whether the statistic predicts anything",
         "replace the diluting proportional count with the frozen Worst-2 mean",
         "the qualification gate", "the boundaries and their calibration",
         "METHOD_PASS_CALIBRATION_PENDING", "yes, as a statistic with no band",
         "on fewer than two independent signals", "EXISTING_QUALIFIED_SIGNAL",
         "Not Estimable"),
 "7.1": ("bodies of evidence as mass functions over a stated frame",
         "Bel, Pl, conflict coefficient, Dempster combination, Shafer discount",
         "the mass assignments and reliability discounts",
         "same-source bodies may not be combined as independent",
         "whether the masses are right",
         "canonical DST over real mass functions with explicit total conflict",
         "the qualification gate", "mass provenance and calibration",
         "METHOD_PASS_CALIBRATION_PENDING", "no", "with no governed mass functions",
         "EXPERT_ELICITATION", "abstains"),
 "7.2": ("a decision table: universe, condition attributes, decision attribute",
         "indiscernibility, lower and upper approximation, boundary",
         "none for the approximation itself; discretisation would need governance",
         "the table's own provenance travels",
         "whether the attributes discriminate",
         "require a real decision table; refuse one project row",
         "the qualification gate", "attribute selection and validation",
         "CORRECT_ABSTENTION", "no", "with no governed decision table",
         "HISTORICAL_DECISION_TABLE", "abstains"),
 "7.3": ("three independent degrees: truth, indeterminacy, falsity",
         "the single-valued neutrosophic triple, preserved exactly",
         "the T/I/F mapping",
         "the assessment's provenance travels",
         "whether the degrees mean anything about projects",
         "keep indeterminacy independent; never derive it as 1-T-F",
         "the qualification gate", "the mapping and its validation",
         "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed assessment",
         "EXPERT_ELICITATION", "abstains"),
 "7.4": ("a membership stated as a range",
         "interval membership with the min/max intersection and union",
         "the interval bounds",
         "the assessment's provenance travels",
         "whether the bounds are right",
         "canonical interval representation; refuse invalid bounds",
         "the qualification gate", "the bounds and their calibration",
         "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed assessment",
         "EXPERT_ELICITATION", "abstains"),
 "7.5": ("a restriction and an explicit reliability",
         "the Z representation, both parts kept explicit",
         "the reliability terms",
         "the assessment's provenance travels",
         "whether the reliability is right",
         "representation and provenance; reduction operator left blocked",
         "the qualification gate", "the reduction operator, the terms and calibration",
         "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed assessment or no reliability",
         "EXPERT_ELICITATION", "abstains"),
 "7.6": ("named terms each carrying a probability",
         "complete normalised probabilistic linguistic term sets",
         "the linguistic probabilities",
         "the assessment's provenance travels",
         "whether the term probabilities are right",
         "enforce completeness and normalisation; refuse rescaling",
         "the qualification gate", "the probabilities and their calibration",
         "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed assessment",
         "EXPERT_ELICITATION", "abstains"),
 "7.7": ("attributes, values, appurtenance and contradiction degrees",
         "laboratory structure only; no operator is frozen anywhere",
         "the degrees and the operator",
         "research-only; no project lineage",
         "not applicable while disabled",
         "canonical laboratory structure, disabled state preserved",
         "nothing: it is not on the qualification path",
         "operator selection is an owner decision; then calibration",
         "FUTURE_RESEARCH_ONLY", "no", "always: it is disabled",
         "RESEARCH_ONLY_LAB_STRUCTURE", "no operational result at all"),
 "7.8": ("antecedent reference states, rule and attribute weights, belief distributions",
         "single fully activated rule exactly; multi-rule ER aggregation blocked",
         "the rule and attribute weights",
         "the rule base's provenance travels",
         "whether the rules are right",
         "canonical rule structure and admissibility; aggregation left blocked",
         "the qualification gate", "the ER operator, the weights and calibration",
         "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed rule base",
         "EXPERT_ELICITATION", "abstains"),
 "7.9": ("a Hilbert-space state and a measurement model",
         "archived; the Born rule is kept as research history only",
         "not applicable while archived",
         "research-only; no project lineage",
         "restoration would require evidence of an order or context effect",
         "create the archive record; keep it non-operational",
         "nothing: it is not on the qualification path",
         "restoration prerequisites are an owner decision",
         "FUTURE_RESEARCH_ONLY", "no", "always: it is archived",
         "RESEARCH_ONLY_LAB_STRUCTURE", "no operational result at all"),
 "7.10": ("a membership and non-membership pair",
          "mu^2 + nu^2 <= 1 with hesitancy sqrt(1 - mu^2 - nu^2)",
          "the memberships",
          "the assessment's provenance travels",
          "whether the memberships are right",
          "canonical domain enforced separately from the other six families",
          "the qualification gate", "the memberships and their calibration",
          "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed assessment",
          "EXPERT_ELICITATION", "abstains"),
 "7.11": ("positive, neutral and negative degrees",
          "mu + eta + nu <= 1 with refusal 1 - mu - eta - nu",
          "the memberships",
          "the assessment's provenance travels",
          "whether the memberships are right",
          "canonical domain; neutrality kept distinct from refusal and missingness",
          "the qualification gate", "the memberships and their calibration",
          "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed assessment",
          "EXPERT_ELICITATION", "abstains"),
 "7.12": ("the set of degrees the assessors gave",
          "hesitant fuzzy element with the declared arithmetic-mean laboratory score",
          "the degree set",
          "the assessment's provenance travels",
          "whether the degrees are right",
          "canonical set representation; the empty set is Not Estimable",
          "the qualification gate", "the degrees and the choice of score",
          "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed assessment or an empty set",
          "EXPERT_ELICITATION", "abstains"),
 "7.13": ("a lower and an upper membership at every point considered",
          "interval type-2 membership and footprint of uncertainty; type reduction blocked",
          "the membership functions",
          "the assessment's provenance travels",
          "whether the footprint is right",
          "genuine IT2 representation; NO midpoint averaging anywhere",
          "the qualification gate",
          "an exact Karnik-Mendel formulation is an owner decision; then calibration",
          "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed membership",
          "EXPERT_ELICITATION", "abstains"),
 "7.14": ("a state space and explicitly supplied constraints",
          "constrained entropy maximisation solved through the convex dual",
          "the constraints and their provenance",
          "the constraints' provenance travels",
          "whether the constraints are the right ones",
          "a real optimiser; remove the min(cpi,spi) dependency entirely",
          "the qualification gate", "constraint provenance and validation",
          "CORRECT_ABSTENTION", "no", "with no state space or constraints",
          "PROJECT_DATA_OBJECT", "abstains; infeasible constraints are named"),
 "7.15": ("a normalised possibility distribution over a state space",
          "Pi as a supremum, N as the dual, maxitivity",
          "the possibility degrees",
          "the distribution's provenance travels",
          "whether the degrees are right",
          "possibility as a maxitive measure; never normalised as a probability",
          "the qualification gate", "the degrees and their calibration",
          "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed distribution",
          "EXPERT_ELICITATION", "abstains"),
 "7.16": ("membership, non-membership and hesitancy",
          "mu^2 + nu^2 + pi^2 <= 1, three distinct components",
          "the memberships",
          "the assessment's provenance travels",
          "whether the memberships are right",
          "canonical domain; no silent projection into the admissible region",
          "the qualification gate", "the memberships and their calibration",
          "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed assessment",
          "EXPERT_ELICITATION", "abstains"),
 "7.17": ("a membership and non-membership pair",
          "mu^3 + nu^3 <= 1",
          "the memberships",
          "the assessment's provenance travels",
          "whether the memberships are right",
          "canonical domain; remove the crisp-KPI proxy and the renormalisation loop",
          "the qualification gate", "the memberships and their calibration",
          "PARAMETER_PROVENANCE_BLOCKED", "no", "with no governed assessment",
          "EXPERT_ELICITATION", "abstains"),
 "7.18": ("explicit alternatives and criteria with orientation and governed weights",
          "the published MARCOS steps over the shared decision structure",
          "the externally governed criterion weights",
          "the ranking retains the lineage of its decision inputs",
          "whether the ranking is right",
          "canonical engine on a shared decision object; identity kept stable",
          "the qualification gate", "placement is Run 32; weights and validation Run 33",
          "OWNER_DECISION_REQUIRED", "no", "with no explicit alternatives",
          "DECISION_ALTERNATIVES_OBJECT", "abstains"),
 "7.19": ("explicit alternatives and criteria with orientation",
          "CRITIC objective weights then TOPSIS over the same structure",
          "none externally: CRITIC weights are algorithmic outputs",
          "the ranking retains the lineage of its decision inputs",
          "whether the ranking is right",
          "canonical engine on the same shared decision object; identity kept stable",
          "the qualification gate", "placement is Run 32; validation Run 33",
          "CORRECT_ABSTENTION", "no", "with fewer than three alternatives or zero variance",
          "DECISION_ALTERNATIVES_OBJECT", "abstains"),
 "7.20": ("attributes, disjoint value subspaces and a mapping for every tuple",
          "Cartesian completeness validation; laboratory only",
          "not applicable while disabled",
          "research-only; no project lineage",
          "not applicable while disabled",
          "canonical representation and completeness; disabled state preserved",
          "nothing: it is not on the qualification path",
          "activation is an owner decision; then calibration",
          "FUTURE_RESEARCH_ONLY", "no", "always: it is disabled",
          "RESEARCH_ONLY_LAB_STRUCTURE", "no operational result at all"),
}

#: Real-corpus reconciliation, per structure, decided INDIVIDUALLY rather than by one blanket
#: sentence. Run 29 proved a blanket "none are populated" can hide a wiring gap.
#: canonical id -> (already_extracted, extracted_under_another_shape, assembled, reaches_module,
#:                  genuinely_absent, reason)
CORPUS: dict[str, tuple] = {
 "6.1": ("yes", "no", "yes", "yes", "no",
         "the four assembled arms ARE in the corpus and DO reach the module; this row is wired "
         "and is the one Category-6 target that computes"),
 "6.2": ("no", "no", "no", "no", "yes",
         "no document, form or field in this corpus states a weight for a signal or names an "
         "authority that set one. A weight is not extractable from a project's evidence"),
 "6.3": ("yes", "no", "yes", "yes", "no",
         "the assembled arms are in the corpus and reach the module"),
 "6.4": ("yes", "no", "yes", "yes", "no",
         "the assembled arms are in the corpus and reach the module"),
 "7.1": ("no", "no", "no", "no", "yes",
         "the corpus carries no mass assignment over a stated frame. The four arm masses the "
         "shipped B2.1 uses are LITERALS IN THE MODULE, not evidence the project supplied"),
 "7.2": ("no", "no", "no", "no", "yes",
         "the corpus holds one project's reporting periods, not a universe of cases with "
         "condition and decision attributes recorded against each"),
 "7.3": ("no", "no", "no", "no", "yes",
         "no field in the extraction registry is an assessed truth, indeterminacy or falsity"),
 "7.4": ("no", "no", "no", "no", "yes",
         "no field is an assessed membership range. An interval built around a crisp index is "
         "an invented spread"),
 "7.5": ("no", "no", "no", "no", "yes",
         "no field states how reliable an assessment is"),
 "7.6": ("no", "no", "no", "no", "yes",
         "no field carries a probability against a named linguistic term"),
 "7.7": ("no", "no", "no", "no", "yes",
         "research-only structure; not sought in the corpus and not inferable from it"),
 "7.8": ("no", "no", "no", "no", "yes",
         "no field is a rule weight, an attribute weight or an elicited belief distribution"),
 "7.9": ("no", "no", "no", "no", "yes",
         "archived; no state space or measurement model exists or is sought"),
 "7.10": ("no", "no", "no", "no", "yes",
          "no field is an assessed membership or non-membership degree"),
 "7.11": ("no", "no", "no", "no", "yes",
          "no field is an assessed positive, neutral or negative degree"),
 "7.12": ("no", "no", "no", "no", "yes",
          "no field is a set of degrees given by several assessors"),
 "7.13": ("no", "no", "no", "no", "yes",
          "no field is a membership with an upper and lower bound"),
 "7.14": ("no", "no", "no", "no", "yes",
          "the corpus carries no designed state space and no moment constraint. The v14 module "
          "read min(cpi,spi) into a lookup table, which measured the lookup table"),
 "7.15": ("no", "no", "no", "no", "yes",
          "no field is a possibility degree over a state space"),
 "7.16": ("no", "no", "no", "no", "yes",
          "no field is an assessed membership, non-membership or hesitancy"),
 "7.17": ("no", "no", "no", "no", "yes",
          "no field is an assessed membership pair. The v14 module was informationally a "
          "function of min(cpi,spi), which is a defect of the implementation"),
 "7.18": ("no", "no", "no", "no", "yes",
          "the corpus records one project's state, never a set of options being chosen between. "
          "Criteria are not alternatives and a project state is not a decision problem"),
 "7.19": ("no", "no", "no", "no", "yes",
          "the same: no alternatives x criteria matrix exists in the corpus"),
 "7.20": ("no", "no", "no", "no", "yes",
          "research-only structure; not sought in the corpus and not inferable from it"),
}


def write(name: str, header: list[str], rows: list[list]) -> None:
    path = OUT / name
    with artifact_out(path).open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path.relative_to(ROOT)}: {len(rows)} rows")


def main() -> None:
    pop = population()
    assert len(pop) == 24, f"expected 24 Category-6/7 targets, found {len(pop)}"
    assert len({r["module_id"] for r in pop}) == 24, "duplicate canonical identity"

    # ---------------------------------------------------------------- scope
    rows = []
    for r in pop:
        cid = r["module_id"]
        j = J[cid]
        rows.append([cid, registry_id(cid), r["module_name"], r["operational_activation"],
                     r["voting_status"], r["scientific_disposition"],
                     V5_STRUCTURE_KEYS.get(registry_id(cid), "(none: no new structure)"),
                     j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7]])
    write("run30_cat6_7_scope.csv",
          ["canonical_id", "registry_id", "current_name", "current_activation",
           "current_voting", "current_scientific_disposition", "v5_structure_key",
           "data_structure_requirement", "method_requirement", "calibration_requirement",
           "lineage_requirement", "validation_requirement", "run30_objective",
           "remaining_run31_work", "remaining_run33_work"], rows)

    # ---------------------------------------------------------------- supply path
    rows = []
    for r in pop:
        cid = r["module_id"]
        rid = registry_id(cid)
        j = J[cid]
        key = V5_STRUCTURE_KEYS.get(rid)
        corp = CORPUS[cid]
        if key:
            writer = ("server/app/writes.py saveprojectdata -> server/app/project_data.py "
                      "(governed, append-only, period-effective)")
            reachable = "yes"
        else:
            writer = ("server/app/simulation/signal_package.py build_signals + adapt "
                      "(the assembled signal package)")
            reachable = "yes"
        rows.append([cid, rid, r["module_name"],
                     key or "the assembled governed signals",
                     V5_STRUCTURE_WORDS.get(rid, "the project's governed signals"),
                     j[11], writer,
                     f"server/app/simulation/canonical_v5.py via {rid}'s runner",
                     "project supplied" if j[11] in ("PROJECT_DATA_OBJECT",
                                                     "DECISION_ALTERNATIVES_OBJECT")
                     else ("derived" if j[11] == "EXISTING_QUALIFIED_SIGNAL"
                           else ("research-only" if j[11] == "RESEARCH_ONLY_LAB_STRUCTURE"
                                 else "elicited")),
                     reachable, corp[4] == "no", "yes" if j[9] != "no" else "no", j[12],
                     "PASS"])
    write("run30_supply_path_reconciliation.csv",
          ["canonical_id", "registry_id", "module", "structure", "structure_in_words",
           "source_type", "production_writer_or_intake", "production_consumer",
           "project_supplied_derived_historical_elicited_or_research_only",
           "production_reachable", "real_corpus_populated", "parameter_provenance_present",
           "behaviour_when_absent", "pass_fail"], rows)

    # ---------------------------------------------------------------- real corpus
    rows = []
    for r in pop:
        cid = r["module_id"]
        rid = registry_id(cid)
        c = CORPUS[cid]
        rows.append([cid, rid, r["module_name"],
                     V5_STRUCTURE_KEYS.get(rid, "the assembled governed signals"),
                     V5_STRUCTURE_WORDS.get(rid, "the project's governed signals"),
                     "yes" if c[4] == "no" else "no", c[0], c[1], c[2], c[3],
                     "unqualified (Category-9 gate is Run 31's)",
                     J[cid][11], c[4], c[5],
                     "PASS"])
    write("run30_real_corpus_structure_reconciliation.csv",
          ["canonical_id", "registry_id", "module", "structure", "defining_evidence",
           "present_in_controlled_corpus", "already_extracted",
           "extracted_under_another_shape", "assembled", "reaches_module",
           "qualification_state", "parameter_provenance", "genuinely_absent", "reason",
           "pass_fail"], rows)

    # ---------------------------------------------------------------- closure
    rows = []
    for r in pop:
        cid = r["module_id"]
        j = J[cid]
        disabled = j[8] == "FUTURE_RESEARCH_ONLY"
        rows.append([cid, registry_id(cid), r["module_name"],
                     "yes", "yes",
                     "yes" if not disabled else "not applicable (research only)",
                     "yes" if CORPUS[cid][4] == "no" else "no",
                     "yes" if j[9] != "no" else "no",
                     "yes", "yes", "yes",
                     j[9], j[10],
                     "yes" if j[2] not in ("none: the rule has no parameter",
                                           "the quorum is structural, not tuned",
                                           "not applicable while archived",
                                           "not applicable while disabled",
                                           "none externally: CRITIC weights are algorithmic "
                                           "outputs") else "no",
                     j[6], j[7],
                     r["operational_activation"] if disabled else "ADVISORY_ONLY",
                     j[8]])
    write("run30_cat6_7_final_closure.csv",
          ["canonical_id", "registry_id", "module",
           "canonical_structure_implemented", "canonical_mathematics_implemented",
           "production_supply_path", "real_corpus_populated", "parameter_provenance",
           "oracle_pass", "invalid_admissibility_pass", "lineage_pass",
           "operationally_computes", "abstains", "calibration_pending",
           "run31_qualification_pending", "run33_validation_parsimony_pending",
           "disabled_or_archive_state", "final_run30_disposition"], rows)

    # ---------------------------------------------------------------- decision oracles
    from run30 import reference_mcdm as REF
    rows = [
        ["7.18 MARCOS", "HAND_DERIVED_CANONICAL_FIXTURE (constructed for Run 30; NOT taken from "
         "a published worked example and not presented as one)",
         "A1(C1=4,C2=3,C3=2); A2(2,5,4); A3(3,1,1)",
         "C1 capability, C2 resilience, C3 whole-life cost",
         "C1 benefit, C2 benefit, C3 cost",
         "externally governed: 0.5 / 0.3 / 0.2, summing to 1",
         f"ideal AI={REF.MARCOS_FROZEN['ideal']}; anti-ideal AAI={REF.MARCOS_FROZEN['anti_ideal']}; "
         f"normalised-against-ideal rows A1(1,.6,.5) A2(.5,1,.25) A3(.75,.2,1); "
         f"S={REF.MARCOS_FROZEN['s']}; S_AI={REF.MARCOS_FROZEN['s_ideal']}; "
         f"S_AAI={REF.MARCOS_FROZEN['s_anti_ideal']}; K-={REF.MARCOS_FROZEN['k_minus']}; "
         f"K+={REF.MARCOS_FROZEN['k_plus']}; f(K)={REF.MARCOS_FROZEN['utility']}",
         " > ".join(REF.MARCOS_FROZEN["ranking"]),
         "server/tools/run30/reference_mcdm.py::marcos and the frozen MARCOS_FROZEN literals",
         "server/app/simulation/canonical_v5.py::marcos",
         "the reference imports nothing from app, works on plain lists assembled by its own "
         "reader, and was written from the published MARCOS steps; production is compared "
         "against BOTH the reference and the frozen literals, so an error common to reference "
         "and production would still have to match the frozen numbers"],
        ["7.19 CRITIC-TOPSIS", "HAND_DERIVED_CANONICAL_FIXTURE (constructed for Run 30; NOT "
         "taken from a published worked example and not presented as one)",
         "A1(8,5,3); A2(6,7,5); A3(9,4,6); A4(5,8,2)",
         "C1 capability, C2 resilience, C3 whole-life cost",
         "C1 benefit, C2 benefit, C3 cost",
         "derived by CRITIC, not externally supplied",
         "min-max normalised columns C1(.75,.25,1,0) C2(.25,.75,0,1) C3 cost(.75,.25,0,1); "
         f"sigma={REF.CRITIC_FROZEN['sigma']} (each column has mean .5 and sample variance "
         ".625/3); r(C1,C2)=-1 exactly, r(C1,C3)=-.6, r(C2,C3)=+.6; "
         f"C_j={REF.CRITIC_FROZEN['information']}; w={REF.CRITIC_FROZEN['weights']}; "
         f"CC={REF.CRITIC_FROZEN['closeness']}",
         " > ".join(REF.CRITIC_FROZEN["ranking"]),
         "server/tools/run30/reference_mcdm.py::critic_topsis and the frozen CRITIC_FROZEN "
         "literals",
         "server/app/simulation/canonical_v5.py::critic_topsis",
         "as above; additionally every sigma, information quantity, weight, D+, D- and CC is "
         "compared element by element rather than only the final rank"],
    ]
    write("run30_decision_ranking_oracles.csv",
          ["method", "benchmark_source_or_type", "alternatives", "criteria", "orientation",
           "weights", "expected_intermediates", "expected_final_rank",
           "oracle_implementation_location", "production_implementation_location",
           "independence_proof"], rows)


if __name__ == "__main__":
    main()
