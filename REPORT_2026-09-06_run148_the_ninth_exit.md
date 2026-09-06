# Run 148 — the ninth exit: a throw on a promise nobody was holding

**`SIMULATION_VERSION` does not move.** It is `sim-2026.09-v73`. Nothing under `server/app/` was
touched. No migration. **The data is correct and nothing needs recomputing.**

Starting commit `4ba23b8`, ending `af7c21b`, pushed, tree clean.

---

## The cause, reproduced before anything was changed

**Run 147 enumerated eight exits and gave every one a banner. All eight are returns. None is a
throw.**

The graft is started by a call that was made with neither `await` nor a `catch`. It is an async
function, so **any exception raised after the response has already been read** — while priming the
shared cache, inside the graft itself, or in any of the second-pass refreshes — **rejects a promise
nobody is holding.** An unhandled rejection writes nothing to the page, never reaches the failure
reporter, and leaves the initial empty state exactly as it stood.

**That is the ninth exit, and it is invisible to both surfaced ones by construction.**

**Reproduced in a browser against the tree exactly as this run found it**, on a constructed fixture,
with one injected exception on that path:

```
client row: module_results=None  abstained=None  signal_inputs=None  dispositions=None
            categories=7  project_status='Awaiting analysis'
network line: '0 of 28 modules in service assert a band; 0 computed without asserting one,
   0 have nothing to report, 0 are not relevant to this project, and 28 have not been called.'
page banner: None      surfacing on the console: []
```

Module rows **absent, not empty**. Your sentence **verbatim, including the 28**. Categories and
project status untouched. **No banner, and not one line from Run 147's surfacing either.**

## How one cause accounts for all three levers

The exception happens **on the client, after the payload has already arrived intact**. So:

1. **The stored 28 module results are irrelevant** — they were sent, and then dropped on the floor.
2. **Carry-forward's 23 banded period-1 readings are equally irrelevant** — the client-side row
   object is never populated, so there is nothing for any consumer, carried or not, to read.
3. **Generating signals changes only what the server stores**, and the loss is downstream of the
   wire.

**That is why every one of your three levers moved nothing.** A cause explaining only one would
have been wrong; this explains all three by the same mechanism.

---

## Task 1 — what the deployment serves

**It cannot be established from this repository, and that is a defect in its own right.** The
service exposes a version on three endpoints and it is **a hardcoded string**, not a git sha and
not a build stamp. It has never moved and cannot distinguish this commit from any before it. **Your
case 1 and case 2 cannot be told apart from inside the tree.** A build stamp was not added — the
order does not authorise one and the fix did not require it — and it is proposed as a finding.

## My own Finding B, confirmed as a code fact and then killed as an explanation

I put a strong candidate to the hunt before it started: **nothing prevents a browser running
yesterday's code.** Every script is referenced by bare path with no version query and no content
hash, and the application sets no cache headers at all. Those code facts are confirmed.

**But the consequence was tested rather than assumed, and it failed.** Serving the genuine
pre-Run-147 file against a post-Run-147 server rendered the page **whole** — module rows,
abstentions, extracted values, real counts in the network line. **A stale asset is not by itself a
blank page.** Old code only produces the reported state if something is *also* failing underneath
it, which would require re-admitting a server failure Run 147 measured as absent.

I had asked whether "the page is running old code" was strong or merely unfalsifiable. **It turned
out to be falsifiable, and it was falsified.** That is the third hypothesis of mine killed by a
measurement in three runs, and each time the measurement was cheaper than the argument.

---

## The enumeration — six candidates, three discarded

Each judged against all four parts: rows absent, the observed sentence, categories still
publishing, and **no banner**. Run in real headless Chromium against a real server, reusing Run
147's harness rather than building a second instrument.

| candidate | verdict |
|---|---|
| an unhandled exception **inside the results route** — Run 147's own first suspect | **discarded** — the surfacing catches it and the page carries a banner |
| the module rows arriving as an **object** rather than an array | **discarded** — the row survives and the network line does not appear at all |
| the module rows under a **renamed key** | a live class, but its line reads "3 have not been called", not 28 — **not the reported instance** |
| **a throw after the response, on an unheld promise** | **reproduces all four parts, sentence verbatim** |
| a **stale pre-fix asset** with a healthy server | **discarded** — the page renders whole |
| a stale asset **and** a server refusal together | reproduces, but only by re-admitting a failure already measured as absent |

**Three of six discarded.**

## What is established, and what is not

**The class is established and reproduced.** **The specific exception raised on your deployment is
not** — a stand-in throw was injected, because the real one cannot be seen from here. **What the
fix does is make that specific exception name itself, with its stack frame, the next time the page
loads.** That is Run 147's posture one exit further in, and this time with a reproduction behind it.

---

## The fix, and the surfacing gap closed

One change, at the call site — the seam where the loss happens, not the renderer. The graft's
promise is now caught and routed through **the same reporter the other eight exits use**. Reporting
only: no band, threshold, weight, posture rule or category rule, and nothing under the server.

With the identical injection and the fix in place, the page now says:

> *"the stored analysis was read from the server but could not be applied to this page: an error
> was raised while applying it."*

**with the raising stack frame named**, on the page and on the console. **The gap is closed.**

## The nine proofs

| # | proof | result |
|---|---|---|
| 1 | what commit the deployment serves | **cannot be established** — the version is a hardcoded string |
| 2 | blank page, no banner, reproduced in a browser | **PASS** — counts and screenshot, observed not inferred |
| 3 | cause named and shown to produce that state | **PASS** |
| 4 | all three levers accounted for by one cause | **PASS** |
| 5 | after the fix, the page is whole | **PASS** — module rows, abstentions, 88 extracted values, dispositions, real counts. Browser observation |
| 6 | categories and project status unchanged | **PASS** — identical across every pass of both suites |
| 7 | the surfacing now covers this path | **PASS** — injected, named on page and console with its stack frame |
| 8 | proved able to fail | **PASS** — the same injection either side of the fix, then restored |
| 9 | blast radius | every detail-page render calls this line; the catch runs only on a rejection that previously vanished |

Re-run by me on merged main: the new suite **17/17**, Run 147's surfacing **24/24 unchanged**, Run
146's browser suite **16/16**.

## A remaining gap, named and not closed

**The renamed-or-retyped-payload class is still silent.** A payload whose shape the client cannot
read satisfies every guard, clears the banner, and empties the page quietly. Closing it means
asserting a payload shape, which is wider than this order authorises. **It is real and it is worth
a run.**

---

## The next measurement, and it is now cheap

**Open PRJ-002 period 2 with the browser console open, and hard-refresh first** to defeat the
unversioned assets. Then one of three things is true:

- **A banner naming an error with a stack frame** → this run's ninth exit fired, and the banner
  names the specific instance outright.
- **A banner from Run 147** → the graft was refused, and the reason is on it.
- **Still blank with no banner after a hard refresh** → the deployment is not serving this commit,
  which settles Task 1 the only way this repository allows.

If the page comes back **whole after the hard refresh alone**, then my Finding B was right in its
compound form and the fix to make is the cache-busting one.

## Iteration log

No finding needed more than one attempt. The correction worth recording is again mine: **I
dispatched this run with a strong candidate, and the agent killed it with a single measurement
rather than building on it.** That is three of my hypotheses falsified in three runs, and it is the
reason this one has a reproduction behind it instead of a fourth plausible seam.
