# Security Scan Report — Lin Project Radar
Date: 2026-07-08
Scanner: Claude Code

Scope: all tracked files (frontend `assets/js/`, `index.html`, `assets/visualizations/`, `backend/` FastAPI app, `.gs` snippets, docs). `.git` and `.claude/worktrees/` excluded.

Architecture note: the repo contains **no deployable Apps Script `Code.gs`** — the two `.gs` files in `backend/` are paste-in snippets. The live backend in-repo is the FastAPI app `backend/main.py`; the frontend targets whatever `LIN_API_URL` points at (currently an Apps Script `/exec` deployment). Both surfaces were scanned.

---

## CRITICAL (fix before any public demo or practitioner interview)

### C1. No server-side authentication on any write endpoint
- **File:** `backend/main.py` — all `@app.post` routes: `/create` (:251), `/save` (:269), `/archive` (:286), `/restore` (:291), `/overwritesignal` (:415), `/resetsignals` (:446), `/ingestcorpus` (:485); plus token-spending routes `/chat` (:306), `/analyze` (:330), `/extractsignals` (:345), `/audit` (:548)
- **Issue:** Zero auth checks — no API key, bearer token, or Google JWT verification anywhere in the backend. Combined with `allow_origins=["*"]` and no CSRF token, any anonymous caller (or any website via a victim's browser) can create, overwrite, reset, and archive projects and spend OpenAI tokens.
- **Why it matters:** Full data tampering and cost amplification by anyone who discovers the endpoint URL (which is in committed `config.js`).
- **Fix:** Verify the Google ID token server-side (signature + `aud` + `email`) on every write/AI route; reject otherwise.

### C2. Client-side auth is forgeable and bypassable
- **File:** `assets/js/auth.js:32-47` (JWT decoded client-side, no signature verification — explicit "Stage 2" TODO at :33-35); `auth.js:115-121` (if `configured()` is false, app runs with **no auth at all**)
- **Issue:** The Google JWT is base64-decoded in the browser and `payload.email` is trusted. An unsigned JWT with `email = window.LIN_AUTHORIZED_EMAIL` (readable in source) passes the gate. The `!configured()` path is an intentional local-dev bypass but removes all gating.
- **Why it matters:** Auth is UX-only; provides zero real access control. Pairs with C1 to leave the system fully open.
- **Fix:** Keep client gate for UX, but enforce token verification server-side (same fix as C1); document the dev bypass explicitly.

---

## HIGH (fix before v1.0-praxis-demo tag)

### H1. No backend file-size or MIME enforcement on uploads
- **File:** `backend/main.py:357-365` (`/extractsignals` base64-decodes any payload, no size cap; MIME only branched on, never validated/rejected)
- **Issue:** Client-side caps (`signals.js:1005-1008`, `:1247-1259`) are bypassable by calling the endpoint directly → memory-exhaustion and OpenAI cost DoS. MIME `accept=` attribute is a UX hint only.
- **Why it matters:** Unauthenticated (see C1) + unlimited payloads = trivial resource/cost abuse.
- **Fix:** Enforce a server-side byte cap (e.g. 5 MB decoded) and a MIME allowlist before decoding/processing.

### H2. Wide-open CORS on the backend
- **File:** `backend/main.py:34-37` — `allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]` (credentials disabled)
- **Issue:** All origins may call all routes. Header comment (:5) confirms this deliberately matches Apps Script behaviour.
- **Why it matters:** Any third-party page can drive writes from a visitor's browser. `allow_credentials=False` is the only mitigation.
- **Fix:** Restrict `allow_origins` to the deployed frontend origin(s) once auth (C1) lands; until then, document as accepted risk.

### H3. Missing Subresource Integrity (SRI) on CDN scripts
- **File:** `index.html:537` (pdf.js 3.11.174), `index.html:539` (xlsx 0.18.5) — both pinned, both from cdnjs, **no `integrity=` attributes** (0 in the file)
- **Issue:** A CDN compromise could inject arbitrary script into the app.
- **Why it matters:** These scripts run with full page privileges (auth token in localStorage).
- **Fix:** Add `integrity="sha384-…" crossorigin="anonymous"` to both script tags.

---

## MEDIUM (fix in next sprint)

### M1. CSP `script-src` includes `'unsafe-inline'` and three unused CDNs
- **File:** `index.html:15` — `script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://esm.sh https://unpkg.com https://accounts.google.com`
- **Issue:** `'unsafe-inline'` weakens XSS defense (required by current inline-script + `innerHTML` architecture; escaping is applied consistently, see PASSED). `cdn.jsdelivr.net`, `esm.sh`, `unpkg.com` are allowlisted but never used — unnecessary supply-chain surface.
- **Fix:** Remove the three unused CDN hosts now; plan a nonce-based CSP to drop `'unsafe-inline'` later.

### M2. Backend `/audit` response omits the data-boundary tag
- **File:** `backend/main.py:548-588` — audit JSON has no `data_boundary` field; only the client-assembled record (`decision.js:204`) carries it
- **Issue:** Server-emitted audit artifacts lack the synthetic-data disclaimer that governance requires.
- **Fix:** Add `"data_boundary": "Synthetic demonstration data only; not a validated production system."` to the `/audit` response.

### M3. Synthetic-data badge documented but never rendered
- **File:** `assets/radar.css:163` (`.synthetic-badge` styles exist), `README.md:67` (claims a visible badge) — no HTML element or JS uses the class
- **Issue:** README overstates the visible disclaimer; only footer/About text renders (`index.html:520`, `:393`, `:505`).
- **Fix:** Either render the badge element or correct the README.

---

## LOW / ACCEPTED RISK (document and acknowledge)

### L1. Apps Script `/exec` URL and authorized email committed in `config.js`
- **File:** `assets/js/config.js:13` (`LIN_API_URL` = `https://script.google.com/macros/s/AKfy***/exec`), `:20` (`LIN_AUTHORIZED_EMAIL` = personal Gmail)
- **Issue:** The endpoint URL is effectively an unauthenticated backend address; the email is PII/enumeration only. `LIN_GOOGLE_CLIENT_ID` (:19) is intentionally public — not flagged.
- **Fix:** Acceptable for a single-user praxis demo; becomes an issue only if C1 remains unfixed.

### L2. Project data and AI outputs cached in localStorage plaintext
- **Files:** `store.js:54` (full project portfolio JSON), `auditor.js:194` (AI audit cache), `app.js:1077` (AI portfolio summary); benign UI prefs at `assistant.js:211` (voice), `app.js:828-829` (theme)
- **Issue:** Beyond the expected set (auth token/email/expiry at `auth.js:42-44`, timezone at `tz.js:45`, ingest log at `ingest.js:35`). No secrets, but project data persists in the browser in plaintext.
- **Fix:** Accepted for synthetic data; revisit if real data is ever loaded.

### L3. No root `.gitignore` for `.env`
- **File:** repo root (no `.gitignore`); `backend/.gitignore` correctly ignores `.env`
- **Issue:** A root-level `.env` created by accident would be committable.
- **Fix:** Add a root `.gitignore` with `.env*` (keep `.env.example`).

### L4. Client size check runs after base64 encoding (single-file path)
- **File:** `assets/js/signals.js:1005-1008` — 3 MB check happens after the full file is read+encoded; the multi-file path (:1247) checks raw size first
- **Fix:** Move the raw `file.size` check before `readFileAsBase64()` in the single-file path.

### L5. `img-src https:` is broad; standalone visualization has no CSP
- **File:** `index.html:18`; `assets/visualizations/pceif_neural_signal_flow.html` (no CSP meta, but fully self-contained — no external resources, constants-only tooltip data)
- **Fix:** Optional tightening; low risk as-is.

---

## PASSED (no issue found)

- **Secrets:** No hardcoded API keys, tokens, or passwords anywhere in tracked files. Only placeholders in `backend/.env.example`; `OPENAI_API_KEY` read from environment (`main.py:94,99`); `render.yaml` declares the key without a value. No real `.env` committed (`git ls-files` verified).
- **Frontend key exposure:** No API key in any fetch() header, localStorage, or HTML. The frontend calls the backend with `Content-Type: text/plain` only (`store.js:77,84-88`); Anthropic/OpenAI calls are brokered server-side.
- **`eval()` / `document.write()`:** Zero occurrences across all JS.
- **XSS / escaping:** `esc()`/`escH()` is defined and consistently applied to every interpolation of user- or API-derived data into `innerHTML` — verified across app.js, detail.js, signals.js (incl. user-entered override reasons), ingest.js, auditor.js, assistant.js (AI chat responses), neural_flow.js, modules.js, projectnet2d.js. knowledge.js raw-HTML bodies are developer-authored curated content, not user input.
- **CSP wildcards:** No `*` in `connect-src`, `script-src`, or `default-src`. `connect-src` lists only expected Google/OpenAI endpoints (`api.anthropic.com` correctly absent — never called from the browser). `unsafe-eval` absent. `frame-ancestors 'none'` set.
- **CDN sources:** pdf.js and xlsx pinned to specific versions on cdnjs (trusted); no `@latest`, no unknown CDNs.
- **Path traversal:** Solid server-side validation — `validate_project_id` (`main.py:70-89`, `^\d{2}$`) on every id-bearing route; `/ingestcorpus` writes use server-generated file ids, never the client `fileName` (`main.py:491,519-520`). No traversal sink.
- **Expiry logic:** `isAuthenticated()` (`auth.js:20-27`) correctly enforces the 8-hour localStorage expiry and re-checks the email (client-side-only caveat noted in C2).
- **Data boundary (client):** Disclaimer present in `index.html:520` footer (+ About :393, :505, meta :25) and `decision.js:27-28` `DATA_BOUNDARY` constant, emitted into client audit records (`decision.js:204`).
