# Group assignment: the verified taxonomy

**100 computations, in four groups.** This file is the authority for how the analytical layer is
described. It was generated from the code, not from a document, and a check in the test suite
fails if the code and this file stop agreeing.

| Group | Name in user-facing text | Count |
|---|---|---|
| A | Project Health | 52 |
| B | Recommendation and Governance | 36 |
| C | Data and Evidence Health | 7 |
| D | Portfolio Level | 5 |
| | **Total** | **100** |

## How to use this in user-facing text

- **Refer to groups by group and purpose, never by module id or number.** "Cat 4", "1.7", "PH.2"
  and "A4.2" do not belong in anything a user reads. The ids below are keys, not names.
- **Write "and", not an ampersand.** The code constants spell two of these names with "&". User
  facing text says "Recommendation and Governance" and "Data and Evidence Health". Do not rename
  the code constants to match.
- **Group C does not contribute to project status.** It measures how trustworthy the evidence base
  is. Folding it into status would make an early scenario read worse for reasons that have nothing
  to do with the project.
- **Group D is portfolio level** and needs more than one project. A single project path that
  reaches one is a routing mistake, and the code raises rather than reporting insufficient data.

## Why the total is 100 and not 101

The module registry declares 101 live entries. The analytical server registers 100 of them.

The difference is **Document Risk Score**, which is **not counted here**. It is a value the
extraction model supplies and the server carries through, not a computation the analytical server
performs. Two places in the code assemble it, and both take the number directly from the field the
extraction model returned, with no arithmetic and no derivation from other extracted figures. It is
deliberately not rescaled, because rescaling would diverge from the instrument being reproduced.

**This is a decision about what counts as a computation, and it has been made.** The count is 100.

## The open caveat, which is not resolved

**Nobody has established whether Document Risk Score is unported by design or unported by
accident.** The registry's refusal message says it "has not been ported and validated against the
JavaScript implementation", which is the wording of work outstanding rather than of deliberate
exclusion.

That refusal is also **a generic catch-all** for anything absent from the validated set. It is not
a Document Risk Score specific exclusion, and it must not be described as one.

**So 100 is current, not permanent.** If the value is later implemented as a server-side
computation, the count becomes 101 and Group A becomes 53. Anything written against this file
should be easy to change for that reason.

**Group A's full roster is 53 named entries, not 52.** The 52 in the table above is the
registry-computed count, exactly as used everywhere else in this file. Document Risk Score is the
53rd named entry: declared in the registry, supplied by the extraction model rather than computed,
and excluded from every count on this page (Run 5, `code_audit/REPORT_2026-08-11_run5-export.md`,
confirmed directly against `VALIDATED` in the code: 52 Group A ids present, `A4.1` absent).

## The registered computations

Generated from the code: the validated single project registry plus the portfolio registry. The
check in `server/tools/test_group_assignment.py` parses the block below and fails if it stops
matching what the server registers.

Retired ids are excluded by the registry loader and none appear here.

```group-assignment
A A1.1 A1.2 A1.3 A1.4 A1.5 A1.6 A1.7 A1.8 A1.9 A1.10 A1.11 A2.1 A2.2 A2.3 A2.4 A2.5 A2.6 A2.7 A2.8 A2.9 A2.10 A2.11 A3.1 A3.2 A3.3 A3.4 A3.5 A3.6 A3.7 A3.8 A3.9 A4.2 A4.3 A4.4 A4.5 A4.6 A4.7 A4.8 A4.9 A4.10 A5.1 A5.2 A5.3 A5.4 A5.5 A5.6 A5.7 A5.8 A6.1 A6.2 A6.3 A6.4
B B1.1 B1.2 B1.3 B1.4 B2.1 B2.2 B2.3 B2.4 B2.5 B2.6 B2.7 B2.8 B2.9 B2.10 B2.11 B2.12 B2.13 B2.14 B2.15 B2.16 B2.17 B2.18 B2.19 B2.20 B3.1 B3.2 B3.3 B3.4 B3.5 B4.1 B4.2 B4.3 B4.4 B4.5 B4.6 B4.7
C C1.1 C1.2 C1.3 C1.4 C1.5 C1.6 C1.7
D D1.1 D1.2 D1.3 D1.4 D1.5
```

## Excluded, recorded so the exclusion cannot be lost

```group-assignment-excluded
A4.1 Document Risk Score
```
