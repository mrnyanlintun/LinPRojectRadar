# Run 147 — the blank page: the cause is NOT established, and the next page load will name it

**`SIMULATION_VERSION` does not move.** Nothing under `server/app/` was touched at all. The only
production change is in the client, and it is the surfacing you ordered. No migration.
**Nothing needs recomputing on the evidence available.**

Starting commit `c663aba`, ending `317a1a3`, pushed, tree clean.

---

## State plainly: the cause is not established

Run 146 fixed a real defect at the wrong seam and the symptom persisted. **I am not going to do
that twice.** What this run establishes is where the fault is **not**, and it makes the next page
load diagnostic instead of silent. That is the honest deliverable.

**My own dispatch hypothesis was killed by measurement.** I sent this run pointing at the
first of the two requests aborting so the second is never issued. **Measured: with that first call
refused, the page still held all its module rows, its abstentions and its extracted values**,
because the module accessor falls back to a cache primed for the same period and several other
consumers on the page fetch the results themselves. The never-issued path is real and is now
surfaced, but **it is not this symptom.** Two hypotheses of mine in two runs, both wrong, both
killed by a measurement rather than by argument.

---

## 1. The captured response — from a CONSTRUCTED FIXTURE, stated plainly

PRJ-002 and its database are unreachable from this container. Every byte below was captured from a
fixture built through the real endpoints into a throwaway database, in PRJ-002's shape: two
periods, the second computed and holding module rows and abstentions, a frozen scenario naming the
project, and a research assignment whose decision in the last period is submitted **and
transitioned**.

```
POST /exec {action: projectperiods}              <- the page's first request
  HTTP 200  ok=True  error=None
  latest_computed_period = 2   computed_periods = [1, 2]

POST /exec {action: projectresults, period: 2}   <- the graft's own request
  HTTP 200  ok=True  error=None
  result: 33 keys
  module_results        PRESENT, is-array True, every stored row
  abstained             PRESENT
  signal_inputs         PRESENT, 88 entries
  decision_dispositions PRESENT
  category_statuses     PRESENT
```

**On this tree the server sends all of it.** Both requests succeed; the module array, the extracted
values, the disposition list and the category statuses are all on the wire. **The loss is not
upstream of the wire here**, which is the half of the problem your measurement was designed to
settle.

## 2. The seam, as far as it can be named

**A `projectresults` response that is refused or never arrives — the graft's own request failing —
and not the client discarding a populated one.**

Proved by browser observation: with that request made to refuse, the page reproduces your report
**verbatim, including the number**:

> *"0 of 28 modules in service assert a band; 0 computed without asserting one, 0 have nothing to
> report, 0 are not relevant to this project, and 28 have not been called."*

together with both missing sentences, and with the module rows **absent entirely rather than an
empty array** — which is your ruling 7, independently reproduced. **The 28 is the registry roster,
not the row's 28.** That coincidence is real and it is not causal, and it is worth knowing because
it has made this look like a data problem twice.

**Eight paths can stop the graft. Four are server refusals of that request** — the caller check,
the membership check, the period derivation, and no live row for the derived period. **A fifth
class was missing from the enumeration**: any unhandled exception anywhere in that route is
converted to a not-ok body at HTTP 200 carrying only `Server error: <TypeName>`, which the client
dropped in complete silence. **No ruling in your order covers that class**, and it is the one I
would look at first.

## 3. How this accounts for all three

1. **The stored 28 rows.** They exist and the server serves them. A refused response means the page
   never receives them; nothing about the row is involved.
2. **Unbounded carry-forward.** Carried readings are appended to the computed set and stored in the
   same field, so on the wire a carried reading is indistinguishable from an own reading. It
   travels only by the same refused response.
3. **Generate signals.** It rewrites stored rows. It cannot help a page whose request for those
   rows is refused.

**A cause that explained only one would be wrong. This one explains all three by the same
mechanism.**

## 4. Why the category statuses survive — confirmed

The list projection carries exactly six keys, measured: result id, period, project status, category
statuses, posture layers and fallback categories. **No module rows, no signal inputs, no
dispositions.** That projection is what the page attaches as its stored result, so postures, the
project status, the header driver and the Signal Flow diagram all render with the graft never
having run. **Run 146's account of the split is correct and stands**, even though its account of
*why* the graft failed did not.

## 5. Carry-forward is not a second fault

Confirmed rather than assumed. It is a server-side compute-time operation whose only route to the
page is the field the list projection omits and the graft supplies. **A blank page carries no
evidence either way about it.** Run 143's work is not implicated.

## 6. The seven proofs

| # | proof | result |
|---|---|---|
| 1 | response captured before any fix | **8/8**, fixture-sourced and stated as such |
| 2 | blank page reproduced in a browser, network line verbatim | **PASS** — your sentence, word for word |
| 3 | after the fix the rows arrive, by browser observation | **PASS** — module rows, abstentions, 88 extracted values, the disposition control present, the network line reading real counts, "No data" cells falling |
| 4 | postures and project status unchanged | **PASS** — identical across all four passes |
| 5 | a refused graft now surfaces | **PASS** — refusals injected at both routes; a page banner and a console error, each naming the action, the period and the server's own reason |
| 6 | proved able to fail | **PASS** — injected, observed, restored, **24/24** |
| 7 | blast radius | the surfacing covers every project, every period and every reader of the detail page. The underlying refusal covers any project whose results request is refused for any of the five reasons; operational projects are unaffected only where none of those fires |

All re-run by me on merged main: the capture 8/8, the carry check 3/3, the surfacing 24/24, and
Run 146's two suites and period removal unchanged at 16/16, 16/16 and 74/74.

## 7. What is NOT established

**Which refusal PRJ-002 actually hits.** On a tree carrying Run 146's fix the fixture is served
whole, so either **the deployment does not yet carry Run 146's merge** — in which case that
diagnosis stands and the fix simply has not shipped — or **the request is refused for one of the
other four reasons**, most plausibly an unhandled exception inside the route for that project's
data, which no ruling covers.

**I am deliberately not choosing between those two.** A third fix in the wrong place would make
this harder to find, not easier.

## The next measurement is now free

**Load PRJ-002's detail page on the deployment.** It will either be whole, or it will carry a
banner naming the request that failed and the server's own reason — an authorization refusal, a
missing result for a period, a transport failure, or `Server error: <TypeName>`. **That single
sentence closes this**, and it costs nothing but a page load.

If you would rather read the database first, the read-only query is:

```sql
SELECT period, result_id, simulation_version, computed_at,
       jsonb_array_length(module_results) AS n_modules
FROM computed_results
WHERE project_id = (SELECT id FROM projects WHERE legacy_id = 'PRJ-002')
  AND superseded_by IS NULL
ORDER BY period;
```

Two rows at v73 with non-zero module counts confirm the data is sound and the fault is entirely in
serving. Anything else would mean recomputation rather than a code fix.

## The defect that cost several runs, now closed

Both silent early exits are gone. A refused or errored graft **names what was refused** — the
action, the period, and the server's reason verbatim — on the page and in the console. **A server
refusal and a request that was never sent used to look identical from the outside: a blank page
with nothing to inspect.** That is why this took three runs to corner, and it will not happen
again.

## Items not done, disclosed

A defect suite holding a line-level allowlist over the client file **is already broken on main** and
does not run, so this run's new lines are unnamed in it should it ever be revived. Not repaired —
out of scope, and reported rather than left to be discovered.

## Iteration log

No finding needed more than one attempt. The correction worth recording is mine, for the second run
running: **I dispatched pointing at a specific client gate, and the measurement killed it.** The
agent reported that rather than building on it, which is the outcome the order asked for.
