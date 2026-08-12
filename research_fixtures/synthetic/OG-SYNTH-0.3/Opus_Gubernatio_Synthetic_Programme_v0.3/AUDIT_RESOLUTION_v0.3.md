# Audit resolution, v0.3

Two ground-truth families were corrected and the module identity tables were
made permanent. Nothing else changed apart from version stamps.

| Finding | v0.3 resolution |
|---|---|
| Monte Carlo distribution undeclared | Cost elements and risk impacts declare TRIANGULAR explicitly, in the element and event tables and in monte_carlo_contract.json. |
| Monte Carlo mean judged against a Beta-PERT expectation | The analytic mean is the triangular expectation, which is what the generator samples. The mean is judged against z times the standard error, not a percentage. |
| Monte Carlo outputs not traceable to inputs | Every element and event now carries its own analytic expectation row, and every project row carries seed, generator, iterations, standard error and acceptance threshold. |
| Monte Carlo identity by overlay | Permanent alias and asset map rows. |
| DSM fields mixed several quantities | Seed, first order, propagated, cumulative state, positive counts and material counts are separate named fields with an explicit threshold and explicit seed inclusion flags. |
| DSM cycle behaviour undocumented | Truncation at a fixed depth is declared in dsm_contract.json and in every row. |

Synthetic data verifies implementation only. It is not empirical evidence.
