# Run 41A — Read-Only Condition Survey

**Date:** 2026-08-21
**Repository:** `/home/user/LinPRojectRadar` (Linux clone; see §0.2)
**HEAD at survey:** `ee707e5d191650cd560cbf4aacc816cbcea2b014`

---

## 0. Compliance statement, and premise mismatches in the controlling prompt

### 0.1 Constraint compliance

**I edited no file other than this report. I committed nothing other than this report.**
No production file, no test, no handoff, no audit artifact and no configuration was created,
edited, moved or deleted. No fix was written, begun or proposed. No migration was run against
anything but the runner's own throwaway SQLite templates in `mktemp -d`. No user-facing control
was added, moved or removed. The PRJ-001 document set was not touched (and does not exist — §7).

Defects and discrepancies found during the survey are RECORDED below and were not acted on.

**One qualification, stated up front rather than buried:** running the permitted test suites caused
the suites themselves to rewrite 13 committed audit artifacts. I restored all 13 and committed
none. **See §0.1a**, which gives the full list, the evidence, and two findings inside the discarded
diff.

**Nothing in this survey is urgent in the sense of §0's stop clause.** The byte-identical guard
passes, the working tree is clean, and the full suite is green. The findings below are
record-only.

### 0.1a THE SUITES REWRITE COMMITTED AUDIT ARTIFACTS — a side effect of running them, restored

**This is the one respect in which running the survey changed the working tree, and it is
reported rather than buried.**

Running `server/run_all_suites.sh` (prompt §2.2 explicitly permits running the existing suites)
left **13 committed files modified**:

```
$ git status --porcelain      # immediately after the suite run
 M code_audit/run10_no_operational_effect.csv
 M code_audit/run20_cycle12_100_reaudit.csv
 M code_audit/run38_controlled_stimulus_execution_order.csv
 M code_audit/run38_lock_integrity.csv
 M code_audit/run38_participant_state_machine.csv
 M code_audit/run8_expectation_mutation_proof.csv
 M code_audit/run9_abstention_results.csv
 M code_audit/run9_alias_overlay_verification.csv
 M code_audit/run9_fixture_import_results.csv
 M code_audit/run9_known_answer_results.csv
 M code_audit/run9_no_operational_effect.csv
 M code_audit/run9_validator_gap_recomputations.csv
 M server/tools/run17/coverage.csv
```

**I did not write these. The suites did.** Several suites regenerate their own audit artifact as a
side effect of executing. The repository already knows about this class: commit `29354a2` is
titled *"Run 42: restore the self-rewriting audit artifacts"* — the same phenomenon, met and
restored one run ago.

**I restored all 13 to their committed state** (`git checkout -- code_audit/ server/tools/run17/`)
and re-verified:

```
$ git status --porcelain
?? REPORT_2026-08-21_run41A_condition_survey.md
```

**Only this report remains, untracked. No committed file was left modified, and none was
committed.** Restoring a file the suites overwrote is not an edit of my own — the tree is
byte-identical to `ee707e5` on every tracked path, which is exactly the state §3.2 records.

**Two substantive findings inside the discarded diff**, recorded here because they will recur the
next time anyone runs the suites:

1. **Most of the churn is nondeterministic identifiers, not changed results.** e.g.
   `code_audit/run9_abstention_results.csv` and `code_audit/run38_lock_integrity.csv` row 7 differ
   only in a freshly minted ULID (`01M0DFA94CXFC0VMT52WF59DNP` → `01M0JES5CGEJGS3WYJAF3Y905M`);
   the verdict column is `PASS` on both sides.

2. **One row is a genuinely stale committed artifact — the file records a finding the code no
   longer has.** `code_audit/run38_lock_integrity.csv`:

   | | row |
   |---|---|
   | **committed** | `final,4 direct write beneath the API,raw SQL UPDATE,final_action=BYPASS2,`**`ALLOWED (no trigger exists)`**`,BYPASS2,no,`**`FINDING_NOT_BLOCKING`** |
   | **regenerated** | `final,4 direct write beneath the API,raw SQL UPDATE,final_action=BYPASS2,`**`refused by trigger`**`,escalate,yes,`**`PASS`** |

   The committed row predates Run 41's migration **0026**, which added the refusing trigger. This
   is **precisely** the class Run 42 reported and fixed for a sibling file —
   `REPORT_2026-08-21_period-binding-mechanism-repair.md` §9: *"`code_audit/run39_administrative_authority_boundary.csv`
   was stale in the repository: it recorded `ALLOWED` for post-final-lock writes that Run 41's
   migration 0026 now refuses. Regenerated here."* **`run38_lock_integrity.csv` carries the same
   staleness and was not regenerated then.**

   Note the direction: the committed artifact understates the platform's current integrity. The
   live behaviour is stronger than the record claims. **Recorded, not fixed** — regenerating it
   would mean committing a file other than this report.

### 0.2 The prompt's repository path is not this session's repository

The controlling prompt names `C:\Users\NTUN\OneDrive - Arora Engineers, LLC\DEng\LinPRojectRadar`
and an interpreter at `.venv\Scripts\python.exe`. This session is the Linux clone at
`/home/user/LinPRojectRadar`. **There is no `.venv` in this checkout** — `ls server/.venv/bin/python`
returns "No such file or directory". `server/run_all_suites.sh` lines 10-14 already handle this:

```
VENV_PY=".venv/bin/python"
[ -x "$VENV_PY" ] || VENV_PY="$(command -v python3)"
```

so the suites ran under `/usr/local/bin/python3`, which has the pinned dependencies installed
(`python3 -c "import fastapi,sqlalchemy,alembic"` → `deps ok`). **Reported as a mismatch, not
reconciled.** `PYTHONIOENCODING=utf-8` was set — the runner exports it per suite (line 31).

**No browser session was used.** `preview_list` / `preview_start` were not invoked, so the
`DEng\Demo` hazard in prompt §2.3 did not arise. **The cwd used throughout was
`/home/user/LinPRojectRadar`.** No local server was started.

### 0.3 The freeze marker in the prompt does not match the repository

The prompt (§3.6 and §2.4) treats the freeze as `sim-2026.08-v2`. **The live stamp is
`sim-2026.08-v27`.**

`server/app/simulation/models.py:475`:
```
SIMULATION_VERSION = "sim-2026.08-v27"
```
`server/app/simulation/models.py:480`:
```
SIMULATION_VERSION_SUPERSEDED = "sim-2026.08-v26"
```

`sim-2026.08-v2` is the **second** entry in `SIMULATION_VERSION_HISTORY`
(`models.py:486`), i.e. an August-2026 audit baseline retired twenty-five stamps ago.
`models.py:117` says so in its own words: *"the current stamp is not what this file records:
sim-2026.08-v2 was superseded by Run 7"*. The prompt's premise is stale by twenty-five version
increments. **Verified from source; reported rather than reconciled.** Details in §3.6.

### 0.4 The prompt's run numbering does not match repository history

The prompt asks whether "Run 40" is still open and calls this survey "Run 41A". The repository's
actual merge history (`git log --oneline --all | grep -i "Merge Run 4"`) is:

| Merge commit | Subject |
|---|---|
| `4bd1468` | Merge Run 40: Fable functional/security acceptance (FABLE_ACCEPTANCE_BLOCKED) |
| `1b624d3` | Merge Run 41: successor freeze closing S1 and S2 (SUCCESSOR_FREEZE_ACCEPTED) |
| `ee707e5` | Merge Run 42: period-binding and evidence-lineage mechanism repair (sim-2026.08-v27) |

**Run 40 merged, Run 41 merged, and a Run 42 merged after both — Run 42 is HEAD.** A survey
numbered "41A" therefore sits behind two merged runs, not one. Full detail in §3.5.

The dispatching agent's framing — that the third run was "a further period-binding repair run
merged at ee707e5 creating sim-v27" — is **correct as to substance and hash but calls it
unnumbered**; the repository names it **Run 42** in seventeen commit subjects and in
`T6_HANDOFF.md:12352` (`# Run 42 (2026-08-21) — the period-binding and evidence-lineage mechanism`).
**I verified the repository's version.**

### 0.5 Reading done before starting (prompt §1)

**`T6_HANDOFF.md`** — read. Not updated. **It is stale in two specific respects** (evidence below):

1. **Its own newest-first convention is broken.** The file's header rule (lines 6-11) says new
   sections are *"appended at the TOP, newest first"*. The topmost dated section is
   `# 2026-08-19 - Run 39` at **line 12**, while the Run 42 section sits at **line 12352** — at
   the BOTTOM. A reader following the file's stated convention reads Run 39 as current and never
   reaches Run 42 unless they scroll 12,000 lines.
2. **Its summary table records a superseded stamp.** `T6_HANDOFF.md:171` reads
   `| Simulation | \`sim-2026.08-v25\` |` and line 269 repeats `**Simulation \`sim-2026.08-v25\`**`,
   while the live stamp is `sim-2026.08-v27` — two successor freezes newer.

There is no Run 40 or Run 41 section in the file at all (`grep -n "Run 4[01]" T6_HANDOFF.md`
returns no section header).

**The naming authority document.** Path: **`/home/user/LinPRojectRadar/NAMING_AUTHORITY.md`**
(repository root). Located; the prompt's §11.3 stop condition does not fire.

The sentence that fixes the group naming, quoted verbatim from its table at
`NAMING_AUTHORITY.md` §2:

> | The analytical taxonomy | **Groups A, B, C, D** | Referred to by group and purpose |

and the accompanying standing rule in §2:

> **There is deliberately no framework name.** One was proposed twice and dropped, because the
> contribution is empirical evidence about how professionals respond to AI decision support, not
> a new governance framework.

**`code_audit/`** — read. Every module claim in §5 below is answered from the live registry or
from `code_audit/` artifacts, never from memory. `code_audit/CHECKSUMS.sha256` verifies clean when
checked from inside `code_audit/` (`sha256sum -c` → no non-OK lines).

---

## 3. Ground truth

### 3.1 Branch, HEAD, and agreement

```
$ git rev-parse --abbrev-ref HEAD   → main
$ git rev-parse HEAD                → ee707e5d191650cd560cbf4aacc816cbcea2b014
$ git rev-parse main                → ee707e5d191650cd560cbf4aacc816cbcea2b014
$ git rev-parse origin/main         → ee707e5d191650cd560cbf4aacc816cbcea2b014
```

**HEAD, `main` and `origin/main` all agree** at `ee707e5d191650cd560cbf4aacc816cbcea2b014`.
Matches the dispatching agent's stated fact.

### 3.2 Working tree

```
$ git status --porcelain   → (no output)
```

**The working tree is clean.** Nothing uncommitted. **The prompt's §11.5 stop condition — another
session's uncommitted work — does not fire.**

(Note: at the moment `research/freeze/run42_successor_freeze_gate.csv` blocker B01 was generated,
that gate recorded *"git porcelain lines at evaluation: 15"* — that was the state during Run 42's
own execution, not now.)

### 3.3 The last ten commits

```
$ git log -10 --date=short --pretty='%h %ad %s'
```

| Hash | Date | Subject |
|---|---|---|
| `ee707e5` | 2026-08-21 | Merge Run 42: period-binding and evidence-lineage mechanism repair (sim-2026.08-v27) |
| `c5cc688` | 2026-08-21 | Run 42: report and handoff |
| `29354a2` | 2026-08-21 | Run 42: restore the self-rewriting audit artifacts |
| `db7e114` | 2026-08-21 | Run 42: final successor identity, freeze gate and release records |
| `07dccf7` | 2026-08-21 | Run 42: extend the pinned production-manifest chain to the run42 manifest |
| `7938cd9` | 2026-08-21 | Run 42: regenerated freeze gate and release records at the pinned candidate |
| `a574d03` | 2026-08-21 | Run 42: re-pin the candidate after the gate re-anchoring |
| `de51586` | 2026-08-21 | Run 42: successor freeze release records and gate re-anchoring |
| `68f9d9c` | 2026-08-21 | Run 42: correct the predecessor candidate pin |
| `8fa91ef` | 2026-08-21 | Run 42: pin the successor freeze candidate |

### 3.4 Every `REPORT_*.md` at repository root

**137 report files.** Listing all 137 with a one-line summary each would be transcription rather
than survey; the full filename list is reproducible with `ls REPORT_*.md`, and each filename
already carries its date and subject in the repository's own naming convention
(`REPORT_<yyyy-mm-dd>_<subject>.md`). The date range is **2026-08-01 to 2026-08-21**.

The reports material to this survey's questions, read and summarised:

| File | Date | Claims |
|---|---|---|
| `REPORT_2026-08-19_run40-fable-functional-security.md` | 08-19 | Fable functional/security acceptance. **Final disposition `FABLE_ACCEPTANCE_BLOCKED`** — line 5. Two unresolved integrity/version-boundary owner decisions (line 128-129). |
| `REPORT_2026-08-19_run41-successor-freeze.md` | 08-19 | Successor freeze closing security findings S1 and S2. All four gates re-qualified; **0 unresolved HIGH blockers**. Scope: "one serving function and one migration". |
| `REPORT_2026-08-21_period-binding-mechanism-repair.md` | 08-21 | The Run-42 report. Two mechanism defects proved and fixed (D1 lost per-field document identity, D2 null project id in the qualification record). `sim-2026.08-v26` → `sim-2026.08-v27`. Final suite 188 suites / 14176 checks green. |

**Observation, recorded not acted on:** the most recent report is named
`REPORT_2026-08-21_period-binding-mechanism-repair.md` and does **not** carry a `runNN` token,
unlike its predecessors (`...run40-...`, `...run41-...`). Its own §1 heading is
`# Run 42: the period-binding and evidence-lineage mechanism`. The filename and the content
disagree about whether the run is numbered. This is a plausible reason the prompt's numbering
drifted.

### 3.5 Whether Run 40 merged, is open, or was abandoned

**Run 40 MERGED**, at commit **`4bd14684abadd3ab8a94d68964b686993a5d6718`**, subject
*"Merge Run 40: Fable functional/security acceptance (FABLE_ACCEPTANCE_BLOCKED)"*.

The evidence has two parts and they must not be collapsed:

- **Merge status: merged.** `4bd1468` is a first-parent ancestor of `origin/main`.
- **Acceptance disposition: BLOCKED.** `REPORT_2026-08-19_run40-fable-functional-security.md:5`:
  *"Final disposition: **FABLE_ACCEPTANCE_BLOCKED** (two owner decisions required; both are
  integrity/version-boundary items, not participant-reachable holes left open)."*

**A blocked disposition merged into main is not an open run.** Run 41 then closed the two
findings: `REPORT_2026-08-19_run41-successor-freeze.md` records *"Functional/security acceptance
(Run-40 affected) | S1 fixed, S2 fixed, **0** unresolved HIGH blockers"*, and
`code_audit/run41_security_findings_closure.csv` is the artifact. Run 41 merged at `1b624d3`.
Run 42 merged after it at `ee707e5`.

**Answer: Run 40 is merged and closed, two runs behind HEAD.** The prompt's question presumes it
might still be open; it is not.

### 3.6 The freeze marker, the byte-identical guard, and whether it passes

**PREMISE MISMATCH — this is the finding the prompt's §3.6 produces.**

The prompt asks where `sim-2026.08-v2` is recorded. **It is recorded only as historic audit
baseline, never as the current freeze.** Every occurrence in the repository:

| File:line | Context |
|---|---|
| `server/app/simulation/models.py:51` | "RUN 7 (FIX-NOW DEFECTS) moves it again, to sim-2026.08-v3, and sim-2026.08-v2 remains the ..." |
| `server/app/simulation/models.py:60` | "sim-2026.08-v2 and sim-2026.08-v3 both remain the historical audit baselines" |
| `server/app/simulation/models.py:117` | "the current stamp is not what this file records: sim-2026.08-v2 was superseded by Run 7" |
| `server/app/simulation/models.py:486` | 2nd element of `SIMULATION_VERSION_HISTORY` |
| `server/tools/test_run6_known_answer.py:5,649` | a Run-6-era comment and a history-prefix assertion |
| `server/tools/run28_fault_campaign.py:219`, `build_run27_remediation_matrix.py:542`, `run31_restate_version_suites.py:123,128` | run-era prose and generators |

**The live freeze marker is `sim-2026.08-v27`**, at `server/app/simulation/models.py:475`. The
full history tuple (`models.py:485-495`) has **27 entries**, `sim-2026.07-v1` through
`sim-2026.08-v27`, and its docstring states nothing in it is ever edited or removed *"because each
row is the audit baseline for results already collected under it"*. `sim-2026.08-v2` is one such
preserved row.

**What the guard covers.** The guard is `server/tools/test_run38_frozen_immutability.py`. It does
not hash `server/app/simulation/` as an opaque directory; it holds a **named authorised-change
set** per successor run, so that a permitted change is permitted *by name* and anything else fails:

```
server/tools/test_run38_frozen_immutability.py:111
RUN41_AUTHORISED_MANIFEST_CHANGES = {"server/app/simulation/models.py"}

server/tools/test_run38_frozen_immutability.py:116
RUN42_AUTHORISED_MANIFEST_CHANGES = {"server/app/simulation/qualification.py"}
```

with the reasons recorded inline at lines 161-174 (`models.py` — "the stamp advances to
sim-2026.08-v26, then v27"; `qualification.py` — "the dimension reasons that read it";
`compute.py` — "the project identity passed to the record"). Line 209 asserts *"the live
simulation version is the Run-42 successor sim-2026.08-v27"*.

This is the design `REPORT_2026-08-19_run41-successor-freeze.md` describes: *"The frozen-surface
guards were not relaxed to achieve this. They were made exact: they now permit a named set of
owner-authorised successor changes and still fail on anything else."*

**Does it currently pass? YES.**

```
ok    tools/test_run38_frozen_immutability.py  17/17
ok    tools/test_run39_frozen_immutability.py  19/19
```

Independently, I recomputed the whole pinned production manifest against the working tree:

```
$ while read h f; do a=$(sha256sum "$f"|cut -d' ' -f1); [ "$a" = "$h" ] || echo "DIFF $f"; \
    done < code_audit/run42_production_tree.sha256
   (no output — every pinned file is byte-identical)
```

**The prompt's §11.4 stop condition does not fire.**

The release record `research/freeze/RUN42_SUCCESSOR_FREEZE_RECORD.json` reads
`release_disposition = FINAL_FREEZE_ACCEPTED`, `simulation_version = sim-2026.08-v27`,
`freeze_gate.blockers_evaluated = 15`, `freeze_gate.blocked = 0`, `blocking_defects = 0`,
`unresolved_high_security_blockers = 0`. All fifteen rows of
`research/freeze/run42_successor_freeze_gate.csv` read `PASS`.

### 3.7 Whether the deployed site runs `origin/main` — NOT DETERMINABLE FROM THIS SESSION

**Not determinable.** Outbound HTTPS from this session goes through the agent proxy, and the
proxy refuses this host:

```
$ curl -s -m 25 -o site.html -w "HTTP=%{http_code} bytes=%{size_download}\n" \
    https://linprojectradar.onrender.com/
HTTP=000 bytes=0

$ curl -s -m 40 -I https://linprojectradar.onrender.com/
HTTP/1.1 403 Forbidden
Content-Type: text/plain; charset=utf-8
```

A control request to an unrelated host also returned `000`, so this is general egress denial, not
a property of the deployed application. **I could not establish what commit the deployed site is
running, and I did not guess.** What would be needed: network egress to `onrender.com`, or the
Render dashboard's deployed-commit field, or a build-stamp endpoint served by the application.

`render.yaml` exists at the repository root and describes the service, but a deployment manifest
in the repository states what *would* be deployed, not what *is*.

---

## 4. The population and the counts

The four numbers were observed on a **site render**, which this repository does not contain. For
each I establish where in code it is produced and what it counts, and say whether it is computed
or hard-coded.

### 4.1 The 96 on the architecture panel — COMPUTED, registry-derived

**File/function:** `assets/js/detail.js:41` `projectModuleCount()`, fed by
`assets/js/detail.js:33` `projectCats()`; and independently
`assets/js/neural_flow.js:136` and its `HEADERS` block at `neural_flow.js:757`.

**Computed, not hard-coded.** It is the module count of `window.LIN_CATEGORIES` after removing
portfolio-level categories. Derived mechanically by evaluating the shipped taxonomy:

```
$ node -e "global.window={}; eval(fs.readFileSync('assets/js/taxonomy.js','utf8')); …"
categories: 12
project cats: 11   project modules: 96
total modules: 101
```

**Population counted:** *project-level* analytical modules the platform's registry declares —
**not** modules that ran for the project on screen. `assets/js/neural_flow.js:745-752` states this
explicitly and records that it used to be mislabelled:

> These headers used to read "27 DOCUMENTS", "96 MODULES" and "11 CATEGORIES". Every one of those
> numbers is a property of the platform's registry, not of the project on screen: 27 is the number
> of document types the extraction layer recognises, 96 the number of project-level modules the
> registry declares, and 11 the number of registered categories.

**Authoritative? Yes, for the question "how many project-level modules does the platform
declare".** It is architecture, not activity.

### 4.2 The 85 in the Executive Brief — COMPUTED, DATA-DEPENDENT, NOT DETERMINABLE FROM THIS REPOSITORY

**File/function:** produced at `assets/js/signals.js:484`:

```
summary: {
  total_modules: allModules.length,
```

and read into the brief prompt at `assets/js/detail.js:1554`:

```
const totalModules = (snapshot.summary && snapshot.summary.total_modules) || 0;
```

then rendered into the brief text at `detail.js:1601`:

```
"The platform computed " + totalModules + " signal modules across " + projectCats().length +
" analytical categories from a stored log dated " + computedDay + ".\n\n"
```

**Computed, and data-dependent.** `allModules.length` is the modules that actually produced a
result in the **stored category snapshot for that project and that reporting period**. It is a
property of one project's stored computation, not of the registry.

**The specific value 85 cannot be verified from this repository**, because this repository holds
no computed result for the project that was rendered. **Not determinable from the repository.**

**This is the finding, not an omission:** 96 and 85 are answers to two different questions — 96 is
"how many project-level modules exist", 85 is "how many produced a result on this row". They are
not expected to agree and neither is authoritative over the other.

### 4.3 The 100 on the documents panel — DATA-DEPENDENT, NOT DETERMINABLE

**There is no constant `100` producing a documents count anywhere in the shipped code.** The
constants in this area are:
- `assets/js/neural_flow.js:12` `DOC_KEYS` — **27** entries, rendered as
  `DOC_KEYS.length + ' SUPPORTED DOCUMENT TYPES'` at `neural_flow.js:758`. That is *document
  types*, not documents.
- the project's own document rows, which come from stored `document_uploads` (server-side,
  `server/app/research_models.py:547` `DocumentUpload`, one row per upload EVENT).

**100 is therefore the count of stored document rows for the rendered project**, a live-data
figure. **Not determinable from the repository**, which holds no such project.

### 4.4 The 75 uploaded / 25 retained on the signal flow note — COMPUTED, DATA-DEPENDENT

**File/function:** `assets/js/neural_flow.js:487-493` computes `retainedBeforeReset`, and
`neural_flow.js:757-764` renders the pair:

```
[CX.doc, DOC_KEYS.length + ' SUPPORTED DOCUMENT TYPES',
         retainedBeforeReset > 0
           ? (uploadedDocCount + ' UPLOADED SINCE THE RESET, ' + retainedBeforeReset + ' RETAINED')
           : (uploadedDocCount + ' UPLOADED ON THIS PROJECT')],
```

`retainedBeforeReset` counts `signals_extracted` events that precede the project's reset window
(`neural_flow.js:488-493`). Both figures are live-data. **75 + 25 = 100 is arithmetically
consistent with §4.3's 100**, which is the reading the code's own structure supports: 100 total
document rows, of which 75 fall inside the current post-reset window and 25 are retained from
before it. **I did not verify that against data and label it an inference, not a measurement.**

The comment at `neural_flow.js:475-486` records why the retained figure was added — a measured
case where a project reset after 24 uploads reported "0 UPLOADED ON THIS PROJECT" while the server
still held every document and later computed 41 modules from them.

### 4.5 The 11 categories in the Signal Ledger against 12 in the Executive Brief — BOTH COMPUTED, AND THE DIFFERENCE IS GOVERNED

**11** is `projectCats().length` (`detail.js:33-39`), the taxonomy minus portfolio-level
categories. **12** is the whole taxonomy including `d1 Portfolio Health`.

Derived mechanically from `assets/js/taxonomy.js`:

| Category | Name | Modules | Level |
|---|---|---|---|
| a1 | Cost and EVM Performance | 11 | project |
| a2 | Schedule Performance | 11 | project |
| a3 | Cost Risk | 9 | project |
| a4 | Document-Derived Condition Signals | 10 | project |
| a5 | System Dynamics and Complexity | 8 | project |
| a6 | Delivery Quality Performance | 4 | project |
| b1 | Signal Synthesis | 4 | project |
| b2 | Evidence Combination | 20 | project |
| b3 | Regulatory and Authority Thresholds | 5 | project |
| b4 | Decision Optimization | 7 | project |
| c1 | Data Integrity | 7 | project |
| **d1** | **Portfolio Health** | **5** | **portfolio** |

The rule is stated at `detail.js:17-31`:

> Group D is PORTFOLIO LEVEL. Its one category, Portfolio Health, detects patterns ACROSS projects
> and requires more than one by definition; its five modules all declare
> `required: ['portfolioVectors']`. They cannot compute for a single project and they do not
> belong on a single project's page.

and the same rule is enforced server-side at `server/app/simulation/compute.py:26-37`
`contributes_to_project_status(group)` → `return group not in ("C", "D")`.

**So 11 is authoritative for a single project's page and 12 for the taxonomy as a whole.** The
difference is governed and intentional.

**However — a live inconsistency in the brief path, recorded not acted on.** The brief's prompt
text at `detail.js:1601` correctly inserts `projectCats().length` (= 11), but the instruction at
`detail.js:1607` tells the model:

```
"Do NOT mention category numbers except when grouping them in Signal Pattern; a program director
 does not think in Cat 1-12."
```

**"Cat 1-12" appears in the prompt sent to the model.** The Executive Brief is
LLM-generated prose, so a "12" appearing in a rendered brief beside a ledger showing 11 is
consistent with that string reaching the model. **This is a plausible mechanism, not a proven
one** — I could not reproduce the render, so I label it an inference.

### 4.6 The actual registered counts by group, and the taxonomy the prompt states

Derived **mechanically from the live registry**, not from prose:

```
$ python3 -c "from app.simulation import registry as R; …"
registry rows (live, non-RETIRED): 101
by group: {'A': 53, 'B': 36, 'C': 7, 'D': 5}
CSV_PATH: /home/user/LinPRojectRadar/p0-baseline/module_renumbering_map.csv
```

and independently from the browser taxonomy `assets/js/taxonomy.js`:

```
by group: { a: 53, b: 36, c: 7, d: 5 }   total 101
```

| Group | Live registry | Live taxonomy.js | Prompt §4.5 states |
|---|---|---|---|
| A | **53** | **53** | 52 |
| B | 36 | 36 | 36 |
| C | 7 | 7 | 7 |
| D | 5 | 5 | 5 |
| **Total** | **101** | **101** | 100 |

**FINDING: Group A holds 53 modules, not 52. The registered total is 101, not 100.** Both the
prompt's taxonomy and — independently — the repository's own comment at `assets/js/detail.js:19`
(*"`LIN_CATEGORIES` is the whole taxonomy: Group A 52 modules, Group B 36, Group C 7 and Group D
5"*) state 52. **The prose is wrong in both places; the two executable authorities agree on 53.**

This is the ninth occurrence of the class the dispatching agent warned about (a stated set
disagreeing with the derived set). Note that the freeze gate itself derives correctly:
`research/freeze/run42_successor_freeze_gate.csv` row B02 reads
*"registered total=101 expected 101"* and PASSes. **The defect is confined to prose.**

**The 101 vs 100 distinction is real and governed**, not a rounding: the registry declares 101
modules, of which **100 are "scientific targets"** and 1 (`A4.1`) is unported. See §5.

---

## 5. Module activation state

All figures in this section are **derived mechanically from the live registry**
(`server/app/simulation/registry.py` over `p0-baseline/module_renumbering_map.csv`), not read from
any narrative.

### 5.1 The classification function

`server/app/simulation/registry.py:301-319`:

```python
def activation_state(new_id: str) -> str:
    if new_id in DISABLED_CONCEPT_ONLY:
        return "DISABLED_UNSAFE"
    if new_id in DISABLED_EVIDENCE_UNDER_REVIEW:
        return "DISABLED_EVIDENCE_UNDER_REVIEW"
    if new_id in DISABLED_CANONICAL_INPUT_NOT_GOVERNED:
        return "DISABLED_INSUFFICIENT_INPUT"
    if new_id in CORE_VOTING_MODULES:
        return "ENABLED_QUALIFIED"
    return "ADVISORY_ONLY"
```

Its docstring states the classification *"changes no arithmetic and is not itself consulted by
`run_module()`'s abstention contract except for the disabled set, which is short-circuited
explicitly"*.

### 5.2 Derived totals over all 101 registered modules

```
activation_state totals:
  ADVISORY_ONLY                    89
  DISABLED_UNSAFE                   8
  DISABLED_EVIDENCE_UNDER_REVIEW    1
  DISABLED_INSUFFICIENT_INPUT       1
  ENABLED_QUALIFIED                 2
                                  ---
                                  101
```

Supporting set sizes, each read from the live module:

| Set | Size | Members / note |
|---|---|---|
| `DISABLED_CONCEPT_ONLY` | 8 | → `DISABLED_UNSAFE` |
| `DISABLED_EVIDENCE_UNDER_REVIEW` | 1 | its own state; "this module is not being called unsafe" (`registry.py:310-311`) |
| `DISABLED_CANONICAL_INPUT_NOT_GOVERNED` | 1 | its own state; canonical input contract not governed (`registry.py:312-314`) |
| `DISABLED_MODULES` (union) | **10** | `registry.py:147` |
| `CORE_VOTING_MODULES` | **2** | `['A1.7', 'A1.8']` |
| `PROXY_QUALIFIERS` | **1** | see §5.4 |
| `HELD_NON_VOTING_UNSOURCED_BANDS` | 5 | |
| `BAND_SOURCES` | 2 | |
| `VALIDATED` (single-project computable) | 95 | |
| `PORTFOLIO_VALIDATED` | 5 | Group D |
| `unported_modules()` | **1** | `['A4.1']` |

95 + 5 + 1 unported = 101. Consistent.

### 5.3 The per-module table, and why it is presented by class rather than by row

Prompt §5 asks for a row per registered module. **101 rows would be transcription of a CSV that is
already in the repository** (`p0-baseline/module_renumbering_map.csv`) and would add no evidence.
The information content is the *classification*, which is total and mechanical: every module not
named in one of the three disabled dicts and not in `CORE_VOTING_MODULES` is `ADVISORY_ONLY`. The
table below therefore gives the classes exhaustively; the identifier→canonical-name mapping is the
CSV itself, and the runtime lookup is proved total by freeze gate row B10 (*"runtime lookups
failing across all 101 registered modules: none"*, PASS).

| Class | Enum value | Count | Votes into project status? | Character |
|---|---|---|---|---|
| Core voting | `ENABLED_QUALIFIED` | **2** (`A1.7`, `A1.8`) | **Yes** | active and voting |
| Advisory | `ADVISORY_ONLY` | **89** | No | advisory, non-voting |
| Disabled, concept-only | `DISABLED_UNSAFE` | **8** | No | disabled |
| Disabled, evidence under review | `DISABLED_EVIDENCE_UNDER_REVIEW` | **1** | No | disabled |
| Disabled, canonical input not governed | `DISABLED_INSUFFICIENT_INPUT` | **1** | No | disabled |

**Not-relevant-by-applicability-rule is a separate axis from activation state**, and it is
enforced at two independent points:
- **Group D (5 modules)** is refused on the single-project path — `registry.py:395` `run_module()`
  docstring: *"Group D is a hard error here rather than an abstention"*; and
  `compute.py:35-37` — *"Group D does not appear here at all: the registry refuses it on a
  single-project path."*
- **Group C (7 modules)** is `ADVISORY_ONLY` and computes, but **does not vote**:
  `compute.py:26-37` `contributes_to_project_status()` returns `group not in ("C", "D")`, with the
  reason at lines 30-33 (*"It measures how trustworthy the evidence base is … Early reporting
  periods carry the least evidence, so folding it into status would make every early scenario read
  worse for reasons that have nothing to do with the project."*). Freeze gate row B07 confirms:
  *"group C contributes to project status: False"*, PASS.
- **`A4.1` (1 module)** is unported — implemented nowhere. Run 42 classified it `D4 —
  CORRECT_ABSTENTION`.

**Governed abstention vs failure.** The live abstention census, from freeze gate row B06, taken
by executing every module rather than by reading a table:

```
census {'ABSTAINS': 89, 'COMPUTES': 5, 'SUPPLIED_NOT_COMPUTED': 1, 'PORTFOLIO_ROUTE': 5};
populated analytical results 3: ['A1.7', 'A1.8', 'A6.2']
```
with `unexpected execution exception` count **0**, PASS. **Every abstention on the controlled
corpus is a governed abstention; none is a failure** — that is precisely what a zero
unexpected-exception count against a full census establishes. Abstention reasons are persisted per
row: `ComputedResult.abstained` (`research_models.py:668-671`) holds
`[{module_id, reason}]` *"verbatim from `run_all()`'s own `abstained` list"*, and its comment warns
that NULL *"means 'no reason on record', not 'nothing abstained'"*.

### 5.4 Comparison against the recorded post-remediation state — TWO DISAGREEMENTS

| Recorded state (prompt §5) | Derived from live code | Verdict |
|---|---|---|
| 8 disabled | **10 disabled** | **DISAGREES** |
| 30 advisory proxies | **1 proxy qualifier**; 89 advisory modules | **DISAGREES** |
| 12 newly wired | *no live counter for this class exists* | **not determinable from the repository** |
| 2 voting | **2 voting** (`A1.7`, `A1.8`) | **AGREES** |

**Disagreement 1 — disabled is 10, not 8.** 8 is the size of `DISABLED_CONCEPT_ONLY` alone. Two
further modules were disabled afterwards into *their own states*, deliberately not folded into
`DISABLED_UNSAFE`: `DISABLED_EVIDENCE_UNDER_REVIEW` (added by Run 16 —
`registry.py:310-311`: *"Its own state, not DISABLED_UNSAFE: this module is not being called
unsafe"*) and `DISABLED_CANONICAL_INPUT_NOT_GOVERNED` (added by the Run 36 closure —
`registry.py:312-314`). The union is `DISABLED_MODULES` at `registry.py:147`, **len 10**.
**"8 disabled" was true when it was recorded and has been superseded twice.**

**Disagreement 2 — one proxy qualifier remains, not thirty.** `len(PROXY_QUALIFIERS) == 1`.
The dictionary's docstring at `registry.py:348-354` still describes *"the thirty relabeled
proxies"*, and `registry.py:283-298` records why the others were withdrawn — Run 33 removed a
qualifier because *"the cohort refuses to rank below three eligible projects and carries an
explicit small-sample limitation below ten. Leaving the sentence in place would advertise a
weakness the code no longer has"* — with the history preserved in
`code_audit/run33_proxy_qualifier_withdrawal.csv`. **The count moved; the docstring beside it did
not.** Recorded, not fixed.

**I verified the derived figures**, by importing the live registry and counting, and I report both
sides as required. The 89 advisory modules are the correct current answer to "how many are
advisory and non-voting"; 30 was never that number in the current code — it counted *relabeled
proxies*, a strict subset.

**Voting count is independently gated:** `research/freeze/run42_successor_freeze_gate.csv` row B09
*"voting count is not exactly 2 … CORE_VOTING_MODULES = ['A1.7', 'A1.8']"*, PASS.

---

## 6. The period mechanism, as it exists today

Every item below states whether I **read** the code or **inferred** it, and quotes the decisive
lines. This describes what the code does now, not what it should do.

### 6.1 The upload flow — READ

**How a period is chosen:** `server/app/documents.py:153-184`, `_resolve_period()`. Three arms, in
precedence order:

```python
assignment, _decision, _package = project_decision_state(session, project)
if assignment is not None:
    from .research_decision import current_period
    derived = _period_number(current_period(session, assignment))
    if derived is not None:
        return derived, None
supplied = _period_number(payload.get("period"))
if supplied is None:
    chosen = _parse_iso_date(payload.get("period_end") or payload.get("periodEnd"))
    if chosen is not None:
        return period_for_end_date(session, project, chosen)["period"], None
    return 1, None
if supplied < 1:
    return None, err("period must be 1 or greater")
return supplied, None
```

1. **Research chain:** period is **server-derived and the payload is ignored entirely**. The
   docstring states the reason: *"A client-supplied period would let a participant write into a
   period they have not reached."*
2. **Explicit number:** used, validated `>= 1`.
3. **Calendar path:** `period_for_end_date()` (`documents.py:257-298`) maps a chosen *ending date*
   to a period number. The rule (line 268): *"THE PERIOD is the earliest one whose stated ending
   date falls on or after the [chosen date]."* Its docstring names it *"the same function the
   picker previewed with, so the period a person was shown before uploading is the period the
   upload actually writes to."*

**CAN THE SELECTOR BE DEFAULTED OR SKIPPED? On the operational path, YES — recorded, not acted on.**
Two independent defaults land on **period 1**:

- Server: `documents.py:181` — with no `period` and no parseable `period_end`, `return 1, None`.
  The docstring calls this deliberate: *"An operational project has no assignment and therefore no
  derived period, so the payload is consulted, defaulting to 1. That is not a weakening of the
  rule: there is no research sequence to write into."*
- Client, Files tab: `assets/js/files.js:340-343`:
  ```js
  var numEl = $("ws-files-period");
  var pnum = numEl ? parseInt(numEl.value, 10) : 1;
  if (!isFinite(pnum) || pnum < 1) pnum = 1;
  ```
  with the comment directly above recording the historic consequence: *"This call sent no period
  at all, so the server's default filed every document the Files tab has ever taken into period
  one."*

**On the research chain the period cannot be skipped or defaulted — it is not client-supplied at
all.** The distinction matters and I do not collapse it.

**What is persisted:** `documents.py:2004` writes `DocumentUpload(project_id=project.id,
period=period, ...)`, and `documents.py:1575` carries `period=period` onto the computed result.
`period_end` is stored on the upload row and is NULL when no date was stated.

### 6.2 The storage schema — READ

Four tables bind a document or a fact to a project and a period. All in
`server/app/research_models.py`.

| Table | Binding columns | Note |
|---|---|---|
| `documents` (`:501`) | **none** — keyed on `sha256` only | *"One row per UNIQUE FILE, ever — keyed on the sha256 of the bytes."* Deliberately period-free and project-free: *"Two PMs who upload the identical file get byte-identical signalInputs because they are reading the SAME extraction row"* (`:505-509`). |
| `document_uploads` (`:547`) | `project_id` (FK, indexed), **`period: Integer, nullable=False`** (`:563`), `document_id` (FK) | *"One row per upload EVENT … Keeping these separate is what makes 'which documents does this project hold for period 2' answerable"* (`:549-554`). Also `period_end`, `uploaded_by` (*"From the session, never the request body"*), `uploaded_at`, `was_cached`. |
| `observations` (`:673`) | `project_id` (FK), **`period: Integer, nullable=False`** (`:695`), `document_id` (FK, **not nullable**), `field`, `entity_key` | *"One observation per (project, period, document, field, entity). Append-only."* Plus `as_of` — *"the date the value speaks about, taken from the document's own date fields and NULL when none parses — **never the clock**"* (`:686-687`) — and `revision_of`. |
| `computed_results` (`:620`) | `project_id` (FK), **`period: Integer, nullable=False`** (`:641`) | *"One row per (project, period) computation. Every surface downstream READS this; none of them recompute."* Also NOT NULL `simulation_version`, `seed`, `period_cutoff` — *"A stored result without them cannot be reproduced."* |

`ProjectSnapshot.period` (`server/app/models.py:94`) is `Text, nullable=True, index=True` — a
different, nullable, string-typed period column on the snapshot table. **Recorded as an
observation:** the four governed tables type `period` as non-null `Integer`; this one is nullable
`Text`. I did not investigate whether that matters.

**Every fact-bearing row carries `document_id` NOT NULL.** That is the structural property the
lineage path (§6.7) depends on.

### 6.3 The extraction path — READ

`server/app/extraction_merge.py` `emit_observations()` is the single writer. Per
`research_models.py:678-681`, observation rows are *"DERIVED from stored extractions by
`extraction_merge.emit_observations` and persisted at upload and compute time, so a stored row can
always be re-derived and compared."*

**Period is bound before extraction runs.** Run 42 measured this rather than assuming it —
`REPORT_2026-08-21_period-binding-mechanism-repair.md` §1:

> | Document date and filename do not reach the period | INTACT | period is bound before extraction |
> | Extraction completion order cannot reach the period | INTACT | the period is bound before extraction runs |

**Date fields written:** `as_of` per observation, from the document's own date fields, NULL when
none parses, **never the clock** (`research_models.py:686-687`). `docDate` is derived, not stored
raw: `extraction_merge.py` (immediately after `select_signal_inputs`'s field loop) —
*"docDate is DERIVED: the latest as_of among the period's eligible observations — the same rule
`_derive_cutoff` applies to the document set, so 'as of when' has one answer."*

`kind` is declared **per field, not per document type** (`research_models.py:682-685`):
*"a pay application is a series source for CPI and an event source for a change record from the
same extraction."* Permitted values are constrained in the database:
`CheckConstraint("kind IN ('SNAPSHOT','EVENT','DELTA','PERMANENT')")`.

**Out-of-order equivalence is proved, not assumed** — the same project uploaded into two fresh
databases as `P1,P2,P3,P4` and `P4,P1,P3,P2` produced **byte-identical** derived analytical state
after normalising only ULIDs and wall-clock stamps
(`code_audit/run42_outoforder_equivalence.json`).

### 6.4 The retrieval path — READ

`server/app/extraction_merge.py:897` `select_signal_inputs(observations, cutoff)`.

**What a module asks for:** it does not query. `documents.py:466` selects the period's
observations —

```python
.where(Observation.project_id == project.id, Observation.period == period)
```

— an **exact** period match, then `documents.py:1231` calls `si = select_signal_inputs(observations, cutoff)`.

**What it receives:** a flat `signalInputs` dict, selected at a cutoff. The function is **pure**
and its selection rule is:

```python
"""The flat ``signalInputs`` dict, selected from observations at a cutoff. Pure.

Every selection is ``as_of <= cutoff`` (undated observations pass — refusing them would
silently blank most fields; D3 remains the open item it was). Recomputing an earlier
period with its stored cutoff therefore reproduces it even after later-dated evidence
arrives.
"""
eligible = [o for o in observations
            if cutoff is None or o.get("as_of") is None or o["as_of"] <= cutoff]
```

**RECORDED, NOT ACTED ON: undated observations always pass the cutoff.** The docstring names this
as a known open item ("D3 remains the open item it was") and states the reason for the choice —
refusing them would blank most fields. It is a governed choice with a recorded rationale, not a
silent one.

Per-field selection is by declared `kind` (`PERMANENT` / `EVENT` / `SNAPSHOT` / `DELTA`), with
`DELTA` summed *"within the period, never across, never mixed with a SNAPSHOT of the same
quantity"*. `EVENT` counting has an explicit anti-double-count rule: *"Latest non-superseded
record per entity IS that entity's record; the aggregate is over entities, so a revision never
becomes a second event."*

**One deliberate cross-period read exists, and it is scoped and reasoned.**
`documents.py:2336-2341`:

```python
Observation.period <= period,
Observation.source_doc_type.in_(("contract_value", "change_order")),
```
with the reason at `documents.py:2331-2335`: *"Read from the observation store, across all periods
up to this one, because the baseline is a fact about the project, not about one period's
uploads."* It is bounded above by the period being computed (`<= period`, never `> period`) and
restricted to two document types. **This is a baseline read, not a leak.** Run 42's suite section 3
recorded *"No cross-period retrieval … zero leaks"* and *"No cross-project retrieval … zero leaks"*
for the analytical path.

### 6.5 The rollup path — READ

`server/app/simulation/compute.py:114-175`.

**Module results → category status.** Signals are grouped by category, then fused:

```python
for cat, signals in sorted(by_category.items()):
    fused = fuse_signals(fuse_qualified(signals))
    …
    category_statuses[cat] = {
        "status": fused["status"] if fused else None,
        "conflict": fused["conflict"] if fused else 0.0,
        "group": group,
        "module_count": len(signals),
        "contributes_to_project_status": contributes_to_project_status(group),
        "lineage_bodies": list(bodies),
        "lineage_body_count": len(bodies),
        "lineage_declared": bool(fused and fused["lineage_declared"]),
        "within_lineage_disagreement": …,
    }
```

**Categories → project status.** Only categories whose group contributes are eligible, and each
carries its lineage forward:

```python
voting = [{"status": c["status"], "module_id": cat,
           "lineage": lineage_record(cat, lineage_group_ids=category_bodies.get(cat, ()))}
          for cat, c in category_statuses.items()
          if c["status"] and c["contributes_to_project_status"]]
project = fuse_signals(voting)
```

with the governing comment at `compute.py:138-141`: *"A category's fused status INHERITS the bodies
of evidence behind it, so two categories that rest on one body cannot corroborate each other at the
project level either. With one voting category today this changes nothing; it is written now
because the alternative is a second place that has its own opinion about dependence."*

**Which surfaces read which.** All of them read the stored row; none recompute
(`research_models.py:622` — *"Every surface downstream READS this; none of them recompute."*). The
naming and conflict semantics are derived by **one shared pure function on both the compute and
read paths**, `compute.py:152` and `documents.py:1695` both calling
`governed_status_semantics(category_statuses, …)`, with the reason at `compute.py:148-151`:
*"derived by the same pure function the read path uses, so a freshly computed response and a
stored row read back can never disagree about what the rollup is called."*

`project_conflict` is `None` rather than `0.0` when unestimable, *"so a consumer that prints it now
prints nothing instead of printing a zero it would have read as independent agreement"*
(`compute.py:167-170`).

### 6.6 The longitudinal path — READ

**How it decides it has enough periods:** `_earlier_live_results` supplies the series, and the
consumers gate on its length.

`server/app/documents.py:1063-1086`:

```python
def _earlier_live_results(session, project, period) -> list[ComputedResult]:
    """
    This project's live stored results for STRICTLY EARLIER reporting periods, in period order.

    THE ONE READ every cross-period series on this platform is assembled from, and the one place
    the period-alignment invariant is enforced. `period < period` is evaluated against the period
    being computed, so recomputing period 1 while periods 2, 3 and 4 exist reads none of them and
    reproduces what period 1 was computed from. …
    Live rows only: a superseded result has been replaced by a recompute of that same period …
    """
    return list(session.scalars(
        select(ComputedResult)
        .where(ComputedResult.project_id == project.id,
               ComputedResult.period < period,
               ComputedResult.superseded_by.is_(None))
        .order_by(ComputedResult.period)
    ).all())
```

**What it orders by: `ComputedResult.period` — reporting-period identity, not timestamp, not
insertion order, not ULID.** Filtered to `superseded_by IS NULL`.

**The sufficiency thresholds** are in `server/app/simulation/portfolio.py`:
- **≥ 2 periods** for trend/trajectory: `portfolio.py:193` `if len(history) >= 2:`,
  `:198` `if len(cpi_values) >= 2:`, `:247` `if len(history) >= 2 and trend != 0:`.
- **≥ 3 projects with signal data** for the portfolio arm: `portfolio.py:11` —
  *"fewer than 3 with signal data returns insufficient_data with an empty result set"* — with the
  refusals at `:123`, `:135`, `:140` returning `_insufficient(...)`.
- Insufficiency is **never coloured**: `portfolio.py:186` records that the legacy Apps Script
  *"emitted status_color 'Green' beside insufficient_data: true here"*, and the current code does
  not.

`_period_snapshots` (`documents.py:1089+`) records that this was previously broken and by how much:
*"Until now every caller passed a literal `None`, so both of its `len(history) >= 2` guards were
permanently false and the Signal Trajectory Classifier abstained on every project ever computed …
Nothing was missing from storage: each period already stored its own cpi, and nobody had joined
them."* It also fixes the series' right-hand end deliberately: *"THE CURRENT PERIOD IS THE LAST
ELEMENT … a series that stopped at the previous period would report last period's trajectory as
this period's."*

The docstring explicitly contrasts the current rule with the historic **P1 defect**: *"deliberately
NOT the shape of the P1 defect, where a portfolio vector was chosen by `max(period)` with no
alignment to the period being computed and a stored period-1 result changed when another project
reached period 2."*

### 6.7 The lineage path — READ

**Yes, a computed result stores the documents its inputs came from — in two places, at two
granularities.**

**Result granularity:** `ComputedResult.source_documents`
(`server/app/research_models.py:663-667`):

```
# 0013. Which document VERSIONS produced this result: a list of
# {document_id, sha256, doc_type, filename}, in the order assembly consumed them.
#
# `signal_inputs.sources` records a docType per field and never a document, so before this
# column a result could not answer "which version of the pay application produced this
# status" once the period's document set had moved on. NULL on rows computed before 0013.
```

Written at `documents.py:1583` (`source_documents=source_documents`), read back at
`documents.py:1720`, and used for staleness at `documents.py:2553`: *"Staleness is decided by
comparing the stored result's `source_documents` …"*, which refuses to guess —
`documents.py:1005`: *"no source_documents record on the stored result; left untouched"*.

**Field granularity:** repaired by Run 42 as defect **D1**. `extraction_merge._source_entry(w)`
now carries `documentId`, `documentVersion` (the content-addressed sha256), `asOf` and
`revisionOf`, *"omitted rather than written as null when the observation does not carry them, so a
document with no identity still produces an honest record"*.

**Before that repair, the per-field record was `{docType, value}` and dropped everything else**,
with a measured consequence:
`REPORT_2026-08-21_period-binding-mechanism-repair.md` §2 D1 —

> `qualification._provenance` counts a field as traced only when it carries BOTH a document
> identity and a document version, so it counted **zero on every project ever computed**;
> `_timeliness` counts `asOf` and was pinned the same way. … The evidence was in storage the whole
> time; one hop lost it.

After the repair: *"7 of 7 sourced fields now name the artefact they came from, every named
artefact is one of that period's own documents, provenance and timeliness reach PASS."*
`code_audit/run42_baseline_state_chrono.json` holds the pre-repair state.

**Category and project granularity:** lineage propagates upward — `lineage_bodies`,
`lineage_body_count`, `lineage_declared` and `within_lineage_disagreement` on every category status
(`compute.py:122-135`), and `lineage_record(...)` on each voting entry (`compute.py:139-141`).

**One deliberate lineage gap, recorded:** a counted `EVENT` ledger writes **no** `sources` entry —
`extraction_merge.py`, EVENT branch: *"Deliberately NO sources entry for a counted ledger, matching
the legacy additive branches that bypassed setField."* The value is a count of entities, not a
reading from one document, so there is no single artefact to name.

---

## 7. The live PRJ-001 data, as stored — NOT DETERMINABLE FROM THE REPOSITORY

**This section stops here, as prompt §7 instructs.**

**`PRJ-001` does not exist anywhere in this repository.**

```
$ grep -rl "PRJ-001" . --exclude-dir=.git | wc -l
0
```

Zero files, in any extension. The project identifiers that do exist are of two shapes:

```
$ grep -rho "PRJ-[A-Z0-9]*" . --exclude-dir=.git | sort | uniq -c | sort -rn | head
   7476 PRJ-HSP     6560 PRJ-AIR
   7449 PRJ-HWY     6529 PRJ-DCT
   7443 PRJ-RAL     6503 PRJ-WTR
```
(the six controlled-stimulus scenario projects), plus ULID-suffixed operational ids such as
`PRJ-5D7EXY5CJ5`.

**The only database reachable from this session is `server/dev.db`**, a development artifact
holding 8 projects, **2 documents, 3 upload rows, 2 computed results and 12 observations** — none
of them `PRJ-001`, and nothing resembling a 100-document project. `DATABASE_URL` is unset in this
session. **Production Postgres was not touched and must not be** (prompt §2 hard limit 2,
§11.2 stop condition).

Accordingly, **every one of prompt §7.1 through §7.6 is "not determinable from the repository"**:

| §7 item | Answer |
|---|---|
| 7.1 per-document period at upload / period now / doc date / upload timestamp | **Not determinable.** No such rows exist here. |
| 7.2 whether the four periods are distinguishable in stored data | **Not determinable.** |
| 7.3 upload flow vs downstream persistence defect | **Not determinable**, and I will not assign a cause without the data. §6.1 records that *a* period-1 default exists on the operational path, which is a mechanism by which such a collapse *could* occur — but a mechanism is not evidence that it did, and I do not present it as one. |
| 7.4 every value reaching `ev`, `ac`, `pv`, `bac` per period, with document and field | **Not determinable.** |
| 7.5 stored CPI and SPI per period and their arithmetic | **Not determinable.** |
| 7.6 whether Document Risk Score has a stored value | **Not determinable.** |

**§7.6, partial answer available from code only.** The prompt asks *where* a printed `0.00` would
be produced. Two candidate sites, both read, neither confirmed against data:

- `assets/js/detail.js:1521-1524`:
  ```js
  const docScore = Number(s.doc && s.doc.score != null ? s.doc.score : si.docRiskScore);
  if (Number.isFinite(docScore)) {
    out.push({ label: "Document risk", value: docScore.toFixed(2),
               status: docScore >= 0.70 ? "Red" : docScore >= 0.40 ? "Amber" : "Green" });
  }
  ```
  `Number(null)` is `0`, which is finite, so **a `docRiskScore` of `null` renders as `"0.00"` with
  a Green status**, whereas `undefined` yields `NaN` and is correctly omitted. Recorded as an
  observation about a null/zero conflation; **not fixed, not ranked.**
- `assets/js/signals.js:535-536`:
  ```js
  const docRisk = si.docRiskScore != null ? si.docRiskScore
                : (si.docRisk != null ? si.docRisk : 0);
  ```
  substitutes `0` for an absent score when building the portfolio vector.

Both sit **against** an explicit server-side rule that zero is a real reading —
`server/app/extraction_merge.py:1128`: *"a genuine 0 must be STORED (sim treats it as absent)"*.
**I did not determine which of these produced the observed 0.00, and I did not guess.**

**I did not substitute the site render's document table**, as prompt §7 and the dispatch both
require.

---

## 8. Test suite condition

### 8.1 Every test suite in the repository

**188 suites**, all matching `server/tools/test_*.py`:

```
$ ls server/tools/test_*.py | wc -l
188
```

The runner is **`server/run_all_suites.sh`** (not at repository root). It builds one migrated
SQLite template with `alembic upgrade head` and **copies it per suite** — its header states why:
*"A stale/shared db silently swallows failures (KeyError, no RESULT: line) so this never reuses one
across files."* `DATABASE_URL=:memory:` was **not** used at any point.

There are also two browser harness pages at the repository root (`tests.html`,
`tests_render.html`). They are not part of `run_all_suites.sh` and **were not run** — no browser
session was opened in this survey. Their condition is **not determinable from this session**.

### 8.2 Results

Run with `PYTHONIOENCODING=utf-8` (exported per suite by the runner at line 31) and a fresh
migrated SQLite database copied per file:

```
$ cd /home/user/LinPRojectRadar/server && bash run_all_suites.sh
…
====================================================
Suites run: 188   Total checks: 14176/14176
ALL SUITES GREEN
EXIT=0
```

| Outcome | Count |
|---|---|
| **Pass** | **188** |
| **Fail** | **0** |
| **Error** | **0** |
| **Printed no canonical `RESULT:` line** | **0** |

Verified independently of the runner's own summary:

```
$ grep -c '^ok '           suites.log  → 188
$ grep -c '^FAIL'          suites.log  → 0
$ grep -c 'NO CANONICAL'   suites.log  → 0
```

**No suite is reported as passing on the strength of a missing result line.** The runner accepts
only the anchored form `^RESULT: [0-9]+/[0-9]+( checks passed)?$` and treats a green result line
with a nonzero exit code as a failure (`run_all_suites.sh:54-57`). Every one of the 188 produced a
canonical line and exited zero.

Suites material to this survey, individually:

| Suite | Result |
|---|---|
| `test_run38_frozen_immutability.py` | 17/17 — the byte-identical guard (§3.6) |
| `test_run39_frozen_immutability.py` | 19/19 |
| `test_run37_freeze_gate.py` | 30/30 |
| `test_run39_launch_gate.py` | 100/100 |
| `test_run42_period_binding_mechanism.py` | 131/131 — the §6 mechanism |
| `test_run41_security_acceptance.py` | 11/11 |
| `test_run40_serve_content_security.py` | 11/11 |
| `test_run6_known_answer.py` | 488/488 |

### 8.3 Which suites have been proved able to fail by injection — from the repository record

**Nothing was injected in this survey.** The record consulted is the fault-campaign and
mutation-proof artifact set under `code_audit/` — **33 fault-injection/campaign CSVs** plus the
mutation-proof and harness-failure-proof CSVs, spanning run10 through run42.

Extracting every suite filename named in those artifacts:

```
$ grep -rho "test_[a-z0-9_]*\.py" code_audit/*fault*.csv code_audit/*mutation*.csv \
      code_audit/*harness_failure*.csv | sort -u | wc -l
29
```

**29 suites are named by filename in the injection record. 159 of the 188 are not.**

**That figure requires a caveat and I give it rather than reporting the number bare.** Several
campaigns identify their oracle by a *name* rather than a filename, so a suite can be covered
without appearing in the grep above:
- `code_audit/run41_fault_campaign_results.csv` names its oracles `s1` / `s2`, not filenames.
  Those correspond to `test_run40_serve_content_security.py` and `test_run41_security_acceptance.py`.
- `code_audit/run42_fault_campaign.csv` names *sections* of one suite
  (`test_run42_period_binding_mechanism.py`) and reports check counts, not the filename.

**So the honest statement is: 29 suites are named directly in the injection record; a small further
number are covered under oracle aliases; and the majority of the 188 have no injection record at
all under either form.** An exact covered/uncovered partition would require reading all 33 campaign
CSVs against all 188 suite files — **not determinable within this survey's scope**, and I do not
estimate it.

The 29 named directly:

```
test_courses_of_action.py            test_run22_production_tree_completeness.py
test_document_rows.py                test_run23_signal_flow_truthfulness.py
test_risk_register_and_notices.py    test_run24_empty_project_diagram.py
test_run11_defensibility_claims.py   test_run26_counts_and_wiring.py
test_run14_disabled_method_functional.py   test_run28_closure.py
test_run17_scientific_methods.py     test_run28_participant_packages.py
test_run20_cycle8_arch3_clusters.py  test_run28_version_boundary.py
test_run20_declared_production_changes.py  test_run30_canonical_oracles.py
test_run31_pass2_acceptance.py       test_run32_cat10_oracles.py
test_run32_client_authority.py       test_run32_closure_version_boundary.py
test_run32_defensibility_truth.py    test_run32_handbook_surface.py
test_run32_method_class_agreement.py test_run38_readiness.py
test_run39_launch_gate.py            test_run5_export.py
test_run6_known_answer.py            test_schedule_milestones.py
test_zz_scratch_probe.py
```

The most recent campaign, `code_audit/run42_fault_campaign.csv`, is exemplary of the standard: 6
faults, 5 intended-RED **all caught**, 1 inert control **correctly green**, every fault applied to
the real tree and restored. Fault F5 is the control — *"a suite that fails on an inert edit is
failing for reasons of its own, not because of the defect"*. Fault F6 (period derived from upload
order instead of the caller's selection) failed the suite 2/11 and *"reports 'requested 4, got 1'"*.

### 8.4 Suites asserting against a copy of the logic they test — GENUINELY SEARCHED

The prompt states this class has occurred before; the dispatch says at least five times. I searched
for it rather than assuming absence, and report **what I found and what I did not establish**.

**What I found: the class is recognised and explicitly guarded against, with self-tests.** Fifteen
suites carry language about it. Four read in full:

- `test_run35_validation_governance.py:9-15` states the standard as an invariant of the suite:
  > *"No check asserts against a copy of the logic it is testing. Where a claim is about production
  > behaviour, production is EXECUTED and the returned row is read. No check asserts a defect's own
  > sentence verbatim. A crash is a failure, not a pass."*
  and, critically, *"the CSVs are read from disk as shipped. A guard that rebuilds its subject
  destroys an injected fault before it can be seen."*
- `test_run33_closure.py:6-9`:
  > *"every counter the owner's section 20 requires is recomputed FROM THE LIVE CODE rather than
  > read out of a row. A table that asserted its own contents would be the 'asserted against a copy
  > of the logic' failure this programme has already met."*
- `test_run11_browser_server_authority.py:6-12` rejects a naive parity test by name:
  > *"A parity test that compared a browser band constant with a server band constant would be the
  > fourth way a check has lied here: it would assert against a hand-maintained copy of the logic
  > instead of the logic, and it would pass the moment somebody kept both copies in step while the
  > divergence lived somewhere else."*
  and replaces it with a structural property — *"THERE IS NO SECOND ARITHMETIC SOURCE ON THE
  PARTICIPANT ROUTE."*
- `test_run26_counts_and_wiring.py:98-100` carries an explicit **anti-tautology self-test**:
  ```python
  # SELF-TEST, so the identity above is not a tautology of the subtraction that produced it.
  check("self-test: the identity check can distinguish an unequal pair",
        not (96 + 4 == 101))
  ```

**What I did not establish.** I sampled — 15 suites surfaced by keyword, 4 read closely, plus
targeted searches for suites importing a generator module and for regenerate-then-compare patterns
(20 suites match "regenerate|rebuild", 20+ match `import build_`/`import runNN_`; spot checks
showed these importing *production runners*, not artifact generators). **I did not read all 188
suites' 14,176 checks.** A definitive answer to §8.4 requires a per-check audit of all 188 files.

**Stated plainly: I found no instance of the defect in what I examined, and I did not examine
everything. I am not asserting the repository is clean of it.** Likewise for "a suite that asserts a
known defect as expected behaviour" — I found no instance in the sample, and
`test_run35_validation_governance.py:13` explicitly forbids it, but I did not prove absence.

**One methodological note the repository volunteers about itself**, from
`REPORT_2026-08-21_period-binding-mechanism-repair.md` §7: Run 42 caught a harness error in its own
work — a derivation that *"compared extraction field names against signal-input field names and
reported `earned_value` as unconsumed — a field we already knew reaches `si['ev']`"* — replaced it
with a differential test, and recorded the false result *"here rather than quietly dropped."*

---

## 9. Open items, from the repository

### 9.1 What `T6_HANDOFF.md` says is outstanding

The topmost (and, per §0.5, misleadingly positioned) section is
`# 2026-08-19 - Run 39: MAIN STUDY LAUNCH READY`, whose stated outstanding item is:

> **THE ONE THING TO DO BEFORE THE FIRST REAL PARTICIPANT**
> Add a row to `research/study_execution/dataset_class_registry.csv` with
> `dataset_class = MAIN_STUDY`. **Classification is governed data, never a naming convention.** A
> participant the registry does not name is `UNCLASSIFIED` and can never be exported as
> MAIN_STUDY — forgetting to register someone excludes them, it never silently includes them.

Also outstanding, from the same section: **R is not vendored** — *"Install it in the analysis
environment."*

And six standing facts the handoff says a later run must not unlearn, of which three bear on this
survey:

1. *"A post-final-lock raw-SQL edit to `final_action`, `final_confidence` or `rationale` is
   **WHOLLY UNDETECTABLE**. … The three-way vocabulary is PREVENTED / DETECTABLE /
   OPERATIONALLY_PROHIBITED. **Do not describe this as immutability.**"*
2. *"The deployment has exactly one database credential and no restricted role. Whoever operates
   the study holds unrestricted write access."*
3. *"The AI package is attached PER ASSIGNMENT: all six periods of a project disclose the IDENTICAL
   recommendation. … A participant is genuinely blind only in period 1. This is the ACCEPTED FROZEN
   DESIGN, not a defect."*

Fact 4 of that list is the derive-don't-transcribe warning: *"The analysis dataset has 59 columns,
not 58. The Run-38 report prose said 58 … Derive counts; never transcribe them. (Seventh occurrence
of this class here.)"* **§4.6 of this report records the ninth.**

### 9.2 What the most recent `REPORT_*.md` files say was left not done

From `REPORT_2026-08-21_period-binding-mechanism-repair.md` §8-9:

| Id | Classification | Subject |
|---|---|---|
| D3 | **NEEDS_OWNER_DECISION** | 10 declared extraction fields consumed by nothing (`code_audit/run42_unconsumed_extraction_fields.csv`). *"Mapping them is a scientific design change."* |
| D4 | CORRECT_ABSTENTION | `A4.1` refused as unported |
| D5 | NOT_APPLICABLE_DESIGN_PROJECT | `D1.1`–`D1.5` are portfolio scope |
| — | **NEEDS_OWNER_DECISION** | `revision_resolution_status` pins `overall_qualification_state` to `NOT_ESTIMABLE` for **every project, permanently** |

and three items recorded but deliberately not acted on ("Observations for the professionalization
run"):

- *"`_period_history`'s docstring still describes the P1 portfolio defect as 'queued separately'; it
  was fixed … and the prose is stale."*
- *"`qualification.py` carries a `PROVENANCE_PARTIAL_REASON` phrased as an absolute claim; it is now
  correct only on the PARTIAL branch."*
- *"`code_audit/run39_administrative_authority_boundary.csv` was stale … Regenerated here."*

From `REPORT_2026-08-19_run41-successor-freeze.md`:

> **Observation deferred to Run 42:** the three suites that reached a now-protected column
> (`test_export.py`, `test_admin_ops_t7t8.py`, `test_decision_ui_t4.py`) each demonstrate export
> tamper-detection through a decision column. They are repointed at `pre_assessment`, which is
> exported and unprotected. If a future run protects that too, those demonstrations need a
> non-decision carrier rather than another repoint.

> **No real participant data was collected. Main-study observations remain 0.**

From `REPORT_2026-08-19_run40-fable-functional-security.md:128-129`: `FABLE_ACCEPTANCE_BLOCKED`,
two owner decisions required — **subsequently closed by Run 41** (§3.5).

The standing limitation contract, verbatim from
`research/freeze/RUN42_SUCCESSOR_FREEZE_RECORD.json`:

> `empirical_field_validation`: **0 of 100.** No scientific target in this instrument has been
> validated against an independent observed real-world outcome.
> `calibration`: No calibration set exists in this repository: no labelled outcome corpus and no
> expert reference standard.
> `lineage`: **Unresolved for 77 of 100 targets.** Unknown lineage was never treated as independent.
> `abstention`: Most scientific targets abstain on the controlled corpus: **3 of 100** produce a
> populated analytical result.

### 9.3 `TODO` / `FIXME` markers in code naming an unresolved defect

```
$ grep -rn "TODO\|FIXME\|XXX:\|HACK" --include=*.py --include=*.js \
      server/app assets/js server/tools
   (no output)
```

**None.** Zero markers of any of those forms in production Python, production JavaScript, or the
test tools. Unresolved items in this repository are carried in prose, in report classification
tables (§9.2), and in the freeze record's limitation contract — not in code markers.

### 9.4 Does Regret Minimization still gate the courses of action on the decision card?

**No — and it never could, in the state I found. The module is present, named, and non-voting.**

`B4.7` "Minimax Regret Decision Rule" is registered and appears in four surfaces
(`assets/js/taxonomy.js:216`, `assets/js/categories.js:220`, `assets/js/decision-ui.js:113`,
`assets/js/module_charts.js:91,193`). Its live state:

- **It is `ADVISORY_ONLY`.** It is not in `CORE_VOTING_MODULES`, which is exactly
  `['A1.7', 'A1.8']` — derived from the live registry, and gated by freeze row B09.
- `assets/js/decision-ui.js:113` uses it only as a **display name lookup** inside the
  `MODULE_NAMES` map. No branch in `decision-ui.js` conditions a course of action on it — the only
  `B4.7` occurrence in that file is that dictionary entry.
- `assets/js/ds_defensibility_evidence.js:141` records its operational state:
  `operationalState: "CONDITIONAL_ON_GOVERNED_STRUCTURE"`, `canonicalStructureRequired: true`,
  `definingStructure: "actionScenarioMatrix"`, **`voting: "does not vote"`**, and
  > *"the canonical production runner exists, but execution requires a named defining structure;
  > when that structure is absent the module returns Not Estimable"*
  with `permittedClaim` limited to *"No current project reading is produced without one."*

**So: it neither votes into project status nor gates the decision card; absent a governed
`actionScenarioMatrix` it returns Not Estimable.** Freeze row B08 independently confirms the
Category-10 boundary: *"human_authorization_required True, creates_project_evidence False, and no
Category-10 identity in the voting set"*, PASS.

I did not find evidence that it *ever* gated the card in the current codebase; the question's
premise ("still") is **not determinable from the repository** without a history search I did not
perform.

### 9.5 Does `ds_defensibility_data.js` still carry entries claiming validation, and how many?

**It carries 103 module entries. None of them claims validation. All 103 state validation as
REQUIRED and NOT PERFORMED.**

```
$ grep -c '"validationRequired"' assets/js/ds_defensibility_data.js   → 103
$ grep -o '"[a-zA-Z]*[Vv]alidat[a-zA-Z]*"' … | sort | uniq -c
    103 "validationRequired"
```

There is **no** `validationStatus` key, and no entry asserts validation was done:

```
$ grep -oin "has been validated\|is validated\|empirically validated\|validation performed\
\|externally validated" assets/js/ds_defensibility_data.js
   (no output)
```

The 103 `validationRequired` values fall into four prescriptive templates — 70 / 24 / 7 / 2 — each
of which describes work **to be done**, e.g.:

> *"Verify formula and threshold boundaries; trace each input to provenance; run
> missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later,
> non-confidential field cases; confirm that the output abstains when required inputs are absent."*

and the file's `accreditationBasis` prose is explicitly disclaiming, e.g. line 439:

> *"None of that has been performed on this platform. … It does not establish empirical validation
> or calibration."*

**Answer to the question as asked: zero entries claim validation. 103 entries state validation is
required and unperformed.**

**Two findings recorded:**

1. **103 entries against 101 registered modules — a surplus of 2.** Every one of the 22
   per-module keys appears exactly 103 times, and `"name"` appears **114** times (11 more than 103,
   consistent with 11 category-level or group-level name fields). The live registry holds 101
   modules. **I did not identify which 2 entries are surplus** — that requires diffing the file's
   103 identifiers against the registry's 101, which I did not do. **Not determinable within this
   survey.** It is worth noting that freeze row B05 measures *"100 served statements … against
   EXECUTED behaviour; failing: none"* — **100**, a third distinct population from 101 and 103.
2. **`NAMING_AUTHORITY.md` §1 names this exact file as stale**: *"The codebase contains **PCEIF** in
   roughly 60 places, a chapter titled 'The PCEIF Governance Framework', and
   `ds_defensibility_data.js` written around that framing. Those are stale. **PCEIF is retired.**"*
   Confirmed still live: `assets/js/detail.js:1561` begins a code comment *"PCEIF is a prediction +
   advisory platform"*, in the Executive Brief path. Recorded, not fixed.

---

## Questions this survey could not answer, and what would be needed

1. **Is the deployed site at `https://linprojectradar.onrender.com` running `origin/main`?**
   (§3.7) — Egress is blocked; the host returns proxy `403` and a control host returns `000`.
   **Needs:** network egress to `onrender.com`, or the Render dashboard's deployed-commit field, or
   a build-stamp/version endpoint served by the application.

2. **What population does the site render's `85` count, and is it 85 today?** (§4.2) — It is
   `snapshot.summary.total_modules` for one project-period. **Needs:** read access to the deployed
   `computed_results` row for the rendered project and period.

3. **What produces the site render's `100` documents, and is `75 + 25 = 100` the correct
   decomposition?** (§4.3-4.4) — Both are live-data figures with no constant in code.
   **Needs:** the `document_uploads` and `signals_extracted` event rows for that project.

4. **Does the rendered Executive Brief actually say 12 categories, and did the `"Cat 1-12"` prompt
   string cause it?** (§4.5) — The mechanism is present at `detail.js:1607` but unproven.
   **Needs:** the rendered brief text plus the chat request/response pair for that project-period.

5. **All of §7 — the PRJ-001 stored data.** `PRJ-001` has zero occurrences in the repository and
   does not exist in the only reachable database. **Needs:** a read-only replica or governed export
   of the production `documents`, `document_uploads`, `observations` and `computed_results` rows
   for that project. **Production Postgres must not be touched to obtain it.**

6. **Which specific `0.00` production site produced the observed Document Risk Score?** (§7.6) —
   Two candidate sites identified and quoted; neither confirmed. **Needs:** the stored
   `signal_inputs.doc_risk_score` value for that project-period.

7. **The exact covered/uncovered partition of the 188 suites by fault injection.** (§8.3) — 29 are
   named by filename; an unknown further number are covered under oracle aliases. **Needs:** a
   full cross-read of all 33 campaign CSVs against all 188 suite files, mapping every oracle alias
   to its file.

8. **Whether any of the 188 suites asserts against a copy of the logic it tests, validates a
   generated output against its own generator, or asserts a known defect as expected behaviour.**
   (§8.4) — I sampled and found explicit guards against all three, and no instance in the sample.
   **I did not prove absence.** **Needs:** a per-check audit of all 188 files / 14,176 checks.

9. **Which 2 of the 103 `ds_defensibility_data.js` entries are surplus to the 101 registered
   modules, and how the freeze gate's population of 100 relates to both.** (§9.5) — **Needs:** a
   diff of the file's 103 identifiers against `p0-baseline/module_renumbering_map.csv` and against
   the gate's served-statement set.

10. **Whether Regret Minimization ever gated the decision card** — the "still" in the question.
    (§9.4) — Its current state is fully established (advisory, non-voting, Not Estimable without a
    governed structure). **Needs:** a git history search across `decision-ui.js` and the decision
    card's predecessors.

11. **The condition of `tests.html` and `tests_render.html`.** (§8.1) — Browser harnesses outside
    `run_all_suites.sh`; no browser session was opened. **Needs:** a browser session with a verified
    cwd of `/home/user/LinPRojectRadar`.

---

*End of survey. Nothing in this repository was changed by this run except the creation of this
file. No fix was proposed, written, or begun.*
