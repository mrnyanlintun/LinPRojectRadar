# Module specifications

Run 76. Each file in this directory is the written specification for one category of modules.
A specification states, for one module: its identity, its required inputs by the exact field
names in `signal_inputs`, its method, its bands and where each threshold came from, what the
reading means, and the conditions under which it has nothing to report, together with the exact words it
reports in.

These specifications are DERIVED, not composed. Every formula, every threshold, every citation
and every sentence of refusal below is transcribed from the module's own Python source in
`server/app/simulation/`, which is the record of what the module was meant to do. Where the
source was unclear or contradicted its documented method, the specification was STOPPED and the
contradiction reported rather than resolved by guesswork. Stopped specifications are listed at
the end of each file.

Nothing here changes what a module computes. This run changes how a module is applied.

## Files

| File | Category | Modules specified |
|---|---|---|
| `A1_cost_and_evm.md` | A1 — Cost and EVM Performance | 10 |
| `A2_schedule_performance.md` | A2 — Schedule Performance | 6 |
| `A3_cost_risk.md` | A3 — Cost Risk | 7 |
| `A4_document_derived_signals.md` | A4 — Document-Derived Condition Signals | 9 of 10 |
| `A5_system_dynamics.md` | A5 — System Dynamics and Complexity | 7 |
| `A6_delivery_quality.md` | A6 — Delivery Quality Performance | 4 |
| `B1_signal_synthesis.md` | B1 — Signal Synthesis | 4 |
| `B2_evidence_combination.md` | B2 — Evidence Combination | 1 |
| `B3_regulatory_authority.md` | B3 — Regulatory and Authority Thresholds | 5 |
| `B4_decision_optimisation.md` | B4 — Decision Optimisation | 2 |
| `C1_data_integrity.md` | C1 — Data Integrity | 7 |

All eleven project-level categories are written. Sixty-two of the sixty-three modules in service
are specified. **One is stopped: A4.1 Document Risk Score**, which is in service, has no runner,
and raises `MissingModuleError` rather than computing or abstaining. Its entry in
`A4_document_derived_signals.md` records the contradiction and does not invent a method.
