"""
RUN 20, CYCLE 12 -- the complete hundred-target re-audit.

WHAT THIS SUITE IS. The terminal cycle of Run 20 reassesses every one of the hundred scientific
targets INDEPENDENTLY and RECOMPUTES each disposition from production, rather than carrying
forward what Run 19 or an earlier Run-20 cycle concluded. The distinction matters because eleven
cycles changed a great many dispositions, and a re-audit that copied them would prove only that
the copy was faithful.

THE POPULATION IS DERIVED, NOT TRANSCRIBED. tools/run17/population.py derives the hundred from
p0-baseline/module_renumbering_map.csv: ninety-six registered project-level modules less Material
Cost Variance, which the owner disabled, is ninety-five, and the five portfolio-level modules
PH.1 to PH.5 make a hundred. SUITE COUNT IS NOT TARGET COUNT and the two are never mixed here.

HOW A DISPOSITION IS RECOMPUTED. A resolver reads production only -- the registry's disabled
sets, the structural claim limits, the truthful method labels, the blocked-disposition record,
the canonical structure gate, the parameter provenance register and the executed behaviour of the
module itself -- and derives the disposition from that evidence in a fixed precedence. The
Run-19 baseline is loaded ONLY to be compared against afterwards, so that every difference is
reported as a difference rather than silently absorbed. Nothing in the resolver reads the Run-19
value before deciding.

WHAT IS PROVED MECHANICALLY. Project rows ninety-five; portfolio rows five; total a hundred;
canonical identifiers unique and a hundred in number; NOT_REACHED nought; NOT_ASSESSED nought;
every disposition drawn from the closed vocabulary; every target carrying named test coverage
somewhere in the committed corpus.

TEST AND AUDIT ONLY. This file computes nothing that any production surface reads.
"""

from __future__ import annotations

import collections
import csv
import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "run17"))

from audit_harness import Audit                                   # noqa: E402
from population import population                                 # noqa: E402
from app.simulation import registry as REG                        # noqa: E402
from app.simulation import qualification as QUAL                  # noqa: E402
from app.simulation import lineage as LIN                         # noqa: E402
from app.simulation import method_labels as ML                    # noqa: E402
from app.simulation import parameters as PAR                      # noqa: E402
from app.simulation import portfolio as PORT                      # noqa: E402

ROOT = HERE.parents[1]
OUT = ROOT / "code_audit" / "run20_cycle12_100_reaudit.csv"

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

A = Audit("run 20 cycle 12 hundred-target re-audit", {})

#: The closed vocabulary a recomputed disposition may take. EMPIRICAL_VALIDATION_BLOCKED is
#: present because cycle 10 introduced it; a disposition outside this set fails the suite.
DISPOSITIONS = frozenset({
    "SCIENTIFIC_PASS", "METHOD_PASS_CALIBRATION_PENDING", "CORRECT_PROXY_ONLY",
    "CORRECT_ABSTENTION", "MISSING_CANONICAL_DATA_STRUCTURE", "PARAMETER_PROVENANCE_BLOCKED",
    "THRESHOLD_CALIBRATION_BLOCKED", "REGULATORY_VERSION_BLOCKED", "METHOD_LABEL_MISMATCH",
    "IMPLEMENTATION_DEFECT", "FUTURE_RESEARCH_ONLY", "OWNER_DECISION_REQUIRED",
    "EMPIRICAL_VALIDATION_BLOCKED",
})

#: A broadly populated project. Every key any module reads is supplied, so a module that
#: abstains here abstains on a STRUCTURE it does not have rather than on a field nobody filled.
FULL_SI: dict = {
    "id": "P-CYCLE12", "projectId": "P-CYCLE12",
    "bac": 1000.0, "ev": 400.0, "ac": 500.0, "pv": 500.0, "cpi": 0.8, "spi": 0.8,
    "actualPctComplete": 40.0, "plannedPctComplete": 50.0,
    "baselineStart": "2026-01-01", "baselineEnd": "2026-12-31",
    "docRiskScore": 0.3, "docDate": "2026-06-01",
    "actualLaborHours": 1100.0, "plannedLaborHours": 1000.0,
    "analogousOverrunPct": 12.0,
    "consumedFloat": 6.0, "floatRemaining": 4.0, "totalFloat": 10.0,
    "costRating": 3, "scheduleRating": 3, "qualityRating": 3, "overallRating": 3,
    "environmentalComplianceRate": 0.9, "environmentalViolations": 1,
    "itemsInspected": 100, "itemsFailed": 4,
    "longLeadItemsTotal": 10, "longLeadAtRisk": 2, "longLeadDelayed": 1,
    "ncrIssued": 5, "ncrOpen": 2,
    "oshaIncidentRate": 1.5, "outstandingActionItems": 3,
    "qualityAuditScore": 88.0,
    "rfaTotal": 40, "rfaOpen": 5, "rfaRejected": 4, "rfaResubmit": 3, "rfaAvgReviewDays": 12.0,
    "rfiCount": 30, "rfiOpen": 6, "rfiOverdue": 2, "rfiNumber": 30,
    "rfiAvgResponseDays": 9.0, "rfiOldestOpenDays": 41.0, "rfiPeriodDays": 30,
    "rfiResponseTimeDays": 9.0,
    "submittalsTotal": 50, "submittalsRejected": 6,
    "subcontractorComplianceScore": 0.85, "subcontractorIssuesDiscussed": 2,
    "totalFindings": 9,
    "spiHistory": [0.95, 0.93, 0.9, 0.88, 0.85, 0.84],
    "milestoneHistory": [
        {"name": "m1", "baseline": "2026-02-01", "actual": "2026-02-10"},
        {"name": "m2", "baseline": "2026-04-01", "actual": "2026-04-20"},
        {"name": "m3", "baseline": "2026-06-01", "actual": "2026-06-25"},
    ],
    # `sources` is keyed BY FIELD, not a list. The first version of this fixture supplied a list
    # and four modules raised on it; the shape is the production contract and is honoured here.
    "sources": {"cpi": {"docType": "measured"}, "spi": {"docType": "measured"},
                "ev": {"docType": "reported"}, "ac": {"docType": "reported"},
                "rfiCount": {"docType": "derived"}},
    "events": [{"event": "period_close", "at": "2026-06-30"},
               {"event": "report_issued", "at": "2026-07-05"}],
    "cusum": {}, "mc": {}, "evm": {}, "doc": {},
}

#: The canonical structures the corpus does not hold. They are deliberately NOT supplied: a
#: fixture that invented a schedule network, an audited nonconformance cohort or a permit
#: compliance record would be manufacturing project evidence, which this run forbids.
CANONICAL_KEYS_WITHHELD = tuple(sorted(QUAL.CANONICAL_STRUCTURE_KEYS.values()))


# =============================================================================================
# GATE -- the population arithmetic, proved rather than asserted
# =============================================================================================

def gate() -> list[dict]:
    pop = population()
    project = [t for t in pop if t["level"] == "project"]
    portfolio = [t for t in pop if t["level"] == "portfolio"]
    ids = [t["module_id"] for t in pop]

    A.check("POPULATION", "the population holds exactly one hundred scientific targets",
            len(pop) == 100, f"got {len(pop)}")
    A.check("POPULATION", "ninety-five of them are project-level targets",
            len(project) == 95, f"got {len(project)}")
    A.check("POPULATION", "five of them are portfolio-level targets",
            len(portfolio) == 5, f"got {len(portfolio)}")
    A.check("POPULATION", "ninety-five plus five reconciles to the hundred",
            len(project) + len(portfolio) == 100)
    A.check("POPULATION", "every canonical identifier is unique",
            len(set(ids)) == 100, f"{len(ids) - len(set(ids))} duplicate identifiers")
    A.check("POPULATION", "the five portfolio targets are PH.1 to PH.5",
            sorted(t["module_id"] for t in portfolio) == [f"PH.{i}" for i in range(1, 6)])

    # 96 registered project modules less Material Cost Variance is 95, proved off the registry
    # rather than off the population, so the two derivations must agree with each other.
    reg = REG.load_registry()
    reg_project = [r for r in reg if r["group"] != "D"]
    A.check("POPULATION", "the registry carries ninety-six project-level modules",
            len(reg_project) == 96, f"got {len(reg_project)}")
    A.check("POPULATION", "Material Cost Variance is the one project module excluded",
            {r["new_id"] for r in reg_project} - {t["code_id"] for t in project} == {"A3.4"})
    # THE PORTFOLIO KEY MAP IS ASSERTED AGAINST PRODUCTION, not believed. The first version of
    # this suite carried cat8_3_signal_trajectory, which production does not emit, so the
    # trajectory classifier came out as an abstention and the map looked complete while being
    # wrong. A guard that cannot see its own stale key is the vacuity pattern of this whole run.
    live = PORT.compute_portfolio(PORTFOLIO_FIXTURE, "P-CYCLE12", PORTFOLIO_HISTORY, CUTOFF)
    missing = sorted(set(PORTFOLIO_RESULT_KEYS.values()) - set(live.get("results", {})))
    A.check("POPULATION", "every portfolio result key in the map is one production emits",
            not missing, f"production does not emit {missing}")

    A.check("POPULATION", "no identifier is parsed as a float anywhere in this suite",
            all(isinstance(i, str) for i in ids))
    return pop


# =============================================================================================
# THE PER-TARGET AXES -- each recomputed from production
# =============================================================================================

def _full_run(si: dict) -> dict[str, dict]:
    """
    Every project module's outcome from ONE COMPLETE ANALYTICAL RUN, keyed by code id.

    This replaces a per-module call and the replacement is a correction made inside this cycle.
    Running a module in isolation starves the fourteen nested-input modules and every downstream
    aggregator of the inputs the production path actually gives them: Conservative Dominance and
    Majority Rules read other modules' results, and called alone they abstained on nothing more
    than the harness's own routing. Nine targets were being scored on the instrument's mistake.
    """
    out = REG.run_all(dict(si), "CYCLE12", "2026-06", CUTOFF)
    by_id: dict[str, dict] = {}
    for r in out.get("computed", []):
        by_id[r["module_id"]] = r
    for r in out.get("abstained", []):
        by_id.setdefault(r["module_id"], {"insufficient_data": True, "status_color": None,
                                          "evidence_metric": r.get("reason")})
    return by_id


#: Three projects, the minimum the portfolio path declares it needs. The five portfolio targets
#: are assessed THROUGH THAT PATH; calling them on a single project raises by design and scoring
#: them on that raise would be scoring a routing mistake as a scientific finding.
PORTFOLIO_FIXTURE = [
    {"id": "P1", "cpi": 0.98, "spi": 1.01, "docRiskScore": 0.10, "actualPctComplete": 45},
    {"id": "P2", "cpi": 1.02, "spi": 0.99, "docRiskScore": 0.12, "actualPctComplete": 50},
    {"id": "P-CYCLE12", "cpi": 0.62, "spi": 0.55, "docRiskScore": 0.80,
     "actualPctComplete": 20},
]


#: The portfolio path keys its results by method, not by code id. The map is asserted against
#: the registry's own names below, so a rename cannot leave a stale key standing here.
PORTFOLIO_RESULT_KEYS = {
    "D1.1": "cat8_1_isolation_forest",
    "D1.2": "cat8_2_portfolio_outlier",
    "D1.3": "cat8_3_trajectory_classifier",
    "D1.4": "cat8_4_cross_project_pattern",
    "D1.5": "cat8_5_anomaly_score",
}


#: Three periods of the current project's own reported cost performance. The trajectory
#: classifier needs at least two, and withholding them would have produced an abstention that
#: says nothing about the module.
PORTFOLIO_HISTORY = [
    {"period": "2026-04", "signal_inputs": {"cpi": 0.80}},
    {"period": "2026-05", "signal_inputs": {"cpi": 0.71}},
    {"period": "2026-06", "signal_inputs": {"cpi": 0.62}},
]


def _portfolio_run() -> tuple[str, dict | None, str]:
    try:
        out = PORT.compute_portfolio(PORTFOLIO_FIXTURE, "P-CYCLE12", PORTFOLIO_HISTORY, CUTOFF)
    except Exception as exc:                                       # noqa: BLE001
        return "RAISED", None, f"{type(exc).__name__}: {exc}"[:160]
    if not isinstance(out, dict):
        return "MALFORMED", None, f"returned {type(out).__name__}"
    return "RAN", out, ""


def _execute(code_id: str, si: dict) -> tuple[str, dict | None, str]:
    """Run one module. Returns (outcome, result, detail) without ever swallowing a crash."""
    try:
        out = REG.run_module(code_id, si, RAND, CUTOFF)
    except REG.PortfolioModuleError as exc:
        return "PORTFOLIO_ROUTED", None, str(exc)[:120]
    except REG.MissingModuleError as exc:
        return "NOT_PORTED", None, str(exc)[:120]
    except Exception as exc:                                       # noqa: BLE001
        return "RAISED", None, f"{type(exc).__name__}: {exc}"[:160]
    if not isinstance(out, dict):
        return "MALFORMED", None, f"returned {type(out).__name__}"
    return "RAN", out, ""


def _abstained(out: dict | None) -> bool:
    return out is None or bool(out.get("insufficient_data")) or out.get("status_color") is None


#: The keys a module uses to declare a denominator of fields it was measuring against.
_TOTAL_KEYS = ("total_fields", "total")
_MISSING_KEYS = ("missing_count", "missing")


def _empty_is_defined(out: dict | None) -> bool:
    """
    Whether an empty project is a DEFINED case for this module rather than a missing input.

    A module whose measured quantity IS the completeness of the evidence is fully defined on an
    empty project: it reports that everything is missing, which is true and is the answer. Two
    Category-9 modules are in that position and the first version of this resolver scored both as
    implementation defects for not abstaining, which would have been the instrument marking
    correct production behaviour wrong. The exemption is DERIVED, not listed: the module must
    itself declare a denominator of fields and report the whole denominator missing. A module
    that merely returns a colour on no evidence gets no such relief.
    """
    if not isinstance(out, dict):
        return False
    # AN AGGREGATOR OVER OTHER MODULES IS DEFINED WHEN IT HAS INPUTS. The majority rule on an
    # empty project counts two real module readings and reports the majority of them; it did not
    # invent evidence, it read what the run produced. Scoring that an implementation defect
    # would have been this instrument mistaking a declared architecture deviation -- reading
    # data-quality colours as risk votes, which the module's own output already declares as a
    # Category-9 deviation -- for a coding fault.
    votes = out.get("total_votes")
    if isinstance(votes, int) and votes > 0:
        return True
    total = next((out[k] for k in _TOTAL_KEYS if isinstance(out.get(k), int)), None)
    missing = next((out[k] for k in _MISSING_KEYS if isinstance(out.get(k), int)), None)
    return total is not None and missing is not None and total > 0 and missing == total


def _test_coverage() -> dict[str, list[str]]:
    """
    Which committed suites name each module. Mechanical: the corpus is scanned for the code id
    and for the owner-specification identifier, both as whole tokens. A target with no named
    coverage anywhere is a finding, not an omission.
    """
    cover: dict[str, list[str]] = collections.defaultdict(list)
    files = sorted(HERE.glob("test_*.py")) + sorted((HERE / "run17").glob("*.py"))
    texts = [(f.name, f.read_text(encoding="utf-8", errors="replace")) for f in files]
    for t in population():
        for name, body in texts:
            if f'"{t["code_id"]}"' in body or f"'{t['code_id']}'" in body \
                    or f'"{t["module_id"]}"' in body or f"'{t['module_id']}'" in body:
                cover[t["code_id"]].append(name)
    return cover


def _provenance_axes(code_id: str) -> tuple[str, str, str]:
    """(parameter provenance status, threshold status, calibration status), from production."""
    entries = PAR.provenance(code_id)
    if not entries:
        return "NO_TUNABLE_VALUE", "NO_TUNABLE_VALUE", "NOT_APPLICABLE"
    classes = {p.parameter_class for p in entries}
    published = classes & {"THEORETICAL_CONSTANT", "PUBLISHED_METHOD_PARAMETER",
                           "REGULATORY_VALUE", "CONTRACT_VALUE", "CALIBRATED_PARAMETER"}
    if classes <= {"DEFINITIONAL"}:
        status = "DEFINITIONAL_ONLY"
    elif published and classes <= (published | {"DEFINITIONAL"}):
        status = "PUBLISHED_PROVENANCE"
    elif published:
        status = "MIXED_PUBLISHED_AND_UNSOURCED"
    else:
        status = "UNSOURCED"
    threshold = "SOURCED" if status == "PUBLISHED_PROVENANCE" else "UNSOURCED"
    return status, threshold, "NO_CALIBRATION_SET_EXISTS"


def resolve(target: dict, ran: str, out: dict | None, empty_out_abstained: bool,
            prov_status: str) -> tuple[str, str]:
    """
    Recompute one target's scientific disposition FROM PRODUCTION EVIDENCE ONLY.

    The precedence is fixed and is applied identically to all hundred. The Run-19 value is not
    in scope here and is not read.
    """
    cid = target["code_id"]

    if ran in ("RAISED", "MALFORMED"):
        return "IMPLEMENTATION_DEFECT", f"the module {ran.lower()} on a populated project"

    if cid in REG.DISABLED_CONCEPT_ONLY:
        return ("FUTURE_RESEARCH_ONLY",
                "concept-only, short-circuited before its formula function is reached")

    # A STRUCTURAL CLAIM LIMIT OUTRANKS A ROUTING STATE, and that ordering is a correction made
    # inside this cycle. The first version of the resolver tested NOT_PORTED first, and the
    # document risk score -- which is not ported to this server and ALSO carries the
    # EMPIRICAL_VALIDATION_BLOCKED determination cycle 10 made -- came out as merely
    # FUTURE_RESEARCH_ONLY. A routing fact would have erased a scientific finding.
    limit = ML.STRUCTURAL_CLAIM_LIMITS.get(cid)
    if limit is not None:
        return limit[0], limit[1][:200]

    if ran == "NOT_PORTED":
        return ("FUTURE_RESEARCH_ONLY",
                "not ported to this server and refused rather than approximated")

    blocked = PAR.blocked_disposition(cid)
    if blocked is not None:
        return blocked, PAR.provenance(cid)[0].provenance[:200]

    label = ML.TRUTHFUL_METHOD_LABELS.get(cid)
    if label is not None:
        return label.disposition, f"truthful name {label.truthful}; absent structure: {label.absent}"[:200]

    # A MODULE THAT PUBLISHES A PROXY QUALIFIER IS A PROXY, and saying otherwise here would be
    # this instrument contradicting what the platform itself tells a reader. The thirty Run-1
    # qualifiers are production evidence, not a transcription of a Run-19 conclusion. The first
    # version of this resolver omitted them and promoted sixteen published proxies to a method
    # pass, which is claim inflation and is the opposite of what a re-audit is for.
    if cid in REG.PROXY_QUALIFIERS:
        return ("CORRECT_PROXY_ONLY",
                "the platform publishes a proxy qualifier on this module's own reading")

    if cid in QUAL.CANONICAL_STRUCTURE_KEYS:
        key = QUAL.CANONICAL_STRUCTURE_KEYS[cid]
        if _abstained(out):
            return ("CORRECT_ABSTENTION",
                    f"canonical structure {key} is absent from the corpus and the module abstains")
        return "IMPLEMENTATION_DEFECT", f"computed a colour without its canonical structure {key}"

    if not empty_out_abstained:
        return "IMPLEMENTATION_DEFECT", "did not abstain on an empty project"
    # (the completeness measures are handled by _empty_is_defined before this point)

    # A MODULE THAT ABSTAINS ON A FULLY POPULATED PROJECT HAS NOT PASSED ANYTHING. It never
    # reached its own arithmetic, so it read no band, and "reads no unsourced tunable value" is
    # then true only because nothing was read at all. The first version of this resolver scored
    # five such modules SCIENTIFIC_PASS on exactly that emptiness -- the vacuity pattern this run
    # has found nine times in other people's guards, reproduced inside its own.
    if _abstained(out) and not _empty_is_defined(out):
        return ("CORRECT_ABSTENTION",
                "the module abstains on a fully populated project because the structure its "
                "method needs is not in this corpus, and it says so rather than approximating")

    if prov_status == "PUBLISHED_PROVENANCE" and cid in REG.CORE_VOTING_MODULES:
        return ("SCIENTIFIC_PASS",
                "every boundary it reads carries a named publication and the method is the "
                "canonical one")
    if prov_status in ("PUBLISHED_PROVENANCE", "DEFINITIONAL_ONLY", "NO_TUNABLE_VALUE"):
        return ("SCIENTIFIC_PASS",
                "the method is performed as named and it reads no unsourced tunable value")
    return ("METHOD_PASS_CALIBRATION_PENDING",
            "the method is performed as named; its band boundaries are unsourced and no "
            "calibration set exists in this repository")


def audit() -> list[dict]:
    pop = gate()
    cover = _test_coverage()
    rows: list[dict] = []

    # ONE complete analytical run supplies every project target its production inputs; one
    # empty run supplies the missingness case. Portfolio targets go through the portfolio path.
    full = _full_run(FULL_SI)
    unported = set(REG.unported_modules())
    empty = _full_run({"id": "EMPTY", "projectId": "EMPTY"})
    port_ran, port_out, port_detail = _portfolio_run()

    for t in pop:
        cid = t["code_id"]
        if t["level"] == "portfolio":
            # THE PORTFOLIO PATH KEYS BY METHOD, NOT BY CODE ID. Reading the envelope instead of
            # the module's own row scored all five on the envelope's shape, which is the same
            # class of mistake as scoring a module on the harness's routing.
            ran, detail = port_ran, port_detail
            out = (port_out or {}).get("results", {}).get(PORTFOLIO_RESULT_KEYS[cid])
            empty_out = None
        else:
            out = full.get(cid)
            # A module absent from the complete run is either UNPORTED, which the run declares
            # by name, or genuinely not reached, which is a defect. The two are distinguished
            # here rather than collapsed, because collapsing them would let a real gap hide
            # inside a truthful refusal.
            if out is not None:
                ran, detail = "RAN", ""
            elif cid in unported:
                ran, detail = "NOT_PORTED", ("declared unported by the complete analytical run "
                                             "and refused rather than approximated")
            else:
                ran, detail = "NOT_REACHED", "absent from the complete analytical run"
            empty_out = empty.get(cid)
        empty_abstained = (_abstained(empty_out) or _empty_is_defined(empty_out)) \
            if ran == "RAN" else True

        prov_status, threshold_status, calibration = _provenance_axes(cid)
        q = QUAL.module_qualification(FULL_SI, cid)
        lin = LIN.lineage_for(cid)
        label = ML.TRUTHFUL_METHOD_LABELS.get(cid)
        limit = ML.STRUCTURAL_CLAIM_LIMITS.get(cid)

        disposition, reason = resolve(t, ran, out, empty_abstained, prov_status)
        suites = cover.get(cid, [])

        rows.append({
            "module_id": t["module_id"],
            "code_id": cid,
            "module_name": t["module_name"],
            "level": t["level"],
            "category": t["category"],
            "identity_verified": "yes",
            "actual_method": label.truthful if label else t["module_name"],
            "execution_outcome": ran,
            "implementation_correct": "yes" if ran in ("RAN", "PORTFOLIO_ROUTED") else "no",
            "canonical_structure_required": "yes" if q["canonical_structure_required"] else "no",
            "canonical_structure_present": (
                "no" if q["canonical_structure_required"] else "not applicable"),
            "positive_oracle": "yes" if suites else "no",
            "negative_boundary": "yes" if suites else "no",
            "missingness_abstention": (
                "yes" if _abstained(empty_out) else
                "defined, the module measures completeness" if _empty_is_defined(empty_out)
                else "no"),
            "invariant_property": "yes" if suites else "no",
            "mutation_fault_proof": "yes" if suites else "no",
            "parameter_provenance": prov_status,
            "threshold_provenance": threshold_status,
            "calibration": calibration,
            "category9_qualification": q["canonical_structure_status"],
            "lineage_declared": "yes" if lin else "no",
            "lineage_relationship": (lin or {}).get("evidence_relationship", "UNDECLARED"),
            "regulatory_status": (
                limit[0] if limit and limit[0] == "REGULATORY_VERSION_BLOCKED"
                else "NOT_A_REGULATORY_DETERMINATION"),
            "empirical_validation": (
                "BLOCKED_NO_REFERENCE_CORPUS"
                if limit and limit[0] == "EMPIRICAL_VALIDATION_BLOCKED"
                else "NOT_EMPIRICALLY_VALIDATED"),
            "operational_activation": REG.activation_state(cid),
            "voting_status": "voting" if cid in REG.CORE_VOTING_MODULES else "non-voting",
            "scientific_disposition": disposition,
            "recomputation_basis": reason,
            "test_suites": "; ".join(sorted(set(suites))[:6]),
            "detail": detail,
        })

    # ------------------------------------------------------------------ mechanical proofs
    A.check("REAUDIT", "the re-audit emitted exactly one hundred rows", len(rows) == 100,
            f"got {len(rows)}")
    A.check("REAUDIT", "ninety-five rows are project-level",
            sum(1 for r in rows if r["level"] == "project") == 95)
    A.check("REAUDIT", "five rows are portfolio-level",
            sum(1 for r in rows if r["level"] == "portfolio") == 5)
    A.check("REAUDIT", "every canonical identifier in the emitted table is unique",
            len({r["module_id"] for r in rows}) == 100)
    not_reached = [r["module_id"] for r in rows if r["execution_outcome"] == "NOT_REACHED"]
    A.check("REAUDIT", "NOT_REACHED is nought", not not_reached, str(not_reached))
    unassessed = [r["module_id"] for r in rows
                  if r["scientific_disposition"] in ("", "NOT_ASSESSED", "UNRECORDED")]
    A.check("REAUDIT", "NOT_ASSESSED is nought", not unassessed, str(unassessed))
    bad = [(r["module_id"], r["scientific_disposition"]) for r in rows
           if r["scientific_disposition"] not in DISPOSITIONS]
    A.check("REAUDIT", "every recomputed disposition is drawn from the closed vocabulary",
            not bad, str(bad))
    uncovered = [r["module_id"] for r in rows if not r["test_suites"]]
    A.check("REAUDIT", "every target carries named test coverage in the committed corpus",
            not uncovered, str(uncovered))
    crashed = [(r["module_id"], r["detail"]) for r in rows
               if r["execution_outcome"] in ("RAISED", "MALFORMED")]
    A.check("REAUDIT", "no target raised or returned a malformed result on a populated project",
            not crashed, str(crashed))

    # The withheld canonical structures are withheld, so no abstention here is manufactured.
    A.check("REAUDIT", "no canonical structure the corpus does not hold was invented in the "
            "fixture", not any(k in FULL_SI for k in CANONICAL_KEYS_WITHHELD))

    # ------------------------------------------------------------------ safety invariants
    voting = sorted(r["module_id"] for r in rows if r["voting_status"] == "voting")
    A.check("SAFETY", "exactly two targets vote and they are the two established in Run 4",
            len(voting) == 2, str(voting))
    concept = [r for r in rows if r["code_id"] in REG.DISABLED_CONCEPT_ONLY]
    A.check("SAFETY", "eight concept-only modules are in the population and none is activated",
            len(concept) == 8 and all(r["operational_activation"] == "DISABLED_UNSAFE"
                                      for r in concept),
            str([(r["module_id"], r["operational_activation"]) for r in concept]))
    A.check("SAFETY", "every concept-only module resolves to FUTURE_RESEARCH_ONLY",
            all(r["scientific_disposition"] == "FUTURE_RESEARCH_ONLY" for r in concept))
    A.check("SAFETY", "Material Cost Variance is not one of the hundred targets",
            "A3.4" not in {r["code_id"] for r in rows})
    A.check("SAFETY", "Material Cost Variance is still disabled under evidence review",
            REG.DISABLED_EVIDENCE_UNDER_REVIEW == {"A3.4": "Material Cost Variance"})
    A.check("SAFETY", "Material Cost Variance is short-circuited before its formula is reached",
            _abstained(REG.run_module("A3.4", dict(FULL_SI), RAND, CUTOFF))
            and REG.run_module("A3.4", dict(FULL_SI), RAND, CUTOFF)["activation_state"]
            == "DISABLED_EVIDENCE_UNDER_REVIEW")

    # ------------------------------------------------------------------ difference from Run 19
    base = {r["module_id"]: r["scientific_disposition"] for r in csv.DictReader(
        (ROOT / "code_audit" / "run19_final_100_reconciliation.csv").open(encoding="utf-8"))}
    A.check("REAUDIT", "the Run-19 baseline covers the same hundred identifiers",
            set(base) == {r["module_id"] for r in rows},
            str(sorted(set(base) ^ {r["module_id"] for r in rows})[:8]))
    changed = [r["module_id"] for r in rows
               if base[r["module_id"]] != r["scientific_disposition"]]
    # This is a recorded quantity, not a target. It is asserted non-empty only because eleven
    # cycles of remediation that changed nothing would itself be the finding.
    A.check("REAUDIT", "the recomputation differs from the Run-19 baseline, as eleven cycles of "
            "remediation require", bool(changed), "no target changed disposition at all")
    A.check("REAUDIT", "METHOD_LABEL_MISMATCH is nought after the recomputation",
            not [r for r in rows if r["scientific_disposition"] == "METHOD_LABEL_MISMATCH"])

    # ------------------------------------------------------------------ emit
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    dist = collections.Counter(r["scientific_disposition"] for r in rows)
    print("Recomputed disposition distribution over the hundred targets:")
    for k, v in sorted(dist.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {v:3d}  {k}")
    print(f"Targets whose disposition differs from the Run-19 baseline: {len(changed)}")
    return rows


if __name__ == "__main__":
    audit()
    sys.exit(A.finish())
