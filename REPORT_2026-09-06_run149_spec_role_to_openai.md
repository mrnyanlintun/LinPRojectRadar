# Run 149 — what serves the spec role, and can it serve from OpenAI

## State plainly, at the top

**What to set on Render:**

```
AI_SPEC_PROVIDER = openai
```

**Set that one variable and nothing else. Do NOT set `AI_PROVIDER`** — see the warning below, it
is the most important thing in this report.

**Was a code change needed? No.** OpenAI already carries a `spec` entry, `gpt-4o`. The environment
change is the whole fix. **Nothing was built, and this run commits only this report.**

**Is OpenAI likely to hit the same Cloudflare refusal? Possibly — the transport is identical.**
Both wires inherit **one** request method using the standard library with no user agent set, so
OpenAI is presented with the same client fingerprint that Groq's edge refused. Whether OpenAI's
edge applies the same rule is **unproven from here** and cannot be established without a live call.
**The switch is worth making — it is free and reversible — but it may not be sufficient.**

**`SIMULATION_VERSION` does not move.** Nothing under `server/app/` was touched. No migration.

---

## ★ The warning: `AI_PROVIDER` would move all five roles

The order asks for both rungs to be measured, and the measurement produced a result worth acting
on. **`AI_SPEC_PROVIDER` moves the spec role alone. `AI_PROVIDER` moves everything.**

| rung | spec | extraction | narration | recognition | mitigation |
|---|---|---|---|---|---|
| nothing set | **groq** `openai/gpt-oss-120b` | anthropic `claude-sonnet-5` | anthropic `claude-haiku-4-5-20251001` | anthropic `claude-sonnet-5` | anthropic `claude-opus-5` |
| **`AI_SPEC_PROVIDER=openai`** | **openai** `gpt-4o` | anthropic, unchanged | anthropic, unchanged | anthropic, unchanged | **anthropic `claude-opus-5`, unchanged** |
| `AI_PROVIDER=openai` | openai `gpt-4o` | **openai** `gpt-4o` | **openai** `gpt-4o-mini` | **openai** `gpt-4o` | **openai `gpt-4o`** |
| both set | openai `gpt-4o` | **openai** `gpt-4o` | **openai** `gpt-4o-mini` | **openai** `gpt-4o` | **openai `gpt-4o`** |

**Setting the account-wide variable would silently take the mitigation role off Opus**, which the
owner chose deliberately at Run 140 and which Run 144's rulings rest on. It would also move
extraction and recognition off Sonnet. **The role variable is the correct instrument and the
account variable is a trap here.**

## The four resolution rungs, executed

Executed, not read, as Run 130 did. Endpoint and key variable for the spec role:

| environment | provider | model | endpoint | key variable |
|---|---|---|---|---|
| nothing set | groq | `openai/gpt-oss-120b` | `https://api.groq.com/openai/v1/chat/completions` | `GROQ_API_KEY` |
| `AI_SPEC_PROVIDER=openai` | **openai** | **`gpt-4o`** | `https://api.openai.com/v1/chat/completions` | `OPENAI_API_KEY` |
| `AI_PROVIDER=openai` | openai | `gpt-4o` | same | `OPENAI_API_KEY` |
| both set | openai | `gpt-4o` | same | `OPENAI_API_KEY` |

The first row is exactly the deployment's present state — no role variable, no account variable, so
the spec role falls through to the code default and reaches Groq, which the edge is refusing. That
matches the reported error string, provider and model identifier.

## Whether OpenAI carries a spec entry — it does

**`PROVIDERS["openai"]["models"]["spec"] = "gpt-4o"`.** It already existed; nothing was added and no
model name was invented.

That answers the question the order says decides the run: **the environment change alone works, and
would not crash.**

**I proved the finding is load-bearing rather than asserting it.** Removing the entry in memory and
resolving the role again raises `KeyError: 'spec'` — the immediate crash Run 130 warned of, not a
fallback. Restored, it resolves to openai `gpt-4o` again. So had the entry been missing, setting the
variable would have replaced a 403 with a crash.

The entry sits beside the other OpenAI identifiers, which the table already marks as **unverified
against the catalogue** — they came from a keyless session and were deliberately left alone rather
than changed on a guess. That marking still stands and applies to this one.

## Whether OpenAI will be refused too — the transport is shared

**One request method serves every provider.** Both client classes inherit a single `_request` that
builds a plain standard-library request and opens it with the standard library's own opener. The
per-class difference is only the headers each attaches — an authorization header and a content
type, plus Anthropic's version header. **No user agent is set anywhere**, so the library supplies
its own.

The provider table confirms the wire sharing directly: **Groq and OpenAI both ride the `openai`
wire**, differing only in base URL and key. Anthropic uses its own wire shape, but the **same
transport underneath**.

**So the fingerprint Run 141 identified is presented identically to OpenAI.** If OpenAI's edge
applies the same browser-integrity rule, the same refusal follows. **Whether it does is not
established** — that needs a live call, which cannot be made here and must not be simulated.

**Not fixed, as instructed.** A user agent addresses only the header half of a fingerprint and the
owner has not asked for it.

## The five proofs

| # | proof | result |
|---|---|---|
| 1 | all four rungs, executed | **PASS** — table above |
| 2 | the other four roles byte-identical before and after | **PASS, trivially and stated as such: no code changed at all**, so nothing could move. Measured under every rung anyway; under the role variable all four are unchanged from the nothing-set baseline |
| 3 | with the role variable the spec role resolves to OpenAI with a real model string, and without it is unchanged | **PASS** — `openai`/`gpt-4o` with it, `groq`/`openai/gpt-oss-120b` without |
| 4 | prove the check can fail | **PASS, twice.** An invalid provider name raises `ProviderConfigError` naming the three valid providers rather than silently defaulting. And removing the spec entry raises `KeyError: 'spec'`, then restores |
| 5 | no key present | **Confirmed: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` and `GROQ_API_KEY` are all absent from this container.** What served in their place: the resolver itself, executed under controlled environments. A resolution is provable without a live call. **No live call was made and none was simulated.** No key was printed, logged or committed — only the variable *names* were checked for presence |

## What moved

**Nothing in the code.** `DEFAULT_PROVIDER` untouched, no other role moved, the mitigation role Run
140 added untouched, nothing under `server/app/simulation/`, no migration. This run commits **only
this report**.

## If the switch does not clear it

If the specification panel still fails after setting the variable, the error string itself
distinguishes the cases, because the platform formats it as provider, model, status and body:

- **`openai (gpt-4o) returned 403: error code: 1010`** — the same Cloudflare fingerprint rejection
  at a different edge. That settles the transport question, and the next step is the transport
  change this run deliberately did not make.
- **A 401 or 403 with an OpenAI error body** — a key or entitlement problem, not a fingerprint.
- **A 404 on the model** — `gpt-4o` is not available to that account, and the identifier needs
  checking against the catalogue with the command the provider table already documents.

Reverting is one variable: remove `AI_SPEC_PROVIDER` and the spec role falls back to the code
default exactly as it does today, which rung one measures.
