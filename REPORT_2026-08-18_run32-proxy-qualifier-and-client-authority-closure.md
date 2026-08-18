# Run 32 final closure - proxy qualifiers, one client authority, and the handbook surface

**Date:** 2026-08-18
**Branch:** `run32-qualifier-authority` from `main` at **`19a70556fe1b6ee8d17706cfbbc5d72e12051086`**
**Simulation version:** **`sim-2026.08-v20`**, unchanged
**Participant package:** **`og-participant-2026.08-v10`** (successor; v9 pinned, not regenerated)

Still Run 32. This closes all three things the previous closures carried.

---

## 1. The nine facts this report leads with

1. **Client qualifier entries inspected: 29, not 30.** The owner's figure was written against my
   previous report, which measured 30 before that closure removed A1.10's entry. Derived from the
   file, not carried forward.
2. **Final classification distribution:** `WITHDRAWN` **27**, `CURRENT_REQUIRED` **2**. No
   `HISTORICAL_ONLY`, no `BACKWARD_ALIAS_ONLY`, no `CURRENT_SERVER_QUALIFIER_MISSING`, and no
   sixth classification was needed. 0 unclassified, 0 duplicate keys.
3. **Current server qualifiers: 5 before, 2 after.** Three were themselves stale.
4. **Silent empty lookups found: 0 - and that is the opposite of what was expected.** Every one of
   the 29 keys was in live use by a current module, so the lookup fired for all of them. The
   defect was **over-claiming**, not emptiness: 27 canonical modules were being told to a reader
   as proxies.
5. **Qualifier actions:** 27 client entries withdrawn, 3 stale server entries withdrawn, 2 kept.
6. **Authority resolution:** both client artifacts are now **generated from one authority**;
   neither is hand-maintained.
7. **Handbook surface: `CURRENT_REQUIRED_SURFACE`.** It exists, it is reachable, and it is now
   verified - **101 module sections rendered** in an authenticated browser.
8. **Participant package:** v10 minted, v9 pinned.
9. **Simulation version:** v20 stands, proved by an identical 95-module profile hash.

**And one defect this closure found in its own predecessor, see section 8: a shipped
`RangeError` on the live participant surface.**

---

## 2. The measurement came first, and it changed the diagnosis

The lookup was executed against the real files **before any edit**
(`code_audit/run32_pre_change_qualifier_measurement.json`). `modDoc()` resolves
`RUN1_PROXY_QUALIFIER[m.mc]` and renders `Status. Proxy: <text>. Advisory, non-voting.`

The expectation going in was empty lookups. The measurement found none: **all 29 keys resolved to
a live module and rendered a Proxy line.** The defect was that 27 of those lines were false.

---

## 3. Classification, established from the production route

**A qualifier is not withdrawn because the server currently lacks it.** The rule applied is the
one the runs state and act on, quoted from their own records:

> Run 29: "removed six proxy qualifiers from `registry.py` **because the six modules they
> described now perform their canonical methods**"
> Run 30: legacy-proxy markers "8 proxy qualifiers, 3 truthful labels" -> **"none"**

So a proxy qualifier is `WITHDRAWN` when the module it described was repointed onto its canonical
method - established from whether the module's runner resolves into a canonical layer and requires
a governed structure.

| Classification | Count | Basis |
|---|---|---|
| `WITHDRAWN` | **27** | routes into canonical v3/v4/v5/v6/v7; the proxy it described no longer exists |
| `CURRENT_REQUIRED` | **2** | A1.2 CUSUM and D1.2 Portfolio Outlier: no canonical layer, still the proxy, server still holds it |

### Three of the five server qualifiers were themselves stale

`registry.PROXY_QUALIFIERS` still held **B3.5, B4.3 and B4.4**, whose modules Runs 31 and 32 had
repointed. The dictionary's own comment block states the rule and warns about this exact
direction - "it would advertise a weakness the code no longer has" - and neither run extended it.
So the served defensibility object was telling readers that B4.3 is *"an explainable four-rule
checklist, not a constraint-satisfaction solver"* **about a module that is a constraint-satisfaction
solver**, and that B4.4 is *"four deterministic EAC variants"* about a module that refuses to run
without a governed action-by-scenario matrix. All three withdrawn; the sentences are preserved in
the reconciliation CSV.

**A1.10's entry was removed rather than renamed** in the previous closure, and that stands: the
server had withdrawn it, so renaming the key would have repaired a stale key into a stale claim.

**`RUN1_DISABLED`, the sibling mirror, was measured and is exactly in step** - 8 client keys
against 8 server disabled modules. No action.

---

## 4. Before and after lookup behaviour

| | before | after |
|---|---|---|
| Client qualifier keys | 29 | **2** |
| Server qualifiers | 5 | **2** |
| Modules rendering a "Proxy:" line | 29 | **2** |
| Modules rendering a proxy line the server does not support | **27** | **0** |
| Empty lookups caused by qualifier drift | 0 | **0** |
| Wrong-module fallback results | 0 | **0** |

Verified in the authenticated browser across 101 rendered module sections: both remaining
qualifiers render their exact server text, and no module presents a withdrawn qualifier.

---

## 5. One authority for the two client artifacts

**Determined mechanically, not assumed.** `index.html` loads `taxonomy.js`; `tests.html` loads
`categories.js`. Both carried a hand-maintained copy of the same 101-module taxonomy, and **they
had already silently diverged**: nine modules carried `disabled: true` in `taxonomy.js` and not in
`categories.js`.

Outcome chosen: **generated derivative**. `server/tools/build_client_taxonomy.py` writes the
`window.LIN_CATEGORIES` block into **both** files. Nothing owns a field twice:

| Field | Authority |
|---|---|
| `name`, `method_class`, `disabled` | `registry.py` and the dispatch tables - the identifiers the runners actually emit |
| category identity, colour, description; module `id`, `num`, `required`, `sectors`, level flags | `server/tools/taxonomy_authority.json` |

`categories.js` gains the nine missing `disabled` flags. **The runtime taxonomy data is otherwise
unchanged - regenerating reproduced the live rows exactly, 0 differences.**

`simulations.js` and `sim.js` remain untouched historical artefacts, as
`client_algorithm_version.js` declares.

### The guard's oracle is not the other file

`test_run32_client_authority.py` (18 checks) compares the generated artifacts against **the
registry authority + the server qualifier authority + the generator's own `--check`**. Comparing
`categories.js` to `taxonomy.js` would be two objects under test agreeing with each other - the
same shape as the defensibility generator that compared its output against itself and stayed green
through a wrong derivation for two runs.

---

## 6. The handbook surface: `CURRENT_REQUIRED_SURFACE`

**It exists, and two closures recorded it `NOT_VERIFIED` because the navigation was wrong.**

The route is: Handbook -> the **"Methods and Framework" tab** -> a per-category *module reference*
topic, registered in `MODREF_TOPICS`, resolved by `lookupTopic()`, rendered through `modDoc()`.
My earlier attempts clicked a button whose text began "Methods and Framework" in a different
state, and never reached the tab.

Reached this time with an authenticated session against a throwaway database: **12 module-reference
topics, 101 module sections rendered.** One further probe bug was found and fixed on the way -
`collapsibleSection()` hides section bodies with `display:none`, and `innerText` returns empty for
hidden elements, so the content must be read with `textContent`.

Guarded from both sides now: `test_run32_handbook_surface.py` proves the surface is **wired** and
covers all 101 registry identities; the browser run proves it **renders**.

---

## 7. Browser verification

`code_audit/run32_proxy_qualifier_browser_verification.csv` - **17 rows, 17 PASS, 0 FAIL, 0
NOT_VERIFIED.**

Authenticated through the normal research login route against a throwaway migrated SQLite
database. `window.confirm` forced false, Google SSO aborted, production Postgres never contacted.
Chromium's headless shell was used; `playwright install` was not run.

---

## 8. The defect this closure found in its own predecessor

**The previous closure shipped a `RangeError` to the live participant surface, and every guard
stayed green.**

Rewriting the three method-class lookups in `taxonomy.js` to go through one resolver caught the
**resolver's own body** as a fourth call site:

```js
function numForMethodClass(methodClass) {
  var num = numForMethodClass(methodClass);   // calls itself
```

Executed against a project with a stored row, `getModuleStatus`, `getModuleResult` and
`getModuleAbstentionReason` all threw **`RangeError: Maximum call stack size exceeded`**.

It survived because **every guard on that file compared strings**, and the one execution probe
drove `categories.js` - the file the live page does not load. That is the same lesson twice over,
one level deeper than last time.

Fixed, and now guarded by execution: `test_run32_method_class_agreement.py` section 4c executes all
three live consumers for every registered module against a stored row and requires that none
throws, none returns a silent null, and none returns another module's row.

---

## 9. The fourteen-fault campaign

`code_audit/run32_qualifier_fault_injection.csv`

| | |
|---|---|
| Attempted / applied / RED for the intended reason / restored GREEN | **14 / 14 / 14 / 14** |
| NOT_APPLIED, crashes accepted as RED, unrelated accepted as RED | **0 / 0 / 0** |

The first pass scored 12: fault 6 mutated the alias branch, which a current identifier never
reaches, so the guard stayed green and **the campaign refused to credit it**; and fault 14's
baseline was red because the recursion fix landed after v10 was minted. Both were resolved by
repointing and regenerating, never by loosening the rule.

Faults 8, 9 and 13 are the ones that test whether this closure worked - two generated files
disagreeing, the live app loading a stale artifact, and a nonexistent surface marked verified - and
all three turn their guard red.

---

## 10. Version and package

**`sim-2026.08-v20` stands.** All 95 dispatched modules executed on identical governed inputs
before and after: digest `a9577151e71ab7211bde450a2b69f82827fde130b7e89c0a1a015f18e137f45a`,
identical on both sides. The only `server/app/` change is the removal of three metadata strings
from `PROXY_QUALIFIERS`, which no calculation reads.

**v10 minted, v9 pinned to `19a7055`, not regenerated.** Four files moved: `categories.js`,
`knowledge.js`, `taxonomy.js`, `ds_defensibility_evidence.js`. The experimental sequence is
unchanged - `decision.js`, `decision-ui.js`, `workspace.js`, `deepdive.js` and both questionnaires
are byte for byte identical to v9, and the guard asserts the moved set is exactly the four declared.

---

## 11. Acceptance

**Full suite: 156 suites, 12554 / 12554.**

| Requirement | Result |
|---|---|
| Current proxy-qualifier drift | **0** |
| Current mixed method classes | **0** |
| Empty lookups caused by drift | **0** |
| Current authority sources | **1** |
| Browser failures / required surfaces not verified | **0 / 0** |
| Defensibility reconciliation | **101 / 101**, 0 unsupported claims |
| Simulation version | **v20**, profile proved identical |
| Voting | **exactly 2** - A1.7, A1.8 |
| MCV / Plithogenic / Quantum / Hypersoft | disabled / disabled / archived / disabled |
| Category-9 gate, raw and missing-assessment bypass | unchanged, 0 / 0 |
| Participant protocol | **unchanged** |
| Production Postgres | never accessed |

---

## 12. Carried findings

1. **`ds_defensibility_data.js`**, the narrative handbook, is still generated from an earlier draft
   rather than from the registry. Its per-capability prose has never been reconciled against the
   instrument. It is the last hand-authored metadata surface of this kind.
2. **`taxonomy.js` and `categories.js` still hold separate hand-written CODE** (their status
   accessors). Only the taxonomy DATA is generated. The accessors differ by design - one reads the
   stored row, the other re-derives for the researcher deep-dive - but they remain two
   implementations of a similar lookup, which is what allowed the recursion defect to hide.
