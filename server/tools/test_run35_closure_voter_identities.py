#!/usr/bin/env python3
"""
RUN 35 FINAL CLOSURE GUARDS. Fifteen named oracles over the two corrected voting identities, the
version boundary, the withdrawn stale labels and the preserved A1.1 finding.

RULES THIS SUITE OBEYS:
 * production is EXECUTED, never described. Every claim about a value or a band comes from
   calling the real dispatch entry and reading what came back.
 * no check asserts against a copy of the logic under test, and no check regenerates the artifact
   it is checking.
 * the label oracle's expectation comes from the REGISTRY AUTHORITY CSV. The generated client
   artifacts are compared against that authority, never against each other, so the generator
   cannot become its own oracle.
 * a crash is a FAILURE: every check is individually trapped and a raised exception is recorded
   as a failed check, with the RESULT line still printed.
"""
from __future__ import annotations

import csv
import json
import pathlib
import subprocess
import sys
from fractions import Fraction as F

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from app.simulation import registry as REG                                  # noqa: E402
from app.simulation.method_labels import TRUTHFUL_METHOD_LABELS as LABELS    # noqa: E402
from app.simulation.models import SIMULATION_VERSION                        # noqa: E402

AUDIT = ROOT / "code_audit"
V22_COMMIT = "034cf03be257f4582bc1a856262c56ea11bb4558"
NOOP = (lambda: 0.5)
CUT = "2026-06-30"
CORPUS = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
          "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
          "actualPctComplete": 40.0, "plannedPctComplete": 45.0}
BOUNDARY = {"bac": 1_000_000.0, "ev": 989_999.0, "ac": 990_000.0}

PASSED = 0
TOTAL = 0
FAILURES: list[str] = []


def check(name, fn):
    global PASSED, TOTAL
    TOTAL += 1
    try:
        ok, detail = fn()
    except Exception as exc:                                          # noqa: BLE001
        ok, detail = False, f"CRASHED (a crash is a FAILURE here): {type(exc).__name__}: {exc}"
    if ok:
        PASSED += 1
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"FAIL  {name}: {detail}")


def run(mid, si):
    return REG.run_module(mid, dict(si), NOOP, CUT)


def git_show(path, rev=V22_COMMIT):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def registry_name(mid):
    """THE AUTHORITY. The registry CSV the frontend taxonomy is generated FROM."""
    with (ROOT / "p0-baseline" / "module_renumbering_map.csv").open(
            encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["new_id"] == mid:
                return r["module_name"]
    return None


# ================================================================= the fifteen named guards
def g01_tcpi_bands_from_full_precision():
    """FAULT 1. A1.7 bands from the rounded value."""
    bad = []
    row = run("A1.7", BOUNDARY)
    if row.get("status_color") != "Amber":
        bad.append(f"boundary fixture banded {row.get('status_color')}, not Amber; the "
                   f"full-precision index {row.get('tcpi')} is above 1.00")
    if row.get("tcpi_display") == row.get("tcpi"):
        bad.append("the display value equals the canonical value here, so this fixture no "
                   "longer distinguishes the two and the guard would be vacuous")
    return not bad, "; ".join(bad[:3])


def g02_tcpi_canonical_value_not_rounded():
    """FAULT 2. The A1.7 canonical value is itself rounded before downstream use."""
    bad = []
    row = run("A1.7", CORPUS)
    ident = (CORPUS["bac"] - CORPUS["ev"]) / (CORPUS["bac"] - CORPUS["ac"])
    if row["tcpi"] != ident:
        bad.append(f"canonical tcpi {row['tcpi']!r} is not the identity {ident!r}")
    if F(str(row["tcpi"])).denominator == 1000 or len(str(row["tcpi"]).split(".")[-1]) <= 3:
        bad.append(f"canonical tcpi {row['tcpi']!r} looks rounded to three decimals")
    return not bad, "; ".join(bad[:3])


def g03_display_value_is_not_the_vote_input():
    """FAULT 3. The A1.7 display value is used as vote input."""
    bad = []
    row = run("A1.7", BOUNDARY)
    disp = row.get("tcpi_display")
    canon = row.get("tcpi")
    band_from_disp = ("Green" if disp <= 1.00 else "Amber" if disp <= 1.10 else "Red")
    band_from_canon = ("Green" if canon <= 1.00 else "Amber" if canon <= 1.10 else "Red")
    if band_from_disp == band_from_canon:
        bad.append("this fixture does not separate the two bands, so the guard is vacuous")
    if row["status_color"] != band_from_canon:
        bad.append(f"the emitted band {row['status_color']} follows the DISPLAY value, not the "
                   f"canonical one ({band_from_canon} expected)")
    return not bad, "; ".join(bad[:3])


def g04_boundary_population_bands_correctly():
    """FAULT 4. The A1.7 boundary fixture receives the wrong band."""
    pre = json.loads((AUDIT / "run35_voter_prechange_measurement.json").read_text())
    fixtures = pre["A1.7_band_boundary_fixtures"]["fixtures"]
    bad = []
    if not fixtures:
        return False, "the pre-change measurement recorded no boundary fixture to re-check"
    for f in fixtures:
        row = run("A1.7", f["inputs"])
        if row.get("status_color") != f["band_from_full_precision"]:
            bad.append(f"{f['inputs']} -> {row.get('status_color')}, expected "
                       f"{f['band_from_full_precision']}")
        if row.get("status_color") == f["band_production_assigned"]:
            bad.append(f"{f['inputs']} still assigns the v22 band "
                       f"{f['band_production_assigned']}")
    return not bad, f"{len(fixtures)} fixtures re-checked; " + "; ".join(bad[:3])


def g05_vac_canonical_value_not_rounded():
    """FAULT 5. The canonical VAC is rounded before downstream use."""
    bad = []
    row = run("A1.8", CORPUS)
    ident = CORPUS["bac"] - CORPUS["bac"] / CORPUS["cpi"]
    if row["vac"] != ident:
        bad.append(f"canonical vac {row['vac']!r} is not the identity {ident!r}")
    if float(row["vac"]).is_integer():
        bad.append(f"canonical vac {row['vac']!r} is a whole number where the identity is not")
    return not bad, "; ".join(bad[:3])


def g06_vac_display_does_not_replace_the_analytical_value():
    """FAULT 6. The A1.8 display value replaces the analytical VAC."""
    bad = []
    row = run("A1.8", CORPUS)
    if "vac_display" not in row:
        bad.append("no separate presentation field is emitted")
    elif row["vac"] == row["vac_display"]:
        bad.append("the analytical and presentation values are the same object on an input "
                   "where they must differ")
    if row.get("vac_pct") == row.get("vac_pct_display"):
        bad.append("the percentage carries no separate presentation value here either")
    return not bad, "; ".join(bad[:3])


def g07_vac_identity_holds():
    """FAULT 7. The canonical VAC identity is perturbed."""
    bad = []
    for bac, cpi in ((1_000_000.0, 0.909), (1_000.0, 0.96), (500_000.0, 1.25),
                     (250_000.0, 1.0), (750_000.0, 0.8)):
        row = run("A1.8", {"bac": bac, "cpi": cpi})
        if row.get("insufficient_data"):
            bad.append(f"bac={bac} cpi={cpi} abstained unexpectedly")
            continue
        ident = bac - bac / cpi
        if row["vac"] != ident:
            bad.append(f"bac={bac} cpi={cpi}: {row['vac']!r} != {ident!r}")
        if row["vac_pct"] != (ident / bac) * 100:
            bad.append(f"bac={bac} cpi={cpi}: percentage is not VAC/BAC")
    return not bad, "; ".join(bad[:3])


def g08_voting_is_exactly_two():
    """FAULT 8. A third voting module is introduced."""
    bad = []
    if set(REG.CORE_VOTING_MODULES) != {"A1.7", "A1.8"}:
        bad.append(f"the voting set is {sorted(REG.CORE_VOTING_MODULES)}")
    if len(REG.CORE_VOTING_MODULES) != 2:
        bad.append(f"voting count is {len(REG.CORE_VOTING_MODULES)}")
    return not bad, "; ".join(bad[:3])


def g09_cost_recovery_reads_analytical_results():
    """
    FAULT 9. Cost Recovery Status consumes a formatted string instead of the analytical result.

    Executed through `compute`, the real fusion path. The proof is behavioural: the boundary
    fixture's DISPLAYED number is "1" while its analytical index is above 1.00, so a fusion that
    read the formatted string could not arrive at the band the analytical value implies.
    """
    from app.simulation import compute as C
    import inspect
    bad = []
    src = inspect.getsource(C)
    if "evidence_metric" in src.split("CORE_VOTING_MODULES")[-1][:1500] and \
            "status_color" not in src.split("CORE_VOTING_MODULES")[-1][:400]:
        bad.append("the voting path reads evidence_metric near its voting selection")
    row = run("A1.7", BOUNDARY)
    if "status_color" not in row:
        bad.append("A1.7 emits no analytical status for fusion to read")
    if row["status_color"] != "Amber":
        bad.append(f"the analytical status reaching fusion is {row['status_color']}, which is "
                   f"the band the FORMATTED value implies, not the analytical one")
    if row["evidence_metric"].split(",")[0] != "TCPI: 1":
        bad.append("this fixture no longer has a display string that disagrees with the "
                   "analytical band, so the guard is vacuous")
    return not bad, "; ".join(bad[:3])


def g10_v22_predecessor_not_rewritten():
    """FAULT 10. The v22 predecessor is rewritten to the corrected behaviour."""
    bad = []
    models = git_show("server/app/simulation/models.py")
    evm = git_show("server/app/simulation/models_evm.py")
    if 'SIMULATION_VERSION = "sim-2026.08-v22"' not in models:
        bad.append("the pinned predecessor object no longer stamps itself v22")
    if "_round3(remaining_work / remaining_budget)" not in evm:
        bad.append("the pinned predecessor object no longer carries the defective A1.7 line, so "
                   "the failing predecessor has been regenerated")
    if "tcpi_display" in evm:
        bad.append("the pinned predecessor object carries the corrected presentation field")
    if SIMULATION_VERSION == "sim-2026.08-v22":
        bad.append("the working tree still stamps v22, so no successor was appended")
    return not bad, "; ".join(bad[:3])


def g11_execution_proof_divergences_are_real():
    """FAULT 11. The v22->v23 execution proof claims divergence where the outputs are equal."""
    bad = []
    with (AUDIT / "run35_v22_v23_voter_execution_proof.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) < 5:
        bad.append(f"the proof carries {len(rows)} rows")
    div = [r for r in rows if r["divergence"] == "YES"]
    non = [r for r in rows if r["divergence"] == "NO"]
    for r in div:
        if r["v22_behaviour"] == r["v23_behaviour"]:
            bad.append(f"{r['module']}/{r['input'][:30]} claims divergence with identical "
                       f"behaviour on both lines")
    for r in non:
        if r["v22_behaviour"] != r["v23_behaviour"]:
            bad.append(f"{r['module']}/{r['input'][:30]} claims non-divergence with different "
                       f"behaviour on both lines")
    if len(div) < 3:
        bad.append(f"only {len(div)} divergences are recorded; the closure requires three")
    if not non:
        bad.append("no genuine non-divergence is recorded")
    return not bad, "; ".join(bad[:3])


def _label_withdrawn(mid, dead_phrase):
    bad = []
    if LABELS.get(mid) is not None:
        bad.append(f"{mid} carries a truthful-method label again: "
                   f"{LABELS[mid].truthful!r}")
    for p in sorted((ROOT / "server" / "app").rglob("*.py")):
        if "__pycache__" in str(p):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if dead_phrase in text and "RUN 35 FINAL CLOSURE" not in text:
            bad.append(f"the withdrawn proxy sentence survives in {p.relative_to(ROOT)}")
    return bad


def g12_b1_2_label_stays_withdrawn():
    """FAULT 12. The B1.2 stale proxy label is restored."""
    bad = _label_withdrawn("B1.2", "Fixed-weight signal band tally")
    return not bad, "; ".join(bad[:3])


def g13_b4_4_label_stays_withdrawn():
    """FAULT 13. The B4.4 stale proxy label is restored."""
    bad = _label_withdrawn("B4.4", "Earned value completion forecast range")
    return not bad, "; ".join(bad[:3])


def g14_label_expectation_comes_from_the_registry_authority():
    """
    FAULT 14. The label guard compares two generated client artifacts rather than authority.

    THE EXPECTATION IS THE REGISTRY CSV, and each generated client artifact is compared against
    IT, never against the other. A guard that compared categories.js with taxonomy.js would stay
    green while both drifted together away from the authority; this one cannot.
    """
    bad = []
    for mid in ("B1.2", "B4.4"):
        authority = registry_name(mid)
        if not authority:
            bad.append(f"{mid} has no name in the registry authority")
            continue
        for art in ("assets/js/categories.js", "assets/js/taxonomy.js"):
            text = (ROOT / art).read_text(encoding="utf-8", errors="ignore")
            line = [ln for ln in text.splitlines() if f"module_id: '{mid}'" in ln]
            if not line:
                bad.append(f"{mid} is absent from {art}")
                continue
            if f"name: '{authority}'" not in line[0]:
                bad.append(f"{art} presents {mid} under a name the registry authority does not "
                           f"carry (authority says {authority!r})")
        # and with the label withdrawn, the presented method name IS the authority's name
        if LABELS.get(mid) is not None and LABELS[mid].truthful != authority:
            bad.append(f"{mid} presents a truthful-method label that is not the canonical name")
    with (AUDIT / "run35_stale_method_label_reconciliation.csv").open(encoding="utf-8") as fh:
        rec = list(csv.DictReader(fh))
    if len(rec) != 2:
        bad.append(f"the reconciliation artifact carries {len(rec)} rows, not exactly two")
    for r in rec:
        if r["canonical_method"] != registry_name(r["module_id"]):
            bad.append(f"{r['module_id']} reconciliation names a method the registry does not")
        if r["implementation_changed"] != "NO":
            bad.append(f"{r['module_id']} reports an implementation change")
    return not bad, "; ".join(bad[:4])


def g15_a1_1_finding_carried_forward():
    """FAULT 15. The A1.1 Run-36 finding disappears from the handoff."""
    bad = []
    rec_path = AUDIT / "run35_a1_1_run36_handoff.json"
    if not rec_path.is_file():
        return False, "the A1.1 Run-36 handoff record is missing"
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    if rec.get("finding_id") != "DECLARED_STRUCTURE_UNCONSUMED_AND_REACHABLE_PARAMETER_UNRESOLVED":
        bad.append(f"the finding id is {rec.get('finding_id')!r}")
    if rec.get("declared_structure") != "costDriverDistributions":
        bad.append("the declared structure is not recorded")
    if rec.get("intake_accepts_it") is not True:
        bad.append("the record no longer states that the intake accepts the key")
    if rec.get("consumers_found") != 0:
        bad.append(f"consumers_found is {rec.get('consumers_found')}; if a consumer now exists "
                   f"the finding must be restated, not silently dropped")
    if rec.get("remediation_attempted_in_this_closure") != "NONE":
        bad.append("the record claims a remediation this closure did not perform")
    # RUN 59, PHASE B. RETIRED, NOT DELETED. Owner's ruling, 2026-08-25: no markdown document
    # carries authority. These two conditions asserted that T6_HANDOFF.md -- history, which
    # governs nothing -- contains two particular strings. Nothing about production depended on
    # them. The finding itself is still asserted, above, against the recorded structure. The body
    # is kept and runs again if the flag is cleared.
    if not RETIRED_RUN59_HANDOFF_STRINGS:
        hand = (ROOT / "T6_HANDOFF.md").read_text(encoding="utf-8")
        if "DECLARED_STRUCTURE_UNCONSUMED_AND_REACHABLE_PARAMETER_UNRESOLVED" not in hand:
            bad.append("the Run-36 handoff does not carry the finding")
        if "costDriverDistributions" not in hand:
            bad.append("the Run-36 handoff does not name the declared structure")
    return not bad, "; ".join(bad[:4])


#: RUN 59, PHASE B. Retired, not deleted: the two T6_HANDOFF.md string conditions inside
#: the guard above stop running, their body is kept, and the reason is recorded there.
#: Owner's ruling, 2026-08-25: no markdown document in this repository carries authority.
RETIRED_RUN59_HANDOFF_STRINGS = True

GUARDS = [
    ("run35c.fault01.tcpi_bands_from_full_precision", g01_tcpi_bands_from_full_precision),
    ("run35c.fault02.tcpi_canonical_not_rounded", g02_tcpi_canonical_value_not_rounded),
    ("run35c.fault03.display_is_not_the_vote_input", g03_display_value_is_not_the_vote_input),
    ("run35c.fault04.boundary_population_bands_correctly", g04_boundary_population_bands_correctly),
    ("run35c.fault05.vac_canonical_not_rounded", g05_vac_canonical_value_not_rounded),
    ("run35c.fault06.vac_display_separate", g06_vac_display_does_not_replace_the_analytical_value),
    ("run35c.fault07.vac_identity_holds", g07_vac_identity_holds),
    ("run35c.fault08.voting_is_exactly_two", g08_voting_is_exactly_two),
    ("run35c.fault09.cost_recovery_reads_analytical", g09_cost_recovery_reads_analytical_results),
    ("run35c.fault10.v22_predecessor_not_rewritten", g10_v22_predecessor_not_rewritten),
    ("run35c.fault11.execution_proof_divergences_real", g11_execution_proof_divergences_are_real),
    ("run35c.fault12.b1_2_label_withdrawn", g12_b1_2_label_stays_withdrawn),
    ("run35c.fault13.b4_4_label_withdrawn", g13_b4_4_label_stays_withdrawn),
    ("run35c.fault14.label_expectation_from_authority",
     g14_label_expectation_comes_from_the_registry_authority),
    ("run35c.fault15.a1_1_finding_carried_forward", g15_a1_1_finding_carried_forward),
]


def main():
    for name, fn in GUARDS:
        check(name, fn)
    print(f"RESULT: {PASSED}/{TOTAL} checks passed")
    return 0 if PASSED == TOTAL else 1


if __name__ == "__main__":
    sys.exit(main())
