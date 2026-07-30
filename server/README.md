# server/ — migration beachhead (M1)

A FastAPI service with health endpoints and a database connection. It serves **no application
traffic** and implements **no Apps Script action**.

`assets/js/config.js` is untouched and still points at the Apps Script endpoint, so deploying this
moves no production traffic. `LinPRojectRadar/backend/` (the v9-era prototype) is also untouched.

## Endpoints

| Path | Purpose | Success | Failure |
|---|---|---|---|
| `GET /healthz` | Liveness. Process is running. **No database call.** | `200` | only if the process is down |
| `GET /readyz` | Readiness. Real `SELECT 1` round-trip. | `200` | `503` with a structured reason |

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
    main.py             FastAPI app, /healthz and /readyz
    settings.py         environment parsing, fail-fast, credential-free accessors
    db.py               engine, session factory, readiness probe, declarative Base
    logging_config.py   JSON formatter with credential redaction backstop
  alembic/
    env.py              reads DATABASE_URL via app.settings, never from alembic.ini
    versions/           empty: no application tables at M1
  alembic.ini           contains no sqlalchemy.url, so no connection string is ever committed
  requirements.txt      pinned
```

## Migrations

Alembic is initialised with no revisions. `target_metadata` points at the declarative `Base`, which
has no subclasses yet, so autogenerate has a target once the research schema arrives at B1.

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
