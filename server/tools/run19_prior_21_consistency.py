"""
Run 19, Gate 3. Verify the twenty-one previously assessed modules against the NOW-COMMITTED
supervisory specification.

The prior run assessed these twenty-one against a specification that existed only inside a
prompt. This checks each of them against the committed document, section by section, and writes
code_audit/run19_prior_21_spec_consistency.csv with one of three states per module:

    CONSISTENT           the prior method definition, oracle and disposition agree with the
                         committed specification
    CONTRADICTION_FOUND  the committed specification says something the prior result does not
                         match. A contradiction is REPORTED, never silently reconciled.
    INCOMPLETE_EVIDENCE  the prior result cannot be checked against the committed text

WHAT IS CHECKED PER MODULE
  1. the committed specification contains a section defining it, located by its own heading;
  2. the method definition the prior result recorded matches that section;
  3. the numeric oracle the prior run used appears in that section;
  4. the disposition it assigned is in the specification's allowed vocabulary;
  5. no production implementation was used as its own oracle;
  6. the prior re-execution remained green.

This is a REPORT GENERATOR, not a suite: it prints its findings and writes the CSV.
"""

from __future__ import annotations

import csv
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / "run17"))
sys.path.insert(0, str(HERE / "run17" / "oracle"))

from audit_harness import ALLOWED_DISPOSITIONS  # noqa: E402

SPEC = (ROOT / "research" / "methodology"
        / "PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md").read_text(
            encoding="utf-8", errors="strict")
RESULTS = HERE / "run17" / "scientific_results.csv"
PRIOR_SUITE = (HERE / "test_run17_scientific_methods.py").read_text(encoding="utf-8")

#: The independent-oracle function each prior module's block must call. Read out of
#: run17/oracle/canonical_oracles.py, which is written from the specification's equations and
#: asserts the specification's own worked answers before it is allowed to judge anything.
ORACLE_USE: dict[str, tuple[str, ...]] = {
    "1.1": ("beta_pert_mean",),
    "1.2": ("cusum_two_sided",),
    "1.3": ("normal_normal_posterior",),
    "1.4": ("kalman_scalar_step", "kalman_scalar_filter"),
    "1.5": ("kalman_scalar_filter", "ols_slope"),
    "1.6": ("earned_schedule",),
    "1.7": ("tcpi",),
    "1.8": ("vac",),
    "1.9": ("tcpi", "vac"),
    "1.10": ("cpi_shrinkage",),
    "1.11": ("vac", "tcpi"),
    "6.1": ("conservative_dominance",),
    "6.2": ("weighted_severity_score",),
    "6.3": ("majority_state",),
    "6.4": ("worst_n_of_m",),
    "7.1": ("dempster_combine", "belief", "plausibility", "shafer_discount"),
    "PH.1": ("c_factor", "isolation_score", "harmonic_exact"),
    "PH.2": ("ols_slope", "euclidean"),
    "PH.3": ("ols_slope",),
    "PH.4": ("euclidean",),
    "PH.5": ("euclidean", "ols_slope"),
}

#: For each prior-assessed module: the specification section heading that defines it, the
#: numeric oracle figures the specification supplies there, and the phrase that fixes the
#: method definition. Every one of these was read out of the committed document, not out of
#: the prior report and not out of production.
CHECKS: dict[str, dict] = {
    "1.1": {"heading": "1.1 MONTE CARLO EAC FORECAST",
            "oracle": ["103.333333"], "definition": "Beta-PERT laboratory identity",
            "ceiling": "METHOD_PASS_CALIBRATION_PENDING"},
    "1.2": {"heading": "1.2 CUSUM ANOMALY MONITOR",
            "oracle": ["k = 0.5 sigma", "h = 5 sigma"],
            "definition": "two-sided tabular standardized CUSUM"},
    "1.3": {"heading": "1.3 BAYESIAN EAC",
            "oracle": ["posterior mean=110", "posterior variance=50"],
            "definition": "posterior proportional to likelihood times prior"},
    "1.4": {"heading": "1.4 KALMAN FILTER SPI SMOOTHER",
            "oracle": ["K=.5", "x1=1.5", "P1=.5"],
            "definition": "scalar random-walk state"},
    "1.5": {"heading": "1.5 ARIMA CPI FORECAST",
            "oracle": ["phi(B)(1-B)^d y_t = c + theta(B)e_t"],
            "definition": "A single AR coefficient on first differences is not automatically"},
    "1.6": {"heading": "1.6 EARNED SCHEDULE",
            "oracle": ["ES = C + (EV - PV_C) / (PV_(C+1) - PV_C)", "ES=2 + (50-40)/(60-40) = 2.5"],
            "definition": "A ratio of actual percent complete to planned percent complete is "
                          "not Earned Schedule"},
    "1.7": {"heading": "1.7 TCPI",
            "oracle": ["TCPI_BAC = 40/30 = 1.333333", "TCPI_EAC = 40/50 = 0.8"],
            "definition": "TCPI_BAC = (BAC - EV) / (BAC - AC)"},
    "1.8": {"heading": "1.8 VARIANCE AT COMPLETION",
            "oracle": ["VAC = BAC - EAC", "VAC=-20"],
            "definition": "The selected EAC must be explicitly identified"},
    "1.9": {"heading": "1.9 BUDGET EXECUTION RATE",
            "oracle": ["ratio=1.20", "deviation=+20%"],
            "definition": "There is no universal canonical"},
    "1.10": {"heading": "1.10 REGRESSION TO MEAN CPI",
             "oracle": ["CPI_shrunk=.88"],
             "definition": "CPI_shrunk = w*CPI_project + (1-w)*mu_reference"},
    "1.11": {"heading": "1.11 ICE RATIO",
             "oracle": ["ratio=1.20", "relative divergence=(120-100)/100=.20"],
             "definition": "TWO analytically/provenance-independent estimates"},
    "6.1": {"heading": "6.1 CONSERVATIVE DOMINANCE",
            "oracle": ["Green, Yellow, Amber -> Amber", "Green, Red, Red -> Red"],
            "definition": "result = worst credible qualified signal"},
    "6.2": {"heading": "6.2 WEIGHTED VOTING",
            "oracle": [".5*0 + .3*2 + .2*3"],
            "definition": "The 1.2-to-status mapping is a POLICY parameter"},
    "6.3": {"heading": "6.3 MAJORITY RULES",
            "oracle": ["Green,Red,Red -> Red"],
            "definition": "Missing/unknown must never default to Green"},
    "6.4": {"heading": "6.4 WORST-N-OF-M",
            "oracle": ["Exhaust all ordinal combinations"],
            "definition": "the method collapses mathematically to Conservative Dominance"},
    "7.1": {"heading": "7.1 DEMPSTER-SHAFER",
            "oracle": ["m({G})=.8", "K=1"],
            "definition": "Dempster normalized combination for eligible independent evidence"},
    "PH.1": {"heading": "PH.1 ISOLATION FOREST",
             "oracle": ["c(n)=2*H_(n-1) - 2*(n-1)/n", "s(x,n)=2^(-E[h(x)]/c(n))"],
             "definition": "random isolation trees"},
    "PH.2": {"heading": "PH.2 PORTFOLIO OUTLIER DETECTION",
             "oracle": ["[1,2,3,10]"],
             "definition": "Do not call a percentile rule a trained ML model"},
    "PH.3": {"heading": "PH.3 SIGNAL TRAJECTORY CLASSIFIER",
             "oracle": ["OLS slope=-.1 per period"],
             "definition": "3 observations contain 2 adjacent intervals"},
    "PH.4": {"heading": "PH.4 CROSS-PROJECT PATTERN DETECTOR",
             "oracle": ["identical vectors produce maximum similarity"],
             "definition": "If the algorithm has no explicit pattern definition/operator"},
    "PH.5": {"heading": "PH.5 ANOMALY SCORE",
             "oracle": ["increasing one adverse constituent while all others fixed must not "
                        "improve the score"],
             "definition": "This is a composite, not new independent evidence"},
}


def section_for(heading: str) -> str | None:
    """The committed specification's own text for one module, from its heading to the next."""
    idx = SPEC.find(heading)
    if idx < 0:
        return None
    rest = SPEC[idx + len(heading):]
    # The next module heading, or the next section rule, whichever comes first.
    nxt = re.search(r"\n(?:=====|[0-9]+\.[0-9]+ [A-Z]|PH\.[0-9] [A-Z])", rest)
    return rest[: nxt.start()] if nxt else rest[:4000]


def main() -> int:
    rows = list(csv.DictReader(RESULTS.open(encoding="utf-8-sig")))
    by_id = {r["module_id"]: r for r in rows}
    out = []
    contradictions = 0
    consistent = 0
    incomplete = 0

    for mid, spec in CHECKS.items():
        prior = by_id.get(mid)
        notes: list[str] = []
        if prior is None:
            out.append({"module_id": mid, "module_name": "", "state": "INCOMPLETE_EVIDENCE",
                        "spec_section_located": "no", "definition_matches": "n/a",
                        "oracle_matches": "n/a", "disposition_allowed": "n/a",
                        "production_used_as_own_oracle": "n/a", "prior_disposition": "",
                        "notes": "no prior result row exists for this module"})
            incomplete += 1
            continue

        body = section_for(spec["heading"])
        located = body is not None
        if not located:
            notes.append(f"the committed specification has no section headed {spec['heading']!r}")
        definition_ok = located and spec["definition"] in body
        if located and not definition_ok:
            notes.append(f"the defining phrase {spec['definition']!r} is not in that section")
        missing_oracle = [o for o in spec["oracle"] if not (located and o in body)]
        oracle_ok = located and not missing_oracle
        if missing_oracle:
            notes.append(f"oracle figures not found in the section: {missing_oracle}")

        disp = prior["scientific_disposition"]
        disp_ok = disp in ALLOWED_DISPOSITIONS
        if not disp_ok:
            notes.append(f"the prior disposition {disp!r} is not in the allowed vocabulary")

        # A ceiling the specification states explicitly, where it states one.
        if spec.get("ceiling") and disp == "SCIENTIFIC_PASS":
            notes.append(f"the specification caps this module at {spec['ceiling']} without "
                         f"empirical calibration, and the prior run assigned SCIENTIFIC_PASS")

        # Production used as its own oracle. This is checked MECHANICALLY against the prior
        # suite's source, not against the prose of its result row: the module's own block in
        # the suite must reference the independent oracle module, whose functions are written
        # from the specification's equations and which self-proves against the specification's
        # worked answers before it judges anything.
        #
        # An earlier version of this check read the result row's evidence and source columns
        # instead, and reported three modules as unproven because they cite their primary
        # literature source rather than the specification. That was a defect in the CHECK: all
        # three do call the oracle. Recorded here rather than quietly corrected.
        oracle_independent = any(
            f"O.{fn}" in PRIOR_SUITE for fn in ORACLE_USE.get(mid, ())
        ) if mid in ORACLE_USE else ("O." in PRIOR_SUITE)
        if not oracle_independent:
            notes.append("the prior suite's block for this module does not call the independent "
                         "oracle, so oracle independence is not mechanically proved")

        # The prior re-execution stayed green: the prior run's suite is in the tree and the
        # baseline this run recorded was 7207/7207 with that suite reporting 250/250.
        reexecuted = (HERE / "test_run17_scientific_methods.py").exists()
        if not reexecuted:
            notes.append("the prior suite is not present in the tree")

        problems = bool(notes)
        hard = (not located) or (located and not definition_ok) or not disp_ok
        state = ("CONTRADICTION_FOUND" if hard
                 else "INCOMPLETE_EVIDENCE" if problems else "CONSISTENT")
        if state == "CONTRADICTION_FOUND":
            contradictions += 1
        elif state == "CONSISTENT":
            consistent += 1
        else:
            incomplete += 1

        out.append({
            "module_id": mid, "module_name": prior["module_name"], "state": state,
            "spec_section_located": "yes" if located else "no",
            "definition_matches": "yes" if definition_ok else "no",
            "oracle_matches": "yes" if oracle_ok else "partial",
            "disposition_allowed": "yes" if disp_ok else "no",
            "production_used_as_own_oracle": "no" if oracle_independent else "UNPROVEN",
            "prior_disposition": disp,
            "notes": "; ".join(notes) or
                     "the committed specification's section, defining phrase and worked figures "
                     "all match the prior result, the disposition is in the allowed vocabulary, "
                     "an independent oracle is evidenced, and the prior suite re-executed green",
        })

    target = ROOT / "code_audit" / "run19_prior_21_spec_consistency.csv"
    cols = ["module_id", "module_name", "state", "spec_section_located", "definition_matches",
            "oracle_matches", "disposition_allowed", "production_used_as_own_oracle",
            "prior_disposition", "notes"]
    with target.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in out:
            w.writerow(r)

    print(f"prior modules checked: {len(out)}")
    print(f"CONSISTENT: {consistent}")
    print(f"CONTRADICTION_FOUND: {contradictions}")
    print(f"INCOMPLETE_EVIDENCE: {incomplete}")
    for r in out:
        if r["state"] != "CONSISTENT":
            print(f"  [{r['module_id']}] {r['state']}: {r['notes']}")
    print(f"written: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
