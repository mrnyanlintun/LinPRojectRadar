# Run 21 — Final Research Instrument / Website Qualification

Starting Run-20 commit: e73f3c9
Run-20 queue items: 9
Run-21 queue items closed: 5/9 — items 1, 2, 3 and 5 CLOSED, item 6 ANSWERED, item 7 PARTIALLY CLOSED; items 4, 8 and 9 are owner or research decisions Run 21 is forbidden to close
Additional instrument defects discovered: 10
Additional instrument defects fixed: 10

Real-browser qualification: PASS
Server-authority qualification: PASS
Reset/reload qualification: PASS
Project Detail qualification: PASS
FINAL FLOW qualification: PASS
Participant workflow qualification: PASS
Lock enforcement qualification: PASS
Period-transition qualification: PARTIAL — a fixture limit, not a defect; see section 18
Project/session isolation: PASS
Abstention/blocked-state rendering: PASS
Category-9/lineage presentation: PASS
Guard non-vacuity: PASS

Voting: 2
Expected: 2

Concept-only activation: 0
Expected: 0

Material Cost Variance enabled: NO
Expected: NO

Participant protocol changed: NO
Expected: NO

Production Postgres accessed: NO
Expected: NO

Full merged-main suite: 10335/10335 across 119 suites, ALL SUITES GREEN
Real-browser re-verification on merged main: instrument driver 78/78, participant driver 78/78
Final merged-main commit: dc02fe8

**Only one qualification is not a clean PASS, and it is a fixture limit rather than a product
defect.** Run 21 drove TWO complete participant periods end to end in a real browser plus the
cross-assignment roll, and could not reach a third period within one assignment because the
fixture does not go there. The owner asked for P1 → P2 → P3 "where the test fixture supports it".
It does not, and this report says so rather than claiming coverage it does not have.

---

## 1. Run-20 closure reconciliation

Committed separately at **a1c5509**, before any qualification work began.

### A. IMPLEMENTATION_DEFECT is 0, and that target is MET

The Run-20 report stated the count two ways that cannot both be true: **0** in its disposition
table and **NOT MET** in its exit-criteria table. Resolved mechanically from committed rows:

| evidence | source | reading |
|---|---|---|
| 100 rows, each carrying a disposition | `run20_cycle12_100_reaudit.csv` | **none is IMPLEMENTATION_DEFECT** |
| B1.4 and PH.5 | same file, `implementation_correct` | **yes** for both |
| B1.4 and PH.5 | `run20_master_remediation_register.csv`, `implementation_defect` | **no** for both |
| B1.4 | disposition | PARAMETER_PROVENANCE_BLOCKED |
| PH.5 | disposition | THRESHOLD_CALIBRATION_BLOCKED |

Both rows are **blocked on parameter and threshold AUTHORITY, not defective in implementation.**
A fixed N for the worst-N-of-M rule exists in no source this repository holds or cites, and no
calibration evidence here can choose the anomaly weights. **Neither was closed and no number was
invented.** Both remain advisory and non-voting. Only the contradictory wording was corrected, in
the Run-20 report and in three places in `T6_HANDOFF.md`. **No scientific behaviour changed.**

Recorded beside it because it would be easy to omit: **row 4.1 carries `implementation_correct =
no`.** Its `execution_outcome` is `NOT_PORTED` — a truthful refusal by the complete analytical run
rather than a defective computation — and its disposition is EMPIRICAL_VALIDATION_BLOCKED.

### B. The stale ARCH.2 owner-decision row

It described **the transitive closure as current behaviour.** It has not been since Run 20 cycle
6, which *replaced* the closure rather than patching it: dependence is asked pairwise and never
closed, and `evidence_bodies` selects a maximum set of pairwise-independent signals. Rewritten
against committed cycle-6 evidence and `server/app/simulation/lineage.py`, so the option presented
for ratification is the one in production and restoring the closure is named for what it is —
mutation M1 of the cycle-6 battery. **Current lineage behaviour is unchanged.**

## 2. The exact 9-item inherited queue

Ingested **mechanically** from the committed Run-20 report by a script that asserts it recovered
items 1–9. Verbatim text preserved in the last column of
`code_audit/run21_instrument_qualification_register.csv`.

| # | item | status |
|---|---|---|
| 1 | Browser/API qualification of the four cycle-1 corrections that now abstain | **CLOSED** |
| 2 | Browser qualification of the thirty-one truthful method labels | **CLOSED** |
| 3 | `simulations.js` carries superseded governance sentences | **CLOSED — defect confirmed and fixed** |
| 4 | The participant-surface rename | **OWNER DECISION — deliberately not applied** |
| 5 | The stale ARCH.2 row | **CLOSED** |
| 6 | The four crash-rather-than-fail suites | **ANSWERED BY DEMONSTRATION** |
| 7 | Pinned-baseline guards and untracked files | **PARTIALLY CLOSED** |
| 8 | B1.4 and PH.5 | **OWNER OR RESEARCH QUESTION** |
| 9 | Empirical validation as a programme | **RESEARCH PROGRAMME — not attempted** |

## 3. Environment and browser setup

Real Chromium at `/opt/pw-browsers`, Playwright, a real `uvicorn` serving the real application,
throwaway SQLite built by `alembic upgrade head`. **No production Postgres, credential or secret
was used, and no migration ran anywhere but against a throwaway file.**

Two drivers, outside the `test_*.py` glob deliberately because `run_all_suites.sh` must not depend
on a browser: `drive_run21_instrument.py` (state matrix, Project Detail, FINAL FLOW, abstention,
voting, authority, responsive, errors) and `drive_run21_participant.py` (sequence, lock attacks,
transitions, isolation). Each drives its own port and ids — **two drivers must never share a
port**, or the second uvicorn silently fails to bind and every request lands on the first.

`window.confirm` returns false in this shell, so the no-handler case is exercised FIRST and
recorded, proving the confirm gate works, before a dialog handler is installed. Every
state-changing operation is additionally proved by its effect **at the server**.

## 4. Server/frontend authority model

**SERVER TRUTH → API RESPONSE → FRONTEND STATE → VISIBLE BROWSER RESULT**, proved for every state
and recorded in `code_audit/run21_server_frontend_reconciliation.csv`. Tested by deliberate
divergence: a fabricated Green result and status injected into frontend memory left the server
unmoved and did not survive a reload.

## 5–7. Empty, one-document and multi-document states

| state | server | browser |
|---|---|---|
| empty | no live row at all | 0 animated paths, "0 WITH A CURRENT RESULT", "NOT ESTIMABLE", rail present with 10 buttons |
| one document | live row, **35** modules, Amber | "1 UPLOADED ON THIS PROJECT", flow renders |
| 24 documents | live row, **41** modules, Amber | "24 UPLOADED ON THIS PROJECT", 100 animated paths |

The architecture inventory is labelled **REGISTERED**, and **no badge presents 96 as a count of
what actually computed** — the owner's explicit prohibition.

## 8. Reset and reload (STATE D, STATE G)

### The reset contract, measured because it was first assumed wrongly

**THE RESET CLEARS STORED SIGNALS. IT DOES NOT DELETE DOCUMENTS** — its own control says so.

| state | upload events | live row | modules |
|---|---|---|---|
| populated | 24 | yes | 41 |
| after reset | 24 (+1 `signals_reset`) | **no** | — |
| after reset + one new document | 25 | yes | **41** |
| control: only ever that one document | 1 | yes | **35** |

Re-reading retained documents after a reset is **designed behaviour**. The first driver version
asserted the opposite from an assumption; that invented requirement was **removed, not weakened.**

### The product defect Run 21 found

After the reset the page read **"0 UPLOADED ON THIS PROJECT"** and **"This project has no uploaded
documents"** — measured **on a RELOADED document**, so not a cache artefact. Both are false: the
documents were retained and the next recompute produced 41 modules from them. **Same class as the
"96 modules" defect Run 16 fixed: a correct number under a false label.**

Fixed in `assets/js/neural_flow.js`. Now: **"0 UPLOADED SINCE THE RESET, 24 RETAINED"**, and the
summary states the retained documents will be read again. Verified in a real browser after reload,
after navigation, and in a fresh browser context, with the retained figure checked against the
server's own event count. **What deliberately did not change**, each asserted as a property: the
since-reset count, the current window's document set, whether anything animates, and both the
pre-reset wording and the empty-project sentence for a project never reset.

### The reload

**MEASURED:** the reload completes, the sentinel is destroyed — which no same-document operation
can produce — and the application is ready at **about 195 seconds**; Playwright's `reload()` times
out at 45s even at `wait_until="commit"`. All four reloads in the final run proved
`application_reloaded_from_server = yes`. The driver keeps **three** outcomes distinct — reloaded,
not reloaded, **not determined** — so a hanging subresource can neither prove the reload broken
nor excuse a real defect. **Run 21 did NOT determine whether the 195 seconds is a container
artefact or a real participant cost.** Run-22 queue item 7, blocking-if-real.

## 9–10. Post-reset evidence and project switching

New post-reset evidence produces a live row, and after re-reading the server the page shows it —
the upload was made through the API, so the browser could not know until it read the server, which
is the point. Switching populated → empty → populated twice: identical on both passes, and the
empty project never inherits the populated one's picture.

## 11–12. FINAL FLOW and Project Detail

Registered architecture is distinguished from current activity **in words** on the page. The
numbered rail is preserved (10 buttons) and the obsolete collapse control is **absent from the
DOM** at 1920, 1680, 1440, 1280, 1024, 820 and 390. The check reads DOM presence, opacity,
visibility, display, pointer-events, hitbox, keyboard focus and the accessible control tree, and
**never uses opacity, size or pointer-events to excuse an element.** Nothing overlaps the rail.
Selecting a rail entry scrolled from y=0 to y=940 and marked the entry active. Three decorative
arrow separators in the colour legend are `tabIndex -1`, roleless, handler-less, not in or over
the rail — **not controls** — and are listed separately rather than dropped.

## 13–15. Abstention, voting, lineage

**No module the server records as abstaining carries a band** — twelve checked from the server's
own list. An abstention carries no band, may not vote, and presents **no status** to the
combination. **Voting is exactly 2** — A1.7, A1.8, read from the registry — and the browser's
project status equals the server's. Two transforms of one body publish as **one** body and do not
sharpen belief; two disjoint bodies still publish as **two**; **no participant-route file calls any
combination entry point**, with the scanner proved to find them where they live.

## 16–17. Participant sequence and lock attacks

Preliminary → lock → reveal → final → lock, driven twice by one generic routine. In both periods:
AI absent from the DOM before lock; `researchreveal` **refused**; a direct `fetch` from the page
returns no AI content; the sequence-state route carries none; preliminary edit, duplicate submit,
final edit, confidence-only and rationale-only changes all **refused**; a direct SQL UPDATE
**refused by the append-only trigger**. **After the preliminary lock the controls are ABSENT from
the DOM, not merely disabled.** The refusal recorder is itself proved non-vacuous by a legitimate
call that must come back NOT REFUSED, and the AI-leak scan is proved to find the recommendation
immediately after each reveal.

## 18. Period transitions — the honest limit

P1 → P2 works in a real browser: advance offered, transition occurs, next period starts at
evidence, the preliminary card returns (the Run-12 defect, re-proved), no prior answer leaks, AI
hidden again. **A third period within one assignment is NOT reachable**: completing an assignment's
second period rolls the participant to the **next assignment** at its own P1, and `researchadvance`
correctly refuses. Established at the route level with no browser. The fixture also froze a rule
for period 1 only; the driver adds frozen P2/P3 rules through the operator routes — test-only
data that changes nothing about treatment, randomisation or sequence. Completed-period
immutability is proved on the **stored row**, byte-identical after later work, with a companion
check proving later periods create their own rows.

## 19. Isolation

A second participant's state carries none of the first's rationale or the AI text; they are
**refused** the other's project result and **cannot reveal** without their own lock; an invalid
token reaches nothing. The leak test reads **decision-bearing fields and a string unique to the
first participant**, because the route legitimately returns the shared five-action vocabulary to
everyone — an earlier substring scan over the whole payload matched that vocabulary and reported a
leak every time. Non-vacuity: the same detector **does** find the rationale in the first
participant's own record.

## 20–21. Responsive and error states

Seven widths, eighteen screenshots retained. An unknown project is **refused** and the refusal
**carries no band** — no silent conversion of failure into a colour. An invalid session is refused.
The confirm-suppressed commit submits **nothing**.

## 22. Guard non-vacuity

Every critical invariant proved RED by violating the **real production structure**, then restored
with the restoration **verified**: voting count, concept-only activation, Material Cost Variance,
raw-bypass refusal, anti-feedback rejection, abstention contract, the six withdrawn regulatory
claims, the executed JS↔server numeric comparison, and six reset-disclosure mutations including two
that would silently undo Run 18. Expectations are pinned in **literals**; no value is compared
against the expression that produced it; and the concept-only check runs over a **pinned id list**
rather than the mapping the violation emptied.

## 23. Defects found and fixed — ten

**One in the product** (section 8) and **nine in Run 21's own instruments**, every one of which
would otherwise have been reported as a product defect:

1. An over-broad literal scan flagged the *corrected* file, because the corrections' commentary
   quotes each withdrawn sentence. Fixed with a comment stripper so the scan reads executed code.
2. An over-broad arrow reader called three decorative legend separators a collapse control.
3. A 90-second deadline for an operation measured at 195 seconds.
4. An invented STATE-E requirement contradicted by the product's own stated contract.
5. A driver that stayed on the old project after a transition, making the correct
   already-revealed response look like an AI leak.
6. An "attack" that resolved to the **current** period and so submitted the new period's
   preliminary instead of attacking the previous one, then reported its own three consequences
   as defects.
7. A "control is offered" check that only asked whether the element existed, while the element
   measured **zero by zero**.
8. A leak test that searched for an action word present in the shared vocabulary.
9. A non-vacuity proof searching a snapshot that did not carry the field it sought; and an
   obstruction check requiring `elementFromPoint` to answer for an element below the fold, where
   it returns null by definition.

**In every one the product was correct and the instrument was wrong. No expected output was
changed anywhere in this run to make defective code go green.**

## 24. Anti-fossilization

Seven rows added (register now 25), each carrying historical behaviour, correct behaviour, reason,
how it was caught, and the test that catches its return.

## 25. The complete suite

**119 suites, 10335 of 10335 checks, ALL SUITES GREEN on merged main.** Baseline at e73f3c9 was
115 suites and 10060 checks; Run 21 adds four suites and 275 checks.

The first merged-main sweep found **three** failures, all in the test layer and none in production:
two more pinned-baseline scope guards fired on Run 21's browser edits (extended **by naming** the
files and reasons, never by widening the rule), and `test_run20_cycle12_fault_evidence.py`
**crashed** because it sorted every anti-fossilization cycle label with `int()` and the register is
append-only across runs. **The strict runner caught the crash as FAIL** — a suite that dies before
printing the canonical line has no canonical line. That is Run-20 queue item 6 answered by
demonstration: a lenient runner would have reported it as a pass.

Both browser drivers were re-run on merged main: **78/78 and 78/78, zero failures.**

## 26. Git and handoff

| commit | what |
|---|---|
| `a1c5509` | Run-20 closure reconciliation, committed separately |
| `c82d06f` | queue item 3, the four withdrawn regulatory claims removed |
| `49c4148` | the reset boundary disclosed, and three qualification suites |
| `496f21c` | the two browser drivers, their evidence, the Run-22 queue |
| `3488b15` | merge to main |
| `35789aa` | the three merged-main failures, traced and fixed |

**Production changes: two files, both browser-side**, declared in
`server/tools/run21_production_changes.py`. The Run-20 freeze remains immovable and the Run-20
manifest was not touched; a check proves no Run-21 path was folded into it.

## 27. The Run-22 freeze queue

Nine items in `code_audit/run21_run22_freeze_queue.csv`. **Three block a freeze:**

| # | item | blocking |
|---|---|---|
| 1 | the participant-surface rename (OWNER) | if anything a participant reads is renamed |
| 2 | B1.4: a fixed N exists in no source | no — advisory, non-voting |
| 3 | PH.5: no calibration evidence exists here | no — advisory, non-voting |
| 4 | empirical validation as a programme | only for a claim of validated performance |
| 5 | **the pinned baseline enumerates a fixed 143-file list**, so a new untracked production file is invisible to it | **YES** |
| 6 | whether the four crash-rather-than-fail suites should fail instead | no |
| 7 | **the 195-second reload: container artefact or real participant cost?** | **YES, if real** |
| 8 | the reset retention contract is stated only in a tooltip | no |
| 9 | **freeze and release qualification itself** | **YES** |

**Run 22 was not launched.**

## What Run 21 could not complete

* **A third period within one assignment** — the fixture rolls the participant to the next
  assignment after the second period (section 18).
* **Whether the 195-second reload is a container artefact or a real participant cost** (section 8).
* **Queue items 4, 8 and 9** — none closable by engineering without inventing a number or
  overriding an owner decision.
* **Queue item 7 only partially** — four pinned-baseline guards were strengthened and all four
  fired on Run 21's own edits, but the freeze still enumerates a fixed file list, so a new
  untracked production file remains invisible to it. A freeze-scope decision for Run 22.
