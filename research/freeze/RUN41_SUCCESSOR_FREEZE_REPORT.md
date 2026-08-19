# Run-41 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v26`.

## Why there is a successor at all

Run 37 accepted a final freeze of the v25 instrument. Run 40 then executed a functional and
security acceptance against that release and confirmed two HIGH defects:

- **S1** stored XSS and content-type spoofing on `GET /documents/{id}/content`
- **S2** raw-SQL mutability of the substantive final participant judgment after the final lock

Run 40 ended `FABLE_ACCEPTANCE_BLOCKED` and left both open, because remediating either moves a
byte inside a frozen surface and neither could be applied silently. The owner ruled that **both
be fixed before participant use**, accepting neither risk for the study period.

Fixing them changes executable behaviour, so v25 is **superseded, not amended**.

    v25 accepted freeze
      -> Run 40 identified S1 and S2
      -> owner authorised remediation
      -> v26 successor
      -> requalification

## The behavioural delta, in full

1. Untrusted document content can no longer execute through the same-origin document-content
   response.
2. Substantive final responses become database-immutable after final lock.

Nothing else. That is not a claim of intent; it is measured. All 100 scientific
targets were executed on both lines, and the whole 101-module registered population was executed
from each line's own git object: **zero emitted rows moved**. The AI recommendation served at all
36 project-period positions is **digest-identical** between the lines.

## What was preserved

| Item | Decision | Basis |
|---|---|---|
| Participant package | RETAINED `og-participant-2026.08-v13` | 0 of 70 governed bytes moved; 0 of 6 sequence-bearing files moved |
| Synthetic package | RETAINED `OG-SYNTH-0.6` | byte-identical to the pinned v25 predecessor |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` | byte-identical to the pinned v25 predecessor |
| Voting set | unchanged, exactly `A1.7` and `A1.8` | read from the live registry |
| Category-9 gate | unchanged | no unqualified probe reaches a band, by execution |
| Category-10 boundary | unchanged | authorisation required, creates no project evidence, no Category-10 identity votes |

A successor package was deliberately **not** minted merely because server behaviour changed.

## Findings closed

| Finding | Original severity | Final status |
|---|---|---|
| S1 stored XSS / content-type spoofing | HIGH | **CONFIRMED_FIXED** |
| S2 final-lock database integrity | HIGH | **CONFIRMED_FIXED** |

Unresolved HIGH security blockers: **0**.

Both original reproductions, their original severities, their fix commits, their regression
evidence and their version boundary are preserved in
`code_audit/run41_security_findings_closure.csv`. The findings are closed, not deleted.

## Qualification

| Gate | Result |
|---|---|
| Freeze qualification (Run-37 equivalent, re-executed) | 15 blocker classes, 0 blocked |
| Twelve-fault campaign | 12 applied, 12 intended RED, 12 restored GREEN, 0 crashes credited |
| Security acceptance (Run-40 coverage re-executed) | 11 attacks, 11 reached their boundary, 0 adverse |

## The predecessor is preserved

`sim-2026.08-v25`, its candidate `6142d877856ea651ef8d7e905f6d27604b3244f1`, its release
`f983bb020f7a184a5742e1fff09d690b0170f0de`, its identity, its gate, its behaviour digest and its
release records are **unchanged**. The v25 line still reconstructs from its own git object and
still says v25 - asserted by the requalified guards rather than assumed. Everything already
computed under v25 remains interpretable against the v25 records.

## Identity

- successor candidate commit: `6966b4fa2aa5891c51ce4783d540d6a060c0e0be`
- candidate identity digest: `dc6b4f38c9cae8a3a72a3ac0ac5e7798ec061d281c7e8d41fae0e4ba9fc98a86`
- candidate behaviour digest: `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`
- release content digest: `a9e85858039bc32e19ef6779e66acdcce82396150f8581311a18b466c9b0e1ce`
