# 2026-08-02 — Four notice items, and unported_modules corrected

All five parts done. Server 1338 checks across 23 suites, `tests_render.html` 49/49,
`tests.html` 51/51, all green on merged `main`. 21 faults injected, every one detected, every one
reverted and rechecked byte-for-byte.

One thing needs your decision and is not implemented: **the CSV export still carries no notice.**
Section 2 explains why and gives you the three options.

---

## Part 1. The access-denied panel notice is removed

`index.html:360` carried:

> Access restricted to authorized use. This platform is an academic proof-of-concept; no warranty
> is provided.

Gone, not replaced. In its place is a comment saying why, so the next session does not helpfully
put an approved variant there instead.

The panel keeps the section 3 attribution sentence, which is approved for that surface and which
`DISCLAIMERS_DRAFT.md` records as being placed there deliberately on 2026-08-02. Removing the
liability line and keeping the attribution is the whole change.

DOM read, panel forced visible the way `auth.js` shows it:

```
Sign-in Not Accepted
This platform is restricted to authorized users only.
Back to sign-in
Developed as part of doctoral research at the School of Engineering and Applied Science,
The George Washington University. The university is not a party to this notice and does not
endorse or warrant the platform.
```

No `.login-disclaimer` element remains in the panel, and no approved variant was substituted.

---

## Part 2. The export paths

### The XLSX export: done

`assets/js/export.js` now builds a **Notice** sheet, and it is the **first** sheet, so it is what
opens. It carries the account-appropriate advisory text, the attribution, and the copyright.

The text is not written in `export.js`. It comes from `window.LinDisclaimers`, which already held
the two approved variants checked character-for-character against `DISCLAIMERS_DRAFT.md`. The
attribution and copyright were added to that same constant rather than to the export, so there is
still exactly one copy of each approved sentence reachable from JavaScript. A check asserts
`export.js` does not restate any of it.

It switches on account type the way every other surface does, reading the same
`body.og-account-operational` signal the CSS switch keys on. **The research variant is the
default**, because a file written before the server has resolved the caller must carry the
restrictive text, not the permissive one. Verified in the DOM:

| body class | first paragraph of the Notice sheet |
|---|---|
| (none, the default) | `Notice: academic research instrument. Opus Gubernatio is a proof of co...` |
| `og-account-operational` | `Notice. Opus Gubernatio is provided as is, without warranty of any kin...` |

### The research export, JSON: done

`server/app/research_export.py` adds `notice`, `attribution` and `copyright` to the JSON body,
quoted verbatim.

**It does not switch on account type, and that is deliberate.** `build_rows()` filters on
`participant.account_type != "research"` and skips everything else, unconditionally, on every
export including refetches of exports taken before that filter existed. An operational account's
rows cannot be in this file. Writing a switch would mean writing an operational branch that is
unreachable by construction, which asserts that an operational research export exists. It does
not. So the research variant is the only correct text.

That reasoning depends entirely on the filter staying there, so `test_export.py` now asserts the
exact guard statement is present exactly once. If the filter is ever relaxed, the notice becomes
wrong and the suite says so.

### The research export, CSV: NOT done, and this is your decision

**A CSV cannot carry the approved text.** RFC 4180 has no comment syntax. Anything above the
header row *is* the header row: `csv.DictReader` would return the first sentence of the notice as
a field name, and `test_export.py` asserts `list(reader[0].keys()) == EXPORT_COLUMNS` precisely
because that contract matters.

The alternatives I considered and rejected rather than shipping on my own judgement:

- **A leading `#` comment block.** Readable by pandas and R with a flag, and it silently breaks
  every existing reader that does not pass one, including this repository's own suite.
- **The notice repeated in an extra column on every row.** Six hundred characters duplicated per
  row is not a notice, and it corrupts the data shape the export exists to provide.
- **A shortened form that fits.** This is composing a new liability variant.
  `DISCLAIMERS_DRAFT.md` is explicit: a surface carries the approved sentence whole or does not
  carry it.

So the gap is reported rather than papered over, and it is asserted rather than left to be
rediscovered: a check confirms the CSV still carries no notice and that nothing was prepended
above its header. If someone later makes it carry one, that check fails and gets updated
deliberately.

**Your three options**, none of which I took:

1. Offer JSON only for exports that leave the study team, and keep CSV as an internal convenience.
2. Accept the leading comment block and update the readers, this suite included.
3. Ship a sidecar `NOTICE.txt` alongside the CSV.

Every fetch response now says which case it is, via `notice_in_payload`, so this is visible when
the file is taken rather than discovered afterwards.

### A regression this nearly caused, and how it is handled

`a_adminexportcreate` stores `checksum(serialise(rows, fmt))`, and `a_adminexportfetch`
re-serialises and compares. **Adding the notice changes those bytes.** Every export record created
before this change would have failed that comparison and been withheld with the message "The
underlying data has changed since this export was taken."

That message would have been false. The data would be exactly what it always was, and telling a
researcher their archived export is corrupt when it is not is the opposite of the guarantee the
checksum exists to provide.

So a mismatch is now checked a second time against the pre-notice serialisation. If that matches,
the rows are provably unchanged, the record simply predates the notice, and it is served with
`predates_notice: true` and both digests. A record matching neither is still refused and audited,
which is checked by a fault that makes the legacy path accept anything.

If you would rather not carry that compatibility branch, the alternative is a migration that
records a payload version per export. I did not add a schema change for this.

---

## Part 3. The meta description

Before:

> Opus Gubernatio: project decision support for public AEC capital programs. Doctor of Engineering
> praxis research, The George Washington University.

After, the short-form standing description from `NAMING_AUTHORITY.md`, quoted verbatim:

> Opus Gubernatio analyses the documents a project produces each reporting period and presents a
> recommendation that a project manager records a decision against, keeping the evidence, the
> recommendation, and the judgment as one reproducible record.

The check parses the short form out of `NAMING_AUTHORITY.md` rather than holding a copy, for the
same reason `source_variants()` parses the disclaimer source: a copy in a test file is a copy that
can drift. It also asserts the description contains none of AEC, capital program, capital project,
public sector.

The praxis attribution tail was dropped rather than shortened. `DISCLAIMERS_DRAFT.md` retired the
middot form, and the approved replacement is a full sentence that does not belong in a meta tag.
A surface carries it whole or not at all.

**Left alone, and worth flagging.** `ds_defensibility_data.js` still describes the *research* as
concerning "public AEC capital programs" in its lead and its Introduction chapter. That is a claim
about the doctoral work, not about the platform's scope, and the authority's constraint is on the
standing description. If you want the domain claim gone everywhere and not just where the platform
is described, that is a separate pass and I did not take it.

---

## Part 4. The framework strings

The lead of `praxisOutline` already said the contribution is empirical evidence "not a new
governance framework". Three chapter descriptions below it contradicted that:

| | before | after |
|---|---|---|
| Literature | "Grounds **the framework** in earned value management..." | "Grounds **the research** in..." |
| Methodology | "**the framework and instrument** are built as artifacts" | "**the platform** is built as an artifact" |
| Validation | "evaluate **the framework** qualitatively; their feedback drives **framework refinement**" | "evaluate **the platform** qualitatively; their feedback drives **its refinement**" |

No description needed inserting; these needed a correct noun, not a definition. The authority's
instruction, "describe what it does instead", is satisfied by naming the actual thing: the
research, the platform.

Nine occurrences of the word remain in the file and all are correct. Eight cite **Sargent's
simulation V&V framework** and one **the course's error framework**: other people's frameworks,
which the platform is entitled to cite. The ninth is the lead denying it has one. The check
forbids the bare definite article ("the framework", "this framework", "our framework", "framework
refinement") which catches an own-framework claim while leaving possessive citations alone.

### The "Methods and Framework" tab label

Three files carry it. One thing about it was obvious from the authority and I changed it; the
other is not, and I did not.

**Changed.** `app.js:2287` spelled it `Methods & Framework` while `index.html:763` spelled it
`Methods and Framework`. Same label, two spellings, and the authority is explicit: "User-facing
text uses 'and', not the ampersand the code constants use." `knowledge.js` already used "and". A
stale HTML comment in `index.html` also used the ampersand and now matches.

**Not changed, and referred to you.** Whether the word **Framework** belongs in the label at all.
The argument for removing it: a tab called "Framework" implies the platform has one, and the
authority says it deliberately does not. The argument for keeping it: the tab's content includes
`governanceAxis`, which maps the platform against NIST AI RMF, explainable AI principles, AI
management and risk standards, and model cards. Those are real external frameworks, and "Methods
and Framework" reads naturally as "our methods, and the frameworks we are accountable to".

The authority does not settle it. It forbids a framework *name* and forbids asserting the
contribution *is* a new governance framework; a generic section heading is neither. So I left it,
per the brief. If you want it changed, "Methods and Standards" would preserve the external-framework
sense without implying an internal one, and it touches four files.

---

## Part 5. unported_modules()

### What was on the branch, and what was actually missing

`t15-local-unpushed` at `9dc137d` is **28 commits behind** `origin/main`, not ahead of it. Merging
it would have deleted roughly 11,500 lines, including twenty report files, the geocoding provider
work, and the disclaimers infrastructure. I did not merge it.

Checking its five commits against origin one at a time:

| On the branch | Already on origin? |
|---|---|
| `dffb68f` the PCEIF sweep of `knowledge.js` / `ds_defensibility_data.js` | **Superseded.** origin has **0** occurrences in `ds_defensibility_data.js` and 9 in `knowledge.js`; the branch has 34 and 31. Origin's sweep went further. |
| `73e6392` CUSUM abstention | **Superseded.** origin's `run_cusum` already abstains and additionally wires `spiHistory` from `documents.py`, which the branch version does not. |
| `ced295c`, `55662e4` | Reports and handoff only. |
| `dffb68f` the `unported_modules()` fix | **Genuinely absent.** The only substantive code on that branch not on origin. |

Your characterisation was right, and it is now verified rather than assumed. The branch is
untouched and can be deleted whenever you like; nothing on it is needed.

### The fix

```python
return sorted(set(registry_index()) - set(VALIDATED) - set(PORTFOLIO_VALIDATED))
```

`VALIDATED` holds only the single-project modules, so the five Group D modules were reported
unported although `portfolio.py` implements them: it answered **6** where exactly **1** is genuine.
It now answers `['A4.1']`. No import cycle: `portfolio.py` imports only from `rng`.

### The workarounds are gone

Two checks computed the unported set themselves to route around the defect. Both now call the
function directly, which is the only way they can notice it regressing.

`test_simulation.py` also gained a partition check, that the registry equals validated plus
portfolio-validated plus unported with nothing left over and nothing counted twice. It earns its
place: it is what catches over-subtraction, which the equality check alone reads as merely a
shorter list.

`test_group_assignment.py` still asks the question a second way, from the CSV minus the two
registries, because a check that only consults the function cannot tell a correct function from a
broken one that agrees with itself. The two routes are independent.

### Proven able to fail

| Fault | Result |
|---|---|
| Restore the original defect (stop subtracting `PORTFOLIO_VALIDATED`) | both suites red; reports `['A4.1', 'D1.1'...'D1.5']` |
| Declare a genuinely unported module in the CSV (`A6.99`) | both suites red; reports `['A4.1', 'A6.99']`, **still excluding Group D** |
| Over-subtract so the unported list empties | both suites red, including the partition check |

The middle one is the case the brief asked for, and the Group D exclusion holding while a new
unported module is detected is the part that matters.

---

## Verification

### Fault injection: 21 faults, all detected, all reverted and rechecked

Every fault asserts its search text occurs **exactly once** before patching, asserts the same of
the injected text before reverting, and is followed by a **byte comparison against a pristine
snapshot plus a re-run confirming the suites return to baseline**. Not once at the end. After
every single fault.

That discipline earned its keep four times in this session:

1. **A deletion fault reverted with an empty needle**, which matches at every position. The
   harness aborted rather than corrupting the file, but the abort happened mid-revert and left
   `index.html` missing its attribution paragraph. The next run's **baseline** came back 144/146
   instead of 146/146, which is how it was caught and repaired. Without the baseline re-check
   every subsequent result would have been measured against a damaged file.
2. **A multi-line search written with `\n` against a CRLF file** matched nothing. Reported as
   "found 0" instead of silently patching something adjacent.
3. **A search string that appeared twice** in `index.html`. Refused rather than picking one.
4. **The working tree moved underneath the campaign.** See the parallel-session note below.

### Three checks that passed for the wrong reason, found by injection

These are the point of the exercise, and all three were mine:

- **`unported_modules()[0]` unguarded.** Over-subtracting emptied the list and `test_simulation.py`
  died with an `IndexError`: **no `RESULT:` line at all**, which reads exactly like a clean run.
  An empty list is now a red check.
- **`old_f["payload"]` on a refused fetch.** Same failure shape, `KeyError`, no `RESULT:` line.
  All payload reads now go through a helper that returns empty rather than raising.
- **The account-type guard check matched my own comment.** I searched for
  `participant.account_type != "research"`, and the comment I had just written in
  `research_export.py` explaining the filter quotes that expression. Deleting the actual guard left
  the check green. It now matches the whole `if` statement and asserts it appears exactly once.

A fourth was weak rather than wrong: the "Notice sheet is first" check compared where the variable
names appear in the source, a proxy for sheet order. A fault moved the sheet without moving the
declaration and the check stayed green. It now compares the order of the `book_append_sheet` calls,
which is what actually decides which sheet opens.

### Suites

- **Server: 23 suites, 1338 checks, 0 failures.** That figure includes the parallel session's
  work as well as mine; an earlier run of 1329 was taken before their commits had fully landed.
- **`tests_render.html` 49/49** and **`tests.html` 51/51**, in a real browser.
- Every changed surface confirmed by DOM read. There is no compositing in this container, so there
  is no screenshot and none is claimed.

The four suites I touched: `test_disclaimers.py` 146 (+25 checks, sections 12 to 17),
`test_export.py` 77 (+13, guarantee 8), `test_simulation.py` 29 (+5, -4 replaced),
`test_group_assignment.py` 18 (+2, -1 replaced).

The DB-backed suites need a migrated database and `SESSION_SECRET`, and are **not idempotent**:
run twice against one database the second run dies without a `RESULT:` line. The harness rebuilds
from a clean `alembic upgrade head` snapshot before every run. Never pointed at production.

---

## The parallel session

An admin and membership session was working in the same tree throughout. **I stayed out of the
admin page and out of `writes.py`;** I did not need either.

We share one working directory, which is worth recording because it is not obvious. Mid-campaign
my byte comparison reported `assets/js/app.js` had changed underneath it, and the file contained a
live `title="FAULT"` injection plus a Signals-button change that were not mine. That is the
harness working: it refused to measure results against a file being edited by someone else.

They have since committed (`be1c0f4`, `45eeaac`, `2bd7dd5`) and `app.js` now carries only my
one-line change. I confirmed their commit did **not** sweep up my uncommitted edits: the retired
panel notice and the old meta description are both still in `HEAD`, and my three `index.html`
hunks are additions on top.

`tests_render.html` is now 49/49 rather than the 43/43 of earlier today. Those six extra checks are
theirs, not mine.

---

## Repository state

`origin/main` was `0cf063c` and in sync with local when I started, with a clean working tree. It
moved to `2bd7dd5` during the work, via their two commits and a merge that brought in `757ee4b`
from the admin and membership branch. Everything above was re-verified on that merged state before
committing.

## Files changed

- `index.html` — the panel notice removed, the meta description replaced, one stale comment.
- `assets/js/export.js` — the Notice sheet, first in the workbook.
- `assets/js/disclaimers.js` — attribution and copyright added to the shared constant, plus
  `currentNotice()`.
- `assets/js/ds_defensibility_data.js` — three framework assertions corrected.
- `assets/js/app.js` — one label, ampersand to "and".
- `server/app/research_export.py` — the approved notice, the CSV gap made explicit, the
  pre-notice checksum path.
- `server/app/simulation/registry.py` — `unported_modules()`, the one permitted change under that
  directory.
- `server/tools/test_disclaimers.py`, `test_export.py`, `test_simulation.py`,
  `test_group_assignment.py` — the checks above.

## Flagged for you, not decided by me

- **The CSV export notice.** Three options in Part 2. Nothing shipped.
- **The word "Framework" in the tab label.** Part 4. Not obvious from the authority, so not
  changed.
- **The domain claim in `ds_defensibility_data.js`'s research framing.** Part 3. Out of scope for
  the meta description, left as it was.
- **The pre-notice checksum compatibility branch.** Removable if you would rather have a migration,
  or if no exports predate today.

No liability or consent wording was composed anywhere in this work. Every notice sentence that now
appears in an export is quoted verbatim from `DISCLAIMERS_DRAFT.md`, and a check fails if any of
them drifts from it by a single character.
