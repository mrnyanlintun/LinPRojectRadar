# The naming authority, and how far the sweep got

Branch `t14-naming-authority-sweep`. **874 checks across 18 suites**, `tests_render.html` 22/22.

Part 1 is complete and on `main`. Part 2 is **one category of four complete**, stopped at a clean
boundary with context, not with the work half-applied to a file.

---

## 1. Part 1: NAMING_AUTHORITY.md

Committed verbatim at the repository root and pushed to `main` (`4fd55b7`), before any sweep work
began. No pre-existing file, so nothing was overwritten. Zero em dashes.

`T6_HANDOFF.md` now opens with a block directing every session to read it before any content work,
before the handoff itself.

The document governed the platform from outside it and failed to reach three consecutive sessions,
two of which correctly stopped rather than guessing. That failure mode is now closed.

## 2. The counts actually found, against the estimate

The estimate was "roughly 60 PCEIF occurrences". The real numbers are larger and, more importantly,
differently shaped.

| Category | Estimate | Found, user-facing | Status |
|---|---|---|---|
| 1. PCEIF and PDAF | ~60 | **90** | **Complete**, in the only sense it can be. See below |
| 2. "Cat N" and module ids | not given | **~366 across 12 files** | **Not started** |
| 3. Em dashes | not given | **76** | **Not started** |
| 4. Bare export paths | 2 | **2, confirmed bare** | **Not started** |

**PDAF appears nowhere in the repository.** The only mention is `NAMING_AUTHORITY.md` retiring it.

## 3. Category 1: what was changed, and what was deliberately not

**39 occurrences replaced**, no misses, across `knowledge.js` and `ds_defensibility_data.js`. Twelve
of those are a single repeated `assumptionsLimitations` string, so this is far fewer than 39
decisions.

**Roughly 45 occurrences remain, and leaving them is the correct outcome, not an unfinished one.**
The inventory split every user-facing occurrence into "merely naming" and "depends on the framing".
The second group cannot be fixed by replacing a word:

- **A chapter titled "The PCEIF Governance Framework"** (`ds_defensibility_data.js:3677`) whose body
  asserts the research contribution *is* a governance framework. `NAMING_AUTHORITY.md` says the
  contribution is empirical evidence and that a framework name was proposed twice and dropped.
  Renaming the chapter leaves a false claim about the research.
- **"How PCEIF Is Accredited"** (`knowledge.js:2638`) sitting over twenty `accreditationBasis`
  strings that define accreditation *as a property of the framework*. With no framework there is
  nothing being accredited, so a name swap would leave an unsupported concept with a tidier label.
- **Two mutually exclusive expansions** shipping simultaneously: "Public Capital EVM Intelligence
  Framework" (`knowledge.js` ×4) and "Probabilistic Capital-project Executive Intelligence
  Framework" (`ds_defensibility_data.js:10`). At most one was ever right, and choosing is not a
  replacement.
- **A conformance topic** stating when an implementation "conforms to PCEIF" (`knowledge.js:2685`).
- **Seven `uncertaintyMethod` strings** referring to "the course's caveat", which has no referent
  for any reader. Leftover coursework voice.

These are flagged for step 5, the judgment prose pass, exactly as the brief directs.

### Occurrences deliberately not changed, with reasons

| What | Why |
|---|---|
| `assets/visualizations/pceif_neural_signal_flow.html` (2 in title and h1) | **Verified not linked** from `index.html` or any JS. An unreachable development-era artifact, and the authority says to leave those file prefixes alone |
| Code identifiers: `PCEIF_VERSION`, `PCEIF_STATUS_LABELS`, `PCEIF_STATUS_HEX`, `svgPceifFlow()`, topic ids `"pceif"` / `"pceif-framework"` | The authority does not ask for a refactor. Renaming carries test risk for no reader benefit |
| `backend/governance.py` `PCEIFGovernanceRouter`, apps_script archive | Code identifiers in non-shipping paths |
| Developer docs: `README.md`, `SECURITY_SCAN.md`, `REPORT_*.md` | Not user-facing. `README.md` belongs to step 5 |
| `NAMING_AUTHORITY.md`, `COPY_GLOSSARY.md` | Authority documents quoting the forbidden form as an example. Explicitly correct as-is |

One item I am flagging rather than deciding: **`decision.js:422` emits `pceif_version` as a key in
the exported audit JSON.** It is a key name, so by the classification rule it is a code identifier,
but the audit export is downloaded and read by humans. Whether that counts as user-facing is your
call, not mine.

## 4. Two findings that change category 2, reported before it is attempted

Both would have made a naive sweep actively harmful.

**The new scheme leaks exactly as the old one does.** `taxonomy.js` and `categories.js` define
`num: 'A1.1'` … `num: 'D1.5'`, and `num` is not an internal key. It exists to be printed, and is
rendered at sixteen confirmed sites including `app.js:1502`, `detail.js:788`, `projectnet2d.js:374`,
`forcenet.js:95`, `export.js:114` and `decision.js:392` (which prints the literal word "Module"
followed by an id). Fixing only "Cat N" would trade one violation of the no-ids rule for another.

**The brief generator instructs the model to print ids.** `detail.js:1243` says *"List the grouped
Cat numbers inside the synthesis once."* and `detail.js:1236` says *"Do NOT mention category numbers
except when grouping them"*. Until those change, executive briefs will contain module ids no matter
how clean every static string is. That is the highest-leverage single edit in the whole inventory
and it is not a string replacement.

Also worth knowing before that category starts: `taxonomy.js` and `categories.js` are
near-duplicates carrying the same roughly 210 `num:` literals, and `deepdive.js:103` *synthesises*
`"Cat " + key` for any unmapped id, so editing its map alone will not stop the leak.

## 5. The registry exception, taken as granted

`unported_modules()` was `registry_index() - VALIDATED`. `VALIDATED` holds only single-project
modules, so all five Group D modules were counted as unported although `portfolio.py` implements
them: **six reported where exactly one is genuine.**

Corrected to subtract `PORTFOLIO_VALIDATED`. It now returns `['A4.1']`. No import cycle:
`portfolio.py` imports only from `rng`.

**Proven able to fail** before being trusted: injecting a genuinely unported module into the CSV
makes it report `['A4.1', 'A6.5']` while still correctly excluding Group D.

The two checks that had been computing the unported set themselves to work around the defect now
call the function directly, and **both were re-proven failable after that simplification**, not
merely assumed to still work.

Nothing else under `server/app/simulation/` was touched.

## 6. Found along the way, not part of the task, and important

**The Knowledge Library does not render at all.** On the running application,
`window.LIN_KNOWLEDGE`, `window.LinKnowledge` and `window.DS_DEFENSIBILITY` are **all undefined**,
and `#knowledge-root` is present but empty: zero children, zero text. Both files are in the script
list and both are fetched (324 KB and 402 KB confirmed in resource timing), but neither defines its
global.

**This predates my edits.** I verified it by stashing my changes and reloading: the unedited `HEAD`
version behaves identically. I did not diagnose the cause further, because I was near the end of my
context and chasing it would have risked leaving the sweep half-applied.

This matters for what comes next. Step 5 is scheduled to rewrite the assistant's knowledge files
and the About and Methods tabs. **A large part of that surface may currently be dead**, which
changes both the priority and the meaning of rewriting it. It also means the roughly 45 remaining
PCEIF occurrences in those two files may not presently reach any user, which is worth knowing
before anyone treats them as urgent.

I could not verify why. Stated plainly rather than argued.

## 7. Guarantees

| Guarantee | Status |
|---|---|
| `NAMING_AUTHORITY.md` committed verbatim, unedited | **Verified**, no pre-existing file, zero em dashes |
| Handoff directs future sessions to read it first | **Verified** |
| Sweep category 1 complete across every file | **Verified** for the merely-naming half. The framing-dependent half is deferred to step 5 by instruction, not left by omission |
| Actual counts reported against the estimate | **Verified**, section 2 |
| Occurrences not changed are reported with reasons | **Verified**, section 3 |
| Sweep categories 2, 3, 4 | **NOT MET.** Not started. Section 8 |
| `unported_modules()` corrected | **Verified**, and proven failable |
| Dependent checks simplified | **Verified**, and re-proven failable after simplification |
| Server suite after the sweep | **Verified**, 874 across 18 |
| `tests_render.html` after the sweep | **Verified**, 22/22 |
| Step 5 not started | **Verified** |
| Operational disclaimer untouched | **Verified** |

## 8. For the next session

**Read `NAMING_AUTHORITY.md` first. It is in the repository now.**

Remaining sweep work, in the brief's order:

1. **Category 2, "Cat N" and module ids: not started.** Roughly 366 user-facing occurrences across
   12 files. **Read section 4 of this report before starting.** The `num:` field and
   `detail.js:1243` are the two things that make a naive sweep counterproductive.
2. **Category 3, em dashes: not started.** 76 user-facing occurrences. Heaviest in `signals.js` (24),
   `admin.js` (11), `auditor.js` (7), `detail.js` (7). `index.html` and `app.js` are already clean;
   their em dashes are all comments. One trap: `detail.js:1336-1338` uses an em dash as a **parsing
   delimiter**, so changing the assistant's "Signal Pattern" output requires changing that parser
   with it.
3. **Category 4, bare export paths: not started.** Both confirmed bare. `export.js` has no test
   coverage at all. For `research_export.py`, the notice must go in the **response envelope**, not
   in `serialise()`: changing the serialised bytes changes the checksum, and every export created
   before the change would then fail verification. There is an existing `review_note` string at
   lines 279 and 449 that is the precedent for placement. **Notice wording is liability language and
   must be drafted for your review rather than adopted.**
4. **The Knowledge Library not rendering**, section 6. Worth resolving before step 5 rewrites it.
5. **`decision.js:422` `pceif_version` in the downloaded audit JSON** needs your call on whether an
   export key counts as user-facing.

## Regression

874 checks across 18 suites, all passing. Change from 873: one new check in
`test_group_assignment.py` asserting that `unported_modules()` agrees with the CSV minus what the
server registers. No other suite changed. `tests_render.html` 22/22.
