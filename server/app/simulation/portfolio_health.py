"""
THE PRODUCTION ROUTE FOR PORTFOLIO HEALTH, v21 (Run 33).

WHAT THIS IS. The single dispatcher that assembles the governed portfolio cohort from the
signal inputs the platform already stores per project, and runs the canonical v8 layer over it.
`documents.run_and_store` calls exactly this and nothing else for Group D.

WHAT IT IS NOT. It is not a second copy of the analysis: every number comes from
`canonical_v8`. And it is not a second intake: the four governed portfolio structures arrive
through `project_data.apply_to_signal_inputs`, the same governed, period-effective, append-only
route every canonical structure since Run 28 arrives through. Nothing here reads a test object,
and nothing here manufactures a cohort out of whatever projects happen to exist.

THE v20 ROUTE IS PRESERVED AND UNREACHABLE. `portfolio.compute_portfolio` still exists, byte for
byte, because Runs 2, 6, 13, 14, 15, 17 and 20 recorded findings ABOUT IT and deleting it would
delete the subject of those findings. It is HISTORICAL ONLY: production resolves Group D through
this file, `assert_not_reachable` below proves it mechanically from the live call site, and the
historical suites continue to execute the legacy function directly and to assert exactly what
they always asserted.

THE COHORT ANCHOR. The cohort definition and the feature schema are read from the project being
computed. Every other project contributes its own feature record and its own signal history, and
a project that supplies neither is a declared member with no record -- reported as such, never
filled in with a stand-in.
"""

from __future__ import annotations

import inspect
from typing import Any, Mapping, Sequence

from . import canonical_v8 as V8

COHORT_KEY = "portfolioCohort"
SCHEMA_KEY = "portfolioFeatureSchema"
RECORD_KEY = "portfolioFeatureRecord"
HISTORY_KEY = "portfolioSignalHistory"

CALIBRATION_KEY = "portfolioCalibrationRecord"

PORTFOLIO_STRUCTURE_KEYS: tuple[str, ...] = (COHORT_KEY, SCHEMA_KEY, RECORD_KEY, HISTORY_KEY,
                                             CALIBRATION_KEY)

#: Named so a guard asserts against a contract rather than a sentence.
LEGACY_V20_ROUTE_REACHABLE = False


# ---------------------------------------------------------------------------------------------
# RUN 43B, THE PORTFOLIO HEALTH OFFLOAD (section 5.3)
# ---------------------------------------------------------------------------------------------
#
# Run 43 retired D1.1 to D1.5. `canonical_v8` computes those same five readings under the names
# PH.1 to PH.5, and `canonical_v8.RESULT_KEYS` is the mapping between the two -- so retiring the
# identifiers in the registry did NOT stop the computation: this dispatcher went on calling
# `V8.compute_portfolio_health` and storing five readings for five modules that no longer exist
# in the taxonomy. That is the gap section 5.3 names, and this is the offload.
#
# THE OFFLOAD IS DERIVED, NOT DECLARED. `live_portfolio_modules()` intersects the PH-to-D map
# with the live registry, exactly as `registry.available_modules()` intersects the implemented
# set with the live registry. There is no list here that says "Portfolio Health is off"; there
# is a registry that no longer carries D1.1 to D1.5, and a computation that is only performed
# for identifiers the registry still carries. If a future run reinstates any of the five in
# `p0-baseline/module_renumbering_map.csv`, this route resumes for exactly those and for no
# others, with no edit here. That is the ninth repetition of the programme's most-repeated
# failure avoided: a stated set that drifts from the computed one.
#
# THE FORMULAS ARE KEPT, exactly as Run 43 kept the single-project formulas. `canonical_v8` is
# untouched. Retiring a module is a statement about the taxonomy and the explanation burden, not
# a claim that its arithmetic is wrong, and Runs 15, 33 and 34 recorded findings ABOUT these
# five implementations that would become unreadable if the code went. What changes is that no
# production path reaches them.
#
# NO CONTROL WAS ADDED, MOVED OR REMOVED (hard limit 4, stop condition 7.6). The snapshot still
# has the same shape, is still stored on every compute, and still carries `structure_absent`,
# `insufficient_data` and `message` -- the three keys the portfolio card already branches on for
# the abstaining case it has always been able to render. The card's own code is not touched.


def live_portfolio_modules() -> tuple[str, ...]:
    """
    The Group D portfolio identifiers the registry still carries, in canonical order.

    Empty after Run 43. Derived from the registry rather than restated, so this answers the
    question by reading the authority instead of remembering it.
    """
    from .registry import registry_index

    live = set(registry_index())
    return tuple(d for d in sorted(V8.RESULT_KEYS) if d in live)


#: The reason recorded on every offloaded snapshot. One sentence, written once, so the API, the
#: stored row and any surface that reads either all quote the same words.
#: NAMING_AUTHORITY section 4 governs this sentence: no module id and no module number appears
#: in it, and it names the group and its purpose instead. It says "no longer part of" rather
#: than "retired from the registry" because the registry is an internal artifact a reader of the
#: portfolio card has no way to see, and describing a surface by an artifact behind it is how
#: this programme has repeatedly produced text that only its author could read.
RETIRED_REASON = (
    "Portfolio Health is no longer part of the analytical taxonomy, so no portfolio-level "
    "reading is produced. Project Status is unaffected: Portfolio Health never contributed to "
    "it."
)


def _histories_from(si: Mapping[str, Any], project_id: str) -> list[dict]:
    raw = si.get(HISTORY_KEY)
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        entries = raw.get("signals")
        entries = entries if isinstance(entries, (list, tuple)) else [raw]
    elif isinstance(raw, (list, tuple)):
        entries = raw
    else:
        return []
    out = []
    for e in entries:
        if not isinstance(e, Mapping):
            continue
        e = dict(e)
        e.setdefault("project_id", project_id)
        out.append(e)
    return out


def assemble(current_id: str, current_si: Mapping[str, Any],
             others: Sequence[tuple[str, Mapping[str, Any]]]) -> dict[str, Any]:
    """
    The governed cohort inputs, from the stored signal inputs of the projects themselves.

    `others` is (project_id, signal_inputs) for every OTHER project the platform would show in
    one portfolio view. Membership is decided by the cohort's own declared `project_ids`, never
    by which rows the query happened to return: a project that is not a declared member of the
    cohort contributes nothing even if it carries a feature record.
    """
    cohort = current_si.get(COHORT_KEY)
    schema = current_si.get(SCHEMA_KEY)
    declared = []
    if isinstance(cohort, Mapping) and isinstance(cohort.get("project_ids"), (list, tuple)):
        declared = [str(p) for p in cohort["project_ids"]]
    records: list[dict] = []
    histories: list[dict] = []
    supplied = [(str(current_id), current_si)] + [(str(p), si) for p, si in others]
    seen: set[str] = set()
    for pid, si in supplied:
        if pid in seen or not isinstance(si, Mapping):
            continue
        seen.add(pid)
        if declared and pid not in declared:
            continue
        rec = si.get(RECORD_KEY)
        if isinstance(rec, Mapping):
            rec = dict(rec)
            rec.setdefault("project_id", pid)
            records.append(rec)
        histories.extend(_histories_from(si, pid))
    records.sort(key=lambda r: str(r.get("project_id")))
    histories.sort(key=lambda h: (str(h.get("project_id")), str(h.get("signal_id"))))
    # RUN 34. The governed calibration records ride with the COHORT ANCHOR, not with each member:
    # a parameter is a property of the cohort's model, not of one project's evidence, and letting
    # members supply their own would let one project change the weighting the whole cohort is
    # read under.
    raw_cal = current_si.get(CALIBRATION_KEY)
    if isinstance(raw_cal, Mapping):
        calibration = [raw_cal]
    elif isinstance(raw_cal, (list, tuple)):
        calibration = [c for c in raw_cal if isinstance(c, Mapping)]
    else:
        calibration = []
    return {"cohort": cohort, "schema": schema, "records": records, "histories": histories,
            "calibration": calibration}


def compute_portfolio_health_snapshot(current_id: str, current_si: Mapping[str, Any],
                                      others: Sequence[tuple[str, Mapping[str, Any]]],
                                      period_cutoff: Any) -> dict[str, Any]:
    """
    The stored `portfolio_snapshot` for one project, computed through the canonical v21 route.

    Always returns a snapshot, including when the governed structure is absent: an absent cohort
    is a REPORTED ABSTENTION carrying its reason, not a null the ledger has to interpret.
    """
    # RUN 43B, THE OFFLOAD. Checked BEFORE `assemble`, so a retired Portfolio Health does not
    # read the cohort, the schema, the feature records, the signal histories or the calibration
    # record either. An offload that still assembled its inputs would leave the intake path
    # live and the claim "Portfolio Health computes nowhere" false in the part that matters.
    if not live_portfolio_modules():
        return _retired_snapshot(current_id, period_cutoff)

    inputs = assemble(current_id, current_si, others)
    run = V8.compute_portfolio_health(inputs["cohort"], inputs["schema"],
                                      inputs["records"], inputs["histories"],
                                      inputs["calibration"])
    cohort = run["cohort"]
    snapshot: dict[str, Any] = {
        "ok": True,
        "id": str(current_id),
        "route": "canonical_v8",
        "simulation_layer": "canonical_v8",
        "evidence_class": V8.PROGRAMME_CONTEXT_EVIDENCE,
        "use": V8.INFORM_ONLY,
        "voting": False,
        "creates_project_evidence": False,
        "authority_note": V8.AUTHORITY_NOTE,
        "structure_absent": run["structure_absent"],
        "cohort": cohort,
        "portfolio_size": (cohort or {}).get("cohort_size", 0),
        "results": run["results"],
        "period_cutoff": str(period_cutoff),
    }
    if run["structure_absent"]:
        reason = run["results"]["cat8_1_isolation_forest"]["abstention_reason"]
        snapshot["insufficient_data"] = True
        snapshot["message"] = reason
    return snapshot


def _retired_snapshot(current_id: str, period_cutoff: Any) -> dict[str, Any]:
    """
    The snapshot stored for a project when no Group D module remains in the registry.

    It is a REPORTED RETIREMENT, not a null and not an empty dict. The distinction matters to
    every reader: `structure_absent` has always meant "the governed cohort was not supplied",
    which is a statement about this project's evidence and invites supplying it. Retirement is a
    statement about the taxonomy and no evidence will change it. A surface that cannot tell the
    two apart would go on inviting a user to supply a cohort for an analysis that no longer
    exists, so `retired` is carried as its own key and `results` is empty rather than five
    abstentions -- there are no longer five modules to abstain.
    """
    return {
        "ok": True,
        "id": str(current_id),
        "route": "retired",
        "simulation_layer": None,
        "evidence_class": V8.PROGRAMME_CONTEXT_EVIDENCE,
        "use": V8.INFORM_ONLY,
        "voting": False,
        "creates_project_evidence": False,
        "authority_note": V8.AUTHORITY_NOTE,
        "retired": True,
        "structure_absent": False,
        "cohort": None,
        "portfolio_size": 0,
        "results": {},
        "insufficient_data": True,
        "message": RETIRED_REASON,
        "period_cutoff": str(period_cutoff),
    }


# ---------------------------------------------------------------------------------------------
# THE OTHER HALF OF EVERY HISTORICAL PORTFOLIO ASSERTION
# ---------------------------------------------------------------------------------------------

def assert_not_reachable(check) -> None:
    """
    Prove current production does not reach the superseded v20 portfolio implementation.

    Derived from the LIVE SOURCE of the one production call site rather than from a list, because
    a list would still say what it said after someone reconnected the proxy. `documents.py`'s
    `run_and_store` is the only place a portfolio snapshot is produced in production; its source
    is read here and asserted to call this module and not `compute_portfolio`.
    """
    from .. import documents

    src = inspect.getsource(documents.run_and_store)
    check("compute_portfolio_health_snapshot" in src,
          "production's only portfolio call site routes through the canonical v21 dispatcher",
          "compute_portfolio_health_snapshot present")
    check("compute_portfolio(" not in src,
          "and does not call the superseded v20 compute_portfolio",
          "compute_portfolio( absent")
    check(LEGACY_V20_ROUTE_REACHABLE is False,
          "and the legacy route is declared unreachable",
          str(LEGACY_V20_ROUTE_REACHABLE))
    from . import portfolio as legacy
    check(callable(getattr(legacy, "compute_portfolio", None)),
          "while the superseded implementation is PRESERVED for historical reconstruction",
          "portfolio.compute_portfolio still exists")
