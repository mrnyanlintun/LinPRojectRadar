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
    models.py           projects, project_snapshots, files
    settings.py         environment parsing, fail-fast, credential-free accessors
    db.py               engine, session factory, readiness probe, declarative Base
    logging_config.py   JSON formatter with credential redaction backstop
  alembic/
    env.py              reads DATABASE_URL via app.settings, never from alembic.ini
    versions/           0001 facade, 0002 nullable snapshot owner, 0003 research schema
  alembic.ini           contains no sqlalchemy.url, so no connection string is ever committed
  requirements.txt      pinned
  tools/
    seed_from_fixtures.py  loads M0 fixtures for contract verification
    test_pre_lock_guard.py migration test for the pre-judgment lock
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
