# OG-SYNTH-0.5 — the Portfolio Health canonical successor package

**Successor to `OG-SYNTH-0.4`, which is preserved byte for byte and is not rewritten.
`OG-SYNTH-0.3`, `OG-SYNTH-0.2` and `OG-SYNTH-0.1` behind it are likewise untouched.**

## Why this package exists

Run 33 replaced the computations of the five Portfolio Health modules (PH.1–PH.5 = D1.1–D1.5)
with the canonical methods the owner's supplied contract states. Every PH fixture the previous
line was exercised against was a **portfolio vector** — a bare `{id, cpi, spi, docRiskScore,
actualPctComplete}` object with no cohort, no period, no feature schema, no orientation, no
qualification state and no model version. The supplied contract names that shape as not being
the method: a portfolio comparison is undefined without a declared population, a declared period,
a declared feature schema and a declared model version.

This package adds the **five canonical fixtures** the Run-33 contract is defined on. It **adds
nothing to and changes nothing in** `OG-SYNTH-0.4`.

## What is in it

| file | serves | canonical property |
|---|---|---|
| `ph1_isolation_forest_fixture.json` | PH.1 | a compact nine-project inlier cluster plus one distant anomaly; the distant point must receive the highest anomaly score under ONE governed forest |
| `ph2_midrank_percentile_fixture.json` | PH.2 | the supplied oracle `[1, 2, 3, 10]` with midranks `1/8, 3/8, 5/8, 7/8`, plus a tie cohort where two equal values must receive the same midrank |
| `ph3_trajectory_slope_fixture.json` | PH.3 | the supplied oracle `t = [0,1,2]`, `x = [1.0,0.9,0.8]`, OLS slope `-1/10`, `q = -1`, AdverseSlope `+1/10`, `DETERIORATING`; plus an irregular-interval series and a constant series |
| `ph4_nearest_neighbour_fixture.json` | PH.4 | identical, near and uniformly distant vectors, and one zero-variance feature that must be excluded and recorded |
| `ph5_component_profile_fixture.json` | PH.5 | a four-project cohort where only one project carries a signal history, so PH.3 is a missing constituent for three of them; and the duplicate-lineage case |

## The identity rule this package obeys

Unchanged from `OG-SYNTH-0.4`:

- the **current** record describes the whole canonical fixture surface;
- a **predecessor** record must describe a strict SUBSET of it and must name none of the files the
  successor added;
- a file that carries a **predecessor programme version** while sitting outside that predecessor's
  own record is a current file masquerading as its predecessor, and is refused.

Declared once in `server/tools/synthetic_packages.py`.

## What this package is not

Synthetic. `data_origin = SYNTHETIC_RESEARCH_FIXTURE` and `not_for_empirical_validation = true`
are stated on every file. It verifies that an implementation computes what the supplied contract
says it computes. It is not evidence about any real project, it is not a calibration set, and it
is not field validation of anything. No production code imports it.
