# Run 141 — why A3 produced no module reading for PRJ-002 period 2

**Diagnostic. Read-only. Nothing was changed.** No fix was applied, no test repaired, nothing
committed but this report. `SIMULATION_VERSION` untouched at `sim-2026.09-v70`.

---

## The answer, plainly

**Reading A is closed. The Groq 403 did not stop A3's modules running.** The specification layer
and the module dispatch are on two disjoint routes that cannot raise into one another, and a
failed specification reading steps aside for the Python modules rather than overwriting them.
That is proved from the code below.

**But the cause of A3's emptiness is not established, and I will not name the most plausible
candidate as a finding.** What I can state, with evidence, is that **the card's sentence does not
mean what the order assumes it means**, and that this collapses the distinction the whole
question rests on:

> The sentence *"no module in this category was run for this period"* is emitted at
> `simulation/compute.py:107` by a test of **key presence**, not of module state:
> `if key not in cats`. A category all of whose modules **ran and abstained** produces no key,
> because `category_statuses` is built only from computed modules (`compute.py:432-440`).

**So "was not run" and "all four ran and abstained" print the identical sentence.** The order's
observation 3 — that the wording is different from abstaining on missing input — rests on a
distinction the code does not make at this seam. **This is the single most consequential finding
of the run**, because it means the observation is equally consistent with two very different
worlds, and only a query against the deployment separates them.

**What would settle it:** query A below. If it returns four A3 rows in the abstained bucket, the
modules ran and declined their evidence, and the cause is upstream in extraction. If it returns
nothing at all, they genuinely never executed and that is a different and more serious finding.

---

## 1. Did A3's modules run?

**Not answerable from this container, and I want that stated rather than worked around.**
`DATABASE_URL` is unset. There is an untracked `server/dev.db`, which I opened read-only before
assuming anything: 89 projects, 131 computed results, **every one at `sim-2026.08-v42` or older,
dated 2026-08-29, and containing no PRJ-002 at all.** It predates v70 entirely and cannot hold
this observation. Nothing in this report is drawn from it.

What the code does establish is which outcome produces which surface:

| outcome | where the row lands | what the card shows |
|---|---|---|
| never dispatched | impossible for A3 by construction — `run_all` iterates `available_modules()` and all four are in service | — |
| dispatched and raised | `registry.py:813` `guarded` converts it to an abstention carrying `module_failed` | as abstained |
| **dispatched and abstained** | `run["abstained"]`; **no** `by_category` key; **no** `category_statuses` entry | **zero A3 rows, and the "was not run" sentence** |
| dispatched, computed, band withheld | routed to `run["computed"]`, so A3 **does** get a key | the *other* sentence: "the category was called and no module in it asserted a band" |

**The observed wording is consistent with all four modules abstaining or failing, and
inconsistent with any of them computing.** Two milder failure modes are therefore ruled out by
the wording alone: A3.2 with contingency present but percent complete absent, and A3.6 with a
valid model but no budget at completion, both land in `computed` and would have produced the
other sentence.

### A second finding: the merge can hide rows that did run

`spec_projection.py:701-722` carries the Python module and abstention rows over **only for
categories in `filled`**, and a category enters `filled` only if it has an entry in
`category_statuses` — which, as above, a fully-abstaining category never gets.

**So A3's four modules can have run, abstained, been recorded on the stored row, and still reach
the card as nothing at all** — no row, no reason, no trace. Reproduced by executing
`merge_python_row` directly with an A3 row present: the A3 entries were dropped while A1, A2, A4
and A6 survived. That is a projection defect, not a dispatch one, and **it is what made A3's
emptiness unreadable rather than what caused it.** Stated as a recommendation at the foot of this
report, not applied.

---

## 2. What the signal inputs hold, against what each module needs

The left half is unreachable here; query C below is the route. The requirement half, read from
each module's own code:

**A3.2 Contingency Burn Rate** (`models_ext.py:783`). Hard: `originalContingency`,
`remainingContingency` — either absent gives `ABSTAIN_MISSING_INPUT`; the remaining amount must
lie within the original, else the structure is refused. **Soft: `actualPctComplete`** — absent,
the module still computes and returns a row with no colour. Note `check_inputs` is an
`is not None` test, so a JSON null counts as absent but a zero does not.

**A3.3 Labor Productivity** (`models_ext.py:925`). Requires the whole `productionOutputRecord`
structure. Six hard fields: output unit, quantity source, earned output, planned output, actual
labour hours, planned labour hours, with sign and positivity constraints. Any one missing gives
`ABSTAIN_STRUCTURE_ABSENT`. **There is no partial reading — it bands or it abstains.**

**A3.5 Overhead Absorption** (`models_ext.py:1136`). Requires `overheadAllocationBase`. Six hard
fields: allocation base, driver source, planned and actual overhead, planned and actual driver,
plus a derived guard that the planned rate is positive.

**A3.6 Cost Risk P80** (`models_ext.py:1253`). Requires `costRiskModel`: cost components summing
above zero, model version and estimate source, a risk-event list with valid probabilities and
distributions, and a dependence policy whenever there is more than one event. **`bac` is read
separately and is not required to produce a reading** — absent, it returns a computed row with
figures and no colour.

**Consequence worth stating:** "04 Cost Report and 08 Resource Report were uploaded" is not
evidence that any of these fields was extracted. The modules read extraction output, not document
presence. For A3 to be absent from `category_statuses`, **all four** must have failed their
inputs.

---

## 3. Spec-layer failure against module dispatch — Reading A is closed

Four pieces of evidence, each verified by me directly against the tree.

**They are disjoint routes.** Module dispatch runs `documents.py:4008` → `compute_project` →
`registry.run_all` → `run_module`, storing to `computed_results`. The specification reading runs
an entirely separate route through `spec_readings.apply_and_store` → `spec_apply.apply_category`,
storing to `specification_readings`. **I grepped `documents.py` for every specification-layer
symbol and it returns zero.** The compute route contains no reference to the specification layer
at all.

**The exception is caught twice and fails only its own row.** `spec_apply.py:448-457` catches the
application error and then bare `Exception`, with the stated reason that a category failure must
not stop the others. `apply_category` never raises. A 403 becomes a stored failed row for that
one category, carrying the provider's text — which is exactly the string on A3's row.
Symmetrically, `registry.py:811-825` wraps every module call and converts a raising module into
an abstention, so one module cannot stop its siblings either.

**A failed specification reading is not a reading.** `spec_projection.py:619` defines a reading as
computed or abstained only. A failed row therefore lands in the unanswered set and is **open to
the Python fallback**; `spec_projection.py:696-698` keeps its unanswered entry rather than
overwriting. **It steps aside. It does not merge an empty list over the Python rows.** That is
the opposite of what Reading A requires, and it is how A1, A2, A4 and A6 obtained postures while
their specification rows failed on the same 403.

**Nothing about A3 differs structurally.** All four of its modules are flat-input first-pass
modules, all admitted to the category rollup, all in the same dispatch pass as the other
categories'. A3's only distinguishing property is arithmetic: **it is the smallest required
category at four modules, and its inputs are the narrowest**, so it is the one most easily
emptied.

### An inconsistency in the observation that must be resolved first

If A3 has a **live** failed specification reading for period 2, then A3 **is** a key in the merged
mapping, and the card should have printed *"the category was called and no module in it asserted
a band"*. It printed the other sentence, which requires A3 to be absent from the merged mapping
entirely. **Both observations cannot be true of the same period.** Query B decides it.

One thing not to over-read: the other five categories showing "Failed" with no error line is not
evidence they carry no reason. `detail.js:3644` renders the reason inside a hidden div, so an
unexpanded row shows nothing regardless of what it holds.

---

## 4. What changed between v66 and v70 — the hypothesis is closed but for one thread

Window taken from the commit that moved the stamp off v66 to HEAD.

**Every alias and emission removed in the window, with the module each fed:**

| removed | run | fed |
|---|---|---|
| the pay application's `ac` emission | 132 | **A1**, the EVM family |
| `inspections_passed` from the first-pass numerator | 135 H5 | **A6.4** |
| `commitments_met` | 135 H5 | **A6.4** |
| `commitments` from `commitments_due` | 136 F8 | **A6.4** |
| `packages` from `packages_due` | 137 | **A6.4** |
| two orphan band sets | 136 F7 | no A3 module |

**Not one is an A3 input**, and no A3 module reads actual cost or the cost index — I verified that
by grep over the module file myself. **The alias hypothesis the order singled out is closed.**

**I verified the two decisive negatives directly:** `simulation/canonical_v3.py`, which holds
every requirement listed in section 2, has **zero diff** across the window; and
`simulation/compute.py`, which holds dispatch, the category mapping and the wording branch, has
**zero diff**. A3's requirements and the dispatch logic are byte-identical between the two
periods. A3's only change in the window is how two already-computed numbers are printed.

### The one surviving thread, sharpened

Run 135 M4 added an `ORDER BY` to the query behind `_period_documents` and a business-key sort in
Python, **changing the order of the document list**. That list is walked by
`_run69_structures`, which builds A3.3's production record and A3.5's overhead base with
`out.setdefault(...)` — **first writer wins**.

**So if period 2 contains two documents of the same type, Run 135 changed which one supplies
A3's structures.** That normally changes which figures land, not whether the structure exists —
but if the now-first document yields an incomplete record, the structure is never set at all and
the module abstains structure-absent, which is exactly the observed shape.

**This is unproven and I am not offering it as the cause.** It requires period 2 to hold at least
two documents of a type feeding A3. The test is precise: check whether the 17 documents include
more than one cost report or more than one resource report, then compare which document supplied
each structure in period 1 against period 2.

I also checked whether Run 135's archive filter could have dropped a document: **it cannot have
been the change**, because that filter at `documents.py:504` predates the window, added at Run 71.

---

## 5. The missing risk register — confirmed, and it explains only part

**Confirmed by execution, and the order's reading is right.** A category posture needs only one
banded module: executed, a lone Red A3.2 with the other three silent gives A3 a **Red** posture
carrying its own "this posture rests on one reading" sentence. Three banded modules with A3.6
absent give **Red** on a stated three-module average. `category_posture.py:29-31` states that a
category where no module banded carries no posture, and an abstaining module contributes nothing
rather than a zero.

**An abstaining A3.6 cannot prevent the other three being dispatched.** They are four independent
iterations of the same loop, each individually guarded. There is no ordering and no shared state.

**But the missing register does not explain the observation.** A3.6 alone abstaining would leave
A3.2, A3.3 and A3.5 to band, and A3 would carry a posture. For A3 to be absent entirely, **all
four** must have failed their inputs. So the register explains A3.6 and nothing else.

---

## 6. The 403, separately

**Established.** The error string's shape matches the platform's own formatter exactly, so what
arrived was a genuine HTTP 403 whose body was `error code: 1010` — not a Groq application error,
not a timeout, not a parse failure; those are three different branches. The spec role resolves to
Groq with that model identifier and uses the Groq key; the mitigation role added at Run 140
resolves to Anthropic with a different key and host and is not implicated. I confirmed both
resolutions by executing the resolver.

The transport is Python's standard library over a plain request. The only headers set are the
content type and the authorization bearer. **No user agent is set**, so the library supplies its
own, and the TLS handshake is the stdlib default.

**Inference, labelled as such.** Cloudflare's 1010 is a client-fingerprint rejection — the edge
refused the TLS and header signature as a disallowed automated client. The platform's request is
the archetype of what such a rule matches. It is not a rate limit and not an authentication
failure, **so rotating the key would not fix it.**

**One anomaly on the record rather than smoothed over.** The applier issues one request per
category, and all seven failed, which is consistent with a fingerprint ban since that is a
property of the client rather than of any one request. **But why only A3's row printed a reason
is not established** — the hidden-div rendering above is the likely explanation and is not proof.

**What would fix it, with consequences, not applied.** Setting an explicit browser-shaped user
agent is the smallest change but addresses only the header half of the fingerprint and **may not
be sufficient**, since 1010 is commonly driven by the TLS half. Moving the transport off the
standard library would address both but touches all roles and both providers. **Repointing the
spec role away from Groq needs no code change at all** — it is the second rung of the existing
resolver, one environment variable — and changes which model authors the specification text.

**On recomputation:** any of the three changes what the specification layer returns, so period 2's
specification readings would need re-issuing. **Whether the module results need recomputing
depends entirely on query A.** If A3's modules abstained on absent structures, no provider change
will produce an A3 posture and what needs re-running is the documents' extraction. If they never
ran, re-running the period under a working spec role is the whole fix.

---

## The queries to run on the deployment

Read-only. Postgres. Nothing here writes.

**A — did A3's modules run, and in what state.** This is the one that answers the question.

```sql
SELECT r.period, r.simulation_version,
       jsonb_path_query_array(r.module_results::jsonb,
         '$[*] ? (@.module_id starts with "A3.")')  AS a3_computed,
       jsonb_path_query_array(r.abstained::jsonb,
         '$[*] ? (@.module_id starts with "A3.")')  AS a3_abstained
FROM computed_results r JOIN projects p ON p.id = r.project_id
WHERE p.legacy_id = 'PRJ-002' AND r.superseded_by IS NULL
ORDER BY r.period;
```

Four abstained rows for period 2 means the modules ran and declined; read each reason to see
which input was missing, and the cause is extraction, not the 403. Both arrays empty means they
never executed, which is a different and more serious finding. Anything in the computed array
with a band means A3 did band and the loss is downstream of compute.

**B — the specification readings, which resolves the inconsistency in section 3.**

```sql
SELECT s.category_key, s.state, s.reason, s.provider, s.model_id,
       s.created_at, s.superseded_by
FROM specification_readings s JOIN projects p ON p.id = s.project_id
WHERE p.legacy_id = 'PRJ-002' AND s.period = 2
ORDER BY s.category_key, s.created_at;
```

A live failed A3 row means the card should have printed the other sentence, and the panel and the
brief were rendered from different fetches — itself the next thing to chase. No live A3 row means
the card's wording is correct as composed. All seven failing with the same reason confirms the
403 was provider-wide and category-blind.

**C — what the period actually held for A3, against period 1.**

```sql
SELECT r.period,
       r.signal_inputs::jsonb -> 'originalContingency'    AS orig_contingency,
       r.signal_inputs::jsonb -> 'remainingContingency'   AS rem_contingency,
       r.signal_inputs::jsonb -> 'actualPctComplete'      AS pct_complete,
       r.signal_inputs::jsonb ? 'productionOutputRecord'  AS has_a33_structure,
       r.signal_inputs::jsonb ? 'overheadAllocationBase'  AS has_a35_structure,
       r.signal_inputs::jsonb ? 'costRiskModel'           AS has_a36_structure,
       r.signal_inputs::jsonb -> 'sources'                AS field_sources
FROM computed_results r JOIN projects p ON p.id = r.project_id
WHERE p.legacy_id = 'PRJ-002' AND r.superseded_by IS NULL
ORDER BY r.period;
```

Comparing period 1 against period 2 is the cleanest test of the premise that only the figures
changed. Any structure present in period 1 and absent in period 2 names the document heading that
stopped landing, and `field_sources` names which document supplied each field — which also tests
the document-ordering thread in section 4.

---

## Recommendations, stated and not applied

1. **The projection drops the abstention rows of a category that has no banded module**
   (`spec_projection.py:701-722`). A required category can therefore be empty on the card while
   its modules ran and recorded their reasons. Whether that should change is the owner's call.
   **It did not cause A3's emptiness; it made it unreadable.** Changing it needs no recomputation,
   because it is a projection over stored rows.
2. **The card cannot distinguish "not run" from "all abstained"** (`compute.py:107`). The two
   sentences the branch chooses between are both accurate about the key and misleading about the
   modules. A third wording would need no recomputation either.
3. **The 403 fix is an environment change, not a code change**, if repointing the spec role is
   acceptable. It changes what the specification layer stores and needs those readings re-issued.

## What is unproven

Whether A3's four modules ran; what the stored inputs held; why one category row printed a reason
and five did not; and whether the Run 135 document reorder participates. All four are settled by
the queries above, and none is settled by anything reachable from this container.

**No model call was made or simulated. No key of any kind exists here.**
