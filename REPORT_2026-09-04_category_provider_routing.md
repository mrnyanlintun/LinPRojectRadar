# Run 129 — the category call routes to the wrong provider

**`SIMULATION_VERSION` DID NOT MOVE.** It stands at `sim-2026.09-v66`. **No production code changed.**
Nothing under `server/app/simulation/` was opened for edit. The only file this run commits is this
report. No migration; migration head `0033_recognition_matches.py` unchanged.

---

## The answer, at the top

* **Which role the category call uses:** **`spec`**. `simulation/spec_apply.py:325` and `:340` both
  call `ai_provider.load_provider("spec")`.
* **Why it resolved to Anthropic:** the order's **cause 1/2** — `AI_SPEC_PROVIDER` is unset, so it
  falls through to `AI_PROVIDER`, which is either unset or set to `anthropic`; that falls through to
  `DEFAULT_PROVIDER = "anthropic"` (`ai_provider.py:137`). The category path **does** consult role
  resolution — cause 3 is excluded, by execution.
* **Configuration or code:** **CONFIGURATION. No code change is warranted and none was made.**
* **What to set on Render:** on the `opus-gubernatio-server` web service, Environment tab:

  ```
  AI_SPEC_PROVIDER = groq
  ```

  `GROQ_API_KEY` must also be set (`ai_provider.PROVIDERS["groq"]["key_env"]`). Setting
  `AI_SPEC_PROVIDER` alone moves **only** the category call; extraction, narration and recognition
  stay on Anthropic. That is the narrower and safer change. Setting `AI_PROVIDER = groq` instead
  moves **all four roles** — including extraction, which Runs 124 and 126 depend on.

* **`temperature` stays. Nothing is given up.** The routing fix alone unblocks the work.

---

## Provenance

* Starting commit `7e6f046` (= `origin/main`), tree clean.
* No model key in this environment: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` all absent.
  **No model call was made and none was simulated.** What served in their place: executing
  `ai_provider.load_provider()` directly under controlled `os.environ` values and reading what it
  returns. A resolution is provable that way without a live call, exactly as the order allows.

---

## A. Which role the category call uses

Traced from the Process button to the client:

| Step | Location |
|---|---|
| Category apply entry | `simulation/spec_apply.py:325`, `:340` |
| Role resolution | `ai_provider.load_provider("spec")` |
| Client build | `ai_provider.build_client(cfg, timeout_s=REQUEST_TIMEOUT_S)` |
| Request | `client.complete([...], max_tokens=MAX_TOKENS, temperature=0.0)` — `spec_apply.py:255` |

**Role: `spec`.** `ROLES = ("extraction", "spec", "narration", "recognition")` (`ai_provider.py:60`)
— Run 123's list is confirmed exhaustive and the category path is inside it, not beside it.

**Override variable: `AI_SPEC_PROVIDER`.** Resolution chain (`ai_provider.py:200-216`):

```
AI_SPEC_PROVIDER  ->  AI_PROVIDER  ->  DEFAULT_PROVIDER ("anthropic", line 137)
```

One dead end worth naming: `spec_apply.py:224` holds
`SPEC_MODEL = ai_provider.PROVIDERS["anthropic"]["models"]["spec"]` — a hard-coded Anthropic
reference. It is **not** on the call path (the call takes its model from the resolved `cfg`), but it
is a latent trap for a future reader and is recorded here rather than edited.

## B. Why it resolved to Anthropic — proven by execution

`load_provider` run for all four roles under three environments:

```
nothing set            -> extraction=anthropic/claude-sonnet-5   spec=anthropic/claude-sonnet-5
                          narration=anthropic/claude-haiku-4-5-20251001  recognition=anthropic/claude-sonnet-5
AI_PROVIDER=groq       -> extraction=groq/openai/gpt-oss-120b    spec=groq/openai/gpt-oss-120b
                          narration=groq/openai/gpt-oss-20b      recognition=groq/openai/gpt-oss-120b
AI_SPEC_PROVIDER=groq  -> extraction=anthropic/claude-sonnet-5   spec=groq/openai/gpt-oss-120b
                          narration=anthropic/claude-haiku-4-5-20251001  recognition=anthropic/claude-sonnet-5
```

The first line reproduces the observed failure. The third is the fix, and demonstrates proof
obligation 3: **the other three roles are unmoved.**

**What is on Render cannot be read from this container.** Whether `AI_PROVIDER` is unset or
explicitly `anthropic` is not distinguishable from here and does not change the remedy. Named as a
gap rather than guessed.

## C. Which roles send `temperature`

Not shared — a per-call-site literal:

| Role | Sends? | Value | Where |
|---|---|---|---|
| **spec** | **yes** | `0.0` | `simulation/spec_apply.py:255` |
| **recognition** | **yes** | `TEMPERATURE = 0.0` | `recognition.py:121`, sent at `:476` |
| extraction | **no** | — | no `temperature` anywhere in `extraction_client.py` |
| narration | **no** | — | — |

Both wires attach it only when non-`None` (`ai_provider.py:309-310` anthropic, `:355-356` openai).

**The research-record question, and it is not a bug.** `temperature=0.0` is deliberate.
`recognition.py:44-64` argues at length that `temperature=0` "narrows the distribution; it does not
make one", and that determinism is obtained by **recording the match and replaying it**, not by
sampling settings. So the platform's determinism guarantee does **not** rest on `temperature` —
which is why nothing is lost here. **`temperature` was not removed and must not be**: on Anthropic
the parameter is now refused, and that is a fact to record about Anthropic, not a reason to strip a
deliberate setting from every provider.

## D. What Groq accepts

`ai_provider.PROVIDERS["groq"]` (`ai_provider.py:122-134`):

| Field | Value |
|---|---|
| wire | **`openai`** — the OpenAI-compatible client, as Run 123 recorded |
| base_url | `https://api.groq.com/openai/v1` |
| path | `/chat/completions` |
| key_env | `GROQ_API_KEY` |
| model for **spec** | **`openai/gpt-oss-120b`** — present in the table, resolves cleanly |

The openai wire **does** send `temperature` (`ai_provider.py:355-356`), and the OpenAI chat
completions contract Groq implements accepts it. **So the routing fix alone unblocks the work with
`temperature` left exactly as it is.** Whether Groq honours `0.0` as strict determinism is a
provider behaviour not testable here without a key; it is not required, per §C.

## What was NOT done, and why

* **No code change.** The order forbids working around a configuration setting in code, and the
  resolver is behaving exactly as designed.
* **`DEFAULT_PROVIDER` untouched.** Changing it would fix this path and move the problem to the
  other three.
* **`temperature` untouched.** §C.
* **`SPEC_MODEL` at `spec_apply.py:224` untouched** — a hard-coded Anthropic model string off the
  call path. Flagged, not edited; it is under `server/app/simulation/`.
* **`T6_HANDOFF.md` untouched.** Stale (newest section Run 89) but its header forbids rewriting, and
  every run since 90 has left it.

## Closing

* Starting commit `7e6f046`; ending commit is the one carrying this file. Tree clean after.
* `git status --porcelain` before commit: `?? REPORT_2026-09-04_category_provider_routing.md` — only.
* Migration head `0033_recognition_matches.py`, unchanged. No migration.
* `SIMULATION_VERSION` `sim-2026.09-v66`, unchanged.
* No key printed, logged or committed. No model call made or simulated.
