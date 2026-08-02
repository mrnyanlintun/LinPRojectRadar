# Merge, disclaimers, and two follow-ups

**901 checks across 19 suites pass. `tests_render.html` passes 26/26.** PR #196 is merged to
`main` and pushed. The approved disclaimers are live on both surfaces for both account types, and
a check now makes the live text and the reviewable source incapable of drifting apart.

---

## Part 1. PR #196 merged

Verified before merging (on the branch), then again on the merged result before pushing, because
a push to `main` deploys.

| | Branch, pre-merge | Merged `main`, pre-push |
|---|---|---|
| Server suites | 873/873, 0 failures | **873/873, 0 failures** |
| `tests_render.html` | 22/22 | **22/22** |
| Methods tab rendered and scanned | — | **51 topics, 0 failed, 0 PCEIF, 0 module ids, 0 "Cat N", 0 em dashes, 0 page errors** |

Merged as a merge commit (`2b7f561`) so the two sessions' history stays legible, then pushed.
GitHub reports PR #196 **merged and closed**.

---

## Part 2. The disclaimers are live

### What is live, and where

Both variants are quoted from `DISCLAIMERS_DRAFT.md` **verbatim**, and each appears on **two
surfaces**: the sign-in notice (a collapsed expander whose body carries the full text) and the
site footer.

| Account type | Surfaces | Variant |
|---|---|---|
| **Before sign-in**, account type unknown | sign-in notice, footer | **Research** (the restrictive text, as the fail-safe direction) |
| **Research** | sign-in notice, footer | **Research** |
| **Operational** | sign-in notice, footer | **Operational** |

### The live research text, verbatim

Shown to research accounts and before sign-in. Sign-in summary line: **Notice: academic research
instrument.**

> **Notice: academic research instrument.** Opus Gubernatio is a proof of concept developed
> solely for doctoral research and demonstration. It is not a commercial service and is provided
> as is, without warranty of any kind, express or implied.
>
> All project data is synthetic. No real project, agency, employer, contractor, or vendor is
> referenced. Do not upload confidential, proprietary, personally identifiable, or otherwise
> sensitive information, or any document relating to an actual project.
>
> Uploaded content is sent to third-party artificial intelligence services for extraction and is
> stored in research infrastructure. Analytical outputs are advisory. They are not a validated
> compliance determination, a contractual direction, or a diagnosis of a live project. The
> operator disclaims all liability arising from or relating to uploaded content to the fullest
> extent permitted by law.

### The live operational text, verbatim

Shown to operational accounts only. Sign-in summary line: **Notice.**

> **Notice.** Opus Gubernatio is provided as is, without warranty of any kind, express or
> implied.
>
> Analytical outputs are advisory. They are not a validated compliance determination, a
> contractual direction, or a diagnosis of a live project.
>
> Uploaded content is sent to third-party artificial intelligence services for extraction and is
> stored in the platform. You are responsible for confirming that you are authorized to upload
> each document, and for your organization's data handling, confidentiality, and records
> obligations. The operator disclaims all liability arising from or relating to uploaded content
> to the fullest extent permitted by law.

Both blocks above are byte-identical to sections 1 and 2 of `DISCLAIMERS_DRAFT.md` and to what
`index.html` serves. Nothing was extended, strengthened, or added.

### The unreviewed operational notice is gone

The text this replaces was the one flagged in the draft: marked in a comment as *"DRAFT. NOT YET
REVIEWED"* and *"it cannot display yet"*, while in fact `auth.js` had begun setting the
operational class from the login response, so an operational account was being shown unreviewed
liability text. That wording is now deleted from the repository, on both the sign-in notice and
the footer.

### How the live text and the source are kept from drifting

`DISCLAIMERS_DRAFT.md` is now **the source**, not a draft of one. Its header says so, records the
approval date, and states which variant is live where. The filename is unchanged because that is
how the approval refers to it.

**`server/tools/test_disclaimers.py`, 28 checks**, parses the blockquotes out of that file and
asserts the live text in `index.html` matches them character for character, after normalising
whitespace and HTML entities. It deliberately does **not** hardcode the wording: a copy of the
text inside the test would be a third copy to drift, which is the thing being prevented. It also
asserts each variant reaches both surfaces, and that the research variant's synthetic-data
sentence never appears on an operational surface.

**Proven able to fail, four independent ways** (each restored byte-identical afterwards):

| Fault injected | Result |
|---|---|
| One word changed live (`as is` to `as-is`) | 27/28, names the failing paragraph, exit 1 |
| Research text leaked onto the operational surface | 27/28, "operational surface does not claim all project data is synthetic" fails, exit 1 |
| A surface loses its notice class | 23/24, "appears on at least 2 surfaces [found 1]" fails, exit 1 |
| The **source** edited without the live text following | 26/28, both research surfaces fail, exit 1 |

The last one matters most: it means editing the approved wording without updating the site turns
the suite red, so the reviewable text cannot silently become fiction.

### Verified in a browser

| State | Research surfaces shown | Operational surfaces shown | "All project data is synthetic" visible |
|---|---|---|---|
| Pre-sign-in, no account type | **2** | 0 | yes (correct: fail-safe) |
| Operational account | 0 | **2** | **no** |
| Research account | **2** | 0 | yes |

Zero page errors. The last column is the one that matters: an operational user uploads real
project documents by design, so telling them all project data is synthetic would be false. It is
never shown to them.

### What I did NOT do, and why

Per your instruction to stop and report rather than compose:

- **The upload-panel notices in `signals.js` and `auditor.js` were left alone.** They carry the
  same `notice-research` / `notice-operational` classes but are a different, shorter surface with
  their own wording, and they are not in the approved file. Replacing them would have meant either
  dropping the approved paragraphs into a panel they were not written for, or composing shorter
  wording. Both were out of bounds. **`auditor.js`'s pair is still the clearest remaining gap
  flagged in the earlier inventory**, and it now differs in wording from the sign-in and footer
  notices, which a reader could notice.
- **The sign-in page's attribution and copyright lines were left alone.** They read "The George
  Washington University · Doctor of Engineering praxis research" and "© 2026 Nyan Lin Tun. All
  rights reserved.", which are shorter than section 3 of the approved file. Section 3 states what
  is constant **across account types**, and the footer already carries it exactly; reconciling the
  sign-in page's separate lines to it is an editorial decision that was not part of this approval.
  Recorded in the source file as still open.
- **Neither export path was touched.** Still no notice, attribution, or copyright in
  `assets/js/export.js` or `server/app/research_export.py`. Adding one means adopting liability
  wording for a new surface; the approved file flags this and explicitly does not decide it.
- **Consent text is untouched**, everywhere.

### One removal that was not in the approved draft

The footer carried a third paragraph, shown to **both** account types, with no notice class:

> Opus Gubernatio is a decision-support platform developed for Doctor of Engineering praxis
> research. Analytical outputs are advisory. They are not a validated compliance determination, a
> contractual direction, or a diagnosis of a live project.

**I removed it.** Its second and third sentences are now carried verbatim by *both* approved
variants, so keeping it printed that sentence twice in adjacent paragraphs of the same footer. Its
first sentence is descriptive rather than liability wording, and the attribution block directly
below it ("Doctor of Engineering / The School of Engineering and Applied Science of The George
Washington University") carries the same praxis context.

This is the one judgement call in Part 2 that goes beyond publishing the approved text, and it is
a **removal** rather than composition, so no unapproved wording entered the site. If you want that
line back, it belongs above the copyright, and its duplicated sentences would need trimming, which
is a wording decision for you.

---

## Part 3. The two follow-ups

### A browser assertion for `knowledge.js`

`tests_render.html` did not load `knowledge.js` at all. It now does, with four assertions:

```
knowledge.js: LIN_KNOWLEDGE is defined (the file parsed)
knowledge.js: the assistant has topics to match against
knowledge.js: the assistant has terms to define
knowledge.js: the Methods tab renderer is callable
```

Existence alone would have been too weak: a file can parse and still lose its content, and the
assistant answers by matching against `topics` and `terms`, so an empty collection is the same
failure wearing a different face. The counts are asserted non-empty.

**Proven by reproducing the original fault exactly.** I deleted a single object's opening line
from `knowledge.js`, which is precisely what commit `e34fa50` did:

```
FAULT:  removed `{ n: "A1.3", name: "Bayesian EAC", mc: "Bayesian_EAC",`
node --check: SyntaxError, Unexpected token ':'
harness:      RESULT: 22/26 checks passed
              23  LIN_KNOWLEDGE is defined ......... expected object    got undefined  FAIL
              24  assistant has topics ............. expected true      got false      FAIL
              25  assistant has terms .............. expected true      got false      FAIL
              26  Methods tab renderer callable .... expected function  got undefined  FAIL
```

Restored byte-identical; `git diff` on `knowledge.js` is empty against merged `main`, and the
harness returns 26/26.

`tests_render.html` is now **26 assertions**, up from 22.

### The stale comment in `taxonomy.js`

The header above `projectCompletionDate_` claimed the project rollup fuses *"all 11 registry
category statuses (10 project categories + Portfolio Health)"*, that *"Portfolio Health still
votes here"*, and that a conflict coefficient raises a Red-review advisory at 0.55.

**All three are false against the shipped server**, and all three had already been removed from
the Methods tab for exactly that reason. The comment was also describing work the block no longer
does at all: what follows it is the completion-date helper and the Complete promotion, not a
fusion.

Corrected to state what the block actually does, and to record why the old claims were wrong so
they are not reintroduced: the fusion is server-side; `contributes_to_project_status()` excludes
Group C and Group D, so Portfolio Health does **not** vote; and nothing writes `red_review`, so
`redReview` is always false today, with an explicit instruction not to reintroduce a browser-side
inference to fill that gap.

---

## Part 4. Two accepted states recorded

Both written into `T6_HANDOFF.md` under a heading that says plainly they are decided, not defects,
and placed **above** the session log so they are read first.

1. **The navigation presents ten categories relabelled by group while the authority document
   defines four.** Recorded as deliberate, with the reason (a rebuild, not a sweep) and an explicit
   instruction not to start it as a side effect of another task.
2. **Method thresholds appear in the module reference and not in the assistant.** Recorded as a
   **rule**, stated so a future surface can apply it without re-deciding: *numeric thresholds
   belong where a reader has navigated to method detail, and never where they arrive unbidden as
   apparent fact.* The entry also names the test a new surface should apply (is this a reference
   the reader navigated into, or an answer delivered to them) and records which two thresholds
   have actually been verified against `server/app/simulation/`.

---

## Verification summary

| Check | Result |
|---|---|
| Server suites, branch pre-merge | 873/873, 0 failures |
| `tests_render.html`, branch pre-merge | 22/22 |
| Server suites, merged `main` pre-push | 873/873, 0 failures |
| `tests_render.html`, merged `main` pre-push | 22/22 |
| Methods tab scan, merged `main` | 51 topics, 0 failed, 0 PCEIF, 0 module ids, 0 "Cat N", 0 em dashes |
| **Server suites, final** | **901/901 across 19 suites, 0 failures** |
| **`tests_render.html`, final** | **26/26** |
| Disclaimer source-vs-live check | 28/28, proven able to fail 4 ways |
| `knowledge.js` browser assertions | proven able to fail by reproducing the historical fault |
| Disclaimer rendering, 3 account states | correct variant on both surfaces in all 3; synthetic claim never shown to operational; 0 page errors |

Suite arithmetic: 873 + 28 (`test_disclaimers`) = 901 across 19 suites.
`tests_render.html`: 22 + 4 (`knowledge.js` group) = 26.

---

## Judgement calls to review

1. **The footer's `footer-praxis-notice` line was removed.** Detailed above. The one change in
   Part 2 that goes beyond publishing approved text, though it is a removal, not composition.
2. **The sign-in notice's summary line is now just the approved bold lead** ("Notice: academic
   research instrument." / "Notice."). The previous summaries carried a one-line gist that is not
   in the approved file, so keeping them would have meant retaining unapproved wording next to
   approved wording. The operational summary is now the single word "Notice.", which is thin;
   the expander cue "Full notice" still invites the reader to open it.
3. **The footer notices changed from bulleted lists to paragraphs.** The approved source is three
   prose paragraphs per variant, and bullets would have imposed a structure the wording does not
   have. Presentation change only, with a small CSS addition; no wording was altered.
4. **The upload-panel notices were left inconsistent with the sign-in and footer notices.** They
   now use different wording for the same account-type distinction. Correcting that means either
   approving the panels' existing text or approving new shorter text, both yours.
5. **`DISCLAIMERS_DRAFT.md` keeps its filename** while no longer being a draft. I judged that the
   approval refers to it by that name and that renaming would break the references in three report
   files and the handoff. Its header now states its real status. Say the word and I will rename it
   and fix the references.
6. **`test_disclaimers.py` asserts the research variant's synthetic-data sentence never appears on
   an operational surface**, singling out one sentence rather than diffing whole variants. That is
   the sentence with the clearest way to be actively false for an operational user, but it is my
   choice of what to guard most tightly.
