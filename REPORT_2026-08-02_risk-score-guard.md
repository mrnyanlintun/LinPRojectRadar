# The document risk score range guard, and PR #197 merged

**985 checks across 20 suites pass. `tests_render.html` 26/26.** PR #197 is merged and pushed.
`document_risk_score` is now refused outside 0 to 1 at every point it can enter, and there were
**three** such points, not the two the finding named.

---

## 1. The entry point the earlier finding missed

The task said to check for other assignment sites rather than assume the two in
`extraction_merge.py` were all. There is a third, and it is the most permissive of them:

**`w_overwritesignal` in `writes.py` (`overwritesignal`)** takes a caller-supplied `field` and
`value` and writes them straight into `signalInputs` with **no validation of either**. It is a
live registered action, not deferred, PM-gated but otherwise open. A PM could set `docRiskScore`
to `85` or `-3` through it and reach fusion **without a document being involved at all**, so a
guard confined to the extraction merge would have left the platform exactly as exposed as before
for anyone using that route.

The full set, all now guarded:

| # | Where | What enters | Guard |
|---|---|---|---|
| 1 | `extract_many()` in `extraction_client.py` | the raw model output, at the moment it arrives | refuses, per document |
| 2 | `_merge_one()` shared risk branch | a stored extraction on its way to fusion | refuses |
| 3 | `_merge_one()` `commissioning_report` branch | same, separate code path | refuses |
| 4 | `w_overwritesignal()` in `writes.py` | an arbitrary caller-supplied value | refuses |

Sites 2 and 3 are one file but two independent branches; a guard on the shared branch alone
leaves `commissioning_report` open, which is why the suite tests them separately.

I also confirmed `extractor.extract(...)` is called in exactly **one** place in the codebase
(`extract_many`), so site 1 is a genuine choke point rather than one of several.

## 2. Refuse, as decided

Implemented as refusal. The reasoning is recorded in the validator's docstring so it is not
re-litigated:

- **Clamping** turns `-3` into a confident `0.0`, which reads as the **best** band. Nothing
  downstream could trace that Green back to a bad input, and the project would look healthier
  than the evidence supports. A silent repair in the reassuring direction is the worst of the
  three options.
- **Store-and-flag** keeps the wrong number in the research record and depends on someone reading
  the flag. The value still reaches fusion.
- **Refusing** states what happened, when it happened, to the person who can act.

### What is refused, and what is deliberately not

Measured through the merge boundary:

| Model returns | Before | Now |
|---|---|---|
| `0` | stored `0`, Green | **stored `0`, Green** (unchanged: a genuine no-concern reading) |
| `1` | stored `1`, Red | **stored `1`, Red** (unchanged: inclusive per the prompt) |
| `0.42` | stored `0.42` | **stored `0.42`** (unchanged) |
| `85` | stored `85`, **pinned Red** | **REFUSED** |
| `"85%"` | stored `85.0`, **pinned Red** | **REFUSED** |
| `-3` | stored `-3`, **read GREEN** | **REFUSED** |
| `1.0001` / `-0.0001` | stored, misbanded | **REFUSED** |
| `None` / absent | not stored | unchanged |
| `"1.2.3"` (unparseable) | not stored | unchanged |
| `"N/A"` | stored `0.0` | **unchanged, deliberately** |

**`"N/A"` is left alone and this is a judgement call.** `_num_or_null` coerces any unparseable
string to `0.0` by a documented legacy quirk reproducing `Number("")` in JavaScript. That lands
in range, so the guard does not fire. Changing it would alter behaviour the instrument has always
had, on a different axis from the range contract, and that is a separate decision. It is flagged
at the end.

## 3. The refusal is visible, on a surface that already exists

No new user-facing surface was built, and none was needed.

`extract_many` already converts any exception from an extractor into the per-file
`{ok: False, error: ...}` shape, and the frontend already renders that verbatim in an
**"Extraction failed"** dialog with a "Try again" button
(`signals.js`: `<p class="ds-modal-err">${esc(opts.error || "Unknown error")}</p>`). Raising at
the extraction boundary therefore reaches the uploader through machinery that was already there.

Because `documents.py` only writes a `Document` row for results whose `ok` is true, a refusal
leaves **nothing behind to clean up**. That is what makes "no out-of-range value reaches storage"
true rather than merely checked later.

The exact text the uploader sees:

> document_risk_score in pay_app_07.pdf is 85, which is outside the required range 0.0 to 1.0
> inclusive. It is a risk rating on a 0 to 1 scale, not a percentage and not a count. Nothing was
> stored for this document and no figures from it were used. Re-run the extraction, or supply the
> document again, and if it keeps happening the extraction model is returning the wrong scale for
> this document type.

**This is composed operational text and I am flagging it rather than assuming it was in scope.**
It is not liability or consent language, it is on an existing error channel, and it is in the same
register as the messages already there ("refusing to invent an extraction"). The feature cannot
work without some wording, so leaving it undrafted would have meant shipping a silent or generic
failure, which the task explicitly ruled out. If you want it worded differently it is one string
in `validate_doc_risk_score` and the suite asserts its content, not its phrasing, except for four
substrings (the value, the filename, the range, and the word "percentage").

The `overwritesignal` path returns the same sentence through `err(...)`, since `/exec` callers
read `error` rather than catching exceptions.

## 4. Tests, and proof they can fail

New suite **`server/tools/test_doc_risk_range.py`, 66 checks**, covering all four guard sites,
both boundary values, the negative case, the percentage case in numeric and string form, the
just-over and just-under cases, and the absent/unparseable cases that must pass through.

**One vacuous test was caught and fixed during writing, which is worth recording.** The
`overwritesignal` checks initially passed for the wrong reason: `w_overwritesignal` returns
"No extracted signals to overwrite" on an empty `signalInputs`, and that refusal happens
**before** the range guard. Every out-of-range check was green on a freshly created project while
proving nothing, and would have stayed green with the guard deleted. The suite now seeds
`signalInputs` first, with a comment saying why, and reads the stored value back independently
rather than trusting the refusal's own response.

Each guard proven load-bearing by deleting it and observing the suite go red:

| Fault injected | Result |
|---|---|
| Guard removed at the extraction boundary | 58/66, exit 1 |
| Guard removed on the shared merge branch | 59/66, exit 1 |
| Guard removed on the `commissioning_report` branch | 62/66, exit 1 |
| Guard removed on `overwritesignal` | 57/66, exit 1 |
| Range widened to 0..100 (accepting a percentage) | 34/66, exit 1 |
| Restored | **66/66, exit 0** |

Five independent faults, five distinct failure signatures. No single guard's removal is masked by
another's presence.

## 5. Already-stored out-of-range values: none found, and nothing was altered

**I did not migrate or alter any stored data.**

Scanned every database reachable from this session: the dev-server SQLite store and all twenty
per-suite throwaway databases. **Zero `document` rows carry an out-of-range
`document_risk_score`.** The stores holding documents at all (`test_documents_b7b` 13 rows,
`test_workspace_t3t5` 2, `test_decision_ui_t4` 1) are all in range.

**Production Postgres was not inspected and must not be**, per the standing rule; no Postgres
`DATABASE_URL` exists in this environment and I did not create one. So the honest statement is:
**no out-of-range values exist in anything reachable from here, and the production store is
unexamined.**

### What would happen to one if it existed

This matters, because the guard changes the behaviour of a project that already holds a bad row:

- The `Document` row itself stays. Nothing deletes it.
- The next `assemble_signal_inputs` for a period containing it **raises**, so
  `_compute_and_store` fails and **that project cannot compute again until the document is
  removed**.
- The failure is loud and names the value, which is the intended behaviour, but it is a hard stop
  rather than a degraded result.

That is the correct consequence of choosing refusal over clamping, and it is worth knowing before
the first real document run. If the production store turns out to hold such a row, the project it
belongs to will stop computing the moment this deploys. Checking that is a query you can run
against production; I have not.

## 6. Verification

| Check | Result |
|---|---|
| Server suite, branch pre-merge (PR #197) | 919/919 across 19 suites, 0 failures |
| `tests_render.html`, pre-merge | 26/26 |
| Server suite, merged `main` pre-push (PR #197) | 919/919, 0 failures |
| `tests_render.html`, merged `main` | 26/26 |
| **Server suite, with the guard** | **985/985 across 20 suites, 0 failures** |
| **`tests_render.html`, with the guard** | **26/26** |
| New suite proven able to fail | 5 independent faults, each distinct |

Suite arithmetic: 919 + 66 (`test_doc_risk_range`) = 985 across 20 suites.

No existing suite changed behaviour, which is the evidence that the guard refuses only what it
should: `test_documents_b7b` (66 checks, 13 stored documents) and `test_workspace_t3t5` still pass
untouched.

## 7. Step 6 remains blocked

Unchanged by this session and **not something I can clear**. Real extraction needs a real project
document and a live `ANTHROPIC_API_KEY` in the same place. Neither is reachable from a local
session: the container holds no real documents, the three files in `server/dev_fixtures/` are the
stub in file form, and `render.yaml` marks the key `sync: false` so it exists only in the Render
dashboard.

**The unblocking run is yours to do**: one real document through the deployed platform, where the
key already is.

This guard makes that run safer rather than substituting for it. If the model returns a percentage
on your first real document, the platform will now say so by name instead of quietly pinning the
project Red, which is a considerably better first result than the one that was possible yesterday.

---

## Judgement calls to review

1. **I composed the refusal wording.** It is operational error text on an existing channel, not
   liability or consent language, and the feature cannot function without some message. Flagged
   because the task asked me to draft rather than compose if new user-facing wording was needed.
   Reworded easily: it is one string, and the suite asserts four substrings rather than the whole
   sentence.
2. **`"N/A"` still becomes `0.0` and is not refused.** It is in range, so the range guard is not
   the right place to address it, and it is a documented legacy coercion the instrument has always
   had. Refusing it would be a second behaviour change bundled into this one.
3. **The merge boundary raises, which can hard-stop a project.** A project holding an
   already-stored bad row will fail to compute rather than compute without that document. That is
   refusal applied consistently, but it is a stronger consequence than refusing at upload alone,
   and I could have guarded only the entry point and left merge permissive. I judged that "no
   out-of-range value reaches computation by any path" required both.
4. **`overwritesignal` is guarded for `docRiskScore` only**, not turned into a general validation
   layer. Every other `signalInputs` field would need its own contract decided first, and
   inventing range rules for `cpi` or `bac` on my own judgement is exactly the kind of quiet
   assumption this codebase keeps having to undo.
5. **The extraction-boundary guard sits in `extract_many` rather than in each extractor.** One
   choke point covers the real and stub extractors alike and cannot be missed when a third
   extractor is added; the cost is that a caller invoking `extractor.extract()` directly would
   bypass it. No such caller exists today, and the suite would not catch one appearing.
6. **`extraction_client` imports from `extraction_merge` inside the function.** It keeps the
   module-level dependency direction clean and follows the pattern `documents.py` already uses for
   the simulation package, but it is a lazy import and those are easy to overlook when reading.
