"""
RUN 36. THE PRODUCTION FILES THIS RUN CHANGED, DECLARED.

WHY THIS FILE EXISTS, and it is the Run-28/29/30/31/32/33 precedent unchanged. The Run-20
baseline freeze compares production bytes against a pinned baseline, and the declared-changes
guard requires the differing set and the declared set to be EXACTLY equal -- so an undeclared
production edit is red and a declared file that was never touched is red too.

IT IS DECLARED HERE AND NOT FOLDED INTO AN EARLIER RUN'S LIST. A run's manifest is the record of
what THAT run did, and merging them would falsify both.

RUN 36 CREATED NO PRODUCTION FILE. It changed exactly one, and the change is the withdrawal of a
band rather than the addition of one.

Each entry is (authority, path, why).
"""

from __future__ import annotations

_OWNER = ("owner supervisory contract of 2026-08-19 for Run 36, section 2 outcome D: an "
          "unresolved parameter may not be allowed to determine an authoritative current "
          "result, and section 6: reachable unsupported parameters producing authoritative "
          "output must be zero")

#: Production files Run 36 CREATED. None.
RUN36_NEW_PRODUCTION_FILES: dict[str, str] = {}

#: Production files Run 36 CHANGED.
RUN36_PRODUCTION_CHANGES: dict[str, tuple[str, str, str]] = {
    "A1.1": (
        _OWNER,
        "server/app/simulation/models_sim.py",
        "A1.1 Monte Carlo EAC Forecast withdrew its status band. Derived mechanically rather "
        "than transcribed: of the 100 scientific targets executed through registry.run_module on "
        "the controlled corpus, six leave the abstention branch, and exactly ONE -- A1.1 -- "
        "carried both a status_color and an UNSUPPORTED parameter classification. Its ten and "
        "five per cent boundaries over the P80 overrun percentage are cited to nothing inside or "
        "outside this repository, no calibration set exists from which they could be fitted or "
        "tested, and the supervisory specification's own pass ceiling for A1.1 is "
        "METHOD_PASS_CALIBRATION_PENDING. Rule 2 of canonical_v3.py already requires a caller "
        "with no evidence-established boundary to emit the number with calibration pending and "
        "assert no colour, which is what A6.1, A6.2 and A6.3 already do; A1.1 now joins them. "
        "`mc_status` is PRESERVED rather than deleted and production cannot reach it. THE FIGURE "
        "DID NOT MOVE: the v23 line extracted from git object "
        "dafc35d35bafe5af76e1ce48ef7daceab9daed2c returns overrun_pct_p80 12.104441685525892 on "
        "the controlled corpus and 11.983407036630878 on the lineage fixture, identical to the "
        "current line on both, so what moved is the colour and nothing else."),
}
