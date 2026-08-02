# server/ — migration beachhead (M1) and /exec facade (A1, A1b)

A FastAPI service with health endpoints, a Postgres schema, and an `/exec` compatibility facade
covering read and write actions. **No traffic is pointed at it.**

`assets/js/config.js` is untouched and still points at the Apps Script endpoint, so deploying this
moves no production traffic. `LinPRojectRadar/backend/` (the v9-era prototype) is also untouched.

## Endpoints

| Path | Purpose | Success | Failure |
|---|---|---|---|
| `GET /healthz` | Liveness. Process is running. **No database call.** Also reports the running interpreter. | `200` | only if the process is down |
| `GET /readyz` | Readiness. Real `SELECT 1` round-trip **and** schema at head. | `200` | `503` with a structured reason |

`/healthz` returns:

```json
{
  "status": "ok",
  "service": "opus-gubernatio-server",
  "version": "m1-beachhead",
  "python_version": "3.12.7",
  "python_version_info": [3, 12, 7, "final", 0],
  "checks": []
}
```

It exposes the interpreter version and nothing else about the environment: no paths, no
environment variables, no package list, and not `sys.version`, whose build string would leak
compiler and build-host detail.

### `/readyz` checks connectivity AND schema

**Every deploy that includes a migration requires `alembic upgrade head` against the target
database, and `/readyz` will report 503 until it is run.** Migrations are deliberately not in
`buildCommand`, so applying them stays an explicit decision.

`/readyz` returns 200 only when both checks pass:

| check | passes when |
|---|---|
| `database` | a real `SELECT 1` round-trip succeeds |
| `schema` | `alembic_version` matches the head revision derived from `alembic/versions/` |

The head revision is **derived from the migration scripts at runtime**, never hardcoded. A literal
revision string in application code is a second source of truth that drifts the moment someone adds
a migration and forgets to update it, and the failure mode is a health check reporting ready
against the wrong schema.

Failure shapes:

```json
{"name":"schema","ok":false,
 "detail":"alembic_version is 0002_snapshot_project_nullable, expected 0003_research_schema",
 "error_type":"SchemaOutOfDate"}
```

| `error_type` | meaning | fix |
|---|---|---|
| `SchemaMissing` | no `alembic_version` table; migrations never ran here | `alembic upgrade head` |
| `SchemaOutOfDate` | present but not at head | `alembic upgrade head` |
| `SchemaUnknown` | migration scripts or version table unreadable | inspect the deploy |
| `NotEvaluated` | database unreachable, so schema was not checked | fix connectivity first |

**Why this exists.** `SELECT 1` succeeds against a completely empty database. `/readyz` reported
ready for hours in production while every table-touching action returned `ProgrammingError`,
because the migrations had never been applied. A health check that cannot tell "reachable" from
"usable" is worse than none, because it is trusted.

`healthCheckPath` in `render.yaml` is `/healthz`, not `/readyz`, deliberately. If Render probed
readiness, a database outage would cause it to restart a process that is running correctly, turning
a dependency failure into an availability failure. Use `/readyz` for diagnosis, not for restarts.

## Environment variables

Set both in the Render dashboard. Both are declared `sync: false` in `render.yaml`, so Render will
not read a value from the repository.

| Variable | Required | Example | Notes |
|---|---|---|---|
| `DATABASE_URL` | **yes** | `postgresql://user:pass@dpg-xxxx.oregon-postgres.render.com:5432/og` | Service refuses to boot without it. `postgres://` and `postgresql://` are normalised to the psycopg 3 dialect automatically. **Never commit this.** |
| `CORS_ORIGINS` | no | `https://mrnyanlintun.github.io` | Comma separated. Omit or leave empty to disable CORS entirely. |
| `PYTHON_VERSION` | set in `render.yaml` | `3.12.7` | Secondary pin. See below. |
| `LOG_LEVEL` | no | `INFO` | Defaults to `INFO`. |
| `SESSION_SECRET` | recommended | random 48+ chars | Signs research session tokens. If unset, a per-process secret is generated and `session_secret_ephemeral` is logged; sessions then break on restart. |
| `SESSION_TTL_SECONDS` | no | `28800` | Session lifetime. Defaults to 8 hours. |
| `GOOGLE_GEOCODING_API_KEY` | recommended | a Google Cloud API key | Primary geocoding provider. Enable the **Geocoding API** in the Cloud project and enable billing, or the key returns `REQUEST_DENIED`. Restrict the key to the Geocoding API; use an **IP** application restriction, never an HTTP referrer one, because this key is used server side. If unset the module is inert and makes no request, the United States Census fallback still runs, and the user is told the service is not configured. **Never commit this.** |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | import only | JSON or a path to it | Read-only Drive key. Never committed. Used by `tools/import_from_drive.py`, not by the running service. |
| `DRIVE_PARENT_FOLDER_ID` | no | `14u6LT8...` | Overrides the default parent folder. |

## Interpreter version: pinned in two places

The Python version is pinned **twice**, deliberately:

1. **`server/.python-version`** containing `3.12.7`. This is the primary pin. Render reads it from
   the service root directory, and it is the more reliable of the two for interpreter selection.
2. **`PYTHON_VERSION: "3.12.7"`** in `render.yaml`. Retained as a belt-and-braces setting.

Both must be kept in step. Changing one alone will produce a build whose interpreter does not match
the file that claims to pin it.

### `/healthz` is the authoritative check

**The build log is no longer the only evidence of which interpreter is running.** Ask the service:

```bash
curl https://<service>.onrender.com/healthz
```

`python_version` in the response is the interpreter actually executing the application, which is
the fact that matters. A build log records what the builder selected; it can be stale, hard to
retrieve after later deploys, and it does not prove what the running process is using.

If `python_version` is not `3.12.7`, neither pin is taking effect. The next thing to check is the
service's **Root Directory** setting: `.python-version` is only read from the service root, so if
Root Directory is empty rather than `server`, the file is in the wrong place.

### Why two pins

A build ran on Python 3.14 despite `PYTHON_VERSION: "3.12.7"` being set in `render.yaml`. Two
things went wrong, only one of them loudly:

- **`psycopg[binary]` failed to resolve.** `psycopg-binary` ships wheels only and has no sdist, so
  pip could not build from source and reported only the versions carrying a wheel for the running
  interpreter. `cp314` wheels first appear in 3.2.10, so 3.2.3 was unreachable on 3.14. This is why
  the pin is now 3.2.13, which carries both `cp312` and `cp314` wheels.
- **SQLAlchemy silently lost its C extensions.** SQLAlchemy 2.0.36 has no `cp314` wheel, so on 3.14
  pip installs the pure-python fallback. It works, just slower, and nothing in the build log says
  so. This is the failure mode the two pins exist to prevent: a wrong interpreter does not always
  announce itself.

`server/.python-version` is forced to LF in `.gitattributes`. A trailing carriage return would make
the version string unparseable on Render's Linux builder.

## Render dashboard steps

1. **Create the Postgres instance.** Dashboard, New, Postgres. Choose name, region and plan. Wait
   until status is Available.
2. **Copy the Internal Database URL** from the instance's Info tab. Prefer Internal over External:
   it keeps traffic inside Render's network and is not reachable from the public internet.
3. **Create the web service.** New, Web Service, connect this repository, select the branch. Render
   reads `render.yaml` at the repository root and picks up `rootDir: server`.
4. **Set the region** to match the database, and **set the plan**. Neither is in `render.yaml`, by
   design, so both stay explicit decisions.
5. **Add the environment variables.** Under Environment, set `DATABASE_URL` to the Internal
   Database URL from step 2, and `CORS_ORIGINS` to the GitHub Pages origin.
6. **Deploy**, then watch the log stream. A successful boot emits one JSON line:
   `{"ts": "...", "level": "INFO", "message": "service_start", "db_backend": "postgresql", ...}`.
   The connection string never appears in the logs.

### Verification URLs

Replace `<service>` with the service name Render assigns.

```
https://<service>.onrender.com/healthz
https://<service>.onrender.com/readyz
```

`/healthz` must return `200` immediately. `/readyz` must return `200` once `DATABASE_URL` is set
correctly. If `/readyz` returns `503`, the JSON body names the failure in
`checks[0].detail` and `checks[0].error_type`.

The first request after idle can be slow on Render's free plan, which spins the service down.

## Local development

```bash
cd server
python -m venv .venv
.venv/Scripts/activate          # Windows; use source .venv/bin/activate elsewhere
pip install -r requirements.txt

export DATABASE_URL="sqlite:///./local.db"
export CORS_ORIGINS="http://localhost:8000"
uvicorn app.main:app --reload --port 8001
```

SQLite is supported for local verification only. Production is Postgres.

## Layout

```
server/
  app/
    __init__.py
    main.py             FastAPI app, /healthz, /readyz, GET+POST /exec
    facade.py           GET dispatch, projections, contract rules
    writes.py           POST dispatch: concurrency, server clocks, verified writes
    research_models.py  research schema ORM, ULID ids
    research_audit.py   durable audit writes on a separate connection
    research_identity.py login, sessions, roles, consent actions
    research_consent.py consent gate as a before_flush listener
    research_assignment.py assignment, counterbalancing, blinding
    research_decision.py  evidence, locked judgment, reveal, disposition
    research_transitions.py branch selection, action families, follow-up periods
    research_export.py    de-identified export, allowlist, checksum chain
    drive_adapter.py      read-only Google Drive adapter
    models.py           projects, project_snapshots, files
    settings.py         environment parsing, fail-fast, credential-free accessors
    db.py               engine, session factory, readiness probe, declarative Base
    logging_config.py   JSON formatter with credential redaction backstop
  alembic/
    env.py              reads DATABASE_URL via app.settings, never from alembic.ini
    versions/           0001 facade, 0002 snapshot owner, 0003 research, 0004 sequences, 0005 transitions
  alembic.ini           contains no sqlalchemy.url, so no connection string is ever committed
  requirements.txt      pinned
  tools/
    seed_from_fixtures.py  loads M0 fixtures for contract verification
    test_pre_lock_guard.py migration test for the pre-judgment lock
    test_research_identity.py B2 identity, roles and consent gate
    test_assignment_blinding.py B3 assignment and blinding
    test_decision_sequence.py B4 the experimental sequence
    test_transitions.py   B5 transitions and follow-up decisions
    test_export.py        B6 de-identified export and archive chain
    import_from_drive.py  A2 one-way Drive import + reconciliation
    test_drive_import.py  A2 offline verification against a stub
```

## Migrations

`0001_facade_schema` creates the three facade tables. `0002_snapshot_project_nullable` makes
`project_snapshots.project_id` nullable for the portfolio-health singleton. No research tables yet;
those arrive at B1.

```bash
alembic current
alembic revision --autogenerate -m "description"
alembic upgrade head
```

The migration step is **not** wired into `buildCommand`. Running migrations automatically on every
deploy would let a schema change ship without a human deciding to apply it.

## Secrets

- `DATABASE_URL` is read from the environment only. It is never written to a tracked file, and
  `alembic.ini` deliberately omits `sqlalchemy.url`.
- Logs record the database **scheme and host only**, never the URL.
- The JSON formatter redacts URL userinfo as a backstop, so a driver exception that embeds the DSN
  is scrubbed. The redaction consumes up to the final `@`, so a password containing `@` does not
  leak its tail. The backstop is not the primary control: no call site passes a secret.

## /exec compatibility facade (A1)

`GET /exec` and `POST /exec` reproduce the Apps Script action API on Postgres, so the existing
frontend could talk to this service unchanged. Read paths (A1) and write paths (A1b) are
implemented; AI and file-ingestion actions are still deferred. `assets/js/config.js` is untouched
and no traffic is pointed here.

### Contract rules

These come from the M0 live capture, not from source.

1. **Application errors are HTTP 200** with `{"ok": false, "error": "..."}`. The frontend reads
   `ok` from the body and never inspects the status code. Non-200 is reserved for transport faults.
   Even an unhandled exception is returned in this shape, because a 500 body would not parse as
   `{ok:false}` and the frontend would surface nothing useful.
2. **Actions match case-insensitively.** The frontend sends `identifyOnly` at `store.js:508` while
   the backend registers `identifyonly`; exact matching would break document identification
   silently.
3. **Key sets and types match `p0-baseline/contracts/`**, verified with `compare.py`.
4. **`ping` and `version` are aliases** reporting the version under `version`; `health` reports it
   under `apiVersion`. Both conventions preserved.

### Schema

`projects` (id, legacy_id, doc jsonb, record_version, archived, created_at, updated_at),
`project_snapshots` (id, project_id, period, snapshot jsonb, saved_at),
`files` (id, project_id, drive_file_id, name, doc_type, sha256, ingested_at).

JSONB first: the whole `project.json` lives in `projects.doc` rather than being shredded into
columns. The Apps Script backend has no fixed project schema. The captured fixtures show `list`
rows carrying geocode fields that `listarchived` rows lack, and each project carries a different
set of `signalInputs` keys. Shredding would force a column set the data does not have and would
silently drop anything unanticipated, which is the one failure a compatibility facade must not
have.

Two storage decisions were forced by evidence rather than by the schema brief:

- **`project_snapshots` is not `doc["history"]`.** PRJ-08421 carries four entries in
  `doc["history"]` while `gethistory` returns `[]`. They are different stores, so reading history
  out of the document would have invented four rows.
- **`docCount` is not a file count.** It is the number of `signals_extracted` events in the
  document. PRJ-08421 reports `docCount` 36 while `listcorpus` returns 3 entries. This derivation
  reproduces all 15 live slim rows exactly and is corroborated by the v10.25 note in the backend
  source: *resetSignals_ preserves signals_extracted events so the Uploaded Documents table
  survives resets*.

### Verifying against the live contract

```bash
export DATABASE_URL="sqlite:///./facade.db"     # or a Postgres URL
alembic upgrade head
python tools/seed_from_fixtures.py --project-id PRJ-08421
uvicorn app.main:app --port 8123
```

Then capture from the facade and diff against the live baseline:

```bash
python tools/contract-fixtures/capture.py --config <facade-config>.json --confirm --repo-root <tmp>
python tools/contract-fixtures/compare.py --baseline p0-baseline/contracts --candidate <tmp>/facade-fixtures
```

`tools/seed_from_fixtures.py` loads the M0 fixtures into the database so the facade can be compared
against the live contract using the same data. It is a verification aid, not a migration path.

## Write actions (A1b)

Implemented: `create`, `save`, `archive`, `restore`, `setprojectnumber`, `resetsignals`,
`overwritesignal`, `savehistory`, `saveauditresult`, `saveportfoliohealth`.

Deferred, returning `Action not implemented in this build: <action>`: `chat`, `analyze`,
`extractsignals`, `identifyonly`, `audit`, `portfolioanalyze`, `ingestcorpus`, `tts`. These are
the AI and file-ingestion paths; they land after the write paths are proven. The error says
"not implemented" rather than "unknown" so nobody debugging it goes looking for a typo.

Response shapes come from the v10.36 reference, since no live POST fixture exists: every write was
`DEFERRED_TO_MANUAL` at M0 and never captured. Error wording is reproduced verbatim because
`store.js` surfaces `error` straight to the user.

### Four rules every write follows

**Server clocks only.** Client timestamps are discarded and replaced. A client clock can be wrong,
skewed, or forged, and `updatedAt` doubles as the concurrency token.

**Verified write.** Each handler commits, re-reads, and confirms the change landed before returning
`ok:true`. A write that cannot be confirmed returns `ok:false` with a specific reason. There is no
path that reports a success it did not check.

**Conflicts are `ok:false`, never 409.** Contract rule 1 admits no non-200 for an application
outcome.

**JSON is replaced, never mutated.** SQLAlchemy does not track in-place mutation of a JSON/JSONB
value, so `doc["x"] = y` is dropped silently at flush. Every handler builds a new dict.

### Optimistic concurrency

`projects.record_version` increments on every write. The check uses whichever token the client
supplies:

1. `record_version` when present. Nothing sends it today; it is accepted so a future same-origin
   client can use the stronger token without a contract change.
2. Otherwise `project.updatedAt`. This is what the existing frontend round-trips: `store.js:359`
   posts `{action:"save", project}` and nothing else. Because the server assigns `updatedAt` on
   every write, a client that has not re-read since the last write presents a stale value and is
   rejected.

If neither token is present the write proceeds. Rejecting would break the frontend for any project
whose document has never carried `updatedAt`.

### Two behaviours worth knowing

`resetsignals` **preserves `signals_extracted` events** while clearing everything else. They are
what the Uploaded Documents table renders and they are the source of the slim `docCount`, so
dropping them would silently zero `docCount` for every project that had ingested a document. This
matches the v10.25 fix noted in the backend source.

`saveportfoliohealth` stores a **singleton** with `project_id NULL`, identified by a reserved
`period`. Migration `0002` makes `project_id` nullable for it. Attaching it to a synthetic owner
would have surfaced it in that project's `gethistory` and corrupted the project's history;
`a_gethistory` also excludes the reserved period explicitly.

## Research schema (B1)

Migration `0003_research_schema` creates twelve tables: `participants`, `participant_profiles`,
`consents`, `configurations`, `scenarios`, `assignments`, `decision_support_packages`,
`decisions`, `transitions`, `expert_references`, `audit_events`, `research_exports`.

They share **no foreign key** with `projects` / `project_snapshots` / `files`. The facade tables
mirror an external system that is still authoritative and still changing; the research record must
outlive it and must never be cascade-deleted by a project cleanup. The one link,
`scenarios.evidence_package_id`, is an opaque reference rather than a constraint.

Identifiers are ULIDs in `CHAR(26)`: they sort by creation time, so the primary key index is also
a time index. All timestamps are `timestamptz` and server-assigned.

### The pre-judgment lock

Two guarantees live in the database, not the application, because the preliminary judgment is the
measurement the study rests on and application code is the thing most likely to change.

**CHECK `ck_decisions_reveal_after_pre_lock`** — `reveal_at IS NULL OR (pre_locked_at IS NOT NULL
AND pre_locked_at <= reveal_at)`. A package cannot be revealed before the judgment is locked, and
the lock cannot be backdated to after the reveal.

**Trigger `trg_decisions_pre_lock_guard`** — rejects any UPDATE that would change `pre_action` or
`pre_confidence` once `pre_locked_at` is set. Columns that are not part of the preliminary
judgment stay writable, because the final decision is recorded on the same row.

### Why the trigger does not write its own audit row

**A trigger that raises cannot durably record its own rejection, on any dialect.** Whatever it
inserts belongs to the same transaction as the rejected UPDATE and is discarded when that
transaction unwinds.

This was measured, not assumed. An earlier version of this migration inserted from inside the
trigger; **zero rows survived on SQLite**, despite `RAISE(FAIL)` preserving statement-level
changes, because the caller's rollback removed them anyway. Postgres behaves the same and has no
autonomous transactions without an extension such as `dblink`.

The alternative — a trigger that silently reverts the protected columns and audits durably — was
rejected. A database that accepts an UPDATE and quietly discards it is precisely the silent
failure this project forbids, and a participant's attempt to revise a locked judgment must not
look like it succeeded.

So the trigger rejects loudly and `app/research_audit.py` writes the audit row **on a separate
connection with its own transaction**, which commits whether or not the caller's transaction
survives. The Postgres exception carries SQLSTATE `OG001` so callers can recognise it precisely;
SQLite carries no SQLSTATE, so that path falls back to a message marker.

### Running the test

```bash
DATABASE_URL=... python tools/test_pre_lock_guard.py
```

20 checks: the CHECK constraint in both directions, all three modification paths (Core UPDATE, ORM
update, raw driver SQL) rejected, three durable audit rows each identifying its path, the locked
values unchanged, and the non-protected columns still writable.

### Dialect differences

| | PostgreSQL (authoritative) | SQLite (local only) |
|---|---|---|
| Trigger | `BEFORE UPDATE` + PL/pgSQL function, checks both columns internally | `BEFORE UPDATE OF pre_action, pre_confidence` with a `WHEN` clause |
| Rejection | `RAISE EXCEPTION` with SQLSTATE `OG001` | `RAISE(ABORT)`, no SQLSTATE |
| JSON | `JSONB` | `JSON` |
| Migration `0002` | direct `ALTER COLUMN` | table rebuild via `batch_alter_table` |

The migration refuses to create the schema on any other dialect rather than silently omitting the
trigger, because the lock is not optional.

## Research identity, roles and consent (B2)

Identity runs on the same `/exec` contract as the facade: application errors are HTTP 200 with
`{"ok":false,"error":...}`, actions match case-insensitively, timestamps are server-assigned.
**No migration is included in B2**, so `/readyz` stays green on deploy.

| Action | Role | Notes |
|---|---|---|
| `researchlogin` | any | access token in, session token + role + stage + consent state out |
| `researchwhoami` | any | identity and role from the session |
| `researchparticipantget` | any | own record only, unless ResearchAdmin |
| `consentgrant` | any | records a `consents` row; `granted_at` server-assigned |
| `consentwithdraw` | any | sets `withdrawn_at`; never deletes |
| `adminparticipantcreate` | ResearchAdmin | server-generated `PM-001` code, returns the plaintext token once |
| `adminparticipantlist` | ResearchAdmin | never returns token hashes |
| `projectupload` | project PM | hash-cached; reports matched-vs-extracted and which files contributed nothing |
| `projectuploadstatus` | any active member | which documents are present, and whether the period is computed |
| `projectcompute` | project PM | runs the analytical layer once; refuses to overwrite an existing result |
| `projectresults` | any active member | READS the stored row; never computes; recommendation gated by `recommendation_visible` |
| `adminrecompute` | ResearchAdmin | requires a reason; writes a new row and supersedes the old one |

### Sessions are signed, not stored

B2 ships no migration, so there is no sessions table. A session token is an HMAC-signed assertion
of **one** thing: the participant id. Role, stage and consent state are read from the database on
every request, so a token cannot carry a stale or elevated role, and a change to a participant
takes effect immediately rather than when their token expires. Signature comparison is
timing-safe.

`SESSION_SECRET` signs them. **If it is unset the service still starts**, with a per-process
secret, and logs `session_secret_ephemeral` at startup. Sessions then stop working across a
restart or a second instance, which is visible and explainable, unlike a hardcoded default that
would be a forgeable signing key in a public repository.

### Access tokens

256 bits of randomness, stored as an unsalted SHA-256. Unsalted is deliberate: the input is
high-entropy random, not a human-chosen password, so there is no dictionary or rainbow-table
attack to defend against, and a deterministic hash allows an indexed lookup instead of scanning
every participant and comparing salted hashes. The plaintext is returned exactly once at creation
and cannot be recovered afterwards.

### The consent gate

No write to `participant_profiles`, `assignments`, `decisions`, `transitions` or
`research_exports` is permitted for a participant without an active consent row.

Enforced by a SQLAlchemy `before_flush` listener registered on the `Session` class, **not** by a
check at the top of each endpoint. An endpoint-level check is only as good as the discipline of
whoever writes the next endpoint, and its failure mode is silent: research data captured from a
participant who never consented, which cannot be repaired afterwards because the consent did not
exist at the time. The listener sees every INSERT and UPDATE the ORM performs, including from code
written later that never heard of the gate.

`decisions` and `transitions` have no `participant_id`; the gate resolves them through their
assignment, checking `session.new` first because a row created in the same flush is not yet
queryable. A `research_exports` row with no `initiated_by` is an administrative act with no owning
participant and must be marked explicitly rather than passing by default.

Not gated: `audit_events`, `participants`, `consents`. Audit rows must record what happened
regardless of consent state, a participant must exist before it can consent, and the consents row
*is* the act of consenting.

Withdrawal re-closes the gate immediately, and the consent row is retained rather than deleted so
the evidence that consent was given and later withdrawn survives.

### Running the test

```bash
DATABASE_URL=... SESSION_SECRET=... python tools/test_research_identity.py
```

41 checks, driven through the real HTTP surface rather than by calling functions, covering all
five rules including every one of the five gated tables.

## Assignment and counterbalancing (B3)

**A migration IS included** (`0004_condition_sequences`). `/readyz` reports 503 with
`SchemaOutOfDate` until `alembic upgrade head` is run against the target database.

| Action | Role | Notes |
|---|---|---|
| `adminscenariocreate` / `adminscenariolist` | ResearchAdmin | |
| `adminconfigurationcreate` / `adminconfigurationlist` | ResearchAdmin | `freeze: true` sets `frozen_at`; list reports `assignable` |
| `adminsequencecreate` / `adminsequencelist` | ResearchAdmin | preregistered condition orders, stored as data |
| `adminassign` | ResearchAdmin | one `assignments` row per scenario, with `sequence_number` and `config_id` |
| `adminassignmentlist` | ResearchAdmin | any participant; includes `config_id` |
| `researchmyassignments` | Participant | own rows only, up to the current position |
| `researchcurrent` | Participant | the single current assignment |

### Sequences are data, not code

`condition_sequences` holds one row per position: `(order_group, scenario_set, version, position)
-> config_code`. A preregistered order is a design decision the committee owns, so encoding it in
Python would mean a code change, review and deploy every time the design is revised, and would put
the allocation rule somewhere the design record cannot see.

A sequence must be **frozen** before it can allocate, exactly as a configuration must. When
`adminassign` is called without an explicit `sequence_version` it uses the latest frozen version,
so an allocation can never silently pick up an unapproved draft.

### Determinism

Allocation is deterministic given `(participant, order_group, scenario_set)`. The scenario list is
sorted before pairing, so request order cannot change the result; the frozen sequence supplies the
condition at each position; and the `sequence_version` used, plus the full position-by-position
allocation, is written to `audit_events`. An assignment can therefore be reproduced years later
even after the sequence is revised. Re-assigning a participant who already has assignments is
refused rather than silently producing a second allocation.

### Blinding, enforced server-side

1. **No cross-participant access.** The participant id comes from the session. An explicit
   `participant_id` in the body is refused and audited rather than ignored, because the attempt is
   itself something the audit trail should hold.
2. **Nothing beyond the current position.** The current position is the lowest `sequence_number`
   not yet `completed`, derived from the assignment rows rather than stored, so it cannot drift out
   of step. Future rows are filtered out, so even the length of the response does not reveal how
   many scenarios remain.
3. **No condition-revealing field.** Every participant-visible assignment is built by one function,
   `_blind_row`, returning only `sequence_number`, `scenario_id`, `status`. Adding a field there is
   the only way to leak one, which keeps the leak reviewable in a single place.
4. **Unfrozen configurations cannot be assigned.** Configurations are resolved for every position
   before any row is written, so an unfrozen configuration fails the whole allocation rather than
   half of it.
5. **The B2 consent gate still applies.** `assignments` is a gated table, so allocation for a
   participant without active consent is refused by the flush listener, and withdrawal re-closes
   the gate.

### Running the test

```bash
DATABASE_URL=... SESSION_SECRET=... python tools/test_assignment_blinding.py
```

44 checks, all driven through the `/exec` HTTP surface.

## The experimental sequence (B4)

**No migration is included.** `/readyz` stays green; head remains `0004_condition_sequences`.
Packages attach to an assignment through the existing `assignments.package_id`.

| Action | Role | Refuses when |
|---|---|---|
| `researchevidenceget` | Participant | not the current assignment |
| `researchprejudgment` | Participant | already locked |
| `researchreveal` | Participant | judgment not locked, or package not frozen |
| `researchdecision` | Participant | `reveal_at` is null, or already submitted |
| `adminpackagecreate` / `adminpackagelist` / `adminpackageattach` | ResearchAdmin | |

### Why this is the phase that carries the study

The claim the study makes is that the preliminary judgment was formed without sight of the
decision support package. Four properties make that verifiable rather than asserted.

**The lock is atomic and server-assigned.** `pre_submitted_at`, `pre_locked_at` and
`pre_judgment_locked` are written in one INSERT, so there is no window in which a judgment exists
unlocked. The test asserts the two timestamps are equal, which is only possible if they were set
in the same statement. No client can supply any of the three.

**Reveal is gated on the lock, and the refusal is silent about content.** A refusal that named the
recommendation would defeat the gate it enforces, so the test greps the refusal body for the
recommendation text, the alternatives, the detected condition, the package id and the hash.

**Stage is derived on every read, never stored or asserted.** Computed from the decisions row:
no row → `evidence`; `pre_submitted_at` set → `awaiting_reveal`; `reveal_at` set → `deciding`;
`final_submitted_at` set → `complete`. `participants.current_stage` is no longer read anywhere,
and a `current_stage` in a request body is ignored.

**Nothing calls a model.** `research_decision.py` imports no HTTP client. The test asserts the
absence of `requests`, `httpx`, `urllib.request`, `http.client`, `socket`, `openai`, `anthropic`
and `fetch(` in the module source, and that the revealed content is byte-identical to the stored
row.

### Package integrity

A package is frozen by computing a sha256 over an explicit, ordered list of content fields
(`HASHED_FIELDS`) and setting `frozen_at`. Only a frozen package with a hash can be revealed. At
reveal the hash is copied onto the decisions row, so a later edit to a package is detectable
against the decisions that were made under it. Re-revealing is idempotent and does not move
`reveal_at`, because `reveal_at` measures when the participant first saw the package.

Attaching a package to an assignment that has already been revealed is refused: changing it would
silently rewrite what the participant was shown.

### Running the test

```bash
DATABASE_URL=... SESSION_SECRET=... python tools/test_decision_sequence.py
```

59 checks, all through `/exec`, covering all seven guarantees.

## Decision-dependent transitions (B5)

**A migration IS included** (`0005_transition_rules`). `/readyz` reports 503 with
`SchemaOutOfDate` until `alembic upgrade head` is run against the target database.

| Action | Role |
|---|---|
| `adminactionfamilycreate` / `adminactionfamilylist` | ResearchAdmin |
| `admintransitionrulecreate` / `admintransitionrulelist` | ResearchAdmin |
| `researchadvance` | Participant |

### Rules and the action taxonomy are data

`transition_rules` holds one row per candidate branch for a
`(scenario_id, period, action_family)`. `action_families` maps each literal action to its family.
Both are versioned and must be frozen before use, like configurations, packages and condition
sequences.

**An unmapped action is an error, never a default.** There is deliberately no fallback family: a
fallback would silently absorb a typo or a newly added action and route a participant down a
branch nobody chose.

### Reproducibility

The seed is `sha256(participant_id | scenario_id | period)`. There is no call to `random()`: a
generator seeded at process start would make a run depend on process history, which cannot be
reproduced from the data. Candidates are ordered by `branch_id` rather than insertion order, so
re-inserting rows cannot change a selection.

The `transitions` row stores `branch_id`, `branch_version`, `seed`, `probability`,
`next_state_id` and `displayed_at`, so an allocation is reconstructible from the row alone and can
be re-derived *against* the rules table to detect drift. `probability` is stored as text so a
preregistered `0.30` survives the round trip exactly instead of becoming `0.29999999999999999`.

Because `branch_version` is on the row, a rule edited afterwards cannot change what an earlier
participant experienced.

### Periods

`decisions` now holds one row per `(assignment, period)`, and the period is **derived**, like the
stage and the sequence position. A completed period advances only once `researchadvance` has
actually executed, which makes "decided but not yet advanced" a distinguishable state rather than
a gap. From period 2 onward, `researchevidenceget` returns the state the transition produced, not
the scenario's opening evidence: re-reading the opening evidence would hide the consequence of the
participant's own decision, which is the thing this design measures.

**Behaviour change from B4:** an assignment now completes only after its *final* period. Before
B5, completing period 1 marked the whole assignment complete and moved the participant to their
next scenario with a period still outstanding. One assertion in `test_decision_sequence.py` had
encoded that bug and was updated.

### Running the test

```bash
DATABASE_URL=... SESSION_SECRET=... python tools/test_transitions.py
```

58 checks, including a full two-period run, all through `/exec`.

## De-identified export (B6)

**No migration is included.** `/readyz` stays green; head remains `0005_transition_rules`.

| Action | Role |
|---|---|
| `adminexportcreate` | ResearchAdmin |
| `adminexportlist` | ResearchAdmin |
| `adminexportfetch` | ResearchAdmin |

### De-identification is an allowlist, never a denylist

`EXPORT_COLUMNS` in `research_export.py` names every field that may leave the system, and each row
is assembled by naming each field explicitly. There is no `dict(row)`, no model introspection and
no `**kwargs`.

A denylist would invert the failure: the day someone adds an `ip_hash` column, every export
silently starts carrying it and the leak is found after the data has been shared. With an
allowlist, a new column simply does not appear. The test proves this by adding a real column to
`decisions`, populating it with a canary value, and asserting neither the name nor the value
reaches the export.

A defensive assertion inside `build_rows` fails the export outright if the assembled row and the
allowlist ever disagree.

`rationale` **is** exported, because it is a dependent variable, but participants can type
anything into it. Every export declares `review_required`, `free_text_columns` and a note that the
text must be reviewed before it is shared outside the study team.

### The payload is regenerated on fetch, not stored

`research_exports` records the checksum, not the bytes. `adminexportfetch` re-derives the payload
from current data and compares. This is stronger than reading back a blob: it detects the
underlying rows changing after the export was taken, which is exactly the drift that would
silently invalidate an analysis quoting that checksum. On mismatch the payload is **withheld** and
the event is audited.

It also means B6 needs no migration.

### Format and derived variables

Long format, one row per decision (participant x scenario x period), for mixed-effects models with
crossed random effects. JSON and CSV; the checksum covers the payload bytes as delivered.

Derived in the export so the analyst does not reconstruct them: `judgment_shift_action`,
`confidence_shift`, `deliberation_seconds` (final minus reveal), `pre_assessment_seconds`
(pre-submission minus first `evidence_viewed`), plus `period`, `sequence_number`, `config_code`,
`order_group`, `scenario_id`, `branch_id` and `branch_version`.

`config_code` is present deliberately: this is the analyst's view, not the participant's, so the
condition must be visible here even though it is hidden everywhere a participant can reach.

`pre_assessment_seconds` is measured from the earliest `evidence_viewed` audit event rather than a
column, because no column records when a participant opened an assignment. The derived variable is
therefore traceable to a recorded event.

### Consent gate interaction

An export is an administrative act gated by role, not by participant consent. The gate honours an
`_admin_authorised` flag set only by a handler that has already verified the caller is a
ResearchAdmin, so recording *who* ran the export does not make the write fail against an
administrator who has never consented as a subject.

### Running the test

```bash
DATABASE_URL=... SESSION_SECRET=... python tools/test_export.py
```

64 checks, seeding a full two-period run for two participants in different conditions.

## Drive import (A2)

**No migration is included.** `/readyz` stays green; head remains `0005_transition_rules`.

```bash
DATABASE_URL=... GOOGLE_SERVICE_ACCOUNT_JSON=... python tools/import_from_drive.py           # dry run
DATABASE_URL=... GOOGLE_SERVICE_ACCOUNT_JSON=... python tools/import_from_drive.py --apply   # writes
```

### One-way, read-only

`app/drive_adapter.py` requests `drive.readonly` and has **no write path at all** — no `create`,
`update`, `delete` or permission call. Apps Script remains the authoritative writer until M7, and
the failure this guards against is a split brain where both stores accept writes and neither is
authoritative. A read-only adapter cannot cause that even if a caller asks it to.

`GOOGLE_SERVICE_ACCOUNT_JSON` holds the key, never a committed file — the repository is public. It
accepts either the JSON itself or a path to it, because a long blob in a shell variable is easy to
truncate. Absent, the script fails immediately naming the variable: a missing credential that
surfaced later as an empty project list would look exactly like an empty Drive folder, and the
reconciliation would then cheerfully report a clean run of nothing against nothing.

### Dry run by default

`--apply` is required to write. Exit codes distinguish the outcomes so a caller checking only the
code cannot mistake one for another: `0` applied and clean, `1` unexplained discrepancies, `2`
could not reach Drive, `3` dry run completed.

### The reconciliation is the deliverable

An import that "worked" but moved 11 of 12 projects is worse than one that failed, because nothing
announces the missing one. Every run therefore ends by comparing both stores and writing
`p0-baseline/reconciliation/<timestamp>/report.md` and `report.json`, covering project counts,
per-project history/corpus/audit counts, unparseable `project.json` files by name, orphaned Drive
file ids, and projects present in only one store.

Differences with a known cause appear under **Explained differences** rather than being counted as
clean — an unparseable `project.json`, or a history file whose name carries no recognisable period.
The run is successful only when there are zero *unexplained* discrepancies.

### What is imported

`project.json` unchanged into `projects.doc`; `_history/*.json` into `project_snapshots` with the
period parsed from the filename; `_corpus`, `_audits` and `_signals` as **metadata only** into
`files`. No file bytes are downloaded in this phase, so `sha256` stays null rather than being
filled with Drive's md5 under a sha256 column name.

Idempotent by `legacy_id` and by `(project, period)`: an existing row is updated in place, so its
primary key, `created_at` and any research reference to it survive a re-run.

### Offline verification

```bash
DATABASE_URL=... python tools/test_drive_import.py
```

37 checks against a stub that mimics the Drive v3 responses this adapter uses, including forced
paging. It proves dry-run safety, idempotency, discrepancy detection and the explained-difference
path. It cannot prove the live API contract: field names, paging behaviour and permissions are
confirmed only by a real run with the service account.
