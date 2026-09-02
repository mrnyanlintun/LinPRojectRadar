# RUN 111 — THE RECOGNITION STEP

**A MIGRATION WAS ADDED: `0033_recognition_matches`.** `/readyz` reports 503 with
SchemaOutOfDate until `alembic upgrade head` is run against the target database.

Starting commit `b055261` (Run 110), tree clean, `main == origin/main`.
`SIMULATION_VERSION` moved `sim-2026.09-v55` → **`sim-2026.09-v56`**, history appended.
No key was present in this session and **no model was called anywhere in this run.**

---

## 1. THE CENSUS, BEFORE AND AFTER

One project, twenty-one documents, `tools/drive_run110_census.py` unchanged between the two
halves, through the real `projectupload` / `projectcomputeall` / `projectcategoryapply` routes.
Nothing under test supplied.

| | band | computed, no band | abstain | no row | total |
|---|---|---|---|---|---|
| **BEFORE** (`b055261`) | 16 | 1 | 14 | 0 | 31 |
| **AFTER** | 16 | 1 | 14 | 0 | 31 |

**The delta, module by module: NONE. Zero modules changed state.** The two census JSON files
are byte-identical. Nothing regressed (section 5.4), and nothing advanced either — and the
reason it did not advance is the honest one: **the recognition step has no key in this
environment, so it did not run.** With no key it does not guess, does not fall back, and does
not fail the upload; it writes a refusal onto the stored signal inputs naming the provider, the
model and the empty variable, and every module abstains exactly as it did before.

The refusal, read out of the stored `computed_results.signal_inputs` of the census project:

```
attempted        : false
reason_code      : provider_key_absent
provider         : anthropic     model: claude-sonnet-4-5     key_env: ANTHROPIC_API_KEY
modules_not_attempted : A4.5, A4.6, A4.8, A4.9
detail: "...NO recognition was attempted, no value was read from any document by
         recognition, and nothing was served by another provider in its place."
```

---

## 2. WHAT YOU MUST DO ON RENDER TO VERIFY THIS

Follow this in order. It takes about ten minutes.

**Step 1 — deploy and migrate.** Push, let Render build, then run
`alembic upgrade head` from `server/` on the deployment. Until you do, `/readyz` returns **503**
and `projectupload` refuses documents. When it is done, `/readyz` returns **200**.

**Step 2 — check the settings before you upload anything.** Open in your phone browser:

```
https://<your-service>/exec?action=health
```

Look at the new **`recognition`** block. You should see:

```json
"recognition": {
  "provider": "anthropic",
  "model": "claude-sonnet-4-5",
  "keyEnv": "ANTHROPIC_API_KEY",
  "keyPresent": true,
  "modelSetting": "AI_RECOGNITION_MODEL or AI_ANTHROPIC_RECOGNITION_MODEL",
  "modulesWithRecipes": ["A4.5","A4.6","A4.8","A4.9"]
}
```

**`keyPresent` must be `true`.** If it is `false`, recognition will not run and nothing below
will happen — set `ANTHROPIC_API_KEY` in the Render environment and redeploy. Also look at
`aiProviders` in the same response: it now lists **four** call sites, `extraction`, `spec`,
`narration` and the new `recognition`. Read the model identifiers there against section 5 below
before you go further — **I strongly suspect `claude-opus-4-6` is not a real model name.**

**Step 3 — upload a subcontractor performance report and compute.** Use the project you
normally test with. Upload a Subcontractor Performance Report that prints a per-firm table —
a firm column, an assessment-period column, and a rating column with words like `Very Good`
or `Satisfactory` — plus the scale it is on, its own date and its version. Then press
**Compute** (the `projectcomputeall` action) as you normally do.

**Step 4 — what you should see if it worked.** On the results card, **A4.8 Subcontractor
Performance should move from "Awaiting a subcontractor performance assessment…" to a banded
reading.** On the exact fixture used here — Northline Mechanical `Very Good`, Harbour
Electrical `Satisfactory` — it should band **Yellow**, governed by Harbour Electrical, because
Very Good is Green, Satisfactory is Yellow, and the most adverse posture governs. That ladder
is the owner's, it is in `canonical_v4`, and the model has no access to it.

**Step 5 — check what was matched to what.** Read the stored result's `signalInputs`; the
`recognitionLog` entry for A4.8 lists, per quantity, the label the model matched, the document
it was printed in, the period, and `anthropic/<model>` that recognised it. If any quantity was
not answered, the entry says `outcome: not_recognised` and names exactly which.

**Step 6 — prove determinism on your own deployment.** Press **Compute again** on the same
period without changing any document. The reading must be identical, and the
`replayed_from_recorded_match` flag on every match must read `true` — meaning **no model call
was made the second time.** If you want to see it in the database:
`SELECT quantity_id, model, evidence_fingerprint FROM recognition_matches;` — one row per
question, and no new rows appear on a recompute.

**If it fails instead.** Every failure is loud and names what to change:
* wrong model name → the reading's log carries the provider's own 404/400 body **with the model
  identifier in it**, and says the setting is `AI_RECOGNITION_MODEL`;
* key missing → names `ANTHROPIC_API_KEY` and says nothing was served by another provider;
* model returned something unusable → the log quotes what came back, up to 400 characters, and
  says what was expected;
* model named a label it was never shown → refused, with the message saying so, and **no figure
  entered any reading.**

Nothing anywhere falls back to a second provider. Nothing abstains quietly.

---

## 3. THE SIX MODULES: DOES EACH PRODUCE A READING?

Measured against the 158 RAW evidence rows the census fixture actually stores.

| module | recipe | can it produce a reading? | on what evidence / which label |
|---|---|---|---|
| **A4.8 Subcontractor Performance** | yes | **YES, once a key is present.** Composed and run end to end here through the real `canonical_v4.subcontractor_reported_ratings` and the real ladder. | `subcontractor_ratings_json [Subcontractor]`, `[Assessment period]`, `[Rating]`, plus `subcontractor_rating_scale`, `subcontractor_report_date`, `subcontractor_report_version` — all in `subcontractor_report`. Result: 2 firms, governing posture **Yellow**. |
| **A4.5 Weather Day Impact** | yes | **NO — and not because the reader is missing.** | The store holds the *approval* scalars (`weather_days_approved`, `weather_days_claimed`, `weather_allowance_days`, `weather_approval_period`, `weather_time_extension_*`) and **no weather event register**. `weatherImpactEvents` needs a row per event with the activity, the schedule path and the float. A count of weather days is not a register, and manufacturing events from a count is inventing values. |
| **A4.6 Change Order Frequency** | yes | **NO.** | Store holds `change_order_count: 2`, `baseline_contract_sum`, `revised_contract_sum`, `change_order_date`. `changeEventRegister` needs a row per change with its value, direction, type and cause. A count is not a register. |
| **A4.9 Procurement Lead Time** | yes | **NO.** | Store holds `long_lead_items_total`, `at_risk`, `delayed`, `on_schedule` — aggregates. `procurementItems` needs a row per item with the required-on-site date, the forecast delivery date and the float. |
| **A4.7 Dispute Escalation Index** | **no recipe, deliberately** | **NO.** | The issues register could in principle be recognised; the **escalation process cannot**. `canonical_v4.dispute_escalation` states outright that the ladder "is not universal and is not defined here" — the stages, their order and their escalation class are declared by whoever governs the process. That is authority of the same kind as `signalWeightPolicy`. Recognising it from a document would invent a governance artefact. |
| **A1.11 Independent EAC Reconciliation** | **no recipe, by the order** | **NO, and it may never be.** | `independentEacPair` is not a figure any document states: it is the **claim that a second forecast was prepared independently of the first**. Two numbers in the evidence store do not establish that. What it would take: a governed intake field, or a field in the forecast document itself, in which whoever prepared the second forecast **asserts** the independence — the assertion has to come from a person with the authority to make it, not from a reader of numbers. |

A4.5, A4.6 and A4.9 **are still asked**, every one of their quantities, and the log records per
quantity that nothing answered it. That is deliberate: the platform must say what it looked for
rather than be silent about four modules. It also gives you the right diagnosis on the
deployment — the fix is a document that prints the register, not a change to this code.

---

## 4. THE TWO REPAIRS, PROVED

Both are in `tools/drive_run111.py`, section 2.1, through the **real upload route** with a
register printed the way a person prints one: headings with capitals and spaces, dates as dates.

**Repair 1 — `canonical_v4._day`.** A register printing `2026-02-05` in the day column was
refused with "carries a day that is not a number". It now falls through to the calendar form.
`_day({"decision_day": "2026-02-05"}, ...)` → ordinal `739652`. A numeric index is unchanged.
**Genuine rubbish still refuses**, now naming both accepted forms.

**Repair 2 — `documents.py` `reporting_period`.** The only cell on that row read by bare exact
key; every other cell used `_first_of` heading matching. It was therefore always `None`, no
decision was ever in window, and `submittal_rejection` refused with "No submittal … was assessed
in the period being reported". It now matches on the register's own heading.

**Measured through the real route:** every decision now carries `2026-03`, and
`submittal_rejection` forms the rate: **3 of 20 = 0.150**.

**Falsification — both proved able to fail.** The pre-change bare-key join, applied to the same
register, refuses it ("assessed in the period being reported"). The pre-change `_day` rule,
applied to the same date, refuses it ("carries a day that is not a number").

---

## 5. THE CONFIGURED MODEL IDENTIFIERS — READ THIS FIRST

Read out of `app/ai_provider.PROVIDERS` through the live resolution path, per provider **and per
call site**. There are now **four** call sites; Run 111 added `recognition`.

| provider | call site | model identifier | key variable |
|---|---|---|---|
| anthropic | extraction | **`claude-opus-4-6`** | `ANTHROPIC_API_KEY` |
| anthropic | spec | `claude-sonnet-4-5` | `ANTHROPIC_API_KEY` |
| anthropic | narration | `claude-3-5-haiku-latest` | `ANTHROPIC_API_KEY` |
| anthropic | **recognition** (new) | `claude-sonnet-4-5` | `ANTHROPIC_API_KEY` |
| openai | extraction / spec / recognition | `gpt-4o` | `OPENAI_API_KEY` |
| openai | narration | `gpt-4o-mini` | `OPENAI_API_KEY` |
| groq | extraction / spec / recognition | `llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| groq | narration | `llama-3.1-8b-instant` | `GROQ_API_KEY` |

Endpoints: `https://api.anthropic.com/v1/messages`,
`https://api.openai.com/v1/chat/completions`, `https://api.groq.com/openai/v1/chat/completions`.

**The new recognition call site introduces NO new model identifier.** Each provider's
recognition default is deliberately the *same string* as its `spec` default. Adding a fourth
unverified name per provider would have given you three more things to check for no gain.
Override with `AI_RECOGNITION_MODEL` or `AI_<PROVIDER>_RECOGNITION_MODEL`.

**Three constants that are NOT the live path**, established by reading the call sites rather
than by grep:
* `extraction_client.EXTRACTION_MODEL = "claude-opus-4-6"` — a **default argument** of
  `ProviderExtractor.__init__`. The live builder passes `model=cfg.model` and a built client, so
  it is never read on the live path; it is read by tools and tests that construct the extractor
  directly.
* `spec_apply.SPEC_MODEL = "claude-sonnet-4-5"` — **dead** on the live path; both appliers take
  a built client. The file says so itself.
* `training_narration.NARRATION_MODEL` — **dead** on the live path, same reason.

**ALL OF THESE ARE UNVERIFIED, AND ONE LOOKS WRONG.** Not one identifier was checked against any
provider's catalogue — not by Run 93, which chose them without a key, and not by this run, which
also has none. **`claude-opus-4-6` does not match any Anthropic model identifier I recognise**;
to the best of my knowledge the current family is Claude 5 (`claude-opus-5`, `claude-sonnet-5`,
`claude-fable-5-1`, plus `claude-haiku-4-5-20251001`), and `claude-sonnet-4-5` was real but is
no longer current. **I could not verify this from this session and this report is not authority
for it — check it first on your deployment.** I did not rename anything: the order asks for the
identifiers to be reported and for rejection to fail well, not for a guess.

**What verifying them takes:** one authenticated `GET https://api.anthropic.com/v1/models`
(header `x-api-key`, `anthropic-version: 2023-06-01`), one `GET
https://api.openai.com/v1/models`, one `GET https://api.groq.com/openai/v1/models`. Three
requests, on the deployment, with the keys that are already there.

**A rejected model name fails well — proved.** A constructed HTTP 404 (transport level; *not* a
model's behaviour and not reported as one) fed to the boundary's own error formatter produces a
message carrying **the model identifier, the provider, and the provider's own status and body**.
An unknown provider name names `AI_PROVIDER` and `AI_RECOGNITION_PROVIDER`. A missing key names
the variable and states that nothing is served by another provider in its place.

---

## 6. DETERMINISM: THE REASONING, THEN THE MECHANISM

**The reasoning.** A model call is not a deterministic function. `temperature=0` narrows the
distribution; it does not collapse it — serving stacks batch requests across users, and an
identifier such as `claude-3-5-haiku-latest` is an *alias* that can be repointed under a running
deployment without any change to your configuration. So determinism cannot be obtained *from the
call*. It has to be obtained by **not making the call twice.**

Three alternatives, considered and rejected as unsound:

1. **"temperature 0 is enough."** It is a narrowing, not a guarantee, and it does not survive an
   alias moving.
2. **"Cache on project, period and module."** Deterministic and **wrong**. A revised document
   changes the evidence, and the stale match would be replayed over it. That is worse than
   varying, because it is silently incorrect.
3. **"Ask three times, take the majority."** Three draws from a distribution are still a draw
   from a distribution, at three times the cost.

**The mechanism.** A recognition question is keyed by a SHA-256 over **everything that could
change its answer**: every candidate offered (document id, document type, sha256, period, label,
value), the exact specification text shown, the prompt template version, the provider name, and
the model identifier. `recognition_matches` (migration 0033, append-only, unique on project +
quantity + fingerprint) holds the answer. A question already answered under that key is
**replayed with no call made at all**. Change the evidence, the specification, the template, the
provider or the model and the fingerprint moves: the question is asked again and *both* rows
remain, so "why did this reading change?" is answerable from the database.

**Proved, and proved so it could fail.** The driver does not stub the model to return an answer.
It replaces the ask function with one that **raises**, so any call at all fails the section:
* a recorded match is replayed and no call is made; two reads give an identical trace;
* the replayed value is read out of the *evidence store* by the recorded identifier;
* changing **one printed value** re-asks (the exploding function fires) — the stale match is not
  replayed over changed evidence;
* changing the **provider** re-asks — two models never share one recorded answer;
* changing **one character** of the specification changes the fingerprint;
* the fingerprint is stable across database row order.

**What is NOT guaranteed, stated plainly.** Within one deployment's store, identical evidence
always produces the identical reading, for ever. The **first** ask against a fingerprint that
has never been asked is one model call and is not itself reproducible: two deployments starting
from empty stores could in principle record different first answers. That is **detectable rather
than invisible**, because every match records its fingerprint, provider and model. Making two
deployments agree requires copying the `recognition_matches` rows between them — the fingerprint
is exactly the key for that, and it is a straightforward export/import you can ask for.

**What I built.** `app/recognition.py` (the engine: specifications, candidates, prompt,
fingerprint, result contract, provider call, match store, orchestrator, health diagnostics) and
`app/recognition_recipes.py` (what the four servable modules ask for, in plain terms, and how a
structure is composed). The single wiring point is `documents.assemble_and_store`, after both
existing document assemblers, with `setdefault` — so a structure from the governed intake or
from the declared vocabulary is **never** displaced. Not one module changed.

**The model's authority is one thing: it returns a candidate identifier.** The value is then
read out of the evidence store by that identifier. A model that echoes a figure cannot put it
into a reading, and an identifier that was not offered is refused by name. *"It never invents a
value"* is therefore a property of the mechanism, not an instruction in a prompt. The recognition
code contains **no division, multiplication, subtraction, modulo or exponentiation anywhere**
(checked by AST walk), and, with docstrings and comments removed, contains no `status_color`, no
`threshold`, no `Green`/`Amber`/`Red`, and no `band_` field.

---

## 7. THE C1.5 QUESTION — FOR YOU, UNDECIDED

`MODULE_USE` in `models_cat89.py` declares which downstream use each module's evidence is
*qualified for*, because qualification is use-specific (spec section 19): A6.1
`requirement_conformance`, A6.2 `safety_measurement`, A6.3 `environmental_conformance`, A6.4
`official_assessment_ingestion` — and `USE_REQUIREMENTS` records that all four of those uses
currently require **nothing** of their evidence, while `governance_authorization` and
`governance_authority_check` require a complete audit chain and freshness. Every one of those
four is a Category-8 module whose evidence is consumed by something downstream. **C1.5
Information Completeness Ratio is not like them**: it is a Category-9 module, it is metadata, it
casts no vote (`category_9_metadata_only = True`, `voting_eligible = False`), and it is routed
`gated=False` precisely because Category 9 *is* the assessment and gating it on its own output
would be circular — so the `MODULE_USE` lookup it crashes on at `models_cat89.py:928` sits on a
line whose result its own route then never uses. **The honest reading is therefore that C1.5
needs no entry at all**, and the fix is not to name a use for it but to stop looking one up for
an ungated route — but that is a governance decision about what qualification means, not an
engineering one, so I have not made it. **The question is: does C1.5's evidence have a
downstream use, or is it an authoring-time gate whose only consumer is the reader of the
Category-9 assessment itself?** Answer that and the fix is one line either way.

Measured, so you decide from facts: **C1.5 abstains cleanly today whenever no
`informationPackageRecord` is supplied** — the structure is absent, `_route` returns before line
928, and the census shows it abstaining rather than failing. It raises `KeyError('C1.5')`
**only** when a package record *is* present. Run 110's guard contains that into a failed reading;
the route survives either way.

---

## 8. EACH GOAL: REACHED OR NOT, INCLUDING THE FAILURES

| goal | reached |
|---|---|
| §1 census before and after, same fixture, delta named | **YES** — identical, zero movement |
| §2.1 both A4.3 repairs, proved, with falsification | **YES** |
| §2.2 C1.5 established and put to the owner undecided | **YES** |
| §3.1 rejected model name fails loudly naming model, provider, setting | **YES** |
| §3.2 identifiers per provider **and per call site** | **YES**, incl. the three dead constants |
| §3.3 stated unverified and what verifying takes | **YES** |
| §4 the recognition step: specification, prompt, result contract, traceability | **BUILT AND EXERCISED TO THE BOUNDARY OF THE CALL** |
| §4 determinism established and reasoned | **YES** — mechanism built and proved able to fail |
| §4 six modules producing readings | **PARTIAL, and honestly so:** one of six is servable on the stored evidence; the other five are blocked by the *evidence*, not the reader (section 3) |
| §5.1–5.5 all five invariants | **YES** |
| §6 report written, committed, printed | **YES** |

**Failures and iterations along the way, all of them:**
1. First driver run: `structure["recognition"]` KeyError — the traceability block is attached by
   the orchestrator, not by `recipe.build`; the driver was asserting against the wrong layer.
   Fixed in the driver.
2. Second run: wrong expected ordinal for `2026-02-05` (I wrote 739287; it is 739652) and wrong
   result key names (`assessed_count` / `rejected_count`; they are `assessed` / `rejected`).
   Both were my errors in the check, not in the code.
3. Third run: the §5.1 "no threshold word" check was matching its own *docstring*, and my
   arithmetic check was a malformed expression that could not have failed correctly. Replaced
   with an AST walk that strips docstrings and looks for real `BinOp` nodes. **That third one is
   worth naming: it was a check that could not fail, which is the same defect as the Run 110
   guard driver's.**
4. Migration first written importing `app.research_models` for its column types and calling
   `JSONType()` / `ULID()` on instances rather than classes. Rewritten to declare both inline so
   the migration does not import the application.

Final: **`tools/drive_run111.py` — 78 passed, 0 failed, 78 checks.**

**Every suite re-run green** on a database migrated to `0033`, as scripts with the system python:
`test_run102` 33/33 · `test_map_and_module_count` 77/77 · `test_run26_counts_and_wiring` 59/59 ·
`test_run67_category9_and_no_band` 21/21 · `test_run89_required_core` ALL PASS ·
`test_run87_comparison_only` ALL PASS · `test_run89_data_integrity_gate` ALL PASS ·
`test_run110` 28/28 · `drive_run98` 99/99 · `drive_run103_census` 6/6 ·
`drive_run103_invalid_network` 33/33 · `drive_run104` 55/55 · `drive_run105` 33/33 ·
`drive_run106` 50/50 · `drive_run107` 92/92 · `drive_run108` 32/32 ·
**`drive_run110_guard` now prints SECTION 2.5: PROVED** (see §11).

---

## 9. PREMISES IN THE ORDER AND THE BRIEFING THAT PROVED FALSE

1. **"Six modules are waiting on it: Weather Day Impact and Subcontractor Performance, whose
   values are already in the store."** Half true. **Subcontractor Performance's values are
   genuinely there**, all six of them. **Weather Day Impact's are not.** The store holds the
   OAC approval scalars; `weatherImpactEvents` is defined on a per-event register with the
   activity, the schedule path and the float, and **no weather event register exists in the
   store at all**. The same is true of Change Order Frequency and Procurement Lead Time: the
   store holds aggregate counts, the structures need registers. **Four of the six are blocked by
   the evidence, not by the reader.** Building the reader does not unblock them and nothing
   short of a document that prints the register will.
2. **"`MODULE_USE` … C1.5 dispatches through the same factory and raises a KeyError. Run 110's
   guard contains it — the route survives — but the module still cannot run."** True only when a
   structure is present. Measured: with no `informationPackageRecord`, C1.5 abstains cleanly
   *before* the `MODULE_USE` lookup, which is why the census shows it ABSTAINS and not a failed
   reading. The KeyError is real but is reached only on the path where the module would
   otherwise have computed.
3. **"The order's section 4 describes the model recognising a quantity."** It does, but the four
   modules that most obviously need it need **table columns**, not stated figures. The order's
   framing of a single "value" does not cover it. I extended the candidate model: a table is
   offered as one candidate per printed column heading, so recognising "the column headed
   *Rating* is the rating" is the same act as recognising a scalar and no column heading is ever
   hand-mapped. This is an addition to what the order describes, and I am flagging it as one.
4. **Section 4 lists four structures that must not be recognised. There is a fifth of the same
   kind.** A4.7's `claimDisputeRegister` carries the **project's own governed escalation
   process** — the stages, their order, their escalation class — which `canonical_v4` is explicit
   is "not universal and is not defined here". That is authority, exactly like
   `signalWeightPolicy`. I gave A4.7 no recipe and said so in code. The order counted A4.7 among
   the six the reader would serve; it cannot be, on the same reasoning the order itself applies
   to the other four.
5. **The briefing's model-identifier table is complete for `PROVIDERS`, but the claim that
   `extraction_client.EXTRACTION_MODEL` and `spec_apply.SPEC_MODEL` are "live call sites or dead
   constants" resolves differently for the two.** `SPEC_MODEL` is fully dead. `EXTRACTION_MODEL`
   is a **default argument** of `ProviderExtractor.__init__` — dead on the live path, live for
   any tool or test that constructs the extractor directly. Not the same status.
6. **A defect neither the order nor the briefing mentions: the `Observation` model and migration
   0032 disagreed about `RAW`.** Migration 0032 widened the `ck_observations_kind` CHECK
   constraint to admit `RAW`; `research_models.py:757` was left declaring only four values. On a
   database built by `alembic upgrade head` this was harmless, because the database's constraint
   is the enforced one — but **any schema created from the SQLAlchemy metadata instead would
   have rejected every RAW row Run 110 emits.** Repaired; the two now say the same thing.

---

## 10. REAL VERSUS HARNESS. NO MODEL CALL WAS SIMULATED

Measured first, not assumed: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` and
`ANTHROPIC_AUTH_TOKEN` are all absent from this environment. The driver checks this and prints
it before anything else.

**REAL** — production code on real data: the census (both halves, real upload/compute/apply
routes, nothing supplied); the 158 RAW evidence rows; candidate construction and its order
independence; prompt construction; every fingerprint property; the determinism replay and both
re-ask paths; the A4.8 composition run through the real `canonical_v4.subcontractor_reported_
ratings` and the real owner ladder; both A4.3 repairs through the real upload route and their
falsifications; the C1.5 measurements; the §5 invariants.

**HARNESS** — inputs constructed by the driver, labelled as such in the output at the point of
use:
* the six `Match` records for A4.8 in §4f. Each one names a **real** candidate from the real
  evidence store; **no model chose them**, and the driver says so in the printed output. What is
  proved is everything *downstream* of the choice.
* the malformed answer strings in §4d. Written by the driver to exercise the parser. They are
  **not** a model's output and are not reported as one.
* the HTTP 404 in §3. A constructed *transport* rejection fed to the error formatter, to prove
  the message names the model. It is not a model's behaviour.
* the single recorded match row in §4e. Constructed by the driver in place of a row a real call
  would have written. The model is never stubbed to *answer*: it is replaced with a function
  that **raises**, so a call that should not happen fails the section.

**WHERE THE TESTED SURFACE STOPS, EXACTLY.** Everything up to and including
`recognition.build_prompt` and `recognition.evidence_fingerprint` is exercised on real data.
Everything from `recognition.parse_answer` onward is exercised on constructed input.
**The one thing that is not exercised at all is the HTTP request itself** —
`ai_provider.build_client(...).complete(blocks, ...)` for the `recognition` role — and therefore:
whether the configured model identifier is accepted by the provider, whether the model obeys the
result contract, and whether it picks the right candidate. **Those three are unknown until you
run step 3 on Render.** Nothing in this report claims otherwise.

---

## 11. FOUND AND NOT FIXED, AND ONE FOUND AND FIXED

**Fixed, beyond the order.**
* `tools/drive_run110_guard.py` read the pre-change file as `git show HEAD:…`. That was correct
  while Run 110 was uncommitted; the moment it committed, HEAD contained the guard, so the
  falsification compared the new code against itself and printed **NOT PROVED on every run** — a
  check that had silently stopped being able to fail. Pinned to `966927b` (Run 109). It now
  prints **SECTION 2.5: PROVED**.
* The `Observation` model / migration 0032 `RAW` disagreement (§9.6).

**Found and NOT fixed.**
* **`USE_REQUIREMENTS` requires nothing of any of the four uses `MODULE_USE` names.** All four
  Category-8 gates therefore pass on any structure that carries a `qualification` block at all.
  That may be exactly right — the comment says "a use absent a requirement does not acquire one
  by default" — but it means the Category-8 self-gate is, today, a gate with no bar. It is a
  governance question, not mine, and it is adjacent to the C1.5 question in §7.
* **Four suites were already red before Run 108** with `MissingModuleError` on retired modules:
  `test_run29_canonical_oracles`, `test_run19_category_4`, `test_run29_supply_path_guard`,
  `test_run29_corpus_reconciliation`. Not touched, as instructed.
* **`recognition_recipes._register_absent`** is the builder for A4.5, A4.6 and A4.9. It returns
  `None` unconditionally and says why in its docstring: no document in this repository has ever
  printed one of those registers, so composing one would ship a shape nothing has been run
  against. When you have a document that prints such a register, that function is the one to
  write, and the quantities beside it are already specified in plain terms.
* **The A4.5 approval scalars are in the store and still unused.** `canonical_v4` reads them
  leniently off `weatherImpactEvents` for the Run 107 band arms — but the structure as a whole
  needs the event register, so the scalars cannot reach the module on their own. Serving them
  would mean a Run 107 band arm that computes without the schedule-impact reading beside it,
  which is a design decision for you, not a defect to fix quietly.
