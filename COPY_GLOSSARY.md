# Copy glossary

The terms this platform uses for its own concepts, and the ones it does not. Two audiences read
this text: research participants, and practising directors using the platform on real projects.

Spelling is **American English**. Two exclusions, both load-bearing:

- `center` is CSS and geometry, not prose.
- `analyze` is an `/exec` action name (`writes.py` `DEFERRED_AI_ACTIONS`, `store.js`). Renaming it
  breaks the facade contract.

A sweep that only ever rewrites British into American satisfies both by construction. Run
`python tools/copy_inventory.py` to measure.

---

## People and roles

| Use | Not | Why |
|---|---|---|
| **Admin** | ResearchAdmin (in copy) | `ResearchAdmin` is the stored role value. A reader sees "Admin". |
| **Participant** | subject, user, respondent | A research subject. |
| **User** | operational user, practitioner | A director, VP or practising staff member. Outside the research record. |
| **PM** | owner, lead, manager | Per project. The one who decides. |
| **Observer** | viewer, reader, watcher | Per project. Reads only. |
| **Expert** | reviewer, panellist | Research review panel. Records the reference standard. |
| **the researcher** | the operator, the administrator, the study team | Who creates accounts and assigns work. One person, named consistently. |

`Demo` is a permitted role in the data model and is branched on nowhere. It is not offered in the
interface and should not appear in copy.

## Things

| Use | Not | Why |
|---|---|---|
| **project** | engagement, program, case | |
| **period** | cycle, reporting period, month | A project advances one period at a time. |
| **document** | file, upload, artifact | What a participant uploads. "File" only when talking about the file itself, e.g. a size limit. |
| **analysis** | computation, run, simulation | What `projectcompute` produces. |
| **stored result** | computed result, cached result | What the analysis produced and the server kept. Say "stored" to distinguish it from a live recomputation. |
| **signals** | metrics, indicators, outputs | What the analysis shows on the project page. |
| **decision support package** | AI package, recommendation package, the package | Written out in participant-facing copy. "Package" alone is acceptable after the first mention. |
| **preliminary judgment** | initial judgment, first decision, pre-judgment | `pre_judgment` is the column. Copy says "preliminary judgment". |
| **final decision** | decision, submission | |
| **reference standard** | expert reference, gold standard | What an expert records and participant decisions are scored against. |

## Status words

Use the stored value as written: **Green**, **Yellow**, **Amber**, **Red**, **Complete**.

**Awaiting analysis** is the state of a project with no stored result. It is not an error and must
not be styled as one. It means the analysis has not been run, which is different from healthy and
different from at risk.

Never invent a status word, and never soften one. A Red is a Red.

## Navigation

| Use | Not |
|---|---|
| **Portfolio** | dashboard, home, overview |
| **Project** | project detail, project view, workspace |
| **Admin** | administration, admin ops, settings |
| **Sign in** / **Sign out** | log in, login, logout |

"Workspace", "Questionnaire" and "Admin Ops" were destinations that no longer exist. Do not
reintroduce them as words.

## Tone

**Short sentences.** One idea each.

**Say what happened, then what to do.** A refusal that only says no leaves the reader stuck.

**Do not stack hedges.** "Cannot be changed", "permanently" and "no way to edit it afterwards" in
one paragraph is one fact said three times, and stacked emphasis reads as anxiety rather than as
a clear consequence.

**Do not explain the interface to itself.** A sign-in form does not need a sentence saying access
requires signing in.

**Do not expose internal structure in a refusal.** Say what the reader can do. Table names, column
names and action names are not copy.

**No em dashes in prose.** Use a comma, a colon, or a full stop, whichever the sentence wants.
Do not substitute a hyphen mechanically; that is its own tell. The standalone `—` used as an
empty-value placeholder in a table cell is not prose and stays.

**Module ids are acceptable in user-facing text, and a name is usually better.** `A1.1` is a
key; "Monte Carlo EAC" is the name. The former prohibition was SUPERSEDED by the owner on
2026-08-23.

**Internal identifiers are not content.** A ULID or a project id is not the name of anything. Show
the name; if an id is genuinely needed, make it secondary and truncated.

## Legal and attribution

Order is **notice, attribution, copyright**. The copyright line is the least useful thing on the
page and goes last.

Liability notices and consent text are **drafted for the researcher's review and never adopted on
an implementer's judgement**. Consent text additionally requires IRB approval. Mark any change to
either as requiring review.

The operational notice must be accurate about responsibility without implying the platform is a
toy. "Proof-of-concept" reads to a director as "do not rely on this" and is not used in the
operational variant. The research variant stays protective, and it is the fail-safe default shown
before an account type is known.
