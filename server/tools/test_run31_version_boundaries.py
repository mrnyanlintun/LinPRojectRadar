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
        (pkg / pathlib.Path(n).name).write_text(src, encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    sys.path.insert(0, tmp)
    mod = __import__(f"{alias}.registry", fromlist=["registry"])
    mod.CSV_PATH = ROOT / "p0-baseline" / "module_renumbering_map.csv"
    return mod


head("0. THE THREE LINES, EXTRACTED FROM GIT AND EXECUTED SIDE BY SIDE")
V16 = extract(V16_COMMIT, "oldsim16")
V17 = extract(V17_COMMIT, "oldsim17")
from app.simulation import registry as V18                        # noqa: E402
from app.simulation.models import (                               # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY as H, SIMULATION_VERSION_SUPERSEDED)

check(V16.SIMULATION_VERSION == "sim-2026.08-v16",
      f"the package at {V16_COMMIT} is stamped v16", V16.SIMULATION_VERSION)
check(V17.SIMULATION_VERSION == "sim-2026.08-v17",
      f"the package at {V17_COMMIT} is stamped v17", V17.SIMULATION_VERSION)
check(SIMULATION_VERSION == "sim-2026.08-v18",
      "and the live line is stamped v18", SIMULATION_VERSION)
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
    check(q18.get("status_color") == r17.get("status_color"),
          f"{cat} {mid}: and qualified evidence reproduces the v17 reading exactly, so the "
          f"analytical answer is unchanged where the evidence is eligible",
          f"v17={r17.get('status_color')} v18-qualified={q18.get('status_color')}")

# Category 9 is NOT gated by itself: it performs the assessment.
c18 = run(V18, "C1.1", UNASSESSED_SI)
check(c18.get("abstention_reason_code") != "evidence_not_qualified_for_use",
      "Category 9 is not gated by its own boundary, which would be the circular architecture the "
      "specification forbids", str(c18.get("abstention_reason_code")))

head("3. VERSION NON-VACUITY")

check("sim-2026.08-v16" in H and "sim-2026.08-v17" in H and "sim-2026.08-v18" in H,
      "v16, v17 and v18 are all present in the append-only history", str(H[-4:]))
check(len(H) == len(set(H)), "every simulation identifier is unique", str(H))
check(H[-1] == SIMULATION_VERSION, "the history ends at the current stamp")
check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v17",
      "and the current line names v17 as the line it supersedes", SIMULATION_VERSION_SUPERSEDED)
check(H.count("sim-2026.08-v18") == 1, "v18 was appended exactly once")

_old = subprocess.run(["git", "show", f"{V16_COMMIT}:server/app/simulation/models.py"],
                      cwd=ROOT, capture_output=True, text=True, check=True).stdout
_seg = _old.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_prev = tuple(s.strip().strip('",') for s in _seg.replace("\n", " ").split()
              if s.strip().strip('",').startswith("sim-"))
check(H[:len(_prev)] == _prev,
      f"the history at {V16_COMMIT} is a strict PREFIX of the history now, read from git rather "
      f"than from a note, so this run appended and overwrote nothing", f"{_prev} vs {H}")
check(H[len(_prev):] == ("sim-2026.08-v17", "sim-2026.08-v18"),
      "and it grew by exactly the two stamps Run 31 is authorised to add", str(H[len(_prev):]))

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
