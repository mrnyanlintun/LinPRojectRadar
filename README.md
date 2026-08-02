# Opus Gubernatio

(repo: `lin-project-radar`)

Project Decision Support. Built for a Doctor of Engineering praxis by Nyan Lin Tun at The George
Washington University.

> Opus Gubernatio analyses the documents a project produces each reporting period and presents a
> recommendation that a project manager records a decision against, keeping the evidence, the
> recommendation, and the judgment as one reproducible record.

That sentence is the standing description from `NAMING_AUTHORITY.md`, quoted verbatim. Read that
file before writing or changing anything user-facing: it is the authority for what the platform
and its analytical taxonomy are called, and the description above is quoted, never paraphrased,
on every surface that describes the platform.

## What this actually is

A static frontend and a Python server, deployed together.

- **Frontend**: vanilla JavaScript, HTML, CSS in `index.html` and `assets/`. No framework, no
  build step. The browser renders results the server computed and stored; it derives no project,
  category, or module status of its own.
- **Server**: FastAPI in `server/`, exposing a single `/exec` facade. It authenticates callers,
  computes and stores the analytical layer, brokers the one AI call, geocodes addresses through
  the Google Geocoding API with a United States Census fallback, and enforces the decision sequence. Persistence is a relational database through
  SQLAlchemy with Alembic migrations (Postgres in production, throwaway SQLite for development
  and tests).
- **One AI call**: server-side document extraction, reading the reported figures from uploaded
  documents, cached by content hash so extraction runs once per unique file. Nothing else on the
  platform calls a model. Actions that would need one (chat, automated audit, speech) are refused
  by name by the server rather than failing quietly. The in-app assistant is scripted: it answers
  from the written knowledge library in `assets/js/knowledge.js` by keyword match.

## The analytical layer

100 distinct computations in four groups, verified against the code and recorded in
`GROUP_ASSIGNMENT.md`, which is the authority for how the taxonomy is described. Groups are
referred to by name and purpose: Project Health, Recommendation and Governance, Data and
Evidence Health, and Portfolio Level. The count excludes the document risk score, which is
recorded as a value the extraction model supplies rather than one the analytical server
computes. A check in `server/tools/test_group_assignment.py` fails if the code and that
artifact stop agreeing.

Every computed result is stored with its inputs, simulation version, seed, and reporting-period
cutoff, append-only: a recompute writes a new row and marks the previous one superseded, and once
a submitted decision references a row, the database refuses to change it.

## The decision sequence

Evidence first, then a preliminary judgment committed and locked before the recommendation is
disclosed, then the recommendation, then a recorded disposition with a rationale field captured.
Enforced server-side. One PM decides per project; observers read; membership is explicit and
auditable.

## Two audiences

One codebase serves research participants and operational users, separated by an `account_type`
field that governs notices, features, and whether data can enter the de-identified research
export. Operational users are never included in an export. Research accounts do not create their
own projects; the researcher creates and assigns them.

## Running it

- **Development server**: `python server/tools/dev_serve.py [port]` (default 8010). It fills
  `DATABASE_URL` only if unset (defaulting to a gitignored repo-local SQLite file), migrates to
  head, seeds development fixtures, and serves the frontend and API together on port 8010.
- **Tests**: the suites in `server/tools/test_*.py` each need a freshly migrated throwaway
  database; run `python -m alembic upgrade head` against each before the suite. Read counts from
  each suite's own `RESULT: n/n` line. `tests.html` and `tests_render.html` are browser suites:
  open them at `http://127.0.0.1:8010/` with the dev server up. `tests_render.html` is the
  regression net for stored-result rendering and must be run after any change to `app.js`,
  `detail.js`, `decision.js`, or `taxonomy.js`.
- **Deployment**: Render, from `render.yaml`. A push to `main` deploys. `DATABASE_URL` and
  secrets live in the Render dashboard, never in this repository.

## Rules that govern the content

From `NAMING_AUTHORITY.md`, which carries the full list:

- There is deliberately no named framework. Describe the capability, not a name. The names the
  code still carries in places (`PCEIF_*` constants and development-era artifacts) are retired;
  do not use them in anything user-facing and do not reason from their framing.
- Quote the standing description verbatim; never paraphrase it into a new variant.
- No module ids or numbers in user-facing text, and no em dashes.
- Do not describe capability the platform does not have. Extraction has never run against a real
  project document.
- Do not adopt liability or consent language on your own judgement; draft it for review.
