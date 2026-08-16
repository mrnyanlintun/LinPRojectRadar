"""
RUN 30 CLOSURE -- THE OPERATIONAL ROUTE TRACER.

WHY THIS EXISTS. The Run-30 first pass built a correct, fully oracled canonical Category-7 layer
that production never called, and every direct-call proof of that layer was green throughout the
defect. So nothing here asks a function what it would do. It EXECUTES the production entry point
and records, from the interpreter itself, which functions actually ran.

`sys.setprofile` is used rather than a wrapper or a decorator, because a wrapper is a thing that
can be bypassed by the very routing defect being looked for, and a decorator has to be applied to
a hand-written list of targets -- which is the vacuity the closure contract names explicitly. The
profiler sees whatever really executed, including anything reached through a path nobody thought
to enumerate.
"""

from __future__ import annotations

import sys
from typing import Any, Callable


def trace_calls(fn: Callable[[], Any]) -> tuple[Any, set[str], str | None]:
    """
    Run `fn()` and return (result, {"module:qualname", ...}, exception repr or None).

    Every Python function entered during the call is recorded as `module:qualname`, so a caller
    can ask "did `app.simulation.canonical_v5:marcos` actually execute" rather than "does the
    dispatcher table say it should have".
    """
    seen: set[str] = set()

    def profile(frame, event, arg):          # noqa: ANN001
        if event != "call":
            return
        code = frame.f_code
        module = frame.f_globals.get("__name__", "?")
        seen.add(f"{module}:{code.co_qualname}")

    old = sys.getprofile()
    sys.setprofile(profile)
    try:
        out = fn()
        err = None
    except Exception as exc:                 # noqa: BLE001
        out = None
        err = repr(exc)[:200]
    finally:
        sys.setprofile(old)
    return out, seen, err


def canonical_hits(seen: set[str]) -> set[str]:
    """Everything in the v5 canonical layer that really executed."""
    return {s for s in seen if s.startswith("app.simulation.canonical_v5:")}


#: The legacy Category-7 proxy implementations, named by the MODULE they live in rather than by a
#: hand-kept list of function names. `legacy_hits` asks the interpreter which functions in those
#: modules ran; it does not consult a table of what should have run.
LEGACY_PROXY_MODULES = (
    "app.simulation.models_evc",
    "app.simulation.models_fuzzy",
)

#: Functions in those modules that are NOT legacy Category-7 proxy arithmetic: the thin canonical
#: runners themselves, and shared helpers that carry no Category-7 method. Anything else executing
#: in those modules during a Category-7 route is legacy proxy arithmetic.
NON_PROXY_QUALNAMES = frozenset({
    "EVC_CANONICAL", "FUZZY_CANONICAL", "_canonical_runner", "_disabled_runner",
    "_lab_runner", "_abstain", "_result", "_route",
})


def legacy_hits(seen: set[str], allowed: frozenset[str] = NON_PROXY_QUALNAMES) -> set[str]:
    out: set[str] = set()
    for s in seen:
        mod, _, qual = s.partition(":")
        if mod in LEGACY_PROXY_MODULES and qual.split(".")[0] not in allowed:
            out.add(s)
    return out
