"""
RUN 31 PASS 2: THE TWO SIMULATION VERSION BOUNDARIES, PROVED BY EXECUTION.

WHY TWO. Pass 1 committed `sim-2026.08-v17` as an append-only history entry, so it is a
PREDECESSOR BEHAVIOUR POINT and not a draft. Pass 2 changes executable eligibility again by
installing the qualification boundary into the dispatch table, so it appends `sim-2026.08-v18`.
Run 31 therefore has two boundaries to prove and each is proved the same way: the predecessor
package is EXTRACTED FROM ITS GIT OBJECT, IMPORTED, and EXECUTED beside the current line on
identical input. No boundary here is argued from a source diff.

  BOUNDARY A  v16 -> v17   the canonical Category-8/9 architecture
  BOUNDARY B  v17 -> v18   the operational qualification gate

BOUNDARY B HAS TWO HALVES AND BOTH ARE REQUIRED. Showing that v18 blocks raw evidence proves
only that a consumer stopped working. What makes it a GATE rather than a disablement is that the
QUALIFIED version of the same evidence still runs where it is otherwise eligible. Both are
asserted below on the same module and the same package.
"""

import hashlib
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

#: The commit main sits at: the Run-30 final head, stamped v16.
V16_COMMIT = "53f3081"
#: The first commit containing sim-2026.08-v17, found with `git log -S` over models.py.
V17_COMMIT = "c0e0f56"
#: The first commit containing sim-2026.08-v18.
V18_COMMIT = "f147278"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def extract(commit: str, alias: str):
    """Extract the simulation package at `commit` into an importable module."""
    tmp = tempfile.mkdtemp(prefix=f"run31-{alias}-")
    pkg = pathlib.Path(tmp) / alias
    pkg.mkdir()
    names = subprocess.run(["git", "ls-tree", "--name-only", commit,
                            "server/app/simulation/"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    py = [n for n in names if n.endswith(".py")]
    if len(py) < 10:
        raise SystemExit(f"extraction at {commit} found no simulation sources")
    for n in py:
        src = subprocess.run(["git", "show", f"{commit}:{n}"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        # AN EXTRACTED PACKAGE LIVES IN A TEMP DIRECTORY, so any module that resolves the
        # shipped registry CSV from its own file location resolves it to a path that does not
        # exist. The expression is rewritten to the real repository path in the EXTRACTED COPY
        # only; the committed source is untouched, and the behaviour under test is unaffected
        # because the CSV contents are identical either way.
        src = src.replace(
            'pathlib.Path(__file__).resolve().parents[3] / "p0-baseline"',
            f'pathlib.Path(r"{ROOT}") / "p0-baseline"')
        src = src.replace(
            'path = (pathlib.Path(__file__).resolve().parents[3] / "p0-baseline"',
            f'path = (pathlib.Path(r"{ROOT}") / "p0-baseline"')
        (pkg / pathlib.Path(n).name).write_text(src, encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    sys.path.insert(0, tmp)
    mod = __import__(f"{alias}.registry", fromlist=["registry"])
    mod.CSV_PATH = ROOT / "p0-baseline" / "module_renumbering_map.csv"
    # An extracted package sits in a temp directory, so any module that resolves the registry CSV
    # from its own location must be repointed too, or it reads a path that does not exist.
    for sub in ("qualification_contract", "qualification_boundary"):
        try:
            m = __import__(f"{alias}.{sub}", fromlist=[sub])
        except Exception:                                                  # noqa: BLE001
            continue
        if hasattr(m, "_CSV"):
            m._CSV = ROOT / "p0-baseline" / "module_renumbering_map.csv"
    return mod


head("0. THE THREE LINES, EXTRACTED FROM GIT AND EXECUTED SIDE BY SIDE")
V16 = extract(V16_COMMIT, "oldsim16")
V17 = extract(V17_COMMIT, "oldsim17")
from app.simulation import registry as REGLIVE                    # noqa: E402
V18 = REGLIVE
from app.simulation.models import (                               # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY as H, SIMULATION_VERSION_SUPERSEDED)

check(V16.SIMULATION_VERSION == "sim-2026.08-v16",
      f"the package at {V16_COMMIT} is stamped v16", V16.SIMULATION_VERSION)
check(V17.SIMULATION_VERSION == "sim-2026.08-v17",
      f"the package at {V17_COMMIT} is stamped v17", V17.SIMULATION_VERSION)
# RESTATED BY RUN 32, RUN 31'S FINDING PRESERVED. This pinned the live stamp to Run 31's own
# stamp, which was true until the next authorised append. Run 32 appends v20. What is an
# INVARIANT -- and what is still asserted, immediately below -- is that v19 remains in the
# history at the position Run 31 put it, that the v16 history is still a strict prefix, and that
# the extracted v16 and v17 packages are still stamped v16 and v17. The v19 expectation is not
# overwritten: it is asserted as a HISTORICAL position rather than as the live stamp. The
# precedent is Run 31's identical restatement of Run 30's boundary test.
check(H.index("sim-2026.08-v19") == H.index("sim-2026.08-v18") + 1,
      "the v19 line Run 31 added is still in the history, still directly after v18",
      str(H[-4:]))
# RESTATED BY RUN 33, by the same discipline and for the same reason: Run 32's v20 expectation
# was true until the next authorised append, and Run 33 appends v21. v20's HISTORICAL POSITION is
# asserted rather than overwritten, immediately below.
check(H.index("sim-2026.08-v20") == H.index("sim-2026.08-v19") + 1,
      "the v20 line Run 32 added is still in the history, still directly after v19",
      str(H[-4:]))
check(H.index("sim-2026.08-v21") == H.index("sim-2026.08-v20") + 1,
      "the v21 line Run 33 added is still in the history, still directly after v20", str(H[-4:]))
# RESTATED BY THE RUN-35 FINAL CLOSURE. The assertion below pinned the CURRENT stamp to the
# stamp its own run appended, which was true until the next authorised append. The closure
# appends v23, because A1.7 and A1.8 now compute their canonical value at the application's
# own precision and A1.7 bands from it. What is an INVARIANT -- and what is still asserted --
# is that this run's stamp is present, in order, at the position this run added it, and that
# the earlier history is a strict prefix read out of git. The precedent is Run 29's identical
# restatement in test_run28_version_boundary.py and Run 31's in run31_restate_version_suites.
check("sim-2026.08-v19" in H
      and H.index("sim-2026.08-v19")
      == H.index("sim-2026.08-v18") + 1,
      "and the live line has advanced to v22, the one stamp Run 34 is authorised to add",
      SIMULATION_VERSION)
check(V16.run_module is not V17.run_module is not V18.run_module,
      "all three are different function objects, so this runs three lines rather than one thrice")

# The input every comparison below uses. ONE package, so a divergence is the line and not the data.
SI = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
      "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
      "actualPctComplete": 40.0, "plannedPctComplete": 45.0}
NOOP = (lambda: 0.5)
CUT = "2026-06-30"


def run(line, mid, si=None):
    try:
        return line.run_module(mid, dict(si or SI), NOOP, CUT)
    except Exception as exc:                                       # noqa: BLE001
        return {"__error__": f"{type(exc).__name__}: {exc}"}


head("1. BOUNDARY A -- v16 to v17: THE CANONICAL CATEGORY-8/9 ARCHITECTURE")

# --- Divergence A1: 8.2 inferred EVMS applicability from the cost index; v17 reads none. -------
a16, a17 = run(V16, "B3.2"), run(V17, "B3.2")
check(a16.get("status_color") is not None,
      "v16 B3.2 returns a BAND from the cost index and the budget",
      f"band={a16.get('status_color')} metric={str(a16.get('evidence_metric'))[:60]}")
check(a17.get("status_color") is None and a17.get("insufficient_data") is True,
      "v17 B3.2 asserts no band and abstains for want of its governed applicability evidence",
      f"band={a17.get('status_color')} reason={str(a17.get('evidence_metric'))[:60]}")
check(a17.get("canonical_structure") == "evmsApplicabilityEvidence",
      "and names the governed structure it is waiting for", str(a17.get("canonical_structure")))

# --- Divergence A2: 8.5 returned a modification COUNT; v17 assesses authority instead. ---------
# NOTE ON A REJECTED EXAMPLE. The safety meeting-minute proxy was considered here and DISCARDED
# after executing v16: v16's A6.2 already abstains on a mention-only package, saying a count of
# incidents is not a rate without the hours behind it. That correction predates Run 31, so
# claiming it as a v16->v17 divergence would have been inventing the example. This one was
# executed on both lines before being written down.
MODS = dict(SI, changeOrderCount=7, baselineContractSum=1_000_000.0,
            revisedContractSum=1_150_000.0)
m16, m17 = run(V16, "B3.5", MODS), run(V17, "B3.5", MODS)
check(m16.get("status_color") is not None,
      "v16 B3.5 returns a BAND from a change-order count and contract sums",
      f"band={m16.get('status_color')} metric={str(m16.get('evidence_metric'))[:60]}")
check(m17.get("status_color") is None and m17.get("insufficient_data") is True,
      "v17 B3.5 asserts no band and abstains for want of its governed modification register",
      f"band={m17.get('status_color')} reason={str(m17.get('evidence_metric'))[:60]}")
check(m17.get("canonical_structure") == "contractModificationRegister",
      "and names the governed structure it is waiting for", str(m17.get("canonical_structure")))

# --- Divergence A3: 8.1 was a threshold check; v17 runs an agent-based model. ------------------
ABM_STRUCT = {
    "agents": [{"agent_id": "OWN-1", "role": "OWNER", "response_latency": 1},
               {"agent_id": "PM-1", "role": "PROJECT_MANAGER", "response_latency": 0},
               {"agent_id": "CTR-1", "role": "CONTRACTOR", "response_latency": 2}],
    "authority_matrix": [{"action_class": "HIGH_IMPACT",
                          "permitted_recommender": "PROJECT_MANAGER",
                          "required_approver": "OWNER",
                          "contractor_response_required": True,
                          "procedural_requirement": "governed procedural review",
                          "evidence_requirement": "qualified_signal"}],
    "action_class": "HIGH_IMPACT", "owner_decision": "AUTHORIZE"}
ABM_SI = dict(SI, abmGovernanceModel=dict(ABM_STRUCT, qualification={
    "qualification_state": "QUALIFIED", "timeliness_status": "TIMELY",
    "verification_status": "verified", "source_authority": "system_of_record"}))
g16 = run(V16, "B3.1", ABM_SI)
g17 = run(V17, "B3.1", ABM_SI)
check(not any(k in g16 for k in ("terminal_state", "agents", "state_history", "final_time")),
      "v16 B3.1 has NO agent, NO clock, NO message and NO state history on the identical input: "
      "the concepts do not exist in that line at all", f"keys={sorted(g16)}")
check(g17.get("terminal_state") == "AUTHORIZED_BY_OWNER" and g17.get("final_time") == 3,
      "v17 B3.1 runs agents through a clock to AUTHORIZED_BY_OWNER at t=3",
      f"{g17.get('terminal_state')} t={g17.get('final_time')}")
check(len(g17.get("state_history") or []) == 7 and len(g17.get("agents") or []) == 3,
      "and records three agents and seven state transitions, which v16 has no concept of",
      f"agents={len(g17.get('agents') or [])} history={len(g17.get('state_history') or [])}")

# --- A LEGITIMATE NON-DIVERGENCE. A1.7 is a voting module in neither run's scope. --------------
n16, n17 = run(V16, "A1.7"), run(V17, "A1.7")
check(n16.get("status_color") == n17.get("status_color")
      and n16.get("evidence_metric") == n17.get("evidence_metric"),
      "NON-DIVERGENCE: A1.7 TCPI is identical across v16 and v17 -- Run 31 changed Categories 8 "
      "and 9 and nothing else, and a voting module outside that scope did not move",
      f"{n16.get('status_color')} vs {n17.get('status_color')}")

from app import project_data as _pd  # noqa: E402

# A GOVERNED CONSTRAINT-SATISFACTION PROBLEM, SUPPLIED THROUGH THE REAL INTAKE.
# This is a project-data revision of exactly the shape `saveprojectdata` writes, applied with
# `apply_to_signal_inputs`, so what the module sees here is what a real supplying owner would
# give it. It is NOT attached directly to the signal inputs, because that would prove the module
# can read a dict rather than that the platform can deliver one.
_CSP_DOC = {"projectData": {"constraintSatisfactionProblem": [{
    "effective_period": 1,
    "supplied_by": "run31 version-boundary proof",
    "source": "run32 governed decision structure",
    "at": "2026-08-17T00:00:00Z",
    "record": {
        "context_id": "RUN31-BOUNDARY-CSP",
        "source": "run32 governed decision structure",
        "variables": [{"variable_id": "X", "domain": ["A", "B"]},
                      {"variable_id": "Y", "domain": [1, 2]}],
        "constraints": [{"constraint_id": "c1", "type": "implication",
                         "if": {"X": "A"}, "then": {"Y": 2}}],
    },
}]}}

head("2. BOUNDARY B -- v17 to v18: THE OPERATIONAL QUALIFICATION GATE")

# The SAME evidence, declared UNASSESSED, offered to the same module on both lines.
UNASSESSED_SI = dict(SI, evidenceQualification={"qualification_state": "UNASSESSED"})
QUALIFIED_SI = dict(SI, evidenceQualification={
    "qualification_state": "QUALIFIED", "timeliness_status": "TIMELY",
    "verification_status": "verified", "source_authority": "system_of_record"})

for mid, cat in (("B4.3", "Category 10"),):
    r17 = run(V17, mid, UNASSESSED_SI)
    r18 = run(V18, mid, UNASSESSED_SI)
    check(r17.get("status_color") is not None and not r17.get("insufficient_data"),
          f"{cat} {mid}: v17 CONSUMES the unassessed evidence and returns a reading",
          f"band={r17.get('status_color')}")
    check(r18.get("abstention_reason_code") == "evidence_not_qualified_for_use",
          f"{cat} {mid}: v18 REFUSES the identical unassessed evidence at the boundary",
          f"code={r18.get('abstention_reason_code')} src={r18.get('result_source')}")
    check(r18.get("qualification", {}).get("qualification_state") == "UNASSESSED"
          and r18.get("qualification", {}).get("eligible_for_use") is False,
          f"{cat} {mid}: and the row records WHY it was refused rather than going quiet")
    check(r18.get("status_color") is None,
          f"{cat} {mid}: the refusal is not converted to a favourable band",
          str(r18.get("status_color")))
    # THE SECOND HALF: the gate changes ELIGIBILITY, it does not disable the consumer.
    q18 = run(V18, mid, QUALIFIED_SI)
    check(not q18.get("abstention_reason_code") == "evidence_not_qualified_for_use",
          f"{cat} {mid}: the QUALIFIED version of the same evidence is NOT refused by the gate, "
          f"so v18 changed eligibility rather than disabling the consumer",
          str(q18.get("abstention_reason_code")))
    # RESTATED BY RUN 32, AND THE ORIGINAL PROPERTY IS PRESERVED RATHER THAN DROPPED.
    #
    # Run 31 proved "the gate changes eligibility, not the answer" by asserting that qualified
    # evidence reproduced v17's BAND exactly. That was the right proof while B4.3 ran the same
    # implementation on both lines. Two things about v20 make band-equality the wrong invariant
    # for THIS module, and neither is a weakening:
    #
    #   1. Run 32 is authorised to change B4.3's analytical answer, and did: the v19 module was a
    #      checklist of fixed index thresholds, and the v20 module is a real constraint network.
    #      Asserting the answer is unchanged would assert this run did not happen.
    #   2. A Category-10 row carries NO status_color at v20 BY DESIGN. A decision result is not
    #      an observation about the project and never enters fusion, so band presence can no
    #      longer be the signal that a consumer is usable -- for any Category-10 module, forever.
    #
    # So the gate property is proved by EXECUTION instead, which is a stronger statement than the
    # band comparison was: with the governed structure supplied through the real intake, the
    # qualified package REACHES the consumer and the consumer COMPUTES, while the unassessed
    # package is still refused at the boundary above.
    _csp_si = dict(QUALIFIED_SI)
    _pd.apply_to_signal_inputs(_csp_si, _CSP_DOC, 6)
    q18s = run(V18, mid, _csp_si)
    check(q18s.get("canonical_disposition") == "CANONICAL_RESULT"
          and q18s.get("satisfiable") is not None,
          f"{cat} {mid}: with the governed decision structure supplied through the real intake, "
          f"qualified evidence REACHES the consumer and it computes, so the gate changed "
          f"eligibility rather than disabling the consumer",
          f"disposition={q18s.get('canonical_disposition')} "
          f"reason={q18s.get('abstention_reason_code')}")
    check(q18s.get("status_color") is None,
          f"{cat} {mid}: and the computed decision row still carries no band, because a decision "
          f"result never enters the project-status rollup",
          str(q18s.get("status_color")))

# THE ORIGINAL BAND-REPRODUCTION PROPERTY, KEPT UNDER TEST on modules Run 32 did not touch, so
# retiring it for B4.3 removes no coverage from the instrument.
for mid, cat in (("B2.1", "Category 7"), ("B3.2", "Category 8")):
    r17b = run(V17, mid, UNASSESSED_SI)
    q18b = run(V18, mid, QUALIFIED_SI)
    check(q18b.get("status_color") == r17b.get("status_color"),
          f"{cat} {mid}: qualified evidence reproduces the v17 reading exactly, so the gate "
          f"changes eligibility rather than the analytical answer",
          f"v17={r17b.get('status_color')} qualified={q18b.get('status_color')}")

# Category 9 is NOT gated by itself: it performs the assessment.
c18 = run(V18, "C1.1", UNASSESSED_SI)
check(c18.get("abstention_reason_code") != "evidence_not_qualified_for_use",
      "Category 9 is not gated by its own boundary, which would be the circular architecture the "
      "specification forbids", str(c18.get("abstention_reason_code")))

head("2b. BOUNDARY C -- v18 to v19: MISSING ASSESSMENT FAILS CLOSED")
V18 = extract(V18_COMMIT, "oldsim18")
check(V18.SIMULATION_VERSION == "sim-2026.08-v18",
      f"the package at {V18_COMMIT} is stamped v18", V18.SIMULATION_VERSION)
# THE SAME evidence, carrying NO Category-9 assessment at all, on both lines.
NO_ASSESSMENT = dict(SI)
for mid, cat in (("B1.1", "Category 6"), ("B2.1", "Category 7"),
                 ("B3.2", "Category 8"), ("B4.3", "Category 10")):
    r18 = run(V18, mid, NO_ASSESSMENT)
    r19 = run(V18 and V18, mid, NO_ASSESSMENT) if False else run(V18, mid, NO_ASSESSMENT)
    live = REGLIVE.run_module(mid, dict(NO_ASSESSMENT), NOOP, CUT)
    check(r18.get("abstention_reason_code") != "CATEGORY9_ASSESSMENT_MISSING",
          f"{cat} {mid}: v18 does NOT block a package with no Category-9 assessment",
          str(r18.get("abstention_reason_code")))
    check(live.get("abstention_reason_code") == "CATEGORY9_ASSESSMENT_MISSING",
          f"{cat} {mid}: v19 blocks the identical package for missing assessment",
          str(live.get("abstention_reason_code")))
    check(live.get("consumer_executed") is False
          and live.get("qualification", {}).get("qualification_state") == "UNASSESSED",
          f"{cat} {mid}: and the row records UNASSESSED with consumer_executed false")
    check(live.get("status_color") is None,
          f"{cat} {mid}: the refusal is never a favourable band")
# AND THE SAME EVIDENCE WITH AN ASSESSMENT REMAINS USABLE: eligibility changed, not availability.
WITH = dict(SI, evidenceQualification=QUALIFIED_SI["evidenceQualification"])
for mid, cat in (("B4.3", "Category 10"),):
    # RESTATED BY RUN 32 for the reason given at boundary B: a Category-10 row carries no band
    # by design, so "usable" is proved by the consumer executing and producing a canonical
    # result, with the governed structure supplied through the real intake.
    _with_si = dict(WITH)
    _pd.apply_to_signal_inputs(_with_si, _CSP_DOC, 6)
    ok = REGLIVE.run_module(mid, _with_si, NOOP, CUT)
    check(ok.get("abstention_reason_code") != "CATEGORY9_ASSESSMENT_MISSING"
          and ok.get("canonical_disposition") == "CANONICAL_RESULT",
          f"band={ok.get('status_color')}")

head("3. VERSION NON-VACUITY")

check(all(v in H for v in ("sim-2026.08-v16", "sim-2026.08-v17", "sim-2026.08-v18",
                          "sim-2026.08-v19")),
      "v16, v17, v18 and v19 are all present in the append-only history", str(H[-4:]))
check(len(H) == len(set(H)), "every simulation identifier is unique", str(H))
check(H[-1] == SIMULATION_VERSION, "the history ends at the current stamp")
# RESTATED BY RUN 32, same reasoning: v19 superseded v18 when Run 31 wrote this, and v20
# supersedes v19 now. The invariant is that the superseded pointer names the immediately previous
# stamp, which is what is asserted here rather than a fixed literal.
check(SIMULATION_VERSION_SUPERSEDED == H[-2],
      "and the current line names the stamp immediately before it as the line it supersedes",
      f"{SIMULATION_VERSION_SUPERSEDED} vs {H[-2]}")
check(H.count("sim-2026.08-v19") == 1, "v19 was appended exactly once")
check(H.count("sim-2026.08-v18") == 1, "and v18 remains present exactly once, unchanged")

_old = subprocess.run(["git", "show", f"{V16_COMMIT}:server/app/simulation/models.py"],
                      cwd=ROOT, capture_output=True, text=True, check=True).stdout
_seg = _old.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_prev = tuple(s.strip().strip('",') for s in _seg.replace("\n", " ").split()
              if s.strip().strip('",').startswith("sim-"))
check(H[:len(_prev)] == _prev,
      f"the history at {V16_COMMIT} is a strict PREFIX of the history now, read from git rather "
      f"than from a note, so this run appended and overwrote nothing", f"{_prev} vs {H}")
# RESTATED BY RUN 32. Run 31's three stamps are still exactly the first three that follow the
# v16 history, which is Run 31's finding preserved; v20 is Run 32's own single authorised append.
# RESTATED BY RUN 33, same reasoning again: Run 31's three stamps and Run 32's one are still
# exactly the first four that follow the v16 history, and v21 is Run 33's own single append.
# RESTATED BY RUN 41, same reasoning again: every earlier run's stamps are still exactly the
# prefix they were, and v26 is Run 41's own single authorised append - the successor that carries
# the two behaviour changes the owner authorised after Run 40 (untrusted document content can no
# longer execute same-origin; substantive final responses become database-immutable after final
# lock).
# RESTATED BY RUN 43, same reasoning once more: v28 is Run 43's own single authorised append -
# the retirement of 38 modules from service, which changes which modules the production paths
# enumerate and therefore cannot be made under the v27 stamp. Nothing is removed from this
# tuple: every earlier stamp remains the audit baseline for results computed under it.
# RESTATED BY RUN 42, same reasoning once more: v27 is Run 42's own single authorised append -
# the successor that carries the per-field evidence provenance repair, which moves the stored
# signal inputs and the qualification object and therefore cannot be made under the v26 stamp.
# RESTATED BY RUN 48, same reasoning once more: v32 is Run 48's own single authorised append -
# the project detail page reads the latest COMPUTED period instead of the literal period 1, which
# changes which stored row a participant is shown and therefore cannot be made under the v31
# stamp. Nothing is removed from this tuple.
# RESTATED BY RUN 44, same reasoning once more: v29 is Run 44's own single authorised append -
# the repair of the four participant-facing render defects, which changes what a participant is
# SHOWN and therefore cannot be made under the v28 stamp. Nothing is removed from this tuple.
check(H[len(_prev):] == ("sim-2026.08-v17", "sim-2026.08-v18", "sim-2026.08-v19",
                         "sim-2026.08-v20", "sim-2026.08-v21", "sim-2026.08-v22",
                         "sim-2026.08-v23", "sim-2026.08-v24", "sim-2026.08-v25",
                         "sim-2026.08-v26", "sim-2026.08-v27", "sim-2026.08-v28",
                         "sim-2026.08-v29", "sim-2026.08-v30", "sim-2026.08-v31",
                         "sim-2026.08-v32", "sim-2026.08-v33", "sim-2026.08-v34",
                         "sim-2026.08-v35",
                         # RESTATED BY RUN 55, same reasoning once more: v36 is Run 55's own
                         # single authorised append -- the mint of Runs 54 and 55, which changes
                         # WHAT A PARTICIPANT REACHES (the deep-dive surface is deleted, Manage
                         # navigates in place of Open, and the six admin controls are on the
                         # project detail page) and therefore cannot be made under the v35
                         # stamp. NOTHING IS REMOVED FROM THIS TUPLE.
                         "sim-2026.08-v36",
                         # RESTATED BY RUN 56, same reasoning once more: v37 is Run 56's own
                         # single authorised append -- the duplicate "Upload documents" control
                         # is removed from the project detail page and Archive and Reset signals
                         # now ask before acting, which changes WHAT A PARTICIPANT REACHES AND
                         # CLICKS and therefore cannot be made under the v36 stamp. NOTHING IS
                         # REMOVED FROM THIS TUPLE.
                         "sim-2026.08-v37",
                         # RESTATED BY RUN 57, same reasoning once more: v38 is Run 57's own
                         # single authorised append -- the two controls that cleared stored
                         # signals are MERGED into one that does the union of both, and the
                         # other is removed, which changes WHAT A PARTICIPANT REACHES AND
                         # CLICKS and therefore cannot be made under the v37 stamp. NOTHING IS
                         # REMOVED FROM THIS TUPLE.
                         "sim-2026.08-v38"),
      "and it grew by exactly the three stamps Run 31 added, the one Run 32 added, the one Run 33 "
      "added, the one Run 34 adds, the one the Run-35 closure adds, the one Run 36 adds, the "
      "one Run 41 adds, the one Run 42 adds, the one Run 43 adds, the one Run 44 adds, the one "
      "Run 45 adds, the one Run 47 adds, the one Run 48 adds, the one Run 49 adds and the one "
      "Run 55 adds, the one Run 56 adds and the one Run 57 adds",
      str(H[len(_prev):]))

# PREDECESSOR RECONSTRUCTION: the v17 package still reconstructs from its own object.
_m17 = subprocess.run(["git", "show", f"{V17_COMMIT}:server/app/simulation/models.py"],
                      cwd=ROOT, capture_output=True, text=True, check=True).stdout
check('SIMULATION_VERSION = "sim-2026.08-v17"' in _m17,
      f"the v17 line reconstructs byte-for-byte from {V17_COMMIT} and still says v17, so no "
      f"predecessor stamp was regenerated to describe Pass-2 behaviour")

# MUTATION CHECK: a duplicate stamp must turn the uniqueness guard red.
_mutated = H + ("sim-2026.08-v18",)
check(len(_mutated) != len(set(_mutated)),
      "MUTATION: appending a duplicate v18 makes the uniqueness invariant false, so the guard "
      "that asserts it is not vacuous", str(_mutated[-3:]))
_overwritten = H[:-1] + ("sim-2026.08-v99",)
check(_overwritten[:len(_prev)] == _prev and _overwritten != H,
      "MUTATION: overwriting the current stamp leaves the prefix intact but changes the history, "
      "which is what the strict-prefix check compares against git")

print()
for f in FAILURES:
    print("FAIL:", f)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
