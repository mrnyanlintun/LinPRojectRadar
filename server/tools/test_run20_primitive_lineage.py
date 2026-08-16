"""
RUN 20 CYCLE 6: DEPENDENCE IS NOT TRANSITIVE, AND THE CLOSURE THAT SAID IT WAS IS REPLACED.

WHAT WAS WRONG. Cycles 3 to 5 separated signals into bodies of evidence by taking the CONNECTED
COMPONENTS of the dependence relation. That is a transitive closure, and it asserts that if A
depends on B and B depends on C then A depends on C. Dependence is not transitive. For A resting
on primitive source {X}, B on {X,Y} and C on {Y}, A and C share nothing at all.

THIS WAS NOT A THOUGHT EXPERIMENT ON THIS PLATFORM. The three signals exist in the shipped
declarations. A is the to-complete performance index on the earned-value measurement; C is the
overhead absorption rate on the indirect cost ledger, which cycle 5 had only just rescued from a
false dependence; B is the tornado risk ranking, which reads the earned-value indices AND the
progress figure that scales C's denominator. Measured on the closure, A and C alone were two
bodies worth 0.9273 and adding B collapsed all three into one body worth 0.7000. The bridging
signal destroyed real corroboration purely by existing, which is the same defect cycle 5 found in
a wrong declaration, arriving this time through the framework instead.

WHAT REPLACES IT. Bodies are a MAXIMUM SET OF PAIRWISE-INDEPENDENT signals; every other signal is
absorbed into exactly one body it depends on. Independence is decided on RESOLVED PRIMITIVE
SOURCE SETS, with derived, synthesized, quality, governance and decision outputs inheriting their
parents' primitives and creating none of their own.

THE VACUOUS-GUARD LESSON, APPLIED AGAIN. Every expected separation below is written by hand as an
explicit list of module-id sets. None is obtained by calling `evidence_bodies`, `dependent`,
`resolve_primitive_sources` or anything else in the file under test. Every frozen number is a
literal. And the controls run in BOTH directions: the suite fails if a false reinforcement
survives AND it fails if a genuine corroboration is suppressed, because a fix that flattens
everything to inert is not a fix.

THE PRODUCTION-DECLARATION LESSON, APPLIED AGAIN. Cycle 3's positive control was built from a
SYNTHETIC independent body written inside the test, so it proved the RULE could corroborate while
saying nothing about whether the shipped declarations had left anything to corroborate with.
Cycle 5 was the bill for that. Every control here that makes a claim about PRODUCTION behaviour
is driven from `lineage.MODULE_LINEAGE`. Synthetic records appear only where the claim is about
the RULE itself, and are named as such.
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from app.simulation import fusion, lineage  # noqa: E402

_passed = 0
_total = 0
_fail: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
    else:
        _fail.append(name + (f" -- {detail}" if detail else ""))


def near(name: str, got, want, tol=5e-5) -> None:
    check(name, got is not None and abs(float(got) - float(want)) <= tol,
          f"got {got!r}, expected {want!r}")


def sig(rec, status):
    return {"status": status, "lineage": rec, "module_id": rec["module_id"]}


def fuse(pairs):
    """pairs is a list of (lineage record, band)."""
    return fusion.fuse_signals([sig(r, b) for r, b in pairs])


def body_sets(result):
    """The separation as a set of frozensets of module ids, for comparison with a HAND-WRITTEN
    expectation. Reading the result object is not the same as asking the code under test what
    the answer should be."""
    return {frozenset(b["member_module_ids"]) for b in result["lineage_bodies"]}


def belief(result, band):
    return result["mass"][band]


PROD = lineage.MODULE_LINEAGE

# =========================================================== 0. THE FIELDS THE MODEL MUST CARRY
#
# The owner decision names the fields by name. A record missing one of them cannot express the
# distinction the rest of this suite tests, so their presence is checked before anything else.
REQUIRED_FIELDS = ("primitive_source_ids", "source_fact_ids", "source_document_ids",
                   "dependency_ids", "parent_signal_ids", "lineage_group_ids",
                   "evidence_relationship", "derivation_chain")
probe = lineage.lineage_record("PROBE", source_fact_ids=("x",))
for f in REQUIRED_FIELDS:
    check(f"the lineage record carries {f}", f in probe, str(sorted(probe)))
check("a record that declares no primitive sources separately takes its governed facts and "
      "documents as its primitive sources, rather than an empty set that would intersect "
      "nothing and read as independent of everything",
      probe["primitive_source_ids"] == ("x",), str(probe["primitive_source_ids"]))
for rel in ("INDEPENDENT", "SAME_SOURCE", "DERIVED", "SAME_SOURCE_TRANSFORM", "CORRELATED",
            "SYNTHESIZED", "QUALITY_METADATA", "GOVERNANCE_OUTPUT", "DECISION_OUTPUT"):
    check(f"the evidence relationship {rel} is in the vocabulary",
          rel in lineage.EVIDENCE_RELATIONSHIPS)

# ============================================ 1. THE CANONICAL A={X}, B={X,Y}, C={Y} ORACLE
#
# INDEPENDENT OF THE IMPLEMENTATION. These three records are built here, from first principles,
# with primitive sources stated directly. Nothing about them is read out of the production table
# or out of the code under test. The five results the owner decision requires are asserted as
# hand-written expectations.
A = lineage.lineage_record("ORACLE_A", primitive_source_ids=("X",),
                           evidence_relationship=lineage.INDEPENDENT)
B = lineage.lineage_record("ORACLE_B", primitive_source_ids=("X", "Y"),
                           evidence_relationship=lineage.CORRELATED)
C = lineage.lineage_record("ORACLE_C", primitive_source_ids=("Y",),
                           evidence_relationship=lineage.INDEPENDENT)

# The two-signal baselines, so the oracle's five claims are read against a measured single body
# and a measured genuine pair rather than against nothing.
ONE_BODY_AMBER = 0.7000       # what one body of Amber evidence carries, frozen
TWO_BODY_AMBER = 0.9273       # what two independent Amber bodies corroborate to, frozen
TWO_BODY_CONFLICT = 0.4414    # and the conflict coefficient across them, frozen

r_a = fuse([(A, "Amber")])
near("baseline: one body of Amber evidence carries 0.7000", belief(r_a, "Amber"), ONE_BODY_AMBER)

# ---- ORACLE CLAIM 1. A + B does not create independent corroboration.
r_ab = fuse([(A, "Amber"), (B, "Amber")])
check("ORACLE 1: A and B, whose primitive sources overlap on X, are ONE body and not two",
      body_sets(r_ab) == {frozenset({"ORACLE_A", "ORACLE_B"})}, str(body_sets(r_ab)))
near("ORACLE 1: and B therefore cannot independently corroborate A -- the belief stays at the "
     "single-body 0.7000 and does not reach the two-body 0.9273",
     belief(r_ab, "Amber"), ONE_BODY_AMBER)
check("ORACLE 1: with one body there is nothing for the conflict coefficient to measure and "
      "none is manufactured", r_ab["conflict_estimable"] is False and r_ab["conflict"] == 0.0)

# ---- ORACLE CLAIM 2. B + C does not create independent corroboration.
r_bc = fuse([(B, "Amber"), (C, "Amber")])
check("ORACLE 2: B and C, whose primitive sources overlap on Y, are ONE body and not two",
      body_sets(r_bc) == {frozenset({"ORACLE_B", "ORACLE_C"})}, str(body_sets(r_bc)))
near("ORACLE 2: and B therefore cannot independently corroborate C either",
     belief(r_bc, "Amber"), ONE_BODY_AMBER)

# ---- ORACLE CLAIM 3. A + C CAN create genuine corroboration. THE POSITIVE DIRECTION.
r_ac = fuse([(A, "Amber"), (C, "Amber")])
check("ORACLE 3: A and C hold DISJOINT primitive sources {X} and {Y} and are TWO bodies",
      body_sets(r_ac) == {frozenset({"ORACLE_A"}), frozenset({"ORACLE_C"})}, str(body_sets(r_ac)))
near("ORACLE 3: and they genuinely corroborate, reaching 0.9273 from 0.7000. A model that "
     "suppressed this would pass every negative check above and still be wrong",
     belief(r_ac, "Amber"), TWO_BODY_AMBER)
near("ORACLE 3: and the conflict coefficient across two real bodies is estimable at 0.4414",
     r_ac["conflict"], TWO_BODY_CONFLICT)
check("ORACLE 3: and it is reported as estimable", r_ac["conflict_estimable"] is True)

# ---- ORACLE CLAIM 4. A + B + C is not three independent bodies.
r_abc = fuse([(A, "Amber"), (B, "Amber"), (C, "Amber")])
check("ORACLE 4: A, B and C are TWO bodies and never three -- B is absorbed, not counted",
      len(r_abc["lineage_bodies"]) == 2, str(body_sets(r_abc)))
check("ORACLE 4: and the two bodies are A's and C's, with B absorbed into one of them and "
      "NOT merging them, which is exactly what the transitive closure got wrong",
      body_sets(r_abc) in ({frozenset({"ORACLE_A", "ORACLE_B"}), frozenset({"ORACLE_C"})},
                           {frozenset({"ORACLE_A"}), frozenset({"ORACLE_B", "ORACLE_C"})}),
      str(body_sets(r_abc)))

# ---- ORACLE CLAIM 5. Adding B to A + C cannot strengthen the result merely by bridging them.
near("ORACLE 5: adding the bridging signal B to A and C leaves the belief exactly where A and "
     "C put it, at 0.9273. It adds no strength by bridging",
     belief(r_abc, "Amber"), belief(r_ac, "Amber"))
near("ORACLE 5: and it leaves the conflict coefficient exactly where A and C put it",
     r_abc["conflict"], r_ac["conflict"])
check("ORACLE 5: nor does B weaken them -- the count of bodies is unchanged at two",
      len(r_abc["lineage_bodies"]) == len(r_ac["lineage_bodies"]))

# THE ORDER-INDEPENDENCE OF ALL FIVE. A separation that depended on the order the signals were
# handed over would be an artefact, and a greedy pass has exactly that fault: presented with B
# first it can select B and reject both A and C, collapsing two genuine bodies into one.
for order in ((B, A, C), (C, B, A), (B, C, A), (C, A, B), (A, C, B)):
    ro = fuse([(rec, "Amber") for rec in order])
    check("the separation does not depend on the order the signals arrive in: "
          + ",".join(r["module_id"] for r in order),
          len(ro["lineage_bodies"]) == 2 and abs(belief(ro, "Amber") - TWO_BODY_AMBER) < 5e-5,
          f'{len(ro["lineage_bodies"])} bodies, {belief(ro, "Amber")}')

# ============================== 2. THE SAME THREE SIGNALS, FROM THE SHIPPED PRODUCTION TABLE
#
# THE CONTROL THAT CYCLE 3 DID NOT HAVE. Everything above is synthetic and proves the RULE. This
# block proves the PRODUCTION BEHAVIOUR, using no record this file authored:
#   A = A1.7 to-complete performance index, on the earned-value measurement
#   B = A5.3 tornado risk ranking, which reads the earned-value indices AND the progress figure
#   C = A3.5 overhead absorption rate, on the indirect cost ledger
# A and C share NO primitive source. B touches both. On the connected-component treatment this
# measured 1 body and 0.7000; the numbers below are the frozen correct answers.
# RUN 29. B was the tornado ranking, which bridged the two bodies because it read the
# earned-value indices and the progress figure. It reads neither now -- it takes the sensitivity
# result as its only argument -- so it is no longer a bridge and the constructed bridge below is
# what drives the control. A and C are unchanged production records.
P_A, P_C = PROD["A1.7"], PROD["A3.5"]
check("production precondition: the to-complete index and the overhead absorption rate share "
      "no governed fact, so this is genuinely the A, C of the oracle and not a rigged pair",
      not (set(P_A["source_fact_ids"]) & set(P_C["source_fact_ids"])),
      f'{P_A["source_fact_ids"]} vs {P_C["source_fact_ids"]}')
# RUN 28 REMOVED THE PRODUCTION BRIDGE, AND THAT IS RECORDED HERE RATHER THAN WORKED AROUND.
# The tornado ranking bridged the earned-value body and the indirect-cost ledger because BOTH it
# and the overhead absorption rate read the reported progress figure. The owner's supplied
# Run-28 contract replaced overhead absorption with rates over an explicit allocation base, and
# progress is not an input it has any more, so the tornado ranking no longer shares a fact with
# it. Sweeping the whole table confirms NO record now bridges these two bodies.
#
# WHAT THAT MEANS FOR THIS CONTROL, STATED PLAINLY. The bridging defect this section exists to
# prove is gone cannot be driven from a production record any more, because production contains
# no bridge to drive it with. The two bodies A and C are still production records and are still
# genuinely disjoint, which is the half that matters and is asserted directly. The bridge is
# constructed, and it is constructed FROM THE TWO BODIES' OWN FACTS rather than from invented
# ones: it declares exactly one fact from each side, which is the minimum that makes something a
# bridge, so the control tests the partition rule and not a fiction about the corpus.
_bridges = sorted(m for m, r in PROD.items()
                  if m not in ("A1.7", "A3.5")
                  and set(r["source_fact_ids"]) & set(P_A["source_fact_ids"])
                  and set(r["source_fact_ids"]) & set(P_C["source_fact_ids"]))
check("production precondition: NO record in the shipped table now bridges the earned-value "
      "body and the indirect-cost ledger, because the overhead absorption rate no longer reads "
      "the progress figure the bridge ran through", not _bridges, str(_bridges))
P_B = lineage.lineage_record(
    "SYNTHETIC.BRIDGE",
    source_fact_ids=(sorted(P_A["source_fact_ids"])[0], sorted(P_C["source_fact_ids"])[0]),
    lineage_group_ids=("SYNTHETIC_BRIDGE",),
    evidence_relationship=lineage.CORRELATED,
    derivation_chain=("one fact from each of the two production bodies",))
check("the constructed bridge shares a fact with EACH of the two production bodies, so it is "
      "genuinely a bridge and not a third body",
      bool(set(P_B["source_fact_ids"]) & set(P_A["source_fact_ids"]))
      and bool(set(P_B["source_fact_ids"]) & set(P_C["source_fact_ids"])),
      str(P_B["source_fact_ids"]))

pr_ac = fuse([(P_A, "Amber"), (P_C, "Amber")])
near("THE AMBER POSITIVE CONTROL, UNCHANGED: an Amber to-complete index and an Amber overhead "
     "absorption are two bodies and corroborate to 0.9273",
     belief(pr_ac, "Amber"), TWO_BODY_AMBER)
near("and their conflict coefficient is estimable at 0.4414", pr_ac["conflict"], TWO_BODY_CONFLICT)

pr_abc = fuse([(P_A, "Amber"), (P_B, "Amber"), (P_C, "Amber")])
check("THE BRIDGING DEFECT IS GONE: adding the bridge leaves two bodies, "
      "where the connected-component treatment left one",
      len(pr_abc["lineage_bodies"]) == 2, str(body_sets(pr_abc)))
near("and the belief stays at 0.9273 rather than collapsing to the measured pre-fix 0.7000",
     belief(pr_abc, "Amber"), TWO_BODY_AMBER)
near("and the conflict coefficient stays estimable at 0.4414 rather than falling to the "
     "measured pre-fix 0.0000", pr_abc["conflict"], TWO_BODY_CONFLICT)

# ============================================ 3. THE TEN ACCEPTANCE CONTROLS
#
# Each names what it is controlling for and is scored on TWO counts, both of which must be zero:
#   false reinforcement -- a body appeared, or belief rose, where the evidence was not new
#   false suppression   -- a body was lost, or belief fell, where the evidence genuinely was new
# The two counts are accumulated and asserted to be zero at the end, as the acceptance test the
# owner decision names, rather than being left implicit in a pile of individual checks.
false_reinforcement = 0
false_suppression = 0
control_rows: list[tuple[str, int, int]] = []


def control(name, records, expect_bodies, expect_belief, band="Amber"):
    """Run one acceptance control and score it on both directions."""
    global false_reinforcement, false_suppression
    res = fuse([(r, band) for r in records])
    got_bodies = len(res["lineage_bodies"])
    got_belief = belief(res, band)
    fr = 1 if (got_bodies > expect_bodies or got_belief > expect_belief + 5e-5) else 0
    fs = 1 if (got_bodies < expect_bodies or got_belief < expect_belief - 5e-5) else 0
    false_reinforcement += fr
    false_suppression += fs
    control_rows.append((name, fr, fs))
    check(f"CONTROL {name}: {expect_bodies} body/bodies and belief {expect_belief:.4f}",
          fr == 0 and fs == 0, f"got {got_bodies} bodies, belief {got_belief!r}")
    return res


# The synthetic records the RULE-level controls need. Named so no reader mistakes them for
# production declarations.
DUP = lineage.lineage_record("SYN_DUPLICATE", primitive_source_ids=("X",),
                             evidence_relationship=lineage.SAME_SOURCE)
XFORM = lineage.lineage_record("SYN_TRANSFORM", primitive_source_ids=("X",),
                               evidence_relationship=lineage.SAME_SOURCE_TRANSFORM,
                               derivation_chain=("ORACLE_A", "a monotone rescale"))
DERIV = lineage.lineage_record("SYN_DERIVED", primitive_source_ids=(),
                               parent_signal_ids=("ORACLE_A",),
                               evidence_relationship=lineage.DERIVED,
                               derivation_chain=("ORACLE_A", "a metric over A's output"))
SYNTH = lineage.lineage_record("SYN_SYNTHESIS", primitive_source_ids=(),
                               dependency_ids=("ORACLE_A", "ORACLE_C"),
                               parent_signal_ids=("ORACLE_A", "ORACLE_C"),
                               evidence_relationship=lineage.SYNTHESIZED,
                               derivation_chain=("ORACLE_A", "ORACLE_C", "a roll-up"))
QUAL = lineage.lineage_record("SYN_QUALITY", primitive_source_ids=("X",),
                              evidence_relationship=lineage.QUALITY_METADATA)
GOVN = lineage.lineage_record("SYN_GOVERNANCE", primitive_source_ids=(),
                              parent_signal_ids=("ORACLE_A",),
                              evidence_relationship=lineage.GOVERNANCE_OUTPUT)
DECN = lineage.lineage_record("SYN_DECISION", primitive_source_ids=(),
                              parent_signal_ids=("ORACLE_A", "ORACLE_C"),
                              evidence_relationship=lineage.DECISION_OUTPUT)

# 1. SAME-SOURCE DUPLICATE. Production: the two voting modules, which read the same three facts.
control("same-source duplicate (production: the two voting modules)",
        [PROD["A1.7"], PROD["A1.8"]], 1, ONE_BODY_AMBER)
# 2. SAME-SOURCE TRANSFORM. RUN 29: the two contract-change readings are no longer one body --
#    A4.6 reads a governed change event register and B3.5 reads the extracted contract sums --
#    so the production pair that carried this control is the sensitivity model and the ranking
#    DERIVED from it, which share one body and produce two readings of it.
control("same-source transform (production: the sensitivity model and the ranking derived from "
        "it)", [PROD["A5.2"], PROD["A5.3"]], 1, ONE_BODY_AMBER)
# 3. DERIVED METRIC. A signal computed from another SIGNAL, holding no primitive of its own.
control("derived metric computed from a signal already present", [A, DERIV], 1, ONE_BODY_AMBER)
# 4. BRIDGING SIGNAL. RUN 29: the tornado ranking no longer touches the earned-value body at
#    all -- it reads A5.2's result and nothing else -- so it cannot bridge anything, and the
#    control is driven from the constructed bridge this section already builds from the two
#    bodies' OWN facts. Recorded rather than worked around: production now contains no bridge.
control("bridging signal (constructed from the two production bodies' own facts, because "
        "production contains no bridging record)", [P_A, P_B, P_C], 2, TWO_BODY_AMBER)
# 5. TWO GENUINELY INDEPENDENT BODIES. Production, and the direction a bad fix fails.
control("two genuinely independent evidence bodies (production: earned value and indirect cost)",
        [PROD["A1.7"], PROD["A3.5"]], 2, TWO_BODY_AMBER)
# 6. THE THREE-BODY CASE. RUN 29, as above: the middle signal is the constructed bridge.
control("three-signal A={X}, B={X,Y}, C={Y} (constructed bridge over two production bodies)",
        [P_A, P_B, P_C], 2, TWO_BODY_AMBER)
# 7. SYNTHESIZED-OUTPUT REUSE. A synthesis of A and C creates no new primitive evidence and must
#    not become a third body beside them.
control("synthesized-output reuse beside its own constituents", [A, C, SYNTH], 2, TWO_BODY_AMBER)
# 8. QUALITY-OUTPUT REUSE. Dropped as non-project evidence, never grouped.
r_q = control("quality-output reuse", [A, C, QUAL], 2, TWO_BODY_AMBER)
check("the quality output is DROPPED and reported as excluded, not quietly grouped",
      [e["module_id"] for e in r_q["excluded_non_evidential"]] == ["SYN_QUALITY"],
      str(r_q["excluded_non_evidential"]))
# 9. GOVERNANCE-OUTPUT FEEDBACK.
r_g = control("governance-output feedback", [A, C, GOVN], 2, TWO_BODY_AMBER)
check("the governance output is DROPPED and reported as excluded",
      [e["module_id"] for e in r_g["excluded_non_evidential"]] == ["SYN_GOVERNANCE"],
      str(r_g["excluded_non_evidential"]))
# 10. DECISION-OUTPUT FEEDBACK.
r_d = control("decision-output feedback", [A, C, DECN], 2, TWO_BODY_AMBER)
check("the decision output is DROPPED and reported as excluded",
      [e["module_id"] for e in r_d["excluded_non_evidential"]] == ["SYN_DECISION"],
      str(r_d["excluded_non_evidential"]))
# And the plain duplicate and transform against the synthetic A, so the RULE is controlled as
# well as the production instance.
control("same-source duplicate (rule level)", [A, DUP], 1, ONE_BODY_AMBER)
control("same-source transform (rule level)", [A, XFORM], 1, ONE_BODY_AMBER)

check("ACCEPTANCE: false duplicate reinforcement across every control is ZERO",
      false_reinforcement == 0,
      "; ".join(f"{n}" for n, fr, _ in control_rows if fr))
check("ACCEPTANCE: false suppression of genuine independent corroboration across every "
      "control is ZERO", false_suppression == 0,
      "; ".join(f"{n}" for n, _, fs in control_rows if fs))

# ================================================== 4. THE SYNTHESIS RULE, STATED SEPARATELY
#
# Rule 3 of the owner decision: a derived, synthesized, quality, governance or decision output
# creates NO NEW PRIMITIVE EVIDENCE. Asserted on the resolved sets directly, not through fusion,
# because a rule that only shows up in an aggregate can be satisfied by accident.
resolved = lineage.resolve_primitive_sources([A, C, SYNTH, DERIV])
check("a synthesis inherits its constituents' primitive sources and adds none of its own",
      resolved[2] == frozenset({"X", "Y"}), str(resolved[2]))
check("a derived metric inherits its parent's primitive sources and adds none of its own",
      resolved[3] == frozenset({"X"}), str(resolved[3]))
check("and a derived metric is therefore NOT independent of the signal it was derived from",
      lineage.dependent(A, DERIV, resolved[0], resolved[3]))
check("nor is a synthesis independent of either constituent",
      lineage.dependent(A, SYNTH, resolved[0], resolved[2])
      and lineage.dependent(C, SYNTH, resolved[1], resolved[2]))

# ================================================== 5. THE SHIPPED DECLARATIONS ARE THE TRUTH
#
# The declaration sweep, kept executable. Each declared module's primitive fact set is compared
# against a HAND-TRANSCRIBED reading of what the module's arithmetic actually consumes, taken
# from the model source and written out here. A declaration that drifts from the computation
# fails this, whichever direction it drifts in.
#
# The convention the table follows, stated once: a performance INDEX is not a fact. A module
# reading the cost performance index rests on earned value and actual cost and declares those;
# a module reading the schedule performance index rests on earned value and planned value.
ACTUAL_FACTS = {
    "A1.1": {"ac", "bac", "doc_risk_score", "ev", "pv"},      # bac, cpi, spi, docRiskScore
    "A1.2": {"ev", "pv", "reporting_history"},                # spi, spiHistory
    # RUN 28. Re-transcribed from the v3 arithmetic. A1.3 updates a stated prior against a
    # stated observation and touches no earned-value field; A1.4 filters the readings the
    # governed state-space model carries, with the two variances that model states.
    "A1.3": {"bayesian_observation", "bayesian_prior"},
    "A1.4": {"measurement_variance", "process_variance", "state_space_observations"},
    "A1.5": {"ac", "ev", "reporting_history"},                # cpi, cpiHistory -- NO pv
    "A1.7": {"ac", "bac", "ev"},                              # ac, bac, ev
    "A1.8": {"bac", "ev", "ac"},                              # bac, cpi
    # RUN 28. The progress figure is gone: overhead is absorbed over an explicit allocation
    # base and nothing is scaled by progress any more.
    "A3.5": {"allocation_base_driver", "indirect_cost_actual", "indirect_cost_plan"},
    # RUN 29. All three now compute from a governed STRUCTURE and read none of the scalar facts
    # transcribed here before. A record still naming those facts would declare a dependence that
    # is not there, which is exactly what this table exists to catch, so the transcription is
    # corrected to the empty set rather than left standing.
    "A4.6": set(),      # the governed change event register, not the extracted contract sums
    "A5.2": set(),      # the governed sensitivity model, not the earned-value scalars
    "A5.3": set(),      # A5.2's result, and nothing else at all
    "B3.5": {"baseline_contract_sum", "change_order_count", "revised_contract_sum"},
    "D1.5": set(),                                            # a synthesis holds no fact itself
    # RUN 20 CYCLE 8, THE ARCH.3 CLUSTERS. These records name their DIRECT facts here and reach
    # the rest through `derived_index_reads`, so the hand-transcribed set below is the direct
    # facts only and the index reads are transcribed separately in ACTUAL_INDEX_READS. Three of
    # them are the cycle's negative controls and are transcribed from what the arithmetic USES
    # and not from what the preflight demands: B3.2, B3.4 and B4.3 all demand the budget and
    # none of them reads it, because each reports a percentage OF the budget.
    # RUN 28. Re-transcribed from the v3 arithmetic. A1.11 reads two provenance-distinct
    # estimates and no earned-value field; A3.6 reads the budget as its base cost and the
    # register's own risk events, and no cost index.
    "A1.11": {"independent_eac", "management_eac"},
    "A3.6": {"bac", "risk_events"},
    "B3.2": set(),                         # the cost index alone; the budget scales out
    "B3.4": set(),                         # the two indices; the budget scales out
    "B4.3": set(),                         # the two indices; the budget scales out
    "B2.10": {"doc_risk_score"},
    "B2.11": {"doc_risk_score"},
    "B2.14": {"doc_risk_score"},           # the schedule index and the risk score; NOT the cost index
    "B2.15": {"doc_risk_score"},
    "B2.16": {"doc_risk_score"},
    "B2.18": {"doc_risk_score"},
    "B2.12": set(),
    "B2.13": set(),
    "B2.17": set(),
    # RUN 28. Re-transcribed: a named external price index and the cost exposure it applies to.
    "A3.9": {"cost_exposure", "external_price_index"},
}

#: The derived indices each record reads, hand-transcribed from the module's arithmetic. A record
#: naming an index it does not read would declare a dependence that is not there; one omitting an
#: index it does read would declare an independence that is not there. Both fail here.
# RUN 28. A1.11 and A3.6 are GONE from this table, because neither reads a derived index any
# more: the reconciliation index reads two separately prepared estimates and the cost risk
# analysis reads the register's events over the budget. A record naming an index it does not read
# would declare a dependence that is not there, which is what removing them prevents.
ACTUAL_INDEX_READS = {
    "B3.2": {"cost_index"},
    "B3.4": {"cost_index", "schedule_index"}, "B4.3": {"cost_index", "schedule_index"},
    "B2.10": {"cost_index", "schedule_index"}, "B2.11": {"cost_index", "schedule_index"},
    "B2.14": {"schedule_index"},
    "B2.15": {"cost_index", "schedule_index"}, "B2.16": {"cost_index", "schedule_index"},
    "B2.18": {"cost_index", "schedule_index"}, "B2.12": {"cost_index", "schedule_index"},
    "B2.13": {"cost_index", "schedule_index"}, "B2.17": {"cost_index", "schedule_index"},
}
for mid, expected_reads in sorted(ACTUAL_INDEX_READS.items()):
    rec = PROD.get(mid)
    check(f"{mid}: the declared derived-index reads are exactly what the module consumes",
          rec is not None and set(rec.get("derived_index_reads") or ()) == expected_reads,
          f'declared {sorted((rec or {}).get("derived_index_reads") or ())}')
check("no record declares a derived index the sweep has not transcribed",
      {m for m, r in PROD.items() if r.get("derived_index_reads")} == set(ACTUAL_INDEX_READS),
      str(sorted({m for m, r in PROD.items() if r.get("derived_index_reads")}
                 ^ set(ACTUAL_INDEX_READS))))
for mid, expected in sorted(ACTUAL_FACTS.items()):
    rec = PROD.get(mid)
    check(f"{mid} is declared in the shipped lineage table", rec is not None)
    if rec is not None:
        check(f"{mid}: the declared governed facts are exactly what the module consumes",
              set(rec["source_fact_ids"]) == expected,
              f'declared {sorted(rec["source_fact_ids"])}, consumes {sorted(expected)}')
check("the shipped table declares no module the sweep has not read against its computation, so "
      "a new declaration cannot arrive undocumented", set(PROD) == set(ACTUAL_FACTS),
      str(sorted(set(PROD) ^ set(ACTUAL_FACTS))))
# AND THE KEYS ARE REAL REGISTRY IDS. This is the defect that hid the false "PH.5" entry: it was
# keyed by an audit target id, so `lineage_for` could never return it and nothing exercised it.
# Checked against the registry itself rather than asserted, because an assertion of True is not
# a check and this programme has already paid for one of those.
from app.simulation import registry as _registry  # noqa: E402
_known = set(_registry.registry_index())
check("every key in the shipped table is a real registry module id, so no declaration can be "
      "written for a signal no consumer can ever look up",
      set(PROD) <= _known, str(sorted(set(PROD) - _known)))

# THE THREE CORRECTIONS THIS CYCLE MAKES, PINNED so a revert is a failure and not a silent
# regression to a table that reads plausibly and is false.
check("A1.3 no longer claims a reporting history it never reads",
      "REPORTING_HISTORY" not in " ".join(PROD["A1.3"]["lineage_group_ids"]),
      str(PROD["A1.3"]["lineage_group_ids"]))
check("A1.5 no longer claims a planned value it never reads",
      "pv" not in PROD["A1.5"]["source_fact_ids"], str(PROD["A1.5"]["source_fact_ids"]))
check("the portfolio synthesis is keyed by its registry id and not by an audit target id that "
      "no consumer could ever look up", "PH.5" not in PROD and "D1.5" in PROD)
check("and it declares the constituents it actually combines, not the two voting modules it "
      "has never touched",
      PROD["D1.5"]["dependency_ids"] == ("D1.2",), str(PROD["D1.5"]["dependency_ids"]))

# =================================================== 6. THE CLOSURE MUST NOT BE REINTRODUCIBLE
#
# The mutation the owner decision names first. If anything restores transitive closure, the
# oracle's claim 3 and claim 5 both break; this check states the structural half directly, so a
# reader does not have to infer it from a belief value.
check("the module exposes no transitive-closure partition for a consumer to reach for",
      not hasattr(lineage, "partition"), "lineage.partition still exists")
check("and it exposes the pairwise dependence predicate and the non-transitive separation",
      callable(getattr(lineage, "dependent", None))
      and callable(getattr(lineage, "evidence_bodies", None)))
# Dependence really is asked pairwise: A and C are not dependent even though both are dependent
# on B. Asserted on the predicate itself, which is where transitivity would have to live.
pr = lineage.resolve_primitive_sources([A, B, C])
check("the predicate itself says A and B are dependent", lineage.dependent(A, B, pr[0], pr[1]))
check("the predicate itself says B and C are dependent", lineage.dependent(B, C, pr[1], pr[2]))
check("and the predicate itself says A and C are NOT, which is the whole correction",
      not lineage.dependent(A, C, pr[0], pr[2]))

# ================================================== 7. THE SEPARATION IS EXACT, NOT GREEDY
r_exact = fuse([(A, "Amber"), (B, "Amber"), (C, "Amber")])
check("the separation reports that it was solved exactly rather than falling back",
      r_exact["body_selection_exact"] is True)

if _fail:
    print(f"\n{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
