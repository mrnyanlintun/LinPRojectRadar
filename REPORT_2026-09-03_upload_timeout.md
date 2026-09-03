# Run 127 — the upload timeout must fit the largest legitimate batch

`SIMULATION_VERSION` DID NOT MOVE. It stays `sim-2026.09-v66`. Justification in §7.

---

## The four numbers, first

| | |
|---|---|
| **Batch cap** | `MAX_BATCH_DOCUMENTS = 30` in `server/app/documents.py` — three waves at `DEFAULT_CONCURRENCY = 10` |
| **Single-document timeout** | `RESILIENT_TIMEOUT_MS` 45 000 → **180 000 ms** (`assets/js/store.js`) |
| **Batch timeout** | new `UPLOAD_TIMEOUT_MS` = **420 000 ms**, passed at the two `projectupload` call sites |
| **Worst-case batch wall time the cap guarantees** | **360 s** = ceil(30/10) waves × `REQUEST_TIMEOUT_S` 120 s |
| **Unknown outside the application** | Render's platform ingress/request timeout. Not in the tree, not readable from this container. If it is shorter than 420 s it becomes the binding limit. |

---

## 1. Two premises in the order were false. The code says otherwise.

The order was briefed on a model of the upload path that the code does not implement. Both
corrections change what had to be built, so they are stated before anything else.

### 1.1 The browser does NOT send one POST carrying every document

The order states: *"One POST carries every document in the upload; `a_projectupload` extracts
them all synchronously inside that single request. At `DEFAULT_CONCURRENCY = 10` a
twenty-document batch runs two sequential waves inside one 45-second clock."*

That is false for the surface `signals.js:1431` belongs to. `handleFiles`
(`assets/js/signals.js:1612`) is:

```js
for (let i = 0; i < files.length; i++) {
  const res = await processOne(id, files[i]) || …;
  …
  if (i < files.length - 1) await new Promise(r => setTimeout(r, 2500));
}
```

**One file per request, awaited in sequence, spaced 2.5 s apart.** `processOne`
(`signals.js:1499`) posts `action:"extractsignals"` with a single `dataBase64`.
`a_extractsignals` (`documents.py:4643`) is an adapter: it wraps that one document as
`documents:[entry]` and calls `a_projectupload`. So on that path the `jobs` list has length 1
(or 0 on a cache hit), `extract_many` runs one wave of one, and the 45 s clock bounded **one
model call**, never a batch.

### 1.2 `RESILIENT_TIMEOUT_MS` was not the batch clock at all

There *are* genuine batch callers of `projectupload` — `assets/js/workspace.js:646` (the
workspace period upload) and `assets/js/files.js:344` (the Files tab). Neither uses
`RESILIENT_TIMEOUT_MS`. Both go through a local `call()` helper that passed an explicit
**`60000`** to `postWithTimeout`, and `postWithTimeout` only falls back to
`RESILIENT_TIMEOUT_MS` when no `timeoutMs` argument is given.

So raising `RESILIENT_TIMEOUT_MS` alone, as the order instructed, **would have changed nothing
on the batch path.** The batch path was on a *tighter* clock (60 s for N documents) than the
single-document path (45 s for one).

### 1.3 What the real defect was

`RESILIENT_TIMEOUT_MS = 45000` sat **below the server's own bound on a single model call**,
`extraction_client.REQUEST_TIMEOUT_S = 120`. A single legitimate extraction the server was
still waiting on at 45 s was aborted in the browser with 75 s of its permitted 120 s left. The
order's causal reading of Run 124 is correct and survives the correction: raising `MAX_TOKENS`
from 1536 to 8192 made long replies the normal case for a register-bearing document, so the fix
for truncation made this abort more likely, not less. Only the *location* was misidentified.

---

## 2. Section A — what bounds this from outside the application

### A.2 verdict: the `render.yaml` header comment is STALE, and the FastAPI service does serve the traffic

The comment claims *"It serves no application traffic … `assets/js/config.js` still points at
the Apps Script endpoint."* `assets/js/config.js` says the opposite, in its own words:

```js
window.LIN_API_URL = "/exec";
/* ROLLBACK ONLY — do not enable alongside the line above:
window.LIN_API_URL = "https://script.google.com/macros/s/AKfycb…/exec";
*/
```

The Apps Script URL is a commented-out rollback line. The live value is the **relative path
`/exec`**, same-origin, and `server/app/main.py:281` defines `@app.post("/exec")`; `main.py:363`
mounts `/assets` and `main.py:375` serves `/`. One Render service serves both the frontend and
`/exec`.

**The upload POST reaches `server/app/documents.py`.** Runs 122–126 were right to treat it as
the live path; the `render.yaml` comment is the thing that is out of date. It is left in place —
correcting deployment prose was not in this run's scope — and is named here as the disagreement.

### A.1 — the second blueprint

`./backend/render.yaml` provisions a *different* service, `lin-project-radar-backend`, docker
runtime, `OPENAI_MODEL: gpt-4.1`, health check `/health`. Nothing in `assets/js` addresses it;
`config.js` names exactly one endpoint and it is `/exec`. It is a separate or dormant service
and is not on the upload path.

### A.1/A.3 — nothing in this repository bounds request duration

Established by search, not assumption:

- `render.yaml` `startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT` — **no
  `--timeout-keep-alive` and no timeout flag of any kind.**
- No `Procfile`, no gunicorn, no `WEB_CONCURRENCY`, no `proxy_read_timeout` anywhere in the
  tree. The only `Dockerfile` is `backend/Dockerfile`, belonging to the other service.
- `uvicorn[standard]==0.34.0` (`server/requirements.txt:3`). `--timeout-keep-alive` (default 5 s)
  governs how long an **idle** keep-alive connection is held open; it does not bound the
  duration of a request being served. Uvicorn imposes no request-duration limit.

**The gap, named rather than guessed:** Render's platform ingress/load-balancer request timeout
is a dashboard setting. It is not in the repository and cannot be read from this container. If
it is shorter than 420 000 ms it becomes the binding limit and the same symptom returns from a
different cause. **The owner must check it in the Render dashboard.** The safe assumption until
then is that a request longer than the platform limit is cut with a gateway error rather than
the browser's own timeout message.

`REQUEST_TIMEOUT_S = 120` at `extraction_client.py:82` was **not touched**, per the order.

---

## 3. Section B — what the worst legitimate batch costs

**B.1 — the largest register.** `extraction_fields.COUNTED_REGISTERS` and the Run 124
measurement of the 46-row submittal decision table (~4004 tokens, ~4148 with siblings) are the
figures on record. Run 126 added `register_row_counts`, a small integer map, which adds tens of
tokens, not thousands. `MAX_TOKENS = 8192` remains the hard ceiling on one reply and was not
changed.

**B.2 — how long one such extraction takes on the wire: NOT MEASURED, AND NOT ESTIMATED.**
There is no `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` or `GROQ_API_KEY` in this environment. No live
model call is possible and none was simulated. What served in a model's place throughout is
`StubExtractor`, keyed on the exact sha256 of each constructed document, which raises on an
unrecorded hash rather than inventing an extraction.

**Rather than estimate a latency, the sizing uses a bound the repository already enforces.**
`extraction_client.REQUEST_TIMEOUT_S = 120` is the timeout on the provider client
(`extraction_client.py:810`, `:1061`). No single extraction can exceed 120 s on the wire,
because the server itself will not wait longer. That is a constant read from the code, not a
figure anyone guessed.

**B.3 — waves.** `extract_many` (`extraction_client.py:1073`) sets
`workers = max(1, min(concurrency, len(jobs)))` with `concurrency = DEFAULT_CONCURRENCY = 10`.
A batch of N never-seen documents therefore runs **ceil(N/10) sequential waves**, and each
wave's wall time is that of its slowest call, bounded by 120 s. So:

```
worst-case batch wall time  =  ceil(N / 10) × 120 s
```

N here is the count of documents that are **new to the store and not reference documents** —
cache hits and specifications never enter `jobs` at all — so this is an upper bound on any real
batch of the same size.

| N | waves | guaranteed worst case |
|---|---|---|
| 10 | 1 | 120 s |
| 20 | 2 | 240 s |
| **30 (the cap)** | **3** | **360 s** |
| 40 | 4 | 480 s |
| 100 (previously permitted) | 10 | 1200 s |

---

## 4. Section C — the recurring document set, and whether the cap forces a split

**The repository does not define a recurring per-period document set.** Searched for and not
found: no "recurring" list, no once-per-project marker on any document type. What exists is:

- `extraction_fields.DOC_TYPES` — **27** analytical document types (`extraction_fields.py:42`).
- `documents._EXPECTED_DOC_TYPES` — only **four** (`pay_application`, `monthly_report`,
  `schedule_update`, `contract_value`), and explicitly *"Advisory only — this is a completeness
  HINT for the PM, never a precondition for compute"* (`documents.py:4972`).

The owner's briefed figure of **seventeen** files for PRJ-002 period 2 is a claim about a
corpus-authoring prompt and is **not verifiable from this repository**. It is reported as
unverified rather than adopted as a fact.

**Reasoning from what is in the tree:** 27 is the largest one-of-each set the analytical
vocabulary admits. `documents.py` notes that a period may legitimately hold two documents of the
same type (*"two RFI logs from different weeks are both current"*), so a cap of exactly 27 would
be too tight. **30 sits above the full vocabulary with three slots spare, and well above the
seventeen the owner described.**

**Conclusion: no client-side chunking is needed, and none was built.** A legitimate single
period fits inside the cap. The order required this to be reported before building; there was
nothing to report.

---

## 5. What changed

| File | Change | Why |
|---|---|---|
| `server/app/documents.py` | `MAX_BATCH_DOCUMENTS = 30` beside `MAX_FILE_BYTES` / `MAX_BASE64_CHARS`, and a guard in `a_projectupload` immediately after the `documents must be a non-empty list` check | Run 123 was right: there was no batch bound. The guard refuses **before any file is decoded**, so an over-large batch costs nothing. Its wording names the limit and the count in the register of the per-file refusals above it. |
| `assets/js/store.js` | `RESILIENT_TIMEOUT_MS` 45 000 → 180 000; new `UPLOAD_TIMEOUT_MS = 420 000`, exported | 180 000 = `REQUEST_TIMEOUT_S` (120 s) + 60 s headroom for transfer, decode, DB write and response — a single extraction cannot reach it by construction. 420 000 = 360 s guaranteed worst case + the same 60 s. Both carry the full derivation in a comment above the constant, including the Render gap. |
| `assets/js/workspace.js` | `call()` takes an optional `timeoutMs` (default unchanged at 60 000); the `projectupload` call site passes `LinStore.UPLOAD_TIMEOUT_MS` | Passed at the one upload call site rather than raised on the helper, so a hung *status read* stays visible in a minute instead of hiding behind an upload-sized clock. |
| `assets/js/files.js` | Same shape as `workspace.js` | Same reason. |
| `server/tools/test_run127_upload_batch_cap.py` | New check script (10 checks) with a `--revert` fault injection | Follows the Run 126 convention: a script, not a pytest module. |
| `REPORT_2026-09-03_upload_timeout.md` | This file | — |

**The refusal message, verbatim:**

> Too many documents in one upload. The maximum is 30 and 31 were sent. Please upload them in smaller batches.

**Not touched, per the order:** `REQUEST_TIMEOUT_S`, `DEFAULT_CONCURRENCY`, `MAX_TOKENS`, the
extraction prompt, anything Run 126 built. `MAX_BASE64_CHARS` and `MAX_FILE_BYTES` are unchanged.
Nothing under `server/app/simulation/` was modified.

---

## 6. Proving the checks can fail

`cd server && DATABASE_URL=sqlite+pysqlite:///<scratchpad>.db python tools/test_run127_upload_batch_cap.py`

**As shipped: 10 / 10 passed.**

```
REFUSAL -- fixture BATCH_31, one document over the cap
  ok   a batch of 31 is refused
  ok   the refusal names the limit
  ok   the refusal names how many were sent
  ok   the refused batch wrote no document_uploads row  [0 -> 0]
  ok   the refused batch wrote no upload_attempts row   [0 -> 0]

ACCEPTANCE -- fixture BATCH_30, exactly at the cap
  ok   a batch of exactly 30 is accepted
  ok   all 30 files come back  [30]
  ok   30 document_uploads rows were written  [0 -> 30]

PER-FILE GUARDS -- they must still fire inside an under-cap batch
  ok   MAX_BASE64_CHARS still refuses an oversize file (batch of 3)
  ok   an over-20MB document is refused (by the base64 guard, see the fixture note)
  ok   MAX_BASE64_CHARS shadows MAX_FILE_BYTES: the byte guard is unreachable
```

### The three required proofs

**1. One over the cap is refused; exactly at the cap is accepted.**
FIXTURE `BATCH_31` — 31 distinct one-line `monthly_report` documents, each stating only
`document_date: 2026-03-31`, each with its sha256 recorded in the `StubExtractor` override
table. FIXTURE `BATCH_30` is its first 30. 31 refused, 30 accepted with all 30 files returned.
**One document over, not ten: a check proven only on a large discrepancy is not proven.**

**2. The per-file byte guards still fire; this run did not displace them.**
FIXTURE `OVERSIZE_B64` — one document of `MAX_BASE64_CHARS + 4` base64 chars inside a batch of
**three**, comfortably under the cap, so only the per-file guard can be what refuses it. It
still refuses, with its own unchanged wording.

**3. A refused batch stores nothing — confirmed by execution, and both tables named.**
Counted directly from the database, scoped to this project's UUID, before and after the refused
POST: `document_uploads` 0 → 0 and `upload_attempts` 0 → 0. **The refusal path writes neither.**
That this is a real result and not a vacuous one is shown by the revert run below, where the
same 31-document batch writes **31 rows to each table**.

### The fault injection

`--revert` raises `MAX_BATCH_DOCUMENTS` to 10 000 at run time. All five cap checks fail; the
three checks belonging to the pre-existing per-file guards correctly keep passing, which is what
shows they are measuring something this run did not build:

```
!! --revert: MAX_BATCH_DOCUMENTS raised to 10000. Checks 2 and 3 MUST fail.
  FAIL a batch of 31 is refused  [ok=True]
  FAIL the refusal names the limit
  FAIL the refusal names how many were sent
  FAIL the refused batch wrote no document_uploads row  [0 -> 31]
  FAIL the refused batch wrote no upload_attempts row   [0 -> 31]
  ok   a batch of exactly 30 is accepted
  ok   MAX_BASE64_CHARS still refuses an oversize file (batch of 3)
5 FAILED
```

### A finding recorded rather than papered over: `MAX_FILE_BYTES` is unreachable

The first draft of check 4 asserted that a document over `MAX_FILE_BYTES` (20 MB) is refused
*by the 20 MB guard*. It **failed**, and the failure is correct. `_decode`
(`server/app/documents.py:195`) tests `len(b64) > MAX_BASE64_CHARS` **before** it decodes, and
base64 is 4/3 the size of the bytes it carries, so 5 000 000 base64 chars can never decode to
more than **3 750 000 bytes** — far below 20 971 520. Any document large enough to trip the 20 MB
guard is refused by the ~3 MB guard first.

`MAX_FILE_BYTES` is therefore dead code on this path. **This run did not introduce it and does
not repair it**: raising `MAX_BASE64_CHARS` to make the byte guard reachable would let a roughly
4× larger document through, which is a change to what the platform accepts and belongs to its
own run. The check was rewritten to assert the arithmetic that makes one guard shadow the other
— a claim that can be false, and that would become false the moment either constant moved.

### No regressions

- `tools/test_run126_register_row_count.py` — all checks passed (fingerprints unchanged).
- `tools/test_run34_version_boundary.py` — 18/18.
- `tools/test_run34_holdout_provenance.py` — known pre-existing failure
  (`ImportError: cannot import name 'portfolio_health'`), not touched by this run.

---

## 7. `SIMULATION_VERSION` did not move, and why

It stays **`sim-2026.09-v66`** at `server/app/simulation/models.py:1021`. Nothing under
`server/app/simulation/` was modified.

The stamp's stated meaning is **what a computed result rests on**. This run changed two kinds of
thing, and neither is that:

- **A browser-side clock.** How long a client waits for an answer does not change the answer.
- **A refusal on batch *shape*.** The cap decides whether a request is accepted; it does not
  alter what an accepted batch computes. The same 30 documents, uploaded as 30 or as three
  batches of 10, produce identical extractions, identical `Document` rows (identity is by
  sha256), and identical computed results.

No extraction contract fingerprint moved — confirmed by re-running Run 126's suite, which prints
them. Moving the stamp would assert a change in the basis of stored results that did not occur,
and would invite re-extraction of a corpus whose extractions are still exactly correct. **No
migration was written; none is required** — no schema, column or constraint changed.

---

## 8. What remains unknown

1. **Render's platform request/ingress timeout.** Not in the tree, not readable from this
   container. If it is under 420 s it is the binding limit on the batch path and the abort
   returns as a gateway error with a worse surface than the browser's own message. **The owner
   must check the Render dashboard.**
2. **Real per-extraction latency.** No key in this environment; never measured, and deliberately
   never estimated. The sizing rests on `REQUEST_TIMEOUT_S = 120` — a bound the server enforces
   — rather than on a figure anyone guessed.
3. **The true recurring per-period set.** Not defined anywhere in the repository. The cap of 30
   is reasoned from the 27 `DOC_TYPES` and clears the owner's unverified "seventeen" with room.
4. **Whether `backend/`'s `lin-project-radar-backend` service is live.** It is not on the upload
   path, but its relationship to the deployment was not established.
5. **`render.yaml`'s stale header comment** still claims the FastAPI service serves no traffic.
   It does. Correcting the prose was out of scope and is flagged for a future run.

---

## 9. Provenance

- **Starting commit:** `16d1a11` (= `origin/main`), `git status --porcelain` **empty**.
- **`git status --porcelain` before commit** — exactly the intended files, nothing else:

  ```
   M assets/js/files.js
   M assets/js/store.js
   M assets/js/workspace.js
   M server/app/documents.py
  ?? REPORT_2026-09-03_upload_timeout.md
  ?? server/tools/test_run127_upload_batch_cap.py
  ```
- **Migration head:** `0033_recognition_matches` (`python -m alembic current` → `0033_recognition_matches (head)`).
- **`SIMULATION_VERSION`:** `sim-2026.09-v66` — unchanged.
- **Database:** a throwaway SQLite file in the scratchpad. Production Postgres was never contacted.
- **No model call was made or simulated.** `StubExtractor` served in its place, keyed on exact sha256.
