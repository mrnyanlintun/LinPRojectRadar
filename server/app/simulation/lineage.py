"""
THE FRAMEWORK-LEVEL EVIDENCE LINEAGE MODEL.

WHY THIS FILE EXISTS AND WHY IT IS NOT PART OF THE COMBINATION RULE. Run 20 cycle 3 step one
measured, and pinned numerically, that one body of evidence counted twice sharpened belief from
0.7000 to 0.9273, and that the two modules which actually vote on project status are two
transforms of one body of earned-value evidence. The obvious repair is to patch the combination
rule so it notices the duplicate. That repair is refused here, because the combination rule is
not the only consumer that needs to know whether two signals are independent: a synthesis, a
governance projection, a decision card and an evidence qualification all have the same question
and would each have grown their own answer to it. So the lineage vocabulary lives HERE, in one
file that knows nothing about Dempster's rule, and every consumer reads the same partition.

WHAT A LINEAGE RECORD CARRIES. The supervisory clarification names the fields, and each is kept
for a reason that is not decorative:

  module_id             which analytical module emitted the signal
  source_fact_ids       the governed facts the signal ultimately rests on, NOT the immediate
                        arguments. A signal that reads a cost performance index rests on earned
                        value and actual cost, and it says so, because the index is not a fact.
  source_document_ids   the artefacts those facts were read from, where an identity exists
  dependency_ids        the other SIGNALS this one consumes
  lineage_group_ids     declared evidence bodies, for dependence a fact list cannot express
  evidence_relationship one of the nine classes below
  derivation_chain      the ordered transformations from the facts to the emitted value. For a
                        derived signal this is the whole point: recording only the final module
                        id loses exactly the information that proves two signals are one.

THE DEPENDENCE RULE, AND WHY IT IS NOT AN EQUIVALENCE. Two signals are evidentially dependent
when any of the following holds. The relation is PAIRWISE AND IS NEVER CLOSED TRANSITIVELY:

  1. their resolved PRIMITIVE SOURCE sets intersect;
  2. they share a declared lineage group id;
  3. one names the other as a parent signal or a dependency;
  4. one names the other in its derivation chain.

DEPENDENCE IS NOT TRANSITIVE, AND THE FIRST VERSION OF THIS FILE GOT THAT WRONG. It closed the
relation into connected components, which asserts that if A depends on B and B depends on C then
A depends on C. For A resting on primitive source {X}, B on {X,Y} and C on {Y} that is false: A
and C share nothing. Measured on this platform's own shipped declarations, the closure let one
bridging signal swallow two genuinely disjoint bodies and destroy corroboration that was really
there. `evidence_bodies` below replaces the closure, and the reason it is not merely patched is
that a closure has no correct version of itself.

Rule 1 is structural and deliberately NOT conditional on what the signals declare themselves to
be. A signal claiming INDEPENDENT while resting on a primitive source its neighbour also rests on
is not independent, and a claim is not evidence. Rules 2 to 4 exist because dependence can be
real without any shared source being recorded: a synthesis of two signals shares no raw fact with
either and must still never corroborate them.

AND PRIMITIVE SOURCES ARE RESOLVED, NOT TAKEN AT FACE VALUE. A derived, synthesized, quality,
governance or decision output creates no new primitive evidence: its primitive set is its
parents'. Carrying another module id does not manufacture a source.

WHAT THIS FILE DOES NOT DO. It assigns no weights, estimates no correlation coefficient and
carries no calibrated constant. There is nothing here to calibrate: the partition is a set
operation on declared identifiers, and the treatment of a partition is the consumer's decision,
stated in the consumer.
"""

from __future__ import annotations

from typing import Any, Iterable

# ----------------------------------------------------------------- the nine evidence relationships
#
# Each is a statement about the signal's relation to the evidence body it belongs to, not about
# its quality. A DERIVED signal is not worse than an INDEPENDENT one; it simply may not
# corroborate the thing it was derived from.

#: Rests on its own body of evidence. The only class that may corroborate another signal.
INDEPENDENT = "INDEPENDENT"
#: Reads the same governed facts as another signal, without transforming them.
SAME_SOURCE = "SAME_SOURCE"
#: Computed from another SIGNAL rather than from facts.
DERIVED = "DERIVED"
#: A deterministic transformation of the same governed facts another signal reads. The two
#: voting modules are this, which is why the class is named rather than folded into SAME_SOURCE.
SAME_SOURCE_TRANSFORM = "SAME_SOURCE_TRANSFORM"
#: Shares part of its evidence body with another signal without being a transform of it.
CORRELATED = "CORRELATED"
#: Produced by combining other signals. Never independent of any of its constituents.
SYNTHESIZED = "SYNTHESIZED"
#: A statement about the EVIDENCE, not about the project. Category 9 lives here.
QUALITY_METADATA = "QUALITY_METADATA"
#: A governance projection over signals that have already been counted.
GOVERNANCE_OUTPUT = "GOVERNANCE_OUTPUT"
#: A recommendation or decision-support output.
DECISION_OUTPUT = "DECISION_OUTPUT"

EVIDENCE_RELATIONSHIPS: tuple[str, ...] = (
    INDEPENDENT, SAME_SOURCE, DERIVED, SAME_SOURCE_TRANSFORM, CORRELATED,
    SYNTHESIZED, QUALITY_METADATA, GOVERNANCE_OUTPUT, DECISION_OUTPUT,
)

#: THE ANTI-FEEDBACK SET. These three are not project-condition evidence at all, whatever module
#: id they carry. A data-quality result says the evidence is thin, which is not the same claim as
#: the project being in trouble; a governance projection and a decision output are computed FROM
#: signals that have already been counted, so admitting them counts that evidence a second time
#: through a longer path. Specification 18 states the rule for Category 9 directly: its output is
#: qualification metadata and not another independent risk vote. A consumer of project condition
#: must drop these rather than group them, because grouping would still let them vote inside
#: whichever body they landed in.
NON_PROJECT_EVIDENCE: frozenset[str] = frozenset({
    QUALITY_METADATA, GOVERNANCE_OUTPUT, DECISION_OUTPUT,
})

#: The classes that assert dependence outright. Membership here is sufficient to refuse
#: corroboration; it is not necessary, because rule 3 of the partition can find dependence a
#: declaration has failed to mention.
DEPENDENT_RELATIONSHIPS: frozenset[str] = frozenset({
    SAME_SOURCE, DERIVED, SAME_SOURCE_TRANSFORM, CORRELATED, SYNTHESIZED,
})


class LineageError(ValueError):
    """An evidence relationship outside the vocabulary, which is never a silent default."""


def lineage_record(module_id: str,
                   source_fact_ids: Iterable[str] = (),
                   source_document_ids: Iterable[str] = (),
                   dependency_ids: Iterable[str] = (),
                   lineage_group_ids: Iterable[str] = (),
                   evidence_relationship: str = INDEPENDENT,
                   derivation_chain: Iterable[str] = (),
                   primitive_source_ids: Iterable[str] | None = None,
                   parent_signal_ids: Iterable[str] = (),
                   derived_index_reads: Iterable[str] = ()) -> dict[str, Any]:
    """
    Build one lineage record. Plain dicts rather than a class, because these are serialised into
    the stored compute result and read back by code that has no import of this module.

    An unrecognised relationship RAISES. There is no default: a signal whose relationship nobody
    declared would otherwise become INDEPENDENT by accident, which is the exact failure this
    file exists to prevent.
    """
    if evidence_relationship not in EVIDENCE_RELATIONSHIPS:
        raise LineageError(
            f"{module_id}: {evidence_relationship!r} is not one of the declared evidence "
            f"relationships {EVIDENCE_RELATIONSHIPS}")
    facts = tuple(sorted(set(source_fact_ids)))
    docs = tuple(sorted(set(source_document_ids)))
    # A signal that does not declare its primitive sources separately HAS its governed facts and
    # documents as its primitive sources. It is not given an empty set, because an empty
    # primitive set intersects nothing and would read as independent of everything.
    #
    # RUN 20 CYCLE 8. A record that names a DERIVED INDEX gets that index's ancestry folded into
    # its primitive set here, at build time, using the UNION for the schedule index. Folding it
    # in at build time rather than at read time means that every existing consumer -- including
    # the ones written before this field existed and never updated -- sees the dependence
    # without changing a line, and the narrowing by evidence is an improvement a consumer opts
    # into, never a correctness fix it has to remember to apply.
    reads = tuple(derived_index_reads)
    for name in reads:
        index_ancestry(name)  # raises on an index this model does not know, never a silent skip
    ancestry: set[str] = set()
    for name in reads:
        ancestry |= set(index_ancestry(name))
    prim = (tuple(sorted(set(primitive_source_ids) | ancestry))
            if primitive_source_ids is not None
            else tuple(sorted(set(facts) | set(docs) | ancestry)))
    return {
        "module_id": module_id,
        "primitive_source_ids": prim,
        "derived_index_reads": tuple(reads),
        "source_fact_ids": facts,
        "source_document_ids": docs,
        "dependency_ids": tuple(sorted(set(dependency_ids))),
        "parent_signal_ids": tuple(sorted(set(parent_signal_ids))),
        "lineage_group_ids": tuple(sorted(set(lineage_group_ids))),
        "evidence_relationship": evidence_relationship,
        "derivation_chain": tuple(derivation_chain),
    }


# ------------------------------------------------------ RUN 20 CYCLE 8. THE DERIVED-INDEX ANCESTRY
#
# WHY THIS EXISTS AND WHY A STATIC DECLARATION CANNOT REPLACE IT. `extraction_merge` derives the
# two indices every advisory cluster reads:
#
#     cost index     = earned value / actual cost
#     schedule index = earned value / planned value
#                      OR, WHEN NO PLANNED VALUE IS PRESENT,
#                      actual progress / planned progress
#
# THE SCHEDULE INDEX THEREFORE HAS TWO POSSIBLE ANCESTRIES, AND WHICH ONE APPLIES IS A PROPERTY
# OF THE PROJECT'S EVIDENCE AND NOT OF THE MODULE. Measured in cycle 8 by execution: with a
# planned value present, Maximum Entropy rests on the earned value; with the planned value
# absent, the same module on the same code rests on the two progress figures and does not touch
# the earned value at all. A lineage record keyed only by module id is therefore WRONG ON ONE OF
# THE TWO REGIMES no matter which ancestry it names -- falsely dependent on the progress readers
# in the first, or falsely independent of the earned-value readers in the second. Cycle 5 proved
# the first error destroys real corroboration and cycle 3 proved the second manufactures it.
#
# SO THE DECLARATION CARRIES THE UNION AND THE EVIDENCE NARROWS IT. A module that reads the
# schedule index declares `derived_index_reads` and gets the UNION of both ancestries, which is
# the conservative direction for a consumer that has no project evidence to hand: it can only
# refuse corroboration, never manufacture it. A consumer that HAS the evidence -- and every
# production consumer does -- calls `resolve_for_evidence` and gets the exact ancestry. The two
# are not two opinions about dependence: the union is the honest statement of what is known
# without the evidence, and the narrowing is what the evidence adds.

#: The ancestry of the cost index. It has only one.
COST_INDEX_ANCESTRY: tuple[str, ...] = ("ac", "ev")
#: The schedule index when a planned value is present.
SCHEDULE_INDEX_ANCESTRY_PV: tuple[str, ...] = ("ev", "pv")
#: The schedule index when it is not, which is the fallback `extraction_merge` applies.
SCHEDULE_INDEX_ANCESTRY_PROGRESS: tuple[str, ...] = ("actual_pct_complete",
                                                    "planned_pct_complete")
#: What a record declares before any project evidence narrows it.
SCHEDULE_INDEX_ANCESTRY_UNION: tuple[str, ...] = tuple(sorted(
    set(SCHEDULE_INDEX_ANCESTRY_PV) | set(SCHEDULE_INDEX_ANCESTRY_PROGRESS)))

#: The two tokens a record may name in `derived_index_reads`.
COST_INDEX = "cost_index"
SCHEDULE_INDEX = "schedule_index"


def index_ancestry(index_name: str, si: dict | None = None) -> tuple[str, ...]:
    """The primitive facts one derived index rests on, narrowed by evidence when evidence is given.

    With `si` omitted the schedule index returns the UNION of its two ancestries, which is the
    only honest answer without the project's evidence in hand.

    The branch reproduces `extraction_merge`'s own condition and the suite asserts the two still
    agree, by deriving both from the same fact dictionaries rather than by reading this comment.
    """
    if index_name == COST_INDEX:
        return COST_INDEX_ANCESTRY
    if index_name != SCHEDULE_INDEX:
        raise LineageError(f"{index_name!r} is not a derived index this model knows")
    if si is None:
        return SCHEDULE_INDEX_ANCESTRY_UNION
    ev, pv = si.get("ev"), si.get("pv")
    if ev is not None and pv not in (None, 0):
        return SCHEDULE_INDEX_ANCESTRY_PV
    apc, ppc = si.get("actualPctComplete"), si.get("plannedPctComplete")
    if apc is not None and ppc not in (None, 0):
        return SCHEDULE_INDEX_ANCESTRY_PROGRESS
    # Neither ancestry is available, so the index does not exist on this project and rests on
    # nothing. An empty tuple here is NOT an independence claim: a module whose index is absent
    # emits no reading at all, so there is no signal for anything to corroborate.
    return ()


def resolve_for_evidence(record: dict, si: dict | None) -> dict:
    """Narrow one record's derived-index ancestry against the project's actual evidence.

    A record that declares no derived index is returned unchanged. Nothing is ever ADDED here:
    the resolution can only replace the declared union with the branch the evidence selects, so
    a resolved record's primitive set is always a subset of its declared one.
    """
    reads = tuple(record.get("derived_index_reads") or ())
    if not reads:
        return dict(record)
    out = dict(record)
    # THE BASE IS THE RECORD'S DIRECT FACTS, NOT ITS DECLARED PRIMITIVE SET. Subtracting an
    # ancestry out of the primitive set would delete a fact the module reads DIRECTLY whenever
    # that fact also happens to sit under an index it reads, which is a silent loss of real
    # evidence. Rebuilding from the direct facts cannot do that.
    resolved = set(record["source_fact_ids"]) | set(record["source_document_ids"])
    for name in reads:
        resolved |= set(index_ancestry(name, si))
    out["primitive_source_ids"] = tuple(sorted(resolved))
    return out


def resolve_records_for_evidence(records: list[dict], si: dict | None) -> list[dict]:
    """`resolve_for_evidence` over a list, for a consumer that partitions a whole signal set."""
    return [resolve_for_evidence(r, si) for r in records]


def resolve_primitive_sources(records: list[dict]) -> list[frozenset[str]]:
    """
    THE SYNTHESIS RULE, RULE 3 OF THE OWNER DECISION, APPLIED ONCE FOR EVERYONE.

    A derived, synthesized, quality, governance or decision output CREATES NO NEW PRIMITIVE
    EVIDENCE. Its primitive source set is the union of its parents' primitive source sets, and
    nothing else. Carrying a different module id does not manufacture a source.

    The resolution walks parent_signal_ids and dependency_ids to a fixed point, so a synthesis of
    a synthesis still reaches the raw sources underneath. A cycle cannot inflate anything,
    because the operation is a union and the iteration stops when nothing grows.

    A signal that names a parent this set does not contain keeps its own declared primitives and
    additionally carries the parent's NAME as a primitive marker, so that dependence on an
    out-of-set parent is still expressible rather than silently lost.
    """
    by_id = {r["module_id"]: i for i, r in enumerate(records)}
    prim = [set(r["primitive_source_ids"]) for r in records]
    for i, r in enumerate(records):
        for parent in tuple(r["parent_signal_ids"]) + tuple(r["dependency_ids"]):
            if parent not in by_id:
                prim[i].add("signal:" + parent)
    for _ in range(len(records) + 1):
        grew = False
        for i, r in enumerate(records):
            for parent in tuple(r["parent_signal_ids"]) + tuple(r["dependency_ids"]):
                j = by_id.get(parent)
                if j is not None and not prim[j] <= prim[i]:
                    prim[i] |= prim[j]
                    grew = True
        if not grew:
            break
    return [frozenset(p) for p in prim]


def dependent(a: dict, b: dict, prim_a: frozenset[str], prim_b: frozenset[str]) -> bool:
    """
    ARE THESE TWO SIGNALS EVIDENTIALLY DEPENDENT? A PAIRWISE QUESTION, ASKED PAIRWISE.

    THIS RELATION IS DELIBERATELY NOT CLOSED TRANSITIVELY, AND THAT IS THE WHOLE POINT OF THIS
    FILE'S SECOND VERSION. Dependence is not transitive. For A resting on primitive source {X},
    B on {X,Y} and C on {Y}: A and B are dependent, B and C are dependent, and A and C are NOT.
    A bridging signal depends on both bodies it draws from; it does not marry them.

    Four rules, each a direct statement about shared evidence and none of them an inference from
    a module id:

      1. their resolved PRIMITIVE SOURCE sets intersect;
      2. they share a declared lineage group id;
      3. one names the other as a parent signal or a dependency;
      4. one names the other in its derivation chain.

    Rule 1 is structural and is NOT conditional on what either signal declares itself to be. A
    signal claiming INDEPENDENT while resting on a primitive source its neighbour also rests on
    is not independent, and a claim is not evidence.
    """
    if prim_a & prim_b:
        return True
    if set(a["lineage_group_ids"]) & set(b["lineage_group_ids"]):
        return True
    if (b["module_id"] in a["dependency_ids"] or a["module_id"] in b["dependency_ids"]
            or b["module_id"] in a["parent_signal_ids"]
            or a["module_id"] in b["parent_signal_ids"]):
        return True
    if b["module_id"] in a["derivation_chain"] or a["module_id"] in b["derivation_chain"]:
        return True
    return False


#: The search cap for the exact independent-body selection below. Beyond it the selection falls
#: back to a deterministic greedy pass and SAYS SO in the returned `selection_exact` flag, rather
#: than silently returning a possibly smaller answer. The cap is a computational bound on a search
#: and is not a scientific parameter: no band, threshold or belief depends on its value.
_EXACT_SEARCH_NODE_CAP = 200000


def evidence_bodies(records: list[dict]) -> dict[str, Any]:
    """
    SEPARATE A SET OF SIGNALS INTO INDEPENDENT BODIES OF EVIDENCE, WITHOUT TRANSITIVE CLOSURE.

    WHY CONNECTED COMPONENTS WERE WRONG AND ARE NOT MERELY EXTENDED. The first version of this
    file partitioned signals into the connected components of the dependence relation. That is a
    transitive closure, and it made the relation into an equivalence it is not. Measured in
    production on this platform's own declarations: an Amber to-complete performance index and an
    Amber overhead absorption rate share no fact and are two bodies that corroborate to 0.9273.
    Add the tornado ranking, which reads the earned-value indices AND the progress figure, and
    the closure swallowed all three into one body worth 0.7000. The bridging signal destroyed
    corroboration that was really there, purely by existing. That is the defect this replaces.

    WHAT REPLACES IT. The bodies are a MAXIMUM SET OF PAIRWISE-INDEPENDENT SIGNALS -- a maximum
    independent set in the dependence graph. Every signal not selected is dependent on at least
    one selected signal (otherwise the set was not maximal) and is ABSORBED into exactly one of
    them, the first in body order. So:

      * a duplicate, a transform or a derived metric of a selected signal is absorbed and adds
        no body, which is the idempotence the duplicate-reinforcement defect required;
      * a bridging signal is absorbed into one of the bodies it draws from. It cannot become a
        third body, and it cannot merge the two bodies it bridges, because selection asks only
        whether the SELECTED signals are pairwise independent of each other;
      * two genuinely disjoint bodies are both selected and both survive, which is the
        corroboration a closure destroyed.

    WHY MAXIMUM AND NOT GREEDY. A greedy pass in module-id order can pick the bridging signal
    first and then reject both of the bodies it bridges, collapsing two genuine bodies into one.
    That is the same defect wearing different clothes, so the selection is exact by search, with
    a declared node cap and an honest flag when the cap is reached.

    THE TIE-BREAK IS DECLARED AND IS NOT AN OUTCOME PREFERENCE. Several maximum independent sets
    can exist. The one chosen is the lexicographically smallest by member module id. It is
    deliberately NOT chosen by which produces the most or least adverse fused result: selecting a
    partition by the answer it gives is exactly the boundary-moved-to-fit-an-example failure this
    programme refuses. Absorption is by worst band in the consumer, so the choice is conservative
    in either direction.

    ABSORPTION IS INTO ONE BODY, NEVER TWO. A bridging signal is evidence, and evidence is
    counted once. Attaching it to every body it touches would let one reading raise two bodies
    and then have them combined against each other, which is duplicate reinforcement by another
    route.

    Returns a mapping with `bodies` (a list of index lists, the selected representative first),
    `primitive_sources` (the resolved set per record) and `selection_exact`.
    """
    n = len(records)
    prim = resolve_primitive_sources(records)
    if n == 0:
        return {"bodies": [], "primitive_sources": prim, "selection_exact": True}

    order = sorted(range(n), key=lambda i: (records[i]["module_id"], i))
    dep = [[False] * n for _ in range(n)]
    for a in range(n):
        for b in range(a + 1, n):
            d = dependent(records[a], records[b], prim[a], prim[b])
            dep[a][b] = dep[b][a] = d

    # THE SEARCH IS DECOMPOSED, AND THE DECOMPOSITION IS NOT THE CLOSURE COMING BACK. Signals in
    # different connected components of the DEPENDENCE GRAPH cannot constrain one another's
    # selection, so a maximum independent set is the union of the maximum independent sets of the
    # components. That is a statement about the SEARCH, not about the evidence: within a
    # component the answer stays non-transitive, which is exactly why A, B and C -- one single
    # connected component -- still come out as two bodies and not one. Without this the search is
    # exponential in the whole signal set and falls back to greedy on realistic inputs; with it,
    # it is exact.
    seen: set[int] = set()
    components: list[list[int]] = []
    for start in order:
        if start in seen:
            continue
        comp, stack = [], [start]
        seen.add(start)
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in range(n):
                if v not in seen and dep[u][v]:
                    seen.add(v)
                    stack.append(v)
        components.append(sorted(comp, key=lambda i: (records[i]["module_id"], i)))

    best: list[int] = []
    exact = True

    for comp in components:
        c_best: list[int] = []
        c_best_key: tuple | None = None
        nodes = 0
        c_exact = True

        def search(pos: int, chosen: list[int], forbidden: frozenset,
                   comp=comp) -> None:
            nonlocal c_best, c_best_key, nodes, c_exact
            nodes += 1
            if nodes > _EXACT_SEARCH_NODE_CAP:
                c_exact = False
                return
            if len(chosen) + (len(comp) - pos) < len(c_best):
                return
            if pos == len(comp):
                k = tuple(sorted(records[i]["module_id"] for i in chosen))
                if c_best_key is None or len(chosen) > len(c_best) or (
                        len(chosen) == len(c_best) and k < c_best_key):
                    c_best, c_best_key = list(chosen), k
                return
            i = comp[pos]
            if i not in forbidden:
                chosen.append(i)
                search(pos + 1, chosen,
                       forbidden | frozenset(j for j in comp if dep[i][j]))
                chosen.pop()
            search(pos + 1, chosen, forbidden)

        search(0, [], frozenset())
        if not c_exact or c_best_key is None:
            # The honest fallback, for this component only. Deterministic, maximal but not proven
            # maximum, and FLAGGED. Greedy can only ever select FEWER bodies, never merge two, so
            # the fallback errs toward refusing corroboration rather than manufacturing it.
            c_best = []
            for i in comp:
                if all(not dep[i][j] for j in c_best):
                    c_best.append(i)
            exact = False
        best.extend(c_best)

    selected = sorted(best, key=lambda i: (records[i]["module_id"], i))
    bodies = [[i] for i in selected]
    for i in range(n):
        if i in selected:
            continue
        # RUN 20 CYCLE 7. WHICH BODY ABSORBS A BRIDGE IS AN EVIDENCE QUESTION, AND IT USED TO BE
        # ANSWERED BY WHICHEVER BODY CAME FIRST ALPHABETICALLY. B2.1 is where that showed. Its
        # cost forecast arm rests overwhelmingly on the earned-value measurement and touches the
        # document evidence only through the spread of its sampling. Absorbed by module-id order
        # into the DOCUMENT body, its adverse earned-value reading became the document body's
        # band: a document body read Red on no document evidence, and combining that against the
        # earned-value body raised Red belief from 0.3974 to 0.9526. That is false reinforcement
        # arriving through the absorption step rather than through the separation step, and the
        # first-in-order rule could not have got it right except by luck.
        #
        # The bridge is now absorbed into the body it SHARES THE MOST PRIMITIVE EVIDENCE WITH,
        # which is a set comparison over the same identifiers the separation already uses and not
        # a weight, a threshold or a correlation estimate. Ties fall back to body order, which
        # stays declared and deterministic. It is deliberately NOT resolved by which assignment
        # gives the more or less adverse fused answer: choosing by the answer is the
        # boundary-moved-to-fit-an-example failure this programme refuses.
        overlaps = [(len(prim[i] & prim[selected[slot]]), -slot)
                    for slot in range(len(selected)) if dep[i][selected[slot]]]
        if overlaps:
            bodies[-max(overlaps)[1]].append(i)
        else:
            # Unreachable while the set is maximal; kept as a loud invariant rather than a
            # silent drop, because a dropped signal is evidence that vanished.
            raise LineageError(
                f"{records[i]['module_id']} is independent of every selected body, so the "
                f"selection was not maximal")
    return {"bodies": bodies, "primitive_sources": prim, "selection_exact": exact}


def group_labels(records: list[dict], groups: list[list[int]]) -> list[str]:
    """A stable, readable name for each body of evidence, for the audit trail and the tests.

    The label names the body by its REPRESENTATIVE -- the selected pairwise-independent signal --
    not by the union over everything absorbed into it. Under the closure the union was the body;
    it is not any more, and a label that read as a union would suggest a merge that did not
    happen.
    """
    out = []
    for g in groups:
        rep = records[g[0]]
        if rep["lineage_group_ids"]:
            out.append("+".join(sorted(rep["lineage_group_ids"])))
        elif rep["primitive_source_ids"]:
            out.append("primitive:" + ",".join(sorted(rep["primitive_source_ids"])))
        else:
            out.append("signal:" + rep["module_id"])
    return out


# ------------------------------------------------------------------- the declared module lineages
#
# WHY THE DERIVATION CHAIN IS SPELLED OUT RATHER THAN SUMMARISED. The supervisory clarification
# asks that a derived signal retain the chain and not only the final module id. The chain below
# is what makes the dependence CHECKABLE by a reader: anyone can see that the variance at
# completion reaches the earned value through the cost performance index, and that the
# to-complete index reaches it directly, without having to trust the relationship label.
#
# The fact vocabulary is the governed input names the modules themselves declare: bac, ev, ac,
# pv and the reporting history. A ratio is never a fact here; it is a step in a chain.

EARNED_VALUE_BODY = "EARNED_VALUE_MEASUREMENT"
DOCUMENT_BODY = "DOCUMENT_EVIDENCE"
REPORTING_HISTORY_BODY = "REPORTING_HISTORY"
#: The change order log and the two contract sums read from it. Run 20 cycle 4. It is its own
#: body and shares nothing with the earned-value measurement, which is why the two advisory
#: duplicate pairs must NOT collapse into one body between them.
CONTRACT_CHANGE_BODY = "CONTRACT_CHANGE_RECORD"
#: The indirect cost ledger. Run 20 cycle 5. Its own body, sharing nothing with the earned-value
#: measurement, which is exactly what the entry corrected in that cycle had denied.
INDIRECT_COST_BODY = "INDIRECT_COST_LEDGER"
#: The material cost baseline and the current material cost. Run 20 cycle 8. Its own body: the
#: cluster it was found in has only one executable member, so it is a body of one and not a pair.
MATERIAL_COST_BODY = "MATERIAL_COST_RECORD"
# ---------------------------------------------------------------------------------------------
# RUN 28. SIX DECLARATIONS BELOW WERE REWRITTEN, BECAUSE THE FACTS THEY NAMED ARE NO LONGER THE
# FACTS THOSE MODULES READ. The owner's supplied Run-28 contract replaced each of the six
# computations with the canonical method it is named for, defined on a governed structure that
# arrives on the signal inputs. Leaving the old declarations would assert dependence on evidence
# the module no longer touches -- which is exactly the error Run 20 cycle 5 recorded as the one
# that DID HARM, in the other direction: a wrong dependence declaration destroys corroboration
# that is really there, and a wrong INDEPENDENCE declaration manufactures corroboration that is
# not. Each new body below is a body because its evidence is separately prepared and separately
# sourced, and each record's derivation chain names the actual steps.
#
# THIS IS NOT A CATEGORY-9 CLOSURE. Run 31 implements the qualification gate. What Run 28 does
# here is keep the provenance that gate will need TRUE, which is the precondition for it.

#: The Bayesian model record: a prior with a stated source and an observation model with a stated
#: variance basis. Its own body, because a prior elicited or fitted outside this platform is not
#: the earned-value measurement and does not share a fact with it.
BAYESIAN_MODEL_BODY = "BAYESIAN_MODEL_RECORD"
#: The state-space model record: a starting estimate, its uncertainty, and process and
#: measurement variances that state where they came from, alongside the readings filtered.
STATE_SPACE_MODEL_BODY = "STATE_SPACE_MODEL_RECORD"
#: The approved time-phased expenditure baseline, with its version and approval source.
EXPENDITURE_BASELINE_BODY = "APPROVED_EXPENDITURE_BASELINE"
#: The governed reference population of comparable completed projects and their outcomes.
REFERENCE_CLASS_BODY = "REFERENCE_CLASS_POPULATION"
#: The INDEPENDENT estimate at completion: prepared by a different party, by a different method,
#: against the same scope. A body of its own is the whole point of the module that reads it, and
#: the module refuses unless the method AND the responsible party genuinely differ.
INDEPENDENT_ESTIMATE_BODY = "INDEPENDENT_COST_ESTIMATE"
#: The activity network: identities, logic and durations, with its schedule version and status
#: basis. One body serving five Category-2 methods, which is why those five must never be fused
#: as though they were five independent readings.
SCHEDULE_NETWORK_BODY = "SCHEDULE_NETWORK"
#: The cumulative time-phased planned value curve and the matching actual series.
TIME_PHASED_BASELINE_BODY = "TIME_PHASED_BASELINE"
#: Each milestone's committed date and the run of forecasts made for it.
MILESTONE_FORECAST_BODY = "MILESTONE_FORECAST_HISTORY"
#: The look-ahead window's activity and constraint inventory.
LOOK_AHEAD_BODY = "LOOK_AHEAD_CONSTRAINT_INVENTORY"
#: Time-phased resource demand against available capacity.
RESOURCE_PROFILE_BODY = "TIME_PHASED_RESOURCE_PROFILE"
#: Installed and planned production quantities with the labour hours each took.
PRODUCTION_OUTPUT_BODY = "PRODUCTION_OUTPUT_RECORD"
#: The overhead allocation base: the driver amounts the overhead is absorbed over.
ALLOCATION_BASE_BODY = "OVERHEAD_ALLOCATION_BASE"
#: The risk register's events, their probabilities and their impacts.
RISK_REGISTER_BODY = "RISK_REGISTER"
#: The identified analogous project, its cost and the factors adapting it.
ANALOG_ESTIMATE_BODY = "ANALOGOUS_PROJECT_RECORD"
#: A named external price index with its authority, geography, base period and vintage. It is
#: external to the project entirely, which is the property the module exists to have.
EXTERNAL_INDEX_BODY = "EXTERNAL_PRICE_INDEX"
# ---------------------------------------------------------------------------------------------

MODULE_LINEAGE: dict[str, dict[str, Any]] = {
    # ---- the two voting modules, which are the reason this file exists
    "A1.7": lineage_record(
        "A1.7", source_fact_ids=("ac", "bac", "ev"),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("bac,ev,ac", "work remaining = bac - ev",
                          "funds remaining = bac - ac",
                          "to-complete performance index = (bac - ev) / (bac - ac)")),
    "A1.8": lineage_record(
        "A1.8", source_fact_ids=("ac", "bac", "ev"),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("bac,ev,ac", "cost performance index = ev / ac",
                          "estimate at completion = bac / cost performance index",
                          "variance at completion = bac - estimate at completion")),
    # ---- the other lineages the supervisory clarification names by example
    # RUN 20 CYCLE 5. This entry declared A1.1 to be the cost performance index. A1.1 IS MONTE
    # CARLO EAC: it forecasts the estimate at completion by sampling, scaled by both indices and
    # spread by the document risk score, and it refuses a budget of zero and either index at or
    # below zero. It is CORRELATED and not a same-source transform, because the sampling is not a
    # deterministic transformation of the facts and because its body is not identical to the
    # voters' -- it reaches the document evidence as well.
    "A1.1": lineage_record(  # Monte Carlo estimate at completion
        "A1.1", source_fact_ids=("ac", "bac", "doc_risk_score", "ev", "pv"),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("bac,ev,ac,pv and the document risk score",
                          "cost performance index = ev / ac",
                          "schedule performance index = ev / pv",
                          "estimate at completion scaled by the two indices",
                          "stochastic sampling of the estimate at completion, spread by the "
                          "document risk score",
                          "eightieth-percentile overrun against the budget")),
    "A1.2": lineage_record(  # two-sided CUSUM over reporting history
        "A1.2", source_fact_ids=("ev", "pv", "reporting_history"),
        lineage_group_ids=(EARNED_VALUE_BODY, REPORTING_HISTORY_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("reporting history of ev and pv",
                          "schedule performance index per period",
                          "two-sided cumulative sum of the index deviations")),
    # RUN 20 CYCLE 6. This entry declared A1.3 to rest on the planned value and on the REPORTING
    # HISTORY, and to be a reading of that history. IT READS NEITHER. Bayesian EAC requires the
    # budget, earned value, actual cost and the cost performance index, and its arithmetic uses
    # the budget and that one index: a normal-normal update of a prior centred on the budget
    # against a likelihood centred on the budget over the index. There is no series in it and no
    # planned value anywhere in it. The declaration placed it in the reporting-history body,
    # where it was falsely dependent on the trend, filter and forecast modules and could not
    # corroborate them; and it named a planned value it never reads, which is a dependence on
    # every schedule reader that does not exist. Both directions of error in one record.
    # RUN 28. The old record declared the earned-value vector, because the v10 module derived
    # both of its designed variances from the budget and the cost index. v3 reads a GOVERNED
    # MODEL RECORD instead: a prior with its stated source and an observation model with its
    # stated variance basis, neither of which is the earned-value measurement.
    "A1.3": lineage_record(  # Bayesian EAC, a governed normal-normal update
        "A1.3", source_fact_ids=("bayesian_prior", "bayesian_observation"),
        lineage_group_ids=(BAYESIAN_MODEL_BODY,),
        evidence_relationship=INDEPENDENT,
        derivation_chain=("the stated prior and its source",
                          "the stated observation and the variance basis it was estimated from",
                          "normal-normal posterior by precision weighting",
                          "posterior mean and its credible interval")),
    # RUN 28. The old record declared the earned value and the planned value, because the v10
    # module filtered the schedule index series with two literal variances. v3 reads a GOVERNED
    # STATE-SPACE RECORD: the readings and the two variances arrive together, with the source of
    # each variance stated, and the module abstains without them.
    "A1.4": lineage_record(  # scalar Kalman recursion on a governed state-space model
        "A1.4", source_fact_ids=("state_space_observations", "process_variance",
                                 "measurement_variance"),
        lineage_group_ids=(STATE_SPACE_MODEL_BODY,),
        evidence_relationship=INDEPENDENT,
        derivation_chain=("the state space model's readings and its two variances",
                          "predict: the state is carried forward and its variance grows by the "
                          "process variance",
                          "update: the Kalman gain weights the reading against the prediction",
                          "the filtered state and its posterior variance")),
    # RUN 20 CYCLE 6. This entry declared the planned value. A1.5 extrapolates the COST
    # performance history, which is earned value over ACTUAL COST. It never reads a planned
    # value. Declaring one asserted a dependence on every schedule reader that is not there,
    # while omitting the actual cost hid the dependence that is.
    "A1.5": lineage_record(  # ARIMA-style extrapolation of the cost performance history
        "A1.5", source_fact_ids=("ac", "ev", "reporting_history"),
        lineage_group_ids=(EARNED_VALUE_BODY, REPORTING_HISTORY_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("reporting history of the cost performance index",
                          "cost performance index = ev / ac",
                          "first differences of the index series",
                          "one-step autoregressive extrapolation")),
    # RUN 20 CYCLE 5. THE A2.1 ENTRY IS REMOVED AND NOT CORRECTED. It declared A2.1 to be earned
    # schedule over the earned-value body. A2.1 IS PERT NETWORK CRITICALITY, and it abstains with
    # the reason code canonical_structure_absent on every project this platform holds, because
    # the corpus carries no activity network with logic and three-point durations. A lineage
    # record is a statement about a SIGNAL'S evidence. A module that emits no signal on any
    # project has no signal whose evidence there is anything to declare, and declaring one
    # asserts the existence of evidence that was never produced. If the corpus ever carries an
    # activity network, the record is written then, against the reading the module then makes.
    # RUN 20 CYCLE 5, AND THIS IS THE ONE THAT DID HARM. This entry declared A3.5 to be a
    # tornado sensitivity sweep resting on the earned-value body. A3.5 IS OVERHEAD ABSORPTION
    # RATE: actual indirect cost over an indirect plan scaled by progress. It shares NO fact with
    # the earned-value measurement, so an INDEPENDENT second body of evidence had been declared
    # inside the first and could no longer corroborate it. Measured before the correction, an
    # Amber to-complete index and an Amber overhead absorption fused to 0.7000 in ONE body; they
    # are two bodies and 0.9273. A wrong dependence declaration is not merely over-cautious: it
    # destroys corroboration that was really there, which is the failure mode the positive
    # control exists to catch and which a control built from a synthetic body cannot see.
    #
    # The progress figure is declared even though declaring it creates a dependence on the other
    # readers of progress. It scales the denominator, so the reading genuinely rests on it, and a
    # fact is not omitted because its consequences are inconvenient.
    # RUN 28. The progress figure is GONE from this record, and its going is the correction.
    # Run 20 cycle 5 declared it because the v10 module scaled the indirect plan by progress, and
    # said in terms that a fact is not omitted because its consequences are inconvenient. v3
    # absorbs overhead over an explicit ALLOCATION BASE and never touches progress, so declaring
    # it would now assert a dependence on every other reader of progress that is not there.
    "A3.5": lineage_record(  # Overhead Absorption Rate, over an explicit allocation base
        "A3.5",
        source_fact_ids=("indirect_cost_actual", "indirect_cost_plan", "allocation_base_driver"),
        lineage_group_ids=(INDIRECT_COST_BODY, ALLOCATION_BASE_BODY),
        evidence_relationship=INDEPENDENT,
        derivation_chain=("the planned and actual overhead",
                          "the planned and actual amount of the allocation base",
                          "planned rate = planned overhead / planned driver",
                          "actual rate = actual overhead / actual driver",
                          "the variance between the two rates")),
    # ---- RUN 20 CYCLE 4. The two advisory duplicate pairs Run 19 recorded as lineage findings
    #      and cycle 3 left undeclared. DECLARATION ONLY: no band, boundary, threshold or
    #      arithmetic result of any of these four modules is changed by their appearing here.
    #
    #      The first pair. Change Order Frequency and Contract Modification Frequency read the
    #      SAME three governed fields, compute the SAME scope-growth expression from the same two
    #      contract sums, and report the same change count. They differ only in the thresholds
    #      they band it with, which is why on one and the same project they can and do return
    #      different colours: two readings of one body of evidence, not two bodies.
    "A4.6": lineage_record(  # Change Order Frequency
        "A4.6",
        source_fact_ids=("baseline_contract_sum", "change_order_count", "revised_contract_sum"),
        lineage_group_ids=(CONTRACT_CHANGE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("change order log", "count of change orders",
                          "scope growth = (revised contract sum - baseline contract sum) "
                          "/ baseline contract sum")),
    "B3.5": lineage_record(  # Contract Modification Frequency
        "B3.5",
        source_fact_ids=("baseline_contract_sum", "change_order_count", "revised_contract_sum"),
        lineage_group_ids=(CONTRACT_CHANGE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("change order log", "count of contract modifications",
                          "scope growth = (revised contract sum - baseline contract sum) "
                          "/ baseline contract sum")),
    #      The second pair. Sensitivity Analysis perturbs the cost index and ranks three drivers;
    #      Tornado Risk Ranking ranks four present-state deviations built from the same indices
    #      and the same document risk score, plus the two progress figures. The overlap is most
    #      of the body, so it is CORRELATED rather than a transform of the other's output: it is
    #      not computed FROM the sensitivity signal, it recomputes over the same evidence. The
    #      partition does not depend on that distinction -- the shared facts settle it -- and the
    #      label is recorded because a label is a claim, and a claim is not evidence.
    "A5.2": lineage_record(  # Sensitivity Analysis
        "A5.2", source_fact_ids=("ac", "bac", "doc_risk_score", "ev", "pv"),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("bac,ev,ac,pv and the document risk score",
                          "cost performance index = ev / ac",
                          "estimate at completion = bac / cost performance index",
                          "one-at-a-time perturbation of the cost index by plus and minus 0.05",
                          "ranked driver swings")),
    "A5.3": lineage_record(  # Tornado Risk Ranking
        "A5.3", source_fact_ids=("ac", "actual_pct_complete", "doc_risk_score", "ev",
                                 "planned_pct_complete", "pv"),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("ev,ac,pv, the document risk score and the two progress figures",
                          "cost performance index = ev / ac",
                          "schedule performance index = ev / pv",
                          "absolute deviation of each index from one",
                          "absolute progress shortfall",
                          "ranked present-state deviations")),
    # ---- RUN 20 CYCLE 8. THE ARCH.3 CLUSTERS.
    #
    # WHAT WAS ACTUALLY ESTABLISHED, AND HOW. ARCH.3 was found by grouping modules by the exact
    # set of field names their preflight demands. Every declaration below was instead settled by
    # EXECUTION: each primitive fact was moved through the real production derivation, one at a
    # time, over four multipliers, and the module's WHOLE emitted result compared. A fact that
    # can be moved anywhere without moving the result is not that module's evidence, whatever
    # the preflight demands of it. The probe is `tools/run20_cycle8_probe.py` and its output is
    # `code_audit/run20_cycle8_material_influence.csv`.
    #
    # THE FIELD SET AND THE EVIDENCE DISAGREE ON THREE OF THESE MODULES, IN PRODUCTION. All
    # three demand the budget and none of them uses it, because each reports a PERCENTAGE of the
    # budget and the ratio is scale-invariant in it:
    #
    #     B3.2  demands bac, ev, ac and the cost index; its result does not move when the budget
    #           is tripled, and does not move when the earned value and the actual cost move
    #           together with the index held. It reads the COST INDEX AND NOTHING ELSE.
    #     B3.4, B4.3  demand the budget and the two indices; the budget is immaterial to both.
    #     B2.14 demands the cost index, the schedule index and the document risk score; its
    #           result does not move for the cost index at all. It reads the SCHEDULE index.
    #
    # A method that inferred common evidence from the required-input set would have declared all
    # three on the earned value AND the budget. Two of those three claims would have been false.
    # They are still dependent on the earned-value readers, but through the cost index being
    # earned value over actual cost, which is the honest route and the only one taken here.
    #
    # AND ONE CLUSTER IS NOT A CLUSTER. A3.4 and A3.9 were grouped on the two material cost
    # figures. A3.4 is disabled and emits no signal on any project, so there is no pair: A3.9
    # stands alone on its own body. This is the A2.1 precedent from cycle 5 unchanged -- a module
    # that emits nothing has no evidence to declare, and declaring some asserts evidence that
    # was never produced. Six of this row's twenty-four modules are disabled and none is
    # declared: B4.2, B2.20, B4.1, B4.5, B4.6 and A3.4.
    #
    # WHY THE SCHEDULE-INDEX READERS NAME NO EARNED-VALUE GROUP. `derived_index_reads` carries
    # the dependence, and it carries it CORRECTLY IN BOTH EVIDENCE REGIMES. Declaring the
    # earned-value group as well would assert dependence on the earned value even on a project
    # with no planned value, where the schedule index is built from the two progress figures and
    # the module does not touch the earned value at all. A cost-index reader is a different case
    # and does name the group, because the cost index has exactly one ancestry.

    # RUN 28. THE OLD RECORD WAS TRUE OF v10 AND IS THE FINDING RUN 28 CLOSED. Both "forecasts"
    # were transforms of one reported vector, so the record correctly declared them
    # SAME_SOURCE_TRANSFORM over the earned-value body -- which is another way of saying no
    # independent estimate existed. v3 requires two provenance-distinct estimates and CHECKS the
    # distinction, so the management forecast and the independent one are two bodies, and the
    # record says so. The relationship is INDEPENDENT because that is now a property the module
    # enforces at run time rather than a claim this table makes.
    "A1.11": lineage_record(  # Independent EAC Reconciliation Index
        "A1.11", source_fact_ids=("management_eac", "independent_eac"),
        lineage_group_ids=(INDEPENDENT_ESTIMATE_BODY,),
        evidence_relationship=INDEPENDENT,
        derivation_chain=("the management forecast, with its source, method, assumptions, model "
                          "version and responsible party",
                          "the independent forecast, with the same five, differing on the "
                          "method and on the responsible party",
                          "the ratio of the independent forecast to the management one",
                          "and their divergence as a share of the management forecast")),
    # RUN 28. The old record declared the budget and the cost index, because v10 inflated an
    # index-based forecast. v3 simulates a total cost over the risk register's own events. The
    # budget REMAINS declared and remains in the earned-value body: production assembles the base
    # cost from the project's budget at completion, so the reading genuinely rests on it and a
    # fact is not omitted because its consequences are inconvenient. The cost index is gone,
    # because nothing in the module reads it any more.
    "A3.6": lineage_record(  # Cost Risk Analysis P80, a simulated total-cost distribution
        "A3.6", source_fact_ids=("bac", "risk_events"),
        lineage_group_ids=(EARNED_VALUE_BODY, RISK_REGISTER_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("the budget at completion as the base cost",
                          "the register's risk events, each with its own probability and its "
                          "own cost impact",
                          "Monte Carlo realisation of the events over the base cost",
                          "the empirical eightieth percentile of the simulated total")),
    "B3.2": lineage_record(  # FAR Threshold Monitor. The budget is demanded and is immaterial.
        "B3.2", source_fact_ids=(),
        derived_index_reads=(COST_INDEX,),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=SAME_SOURCE_TRANSFORM,
        derivation_chain=("the cost performance index",
                          "cost performance index = ev / ac",
                          "forecast overrun as a percentage of the budget, which is "
                          "scale-invariant in the budget",
                          "comparison against an internal review level")),
    "B3.4": lineage_record(  # EVM Reporting Threshold
        "B3.4", source_fact_ids=(),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=CORRELATED,
        derivation_chain=("the cost and schedule performance indices",
                          "deviation of each index from one",
                          "comparison against an internal reporting level")),
    "B4.3": lineage_record(  # Constraint Satisfaction Analysis
        "B4.3", source_fact_ids=(),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=CORRELATED,
        derivation_chain=("the cost and schedule performance indices",
                          "satisfaction of each index constraint",
                          "count of constraints met")),
    #      The fuzzy and ranking family. Ten modules were grouped here by field name; four are
    #      disabled and are not declared, one reads only the schedule index, and the remaining
    #      five read both indices and the document risk score.
    "B2.10": lineage_record(  # Pythagorean Fuzzy Sets
        "B2.10", source_fact_ids=("doc_risk_score",),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("the two indices and the document risk score",
                          "membership and non-membership degrees",
                          "Pythagorean aggregation to a band")),
    "B2.11": lineage_record(  # Picture Fuzzy Sets
        "B2.11", source_fact_ids=("doc_risk_score",),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("the two indices and the document risk score",
                          "positive, neutral and negative membership degrees",
                          "picture aggregation to a band")),
    "B2.14": lineage_record(  # Maximum Entropy. Demands the cost index and does not read it.
        "B2.14", source_fact_ids=("doc_risk_score",),
        derived_index_reads=(SCHEDULE_INDEX,),
        lineage_group_ids=(DOCUMENT_BODY,),
        evidence_relationship=CORRELATED,
        derivation_chain=("the schedule performance index and the document risk score",
                          "maximum-entropy distribution over the four bands",
                          "the modal band and its entropy")),
    "B2.15": lineage_record(  # Possibility Theory
        "B2.15", source_fact_ids=("doc_risk_score",),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("the two indices and the document risk score",
                          "possibility and necessity measures over the bands")),
    "B2.16": lineage_record(  # Spherical Fuzzy Sets
        "B2.16", source_fact_ids=("doc_risk_score",),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("the two indices and the document risk score",
                          "spherical membership triple",
                          "spherical aggregation to a band")),
    "B2.18": lineage_record(  # MARCOS Ranking
        "B2.18", source_fact_ids=("doc_risk_score",),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
        evidence_relationship=CORRELATED,
        derivation_chain=("the two indices and the document risk score",
                          "ideal and anti-ideal reference points",
                          "utility ratios and the MARCOS composite")),
    "B2.12": lineage_record(  # Hesitant Fuzzy Sets
        "B2.12", source_fact_ids=(),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=CORRELATED,
        derivation_chain=("the two indices", "hesitant membership set", "aggregation to a band")),
    "B2.13": lineage_record(  # Type-2 Fuzzy Sets
        "B2.13", source_fact_ids=(),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=CORRELATED,
        derivation_chain=("the two indices", "upper and lower membership functions",
                          "type reduction to a band")),
    "B2.17": lineage_record(  # Fermatean Fuzzy Sets
        "B2.17", source_fact_ids=(),
        derived_index_reads=(COST_INDEX, SCHEDULE_INDEX),
        lineage_group_ids=(EARNED_VALUE_BODY,),
        evidence_relationship=CORRELATED,
        derivation_chain=("the two indices", "Fermatean membership and non-membership degrees",
                          "aggregation to a band")),
    #      The cluster that dissolved. Its other member is disabled, so this is not a pair.
    # RUN 28. The cluster that dissolved has dissolved further, and correctly. Run 20 cycle 8
    # declared this module on the project's own two material cost figures and its progress,
    # because that is what v10 read. The supplied contract states in terms that a
    # baseline-to-current project material price ratio is NOT an external inflation index; v3
    # reads a NAMED EXTERNAL SERIES with its authority, geography, base period and vintage. The
    # index is external to the project entirely, which is the property the module exists to have,
    # so it shares no fact with any other module on the platform and its body is its own.
    "A3.9": lineage_record(  # Inflation Adjustment Index, from a named external series
        "A3.9",
        source_fact_ids=("external_price_index", "cost_exposure"),
        lineage_group_ids=(EXTERNAL_INDEX_BODY,),
        evidence_relationship=INDEPENDENT,
        derivation_chain=("the named external price index at its base period and at the period "
                          "being adjusted to, with its authority, geography, scope and vintage",
                          "escalation factor = the current index level / the base index level",
                          "the adjusted cost exposure")),
    # ---- the synthesis, which may never corroborate anything it was built from
    #
    # RUN 20 CYCLE 6. THIS ENTRY WAS KEYED "PH.5" AND DECLARED DEPENDENCIES ON A1.7 AND A1.8.
    # BOTH HALVES WERE FALSE. "PH.5" is an AUDIT target id from the scientific-audit numbering,
    # not a module id in the registry this table is keyed by, so `lineage_for` could never return
    # it for any signal the platform computes: a declaration no consumer could reach. And the
    # signal it meant, the portfolio Anomaly Score, is D1.5, whose constituents are the portfolio
    # outlier distance and rank and, when a history exists, a cost trend term. It has never
    # touched the to-complete index or the variance at completion. Re-keyed to the real module
    # and declared against what that module actually combines.
    "D1.5": lineage_record(  # Anomaly Score, a mean over portfolio-outlier constituents
        "D1.5", source_fact_ids=(),
        dependency_ids=("D1.2",),
        parent_signal_ids=("D1.2",),
        lineage_group_ids=("PORTFOLIO_ANOMALY_SYNTHESIS",),
        evidence_relationship=SYNTHESIZED,
        derivation_chain=("D1.2", "relative distance from the portfolio centroid",
                          "one minus the composite rank",
                          "a cost trend term when two or more periods exist",
                          "mean over the constituents actually measured")),
}


def lineage_for(module_id: str) -> dict[str, Any] | None:
    """The declared lineage of a module, or None when none is declared.

    None is NOT an independence claim. A consumer that needs a partition and receives None must
    say so; `fusion` records it as an undeclared lineage rather than assuming independence.
    """
    rec = MODULE_LINEAGE.get(module_id)
    return dict(rec) if rec else None
