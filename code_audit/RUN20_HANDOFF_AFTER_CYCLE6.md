# Run 20 handoff after cycle 6

## State

* Branch `claude/run20-primitive-lineage`, cycle 6 committed as its own commit on top of
  `origin/main` at `6907688`.
* Cycles complete: **6 of 12**. Six remain.
* Voting modules: exactly 2 (A1.7, A1.8). Unchanged.
* Material Cost Variance: disabled. Unchanged.
* Register: 106 rows, 86 OPEN, 1 CLOSED (ARCH.4, this cycle). The row count rose by one because
  ARCH.4 is a new defect class raised and closed in the same cycle by owner decision.
* Open P0D: **B2.1 only**, which is the next item in the owner's order.

## What cycle 6 did

Replaced the transitive-closure partition with a primitive-source, pairwise, non-transitive
dependence model. Swept all thirteen shipped lineage declarations against the actual module
computations and corrected three. Full detail in
`code_audit/REPORT_2026-08-13_run20-cycle6-primitive-lineage.md`.

## The owner's order, and where it stands

1. Primitive-source lineage model and bridging-signal oracle. **DONE, cycle 6.**
2. **B2.1** — the last open P0D. **NOT STARTED.** The register row already records the
   reproduction: `server/app/simulation/models_gov.py` `run_dst` combines four arms through
   `dst_combine` carrying no lineage. Three of the four arms are transforms or extrapolations of
   one earned-value body; the document arm is the candidate independent one. Now that
   `fuse_signals` carries the primitive-source model, the arms need lineage records built from
   their ACTUAL inputs, read the way cycle 6's sweep read the module table, and not from their
   names. The module is non-voting and advisory and reaches no governed status.
3. **ARCH.3** — six clusters with identical required-input sets. **NOT STARTED.** Cycle 6 supplies
   a warning that belongs at the front of this work: A1.3 sits in one of these clusters and its
   preflight requires four fields while its arithmetic uses two of them. The field set alone
   misleads. Determine actual primitive facts, actual derivation, raw versus derived versus alias,
   and whether temporal windows differ, before declaring anything.
4. Remaining P1 implementation defects. NOT STARTED.
5. P2 missing canonical structures. NOT STARTED.
6. P3 parameter, provenance and calibration. NOT STARTED.
7. Remaining lower-priority label and proxy cleanup. NOT STARTED.
8. Mandatory full 100-module scientific re-audit. NOT STARTED.

## Evidence gaps still open, neither silently closed

* Cycle 3's M13 to M21 fault-injection rows exist only in prose. A rerun closes it, not a
  transcription. STILL OPEN.
* No anti-fossilization register file exists under any name; the neighbour-sweep artifact carries
  the function. STILL OPEN.

## Fossilized suites

Cycle 6 found **three more**, all in the run 20 lineage family, all caught the same way the
programme has caught the previous twelve: by an exception rather than a failure, refused by the
strict runner's demand for a canonical RESULT line.

* `test_run20_lineage_model.py` — `KeyError: 'PH.5'`
* `test_run20_lineage_declaration_truth.py` — `AttributeError: no attribute 'partition'`
* `test_run20_advisory_lineage_disclosure.py` — `AttributeError: no attribute 'partition'`

They were not fossilized against the OLD code; they broke the moment the model changed under them.
The point they make is narrower and still worth recording: three suites written one, two and three
cycles ago all depended on a single production symbol, and none of them would have failed
informatively if that symbol had merely changed MEANING rather than disappearing. Nothing in them
asserted the property independently of the function that computed it.

## Full-suite status: VERIFIED GREEN

`server/run_all_suites.sh` was run to completion against this commit, cleanly, with no production
file being edited during the run.

**Suites run: 105. Total checks: 9207/9207. ALL SUITES GREEN.**

The total rises from the previous 9089/9089 by 118: 104 new checks in
`test_run20_primitive_lineage.py`, and 14 net added to the four earlier lineage suites as their
call sites moved onto the non-transitive separation and two reversed checks were written out.

The twenty-mutation battery was separately run to completion against the final code state with
zero survivors.

One earlier run of the suite was discarded rather than reported. It reached 100 of 105 with two
failures, `test_run13_module_evidence.py` and `test_run14_mismatch_remediation.py`, both of which
executed against `server/app/simulation/lineage.py` while that file was being rewritten mid-run.
Both pass on their own against the committed code, 189/189 and 112/112, and both pass in the clean
run above. The run was rerun rather than explained away, which is the only way that result is
worth anything.

## A caution for whoever runs the suites next

Cycle 6 lost a full-suite run by editing `server/app/simulation/lineage.py` while
`run_all_suites.sh` was in flight. Two suites failed against a half-written file and both pass
cleanly on their own. Do not edit production files during a suite run; the failures look exactly
like real ones.
