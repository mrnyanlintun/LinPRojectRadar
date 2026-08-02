# Notice and copyright revision, 2026-08-02

The approved copyright paragraph and the approved university sentence are live on every surface
that carried any part of the old text. The source of the wording is `DISCLAIMERS_DRAFT.md`
section 3, and `server/tools/test_disclaimers.py` now fails if the live text diverges from it by a
character, in both directions, on all six surfaces that carry it.

Suites: **1057/1057 server checks across 21 suites**, `tests.html` 51/51, `tests_render.html`
33/33. Every surface confirmed in a browser for both account types. Nothing under
`server/app/simulation/` was touched.

---

## 1. What is live now, quoted verbatim from the rendered page

Read out of a real browser with Playwright against the served `index.html`, not out of the source
file, so this is what a user sees.

### Footer, copyright. Constant in both account types

> © 2026 Nyan Lin Tun. All rights reserved. Opus Gubernatio and the associated software and
> documentation are the intellectual property of the author. Unauthorized reproduction,
> distribution, or use is prohibited.

### Footer, attribution. Constant in both account types

> Developed as part of doctoral research at the School of Engineering and Applied Science, The
> George Washington University. The university is not a party to this notice and does not endorse
> or warrant the platform.

### Sign-in box, attribution

> Developed as part of doctoral research at the School of Engineering and Applied Science, The
> George Washington University. The university is not a party to this notice and does not endorse
> or warrant the platform.

### Sign-in box, copyright. Unchanged, still the short form

> © 2026 Nyan Lin Tun. All rights reserved.

Left as it was, per the task: this revision changed the wording each surface carries, not which
surfaces carry the full copyright paragraph.

### Access-denied panel, attribution

> Developed as part of doctoral research at the School of Engineering and Applied Science, The
> George Washington University. The university is not a party to this notice and does not endorse
> or warrant the platform.

### The four developer-facing pages

`calibration/verify.html`, `tools/export_lib.html`, `tests.html`,
`assets/visualizations/pceif_neural_signal_flow.html` each now close with two sentences, both
quoted verbatim from the approved text and neither composed:

> Analytical outputs are advisory. They are not a validated compliance determination, a
> contractual direction, or a diagnosis of a live project.
>
> Developed as part of doctoral research at the School of Engineering and Applied Science, The
> George Washington University. The university is not a party to this notice and does not endorse
> or warrant the platform.

### The notice bodies, unchanged

Verified in the browser that exactly one of the two variants is visible per account type, on the
footer and on the upload panels, with the copyright and attribution constant across both.

Research account, and before sign-in (the default, because restrictive text is the fail-safe
direction):

> **Notice: academic research instrument.** Opus Gubernatio is a proof of concept developed solely
> for doctoral research and demonstration. It is not a commercial service and is provided as is,
> without warranty of any kind, express or implied.
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

Operational account:

> **Notice.** Opus Gubernatio is provided as is, without warranty of any kind, express or implied.
>
> Analytical outputs are advisory. They are not a validated compliance determination, a
> contractual direction, or a diagnosis of a live project.
>
> Uploaded content is sent to third-party artificial intelligence services for extraction and is
> stored in the platform. You are responsible for confirming that you are authorized to upload
> each document, and for your organization's data handling, confidentiality, and records
> obligations. The operator disclaims all liability arising from or relating to uploaded content
> to the fullest extent permitted by law.

---

## 2. ONE JUDGEMENT CALL, PLEASE CONFIRM IT

**The research variant was not replaced by the approved text, and I believe that is what you
meant.**

The approved block contains three notice paragraphs. Those three paragraphs are, character for
character, the existing **operational** variant. They are not the research variant. Read one way,
"replace the notice text everywhere it appears" would mean the research variant is deleted and
research accounts get the operational notice instead. That would remove "All project data is
synthetic", "No real project, agency, employer, contractor, or vendor is referenced", and "Do not
upload confidential, proprietary, personally identifiable, or otherwise sensitive information, or
any document relating to an actual project" from every surface a participant sees.

I did not do that, for four reasons.

1. Your "what changed and why" section enumerates three changes. All three are to the copyright
   and the attribution. None is to a notice body.
2. Your sign-in instruction says this task "changes the notice and the attribution, not what each
   surface includes".
3. The two variants exist precisely because the research statements would be false for an
   operational user and the restrictive statements are the ones a participant needs. Collapsing
   them one way deletes participant-facing restrictions.
4. Removing liability language is composing liability language. Both `NAMING_AUTHORITY.md` and
   your own instruction forbid a session doing that on its own judgement.

So: copyright and attribution changed everywhere; the two notice bodies are untouched and still
switch on `account_type`. **If you did intend the research variant to be retired, say so and it is
a five-line change** — but it is your call, not mine.

---

## 3. Every surface found, with its old text quoted

Nine surfaces carried some part of the text, in **six** distinct wordings. You had seen two.

### Changed

| # | Surface | Old text | New |
|---|---|---|---|
| 1 | `index.html:1082` `.footer-copyright` | `© 2026 Nyan Lin Tun. All rights reserved. Opus Gubernatio™ and the associated framework, software, and documentation are the intellectual property of the author. Unauthorized reproduction, distribution, or use is prohibited.` | approved copyright |
| 2 | `index.html:1093` `.footer-praxis` | `Doctor of Engineering<br>The School of Engineering and Applied Science of The George Washington University` | approved attribution |
| 3 | `index.html:344` sign-in `.login-footnote` | `The George Washington University · Doctor of Engineering praxis research` | approved attribution |
| 4 | `index.html:361` access-denied `.login-footnote` | `GWU Doctor of Engineering Praxis, Nyan Lin Tun` | approved attribution |
| 5 | `calibration/verify.html:166` | `Opus Gubernatio is a decision-support platform developed for Doctor of Engineering praxis research at The George Washington University. Analytical outputs are advisory and do not constitute a validated compliance determination.` | approved advisory + attribution |
| 6 | `tools/export_lib.html:210` | same sentence, verbatim | same |
| 7 | `tests.html:284` | same sentence, verbatim | same |
| 8 | `assets/visualizations/pceif_neural_signal_flow.html:711` | same sentence, verbatim | same |
| 9 | `DISCLAIMERS_DRAFT.md` section 3 | the two blockquotes above | rewritten, with a "do not reintroduce" note |

**Surface 4 is a variant you had not seen and has the identical defect** you described: a bare
comma-separated attribution sitting directly beneath the line `Access restricted to authorized
use. This platform is an academic proof-of-concept; no warranty is provided.` It reads as a
signature block on a liability statement, in the shortest form yet.

**Surfaces 5 to 8 are a fourth variant you had not seen**, four identical copies of one sentence
that fused the attribution and the advisory statement. They are developer-facing (a calibration
harness, an export-library preview, the signal-math harness, a static visualization), so no
participant reaches them, but the sentence was invented locally and matched no approved text. Each
now carries two approved sentences instead. **No new wording was composed for them**: both
sentences are quoted from the approved block.

### Found and deliberately not changed

- **`index.html:347`, sign-in copyright**: `© 2026 Nyan Lin Tun. All rights reserved.` Left per
  your instruction that the sign-in box does not carry the copyright paragraph.
- **`index.html:360`, access-denied notice**: `Access restricted to authorized use. This platform
  is an academic proof-of-concept; no warranty is provided.` **This is a third notice variant**,
  short, not derived from either approved variant, and never approved. Changing it means composing
  or selecting liability wording, which you told me not to do. **Flagged for your decision.** Note
  that it does not switch on account type: an operational user who fails sign-in is told the
  platform is an academic proof of concept.
- **`README.md:5`**: `Project Decision Support. Built for a Doctor of Engineering praxis by Nyan
  Lin Tun at The George Washington University.` This is the only thing README carries — **it has
  no copyright line and no notice at all.** The sentence is repository prose, not a notice, and it
  does not sit under a liability disclaimer, so it does not have the defect you described. Left
  alone. Say the word if you want it aligned.
- **`index.html:29`, the `<meta name="description">`**: `Opus Gubernatio: project decision support
  for public AEC capital programs. Doctor of Engineering praxis research, The George Washington
  University.` Not a notice, but it is the text search engines and link previews show, and it
  asserts the domain scope (`public AEC capital programs`) that `NAMING_AUTHORITY.md` section 3
  deliberately keeps out of the standing description. **Flagged, not changed.**
- **`server/app/geocode.py:62`**: the Nominatim `User-Agent` string carries
  `Doctor of Engineering praxis research, The George Washington University`. Machine-facing,
  required by Nominatim's policy to identify the operator, not user-facing. Left alone.
- **`index.html:866-867`, About page Version table**: `Institution | The George Washington
  University` and `Program | Doctor of Engineering, Engineering Management`. Table rows of fact,
  not an attribution under a disclaimer. Left alone.
- **`index.html:877`, About page Research context**: `Opus Gubernatio was built for a Doctor of
  Engineering praxis by Nyan Lin Tun at The George Washington University.` Prose, not a notice.
  Left alone.

### The export paths still carry nothing

`assets/js/export.js` and `server/app/research_export.py` carry **no notice, no attribution and no
copyright**, exactly as `DISCLAIMERS_DRAFT.md` already flagged. I confirmed this rather than
assuming it. Adding one would be composing the decision, not applying it, so it is unchanged and
still open. This is the artifact most likely to leave the platform and be read by someone who
never saw a footer.

---

## 4. The "framework" sweep

The word survives in 40-odd places. Almost all are legitimate: `No framework` describing the
absence of a JavaScript library, and `mathematical framework` / `evidence framework` describing
Dempster-Shafer, rough sets, linear programming and so on in `knowledge.js`. Those are the
ordinary English word and assert nothing about this platform.

**Fixed, one clear assertion:** the footer copyright's `the associated framework`. That was the
only place in participant-facing text asserting a proprietary framework exists.

**Correct already, and worth knowing they are:** `index.html:785` says in prose "There is
deliberately no named framework here", `knowledge.js:76` and `knowledge.js:2611` both say "There is
deliberately no named framework", and `README.md:81` says the same.

### Flagged, needs your judgement

- **`assets/js/ds_defensibility_data.js`, three strings.** `"Grounds the framework in earned value
  management and its limits..."`, `"Design Science Research: the framework and instrument are built
  as artifacts and evaluated through structured practitioner validation..."`, and `"Twelve or more
  professionals ... evaluate the framework qualitatively; their feedback drives framework
  refinement and defines the boundary of claims."` These assert a framework exists and is being
  evaluated. `NAMING_AUTHORITY.md` already records this file as stale and written around the
  retired PCEIF framing, and the same file's own lead string correctly ends "not a new governance
  framework", so it contradicts itself. **This is research-methodology prose about your praxis
  design, not platform copy. Rewriting it is your call, not a session's.**
- **The `Methods and Framework` tab label**, at `index.html:763`, `app.js:2273`, and as the
  eyebrow on seven `knowledge.js` topics. It names a section rather than claiming a proprietary
  framework, so it is defensible as it stands, but it is the most prominent surviving use of the
  word and a reader can take it either way. **Renaming it touches a navigation label in three
  files and eight strings, so I left it.**
- **`deepdive.js:1808`** carries `Cat 6.1` and `Cat 7.1–7.9`, which is a module-id violation of
  `NAMING_AUTHORITY.md` section 4, not a framework issue. Out of scope here, noted so it is not
  lost.

---

## 5. The check

`server/tools/test_disclaimers.py` went from 62 checks to 90. It already asserted that the two
notice variants match their source character for character. It now also asserts:

- Section 3 of the source parses into exactly two blockquotes, one attribution and one copyright.
- The attribution states the university is not a party to the notice, and does not endorse or
  warrant the platform. These are asserted against the source, so weakening the source is a red
  suite too.
- The copyright contains no `framework` and no trademark symbol.
- The footer carries both, verbatim, and each appears exactly once.
- At least two `.login-footnote` surfaces carry the attribution sentence, which is the sign-in box
  and the access-denied panel.
- All four developer-facing pages carry it verbatim.
- **Four retired strings appear on no live surface**: `Opus Gubernatio™`, `the associated
  framework`, the middot sign-in line, and the old title-block attribution.

**Both new check families were proven able to fail, then restored.** The retired-string check
caught a genuine violation on its first run: a comment I had just written in `index.html`
explaining the change quoted `"the associated framework"` verbatim. The source-vs-live check was
then failed deliberately by shortening the footer attribution to "The university does not endorse
the platform.", which produced `RESULT: 89/90` and the failing line, and passed again once
restored.

---

## 6. Verification

**Server suite, 1057/1057 across 21 suites.** Every suite was run against its own freshly migrated
throwaway SQLite database in the scratchpad. Production Postgres was never configured, contacted,
or inspected.

A note for whoever runs these next, because it cost time here: **six suites fail if they share one
database**, with `UNIQUE constraint failed: action_families.action`, `pseudonymous_code already in
use: T3T5-PM`, and `duplicate column name: secret_side_channel`. Those are fixture collisions
between suites, not defects. All six pass on a fresh database. Nothing to do with this change, but
worth knowing before someone chases it.

**Browser harnesses:** `tests.html` 51/51, `tests_render.html` 33/33, no page errors.

**Surfaces, confirmed in headless Chromium against the served page**, with the account-type switch
toggled both ways: exactly one notice variant visible per account type on the footer and on the
upload panels; the copyright and attribution visible and identical in both states; the sign-in box
and the access-denied panel each carrying the approved attribution sentence. The quoted text in
section 1 above is the browser's rendered text, not the file's.
