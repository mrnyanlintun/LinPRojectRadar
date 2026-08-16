# OG-SYNTH-0.4 — the Category 4 and 5 canonical successor package

**Successor to `OG-SYNTH-0.3`, the package the importers read, which is preserved byte for byte and is not rewritten. `OG-SYNTH-0.2` and `OG-SYNTH-0.1` behind it are likewise untouched.**

## Why this package exists

Run 29 replaced the computations of eighteen Category-4 and Category-5 modules with the canonical
methods the owner's supplied contract states. Three of those modules were still being exercised
against the *shapes* the previous line read, which the canonical contracts name as not being the
method at all:

| module | the shape OG-SYNTH-0.3 was imported into | why that shape is not the method |
|---|---|---|
| A4.4 NCR Rate | an audited findings cohort with an open backlog | a stock over the size of one audit is a ratio of two different populations, not a rate over a governed exposure |
| A5.6 Queueing Theory Bottleneck | an occupancy log of entities, a horizon and measured waits | a share of occupied server time is a measurement, not a queueing model: no arrival process, no service process, no stability condition |
| A5.7 Agent-Based Supply Chain | a typed-in agent state history | the decision rules were named and never executed, so it was a table read and not a simulation |

This package adds the **known-answer tables** those three canonical contracts are defined on, at
the exact figures the supplied contract states. It **adds nothing to and changes nothing in**
`OG-SYNTH-0.3`: the six projects' real synthetic evidence is imported into the canonical shapes
directly from that package, unchanged, by
`server/tests/synthetic_fixtures/importers/production_structures.py`.

## What is in it

| file | serves | known answer |
|---|---|---|
| `ncr_exposure_known_answer.csv` | A4.4 | 4 nonconformances over 100 inspections = **0.04** |
| `queue_model_known_answer.csv` | A5.6 | lambda 2, mu 3, one server: rho 2/3, L 2, W 1, Lq 4/3, Wq 2/3; plus lambda = mu and lambda > mu, which must REFUSE a finite steady state |
| `abm_agents_known_answer.csv`, `abm_environment_known_answer.csv` | A5.7 | the deterministic one supplier, one carrier, one project model: stock 2, travel delay 1, demand 2, receipts 0,0,1,2,2,2, received 2, backordered 0; and a zero-stock case receiving nothing |

## The identity rule this package obeys

The same rule that governs the participant-package chain, stated for a chain whose predecessor
data are genuinely unchanged rather than superseded:

- the **current** record describes the whole canonical fixture surface;
- a **predecessor** record must describe a strict SUBSET of it and must name none of the files the
  successor added;
- a file that carries a **predecessor programme version** while sitting outside that predecessor's
  own record is a current file masquerading as its predecessor, and is refused.

Declared once in `server/tools/synthetic_packages.py` and enforced by
`server/tools/test_run29_synthetic_packages.py`.

## What this package is not

Synthetic. `not_for_empirical_validation` is True on every row. It verifies that an implementation
computes what the supplied contract says it computes. It is not evidence about any real project,
and no production code imports it.
