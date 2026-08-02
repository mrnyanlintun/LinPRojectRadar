# A failed geocode no longer erases coordinates, and the decision card no longer contradicts itself

**1177 checks across 22 suites, 0 failures. `tests_render.html` 43/43, `tests.html` 51/51.**
Playwright driving the pre-installed Chromium (`/opt/pw-browsers/chromium-1194`), compositing
proven before anything was read from the DOM: `visibilityState` "visible", **62 rAF frames per
second**. There is no `preview_start` in this container. No coordinate data was written, repaired
or backfilled anywhere except a throwaway `dev.db` used as a browser fixture.

---

## What a full D7.2 fix would require, which is the thing you own

The card has four fields and an action-plan table. **Only one of the five could be sourced from
stored data today, and it is not the one that matters most.**

**Measured on a real computed result** (36 modules stored, 10 of them Group B), by taking the
union of every key on every stored module:

```
action-ish keys present anywhere in module_results : recommended_action, expected_regret
                                    both from      : B4.7 Regret_Minimization
                       B4.7 emits   : recommended_action "escalate"
                                      expected_regret {monitor: 11, investigate: 5, escalate: 8}
```

| Card field | Can stored data supply it today? |
|---|---|
| **Recommended action** | **Yes, partially.** B4.7 Regret Minimization emits `recommended_action` from the closed vocabulary {monitor, investigate, escalate}. It is one module's minimax-regret answer, not a project-level recommendation, and it is withheld from a research participant until the preliminary judgment is locked. |
| **Authority** | **No.** No stored module emits an authority, an owner or a role. Nothing in the key union comes close. |
| **Documentation required** | **No.** Same — no stored field names a documentation requirement. |
| **Fairness gate** | **No, and it is still unobtainable.** `fairnessSensitive` is absent from `SIGNAL_INPUT_KEYS` (79 keys) and is not wired by `documents.py`, which D1 used to wire `events`, `spiHistory` and `cpiHistory`. It stayed in D1's "abstaining, because nothing can ever supply them" set. **The gate has never been able to fire and still cannot.** |
| **Action plan table** | **No.** Its content came entirely from `CATEGORY_ACTIONS`, a hand-written table in `decision.js`. |

**So a full fix is not a wiring job. Three of the four fields have no server-side source at all**,
and creating one means deciding what the analytical layer should say about authority and
documentation — which is composing governance wording, not porting a computation. That decision is
yours, and it is why I stopped at removing the contradiction.

**The three routes I can see, stated so you have something to choose between:**

1. **Retire the card's derived fields.** Keep the stored status badge and the evidence; drop
   Authority, Documentation and the fairness gate, which assert things nothing computed. Needs no
   new wording — it is deletion — but it removes a surface the About page currently describes.
2. **Source the action from B4.7 and abstain on the rest.** Honest and small, but it puts one
   module's verdict where a project-level recommendation used to be, and B4.7 is redaction-gated,
   so the card would be empty pre-lock for a research participant.
3. **Author the governance mapping as data.** Make authority/documentation/fairness an explicit,
   versioned, reviewable artefact the way `GROUP_ASSIGNMENT.md` and the disclaimers are, rather
   than a four-branch `if` in a render file. The most work, and the only one that makes the card
   defensible in the praxis.

**In all three, `fairnessSensitive` needs a decision of its own**: either something must set it
(an intake question? a project attribute?) or the gate should go. It is currently a control that
reads a field nothing writes, which is worse than not having it.

---

## Part 1. `w_save` no longer erases coordinates it cannot replace

### The defect

`geocode.apply_to_doc` cleared `lat`, `lng` and `formattedAddress` on **every** failure. Its
docstring justified it: a project whose address changed to somewhere unfindable must not keep
pointing at where it used to be. That reasoning is right about the pin and wrong about the data,
and the deployment made it catastrophic: **Nominatim has never been reachable from any session, so
every address edit destroyed the project's location and replaced it with nothing.**

Measured live against the running server, real geocode path, no stub:

```
BEFORE  lat 38.8977  formatted "Washington, DC (fixture)"  stale None
        (edit address to "221B Baker Street, London")
AFTER   lat 38.8977  formatted "Washington, DC (fixture)"  stale True
        address now: 221B Baker Street, London
        error: The location service could not be reached, so this address has not been
               matched yet. Saving the address again will retry it.
```

### The fix

The coordinates stay. A new `geocodeStale` flag marks them as belonging to an **earlier** address,
and `formattedAddress` is carried with them deliberately — it names the address those coordinates
actually matched, which is exactly what a reader needs in order to see it is not the address now
stored. Nothing is retained when there was nothing to retain, and a later success clears the flag.

**Retention reads the STORED document, not the client's payload.** `w_save` replaces the stored
doc wholesale with what the client posted, so `apply_to_doc` now takes `previous=project.doc`. A
client that omits `lat`/`lng` from its payload cannot delete a stored position through a failed
geocode. This is asserted directly, and it fails when the parameter is removed.

**Clearing the address still drops everything.** That is the user saying there is no place, not a
geocoder failing to answer, so nothing is retained and the flag goes too.

### What the user sees

`linLocationNote(project)` in `config.js` is now the single definition of how a location reads,
because four surfaces render it and had already drifted apart once. Same reasoning as
`disclaimers.js`: a sentence rendered in four places is a sentence that diverges in four places.
It returns three states, where there used to be two — `matched`, `stale`, `none`.

Browser-verified, operational account, on the project above:

```
workspace list  : "Map position is for the previous address (Washington, DC (fixture)). The
                   location service could not be reached, so this address has not been matched
                   yet. Saving the address again will retry it."
detail Location : same sentence, class "detail-globe-note ws-note ws-geo-warn", and the atlas
                   still draws the pin
```

The pin is drawn and labelled, not deleted and not passed off as current.

**One string changed, and it is composed operational wording — flagged for your review.** The
unreachable-geocoder message said "…so this project has **no map position yet**", which became
false the moment a position was retained: the line would have shown a pin while asserting there
was none, which is the exact class of contradiction Part 2 exists to remove. It now reads "…so
this **address has not been matched** yet". True in both cases, and more accurate anyway, since
the failure is about the address. The new "Map position is for the previous address (X)." clause
is also mine. Neither is liability or consent language; both are one string each to change.

### The same shape elsewhere: one instance, and it was this one

I swept the server for "overwrite or clear stored data with the result of an operation that can
fail". Every `.pop(` on a stored document in `server/app/` outside `simulation/`:

```
geocode.py:172-176   the defect above
writes.py:196        w_save's address-CLEARED branch — a success path, user intent, correct
```

That is the whole list. Related but not the same shape, checked and cleared:

- **`_derive_cutoff`** substitutes the wall clock for an unparseable document date (the pipeline
  audit's D3). It replaces a *missing* value rather than discarding a stored one. Still a defect,
  still open, not this one.
- **`extract_many` / `documents.py`** refuse and store nothing on failure, which is the correct
  handling of the same risk.
- **`w_saveportfoliohealth`** deletes prior snapshots before inserting, but in one transaction, so
  a failed insert rolls the delete back.
- **`LinStore.saveProject`** writes its caches only inside the success path.
- **`store.js hydrate`** was this shape — a slim refresh overwriting location with absence — and
  was fixed generally in PR #198. Verified still fixed in the previous session.

**So: one instance, now fixed.** I am reporting that as a real answer rather than a reassuring
one, and the sweep was mechanical rather than exhaustive by reading — a path that overwrites a
stored field by assignment rather than by `.pop` would not have shown up in that grep.

---

## Part 2. The decision card no longer contradicts the status beside it

### Why the derived branch disagreed with the badge: two different sources, one of them dead

**Not the same status read differently. Two sources**, and the second one has been broken since
the module renumbering.

The badge reads the stored `project_status` through `getProjectFusion`. The action plan called
`deriveActionPlan`, which has three branches:

1. **One row per Yellow/Amber/Red category.** Looks up `CATEGORY_ACTIONS[c.id]`. `CATEGORY_ACTIONS`
   is keyed `cat1`…`cat11`; `LIN_CATEGORIES` ids have been `a1`…`d1` since `fd5bf45`. **The lookup
   never matches, so `if (!a) return;` skips every category, on every project, always.**
2. **A row per Red module**, from `fusion.redFlags`. `redFlags` is produced only by
   `categories.js`, the retired client-side engine that no participant route loads;
   `taxonomy.js`'s `getProjectFusion` returns `{status, redReview, stored}`. **Always empty.**
3. **The all-clear fallback**, fired when the first two produced nothing — which is always.

So the plan's only reachable output was a hardcoded row reading "All categories Green / Routine
monitoring", printed beside a Red badge on the same card. Not a disagreement about the status: a
table that could not see the status at all, falling back to reassurance.

### The minimum change

**The all-clear fallback is deleted, and nothing replaces it.** `actionPlanHtml` already returns
`""` for an empty plan, so the table simply does not render — the same abstain-by-absence contract
the server keeps, where a module with no evidence is absent from `module_results` rather than
present with a comforting value.

**No wording was composed and nothing was invented.** I did not repoint `CATEGORY_ACTIONS` to the
current ids: that would switch on a recommendation engine that has never run, which is the design
decision you reserved, not a defect fix.

**The four card fields are untouched and are not contradictory.** Conflict, Authority, Recommended
action and Documentation are derived by `deriveDecision` *from the badge's own status*, so they
agree with it by construction — on a Red project they read "Recovery-plan review and management
escalation / Program director / PMO lead". They are still derived rather than stored, which is
D7.2 and is the thing the section above is about. **Removing them needs replacement wording that
does not exist, so I stopped, as instructed.**

Browser-verified after the change, both account types:

| | Operational (OPS-1) | Research (PM-R1) |
|---|---|---|
| Detail page renders | yes, 12,024 chars | yes, 8,745 chars |
| State badge | **Red** | **Awaiting analysis** |
| Card badge | Red | (no card — no stored result) |
| Action-plan table present | **no** | no |
| "All categories Green" anywhere | **no** | no |
| "Routine monitoring" anywhere | **no** | no |
| Page errors | none | none |

### A second dead read, found and left alone

`detail.js:1558` also reads `f.redFlags`, from the same `getProjectFusion` that has not returned
it since `taxonomy.js` replaced `categories.js`. It fails safe — an empty list renders nothing —
so it is not producing a false statement the way the action plan was. Reported, not touched.

---

## Verification

| Check | Result |
|---|---|
| Server suite, freshly migrated DB per suite | **1177 across 22 suites, 0 failures** (1159 → 1177) |
| `tests_render.html` | **43/43** (37 → 43) |
| `tests.html` | **51/51** |
| Geocode retention proven able to fail | 4 faults, distinct signatures (below) |
| Decision card proven able to fail | fallback restored → 39/43, the 4 substantive new checks red |
| Detail page, both account types, no contradiction | verified in a browser |
| Failed geocode leaves the previous location intact | verified in a browser, real geocode path |

**Fault injection, `test_workspace_t3t5` (70 checks, was 52):**

| Fault restored | Result |
|---|---|
| The old erase-on-failure | **62/70**, 6 checks red |
| Retention reads the client doc, not the stored one | **67/70**, the payload-stripping check red |
| A later success does not clear the stale flag | **67/70** |
| The address-cleared branch leaves the flag behind | **69/70** |

**One vacuous check was written and caught by that injection.** The address-cleared check
originally ran on a project whose flag had *already* been cleared by an earlier successful
geocode, so it passed whatever the code did — fault 4 came back green the first time. It now
asserts the precondition that the project is flagged stale at that moment, and the check fails
when the fault is restored. That is the fifth session running in which a check turned out to pass
for the wrong reason, and again it was fault injection rather than review that caught it.

---

## What I could not establish, and what is still open

- **Whether any production project has coordinates.** Production was not inspected. This fix had
  to land before any geocoding is attempted, which is why it went first — a backfill would have
  been destroyed by the next address edit.
- **Whether Render can reach Nominatim.** Unknowable from here. The retention change makes the
  question safe to answer by experiment rather than expensive.
- **Whether the overwrite-on-failure sweep is exhaustive.** It was a `.pop`-based grep plus
  reading the failure paths I know. A field overwritten by assignment inside an `except` would not
  have appeared.
- **D7.2 itself.** Three of the card's four fields still have no stored source, and
  `fairnessSensitive` is still unobtainable. The routes are in the first section; the decision is
  yours.
- **`CATEGORY_ACTIONS` is now provably dead code**, along with `detail.js`'s `redFlags` read.
  Whether to repoint it or delete it depends on which of the three routes you take.
