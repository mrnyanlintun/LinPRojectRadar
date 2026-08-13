# Run 20 cycle 5 — three lineage declarations named the wrong module, and one of them destroyed real corroboration

Continues Run 20 from the cycle-4 commit on `main`.

## The exit block

```
declared ids audited against the method they really carry = 13, all of them, not a sample
declarations naming the wrong method                      = 3 found, 3 corrected
suppressed corroboration, measured
  Amber to-complete index with Amber overhead absorption  = 0.7000 in ONE body before
                                                          = 0.9273 in TWO bodies after
same-lineage suppression, unchanged                       = Amber 0.7000, Green 0.8000,
                                                            Red 0.8340
independent positive control, unchanged                   = 0.9273
bands, boundaries or arithmetic results changed           = 0
voting modules                                            = 2, unchanged
mutations                                                 = 5, M30 to M33 plus M32b; M32 did
                                                            not qualify on its first attempt
fossilized suites found                                   = 1, and it CRASHED rather than failed
full regression                                           = 104 suites, 9089 checks, all green
```

## What was found, and how

Cycle 4's neighbour sweep grouped every module by the field set its own preflight requires.
Reading that grouping back against the declared lineage table showed three declarations describing
methods those module ids do not carry.

| id | declared as | what it actually is |
|---|---|---|
| A1.1 | the cost performance index, chain `ev / ac` | Monte Carlo EAC |
| A2.1 | earned schedule, chain schedule performance index (time) | PERT Network Criticality |
| A3.5 | a tornado sensitivity sweep over the earned-value body | Overhead Absorption Rate |

The error was not random. All three are worked examples cycle 3 added for illustration, and none
of them was ever executed by a consumer, which is exactly why nothing caught them. The other ten
declarations hold.

## Why the third one is not cosmetic

Most declaration errors in a table like this are conservative. A wrongly declared dependence
refuses corroboration that was really available; a wrongly declared independence is caught by the
fact-intersection rule, because a claim is not evidence.

A3.5 was the conservative direction taken far enough to do harm. Overhead Absorption Rate rests on
the planned and actual indirect cost and the progress figure, and shares **no fact** with the
earned-value measurement. It had been declared inside the earned-value body, so a genuine second
body of evidence was absorbed into the first and could no longer corroborate it. Measured: an Amber
to-complete index and an Amber overhead absorption fused to **0.7000 in one body**. They are two
bodies and **0.9273**.

This is the failure the programme's own instruction names: a fix that also suppresses real
corroboration is not a fix. **Cycle 3's positive control could not see it**, and the reason is
worth stating plainly. That control was real, but it was built from a *synthetic* independent body
written inside the test. It proved the combination *rule* could still corroborate while saying
nothing about whether the *declarations shipped in production* had left anything to corroborate
with. This cycle's control is driven from the declared table itself.

## What changed, and what deliberately did not

A1.1 and A3.5 are corrected, and a new indirect cost ledger body is added. **The A2.1 entry is
removed rather than rewritten.** PERT Network Criticality abstains with the reason code
`canonical_structure_absent` on every project this platform holds, because the corpus carries no
activity network with logic and three-point durations. A lineage record is a statement about a
signal's evidence, and a module that emits no signal has no signal whose evidence there is anything
to declare. If the corpus ever carries an activity network, the record is written then.

No module's band, boundary, threshold or arithmetic is touched, and the readings are pinned on a
fixture and asserted after.

The progress figure is declared for A3.5 even though declaring it creates a dependence. It scales
the denominator, so the reading genuinely rests on it, and a fact is not omitted because its
consequences are inconvenient.

## The transitive bridge, stated rather than engineered away

Over the whole declared table, overhead absorption does land in the same part as the earned-value
readings, and not because it shares a fact with any of them. It shares the progress figure with
Tornado Risk Ranking, which in turn shares the earned-value facts, and the partition closes
transitively by design. The two share no fact and are two bodies whenever no bridging signal is
present, which is the case that governs any fusion this platform actually performs.

Whether transitive closure through a bridging signal is the right treatment is a real
methodological question. Loosening the closure so the check reads better would be moving a rule to
satisfy an example, which this programme does not do. It is raised as an owner decision with the
current transitive behaviour as the recommended default, because that is the option that can never
manufacture reassurance, and its cost is now visible and recorded rather than silent.

## Mutations

| id | mutation | caught by |
|---|---|---|
| M30 | overhead absorption put back inside the earned-value body | the defect returns, 6 checks |
| M31 | the progress figure dropped from its facts | the declared-fact check and the named bridge |
| M32 | the sampling step removed from the Monte Carlo chain | **NOTHING. It did not qualify.** |
| M32b | the same mutation after the check was hardened | the sampling-step check |
| M33 | a lineage declared for A2.1 again | the no-signal checks, 2 of them |

**M32 is recorded rather than hidden.** The check accepted any chain step containing the word
"percentile" as evidence of the stochastic step, and the eightieth-percentile step satisfied it, so
removing the sampling altogether left the check green. A percentile is what is read off a
distribution, not the step that produces one. The check now demands the sampling be named, and the
mutation was rerun and qualified. This is the second time in Run 20 that a mutation failed to
qualify on its first attempt and the guard was hardened rather than the mutation abandoned.

## The twelfth fossilized suite, and it crashed

`test_run20_lineage_model.py`, written by cycle 3 three cycles ago, indexed the lineage table
directly and **crashed with a KeyError** when the A2.1 entry was removed, rather than failing. It
was caught only because the strict runner refuses a missing RESULT line, which is the same
mechanism that caught three of cycle 1's four and one of cycle 2's two. The programme count of
suites found encoding a defect, a superseded reading or a crash-not-fail lookup goes from eleven to
twelve.

It also carried two partition cases describing A1.1 as the cost performance index and A2.1 as
earned schedule. Both cases keep the property they measured and lose only the false description:
the earned-schedule case is now driven from a hand-written record rather than from a module id that
never carried the method. Deleting the case would have lost a real property along with the
misdescription.

## What is complete and what remains

Complete: the three corrections; the whole-table guard that makes every declared id prove itself
against the module's runtime behaviour, so this class cannot repeat silently; the corrected
cycle-3 suite; the register, transitions, lineage results, neighbour sweep, fault injection, owner
decision and this report.

Remaining: B2.1, the last open P0D row; ARCH.3, the five undeclared shared-evidence clusters; the
P1 method-label work including 4.6 and 5.3; then P2, P3, and the mandatory complete 100-module
re-audit. Run 21 has not been launched.
