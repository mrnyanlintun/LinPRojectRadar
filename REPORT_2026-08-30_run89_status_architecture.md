NO MIGRATION WAS ADDED. Migration head is unchanged at `0030_extraction_contract`.

# Run 89 — the status architecture

**Repository:** `/home/user/LinPRojectRadar`, branch `main`.
**Starting commit:** `2c02e537a05a35cbe5cdb3a12c24fef2a594a37d` ("Run 88 report: the 33 retained
specifications printed verbatim; B1.2 weighs two dropped arms"), clean tree, `main == origin/main`.
**Ending commit:** `4c35bef` (this report adds one more). Eight commits, none pushed.
**Python:** system `python3` 3.11.15 at `/usr/local/bin/python3`. There is no repo venv.
**`ANTHROPIC_API_KEY`:** not set — verified by `os.environ.get("ANTHROPIC_API_KEY")` returning
`None`. No model behaviour is reported anywhere below.

---

## 1. The owner's deployment sequence

**No migration.** Nothing to run against the database.

```bash
# 1. From the repository root, on main:
git log --oneline -9        # the eight Run 89 commits plus Run 88's report

# 2. Push when you are ready. I did not push.
git push origin main

# 3. Verify the stamp and the population (from server/):
cd server
python3 -c "import sys;sys.path.insert(0,'.');
from app.simulation.models import SIMULATION_VERSION as V;
from app.simulation.registry import service_index, registry_index, available_modules;
print(V, len(registry_index()), 'registered,', len(service_index()), 'in service,',
      len(available_modules()), 'computed')"
# expect: sim-2026.08-v43 101 registered, 60 in service, 59 computed

# 4. The four Run 89 suites (from server/), each with a throwaway SQLite:
python3 tools/test_run89_required_core.py          # expect ALL PASS
python3 tools/test_run89_data_integrity_gate.py    # expect ALL PASS
python3 tools/test_run87_comparison_only.py        # expect ALL PASS
node ../server/tools/test_run89_indeterminate_brief.js   # run from repo root: node server/tools/test_run89_indeterminate_brief.js
```

**What to press, and what to expect per category.** Open any project detail page for a period
that has been computed.

| Category | What you will now see |
|---|---|
| A1 Cost and EVM Performance | **Required.** Unchanged. If it carries no posture the project status is Indeterminate. |
| A2 Schedule Performance | **Required.** Unchanged. Same. |
| A3 Cost Risk | **Required.** Unchanged. Same. |
| A6 Delivery Quality Performance | **Required.** Unchanged. Same. |
| A4 Document-Derived Condition Signals | **Supporting.** Never blocks the official status. Never produces a Green because no documents were supplied. |
| A5 System Dynamics & Complexity | **Supporting.** Now shows **five** modules, not seven: A5.1 and A5.5 left service. The category is NOT removed. |
| B1 Signal Synthesis | Four modules. **B1.2 Weighted Voting now reads the six category postures**, so it abstains during the module pass and carries its reading after the rollup. Its band still cannot set B1's status. |
| B4 Decision Optimization | Now shows **one** module, B4.3. B4.4 left service. The category is NOT removed. |
| C1 Data Integrity | Unchanged on screen: seven modules, no bands, no votes. Its specification now states its role is **eligibility**. |
| Project header | Where any of A1/A2/A3/A6 has no posture the status reads **Indeterminate**, and the Executive Brief renders the full Indeterminate brief rather than a health posture. **On the richest stored row this is what you will see** — only A1 of the four carries a posture today. |

**One thing you should confirm.** `server/tools/build_run37_acceptance.py`'s `CANDIDATE`
constant is described in the tree as your hand-set assignment. The generator refused with exit 3
and *named* the value the candidate identity describes, and I wrote exactly that value and
nothing else:

```
CANDIDATE = "085d14d90dd4b2ada33b6d11928fb0ecb362bbef"   # before
CANDIDATE = "6ccb650cf8de57c8a09afb114dea0b6d70710368"   # after
```

If you would rather set it yourself, revert commit `fca31fe` and paste that value.

---

## 2. Every specification edit, before and after, verbatim

Two specifications were edited, both named by the order: `B1_signal_synthesis.md` (section 2) and
`C1_data_integrity.md` (section 3). **No other specification was touched.**

### 2.1 `specifications/B1_signal_synthesis.md`, edit 1 of 3

**BEFORE:**

```
Three of the four (B1.2, B1.3, B1.4) read the **four assembled arms** the signal package carries —
`evm` the cost and schedule indices, `mc` the cost forecast, `cusum` the performance trend, `doc`
the document risk score — resolved through `canonical_v5.governed_signals_from_project`, each with
its identity, state, period, source provenance, evidence-lineage body, qualification state and
abstention reason.
```

**AFTER:**

```
Two of the four (B1.3, B1.4) read the **four assembled arms** the signal package carries —
`evm` the cost and schedule indices, `mc` the cost forecast, `cusum` the performance trend, `doc`
the document risk score — resolved through `canonical_v5.governed_signals_from_project`, each with
its identity, state, period, source provenance, evidence-lineage body, qualification state and
abstention reason.

**B1.2 no longer reads the arms.** The owner ruled at Run 89 that Weighted Voting reads the **six
performance category postures**, not the arms: two of the four arms trace to modules he has
dropped — `mc` to the Monte Carlo EAC forecast retired at Run 43, and `doc` to the Document Risk
Score, which carries `STOPPED. Not specified.` — so half of what the retained synthesiser weighed
came from outside the retained roster. B1.2's inputs and rule are stated in its own section below.
The arms are **not** deleted: B1.3, B1.4, `arm_lineage.py`,
`canonical_v5.governed_signals_from_project`, `signal_package.py` and `models_evc.py` (which
serves B2.2–B2.9, Evidence Combination) all still read them.
```

### 2.2 `specifications/B1_signal_synthesis.md`, edit 2 of 3

**BEFORE:**

```
Where no governed signals were supplied at all, B1.2, B1.3 and B1.4 report nothing, in these words:
```

**AFTER:**

```
Where no governed signals were supplied at all, B1.3 and B1.4 report nothing, in these words
(B1.2 no longer reads governed signals and states its own nothing-to-report sentence below):
```

### 2.3 `specifications/B1_signal_synthesis.md`, edit 3 of 3 — the whole B1.2 section replaced

**BEFORE:**

```
## B1.2 — Weighted Voting

**Identity.** Live id `B1.2`. Method class `Weighted_Voting`. Class-weighted voting over the
governed signals.

**Required inputs, by their exact `signal_inputs` field names.**
`signals` — the assembled arms, read through `governed_signals_from_project`.
`signalWeightPolicy` — a mapping carrying `weights` (a weight per signal id), `set_by` and
`authority`. **Required. There is no default weight anywhere in this function**, so a project with
no policy cannot be given one implicitly.

**Method.**
```
Vote(c) = sum over voting signals i of  w_i * I(s_i = c)
winner  = argmax over c of Vote(c)
```
Weights must be non-negative and are **normalised to sum to one over the eligible independent
signals actually voting**, which is what makes class votes comparable between projects with
different signal counts. The classes are the four severity classes in order.

**Bands.** The winner is emitted as `status_color`. Where there is no unique winner,
`status_color` is `None` and `tied_classes` names the tied classes.

**Interpretation.** The weighted vote says which state carries most of the authority-assigned
weight, and the normalised weights and their provenance travel with the reading so a reader can see
whose judgment produced them.

**Nothing to report.**
1. No governed signals: the shared sentence above.
2. Every governed signal abstained: `"every governed signal for this project abstained, so there
   is nothing to weigh and no vote is reported"`.
3. `signalWeightPolicy` absent or not a mapping: `"Awaiting a weighting policy for this project's
   governed signals. A weighted vote cannot be taken without stated weights, and none is
   assumed."`
4. The policy states no weights: `"The a weighting policy for the project's governed signals: a
   weight for each signal, and the authority that set it provided for this project states no
   weights, so no weighted vote is taken and no weight is assumed for any signal."`
5. The policy omits a weight for a voting signal: the same sentence stem ending `"...does not
   state a weight for every signal being voted on, so no weighted vote is taken and no weight is
   assumed for the signals it omits."`
6. A negative weight: the same stem ending `"...states a negative weight, which a vote is not
   defined on, so no weighted vote is taken."`
7. Every voting signal weighted zero: `"the weighting policy for this project gives every voting
   signal no weight at all, so no winner is reported"`.
```

**AFTER:**

```
## B1.2 — Weighted Voting

**Identity.** Live id `B1.2`. Method class `Weighted_Voting`. Class-weighted voting over the **six
performance category postures**.

**What it reads, and when.** The **category postures** produced by the category rollup — the same
`category_statuses` every surface renders. It reads **no arm**, **no signal package** and **no
`signalWeightPolicy`**. Because the postures are the rollup of the modules this run dispatches,
they do not exist at module dispatch: B1.2 abstains at dispatch naming exactly that, and is
evaluated in a **second pass** after the rollup, in `compute.compute_project`. It remains a module
with a registry row, a method class and this specification; what moved is *when* in the run it is
evaluated.

**The weight profile. The owner's stated authority, Run 89 — his decision, not a derived value,
not a literature value, and not calibrated.**

| Category | Weight |
|---|---|
| Cost and EVM Performance (`A1`) | 0.25 |
| Schedule (`A2`) | 0.25 |
| Cost Risk (`A3`) | 0.15 |
| Document Signals (`A4`) | 0.10 |
| Delivery Quality (`A6`) | 0.15 |
| Systems and Dynamics (`A5`) | 0.10 |

Total 1.00. **Data Integrity (`C1`) is not in this profile and must never be added to it.**
Integrity is a precondition for using the criteria, not a criterion to trade against performance.

**Method.**
```
Vote(c) = sum over assessed categories k of  w_k * I(posture_k = c)
winner  = argmax over c of Vote(c)
```

**A category with no posture carries no weight, and the remainder is renormalised.** This is the
category's own shared rule 3 applied one level up — *"Missing evidence never defaults Green. An
abstaining signal casts no vote, **carries no weight**, and cannot occupy a position among the
worst."* Carrying no weight is not carrying weight toward zero. So an unassessed category is
**removed from the denominator** and the weights of the categories that do carry a posture are
renormalised to sum to one, which is also what the arm-based rule already did over its eligible
signals. It is **not** scored as a zero, **not** treated as Green, and **not** dropped without
renormalising — the first would score an absence and the last would make class votes incomparable
between projects. The reading reports `assessed_categories`, `unassessed_categories` and
`renormalised` so the reader can see which categories were in the denominator.

**Bands.** The winner is emitted as `status_color`. Where there is no unique winner,
`status_color` is `None` and `tied_classes` names the tied classes.

**Comparison only. It cannot set a status.** B1.2 is in
`spec_projection.COMPARISON_ONLY_MODULES`, so its band is never admitted to its category's rollup
on the specification-reading path; and on the Python path it is evaluated *after* the rollup that
produced its own input, so it is structurally incapable of reaching it. Conservative Dominance
alone sets the official project status.

**Interpretation.** The weighted vote says which state carries most of the owner's assigned weight
across the performance categories, and the normalised weights and their provenance travel with the
reading so a reader can see whose judgment produced them.

**Nothing to report.**
1. At module dispatch, before the rollup: `"Weighted Voting reads the six performance category
   postures. Those postures are the rollup of the modules this run dispatches, so they do not
   exist yet at module dispatch; this module is evaluated in the second pass, after the category
   rollup."`
2. No weighted category carries a posture: `"none of the six weighted performance categories
   carries a posture, so there is nothing to weigh and no weighted vote is reported"`.
```

*(One later line in the AFTER text was amended once more, after the `votes` collision was
measured. Its final form reads: "The reading reports `assessed_categories`,
`unassessed_categories` and `renormalised` so the reader can see which categories were in the
denominator, and the class weight distribution on **`class_votes`** — deliberately not on
`votes`, which `registry.run_all` already uses on every module row for the boolean *is this
module one of the core voting modules*.")*

### 2.4 `specifications/C1_data_integrity.md` — one insertion after the opening paragraph

**BEFORE:**

```
# Category C1 — Data Integrity

Seven modules: C1.1 through C1.7. These are **evidence qualification measures**. They read how
complete, how fresh, how traceable and how internally consistent the project's own evidence is —
not how the project is performing.
```

**AFTER:**

```
# Category C1 — Data Integrity

Seven modules: C1.1 through C1.7. These are **evidence qualification measures**. They read how
complete, how fresh, how traceable and how internally consistent the project's own evidence is —
not how the project is performing.

## The category's role: ELIGIBILITY, not performance

**The owner's ruling, Run 89 section 3.** This category's role is **eligibility only**. It
determines whether methods and categories have sufficient evidence to produce a posture. It
produces **no project-health posture**. It enters **neither Conservative Dominance nor Weighted
Voting**, and no reading in it can reach the official project status by any path.

**Information Completeness Ratio (`C1.5`) is the eligibility gate the owner named.** Its registry
note already says what it is for: *"authoring-time quality gate; not participant-facing; must not
enter project status aggregation"*.

**Three independent barriers keep this category out of the project status, and all three are
executable.** Removing any one of them still leaves the other two:

1. **The group predicate.** Every C1 module sits in registry group `C`, and
   `compute.contributes_to_project_status` returns `False` for group `C`. The category can carry
   an entry, be rendered, and still contribute nothing.
2. **No band is ever asserted.** `models_cat89._route` sets `status_color = None`,
   `band_asserted = False`, `category_9_metadata_only = True` and `voting_eligible = False` for
   every module whose id begins `C1.`.
3. **The severity rule has nothing to rank.** `fusion.worst_band` over no asserted band returns
   `None`, not `Green`.

`tools/test_run89_data_integrity_gate.py` proves this by injecting an adverse `C1.5` band on both
status paths and measuring that nothing moves — and proves the check can fail by neutralising the
group predicate and measuring the project status flip to the injected band.

**What "sufficient evidence" produces, and what it does not.** A category with insufficient
eligible evidence returns **not assessed** — a **null status** — never `Green`, `Amber` or `Red`.
*Not assessed* and *never called* are **not the same thing in this tree, and they are not two
states**: *never called* is a state (the client's `not_run`, "Not called yet", where no reading is
stored at all), while *not assessed* is the **absence of a band on a reading that exists**, which
occurs across `computed`, `abstained`, `out_of_order` and `failed` alike and renders as "No band".
No new state is invented for either.

**What this category does NOT compute.** There are **no per-category completeness percentages** in
this category. `C1.5` computes one **package-level** ratio over the components of a governed
information package; it has no notion of a performance category and produces no figure per
category. Producing per-category completeness would require a structure that declares, per
category, which components its methods require — no such structure exists in the tree, and none is
invented here.
```

---

## 3. Per goal: reached or not, every iteration

### Goal one — Weighted Voting reads category postures. **REACHED, one iteration.**

**Iteration 1 — measured.** `models_gov.run_weighted_voting` called
`canonical_v5.weighted_voting(_governed(si, cutoff), si["signalWeightPolicy"])`. Its full prior
body, verbatim:

```python
def run_weighted_voting(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    from .canonical import StructureAbsent
    from .canonical_v5 import SignalNotEligible, weighted_voting
    try:
        out = weighted_voting(_governed(si, period_cutoff), (si or {}).get("signalWeightPolicy"))
    except (SignalNotEligible, StructureAbsent) as exc:
        return dict(insufficient("Weighted_Voting"), abstention_reason=str(exc))
    if not out.get("estimable"):
        return dict(insufficient("Weighted_Voting"), abstention_reason=out.get("reason"))
    return {
        "method_class": "Weighted_Voting",
        "status_color": out["winner"],
        "votes": out["votes"],
        "unique_winner": out["unique_winner"],
        "tied_classes": out["tied_classes"],
        "tie_policy": out["tie_policy"],
        "normalised_weights": out["normalised_weights"],
        "weight_provenance": out["weight_provenance"],
        "lineage": _synthesis_lineage(out),
        "evidence_metric": (
            f"Weighted vote: {out['winner']}" if out["unique_winner"]
            else "Weighted vote: no single state carries most of the weight"),
    }
```

**§2.2 — who reads the four arms. Established before touching anything, as required.** The full
reader list, each verified by grep and by import:

| Reader | What it is | Left intact? |
|---|---|---|
| `simulation/arm_lineage.py` | the lineage declaration for the four arms | yes |
| `canonical_v5.governed_signals_from_project` (`:294`, importing at `:319`) | builds the governed signal list | yes |
| `simulation/signal_package.py:162` | builds `signals["evm"]` | yes |
| `models_gov.py:41` | re-exports the arm names "for existing readers" | yes |
| `models_gov.run_majority_rules` (B1.3), `run_worst_n_of_m` (B1.4) | still synthesise the arms | yes |
| **`simulation/models_evc.py:25`** | **imports `ARM_LINEAGE_BY_KEY, one_reading_per_body`** | yes |

**The order's `models_evc.py` question, answered by execution.** `models_evc.py` exports
`EVC_EXTENSIONS`, imported by `models.py:1339`. Measured:

```
>>> from app.simulation.models_evc import EVC_EXTENSIONS; sorted(EVC_EXTENSIONS)
['B2.2', 'B2.3', 'B2.4', 'B2.5', 'B2.6', 'B2.7', 'B2.8', 'B2.9']
```

**`models_evc.py` serves the eight modules B2.2–B2.9 of category B2, Evidence Combination.** That
is the concrete second consumer §2.2 anticipated, and it is why the arms are not deleted.

**Hypothesised.** The ordering problem is real: category postures are the rollup of the modules
dispatch produces, so no module can see them at dispatch. Of the three options the order left
open, (b) "the postures are passed into `si` before dispatch" is **impossible** — they do not
exist yet — and (c) "B1.2 moves into the projection layer" would stop it being a module with a
registry row. **Option (a), a pass-two/post-rollup computation, was chosen**, and it turns out to
carry a bonus the other two do not: a module evaluated *after* the rollup is **structurally
incapable of reaching the rollup that produced its own input**, which is the same conclusion
Run 87 reached by admission, reached here by ordering instead.

**Changed.** One thing: B1.2's input path.
1. `weighted_category_vote(category_statuses)` and `weighted_voting_result(...)` in
   `models_gov.py`, carrying `WEIGHTED_VOTING_CATEGORY_WEIGHTS` (the owner's profile) and
   `WEIGHTED_VOTING_EXCLUDED_CATEGORIES = {"C1"}` behind an **executable assert**.
2. `run_weighted_voting` now abstains at dispatch with a reason *about the postures*.
3. `compute.compute_project` runs the second pass after the rollup and replaces B1.2's row.

**Measured after — on the real stored row `01M11XEYX5V5S6CQSCSJBHBV6T`:**

```
project_status Red        <- IDENTICAL to the stored row
  A1 Red 6                <- IDENTICAL
  A2 None 2   A3 None 3   A4 Red 3   A6 None 3   B1 Red 2   B3 None 2   <- all IDENTICAL
B1.2 COMPUTED Red  "Weighted vote over 2 of six performance categories: Red"
                   {'A1': 0.7142857142857143, 'A4': 0.28571428571428575}
```

B1.2 computes from the postures, and every category status and the project status are unchanged —
so it reached nothing.

**The six weights, measured to sum to 1.00 with all six assessed:**

```
normalised_weights {'A1': 0.25, 'A2': 0.25, 'A3': 0.15, 'A4': 0.1, 'A6': 0.15, 'A5': 0.1}
votes {'Green': 0.85, 'Yellow': 0.0, 'Amber': 0.0, 'Red': 0.15}  winner Green
```

**§2.3 — a category not assessed. The rule, and why it is derivable rather than invented.** The
order named three candidates and chose none. The tree chooses: `B1_signal_synthesis.md`'s own
shared rule 3, which this run did not write, says *"Missing evidence never defaults Green. An
abstaining signal casts no vote, **carries no weight**, and cannot occupy a position among the
worst."* **Carrying no weight is not carrying weight toward zero.** So the unassessed category is
removed from the denominator and the rest are renormalised — which is also what
`canonical_v5.weighted_voting` already did ("normalised to sum to one over the eligible
independent signals actually voting"). Scoring it as zero would score an absence; dropping the
term without renormalising would make class votes incomparable between projects. The
specification now states this, and it is measured: with A2/A3/A6/A5 unassessed the denominator is
A1+A4 and the weights renormalise to 0.714/0.286, with `renormalised: true` and
`unassessed_categories: ['A2','A3','A6','A5']` on the reading. **No fourth rule was invented.**

**§2.4 — it remains comparison-only, and the test can still fail.** `COMPARISON_ONLY_MODULES` is
untouched at `{B1.2, B1.3, B1.4}`. `tools/test_run87_comparison_only.py` **ALL PASS**, including
its section 4, which neutralises the fix and asserts the project status flips — that section
still goes red on demand and is asserted, so the test cannot pass vacuously.

**GOAL ONE: REACHED.**

### Goal two — Data Integrity is an eligibility gate. **REACHED, one iteration.**

**Iteration 1 — measured, before changing anything.**

```
>>> {v['category_name'] for k,v in service_index().items() if v['category']=='C1'}
{'Data Integrity'}
>>> sorted(k for k,v in service_index().items() if v['category']=='C1')
['C1.1','C1.2','C1.3','C1.4','C1.5','C1.6','C1.7']
>>> contributes_to_project_status('C')
False
>>> worst_band([]) , worst_band([None])
(None, None)
```

**§3.1 was ALREADY TRUE and needed no code change: the category already renders as Data
Integrity, from the registry.** What was missing was the *stated role*, which the specification
now carries.

**Hypothesised.** Nothing in the code needed to move; what needed to exist was proof that C1.5
cannot reach the project status by any path, and a written statement of the role. **Three
independent barriers** were found and all three measured: the group predicate (group C returns
False), `models_cat89._route` setting `status_color=None`, `band_asserted=False`,
`category_9_metadata_only=True`, `voting_eligible=False` for every `C1.` id, and `worst_band`
returning `None` over nothing.

**Changed.** The C1 specification's role statement, and `tools/test_run89_data_integrity_gate.py`.
No production code.

**Measured after.** `test_run89_data_integrity_gate.py` **ALL PASS**, 24 checks. Its section 3 is
the neutralise-and-go-red proof: with the group predicate neutralised, the injected adverse C1.5
flips the fused band to `Red`, and section 4 measures the restore. **The check can fail.**

**§3.2 answered:** Information Completeness Ratio cannot reach the project status. Proved by
injection with a proof it can fail.

**§3.3 answered by measurement, and the answer is neither of the two the question offered.**
`assets/js/detail.js:2850-2871` and `:2962` carry six labels: server states
`computed | abstained | out_of_order | failed`, plus client-derived `not_run` ("Not called yet")
and `unspecified` ("No specification"). So:

* **"never called" IS a state** — `not_run`, the client's derivation when no reading is stored.
* **"not assessed" is NOT a state.** It is the **absence of a band on a reading that exists**, and
  it occurs *across* `computed`, `abstained`, `out_of_order` and `failed` alike, rendering as
  "No band" through `SPEC_NO_STATUS_WORDS`.

They are two different facts about an absence, but only one of them is a state. **No new state
was invented.** Measured: a called category whose modules assert no band carries `status: None`,
and `status == "Green"` is `False`.

**§3.3's third clause, and the note about per-category percentages.** C1.5 computes a
**package-level** ratio over the components of a governed information package
(`|present_usable| / |applicable|`). **It does not compute per-category completeness
percentages, and none were built.** What would be required: a governed structure that declares,
per performance category, which package components its methods need. No such structure exists in
the tree, and none was invented.

**COMPARISON_ONLY_MODULES was NOT extended.** C1.5 does not need to be in it — the whole of group
C is already excluded one level up — and the test asserts the set is still exactly Run 87's.
Reporting this as §7.5 requires.

**GOAL TWO: REACHED**, with one premise of the order found false (see section 6).

### Goal three — the required core, and Indeterminate. **REACHED, one iteration.**

**The mandatory pre-change measurement, first, as ordered.** Richest stored row measured by
`length(module_results)+length(category_statuses)+length(signal_inputs)`:

```
01M11XFQ9BZAYSTX8JBB98ADTT  a81ca9d2...  period 8   83109 bytes
01M11XEYX5V5S6CQSCSJBHBV6T  507be211...  period 8   83108 bytes   <- Run 88's row
```

Both give the same answer. On `01M11XEYX5V5S6CQSCSJBHBV6T`:

```
project_status Red
  A1 status= Red   modules= 6  setby= ['A1.7','A1.8']
  A2 status= None  modules= 2  setby= []
  A3 status= None  modules= 3  setby= []
  A4 status= Red   modules= 3  setby= ['A4.2']
  A6 status= None  modules= 3  setby= []
  B1 status= Red   modules= 2  setby= ['B1.1']
  B3 status= None  modules= 2  setby= []
```

**ONE of the four required categories carries a posture today: A1 (Red). A2, A3 and A6 carry
none.** Note which meaning was measured, as the order asks: **"carries a posture" was taken to
mean a non-null category status**, not "has modules". A2 has two modules and A3 has three, and
both carry no posture, because those modules computed without asserting a band. **The owner's
suspicion is confirmed: Indeterminate is the common case, not the rare one.**

**Hypothesised.** The gate must not be inside `worst_band`, because "Indeterminate" is not a
severity and cannot be ranked against one. It must be a condition layered on top, so that the
identity §4.2 demands is true by construction rather than by care.

**Changed.**
1. `spec_projection.py`: `REQUIRED_CATEGORIES = ("A1","A2","A3","A6")`,
   `SUPPORTING_CATEGORIES = ("A4","A5")`, `INDETERMINATE`, `required_core_missing()`,
   `project_status_basis()`, and `project_status()` returning the basis's `status`. The required
   and supporting sets are **defined once**, in `simulation/compute.py`, and imported here, so the
   two status paths cannot drift.
2. `simulation/compute.py`: the same gate on the Python rollup, publishing
   `project_status_basis` and keeping the band worst-wins produced under `fused_band`.
3. `documents._result_view`: carries `project_status_basis` to the client, **derived** on a
   Python-layer row by the same pure function rather than read from an invented stored field.
4. `assets/js/detail.js`: the Indeterminate brief in `scriptedBrief`, plus `statusBasis` on the
   evidence record and a `__briefForTest` export following the existing `__resetMapForTest`
   convention.

**Measured after — §4.2, worst-wins unchanged.** Not argued; measured. Over **all 256
combinations** of the four severity bands across the four required categories, the published
status equals `fusion.worst_band` computed independently over the same contributing categories:

```
1. WORST-WINS IS UNCHANGED WHEN ALL FOUR REQUIRED CATEGORIES ARE ASSESSED
  [PASS] all 256 four-band combinations publish exactly worst_band, unchanged
```

**§4.1 — Indeterminate on a real stored row.** `compute_project` on the stored signal inputs of
`01M11XEYX5V5S6CQSCSJBHBV6T`:

```
project_status Indeterminate
fused_band     Red
required_assessed ['A1']        required_missing ['A2','A3','A6']
supporting_assessed ['A4']      supporting_not_assessed ['A5']
official False
```

**§4.4 — Indeterminate is not a band.** `"Indeterminate" in BAND_SEVERITY` is `False`;
`worst_band(["Indeterminate"])` is `None`; `worst_band(["Indeterminate","Green"])` is `"Green"`.

**§4.3 — the three recommendation checks, NOT weakened.** They were not edited. The brief was
measured by loading `assets/js/detail.js` **whole** into a VM context and calling its own
`briefGate` through `LinDetail.__briefForTest` — the production gate on the production text.
`node server/tools/test_run89_indeterminate_brief.js` → **ALL PASS**, including the proof the
harness can fail: the same gate on a brief asserting "the evidence suggests meaningful risk" with
no figure is **rejected by check 1**.

The brief as it renders on that row:

```
### Recommendation
INDETERMINATE - there is insufficient evidence for an official project posture this period, so none is issued.
Schedule Performance (A2) could not be assessed: the category was called and no module in it asserted a band.
Cost Risk (A3) could not be assessed: the category was called and no module in it asserted a band.
Delivery Quality Performance (A6) could not be assessed: the category was called and no module in it asserted a band.
Escalate now, without waiting for an official posture: A1 Cost and EVM Performance reads Red, set by A1.7 reading TCPI 1.34; A1.8 reading VAC -412000.
Escalate now, without waiting for an official posture: A4 Document-Derived Condition Signals reads Red, set by A4.2 reading document risk 0.66.
Worst-wins over the categories that did report would have produced Red; that band is recorded and is not issued as the official status, because the required categories are not all assessed.
### Signal Pattern
* A1 Cost and EVM Performance: Red.
* A4 Document-Derived Condition Signals: Red.
o A2 Schedule Performance: not assessed.
o A3 Cost Risk: not assessed.
o A6 Delivery Quality Performance: not assessed.
o A5 System Dynamics and Complexity: never called this period.
### Key Drivers
- A1 Cost and EVM Performance (required): Red
- A2 Schedule Performance (required): not assessed.
- A3 Cost Risk (required): not assessed.
- A6 Delivery Quality Performance (required): not assessed.
- A4 Document-Derived Condition Signals (supporting): Red
- A5 System Dynamics and Complexity (supporting): not assessed. A supporting category that was not assessed never produces a Green.
### Required Actions
- Acquire the evidence Schedule Performance (A2) needs, and re-run the period once it is on file
- Acquire the evidence Cost Risk (A3) needs, and re-run the period once it is on file
- Acquire the evidence Delivery Quality Performance (A6) needs, and re-run the period once it is on file
- Verify the figures already on file for the categories that did report, so the partial picture is at least trustworthy
- Escalate A1, A4 to the controls lead now rather than waiting for an official posture
- Record how you treated this recommendation on the decision card - accept, accept with conditions, modify, reject, defer, request evidence, escalate or transfer authority - and request evidence is the disposition this status is about
```

All five of the owner's requirements are individually asserted in the test and all five pass.

**§4.5 — where the participant's course renders, and what it says.** It renders in the **Executive
Brief panel's Required Actions**, and the control it names is the **decision card in
`assets/js/decision-ui.js:623`** — *"How did you treat the recommendation?"* — whose vocabulary is
`research_decision.DISPOSITIONS`:
`accept, accept_with_conditions, modify, reject, defer, request_evidence, escalate,
transfer_authority`. **`decision-ui.js` is sequence-bearing and was NOT touched.**

**An honest correction inside this goal.** My first draft of that line read *"Accept, reject or
modify this course using the controls below"*. I then measured
`assets/js/recommendation_options.js:149` and found the courses-of-action surface returns
`available: false` on **every current row**, because the module that scores the courses (B4.7) is
non-voting. So the sentence was asserting a control that does not exist there. It was rewritten to
name the decision card and its real vocabulary, and the test asserts the exact string.

**GOAL THREE: REACHED.**

### Goal four — drop the three structure-defined modules. **REACHED, one iteration.**

**Iteration 1 — measured.** All three verified against the registry CSV before touching anything:

```
43:A5.1,DSM Rework Propagation,5.1,A,...,A5,System Dynamics & Complexity,absorbs former 3.2 ... (alias)
47:A5.5,Rework Feedback Loop,5.5,A,...,A5,System Dynamics & Complexity,
87:B4.4,What-If Scenario Matrix,10.4,B,...,B4,Decision Optimization,
```

**Run 43's mechanism, found and reused exactly.** `registry.RETIRED_NOTE_PREFIX = "RETIRED "`,
`_retired_reason()` reading the CSV `notes` column, `retired_modules()`, `modules_in_service()`.
Run 43D's ruling is in the file: *"RETIREMENT IS REMOVAL FROM SERVICE, NOT REMOVAL FROM
EXISTENCE"*. The `new_id` is kept so every reference still resolves.

**Changed.** The `notes` column on exactly three CSV rows. **No tombstone, no refusal, no new
error class.** A5.1's pre-existing alias note was preserved by appending, not overwritten.

**Measured after:**

```
service 60  available 59  registered 101  retired 41
A5.1 in service: False | available: False | resolves in registry: True
A5.5 in service: False | available: False | resolves in registry: True
B4.4 in service: False | available: False | resolves in registry: True
dispatched ids containing the three: []   total dispatched: 59
```

Retirement is expressed by roster membership and nothing raises.

**GOAL FOUR: REACHED.**

---

## 4. How many of the four required categories carry a posture on the richest stored row

| | A1 | A2 | A3 | A6 | count |
|---|---|---|---|---|---|
| **Today (before this run)** | Red | none | none | none | **1 of 4** |
| **After this run** | Red | none | none | none | **1 of 4** |

This run did not change which categories carry a posture — nothing in it was supposed to. What
changed is what the platform *says* about that fact: before, the row published **Red** as an
official project status on the strength of one required category out of four. It now publishes
**Indeterminate**, with `fused_band: Red` recorded beside it and every assessed category, both
Reds included, rendered in the brief. **"Carries a posture" was measured as a non-null category
status.**

---

## 5. The resulting counts, and the two categories that lost modules

| | before | after |
|---|---|---|
| registered | 101 | **101** |
| in service | 63 | **60** |
| retired | 38 | **41** |
| the server computes | 62 | **59** |
| supplied but unported | 1 (A4.1) | **1 (A4.1)** |

Per category, **measured on the server and independently in the browser taxonomy, and identical**:

| | A1 | A2 | A3 | A4 | A5 | A6 | B1 | B2 | B3 | B4 | C1 | total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| server `service_index()` | 10 | 6 | 7 | 10 | **5** | 4 | 4 | 1 | 5 | **1** | 7 | **60** |
| client `LIN_CATEGORIES` | 10 | 6 | 7 | 10 | **5** | 4 | 4 | 1 | 5 | **1** | 7 | **60** |

**What happened to the two categories: nothing. Neither emptied, so Run 51 does not trigger.**
This was measured, not decided:

* **A5 System Dynamics & Complexity keeps FIVE modules in service** — A5.2, A5.4, A5.6, A5.7,
  A5.8. It held seven before, not two.
* **B4 Decision Optimization keeps B4.3** Constraint Satisfaction Analysis. It held two before,
  not one.

Both stay in service, in the ledger, and on the participant surfaces.

**Where the counts render, and each one checked:** `assets/js/taxonomy.js:49` and
`assets/js/categories.js:53` (`LIN_TAXONOMY_COUNTS`, both updated to
`{registered:101, inService:60, retired:41, serverComputes:59, supplied:1}`), the
`LIN_CATEGORIES` module arrays in both files (the three entries removed, matching how Run 43
removed its 38 — A2.4 is likewise absent), `tools/test_map_and_module_count.py` (75/75),
`tools/test_run47_evm_consistency.py` and `tools/test_run48_current_period.py`.

**Where they deliberately do NOT change:** `assets/js/workspace.js`, `assets/js/decision-ui.js`,
`assets/js/knowledge.js` and `assets/js/ds_defensibility_evidence.js` keep their entries for all
three, exactly as they keep A2.4's — those are **label and evidence tables, not populations**, and
Run 43D's ruling requires a retired module to stay readable. Verified: A2.4 is present in all
four. The `build_run*`, `participant_packages.py` and `production_tree.py` occurrences of "63" are
**sealed historical release prose** describing what was true at those runs and were not edited.

---

## 6. Every premise in this order that proved false against the tree

**Three.**

**6.1 — §5's closing premise is false. Neither category empties.** §5 states *"Systems and
Dynamics loses both its modules and Decision Optimisation loses its only one."* Measured:

```
A5 ids in service (before): ['A5.1','A5.2','A5.4','A5.5','A5.6','A5.7','A5.8']   SEVEN
B4 ids in service (before): ['B4.3','B4.4']                                       TWO
```

The order is counting the **retained roster** (2 in A5, 1 in B4), not what is in service.
Dropping A5.1 and A5.5 leaves A5 with **five**; dropping B4.4 leaves B4 with **B4.3**. **Run 51's
empty-category removal does not trigger, and §5's "report what happens to those two categories;
do not decide it" is answerable by measurement: nothing happens to them.**

**6.2 — §3's "holds exactly this one module" is false.** The order says Data Integrity *"holds
exactly this one module"*. **C1 holds seven in service: C1.1 through C1.7.** Only C1.5 is on the
retained roster. §6.7 puts "the remaining 30 modules outside the retained roster" out of scope, so
**C1.1–C1.4, C1.6 and C1.7 were NOT dropped.** The conflict is reported and the run worked from
what is there: the category's **role** is now stated as eligibility, which is true of all seven —
the specification's own opening already called them "evidence qualification measures ... not how
the project is performing" — while C1.5 is named as the eligibility gate the owner identified. The
test prints the seven ids as a measurement rather than asserting the count.

**6.3 — §3.1's rename was already done.** The order asks that "the category renders as Data
Integrity". It already does, from the registry itself:
`{v['category_name'] for v in service_index().values() if v['category']=='C1'} == {'Data
Integrity'}`. No rename was needed and none was made. What was genuinely absent — the stated
*role* — is what the specification edit supplies.

**One premise checked and found TRUE**, since the order asked me not to act on any without
checking: §2's claim that B1.2 read four arms of which `mc` and `doc` trace to dropped modules is
correct — the prior body is quoted verbatim in section 3 above, and `canonical_v5.weighted_voting`
weighed whatever `governed_signals_from_project` returned.

---

## 7. Real versus harness measurements

**Real (executed against production code and, where stated, real stored rows):**

* Every registry, population and count figure — `service_index()`, `registry_index()`,
  `available_modules()`, `retired_modules()`, `run_all()`.
* The pre-change and post-change category statuses and project status on the **real stored rows**
  `01M11XEYX5V5S6CQSCSJBHBV6T` and `01M11XFQ9BZAYSTX8JBB98ADTT`, read from a **scratchpad copy of
  `server/dev.db`**. Production Postgres was never contacted; `DATABASE_URL` pointed only at
  throwaway SQLite files under the scratchpad and `/tmp/sw/`.
* `compute_project` run end to end on those rows' own stored `signal_inputs` and `period_cutoff`.
* All six suites: `test_run89_required_core.py` (ALL PASS),
  `test_run89_data_integrity_gate.py` (ALL PASS), `test_run87_comparison_only.py` (ALL PASS),
  `test_run6_known_answer.py` (488/489, **baseline restored**),
  `test_run17_scientific_methods.py` (287/287, up from 284),
  `test_run30_non_vacuity.py` (120/120, **baseline restored**),
  `test_map_and_module_count.py` (75/75), `test_group_assignment.py` (16/16),
  `test_run24_empty_project_diagram.py` (53/53),
  `test_run36_instrument_qualification.py` (76/76).
* The freeze gate, run through `build_run37_acceptance.py` to completion.
* The client brief: `assets/js/config.js`, `taxonomy.js` and `detail.js` loaded **whole** into a
  Node VM context, and `detail.js`'s **own** `briefGate`, `scriptedBrief`, `briefEvidence` and
  `parseBrief` called through it. The three Run 70 checks measured are the production ones.

**Harness (and labelled as such):**

* The stored row used by `test_run89_indeterminate_brief.js` is a **fixture built to the shape of**
  the richest stored row, not the row itself — the row's own bytes were measured separately and are
  quoted in section 4. The DOM in that harness is a stub; every function measured through it is
  pure over its arguments.
* `test_run89_required_core.py` and `test_run89_data_integrity_gate.py` construct
  `SpecificationReading` objects in memory rather than reading a stored row, because
  `specification_readings` holds **no row for either richest project** (measured: 41 rows across
  ten other projects). The functions under test are the production ones.

**Not measured at all, and not reported as anything:** any model behaviour. There is no
`ANTHROPIC_API_KEY`. No extractor was run. Nothing below or above reports a StubExtractor or
recorded-applier result as the model's behaviour.

**Not run:** the browser drivers. The Indeterminate brief was measured through detail.js's real
functions in Node, not in a rendered Chromium page. **I did not verify it in a browser**, and say
so plainly rather than arguing it.

---

## 8. Anything found and not fixed

1. **A real field collision, FOUND AND FIXED, reported because it was a genuine defect.** B1.2's
   class-weight distribution was landing on the module-row key `votes`, which
   `registry.run_all:710` already uses for the **boolean** `new_id in CORE_VOTING_MODULES`. A
   truthy dict made B1.2 read as a voter on the stored row, which
   `test_run6_known_answer.py` caught. It is now `class_votes`. **The collision was latent before
   this run only because B1.2 never computed** — the same key was on the old return shape.
2. **The A5 and B4 specifications still describe A5.1, A5.5 and B4.4 as live modules.** §0.1 is
   binding — a specification this order does not name is not touched — and the order names only
   B1 and C1. So `specifications/A5_system_dynamics.md` and
   `specifications/B4_decision_optimisation.md` now disagree with the registry about three
   modules. **Not fixed, deliberately. It needs an order naming them.**
3. **`assets/js/categories.js:14`** still carries a comment referencing "(A4.1 and A5.1)" as
   aliases. Historical and true of the alias rows; left.
4. **Per-category completeness percentages do not exist** and were not built (§3's instruction).
   What would be required is stated in section 3 above.
5. **`test_documents_b7b` 76/77, `test_run3_adapter`, `test_run10_state_protection`,
   `test_workspace_t3t5`, `test_run48_current_period`** remain pre-existing failures; not chased,
   as instructed.
6. **The freeze gate is BLOCKED and v43 is not merged.** See section 9.
7. **A whole-suite sweep was not completed.** Roughly forty DB-shaped suites need a migrated
   database each and the sweep timed out. I ran the suites that touch the registry, the rollup,
   the status, the counts and the brief, and diffed three of them against the starting commit in a
   git worktree to prove I had not moved a baseline. **The remaining suites were not run**, and I
   do not claim they pass.

---

## 9. Every guarantee, marked

| # | Guarantee | Verdict |
|---|---|---|
| 2.1 | B1.2 computes from the six category postures on a real stored row | **VERIFIED** — Red from A1+A4 on `01M11XEYX5V5S6CQSCSJBHBV6T` |
| 2.2 | The four-arm dependency is gone from its specification and its input path; arm readers established and reported | **VERIFIED** — six readers listed; `models_evc.py` serves B2.2–B2.9 |
| 2.3 | A category not assessed is not a zero, a Green or a dropped term; the rule is stated and proved | **VERIFIED** — renormalisation, derived from B1 shared rule 3, measured |
| 2.4 | It stays comparison-only; the Run 87 injection still passes and can still fail | **VERIFIED** — ALL PASS incl. its neutralise-and-go-red section |
| 3.1 | The category renders as Data Integrity, with an eligibility role | **VERIFIED** — already true from the registry; role now stated |
| 3.1 | "one module" | **NOT MET, AND CANNOT BE** — C1 holds seven in service; the other six are out of scope (§6.7). Reported, not acted on. |
| 3.2 | C1.5 cannot reach the project status; proved by injection; the check can fail | **VERIFIED** |
| 3.3 | Insufficient eligible evidence returns not assessed, never a band | **VERIFIED** — `worst_band` over nothing is `None` |
| 3.3 | Whether "not assessed" and "never called" are one state or two | **VERIFIED AND ANSWERED** — "never called" is a state (`not_run`); "not assessed" is the absence of a band, not a state. No state invented. |
| 3 (note) | Per-category completeness percentages not built unless already computed | **VERIFIED** — not computed, not built, requirement stated |
| 4.1 | Indeterminate is a real status, provable on a stored row | **VERIFIED** |
| 4.2 | Worst-wins unchanged when all four required categories are assessed | **VERIFIED** — identical across all 256 combinations |
| 4.3 | The brief passes the three checks, which are not weakened | **VERIFIED** — production `briefGate` on production text; checks unedited |
| 4.4 | A participant has a concrete recommendation to accept, reject or modify; where and what | **VERIFIED** — Executive Brief Required Actions → decision card, `research_decision.DISPOSITIONS` |
| 4 (pre) | Measure and report how many required categories carry a posture today | **VERIFIED** — **1 of 4** |
| 5 | The three no longer appear in service | **VERIFIED** |
| 5 | Counts consistent everywhere they render | **VERIFIED** on the server, both client taxonomy files, and the suites; sealed historical prose deliberately unchanged |
| 5 | Every check keyed to them updated to assert the new state | **VERIFIED** for the suites I ran; **NOT VERIFIED** for the ~40 DB-shaped suites the sweep did not reach |
| 5 | No tombstone, refusal or new error class | **VERIFIED** — Run 43's CSV `notes` mechanism reused; all three still resolve |
| 5 | What happens to A5 and B4 — report, do not decide | **VERIFIED** — nothing happens; measured, not ruled |
| 0.2 | Every specification edit quoted before and after | **VERIFIED** — section 2 |
| 0.3 | Nothing invented | **VERIFIED** — the weight profile is the owner's; the unassessed rule is derived from B1's own shared rule 3; `class_votes` is a rename to avoid a measured collision, stated in the specification; `project_status_basis` is derived, never stored |
| 0.4 | SIMULATION_VERSION moves once, at the end; requalify; report the gate | **VERIFIED, GATE BLOCKED** — see below |
| 7.5 | Run 87's admission seam untouched except to add to COMPARISON_ONLY_MODULES | **VERIFIED** — not extended; C1.5 not added; reported as required |
| 8.3 | Never point DATABASE_URL at production | **VERIFIED** — scratchpad copy of `dev.db` and throwaway SQLite only |
| 8.4 | Never `git add -A` or `git add .` | **VERIFIED** — every add explicit |
| 8.5 | `git status --porcelain` before every commit | **VERIFIED** |
| — | The Indeterminate brief in a rendered browser | **COULD NOT VERIFY** — measured in Node against detail.js's real functions, not in Chromium |

### The mint

`SIMULATION_VERSION` = **`sim-2026.08-v43`** (`server/app/simulation/models.py`), superseding
`sim-2026.08-v42`, appended to `SIMULATION_VERSION_HISTORY`, with the reason recorded in the file.

`build_run37_acceptance.py` first **refused with exit 3** on the candidate fixed point and named
the value. With it reconciled, **the gate RAN**:

```
FREEZE GATE: 15 blockers evaluated, 4 BLOCKED -> FINAL_FREEZE_BLOCKED
  BLOCKED B01 dirty candidate identity: 11 digests recomputed; diverging: 7
  BLOCKED B04 participant-sequence drift: moved: ['assets/js/decision.js', 'assets/js/workspace.js']
  BLOCKED B11 package or predecessor mutation: og-participant-2026.08-v26 files not matching record
  BLOCKED B15 candidate behaviour changed during the run: behaviour digest moved:
             8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1
          -> 3839c63df2a02099e2d536defb4b89e07d55d1eeb5ac6fee31704f2307...
```

**B15 is expected and §0.4 authorises it** — this run deliberately changed what several modules
compute. **B01, B04 and B11 are the standing blockers** that have held v27 for many runs, on a
ruling about `decision.js` being sequence-bearing that the owner has not given.
**`V26_TO_V27_SEQUENCE_EXCEPTION` was NOT composed** — that justification is the owner's to write,
not mine, and I stopped there.

**Per §0.4's own escape clause: the work is committed to the branch, it is NOT merged, and I am
saying so.** The sealed v42 record `research/freeze/run67_successor_freeze_gate.csv` was rewritten
by the generator and **restored with `git checkout --`; it is not committed.** The ten
`code_audit/*.csv` and `server/tools/run17/coverage.csv` artefacts the suites rewrote were
likewise restored and not committed.

### Where budget ran out

Nowhere that mattered. All four goals were reached, each in **one iteration** — no goal needed a
second hypothesis, and there is no failed iteration to hide, because there was none; the two
course corrections that did occur (the `votes` collision, and the accept/reject/modify sentence
naming a control that does not exist) are both reported in full above, in sections 8.1 and 3
respectively. The one thing I did not finish is the **whole-suite sweep** (item 8.7), and the one
thing I did not do at all is **verify the brief in a rendered browser**.

**Sequence-bearing files this run moved: the empty tuple `()`.** `decision.js`, `decision-ui.js`,
`workspace.js`, `intake.json` and `debrief.json` were not touched. B04 reports `decision.js` and
`workspace.js` as moved against the **v26 record**, which is the standing pre-existing drift, not
this run's doing.

---

## Commits

```
4c35bef Run 89: T6_HANDOFF section
fca31fe Run 89: reconcile the acceptance generator's CANDIDATE constant
6ccb650 Run 89: SIMULATION_VERSION moves to sim-2026.08-v43
d870247 Run 89: the checks keyed to B1.2's old arm path assert the new state
b88cf61 Run 89 goal four: A5.1, A5.5 and B4.4 dropped from service
113bcba Run 89 goal three: the required core, and Indeterminate
8cd6c23 Run 89 goal two: Data Integrity is an eligibility gate, not a posture
dfaa89f Run 89 goal one: Weighted Voting reads the six category postures, not the four arms
```
