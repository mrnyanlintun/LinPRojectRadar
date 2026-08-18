# Run 32 final closure - method-class identifier propagation

**Date:** 2026-08-18 (the run began 2026-08-17 and crossed midnight)
**Branch:** `run32-b3-method-class` from `main` at **`6e7ce204567a3a3331ee894436cd21748bde381e`**
**Simulation version:** **`sim-2026.08-v20`**, unchanged
**Participant package:** **`og-participant-2026.08-v9`** (successor; v8 pinned, not regenerated)

Still Run 32. This closes the finding the previous closure carried rather than fixed.

---

## 1. Before and after

The owner named four. **The mechanical inventory found six**, and the browser verification then
found a seventh in a different shape. All are the same defect: a display name was renamed and the
`method_class` identifier - which is a **join key** - was left behind.

| Module | Authoritative current name | Old identifier | Canonical identifier | Renamed by |
|---|---|---|---|---|
| A1.10 | CPI Shrinkage Forecast | `Regression_To_Mean` | `CPI_Shrinkage_Forecast` | Run 28 |
| A1.11 | Independent EAC Reconciliation Index | `ICE_Ratio` | `Independent_EAC_Reconciliation` | Run 28 |
| B3.2 | FAR/Agency EVMS Applicability Monitor | `FAR_Threshold` | `EVMS_Applicability` | Run 31 |
| B3.3 | Versioned A-11 Capital Programming Conformance Check | `OMB_A11_Check` | `A11_Conformance` | Run 31 |
| B3.4 | EVMS Reporting Compliance Monitor | `EVM_Reporting_Threshold` | `EVMS_Reporting_Compliance` | Run 31 |
| B3.5 | Contract Modification Governance Check | `Contract_Mod_Frequency` | `Modification_Governance` | Run 31 |

**Seventh, found by executing the lookup rather than comparing strings:** `categories.js` carried
an explicit remap, `case "DSM_Rework_Cat5": return findSim("DSM_Rework_Propagation")`, translating
A5.1's **current** identifier into one no runner emits. A remap that rewrites a correct key into a
wrong one is the same defect wearing different clothes.

**Current mixed identifiers across the whole tree: 0.**

---

## 2. Two corrections I have to make to my own previous report

### (a) The scope was four; it is six

I reported B3.2-B3.5 last time because my browser probe only inspected a focus list that did not
include A1.10 or A1.11. Deriving the drift mechanically from `registry.VALIDATED` rather than from
a list found two more, from Run 28. The owner's §7 requires mixed identifiers = 0, which four
alone cannot deliver, so all six are propagated.

### (b) I first fixed the wrong file, and the browser check is what caught it

`index.html` loads **`taxonomy.js`** and explicitly **not** `categories.js` - the header says
"taxonomy.js replaces categories.js here". `categories.js` is the researcher-side stack, loaded by
`tests.html`.

My first pass put the alias map, the matched lookup and the A5.1 remap fix into `categories.js`
alone. Every string-based check passed. The authenticated browser session then reported
`window.linMethodClassMatches is not a function`, because the page never loads that file. **I had
fixed a copy the participant never sees** - the "asserted against a copy of the logic" failure this
repository already knows, committed by me. The live file now carries the alias map and every
method-class-to-module-number lookup in it goes through one resolver.

### (c) The consequence was not what I assumed, and I will not overclaim it

The two files join differently, and that matters:

* **`categories.js`** matches `m.method_class === cls` against the signal array. A stale identifier
  matches nothing, `find` returns undefined, the lookup returns `null`. **Measured on the
  pre-change tree**: all six returned `null` with the client's identifier and resolved with the
  server's. Evidence: `code_audit/run32_b3_pre_change_lookup_evidence.json`.
* **`taxonomy.js`**, the live participant surface, resolves through `METHOD_TO_NUM` - built from
  its *own* taxonomy rows - to a **module number**, then matches the stored row by number. A stale
  identifier is self-consistent there and still resolves.

So the demonstrated silent-empty-lookup is on the **researcher-side stack**. On the participant
surface the drift was **latent**, not manifest: it would bite a caller holding a stored row's
server-side class. I tried to measure that direction and my fixture did not match `rowFor`'s
expected shape, so **I am not claiming it**. The identifiers are wrong either way and are fixed
either way; the blast radius is smaller than "the participant surface was broken" and I am saying
so rather than letting the stronger claim stand.

**One consequence is confirmed and was silently active:** `RUN1_PROXY_QUALIFIER` in `knowledge.js`
is keyed by method_class and mirrors `registry.PROXY_QUALIFIERS`. B3.5's key was stale, so a proxy
qualifier the server **still holds** had stopped rendering. Renaming the key restores it.

---

## 3. Every current consumer

`code_audit/run32_b3_method_class_reconciliation.csv` - **6 rows, 6 unique modules, 0 FAIL.**

| Surface | Role | Action |
|---|---|---|
| `assets/js/taxonomy.js` | **LIVE participant surface**; taxonomy rows, `METHOD_TO_NUM`, `getModuleStatus`, `getModuleResult`, `getModuleAbstentionReason` | identifiers propagated; alias resolver added; all lookups routed through it |
| `assets/js/categories.js` | researcher-side stack (`tests.html`) | identifiers propagated; alias map; A5.1 remap corrected |
| `assets/js/knowledge.js` | handbook entries `mc:`; `RUN1_PROXY_QUALIFIER` keys | identifiers propagated; B3.5 key renamed; A1.10 entry removed |
| `server/app/simulation/registry.py` | the authority | unchanged - it was already correct |
| `assets/js/ds_defensibility_evidence.js` | generated | regenerated; carries no method_class, so byte-identical |
| `assets/js/simulations.js`, `sim.js` | **HISTORICAL browser implementations** | **deliberately NOT propagated** |
| `server/app/simulation/models_gov.py` | preserved v19 runners, overridden by `models_cat89` | **not touched** |

**A1.10's proxy qualifier was removed, not renamed.** The server withdrew it when Run 28 made the
module canonical. Renaming the key would have repaired a stale key into a stale claim - newly
surfacing an assertion the source of truth no longer makes.

`simulations.js` and `sim.js` are declared historical test artefacts by
`client_algorithm_version.js`: "the server is the single computational authority and a second
implementation is the defect rather than the backup." Propagating into them would have falsified
that record.

---

## 4. Aliases

`LIN_HISTORICAL_METHOD_CLASS` maps each **current** identifier to the superseded one, for **stored
rows only**. A period result written before a rename carries the old identifier. Nothing emits an
alias, no taxonomy row carries one, and the guard asserts no superseded identifier is ever a
current primary.

---

## 5. Browser verification

`code_audit/run32_b3_browser_verification.csv` - **21 rows: 20 PASS, 0 FAIL, 1 NOT_VERIFIED.**

**Previous browser failures: 4. Final browser failures: 0.** The four were the B3.2-B3.5 taxonomy
rows and they pass because the identifiers are now correct, not because the rows were rewritten or
the expectation moved.

A participant was provisioned through the normal research route, the session established as the
client does (`sessionStorage['og-session-token']`), against a throwaway migrated SQLite database.
Chromium's headless shell was used (the installed build removed old headless mode);
`playwright install` was not run. `window.confirm` forced false, Google SSO aborted. Production
Postgres never contacted.

**One check is NOT_VERIFIED and is not counted as a pass.** The handbook renders authenticated and
carries **no superseded module name anywhere**, which is verified. But the per-module method
documentation did not appear by any navigation path attempted - handbook, "Methods and Framework",
every collapsible section expanded. The arrays are module-local to `knowledge.js` and are not
exposed on `window`. **This is a reachability limit of the surface, not a consequence of this
change:** "Minimax Regret Decision Rule", renamed by the previous closure, is equally absent. Those
identifiers are guarded at source by `test_run32_method_class_agreement.py` section 2.

---

## 6. The six-fault campaign

`code_audit/run32_b3_fault_injection.csv`

| | |
|---|---|
| Attempted / applied / RED for the intended reason / restored GREEN | **6 / 6 / 6 / 6** |
| NOT_APPLIED, crashes accepted as RED, unrelated accepted as RED | **0 / 0 / 0** |

Faults 1-4 restore each B3 identifier; fault 5 neuters the alias matcher so a lookup silently
returns an empty result - the exact failure mode that hid this defect; fault 6 makes a generated
file disagree with its authority source, which is the shape of the root cause the previous closure
found in the defensibility generator.

---

## 7. Version and package

**`sim-2026.08-v20` stands.** **No `server/app/` file changed at all**, and the profile was proved
rather than assumed: all **95 dispatched modules** executed on identical governed inputs, digest
`a9577151e71ab7211bde450a2b69f82827fde130b7e89c0a1a015f18e137f45a` - **byte-identical to the
previous closure's baseline.**

**v9 minted, v8 pinned to `6e7ce20`, not regenerated.** Three files moved: `categories.js`,
`knowledge.js`, `taxonomy.js`. **The experimental sequence is unchanged** - `decision.js`,
`decision-ui.js`, `workspace.js`, `deepdive.js` and both questionnaires are byte for byte identical
to v8, and the guard asserts the moved set is exactly the three declared.

---

## 8. Acceptance

**Full suite: 154 suites, 12523 / 12523.**

| Requirement | Result |
|---|---|
| B3.2-B3.5 canonical identifiers propagated | yes, plus A1.10, A1.11 and A5.1 |
| Current mixed identifiers | **0** |
| Empty lookups caused by identifier mismatch | **0** |
| Browser failures | **0** (1 NOT_VERIFIED, stated) |
| Defensibility reconciliation | **101 / 101**, 0 unsupported claims |
| Voting | **exactly 2** - A1.7, A1.8 |
| MCV / Category-9 gate / participant protocol | disabled / unchanged / unchanged |
| Production Postgres | never accessed |

---

## 9. Carried findings

1. **`RUN1_PROXY_QUALIFIER` is 27 entries stale.** It holds 30 keys; the server now holds 5
   qualifiers. Runs 28-32 withdrew the rest as modules became canonical and the mirror was never
   updated, so the handbook still attributes proxy qualifiers to modules that no longer carry one.
   Only the two entries whose **keys** were drifting were touched here. This is the same
   class as the defensibility drift, on a third surface, and needs its own authorisation.
2. **`categories.js` and `taxonomy.js` are near-duplicate taxonomies** that must be kept in step by
   hand. The alias map now exists in both and a guard asserts they agree, but the duplication is
   the underlying hazard and one generator would remove it.
