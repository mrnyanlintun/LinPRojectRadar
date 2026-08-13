# Run 20 cycle 3 — evidence lineage in the combination rule, and the Category-9 operational gate

Continues Run 20 from `f59a38e`. Branch `claude/run20-p0d-lineage-cat9`. Commits A `0a2786d`,
B `bd7f290`, C `eb9b0e5`, D this one.

## The exit block

```
lineage cases tested                                     = 8 named cases A to H, plus 9 partition
                                                           cases, plus the complete 16-combination
                                                           sweep of the two voters, plus idempotence
                                                           over 4 bands at 2, 3 and 5 copies = 45
same or dependent lineage cases increasing evidential
  strength                                               = 0
Category-9 bypass attempts tested                        = 4 object types through the converter,
                                                           plus 1 live-path bypass mutation = 5
raw or unqualified bypasses accepted as fully qualified  = 0
Voting modules                                           = 2
TCPI scientific method result                            = SCIENTIFIC_PASS, re-proved through the
                                                           qualified-signal path at both sourced
                                                           boundaries against hand oracles
VAC scientific method result                             = SCIENTIFIC_PASS, re-proved the same way
Voting-fusion dependence result                          = REMEDIATED. The two voters are declared
                                                           SAME_SOURCE_TRANSFORM over one
                                                           earned-value body and are combined as
                                                           one body, not two.
P0A                                                      = CLOSED at the fusion layer, with one
                                                           ratification row recorded and not
                                                           blocking
P0D                                                      = ARCH.1 CLOSED, ARCH.2 CLOSED;
                                                           4.6 and 5.3 lineage disclosure OPEN
original Amber: 0.7000 -> duplicate before 0.9273 -> duplicate after 0.7000
original Green: 0.8000 -> duplicate before 0.9722 -> duplicate after 0.8000
original Red:   0.8340 -> duplicate before 0.9787 -> duplicate after 0.8340
conflict of a body against its own copy: 0.4414 before -> not estimated at all after
positive control, two genuinely independent Amber bodies: 0.9273, unchanged
full regression                                          = 102 suites, 8722 checks, all green
working tree                                             = clean
continuation commit                                      = see the commit that carries this file
```

## How the fusion actually combines the two voters, and where independence was assumed

`compute.compute_project` groups the voting modules by category. Both live in A1, so
`fusion.dst_fuse` received a two-element list of status strings and applied Dempster's rule
pairwise. The project level then fused the single category status.

Independence was assumed in exactly one place and it was never written down: Dempster's rule
itself. Its normalisation by the conflict coefficient K is defined only for independent bodies
of evidence. Nothing anywhere recorded that the two inputs shared a lineage, and `dst_fuse` took
only status strings, so a caller that knew the lineage had no way to supply it.

The proof that independence was assumed is arithmetic and not inferred from the module count: the
rule reported K = 0.4414 between two readings of one body of evidence. One body cannot disagree
with itself, so the number was itself the proof.

## Whether shared lineage could move Cost Recovery Status, in either direction

Yes, in both senses, and the answer comes from sweeping all sixteen band combinations rather than
sampling.

**Confidence.** Duplication inflated the mass on the resulting band: Amber 0.7000 to 0.9273, Green
0.8000 to 0.9722, Red 0.8340 to 0.9787. Reassurance and alarm alike.

**The band itself.** In two of the sixteen combinations the band moved, and both moved in the
FAVOURABLE direction. A Green reading and a Yellow reading of the one earned-value body produced
GREEN, in both orders, because the Green mass function is the more committed of the two and won
the normalisation. So the governed label was not a deterministic conservative case comparison: in
two of sixteen cases it reported the better of two readings of one body of evidence. It is a
conservative comparison now, explicitly, and all sixteen resolve to the more adverse reading.

## The dependence treatment implemented, and why

Partition first, then two operators for two different questions.

**Within a body of evidence** the question is not whether the readings agree, because one body
cannot agree with itself. The question is what the body says when read more than one way, and the
answer taken is the most adverse reading. That operator is idempotent, which is exactly the
property required: adding a copy, an algebraic transform or a derived metric changes nothing at
all. It carries no weight, no correlation estimate and no tuned parameter, because there is no
defensible empirical basis in this repository for any of those, and inventing one would be worse
than being conservative. Disagreement between two readings of one body is recorded, never scored.

**Across bodies of evidence** Dempster's rule applies unchanged, its independence assumption now
true by construction. The Red emphasis is applied once per body rather than once per signal, so
duplicating a Red signal cannot apply it twice.

The choice among idempotent operators is governance policy and not science. That is recorded as a
ratification row in `run20_owner_decisions_required.csv`; it does not block the scientific closure,
because any idempotent operator satisfies the requirement and the one chosen is the one that can
never manufacture reassurance.

## The eight lineage cases

Baseline: one Amber earned-value body, mass 0.7000, one lineage group.

| case | what was added | mass after | groups | outcome |
|---|---|---|---|---|
| A | an exact duplicate | 0.7000 | 1 | joined the body |
| B | an algebraic transform of the same facts | 0.7000 | 1 | joined the body |
| C | a derived metric reaching the facts through another ratio | 0.7000 | 1 | joined the body |
| D | a second method over the same raw facts | 0.7000 | 1 | joined the body |
| E | a synthesis of the signal, reused as evidence | 0.7000 | 1 | joined the body |
| F | a quality result reused as risk evidence | 0.7000 | 1 | refused as project evidence |
| G | a governance output fed back | 0.7000 | 1 | refused as project evidence |
| H | a decision output fed back | 0.7000 | 1 | refused as project evidence |

In no case did the mass rise, in no case did a second body appear, and in no case did the band
move. Cases F, G and H were additionally driven with a maximally contrary reading in both
directions and could not move an Amber band either way.

**Positive control**, so the file is capable of failing: two genuinely independent Amber bodies
still corroborate to 0.9273, a third strengthens further, and their conflict coefficient is
estimable where a single body's is not.

## The nine Category-9 conditions

| condition | outcome | what it does, not what it says |
|---|---|---|
| missing required evidence | ABSTAINED | no value exists; no band, no vote |
| stale evidence | DEGRADED | value readable and on the ledger; may not vote |
| missing provenance | DEGRADED | value readable; may not vote |
| conflicting source evidence | REJECTED | band and value both unreachable |
| incomplete audit chain | REJECTED | band and value both unreachable |
| invalid or out-of-domain value | REJECTED | band and value both unreachable |
| duplicate lineage | ALLOWED | votes, and counts as one body carrying 0.7000 |
| derived or synthesized evidence | ALLOWED | votes as a reading of its own body only |
| raw bypass attempt | REJECTED | refused with an exception, never a silent drop |

Each is asserted twice, once on the verdict and once on the execution, because a verdict with no
execution consequence is the failure the clarification names.

Three boundary refusals are recorded rather than hidden. A record dated after the period cutoff
is REJECTED as malformed and not DEGRADED as stale. Critical audit fields are noncompensatory:
six optional fields do not average away one missing critical one. And what a package does not
declare is not assessed and is certainly not assumed clean.

**The stated limit.** On the evidence packages this platform produces today only the
required-evidence condition is live, because those packages declare no as-of dates, no document
identities, no audit record and no domains. This repository records a document type per sourced
field and no document identity, and `qualification.py` already states that as a PARTIAL dimension
that must not become a penalty. A gate that degraded every field on every project for a provenance
the platform has never recorded would assert a capability rather than enforce a contract, and
would stop all voting as a side effect. The other conditions become live for any package that
carries the declarations, with no change at the call site.

## Anti-feedback

Quality, governance and decision outputs are refused as project-condition evidence in TWO places:
at the gate, where their band and value become unreachable, and inside the combination, where they
are dropped by name rather than grouped. Two places, because a signal can reach a synthesis
without passing through the fusion.

## Mutations

| id | mutation | caught by |
|---|---|---|
| M13 | the declared-lineage-group rule erased from the partition | the declared-shared-group partition case |
| M14 | the two voters relabelled INDEPENDENT | the two same-source-transform declaration checks |
| M15 | QUALITY_METADATA removed from the anti-feedback set | case F and both anti-feedback directions, 6 checks |
| M16 | the within-body reading inverted to the most favourable | 26 checks including the sweep rows and the live status |
| M17 | the live path stops supplying lineage, a raw bypass | the anti-bypass check that the live path never fuses on an undeclared lineage |
| M18 | the band property stops honouring the verdict | 6 execution checks |
| M19 | DEGRADED admitted to the voting set | the two may-not-vote checks |
| M20 | the raw-bypass guard removed | all four bypass checks |
| M21 | the anti-feedback rejection removed from the gate | 6 anti-feedback checks |

Every mutation was byte-confirmed before the red was believed, and every restore was proved green.

Two honesty notes. M20 at first failed only by an incidental `AttributeError` from the converter
rather than by the gate's own refusal; an accident is not a refusal, so the test was hardened to
make any other exception a red, and the mutation was rerun. And one restore appeared red because
of stale bytecode; the cache was cleared and the restore proved green. Both are recorded rather
than hidden.

## Further fossilized suites and guards found

No new fossilized suite in the sense of a suite that could not fail. Three related findings:

1. **A proposition that would have become vacuous.** `test_run2_fifteen_defects.py` proved the
   corrected Dempster combination moves the rollup conflict. After the lineage correction the one
   voting category is one body of evidence and no conflict is estimated for it in either rule, so
   the vehicle no longer reaches the finding. The finding was moved to where it lives, on
   `dst_combine` itself against the audit's own two-Green example, 0.32 before and 0 after, and the
   rollup's new inertness is asserted as its own named proposition.
2. **A structural gap in the Run-20 byte guard.** It compares production against a freeze, so a
   file that did not exist when the freeze was taken had no row to differ from and could have been
   added with no declaration at all. A declared new-production-file list was added, with a check
   that every file in the simulation package is either in the freeze or on that list.
3. **The guard is not vacuous**, and this was demonstrated three times: it went red on the
   undeclared `fusion.py`, again on the undeclared `compute.py`, and again on the undeclared
   `qualification_gate.py`, each time before being declared.

## The P0A determination

The clarification asked that three things be distinguished, and they separate cleanly.

**(A) Module method validity.** Never in question and not revoked. Both voters were re-proved
through the qualified-signal path at their sourced boundaries against hand calculations: the
to-complete index at 1.000 and 1.10132, the variance at completion at 0 per cent and
-11.235 per cent, and both abstain when any declared input is absent.

**(B) Evidence lineage and dependence.** Established and now declared. Both are transforms of one
earned-value body: the to-complete index reaches the earned value directly, the variance at
completion through the cost performance index and the estimate at completion. Both carry
`SAME_SOURCE_TRANSFORM`, both carry their derivation chain, and both name the body.

**(C) Governed fusion validity.** Proved. The rule partitions before combining; it claims no
independent corroboration; it estimates no conflict coefficient between a body and itself; it
resolves a disagreement within one body to the more adverse reading; the live path never fuses on
an undeclared lineage; voting remains exactly two modules; no third signal enters Cost Recovery
Status; and no quality, governance or decision output can become project-risk evidence.

**P0A = CLOSED at the fusion layer.** The approved two-voter architecture is reconcilable with the
dependence structure without changing governance policy in any way that removes a voter, adds one,
averages them or invents independence weights. One ratification row is recorded asking the owner to
confirm the choice of idempotent operator, which is policy rather than science and does not block
the closure.

## What is complete and what remains

Complete: ARCH.2 the lineage model and the dependence-aware combination; ARCH.1 the Category-9
operational gate; the voting-path requalification; the P0A determination; the register, the
transitions, the cycle record, the lineage results, the Category-9 enforcement results, the
neighbour sweep and this report.

Remaining, and stated plainly rather than folded away:

- **4.6 and 5.3 lineage disclosure**, both still OPEN. The framework to express them now exists
  and the anti-feedback rule is enforced, but neither module's own lineage record is declared.
  Both are non-voting and advisory, so neither can reach a governed status.
- **B2.1 DST Evidence Combination** carries the same uncontrolled reinforcement the voting path
  carried: three of its four arms are transforms or extrapolations of one earned-value body.
  It is non-voting and advisory. Recorded in the neighbour sweep, carried forward, not done.
- The remaining 84 OPEN register rows: implementation defects, label mismatches, missing
  structures and calibration work, in the register's own order.

Run 21 has not been launched.
