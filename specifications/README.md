# Module specifications

Run 76. Each file in this directory is the written specification for one category of modules.
A specification states, for one module: its identity, its required inputs by the exact field
names in `signal_inputs`, its method, its bands and where each threshold came from, what the
reading means, and the conditions under which it declines together with the exact words it
declines in.

These specifications are DERIVED, not composed. Every formula, every threshold, every citation
and every sentence of refusal below is transcribed from the module's own Python source in
`server/app/simulation/`, which is the record of what the module was meant to do. Where the
source was unclear or contradicted its documented method, the specification was STOPPED and the
contradiction reported rather than resolved by guesswork. Stopped specifications are listed at
the end of each file.

Nothing here changes what a module computes. This run changes how a module is applied.

## Files

| File | Category | Modules |
|---|---|---|
| `A1_cost_and_evm.md` | A1 — Cost and EVM Performance | 10 |

The remaining ten categories are not yet written. They stay in Python.
