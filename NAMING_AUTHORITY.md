# Naming Authority and Current State

Read this before writing, reviewing, or reasoning about anything user-facing on this platform.

## 1. The name situation

The codebase contains **PCEIF** in roughly 60 places, a chapter titled "The PCEIF Governance
Framework", and `ds_defensibility_data.js` written around that framing.

Those are stale. **PCEIF is retired. So is PDAF.** The code has not caught up with a
research-direction change.

Do not use either name in anything you write, and do not reason from the framing they carry.

## 2. What the names are now

| Thing | Name | Notes |
|---|---|---|
| The platform | **Opus Gubernatio** | Descriptor: Project Decision Support |
| The analytical taxonomy | **Groups A, B, C, D** | Referred to by group and purpose |
| What occupies the framework slot | **A described capability, not a named framework** | Standing description below |
| Internal file prefix | `PCEIF_*` on development-era artifacts | Nobody sees these. Leave them. |

**There is deliberately no framework name.** One was proposed twice and dropped, because the
contribution is empirical evidence about how professionals respond to AI decision support, not a
new governance framework. If you find yourself needing a framework name to describe what the
platform does, describe what it does instead.

## 3. The standing description

Where a framework name would have gone, use this. It is written once so that every surface quotes
the same words rather than each file inventing its own version. That is how three incompatible
taxonomies arose in the first place.

**Short form, one sentence:**

> Opus Gubernatio analyses the documents a project produces each reporting period and presents a
> recommendation that a project manager records a decision against, keeping the evidence, the
> recommendation, and the judgment as one reproducible record.

**Long form, for the About page and anywhere a paragraph is wanted:**

> Opus Gubernatio takes the documents a project produces each reporting period, reads the
> reported figures from them, and runs an analytical layer over that evidence to produce a
> recommendation. The project manager records an independent assessment before the recommendation
> is disclosed, then records a decision after it, with the reasoning and the evidence relied upon.
> Every computed result is stored with the inputs and the code version that produced it, so what
> was shown at the moment of a decision can be reproduced rather than re-derived. The platform
> does not decide anything. It analyses evidence, presents what it found, and keeps the record of
> what a professional decided in response.

Use the short form in constrained space and the long form where a paragraph fits. **Do not
paraphrase either into a new variant.** Quote them verbatim.

**Two constraints on this wording, both deliberate and both fixed until Lin says otherwise.**

It says "a project", not "a capital project". Domain scope is an open advisor decision. Because
this description is quoted verbatim across every surface, it is the most expensive place for a
contested claim to sit. Do not add the setting.

It says "reads the reported figures", not "extracts the figures". Extraction has never run against
a real project document. Do not strengthen this wording.

## 4. The analytical taxonomy

**101 registered modules**, verified against the code and recorded in `GROUP_ASSIGNMENT.md`:

| Group | Purpose | Count |
|---|---|---|
| A | Project Health, what condition the project is in | 53 |
| B | Recommendation and Governance, what should be done and by whom | 36 |
| C | Data and Evidence Health, how trustworthy the evidence is | 7 |
| D | Portfolio Level, requires more than one project | 5 |

These are the REGISTERED counts, and they are what `server/app/simulation/registry.py` and
`assets/js/taxonomy.js` both derive. This table previously read 100 and 52. That was wrong: it
described the registered taxonomy but carried the count of a different population, the set the
analytical server computes. Both populations are real and the difference between them is one
module, so the two numbers must not be used interchangeably.

Where the count appears in user-facing text, state which population it counts. The registry holds
101 (Group A 53 of them). The analytical server computes 100 of those 101 (Group A 52 of them).
The single difference is Document Risk Score, `A4.1`: it holds a registry entry, so it counts in
the 101, but it is a value the extraction model supplies rather than one the analytical server
computes, so it has no formula and is absent from `VALIDATED`. Group A's roster is 53 named
entries: 52 computed plus Document Risk Score, supplied.

That split is current rather than permanent. Document Risk Score is absent from `VALIDATED` and
the registry reports it as not ported. If it is later implemented server-side, the computed count
becomes 101 and Group A's computed count becomes 53, at which point the two populations coincide
and the distinction above stops being needed.

**Group C does not contribute to project status.** Evidence quality describes what is known about
a project, not the project's condition.

**Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
"A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

**User-facing text uses "and", not the ampersand the code constants use.** Write "Recommendation
and Governance". Do not rename the code constants.

## 5. What the platform actually does

Verify against the code rather than taking this list on trust.

- **Computation is server-side.** The browser renders stored results and computes nothing.
  `sim.js`, `simulations.js` and `categories.js` do not load on participant-facing routes.
- **Documents extract once per unique file**, cached by content hash, so the same document always
  yields the same values.
- **Every computed result is stored** with its simulation version, seed, and period cutoff.
- **The decision sequence**: evidence, then a preliminary judgment committed and locked before the
  recommendation is disclosed, then the recommendation, then a recorded disposition with rationale.
- **One PM decides per project; observers read.** Membership is explicit and auditable.
- **Geocoding is server-side** via the Google Geocoding API with a United States Census fallback,
  and the matched address is shown back to the user.
- **Two audiences from one codebase**: research participants and operational users, separated by
  an `account_type` field that governs disclaimers, features, and whether data can enter a
  research export.

Anything that says the browser computes signals is stale.

## 6. Standing rules

- Verify against the code rather than asserting from memory.
- A test that cannot fail is worse than no test. Prove a check can fail by introducing the fault,
  then remove it.
- Loud refusal over quiet approximation.
- Stop at a clean boundary. Partial work on a research-critical path is worse than none.
- No em dashes in user-facing text.
- No module ids or numbers in user-facing text.
- Do not describe capability the platform does not have.
- Do not adopt liability or consent language on your own judgement. Draft it and mark it as
  requiring Lin's review.
