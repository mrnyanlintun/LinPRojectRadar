# The globe switching itself back to Map, and the globe not rotating

854 checks across 17 suites pass.

Both symptoms are fixed. **They shared a trigger but had different root causes**, so they needed
separate fixes — and one of them was hiding the other.

---

## 1. "Selecting Globe switches back to Map after a moment"

**My bug, introduced last session.** Not the persisted-view restore — there are only two callers of
`setPortfolioView` (the click handler and the startup restore), so nothing was re-restoring.

Last session I added a watchdog to catch the case this whole change exists to prevent: a globe that
resolves `ok` while drawing nothing, leaving a black panel. It asked `handle.hasScene()` **once**,
the instant `mount()` resolved.

`mount()` resolves in about **40 ms**. globe.gl does not build its scene group until roughly a
**second** later. So the single check always saw `false`, the watchdog never stood down, and four
seconds later it destroyed a perfectly good globe and switched to the atlas.

The watchdog fired *precisely when the globe was working*. On a machine where the globe genuinely
failed, the outcome looked identical — which is why it survived review.

**Fix:** poll to a deadline instead of asking once. The moment a scene appears the watchdog stands
down; only a deadline reached with no scene at all counts as failure. Deadline 6 s, poll 150 ms.

Verified both directions:

| Case | Result |
|---|---|
| Healthy globe (scene at 1.2 s, simulated) | Stays on Globe at 3 s **and at 10 s**. Before the fix it flipped at 4 s. |
| Globe that never builds a scene (`hasScene()` forced `false`) | Falls back to the atlas at the deadline, WebGL context released (`liveCount` 0), atlas rendered (207 nodes) |

The protection is intact; it simply no longer misfires on success.

---

## 2. "The globe is not rotating"

**A separate cause, and it was never rotating in the case you were looking at.**

`autoRotate` was only enabled when `interactive === false` (the detail globe) or when
`pts.length === 0` (the empty state). The portfolio globe **with projects placed** was neither, so
it had auto-rotation switched off by construction. Not a tuning problem — it was never turned on.

**A second, quieter problem underneath it.** three.js turns at 6°/s per unit of `autoRotateSpeed`,
so the previous `0.35` was 2.1°/s — about **171 seconds per revolution**, which reads as a still
image even when it is enabled.

I should be plain about how that got through: earlier sessions, including mine, confirmed "empty
state rotating at 0.35" by **reading the property**, never by watching it. The property was true.
The globe was, for practical purposes, motionless.

**Fix:** auto-rotate in every state, at `1.0` — 6°/s, one revolution a minute. Unmistakably alive,
still slow enough not to compete with the points. OrbitControls suspends rotation while the user
drags and resumes after, so it does not fight anyone inspecting a marker. It now also respects
`prefers-reduced-motion`, which it did not before.

| State | autoRotate | Speed | Rate |
|---|---|---|---|
| Empty (resting visual) | true | 1.0 | 6°/s — 60 s/rev |
| Portfolio, 2 projects placed | true | 1.0 | 6°/s — 60 s/rev |
| Detail, focused | true | 1.0 | 6°/s — 60 s/rev |

### Did they have one cause?

No — but the first was masking the second. The watchdog removed the globe about four seconds after
selection, which is roughly the window in which rotation at the old speed would have been
invisible anyway. Fixing only the watchdog would have left a globe that stayed put and sat still.

---

## 3. The globe does place points

Confirmed rather than assumed. Your "0 project(s) placed" is a data condition, not a fault.

I created a second located project so this was tested with more than one. With two projects that
have coordinates:

```
mountResult: { ok: true, points: 2, unplaceable: 0 }
```

- `Globe Verify PHL` — 39.8882634, −75.2462739
- `Globe Points BNA` — 36.1195848, −86.6826622 (matches the handoff's independently verified
  BNA fix of 36.11958, −86.68266)

After a reload with Globe as the restored view: `liveGlobes: 1`, `tilt: 23.4`, `points: 2`.

Both render in `--status-nodata` because neither has a stored `computed_results` row yet — correct
behaviour, and the globe still derives nothing.

---

## 4. View selection sticks

All three views select, persist, and restore, showing exactly one stage each:

| Picked | Persisted | Active button | Stage shown |
|---|---|---|---|
| Radar | `radar` | radar | radar |
| Map | `map` | map | atlas |
| Globe | `globe` | globe | globe |

Verified across real reloads: Radar restored as Radar (**with globe assets still unloaded — 0**),
Globe restored as Globe and **still on Globe at 13 seconds**, with `globe.gl` and the Blue Marble
texture loaded only in that case.

---

## 5. Which view is the default, and why

**Map — the flat SVG atlas — for a user with no stored preference.**

It is the only geographic view that cannot fail to render: no WebGL, no 3D library, no animation
loop, every mark a DOM node the instant `render()` returns. That was the point of the previous
change — the risk that could not be ruled out was a director opening the portfolio to a black
sphere before anyone else saw it.

Now that you have confirmed the globe renders correctly by eye, that argument is weaker than it
was, and moving the default to Globe is a reasonable thing to want. I have not done it, because it
is a product decision rather than a bug fix and you have not asked for it. Say the word and it is a
one-line change.

**Note on what you will see:** a stored preference always wins over the default. If you selected
Globe at any point, you will keep landing on Globe — that is the fix working, not the default
having changed.

---

## 6. For the next session

- The rotation rate is `autoRotateSpeed = 1.0` in `globe.js`, with the arithmetic written beside it
  (6°/s per unit). Tune there, and check by watching rather than by reading the property — that is
  exactly how the 0.35 problem survived three sessions.
- The watchdog deadline is 6 s with a 150 ms poll. If a slow machine ever trips it on a working
  globe, raise `DEADLINE_MS`; do not go back to a single check.
- My browser pane still does not composite (`visibilityState: "hidden"`, 0 rAF frames), so **I have
  still not seen either view by eye.** The healthy-globe case above was verified by simulating the
  scene appearing at 1.2 s, not by watching a real one. Your eyes remain the only ones that have
  looked at this.

---

## Regression

854 checks across 17 suites, unchanged.

| Suite | | Suite | |
|---|---|---|---|
| `test_admin_ops_t7t8` | 59/59 | `test_membership` | 46/46 |
| `test_assignment_blinding` | 44/44 | `test_pre_lock_guard` | 20/20 |
| `test_auth_session` | 52/52 | `test_research_identity` | 41/41 |
| `test_decision_sequence` | 60/60 | `test_simulation` | 27/27 |
| `test_decision_ui_t4` | 73/73 | `test_transitions` | 58/58 |
| `test_documents_b7b` | 66/66 | `test_workspace_t3t5` | 50/50 |
| `test_drive_import` | 37/37 | `test_writes_a1b` | 57/57 |
| `test_expert_reference_t6` | 59/59 | `test_export` | 64/64 |
| `test_features` | 41/41 | | |
