# Run 124 — the extraction output budget, sized from measurement

**Report date:** 2026-09-03
**Starting commit:** `ca1a745` (= origin/main, `git status --porcelain` empty)
**Ending commit:** the single commit titled "Run 124: the extraction output budget, sized from measurement (MAX_TOKENS 1536 -> 8192)". Its sha cannot be printed inside itself; it is recorded in the run's handoff message and is verifiable with `git log --oneline -1`. Tree clean after.
**Migration head:** `server/alembic/versions/0033_recognition_matches.py` — **no migration added; none was required.** Nothing about a module output budget touches a stored schema.
**`SIMULATION_VERSION`: MOVED, `sim-2026.09-v64` -> `sim-2026.09-v65`,** because a production constant changed. Appended to `SIMULATION_VERSION_HISTORY` with its reasoning.
**No model key in this environment.** `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` are all absent. **No model call was made and none was simulated.** What served in their place: reading the code, and an offline token estimate using `cl100k_base` via `tiktoken` in a throwaway venv in the scratchpad. That is an **estimate, not a measurement of the extraction model's own tokenizer** — see §C for why the conclusion is robust to that anyway.

---

## The answer, at the top

**Yes — with one qualification the owner must decide on.**

The output cap was the binding constraint for the six failed documents and it is now large enough that no register the corpus will plausibly produce can exceed it. `MAX_TOKENS` moved from **1536 to 8192**, sized at roughly **twice the largest complete reply measured** (a 46-row submittal decision table, ~4004 tokens). Nothing in this codebase bounds it independently: `ai_provider.PROVIDERS` carries **no per-provider or per-model output limit**, and `simulation/spec_apply.py:225` has been issuing **8192 through the same client class against the same provider** all along. This is not a raise into an unproven region.

**The qualification: the 45-second timeout is a separate problem, it is NOT in the application, and this run did not fix it.** I found it. It is `RESILIENT_TIMEOUT_MS = 45000` at **`assets/js/store.js:278`** — a **browser-side `AbortController`**, not a server limit. The server's own `REQUEST_TIMEOUT_S = 120` is untouched and was never the binding limit. This matters more than it looks: **raising the output cap makes replies longer, therefore slower to generate, therefore more likely to hit the 45s browser abort.** The fix for truncation makes the timeout more likely, not less. §B states the options; I changed nothing there because it is a policy choice, not a one-line edit.

**A third finding the owner did not ask for and needs most.** The order's premise that truncation might be silent is **half right, and the wrong half is the dangerous one.** A reply cut off by the output cap is caught loudly, in two independent places, and always was. But a model that **closes the array early on its own** — returning 18 of 26 rows as syntactically perfect JSON — passes every check on the path and is assembled as a complete register. **Nothing anywhere compares the row count against the document's own stated total, even when the same reply carries it.** I demonstrated this. It is reported, not fixed, per the order.

---

## Three premises checked. The owner was right twice and incomplete once.

| Premise (as briefed) | Code | Verdict |
|---|---|---|
| The order says a 45-second timeout; the brief says the code says 120 and there is no 45 in the app | `extraction_client.py:82 REQUEST_TIMEOUT_S = 120`. **No 45-second constant in `server/app/`** — confirmed, every `45` there is "Run 45" or a ratio | **Owner's brief correct — and I closed the gap it named.** The 45s is real and it is at `assets/js/store.js:278`, in the browser. See §B.1 |
| The order says twenty concurrent calls | `extraction_client.py:79 DEFAULT_CONCURRENCY = 10` | **Owner's brief correct.** A twenty-file batch runs **two waves of ten**, not twenty at once |
| The order treats the cap failure and the timeout as one problem | They are two mechanisms with opposite responses to the same fix | **Owner's brief correct, and it matters.** Kept separate throughout |

One correction to the brief itself, offered because it was invited: the brief called `describe_json_truncation` the truncation defence. It is the **fallback**. The authoritative test is the provider's own `stop_reason`, and there are **two** of them (§D).

---

## A. Why was it 1536?

**The constant:** `server/app/extraction_client.py`, line 81 before this run. Value `1536`. It is now line 120, value `8192`, with its reasoning recorded above it.

**When it was set, and on what reasoning.** `git log -L81,82:server/app/extraction_client.py` returns exactly one commit: **`fc7be2c`, "Training upgrade run 1: the quality thread (#212)"** — the commit that **created the file**. It was added as `+MAX_TOKENS = 1536` in the file's initial state, as a bare literal.

**No reasoning was recorded, and I am saying so plainly rather than inferring one.** There is no comment above it, no cost note, no latency note, and nothing in the commit message about output budgets. This is worth contrasting with the line immediately above it: `DEFAULT_CONCURRENCY = 10` carries a three-line comment explaining exactly why ten ("well inside the provider's per-minute limits… collapsing a 27-document period from >2 minutes to well under half a minute"). The author documented the concurrency decision and did not document this one. **The most defensible reading is that 1536 was a default nobody had yet had a reason to question — not a deliberate cost ceiling being overridden here.** No register-bearing document type existed when it was written.

**A.1 — one constant, or per type, or per provider?** **One constant, for all extraction, all document types, all providers.** It reaches the wire at `extraction_client.py:887` -> `_post(..., MAX_TOKENS)` -> `client.complete(blocks, max_tokens=...)`. There is no per-document-type and no per-provider variation anywhere on the path.

**A.2 — environment variable?** **No.** Nothing reads it from `os.environ` and there is no override. It is a source constant only, so changing it requires a deploy — which is the honest behaviour for a research instrument, but worth stating.

**A.3 — does it govern the other roles?** **No. The four roles have four separate constants**, and the brief was right to flag this:

| Role | Constant | Value |
|---|---|---|
| extraction | `extraction_client.py:120` | **8192** (was 1536) |
| spec | `simulation/spec_apply.py:225` | **8192** |
| recognition | `recognition.py:116` | 512 |
| narration | `training_narration.py:42` | 300 |

`spec_apply` is the load-bearing one for A.4 and I verified it: same `MAX_TOKENS` name, same `client.complete(...)` call at line 255, resolved through the same `ai_provider` machinery, same `anthropic` wire, same `claude-sonnet-5` model string. **A role in this codebase already runs at 8192 against the identical client and provider.** The new extraction value is not novel territory.

**A.4 — does the provider table impose a ceiling underneath?** **No.** `ai_provider.PROVIDERS` (lines 96-124) carries `wire`, `base_url`, `path`, `key_env` and a `models` dict per provider. **There is no output-limit field of any kind, for any provider or any model.** `max_tokens` is passed straight from the caller into the request body (`ai_provider.py:306` for Anthropic, `:352` for the OpenAI-compatible wire) with no clamp, no `min()`, and no validation. So nothing in this codebase would make the raise a false fix. A remote API-side model ceiling is not visible from here and cannot be tested without a key — but 8192 is below any plausible one for this model class, and `spec_apply` is standing evidence that this exact value is accepted on this wire.

---

## B. The timeout — separate, and NOT where anyone was looking

### B.1 What sets 45 seconds

**`assets/js/store.js:278` — `const RESILIENT_TIMEOUT_MS = 45000;`**

It is a **per-attempt browser `AbortController` timeout** in `postWithTimeout`, applied to the `fetch()` that carries the upload. The corroborating trail is at `assets/js/signals.js:1429`, which records that this was once a direct `fetch()` in the upload path and that "its 45s timeout and 20/40/60s rate-limit backoff moved to `LinStore.postResilient`". The upload path calls `LinStore.postWithTimeout(payload)` (`signals.js:1431`).

Four consequences, and they are not small:

1. **It is per attempt, and it bounds the WHOLE BATCH, not one call.** One HTTP POST carries all twenty documents; `a_projectupload` extracts them all inside that single request. So the 45s is not 45s per extraction — it is **45 seconds for the entire twenty-document extraction run**, and at concurrency 10 that is two waves inside one 45-second window.
2. **The server never learns it happened.** The browser aborts; the FastAPI handler keeps going to completion and stores what it extracted. So a "timeout" reported to the PM does **not** mean nothing was stored — it means the PM was not told what was. That is a reporting discrepancy, not a data loss. It is also why re-uploading after a timeout is cheap: `extraction_contract_fingerprint` caching means already-extracted documents are served from the cache and not re-billed.
3. **The upload path does not retry.** `postWithTimeout` is a single attempt; `postResilient`'s 20/40/60s backoff retries **only on a rate limit** (`store.js:272-273`) and the upload does not use it. So a timeout does **not** duplicate model calls. Good.
4. **Raising `REQUEST_TIMEOUT_S` would fix nothing**, exactly as the brief predicted. The server limit is 120 and was never reached. The binding limit is in the browser.

### B.2 Concurrency

`DEFAULT_CONCURRENCY = 10` (`extraction_client.py:79`), passed through `extract_many(extractor, jobs)` at `documents.py:4294` with **no override at the call site** — so production runs the default. **A twenty-file batch runs two sequential waves of ten**, and the batch's wall time is roughly the sum of two waves' slowest calls, not one. This is the mechanism by which a large batch starves individual calls: not that any one call is slowed, but that the **fixed 45-second browser budget is shared across waves.**

### B.3 Is the batch count capped?

**Run 123's claim is confirmed against the code.** `documents.py` enforces `MAX_BASE64_CHARS = 5_000_000` (line 200) and `MAX_FILE_BYTES = 20 * 1024 * 1024` (line 208) **per file**. The `jobs` list is built by an unbounded loop over `decoded` (lines 4277-4291) and **there is no test of `len(jobs)` or `len(decoded)` anywhere.** A hundred-document batch would be attempted in one request under one 45-second browser clock.

### B.4 Does a timeout risk a silent partial?

**No — it is clean, for a reason worth stating.** The abort happens in the browser, before any response is read, so no partial extraction ever reaches the client to be misread. On the server side, `extract_many` captures failures per job and `documents.py` **only persists results whose `ok` is `True`** (the comment at `extraction_client.py` is explicit that this is what makes "no out-of-range value reaches storage" true by construction). A document that did not extract leaves **nothing** behind. The timeout's failure mode is **under-reporting to the PM**, not corruption of the record.

### B.5 Options, since the timeout is now the plausible binding constraint

I did not choose among these; it is a policy decision with a UX cost.

- **(a) Raise `RESILIENT_TIMEOUT_MS`.** One constant, frontend only, no server change. Simplest. Cost: a genuinely hung request now hangs the PM for longer.
- **(b) Cap the batch count** in `a_projectupload` and have the client upload in chunks. Bounds worst-case wall time by construction. This is the only option that makes the 45s *sufficient* rather than *larger*. Most work.
- **(c) Lower concurrency and extract sequentially.** **Wrong direction** — it makes wall time worse, not better. Named only to be dismissed.
- **(d) Per-document-type timeout.** Not achievable: the timeout is on the batch POST, not per call. It would require (b) first.

**My recommendation, offered not taken: (b), with (a) as the immediate unblock.**

---

## C. How much of the output is payload? — the measurement that changed the answer

This was the order's most important question, and **the hypothesis behind it is false.** That is a better finding than confirming it would have been, because it closes off a change that would have risked every reader in `documents.py` for nothing.

**The instruction is general, as suspected.** The "using the table's own column headings as keys and its values as printed" wording is not confined to `procurement_items_json`. It appears verbatim across `milestones_json`, `baseline_curve_json`, `resource_profile_json`, `modifications_json`, `reference_class_json`, `lookahead_activities_json`, `schedule_network_json`, `quality_requirements_json`, `environmental_requirements_json`, `critical_quality_failures_json`, `submittal_decisions_json` and `weather_events_json` — **every register structure in the contract.** Run 122's quote generalises correctly.

**Method.** No key, so no reply could be obtained. I constructed the JSON a *correct and complete* extraction would return for the two documents named, using headings the readers actually accept — `compliance_register._HEADINGS` for the quality register, and the `_first_of` synonym tuples at `documents.py:2122-2135` for the submittal register — and counted tokens with `cl100k_base`. **This is an estimate of the extraction model's token count, not a measurement of it**, since `cl100k_base` is OpenAI's tokenizer. It is fit for purpose because the question is a **ratio between two encodings of the same data**, where tokenizer differences largely cancel, and because the margins below are far too wide for a tokenizer difference to reverse.

### The result

| Payload | Own headings | Short fixed keys | Ratio |
|---|---|---|---|
| inspection report — 26-row quality register x 9 columns | **2784 tok** | 2602 tok | **1.07x** |
| submittal register — 46-row decision table x 7 columns | **4004 tok** | 3774 tok | **1.06x** |

With the sibling scalar fields of the same reply (14 and 12 respectively), the full replies are approximately **2952** and **4148** tokens. Against the old cap of 1536 that is **1.9x and 2.7x over**.

**Sensitivity, because a single ratio is not evidence.** I re-measured the 26-row register across terse-versus-verbose cell values and compact-versus-indented JSON:

| | compact | indented |
|---|---|---|
| terse values | 1.11x | 1.09x |
| verbose values | 1.08x | 1.07x |

**The ratio is 1.07x–1.11x across the whole range. The key repetition is 7–11% of the output, not "several times the size of the data."**

**Why the hypothesis failed.** Long headings tokenize cheaply — "Requirement ID" is two or three tokens, and a short key like `req_id` is not meaningfully fewer. The saving is real but marginal.

**The decisive number.** The **most favourable case in the entire sensitivity grid** — terse values, short fixed keys, compact JSON, no sibling fields — is **1666 tokens. Still over 1536.** A key-contract change could not have rescued even the smaller of the two registers. **The cap was inadequate; the prompt is not meaningfully wasteful.**

**Therefore the key contract is untouched, as the order directed.** Every `_first_of` synonym list and every `_HEADINGS` tuple is exactly as it was. And the measurement now stands as the reason not to revisit it: the change would cost the reader-compatibility risk Run 122 documented and buy 7–11%.

---

## D. Detectability — the half of the goal that is not satisfied

The order asked what happens when a model returns a **syntactically valid but incomplete** JSON array. I traced it and then demonstrated both branches. The demonstration script lives in the scratchpad and is deliberately not committed; it introduces the fault, observes the outcome, and removes it.

### D.1 A reply cut off by the cap: DETECTED, loudly, in two places

**The authoritative test is the provider's own stop signal, and both wires implement it.** `AnthropicClient.complete` tests `stop_reason == "max_tokens"` (`ai_provider.py:318`) and `OpenAICompatClient.complete` tests `finish_reason == "length"` (`ai_provider.py:371`); each raises `ProviderTruncated`. `_WIRES` (`ai_provider.py:373`) contains **exactly these two**, so **there is no client path that lacks the test** — the owner's stated concern about a wire without it does not currently have a place to enter. `ProviderExtractor._post` converts it to `TruncatedResponseError` with the exact wording the owner quoted. **The six reported failures were refusals. Nothing partial was stored.**

The second, independent defence is `parse_json_response` -> `describe_json_truncation`, for a caller that never sees `stop_reason`. Observed on a mid-array cut of a real 26-row payload:

```
describe_json_truncation -> "the model's answer was cut off after the field 'Conformance'"
parse_json_response      -> raised TruncatedResponseError   <-- DETECTED
```

### D.2 A reply the model closed early on its own: NOT DETECTED

Observed, on 18 of 26 rows returned as well-formed JSON with the array properly closed:

```
describe_json_truncation -> None
parse_json_response      -> ACCEPTED
read_requirement_rows    -> 18 rows
   ...while the same reply carries items_inspected = 26.
control: the complete reply parses to 26 rows.
```

**Nothing notices.** `parse_json_response` is satisfied because the JSON is valid. `describe_json_truncation` is satisfied because no structure is unterminated. `extraction_merge` contains **no row-count validation of any kind** — I grepped for `len(rows)`, `row_count` and `incomplete` and there is nothing. `read_requirement_rows` (`compliance_register.py:193`) maps whatever list it is handed and returns it. A6.1 then bands on 18 rows as though 18 were the whole population.

**The sharpest form of the finding: the evidence to catch this is already in the same reply and is already extracted.** `inspection_report` asks for `items_inspected` **and** `quality_requirements_json` in the same call (`extraction_fields.py:506-517`). **Nobody compares them.** A one-line cross-check at the assembler would have caught the case above.

**As the order directed, this is reported and not fixed in this run.** It is a design decision about what a mismatch should do — refuse the document, or assemble and disclose — and Run 122's finding that "longest-register-wins discards the loser whole" means a wrong choice here is destructive. It should be its own run.

**Reassurance the owner is owed:** this failure mode is **not** what produced the six reported failures, and raising the cap does not create it. It is a latent gap that was there before this run and is there after it. Raising the cap makes an early self-close *less* likely, not more, because the model is no longer working against a budget it cannot meet.

---

## What changed

Two files. Both edited by explicit path. No check, driver or test file was added — the order's "prove a check can fail" clause is satisfied by the D.1/D.2 demonstration against existing code, which needed no new committed artefact.

**1. `server/app/extraction_client.py`** — `MAX_TOKENS` **1536 -> 8192**, with a ~30-line comment recording: where 1536 came from and that no reasoning was recorded; the measured sizes that break it; the measured rejection of the key-contract alternative; why 8192 and that `spec_apply` already proves it on this wire; the cost consequence; and that it is not in the cache key.

**The headroom I chose and why.** 8192 is **approximately twice the largest complete reply measured** (~4148 tokens, the 46-row submittal register). That accommodates a register roughly double the corpus's largest known. I chose 2x rather than a larger multiple for one reason: **the constraint that actually binds beyond here is latency against the 45s browser abort, not the cap.** A 16384 budget would not extract a document the 8192 budget cannot; it would only permit a reply so long that the browser aborts first. Sizing the cap past the point where the timeout governs would be a false comfort. **8192 is sized to the measurement; the timeout is what to fix next.**

**The cost consequence, stated honestly.** **There is essentially none.** Output tokens are billed as generated, not as budgeted — the cap is a ceiling, not a purchase. A scalar-only cost report answering in 300 tokens costs exactly what it cost yesterday. The eleven documents that already succeed are unaffected in both cost and behaviour. The real new cost is the six documents that previously produced **nothing** now producing 3000–4200 output tokens each — which is the cost of getting the data at all, and is not a comparison against a cheaper working state. The **latency** cost is the one that matters, and it is §B.

**No cached extraction is invalidated, verified not assumed.** `extraction_contract_fingerprint` (`extraction_client.py:633-648`) hashes **the prompt text and field list only**. `MAX_TOKENS` is not an input to it. I confirmed by execution that the fingerprint for `submittal_register` is unchanged after the edit. So no stored row goes stale, nothing is re-extracted, and nothing is re-billed.

**2. `server/app/simulation/models.py`** — `SIMULATION_VERSION` `sim-2026.09-v64` -> `sim-2026.09-v65`, and one appended entry in `SIMULATION_VERSION_HISTORY`, each with the reasoning. This is the **only** edit made under `server/app/simulation/`, and it was made solely to satisfy the owner's standing rule that a production-constant change must move the stamp. **The stamp moves because a result computed under v65 may rest on register evidence a v64 result could not extract at all. No band, threshold, weight, category rule, project rule or module population changed and no census figure moves.**

**Verification of the stamp move:** `tests/test_run34_version_boundary.py` — **18/18 checks passed**, including that the history is append-only, is a strict prefix of the version read out of git, and contains no duplicates. `tests/test_run34_holdout_provenance.py` fails on `ImportError: cannot import name 'portfolio_health'`, and I confirmed by `git stash` that **it fails identically at `ca1a745`** — pre-existing, unrelated to this run.

**`T6_HANDOFF.md`:** read its top block as directed. Not stale with respect to this path and **not modified** — consistent with Runs 122 and 123, neither of which appended to it. It carries no authority and nothing here rests on it.

---

## What I did not do, and why

- **Did not change the key contract.** §C measured it as a 7–11% saving that would not have fixed even the smaller register, and the order forbade it in this run regardless.
- **Did not change the 45s browser timeout.** It is a policy choice with a UX cost, and the better fix (a batch cap) is not a one-line edit. §B.5 states the options.
- **Did not add a row-count cross-check.** §D.2 reports it as directed. It needs its own run.
- **Did not add a batch-count cap.** §B.3 confirms the absence; the fix belongs with the timeout decision.
- **Did not add a migration.** None was required.

## A, B and C: all three completed. Plus D.

---

## Closing block

`git status --porcelain` **before commit** — only the intended files:

```
 M server/app/extraction_client.py
 M server/app/simulation/models.py
 A REPORT_2026-09-03_extraction_output_budget.md
```

- **Starting commit:** `ca1a745`, tree clean.
- **Migration head:** `0033_recognition_matches.py`. No migration added.
- **`SIMULATION_VERSION`:** `sim-2026.09-v65` (moved from v64; history appended; 65 stamps, all unique, current stamp last).
- **Ending commit:** the one commit named above. `git status --porcelain` after commit: **empty**.
- **Not pushed.** The owner verifies and pushes.
