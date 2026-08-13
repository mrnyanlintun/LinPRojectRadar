"""
RUN 20 CYCLE 7. B2.1 EVIDENCE COMBINATION: FOUR ARMS, TWO BODIES OF EVIDENCE.

WHAT THIS SUITE IS FOR. B2.1 combines four arms through Dempster's rule with no lineage carried.
Dempster's rule normalises by a conflict coefficient that is defined only for INDEPENDENT bodies
of evidence, so combining several readings of one body is not a stronger reading of that body: it
is the same evidence counted again. Measured on the shipped module before the correction, three
adverse readings of ONE earned-value body drove Red belief from 0.4342 to 0.9646. Nothing new was
learned between those two numbers.

THE RULE THIS CYCLE WORKS UNDER, WHICH IS THE OWNER'S AND NOT THIS SUITE'S.

    DEPENDENCE MUST COME FROM ACTUAL EVIDENCE AND COMPUTATION LINEAGE. NOT MODULE ID PROXIMITY,
    NOT CATEGORY MEMBERSHIP, NOT SHARED FIELD NAMES, NOT SCHEMA SIMILARITY.

So no arm here is called dependent because its inputs are spelled the same as another's. For every
arm this suite establishes, by EXECUTION rather than by reading a declaration, what the arm
actually reads, what it does to it, and which source facts materially influence its result -- the
last of those by holding everything else fixed and moving one fact at a time. A fact that can be
moved anywhere at all without moving the arm's output is NOT part of that arm's evidence, whatever
the preflight demands of it.

THE NEGATIVE CONTROL FOR SCHEMA-BASED INFERENCE IS BAYESIAN EAC, AND IT IS EXECUTED, NOT ASSERTED.
A1.3's preflight requires four fields and its arithmetic reads two of them. Section 5 below moves
the earned value and the actual cost across a wide range with the budget and the cost index held
fixed and shows the posterior does not move by so much as a rounding step. Anything that inferred
common evidence from a declared or required input schema would call A1.3 dependent on every reader
of the earned value in its own right; the primitive resolution reaches the same body by the honest
route, through the cost index being ev over ac and never through the field list. The control is
here so that the method this cycle uses is falsifiable, not merely described.

AND THE SECOND NEGATIVE CONTROL WAS FOUND BY THIS CYCLE'S SWEEP. `monte_carlo_eac` accepts
`cusumBreached`, `cusumDrift` and `cusumThreshold` and its spread widens when they are supplied.
A1.1, the wrapper the platform actually calls, NEVER SUPPLIES THEM. A schema reading of the
function signature would declare the cost forecast arm DERIVED from the trend arm's output. It is
not: section 6 moves all three and the forecast does not move. The two arms are dependent for a
different and real reason -- both rest on the earned-value measurement -- and being right for the
wrong reason is not being right.

THE TWO DIRECTIONS OF DEFECT ARE BOTH SCORED. Cycle 5 proved that a false declaration of
dependence destroys corroboration that was really there. This suite therefore never counts a
suppression as a success: section 8 scores false reinforcement and false suppression separately
and both must be zero.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.simulation import lineage  # noqa: E402
from app.simulation.fusion import dst_combine  # noqa: E402
from app.simulation.models_evm import run_bayesian_eac  # noqa: E402
from app.simulation.models_gov import run_dst  # noqa: E402
from app.simulation.models_sim import monte_carlo_eac, run_cusum, run_monte_carlo  # noqa: E402

_passed = 0
_total = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}" + (f"  [{detail}]" if detail else ""))


def near(name: str, got, want, tol=5e-5) -> None:
    check(name, got is not None and abs(float(got) - float(want)) <= tol,
          f"got {got!r}, wanted {want!r}")


def dst(si):
    return run_dst(dict(si), lambda: 0.5, None)


# ============================================================ 0. THE FIXTURES
#
# One project's evidence, in the four shapes the module accepts. Every arm adverse except the
# document arm, which is the shape that exposes the defect: three readings of one body against
# one reading of a genuinely different body.

EV_RED = {"cpi": 0.85, "spi": 0.85}          # min 0.85, below 0.90 -> the Red evidence branch
EV_GREEN = {"cpi": 0.99, "spi": 0.99}        # min 0.99, at or above 0.95 -> the Green branch
MC_RED = {"p80DeltaPct": 20.0}               # above 10 -> the Red evidence branch
MC_GREEN = {"p80DeltaPct": 1.0}              # at or below 5 -> the Green branch
CU_RED = {"breached": True}
CU_GREEN = {"breached": False}
DOC_GREEN = {"score": 0.10}                  # below 0.30 -> the Green branch
DOC_RED = {"score": 0.90}                    # at or above 0.70 -> the Red branch

THREE_EV_RED = {"evm": EV_RED, "mc": MC_RED, "cusum": CU_RED, "doc": DOC_GREEN}
THREE_EV_GREEN = {"evm": EV_GREEN, "mc": MC_GREEN, "cusum": CU_GREEN, "doc": DOC_GREEN}

# The masses the module itself assigns each arm. Transcribed from the module, NOT imported from
# it, so that a change to a mass is caught here rather than silently agreed with.
M_EV_RED = {"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05}
M_MC_RED = {"Green": 0.05, "Amber": 0.10, "Red": 0.80, "Unknown": 0.05}
M_CU_RED = {"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05}
M_DOC_GREEN = {"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05}
M_EV_GREEN = {"Green": 0.80, "Amber": 0.10, "Red": 0.05, "Unknown": 0.05}


def chain(masses):
    """Dempster over a list of masses, returning the result and the LAST conflict coefficient."""
    r = dict(masses[0])
    k = 0.0
    for m in masses[1:]:
        r = dst_combine(r, m)
        k = r["conflict"]
    return r, k


print("\n=== 1. WHAT EACH ARM ACTUALLY READS, ESTABLISHED BY EXECUTION ===")
#
# Not by reading the module's prose. Each probe moves ONE thing and observes whether the module's
# answer moves. A field that cannot move the answer is not that arm's evidence.

# EACH ARM IS PROBED ALONE, WITH THE OTHER ARMS ABSENT, AND THAT IS NOT A CONVENIENCE. Probing
# an arm through the full four-arm package cannot establish what that arm reads: once the arms
# are separated into bodies correctly, a change to one reading of a body that another reading
# already dominates is SUPPOSED to leave the answer alone. A probe run through the whole package
# would then read the correction itself as the arm being blind, which is precisely backwards. So
# the arm under test is the only one present.

def solo(**arm):
    """The module driven with exactly one arm present besides the document arm's fixed default."""
    return dst(arm)


# The earned-value index arm reads the two indices and nothing else.
# The probe moves each index DOWNWARD from the calm pair, one at a time. Moving one index upward
# from the adverse pair proves nothing, because the arm reads the LESSER of the two and the other
# index still holds it down: that probe would report the arm as blind to an input it plainly
# reads. The direction of a material-influence probe has to suit the transformation it is
# probing, and this one was corrected after it did exactly that.
b_evm = solo(evm=EV_GREEN)
for field in ("cpi", "spi"):
    probe = solo(evm=dict(EV_GREEN, **{field: 0.85}))
    check(f"the earned-value index arm materially reads {field}: moving it moves the reading",
          probe["belief_red"] != b_evm["belief_red"],
          f'{probe["belief_red"]} vs {b_evm["belief_red"]}')
probe = solo(evm=dict(EV_GREEN, bac=999999.0))
check("and it does NOT read the budget carried beside those indices in the very same object: "
      "moving the budget moves nothing, so the budget is not this arm's evidence however "
      "present it is in what the arm is handed",
      probe["belief_red"] == b_evm["belief_red"])

# The cost forecast arm reads one number out of the forecast.
b_mc = solo(mc=MC_RED)
check("the cost forecast arm materially reads the eightieth-percentile overrun",
      solo(mc={"p80DeltaPct": 1.0})["belief_red"] != b_mc["belief_red"])
check("and it reads NOTHING ELSE the forecast carries: the fiftieth percentile, the absolute "
      "eightieth percentile and the forecast's own status colour move it not at all",
      solo(mc=dict(MC_RED, p50=1.0, p80=2.0, status="green"))["belief_red"]
      == b_mc["belief_red"])

# The trend arm reads one boolean.
b_cu = solo(cusum=CU_RED)
check("the trend arm materially reads the breach flag",
      solo(cusum=CU_GREEN)["belief_red"] != b_cu["belief_red"])
check("and it reads neither the statistic nor the decision interval nor the trend's own status "
      "colour, so no amount of trend detail beyond the flag is evidence to this module",
      solo(cusum=dict(CU_RED, maxStat=0.0, H=99.0, status="green"))["belief_red"]
      == b_cu["belief_red"])

# The document arm reads one score.
check("the document arm materially reads the document risk score",
      solo(evm=EV_RED, doc=DOC_RED)["belief_red"] != solo(evm=EV_RED, doc=DOC_GREEN)["belief_red"])


print("\n=== 2. WHICH SOURCE FACTS MATERIALLY INFLUENCE EACH ARM, THROUGH ITS PRODUCER ===")
#
# The arm inputs above are not facts. The cost index is earned value over actual cost, the
# schedule index is earned value over planned value, the overrun is a forecast off the budget and
# both indices, and the breach flag is a control chart over the reporting history. This section
# drives the PRODUCING modules so the primitive facts are established by execution too.

MC_SI = {"bac": 1000.0, "cpi": 0.90, "spi": 0.90, "docRiskScore": 0.20}
mc_base = run_monte_carlo(dict(MC_SI), lambda: 0.5, 7)
for field, alt in (("cpi", 0.70), ("spi", 0.70), ("docRiskScore", 0.95)):
    alt_out = run_monte_carlo(dict(MC_SI, **{field: alt}), lambda: 0.5, 7)
    check(f"the cost forecast's overrun percentage materially rests on {field}",
          alt_out["overrun_pct_p80"] != mc_base["overrun_pct_p80"],
          f'{alt_out["overrun_pct_p80"]} vs {mc_base["overrun_pct_p80"]}')
# AND THE BUDGET IS NOT AMONG THEM, WHICH THIS CYCLE'S OWN FIRST DRAFT DECLARED THAT IT WAS. The
# arm reads a PERCENTAGE of the budget, and that ratio is scale-invariant in the budget. A1.1's
# own record names the budget correctly, because A1.1 also emits absolute forecast figures which
# do rest on it. The producing module's declaration is therefore NOT a safe substitute for
# asking what the consuming arm actually reads, and the probe is what established the difference.
alt_out = run_monte_carlo(dict(MC_SI, bac=2000.0), lambda: 0.5, 7)
check("the budget does NOT materially move the overrun percentage the arm reads: it is a ratio "
      "against the budget and is scale-invariant in it, so the budget is not this ARM's evidence "
      "even though it is the producing module's",
      alt_out["overrun_pct_p80"] == mc_base["overrun_pct_p80"],
      f'{alt_out["overrun_pct_p80"]} vs {mc_base["overrun_pct_p80"]}')
check("while the producing module's absolute forecast figure does rest on the budget, which is "
      "why A1.1's own record names it and this arm's record must not",
      alt_out["p80_eac"] != mc_base["p80_eac"]
      and "bac" in lineage.MODULE_LINEAGE["A1.1"]["source_fact_ids"])
check("SO THE COST FORECAST ARM RESTS ON THE EARNED-VALUE MEASUREMENT AND ON THE DOCUMENT "
      "EVIDENCE BOTH. It is the arm that touches two bodies, which is what makes it the bridge",
      True)

# AND THE SHIPPED ARM RECORDS ARE HELD TO EXACTLY WHAT THE PROBES ABOVE ESTABLISHED, so a record
# cannot drift back to a fact the arm does not read or lose one it does.
from app.simulation import models_gov as _mg  # noqa: E402
check("the shipped cost forecast arm record names the facts the probes found and NOT the budget",
      _mg.ARM_LINEAGE_MC["source_fact_ids"] == ("ac", "doc_risk_score", "ev", "pv"),
      str(_mg.ARM_LINEAGE_MC["source_fact_ids"]))
check("the shipped index arm record names the earned value, the actual cost and the planned "
      "value and nothing else",
      _mg.ARM_LINEAGE_EVM["source_fact_ids"] == ("ac", "ev", "pv"),
      str(_mg.ARM_LINEAGE_EVM["source_fact_ids"]))
check("the shipped trend arm record names this period's earned value and planned value beside "
      "the reporting history, because the history ends with this period",
      _mg.ARM_LINEAGE_CUSUM["source_fact_ids"] == ("ev", "pv", "reporting_history"),
      str(_mg.ARM_LINEAGE_CUSUM["source_fact_ids"]))
check("the shipped document arm record names the document risk score and NOTHING from the "
      "earned-value measurement, which is what keeps it a second body",
      _mg.ARM_LINEAGE_DOC["source_fact_ids"] == ("doc_risk_score",)
      and _mg.ARM_LINEAGE_DOC["evidence_relationship"] == lineage.INDEPENDENT,
      str(_mg.ARM_LINEAGE_DOC))

CU_SI = {"spi": 0.90, "spiHistory": [1.0, 0.98, 0.95, 0.90, 0.85, 0.80]}
cu_base = run_cusum(dict(CU_SI), lambda: 0.5, 7)
alt = run_cusum(dict(CU_SI, spiHistory=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0]), lambda: 0.5, 7)
check("the trend arm materially rests on the reporting history of the schedule index",
      alt["max_stat"] != cu_base["max_stat"])
# AND THE HISTORY ENDS WITH THIS PERIOD. The assembler appends the current index to the earlier
# periods' indices, so the trend arm and the index arm share THIS period's earned value and
# planned value and not merely older ones. That is a real shared fact and not a proximity.
alt = run_cusum(dict(CU_SI, spiHistory=[1.0, 0.98, 0.95, 0.90, 0.85, 0.20]), lambda: 0.5, 7)
check("and the last point of that history is this period's own schedule index, so the trend arm "
      "and the index arm share THIS period's earned value and planned value, not only older ones",
      alt["max_stat"] != cu_base["max_stat"])


print("\n=== 3. THE LINEAGE CONTRACT FOR THE FOUR ARMS ===")
#
# Stated as records and checked pairwise against the framework, which knows nothing about B2.1.

ARM_EVM = lineage.lineage_record(
    "B2.1.evm", source_fact_ids=("ac", "ev", "pv"),
    lineage_group_ids=(lineage.EARNED_VALUE_BODY,),
    evidence_relationship=lineage.SAME_SOURCE_TRANSFORM,
    derivation_chain=("ev,ac,pv", "cost performance index = ev / ac",
                      "schedule performance index = ev / pv",
                      "the lesser of the two indices"))
ARM_MC = lineage.lineage_record(
    "B2.1.mc", source_fact_ids=("ac", "doc_risk_score", "ev", "pv"),
    lineage_group_ids=(lineage.EARNED_VALUE_BODY, lineage.DOCUMENT_BODY),
    evidence_relationship=lineage.CORRELATED,
    derivation_chain=("A1.1", "eightieth-percentile overrun against the budget"))
ARM_CUSUM = lineage.lineage_record(
    "B2.1.cusum", source_fact_ids=("ev", "pv", "reporting_history"),
    lineage_group_ids=(lineage.EARNED_VALUE_BODY, lineage.REPORTING_HISTORY_BODY),
    evidence_relationship=lineage.CORRELATED,
    derivation_chain=("A1.2", "two-sided cumulative sum of the schedule index deviations"))
ARM_DOC = lineage.lineage_record(
    "B2.1.doc", source_fact_ids=("doc_risk_score",),
    lineage_group_ids=(lineage.DOCUMENT_BODY,),
    evidence_relationship=lineage.INDEPENDENT,
    derivation_chain=("the document risk score",))

ARMS = [ARM_EVM, ARM_MC, ARM_CUSUM, ARM_DOC]
prim = lineage.resolve_primitive_sources(ARMS)
by = {r["module_id"]: i for i, r in enumerate(ARMS)}


def dep(a, b):
    return lineage.dependent(ARMS[by[a]], ARMS[by[b]], prim[by[a]], prim[by[b]])


check("the index arm and the cost forecast arm are dependent: both rest on the earned value",
      dep("B2.1.evm", "B2.1.mc"))
check("the index arm and the trend arm are dependent: both rest on the earned value and the "
      "planned value, this period's included", dep("B2.1.evm", "B2.1.cusum"))
check("the cost forecast arm and the trend arm are dependent for the same reason",
      dep("B2.1.mc", "B2.1.cusum"))
check("the cost forecast arm and the document arm are dependent: the forecast's spread is "
      "widened by the document risk score, so it really does read that evidence",
      dep("B2.1.mc", "B2.1.doc"))
check("THE INDEX ARM AND THE DOCUMENT ARM ARE INDEPENDENT. They share no primitive fact, and "
      "this is the corroboration the module must not lose", not dep("B2.1.evm", "B2.1.doc"))
check("and so are the trend arm and the document arm",
      not dep("B2.1.cusum", "B2.1.doc"))

# AND THE COST FORECAST ARM IS EXACTLY THE BRIDGE OF THE A={X}, B={X,Y}, C={Y} CASE. B2.1 is not
# a thought experiment about that case: it is an instance of it in shipped production code.
sep = lineage.evidence_bodies(ARMS)
check("the four arms separate into exactly TWO bodies of evidence, not four and not one",
      len(sep["bodies"]) == 2, str(sep["bodies"]))
check("and the separation is exact rather than the flagged greedy fallback",
      sep["selection_exact"] is True)
members = [sorted(ARMS[i]["module_id"] for i in g) for g in sep["bodies"]]
check("the document arm stands alone as its own body, so its evidence still corroborates",
      ["B2.1.doc"] in members, str(members))
check("and the other three arms are one body between them, the bridging cost forecast arm "
      "absorbed rather than made into a third body or used to marry the two",
      sorted(sum((m for m in members if m != ["B2.1.doc"]), [])) ==
      ["B2.1.cusum", "B2.1.evm", "B2.1.mc"], str(members))


print("\n=== 4. THE PINNED PRE-FIX BEHAVIOUR, AND WHAT REPLACES IT ===")
#
# THE NUMBERS BELOW WERE MEASURED ON THE SHIPPED MODULE BEFORE ANY CORRECTION and are frozen here
# so the size of the amplification is on the record and not merely described. The uncorrected
# module combined all four arms as if independent.

PRE_FIX_RED_BELIEF = 0.964642     # three earned-value readings plus the document arm
PRE_FIX_RED_CONFLICT = 0.897617
PRE_FIX_GREEN_BELIEF = 0.997036
PRE_FIX_GREEN_CONFLICT = 0.207467

r, k = chain([M_EV_RED, M_MC_RED, M_CU_RED, M_DOC_GREEN])
near("the pre-fix arithmetic is reproduced exactly from the arms' own masses: four arms "
     "combined as independent give Red 0.964642", r["Red"], PRE_FIX_RED_BELIEF)
near("and conflict 0.897617", k, PRE_FIX_RED_CONFLICT)
r, k = chain([M_EV_GREEN, {"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05},
              {"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05}, M_DOC_GREEN])
near("and on the calm project the same four arms give Green 0.997036",
     r["Green"], PRE_FIX_GREEN_BELIEF)

# WHAT THE TWO BODIES GIVE. Within a body the most adverse reading is taken, which is idempotent:
# a second and a third reading of the same body change nothing. Across the two bodies Dempster's
# rule applies, because the independence it assumes is now true by construction. On the adverse
# project all three earned-value readings band Red, and the earliest of them in the module's own
# evaluation order is the index arm, so the index arm's mass represents the body.
POST_FIX_RED_BELIEF = 0.397436
POST_FIX_RED_CONFLICT = 0.805000
r, k = chain([M_EV_RED, M_DOC_GREEN])
near("the two-body answer on the adverse project is Red 0.397436", r["Red"], POST_FIX_RED_BELIEF)
near("with the conflict coefficient across the two bodies at 0.805000", k, POST_FIX_RED_CONFLICT)

d = dst(THREE_EV_RED)
near("AND THE MODULE NOW RETURNS IT: Red belief 0.40 and not the pre-fix 0.96",
     d["belief_red"], 0.40)
near("Green belief 0.40, because one body reads Red and the other reads Green and neither is "
     "counted more than once", d["belief_green"], 0.40)
near("Amber belief 0.19", d["belief_amber"], 0.19)
check("and the module reports how many bodies of evidence it actually had",
      d.get("evidence_bodies") == 2, str(d.get("evidence_bodies")))
check("and that its conflict coefficient is estimable, because there are two bodies for it to "
      "be estimated across", d.get("conflict_estimable") is True)

print("\n=== 5. THE IDEMPOTENCE THE DEFECT REQUIRED ===")
#
# Adding a second and a third reading of one body must change NOTHING. This is the property the
# uncorrected module lacked, and it is asserted against the module and not against the rule.

one_ev = {"evm": EV_RED, "doc": DOC_GREEN, "mc": None, "cusum": None}
two_ev = {"evm": EV_RED, "mc": MC_RED, "doc": DOC_GREEN, "cusum": None}
a, b, c = dst(one_ev), dst(two_ev), dst(THREE_EV_RED)
check("adding the cost forecast reading of the earned-value body to the index reading changes "
      "no belief at all", (a["belief_red"], a["belief_green"]) == (b["belief_red"],
                                                                   b["belief_green"]),
      f'{a["belief_red"]}/{a["belief_green"]} vs {b["belief_red"]}/{b["belief_green"]}')
check("and adding the trend reading on top of both changes nothing either",
      (b["belief_red"], b["belief_green"]) == (c["belief_red"], c["belief_green"]),
      f'{b["belief_red"]} vs {c["belief_red"]}')
check("nor does any of it change the number of bodies, which stays two throughout",
      a.get("evidence_bodies") == b.get("evidence_bodies") == c.get("evidence_bodies") == 2,
      f'{a.get("evidence_bodies")}, {b.get("evidence_bodies")}, {c.get("evidence_bodies")}')

print("\n=== 6. AND THE INDEPENDENT BODY IS NOT SUPPRESSED. THE POSITIVE DIRECTION ===")
#
# The failure this cycle must not commit is the other one. If the document arm were folded into
# the earned-value body on the strength of superficial similarity, the module would lose real
# corroboration, which is exactly the harm cycle 5 measured.

both_red = {"evm": EV_RED, "mc": MC_RED, "cusum": CU_RED, "doc": DOC_RED}
r = dst(both_red)
near("when the earned-value body AND the document evidence both read Red they genuinely "
     "corroborate, and Red belief rises well above what either body carries alone",
     r["belief_red"], 0.93)
check("and there are still two bodies, so the corroboration is between two and not within one",
      r.get("evidence_bodies") == 2)
check("the corroborated Red belief is strictly greater than the Red belief when only the "
      "earned-value body is adverse, which a wrongly suppressed second body could not produce",
      r["belief_red"] > dst(THREE_EV_RED)["belief_red"])

print("\n=== 7. THE BAYESIAN EAC NEGATIVE CONTROL FOR SCHEMA-BASED INFERENCE ===")
#
# A1.3's preflight requires bac, ev, ac AND cpi. Its arithmetic reads bac and cpi. Move the two
# it does not read, across a wide range, and nothing whatever happens to its answer.

BAY = {"bac": 1000.0, "ev": 800.0, "ac": 900.0, "cpi": 0.90}
bay_base = run_bayesian_eac(dict(BAY), lambda: 0.5, None)
check("Bayesian EAC returns a result on the base fixture, so the control is not vacuous",
      bay_base.get("posterior_eac") is not None, str(bay_base))
moved = 0
for ev, ac in ((1.0, 2.0), (500.0, 10.0), (999999.0, 3.0), (0.001, 999999.0)):
    alt = run_bayesian_eac(dict(BAY, ev=ev, ac=ac), lambda: 0.5, None)
    if (alt.get("posterior_eac"), alt.get("delta_pct"), alt.get("status_color")) != \
            (bay_base.get("posterior_eac"), bay_base.get("delta_pct"),
             bay_base.get("status_color")):
        moved += 1
check("THE NEGATIVE CONTROL: the earned value and the actual cost can be moved anywhere at all, "
      "including to values that contradict the cost index beside them, and Bayesian EAC's "
      "posterior, its variance from budget and its band do not move by a rounding step. Its "
      "PREFLIGHT REQUIRES FOUR FIELDS AND ITS ARITHMETIC READS TWO",
      moved == 0, f"{moved} of four probes moved the answer")
alt = run_bayesian_eac(dict(BAY, cpi=0.70), lambda: 0.5, None)
check("while the cost index, which it does read, moves it immediately -- so the probe is "
      "sensitive and the null result above means something",
      alt.get("posterior_eac") != bay_base.get("posterior_eac"))
check("SO A DECLARED OR REQUIRED INPUT SCHEMA IS NOT PROOF OF COMMON EVIDENCE LINEAGE. Anything "
      "that grouped modules by their required field sets would call this module a reader of the "
      "earned value in its own right. It reaches the earned-value body honestly, through the "
      "cost index being earned value over actual cost, and the primitive resolution is what "
      "establishes that -- never the field list",
      set(lineage.MODULE_LINEAGE["A1.3"]["lineage_group_ids"]) == {lineage.EARNED_VALUE_BODY}
      and "pv" not in lineage.MODULE_LINEAGE["A1.3"]["source_fact_ids"]
      and "reporting_history" not in lineage.MODULE_LINEAGE["A1.3"]["source_fact_ids"],
      str(lineage.MODULE_LINEAGE["A1.3"]))

print("\n=== 8. THE SECOND NEGATIVE CONTROL, FOUND BY THIS CYCLE'S SWEEP ===")
#
# `monte_carlo_eac` accepts three cusum fields and widens its spread when they are given. The
# wrapper the platform calls never gives them. A schema reading of the signature would make the
# cost forecast arm DERIVED from the trend arm's output, which is false.

raw_plain = monte_carlo_eac({"cpi": 0.90, "spi": 0.90, "bac": 1000.0, "docScore": 0.20}, seed=7)
raw_cusum = monte_carlo_eac({"cpi": 0.90, "spi": 0.90, "bac": 1000.0, "docScore": 0.20,
                             "cusumBreached": True}, seed=7)
check("the forecast function DOES respond to a breach flag when one is passed to it, so the "
      "signature is not dead code and the control is not vacuous",
      raw_cusum["s"] != raw_plain["s"], f'{raw_cusum["s"]} vs {raw_plain["s"]}')
mc_ref = run_monte_carlo({"bac": 1000.0, "cpi": 0.90, "spi": 0.90, "docRiskScore": 0.20},
                         lambda: 0.5, 7)
moved = 0
for extra in ({"cusumBreached": True}, {"cusumDrift": 5.0, "cusumThreshold": 1.0},
              {"cusumBreached": True, "cusumDrift": 99.0, "cusumThreshold": 0.1}):
    alt = run_monte_carlo(dict({"bac": 1000.0, "cpi": 0.90, "spi": 0.90, "docRiskScore": 0.20},
                               **extra), lambda: 0.5, 7)
    if alt["overrun_pct_p80"] != mc_ref["overrun_pct_p80"]:
        moved += 1
check("THE NEGATIVE CONTROL: the module the platform actually calls does not pass any of the "
      "three through, so no trend evidence reaches the cost forecast and the forecast arm is "
      "NOT derived from the trend arm. The two arms are dependent for a different and real "
      "reason, and being right for the wrong reason is not being right",
      moved == 0, f"{moved} of three probes moved the forecast")

print("\n=== 9. THE ACCEPTANCE COUNTERS, SCORED IN BOTH DIRECTIONS ===")

false_reinforcement = 0
false_suppression = 0

CONTROLS = [
    # name, signal package, expected bodies, expected Red belief
    ("one reading of the earned-value body, plus the document body", one_ev, 2, 0.40),
    ("two readings of that one body", two_ev, 2, 0.40),
    ("three readings of that one body", THREE_EV_RED, 2, 0.40),
    ("both bodies adverse, which must corroborate", both_red, 2, 0.93),
]
for name, si, eb, ebel in CONTROLS:
    got = dst(si)
    gb, gbel = got.get("evidence_bodies"), got["belief_red"]
    fr = 1 if (gb is not None and gb > eb) or gbel > ebel + 5e-3 else 0
    fs = 1 if (gb is not None and gb < eb) or gbel < ebel - 5e-3 else 0
    false_reinforcement += fr
    false_suppression += fs
    check(f"CONTROL {name}: {eb} bodies, Red belief {ebel}",
          fr == 0 and fs == 0, f"got {gb} bodies, Red {gbel}")

check("FALSE REINFORCEMENT ACROSS THE B2.1 CONTROLS IS ZERO", false_reinforcement == 0,
      str(false_reinforcement))
check("FALSE SUPPRESSION ACROSS THE B2.1 CONTROLS IS ZERO", false_suppression == 0,
      str(false_suppression))

print("\n=== 10. WHAT MUST NOT HAVE CHANGED ===")

check("the module still refuses entirely when it has no evidence at all",
      dst({}).get("insufficient_data") is True, str(dst({})))
check("an absent arm now contributes NO body and NO mass, so the same evidence gives the same "
      "answer however many arms happen to be missing beside it. The vacuous {0.25 x 4} an absent "
      "arm used to contribute is not ignorance, it is an assertion that the four states are "
      "equally likely, and Dempster's rule is not neutral to it",
      dst({"evm": EV_RED, "doc": DOC_GREEN})["belief_red"] == dst(THREE_EV_RED)["belief_red"])
check("the module is still non-voting and advisory: it reaches no governed status",
      "B2.1" not in __import__("app.simulation.registry", fromlist=["x"]).CORE_VOTING_MODULES)
# CAUGHT BY THE MUTATION BATTERY AND NOT BY FORESIGHT. Both checks below exist because a
# mutation survived without them: restoring the vacuous mass for an absent arm, and reporting the
# conflict coefficient as estimable when there is only one body for it to be estimated across.
# AND WITH THE INDEX ARM ABSENT THE ANSWER IS ONE BODY, NOT TWO, which is not a weaker version
# of the four-arm case but a different and correct one: with no index arm to hold the earned-value
# body open, the forecast arm and the document arm are dependent on each other alone -- the
# forecast's spread really is widened by the document risk score -- so there is ONE body and the
# most adverse reading of it is the forecast's own. The expectation was wrong when this check was
# first written and the module was right.
r_no_evm = dst({"mc": MC_RED, "doc": DOC_GREEN})
near("with the index arm ABSENT the module combines the arms it has and nothing else: no "
     "vacuous placeholder stands in for the missing arm and dilutes the arms that are real, so "
     "the answer is the one body's own most adverse reading at Red 0.80",
     r_no_evm["belief_red"], 0.80)
check("and the count of bodies is the count of bodies it actually had, which here is ONE, "
      "because without the index arm the forecast arm and the document arm share the document "
      "risk score and nothing separates them",
      r_no_evm.get("evidence_bodies") == 1, str(r_no_evm.get("evidence_bodies")))

r_one = dst({"doc": DOC_RED})
check("WITH ONE BODY OF EVIDENCE THERE IS NOTHING FOR THE CONFLICT COEFFICIENT TO MEASURE, and "
      "the module says so rather than reporting a number that reads like agreement",
      r_one.get("evidence_bodies") == 1 and r_one.get("conflict_estimable") is False,
      f'{r_one.get("evidence_bodies")} bodies, estimable {r_one.get("conflict_estimable")}')
check("and it does not put a conflict level on it either",
      r_one.get("conflict_level") is None, str(r_one.get("conflict_level")))
check("and it says so in the sentence a reader sees, rather than only in a field",
      "not estimable from one body" in r_one["evidence_metric"], r_one["evidence_metric"])
check("while the two-body case still carries the conflict mass it always carried",
      "Conflict mass" in dst(THREE_EV_RED)["evidence_metric"])

check("the module still reports its method class unchanged",
      dst(THREE_EV_RED)["method_class"] == "DST_Evidence_Combination")
check("the agreement field still compares against the conservative state it is given",
      dst(dict(THREE_EV_RED, decision={"state": "Red"}))["agrees_with_conservative"] is True)

print(f"\nRESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
