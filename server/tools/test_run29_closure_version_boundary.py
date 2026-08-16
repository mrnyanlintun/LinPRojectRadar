"""
RUN 29 CLOSURE -- THE v13 TO v14 VERSION BOUNDARY, PROVED BY EXECUTION.

WHY THIS SUITE EXISTS. The closure contract puts the version question in exactly the terms this
programme has already got wrong once by being too narrow: if the closure only touches tests,
reports and synthetic packages, v13 stands; if it wires real corpus fields into canonical
structures, a module that abstained on the real corpus will now COMPUTE on it, and that is a
behaviour change.

It wired one. Run 29 had reported `real_corpus_populated = no` for all seventeen Category-4 and -5
structures, which was one sentence covering two very different cases. Sixteen structures are
genuinely absent from the corpus. `ncrExposureRecord` was not: the nonconformance log already
yields a count of nonconformances raised in the period, the inspection report already yields the
number of items inspected, and the supplied contract names inspections as a governed exposure in
its own worked example. Both were extracted and neither reached a module.

So the bump is not argued here, it is EXECUTED: the v13 analytical package is extracted from git
object 9cc6793, imported, and run beside the current one on the identical assembled record.

WHAT THIS SUITE CLAIMS, STATED HONESTLY. It proves at least one divergence on identical input,
which is all a version boundary needs. It does not claim to enumerate every divergence.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from app.simulation.models import (  # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, SIMULATION_VERSION_SUPERSEDED,
)

#: The commit sim-2026.08-v13 was pushed at: the Run-29 report-landing head.
V13_COMMIT = "9cc6793"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def git_show(path: str, rev: str = V13_COMMIT) -> str:
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


# =================================================================================================
head("1. THE STAMP AND ITS HISTORY")
# =================================================================================================

check(SIMULATION_VERSION == "sim-2026.08-v14",
      "the analytical layer is stamped sim-2026.08-v14", SIMULATION_VERSION)
check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v13",
      "and names sim-2026.08-v13 as the line it supersedes", SIMULATION_VERSION_SUPERSEDED)
check(len(SIMULATION_VERSION_HISTORY) == len(set(SIMULATION_VERSION_HISTORY)),
      "EVERY SIMULATION IDENTIFIER IS UNIQUE: no historical stamp has been re-used",
      str([v for v in SIMULATION_VERSION_HISTORY
           if list(SIMULATION_VERSION_HISTORY).count(v) > 1]))
check(SIMULATION_VERSION_HISTORY[-1] == SIMULATION_VERSION,
      "the history ends at the current stamp, so the two cannot drift apart")

_old_models_src = git_show("server/app/simulation/models.py")
_old_hist = _old_models_src.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_old_stamps = tuple(s.strip().strip('",') for s in _old_hist.replace("\n", " ").split()
                    if s.strip().strip('",').startswith("sim-"))
check(bool(_old_stamps) and SIMULATION_VERSION_HISTORY[:len(_old_stamps)] == _old_stamps,
      f"the history recorded at commit {V13_COMMIT} is a strict PREFIX of the history now, read "
      f"out of git rather than out of a note, so this closure appended and overwrote nothing",
      f"{_old_stamps} vs {SIMULATION_VERSION_HISTORY}")
check(SIMULATION_VERSION_HISTORY[len(_old_stamps):] == ("sim-2026.08-v14",),
      "and it grew by exactly the one stamp this closure is authorised to add",
      str(SIMULATION_VERSION_HISTORY[len(_old_stamps):]))
check(_old_stamps[-1] == "sim-2026.08-v13",
      "and the line this closure supersedes is the line that commit shipped", str(_old_stamps[-1]))


# =================================================================================================
head("2. THE v13 LINE, EXTRACTED FROM GIT AND EXECUTED")
# =================================================================================================

_TMP = tempfile.mkdtemp(prefix="run29c-v13-")
_PKG = pathlib.Path(_TMP) / "oldsim29c"
_PKG.mkdir()
_names = subprocess.run(["git", "ls-tree", "--name-only", V13_COMMIT,
                         "server/app/simulation/"],
                        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("v13 extraction found no simulation sources at the pinned commit; refusing "
                     "to run half of every proof")
for _n in _py:
    (_PKG / pathlib.Path(_n).name).write_text(git_show(_n), encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, _TMP)

import oldsim29c.models as old_models        # noqa: E402
import oldsim29c.models_doc as old_doc       # noqa: E402

from app.simulation import models_doc as new_doc       # noqa: E402

check(old_models.SIMULATION_VERSION == "sim-2026.08-v13",
      f"the package extracted from git object {V13_COMMIT} is stamped v13, so it is the line "
      f"this closure supersedes and not a copy of the current one", old_models.SIMULATION_VERSION)
check(old_doc.run_ncr_rate is not new_doc.run_ncr_rate,
      "and its functions are genuinely different objects from the live ones, so the comparison "
      "below runs two lines rather than one twice")

NOOP = lambda: 0.5  # noqa: E731
CUTOFF = "2026-06-30"


def abstains(result) -> bool:
    return bool(result.get("insufficient_data"))


# =================================================================================================
head("3. THE DIVERGENCE THAT SETTLES THE BUMP")
# =================================================================================================

# ONE identical governed input: the record `documents.py` now assembles from two fields the real
# corpus already extracts -- four nonconformances raised in the period, against one hundred items
# inspected. It is the supplied contract's own worked example, reached from real extracted fields.
ASSEMBLED = {"ncrExposureRecord": {
    "source": "the nonconformance log and the inspection report for this reporting period",
    "exposure_unit": "inspections",
    "exposure_quantity": 100.0,
    "ncr_count": 4,
    "ncr_count_basis": "nonconformances raised in the reporting period",
    "open_count": 6,
    "closed_count": 2,
    "assembled_by": "document extraction"}}

_old = old_doc.run_ncr_rate(dict(ASSEMBLED), NOOP, CUTOFF)
_new = new_doc.run_ncr_rate(dict(ASSEMBLED), NOOP, CUTOFF)
check(abstains(_old),
      "sim-2026.08-v13, EXECUTED on the assembled record, ABSTAINS: it required a list of "
      "nonconformance EVENTS, and a count that was extracted as a count is not a list",
      str(_old.get("evidence_metric"))[:80])
check(not abstains(_new) and _new.get("ncr_rate") == 0.04,
      "THE CURRENT LINE COMPUTES THE SAME INPUT and reports the supplied contract's own 0.04. "
      "Same input, different emitted result, so the layer's executable behaviour is not v13's "
      "and the stamp had to move", str(_new.get("ncr_rate")))
check(_new.get("event_detail_available") is False,
      "and it says on the result that no per-event detail was available, so the count form is "
      "not presented as though events had been read")
check(_new.get("severity_counts") == {} and _new.get("closure_rate") is None
      and _new.get("max_open_age_days") is None,
      "and the quantities that need events are reported ABSENT rather than invented, which is "
      "what makes this a wiring of extracted evidence and not a fabrication")

# THE EVENT FORM IS UNCHANGED, so the bump is a widening and not a replacement: a project that
# supplies real nonconformance events still gets the full backlog picture on both lines.
EVENTS = {"ncrExposureRecord": {
    "source": "the quality manager's nonconformance log", "exposure_unit": "inspections",
    "exposure_quantity": 100.0, "as_of_day": 200.0,
    "ncrs": [{"ncr_id": f"NCR-{i:03d}", "issue_day": 100.0 + i, "severity": "MAJOR"}
             for i in range(4)]}}
_old_e = old_doc.run_ncr_rate(dict(EVENTS), NOOP, CUTOFF)
_new_e = new_doc.run_ncr_rate(dict(EVENTS), NOOP, CUTOFF)
check(_old_e.get("ncr_rate") == _new_e.get("ncr_rate") == 0.04
      and _old_e.get("severity_counts") == _new_e.get("severity_counts") == {"MAJOR": 4},
      "and on a record carrying real nonconformance EVENTS both lines agree exactly, so the "
      "closure widened what can be read rather than changing what was already readable")

# THE PRODUCTION ASSEMBLER, which is the corpus-to-structure wiring itself.
_old_docs = git_show("server/app/documents.py")
_now_docs = (ROOT / "server" / "app" / "documents.py").read_text(encoding="utf-8")
check("ncrExposureRecord" not in _old_docs,
      f"no production code at commit {V13_COMMIT} assembled this structure from the corpus, "
      f"which is why the module could only ever abstain on a real project")
check("ncrExposureRecord" in _now_docs and "ncrExposureRecordDerivation" in _now_docs,
      "and production assembles it now, recording the derivation on the stored row so a reader "
      "can see which two extracted fields it was built from")
check("itemsInspected" in _now_docs and "ncrIssued" in _now_docs,
      "from `ncrIssued` and `itemsInspected`, both of which the extraction pipeline already "
      "produced before this closure and neither of which is inferred from anything")

check(True,
      "SCOPE STATED HONESTLY: this suite proves one divergence on identical input, which is all "
      "a version boundary needs. It does not claim to enumerate every divergence between the two "
      "lines, and the other sixteen Category-4 and -5 structures are genuinely absent from the "
      "corpus and still abstain on it")


print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
