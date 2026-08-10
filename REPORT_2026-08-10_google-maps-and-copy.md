# Google Maps on the project detail page, and a site-wide copy sweep

Date: 2026-08-10

---

## 1. What the owner must provision for the map key

The detail-page street map is the **Google Maps JavaScript API**, loaded in the browser and keyed
from the deployment's environment. Nothing in the repository holds the key.

Provision three things in the Google Cloud project that already holds the geocoding key:

| What | Value |
|---|---|
| **Environment variable** (on the server, e.g. Render) | `GOOGLE_MAPS_BROWSER_KEY` |
| **API to enable** in the Cloud console | **Maps JavaScript API** |
| **Key restriction** to set | **HTTP referrer (websites)** restriction, limited to the platform's own origin(s), e.g. `https://<your-domain>/*` |

Notes that matter:

- This is a **different key** from the server-side geocoding key. The geocoding key
  (`GOOGLE_GEOCODING_API_KEY`) is used from the backend and takes an **IP** restriction; it is
  never sent to a page. The browser map key is drawn **in the browser**, so it necessarily travels
  in the `<script src=…>` URL the page loads. Its protection is not secrecy but the **HTTP
  referrer** restriction, which makes a copy lifted from the page inert on any other origin. Do not
  reuse one key for both; the restrictions are mutually exclusive.
- The key is read from the environment **at the point of use** (`server/app/map_config.py`), never
  held on `Settings`, so rotating it in the environment takes effect on the next request without a
  restart — the same discipline `geocode.py` uses.
- **No key is a supported state.** With `GOOGLE_MAPS_BROWSER_KEY` unset, the page makes **no
  request to Google**, and the Location section falls back to the flat atlas (the outline view)
  with a note that the street map is unavailable. Set the key to turn on streets; unset it to fall
  back. Nothing else changes.
- Billing: Dynamic Maps includes 10,000 free map loads per month; this platform's volume is in the
  hundreds, so the map is expected to sit inside the free tier.

Once the variable is set, the page fetches `/mapconfig` (same-origin), sees `present: true`, and
draws Google Maps at street zoom on each project's coordinates.

---

## 2. Google Maps on the detail page — what was built

The Location section previously showed a flat world atlas that cannot zoom to a street because it
holds no street data. It now shows **Google Maps at street level (zoom 17)** centred on the
project's coordinates, with a marker, whenever a browser key is set.

Behaviour, all verified (see §6):

- **Key present** → Google Maps opens at street zoom on the project's coordinates, marker placed;
  the matched-address line stays beneath it.
- **No key** → no request to Google at all; the section renders the flat atlas as the no-key map
  and the note reads *"The street map is unavailable, so this is the outline view."* — not a blank
  panel and not a broken frame.
- **Google library unreachable** (key set but the script fails to load) → the atlas again, with the
  note *"The street map could not be reached, so this is the outline view."*
- **No coordinates** → no map is drawn, no marker, nothing thrown; the Location badge reads
  *"no location"* and the note explains the project has no map position.

How the key reaches the browser without living in a committed file:

- `server/app/map_config.py` reads `GOOGLE_MAPS_BROWSER_KEY` from the environment and exposes it
  through a new endpoint **`GET /mapconfig`** (`server/app/main.py`), which returns
  `{provider, present, apiKey}`. `present` lets the page branch without ever needing the key when
  there is none; `apiKey` is sent only when one is set.
- `assets/js/detail.js` fetches `/mapconfig` once per page load, then loads the Maps JavaScript API
  on demand (`ensureGoogleMaps`) and draws the map (`renderGoogleMap`). The API script is injected
  in exactly one place, only on the keyed branch.
- The Content-Security-Policy in `index.html` now permits `maps.googleapis.com` and
  `maps.gstatic.com` on `script-src` and `connect-src`, `fonts.googleapis.com` on `style-src`, and
  `fonts.gstatic.com` on `font-src` (Google Maps' own styles and Roboto). The retired
  `tiles.openfreemap.org` permission is gone.

The **portfolio Map view was not touched** — it keeps the flat SVG atlas exactly as before.

---

## 3. MapLibre removed outright

The previous session left MapLibre as an unreachable ~400-line stage in `app.js`, guarded so it
could never run, plus 837 KB of vendored library on disk. Confirmed nothing reached it (its
interaction functions were called only as no-ops over an always-empty marker set on a `.map-wrap`
that view-switching kept permanently hidden), then removed it all:

- **`assets/js/app.js`** — the whole stage: `buildMap`, `createGlMap`, `loadMapAssets`,
  `scheduleMapWarmup`, the GL markers/popups/pins, theme swap, reset, and the live no-op call
  sites. Removed the two dead references to `.map-wrap` that view-switching left behind.
- **`assets/vendor/maplibre-gl.min.js` and `assets/vendor/maplibre-gl.min.css`** — deleted (837 KB).
- **`assets/css/radar.css`** — every MapLibre rule (`.map-wrap`, `#map-gl`, `.gl-pin*`, `.gl-pop*`,
  `.gl-pill`, `.map-fx`, `.map-scan-*`, `.map-boot-*`, `.map-reset-btn`, `.map-caption`,
  `.map-nolocation`, the `.maplibregl-*` selectors, and the light-theme variants).
- **`index.html`** — the `.map-wrap` markup and the stale MapLibre comments; the CSP no longer
  lists the tile host.
- **`assets/vendor/ASSETS.md`** — the MapLibre rows and the tile-host paragraph, replaced by the
  Google Maps note; total updated 5.9 MB → 5.1 MB.

The two dead taxonomy-counting functions `activeModuleTotal()` and `buildModuleAxes()` were left
alone, as instructed (they are pinned by `test_map_and_module_count.py` §5).

---

## 4. Copy errors found and fixed, per surface

The two the owner found were both on the **project detail page**, in the status-provenance trace:

| Surface | Before | After |
|---|---|---|
| Detail page → provenance | `…other category` + `ies` → **"categoryies"** at a plural count | "**2 other categories**" (correct plural; "1 other category" at a single tie) |
| Detail page → provenance | `Monte Carlo EAC Forecast: red` (lower-case, straight from the data) | `Monte Carlo EAC Forecast: **Red**` (capitalised via `normalizeStatus`) |

The status-word case error was invisible in source because the value came from data; it is now
driven from data in a test and asserted on the rendered text (§6, GROUP 22).

### 4.1 Status-word / empty-state capitalisation

| Surface | Before | After |
|---|---|---|
| Training figures (`training.js`) | `no data` (lower-case) | `No data` — matches the "No data" empty state used on every other surface |

Everywhere else the status words (Green/Yellow/Amber/Red/Complete) and the empty states
("No data", "Awaiting analysis", "Not relevant") were already capitalised consistently in rendered
code. The lower-case "awaiting ingest" forms that appear in the source are all in **comments**
about retired wording, not rendered text.

### 4.2 Category / group names: "&" → "and" (NAMING_AUTHORITY §4)

The authority mandates *"user-facing text uses 'and', not the ampersand the code constants use"*
and names Groups B and C as "Recommendation and Governance" and "Data and Evidence Health". The
Knowledge Library already used "and"; the ledger, decision UI, workspace, export and project
network rendered "&" — a live inconsistency. Fixed in `taxonomy.js`, `categories.js`,
`decision-ui.js`, `workspace.js`, `export.js`, `projectnet2d.js` (41 occurrences):

| Before | After |
|---|---|
| Cost & EVM Performance | Cost and EVM Performance |
| System Dynamics & Complexity | System Dynamics and Complexity |
| Regulatory & Authority Thresholds | Regulatory and Authority Thresholds |
| Recommendation & Governance (Group B) | Recommendation and Governance |
| Data & Evidence Health (Group C) | Data and Evidence Health |

### 4.3 Em dashes in user-facing prose (forbidden by NAMING_AUTHORITY)

Em dashes used as prose punctuation in rendered strings were replaced with the correct punctuation
(colon, comma, or a full stop) or, where they merely separated a value pair, the house middle-dot
`·`. 59 replacements across the following surfaces. Representative before → after per surface;
every changed string is in the diff.

**Admin (`admin.js`, `admin-ops.js`)**
- `Participant — research subject` → `Participant: research subject` (and the Admin / Expert role options likewise)
- `Copy failed — select the field and copy manually` → `Copy failed. Select the field and copy manually`
- `Username (optional — generated as PM-### if left blank)` → `Username (optional, generated as PM-### if left blank)`
- `Reset password — ` / `Link Google account — ` / `Feature flags — ` (dialog titles) → `: `
- `…cannot be retrieved again — write it down or copy it now.` → `…again. Write it down or copy it now.`
- `NOT filtered to research accounts — a project's results carry no account type.` → `…accounts. A project's results carry no account type.`

**Signals / upload (`signals.js`)** — the largest set, ~24 messages, e.g.
- `File too large — maximum 3MB. Please compress the PDF.` → `File too large: maximum 3MB. Please compress the PDF.`
- `✓ All models complete — view results below.` → `✓ All models complete. View results below.`
- `Models could not run — check CPI / SPI.` → `Models could not run: check CPI / SPI.`
- `CPI and SPI ready — running models…` → `CPI and SPI ready. Running models…`
- `Extracted — models ran on the extracted signals.` → `Extracted. Models ran on the extracted signals.`
- `⏳ Rate limited — retrying in …` → `⏳ Rate limited. Retrying in …`
- `All required values present — nothing outstanding.` → `All required values present. Nothing outstanding.`
- project-picker options `${id} — ${name}` → `${id} · ${name}`

**Auditor (`auditor.js`)**
- `Couldn't load corpus — store unreachable.` → `Couldn't load corpus: store unreachable.`
- `SheetJS not loaded — cannot export XLSX.` → `SheetJS not loaded: cannot export XLSX.`
- `✓ Uploaded — <file>` → `✓ Uploaded: <file>`
- `N items reviewed —` → `N items reviewed:`
- `Draft response request (for contractor fairness gate) — requires human review before sending` → `…gate): requires human review before sending`

**Detail page (`detail.js`)**
- `Ensemble Scatter — N active modules (N total)` → `Ensemble Scatter · N active modules (N total)`
- provenance `— first shown` → `, shown first`; `— estimated field, not a direct extraction` → ` (estimated field, not a direct extraction)`
- pattern line `(N categories) — …` → `(N categories): …`
- `Executive brief — <name>` → `Executive brief: <name>`

**Export (`export.js`)**
- `XLSX library not loaded — cannot export the report.` → `…loaded: cannot export the report.`
- report headers `OPUS GUBERNATIO — NOTICE` / `— PROJECT REPORT` → `OPUS GUBERNATIO: NOTICE` / `: PROJECT REPORT`
- `Stage 2 — not yet active` → `Stage 2: not yet active`

**Project network / neural / atlas / charts**
- `PROJECT SIGNAL NETWORK — N modules · N categories` → `PROJECT SIGNAL NETWORK · N modules · N categories`
- `Awaiting signal extraction — all categories shown as no-data.` → `Awaiting signal extraction. All categories shown as no-data.`
- `N/A — not applicable to <sector>-sector projects` → `N/A: not applicable to …`
- atlas hover title `name — status — address` → `name · status · address`
- chart annotation `P06 row highlighted — consistent underperformer` → `…: consistent underperformer`

Grammar/plural agreement was checked across every count-driven fragment: apart from the
"categoryies" case, all guards (`n === 1 ? "" : "s"`, `? "category" : "categories"`) were already
correct, and no "1 modules"-style disagreement was found.

---

## 5. Found but deliberately NOT changed (flagged for your decision)

These are real observations, left unchanged with reasons, so the decision is yours rather than
mine:

1. **Module numbers on the portfolio Signal Ledger.** The ledger renders `A1.1`, `A1` etc.
   (`cat-mod-num`, `cat-row-num` in `app.js`). The naming authority forbids module ids in
   user-facing text, but the task says *"do not touch the portfolio,"* and removing the number
   columns is a layout change, not a copy fix. **Left as-is.** The **detail page itself carries no
   module ids** (verified — its executive brief instructs the model not to use them, and the
   `BRIEF_CAT_LABEL` map that contained "(Cat N)" is dead code, never rendered).
2. **Module numbers in the Knowledge Library and the researcher deep-dive** (`B1.1`, "Module 19",
   "Cat 8.1"). These surfaces are a technical catalogue whose organising structure *is* the
   computation index; stripping the ids is a documentation redesign, not a copy fix. **Left as-is.**
3. **The empty-value glyph "—".** Dozens of table cells render a lone "—" to mean "no value"
   (`status || "—"`), and the About page's "Last updated" cell before it is filled. This is a
   typographic convention, not prose, so the rendered-em-dash scanner is scoped to *prose*
   (a letter, spaced em dash, a letter) and does not flag it. **Left as-is** — say the word and it
   becomes "n/a" or blank everywhere.
4. **"&" outside the taxonomy names.** Document-type labels ("Financial & Schedule Documents",
   "Risk & Correspondence Documents", …) and category short-aliases on researcher surfaces
   ("Document & Risk", "Governance & Compliance", "ML & AI") still use "&". These are not the
   taxonomy group/category names the authority governs. **Left as-is** — trivial to convert if you
   want them consistent.
5. **Citation authors keep "&"** ("Busemeyer & Bruza", "Wang & Strong") — correct citation style,
   not touched.
6. **Provenance panel structure.** The `.det-prov-panel` is a `<span>` inside a `<p>`, and its rows
   are `<div>`s; the HTML parser closes the `<p>` before a block `<div>`, so the rows render as
   siblings *outside* the "hidden" span and are effectively always visible (which is why the owner
   saw the text without clicking "why?"). This is a pre-existing structural quirk, not a copy
   error, and fixing it touches shared markup — **flagged, not changed.**

---

## 6. Verification

Every check below was proven able to fail by introducing the fault, confirming the specific check
went red, reverting, and confirming the baseline came back green.

**Server suite** (`server/tools/test_map_and_module_count.py`, rewritten): 55/55, and the whole
server suite 2992/2992 green on a fresh database per file.

- The old §3 asserted app.js "still marks its MapLibre stage as orphaned" and "still guards on the
  global being absent." That check went red because **the stage it protected no longer exists** —
  it recorded the intermediate state, not a property worth keeping. Full removal is a strictly
  stronger guarantee, so §3 now asserts the stage, files, CSS and markup are **gone**. (This is the
  "a red recorded a defect, not a property" case the task flagged: established, and stated.)
- New file-level checks (each fault-proven): app.js has no live MapLibre identifiers; the vendored
  files are deleted; radar.css carries no MapLibre rules; the CSP permits the Google Maps hosts and
  no longer permits the tile host; `map_config.py` reads `GOOGLE_MAPS_BROWSER_KEY` from the
  environment; `config.js` holds no key; `/mapconfig` exists; and `map_config()` reports
  `present:false/apiKey:null` with no key and `present:true/apiKey` with one.

**Render harness** (`tests_render.html`, driven headless): 278/279. The one red — "production read
path: exercised against the server" — is the pre-existing group that requires a signed-in session
token, which a headless tab does not have; it is an environment gate, not a defect, and was red at
HEAD too.

- **GROUP 21 (new)** drives the rendered Location section. No key: the atlas renders, the note says
  the street map is unavailable, and **no `maps.googleapis.com` script is injected** (counted
  before/after). Key present (Google API stubbed, because the container cannot reach
  `maps.gstatic.com`): a Google map is constructed at **zoom 17**, centred on the project's
  latitude and longitude, with a marker, and the host is a Google map, not the atlas. Each of these
  was fault-proven (wrong zoom, wrong centre, removed marker, missing note, an injected request all
  turned the matching check red).
- **GROUP 20c (existing)**: a project with no coordinates renders, throws nothing, draws no marker,
  and the badge says "no location".
- **GROUP 22 (new)** renders the detail page from a stored row carrying **lower-case** statuses and
  a three-way category tie, then reads the rendered text: it must say "2 other categories" (not
  "categoryies"), render the status as "Red" (not "red"), carry no em dash and no module id, and
  name the category "Cost and EVM Performance" (not "&"). Each of the four was fault-proven by
  reintroducing the original bug and watching the check go red.

---

## 7. Files changed

- **New:** `server/app/map_config.py`, `REPORT_2026-08-10_google-maps-and-copy.md`
- **Server:** `server/app/main.py` (+`/mapconfig`), `server/tools/test_map_and_module_count.py`
- **Client:** `index.html`, `assets/js/detail.js`, `assets/js/app.js`, `assets/css/radar.css`,
  and the copy fixes in `admin.js`, `admin-ops.js`, `atlas.js`, `auditor.js`, `categories.js`,
  `charts3d.js`, `decision-ui.js`, `export.js`, `knowledge.js`, `neural_flow.js`,
  `projectnet2d.js`, `signals.js`, `taxonomy.js`, `training.js`, `workspace.js`
- **Tests:** `tests_render.html` (GROUP 21, GROUP 22, GROUP 20 comment, LinAuth stub)
- **Deleted:** `assets/vendor/maplibre-gl.min.js`, `assets/vendor/maplibre-gl.min.css`
- **Docs:** `assets/vendor/ASSETS.md`
