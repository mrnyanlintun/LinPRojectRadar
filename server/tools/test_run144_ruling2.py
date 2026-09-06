"""
RUN 144 RULING 2 -- a carried reading composes no mitigation and makes NO MODEL CALL.

Every figure this file prints was TAKEN by this file. Run from `server/`:

    PYTHONPATH=. python tools/test_run144_ruling2.py

The owner ruled: NO CHANGE. Replaying an earlier period's mitigation verbatim against a reading
nobody produced this period would present stale advice as current, so the exclusion Run 143 built
stands. Nothing in `app/mitigation.py`'s exclusion logic is edited by Run 144.

WHAT THIS FILE ADDS. Ruling 1 changed WHICH readings carry -- an A6 measure refused by the
Category-9 gate now carries -- and the mitigation layer must not start composing against the
newly carried ones. Run 142 recorded a band colour emitted without a band, so this is verified by
COUNTING PROVIDER CALLS, not by assuming that returning None implies no call. `compose_one` and
`mitigations_for_card` both take `caller=`, so the count is taken at the provider boundary
itself: a counting caller that RAISES if it is ever reached for a carried module.
"""
from __future__ import annotations

import sys
from typing import Any

from app.mitigation import build_context, compose_one, mitigations_for_card

FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


class CountingCaller:
    """Stands where the provider stands. Records every call; never contacts anything."""

    def __init__(self) -> None:
        self.calls: list[Any] = []

    def __call__(self, blocks, cfg, environ=None) -> str:
        self.calls.append(blocks)
        return "- Do the thing that would move the band.\n"


class NullStore:
    """No replay, no persistence: every composition that happens here reaches the caller."""

    def get(self, period, mid, fingerprint):
        return None

    def put(self, *a, **k):
        return None


class Cfg:
    provider = "test"
    model = "test-model"


def row(mid: str, *, band: str, carried: bool) -> dict[str, Any]:
    """A stored module row shaped as `compute_project` stores one."""
    r: dict[str, Any] = {
        "module_id": mid,
        "group": mid[0],
        "status_color": band,
        "evidence_metric": "the reading sentence",
        "band_boundary": "Amber begins at 0.90 and Green at 0.95.",
        "value": 0.80,
    }
    if carried:
        r.update({"carried": True, "carried_from_period": "P1", "carried_from_age": 3,
                  "carried_evidence": "P1's own sentence.",
                  "carried_reason": "no Category-9 assessment was declared this period"})
    return r


# ------------------------------------------------------ the exclusion is at the context gate
CARRIED = row("A6.1", band="Red", carried=True)
CURRENT = row("A2.1", band="Red", carried=False)

check("a carried adverse reading builds NO mitigation context",
      build_context(CARRIED) is None)
check("an identical CURRENT adverse reading DOES build one -- so the None above is about "
      "carrying and not about the fixture",
      build_context(CURRENT) is not None)

# ------------------------------------------------------------------ PROOF 3: counted, not assumed
caller = CountingCaller()
out = compose_one(CARRIED, store=NullStore(), period=4, cfg=Cfg(), environ={}, caller=caller)
check("proof 3: compose_one returns nothing for a carried reading", out is None)
check("proof 3: and it made ZERO provider calls", len(caller.calls) == 0,
      f"calls = {len(caller.calls)}")

caller2 = CountingCaller()
out2 = compose_one(CURRENT, store=NullStore(), period=4, cfg=Cfg(), environ={}, caller=caller2)
check("proof 3 control: a current adverse reading DOES compose", out2 is not None)
check("proof 3 control: and it made EXACTLY ONE provider call", len(caller2.calls) == 1,
      f"calls = {len(caller2.calls)}")

# ------------------------------------- and at the card level, where the population is mixed
adverse = [{"module_id": "A6.1"}, {"module_id": "A2.1"}]     # the card's real ordered shape
caller3 = CountingCaller()
entries = mitigations_for_card(None, "PRJ-R144", 4, adverse, [CARRIED, CURRENT],
                               environ={"MITIGATION_PROVIDER": "test"}, caller=caller3)
ids = [e["module_id"] for e in entries]
print(f"\ncard population: {[r['module_id'] for r in adverse]}   "
      f"mitigations composed for: {ids}   provider calls: {len(caller3.calls)}")
check("proof 3: the card composes for the current reading only",
      ids == ["A2.1"], str(ids))
check("proof 3: one adverse row in, one call out -- the carried row consumed no call",
      len(caller3.calls) == 1, f"calls = {len(caller3.calls)}")
check("proof 3: the carried module gets NO block at all -- not an empty one",
      not any(e["module_id"] == "A6.1" for e in entries))

# ------------------------- the exclusion holds for a carried reading of ANY adverse band, and
# ------------------------- for the newly-carrying Category-9 population ruling 1 created
for band in ("Red", "Amber", "Yellow"):
    for mid in ("A6.1", "A6.2", "A6.3", "A6.4"):
        c = CountingCaller()
        r = compose_one(row(mid, band=band, carried=True), store=NullStore(), period=4,
                        cfg=Cfg(), environ={}, caller=c)
        check(f"a carried {band} on {mid} (ruling 1's new carriers) composes nothing "
              f"and calls nothing", r is None and not c.calls,
              f"entry={r is not None}, calls={len(c.calls)}")

# ------------------------------ FAULT: remove the exclusion and the call happens, so the count
# ------------------------------ above is about the exclusion and not about an inert fixture
NOT_MARKED = dict(CARRIED)
NOT_MARKED.pop("carried")
caller4 = CountingCaller()
r4 = compose_one(NOT_MARKED, store=NullStore(), period=4, cfg=Cfg(), environ={}, caller=caller4)
check("FAULT: the SAME row with the carrying marker removed composes and calls once",
      r4 is not None and len(caller4.calls) == 1,
      f"entry={r4 is not None}, calls={len(caller4.calls)}")

print()
if FAILS:
    print(f"{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("ALL CHECKS PASSED")
