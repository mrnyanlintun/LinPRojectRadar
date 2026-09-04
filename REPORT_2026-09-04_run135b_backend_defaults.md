# Run 135B — Group 4 (favourable defaults and zero-as-absent) and S6 (percentile divergence)

Agent B of four. Branch `worktree-agent-ac6c002dc23b88474`.
Starting commit `6d9899f34d7b08561ccfc7979c1f05389df8f772`.
Last code commit `5a0082025985d7275586d2e7f5946388d93183f9`; this report is committed after it.

Scope owned: `backend/` entire, plus `assets/js/simulations.js`. Nothing outside it was
modified — `assets/js/simulations.js` was read and, during one fault injection, temporarily
edited, then restored byte-identical; it is unchanged in every commit.

No model key was set, no model was called, no model was simulated. No migration was written
and none is required — `backend/` has no schema. `SIMULATION_VERSION` did not move: it lives in
`server/app/simulation/`, which this agent does not own and did not touch. No production
recomputation is required by anything here, for the reason the verdict below gives.

---

## Disposition table

| Finding | Site | Disposition | Attempts |
|---|---|---|---|
| S2 — missing/malformed status becomes favourable | `backend/governance.py:24` | **RESOLVED** | 1 |
| S3 — missing and zero inputs defaulted into scored outputs | `backend/simulations.py:21` | **RESOLVED** | 1 |
| S4 — zero EV treated as absence | `backend/main.py:180` | **RESOLVED** | 1 |
| S6 — backend and browser compute different P80 quantities | `backend/simulations.py:91` vs `assets/js/simulations.js:168` | **RESOLVED** | 1 |

Nothing BLOCKED. Nothing UNRESOLVED AFTER 5. Nothing NOT REACHED within the assigned scope.
No decision is needed from the owner to close any of the four.

---

## The verdict on `backend/`: it is dead, and it is worth knowing

**`backend/` serves no live path, and `assets/js/simulations.js` is loaded by no live page.**
Established by registration, not by name. The evidence, in the order it settles the question:

1. **No page loads `backend/`.** `assets/js/config.js:28` sets `window.LIN_API_URL = "/exec"`, a
   relative path, and the file's own header says the app "is served by the Render service that
   also serves `/exec`" — that is `server/`, provisioned by the repository-root `render.yaml` as
   `opus-gubernatio-server`. `backend/render.yaml` provisions a *separate* service,
   `lin-project-radar-backend`, docker runtime, free plan, `OPENAI_API_KEY` / `OPENAI_MODEL:
   gpt-4.1`. Nothing points at it.
2. **No asset names a `backend/` route.** Grepping every route path declared in `backend/main.py`
   (`/health`, `/list`, `/listarchived`, `/get`, `/gethistory`, `/create`, `/save`, `/archive`,
   `/restore`, `/chat`, `/analyze`, `/extractsignals`, `/overwritesignal`, `/resetsignals`,
   `/simulate`, `/tts`, `/ingestcorpus`, `/listcorpus`, `/audit`) and the service name
   `lin-project-radar-backend` across `assets/`, `index.html` and `tests.html` returns nothing.
   The only absolute fetch targets in `assets/js/` are `/mapconfig`, a local questionnaire JSON,
   and a countries file; everything else resolves through the `/exec` helper.
3. **No live page loads `simulations.js`.** The only `<script src="assets/js/simulations.js">` in
   the tree is `tests.html:49`, a browser test harness. `index.html:1292` states in terms that
   "sim.js / simulations.js are gone". `assets/js/signals.js:295` records the same:
   "simulations.js is not loaded on the application page". No JS file builds a script tag for it —
   the only two dynamic script builders, `globe.js:95` and `gmap.js:44`, load external map
   libraries.
4. **The in-service implementation says so itself, twice, and says why.**
   `server/app/simulation/models.py:8` — "NOT ported from `backend/simulations.py`. That spike
   covers 5 of 91 and diverges from the JavaScript in every one of them: different network
   topology and thresholds in PERT, different rates and unit counts in LOB, a different default
   completion in CCPM, **a different percentile rule in RCF**, and a different coefficient in the
   DSM matrix."  `server/app/simulation/fusion.py:4` — "Deliberately NOT ported from
   `backend/governance.py`. That router classifies into `Critical` and `Red-Review`, which no
   module emits, and its `FAIRNESS_SENSITIVE` list names two modules that exist nowhere in the
   codebase."
5. **No Python in the repository imports it.** A grep for `from backend` / `import backend` over
   `server/` and `tools/` returns only those two prose disclaimers.

So: **dead, and previously surveyed as dead by the team that built the replacement.** Two
consequences matter more than the verdict itself.

- **The defects were not hypothetical when they were live.** The S6 divergence is named
  explicitly in `models.py:8` as one of the reasons the port was refused. The favourable-default
  family in S2/S3/S4 is not named there; it was found by the second hunt, not by the porting
  survey. A survey that rejects a module for *arithmetic* divergence can still leave its
  *epistemic* defects — abstention, zero-versus-absent — unrecorded, and that is what happened.
- **`assets/js/simulations.js` is not dead in the same sense.** It is the acknowledged original
  (`models.py:4`: "the implementation the instrument has always run"), it is still consumed by
  `tests.html`, and `server/app/simulation/models.py` is validated numerically against it. That is
  why the S6 parity check reads the browser function through node rather than pinning a constant:
  the JS side is a live reference, so a check that watches it is worth keeping.

Per the order, all four were fixed regardless. What the fixes buy is that `backend/` no longer
carries a favourable-default pattern that could be copied forward if the spike is ever revived,
and that the percentile divergence now has an executable guard rather than a comment.

---

## S2 — missing or malformed status silently becomes favourable

**Falsifiable outcome sought.** `synthesize([{}])` must not return `final_status == "Green"`;
`synthesize([{"status_color": "red"}])` must not return `"Green"`; both must instead report what
they need; and canonical inputs must band exactly as before.

**Reproduced.** `backend/governance.py:24`, `color = sig.get("status_color", "Green")`.

```
S2a empty sig:        Green
S2b lowercase red:    Green
```

A lowercase `"red"` was admitted by `if color not in counts: counts[color] = 0` and counted under
`counts["red"]`, a key the ladder at `:33-58` never reads, so a red signal reached the `else`
branch and published Green with the conflict text "Agreement — All Channels Stable".

**Change (attempt 1, one atomic change).** `backend/governance.py:9-65, :95-105`.

- Before: `color = sig.get("status_color", "Green")`, then an admit-anything counter.
- After: `CANONICAL_SIGNAL_STATUS = ("Green", "Amber", "Red", "Critical")`, case-sensitive. A
  signal with no `status_color` key, or with a value outside that set, appends a reason to `needs`
  and the whole synthesis returns `_abstain(...)` — `final_status "Indeterminate"`, a new
  `AUTHORITY_MATRIX` row routing "Abstain — resolve signal status before routing", plus the
  `needs` list.
- Also removed, as part of the same defect: `AUTHORITY_MATRIX.get(status, ...["Green"])` at the
  routing seam (`:63` before). A `human_override` naming an undefined status routed Green. It now
  abstains, and the remaining lookup is a direct subscript because every reachable status has a
  row.

Nothing was invented. `Indeterminate` is not a band and carries no threshold; it is the
abstention the house rule already requires — a module missing what it needs abstains and says
what it needs.

**After.** 8 checks pass in `backend/test_run135b_group4_defaults.py`, including the two
regression checks that canonical Red+Amber still routes `Red-Review` and an all-Green array still
routes `Green`.

**Proof the fix can fail.** Reinstated `sig.get("status_color", "Green")` in place of the
presence test. Result: the three abstention checks FAIL, and the lowercase case raises
`KeyError: 'red'` at `counts[color] += 1` — the fault is visible two ways. Restored from a
scratch copy; re-ran; 8/8 green.

**Suite.** `backend/test_run135b_group4_defaults.py` 8 checks, 0 failed. `backend/` had no test
file before this run. Sole consumer of `synthesize` is `backend/main.py:326`, which passes the
dict through unmodified to the `/chat` response.

---

## S3 — missing and zero inputs defaulted into scored outputs

**Falsifiable outcome sought.** `run_all({})` must not return a fully-scored five-signal verdict;
`run_all({"spi":0,"bac":0,"actualPctComplete":0})` must return something *different* from
`run_all({})`; and a complete input set must still score.

**Reproduced.**

```
S3a run_all({}):  ['Red', 'Green', 'Green', 'Red', 'Amber']
S3b zeros:        ['Red', 'Green', 'Green', 'Red', 'Amber']
```

Identical, exactly as stated. Cause: `signal_inputs.get("spi") or 1.0` (`:21`, `:49`, `:74`),
`get("bac") or 1` (`:88`), and `get("actualPctComplete") or get("plannedPctComplete") or 37`
(`:73`). `or` cannot distinguish a missing key from a real zero, and every stand-in it substituted
was favourable: an on-plan SPI of 1.0, a BAC of 1, and a literal 37 per cent complete that appears
nowhere else in the codebase.

**Change (attempt 1, one atomic change).** `backend/simulations.py`.

- Added `_required(signal_inputs, key)` — presence is `key not in d or d[key] is None`, never
  truthiness — returning `(value, None)` or `(None, reason)`.
- Added `_abstain(method_class, needs)` returning `status_color "Indeterminate"` plus a `needs`
  list. That value is deliberately outside `PCEIFGovernanceRouter.CANONICAL_SIGNAL_STATUS`, so
  the S2 router rejects it and abstains in turn: the absence propagates instead of being coloured
  in at the next seam.
- `run_pert` and `run_lob` require `spi`. `run_ccpm` requires `spi` and one of
  `actualPctComplete` / `plannedPctComplete`, with the invented 37 deleted. `run_rcf` requires
  `bac`.
- `run_dsm` reads no `signalInputs` at all — a constant 3x3 matrix — so it scores
  unconditionally and is excluded from the abstention checks *by name*, not by a wildcard.
- `run_rcf`'s `pct_over` now derives from the debias multiplier rather than
  `(p80 / bac - 1) * 100`. Algebraically identical for `bac > 0`, and defined at the real zero BAC
  this change makes reachable — the old form would have raised `ZeroDivisionError` on the very
  input the fix admits. One canonical quantity, per R1.

**After.**

```
run_all({}):          4 x Indeterminate (each carrying needs) + DSM Amber
run_all(all zeros):   scored, and different from the empty case
```

The zero case is materially different from the old reading: CCPM now reports 0.0 per cent chain
complete and bands **Red** where the invented 37 had produced Green; RCF reports a P80 of 0
rather than the `bac = 1` stand-in.

**Proof the fix can fail.** Replaced `_required`'s presence test with truthiness
(`if not signal_inputs.get(key)`). Result: "a real zero is not the same as a missing input" and
"valid zeros are scored, not abstained" both FAIL, and the run then raises
`KeyError: 'pct_chain_complete'` because an all-zero input had abstained instead of scoring.
Restored; re-ran; green.

**Suite.** 16 checks, 0 failed at the time of the S3 commit.

---

## S4 — zero EV treated as absence

**Falsifiable outcome sought.** `_compute({"ev": 0, "ac": 100})` must return `cpi == 0.0`, not
`None`; same shape for SPI; and `ac = 0` must still yield `None` rather than dividing by zero.

**Reproduced.**

```
_compute({"ev":0,"ac":100})  -> {'cpi': None, 'spi': None}
_compute({"ev":0,"pv":100})  -> {'cpi': None, 'spi': None}
```

`backend/main.py:180`, `if cpi is None and ev and ac`. A CPI of exactly 0.0 — every dollar spent,
nothing earned — published as an absent index. Suppression in the reassuring direction.

**Change (attempt 1, one atomic change).** `backend/main.py:180-188`, exactly the fix the order
specifies:

```python
if cpi is None and ev is not None and ac not in (None, 0):
if spi is None and ev is not None and pv not in (None, 0):
```

Presence is `is not None`. The denominator additionally excludes zero, and that exclusion is
arithmetic — the quotient is undefined — not a judgement about the numerator.

**After.** `cpi == 0.0` and `spi == 0.0` on the stated inputs. Four regression checks hold: an
ordinary CPI still computes (0.9), `ac = 0` and `pv = 0` still yield `None`, a genuinely absent EV
still yields `None`, and a supplied CPI is not overwritten.

**Proof the fix can fail.** Restored the `ev and ac` / `ev and pv` truthiness guards. Result:
exactly the two zero-EV checks FAIL, the other 21 still pass — the injection is precisely
targeted, which is what makes the check meaningful. Restored; re-ran; 23/23 green.

---

## S6 — backend and browser compute different P80 quantities

**Falsifiable outcome sought.** The backend's RCF P80 multiplier must equal the browser's; a
check must exist that evaluates both implementations and fails when they diverge; and that check
must itself be shown to fail when either side is changed.

**Reproduced.**

```
backend run_rcf(bac=10,000,000):  debias 1.45, P80 $14,500,000
browser pctile(mult, 0.80):       floor(0.8 * 8) = 6 -> 1.38, P80 $13,800,000
```

`int(len(multipliers) * 0.8)` = `int(7.2)` = 7 against `floor(q * (n - 1))` = 6. A $700,000
overstatement on a $10M BAC, and not a rounding artefact — a different order statistic.

**Third definition found while fixing it.** `run_pert` used `np.percentile(durations, 80)`, which
interpolates linearly between order statistics, where the browser's `runPERT` calls the same
`pctile` as its `runRCF`. So there were three definitions across two files that the backend's own
docstring says are a port of each other. Reported here as an additional instance; both backend
sites now call one helper.

**Naming authority for the canonical definition.** `backend/simulations.py:2-3` — "Python port of
the five client-side JS simulation models". A port matches its original, so the browser definition
at `assets/js/simulations.js:38-42` is canonical and the Python is a transcription of it. This is
independently corroborated by `server/app/simulation/models.py:4`, which calls
`assets/js/simulations.js` "the implementation the instrument has always run" and validates the
in-service port against it. No threshold was invented, and the RCF P50 is unchanged at 1.15 under
both the old and the new code — a useful control, since it shows the change moved only the
quantity that was wrong.

**Change (attempt 1, one atomic change).** `backend/simulations.py`: added `_pctile(sorted_asc, q)`
transcribing the JS, and routed both `run_pert` (sorting `durations` first) and `run_rcf` through
it.

**After.** `debias 1.38`, `rcf_p80_adjusted 13,800,000`, `rcf_p50_adjusted 11,500,000`.

**The divergence check.** `backend/test_run135b_percentile_parity.py`. A helper cannot be shared
across the language boundary, so the check evaluates *both* implementations on one fixture grid —
8 arrays x 9 quantiles = 72 points, chosen to include the RCF multiplier array itself, `n = 1`,
and lengths where `q * (n - 1)` lands on an integer and where it does not — and fails on any
disagreement. It obtains the JS side by extracting the `pctile` and `clamp` function text out of
`assets/js/simulations.js` and evaluating that text under node, rather than reimplementing it in
the check, which would have reintroduced the very duplication the finding is about. If the
extraction cannot locate the function the run exits 3 with `MARKER_MOVED` — a moved marker fails
loudly. If node is absent it prints SKIP and exits 2, which is neither a pass nor a silent
success.

**Proof the check can fail — two independent ways.**
(a) Changed `_pctile`'s index to `int(q * n)`. Result: 3 of 5 checks FAIL and the run prints the
diverging grid points (`python 2.0 vs js 1`, and so on).
(b) Renamed the JS function's parameter so the extraction could not match. Result:
`RuntimeError: node failed (3): MARKER_MOVED: could not locate pctile in .../simulations.js`.
Both restored — `assets/js/simulations.js` byte-identical to HEAD — and reconfirmed 5/5 green.

---

## Iteration log

`finding | attempt | change made | proof result | suite | disposition`

```
S2 | 1 | CANONICAL_SIGNAL_STATUS + Indeterminate abstention row; removed the
     |   sig.get(...,"Green") default and the AUTHORITY_MATRIX .get(...,"Green")
     |   routing fallback | {} -> Indeterminate; "red" -> Indeterminate; canonical bands unchanged | group4 8/8 | RESOLVED
S2 | - | fault injection: reinstate the "Green" default | 3 checks FAIL + KeyError('red') | 8 run, 3 fail | can-fail proved
S3 | 1 | _required (is None, not truthiness) + _abstain; required inputs declared
     |   per model; deleted the literal 37; pct_over from the debias multiplier
     |   | run_all({}) 4x Indeterminate; zeros now score and differ | group4 16/16 | RESOLVED
S3 | - | fault injection: truthiness in _required | 2 checks FAIL + KeyError('pct_chain_complete') | 16 run, 2+ fail | can-fail proved
S4 | 1 | ev is not None and ac not in (None, 0); same for SPI | cpi 0.0 and spi 0.0 on ev=0 | group4 23/23 | RESOLVED
S4 | - | fault injection: restore the ev-and-ac truthiness guards | exactly the 2 zero-EV checks FAIL | 23 run, 2 fail | can-fail proved
S6 | 1 | _pctile transcribing assets/js/simulations.js:38-42; run_rcf and run_pert
     |   both routed through it; np.percentile removed | debias 1.38, P80 $13.8M, P50 unchanged $11.5M | parity 5/5, group4 23/23 | RESOLVED
S6 | - | fault injection (a): _pctile index -> int(q * n) | 3 of 5 FAIL with grid points printed | 5 run, 3 fail | can-fail proved
S6 | - | fault injection (b): rename the JS pctile parameter | exit 3 MARKER_MOVED | run aborts loudly | can-fail proved
```

Nine loop entries, four findings, one attempt each, five fault injections all restored and
reconfirmed. No finding needed a second attempt; none approached the five-attempt cap.

---

## Working-tree status before each commit

```
S2  -> 044c757
 M backend/governance.py
?? backend/test_run135b_group4_defaults.py

S3  -> f498acc
 M backend/simulations.py
 M backend/test_run135b_group4_defaults.py

S4  -> f89076e
 M backend/main.py
 M backend/test_run135b_group4_defaults.py

S6  -> 5a00820
 M backend/simulations.py
?? backend/test_run135b_percentile_parity.py

report (this file)
?? REPORT_2026-09-04_run135b_backend_defaults.md
```

Only intended files in every case. Staging was by explicit path throughout; no -A, no dot.
`assets/js/simulations.js` never appears — it was restored byte-identical after injection (b).

---

## Items outside this agent's scope, noted for whoever owns them

- **`server/app/simulation/models.py` and `fusion.py` carry the survey that found S6 first.**
  The percentile divergence was recorded in a docstring as a reason not to port, and then left in
  the unported module for another hunt to rediscover. Worth a convention: when a port is refused
  because the source diverges, the divergence is a finding against the source, not only a
  justification for the port.
- **The favourable-default family was not in that survey.** S2, S3 and S4 are epistemic rather
  than arithmetic, and an arithmetic comparison did not surface them. If the same survey method is
  used again, it will miss the same class again.
- **`backend/` is unreferenced but still provisioned.** `backend/render.yaml` describes a Render
  service (`lin-project-radar-backend`, free plan, `OPENAI_API_KEY`). Nothing in this repository
  points a browser at it. Whether that service still exists in the Render account, and whether it
  should be torn down, is an owner decision this agent cannot settle from the tree — and it is the
  only decision arising from this scope, though it blocks nothing.
