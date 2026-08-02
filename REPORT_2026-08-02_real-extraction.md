# Step 6: real extraction. STOPPED, and why.

**Parts 1 through 4 were not attempted. There is no real project document available in this
environment, and the extraction path could not run against one even if there were.** Per the
dependency clause, I stopped rather than substituting a synthetic document or proceeding against
the stub.

The disclaimer wording gap, which does not depend on the document, is done. 919 checks across 19
suites pass; `tests_render.html` 26/26.

---

## 1. The blocker, with evidence

Three independent facts. Any one of them alone would stop the task.

### 1.1 There is no real project document in this environment

The repository contains **zero** PDF, DOCX, XLSX, DOC or XLS files. The only documents present are
three files in `server/dev_fixtures/`, and those are **the stub in file form**, not documents:
`dev_serve.py` writes them itself at startup from hardcoded numbers, and their sha256 hashes are
the StubExtractor's recording keys.

```
DEV_CASES = { "healthy": (5_250_000, 5_000_000, 5_000_000), ... }
_raw = _doc(f"MONTHLY REPORT {_name.upper()}", _ev, _ac, _pv)
DEV_RECORDINGS[hashlib.sha256(_raw).hexdigest()] = ("monthly_report", {...})
(SERVER_DIR / "dev_fixtures" / f"monthly_report_{_name}.txt").write_bytes(_raw)
```

Using one of those would be running the stub against its own recording, which is precisely the
circular verification this task exists to break.

This session runs in a remote Linux container against a fresh clone. The repository on your
machine is under OneDrive; any real project documents on that disk are not present here by
construction.

### 1.2 The extraction path cannot run, because there is no `ANTHROPIC_API_KEY`

Not asserted from reading the code. Measured:

```
build_extractor()                -> StubExtractor  | model_id: stub/recorded-v1
build_extractor(require_real=True) -> ExtractionError: "ANTHROPIC_API_KEY is not set. Refusing
                                      to extract with the stub in an environment that requires
                                      real extraction."
extract(<any unrecorded bytes>)  -> ExtractionError: "stub extractor has no recording for
                                      sha256 294e8a5164c5...; refusing to invent an extraction."
```

This is decisive on its own and **independent of document availability**. Handed a real document
today, the actual extraction path in this environment would refuse it rather than call a model.
The only way to get output would be to record the document into the stub first, which is a
harness imitating extraction, explicitly out of bounds.

No key exists anywhere reachable: not in the environment, not in a `.env` (only
`backend/.env.example`), and `render.yaml` marks it `sync: false`, meaning it is set in the Render
dashboard and deliberately never in a tracked file. That is the correct design; it just means real
extraction cannot be exercised from here.

### 1.3 The Google Drive connector cannot be reached

The one remaining avenue to a real document. Both `search_files` and `list_recent_files` return
`MCP error -32003: MCP tool call requires approval`, which cannot be granted in a non-interactive
session.

### What would unblock this

Any one of these, in rough order of least effort:

1. **Run it where the key already is.** Render has `ANTHROPIC_API_KEY` set. A single upload of one
   real document through the deployed platform, with the resulting stored extraction shared as
   redacted field names and values, is the whole of Part 1.
2. **Attach a real document to a session that also has the key**, so extraction runs locally.
3. **Approve the Drive connector** in an interactive session, if a suitable document is there.

The report you actually want is field-by-field agreement between a model's output and a document a
human can read. None of that is available from here, and no amount of local work substitutes.

---

## 2. What I could establish without running extraction

These are **code-read and unit-measured findings, not observations of real model output**. They
say what the platform does with a given extraction. They say nothing about what a model actually
returns on a real document, which is the open question.

### 2.1 The `document_risk_score` contract is unguarded, and the failure is silent

The task flagged this. It is real, and worse than the note suggests. I measured the merge path
directly (this exercises the merge contract with chosen values; it is **not** a stand-in for
extraction):

| Model returns | Stored `docRiskScore` | Band |
|---|---|---|
| `0.15` (compliant) | `0.15` | Green |
| `0.85` (compliant) | `0.85` | Red |
| **`85` (percentage)** | **`85`** | **Red** |
| **`"85%"` (string)** | **`85.0`** | **Red** |
| `"N/A"` | `0.0` | Green |
| **`-3` (nonsense)** | **`-3`** | **Green** |

There is **no range validation anywhere on the server**. `_num_or_null` coerces and returns; the
merge branch does `acc.set_field("docRiskScore", risk)` with no check. `extraction_merge.py`
documents this as deliberate, on the grounds that rescaling would diverge from the instrument
being reproduced. That reasoning is sound for rescaling and does not extend to **detecting**.

Two things sharpen the risk:

- **The only guard is a sentence in the prompt.** `build_prompt` says `document_risk_score` "is a
  number between 0 and 1 inclusive... never a count and never a percentage". Prompt compliance is
  not a contract, and this is exactly the field with no schema enforcement behind it.
- **The negative case is worse than the percentage case.** A percentage pins every project to Red,
  which is loud and someone notices. A negative or out-of-range-low value reads as **Green**, the
  safest-looking band, and nothing anywhere would surface it.

**No test asserts this field stays in range.** I searched; there is none.

I did not fix it. A range check is a behaviour change on the research-critical path, it needs a
decision about what to do when the contract is violated (refuse the document, clamp, or store and
flag), and refusing versus clamping is a research-data decision, not an editing one.

### 2.2 Things I explicitly could not establish

Everything Parts 1 through 3 actually asked for:

- Whether the model locates fields correctly in a real document's layout.
- Which document structures it does not handle: multi-column pay applications, scanned pages,
  tables split across pages, continuation sheets.
- Whether it confuses adjacent columns, which is the classic earned-value extraction failure
  (this-period versus to-date).
- Whether it returns null honestly for absent fields, or fills them.
- Whether `document_risk_score` in practice comes back on the 0 to 1 scale the prompt asks for.
- Whether the computed result is **right** rather than merely produced.

---

## 3. Part 4: the wording question

**This run justifies no change to `NAMING_AUTHORITY.md`, and I have not touched it.**

The standing description says "reads the reported figures" rather than "extracts the figures"
precisely because extraction had never run against a real document. That is still true. Nothing in
this session moved that fact by a single step: extraction did not run, because it could not.

Worth stating plainly, because it is the trap this wording exists to avoid: a successful run would
not by itself justify the stronger wording either. "Extracts the figures" is a claim about
reliability across real document structures, not about one document parsing correctly. One
successful extraction would justify "has been run against a real project document", which is a
different and much weaker sentence. The evidence that would support the stronger claim is several
documents of different types, with field-by-field agreement measured against what a human reads in
them, and the failures counted rather than the successes.

---

## 4. The disclaimer wording gap: closed

This did not depend on the document, so it is done.

### What was wrong

Four upload panels (`signals.js` x2, `auditor.js` x2) carried liability wording that matched
**neither the approved notice nor each other**. The two files' operational variants differed from
one another in wording, and both differed from the approved text. They were a surface the original
approval did not cover.

### What is live now

All four panels render the **approved wording from `DISCLAIMERS_DRAFT.md`, verbatim**, the same
text the sign-in notice and the footer carry. No new liability language was composed; both
variants are used in full, all three paragraphs each, since every paragraph is apt at an upload
surface.

The text now comes from **one shared constant**, `assets/js/disclaimers.js`. Four copies of
approved legal text across two files is the shape that drifts, and it demonstrably had. The
sign-in notice and the footer deliberately do **not** use it: they stay static HTML in
`index.html`, so a liability notice never depends on JavaScript having loaded. The upload panels
are built as HTML strings at render time and cannot be static, which is why they get a constant
rather than markup.

Verified in a browser: three paragraphs per variant, correct bold leads, no literal
`${LinDisclaimers...}` placeholder shipped, and **"All project data is synthetic" absent from the
operational variant**, which is the sentence that must never reach a user uploading real project
documents by design.

### The check now covers them

`test_disclaimers.py` grew from 28 to **46 checks**. New coverage:

- The shared constant matches the approved source paragraph by paragraph.
- Each panel file renders the shared notice and **carries no literal notice of its own**, so a
  future edit cannot quietly reintroduce divergent wording.
- **Each call site is inside a template literal.** `${...}` in an ordinary quoted string is valid
  syntax that ships to the user as the characters `${LinDisclaimers.uploadNoticeHtml()}`.
  `node --check` accepts both, so the delimiter is asserted rather than assumed.
- `disclaimers.js` loads **before** the files that use it.

Proven able to fail four ways, each restored afterwards:

| Fault | Result |
|---|---|
| Shared constant drifts from the source | 45/46, names the paragraph, exit 1 |
| A panel reintroduces its own literal notice | 44/45, exit 1 |
| Call site moved out of a template literal | 44/46, both sites named, exit 1 |
| Script load order broken | 44/46, exit 1 |

### Nothing needed that the approved file lacks

The approved variants covered this surface without composition. Both were used whole.

---

## 5. Verification

| Check | Result |
|---|---|
| Server suite | **919 checks across 19 suites, 0 failures** |
| `test_disclaimers` | 28 → **46**, proven able to fail 4 new ways |
| `tests_render.html` | **26/26** |
| Upload panels in a browser | 3 paragraphs per variant, correct leads, no placeholder leak, synthetic claim absent from operational, 0 page errors |
| Extraction path | **could not run**, see section 1 |

Suite arithmetic: 873 + 46 (`test_disclaimers`, was 28) = 919.

Nothing derived from any real document was committed, because no real document was reached.

---

## 6. For the next session

**The extraction verification is still entirely open.** Do not treat this report as partial
progress toward it; treat it as a statement that it has not begun. The prerequisite is a real
document plus a live key in the same place, and section 1.4 lists the three ways to get there.

**Take the `document_risk_score` finding with you.** It is a genuine unguarded contract with a
silent failure mode in the safe-looking direction, and it needs a decision (refuse, clamp, or
store and flag) before a range check can be written.

**A caution about what a first successful run proves.** It will be tempting to read one clean
extraction as licence to strengthen the standing description. Section 3 sets out why that does not
follow.

---

## Judgement calls to review

1. **I stopped Parts 1 through 4 entirely rather than doing a reduced version.** I could have
   recorded a document into the stub and exercised the merge and compute path with realistic
   shapes. That is a harness imitating extraction, which the task ruled out, and it would have
   produced a report that looked like evidence and was not.
2. **I completed the disclaimer work despite stopping the extraction task.** The "stop" clause is
   scoped to the extraction dependency, and the disclaimer item is introduced separately and is
   fully independent. If you meant the whole session to halt, that work is on its own branch and
   is easy to drop.
3. **I measured the `document_risk_score` contract with chosen values through the merge path.**
   This is a unit-level demonstration of the storage contract, not extraction against a
   substituted document, and I judged it inside the boundary. It converts a code-read claim into a
   measured one. If you consider any synthetic value out of bounds for this session, the finding
   still stands on the code alone.
4. **The upload panels now carry all three approved paragraphs** rather than a selected subset.
   Selecting which sentences of an approved notice appear on a surface is itself a liability
   decision, so I used both variants whole. The panels are consequently much longer than the one
   line they replaced.
5. **The upload panels' text now depends on JavaScript**, via the shared constant. Those panels
   are entirely JS-rendered already, so this adds no new dependency, but it is a different
   robustness posture from the sign-in and footer notices, which are deliberately static.
6. **I did not fix the unguarded range contract**, per the instruction to report rather than
   repair. It is not small and obviously correct: it needs a policy decision first.
