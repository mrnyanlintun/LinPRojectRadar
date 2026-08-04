# Training mode, run 1: gating and data isolation

2026-08-04. `training_mode_roadmap.md` did not exist in the repository, on `origin/main`, in git
history, or on disk when this run started; per the brief's own instruction it was not
reconstructed from the task text, and Lin supplied its contents directly. It is now committed.

This run builds **only** the two things that must exist before any training content does: the
flag that turns training mode on, and the isolation that keeps training data out of the research
record. **Nothing in this run generates a training project or advances a period.** No production
migration has been applied; the schema change below (0018) is written and verified against a
throwaway SQLite only, per the standing constraint that a push assuming an unapplied schema has
taken sign-in down once already.

## Leading with the isolation, since that is the part that cannot be retrofitted

**One column, on `projects`: `is_training`, `NOT NULL`, default `false`, indexed the same way
`archived` already is.** Every project that exists today, and every project created before a
later run builds actual training-project generation, resolves to "not training" by construction —
there is no code path yet that could pass anything else. This is the single source of truth
everything else joins back to, rather than a training flag scattered onto every table that might
touch a training project (the roadmap's own reasoning: a duplicated marker is a marker that
drifts the first time one write path forgets to set it).

### The one read path that needed a real filter, and why it is the only one

`project_health` (`research_export.build_module_results_rows`, `project_legacy_ids=None`) pulls
**every** project's `ComputedResult` rows in the date window, with **no `account_type` filter at
all** — the module's own docstring says so: "a project has no account_type of its own." That is
exactly the gap training mode will exercise once it exists: roadmap item 7 says training state
sets `signalInputs` directly and the *existing* computations run unchanged, which means a
training project's `ComputedResult` rows will look identical in shape to a real project's. Before
this run, nothing stood between those rows and `project_health` (json, csv, and xlsx alike, since
all three formats funnel through `build_module_results_rows` — confirmed by reading
`_row_count_for`, `_build_payload`, and `build_workbook`, all three call sites). One `continue`
added there, keyed on `project.is_training`, closes it for every format at once.

`participant_inputs` (`build_rows` / `_eligible_instances`) needed **no code change**, because it
is already closed by construction: every instance is filtered to `participant.account_type ==
"research"` unconditionally, and training mode is operational-only — refused server-side to a
research account whatever the flag says (below). A training decision can never be attached to a
research participant, so there is no row for this filter to admit. Verified, not assumed: the
isolation suite creates a training project and confirms it is absent from *both* export kinds,
not only `project_health`.

### The research chain — assignments, consents, transitions, decision sequence — considered, not touched

None of `assignments`, `consents`, `decisions`, or `transitions` needed a training-isolation
filter, because none of them can structurally hold a training row. `Assignment` links a
`participant_id` to a `scenario_id`; a scenario is created by an admin and names an
**evidence project** (`Scenario.evidence_package_id`). Training mode does not use scenarios —
roadmap items 6–9 describe a separate state store "beside the observations store," not inside the
research assignment machinery. So the only door from a training project into the research chain
is an admin naming one as a scenario's evidence, by mistake or otherwise. That door is now closed
too: `a_adminscenariocreate` refuses a training project as evidence at creation, and
`a_adminassign`'s own re-check (already there, for the case where a project is renumbered after
its scenario was made) refuses it again at assignment time. Both refusals are named explicitly
("... is a training project and cannot be used as research evidence"), not folded into the
generic "not found" message, since an admin acting in good faith needs to know why.

**Table by table, what was touched and what was considered and left alone:**

| Table | Touched | Reasoning |
|---|---|---|
| `projects` | Yes — `is_training` column added | The single source of truth |
| `computed_results` | No column change; read path filtered | No `account_type`; `project_health` reads it unfiltered otherwise |
| `scenarios` | No column change; write path guarded | The only door from a training project into the research chain |
| `assignments` | No | Cannot exist without a scenario; scenarios are now guarded at both write sites |
| `consents` | No | Consent is per participant, not per project; training is operational-only, refused before a research participant is even in the picture |
| `decisions` | No | Anchored on `Assignment`; unreachable once assignments are |
| `transitions` | No | Anchored on `Decision`; unreachable transitively |
| `decision_support_packages` | No | Authored per scenario by a researcher; no training-project linkage exists |
| `observations` | Considered, not touched | Roadmap item 6 puts the future training state store *beside* this table, not inside it; nothing here reads across projects the way `project_health` does |
| `document_uploads` / `documents` | Considered, not touched | Roadmap item 7: training explicitly generates no documents ("No documents, no extraction, no filing") |
| `audit_events` | Not filtered | An audit trail is not an analytical record; a training refusal being audited is itself part of what this run had to prove (see Guarantee 1c below) |

**Not yet decided, and out of this run's scope by the brief's own boundary:** whether a training
project should appear in an *operational* cross-project view — portfolio health
(`getportfoliohealth`), which aggregates `ComputedResult` across every project the caller can
see, is not part of "the research export" or "the research chain," and the roadmap's own Verify
section scopes isolation to the two export kinds. A training project showing up in an operator's
own portfolio dashboard is a product decision for roadmap item 8 ("The screen"), not a research-
contamination risk, and is flagged here rather than decided.

## Part 1: the flag and the gate

**Reused the technical-reviewer (`auditor`) flag pattern exactly**, per the brief's instruction:
`training` is a fifth key in `FEATURE_KEYS` / `FEATURE_LABELS`, resolved by the same
`effective_features` (operational defaults enabled, research defaults disabled), toggled by the
same `adminfeaturesset`/`adminfeaturesget` actions, no third mechanism introduced.

**One real action this run implements, `trainingstatus`** — read-only, returns whether the
caller may use training mode right now. It exists so the "Train" nav item has something real to
ask, and so the gate has something real to probe over HTTP rather than only in the abstract. Five
more actions later runs will need (`trainingstart`, `trainingstate`, `trainingdecision`,
`trainingadvance`) are listed in `GATED_ACTIONS` **before their handlers exist**, the same way
`chat` and `audit` are — the gate already covers them the day their handlers land.

**Two independent refusals for a research account, not one.** `gate_action`'s
`RESEARCH_FORBIDDEN_ACTIONS` set refuses every training action *unconditionally* — not by relying
on the flag defaulting to disabled for research. That distinction matters: nothing in the
codebase stops an admin from writing `training: true` onto a research participant's stored
`features` row (`adminfeaturesset` has no account_type check on the *target*, only on the
caller), and the moment that write happens the default-off protection is gone. The suite proves
this is not hypothetical: it performs exactly that write, then confirms the account is still
refused. `a_trainingstatus` repeats the check inside the handler too, the same defence-in-depth
`a_themeset` already uses, so the refusal does not rest on `gate_action` alone.

**The unauthenticated-caller gap, closed for training specifically.** `gate_action` itself leaves
a sessionless caller alone (documented in its own scope note) — this is the exact shape of gap a
previous session found letting an anonymous `getportfoliohealth` bypass a flag a signed-in user
with it off was held to. `a_trainingstatus` does not rely on `gate_action` for authentication: it
calls `resolve_caller` itself and refuses a missing or garbage token before it ever asks what the
flag says. Probed with both no `session_token` at all and a fabricated one.

## The operational-and-research combination

**It is possible**, and nothing today prevents it: `account_type` is a single column with a CHECK
constraint (`research`/`operational`), so a participant can never hold both at once — but
`a_adminassign` never checks a target's `account_type` before writing an `Assignment` row, and
`research_consent.enforce_consent` has no `account_type` branch either. So an admin *can* assign
an operational account to a scenario and let it proceed through consent and the decision
sequence. **`account_type` wins, unconditionally, regardless of what else is true of the
account.** `research_export._eligible_instances` filters on `participant.account_type ==
"research"` and nothing else — an operational account's decisions, however they came to exist,
never leave through `participant_inputs`. This was true before this run and is unchanged by it;
stated here because the brief asked the question to be settled, not assumed.

## Verify

**Gate, probed over real HTTP against a running server (`fastapi.testclient.TestClient`, not
read from code) — `server/tools/test_training_gating.py`, 43 checks:**

- Operational + flag explicitly OFF: refused, reason names the feature as disabled.
- Operational + flag explicitly ON: reaches `trainingstatus`, told `enabled: true`.
- Research, flag never touched (defaults disabled): refused.
- Research, flag explicitly set to `true` by an admin (the load-bearing case — the default-off
  protection is deliberately defeated first): still refused, audited (`training_denied_research`),
  and the audit count is compared before/after to prove the write really happened.
- The handler called directly with `gate_action` bypassed entirely: still refuses research,
  proving the inner layer does not depend on the outer one.
- No `session_token` at all: refused. A garbage token: refused.

**Isolation, with the check proven able to fail — `server/tools/test_training_gating.py`
continued:**

- A training project and an ordinary project each get one `ComputedResult` row.
- `build_module_results_rows` (the query itself, not a copy of its logic): the ordinary project's
  row is present, the training project's is not.
- `adminexportcreate` + `adminexportfetch`, `project_health`, all **three formats**: json and csv
  read directly off the decoded `payload` string; xlsx is base64-decoded and opened with
  `openpyxl` and its cells read, not searched as raw bytes (an earlier draft of this check
  searched the base64 text directly and passed for the wrong reason — compressed, encoded bytes
  do not preserve a legacy_id substring, so "absent" would have meant nothing). All three: the
  training project's `legacy_id` appears in no cell/row; the ordinary project's does, so absence
  is a real filter and not a broken export.
- **The check proven able to fail**: the training project is unmarked (`is_training = false`),
  and the exact same project's results now appear in a fresh query and a fresh export fetch. It
  is re-marked and confirmed absent again, so the flag — not something else about the fixture —
  is what the filter is keying on.
- A scenario naming a training project as evidence is refused at creation with a named reason; an
  ordinary project is still accepted.

**Every check proven able to fail by fault injection against the running module (not a copy),
with a full baseline recheck after each fault, before it was believed:**

1. Removed the five training actions from `RESEARCH_FORBIDDEN_ACTIONS` → 1 distinct red (the
   structural check that inspects the set directly), 42/43.
2. Removed the redundant research check inside `a_trainingstatus` (the inner defence-in-depth
   layer) → a different single check went red (the direct-call-with-gate-bypassed probe),
   42/43 — a different signature from fault 1, confirming the two checks test two different
   layers.
3. Removed the `is_training` skip from `build_module_results_rows` → five distinct reds across
   the direct-query check and all three export formats, 38/43.
4. Removed the training-evidence refusal from `a_adminscenariocreate` → two distinct reds (the
   refusal itself, and the reason text), 41/43.

All four faults confirmed applied (diffed against the pre-fault file), each produced a distinct
failure signature, each was reverted byte-identical (`diff` against the backup, clean), and the
suite returned to 43/43 after every single one — not just at the end.

**Full server suite, fresh throwaway SQLite, `alembic upgrade head` including migration 0018:
1692/1692 across 31 suites.** `tests_render.html`: 62/63 — the one red
("production read path: exercised against the server") is a pre-existing check that needs a real
signed-in session token pasted into that tab manually; confirmed pre-existing by stashing every
change in this run and re-running against the same unmodified page, same result. `tests.html`:
51/51.

**The nav item, driven in a real browser (Chromium via Playwright), not only read from markup.**
Signed in as a real operational account with `training: false`: `[data-nav="training"]` exists in
the DOM but computes `display: none` (`body` carries `og-no-training`). The same account with
`training: true`, same session: the button is visible, and clicking it shows
`[data-page="training"]`. `[data-nav="training"]` is hidden directly by its own CSS rule — unlike
the existing `auditor` rule, which hides only `[data-page="auditor"]` (the page content) and
never the dock button itself, a pre-existing gap left alone here because fixing it is outside
this run's scope, but noted since it means the "Auditor" nav icon is currently visible to every
operational account regardless of the flag, however the page behind it correctly refuses.

## Things worth knowing before the next training-mode run

- **`training_mode_roadmap.md` did not exist before this run.** It is now committed at the repo
  root with items 4 and 5 marked DONE below; items 1–3 (the elicited figures, the state
  variables, which decisions a trainee should get wrong) are still Lin's decisions and block
  everything from item 6 onward.
- **The `auditor` nav-hiding gap** (`[data-nav="auditor"]` not hidden by CSS, only the page
  content is): found while building the `training` equivalent correctly. Not fixed here — out of
  this run's scope — but worth a line item, since the difference between the two rules is now
  sitting side by side in `radar.css`.
- **`RESEARCH_FORBIDDEN_ACTIONS` now needs an entry for every training action `GATED_ACTIONS`
  lists**, not just the one this run implements. Both lists were extended together, deliberately,
  so a later run adding a handler for `trainingstart` (say) does not have to remember to touch
  two files — the gate and the refusal are already there for all five listed actions, waiting on
  a handler.
- **`_RESEARCH_REFUSALS` (features.py) carries five near-identical entries**, one per training
  action, because the dict is keyed by action and a `None` fallback exists specifically so a
  forbidden action nobody wrote a reason for degrades to a true-but-vague message rather than a
  false specific one (see `themeset`'s comment). A later run building `trainingstart` etc. for
  real may want to word these per-action once the actions do something distinguishable; today
  they are identical because none of the five actions differ from a caller's perspective yet.
- **No migration has touched production.** 0018 is written and verified locally only, per the
  standing instruction. It must run before any training project is created, same as 0014
  before observations.

Server 1692/1692 across 31 suites. `tests_render.html` 62/63 (pre-existing gap, confirmed
unrelated). `tests.html` 51/51. Four faults injected, all confirmed applied, all distinct, all
reverted byte-identical, baseline re-run clean after each. `server/app/simulation/` untouched.
