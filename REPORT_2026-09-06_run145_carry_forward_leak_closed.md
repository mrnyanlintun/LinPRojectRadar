# Run 145 — close the carry-forward leak in the qualification gate

**`SIMULATION_VERSION` moved `sim-2026.09-v72` → `sim-2026.09-v73`, and it had to.** Closing the
leak changes which readings carry and therefore which categories vote and what status is published:
on the reproduction case it is the difference between a published band and a withheld status. The
history tuple is **appended** to, no prior row edited, and the superseded marker is untouched.
**No migration.**

Starting commit `4995deb`, ending `d613490`, pushed, tree clean.

---

## The leak, reproduced and closed

**The reproduction, measured by me.** One material conflict between two equal-precedence documents,
with the qualification record declared:

```
clean declaration     -> []
one material conflict -> ['A6.1','A6.2','A6.3','A6.4','B1.1','B1.2']
```

Two are exempt by module identity, so **the real exposure is the four Delivery Quality arms** — the
category that gates the fifth vote.

**Driven end to end against one prior period of Greens, re-run by me on merged main:**

| | project status | categories voting | A6 | carried |
|---|---|---|---|---|
| **before** | `Green` | 5 | assessed | A1.6, A2.1, A3.3, A4.4, **A6.1, A6.2, A6.3, A6.4** |
| **after** | `Awaiting analysis` | 4 | `required_missing = ['A6']` | A1.6, A2.1, A3.3, A4.4 |

**The published status changes on the reproduction case, and I state it plainly: a published band
becomes a withheld status.** That is the correct outcome. The four carried Greens were readings the
gate had refused, and removing them leaves the category with nothing to vote on, which is what
"unassessed" means.

**The sentence beside them, unchanged and now true:** *"The evidence supplied for this measure has
not been qualified for this use… **No earlier reading is carried forward in its place either**: the
refusal is about whether this evidence may be used at all, not about a missing input."* Before the
fix, each of those four rows carried a Green while that sentence stood beside it on the same
ledger.

**The change is one entry**, plus its own exemption words so that no reader is told a module
crashed when it did not. **The sentence was not touched**, as ordered: it was right and the
behaviour was wrong.

---

## The four codes, and which carry

| # | code | refusal primitive | what it means | carries |
|---|---|---|---|---|
| 1 | `CATEGORY9_ASSESSMENT_MISSING` | `_refuse_missing`, on `ev is None` | nothing was ever assessed | **yes** — ruling 1, intact |
| 2 | `evidence_not_qualified_for_use` | `_refuse`, taking the evidence object | evidence weighed and judged unfit | **no** — this ruling |
| 3 | `module_execution_failed` | the registry's guard | the module raised | no, unchanged |
| 4 | `QUALIFICATION_CONTRACT_MISSING` | `_refuse_missing` | the route has no governed requirement declaration | **yes** |

I verified all four by execution on merged main rather than by reading, and the block list now
holds exactly the two that must not carry.

---

## The fourth code, and how it was ruled

**It carries**, and the evidence is structural rather than a matter of taste.

It fires **before the evidence is ever fetched** — the contract lookup happens first, so no
evidence object exists at that point. It uses the same refusal primitive as code 1, documented as
*the governed abstention for a route blocked before any evidence could be assessed*, marking the
state unassessed and recording that the consumer never executed. Code 2 uses a **different**
primitive that takes the evidence object and carries its qualification reasons. **The codebase
itself groups 1 and 4 together and separates 2**, which is exactly the line the owner's test draws.
So by the first branch — nothing judged, no evidence weighed — it carries.

**The counter-argument was weighed rather than ignored.** The call site says an undeclared route is
a configuration failure and the default branch is deny. That deny governs whether the **consumer
executes this period**, not what an earlier period lawfully established.

**And the sharper point strengthens the ruling rather than upsetting it.** A missing contract is a
platform-configuration state, not a per-period evidence fact, so it refuses every period alike. The
only way an earlier banded reading can coexist with it is if the contract was declared then and
withdrawn since — which is precisely the case where the earlier reading was lawfully taken under a
declared contract, and where there is nothing about *this period's evidence* to defeat.

**Its exposure is LATENT, and both of us measured it independently: of the 31 routes in service,
zero have no declared contract.** Nothing in service can reach it today. That is the opposite of
code 2, which one material conflict reaches immediately. The check exercises the path anyway, by
withdrawing a declaration in process — the only way an earlier reading can coexist with it —
confirming the refusal, confirming it carries, and restoring.

**The trap was confirmed and recorded.** Two different constants share the single string value: one
is the requirement lookup's sentinel, the other is the reason code written on the row. Block-listing
the string would do the right thing, but they do not mean the same thing, and the new list entry
imports its code from the boundary rather than the contract so the distinction survives the next
reader.

---

## The seven proofs

| # | proof | result |
|---|---|---|
| 1 | leak reproduced before the fix, with the sentence quoted beside the behaviour | **PASS** |
| 2 | after the fix the same case does not carry; the category is unassessed and the posture reflects the absence | **PASS** |
| 3 | code 1 still carries and code 2 does not, driven side by side; on an ungoverned package the category still carries all four arms and still votes five of five | **PASS** |
| 4 | the published status changes with it, band to withheld | **PASS** |
| 5 | fault injection — the entry removed returns the leak, all four Greens carried again, status back to a band; restored and asserted restored | **PASS, and I ran this myself** |
| 6 | the fourth code demonstrated carrying, on the reproduction case with its contract withdrawn | **PASS** |
| 7 | nothing else moved | **PASS** |

**My own injection, on merged main**, is the clearest statement of what changed:

```
AFTER FIX     : ('Awaiting analysis', 4, ['A6'], [A1.6, A2.1, A3.3, A4.4])
LEAK RESTORED : ('Green',             5, [],     [A1.6, A2.1, A3.3, A4.4, A6.1, A6.2, A6.3, A6.4])
RE-CLOSED     : ('Awaiting analysis', 4, ['A6'], [A1.6, A2.1, A3.3, A4.4])
```

## Proof 7 — how each was confirmed

Every suite on a **fresh** throwaway database, never production, never the stale development file.
Ten suites re-run by me on merged main after the merge: the two new Run 145 checks; both Run 144
ruling checks; the Run 143 carry and fault suites, the latter reporting every injection producing
its defect and every restore holding; period removal at 74 of 74; the A1/A3 band contract at 54 of
54; the Category-9 and no-band suite at 21 of 21; and the mitigation engine at 55 of 55.

**Ruling 2's mitigation exclusion and ruling 3's age display were confirmed unmoved** by their own
suites passing, including ruling 2's fault injection. **No band ladder, threshold, weight or posture
rule was touched** — the only production change is one entry in a frozen set and its comment. The
never-carry module list is asserted unchanged.

## One thing the agent did outside its brief, and my judgment on it

Run 144's own check pinned four things that were true only at that moment: the exact contents of
the block list, the stamp equalling v72, and the history ending at v72. **Those failed for the
right reason once this run moved both.** The agent rescoped rather than suppressed, and flagged
that the file was outside its stated ownership.

**I reviewed the change and accept it.** It preserves ruling 1's substance — that its code is off
the list, that v72 is in the history unedited, and that v71 and v72 remain adjacent — and drops
only the pinned tails, which is the same re-pointing rule Run 137 established. **One caution for the
next run:** the rescoped assertion now pins the list to exactly two codes, so the next code ruled
onto it will fail this check for the same right reason.

**Also reported and not touched:** a Run 38-era freeze-manifest suite reports 10 of 17 against a
baseline whose named files are from Run 41. Pre-existing, unrelated, and outside scope.

## Left alone, as ordered

The theme defect, where one theme paints a dark page while leaving the colour token at the light
default. The period-scoping check at 73 of 77, still failing for the reason already given. The rest
of the gate. The recomputation was not triggered.

## What the recomputation must now cover

**Every stored result row on every project.** The move from v72 to v73 changes which readings carry
on any project-period whose evidence the gate assessed and judged not qualified: the four Delivery
Quality arms lose their carried readings there, the category becomes unassessed, the voting count
falls from five to four, and the published status falls to withheld. Rows stamped v72 and earlier
remain valid under their own stamp.

**It will not fire as a side effect of the deploy, and this is the thing most likely to be
forgotten.** The staleness check keys on the document set and the qualification record — **not on
the simulation version.** A stamp move therefore marks nothing stale, and a recompute-all skips
every row. **The recomputation has to be triggered deliberately.**

## Iteration log

No finding needed more than one attempt; nothing reached the cap and nothing was reverted. The only
judgment recorded beyond the two rulings is the rescoping above, disclosed by the agent rather than
discovered.
