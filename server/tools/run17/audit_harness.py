"""
Run 19 shared audit harness.

TEST-ONLY. Nothing under server/app imports this file and it imports nothing from server/app
except through the caller. It exists so that the nine Run-19 category suites share ONE
implementation of the two-directional proposition rule rather than nine hand-maintained copies
that could drift apart, which is exactly the failure mode the anti-fossilisation register was
created to catch.

THE TWO-DIRECTIONAL RULE (supervisory specification sections 0, 9 and 30).

Run 19 is an audit and is forbidden from remediating production. So a canonical proposition that
production fails cannot be turned green by fixing the code. Nor may a suite assert the defective
behaviour as though it were the expected answer: five suites in this programme were already
found doing exactly that, and one of them asserted the defect's own sentence verbatim.

So proposition() decides in BOTH directions:

  - a canonical proposition that FAILS and is not named in the suite's register makes the suite
    red for an unrecorded scientific defect;
  - a proposition that HOLDS while it IS named in the register also makes the suite red, because
    a later run has repaired it and the recorded disposition has gone stale.

Neither a new defect nor a repaired one can pass silently. The check that passes is "this
proposition was decided and its answer agrees with the register". The proposition's own truth
value is the finding, never the pass.
"""

from __future__ import annotations

import csv
import pathlib
import sys
import traceback


class Audit:
    """One category suite's accumulated state."""

    def __init__(self, name: str, known_defects: dict[str, str]) -> None:
        self.name = name
        #: key -> the scientific disposition recorded for the proposition that fails.
        self.known_defects = dict(known_defects)
        self.passed = 0
        self.total = 0
        self.failures: list[str] = []
        #: module_id -> the check names that exercised it, for the evidence column.
        self.coverage: dict[str, list[str]] = {}
        #: canonical propositions that did NOT hold against production.
        self.defects: list[dict] = []
        #: keys seen this run, so a register entry naming a proposition never evaluated is caught.
        self._seen: set[str] = set()

    # ------------------------------------------------------------------ recording

    def check(self, module_id: str, name: str, condition: bool, detail: str = "") -> bool:
        """A plain assertion about the test's own arithmetic, oracles, or structure."""
        self.total += 1
        self.coverage.setdefault(module_id, []).append(name)
        if condition:
            self.passed += 1
            return True
        self.failures.append(f"[{module_id}] {name}" + (f" -- {detail}" if detail else ""))
        return False

    def near(self, module_id: str, name: str, got, want, tol: float = 1e-9) -> bool:
        try:
            ok = got is not None and abs(float(got) - float(want)) <= tol
        except (TypeError, ValueError):
            ok = False
        return self.check(module_id, name, ok, f"got {got!r}, oracle {want!r}, tol {tol}")

    def proposition(self, module_id: str, key: str, name: str, holds: bool,
                    detail: str = "") -> bool:
        """
        Decide one canonical proposition against production, both directions.

        `key` is the stable register name. `holds` is whether production satisfied the
        specification's requirement. `detail` is carried into the finding, not into the pass.
        """
        self.total += 1
        self._seen.add(key)
        self.coverage.setdefault(module_id, []).append(name)
        registered = key in self.known_defects
        if not holds:
            self.defects.append({
                "module_id": module_id, "key": key, "proposition": name, "detail": detail,
                "disposition": self.known_defects.get(key, "UNRECORDED"),
            })
        if holds and registered:
            self.failures.append(
                f"[{module_id}] {name} -- this proposition NOW HOLDS but is recorded in the "
                f"Run-19 register as {self.known_defects[key]}. The finding is stale: the "
                f"disposition must be revised, not the test.")
            return False
        if not holds and not registered:
            self.failures.append(
                f"[{module_id}] {name} -- proposition FAILED and is not in the Run-19 register. "
                f"An unrecorded scientific defect. {detail}")
            return False
        self.passed += 1
        return True

    # ------------------------------------------------------------------ finishing

    def register_is_exhausted(self) -> None:
        """
        A register entry naming a proposition the suite never evaluates is dead weight that
        would quietly excuse a defect nobody is testing for any more. Catch it.
        """
        unseen = sorted(set(self.known_defects) - self._seen)
        self.check("REGISTER", "every registered defect was actually evaluated this run",
                   not unseen, f"never evaluated: {unseen}")

    def finish(self) -> int:
        """
        Print the one anchored canonical RESULT line the strict harness accepts and return the
        process exit code. The runner rejects prose summaries, a reported failed count, and a
        green line accompanied by a nonzero exit, so this prints nothing that resembles a
        result except the real one.
        """
        self.register_is_exhausted()
        if self.failures:
            print(f"\n{len(self.failures)} check(s) did not hold:")
            for f in self.failures:
                print(f"  - {f}")
        if self.defects:
            print(f"\nCanonical propositions that production did not satisfy "
                  f"({len(self.defects)}), each recorded with its Run-19 disposition:")
            for d in self.defects:
                print(f"  - [{d['module_id']}] {d['key']}: {d['disposition']}")
                print(f"      {d['proposition']}")
                if d["detail"]:
                    print(f"      {d['detail']}")
        print(f"RESULT: {self.passed}/{self.total} checks passed")
        return 0 if (self.passed == self.total and not self.failures) else 1


def guarded(audit: Audit, module_id: str, label: str):
    """
    Run a block and turn an exception into a recorded failure instead of a silent crash.

    A suite that dies mid-way prints no RESULT line and the runner already fails it, but the
    diagnosis is far better if the surviving checks still report and the crash is named against
    the module that caused it.
    """
    class _Guard:
        def __enter__(self_inner):
            return self_inner

        def __exit__(self_inner, exc_type, exc, tb):
            if exc_type is None:
                return False
            audit.check(module_id, f"{label} completed without crashing", False,
                        f"{exc_type.__name__}: {exc}\n"
                        + "".join(traceback.format_tb(tb)[-3:]))
            return True
    return _Guard()


def write_results(path: pathlib.Path, header: list[str], rows: list[dict]) -> None:
    """Write one category's result rows with the exact 29-column contract."""
    path.parent.mkdir(parents=True, exist_ok=True)
    for r in rows:
        missing = [c for c in header if c not in r]
        if missing:
            raise KeyError(f"{path.name} row {r.get('module_id')} is missing {missing}")
        extra = [c for c in r if c not in header]
        if extra:
            raise KeyError(f"{path.name} row {r.get('module_id')} has unknown columns {extra}")
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(r)


RESULT_HEADER = [
    "module_id", "module_name", "category", "basis_class", "operational_activation",
    "voting_status", "primary_method_source", "canonical_structure_required",
    "canonical_structure_present", "implementation_verified", "known_answer_pass",
    "boundary_pass", "missingness_pass", "invariant_pass", "stochastic_diagnostics_pass",
    "reproducibility_pass", "parameter_provenance_status", "calibration_status",
    "threshold_status", "empirical_validation_status", "regulatory_snapshot",
    "cat9_qualification_status", "lineage_status", "scientific_disposition",
    "production_change_made", "finding_summary", "required_next_action", "test_names",
    "evidence_paths",
]

ALLOWED_DISPOSITIONS = frozenset({
    "SCIENTIFIC_PASS", "METHOD_PASS_CALIBRATION_PENDING", "CORRECT_PROXY_ONLY",
    "CORRECT_ABSTENTION", "MISSING_CANONICAL_DATA_STRUCTURE", "PARAMETER_PROVENANCE_BLOCKED",
    "THRESHOLD_CALIBRATION_BLOCKED", "REGULATORY_VERSION_BLOCKED", "METHOD_LABEL_MISMATCH",
    "IMPLEMENTATION_DEFECT", "FUTURE_RESEARCH_ONLY", "OWNER_DECISION_REQUIRED",
})
