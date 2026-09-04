# Run 130 — the spec role defaults to Groq in code

**`SIMULATION_VERSION` MOVED: `sim-2026.09-v66` → `sim-2026.09-v67`, history appended.** It moves
because a category specification application computed after this run was served by a **different
model** than one computed before it, and the stamp records what a computed result rests on. No
band, threshold, weight, category rule, project rule or module population changed; no census
figure moves. **`spec_apply.py:224` was NOT touched** — it is under `server/app/simulation/` and is
report-only, per the order. No migration; head `0033_recognition_matches.py` unchanged.

---

## The answer, at the top

* **With nothing set in the environment, `spec` now resolves to `groq` / `openai/gpt-oss-120b`.**
* **The other three roles are unmoved**, byte-identical to the starting commit: `extraction` and
  `recognition` on `anthropic/claude-sonnet-5`, `narration` on
  `anthropic/claude-haiku-4-5-20251001`.
* **The environment override still wins**, and the middle rung still sits between: proven for
  `AI_SPEC_PROVIDER`, for `AI_PROVIDER`, and for the two together.
* **`DEFAULT_PROVIDER` is untouched** at `"anthropic"`. **`temperature` is untouched.**
* **Nothing needs to be set on Render for this.** `GROQ_API_KEY` must be populated, as before.

---

## Provenance

* Starting commit `183e1d2` (= `origin/main`), tree clean.
* **No model key in this environment** — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` all
  absent. **No model call was made and none was simulated.** What served in their place: executing
  `ai_provider.load_provider()` under controlled `environ` mappings and reading what it returns.

## Establish first — the four questions

**1. Was there already a per-role default structure?** **No.** `ai_provider.py` had exactly two
rungs in code: `configured_provider()` (`AI_PROVIDER` or `DEFAULT_PROVIDER`) and the role variable
read inside `load_provider`. One rung was introduced, in the file's existing dict-driven idiom
(`PROVIDERS`, `ROLES`), not as a parallel mechanism.

**One subtlety that would have silently defeated the change**, recorded because it is the trap
here: `load_provider` read `... or configured_provider(env)`, and `configured_provider` **folds
rungs 2 and 4 together** — it never returns empty, so a role default appended after it could never
be reached. The chain in `load_provider` is now spelled out explicitly and `configured_provider` is
left alone for its own caller (`ai_provider.py:391`, the status view), where "the account-wide
switch" is still what it means.

**2. Groq's spec model.** Confirmed by execution, not carried forward:
`PROVIDERS["groq"]["models"]["spec"]` → **`openai/gpt-oss-120b`**. Present in the table. Endpoint
`https://api.groq.com/openai/v1/chat/completions`, key `GROQ_API_KEY`.

**3. Anything else assuming spec is Anthropic.**
* **`simulation/spec_apply.py:224`** — `SPEC_MODEL = ai_provider.PROVIDERS["anthropic"]["models"]["spec"]`.
  Run 129's finding confirmed: it is **not** on the call path (the call takes its model from the
  resolved `cfg` at `:325`/`:340`). **Reported, not changed** — it is under
  `server/app/simulation/`. **Proposed correction:** delete the constant if nothing reads it, or
  derive it from the resolved config rather than from a hard-coded provider key. It is now
  actively misleading: a reader will take it for the model the category call uses, and it names
  the wrong provider.
* **`tools/test_run93_provider_switch.py`** — asserted `spec` defaults to Anthropic in four
  checks. Those encode the behaviour the owner has now overruled. **Re-pointed, not weakened:**
  every property the loop checked for `spec` (provider, model, endpoint, key variable) is still
  checked for `spec`, against Groq, and **three new checks were added** for the override rungs.
  72/72 before → **75/75 after**.
* Nothing else. `drive_run113_context.py`, `run93_provider_comparison.py` and `drive_run111.py`
  reference `load_provider` without asserting spec's default.

**4. Is `temperature: 0.0` safe on Groq's wire?** **Confirmed.** `PROVIDERS["groq"]["wire"]` is
`"openai"`; `OpenAICompatClient.complete` attaches `temperature` to the body only when non-`None`
(`ai_provider.py:355-356`), and the OpenAI chat-completions contract Groq implements accepts it.
**`temperature` was not removed and must not be.** Run 129 established from `recognition.py:44-64`
that determinism comes from recording the match and replaying it, not from the sampling parameter.

## Proof — by executing the resolver

**Before (`183e1d2`) and after, nothing set:**

| role | before | after |
|---|---|---|
| extraction | `anthropic/claude-sonnet-5` | `anthropic/claude-sonnet-5` |
| **spec** | **`anthropic/claude-sonnet-5`** | **`groq/openai/gpt-oss-120b`** |
| narration | `anthropic/claude-haiku-4-5-20251001` | `anthropic/claude-haiku-4-5-20251001` |
| recognition | `anthropic/claude-sonnet-5` | `anthropic/claude-sonnet-5` |

**The chain, after:**

```
AI_SPEC_PROVIDER=anthropic                     -> spec: anthropic   (variable beats role default)
AI_PROVIDER=anthropic                          -> spec: anthropic   (middle rung still sits between)
AI_PROVIDER=anthropic + AI_SPEC_PROVIDER=groq  -> spec: groq        (variable beats AI_PROVIDER)
```

**The check can fail.** The `"spec": "groq"` entry was commented out, the resolver re-run, and the
entry restored:

```
role default removed, nothing set -> spec: anthropic     ROLE_DEFAULT_PROVIDERS == {}
restored                          -> spec: groq
```

## What changed

| File | Change | Left alone |
|---|---|---|
| `server/app/ai_provider.py` | **+33 −1.** New `ROLE_DEFAULT_PROVIDERS = {"spec": "groq"}` with the four-rung order documented above it and two executable asserts (a role default must name a real role and a real provider). `load_provider`'s chain spelled out explicitly. | `DEFAULT_PROVIDER`, `PROVIDERS`, `ROLES`, `configured_provider`, both wire clients, `temperature` handling. |
| `server/tools/test_run93_provider_switch.py` | `spec` moved out of the anthropic-default loop into its own four assertions against Groq, plus three new override assertions. 75/75. | Every other check in the file. |
| `server/app/simulation/models.py` | Stamp only: v66 → v67, one history entry, both with reasoning. | Everything else in that tree. |

## Closing

* `git status --porcelain` before commit: ` M server/app/ai_provider.py`,
  ` M server/app/simulation/models.py`, ` M server/tools/test_run93_provider_switch.py`,
  `?? REPORT_2026-09-04_spec_provider_default.md` — only the intended files.
* `test_run93_provider_switch.py` **75/75**. `test_run34_version_boundary.py` **18/18**.
* Migration head `0033_recognition_matches.py`, unchanged. No migration.
* No key printed, logged or committed. No model call made or simulated.
